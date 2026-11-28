---
id: F-17
title: Import-Vorprüfung mit E-Mail-Zuordnung und Importliste
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-28
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/frontend/src/utils/tenantImport.ts:44
      resolution: proceed
      evidence: "Das Step-up-Ziel 'archive:<32 Hex>' berechnet der Browser aus der Datei (:44-52); beim Start ohne erneuten Upload liegt keine vor, und TenantImportResponse (api/v1/tenant_exports/schemas.py:61-75) gibt archive_sha256 nicht aus. acceptance-3 legt fest: Die Vorschau nennt das Ziel."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:1019
      resolution: proceed
      evidence: "'actor_user_key=claimed.requested_by_user_key' macht den Hochladenden zum Audit-Akteur und Ersatz-Eigentümer; startet ein anderer Admin (D2), handelt er. Neues Kriterium acceptance-4."
    - kind: drift
      target: src/backend/app/api/v1/tenant_exports/router.py:212
      resolution: proceed
      evidence: "Synchrone Ablehnungen der neuen Start-Route (unbekannter Plan, Zuordnung) hatten kein Kriterium zu Antwort, Zustand des Vorprüf-Datensatzes und Audit. Neues Kriterium acceptance-7."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:835
      resolution: proceed
      evidence: "get_import (:835-845) gibt den Datensatz jedem Plattform-Admin; mit der Mitgliederliste läse jeder Admin die Namen. acceptance-10 begrenzt die Sicht; neue Kontofelder brauchen Guard R6 (scripts/check_privacy_inventory.py:54, REQ-056 §12.3)."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:773
      resolution: proceed
      evidence: "refused:<Code> gibt es nur für Ablehnungen aus dem Block :773-786; Rolle, Größe und Step-up schreiben keinen Import-Audit-Eintrag. acceptance-8 sagt nur noch, dass sie nicht in der Liste stehen."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "'Plan vorhanden' und 'E-Mail → Konto' liegen nach F-15 an der Upload-Antwort und wandern hier an die Start-Route; der F-15-Test zu request_import wird angepasst (Hook zu acceptance-7). Begründung in den Consistency notes (Agentenlauf 2026-11-28)."
    - kind: prior-art
      target: src/backend/app/api/v1/tenant_exports/router.py:213
      resolution: proceed
      evidence: "Ratenlimit '@limiter.limit(settings.rate_limit_tenant_import …)' (:213) und STEP_UP_RESPONSES (:212) stehen nur am Upload; Light-Modus-Ausschluss AK-43 (REQ-056:704). In den Hooks zu acceptance-2 und -3 benannt."
---

## Description

Wer heute einen Mandanten importiert, muss die internen Mitglieds-Schlüssel
aus der Datei `members.jsonl` des Archivs abschreiben, bevor er die Mitglieder
per E-Mail Zielkonten zuordnen kann; das Archiv selbst sieht er erst nach dem
Import. Frühere Importe sind nirgends aufgelistet.

Nach dieser Änderung lädt der Plattform-Admin das Archiv hoch und bestätigt
sich per Step-up. Der Hintergrundprozess prüft das Archiv, danach zeigt die
Seite eine Vorschau: Herkunft, ob das Archiv aus dieser Installation stammt,
und die Mitglieder mit Anzeigename und bisheriger Rolle. Für jedes Mitglied
trägt der Admin die E-Mail des Zielkontos ein; die Rolle ist vorbelegt und
wird erst mit seiner Bestätigung vergeben, nicht zugeordnete Mitglieder sind
vorab als „wird pseudonymisiert“ markiert. Der Import nutzt das bereits
hochgeladene Archiv. Die Bestätigung gilt eine Stunde und nur für den Admin,
der sie gegeben hat; wer den Import startet, ist der handelnde Admin. Ein nicht importiertes Archiv verschwindet nach
24 Stunden.

Eine Liste zeigt frühere Vorprüfungen und Importe mit Quelle, Ziel, Status und
Fehler sowie die Phase eines laufenden Imports. Scheitert die Prüfung an einem
Fehler im Archiv, steht das mit Grund in dieser Liste.

## Acceptance criteria

