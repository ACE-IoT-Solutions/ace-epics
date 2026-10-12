# Native EPICS files

An EPICS file starts with `PICS n`, immediately followed by the conformance signature, then the four general-information lines and nine braced sections. The test database is last. The end-of-conformance line terminates the file. Canonical output uses CRLF and the printed section order.

```python
from ace_epics.codecs.epics import load, dumps, parse

result = parse(data, strict=False)
for finding in result.diagnostics:
    print(finding.code, finding.line, finding.message)

if result.document is not None:
    canonical_text = dumps(result.document)
```

`parse()` returns a shared `ParseResult` and never raises for malformed input. `load()` and `loads()` raise `EpicsError` on error diagnostics by default; `raise_on_error=False` returns a recovered document when one is available. Strict mode promotes accepted syntactic deviations to errors. Hard defects, including missing signatures and inconsistent object headers, remain errors in both modes.

The writer emits canonical heading spellings, `Createable`/`Deleteable` flags, one declaration per line, colon-form restrictions, and real-valued timers. It preserves property order and comments. Groups longer than 100 characters are wrapped. `Preserving` retains value-level real spelling, quotes, and group punctuation; original whole-file layout is not retained. Unsupported character strings containing line breaks or both closing quote characters raise an explicit error.

For example, this lenient input:

```text
Vendor Name: Example Works
```

is written as:

```text
Vendor Name: "Example Works"
```

A lenient `Notification Fail Time: 2` becomes `Notification Fail Time: 2.0`. An explicit property `R` marker is omitted. A property recorded as inaccessible via ReadProperty gets the extension comment `-- @not-readable`.

`dumps()` returns text. `dump()` writes encoded bytes to a path or binary stream using the PICS header's character-set selector. All six selectors are supported; wide encodings use big-endian, BOM-free output. DBCS on non-Windows systems uses CP932 with an ambiguity diagnostic.

Malformed object values recover at the next property or object header. Later valid objects remain available for consistency checks. An object with a missing identifier instance is skipped with `P-OBJECT-IDENTIFIER`; the model does not invent an instance or weaken its 22-bit identifier invariant.

Source paths, decoding information, and unknown lenient section/character-set entries are recorded in `SourceInfo`. Document equality excludes source metadata and diagnostics. Lexical value hints are also excluded from semantic equality. These rules support canonical round trips across native, JSON, YAML, and RDF codecs.
