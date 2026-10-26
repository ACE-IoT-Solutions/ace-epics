"""Extension rules obey strictness and dependency graph semantics."""

from dataclasses import dataclass

import pytest

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.validation import validate


@dataclass
class CustomRule:
    id: str = "S-CUSTOM"
    clause: str = "4.5"
    severity: Severity = Severity.WARNING
    requires: frozenset[str] = frozenset()
    depends_on: tuple[str, ...] = ()

    def applies(self, ctx):
        return True

    def check(self, ctx):
        yield Diagnostic(
            code=self.id, severity=self.severity, clause=self.clause, message="Custom advisory"
        )


def test_strict_promotes_structural_warning(document, provider):
    assert validate(document, provider, rules=[CustomRule()]).results[0].outcome == "pass"
    strict = validate(document, provider, rules=[CustomRule()], strict=True)
    assert strict.results[0].outcome == "fail"
    assert strict.diagnostics[0].severity == Severity.ERROR


def test_dependency_cycle_is_rejected(document, provider):
    with pytest.raises(ValueError, match="cycle"):
        validate(document, provider, rules=[CustomRule(depends_on=("S-CUSTOM",))])


@pytest.mark.parametrize("rule", [f"C5-{n:02d}" for n in (9, 10, 11, 12, 15, 18, 19, 20)])
def test_mixed_object_knowledge_preserves_checked_scope(document, provider, monkeypatch, rule):
    definition = provider.object_definition
    monkeypatch.setattr(
        provider,
        "object_definition",
        lambda kind, revision: None if kind == "analog-output" else definition(kind, revision),
    )
    result = validate(document, provider, rules=[rule]).results[0]
    assert result.outcome == "partial"
    assert result.checked_objects == ["(device, 100)"]
    assert result.skipped_objects == ["(analog-output, 1)"]
    assert result.diagnostics[0].object_id == "(analog-output, 1)"
    monkeypatch.setattr(provider, "object_definition", lambda kind, revision: None)
    result = validate(document, provider, rules=[rule]).results[0]
    assert result.outcome == "skipped"
    assert result.checked_objects == []
    assert result.skipped_objects == [str(obj.identifier) for obj in document.objects]


def test_failure_takes_precedence_over_missing_object_knowledge(document, provider, monkeypatch):
    definition = provider.object_definition
    monkeypatch.setattr(
        provider,
        "object_definition",
        lambda kind, revision: None if kind == "analog-output" else definition(kind, revision),
    )
    document.device.properties = [
        prop
        for prop in document.device.properties
        if prop.name.canonical != "max-segments-accepted"
    ]
    report = validate(document, provider, rules=["C5-09"])
    result = report.results[0]
    assert result.outcome == "fail"
    assert result.checked_objects == ["(device, 100)"]
    assert result.skipped_objects == ["(analog-output, 1)"]
    assert report.exit_code() == 1
