# ace-epics

BACnet EPICS (ASHRAE 135.1) parsing, serialization, and static consistency validation
for Python. EPICS means Electronic Protocol Implementation Conformance Statement.

The library reads native `.tpi` files, converts between EPICS, JSON, YAML, and
RDF/Turtle, and runs all 20 Clause 5 checks through a pluggable BACnet knowledge
provider. Python 3.13 or newer is required. Development follows the
[phased workplan](docs/plans/00-overview.md).

Enumeration tables cover Protocol_Revision 14–30. Shipped object property snapshots
cover revisions 28–30; unresolved historical definitions and implementation conditions
are reported as `SKIPPED`. See the [knowledge guide](docs/site/validation/knowledge.md).
The project is in development and has not completed the release acceptance gates.

```python
from ace_epics import convert, load, validate

# Supply your device's EPICS file.
document = load("device.tpi")
report = validate(document)
print(report.summary())
convert("device.tpi", "device.ttl")
```

From a repository checkout:

```sh
uv sync --all-extras --group dev
uv run pytest
uv run mkdocs build --strict
```

Read the [getting started guide](docs/site/getting-started.md),
[format guide](docs/site/format-guide/index.md), and
[contribution guide](CONTRIBUTING.md). API pages and the conformance matrix are
rendered during the documentation build.

The project uses the Apache License 2.0. Licensed standards PDFs and verbatim
extractions are private inputs; fixtures are synthetic and committed knowledge
records contain identifiers and interpreted facts with edition attribution.

## Interchange formats

The JSON codec stores exact tagged value trees and publishes a JSON Schema. YAML
uses the same model with editable EPICS literal strings. RDF/Turtle exposes ordered
objects, properties, services, timers, restrictions, and typed value information.
See the [serialization guides](docs/site/serialization/overview.md) for extras and
semantic round-trip behavior.
