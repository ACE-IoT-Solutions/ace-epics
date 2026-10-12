"""Ordered, queryable RDF interchange for ASHRAE 135.1 Clause 4 documents."""

import hashlib
import importlib
import json
import re
from datetime import date, datetime, time
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import IO, Any
from urllib.parse import quote, unquote
from uuid import uuid4

from ace_epics.diagnostics import EpicsError
from ace_epics.model.document import EpicsDocument
from ace_epics.values import ValueNode

from ._interchange import VALUES, decode_document, document_data, failure
from .base import ParseResult, document_from_result
from .errors import MissingExtraError

name = "rdf"
extensions = (".ttl", ".nt", ".jsonld")
media_type = "text/turtle"
NAMESPACE = "https://w3id.org/ace-epics#"
BACNET_NAMESPACE = "http://data.ashrae.org/bacnet/"
BACPYPES3_RDF_VERSION = "0.0.110"
VALUE_KINDS = {
    "null",
    "boolean",
    "integer",
    "real",
    "octet-string",
    "character-string",
    "enumerated",
    "empty",
    "unspecified",
    "wildcard",
    "date",
    "time",
    "date-range",
    "object-identifier",
    "context-tagged",
    "group",
}
ALIASES = {
    "objects": "object",
    "properties": "property",
    "bibbs": "bibb",
    "services": "service",
    "object_types": "objectTypeSupport",
    "data_links": "dataLink",
    "character_sets": "characterSet",
    "default_restrictions": "defaultRestriction",
    "fail_times": "failTimes",
    "restrictions": "restriction",
    "baud_rates": "baudRate",
    "identifier": "objectIdentifier",
    "not_readable": "notReadable",
}
REVERSE = {value: key for key, value in ALIASES.items()}
CLASS_NAMES = {
    "services": "ServiceSupport",
    "object_types": "ObjectTypeSupport",
    "objects": "Object",
    "properties": "Property",
    "identifier": "ObjectIdentifier",
    "special": "SpecialFunctionality",
    "default_restrictions": "DefaultRestrictions",
    "restrictions": "RestrictionSet",
    "fail_times": "FailTimes",
    "data_links": "DataLink",
}
ACCESS = {"R": "ReadOnly", "W": "Writable", "C": "ConditionallyWritable"}


def _rdf() -> Any:
    try:
        return importlib.import_module("rdflib")
    except ImportError as exc:
        raise MissingExtraError("rdf") from exc


@lru_cache(maxsize=1)
def _profile() -> dict[str, Any]:
    """Released vocabulary facts; importing BACpypes3 is not a runtime requirement."""
    return json.loads(files("ace_epics.codecs").joinpath("data/bacpypes3-rdf.json").read_text())


def _enum_member(datatype: str, value: str | int) -> str | None:
    profile = _profile()["enums"].get(datatype)
    if profile is None:
        return None
    if isinstance(value, int):
        minimum = profile.get("minimum", 0)
        maximum = min(
            profile.get("maximum", _profile()["wire_enumerated_maximum"]),
            _profile()["wire_enumerated_maximum"],
        )
        if value < minimum or (maximum is not None and value > maximum):
            return None
        return profile["numeric_names"].get(str(value), str(value))
    normalized = re.sub(r"[-_\s]+", "-", value.strip().lower())
    return profile["aliases"].get(normalized)


def _object_type(value: str | int) -> str | None:
    """Resolve released object symbols, or sourced numeric identifiers for newer types."""
    return _enum_member("ObjectType", value)


def _camel(field: str) -> str:
    words = field.split("_")
    return ALIASES.get(field, words[0] + "".join(word.title() for word in words[1:]))


def _field(term: str) -> str:
    return REVERSE.get(term, re.sub(r"(?<!^)(?=[A-Z])", "_", term).lower())


def _restore_wildcards(data: Any, *, field: str | None = None, in_node: bool = False) -> Any:
    from ._interchange import DATE_FIELDS

    if isinstance(data, list):
        return [_restore_wildcards(item, in_node=in_node) for item in data]
    if isinstance(data, dict):
        node = data.get("kind") in VALUE_KINDS
        return {
            key: _restore_wildcards(value, field=key, in_node=node) for key, value in data.items()
        }
    if data == "*" and in_node and (field in DATE_FIELDS or field is None):
        return {"kind": "wildcard"}
    return data


