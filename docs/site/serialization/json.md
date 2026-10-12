# JSON

The JSON codec writes `ace-epics/1` documents with a `$schema` identifier and the
Pydantic document's field names. Read the [published schema](../schema/epics-document.schema.json).
Unknown format versions and invalid documents raise a structured `EpicsError`.

```python
from ace_epics.codecs import json

text = json.dumps(document)
restored = json.loads(text)
assert restored == document
```

Values use a `kind` discriminator. Real numbers store exact decimal strings;
octet strings use hexadecimal strings. Unspecified values have `kind: unspecified`.
Dates and times keep their component fields; wildcard components serialize as `*`.
Groups retain delimiters and ordered elements. Names use normalized strings;
`preserve_raw=True` retains the original name spelling in a mapping.

`values="text"` writes canonical EPICS literal strings and accepts them on input.
Tagged and text values may be mixed in the same document. Text mode preserves semantic
values but canonicalizes lexical metadata, including the original real spelling,
quotation style, and abbreviated times. Diagnostics and source metadata are not
serialized. Tree mode retains value-node lexical metadata.

```python
compact = json.dumps(document, values="text", indent=None)
json.dump(document, "example.json")
restored = json.load("example.json")
```

Regenerate the checked-in schema with `uv run python scripts/gen_schema.py`.
Its identifier is `https://w3id.org/ace-epics/schema/1/epics-document.json`;
external redirect registration is a release infrastructure task.
