# ADR 0005: argparse CLI

Status: accepted.

The Phase6 command-line interface uses Python's standard-library `argparse`.
This keeps the runtime dependency set at Pydantic with optional YAML and RDF extras.
Commands share the public codec registry and validation APIs. Validation exits0
for clean/warning-only reports,1 for warnings with `--warnings-as-errors`, and2
for parsing or validation errors, following the Phase6 CLI plan.