class _Writer:
    def __init__(self, base: str, deterministic: bool) -> None:
        self.rdf = _rdf()
        self.epics = self.rdf.Namespace(NAMESPACE)
        self.graph = self.rdf.Graph()
        self.bacnet = self.rdf.Namespace(BACNET_NAMESPACE)
        self.graph.bind("ace-epics", self.epics)
        self.graph.bind("bacnet", self.bacnet)
        self.graph.bind("rdf", self.rdf.RDF)
        self.graph.bind("xsd", self.rdf.XSD)
        self.base = base.rstrip("/")
        self.deterministic = deterministic
        self.counter = 0

    def node(self) -> Any:
        self.counter += 1
        return (
            self.rdf.URIRef(f"{self.base}/_/n{self.counter}")
            if self.deterministic
            else self.rdf.BNode()
        )

    def literal(self, value: Any) -> Any:
        if isinstance(value, (self.rdf.URIRef, self.rdf.BNode)):
            return value
        return self.epics.Null if value is None else self.rdf.Literal(value)

    def sequence(self, values: list, field: str) -> Any:
        if not values:
            return self.rdf.RDF.nil
        cells = [self.node() for _ in values]
        for index, (cell, item) in enumerate(zip(cells, values, strict=True)):
            self.graph.add((cell, self.rdf.RDF.first, self.encode(item, field)))
            following = cells[index + 1] if index + 1 < len(cells) else self.rdf.RDF.nil
            self.graph.add((cell, self.rdf.RDF.rest, following))
        return cells[0]

    def encode(self, value: Any, field: str = "", subject: Any = None) -> Any:
        if isinstance(value, list):
            return self.sequence(value, field)
        if not isinstance(value, dict):
            return self.literal(value)
        if field in {"extra", "header_metadata"}:
            node = subject or self.node()
            self.graph.add((node, self.rdf.RDF.type, self.epics.Dictionary))
            items = [{"key": key, "item": item} for key, item in value.items()]
            self.graph.add((node, self.epics.entryOrder, self.sequence(items, "entry")))
            return node
        kind = value.get("kind")
        if kind in VALUE_KINDS:
            return self.value(value)
        node = subject or self.node()
        cls = CLASS_NAMES.get(field, "Record")
        if "minimum" in value and "maximum_length_array" in value:
            cls = "RestrictionSet"
        if field == "data_links":
            cls = "".join(word.title() for word in str(kind).split("-")) + "DataLink"
        self.graph.add((node, self.rdf.RDF.type, self.epics[cls]))
        if cls == "RestrictionSet" and field != "restrictions":
            self.graph.add((node, self.epics.datatypeKey, self.literal(field)))
        for key, item in value.items():
            if item is None:
                continue
            if cls == "Object" and key in {"identifier", "object_type", "name"}:
                if key == "identifier":
                    obj_type = item["object_type"]
                    member = _object_type(obj_type)
                    if member is None:
                        literal = self.value(
                            {
                                "kind": "object-identifier",
                                "object_type": obj_type,
                                "instance": item["instance"],
                            }
                        )
                    else:
                        literal = self.rdf.Literal(
                            f"{member},{item['instance']}", datatype=self.bacnet.objectIdentifier
                        )
                    self.graph.add((node, self.bacnet["object-identifier"], literal))
                elif key == "object_type":
                    member = _object_type(item)
                    term = (
                        self.bacnet[f"ObjectType.{member}"]
                        if member is not None
                        else self.epics[f"object-type/{quote(str(item), safe='')}"]
                    )
                    self.graph.add((node, self.bacnet["object-type"], term))
                    if member != str(item):
                        self.graph.add((node, self.epics.canonicalObjectType, self.literal(item)))
                else:
                    self.graph.add((node, self.bacnet["object-name"], self.rdf.Literal(item)))
                continue
            predicate = _camel(key)
            if key == "name" and cls in {"ServiceSupport", "Property", "Object"}:
                predicate = {
                    "ServiceSupport": "serviceName",
                    "Property": "propertyName",
                    "Object": "objectName",
                }[cls]
            if key == "access":
                self.graph.add((node, self.epics.access, self.epics[ACCESS[item]]))
            elif isinstance(item, list):
                head = self.sequence(item, key)
                self.graph.add((node, self.epics[predicate + "Order"], head))
                for entry in self.read_list(head):
                    self.graph.add((node, self.epics[predicate], entry))
            else:
                self.graph.add((node, self.epics[predicate], self.encode(item, key)))
        return node

    def read_list(self, head: Any):
        while head != self.rdf.RDF.nil:
            yield self.graph.value(head, self.rdf.RDF.first)
            head = self.graph.value(head, self.rdf.RDF.rest)

    def bacnet_value(self, data: dict, datatype: str | None = None) -> Any:
        """Project values using the released BACpypes3 RDF atomic/list conventions."""
        if data == "*":
            data = {"kind": "wildcard"}
        kind = data["kind"]
        dtype = (datatype or "").removeprefix("BACnet")
        dtype = {
            "integer": "Integer",
            "real": "Real",
            "boolean": "Boolean",
            "character-string": "CharacterString",
            "octet-string": "OctetString",
            "date": "Date",
            "time": "Time",
            "enumerated": "",
            "group": "",
            "object-identifier": "ObjectIdentifier",
            "date-range": "DateRange",
            "Any": "",
        }.get(dtype, dtype)
        dtype = dtype.removeprefix("Optional")
        primitive_types = {
            "boolean": {"Boolean"},
            "real": {"Real", "Double"},
            "character-string": {"CharacterString"},
            "octet-string": {"OctetString"},
            "date": {"Date"},
            "time": {"Time"},
            "date-range": {"DateRange"},
            "object-identifier": {"ObjectIdentifier"},
        }
        if dtype and kind in primitive_types and dtype not in primitive_types[kind]:
            return self.value(data)
        if kind == "null":
            return self.bacnet.Null
        if kind == "boolean":
            return self.rdf.Literal(data["value"])
        if kind == "integer":
            if dtype in {"Real", "Double"}:
                try:
                    projected = float(data["value"])
                except OverflowError:
                    return self.value(data)
                return self.rdf.Literal(
                    projected,
                    datatype=(self.rdf.XSD.double if dtype == "Double" else self.rdf.XSD.float),
                )
            if dtype in _profile()["enums"]:
                member = _enum_member(dtype, data["value"])
                return self.bacnet[f"{dtype}.{member}"] if member is not None else self.value(data)
            if dtype and not dtype.startswith(("Unsigned", "Integer", "Signed")):
                return self.value(data)
            if dtype.startswith("Unsigned") and data["value"] < 0:
                return self.value(data)
            return self.rdf.Literal(
                data["value"],
                datatype=(
                    self.rdf.XSD.nonNegativeInteger
                    if dtype.startswith("Unsigned")
                    else self.rdf.XSD.integer
                ),
            )
        if kind == "real":
            return self.rdf.Literal(
                float(data["value"]),
                datatype=(self.rdf.XSD.double if dtype == "Double" else self.rdf.XSD.float),
            )
        if kind == "character-string":
            return self.rdf.Literal(data["value"])
        if kind == "octet-string":
            return self.rdf.Literal(
                str(data["value"]).lower(), datatype=self.rdf.XSD.hexBinary, normalize=False
            )
        if kind == "enumerated":
            enum_name = data.get("proprietary_number")
            if enum_name is None:
                enum_name = data["name"]
            if isinstance(enum_name, dict):
                enum_name = enum_name["canonical"]
            member = _enum_member(dtype, enum_name)
            return self.bacnet[f"{dtype}.{member}"] if member is not None else self.value(data)
        if kind == "object-identifier" and data["instance"] is not None:
            obj_type = data["object_type"]
            if isinstance(obj_type, dict):
                obj_type = obj_type["canonical"]
            member = _object_type(obj_type)
            if (
                member is None
                or not 0
                <= data["instance"]
                <= _profile()["wire_object_identifier"]["instance_maximum"]
            ):
                return self.value(data)
            return self.rdf.Literal(
                f"{member},{data['instance']}", datatype=self.bacnet.objectIdentifier
            )
        if kind == "date":
            year, month, day = (data[field] for field in ("year", "month", "day"))
            weekday = data.get("weekday")
            if all(type(field) is int for field in (year, month, day)) and weekday is None:
                try:
                    return self.rdf.Literal(date(year, month, day))
                except ValueError:
                    pass
            if all(type(field) is int for field in (year, month, day, weekday)):
                try:
                    return self.rdf.Literal(date(year, month, day))
                except ValueError:
                    pass

            def date_field(field: Any, specials: dict[int, str] | None = None) -> str:
                if type(field) is not int:
                    return "*"
                return (specials or {}).get(field, str(field))

            weekdays = {1: "mon", 2: "tue", 3: "wed", 4: "thu", 5: "fri", 6: "sat", 7: "sun"}
            lexical = (
                f"{date_field(year)}-{date_field(month, {13: 'odd', 14: 'even'})}-"
                f"{date_field(day, {32: 'last', 33: 'odd', 34: 'even'})} "
                f"{date_field(weekday, weekdays)}"
            )
            return self.rdf.Literal(lexical, datatype=self.bacnet.datePattern)
        if kind == "time":
            fields = [data[field] for field in ("hour", "minute", "second", "hundredth")]
            if all(type(field) is int for field in fields):
                return self.rdf.Literal(time(*fields[:3], microsecond=fields[3] * 10_000))
            parts = [str(field) if type(field) is int else "*" for field in fields]
            if type(fields[3]) is int:
                parts[3] = f"{fields[3]:02d}"
            return self.rdf.Literal(
                ":".join(parts[:3]) + "." + parts[3], datatype=self.bacnet.timePattern
            )
        if kind == "date-range":
            node = self.node()
            self.graph.add(
                (node, self.bacnet["start-date"], self.bacnet_value(data["start"], "Date"))
            )
            self.graph.add((node, self.bacnet["end-date"], self.bacnet_value(data["end"], "Date")))
            return node
        if kind == "group":
            elements = data["elements"]
            if (
                dtype == "DateTime"
                and len(elements) == 2
                and isinstance(elements[0], dict)
                and isinstance(elements[1], dict)
                and (elements[0].get("kind") == "date" and elements[1].get("kind") == "time")
            ):
                date_term = self.bacnet_value(elements[0], "Date")
                time_term = self.bacnet_value(elements[1], "Time")
                if (
                    date_term.datatype == self.rdf.XSD.date
                    and time_term.datatype == self.rdf.XSD.time
                ):
                    return self.rdf.Literal(
                        datetime.combine(date_term.toPython(), time_term.toPython())
                    )
                if date_term.datatype == self.bacnet.datePattern:
                    date_text = str(date_term)
                else:
                    day = date_term.toPython()
                    weekday = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[day.weekday()]
                    date_text = f"{day.year}-{day.month}-{day.day} {weekday}"
                if time_term.datatype == self.bacnet.timePattern:
                    time_text = str(time_term)
                else:
                    instant = time_term.toPython()
                    time_text = f"{instant.hour}:{instant.minute:02d}:{instant.second:02d}"
                    if instant.microsecond:
                        time_text += f".{instant.microsecond // 10_000:02d}"
                return self.rdf.Literal(
                    f"{date_text} {time_text}", datatype=self.bacnet.dateTimePattern
                )
            if dtype == "DateTime":
                return self.value(data)
            bit_types = _profile()["bitstrings"]
            collection = re.fullmatch(
                r"(?:array|list)(?:\[[^]]*\])?(?:\s+of\s+(.+))?", dtype, flags=re.IGNORECASE
            )
            if dtype and dtype not in bit_types and collection is None and dtype != "DateTime":
                return self.value(data)
            if dtype in bit_types and all(
                isinstance(item, dict) and item["kind"] == "boolean" for item in elements
            ):
                names = {v: k for k, v in bit_types[dtype]["values"].items()}
                values = [
                    self.bacnet[f"{dtype}.{names[i]}"] if i in names else self.rdf.Literal(i)
                    for i, item in enumerate(elements)
                    if item["value"]
                ]
            elif dtype in bit_types:
                return self.value(data)
            else:
                element_type = collection.group(1) if collection is not None else None
                values = [self.bacnet_value(item, element_type) for item in elements]
            return self.sequence(values, "")
        return self.value(data)

    def value(self, data: dict) -> Any:
        from ace_epics.values.render import render

        kind = data["kind"]
        node = (
            self.epics.emptyElement
            if kind == "empty"
            else self.epics.unspecifiedValue
            if kind == "unspecified"
            else self.node()
        )
        cls = "".join(word.title() for word in kind.split("-")) + "Value"
        if kind == "empty":
            cls = "EmptyElement"
        self.graph.add((node, self.rdf.RDF.type, self.epics[cls]))
        self.graph.add(
            (
                node,
                self.epics.lexical,
                self.rdf.Literal(render(VALUES.validate_python(_restore_wildcards(data)))),
            )
        )
        if kind == "group":
            self.graph.add((node, self.epics.delimiter, self.literal(data["delimiter"])))
            self.graph.add((node, self.epics.elements, self.sequence(data["elements"], "value")))
        elif kind == "context-tagged":
            self.graph.add((node, self.epics.tag, self.literal(data["tag"])))
            self.graph.add((node, self.epics.value, self.value(data["value"])))
        elif kind == "object-identifier":
            obj_type = data["object_type"]
            if isinstance(obj_type, dict):
                obj_type = obj_type["canonical"]
            self.graph.add((node, self.epics.objectType, self.literal(obj_type)))
            self.graph.add((node, self.epics.instance, self.literal(data["instance"])))
        elif kind == "date":
            fields = [data[field] for field in ("year", "month", "day")]
            if all(type(field) is int for field in fields):
                try:
                    lexical = date(*fields).isoformat()
                except ValueError:
                    pass  # BACnet special dates have no exact xsd:date counterpart.
                else:
                    self.graph.add(
                        (
                            node,
                            self.epics.typedValue,
                            self.rdf.Literal(lexical, datatype=self.rdf.XSD.date),
                        )
                    )
        elif kind == "time":
            fields = [data[field] for field in ("hour", "minute", "second", "hundredth")]
            if all(type(field) is int for field in fields):
                try:
                    lexical = time(*fields[:3], microsecond=fields[3] * 10_000).isoformat()
                except ValueError:
                    pass
                else:
                    self.graph.add(
                        (
                            node,
                            self.epics.typedValue,
                            self.rdf.Literal(lexical, datatype=self.rdf.XSD.time),
                        )
                    )
        elif kind in {"integer", "boolean", "character-string", "real", "octet-string"}:
            datatype = {
                "integer": self.rdf.XSD.integer,
                "boolean": self.rdf.XSD.boolean,
                "character-string": self.rdf.XSD.string,
                "real": self.rdf.XSD.decimal,
                "octet-string": self.rdf.XSD.hexBinary,
            }[kind]
            raw = data["value"]
            if kind != "real" or str(raw) not in {"Infinity", "-Infinity", "NaN"}:
                self.graph.add(
                    (
                        node,
                        self.epics.typedValue,
                        self.rdf.Literal(raw, datatype=datatype, normalize=False),
                    )
                )
        return node