- [ ] **acceptance-1** Nach Upload und Step-up zeigt die Import-Seite, sobald die Hintergrundprüfung abgeschlossen ist, eine Vorschau mit Herkunft (Name und Kurzname des archivierten Gartens), Signaturstatus und Mitgliederliste (Anzeigename, bisherige Rolle und Zusatzberechtigungen); solange der Admin den Import nicht startet, entsteht kein Garten.
- [ ] **acceptance-2** Der Admin, der die Vorprüfung per Step-up bestätigt hat, startet den Import innerhalb einer Stunde nach dem Step-up aus der Vorschau, ohne das Archiv erneut hochzuladen und ohne erneuten Step-up.
- [ ] **acceptance-3** Startet ein anderer Plattform-Admin den Import oder liegt der Step-up länger als eine Stunde zurück, verlangt der Start einen neuen Step-up für dieses Archiv, und ohne ihn wird nichts importiert; die Vorschau nennt das Step-up-Ziel des Archivs, sodass auch ein Konto ohne Passwort (Code oder frische Anmeldung) ohne die Datei bestätigen kann.
- [ ] **acceptance-4** Der Admin, der den Import startet, ist der handelnde Admin: Er steht im Audit und wird Eigentümer des neuen Gartens, wenn kein zugeordnetes Mitglied Leitung mit Verwaltung erhält; wer das Archiv hochgeladen hat, bleibt am Eintrag als Hochladender sichtbar.
- [ ] **acceptance-5** Die Zuordnungszeilen sind aus der Mitgliederliste der Vorschau vorbelegt; der Admin trägt je Mitglied die E-Mail des Zielkontos ein, und eine E-Mail ohne aktives Konto wird an dieser Zeile gemeldet.
- [ ] **acceptance-6** Die bisherige Rolle ist vorausgewählt und wird nur mit Bestätigung des Admins vergeben; Mitglieder ohne Zuordnung sind vor dem Start als „wird pseudonymisiert“ gekennzeichnet.
- [ ] **acceptance-7** Lehnt der Start ab (unbekannter Plan, eine Zuordnung ohne aktives Konto oder gültige Rolle), entsteht kein Garten, die Vorprüfung bleibt bis zu ihrem Ablauf startbar, und die Ablehnung steht mit ihrem Code im Audit.
- [ ] **acceptance-8** Die Admin-Seite listet Vorprüfungen und Importe mit Datum, Quelle, Ziel-Garten, Admin, Status und Fehlertext und zeigt bei einem laufenden Import die Phase (Prüfen, Datensätze schreiben); eine an einem Archivfehler gescheiterte Vorprüfung steht dort als fehlgeschlagen mit Grund und betroffenen Einträgen, eine vor dem Speichern abgelehnte Anfrage (Rolle, Größe, Step-up) erscheint nicht in der Liste.
- [ ] **acceptance-9** Ein vorgeprüftes, nicht importiertes Archiv bleibt 24 Stunden startbar — auch wenn es länger als sechs Stunden wartet — und ist danach gelöscht; der Eintrag steht dann als abgelaufen in der Liste, lässt sich nicht mehr starten und verschwindet wie jeder Listeneintrag 30 Tage nach seinem Ende.
- [ ] **acceptance-10** Die Mitgliederliste der Vorschau sieht nur ein Admin mit gültiger Bestätigung für dieses Archiv (Step-up höchstens eine Stunde alt); jeder andere Plattform-Admin sieht den Eintrag ohne Namen. Die Mitgliederliste wird geleert, sobald der Import endet oder die Vorprüfung abläuft.
- [ ] **acceptance-11** Beschriftungen und Doku (DE + EN) beschreiben den Ablauf; REQ-056 §8.2, §12.1 (Gültigkeit der Bestätigung), §12.3 (neue Kontofelder bei Kontolöschung), §13.5 (Zustände, Vorschau, 24-Stunden-Frist), §14, der Status von NFR-011 R-40 und das Dateninventar `spec/privacy/02-personal-data-inventory.md` sind nachgezogen.

## Test hooks

