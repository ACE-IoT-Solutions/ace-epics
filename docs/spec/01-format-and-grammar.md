# EPICS File Format: Lexical Structure and Value Grammar

Source: ANSI/ASHRAE Standard 135.1-2025 (BACnet Method of Test), Clause 4 intro and 4.1 through 4.4 (plus Clause 3 terminology).
This digest paraphrases the standard. Items marked **(inferred)** are not stated in the text. Sections 4.5 and later (section layout, default restrictions in 4.5.8) are out of scope and not seen.

## 0. Terminology and framing (Clause 3, Clause 4 intro)

- EPICS = electronic protocol implementation conformance statement; TPI = "text protocol information"; IUT = implementation under test; TD = testing device. (3.2)
- "Test database" = a database of BACnet functionality/objects created by reading the contents of an EPICS. (3.1) The restriction examples in 4.4.2 are phrased as "test database" content.
- Clause 4 intro: an EPICS file expresses a device's BACnet PICS as standardized text; it is both human and machine readable. File extension shall be `.TPI`. Content is editable text lines ending in CR/LF pairs (X'0D', X'0A'). An EPICS shall accompany any device tested per this standard.
- 3.2 lists BNF as an abbreviation, but Clause 4 contains no formal BNF; the grammar below is derived.

## 1. Character encoding (4.1)

### 1.1 Three encoding groups
- Octet streams: one octet per character. Multi-byte lead-in schemes (Microsoft DBCS, JIS C 6226) are still "octet streams" because certain octet values signal that the following octet combines with the lead octet.
- Double-octet streams: each pair of octets is one character, leading (first) octet is most significant (big-endian). Example: ISO 10646 UCS-2.
- Quad-octet streams: each 4-octet tuple is one character, leading octet most significant (big-endian). Example: ISO 10646 UCS-4.

### 1.2 Header and Table 4-1
The file begins with a header whose text starts with `PICS #`, where `#` is a numeral giving the character set code. The header both identifies the file as an EPICS and identifies the encoding.

| code | character set |
|---|---|
| 0 | ISO 10646 (UTF-8) |
| 1 | IBM/Microsoft DBCS |
| 2 | JIS X 0208 |
| 3 | ISO 10646 (UCS-4) |
| 4 | ISO 10646 (UCS-2) |
| 5 | ISO 8859-1 |

The number is the character-set code, not a version or count. Codes outside 0-5 are not defined.

### 1.3 Detection by octet pattern
Detection examines the start of the file. The header line is `PICS n` followed by CR LF (8 characters).

- **Octet stream**: examine first 8 octets. Example given (with "ANSI X3.4" encoding): `50 49 43 53 20 30 0D 0A` = "PICS 0" CR LF.
- **Double octet stream**: examine first 16 octets. Example (UCS-2): `00 50 00 49 00 43 00 53 00 20 00 34 00 0D 00 0A` = "PICS 4" CR LF.
- **Quad octet stream**: examine first 32 octets. Example (UCS-4): `00 00 00 50 00 00 00 49 00 00 00 43 00 00 00 53 00 00 00 20 00 00 00 33 00 00 00 0D 00 00 00 0A` = "PICS 3" CR LF.

Detection recipe (inferred from the examples): if bytes 0..7 equal `PICS d\r\n` for some digit, octet stream; elif the 16 octets match `00 'P' 00 'I' 00 'C' 00 'S' 00 ' ' 00 d 00 CR 00 LF`, double octet; elif the 32 octets match the same pattern with three zero bytes before each character, quad octet. Little-endian UTF-16/UTF-32 is not described and therefore not supported by the text.

### 1.4 Notes and gaps
- No BOM is mentioned anywhere in 4.1. The standard's detection scheme makes a BOM unnecessary; a leading BOM would break the stated octet patterns. Handling is an implementer decision (see Section 8).
- The text does not require the digit in the header to agree with the detected width, but the examples pair code 0 with 8-octet, 4 with 16-octet and 3 with 32-octet. Mapping (inferred): 0, 1, 2, 5 = octet streams; 4 = double octet; 3 = quad octet. The text does not state which codes belong to which group except by the examples (UTF-8/ANSI X3.4 = octet, UCS-2 = double, UCS-4 = quad) and the group descriptions (DBCS and JIS are octet streams).
- The example for octet streams cites "ANSI X3.4" (ASCII), which is not a Table 4-1 entry; presumably ASCII-compatible and covered by code 0 (inferred).

