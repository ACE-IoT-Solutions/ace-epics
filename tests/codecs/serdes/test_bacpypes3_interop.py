"""Compare RDF projections with the pinned official BACpypes3 RDF implementation."""

from datetime import date, datetime
from decimal import Decimal
from importlib.metadata import version
from typing import cast

import pytest
from bacpypes3 import basetypes, primitivedata
from bacpypes3.rdf import core, util
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.collection import Collection

from ace_epics.codecs import json, rdf, yaml
from ace_epics.model import EpicsDocument
from ace_epics.model.names import NamedToken
from ace_epics.values.nodes import (
    BooleanValue,
    CharacterStringValue,
    DateRangeValue,
    DateValue,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    NullValue,
    ObjectIdentifierValue,
    OctetStringValue,
    RealValue,
    TimeValue,
    WildcardValue,
)
from tests.codecs.serdes.test_interchange import document

BACNET = util.BACNET


def _object_id(value: str) -> primitivedata.ObjectIdentifier:
    return cast(primitivedata.ObjectIdentifier, primitivedata.ObjectIdentifier(value))


def test_pinned_official_namespace_and_release():
    assert version("bacpypes3") == "0.0.110"
    assert str(BACNET) == "http://data.ashrae.org/bacnet/"
    assert rdf.BACNET_NAMESPACE == str(core.BACNET) == str(BACNET)


ATOMIC_CASES = [
    (NullValue(), None, primitivedata.Null(())),
    (BooleanValue(value=True), None, primitivedata.Boolean(True)),
    (BooleanValue(value=False), None, primitivedata.Boolean(False)),
    (IntegerValue(value=-42), "Integer", primitivedata.Integer(-42)),
    (IntegerValue(value=42), "Integer", primitivedata.Integer(42)),
    (IntegerValue(value=42), "Unsigned", primitivedata.Unsigned(42)),
    (IntegerValue(value=255), "Unsigned8", primitivedata.Unsigned8(255)),
    (RealValue(value=Decimal("1.25")), "Real", primitivedata.Real(1.25)),
    (RealValue(value=Decimal("1.25")), "Double", primitivedata.Double(1.25)),
    (OctetStringValue(value=b"\x00\xab\xff"), None, primitivedata.OctetString(b"\x00\xab\xff")),
    (
        CharacterStringValue(value="Example é \U0001f321"),
        None,
        primitivedata.CharacterString("Example é \U0001f321"),
    ),
    (DateValue(year=2024, month=1, day=2, weekday=2), None, primitivedata.Date(date(2024, 1, 2))),
    (DateValue(year=2024, month=1, day=2), None, primitivedata.Date(date(2024, 1, 2))),
    (
        DateValue(year=2024, month=WildcardValue(), day=WildcardValue(), weekday=WildcardValue()),
        None,
        primitivedata.Date((124, 255, 255, 255)),
    ),
    (
        DateValue(year=2024, month=1, day=2, weekday=WildcardValue()),
        None,
        primitivedata.Date((124, 1, 2, 255)),
    ),
    (
        DateValue(year=2024, month=13, day=32, weekday=WildcardValue()),
        None,
        primitivedata.Date((124, 13, 32, 255)),
    ),
    (
        TimeValue(hour=12, minute=34, second=56, hundredth=78),
        None,
        primitivedata.Time((12, 34, 56, 78)),
    ),
    (
        TimeValue(hour=12, minute=34, second=56, hundredth=0),
        None,
        primitivedata.Time((12, 34, 56, 0)),
    ),
    (
        TimeValue(
            hour=WildcardValue(), minute=30, second=WildcardValue(), hundredth=WildcardValue()
        ),
        None,
        primitivedata.Time((255, 30, 255, 255)),
    ),
]


@pytest.mark.parametrize(
    "value,datatype,official", ATOMIC_CASES, ids=[f"atomic-{i}" for i in range(len(ATOMIC_CASES))]
)
def test_atomic_projection_matches_real_encoder_and_decoder(value, datatype, official):
    graph = Graph()
    actual = rdf.bacnet_value(value, datatype, graph=graph)
    expected = (
        util.double_encode(graph, official)
        if type(official) is primitivedata.Double
        else util.atomic_encode(graph, official)
    )
    assert actual == expected
    restored = (
        util.double_decode(graph, actual)
        if type(official) is primitivedata.Double
        else util.atomic_decode(graph, actual, type(official))
    )
    assert restored == official


