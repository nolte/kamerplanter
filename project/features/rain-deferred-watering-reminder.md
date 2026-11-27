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
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/backend/app/domain/services/care_reminder_service.py:852
      resolution: revisit-after Betreiberentscheidung "Verschieben = Umterminieren (Stufe bleibt) oder neues Vorkommen (Stufe zurück)" + Edit acceptance-4
      evidence: "_retime_care_task rechnet das Datum selbst über _compute_care_reschedule (:1028-1038, Anker letzte Bestätigung); es gibt keinen Weg, ein Zieldatum aus der Bilanz zu übergeben. RecurrenceEngine.next_occurrence(rule, after) (recurrence_engine.py:77) kennt kein DTSTART-Reseed."
    - kind: drift
      target: src/backend/app/domain/services/care_reminder_service.py:929
      resolution: revisit-after Edit acceptance-5 (alle Umterminierer nennen)
      evidence: "redetermine_open_care_task (only_if_changed) und update_profile (:751) rechnen den Termin aus der Bestätigung neu und würden eine Verschiebung zurücksetzen; der Verschiebe-Zustand ist nirgends gespeichert (Task-Modell task.py:132-207 ohne Feld für Vermerk oder Ursprungstermin)."
    - kind: drift
      target: src/backend/app/domain/services/care_reminder_service.py:1789
      resolution: revisit-after Edit acceptance-1/-5
      evidence: "_dashboard_entries leitet due_date und urgency aus der letzten Bestätigung ab, unabhängig von der Aufgabe; eine umterminierte Aufgabe bleibt im Pflege-Dashboard fällig. Hier sitzt auch die wirkungslose Unterdrückung (:1784)."
    - kind: drift
      target: spec/req/REQ-005_Hybrid-Sensorik.md:128
      resolution: revisit-after Edit acceptance-3
      evidence: "'Bei >5mm Regen in den nächsten 24h wird die Erinnerung unterdrückt' - im Care-Code gibt es keinen Prognose-Leser (Grep rain|precip|forecast in care_reminder_engine.py und care_reminder_service.py: nur der ET-Parameter). 'Bleibt unverändert' ist leer, der Test 'forecast rule unchanged' beweist nichts."
    - kind: drift
      target: src/backend/app/tasks/care_tasks.py:170
      resolution: "revisit-after Betreiberentscheidung \"Geltungsbereich: auch Gießplan-Aufgaben?\""
      evidence: "Pflanzen mit aktivem Gießplan bekommen keine Pflege-Gießaufgabe (plants_with_schedule :73); ihre Aufgaben erzeugt watering-generate-tasks-daily (tasks/__init__.py:501). Der Bedarf entsteht je Run (irrigation_tasks.py:100) - gerade Run-Pflanzen mit Gießplan erfasst F-30 nicht, Pflanzen ohne Run haben keinen Bedarf."
    - kind: prior-art
      target: src/backend/app/domain/services/watering_service.py:496
      resolution: proceed
      evidence: "_latest_irrigation_demand_ml löst Pflanze -> Run -> neuester Bedarf auf (get_runs_for_plant, get_latest_for_run) - die Vorlage für die Zuordnung Erinnerung <-> Bedarf."
    - kind: prior-art
      target: src/backend/app/domain/services/notification_propagation_service.py:340
      resolution: proceed
      evidence: "sync_care_notification baut data mit festen Schlüsseln (plant_key, reminder_type, task_key, due_date, action_url); ein Vermerk in der Benachrichtigung braucht eine Erweiterung dieses einen Besitzers (Grenze 3)."
    - kind: prior-art
      target: scripts/check_recurrence_boundary.py:1
      resolution: proceed
      evidence: "Der Scanner zu Gate (a) existiert (daneben check_notification_write_boundary.py, laut F-8 '0 offen'); der Test-Hook kann ihn nennen statt 'guard of F-10', das noch draft ist."
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

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`; same run, triggers and caveats as recorded in `site-rain-sensor.md` (no test run; resolutions are proposals; line references into this file are those of `cc8531492`). The frontmatter holds the eight findings of this run; the nine findings of 2026-11-17 (`feature-consistency-reviewer@5d01b6c4`) are listed with their fate. The report's verdict: **blocked** on two operator decisions, see the German section below. "ADR-008 is not a precondition" agrees with the notes above and with A2; REQ-022 v3.0 lists ADR-008 as Accepted (`:1000-1009`).

**Findings of 2026-11-17 — fate.**

1. `care_reminder_engine.py:656`, `care_reminder_service.py:1626`, `care_tasks.py:199-202` (prior-art, proceed) — engine unchanged (`:656-663`). Service moved to `:1784`; `_build_plant_data_for_tenant` (`:1842` ff.) does not fill the key — still inert. `care_tasks.py` moved to `:200-203`.
2. `REQ-005:127`, G-010 (drift, proceed) — moved to `:128` (table `:99`). New: not implemented in the code, see the G-010 finding below.
3. `REQ-022:1006` (drift, proceed) — still true (boundary 1 `:1006`, boundary 3 `:1008`).
4. `REQ-022:995`, `:1386` (drift, proceed) — `:995` still true; `:1386` moved to about `:1385`.
5. `REQ-037:390` / `:401` (prior-art, proceed) — moved to `:393` and `:402`.
6. `REQ-037:400` / `:462` (drift, split-out F-31) — moved to `:401` and `:463`. Still true.
7. Overlap F-7 (proceed) — F-7 is still `draft`. Snooze is not a reseeded RRULE (`_next_watering_due_date` `:2297-2307` stays in the care engine), and `snooze_reminder` (`:1700-1725`) only writes a confirmation and does not retime the task. The shape exists nowhere; F-30 would have to build it itself. The note "Overlap with F-7" above no longer carries as written.
8. Overlap F-24 (proceed) — F-24 still `draft`; `CareDashboardEntryResponse` is at `schemas.py:148`. Still true.
9. `irrigation_zone.py:267` (prior-art, proceed) — still true (`:267-273`).

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
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
```

