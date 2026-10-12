# Annex A (Informative) Example EPICS: Syntax Analysis

Source: ANSI/ASHRAE 135.1-2025, Annex A "EXAMPLE EPICS (INFORMATIVE)" (PDF pages 1100-1112).
This document analyses the example for parser and test-corpus design. It quotes only short
snippets. The full reconstruction lives outside the repo (the standard is copyrighted); line
references below (`L###`) point to that private reconstruction, `annexA-clean.epics`
(1063 lines, produced from `pdftotext -layout`, page furniture removed, a few
`-- EXTRACTION-NOTE:` comment lines added). Line numbers include those note lines.

Verification note: suspicious spots were cross-checked against `pdftotext -raw`. Typos listed in
section 5 are in the standard itself, not extraction damage. Only the "Special Functionality:"
heading spacing and justified comment padding were extraction artefacts.

---

## a. Section sequence

| # | Exact heading / delimiter line | Lines | Notes |
|---|---|---|---|
| 0 | `PICS 0` | L1 | Character-set header (Table 4-1 code 0 = UTF-8) |
| 1 | `BACnet Protocol Implementation Conformance Statement` | L2 | Signature line |
| - | `--` then three `-- ...` comment lines | L4-7 | Comment block; first comment line is a bare `--` |
| 2 | `Vendor Name:` / `Product Name:` / `Product Model Number:` / `Product Description:` | L9-12 | General information (single-line key: value) |
| 3 | `BIBBs Supported:` | L15 | `{` on the next line, one BIBB per line |
| 4 | `BACnet Standard Application Services Supported:` | L199 | |
| 5 | `Standard Object Types Supported:` | L252 | |
| 6 | `Data Link Layer Option:` | L322 | |
| 7 | `Character Sets Supported:` | L348 | |
| 8 | `Special Functionality:` | L365 | |
| 9 | `Default Property Value Restrictions:` | L382 | |
| 10 | `List of Objects in test device:` | L403 | Test database |
| 11 | `End of BACnet Protocol Implementation Conformance Statement` | L1063 | Terminator |

Observations:

- All section headings are followed by `{` on the NEXT line and closed by `}` on its own line
  (never `Heading: {` on one line, and `Heading:` is never followed by value text on the
  same line).
- Section order is exactly the order of Clause 4.5.x EXCEPT that the Annex has no
  `Fail Times:` section (4.5.9). The Annex omits it entirely.
- Heading case differs from Clause 4: Annex uses `List of Objects in test device:` where
  Clause 4.5.10 writes `List of Objects in Test Device:`. Keywords must be matched
  case-insensitively (4.4(a) already says so).
- Section comments precede each section (`-- Delete any BIBBS not supported.` L14 etc.). They
  contain instructional text and are plain `--` comments.
- Header text before the sections: `--` comment lines only (no blank-line semantics).
- Blank lines occur between sections and between objects. They are insignificant.

## b. General Information section

Exact keywords (4, all present, all in the order of Clause 4.5.1):

| Keyword (exact spelling) | Value style | Example |
|---|---|---|
| `Vendor Name:` | double-quoted string | `Vendor Name: "ASHRAE"` |
| `Product Name:` | double-quoted string | `Product Name: "Standard BACnet Device"` |
| `Product Model Number:` | double-quoted string (a numeric-looking text stays quoted) | `Product Model Number: "1.0"` |
| `Product Description:` | double-quoted string, may contain spaces and `!` | `Product Description: "A really great thing!"` |

No braces. One line per keyword. Values are always on the same line as the keyword.
No other general-information keywords (no vendor id, firmware, protocol revision) appear.

## c. Conformance, services, object types, data link, charsets, special functionality

### c.1 BIBBs (L15-196)
`BIBBs Supported:` then `{`, 177 BIBB acronyms one per line, `}`. Spelling is
`BIBBs` in the heading (the comment says `BIBBS`). Entries are bare tokens made of upper-case
letters and hyphens with 1-3 hyphens, e.g. `DS-RP-A`, `DS-WG-I-B`, `T-VMMV-I-B`, `SCHED-AVM-A`,
`AA-NAT-B`, `DM-SP-VM-A`. No quotes, no commas, no inline comments. The list is indented
inconsistently (3 or 4 spaces) because of page breaks and source formatting.

### c.2 Application services (L199-250)
`BACnet Standard Application Services Supported:` then 46 lines of the form

```
  AcknowledgeAlarm                       Initiate   Execute
```