@pytest.mark.parametrize(
    "datatype,name,official_class",
    [
        ("BACnetObjectType", "analog-input", basetypes.ObjectType),
        ("BACnetReliability", "no-fault-detected", basetypes.Reliability),
        ("BACnetEngineeringUnits", "kilowatts", basetypes.EngineeringUnits),
        ("BACnetSegmentation", "no-segmentation", basetypes.Segmentation),
        ("BACnetEventState", "normal", basetypes.EventState),
        ("BACnetBinaryPV", "active", basetypes.BinaryPV),
    ],
)
def test_enumeration_class_and_member_match_official_encoder(datatype, name, official_class):
    value = EnumeratedValue(name=NamedToken(canonical=name))
    expected = official_class(name)
    graph = Graph()
    term = rdf.bacnet_value(value, datatype, graph=graph)
    assert term == util.atomic_encode(graph, expected)
    assert util.atomic_decode(graph, term, official_class) == expected


def test_proprietary_enum_uses_official_numeric_member():
    value = EnumeratedValue(
        name=NamedToken(canonical="proprietary-object-type-128"), proprietary_number=128
    )
    graph = Graph()
    term = rdf.bacnet_value(value, "BACnetObjectType", graph=graph)
    expected = basetypes.ObjectType(128)
    assert term == util.atomic_encode(graph, expected) == BACNET["ObjectType.128"]
    assert util.atomic_decode(graph, term, basetypes.ObjectType) == expected


@pytest.mark.parametrize("object_type", ["analog-input", "device", 128])
def test_object_identifier_matches_official_encoder(object_type):
    value = ObjectIdentifierValue(
        object_type=NamedToken(canonical=object_type)
        if isinstance(object_type, str)
        else object_type,
        instance=7,
    )
    graph = Graph()
    term = rdf.bacnet_value(value, graph=graph)
    official = primitivedata.ObjectIdentifier((object_type, 7))
    assert term == util.atomic_encode(graph, official)
    assert term.datatype == BACNET.objectIdentifier
    # BACpypes3's constructor supports its encoder's lexical form independently
    # of the RDF decoder's upstream URI identity assertion.
    assert primitivedata.ObjectIdentifier(str(term)) == official


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="BACpypes3 0.0.110 objectidentifier_decode compares URI datatype with 'is'",
)
def test_upstream_object_identifier_decoder_identity_bug():
    graph = Graph()
    official = _object_id("analog-input,7")
    term = util.atomic_encode(graph, official)
    assert util.atomic_decode(graph, term, primitivedata.ObjectIdentifier) == official


@pytest.mark.parametrize(
    "datatype,bits,official_class",
    [
        ("BACnetStatusFlags", [True, False, True, False], basetypes.StatusFlags),
        ("BACnetEventTransitionBits", [True, False, True], basetypes.EventTransitionBits),
        ("BACnetLimitEnable", [True, False], basetypes.LimitEnable),
    ],
)
def test_named_bit_lists_match_real_encoder_and_decoder(datatype, bits, official_class):
    value = GroupValue(delimiter="{", elements=[BooleanValue(value=bit) for bit in bits])
    graph = Graph()
    term = rdf.bacnet_value(value, datatype, graph=graph)
    expected_graph = Graph()
    official = official_class([int(bit) for bit in bits])
    expected = util.atomic_encode(expected_graph, official)
    assert list(Collection(graph, term)) == list(Collection(expected_graph, expected))
    assert util.atomic_decode(graph, term, official_class) == official


def test_device_and_object_queries_use_official_prepared_queries():
    doc = document(["NULL"])
    data = doc.model_dump(mode="json")
    data["objects"].append(
        {
            "identifier": {"object_type": "analog-input", "instance": 3},
            "object_type": "analog-input",
            "name": "Example input",
            "properties": [{"name": "present-value", "value": {"kind": "real", "value": "1.25"}}],
        }
    )
    doc = EpicsDocument.model_validate(data)
    graph = rdf.to_graph(doc, base_iri="urn:example:interop", deterministic=True)
    official = core.BACnetGraph(graph)
    devices = list(official.query(core.find_device_by_instance, device_instance=7))
    analog_inputs = list(
        official.query(core.find_object_by_type, objtype=basetypes.ObjectType("analog-input"))
    )
    assert len(devices) == len(analog_inputs) == 1
    device, analog_input = devices[0][0], analog_inputs[0][0]
    device_objects = list(
        official.query(core.find_object_by_type, objtype=basetypes.ObjectType("device"))
    )
    assert len(device_objects) == 1
    device_object = device_objects[0][0]
    assert device == URIRef("urn:example:interop/device/7")
    assert device_object != device
    assert device_object == core.object_node(device, _object_id("device,7"))
    assert analog_input == core.object_node(device, _object_id("analog-input,3"))
    assert (device, BACNET.contains, device_object) in graph
    assert (device, RDF.type, BACNET.Device) in graph
    assert (device, BACNET.contains, analog_input) in graph
    assert graph.value(analog_input, BACNET["object-name"]) == Literal("Example input")
    assert graph.value(analog_input, BACNET["object-identifier"]) == util.atomic_encode(
        graph, _object_id("analog-input,3")
    )
    present_value = graph.value(analog_input, BACNET["present-value"])
    assert present_value == util.atomic_encode(graph, primitivedata.Real(1.25))
    assert util.atomic_decode(graph, present_value, primitivedata.Real) == primitivedata.Real(1.25)
    size = len(graph)
    proxy = core.DeviceGraph(official, device).create_object(_object_id("analog-input,3"))
    assert proxy._object_iri == analog_input
    assert len(graph) == size


