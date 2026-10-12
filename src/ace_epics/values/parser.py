"""Recoverable recursive-descent syntactic value parser (135.1 Clause 4.4)."""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.lexer import Token, tokenize
from ace_epics.lexer import TokenKind as K
from ace_epics.model.names import NamedToken
from ace_epics.values.classify import as_object_identifier
from ace_epics.values.nodes import (
    BooleanValue,
    CharacterStringValue,
    ContextTaggedValue,
    DateRangeValue,
    DateValue,
    EmptyElement,
    EnumeratedValue,
    GroupValue,
    IntegerValue,
    NullValue,
    OctetStringValue,
    RealValue,
    TimeValue,
    UnspecifiedValue,
    ValueNode,
    WildcardValue,
)

_MONTHS = list(calendar.month_name)[1:]
_DAYS = list(calendar.day_name)
_DATE = re.compile(r"(?:(\*|[A-Za-z]+),)?(\*|\d+)-(\*|[A-Za-z]+|\d+)-(\*|\d+)$")
_TIME = re.compile(r"(\*|\d+):(\*|\d+)(?::(\*|\d+)(?:\.(\*|\d+))?)?$")


class ValueParser:
    """A cursor parser; position reports where a property marker/restriction starts. (135.1
    Clause 4.4 and 4.4.1).
    """

    def __init__(self, tokens: Iterable[Token], *, strict: bool = False):
        self.tokens = list(tokens)
        if not self.tokens or self.tokens[-1].kind != K.EOF:
            self.tokens.append(Token(K.EOF, ""))
        self.position = 0
        self.strict = strict
        self.diagnostics: list[Diagnostic] = []

    @property
    def current(self):
        """Return the token at the current property-value cursor (135.1 Clause 4.4 and 4.4.1)."""
        return self.tokens[min(self.position, len(self.tokens) - 1)]

    def issue(self, code: str, message: str, token: Token | None = None, *, error=False):
        """Record a located finding with strict-mode severity promotion (135.1 Clause 4.4 and
        4.4.1).
        """
        token = token or self.current
        self.diagnostics.append(
            Diagnostic(
                code=code,
                message=message,
                severity=Severity.ERROR if error or self.strict else Severity.WARNING,
                clause="4.4",
                line=token.line,
                column=token.column,
            )
        )

    def skip(self):
        """Consume comments and newlines as value-level whitespace (135.1 Clause 4.4 and 4.4.1)."""
        while self.current.kind in (K.NEWLINE, K.COMMENT):
            self.position += 1

    def date(self, raw: str, token: Token, *, parenthesised=True):
        """Recognize English date fields and preserve wildcard positions (135.1 Clause 4.4 and
        4.4.1).
        """
        m = _DATE.fullmatch(raw.replace(" ", ""))
        if not m:
            return None

        def name_field(text, names):
            if text is None:
                return None
            if text == "*":
                return WildcardValue()
            if text.isdigit():
                self.issue("V-DATE-NAME", "Date month must use its English name.", token)
                return int(text)
            matches = [i + 1 for i, name in enumerate(names) if name.lower() == text.lower()]
            if matches:
                return matches[0]
            matches = [i + 1 for i, name in enumerate(names) if name[:3].lower() == text.lower()]
            if matches:
                self.issue("V-DATE-ABBREVIATION", "Abbreviated English date name accepted.", token)
                return matches[0]
            return None

        weekday = name_field(m[1], _DAYS)
        month = name_field(m[3], _MONTHS)
        if month is None or (m[1] is not None and weekday is None):
            self.issue("V-DATE", "Unknown date month or weekday.", token, error=True)
            return None

        def number(text):
            return WildcardValue() if text == "*" else int(text)

        day, year = number(m[2]), number(m[4])
        if isinstance(day, int) and not 1 <= day <= 32:
            self.issue("V-DATE-RANGE", "Date day is out of range.", token, error=True)
        return DateValue(
            weekday=weekday, day=day, month=month, year=year, parenthesised=parenthesised
        )

    def parse(self, depth=0) -> ValueNode:
        """Parse one recoverable value while retaining the suffix cursor (135.1 Clause 4.4 and
        4.4.1).
        """
        self.skip()
        token = self.current
        if depth > 100:
            self.issue("V-DEPTH", "Value nesting exceeds supported depth.", token, error=True)
            self.position += int(token.kind != K.EOF)
            return UnspecifiedValue()
        kind = token.kind
        if kind in (K.EOF, K.LT, K.RBRACE, K.RPAREN, K.GT, K.SEMI, K.COMMA):
            self.issue("V-MISSING", "Expected a value.", token, error=True)
            return UnspecifiedValue()
        if kind in (K.LBRACE, K.LPAREN):
            if kind == K.LPAREN:
                j = self.position + 1
                while j < len(self.tokens) and self.tokens[j].kind not in (
                    K.RPAREN,
                    K.LPAREN,
                    K.LBRACE,
                    K.EOF,
                ):
                    j += 1
                raw = "".join(
                    t.text
                    for t in self.tokens[self.position + 1 : j]
                    if t.kind not in (K.COMMENT, K.NEWLINE)
                )
                date = self.date(raw, token)
                if date is not None:
                    self.position = j
                    if self.current.kind == K.RPAREN:
                        self.position += 1
                    else:
                        self.issue(
                            "V-UNBALANCED", "Date is missing a closing parenthesis.", error=True
                        )
                    return self.range(date, depth)
            node = self.group(depth)
            return node
        if kind == K.LBRACK:
            self.position += 1
            self.skip()
            tag = self.current
            valid = tag.kind == K.WORD and tag.text.isdigit()
            if valid:
                self.position += 1
            else:
                self.issue("V-TAG", "Context tag must be a non-negative integer.", error=True)
            if self.current.kind == K.RBRACK:
                self.position += 1
            else:
                self.issue("V-TAG", "Context tag is missing its closing bracket.", error=True)
            return ContextTaggedValue(
                tag=int(tag.text) if valid else 0, value=self.parse(depth + 1)
            )
        if kind == K.STRING:
            self.position += 1
            return CharacterStringValue(value=token.value or "", quote=token.quote or '"')
        if kind == K.OCTETS:
            self.position += 1
            digits = token.value or ""
            if not re.fullmatch(r"[0-9a-fA-F]*", digits):
                self.issue(
                    "V-OCTETS", "Octet strings require hexadecimal digits.", token, error=True
                )
                digits = "".join(c for c in digits if c in "0123456789abcdefABCDEF")
            odd = len(digits) % 2 == 1
            if odd:
                self.issue("V-ODD-OCTETS", "Odd hex digit count padded with a leading zero.", token)
                digits = "0" + digits
            return OctetStringValue(value=bytes.fromhex(digits), odd_length=odd)
        # Date/time lexical punctuation can span multiple tokens, including '*'.
        j = self.position
        while j < len(self.tokens) and self.tokens[j].kind in (K.WORD, K.STAR, K.MINUS, K.COLON):
            j += 1
        for end in range(j, self.position, -1):
            raw = "".join(t.text for t in self.tokens[self.position : end])
            match = _TIME.fullmatch(raw)
            if match:
                self.position = end
                fields = match.groups()
                precision = (
                    -1
                    if fields[2] is None
                    else 0
                    if fields[3] is None
                    else 2
                    if fields[3] == "*"
                    else len(fields[3])
                )
                if precision != 2:
                    self.issue(
                        "V-TIME-PRECISION", "Time requires seconds and two hundredth digits.", token
                    )

                def part(field, fraction=False):
                    if field == "*":
                        return WildcardValue()
                    if field is None:
                        return 0
                    return int(field) * 10 if fraction and len(field) == 1 else int(field)

                vals = [part(fields[i], i == 3) for i in range(4)]
                for value, limit in zip(vals, (24, 59, 59, 99), strict=True):
                    if isinstance(value, int) and value > limit:
                        self.issue("V-TIME-RANGE", "Time field is out of range.", token, error=True)
                return TimeValue(
                    hour=vals[0],
                    minute=vals[1],
                    second=vals[2],
                    hundredth=vals[3],
                    precision=precision,
                )
            date = self.date(raw, token, parenthesised=False) if "-" in raw else None
            if date is not None:
                if depth == 0:
                    self.issue("V-BARE-DATE", "Date values require parentheses.", token)
                self.position = end
                return self.range(date, depth)
        self.position += 1
        if kind == K.QUESTION:
            return UnspecifiedValue()
        if kind == K.STAR:
            return WildcardValue()
        if kind != K.WORD:
            self.issue("V-TOKEN", "Unexpected punctuation in value.", token, error=True)
            return UnspecifiedValue()
        word = token.text
        lower = word.lower()
        if lower == "null":
            return NullValue()
        if lower in ("t", "true", "f", "false"):
            return BooleanValue(value=lower in ("t", "true"), short=len(word) == 1)
        if re.fullmatch(r"-?\d+", word):
            try:
                return IntegerValue(value=int(word))
            except ValueError:
                self.issue("V-NUMBER", "Integer exceeds supported text length.", token, error=True)
                return UnspecifiedValue()
        if re.fullmatch(r"-?(?:\d+\.\d+|\d*\.\d+|\d+\.)(?:[eE][+-]?\d+)?|-?\d+[eE][+-]?\d+", word):
            if not re.fullmatch(r"-?\d+\.\d+", word):
                self.issue("V-REAL-NOTATION", "Noncanonical real notation accepted.", token)
            try:
                return RealValue(value=Decimal(word), text=word)
            except InvalidOperation:
                self.issue("V-NUMBER", "Invalid real number.", token, error=True)
                return UnspecifiedValue()
        if lower in ("nan", "inf", "infinity") or word.startswith("+"):
            self.issue("V-NUMBER", "Unsupported numeric notation.", token, error=True)
        proprietary = None
        if lower == "proprietary" and self.current.kind == K.WORD and self.current.text.isdigit():
            proprietary = int(self.current.text)
            self.position += 1
            word = f"proprietary-{proprietary}"
        elif lower.startswith("proprietary"):
            m = re.search(r"(?:-|_)(\d+)$", lower)
            if m:
                proprietary = int(m[1])
            else:
                self.issue(
                    "V-PROPRIETARY",
                    "Proprietary enumeration needs a numeric suffix.",
                    token,
                    error=True,
                )
        return EnumeratedValue(name=NamedToken(canonical=word), proprietary_number=proprietary)

    def range(self, date, depth):
        """Recognize a following date endpoint joined by a minus token (135.1 Clause 4.4 and
        4.4.1).
        """
        if self.current.kind == K.MINUS:
            self.position += 1
            other = self.parse(depth + 1)
            if isinstance(other, DateValue):
                return DateRangeValue(start=date, end=other)
            self.issue("V-DATE-RANGE", "Date range requires two dates.", error=True)
        return date

    def group(self, depth):
        """Parse nested positional groups and repair malformed delimiters (135.1 Clause 4.4 and
        4.4.1).
        """
        opener = self.current
        self.position += 1
        closer = K.RBRACE if opener.kind == K.LBRACE else K.RPAREN
        elements: list[ValueNode] = []
        trailing = False
        expecting = True
        while True:
            self.skip()
            token = self.current
            if token.kind == closer:
                self.position += 1
                break
            if token.kind in (K.EOF, K.LT):
                self.issue("V-UNBALANCED", "Group is missing a closing delimiter.", error=True)
                break
            if token.kind in (K.RBRACE, K.RPAREN, K.RBRACK):
                self.issue("V-CLOSER", "Mismatched closing delimiter repaired.", error=True)
                self.position += 1
                break
            if token.kind == K.COMMA:
                if expecting:
                    elements.append(EmptyElement())
                self.position += 1
                self.skip()
                trailing = self.current.kind == closer
                if trailing:
                    self.issue(
                        "V-TRAILING-COMMA",
                        "Trailing group comma omitted by canonical writing.",
                        token,
                    )
                expecting = True
                continue
            if not expecting:
                self.issue("V-MISSING-COMMA", "Missing group comma repaired.", token)
            # Space-separated object names are one enumeration before their comma.
            if opener.kind == K.LPAREN and not elements and token.kind == K.WORD:
                j = self.position
                while self.tokens[j].kind == K.WORD:
                    j += 1
                words = self.tokens[self.position : j]
                if (
                    len(words) > 1
                    and self.tokens[j].kind == K.COMMA
                    and all(not w.text.isdigit() for w in words)
                ):
                    self.position = j
                    elements.append(
                        EnumeratedValue(name=NamedToken(canonical=" ".join(t.text for t in words)))
                    )
                    expecting = False
                    continue
            before = self.position
            elements.append(self.parse(depth + 1))
            if self.position == before:
                self.position += 1
            expecting = False
            trailing = False
        if any(isinstance(n, UnspecifiedValue) for n in elements) and not all(
            isinstance(n, (BooleanValue, UnspecifiedValue)) for n in elements
        ):
            self.issue(
                "V-NESTED-UNSPECIFIED", "Unspecified element accepted outside a bit string.", opener
            )
        group = GroupValue(
            delimiter="{" if opener.kind == K.LBRACE else "(",
            elements=elements,
            trailing_comma=trailing,
        )
        return as_object_identifier(group) or group


