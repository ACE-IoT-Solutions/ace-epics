"""Frozen syntax-only value trees (135.1 Clauses 4.4 and 4.4.1)."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ace_epics.model.names import NamedToken


class Node(BaseModel):
    """Base for immutable, semantically comparable value syntax (135.1 Clause 4.4 and 4.4.1)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    def _semantic_key(self):
        def freeze(value):
            if isinstance(value, dict):
                unspecified_fields = {
                    "date": ("day", "month", "year"),
                    "time": ("hour", "minute", "second", "hundredth"),
                }
                if value.get("kind") in unspecified_fields:
                    value = dict(value)
                    for field in unspecified_fields[value["kind"]]:
                        if value[field] is None:
                            value[field] = {"kind": "wildcard"}
                if "canonical" in value:
                    return (("canonical", value["canonical"]),)
                return tuple(
                    (key, freeze(item))
                    for key, item in value.items()
                    if key
                    not in {
                        "text",
                        "short",
                        "quote",
                        "precision",
                        "trailing_comma",
                        "parenthesised",
                        "odd_length",
                    }
                )
            if isinstance(value, list):
                return tuple(freeze(item) for item in value)
            return value

        return freeze(self.model_dump())

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self._semantic_key() == other._semantic_key()

    def __hash__(self):
        return hash(self._semantic_key())


class NullValue(Node):
    """A null application value (135.1 Clause 4.4(b))."""

    kind: Literal["null"] = "null"


class BooleanValue(Node):
    """A Boolean value with its abbreviated spelling retained (135.1 Clause 4.4(c))."""

    kind: Literal["boolean"] = "boolean"
    value: bool
    short: bool = False


class IntegerValue(Node):
    """A signed or unsigned integer in untyped EPICS syntax (135.1 Clause 4.4(d))."""

    kind: Literal["integer"] = "integer"
    value: int


class RealValue(Node):
    """A finite decimal value with the original numeric text retained (135.1 Clause 4.4(e))."""

    kind: Literal["real"] = "real"
    value: Decimal
    text: str = ""

    @field_validator("value")
    @classmethod
    def finite_value(cls, value: Decimal) -> Decimal:
        """Reject non-finite numbers that have no permitted EPICS representation (135.1 Clause
        4.4 and 4.4.1).
        """
        if not value.is_finite():
            raise ValueError("EPICS real values must be finite")
        return value


class OctetStringValue(Node):
    """Raw octets with odd-length recovery metadata (135.1 Clause 4.4(f))."""

    kind: Literal["octet-string"] = "octet-string"
    value: bytes
    odd_length: bool = False

    @field_serializer("value", when_used="json")
    def serialize_bytes(self, value: bytes) -> str:
        """Serialize binary octets as interoperable hexadecimal JSON text (135.1 Clause 4.4 and
        4.4.1).
        """
        return value.hex().upper()

    @field_validator("value", mode="before")
    @classmethod
    def deserialize_bytes(cls, value):
        """Restore octets from hexadecimal interchange text or raw bytes (135.1 Clause 4.4 and
        4.4.1).
        """
        return bytes.fromhex(value) if isinstance(value, str) else value


class CharacterStringValue(Node):
    """A character string with its original opening quote retained (135.1 Clause 4.3 and 4.4(g))."""

    kind: Literal["character-string"] = "character-string"
    value: str
    quote: Literal['"', "'", "`"] = '"'


class EnumeratedValue(Node):
    """A normalized enumeration name and optional proprietary number (135.1 Clause 4.4(i))."""

    kind: Literal["enumerated"] = "enumerated"
    name: NamedToken
    proprietary_number: int | None = None


class EmptyElement(Node):
    """An omitted positional field inside a generic constructed group (135.1 Clause 4.4 and
    4.4.1).
    """

    kind: Literal["empty"] = "empty"


class UnspecifiedValue(Node):
    """An unspecified property or bit value denoted by a question mark (135.1 Clause 4.4 and
    4.4.1).
    """

    kind: Literal["unspecified"] = "unspecified"


class WildcardValue(Node):
    """An asterisk wildcard, standalone or in a date/time field (135.1 Clause 4.4 and 4.4.1)."""

    kind: Literal["wildcard"] = "wildcard"


DateField = int | None | WildcardValue


class DateValue(Node):
    """Date fields with an optional weekday and independent wildcards (135.1 Clause 4.4(j))."""

    kind: Literal["date"] = "date"
    weekday: DateField = None
    day: DateField
    month: DateField
    year: DateField
    parenthesised: bool = True


class TimeValue(Node):
    """Time fields and their original fractional precision (135.1 Clause 4.4(k))."""

    kind: Literal["time"] = "time"
    hour: DateField
    minute: DateField
    second: DateField = 0
    hundredth: DateField = 0
    precision: int = 2


class DateRangeValue(Node):
    """An inclusive pair of date endpoints in calendar syntax (135.1 Clause 4.4 and 4.4.1)."""

    kind: Literal["date-range"] = "date-range"
    start: DateValue
    end: DateValue


class ObjectIdentifierValue(Node):
    """An object type token or proprietary number with its instance (135.1 Clause 4.4(l))."""

    kind: Literal["object-identifier"] = "object-identifier"
    object_type: NamedToken | int
    instance: int | None


class ContextTaggedValue(Node):
    """A context tag number followed by its selected value (135.1 Clause 4.4.1(b))."""

    kind: Literal["context-tagged"] = "context-tagged"
    tag: int
    value: ValueNode


class GroupValue(Node):
    """A generic parenthesis or brace group with positional elements (135.1 Clause 4.4(m) and
    4.4.1(c)-(d)).
    """

    kind: Literal["group"] = "group"
    delimiter: Literal["{", "("]
    elements: list[ValueNode] = Field(default_factory=list)
    trailing_comma: bool = False


ValueNode = Annotated[
    NullValue
    | BooleanValue
    | IntegerValue
    | RealValue
    | OctetStringValue
    | CharacterStringValue
    | EnumeratedValue
    | DateValue
    | TimeValue
    | DateRangeValue
    | ObjectIdentifierValue
    | ContextTaggedValue
    | GroupValue
    | EmptyElement
    | UnspecifiedValue
    | WildcardValue,
    Field(discriminator="kind"),
]
ContextTaggedValue.model_rebuild()
GroupValue.model_rebuild()
