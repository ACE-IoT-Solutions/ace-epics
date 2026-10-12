# Phase 3: Native EPICS Reader and Writer (Clause 4, whole file)

Goal: `ace_epics.codecs.epics.loads/load/dumps/dump` turning a `.tpi` file into
`EpicsDocument` and back, with complete diagnostics, strict and lenient modes, and the
round-trip guarantee from decision 2. Depends on Phases 1 and 2. Estimated effort: 6 to 9
days.

Modules: `codecs/epics/reader.py`, `codecs/epics/sections.py`, `codecs/epics/database.py`,
`codecs/epics/writer.py`, `codecs/epics/__init__.py`.

## 3.1 Reader pipeline (`reader.py`)

1. `decode` (Phase 1) to text plus encoding diagnostics.
2. Line-ending audit: count CRLF vs bare LF/CR (D2).
3. Header line `PICS n`, signature line, end line (D3): case-insensitive, trailing comment
   and whitespace allowed, blank and comment lines allowed between header and signature in
   lenient mode (strict: error, 4.2 says "first line following the header").
4. Section splitter: scan lines at brace depth 0 for `<heading>:` where heading matches a
   known 4.5 section name (case-insensitive, whitespace-collapsed; aliases: `List of
   Objects in test device`, `BIBBS Supported`). Unknown headings at depth 0 become
   `UnknownSection` diagnostics (warning in lenient, error in strict) and are skipped to
   the matching `}`. The section body is either the rest of the line (4.5.1 general
   information) or the balanced `{ ... }` block that follows (brace may be on the same
   line or the next, Annex §a).
5. Per-section parsers (`sections.py`), each `(body_lines, sink) -> model`:
   - General information: string value; missing quotes is a lenient warning (value taken to end of line).
   - BIBBs: one WORD per line; several per line accepted with a warning.
   - Services: `name` then flag words in any order; missing flags is an error (4.5.3);
     unknown words after the name are errors.
   - Object types: name words up to the first `Createable|Creatable|Deleteable` word (D18),
     flags in any order.
   - Data link: `line_mode()` text matched against the `DataLinkOption` class regexes
     (Phase 2); unmatched lines produce `Other(text=...)` with a warning. Baud suffixes
     `14.4k`/`28.8k` are normalised to integers with a warning (D19). Missing baud list
     where required: error in strict, warning in lenient.
   - Character sets: alias table lookup; unknown is a warning and stored in `raw`.
   - Special functionality: regex per entry; `BACmet` style typos are unknown lines
     (warning) kept in `unknown`.
   - Default restrictions: datatype key with `-`, `_`, or space normalisation (Annex c.7),
     colon optional, restriction parser from Phase 1.
   - Fail Times: `name: real`; alias table; completeness per D6; integer value coerced with warning.
6. Test database (`database.py`): see 3.2.
7. Document-level validators from Phase 2 run last; their diagnostics merge into the sink.
8. Ordering check (D4) and completeness check (D5).

`loads(text_or_bytes, *, strict=False, raise_on_error=True, source=None) -> EpicsDocument`.
`parse(...) -> ParseResult(document | None, diagnostics)` never raises.

## 3.2 Test database parser (`database.py`, 4.5.10)

- The list body is a sequence of `{ ... }` object blocks; commas between blocks are
  tolerated (Annex d.2). Anything else at depth 1 is an error with resynchronisation at
  the next `{`.
- Inside an object block, a property line is: `name` `:` value-tokens [marker] [`<`
  restrictions `>`] [comment]. The property name is the WORD run before the first `:` at
  depth 0 on a line; names may contain `-`, `_`, upper-case, and a leading ellipsis
  (stripped with warning, Annex d.3). No space after the colon is fine.
- Value extent: tokens from after the colon until the first `NEWLINE` at group depth 0.
  If nothing but a comment follows the colon on that line, the value begins on the next
  line (Annex d.19). Unbalanced groups extend across lines until balanced or until a line
  that looks like a new property at depth 0 (`^\s*[\w.-]+\s*:` and not a time literal),
  at which point an "unbalanced value" error is emitted and the group is closed.
