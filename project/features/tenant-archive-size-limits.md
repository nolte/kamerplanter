---
id: F-15
title: Archivgrößen bis ~500 MiB mit klarer Grenze
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-28
  agent_version: manual-2026-11-28
  findings:
    - kind: prior-art
      target: helm/kamerplanter/values.yaml:2468
      resolution: proceed
      evidence: "backend-tmp und celery-worker-tmp: 'type: emptyDir, medium: Memory, sizeLimit: 64Mi' (:2468-2486); limits.memory 2Gi für backend (:1022) und celery-worker (:1662); UPLOAD_SPOOL_BUDGET_MB 'max 52 …' (:926). Die Deltas stehen in acceptance-1, -2 und -7; backend-tmp auf Disk ist am 2026-11-27 entschieden."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:384
      resolution: proceed
      evidence: "§8.4 Schritt 6 'Geprüft wird am Antrag (synchrone Ablehnung, nichts gespeichert)', AK-34 (:680) '422 … nichts geschrieben', AK-46 (:687) 'speichert keinen Upload und auditiert refused:<Code>' gegen acceptance-5/-6; Option B am 2026-11-27 entschieden, acceptance-8 zieht die Stellen nach."
    - kind: prior-art
      target: src/backend/app/domain/models/tenant_export.py:40
      resolution: proceed
      evidence: "TenantExportFailureReason enthält 'too_large'; tenant_export_service.py:511-513 beendet den Export damit; AK-44 (REQ-056:710) 'umgesetzt'. Delta nur: min(Kontingent + 10 %, Importgrenze), unbegrenztes Kontingent (_size_limit :486-490 gibt None) und ENOSPC (heute internal_error, :514-518)."
    - kind: drift
      target: helm/kamerplanter/values.yaml:929
      resolution: proceed
      evidence: "TENANT_IMPORT_MAX_UPLOAD_MB steht nur unter controllers.backend (:929; einziger Treffer im Chart), der Export läuft im Worker (tasks/tenant_export_tasks.py:31-32); acceptance-3 und sein Hook verlangen dieselbe Grenze im Worker."
    - kind: prior-art
      target: src/backend/app/domain/engines/tenant_export_engine.py:1003
      resolution: proceed
      evidence: "MAX_UNCOMPRESSED_BYTES 1 GiB (:1003), MAX_DOCUMENT_BYTES 128 MiB (:1007), MAX_ROWS 1 000 000 (:1012); acceptance-1 nennt die Zusammensetzung des 500-MiB-Archivs."
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_export_service.py:1013
      resolution: proceed
      evidence: "run_import ruft '_verified_archive(buffer)' (:1013) und speichert den Code über _fail_import (:1072-1112); acceptance-5 entfernt nur den Aufruf im Antrag (:774), acceptance-6 ergänzt die Details am Datensatz (heute nur fehlende Katalogeinträge, :1105)."
    - kind: prior-art
      target: scripts/ci/assert_chart_contracts.sh:555
      resolution: proceed
      evidence: "Block '#2138 — the tenant import's own body limit' (ab :555) rendert das Chart und prüft die Importgrenze; der Hook zu acceptance-7 erweitert ihn um /tmp und Spool-Budget."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "acceptance-6 (Ablehnungsdetails an Datensatz und Statuskarte) und F-17 acceptance-6 (fehlgeschlagene Vorprüfung in der Importliste) zeigen dieselben Details; Begründung in den Consistency notes (Re-run 2026-11-28)."
    - kind: overlap
      target: F-32
      resolution: proceed
      evidence: "F-32 schreibt seine abgelehnten Dokumente in dasselbe Detailfeld, das acceptance-6 einführt; Begründung in den Consistency notes (Re-run 2026-11-28)."
---

## Description

Ein Mandanten-Archiv lässt sich heute mit den mitgelieferten Einstellungen nur
bis rund 50 MiB importieren, obwohl die Importgrenze auf 512 MiB steht; größere
Exporte und Importe scheitern mit einem unverständlichen internen Fehler, wenn
`/tmp` oder der Arbeitsspeicher volllaufen. Ein Export kann außerdem größer
werden, als ein Import je annehmen würde.

Nach dieser Änderung kommen Archive bis etwa 500 MiB mit den mitgelieferten
Helm-Werten durch. Ein Export bricht spätestens an der Importgrenze ab, sodass
jedes exportierte Archiv auch wieder importierbar ist. Was zu groß ist, wird
mit einer Meldung abgelehnt, die die Grenze nennt.

Beim Hochladen prüft das Backend nur noch, was ohne Öffnen des Archivs
feststeht: Berechtigung, Größe, Bestätigung (Step-up), ob der Plan existiert
und ob die genannten E-Mail-Adressen zu aktiven Konten gehören. Das Archiv
selbst prüft ausschließlich der Hintergrundprozess (Worker). Ist es
fehlerhaft, endet der Import als fehlgeschlagen, und die Statusanzeige nennt
den Grund und die betroffenen Einträge. Der Upload liegt dabei auf Disk, nicht
im Arbeitsspeicher des Backends.

