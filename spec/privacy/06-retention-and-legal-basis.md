# SPEC-06 — Retention and Legal Basis Matrix

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-400 … PRIV-449
Depends on: NFR-011 (retention rules R-nn), REQ-025 §3, 02 (inventory), 03/04 (behaviour)
```

Every legal basis below is a **proposal** unless marked [verified in spec] (meaning NFR-011
or REQ-025 already states it). Everything flagged **LEG-nn** needs legal counsel / DPO
approval before it is treated as decided. Art. 17(3) is used only as an **exception to
erasure**, never as a basis for processing.

---

## 1. Controller roles — the question that comes first

**LEG-01** Who is controller for the member data of a community garden or a commercial
operation using Kamerplanter?

| Option | Consequence for this package |
|--------|------------------------------|
| (a) The **tenant organisation** is controller, the platform operator is **processor** (Art. 28) | Art. 13/14 information, the balancing tests of §4, the DPIA and the RoPA entries are the tenant's; the operator provides the technical means (visibility setting, review queue, export) and a DPA; the operator's own controllership covers accounts, platform tenant, security audit, logs |
| (b) The operator and the tenant are **joint controllers** (Art. 26) | an arrangement is needed; the operator carries the balancing tests |
| (c) The operator is sole controller | every rule below is the operator's; the tenant's leads act on the operator's behalf |

The package is written for **(a)** (the common SaaS reading) and marks every place where the
choice matters with "(controller: tenant)". The specs today never address the question
(REQ-025 §8 puts the RoPA "outside the software"; `data_controller` in the export bundle is
a configured string). For a **self-hosted** installation (a) collapses: the operator *is* the
tenant.

---

## 2. Retention matrix — personal data categories

Columns: Purpose · Legal basis · Retention trigger · Period · Deletion behaviour · Legal
retention exception · Responsible role (controller (a) reading). "Setting" names the
environment variable / `RETENTION_CEILINGS` entry [verified in code unless noted].

### 2.1 Account and session data (controller: operator)

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| R-01 | soft-deleted account | serve Art. 17 with a safety window against mistaken requests | Art. 6(1)(c)+(b) | erasure request | 90 d (`RETENTION_SOFT_DELETE_RETENTION_DAYS`, ceiling 90) | hard delete plan | — | operator | implemented [v] |
| R-02 | unverified accounts | hygiene | 6(1)(f) | registration | 7 d | delete (dry-run until `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED`) | — | operator | implemented [v] |
| R-03 | IP in refresh tokens | session security | 6(1)(f) [v spec] | token issue | 7 d | anonymise (IPv4 /24, IPv6 /48) | — | operator | implemented [v] |
| R-08…R-11 | token hashes, OAuth state, refresh tokens | auth | 6(1)(b) | issue | 1 h / 24 h / 5 min / own expiry | delete | — | operator | implemented |
| — | `last_login_at`, `failed_login_attempts`, `locked_until` | account security | 6(1)(f) | each login | life of account | with account | — | operator | implemented; **no period for `last_login_at`** → propose overwrite-only (it is) |
| R-04 / R-04a | consent records + IP | prove consent (Art. 7(1)) | 6(1)(c) [v spec] | revocation | 3 y after revocation / IP 7 d | delete; tombstone at erasure | — | operator | implemented [v] |
| R-06 | `erasure_requests` | prove erasure (Art. 5(2)) | 6(1)(c) | completion | 3 y (`retention_erasure_audit_retention_years`; docstring says "one year" — **fix docstring**) | delete only if tombstoned | — | operator | implemented [v] |
| R-38 | `security_audit_log` | Art. 32 proof of access changes | 6(1)(c)/(f) [v spec] | `created_at` | 730 d fixed | delete; tombstone at erasure; kept at tenant erasure | — | operator | implemented [v] |
| **new R-44** | privacy-operation audit actions in `security_audit_log` (`04` §4.2) | Art. 5(2) | 6(1)(c) | `created_at` | 730 d (same row type) | same | — | operator | **proposal** |
| **new R-45** | `erasure_replay_ledger` (raw `user_key` + erasure key, for backup restores, `09` §6) | enforce Art. 17 after a restore | 6(1)(c) (Art. 17 is the obligation) | erasure completion | `BACKUP_RETENTION_DAYS + 5` (default 35) | hard delete | — | operator | **proposal, LEG-11** |

### 2.2 Membership and tenant data

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| — | `memberships` (role, scopes, `joined_at`) | run the tenant | 6(1)(b) (membership/employment relationship) | membership end | immediate (row deleted) | delete | security audit keeps old role 730 d | tenant | implemented [v] |
| **new** | former-member **name rendering** (derived, no row) | hand-over, accountability | 6(1)(f) — balancing §4.3 | membership end | `RETENTION_FORMER_MEMBER_NAME_DAYS` 90 (0–365) | rendering switches to `former_member` | — | tenant | **proposal, LEG-06** |
| R-12 | invitations (`email`) | onboarding | 6(1)(b) | expiry | 30 d | delete | — | tenant | implemented |
| R-01b | tenant in `pending_deletion` | mistake window, Art. 20 export window | 6(1)(b) | request | 90 d (0–90) | tenant inventory | statutory rows pseudonymised | tenant (lead ∧ management) | implemented [v] |
| R-06a | `tenant_erasure_records` | proof | 6(1)(c) | completion | until last statutory row, ≤ 5 y | delete | — | operator | implemented |
| — | member **e-mail in `/members`** | contact | 6(1)(b)? necessity doubtful | — | — | — | — | tenant | **LEG-14**: restrict to `management` (PRIV-305) |

### 2.3 Domain history with attribution (controller: tenant)

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| R-25 | `care_events` (performer, creator, free text, photos) | bed history, crop rotation, coordination ("who last watered") | content: 6(1)(f) crop-rotation history [v spec says "Art. 17(3) (berechtigtes Interesse: Anbauhistorie)" — reword: basis is 6(1)(f), 17(3) is not a basis]; **attribution**: 6(1)(f) balancing §4.1 | `performed_at` | 5 y (floor = ceiling 5, `RETENTION_CARE_EVENT_RETENTION_YEARS`) | after 5 y: account refs → marker, free text → `[redacted]`, photos deleted; `pest_control`/`ipm` wait for `max(R-25, R-17)` | 17(3)(b) only for `pest_control`/`ipm` **and only if LEG-03 applies**; otherwise none | tenant | implemented [v]; **proposal**: attribution suppression for former members, review queue at erasure |
| — | `watering_events`, `feeding_events`, `watering_logs`, `tank_fill_events`, `maintenance_logs` (free-text `performed_by`, `notes`) | operations | 6(1)(b)/(f) | — | **none** [v: deleted only with the tenant] | — | — | tenant | **gap**: propose R-46 = align with R-25 (5 y, then `performed_by`/`notes` redacted); migrate `performed_by` to a keyed field (`08` §3.4) |
| — | `plant_diary_entries` (author, text, photos, AI analysis) | plant record | 6(1)(b) (the user's own documentation) / 6(1)(f) for the tenant | — | none (life of plant/tenant) | marker at erasure, text kept + review | — | tenant | implemented [v]; review **proposal** |
| — | `task_comments`, `tasks` (assignee, names, notes) | coordination | 6(1)(b) | task closed | none | marker; review | — | tenant | gap: propose R-47 closed tasks/comments 2 y → redact free text (**LEG-08** scope) |
| — | `garden_objects`, `bed_templates`, `locations` (labels, names, notes, `created_by`) | plan | 6(1)(b) | — | life of plan | marker at erasure; names reviewed | — | tenant | implemented [v]; review **proposal** |
| R-26 | `garden_plan_audit` (actor, summary, snapshot) | plan change log, snapshot restore | 6(1)(f) | `at` | 365 d | hard delete; actor → **marker** (DEC-16; today tombstone) | — | tenant | implemented [v]; DEC-16 **spec change** |
| — | attachments (`created_by`, `caption`, `original_filename`) | photos | 6(1)(b) | — | life of parent | marker; `original_filename` cleared (PRIV-211); caption reviewed | shared bytes stay (Art. 19 notice, AK-OS-09 **not implemented** [v]) | tenant | partly |
| — | `notifications` (recipient, title, body, data) | delivery | 6(1)(b) | read / created | **none** [v: no R-row, no beat] | deleted only at erasure | — | operator | **gap**: propose R-48 = 90 d after `read_at`, 180 d unread, hard delete |
| R-41 / R-42 | device read cache / write buffer | offline function | 6(1)(b) [v spec, "Vorschlag"] | TTL / capture | 15 min / 365 d pending, 90 d unsendable | wiped on device | known gap (other device) | user (own device) / operator for defaults | implemented [v]; **proposal** shorter defaults (`07`), **LEG-09/10** |

### 2.4 Statutory records (controller: tenant; applicability per tenant — LEG-03)

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| R-16 | `harvest_batches`, `quality_assessments`, `yield_metrics` | cultivation-association documentation (KCanG — **paragraph not cited anywhere**, REQ-025 L219 "CanG §X", **LEG-17**) | 6(1)(c) **only for a Anbauvereinigung**; otherwise 6(1)(b)/(f) ordinary record | `harvest_date` | ≥ 5 y (floor 5, no ceiling) | key → tombstone, `harvester`/`assessed_by` cleared at erasure; deleted when tenant gone and period over | **17(3)(b)** for the row; the *name* — LEG-04 | tenant | implemented [v]; **proposal** `record_keeping` profile |
| R-17 | `treatment_applications` (+ edges) | PflSchG §11 record for **professional users** (Art. 67 Reg. (EC) 1107/2009: product, time, dose, area, crop; §11(2) PflSchG adds the applicator) | 6(1)(c) for professional users; otherwise none | `applied_at` | ≥ 3 y | as R-16 | 17(3)(b); **LEG-04** name legibility | tenant | implemented [v] |
| R-18 | `inspections` | PflSchG §11 monitoring record | as R-17 | `inspected_at` | ≥ 3 y | as R-16 | 17(3)(b) | tenant | implemented [v] |
| — | `care_events` with `category ∈ {pest_control, ipm}` | mirror of the above in the care log | **not** a statutory record (REQ-053 §13.2, E-16) | — | `max(R-25, R-17)` | marker at erasure; deleted with the tenant | the spec's "PflSchG-Vorbehalt" is a *retention floor*, not a legal record — **LEG-07** confirm | tenant | implemented [v] |

### 2.5 Pseudonymised and audit rows (controller: operator / tenant)

| # | Category | Basis | Period | Note |
|---|----------|-------|--------|------|
| — | `mcp_audit_log` (`service_account_key`, shortened IP) | 6(1)(f) Art. 32 | 90 d (`settings`) | tombstone at erasure |
| — | `ai_audit_log` | 6(1)(f) | per setting | marker at erasure |
| — | structured logs (`sub_…`, `ten_…` pseudonyms) | 6(1)(f) | 30 d pipeline (NFR-011 Q-R3) | no raw keys (guards) |
| **new R-43** | `privacy_review_items` + decisions | 6(1)(c) Art. 5(2) proof of erasure follow-up | 3 y after decision; with the tenant | **proposal** |

---

## 3. Statutory record-keeping — applicability per tenant (LEG-03)

**PRIV-400** The system MUST NOT assume that every tenant is bound by PflSchG §11 or the
KCanG documentation duties. [verified] Today `LEGAL_RETENTION_RULES` apply to every tenant,
every `treatment_applications` row of a hobby garden becomes a pseudonymised 3-year record
after the author asks for erasure, and the Art. 15 export of a still-active person finds it
through the tombstone.

**PRIV-401** [DEC-11] `Tenant.settings.record_keeping` (`03` PRIV-122) decides the class of
the four collections: `legacy`/`pflschg_professional`/`kcang_association`/`both` → statutory
(as today); `none` → `shared_history`. Defaults: existing tenants `legacy`; new
`organization` tenants ask at creation (required choice with explanation); new `personal`
tenants `none`. **[legal LEG-03]**: (i) is the PflSchG §11 duty limited to "berufliche
Anwender" (the package assumes yes); (ii) which KCanG provision carries the 5-year harvest
documentation duty and for whom (the package assumes: Anbauvereinigungen only); (iii) may the
operator rely on the tenant's self-declaration.

**PRIV-402** When `record_keeping` changes from statutory to `none`, existing pseudonymised
rows MUST be re-classified by a tenant-scoped, idempotent job (`09` §4): tombstones → marker
(the person is gone; the linkable pseudonym has no basis any more), typed names already
cleared, `notes` → review items. The change is audited (`TENANT_RECORD_KEEPING_CHANGED`).
The reverse change is allowed for new rows only (a marker cannot become a pseudonym).

---

## 4. Legitimate-interest assessments (Art. 6(1)(f)) — three-step tests

Each test records: (1) legitimate purpose, (2) necessity, (3) balancing with the subjects'
interests and rights, plus the safeguards the package provides. All are **proposals for the
controller's LIA**; counsel reviews them (LEG-02, LEG-06, LEG-07).

### 4.1 LIA-1 — Performer/creator attribution in shared tenants (current members)

1. **Purpose**: coordination of shared work (who watered, who last treated bed 3), quality
   of the record (correction by the author), accountability inside a community garden or a
   business, agronomic history (crop rotation needs *what* and *when*, not *who*).
2. **Necessity**: the *coordination* purpose needs the name while the person is a member and
   the activity is recent; the *history* purpose does not need the name at all; the
   *accountability* purpose needs the name for a bounded time.
3. **Balancing**: members reasonably expect co-members to see who did what (a garden
   notice board does the same); the risk is profiling (activity patterns, presence times —
   REQ-051 §11 and the REQ-055 review note posting-time patterns) and, in businesses,
   performance evaluation. Safeguards: no per-person statistics (PRIV: matrix row S), filter
   by another person only for leads/management (SR-020), tenant setting `leads_and_self`
   (PRIV-300), name suppression after membership end (PRIV-112), attribution removal on
   request (PRIV-116), no attribution in exports for non-leads (PRIV-307), transparency text
   in the leave dialog and the privacy policy (PRIV-115).
   **Result (proposed)**: interest prevails for current members under the safeguards;
   **does not** prevail for the five-year retention of the *name* — hence suppression and the
   R-25 end-of-period marker. **LEG-02**.

### 4.2 LIA-2 — Copying the performer from statutory rows into the care log (v0104, consistency job)

1. **Purpose**: a complete bed history that includes harvests and treatments entered before
   the care log existed.
2. **Necessity**: the history needs the *event*; the *performer* is the same operational fact
   the member entered (it was a `performed_by` on the source, stamped from the caller) — no
   new information is created, but it moves into a store with a 5-year retention, a
   per-person filter and a CSV export.
3. **Compatibility (Art. 6(4))**: same controller, same context (the tenant), the person
   entered it as "I did this", reasonable expectation that the garden's log shows it; no
   sensitive data; safeguards of LIA-1 apply. Pseudonyms/tombstones MUST never be copied
   (PRIV-205). **Result (proposed)**: compatible further processing; **LEG-07** confirms,
   and the privacy notice / RoPA entry must name the care log as a purpose.

### 4.3 LIA-3 — Former members' names for N days

1. **Purpose**: hand-over ("who looked after this bed until last week?").
2. **Necessity**: short; after the season's hand-over the name adds nothing to the history.
3. **Balancing**: the person left; their expectation of being named decreases over time;
   safeguards: N ≤ 365 with default 90, no filter/export by them (PRIV-114), transparency
   (PRIV-115), the security audit keeps the fact for the platform admin only.
   **LEG-06**: N and whether leads may keep the name longer (the package says no).

### 4.4 LIA-4 — Sentry error tracking

[verified in spec] REQ-025 §9: event 6(1)(f) "rechtlich zu bestätigen", user block only with
consent. Not changed; referenced as LEG-16.

---

## 5. Employee and volunteer data (LEG-05)

**Assessment**
- A commercial tenant whose growers are employees processes employee data when it stores
  `performed_by`/confirmation identities with timestamps and lets leads filter by person.
  Art. 88 GDPR opens national law; §26(1) BDSG allows processing *necessary* for the
  employment relationship (note: the CJEU, C-34/21 of 30 March 2023, held the parallel Hessian
  provision incompatible with Art. 88 insofar as it merely repeats Art. 6(1)(b) — the
  continued reliance on §26 BDSG is legally uncertain; counsel must assess). A record of
  who performed which task is ordinarily *necessary* for running the work (task
  coordination, PflSchG record for professional users); using it for **performance
  evaluation** is a different purpose. §87(1) No. 6 BetrVG: a system *objectively suited* to
  monitor behaviour or performance is subject to co-determination where a works council
  exists — the per-person filter and a CSV export per person make the care log suited. That
  duty falls on the **employer (tenant)**, not the platform; the platform must make the
  function describable and switchable.
- **Volunteers and association members** are not "Beschäftigte" (§26(8) BDSG); §26 BDSG and
  BetrVG do not apply. The basis is 6(1)(b) (membership relationship, statutes) and 6(1)(f)
  (LIA-1). The package does **not** apply employment law to them.
- The **five-year confirmation retention** is not what it seems: `care_confirmations` have no
  actor and no retention row [verified]; the 5 years are R-25 on the derived care event. The
  LIA-1 result (no name after the period / after membership end) applies.

**Technical restrictions required (PRIV-403 … PRIV-407)**

- **PRIV-403** No endpoint, export or UI MUST aggregate activity per person (counts, time
  series, rankings). A future "statistics" feature MUST carry its own LIA and, for employee
  tenants, a works-council note.
- **PRIV-404** `attribution_visibility = leads_and_self` MUST be available (PRIV-300) and
  recommended by default for organisation tenants created after the change (operator decision).
- **PRIV-405** The per-person filter and the names export MUST be logged (PRIV-308) so the
  employer can show the works council how the function is used; the log is readable by the
  tenant's `management` (counts per actor, 90 days) — **proposal**, counts only.
- **PRIV-406** The privacy documentation (docs `privacy.md`, DE/EN) MUST contain a section
  "Für Betriebe und Vereine" that explains: what is stored about who did what, who sees it,
  for how long, the setting, and that a Betriebsvereinbarung may be required — a template
  text the tenant can hand to its works council (product deliverable, `12`).
- **PRIV-407** Nothing in the task-completion or confirmation path MUST record *duration* or
  *speed* of work beyond `performed_at` (no start/stop timestamps).

---

## 6. Purpose limitation checks (Art. 5(1)(b))

| Flow | Original purpose | Secondary use | Verdict |
|------|------------------|---------------|---------|
| `treatment_applications.applied_by_key` → `care_events.performed_by_user_key` | PflSchG record | bed history, filter, CSV | compatible under LIA-2 (LEG-07); tombstones never |
| `harvest_batches.harvested_by_key` ← task completion engine (`harvested_by_key = event.performed_by_user_key`) | care log | statutory record | the same fact, same moment; fine — but the *record's* content requirements (LEG-04) must be met from the completion (today no `treatment_applications` row is written by a completion [verified], so the §11 record is **not** produced by the task path — REQ-053 §13.2 confirms the IPM endpoint is the proof) |
| `bed_templates.name` → `Location.name` → `garden_plan_audit.summary` → SVG/PDF/JSON | plan | export/print | content, not attribution; lineage registered (PRIV-230) |
| `users.display_name` → every API rendering | identification | activity display | LIA-1 safeguards |
| `security_audit_log` | Art. 32 | — | no secondary use allowed (REQ-049 "no surveillance") |
| device cache (`kp-plan-cache`) | offline reading | — | minimised ([verified] no names, notes, assignments) |

---

## 7. Information duties (Art. 13/14) — inputs the package produces

**PRIV-408** The privacy policy text (operator, `GET /privacy/policy`) and the tenant-facing
docs MUST state: the care log and its attribution; former-member suppression; the review
queue (a lead may see rows the person wrote); the offline storage on the device (REQ-025 §10
rows); third-party names in `performed_by_label` (Art. 14 — the tenant informs the third
party; the UI hint "keine vollständigen Namen" [verified SR-006] stays); photos showing
persons (REQ-053 §32.5 Pkt. 12 open). **LEG-12** covers the wording.

---

## 8. Periods requiring legal approval (summary flags)

| Period / basis | Where | Flag |
|----------------|-------|------|
| 5 y care-event retention as 6(1)(f) (crop rotation) | R-25 | LEG-02 |
| 90 d former-member name | PRIV-112 | LEG-06 |
| statutory applicability per tenant; KCanG paragraph; PflSchG name legibility | §3 | LEG-03, LEG-04, LEG-17 |
| purpose compatibility of the backfill | LIA-2 | LEG-07 |
| free-text review model and 30-day SLA | `04` §5 | LEG-08 |
| TDDDG classification of IndexedDB/Cache Storage | `07` §2 | LEG-09 |
| offline buffer 90/30 d, dead-session 14 d | `07` §6–7 | LEG-10 |
| backups 30 d + replay ledger 35 d | `09` §6 | LEG-11 |
| DPIA threshold, RoPA, Art. 13/14 texts | `11` | LEG-12 |
| tenant archive leaving the installation | REQ-056 §8 | LEG-13 |
| member e-mail visibility | PRIV-305 | LEG-14 |
| deterministic tombstones | `04` §2.3 | LEG-15 |
| notifications 90/180 d; watering/feeding logs 5 y; closed tasks 2 y | §2.3 new rows | LEG-08 (scope), DSB per NFR-011 v1.29 ("Vorschlag, DSB-Prüfung offen") |

---

## 9. Required spec changes (proposals, not applied)

| Spec | Change |
|------|--------|
| NFR-011 | new rows R-43 (review items), R-44 (privacy actions in security audit), R-45 (replay ledger), R-46 (watering/feeding/tank logs), R-47 (closed tasks/comments), R-48 (notifications); R-26 actor → marker; R-25 basis wording "6(1)(f); Art. 17(3) is the erasure exception"; `care_events.material` in R-25's redaction set; §3.1 beat table rows for the new tasks |
| REQ-025 | §3.1.3: attribution roles and the review queue as phase 2.6; §10 rows for `kp_local_data_owner`, `kp-garden-field-mode`, `kp.emailChange.address`, `kp.stepUp.*`, `kamerplanter:consent:v1` (today missing [verified]); fix the stale rows `i18next`/`theme`/`redux_state` (keys are `kamerplanter-lang`, `kamerplanter-theme`; no `redux_state`); footer version 1.5 → current |
| REQ-053 | GP-FR-109 field set + `material`; GP-NFR-055 `garden_plan_audit` marker; the contradiction "DSGVO-Kaskade kann Freitexte ersetzen" (GP-FR-109) vs "kein Freitextfeld wird bei der Kaskade geleert" (E-16) resolved in favour of E-16 + review queue |
| REQ-024 / REQ-049 | `attribution_visibility`, `record_keeping` settings; e-mail only for `management`; `management` may redact |
| REQ-022 | state that confirmations have no actor and no own retention; the derived care event carries both |
| REQ-023 §5b.1 | remove "Backup-System → Cross-Tenant Read-Access" or reconcile with REQ-049 P4 |
| docs `privacy.md` | remove "eine DSFA wurde durchgeführt" until one exists (ADR-003 says open) |
