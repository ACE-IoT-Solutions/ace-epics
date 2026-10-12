# CLI reference

`ace-epics` uses argparse and shares the library's codec and validation APIs.
Global `--version`, `--quiet`, `--no-color`, and `--log-level` options precede
the subcommand. Output uses plain text by default.

| Command | Purpose | Options |
|---|---|---|
| `convert SRC DST` | Any supported serialization to another | `--from`, `--to`, `--strict`, `--values text\|tree`, `--base-iri` |
| `validate SRC` | Native diagnostics and Clause 5 report | `--strict`, `--rules ID,...`, `--knowledge PATH`, `--format text\|json\|markdown`, `--warnings-as-errors` |
| `fmt SRC` | Canonical native EPICS | `-o DST`, `--in-place`, `--preserve` |
| `inspect SRC` | Product identity and section counts | `--objects`, `--object TYPE,INSTANCE`, `--property NAME` |
| `schema` | Published JSON Schema to stdout | none |
| `ontology` | Published RDF vocabulary to stdout | none |

Format names are `epics`, `json`, `yaml`, and `rdf`; `native`, `turtle`, and `ttl`
are accepted aliases. `--values` applies to JSON and YAML. `--base-iri` applies
to RDF. `--strict` audits native EPICS syntax and, for validation, promotes
structural warning findings to errors.

Validation exits 0 for clean or warning-only reports, 1 for warning-only reports
with `--warnings-as-errors`, and 2 for errors. Skipped rules remain visible in the
report and do not themselves change the exit code. This policy follows the
Phase 6 plan; the library report's `exit_code()` method maps errors to 1.

JSON validation output includes `parse_diagnostics` alongside the document identity,
run time, tool version, and rule results. Native parse errors produce a JSON envelope
with diagnostics and an empty rule-result list. Text and Markdown include parse
findings as well as validation findings.

`fmt --in-place` serializes successfully before atomically replacing the file and
preserves its permissions. `--preserve` retains value formatting metadata where
representable. Native strings follow the format's quoting rules; unrepresentable
content is rejected explicitly.
