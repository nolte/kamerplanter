---
id: F-30
title: Gießerinnerung nach gemessenem Regen verschieben
status: draft
roadmap_item: R-27
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: acceptance-1
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@5d01b6c4
  findings:
    - kind: prior-art
      target: src/backend/app/domain/engines/care_reminder_engine.py:656
      resolution: proceed
      evidence: "should_generate_reminder suppresses WATERING when irrigation_demand_capped_mm <= 0, but its only input (care_reminder_service.py:1626) is never populated — implemented but inert; operator decision D5: the deferral replaces this dead path (acceptance-5)."
    - kind: drift
      target: spec/req/REQ-005_Hybrid-Sensorik.md:127
      resolution: proceed
      evidence: "REQ-005 G-010 defers on > 5 mm forecast rain; operator decision D3: that rule stays, F-30's freshness condition covers only deferrals because of measured rain (acceptance-3); agent proposed revisit-after operator decision."
    - kind: drift
      target: spec/req/REQ-022_Pflegeerinnerungen.md:1006
      resolution: proceed
      evidence: "ADR-008 boundaries 1 and 3 (no own date arithmetic, follow-ups only via NotificationPropagationService) bind the deferral (acceptance-4, D5)."
    - kind: drift
      target: spec/req/REQ-022_Pflegeerinnerungen.md:995
      resolution: proceed
      evidence: "snooze_days is 1..7 and snooze excludes adaptive learning (:1386); the deferral is not a snooze and does not feed ADAPTIVE_* (acceptance-4)."
    - kind: prior-art
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:390
      resolution: proceed
      evidence: "§3.4 specifies 'net_demand_mm_capped == 0 → suppress' and a 'regenbedingt verschoben' badge (:401); F-30 turns suppression into deferral with annotation and restore — REQ-037 §3.4 amended (acceptance-6)."
    - kind: drift
      target: spec/req/REQ-037_Evapotranspiration-Bewaesserung.md:400
      resolution: split-out F-31
      evidence: "No water-balance widget and no irrigation_demands read endpoint exist (REQ-037:462); split out as F-31 before F-30 (operator decision D4)."
    - kind: overlap
      target: F-7
      resolution: proceed
      evidence: "F-7 acceptance-2 expresses snooze as a reseeded RRULE (DTSTART = target); the deferral uses the same shape so F-10's gate (a) accepts it."
    - kind: overlap
      target: F-24
      resolution: proceed
      evidence: "F-24 shows watering reminders with confirm/snooze on the care-dashboard endpoint (schemas.py:148); the annotation and restore action appear in the same widget and payload."
    - kind: prior-art
      target: src/backend/app/domain/models/irrigation_zone.py:267
      resolution: proceed
      evidence: "A rain-skipped zone round (GP-FR-117) leaves open watering tasks open; acceptance-7 states how a deferred bed reminder and a skipped round interact."
---

## Description

Hat es nachweislich geregnet, obwohl die Prognose trocken war, erinnert
Kamerplanter heute trotzdem ans Gießen. Eine Unterdrückung bei gedecktem Bedarf
ist zwar angelegt, bekommt aber nie Daten und wirkt deshalb nicht.

Nach dieser Änderung verschiebt Kamerplanter eine fällige Gießerinnerung auf
den ersten Tag, an dem die Bodenwasser-Bilanz (F-29) wieder Bedarf zeigt. Wegen
gemessenem Regen geschieht das nur, wenn ein frischer Messwert (F-28) den
Zeitraum abdeckt; die Verschiebung nach Prognose (REQ-005 G-010) bleibt
unverändert. Die Erinnerung trägt einen Vermerk mit Menge und Quelle, und der
Nutzer kann sie zurückholen. Die Verschiebung nutzt den Wiederholungsmechanismus
der Pflegeerinnerungen und rechnet kein eigenes Datum.

## Acceptance criteria

