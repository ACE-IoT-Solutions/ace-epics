"""Read-only EPICS queries for consistency checks and Clause 7 test tooling."""

import contextlib
import json
from collections import defaultdict
from typing import Any

from ace_epics.knowledge import KnowledgeProvider, NullProvider
from ace_epics.knowledge.provider import normalize_name
from ace_epics.model import (
    Access,
    EpicsDocument,
    ObjectIdentifier,
    PropertyEntry,
    Restrictions,
    TestObject,
)
from ace_epics.model.names import NamedToken
from ace_epics.values import (
    BooleanValue,
    CharacterStringValue,
    EnumeratedValue,
    GroupValue,
    ObjectIdentifierValue,
    UnspecifiedValue,
    ValueNode,
)


def primitive(value: ValueNode | None) -> Any:
    """Decode scalar/group nodes for Clause 5 checks without guessing datatypes."""
    if value is None:
        return None
    kind = value.kind
    if kind == "unspecified":
        return None
    if isinstance(value, EnumeratedValue):
        return value.name.canonical
    if isinstance(value, ObjectIdentifierValue):
        if value.instance is None:
            return None
        return ObjectIdentifier(object_type=value.object_type, instance=value.instance)
    if isinstance(value, GroupValue):
        return [primitive(element) for element in value.elements]
    return getattr(value, "value", None)


