import json
import os
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ace_epics.codecs.epics import loads, parse
from ace_epics.diagnostics import EpicsError, Severity
from ace_epics.model import GeneralInformation
from tests.fixtures_build_epics import full

BASE = Path(__file__).parents[2] / "fixtures/epics"
FILES = sorted(BASE.rglob("*.tpi"))


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(BASE)))
def test_corpus_snapshots_and_mode_diagnostics(path):
    expected = json.loads(path.with_suffix(".expected.json").read_text())
    diagnostics = json.loads(path.with_suffix(".expected_diagnostics.json").read_text())
    for mode in ["lenient", "strict"]:
        result = parse(path.read_bytes(), strict=mode == "strict")
        expected_codes = diagnostics[mode]
        if os.name == "nt":
            expected_codes = [code for code in expected_codes if code != "E-DBCS"]
        assert [d.code for d in result.diagnostics] == expected_codes
        assert result.document is not None
        if mode == "lenient":
            assert result.document.model_dump(mode="json", exclude={"source"}) == expected
        if any(d.severity == Severity.ERROR for d in result.diagnostics):
            with pytest.raises(EpicsError):
                loads(path.read_bytes(), strict=mode == "strict")
        else:
            assert loads(path.read_bytes(), strict=mode == "strict") == result.document


def test_full_exact_model_and_strictness():
    result = parse((BASE / "full.tpi").read_bytes(), strict=True)
    assert result.document is not None
    assert result.document == full()
    assert len(result.document.objects) == 30
    assert result.diagnostics == []
    assert result.document.device is not None
    prop = result.document.device.property("protocol-revision")
    assert prop is not None
    assert getattr(prop.value, "value", None) == 30
    assert result.document.supports_service("read-property", initiate=True, execute=True)


@pytest.mark.parametrize(
    "fixture,code",
    [
        ("missing_signature", "P-SIGNATURE"),
        ("missing_end", "P-END"),
        ("wrong_headers", "P-OBJECT-HEADERS"),
        ("unknown_restriction", "R-NAME"),
        ("missing_instance", "P-OBJECT-IDENTIFIER"),
        ("unbalanced_value", "P-VALUE-UNBALANCED"),
    ],
)
def test_explicit_error_recovery(fixture, code):
    result = parse((BASE / "negative" / (fixture + ".tpi")).read_bytes())
    assert result.has_errors
    assert code in [d.code for d in result.diagnostics]
    assert result.document is not None
    assert len(result.document.objects) >= 29


@pytest.mark.parametrize(
    "fixture,code",
    [
        ("line_endings", "E-LINE-ENDINGS"),
        ("signature_gap", "P-SIGNATURE-POSITION"),
        ("unquoted_general", "P-UNQUOTED-STRING"),
        ("baud_k", "P-BAUD-K"),
        ("integer_timer", "P-TIMER-INTEGER"),
        ("explicit_r", "P-READONLY-MARKER"),
        ("unknown_section", "P-UNKNOWN-SECTION"),
    ],
)
def test_leniency_promotes_to_strict_error(fixture, code):
    content = (BASE / "lenient" / (fixture + ".tpi")).read_bytes()
    loose = parse(content)
    strict = parse(content, strict=True)
    assert not loose.has_errors
    assert strict.has_errors
    assert next(d for d in loose.diagnostics if d.code == code).severity == Severity.WARNING
    assert next(d for d in strict.diagnostics if d.code == code).severity == Severity.ERROR


def test_missing_header_end_and_recovery_result():
    result = parse("arbitrary text")
    assert result.has_errors
    assert {"P-HEADER", "P-SIGNATURE", "P-END"} <= {d.code for d in result.diagnostics}
    assert loads("arbitrary text", raise_on_error=False).general == GeneralInformation(
        vendor_name="", product_name="", product_model_number="", product_description=""
    )
    invalid: Any = None
    assert parse(invalid).document is None


@settings(max_examples=10000, deadline=None)
@given(st.one_of(st.binary(max_size=2000), st.text(max_size=2000)))
def test_never_raises_arbitrary_input(content):
    result = parse(content)
    assert isinstance(result.diagnostics, list)


def test_unknown_character_set_retained_in_source_raw():
    text = (
        (BASE / "full.tpi").read_bytes().decode().replace("ISO 10646 (UTF-8)", "Custom Characters")
    )
    result = parse(text)
    assert result.document is not None and result.document.source is not None
    assert result.document.source.raw["character_sets"] == ["Custom Characters"]
    assert "P-CHARACTER-SET" in [d.code for d in result.diagnostics]


def test_multiline_after_comment_missing_value_and_marker_order():
    text = (BASE / "full.tpi").read_bytes().decode()
    text = text.replace(
        "present-value: 1.0 C",
        "Present Value: -- source comment\r\n        1.0 <minimum: 0.0> C",
        1,
    )
    result = parse(text)
    assert result.document is not None
    item = result.document.objects_of_type("analog-input")[0]
    entry = item.property("present-value")
    assert entry is not None and entry.access == "C" and entry.restrictions is not None
    assert entry.comment == "source comment"
    text = text.replace("1.0 <minimum: 0.0> C", "", 1)
    missing = parse(text)
    assert "P-PROPERTY-VALUE" in [d.code for d in missing.diagnostics]
    assert missing.document is not None
    assert missing.document.objects_of_type("analog-input")[0].has_property("status-flags")


def test_structurally_empty_document_collects_errors():
    result = parse("")
    assert result.has_errors and result.document is not None
    assert {"P-HEADER", "P-SIGNATURE", "P-END", "P-SECTIONS-INCOMPLETE"} <= {
        d.code for d in result.diagnostics
    }
