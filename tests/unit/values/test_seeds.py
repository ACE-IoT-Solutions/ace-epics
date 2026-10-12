from decimal import Decimal

import pytest
from pydantic import TypeAdapter

from ace_epics.diagnostics import Severity
from ace_epics.values import (
    GroupValue,
    IntegerValue,
    ObjectIdentifierValue,
    Preserving,
    RealValue,
    ValueNode,
    as_bitstring,
    as_date,
    as_datetime,
    as_list_of,
    parse_restrictions,
    parse_value,
    render,
    render_restrictions,
)


@pytest.mark.parametrize(
    "source,kind",
    [
        ("NULL", "null"),
        ("null", "null"),
        ("Null", "null"),
        ("T", "boolean"),
        ("true", "boolean"),
        ("False", "boolean"),
        ("f", "boolean"),
        ("12345", "integer"),
        ("-111", "integer"),
        ("-0", "integer"),
        ("1.23", "real"),
        ("0.02", "real"),
        ("1.0", "real"),
        ("X'001122'", "octet-string"),
        ("x'ab'", "octet-string"),
        ("{T,T,F}", "group"),
        ("{TRUE, TRUE, FALSE}", "group"),
        ("{T,T,?}", "group"),
        ("Object_Type", "enumerated"),
        ("object-type", "enumerated"),
        ("proprietary-object-type-653", "enumerated"),
        ("(Monday, 24-January-1998)", "date"),
        ("(Monday, *-January-1998)", "date"),
        ("(24-January-1998)", "date"),
        ("2:05:44.00", "time"),
        ("16:54:59.99", "time"),
        ("16:54:*.*", "time"),
        ("(analog-input, 56)", "object-identifier"),
        ("(proprietary 700,1)", "object-identifier"),
        ("{1, {2, 3}, 4}", "group"),
        ("(1, 2, 3)", "group"),
        ("({1,2},{3,4})", "group"),
        ("[2] 5", "context-tagged"),
        ("5", "integer"),
    ],
)
def test_normative_value_seeds(source, kind):
    value, diagnostics = parse_value(source, strict=True)
    assert value.kind == kind
    assert not diagnostics


@pytest.mark.parametrize(
    "source,code",
    [
        (".02", "V-REAL-NOTATION"),
        ("-.02", "V-REAL-NOTATION"),
        ("5.", "V-REAL-NOTATION"),
        ("1E38", "V-REAL-NOTATION"),
        ("X'001'", "V-ODD-OCTETS"),
        ("proprietary-object-type", "V-PROPRIETARY"),
        ("(Monday, 24-January-1998", "V-UNBALANCED"),
        ("(analog-input 56)", "V-MISSING-COMMA"),
        ("{1,2", "V-UNBALANCED"),
        ("{TRUE FALSE, FALSE}", "V-MISSING-COMMA"),
        ("{1,}", "V-TRAILING-COMMA"),
        ("{1)", "V-CLOSER"),
        ("5}", "V-CLOSER"),
        ("8:00", "V-TIME-PRECISION"),
        ("18:50:21.2", "V-TIME-PRECISION"),
        ("(Mon, 2-Jan-2007)", "V-DATE-ABBREVIATION"),
        ("{1,?}", "V-NESTED-UNSPECIFIED"),
        ("X'zz'", "V-OCTETS"),
        ("[bad] 5", "V-TAG"),
        ("[2 5", "V-TAG"),
    ],
)
def test_deviation_matrix(source, code):
    _, findings = parse_value(source)
    assert code in {d.code for d in findings}
    _, strict = parse_value(source, strict=True)
    assert any(d.code == code and d.severity == Severity.ERROR for d in strict)


@pytest.mark.parametrize(
    "source",
    [
        '"zone, east"',
        '""',
        '"1.2 "',
        '{"Off","On_High"}',
        "58.1",
        "-50.0",
        "FALSE",
        "{T,T, -- row\nT}",
        "(TRUE, TRUE, FALSE)",
        "{Monday, Tuesday, Wednesday}",
        "NO_FAULT_DETECTED",
        "(*-*-*)",
        "*:*:*.*",
        "{(*-*-*),*:*:*.*}",
        "{(5-September-2001)-(10-June-2002)}",
        "((19-February-2001),{(24-December-2001)-(4-January-2002)})",
        "(16-December-2001,13:15:07.32)",
        "{{(Monday,24-January-2000),18:50:21.02},{(*-*-*),*:*:*.*}}",
        "{6,3,5}",
        "{09:02:31.05,14:07:21.57}",
        "{NULL,2,NULL}",
        "(ALARM)",
        "(3)",
        "()",
        "((life-safety-zone, 5))",
        "{({8:00,ACTIVE},{17:00,INACTIVE}),({8:00,ACTIVE})}",
        "{,0,,{TRUE,FALSE}}",
        "[1] {(analog-input,3),85}",
        "?",
    ],
)
def test_annex_notation_inventory(source):
    value, findings = parse_value(source)
    assert not [d for d in findings if d.severity == Severity.ERROR]
    again, _ = parse_value(render(value))
    assert again.kind == value.kind