**What "defer" maps onto today.** The description ("uses the recurrence mechanism", "like snoozing in F-7") does not fit the existing paths. There are two mechanisms:

- **A — retiming the same task.** `CareReminderService._retime_care_task` (`:822`) → `_propagate_care_reschedule(..., announces_new_task=False)` (`:974`) → `NotificationPropagationService.sync_care_notification(reset_read=False)` (`notification_propagation_service.py:294`). Effect on escalation: the level stays, levels already sent are not repeated (`:324-329`). Existing "overdue" rows of the group are **not** settled; that happens only on `new_occurrence` (`:360-363`). A parallel escalation run writes nothing because `on_notification_escalated` requires the announced `due_date` (`:501-512`).
- **B — closing and a new occurrence.** `_close_care_task_without_care` (`:943`; SKIPPED, `on_task_completed` settles the group including escalations) → `_materialise_next_watering_task` (`:793`) or `ensure_and_announce_next_watering_task` (`:2196`), with `reset_read=True` and `_reset_escalation` (`:375`).

A fits acceptance-2 (the same task, the original date restorable). B fails without a new anchor: the next date is computed from the last real confirmation (`:2168-2180`) and would be due again at once; a rain "confirmation" as anchor would flow into adaptive learning (warning in the docstring `:953-957`). Open in substance for A: if level 1 was sent before the rain, the "overdue" rows stay visible although the rain covered the demand, and after the next dry spell the HIGH level is not sent again.

**New findings.**

