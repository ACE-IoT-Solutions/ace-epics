# Knowledge tables

The packaged provider reads factual names, identifiers, bit layouts, Annex K service
requirements, and Clause 12 property facts extracted from ASHRAE 135-2024. Each file
names its source edition. The licensed PDFs and private text extracts are ignored by
Git. The repository contains synthetic fixtures and factual tables.

Enumeration history and exact bit counts cover Protocol_Revision 14–30. Object
property snapshots cover revisions 14–30 for all fifteen bundled object types.
Historical snapshots reverse sourced amendments to the current tables; their evidence
records identify the official addenda. The loader returns `None` outside verified
coverage instead of applying a modern requirement to an old device. BIBBs retain
conditional requirements, alternatives, and transitive dependencies.

```python
from ace_epics.knowledge import JsonKnowledgeProvider, NullProvider
from ace_epics.validation import validate

report = validate(document, JsonKnowledgeProvider())
custom = validate(document, JsonKnowledgeProvider("my-knowledge-data"))
without_external_data = validate(document, NullProvider())
```

A custom provider implements the `KnowledgeProvider` protocol. Empty mappings and
`None` mean unavailable data and produce `SKIPPED` findings where those facts are
needed. A read conformance code R means minimally readable; `read_only: true` is a
separate verified obligation. This distinction matters for C5-18.

To update tables, extract a licensed standard privately, record edition and clause,
verify names and numbers, and add lifecycle metadata only with revision evidence.
Run the knowledge tests and the development cross-check:

```sh
uv run pytest tests/knowledge tests/unit/test_knowledge_provider.py
uv run --with bacpypes3 python scripts/knowledge/check_against_bacpypes3.py
```

The cross-check reports numeric mismatches separately from newer entries absent in
the comparison stack. Do not copy implementation code from incompatible licenses.
See [object knowledge](object-knowledge.md) and [BIBB knowledge](bibb-knowledge.md)
for coverage and conditional interpretation. Runtime algorithm constraints retained
in the tables are provenance metadata; the static validator does not execute BACnet
event or fault algorithms.


Providers may implement the optional `CapabilityProvider` contract:
`capabilities() -> frozenset[str]`. The engine checks each rule's `requires` before
running it and emits one SKIPPED diagnostic if a declared family is absent. The
packaged JSON provider advertises `bibbs`, `objects`, `services`, `object_types`, and
`property_identifiers` when the corresponding tables exist; `NullProvider` declares
an empty set. Custom providers can advertise additional names for custom rules.

A capability promises a knowledge family, not complete object or revision coverage.
Missing individual definitions, conditions, and enumerations still produce SKIPPED
findings during a rule. Legacy providers without `capabilities()` retain lookup-based
behavior; their rules run and must report unavailable facts themselves. C5-07 checks
declared object instances directly and requires no external capability.
