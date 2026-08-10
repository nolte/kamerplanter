---
id: F-6
title: Inventar-Baseline — Kadenz-Vorschübe und Notification-Writes außerhalb ihrer Besitzer zählen
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
    - kind: overlap
      target: project/features/freeze-recurrence-propagation-boundaries.md
      resolution: proceed
      evidence: "F-6 baut einen Scanner für dieselben zwei Eigenschaften, die F-10 als Gates einfriert — zwei Implementierungen derselben Erkennungslogik wären die Duplikation, die ADR-008 bekämpft."
    - kind: prior-art
      target: spec/nfr/NFR-018_CI-CD-Pipeline-Integritaet.md:114
      resolution: proceed
      evidence: "§2.1: Ratchet-Baseline MUSS aus dem Ist-Zustand berechnet werden, nie als versionierte Konstante."
    - kind: prior-art
      target: scripts/check_schema_examples.py
      resolution: proceed
      evidence: "Muster #850: computed-Count-Script + Ratchet-Test mit Load-by-Path und Vakuum-Pins — exakt die geforderte Artefaktform."
    - kind: drift
      target: src/backend/app/domain (timedelta-Sites) / notification_service.py:352
      resolution: proceed
      evidence: "Nicht jedes timedelta ist ein Kadenz-Vorschub (Clone-/Template-Offsets, TTLs); Notification-Writes zerfallen in Propagation, Event-Erzeugung und Nutzer-Aktion — ohne Zähldefinition ist die Baseline Rauschen."
---

## Description

Bevor die Konsolidierung (F-7/F-8) beginnt, wird der Ist-Zustand messbar: Zwei
Scanner-Scripts zählen (a) jede Stelle, die eine nächste Fälligkeit außerhalb
der `RecurrenceEngine` berechnet, und (b) jeden Notification-Write außerhalb des
`NotificationPropagationService` — mit Datei-und-Zeile-Attribution. Die Zählung
ist **computed** (NFR-018 §2.1): sie wird zur Testzeit aus dem Baum erhoben, nie
als versionierte Konstante gepflegt. Für den Maintainer heißt das: der
Fortschritt der Phasen 1–2 ist eine sinkende Zahl, und ein neuer Verstoß fällt
sofort auf, statt als dreizehntes Symptom-Issue zurückzukommen.

Der Kern des Features ist die **schriftliche Zähldefinition**: Was zählt als
Kadenz-Vorschub (und was ist legitimer Offset wie Clone-/Template-Versatz oder
TTL), und welche der drei Notification-Schreibklassen (Propagations-Write,
Event-Erzeugung, Nutzer-Aktion wie `mark_read`) zählt gegen die Grenze. Diese
Definition wird identisch von F-8 (Exit-Kriterium) und F-10 (Exemption-Marker
der Gates) konsumiert — ein Vokabular, drei Konsumenten.

## Acceptance criteria

- [ ] **acceptance-1** Eine schriftliche Zähldefinition (Docstring der Scanner-Scripts) legt fest, was als Next-Occurrence-Berechnung zählt (Kadenz-Vorschub vs. legitime Offsets/TTLs) und welche Notification-Schreibklassen gegen die Grenze zählen (Propagations-Write) bzw. benannt außerhalb bleiben (Event-Erzeugung, Nutzer-Aktion); F-8 und F-10 referenzieren dieselbe Definition.
- [ ] **acceptance-2** `scripts/check_recurrence_boundary.py` und `scripts/check_notification_write_boundary.py` melden im Count-/Report-Modus die computed Zählungen (a) und (b) mit `file:line`-Attribution je Site; keine versionierte Konstante trägt die Baseline.
- [ ] **acceptance-3** Ein Ratchet-Test schlägt fehl, sobald eine der beiden Zählungen über die zur Testzeit gemessene Baseline wächst, und trägt eine Obsoleszenz-Regel: erreicht eine Zählung null, verlangt der Test seine eigene Ablösung durch den Zero-Threshold-Gate-Modus (F-10).
- [ ] **acceptance-4** Beide Scanner sind lokal über ein Task-Target ausführbar und drucken die Site-Liste; ein synthetischer Verstoß in einem Testbaum wird erkannt (Vakuum-Pin nach #946-Muster).

## Test hooks

- **acceptance-1** — Review der Definition + Referenz-Grep aus F-8/F-10-Artefakten — pending
- **acceptance-2** — Unit-Test der Scanner über tmp_path-Konstrukte (Load-by-Path, nie der reale Baum) — pending
- **acceptance-3** — Unit-Test Ratchet (Wachstum → rot; Obsoleszenz-Regel bei null) — pending
- **acceptance-4** — Task-Target-Aufruf + Vakuum-Pin-Test (synthetische Drift-Quelle → erkannt) — pending

## Consistency notes

**overlap F-6 ↔ F-10 (`proceed`, Rationale):** Beide Features arbeiten auf
derselben Erkennungslogik über dieselben zwei Eigenschaften. Die Phasen-Teilung
(erst zählen, zuletzt einfrieren) ist der bewusste Kern der
ADR-008-Migrationsskizze und bleibt bestehen — tragfähig wird sie durch die
geteilte Implementierung: F-6 liefert die `check_*.py`-Scripts mit
Count-/Ratchet-Modus, F-10 flippt **dieselben Scripts** auf Zero-Threshold in
der required Lane und löst den Ratchet-Test über dessen eigene Obsoleszenz-Regel
ab. Es gibt genau einen Scanner mit zwei Modi, nie zwei Implementierungen.

Die prior-art-Findings (NFR-018 §2.1, `check_schema_examples.py` als
Artefakt-Vorbild) bestätigen die Form; das drift-Finding (Zähldefinition nötig,
sonst Rauschen) ist als acceptance-1 in den Kern des Features gehoben.

## Risks

- Eine zu enge Zähldefinition versteckt echte Verstöße, eine zu weite ertränkt
  die Baseline in legitimen Offsets — die Definition ist darum ein eigenes,
  reviewbares AC und kein Implementierungsdetail.
- Scanner-Tests müssen gegen synthetische Bäume laufen (tmp_path), nie gegen den
  realen Baum — sonst bricht jeder unabhängige Refactor die Suite (#850-Lektion).
