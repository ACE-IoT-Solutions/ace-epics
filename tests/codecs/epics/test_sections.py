"""Literal and keyword traceability for 135.1 Clause 4.5 sections."""

import pytest

from ace_epics.codecs.epics import dumps, parse, sections
from ace_epics.model import CharacterSet, SpecialFunctionality
from ace_epics.model.restrictions import ALLOWED_DEFAULT_RESTRICTIONS
from ace_epics.model.timers import FailTimes
from tests.fixtures_build_epics import minimal
from tests.unit.model.test_datalink import OPTIONS


@pytest.mark.parametrize("option", OPTIONS)
def test_native_every_data_link_literal(option):
    issues = sections.Issues(True)
    assert sections.data_links(option.canonical_text(), 1, issues) == [option]
    assert issues.diagnostics == []


@pytest.mark.parametrize("literal", list(CharacterSet))
def test_native_every_character_set_literal(literal):
    issues = sections.Issues(True)
    assert sections.character_sets(str(literal), 1, issues) == [literal]
    assert not issues.diagnostics


@pytest.mark.parametrize("name", [n for n in SpecialFunctionality.model_fields if n != "unknown"])
def test_native_every_special_keyword(name):
    field = SpecialFunctionality.model_fields[name]
    numeric = name in {"max_apdu_size", "segmented_requests_window", "segmented_responses_window"}
    issues = sections.Issues(True)
    result = sections.special((field.alias or name) + (": 4" if numeric else ""), 1, issues)
    assert getattr(result, name) == (4 if numeric else True)
    assert not issues.diagnostics


@pytest.mark.parametrize("datatype,allowed", ALLOWED_DEFAULT_RESTRICTIONS.items())
def test_native_every_default_datatype_and_restriction(datatype, allowed):
    contents = "; ".join(name.replace("_", " ") + ": 1" for name in sorted(allowed))
    issues = sections.Issues(True)
    result = sections.defaults(datatype.replace("_", "-") + ": <" + contents + ">", 1, issues)
    restriction = getattr(result, datatype)
    assert restriction is not None
    assert all(getattr(restriction, name) is not None for name in allowed)
    assert not issues.diagnostics and not result.warnings()


@pytest.mark.parametrize("name", [n for n in FailTimes.model_fields if n != "extra"])
def test_native_every_timer_keyword(name):
    field = FailTimes.model_fields[name]
    issues = sections.Issues(True)
    result = sections.timers(
        (field.serialization_alias or field.alias or name) + ": 1.5", 1, issues
    )
    assert getattr(result, name) == 1.5
    assert all(d.code == "P-TIMERS-INCOMPLETE" for d in issues.diagnostics)


@pytest.mark.parametrize("flags", ["Initiate", "Execute", "Execute Initiate"])
def test_native_service_flag_forms(flags):
    issues = sections.Issues(True)
    result = sections.services("ReadProperty " + flags, 1, issues)
    assert result[0].name.canonical == "read-property"
    assert result[0].initiate == ("Initiate" in flags)
    assert result[0].execute == ("Execute" in flags)
    assert not issues.diagnostics


@pytest.mark.parametrize("flags", ["", "Unknown", "Execute Unknown"])
def test_native_rejects_missing_and_unknown_service_flags(flags):
    issues = sections.Issues(True)
    assert sections.services("ReadProperty " + flags, 1, issues) == []
    assert issues.diagnostics[0].code == "P-SERVICE-FLAGS"


@pytest.mark.parametrize(
    "flags", ["", "Createable", "Creatable", "Deleteable", "Deleteable Createable"]
)
def test_native_object_type_flag_forms(flags):
    issues = sections.Issues(True)
    result = sections.object_types("Analog Value " + flags, 1, issues)
    assert result[0].name.canonical == "analog-value"
    assert result[0].createable == ("Createable" in flags or "Creatable" in flags)
    assert result[0].deleteable == ("Deleteable" in flags)
    assert not issues.diagnostics


