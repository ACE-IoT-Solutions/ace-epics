"""Ordered test objects and property declarations (Clause 4.5.10)."""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, model_validator

from ace_epics.values import ValueNode

from .base import EpicsModel
from .names import NamedToken, normalize_name
from .restrictions import Restrictions

ObjectType = NamedToken | Annotated[int, Field(strict=True, ge=128)]


class ObjectIdentifier(EpicsModel):
    """An object type and its 22-bit instance number (4.4l, 4.5.10)."""

    object_type: ObjectType = Field(description="Standard name or proprietary number (4.4l).")
    instance: Annotated[int, Field(strict=True, ge=0, le=4194303)] = Field(
        description="22-bit instance (4.4l)."
    )

    @property
    def is_proprietary(self) -> bool:
        """Whether the type is a proprietary numeric identifier (4.4l)."""
        return isinstance(self.object_type, int)

    def __str__(self) -> str:
        name = f"proprietary {self.object_type}" if self.is_proprietary else str(self.object_type)
        return f"({name}, {self.instance})"


class Access(StrEnum):
    """EPICS access flags; no native marker means R (4.5.10)."""

    R = "R"
    W = "W"
    C = "C"


class PropertyMetadata(EpicsModel):
    """Non-value property declarations, including object headers (Clause 4.5.10)."""

    access: Access = Field(default=Access.R, description="Access marker (4.5.10).")
    restrictions: Restrictions | None = Field(
        default=None, description="Instance restrictions (4.4.2)."
    )
    comment: str | None = Field(default=None, description="Trailing comment (4.3).")
    not_readable: bool = Field(default=False, description="ReadProperty extension marker (7.1.1).")


class PropertyEntry(EpicsModel):
    """A value, access declaration, restrictions, and optional comment (4.5.10)."""

    name: NamedToken = Field(description="Property name (4.5.10).")
    value: ValueNode = Field(description="Property value node (4.4, 4.5.10).")
    access: Access = Field(
        default=Access.R, description="Writable or conditionally writable marker (4.5.10)."
    )
    restrictions: Restrictions | None = Field(
        default=None, description="Instance restrictions (4.4.2)."
    )
    comment: str | None = Field(default=None, description="Trailing comment (4.3).")
    not_readable: bool = Field(
        default=False, description="Unavailable through ReadProperty; extension marker (7.1.1)."
    )


class TestObject(EpicsModel):
    """The three object headers and ordered subsequent properties (4.5.10)."""

    __test__ = False
    identifier: ObjectIdentifier = Field(
        alias="object-identifier", description="Object identifier header (4.5.10)."
    )
    name: str = Field(alias="object-name", description="Object name header (4.5.10).")
    object_type: ObjectType = Field(alias="object-type", description="Object type header (4.5.10).")
    header_metadata: dict[str, PropertyMetadata] = Field(
        default_factory=dict,
        description="Nondefault metadata for the three object headers (4.5.10).",
    )
    properties: list[PropertyEntry] = Field(
        default_factory=list, description="Ordered properties after headers (4.5.10)."
    )

    @model_validator(mode="after")
    def consistent_headers_and_properties(self):
        """Enforce matching types, proprietary shape, and unique properties (4.5.10)."""
        headers = {"object-identifier", "object-name", "object-type"}
        if set(self.header_metadata) - headers:
            raise ValueError("header_metadata keys must name one of the three object headers")
        self.header_metadata = {
            key: value for key, value in self.header_metadata.items() if value != PropertyMetadata()
        }
        if self.object_type != self.identifier.object_type:
            raise ValueError("object-type does not match object-identifier type")
        if self.identifier.is_proprietary and self.properties:
            raise ValueError("proprietary objects carry only the three header properties in EPICS")
        names = [entry.name.canonical for entry in self.properties]
        if len(names) != len(set(names)):
            raise ValueError("duplicate property name")
        if set(names) & {"object-identifier", "object-name", "object-type"}:
            raise ValueError("object header properties must not be repeated in properties")
        return self

    def property(self, name: str | NamedToken) -> PropertyEntry | None:
        """Find a listed property by normalized name (4.5.10)."""
        canonical = name.canonical if isinstance(name, NamedToken) else normalize_name(name)
        return next((entry for entry in self.properties if entry.name.canonical == canonical), None)

    def has_property(self, name: str | NamedToken) -> bool:
        """Whether a property is listed after the object headers (4.5.10)."""
        return self.property(name) is not None

    def property_names(self) -> set[NamedToken]:
        """Return the normalized listed-property set (4.5.10)."""
        return {entry.name for entry in self.properties}
