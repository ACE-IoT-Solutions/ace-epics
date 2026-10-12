import pytest
from pydantic import ValidationError

from ace_epics.model.enums import CHARACTER_SET_ALIASES, CharacterSet, CharacterSetCode
from ace_epics.model.general import GeneralInformation, PicsHeader


@pytest.mark.parametrize("code,width", [(0, 1), (1, 1), (2, 1), (3, 4), (4, 2), (5, 1)])
def test_header(code, width):
    header = PicsHeader(charset_code=code)
    assert header.charset == CharacterSetCode(code)
    assert header.charset.octet_width == width


def test_header_rejects_unknown_code():
    with pytest.raises(ValidationError):
        PicsHeader.model_validate({"charset_code": 6})


@pytest.mark.parametrize("literal", list(CHARACTER_SET_ALIASES))
def test_character_set_alias(literal):
    assert CharacterSet(literal) == CHARACTER_SET_ALIASES[literal]
    assert CharacterSet("  " + literal.lower() + "  ") == CHARACTER_SET_ALIASES[literal]


def test_unsupported_character_set():
    with pytest.raises(ValueError):
        CharacterSet("ISO 10646 (UTF-16)")
    with pytest.raises(ValueError):
        CharacterSet(42)


def test_general_keeps_content_and_aliases():
    general = GeneralInformation(
        **{
            "Vendor Name": " Ace ",
            "Product Name": 'say "x"',
            "Product Model Number": "",
            "Product Description": "He said 'hi'",
        }
    )
    assert general.vendor_name == " Ace "
    assert general.model_dump(by_alias=True)["Product Name"] == 'say "x"'
    with pytest.raises(ValidationError):
        GeneralInformation.model_validate(general.model_dump() | {"typo": True})
