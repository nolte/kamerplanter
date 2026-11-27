---
id: F-17
title: Import-Vorprüfung mit E-Mail-Zuordnung und Importliste
status: draft
roadmap_item: R-19
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/backend/app/domain/services/step_up_service.py:249
      resolution: revisit-after Betreiberentscheidung zur Gültigkeit der Step-up-Bestätigung (D2)
      evidence: "REAUTH_TOKEN_TTL_SECONDS = 300 (:249), CODE_TTL_SECONDS = 600 (:253), Einmalverbrauch '_reauth_store.consume' / '_code_store.consume' (:694-698); REQ-056 §12.1 :453 'geprüft vor jedem Parsen'"
    - kind: drift
      target: project/features/tenant-import-preflight.md:59
      resolution: revisit-after Betreiberentscheidung, was „abgelehnter Upload" nach F-15 Kriterium 4 heißt (D1)
      evidence: "'abgelehnte Uploads erscheinen nur im Audit' gegen tenant-archive-size-limits.md:52 'die Prüfung läuft nur im Worker'; heute: Ablehnung vor dem Speichern (service :782-786), Datensatz erst :788"
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:168
      resolution: revisit-after Test-Hooks 4/5 decken den neuen Status in Stale-Sweep und R-40-Purge ab
      evidence: "STALE_AFTER = timedelta(hours=6); list_stale_active nimmt 'pending/validating/running' (interfaces/tenant_export_store.py:135-138); delete_finished_before nur 'completed/failed' (:131-133)"
    - kind: prior-art
      target: src/backend/tests/unit/test_route_consumers_check.py:368
      resolution: revisit-after Feature legt die Routenform fest und nennt die Registrierungen als Hooks
      evidence: "'assert len(checker.collect_operations(app)) == 915'; Step-up-Guard guards/test_credential_changes_go_through_the_step_up.py:158-162 nennt 'request_import passes the verifier'; Body-Grenze am exakten Pfad: router.py:41-42, main.py:431-443, nginx.conf:98, scripts/ci/assert_chart_contracts.sh:555-591"
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:565
      resolution: revisit-after Kriterium 1/5 sagen, wo Mitgliederliste und Quelle liegen und wann sie geleert werden
      evidence: "'report: dict[str, int] = {}  # Anzahl je Collection; keine Inhalte'; spec/privacy/02-personal-data-inventory.md:139 führt nur requested_by_user_key; Muster: member_grants wird am Ende geleert (service :1064, :1110)"
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:480
      resolution: split-out neues Feature in R-19 oder dokumentierter Ausschluss
      evidence: "§12.4: 'Schema-Validierung jedes Dokuments gegen das Domänenmodell (422)' gegen tenant_export_service.py:52-53 'Not part of this slice: … the per-document validation against the domain models'; validate_documents prüft nur Besitz und Verweise (tenant_import_engine.py:167-183)"
    - kind: prior-art
      target: spec/privacy/14-contradiction-register.md:59
      resolution: proceed
      evidence: "W-38: NFR-011 R-40 'Nicht implementiert' (NFR-011:151) → 'Umgesetzt (#2138)', PRA-3.10 / TA-917; TA-756 'Zuordnung gesperrt' (spec/privacy/10-testing-and-acceptance.md:334)"
---

## Description

Wer heute einen Mandanten importiert, muss die internen Mitglieds-Schlüssel
aus der Datei `members.jsonl` des Archivs abschreiben, bevor er die Mitglieder
per E-Mail Zielkonten zuordnen kann; das Archiv selbst sieht er erst nach dem
Import. Frühere Importe sind nirgends aufgelistet.

Nach dieser Änderung lädt der Plattform-Admin das Archiv hoch, bestätigt sich
per Step-up und sieht dann eine Vorschau: Herkunft, Inhalt und die Mitglieder
mit Anzeigename und bisheriger Rolle. Für jedes Mitglied trägt er die E-Mail
des Zielkontos ein; die Rolle ist vorbelegt und wird erst mit seiner
Bestätigung vergeben, nicht zugeordnete Mitglieder sind vorab als
„wird pseudonymisiert“ markiert. Der Import nutzt das bereits hochgeladene
Archiv. Ein nicht importiertes Archiv verschwindet nach 24 Stunden. Eine Liste
zeigt frühere Importe mit Quelle, Ziel, Status und Fehler sowie den
Fortschritt eines laufenden Imports.

