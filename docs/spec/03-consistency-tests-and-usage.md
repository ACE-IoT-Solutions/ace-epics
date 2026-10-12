# 135.1-2025: EPICS Consistency Tests (Clause 5) and How Other Clauses Consume the EPICS

Source: ANSI/ASHRAE 135.1-2025 clauses 3, 5, 6, 7.1, 7.2, 14 (paraphrased). "Inferred" marks anything not stated in the text.
Clause 5 is only ~1.5 pages: items (a) through (r). It states no severities; every item is a "shall", so all are errors unless noted. Warning levels below are inferred.

## 1. Clause 5 consistency checks (all 18 items, (a)-(r))

Clause 5 intro: these are static checks on the EPICS only; the IUT is never interrogated. "Test database" (cl. 3.1) = the database of objects/functionality built from reading the EPICS. "Supported" object type = it can be made to exist in the IUT's database (note on (f)/(g)).

| ID | Ref | Rule | Cross-checks | Pass/fail | Severity |
|---|---|---|---|---|---|
| C5-01 | 5(a) | Every object type required by the claimed BIBBs must be marked supported in "Standard Object Types Supported". | BIBB list (4.5.x BIBBs section) -> Standard Object Types Supported section. | Fail if a BIBB-required type is missing/unsupported there. | Error. Needs BIBB->object-type table (external, 135 Annex K). |
| C5-02 | 5(b) | At least one instance of each BIBB-required object type is in the test database. | BIBBs -> test database objects. | Fail if zero instances of any required type. | Error. Same external table. |
| C5-03 | 5(c) | Device.Protocol_Object_Types_Supported must set the bit for each object type required by BIBBs. | BIBBs -> Device object property in test DB. | Fail if a required type's bit is 0. | Error. |
| C5-04 | 5(d) | Every application service required by claimed BIBBs must be marked supported in "BACnet Standard Application Services Supported", with Initiate and/or Execute flags as the BIBB requires (A-side=initiate, B-side=execute; inferred mapping). | BIBBs -> Application Services section (per-service Initiate/Execute). | Fail if service absent or the required direction flag missing. | Error. Needs BIBB->service+direction table (external). |
| C5-05 | 5(e) | Device.Protocol_Services_Supported must have the bit set for each service the BIBBs require to be *executed*. | BIBBs -> Device.Protocol_Services_Supported. | Fail if a bit is 0. Only the execute side is demanded here (initiate has no bit). | Error. |
| C5-06 | 5(f) | Object types in "Standard Object Types Supported" correspond one-to-one with set bits of Device.Protocol_Object_Types_Supported. | Standard Object Types Supported section <-> Device property. | Fail on any type in one set but not the other. (Proprietary types are not covered by this wording; inferred: ignore them.) | Error. Needs object-type enumeration (external). |
| C5-07 | 5(g) | Each object type listed as supported must have at least one object in the test database. Exception: File may have zero instances if File objects are dynamically created and exist only transiently during Backup/Restore. | Standard Object Types Supported -> test database. | Fail if a supported type has no instance, except the File exception. | Error. The exception depends on a vendor statement; the EPICS format may have no explicit flag for "dynamically creatable File" (inferred: accept zero Files with a warning/annotation). |
| C5-08 | 5(h) | Device.Object_List entries correspond one-to-one with objects in the test database; proprietary objects must be in both. Properties of proprietary objects that are not required by 135 cl. 23.4.3 need not be in the test DB. | Device.Object_List <-> test DB object identifiers. | Fail if an object is in one but not the other (duplicates also fail, inferred). | Error. 23.4.3 is external. |
| C5-09 | 5(i) part 1 | For each test DB object, all properties required by 135 Clause 12 must be present. | Object type -> required property list -> object's properties. | Fail on any missing required property. | Error. Needs per-type, per-revision required-property table (external). |
| C5-10 | 5(i) part 2 | Standard properties not defined in the declared Protocol_Revision must not be present. | Property -> "introduced in revision"; Device.Protocol_Revision. | Fail if a property newer than the declared revision appears. | Error. Needs property introduction-revision metadata (external). |
| C5-11 | 5(i) part 3 | Where a supported property requires conditional presence of other properties, those must be present (e.g. Event_Detection_Enable implies reporting properties, Priority_Array implies Relinquish_Default, etc. - examples inferred). | Conditional-presence rules from Clause 12. | Fail if the dependent property is missing. | Error. Largest external rule set. |
| C5-12 | 5(j) | Each property that must be writable, or conditionally writable, must be marked writable (W) or conditionally writable (C) in the EPICS. | Property -> required-access (Clause 12) vs the EPICS writability flag. | Fail if marked read-only. | Error. Needs required-writability table (external); "required writable" depends on object type and can depend on e.g. Out_Of_Service. |
| C5-13 | 5(k) | Length of Protocol_Services_Supported bitstring equals bit count of BACnetProtocolServicesSupported for the declared Protocol_Revision. | Device.Protocol_Services_Supported length vs Protocol_Revision. | Fail on length mismatch (too short or too long). | Error. Needs per-revision bit counts (external). |
| C5-14 | 5(l) | Length of Protocol_Object_Types_Supported bitstring equals bit count of BACnetObjectTypesSupported for the declared revision. | Device.Protocol_Object_Types_Supported length vs Protocol_Revision. | Same. | Error. External per-revision counts. |
| C5-15 | 5(m) | Properties deprecated or removed must not appear for revisions after the one in which they were deprecated/removed. Wording is "after the Protocol_Revision in which ... deprecated or removed". | Property -> deprecated/removed-in revision; Protocol_Revision. | Fail if present at a later revision. Boundary (the revision itself) is ambiguous in the text: inferred, treat the revision of deprecation as still allowed. | Error. External metadata. Note overlap with C5-10 (both are revision/property tables). |
| C5-16 | 5(n) | If Protocol_Revision is present and >= 14, each test DB object's Property_List must have one entry per property present, including non-standard properties, except Object_Type, Object_Identifier, Object_Name and Property_List themselves. | Per object: Property_List value vs the set of properties in the EPICS. | Fail on mismatch. Note: proprietary properties need not appear in the EPICS (7.1.3), so statically only verifiable for properties that are listed (inferred). | Error. Conditional on revision >= 14. |
| C5-17 | 5(o) | If Device.Segmentation_Supported is SEGMENTED_BOTH or SEGMENTED_RECEIVE, Device.Max_Segments_Accepted must be > 1. | Device.Segmentation_Supported, Max_Segments_Accepted. | Fail if <= 1 (or absent; inferred, since property is needed to judge). | Error. Self-contained, no external knowledge beyond enum names. |
| C5-18 | 5(p) | Each property required to be read-only must not be marked W or C in the EPICS. | Required-read-only (Clause 12) vs EPICS flag. | Fail if marked writable/conditionally writable. | Error. External table; dual of C5-12. |
| C5-19 | 5(q) | Where the standard limits a property's value range, any value given in the EPICS must lie in that range. | Property value vs standard range (Clause 12 / datatype definitions). | Fail if out of range. "?" (unspecified) values are not checked (inferred). | Error. External. |
| C5-20 | 5(r) | Where the EPICS declares a restricted value range for a property, the restriction must lie inside the standard's allowable range and must contain the standard's minimal required range. | EPICS restrictions (4.4.2 / 4.5.8 default restrictions, per-property overrides) vs standard allowed range and minimal range. | Fail if the restriction exceeds the allowed range or fails to cover the minimum. | Error. External (the "minimal value range" is defined in Clause 12 text, in few places). |

