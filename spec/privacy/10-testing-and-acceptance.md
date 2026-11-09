# SPEC-10 — Test and Acceptance Strategy

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Test IDs: TA-nnn (acceptance), referenced from every PRIV-nnn; TA numbers follow the
document they belong to (TA-0xx → 01, TA-1xx → 03, TA-2xx → 04, TA-3xx → 05, TA-4xx → 06,
TA-5xx → 07, TA-6xx → 08, TA-7xx → 09, TA-8xx → cross-cutting negatives)
```

---

## 1. Principles (from the repository's own test culture)

1. **Guards over reviews.** Every list this package introduces (attribution, lineage,
   redactable fields, tombstone allowlist, device storage keys) gets a guard that fails when
   the code and the list drift — the pattern of `scripts/check_privacy_inventory.py` and
   `tests/unit/guards/`.
2. **Reach tests against a real database.** The erasure contract is proven in
   `tests/integration/test_account_erasure_reach.py` / `test_tenant_erasure_reach.py`
   (real ArangoDB, plant → run → scan every collection). New behaviour extends these files.
3. **Negative tests that can fail.** Each guard has a planted-violation test (the repo's
   `TestTheMatrixCanFail` idiom) so that a vacuous guard is caught.
4. **The test reaches the rule by the same path as production** (memory of past defects:
   list vs by-key, escaped literal). Each TA names the entry path.
5. **Run the whole suite**, never `pytest -k` with "0 selected"; backend through
   `.venv/bin/python -m pytest` (28 tests skip silently with the global interpreter).

---

## 2. Test matrix by requirement group

### 2.1 Registry and guards (01, 02, 08 §2)

| TA | Type | Test | Path (new or extended) |
|----|------|------|------------------------|
| TA-001 | guard | R7: every `AnonymizationRule`/`PseudonymizationRule` has `attribution`; every account-shaped field has exactly one; planted rule without attribution fails | `scripts/check_privacy_inventory.py`, `tests/unit/domain/engines/test_privacy_engines.py` |
| TA-002 | unit | mapper never copies across roles: a source with only `created_by` yields `performed_by_user_key = None` | `tests/unit/domain/engines/test_care_event_backfill_mapper.py` |
| TA-005 | guard | single resolver: AST scan finds no `DOCUMENT(CONCAT(@users` whose result reaches a response field except through `IdentityReferenceService`; planted direct join fails | `tests/unit/guards/test_person_display_goes_through_the_resolver.py` |
| TA-006 | guard | no localised literal: `"anonymisiert"` / `"anonymised"` appears in `app/` only in the deprecated adapter | `tests/unit/guards/test_no_localised_person_literals.py` |
| TA-010 | guard (exists) | new collections in `TenantErasureEngine.INVENTORY` or `NOT_TENANT_SCOPED` | `tests/unit/guards/test_tenant_erasure_inventory_is_complete.py` |
| TA-030 | guard | doc-table ⟂ rows of `02` §3 equal the registry (collection, field, attribution, retention class, review fields) | `scripts/check_privacy_registry_doc.py` (pre-commit) |
| TA-200 | guard | one definition of marker/regex/`REDACTED`; planted second literal fails | `tests/unit/guards/test_privacy_constants_are_defined_once.py` (replaces the three-copies pin in `test_garden_plan_retention.py`) |
| TA-606 | guard | R8 lineage: every account-field copy site is in `DERIVED_FIELDS`; planted copy fails | `scripts/check_privacy_inventory.py` |

### 2.2 Account deletion (03 §2)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-100 | integration | after `request_erasure`, care-event list / plan audit / diary responses render `erased` for the subject to a grower; the platform erasure preview shows the name | `tests/integration/test_account_erasure_reach.py` (+ API client) |
| TA-101 | unit | resolver: `is_active=false` + erasure request → `erased` | `tests/unit/domain/services/test_identity_reference_service.py` |
| TA-102 | integration | **residue**: after completion no shared collection holds the raw key **or** the tombstone outside `tombstone_allowed_fields()`; a planted copy in `care_events` marks the run `partially_completed` with `residue` | `test_account_erasure_reach.py::test_residue_scan_catches_a_planted_copy` |
| TA-103 | integration | review items: one per authored/performed row with review fields and one per name-token row; items store no text/token/key (assert the serialized item contains neither the display name tokens nor the key); second run creates none | `tests/integration/test_privacy_review_items.py` |
| TA-104 | api | `GET /admin/platform/privacy/operations?status=partially_completed` lists a planted one; metric `privacy_operations_open` reflects it | `tests/api/test_admin_privacy_operations.py` |
| TA-105 | unit | same escalation threshold for account and tenant erasure (reads the shared setting) | `tests/unit/domain/services/test_erasure_retry_lifecycle.py`, `test_tenant_erasure_async.py` |
| TA-106 | integration | erasure report carries `review_items_created` per tenant and `tombstone_copies_corrected` | `test_account_erasure_reach.py` |
| TA-108 | unit | post-commit phase failure does not roll back the erasure; the request is flagged `post_commit_pending`; the follow-up beat retries idempotently | `tests/unit/domain/services/test_privacy_erase_account.py` |
| TA-131 | api | buffered write replay (`client_event_id`) after account closure → 401 `account.closed` on `/care-events`, `/tasks/{k}/complete`, photo uploads | `tests/integration/test_client_event_idempotency.py` (extend) |

### 2.3 Membership termination (03 §3)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-110 | integration (pin) | leaving changes no domain row; assignee cleared; calendar feeds deleted; audit row written | `tests/unit/domain/services/test_tenant_service.py` (exists partly) + reach-style scan |
| TA-111 | integration | after `RETENTION_FORMER_MEMBER_NAME_DAYS` (clock pinned, the repo's clock-anchored idiom) the resolver returns `former_member` without a name for viewer/grower/lead/management; before the period the name shows; platform admin user page still shows the account | `tests/integration/test_former_member_rendering.py` |
| TA-112 | integration | rejoin → `member`; PRIV-116 markers unchanged | same |
| TA-113 | api | filter by suppressed former member → 422 `care_event.filter_target_unavailable`; CSV renders the state | `tests/api/test_care_events_api.py` |
| TA-114 | unit | departure instant read from `security_audit_log`; absent row → suppressed immediately | `test_identity_reference_service.py` |

### 2.4 Attribution at write time (03 §4)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-120 | unit + api | four confirmation paths (REST, notification action, task-queue completion, MCP) store `performed_by_user_key = principal` and `created_by = principal`; MCP stores the service-account key | `tests/unit/domain/services/test_care_confirmation_bed_event.py` (the task-queue case today asserts only trigger/category — **extend to assert the performer**), `tests/unit/mcp_server/test_tools.py`, `tests/api/test_tasks_api.py` |
| TA-121 | unit | `carry_account_reference`: tombstone → marker (marker target) / `None` (tombstone target); label → `None`; current key passes | `tests/unit/domain/models/test_privacy_constants.py` |
| TA-122 | integration | `record_keeping = none` tenant: the four statutory collections receive the marker and review items at erasure; `pflschg_professional` tenant unchanged (tombstone) | `test_account_erasure_reach.py` |
| TA-123 | unit | task completion performer = token, never body or assignee (exists: `test_task_completion_service.py:140`) — keep | existing |

### 2.5 Anonymisation and redaction (04)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-201 | unit | see TA-121 | — |
| TA-202 | integration | `privacy.consistency` reports a planted tombstone in `care_events.performed_by_user_key` and a planted marker in `treatment_applications.applied_by_key`; corrects nothing | `tests/integration/test_privacy_consistency.py` |
| TA-203 | api | `performed_by=anon_<16hex>` → 422 for lead and grower | `tests/api/test_care_events_api.py`, `test_bed_history_api.py` |
| TA-204 | unit + integration | redaction and R-25 patch cover `material` and measurement strings; `undo` stays | `tests/unit/domain/services/test_garden_plan_retention.py`, `test_care_event_service.py` |
| TA-205 | integration | see TA-103 + bound (`PRIVACY_REVIEW_ITEMS_MAX_PER_ERASURE = 10` in test → `review_items_truncated`) | `test_privacy_review_items.py` |
| TA-206 | api | generic redaction: non-allowlisted field → 422; idempotent 200; audit row category only; old value absent from DB and audit (grep the whole document store for the planted string) | `tests/api/test_privacy_redactions.py` |
| TA-207 | integration | `garden_plan_audit.user_key` receives the marker at erasure; planted tombstone reported by consistency | `test_account_erasure_reach.py`, `test_privacy_consistency.py` |
| TA-208 | integration | residue scan (see TA-102) | — |
| TA-209 | integration | `original_filename` cleared; `caption` kept + review item | `test_account_erasure_reach.py` |
| TA-210 | api | lineage suggestions for a template name list the locations with `template_key` and their audit rows; accepting redacts all; declining redacts the template only | `test_privacy_redactions.py` |
| TA-211 | unit | `management` may redact; grower 403 (exists for lead/grower — extend) | `test_care_event_service.py` |
| TA-226 | unit + api | open review items older than `PRIVACY_REVIEW_SLA_DAYS` (clock pinned) appear as `overdue` in `GET /t/{slug}/privacy/summary` and in the metric `privacy_review_items_overdue`; decided items never count | `tests/unit/tasks/test_privacy_consistency_task.py`, `tests/api/test_privacy_review_api.py` |

### 2.6 Tenant isolation and role-based visibility (05)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-300 | api | `leads_and_self`: grower sees `R` for others, `N` for own; lead sees `N`; viewer `R` | `tests/api/test_attribution_visibility.py` |
| TA-301 | api (pin) | `all_members` equals today's responses (golden comparison on a fixture tenant) | same |
| TA-302 | api | `GET /members` omits `email` without `management`; includes it for `management`, platform admin | `tests/api/test_tenants_members_api.py` |
| TA-303 | api | CSV by viewer → `R`; by lead → names + `ATTRIBUTION_EXPORTED` audit row with `row_count` | `tests/api/test_care_events_api.py`, `tests/integration/test_care_events_csv_export.py` |
| TA-304 | unit | MCP diary/ipm tools return `PersonRef`, never a string matching `^[0-9a-f-]{20,}$`/users key shape | `tests/unit/mcp_server/test_tools.py` |
| TA-305 | api | platform admin: review items 403; `/admin/platform/privacy/consistency` counts only (response contains no `row_key`, no text) | `tests/api/test_admin_privacy_operations.py` |
| TA-306 | api (pin) | filter by another member as grower → 403 (exists) | existing |
| TA-307 | integration | **route walk**: every `/t/{slug}/privacy/*` route refuses a foreign tenant with the same 404 body, DB byte-identical | `tests/integration/test_garden_plan_tenant_isolation.py` (extend the matrix) or a sibling `test_privacy_tenant_isolation.py` |
| TA-308 | unit | notification text never contains another member's display name under either setting (fixture with names that would collide) | `tests/unit/domain/services/test_notification_propagation_service.py` |
| TA-309 | guard | no endpoint aggregates per person: AST scan for `COLLECT … performed_by_user_key` / `created_by` with `COUNT` in `app/`; planted query fails | `tests/unit/guards/test_no_per_person_aggregation.py` |

### 2.7 Retention enforcement (06)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-400 | unit | new beats in `TENANT_AGNOSTIC_BEATS`/`TENANT_WRITING_BEATS`; NFR-011 §3.1 table matches the beat (guard exists) | `tests/unit/guards/test_nfr011_task_table_matches_the_beat.py`, `test_beats_skip_inactive_tenants.py` |
| TA-401 | unit | ceilings/floors for every new setting (`08` §8) | `tests/unit/config/test_retention_ceilings.py` |
| TA-402 | unit | R-43 purges decided items > 3 y, keeps open; R-45 purges ledger entries past `expires_at` | `tests/unit/tasks/test_retention_tasks.py` |
| TA-403 | unit | R-48 notifications: 90 d after `read_at`, 180 d unread | same |
| TA-404 | integration | reclassify job on `record_keeping → none` (TA-703) | `tests/integration/test_record_keeping_reclassify.py` |
| TA-405 | unit (pin) | R-25 floor = ceiling = 5; `pest_control` waits for `max(R-25, R-17)` (exists) | existing |

### 2.8 Offline (07)

| TA | Type | Test | Path (frontend vitest unless stated) |
|----|------|------|--------------------------------------|
| TA-500 | script | REQ-025 §10 table ↔ storage keys in code | `scripts/check_device_storage_table.py` (pre-commit) |
| TA-501 | unit (pin) | namespace filter on every read | `features/gardenPlanner/offline/queue.test.ts`, `planCache.test.ts` |
| TA-502 | guard | no API payload in web storage; PRIV-512 keys cleared on logout | `src/test/guards/noApiDataInWebStorage.test.ts` (exists?) — extend `offlineDataClearedOnSessionChange.test.ts` |
| TA-505 | unit | plan-cache byte eviction | `planCache.test.ts` |
| TA-509 | unit | photo byte ceiling | `queue.test.ts` |
| TA-511 | unit | sweep periods from runtime config; 60-day prompt once | `retention.test.ts`, `OfflineSyncHost.test.tsx` |
| TA-512 | unit | after logout the listed keys are absent; theme/lang/consent survive | `offlineData.test.ts` |
| TA-514 | guard | logout awaits the wipe before navigation; planted un-awaited call fails | `src/test/guards/offlineDataClearedOnSessionChange.test.ts` |
| TA-516 | unit (SW) | `KP_CLEAR_DATA` → no `kp-sw-state`; `KP_CLEAR_DONE` posted | `src/test/pwa/offlineData.test.ts`, `swApiCachePerClient.test.ts` |
| TA-519 | unit | dead-session quarantine / restore / purge | `sync.test.ts`, `queue.test.ts` |
| TA-520 | api (backend) | `401 account.closed` on refresh for a closed account; `403 membership.ended` only when an ended membership is recorded; generic 403 otherwise | `tests/api/test_auth_router.py`, `tests/api/test_care_events_api.py` |
| TA-521 | unit | client reaction to both codes | `sync.test.ts` |
| TA-523 | unit | kill switch on `visibilitychange` | `src/test/pwa/killSwitch.test.ts` |
| TA-524 | unit | shared-device idle wipe, TTL 5 min, purge after one attempt | new `sharedDeviceMode.test.ts` |
| TA-528 | api (backend) | replay never un-redacts; replay by closed author refused; foreign completion 409 | `tests/integration/test_client_event_idempotency.py` |
| TA-529 | component | conflict dialog renders no winner name | `ConflictDialog.test.tsx` |
| TA-530 | component | device page content and wipe button | `AccountSettingsPage.test.tsx` |
| E2E | selenium | TC-053-091 logout clears every user key; TC-053-092 dead-session quarantine; TC-053-093 shared-device idle wipe | `tests/e2e/test_req053_wave9_offline.py` (extend; `req053` marker) |

### 2.9 Data exports (Art. 15/20, CSV, tenant archive)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-600 | integration (exists, extend) | Art. 15 bundle contains no other member's key (`_CARE_EVENT_EXPORT_FIELDS` pin) and, new, no `PersonRef.display_name` of others in personal-garden sections | `tests/integration/test_privacy_export_walk.py` |
| TA-601 | integration | bundle finds statutory rows by tombstone for a still-active person after a tenant erasure (exists: `test_privacy_export_tombstone.py`) — keep | existing |
| TA-602 | integration | after a `record_keeping → none` reclassification the bundle lists the person's rows as `attribution_gap`? — no: the person's account exists, rows carry their live key until erasure; pin that nothing changes for live accounts | `test_privacy_export_walk.py` |
| TA-603 | guard (exists) | R2 reciprocity for the new collections (`privacy_review_items`, `erasure_replay_ledger` in `EXCLUDED_FROM_DISCLOSURE` with reasons) | `scripts/check_privacy_inventory.py` |
| TA-604 | integration | tenant archive `members.jsonl` has no e-mail (exists per REQ-056 E-09 — pin) | `tests/integration/test_tenant_export*.py` |

### 2.10 Migrations (09)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-700…TA-703, TA-716, TA-717 | unit + integration | as listed in `09` §12 | `tests/unit/migrations/versions/test_v0107_*.py`, `tests/integration/migrations/` |
| TA-701a | unit | report redaction filter: a planted user key / name in `details` is rejected | `tests/unit/migrations/test_migration_report_redaction.py` |
| TA-704 | guard | privacy migrations declare `kind`; a `data_backfill` uses `ActiveTenants`, a `privacy_correction` does not | `tests/unit/guards/test_migration_tenant_gate_kind.py` |

### 2.11 Backup restoration (09 §6)

| TA | Type | Test | Path |
|----|------|------|------|
| TA-709 | integration | ledger entry + mirror written at completion; purge filters the mirror | `tests/integration/test_erasure_replay_ledger.py` |
| TA-710 | integration (restore drill, nightly) | dump → erase → restore → replay → raw key absent everywhere but the ledger; review items idempotent | `tests/integration/test_restore_replay.py` (marked `slow`, nightly lane) |
| TA-711 | docs | restore guide contains the replay step; `mkdocs build --strict` | docs lane |

---

## 3. Negative tests — "deleted identities cannot reappear"

These are the tests that prove the package's central claim. Each plants an erased subject
(real key `K`, tombstone `T`, display name tokens `N…`) and asserts absence.

| TA | Channel | Assertion |
|----|---------|-----------|
| TA-800 | **migrations** | run every pending migration after an erasure on a fixture DB; scan all collections: `K` absent; `T` only in `tombstone_allowed_fields()`; `N…` absent from every field that the review queue listed as decided `redact` |
| TA-801 | **backfill / consistency job** | plant a statutory row with `T`; run v0104-equivalent mapper and `care_events.consistency`; `care_events` holds `_anonymized`, never `T` |
| TA-802 | **exports** | Art. 15 bundle of another member, care-event CSV (lead), plan JSON/SVG/PDF, tenant archive, MCP read tools: none contains `K`, `T` or (for CSV/archive after redaction) `N…` |
| TA-803 | **offline synchronisation** | device A buffers a note by `K` → `K` erased elsewhere → device A replays: 401 `account.closed` (closed phase) or generic 401 (erased) → quarantine → purge; the server never stores the note; device B (another user) opening the tenant gets no cache row of `K` |
| TA-804 | **backup restore** | TA-710 |
| TA-805 | **rejoin** | after PRIV-116 and a rejoin, the old rows keep the marker (no un-anonymisation by key reappearance) |
| TA-806 | **tenant import** | importing an archive that contains `K` (exported before the erasure) maps `K` to `_anonymized` (unmapped account rule exists [v]; pin that an erased key is treated as unmapped even if the archive's `members.jsonl` lists it) |
| TA-807 | **notifications** | no notification created after closure names or addresses `K`; existing ones deleted at erasure (exists) |
| TA-808 | **logs** | structlog capture during the whole flow contains neither `K` nor `N…` (guards `test_privacy_logs_carry_no_plaintext_subject` exist — extend the scenario) |
| TA-809 | **search** | `GET /diary?q=<name token>` after redaction returns none of the redacted rows |

---

## 4. Coverage and gates

**PRIV-900** The new guards join the pre-commit set (`scripts/check_privacy_inventory.py`
is already there) and the required `backend-guards` lane. Integration tests run in the
existing ArangoDB-backed lane; the restore drill (TA-710) is nightly.

**PRIV-901** Frontend tests follow `FRONTEND.md` (`cleanup()` first in `afterEach`; jsdom
IndexedDB via `fake-indexeddb` as wave 9 does).

**PRIV-902** E2E additions carry the `req053` marker (and a new `req025` marker for
privacy-only flows) so that the conftest selection by requirement works
(`spec/e2e-testcases/` matrix rows GP-REQ/PRIV).

---

## 5. Acceptance of the package as a whole

The package is **done** when: every PRIV requirement in `01`–`09` with status P0/P1 in `12`
has a passing TA; the three guards (R7, R8, constants) are in pre-commit; the registry
document check (TA-030) passes; TA-800…TA-809 pass; the DPIA pre-screening (`11`) has been
handed to the DPO with the LEG list; and the spec change proposals of `06` §9 have been
turned into versioned edits of REQ-025 / NFR-011 / REQ-053 / REQ-024 / REQ-049 (not silently
— each with a changelog row referencing this package).