def test_classifiers_and_lexical_preservation():
    bits, _ = parse_value("{T,F,?}")
    assert isinstance(bits, GroupValue)
    assert as_bitstring(bits) == [True, False, None]
    other_bits = parse_value("{T,X,F}")[0]
    assert isinstance(other_bits, GroupValue)
    assert as_bitstring(other_bits) is None
    assert as_list_of(bits, "boolean") is None
    integers = parse_value("(1,2,3)")[0]
    assert isinstance(integers, GroupValue)
    assert as_list_of(integers, "integer")
    datetime, _ = parse_value("{(1-January-2001), 8:00:00.00}")
    assert isinstance(datetime, GroupValue)
    assert as_datetime(datetime)
    assert as_date(datetime.elements[0])
    assert as_date(bits) is None
    assert as_datetime(bits) is None
    object_id = parse_value("(analog input, 56)")[0]
    assert isinstance(object_id, ObjectIdentifierValue)
    assert str(object_id.object_type) == "analog-input"
    value, _ = parse_value("(proprietary 700, 1)")
    assert isinstance(value, ObjectIdentifierValue)
    assert value.object_type == 700
    real, _ = parse_value("1.2300")
    assert isinstance(real, RealValue)
    assert real.value == Decimal("1.23")
    assert render(real, Preserving) == "1.2300"
    assert render(parse_value("T")[0], Preserving) == "T"
    assert render(parse_value("8:00")[0], Preserving) == "08:00"
    assert render(parse_value("18:50:21.2")[0], Preserving) == "18:50:21.2"
    assert render(parse_value("`hello'")[0], Preserving) == "`hello'"


@pytest.mark.parametrize(
    "source",
    [
        "<minimum: 0.0; maximum: 20.0; resolution: 0.1>",
        "<maximum length string: 30>",
        "<allowed values: milliamperes, amperes>",
        "<allowed values: analog input, analog value>",
    ],
)
def test_normative_restriction_seeds(source):
    value, findings = parse_restrictions(source, strict=True)
    assert not findings
    assert parse_restrictions(render_restrictions(value), strict=True)[0] == value


@pytest.mark.parametrize(
    "source,code",
    [
        ("<minimum: 0, maximum: 9>", "R-SEPARATOR"),
        ("<minimum 0>", "R-COLON"),
        ("<bogus: 1>", "R-NAME"),
        ("<maximum length array10>", "R-COLON"),
        ("<minimum: 01-January-2001>", "R-BARE-DATE"),
        ("<minimum: 0", "R-BRACKETS"),
        ("minimum: 0", "R-BRACKETS"),
        ("<maximum length list: -1>", "R-LENGTH"),
        ("<minimum: 1; minimum: 2>", "R-DUPLICATE"),
        ("<minimum:>", "R-VALUE"),
    ],
)
def test_restriction_errors(source, code):
    _value, findings = parse_restrictions(source, strict=True)
    assert any(d.code == code and d.severity == Severity.ERROR for d in findings)


def test_json_ast_roundtrip_binary_and_nested():
    adapter = TypeAdapter(ValueNode)
    value, _ = parse_value("{X'FF00', [2] {TRUE, 1.20}}")
    assert adapter.validate_json(adapter.dump_json(value)) == value


@pytest.mark.parametrize(
    "source,code",
    [
        ("(33-January-2001)", "V-DATE-RANGE"),
        ("(1-2-2001)", "V-DATE-NAME"),
        ("(Bogus,1-January-2001)", "V-DATE"),
        ("(1-Bogus-2001)", "V-DATE"),
        ("25:99:99.99", "V-TIME-RANGE"),
        ("(1-January-2001)- 5", "V-DATE-RANGE"),
        ("1 garbage", "V-TRAILING"),
        ("proprietary " + ("9" * 5000), "V-INVALID"),
        ("9" * 5000, "V-NUMBER"),
        ("1e" + ("9" * 100), "V-NUMBER"),
        ("{" * 102 + "1" + "}" * 102, "V-DEPTH"),
    ],
)
def test_recovery_limits(source, code):
    assert code in {d.code for d in parse_value(source)[1]}


