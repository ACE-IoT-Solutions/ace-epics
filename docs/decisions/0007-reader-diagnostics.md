# ADR 0007: Separate recoverable parsing from document convenience readers

Date: 2026-10-11
Status: accepted

## Context

The testing plan requires readers to collect diagnostics for arbitrary input.
The codec protocol also declares `loads` as returning an EpicsDocument. Malformed
JSON, YAML, or RDF may contain no recoverable document or vendor information.
Constructing a placeholder document would invent facts absent from the input.

## Decision

Every codec exposes `parse`, returning a shared ParseResult with an optional document
and diagnostic list. Arbitrary malformed input yields diagnostics and `document=None`
when recovery is impossible. Property P8 exercises these nonraising parsing entry
points. Missing optional codec dependencies remain explicit MissingExtraError failures.

`loads` is the convenience document API and raises collected EpicsError failures by
default. `raise_on_error=False` returns a document only when the reader has actually
recovered one. An unrecoverable parse still raises; callers needing a nonraising
result use `parse`. Source metadata and diagnostic findings are not interchange facts.

## Consequences

All four codecs share the same result semantics. Conversion tools must inspect error
diagnostics before writing recovered documents. Invalid input never acquires invented
vendor, object, or property facts. This interpretation preserves both the typed codec
protocol and the testing plan's recovery requirement.
