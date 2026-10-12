"""Pluggable BACnet 135 knowledge used by 135.1 Clause 5 rules."""

from collections.abc import Mapping
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


def normalize_name(name: str) -> str:
    """Normalize factual BACnet names for Clause 5 comparisons (decision D11)."""
    canonical = "-".join(name.lower().replace("_", " ").replace("-", " ").split())
    aliases = {
        "max-master": "max-manager",
        "slave-proxy-enable": "subordinate-proxy-enable",
        "manual-slave-address-binding": "manual-subordinate-address-binding",
        "auto-slave-discovery": "auto-subordinate-discovery",
        "slave-address-binding": "subordinate-address-binding",
    }
    return aliases.get(canonical, canonical)


class KnowledgeModel(BaseModel):
    """Extensible factual data retaining source annotations (Clause 5)."""

    model_config = ConfigDict(extra="allow", frozen=True)


class PropertySpec(KnowledgeModel):
    """Clause 12 property requirements used by C5-09 through C5-20."""

    requirement: Literal["required", "optional", "conditional"]
    datatype: str
    access: Literal["R", "W", "C"] = "R"
    read_only: bool = False
    introduced_rev: int | None = None
    deprecated_rev: int | None = None
    removed_rev: int | None = None
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    range: dict[str, Any] | None = None
    min_range: dict[str, Any] | None = None


class ObjectDefinition(KnowledgeModel):
    """A sourced revision-specific Clause 12 object definition."""

    source: str
    object_type: str
    revision: int
    coverage_min_revision: int | None = None
    properties: dict[str, PropertySpec]
    historical_properties: dict[str, PropertySpec] = Field(default_factory=dict)


class ServiceRequirement(KnowledgeModel):
    """Required Annex K service direction for C5-04 and C5-05."""

    name: str
    initiate: bool = False
    execute: bool = False
    conditions: list[dict[str, Any]] = Field(default_factory=list)


class BibbDefinition(KnowledgeModel):
    """Annex K requirements for Clause 5(a)-(e), retaining conditional obligations."""

    services: list[ServiceRequirement] = Field(default_factory=list)
    object_types: list[str] = Field(default_factory=list)
    requires_bibbs: list[str] = Field(default_factory=list)
    object_type_alternatives: list[list[str]] = Field(default_factory=list)
    conditional_requirements: list[dict[str, Any]] = Field(default_factory=list)


@runtime_checkable
class KnowledgeProvider(Protocol):
    """BACnet knowledge contract for Clause 5; empty/None means unavailable."""

    def object_types(self, revision: int | None) -> Mapping[str, int]:
        """BACnet object identifiers available at a revision (Clause5(f))."""
        ...

    def object_types_bit_count(self, revision: int | None) -> int | None:
        """Exact supported-object bit count at a revision (Clause5(l))."""
        ...

    def services(self, revision: int | None) -> Mapping[str, int]:
        """Supported-service bit positions at a revision (Clause5(e))."""
        ...

    def services_bit_count(self, revision: int | None) -> int | None:
        """Exact service bit count at a revision (Clause5(k))."""
        ...

    def property_identifiers(self) -> Mapping[str, int]:
        """BACnet property names and identifiers (Clause7.1.2)."""
        ...

    def bibb(self, name: str) -> BibbDefinition | None:
        """Sourced AnnexK BIBB requirements (Clause5(a) through5(e))."""
        ...

    def object_definition(self, object_type: str, revision: int | None) -> ObjectDefinition | None:
        """Verified object property definition at a revision (Clause5(i))."""
        ...

    def proprietary_object_required_properties(self) -> set[str]:
        """Required proprietary-object properties (135 Clause23.4.3)."""
        ...


@runtime_checkable
class CapabilityProvider(Protocol):
    """Optional capability declaration for Clause 5 rule prerequisites.

    Names identify available knowledge families, not complete revision coverage.
    Individual lookups still return unavailable facts as empty/None.
    """

    def capabilities(self) -> frozenset[str]:
        """Knowledge families this provider can supply for Clause 5, including custom names."""
        ...


class NullProvider:
    """No external knowledge: dependent Clause 5 checks must report SKIPPED."""

    def capabilities(self) -> frozenset[str]:
        """No external knowledge families are supplied for Clause 5."""
        return frozenset()

    def object_types(self, revision: int | None) -> Mapping[str, int]:
        """Unavailable object enumeration (C5-06)."""
        return {}

    def object_types_bit_count(self, revision: int | None) -> int | None:
        """Unavailable supported-object bit count (C5-14)."""
        return None

    def services(self, revision: int | None) -> Mapping[str, int]:
        """Unavailable service enumeration (C5-05)."""
        return {}

    def services_bit_count(self, revision: int | None) -> int | None:
        """Unavailable service bit count (C5-13)."""
        return None

    def property_identifiers(self) -> Mapping[str, int]:
        """Unavailable property enumeration (C5-16)."""
        return {}

    def bibb(self, name: str) -> BibbDefinition | None:
        """Unavailable BIBB definition (C5-01..05)."""
        return None

    def object_definition(self, object_type: str, revision: int | None) -> ObjectDefinition | None:
        """Unavailable object definition (C5-09..20)."""
        return None

    def proprietary_object_required_properties(self) -> set[str]:
        """Unavailable proprietary-object requirements (135 Clause 23.4.3)."""
        return set()
