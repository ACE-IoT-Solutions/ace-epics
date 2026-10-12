# ace-epics: Implementation Program Overview

`ace-epics` is a public, PyPI-published Python library that implements the BACnet EPICS
(Electronic Protocol Implementation Conformance Statement) file format defined in
ANSI/ASHRAE Standard 135.1-2025, Clause 4, together with the Clause 5 EPICS consistency
tests. One Pydantic type structure is the single in-memory representation; four
serializations read and write it losslessly at the semantic level:

| Format | Role | Library |
|---|---|---|
| Native EPICS text (`.tpi`) | Normative format from 135.1 Clause 4 | hand-written lexer/parser + writer |
| JSON | Canonical interchange, JSON Schema published | Pydantic |
| YAML | Human-editable interchange, same document model as JSON | PyYAML (ruamel optional) |
| RDF / Turtle | Linked-data form for 223P / knowledge-graph integration | rdflib |

Source material used to build these plans lives in `docs/spec/` (digests of the standard,
paraphrased, with clause citations). The standard itself is copyrighted and must never be
committed; see "Licensing and copyright" below.

## Phases

| Phase | Plan | Outcome | Depends on |
|---|---|---|---|
| 0 | [01-phase-0-foundation.md](01-phase-0-foundation.md) | Repo, toolchain, CI, docs skeleton, release pipeline | none |
| 1 | [02-phase-1-lexer-and-values.md](02-phase-1-lexer-and-values.md) | Encoding detection, tokenizer, value grammar, restrictions grammar | 0 |
| 2 | [03-phase-2-data-model.md](03-phase-2-data-model.md) | Complete Pydantic model of every EPICS section | 0 (can run parallel with 1) |
| 3 | [04-phase-3-parser-and-writer.md](04-phase-3-parser-and-writer.md) | Native EPICS reader and writer, diagnostics, round-trip | 1, 2 |
| 4 | [05-phase-4-serdes.md](05-phase-4-serdes.md) | JSON, YAML, RDF/Turtle serdes, JSON Schema and ontology publication | 2, 3 |
| 5 | [06-phase-5-validation.md](06-phase-5-validation.md) | Clause 5 consistency rule engine, BACnet knowledge tables, query API | 3 |
| 6 | [07-phase-6-cli-docs-release.md](07-phase-6-cli-docs-release.md) | CLI, documentation site, 1.0 release | 4, 5 |
| X | [08-testing-and-compliance.md](08-testing-and-compliance.md) | Cross-cutting test and compliance strategy (applies to every phase) | 0 |

Phases 1 and 2 can be worked in parallel by two people. Phase 4 and Phase 5 can also run
in parallel once Phase 3 is merged. Each phase plan lists its tasks, acceptance criteria,
tests, and documentation deliverables. A phase is done when every acceptance criterion is
met, the conformance matrix in `08-testing-and-compliance.md` is updated, and the docs for
that phase are merged.

## Architecture (fixed decisions)

These decisions are made; the phase plans build on them. Re-open one only with a written
rationale in `docs/decisions/`.

1. **Two-layer value model.** EPICS property values are untyped text (the datatype comes
   from the property, which 135.1 does not define). The parser therefore produces a
   *syntactic* value tree (`ValueNode`: Null, Boolean, Integer, Real, OctetString,
   CharacterString, BitString, Enumerated, Date, Time, ObjectIdentifier, ParenGroup/List,
   BraceGroup/Constructed, ContextTagged, Unspecified `?`) without consulting any BACnet
   knowledge. A separate, optional *interpretation* layer resolves ambiguous nodes
   (parentheses are overloaded for dates, object identifiers, and lists) against a
   declared BACnet datatype when one is available. Parsing never fails for lack of
   BACnet knowledge.
2. **Semantic round trip, not byte round trip.** `parse(write(parse(x))) == parse(x)` is
   guaranteed for every format. Comments on property lines are preserved as data;
   whitespace, line breaks, and keyword case are canonicalized by the writer.
3. **Strict and lenient modes.** `strict=True` enforces the standard literally (CRLF
   endings, no BOM, all 13 Fail Times, Test Database last, exact literals). The default
   lenient mode accepts common real-world deviations and reports them as warnings. Both
   modes return the same model type.
4. **Diagnostics are data.** Every parse and validation problem is a `Diagnostic` with
   severity, code, clause reference, line/column, and message. Parsing collects
   diagnostics rather than raising on the first error; `raise_on_error` wraps them.
5. **BACnet knowledge is a pluggable data provider.** Enumerations, bit counts per
   Protocol_Revision, BIBB tables, and per-object required-property tables live in
   `ace_epics.knowledge` as versioned JSON data behind a `KnowledgeProvider` protocol.
   Validation rules that lack data report `SKIPPED` rather than passing silently.
