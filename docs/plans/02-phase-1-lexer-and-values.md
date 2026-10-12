# Phase 1: Encoding, Lexer, and Value Grammar (Clauses 4.1 to 4.4)

Goal: turn bytes into decoded text, text into tokens, and token runs into a syntactic
`ValueNode` tree, implementing every rule in `docs/spec/01-format-and-grammar.md` and
tolerating every notation inventoried in `docs/spec/04-annex-a-example-analysis.md` §d.
No BACnet knowledge is used here (decision D7). Can run in parallel with Phase 2.
Estimated effort: 6 to 8 days.

Modules: `encoding.py`, `lexer.py`, `values/nodes.py`, `values/parser.py`,
`values/restrictions.py`, `values/classify.py`, `values/render.py`.

## 1.1 Encoding detection and decoding (`encoding.py`, 4.1)

- `detect(data: bytes) -> Detected(charset_code, width, bom, python_codec)` using the exact
  octet patterns in `docs/spec/01` §1.3: 8-byte `PICS d\r\n`, 16-byte big-endian UCS-2
  pattern, 32-byte big-endian UCS-4 pattern. Also recognise little-endian and BOM-prefixed
  variants (D1) and report them as warnings in lenient mode, errors in strict mode.
- Codec map: 0 `utf-8`, 1 `mbcs` on Windows else `cp932` with a warning that DBCS code
  page is ambiguous, 2 `iso2022_jp`/`shift_jis` (document the choice), 3 `utf-32-be`,
  4 `utf-16-be`, 5 `latin-1`. Unknown digit: error, fall back to utf-8 so parsing can
  continue and report further problems.
- `decode(data) -> (text, Detected, list[Diagnostic])`; `encode(text, charset_code) -> bytes`
  for the writer. Line endings are not normalised here.

## 1.2 Lexer (`lexer.py`, 4.2, 4.3)

Token kinds: `WORD` (bare run of non-space, non-punctuation characters, may contain `-`,
`_`, `/`, `.`, `'` as in `'DIX'`, and digits), `STRING` (with quote style and
`terminated: bool`), `OCTETS` (`X'..'`), `LBRACE RBRACE LPAREN RPAREN LBRACK RBRACK LT GT
COMMA SEMI COLON QUESTION STAR MINUS`, `NEWLINE` (kept so the section parser can do
line-oriented work; the value parser skips it), `COMMENT` (text, kept for attachment to
property lines), `EOF`. Every token carries line and column (1-based) and the source
slice.

Rules to implement and test:
- `--` outside strings starts a comment to end of line; `--` inside strings does not.
  A bare `--` line is an empty comment.
- Strings per 4.3: `"` closes at `"`; `'` and `` ` `` close at `'`; end of line terminates
  with `terminated=False` (D12 warning).
- Whitespace runs collapse; CR, LF, tab, space are whitespace. The lexer still emits
  `NEWLINE` tokens because the section parsers and the "value starts on the next line"
  rule need them (Annex A d.19).
- A `MINUS` token is only emitted when `-` is not part of a WORD (needed for date ranges
  `(d1)-(d2)` and negative numbers are part of WORD).
- Lexer never fails; malformed input yields `WORD` tokens and diagnostics.

Lexer modes: `line_mode()` returns the raw text of the rest of the line with comments
stripped, for free-text sections (4.5.5 data link lines, 4.5.7 special functionality)
where tokenising would destroy the literal.

## 1.3 Value AST (`values/nodes.py`)

Pydantic models (frozen) with a `kind` discriminator so Phase 4 can serialise them:

| Node | Fields | Source |
|---|---|---|
| `NullValue` | | 4.4(b) |
| `BooleanValue` | `value: bool`, `short: bool` (T/F vs TRUE/FALSE) | 4.4(c) |
| `IntegerValue` | `value: int` | 4.4(d) |
| `RealValue` | `value: Decimal`, `text: str` (keeps `1.0` vs `1.00`, exponent form) | 4.4(e), Annex d.6 |
| `OctetStringValue` | `value: bytes`, `odd_length: bool` | 4.4(f), Annex d.15 |
| `CharacterStringValue` | `value: str`, `quote: Literal['"', "'", '`']` | 4.3, 4.4(g) |
| `EnumeratedValue` | `name: NamedToken`, `proprietary_number: int | None` | 4.4(i) |
| `DateValue` | `weekday, day, month, year: int | None | Wildcard`, `parenthesised: bool` | 4.4(j), Annex d.10 |
| `TimeValue` | `hour, minute, second, hundredth: int | None | Wildcard`, `precision` | 4.4(k), Annex d.11 |
| `DateRangeValue` | `start: DateValue, end: DateValue` | Annex d.10 |
| `ObjectIdentifierValue` | `object_type: NamedToken | int`, `instance: int | None` | 4.4(l) |
| `ContextTaggedValue` | `tag: int`, `value: ValueNode` | 4.4.1(b) |
| `GroupValue` | `delimiter: Literal["{", "("]`, `elements: list[ValueNode | EmptyElement]`, `trailing_comma: bool` | 4.4(h)(m), 4.4.1(c)(d), Annex d.12, d.13 |
| `EmptyElement` | | Annex d.13 (`{,x,,y}`) |
| `UnspecifiedValue` | | `?`, 4.5 intro |
| `WildcardValue` | | `*` standalone, defensive |

