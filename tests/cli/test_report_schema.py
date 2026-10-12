"""Validate actual subprocess reports against the public CLI JSON envelope contract."""

import copy
import json

import jsonschema
import pytest

from ace_epics.codecs import json as json_codec
from tests.cli.test_cli import run
from tests.validation.conftest import integer, set_value

DIAGNOSTIC = {
    "type": "object",
    "required": ["code", "severity", "message", "caused_by"],
    "additionalProperties": False,
    "properties": {
        "code": {"type": "string", "minLength": 1},
        "severity": {"enum": ["error", "warning", "info", "skipped"]},
        "message": {"type": "string", "minLength": 1},
        "clause": {"type": ["string", "null"]},
        "line": {"type": ["integer", "null"], "minimum": 1},
        "column": {"type": ["integer", "null"], "minimum": 1},
        **{name: {"type": ["string", "null"]} for name in ("section", "object_id", "property")},
        "caused_by": {"type": "array", "items": {"type": "string"}},
    },
}
RULE = {
    "type": "object",
    "required": ["rule_id", "clause", "outcome", "diagnostics"],
    "additionalProperties": False,
    "properties": {
        "rule_id": {"type": "string", "minLength": 1},
        "clause": {"type": "string"},
        "outcome": {"enum": ["pass", "fail", "skipped", "not_applicable"]},
        "diagnostics": {"type": "array", "items": DIAGNOSTIC},
    },
}
ENVELOPE = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "oneOf": [
        {
            "type": "object",
            "required": ["document_id", "tool_version", "run_at", "results", "parse_diagnostics"],
            "additionalProperties": False,
            "properties": {
                "document_id": {
                    "type": "object",
                    "required": ["vendor", "product", "model"],
                    "additionalProperties": False,
                    "properties": {
                        key: {"type": "string"} for key in ("vendor", "product", "model")
                    },
                },
                "tool_version": {"type": "string", "minLength": 1},
                "run_at": {"type": "string", "format": "date-time"},
                "results": {"type": "array", "items": RULE},
                "parse_diagnostics": {"type": "array", "items": DIAGNOSTIC},
            },
        },
        {
            "type": "object",
            "required": ["results", "parse_diagnostics"],
            "additionalProperties": False,
            "properties": {
                "results": {"type": "array", "maxItems": 0},
                "parse_diagnostics": {
                    "type": "array",
                    "minItems": 1,
                    "items": DIAGNOSTIC,
                    "contains": {
                        "type": "object",
                        "required": ["severity"],
                        "properties": {"severity": {"const": "error"}},
                    },
                },
            },
        },
    ],
}
VALIDATOR = jsonschema.Draft202012Validator(ENVELOPE, format_checker=jsonschema.FormatChecker())


@pytest.mark.parametrize("failure", [False, True])
def test_validation_success_and_failure_envelopes(tmp_path, document, failure):
    if failure:
        set_value(document.device, "max-segments-accepted", integer(1))
    path = tmp_path / "report.json"
    json_codec.dump(document, path)
    command = run("validate", path, "--rules", "C5-17", "--format", "json")
    assert command.returncode == (2 if failure else 0)
    payload = json.loads(command.stdout)
    VALIDATOR.validate(payload)
    assert payload["results"][0]["outcome"] == ("fail" if failure else "pass")
    malformed = copy.deepcopy(payload)
    malformed["results"][0]["outcome"] = "unexpected"
    assert not VALIDATOR.is_valid(malformed)


def test_parse_failure_envelope_and_diagnostic_types(tmp_path):
    path = tmp_path / "malformed.tpi"
    path.write_text("broken")
    command = run("validate", path, "--format", "json")
    assert command.returncode == 2
    payload = json.loads(command.stdout)
    VALIDATOR.validate(payload)
    assert payload["results"] == []
    malformed = copy.deepcopy(payload)
    malformed["parse_diagnostics"][0]["severity"] = "fatal"
    assert not VALIDATOR.is_valid(malformed)
    malformed = copy.deepcopy(payload)
    del malformed["parse_diagnostics"][0]["message"]
    assert not VALIDATOR.is_valid(malformed)
