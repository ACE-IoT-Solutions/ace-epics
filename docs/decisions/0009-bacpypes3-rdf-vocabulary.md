# Prefer the upstream BACnet RDF vocabulary

Status: accepted.

ASHRAE 135.1 Clause 4 describes EPICS declarations; BACpypes3 supplies an RDF
representation of BACnet objects and values. The RDF codec uses the released
BACpypes3 0.0.110 conventions under `http://data.ashrae.org/bacnet/` for established
concepts and reserves `https://w3id.org/ace-epics#` for EPICS-specific extensions.

Turtle binds these namespaces as `bacnet:` and `ace-epics:`. Object identities,
containment, known property predicates, and supported value encodings use the
upstream vocabulary. Declaration order, access flags, restrictions, comments,
unspecified values, and unresolved syntax retain extension metadata so that the
native/JSON/YAML/RDF cycle remains semantically exact.

Unknown names must not masquerade as official BACnet terms. Generic syntax is not
sufficient evidence for a constructed BACnet datatype or CHOICE; use supported
property metadata where possible and keep unresolved concepts explicitly in the
extension namespace. Interoperability tests use the actual pinned BACpypes3 release
as their oracle rather than relying solely on self-round-trips.

Future upstream additions require a mapping review and migration tests before a
project extension is replaced. Do not declare OWL equivalence solely because two
terms have similar names. This keeps project-owned concepts identifiable and
allows deliberate migration to future official models.
