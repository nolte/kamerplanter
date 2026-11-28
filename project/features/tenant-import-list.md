---
id: F-33
title: Importliste und Ablauf vorgeprüfter Archive
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-28
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-28
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: prior-art
      target: src/backend/app/domain/interfaces/tenant_export_store.py:115
      resolution: proceed
      evidence: "ITenantImportRequestRepository (:115-138) hat keine Listenmethode; TenantImportRequest (domain/models/tenant_export.py:81-107) hat weder Quelle noch Phase; die Seite zeigt heute nur einen einzelnen Import (TenantImportStatusCard.tsx)."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:168
      resolution: proceed
      evidence: "STALE_AFTER = timedelta(hours=6) (:168); list_stale_active nimmt 'pending/validating/running' (tenant_export_store.py:135-138), delete_finished_before nur 'completed/failed' (:131-133). Ein wartendes vorgeprüftes Archiv darf der Sweep nicht nach 6 Stunden beenden, ein abgelaufenes muss die Löschung nach 30 Tagen erfassen (acceptance-4, -5)."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:572
      resolution: proceed
      evidence: "§13.5: 'Das hochgeladene Archiv eines Imports wird nach Abschluss oder Fehlschlag sofort gelöscht' und 'report … keine Inhalte' (:565); spec/privacy/02-personal-data-inventory.md:139 führt nur requested_by_user_key. acceptance-6 zieht nach."
    - kind: prior-art
      target: spec/privacy/14-contradiction-register.md:59
      resolution: proceed
      evidence: "W-38 korrigiert NFR-011 R-40 von 'Nicht implementiert' (NFR-011:151) auf umgesetzt; REQUEST_RETENTION 30 Tage existiert (tenant_export_service.py:171, :1410-1411). Wer zuerst mergt, erledigt die Korrektur."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "Abgespalten aus F-17 (Betreiberentscheidung A, 2026-11-28). F-17 legt Vorprüf-Datensatz, Mitgliedervorschau und Start an; F-33 listet sie und regelt Ablauf und Leerung. Begründung in den Consistency notes."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "acceptance-2 zeigt in der Liste die Ablehnungsdetails, die F-15 acceptance-6 am Datensatz speichert (auch die Einträge aus F-32); 'nur im Audit' für frühe Ablehnungen stützt sich auf F-15 acceptance-10. Begründung in den Consistency notes."
    - kind: drift
      target: project/features/tenant-archive-size-limits.md
      resolution: proceed
      evidence: "Dritter Agentenlauf (2026-11-28): acceptance-2 nannte 'nur im Audit' ohne die Ausnahme aus F-15 acceptance-10; die Größenprüfung im Dienst greift fast nie, weil 413 aus Proxy oder Middleware vorher kommt (kein Konto, kein Audit). Ergänzt."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:1110
      resolution: proceed
      evidence: "Dritter Agentenlauf: acceptance-5 ließ offen, ob eine an einem Archivfehler gescheiterte Vorprüfung eine Mitgliederliste trägt. Zusage ergänzt: Sie trägt keine (heute leert _fail_import member_grants, :1110)."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "Dritter Agentenlauf: Das Dateninventar für die Anzeigenamen gehört zu dem Feature, das die Felder anlegt. Nach F-17 acceptance-7 verschoben; acceptance-6 hier nennt nur noch Quelle und Zustände."
---

## Description

Frühere Importe eines Mandanten-Archivs sind heute nirgends aufgelistet; der
Plattform-Admin sieht nur den Import, den er gerade gestartet hat. Ein
hochgeladenes Archiv wird sofort nach dem Import gelöscht.

Nach dieser Änderung zeigt die Admin-Seite eine Liste aller Vorprüfungen und
Importe mit Quelle, Ziel, beteiligten Admins, Status und Fehler sowie der
Phase eines laufenden Imports. Scheitert die Prüfung an einem Fehler im
Archiv, steht das mit Grund in dieser Liste. Ein vorgeprüftes Archiv, das
niemand importiert, verschwindet nach 24 Stunden; die Namen der
Archiv-Mitglieder werden gelöscht, sobald der Import gelungen oder die
Vorprüfung abgelaufen ist, und jeder Eintrag verschwindet 30 Tage nach seinem
Ende.

## Acceptance criteria

