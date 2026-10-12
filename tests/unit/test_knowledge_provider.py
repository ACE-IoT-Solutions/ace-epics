"""Provider boundaries protect validators from unsupported knowledge claims."""

import json

import pytest

from ace_epics.knowledge import JsonKnowledgeProvider, KnowledgeProvider, NullProvider


def write_table(tmp_path, name, **data):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source": "synthetic", **data}))


def test_null_provider_explicitly_unavailable():
    provider = NullProvider()
    assert isinstance(provider, KnowledgeProvider)
    assert provider.object_types(30) == {}
    assert provider.services_bit_count(30) is None
    assert provider.object_definition("device", 30) is None
    assert provider.bibb("DS-RP-B") is None


def test_revision_filtering_and_unknown_future(tmp_path):
    write_table(
        tmp_path,
        "object_types.json",
        revision=30,
        coverage_min_revision=14,
        values={"device": 8, "timer": 31, "network-security": 38},
        introduced_revision={"timer": 17},
        removed_revision={"network-security": 22},
        bit_counts={"14": 55, "30": 65},
    )
    provider = JsonKnowledgeProvider(tmp_path)
    assert provider.object_types(14) == {"device": 8, "network-security": 38}
    assert provider.object_types(22) == {"device": 8, "timer": 31}
    assert provider.object_types(None) == provider.object_types(30)
    assert provider.object_types(31) == {}
    assert provider.object_types(13) == {}
    assert provider.object_types_bit_count(15) is None


def test_snapshot_does_not_claim_historical_completeness(tmp_path):
    write_table(
        tmp_path,
        "objects/device.json",
        object_type="device",
        revision=30,
        properties={
            "description": {"requirement": "optional", "datatype": "CharacterString", "access": "R"}
        },
    )
    provider = JsonKnowledgeProvider(tmp_path)
    assert provider.object_definition("Device", 29) is None
    current = provider.object_definition("Device", 30)
    assert current is not None
    assert not current.properties["description"].read_only
    assert provider.object_definition("../device", 30) is None


def test_bibb_dependencies_directions_and_conditional_preservation(tmp_path):
    write_table(
        tmp_path,
        "bibbs.json",
        definitions={
            "DS-RP-A": {"services": [{"name": "read-property", "initiate": True}]},
            "COMPOSITE-B": {
                "requires_bibbs": ["DS-RP-A"],
                "services": [
                    {"name": "read-property", "execute": True},
                    {
                        "name": "write-property",
                        "execute": True,
                        "conditions": [{"kind": "optional"}],
                    },
                ],
                "object_type_alternatives": [["calendar", "schedule"]],
            },
            "MISSING-B": {"requires_bibbs": ["UNKNOWN-A"]},
            "CYCLE-B": {"requires_bibbs": ["CYCLE-B"]},
        },
    )
    provider = JsonKnowledgeProvider(tmp_path)
    definition = provider.effective_bibb("composite_b")
    assert definition is not None
    assert len(definition.services) == 1
    assert definition.services[0].initiate and definition.services[0].execute
    assert definition.object_type_alternatives == [["calendar", "schedule"]]
    assert definition.conditional_requirements
    assert provider.effective_bibb("MISSING-B") is None
    assert provider.effective_bibb("CYCLE-B") is not None


def test_malformed_table_requires_source(tmp_path):
    (tmp_path / "services.json").write_text('{"values": {}}')
    with pytest.raises(ValueError, match="source edition"):
        JsonKnowledgeProvider(tmp_path).services(30)


def test_packaged_tables_load_through_public_provider():
    provider = JsonKnowledgeProvider()
    assert provider.object_types(30)["device"] == 8
    assert provider.services(30)["read-property"] == 12
    assert provider.property_identifiers()["object-name"] == 77
    bibb = provider.bibb("DS-RP-B")
    assert bibb is not None and bibb.services[0].execute
    definition = provider.object_definition("analog-input", 30)
    assert definition is not None and definition.properties["present-value"].access == "C"