- Service name, then the whitespace-separated words `Initiate` and `Execute`. Every line has
  BOTH words (this is a template; the instructions say "Remove Initiate and Execute as
  appropriate").
- Separator whitespace is variable. One line has a SINGLE space between name and `Initiate`
  because the name overflows the column:
  `UnconfirmedCOVNotificationMultiple Initiate       Execute`.
- Names are the Clause 21 style, CamelCase with hyphenated forms for unconfirmed/network ones:
  `Who-Has`, `I-Have`, `Who-Is`, `I-Am`, `Who-Am-I`, `You-Are`, `VT-Open`, `VT-Close`, `VT-Data`.
  Others without spaces: `ConfirmedCOVNotificationMultiple`, `UnconfirmedAuditNotification`,
  `AuditLogQuery`, `WriteGroup`, `LifeSafetyOperation`.
- No line has only `Initiate` or only `Execute` and no tabs are used.

### c.3 Standard object types (L252-321)
`Standard Object Types Supported:` then 64 lines. 63 of them are

```
    Analog Input                 Creatable            Deleteable
```

and one is bare: `    Device` (no suffix). Exact observed type strings (names are multi-word with
single spaces; one hyphenated): `Accumulator`, `Analog Input`, `Analog Output`, `Analog Value`,
`Averaging`, `Binary Input`, `Binary Output`, `Binary Value`, `Calendar`, `Command`, `Device`,
`Event Enrollment`, `File`, `Group`, `Life Safety Point`, `Life Safety Zone`, `Loop`,
`Multi-state Input`, `Multi-state Output`, `Multi-state Value`, `Notification Class`, `Program`,
`Pulse Converter`, `Schedule`, `Trend Log`, `Event log` (lower-case `log`), `Global Group`,
`Trend Log Multiple`, `Load Control`, `Structured View`, `Access Door`, `Timer`,
`Access Credential`, `Access Point`, `Access Rights`, `Access User`, `Access Zone`,
`Credential Data Input`, `Bitstring Value`, `Characterstring Value`, `Date Pattern Value`,
`Date Value`, `Datetime Pattern Value`, `Datetime Value`, `Integer Value`, `Large Analog Value`,
`Octetstring Value`, `Positive Integer Value`, `Time Pattern Value`, `Time Value`,
`Notification Forwarder`, `Alert Enrollment`, `Channel`, `Lighting Output`,
`Binary Lighting Output`, `Network Port`, `Elevator Group`, `Escalator`, `Lift`, `Staging`,
`Audit Log`, `Audit Reporter`, `Color`, `Color Temperature`.

KEY DIFFERENCE: the Annex spells the suffix `Creatable`; Clause 4.5.4 spells it `Createable`.
`Deleteable` matches. A parser must accept both `Creatable` and `Createable` (and the doc 02
test seed that rejects `Creatable` conflicts with the standard's own example).

### c.4 Data link layer options (L322-346)
`Data Link Layer Option:` (singular `Option`) then 21 free-text lines (see section d of Clause 4.5.5).
Exact strings:

```
ISO 8802-3, 10BASE5 | ISO 8802-3, 10BASE2 | ISO 8802-3, 10BASET | ISO 8802-3, Fiber
ARCNET, coax star | ARCNET, coax bus | ARCNET, twisted pair star | ARCNET, twisted pair bus
ARCNET, fiber star
MS/TP manager. Baud rate(s): 9600, 19200, 38400, 76800, 115200
MS/TP subordinate. Baud rate(s): 9600, 19200, 38400, 76800, 115200
Point-To-Point. EIA 232, Baud rate(s)
Point-To-Point. Modem, Baud rate(s): 14.4k
Point-To-Point. Modem, Autobaud range: 9600 to 28.8k
BACnet/IP, 'DIX' Ethernet | BACnet/IP, PPP Other | LonTalk | Other | BACnet/SC
BACnet/IPv6, 'DIX' Ethernet | Zigbee
```

Notable: `Fiber` capitalised (Clause 4 has `fiber`); `BACnet/IP, PPP Other` and `LonTalk` are
not in Clause 4's list; `ARCNET, twisted pair, EIA-485` is absent; `Point-To-Point. EIA 232,
Baud rate(s)` has no colon and no value; baud rates use plain integers but also `14.4k` and
`28.8k` suffix notation and the words `to` in `Autobaud range: 9600 to 28.8k`; single-quoted
`'DIX'` appears inside a bare (not string-quoted) line.

### c.5 Character sets (L348-357)
`Character Sets Supported:` then 6 lines: `ISO 10646 (UTF-8)`, `IBM/Microsoft DBCS`,
`JIS X 0208`, `ISO 8859-1`, `ISO 10646 (UCS-4)`, `ISO 10646 (UCS-2)`. (Clause 4 prints
`UCS2` without hyphen.) Free text lines with parentheses; no quotes.

### c.6 Special functionality (L365-377)
Heading `Special Functionality:`; entries:

```
Maximum APDU size in octets: 1476
Segmented Requests Supported, window size: 8
Segmented Responses Supported, window size: 8
Router
BACnet/IP BBMD
BACnet/IPv6 BBMD
BACnet/SC Hub
BACmet/SC Direct Connect
```

Keyword-with-integer lines (`label: <integer>`) and bare flags. Typo `BACmet/SC Direct
Connect` (Clause 4: `BACnet/SC Direct Connect`). Clause 4 prints `BACnet/IPV6 BBMD`
(capital V); Annex `IPv6`.

### c.7 Default property value restrictions (L382-394)

```
unsigned-integer: <minimum 0; maximum 4294967295>
signed integer: <minimum -2147483647; maximum 2147483647>
real <minimum -3.40282347E38; maximum 3.40282347E38; resolution 0.01>
double <minimum -1.7976931348623157E308; ...; resolution 0.0001>
date: <minimum 01-January-1970; maximum 31-December-2038>
octet-string: <maximum length string 512>
character string: <maximum length string 255>
list: <maximum length list 10>
variable-length array: <maximum length array10>
```

Very different from Clause 4.4.2/4.5.8 (see section e).

### c.8 Conformance / profile / protocol-revision lines
None exist as sections. `protocol-version: 1` and `protocol-revision: 4` appear only as
Device object properties in the test database (L657-658; both integers). No profile
section; `profile-name: ""` appears as an object property (accumulator, pulse-converter,
schedule, trend-log). No `Fail Times` section.

## d. Test Database notation inventory

### d.1 Object types represented (25 objects, one each) and identifier form

`accumulator`, `analog-input`, `analog-output`, `analog-value`, `averaging`, `binary-input`,
`binary-output`, `binary-value`, `calendar`, `Command`, `device`, `event-enrollment`, `file`,
`Group`, `life-safety-point`, `life-safety-zone`, `loop`, `multi-state-input`,
`multi-state-output`, `multi-state-value`, `notification-class`, `Program`, `pulse-converter`,
`schedule`, `trend-log`.

Not represented despite the 64 object types declared supported: all types from `Event Enrollment`
onward in the supported list that are not above (Global Group, Trend Log Multiple, Load Control,
Structured View, Access *, Timer, *Value primitives, Notification Forwarder, Alert Enrollment,
Channel, Lighting Output, Binary Lighting Output, Network Port, Elevator Group, Escalator, Lift,
Staging, Audit Log, Audit Reporter, Color, Color Temperature, Event Log). So the "at least one of
every kind of object type" comment is false for 2025 types, and the Annex violates the
5(g) consistency rule (every supported type has an instance), see doc 03.

### d.2 Container and object header

```
List of objects in test device:      <- heading (L403)
{                                    <- list open
  {                                  <- object open (L405)
   object-identifier: (accumulator, 1)
   object-name: "meter 1"
   object-type: ACCUMULATOR
   ...
  },                                 <- object close WITH trailing comma
  ...
  }                                  <- last object close, NO comma
}                                    <- list close
```

- Every object follows the Clause 4 order: `object-identifier`, `object-name`, `object-type`
  as the first three properties (all 25 objects conform).
- Objects are separated by `},` except the last (`}`), but the comma is optional-looking
  (trend-log L1037 opens after `},` and the final close has none).
- Brace placement/indentation varies wildly per object (0-10 spaces); the open `{` is always
  alone on its line.
- `object-identifier` value is a parenthesised pair `(type, instance)`:
  `(analog-input, 1)`. Type token forms: lower-case hyphenated (`analog-input`), capitalised
  (`Command` L632, `Group` L767, `Program` L959, `Device` in L727), and with a space
  (`analog input` in L1042). Whitespace after the comma is optional: `(multi-state-output,1)`,
  `(Device,1)`.
- `object-type` value is UPPER_SNAKE enumeration: `ANALOG_INPUT`, `MULTI_STATE_INPUT`,
  `EVENT_ENROLLMENT`, `LIFE_SAFETY_POINT`, `PULSE_CONVERTER`, `TREND_LOG`, `DEVICE`. It must be
  matched to the identifier's type with `_`/`-`/case normalisation (and, for L1042-style,
  space).

### d.3 Property line syntax

`<property-name>: <value> [W|R]`, property names are lower-case hyphenated by default with
exceptions listed in d.17. Mixed case: `COV-increment` (L456, L501, L872) next to `cov-increment`
(L992); `max-APDU-length-accepted`; `maximum-value_Timestamp` (underscore + capital T, L522). Space
after the colon is usually present but not always: `local-time:?` (L717),
`priority-array:{NULL,...` (L916). One property is prefixed by U+2026: `…protocol-services-supported:`
(L660). The property name is followed by value on the same line, EXCEPT for multi-line values
where the opening brace/paren is on the next line (`protocol-services-supported:`, `protocol-object-types-supported:`,
`object-list:` in the Device object, L660-710) or on the same line with continuation lines.
Property lines are not separated by commas.

### d.4 Writable markers

- Suffix `W` after the value, separated by a space: `object-name: "1AH1MAT" W` (L442),
  `value-set: 67 W` (L422), also AO L471, AV L490, Device L648 `object-name`.
- Suffix `R` after a value: `priority-array: {?, ?, ...} R` (L484, L499). Clause 4 defines `W`
  and `C` only; `R` is not defined there. `C` is NOT used anywhere in the Annex.
- Markers always sit at end of the logical property value (after the closing brace of the value).
- Markers appear on only 7 property lines (5 W, 2 R); the Annex otherwise leaves almost all
  properties unmarked even though the template comment L401 says "All property values that
  are writable should be followed by a W".

### d.5 Strings
Double quoted only, single line: `"meter 1"`, `""` (empty, many), `"Floor 3, West Zone Smoke
Detector"` (commas inside), `"V4.0 - April 12, 2005"`, `"1.2 "` (trailing space preserved), `"2-speed Fan#1"`,
`"Fourth Floor, West Wing Office Suite"`. No single-quote/accent-grave strings and no embedded
quotes are in the Annex. Strings are also used in lists: `{"Off","On_Low","On_High"}`,
`{"Unoccupied", "Occupied"}`. `instance-of: "ThreeWayAverager"`.

### d.6 Numbers
- unsigned/signed integers: `125`, `-50.0` (real), `4294967295` (only in restrictions).
- reals always with decimal point and digits on both sides: `58.1`, `0.2`, `-50.0`, `6.0`, `1000.0`.
- scientific notation appears only in restrictions (L386-387): `-3.40282347E38`,
  `1.7976931348623157E308`.
- Reals where an integer might be expected: `utc-offset: 6.0`, `present-value: 125.0`.
- No `NaN`/`INF` forms.

### d.7 Booleans
`TRUE`/`FALSE` only (never `T`/`F` as scalar values), e.g. `out-of-service: FALSE`,
`present-value: TRUE` (calendar, L627).

### d.8 Bit strings
Curly-brace lists of TRUE/FALSE: `status-flags: {FALSE,FALSE,FALSE,FALSE}`, with or without
spaces after commas, e.g. `limit-enable: {TRUE, TRUE}`, `event-enable: {TRUE, FALSE, TRUE}`.
- Abbreviated `T`: the Device `protocol-services-supported` and `protocol-object-types-supported`
  are multi-line bit strings of `T, T, ...` with trailing `--` comments after each row
  (L660-681).

```
protocol-services-supported:
{
  T, T, T, T, T, T,       -- Alarm and event
  ...
  T                       -- GetEventInfo
}
```

  Comments occur between rows INSIDE the braces (so the lexer must treat comments as whitespace
  inside values). Note this bit string is only 40 bits of T; every bit set to T, none `F`.
- `?` as a bit value in bit strings: none, but `?` appears as array elements (d.12).
- Bit strings written with PARENTHESES in one spot: `(TRUE, TRUE, FALSE)` at the last
  recipient in `recipient-list` (L954) instead of `{TRUE, TRUE, FALSE}`.
- Named-bit bit string (day names): `{Monday, Tuesday, Wednesday, Thursday, Friday}` in
  `recipient-list` (valid-days). This is a list of NAMED bits (only the set bits listed),
  not TRUE/FALSE values.
- `event-time-stamps: {6,3,5}` etc. are NOT bit strings (see d.11).
- Missing comma typo: `status-flags: {TRUE FALSE, FALSE, FALSE}` (L820).

### d.9 Enumerations
Bare upper-case words, both `_` and `-` forms in the SAME file for the same kind of value:
`reliability: NO-FAULT-DETECTED` (L414, L449, L478, L496, L540, L983) vs `NO_FAULT_DETECTED` (many). Similarly
`units: DEGREES-FAHRENHEIT` / `POUNDS-FORCE-PER-SQUARE-INCH` (hyphens) vs `KILOWATT_HOURS`,
`LITERS_PER_HOUR`, `PSI_PER_DEGREE_FAHRENHEIT` (underscores). `segmentation-supported:
segmented-both` and `vt-classes-supported: (DEFAULT-TERMINAL, DEC-VT100)` use lower-case and
hyphenated forms. `mode: ON`, `polarity: NORMAL`, `NULL` as enum-like. No `proprietary` values.

### d.10 Dates
- With weekday: `(Tuesday, 2-January-2007)`; weekday with no space: `(Monday,24-January-1998)`.
- Without weekday: `(23-March-1995)`, `(1-January-1995)`.
- Wildcard date: `(*-*-*)` (L436 etc.). Wildcard time: `*:*:*.*`. The pair
  `{(*-*-*),*:*:*.*}` is a fully-wild BACnetDateTime.
- Day without leading zero everywhere (`1-January-1995`) and with in restrictions
  (`01-January-1970`), restriction dates are NOT parenthesised (L388).
- Date range: `{(5-September-1995)-(10-June-1996)}` (effective-period, L1014): two dates joined
  by `-` inside braces.
- Date in list: `date-list: ((19-February-1995),(28-May-1995),{(24-December-1995)-(4-January-1996)})`
  mixes single dates and a range (range wrapped in `{}` while the list is `()`).
- Month names are full English names with a hyphen delimiter. No numeric months.

### d.11 Times, date-times and timestamps
- Times: `9:39:21.02`, `18:50:21.2` (1-digit hundredths), `00:00:00.0`, `19:01:34.0`,
  `13:15:07.32`; hour with/without leading zero; HH:MM only in schedules: `{8:00,ACTIVE}`,
  `6:00`, `20:00`, `24:00` (L954), `0:00`.
- Date-time in braces: `{(Tuesday, 2-January-2007), 9:39:21.02}` (`value-change-time`).
- Date-time in PARENTHESES with a single comma: `(16-December-1999,13:15:07.32)`
  (`minimum-value-timestamp`, `maximum-value_Timestamp`).
- `event-time-stamps` (array of 3 BACnetTimeStamp) shows ALL THREE CHOICEs:
  - sequence number: `{6,3,5}` (L511)
  - time only: `{09:02:31.05,14:07:21.57,13:33:02.82}` (L556)
  - date-time: `{{(Monday,24-January-1998),18:50:21.02},{(*-*-*),*:*:*.*},{(23-March-1998), 19:01:34.0}}`
  Choices are NOT tagged with `[n]` context notation as 4.4.1(b) would suggest. Also a
  mixed array where one element lacks a weekday.
- `event-time-stamps` wraps onto a second line in places (L435-436, L1003-1004, L1057-1058).

### d.12 Arrays and lists
- Arrays use `{ }`; lists use `( )`. Both appear. Examples:
  - array of 3 reals/ints `priority: {3, 10, 10}`; `ack-required: {TRUE, TRUE, TRUE}`;
  - priority-array (16 elements) of `NULL`s with a real value or enum in one slot:
    `priority-array: {NULL, ..., 2, NULL, ...}` (multi-line, L916-917), or 16 `?`:
    `{?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?} R`;
  - list of enums `(ALARM)`, `(PREALARM)`, `(FAULT)`, list of ints `(3)`, `(2)`;
  - list of object ids `((life-safety-zone, 5))`, `((life-safety-point, 22),(life-safety-point, 23))`;
  - empty list `()`: `log-buffer: ()` (L1046) and in a comment `-- device-address-binding: () --empty list example`;
  - multi-line list of object identifiers (Device `object-list`, braces `{ }` NOT parens, L684-710:
    `{ (accumulator, 1), ..., (trend-log, 1), }`), with trailing comma before the closing brace.
- Weekly schedule: array of 7 lists-of-time-value pairs:
  `weekly-schedule: { ({8:00,ACTIVE},{17:00,INACTIVE}), ({8:00,ACTIVE}), ... }` (outer `{}`,
  inner day `()` list, each time-value `{}`).
- Both `{...}` and `(...)` used around list/array values for the same datatype across
  properties (`configuration-files: {(file,1),...}` uses `{}`, `member-of: ((life-safety-zone, 5))`
  uses `()`). The parser cannot infer array vs list from the delimiter alone.
- Trailing comma in a list/array: `configuration-files: {(file, 1),(file, 2),(file, 3),}`
  (L731) and `object-list` (L710), while `(multi-state-value, 1)` lacks the separating comma (L706).

### d.13 Constructed values
Curly braces with comma separated elements; nesting arbitrary:
- `prescale: (1,10000)` (PARENTHESES for a SEQUENCE; Clause 4 says `{}`).
- `logging-record: {{(Tuesday, 2-January-2007), 9:39:33.01}, 0, 27,NORMAL}` (nested datetime then
  scalars including an enum).
- `object-property-reference: {(analog-input, 2), present-value}` (object-id + property name
  enumeration, the property is a bare lower-case token, no property-array-index).
- `object-property-reference: (analog-input, 12)` in the Averaging object is only an object id.
- `log-deviceobjectproperty: {(device, 100), (analog input, 3), present-value}`.
- `event-parameters: {30, 65.0, 85.0, 0.25}` (the CHOICE alternative is not named or tagged).
- `list-of-session-keys: ({X'3799246237984589', {1, X'3'}}, {X'4446214686489744',{ 1, X'5'}})`.
- `device-address-binding: ({(Device,1), {1, X'1'}}, {(Device,12),{1, X'23'}}, {(Device,40),{2, X'02608C41A606'}})`.
- `active-cov-subscriptions: ({{(device, 12), 300},{(analog-input, 1),present-value},TRUE,100,1.0}, ({(device, 40), 600},...)`.
- `list-of-group-members: ( {(analog-input, 8),(present-value, reliability, description)}, ... )` with a
  parenthesised LIST of property names nested in a brace record, multi-line with the opening
  `(` at end of the property line.
- `recipient-list: ( {{Monday,...,Friday}, 6:00, 20:00, (device, 12), 21, TRUE, {TRUE,TRUE,TRUE}}, ... )`
- `exception-schedule: { {(23-November-1995),({0:00,INACTIVE}),10}, {(calendar, 1),({0:00,INACTIVE}),11}, {{(5-March-1996)-(7-March-1996)},({9:00,ACTIVE},{14:00,INACTIVE}),6} }`
  The first element of each entry is a CHOICE with three untagged forms: a date `(...)`, an
  object id `(calendar, 1)`, and a date range `{(...)-(...)}`.
- Command `action` (L639-642), with EMPTY fields between commas for omitted optionals:
  `action: { ({,(analog-value, 5),present-value,,65.0,,,TRUE,TRUE},{,(binary-output, 3),present-value,,
  INACTIVE,8,1,TRUE,TRUE}), ({...}) }` (a leading comma `{,`, double commas `,,` and `,,,`).
  The structure spans several physical lines.

### d.14 "?" values
- Whole value unknown: `local-time:?` (no space), `local-date: ?`, `present-value: ?` (Group,
  L778).
- Per-element: `priority-array: {?, ?, ..., ?} R`.
- Never inside bit strings or as `T,T,?`.

### d.15 Octet strings
`X'3799246237984589'`, `X'3'` (ODD number of hex digits!), `X'5'`, `X'23'`, `X'02608C41A606'`.
Only single-quote delimiters; upper-case hex; no spaces in digits.

### d.16 Object identifiers in values
`(device, 12)`, `(file, 1)`, `(life-safety-zone, 5)`, `(calendar, 1)`, `(binary-output, 9)`,
`(trend-log, 3)`; always parenthesised. Mixed case type `(Device,1)`. A missing instance:
`(life-safety-zone),` (L701; typo).

### d.17 Limits (min/max) in the test database
NONE. No `<...>` restriction statements appear on any property in the test database; they
exist only in the Default Property Value Restrictions section (c.7). `min-pres-value`,
`max-pres-value` are ordinary properties, not restrictions.

### d.18 Comments
- Full-line `--` comments between sections and inside Device bit strings.
- Trailing comment on a bit-string row: `T, T, T, T, T, T,   -- Alarm and event`.
- Comment on a line with a property: `-- device-address-binding: () --empty list example`
  (a commented-out property; a second `--` inside the comment, no space after it).
- The bare line `--` (L4).

### d.19 Other distinctive notation
- Property value begins on next line (`protocol-services-supported:` then `{`).
- Properties whose values wrap across lines: `event-time-stamps`, `priority-array`,
  `action`, `weekly-schedule`, `exception-schedule`, `recipient-list`, `device-address-binding`,
  `active-cov-subscriptions`, `list-of-group-members`.
- Odd indentation of a single property (`effective-period` at L1014 is indented ~25 spaces).
- Object member property order is not strictly alphabetical; also repeats of `notification-class`
  as BOTH a property of Notification Class (`notification-class: 1`) and event-generating objects.
- `description` before `device-type` etc. -- no required order beyond the first three.
- Duplicate property names within one object: none found.
- Property named `action` is an enumeration (`DIRECT`) in Loop and a list in Command.
- `present-value` type varies by object (real, enum, int, bool, `?`).
- Property names `log-deviceobjectproperty` (single token) and `list-of-session-keys` are used.

## e. Notation in the example likely NOT covered by Clause 4 rules

Line references are to `annexA-clean.epics`.

1. Section `Fail Times:` is absent (entire section missing; L1-1063), though 4.5.9 defines it.
2. `Creatable` spelling vs `Createable` (L254-319).
3. `R` marker after a property value (L484, L499); Clause 4 only defines `W` and `C`.
4. Default restrictions syntax differs from 4.4.2 / 4.5.8 (L384-393):
   - no colon after restriction names (`minimum 0`, `maximum length string 512`) where 4.4.2 uses
     `minimum: 0`;
   - heading names without colon `real <...>` (L386, L387) or with space `signed integer:`,
     `character string:`, `variable-length array:` vs Clause `signed-integer`, `character-string`,
     `variable-length-array`;
   - `maximum length array10` (no whitespace, L393);
   - scientific notation reals (`3.40282347E38`) which 4.4(e) does not define;
   - unparenthesised dates (`01-January-1970`) which 4.4(j) says are parenthesised.
5. Data link lines not in the Clause list or syntax: `BACnet/IP, PPP Other`, `LonTalk`,
   `Point-To-Point. EIA 232, Baud rate(s)` (no value), `14.4k`/`28.8k` suffixes and
   `Autobaud range: 9600 to 28.8k` (L322-346). `ISO 8802-3, Fiber` capitalisation.
6. `BACnet/IPv6 BBMD` vs Clause `BACnet/IPV6 BBMD` (case-insensitive probably) and the
   `BACmet/SC Direct Connect` typo (L374).
7. Heading `Special Functionality:` etc. fine; but heading `List of objects in test device:` is
   case-different (L403).
8. Object type suffix text `Event log` lower-case `l` (L264); `Characterstring Value`,
   `Octetstring Value`, `Bitstring Value` spellings (L296-306).
9. Object-identifier forms not defined: capitalised type (`Command`, `Group`, `Program`,
   `Device`), a space inside the type (`analog input`, L1042), missing instance
   `(life-safety-zone),` (L701), no space after the comma.
10. Enumeration names mixing `-`/`_` is covered by 4.4(i), BUT enumerations written in lower case
   (`segmented-both`), `ON`, and `NULL` as an enum member need case folding; `units` names like
   `DEGREES-FAHRENHEIT` are fine.
11. Property names: mixed case (`COV-increment`), underscore (`maximum-value_Timestamp`, L522),
    leading ellipsis (`…protocol-services-supported`, L660), no space after colon
    (`local-time:?` L717, `priority-array:{` L916).
12. Constructed value delimiters: parentheses for SEQUENCEs (`prescale: (1,10000)` L418), parentheses for lists as 4.4.1(c) says (`vt-classes-supported`, `member-of`), braces for list-like values (`object-list`, `configuration-files`).
    Clause 4.4(m) says constructed items use `{ }`, 4.4.1(c) says lists use `( )`; the Annex mixes.
    Includes `(TRUE, TRUE, FALSE)` bit string in parens (recipient-list).
13. Date-time in parentheses `(16-December-1999,13:15:07.32)` (L519, L522) vs braces
    `{(date),time}` elsewhere.
14. Times without seconds (`8:00`, `24:00`, `0:00`) and with single-digit fraction (`18:50:21.2`);
    4.4(k) mandates `hh:mm:ss.xx`.
15. Date ranges `(d1)-(d2)` and mixing dates, ranges and calendar references untagged in
    one list (L628, L1014, L1024-1026).
16. BACnetTimeStamp CHOICE as bare sequence numbers / bare times (`{6,3,5}`, L511; L556) without
    `[n]` context tags that 4.4.1(b) calls for.
17. Named-bit string (`{Monday, Tuesday, ...}`) in bit strings: 4.4(h) defines only T/F lists.
18. Empty list elements (`{,(analog-value, 5),present-value,,65.0,,,TRUE,TRUE}`, L639-642) for
    omitted OPTIONAL fields; not in Clause 4.
19. Odd-length octet strings `X'3'`, `X'5'` (L724).
20. Trailing commas (`{(file,1),...,(file,3),}` L731; `object-list` L710), missing commas
    (L706, L820), stray closers (`19:01:34.0)}}` L802/L834, `{00:00,INACTIVE{),` L1020).
    These are typos in the standard; a strict parser rejects them, a lenient one repairs them.
21. Comments INSIDE a multi-line value (between rows of a bit string, L660-681); 4.2 treats
    comments as whitespace, so this is covered, but the lexer must do it before brace matching.
22. A property value starting on the line AFTER the property name (`protocol-services-supported:`
    then `{`, L660-661); covered by whitespace rules but affects line-based parsers.
23. `T, T, ...` abbreviated booleans in bit strings (covered) but with a bit-string whose LENGTH
    (40/25 here) doesn't match the current BACnetServicesSupported size; semantic, not syntactic.
24. Semantic inconsistencies useful for consistency testing: Device `object-list` lists
    `(file, 1)`, `(life-safety-point, 1)`, `(life-safety-zone)`, `(schedule, 1)` while the database
    objects are `(file, 7)`, `(life-safety-point, 2)`, `(life-safety-zone, 2)`, `(schedule, 2)`;
    64 supported object types vs 25 represented; BIBBs claimed without matching services.
25. `W` on `object-name` (L442 etc.) is a legal use but the template says writable properties
    need `W` while the example has almost none.

## f. Statistics

- Objects in test database: 25 (one per type, listed in d.1).
- Property lines inside objects (every `name:` line, including `object-identifier`,
  `object-name`, `object-type`): 491.
- Non-database list sizes: 177 BIBBs, 46 services (all `Initiate Execute`), 64 object types
  (63 `Creatable Deleteable` + `Device`), 21 data link lines, 6 character sets, 8 special
  functionality lines (+ heading), 9 default restriction lines.

Per object (line range start, property-line count):

| Object | Start line | Property lines |
|---|---|---|
| accumulator | 406 | 31 |
| analog-input | 441 | 26 |
| analog-output | 470 | 16 |
| analog-value | 489 | 23 |
| averaging | 515 | 14 |
| binary-input | 532 | 25 |
| binary-output | 560 | 29 |
| binary-value | 592 | 27 |
| calendar | 623 | 6 |
| Command | 632 | 9 |
| device | 647 | 32 |
| event-enrollment | 739 | 12 |
| file | 754 | 10 |
| Group | 767 | 6 |
| life-safety-point | 782 | 28 |
| life-safety-zone | 814 | 25 |
| loop | 844 | 35 |
| multi-state-input | 882 | 19 |
| multi-state-output | 904 | 20 |
| multi-state-value | 928 | 11 |
| notification-class | 942 | 8 |
| Program | 959 | 13 |
| pulse-converter | 975 | 30 |
| schedule | 1009 | 14 |
| trend-log | 1037 | 22 |

Counts per object type: 1 each (25 types x 1). Markers: 5 `W`, 2 `R`, 0 `C`. Restriction
statements `<...>` in the test database: 0. `?` values: 3 whole-property (`local-time`,
`local-date`, Group `present-value`) plus two 16-element priority arrays of `?`.

## g. Distinct property identifiers and enumeration literals

### g.1 Property identifiers (169 distinct spellings, exact)

```
COV-increment ack-required acked-transitions action action-text active-cov-subscriptions
active-text adjust-value alarm-value alarm-values all-writes-successful apdu-segment-timeout
apdu-timeout application-software-version archive attempted-samples average-value
backup-failure-timeout bias buffer-size change-of-state-count change-of-state-time
configuration-files controlled-variable-reference controlled-variable-units
controlled-variable-value count count-before-change count-change-time cov-increment cov-period
database-revision date-list daylight-savings-status deadband derivative-constant
derivative-constant-units description description-of-halt device-address-binding device-type
direct-reading effective-period elapsed-active-time error-limit event-enable event-parameters
event-state event-time-stamps event-type exception-schedule fault-values feedback-value
file-access-method file-size file-type firmware-revision high-limit in-process inactive-text
input-reference instance-of integral-constant integral-constant-units last-notify-record
last-restore-time life-safety-alarm-values limit-enable limit-monitoring-interval
list-of-group-members list-of-object-property-references list-of-session-keys local-date
local-time location log-buffer log-deviceobjectproperty log-enable log-interval logging-object
logging-record low-limit maintenance-required manipulated-variable-reference max-APDU-length-accepted
max-pres-value maximum-output maximum-value maximum-value_Timestamp member-of min-pres-value
minimum-off-time minimum-on-time minimum-output minimum-value minimum-value-timestamp mode
model-name modification-date notification-class notification-threshold notify-type
number-of-APDU-retries number-of-states object-identifier object-list object-name
object-property-reference object-type operation-expected out-of-service output-units polarity
prescale present-value priority priority-array priority-for-writing profile-name program-change
program-location program-state proportional-constant proportional-constant-units
protocol-object-types-supported protocol-revision protocol-version pulse-rate read-only
reason-for-halt recipient-list record-count records-since-notification reliability
relinquish-default resolution scale scale-factor schedule-default segmentation-supported
setpoint setpoint-reference setting silenced state-text status-flags stop-when-full
system-status time-delay time-of-active-time-reset time-of-state-count-reset total-record-count
tracking-value units update-interval update-time utc-offset valid-samples value-before-change
value-change-time value-set vendor-identifier vendor-name vt-classes-supported weekly-schedule
window-interval window-samples zone-members …protocol-services-supported
```

(The last entry carries the leading U+2026; ignoring it gives 168 distinct names.)
Case-variant pair: `COV-increment` / `cov-increment`. Quirk spellings: `maximum-value_Timestamp`,
`max-APDU-length-accepted`, `log-deviceobjectproperty`.

### g.2 Enumeration literals observed (scalar/enum values, exact)

object-type values (UPPER_SNAKE): `ACCUMULATOR ANALOG_INPUT ANALOG_OUTPUT ANALOG_VALUE AVERAGING
BINARY_INPUT BINARY_OUTPUT BINARY_VALUE CALENDAR COMMAND DEVICE EVENT_ENROLLMENT FILE GROUP
LIFE_SAFETY_POINT LIFE_SAFETY_ZONE LOOP MULTI_STATE_INPUT MULTI_STATE_OUTPUT MULTI_STATE_VALUE
NOTIFICATION_CLASS PROGRAM PULSE_CONVERTER SCHEDULE TREND_LOG`.

Other enumerations by property:

| Property | Literals seen |
|---|---|
| `event-state` | `NORMAL`, `OFFNORMAL`, `HIGH_LIMIT`, `LIFE_SAFETY_ALARM` |
| `reliability` | `NO-FAULT-DETECTED`, `NO_FAULT_DETECTED` |
| `units` / `*-units` | `KILOWATT_HOURS`, `DEGREES-FAHRENHEIT`, `PERCENT`, `BTUS_PER_POUND_DRY_AIR`, `PERCENT_OBSCURATION_PER_METER`, `LITERS_PER_HOUR`, `POUNDS-FORCE-PER-SQUARE-INCH`, `PSI_PER_DEGREE_FAHRENHEIT`, `PER_MINUTE`, `NO_UNITS` |
| `notify-type` | `ALARM`, `EVENT` |
| `present-value` (binary/schedule) | `ACTIVE`, `INACTIVE` (also `alarm-value`, `feedback-value`, `relinquish-default`, `schedule-default`) |
| `polarity` | `NORMAL`, `REVERSE` |
| `system-status` | `OPERATIONAL` |
| `segmentation-supported` | `segmented-both` (lower case) |
| `vt-classes-supported` | `DEFAULT-TERMINAL`, `DEC-VT100` |
| `event-type` | `OUT_OF_RANGE` |
| `file-access-method` | `RECORD_ACCESS` |
| `present-value` / `tracking-value` / `alarm-values` (life safety) | `PREALARM` |
| `life-safety-alarm-values` | `ALARM` |
| `fault-values` | `FAULT` |
| `mode` | `ON` |
| `silenced` | `SILENCE_AUDIBLE`, `UNSILENCED` |
| `operation-expected` | `RESET_ALARM`, `SILENCE_AUDIBLE` |
| `maintenance-required` | `NONE` |
| `action` (Loop) | `DIRECT` |
| `program-state` / `program-change` | `RUNNING` / `READY` |
| `reason-for-halt` | `NORMAL` |
| `logging-record` (element) | `NORMAL` |
| `priority-array` elements | `NULL` |
| Day names (named bits in `recipient-list`, and in dates) | `Monday` `Tuesday` `Wednesday` `Thursday` `Friday` `Saturday` `Sunday` |
| Month names in dates | `January` `February` `March` `May` `June` `September` `November` `December` |

Property names used as enum values (`present-value`, `reliability`, `description`) in
`object-property-reference` / `list-of-group-members`.

## h. Recommendations for a synthetic fixture corpus

Do not ship Annex A. Write original fixtures (invented vendor, object names, values) that exercise
every pattern. Suggested layout `tests/fixtures/epics/`:

1. `minimal.tpi` - header, signature, general info, empty `{}` sections, empty database list
   `{ }`; terminator.
2. `sections_full.tpi` - every section with synthetic content: BIBBs (include 3-hyphen names),
   services showing `Initiate` only / `Execute` only / both / single-space overflow, object types
   with both `Createable` and `Creatable` spellings, data link lines (MS/TP with and without
   baud values, `14.4k` suffix, `Autobaud range: A to B`), charsets, special functionality, default
   restrictions in BOTH the Clause 4 colon form and the Annex colon-less form.
3. `objects_by_type.tpi` - at least one object for each of the 25 types seen, plus a few
   not in the Annex (to prove the parser is type-agnostic).
4. `values_scalar.tpi` - one property per scalar form: empty string, comma-containing string,
   trailing-space string, single-quote and accent-grave strings, `T`/`F`/`TRUE`/`FALSE`, ints,
   negative ints, reals (`6.0`, `-50.0`, `1.5E3` as an extension), octet strings (even and odd
   digit counts, upper/lower hex, single-quote and accent-grave), enum names with `_`, `-`,
   lower case and proprietary (`proprietary-object-type-653`), `NULL`, `?`.
5. `values_time.tpi` - dates with/without weekday, `*` wildcards, ranges, restriction-style
   unparenthesised dates, times `h:mm`, `hh:mm:ss.x`, `hh:mm:ss.xx`, wildcard times, date-times
   in `{}` and `()`, timestamp choices (sequence number / time / datetime / tagged `[n]`).
6. `values_constructed.tpi` - nested `{}`/`()` (SEQUENCE, list, array); empty list `()`;
   empty array `{}`; empty elements (`{,x,,y,,,z}`) as in an action list; arrays of 16 `?`
   with `R`; priority arrays of `NULL` with one value; named-bit strings; multi-line values with
   continuation lines; comments inside values; property value starting on the next line;
   trailing and missing commas (leniency tests, in separate files flagged `strict=reject`).
7. `markers.tpi` - `W`, `C` (+ trailing comment explaining the governing condition), `R`
   (flagged as non-standard), and restriction statements `<minimum: 0; maximum: 10>` per 4.4.2
   (none exist in the Annex so these must be synthesised from the Clause text).
8. `identifier_forms.tpi` - `(analog-input, 1)`, `(Analog_Input,1)`, `(analog input, 3)`,
   `(Command, 1)`, `(proprietary 700,1)`, missing instance (reject).
9. `case_and_layout.tpi` - upper-case keywords, `Heading:` followed by value on the same line
   vs `{` next line, tabs, CRLF and LF line endings, no space after the colon, mixed indentation,
   `Heading : {` spacing variations, blank lines inside lists.
10. `encodings/` - `PICS 0` UTF-8, `PICS 3`/`PICS 4` UTF-16/32 variants of the same minimal file.
11. `negative/` - one file per defect: missing signature, missing terminator, wrong first three
    properties, unbalanced braces (like the Annex typos `{00:00,INACTIVE{)`), stray `)`.
12. `consistency/` - objects declared supported but missing from the database, Device
    `object-list` that disagrees with database instances (as in Annex A), BIBBs vs services.

Parser design cues drawn from the Annex:

- Tokenise with comments and whitespace removed BEFORE bracket matching; track brace/paren
  nesting for multi-line values rather than relying on line ends.
- Property lines can only be recognised by `identifier ':'` at the top nesting level of an object.
- Keep the raw text of every value alongside the typed parse; many Annex values are typed
  ambiguously (arrays vs lists, parens vs braces) and a type-directed second pass (driven by a
  property/datatype table) is required.
- Provide a "lenient/repair" mode for the Annex-style typos and a "strict" mode.
- Normalise enumeration names by lower-casing and mapping `_`/`-`/space to one form.
- Treat markers (`W`, `C`, `R`) as a trailing token on the logical value after the last closing
  delimiter.