def to_graph(
    doc: EpicsDocument, *, base_iri: str | None = None, deterministic: bool = False, **opts: Any
) -> Any:
    """Build linked sections, local objects, properties, and ordered value lists (4.5)."""
    from ace_epics.knowledge import JsonKnowledgeProvider
    from ace_epics.knowledge.provider import normalize_name
    from ace_epics.validation import Query

    data = document_data(doc)
    provider = JsonKnowledgeProvider()
    query = Query(doc, provider)
    standard_properties = provider.property_identifiers()
    object_nodes = []
    object_identities: set[Any] = set()
    if base_iri is None:
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        base_iri = f"urn:ace-epics:{digest}" if deterministic else f"urn:uuid:{uuid4()}"
    writer = _Writer(base_iri, deterministic)
    subject = writer.rdf.URIRef(base_iri)
    device = doc.device
    device_subject = (
        writer.rdf.URIRef(f"{base_iri}/device/{device.identifier.instance}")
        if device is not None
        else None
    )
    if device_subject is not None and device is not None:
        writer.graph.add((subject, writer.epics.describesDevice, device_subject))
        writer.graph.add((device_subject, writer.rdf.RDF.type, writer.bacnet.Device))
        writer.graph.add(
            (
                device_subject,
                writer.bacnet["device-instance"],
                writer.rdf.Literal(device.identifier.instance),
            )
        )
    writer.graph.add((subject, writer.rdf.RDF.type, writer.epics.Document))
    writer.graph.add(
        (subject, writer.epics.headerCode, writer.literal(data["header"]["charset_code"]))
    )
    for key, value in data["general"].items():
        writer.graph.add((subject, writer.epics[_camel(key)], writer.literal(value)))
    for key in ("bibbs", "services", "object_types", "data_links", "character_sets", "objects"):
        values = data[key]
        if key == "objects":
            # Stable object and property identities permit joins with application graphs.
            nodes = []
            for original, obj in zip(doc.objects, values, strict=True):
                identifier = obj["identifier"]
                type_name = quote(
                    str(_object_type(identifier["object_type"]) or identifier["object_type"]),
                    safe="",
                )
                node = writer.rdf.URIRef(
                    f"{device_subject}/{type_name},{identifier['instance']}"
                    if device_subject is not None
                    else f"{base_iri}/object/{type_name}/{identifier['instance']}"
                )
                if node in object_identities:
                    raise failure(
                        f"Object identifiers collide after BACnet alias normalization: {node}",
                        "RDF-SHAPE",
                    )
                object_identities.add(node)
                properties = obj.pop("properties")
                writer.encode(obj, "objects", node)
                object_nodes.append(node)
                property_nodes = []
                for prop in properties:
                    prop_node = writer.rdf.URIRef(f"{node}/{quote(prop['name'], safe='')}")
                    writer.encode(prop, "properties", prop_node)
                    number = standard_properties.get(normalize_name(prop["name"]))
                    property_term = _profile()["enums"]["PropertyIdentifier"]["numeric_names"].get(
                        str(number)
                    )
                    if property_term is not None:
                        writer.graph.add(
                            (
                                node,
                                writer.bacnet[property_term],
                                writer.bacnet_value(
                                    prop["value"], query.datatype(original, prop["name"])
                                ),
                            )
                        )
                    writer.graph.add((node, writer.epics.property, prop_node))
                    property_nodes.append(prop_node)
                head = writer.sequence(property_nodes, "")
                writer.graph.add((node, writer.epics.propertyOrder, head))
                nodes.append(node)
            head = writer.sequence(nodes, "")
        else:
            head = writer.sequence(values, key)
        predicate = _camel(key)
        writer.graph.add((subject, writer.epics[predicate + "Order"], head))
        for item in writer.read_list(head):
            writer.graph.add((subject, writer.epics[predicate], item))
    for key in ("special", "default_restrictions", "fail_times"):
        writer.graph.add((subject, writer.epics[_camel(key)], writer.encode(data[key], key)))
    timer_values = {
        key: value
        for key, value in data["fail_times"].items()
        if key != "extra" and value is not None
    }
    timer_values.update(data["fail_times"].get("extra", {}))
    for key, value in timer_values.items():
        timer = writer.node()
        writer.graph.add((timer, writer.rdf.RDF.type, writer.epics.FailTime))
        writer.graph.add((timer, writer.epics.timerName, writer.literal(key)))
        writer.graph.add((timer, writer.epics.seconds, writer.literal(value)))
        writer.graph.add((subject, writer.epics.failTime, timer))
    if device_subject is not None:
        for object_node in object_nodes:
            writer.graph.add((device_subject, writer.bacnet.contains, object_node))
    return writer.graph