- **acceptance-1** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py` + `src/backend/tests/api/test_tenant_export_routes.py`: the upload answers 202 with a pre-check record, the worker's check fills origin, `verified` and members, no tenant exists before the start; vitest `src/frontend/src/test/pages/AdminTenantImportsPage.test.tsx` (preview appears by polling) — pending
- **acceptance-2** — service test: start by the same admin 59 minutes after the step-up imports the stored archive (the upload's storage key is reused, no factors sent). Route registrations: `src/backend/tests/unit/test_route_consumers_check.py:368` counts 917 (list + start; the stale comment at `:232` is corrected); both new routes are absent in light mode (AK-43, `src/backend/tests/api/test_tenant_export_routes.py`); the start route carries the import rate limit (`router.py:213` has it on the upload only); the body-ceiling guards (`tests/unit/guards/test_tenant_import_body_ceiling_names_the_route.py`, `tests/unit/guards/test_proxy_body_limit.py`, `scripts/ci/assert_chart_contracts.sh` from `:555`) stay green unchanged because the upload path does not move — pending
- **acceptance-3** — service tests: start by another platform admin, and start by the same admin 61 minutes after the step-up, both answer the step-up refusal and found no tenant; with fresh factors bound to `archive:<digest>` both succeed, including an account without a password using an e-mailed code bound to the target the preview returned (`TenantImportResponse`, `schemas.py:61-75`, gains the target); the start route declares `STEP_UP_RESPONSES` (`router.py:212`); `src/backend/tests/unit/guards/test_credential_changes_go_through_the_step_up.py` (`:161`) classifies the start route; vitest: the step-up dialog of the start uses the returned target, not a file — pending
- **acceptance-4** — service test: upload by admin A, start by admin B with B's step-up → `tenant_imported` names B as actor, B is the owner when no mapped member is lead with management, the record still names A as uploader (today `actor_user_key=claimed.requested_by_user_key`, `tenant_export_service.py:1019`) — pending
- **acceptance-5** — vitest `src/frontend/src/test/pages/AdminTenantImportsPage.test.tsx` (rows pre-filled from the preview, per-row `IMPORT_MEMBER_NOT_FOUND`) + service test for the start route's row-exact refusal — pending
- **acceptance-6** — service test: the role comes from the start request, never from `members.jsonl` (SEC-003); vitest for the pre-selected role and the pseudonymised hint — pending
- **acceptance-7** — service test: a start refused for an unknown plan or an unmappable row leaves the record pre-checked and startable, founds nothing and audits `refused:<Code>` with the archive hash; the F-15 test that pins these two refusals on `request_import` is rewritten to the start route in the same change — pending
- **acceptance-8** — repository list-method test + service test (a pre-check failed on a corrupt archive is listed with code and entries; a 403/413/step-up refusal creates no record; the record's phase follows validating → writing) + vitest of the list table and the phase display — pending
- **acceptance-9** — unit tests of the hourly sweep (`TenantExportService.expire`): a waiting pre-check untouched for 7 h is not ended by the stale sweep and can still be started; after 24 h the upload is deleted, the record is expired and a start is refused; `delete_finished_before` removes expired and failed pre-checks 30 days after their end — pending
- **acceptance-10** — service + API tests: `GET …/tenant-imports/{import_key}` and the list return the member preview to the confirming admin within the hour and to another admin only after that admin's own step-up for the archive, otherwise no names; the preview is empty on `completed`, `failed` and expired records; `scripts/check_privacy_inventory.py` (guard R6) lists the new account-key fields and the account erasure sets them to `_anonymized` — pending
- **acceptance-11** — i18n completeness + `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte) — betrifft den Abschnitt „Re-run 2026-11-28“; die älteren Läufe stammen vom `feature-consistency-reviewer`.

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

**Korrekturen 2026-11-28 zu den Notizen vom 2026-11-17.** „Refused uploads stay audit-only“ gilt seit der Entscheidung D1 (2026-11-27) nur noch für Ablehnungen vor dem Speichern (Rolle, Größe, Step-up); „reused by the import of the same archive“ ist durch D2 auf eine Stunde und denselben Admin begrenzt. Die Phase „Messwerte“ der Fortschrittsanzeige ist nach F-16 verschoben. „Same-file order with F-12“ ist erledigt (F-12 ist `done`). Verrutschte Anker der Notizen oben: `AdminTenantImportsPage.tsx:113-114` ist `:113-115`, die Zeilenmeldung steht in `:311`, die Rücksprünge in `:366,638`; die Löschung nach 30 Tagen steht in `tenant_export_service.py:1410-1411`; `TenantImportRequest` ist `tenant_export.py:81-107`.

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

### Re-run 2026-11-28

Manueller, rein lesender Durchgang gegen develop `17e1034d2`; Lauf, Auslöser und Vorbehalte wie in `tenant-archive-size-limits.md` (kein Test gelaufen; manueller Durchgang statt Agent, als Workflow-Health-Befund vermerkt). Die Zeilenanker dieses Features wurden nachgelesen; verrutscht war keiner, zwei wurden präzisiert (unten).

**Befunde vom 2026-11-27 — Verbleib.**

1. `src/backend/app/domain/services/step_up_service.py:249` (drift) — entschieden (D2, 2026-11-27): eine Stunde, an denselben Admin gebunden. Präzisierter Anker: der Einmalverbrauch steht in `:694-700` (der Lauf vom 27.11. nannte `:694-698`). acceptance-2 und -3.
2. `project/features/tenant-import-preflight.md:59` (drift) — entschieden (D1, 2026-11-27): Archivfehler erscheinen als fehlgeschlagene Vorprüfung in der Liste. acceptance-6.
3. `src/backend/app/domain/services/tenant_export_service.py:168` (drift) — erledigt durch acceptance-8 und -9 mit ihren Hooks.
4. `src/backend/tests/unit/test_route_consumers_check.py:368` (prior-art) — erledigt: Routenform unten festgelegt, Registrierungen stehen in den Hooks zu acceptance-2 und -3. Präzisierter Anker: der Step-up-Guard nennt `request_import` in `:161`.
5. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:565` (drift) — erledigt: acceptance-9 legt Ablage und Leerung fest, acceptance-10 zieht §13.5 und das Dateninventar nach.
6. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:480` (drift, split-out) — entschieden (2026-11-27): eigenes Feature F-32.
7. `spec/privacy/14-contradiction-register.md:59` (prior-art, proceed) — unverändert richtig.

