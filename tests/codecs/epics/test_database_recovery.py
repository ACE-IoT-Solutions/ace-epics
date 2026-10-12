"""Malformed database input recovers at the next object (135.1 Clause 4.5.10)."""

import pytest

from ace_epics.codecs.epics.database import parse_database
from ace_epics.codecs.epics.sections import Issues

VALID = '{\nobject-identifier: (device, 1)\nobject-name: "D"\nobject-type: device\n}'


@pytest.mark.parametrize(
    "body,code,expected",
    [
        ("invalid", "P-DATABASE-ENTRY", 0),
        ("invalid\n" + VALID, "P-DATABASE-ENTRY", 1),
        (VALID + "\nstray", "P-DATABASE-ENTRY", 1),
        (VALID[:-1], "P-OBJECT-BRACE", 1),
        (VALID.replace('object-name: "D"', "object-name: 2"), "P-OBJECT-HEADERS", 0),
        (VALID.replace("object-type: device", "object-type: 2"), "P-OBJECT-HEADERS", 0),
        (
            VALID.replace("object-type: device", "object-type: device\ninvalid property line"),
            "P-PROPERTY",
            1,
        ),
        (
            VALID.replace("object-type: device", "object-type: device\npresent-value: 1)"),
            "P-VALUE-CLOSER",
            1,
        ),
    ],
)
def test_malformed_database_entries(body, code, expected):
    issues = Issues(False)
    result = parse_database(body, 10, issues)
    assert len(result) == expected
    assert code in [d.code for d in issues.diagnostics]
    assert all(d.line is None or d.line >= 10 for d in issues.diagnostics)


def test_comments_and_proprietary_type_alias():
    body = VALID.replace("(device, 1)", "(proprietary 700, 1)").replace(
        "object-type: device", "object-type: proprietary-object-type-700 -- -- retained"
    )
    issues = Issues(False)
    result = parse_database(body, 1, issues)
    assert len(result) == 1 and result[0].object_type == 700
    assert result[0].header_metadata["object-type"].comment == "retained"