def test_cross_codec_identity_covers_every_epics_value_kind():
    doc = document(
        [
            "NULL",
            "TRUE",
            "42",
            "1.25",
            "X'00AB'",
            '"Example"',
            "no-fault-detected",
            "?",
            "*",
            "(Tuesday, 2-January-2024)",
            "12:34:56.78",
            "(analog-input, 3)",
            "[2] 42",
            "{TRUE, 42, NULL}",
            "(2-January-2024)-(3-January-2024)",
        ]
    )
    assert {entry.value.kind for entry in doc.objects[0].properties} == rdf.VALUE_KINDS
    cycle = rdf.loads(
        rdf.dumps(yaml.loads(yaml.dumps(json.loads(json.dumps(doc)))), deterministic=True)
    )
    assert cycle == doc
    assert json.loads(json.dumps(cycle)) == doc


def test_untyped_enum_does_not_invent_an_official_enumeration_term():
    value = EnumeratedValue(name=NamedToken(canonical="invented-state"))
    term = rdf.bacnet_value(value, graph=Graph())
    assert not isinstance(term, URIRef) or not str(term).startswith(str(BACNET))


@pytest.mark.parametrize(
    "datatype,official_class,selected,length",
    [
        ("BACnetServicesSupported", basetypes.ServicesSupported, [12, 47], 49),
        ("BACnetObjectTypesSupported", basetypes.ObjectTypesSupported, [0, 41], 63),
    ],
)
def test_support_bits_preserve_real_encoder_legacy_member_spellings(
    datatype, official_class, selected, length
):
    bits = [int(index in selected) for index in range(length)]
    value = GroupValue(delimiter="{", elements=[BooleanValue(value=bool(bit)) for bit in bits])
    graph = Graph()
    term = rdf.bacnet_value(value, datatype, graph=graph)
    official_graph = Graph()
    expected_value = official_class(bits)
    expected = util.atomic_encode(official_graph, expected_value)
    assert list(Collection(graph, term)) == list(Collection(official_graph, expected))
    assert util.atomic_decode(graph, term, official_class) == expected_value


@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason="BACpypes3 0.0.110 bitstring_decode treats RDF Literal numeric positions as names",
)
def test_upstream_generic_numeric_bit_decoder_bug():
    graph = Graph()
    official = primitivedata.BitString([1, 0, 1])
    term = util.atomic_encode(graph, official)
    assert util.atomic_decode(graph, term, primitivedata.BitString) == official


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="BACpypes3 0.0.110 atomic_encode dispatches Double through its Real superclass",
)
def test_upstream_double_dispatch_bug():
    from rdflib import XSD

    term = util.atomic_encode(Graph(), primitivedata.Double(1.25))
    assert term.datatype == XSD.double


@pytest.mark.parametrize("pattern", [False, True])
def test_datetime_projection_matches_official_encoder_decoder(pattern):
    day = (
        DateValue(year=2024, month=WildcardValue(), day=WildcardValue(), weekday=WildcardValue())
        if pattern
        else DateValue(year=2024, month=1, day=2, weekday=2)
    )
    time = (
        TimeValue(
            hour=WildcardValue(), minute=30, second=WildcardValue(), hundredth=WildcardValue()
        )
        if pattern
        else TimeValue(hour=12, minute=34, second=56, hundredth=78)
    )
    value = GroupValue(delimiter="(", elements=[day, time])
    official = (
        basetypes.DateTime("2024-*-* * *:30:*.*")
        if pattern
        else basetypes.DateTime(datetime(2024, 1, 2, 12, 34, 56, 780000))
    )
    graph = Graph()
    term = rdf.bacnet_value(value, "BACnetDateTime", graph=graph)
    assert term == util.datetime_encode(graph, official)
    assert util.datetime_decode(graph, term) == official


