---
id: F-7
title: Jede Wiederholung durch die eine RecurrenceEngine — abschluss-verankert
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
      target: src/backend/app/domain/services/care_reminder_service.py:1381
      resolution: proceed
      evidence: "Die abschluss-verankerte RRULE-Neuaufsetzung existiert für den WATERING-Pfad bereits (#510); der genuine Rest sind die übrigen Reminder-Typen, Saison/Winter, Sukzession, Inspektion, Tank."
    - kind: drift
      target: src/backend/app/domain/services/task_service.py:1132
      resolution: proceed
      evidence: "Generische Tasks sind heute faktisch abschluss-/jetzt-verankert (Engine seedet dtstart=now, kein DTSTART persistiert). Agent schlug revisit-after vor (Raster-Anker + Migration ODER Draft-Angleichung); Operator entschied 2026-08-10: Draft ans Ist-Verhalten angleichen, R5 des Requirements-Artefakts revidiert — beide Pfade abschluss-verankert, keine Migration."
    - kind: drift
      target: src/backend/app/domain/engines/care_reminder_engine.py:365
      resolution: proceed
      evidence: "Snooze-/Bootstrap-Arithmetik liegt dokumentiert in der Care-Engine ('cases a static RRULE cannot express'). Operator entschied 2026-08-10: Snooze wird als neu geseedete Regel (DTSTART=Snooze-Ziel) ausgedrückt; die dokumentierte Ausnahme wird abgelöst, Counter (a) erreicht echte Null."
    - kind: prior-art
      target: src/backend/app/domain/engines/succession_plan_engine.py:54
      resolution: proceed
      evidence: "Weitere Kadenz-Vorschübe jenseits der Draft-Aufzählung (succession, watering_schedule, watering_forecast, inspection_scheduler:54, tank_engine:492) — AC an die F-6-Baseline binden, nicht an eine Aufzählung."
    - kind: prior-art
      target: spec/req/REQ-006_Aufgabenplanung.md:178
      resolution: proceed
      evidence: "REQ-006 benennt die RecurrenceEngine bereits als einzige Recurrence-Autorität — F-7 setzt eine benannte Autorität durch, erfindet keine neue."
---

## Description

Jeder Pfad mit einer Kadenz — generische Aufgabe, Pflegeerinnerung, Saison- und
Winteraufgabe, Sukzessionssatz, Inspektions- und Tank-Wartungsintervall — drückt
sie als `RRULE` aus und lässt die `RecurrenceEngine` das Datum berechnen. Die
Care-Engine bleibt die fachliche Intervall-Autorität (sie sagt „alle 6 Tage",
die Engine sagt „also am 14."), verliert aber ihre eigene Datumsarithmetik:
auch Snooze wird zur neu geseedeten Regel statt zur Sonderrechnung. Für die
Gärtnerin ändert sich das sichtbare Verhalten nicht — die Fortschreibung ist
und bleibt abschluss-verankert (fällig Montag, gegossen Mittwoch, Intervall 6
Tage → nächste Fälligkeit Dienstag); neu ist, dass diese Semantik nur noch an
**einer** Stelle implementiert ist und nicht mehr driften kann (#508–#511).

Exit-Kriterium der Phase ist die F-6-Baseline (a) auf null — gebunden an die
Zählung, nicht an eine Aufzählung von Pfaden, damit auch die vom Review
gefundenen Nebenpfade (Inspektion, Tank) erfasst sind.

## Acceptance criteria

- [ ] **acceptance-1** Die F-6-Zählung (a) — Next-Occurrence-Berechnungen außerhalb der `RecurrenceEngine` — steht auf null; jeder Kadenz-Pfad (inkl. Sukzession, Inspektion, Tank-Wartung) bezieht Termine aus der Engine.
- [ ] **acceptance-2** Die Care-Engine bestimmt Intervalle (Saison/Phase/adaptiv) und drückt sie als `RRULE` aus; sie enthält keine eigene Datumsarithmetik mehr — Snooze ist eine neu geseedete Regel mit `DTSTART` = Snooze-Ziel, die dokumentierte Alt-Ausnahme ist abgelöst.
- [ ] **acceptance-3** Die Fortschreibung ist einheitlich abschluss-verankert (R5 rev. 2026-08-10): ein verspäteter Abschluss verschiebt die nächste Fälligkeit (fällig Mo, erledigt Mi, Intervall 6 → Di), für Care-Reminders und generische Tasks gleichermaßen, per Test gepinnt.
- [ ] **acceptance-4** Der Kalender-Export (REQ-015) bleibt unverändert: exportierte RRULE-Serien behalten ihre bisherige Form; ein Test belegt das.
- [ ] **acceptance-5** Verhaltensparität: die bestehenden Task- und Care-Recurrence-Suiten bleiben grün; kein Nutzer sieht andere Termine als vor der Konsolidierung.

## Test hooks

- **acceptance-1** — F-6-Scanner im Count-Modus: (a) == 0; Ratchet-Test-Obsoleszenz greift — pending
- **acceptance-2** — Unit-Tests Care-Engine (RRULE-Ausgabe; Snooze als Neuaufsetzung; kein timedelta-Vorschub) — pending
- **acceptance-3** — Unit-Test Anker-Semantik (Mo/Mi/6→Di) für beide Pfade — pending
- **acceptance-4** — Bestehende REQ-015-Export-Tests + gezielter Parity-Test — pending
- **acceptance-5** — Bestehende Recurrence-Suiten (`test_task_service`-Recurrence, Care-Suiten) — pending

## Consistency notes

**drift Task-Anker (`proceed` nach Operator-Entscheidung):** Der Agent stellte
fest, dass „raster-verankerte" generische Tasks eine Verhaltens- und
Datenmodell-Änderung wären (kein DTSTART persistiert; Engine seedet bei
„jetzt"), und eskalierte als `revisit-after`. Der Operator entschied am
2026-08-10: **Draft ans Ist-Verhalten angleichen** — beide Pfade
abschluss-verankert, keine Migration, kein Terminsprung für Bestandsserien; R5
des Requirements-Artefakts wurde entsprechend revidiert (Revisionsvermerk dort).
Der ursprüngliche Agenten-Vorschlag bleibt als Audit-Trail im Finding erhalten.

**drift Snooze-Grenze (`proceed` nach Operator-Entscheidung):** Die
dokumentierte Care-Engine-Ausnahme („cases a static RRULE cannot express") wird
nicht als Exemption weitergetragen, sondern abgelöst: Snooze wird als neu
geseedete Regel ausgedrückt — Counter (a) erreicht echte Null ohne benannte
Ausnahme.

Prior-art: der WATERING-Pfad trägt die Zielform bereits (#510); REQ-006 benennt
die Engine als einzige Autorität; die Pfad-Unterzählung der Draft-Aufzählung ist
durch die Bindung an die F-6-Baseline (acceptance-1) neutralisiert.

## Risks

- Die Snooze-Ablösung berührt dokumentiertes Verhalten — der bestehende
  Docstring-Kontrakt in `care_reminder_service.py` muss mitgezogen werden,
  sonst widersprechen Code-Kommentar und Implementierung.
- Verhaltensparität (acceptance-5) ist die Wache gegen stille Semantikwechsel;
  schlägt eine Bestandssuite an, ist das ein Befund, keine anzupassende Suite.