- [ ] **acceptance-1** Nach gemessenem Regen, der den Bedarf deckt, ist die fällige Gießerinnerung auf den ersten Tag mit Bedarf verschoben, und ihr Vermerk nennt Menge und Quelle (z. B. „verschoben: 12 mm Regen, Netatmo“).
- [ ] **acceptance-2** Der Nutzer kann eine verschobene Erinnerung zurückholen; sie ist danach wieder zum ursprünglichen Termin fällig und wird für denselben Regen nicht erneut verschoben.
- [ ] **acceptance-3** Ohne frischen Messwert (F-29 acceptance-3) wird keine Erinnerung wegen gemessenem Regen verschoben; die Verschiebung nach Prognose (REQ-005 G-010) bleibt davon unberührt.
- [ ] **acceptance-4** Die Verschiebung setzt die Wiederholung neu an wie das Schlummern in F-7 (neu gesetzte RRULE), rechnet kein eigenes Datum, benachrichtigt nur über `NotificationPropagationService`, ist nicht auf 7 Tage begrenzt und fließt nicht ins adaptive Lernen ein (ADR-008, REQ-022 §0).
- [ ] **acceptance-5** Die bisher wirkungslose Unterdrückung (`care_reminder_engine.py:656`) ist durch die Verschiebung ersetzt; kein zweiter Pfad entscheidet über dieselbe Erinnerung.
- [ ] **acceptance-6** REQ-037 §3.4 beschreibt Verschieben statt Unterdrücken; Beschriftungen (DE + EN) und Nutzerdoku beschreiben Verschieben und Zurückholen; Vermerk und Zurückholen erscheinen auch im Pflege-Widget (F-24).
- [ ] **acceptance-7** Eine wegen Regen übersprungene Zonen-Runde (GP-FR-117) und eine verschobene Beet-Erinnerung widersprechen sich nicht: Die verschobene Erinnerung bleibt verschoben, die Runde bleibt dokumentiert.

## Test hooks

- **acceptance-1** — service test: measured rain covers demand → reminder deferred with annotation; E2E on the reminder list — pending
- **acceptance-2** — service + vitest: restore, no re-deferral for the same rainfall — pending
- **acceptance-3** — service tests: stale / missing measurement → no measured deferral; forecast rule unchanged — pending
- **acceptance-4** — unit test of the RRULE reseed; guard of F-10 gate (a) green; no ADAPTIVE_* write — pending
- **acceptance-5** — guard/test: the engine's suppression input removed or fed by the deferral only — pending
- **acceptance-6** — spec diff + i18n completeness + `mkdocs build --strict` + vitest on the care widget — pending
- **acceptance-7** — service test combining a skipped zone round and a deferred bed reminder — pending

## Consistency notes

**Inert suppression (proceed, D5).** Established: `should_generate_reminder`
suppresses watering when `irrigation_demand_capped_mm <= 0`
(`care_reminder_engine.py:656-663`), but the only caller reads a key nothing
populates (`care_reminder_service.py:1626`), and the nightly path skips watering
(`care_tasks.py:199-202`). The docstrings (`irrigation_demand.py:13-14`,
REQ-037:462) claim a wiring that does not exist. F-30 replaces the dead path
rather than building a second one beside it.

**REQ-005 G-010 (proceed, D3).** The forecast deferral (> 5 mm) stays as
specified; the interview requirement R7 is narrowed to deferrals because of
measured rain.

**ADR-008 boundaries (proceed, D5).** Binding regardless of #1061 being on hold:
no own date arithmetic, follow-ups only through `NotificationPropagationService`;
the deferral is not a snooze (`snooze_days` 1..7, `:995`) and stays out of
adaptive learning (`:1386`).

**Overlap with F-7 (proceed).** F-7 expresses snooze as a reseeded RRULE; the
deferral takes the same shape so F-10's gate (a) does not flag it. F-7 does not
need to land first: the reseed shape is the contract, whichever lands first
provides it.

**Overlap with F-24 (proceed).** F-24's care widget shows watering reminders
with confirm/snooze; the annotation and the restore action belong in the same
payload (acceptance-6).

**Widget split out (split-out F-31, D4).** The water-balance widget and its read
endpoint do not exist; they become F-31, ordered before F-30.

## Risks

- Assumption A2: reuses the existing care-reminder scheduling (REQ-022) within the ADR-008 boundaries.

## References

- Issue #3002, roadmap item R-27, REQ-037 §3.4, REQ-022 §0, REQ-005 G-010
- `project/requirements/measured-rain-soil-water-balance.md` (R6, R7)