`GroupValue` is deliberately generic: bit strings, arrays, lists, constructed values,
named-bit lists, and date-time pairs are all groups at this layer. `classify.py` provides
pure functions that recognise shapes without BACnet knowledge:
`as_bitstring(group)` (all elements Boolean or `?`), `as_datetime(group)` (date then time),
`as_object_identifier(group)` (enumerated-or-`proprietary n`, then integer),
`as_date(group)`, `as_list_of(kind)`. The parser already applies `as_date` and
`as_object_identifier` eagerly when the shape is unambiguous (D7), so
`(analog-input, 56)` parses to `ObjectIdentifierValue` and `(1, 2, 3)` to a `GroupValue`.
`(Device, 1)` style capitalised types are normalised by `NamedToken`.

## 1.4 Value parser (`values/parser.py`, 4.4, 4.4.1)

`parse_value(tokens, *, strict) -> (ValueNode, diagnostics)`; recursive descent over the
token stream, stopping at depth 0 when it meets a `NEWLINE`, a marker word, `<`, or `}`.
Rules, with the Annex deviations that lenient mode must accept (each produces a WARNING
diagnostic with a dedicated code so users can see how non-standard a file is):

- Numbers: integer `-?\d+`; real `-?\d+\.\d+`; lenient also accepts `\d+(\.\d+)?[eE][+-]?\d+`
  (Annex c.7) and bare `.5`/`5.` with warning. Strict rejects all three.
- Booleans `T/TRUE/F/FALSE` case-insensitive. `NULL` is `NullValue`, never an enumeration.
- Octet strings `X'...'` and `` X`...` ``; odd digit count is a warning (Annex d.15).
- Enumerations: any WORD not matched above; `proprietary-...-<n>` and `proprietary <n>`
  (two tokens) set `proprietary_number`.
- Dates: `(` [weekday `,`] day `-` month `-` year `)`; lenient accepts no parentheses in
  restriction context (Annex c.7) and `(*-*-*)`. Month and weekday names are matched
  case-insensitively by full English name; three-letter abbreviations are a lenient warning.
- Times: `h:mm:ss.xx` canonical; lenient accepts `h:mm`, `h:mm:ss`, `h:mm:ss.x`
  (Annex d.11) and records `precision`. `*` in any field.
- Date range: `date MINUS date`, inside or outside braces (Annex d.10).
- Context tag: `[` integer `]` value.
- Groups: `{`/`(` elements separated by `,`; an element may be empty (Annex d.13); trailing
  comma sets `trailing_comma` (warning); a missing comma between two complete values at the
  same depth is repaired with a warning in lenient mode, error in strict (Annex d.12, d.8
  `{TRUE FALSE, ...}`).
- Mismatched or stray closers: strict error; lenient repairs to the innermost open group,
  emits error-level diagnostic but keeps parsing (Annex e.20).
- `?` anywhere a value is expected (D9); `*` standalone yields `WildcardValue`.

## 1.5 Restrictions (`values/restrictions.py`, 4.4.2, 4.5.8)

`parse_restrictions(tokens) -> (RestrictionSet, diagnostics)`: `<` statement (`;` statement)* `>`;
statement = name (`:`)? value-list. Names are the closed set of seven (D14) matched with
spaces collapsed; the colon is required in strict mode and optional in lenient (Annex c.7);
`maximum length array10` (no space before the number) is accepted leniently by splitting a
trailing integer off the name. Values are `ValueNode`s (`allowed values` yields a list of
enumerated or object-type names, accepting space-separated type names per 4.4.2 example).

## 1.6 Renderer (`values/render.py`)

`render(node, style=Canonical) -> str`, the inverse of the parser, used by the Phase 3
writer. Canonical style: `TRUE/FALSE`, lowercase-hyphen enumerations, `(analog-input, 56)`,
`(Monday, 24-January-1998)`, `hh:mm:ss.xx` zero-padded, groups with `, ` separators and
the original delimiter, no trailing commas, `X'..'` uppercase hex. A `Preserving` style
reproduces `RealValue.text`, quote styles, and `short` booleans for diff-friendly rewrites.
Property: `parse_value(render(n)) == n` for all nodes generated by the Hypothesis
strategies (modulo `text`/`short` cosmetic fields under Canonical style).

## 1.7 Tests (`tests/unit/encoding`, `tests/unit/lexer`, `tests/unit/values`)

- Encoding: the 8 seeds in `docs/spec/01` §9 (1 to 8) plus little-endian and BOM cases;
  round trip `decode(encode(text))` for all six codes.
- Lexer: seeds 9 to 20; comment inside multi-line group (Annex d.8); `--` inside string;
  bare `--` line; unterminated string diagnostics; column accuracy on tabs.
- Values: seeds 21 to 48 as a parametrised table `(input, expected_node, expected_codes)`;
  one test per Annex §d notation (d.5 to d.16, every example quoted there, rewritten with
  synthetic values); strict-vs-lenient matrix for every deviation in Annex §e that is
  value-level (e.4, e.9 to e.20).
- Restrictions: seeds 49 to 56; both colon forms; `allowed values` with spaces.
- Hypothesis: `tests/strategies.py` generates random `ValueNode` trees; property tests for
  render/parse round trip and for "parser never raises" on random token soup.

## 1.8 Documentation deliverables

- `docs/site/format-guide/values.md`: one subsection per node type with the canonical
  syntax, accepted lenient variants, and the diagnostic codes they raise.
- `docs/site/format-guide/encodings.md`.
- `docs/site/reference/diagnostics.md`: table of all codes introduced in this phase
  (generated from a registry in `diagnostics.py`, not hand-written).

## Acceptance criteria

- All seeds from `docs/spec/01` §9 pass; every Annex §d notation has a passing test.
- Round-trip property test runs 2000 examples clean on CI.
- Lexer and value parser never raise on arbitrary input (fuzz test with 10k random inputs).
- Diagnostic code registry documented; coverage of `values/` and `lexer.py` at 95 percent.
