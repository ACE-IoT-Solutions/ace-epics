# Strictness and accepted deviations

Lenient mode retains recoverable declarations and records the following deviations as warnings. Strict mode promotes them to errors. Normalization of case, underscores, permitted whitespace, charset aliases, and `Creatable` is supported in both modes without a deviation diagnostic.

| Deviation | Diagnostic | Motivation |
| --- | --- | --- |
| Bare LF or CR line terminators | `E-LINE-ENDINGS` | D2; canonical files use CRLF |
| Blank/comment gap before the signature | `P-SIGNATURE-POSITION` | D3; the signature immediately follows the header |
| Unquoted general-information string | `P-UNQUOTED-STRING` | Preserve common exporter output |
| Several BIBBs on one line | `P-BIBB-LAYOUT` | Printed syntax uses one entry per line |
| Unknown section | `P-UNKNOWN-SECTION` | Skip its balanced body; preserve source metadata |
| Sections outside printed order | `P-SECTION-ORDER` | D4; database-last remains mandatory |
| Missing sections | `P-SECTIONS-INCOMPLETE` | D5; Annex A omits Fail Times |
| Integer-valued timer | `P-TIMER-INTEGER` | 4.5.9 calls for real seconds |
| Missing template timers | `P-TIMERS-INCOMPLETE` | D6; older EPICS omit newer timers |
| Unknown timer name | `P-TIMER-UNKNOWN` | Preserve in `FailTimes.extra` |
| Baud rates with k suffixes | `P-BAUD-K` | Annex A §e.5 |
| Unknown data link | `P-UNKNOWN-DATA-LINK` | Annex A §e.5; preserve as `Other` |
| Incomplete data link | `P-DATA-LINK` | Annex A §e.5; lenient `Other` retains its line |
| Unknown character set | `P-CHARACTER-SET` | Preserve its spelling in `SourceInfo.raw` |
| Unknown special feature | `P-SPECIAL-UNKNOWN` | Annex A §e.6; preserve in `unknown` |
| Unknown default restriction datatype | `P-DEFAULT-TYPE` | 4.4.2 permits defaults not listed in 4.5.8 |
| Explicit property R marker | `P-READONLY-MARKER` | Annex A §e.3 |
| Leading ASCII or Unicode ellipsis on a property | `P-ELLIPSIS` | Annex A §e.11 |
| Restriction without a colon | `R-COLON` | Annex A §e.4 |
| Scientific or abbreviated real notation | `V-REAL-NOTATION` | Annex A §e.4 |
| Bare date | `V-BARE-DATE`, `R-BARE-DATE` | Annex A §e.4 |
| Abbreviated time precision | `V-TIME-PRECISION` | Annex A §e.14 |
| Odd-length octet string | `V-ODD-OCTETS` | Annex A §e.19 |
| Missing or trailing group comma | `V-MISSING-COMMA`, `V-TRAILING-COMMA` | Annex A §e.20 |

Balanced positional groups, unnamed optional elements, named enumeration groups, date ranges, multiline values, and comments inside values remain syntactically representable without guessing their BACnet datatypes. The separate knowledge provider supplies semantic checks.

Missing signatures/end lines, unbalanced section/property groups, stray closers, bad service flags, invalid parameter datatypes, unknown restriction names, mismatched headers, and duplicate object identifiers remain error diagnostics. Recovery preserves later usable content. The optional local Annex A smoke therefore uses `parse()` and checks its known diagnostic multiset rather than requiring error-free input.
