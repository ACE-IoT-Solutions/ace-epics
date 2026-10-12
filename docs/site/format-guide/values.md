# Values

EPICS values are syntax trees. Parsing does not consult BACnet datatype tables;
property interpretation and consistency validation happen later. Each frozen
Pydantic node has a `kind` discriminator for JSON and YAML serialization.

```python
from ace_epics.values import parse_value, render, as_bitstring

value, diagnostics = parse_value("{T, F, ?}")
assert as_bitstring(value) == [True, False, None]
assert render(value) == "{TRUE, FALSE, ?}"
```

`parse_value()` accepts text or lexer tokens and returns one node plus diagnostics.
`ValueParser.position` provides a cursor for property parsers that need to read
following access markers or restrictions. Canonical rendering normalizes cosmetic
spelling. `render(value, Preserving)` keeps real text, Boolean abbreviations, string
quote style, time precision and recorded trailing commas. Node equality compares
meaning while ignoring these cosmetic differences.

## Null

`NULL` produces `NullValue`. Keywords are case insensitive.

## Boolean

`TRUE`, `FALSE`, `T` and `F` produce `BooleanValue`. The `short` field records the
single-letter form. Canonical writing uses full words.

## Integer

`42` and `-17` produce `IntegerValue`. Integers have arbitrary Python precision;
protocol-specific ranges belong to validation. Unsupported leading plus signs and
non-finite number spellings produce `V-NUMBER`.

## Real

`1.25` produces `RealValue` with a `Decimal` value and original text. Scientific
notation, a missing leading digit (`.5`) and a missing fractional digit (`5.`) are
accepted with `V-REAL-NOTATION` in lenient mode and errors in strict mode.

## Octet string

`X'00FF'` produces `OctetStringValue` containing bytes. Grave-delimited octets also
work. Odd hex lengths produce `V-ODD-OCTETS` and are padded with a leading zero in
lenient mode; strict mode reports an error. Invalid hex characters produce
`V-OCTETS`. JSON represents the bytes as uppercase hexadecimal text.

## Character string

`"zone, east"`, `'say "hello"'` and grave-opened, apostrophe-closed strings produce
`CharacterStringValue`. Strings have no escape notation. A physical line boundary
terminates an unfinished string with `L-UNTERMINATED-STRING`, including strict mode.
Comments and punctuation inside a string retain their literal meaning. A writer
raises `ValueError` when a string cannot be represented using either permitted
closing quote or contains a line break.

## Enumeration

`NO_FAULT_DETECTED` produces `EnumeratedValue` with canonical name
`no-fault-detected`. `NamedToken` preserves source spelling and treats case, spaces,
underscores and hyphens as equivalent. `proprietary-object-type-700` and
`proprietary 700` record a proprietary number. A proprietary name without its
numeric suffix produces `V-PROPRIETARY`.

## Date

`(Monday, 24-January-2000)` produces `DateValue`. Omitting the weekday means it is
unspecified; `*` wildcard fields produce `WildcardValue`. Full English month and
weekday names are canonical. Abbreviations produce `V-DATE-ABBREVIATION`; numeric
month notation produces `V-DATE-NAME`. Unknown names and invalid days produce
`V-DATE` or `V-DATE-RANGE`. Bare dates are accepted for date-time grouping and with
`V-BARE-DATE` when used as standalone values. Canonical writing adds parentheses.

## Time

`02:05:44.00` produces `TimeValue`. Wildcards may appear in any field, for example
`16:54:*.*`. Lenient short forms `08:00`, `08:00:00` and `08:00:00.2` produce
`V-TIME-PRECISION`; strict mode reports an error. The `precision` field is `-1`
for hours/minutes, `0` for whole seconds and `1` or `2` for fractional precision.
One fractional digit denotes tenths of a second. Canonical writing supplies all
four fields. Out-of-range numeric fields produce `V-TIME-RANGE`.

## Date range

`(5-September-2001)-(10-June-2002)` produces `DateRangeValue`. A range may appear
inside either group delimiter. A non-date endpoint produces `V-DATE-RANGE`.

## Object identifier

`(analog-input, 56)` produces `ObjectIdentifierValue`. The object type is a
`NamedToken`, or an integer for `(proprietary 700, 1)`. Space-separated names such
as `(analog input, 56)` normalize to the same object type. Generic parenthesis
pairs with an enumeration and an integer also have this syntactic shape;
a later datatype interpreter can resolve list ambiguity.

## Context tag

`[2] 5` produces `ContextTaggedValue`. Nested groups or any other node can follow
the tag. Invalid tags and missing closing brackets produce `V-TAG`.

## Group

`{1, {2, 3}}` and `(1, 2, 3)` produce `GroupValue`. Groups represent arrays, lists,
constructed values, bit strings and named-bit collections without assigning a
BACnet datatype. Empty groups are allowed. Comments and line breaks inside groups
are whitespace. The `as_bitstring`, `as_datetime`, `as_date`, `as_object_identifier`
and `as_list_of` helpers recognize shapes without external knowledge.

Missing commas produce `V-MISSING-COMMA` and trailing commas produce
`V-TRAILING-COMMA`: warnings in lenient mode, errors in strict mode. Mismatched or
stray closers produce `V-CLOSER`; unclosed groups produce `V-UNBALANCED`. Both modes
retain a recoverable tree alongside these errors. Excessive nesting produces
`V-DEPTH`.

## Empty element

The gaps in `{,0,,1}` produce `EmptyElement`. A final empty element is written with
an additional comma so its position survives parsing.

## Unspecified

`?` produces `UnspecifiedValue`. It is valid as a complete property value and as a
bit-string element. Within other groups it produces `V-NESTED-UNSPECIFIED`: a
lenient warning or strict error.

## Wildcard

A standalone `*` produces `WildcardValue`. Dates and times also use this node for
individual wildcard fields.

## Restrictions

```python
from ace_epics.values import parse_restrictions, render_restrictions

limits, diagnostics = parse_restrictions("<minimum: 0; maximum: 100>")
assert render_restrictions(limits) == "<minimum: 0; maximum: 100>"
```

The seven names are `minimum`, `maximum`, `resolution`, `maximum length string`,
`maximum length list`, `maximum length array` and `allowed values`. Statements use
semicolons; allowed values use commas. Numeric/date bounds retain value nodes;
length limits are non-negative integers. Space-separated allowed enumeration names
normalize to hyphenated names. `merged_over()` combines explicit limits with defaults.

Missing colons (`R-COLON`), bare dates (`R-BARE-DATE`) and joined name/length notation
such as `maximum length array10` are tolerated in lenient mode. Unknown names
(`R-NAME`), duplicate statements (`R-DUPLICATE`), invalid lengths (`R-LENGTH`),
missing values (`R-VALUE`), missing angle brackets (`R-BRACKETS`) and commas used as
statement separators (`R-SEPARATOR`) produce errors.

Unexpected value tokens produce `V-TOKEN`, missing values produce `V-MISSING` and
unexpected suffixes produce `V-TRAILING`. Oversized or otherwise invalid input that
cannot form a node produces `V-INVALID` with an unspecified recovery value.
