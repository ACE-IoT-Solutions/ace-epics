# Query API

`Query(document, provider)` exposes the facts consumed by ASHRAE 135.1 Clauses 5
and 7. Values come from the document; datatype and standard range metadata come
from the selected `KnowledgeProvider`.

```python
from ace_epics.knowledge import JsonKnowledgeProvider
from ace_epics.validation import Query

query = Query(document, JsonKnowledgeProvider())
revision = query.protocol_revision
for objects in query.variants("analog-output"):
    representative = objects[0]
    for entry in representative.properties:
        if query.is_writable(representative, entry.name.canonical):
            limits = query.limits(representative, entry.name.canonical)
```

`is_writable` includes W and C. `is_conditionally_writable` identifies C alone.
`is_readable` respects the `not_readable` interchange extension. Missing properties
raise `KeyError` when an access declaration or limits are requested.

`limits` merges property restrictions over datatype defaults over sourced standard
bounds. Each nonempty override field replaces that field; it does not remove other
bounds. Property-relative standard endpoints are resolved from the same object;
an unspecified referenced value leaves that endpoint unavailable. Standard string,
list, and array maximum lengths are included when the datatype is known.
`expected_property_list` omits Object_Name, Object_Type, Object_Identifier,
and Property_List. `array_length` returns a group element count corresponding to
index-zero array semantics. Datatype interpretation is necessary to distinguish
an array from another constructed group.

`variants` groups by property set, access, readability, and effective restrictions.
Current values and declaration order do not create a variant. `object_list` and
supported-bit accessors return `None` for malformed or unspecified values, preserving
the distinction between an empty list and unavailable evidence.
