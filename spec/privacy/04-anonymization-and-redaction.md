# SPEC-04 — Anonymization and Redaction

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-200 … PRIV-249
Depends on: 01 §2 (vocabulary), 02 (field inventory), 03 (when each rule fires)
```

---

## 1. The three replacement forms and what they prove

| Form | Written where [verified] | Linkable? | Is the row anonymous afterwards? |
|------|--------------------------|-----------|----------------------------------|
| `null` / row deleted | `DELETE_STEPS`; `_end_membership` clears `assigned_to_user_key` | no | the attribute is gone; the row may still identify through content |
| marker `_anonymized` (`ANONYMIZED_MARKER`) | `ANONYMIZE_COLLECTIONS` rules with `anonymized_value=ANONYMIZED_MARKER`; R-25 retention patch; attachment storage scope; tenant import for unmapped accounts (`ANONYMIZED_ACCOUNT`) | no — every erased person of a tenant shares the literal | **not by itself**: the row is anonymous only if no free text, photo or co-occurring attribute identifies the person (Recital 26) |
| tombstone `anon_<16hex>` (`compute_tombstone_hash`) | `tombstone_hash` rules (statutory rows), `PSEUDONYMIZE_AUDIT_COLLECTIONS`, tenant erasure pseudonymisation | yes — deterministic per `(user_key, ERASURE_TOMBSTONE_SALT)`, instance-wide | **no**: pseudonymised personal data (Art. 4(5)); the salt is the "additional information" |

**PRIV-200** The package MUST use the terms as above in code comments, API documentation
and user-facing texts: "anonymised" only where the whole row has been reviewed or contains
no identifying content; otherwise "attribution removed" (marker) or "pseudonymised"
(tombstone). The i18n key for the person rendering is `enums.personRef.erased`, with the
German text "entferntes Mitglied" rather than "anonymisiert" **[proposal]** — the current
word promises more than the data delivers.

**PRIV-201** The marker and the tombstone regex MUST have exactly one definition each.
[verified] `_anonymized` is defined four times (`erasure_engine.py:ANONYMIZED_MARKER`,
`models/care_event.py:ANONYMIZED_MARKER`, `attachment_repository.py:ANONYMIZED_MARKER`,
`tenant_export_engine.py:ANONYMIZED_ACCOUNT`), the regex `^anon_[0-9a-f]{16}$` three times
(`erasure_engine.TOMBSTONE_FULLMATCH_REGEX`, `tenant_erasure_executor._TOMBSTONE_REGEX`,
`tenant_export_engine._TOMBSTONE`). Move both to `domain/models/privacy.py` (the domain layer
may import it from every other layer); the existing test
`test_garden_plan_retention.py` that pins three copies equal becomes a guard that there is
one. Acceptance: TA-200.

---

## 2. Tombstone rules

### 2.1 Derivation (kept)

**PRIV-202** The derivation `anon_ + sha256(user_key + salt)[:16]` MUST NOT change for
existing data: statutory and audit rows written over years must stay linkable to each other
and the Art. 15 tombstone lookup (REQ-025 §3.1.2 rule 6) depends on it. [verified] It is
plain SHA-256 with a concatenated salt, not HMAC, truncated to 64 bits; the sibling
derivations (`compute_request_key`, `log_subject`) use HMAC with a purpose label. Recorded as
DEC-04; a future key rotation needs a re-keying migration (`09` §7) and is out of scope.

**PRIV-203** New derivations introduced by this package (none are strictly required; e.g. a
review-item key) MUST use HMAC with a purpose label, not `sha256(x + salt)`. The client-event
digest key reuse of `erasure_tombstone_salt` (REQ-053 §32.6 Pkt. 16, SEC-003) is noted, not
changed here.

### 2.2 Where a tombstone may exist

**PRIV-204** Tombstones MUST exist only in the **tombstone allowlist**, derived from the
inventory (no second list): every collection/field that has a `tombstone_hash` rule in
`ANONYMIZE_COLLECTIONS` or an entry in `PSEUDONYMIZE_AUDIT_COLLECTIONS`. [verified today]:
`harvest_batches.harvested_by_key`, `quality_assessments.assessed_by_key`,
`treatment_applications.applied_by_key`, `inspections.inspected_by_key`,
`garden_plan_audit.user_key` (→ marker after DEC-16), `erasure_requests.user_key`,
`mcp_audit_log.service_account_key`, `security_audit_log.actor_user_key/target_user_key`,
`consent_records.user_key`.

**PRIV-205** Any process that copies an account-shaped value from one row to another
(backfill mapper, consistency job, tenant import, task completion engine writing
`harvested_by_key=event.performed_by_user_key`, supersede keeping the predecessor's performer)
MUST pass the value through one function `carry_account_reference(value) -> str | None`:
a current-shaped key is returned as is; a tombstone or the marker becomes `_anonymized`
when the target is a marker field and `null` when the target is a tombstone field (a
pseudonym must never be re-minted from a copy). [verified defect] `account_of` in
`care_event_backfill_mapper.py` accepts any non-blank string (#2770 item 1).

**PRIV-206** A consistency check (`privacy.consistency`, new beat, `08` §6) MUST report every
tombstone-shaped value outside the allowlist and every marker in a tombstone field, per
collection, as counts; the finding is a defect, never silently corrected except by the
one-off migration of `09` §3.

**PRIV-207** The `erased`-rendering MUST treat a tombstone-shaped value like the marker
(`display_performer` today checks only `ANONYMIZED_MARKER` [verified]; a tombstone renders
"anonymisiert" only because the user document is missing). The `performed_by` filter MUST
refuse a tombstone-shaped value as it refuses the marker (422) [verified gap: only the exact
marker is refused].

### 2.3 Linkability as a legal question

**PRIV-208 [legal LEG-15]** Whether one deterministic pseudonym per person across all
statutory rows for up to five years is proportionate (vs. per-row random tokens that still
satisfy the record's content) is for counsel. The current design argues: the pseudonym lets
an inspector check that the same (unnamed) applicator treated several plots — a property the
record needs; and it lets the person's own Art. 15 export find the rows. The package keeps
it for statutory and security-audit rows and removes it from `garden_plan_audit` (DEC-16),
where neither argument applies.

---

## 3. Anonymisation rules (account erasure)

### 3.1 Rule set

**PRIV-209** The rule set MUST remain the single `ErasureEngine` inventory; this package adds
attributes, not a second engine. Required additions (see `08` §2 for the dataclass changes):

| Rule attribute | Meaning |
|----------------|---------|
| `attribution` | role from `01` §4.1 |
| `retention_class` | `ephemeral`, `shared_history`, `statutory`, `audit` |
| `review_fields` | free-text fields of the row that go to the review queue when the rule fires (e.g. `care_events: summary, reason, observed_outcome, product_label, material, performed_by_label`) |
| `clear_fields` (exists) | free-text fields that are **cleared** at erasure (typed display names, `user_agent`) |

### 3.2 What is cleared, what is reviewed, what is kept

**PRIV-210** Clearing (`clear_fields`) MUST stay limited to fields whose *only* purpose is to
name the account holder: `harvester`, `assessed_by`, `inspector`, `applied_by`,
`consent_records.user_agent` [verified]. Content free text is never cleared automatically
(REQ-025 §3.1.3 rule 4 "never key on free text"; REQ-053 E-16).

**PRIV-211** [proposal] Two fields MUST be added to `clear_fields` because they are
identity-bearing by construction, not content:
- `attachments.original_filename` → `""` (a camera/phone file name commonly contains the
  owner's name; the stored object key never did);
- `care_events.performed_by_label` **only when** `performed_by_user_key` is the subject? —
  No: the label names a *third party*, not the subject; it stays and goes to review.

**PRIV-212** [proposal] Content free text of the subject's rows in a shared tenant MUST be
kept **and** listed for review (§5). The list of reviewable fields is the registry's
`review_fields`; `02` §3 gives the full inventory. Minimum set (verified fields):

| Collection | Reviewable fields |
|------------|-------------------|
| `care_events` | `summary`, `reason`, `observed_outcome`, `product_label`, `material`, `performed_by_label`, `void_reason`, `redaction_reason` |
| `plant_diary_entries` | `title`, `text`, `tags`, `analysis.summary` |
| `task_comments` | `comment_text` |
| `tasks` (assigned or created by the subject — `tasks` has no `created_by` [verified]; only assignee rows) | `name`, `instruction`, `completion_notes` |
| `garden_objects` | `label`, `notes` |
| `bed_templates` | `name` |
| `locations` created from a template of the subject (`template_key` lineage) | `name` (copied), `description`, `notes` |
| `garden_plan_audit` rows with the subject as actor | `summary`; `snapshot` (import snapshot) |
| `attachments` | `caption` |
| `manual_overrides` | `reason` |
| `harvest_batches`, `quality_assessments`, `inspections`, `treatment_applications` (if `record_keeping = none`, else kept as statutory) | `notes` |

**PRIV-213** `care_events.material` MUST join the redaction field set `FREE_TEXT_FIELDS`
(code `models/care_event.py`) and the spec lists (REQ-053 GP-FR-109, NFR-011 R-25) — a
**spec change proposal**, not a silent change: the field is free text (≤ 200), exported in
the CSV, and today untouched by redaction and R-25 [verified]. Likewise
`measurements[].source` and `measurements[].extraction_method` (free strings) MUST be
redacted with the set.

### 3.3 Backfilled and derived rows

**PRIV-214** The backfill mapper and the consistency job MUST set `created_by = null`
(system origin) and `performed_by_user_key` only through `carry_account_reference` from a
field of the **same attribution role** (`applied_by_key`, `harvested_by_key` are
`performed_by`; `watering_events.performed_by` is free text → never). [verified] The mapper
already refuses labels and sets `created_by = None`; it does not refuse tombstones.

**PRIV-215** Rows with system origin (`trigger ∈ {backfill}` and `created_by = null`) MUST
grant correction rights to the **performer**: `care_event_service` lets `created_by == user`
or a lead correct [verified]; add `or (created_by is None and performed_by_user_key == user)`.
This replaces the suggestion in #2770 item 3 for backfilled rows (where there is no author);
live reminder rows get `created_by = principal` (`03` §4.2).

---

## 4. Audit trail behaviour

### 4.1 Garden plan audit

**PRIV-216** [DEC-16, spec change proposal] `garden_plan_audit.user_key` MUST move from
`PSEUDONYMIZE_AUDIT_COLLECTIONS` (tombstone) to `ANONYMIZE_COLLECTIONS` (marker). NFR-011
R-26 states both today [verified contradiction]; GP-NFR-055 argues linkability "so that rows
stay linkable — WP 1.8". The rows are deleted after 365 days (R-26) and with the tenant; the
Art. 15 export does not need linkability (the person's own rows are found by the real key
while the account exists). **[legal LEG-15]**

**PRIV-217** `garden_plan_audit.summary` holds a copy of `Location.name` /
`GardenObject.label` / `Site.name` / zone name [verified] and `snapshot` holds the full plan
export including `notes`/`description`. Both are review fields (PRIV-212) and MUST be
redactable (`[redacted]` in `summary`; `snapshot` → redact `notes`/`description`/`label`
fields inside the JSON through the same allowlist). The audit of a redaction itself writes
only the category (`care_event_repository.py` comment: "The category, never the text")
[verified] — this pattern MUST hold for every audit writer.

**PRIV-218** [verified gap] `garden_plan_audit` rows are readable by every member with a
live display name (`changed_by_name`) and the UI drops `null` actors silently
(`SnapshotPanel.tsx`). After this package: `changed_by` becomes a `PersonRef` (`08` §3),
rendered through the one resolver, `former_member`/`erased` shown as such.

### 4.2 Security audit

**PRIV-219** [unchanged] `security_audit_log` keeps the tombstone for 730 days; it carries no
free text [verified]. New actions for privacy operations (`08` §4): `ERASURE_REQUESTED`,
`ERASURE_COMPLETED`, `EXPORT_REQUESTED`, `CONSENT_CHANGED`, `REDACTION_APPLIED`,
`REVIEW_DECIDED`, `ATTRIBUTION_REMOVED` (PRIV-116). `target_user_key` of an erasure row is
written **as the tombstone from the start** (the key is about to vanish; the request record
already does this).

### 4.3 Redaction audit

**PRIV-220** Every redaction and every review decision MUST produce: a row in
`garden_plan_audit` when the target is a garden-plan collection (existing pattern) **or** a
`security_audit_log` row (`REDACTION_APPLIED`, tenant-scoped) otherwise; plus the
`privacy_review_items` entry's `decision`, `decided_by`, `decided_at`, `reason_code`,
`reason_text` (≤ 500, itself free text — not shown to members, visible to leads of the tenant
and deleted with the item). The *previous value* MUST NOT be stored anywhere (no "undo"
of a redaction — it is a deletion in the Art. 17 sense).

---

## 5. Free-text review queue (Privacy Administration)

### 5.1 Why a queue, not a rule

Automatic deletion keyed on free text is forbidden (REQ-025 rule 4) and wrong (the text is
usually the tenant's agronomic record: "gegossen 10 L", "Blattläuse auf Beet 3"). Reactive
manual redaction without a list is insufficient (#2517). The middle ground: the system
**finds** candidates, a human **decides**, the decision is **recorded**.

### 5.2 Item creation

**PRIV-221** When an account erasure commits (and when PRIV-116 attribution removal runs),
the engine MUST create one `privacy_review_items` entry per `(tenant_key, collection,
row_key)` for every row that (a) carried the subject's key in any attribution role and has at
least one non-empty review field, **or** (b) — only if the subject had a `display_name` of
≥ 3 characters — contains a **name token** of the subject in a review field. Name tokens:
the display name split on whitespace, tokens of ≥ 3 letters, case-insensitive substring
match, computed **before** the user row is deleted and discarded afterwards; the e-mail
local part is **not** used (too many false positives, and it is itself personal data to
handle). The item stores `match_kinds ∈ {authored, performed, name_token}` and the field
names — **never the text, never the token, never the subject's key** (the item's
`erasure_key` links to the request record, whose `user_key` is the tombstone).

**PRIV-222** Items MUST be scoped to **shared tenants only**: a personal tenant of the subject
is deleted; a personal tenant of another person where the subject contributed *is* shared
for this purpose. Statutory rows produce an item only for `notes` and only where the tenant
has `record_keeping = none` or the row is past its statutory period.

**PRIV-223** Item creation MUST be bounded: at most `PRIVACY_REVIEW_ITEMS_MAX_PER_ERASURE`
(default 5 000) per erasure; beyond that the engine records `review_items_truncated = true`
and the tenant's leads see a banner "more rows than listed — use the care-log search by
date". Name-token scanning MUST read with the same bounded, paged AQL as the export
(`test_beat_task_reads_are_paged`).

### 5.3 Review and decision

**PRIV-224** Leads and `management` of the tenant MUST see the queue
(`GET /t/{slug}/privacy/review?status=open|decided`, `08` §5), each item resolving to the
current row through the normal (role-gated) read path, so they look at the live text with the
app's own detail view.

**PRIV-225** Decisions: `redact` (fields listed in the item, or a subset) → the generic
redaction (`§6`); `keep` with `reason_code ∈ {no_personal_reference, agronomic_record,
third_party_consent, statutory}` and optional `reason_text`; `defer` (stays open). A decided
item MUST NOT be re-opened by a later erasure of a *different* subject matching the same row
— a new item is created instead (key includes `erasure_key`).

**PRIV-226** Open items older than `PRIVACY_REVIEW_SLA_DAYS` (default 30) MUST appear in the
tenant's privacy page as overdue and in the platform metric
`privacy_review_items_open{tenant_kind}`; the platform admin sees counts only (REQ-049 P4).
**[legal LEG-08]** whether the controller (LEG-01) may leave the decision to the tenant's
leads, and whether 30 days is acceptable against the "without undue delay" of Art. 17(1).

**PRIV-227** Items and their decisions are deleted with the tenant and after
`PRIVACY_REVIEW_ITEM_RETENTION_DAYS` (default 3 years, aligned with R-06 as the proof of the
erasure's follow-up) — NFR-011 needs a row `R-43` (spec change proposal, `06`).

---

## 6. Generic redaction

**PRIV-228** One redaction endpoint per tenant MUST replace the care-event-only route over
time: `POST /t/{slug}/privacy/redactions` with body `{collection, key, fields[], reason_code,
reason_text?, review_item_key?}`; the existing `POST /care-events/{key}/redact` stays and
delegates. Allowed `(collection, field)` pairs are the registry's `REDACTABLE_FIELDS`
(= the union of `review_fields`); anything else is 422 `redaction.field_not_redactable`.

**PRIV-229** Redaction semantics per field type: string → `[redacted]` (code `REDACTED`);
list of strings (`tags`) → `[]`; nested JSON (`snapshot`) → redact the allowlisted leaf
fields; `photo_refs` → attachments deleted as today (`care_event_repository.redact`, asking
other holders first per `test_stored_object_deletes_ask_for_other_holders`). The row's
`redacted_at`, `redacted_by`, `redaction_reason` are set where the model has them
(`care_events`); other models gain a `redactions: list[{field, at}]` metadata list **only if**
the UI needs to show the chip; otherwise the audit row suffices (decision per collection in
`08` §3).

**PRIV-230** Redaction MUST follow lineage (`02` §5, `DERIVED_FIELDS`): redacting
`bed_templates.name` offers the locations created from it (`template_key`) and their
`garden_plan_audit.summary` copies as a **batch suggestion** in the UI; it does not redact
them automatically (a bed name typed over by the tenant since is theirs). Redacting a
care-event chain redacts the whole supersede chain [verified, GP-FR-109].

**PRIV-231** Who may redact: role `lead` or scope `management` (ACV, `05` §3). Today:
`require_permission(CARE_EVENT, DELETE)` = lead only [verified]. Adding `management` follows
REQ-049 §2.4 ("members, roles …") — **spec change proposal**, because the scope today has no
data rights.

**PRIV-232** Redaction MUST NOT touch anything in another tenant and MUST be idempotent
(redacting an already redacted field is a no-op with 200).

---

## 7. Legacy tombstone and marker migration (see `09` §3 for the procedure)

**PRIV-233** Legacy rows to correct, all **[verified]**:

| Finding | Correction |
|---------|------------|
| `care_events.performed_by_user_key =~ ^anon_[0-9a-f]{16}$` (copied by v0104 / consistency job from erased statutory rows) | → `_anonymized`; count per tenant |
| `garden_plan_audit.user_key` tombstones (after DEC-16) | → `_anonymized` |
| rows written before #1669/#1663 with `*_by_key = null` and a typed display name (`harvester`, `applied_by`, `inspector`, `assessed_by`) | **not** correctable automatically (REQ-025: a name is not a key); listed as review items for the tenant's leads **once**, with `match_kind = legacy_unkeyed_name`, bounded by PRIV-223 |
| `attachments.original_filename` of rows whose `created_by = _anonymized` | → `""` |
| `tenant_export_engine.ANONYMIZED_ACCOUNT` / three regex copies | code consolidation, no data change |

---

## 8. Verification of successful anonymisation

**PRIV-234** After every erasure the executor MUST run the **residue scan** that tenant
erasure already has (`tenant_erasure_executor` residue check reports `undeclared:<collection>`
[verified]) for account erasure too: for every collection with an account-shaped field, count
rows where the field equals the real key **or** the subject's tombstone (outside the
allowlist). A non-zero count marks the erasure `partially_completed` with
`residue = {collection: count}`.

**PRIV-235** The reach tests (`tests/integration/test_account_erasure_reach.py`) MUST gain the
negative cases of `10` §4: tombstone in a non-allowlisted collection, marker in a tombstone
field, name token in the review queue, closed-account rendering.

**PRIV-236** "Anonymised" MUST never be asserted for a row by a marker alone in any report or
UI text; reports say "attribution removed; N free-text rows under review / decided".

---

## 9. Before/after examples

### 9.1 Care event of an erased member (shared tenant)

Before (member "Maren K." erased on 2026-12-01; her key `u_7f3a`):

```json
{"_key":"ce_1","tenant_key":"t_garden","category":"watering",
 "summary":"Maren hat Beet 3 gegossen, 10 L","material":null,
 "performed_by_user_key":"u_7f3a","created_by":"u_7f3a","performed_by_label":null}
