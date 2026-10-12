import json
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from pydantic import ValidationError

from ace_epics.model import (
    Bibb,
    EpicsDocument,
    GeneralInformation,
    ObjectIdentifier,
    ObjectTypeSupport,
    ServiceSupport,
    SpecialFunctionality,
    TestObject,
)
from tests.model_strategies import documents


def document(**kwargs):
    general = GeneralInformation(
        vendor_name="Ace",
        product_name="Synthetic",
        product_model_number="1",
        product_description="Example",
    )
    return EpicsDocument(general=general, **kwargs)


def device(instance=1):
    return TestObject(
        identifier=ObjectIdentifier(object_type="device", instance=instance),
        name=f"Device {instance}",
        object_type="device",
    )


def test_all_queries_and_diagnostics_exclusion():
    item = device()
    doc = document(
        objects=[item],
        services=[ServiceSupport(name="Who-Is", initiate=True)],
        bibbs=[Bibb(canonical="DM-DDB-A")],
        object_types=[ObjectTypeSupport(name="Device")],
    )
    assert doc.device == item
    assert doc.get_object(item.identifier) == item
    assert doc.get_object(ObjectIdentifier(object_type="device", instance=2)) is None
    assert doc.objects_of_type("Device") == [item]
    assert doc.objects_of_type(700) == []
    assert doc.objects_of_type(item.object_type) == [item]
    assert doc.supports_service("Who-Is", initiate=True, execute=False)
    assert not doc.supports_service("Who-Is", execute=True)
    assert doc.supports_service("Who-Is")
    assert doc.supports_bibb("dm-ddb-a") and not doc.supports_bibb("missing")
    assert doc.supports_object_type("Device") and not doc.supports_object_type("missing")
    assert not doc.diagnostics
    assert "diagnostics" not in doc.model_dump()


def test_duplicate_identifiers_rejected_and_declarations_warn():
    with pytest.raises(ValidationError):
        document(objects=[device(), device()])
    doc = document(
        bibbs=[Bibb(canonical="DS-RP-B"), Bibb(canonical="ds-rp-b")],
        services=[ServiceSupport(name="Who-Is", initiate=True)] * 2,
        object_types=[ObjectTypeSupport(name="Device")] * 2,
        character_sets=["ISO 10646 (UCS2)", "ISO 10646 (UCS-2)"],
        special=SpecialFunctionality(segmented_requests_window=0),
    )
    codes = [d.code for d in doc.diagnostics]
    assert codes.count("M-DUPLICATE-DECLARATION") == 4
    assert "M-DEVICE-COUNT" in codes and "M-WINDOW-RANGE" in codes
    assert doc.device is None
    count = len(doc.diagnostics)
    assert len(EpicsDocument.model_validate(doc).diagnostics) == count
    assert document(objects=[device(1), device(2)]).diagnostics[0].code == "M-DEVICE-COUNT"


def test_public_import_order_is_acyclic():
    for order in [("ace_epics.values", "ace_epics.model"), ("ace_epics.model", "ace_epics.values")]:
        script = "; ".join(f"import {name}" for name in order)
        script += "; from ace_epics.model import EpicsDocument; EpicsDocument.model_json_schema()"
        subprocess.run([sys.executable, "-c", script], check=True)
    import ace_epics.model as model

    assert model.GeneralInformation
    with pytest.raises(AttributeError):
        _ = model.missing


def test_schema_snapshot():
    path = Path(__file__).parents[2] / "snapshots/epics-document.schema.json"
    assert EpicsDocument.model_json_schema() == json.loads(path.read_text())


@settings(max_examples=1000, deadline=None)
@given(documents())
def test_thousand_valid_documents_roundtrip_json(doc):
    decoded = EpicsDocument.model_validate_json(doc.model_dump_json())
    assert decoded.model_dump() == doc.model_dump()
