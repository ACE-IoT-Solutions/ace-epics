# EPICS Sections and Data Model (ANSI/ASHRAE 135.1-2025, Clause 4.5)

Source: Clause 4.5 (4.5.1 to 4.5.10), with cross-references to 4.1 to 4.4.2 for lexical rules.
Paraphrased digest; exact keywords and literals are quoted. Items marked **(inferred)** are not stated by the standard.

Important extraction caveat: the source text lost the "open box" placeholder glyphs (the parameter markers). In this
digest, `""` in a syntax template means "a character string goes here" and a bare gap (e.g. `Maximum APDU size in octets: `)
means "a non-string value goes here". The standard defines these symbols in 4.5 intro: (a) open box inside quotes = a
character string shall be present; (b) open box with no quotes = a non-string datatype shall be present;
(c) `?` (used in the test database only) = property present but value unknown (hardware input / internal algorithm).

---

## 0. Lexical rules that apply to every section (from 4.1 to 4.4, context only)

- File extension `.TPI`; lines end CR/LF. First line is the header `PICS #` (# = charset code; 0 ISO 10646 UTF-8, 1 IBM/Microsoft DBCS, 2 JIS X 0208, 3 ISO 10646 UCS-4, 4 ISO 10646 UCS-2, 5 ISO 8859-1) (4.1, Table 4-1).
- Next line (signature): `BACnet Protocol Implementation Conformance Statement`; last line: `End of BACnet Protocol Implementation Conformance Statement` (4.2).
- Whitespace (tab, space, CR, LF) runs collapse to one space except in strings. `--` starts a comment to end of line (except inside strings); comments are whitespace (4.2).
- Strings: `"..."` ends at next `"` or end of line; `'...'` or accent-grave quoting ends at next `'` or end of line (4.3). Note: the standard says a backtick-opened string ends at a single quote (4.3).
- Keywords are case-insensitive (4.4a). Booleans `T`/`TRUE`/`F`/`FALSE`; null `NULL`; integers `12345`/`-111`; reals need a digit on both sides of the point (`1.23`, not `.02`); octet strings `X'001122'`; bitstrings `{T,T,?}`; enumerations are case-insensitive with `_` equivalent to `-`, proprietary values are `proprietary-<name>-<n>` style names starting with "proprietary" and ending in a non-negative decimal (4.4i); dates `(Monday, 24-January-1998)` with `*` wildcards, day-of-week may be omitted; times `hh:mm:ss.xx` with `*` wildcards; object identifiers `(analog-input, 56)` or `(proprietary 700,1)`; constructed `{a,b}` (4.4j-m, 4.4.1).
- 4.4.1: CHOICE of context-tagged values is `[tag] value`; SEQUENCE OF lists are `( a, b )` with constructed elements in `{}`; arrays `{ a, b }`.
- 4.4.2 restriction syntax: `<name: value; name: value>` placed after a value.

## 1. Section structure (4.5 intro)

- Every section is `Section Name: { ... }` : a name, a colon, then one or more parameters delimited by curly braces (4.5). The general-information sections 4.5.1 are the exception: they are single-line `Keyword: "string"` entries with no braces (4.5.1 syntax).
- The standard prints a section order by subsection number and states only that the Test Database is "the last section" (4.5.10). It does **not** explicitly state that order is fixed for sections 4.5.1 to 4.5.9, nor which sections are mandatory. **(inferred)**: the printed order is canonical; a tolerant parser should accept any order except Test Database last.
- Mandatory vs optional is not stated anywhere in 4.5. Only weak hints: empty lists are explicitly legal for BIBBs (4.5.2.1) and Default Property Value Restrictions (4.5.8) ("An empty list indicates..."), implying those sections are still present when empty. **(inferred)** treat as required-by-format but allow empty.

Ordered list of sections (heading keyword as printed):

| # | Clause | Heading | Form |
|---|--------|---------|------|
| 1 | 4.5.1 | `Vendor Name` | single-line string |
| 2 | 4.5.1 | `Product Name` | single-line string |
| 3 | 4.5.1 | `Product Model Number` | single-line string |
| 4 | 4.5.1 | `Product Description` | single-line string |
| 5 | 4.5.2.1 | `BIBBs Supported` | braced list |
| 6 | 4.5.3 | `BACnet Standard Application Services Supported` | braced list |
| 7 | 4.5.4 | `Standard Object Types Supported` | braced list |
| 8 | 4.5.5 | `Data Link Layer Option` | braced list |
| 9 | 4.5.6 | `Character Sets Supported` | braced list |
| 10 | 4.5.7 | `Special Functionality` | braced list |
| 11 | 4.5.8 | `Default Property Value Restrictions` | braced list |
| 12 | 4.5.9 | `Fail Times` | braced key:value list |
| 13 | 4.5.10 | `List of Objects in Test Device` | braced list of braced objects, LAST |

Heading-name notes:
- The title of 4.5.2 is "Conformance Sections" (container title only; no `Conformance:` keyword). 4.5.2.1 is the only subsection and its heading is `BIBBs Supported`. The BIBB example in the standard prints `BIBBS Supported` (capital S); keywords are case-insensitive so both are the same heading.
- 4.5.5 heading is singular `Data Link Layer Option` (not "Options"), though subsection title is "Data Link Layer Options". 4.5.6 is `Character Sets Supported` (clause title "Character Sets").
- 4.5.4 example block erroneously reuses the heading `BACnet Standard Application Services Supported` (copy-paste error in the standard); the syntax block shows the correct heading `Standard Object Types Supported`. Parsers should key on the syntax-block heading. (Also see Ambiguities.)
- The 4.5.1 title says "Sections" (four separate one-line sections), each with its own keyword.
- The standard in Clause 4.5 defines NO keywords for protocol revision, profile, vendor identifier, firmware/software version, segmentation, or Device-level identity. Those facts appear only via the test database (Device object properties such as `protocol-revision`, `vendor-identifier`) **(inferred)**; the Fail Times/BIBB sections are the only conformance claims.

---

## 2. Subsection details

### 4.5.1 General Information Sections

Four independent single-line sections, each `Keyword: "string"`:

| Keyword | Value type | Card. | Notes |
|---|---|---|---|
| `Vendor Name` | character string | 1 | quoted per 4.3 |
| `Product Name` | character string | 1 | |
| `Product Model Number` | character string | 1 | |
| `Product Description` | character string | 1 | |

No defaults, allowed values, or length limits are stated. No braces. Whether any is optional is not stated.

### 4.5.2 / 4.5.2.1 BIBBs Supported

- Heading: `BIBBs Supported:` then `{` ... `}`.
- One BIBB per line, between braces. Empty list means no BIBBs supported.
- Value: the short acronym of the BIBB title from Annex K, e.g. `DS-RP-B` for "Data Sharing - ReadProperty - B". The list of valid BIBB acronyms is NOT in Clause 4.5 (Annex K); the standard's example uses `DS-RP-B`, `DS-WP-B`, `DS-RPM-B`, `DM-DOB-B`, `DM-DDB-B`, `DM-DDB-A`.
- Cardinality: list of strings (zero or more). No duplicates rule stated. Acronym format convention (inferred from examples): `<Group>-<Name>-<A|B>` with hyphens; devices may also have other suffixes in Annex K (not verified here).

### 4.5.3 Application Services Supported

- Heading: `BACnet Standard Application Services Supported:`
- One service per line: service name, then one of the flag forms:
  - `Initiate`
  - `Execute`
  - `Initiate Execute` (both)
- Syntax template shows just flag words; example shows `<ServiceName> <flags>` aligned in columns (whitespace is insignificant).
- Service name form: the title of the service's clause in the standard with the trailing word "Service" removed (e.g. `AcknowledgeAlarm`). Valid names are those in the Clause 21 production `BACnetServicesSupported` (not reproduced in 4.5).
- Examples given: `Who-Is Initiate Execute`, `I-Am Initiate Execute`, `Who-Has Execute`, `I-Have Initiate`, `ReadProperty Execute`, `ReadPropertyMultiple Execute`, `WriteProperty Execute`.
- Flags: required (at least one) per line; `Initiate` and `Execute` are the only flag words; flag order shown as `Initiate Execute` **(inferred: also accept reversed order)**. Cardinality: list of (name, flags).
- Name spelling includes hyphens for some (`Who-Is`, `I-Am`, `Who-Has`, `I-Have`) and CamelCase for others; hence match case-insensitively and normalize **(inferred)**.

### 4.5.4 Object Types Supported

- Heading: `Standard Object Types Supported:`
- One object type per line, optionally followed by `Createable`, `Deleteable`, or both (`Createable Deleteable`). Note the spellings: `Createable` (not "Creatable") and `Deleteable`.
- Object type name form: the title of the object type's clause minus the words "Object Type", written with spaces and capitalization, e.g. `Analog Value`, `Analog Input`, `Device`. Valid ones are from Clause 21 `BACnetObjectTypesSupported` (not reproduced in 4.5). Contrast with the test database, where object types are enumeration-style (`analog-value`).
- Example: `Analog Value Createable Deleteable`, `Analog Input`, `Device`.
- Cardinality: list of (type name, createable: bool, deleteable: bool), flags default false.

### 4.5.5 Data Link Layer Options

- Heading: `Data Link Layer Option:` (singular).
- One option per line. Complete list of literal strings from the standard (angle/box placeholders shown as `<...>`):

```
ISO 8802-3, 10BASE5
ISO 8802-3, 10BASE2
ISO 8802-3, 10BASET
ISO 8802-3, fiber
ARCNET, coax star
ARCNET, coax bus
ARCNET, twisted pair star
ARCNET, twisted pair bus
ARCNET, fiber star
ARCNET, twisted pair, EIA-485, Baud rate(s): <baud list>
MS/TP manager. Baud rate(s): 9600, <more baud rates>
MS/TP subordinate. Baud rate(s): 9600, <more baud rates>
Point-To-Point. EIA 232, Baud rate(s): <baud list>
Point-To-Point. Modem, Baud rate(s): <baud list>
Point-To-Point. Modem, Autobaud range: <min> to <max>
BACnet/IP, 'DIX' Ethernet
BACnet/IP, Other
BACnet/IPv6, 'DIX' Ethernet
BACnet/SC
Zigbee
Other
```

- Narrative says "MS/TP and Point-To-Point data links shall also specify supported baud rate(s)". The template also attaches baud rates to the ARCNET EIA-485 line (narrative omits it). The `MS/TP` templates show `9600,` followed by a placeholder: 9600 is a literal first value shown (inferred: MS/TP manager/subordinate must support 9600, with further rates following as a comma list; stated only by the template, not narrative). Baud rates are integers, comma-separated **(inferred)**.
- Punctuation is inconsistent and must be preserved/normalized: `MS/TP manager.` and `Point-To-Point.` use a period after the type; ARCNET/ISO use a comma. `Modem` has two alternative lines: `Baud rate(s):` list or `Autobaud range: <low> to <high>` (the word `to` is literal).
- Note `ARCNET, fiber star` appears but no `fiber bus`; `BACnet/IP` has `'DIX' Ethernet` and `Other`, but `BACnet/IPv6` only has `'DIX' Ethernet`. These are as printed (no `BACnet/IPv6, Other`). The single quotes around DIX are literal.
- Cardinality: list (zero or more; empty not discussed). `Other` has no free-text description defined.

### 4.5.6 Character Sets

- Heading: `Character Sets Supported:`; one per line. Complete literal list:

```
ISO 10646 (UTF-8)
IBM/Microsoft DBCS
JIS X 0208
ISO 8859-1
ISO 10646 (UCS-4)
ISO 10646 (UCS2)
```

- Surprise: `ISO 10646 (UCS2)` here has no hyphen, whereas Table 4-1 in 4.1 says `ISO 10646 (UCS-2)`; Table 4-1 also writes `IBM™/Microsoft™ DBCS` (with trademark symbols) vs `IBM/Microsoft DBCS` here. Treat as aliases **(inferred)**. Order in the section differs from Table 4-1 numeric codes.
- Cardinality: list. Relationship to the `PICS #` header code (file encoding) is not stated; the supported-set list is independent of the file's own encoding.

### 4.5.7 Special Functionality

- Heading: `Special Functionality:`; one entry per line. Literal entries:

| Entry (literal) | Parameter | Type |
|---|---|---|
| `Maximum APDU size in octets: <n>` | n | integer |
| `Segmented Requests Supported, window size: <n>` | n | integer |
| `Segmented Responses Supported, window size: <n>` | n | integer |
| `Router` | flag | none |
| `BACnet/IP BBMD` | flag | none |
| `BACnet/IPV6 BBMD` | flag | none |
| `BACnet/SC Hub` | flag | none |
| `BACnet/SC Direct Connect` | flag | none |

- "Maximum APDU size and window sizes shall be specified as integers." Presence of the Segmented lines means segmentation of that direction is supported **(inferred)**; absence means not supported. Each entry appears at most once **(inferred)**. Window size meaning/range is not defined in 4.5. Note `BACnet/IPV6 BBMD` spelled with uppercase V (case-insensitive anyway).

### 4.5.8 Property Value Restrictions

- Heading: `Default Property Value Restrictions:`; one datatype per line; only datatypes with defaults are listed; empty list means none.
- Restrictions listed per datatype apply to every writable property (or component of one) of that datatype; override per property in the test database using 4.4.2 syntax.
- Datatype keys (lowercase literals) and their restriction tuples, all in angle brackets, `;`-separated:

| Datatype key | Restrictions |
|---|---|
| `unsigned-integer` | `<minimum: N; maximum: N>` |
| `signed-integer` | `<minimum: N; maximum: N>` |
| `real` | `<minimum: R; maximum: R; resolution: R>` |
| `double` | `<minimum: R; maximum: R; resolution: R>` |
| `date` | `<minimum: DATE; maximum: DATE>` |
| `octet-string` | `<maximum length string: N>` |
| `character-string` | `<maximum length string: N>` |
| `list` | `<maximum length list: N>` |
| `variable-length-array` | `<maximum length array: N>` |

- Observations: 4.4.2 also defines `resolution` for Time and `allowed values`, but 4.5.8 provides no `time` key and no `allowed values`/enumerated default. The syntax lists `minimum`/`maximum`/`resolution` for real/double (3 items), 2 for ints and date. The `maximum length array` restriction applies to arrays (key is `variable-length-array`). Whether all restriction items in a tuple are required or can be partially specified is not stated **(inferred: allow subset)**.

### 4.5.9 Timers (Fail Times)

- Heading: `Fail Times:`; each entry `Name: <real seconds>`. "A Real value in seconds must be provided for each timer" (so all 13 required, real format with decimal point per 4.4e). Referenced: Clause 6.3 for meaning.
- Complete list of keywords:

```
Notification Fail Time
Internal Processing Fail Time
Minimum ON/OFF Time
Schedule Evaluation Fail Time
External Command Fail Time
Program Object State Change Fail Time
Acknowledgement Fail Time
Subordinate Proxy Confirm Interval
Unconfirmed Response Fail Time
Channel Write Fail Time
Auto Negotiation Fail Time
Activate Changes Fail Time
Foreign Device Registration Fail Time
```

- Value type: Real (seconds). No defaults/bounds stated. Two names do not end in "Fail Time" (`Minimum ON/OFF Time`, `Subordinate Proxy Confirm Interval`). Spelling `Acknowledgement` (British, with "e").

---

## 3. Test Database (4.5.10) in depth

### Container

```
List of Objects in Test Device:
{
    object1
    object2
    ...
    objectN
}
```
Last section of the file. Each object is itself a braced block `{ ... }` of property lines (the template's `object1..objectN` are those braced blocks). Commas between objects are not shown **(inferred: none)**.

### Object block (fixed leading three properties)

1. First property is always `object-identifier: (object-type, instance)` (the tuple type+instance).
2. Second is always `object-name: "<string>"`.
3. Third is always `object-type: <object-type>` and its value must match the type in the identifier tuple.
4. Then "other properties...".

```
{
    object-identifier: (analog-value, 6)
    object-name: "AV6"
    object-type: analog-value
    present-value: 23.4 W
}
```

### Property line syntax

`property-name: value [W|C] [<restrictions>] [-- comment]`
- Property names appear in the lowercase hyphenated enumeration style (`object-identifier`, `present-value`, `object-property-reference`, `units`, `description`); by 4.4i-style equivalence of `_` and `-` and case-insensitivity **(inferred)** `Present_Value` should also be accepted.
- Object types are enumeration names: `analog-value`, `analog-input`. In restriction `allowed values` lists, 4.4.2's example shows spaces: `(analog input, 12) <allowed values: analog input, analog value>` (spaces instead of hyphens, an inconsistency in the standard; accept both) **(inferred)**.
- Values use 4.4/4.4.1 notation (strings, reals, enumerations, bitstrings, dates, times, object IDs, constructed `{}`, lists `()`, arrays `{}`, CHOICE `[n] value`).

### Writability markers

- `W` after the value: property is writable. Example: `present-value: 23.4 W`.
- `C` after the value: conditionally writable. Example: `present-value: 12.3 C -- Writable when Out_Of_Service is TRUE`. The standard recommends (not requires) naming the governing mechanism in a comment.
- No marker: read-only (stated by contrast; no explicit `R` marker exists in 4.5. Nothing defined as "R").
- Marker position relative to restriction brackets: 4.4.2 says restrictions "follow the default value", and their examples show no marker; the combination order (`23.4 W <minimum: 0.0>` vs `23.4 <...> W`) is NOT specified. Open question.

### Unknown value `?`

- `?` (4.5 intro) indicates property present but value unknown (depends on hardware input or internal algorithm). Within bitstrings, `?` marks a don't-care bit (`{T,T,?}`, 4.4h); in dates/times `*` marks wildcards (4.4j-k). Whether `?` is valid inside arrays/lists elements or as value for any datatype is not stated **(inferred: whole-value only, plus bit positions)**.

### Proprietary objects and properties

- Nonstandard (proprietary) object definitions shall contain only the three required properties:
```
{
    object-identifier: (proprietary 700, 1)
    object-name: "..."
    object-type: proprietary 700
}
```
(Standard shows placeholders `proprietary ` plus number; 4.4l writes `(proprietary 700,1)`; 4.4i says proprietary enumeration names are `proprietary-...-<n>`: two notations coexist for object type. Unclear: the type value on `object-type:` is shown as `proprietary <n>` (with a space) in the template.)
- Proprietary properties on standard objects are not addressed in 4.5 (only proprietary-valued enumerations in 4.4i).

### Device object / Object_List

- 4.5.10 contains no special rule for the Device object or `object-list`. The Device appears as an ordinary object entry (listed with type `Device` in 4.5.4). Whether the Device object must be listed, and consistency between `object-list`, the test-database entries and 4.5.4, belong to Clause 5 (EPICS consistency tests, not in this extract). Heading of Clause 5 appears right after 4.5.10.

### Limits (4.4.2) in the database

- Restriction statements go in angle brackets after the value; multiple separated by `;`; each is `name: value` or `name: v1, v2, ...`. Restriction names: `minimum`, `maximum`, `resolution`, `maximum length string`, `maximum length list`, `maximum length array`, `allowed values`.
- Examples: `present-value: 13.4 <minimum: 0.0; maximum: 20.0; resolution: 0.1>`; `description: "this is a description" <maximum length string: 30>`; `units: milliamperes <allowed values: milliamperes, amperes>`; `object-property-reference: (analog input, 12) <allowed values: analog input, analog value>`.
- A restriction on a specific property overrides the 4.5.8 default for that property. For `units`, min/max/resolution only apply to the default Units value.
- Applies to writable properties (defaults apply "to every writable property or component" of that datatype).

---

## 4. Proposed Pydantic model sketch (PROPOSAL, not from the standard)

```
EpicsFile
  header: PicsHeader
      charset_code: int            # 0..5, Table 4-1
  signature_ok: bool               # first/last line literals (4.2)
  general: GeneralInfo
      vendor_name: str
      product_name: str
      product_model_number: str
      product_description: str
  bibbs_supported: list[str]
  application_services: list[ServiceSupport]
      ServiceSupport: name: str; initiate: bool; execute: bool    # >=1 true
  object_types_supported: list[ObjectTypeSupport]
      ObjectTypeSupport: name: str; createable: bool=False; deleteable: bool=False
  data_link_layers: list[DataLinkOption]
      DataLinkOption: kind: Literal[<enumerated base strings>] | str (Other)
                      raw: str
                      baud_rates: list[int] | None
                      autobaud_min: int | None; autobaud_max: int | None
  character_sets: list[CharacterSet]          # enum of 6 strings
  special_functionality: SpecialFunctionality
      max_apdu_size: int | None
      segmented_requests_window: int | None
      segmented_responses_window: int | None
      router: bool = False
      bacnet_ip_bbmd: bool = False
      bacnet_ipv6_bbmd: bool = False
      bacnet_sc_hub: bool = False
      bacnet_sc_direct_connect: bool = False
  default_restrictions: DefaultRestrictions
      unsigned_integer: IntRange | None       # minimum, maximum
      signed_integer: IntRange | None
      real: RealRange | None                  # minimum, maximum, resolution
      double: RealRange | None
      date: DateRange | None
      octet_string: MaxLength | None          # maximum_length_string
      character_string: MaxLength | None
      list_: MaxListLength | None
      variable_length_array: MaxArrayLength | None
  fail_times: FailTimes                       # 13 float fields (seconds)
      notification, internal_processing, minimum_on_off, schedule_evaluation,
      external_command, program_object_state_change, acknowledgement,
      subordinate_proxy_confirm_interval, unconfirmed_response, channel_write,
      auto_negotiation, activate_changes, foreign_device_registration
  test_database: list[TestObject]
      TestObject
          object_identifier: ObjectId          # (type: str, instance: int, proprietary_type: int|None)
          object_name: str
          object_type: str
          properties: list[PropertyEntry]      # ordered
      PropertyEntry
          name: str
          value: Value | Unknown               # Unknown for "?"
          access: Literal["R","W","C"] = "R"
          restrictions: Restrictions | None
          comment: str | None
      Value = Null | bool | int | float | str | bytes | BitString | Date | Time
              | ObjectId | Enum | Sequence(list) | Array | Choice(tag:int,value) | Constructed
      Restrictions: minimum, maximum, resolution, maximum_length_string,
                    maximum_length_list, maximum_length_array, allowed_values: list[str]
```

## 5. Ambiguities and open questions

1. Which sections are mandatory, and is order fixed? Standard says only that Test Database is last. Decide: strict printed order vs. lenient.
2. Placeholder glyph loss: exact value syntax of baud-rate lists (comma separated? spaces?) and the autobaud `<min> to <max>` is inferred.
3. MS/TP template includes literal `9600,` as first baud; is 9600 mandatory? Likely, but unstated.
4. ARCNET `EIA-485` line: baud rates per template but narrative says only MS/TP and PTP.
5. Service/object type name normalization: `Who-Is` vs `WhoIs`; `Analog Value` vs `analog-value`; validate against Clause 21 lists, which are not in this extract. Annex K BIBB list also not in this extract.
6. `Initiate`/`Execute` order and whether `Execute Initiate` is accepted.
7. Marker order: `W`/`C` vs `<restrictions>` and vs comment.
8. `?` scope (whole value only? inside lists/arrays/structures?). Is `?` allowed on writable (`W`) properties?
9. Proprietary object `object-type:` notation (`proprietary 700` vs `proprietary-object-type-700`) and whether proprietary properties on standard objects are permitted/how named.
10. Property-name spelling in test database: hyphen (`object-identifier`) vs underscore (`Object_Identifier`) both appear (the intro text says "Object_Identifier"; examples use hyphens, comments use `Out_Of_Service`). Treat equivalent.
11. Restriction `allowed values` spelling of object types with spaces vs hyphens.
12. `ISO 10646 (UCS2)` vs `(UCS-2)`; `IBM/Microsoft DBCS` vs trademarked form.
13. `Default Property Value Restrictions` lacks `time` and `enumerated`; 4.4.2 allows `resolution` on Time and `allowed values`.
14. Heading error in 4.5.4 example (reuses services heading).
15. Does the Fail Times section require all 13 timers (text says "for each timer")? Newer timers (Auto Negotiation, Activate Changes, Foreign Device Registration) would be absent from older EPICS files; decide leniency/defaults.
16. Cardinality of repeated entries (duplicates) and empty lists (only BIBBs/default restrictions are explicitly allowed empty).
17. Whether the Device object and `object-list` must match the test database (Clause 5, out of scope here).
18. Whether commas or other separators are used between objects/properties (none shown).

## 6. Test case seeds

Valid (V) and invalid (I). Invalid ones are "I (strict)" if the standard implies but does not explicitly state invalidity.

1. V: `Vendor Name: "Ace IoT Solutions"` -> general.vendor_name = `Ace IoT Solutions`.
2. V: `vendor name: 'ACME'` (lowercase keyword, single quotes) -> same as 1 (4.4a, 4.3).
3. V: `Product Description: "He said 'hi'"` -> value contains single quotes (4.3).
4. V: `Product Name: 'say "x"'` -> value contains double quotes.
5. V: unterminated `Product Name: "abc` (no closing quote) -> string ends at end of line = `abc` (4.3).
6. V: `BIBBs Supported:` with `{` `}` and nothing between -> empty list.
7. V: `BIBBS Supported:` `{ DS-RP-B DM-DDB-A }` on separate lines -> ["DS-RP-B","DM-DDB-A"], heading case-insensitive.
8. I (strict): `BIBBs Supported: DS-RP-B` without braces -> error.
9. V: `Who-Is Initiate Execute` -> initiate True, execute True.
10. V: `Who-Has Execute` -> execute only.
11. V: `I-Have Initiate ` (trailing space) -> initiate only.
12. I: `ReadProperty` with no flag -> error (flag required).
13. I: `ReadProperty Both` -> error (unknown flag).
14. V: `Analog Value Createable Deleteable` -> createable and deleteable True.
15. V: `Device` -> both False. I: `Analog Input Creatable` -> error (spelling `Createable`).
16. V: `ISO 8802-3, 10BASET` ; `BACnet/SC` ; `Zigbee` ; `Other`.
17. V: `MS/TP manager. Baud rate(s): 9600, 19200, 38400` -> baud_rates [9600,19200,38400] (inferred format).
18. V: `Point-To-Point. Modem, Autobaud range: 9600 to 57600` -> autobaud 9600..57600.
19. I: `MS/TP manager.` with no baud rates -> error (shall specify baud rates).
20. I: `ARCNET, fiber bus` -> not in the standard's list.
21. V: `ISO 10646 (UTF-8)` ; I (strict): `ISO 10646 (UTF-16)`.
22. V: `Maximum APDU size in octets: 1476` -> 1476; I: `Maximum APDU size in octets: 1476.0` -> error (integer required).
23. V: `Segmented Requests Supported, window size: 4`; V: `Router`; V: `BACnet/IPV6 BBMD` and `bacnet/ipv6 bbmd` equal.
24. V: `real: <minimum: 0.0; maximum: 100.0; resolution: 0.1>` under `Default Property Value Restrictions`.
25. I: `real: <minimum: .5; maximum: 1.0>` -> `.5` invalid real (4.4e); V: `signed-integer: <minimum: -10; maximum: 10>`.
26. V: `octet-string: <maximum length string: 255>`; I (strict): `octet-string: <maximum length list: 5>` -> wrong restriction for type.
27. V: `Fail Times:` block with `Notification Fail Time: 10.0` ; I: `Notification Fail Time: 10` (integer where Real required; lenient parsers may coerce).
28. I: Fail Times missing `Channel Write Fail Time` -> error per "for each timer" (or warn, see open question 15).
29. V: object with identifier `(analog-value, 6)`, name `"AV6"`, type `analog-value`, `present-value: 23.4 W` -> access W.
30. V: `present-value: 12.3 C -- Writable when Out_Of_Service is TRUE` -> access C, comment captured, not part of value.
31. V: `present-value: ?` -> Unknown; V: `status-flags: {F,F,?,F}`.
32. I: object whose `object-type: analog-input` conflicts with identifier `(analog-value, 6)` -> error.
33. I: object where `object-name` appears before `object-identifier` -> error (order fixed: id, name, type).
34. V: proprietary object with exactly three properties and `(proprietary 700, 1)`; I: same plus `present-value: 1` -> error (only three properties allowed).
35. V: `present-value: 13.4 <minimum: 0.0; maximum: 20.0; resolution: 0.1>` -> value 13.4, restrictions parsed.
36. V: `units: milliamperes <allowed values: milliamperes, amperes>` -> allowed_values list of 2.
37. V: `description: "this is a description" <maximum length string: 30>`.
38. V: `Present_Value: 1.0` equals `present-value: 1.0` (underscore/dash/case equivalence, inferred for property names).
39. V: `-- comment line` between sections and trailing `-- x` on lines ignored; I: `"a -- b"` inside string is not a comment.
40. V: file with `PICS 0` header, signature, sections, `End of BACnet Protocol Implementation Conformance Statement`; I: missing end line -> error.
