# Standard compatibility

Native syntax targets ANSI/ASHRAE Standard 135.1-2025 Clause 4. The twenty static
consistency checks implement Clause 5(a)–(r), splitting item (i) into three checks.
The read-only query facade supports the facts consumed by Clauses 7.1 and 7.2.

Knowledge tables are sourced from ASHRAE 135-2024 (Protocol_Revision 30).
Object-type and service enumerations and exact bit counts have verified history
for revisions 14–30. Fifteen object-type property tables provide verified complete snapshots
for revisions 14–30, reconstructed against official addenda. Historical snapshots
reverse verified property, access, datatype, and range changes. Canonical datatype
and property-name aliases retain their original source spellings as metadata.
Runtime event/fault constraints are retained as evidence and are outside static
EPICS validation; the validator does not simulate BACnet algorithms.

BIBB coverage includes DS, AE, SCHED, T, and DM, with one supporting NM definition.
Requirements depending on implementation features or service parameters absent
from the EPICS are reported as skipped. A zero-error report can still contain
skipped checks; it is not a statement of product certification.

Consult [knowledge coverage](../validation/knowledge.md) and the
[conformance matrix](conformance.md) for precise evidence. Layout, keyword case,
source metadata, and lexical value hints are excluded from semantic round-trip
identity. Comments attached to property entries remain document data.
