# SPEC-08 — API and Data Model Changes

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-600 … PRIV-649
Depends on: 01 §3 (components), 03–07 (behaviour); BACKEND.md / FRONTEND.md style guides;
NFR-016 (migrations), NFR-006 (error format)
```

Every change below is **additive** unless marked *breaking*; where compatibility costs
little it is preserved for one release and the deprecation is stated. Nothing here was
implemented; the existing model was validated first (`02` §4 lists fields that do not
exist).

---

## 1. Principles

**PRIV-600** New metadata extends the existing Pydantic models in
`src/backend/app/domain/models/privacy.py` (`AnonymizationRule`, `PseudonymizationRule`,
`ErasureStep`, `ErasureExclusion`, `DataSourceDefinition`); no parallel registry module. The
existing fields (`collection`, `user_field`, `anonymized_value`, `replacement_strategy`,
`clear_fields`, `rename_fields`, `rename_when`, `reason`) are unchanged.

**PRIV-601** Enum values are additive only; DE/EN i18n in the same PR (project rule).

**PRIV-602** New routes are tenant-scoped under `/api/v1/t/{tenant_slug}/privacy/…` and
platform-scoped under `/api/v1/admin/platform/privacy/…`; every new route goes into the
route-walk isolation matrix, the route-consumer pin and the bounded-list guard (REQ-053
guardrails), and new service methods that load by key and write take `*, tenant_key: str`.

**PRIV-603** Error format follows NFR-006 (`error_code` strings listed in §7).

---

## 2. Registry (domain models)

### 2.1 Attribution and retention class on the inventory entries

```python
# domain/models/privacy.py — additive fields (defaults keep every existing entry valid)
class AttributionRole(StrEnum):
    PERFORMED_BY = "performed_by"; PERFORMED_FOR = "performed_for"; CREATED_BY = "created_by"
    CONFIRMED_BY = "confirmed_by"; MODIFIED_BY = "modified_by"; ASSIGNED_TO = "assigned_to"
    OWNER = "owner"; ACTOR = "actor"; RECIPIENT = "recipient"; SUBJECT_OF = "subject_of"

class RetentionClass(StrEnum):
    EPHEMERAL = "ephemeral"; SHARED_HISTORY = "shared_history"; STATUTORY = "statutory"; AUDIT = "audit"

class AnonymizationRule(BaseModel):
    ...  # existing fields unchanged
    attribution: AttributionRole                      # PRIV-001 — required (no default) → every rule names it
    retention_class: RetentionClass = RetentionClass.SHARED_HISTORY
    required_attribution: bool = False                # PRIV-004
    review_fields: list[str] = Field(default_factory=list)   # PRIV-212; free text listed for review

class PseudonymizationRule(BaseModel):
    ...
    attribution: AttributionRole
    retention_class: RetentionClass = RetentionClass.AUDIT
    review_fields: list[str] = Field(default_factory=list)

class ErasureStep(BaseModel):
    ...
    attribution: AttributionRole | None = None        # None for edge/user steps
    retention_class: RetentionClass = RetentionClass.EPHEMERAL

class ErasureExclusion(BaseModel):
    ...
    attribution: AttributionRole | None = None        # free-text "performed_by" fields: None + reason
```

**PRIV-604** `scripts/check_privacy_inventory.py` gains **R7**: every `AnonymizationRule` and
`PseudonymizationRule` has an `attribution`; every account-shaped model field reached by a
rule has exactly one. The unit test `test_privacy_engines.py` gains the same assertion.

### 2.2 Shared constants (one definition)

```python
# domain/models/privacy.py
ANONYMIZED_MARKER = "_anonymized"
TOMBSTONE_PATTERN = re.compile(r"^anon_[0-9a-f]{16}$")
REDACTED = "[redacted]"

def is_tombstone(value: str | None) -> bool: ...
def carry_account_reference(value: str | None, *, target: Literal["marker", "tombstone"]) -> str | None:
    """PRIV-205: a current key passes; marker/tombstone → marker (marker target) or None (tombstone target);
    any other string (a label) → None."""
