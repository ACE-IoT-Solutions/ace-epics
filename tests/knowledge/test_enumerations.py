"""Factual regression checks for Clause 21 tables and supported revision history."""

import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[2] / "src/ace_epics/knowledge/data"


def table(name):
    return json.loads((DATA / f"{name}.json").read_text())


@pytest.mark.parametrize(
    "name", ["object_types", "services", "property_identifiers", "enums/segmentation"]
)
def test_enumeration_integrity(name):
    data = table(name)
    assert data["source"] == "ASHRAE 135-2024"
    assert data["revision"] == 30
    assert data["provenance"]["enumeration"].startswith("Clause 21")
    values = data["values"]
    assert len(set(values.values())) == len(values)
    assert all(isinstance(number, int) and number >= 0 for number in values.values())
    assert all(name == name.lower() and "_" not in name for name in values)


@pytest.mark.parametrize("name", ["object_types", "services"])
def test_revision_history_is_complete_and_monotonic(name):
    data = table(name)
    counts = data["bit_counts"]
    assert set(counts) == {str(revision) for revision in range(14, 31)}
    assert [counts[str(r)] for r in range(14, 31)] == sorted(counts.values())
    assert counts["30"] == max(data["values"].values()) + 1
    assert set(data["introduced_revision"]) <= set(data["values"])


def test_object_revision_boundaries_include_reserved_positions():
    data = table("object_types")
    counts = data["bit_counts"]
    assert [counts[str(r)] for r in (14, 15, 16, 17, 18, 19, 20, 23, 24, 30)] == [
        55,
        55,
        56,
        57,
        60,
        60,
        63,
        63,
        65,
        65,
    ]
    assert data["values"]["timer"] == 31
    assert data["introduced_revision"]["timer"] == 17
    assert data["values"]["network-security"] == 38
    assert data["removed_revision"]["network-security"] == 22
    assert counts["21"] == counts["22"]  # Removal preserves assigned bit positions.
    assert data["values"]["color"] == 63
    assert data["values"]["color-temperature"] == 64


def test_service_history_and_removed_slots():
    data = table("services")
    counts = data["bit_counts"]
    assert [counts[str(r)] for r in (14, 17, 18, 19, 20, 21, 22, 28, 29, 30)] == [
        41,
        41,
        44,
        44,
        47,
        47,
        49,
        49,
        50,
        50,
    ]
    assert len(data["values"]) == 47
    assert {13, 24, 25}.isdisjoint(data["values"].values())
    assert data["values"]["auth-request"] == 49
    assert data["introduced_revision"]["auth-request"] == 29
    assert data["values"]["who-am-i"] == 47
    assert data["introduced_revision"]["who-am-i"] == 22


def test_property_identifiers_cover_core_and_extended_ranges():
    values = table("property_identifiers")["values"]
    assert len(values) == 512
    expected = {
        "object-identifier": 75,
        "object-name": 77,
        "object-type": 79,
        "present-value": 85,
        "property-list": 371,
        "protocol-revision": 139,
        "max-manager": 64,
        "write-every-scheduled-action": 4194333,
        "authorization-cache": 4194343,
    }
    assert {name: values[name] for name in expected} == expected


def test_segmentation_numeric_semantics():
    assert table("enums/segmentation")["values"] == {
        "segmented-both": 0,
        "segmented-transmit": 1,
        "segmented-receive": 2,
        "no-segmentation": 3,
    }
