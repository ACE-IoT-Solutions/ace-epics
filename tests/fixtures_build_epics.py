"""Invented EPICS corpus; contains no standard-document extracts."""

import json
from pathlib import Path

from ace_epics.codecs.epics import dumps, parse
from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.model import (
    Bibb,
    CharacterSet,
    EpicsDocument,
    FailTimes,
    GeneralInformation,
    ObjectIdentifier,
    ObjectTypeSupport,
    PropertyEntry,
    Restrictions,
    ServiceSupport,
    SpecialFunctionality,
    TestObject,
)
from ace_epics.model.datalink import BacnetIp, MsTp
from ace_epics.values import (
    BooleanValue,
    CharacterStringValue,
    DateValue,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    ObjectIdentifierValue,
    RealValue,
    TimeValue,
    UnspecifiedValue,
)

BASE = Path(__file__).parent / "fixtures/epics"
TYPES = [
    "accumulator",
    "analog-input",
    "analog-output",
    "analog-value",
    "averaging",
    "binary-input",
    "binary-output",
    "binary-value",
    "calendar",
    "command",
    "device",
    "event-enrollment",
    "file",
    "group",
    "life-safety-point",
    "life-safety-zone",
    "loop",
    "multi-state-input",
    "multi-state-output",
    "multi-state-value",
    "notification-class",
    "program",
    "pulse-converter",
    "schedule",
    "trend-log",
    "network-port",
    "channel",
    "timer",
    "color",
    "audit-log",
]


def minimal():
    return EpicsDocument(
        general=GeneralInformation(
            vendor_name="Synthetic Works",
            product_name="Example Controller",
            product_model_number="SW-1",
            product_description="Invented conformance fixture",
        ),
        fail_times=FailTimes.model_validate(
            {
                name: 1.0
                for name in FailTimes.model_fields
                if name not in {"extra", "audit_notification_forwarder_fail_time"}
            }
        ),
    )