Count note: 18 lettered items map to 20 checks because (i) is split in three.

Not in Clause 5 but cited in other clauses and relevant (inferred as additional checks worth adding as "extra" rules, not mandatory): Object_Identifier uniqueness; Device object identifier match; resolution/limits datatype consistency with 4.4.2; presence of Protocol_Revision absent (treated as "no Property_List requirement", per 7.1.3 conditionality).

## 2. How Clauses 7.1 / 7.2 consume the test database

### 2.1 "?" semantics (7.1.1 Notes to Tester)
- "?" in the EPICS as a property value means "unspecified": any value of the correct datatype matches in a read comparison. Library must represent an explicit `Unspecified` value distinct from "absent property" and distinct from NULL. It still carries a datatype (inferred from property definition).
- For ReadPropertyMultiple, a ReadAccessResult error with the expected class/code is also accepted. (Not an EPICS matter.)

### 2.2 Read tests (7.1.1)
- Iterate all objects in the IUT database and all properties of each object (so API: `iter_objects()`, `iter_properties(obj)`).
- A property "indicated as not accessible via ReadProperty" (EPICS flag) should return an error: READ_ACCESS_DENIED / PROPERTY class for Protocol_Revision >= 13; for older revisions a broader set of error classes (OBJECT or PROPERTY, any code; or SERVICES with SERVICE_REQUEST_DENIED or OTHER). The EPICS therefore needs a per-property "not readable via ReadProperty" marker (4.4 notation; inferred it is a property-level flag). API: `is_readable(obj, prop)`.
- Arrays too big for APDU/segmentation: test expects an Abort (SEGMENTATION_NOT_SUPPORTED or BUFFER_OVERFLOW) on the whole-array read, then reads index 0 which must equal the element count N "as indicated in the EPICS", then verifies each element 1..N. API: array length (index 0 value) and per-element values; whole array vs element access. Arrays in the EPICS must therefore carry their length (index 0 semantic = element count, unsigned).
- Otherwise whole-value compare against the EPICS value. Value comparison applies the 4.4.2 resolution rules (6.6.1): values are equal if identical after applying the resolution constraints; floats may be rounded/truncated; consistent behaviour required. API: `get_resolution(prop)` for Real/Double, and datatype-aware equality.
- Test steps use "REPEAT Y = (all properties in object X)" so the EPICS property set must be complete for standard properties (see 7.1.2).