## Acceptance criteria

- [ ] **acceptance-1** Nach Upload und Step-up sieht der Admin vor dem Import Herkunft (Name, Kurzname) und Mitgliederliste (Anzeigename, bisherige Rolle und Scopes); der Import verwendet das hochgeladene Archiv ohne zweiten Upload und ohne erneuten Step-up.
- [ ] **acceptance-2** Die Zuordnungszeilen sind aus der Mitgliederliste vorbelegt; der Admin trägt je Mitglied die E-Mail des Zielkontos ein, eine unbekannte E-Mail wird an dieser Zeile gemeldet.
- [ ] **acceptance-3** Die bisherige Rolle ist vorausgewählt und wird nur mit Bestätigung des Admins vergeben; nicht zugeordnete Mitglieder sind vor dem Import als „wird pseudonymisiert“ gekennzeichnet.
- [ ] **acceptance-4** Ein vorgeprüftes, nicht importiertes Archiv wird nach 24 Stunden gelöscht.
- [ ] **acceptance-5** Die Admin-Seite listet frühere Importe (Datum, Quelle, Ziel-Mandant, Admin, Status, Fehlertext) und zeigt bei einem laufenden Import die Phase (prüfen, Dokumente, Messwerte, fertig); abgelehnte Uploads erscheinen nur im Audit, Einträge werden nach 30 Tagen gelöscht.
- [ ] **acceptance-6** Beschriftungen und Doku (DE + EN) beschreiben den Ablauf; REQ-056 §8.2/§13.5/§14 und der Status von NFR-011 R-40 sind nachgezogen.

## Test hooks

- **acceptance-1** — router/service tests: preflight returns manifest + members only after step-up bound to the archive hash; import reuses stored archive — pending
- **acceptance-2** — vitest on `AdminTenantImportsPage` (rows pre-filled from preflight, per-row `IMPORT_MEMBER_NOT_FOUND`) — pending
- **acceptance-3** — service test: role from the request, never from `members.jsonl` (SEC-003); vitest for the pseudonymised hint — pending
- **acceptance-4** — unit test of the expiry sweep (24 h) — pending
- **acceptance-5** — repository list method test + vitest of the history table and phase display — pending
- **acceptance-6** — i18n completeness + `mkdocs build --strict` + spec diff review — pending

## Consistency notes

**E-mail member mapping prior art (proceed).** Established: the import
already takes `member_mapping {email, role, admin_scopes}` with an
admin-confirmed role and a per-row `IMPORT_MEMBER_NOT_FOUND` refusal
(`tenant_export_service.py:954-982`, `router.py:217-223`,
`AdminTenantImportsPage.tsx:67-103,272-311,580-610`). The delta is pre-filling
the rows from the preflight instead of typing the archive user key
(`AdminTenantImportsPage.tsx:113-114`).

**Upload retention and status (drift, proceed).** Established: REQ-056 §13.5
(`:561,571`) deletes the uploaded archive immediately after completion or
failure, and the status literal has no preflight state
(`tenant_export.py:37`). Keeping the upload for 24 h, a preflight state and
route need a §8.2/§13.5/§14 amendment (criterion 6).

**Step-up invariant (drift, proceed).** Established: the service requires the
`tenant_import` step-up before anything of an archive is parsed, bound to the
upload's SHA-256 (`tenant_export_service.py:750-771`). Operator decision
2026-11-17: the step-up moves to the preflight, bound to the archive hash, and
is reused by the import of the same archive — the invariant holds.

**Retention prior art (proceed).** Established: `REQUEST_RETENTION` = 30 days
(NFR-011 R-40, `tenant_export_service.py:170-171`) purges import records in
the hourly beat (`:1407-1411`); the same sweep carries the 24 h preflight
expiry. `NFR-011:151` still marks R-40 as not implemented and is corrected.

**History fields (decision).** Established: the store has no list method
(`tenant_export_store.py:115-138`) and `TenantImportRequest` has neither a
source nor a progress field (`tenant_export.py:81-105`); refused uploads are
audit-only (`tenant_export_service.py:782-786`). Operator decision 2026-11-17:
refused uploads stay audit-only; source = name + slug from `tenant.json`;
progress = coarse phases.

