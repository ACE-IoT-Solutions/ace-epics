# RDF and Turtle

Install the `rdf` extra. The codec emits a queryable graph using the project namespace
`https://w3id.org/ace-epics#`. It records individual objects, properties, access flags,
services, data links, timers, restrictions, and value nodes. It retains declaration
order using RDF lists rather than depending on triple order.

```python
from ace_epics.codecs import rdf

text = rdf.dumps(document, base_iri="urn:example:device", deterministic=True)
restored = rdf.loads(text)
assert restored == document
```

Objects use `<base>/object/<type>/<instance>` IRIs, and properties append their
normalized names. Other structured records and list cells use blank nodes normally,
or stable skolem IRIs in deterministic mode. When no base is supplied, ordinary
writes use a UUID; deterministic writes derive the base from the document content.
Sorted N-Triples provide deterministic Turtle output. Other RDF syntaxes can be
selected with `format`; ordinary writes use rdflib's corresponding serializer.

Each value has authoritative canonical `epics:lexical` text, plus derived convenience
triples where applicable. Groups also have ordered `epics:elements`. Access uses
`epics:ReadOnly`, `epics:Writable`, or `epics:ConditionallyWritable`. Readers rebuild
values from lexical text and require exactly one document, unambiguous structural
predicates, and well-formed ordered lists. Cycles and excessive node expansion are
rejected. Lexical cosmetics, diagnostics, and source metadata are canonicalized or
omitted as described in the [JSON guide](json.md).

Nondefault declarations for Object_Name, Object_Type, and Object_Identifier use
`epics:headerMetadata`, a dictionary whose keys retain the canonical property names.
Its entries retain access, restrictions, readability, and comments without duplicating
the header values.

For joining application graphs, choose a persistent document base and refer to the
object/property IRIs from an external 223P model. No unverified terms from the draft
BACnet Annex YY vocabulary are emitted. The project vocabulary can be extended with
confirmed external term mappings after their authoritative definitions are available.

The [ontology](../ns/epics.ttl), [SHACL shapes](../ns/shapes.ttl), and
[generated vocabulary reference](vocabulary.md) describe the representation.
SHACL validation is a development check; it is not a runtime dependency. The shapes
constrain document identity, object headers, property access, and lexical values;
the codec additionally checks list order and model invariants.

The w3id namespace and schema identifiers identify the intended published artifacts.
Their redirects still require an external w3id registration and a deployed hosting
URL; a local docs build does not establish those redirects.
