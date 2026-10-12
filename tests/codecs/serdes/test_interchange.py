"""Semantic interchange, queryable graphs, input bounds, and artifact traceability."""

import builtins
import importlib
import json as standard_json
from pathlib import Path

import jsonschema
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pyshacl import validate as validate_shapes
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from ace_epics.codecs import json, rdf, yaml
from ace_epics.codecs._interchange import ValueMode
from ace_epics.codecs.errors import MissingExtraError
from ace_epics.diagnostics import EpicsError
from ace_epics.model import EpicsDocument
from ace_epics.values.nodes import EmptyElement
from ace_epics.values.parser import parse_value

ROOT = Path(__file__).resolve().parents[3]
CODECS = (json, yaml, rdf)
EPICS = Namespace(rdf.NAMESPACE)


def document(literals: list[str] | None = None) -> EpicsDocument:
    values = literals or ["13.400", '"Invented sensor"', "{TRUE, 42, NULL}"]
    properties = []
    for index, literal in enumerate(values):
        value, _ = parse_value(literal)
        properties.append(
            {
                "name": f"example-{index}",
                "value": value,
                "access": "C" if index % 2 else "W",
                "comment": "Synthetic declaration",
            }
        )
    properties.append({"name": "empty-example", "value": EmptyElement()})
    return EpicsDocument.model_validate(
        {
            "general": {
                "vendor_name": "Example Controls",
                "product_name": "Invented Sensor",
                "product_model_number": "EX-1",
                "product_description": "Synthetic codec fixture",
            },
            "bibbs": ["DS-RP-B", "DM-DDB-B"],
            "services": [{"name": "ReadProperty", "execute": True}],
            "object_types": [{"name": "device"}],
            "data_links": [{"kind": "ms-tp", "role": "manager", "baud_rates": [9600, 38400]}],
            "special": {"max_apdu_size": 480, "unknown": ["Example extension"]},
            "fail_times": {"internal_processing_fail_time": 0.25, "extra": {"Invented Timer": 1.5}},
            "default_restrictions": {"real": {"minimum": {"kind": "real", "value": "-100.0"}}},
            "objects": [
                {
                    "identifier": {"object_type": "device", "instance": 7},
                    "object_type": "device",
                    "name": "Invented Device",
                    "properties": properties,
                }
            ],
        }
    )


@pytest.mark.parametrize("codec", CODECS, ids=lambda c: c.name)
def test_complete_document_round_trip(codec) -> None:
    doc = document(
        [
            "NULL",
            "TRUE",
            "42",
            "13.400",
            "X'00AB'",
            '"Example"',
            "RELIABLE",
            "?",
            "*",
            "(Monday, 24-January-2000)",
            "12:34:56.78",
            "(analog-input, 3)",
            "[2] 42",
            "{TRUE, 42, NULL}",
            "{, NULL}",
            "(24-January-2000)-(25-January-2000)",
        ]
    )
    restored = codec.loads(codec.dumps(doc, deterministic=True))
    assert restored == doc
    assert [p.name.canonical for p in restored.objects[0].properties] == [
        p.name.canonical for p in doc.objects[0].properties
    ]


@pytest.mark.parametrize("codec", (json, yaml), ids=lambda c: c.name)
@pytest.mark.parametrize("values", ["tree", "text"])
def test_json_yaml_value_modes_and_raw_names(codec, values: ValueMode) -> None:
    doc = document(["13.400", "T", '"Preserved text"'])
    text = codec.dumps(doc, values=values, preserve_raw=True)
    assert codec.loads(text) == doc
    if codec is json:
        assert standard_json.loads(text)["services"][0]["name"]["raw"] == "ReadProperty"


@pytest.mark.parametrize("codec", CODECS, ids=lambda c: c.name)
def test_determinism(codec) -> None:
    doc = document()
    assert codec.dumps(doc, deterministic=True) == codec.dumps(doc, deterministic=True)


def test_cross_codec_identity() -> None:
    doc = document()
    cycle = rdf.loads(rdf.dumps(yaml.loads(yaml.dumps(json.loads(json.dumps(doc))))))
    assert json.loads(json.dumps(cycle)) == doc


