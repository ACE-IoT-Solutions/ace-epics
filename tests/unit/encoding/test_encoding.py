import codecs

import pytest

from ace_epics.diagnostics import Severity
from ace_epics.encoding import decode, detect, encode


@pytest.mark.parametrize("code,width", [(0, 1), (1, 1), (2, 1), (3, 4), (4, 2), (5, 1)])
def test_standard_headers_roundtrip(code, width):
    text = f"PICS {code}\r\nBACnet Protocol Implementation Conformance Statement\r\n"
    raw = encode(text, code)
    decoded, found, diagnostics = decode(raw)
    assert decoded == text
    assert found.charset_code == code
    assert found.width == width
    assert not found.bom
    assert not [d for d in diagnostics if d.severity == Severity.ERROR]


@pytest.mark.parametrize(
    "raw,code",
    [
        (b"PICS 9\r\n", "E-CHARSET"),
        (b"PICS\r\n", "E-HEADER"),
        (b"PICS x\r\n", "E-HEADER"),
        (b"PICS 0\n", "E-LINE-ENDINGS"),
    ],
)
def test_header_seeds(raw, code):
    assert code in {d.code for d in decode(raw, strict=True)[2]}


@pytest.mark.parametrize(
    "codec,code,bom",
    [
        ("utf-8", 0, codecs.BOM_UTF8),
        ("utf-16-be", 4, codecs.BOM_UTF16_BE),
        ("utf-16-le", 4, codecs.BOM_UTF16_LE),
        ("utf-32-be", 3, codecs.BOM_UTF32_BE),
        ("utf-32-le", 3, codecs.BOM_UTF32_LE),
    ],
)
def test_bom_variants(codec, code, bom):
    text = f"PICS {code}\r\n"
    raw = bom + text.encode(codec)
    assert decode(raw)[0] == text
    assert detect(raw).bom == bom
    assert all(d.severity == Severity.WARNING for d in decode(raw)[2])
    assert all(d.severity == Severity.ERROR for d in decode(raw, strict=True)[2])


@pytest.mark.parametrize("codec,code", [("utf-16-le", 4), ("utf-32-le", 3)])
def test_little_endian_without_bom(codec, code):
    decoded, _, diagnostics = decode(f"PICS {code}\r\n".encode(codec))
    assert decoded == f"PICS {code}\r\n"
    assert [d.code for d in diagnostics] == ["E-ENDIAN"]


def test_invalid_encoding_and_conflicting_width():
    assert decode(b"PICS 0\r\n\xff")[2][0].code == "E-DECODE"
    assert "E-WIDTH" in {d.code for d in decode("PICS 0\r\n".encode("utf-16-be"))[2]}
    with pytest.raises(ValueError):
        encode("", 9)
    assert decode(b"")[2][0].code == "E-HEADER"


@pytest.mark.parametrize(
    "code,content", [(0, "é漢字"), (1, "漢字"), (2, "漢字"), (3, "é漢字"), (4, "é漢字"), (5, "é")]
)
def test_non_ascii_codec_choices(code, content):
    text = f"PICS {code}\r\n{content}\r\n"
    assert decode(encode(text, code))[0] == text


def test_header_case_spacing_policy():
    text, _, diagnostics = decode(b"pics 0 -- note\r\n")
    assert text == "pics 0 -- note\r\n"
    assert [d.code for d in diagnostics] == ["E-HEADER-FORM"]
    assert decode(b"pics 0 -- note\r\n", strict=True)[2][0].severity == Severity.ERROR


def test_structurally_empty_epics_seed():
    from ace_epics.codecs.epics import parse

    result = parse(
        "PICS 0\r\n"
        "BACnet Protocol Implementation Conformance Statement\r\n"
        "End of BACnet Protocol Implementation Conformance Statement\r\n",
        strict=True,
    )
    assert result.document is not None
    assert {d.code for d in result.diagnostics} == {"P-SECTIONS-INCOMPLETE", "M-DEVICE-COUNT"}
    assert result.document.objects == []