```

After the erasure commit (today's behaviour, kept):

```json
{"_key":"ce_1","summary":"Maren hat Beet 3 gegossen, 10 L",
 "performed_by_user_key":"_anonymized","created_by":"_anonymized"}
```

New: one review item (no text, no name):

```json
{"_key":"rvw_9c…","tenant_key":"t_garden","erasure_key":"erq_…","collection":"care_events",
 "row_key":"ce_1","fields":["summary"],"match_kinds":["performed","name_token"],
 "status":"open","created_at":"2026-12-01T04:12:00Z"}
```

Lead decides `redact` → row: `"summary":"[redacted]"`, `redacted_at/by/reason` set,
`garden_plan_audit` row `{op:"redact", entity:"care_event", summary:"watering"}`; item
`status:"decided", decision:"redact", decided_by:"u_lead"`.

API rendering of the row to a grower, before and after: `performed_by: null`,
`performed_by_kind: "erased"` (today: `performed_by: "anonymisiert"`).

### 9.2 Treatment application (statutory tenant)

Before: `{"applied_by":"Maren K.","applied_by_key":"u_7f3a","notes":"Neem auf Tomaten, Maren hat die Dosis halbiert"}`
After (unchanged today): `{"applied_by":"","applied_by_key":"anon_3b9f…","notes":"… Maren hat …"}`
New: review item for `notes` **only if** `record_keeping = none` or the row is past R-17;
otherwise the row stays as is (statutory content) — LEG-04 may change this.

### 9.3 Legacy copied tombstone

Before (written by v0104 on 2026-11-07): `care_events.performed_by_user_key = "anon_3b9f…"`
After migration `09` §3: `"_anonymized"`; report `{tenant: t_garden, corrected: 12}`.

### 9.4 Bed template name

Before: `bed_templates {name:"Omas Hochbeet", created_by:"u_7f3a"}`;
`locations {name:"Omas Hochbeet", template_key:"bt_1"}`;
`garden_plan_audit {op:"delete", summary:"Omas Hochbeet"}`.
After erasure: template `created_by:"_anonymized"`, name kept; review items for the
template (`name`), the location (`name`, lineage `template_key`) and the audit row
(`summary`). Lead redacts the template and accepts the batch suggestion → all three
`[redacted]`; or keeps with `reason_code: no_personal_reference` ("Oma" is not the member).

---

## 10. Acceptance (summary)

| ID | Criterion |
|----|-----------|
| TA-200 | One definition of the marker and of the tombstone regex; a planted second copy fails the guard. |
| TA-201 | `carry_account_reference` maps tombstone/marker → marker for marker fields, → `null` for tombstone fields, label → `null`. |
| TA-202 | Consistency beat reports a planted tombstone in `care_events` and a planted marker in `treatment_applications.applied_by_key`. |
| TA-203 | Filter by a tombstone-shaped `performed_by` → 422. |
| TA-204 | `material` and measurement strings are redacted with the set, by redaction and by R-25. |
| TA-205 | Review items are created for authored rows and name-token rows, store no text/token/key, are idempotent per erasure, and bounded. |
| TA-206 | Generic redaction refuses a non-allowlisted field, is idempotent, writes the audit row with category only, never stores the old value. |
| TA-207 | `garden_plan_audit.user_key` receives the marker; a planted tombstone there is reported. |
| TA-208 | Residue scan marks an erasure `partially_completed` when a planted row keeps the real key or the tombstone outside the allowlist. |
| TA-209 | `original_filename` is cleared at erasure. |