class _Reader:
    def __init__(self, graph: Any, max_nodes: int) -> None:
        self.rdf = _rdf()
        self.epics = self.rdf.Namespace(NAMESPACE)
        self.bacnet = self.rdf.Namespace(BACNET_NAMESPACE)
        self.graph = graph
        self.max_nodes = max_nodes
        self.count = 0

    def one(self, subject: Any, predicate: Any, *, required: bool = True) -> Any:
        values = list(self.graph.objects(subject, predicate))
        if len(values) != 1:
            if not values and not required:
                return None
            raise failure(f"RDF requires exactly one {predicate} on {subject}", "RDF-SHAPE")
        return values[0]

    def sequence(self, head: Any, ancestors: frozenset) -> list:
        seen = set()
        result = []
        while head != self.rdf.RDF.nil:
            if head in seen or len(seen) >= self.max_nodes:
                raise failure("Invalid or cyclic RDF list", "RDF-LIST")
            seen.add(head)
            result.append(self.decode(self.one(head, self.rdf.RDF.first), ancestors))
            head = self.one(head, self.rdf.RDF.rest)
        return result

    def decode(self, node: Any, ancestors: frozenset = frozenset()) -> Any:
        self.count += 1
        if self.count > self.max_nodes or node in ancestors:
            raise failure("RDF node expansion limit or cycle encountered", "RDF-LIMIT")
        if node == self.epics.Null:
            return None
        if isinstance(node, self.rdf.Literal):
            return node.toPython()
        lexical = self.one(node, self.epics.lexical, required=False)
        if lexical is not None:
            if (node, self.rdf.RDF.type, self.epics.ObjectIdentifierValue) in self.graph:
                obj_type = self.one(node, self.epics.objectType, required=False)
                if obj_type is not None:
                    return {
                        "kind": "object-identifier",
                        "object_type": self.decode(obj_type),
                        "instance": self.decode(self.one(node, self.epics.instance)),
                    }
            return str(lexical)
        if node == self.rdf.RDF.nil or self.graph.value(node, self.rdf.RDF.first) is not None:
            return self.sequence(node, ancestors | {node})
        types = {str(value) for value in self.graph.objects(node, self.rdf.RDF.type)}
        if str(self.epics.Dictionary) in types:
            entries = self.sequence(self.one(node, self.epics.entryOrder), ancestors | {node})
            return {entry["key"]: entry["item"] for entry in entries}
        result: dict[str, Any] = {}
        predicates = sorted({p for p in self.graph.predicates(node)}, key=str)
        orders = {
            str(p)[len(NAMESPACE) : -5]
            for p in predicates
            if str(p).startswith(NAMESPACE) and str(p).endswith("Order")
        }
        for predicate in predicates:
            if not str(predicate).startswith(NAMESPACE):
                continue
            term = str(predicate)[len(NAMESPACE) :]
            if term == "datatypeKey" or term.startswith("property/"):
                continue
            if term in orders or (
                term in {"typedValue", "instance"} and str(self.epics.Object) in types
            ):
                continue
            value = self.one(node, predicate)
            if term.endswith("Order"):
                field = _field(term[:-5])
                result[field] = self.sequence(value, ancestors | {node})
            elif term == "access":
                reverse_access = {str(self.epics[v]): k for k, v in ACCESS.items()}
                if str(value) not in reverse_access:
                    raise failure("Unknown RDF access declaration", "RDF-SHAPE")
                result["access"] = reverse_access[str(value)]
            else:
                field = (
                    "name"
                    if term in {"serviceName", "propertyName", "objectName"}
                    else _field(term)
                )
                result[field] = self.decode(value, ancestors | {node})
        if str(self.epics.Object) in types:
            identifier = self.one(node, self.bacnet["object-identifier"], required=False)
            if identifier is not None:
                if isinstance(identifier, self.rdf.Literal):
                    object_type, instance = str(identifier).rsplit(",", 1)
                    if object_type.isdigit():
                        object_type = int(object_type)
                    result["identifier"] = {"object_type": object_type, "instance": int(instance)}
                else:
                    decoded = self.decode(identifier, ancestors | {node})
                    result["identifier"] = {
                        "object_type": decoded["object_type"],
                        "instance": decoded["instance"],
                    }
                type_term = str(self.one(node, self.bacnet["object-type"]))
                if type_term.startswith(BACNET_NAMESPACE + "ObjectType."):
                    type_name = type_term.removeprefix(BACNET_NAMESPACE + "ObjectType.")
                elif type_term.startswith(NAMESPACE + "object-type/"):
                    type_name = unquote(type_term.removeprefix(NAMESPACE + "object-type/"))
                else:
                    raise failure("Unsupported BACnet object-type term", "RDF-SHAPE")
                result["object_type"] = int(type_name) if type_name.isdigit() else type_name
                canonical = result.pop("canonical_object_type", None)
                if canonical is not None:
                    result["object_type"] = canonical
                    result["identifier"]["object_type"] = canonical
                result["name"] = str(self.one(node, self.bacnet["object-name"]))
        return result


