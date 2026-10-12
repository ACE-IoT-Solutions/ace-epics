# Conformance matrix

Generated from `tests/conformance/matrix.yaml`; do not edit this page directly.

This matrix records implementation and test traceability. Planned entries
are unfinished work, and implemented entries do not imply product certification.

## Status counts

| Status | Count |
|---|---:|
| implemented | 369 |

## Clause counts

| Clause | Count |
|---|---:|
| 4.1 | 22 |
| 4.2 | 17 |
| 4.3 | 13 |
| 4.4 | 43 |
| 4.4(a) | 1 |
| 4.4(b) | 1 |
| 4.4(c) | 1 |
| 4.4(d) | 1 |
| 4.4(e) | 1 |
| 4.4(f) | 1 |
| 4.4(g) | 1 |
| 4.4(h) | 1 |
| 4.4(i) | 1 |
| 4.4(j) | 1 |
| 4.4(k) | 1 |
| 4.4(l) | 1 |
| 4.4(m) | 1 |
| 4.4.1 | 7 |
| 4.4.1(a) | 1 |
| 4.4.1(b) | 1 |
| 4.4.1(c) | 1 |
| 4.4.1(d) | 1 |
| 4.4.2 | 31 |
| 4.5 | 45 |
| 4.5.1 | 4 |
| 4.5.10 | 16 |
| 4.5.2.1 | 5 |
| 4.5.3 | 6 |
| 4.5.4 | 3 |
| 4.5.5 | 26 |
| 4.5.6 | 9 |
| 4.5.7 | 10 |
| 4.5.8 | 20 |
| 4.5.9 | 21 |
| 5 | 33 |
| 5(a) | 1 |
| 5(b) | 1 |
| 5(c) | 1 |
| 5(d) | 1 |
| 5(e) | 1 |
| 5(f) | 1 |
| 5(g) | 1 |
| 5(h) | 1 |
| 5(i) | 3 |
| 5(j) | 1 |
| 5(k) | 1 |
| 5(l) | 1 |
| 5(m) | 1 |
| 5(n) | 1 |
| 5(o) | 1 |
| 5(p) | 1 |
| 5(q) | 1 |
| 5(r) | 1 |
| 6.3.14 | 1 |

## Requirements

