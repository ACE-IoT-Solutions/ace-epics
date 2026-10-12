# YAML

Install the `yaml` extra. YAML uses the JSON document shape and defaults to canonical
EPICS literal strings for values. Exact real values are quoted or tagged rather than
being converted to binary floating point.

```python
from ace_epics.codecs import yaml

text = yaml.dumps(document)
restored = yaml.loads(text)
assert restored == document
```

Use `values="tree"` to retain value-node lexical metadata. `preserve_raw=True`
retains name spellings. Readers use `yaml.safe_load` exclusively. Recursive aliases,
excessive expansion, and nesting beyond configured limits raise `EpicsError`.
The `max_nodes` and `max_depth` options bound expanded input traversal; ordinary
anchors remain supported within those limits.

Unknown YAML tags are rejected. Comment-preserving editing with ruamel is outside
the current codec's scope. Missing optional dependencies raise `MissingExtraError`
with the extra's installation command.