## Acceptance criteria

- [ ] **acceptance-1** Mit den mitgelieferten Helm-Werten gelingen Export und anschließender Import eines Archivs von rund 500 MiB, das überwiegend aus Fotos besteht (Datensätze unter 128 MiB, entpackt unter 1 GiB, höchstens 1 000 000 Zeilen); der importierte Garten ist danach aktiv, und weder Backend noch Worker werden dabei wegen Speichermangels beendet.
- [ ] **acceptance-2** Mit den mitgelieferten Werten wird ein Archiv von 100 MiB angenommen und ein Upload über der Importgrenze (512 MiB) mit 413 abgelehnt; die Meldung nennt die Grenze.
- [ ] **acceptance-3** Ein Export bricht spätestens an der Importgrenze ab (bzw. am Kontingent + 10 %, falls das kleiner ist) und endet mit dem Grund „zu groß“ — auch bei unbegrenztem Speicherkontingent; der Worker verwendet dabei dieselbe Importgrenze wie das Backend.
- [ ] **acceptance-4** Läuft `/tmp` des Workers beim Zusammenstellen eines Exports voll, endet der Export mit dem Grund „zu groß“ statt mit einem internen Fehler.
- [ ] **acceptance-5** Die Upload-Antwort lehnt nur noch ab, was ohne Öffnen des Archivs feststeht — fehlende Plattform-Admin-Rolle, Größe, Step-up, unbekannter Plan, eine Zuordnung, die kein aktives Konto oder keine gültige Rolle nennt (zeilengenau) —, speichert dann nichts und vermerkt die Ablehnung im Audit; jedes andere Archiv wird mit 202 angenommen, auch ein fehlerhaftes.
- [ ] **acceptance-6** Scheitert die Hintergrundprüfung eines angenommenen Archivs, endet der Import als fehlgeschlagen, ohne dass ein Garten entsteht; Statusabfrage und Statuskarte nennen den Code und die betroffenen Einträge (höchstens 200, keine Inhalte), und das hochgeladene Archiv ist gelöscht.
- [ ] **acceptance-7** Die mitgelieferten Helm-Werte legen `/tmp` des Backends auf Disk statt in den Arbeitsspeicher, mit Platz für einen Upload an der Importgrenze; das Speicherlimit des Backends bleibt bei 2 GiB.
- [ ] **acceptance-8** Runbook (DE + EN, Abschnitte „Wenn der Import ablehnt“ und „Archivgröße und /tmp“), der Kommentar in `values.yaml` und REQ-056 (§8.3, §8.4 Schritt 6, §13.5, §13.6, AK-34, AK-44, AK-46, AK-49) beschreiben die neue Grenze, die Exportregel, die Aufteilung in synchrone und asynchrone Prüfung und die gemeinsam anzuhebenden Ressourcen.

## Test hooks

- **acceptance-1** — manual only: a new `workflow_dispatch` workflow (never per pull request, never nightly; operator decision 2026-11-27) renders the chart with its default values, exports a synthetic photo-dominated tenant of ~500 MiB and imports the archive again, asserting `completed`, an `active` tenant and no restarted or OOM-killed pod; the source tenant has no own species or is deleted first (runbook `docs/de/deployment/tenant-export-import.md:136-137`); the run once uploads through the admin page to cover the browser-side hash (`src/frontend/src/utils/tenantImport.ts:47`) — pending
- **acceptance-2** — `src/backend/tests/api/test_tenant_import_body_ceiling.py` extended (100 MiB passes the ceiling, a body above the limit answers 413 naming it, `exceptions.py:1016-1030`) plus the chart contract of acceptance-7 (the rendered default spool budget no longer lowers the ceiling) — pending
- **acceptance-3** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: limit = min(quota + 10 %, import limit), unlimited quota → import limit; `scripts/ci/assert_chart_contracts.sh`: the worker's rendered `TENANT_IMPORT_MAX_UPLOAD_MB` equals the backend's — pending
- **acceptance-4** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: `OSError(ENOSPC)` while the archive is assembled ends the request `failed`/`too_large` — pending
- **acceptance-5** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: `request_import` never calls the archive reader (spy on `read_tenant_archive`); each synchronous refusal stores no upload and no record and audits `refused:<Code>`; a corrupt ZIP answers 202; `src/backend/tests/unit/guards/test_credential_changes_go_through_the_step_up.py` (entry at `:161`) stays green — pending
- **acceptance-6** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: `run_import` on a corrupt archive, on missing catalogue entries and on a mapped member key the archive does not hold ends `failed` with code and at most 200 entries, upload deleted, no tenant; `src/backend/tests/integration/test_tenant_export_roundtrip.py` (AK-34 case read from the record); vitest `src/frontend/src/test/components/TenantImportStatusCard.test.tsx` (code and entries shown) — pending
- **acceptance-7** — `scripts/ci/assert_chart_contracts.sh` (block starting at `:555`): with default values the backend's `/tmp` volume is not `medium: Memory`, its size and `UPLOAD_SPOOL_BUDGET_MB` hold one upload at the import limit, `limits.memory` of the backend is `2Gi` — pending
- **acceptance-8** — `mkdocs build --strict` + spec diff review (REQ-056 sections and AKs named in the criterion, runbook DE/EN, `helm/kamerplanter/values.yaml:109-130`) — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte) — betrifft den Abschnitt „Re-run 2026-11-28“; die älteren Läufe stammen vom `feature-consistency-reviewer`.

