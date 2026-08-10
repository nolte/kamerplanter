---
id: F-9
title: Ein atomarer Abschluss-Übergang für Aufgabe, Erinnerung und Benachrichtigung
status: draft
roadmap_item: R-15
sprint: null
created: 2026-08-10
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-08-10
  agent_version: feature-consistency-reviewer@66bd4c0fe
  findings:
    - kind: prior-art
      target: src/backend/app/domain/services/task_service.py:1037
      resolution: proceed
      evidence: "Die Übergangs-Hälften existieren verstreut (complete_task/skip_task + best-effort Hooks; care-seitig confirm/complete/snooze); kein CompletionTransitionService existiert — genuines Konsolidierungsziel, kein Nachbau."
    - kind: prior-art
      target: src/backend/app/data_access/arango/
      resolution: proceed
      evidence: "Kein Stream-Transaktions-Support im Arango-Repository-Layer vorhanden — das Transaktions-Arbeitspaket (R2) ist bestätigt from-scratch."
    - kind: drift
      target: src/backend/app/domain/services/notification_propagation_service.py:29
      resolution: proceed
      evidence: "Der dokumentierte Kontrakt 'a propagation failure … can never abort the underlying task/care mutation (NFR-007)' wird auf der Abschluss-Kante bewusst invertiert (R2 atomar); außerhalb gilt er weiter (R3). Die Kanten-Grenze wird in Docstrings dokumentiert und in F-10 nach BACKEND.md gehoben."
    - kind: drift
      target: src/backend/app/domain/services/task_service.py:1079
      resolution: proceed
      evidence: "Der Next-Occurrence-Spawn läuft heute NACH dem Status-Write, nicht-atomar; F-9 zieht ihn in dieselbe Transaktion. Transaktions-Reichweite: genau die Collections des Übergangs; Kanalzustellung nie Teil der Transaktion (Requirements-Annahme)."
    - kind: overlap
      target: project/features/unify-notification-propagation.md
      resolution: proceed
      evidence: "Dieselbe Naht wie in F-8: Notification-Write der Transition vs. 'ein Propagationspfad'. Operator-Entscheidung 2026-08-10: Propagationsdienst läuft mit Transaktions-Kontext INNERHALB der Transaktion."
---

## Description

