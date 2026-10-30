# Pre-analysis: #2512 frost_exposed round-trip (transient, removed before merge)

Class: bug (primary). Source: issue #2512 = operator decision 2026-10-19 on #2503 option (a) and #2466 item 12.
Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: the issue body is the decision record (U_gate override: operator decision, three numbered points).

## Established (read in code at develop a7b83bd1e)
- `ExportLocation` (`app/domain/models/garden_plan_export.py:70`) has no `frost_exposed`; `_ExportModel` is `from_attributes=True, extra="ignore"`, so adding the field fills it from `Location` in `_validated(ExportLocation, loc)` (`garden_plan_export_service.py:232,238`).
- Import (`garden_plan_import_service.py:705-709`) derives `frost_exposed` from the sent risk unconditionally: high -> True, low -> False, normal/unknown -> None. So a migrated false/normal bed returns as None (edge 2 of #2503).
- PATCH sync `GardenResourceService._mirror_frost_risk` (`garden_resource_service.py:322-338`): on any risk CHANGE sets `frost_exposed = frost_exposed_from_risk(sent)`, so normal -> None clears a forced False (edge 1: normal -> high -> normal ends None).
- `frost_risk_from_exposed` docstring (`frost_exposure_resolver.py:47-57`) and the `frost_exposed_from_risk` docstring describe the open question #2503 and must be updated.
- Tests that pin current behaviour: `tests/unit/domain/services/test_garden_resource_service.py` (~l.337-366, 426-470: normal -> None; high -> normal) and `tests/unit/domain/services/test_garden_plan_import_service.py` (~l.273-287: restored false/normal bed has `frost_exposed is None`).
- Spec REQ-053 version-table row "1.6 (Nachtrag WP 3.9)" point (b) already says `false` -> `normal` (point 3 of the issue: verify, change only if a `false` -> `low` wording remains anywhere, e.g. `.audits/plans`, docs, migration docstrings).

## Design
- D-1 Export: `ExportLocation.frost_exposed: bool | None = None` (additive inside `schema_version "1"`; the import already ignores unknown keys inside items, refuses unknown TOP-LEVEL keys only).
- D-2 Import: if the file's location item carries `frost_exposed` (key present, `"frost_exposed" in item.model_fields_set`), store it as sent; if the key is absent (file written before this change) keep deriving from the risk as today. Explicit `null` = inherit.
- D-3 PATCH rule on a risk change: sent `high` -> True, `low` -> False (unchanged); `normal` -> clears only a stored `True` to None and leaves `False`/None untouched (do not put `frost_exposed` into `provided`); `unknown` -> None as today (explicit "no information"). Keep "unchanged risk never touches the boolean".
- D-4 Docs: `frost_exposed_from_risk` / `frost_risk_from_exposed` docstrings, the import comment at l.705, API docs DE/EN (export contents list in `docs/{de,en}/reference/api-reference.md`, if it enumerates location fields), spec REQ-053 (export field list / WP 3.9 (b) sentence "Folgen für Import/Rückänderung in #2503" -> resolved by #2512), version-table row "1.6 (Nachtrag #2512)".

## Work packages
| id | what | files | specialist |
|---|---|---|---|
| P1 | export field + import honours it + tests (round trip of false/normal, true/high, null/unknown, legacy file without the key) | garden_plan_export.py, garden_plan_import_service.py, tests/unit/.../test_garden_plan_import_service.py, an integration/export round-trip test where the export tests live | fullstack-developer |
| P2 | PATCH rule D-3 + update the pinned tests (#2503 edges 1 and 2) | garden_resource_service.py, test_garden_resource_service.py, frost_exposure_resolver.py docstrings | fullstack-developer |
| P3 | spec/docs/changelog wording (D-4) | spec/req/REQ-053*.md, docs/{de,en} | fullstack-developer |

Dependencies: none between P1-P3; one run, three commits.

## Risks / operator points
- A file written by the new export imported by an OLD backend: `extra="ignore"` on items, key dropped, unchanged behaviour. A new-format file always carries the key, so `null` means inherit (differs from the legacy derive-from-risk only where risk is high/low and the boolean is null: not producible by the sync paths).
- `normal` no longer clears a False: a user cannot return a forced-False bed to "inherit" via the risk dropdown (only via `unknown` or the legacy boolean field on PUT). Reported to operator as consequence of the decided rule.
