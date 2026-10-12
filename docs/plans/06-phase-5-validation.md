# Phase 5: Consistency Validation (Clause 5) and BACnet Knowledge

Goal: implement the twenty checks C5-01 to C5-20 from
`docs/spec/03-consistency-tests-and-usage.md` as a rule engine, with the BACnet 135
knowledge they need behind a pluggable provider, plus the query API that Clause 7 tests
imply. Depends on Phase 3. Can run in parallel with Phase 4. Estimated effort: 8 to 12
days; the knowledge tables are the long pole and can be grown incrementally after 1.0.

Modules: `src/ace_epics/validation/` (`engine.py`, `rules/`, `query.py`, `report.py`) and
`src/ace_epics/knowledge/` (`provider.py`, `data/*.json`, `loader.py`).

## 5.1 Query API (`query.py`)

A read-only facade over `EpicsDocument` that the rules and downstream test tools use
(from `docs/spec/03` §2.6):

- `protocol_revision: int | None` (from `device.protocol-revision`, interpreted as Unsigned).
- `services_supported_bits`, `object_types_supported_bits` (decoded BitString with length).
- `object_list: list[ObjectIdentifier]` from the Device object.
- `access(obj, prop) -> Access`, `is_writable`, `is_conditionally_writable`,
  `is_read_only`, `is_readable`.
- `limits(obj, prop) -> Restrictions`: per-property override merged over the 4.5.8 default
  for the property's datatype (datatype from the knowledge provider when available; else
  inferred from the value node kind) and over the standard range (provider).
- `array_length(obj, prop) -> int | None` (index 0 semantics, Clause 7.1.1).
- `expected_property_list(obj) -> set[NamedToken]` (all listed properties minus
  object-name, object-type, object-identifier, property-list; Clause 7.1.3).
- `variants(object_type) -> list[list[TestObject]]`: group objects by signature
  (property set, access flags, restrictions) for Clause 7.1.2 sampling.
- `is_unspecified(value)`.

## 5.2 Knowledge provider (`knowledge/`)

```
class KnowledgeProvider(Protocol):
    def object_types(self, revision: int | None) -> Mapping[str, int]
    def object_types_bit_count(self, revision) -> int | None
    def services(self, revision) -> Mapping[str, int]          # BACnetServicesSupported bits
    def services_bit_count(self, revision) -> int | None
    def property_identifiers(self) -> Mapping[str, int]
    def bibb(self, name) -> BibbDefinition | None             # services (dir), object types
    def object_definition(self, object_type, revision) -> ObjectDefinition | None
        # properties: name -> PropertySpec(required|optional|conditional, datatype,
        #   access (R/W/C), introduced_rev, deprecated_rev, removed_rev, range, min_range)
    def proprietary_object_required_properties(self) -> set[str]   # 135 23.4.3
```

Data files (`knowledge/data/`), each with a `source` field naming the 135 edition and a
`revision` key where values vary by Protocol_Revision:

| File | Content | Needed by | 1.0 scope |
|---|---|---|---|
| `object_types.json` | name to number; per-revision bit count | C5-06, 07, 14 | required |
| `services.json` | BACnetServicesSupported names, bits, per-revision count | C5-04, 05, 13 | required |
| `property_identifiers.json` | name to number | C5-16, 7.1.2 | required |
| `bibbs.json` | BIBB to required services (initiate/execute) and object types (Annex K) | C5-01..05 | required for DS, DM, AE, SCHED, T groups; others incremental |
| `objects/<type>.json` | per-object property specs (Clause 12) | C5-09..12, 15, 18..20 | 1.0: device, analog/binary/multistate I/O/V, file, notification-class, schedule, calendar, trend-log; others incremental |
| `enums/*.json` | segmentation, units, etc. as needed by rules | C5-17, 19 | segmentation only |

Sourcing rules: the base standard is available locally as `resources/ASHRAE-135-2024.pdf`
(gitignored, licensed to one person; never commit it or verbatim extracts). Extract Clause 21
enumerations (BACnetObjectType, BACnetPropertyIdentifier, BACnetServicesSupported,
BACnetObjectTypesSupported), Clause 12 property tables, Annex K BIBB tables, and the
Protocol_Revision history (Annex of revision changes) with `pdftotext -layout` plus low-cost
agents, the same way `docs/spec/` was produced; name `ASHRAE 135-2024` as `source` in every
data file. Do not copy from GPL code. Cross-check numbers against at least one permissively licensed stack (bacpypes3,
MIT) in a script under `scripts/knowledge/check_against_bacpypes3.py` that is dev-only.
A `NullProvider` returns `None` everywhere so rules degrade to SKIPPED.