```

Call sites to repoint [verified]: `erasure_engine.py` (defines today), `models/care_event.py`
(`ANONYMIZED_MARKER`, `REDACTED`), `data_access/arango/attachment_repository.py`,
`domain/engines/tenant_export_engine.py` (`ANONYMIZED_ACCOUNT`, `_TOMBSTONE`),
`data_access/arango/tenant_erasure_executor.py` (`_TOMBSTONE_REGEX`),
`domain/engines/care_event_backfill_mapper.py` (`account_of` → uses
`carry_account_reference`), `domain/engines/task_completion_engine.py`
(`harvested_by_key = event.performed_by_user_key`). The test
`test_garden_plan_retention.py` (pins three copies equal) becomes a guard that the names
are imported, not redefined (AST scan for a second literal `"_anonymized"` in `app/`).

### 2.3 PersonRef and the resolver

```python
# domain/models/person_ref.py (new)
class PersonRefState(StrEnum):
    MEMBER = "member"; FORMER_MEMBER = "former_member"; ERASED = "erased"
    THIRD_PARTY = "third_party"; SYSTEM = "system"; SERVICE_ACCOUNT = "service_account"

class PersonRef(BaseModel):
    state: PersonRefState
    display_name: str | None = None      # only for MEMBER (and SERVICE_ACCOUNT label); never a key
    is_self: bool = False
```

```python
# domain/services/identity_reference_service.py (new; pure resolution, repositories injected)
class IdentityReferenceService:
    def resolve_display(self, keys_or_labels: Iterable[tuple[str | None, str | None]], *,
                        tenant_key: str, viewer: TenantContext, visibility: AttributionVisibility) -> dict[str, PersonRef]:
        """One batched lookup (users.display_name, users.is_active, users.account_type, active membership
        in tenant_key, last MEMBERSHIP_LEFT/REMOVED instant from security_audit_log) → PersonRef per key.
        Rules: PRIV-006/007/008, PRIV-104 (closed → erased), PRIV-112 (former member after N days),
        PRIV-300 (leads_and_self), tombstone/marker/missing → ERASED, label without key → THIRD_PARTY,
        None/None → SYSTEM, account_type=service → SERVICE_ACCOUNT."""
```

**PRIV-605** `display_performer()` in `models/care_event.py` is replaced by a thin adapter
that calls the service result; its `anonymised=` keyword (used by print templates) maps to
the i18n of `PersonRefState.ERASED`.

### 2.4 Lineage registry

```python
# domain/models/privacy.py
class PropagationRule(StrEnum):
    CARRY_ACCOUNT_REFERENCE = "carry_account_reference"   # account fields copied between rows
    REVIEW_SUGGESTION = "review_suggestion"               # content copies → batch suggestion in the review UI
    NONE = "none"                                          # live resolution, nothing stored

class DerivedField(BaseModel):
    source: str          # "collection.field"
    derived: str         # "collection.field"
    via: str             # "backfill_mapper" | "task_completion_engine" | "place_template" | "plan_audit_summary" | "import_snapshot" | "supersede"
    propagation: PropagationRule
    reason: str

