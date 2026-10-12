import pytest

from ace_epics.diagnostics import Diagnostic, DiagnosticSink, EpicsError, Severity


def test_collect_sort_filter_raise_and_json():
    sink = DiagnosticSink()
    error = Diagnostic(code="C5-08", severity=Severity.ERROR, message="Missing object", line=9)
    warning = Diagnostic(code="W4.1", severity=Severity.WARNING, message="BOM", line=1, column=1)
    sink.add(error)
    sink.add(warning)
    assert sink.sorted() == [warning, error]
    assert sink.filtered(Severity.ERROR) == [error]
    assert error.model_dump(mode="json")["severity"] == "error"
    with pytest.raises(EpicsError) as caught:
        sink.raise_if_errors()
    assert caught.value.diagnostics == [warning, error]
    clean = DiagnosticSink()
    clean.add(warning)
    assert not clean.has_errors()
    clean.raise_if_errors()
