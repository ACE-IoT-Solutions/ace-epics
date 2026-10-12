"""Dependency-aware consistency-validation engine (135.1 Clause 5)."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.knowledge import JsonKnowledgeProvider, KnowledgeProvider
from ace_epics.model import EpicsDocument

from .query import Query
from .report import RuleResult, ValidationReport


@dataclass
class Context:
    """Memoized document, query, and external knowledge for Clause 5 rules."""

    document: EpicsDocument
    provider: KnowledgeProvider
    strict: bool = False
    memo: dict[str, Any] = field(default_factory=dict)
    query: Query = field(init=False)

    def __post_init__(self) -> None:
        self.query = Query(self.document, self.provider)


class Rule(Protocol):
    """Contract for built-in or caller-provided Clause 5 rules."""

    @property
    def id(self) -> str:
        """Stable rule identifier for Clause5 and structural checks."""
        ...

    @property
    def clause(self) -> str:
        """Standard clause owning this Clause5 check."""
        ...

    @property
    def severity(self) -> Severity:
        """Default finding severity for this Clause5 check."""
        ...

    @property
    def requires(self) -> frozenset[str]:
        """External knowledge capabilities needed by this Clause5 check."""
        ...

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Root-cause dependencies of this Clause5 check."""
        ...

    def applies(self, ctx: Context) -> bool:
        """Whether the Clause5 check is applicable to this document."""
        ...

    def check(self, ctx: Context) -> Iterable[Diagnostic]:
        """Yield structured Clause5 findings from the context."""
        ...


def validate(
    doc: EpicsDocument,
    provider: KnowledgeProvider | None = None,
    *,
    rules: Iterable[str | Rule] | None = None,
    strict: bool = False,
) -> ValidationReport:
    """Execute selected Clause 5 checks; unavailable facts explicitly yield SKIPPED."""
    from .rules import RULES

    registry = {rule.id: rule for rule in RULES}
    selected = (
        list(RULES) if rules is None else [registry[r] if isinstance(r, str) else r for r in rules]
    )
    ids = [rule.id for rule in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("Rules must have unique identifiers")
    ordered: list[Rule] = []
    visiting: set[str] = set()
    completed: set[str] = set()
    selection = {rule.id: rule for rule in selected}

    def visit(rule: Rule) -> None:
        if rule.id in completed:
            return
        if rule.id in visiting:
            raise ValueError(f"Rule dependency cycle at {rule.id}")
        visiting.add(rule.id)
        for dependency in rule.depends_on:
            if dependency in selection:
                visit(selection[dependency])
        visiting.remove(rule.id)
        completed.add(rule.id)
        ordered.append(rule)

    for rule in selected:
        visit(rule)
    ctx = Context(doc, provider if provider is not None else JsonKnowledgeProvider(), strict)
    report = ValidationReport(
        document_id={
            "vendor": doc.general.vendor_name,
            "product": doc.general.product_name,
            "model": doc.general.product_model_number,
        }
    )
    failed: set[str] = set()
    capability_lookup = getattr(ctx.provider, "capabilities", None)
    available = capability_lookup() if capability_lookup is not None else None
    for rule in ordered:
        if not rule.applies(ctx):
            report.results.append(
                RuleResult(rule_id=rule.id, clause=rule.clause, outcome="not_applicable")
            )
            continue
        missing = rule.requires - available if available is not None else frozenset()
        if missing:
            findings = [
                Diagnostic(
                    code=rule.id,
                    clause=rule.clause,
                    severity=Severity.SKIPPED,
                    message=(
                        "Provider lacks required knowledge capabilities: "
                        + ", ".join(sorted(missing))
                    ),
                )
            ]
        else:
            findings = list(rule.check(ctx))
        causes = [dependency for dependency in rule.depends_on if dependency in failed]
        for finding in findings:
            if strict and rule.id.startswith("S-") and finding.severity == Severity.WARNING:
                finding.severity = Severity.ERROR
            finding.caused_by = list(dict.fromkeys([*finding.caused_by, *causes]))
        if any(d.severity == Severity.ERROR for d in findings):
            outcome = "fail"
            failed.add(rule.id)
        elif any(d.severity == Severity.SKIPPED for d in findings):
            outcome = "skipped"
        else:
            outcome = "pass"
        report.results.append(
            RuleResult(rule_id=rule.id, clause=rule.clause, outcome=outcome, diagnostics=findings)
        )
    return report
