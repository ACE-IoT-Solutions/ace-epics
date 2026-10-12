"""Clause14 report serialization and CLI outcome policy."""

import json
from datetime import UTC, datetime

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.validation.report import RuleResult, ValidationReport


def test_report_roundtrip_summary_markdown_and_exit_policy():
    warning = Diagnostic(
        code="C5-07", clause="5(g)", severity=Severity.WARNING, message="File | absent\ntransient"
    )
    report = ValidationReport(
        run_at=datetime(2026, 1, 1, tzinfo=UTC),
        results=[
            RuleResult(rule_id="C5-07", clause="5(g)", outcome="pass", diagnostics=[warning]),
            RuleResult(rule_id="C5-14", clause="5(l)", outcome="skipped"),
        ],
    )
    assert report.summary() == {"pass": 1, "fail": 0, "skipped": 1, "not_applicable": 0}
    assert report.exit_code() == 0
    assert report.exit_code(warnings_as_errors=True) == 1
    assert ValidationReport.model_validate(json.loads(report.to_json())) == report
    assert "File \\| absent<br>transient" in report.to_markdown()
    report.results.append(
        RuleResult(
            rule_id="S-02",
            clause="5",
            outcome="fail",
            diagnostics=[Diagnostic(code="S-02", severity=Severity.ERROR, message="No Device")],
        )
    )
    assert report.exit_code() == 1
