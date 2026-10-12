"""Verified amendment facts must not masquerade as complete earlier snapshots."""

import json
from pathlib import Path

import pytest

from ace_epics.knowledge import JsonKnowledgeProvider

OBJECTS = Path(__file__).parents[2] / "src/ace_epics/knowledge/data/objects"


def table(name):
    return json.loads((OBJECTS / f"{name}.json").read_text())


@pytest.mark.parametrize(
    "name",
    [
        "analog-input",
        "analog-output",
        "analog-value",
        "binary-input",
        "binary-output",
        "binary-value",
        "multi-state-input",
        "multi-state-output",
        "multi-state-value",
        "device",
        "file",
        "notification-class",
        "schedule",
        "calendar",
        "trend-log",
    ],
)
def test_global_metadata_introductions(name):
    data = table(name)
    for prop, revision, amendment in [
        ("tags", 19, "135-2012ba"),
        ("profile-location", 19, "135-2012ba"),
        ("audit-level", 20, "135-2016bi"),
        ("auditable-operations", 20, "135-2016bi"),
    ]:
        spec = data["properties"][prop]
        assert spec["introduced_rev"] == revision
        assert amendment in spec["introduction_evidence"]["source"]
        assert spec["introduction_evidence"]["url"].startswith("https://bacnet.org/")
    assert data["coverage_min_revision"] >= 26
    assert data["history_coverage"]["complete"] is True
    assert JsonKnowledgeProvider().object_definition(name, 29) is not None
    assert JsonKnowledgeProvider().object_definition(name, 13) is None


@pytest.mark.parametrize(
    "name",
    [
        "analog-input",
        "analog-output",
        "binary-input",
        "binary-output",
        "multi-state-input",
        "multi-state-output",
    ],
)
def test_interface_value_introduced_revision16(name):
    spec = table(name)["properties"]["interface-value"]
    assert spec["introduced_rev"] == 16
    assert "135-2012at" in spec["introduction_evidence"]["source"]


@pytest.mark.parametrize(
    "name",
    [
        "analog-output",
        "analog-value",
        "binary-output",
        "binary-value",
        "multi-state-output",
        "multi-state-value",
    ],
)
def test_command_and_source_introductions_revision17(name):
    data = table(name)
    for prop in [
        "current-command-priority",
        "value-source",
        "value-source-array",
        "last-command-time",
        "command-time-array",
    ]:
        spec = data["properties"][prop]
        assert spec["introduced_rev"] == 17
        assert "135-2012as" in spec["introduction_evidence"]["source"]
    assert data["properties"]["audit-priority-filter"]["introduced_rev"] == 20


def test_device_and_schedule_verified_history():
    props = table("device")["properties"]
    assert props["serial-number"]["introduced_rev"] == 14
    assert props["active-cov-multiple-subscriptions"]["introduced_rev"] == 18
    assert props["deployed-profile-location"]["introduced_rev"] == 19
    assert props["audit-notification-recipient"]["introduced_rev"] == 20
    assert props["device-uuid"]["introduced_rev"] == 22
    assert table("schedule")["properties"]["write-every-scheduled-action"]["introduced_rev"] == 24


def test_device_revision28_snapshot_reverses_authorization_additions():
    provider = JsonKnowledgeProvider()
    before = provider.object_definition("device", 28)
    after = provider.object_definition("device", 29)
    assert before is not None and after is not None
    added = {
        "authorization-server",
        "authorization-status",
        "authorization-policy",
        "authorization-scope",
        "authorization-cache",
        "authorization-groups",
    }
    assert set(after.properties) - set(before.properties) == added
    assert len(before.properties) == 74
    assert all(after.properties[name].introduced_rev == 29 for name in added)
    assert provider.object_definition("device", 27) is not None
    assert provider.object_definition("device", 13) is None


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
def test_recent_snapshots_have_complete_amendment_chain(name):
    data = table(name)
    assert {28, 29, 30} <= set(data["history_coverage"]["complete_snapshot_revisions"])
    evidence = data["history_coverage"]["snapshot_evidence"]
    assert {29, 30} <= {e["protocol_revision"] for e in evidence}
    provider = JsonKnowledgeProvider()
    for revision in [28, 29, 30]:
        snapshot = provider.object_definition(name, revision)
        assert snapshot is not None
        assert len(snapshot.properties) == len(data["properties"]) - (
            6 if name == "device" and revision == 28 else 0
        )


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
def test_revision27_reliability_runtime_additions_are_reversed(name):
    affected = {
        "analog-input",
        "analog-output",
        "analog-value",
        "multi-state-input",
        "multi-state-value",
    }
    provider = JsonKnowledgeProvider()
    snapshot = provider.object_definition(name, 27)
    assert snapshot is not None
    if name in affected:
        assert "runtime_constraints" not in snapshot.properties["reliability"].model_dump()
        assert table(name)["properties"]["reliability"]["runtime_constraints"]
    assert provider.object_definition(name, 13) is None
    if snapshot is not None:
        assert len(snapshot.properties) == len(table(name)["properties"]) - (
            6 if name == "device" else 0
        )