**Upload ceiling prior art (proceed).** Established: the import ceiling of
512 MiB (`settings.py:441`, `main.py:427-431`) is clamped at start to
`UPLOAD_SPOOL_BUDGET_MB=52` (`settings.py:1311`, `values.yaml:122-123,926`);
the 413 response naming the size exists (`exceptions.py:1016-1030`) and the
edge already allows 513m (`nginx.conf:84-85`). The real gap of criterion 1 is
the shipped defaults (spool 52, backend/worker tmp 64Mi at
`values.yaml:2410-2428`, memory).

**Runbook prior art (proceed).** Established: the runbook section
"Archivgröße und /tmp" (`docs/de/deployment/tenant-export-import.md:151-164`,
EN mirror) already lists the resources; criterion 5 updates it to the new
defaults.

**Export ceiling vs. import limit (drift, proceed).** Established: the export
stops at effective storage quota + 10 % (`tenant_export_service.py:486-490`),
up to ~2.2 GiB with the default quota, and a worker `/tmp` overflow ends as
`internal_error` (`:503,514-518`). Operator decision 2026-11-17: the export
stops at min(quota + 10 %, import limit), and `TenantExportFailureReason`
(`tenant_export.py:40`) gains `too_large`; REQ-056 §8.3 is amended.

**In-memory verification (prior-art, proceed).** Established: the archive is
held in memory while verified (`tenant_export_engine.py:1000-1003`, up to
1 GiB uncompressed), in the backend request (`tenant_export_service.py:774`)
and again in the worker (`:1006`). Operator decision 2026-11-17: only the
worker verifies (memory limit ~2 GiB); the backend streams the upload to
storage (criterion 4).

**Korrekturen 2026-11-28 zu den Notizen vom 2026-11-17.** Der Grund `too_large` existiert bereits (`tenant_export.py:40`, `tenant_export_service.py:511-513`); „gains `too_large`“ oben ist überholt, offen sind nur die Grenze min(Kontingent + 10 %, Importgrenze) und ENOSPC. Das Speicherlimit des Workers steht bereits auf 2 Gi (`helm/kamerplanter/values.yaml:1662`) und wächst nicht weiter. Verrutschte Anker der Notizen oben: `settings.py:441` und `:1311` sind `src/backend/app/config/settings.py:441` und `:1315`; `main.py:427-431` ist `:431-443`; `nginx.conf:84-85` ist `src/frontend/nginx.conf:98-99`; `values.yaml:2410-2428` ist `:2468-2486`.

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`. Triggers: develop moved on since 2026-11-17 (F-19, F-20 and F-12 landed) and the operator decisions of 2026-11-27. The frontmatter holds the six findings of this run; the four findings of 2026-11-17 (`feature-consistency-reviewer@1004fe514`) are listed below with their fate. No test was run; every statement comes from reading code and specs. Line references into this file are those of `cc8531492`, before this section was added. The reviewer codes a contradiction as `drift` and "adjust" / "block" as `revisit-after <event>`; the resolutions are proposals, the operator decides. The canonical feature spec (`spec/project/feature/`, `spec/.spec-config.yml`) is not in the repository; the run used the vocabulary fixed in the agent prompt. Health of the run: 17 criteria checked (5 + 6 + 6), none deferred, no surface without a hit. No finding is `overlap` or `duplication`, so the formal `draft → ready` lock does not apply; the `revisit-after` items are preconditions in substance.

**Findings of 2026-11-17 — fate.**

1. `src/backend/app/common/body_limit.py:35` (prior-art, proceed) — still true. Moved: `main.py:427-431` → `:431-443`, `settings.py:1311` → `:1315`, `nginx.conf:84-85` → `:98-99`. Unchanged: `settings.py:441`, `values.yaml:122-123,926`, `exceptions.py:1016-1030`.
2. `docs/de/deployment/tenant-export-import.md:151` (prior-art, proceed) — still true (`:151-164`); the line "etwa 51 MiB" is at `:155`.
3. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:370` (drift, proceed) — moved to `:371` (size rule) and `:373` (upload limit). Service `:486-490`, `:503`, `:514-518` and `_SPOOL_BYTES` `:162` still true. **Partly obsolete:** "new reason too_large" is wrong, the reason exists (`tenant_export.py:40`; `tenant_export_service.py:511-513`; AK-44 `REQ-056:710` "umgesetzt"). The note above ("gains `too_large`") is to be corrected when the feature is promoted.
4. `src/backend/app/domain/engines/tenant_export_engine.py:1000` (prior-art, proceed) — still true (`:1000-1003`, `_assemble` `:1263,1294`, service `:774`, `:1006-1013`). The worker check already exists (`run_import` `:1013`), so criterion 4 only removes the backend call.

