# Pre-analysis: #2524 v0100 backfill hardening (transient, removed before merge)

Class: bug (hardening of a migration before prod point P-2; secondary refactor). Source: issue #2524 = non-blocking notes of the final review of #2508. Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: the issue body (5 numbered notes) is the decision record.

## Established (develop bd71f2d64)
- v0100 (`src/backend/app/migrations/versions/v0100_backfill_plant_location_site.py`, merged in #2508/dadb1e936) is above `_PINNED_THROUGH = "0092"` of `tests/unit/guards/test_applied_migration_sources_are_frozen.py` and in no release tag (v0.4.2 tops out at v0092): its class source may still change without the freeze guard; a dev cluster that already applied it logs `migration_checksum_drift` for 0100 (record as a rollout note, never re-stamp).
- Item 1 (half-set plants): in `_plan` (l.~115-130) a plant with `location_key` null and `site_key` set takes `location_key` from the slot (`update["location_key"] = row["slot_location_key"]`), while `site_key` is kept (`if row["site_key"] is None` guards the site write), so the two can disagree. Reproduced by reading; needs a test.
- Item 2: `_tenant_reason` returns `cross_tenant` for a site without `tenant_key`, for a missing site (DOCUMENT null) and for a plant without tenant alike; `location_without_site_key` (details counter `no_site_on_location`) is unreachable because a location without a resolvable site already ends as `cross_tenant`.
- Item 3: `tests/integration/test_v0100_backfill_plant_location_site.py` seeds L1/L2/L4, S1/S2/S4, s1/s2; no plant without tenant_key, site without tenant_key, deleted slot (`slot_missing`), slot without location, or batch over 500 (`_BATCH_SIZE`).
- Item 4: `_plan` does `rows = list(cursor)` over all plants with a missing field.
- Item 5: the module docstring says "plants"; the collection is `plant_instances`.

## Design
- D-1 Half-set: when `location_key` is null and `site_key` is set, repair only if the existing `site_key` equals the site derived through the slot's location; otherwise unresolved with a new reason (e.g. `site_mismatch`); the plant is left untouched (neither field written).
- D-2 Reasons made truthful: `site_without_tenant` (site found, no tenant_key), `site_missing` (a location names a site that does not exist), `location_without_site_key` repurposed as an unresolved reason (location found, no site_key) instead of the dead counter, `cross_tenant` stays for a plant without tenant and for a really foreign site. The scan returns the flags needed (site found / site tenant) so the reasons come from facts, not guesses. Update the module docstring (reason list) and the dry-run report keys; grep docs/spec/.audits-free for the old keys (`location_without_site_key`, `no_site_on_location`, "cross_tenant" lists) and fix every copy (P-2 runbook, docs, REQ-053 spec rows).
- D-3 Integration seeds for every gap listed in item 3 (plant without tenant, site without tenant, deleted slot, slot without location, batch over 500 incl. idempotent second run).
- D-4 Streaming: iterate the cursor instead of `list(cursor)`; keep counts, the first `_LISTED` keys per reason and apply update batches as they fill (or keep only the batch list), so memory is bounded; the dry-run report must stay byte-identical in shape/values for the same data (add a test comparing dry-run `will_update` with the later `updated`). Never read-while-write hazards: `_APPLY` already re-reads both fields; if applying inside the loop, use a non-streaming server cursor or collect the batch first; measure/justify the choice.
- D-5 Docstring: `plants` -> `plant_instances`.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | D-1, D-2, D-5 in the migration + unit tests (fake db) | fullstack-developer |
| P2 | D-3 integration seeds/tests | fullstack-developer |
| P3 | D-4 streaming scan + report-equality test; docs/runbook wording of the new reasons | fullstack-developer |
Review after: python-code-reviewer (idempotence, never-guesses, report compatibility).

## Risks
- Report shape changes (reason names, removed counter): operators read `plant_location_backfill_dry_run` before P-2; no consumer in code besides tests — grep to confirm.
- Dev clusters that already applied v0100 will log `migration_checksum_drift` for 0100 after this edit (accepted; note in PR).