def bacnet_value(
    value: ValueNode,
    datatype: str | None = None,
    *,
    graph: Any = None,
    deterministic: bool = False,
) -> Any:
    """Encode a Clause4.4 value using BACpypes3 0.0.110 RDF conventions.

    Supply Clause12 datatype metadata for unsigned, enumeration, and bit-string
    projections. EPICS-only values retain ace-epics lexical declarations. Structured
    projections require the returned term's accompanying graph; pass a graph to
    receive their triples. BACpypes3 is a development cross-check, not a runtime dependency.
    """
    writer = _Writer(f"urn:ace-epics:value:{uuid4()}", deterministic)
    if graph is not None:
        writer.graph = graph
        graph.bind("ace-epics", writer.epics)
        graph.bind("bacnet", writer.bacnet)
    data = value.model_dump(mode="json")
    term = writer.bacnet_value(data, datatype)
    if graph is None and len(writer.graph):
        raise ValueError("Structured or EPICS-only values require an accompanying graph")
    return term


def from_graph(graph: Any, *, max_nodes: int = 1_000_000, **opts: Any) -> EpicsDocument:
    """Reconstruct a document using RDF list order and canonical lexical values (4.4)."""
    reader = _Reader(graph, max_nodes)
    documents = list(graph.subjects(reader.rdf.RDF.type, reader.epics.Document))
    if len(documents) != 1:
        raise failure("RDF must contain exactly one epics:Document", "RDF-DOCUMENT")
    subject = documents[0]
    data: dict[str, Any] = {
        "header": {"charset_code": int(reader.one(subject, reader.epics.headerCode))}
    }
    general = {}
    for key in ("vendor_name", "product_name", "product_model_number", "product_description"):
        general[key] = str(reader.one(subject, reader.epics[_camel(key)]))
    data["general"] = general
    for key in ("bibbs", "services", "object_types", "data_links", "character_sets", "objects"):
        head = reader.one(subject, reader.epics[_camel(key) + "Order"])
        data[key] = reader.sequence(head, frozenset({subject}))
    for key in ("special", "default_restrictions", "fail_times"):
        data[key] = reader.decode(reader.one(subject, reader.epics[_camel(key)]))
    return decode_document(data)


