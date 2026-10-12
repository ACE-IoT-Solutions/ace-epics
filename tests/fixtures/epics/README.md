# Synthetic EPICS corpus

These fixtures use invented products, object values, and examples. No fixture contains a copied Annex A extract. `tests/fixtures_build_epics.py` regenerates CRLF `.tpi` files, document snapshots, and mode-specific diagnostic snapshots from the invented model corpus.

`full.tpi` represents all 25 object families in the Annex's coverage list plus Network Port, Channel, Timer, Color, and Audit Log. It supplies required properties for the fifteen bundled object definitions, consistent revision-30 service/object bits, Object_List, and every Property_List. It validates with zero errors; object families without bundled property tables produce honest skipped semantic checks.

Scalar, time, group, marker, identifier, and case/layout files exercise grammar independently. `lenient/` isolates accepted deviations; `negative/` exercises hard-error recovery. The tests assert explicit error codes independently of stored snapshots. Licensed Annex A input stays local under `docs/spec/private/` and is used only by the optional private smoke test.