Der Block vom 2026-11-27, wie er bis zu diesem Lauf im Frontmatter stand:

```yaml
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
```

**Festlegungen dieses Laufs.**

- **Routenform (prior-art, proceed).** Established: Die Body-Grenze hängt am exakten Pfad `TENANT_IMPORT_PATH` (`api/v1/tenant_exports/router.py:42`, `main.py:431-443`, `nginx.conf:98-99`, Chart-Contract ab `scripts/ci/assert_chart_contracts.sh:555`), der Routenzähler steht auf 915 (`test_route_consumers_check.py:368`). Festlegung der Planung: Der Upload bleibt `POST /admin/platform/tenant-imports` (mit Step-up; legt den Vorprüf-Datensatz an und stößt die Hintergrundprüfung an), `GET /admin/platform/tenant-imports/{import_key}` liefert zusätzlich die Vorschau, neu sind `GET /admin/platform/tenant-imports` (Liste) und `POST /admin/platform/tenant-imports/{import_key}/start` (Zuordnung, Plan, bei Bedarf Step-up-Faktoren). Weil der Upload-Pfad bleibt, bewegen sich die vier Schichten der Body-Grenze und ihre drei Guards nicht; der Zähler steigt auf 917, der Step-up-Guard bekommt die Start-Route. Weicht die Umsetzung davon ab, ist der Lauf zu wiederholen.
- **Was beim Start synchron geprüft wird.** Die nach F-15 synchronen Prüfungen „Plan vorhanden“ und „E-Mail → Konto“ wandern mit der Zuordnung vom Upload zum Start; Rolle, Größe und Step-up bleiben am Upload. Established: Die Zuordnung prüft heute Konto, Rolle und Scopes aus dem Antrag (`tenant_export_service.py:965-982`).
- **Gültigkeit der Bestätigung (D2).** Established: Die Step-up-Faktoren sind einmalig und kurzlebig (`step_up_service.py:249`, `:253`, `:694-700`). „Ohne erneuten Step-up“ heißt deshalb: Der Vorprüf-Datensatz hält Zeitpunkt und Konto der Bestätigung; der Start prüft „dasselbe Konto“ und „höchstens eine Stunde“. Die Bindung an das Archiv bleibt (`archive:<Hash>`, REQ-056 §12.1 `:453`), geprüft wird weiterhin vor jedem Parsen, weil der Step-up am Upload vor der Hintergrundprüfung liegt.
- **Ablage der Vorschau (drift, proceed).** Established: `TenantImportRequest` hat weder Quelle noch Mitgliederliste noch Phase (`tenant_export.py:81-107`), das Repository keine Listenmethode (`interfaces/tenant_export_store.py:115-138`). Festlegung der Planung: Quelle (Name, Kurzname) und Mitgliederliste (Archiv-Schlüssel, Anzeigename, Rolle, Scopes) liegen am Import-Datensatz. Die Mitgliederliste wird geleert wie heute `member_grants` (`tenant_export_service.py:1064`, `:1110`), die Quelle bleibt bis zur Löschung nach 30 Tagen (`REQUEST_RETENTION`, `:171`, `:1410-1411`). Anzeigenamen sind personenbezogen; acceptance-10 trägt die Felder in das Dateninventar ein (`spec/privacy/02-personal-data-inventory.md:139` nennt heute nur `requested_by_user_key`).
- **Überschneidung mit F-15 (overlap, proceed).** Begründung für `proceed`: F-15 speichert die Ablehnungsdetails am Datensatz und zeigt sie an der Statuskarte eines Imports; F-17 zeigt denselben Datensatz in der Liste. Eine Quelle, zwei Ansichten. Das gilt auch für die Einträge, die F-32 schreibt: Die Vorgabe „die Vorprüfung zeigt das Ergebnis der Dokumentprüfung“ ist mit acceptance-6 erfüllt, ohne eigenes Kriterium.
- **Phase „Messwerte“ (overlap, split-out F-16).** Das Kriterium 5 vom 2026-11-17 nannte die Phasen prüfen, Dokumente, Messwerte, fertig. Messwerte schreibt erst F-16, das in der entschiedenen Reihenfolge nach F-17 kommt. Die Phase „Messwerte“ ist deshalb nach F-16 acceptance-9 verschoben; acceptance-7 hier ist ohne F-16 prüfbar. Damit hängt F-17 nicht mehr von F-16 ab.