The body note `values.yaml:2410-2428` (tmp 64Mi) moved to `:2468-2486`.

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@1004fe514
  findings:
    - kind: prior-art
      target: src/backend/app/common/body_limit.py:35
      resolution: proceed
      evidence: "TENANT_IMPORT_MAX_UPLOAD_MB=512 (settings.py:441, main.py:427-431) is clamped at start to UPLOAD_SPOOL_BUDGET_MB=52 (settings.py:1311; values.yaml:122-123,926); 413 with the size exists (exceptions.py:1016-1030); edge already 513m (nginx.conf:84-85, _tenant_import_ingress.tpl)."
    - kind: prior-art
      target: docs/de/deployment/tenant-export-import.md:151
      resolution: proceed
      evidence: "Runbook section 'Archivgröße und /tmp' (DE+EN, :151-164) already names spool budget, backend /tmp, memory, worker /tmp; values.yaml:119-130 repeats it."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:370
      resolution: proceed
      evidence: "Export limit is effective storage quota + 10 % (service :486-490; default 2048 MiB) while import stops at ~500 MiB; worker /tmp overflow ends internal_error (service :503,514-518, _SPOOL_BYTES 32 MiB :162); operator decision: export stops at min(quota+10 %, import limit), new reason too_large."
    - kind: prior-art
      target: src/backend/app/domain/engines/tenant_export_engine.py:1000
      resolution: proceed
      evidence: "The archive is held in memory while verified (MAX_UNCOMPRESSED_BYTES 1 GiB; _assemble :1263,1294), in the backend request (service :774) and again in the worker (:1006); operator decision: verify only in the worker."
