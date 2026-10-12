"""Clause5 access and restriction checks include object header metadata."""

from ace_epics.knowledge import JsonKnowledgeProvider, ObjectDefinition, PropertySpec
from ace_epics.model import Access, PropertyMetadata, Restrictions
from ace_epics.validation import Query, validate
from tests.validation.conftest import SyntheticProvider, entry, integer, token


def test_header_access_restrictions_and_variants(document, provider):
    obj = document.objects[1]
    obj.header_metadata["object-name"] = PropertyMetadata(
        access=Access.W, restrictions=Restrictions(maximum_length_string=12), not_readable=True
    )
    query = Query(document, provider)
    assert query.is_writable(obj, "object-name")
    assert not query.is_readable(obj, "object-name")
    assert query.limits(obj, "object-name").maximum_length_string == 12
    copy = obj.model_copy(deep=True)
    copy.identifier.instance += 1
    copy.header_metadata.clear()
    document.objects.append(copy)
    assert len(query.variants("analog-output")) == 2


def test_required_writable_and_read_only_headers(document, provider):
    class Headers(SyntheticProvider):
        def object_definition(self, object_type, revision):
            definition = super().object_definition(object_type, revision)
            assert definition is not None
            definition.properties["object-name"] = PropertySpec(
                requirement="required", datatype="CharacterString", access="W"
            )
            definition.properties["object-type"] = PropertySpec(
                requirement="required", datatype="BACnetObjectType", read_only=True
            )
            return definition

    knowledge = Headers()
    assert validate(document, knowledge, rules=["C5-12"]).results[0].outcome == "fail"
    for obj in document.objects:
        obj.header_metadata["object-name"] = PropertyMetadata(access=Access.W)
    assert validate(document, knowledge, rules=["C5-12"]).results[0].outcome == "pass"
    document.objects[1].header_metadata["object-type"] = PropertyMetadata(access=Access.W)
    assert validate(document, knowledge, rules=["C5-18"]).results[0].outcome == "fail"


def test_legacy_property_names_resolve_without_changing_source(document):
    obj = document.device
    obj.properties.append(entry("Max_Master", integer(31)))
    query = Query(document, JsonKnowledgeProvider())
    assert query.value(obj, "max-manager") == integer(31)
    assert query.access(obj, "Max_Master") == Access.R
    assert obj.properties[-1].name == token("max-master")


def test_removed_historical_properties_remain_checked(document, provider):
    class History(SyntheticProvider):
        def object_definition(self, object_type, revision):
            definition = super().object_definition(object_type, revision)
            assert definition is not None
            return ObjectDefinition.model_validate(
                {
                    **definition.model_dump(),
                    "historical_properties": {
                        "subordinate-proxy-enable": PropertySpec(
                            requirement="optional", datatype="Boolean", removed_rev=17
                        )
                    },
                }
            )

    document.device.properties.append(entry("Slave_Proxy_Enable", integer(1)))
    report = validate(document, History(), rules=["C5-15"])
    assert report.results[0].outcome == "fail"
    assert report.diagnostics[0].property == "subordinate-proxy-enable"


def test_header_restriction_datatype_is_checked(document, provider):
    document.objects[1].header_metadata["object-name"] = PropertyMetadata(
        restrictions=Restrictions(minimum=integer(1))
    )
    report = validate(document, provider, rules=["S-04"])
    assert report.results[0].outcome == "fail"
    assert report.diagnostics[0].property == "object-name"


def test_legacy_property_list_numeric_identifier_uses_canonical_alias(document, provider):
    from tests.validation.conftest import group, set_value

    obj = document.device
    obj.properties.append(entry("Max_Master", integer(31)))
    ids = provider.property_identifiers()
    names = Query(document, provider).expected_property_list(obj)
    assert token("max-manager") in names
    set_value(obj, "property-list", group([integer(ids[n.canonical]) for n in names]))
    assert validate(document, provider, rules=["C5-16"]).results[0].outcome == "pass"