def test_date_range_projection_matches_official_sequence():
    start = DateValue(year=2024, month=1, day=2, weekday=2)
    end = DateValue(year=2024, month=1, day=3, weekday=3)
    graph = Graph()
    node = rdf.bacnet_value(DateRangeValue(start=start, end=end), graph=graph)
    assert graph.value(node, BACNET["start-date"]) == util.atomic_encode(
        graph, primitivedata.Date(date(2024, 1, 2))
    )
    assert graph.value(node, BACNET["end-date"]) == util.atomic_encode(
        graph, primitivedata.Date(date(2024, 1, 3))
    )
    restored = util.graph_to_sequence(graph, node, basetypes.DateRange)
    assert restored.startDate == primitivedata.Date(date(2024, 1, 2))
    assert restored.endDate == primitivedata.Date(date(2024, 1, 3))


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="BACpypes3 0.0.110 ObjectProxy getter calls missing BACnetGraph.value",
)
def test_upstream_object_proxy_getter_bug():
    graph = core.BACnetGraph(Graph())
    device = graph.create_device(None, _object_id("device,7"))
    proxy = device.create_object(_object_id("analog-input,3"))
    assert proxy.objectIdentifier is not None


def _registry():
    import json as standard_json
    from importlib.resources import files

    return standard_json.loads(
        files("ace_epics.codecs").joinpath("data/bacpypes3-rdf.json").read_text()
    )


def test_registry_provenance_and_all_released_enum_members():
    registry = _registry()
    assert registry["version"] == version("bacpypes3")
    assert registry["source"]["wheel_sha256"] == (
        "02abc0c9e7e92d7061727898ba00204ec072f1d451a63c4e7de76015b5b14911"
    )
    assert registry["source"]["wheel_url"].endswith("bacpypes3-0.0.110-py3-none-any.whl")
    assert len(registry["enums"]) == 82
    for name, definition in registry["enums"].items():
        official_class = getattr(basetypes, name)
        for member, number in definition["values"].items():
            official = official_class(number)
            assert official.asn1 == member
            graph = Graph()
            value = EnumeratedValue(name=NamedToken(canonical=member))
            term = rdf.bacnet_value(value, "BACnet" + name, graph=graph)
            assert term == util.atomic_encode(graph, official), (name, member)
            assert util.atomic_decode(graph, term, official_class) == official


def test_registry_all_released_bit_names_and_positions():
    registry = _registry()
    assert len(registry["bitstrings"]) == 10
    for name, definition in registry["bitstrings"].items():
        official_class = getattr(basetypes, name)
        assert definition["values"] == official_class._bitstring_names
        assert definition["length"] == official_class._bitstring_length


@pytest.mark.parametrize(
    "name,number",
    [
        ("datepattern-value", 41),
        ("datetimepattern-value", 43),
        ("timepattern-value", 49),
        ("color", 63),
        ("color-temperature", 64),
    ],
)
def test_object_type_aliases_and_newer_types_use_actual_encoder_terms(name, number):
    graph = Graph()
    term = rdf.bacnet_value(
        EnumeratedValue(name=NamedToken(canonical=name)), "BACnetObjectType", graph=graph
    )
    official = basetypes.ObjectType(number)
    assert term == util.atomic_encode(graph, official)
    assert util.atomic_decode(graph, term, basetypes.ObjectType) == official
    identifier = rdf.bacnet_value(
        ObjectIdentifierValue(object_type=NamedToken(canonical=name), instance=7), graph=graph
    )
    assert identifier == util.atomic_encode(graph, primitivedata.ObjectIdentifier((number, 7)))


@pytest.mark.parametrize("raw_name", ["max-manager", "max-master"])
def test_property_name_alias_uses_released_predicate_and_preserves_declaration(raw_name):
    data = document(["42"]).model_dump(mode="json")
    data["objects"][0]["properties"] = [
        {"name": raw_name, "value": {"kind": "integer", "value": 42}}
    ]
    doc = EpicsDocument.model_validate(data)
    graph = rdf.to_graph(doc, base_iri="urn:example:alias", deterministic=True)
    subject = URIRef("urn:example:alias/device/7/device,7")
    assert graph.value(subject, BACNET["max-master"]) == Literal(
        42, datatype=util.XSD.nonNegativeInteger
    )
    assert graph.value(subject, BACNET["max-manager"]) is None
    assert rdf.from_graph(graph) == doc