```

**New findings.**

- **Worker limit already at 2 GiB (prior-art, `helm/kamerplanter/values.yaml:1662`).** `celery-worker` and `backend` both have `limits.memory: 2Gi` (`:1662`, `:1022`); `backend-tmp` and `celery-worker-tmp` are `medium: Memory, sizeLimit: 64Mi` (`:2468-2482`). Open are only the tmp sizes and the spool budget, and a memory-backed `/tmp` counts against the same limit. Criteria 1 and 4 should name these real deltas.
- **Synchronous refusals (drift, `REQ-056:384`).** §8.4 step 6 checks at the request ("synchrone Ablehnung, nichts gespeichert"), AK-46 (`:687`) stores no upload and audits `refused:<Code>`, AK-34 (`:680`) answers 422 with nothing written; the service does this in `request_import` (`:773-786`). Verifying only in the worker turns synchronous 422/409 answers into asynchronous `failed` states, and criterion 5 amends only §8.3. See the open operator decision on criterion 4 below.
- **`too_large` exists (prior-art, proceed, `tenant_export.py:40`).** The delta is only `min(quota + 10 %, import limit)` and ENOSPC → `too_large`.
- **The worker does not know the chart's import limit (drift, `values.yaml:926`).** `UPLOAD_SPOOL_BUDGET_MB` (`:926`) and `TENANT_IMPORT_MAX_UPLOAD_MB` (`:929`) are set only under `controllers.backend`; the export runs in the worker (`tasks/tenant_export_tasks.py:31-40`), and `_size_limit` (`:486-490`) returns `None` for an unlimited quota. The worker sees only the settings default 512, neither the chart value nor the spool budget, so "every exported archive can be imported" does not hold safely. The test hook of criterion 3 should pin that the worker knows the same import limit.
- **Test hook 1 contradicts the operator decision (drift, this file `:57` against `:105`).** The hook says "(CI lane)", the decision says manual only (`workflow_dispatch`). A chart-contract block exists (`scripts/ci/assert_chart_contracts.sh:555-591`) and can carry the permanent check; without one the default values drift unnoticed.
- **Composition of the 500 MiB archive (prior-art, `tenant_export_engine.py:1003`).** `MAX_UNCOMPRESSED_BYTES` 1 GiB (`:1003`), `MAX_DOCUMENT_BYTES` 128 MiB (`:1007`), `MAX_ROWS` 1 000 000 (`:1012`); `_with_stored_bodies` holds objects twice (service `:1286-1311`); the browser hashes with `subtle.digest("SHA-256", await file.arrayBuffer())` (`src/frontend/src/utils/tenantImport.ts:47`). A 500 MiB archive passes only when photos dominate it; the worker's memory need and the hash in the browser are not named. Criterion 1 should define the composition.

**Criterion by criterion.**

- **Criterion 2** is met except for the new figure (`RequestBodyTooLargeError` names the limit).
- **Criterion 3** is testable as a unit test. Limit: an OOM kill caused by the memory-backed `/tmp` still ends as `internal_error` after 6 h (stale sweep, service `:1402-1405`); that belongs in the risks.
- **Criterion 4** is the critical point (proposal: adjust). Four things hang on the synchronous archive check today: the member mapping (`old_key in known`, service `:962-968`), the quota check, the catalogue check and the audit entry `refused:<Code>`. On a failure the record holds only the code and the missing catalogue entries (`_fail_import` `:1100-1111`), not the affected rows; between F-15 and F-17 the UI would lose the row-exact message `IMPORT_MEMBER_NOT_FOUND`. Its half sentence "the backend's memory limit does not grow": `backend-tmp` has to grow above 513 Mi and counts against the 2 Gi — accept that or put `/tmp` on disk, and name which.
- **Criterion 5** should additionally name REQ-056 §13.6 (`:580`), AK-44 (`:710`), AK-49 (`:685`), the comment `values.yaml:109-130` and the EN mirror.

**Already implemented:** 413 naming the limit, `too_large`, edge 513m, the worker check, the worker limit of 2 Gi.

**Cross-feature (R-19).**

- The order F-15 → F-16 → F-17 is right. Two dependencies were not recorded: F-16 depends on F-15 (sizes), and F-17 criterion 5 depends on F-16 (phase "Messwerte"); the roadmap names only "F-17 after F-15".
- Coupling of criterion 4 and F-17: either F-15 carries the interim solution for asynchronous refusals (option B below), or both features ship in the same sprint without a release in between.
- Sprint-value verifier: F-17 criterion 1 does not prove the chain (preview and import without a second upload, neither completeness nor size). Closest to the roadmap promise "complete" is F-16 criterion 5. Chain-proving would be an integration test "pre-check → import of the stored archive with readings → empty difference" as an extended hook on F-17 criterion 1. Size (criterion 1 here) stays a manual proof after the operator decision.
- One installation: restoring beside the existing original fails on own species with the same scientific name (runbook `:136-137`). The manual 500 MiB test and every demo need a tenant without own species or an original deleted beforehand.
- Stale texts on "one installation": REQ-056 §8.1 (`:337`, "Installation wechseln"), runbook `:3`, roadmap origin "O-4 Umzug" — spec maintenance, not a blocker.
- No overlap with other features: F-20 did the export part, F-12 is done.

**Issue #3140 (read 2026-11-27; the reviewer could not).** The issue lists exactly F-15, F-16, F-17 in this serial order (all change `tenant_export_service.py`), which matches the feature set and the two dependencies recorded now. Its decisions of 2026-11-27 (worker memory limit rises, the 500 MiB test is manual only, privacy findings on the archive go into their own lane) agree with the sections of the three files; it names two privacy points beyond the list in this file (reason for a platform export, DSFA note), also outside R-19. It does not state the "one installation" decision. It decides none of the open points: it takes "the check runs in the worker only" for F-15 as given without saying what stays synchronous (so it fits option B and speaks against option A, which would move that sentence to F-17); it describes F-17 as "step-up on the archive hash, 24-hour expiry, import list with phases" without a validity period, a binding to the same admin (D2) or a rule for where archive errors appear (D1); and it does not mention the per-document validation of REQ-056 §12.4 or any spec/runbook amendment. One item is stale: it lists the abort reason `too_large` as open work, the reason exists. No point of the issue is left without a feature.

**Edits required before `ready`** (the report's verdict for F-15: ready after edits; translated):

1. Make criterion 4 precise along option B.
2. Extend criterion 5 by §8.4, AK-34, AK-44, AK-46, AK-49, §13.6 and the runbook table.
3. Switch hook 1 to `workflow_dispatch` and add a chart-contract check.
4. Extend hook 3 by "the worker knows the import limit".
5. Name the composition of the 500 MiB archive.
6. Correct the consistency note on `too_large` and on the worker limit of 2 Gi.

### Re-run 2026-11-28

Manueller, rein lesender Durchgang gegen develop `17e1034d2`, zusammen für F-15, F-32, F-17 und F-16. Auslöser: die Betreiberentscheidungen vom 2026-11-27 (Option B, `/tmp` auf Disk, D1, D2, Dokumentprüfung als eigenes Feature), die danach umgeschriebenen Kriterien und das neue Feature F-32 mit überschneidendem Umfang. Es lief kein Test; jede Aussage über heutiges Verhalten stammt aus dem Lesen der genannten Stelle. Abweichung vom Regelweg: Der Lauf ist ein manueller Durchgang, obwohl der Agent `feature-consistency-reviewer` verfügbar ist. Der Auftrag kam an einen Subagenten, der selbst keinen Agenten starten darf; nach `spec/project/feature/` §Consistency check ist das ein Workflow-Health-Befund, und der Lauf über den Agenten ist nachzuholen, sobald sich an den Kriterien etwas ändert.

Seit dem Lauf vom 2026-11-27 (develop `cc8531492`) hat sich von den zitierten Dateien nur `src/backend/app/common/dependencies.py` (+2 Zeilen) und `src/backend/app/domain/models/site.py` (+13 Zeilen) geändert (`git diff --stat cc8531492 17e1034d2`); alle anderen Zeilenanker dieses Features wurden nachgelesen und stimmen.

**Befunde vom 2026-11-27 — Verbleib.**

1. `helm/kamerplanter/values.yaml:1662` (prior-art) — erledigt. Established: `limits.memory: 2Gi` für Backend (`:1022`) und Worker (`:1662`); beide `/tmp`-Volumes `medium: Memory`, `sizeLimit: 64Mi` (`:2468-2486`; der Lauf vom 27.11. nannte `:2468-2482`). acceptance-1, -2 und -7 nennen die Deltas.
2. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:384` (drift) — entschieden: Option B (2026-11-27). acceptance-5 legt fest, was synchron bleibt, acceptance-6 die asynchrone Ablehnung, acceptance-8 zieht §8.4 Schritt 6, AK-34 und AK-46 nach.
3. `src/backend/app/domain/models/tenant_export.py:40` (prior-art, proceed) — unverändert richtig.
4. `helm/kamerplanter/values.yaml:926` (drift) — erledigt durch acceptance-3 und seinen Hook. Korrigierter Anker: `TENANT_IMPORT_MAX_UPLOAD_MB` steht in `:929`, das Spool-Budget in `:926`.
5. `project/features/tenant-archive-size-limits.md:57` (drift) — erledigt: Hook 1 ist `workflow_dispatch`, die Dauerprüfung liegt als Chart-Contract an acceptance-7.
6. `src/backend/app/domain/engines/tenant_export_engine.py:1003` (prior-art) — erledigt: acceptance-1 nennt die Zusammensetzung; der Hash im Browser steht im Hook und in den Risiken.