def dumps(
    doc: EpicsDocument, *, format: str = "turtle", deterministic: bool = False, **opts: Any
) -> str:
    """Write a queryable graph; deterministic mode uses stable skolem IRIs (Clause 4)."""
    graph = to_graph(doc, deterministic=deterministic, **opts)
    if deterministic and format in {"nt", "ntriples"}:
        return "\n".join(sorted(graph.serialize(format="nt").splitlines())) + "\n"
    if deterministic and format in {"turtle", "ttl"}:
        rdf = _rdf()
        namespaces = {
            "ace-epics": NAMESPACE,
            "bacnet": BACNET_NAMESPACE,
            "rdf": str(rdf.RDF),
            "xsd": str(rdf.XSD),
        }
        headers = [f"@prefix {prefix}: <{uri}> ." for prefix, uri in namespaces.items()]
        manager = graph.namespace_manager
        known = tuple(namespaces.values())

        def term(value: Any) -> str:
            if isinstance(value, rdf.URIRef) and not str(value).startswith(known):
                return value.n3()
            return value.n3(namespace_manager=manager)

        triples = sorted(f"{term(s)} {term(p)} {term(o)} ." for s, p, o in graph)
        return "\n".join([*headers, "", *triples]) + "\n"
    return graph.serialize(format=format)