- **No way to pass a target date (drift, `care_reminder_service.py:852`).** `_retime_care_task` computes the date itself through `_compute_care_reschedule` (`:1028-1038`, anchor: last confirmation); a target date from the balance cannot be handed in. `RecurrenceEngine.next_occurrence(rule, after)` (`recurrence_engine.py:77`) knows no DTSTART reseed. Blocked on the decision "defer = retime (level stays) or new occurrence (level reset)", then an edit of acceptance-4.
- **Other retimers would undo a deferral (drift, `care_reminder_service.py:929`).** `redetermine_open_care_task` (`only_if_changed`) and `update_profile` (`:751`) recompute the date from the confirmation; the deferral state is stored nowhere (task model `task.py:132-207` has no field for the annotation or the original date). acceptance-5 should name every retimer.
- **The care dashboard ignores the task (drift, `care_reminder_service.py:1789`).** `_dashboard_entries` derives `due_date` and `urgency` from the last confirmation, independent of the task; a retimed task stays due in the care dashboard. The inert suppression sits here too (`:1784`). Edits of acceptance-1/-5.
- **G-010 is not built (drift, `REQ-005:128`).** "Bei >5mm Regen in den nächsten 24h wird die Erinnerung unterdrückt" — the care code has no forecast reader (grep for rain|precip|forecast in `care_reminder_engine.py` and `care_reminder_service.py` finds only the ET parameter). "Stays unchanged" is empty, and the test "forecast rule unchanged" proves nothing. acceptance-3 has to be detached from it.
- **Scope: watering-plan tasks (drift, `care_tasks.py:170`).** Plants with an active watering plan get no care watering task (`plants_with_schedule` `:73`); their tasks come from `watering-generate-tasks-daily` (`tasks/__init__.py:501`). The demand arises per run (`irrigation_tasks.py:100`) — F-30 does not reach exactly the run plants with a watering plan, and plants without a run have no demand. Operator decision.
- **Template for reminder ↔ demand (prior-art, proceed, `watering_service.py:496`).** `_latest_irrigation_demand_ml` resolves plant → run → latest demand (`get_runs_for_plant`, `get_latest_for_run`).
- **One owner of the notification payload (prior-art, proceed, `notification_propagation_service.py:340`).** `sync_care_notification` builds `data` with fixed keys (`plant_key`, `reminder_type`, `task_key`, `due_date`, `action_url`); an annotation in the notification needs an extension of this one owner (boundary 3).
- **The scanner for gate (a) exists (prior-art, proceed, `scripts/check_recurrence_boundary.py:1`).** Beside it `check_notification_write_boundary.py` (per F-8 "0 open"); the test hook can name the scanner instead of "guard of F-10", which is still draft.

**Further discussion.**