Der Block vom 2026-11-27, wie er bis zu diesem Lauf im Frontmatter stand:

```yaml
consistency_check:
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: prior-art
      target: helm/kamerplanter/values.yaml:1662
      resolution: revisit-after Kriterium 1/4 nennen die echten Deltas (tmp-Größen, Spool-Budget)
      evidence: "celery-worker limits.memory: 2Gi (:1662), backend 2Gi (:1022); backend-tmp und celery-worker-tmp 'medium: Memory, sizeLimit: 64Mi' (:2468-2482)"
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:384
      resolution: revisit-after Kriterium 4 legt fest, was synchron bleibt, und Kriterium 5 nennt §8.4, AK-34, AK-46
      evidence: "§8.4 Schritt 6: 'Geprüft wird am Antrag (synchrone Ablehnung, nichts gespeichert)'; AK-46 :687 'speichert keinen Upload und auditiert refused:<Code>'; AK-34 :680 '422 … nichts geschrieben'; service request_import :773-786"
    - kind: prior-art
      target: src/backend/app/domain/models/tenant_export.py:40
      resolution: proceed
      evidence: "TenantExportFailureReason = Literal['too_large', ...]; tenant_export_service.py:511-513 'except ArchiveTooLargeError … _fail_export(claimed, \"too_large\")'; AK-44 REQ-056:710 'umgesetzt'"
    - kind: drift
      target: helm/kamerplanter/values.yaml:926
      resolution: revisit-after Test-Hook zu Kriterium 3 pinnt, dass der Worker dieselbe Importgrenze kennt
      evidence: "UPLOAD_SPOOL_BUDGET_MB (:926) und TENANT_IMPORT_MAX_UPLOAD_MB (:929) stehen nur unter controllers.backend; der Export läuft im Worker (tasks/tenant_export_tasks.py:31-40); _size_limit :486-490 gibt None bei unbegrenztem Kontingent"
    - kind: drift
      target: project/features/tenant-archive-size-limits.md:57
      resolution: revisit-after Test-Hook 1 auf workflow_dispatch umgeschrieben und Chart-Contract als Dauerprüfung ergänzt
      evidence: "Hook: '(CI lane) — pending' gegen :105 'läuft nur manuell (workflow_dispatch)'; Chart-Contract-Block existiert: scripts/ci/assert_chart_contracts.sh:555-591"
    - kind: prior-art
      target: src/backend/app/domain/engines/tenant_export_engine.py:1003
      resolution: revisit-after Kriterium 1 definiert die Zusammensetzung des 500-MiB-Archivs
      evidence: "MAX_UNCOMPRESSED_BYTES 1 GiB (:1003), MAX_DOCUMENT_BYTES 128 MiB (:1007), MAX_ROWS 1 000 000 (:1012); _with_stored_bodies hält Objekte doppelt (service :1286-1311); Browser-Hash 'subtle.digest(\"SHA-256\", await file.arrayBuffer())' (src/frontend/src/utils/tenantImport.ts:47)"
```

**Neue Befunde.**

