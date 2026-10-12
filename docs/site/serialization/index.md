# Serialization

Four codecs share one Pydantic document model. Native EPICS implements ASHRAE
135.1 Clause 4; JSON, YAML, and RDF/Turtle provide interchangeable serializations.

Read the [overview](overview.md), [JSON guide](json.md), [YAML guide](yaml.md),
and [RDF guide](rdf.md). Shared conformance tests verify semantic identity and a
complete native → JSON → YAML → RDF → native cycle against the synthetic corpus.

```python
from ace_epics import convert

convert("device.tpi", "device.json")
convert("device.json", "device.ttl")
```

Canonical output normalizes layout and value spelling. Tagged JSON trees preserve
exact numeric values; text values provide compact EPICS literals. YAML and RDF
require their optional extras. The published [vocabulary](vocabulary.md) describes
queryable RDF terms and downloadable artifacts.
