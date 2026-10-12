# Preserve object header property metadata

Status: accepted.

Clause 4.5.10 places object-identifier, object-name, and object-type first in every object. These lines still carry property access flags, restrictions, comments, and the library's unreadable extension marker. A writable object-name is a meaningful declaration; an invalid writable object-type must survive parsing so validation can report it.

`TestObject.header_metadata` stores nondefault `PropertyMetadata` under the three canonical header names. The identifier, name, and object type remain the sole source of their values. This prevents stale duplicate value nodes while retaining declarations through every serialization format. Missing metadata means readable access with no restrictions, comment, or unreadable marker. Empty metadata entries are discarded during validation; unrelated keys are rejected. Proprietary objects can attach metadata to their three headers without adding a fourth property.

The native writer derives each header value and appends the preserved metadata. Validation and query APIs apply that metadata to their synthesized header properties.