| ID | Clause | Rule | Mode | Status | Tests |
|---|---|---|---|---|---|
| R-4.1-CHARSET-0 | 4.1 | Header charset code 0 selects UTF-8 | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip`<br>`tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.1-CHARSET-1 | 4.1 | Header charset code 1 selects Microsoft DBCS | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip`<br>`tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.1-CHARSET-2 | 4.1 | Header charset code 2 selects JIS X 0208 | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip`<br>`tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.1-CHARSET-3 | 4.1 | Header charset code 3 selects UCS-4 | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip`<br>`tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.1-CHARSET-4 | 4.1 | Header charset code 4 selects UCS-2 | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip`<br>`tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.1-CHARSET-5 | 4.1 | Header charset code 5 selects ISO 8859-1 | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip`<br>`tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.1-HEADER | 4.1 | The first line identifies the EPICS stream and charset digit | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_seeds` |
| R-4.1-WIDTH | 4.1 | Identify one-, two- and four-byte big-endian header patterns | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip` |
| R-4.1-UNKNOWN | 4.1 | Unknown and malformed charset digits produce errors with recovery | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_seeds` |
| R-4.1-INVALID-BYTES | 4.1 | Encoded characters that cannot be decoded produce diagnostic evidence | both | implemented | `tests/unit/encoding/test_encoding.py::test_invalid_encoding_and_conflicting_width` |
| R-4.1-BOM | 4.1 | Accept BOM-prefixed streams with warning; reject strictly | both | implemented | `tests/unit/encoding/test_encoding.py::test_bom_variants` |
| R-4.1-LITTLE-ENDIAN | 4.1 | Accept little-endian wide streams with warning; reject strictly | both | implemented | `tests/unit/encoding/test_encoding.py::test_little_endian_without_bom` |
| R-4.1-HEADER-FORM | 4.1 | Accept noncanonical header case/spacing with warning; reject strictly | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_case_spacing_policy` |
| R-4.2-LINE-ENDINGS | 4.2 | Physical lines use CRLF; bare LF or CR produce mode-dependent diagnostics | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_seeds` |
| R-4.2-WHITESPACE | 4.2 | Space, tab, CR and LF runs separate tokens while retaining physical newlines | both | implemented | `tests/unit/lexer/test_lexer.py::test_comments_whitespace_and_locations` |
| R-4.2-COMMENT | 4.2 | Two dashes outside a string begin a comment through the line boundary | both | implemented | `tests/unit/lexer/test_lexer.py::test_comments_whitespace_and_locations` |
| R-4.2-COMMENT-IN-STRING | 4.2 | Two dashes inside a character string remain literal | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.2-EMPTY-COMMENT | 4.2 | A bare two-dash line is an empty comment | both | implemented | `tests/unit/lexer/test_lexer.py::test_comments_whitespace_and_locations` |
| R-4.2-COMMENT-IN-GROUP | 4.2 | Comments inside multi-line values count as whitespace | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.2-LINE-MODE | 4.2 | Free-text lines retain literals while removing outside-string comments | both | implemented | `tests/unit/lexer/test_lexer.py::test_punctuation_minus_and_raw_line` |
| R-4.2-SIGNATURE | 4.2 | The line following the header is the EPICS signature | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.2-END | 4.2 | The final line is the EPICS end marker | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.2-EMPTY-FILE | 4.2 | Header, signature and end marker form a structurally empty EPICS | both | implemented | `tests/unit/encoding/test_encoding.py::test_structurally_empty_epics_seed` |
| R-4.3-DOUBLE-QUOTE | 4.3 | A double quote opens a string closed by the next double quote | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.3-SINGLE-QUOTE | 4.3 | A single quote opens a string closed by the next apostrophe | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.3-GRAVE-QUOTE | 4.3 | A grave opens a string closed by the next apostrophe | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.3-LINE-TERMINATION | 4.3 | A line boundary terminates an unfinished character string with a warning | both | implemented | `tests/unit/lexer/test_lexer.py::test_unterminated_string_and_single_quote_no_escape` |
| R-4.3-NO-ESCAPES | 4.3 | The closing quote terminates the string without an escape mechanism | both | implemented | `tests/unit/lexer/test_lexer.py::test_unterminated_string_and_single_quote_no_escape` |
| R-4.3-LITERAL-CONTENT | 4.3 | Punctuation, spaces and angle brackets inside strings remain literal | both | implemented | `tests/unit/values/test_seeds.py::test_angles_inside_string_and_inline_comment_boundary` |
| R-4.3-CHARSET | 4.3 | String characters use the declared file encoding | both | implemented | `tests/unit/encoding/test_encoding.py::test_non_ascii_codec_choices` |
| R-4.4-A | 4.4(a) | Keywords are case insensitive | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-B | 4.4(b) | NULL denotes a null value | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-C | 4.4(c) | T/TRUE and F/FALSE denote Boolean values | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-D | 4.4(d) | Integers contain digits with an optional leading minus | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-E | 4.4(e) | Canonical real values contain a decimal point with digits on both sides | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-F | 4.4(f) | Octet strings use X with paired hexadecimal digits inside apostrophe or grave delimiters | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-G | 4.4(g) | Character-string values follow the string grammar | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings`<br>`tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-H | 4.4(h) | Boolean bit strings use brace groups containing Boolean or unspecified bits | both | implemented | `tests/unit/values/test_seeds.py::test_classifiers_and_lexical_preservation` |
| R-4.4-I | 4.4(i) | Enumeration names normalize case and equivalent separators with proprietary numeric suffixes | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-J | 4.4(j) | Dates use parenthesized English names and wildcard fields with an optional weekday | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-K | 4.4(k) | Times contain hour, minute, second and hundredth fields with wildcard support | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-L | 4.4(l) | Object identifiers use a parenthesized type and numeric instance, including proprietary types | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-M | 4.4(m) | Constructed values use nested comma-separated brace groups | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4.1-A | 4.4.1(a) | Application-tagged CHOICE values contain the chosen value without a context tag | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4.1-B | 4.4.1(b) | Context-tagged CHOICE values use a bracketed non-negative tag before the value | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4.1-C | 4.4.1(c) | Lists use comma-separated parenthesis groups, with constructed elements in braces | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4.1-D | 4.4.1(d) | Arrays use comma-separated brace groups, with constructed elements in braces | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4.2-MINIMUM | 4.4.2 | The minimum restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-MAXIMUM | 4.4.2 | The maximum restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-RESOLUTION | 4.4.2 | The resolution restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-MAXIMUM-LENGTH-STRING | 4.4.2 | The maximum length string restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-MAXIMUM-LENGTH-LIST | 4.4.2 | The maximum length list restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-MAXIMUM-LENGTH-ARRAY | 4.4.2 | The maximum length array restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-ALLOWED-VALUES | 4.4.2 | The allowed values restriction is parsed and retains its datatype or list of values | both | implemented | `tests/unit/values/test_seeds.py::test_each_restriction_name` |
| R-4.4.2-PLACEMENT | 4.4.2 | Restrictions follow the default property value | both | implemented | `tests/unit/values/test_seeds.py::test_property_value_restriction_suffix_seeds` |
| R-4.4.2-BRACKETS | 4.4.2 | Restriction statements are enclosed by angle brackets | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-COLON | 4.4.2 | Restriction names and values require a colon in strict mode | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-SEMICOLON | 4.4.2 | Multiple restriction statements use semicolons rather than commas | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-ALLOWED-SPACES | 4.4.2 | Space-separated allowed enumeration and object-type names normalize to hyphenated names | both | implemented | `tests/unit/values/test_seeds.py::test_normative_restriction_seeds` |
| R-4.4.2-CLOSED-NAMES | 4.4.2 | Unknown restriction names are errors in both modes | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-OVERRIDE | 4.4.2 | Explicit property bounds override datatype defaults | both | implemented | `tests/unit/values/test_seeds.py::test_helpers_edge_cases_and_semantic_equality` |
| R-4.4.2-STRING-LITERAL | 4.4.2 | Angle-bracket content inside a string is not parsed as restrictions | both | implemented | `tests/unit/values/test_seeds.py::test_angles_inside_string_and_inline_comment_boundary` |
| R-4.1-SEED-01 | 4.1 | UTF-8 octet header | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip` |
| R-4.1-SEED-02 | 4.1 | Latin-1 octet header | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip` |
| R-4.1-SEED-03 | 4.1 | Big-endian two-octet header | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip` |
| R-4.1-SEED-04 | 4.1 | Big-endian four-octet header | both | implemented | `tests/unit/encoding/test_encoding.py::test_standard_headers_roundtrip` |
| R-4.1-SEED-05 | 4.1 | Unknown charset digit | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_seeds` |
| R-4.1-SEED-06 | 4.1 | Missing or nonnumeric header digit | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_seeds` |
| R-4.1-SEED-07 | 4.1 | Bare LF header terminator | both | implemented | `tests/unit/encoding/test_encoding.py::test_header_seeds` |
| R-4.1-SEED-08 | 4.1 | UTF-8 BOM header | both | implemented | `tests/unit/encoding/test_encoding.py::test_bom_variants` |
| R-4.2-SEED-09 | 4.2 | Structurally empty EPICS file | both | implemented | `tests/codecs/epics/test_reader.py::test_structurally_empty_document_collects_errors` |
| R-4.2-SEED-10 | 4.2 | Missing signature line | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.2-SEED-11 | 4.2 | Missing end-marker line | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.2-SEED-12 | 4.2 | Comment in file body | both | implemented | `tests/unit/lexer/test_lexer.py::test_comments_whitespace_and_locations` |
| R-4.2-SEED-13 | 4.2 | Trailing property comment | both | implemented | `tests/unit/lexer/test_lexer.py::test_comments_whitespace_and_locations` |
| R-4.2-SEED-14 | 4.2 | Dashes inside a string | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.2-SEED-15 | 4.2 | Collapsed space and tab separators | both | implemented | `tests/unit/lexer/test_lexer.py::test_comments_whitespace_and_locations` |
| R-4.3-SEED-16 | 4.3 | Double-quoted embedded apostrophe | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.3-SEED-17 | 4.3 | Single-quoted embedded double quote | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.3-SEED-18 | 4.3 | Grave-opened apostrophe-closed string | both | implemented | `tests/unit/lexer/test_lexer.py::test_strings` |
| R-4.3-SEED-19 | 4.3 | Line-terminated unfinished string | both | implemented | `tests/unit/lexer/test_lexer.py::test_unterminated_string_and_single_quote_no_escape` |
| R-4.3-SEED-20 | 4.3 | Apostrophe terminates without escaping | both | implemented | `tests/unit/lexer/test_lexer.py::test_unterminated_string_and_single_quote_no_escape` |
| R-4.4-SEED-21 | 4.4 | Case-insensitive null | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-22 | 4.4 | Case-insensitive Boolean forms | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-23 | 4.4 | Positive and negative integer | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-24 | 4.4 | Negative zero integer | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-25 | 4.4 | Canonical real decimal forms | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-26 | 4.4 | Noncanonical leading/trailing decimal point | both | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-SEED-27 | 4.4 | Paired hexadecimal octets and odd-length diagnostics | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-SEED-28 | 4.4 | Boolean bit-string forms | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-29 | 4.4 | Unspecified bit value | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-30 | 4.4 | Mixed group is not syntactically a Boolean bit string | both | implemented | `tests/unit/values/test_seeds.py::test_classifiers_and_lexical_preservation` |
| R-4.4-SEED-31 | 4.4 | Equivalent enumeration separators | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-32 | 4.4 | Proprietary enumeration numeric suffix | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-33 | 4.4 | Proprietary name without numeric suffix | both | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-SEED-34 | 4.4 | Date with weekday | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-35 | 4.4 | Date with wildcard day | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-36 | 4.4 | Date without weekday | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-37 | 4.4 | Unclosed date | both | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-SEED-38 | 4.4 | Canonical time fields | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-39 | 4.4 | Wildcard time fields | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-40 | 4.4 | Standard object identifier | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-41 | 4.4 | Proprietary object identifier | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-SEED-42 | 4.4 | Missing object-identifier comma | both | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4.1-SEED-43 | 4.4.1 | Nested constructed values | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4.1-SEED-44 | 4.4.1 | Integer parenthesis list | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4.1-SEED-45 | 4.4.1 | List of constructed values | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4.1-SEED-46 | 4.4.1 | Context-tagged integer | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4.1-SEED-47 | 4.4.1 | Application-tagged chosen integer | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4.1-SEED-48 | 4.4.1 | Unclosed constructed group | both | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4.2-SEED-49 | 4.4.2 | Property real value with numeric restrictions | both | implemented | `tests/unit/values/test_seeds.py::test_property_value_restriction_suffix_seeds` |
| R-4.4.2-SEED-50 | 4.4.2 | Character-string maximum-length restriction | both | implemented | `tests/unit/values/test_seeds.py::test_property_value_restriction_suffix_seeds` |
| R-4.4.2-SEED-51 | 4.4.2 | Allowed enumeration values | both | implemented | `tests/unit/values/test_seeds.py::test_property_value_restriction_suffix_seeds` |
| R-4.4.2-SEED-52 | 4.4.2 | Allowed object types with space-separated names | both | implemented | `tests/unit/values/test_seeds.py::test_property_value_restriction_suffix_seeds` |
| R-4.4.2-SEED-53 | 4.4.2 | Invalid comma-separated restriction statements | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-SEED-54 | 4.4.2 | Missing restriction colon | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-SEED-55 | 4.4.2 | Unknown restriction name | both | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4.2-SEED-56 | 4.4.2 | Restriction-shaped string literal | both | implemented | `tests/unit/values/test_seeds.py::test_angles_inside_string_and_inline_comment_boundary` |
| R-4.4-ANNEX-E04-COLON | 4.4 | Default restrictions without colons are repaired | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4-ANNEX-E04-JOINED-LENGTH | 4.4 | A joined restriction name and array length is split | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4-ANNEX-E04-EXPONENT | 4.4 | Scientific real notation is accepted with diagnostics | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-ANNEX-E04-BARE-DATE | 4.4 | Bare restriction dates are accepted with diagnostics | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_restriction_errors` |
| R-4.4-ANNEX-E09-NAME | 4.4 | Capitalized and space-separated object types normalize consistently | both | implemented | `tests/unit/values/test_seeds.py::test_classifiers_and_lexical_preservation` |
| R-4.4-ANNEX-E10-ENUM | 4.4 | Case and dash/underscore enumeration spellings normalize consistently | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-ANNEX-E12-DELIMITERS | 4.4 | Generic syntactic groups retain parentheses or braces without imposing a datatype | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E13-DATETIME | 4.4 | Date-time groups accept either delimiter and bare nested dates | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E14-TIME | 4.4 | Short times and single-digit fractions are accepted with diagnostics | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-ANNEX-E15-RANGE | 4.4 | Date ranges coexist with dates in generic calendar groups | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E16-CHOICE | 4.4 | Syntax preserves untagged timestamp choices for later datatype interpretation | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E17-NAMED-BITS | 4.4 | Named-bit collections remain generic groups | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E18-EMPTY | 4.4 | Empty constructed-value positions remain explicit | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E19-OCTETS | 4.4 | Odd-length hex strings are padded with diagnostics | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-ANNEX-E20-TRAILING | 4.4 | Trailing group commas produce mode-dependent diagnostics | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-ANNEX-E20-MISSING | 4.4 | Missing group commas are repaired with diagnostics | lenient-only | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-ANNEX-E20-CLOSERS | 4.4 | Mismatched and stray closers retain recovery trees with errors | both | implemented | `tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.4-ANNEX-E21-COMMENTS | 4.4 | Comments inside multiline values are whitespace | both | implemented | `tests/unit/values/test_seeds.py::test_annex_notation_inventory` |
| R-4.4-ANNEX-E23-BOOLEAN | 4.4 | Abbreviated Boolean bits remain valid syntax | both | implemented | `tests/unit/values/test_seeds.py::test_normative_value_seeds` |
| R-4.4-ROUNDTRIP | 4.4 | Canonical render/parse retains meaning across 2000 generated value trees | both | implemented | `tests/unit/values/test_properties.py::test_render_parse_roundtrip` |
| R-4.4-FUZZ | 4.4 | Lexer and value parser never raise across 10000 arbitrary Unicode inputs | both | implemented | `tests/unit/values/test_properties.py::test_arbitrary_input_never_raises` |
| R-4.5-CAPABILITY | 4.5 | Capability sections | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_native_generated_semantic_roundtrip` |
| C5-01 | 5(a) | BIBB-required object types are marked supported | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-01]`<br>`tests/validation/test_clause5.py::test_bibb_local_object_requirements[C5-01]`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-01]` |
| C5-02 | 5(b) | BIBB-required object instances exist | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-02]`<br>`tests/validation/test_clause5.py::test_bibb_local_object_requirements[C5-02]`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-02]` |
| C5-03 | 5(c) | BIBB-required object bits are set | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-03]`<br>`tests/validation/test_clause5.py::test_bibb_local_object_requirements[C5-03]`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-03]` |
| C5-04 | 5(d) | BIBB-required service directions are supported | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-04]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-04]` |
| C5-05 | 5(e) | BIBB-required executed service bits are set | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-05]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-05]` |
| C5-06 | 5(f) | Object support section matches Device supported bits | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-06]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-06]` |
| C5-07 | 5(g) | Supported object types have database instances | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-07]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-08 | 5(h) | Object_List matches the test database | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-08]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-09 | 5(i) | All required object properties are present | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-09]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-09]` |
| C5-10 | 5(i) | Properties exist at the declared protocol revision | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-10]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-10]` |
| C5-11 | 5(i) | Conditional property requirements are satisfied | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-11]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-11]` |
| C5-12 | 5(j) | Required writable properties are marked W or C | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-12]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-12]` |
| C5-13 | 5(k) | Services bit string has the revision's exact length | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-13]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-13]` |
| C5-14 | 5(l) | Object-types bit string has the revision's exact length | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-14]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-14]` |
| C5-15 | 5(m) | Deprecated/removed properties obey the revision boundary | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-15]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-15]` |
| C5-16 | 5(n) | Property_List matches explicitly listed properties | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-16]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-17 | 5(o) | Receiving segmentation accepts more than one segment | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-17]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-18 | 5(p) | Required read-only properties are marked R | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-18]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-18]` |
| C5-19 | 5(q) | Specified values lie within standard bounds | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-19]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-19]` |
| C5-20 | 5(r) | Declared restrictions respect allowed and minimum bounds | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[C5-20]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_missing_knowledge_is_skipped[C5-20]` |
| S-01 | 4.5.10 | Object identifiers are unique | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[S-01]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| S-02 | 5 | Exactly one Device object exists | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[S-02]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| S-03 | 4.5.9 | Fail times are finite and non-negative | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[S-03]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| S-04 | 4.4.2 | Restriction datatypes match their values | both | implemented | `tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule[S-04]`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| R-4.5.1-HEADING-1 | 4.5.1 | Recognize and canonically emit Vendor Name | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.1-HEADING-2 | 4.5.1 | Recognize and canonically emit Product Name | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.1-HEADING-3 | 4.5.1 | Recognize and canonically emit Product Model Number | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.1-HEADING-4 | 4.5.1 | Recognize and canonically emit Product Description | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.2.1-HEADING-5 | 4.5.2.1 | Recognize and canonically emit BIBBs Supported | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.3-HEADING-6 | 4.5.3 | Recognize and canonically emit BACnet Standard Application Services Supported | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.4-HEADING-7 | 4.5.4 | Recognize and canonically emit Standard Object Types Supported | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.5-HEADING-8 | 4.5.5 | Recognize and canonically emit Data Link Layer Option | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.6-HEADING-9 | 4.5.6 | Recognize and canonically emit Character Sets Supported | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.7-HEADING-10 | 4.5.7 | Recognize and canonically emit Special Functionality | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.8-HEADING-11 | 4.5.8 | Recognize and canonically emit Default Property Value Restrictions | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.9-HEADING-12 | 4.5.9 | Recognize and canonically emit Fail Times | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.10-HEADING-13 | 4.5.10 | Recognize and canonically emit List of Objects in Test Device | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.5.5-LITERAL-1 | 4.5.5 | Data link literal ISO 8802-3, 10BASE5 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-2 | 4.5.5 | Data link literal ISO 8802-3, 10BASE2 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-3 | 4.5.5 | Data link literal ISO 8802-3, 10BASET | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-4 | 4.5.5 | Data link literal ISO 8802-3, fiber | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-5 | 4.5.5 | Data link literal ARCNET, coax star | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-6 | 4.5.5 | Data link literal ARCNET, coax bus | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-7 | 4.5.5 | Data link literal ARCNET, twisted pair star | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-8 | 4.5.5 | Data link literal ARCNET, twisted pair bus | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-9 | 4.5.5 | Data link literal ARCNET, fiber star | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-10 | 4.5.5 | Data link literal ARCNET, twisted pair, EIA-485, Baud rate(s): 9600, 19200 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-11 | 4.5.5 | Data link literal MS/TP manager. Baud rate(s): 9600, 19200, 38400 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-12 | 4.5.5 | Data link literal MS/TP subordinate. Baud rate(s): 9600 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-13 | 4.5.5 | Data link literal Point-To-Point. EIA 232, Baud rate(s): 9600 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-14 | 4.5.5 | Data link literal Point-To-Point. Modem, Baud rate(s): 9600, 19200 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-15 | 4.5.5 | Data link literal Point-To-Point. Modem, Autobaud range: 9600 to 57600 | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-16 | 4.5.5 | Data link literal BACnet/IP, 'DIX' Ethernet | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-17 | 4.5.5 | Data link literal BACnet/IP, Other | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-18 | 4.5.5 | Data link literal BACnet/IPv6, 'DIX' Ethernet | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-19 | 4.5.5 | Data link literal BACnet/SC | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-20 | 4.5.5 | Data link literal Zigbee | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-21 | 4.5.5 | Data link literal Other | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.5-LITERAL-22 | 4.5.5 | Data link literal Other custom transport | both | implemented | `tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union`<br>`tests/codecs/epics/test_sections.py::test_native_every_data_link_literal` |
| R-4.5.6-LITERAL-1 | 4.5.6 | Supported character-set literal ISO 10646 (UTF-8) | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5.6-LITERAL-2 | 4.5.6 | Supported character-set literal IBM/Microsoft DBCS | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5.6-LITERAL-3 | 4.5.6 | Supported character-set literal JIS X 0208 | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5.6-LITERAL-4 | 4.5.6 | Supported character-set literal ISO 8859-1 | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5.6-LITERAL-5 | 4.5.6 | Supported character-set literal ISO 10646 (UCS-4) | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5.6-LITERAL-6 | 4.5.6 | Supported character-set literal ISO 10646 (UCS2) | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5.7-KEYWORD-MAX_APDU_SIZE | 4.5.7 | Special functionality keyword Maximum APDU size in octets | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-SEGMENTED_REQUESTS_WINDOW | 4.5.7 | Special functionality keyword Segmented Requests Supported, window size | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-SEGMENTED_RESPONSES_WINDOW | 4.5.7 | Special functionality keyword Segmented Responses Supported, window size | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-ROUTER | 4.5.7 | Special functionality keyword Router | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-BACNET_IP_BBMD | 4.5.7 | Special functionality keyword BACnet/IP BBMD | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-BACNET_IPV6_BBMD | 4.5.7 | Special functionality keyword BACnet/IPV6 BBMD | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-BACNET_SC_HUB | 4.5.7 | Special functionality keyword BACnet/SC Hub | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.7-KEYWORD-BACNET_SC_DIRECT_CONNECT | 4.5.7 | Special functionality keyword BACnet/SC Direct Connect | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5.8-DEFAULT-UNSIGNED_INTEGER-MAXIMUM | 4.5.8 | unsigned-integer permits maximum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-UNSIGNED_INTEGER-MINIMUM | 4.5.8 | unsigned-integer permits minimum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-SIGNED_INTEGER-MAXIMUM | 4.5.8 | signed-integer permits maximum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-SIGNED_INTEGER-MINIMUM | 4.5.8 | signed-integer permits minimum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-REAL-MAXIMUM | 4.5.8 | real permits maximum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-REAL-MINIMUM | 4.5.8 | real permits minimum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-REAL-RESOLUTION | 4.5.8 | real permits resolution | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-DOUBLE-MAXIMUM | 4.5.8 | double permits maximum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-DOUBLE-MINIMUM | 4.5.8 | double permits minimum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-DOUBLE-RESOLUTION | 4.5.8 | double permits resolution | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-DATE-MAXIMUM | 4.5.8 | date permits maximum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-DATE-MINIMUM | 4.5.8 | date permits minimum | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-OCTET_STRING-MAXIMUM_LENGTH_STRING | 4.5.8 | octet-string permits maximum length string | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-CHARACTER_STRING-MAXIMUM_LENGTH_STRING | 4.5.8 | character-string permits maximum length string | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-LIST-MAXIMUM_LENGTH_LIST | 4.5.8 | list permits maximum length list | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.8-DEFAULT-VARIABLE_LENGTH_ARRAY-MAXIMUM_LENGTH_ARRAY | 4.5.8 | variable-length-array permits maximum length array | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5.9-KEYWORD-NOTIFICATION_FAIL_TIME | 4.5.9 | Timer keyword Notification Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-INTERNAL_PROCESSING_FAIL_TIME | 4.5.9 | Timer keyword Internal Processing Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-MINIMUM_ON_OFF_TIME | 4.5.9 | Timer keyword Minimum ON/OFF Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-SCHEDULE_EVALUATION_FAIL_TIME | 4.5.9 | Timer keyword Schedule Evaluation Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-EXTERNAL_COMMAND_FAIL_TIME | 4.5.9 | Timer keyword External Command Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-PROGRAM_OBJECT_STATE_CHANGE_FAIL_TIME | 4.5.9 | Timer keyword Program Object State Change Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-ACKNOWLEDGEMENT_FAIL_TIME | 4.5.9 | Timer keyword Acknowledgement Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-SUBORDINATE_PROXY_CONFIRM_INTERVAL | 4.5.9 | Timer keyword Subordinate Proxy Confirm Interval | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-UNCONFIRMED_RESPONSE_FAIL_TIME | 4.5.9 | Timer keyword Unconfirmed Response Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-CHANNEL_WRITE_FAIL_TIME | 4.5.9 | Timer keyword Channel Write Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-AUTO_NEGOTIATION_FAIL_TIME | 4.5.9 | Timer keyword Auto Negotiation Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-ACTIVATE_CHANGES_FAIL_TIME | 4.5.9 | Timer keyword Activate Changes Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-KEYWORD-FOREIGN_DEVICE_REGISTRATION_FAIL_TIME | 4.5.9 | Timer keyword Foreign Device Registration Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-6.3.14-KEYWORD-AUDIT_NOTIFICATION_FORWARDER_FAIL_TIME | 6.3.14 | Timer keyword Audit Notification Forwarder Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-ALIAS-ACKNOWLEDGEMENT_FAIL_TIME | 4.5.9 | Timer spelling alias Acknowledgment Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_clause_six_aliases` |
| R-4.5.9-ALIAS-AUTO_NEGOTIATION_FAIL_TIME | 4.5.9 | Timer spelling alias Autonegotiation Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_clause_six_aliases` |
| R-4.5.9-ALIAS-MINIMUM_ON_OFF_TIME | 4.5.9 | Timer spelling alias Minimum ON/OFF Fail Time | both | implemented | `tests/unit/model/test_timers.py::test_clause_six_aliases` |
| R-4.5-ORDER | 4.5 | Printed section order is canonical; strict deviation is diagnosed | both | implemented | `tests/codecs/epics/test_sections.py::test_section_order_completeness_duplicates_and_database_last` |
| R-4.5-COMPLETENESS | 4.5 | Missing template sections are diagnosed by mode | both | implemented | `tests/codecs/epics/test_sections.py::test_section_order_completeness_duplicates_and_database_last` |
| R-4.5-DUPLICATES | 4.5 | Duplicate sections report an error | both | implemented | `tests/codecs/epics/test_sections.py::test_section_order_completeness_duplicates_and_database_last` |
| R-4.5.10-DATABASE-LAST | 4.5.10 | The test database is the final section | both | implemented | `tests/codecs/epics/test_sections.py::test_section_order_completeness_duplicates_and_database_last` |
| R-4.5.2.1-BIBB-EMPTY | 4.5.2.1 | Empty BIBB list is legal | both | implemented | `tests/codecs/epics/test_writer.py::test_native_generated_semantic_roundtrip` |
| R-4.5.2.1-BIBB-LAYOUT | 4.5.2.1 | One BIBB per line; lenient multiple words produce warning | both | implemented | `tests/codecs/epics/test_reader.py::test_corpus_snapshots_and_mode_diagnostics` |
| R-4.5.2.1-BIBB-NAME | 4.5.2.1 | Unknown BIBB name shape is advisory | both | implemented | `tests/unit/model/test_conformance.py::test_default_flags_and_bibb_warnings` |
| R-4.5.2.1-BIBB-DUPLICATE | 4.5.2.1 | Duplicate BIBB declarations are advisory | both | implemented | `tests/unit/model/test_document.py::test_duplicate_identifiers_rejected_and_declarations_warn` |
| R-4.5.3-SERVICE-INITIATE | 4.5.3 | Initiate direction is accepted | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms` |
| R-4.5.3-SERVICE-EXECUTE | 4.5.3 | Execute direction is accepted | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms` |
| R-4.5.3-SERVICE-BOTH | 4.5.3 | Both service directions accepted in either order | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms` |
| R-4.5.3-SERVICE-INVALID | 4.5.3 | Missing and unknown service flags are errors | both | implemented | `tests/codecs/epics/test_sections.py::test_native_rejects_missing_and_unknown_service_flags` |
| R-4.5.3-SERVICE-NAMES | 4.5.3 | CamelCase service names normalize without a knowledge provider | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms` |
| R-4.5.4-OBJECT-FLAGS | 4.5.4 | Createable, Creatable and Deleteable with optional or reversed flags | both | implemented | `tests/codecs/epics/test_sections.py::test_native_object_type_flag_forms` |
| R-4.5.4-OBJECT-FLAGS-INVALID | 4.5.4 | Unknown trailing object flags are errors | both | implemented | `tests/codecs/epics/test_sections.py::test_invalid_object_flags_and_data_link_ranges` |
| R-4.5.5-BAUD-PARAMETERS | 4.5.5 | Required baud lists, ARCNET restrictions, modem-only ordered autobaud | both | implemented | `tests/unit/model/test_datalink.py::test_invalid_parameters` |
| R-4.5.5-BAUD-9600 | 4.5.5 | Missing 9600 MS/TP support is advisory | both | implemented | `tests/unit/model/test_datalink.py::test_mstp_9600_advisory` |
| R-4.5.5-BAUD-K | 4.5.5 | Lenient k suffix expands to integer baud rates | both | implemented | `tests/codecs/epics/test_reader.py::test_leniency_promotes_to_strict_error` |
| R-4.5.6-CHARSET-ALIASES | 4.5.6 | UCS-2, UCS2 and trademarked DBCS forms alias by case and whitespace | both | implemented | `tests/unit/model/test_general.py::test_character_set_alias` |
| R-4.5.6-CHARSET-UNKNOWN | 4.5.6 | Unknown character-set entries remain in source raw data | both | implemented | `tests/codecs/epics/test_reader.py::test_unknown_character_set_retained_in_source_raw` |
| R-4.5.7-WINDOW-ADVISORY | 4.5.7 | Window range outside1..127 is advisory | both | implemented | `tests/unit/model/test_conformance.py::test_special_numbers_and_advisory_windows` |
| R-4.5.8-DEFAULT-EMPTY | 4.5.8 | Empty datatype defaults are legal | both | implemented | `tests/codecs/epics/test_writer.py::test_native_generated_semantic_roundtrip` |
| R-4.5.8-DEFAULT-EXTENSION | 4.5.8 | Extra time defaults are preserved with unknown datatype warning | both | implemented | `tests/codecs/epics/test_sections.py::test_extension_defaults_allowed_values_and_unknown_timers` |
| R-4.5.8-DEFAULT-MERGE | 4.5.8 | Defined instance restriction fields override defaults independently | both | implemented | `tests/unit/model/test_restrictions.py::test_merge_preserves_datatypes_and_only_overrides_defined_fields` |
| R-4.5.9-TIMER-COMPLETENESS | 4.5.9 | Each of thirteen template timers must be present in strict input | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5.9-TIMER-INTEGER | 4.5.9 | Integer timer seconds are leniently coerced with warning | both | implemented | `tests/codecs/epics/test_reader.py::test_leniency_promotes_to_strict_error` |
| R-4.5.9-TIMER-EXTRA | 4.5.9 | Unknown timer values remain in extra | both | implemented | `tests/codecs/epics/test_sections.py::test_extension_defaults_allowed_values_and_unknown_timers` |
| R-4.5.10-HEADER-ORDER | 4.5.10 | First object properties are identifier, name, type | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.5.10-TYPE-MATCH | 4.5.10 | Object-type must match the identifier type | both | implemented | `tests/unit/model/test_database.py::test_mismatch_duplicates_and_repeated_headers` |
| R-4.5.10-PROPRIETARY | 4.5.10 | Proprietary object type is >=128 and only three headers are permitted | both | implemented | `tests/unit/model/test_database.py::test_proprietary_header_only` |
| R-4.5.10-INSTANCE | 4.5.10 | Object instance integer is bounded0..4194303 | both | implemented | `tests/unit/model/test_database.py::test_invalid_identifiers` |
| R-4.5.10-MISSING-INSTANCE | 4.5.10 | Missing instance produces error and malformed object is skipped; ADR0007 recovery policy | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.5.10-PROPERTY-UNIQUE | 4.5.10 | Duplicate properties and repeated object headers are invalid | both | implemented | `tests/unit/model/test_database.py::test_mismatch_duplicates_and_repeated_headers` |
| R-4.5.10-PROPERTY-COMMENT | 4.5.10 | Trailing comments and not-readable extension are preserved | both | implemented | `tests/codecs/epics/test_reader.py::test_multiline_after_comment_missing_value_and_marker_order` |
| R-4.5.10-HEADER-METADATA | 4.5.10 | Header access restrictions comments and not-readable marker survive round trips | both | implemented | `tests/codecs/epics/test_writer.py::test_header_metadata_roundtrip` |
| R-4.5.10-VALUE-RECOVERY | 4.5.10 | Unbalanced values recover before the next property | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.5.10-MARKER-ORDER | 4.5.10 | W/C markers accepted before or after restrictions; implicit R | both | implemented | `tests/codecs/epics/test_reader.py::test_multiline_after_comment_missing_value_and_marker_order` |
| R-4.5.10-EXPLICIT-R | 4.5.10 | Explicit R marker is accepted only with mode-dependent diagnostic | both | implemented | `tests/codecs/epics/test_reader.py::test_leniency_promotes_to_strict_error` |
| R-4.5.10-VALUE-EXTENT | 4.5.10 | Comment-only property line accepts a value on the next line | both | implemented | `tests/codecs/epics/test_reader.py::test_multiline_after_comment_missing_value_and_marker_order` |
| R-4.5.10-IDENTIFIER-UNIQUE | 4.5.10 | Duplicate object identifiers are errors | both | implemented | `tests/unit/model/test_document.py::test_duplicate_identifiers_rejected_and_declarations_warn` |
| R-4.1-NATIVE-CRLF | 4.1 | Canonical native output usesCRLF, charset-selected binary path and streams | both | implemented | `tests/codecs/epics/test_writer.py::test_full_roundtrip_and_byte_stability` |
| R-4.4.1-NATIVE-GROUP-WRAP | 4.4.1 | Long constructed values wrap by element and preserving style keeps lexical hints | both | implemented | `tests/codecs/epics/test_writer.py::test_preserving_hints_and_group_wrapping` |
| R-4.3-NATIVE-REPRESENTABILITY | 4.3 | Unrepresentable character strings fail explicitly | both | implemented | `tests/codecs/epics/test_writer.py::test_writer_rejects_unrepresentable_strings` |
| R-4.5-NATIVE-ROUNDTRIP | 4.5 | 2000representable generated documents are strict-clean and byte stable | both | implemented | `tests/codecs/epics/test_writer.py::test_native_generated_semantic_roundtrip` |
| R-4.4.2-MODEL-MINIMUM | 4.4.2 | Typed model restriction minimum | both | implemented | `tests/unit/model/test_restrictions.py::test_merge_preserves_datatypes_and_only_overrides_defined_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.4.2-MODEL-MAXIMUM | 4.4.2 | Typed model restriction maximum | both | implemented | `tests/unit/model/test_restrictions.py::test_merge_preserves_datatypes_and_only_overrides_defined_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.4.2-MODEL-RESOLUTION | 4.4.2 | Typed model restriction resolution | both | implemented | `tests/unit/model/test_restrictions.py::test_merge_preserves_datatypes_and_only_overrides_defined_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.4.2-MODEL-MAXIMUM_LENGTH_STRING | 4.4.2 | Typed model restriction maximum length string | both | implemented | `tests/unit/model/test_restrictions.py::test_lengths_and_named_allowed_values`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.4.2-MODEL-MAXIMUM_LENGTH_LIST | 4.4.2 | Typed model restriction maximum length list | both | implemented | `tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.4.2-MODEL-MAXIMUM_LENGTH_ARRAY | 4.4.2 | Typed model restriction maximum length array | both | implemented | `tests/unit/model/test_restrictions.py::test_lengths_and_named_allowed_values`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.4.2-MODEL-ALLOWED_VALUES | 4.4.2 | Typed model restriction allowed values | both | implemented | `tests/unit/model/test_restrictions.py::test_lengths_and_named_allowed_values`<br>`tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| C5-SEED-01 | 5 | BIBB DS-RP-B claimed but Device.Protocol_Services_Supported lacks ReadProperty bit -> C5-05 error. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule` |
| C5-SEED-02 | 5 | BIBB requiring an Analog Input object type but AI not in "Standard Object Types Supported" -> C5-01. | both | implemented | `tests/validation/test_clause5.py::test_bibb_local_object_requirements` |
| C5-SEED-03 | 5 | Same BIBB, AI listed but no AI object in test DB -> C5-02 (and C5-07). | both | implemented | `tests/validation/test_clause5.py::test_bibb_local_object_requirements` |
| C5-SEED-04 | 5 | Protocol_Object_Types_Supported has AI bit unset while section lists AI -> C5-06 (and C5-03). | both | implemented | `tests/validation/test_digest_seeds.py::test_seed04_unset_analog_input_bit_with_retained_section` |
| C5-SEED-05 | 5 | Services section lacks Execute for ReadProperty while BIBB B side claimed -> C5-04. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-06 | 5 | Services section has ReadProperty with only Initiate where BIBB is B-side -> C5-04. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed06_initiate_only_b_side_service` |
| C5-SEED-07 | 5 | Object_List contains (AV,3) not in test DB -> C5-08. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed07_extra_object_list_entry` |
| C5-SEED-08 | 5 | Test DB has (BV,1) not in Object_List -> C5-08. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-09 | 5 | Proprietary object type (>=128) present in DB but missing in Object_List -> C5-08. | both | implemented | `tests/validation/test_preconditions.py::test_object_list_includes_proprietary_identifiers` |
| C5-SEED-10 | 5 | File type supported, no File object, annotated dynamic -> passes (warning-level note) per C5-07 exception; without annotation -> inferred warning/error. | both | implemented | `tests/validation/test_clause5.py::test_dynamic_file_exception_is_warning` |
| C5-SEED-11 | 5 | AI object missing Present_Value -> C5-09. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-12 | 5 | Protocol_Revision 5 and object has Property_List (introduced later) -> C5-10. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed12_revision_five_property_list_introduction` |
| C5-SEED-13 | 5 | Conditionally required property missing (e.g. Event_Detection_Enable set but Notification_Class missing) -> C5-11 (example inferred). | both | implemented | `tests/validation/test_conditions.py::test_object_condition_groups_and_known_property_values` |
| C5-SEED-14 | 5 | Present_Value of AO marked read-only in EPICS (must be writable) -> C5-12. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-15 | 5 | Device.Description-like required read-only property marked W -> C5-18. | both | implemented | `tests/validation/test_header_metadata.py::test_required_writable_and_read_only_headers` |
| C5-SEED-16 | 5 | Protocol_Services_Supported bitstring of wrong length for Protocol_Revision 14 -> C5-13; too long -> C5-13; correct -> pass. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed16_revision_fourteen_service_vector_length` |
| C5-SEED-17 | 5 | Protocol_Object_Types_Supported length mismatch -> C5-14. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation`<br>`tests/validation/test_clause5.py::test_independent_baseline_passes_every_rule` |
| C5-SEED-18 | 5 | Protocol_Revision 12 with a property deprecated at 12 present at 13+ -> C5-15 boundary (inferred) tests. | both | implemented | `tests/validation/test_clause5.py::test_deprecation_boundary_and_unspecified_range` |
| C5-SEED-19 | 5 | Protocol_Revision 15, Property_List missing a present property -> C5-16; Property_List contains Object_Name -> C5-16 failure; correct list with different order -> pass; Protocol_Revision 13 with no Property_List -> rule skipped. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed19_revision_fifteen_property_list_membership_and_order`<br>`tests/validation/test_clause5.py::test_property_list_old_revision_not_applicable` |
| C5-SEED-20 | 5 | Protocol_Revision absent -> C5-16 skipped; C5-10 conservative behaviour noted. | both | implemented | `tests/validation/test_clause5.py::test_property_list_old_revision_not_applicable` |
| C5-SEED-21 | 5 | Segmentation_Supported = SEGMENTED_BOTH with Max_Segments_Accepted = 1 -> C5-17 error; = 2 -> pass; SEGMENTED_TRANSMIT with 1 -> pass; NO_SEGMENTATION -> pass. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed21_segmentation_without_receiving`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-22 | 5 | Priority_Array-style value outside standard range (e.g. Present_Value of Multi-state input = 0, min is 1) -> C5-19. | both | implemented | `tests/validation/test_conditions.py::test_dynamic_standard_bounds_and_constructed_element_ranges` |
| C5-SEED-23 | 5 | "?" value in a ranged property -> no C5-19 failure. | both | implemented | `tests/validation/test_preconditions.py::test_null_is_not_an_unspecified_bit_or_numeric_value` |
| C5-SEED-24 | 5 | Restricted range for an Analog Output Present_Value exceeding allowed standard range -> C5-20. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-25 | 5 | Restricted range smaller than the minimal range mandated by the standard (e.g. restricting Max_Segments_Accepted below minimum, inferred example) -> C5-20. | both | implemented | `tests/validation/test_clause5.py::test_minimum_required_range_and_conditional_access` |
| C5-SEED-26 | 5 | Per-property override missing but datatype default (4.5.8) used for C5-20 resolution -> default applied. | both | implemented | `tests/validation/test_digest_seeds.py::test_seed26_datatype_default_restrictions_are_validated` |
| C5-SEED-27 | 5 | Timer section missing Internal Processing Fail Time -> completeness warning; timer value negative or non-real -> error (inferred). | both | implemented | `tests/validation/test_digest_seeds.py::test_seed27_missing_internal_processing_timer_warns` |
| C5-SEED-28 | 5 | Timer list includes Audit Notification Forwarder Fail Time -> accepted. | both | implemented | `tests/unit/model/test_timers.py::test_all_fourteen_timer_fields`<br>`tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| C5-SEED-29 | 5 | Property marked "conditionally writable" must count as writable for C5-12 and as non-read-only for C5-18. | both | implemented | `tests/validation/test_clause5.py::test_minimum_required_range_and_conditional_access`<br>`tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-30 | 5 | Duplicate object identifiers in test DB -> extra rule (inferred) mapping to C5-08. | both | implemented | `tests/validation/test_clause5.py::test_rule_fails_on_targeted_mutation` |
| C5-SEED-31 | 5 | Device object absent from test DB -> everything cascading from Device properties yields a single root-cause error (inferred; Device property reads are prerequisites). | both | implemented | `tests/validation/test_digest_seeds.py::test_seed31_absent_device_has_one_root_error` |
| C5-SEED-32 | 5 | Object type names in section differ only by case/spacing/hyphen from enum names -> parser normalisation (inferred). | both | implemented | `tests/unit/model/test_names.py::test_normalization`<br>`tests/unit/model/test_conformance.py::test_creation_aliases` |
| R-4.5-SEED-01 | 4.5 | V: `Vendor Name: "Ace IoT Solutions"` -> general.vendor_name = `Ace IoT Solutions`. | both | implemented | `tests/codecs/epics/test_sections.py::test_general_string_seeds` |
| R-4.5-SEED-02 | 4.5 | V: `vendor name: 'ACME'` (lowercase keyword, single quotes) -> same as 1 (4.4a, 4.3). | both | implemented | `tests/codecs/epics/test_sections.py::test_general_string_seeds` |
| R-4.5-SEED-03 | 4.5 | V: `Product Description: "He said 'hi'"` -> value contains single quotes (4.3). | both | implemented | `tests/codecs/epics/test_sections.py::test_general_string_seeds` |
| R-4.5-SEED-04 | 4.5 | V: `Product Name: 'say "x"'` -> value contains double quotes. | both | implemented | `tests/codecs/epics/test_sections.py::test_general_string_seeds` |
| R-4.5-SEED-05 | 4.5 | V: unterminated `Product Name: "abc` (no closing quote) -> string ends at end of line = `abc` (4.3). | both | implemented | `tests/codecs/epics/test_sections.py::test_general_string_seeds` |
| R-4.5-SEED-06 | 4.5 | V: `BIBBs Supported:` with `{` `}` and nothing between -> empty list. | both | implemented | `tests/codecs/epics/test_sections.py::test_bibb_empty_case_alias_and_missing_braces` |
| R-4.5-SEED-07 | 4.5 | V: `BIBBS Supported:` `{ DS-RP-B DM-DDB-A }` on separate lines -> ["DS-RP-B","DM-DDB-A"], heading case-insensitive. | both | implemented | `tests/codecs/epics/test_sections.py::test_bibb_empty_case_alias_and_missing_braces` |
| R-4.5-SEED-08 | 4.5 | I (strict): `BIBBs Supported: DS-RP-B` without braces -> error. | both | implemented | `tests/codecs/epics/test_sections.py::test_bibb_empty_case_alias_and_missing_braces` |
| R-4.5-SEED-09 | 4.5 | V: `Who-Is Initiate Execute` -> initiate True, execute True. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms`<br>`tests/unit/model/test_conformance.py::test_services` |
| R-4.5-SEED-10 | 4.5 | V: `Who-Has Execute` -> execute only. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms`<br>`tests/unit/model/test_conformance.py::test_services` |
| R-4.5-SEED-11 | 4.5 | V: `I-Have Initiate ` (trailing space) -> initiate only. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_service_flag_forms`<br>`tests/unit/model/test_conformance.py::test_services` |
| R-4.5-SEED-12 | 4.5 | I: `ReadProperty` with no flag -> error (flag required). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_rejects_missing_and_unknown_service_flags` |
| R-4.5-SEED-13 | 4.5 | I: `ReadProperty Both` -> error (unknown flag). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_rejects_missing_and_unknown_service_flags` |
| R-4.5-SEED-14 | 4.5 | V: `Analog Value Createable Deleteable` -> createable and deleteable True. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_object_type_flag_forms` |
| R-4.5-SEED-15 | 4.5 | V: `Device` -> both False. I: `Analog Input Creatable` -> error (spelling `Createable`). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_object_type_flag_forms`<br>`tests/unit/model/test_conformance.py::test_creation_aliases` |
| R-4.5-SEED-16 | 4.5 | V: `ISO 8802-3, 10BASET` ; `BACnet/SC` ; `Zigbee` ; `Other`. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_data_link_literal`<br>`tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union` |
| R-4.5-SEED-17 | 4.5 | V: `MS/TP manager. Baud rate(s): 9600, 19200, 38400` -> baud_rates [9600,19200,38400] (inferred format). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_data_link_literal`<br>`tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union` |
| R-4.5-SEED-18 | 4.5 | V: `Point-To-Point. Modem, Autobaud range: 9600 to 57600` -> autobaud 9600..57600. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_data_link_literal`<br>`tests/unit/model/test_datalink.py::test_every_literal_roundtrips_regex_and_union` |
| R-4.5-SEED-19 | 4.5 | I: `MS/TP manager.` with no baud rates -> error (shall specify baud rates). | both | implemented | `tests/codecs/epics/test_reader.py::test_corpus_snapshots_and_mode_diagnostics` |
| R-4.5-SEED-20 | 4.5 | I: `ARCNET, fiber bus` -> not in the standard's list. | both | implemented | `tests/unit/model/test_datalink.py::test_invalid_parameters` |
| R-4.5-SEED-21 | 4.5 | V: `ISO 10646 (UTF-8)` ; I (strict): `ISO 10646 (UTF-16)`. | both | implemented | `tests/unit/model/test_general.py::test_unsupported_character_set`<br>`tests/codecs/epics/test_sections.py::test_native_every_character_set_literal` |
| R-4.5-SEED-22 | 4.5 | V: `Maximum APDU size in octets: 1476` -> 1476; I: `Maximum APDU size in octets: 1476.0` -> error (integer required). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword`<br>`tests/codecs/epics/test_sections.py::test_native_invalid_parameter_rules` |
| R-4.5-SEED-23 | 4.5 | V: `Segmented Requests Supported, window size: 4`; V: `Router`; V: `BACnet/IPV6 BBMD` and `bacnet/ipv6 bbmd` equal. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_special_keyword` |
| R-4.5-SEED-24 | 4.5 | V: `real: <minimum: 0.0; maximum: 100.0; resolution: 0.1>` under `Default Property Value Restrictions`. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction` |
| R-4.5-SEED-25 | 4.5 | I: `real: <minimum: .5; maximum: 1.0>` -> `.5` invalid real (4.4e); V: `signed-integer: <minimum: -10; maximum: 10>`. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/values/test_seeds.py::test_deviation_matrix` |
| R-4.5-SEED-26 | 4.5 | V: `octet-string: <maximum length string: 255>`; I (strict): `octet-string: <maximum length list: 5>` -> wrong restriction for type. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/unit/model/test_restrictions.py::test_default_restrictions_warn_without_rejecting` |
| R-4.5-SEED-27 | 4.5 | V: `Fail Times:` block with `Notification Fail Time: 10.0` ; I: `Notification Fail Time: 10` (integer where Real required; lenient parsers may coerce). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_timer_keyword`<br>`tests/codecs/epics/test_reader.py::test_leniency_promotes_to_strict_error` |
| R-4.5-SEED-28 | 4.5 | I: Fail Times missing `Channel Write Fail Time` -> error per "for each timer" (or warn, see open question 15). | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_timer_keyword` |
| R-4.5-SEED-29 | 4.5 | V: object with identifier `(analog-value, 6)`, name `"AV6"`, type `analog-value`, `present-value: 23.4 W` -> access W. | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness` |
| R-4.5-SEED-30 | 4.5 | V: `present-value: 12.3 C -- Writable when Out_Of_Service is TRUE` -> access C, comment captured, not part of value. | both | implemented | `tests/codecs/epics/test_reader.py::test_multiline_after_comment_missing_value_and_marker_order` |
| R-4.5-SEED-31 | 4.5 | V: `present-value: ?` -> Unknown; V: `status-flags: {F,F,?,F}`. | both | implemented | `tests/codecs/epics/test_reader.py::test_corpus_snapshots_and_mode_diagnostics` |
| R-4.5-SEED-32 | 4.5 | I: object whose `object-type: analog-input` conflicts with identifier `(analog-value, 6)` -> error. | both | implemented | `tests/unit/model/test_database.py::test_mismatch_duplicates_and_repeated_headers` |
| R-4.5-SEED-33 | 4.5 | I: object where `object-name` appears before `object-identifier` -> error (order fixed: id, name, type). | both | implemented | `tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
| R-4.5-SEED-34 | 4.5 | V: proprietary object with exactly three properties and `(proprietary 700, 1)`; I: same plus `present-value: 1` -> error (only three properties allowed). | both | implemented | `tests/unit/model/test_database.py::test_proprietary_header_only`<br>`tests/codecs/epics/test_reader.py::test_corpus_snapshots_and_mode_diagnostics` |
| R-4.5-SEED-35 | 4.5 | V: `present-value: 13.4 <minimum: 0.0; maximum: 20.0; resolution: 0.1>` -> value 13.4, restrictions parsed. | both | implemented | `tests/codecs/epics/test_reader.py::test_corpus_snapshots_and_mode_diagnostics` |
| R-4.5-SEED-36 | 4.5 | V: `units: milliamperes <allowed values: milliamperes, amperes>` -> allowed_values list of 2. | both | implemented | `tests/codecs/epics/test_sections.py::test_extension_defaults_allowed_values_and_unknown_timers` |
| R-4.5-SEED-37 | 4.5 | V: `description: "this is a description" <maximum length string: 30>`. | both | implemented | `tests/codecs/epics/test_sections.py::test_native_every_default_datatype_and_restriction`<br>`tests/codecs/epics/test_writer.py::test_header_metadata_roundtrip` |
| R-4.5-SEED-38 | 4.5 | V: `Present_Value: 1.0` equals `present-value: 1.0` (underscore/dash/case equivalence, inferred for property names). | both | implemented | `tests/unit/model/test_database.py::test_property_helpers_and_non_readable_marker` |
| R-4.5-SEED-39 | 4.5 | V: `-- comment line` between sections and trailing `-- x` on lines ignored; I: `"a -- b"` inside string is not a comment. | both | implemented | `tests/codecs/epics/test_sections.py::test_general_string_seeds`<br>`tests/codecs/epics/test_reader.py::test_multiline_after_comment_missing_value_and_marker_order` |
| R-4.5-SEED-40 | 4.5 | V: file with `PICS 0` header, signature, sections, `End of BACnet Protocol Implementation Conformance Statement`; I: missing end line -> error. | both | implemented | `tests/codecs/epics/test_reader.py::test_full_exact_model_and_strictness`<br>`tests/codecs/epics/test_reader.py::test_explicit_error_recovery` |