## 2. Structure of EPICS files (4.2)

- **Lines**: text lines terminated by CR LF (X'0D0A'), encoded in the stream's width (4.2). The symbol `↵` in the standard denotes CR LF. A "character" means one symbol in 1, 2 or 4 octets per the header; space is X'20', X'0020' or X'00000020'. The standard shows all characters in single-octet form.
- **White space** (outside character strings): tab X'09', space X'20', CR X'0D', LF X'0A'. Any run of 1 or more white space characters is equivalent to one white space character. Note CR and LF count as white space, so line breaks are insignificant outside strings and comments (inferred consequence).
- **Comments** (outside character strings): two dashes `--` start a comment that ends at the next CR LF (the end of that line). Comments count as white space and may be inserted freely. Inside a character string `--` is not a comment.
- **Header line**: `PICS n` + CR LF as the first line (4.1).
- **Signature line**: first line following the header shall be the literal text:
  `BACnet Protocol Implementation Conformance Statement` followed by CR LF. It identifies the EPICS format.
- **Body**: lines that define sections (see 4.5, out of scope) and the implementation data follow the signature line.
- **End marker**: file ends with a line containing the literal text:
  `End of BACnet Protocol Implementation Conformance Statement` followed by CR LF.
- **Case sensitivity**: 4.4(a) says keywords are case insensitive. Whether the header, signature and end lines are subject to that is not stated.
- **Not in 4.1-4.4**: section delimiters, section order, per-section END markers, continuation lines. Only the file-level start/end literals are defined here. Continuation is only implied by the fact that line breaks are white space.

## 3. Character strings (4.3)

- A string opens with a double quote (X'22'), single quote (X'27') or accent grave (X'60').
- Opened with double quote: closes at the next double quote, or end of line.
- Opened with single quote or accent grave: closes at the next single quote (X'27'), or end of line. (Surprise: an accent-grave-opened string is closed by a single quote, not by another grave.)
- No escape mechanism exists. To embed a single quote or grave, use the double-quote form; to embed a double quote, use the single-quote or grave form. A string cannot contain both a double quote and a single quote.
- An unterminated string ends silently at end of line (not an error by the text).
- Character set of the contents is the file's encoding from the header (4.1/4.2). No other character-set rules are given.
- Strings cannot span lines because end of line terminates them.

## 4. Notational rules for parameter values (4.4)

Rules (a) to (m). Within each section, parameters are expressed in these forms.

| Rule | Type | Syntax | Examples from text |
|---|---|---|---|
| (a) | keywords | case insensitive (A-Z equals a-z) | n/a |
| (b) | Null | the string `NULL` | `NULL` |
| (c) | Boolean | `T` or `TRUE` for true; `F` or `FALSE` for false | `T`, `FALSE` |
| (d) | Integer (and by inference Unsigned) | string of digits, optional leading `-` | `12345`, `-111` |
| (e) | Real (and by inference Double) | contains a decimal point, which may not be first or last character | `1.23`, `0.02`, `1.0`; invalid `.02` |
| (f) | OctetString | letter `X`, then pairs of hex digits enclosed in single quotes or accent graves | `X'001122'` |
| (g) | CharacterString | one or more characters in double, single or grave quotes per 4.3 | `'text'`, `"text"` (the standard prints two identical forms, a typographic loss of the grave variant) |
| (h) | BitString | list in curly brackets of true/false values; `?` means the bit value does not matter | `{T,T,F}`, `{TRUE, TRUE, FALSE}`, `{T,T,?}` |
| (i) | Enumerated | named values, not numeric | `Object_Type`, `proprietary-object-type-653` |
| (j) | Date | in parentheses; asterisk for any wildcard/unspecified field; omitting day-of-week means unspecified | `(Monday, 24-January-1998)`, `(Monday, *-January-1998)`, `(24-January-1998)` |
| (k) | Time | `hh:mm:ss.xx` (hours, minutes, seconds, hundredths); asterisk for wildcard fields | `2:05:44.00`, `16:54:59.99`, `16:54:*.*` |
| (l) | ObjectIdentifier | in parentheses, object type and instance separated by comma; proprietary type is `proprietary` followed by numeric type value | `(analog-input, 56)`, `(proprietary 700,1)` |
| (m) | Constructed | in curly brackets, elements comma separated; a nested constructed element is also in curly brackets | none given |

