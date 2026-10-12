# Phase 2: Pydantic Data Model (Clause 4.5)

Goal: a complete, I/O-free Pydantic v2 model of an EPICS document, covering every section
and keyword in `docs/spec/02-sections-and-data-model.md`, with validators that enforce the
rules the standard states and nothing more. Can run in parallel with Phase 1. Estimated
effort: 4 to 6 days.

Module: `src/ace_epics/model/` (split into `document.py`, `general.py`, `conformance.py`,
`datalink.py`, `restrictions.py`, `timers.py`, `database.py`, `enums.py`, `names.py`).
Keep every file under 500 lines.

## 2.1 Shared conventions

- All models: `ConfigDict(extra="forbid", frozen=False, populate_by_name=True,
  str_strip_whitespace=False)`. Field names are snake_case; aliases hold the EPICS
  keyword (`Field(alias="Vendor Name")`) so JSON/YAML can dump either style.
- `names.py`: `normalize_name(s) -> str` implementing decision D11 (lowercase, `_` and
  space to `-`, collapse runs). `NamedToken` value type stores `canonical` and `raw`.
  Equality and hashing use `canonical`.
- Every model and field has a docstring citing its clause.
- Models never import from `codecs`, `lexer`, or `values` except the `ValueNode` types.

## 2.2 Models to implement

### `EpicsDocument` (`document.py`)
Fields, in 4.5 order: `header: PicsHeader`, `general: GeneralInformation`,
`bibbs: list[Bibb]`, `services: list[ServiceSupport]`, `object_types: list[ObjectTypeSupport]`,
`data_links: list[DataLinkOption]`, `character_sets: list[CharacterSet]`,
`special: SpecialFunctionality`, `default_restrictions: DefaultRestrictions`,
`fail_times: FailTimes`, `objects: list[TestObject]`, `diagnostics: list[Diagnostic]`
(non-serialized, `exclude=True`), `source: SourceInfo | None` (path, encoding, mode).

Convenience accessors (thin, no BACnet knowledge): `device: TestObject | None` (first object
whose type is `device`), `get_object(ObjectIdentifier)`, `objects_of_type(name)`,
`supports_service(name, *, initiate=None, execute=None)`, `supports_bibb(name)`,
`supports_object_type(name)`. The Phase 5 query API builds on these.

### `PicsHeader` (4.1)
`charset_code: Literal[0,1,2,3,4,5]`, property `charset: CharacterSetCode` enum with
names `UTF8, DBCS, JIS_X_0208, UCS4, UCS2, ISO_8859_1` and the octet width (1/1/1/4/2/1).

### `GeneralInformation` (4.5.1)
`vendor_name, product_name, product_model_number, product_description: str`. No length
validation (standard sets none).

### `Bibb` (4.5.2.1)
`NamedToken` subtype; validator: pattern `^[A-Za-z]+(-[A-Za-z0-9]+)+-[AB]$` is a
**warning**, not an error (Annex K names are external; see D11). Duplicates are a warning
at document level.

### `ServiceSupport` (4.5.3)
`name: NamedToken`, `initiate: bool`, `execute: bool`; validator: at least one true.
Document validator: duplicate service names warn.

### `ObjectTypeSupport` (4.5.4)
`name: NamedToken` (canonical form `analog-value`; raw keeps `Analog Value`),
`createable: bool = False`, `deleteable: bool = False`. The parser accepts both `Createable`
(4.5.4) and `Creatable` (Annex A) per D18; the writer emits `Createable` and `Deleteable`.

### `DataLinkOption` (4.5.5) (`datalink.py`)
Discriminated union on `kind`, one class per literal family:
`Iso8802_3(media: Literal["10BASE5","10BASE2","10BASET","fiber"])`,
`Arcnet(media: Literal["coax star","coax bus","twisted pair star","twisted pair bus","fiber star","twisted pair, EIA-485"], baud_rates: list[int] | None)` (baud rates only valid, and required, for EIA-485),
`MsTp(role: Literal["manager","subordinate"], baud_rates: list[int])` (validator: non-empty, 9600 present is a warning if absent),
`PointToPoint(medium: Literal["EIA 232","Modem"], baud_rates: list[int] | None, autobaud: tuple[int,int] | None)` (exactly one of baud_rates/autobaud; autobaud only for Modem),
`BacnetIp(variant: Literal["'DIX' Ethernet","Other"])`, `BacnetIpv6(variant: Literal["'DIX' Ethernet"])`,
`BacnetSc()`, `Zigbee()`, `Other(text: str | None)`.
Each class has `canonical_text()` producing the exact 4.5.5 literal for the writer, and a
class-level regex the parser uses. Punctuation (period after `MS/TP manager`, comma after
`ARCNET`) must match the standard's literals in `canonical_text()`.

### `CharacterSet` (4.5.6)
StrEnum with the six literals; alias table maps `ISO 10646 (UCS-2)`, `IBM™/Microsoft™ DBCS`
and case/space variants to the canonical member. Document-level warning on duplicates.