**Umgesetzte Edits aus dem Lauf vom 2026-11-27** (alle fünf): Routenform festgelegt und Registrierungen als Hooks benannt; neuer Zustand in Sweep und Purge (acceptance-8, -9); Ablage und Leerung der Vorschau (acceptance-9); Kriterium 5 geteilt (acceptance-6, -7, -9); Dokumentprüfung hat mit F-32 einen Besitzer. Zusätzlich: Kriterium 1 geteilt in Vorschau (acceptance-1), Start ohne zweiten Step-up (acceptance-2) und erneuter Step-up (acceptance-3).

**Verhältnis der vier Features (R-19).** F-17 setzt F-15 voraus (Hintergrundprüfung, Detailfeld) und zeigt die Ergebnisse von F-32; F-16 setzt F-17 voraus (Phase „Messwerte“ in der Liste, Wertnachweis über die Vorprüfung). Die Reihenfolge F-15 → F-32 → F-17 → F-16 trägt.

**Ergebnis:** D1 und D2 sind entschieden, kein ungelöster Befund; F-17 ist `ready`.

### Agentenlauf 2026-11-28

Lauf des `feature-consistency-reviewer` (`agent_version: feature-consistency-reviewer@unknown`) am 2026-11-28 gegen den Stand `3a8c33e43`, von der Hauptsitzung gestartet; die Befunde stehen sinngemäß im Frontmatter. Damit ist der im manuellen Durchgang vermerkte Workflow-Health-Befund erledigt. Die Einarbeitung unten stammt vom selben Subagenten wie der manuelle Durchgang; die zitierten Stellen wurden nachgelesen, ein Test lief nicht. Nach dieser Einarbeitung lässt die Hauptsitzung den Agenten erneut laufen.

Der Block des manuellen Durchgangs vom 2026-11-28, wie er bis zu diesem Lauf im Frontmatter stand:

```yaml
consistency_check:
  performed_at: 2026-11-28
  agent_version: manual-2026-11-28
  findings:
    - kind: drift
      target: src/backend/app/domain/services/step_up_service.py:249
      resolution: proceed
      evidence: "REAUTH_TOKEN_TTL_SECONDS = 300 (:249), CODE_TTL_SECONDS = 600 (:253), Einmalverbrauch über _reauth_store.consume / _code_store.consume (:694-700); REQ-056 §12.1 (:453) 'geprüft vor jedem Parsen'. D2 am 2026-11-27 entschieden (1 Stunde, derselbe Admin): acceptance-2 und -3."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:782
      resolution: proceed
      evidence: "Heute Ablehnung vor dem Speichern (:782-786), Datensatz erst danach (:788). D1 am 2026-11-27 entschieden: Archivfehler stehen als fehlgeschlagene Vorprüfung in der Liste, nur Ablehnungen vor dem Speichern bleiben im Audit — acceptance-6."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:168
      resolution: proceed
      evidence: "STALE_AFTER = timedelta(hours=6) (:168); list_stale_active nimmt 'pending/validating/running' (interfaces/tenant_export_store.py:135-138), delete_finished_before nur 'completed/failed' (:131-133). acceptance-8 und -9 mit ihren Hooks decken den wartenden und den abgelaufenen Zustand in beiden ab."
    - kind: prior-art
      target: src/backend/tests/unit/test_route_consumers_check.py:368
      resolution: proceed
      evidence: "'assert len(checker.collect_operations(app)) == 915'; Step-up-Guard guards/test_credential_changes_go_through_the_step_up.py:161; Body-Grenze am exakten Pfad TENANT_IMPORT_PATH (api/v1/tenant_exports/router.py:42, main.py:431-443, nginx.conf:98-99, scripts/ci/assert_chart_contracts.sh ab :555). Routenform festgelegt (Consistency notes), Registrierungen als Hooks benannt."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:565
      resolution: proceed
      evidence: "'report: dict[str, int] = {}  # Anzahl je Collection; keine Inhalte'; §13.5 (:572) 'wird nach Abschluss oder Fehlschlag sofort gelöscht'; spec/privacy/02-personal-data-inventory.md:139 führt nur requested_by_user_key; Muster: member_grants wird am Ende geleert (tenant_export_service.py:1064, :1110). acceptance-9 legt Ablage und Leerung fest, acceptance-10 zieht die Spec nach."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:480
      resolution: split-out F-32
      evidence: "§12.4 'Schema-Validierung jedes Dokuments gegen das Domänenmodell (422)' gegen tenant_export_service.py:52-53; Betreiberentscheidung 2026-11-27: eigenes Feature F-32 (tenant-import-document-validation.md)."
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_export_service.py:954
      resolution: proceed
      evidence: "_resolve_member_mapping (:954-993) nimmt {email, role, admin_scopes} mit bestätigter Rolle und lehnt zeilengenau mit IMPORT_MEMBER_NOT_FOUND ab; die Seite zeigt es (AdminTenantImportsPage.tsx:311). Delta: Vorbelegung aus der Vorprüfung statt Abtippen der Schlüssel (:113-115)."
    - kind: prior-art
      target: spec/privacy/14-contradiction-register.md:59
      resolution: proceed
      evidence: "W-38 korrigiert NFR-011 R-40 von 'Nicht implementiert' (NFR-011:151) auf umgesetzt; wer zuerst mergt, erledigt die Korrektur (acceptance-10)."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "acceptance-6 zeigt in der Liste dieselben Ablehnungsdetails, die F-15 acceptance-6 am Datensatz speichert und an der Statuskarte zeigt (auch die Einträge aus F-32); Begründung in den Consistency notes (Re-run 2026-11-28)."
    - kind: overlap
      target: F-16
      resolution: split-out F-16
      evidence: "Das Kriterium 5 vom 2026-11-17 nannte die Phase 'Messwerte', die erst F-16 schreibt; die Phase ist nach F-16 acceptance-9 verschoben, acceptance-7 hier nennt nur Prüfen und Datensätze."
```

