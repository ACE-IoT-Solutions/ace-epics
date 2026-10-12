"""Curated checks of Clause 12 facts, distinct from the private extraction tool."""

import json
from pathlib import Path

import pytest

DATA = Path(__file__).parents[2] / "src/ace_epics/knowledge/data"
COUNTS = {
    "analog-input": 42,
    "analog-output": 47,
    "analog-value": 47,
    "binary-input": 39,
    "binary-output": 49,
    "binary-value": 46,
    "multi-state-input": 34,
    "multi-state-output": 41,
    "multi-state-value": 40,
    "device": 80,
    "file": 17,
    "notification-class": 25,
    "schedule": 31,
    "calendar": 12,
    "trend-log": 43,
}


def table(name):
    return json.loads((DATA / "objects" / f"{name}.json").read_text())


@pytest.mark.parametrize("name,count", COUNTS.items())
def test_complete_snapshot_and_resolved_identifiers(name, count):
    data = table(name)
    identifiers = json.loads((DATA / "property_identifiers.json").read_text())["values"]
    assert data["source"] == "ASHRAE 135-2024"
    assert data["object_type"] == name
    assert data["revision"] == 30
    assert data["coverage_min_revision"] == (
        29
        if name == "device"
        else 28
        if name
        in {
            "analog-input",
            "analog-output",
            "analog-value",
            "multi-state-input",
            "multi-state-value",
        }
        else 26
    )
    assert len(data["properties"]) == count
    assert set(data["properties"]) <= identifiers.keys()
    for prop, spec in data["properties"].items():
        assert spec["requirement"] in {"required", "optional", "conditional"}
        assert spec["access"] in {"R", "W", "C"}
        assert spec["datatype"]
        assert isinstance(spec["conditions"], list)
        for c in spec["conditions"]:
            if c["kind"] in {"all_or_none", "at_least_one"}:
                assert set(c["properties"]) <= data["properties"].keys()
        if spec.get("read_only"):
            assert spec["access"] == "R", prop
    assert data["properties"]["object-type"]["read_only"]
    assert data["properties"]["property-list"]["read_only"]
    assert data["properties"]["property-list"]["introduced_rev"] == 14


@pytest.mark.parametrize("name", ["analog", "binary", "multi-state"])
def test_input_output_value_access_and_commandability(name):
    inp = table(f"{name}-input")["properties"]
    out = table(f"{name}-output")["properties"]
    val = table(f"{name}-value")["properties"]
    assert inp["present-value"]["access"] == "C"
    assert {"kind": "writable_if", "property": "out-of-service", "equals": True} in inp[
        "present-value"
    ]["conditions"]
    assert out["present-value"]["access"] == "W"
    assert out["priority-array"]["requirement"] == "required"
    assert out["priority-array"]["array_length"] == 16
    assert out["priority-array"]["read_only"]
    assert val["priority-array"]["requirement"] == "conditional"
    assert {"kind": "required_if", "commandable": True} in val["priority-array"]["conditions"]
    assert val["present-value"]["access"] == "C"


def test_optional_readable_does_not_mean_read_only():
    props = table("analog-input")["properties"]
    assert props["description"]["access"] == "R"
    assert not props["description"].get("read_only")
    assert props["status-flags"]["read_only"]


def test_device_services_and_revision_facts():
    props = table("device")["properties"]
    assert props["protocol-revision"]["introduced_rev"] == 1
    assert props["authorization-server"]["introduced_rev"] == 29
    assert props["authorization-scope"]["introduced_rev"] == 29
    assert props["device-uuid"]["range"] == {"min_length": 16, "max_length": 16}
    assert {
        "kind": "required_if",
        "service": "subscribe-cov-property-multiple",
        "direction": "execute",
    } in props["active-cov-multiple-subscriptions"]["conditions"]
    assert props["backup-failure-timeout"]["access"] == "W"
    assert {"kind": "only_if", "feature": "segmentation"} in props["max-segments-accepted"][
        "conditions"
    ]


def test_conditional_groups_and_prose_ranges():
    props = table("binary-input")["properties"]
    assert props["change-of-state-count"]["min_range"] == {"min": 0, "max": 65535}
    assert {"kind": "all_or_none", "properties": ["inactive-text", "active-text"]} in props[
        "active-text"
    ]["conditions"]
    states = table("multi-state-input")["properties"]
    assert states["present-value"]["range"] == {"min": 1, "max_property": "number-of-states"}
    schedule = table("schedule")["properties"]
    assert schedule["priority-for-writing"]["range"] == {"min": 1, "max": 16}
    assert schedule["present-value"]["access"] == "C"
    assert {
        "kind": "at_least_one",
        "properties": ["weekly-schedule", "exception-schedule"],
    } in schedule["weekly-schedule"]["conditions"]
    assert table("notification-class")["properties"]["priority"]["range"] == {
        "element_min": 0,
        "element_max": 255,
    }


def test_file_and_logging_conditional_writability():
    props = table("file")["properties"]
    assert props["archive"]["access"] == "W"
    assert props["file-size"]["access"] == "C"
    assert {
        "kind": "only_if",
        "property": "file-access-method",
        "equals": "record-access",
    } in props["record-count"]["conditions"]
    trend = table("trend-log")["properties"]
    assert trend["log-device-object-property"]["datatype"] == "BACnetDeviceObjectPropertyReference"
    assert trend["enable"]["access"] == trend["record-count"]["access"] == "W"
    assert trend["start-time"]["access"] == "W"
    assert {"kind": "read_only_if", "property": "logging-type", "equals": "triggered"} in trend[
        "log-interval"
    ]["conditions"]
