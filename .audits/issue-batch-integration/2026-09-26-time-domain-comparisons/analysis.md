# Group 2026-09-26-time-domain-comparisons

- **Tier:** 2 (one repository, no published contract beyond an OpenAPI description string)
- **Research question:** which time values in `app/` are compared or sorted in a domain other than the one they denote, and what is the smallest fix per member that a guard can hold?
- **Logical change (one sentence):** every stored time value is compared and sorted as the instant or date it denotes, and every year shift survives 29 February.
- **Classification:** class cluster (one recurring defect class: time values compared/sorted in the wrong domain), prior art #1784/#1808.
- **Mode:** A (single strand) — every member touches the same guard file and the same query builder; no member is independently removable without re-editing the guard.
- **Operator approval:** pre-granted for the sweep (strand Y brief, 2026-09-26).

## Members

| # | Predicate | Asserted cause | Verification (actual output) | Result |
|---|---|---|---|---|
| #1798 | thematic coupling + shared touch surface (guard `_ALLOWLIST`) | `DATE_ADD(...) > DATE_NOW()` string vs number | `RETURN DATE_ADD('2020-01-01T00:00:00Z',1,'days') > DATE_NOW()` → `true`; wrapped in `DATE_TIMESTAMP` → `false` (ArangoDB 3.12.8) | confirmed, fixed |
| #1799 | thematic coupling | date field vs datetime cutoff; `.replace(year=)` raises on 29 Feb | `'2025-09-25' < '2025-09-25T00:00:00+00:00'` → `true`; Python `replace(year=)` on 29 Feb raises `ValueError` | confirmed; class sweep found 5 more `.replace(year=)` sites (calendar, sowing engine, retention) |
| #1801 | thematic coupling | ICU collation misorders `SORT` on mixed spellings | integration: `count_below_threshold` counted a tank whose later state (`…00.5Z`, 90 %) lost to `…00+00:00` (5 %) → `1` on develop | confirmed; 68 hand-written sorts + builder |
| #1802 | shared touch surface (`tank_repository`) | date-only `end_date` read as midnight | `DATE_TIMESTAMP('2025-09-25')` → `1758758400000` (midnight); integration: 2 fills on the day → `0` on develop | confirmed, fixed |
| #1809 | dependency chain (#1808 consequence) | `DATE_TIMESTAMP(doc.x)` hides the index | explain on develop: 5 sweeps `EnumerateCollectionNode`; after: `IndexNode` on the swept field; seeded 20 000 docs: scannedFull 20000 → scannedIndex 3324, same result count | confirmed for 5 sites; refuted for `erasure_requests` (already uses the `status` index), `ai_tip_cache.valid_until` (no sweep exists; the read is served by the context index), `data_export_requests` (an OR arm on `status` defeats any `expires_at` range); `mcp_idempotency_record` kept as is (its contract sweeps unreadable values, which no raw range can select) |

## Completeness matrix

| Member | Query fix | Guard | Unit | Integration | Docs |
|---|---|---|---|---|---|
| #1798 | `ipm_repository.get_active_karenz_periods` | allowlist entry removed; existing string-function rule now holds it | n/a — rule already had falsification tests | `test_only_a_running_karenz_period_is_listed_as_active` | not applicable: no user-facing doc describes the Karenz list query |
| #1799 | `plant_instance_repository.get_history_by_slot` (date cutoff), `replace_year` helper | new `test_year_shifts_survive_29_february.py` | helper parametrised test | cutoff-day and 29-Feb cases | not applicable: internal |
| #1801 | 68 SORT keys + `AQLBuilder.sort` | SORT rule + literal builder-sort rule | builder sort test, falsification | latest-pick + builder sort | not applicable: internal ordering |
| #1802 | `tank_repository.get_fill_event_stats` | not applicable: a single-site semantic bug, no class beyond #1784's | — | 3 parametrised bounds | OpenAPI description of `end_date` updated |
| #1809 | 5 sweeps + `instant_prefilter_bound` | pre-filter acceptance rule with 5 negative cases | helper via guard/unit | index-reach test on the MCP audit sweep | module docstring of `query_builder` |

## Out of scope

- `v0045` migration's Python `_sort_rank` orders ISO strings as text (applied migration, recorded history).
