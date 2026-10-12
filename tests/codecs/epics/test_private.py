"""Optional licensed Annex A smoke: local input only, never a committed extract."""

import os
from collections import Counter
from pathlib import Path

import pytest

from ace_epics.codecs.epics import parse
from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.validation import validate

EXPECTED = {
    "V-TIME-PRECISION": 44,
    "R-COLON": 16,
    "V-CLOSER": 9,
    "V-REAL-NOTATION": 4,
    "V-MISSING-COMMA": 3,
    "V-ODD-OCTETS": 3,
    "P-BAUD-K": 2,
    "P-UNKNOWN-DATA-LINK": 2,
    "V-BARE-DATE": 2,
    "R-BARE-DATE": 2,
    "P-READONLY-MARKER": 2,
    "V-TRAILING-COMMA": 2,
    "P-SECTION-BRACE": 1,
    "P-SECTIONS-INCOMPLETE": 1,
    "P-DATA-LINK": 1,
    "P-SPECIAL-UNKNOWN": 1,
    "P-VALUE-UNBALANCED": 1,
    "M-BIBB-NAME": 1,
    "P-ELLIPSIS": 1,
}


def test_private_annex_counts_and_known_diagnostics():
    directory = os.environ.get("ACE_EPICS_PRIVATE_FIXTURES")
    if not directory:
        pytest.skip("Set ACE_EPICS_PRIVATE_FIXTURES to licensed local fixture directory")
    path = Path(directory) / "annex-a.tpi"
    assert path.is_file(), (
        "Reconstruct annex-a.tpi privately from the licensed PDF; see CONTRIBUTING"
    )
    result = parse(path.read_bytes())
    assert result.document is not None
    assert len(result.document.objects) == 25
    assert sum(3 + len(obj.properties) for obj in result.document.objects) == 491
    assert Counter(d.code for d in result.diagnostics) == EXPECTED
    report = validate(result.document, JsonKnowledgeProvider())
    failed = {result.rule_id for result in report.results if result.outcome == "fail"}
    assert {"C5-07", "C5-08"} <= failed
