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

## Risks

- The worker's permanent memory limit grows to ~2 GiB; on small self-hosted nodes this competes with other pods.
- Moving verification out of the backend request changes when a malformed archive is reported (async instead of in the upload response) — F-17's preflight shows the result.

## References

- Issue #2138 (MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R1, R2, R10–R12)
