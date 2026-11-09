# SPEC-03 — Account and Membership Lifecycle

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-100 … PRIV-139
Depends on: 01 (vocabulary, components), 04 (what the marker/tombstone mean), 06 (periods)
```

This document specifies the complete lifecycle of a subject's relationship with the
platform and with each tenant: account deletion, membership termination, tenant deletion,
rejoining, deletion requests during offline operation, deletion of users with statutory
records, and reprocessing after partial failure. For every related record it states the
expected behaviour. Verified facts are marked **[verified]**, new behaviour **[proposal]**.

---

## 1. States

### 1.1 Account

| State | Definition [verified unless marked] | Observable |
|-------|---------------------------------------|------------|
| `active` | `users.is_active = true`, no `erasure_requests` row in `scheduled`/`in_progress` | login works |
| `closed` | `request_erasure` ran: `is_active=false`, `password_hash=None`, all refresh tokens revoked, personal-tenant invitations revoked, organisations settled (INV-1), members of personal tenants notified; `erasure_requests.status = scheduled`, `hard_delete_scheduled_at = now + R-01` | no login; **[proposal]** display name no longer resolvable for other members (PRIV-104) |
| `erasing` | `claim_for_run` succeeded (`status = in_progress`, 6 h stale window) | — |
| `partially_completed` | an attempt failed or left unreached steps; `attempt_count`, `next_attempt_at` (backoff `min(2^(n-1), 7)` days), escalation log at attempt 5 | admin sees it at `GET /admin/platform/erasures/{key}` |
| `erased` | `users` row removed; `erasure_requests.user_key` is the tombstone; `status = completed` | nothing resolves; rows carry marker/tombstone |
| `purged` | `erasure_requests` row deleted by R-06 (3 years, only when `user_key` is a tombstone) | — |

There is **no cancel** of an account erasure request **[verified]** (`privacy_service.py`
docstring: "there is no cancel route, the password hash is dropped with the request").
This package keeps that decision; see §7.3 for its consequence on offline devices.

### 1.2 Membership (per tenant)

| State | Definition | Record |
|-------|------------|--------|
| `invited` | `invitations` row (e-mail-bound or link) | invitation |
| `member` | `memberships` row, `is_active = true`, `role`, `admin_scopes`, `joined_at` | membership |
| `former` | **no row** — `leave_tenant` / `remove_member` / `admin_remove_membership` hard-delete the membership and its edges and `location_assignments` **[verified]** (`membership_repository.py:130-142`); only `security_audit_log` (`MEMBERSHIP_LEFT` / `MEMBERSHIP_REMOVED`, with `old_role`, `old_scopes`, 730 days) records that the person was a member | derived: "account key present in tenant rows, no active membership" |
| `deactivated` | `is_active = false` — used only by tenant erasure/import (`deactivate_all_for_tenant`) | membership |

**[verified]** There is no `status`, `left_at` or membership history on the model
(`domain/models/membership.py`). **[proposal, DEC-05]** This package does **not** add one:
the former-member state is derived at read time (§3), and the security audit remains the
record of who was a member when. Rationale: a `former_members` collection would be a new
store of personal data with its own retention; the derived state needs none.

### 1.3 Tenant

**[verified]** `TenantStatus ∈ {active, suspended, pending_deletion, orphaned, deleted, importing}`
(`common/enums.py`); only `active` resolves a slug (`_membership_for_slug`, same 403 for
unknown / inactive / no membership). Deletion: `delete_tenant` (lead **and** `management`,
step-up) → `pending_deletion` for `RETENTION_TENANT_ERASURE_GRACE_DAYS` (default 90, ceiling
90, 0 allowed) → `resume_tenant_erasures` (04:30 UTC) runs the tenant inventory → `deleted`.
`cancel_tenant_erasure` exists. `TenantType ∈ {personal, organization}` only — there is no
`community` or `commercial` type in code.

---

## 2. Account deletion

### 2.1 Request (as implemented, unchanged)

**PRIV-100** The request path MUST stay as implemented [verified]: step-up
(`StepUpVerifier`: echoed e-mail, current password or e-mailed code; API keys and service
accounts refused; lockout 429 `STEP_UP_LOCKED`), idempotent record key
`compute_request_key` (`erq_` + HMAC), `find_active_for_user` refuses a second request,
immediate closure, organisation settlement, member notice. `DELETE /users/me` opens the
same request (REQ-023 §3.9).

### 2.2 Grace period behaviour (new)

**PRIV-101** [proposal] While the account is `closed`, the person's data MUST be treated as
*restricted* (Art. 18 by analogy): no notification is sent to them, no reminder names them,
no task is assigned to them. [verified gap] Today only `is_active` and `password_hash` change;
`DOCUMENT(users/…)` joins still resolve the display name for up to 90 days.

**PRIV-102** [proposal] The subject MUST be able to see the state of the request
(`GET /privacy/erasure/{key}` exists) **without logging in**? — No: the account is closed, so
the status page is reachable only through the e-mail link pattern of the e-mail-change flow.
This package does **not** add an unauthenticated status endpoint (information leak risk); the
confirmation e-mail already states the scheduled date. *Decision recorded as DEC-19.*

**PRIV-103** The hard-delete date MUST NOT be postponed by anything except the member-notice
wait (`RETENTION_ERASURE_MEMBER_NOTICE_DAYS`, 7) already specified in REQ-025 §3.1.3.

**PRIV-104** [proposal] From the moment of closure, `IdentityReferenceRegistry.resolve_display`
MUST return state `erased` for the subject's key to every viewer except platform admins
(who need the name for the erasure preview and support). Implementation: the resolver reads
`users.is_active` together with the display name (one extra field in the existing join); a
closed account renders like a missing one. Acceptance: TA-101.

### 2.3 Hard delete (as implemented) and its result per record class

**PRIV-105** The plan order MUST stay: object storage (Phase 0) → pgvector (0.5) → edges →
documents → `ANONYMIZE_COLLECTIONS` → `PSEUDONYMIZE_AUDIT_COLLECTIONS` (2.5) → `users`;
personal tenants are erased through the tenant inventory **before** the plan; the ArangoDB
part is one transaction (`erasure_executor.py`). [verified]

Expected state of every record class after a completed erasure (the table is the normative
contract; `02` lists every field):

| Record class | Today [verified] | Required [this package] | Spec |
|--------------|------------------|-------------------------|------|
| sessions, tokens, API keys, preferences, onboarding, restrictions, exports, email-change, auth providers | deleted | unchanged | — |
| notifications, notification preferences, calendar feeds, AI conversations, identification/diagnosis requests, pest detections, own pest contributions | deleted | unchanged | — |
| memberships, location assignments, accepted invitations | deleted | unchanged | — |
| personal tenant(s) owned by the subject | deleted with everything in them (also other members' rows, who were notified at request time; `retained_late_joiner` exception) | unchanged | REQ-025 Q-E1/Q-E5 |
| shared-tenant rows the subject authored/performed (care events, diary, task comments, garden objects, bed templates, attachments, manual overrides, import jobs, weather configs, dismissed tips, sent invitations) | account refs → `_anonymized`; **all free text kept**; photos kept (EXIF re-strip) | account refs → marker **and** one `privacy_review_items` entry per row with reviewable free text (`04` §5); `attachments.original_filename` cleared (PRIV-211) | `04` |
| `tasks.assigned_to_user_key` | marker | marker (unchanged; a task assigned to nobody) | — |
| `sites.plan.plan_updated_by` | marker | marker | — |
| statutory rows (`harvest_batches`, `quality_assessments`, `treatment_applications`, `inspections`) | key → tombstone, typed display name cleared; `notes` kept | unchanged **pending LEG-03/LEG-04**: if the tenant has no record-keeping duty, these rows MUST be treated as `shared_history` (marker, review) instead | `06` §3 |
| `garden_plan_audit.user_key` | tombstone | **marker** (DEC-16): the plan audit is tenant-internal, not statutory; linkability is not needed; `summary`/`snapshot` free text → review items | `04` §4.3 |
| `security_audit_log.actor/target`, `erasure_requests.user_key`, `consent_records.user_key`, `mcp_audit_log.service_account_key` | tombstone | unchanged | `06` |
| `ai_audit_log.user_key` | marker | unchanged | — |
| `tenants.owner_user_key` of a surviving organisation | marker (REQ-056 §9.1 handover planned, not implemented) | unchanged until REQ-056 lands | — |
| `care_events` rows whose `performed_by_user_key` holds the subject's **tombstone** (copied by v0104/consistency job) | untouched — the rule matches the real key only | reached: `04` §3.3 forbids tombstones here; migration `09` §3 corrects legacy copies | #2770 |
| device storage on the subject's devices | this device wiped (`AccountSettingsPage` → `clearOfflineData({discardWriteQueueOf})`); other devices keep the write queue until 90/365 days | dead-session quarantine `07` §7 | `07` |

**PRIV-106** [proposal] The erasure report (`erasure_requests` collection lists and counts)
MUST additionally record `review_items_created` per tenant and `tombstone_copies_corrected`
so that the operator can see that the new phases ran. No row content, no tenant names.

### 2.4 Partial failure and reprocessing

**PRIV-107** The claim/retry mechanics MUST stay [verified]: `claim_for_run` with a 6 h stale
window, `pre_arango_completed_at` checkpoint (storage phases are not repeated), transactional
ArangoDB plan (all-or-nothing), `partially_completed` with backoff, configuration errors hold
without spending an attempt, a tombstoned `user_key` means "committed".

**PRIV-108** [proposal] The two new phases (review items, replay ledger) MUST run **after**
the ArangoDB transaction committed and MUST be idempotent on their own keys
(`privacy_review_items._key = hash(erasure_key, collection, row_key, field)`;
ledger key = `erasure_key`). A failure in these phases MUST NOT roll back the erasure (the
right is satisfied; the follow-ups are retried by the next beat as `post_commit_pending`).

**PRIV-109** [proposal] Escalation thresholds MUST be the same for account and tenant erasure.
Today account erasure escalates at attempt 5 (`ERASURE_ESCALATE_AFTER_ATTEMPTS`), tenant
erasure at 3 (`TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS`). Recommendation: 3 for both,
one setting `PRIVACY_OPERATION_ESCALATE_AFTER_ATTEMPTS`. Acceptance: TA-108.

**PRIV-110** [proposal] An erasure in `partially_completed` for longer than
`PRIVACY_OPERATION_STALE_ALERT_DAYS` (default 14) MUST be visible as a metric
(`privacy_operations_open{kind,status}`) and in `GET /admin/platform/privacy/operations`
(`08` §5). Today the only signal is the log field `open_failing`.

---

## 3. Membership termination

### 3.1 What happens today [verified]

`leave_tenant`, `remove_member`, `admin_remove_membership`, service-account removal:
INV-1 guard (last `management` cannot leave), step-up for removal, membership row deleted
with edges and `location_assignments`, `security_audit_log` row, `_end_membership` clears
`tasks.assigned_to_user_key` in that tenant and deletes the member's calendar feeds there.
**Nothing else changes**: every `performed_by`/`created_by`/`actor` reference of the former
member stays, their display name keeps resolving for all members, the care-log filter by
that person keeps working for leads, their rows stay in CSV exports with their name.

### 3.2 Required behaviour

**PRIV-111** Membership termination MUST NOT delete, mark or pseudonymise any domain row.
Rationale: the rows are the tenant's history (Art. 6(1)(f) of the tenant and its members);
the person still exists and may exercise Art. 15 over them (the Art. 15 manifest reads
tenant-scoped sources only in current tenants — REQ-025 §3.1.2 rule 4 — so a former tenant's
rows drop out of the person's own export; **[legal] LEG-06(b)** whether that is acceptable).

**PRIV-112** [proposal, DEC-05] After `RETENTION_FORMER_MEMBER_NAME_DAYS` (default **90**,
floor 0, ceiling 365; **[legal] LEG-06(a)**) from the membership end, the former member's
display name MUST NOT be resolved for other members of that tenant: `resolve_display` returns
state `former_member` with `display_name = null`. Before the period elapses the name is
shown so that hand-overs ("who last watered bed 3?") keep working. The membership-end
instant is read from `security_audit_log` (`MEMBERSHIP_LEFT`/`REMOVED`, `created_at`); if no
audit row exists (pre-#2111 departures), the key is treated as suppressed immediately.

**PRIV-113** [proposal] Leads and `management` MAY still resolve a former member's name for
the same period **plus** the time needed for accountability questions? — No: the suppression
applies to every role in the tenant; the platform admin sees the account (if it exists) in
`/admin/platform/users`. Rationale: the tenant's accountability interest is time-bound; the
name is still in the security audit (730 days) for genuine disputes, readable by the platform
admin only.

**PRIV-114** [proposal] The care-log `performed_by` filter and the CSV export MUST treat a
suppressed former member like an erased one: the filter value is refused with 422
(`care_event.filter_target_unavailable`), the CSV shows the `former_member` rendering.

**PRIV-115** [proposal] The leaving member MUST be told, in the leave dialog and in the
removal notice, that their contributions remain in the tenant's history, that their name is
shown to members for N more days, and how to request erasure (link to Art. 17 self-service)
— the information duty of Art. 13(2)(a)/(b).

**PRIV-116** [proposal, MAY] A member leaving a tenant MAY request *attribution removal* in
that tenant (Art. 21 objection, Art. 17(1)(c)): their account references in that tenant are
set to the marker immediately and review items are created for the tenant's leads. This is a
tenant-scoped subset of the erasure plan (`ANONYMIZE_COLLECTIONS` filtered by `tenant_key`),
not a new rule set. Statutory rows are exempt where LEG-03 applies. Priority P2.

### 3.3 Rejoining

**PRIV-117** [verified] Rejoining creates a new `memberships` row with a new `joined_at`; the
old rows of the person are untouched and resolve again because the key is the same.

**PRIV-118** [proposal] On rejoin, suppression (PRIV-112) ends automatically for that tenant
(the derived state becomes `member` again). If the person used PRIV-116, the markers stay —
a marker is irreversible by design (the mapping is gone). The rejoin dialog MUST say so.

---

## 4. Attribution at write time (who is stored)

### 4.1 Rule

**PRIV-119** Every write path MUST stamp account references from the **authenticated
principal** of the request, never from the body (REQ-053 GP-NFR-054 [verified for care
events]). The principal of an MCP tool call is the service account (`ctx.principal`); of a
task-queue completion the token's user (`CompletionActor.user_key`); of a notification
action the acting user; of a Celery job **no one** (`null`).

### 4.2 Verified deviations and required fixes

| Path | Today | Required | Issue |
|------|-------|----------|-------|
| REST `POST /plants/{key}/confirm`, notification action | caller stored | unchanged | — |
| task-queue completion → `record_care_task_completion` | `performed_by_user_key = null` (`_bed_event_for` called without `user_key`) | caller (`ctx.user_key` available at `tasks/tenant_router.py`) | #2770 item 2 |
| MCP `ConfirmCareTask` | `null` | service-account key (`account_type: service`), rendered `service_account` | #2770 item 2 |
| live reminder/confirmation rows via `map_document` | `created_by = None` → `created_by_me` false, author cannot correct | `created_by = performed_by_user_key` on **live** paths; backfill and consistency job keep `null` (system origin) | #2770 item 3 |
| backfill/consistency `account_of` | copies any non-blank string incl. tombstones | copies only a value that is a current `users._key` *or* writes `_anonymized` for a tombstone/marker; never a label | #2770 item 1, `04` §3.3 |

### 4.3 `confirmed_by`

**PRIV-120** `CareConfirmation` has no actor field [verified]. This package does **not** add
one: the confirmation's care event carries `performed_by_user_key` (the principal) and is the
single attribution; adding a second copy on the confirmation would create lineage to keep in
sync. The registry records `care_confirmations: attribution = none, derived_event =
care_events(source_ref)`.

---

## 5. Deletion of users with statutory records

**PRIV-121** [verified] Statutory rows survive the account and the tenant: key → tombstone,
typed display name (`harvester`, `applied_by`, `inspector`, `assessed_by`) cleared;
`purge_expired_legal_retention_rows` deletes them only when the tenant no longer exists and
the period (R-16 5 y from `harvest_date`, R-17/R-18 3 y) has elapsed; the Art. 15 export
finds them for a still-active person through the tombstone.

**PRIV-122** [proposal, DEC-11; **legal LEG-03**] A tenant MUST declare whether a statutory
record-keeping duty applies: `Tenant.settings.record_keeping ∈ {legacy, none, pflschg_professional,
kcang_association, both}`. Default for existing tenants: `legacy` = today's behaviour (all
statutory rules apply). For `none`, the four collections are treated as `shared_history`
(marker at erasure, deleted with the tenant, review items). Rationale: PflSchG §11 binds
*professional* users and the KCanG documentation duties bind cultivation associations; a
hobby garden has no Art. 6(1)(c) basis to keep a pseudonymised harvest record for five years
after the person asked for erasure. The operator confirms the value; the UI explains the
consequence.

**PRIV-123** [**legal LEG-04**] Whether the applicator's *name* must remain legible in a
PflSchG §11 record for the whole period (today it is cleared at erasure and only the
pseudonym stays) is unresolved. If counsel says yes, the alternative design is: keep the
display name in a sealed field `applied_by_sealed` readable only by `management`+`lead`
with a step-up, cleared at the statutory end. No code change until decided.

**PRIV-124** `pest_control`/`ipm` care events MUST follow the care log, not the statutory
record: at tenant erasure they are deleted [verified comment at
`tenant_erasure_engine.py`], at account erasure they carry the marker, at R-25 they wait for
the PflSchG cutoff (`care_event_pflschg_cutoff = max(R-25, R-17)`) [verified]. The
`treatment_applications` row is the only §11 proof (REQ-053 §13.2, E-16). **[legal] LEG-07**
confirms this reading.

---

## 6. Tenant deletion

**PRIV-125** [verified, unchanged] `pending_deletion` for the grace period, members notified
with an Art. 20 export window, cancellable, then: tenant inventory deletes every tenant-scoped
collection (care events incl. `pest_control`, diary, tasks, attachments, memberships
deactivated then deleted, `client_event_tombstones`), statutory rows pseudonymised,
`security_audit_log` kept, TimescaleDB readings purged, `tenant_erasure_records` kept until
the longest retained statutory row or 5 years (R-06a).

**PRIV-126** [proposal] The new collections `privacy_review_items` and (if separate)
`redaction_log` MUST be in `TenantErasureEngine.INVENTORY` as `_delete`. The replay ledger
is platform-scoped (`NOT_TENANT_SCOPED` with reason).

**PRIV-127** [proposal] Orphaned tenants (`orphaned`, REQ-024 AK-65) MUST be included in the
privacy-operations monitoring (PRIV-110) because their grace timer runs without any member
able to act.

**PRIV-128** [verified gap, **legal LEG-13**] The tenant export archive (REQ-056 §8,
`members.jsonl` with `user_key`, `display_name`, role, scopes; site GPS) leaves the
installation. This package records the question; no change proposed here.

---

## 7. Deletion and offline operation

**PRIV-129** [verified] On the device where the erasure is requested,
`AccountSettingsPage` wipes read cache and the subject's write queue before redirecting.

**PRIV-130** [proposal] On every other device of the subject, the next refresh fails (tokens
revoked). The client MUST treat a refused refresh (401/403) as a **dead session** and
quarantine the stored user's write queue (`07` §7): entries become `quarantined`, are never
replayed, and are purged after `OFFLINE_DEAD_SESSION_GRACE_DAYS` (default 14) unless the
same `user_key` logs in again on that device. A closed account cannot log in, so the
quarantine ends in a purge.

**PRIV-131** [proposal] The server MUST answer a replay from an erased or closed account with
`401` and a stable `error_code` the client can act on. Because the user document is gone
after hard delete, the server cannot distinguish "erased" from "unknown" — so the signal is
emitted during the **closed** phase: refresh and any `/t/{slug}/…` write from a closed
account answer `401 account.closed`. The client purges the queue immediately on that code.
After hard delete the generic 401 falls back to the quarantine of PRIV-130.

**PRIV-132** A buffered write MUST NOT be accepted after the account is closed: the write
path already requires an active membership and `users.is_active` [verified via
`_membership_for_slug`]; TA-131 pins it for the `client_event_id` paths
(`POST /care-events`, `/tasks/{key}/complete`, photo uploads).

**PRIV-133** [verified] `client_event_tombstones` (ids of deleted buffered writes, random
UUIDs, TTL 395 days) carry no personal data; they are deleted with the tenant.

---

## 8. Service accounts

**PRIV-134** [verified] Service accounts (`account_type: service`) cannot request erasure
(step-up refuses API keys/service accounts). Their removal is a membership removal plus key
revocation. **[proposal]** Rows stamped with a service account's key render as
`service_account` with the account's label (not a person); at removal of the service account
the label is suppressed like a former member (PRIV-112).

---

## 9. Acceptance criteria (summary; details in `10`)

| ID | Criterion |
|----|-----------|
| TA-100 | After `request_erasure`, every API response that would show the subject's name shows state `erased`; the erasure preview for a platform admin still shows it. |
| TA-101 | PRIV-104: the display join reads `is_active`; a closed account renders like a missing one. |
| TA-102 | A completed erasure leaves no row in any shared collection whose account-shaped field equals the real key **or** the tombstone (except the allowlisted statutory/audit collections). |
| TA-103 | Every reviewable free-text row of the subject in a shared tenant has exactly one `privacy_review_items` entry; a second erasure run creates none. |
| TA-104 | `partially_completed` erasure is listed by `GET /admin/platform/privacy/operations` and counted by `privacy_operations_open`. |
| TA-105 | Account and tenant erasure escalate at the same attempt count. |
| TA-110 | Leaving a tenant changes no domain row; task assignee and calendar feeds are cleared (unchanged behaviour pinned). |
| TA-111 | N days after leaving, `resolve_display` returns `former_member` without a name for every member role; a platform admin still sees the account. |
| TA-112 | Rejoining restores the `member` rendering; markers set by PRIV-116 stay. |
| TA-113 | Filtering the care log by a suppressed former member → 422; the CSV shows the former-member rendering. |
| TA-120 | All four confirmation paths store the principal as `performed_by_user_key` and `created_by`. |
| TA-121 | `account_of` never returns a tombstone or a label; a tombstone source yields `_anonymized`. |
| TA-122 | A tenant with `record_keeping = none` treats the four statutory collections as shared history at erasure. |
| TA-130 | A refused refresh quarantines the queue; `401 account.closed` purges it immediately. |
| TA-131 | A buffered write replayed after account closure is refused on every `client_event_id` path. |