@settings(max_examples=500, deadline=None)
@given(st.lists(st.integers(min_value=-(2**31), max_value=2**31 - 1), max_size=8))
def test_generated_documents_round_trip_all_codecs(numbers: list[int]) -> None:
    doc = document([str(number) for number in numbers] or ["NULL"])
    for codec in CODECS:
        assert codec.loads(codec.dumps(doc)) == doc


@pytest.mark.parametrize("values", ["tree", "text"])
def test_json_schema_validates_dumps_and_snapshot(values: ValueMode) -> None:
    published = standard_json.loads((ROOT / "schema/epics-document.schema.json").read_text())
    assert json.schema() == published
    jsonschema.Draft202012Validator.check_schema(published)
    jsonschema.validate(standard_json.loads(json.dumps(document(), values=values)), published)
    for example in published["examples"]:
        jsonschema.validate(example, published)


def test_json_schema_validates_wildcard_date_and_group() -> None:
    doc = document(["(*-January-2000)", "{*, NULL}"])
    jsonschema.validate(standard_json.loads(json.dumps(doc)), json.schema())
    assert json.loads(json.dumps(doc)) == doc


@pytest.mark.parametrize("source", ["[]", '{"format":"ace-epics/99"}', "{", "null"])
def test_invalid_json_returns_structured_error(source: str) -> None:
    with pytest.raises(EpicsError):
        json.loads(source, raise_on_error=True)


def test_literal_values_reject_trailing_native_markers() -> None:
    data = standard_json.loads(json.dumps(document(), values="text"))
    data["objects"][0]["properties"][0]["value"] = "42 W"
    with pytest.raises(EpicsError):
        json.loads(standard_json.dumps(data), raise_on_error=True)


def test_yaml_safe_loader_and_alias_bounds() -> None:
    with pytest.raises(EpicsError):
        yaml.loads("!!python/object/apply:os.system ['echo unsafe']", raise_on_error=True)
    with pytest.raises(EpicsError):
        yaml.loads("a: &a [*a]", raise_on_error=True)
    with pytest.raises(EpicsError):
        yaml.loads("a: &a [1, 2, 3]\nb: [*a, *a, *a]\n", max_nodes=5, raise_on_error=True)
    with pytest.raises(EpicsError):
        yaml.loads("a: [[[1]]]", max_depth=2, raise_on_error=True)