- **Functions F-30 would call or extend on path A.** A new service entry after the pattern of `redetermine_open_care_task` (`tenant_key` keyword-only, #2107), with `find_open_care_task(..., include_completed_today=False)` and only for `PENDING`; a variant of `_retime_care_task` with a given target date; `_propagate_care_reschedule` → `sync_care_notification`, extended by the annotation and possibly by "settle escalation rows without resetting the level"; for the restore the same chain with the stored original date; for the dashboard feeding `_dashboard_entries` instead of the dead parameter. `dispatch_due_care` (06:05 UTC, `notification_tasks.py:165`) reads tasks due today; a retimed task triggers nothing there.
- **Trigger time.** The file names none. The care beat runs every 86400 s from worker start (`tasks/__init__.py:496-499`), not coupled to the weather fetch. Sensible would be the chain fetch → `compute_irrigation_demand` → deferral (after `_dispatch_followups`, `weather_tasks.py:150`); otherwise the 6-hour freshness decides by chance.
- **Sprint-value verifier.** acceptance-1 is the right choice but does not prove the whole chain: the hook ("service test: measured rain covers demand") can stub the demand, and the criterion names neither the dry forecast nor the notification. For R-27 it would have to read: from an HA reading (stubbed client) a deferred task arises through sum, `observed` record and balance, whose `care.watering` row carries the new date and which is no longer due in the care dashboard although the forecast said 0 mm — an integration test across F-28 to F-30.
- **acceptance-2.** "Not again for the same rain" needs an identity of the rain event (for example the day or period of the measurement).

**Already implemented:** the propagation owner, retiming with notification, SKIPPED closing, announcing new occurrences, the escalation claim. **New:** target date from the balance, stored deferral state, annotation, restore, feeding the dashboard.

**Cross-feature.** F-30 presupposes F-28 (measured rain) and F-29 (demand threshold, look-ahead); both are now recorded under References. F-31 is no technical precondition (acceptance-6 refers to F-24), the roadmap order F-28, F-29, F-31, F-30 (D4) stays defensible. The common gaps, the spec follow-up outside any criterion (among them `REQ-037:383` calling the non-existent `care_reminder_service.apply_irrigation_demand()` and G-010) and the comparison with issue #3002 are in `site-rain-sensor.md`. The issue's "the postponement uses the existing care scheduling" decides neither of the two open points below. Deferred in this run: acceptance-7 (zone round) was read only against the model, not the service; the documentation content of acceptance-6 was not read.

**Edits required before `ready`** (the report's verdict for F-30, translated): blocked on the two decisions; presupposes F-28 and F-29. After them:

1. Rewrite the description and acceptance-4 onto the real paths.
2. Extend acceptance-5 by all retimers and the care dashboard.
3. Detach acceptance-3 from the unbuilt G-010 rule.
4. Word acceptance-1 as a proof of the chain.
5. Name the trigger time.

## Risks

- Assumption A2: reuses the existing care-reminder scheduling (REQ-022) within the ADR-008 boundaries.

## References

- Issue #3002, roadmap item R-27, REQ-037 §3.4, REQ-022 §0, REQ-005 G-010
- `project/requirements/measured-rain-soil-water-balance.md` (R6, R7)
- Depends on F-28 (measured rain) and F-29 (demand threshold, look-ahead) — recorded by the consistency re-run 2026-11-27

## Betreiberentscheidungen 2026-11-27

- ADR-008 ist keine Vorbedingung.
- Die Datenfrische von 6 Stunden ist fest.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

F-30 ist auf beide Entscheidungen blockiert.

- **(1) Verschieben = dieselbe Aufgabe umterminieren oder ein neues Vorkommen?** Heute gibt es beide Wege, aber keinen, der ein Zieldatum aus der Bilanz annimmt (`care_reminder_service.py:852`, `:1028-1038`); ein Verschiebe-Zustand wird nirgends gespeichert (`task.py:132-207`).
  - **Umterminieren (Stufe bleibt; `_retime_care_task :822`, `sync_care_notification(reset_read=False)` `notification_propagation_service.py:294`):** Passt zu acceptance-2 (dieselbe Aufgabe, Ursprungstermin wiederherstellbar); bereits gesendete Eskalationsstufen werden nicht wiederholt (`:324-329`), nach der nächsten Trockenphase kommt die HIGH-Stufe also nicht erneut.
  - **Neues Vorkommen (Stufe zurück; `_close_care_task_without_care :943`, `_reset_escalation :375`):** Die Eskalation beginnt neu; ohne neuen Anker wäre das Vorkommen sofort wieder fällig (`:2168-2180`), und eine Regen-„Bestätigung“ als Anker flösse ins adaptive Lernen (`:953-957`).
  - **Dazu: Was geschieht mit bereits gesendeten „Überfällig“-Zeilen?** Beim Umterminieren bleiben sie heute sichtbar, obwohl der Regen den Bedarf gedeckt hat (erledigt werden sie nur bei `new_occurrence`, `:360-363`). Entweder so lassen oder sie erledigen, ohne die Stufe zurückzusetzen (Erweiterung von `sync_care_notification`).
- **(2) Geltungsbereich: nur Pflege-Erinnerungen oder auch Gießplan-Aufgaben der Runs?** Heute bekommen Pflanzen mit aktivem Gießplan keine Pflege-Gießaufgabe (`care_tasks.py:73`, `:170`); ihre Aufgaben erzeugt `watering-generate-tasks-daily` (`tasks/__init__.py:501`). Der Bedarf entsteht je Run (`irrigation_tasks.py:100`).
  - **Nur Pflege-Erinnerungen:** Gerade Run-Pflanzen mit Gießplan erfasst F-30 nicht, und Pflanzen ohne Run haben keinen Bedarf — die Verschiebung träfe kaum eine Aufgabe.
  - **Auch Gießplan-Aufgaben:** F-30 muss einen zweiten Aufgaben-Erzeuger verschieben; der Umfang wächst über die Pflege-Erinnerungen (REQ-022) hinaus.