**Same-file order with F-12 (prior-art, proceed).** Established: F-12 rewrites
the back links in `AdminTenantImportsPage.tsx:365,637`; there is no shared
criterion, only a merge order on the same file.

**E-09 / SEC-003 (constraint).** The archive keeps carrying no e-mail
(REQ-056 E-09); the role is only pre-selected in the UI and the backend keeps
reading it from the admin's request, never from `members.jsonl` (SEC-003,
`tenant_export.py:72-73`).

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`; same run, triggers and caveats as recorded in `tenant-archive-size-limits.md` (no test run; resolutions are proposals; line references into this file are those of `cc8531492`). The frontmatter holds the seven findings of this run; the five findings of 2026-11-17 (`feature-consistency-reviewer@1004fe514`) are listed with their fate. The report's verdict: **blocked on two operator decisions (D1, D2)**, see the German section below.

**Findings of 2026-11-17 — fate.**

1. `src/backend/app/domain/services/tenant_export_service.py:954` (prior-art, proceed) — still true (`_resolve_member_mapping` `:954-993`, `router.py:217-223`). The page doc is now at `AdminTenantImportsPage.tsx:113-115`, the row message at `:311`.
2. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:561` (drift, proceed) — moved: §13.5 `:557-572`, the sentence "sofort gelöscht" at `:572`. `tenant_export.py:37` still true; the status type has gained `cleanup_pending`, still no pre-check status.
3. `src/backend/app/domain/services/tenant_export_service.py:750` (drift, proceed) — still true (`:750-771`); to be extended by the first new finding.
4. `src/backend/app/domain/services/tenant_export_service.py:170` (prior-art, proceed) — still true. The purge is at `:1410-1411`; `:1407` is the loop over aborted imports. `NFR-011:151` is still stale.
5. `project/features/platform-settings-in-admin.md` (prior-art, proceed) — **obsolete.** F-12 is `done`; the back links are at `AdminTenantImportsPage.tsx:366,638`.

The body note "History fields" is still true: no list method (`interfaces/tenant_export_store.py:115-138`), no source or progress field (`tenant_export.py:81-107`).

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@1004fe514
  findings:
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_export_service.py:954
      resolution: proceed
      evidence: "member_mapping {email, role, admin_scopes} with admin-confirmed role and per-row IMPORT_MEMBER_NOT_FOUND exists (:954-982, router.py:217-223, AdminTenantImportsPage.tsx:67-103,272-311,580-610); the delta is pre-filling the rows from a preflight (page doc :113-114)."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:561
      resolution: proceed
      evidence: "§13.5 deletes the uploaded archive immediately after completion or failure; the status literal has no preflight state (tenant_export.py:37) — §8.2/§13.5/§14 amended."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:750
      resolution: proceed
      evidence: "Invariant: the step-up comes first and nothing is parsed before it, bound to the upload's SHA-256 (:750-771); operator decision: step-up at preflight, bound to the archive hash, reused by the import."
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_export_service.py:170
      resolution: proceed
      evidence: "REQUEST_RETENTION=30 d (NFR-011 R-40, :170-171) purges import records in the hourly beat (:1407-1411) — hook for the 24 h preflight expiry; NFR-011:151 'Nicht implementiert' is stale."
    - kind: prior-art
      target: project/features/platform-settings-in-admin.md
      resolution: proceed
      evidence: "F-12 rewrites the back links in AdminTenantImportsPage.tsx:365,637; no shared criterion, only a same-file merge order."