- [ ] **acceptance-1** Die Admin-Seite listet Vorprüfungen und Importe mit Datum, Quelle (Name und Kurzname des archivierten Gartens), Ziel-Garten, hochladendem und startendem Admin, Status und Fehlertext; Mitgliedernamen zeigt die Liste nicht.
- [ ] **acceptance-2** Eine an einem Archivfehler gescheiterte Vorprüfung steht in der Liste als fehlgeschlagen mit Grund und betroffenen Einträgen; eine vor dem Speichern abgelehnte Anfrage (Rolle, Größe, Bestätigung) erscheint nicht in der Liste, sondern nur im Audit — ausgenommen Anfragen ohne erkennbares Konto, die auch dort nicht stehen: unangemeldete und solche, die schon Proxy oder Middleware wegen der Größe mit 413 abweist, was für zu große Uploads der Regelfall ist.
- [ ] **acceptance-3** Bei einem laufenden Import zeigt die Liste die aktuelle Phase (Prüfen, Datensätze schreiben).
- [ ] **acceptance-4** Ein vorgeprüftes, nicht importiertes Archiv bleibt 24 Stunden ab dem Upload startbar — auch wenn es länger als sechs Stunden wartet — und ist danach gelöscht; der Eintrag steht dann als abgelaufen in der Liste und lässt sich nicht mehr starten.
- [ ] **acceptance-5** Die Mitgliederliste einer Vorprüfung ist geleert, sobald der Import gelungen oder die Vorprüfung abgelaufen ist, und eine an einem Archivfehler gescheiterte Vorprüfung trägt von vornherein keine; jeder Listeneintrag, auch eine fehlgeschlagene oder abgelaufene Vorprüfung, verschwindet 30 Tage nach seinem Ende.
- [ ] **acceptance-6** Beschriftungen und Doku (DE + EN) beschreiben Liste und Ablauf; REQ-056 §13.5 (Zustände, Quelle, 24-Stunden-Frist statt sofortiger Löschung), §14 und der Status von NFR-011 R-40 sind nachgezogen, und das Dateninventar `spec/privacy/02-personal-data-inventory.md` nennt die Quelle (Name und Kurzname des archivierten Gartens).

## Test hooks