DERIVED_FIELDS: tuple[DerivedField, ...] = (...)   # content of 02 §5
```

**PRIV-606** Guard **R8** (`scripts/check_privacy_inventory.py`): every code location that
assigns an account-shaped field from another document's field (AST: attribute → attribute
assignment inside `domain/engines/*` and `domain/services/*`) is listed in `DERIVED_FIELDS`
or in an explicit exclusion with reason.

### 2.5 Redactable fields

```python
REDACTABLE_FIELDS: frozenset[tuple[str, str]]  # derived: union of review_fields over all rules + garden_plan_audit.summary/snapshot leaves
```

### 2.6 Tombstone allowlist

```python
def tombstone_allowed_fields() -> frozenset[tuple[str, str]]:
    """Derived from ANONYMIZE_COLLECTIONS (strategy tombstone_hash) ∪ PSEUDONYMIZE_AUDIT_COLLECTIONS. No second list."""
```

---

## 3. Domain model changes

### 3.1 Care events (additive)

| Field / change | Type | Purpose | Compat |
|----------------|------|---------|--------|
| `CareEventView.performed_by_kind`, `performed_for_kind`, `created_by_kind`, `voided_by_kind`, `redacted_by_kind` | `PersonRefState` | PRIV-007 rendering by kind | additive; `performed_by` string stays for one release (deprecated: still `"anonymisiert"` for erased until removal, then `null`) |
| `CareEventResponse.performed_by_kind` etc. | same | API | additive |
| `FREE_TEXT_FIELDS` += `material`; measurement strings handled by the redaction/retention patch | — | PRIV-213 | behaviour change for redaction/R-25 (spec change proposal) |
| correction right: `created_by is None and performed_by_user_key == user` | — | PRIV-215 | additive |
| `check_performed_by_filter`: refuse tombstone-shaped values (422) | — | PRIV-207 | additive |

### 3.2 Tenants (additive settings)

```python
class AttributionVisibility(StrEnum): ALL_MEMBERS = "all_members"; LEADS_AND_SELF = "leads_and_self"
class RecordKeeping(StrEnum): LEGACY = "legacy"; NONE = "none"; PFLSCHG_PROFESSIONAL = "pflschg_professional"; KCANG_ASSOCIATION = "kcang_association"; BOTH = "both"

class TenantSettings(BaseModel):
    ...  # existing ai_* fields
    attribution_visibility: AttributionVisibility = AttributionVisibility.ALL_MEMBERS   # PRIV-300
    record_keeping: RecordKeeping = RecordKeeping.LEGACY                                 # PRIV-122/401
    shared_device_mode: bool = False                                                    # PRIV-524
```

Defaults equal today's behaviour (no migration needed; `extra="allow"` keeps stored
documents valid). `PATCH /tenants/{slug}` accepts them for `lead ∧ management`; changes are
audited (`TENANT_PRIVACY_SETTING_CHANGED`, old/new value in the existing `reason`-free
shape → add `setting_key`, `old_value`, `new_value` to `SecurityAuditEntry` as optional
strings, no free text).

### 3.3 Users (no new persisted field)

Closed state is derived (`is_active=false` ∧ erasure request exists) — PRIV-104 needs
`is_active` in the display join only.

### 3.4 Free-text performer fields → keyed (migration, `09` §5)

| Model | Today [v] | Target |
|-------|-----------|--------|
| `watering_events.performed_by`, `watering_logs.performed_by`, `tank_fill_events.performed_by`, `maintenance_logs.performed_by` | free text, excluded from erasure | `performed_by_user_key: str \| None` (server-stamped, not in request schema) + `performed_by_label: str \| None` (≤ 80, third party only); the old field becomes the label on migration; UI dialog replaced by "I did it / someone else (label)" |
| `nutrient_plans.author`, `propagation.*.author` | free text, unbounded | `author_user_key` + `author_label` (≤ 80); print template renders through `PersonRef` |
| `inspections.inspector` via MCP `"mcp:<key>"` | pseudo-key in free text | `inspected_by_key = service account key`; `inspector = ""` |
| `workflow_templates.created_by` | free text | `created_by_user_key` + review field |

All new `*_user_key` fields join `ANONYMIZE_COLLECTIONS` (marker, `attribution=performed_by`
/ `created_by`) and `USER_DATA_MANIFEST` (R2 reciprocity) in the same PR.

### 3.5 Attachments

`original_filename` stays a field; erasure clears it (`clear_fields` on the attachment
rule, PRIV-211). No schema change.

### 3.6 Garden plan audit

`PlanAuditRecord.user_key` rule moves to the marker (DEC-16). API `PlanAuditEntry.changed_by:
PersonRef` added; `changed_by_name` deprecated (kept one release, `null` for non-members).

### 3.7 New collections

```python
# collections.py (additive)
PRIVACY_REVIEW_ITEMS = "privacy_review_items"      # tenant-scoped → TenantErasureEngine.INVENTORY _delete
ERASURE_REPLAY_LEDGER = "erasure_replay_ledger"    # platform → NOT_TENANT_SCOPED (reason: re-applies erasures after a restore)
```

```python
class PrivacyReviewItem(BaseModel):
    key: str | None = Field(alias="_key")        # sha256(erasure_key|collection|row_key)[:32] — deterministic, idempotent
    tenant_key: str
    erasure_key: str                              # erasure_requests key (its user_key is the tombstone)
    source_kind: Literal["account_erasure", "attribution_removal", "legacy_unkeyed_name", "record_keeping_change"]
    collection: str
    row_key: str
    fields: list[str]                             # review fields present on the row at creation
    match_kinds: list[Literal["authored", "performed", "modified", "name_token", "lineage"]]
    status: Literal["open", "decided", "void"] = "open"   # void: the row no longer exists
    decision: Literal["redact", "keep"] | None = None
    redacted_fields: list[str] = Field(default_factory=list)
    reason_code: Literal["no_personal_reference", "agronomic_record", "third_party_consent", "statutory", "other"] | None = None
    reason_text: str | None = Field(default=None, max_length=500)
    decided_by: str | None = None                 # account ref, attribution=actor → marker at erasure
    decided_at: datetime | None = None
    created_at: datetime
    # never: text, token, subject key, display name
```

```python
class ErasureReplayLedgerEntry(BaseModel):
    key: str | None = Field(alias="_key")         # = erasure_key
    user_key: str                                 # RAW — the only place after erasure; R-45 purge
    tombstone: str
    completed_at: datetime
    plan_fingerprint: str                         # checksum of the plan collections list used
    expires_at: datetime                          # completed_at + BACKUP_RETENTION_DAYS + 5
```

Indexes (migration `vNNNN`): `privacy_review_items(tenant_key, status, created_at)`,
`(tenant_key, collection, row_key)`, `(erasure_key)`; `erasure_replay_ledger(expires_at)`.
Both collections join the Art. 15 manifest? — `privacy_review_items` discloses nothing about
the subject (their key is gone; the item has no text) → `EXCLUDED_FROM_DISCLOSURE` with
reason; `erasure_replay_ledger` is disclosed to the subject while it exists (it is their
key) — but the subject cannot log in (closed/erased); the admin erasure status shows
"ledger entry present until <date>". Decision: list it in `EXCLUDED_FROM_DISCLOSURE` with the
reason "subject has no login during its lifetime; its existence is shown in the erasure
status". Guard R2 accepts exclusions with reasons [v].

### 3.8 Security audit (additive enum values and optional fields)

```python
class SecurityAuditAction(StrEnum):
    ...  # existing
    ERASURE_REQUESTED = "erasure_requested"; ERASURE_COMPLETED = "erasure_completed"
    EXPORT_REQUESTED = "export_requested"; CONSENT_CHANGED = "consent_changed"
    REDACTION_APPLIED = "redaction_applied"; REVIEW_DECIDED = "review_decided"
    ATTRIBUTION_REMOVED = "attribution_removed"; ATTRIBUTION_EXPORTED = "attribution_exported"
    ATTRIBUTION_FILTER_USED = "attribution_filter_used"            # PRIV-405, counts only
    TENANT_PRIVACY_SETTING_CHANGED = "tenant_privacy_setting_changed"
    TENANT_RECORD_KEEPING_CHANGED = "tenant_record_keeping_changed"

class SecurityAuditEntry(BaseModel):
    ...
    setting_key: str | None = None; old_value: str | None = None; new_value: str | None = None  # enum values only
    row_count: int | None = None                                                                # exports
```

`target_user_key` of erasure rows is the tombstone from the start (PRIV-219).

---

## 4. API changes

### 4.1 Tenant-scoped privacy routes (new; `api/v1/privacy/tenant_router.py`)

| Method & path | Gate | Body / query | Response | Spec |
|---------------|------|--------------|----------|------|
| `GET /t/{slug}/privacy/review` | `privacy.review` (lead ∨ management) | `status=open\|decided\|void`, `collection`, cursor, `limit ≤ 200` | `{items: PrivacyReviewItemResponse[], next_cursor, counts: {open, overdue}}`; each item carries a **resolved row preview** fetched through the normal read path (`detail_url`, current `fields` values) — the preview is computed, never stored | PRIV-224 |
| `POST /t/{slug}/privacy/review/{item_key}/decide` | `privacy.review` | `{decision: redact\|keep, fields?: [], reason_code, reason_text?}` | item | PRIV-225 |
| `POST /t/{slug}/privacy/redactions` | `privacy.review` | `{collection, key, fields[], reason_code, reason_text?, review_item_key?}` | `{redacted_fields, audit_key}`; 422 `redaction.field_not_redactable`; idempotent 200 | PRIV-228 |
| `GET /t/{slug}/privacy/review/suggestions?item={key}` | `privacy.review` | — | lineage batch (locations from a template, audit summaries) | PRIV-230 |
| `GET /t/{slug}/privacy/summary` | `privacy.review` | — | `{open_review_items, overdue, last_erasure_at, settings: {attribution_visibility, record_keeping, shared_device_mode}}` | — |
| `POST /t/{slug}/privacy/attribution-removal` | member (self) | `{confirm: true}` + step-up | 202; tenant-scoped marker run + review items | PRIV-116 (P2) |
| `POST /care-events/{key}/redact` (existing) | lead → lead ∨ management | unchanged body | delegates to the generic redaction | PRIV-228/231 |

### 4.2 Platform routes (new; `api/v1/admin/platform/router.py`)

| Method & path | Response |
|---------------|----------|
| `GET /admin/platform/privacy/operations?kind=account_erasure\|tenant_erasure\|export\|migration&status=…` | list of operation state documents (keys, status, attempt_count, next_attempt_at, residue counts, `review_items_created`, `ledger_present_until`); **no tenant names beyond key, no row content** |
| `GET /admin/platform/privacy/consistency` | last `privacy.consistency` run: tombstones outside allowlist per collection, markers in tombstone fields, open review items per tenant (counts), overdue |

### 4.3 Changed responses (additive)

| Response | Change |
|----------|--------|
| `CareEventResponse` | `+ performed_by_kind, performed_for_kind, created_by_kind, voided_by_kind, redacted_by_kind` (`PersonRefState`); `performed_by`/`performed_for` strings deprecated for the erased case |
| `PlanAuditEntry` | `+ changed_by: PersonRef`; `changed_by_name` deprecated |
| `MemberInfoResponse` | `email` present only for `management`/platform admin (*breaking for viewer/grower clients that read it*; frontend `TenantSettingsPage` adjusted in the same PR) |
| Harvest/IPM responses | `+ harvested_by: PersonRef`, `applied_by_ref: PersonRef`, `inspected_by: PersonRef`; free-text name fields unchanged |
| Diary, task comment, garden object, bed template, attachment responses | `+ created_by: PersonRef` (today: nothing or raw key in MCP) |
| MCP tools `diary.*`, `ipm.*` | `created_by`/`inspector` → `PersonRef` shape; raw keys removed (*breaking for MCP clients*; REQ-033 version bump) |
| `GET /care-events?format=csv` | columns unchanged; values render `R` for non-leads (PRIV-307); `+ Cache-Control: no-store` exists |
| `GET /tenants/{slug}` | `+ settings.attribution_visibility, record_keeping, shared_device_mode` |
| Auth refresh | `401 {error_code: "account.closed"}` for a closed account (PRIV-520) |
| Tenant write paths | `403 {error_code: "membership.ended"}` when the caller's token is valid and a `MEMBERSHIP_LEFT/REMOVED` audit row exists for `(user, tenant)` (PRIV-520) |

### 4.4 Frontend

| Area | Change |
|------|--------|
| i18n | `enums.personRef.{member, former_member, erased, third_party, system, service_account}` DE/EN; drop reliance on the literal `anonymisiert` |
| `HistoryList`, bed history, CSV button | render by `*_kind`; CSV button shows "names included" only for leads |
| Tenant settings page | three new settings with explanations (PRIV-301, PRIV-401, PRIV-524) |
| Privacy admin page (new, `pages/tenants/PrivacyReviewPage.tsx`) | review queue, decide, batch suggestions, summary; lazy chunk (bundle budget) |
| Account page | device section (PRIV-530); leave-tenant dialog text (PRIV-115); attribution-removal action (P2) |
| Offline layer | `quarantined` state, settings from `runtime-config.js`, PRIV-512 key wipe, awaited logout wipe, `KP_CLEAR_DONE` handshake, shared-device mode |

---

## 5. Observability

**PRIV-607** Prometheus metrics (`app/observability/privacy_metrics.py`, new):
`privacy_operations_open{kind,status}` (gauge, set by each beat), `privacy_review_items_open{tenant_kind}`,
`privacy_review_items_overdue`, `privacy_consistency_findings{kind}`,
`privacy_erasure_duration_seconds` (histogram), `privacy_replay_ledger_entries`. No tenant
key as a label (cardinality and privacy); `tenant_kind ∈ {personal, organization}`.

**PRIV-608** Structlog events keep the `sub_…`/`ten_…` pseudonyms (guards exist); new events:
`privacy.review_items_created`, `privacy.redaction_applied` (category only),
`privacy.consistency.completed`, `privacy.ledger_purged`.

---

## 6. Background jobs (additive beats; each in `TENANT_AGNOSTIC_BEATS` or `TENANT_WRITING_BEATS` with reason)

| Task | Schedule (UTC) | Does | Tenant gate |
|------|----------------|------|-------------|
| `privacy.consistency` | 05:20 daily | PRIV-206 scans (tombstones outside allowlist, markers in tombstone fields), open/overdue review counts, metrics | agnostic (read-only counts) |
| `privacy.purge_replay_ledger` (R-45) | 05:25 | delete `expires_at < now` | agnostic |
| `privacy.purge_review_items` (R-43) | 05:30 | delete decided items older than 3 y | agnostic |
| `privacy.post_commit_followups` | 04:05 (after erasures) | retries review-item creation / ledger for erasures flagged `post_commit_pending` | agnostic |
| `retention.purge_notifications` (R-48, proposal) | 05:35 | 90 d after `read_at`, 180 d unread | writing beat → `ActiveTenants` not needed (deletes) |

NFR-011 §3.1 table rows added in the same PR (guard `test_nfr011_task_table_matches_the_beat`).

---

## 7. Error codes (NFR-006)

| Code | HTTP | Where |
|------|------|-------|
| `care_event.filter_target_unavailable` | 422 | filter by marker / tombstone / suppressed former member |
| `redaction.field_not_redactable` | 422 | generic redaction |
| `redaction.row_not_found` | 404 | generic redaction (same body as foreign tenant) |
| `privacy_review.already_decided` | 409 | decide twice with a different decision |
| `account.closed` | 401 | refresh / writes from a closed account |
| `membership.ended` | 403 | tenant write after membership end (valid token) |
| `tenant.record_keeping_downgrade_blocked` | 422 | `record_keeping` statutory → none while a statutory purge job is running |

---

## 8. Settings (environment / `runtime-config.js`)

| Setting | Default | Floor / ceiling | Spec |
|---------|---------|-----------------|------|
| `RETENTION_FORMER_MEMBER_NAME_DAYS` | 90 | 0 / 365 | PRIV-112 |
| `PRIVACY_OPERATION_ESCALATE_AFTER_ATTEMPTS` | 3 | 1 / 10 | PRIV-109 |
| `PRIVACY_OPERATION_STALE_ALERT_DAYS` | 14 | 1 / 60 | PRIV-110 |
| `PRIVACY_REVIEW_ITEMS_MAX_PER_ERASURE` | 5000 | 100 / 50000 | PRIV-223 |
| `PRIVACY_REVIEW_SLA_DAYS` | 30 | 7 / 90 | PRIV-226 |
| `PRIVACY_REVIEW_ITEM_RETENTION_YEARS` | 3 | 1 / 3 | R-43 |
| `BACKUP_RETENTION_DAYS` | 30 (helm `backup.retentionDays`) | 1 / 35 | `09` §6 |
| `ERASURE_REPLAY_LEDGER_GRACE_DAYS` | 5 | 0 / 10 | R-45 |
| `OFFLINE_QUEUE_PENDING_MAX_DAYS` (runtime-config) | 90 | 7 / 365 | PRIV-511 |
| `OFFLINE_QUEUE_UNSENDABLE_MAX_DAYS` | 30 | 1 / 90 | PRIV-511 |
| `OFFLINE_DEAD_SESSION_GRACE_DAYS` | 14 | 0 / 30 | PRIV-511 |
| `OFFLINE_SHARED_DEVICE_MODE` | false | — | PRIV-524 |
| `SHARED_DEVICE_IDLE_MINUTES` | 15 | 1 / 120 | PRIV-524 |
| `PLAN_CACHE_MAX_BYTES` | 20 MB | — | PRIV-505 |
| `QUEUE_PHOTO_MAX_BYTES` | 100 MB | — | PRIV-509 |

All added to `RETENTION_CEILINGS` / `test_retention_ceilings.py` and
`docs/de/reference/environment-variables.md` (DE/EN).

---

## 9. Compatibility summary

| Change | Compat |
|--------|--------|
| new fields on inventory models | internal |
| `*_kind` fields on responses | additive |
| `performed_by` string for erased → stays `"anonymisiert"` one release, then `null` | deprecation notice in OpenAPI |
| `MemberInfoResponse.email` restricted | **breaking** for non-management clients (frontend updated in the same PR; documented in release notes) |
| MCP raw keys removed | **breaking** (REQ-033 tool version) |
| CSV values `R` for non-leads | behaviour change for viewers/growers; documented |
| `material` redacted with the set | behaviour change (more redaction), spec change proposal |
| `garden_plan_audit` tombstone → marker | data migration `09` §3 |
| free-text performer → keyed | migration `09` §5; request schemas accept the old field as `performed_by_label` for one release |