def test_device_proxy_properties_revision27_and_positive_rate():
    provider = JsonKnowledgeProvider()
    for revision in [27, 28, 29, 30]:
        definition = provider.object_definition("device", revision)
        assert definition is not None
        for name in ["max-proxied-i-ams-per-second", "device-address-proxy-table"]:
            assert definition.properties[name].introduced_rev == 27
        assert definition.properties["max-proxied-i-ams-per-second"].range == {"min": 1}


def test_device_revision26_reverses_two_proxy_additions():
    provider = JsonKnowledgeProvider()
    before = provider.object_definition("device", 26)
    after = provider.object_definition("device", 27)
    assert before is not None and after is not None
    assert set(after.properties) - set(before.properties) == {
        "max-proxied-i-ams-per-second",
        "device-address-proxy-table",
    }
    assert len(before.properties) == 72
    assert provider.object_definition("device", 13) is None


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
@pytest.mark.parametrize("revision", [24, 25, 26, 27])
def test_all_midrange_history_snapshots_available(name, revision):
    definition = JsonKnowledgeProvider().object_definition(name, revision)
    assert definition is not None
    assert definition.revision == revision
    assert len(definition.properties) == len(table(name)["properties"]) - (
        8 if name == "device" and revision < 27 else 6 if name == "device" else 0
    )


def test_ck_datatype_spelling_preserves_wire_semantics():
    provider = JsonKnowledgeProvider()
    old = provider.object_definition("analog-input", 25)
    new = provider.object_definition("analog-input", 26)
    assert old is not None and new is not None
    assert (
        old.properties["present-value"].datatype
        == new.properties["present-value"].datatype
        == "Real"
    )
    spec = old.properties["present-value"].model_dump()
    assert spec["source_datatype"] == "REAL"
    assert spec["datatype_normalization"]["revision"] == 26
    assert "same application tag" in spec["datatype_normalization"]["rationale"]


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
@pytest.mark.parametrize("revision", [21, 22, 23])
def test_reversed_device_uuid_and_schedule_action_history(name, revision):
    definition = JsonKnowledgeProvider().object_definition(name, revision)
    assert definition is not None
    if name == "device":
        assert ("device-uuid" in definition.properties) == (revision >= 22)
        assert definition.properties["max-manager"].model_dump()["source_name_aliases"] == [
            "max-master"
        ]
    if name == "schedule":
        assert "write-every-scheduled-action" not in definition.properties
    assert all(
        spec.introduced_rev is None or spec.introduced_rev <= revision
        for spec in definition.properties.values()
    )


def test_device_four_property_removals_have_exact_revision17_evidence():
    definition = JsonKnowledgeProvider().object_definition("device", 30)
    assert definition is not None
    assert set(definition.historical_properties) == {
        "subordinate-proxy-enable",
        "manual-subordinate-address-binding",
        "auto-subordinate-discovery",
        "subordinate-address-binding",
    }
    for spec in definition.historical_properties.values():
        assert spec.removed_rev == 17
        assert spec.model_dump()["removal_evidence"]["source"] == "ASHRAE Addendum 135-2012ai"


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
def test_revision19_reverses_audit_and_mandatory_reliability_writes(name):
    provider = JsonKnowledgeProvider()
    before = provider.object_definition(name, 19)
    after = provider.object_definition(name, 20)
    assert before is not None and after is not None
    assert "audit-level" not in before.properties
    assert "auditable-operations" not in before.properties
    assert after.properties["audit-level"].introduced_rev == 20
    if name.startswith(("analog-", "binary-", "multi-state-")):
        assert before.properties["reliability"].access == "R"
        assert not any(
            c["kind"] == "writable_if" for c in before.properties["reliability"].conditions
        )
        assert after.properties["reliability"].access == "C"


