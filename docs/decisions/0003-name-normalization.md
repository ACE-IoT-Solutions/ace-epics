# D11: Normalize names and retain spelling

Accepted. Clause 4.4i names are case-insensitive; examples use spaces, underscores, and hyphens inconsistently. `NamedToken` stores `canonical` and `raw`. Normalization lowercases names, replaces spaces and underscores with hyphens, and collapses separator runs. Equality and hashing use only the canonical name. Original spelling remains available to preserving writers.

The `name`/`original` aliases and properties support value-tree consumers. BIBB shape validation is advisory because Annex K is external knowledge. Service CamelCase aliases belong to the native parser's literal recognition rather than generic name normalization.