def parse_value(
    tokens: str | Iterable[Token], *, strict: bool = False
) -> tuple[ValueNode, list[Diagnostic]]:
    """Parse one value and collect recovery diagnostics; property suffixes are left alone.
    (135.1 Clause 4.4 and 4.4.1).
    """
    lexical = []
    if isinstance(tokens, str):
        tokens, lexical = tokenize(tokens, strict=strict)
    parser = ValueParser(tokens, strict=strict)
    try:
        node = parser.parse()
    except (ValueError, RecursionError, ValidationError, OverflowError):
        parser.issue(
            "V-INVALID", "Invalid or excessively large value recovered as unspecified.", error=True
        )
        node = UnspecifiedValue()
    if parser.current.kind in (K.RBRACK, K.RPAREN, K.RBRACE):
        parser.issue("V-CLOSER", "Stray closing delimiter after value.", error=True)
    if parser.current.kind not in (
        K.EOF,
        K.NEWLINE,
        K.COMMENT,
        K.LT,
        K.RBRACE,
        K.RPAREN,
        K.GT,
        K.SEMI,
        K.COMMA,
    ) and not (parser.current.kind == K.WORD and parser.current.text.upper() in {"W", "C", "R"}):
        parser.issue("V-TRAILING", "Unexpected tokens after a complete value.", error=True)
    return node, lexical + parser.diagnostics