def test_device_utc_offset_revision18_range_extension():
    for revision in range(19, 31):
        definition = JsonKnowledgeProvider().object_definition("device", revision)
        assert definition is not None
        assert definition.properties["utc-offset"].range == {"min": -1440, "max": 1440}
        assert definition.properties["utc-offset"].min_range == {
            "min": -1440,
            "max": 1440,
            "step": 15,
        }


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
def test_revision18_reverses_global_semantic_metadata_revision19(name):
    provider = JsonKnowledgeProvider()
    before = provider.object_definition(name, 18)
    after = provider.object_definition(name, 19)
    assert before is not None and after is not None
    assert "tags" not in before.properties and "profile-location" not in before.properties
    assert "tags" in after.properties and "profile-location" in after.properties


def test_revision17_reverses_cov_multiple_and_utc_offset_extension():
    provider = JsonKnowledgeProvider()
    before = provider.object_definition("device", 17)
    after = provider.object_definition("device", 18)
    assert before is not None and after is not None
    assert "active-cov-multiple-subscriptions" not in before.properties
    assert before.properties["utc-offset"].range == {"min": -780, "max": 780}
    assert after.properties["utc-offset"].range == {"min": -1440, "max": 1440}
    assert {
        "kind": "only_if",
        "service": "subscribe-cov-property-multiple",
        "direction": "execute",
    } in after.properties["active-cov-multiple-subscriptions"].conditions


@pytest.mark.parametrize("name", [p.stem for p in OBJECTS.glob("*.json")])
@pytest.mark.parametrize("revision", range(14, 31))
def test_complete_revision14_through30_history_grid(name, revision):
    definition = JsonKnowledgeProvider().object_definition(name, revision)
    assert definition is not None
    expected = {
        prop
        for prop, spec in table(name)["properties"].items()
        if spec.get("introduced_rev", 0) <= revision
    }
    if name == "device" and revision < 17:
        expected.update(table(name)["historical_properties"])
    assert set(definition.properties) == expected
    assert all(
        spec.datatype and spec.access in {"R", "W", "C"} for spec in definition.properties.values()
    )
    for spec in definition.properties.values():
        for condition in spec.conditions:
            if condition["kind"] in {"all_or_none", "at_least_one"}:
                assert set(condition["properties"]) <= set(definition.properties)


def test_pre_network_port_device_properties_and_ranges_restored():
    definition = JsonKnowledgeProvider().object_definition("device", 16)
    assert definition is not None
    for name in table("device")["historical_properties"]:
        assert name in definition.properties
        assert definition.properties[name].removed_rev == 17
    assert definition.properties["max-manager"].range == {"min": 1, "max": 127}
    assert definition.properties["max-info-frames"].range == {"min": 1, "max": 255}


def test_pre_revision16_fault_and_notification_properties_reversed():
    provider = JsonKnowledgeProvider()
    for name in ["analog-input", "analog-value"]:
        definition = provider.object_definition(name, 15)
        assert definition is not None
        assert "fault-low-limit" not in definition.properties
        assert "fault-high-limit" not in definition.properties
    definition = provider.object_definition("notification-class", 15)
    assert definition is not None
    assert (
        "status-flags" not in definition.properties and "reliability" not in definition.properties
    )
    assert definition.properties["notification-class"].requirement == "required"
    assert definition.properties["notification-class"].range == {
        "min": 0,
        "equals_object_instance": True,
    }
    assert definition.properties["recipient-list"].range == {"min_length": 1}


def test_binary_pre_revision16_datatype_and_timestamp_access():
    provider = JsonKnowledgeProvider()
    for name in ["binary-input", "binary-output", "binary-value"]:
        before = provider.object_definition(name, 15)
        after = provider.object_definition(name, 16)
        assert before is not None and after is not None
        assert before.properties["time-of-state-count-reset"].access == "R"
        assert after.properties["time-of-state-count-reset"].access == "C"
        if name == "binary-value":
            assert before.properties["change-of-state-count"].datatype == "Unsigned32"
            assert after.properties["change-of-state-count"].datatype == "Unsigned"


def test_revision14_time_distribution_bundle_before_ar():
    definition = JsonKnowledgeProvider().object_definition("device", 14)
    assert definition is not None
    for name in ["time-synchronization-recipients", "utc-time-synchronization-recipients"]:
        assert definition.properties[name].requirement == "optional"
        assert definition.properties[name].conditions == []
    for name in ["time-synchronization-interval", "align-intervals", "interval-offset"]:
        assert {
            "kind": "only_if_any_present",
            "properties": [
                "time-synchronization-recipients",
                "utc-time-synchronization-recipients",
            ],
        } in definition.properties[name].conditions