### 2.3 Non-documented property test (7.1.2)
- Property IDs 0..511 except 8 (ALL), 80 (OPTIONAL), 105 (REQUIRED) and, when Protocol_Revision >= 20, a random sample of IDs in 4194304..(2^32 - 1), are read for tester-selected objects; each property not in the EPICS for that object must return PROPERTY/UNKNOWN_PROPERTY.
- Objects chosen: one instance per supported object type, plus one per *variant* (instances that differ in supported property set, allowed ranges, or writability). Library should expose `variants(object_type)` / a grouping of objects by signature (property set + ranges + writability). Inferred helper.
- API: `has_property(obj, prop_id)`; `properties_not_present(obj)` against the full set of standard property IDs; Protocol_Revision accessor.

### 2.4 Property_List verification (7.1.3)
- Skipped if Protocol_Revision absent or < 14.
- Object_Name (77), Object_Type (79), Object_Identifier (75), Property_List (371) appear in the EPICS but must not appear in the Property_List value.
- Proprietary properties supported by the object must appear in Property_List but need not appear in the EPICS. Order is irrelevant: compare as sets.
- The test reads Object_List, then each object's Property_List. Whole-array reads that exceed Max APDU are read element by element.
- Implication: the library's expected-Property_List = (EPICS property set minus the four above). Proprietary properties are a known incompleteness, so a static check can only assert subset, not equality (inferred; C5-16 wording says "one entry for each property present", i.e. equality over what is declared).

### 2.5 Write tests (7.2)
- Writable property = EPICS flag W (writable) and C (conditionally writable) both count for 7.2.2 "all writable properties". Read-only = neither W nor C (7.2.3). So API: `access(obj, prop) -> {R, W, C}`; `is_writable()` true for W or C; `is_read_only()` = not W and not C; separate `is_conditionally_writable()`.
- "Not currently writable" for a conditionally writable property: expect PROPERTY / WRITE_ACCESS_DENIED.
- Not run on any property in Network Port objects or on Device.Object_Identifier. API consumers can use a skip-list; the library may expose object type to allow filtering.
- Range tests (7.2.1) pick values from the limits the vendor gives in the EPICS (4.4.2), including defaults per datatype from 4.5.8 "Default Property Value Restrictions" (unsigned/signed min,max; real/double min,max,resolution; date min,max; octet-string / character-string max length; list max length; variable-length array max length), overridable per property in the test DB. API: `get_limits(obj, prop)` resolving per-property override else datatype default else standard range; returns min, max, resolution, max-length, allowed enumeration subset.
  - Enumerated/Boolean: test lowest, highest, mid-range of the defined enumerations after removing permitted restrictions (so the EPICS can restrict enumerations: expose allowed-value set).
  - Unsigned/Signed/Real/Double: upper, lower and two intermediate points; vendor supplies actual limits.
  - Octetstring/Characterstring: min length, max length, between. Vendor provides min and max lengths. If no fixed max, vendor supplies a practical max (no statement a longer string would be rejected). If Protocol_Revision >= 10 (UTF-8) at least one value must contain multi-byte characters.
  - Bitstring: one value different from current. Date: one different date. Time: explicit all-fields value differing by more than clock resolution; plus one value with an unspecified field (round-trips unchanged except Device.Local_Time, whose unspecified portion is a local matter).
  - Constructed datatypes: tester-chosen valid value.
  - Whole arrays are written without index where possible.