def parse(data: str | bytes, *, format: str = "turtle", **opts: Any) -> ParseResult:
    """Read an RDF graph recoverably without inventing document facts (Clause 4)."""
    rdf = _rdf()
    graph = rdf.Graph()
    try:
        try:
            graph.parse(data=data, format=format)
        except Exception as exc:
            raise failure(f"Invalid RDF: {exc}", "RDF-INPUT") from exc
        try:
            doc = from_graph(graph, **opts)
        except (ValueError, TypeError, RecursionError) as exc:
            raise failure(f"Invalid RDF structure: {exc}", "RDF-SHAPE") from exc
        return ParseResult(doc, doc.diagnostics)
    except EpicsError as exc:
        return ParseResult(None, exc.diagnostics)


def loads(data: str | bytes, *, raise_on_error: bool = True, **opts: Any) -> EpicsDocument:
    """Read an RDF document, raising collected failures by default (Clause 4)."""
    return document_from_result(parse(data, **opts), raise_on_error=raise_on_error)


def load(src: Path | str | IO[str] | IO[bytes], **opts: Any) -> EpicsDocument:
    """Read an RDF graph from a path or file object (Clause 4 interchange)."""
    data = Path(src).read_bytes() if isinstance(src, (str, Path)) else src.read()
    return loads(data, **opts)


def dump(doc: EpicsDocument, dst: Path | str | IO[str], **opts: Any) -> None:
    """Write RDF to a path or text file object (Clause 4 interchange)."""
    text = dumps(doc, **opts)
    if isinstance(dst, (str, Path)):
        Path(dst).write_text(text, encoding="utf-8")
    else:
        dst.write(text)
