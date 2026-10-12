# Phase 4: JSON, YAML, and RDF/Turtle Serdes

Goal: three additional codecs that read and write the same `EpicsDocument`, each passing a
shared codec conformance suite, with a published JSON Schema and RDF vocabulary. Depends
on Phases 2 and 3. Can run in parallel with Phase 5. Estimated effort: 7 to 10 days
(RDF is roughly half).

Modules: `codecs/base.py`, `codecs/json.py`, `codecs/yaml.py`, `codecs/rdf/` (`vocab.py`,
`writer.py`, `reader.py`, `ontology.ttl`), `codecs/registry.py`.

## 4.1 Codec protocol (`base.py`, `registry.py`)

```
class Codec(Protocol):
    name: str; extensions: tuple[str, ...]; media_type: str
    def loads(self, data: str | bytes, **opts) -> EpicsDocument
    def dumps(self, doc: EpicsDocument, **opts) -> str | bytes
    def load(self, src: Path | IO, **opts) -> EpicsDocument
    def dump(self, doc, dst: Path | IO, **opts) -> None
```
`registry.get("json")`, `registry.for_path(path)` (by extension: `.tpi` `.epics` native,
`.json`, `.yaml` `.yml`, `.ttl`). `ace_epics.load(path)` / `ace_epics.convert(src, dst)`
top-level helpers. Optional dependencies raise a clear `MissingExtraError("pip install
ace-epics[yaml]")`.

## 4.2 JSON (`json.py`)

- Document shape is `EpicsDocument.model_dump(mode="json", by_alias=False)` with a top-level
  `"$schema"` URL and `"format": "ace-epics/1"` version key for forward compatibility.
- Value nodes serialise as tagged objects via the `kind` discriminator, e.g.
  `{"kind": "real", "value": "13.4"}` (Decimal as string to stay exact),
  `{"kind": "date", "weekday": 1, "day": 24, "month": 1, "year": 1998}`,
  `{"kind": "group", "delimiter": "{", "elements": [...]}`,
  `{"kind": "object-identifier", "object_type": "analog-input", "instance": 56}`,
  `{"kind": "unspecified"}`. Wildcards serialise as the string `"*"`.
- Option `values="text"` emits each value as its canonical EPICS literal string instead
  (compact, human-readable); the reader accepts both forms by re-running the Phase 1 value
  parser on strings. Document this as lossy for `RealValue.text` only.
- `NamedToken` serialises as its canonical string; `raw` is dropped unless
  `preserve_raw=True`.
- JSON Schema: `EpicsDocument.model_json_schema()` post-processed to add `$id`
  (`https://w3id.org/ace-epics/schema/1/epics-document.json`), title, and examples;
  written by `scripts/gen_schema.py` to `schema/epics-document.schema.json`, checked in,
  snapshot-tested, and published on the docs site.

## 4.3 YAML (`yaml.py`)

- Same document shape as JSON (so a YAML file is valid input to the JSON reader after
  `yaml.safe_load`). Uses `yaml.safe_dump` with `sort_keys=False`, block style, and a
  custom representer for Decimal and the value nodes so output is readable:
  scalars as plain YAML scalars where unambiguous (`13.4` for reals is **not** used, because
  YAML would read it as float; reals stay tagged or quoted). Default `values="text"` for
  YAML because humans edit it; `values="tree"` available.
- Reader: `yaml.safe_load` only; never `yaml.load`. Reject documents with anchors that
  expand beyond a size limit (billion-laughs guard).
- Optional ruamel round-trip mode preserving comments is explicitly out of scope for 1.0.

## 4.4 RDF / Turtle (`codecs/rdf/`)

Vocabulary (`vocab.py`, `ontology.ttl`), namespace `epics: <https://w3id.org/ace-epics#>`
(register the w3id redirect to the docs site in this phase; D17). Reuse
`bacnet: <https://data.ashrae.org/bacnet/>` only for terms that the draft 135 Annex YY
actually defines (verify against the draft; if a term is not there, use `epics:`). Classes:

- `epics:Document` with datatype properties for the header code and general information
  (`epics:vendorName` etc.), and object properties `epics:bibb` (literal), `epics:service`
  (-> `epics:ServiceSupport` with `epics:serviceName`, `epics:initiate`, `epics:execute`),
  `epics:objectTypeSupport`, `epics:dataLink` (-> subclasses per `DataLinkOption` kind
  with `epics:baudRate` list), `epics:characterSet`, `epics:special` (-> `epics:SpecialFunctionality`),
  `epics:defaultRestriction` (-> `epics:RestrictionSet` with `epics:datatypeKey`),
  `epics:failTime` (-> `epics:FailTime` with `epics:timerName`, `epics:seconds`),
  `epics:object` (-> `epics:Object`) plus `epics:objectOrder` as an `rdf:List` of the
  objects because order is significant for round trip.