@pytest.mark.parametrize(
    "record,code",
    [
        ("Router: 1", "P-SPECIAL-FLAG"),
        ("Maximum APDU size in octets: 1.5", "P-SPECIAL-INTEGER"),
        ("real: invalid", "P-DEFAULT-RESTRICTION"),
        ("Notification Fail Time: -1.0", "P-TIMER-VALUE"),
    ],
)
def test_native_invalid_parameter_rules(record, code):
    issues = sections.Issues(True)
    parser = (
        sections.special
        if code.startswith("P-SPECIAL")
        else sections.defaults
        if code.startswith("P-DEFAULT")
        else sections.timers
    )
    parser(record, 1, issues)
    assert code in [d.code for d in issues.diagnostics]


def test_section_order_completeness_duplicates_and_database_last():
    text = dumps(minimal())
    mutations = [
        (
            text.replace("BIBBs Supported: {", 'Vendor Name: "Duplicate"\r\nBIBBs Supported: {'),
            "P-DUPLICATE-SECTION",
        ),
        (text.replace("BIBBs Supported: {", "Unknown Section: {"), "P-SECTIONS-INCOMPLETE"),
        (
            text[: text.index("Fail Times:")]
            + text[text.index("List of Objects") : text.index(sections.END)]
            + text[text.index("Fail Times:") : text.index("List of Objects")]
            + sections.END
            + "\r\n",
            "P-DATABASE-LAST",
        ),
    ]
    for content, code in mutations:
        if code:
            assert code in [d.code for d in parse(content, strict=True).diagnostics]
    lines = text.splitlines()
    lines[2], lines[3] = lines[3], lines[2]
    assert "P-SECTION-ORDER" in [
        d.code for d in parse("\r\n".join(lines) + "\r\n", strict=True).diagnostics
    ]


def test_extension_defaults_allowed_values_and_unknown_timers():
    issues = sections.Issues(False)
    result = sections.defaults(
        "time <resolution: 1>\ncharacter string: <maximum length string: 20>", 1, issues
    )
    assert result.extra["time"].resolution is not None
    assert result.character_string is not None
    assert result.character_string.maximum_length_string == 20
    allowed = sections.restrictions("<allowed values: amperes, milliamperes>", 1, issues)
    assert allowed.allowed_values is not None
    assert [n.canonical for n in allowed.allowed_values] == ["amperes", "milliamperes"]
    sections.restrictions("<allowed values: 3>", 1, issues)
    assert sections.timers("Custom Timer: 2.5", 1, issues).extra == {"Custom Timer": 2.5}
    assert {"P-DEFAULT-TYPE", "P-ALLOWED-VALUES", "P-TIMER-UNKNOWN"} <= {
        d.code for d in issues.diagnostics
    }


def test_invalid_object_flags_and_data_link_ranges():
    issues = sections.Issues(True)
    assert sections.object_types("Analog Value Createable Unknown", 1, issues) == []
    assert (
        sections.data_links("Point-To-Point. Modem, Autobaud range: 57600 to 9600", 1, issues) == []
    )
    assert {"P-OBJECT-TYPE", "P-DATA-LINK"} == {d.code for d in issues.diagnostics}


@pytest.mark.parametrize(
    "text,value",
    [
        ('"Ace IoT Solutions"', "Ace IoT Solutions"),
        ("'ACME'", "ACME"),
        ("\"He said 'hi'\"", "He said 'hi'"),
        ("'say \"x\"'", 'say "x"'),
        ('"abc', "abc"),
        ('"a -- b" -- comment', "a -- b"),
    ],
)
def test_general_string_seeds(text, value):
    issues = sections.Issues(False)
    assert sections.quoted_string(text, 1, issues) == value
    assert not any(d.severity == "error" for d in issues.diagnostics)


def test_bibb_empty_case_alias_and_missing_braces():
    issues = sections.Issues(True)
    assert sections.bibbs("", 1, issues) == []
    assert [b.canonical for b in sections.bibbs("DS-RP-B\nDM-DDB-A", 1, issues)] == [
        "ds-rp-b",
        "dm-ddb-a",
    ]
    text = dumps(minimal()).replace("BIBBs Supported: {", "BIBBS SUPPORTED: {")
    assert not parse(text, strict=True).has_errors
    invalid = text.replace("BIBBS SUPPORTED: {\r\n}", "BIBBS SUPPORTED: DS-RP-B")
    assert "P-SECTION-BRACE" in [d.code for d in parse(invalid, strict=True).diagnostics]
