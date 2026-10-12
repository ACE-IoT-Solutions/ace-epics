# EPICS format guide

ASHRAE 135.1 Clause 4 defines EPICS text: a character-set header, opening signature,
general product information, capability sections, a test database, and closing
signature. Property values and access markers describe a device for test tools.

The implementation separates syntax from optional BACnet datatype interpretation.
The [value-model decision](../reference/decisions.md#two-layer-value-model) explains
why parsing does not depend on a knowledge provider. The implemented grammar and canonical writer behavior are described in these guides:

- [File structure and canonical output](overview.md)
- [Character encodings](encodings.md)
- [Sections and model fields](sections.md)
- [Value grammar](values.md)
- [Lenient parsing and diagnostics](leniency.md)