- `epics:Object`: `epics:objectType`, `epics:instance`, `epics:objectName`,
  `epics:property` (-> `epics:Property`), `epics:propertyOrder` (`rdf:List`).
- `epics:Property`: `epics:propertyName`, `epics:access` (`epics:ReadOnly`, `epics:Writable`,
  `epics:ConditionallyWritable`), `epics:notReadable`, `epics:comment`, `epics:restriction`,
  `epics:value` (-> value node).
- Value nodes: one class per `kind` (`epics:RealValue` ...), with `epics:lexical` holding
  the canonical EPICS literal text for every node (lossless), plus convenience typed
  literals where exact: `xsd:integer`, `xsd:boolean`, `xsd:decimal`, `xsd:string`,
  `xsd:hexBinary`, `xsd:date` and `xsd:time` only for fully specified dates/times.
  Groups: `epics:delimiter` and `epics:elements` as an `rdf:List`; `epics:EmptyElement`
  and `epics:UnspecifiedValue` are singletons.
- IRIs: document base from `base_iri` option (default a `urn:uuid:` per dump); objects at
  `<base>/object/<type>/<instance>`; properties at `<base>/object/<type>/<instance>/<name>`;
  value nodes are blank nodes. Object type and property names also link to
  `bacnet:<name>` IRIs when the knowledge provider knows the name (Phase 5 optional hook).
- Writer: rdflib `Graph`, `serialize(format="turtle")` with bound prefixes; deterministic
  output (sorted triples; rdflib's turtle serialiser is stable enough with blank-node
  ordering handled by using skolem IRIs under `<base>/_/n` when `deterministic=True`).
- Reader: parse any rdflib-supported syntax (turtle, n-triples, JSON-LD if available);
  rebuild the document from `epics:lexical` strings via the Phase 1 value parser, using the
  `rdf:List` orderings. Structured value triples are not read back (they are derived), which
  keeps the reader simple and the round trip exact.
- Ship `ontology.ttl` (RDFS plus a few OWL class disjointness statements) and a SHACL
  shapes file `shapes.ttl` that constrains an `epics:Document` graph; `pyshacl` validation
  is an optional dev-only test, not a runtime dependency.
- Document the JSON-LD context (`context.jsonld`) mapping the JSON document shape to the
  vocabulary as a stretch goal; it is not required for the round-trip guarantee.

## 4.5 Shared codec conformance suite (`tests/codecs/test_conformance.py`)

Parametrised over every registered codec:
- For every synthetic corpus document and 500 Hypothesis documents:
  `codec.loads(codec.dumps(doc)) == doc` (excluding diagnostics and source).
- Cross-codec: `json -> yaml -> ttl -> epics -> json` returns the starting document.
- Determinism: dumping twice yields identical bytes.
- Size: a 10,000-object document dumps and loads in under 10 seconds for each codec.
- Media types and extensions registered; `MissingExtraError` raised when extras absent
  (tested by monkeypatching the import).

Format-specific tests: JSON Schema validates every dumped JSON document (jsonschema in dev
deps); YAML safe-load only; RDF graph conforms to `shapes.ttl` (pyshacl, dev only); RDF
reader rejects graphs with no `epics:Document`.

## 4.6 Documentation deliverables

- `docs/site/serialization/overview.md` (choosing a format, lossless guarantees, extras).
- `docs/site/serialization/json.md` (document shape, value node table, schema link),
  `yaml.md`, `rdf.md` (vocabulary reference generated from `ontology.ttl`, example graph,
  IRI scheme, how to join with 223P models).
- Published artifacts on the site: `schema/epics-document.schema.json`, `ns/epics.ttl`,
  `ns/shapes.ttl`, `ns/context.jsonld` (if done); w3id redirects point at them.
- CHANGELOG entries and README "formats" section.

## Acceptance criteria

- Four codecs pass the conformance suite on both CI operating systems.
- Schema and ontology files are checked in, snapshot-tested, and served by the docs site.
- `ace_epics.convert("x.tpi", "x.ttl")` works end to end in the quick-start example.