6. **One model, four codecs.** `ace_epics.model` has no I/O. Each codec lives in
   `ace_epics.codecs.<name>` with `loads/dumps/load/dump` and a shared conformance test
   suite that every codec must pass.
7. **Runtime dependencies stay minimal.** Required: `pydantic>=2`. Optional extras:
   `yaml` (PyYAML), `rdf` (rdflib), `cli` (typer or argparse-only; decided in Phase 6).
8. **Python 3.13 minimum**, tested on 3.13 and 3.14. (The current `pyproject.toml` says
   `>=3.14` and uses `uv_build`; Phase 0 corrects both to match the global standards.)

## Package layout

```
src/ace_epics/
  __init__.py            public API re-exports, __version__
  diagnostics.py         Diagnostic, Severity, DiagnosticSink
  encoding.py            header detection and decoding (4.1)
  lexer.py               tokens (4.2, 4.3)
  values/                ValueNode AST, value grammar (4.4, 4.4.1), restrictions (4.4.2)
  model/                 Pydantic models per section (4.5)
  codecs/
    epics.py             native reader/writer (Clause 4)
    json.py, yaml.py, rdf.py
  knowledge/             BACnet 135 tables, KnowledgeProvider
  validation/            Clause 5 rules engine, query helpers
  cli.py                 Phase 6
tests/
  unit/, codecs/, validation/, fixtures/, conformance/
docs/
  spec/                  digests of the standard (internal reference)
  plans/                 these plans
  decisions/             ADRs for any change to the fixed decisions above
  site/                  mkdocs source (Phase 0 skeleton, filled per phase)
```

## Licensing and copyright

- The ASHRAE 135.1-2025 and 135-2024 PDFs live in `resources/`, which is gitignored along
  with `*.pdf`. They are licensed to one person. Never commit them or any verbatim
  extraction of them; `docs/spec/` digests are the only derived material allowed in git.
- Annex A's example EPICS is informative but still copyrighted. The test corpus will be
  **synthetic** files written by the team that exercise every notation Annex A uses
  (inventory in `docs/spec/04-annex-a-example-analysis.md`). Annex A may be used locally
  as a private smoke test only; CI must not depend on it.
- `docs/spec/*.md` paraphrase the standard with short quoted keywords and syntax
  examples. Keep them that way; do not expand them into reproductions.
- Enumeration names, keyword lists, and bit layouts from ASHRAE 135 are facts needed for
  interoperability and appear in several open-source BACnet stacks. Document the source
  edition for every knowledge table.
- Library license: Apache-2.0 (patent grant matters for a protocol library). Decide in
  Phase 0 and record it.

## Naming

- PyPI distribution name `ace-epics`, import name `ace_epics`. A search found no existing
  package with that name. Note the collision risk with the unrelated physics "EPICS"
  control system (`pyepics`); the PyPI description and README must say "BACnet" in the
  first sentence.

## Decision log (items the digests left open, now decided)