- After write, VERIFY (wait Internal Processing Fail Time, read back). Skip VERIFY for properties that an internal process changes after write (momentary pushbutton, Record_Count): EPICS or a tester-side table identifies these (not a stated EPICS field; inferred need for an "auto-resets" annotation).
- Read-only test (7.2.3): skipped if WriteProperty not supported (EPICS services section; API: `supports_service("WriteProperty", execute=True)`). Writes the read value and a different in-range value expecting WRITE_ACCESS_DENIED (PROPERTY class); acceptable alternates VALUE_OUT_OF_RANGE or RESOURCES/NO_SPACE_TO_WRITE_PROPERTY. For arrays, uses index 0 length then index 1. If AddListElement supported and property is a list (or array of lists), AddListElement must also error.
- Hence API needs: datatype of each property (list/array/scalar), whether the IUT supports AddListElement/WriteProperty, and Protocol_Revision.

### 2.6 Minimal query API implied
`epics.protocol_revision`; `epics.supports_bibb(name)`; `epics.supports_service(name, initiate|execute)`; `epics.supported_object_types`; `epics.objects()` / `objects(type)`; `obj.id`, `obj.type`, `obj.properties()`; `prop.value` (with Unspecified); `prop.access` (R/W/C, plus "not readable via ReadProperty"); `prop.limits` (merged defaults); `prop.is_array`, `prop.array_length`; `epics.timers[...]`; `epics.vendor_proprietary_flag`; `epics.device` shortcut; BIT-string helpers with length; object variants grouping.

## 3. Clause 6 extracts

### 3.1 Timers (6.3, EPICS 4.5.9)
Vendor provides each in the EPICS; datatype is Real; unit seconds. No default values are given by the standard (all must be provided; "A Real value in seconds must be provided for each timer").

Names in the 4.5.9 EPICS template (note wording differences vs 6.3):
1. Notification Fail Time (6.3.1): max delay until an event/COV notification must be transmitted after the condition is observable.
2. Internal Processing Fail Time (6.3.2): delay after a write/event until the property value is updated. EPICS value is the maximum for all situations; tests may use shorter values per test if harmless. Also the implicit wait before every VERIFY / READ (6.2.10, 6.2.13) and the default allowable delay for any RECEIVE (6.3.8).
3. Minimum ON/OFF Time (template label; 6.3.3 calls it "Minimum ON/OFF Fail Time"): max time after a min-on/min-off timer expires until priority-6 value is as expected.
4. Schedule Evaluation Fail Time (6.3.4): after a Calendar/Schedule property change or Local_Time change until Present_Value correct.
5. External Command Fail Time (6.3.5): Command object Present_Value change until first message of the new state is sent.
6. Program Object State Change Fail Time (6.3.6): write to Program_Change until expected program result.
7. Acknowledgement Fail Time (template spelling; 6.3.7 "Acknowledgment"): confirmed request transmitted until acknowledgement received. Used as `BEFORE Acknowledgment Fail Time ...`.
8. Subordinate Proxy Confirm Interval: in the 4.5.9 template only; no 6.3.x clause in the Clause 6 text provided (surprise/gap).
9. Unconfirmed Response Fail Time (6.3.9): unconfirmed request received until expected unconfirmed request out (e.g. I-Am after Who-Is).
10. Channel Write Fail Time (6.3.10): Channel Present_Value change until first write; for multiple targets, total allowed is target count x this value.
11. Auto Negotiation Fail Time (template; 6.3.11 "Autonegotiation Fail Time").
12. Activate Changes Fail Time (6.3.12): includes any device reset needed.
13. Foreign Device Registration Fail Time (6.3.13): Register-Foreign-Device sent until considered failed for lack of BVLC-Result.
14. Audit Notification Forwarder Fail Time (6.3.14): defined in Clause 6 but NOT in the 4.5.9 template shown (surprise; library should treat it as optional/accept it).
Inferred: parser should be tolerant to the spelling variants and to unknown timers, and consider timers as required-for-completeness per 4.5.9 but only some relevant per BIBB.

Validation (inferred): each timer parses as Real, >= 0.