## 5.3 Rule engine (`engine.py`, `rules/`)

```
class Rule(Protocol):
    id: str; clause: str; severity: Severity; requires: frozenset[str]   # provider capabilities
    def applies(self, ctx: Context) -> bool
    def check(self, ctx: Context) -> Iterable[Diagnostic]
```

`validate(doc, provider=None, *, rules=None, strict=False) -> ValidationReport`.
`Context` holds the document, query facade, provider, and a memo of derived facts
(decoded bit strings, device object, revision) so rules do not recompute them.
Each rule yields diagnostics with `code=rule id`, `clause=5(x)`, location fields filled.
Rules whose `requires` are not met by the provider yield one `SKIPPED` diagnostic.
Cascade control: rules declare `depends_on` and the engine attaches `caused_by` when a
dependency already failed (C5-06 failing also explains C5-03 and C5-07).

Rules, grouped by tier (implement in this order):

- Tier 0, no external data: C5-08 (Object_List vs database), C5-16 (Property_List,
  revision >= 14), C5-17 (segmentation vs Max_Segments_Accepted), plus library-level
  structural rules S-01 duplicate identifiers, S-02 Device object present, S-03 timers
  non-negative, S-04 restriction datatype matches value kind.
- Tier 1, enumerations only: C5-06, C5-07 (D16 File exception as warning), C5-13, C5-14.
- Tier 2, BIBB tables: C5-01, C5-02, C5-03, C5-04, C5-05.
- Tier 3, object definitions: C5-09, C5-10, C5-11, C5-12, C5-15 (D15 boundary), C5-18,
  C5-19 (skip `?` values), C5-20 (uses `query.limits`).

## 5.4 Report (`report.py`) (Clause 14)

`ValidationReport`: `document_id` (vendor, product, model), `tool_version`, `run_at`,
`results: list[RuleResult]` where `RuleResult` has `rule_id, clause, outcome
(pass|fail|skipped|not_applicable), diagnostics`. Methods: `summary()`, `to_json()`,
`to_markdown()`. Exit-code mapping for the CLI: errors 1, warnings only 0 unless
`--warnings-as-errors`.

## 5.5 Tests (`tests/validation/`)

- One test module per rule; each uses the synthetic fixture corpus plus targeted mutations
  (`tests/validation/mutate.py` helpers: drop property, flip access, resize bit string,
  change revision). Cover all 32 seeds in `docs/spec/03` §7.
- Provider tests: every data file loads, numbers are unique, per-revision counts are
  monotonic non-decreasing, BIBB references resolve to known services and object types.
- Engine tests: SKIPPED behaviour with `NullProvider`, `caused_by` attachment, rule
  selection, strict mode promoting structural warnings.
- Golden report snapshot for one full synthetic document (JSON and Markdown).

## 5.6 Documentation deliverables

- `docs/site/validation/rules.md`: table of every rule (id, clause, severity, what it
  checks, which knowledge it needs, example message). Generated from the rule registry by
  a mkdocs hook so it cannot drift.
- `docs/site/validation/knowledge.md`: how to add or update a knowledge table, the source
  edition policy, and the bacpypes3 cross-check script.
- `docs/site/validation/query-api.md` with examples for writing an external test tool.

## Acceptance criteria

- All 20 Clause 5 checks and 4 structural rules registered; each has tests for pass,
  fail, and (where applicable) skipped.
- With the shipped provider, validating the synthetic "full" corpus document yields zero
  errors; each mutation fixture yields exactly its expected rule failure.
- Rule documentation page is generated, not hand-written.


## Local implementation evidence (2026-10-11)

All twenty Clause 5 rules and four structural rules are registered and tested, including
capability-based SKIPPED results, dependency attribution, and the 32 digest seeds.
The query API resolves derived header properties, revision-aware standard ranges,
legacy property aliases, datatype defaults for writable properties, and overrides.
The synthetic full corpus validates with zero errors; unavailable definitions for
object types outside the 15-type scope and external runtime conditions remain visible
as SKIPPED findings. Reports have fixed-time JSON and Markdown golden snapshots.

The shipped enumerations and exact bit counts cover revisions 14-30. All fifteen
planned object types have sourced property snapshots throughout that interval, with
143 verified introductions and four historical Device-property removals. Annex K
includes all 152 scoped BIBBs plus one supporting NM definition. The BACpypes3 numeric
cross-check compared 574 entries with zero mismatches; 53 newer entries were absent
from the comparison stack. The licensed standard and amendment PDFs remain ignored.

Rule, diagnostic, vocabulary, and conformance pages are generated from their registries
and source tables. Live multi-platform CI remains an external acceptance gate.
