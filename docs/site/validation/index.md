# Validation

Clause 5 validation compares EPICS capability claims and the test database. Checks
cover BIBBs, service and object support bits, object and property lists, property
access, revisions, and value restrictions.

BACnet 135 knowledge is supplied through a pluggable provider. Checks that require
unavailable knowledge must report skipped results. See the
[BIBB data guide](bibb-knowledge.md) and [knowledge maintenance guide](knowledge.md).
