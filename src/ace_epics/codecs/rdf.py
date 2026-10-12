"""Ordered, queryable RDF interchange for ASHRAE 135.1 Clause 4 documents."""

import hashlib
import importlib
import json
import re
from datetime import date, time
from pathlib import Path
from typing import IO, Any
from urllib.parse import quote
from uuid import uuid4

from ace_epics.diagnostics import EpicsError
from ace_epics.model.document import EpicsDocument

from ._interchange import VALUES, decode_document, document_data, failure
from .base import ParseResult, document_from_result
from .errors import MissingExtraError

name = "rdf"
extensions = (".ttl", ".nt", ".jsonld")
media_type = "text/turtle"
NAMESPACE = "https://w3id.org/ace-epics#"
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
        self.graph.bind("epics", self.epics)
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
        if cls == "Object":
            identifier = value["identifier"]
            self.graph.add((node, self.epics.objectType, self.literal(identifier["object_type"])))
            self.graph.add((node, self.epics.instance, self.literal(identifier["instance"])))
        return node

    def read_list(self, head: Any):
        while head != self.rdf.RDF.nil:
            yield self.graph.value(head, self.rdf.RDF.first)
            head = self.graph.value(head, self.rdf.RDF.rest)

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
    data = document_data(doc)
    if base_iri is None:
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        base_iri = f"urn:ace-epics:{digest}" if deterministic else f"urn:uuid:{uuid4()}"
    writer = _Writer(base_iri, deterministic)
    subject = writer.rdf.URIRef(base_iri)
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
            for obj in values:
                identifier = obj["identifier"]
                type_name = quote(str(identifier["object_type"]), safe="")
                node = writer.rdf.URIRef(f"{base_iri}/object/{type_name}/{identifier['instance']}")
                properties = obj.pop("properties")
                writer.encode(obj, "objects", node)
                property_nodes = []
                for prop in properties:
                    prop_node = writer.rdf.URIRef(f"{node}/{quote(prop['name'], safe='')}")
                    writer.encode(prop, "properties", prop_node)
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
    return writer.graph


class _Reader:
    def __init__(self, graph: Any, max_nodes: int) -> None:
        self.rdf = _rdf()
        self.epics = self.rdf.Namespace(NAMESPACE)
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
            if term == "datatypeKey":
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
        return result


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
    if deterministic and format in {"turtle", "ttl", "nt", "ntriples"}:
        triples = sorted(graph.serialize(format="nt").splitlines())
        # Sorted N-Triples is valid Turtle as well and independent of serializer ordering.
        return "\n".join(triples) + "\n"
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