Details and consequences:
- (a): hex digits X/x in the octet string prefix are presumably case insensitive too (inferred).
- (b) Null: spelled `NULL`; case insensitive by (a) (inferred).
- (c) Boolean: four spellings; one-letter forms `T`/`F` are also what bit strings use.
- (d) No `+` sign is mentioned. No separate Unsigned rule: Unsigned = digits only with no minus (inferred). No range checking is stated.
- (e) Real: no exponent notation is described; leading minus presumably allowed (inferred). No separate Double rule; same notation (inferred). Neither `1.` nor `.5` is allowed. Special values (INF, NaN) are not mentioned.
- (f) The text's printed "X'2D'" and "X'60'" for the quote characters are cross-references that appear to be errors (single quote is X'27'); treat the opening quote as `'` or the grave. Whether closing must match the opening one is not stated (inferred: grave opens, apostrophe or grave closes is not stated either; see ambiguities). Hex digit count is even by "pairs". The empty octet string `X''` is not discussed.
- (g) See 4.3 for termination.
- (h) `?` is a third value used only in bit strings in this text. Elements separated by commas; whitespace allowed around them (shown with spaces in the second example). Bit order (first element = bit 0) is not stated here (inferred, standard BACnet convention).
- (i) Enumerations: names case insensitive, and underscore and dash are equivalent (so `Object_Type` equals `object-type`). Proprietary values: a name with no whitespace that begins with the word "proprietary" and ends in a non-negative decimal number. Example `proprietary-object-type-653`. Names are enumeration-specific; the lists are not in 4.4.
- (j) Date: format `(DayOfWeek, D-Month-YYYY)`. Day of week is a name (`Monday`), month a name (`January`), day and year numeric. Any field can be `*`. If the weekday and its comma are omitted the weekday is unspecified: `(24-January-1998)`. Whether abbreviations (Mon, Jan), numeric months, or `*` for month in a form like `*-*-*` are accepted is not stated (see ambiguities).
- (k) Time: hour may be one digit (`2:05:44.00`). Four fields `hh:mm:ss.xx`; any field may be `*`; the example shows the seconds and hundredths both wildcarded as `*.*` after `16:54:`. Whether the `.xx` part may be omitted is not stated.
- (l) ObjectIdentifier: type is an enumeration name per (i) (with dashes), then `,`, then instance number. Proprietary uses `proprietary 700` (a space between word and number here, versus the hyphenated form in (i)). Space after the comma is allowed (`(analog-input, 56)` vs `(proprietary 700,1)`).
- (m) Constructed values: braces, comma-separated. Applies to SEQUENCE-like structures. Distinct from bit strings only by content.

## 5. Complex parameter values (4.4.1)

For constructed or CHOICE values, notation tied to the ASN.1 encoding. Rules:
- (a) CHOICE of **application-tagged** values: write just the chosen item's value as in 4.4 (no tag shown).
- (b) CHOICE of **context-tagged** values: write the context tag number in square brackets, then the chosen item's value: `[2] 5` style (inferred example; the text gives no concrete example).
- (c) **List** values (ASN.1 SEQUENCE OF): enclosed in **parentheses**, elements comma separated. A constructed element is enclosed in curly brackets.
- (d) **Array** values: enclosed in **curly brackets**, comma separated. A constructed element is enclosed in curly brackets.
- Consequence: list = `( ... )`, array and constructed = `{ ... }`. Date and ObjectIdentifier also use parentheses, so parentheses are overloaded and need context (the datatype of the property) to disambiguate.
- No rule on how field names are written inside constructed values. Elements are positional (inferred), no names. Optional elements and how they are omitted are not described.
- No explicit syntax for empty list/array in the text (inferred `()` / `{}`).

## 6. Limits on parameter values (4.4.2)

Purpose: tests that write a property then read it back need known restrictions. Restriction statements may appear in the test database.

Restriction names and applicability:

| Name | Applies to | Meaning |
|---|---|---|
| `minimum` | Unsigned, Integer, Real, Double; Date | minimum value; earliest date |
| `maximum` | Unsigned, Integer, Real, Double; Date | maximum value; latest date |
| `resolution` | Real, Double; Time | minimum guaranteed resolution; for Time the minimum resolution in seconds |
| `maximum length string` | CharacterString, OctetString | maximum length |
| `maximum length list` | lists | maximum number of elements guaranteed to fit |
| `maximum length array` | arrays | maximum number of elements |
| `allowed values` | Enumerated; object identifier references | comma-delimited list of supported enumerations; comma-delimited list of allowed object types for properties referencing an external object identifier |

Syntax:
- Statements are enclosed in angle brackets `< >` and placed **after the default value**.
- Multiple restrictions in one pair of brackets are separated by semicolon `;`.
- A statement is `name: value` (colon), or `name: v1, v2, ...` for allowed values.
- Restriction names contain spaces (`maximum length string`).

Examples from the text:
```
present-value: 13.4 <minimum: 0.0; maximum: 20.0; resolution: 0.1>
description: "this is a description" <maximum length string: 30>
units: milliamperes <allowed values: milliamperes, amperes>
object-property-reference: (analog input, 12) <allowed values: analog input, analog value>
```
Notes:
- Examples show property-name colon value form `name: value`; the property-line syntax itself is defined in 4.5 and later (not here).
- The last example writes object types with a space (`analog input`) rather than a dash, while 4.4(l) uses `analog-input`. Treat space/dash/underscore in enumeration names as equivalent when parsing limits (inferred).
- Units special case: min, max and resolution restrictions are valid only for the default value of the Units property, because changing units may change Present_Value and its restrictions.
- Default restrictions for most datatypes can be specified per 4.5.8 (not seen); a restriction on an individual property overrides the default.
- `<` `>` inside strings are part of the string; a `>` ends the restriction block otherwise (inferred).

## 7. Grammar sketch (derived, not normative)

```ebnf
(* Lexical level: operates on decoded characters *)
file          = header-line , signature-line , { body-line } , end-line ;
header-line   = "PICS" , SP , digit , CRLF ;           (* digit in 0..5; 4.1 *)
signature-line= "BACnet Protocol Implementation Conformance Statement" , CRLF ;
end-line      = "End of BACnet Protocol Implementation Conformance Statement" , CRLF ;
body-line     = { token | WS } , CRLF ;                 (* sections: 4.5, not defined here *)

