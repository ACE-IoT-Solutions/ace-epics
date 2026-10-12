"""Closed restriction grammar and models (135.1 Clauses 4.4.2 and 4.5.8)."""

from __future__ import annotations

import re
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from ace_epics.diagnostics import Diagnostic, Severity
from ace_epics.lexer import Token, tokenize
from ace_epics.lexer import TokenKind as K
from ace_epics.model.names import NamedToken
from ace_epics.values.nodes import EnumeratedValue, IntegerValue, ValueNode
from ace_epics.values.parser import ValueParser, parse_value
from ace_epics.values.render import render


class RestrictionSet(BaseModel):
    """The seven closed restriction forms with typed bounds and lengths (135.1 Clause 4.4.2)."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    minimum: ValueNode | None = None
    maximum: ValueNode | None = None
    resolution: ValueNode | None = None
    maximum_length_string: int | None = Field(default=None, ge=0)
    maximum_length_list: int | None = Field(default=None, ge=0)
    maximum_length_array: int | None = Field(default=None, ge=0)
    allowed_values: list[ValueNode] | None = None

    def merged_over(self, defaults: RestrictionSet | None) -> RestrictionSet:
        """Overlay explicit property restrictions on datatype defaults. (135.1 Clause 4.4.2)."""
        values = defaults.model_dump() if defaults else {}
        values.update({k: v for k, v in self.model_dump().items() if v is not None})
        return RestrictionSet.model_validate(values)


_NAMES = {name.replace("_", " "): name for name in RestrictionSet.model_fields}


def parse_restrictions(
    tokens: str | Iterable[Token], *, strict=False
) -> tuple[RestrictionSet, list[Diagnostic]]:
    """Parse semicolon-separated bounds, preserving typed values and error evidence. (135.1
    Clause 4.4.2).
    """
    diagnostics = []
    if isinstance(tokens, str):
        tokens, diagnostics = tokenize(tokens, strict=strict)
    tokens = [t for t in tokens if t.kind not in (K.NEWLINE, K.COMMENT, K.EOF)]
    data: dict[str, object] = {}

    def issue(code, message, token=None, error=False):
        diagnostics.append(
            Diagnostic(
                code=code,
                message=message,
                clause="4.4.2",
                severity=Severity.ERROR if error or strict else Severity.WARNING,
                line=token.line if token else None,
                column=token.column if token else None,
            )
        )

    if not tokens or tokens[0].kind != K.LT:
        issue("R-BRACKETS", "Restrictions require angle brackets.", error=True)
        return RestrictionSet(), diagnostics
    if tokens[-1].kind != K.GT:
        issue(
            "R-BRACKETS",
            "Restrictions are missing their closing angle bracket.",
            tokens[-1],
            error=True,
        )
        body = tokens[1:]
    else:
        body = tokens[1:-1]
    statements = []
    start = 0
    for i, t in enumerate(body):
        if t.kind == K.SEMI:
            statements.append(body[start:i])
            start = i + 1
    statements.append(body[start:])
    for stmt in statements:
        if not stmt:
            continue
        colon = next((i for i, t in enumerate(stmt) if t.kind == K.COLON), None)
        name = None
        values = []
        if colon is not None:
            candidate = (
                " ".join(t.text for t in stmt[:colon]).lower().replace("_", " ").replace("-", " ")
            )
            name = _NAMES.get(candidate)
            values = stmt[colon + 1 :]
        else:
            issue("R-COLON", "Restriction name and value require a colon.", stmt[0])
            raw = " ".join(t.text for t in stmt)
            for candidate, field in sorted(
                _NAMES.items(), key=lambda pair: len(pair[0]), reverse=True
            ):
                m = re.match(re.escape(candidate) + r"\s*(.*)$", raw, re.I)
                if m and m[1]:
                    name = field
                    values, _ = tokenize(m[1])
                    values = values[:-1]
                    break
        if name is None:
            issue("R-NAME", "Unknown restriction name.", stmt[0], error=True)
            continue
        if name in data:
            issue("R-DUPLICATE", "Restriction is specified more than once.", stmt[0], error=True)
        if not values:
            issue("R-VALUE", "Restriction requires a value.", stmt[0], error=True)
            continue
        if name == "allowed_values":
            chunks = []
            start = 0
            for i, t in enumerate(values):
                if t.kind == K.COMMA:
                    chunks.append(values[start:i])
                    start = i + 1
            chunks.append(values[start:])
            allowed: list[ValueNode] = []
            for chunk in chunks:
                if chunk and all(t.kind == K.WORD and not t.text.isdigit() for t in chunk):
                    allowed.append(
                        EnumeratedValue(name=NamedToken(canonical=" ".join(t.text for t in chunk)))
                    )
                else:
                    value, findings = parse_value(chunk, strict=strict)
                    diagnostics.extend(findings)
                    allowed.append(value)
            data[name] = allowed
        else:
            parser = ValueParser(values, strict=strict)
            value = parser.parse()
            diagnostics.extend(parser.diagnostics)
            if parser.current.kind != K.EOF:
                issue(
                    "R-SEPARATOR",
                    "Restriction statements must be separated by semicolons.",
                    parser.current,
                    error=True,
                )
            if value.kind == "date" and not value.parenthesised:
                issue("R-BARE-DATE", "Restriction date requires parentheses.", stmt[0])
            if name.startswith("maximum_length"):
                if not isinstance(value, IntegerValue) or value.value < 0:
                    issue(
                        "R-LENGTH",
                        "Length restrictions require a non-negative integer.",
                        stmt[0],
                        error=True,
                    )
                    continue
                data[name] = value.value
            else:
                data[name] = value
    return RestrictionSet.model_validate(data), diagnostics


def render_restrictions(restrictions: RestrictionSet) -> str:
    """Render the seven restriction forms in their standard order (135.1 Clause 4.4.2)."""
    statements = []
    for field in RestrictionSet.model_fields:
        value = getattr(restrictions, field)
        if value is None:
            continue
        text = (
            ", ".join(render(n) for n in value)
            if isinstance(value, list)
            else str(value)
            if isinstance(value, int)
            else render(value)
        )
        statements.append(field.replace("_", " ") + ": " + text)
    return "<" + "; ".join(statements) + ">"