- Markers: a trailing WORD `W` or `C` sets `access`; `R` is accepted as read-only with a
  warning (D20). Marker may precede or follow `<restrictions>` (D8).
- Trailing comment is stored in `PropertyEntry.comment`; a comment `-- @not-readable`
  sets `not_readable` (Phase 2 ADR 0004).
- First three properties must be `object-identifier`, `object-name`, `object-type` in that
  order (error otherwise, 4.5.10); the object-type value is normalised and compared with
  the identifier type; `object-type` written as `proprietary 700` or
  `proprietary-object-type-700` maps to the integer (D10).
- Object identifiers with a missing instance (`(life-safety-zone)`) are an error; the
  object is still created with `instance=None` only in lenient mode so later rules can
  report on it.

## 3.3 Writer (`writer.py`)

`dumps(doc, *, style=Canonical, line_ending="\r\n", charset_code=None) -> str` and
`dump(doc, path_or_binary_io)` which encodes per the header code.

Canonical output rules:
- Header, signature, sections in the 4.5 printed order, end line, CRLF.
- Section headings exactly as the 4.5 syntax blocks spell them; `{` on the same line as
  the heading, one entry per line indented two spaces, `}` on its own line.
- Services aligned in two columns (`name` padded to the longest, then `Initiate`/`Execute`).
- Object types with `Createable`/`Deleteable` as 4.5.4 spells them.
- Data link and special functionality via `canonical_text()`.
- Default restrictions in 4.4.2 colon form; fail times with one decimal place minimum.
- Objects: the three header properties first, remaining properties in model order, values
  via `render(node, style)`, then ` W`/` C`, then ` <restrictions>`, then ` -- comment`.
  Groups longer than 100 characters are wrapped one element per line with the opening
  delimiter on the property line.
- `Preserving` style keeps original real text, quote styles, delimiter choices.

The writer must emit a file that the strict reader accepts with zero diagnostics.

## 3.4 Tests (`tests/codecs/epics/`)

- Synthetic corpus (see `08-testing-and-compliance.md` §3) parsed in lenient mode: every
  file yields the expected document snapshot (`syrupy` or hand-written JSON expectations)
  and exactly the expected diagnostic codes (`expected_diagnostics.json` next to each
  fixture). Strict mode: the `strict=reject` subset fails with the expected codes.
- Round trip: for every corpus file, `loads(dumps(loads(f))) == loads(f)` (ignoring
  diagnostics and source), and `dumps(loads(dumps(doc)))` is byte-stable.
- Hypothesis: random documents from `tests/strategies.py` round trip through the writer and
  strict reader with zero diagnostics.
- Error recovery: unbalanced braces, stray closers, missing commas, missing signature,
  missing end line, wrong first three properties, duplicate sections, unknown section.
- Encodings: the same minimal document in all six charset codes reads to the same model.
- Private smoke test (skipped unless `ACE_EPICS_PRIVATE_FIXTURES` points at a directory):
  parse the locally reconstructed Annex A in lenient mode and assert the known counts
  (25 objects, 491 property lines) and the list of expected diagnostic codes from Annex §e.
  Never commit that file.
- Windows CI job runs this whole suite to catch CRLF handling regressions.

## 3.5 Documentation deliverables

- `docs/site/format-guide/overview.md`: file structure, strict vs lenient, what the writer
  canonicalises, a worked example (synthetic file, before and after `fmt`).
- `docs/site/format-guide/leniency.md`: table of every deviation accepted in lenient mode
  with its diagnostic code and the Annex A observation that motivated it.
- `docs/site/reference/diagnostics.md` extended with reader codes.
- API docs for `ace_epics.codecs.epics`.

## Acceptance criteria

- Every corpus file parses with the expected diagnostics in both modes.
- Writer output is strict-clean; round-trip properties hold for 2000 generated documents.
- Private Annex A smoke test passes locally for at least one maintainer and is documented
  in CONTRIBUTING as an optional step.
- Reader performance: a synthetic 10,000-object file parses in under 5 seconds on CI.
