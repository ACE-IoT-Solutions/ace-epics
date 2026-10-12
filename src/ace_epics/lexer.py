"""Lossless located lexical tokens for 135.1 Clauses 4.2 and 4.3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, cast

from ace_epics.diagnostics import Diagnostic, Severity


class TokenKind(StrEnum):
    """The lexical alphabet for names, quoted values and delimiters (135.1 Clause 4.2 and 4.3)."""

    WORD = "WORD"
    STRING = "STRING"
    OCTETS = "OCTETS"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACK = "LBRACK"
    RBRACK = "RBRACK"
    LT = "LT"
    GT = "GT"
    COMMA = "COMMA"
    SEMI = "SEMI"
    COLON = "COLON"
    QUESTION = "QUESTION"
    STAR = "STAR"
    MINUS = "MINUS"
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    """A source token retaining its spelling and one-based location (135.1 Clause 4.2 and 4.3)."""

    kind: TokenKind
    text: str
    line: int = 1
    column: int = 1
    value: str | None = None
    terminated: bool = True
    quote: Literal['"', "'", "`"] | None = None
    offset: int = 0


_PUNCT = dict(
    zip(
        "{}()[]<>,;:?*",
        [
            TokenKind.LBRACE,
            TokenKind.RBRACE,
            TokenKind.LPAREN,
            TokenKind.RPAREN,
            TokenKind.LBRACK,
            TokenKind.RBRACK,
            TokenKind.LT,
            TokenKind.GT,
            TokenKind.COMMA,
            TokenKind.SEMI,
            TokenKind.COLON,
            TokenKind.QUESTION,
            TokenKind.STAR,
        ],
        strict=True,
    )
)


class Lexer:
    """Tokenize recoverably, retaining comments and physical line boundaries. (135.1 Clause 4.2
    and 4.3).
    """

    def __init__(self, text: str, *, strict: bool = False):
        self.text = text
        self.strict = strict
        self.diagnostics: list[Diagnostic] = []

    def tokens(self) -> list[Token]:
        """Scan tokens without losing line boundaries or comments (135.1 Clause 4.2 and 4.3)."""
        self.diagnostics = []
        result = []
        s = self.text
        i, line, column = 0, 1, 1
        while i < len(s):
            start, ln, col = i, line, column
            ch = s[i]
            if ch in " \t":
                i += 1
                column += 1
                continue
            kind, value, quote, terminated = TokenKind.WORD, None, None, True
            if ch in "\r\n":
                i += 2 if s.startswith("\r\n", i) else 1
                kind = TokenKind.NEWLINE
                line += 1
                column = 1
            elif s.startswith("--", i):
                i += 2
                while i < len(s) and s[i] not in "\r\n":
                    i += 1
                kind, value = TokenKind.COMMENT, s[start + 2 : i]
                column += i - start
            elif ch in "\"'`" or (ch.lower() == "x" and i + 1 < len(s) and s[i + 1] in "'`"):
                octets = ch.lower() == "x"
                if octets:
                    i += 1
                quote = cast(Literal['"', "'", "`"], s[i])
                i += 1
                content_start = i
                closer = quote if octets else ('"' if quote == '"' else "'")
                while i < len(s) and s[i] not in "\r\n" and s[i] != closer:
                    i += 1
                value = s[content_start:i]
                terminated = i < len(s) and s[i] == closer
                if terminated:
                    i += 1
                else:
                    self.diagnostics.append(
                        Diagnostic(
                            code="L-UNTERMINATED-STRING",
                            severity=Severity.WARNING,
                            message="String terminates at the line boundary.",
                            clause="4.3",
                            line=ln,
                            column=col,
                        )
                    )
                kind = TokenKind.OCTETS if octets else TokenKind.STRING
                column += i - start
            elif ch in _PUNCT:
                kind = _PUNCT[ch]
                i += 1
                column += 1
            elif ch == "-" and (
                i + 1 == len(s)
                or not (
                    s[i + 1].isdigit()
                    or s[i + 1].isalpha()
                    or (s[i + 1] == "." and i + 2 < len(s) and s[i + 2].isdigit())
                )
            ):
                kind = TokenKind.MINUS
                i += 1
                column += 1
            else:
                i += 1
                while (
                    i < len(s)
                    and s[i] not in ' \t\r\n{}()[]<>,;:?*"`'
                    and not s.startswith("--", i)
                ):
                    i += 1
                column += i - start
            result.append(Token(kind, s[start:i], ln, col, value, terminated, quote, start))
        result.append(Token(TokenKind.EOF, "", line, column, offset=len(s)))
        return result

    def line_mode(self, line: int = 1) -> str:
        """Return the requested physical line's literal text, removing its comment. (135.1
        Clause 4.2 and 4.3).
        """
        lines = self.text.splitlines()
        if line < 1 or line > len(lines):
            return ""
        raw = lines[line - 1]
        tokens, _ = tokenize(raw)
        comment = next((t for t in tokens if t.kind == TokenKind.COMMENT), None)
        return raw[: comment.offset if comment else len(raw)].rstrip()


def tokenize(text: str, *, strict: bool = False) -> tuple[list[Token], list[Diagnostic]]:
    """Tokenize decoded EPICS text and collect recoverable lexical diagnostics (135.1 Clause
    4.2 and 4.3).
    """
    lexer = Lexer(text, strict=strict)
    return lexer.tokens(), lexer.diagnostics
