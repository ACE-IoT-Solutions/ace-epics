import time

import pytest

from ace_epics.codecs.epics import dumps, parse
from ace_epics.model import ObjectIdentifier, TestObject
from tests.fixtures_build_epics import minimal


@pytest.mark.slow
def test_ten_thousand_objects_under_five_seconds():
    doc = minimal()
    doc.objects = [
        TestObject(
            identifier=ObjectIdentifier(
                object_type="device" if i == 0 else "analog-value", instance=i
            ),
            name=f"Object {i}",
            object_type="device" if i == 0 else "analog-value",
        )
        for i in range(10000)
    ]
    text = dumps(doc)
    start = time.perf_counter()
    result = parse(text, strict=True)
    elapsed = time.perf_counter() - start
    assert result.document is not None
    assert len(result.document.objects) == 10000
    assert not result.diagnostics
    assert elapsed < 5, f"10,000 objects parsed in {elapsed:.3f}s"
