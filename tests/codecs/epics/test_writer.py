from io import BytesIO
from typing import Any

import pytest
from hypothesis import given, settings

from ace_epics.codecs.epics import dump, dumps, load, loads, parse
from ace_epics.model import ObjectIdentifier, PropertyEntry, SourceInfo, TestObject
from ace_epics.values import GroupValue, IntegerValue, Preserving, parse_value
from tests.fixtures_build_epics import full, minimal
from tests.model_strategies import native_documents


@settings(max_examples=2000, deadline=None)
@given(native_documents())
def test_native_generated_semantic_roundtrip(doc):
    text = dumps(doc)
    result = parse(text, strict=True)
    assert result.diagnostics == []
    assert result.document is not None
    assert result.document == doc
    assert dumps(result.document) == text


def test_full_roundtrip_and_byte_stability(tmp_path):
    doc = full()
    text = dumps(doc)
    assert "\r\n" in text and "\n" not in text.replace("\r\n", "")
    assert loads(text, strict=True) == doc
    path = tmp_path / "example.tpi"
    dump(doc, path)
    assert path.read_bytes() == text.encode()
    assert load(path) == doc
    stream = BytesIO()
    dump(doc, stream)
    stream.seek(0)
    assert load(stream) == doc


@pytest.mark.parametrize("code", range(6))
def test_all_header_encodings(code):
    doc = minimal()
    doc.objects = [
        TestObject(
            identifier=ObjectIdentifier(object_type="device", instance=1),
            name="D",
            object_type="device",
        )
    ]
    doc.header.charset_code = code
    stream = BytesIO()
    dump(doc, stream)
    stream.seek(0)
    decoded = load(stream)
    assert decoded == doc
    assert decoded.header.charset_code == code


def test_preserving_hints_and_group_wrapping():
    doc = minimal()
    value, _ = parse_value("{1.2300, 'example', T}")
    obj = TestObject(
        identifier=ObjectIdentifier(object_type="device", instance=1),
        name="D",
        object_type="device",
        properties=[
            PropertyEntry(name="example", value=value),
            PropertyEntry(
                name="large",
                value=GroupValue(
                    delimiter="{", elements=[IntegerValue(value=i) for i in range(80)]
                ),
            ),
        ],
    )
    doc.objects = [obj]
    preserving = dumps(doc, style=Preserving)
    assert "1.2300, 'example', T" in preserving
    canonical = dumps(doc)
    assert loads(canonical) == doc
    assert "large: {\r\n" in canonical


@pytest.mark.parametrize("value", ["both ' and \" quotes", "line\nbreak", "line\rbreak"])
def test_writer_rejects_unrepresentable_strings(value):
    doc = minimal()
    doc.general.product_description = value
    with pytest.raises(ValueError):
        dumps(doc)


def test_unrepresentable_comments_and_options():
    doc = full()
    doc.objects[0].properties[0].comment = "bad\ncomment"
    with pytest.raises(ValueError):
        dumps(doc)
    cases: list[dict[str, Any]] = [{"charset_code": 6}, {"line_ending": "invalid"}]
    for kwargs in cases:
        with pytest.raises(ValueError):
            dumps(minimal(), **kwargs)
    assert "\n" in dumps(minimal(), line_ending="\n")
    assert dumps(minimal(), charset_code=5).startswith("PICS 5")


def test_document_equality_ignores_metadata():
    doc = full()
    other = loads(dumps(doc), source="example.tpi")
    other.source = SourceInfo(path="changed")
    assert other == doc
    assert doc != "not a document"


def test_header_metadata_roundtrip():
    from ace_epics.model import PropertyMetadata, Restrictions

    doc = full()
    doc.objects[0].header_metadata = {
        "object-name": PropertyMetadata(
            access="W",
            restrictions=Restrictions(maximum_length_string=30),
            comment="May be renamed",
            not_readable=True,
        ),
        "object-type": PropertyMetadata(
            access="W", comment="Incorrect access retained for validation"
        ),
    }
    text = dumps(doc)
    assert " W <maximum length string: 30> -- @not-readable May be renamed" in text
    decoded = loads(text, strict=True)
    assert decoded == doc
    assert decoded.objects[0].header_metadata == doc.objects[0].header_metadata
    assert dumps(decoded) == text


def test_header_comments_reject_newlines():
    from ace_epics.model import PropertyMetadata

    doc = full()
    doc.objects[0].header_metadata = {"object-name": PropertyMetadata(comment="one\ntwo")}
    with pytest.raises(ValueError, match="comments cannot contain newlines"):
        dumps(doc)