```

**New findings.**

- **Step-up factors are single-use (drift, `step_up_service.py:249`).** `REAUTH_TOKEN_TTL_SECONDS = 300` (`:249`), `CODE_TTL_SECONDS = 600` (`:253`), consumed once (`_reauth_store.consume` / `_code_store.consume`, `:694-698`); REQ-056 §12.1 (`:453`) checks "before any parsing". "Reuse" therefore means a confirmation stored on the pre-check record, valid for up to 24 h and so far not bound to the same admin — operator decision D2.
- **"Refused uploads appear only in the audit" (drift, this file `:59`).** Against F-15 criterion 4 (`tenant-archive-size-limits.md:52`, the check runs only in the worker): today the refusal happens before storing (service `:782-786`), the record is created at `:788`. With the worker check, upload and record exist before an archive error is known; "only in the audit" cannot hold for archive errors — operator decision D1.
- **The new status in stale sweep and purge (drift, `tenant_export_service.py:168`).** `STALE_AFTER = timedelta(hours=6)`; `list_stale_active` takes `pending/validating/running` (`interfaces/tenant_export_store.py:135-138`), `delete_finished_before` only `completed/failed` (`:131-133`). A pre-checked archive waits up to 24 h while the sweep ends waiting records after 6 h, and an expired pre-check record would never be purged. Test hooks 4/5 should cover the new status in both.
- **Route form and registrations (prior-art, `test_route_consumers_check.py:368`).** The route counter asserts `len(checker.collect_operations(app)) == 915`; the step-up guard `guards/test_credential_changes_go_through_the_step_up.py:158-162` names "request_import passes the verifier"; the body limit hangs on the exact path (`router.py:41-42`, `main.py:431-443`, `nginx.conf:98`, `scripts/ci/assert_chart_contracts.sh:555-591`). New routes change the counter and the step-up classification; if the upload moves to a new path, four layers and three guards move with it. The feature should fix the route form and name the registrations as hooks.
- **Where the member preview and the source live (drift, `REQ-056:565`).** The record's `report` is "Anzahl je Collection; keine Inhalte"; `spec/privacy/02-personal-data-inventory.md:139` lists only `requested_by_user_key`; the existing pattern empties `member_grants` at the end (service `:1064`, `:1110`). Display names of the archive members on the record would sit for 30 days (R-40) in a collection that carries no content according to spec and privacy inventory. Criteria 1/5 should say where member list and source are stored and when they are emptied.
- **Per-document validation has no owner (drift, split-out, `REQ-056:480`).** §12.4 promises "Schema-Validierung jedes Dokuments gegen das Domänenmodell (422)"; `tenant_export_service.py:52-53` says "Not part of this slice: … the per-document validation against the domain models", and `validate_documents` checks only ownership and references (`tenant_import_engine.py:167-183`). None of the three features owns it; R1–R17 do not name it. F-17 does not cover it: R5 and criterion 1 check only signature and format. Since F-19 and F-20 the archive carries more enum fields as raw documents (`plant_instance.py:47-62`, `site.py:709`); the roundtrip test validates only one good document (`test_tenant_export_roundtrip.py:498`); a manipulated enum would be written and break later reads. Technically the check belongs in `_verified_archive` (worker); the pre-check would only display it. With one installation signed archives are the normal case; affected are unverified and older archives. Related gap, not verified in depth: §8.4 step 1 promises to lift older archives through migrations, the service only refuses newer archives (`:870`), and the comment in `v0095_task_suggested_flag.py:15` points to case-by-case handling. Not blocking, but it needs an owner — see the German section.
- **R-40 correction also in the privacy lane (prior-art, proceed, `spec/privacy/14-contradiction-register.md:59`).** W-38 corrects NFR-011 R-40 from "Nicht implementiert" (`NFR-011:151`) to "Umgesetzt (#2138)" (PRA-3.10 / TA-917); TA-756 "Zuordnung gesperrt" (`spec/privacy/10-testing-and-acceptance.md:334`) later touches the same mapping surface. Whoever merges first settles the correction.

**Criterion by criterion.**

- **Criterion 1** should name "the same admin" and the asynchronous flow (upload → step-up → worker checks → preview by polling). It does not prove the chain as sprint-value verifier; an integration test "pre-check → import of the stored archive with readings → empty difference" as an extended hook would.
- **Criterion 4** leaves open what happens to the record after 24 h (status, visibility in the list).
- **Criterion 5** bundles four things and should be split. The 30-day deletion exists already. The phase "Messwerte" presupposes F-16 (dependency now recorded under References).
- The isolation matrix `test_garden_plan_tenant_isolation.py` is not affected: the routes are platform-admin routes without a tenant-scoped resource.
- The comment `test_route_consumers_check.py:232` ("No consumer in the tree yet") is stale; the UI exists.

**Already implemented:** the e-mail mapping with confirmed role, the row-exact message, the 30-day purge, the status card for a single import (`TenantImportStatusCard.tsx`).

**Cross-feature.** F-17 criterion 5 depends on F-16; the coupling with F-15 criterion 4 (interim solution in F-15, or both features in one sprint without a release in between) and the comparison with issue #3140 are in `tenant-archive-size-limits.md`. The issue decides neither D1 nor D2 and does not mention the per-document validation.

**Edits required before `ready`** (the report's verdict for F-17, translated): blocked on D1 and D2. After the decisions:

1. Fix the route form and name the registrations as hooks.
2. Handle the new status in sweep and purge.
3. State where the member preview is stored and when it is emptied.
4. Split criterion 5.
5. The per-document validation (§12.4) does not block, but needs an owner.

## Risks

- A stored preflight archive (up to ~500 MiB) occupies object storage for up to 24 h.
- The step-up's validity window must cover the time between preflight and import; too short a TTL forces a second step-up.

## References

- Issue #2138 (MT-042), roadmap item R-19; depends on F-15
- `project/requirements/tenant-export-import-remainder.md` (R5–R8, R15–R17)
- Criterion 5 (phase „Messwerte“) depends on F-16 — recorded by the consistency re-run 2026-11-27

## Betreiberentscheidungen 2026-11-27

- Es gibt nur **eine** Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv laufen in einer eigenen Lane.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`).
- Ein Speicherlimit des Workers von rund 2 GiB ist akzeptabel.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

