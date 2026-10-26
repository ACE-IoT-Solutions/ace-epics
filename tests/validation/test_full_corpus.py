"""The real native synthetic corpus reaches the shipped Clause5 provider."""

from datetime import UTC, datetime
from pathlib import Path

from ace_epics.codecs.epics import loads
from ace_epics.diagnostics import Severity
from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.validation import RULES, validate

ROOT = Path(__file__).resolve().parents[2]


def test_full_corpus_zero_errors_and_golden_reports():
    doc = loads((ROOT / "tests/fixtures/epics/full.tpi").read_bytes(), strict=True)
    assert len(doc.objects) == 30
    assert not doc.diagnostics
    report = validate(doc, JsonKnowledgeProvider())
    assert len(report.results) == 24
    assert {r.rule_id for r in report.results} == {r.id for r in RULES}
    assert not [d for d in report.diagnostics if d.severity == Severity.ERROR]
    # Missing object tables and externally determined feature conditions remain visible.
    assert any(result.outcome == "partial" for result in report.results)
    report.run_at = datetime(2026, 1, 1, tzinfo=UTC)
    snapshots = ROOT / "tests/snapshots/validation"
    assert report.to_json() + "\n" == (snapshots / "full.json").read_text()
    assert report.to_markdown() == (snapshots / "full.md").read_text()