- **Synchron bleibt, was das Archiv nicht braucht (drift, proceed).** Established: `request_import` prüft heute Rolle (`tenant_export_service.py:756-757`), Größe (`:758-759`) und Step-up (`:761-771`), bevor es das Archiv öffnet, danach `_verified_archive` (`:774`), die Zuordnung (`:775`), den Plan (`:776-778`), die Kontingente (`:779`) und den Objektspeicher (`:780-781`). Von der Zuordnung braucht nur die Frage „ist der Schlüssel ein Mitglied des Archivs“ das Archiv (`known`, `:962`, `:968`); Konto, Rolle und Scopes kommen aus dem Antrag (`:965-984`). Nach Option B bleiben Rolle, Größe, Step-up, „Plan vorhanden“ und E-Mail → Konto synchron; der Abgleich der Mitgliedsschlüssel, die Kontingente (§8.4 Schritt 6) und die Katalogprüfung laufen nur noch im Worker, der sie heute schon ausführt (`:1013`, erneute Kontingentprüfung vor der Gründung laut Moduldoku `:42-44`).
- **Ablehnungsdetails am Datensatz (prior-art, proceed).** Established: `_fail_import` speichert den Code immer, die Einträge aber nur für `IMPORT_MISSING_CATALOG_ENTRIES`, gekappt auf 200 (`:1105`); die Statuskarte zeigt Code und fehlende Katalogeinträge (`TenantImportStatusCard.tsx:241-266`). acceptance-6 verallgemeinert das auf jeden Code. REQ-056 §13.5 nennt den Bericht „Anzahl je Collection; keine Inhalte“ (`:565`); die Details sind Bezeichner (Collection, Schlüssel, Feld, Pfad), keine Feldwerte, und §13.5 wird mit acceptance-8 ergänzt.
- **Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: F-15 liefert die Speicherung der Details und ihre Anzeige an der Statuskarte eines einzelnen Imports, F-17 zeigt denselben Datensatz zusätzlich in der Importliste. Es gibt eine Quelle (den Import-Datensatz) und zwei Ansichten; kein Kriterium wird doppelt umgesetzt. Mit Option B ist die zeilengenaue Meldung `IMPORT_MEMBER_NOT_FOUND` für unbekannte E-Mail-Adressen auch zwischen F-15 und F-17 vorhanden, ein Zwischenstand ohne sie entsteht nicht; die Kopplung „F-15 und F-17 ohne Zwischenrelease“ aus dem Lauf vom 27.11. entfällt.
- **Überschneidung mit F-32 (overlap, proceed).** Begründung für `proceed`: F-32 fügt der Hintergrundprüfung einen weiteren Ablehnungsgrund hinzu und nutzt für seine Einträge das Detailfeld aus acceptance-6. F-15 definiert das Feld, F-32 füllt es; deshalb steht F-32 in der Reihenfolge nach F-15.
- **Worker-`/tmp` (prior-art, proceed mit offenem Umsetzungspunkt).** Established: Der Worker schreibt und liest das Archiv über `SpooledTemporaryFile(max_size=_SPOOL_BYTES)` (`:503`, `:1006`; 32 MiB, `:162`), hält es beim Prüfen im Speicher (`tenant_export_engine.py:1000-1003`) und ersetzt die Objekte durch eine zweite Kopie (`_with_stored_bodies`, `tenant_export_service.py:1286-1312`); `celery-worker-tmp` ist speicherbasiert mit 64 Mi. Entschieden ist nur `backend-tmp`. Unestablished: ob ein 500-MiB-Archiv mit speicherbasiertem Worker-`/tmp` unter 2 GiB bleibt; das klärt erst der manuelle Lauf zu acceptance-1 (nicht durchgeführt). Siehe „Offene Punkte“.

**Umgesetzte Edits aus dem Lauf vom 2026-11-27** (alle sechs): Kriterium 4 entlang Option B (jetzt acceptance-5 und -6), Kriterium 5 erweitert (acceptance-8), Hook 1 auf `workflow_dispatch` mit Chart-Contract, Hook 3 um „der Worker kennt die Importgrenze“, Zusammensetzung des 500-MiB-Archivs (acceptance-1), Notizen zu `too_large` und zum Worker-Limit korrigiert (oben datiert vermerkt). Zusätzlich: altes Kriterium 3 in acceptance-3 und -4 geteilt, `/tmp` des Backends als acceptance-7.

**Verhältnis der vier Features (R-19).** F-15 hängt von keinem der anderen ab. F-32, F-17 und F-16 setzen F-15 voraus (Hintergrundprüfung, Detailfeld, Größen). Die Reihenfolge F-15 → F-32 → F-17 → F-16 trägt; Einzelheiten in `project/sprints/0005-garten-aus-archiv-vollstaendig-wiederherstellen.md`.

**Ergebnis:** kein ungelöster Befund; F-15 ist `ready`.

## Risks

- Das Speicherlimit des Workers bleibt bei rund 2 GiB (`helm/kamerplanter/values.yaml:1662`); beim Prüfen eines fotolastigen 500-MiB-Archivs liegen die Objekte zeitweise doppelt im Speicher. Reicht das nicht, zeigt es der manuelle Lauf zu acceptance-1.
- Wird der Worker vom Kernel wegen Speichermangels beendet, endet der Lauf nicht mit „zu groß“, sondern erst nach sechs Stunden über den Stale-Sweep (`tenant_export_service.py:168`, `:1402-1408`); acceptance-4 deckt nur das volle `/tmp` ab.
- Die Import-Seite berechnet den Hash des Archivs im Browser über die ganze Datei im Speicher (`src/frontend/src/utils/tenantImport.ts:47`); bei 500 MiB kann das auf schwachen Geräten scheitern. Der manuelle Lauf prüft es einmal über die Oberfläche.
- Ein fehlerhaftes Archiv wird nicht mehr in der Upload-Antwort gemeldet, sondern in der Statusanzeige. Bis F-17 die Importliste liefert, sieht der Admin das nur an der Statuskarte des gerade gestarteten Imports.
- `/tmp` des Backends auf Disk braucht Platz auf dem Knoten für mindestens einen Upload an der Importgrenze; auf kleinen Knoten konkurriert das mit anderen Pods.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R1, R2, R10–R12)
- F-32, F-17 und F-16 setzen dieses Feature voraus

