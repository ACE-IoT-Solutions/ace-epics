"""Valid strategies for every Phase 2 model; shared with codec round-trip tests."""

from hypothesis import strategies as st

from ace_epics.model import (
    Bibb,
    DefaultRestrictions,
    EpicsDocument,
    FailTimes,
    GeneralInformation,
    NamedToken,
    ObjectIdentifier,
    ObjectTypeSupport,
    PicsHeader,
    PropertyEntry,
    PropertyMetadata,
    Restrictions,
    ServiceSupport,
    SourceInfo,
    SpecialFunctionality,
    TestObject,
)
from ace_epics.model.datalink import (
    Arcnet,
    BacnetIp,
    BacnetIpv6,
    BacnetSc,
    Iso8802_3,
    MsTp,
    Other,
    PointToPoint,
    Zigbee,
)
from ace_epics.model.enums import CharacterSet
from ace_epics.values import BooleanValue, CharacterStringValue, IntegerValue, UnspecifiedValue

texts = st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=30)
names = st.sampled_from(["device", "analog-value", "binary-value", "multi-state-value"])
named_tokens = st.builds(NamedToken, canonical=names)
bibbs = st.builds(Bibb, canonical=st.sampled_from(["DS-RP-B", "DM-DDB-A"]))
headers = st.builds(PicsHeader, charset_code=st.integers(min_value=0, max_value=5))
general_information = st.builds(
    GeneralInformation,
    vendor_name=texts,
    product_name=texts,
    product_model_number=texts,
    product_description=texts,
)
service_support = st.builds(
    ServiceSupport,
    name=st.sampled_from(["ReadProperty", "Who-Is"]),
    initiate=st.just(True),
    execute=st.booleans(),
)
object_type_support = st.builds(
    ObjectTypeSupport, name=names, createable=st.booleans(), deleteable=st.booleans()
)
special_functionality = st.builds(
    SpecialFunctionality,
    max_apdu_size=st.one_of(st.none(), st.integers(min_value=0, max_value=65535)),
    router=st.booleans(),
)
values = st.one_of(
    st.builds(IntegerValue, value=st.integers()),
    st.builds(BooleanValue, value=st.booleans()),
    st.builds(CharacterStringValue, value=texts),
    st.builds(UnspecifiedValue),
)
restrictions = st.builds(
    Restrictions,
    minimum=st.one_of(
        st.none(), st.builds(IntegerValue, value=st.integers(min_value=-100, max_value=0))
    ),
    maximum_length_string=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
)
default_restrictions = st.builds(DefaultRestrictions, character_string=restrictions)
fail_times = st.builds(
    FailTimes,
    notification_fail_time=st.floats(
        min_value=0, max_value=1000, allow_nan=False, allow_infinity=False
    ),
)
property_entries = st.builds(
    PropertyEntry,
    name=st.sampled_from(["present-value", "description", "units"]),
    value=values,
    access=st.sampled_from(["R", "W", "C"]),
    restrictions=st.one_of(st.none(), restrictions),
    not_readable=st.booleans(),
)
header_metadata = st.dictionaries(
    st.sampled_from(["object-identifier", "object-name", "object-type"]),
    st.builds(
        PropertyMetadata,
        access=st.sampled_from(["R", "W", "C"]),
        restrictions=st.one_of(st.none(), restrictions),
        comment=st.one_of(st.none(), st.sampled_from(["Header comment", "Notes"])),
        not_readable=st.booleans(),
    ),
    max_size=3,
)
object_identifiers = st.builds(
    ObjectIdentifier, object_type=names, instance=st.integers(min_value=0, max_value=4194303)
)
source_info = st.builds(
    SourceInfo,
    path=st.one_of(st.none(), texts),
    encoding=st.sampled_from(["utf-8", "iso8859-1"]),
    mode=st.sampled_from(["strict", "lenient"]),
)
bauds = st.lists(
    st.sampled_from([9600, 19200, 38400, 57600, 76800]), min_size=1, max_size=4, unique=True
)
data_links = st.one_of(
    st.builds(Iso8802_3, media=st.sampled_from(["10BASE5", "10BASE2", "10BASET", "fiber"])),
    st.builds(Arcnet, media=st.just("fiber star")),
    st.builds(Arcnet, media=st.just("twisted pair, EIA-485"), baud_rates=bauds),
    st.builds(MsTp, role=st.sampled_from(["manager", "subordinate"]), baud_rates=bauds),
    st.builds(PointToPoint, medium=st.just("Modem"), autobaud=st.just((9600, 57600))),
    st.builds(BacnetIp, variant=st.sampled_from(["'DIX' Ethernet", "Other"])),
    st.builds(BacnetIpv6),
    st.builds(BacnetSc),
    st.builds(Zigbee),
    st.builds(Other),
)


@st.composite
def test_objects(draw):
    identifier = draw(object_identifiers)
    props = draw(st.lists(property_entries, unique_by=lambda p: p.name.canonical, max_size=3))
    return TestObject(
        identifier=identifier,
        name=draw(texts),
        object_type=identifier.object_type,
        properties=props,
        header_metadata=draw(header_metadata),
    )


@st.composite
def documents(draw):
    objects = draw(st.lists(test_objects(), unique_by=lambda obj: str(obj.identifier), max_size=4))
    return EpicsDocument(
        header=draw(headers),
        general=draw(general_information),
        bibbs=draw(st.lists(bibbs, max_size=3)),
        services=draw(st.lists(service_support, max_size=3)),
        object_types=draw(st.lists(object_type_support, max_size=3)),
        data_links=draw(st.lists(data_links, max_size=3)),
        character_sets=draw(st.lists(st.sampled_from(list(CharacterSet)), max_size=3)),
        special=draw(special_functionality),
        default_restrictions=draw(default_restrictions),
        fail_times=draw(fail_times),
        objects=objects,
        source=draw(st.one_of(st.none(), source_info)),
    )


@st.composite
def native_documents(draw):
    """Native-representable documents with all timers and one Device (Phase 3)."""
    safe_text = st.text(
        alphabet=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", max_size=30
    )
    doc = draw(documents())
    for field in GeneralInformation.model_fields:
        setattr(doc.general, field, draw(safe_text))
    doc.bibbs = list({b.canonical: b for b in doc.bibbs}.values())
    doc.services = [
        ServiceSupport(name="read-property", initiate=True, execute=draw(st.booleans()))
    ]
    doc.object_types = list({o.name.canonical: o for o in doc.object_types}.values())
    doc.character_sets = list(dict.fromkeys(doc.character_sets))
    for option in doc.data_links:
        if isinstance(option, MsTp) and 9600 not in option.baud_rates:
            option.baud_rates.insert(0, 9600)
    doc.default_restrictions = DefaultRestrictions()
    doc.fail_times = FailTimes.model_validate(
        {
            name: float(draw(st.integers(min_value=0, max_value=1000)))
            for name in FailTimes.model_fields
            if name != "extra"
        }
    )
    doc.objects = [o for o in doc.objects if str(o.object_type) != "device"]
    doc.objects.insert(
        0,
        TestObject(
            identifier=ObjectIdentifier(object_type="device", instance=999),
            name="Device",
            object_type="device",
        ),
    )
    for obj in doc.objects:
        obj.name = draw(safe_text)
        for prop in obj.properties:
            if isinstance(prop.value, CharacterStringValue):
                prop.value = CharacterStringValue(value=draw(safe_text))
    doc.diagnostics = []
    return EpicsDocument.model_validate(doc.model_dump())
