"""Verify Annex K facts and conditional requirements without licensed extracts."""

import json
from collections import Counter
from pathlib import Path

import pytest

DATA = Path(__file__).parents[2] / "src" / "ace_epics" / "knowledge" / "data"


def table(name: str) -> dict:
    return json.loads((DATA / name).read_text())


@pytest.fixture
def bibbs() -> dict:
    return table("bibbs.json")["definitions"]


def test_required_annex_k_families_complete(bibbs: dict) -> None:
    counts = Counter(name.split("-")[0] for name in bibbs)
    assert counts == {"DS": 53, "AE": 39, "SCHED": 10, "T": 13, "DM": 37, "NM": 1}
    assert table("bibbs.json")["source"] == "ASHRAE 135-2024"
    assert table("bibbs.json")["revision"] == 30
    for family, count in ((1, 53), (2, 39), (3, 10), (4, 13)):
        assert {d["clause"] for d in bibbs.values() if d["clause"].startswith(f"K.{family}.")} == {
            f"K.{family}.{i}" for i in range(1, count + 1)
        }
    # K.5.7 and K.5.8 have no current BIBB definitions.
    assert {d["clause"] for d in bibbs.values() if d["clause"].startswith("K.5.")} == {
        f"K.5.{i}" for i in range(1, 40) if i not in (7, 8)
    }


def test_all_references_resolve(bibbs: dict) -> None:
    services = table("services.json")["values"]
    objects = table("object_types.json")["values"]
    for definition in bibbs.values():
        entries = [definition, *definition.get("conditional_requirements", [])]
        for entry in entries:
            for service in entry.get("services", []):
                assert service["name"] in services
                assert service["initiate"] or service["execute"]
                assert isinstance(service["initiate"], bool)
                assert isinstance(service["execute"], bool)
            assert set(entry.get("object_types", [])) <= objects.keys()
            assert set(entry.get("requires_bibbs", [])) <= bibbs.keys()
        for group in definition.get("object_type_alternatives", []):
            assert len(group) >= 2
            assert set(group) <= objects.keys()
        for group in definition.get("bibb_alternatives", []):
            assert len(group) >= 2
            assert set(group) <= bibbs.keys()
        for group in definition.get("service_alternatives", []):
            assert len(group) >= 2
            assert all(service["name"] in services for service in group)


def test_dependencies_have_no_cycles(bibbs: dict) -> None:
    def visit(name: str, ancestors: frozenset[str]) -> None:
        assert name not in ancestors
        for dependency in bibbs[name].get("requires_bibbs", []):
            visit(dependency, ancestors | {name})

    for name in bibbs:
        visit(name, frozenset())


def test_direction_is_taken_from_table_not_bibb_suffix(bibbs: dict) -> None:
    assert bibbs["DS-RP-B"]["services"] == [
        {"name": "read-property", "initiate": False, "execute": True}
    ]
    assert bibbs["AE-N-A"]["services"] == [
        {"name": "confirmed-event-notification", "initiate": False, "execute": True},
        {"name": "unconfirmed-event-notification", "initiate": False, "execute": True},
    ]
    assert next(s for s in bibbs["DM-VT-A"]["services"] if s["name"] == "vt-close") == {
        "name": "vt-close",
        "initiate": True,
        "execute": True,
    }
    assert next(
        s for s in bibbs["AE-NF-B"]["services"] if s["name"] == "confirmed-event-notification"
    ) == {"name": "confirmed-event-notification", "initiate": True, "execute": True}


@pytest.mark.parametrize("name", ["DS-COV-A", "DS-COVP-A", "DS-COVM-A"])
def test_cov_notifications_depend_on_request_parameter(bibbs: dict, name: str) -> None:
    definition = bibbs[name]
    assert len(definition["services"]) == 1
    assert definition["services"][0]["name"].startswith("subscribe-cov")
    requirements = definition["conditional_requirements"]
    assert {r["condition"]["value"] for r in requirements} == {True, False}
    assert all(r["condition"]["kind"] == "service_parameter_used" for r in requirements)
    assert all(r["services"][0]["execute"] for r in requirements)


def test_alternatives_are_not_unconditional_requirements(bibbs: dict) -> None:
    assert bibbs["DM-TM-A"]["services"] == []
    assert len(bibbs["DM-TM-A"]["service_alternatives"][0]) == 2
    assert bibbs["AE-LS-B"]["object_types"] == []
    assert bibbs["AE-LS-B"]["object_type_alternatives"] == [
        ["life-safety-point", "life-safety-zone"]
    ]
    assert bibbs["SCHED-WS-I-B"]["bibb_alternatives"] == [["DM-TS-B", "DM-UTC-B"]]
    assert {s["name"] for s in bibbs["SCHED-WS-I-B"]["services"]} == {
        "read-property",
        "write-property",
    }


def test_backup_create_object_is_conditional(bibbs: dict) -> None:
    definition = bibbs["DM-BR-B"]
    assert "create-object" not in {s["name"] for s in definition["services"]}
    assert definition["conditional_requirements"][0]["services"] == [
        {"name": "create-object", "initiate": False, "execute": True}
    ]
    assert definition["object_types"] == ["file"]


def test_remote_objects_do_not_imply_local_instances(bibbs: dict) -> None:
    for name in ("DS-V-A", "DS-AV-A", "AE-AVM-A", "SCHED-AVM-A", "T-AVM-A"):
        assert bibbs[name]["object_types"] == []
    assert bibbs["SCHED-I-B"]["object_types"] == ["calendar", "schedule"]
    assert bibbs["AE-AC-B"]["object_types"] == ["access-point"]


def test_archival_multiple_values_is_revision_conditional(bibbs: dict) -> None:
    assert bibbs["T-A-A"]["requires_bibbs"] == ["T-ATR-A"]
    assert bibbs["T-A-A"]["conditional_requirements"] == [
        {
            "condition": {"kind": "protocol_revision_at_least", "revision": 7},
            "requires_bibbs": ["T-AMVR-A"],
        }
    ]


def test_external_event_reporting_requires_confirmed_initiation(bibbs: dict) -> None:
    assert bibbs["AE-N-E-B"]["services"] == [
        {"name": "confirmed-event-notification", "initiate": True, "execute": False}
    ]
    assert bibbs["AE-N-E-B"]["object_types"] == ["event-enrollment"]
