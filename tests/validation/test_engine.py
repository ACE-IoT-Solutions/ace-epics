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
