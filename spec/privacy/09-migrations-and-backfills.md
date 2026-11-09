# SPEC-09 — Migration and Backfill Strategy

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-700 … PRIV-739
Depends on: NFR-016 / ADR-009 (migration framework), 04 §7 (legacy findings), 08 (model)
```

---

## 1. Framework facts the migrations rely on [verified]

- Versions `app/migrations/versions/vNNNN_<slug>.py`, gapless, one `migration` object; `up(db,
  *, dry_run=False) -> MigrationReport` idempotent (M-3), `dry_run` honoured (M-5); default
  `down` raises `IrreversibleMigrationError` (M-6); applied sources are frozen by
  `test_applied_migration_sources_are_frozen`.
- `MigrationReport {version, name, scanned, changed, dry_run, duration_ms,
  precondition_unmet, details}`; the CLI prints counts only, `details` reach stdout only
  through the migration's own structlog line; **no dry-run report is persisted** — the
  operator writes `.audits/prod-release/*.md` by hand from captured logs.
- No framework-level tenant scoping: each migration scopes itself; unique indexes lead with
  `tenant_key`. Runs on startup (`run_pending_migrations`), lock in `schema_migrations`
  (`__lock__`, TTL 300 s); a failing migration is fatal for startup (M-4).
- Reversibility is the exception (v0104 is reversible via its marker `trigger=backfill` +
  `source_ref`, excluding rows a person since edited).
- Latest version: `v0106_client_event_id_index`.

**PRIV-700** Every migration of this package MUST be idempotent (second run `changed == 0`),
tenant-scoped in its AQL (`FILTER doc.tenant_key == @tenant_key` or a per-tenant loop with
the tenant list read once), and observable (a structlog line with the `details` dict **and**
a persisted dry-run report, §2).

---

## 2. Dry-run reports become persisted artefacts

**PRIV-701** A new collection `migration_reports` (platform, `NOT_TENANT_SCOPED` with reason
"operator proof of a migration run; no personal data") MUST store every `MigrationReport`
of a privacy migration (`dry_run` and real) with `details` **after passing a redaction
filter**: `details` may contain only counts, collection names, field names, tenant **keys**,
and sample **row keys** (≤ 25 per bucket, as v0104 does) — never user keys, names, text or
tombstones. A unit test parses each privacy migration's report builder and asserts the
allowed key set.

**PRIV-702** The CLI `upgrade --dry-run --report-out <path>` MUST write the reports as JSON
so that the `.audits/prod-release` document can embed them verbatim instead of copying
numbers from logs.

---

## 3. M-P1 — Correct copied tombstones and move the plan audit actor to the marker

**Migration `v0107_privacy_tombstone_copies`** (reversible: no — a marker cannot be turned
back into the pseudonym; the information is intentionally gone).

| Step | AQL (per tenant) | Report bucket |
|------|------------------|---------------|
| 1 | `care_events` where `performed_by_user_key =~ TOMBSTONE_REGEX` → `_anonymized` (also `performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`) | `care_events.tombstone_to_marker{tenant_key: count}` |
| 2 | `garden_plan_audit.user_key =~ TOMBSTONE_REGEX` → `_anonymized` (DEC-16) | `garden_plan_audit.tombstone_to_marker` |
| 3 | every other **non-allowlisted** collection with an account-shaped field (list derived from the inventory at runtime, `tombstone_allowed_fields()` excluded): count only, no write | `undeclared_tombstones{collection.field: count}` → precondition for the consistency beat, not corrected blindly |
| 4 | `attachments.created_by == _anonymized AND original_filename != ""` → `""` | `attachments.filename_cleared` |

**PRIV-703** Preconditions: the inventory rule change for `garden_plan_audit` (tombstone →
marker) MUST be merged in the same PR; the consistency beat (`privacy.consistency`) MUST be
registered so that bucket 3 keeps being watched after the migration.

**PRIV-704** The dry run MUST be run against a production snapshot before P-8 (the next REQ-053
production point) and its persisted report attached to the release document; the real run
is part of the normal startup migration.

Expected production counts (from the P-6 report's v0104 run): small — the backfill ran on
2026-11-07; tombstones exist only for accounts erased before that date whose
treatments/harvests fell into the R-25 window.

---

## 4. M-P2 — Record-keeping profile and re-classification

**Migration `v0108_tenant_record_keeping_default`**: sets `settings.record_keeping = "legacy"`
explicitly on every tenant that has none (so later code can distinguish "never asked" from
"declared none"). Reversible (removes the key where it equals `legacy`).

**Job (not a migration): `privacy.reclassify_statutory_rows`** — runs when a tenant's
`record_keeping` changes to `none` (PRIV-402), tenant-scoped, idempotent:

| Rows | Action |
|------|--------|
| `harvest_batches`, `quality_assessments`, `treatment_applications`, `inspections` with a tombstone in `*_by_key` | → `_anonymized`; `review item` for `notes` (`source_kind = record_keeping_change`) |
| same collections with a live key | nothing now (the account exists); the erasure rules of a `none` tenant treat them as `shared_history` from now on |

Report: counts per collection; audited `TENANT_RECORD_KEEPING_CHANGED`.

---

## 5. M-P3 — Free-text performer fields → keyed

**Migration `v0109_keyed_performers`** (additive schema; reversible for the field *copy*,
not for later writes):

| Collection | Step |
|------------|------|
| `watering_events`, `watering_logs`, `tank_fill_events`, `maintenance_logs` | add `performed_by_user_key = null`, `performed_by_label = performed_by[:80]` (the typed text becomes the third-party label — it is **not** a key, REQ-025 rule 4); keep `performed_by` for one release (deprecated) |
| `nutrient_plans`, `propagation` batches | `author_user_key = null`, `author_label = author[:80]` |
| `inspections` where `inspector LIKE "mcp:%"` | `inspected_by_key = substring after "mcp:"` **only if** that key is a current `users._key` with `account_type = service`; otherwise `inspected_by_key = null`; `inspector = ""` |
| `workflow_templates` | `created_by_user_key = null`; `created_by` kept as label |

**PRIV-705** The migration MUST NOT infer an account from a typed name (REQ-025 §3.1.3 rule
4; #1662/#1663 measured that it never matches the right account). The one exception is the
`mcp:<key>` prefix, which the MCP code wrote deterministically [verified
`mcp_server/tools/ipm.py`].

**PRIV-706** Rows whose label equals a **current member's display name** of the same tenant
MAY be listed as review items (`legacy_unkeyed_name`) so a lead can decide to keep the
label or clear it; the migration never changes them. Bounded by PRIV-223.

---

## 6. Backups and restoration

### 6.1 Facts [verified]

- Helm CronJob `arangodb-backup` (`arangodump` → rclone → S3) exists, **disabled by
  default**, `retentionDays: 30`; TimescaleDB and attachments are not covered by the chart
  (docs suggest snapshots/versioning); no backup is documented as running in production
  (audit DR-01…04).
- Docs require the same `FERNET_KEY` and `ERASURE_TOMBSTONE_SALT` at restore; NFR-011 §4
  requires the salt in the DR backup.
- **No procedure re-applies erasures after a restore**; no check of `erasure_requests` on
  restore; dump retention vs Art. 17 is not addressed.

### 6.2 Requirements

**PRIV-707** Backups MUST NOT be enabled in production before the replay ledger (§6.3) and
the restore procedure (§6.4) exist. (Decision for the operator; recorded as DEC-13.)

**PRIV-708 [legal LEG-11]** Dump retention MUST be ≤ `BACKUP_RETENTION_DAYS` (default 30,
ceiling 35) and MUST be stated in the privacy policy ("backup copies are deleted within 35
days; after a restore, completed erasures are re-applied automatically"). The EDPB/DSK
position that backups need not be edited for an erasure if they are deleted on a short
schedule and erasures are re-applied on restore is the assumption; counsel confirms.

### 6.3 Erasure replay ledger (`08` §3.7)

**PRIV-709** On every completed account erasure the engine MUST write
`erasure_replay_ledger {erasure_key, user_key (raw), tombstone, completed_at, plan_fingerprint,
expires_at = completed_at + BACKUP_RETENTION_DAYS + ERASURE_REPLAY_LEDGER_GRACE_DAYS}`. The
raw key is necessary because every erasure rule matches the raw key; the tombstone cannot
find rows. The ledger is purged by `privacy.purge_replay_ledger`; the retention is R-45.
Tenant erasures need no ledger: `tenant_erasure_records` (key `ter_<tenant_key>`) already
carries the tenant key and survives.

**PRIV-710** The ledger MUST be excluded from the dump? — No: it must be **in** the dump so
that a restore of an older dump finds the entries made after it... which it cannot (they
are newer than the dump). Correct design: the ledger lives in ArangoDB **and** is mirrored
append-only to a small object `privacy/replay-ledger.jsonl` in the backup bucket (encrypted
with the Fernet key) at each erasure completion; restore reads the mirror. The mirror is
rewritten (filtered) by the purge beat. Acceptance TA-709.

### 6.4 Restore procedure (`docs/de/deployment/backup-restore.md` extension)

**PRIV-711** After `arangorestore` and before the backend accepts traffic, the operator MUST
run `python -m app.migrations.privacy_restore_replay --from-mirror <path>`, which:
1. loads the ledger mirror, skips entries whose `erasure_key` exists as `completed` in the
   restored `erasure_requests` **and** whose tombstone appears in `users`? — the user row is
   gone in a consistent dump; the check is: `users/<user_key>` **exists** in the restored data
   → the dump predates the erasure → re-run `erase_account_now`-equivalent for that key with
   the ledger's tombstone (deterministic from the salt anyway);
2. re-runs tenant erasures for `tenant_erasure_records` in `completed` whose tenant row
   exists in the restored data;
3. replays review-item creation (idempotent keys) and prints a report (counts) persisted as a
   `migration_reports` entry `restore_replay`.

**PRIV-712** The restore drill (docs §"Restore-Drill") MUST include a planted erased account
and verify TA-710: after restore + replay, no row carries the raw key outside the ledger.

**PRIV-713** Attachments bucket versioning and TimescaleDB snapshots MUST follow the same
retention (≤ 35 d); object versions of hard-deleted personal files (`user_personal`, pest
references) are purged by lifecycle rules on the bucket — documented, operator-owned.

---

## 7. Salt rotation (out of scope, constraint recorded)

**PRIV-714** `ERASURE_TOMBSTONE_SALT` MUST NOT be rotated without a re-keying migration that
rewrites every tombstone in the allowlist (`old → new`) in one pass — the Art. 15 tombstone
lookup and the R-06 purge depend on determinism. Not planned; the constraint goes into the
operations docs.

---

## 8. Existing offline records on devices

**PRIV-715** There is no server-side migration for device data. The client migration
(Dexie `version(3)` on `kp-write-queue`) MUST: add `status = quarantined` support, recompute
`expiresAt` with the new defaults (90/30) **only forward** (an entry already older than the
new period is purged at the next sweep with the notice), and delete the PRIV-512 keys on the
next logout. A frontend release note tells users that unsent entries older than 90 days
will be removed at the next start.

---

## 9. Inactive tenants

**PRIV-716** Privacy migrations MUST process tenants in every status **except `deleted`**:
`suspended`, `pending_deletion`, `orphaned` and `importing` tenants hold personal data that
the subject's Art. 17 right covers regardless of the tenant's state. (v0104 writes into
non-active tenants [verified, #2770 item 4] — for a *backfill* that is a defect; for a
*privacy correction* it is required. The two kinds MUST be labelled in the migration
docstring: `kind = "privacy_correction" | "data_backfill"`, and the guard
`test_beats_skip_inactive_tenants` gets a sibling for migrations that checks a backfill uses
`ActiveTenants` and a correction does not.)

---

## 10. Partially completed deletion operations

**PRIV-717** A one-off job `privacy.resume_partial_erasures --older-than 30d` MUST list every
`partially_completed` erasure with its unreached steps and residue (there is no list today),
and re-dispatch them with `attempt_count` reset to allow the backoff to restart; escalation
rows go to the operations endpoint. It is a job, not a migration (it may run any time).

---

## 11. Rollback limitations (per migration)

| Migration | Rollback |
|-----------|----------|
| v0107 tombstone copies → marker | none (information destroyed on purpose); the dry-run report is the record |
| v0108 record-keeping default | removes the explicit `legacy` |
| v0109 keyed performers | drops the new fields if they are all `null`/copies; refuses otherwise |
| reclassify job | none (statutory → shared is one-way) |
| restore replay | none (it re-applies erasures) |

---

## 12. Verification

| ID | Criterion |
|----|-----------|
| TA-700 | Each privacy migration: second run `changed == 0`; AQL binds `tenant_key`; report persisted with only allowed keys. |
| TA-701 | v0107 dry run writes nothing; real run converts planted tombstones in `care_events` and `garden_plan_audit`, counts an undeclared tombstone in a planted non-allowlisted field without changing it, clears a planted `original_filename`. |
| TA-702 | v0109 never sets a `*_user_key` from a typed name; `mcp:<service-key>` is mapped only for an existing service account. |
| TA-703 | Reclassify job turns tombstones into markers for a `none` tenant and leaves a `pflschg_professional` tenant untouched. |
| TA-709 | Ledger entry written at completion; mirror object updated; purged after `expires_at`; mirror filtered. |
| TA-710 | Restore drill: dump taken before an erasure, erasure completed, restore, replay → the raw key is absent from every collection, present only in the ledger until expiry; review items recreated idempotently. |
| TA-716 | A privacy correction processes a `suspended` tenant; a data backfill skips it. |
| TA-717 | Resume job lists and re-dispatches planted `partially_completed` erasures. |