**Befunde und Einarbeitung.**

- **Step-up-Ziel beim Start (drift, proceed).** Established: `archiveStepUpTarget` berechnet das Ziel aus der Datei (`tenantImport.ts:44-52`); `TenantImportResponse` (`schemas.py:61-75`) trägt keinen Hash. Ein Konto ohne Passwort könnte beim Start ohne Datei weder Code noch frische Anmeldung an das Archiv binden. Festlegung: Die Vorschau-Antwort nennt das Step-up-Ziel (`archive:` plus die ersten 32 Hex-Zeichen, dieselbe Angabe, die heute der Browser bildet); acceptance-3.
- **Handelnder Admin (drift, proceed).** Established: Der Lauf nimmt `requested_by_user_key` als Akteur (`tenant_export_service.py:1019`), und der Akteur wird Eigentümer, wenn kein zugeordnetes Mitglied Leitung mit Verwaltung hat (`_owner_of`, `:1367-1380`). Vorgabe der Hauptsitzung: Der startende Admin ist Akteur und Ersatz-Eigentümer, der Hochladende bleibt am Datensatz; acceptance-4.
- **Ablehnungen der Start-Route (drift, proceed).** acceptance-7 legt Antwort, Zustand und Audit fest. Established: Der Audit-Eintrag `refused:<Code>` mit dem Hash des Archivs existiert für solche Ablehnungen (`:782-786`, `_audit_import_refused` `:823-833`).
- **Wer die Mitgliederliste liest (drift, proceed).** Established: `get_import` prüft nur „Plattform-Admin in Person“ (`:835-845`). Vorgabe der Hauptsitzung: nur der Admin, der die Vorprüfung bestätigt hat, innerhalb der Frist; andere sehen den Status ohne Namen. Festlegung der Planung dazu: „gültige Bestätigung für dieses Archiv“ schließt einen anderen Admin nach eigenem Step-up ein, denn D2 erlaubt ihm den Start, und ohne die Liste könnte er nicht zuordnen (siehe „Offene Punkte“). Neue Kontofelder (wer bestätigt, wer startet) brauchen den Guard R6 der Kontolöschung (`scripts/check_privacy_inventory.py:54`, REQ-056 §12.3), nicht nur das Dateninventar; acceptance-10 und -11.
- **Audit der Ablehnungen vor dem Speichern (drift, proceed).** Wie in F-15: Rolle, Größe und Step-up schreiben heute keinen Import-Audit-Eintrag. acceptance-8 verspricht nur, dass sie nicht in der Liste erscheinen.
- **Überschneidung mit F-15 (overlap, proceed).** Begründung für `proceed`: F-15 prüft „Plan vorhanden“ und „E-Mail → Konto“ an der Upload-Antwort, weil Zuordnung und Plan dort noch mit dem Upload kommen. F-17 verschiebt beide an die Start-Route und nimmt die Prüfungen mit; der Upload trägt danach weder Zuordnung noch Plan. Das ist ein geplanter Ersatz in fester Reihenfolge, kein doppelter Umfang. Der F-15-Test zu `request_import` wird hier umgeschrieben (Hook zu acceptance-7).
- **Registrierungen (prior-art, proceed).** Ratenlimit, `STEP_UP_RESPONSES`, Light-Modus-Ausschluss (AK-43) und Routenzähler 915 → 917 stehen in den Hooks zu acceptance-2 und -3.