### 3.2 Notation relevant to EPICS values
- 6.1.2 integers: decimal, `D'..'`, hex `X'..'`, binary `B'..'`.
- 6.1.3 text: double-quoted, any case. 6.1.4 enumerations: UPPER CASE unquoted (TRUE, FALSE, RELIABLE). 6.1.5 property identifiers: Capitalized_Words_With_Underscores. 6.1.7 object identifier: `(Analog Input, 1)` i.e. (type name, unsigned instance).
- 6.4: all BACnet clause references are to ANSI/ASHRAE 135-2020 unless noted ("BACnet-2001" means 135-2001). Note this means the "Clause 12" and "23.4.3" in Clause 5 are the 135-2020 numbering, though 135.1-2025 also keys behaviours to later Protocol_Revision values (up to >= 20 in 7.1.2). Treat the external tables as "the revision the EPICS declares" (inferred) and source them from the edition matching Protocol_Revision.
- Clause 6 contains no other EPICS-value syntax; "?" is defined in 4.4/7.1.1 not in 6. (The literal `'?'` in 6.0 is a BNF quoting example.)
- 6.6.1: value comparison honours 4.4.2 resolution (truncate or round, consistent per datatype); 6.6.3 applies component-wise to constructed types.
- 3.3 "any valid value" = correct datatype and within the vendor-specified range for that property (so ranges come from the EPICS). Passwords where required by vendor are at most 20 characters (EPICS password constraint; inferred relevant to a "password <= 20 chars" check).

## 4. Clause 14: report contents
A report to the manufacturer contains: (a) summary of each executed test case; (b) pass/fail per executed case; (c) diagnostic information for failures. Report model: `Report{ epics_id, run_time, tool_version, results: [CaseResult{case_id/rule_id, summary, outcome: pass|fail (skipped/not-applicable inferred), diagnostics: [str]}] }`. For the validator, map each rule C5-xx to a "test case".

## 5. Validator design notes

- Rule engine: each rule = `Rule(id, clause_ref, severity, requires: set[Capability], applies(ctx) -> bool, check(ctx) -> list[Finding])`. Finding = (rule_id, severity, location (section/object/property/line), message, expected, actual).
- Severities: Clause 5 says "shall" everywhere -> ERROR default. Add WARNING for inferred soft checks (File exception, proprietary-only gaps, unknown timers, ambiguity at revision boundary). Add INFO / SKIPPED for not-applicable (revision < 14 for C5-16) and for rules lacking external data (so user sees them rather than silently passing).
- Pipeline: parse -> normalise to model -> build indices -> resolve derived data (declared revision, bitstring decode, object-type set) -> run rules in dependency order -> report.
- Dependency graph:
  - Tier 0 (structure only): C5-17, timers sanity, C5-08, C5-06, C5-07 (needs only object-type enum names), C5-13/14 (need bit counts).
  - Tier 1 (BIBB knowledge): C5-01 to C5-05.
  - Tier 2 (per-object schema knowledge): C5-09 to C5-12, C5-15, C5-18, C5-19, C5-20.
  - C5-16 needs only Protocol_Revision and the EPICS property sets (no external data).
  - Rules depending on Protocol_Revision should emit one precondition finding if missing (revision absent => treat as old, per 7.1.3, and C5-10/C5-15 use a conservative assumption; inferred).
- External-knowledge pluggability: define interfaces `Standard135Data` with providers keyed by revision, backed by generated JSON tables, so rules degrade to SKIPPED if no data provider is installed.
- Sorting out which rules need external data: needs none: C5-06 (apart from names), C5-08, C5-16, C5-17. Needs a little: C5-07 (object type names), C5-13/14 (bit counts). Needs heavy: C5-01..05 (BIBBs), C5-09..12, 15, 18..20.
- Cross-section dependencies: Application Services section, Object Types Supported section, BIBBs section, Device object in test DB, Standard Object Types Supported vs test DB; Default Property Value Restrictions (4.5.8) vs per-property restrictions (C5-20).
- Be careful about double counting: C5-06 mismatch will also cascade to C5-03 and C5-07; dedupe or tag as `caused_by`.

## 6. External knowledge required (from ASHRAE 135, not defined in 135.1)

