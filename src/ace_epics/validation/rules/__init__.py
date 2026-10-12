"""Registry of all twenty Clause 5 and four structural consistency checks."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.knowledge.provider import normalize_name

from ..query import primitive

if TYPE_CHECKING:
    from ..engine import Context


@dataclass(frozen=True)
class ConsistencyRule:
    """A registered Clause 5 check with explicit dependencies and knowledge needs."""

    id: str
    clause: str
    description: str
    requires: frozenset[str] = frozenset()
    depends_on: tuple[str, ...] = ()
    severity: Severity = Severity.ERROR

    def applies(self, ctx: "Context") -> bool:
        """Property_List consistency only applies to revision14 and newer (5(n))."""
        return self.id != "C5-16" or (ctx.query.protocol_revision or 0) >= 14

    def finding(
        self,
        message: str,
        *,
        severity: Severity | None = None,
        object_id: str | None = None,
        prop: str | None = None,
    ) -> Diagnostic:
        """Build a located finding for a Clause 5 check."""
        return Diagnostic(
            code=self.id,
            clause=self.clause,
            message=message,
            severity=severity or self.severity,
            object_id=object_id,
            property=prop,
            section="Test Database",
        )

    def skipped(self, message: str) -> Diagnostic:
        """Missing knowledge never counts as a passing Clause 5 check."""
        return self.finding(message, severity=Severity.SKIPPED)

    def check(self, ctx: "Context") -> Iterable[Diagnostic]:
        """Dispatch this rule to its tier's implementation (Clause 5)."""
        from . import bibbs, objects, structural

        if self.id.startswith("S-") or self.id in {
            "C5-06",
            "C5-07",
            "C5-08",
            "C5-13",
            "C5-14",
            "C5-16",
            "C5-17",
        }:
            yield from structural.check(self, ctx)
        elif self.id in {f"C5-{n:02d}" for n in range(1, 6)}:
            yield from bibbs.check(self, ctx)
        else:
            yield from objects.check(self, ctx)


def name(value: Any) -> str:
    """Canonicalize object/property tokens for Clause 5 comparisons."""
    return normalize_name(value.canonical if hasattr(value, "canonical") else str(value))


def property_names(obj: Any) -> set[str]:
    """Include the three implicit object header properties (5(i))."""
    return {"object-identifier", "object-name", "object-type"} | {
        name(entry.name) for entry in obj.properties
    }


def scalar(ctx: "Context", obj: Any, prop: str) -> Any:
    """Retrieve a syntactic scalar for a Clause 5 precondition."""
    return primitive(ctx.query.value(obj, prop))


DESCRIPTIONS = [
    ("a", "BIBB-required object types are marked supported", "bibbs"),
    ("b", "BIBB-required object instances exist", "bibbs"),
    ("c", "BIBB-required object bits are set", "bibbs,object_types"),
    ("d", "BIBB-required service directions are supported", "bibbs"),
    ("e", "BIBB-required executed service bits are set", "bibbs,services"),
    ("f", "Object support section matches Device supported bits", "object_types"),
    ("g", "Supported object types have database instances", ""),
    ("h", "Object_List matches the test database", ""),
    ("i", "All required object properties are present", "objects"),
    ("i", "Properties exist at the declared protocol revision", "objects"),
    ("i", "Conditional property requirements are satisfied", "objects"),
    ("j", "Required writable properties are marked W or C", "objects"),
    ("k", "Services bit string has the revision's exact length", "services"),
    ("l", "Object-types bit string has the revision's exact length", "object_types"),
    ("m", "Deprecated/removed properties obey the revision boundary", "objects"),
    ("n", "Property_List matches explicitly listed properties", ""),
    ("o", "Receiving segmentation accepts more than one segment", ""),
    ("p", "Required read-only properties are marked R", "objects"),
    ("q", "Specified values lie within standard bounds", "objects"),
    ("r", "Declared restrictions respect allowed and minimum bounds", "objects"),
]
RULES = (
    *tuple(
        ConsistencyRule(
            f"C5-{index:02d}",
            f"5({letter})",
            description,
            frozenset(filter(None, needs.split(","))),
            ("S-02", "C5-06") if index in {3, 7} else ("S-02",),
        )
        for index, (letter, description, needs) in enumerate(DESCRIPTIONS, 1)
    ),
    ConsistencyRule("S-01", "4.5.10", "Object identifiers are unique"),
    ConsistencyRule("S-02", "5", "Exactly one Device object exists"),
    ConsistencyRule("S-03", "4.5.9", "Fail times are finite and non-negative"),
    ConsistencyRule("S-04", "4.4.2", "Restriction datatypes match their values"),
)

__all__ = ["RULES", "ConsistencyRule"]
