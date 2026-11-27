---
id: F-15
title: Archivgrößen bis ~500 MiB mit klarer Grenze
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
mit einer Meldung abgelehnt, die die Grenze nennt. Das Prüfen des Archivs
übernimmt ausschließlich der Worker; das Backend nimmt den Upload nur
entgegen und legt ihn ab, damit sein Speicherbedarf nicht dauerhaft wächst.

## Acceptance criteria

- [ ] **acceptance-1** Mit den mitgelieferten Helm-Werten gelingen Export und Import eines Archivs von rund 500 MiB.
- [ ] **acceptance-2** Ein Upload über der Grenze wird mit 413 abgelehnt; die Meldung nennt die Grenze.
- [ ] **acceptance-3** Ein Export bricht spätestens an der Importgrenze (bzw. am Kontingent + 10 %, falls kleiner) mit dem Grund „zu groß“ ab; auch ein volllaufendes `/tmp` endet mit diesem Grund statt mit einem internen Fehler.
- [ ] **acceptance-4** Das Backend prüft hochgeladene Archive nicht mehr selbst; die Prüfung läuft nur im Worker, und das Speicherlimit des Backends wächst nicht.
- [ ] **acceptance-5** Runbook (DE + EN) und REQ-056 §8.3 nennen die neue Grenze, die Exportregel und die gemeinsam anzuhebenden Ressourcen.

## Test hooks

- **acceptance-1** — integration test with a ~500 MiB synthetic archive against the rendered default values (CI lane) — pending
- **acceptance-2** — existing body-limit test extended to the new ceiling (`exceptions.py:1016-1030`) — pending
- **acceptance-3** — unit tests: export limit = min(quota+10 %, import limit); ENOSPC during assembly → `too_large` — pending
- **acceptance-4** — unit test: import route stores the upload without calling the archive reader — pending
- **acceptance-5** — `mkdocs build --strict` + spec diff review — pending

## Consistency notes

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

## Risks

- The worker's permanent memory limit grows to ~2 GiB; on small self-hosted nodes this competes with other pods.
- Moving verification out of the backend request changes when a malformed archive is reported (async instead of in the upload response) — F-17's preflight shows the result.

## References

- Issue #2138 (MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R1, R2, R10–R12)

## Betreiberentscheidungen 2026-11-27

- Das Speicherlimit des Workers darf für Archive bis etwa 500 MiB dauerhaft auf rund 2 GiB steigen.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`), weder je Pull Request noch nachts.
- Es gibt nur eine Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv (Abgleich mit abgeschlossenen Löschungen, `anon_`-Pseudonyme, GPS-Genauigkeit) laufen in einer eigenen Lane und sind kein Teil von R-19.
- #2138 ist geschlossen; der Rest läuft als #3140.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

- **Kriterium 4 — was bleibt synchron, wenn nur noch der Worker das Archiv prüft?** Heute lehnt `request_import` ein fehlerhaftes Archiv in der Upload-Antwort ab und speichert nichts (`tenant_export_service.py:773-786`; REQ-056 §8.4 Schritt 6 `:384`, AK-34 `:680`, AK-46 `:687`). An dieser Prüfung hängen die Mitgliederzuordnung (`:962-968`), die Kontingent- und die Katalogprüfung sowie der Audit-Eintrag `refused:<Code>`. Der Import-Datensatz hält bei einem Fehlschlag nur den Code und die fehlenden Katalogeinträge (`_fail_import :1100-1111`), nicht die betroffenen Zeilen.
  - **Option A — Kriterium 4 nach F-17 verschieben:** Kriterium 1 ist gefährdet, weil das Backend ein 500-MiB-Archiv im Request prüfen müsste.
  - **Option B (empfohlen) — Kriterium 4 bleibt und benennt die Grenze:** Synchron bleiben Rolle, Größe, Step-up, „Plan vorhanden“ und E-Mail → Konto; alles Übrige wird asynchron. Die Ablehnungsdetails werden am Import-Datensatz gespeichert; Kriterium 5 zieht §8.4, AK-34, AK-46 und die Runbook-Tabelle (`:117-131`) nach.
  - **Ohne Übergangslösung — F-15 und F-17 im selben Sprint ohne Zwischenrelease:** Die zeilengenaue Meldung `IMPORT_MEMBER_NOT_FOUND` fehlt der Oberfläche dann nie in einem ausgelieferten Stand; beide Features sind aneinander gebunden.
- **Kriterium 4 — `/tmp` des Backends.** Heute sind `backend-tmp` und `celery-worker-tmp` speicherbasiert mit 64 Mi (`helm/kamerplanter/values.yaml:2468-2482`) und zählen gegen das Limit von 2 Gi (`:1022`, `:1662`). Für 500 MiB muss `backend-tmp` auf über 513 Mi wachsen.
  - **Speicherbasiert lassen:** Der Halbsatz „das Speicherlimit des Backends wächst nicht“ gilt nur dem Wert nach; der Upload belegt bis zu einem Viertel des Limits.
  - **`/tmp` auf Disk legen:** Der Arbeitsspeicher bleibt frei; das Chart braucht ein Volume mit Platz auf dem Knoten.
