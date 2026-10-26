# Validation

Clause 5 validation compares EPICS capability claims and the test database. Checks
cover BIBBs, service and object support bits, object and property lists, property
access, revisions, and value restrictions.

BACnet 135 knowledge is supplied through a pluggable provider. Checks that require
unavailable knowledge must report skipped results. See the
[BIBB data guide](bibb-knowledge.md) and [knowledge maintenance guide](knowledge.md).

Object-property rules report `partial` when they process available object definitions
but cannot check some objects or facts. `checked_objects` lists objects processed
using available definitions; `skipped_objects` lists objects with unavailable facts.
An object can appear in both lists when only some of its conditions or bounds are
known. Located skipped diagnostics explain the remaining gaps. A rule with no
available definitions reports `skipped`; any error still makes the outcome `fail`,
with coverage information retained. `pass` means no check was skipped.

JSON, text, and Markdown reports include this scope information. Partial and skipped
outcomes do not themselves change the exit code; inspect them before treating a
report as complete conformance evidence.
