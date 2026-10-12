# ace-epics

ace-epics implements BACnet EPICS, the Electronic Protocol Implementation
Conformance Statement format described in ASHRAE 135.1 Clause 4, and static
consistency checks from Clause 5.

Python 3.13 or newer is required. The project is under active development: consult
the [conformance matrix](reference/conformance.md) for implemented and planned rules.
The matrix describes test evidence, rather than claiming certification.

Begin with [getting started](getting-started.md), then read the
[format guide](format-guide/index.md) and [validation guide](validation/index.md).


## Try all four formats

From the checkout, install the optional codecs with `uv sync --all-extras`, then
run this example using the invented fixture. Replace the input path with your
vendor's EPICS when using your own device.

```python
from ace_epics import dump, load, validate

native = load("tests/fixtures/epics/full.tpi", strict=True)
dump(native, "example.tpi")  # Native EPICS for BACnet test tools
dump(native, "example.json")  # Tagged values and JSON Schema
dump(native, "example.yaml")  # YAML with the same document fields
dump(native, "example.ttl")  # Queryable RDF/Turtle

assert load("example.json") == native
assert load("example.yaml") == native
assert load("example.ttl") == native
print(validate(native).summary())
```

Read the [serialization overview](serialization/overview.md) to choose a format,
or use `uv run ace-epics convert example.tpi example.json` at the command line.