„Erledigt", „übersprungen" und „umgeplant" werden **ein** Übergang mit **einem**
Besitzer: ein neuer `CompletionTransitionService` im Service-Layer bewegt
Aufgabe, Pflegeerinnerung und Benachrichtigung gemeinsam — in einer
ArangoDB-Stream-Transaktion, sodass die Gärtnerin nie einen halben Zustand
sieht (Aufgabe erledigt, aber die Benachrichtigung mahnt weiter — die
#548/#619/#622-Klasse). Innerhalb desselben Übergangs schreibt die
`RecurrenceEngine` die nächste Fälligkeit abschluss-verankert fort, und der
`NotificationPropagationService` läuft mit Transaktions-Kontext innerhalb der
Transaktion, damit „ein Propagationspfad" auch hier wörtlich gilt.

Dafür erhält der Repository-Layer Stream-Transaktions-Support — heute existiert
keiner (bestätigt from-scratch). Außerhalb des Abschluss-Übergangs bleibt die
dokumentierte best-effort-Semantik der Propagation unverändert (R3): zwei
Fehlerpolitiken, eine explizit dokumentierte Grenze.

## Acceptance criteria

- [ ] **acceptance-1** Done/skipped/rescheduled läuft für Aufgaben, Erinnerungen und deren Benachrichtigungen ausschließlich über den geteilten `CompletionTransitionService`; kein Router oder Service implementiert eine eigene Hälfte des Übergangs.
- [ ] **acceptance-2** Der Übergang schreibt atomar in einer ArangoDB-Stream-Transaktion: ein erzwungener Fehlschlag eines beliebigen Einzel-Writes hinterlässt keinen Teilzustand (Test je Write-Arm, rot-zuerst).
- [ ] **acceptance-3** Der Repository-Layer bietet Stream-Transaktions-Support, ohne nicht-transaktionale Pfade zu verändern; alle Bestandssuiten bleiben grün.
- [ ] **acceptance-4** Der Abschluss einer wiederkehrenden Aufgabe/Erinnerung schreibt die nächste Fälligkeit abschluss-verankert über die `RecurrenceEngine` fort — innerhalb derselben Transaktion (kein nachgelagerter Spawn mehr).
- [ ] **acceptance-5** Der `NotificationPropagationService` akzeptiert einen Transaktions-Kontext und schreibt den Notification-Teil des Übergangs innerhalb der Transaktion; außerhalb des Übergangs bleibt seine best-effort-/Nachhol-Semantik unverändert (Docstring-Kontrakt aktualisiert, per Test gepinnt).
- [ ] **acceptance-6** Die Kanalzustellung (HA, E-Mail, Web Push) ist nie Teil der Transaktion (Test: Transaktions-Rollback erzeugt keinen Kanal-Dispatch und blockiert keinen).

## Test hooks

- **acceptance-1** — Absenz-/Struktur-Test: keine zweite Übergangs-Implementierung (AST-Scan analog #816-Pendants) — pending
- **acceptance-2** — Unit-/Integrationstests mit erzwungenem Einzel-Write-Fehlschlag je Arm, rot-zuerst — pending
- **acceptance-3** — Bestandssuiten + neue Repo-Transaktions-Unit-Tests — pending
- **acceptance-4** — Service-Test Abschluss → Spawn in Transaktion (Rollback nimmt den Spawn mit) — pending
- **acceptance-5** — Propagationsdienst-Tests beider Modi (mit/ohne Kontext) — pending
- **acceptance-6** — Test Kanal-Dispatch-Entkopplung bei Rollback — pending

## Consistency notes

**overlap F-9 ↔ F-8 (`proceed`, Rationale):** Der Notification-Write des
Übergangs gehört beiden Invarianten — Atomarität (F-9) und „ein
Propagationspfad" (F-8). Die am 2026-08-10 getroffene Operator-Entscheidung
löst die Naht ohne Ausnahme: der Propagationsdienst erhält einen optionalen
Transaktions-Kontext und läuft innerhalb der Stream-Transaktion. Beide Features
referenzieren dieselbe Entscheidung; sie wird nicht zweimal getroffen, und das
F-10-Gate (b) braucht keine Exemption für den Transition-Service.

**drift Fehlerpolitik (`proceed`):** R2 (atomar auf der Abschluss-Kante)
invertiert den dokumentierten NFR-007-Kontrakt der Propagation bewusst; R3
behält ihn außerhalb. Die Grenze — welche Politik an welcher Kante — wird in
den Docstrings beider Dienste dokumentiert (acceptance-5) und in F-10 nach
`BACKEND.md` gehoben, damit das nächste #622 nicht aus Unklarheit entsteht.

**drift Spawn-Reihenfolge (`proceed`):** Der heute nachgelagerte, nicht-atomare
Next-Occurrence-Spawn wandert in die Transaktion (acceptance-4); die
Transaktions-Reichweite umfasst genau die Übergangs-Collections, nie die
Kanalzustellung (acceptance-6, Requirements-Annahme bestätigt).

## Risks

- Stream-Transaktionen über mehrere Collections sind neu im Repository-Layer —
  Lock-Verhalten und Timeout-Semantik von ArangoDB sind vor der breiten
  Verdrahtung an einer Kante zu erproben (acceptance-3 schützt die Bestandspfade).
- Der Übergang berührt drei große Services gleichzeitig; die Umsetzung sollte
  kantenweise erfolgen (erst complete, dann skip, dann reschedule), jede Kante
  rot-zuerst.