**Umnummerierung.** Durch die neuen Kriterien verschieben sich die Nummern gegenüber dem Stand `3a8c33e43`: Zuordnung 4 → 5, Rolle 5 → 6, Liste 6 und Phase 7 → 8, Ablauf 8 und 30-Tage-Löschung → 9, Leerung der Mitgliederliste 9 → 10, Doku 10 → 11. Neu sind 4 (handelnder Admin) und 7 (Ablehnung am Start). Verweise in F-15, F-32 und F-16 auf „F-17 acceptance-6“ (Liste) und „acceptance-7“ (Phase) meinen jetzt acceptance-8.

**Ergebnis:** alle sieben Befunde eingearbeitet; F-17 ist `ready`, vorbehaltlich des erneuten Agentenlaufs. Mit elf Kriterien liegt das Feature über der Empfehlung der Feature-Spec (mehr als zehn legt eine Teilung nahe); eine Teilung in „Vorprüfung“ und „Importliste“ wäre möglich, ist aber eine Betreiberentscheidung.

## Risks

- Ein gespeichertes, vorgeprüftes Archiv (bis ~500 MiB) belegt bis zu 24 Stunden Objektspeicher.
- Die Bestätigung gilt eine Stunde ab dem Step-up. Dauert die Hintergrundprüfung eines großen Archivs lange oder ordnet der Admin viele Mitglieder zu, ist ein zweiter Step-up nötig.
- Zuordnung und Plan liegen innerhalb dieser Stunde hinter keinem Step-up: Wer in dieser Zeit die Sitzung des Admins übernimmt, bestimmt, wer im neuen Garten Leitung mit Verwaltung wird. Heute bindet der Step-up den ganzen Antrag einschließlich Zuordnung an eine frische Bestätigung.
- Anzeigenamen der Archiv-Mitglieder liegen bis zum Ende des Imports bzw. bis zu 24 Stunden am Import-Datensatz, in einer Collection, die laut Spec bisher keine Inhalte trägt. Sicht und Leerung sind Kriterium (acceptance-10); die Datenschutz-Lane zum Archiv berührt dieselbe Zuordnungsfläche (TA-756, `spec/privacy/10-testing-and-acceptance.md:334`).
- Der Ablauf über die API ändert sich: Zuordnung und Plan gehen nicht mehr mit dem Upload, sondern mit dem Start. Wer die Route direkt nutzt, muss umstellen; das Runbook nennt es (acceptance-11).
- Elf Kriterien in einem Feature; der Umfang ist der größte des Sprints.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R5–R8, R15–R17; R15 und R16 am 2026-11-27 präzisiert)
- Setzt F-15 voraus; zeigt die Ergebnisse von F-32; F-16 ergänzt die Phase „Messwerte“ (bis 2026-11-28 stand sie hier in Kriterium 5)

## Betreiberentscheidungen 2026-11-27