def test_helpers_edge_cases_and_semantic_equality():
    from ace_epics.values import CharacterStringValue, GroupValue, parse_restrictions
    from ace_epics.values.nodes import NullValue

    date = parse_value("(1-January-2001)")[0]
    assert as_date(GroupValue(delimiter="(", elements=[date])) == date
    assert date.__eq__(1) is NotImplemented
    first = parse_value("T")[0]
    second = parse_value("TRUE")[0]
    assert first == second
    assert hash(first) == hash(second)
    assert render(parse_value("X'001'")[0], Preserving) == "X'001'"
    assert render(parse_value("8:00:00")[0], Preserving) == "08:00:00"
    with pytest.raises(ValueError):
        render(CharacterStringValue(value="both \" and ' quotes"))
    with pytest.raises(TypeError):
        render(object())
    assert render(parse_value("{1,}")[0], Preserving) == "{1,}"
    assert parse_value("NULL W")[0] == NullValue()
    defaults = parse_restrictions("<minimum: 0; maximum: 10>")[0]
    explicit = parse_restrictions("<maximum: 7>")[0]
    merged = explicit.merged_over(defaults)
    assert isinstance(merged.minimum, IntegerValue) and isinstance(merged.maximum, IntegerValue)
    assert merged.minimum.value == 0 and merged.maximum.value == 7
    assert explicit.merged_over(None) == explicit
    assert not parse_restrictions("<;allowed values: 1, TRUE;>")[1]


def test_unspecified_datetime_fields_semantic_roundtrip():
    from pydantic import ValidationError

    from ace_epics.values import DateValue, TimeValue

    date = DateValue(day=None, month=None, year=None)
    time = TimeValue(hour=None, minute=None, second=None, hundredth=None)
    assert parse_value(render(date))[0] == date
    assert parse_value(render(time))[0] == time
    assert hash(parse_value(render(date))[0]) == hash(date)
    with pytest.raises(ValidationError):
        RealValue(value=Decimal("NaN"))


@pytest.mark.parametrize(
    "source,kind,field,expected",
    [
        (
            "present-value: 13.4 <minimum: 0.0; maximum: 20.0; resolution: 0.1>",
            "real",
            "minimum",
            Decimal("0.0"),
        ),
        (
            'description: "synthetic description" <maximum length string: 30>',
            "character-string",
            "maximum_length_string",
            30,
        ),
        (
            "units: milliamperes <allowed values: milliamperes, amperes>",
            "enumerated",
            "allowed_values",
            2,
        ),
        (
            "object-property-reference: (analog input, 12) "
            "<allowed values: analog input, analog value>",
            "object-identifier",
            "allowed_values",
            2,
        ),
    ],
)
def test_property_value_restriction_suffix_seeds(source, kind, field, expected):
    from ace_epics.lexer import tokenize
    from ace_epics.values import ValueParser

    tokens, _ = tokenize(source)
    parser = ValueParser(tokens[2:], strict=True)
    value = parser.parse()
    assert value.kind == kind
    restrictions, diagnostics = parse_restrictions(parser.tokens[parser.position :], strict=True)
    assert not diagnostics
    actual = getattr(restrictions, field)
    assert (
        len(actual)
        if isinstance(actual, list)
        else actual.value
        if hasattr(actual, "value")
        else actual
    ) == expected


@pytest.mark.parametrize(
    "source,field,value",
    [
        ("<minimum: 0>", "minimum", 0),
        ("<maximum: 100>", "maximum", 100),
        ("<resolution: 0.25>", "resolution", Decimal("0.25")),
        ("<maximum length string: 20>", "maximum_length_string", 20),
        ("<maximum length list: 10>", "maximum_length_list", 10),
        ("<maximum length array: 16>", "maximum_length_array", 16),
        ("<allowed values: active, inactive>", "allowed_values", 2),
    ],
)
def test_each_restriction_name(source, field, value):
    restrictions, diagnostics = parse_restrictions(source, strict=True)
    assert not diagnostics
    actual = getattr(restrictions, field)
    assert (
        len(actual)
        if isinstance(actual, list)
        else actual.value
        if hasattr(actual, "value")
        else actual
    ) == value


def test_angles_inside_string_and_inline_comment_boundary():
    value, diagnostics = parse_value('"literal <maximum length string: 3>" -- comment')
    from ace_epics.values import CharacterStringValue

    assert isinstance(value, CharacterStringValue)
    assert value.value == "literal <maximum length string: 3>"
    assert not diagnostics