- **acceptance-1** — repository list-method test + `src/backend/tests/api/test_tenant_export_routes.py` (`GET /admin/platform/tenant-imports`, platform admin in person, absent in light mode per AK-43; `src/backend/tests/unit/test_route_consumers_check.py:368` counts 918 after F-17's 917) + vitest of the list table (`src/frontend/src/test/pages/AdminTenantImportsPage.test.tsx`); the list response carries no member names for any admin — pending
- **acceptance-2** — service test: a pre-check failed on a corrupt archive, and one failed on `IMPORT_DOCUMENT_INVALID` (F-32), are listed with code and entries; a refusal for role, a service-level size refusal or a step-up refusal creates no record and is found in the audit only (F-15 acceptance-10); a 413 from the body ceiling and an unauthenticated request create neither a record nor an audit entry, which the test pins as the documented exception — pending
- **acceptance-3** — service test (the record's phase follows validating → writing) + vitest of the phase display — pending
- **acceptance-4** — unit tests of the hourly sweep (`TenantExportService.expire`, `tenant_export_service.py:1384`): a waiting pre-check untouched for 7 h is not ended by the stale sweep (`:1407`) and can still be started; 24 h after the upload the stored archive is deleted, the record is expired and a start is refused — also for a pre-check whose run failed and was kept startable (F-17 acceptance-6) — pending
- **acceptance-5** — unit tests: the member preview is empty on `completed` and expired records, never filled on a pre-check that failed on an archive error, and still present on a failed run that is startable again; `delete_finished_before` (`interfaces/tenant_export_store.py:131-133`) removes expired and failed pre-checks 30 days after their end — pending
- **acceptance-6** — i18n completeness + `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte)

Manueller, rein lesender Durchgang gegen develop `17e1034d2` beim Anlegen des Features am 2026-11-28; es lief kein Test. Der Agent `feature-consistency-reviewer` ist verfügbar, ein Subagent darf ihn aber nicht starten; die Hauptsitzung lässt ihn nach diesem Commit laufen. Das Feature ist aus F-17 abgespalten (Betreiberentscheidung A vom 2026-11-28); die Vorgeschichte seiner Kriterien steht in `tenant-import-preflight.md`.

**Keine Liste, kein Feld für Quelle und Phase (prior-art, proceed).** Established: Das Repository der Import-Anträge kennt `create`, `get`, `claim`, `update_fields`, `delete_finished_before` und `list_stale_active`, aber keine Liste (`interfaces/tenant_export_store.py:115-138`); der Datensatz hat weder Quelle noch Phase (`tenant_export.py:81-107`). Die Quelle (Name, Kurzname aus `tenant.json`) schreibt die Hintergrundprüfung aus F-17 an den Datensatz; F-33 zeigt sie.

**Sweep und Löschung kennen den wartenden Zustand nicht (drift, proceed).** Established: Der stündliche Lauf beendet Anträge, die sechs Stunden unberührt sind (`tenant_export_service.py:168`, `:1407-1409`; erfasst `pending/validating/running`, `tenant_export_store.py:135-138`), und löscht nach 30 Tagen nur `completed/failed` (`:131-133`, `:1410-1411`). Ein vorgeprüftes Archiv wartet bis zu 24 Stunden; acceptance-4 und -5 verlangen, dass der Sweep es bis dahin in Ruhe lässt und danach erfasst.

**Spec sagt „sofort gelöscht“ (drift, proceed).** Established: REQ-056 §13.5 (`:572`) und der Bericht ohne Inhalte (`:565`); das Dateninventar nennt für die Collection nur `requested_by_user_key` (`spec/privacy/02-personal-data-inventory.md:139`). acceptance-6 zieht nach, was Liste und Ablauf betrifft; die Anzeigenamen im Dateninventar trägt F-17 acceptance-7 (das Feature, das die Felder anlegt), die neuen Kontofelder und den Guard R6 F-17 acceptance-4.

**Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: Die Teilung trennt nach Zuständigkeit. F-17 erzeugt den Vorprüf-Datensatz, hält die Mitgliedervorschau, regelt wer sie sieht und startet den Import; F-33 liest diese Datensätze als Liste und regelt ihr Ende (Ablauf, Leerung, Löschung). Kein Kriterium steht in beiden. Die Leerung der Mitgliederliste liegt hier, weil sie an Ablauf und Abschluss hängt; die Sicht auf die Namen liegt in F-17 acceptance-3.

**Überschneidung mit F-15 (overlap, proceed).** Begründung für `proceed`: F-15 speichert Code und Einträge einer gescheiterten Hintergrundprüfung am Datensatz und zeigt sie an der Statuskarte; F-33 zeigt denselben Datensatz in der Liste. Eine Quelle, zwei Ansichten; das gilt auch für die Einträge aus F-32. Der zweite Halbsatz von acceptance-2 („nur im Audit“) stimmt erst mit F-15 acceptance-10.

**Ergebnis des manuellen Durchgangs:** kein ungelöster Befund.

### Stand nach dem dritten Agentenlauf (2026-11-28)

Der Agent hat F-33 im dritten Lauf (`feature-consistency-reviewer@unknown`, 2026-11-28, gegen `b3c7f6eba`) geprüft und für `ready` befunden; `agent_version` im Frontmatter nennt jetzt den Agenten, seine drei Hinweise sind angehängt und eingearbeitet: die Ausnahme aus F-15 acceptance-10 in acceptance-2, die Zusage zur Mitgliederliste einer gescheiterten Vorprüfung in acceptance-5 (Established: `_fail_import` leert `member_grants` schon heute, `tenant_export_service.py:1110`), das Dateninventar für die Anzeigenamen nach F-17 acceptance-7 verschoben.

**Ergebnis:** F-33 ist `ready`.

## Risks

- Ein gespeichertes, vorgeprüftes Archiv (bis ~500 MiB) belegt bis zu 24 Stunden Objektspeicher; mehrere wartende Archive summieren sich.
- Quelle (Name und Kurzname des archivierten Gartens) bleibt 30 Tage am Eintrag. Der Name eines persönlichen Gartens kann ein Personenname sein; das Dateninventar nennt das Feld (acceptance-6).
- Die Phase „Messwerte“ zeigt die Liste erst mit F-16.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R6, R8, R16, R17)
- Setzt F-17 voraus (Vorprüf-Datensatz, Start) und F-15 (Detailfeld, Audit früher Ablehnungen); F-16 ergänzt die Phase „Messwerte“

## Betreiberentscheidungen 2026-11-27

- **D1:** Archivfehler erscheinen als fehlgeschlagene Vorprüfung in der Importliste; „nur im Audit“ gilt für Ablehnungen vor dem Speichern (Rolle, Größe, Step-up).
- Ein vorgeprüftes, nicht importiertes Archiv verschwindet nach 24 Stunden (Entscheidung vom 2026-11-17, R6).

## Betreiberentscheidungen 2026-11-28

- **A — F-17 wird geteilt**; dieses Feature ist der Teil „Importliste und Ablauf“.
- **C — Früh abgelehnte Uploads werden auditiert** (F-15 acceptance-10); damit stimmt „nur im Audit“ in acceptance-2.

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-33.

- **Spalte „Admin“.** Die Liste zeigt den hochladenden und den startenden Admin getrennt, weil sie nach der Entscheidung B verschieden sein können. Festlegung der Planung.