WS            = ( TAB | SP | CR | LF ) , { TAB | SP | CR | LF } | comment ;
comment       = "--" , { any-char - CRLF } , CRLF ;      (* outside strings *)

string        = dq-string | sq-string ;
dq-string     = '"' , { any-char - '"' - CRLF } , ( '"' | CRLF-or-EOL ) ;
sq-string     = ( "'" | "`" ) , { any-char - "'" - CRLF } , ( "'" | CRLF-or-EOL ) ;

(* Values; keywords case-insensitive *)
value         = null | boolean | integer | real | octetstring | string
              | bitstring | enumerated | date | time | objectid
              | constructed | list | tagged ;
null          = "NULL" ;
boolean       = "T" | "TRUE" | "F" | "FALSE" ;
integer       = [ "-" ] , digit , { digit } ;            (* unsigned: no "-" (inferred) *)
real          = [ "-" ] , digit , { digit } , "." , digit , { digit } ;  (* "-" inferred *)
octetstring   = "X" , ( "'" | "`" ) , { hexdigit , hexdigit } , ( "'" | "`" ) ;
bitstring     = "{" , [ bit , { "," , bit } ] , "}" ;
bit           = boolean | "?" ;
enumerated    = ename | proprietary ;
ename         = letter , { letter | digit | "_" | "-" } ; (* "_" == "-" *)
proprietary   = "proprietary" , { "_" | "-" | letter | digit } , digit , { digit } ;
date          = "(" , [ dow , "," ] , dayf , "-" , monthf , "-" , yearf , ")" ;
dow           = weekday-name | "*" ;
dayf          = digit , { digit } | "*" ;
monthf        = month-name | "*" ;
yearf         = digit , digit , digit , digit | "*" ;    (* width inferred *)
time          = hourf , ":" , minf , ":" , secf , "." , hundf ;
hourf = minf = secf = hundf = digit , { digit } | "*" ;
objectid      = "(" , objtype , "," , integer , ")" ;
objtype       = ename | "proprietary" , integer ;
constructed   = "{" , [ elem , { "," , elem } ] , "}" ;  (* also arrays *)
list          = "(" , [ elem , { "," , elem } ] , ")" ;
elem          = value ;                                  (* nested constructed in braces *)
tagged        = "[" , integer , "]" , value ;            (* context-tagged CHOICE *)