@pytest.mark.parametrize(
    "value,datatype",
    [
        (EnumeratedValue(name=NamedToken(canonical="invented-state")), "BACnetReliability"),
        (IntegerValue(value=42), "BACnetARRAY[N] of BACnetPropertyIdentifier"),
        (BooleanValue(value=True), "Unsigned"),
        (RealValue(value=Decimal("1.25")), "Integer"),
        (
            ObjectIdentifierValue(object_type=NamedToken(canonical="invented-object"), instance=7),
            None,
        ),
        (ObjectIdentifierValue(object_type=1024, instance=7), None),
        (ObjectIdentifierValue(object_type=0, instance=4194304), None),
        (
            EnumeratedValue(name=NamedToken(canonical="proprietary-1024"), proprietary_number=1024),
            "BACnetObjectType",
        ),
        (IntegerValue(value=-1), "BACnetReliability"),
        (IntegerValue(value=4294967296), "BACnetReliability"),
    ],
)
def test_unrepresentable_values_do_not_invent_official_terms(value, datatype):
    graph = Graph()
    term = rdf.bacnet_value(value, datatype, graph=graph)
    assert not isinstance(term, Literal)
    assert not isinstance(term, URIRef) or not str(term).startswith(str(BACNET))
    assert graph.value(term, RDF.type) is not None
    assert str(graph.value(term, RDF.type)).startswith(rdf.NAMESPACE)


def test_upstream_enum_constructor_overflow_is_not_wire_representable():
    import struct

    with pytest.raises(ValueError):
        basetypes.Reliability(-1)
    overflowing = basetypes.Reliability(4294967296)
    assert util.atomic_encode(Graph(), overflowing) == BACNET["Reliability.4294967296"]
    with pytest.raises(struct.error):
        overflowing.encode()
    with pytest.raises(ValueError):
        primitivedata.ObjectIdentifier((1024, 7))


def test_previous_all_extension_graph_still_round_trips():
    from pathlib import Path

    fixture = Path(__file__).parents[2] / "fixtures/rdf/legacy-ace-epics.ttl"
    expected = document(["NULL", "1.25", "(Tuesday, 2-January-2024)"])
    result = rdf.parse(fixture.read_text())
    assert result.diagnostics == []
    assert result.document is not None
    assert result.document == expected
    assert rdf.loads(rdf.dumps(result.document, deterministic=True)) == expected


@pytest.mark.parametrize(
    "name,number",
    [
        ("datepattern-value", 41),
        ("datetimepattern-value", 43),
        ("timepattern-value", 49),
        ("color", 63),
        ("color-temperature", 64),
    ],
)
def test_object_alias_graph_uses_official_object_node_and_keeps_source_type(name, number):
    data = document(["NULL"]).model_dump(mode="json")
    data["objects"].append(
        {
            "identifier": {"object_type": name, "instance": 3},
            "object_type": name,
            "name": "Example typed object",
            "properties": [],
        }
    )
    doc = EpicsDocument.model_validate(data)
    graph = rdf.to_graph(doc, base_iri="urn:example:types", deterministic=True)
    root = URIRef("urn:example:types/device/7")
    identifier = cast(primitivedata.ObjectIdentifier, primitivedata.ObjectIdentifier((number, 3)))
    obj = core.object_node(root, identifier)
    assert (root, BACNET.contains, obj) in graph
    assert graph.value(obj, BACNET["object-identifier"]) == util.atomic_encode(graph, identifier)
    assert graph.value(obj, BACNET["object-type"]) == util.atomic_encode(
        graph, basetypes.ObjectType(number)
    )
    assert rdf.from_graph(graph) == doc


def test_unknown_named_object_header_is_explicit_extension_and_round_trips():
    data = document(["NULL"]).model_dump(mode="json")
    data["objects"].append(
        {
            "identifier": {"object_type": "invented-object", "instance": 3},
            "object_type": "invented-object",
            "name": "Example extension object",
            "properties": [],
        }
    )
    doc = EpicsDocument.model_validate(data)
    graph = rdf.to_graph(doc, base_iri="urn:example:unknown", deterministic=True)
    obj = URIRef("urn:example:unknown/device/7/invented-object,3")
    identifier = graph.value(obj, BACNET["object-identifier"])
    assert not isinstance(identifier, Literal)
    assert graph.value(identifier, RDF.type) == URIRef(rdf.NAMESPACE + "ObjectIdentifierValue")
    assert graph.value(obj, BACNET["object-type"]) != BACNET["ObjectType.invented-object"]
    assert rdf.from_graph(graph) == doc
