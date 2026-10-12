# D7.1.1: Represent non-readable properties

Accepted. Clause 7.1.1 needs a distinction between a listed property and a property accessible through ReadProperty. Native EPICS defines no such marker.

`PropertyEntry.not_readable` defaults to false. Structured codecs and callers may set it. The native writer emits the extension comment `-- @not-readable`; the native parser recognizes that exact comment marker while retaining other comment content. The marker is metadata and does not replace the property's R/W/C access declaration.