(* Restrictions, 4.4.2 *)
restrictions  = "<" , restriction , { ";" , restriction } , ">" ;
restriction   = rname , ":" , rvalue , { "," , rvalue } ;
rname         = "minimum" | "maximum" | "resolution" | "maximum length string"
              | "maximum length list" | "maximum length array" | "allowed values" ;
prop-value    = value , [ restrictions ] ;
```
Parenthesis ambiguity: date, objectid and list all start with `(`; resolve by property datatype or by lookahead (month-name present means date; first element an object type name followed by one comma and an integer means objectid).

## 8. Ambiguities and open questions

1. BOM: not mentioned. Accept/ignore a leading UTF-8 BOM, or reject? UCS-2/UCS-4 BOMs would conflict with the fixed detection patterns.
2. Whether code 1/2/5 files are detected only by the 8-octet check (yes by the "octet stream" definition) and what to do with DBCS/JIS (decoding libraries: cp932/cp936? Unspecified which DBCS code page).
3. What if the header digit conflicts with the detected width (e.g. wide-pattern file saying "PICS 0")? Not stated.
4. Little-endian UTF-16/32 not covered.
5. Is the header, signature and end line case-insensitive? Is trailing whitespace or a comment allowed on them? Are they required to be a line by themselves (the text says "line containing the literal text")?
6. Bare LF or CR line endings: standard requires CRLF, but CR/LF are also white space. Tolerance is a decision.
7. Is a blank/comment line allowed between header and signature? ("first line following the header").
8. Since CR LF are white space, can a value or property span multiple lines? The text states no continuation rule.
9. Strings: no escapes, auto-termination at end of line (error or silent?), grave opening closes with apostrophe. Do octet strings follow the same pairing?
10. Octet-string rule (f) prints X'2D' for quote chars, almost certainly a typo for X'27'. Is empty `X''` valid? Can hex digits be mixed case? Can whitespace separate pairs?
11. Real numbers: exponent, leading `+`, `-` sign, `INF/NaN` not defined. No separate Unsigned/Double notation. Integer range limits not stated.
12. Dates: allowed month/day-of-week spellings (full names only in examples), abbreviations, case; whether `*` allowed in all of day/month/year; year width; whether `(*-*-*)` valid; whether date separators are always `-`. Also whether the date could appear without parentheses.
13. Times: hour padding, optional `.xx`, whether `*:*:*.*` and partial wildcard like `5*` valid.
14. Enumeration names: allowed characters; "proprietary" form with hyphen (`proprietary-object-type-653`) vs space form in object identifiers (`proprietary 700`); is case/underscore equivalence applied to the "proprietary" word too? Object-type names with spaces in 4.4.2 example (`analog input`).
15. `?` wildcard: stated only for bit strings. Not stated for other types; `*` only for date/time.
16. Context tag syntax `[n] value`: no worked example; whitespace between `]` and value unspecified.
17. Constructed values are positional with no field names? How are optional/absent elements encoded? Empty list/array/constructed forms not shown.
18. Lists vs dates vs object identifiers all use parentheses; needs type-driven parsing or lookahead.
19. Restrictions: allowed whitespace; whether value types inside restrictions follow 4.4 (date for min/max on Date, time resolution as a real number of seconds); whether restrictions may follow constructed values; multiple `allowed values` (the list uses commas while statements use `;`, so commas never terminate a restriction).
20. Section delimiting, ordering, default restrictions (4.5.8) are outside this scope and must be read in 4.5.
21. Keywords inside strings and comments: `--` in unquoted tokens such as enumeration names with consecutive dashes would start a comment (a name like `a--b` is a comment start).

## 9. Test case seeds

Notation: input -> expected. "ERR" means a conforming parser should reject; "(inferred)" or "(policy)" means the standard is silent and the decision is up to the implementers.

Header and detection
1. `50 49 43 53 20 30 0D 0A` (bytes) -> octet stream, code 0 UTF-8.
2. `PICS 5\r\n` -> octet stream, ISO 8859-1.
3. 16 bytes `00 50 00 49 00 43 00 53 00 20 00 34 00 0D 00 0A` -> double octet, code 4 UCS-2.
4. 32 bytes `00 00 00 50 ... 00 00 00 33 00 00 00 0D 00 00 00 0A` -> quad octet, code 3 UCS-4.
5. `PICS 9\r\n` -> ERR unknown character set code (inferred).
6. `PICS\r\n` or `PICS x\r\n` -> ERR missing numeral.
7. First line `PICS 0\n` (bare LF) -> ERR per strict 4.2; lenient mode may accept (policy).
8. UTF-8 BOM `EF BB BF` then `PICS 0\r\n` -> policy decision (standard silent).

Structure
9. Header, then `BACnet Protocol Implementation Conformance Statement\r\n`, then `End of BACnet Protocol Implementation Conformance Statement\r\n` -> valid empty EPICS.
10. Same file without the signature line -> ERR.
11. Same file without the End line -> ERR (4.2 says the file ends with it).
12. `-- a comment\r\n` inside the body -> ignored as white space.
13. `x: 5 -- trailing comment\r\n` -> value `5`, comment dropped.
14. `description: "a -- b"\r\n` -> string `a -- b`, not a comment (4.2, 4.3).
15. `a  \t  b` -> equivalent to `a b`.

Strings (4.3)
16. `"it's"` -> string `it's`.
17. `'say "hi"'` -> string `say "hi"`.
18. `` `say "hi"' `` -> string `say "hi"` (grave opens, apostrophe closes).
19. `"unterminated` + CRLF -> string `unterminated`, ended by line end (policy: warn).
20. `'it's'` -> string `it`, then stray `s'` (no escapes) -> likely ERR downstream.

