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

## Risks

- A stored preflight archive (up to ~500 MiB) occupies object storage for up to 24 h.
- The step-up's validity window must cover the time between preflight and import; too short a TTL forces a second step-up.

## References

- Issue #2138 (MT-042), roadmap item R-19; depends on F-15
- `project/requirements/tenant-export-import-remainder.md` (R5–R8, R15–R17)