F-17 ist auf D1 und D2 blockiert.

- **D1 — Erscheinen Archivfehler als fehlgeschlagene Vorprüfung in der Liste?** Heute wird ein Upload vor dem Speichern abgelehnt (`tenant_export_service.py:782-786`), der Datensatz entsteht erst danach (`:788`); die Entscheidung vom 2026-11-17 lautet „abgelehnte Uploads erscheinen nur im Audit“. Mit F-15 Kriterium 4 prüft nur noch der Worker, Upload und Datensatz existieren also, bevor ein Archivfehler bekannt ist.
  - **Ja — „nur im Audit“ gilt nur für Ablehnungen vor dem Speichern (Rolle, Größe, Step-up):** Archivfehler stehen als fehlgeschlagene Vorprüfung in der Importliste; der Admin sieht den Grund dort.
  - **Nein — auch Archivfehler nur im Audit:** Mit der Prüfung im Worker ist das laut Bericht nicht haltbar, weil Upload und Datensatz dann schon existieren; der Datensatz müsste nachträglich entfernt werden.
- **D2 — Wie lange gilt die Step-up-Bestätigung der Vorprüfung, und ist sie an denselben Admin gebunden?** Heute sind die Faktoren einmalig und kurzlebig (`step_up_service.py:249` 300 s, `:253` 600 s, Verbrauch `:694-698`); REQ-056 §12.1 (`:453`) prüft vor jedem Parsen. „Wiederverwenden“ heißt deshalb: eine am Vorprüf-Datensatz gespeicherte Bestätigung.
  - **Bis zum 24-h-Ablauf der Vorprüfung:** Ein Step-up genügt für Vorprüfung und Import; die Bestätigung gilt bis zu 24 h statt wenige Minuten.
  - **Kürzer als 24 h:** Liegt zwischen Vorprüfung und Import mehr als die Frist, ist ein zweiter Step-up nötig.
  - **An denselben Admin gebunden:** Nur wer vorgeprüft hat, importiert ohne neuen Step-up; ein zweiter Admin bestätigt selbst.
  - **Nicht gebunden:** Jeder Plattform-Admin kann das vorgeprüfte Archiv mit der fremden Bestätigung importieren.
- **Dokumentvalidierung nach REQ-056 §12.4 — wer besitzt sie?** Heute prüft der Import nur Besitz und Verweise (`tenant_import_engine.py:167-183`); die Schema-Validierung jedes Dokuments ist ausdrücklich nicht Teil der Lieferung (`tenant_export_service.py:52-53`), obwohl §12.4 (`REQ-056:480`) sie verspricht. Kein Feature von R-19 nennt sie. Blockiert F-17 nicht.
  - **Eigenes kleines Feature in R-19:** Die Prüfung kommt in den Worker (`_verified_archive`), die Vorprüfung zeigt das Ergebnis; ein manipuliertes Enum wird abgelehnt statt geschrieben.
  - **Dokumentierter Ausschluss mit Korrektur von §12.4:** Unverifizierte und ältere Archive können weiter Dokumente einspielen, die spätere Lesezugriffe brechen; signierte Archive der eigenen Installation sind nicht betroffen.