### `SpecialFunctionality` (4.5.7)
`max_apdu_size: int | None`, `segmented_requests_window: int | None`,
`segmented_responses_window: int | None`, `router: bool`, `bacnet_ip_bbmd: bool`,
`bacnet_ipv6_bbmd: bool`, `bacnet_sc_hub: bool`, `bacnet_sc_direct_connect: bool`,
`unknown: list[str]` (lenient capture of unrecognized lines). Integers must be `>= 0`;
window sizes `1..127` is a **warning** (range comes from 135, not 135.1).

### Restrictions (`restrictions.py`) (4.4.2 and 4.5.8)
`Restrictions` model: `minimum: ValueNode | None`, `maximum: ValueNode | None`,
`resolution: ValueNode | None`, `maximum_length_string: int | None`,
`maximum_length_list: int | None`, `maximum_length_array: int | None`,
`allowed_values: list[NamedToken] | None`. Keep min/max/resolution as `ValueNode` because
they may be Real, Integer, or Date (D7 interpretation later).
`DefaultRestrictions`: optional `Restrictions` per datatype key
`unsigned_integer, signed_integer, real, double, date, octet_string, character_string,
list, variable_length_array`, plus `extra: dict[str, Restrictions]` for lenient capture
(e.g. a `time` key, which 4.4.2 implies but 4.5.8 omits). Validator per key: only the
restriction names 4.5.8 lists for that datatype; others warn.
`merge(default, override) -> Restrictions` helper (override wins per field) used by Phase 5.

### `FailTimes` (4.5.9) (`timers.py`)
Thirteen `float | None` fields named from the template (`notification_fail_time`, ...,
`foreign_device_registration_fail_time`), plus `audit_notification_forwarder_fail_time`
(Clause 6.3.14) and `extra: dict[str, float]`. Alias table maps the template spellings and
the Clause 6 variants (`Acknowledgment`, `Autonegotiation`, `Minimum ON/OFF Fail Time`) to
fields. Validator: values `>= 0`. Completeness is a mode decision (D6) enforced by the
parser, not the model.

### Test database (`database.py`) (4.5.10)
`ObjectIdentifier`: `object_type: NamedToken | int` (int for proprietary, `>= 128`),
`instance: int` (`0 <= n <= 4194303`); `is_proprietary`; `__str__` gives `(analog-value, 6)`
or `(proprietary 700, 1)`.
`Access` StrEnum: `R`, `W`, `C`.
`PropertyEntry`: `name: NamedToken`, `value: ValueNode`, `access: Access = R`,
`restrictions: Restrictions | None`, `comment: str | None`, `not_readable: bool = False`
(Clause 7.1.1 needs a "not accessible via ReadProperty" marker; the EPICS text defines no
syntax, so this is set only by JSON/YAML/RDF inputs or programmatically; the native writer
emits it as a structured comment `-- @not-readable`, which the parser recognizes).
`TestObject`: `identifier: ObjectIdentifier`, `name: str`, `object_type: NamedToken | int`,
`properties: list[PropertyEntry]` (ordered, excludes the three header properties),
validators: `object_type` equals `identifier.object_type`; proprietary objects carry no
further properties (error per 4.5.10); duplicate property names error; `property(name)`,
`has_property(name)`, `property_names()` helpers.
Document validator: duplicate object identifiers error; exactly one `device` object is a
**warning** when absent (Clause 5 needs it; 4.5.10 does not mandate it).

## 2.3 Value types used by the model

Import `ValueNode` union from `ace_epics.values` (Phase 1). Until Phase 1 lands, stub it as
a Pydantic `RootModel[Any]` behind the same name so Phase 2 tests can proceed; replace in
the Phase 3 integration PR.

## 2.4 Tests (`tests/unit/model/`)

- One test module per model file; parametrize over the 40 seeds in
  `docs/spec/02-sections-and-data-model.md` §6 that are model-level (validation of flags,
  spellings, duplicates, proprietary objects, object_type mismatch, timer alias mapping).
- `DataLinkOption.canonical_text()` round-trips every literal in 4.5.5 through the class
  regex (table-driven test with all 21 literals plus baud/autobaud variants).
- `CharacterSet` alias table covers both spellings of UCS-2 and the trademarked DBCS form.
- Hypothesis strategies for every model (`tests/strategies.py`) that generate valid
  documents; used by codecs in Phase 4 for round-trip property tests.
- `model_json_schema()` generates without error for `EpicsDocument` and the schema is
  checked into `tests/snapshots/epics-document.schema.json` with a snapshot test.

## 2.5 Documentation deliverables

- `docs/site/format-guide/sections.md`: one subsection per EPICS section, each showing the
  EPICS syntax (short synthetic example), the model class, and the clause reference.
- API reference pages for `ace_epics.model` (mkdocstrings), including the alias tables.
- `docs/decisions/0003-name-normalization.md` (D11) and `0004-not-readable-marker.md`.

## Acceptance criteria

- Every keyword, literal, and enumeration in `docs/spec/02` has a corresponding field,
  enum member, or alias (reviewer checks with a traceability table added to
  `docs/site/format-guide/sections.md`).
- Hypothesis strategies generate 1000 documents without validation error.
- JSON Schema snapshot committed; `pyrefly` clean; coverage of `model/` at 95 percent.