Primitive values (4.4)
21. `NULL`, `null`, `Null` -> Null.
22. `T`, `true`, `False`, `f` -> True, True, False, False.
23. `12345`, `-111` -> Integer 12345, -111.
24. `-0` -> Integer 0 (inferred).
25. `1.23`, `0.02`, `1.0` -> Real.
26. `.02` -> ERR; `5.` -> ERR (4.4(e)).
27. `X'001122'` -> OctetString 00 11 22. `X'001'` -> ERR (odd digits, inferred). `x'ab'` accepted (inferred).
28. `{T,T,F}` and `{TRUE, TRUE, FALSE}` -> BitString [1,1,0] / same.
29. `{T,T,?}` -> BitString with don't-care third bit.
30. `{T,X,F}` -> ERR.
31. `Object_Type` and `object-type` -> same enumeration.
32. `proprietary-object-type-653` -> proprietary enumerated value 653.
33. `proprietary-object-type` (no trailing number) -> ERR as proprietary (inferred).
34. `(Monday, 24-January-1998)` -> Date weekday=Monday, 24, January, 1998.
35. `(Monday, *-January-1998)` -> day wildcard.
36. `(24-January-1998)` -> weekday unspecified.
37. `(Monday, 24-January-1998` -> ERR (unbalanced).
38. `2:05:44.00`, `16:54:59.99` -> Time with hour/minute/second/hundredths.
39. `16:54:*.*` -> Time with wildcard seconds and hundredths.
40. `(analog-input, 56)` -> ObjectIdentifier(analog-input, 56).
41. `(proprietary 700,1)` -> ObjectIdentifier(proprietary type 700, 1).
42. `(analog-input 56)` -> ERR (missing comma, inferred).

Complex values (4.4, 4.4.1)
43. `{1, {2, 3}, 4}` -> constructed/array of 1, constructed(2, 3), 4.
44. `(1, 2, 3)` -> list of three Integers.
45. `({1,2},{3,4})` -> list of two constructed items.
46. `[2] 5` -> context tag 2 holding Integer 5 (inferred spacing).
47. `5` for CHOICE of application-tagged -> chosen value without tag.
48. `{1,2` -> ERR (unbalanced).

Limits (4.4.2)
49. `present-value: 13.4 <minimum: 0.0; maximum: 20.0; resolution: 0.1>` -> Real 13.4 with minimum 0.0, maximum 20.0, resolution 0.1.
50. `description: "this is a description" <maximum length string: 30>` -> string with max length 30.
51. `units: milliamperes <allowed values: milliamperes, amperes>` -> enumerated with allowed set {milliamperes, amperes}.
52. `object-property-reference: (analog input, 12) <allowed values: analog input, analog value>` -> object identifier with allowed types {analog input, analog value} (space-form names, treat as equivalent to analog-input).
53. `x: 5 <minimum: 0, maximum: 9>` -> ERR (comma is not a statement separator; semicolon required).
54. `x: 5 <minimum 0>` -> ERR (missing colon).
55. `x: 5 <bogus: 1>` -> ERR unknown restriction name (inferred).
56. `x: "abc <maximum length string: 3>"` -> a single string `abc <maximum length string: 3>`, no restriction (inside quotes).