def test_missing_yaml_extra_explains_installation(monkeypatch) -> None:
    original = builtins.__import__

    def unavailable(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(MissingExtraError, match=r"ace-epics\[yaml\]"):
        yaml.dumps(document())


def test_missing_rdf_extra_explains_installation(monkeypatch) -> None:
    original = importlib.import_module

    def unavailable(name, *args, **kwargs):
        if name == "rdflib":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", unavailable)
    with pytest.raises(MissingExtraError, match=r"ace-epics\[rdf\]"):
        rdf.dumps(document())


def test_rdf_graph_has_queryable_properties_values_and_shape_conformance() -> None:
    graph = rdf.to_graph(document(), base_iri="urn:example:epics", deterministic=True)
    prop = URIRef("urn:example:epics/device/7/device,7/example-0")
    assert graph.value(prop, EPICS.propertyName) == Literal("example-0")
    assert graph.value(prop, EPICS.access) == EPICS.Writable
    value = graph.value(prop, EPICS.value)
    assert graph.value(value, EPICS.lexical) == Literal("13.400")
    assert list(graph.subjects(RDF.type, EPICS.FailTime))
    ontology = Graph().parse(ROOT / "src/ace_epics/codecs/data/ontology.ttl")
    shapes = Graph().parse(ROOT / "src/ace_epics/codecs/data/shapes.ttl")
    conforms, _, report = validate_shapes(graph, shacl_graph=shapes, ont_graph=ontology)
    assert conforms, report


def test_rdf_rejects_missing_document_ambiguous_properties_and_cyclic_lists() -> None:
    with pytest.raises(EpicsError):
        rdf.loads("<urn:x> <urn:p> <urn:y> .", raise_on_error=True)
    graph = rdf.to_graph(document(), base_iri="urn:example:epics", deterministic=True)
    doc = URIRef("urn:example:epics")
    graph.add((doc, EPICS.vendorName, Literal("Conflicting vendor")))
    with pytest.raises(EpicsError):
        rdf.from_graph(graph)
    graph.remove((doc, EPICS.vendorName, Literal("Conflicting vendor")))
    head = graph.value(doc, EPICS.objectOrder)
    graph.set((head, RDF.rest, head))
    with pytest.raises(EpicsError):
        rdf.from_graph(graph)


@pytest.mark.parametrize("codec,extension", [(json, "json"), (yaml, "yaml"), (rdf, "ttl")])
def test_path_io(codec, extension: str, tmp_path: Path) -> None:
    path = tmp_path / f"invented.{extension}"
    doc = document()
    codec.dump(doc, path)
    assert codec.load(path) == doc


def test_rdf_typed_dates_times_restrictions_and_declared_vocabulary() -> None:
    from rdflib import XSD

    graph = rdf.to_graph(document(["(24-January-2000)", "12:34:56.78"]), deterministic=True)
    assert any(value.datatype == XSD.date for value in graph.objects(None, EPICS.typedValue))
    assert any(value.datatype == XSD.time for value in graph.objects(None, EPICS.typedValue))
    assert Literal("real") in graph.objects(None, EPICS.datatypeKey)
    ontology = Graph().parse(ROOT / "src/ace_epics/codecs/data/ontology.ttl")
    project_predicates = {p for p in graph.predicates() if str(p).startswith(rdf.NAMESPACE)}
    assert project_predicates <= set(ontology.subjects())
    project_classes = {
        cls for cls in graph.objects(None, RDF.type) if str(cls).startswith(rdf.NAMESPACE)
    }
    assert project_classes <= set(ontology.subjects())


@settings(max_examples=200, deadline=None)
@given(st.binary(max_size=1024))
def test_arbitrary_bytes_produce_reader_diagnostics_without_raising(data: bytes) -> None:
    for codec in CODECS:
        result = codec.parse(data)
        assert result.document is None or isinstance(result.document, EpicsDocument)
        if result.document is None:
            assert result.has_errors


def test_mixed_nested_tagged_and_literal_values() -> None:
    data = standard_json.loads(json.dumps(document()))
    prop = data["objects"][0]["properties"][0]
    prop["value"] = {
        "kind": "group",
        "delimiter": "{",
        "elements": [
            "TRUE",
            {"kind": "integer", "value": 3},
            {"kind": "context-tagged", "tag": 2, "value": '"Nested literal"'},
        ],
    }
    jsonschema.validate(data, json.schema())
    restored = json.loads(standard_json.dumps(data))
    assert restored.objects[0].properties[0].value.kind == "group"
    assert json.loads(json.dumps(restored)) == restored


@pytest.mark.parametrize("codec", CODECS, ids=lambda c: c.name)
def test_failed_parse_has_no_fabricated_document(codec) -> None:
    result = codec.parse(b"\xff malformed input")
    assert result.document is None
    assert result.has_errors
    with pytest.raises(EpicsError):
        codec.loads(b"\xff malformed input", raise_on_error=False)


@pytest.mark.parametrize("codec", CODECS, ids=lambda c: c.name)
def test_object_header_metadata_roundtrips(codec) -> None:
    from ace_epics.model import Access, PropertyMetadata, Restrictions
    from ace_epics.values import IntegerValue

    doc = document()
    doc.objects[0].header_metadata = {
        "object-name": PropertyMetadata(
            access=Access.W,
            restrictions=Restrictions(maximum_length_string=40),
            comment="Header declaration",
            not_readable=True,
        ),
        "object-identifier": PropertyMetadata(
            restrictions=Restrictions(maximum=IntegerValue(value=4194303)),
        ),
    }
    restored = codec.loads(codec.dumps(doc))
    assert restored == doc
    assert restored.objects[0].header_metadata == doc.objects[0].header_metadata
    if codec is rdf:
        graph = rdf.to_graph(doc)
        assert any(graph.objects(None, EPICS.headerMetadata))
        ontology = Graph().parse(ROOT / "src/ace_epics/codecs/data/ontology.ttl")
        predicates = {p for p in graph.predicates() if str(p).startswith(rdf.NAMESPACE)}
        assert predicates <= set(ontology.subjects())
