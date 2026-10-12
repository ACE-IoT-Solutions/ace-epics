"""RDF canonical object identities must not silently merge EPICS declarations."""

import pytest

from ace_epics.codecs import rdf
from ace_epics.diagnostics import EpicsError
from ace_epics.model import ObjectIdentifier, TestObject
from tests.codecs.serdes.test_interchange import document


def object_with_type(name, instance):
    return TestObject(
        identifier=ObjectIdentifier(object_type=name, instance=instance),
        object_type=name,
        name=f"Invented {name}",
    )


def test_canonical_object_alias_collision_raises_located_reader_error():
    doc = document()
    doc.objects.extend(
        [
            object_with_type("datepattern-value", 4),
            object_with_type("date-pattern-value", 4),
        ]
    )
    with pytest.raises(EpicsError) as error:
        rdf.to_graph(doc, base_iri="urn:example:alias-collision", deterministic=True)
    assert error.value.diagnostics[0].code == "RDF-SHAPE"
    assert "collide" in error.value.diagnostics[0].message


def test_distinct_instances_of_alias_types_remain_distinct():
    doc = document()
    doc.objects.extend(
        [
            object_with_type("datepattern-value", 4),
            object_with_type("date-pattern-value", 5),
        ]
    )
    graph = rdf.to_graph(doc, base_iri="urn:example:distinct-aliases", deterministic=True)
    assert rdf.from_graph(graph) == doc
