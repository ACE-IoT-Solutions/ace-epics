import pytest

from ace_epics.lexer import Lexer, tokenize
from ace_epics.lexer import TokenKind as K


@pytest.mark.parametrize(
    "text,value",
    [
        ('"it\'s"', "it's"),
        ("'say \"hi\"'", 'say "hi"'),
        ('`say "hi"\'', 'say "hi"'),
        ('"a -- b"', "a -- b"),
    ],
)
def test_strings(text, value):
    tokens, diagnostics = tokenize(text)
    assert tokens[0].kind == K.STRING
    assert tokens[0].value == value
    assert not diagnostics


def test_comments_whitespace_and_locations():
    tokens, _ = tokenize("a  \t b\r\n--\r\nx: 5 -- last\n")
    assert [(t.text, t.line, t.column) for t in tokens if t.kind == K.WORD] == [
        ("a", 1, 1),
        ("b", 1, 6),
        ("x", 3, 1),
        ("5", 3, 4),
    ]
    assert [t.value for t in tokens if t.kind == K.COMMENT] == ["", " last"]
    assert len([t for t in tokens if t.kind == K.NEWLINE]) == 3


def test_unterminated_string_and_single_quote_no_escape():
    tokens, diagnostics = tokenize('"missing\r\n')
    assert not tokens[0].terminated
    assert diagnostics[0].code == "L-UNTERMINATED-STRING"
    assert tokenize("'it's'")[0][1].text == "s'"


def test_punctuation_minus_and_raw_line():
    tokens, _ = tokenize("{}()[]<>,;:?* - -5 a-b X`0A`")
    assert K.MINUS in [t.kind for t in tokens]
    assert [t.text for t in tokens if t.kind == K.WORD] == ["-5", "a-b"]
    assert [t.value for t in tokens if t.kind == K.OCTETS] == ["0A"]
    lexer = Lexer('BACnet/IP -- supported\nname: "--"\n')
    assert lexer.line_mode() == "BACnet/IP"
    assert lexer.line_mode(2) == 'name: "--"'
    assert lexer.line_mode(999) == ""