- Es gibt nur **eine** Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv laufen in einer eigenen Lane.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`).
- Ein Speicherlimit des Workers von rund 2 GiB ist akzeptabel.
- **D1:** Archivfehler erscheinen als fehlgeschlagene Vorprüfung in der Importliste; „nur im Audit“ gilt nur noch für Ablehnungen vor dem Speichern (Rolle, Größe, Step-up).
- **D2:** Die Step-up-Bestätigung der Vorprüfung gilt eine Stunde für den anschließenden Import und ist an denselben Admin gebunden; danach oder für einen anderen Admin ist ein neuer Step-up nötig.
- **Dokumentvalidierung nach REQ-056 §12.4:** eigenes kleines Feature in R-19 (F-32, `tenant-import-document-validation.md`).
- Sprint 5 enthält nur R-19; Reihenfolge der Umsetzung F-15 → F-32 → F-17 → F-16.

## Betreiberentscheidungen 2026-11-28

Vorgaben der Hauptsitzung zur Einarbeitung des Agentenlaufs:

- **Handelnder Admin ist, wer startet.** Er ist Audit-Akteur und Ersatz-Eigentümer; der Hochladende bleibt als Hochladender am Datensatz (acceptance-4).
- **Die Mitgliederliste sieht nur der Admin, der bestätigt hat**, innerhalb der Frist; andere sehen den Status ohne Namen (acceptance-10).
- Aus der Runde vom 2026-11-28 gilt für den ganzen Sprint: Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

F-17 war auf D1 und D2 blockiert. **Stand 2026-11-28: D1, D2 und die Dokumentvalidierung sind entschieden, die Blockade ist aufgehoben.**

- **D1 — Erscheinen Archivfehler als fehlgeschlagene Vorprüfung in der Liste?** Heute wird ein Upload vor dem Speichern abgelehnt (`tenant_export_service.py:782-786`), der Datensatz entsteht erst danach (`:788`); die Entscheidung vom 2026-11-17 lautet „abgelehnte Uploads erscheinen nur im Audit“. Mit F-15 Kriterium 4 prüft nur noch der Worker, Upload und Datensatz existieren also, bevor ein Archivfehler bekannt ist.
  - **Ja — „nur im Audit“ gilt nur für Ablehnungen vor dem Speichern (Rolle, Größe, Step-up):** Archivfehler stehen als fehlgeschlagene Vorprüfung in der Importliste; der Admin sieht den Grund dort.
  - **Nein — auch Archivfehler nur im Audit:** Mit der Prüfung im Worker ist das laut Bericht nicht haltbar, weil Upload und Datensatz dann schon existieren; der Datensatz müsste nachträglich entfernt werden.
  - **Entschieden 2026-11-27: Ja.** Archivfehler erscheinen als fehlgeschlagene Vorprüfung in der Importliste; „nur im Audit“ gilt nur noch für Ablehnungen vor dem Speichern (acceptance-6).
- **D2 — Wie lange gilt die Step-up-Bestätigung der Vorprüfung, und ist sie an denselben Admin gebunden?** Heute sind die Faktoren einmalig und kurzlebig (`step_up_service.py:249` 300 s, `:253` 600 s, Verbrauch `:694-698`); REQ-056 §12.1 (`:453`) prüft vor jedem Parsen. „Wiederverwenden“ heißt deshalb: eine am Vorprüf-Datensatz gespeicherte Bestätigung.
  - **Bis zum 24-h-Ablauf der Vorprüfung:** Ein Step-up genügt für Vorprüfung und Import; die Bestätigung gilt bis zu 24 h statt wenige Minuten.
  - **Kürzer als 24 h:** Liegt zwischen Vorprüfung und Import mehr als die Frist, ist ein zweiter Step-up nötig.
  - **An denselben Admin gebunden:** Nur wer vorgeprüft hat, importiert ohne neuen Step-up; ein zweiter Admin bestätigt selbst.
  - **Nicht gebunden:** Jeder Plattform-Admin kann das vorgeprüfte Archiv mit der fremden Bestätigung importieren.
  - **Entschieden 2026-11-27: eine Stunde, an denselben Admin gebunden.** Danach oder für einen anderen Admin ist ein neuer Step-up nötig (acceptance-2, -3).
- **Dokumentvalidierung nach REQ-056 §12.4 — wer besitzt sie?** Heute prüft der Import nur Besitz und Verweise (`tenant_import_engine.py:167-183`); die Schema-Validierung jedes Dokuments ist ausdrücklich nicht Teil der Lieferung (`tenant_export_service.py:52-53`), obwohl §12.4 (`REQ-056:480`) sie verspricht. Kein Feature von R-19 nennt sie. Blockiert F-17 nicht.
  - **Eigenes kleines Feature in R-19:** Die Prüfung kommt in den Worker (`_verified_archive`), die Vorprüfung zeigt das Ergebnis; ein manipuliertes Enum wird abgelehnt statt geschrieben.
  - **Dokumentierter Ausschluss mit Korrektur von §12.4:** Unverifizierte und ältere Archive können weiter Dokumente einspielen, die spätere Lesezugriffe brechen; signierte Archive der eigenen Installation sind nicht betroffen.
  - **Entschieden 2026-11-27: eigenes kleines Feature in R-19** — F-32 (`tenant-import-document-validation.md`).

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-17. Diese Festlegungen stammen aus der Planung und sind vor dem Start von F-17 widerrufbar:

- **Routenform.** Upload-Pfad bleibt, neu sind Liste und Start (siehe Consistency notes, Re-run 2026-11-28). Eine andere Form verschiebt die Body-Grenze auf vier Schichten und drei Guards.
- **Ablage der Mitgliedervorschau am Import-Datensatz**, geleert am Ende des Imports bzw. nach 24 Stunden. Die Alternative, die Vorschau bei jedem Aufruf aus dem gespeicherten Archiv zu lesen, hieße, dass das Backend das Archiv wieder selbst öffnet, was F-15 abschafft.
- **Mitgliederliste für einen zweiten Admin.** Die Vorgabe lautet „nur der Admin, der bestätigt hat“. acceptance-10 liest das als „ein Admin mit gültiger Bestätigung für dieses Archiv“ und schließt damit einen anderen Admin nach eigenem Step-up ein, weil D2 ihm den Start erlaubt und er ohne die Liste nicht zuordnen kann. Soll der zweite Admin die Namen nie sehen, kann er faktisch nicht starten; dann wäre D2 auf denselben Admin zu verengen.
- **Sicht nach Ablauf der Stunde.** Nach einer Stunde sieht auch der bestätigende Admin die Namen erst nach einem neuen Step-up wieder. Die Vorgabe nannte „Stunde/24 h“; gewählt ist die strengere Lesart.
- **Audit für Rolle, Größe, Step-up:** siehe „Offene Punkte“ in `tenant-archive-size-limits.md`.
