# Object property knowledge

The bundled Clause 12 tables cover the fifteen object types in Phase 5's initial scope: Device; Analog, Binary, and Multi-state Input/Output/Value; File; Notification Class; Schedule; Calendar; and Trend Log. Each JSON table identifies its source edition, clause, table, object type, and verified protocol revision.

ASHRAE 135-2024 consolidates protocol revision 30. Complete property-fact snapshots cover revisions 14–30 for all fifteen types. The loader selects a versioned snapshot before consulting a current table within its declared coverage. Snapshot evidence records the official amendment chain used to reverse additions, removals, access conditions, datatype changes, and ranges. Individual lifecycle dates remain absent when no independent evidence establishes them; complete snapshots do not imply a known introduction date for every property. Revisions outside 14–30 are unavailable.

Each property has `requirement` (`required`, `optional`, or `conditional`), its BACnet datatype, minimum required access, original conformance code, and structured conditions. A table's R code requires readable support; it permits additional writable support. `access: R` therefore does not imply mandatory read-only behavior. `read_only: true` records an explicit restriction from the property's description. W requires writable support; C records conditional writability with its predicates. Optional properties can have conditions restricting when they may exist.

Conditions use a `kind` and operands:

| Kind | Meaning |
| --- | --- |
| `required_if` | Presence is required when the feature, service, or property predicate holds. |
| `only_if` | Presence is permitted only when the predicate holds. |
| `required_if_present` | Presence of the named property requires this property. |
| `required_if_any_present` | Any member of the named group requires this property. |
| `only_if_any_present` | This property is permitted only when some member of the named group exists. |
| `requires_property` | This property's presence requires the named property. |
| `all_or_none` | The named property group must be present together. |
| `at_least_one` | At least one named property must exist. |
| `writable_if` | Writable support is required when the predicate holds. |
| `read_only_if` | Writable support is forbidden when the predicate holds. |

Operands within one condition are conjunctive. Separate conditions are independent obligations. Feature predicates need evidence from the implementation; an unknown feature is not equivalent to a false feature. Services carry their initiation/execution direction. Initialized reference predicates distinguish the unspecified instance sentinel from a working reference.

`range` describes allowed values or lengths; `max_property` refers to an instance property such as Number_Of_States. `element_min` and `element_max` constrain array elements. `min_range` describes the minimum range that an implementation must support, rather than a limit on an individual value. For example, binary Change_Of_State_Count must support at least 0 through 65535. Fixed arrays have `array_length`.

Clause 21 identifiers and property descriptions resolve table spelling inconsistencies: Device uses the canonical `authorization-policy` and `authorization-scope`, and Trend Log uses `log-device-object-property`. The Analog Output Property_List description has a duplicated word in its heading; the property's read-only behavior is retained.

Tests check complete property counts, identifier resolution, known access distinctions, conditional groups, fixed arrays, revision facts, and range constraints. The licensed PDF, intermediate extracted text, and extraction script remain in ignored local directories. Shipped JSON contains normalized facts and predicates, not copied descriptive passages.

Historical reconstruction preserves wire semantics when a standard amendment changes terminology. Addendum 135-2020ck, revision 26, gives the renamed application types the same application tags, ASN.1 primitives, and value sets. Older snapshots therefore retain canonical `Real`, `Boolean`, and related types while `source_datatype` records spellings such as `REAL` and `BOOLEAN`. Addendum 135-2020ce, revision 24, similarly renames Max_Master and the subordinate-proxy properties without changing their identifiers or encoding; `source_name_aliases` preserves the earlier names and the provider resolves them.

The snapshots reverse factual changes rather than filtering property names alone. Examples include the four Device proxy properties removed at revision 17, Binary Value's Change_Of_State_Count datatype change at revision 16, reset-timestamp access conditions, Notification Class's earlier nonempty recipient list, Device's UTC offset range extension, and the revision 15 time-distribution property bundle. Current Device tables retain removed properties separately in `historical_properties` so lifecycle checks can identify them.

`runtime_constraints` retains sourced event and fault algorithm behavior, including the revision 28 Reliability configuration-fault additions. These annotations are evidence metadata: static EPICS validation does not simulate algorithm execution or prove runtime behavior. The minimum supported UTC-offset range also records its required 15-minute grid; endpoint facts and the grid are distinct from the allowed range of an individual value.
