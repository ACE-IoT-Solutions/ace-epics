"""Run public CLI entry points in subprocesses against invented documents."""

import json
import subprocess
import sys

import pytest

from ace_epics.codecs import json as json_codec


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "ace_epics.cli", *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def source(tmp_path, document):
    path = tmp_path / "synthetic.json"
    json_codec.dump(document, path)
    return path


def test_version_inspect_and_selected_validation(source):
    version = run("--version")
    assert version.returncode == 0 and "ace-epics 0.0.1" in version.stdout
    objects = run("inspect", source, "--objects")
    assert objects.returncode == 0 and "(device, 100)" in objects.stdout
    prop = run("inspect", source, "--object", "analog-output,1", "--property", "present-value")
    assert prop.returncode == 0 and "present-value: 50 [W]" in prop.stdout
    report = run("validate", source, "--rules", "C5-17", "--format", "json")
    assert report.returncode == 0
    payload = json.loads(report.stdout)
    assert payload["results"][0]["outcome"] == "pass"
    assert "parse_diagnostics" in payload
    markdown = run("validate", source, "--rules", "C5-17", "--format", "markdown")
    assert markdown.returncode == 0 and "| C5-17 |" in markdown.stdout


def test_conversion_all_formats_and_native_formatting(source, tmp_path):
    current = source
    for suffix in ("yaml", "ttl", "tpi", "json"):
        target = tmp_path / ("converted." + suffix)
        result = run("convert", current, target)
        assert result.returncode == 0, result.stderr
        current = target
    native = tmp_path / "converted.tpi"
    assert run("fmt", native, "--in-place").returncode == 0
    formatted = tmp_path / "formatted.tpi"
    assert run("fmt", native, "-o", formatted, "--preserve").returncode == 0
    stdout = run("fmt", native)
    assert stdout.returncode == 0 and stdout.stdout.startswith("PICS 0")
    assert native.read_bytes() == formatted.read_bytes()


def test_error_exit_and_structured_parse_error(source, tmp_path, document):
    from ace_epics.values import IntegerValue

    document.device.property("max-segments-accepted").value = IntegerValue(value=1)
    json_codec.dump(document, source)
    report = run("validate", source, "--rules", "C5-17", "--format", "json")
    assert report.returncode == 2
    assert json.loads(report.stdout)["results"][0]["outcome"] == "fail"
    malformed = tmp_path / "malformed.tpi"
    malformed.write_text("broken")
    error = run("validate", malformed, "--format", "json")
    assert error.returncode == 2
    assert json.loads(error.stdout)["parse_diagnostics"]
    assert run("convert", source, tmp_path / "unknown.blob").returncode == 2
    assert run("inspect", source, "--object", "device,999").returncode == 2


def test_warning_policy(source, document):
    from ace_epics.model import ObjectTypeSupport
    from ace_epics.model.names import NamedToken

    document.object_types.append(ObjectTypeSupport(name=NamedToken.model_validate("file")))
    json_codec.dump(document, source)
    assert run("validate", source, "--rules", "C5-07").returncode == 0
    assert run("validate", source, "--rules", "C5-07", "--warnings-as-errors").returncode == 1


def test_published_artifacts():
    result = run("schema")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["$id"]
    ontology = run("ontology")
    assert ontology.returncode == 0, ontology.stderr
    assert "https://w3id.org/ace-epics#" in ontology.stdout