def full():
    provider = JsonKnowledgeProvider()
    doc = minimal()
    doc.services = [
        ServiceSupport(name=name, initiate=True, execute=True) for name in provider.services(30)
    ]
    doc.bibbs = [Bibb(canonical="DS-RP-B")]
    doc.object_types = [ObjectTypeSupport(name=name) for name in TYPES]
    doc.data_links = [
        BacnetIp(variant="'DIX' Ethernet"),
        MsTp(role="manager", baud_rates=[9600, 19200]),
    ]
    doc.character_sets = [CharacterSet.UTF8]
    doc.special = SpecialFunctionality(max_apdu_size=1476)
    for instance, name in enumerate(TYPES, 1):
        definition = provider.object_definition(name, 30)
        props = []
        if definition:
            for prop, spec in definition.properties.items():
                if (
                    prop in {"object-identifier", "object-name", "object-type", "property-list"}
                    or spec.requirement != "required"
                ):
                    continue
                value = UnspecifiedValue()
                if spec.datatype in {"Unsigned", "Unsigned16", "Unsigned32"}:
                    value = IntegerValue(value=1)
                elif spec.datatype == "Real":
                    value = RealValue(value="1.0")
                elif spec.datatype == "Boolean":
                    value = BooleanValue(value=False)
                elif spec.datatype == "CharacterString":
                    value = CharacterStringValue(value="Synthetic")
                elif spec.datatype == "BACnetBinaryPV":
                    value = EnumeratedValue(name="inactive")
                elif spec.datatype.startswith("BACnetARRAY[16]"):
                    value = GroupValue(delimiter="{", elements=[UnspecifiedValue()] * 16)
                elif "BACnetARRAY" in spec.datatype or "BACnetLIST" in spec.datatype:
                    value = GroupValue(delimiter="{", elements=[])
                access = spec.access if spec.access in {"W", "C"} else "R"
                props.append(PropertyEntry(name=prop, value=value, access=access))
        if name == "schedule":
            props.append(
                PropertyEntry(
                    name="weekly-schedule",
                    value=GroupValue(
                        delimiter="{", elements=[GroupValue(delimiter="(", elements=[])] * 7
                    ),
                )
            )
        if name == "analog-value":
            props.append(
                PropertyEntry(
                    name="description",
                    value=CharacterStringValue(value="Invented value"),
                    restrictions=Restrictions(maximum_length_string=30),
                    access="W",
                )
            )
        if name == "device":
            replacements = {
                "protocol-revision": IntegerValue(value=30),
                "protocol-version": IntegerValue(value=1),
                "segmentation-supported": EnumeratedValue(name="no-segmentation"),
                "object-list": GroupValue(
                    delimiter="{",
                    elements=[
                        ObjectIdentifierValue(object_type=typ, instance=i)
                        for i, typ in enumerate(TYPES, 1)
                    ],
                ),
                "protocol-services-supported": GroupValue(
                    delimiter="{",
                    elements=[
                        BooleanValue(value=True)
                        for _ in range(provider.services_bit_count(30) or 0)
                    ],
                ),
                "protocol-object-types-supported": GroupValue(
                    delimiter="{",
                    elements=[
                        BooleanValue(value=i in {provider.object_types(30)[typ] for typ in TYPES})
                        for i in range(provider.object_types_bit_count(30) or 0)
                    ],
                ),
            }
            conditional_values = {
                "local-time": TimeValue(hour=12, minute=0, second=0, hundredth=0),
                "local-date": DateValue(weekday=4, day=1, month=1, year=2026),
                "utc-offset": IntegerValue(value=0),
                "daylight-savings-status": BooleanValue(value=False),
                "active-cov-subscriptions": GroupValue(delimiter="(", elements=[]),
                "active-cov-multiple-subscriptions": GroupValue(delimiter="(", elements=[]),
                "serial-number": CharacterStringValue(value="SYNTHETIC-001"),
            }
            props.extend(
                PropertyEntry(name=key, value=value) for key, value in conditional_values.items()
            )
            for prop in props:
                if prop.name.canonical in replacements:
                    prop.value = replacements[prop.name.canonical]
        props.append(
            PropertyEntry(
                name="property-list",
                value=GroupValue(
                    delimiter="{", elements=[EnumeratedValue(name=p.name) for p in props]
                ),
            )
        )
        doc.objects.append(
            TestObject(
                identifier=ObjectIdentifier(object_type=name, instance=instance),
                name=f"Synthetic {name}",
                object_type=name,
                properties=props,
            )
        )
    # Revalidate the final assembled document so warnings describe its final shape.
    return EpicsDocument.model_validate(doc.model_dump())


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = text.encode("utf-8") if isinstance(text, str) else text
    path.write_bytes(content)
    result = parse(content)
    assert result.document is not None
    path.with_suffix(".expected.json").write_text(
        json.dumps(
            result.document.model_dump(mode="json", exclude={"source"}), indent=2, sort_keys=True
        )
        + "\n"
    )
    path.with_suffix(".expected_diagnostics.json").write_text(
        json.dumps(
            {
                mode: [d.code for d in parse(content, strict=mode == "strict").diagnostics]
                for mode in ["lenient", "strict"]
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    mini = dumps(minimal())
    baseline = dumps(full())
    write(BASE / "minimal.tpi", mini)
    write(BASE / "full.tpi", baseline)
    for name, values in {
        "values_scalar": [
            "NULL",
            "TRUE",
            "-123",
            "12.3",
            "X'0123'",
            '"synthetic"',
            "milliamperes",
            "?",
        ],
        "values_time": ["(Monday, 1-January-2024)", "12:30:15.25", "(*, *-*-*)"],
        "values_constructed": ["{TRUE,FALSE,?}", "[0] 2", "({1,2},{3,4})", "{}"],
        "markers": ["12.3 W <minimum: 0.0; maximum: 20.0> -- example", "? C -- @not-readable"],
        "identifier_forms": ["(analog-value, 6)", "(Analog_Value,6)", "(analog value, 6)"],
    }.items():
        doc = minimal()
        doc.objects = [
            TestObject(
                identifier=ObjectIdentifier(object_type="device", instance=1),
                name="Example",
                object_type="device",
            )
        ]
        text = dumps(doc)
        insert = "".join(
            f"    proprietary-fixture-{512 + i}: {value}\r\n" for i, value in enumerate(values)
        )
        text = text.replace("    object-type: device\r\n", "    object-type: device\r\n" + insert)
        write(BASE / (name + ".tpi"), text)
    write(
        BASE / "case_and_layout.tpi",
        baseline.replace("Vendor Name", "VENDOR NAME").replace("Product Name", "product name"),
    )
    deviations = {
        "line_endings": baseline.replace("\r\n", "\n"),
        "signature_gap": baseline.replace("PICS 0\r\n", "PICS 0\r\n\r\n"),
        "unquoted_general": baseline.replace(
            'Vendor Name: "Synthetic Works"', "Vendor Name: Synthetic Works"
        ),
        "baud_k": baseline.replace("9600, 19200", "9.6k, 19.2k"),
        "integer_timer": baseline.replace(
            "Notification Fail Time: 1.0", "Notification Fail Time: 1"
        ),
        "explicit_r": baseline.replace('vendor-name: "Synthetic"', 'vendor-name: "Synthetic" R'),
        "unknown_section": baseline.replace(
            "BIBBs Supported: {", "Vendor Feature: {\r\n  custom\r\n}\r\nBIBBs Supported: {"
        ),
    }
    for name, text in deviations.items():
        write(BASE / "lenient" / (name + ".tpi"), text)
    negatives = {
        "missing_signature": baseline.replace(
            "BACnet Protocol Implementation Conformance Statement\r\n", "", 1
        ),
        "missing_end": baseline.replace(
            "End of BACnet Protocol Implementation Conformance Statement\r\n", ""
        ),
        "wrong_headers": baseline.replace(
            '    object-name: "Synthetic analog-input"\r\n    object-type: analog-input',
            '    object-type: analog-input\r\n    object-name: "Synthetic analog-input"',
        ),
        "unknown_restriction": baseline.replace("maximum length string: 30", "mystery: 30"),
        "unbalanced_value": baseline.replace("present-value: 1.0", "present-value: {1.0", 1),
        "missing_instance": baseline.replace("(device, 11)", "(device)", 1),
    }
    for name, text in negatives.items():
        write(BASE / "negative" / (name + ".tpi"), text)
    more_deviations = {
        "missing_timers": baseline.replace("Fail Times: {", "Ignored Timers: {"),
        "several_bibbs": baseline.replace("  DS-RP-B\r\n", "  DS-RP-B DS-WP-B\r\n"),
        "unknown_data_link": baseline.replace("BACnet/IP, 'DIX' Ethernet", "LonTalk"),
        "incomplete_data_link": baseline.replace(
            "MS/TP manager. Baud rate(s): 9600, 19200", "MS/TP manager."
        ),
        "unknown_charset": baseline.replace("ISO 10646 (UTF-8)", "Custom Charset"),
        "special_typo": baseline.replace(
            "Maximum APDU size in octets: 1476", "BACmet/SC Direct Connect"
        ),
        "leading_ellipsis": baseline.replace("present-value: 1.0 C", "…present-value: 1.0 C", 1),
        "scientific_real": baseline.replace("present-value: 1.0 C", "present-value: 1E3 C", 1),
        "abbreviated_time": baseline.replace("present-value: 1.0 C", "present-value: 8:00 C", 1),
        "odd_octets": baseline.replace("present-value: 1.0 C", "present-value: X'3' C", 1),
        "trailing_comma": baseline.replace("present-value: 1.0 C", "present-value: {1.0,} C", 1),
        "missing_comma": baseline.replace("present-value: 1.0 C", "present-value: {1.0 2.0} C", 1),
        "restriction_colon": baseline.replace(
            "maximum length string: 30", "maximum length string 30"
        ),
    }
    for name, text in more_deviations.items():
        write(BASE / "lenient" / (name + ".tpi"), text)
    write(
        BASE / "negative/duplicate_identifier.tpi",
        baseline.replace("(analog-input, 2)", "(accumulator, 1)", 1).replace(
            "object-type: analog-input", "object-type: accumulator", 1
        ),
    )
    write(
        BASE / "negative/proprietary_extra.tpi",
        baseline.replace("(accumulator, 1)", "(proprietary 700, 1)", 1).replace(
            "object-type: accumulator", "object-type: proprietary 700", 1
        ),
    )
