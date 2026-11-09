# SPEC-11 — DPIA Pre-Screening (Art. 35 GDPR)

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Status: technical pre-screening prepared by the engineering side. It is NOT a DPIA and NOT
a legal assessment. It gives the DPO / counsel the facts and the risk inventory needed to
decide whether a full DPIA is required and to write one.
```

---

## 1. Baseline facts (verified)

- No DPIA exists in the repository. NFR-001 §6.7 requires one **for sensor data** before
  sensor capture goes live; ADR-003 (sensor retention) calls the DPIA question open; the
  end-user doc `docs/de/user-guide/privacy.md` states that a DPIA "wurde durchgeführt" —
  a contradiction to be corrected (`06` §9).
- No record of processing activities (Art. 30) exists; REQ-025 §8 and NFR-011 §8 put it
  outside the software.
- REQ-056 O-03 (tenant archive), REQ-053 SR-020 ("berechtigtes Interesse oder DSFA") and
  GP-FR-146 (GeoJSON, "eigene DSFA") and the REQ-055 review (S-018 posting-time patterns)
  each point at a DPIA that does not exist.
- Controller roles (LEG-01) are undecided; the screening below is written from the
  perspective of the **platform operator as processor and the tenant as controller for member
  data**, noting where the operator is controller itself.

---

## 2. Processing operations in scope

| # | Operation | Data subjects | Data | Where |
|---|-----------|---------------|------|-------|
| O1 | Historical activity tracking (care log, confirmations, harvests, treatments, plan audit) with performer/creator attribution and timestamps | members (employees, volunteers, association members, household members), third parties named in labels | who did what when where; free text | `care_events`, statutory rows, `garden_plan_audit`, tasks |
| O2 | Lead/management access to member activity (filter by person, CSV export with names, bed history) | members | activity per person | `GET /care-events`, CSV, bed history |
| O3 | Employee monitoring potential in commercial tenants | employees | O1 + O2 | same |
| O4 | Free-text content naming persons (diary, notes, labels, names, captions, audit summaries) | members, third parties, persons on photos | names, descriptions, photos | ~25 fields (`02` §3) |
| O5 | Long retention (5 y care events, 3–5 y statutory, 730 d security audit, pseudonymised rows outliving the account) | former members, erased accounts | pseudonymised attribution, free text | retention beats |
| O6 | Shared devices and offline storage (IndexedDB queue with notes/photos, plan cache, localStorage keys with `user_key`/e-mail) | the device's users | unsent notes/photos, keys | browser |
| O7 | Multi-tenant processing (one installation, many controllers; platform operator with admin access to member lists and security audit; tenant archives leaving the installation) | all users | directory data, GPS of sites | platform tenant, `/admin/platform/*`, REQ-056 export |
| O8 | Derived records and propagation (backfill copies performer from statutory rows; plan audit copies names; templates copy names into beds; import snapshots) | members | attribution and content copies | v0104, consistency job, `place_template`, audit |
| O9 | Sensor data that may reveal presence (CO₂, motion, manual overrides) — the operation NFR-001 §6.7 already flags | household members, employees | time series, overrides | TimescaleDB, `manual_overrides` |
| O10 | Location data (site GPS = home address for personal gardens; rounded to 2 decimals before leaving) | account holders | coordinates | `sites.gps_coordinates`, weather calls, Art. 15 bundle, tenant archive |

Sensitive categories (Art. 9): none by design. Health inferences are possible only
indirectly (a diary entry may mention an illness; a cannabis cultivation association's
membership itself may be considered sensitive context — **[legal]** for the DPO). Children:
not addressed by the specs (no age gate) — **[legal]** note for the DPO.

---

## 3. Risk register

Likelihood / impact on a 3-level scale (low / medium / high) as the engineering side sees
them; the DPO calibrates.

| R | Threat scenario | Subjects | Likelihood | Impact | Existing controls [verified] | Required controls (this package) | Residual |
|---|-----------------|----------|------------|--------|-------------------------------|----------------------------------|----------|
| RISK-01 | **Activity profiling of members**: a lead or any member reconstructs when a person was in the garden from performer timestamps (presence pattern) | members, esp. in community gardens | medium (data is visible to all members) | medium (private life, presence) | filter by other person only for lead/management (SR-020); no statistics endpoint; CSV bounded 50 000 rows | `attribution_visibility = leads_and_self` (PRIV-300); CSV names only for leads + audited (PRIV-307/308); no per-person aggregation guard (PRIV-403); former-member suppression (PRIV-112) | low–medium (leads still see all; justified by coordination) |
| RISK-02 | **Employee performance evaluation** by an employer using filter/export | employees | medium in commercial tenants | high (employment consequences; §26 BDSG / Art. 88; co-determination) | none specific | PRIV-403…407; transparency text for works councils; `leads_and_self` default recommendation for organisation tenants (LEG-05) | medium — the platform cannot prevent off-platform use of an exported CSV; mitigated by audit and restriction |
| RISK-03 | **Erased person still identifiable** through free text ("Maren hat gegossen"), photo captions, file names, template/bed names, audit summaries, legacy typed names | erased accounts | high (today certain for any row naming the person) | medium–high (Art. 17 not fulfilled; reputational for the operator) | marker on account fields; lead-only manual redaction of care events without a list | review queue with name-token flagging (PRIV-221), generic redaction (PRIV-228), `original_filename` cleared (PRIV-211), legacy unkeyed names listed (PRIV-233), SLA metric (PRIV-226) | low–medium — depends on leads acting; LEG-08 on sufficiency |
| RISK-04 | **Pseudonym leaks into non-statutory stores** (tombstone copied into the care log, linkable for 5 y, filterable) | erased accounts | medium (happened: #2770) | medium | none | PRIV-204…207, migration v0107, consistency beat | low |
| RISK-05 | **Former member remains named indefinitely** in a tenant they left (and cannot export those rows under Art. 15 because the manifest reads current tenants only) | former members | high (certain today) | medium | security audit of the departure | PRIV-112 suppression, PRIV-115 information, PRIV-116 attribution removal (P2); LEG-06(b) on Art. 15 | low–medium |
| RISK-06 | **Statutory retention applied without a legal duty** (hobby tenant's harvest/treatment rows kept pseudonymised 3–5 y after erasure; the person's export finds them) | erased accounts in hobby tenants | high (certain today) | medium | tombstone (pseudonymised, not named) | `record_keeping` profile (PRIV-122/401), reclassification job | low; LEG-03 decides |
| RISK-07 | **Statutory record weakened** (applicator name cleared at erasure although §11(2) PflSchG may require it) | the tenant (compliance), inspectors | medium | medium (regulatory for the tenant) | tombstone linkability | LEG-04 decision; sealed-name alternative | open |
| RISK-08 | **Closed account still displayed** for up to 90 days | persons who asked for erasure | high (certain) | low–medium (the person expects to vanish) | `is_active=false` | PRIV-104 | low |
| RISK-09 | **Shared device exposes unsent notes/photos and the previous user's identity**; account deleted elsewhere leaves data for up to 365 d; `localStorage` keeps `user_key`/e-mail; logout wipe not awaited | users of shared tablets/phones (community gardens, employees) | high (shared devices are the norm in gardens) | medium (notes, photos, identity) | namespace per user+tenant; explicit-logout dialog; TTL 15 min for the cache; docs hint | PRIV-511…526 (shorter defaults, quarantine, `account.closed`, awaited wipe, key hygiene, shared-device mode, device page) | low–medium; LEG-09/10 |
| RISK-10 | **Backup restore re-creates erased persons** (no replay procedure; dump retention undefined) | erased accounts | low today (no backups run) → high once enabled | high (full re-identification) | none | ledger + mirror + restore replay (PRIV-707…713) before enabling backups | low after implementation; LEG-11 |
| RISK-11 | **Platform operator over-reach**: admin routes return member e-mails and security audit across tenants; a REQ-023 line even names "Backup-System → Cross-Tenant Read-Access" | all users | low (routes gated; principle P4 holds in code) | high | `require_platform_admin`; no domain data routes | PRIV-311 (no new reads); operations endpoint counts only; reconcile REQ-023 §5b.1 with REQ-049 P4 (`06` §9) | low |
| RISK-12 | **Member directory exposure**: every member sees every member's e-mail | members | high (certain) | low–medium (spam, unsolicited contact; employees' addresses) | — | PRIV-305 (e-mail only for `management`); LEG-14 | low |
| RISK-13 | **Purpose creep through derivation**: statutory performer copied into the care log; names copied into beds/audit; template exchange files (GP-API-070) carry template names | members | medium | low–medium | GP-NFR-051 (plan exports without `*_by`); template export "ohne Personenbezüge" by spec | lineage registry (PRIV-031/606), `carry_account_reference`, review suggestions; LEG-07 | low |
| RISK-14 | **Presence inference from sensors and overrides** (NFR-001 §6.7) | household members | medium | medium–high (private life) | sensor retention tiers; `OUTDOOR_OPEN` classed non-personal; DP-002 rounding | out of this package's scope except `manual_overrides.created_by/reason` (marker, review); the DPO's sensor DPIA remains due | open (pre-existing) |
| RISK-15 | **Location data leaves the installation** (tenant archive with GPS; Art. 15 bundle with GPS; weather calls rounded) | account holders | low–medium | medium (home address) | rounding DP-002; archive 72 h; step-up | LEG-13; no change proposed here | medium (pre-existing) |
| RISK-16 | **Incomplete privacy operations go unnoticed** (`partially_completed` erasures visible only in logs; differing escalation thresholds) | erased accounts | medium | medium | retry/backoff; error logs at attempt 1 and 5 | metrics + operations endpoint + stale alert (PRIV-110, PRIV-607) | low |
| RISK-17 | **Third parties named without information** (`performed_by_label`, photos of persons) | non-users | medium | low–medium | UI hint "keine vollständigen Namen" (SR-006); label ≤ 80 | review field; Art. 14 text for tenants (PRIV-408); LEG-12 | low–medium |
| RISK-18 | **Cannabis context**: membership in a cultivation association and harvest records may be sensitive by context | association members | low–medium | high (stigma, legal) | statutory retention; tenant isolation | `record_keeping = kcang_association` makes the class explicit; DPO to assess Art. 9 analogy | open |

---

## 4. Is a full DPIA likely required?

Criteria (WP 248 rev.01, DSK "Muss-Liste"): a DPIA is required when two or more of the nine
criteria apply, or when the processing is on a supervisory authority's list.

| Criterion | Applies? | Why |
|-----------|----------|-----|
| Evaluation or scoring (incl. profiling of work performance) | **yes, potentially** (O2/O3 in commercial tenants) | per-person activity filter and export make performance evaluation possible |
| Systematic monitoring | partly (O1 continuous logging of activity; O9 sensors with presence inference) | |
| Sensitive data or data of highly personal nature | partly (O9 presence patterns; O18 cannabis context; O10 home address) | |
| Large scale | **no** today (single installation, small tenants); changes with commercial SaaS | |
| Matching/combining datasets | partly (O8 derived records across collections; multi-tenant) | |
| Vulnerable data subjects | **yes** (employees in commercial tenants — WP 248 names employees explicitly) | |
| Innovative use / new technology | no (AI features are consent-gated and out of this scope) | |
| Prevents exercising a right or using a service | no | |
| DSK Muss-Liste: "Verarbeitung von Beschäftigtendaten zur Verhaltens-/Leistungskontrolle"? | **to check by the DPO** — the care log is not built for it but is suited to it (the §87(1) No. 6 BetrVG test) | |

**Engineering assessment**: for a **self-hosted hobby or household installation**, a full
DPIA is probably **not** required (one criterion at most; small scale). For **commercial SaaS
operation with organisation tenants that employ staff**, at least two criteria plausibly
apply (employee data + evaluation potential; plus systematic monitoring/presence inference
once sensors are used) — a full DPIA is **likely required** before that operating model
starts, and the sensor DPIA that NFR-001 §6.7 already demands should be folded into it.
This statement is not a legal conclusion (LEG-12).

---

## 5. Inputs the DPIA will need from this package

| DPIA section | Source |
|--------------|--------|
| Systematic description of the processing | `01` §3/§6, `02` §3 |
| Necessity and proportionality | `06` §4 LIA-1…3, `05` §3 matrix |
| Legal bases and retention | `06` §2 |
| Risks and measures | §3 above; `03`, `04`, `07` controls |
| Data subject rights handling | `03` §2, REQ-025 (existing) |
| Processors / recipients | REQ-025 §9 (Sentry, weather, OAuth), REQ-056 archive, LEG-01 |
| Residual risk and consultation (Art. 36) | DPO |

---

## 6. Open legal items for the DPO (cross-reference)

LEG-01 controller roles · LEG-02 LIA attribution · LEG-03 statutory applicability · LEG-04
applicator name legibility · LEG-05 employee data basis, BetrVG · LEG-06 former-member
period and Art. 15 scope · LEG-07 backfill purpose compatibility · LEG-08 free-text review
model and SLA · LEG-09 TDDDG classification and offline opt-in · LEG-10 device retention and
dead-session grace · LEG-11 backups and replay ledger · LEG-12 DPIA threshold, RoPA, Art.
13/14 texts · LEG-13 tenant archive · LEG-14 member e-mail visibility · LEG-15 tombstone
linkability · LEG-16 Sentry legitimate interest (pre-existing) · LEG-17 KCanG paragraph.
Details and defaults: `decision-log.md`.
