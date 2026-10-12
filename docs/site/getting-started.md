# Getting started

Python 3.13 or newer is required. Install from a checkout while the library is in
development:

```sh
uv sync --all-extras --group dev
uv run pytest
uv run mkdocs build --strict
```

For a runtime installation from local source, use `uv pip install '.[all]'`.
The import name is `ace_epics`; YAML and RDF dependencies are optional extras.

## Parse, validate, and convert

```python
from ace_epics import convert, load, validate
from ace_epics.codecs.epics import parse

# Replace this repository fixture with the EPICS from your vendor.
document = load("tests/fixtures/epics/full.tpi", strict=True)
report = validate(document)
print(report.summary())
print(report.to_markdown())
convert("tests/fixtures/epics/full.tpi", "example.json")
convert("example.json", "example.ttl")

# For diagnostic collection without raising, use the native parser.
result = parse(b"malformed input", strict=True)
for diagnostic in result.diagnostics:
    print(diagnostic.code, diagnostic.message)
```

`load` infers the codec from `.tpi`, `.epics`, `.json`, `.yaml`, `.yml`, or `.ttl`.
`format="json"` overrides inference. Native `strict=True` audits standard syntax;
default lenient parsing accepts documented variations and retains diagnostics.

`validate` returns each registered rule's outcome. A `skipped` result means a fact
was unavailable. It does not establish conformance. See the
[knowledge coverage](validation/knowledge.md) and [generated rule table](validation/rules.md).

## Command line

```sh
uv run ace-epics inspect tests/fixtures/epics/full.tpi --objects
uv run ace-epics validate tests/fixtures/epics/full.tpi --format json
uv run ace-epics convert tests/fixtures/epics/full.tpi example.yaml
uv run ace-epics fmt example.yaml -o canonical.tpi
uv run ace-epics schema
```

Read the [CLI reference](reference/cli.md), [query API](validation/query-api.md),
and [serialization guides](serialization/overview.md) for options. Tests use
synthetic documents and need no licensed standard file.