class Query:
    """Facade over a document for 135.1 Clauses 5 and 7.1/7.2."""

    def __init__(self, document: EpicsDocument, provider: KnowledgeProvider | None = None) -> None:
        self.document = document
        self.provider = provider if provider is not None else NullProvider()

    def value(self, obj: TestObject | None, name: str) -> ValueNode | None:
        """Look up listed values and the three object header values (Clause 7.1.1)."""
        if obj is None:
            return None
        canonical = normalize_name(name)
        prop = next(
            (p for p in obj.properties if normalize_name(p.name.canonical) == canonical), None
        )
        if prop is not None:
            return prop.value
        if canonical == "object-name":
            return CharacterStringValue(value=obj.name)
        if canonical == "object-identifier":
            return ObjectIdentifierValue(
                object_type=obj.identifier.object_type, instance=obj.identifier.instance
            )
        if canonical == "object-type":
            if isinstance(obj.object_type, int):
                return EnumeratedValue(
                    name=NamedToken.model_validate(f"proprietary-object-type-{obj.object_type}"),
                    proprietary_number=obj.object_type,
                )
            return EnumeratedValue(name=obj.object_type)
        return None

    def _entry(self, obj: TestObject, prop: str) -> PropertyEntry | None:
        canonical = normalize_name(prop)
        entry = next(
            (p for p in obj.properties if normalize_name(p.name.canonical) == canonical), None
        )
        if entry is not None:
            return entry
        value = self.value(obj, canonical)
        if value is None:
            return None
        metadata = obj.header_metadata.get(canonical)
        kwargs = (
            {
                field: getattr(metadata, field)
                for field in ("access", "restrictions", "comment", "not_readable")
            }
            if metadata
            else {}
        )
        return PropertyEntry(name=NamedToken.model_validate(canonical), value=value, **kwargs)

    @property
    def protocol_revision(self) -> int | None:
        """Device.Protocol_Revision when represented as an Unsigned (Clause 5)."""
        value = primitive(self.value(self.document.device, "protocol-revision"))
        return value if type(value) is int and value >= 0 else None

    def bits(self, name: str) -> list[bool | None] | None:
        """Decode a Boolean/unspecified bit group, retaining bit length (Clause 5)."""
        node = self.value(self.document.device, name)
        if not isinstance(node, GroupValue) or not all(
            isinstance(element, (BooleanValue, UnspecifiedValue)) for element in node.elements
        ):
            return None
        return [
            element.value if isinstance(element, BooleanValue) else None
            for element in node.elements
        ]

    @property
    def services_supported_bits(self) -> list[bool | None] | None:
        """Device.Protocol_Services_Supported bit vector (C5-05, C5-13)."""
        return self.bits("protocol-services-supported")

    @property
    def object_types_supported_bits(self) -> list[bool | None] | None:
        """Device.Protocol_Object_Types_Supported bit vector (C5-06, C5-14)."""
        return self.bits("protocol-object-types-supported")

    @property
    def object_list(self) -> list[ObjectIdentifier] | None:
        """Decode Device.Object_List, returning None for unavailable values (C5-08)."""
        value = primitive(self.value(self.document.device, "object-list"))
        if not isinstance(value, list) or not all(isinstance(v, ObjectIdentifier) for v in value):
            return None
        return value

    def access(self, obj: TestObject, prop: str) -> Access:
        """Declared R/W/C access for a listed property (Clause 7.2)."""
        entry = self._entry(obj, prop)
        if entry is None:
            raise KeyError(prop)
        return entry.access

    def is_writable(self, obj: TestObject, prop: str) -> bool:
        """Both W and C participate in writable-property tests (Clause 7.2.2)."""
        return self.access(obj, prop) in {Access.W, Access.C}

    def is_conditionally_writable(self, obj: TestObject, prop: str) -> bool:
        """Whether access depends on runtime state (Clause 7.2.2)."""
        return self.access(obj, prop) == Access.C

    def is_read_only(self, obj: TestObject, prop: str) -> bool:
        """Whether the EPICS declares read-only access (Clause 7.2.3)."""
        return self.access(obj, prop) == Access.R

    def is_readable(self, obj: TestObject, prop: str) -> bool:
        """Whether ReadProperty access is declared available (Clause 7.1.1)."""
        entry = self._entry(obj, prop)
        return entry is not None and not entry.not_readable

    def datatype(self, obj: TestObject, prop: str) -> str | None:
        """Prefer sourced datatype metadata for Clause 7.2, otherwise infer the syntactic kind."""
        definition = self.provider.object_definition(str(obj.object_type), self.protocol_revision)
        if definition is not None and normalize_name(prop) in definition.properties:
            return definition.properties[normalize_name(prop)].datatype
        node = self.value(obj, prop)
        return node.kind if node is not None else None

    def limits(self, obj: TestObject, prop: str) -> Restrictions:
        """Resolve property overrides over datatype defaults and standard bounds (7.2.1)."""
        from decimal import Decimal

        from ace_epics.values import IntegerValue, RealValue

        entry = self._entry(obj, prop)
        if entry is None:
            raise KeyError(prop)
        definition = self.provider.object_definition(str(obj.object_type), self.protocol_revision)
        spec = definition.properties.get(normalize_name(prop)) if definition else None
        fields: dict[str, Any] = {}
        if spec is not None and spec.range:
            for bound, key in (("minimum", "min"), ("maximum", "max")):
                val = (
                    obj.identifier.instance
                    if spec.range.get("equals_object_instance")
                    else spec.range.get(key)
                )
                if f"{key}_property" in spec.range:
                    val = primitive(self.value(obj, spec.range[f"{key}_property"]))
                if type(val) is int:
                    fields[bound] = IntegerValue(value=val)
                elif isinstance(val, (float, str)):
                    with contextlib.suppress(ValueError):
                        fields[bound] = RealValue(value=Decimal(str(val)), text=str(val))
            datatype_name = normalize_name(spec.datatype)
            length_field = (
                "maximum_length_array"
                if datatype_name.startswith("bacnetarray")
                else "maximum_length_list"
                if datatype_name.startswith("list")
                else "maximum_length_string"
                if datatype_name in {"characterstring", "octetstring"}
                else None
            )
            if length_field and "max_length" in spec.range:
                fields[length_field] = spec.range["max_length"]
        result = Restrictions(**fields)
        datatype = normalize_name(self.datatype(obj, prop) or "")
        key = {
            "unsigned": "unsigned_integer",
            "integer": "signed_integer",
            "signed": "signed_integer",
            "octetstring": "octet_string",
            "characterstring": "character_string",
            "group": "list",
        }.get(datatype, datatype.replace("-", "_"))
        if datatype.startswith("bacnetarray"):
            key = "variable_length_array"
        elif datatype.startswith("list"):
            key = "list"
        default = (
            getattr(self.document.default_restrictions, key, None)
            if entry.access in {Access.W, Access.C}
            else None
        )
        for override in (default, entry.restrictions):
            if override is not None:
                from ace_epics.model.restrictions import merge

                result = merge(result, override)
        return result

    def array_length(self, obj: TestObject, prop: str) -> int | None:
        """Element count corresponds to array index zero semantics (Clause 7.1.1)."""
        value = self.value(obj, prop)
        return len(value.elements) if isinstance(value, GroupValue) else None

    def expected_property_list(self, obj: TestObject) -> set[NamedToken]:
        """Listed property names excluding four special properties (Clause 7.1.3)."""
        excluded = {"object-name", "object-type", "object-identifier", "property-list"}
        return {
            NamedToken.model_validate(normalize_name(entry.name.canonical))
            for entry in obj.properties
            if entry.name.canonical not in excluded
        }

    def variants(self, object_type: str) -> list[list[TestObject]]:
        """Group by property set, access, readability, and effective limits (Clause 7.1.2)."""
        groups: dict[str, list[TestObject]] = defaultdict(list)
        for obj in self.document.objects_of_type(object_type):
            names = [entry.name.canonical for entry in obj.properties]
            names.extend(("object-identifier", "object-name", "object-type"))
            entries = [self._entry(obj, prop) for prop in names]
            signature = sorted(
                (
                    normalize_name(entry.name.canonical),
                    str(entry.access),
                    entry.not_readable,
                    self.limits(obj, entry.name.canonical).model_dump(mode="json"),
                )
                for entry in entries
                if entry is not None
            )
            groups[json.dumps(signature, sort_keys=True)].append(obj)
        return list(groups.values())

    @staticmethod
    def is_unspecified(value: ValueNode) -> bool:
        """An unspecified value is distinct from NULL or missing (Clause 7.1.1)."""
        return value.kind == "unspecified"
