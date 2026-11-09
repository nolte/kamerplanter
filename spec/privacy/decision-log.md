# Decision Log — Privacy Architecture

```
Package: spec/privacy · Version 1.0 · 2026-11-09
Two series: DEC-nn = architectural/product decisions this package recommends (operator
decides); LEG-nn = questions that need qualified legal counsel / the DPO. Every row names the
default the specification ships with, so engineering is not blocked; a different answer
changes the default through the setting or rule named in "Where it lands".
Status values: proposed · accepted · rejected · superseded · open (LEG) · decided (LEG)
```

---

## A. Architectural and product decisions (DEC)

| ID | Context | Options considered | Recommendation | Rationale | Legal review | Where it lands | Status |
|----|---------|--------------------|----------------|-----------|--------------|----------------|--------|
| DEC-01 | Where the package lives | `docs/specs/privacy/` (task suggestion) · `spec/privacy/` | **`spec/privacy/`** | `spec/` is the repository's specification convention; it is outside the MkDocs `docs_dir` (no strict-build risk) and excluded from Vale (`.vale.ini [spec/**]`), so English prose there is not linted as docs prose; `docs/` is the DE/EN end-user mirror and would need both languages | no | this directory | accepted (by this package) |
| DEC-02 | Registry vs new list | separate registry module · attributes on the existing inventory models | **attributes on `AnonymizationRule`/`PseudonymizationRule`/`ErasureStep`/`ErasureExclusion`** | REQ-025 §3.1 learned from three drift incidents (#1663, #1700, #1716) that two lists never match; the guard extends naturally (R7, R8) | no | `08` §2 | proposed |
| DEC-03 | Identity representation | keep raw `users._key` in rows · introduce a `UserRef` embedded type everywhere | **keep raw keys; add one resolver (`PersonRef`) for rendering** | a type migration across ~30 fields and 54 collections has no privacy benefit by itself; the risk is in rendering and copying, which the resolver and `carry_account_reference` address | no | `01` §4.3, `08` §2.3 | proposed |
| DEC-04 | Tombstone derivation | keep `sha256(user_key+salt)[:16]` · move to HMAC with domain separation · per-row random tokens | **keep for existing data; HMAC for any new derivation; allowlist where tombstones may exist** | determinism is relied upon by the Art. 15 lookup and R-06 purge; a change needs a re-keying migration; the leak class (#2770) is solved by confinement, not by a stronger hash | LEG-15 (linkability) | `04` §2 | proposed |
| DEC-05 | Membership end | add `left_at`/history collection · derive the former-member state at read time | **derive at read time from "key present, no active membership" + security-audit departure instant** | no new store of personal data, no new retention; the security audit already records departures (730 d) | LEG-06 | `03` §1.2, §3 | proposed |
| DEC-06 | Free text of erased members | delete automatically · keep untouched (today) · keep + human review with system-found candidates | **keep + review queue + generic redaction** | REQ-025 rule 4 forbids keying on free text; untouched text fails Art. 17 in practice (#2517); candidates found by authorship and name tokens, decisions recorded | LEG-08 | `04` §5–6 | proposed |
| DEC-07 | `material` and measurement strings | leave outside the redaction set (today) · add | **add to `FREE_TEXT_FIELDS`** (spec change REQ-053 GP-FR-109, NFR-011 R-25) | free text, CSV-exported, otherwise never redacted | no | `04` PRIV-213 | proposed |
| DEC-08 | Backfill attribution | copy nothing · copy only live keys of the same role, tombstone → marker · copy everything (today) | **copy same-role live keys; tombstone/marker → marker; `created_by = null`** | same operational fact; purpose compatible (LIA-2) if confirmed; pseudonyms must never be re-minted | LEG-07 | `04` §3.3, E01 | proposed |
| DEC-09 | Confirmation actor | store `null` for queue/MCP (today) · store the principal everywhere | **principal everywhere; service account rendered as such** | one rule; visibility is decided separately (DEC-10) | LEG-05 (visibility, not storage) | `03` §4, E01 | proposed |
| DEC-10 | Performer visibility | all members (today, REQ-049 P2) · leads and self only · tenant setting | **tenant setting `attribution_visibility`, default `all_members`; recommended `leads_and_self` for new organisation tenants** | community gardens want transparency; employers need the restriction; no silent change for existing tenants | LEG-02, LEG-05 | `05` §4, E08 | proposed |
| DEC-11 | Statutory retention scope | apply to every tenant (today) · tenant profile | **`record_keeping` profile; default `legacy` = today** | Art. 6(1)(c) exists only where a legal duty exists; the switch lets the legal answer be applied without a release | LEG-03, LEG-04, LEG-17 | `06` §3, E09 | proposed |
| DEC-12 | Offline revocation and retention | document the gap (today) · quarantine + stable codes + shorter defaults + shared-device mode | **quarantine 14 d, `account.closed`/`membership.ended`, defaults 90/30, shared-device mode, key hygiene, awaited wipe** | a hint is not protection; the server can signal closure during the grace; data loss after 14 d is deliberate and disclosed | LEG-09, LEG-10 | `07`, E10, E11 | proposed |
| DEC-13 | Backups | enable the Helm CronJob as is · enable only with a replay ledger and restore procedure | **ledger + mirror + replay before enabling; dumps ≤ 35 d** | without replay, every restore re-creates erased persons | LEG-11 | `09` §6, E14 | proposed |
| DEC-14 | Privacy-operation observability | logs only (today) · metrics + endpoint + consistency beat | **metrics + admin endpoint (counts/states only) + `privacy.consistency`** | `open_failing` is a log field; partial erasures were invisible | no | `08` §5–6, E15 | proposed |
| DEC-15 | Notifications retention | none (today) · R-48 90 d after read / 180 d unread | **R-48** | recipient-bound texts with task names; no reason to keep after reading | DSB (NFR-011 v1.29 rule) | `06` §2.3, E13 | proposed |
| DEC-16 | `garden_plan_audit` actor at erasure | tombstone (code today; GP-NFR-055) · marker (NFR-011 R-26 text) | **marker** | tenant-internal change log, 365 d, no statutory or Art. 15 need for linkability; resolves the spec contradiction | LEG-15 | `04` §4.1, E04 | proposed |
| DEC-17 | Member e-mail in `/members` | every member (today) · `management` only | **`management` only (breaking)** | necessity doubtful; employees' addresses | LEG-14 | `05` PRIV-305, E08 | proposed |
| DEC-18 | MCP raw keys | keep · `PersonRef` | **`PersonRef`; `inspector="mcp:<key>"` → `inspected_by_key`** | GP-API-034 forbids keys in REST; MCP must follow | no | `05` PRIV-310, E08 | proposed |
| DEC-19 | Status of a closed account without login | add an unauthenticated status endpoint · rely on the confirmation e-mail | **e-mail only** | an anonymous status endpoint leaks whether an account existed | no | `03` PRIV-102 | proposed |
| DEC-20 | Spec drift found (REQ-025 footer 1.5 vs header 1.40; NFR-011 footer 1.7; REQ-051 footer 1.0; `redux_state`/`i18next`/`theme` rows; REQ-023 §5b.1 backup read access; docs "DSFA durchgeführt"; GP-FR-109 vs E-16) | fix silently · versioned spec change set | **versioned change set (E16)** | the package must not change requirements silently | LEG-12 for the Art. 13/14 texts | `06` §9, E16 | proposed |
| DEC-21 | Offline opt-in | cache on first login (today) · explicit "Offline-Modus" toggle per device | **toggle, default off for new installations** | settles TDDDG "expressly requested"; minimises device data for users who never work offline | LEG-09 | `07` §2, E11 | proposed |
| DEC-22 | `created_by` on backfilled rows | set to the performer (#2770 item 3 suggestion) · `null` + correction right for the performer | **`null` (system origin) + PRIV-215** | a backfill has no author; copying the performer into `created_by` would cross attribution roles (PRIV-002) | no | `04` §3.3 | proposed |

---

## B. Questions requiring legal counsel / DPO (LEG)

| ID | Question | Default the package ships with | Alternative if answered differently | Where it lands | Status |
|----|----------|-------------------------------|-------------------------------------|----------------|--------|
| LEG-01 | Who is controller for member data of an organisation tenant — the tenant (operator = processor, Art. 28), joint (Art. 26), or the operator? Self-hosted: the operator is the tenant. | tenant = controller, operator = processor; the operator is controller for accounts, platform tenant, security audit, logs | if operator is (joint) controller: the LIAs, DPIA and Art. 13/14 texts are the operator's; review-queue decisions by tenant leads need a mandate | `06` §1, `11` | open |
| LEG-02 | Balancing test (Art. 6(1)(f)) for performer/creator attribution visible to co-members, and for the 5-year retention of the attribution in the care log (R-25). | LIA-1 as written; name visible to current members under safeguards; attribution → marker after R-25; suppression for former members | if rejected: default `leads_and_self` for all tenants; shorter attribution retention (e.g. 2 y) via a new ceiling | `06` §4.1, `05` §4 | open |
| LEG-03 | Does PflSchG §11 bind only professional users, and which KCanG provision carries the 5-year documentation duty for cultivation associations? May the operator rely on the tenant's declaration (`record_keeping`)? | profile with default `legacy` (= statutory rules for everyone, today) | if duties apply more broadly: keep `legacy`; if narrower: change new-tenant defaults and run the reclassification job | `06` §3, E09 | open |
| LEG-04 | Must the applicator's **name** stay legible in a §11 record for 3 years (Art. 17(3)(b)), or is the pseudonym sufficient? Today the name is cleared at erasure. | current behaviour (clear name, keep tombstone) | sealed-name field readable by `management ∧ lead` with step-up until the statutory end | `03` PRIV-123 | open |
| LEG-05 | Basis for storing and showing confirmation/performer identities of employees (Art. 88, §26 BDSG after CJEU C-34/21); is the care log "geeignet" under §87(1) No. 6 BetrVG; what transparency the platform must provide to employers. | store the principal; show per `attribution_visibility`; no statistics; audit of filter/export use; works-council template text | if §26 BDSG cannot carry it: `leads_and_self` mandatory for employee tenants; filter/export only with a documented purpose | `06` §5, E08, E16 | open |
| LEG-06 | (a) Former-member name suppression period (default 90 d, 0–365) and whether leads may keep the name longer; (b) is it acceptable that a former tenant's rows drop out of the person's Art. 15 export (manifest reads current tenants only, REQ-025 §3.1.2 rule 4)? | 90 d, no lead exception; (b) unchanged | (a) other value via setting; (b) extend the manifest to tenants the person left within the last N days | `03` §3, `06` §4.3 | open |
| LEG-07 | Purpose compatibility (Art. 5(1)(b), 6(4)) of copying the performer from statutory rows into the care log (v0104, consistency job); confirmation that `pest_control` care events are not §11 records and may be deleted with the tenant. | compatible (LIA-2); deletion with the tenant | if incompatible: backfill with `performed_by_user_key = null` for statutory sources; one-off correction | `06` §4.2, E01 | open |
| LEG-08 | Is a review model (system finds candidates by authorship/name tokens, tenant leads decide within 30 d, decision recorded) sufficient for Art. 17 regarding free text? Is automatic name-token flagging proportionate? May the decision be left to tenant leads (see LEG-01)? | review queue, SLA 30 d, flagging on display-name tokens only | shorter SLA; operator-side review; automatic redaction of `name_token` matches after SLA expiry | `04` §5, E07 | open |
| LEG-09 | TDDDG §25(2) Nr. 2: are IndexedDB `kp-plan-cache`/`kp-write-queue`, Cache Storage namespaces and the listed localStorage keys "strictly necessary" for a service the user expressly requested? Does an explicit offline toggle settle it? | classification per `07` §2; toggle recommended (DEC-21) | consent dialog for offline storage (UI-NFR-013 pattern) | `07` §2, REQ-025 §10 | open |
| LEG-10 | Device retention: pending 90 d / unsendable 30 d / dead-session 14 d (today 365/90/none); is documenting the "account deleted elsewhere" gap plus quarantine adequate; shared-device measures (idle wipe, session-bound queue). | defaults as `07` §6; shared-device mode opt-in | shorter defaults; shared-device mode default on for kiosk; encryption of the queue with a server-held key (not proposed) | `07` §6–8, E10/E11 | open |
| LEG-11 | Backups: dump retention ≤ 35 d with re-application of erasures on restore — acceptable under Art. 17? May the replay ledger keep the raw `user_key` for that window (Art. 6(1)(c) to perform the erasure)? | yes / yes, R-45 | if the raw key may not be kept: store `(collection, row_key)` lists instead (larger, still personal); or shorter dump retention | `09` §6, E14 | open |
| LEG-12 | Is a full DPIA required (Art. 35) — for which operating model; RoPA entries for the care log, review queue, device storage; Art. 13/14 texts (third-party labels, photos, former-member rule, offline storage). | pre-screening says: likely required for commercial SaaS with employee tenants; not for self-hosted hobby use | DPO decides; texts drafted in E16 | `11`, E16, E17 | open |
| LEG-13 | Tenant export archive (REQ-056 §8) with member keys/names and site GPS leaving the installation (also platform-admin export of orphaned tenants): basis, Art. 28/44 implications, DPIA note (REQ-056 O-03). | unchanged (not in this package's engineering scope) | — | REQ-056 | open |
| LEG-14 | May every member see every member's e-mail address (`GET /members`)? | restrict to `management` (DEC-17) | keep for all with an opt-in per member | `05` PRIV-305 | open |
| LEG-15 | Is one deterministic pseudonym per person across statutory rows (and today the plan audit) for up to 5 years proportionate; may the plan audit use the marker instead (DEC-16)? | keep for statutory + security audit; marker for the plan audit | per-row random tokens for statutory rows (breaks the Art. 15 tombstone lookup) | `04` §2.3 | open |
| LEG-16 | Sentry event processing on Art. 6(1)(f) (REQ-025 §9, "rechtlich zu bestätigen") — pre-existing. | as REQ-025 | — | REQ-025 §9 | open (pre-existing) |
| LEG-17 | Which KCanG paragraph founds the 5-year harvest/quality documentation (REQ-025 L219 "CanG §X"), and does it apply to personal cultivation at all? | R-16 as today | adjust floor/scope via `record_keeping` | `06` §2.4 | open |

---

## C. Decisions already taken by the operator that this package relies on (verified in specs/issues)

| Date | Decision | Source |
|------|----------|--------|
| 2026-10-18 (E-16) | `performed_by` filter: viewer/grower self only; lead/`management` anyone; care log is not a §11 record; free texts of erased members stay (diary precedent) | REQ-053 §32.3, #2411 |
| 2026-10-19 | WP 4.3 placeholders 1–5 confirmed; item 6 (DSFA wording, balancing test) → #2517 | #2416 |
| 2026-11-03 (§32.5 Pkt. 5) | M4 backfill: performer only from an account reference, otherwise `null` | REQ-053 §32.5 |
| 2026-11-03 (§32.5 Pkt. 13) | bed-list CSV `include_assignment` without role check — "a barrier only at the CSV protects nothing" | REQ-053 §32.5 — this package proposes to revisit under `attribution_visibility` (PRIV-309) |
| 2026-10-04 (#2134/#2135) | INV-1 settlement at request time; personal garden in the Art. 15 bundle; third-party free text in the bundle unmasked | REQ-025 v1.32/1.33 |
| 2026-09-26 (#1824) | personal tenant erased entirely at account erasure | REQ-025 Q-E1/Q-E5 |
| 2026-11-09 | REQ-053 partition: #2770 next after #2758; #2517 legal hold | partition artefact |

---

## D. Change control

A DEC row changes status when the operator confirms it (comment in the issue that
implements it, referenced here). A LEG row changes to `decided` with the date, the
decision, and the rule/setting it changed; the affected PRIV requirement gets a changelog
entry in its document. Nothing in this log is applied to REQ/NFR documents without a
versioned edit (E16).