Needs from 135 (2020, and later for revisions up to the Protocol_Revision of the EPICS):
- BACnetObjectType enumeration (names, numbers); BACnetObjectTypesSupported bit count per revision (C5-14).
- BACnetProtocolServicesSupported bits and count per revision (C5-13); service names and which are confirmed vs unconfirmed, and the initiate/execute concept.
- Property identifier enumeration and names (to catch IDs 0..511 plus proprietary >= 512 and 4194304+ ranges; IDs 8, 80, 105 are ALL, OPTIONAL, REQUIRED).
- Clause 12 object definitions: per object type, per revision: required/optional/conditional properties, datatypes, access (R, W, conditionally W), value range limits, minimal ranges; revision of introduction; deprecation/removal revision (C5-09..12, 15, 18..20).
- Clause 23.4.3 (proprietary object required properties).
- Annex K BIBB definitions: required services (initiate/execute) and required object types per BIBB (C5-01..05).
- Segmentation enum names (SEGMENTED_BOTH etc.); Protocol_Revision semantics; datatype definitions.
- Error class/code names (for tests, not for validation).

Defined by 135.1 itself: the list of consistency rules (cl. 5), "?" semantics, writability markers' use in tests, timers and their meanings, test notation, resolution semantics, Property_List content rules for tests, report contents, the 135.1 EPICS format (cl. 4, in other digests).

## 7. Test case seeds (validator unit tests)

1. BIBB DS-RP-B claimed but Device.Protocol_Services_Supported lacks ReadProperty bit -> C5-05 error.
2. BIBB requiring an Analog Input object type but AI not in "Standard Object Types Supported" -> C5-01.
3. Same BIBB, AI listed but no AI object in test DB -> C5-02 (and C5-07).
4. Protocol_Object_Types_Supported has AI bit unset while section lists AI -> C5-06 (and C5-03).
5. Services section lacks Execute for ReadProperty while BIBB B side claimed -> C5-04.
6. Services section has ReadProperty with only Initiate where BIBB is B-side -> C5-04.
7. Object_List contains (AV,3) not in test DB -> C5-08.
8. Test DB has (BV,1) not in Object_List -> C5-08.
9. Proprietary object type (>=128) present in DB but missing in Object_List -> C5-08.
10. File type supported, no File object, annotated dynamic -> passes (warning-level note) per C5-07 exception; without annotation -> inferred warning/error.
11. AI object missing Present_Value -> C5-09.
12. Protocol_Revision 5 and object has Property_List (introduced later) -> C5-10.
13. Conditionally required property missing (e.g. Event_Detection_Enable set but Notification_Class missing) -> C5-11 (example inferred).
14. Present_Value of AO marked read-only in EPICS (must be writable) -> C5-12.
15. Device.Description-like required read-only property marked W -> C5-18.
16. Protocol_Services_Supported bitstring of wrong length for Protocol_Revision 14 -> C5-13; too long -> C5-13; correct -> pass.
17. Protocol_Object_Types_Supported length mismatch -> C5-14.
18. Protocol_Revision 12 with a property deprecated at 12 present at 13+ -> C5-15 boundary (inferred) tests.
19. Protocol_Revision 15, Property_List missing a present property -> C5-16; Property_List contains Object_Name -> C5-16 failure; correct list with different order -> pass; Protocol_Revision 13 with no Property_List -> rule skipped.
20. Protocol_Revision absent -> C5-16 skipped; C5-10 conservative behaviour noted.
21. Segmentation_Supported = SEGMENTED_BOTH with Max_Segments_Accepted = 1 -> C5-17 error; = 2 -> pass; SEGMENTED_TRANSMIT with 1 -> pass; NO_SEGMENTATION -> pass.
22. Priority_Array-style value outside standard range (e.g. Present_Value of Multi-state input = 0, min is 1) -> C5-19.
23. "?" value in a ranged property -> no C5-19 failure.
24. Restricted range for an Analog Output Present_Value exceeding allowed standard range -> C5-20.
25. Restricted range smaller than the minimal range mandated by the standard (e.g. restricting Max_Segments_Accepted below minimum, inferred example) -> C5-20.
26. Per-property override missing but datatype default (4.5.8) used for C5-20 resolution -> default applied.
27. Timer section missing Internal Processing Fail Time -> completeness warning; timer value negative or non-real -> error (inferred).
28. Timer list includes Audit Notification Forwarder Fail Time -> accepted.
29. Property marked "conditionally writable" must count as writable for C5-12 and as non-read-only for C5-18.
30. Duplicate object identifiers in test DB -> extra rule (inferred) mapping to C5-08.
31. Device object absent from test DB -> everything cascading from Device properties yields a single root-cause error (inferred; Device property reads are prerequisites).
32. Object type names in section differ only by case/spacing/hyphen from enum names -> parser normalisation (inferred).