| # | Question (digest ref) | Decision |
|---|---|---|
| D1 | BOM handling (01 §8.1) | Lenient: strip a UTF-8/UTF-16/UTF-32 BOM and warn. Strict: error. |
| D2 | Bare LF line endings (01 §8.6) | Lenient: accept, warn once. Strict: error. Writer always emits CRLF. |
| D3 | Header/signature/end literal case (01 §8.5) | Case-insensitive match, trailing whitespace and comments allowed. Writer emits canonical case. |
| D4 | Section order (02 §5.1) | Lenient: any order, Test Database must be last. Strict: printed order of 4.5. Writer emits printed order. |
| D5 | Mandatory sections (02 §5.1) | All sections in the 4.5 table are required to be present; lists may be empty. Lenient mode downgrades missing non-database sections to warnings. |
| D6 | Fail Times completeness (02 §5.15) | Model has the 13 template timers plus `Audit Notification Forwarder Fail Time` and an `extra` map. Strict: all 13 required. Lenient: missing timers are warnings. |
| D7 | Parenthesis ambiguity (01 §8.18) | Parser emits `ParenGroup`; a classifier yields Date / ObjectIdentifier / List using syntactic shape; the interpretation layer overrides with datatype when known. |
| D8 | `W`/`C` vs `<restrictions>` order (02 §5.7) | Accept either order. Writer emits `value W <restrictions> -- comment`. |
| D9 | `?` scope (02 §5.8) | Allowed as a whole property value and as a bit inside bit strings. Allowed inside list/array elements in lenient mode with a warning. |
| D10 | Proprietary object-type spelling (02 §5.9) | Accept `proprietary 700`, `proprietary-700`, `proprietary-object-type-700`. Model stores the integer. Writer emits `proprietary 700` in identifiers and `proprietary-object-type-700` as an enumeration. |
| D11 | Name normalization (02 §5.5) | All keyword, enumeration, property, service, and object-type comparisons are case-insensitive with `_`, `-`, and space treated as equivalent. Model stores canonical lowercase-hyphen enumeration form plus the original text for display. |
| D12 | Unterminated strings (01 §8.9) | Terminate at end of line and warn (both modes). |
| D13 | Numeric notation (01 §8.11) | No exponent, no `+`, no INF/NaN. Real requires digits on both sides of the point. Unsigned vs Integer is decided by the interpretation layer, not the lexer. |
| D14 | Unknown restriction names (01 §9.55) | Error in both modes; the seven names in 4.4.2 are the closed set. |
| D15 | C5-15 revision boundary (03 C5-15) | Property deprecated at revision N is allowed at N, rejected at N+1 and later. |
| D16 | C5-07 File exception (03 C5-07) | Zero File objects with File type supported is a warning, never an error. |
| D17 | RDF identifiers | Objects get IRIs minted from a document base IRI; ordering kept with `rdf:List` where the standard makes order significant (object property order, array elements). Vocabulary namespace `https://w3id.org/ace-epics#` (register the w3id redirect in Phase 4) with `bacnet:` (`https://data.ashrae.org/bacnet/`) terms reused where the draft 135 Annex YY defines them. |
| D18 | `Creatable` vs `Createable` (04 §e.2) | Accept both spellings; writer emits `Createable` (4.5.4). |
| D19 | Baud rate suffixes `14.4k` (04 §e.5) | Lenient: normalize `k` suffix to integer bits per second with a warning. Strict: error. |
| D20 | `R` marker (04 §e.3) | Accept as read-only with a warning; writer never emits it. |
| D21 | Exponent reals, bare restriction dates, colon-less restriction names (04 §e.4) | Lenient: accept with warnings. Strict: reject. Writer emits 4.4.2 form. |
| D22 | Times without seconds or with one fractional digit (04 §e.14) | Lenient: accept, record precision. Writer emits `hh:mm:ss.xx`. |
| D23 | Untagged CHOICE values, date ranges, named-bit lists, empty elements (04 §e.12-18) | Parsed as generic groups/ranges at the syntactic layer; interpretation is deferred to the typed layer. No warning, since the standard's own example uses them. |
| D24 | Trailing or missing commas, stray closers (04 §e.20) | Lenient: repair with a warning (trailing) or error-but-continue (missing/stray). Strict: error. |
| D25 | Odd-length octet strings (04 §e.19) | Lenient: warning, value padded with a leading zero nibble. Strict: error. |
| D26 | Unknown data link or special functionality lines (04 §e.5-6) | Captured verbatim in `Other`/`unknown` with a warning so nothing is lost. |

## Definition of done for 1.0

- Every clause 4 rule in `docs/spec/01` and `02` maps to at least one test in the
  conformance matrix.
- All 20 Clause 5 checks implemented; those needing knowledge tables ship with tables for
  Protocol_Revision 14 through the latest the team can source, and report SKIPPED below.
- Four codecs pass the shared codec conformance suite.
- Published docs site with API reference, format guide, validation guide, and examples.
- `uv build` produces a wheel and sdist; release workflow publishes to PyPI on tag.


## Integration status (2026-10-11)

The local implementation for Phases 0-6 is present: encoding/value parsing, Pydantic
models, four codecs, all 24 validation checks, revision-aware knowledge, query tools,
CLI commands, generated documentation, and release workflows. Three parallel agents
extracted the enumeration, object, and BIBB facts and completed independent reviews.
The conformance matrix contains 369 implemented entries, including all digest seeds.

Final frozen-source verification: 1,165 tests passed and one optional private smoke
was skipped in the public suite; the private licensed Annex smoke passed separately.
Overall statement coverage is 98.42%, and every required module group exceeds 95%.
Lint, formatting, type checking, and pre-commit checks pass. Strict docs build and
68-page local-link check pass. Two distribution archives passed metadata and data
checks; all eight clean installs passed across Python 3.13/3.14, base/all extras,
and wheel/source archive. The full synthetic corpus has zero validation errors.

The 1.0 definition of done remains open for external gates: live Ubuntu/Windows CI,
GitHub Pages hosting, w3id redirects, TestPyPI/PyPI publication and installation, and
release sign-off. This checkout has no configured Git remote. Workflow files and
local build results do not establish those external outcomes. The current development
version remains 0.0.1; no release has been tagged or published.


### Follow-up completion audit

The public-symbol clause-citation check is now automated (47 source modules), CLI
JSON envelopes are schema-validated for successful, rule-failure, and parse-failure
responses, and the documentation includes examples for all four formats plus every
ADR, the security policy, and the license. The release workflow verifies the exact
published TestPyPI version on both supported Python versions and checks site links
before building artifacts. Those workflow steps are configured but await a live run.
A GitHub repository-name search did not identify a destination; the repository URL
and external publishing/hosting configuration are still required to finish 1.0.
