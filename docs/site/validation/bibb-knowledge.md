# BIBB knowledge

`knowledge/data/bibbs.json` records the service directions and local object types
required by Annex K of ASHRAE 135-2024. Its 153 definitions cover every BIBB in the
DS, AE, SCHED, T, and DM families, plus the NM-RC-B prerequisite of DM-DAP-B.
The revision field identifies the edition's Protocol_Revision 30 snapshot; it
is not a claim that every BIBB existed at every earlier revision.

Each definition carries its Annex K clause. Service entries use normalized names
and independent `initiate` and `execute` flags: the suffix A or B does not determine
a service's direction. `requires_bibbs` records mandatory prerequisites, whose
requirements must be considered transitively.

Alternatives are separate from unconditional requirements:

- `service_alternatives` requires at least one service entry from each group.
- `bibb_alternatives` requires at least one BIBB from each group.
- `object_type_alternatives` requires at least one local object type from each group.

`conditional_requirements` contains a structured condition and the requirements
that apply when it is true. Conditions cover revision thresholds, requested
notification format, alarm acknowledgement, recipient configuration, and restore
file availability. Unknown device capabilities do not justify treating the
conditional requirement as unconditional. For example, DS-COV-A requires receiving
confirmed notifications only when its subscription can request that format;
DM-BR-B requires CreateObject execution when restore files may be absent.

Object types in `object_types` belong to the claiming device. An A device's ability
to read, configure, or create a remote object does not require a local instance of
that type. Empty service or object lists can therefore be valid. DS-VSI-B and the
time-series import/export BIBBs define functionality without an explicit required
application-service table.

The data retains historical deprecated BIBBs and notes the interpreted mismatched
cross-reference in K.1.40. It records identifiers and interpreted requirements;
the licensed standard and verbatim extractions remain outside committed files.
The BIBB table covers the five Clause 5 cross-checks, rather than every functional
conformance requirement, such as presentation formats and minimum list capacities.