## Betreiberentscheidungen 2026-11-27

- Das Speicherlimit des Workers darf für Archive bis etwa 500 MiB dauerhaft auf rund 2 GiB steigen.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`), weder je Pull Request noch nachts.
- Es gibt nur eine Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv (Abgleich mit abgeschlossenen Löschungen, `anon_`-Pseudonyme, GPS-Genauigkeit) laufen in einer eigenen Lane und sind kein Teil von R-19.
- #2138 ist geschlossen; der Rest läuft als #3140.
- **Kriterium 4: Option B.** Synchron bleiben Rolle, Größe, Step-up, „Plan vorhanden“ und E-Mail → Konto; alles Übrige läuft asynchron; die Ablehnungsdetails werden am Import-Datensatz gespeichert; die Doku zieht REQ-056 §8.4, AK-34, AK-46 und die Runbook-Tabelle nach (acceptance-5, -6, -8).
- **`/tmp` des Backends liegt auf Disk** (Volume im Helm-Chart) und wird nicht speicherbasiert vergrößert (acceptance-7).
- Sprint 5 enthält nur R-19; Reihenfolge der Umsetzung F-15 → F-32 → F-17 → F-16.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

- **Kriterium 4 — was bleibt synchron, wenn nur noch der Worker das Archiv prüft?** Heute lehnt `request_import` ein fehlerhaftes Archiv in der Upload-Antwort ab und speichert nichts (`tenant_export_service.py:773-786`; REQ-056 §8.4 Schritt 6 `:384`, AK-34 `:680`, AK-46 `:687`). An dieser Prüfung hängen die Mitgliederzuordnung (`:962-968`), die Kontingent- und die Katalogprüfung sowie der Audit-Eintrag `refused:<Code>`. Der Import-Datensatz hält bei einem Fehlschlag nur den Code und die fehlenden Katalogeinträge (`_fail_import :1100-1111`), nicht die betroffenen Zeilen.
  - **Option A — Kriterium 4 nach F-17 verschieben:** Kriterium 1 ist gefährdet, weil das Backend ein 500-MiB-Archiv im Request prüfen müsste.
  - **Option B (empfohlen) — Kriterium 4 bleibt und benennt die Grenze:** Synchron bleiben Rolle, Größe, Step-up, „Plan vorhanden“ und E-Mail → Konto; alles Übrige wird asynchron. Die Ablehnungsdetails werden am Import-Datensatz gespeichert; Kriterium 5 zieht §8.4, AK-34, AK-46 und die Runbook-Tabelle (`:117-131`) nach.
  - **Ohne Übergangslösung — F-15 und F-17 im selben Sprint ohne Zwischenrelease:** Die zeilengenaue Meldung `IMPORT_MEMBER_NOT_FOUND` fehlt der Oberfläche dann nie in einem ausgelieferten Stand; beide Features sind aneinander gebunden.
  - **Entschieden 2026-11-27: Option B.** Umgesetzt in acceptance-5 und -6; acceptance-8 zieht die Spec nach.
- **Kriterium 4 — `/tmp` des Backends.** Heute sind `backend-tmp` und `celery-worker-tmp` speicherbasiert mit 64 Mi (`helm/kamerplanter/values.yaml:2468-2482`) und zählen gegen das Limit von 2 Gi (`:1022`, `:1662`). Für 500 MiB muss `backend-tmp` auf über 513 Mi wachsen.
  - **Speicherbasiert lassen:** Der Halbsatz „das Speicherlimit des Backends wächst nicht“ gilt nur dem Wert nach; der Upload belegt bis zu einem Viertel des Limits.
  - **`/tmp` auf Disk legen:** Der Arbeitsspeicher bleibt frei; das Chart braucht ein Volume mit Platz auf dem Knoten.
  - **Entschieden 2026-11-27: `/tmp` des Backends auf Disk legen** (acceptance-7). Für den Worker siehe „Offene Punkte“.

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-15.

- **`/tmp` des Workers — speicherbasiert vergrößern oder ebenfalls auf Disk?** Entschieden ist nur `backend-tmp`. Heute ist `celery-worker-tmp` speicherbasiert mit 64 Mi (`helm/kamerplanter/values.yaml:2478-2486`) und zählt gegen das Limit von 2 Gi (`:1662`). Die Wahl bleibt der Umsetzung überlassen, solange acceptance-1 hält und das Limit von 2 GiB nicht steigt. Empfehlung der Planung: auf Disk wie beim Backend, weil der Worker das Archiv beim Prüfen zusätzlich im Speicher hält. Blockiert niemanden; wünscht der Betreiber eine feste Vorgabe, genügt ein Satz vor dem Start von F-15.
