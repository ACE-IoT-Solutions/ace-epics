# Choosing an interchange format

Use native EPICS for ASHRAE 135.1 test tools, JSON for exact tagged value trees and
schema validation, YAML for editing, and RDF/Turtle for graph queries and joins.
All codecs share the document model and preserve semantic values and declaration
order. Their round-trip guarantee excludes source metadata and diagnostics.

JSON has no additional runtime dependency. Install `ace-epics[yaml]` or
`ace-epics[rdf]` for the corresponding codec. Tagged tree mode retains lexical
value metadata; text and RDF lexical mode canonicalize that metadata.

Use each codec's `parse` function when input may be malformed. It returns a shared
`ParseResult` with a document only when one can actually be recovered, plus all
diagnostics. `loads` returns a document and raises `EpicsError` by default; disabling
`raise_on_error` permits a recovered document with findings, while an unrecoverable
input still raises. See ADR 0007 for the contract and its testing rationale.
