# RDF and Turtle

The RDF codec uses the BACnet vocabulary implemented by
[BACpypes3 0.0.110](https://pypi.org/project/bacpypes3/0.0.110/) wherever a concept has
an established mapping. EPICS-specific information uses a separate extension
namespace. These bindings make ownership explicit:

```turtle
@prefix bacnet: <http://data.ashrae.org/bacnet/> .
@prefix ace-epics: <https://w3id.org/ace-epics#> .
```

## Standard concepts and extensions

| Concept | Representation |
| --- | --- |
| Device identity | `bacnet:Device`, `bacnet:device-instance` |
| Device objects | `bacnet:contains` |
| Object headers | `bacnet:object-identifier`, `bacnet:object-type`, `bacnet:object-name` |
| Known BACnet properties | Direct predicates such as `bacnet:present-value` |
| Enumerated values | BACpypes3 class-qualified IRIs such as `bacnet:ObjectType.analog-output` |
| Scalar and pattern values | BACpypes3-compatible literals, datatypes, and `bacnet:Null` |
| EPICS document and capability declarations | `ace-epics:Document` and declaration records |
| Access, readability, restrictions, comments | `ace-epics:Property` declaration metadata |
| Unspecified values and ambiguous syntax | `ace-epics:` value records with canonical lexical text |
| Declaration and value order | RDF lists linked by `ace-epics:` predicates |
| Unknown object types and property names | Explicit IRIs in the `ace-epics:` namespace |

Standard property values can be queried directly from their object subjects. The
extension records preserve the information needed to reconstruct the EPICS document;
a scalar BACnet value alone cannot retain an EPICS access flag or restriction.
`ace-epics:Object` marks this declaration metadata. It does not claim to be an
upstream generic BACnet object class.

Syntax can be insufficient to identify a BACnet datatype. A generic group might be
an array, named bits, a sequence, or a CHOICE. The codec uses known property datatypes
where it can make a supported mapping and retains the original EPICS syntax in its
extension records. It does not invent official terms for unresolved concepts.

## Serialize and query

```python
from ace_epics.codecs import rdf

text = rdf.dumps(document, base_iri="urn:example:epics", deterministic=True)
restored = rdf.loads(text)
assert restored == document

graph = rdf.to_graph(document, base_iri="urn:example:epics", deterministic=True)
```

The document links to a separate Device endpoint through
`ace-epics:describesDevice`. The endpoint IRI is `<base>/device/<instance>` and its
contained object IRIs are `<endpoint>/<object-type>,<instance>`, following
BACpypes3's object-IRI convention relative to a chosen endpoint. This keeps the
Device endpoint separate from its contained Device-type BACnet object. BACpypes3's
default endpoint URIs use `bacnet://<instance>`; our explicit document base provides
scope for independent EPICS descriptions.

Objects and property declarations get stable IRIs under the document base. Ordered
collections use RDF lists; deterministic mode uses stable skolem IRIs for auxiliary
nodes. Choose a persistent `base_iri` when joining another application graph to
these objects.

```sparql
PREFIX bacnet: <http://data.ashrae.org/bacnet/>
SELECT ?device ?object ?name WHERE {
  ?device a bacnet:Device ; bacnet:contains ?object .
  ?object bacnet:object-name ?name .
}
```

The reader requires an EPICS document and its declaration metadata for a complete
round-trip. A BACpypes3 device graph by itself does not supply the EPICS capability
sections, access declarations, restrictions, and source ordering. Extra application
triples do not become invented EPICS declarations.

## Compatibility and future migration

Development interoperability tests pin BACpypes3 0.0.110 as the current reference.
They exercise the released encoder/decoder and graph conventions. This reference
is a test dependency; the RDF runtime extra remains RDFlib. When adopting a newer
upstream model, update the reference version, review the mapping, and run the
interoperability and complete cross-format round-trip tests.

The reference release has four independently reproduced RDF defects: its generic
Double encoder dispatch, object-identifier datatype identity check, numeric-position
bit-string decoder, and ObjectProxy getter. Strict expected-failure tests isolate
those upstream defects; separate passing tests verify our encodings, supported
decoders, prepared queries, and object-IRI conventions. A future upstream fix will
turn the corresponding expected failure into a failing test so it can be reviewed.

Every `ace-epics:` term is a project extension, not an official ASHRAE definition.
When upstream defines an equivalent concept, migrate the mapping deliberately;
namespace ownership alone does not assert semantic equivalence. The
[extension vocabulary](vocabulary.md), [ontology](../ns/epics.ttl), and
[SHACL shapes](../ns/shapes.ttl) document these records. SHACL constraints are
project validation rules, not a claim that BACpypes3 publishes those shapes.

The w3id namespace and schema identifiers identify the intended published artifacts.
Their redirects require external registration and configured hosting. A local docs
build does not establish those redirects.
