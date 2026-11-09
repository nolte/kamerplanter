# SPEC-02 — Personal Data Inventory

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-030 … PRIV-049 (inventory rules)
Source of truth for the lists: the code inventories named in REQ-025 §3.1.1; this document
is a *classification* of them, not a copy to be maintained by hand (see §1).
```

---

## 1. How this inventory relates to the code

REQ-025 §3.1 decided (v1.10, #1719) that the lists of personal-data sources live **only in
code** and are guarded. This document therefore does not re-list every disclosure or
erasure entry. It adds the **classification** the code does not yet carry (attribution role,
retention class, review fields, lineage) and states, for each field, what the package
requires. The classification becomes code too (`08` §2: attributes on the existing
dataclasses) and is then guarded by `scripts/check_privacy_inventory.py` rule R7.

**PRIV-030** Every field listed in §3 with a non-empty "Required" column MUST appear in the
registry with the stated values; the guard compares this document's table against the code
(a script `scripts/check_privacy_registry_doc.py` parses the table rows marked `⟂`) so that
the two cannot drift silently — the failure of #1663/#1700/#1716 (hand-maintained copies)
is avoided by making the doc the *test input*, not a parallel truth.

Conventions: `⟂` row is machine-checked; `[v]` verified in code; `[?]` unverified (marked
where the analysis could not confirm); "Erasure"/"Anonymisation" columns describe the
behaviour at **account** erasure (tenant erasure deletes almost everything tenant-scoped —
exceptions are stated). Legal basis values are **proposals** (`06`), except where NFR-011
already states them.

Categories: `IDN` identifier (key, e-mail), `PRO` profile, `AUTH` credentials/session,
`ATTR` attribution (who did/wrote/changed), `TXT` free text, `MED` media, `LOC` location
(coordinates, addresses), `SENS` sensor/behavioural, `CONS` consent/legal state, `AUD` audit,
`DEV` on-device.

---

## 2. Entities without personal data (for completeness)

[v] Global catalogue data (`species`, `cultivars`, `fertilizers`, `substrates`,
`phase_definitions`, IPM catalogue) carry `tenant_key` at most, no account reference and
no personal free text by design. Geometry (`garden_objects.geometry`, `locations.geometry`)
"sind keine personenbezogenen Daten" (GP-NFR-055) — **but** site coordinates are (§3.6).
`client_event_tombstones` hold random UUIDs only [v]. `yield_metrics` has no user field [v].

---

## 3. Inventory

### 3.1 Account and identity (controller: operator)

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility | Retention | Erasure | Anonymisation | Lineage / copies |
|---|--------------|-----|-----------|---------|-------------|------------|-----------|---------|---------------|------------------|
| ⟂ | `users._key` | IDN | yes (pseudonymous identifier) | primary key | 6(1)(b) | internal; **never in API responses** except own profile and admin | life of account | row removed | tombstone in audit/statutory rows; marker elsewhere | referenced by ~30 fields (§3.3–3.6) |
| ⟂ | `users.email` | IDN | yes | login, notices | 6(1)(b) | self; `management` + platform admin ([v] today every member via `/members` — PRIV-305) | life; R-01 then gone | removed | — | `invitations.email`, `email_change_requests`, Art. 15 bundle |
| ⟂ | `users.display_name` | PRO | yes | show who | 6(1)(b) | members per `05` matrix | life | removed | rendering states `former_member`/`erased` | resolved into every attribution rendering; `members.jsonl` of tenant export |
| | `users.avatar_url`, `locale`, `timezone` | PRO | yes | UI | 6(1)(b) | self | life | removed (avatar object: `user_personal` storage rule) | — | — |
| | `users.password_hash`, verification/reset token hashes, `session_generation`, `access_token_generation` | AUTH | yes | auth | 6(1)(b) | none | life; hashes R-08/R-09 | removed; `password_hash` nulled at request | — | — |
| | `users.is_active`, `email_verified`, `email_confirmed_at`, `failed_login_attempts`, `locked_until`, `last_login_at` | AUTH | yes (behavioural) | security | 6(1)(f) | self/admin | life | removed | — | security audit records flag changes |
| | `users.account_type` (`human`/`service`) | PRO | no (type) | — | — | — | — | — | — | rendering state `service_account` |
| | `auth_providers`, `refresh_tokens` (incl. `ip_address` R-03, `device_info`) | AUTH | yes | sessions | 6(1)(b)/(f) | none | token expiry; IP 7 d | deleted | IP anonymised | — |
| | `api_keys` (hash, label, IP allowlist, `tenant_scope`) | AUTH | yes (label, IPs) | M2M | 6(1)(b) | owner, `technical` | life of key | deleted; tenant-scoped keys with the tenant | — | `mcp_audit_log` references |
| | `user_preferences`, `onboarding_states`, `notification_preferences` (push `subscriptions`) | PRO | yes | UI, delivery | 6(1)(b) | self | life | deleted | — | — |
| | `memberships.{user_key, tenant_key, role, admin_scopes, is_active, joined_at}` | IDN | yes | tenant access | 6(1)(b) | members (`/members`), platform admin | until membership end (row deleted) | deleted | — | `security_audit_log` (old role 730 d); `members.jsonl` |
| | `invitations.{email, invited_by_user_key, accepted_by_user_key}` | IDN/ATTR | yes | onboarding | 6(1)(b) | `management` | R-12 30 d | `invited_by` → marker; accepted rows deleted | marker | — |
| | `location_assignments` | ATTR (`assigned_to`) | yes | responsibility hint (REQ-049 §3.5) | 6(1)(b) | members ([v]; `(t)` after PRIV-309) | with membership | deleted | — | bed-list CSV `include_assignment` |

### 3.2 Privacy and audit state (controller: operator)

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility | Retention | Erasure | Anonymisation | Lineage |
|---|--------------|-----|-----------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `erasure_requests.{user_key, status, step_up, requested_by_subject, members_notified_at, …}` | CONS/AUD | yes → pseudonymised | Art. 5(2) proof | 6(1)(c) | self (status), platform admin | R-06 3 y | `user_key` → tombstone | tombstone | `erasure_replay_ledger` (new, `09` §6) |
| | `data_export_requests`, export bundle `privacy/exports/<user_key>/<key>.json` [v only object key with a user key] | CONS | yes | Art. 15/20 | 6(1)(c) | self | R-05 72 h | deleted | — | — |
| | `processing_restrictions`, `email_change_requests` | CONS | yes | Art. 18/16 | 6(1)(c) | self | R-13 unlimited / R-07 | deleted | — | — |
| ⟂ | `consent_records.{user_key, purpose, granted, ip, user_agent, revoked_at}` | CONS | yes | Art. 7(1) | 6(1)(c) | self, platform admin | R-04 3 y after revocation; IP 7 d | `user_key` → tombstone, `user_agent` cleared | tombstone | — |
| ⟂ | `security_audit_log.{actor_user_key, target_user_key, tenant_key, membership_key, old/new role & scopes, request_id}` | AUD (`actor`) | yes | Art. 32 | 6(1)(c)/(f) | platform admin | R-38 730 d | keys → tombstone; row kept at tenant erasure | tombstone | new actions `04` §4.2 |
| | `mcp_audit_log.{service_account_key, shortened IP}` | AUD | yes | Art. 32 | 6(1)(f) | self (`/privacy/mcp-activity`), admin | 90 d | → tombstone | tombstone | — |
| | `ai_audit_log.user_key`, `ai_conversations.{user_key, title, content}` | AUD/TXT | yes | AI features | 6(1)(a) consent purposes | self | per setting | audit → marker; conversations deleted | marker | — |
| | `tenant_erasure_records`, `tenant_export_requests.requested_by_user_key`, `tenant_import_requests.requested_by_user_key`, `import_jobs.uploaded_by` | AUD/ATTR | yes | proof / ops | 6(1)(c)/(b) | `management`, admin | R-06a / R-40 30 d (not implemented) | → marker | marker | — |
| ⟂ | **new** `privacy_review_items.{tenant_key, erasure_key, collection, row_key, fields[], match_kinds[], status, decision, decided_by, reason_code, reason_text}` | AUD | yes (`decided_by`; `reason_text` free text) | Art. 17 follow-up | 6(1)(c) | tenant `lead`/`management`; admin counts | R-43 3 y after decision; with tenant | `decided_by` → marker | marker | stores **no** text/token/subject key (PRIV-221) |
| ⟂ | **new** `erasure_replay_ledger.{erasure_key, user_key (raw), tombstone, completed_at}` | IDN | **yes, raw key** | re-apply erasure after restore | 6(1)(c) | none (job only) | R-45 `BACKUP_RETENTION_DAYS + 5` | hard delete by beat | — | LEG-11 |

### 3.3 Care log and garden plan (controller: tenant)

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility (`05`) | Retention | Erasure | Anonymisation | Lineage / copies |
|---|--------------|-----|-----------|---------|-------------|-------------------|-----------|---------|---------------|------------------|
| ⟂ | `care_events.performed_by_user_key` | ATTR `performed_by`, optional | yes | coordination, accountability | 6(1)(f) LIA-1 | P (t) | R-25 5 y → marker | marker | marker | from task completion (`CompletionActor`), confirmation principal, backfill `account_of` (tombstone → marker, PRIV-205); supersede keeps predecessor's |
| ⟂ | `care_events.performed_for_user_key` | ATTR `performed_for` | yes | proxy entry | 6(1)(f) | P (t) | R-25 | marker | marker | — |
| ⟂ | `care_events.created_by` | ATTR `created_by` | yes | own-row rights, audit | 6(1)(f) | C: `created_by_me` only | R-25 | marker | marker | `null` on backfill (system) |
| ⟂ | `care_events.voided_by`, `redacted_by` | ATTR `modified_by` | yes | audit | 6(1)(f) | M | R-25 | marker | marker | — |
| ⟂ | `care_events.performed_by_label` (≤ 80 in, 200 stored [v]) | TXT (third party) | yes — **third party** | name a helper without account | 6(1)(f); Art. 14 info by the tenant | all members | R-25 → `[redacted]` | kept; **review** | redaction | CSV `performed_by` column |
| ⟂ | `care_events.summary` (≤ 500), `reason` (≤ 1000), `observed_outcome` (≤ 2000), `product_label` (≤ 200), `void_reason`, `redaction_reason` | TXT | may | record | 6(1)(b)/(f) | all members | R-25 → `[redacted]` | kept; **review** | redaction (lead/management) | CSV; `garden_plan_audit` never copies text [v] |
| ⟂ | `care_events.material` (≤ 200) | TXT | may | record | 6(1)(b) | all members | **not in R-25 set today [v] → PRIV-213** | kept; **review** | redaction | CSV `material` |
| | `care_events.measurements[].source`, `.extraction_method` | TXT | may | record | 6(1)(b) | members | add to set (PRIV-213) | kept; review | redaction | — |
| | `care_events.photo_refs` | MED | may (persons on photos) | record | 6(1)(b)/(f) | members | R-25 → deleted | kept (attachment rules) | redaction deletes | `attachments` |
| | `care_events.client_event_id`, `client_event_digest`, `client_round_id` [v, wave 9] | — | digest keyed with `erasure_tombstone_salt`; includes `user` in the digest input → pseudonymous | replay dedupe | 6(1)(b) | none | with row | with row | — | `client_event_tombstones` (ids only) |
| | `care_events.{tenant_key, site_key, location_key, plant_keys, category, performed_at, trigger, task_key, source_ref, quantity…}` | — | contextual (time pattern) | record | 6(1)(b) | members | R-25 (kept after anonymisation) | kept | — | `source_ref` = lineage to source collection |
| ⟂ | `care_confirmations.{plant_key, reminder_type, action, confirmed_at, notes, task_key, completion_client_event_id}` | TXT (`notes`) | may; **no actor field [v]** | reminder state | 6(1)(b) | members | **none [v]**; with tenant | not reached (no account field) | — | derived `care_events(trigger=reminder)` carries the actor |
| ⟂ | `garden_plan_audit.user_key` | ATTR `actor` | yes | change log | 6(1)(f) | M: `changed_by` ([v] all members see name) | R-26 365 d | **tombstone today → marker (DEC-16)** | marker | — |
| ⟂ | `garden_plan_audit.summary` (≤ 200), `snapshot` | TXT | may (copies of names/labels/notes) | change log, restore | 6(1)(f) | all members | R-26 | kept; **review** | redaction (leaf allowlist) | copies of `Location.name`, `GardenObject.label`, `Site.name`, zone name; snapshot = plan export |
| ⟂ | `garden_objects.created_by` | ATTR `created_by` | yes | authorship | 6(1)(f) | C | life | marker | marker | — |
| ⟂ | `garden_objects.label` (≤ 200), `notes` (≤ 4000) | TXT | may | plan | 6(1)(b) | members | life | kept; **review** | redaction | SVG/PDF/JSON export, audit summary |
| ⟂ | `bed_templates.created_by` | ATTR `created_by` | yes | authorship | 6(1)(f) | C | life | marker | marker | — |
| ⟂ | `bed_templates.name` (≤ 200) | TXT | may ("Omas Hochbeet") | catalogue | 6(1)(b) | members; **exported via GP-API-070 template exchange [v spec: "ohne Personenbezüge"]** | life | kept; **review** | redaction with lineage batch (PRIV-230) | → `locations.name` on `place_template`; → audit `summary`; → template export file |
| ⟂ | `locations.name` (no stored max [v]), `description` (≤ 1000), `notes` (≤ 4000), `soil_profile.notes` | TXT | may | plan | 6(1)(b) | members; SVG/PDF/JSON; **plan cache omits notes/description [v]** | life | kept; **review when created from an erased subject's template or named in a review hit** | redaction | `template_key` lineage; audit summary |
| | `locations.photo_refs`, `cover_photo_ref` | MED | may | bed photos | 6(1)(b)/(f) | members | life | attachments rule | — | `attachments` |
| ⟂ | `sites.plan.plan_updated_by` | ATTR `modified_by` | yes | plan | 6(1)(f) | M | life | marker | marker | plan cache nulls `plan_updated_by_name` [v] |
| ⟂ | `sites.{name, climate_zone}` | TXT | may | plan | 6(1)(b) | members | life | kept; review on hit | redaction | audit summary |
| | `irrigation_zones.name` | TXT | unlikely | plan | 6(1)(b) | members | life | kept | — | audit summary |
| | `tasks.assigned_to_user_key` | ATTR `assigned_to` | yes | responsibility | 6(1)(b) | members (`(t)` for name) | until done / membership end (cleared) | marker | marker | plan cache nulls assignee [v] |
| ⟂ | `tasks.{name (≤200), instruction, suggestion_reason, completion_notes, timer_label, tags}` | TXT | may | work | 6(1)(b) | members | **none [v] → R-47 proposal** | kept; review for assignee rows | redaction | notifications carry task names [v]; `care_events` via completion (`reason`, `material`) |
| | `tasks` — `created_by`/`completed_by` | — | **do not exist [v]** | — | — | — | — | — | — | completer only as `care_events.performed_by_user_key` |
| ⟂ | `task_comments.{created_by, comment_text (≤2000)}` | ATTR/TXT | yes/may | discussion | 6(1)(b) | members | none → R-47 | marker; review | redaction | — |
| | `task_audit_entries.changed_by` | ATTR | always `'system'` [v exclusion note] | — | — | — | — | excluded | — | — |
| | `workflow_templates.created_by` | TXT (free text, not a key [v]) | may | — | 6(1)(b) | members | life | excluded today → **review field** (PRIV-212) | redaction | — |

### 3.4 Plant care logs and statutory records (controller: tenant)

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility | Retention | Erasure | Anonymisation | Lineage |
|---|--------------|-----|-----------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `harvest_batches.harvested_by_key` | ATTR `performed_by`, **required under statutory profile** | yes | harvest record | 6(1)(c) (R-16, if LEG-03) else 6(1)(b) | P | ≥ 5 y from `harvest_date` | → tombstone (statutory) / marker (`record_keeping=none`) | pseudonym | from completion engine `event.performed_by_user_key` |
| ⟂ | `harvest_batches.harvester` (≤ 200, free text) | TXT (typed name) | yes | legacy name field | — | members (`HarvestBatchResponse` [v]) | — | **cleared** [v] | cleared | pre-#1669 rows: `*_by_key = null`, name stays → legacy review item (PRIV-233) |
| | `harvest_batches.notes` | TXT | may | record | 6(1)(c)/(b) | members | R-16 | kept (statutory) / review (`none`) | redaction only if non-statutory | — |
| ⟂ | `quality_assessments.{assessed_by_key, assessed_by, notes}` | as above | | | R-16 | | | as harvest | | |
| ⟂ | `treatment_applications.{applied_by_key, applied_by, notes, applied_at, dosage, product}` | ATTR/TXT | yes | PflSchG §11 record (professional) | 6(1)(c) if LEG-03 | P; members | ≥ 3 y | tombstone + name cleared [v] — **LEG-04** | pseudonym | → `care_events(pest_control)` via backfill (performer carried, PRIV-205) |
| ⟂ | `inspections.{inspected_by_key, inspector, notes}` | as above | yes | PflSchG monitoring | R-18 | | ≥ 3 y | as treatment | | MCP writes `inspector = "mcp:<key>"` [v] → PRIV-310 |
| | `watering_events.{performed_by (free text), notes}`, `watering_logs.{performed_by, notes}`, `tank_fill_events.{performed_by, notes}`, `maintenance_logs.{performed_by, notes}` | TXT (typed name) | yes (name) | operations | 6(1)(b) | members; editable in UI [v] | **none [v] → R-46** | **excluded [v] (free text)** → **migrate to keyed field + label** (`08` §3.4) | after migration: marker | → `care_events(watering/feeding)` without performer [v] |
| | `feeding_events.{notes, material}` | TXT | may | operations | 6(1)(b) | members | none → R-46 | kept | — | → `care_events(feeding)` |
| | `nutrient_plans.author` (free text, **no max [v]**), `propagation.*.author` | TXT (typed name) | yes | authorship | 6(1)(b) | members; **printed on the nutrient-plan PDF [v]** | life | **not in any rule [v]** → keyed field + label (`08` §3.4) | marker | print template |
| ⟂ | `plant_diary_entries.{created_by, analysis_requested_by, analysis_claimed_by}` | ATTR | yes | plant record | 6(1)(b)/(f) | C (t); all members read entries [v] | life | marker [v] | marker | — |
| ⟂ | `plant_diary_entries.{title (≤200), text (≤5000), tags, analysis.summary, analysis.findings}` | TXT | may | plant record | 6(1)(b) | all members; `GET /diary?q=` substring search [v] | life | kept [v]; **review** | redaction | AI analysis derived from text (consent `diary_ai_analysis`) |
| | `plant_diary_entries.photo_refs` | MED | may | record | 6(1)(b) | members | life | storage scope `user_diary_attachments` (bytes kept, `created_by` marker, EXIF re-strip) | — | `attachments` |
| | `plant_instances.plant_name`, `planting_runs.{name, notes}`, `propagation.{name, notes, PhenotypeNote.note}`, `post_harvest.*notes`, `succession_plan.notes`, `aquaponik.*`, `care_profiles.notes`, actuator/schedule `notes`, `manual_overrides.reason` (≤500) | TXT | may (low) | domain | 6(1)(b) | members | life | kept; `manual_overrides.created_by` → marker [v] | review on name-token hit only | — |

### 3.5 Media and attachments

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility | Retention | Erasure | Anonymisation | Lineage |
|---|--------------|-----|-----------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `attachments.created_by` | ATTR `created_by` | yes | ownership | 6(1)(b) | C | life of parent | marker (storage scope) / `pest_reference` deleted / `user_personal` deleted [v] | marker | shared bytes (dedup per contributor since #1770, Art. 19 notice AK-OS-09 **not implemented**) |
| ⟂ | `attachments.original_filename` | TXT (identity-bearing) | often | upload echo | 6(1)(b) | members; Art. 15 bundle | life | **kept today [v] → cleared (PRIV-211)** | cleared | v0062 blanks it on split records [v] |
| ⟂ | `attachments.caption` (≤ 500) | TXT | may | gallery | 6(1)(b) | members | life | kept; **review** | redaction | — |
| | attachment bytes (photos; EXIF stripped on upload and re-stripped at erasure [v]; storage key `t/{tenant}/{category}/{yyyy}/{mm}/{ulid}` — no user in path [v]) | MED | may (faces, places) | record | 6(1)(b)/(f) | members; thumbnails | life of parent | kept for shared categories; `user_personal`/pest reference deleted | — | renditions |
| | `attachments.client_event_id/_digest` [v wave 9] | — | pseudonymous | replay | 6(1)(b) | none | with row | with row | — | — |
| | `pest_image_contributions.{contributed_by, promoted_by}`, pgvector `species_embeddings(source='user_contributed', contributed_by, tenant_key)` | ATTR/SENS | yes | recognition index (consent) | 6(1)(a) | admin | until revocation / erasure | deleted / `promoted_by` marker [v] | marker | — |

### 3.6 Location and sensor data

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility | Retention | Erasure | Anonymisation | Lineage |
|---|--------------|-----|-----------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `sites.gps_coordinates` | LOC | **yes** — personal garden = home address (REQ-025 §3.1.2) | weather, frost, climate zone | 6(1)(b); coordinates rounded to 2 decimals before leaving (DP-002) | members; Art. 15 bundle; **tenant archive (LEG-13)**; GeoJSON WON'T [v] | life of site | with personal tenant; stays in shared tenant | — | weather requests (rounded) |
| | `sensor_readings` (TimescaleDB: `tenant_key`, `sensor_key`, value, `source`, `metadata` JSONB) — **no user column [v]**; `metadata` is a free client dict [?] | SENS | contextual (CO₂/motion/manual override → presence patterns; NFR-001 §6.7 DSFA) | monitoring | 6(1)(b) | members | 90 d raw → 2 y hourly → 5 y daily (fixed SQL; R-14 classification **not implemented [v]**) | with tenant (`delete_by_tenant`) | — | aggregates |
| | `manual_overrides.{created_by, reason}` | ATTR/TXT | yes | actuator override (presence signal) | 6(1)(b)/(f) | members | none | marker [v]; review | redaction | — |

### 3.7 Notifications

| ⟂ | Entity.field | Cat | Personal? | Purpose | Legal basis | Visibility | Retention | Erasure | Anonymisation | Lineage |
|---|--------------|-----|-----------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `notifications.{user_key, title, body, data, read_at, acted_at}` | ATTR `recipient` / TXT | yes | delivery | 6(1)(b) | recipient | **none [v] → R-48 proposal** | deleted [v] | — | texts carry task/plant names, not member names [v measurement] |
| | `notification_preferences.pwa.subscriptions`, Apprise URLs (Fernet) | AUTH | yes | channels | 6(1)(b) | self | life | deleted | — | — |

### 3.8 On-device data (controller: operator for defaults; see `07`)

| ⟂ | Store.key | Cat | Personal? | Purpose | Legal basis (TDDDG §25 / GDPR) | Retention | Cleared on logout? [v] | Required |
|---|-----------|-----|-----------|---------|--------------------------------|-----------|------------------------|----------|
| ⟂ | IndexedDB `kp-plan-cache` (`{key, userKey, tenantKey, cachedAt, data}`; no names, notes, assignments [v]) | DEV | yes (keys, plan) | offline reading | §25(2) Nr. 2 strictly necessary — **proposal, LEG-09**; 6(1)(b) | 15 min TTL; purged at start/read/write | all databases except queue deleted | keep |
| ⟂ | IndexedDB `kp-write-queue` (`id`, `userKey`, `tenantKey`, `capturedAt`, `status`, `write` incl. note text and photo bytes, `bedName`) | DEV/TXT/MED | yes | offline writes | as above | 365 d pending / 90 d unsendable | only the leaving user's rows, after approval | shorten + quarantine (`07`) |
| ⟂ | Cache Storage `kp:{user_key}:{tenant_key}` (latent, empty [v]), `kp-sw-state` | DEV | keys | SW cache | as above | 15 min / session | deleted | keep; fix the persist race (`07`) |
| | Cache Storage precache, `kp-static-assets`, `kp-runtime-config` | — | no | app shell | necessary | — | kept | — |
| ⟂ | localStorage `kp_local_data_owner` (**a `user_key`** [v]) | DEV/IDN | yes | owner check of local data | necessary | — | **no [v]** → clear (PRIV-512) | |
| ⟂ | localStorage `kp-garden-field-mode` (`userKey`, `tenantSlug`, `siteKey`, tab) | DEV/IDN | yes | field-mode resume | necessary | — | **no [v]** → clear | |
| ⟂ | sessionStorage `kp.emailChange.address` (**e-mail**), `kp.stepUp.{token,resume,error}` | DEV/IDN/AUTH | yes | flows | necessary | flow-bound | **no [v]** → clear | |
| | localStorage `kp_active_tenant_slug` | DEV | slug (may derive from a name) | routing | necessary | — | yes | — |
| | localStorage `kp.gardenPlanner.planting.lastUsed.{tenantSlug}` | DEV | tenant slug in key | UX | necessary | — | no | clear on logout (hygiene) |
| | localStorage `kamerplanter:consent:v1`, `plant_identification_consent` | CONS | decision only | consent | necessary | — | no (must survive) | keep |
| | localStorage theme/lang/kiosk/layout/module-visibility/page sizes/dismissed tips/editor prefs | DEV | no | UX | necessary | — | no | keep |
| | sessionStorage `kamerplanter.pendingInvitation` | AUTH | token | onboarding | necessary | flow | yes | — |
| | refresh cookie (HttpOnly [spec; not verified in backend code by the analysis]), CSRF cookie | AUTH | yes | auth | necessary | 30 d | revoked | — |

**Not present [v]**: `redux_state` sessionStorage (REQ-025 §10 row is stale), `i18next` /
`theme` keys (actual keys `kamerplanter-lang`, `kamerplanter-theme`), `device_id` (R-049b
not implemented), any API payload in localStorage (G-W9 a holds).

---

## 4. Fields the task named that do **not** exist (do not invent)

| Named | Finding |
|-------|---------|
| `care_events.note` | no such field; notes go to `summary`/`reason` |
| `care_events.origin` as stored field | server-side dataclass `CareEventOrigin` only |
| `tasks.created_by`, `tasks.completed_by` | absent |
| `CareConfirmation.<actor>` | absent |
| `plant_diary_analyses` | collection does not exist (REQ-051 §5 / REQ-025 AK-DA-04 target a phantom) |
| `TenantType.community/commercial` | only `personal`/`organization` |
| `Membership.status/left_at` | absent |
| `users.deleted_at/status/name` | absent |
| `plant_instances.nickname` | field is `plant_name` |
| `client_event_id` on `tasks` | stored as `tasks.completion_client_event_id` (index v0106) [v] |

---

## 5. Lineage (source → derived copies)

**PRIV-031** The following copies MUST be declared in `DERIVED_FIELDS` (`08` §2.4) with a
propagation rule; the guard R8 checks that every writer of a derived field is listed.

| Source | Derived | Copy semantics | Propagation at erasure / redaction |
|--------|---------|----------------|------------------------------------|
| `treatment_applications.applied_by_key`, `harvest_batches.harvested_by_key` | `care_events.performed_by_user_key` (backfill, consistency) | account ref, same role | `carry_account_reference` (tombstone → marker); erasure rule reaches the copy by key |
| `care_events.performed_by_user_key` (task completion) | `harvest_batches.harvested_by_key` | same role | both reached by their own rules |
| `care_events.performed_by_user_key` (predecessor) | `care_events.performed_by_user_key` (supersede) | same role | chain redaction (exists) |
| `bed_templates.name` | `locations.name` (`place_template`) | content copy; `template_key` keeps provenance | review batch suggestion (PRIV-230) |
| `locations.name`, `garden_objects.label`, `sites.name`, `irrigation_zones.name` | `garden_plan_audit.summary` | content copy at delete time | review; redactable |
| plan export (`locations.*`, `garden_objects.*`) | `garden_plan_audit.snapshot` (import) | full copy | leaf redaction |
| `users.display_name` | every rendering; `members.jsonl` (tenant archive); CSV `performed_by`; `changed_by_name` | live resolution (no stored copy) except archive/CSV files | archives expire (R-05 72 h); CSV is the recipient's |
| `task.completion_notes`, `TaskCompletionDetails.{reason, material}` | `care_events.{reason, material}`; `care_confirmations.notes` | content copy | both in review sets |
| attachment bytes | renditions, shared records (dedup) | bytes | Art. 19 notice (not implemented) |
| `tenants.slug` (may derive from a name) | `kp_active_tenant_slug`, URLs, logs (`ten_` pseudonym) | — | slug rename not in scope |

---

## 6. Gaps found by the inventory (fact list; resolution in `04`–`09`, `12`)

1. Tombstones reachable in `care_events.performed_by_user_key` via `account_of` (#2770).
2. Free text never cleared or listed at erasure; redaction only for care events, lead-only,
   no UI action beyond a chip; no affected-rows list.
3. `care_events.material`, measurement strings outside the redaction set.
4. `original_filename` and `caption` survive erasure; `nutrient_plans.author` and the
   `performed_by` free-text fields of watering/tank logs are outside every rule.
5. `garden_plan_audit` keeps free-text copies and a tombstone; UI drops `null` actors.
6. No retention for `notifications`, `watering_events`/`feeding_events`/tank logs, tasks and
   comments, `care_confirmations`.
7. Membership end has no privacy effect; no `left_at`; name resolves forever.
8. Closed accounts still resolve their display name for up to 90 days.
9. Every member sees every member's e-mail.
10. MCP diary tool returns raw `users._key`; MCP inspections write `inspector = "mcp:<key>"`.
11. Statutory rules apply to every tenant; `CanG §X` unspecified.
12. Several `localStorage`/`sessionStorage` keys with a `user_key` or an e-mail survive
    logout; REQ-025 §10 lists stale/non-existent keys and misses existing ones.
13. No backups → no erasure-after-restore procedure; when backups come, nothing re-applies
    erasures.
14. No privacy-operation metrics or list endpoint; "gauge" is a log field.
15. Marker/regex constants duplicated.
16. `security_audit_log` has no action for erasure/export/consent/redaction.
