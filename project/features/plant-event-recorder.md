---
id: F-25
title: Ereignis-Recorder und Anbindungs-Inventar
status: draft
roadmap_item: R-23
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@4a3321288
  findings:
    - kind: overlap
      target: F-9
      resolution: proceed
      evidence: "F-9 moves care confirm/complete into one stream transaction (atomic-completion-transition.md:55-59); the care_done source (REQ-055 §11.2:443) is written there, and PS-EVT-015 (REQ-055:492) forbids the recorder from blocking the business write; operator decision: recorder after commit, best-effort, reconciliation catches misses."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:418
      resolution: proceed
      evidence: "Unique index (source_collection, source_key, event_type) vs. WateringEvent.slot_keys/plant_keys lists (watering_event.py:33-37) and FeedingEvent.plant_keys (feeding_event.py:39); operator decision: one event per plant, plant_instance_key in the index, slots resolved to plants on write."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:436
      resolution: proceed
      evidence: "'every MVP source' includes identity_created (wave 2), digest (wave 3) and aliases germinated/flowering_started of one phase_histories document (§11.2:436-464); operator decision: wave-1 sources only, aliases are labels of the phase change."
    - kind: prior-art
      target: src/backend/app/domain/services/plant_instance_service.py:374
      resolution: proceed
      evidence: "No location history or move time (v0112_placed_in_backfill.py:14); only slot moves write a placed_in edge since #2948; operator decision: wave 1 records slot moves via placed_in from introduction on (O-19), location-only moves later."
    - kind: prior-art
      target: src/backend/tests/unit/guards/test_tenant_erasure_inventory_is_complete.py:68
      resolution: proceed
      evidence: "Every new collection fails until classified; test_tenant_export_covers_the_inventory.py:6-25 adds AK-29/AK-31; source_ref.key, attachment_ids, aggregated_into need manual references_of entries."
    - kind: drift
      target: spec/req/REQ-055_Plant-Identity-Plant-Social.md:2001
      resolution: proceed
      evidence: "§37 puts field-level GDPR integration in wave 2; the inventory guard forces it into wave 1; PS-PRI-051 (:963) needs USER_DATA_MANIFEST (data_export_engine.py:113) for actor.user_key; performed_by_label carries names (watering_event.py:58-60); operator decision: pull forward, amend §37."
    - kind: prior-art
      target: project/features/plant-photo-upload.md:73
      resolution: proceed
      evidence: "F-1 acceptance-6 hard-deletes a plant incl. photos; REQ-055:982 says plant_events follow the plant — extend test_plant_instance_delete_cascade.py; tombstones only for deleted sources."
    - kind: prior-art
      target: spec/req/REQ-051_Pflanzen-Tagebuch.md:876
      resolution: proceed
      evidence: "milestone_kind is specified in REQ-051 v1.3 (422 diary.milestone_kind_requires_milestone), no code yet; DiaryEntryType.MILESTONE exists (enums.py:619); next free migration v0115."
---

## Description

Was mit einer Pflanze passiert, steht heute verstreut: im Tagebuch, in
Gieß- und Düngeprotokollen, in der Phasenhistorie, bei den Fotos und der
Ernte. Eine gemeinsame, chronologische Spur gibt es nicht.

Dieses Feature legt einen Ereignisindex an. Jede Quelle meldet nach ihrem
eigenen Speichern ein Ereignis je betroffener Pflanze — mit dem fachlichen
Zeitpunkt, wer oder was es ausgelöst hat (Mensch, Kamerplanter, Sensor,
Automation …) und einer Einstufung jedes Feldes danach, ob es je öffentlich
werden darf. Ein Ereignis entsteht nie auf einem zweiten Weg; bearbeitete
Quellen erhöhen eine Version, gelöschte Quellen verschwinden aus der Spur. Ein
Prüftest stellt sicher, dass keine Quelle vergessen wird. Die Ereignisse sind
von Anfang an in Löschung und Datenauskunft eingebunden. Das Tagebuch erhält
die Art des Meilensteins (neues Blatt, Blüte, Frucht …).

## Acceptance criteria

- [ ] **acceptance-1** Jede bestehende Quelle (Tagebuch inkl. Meilensteine, Gießen, Düngen, Phasenwechsel, Foto, Ernte, Pflege-Bestätigung, Behandlung, Diagnose, Vermehrung, Umsetzen zwischen Slots) erzeugt nach ihrem eigenen erfolgreichen Speichern genau ein Ereignis je betroffener Pflanze, mit Herkunft und Akteur; Keimung und Blühbeginn sind Bezeichnungen des Phasenwechsels, keine eigenen Ereignisse.
- [ ] **acceptance-2** Schlägt das Schreiben eines Ereignisses fehl, bleibt die fachliche Aktion gespeichert; der Abgleich (F-26) holt das Ereignis nach.
- [ ] **acceptance-3** Wird eine Quelle bearbeitet, steigt die Version ihres Ereignisses; wird sie gelöscht, verschwindet das Ereignis aus dem Verlauf; wird die Pflanze gelöscht, werden ihre Ereignisse mitgelöscht.
- [ ] **acceptance-4** Ein Prüftest schlägt fehl, sobald eine Quellcollection ohne Ereignis-Aufruf bleibt; der Recorder ist der einzige Schreiber, unbekannte Ereignistypen werden abgewiesen, und jedes Feld jedes Ereignistyps ist als öffentlich zulässig, optional oder nie öffentlich eingestuft.
- [ ] **acceptance-5** Ein Tagebucheintrag vom Typ Meilenstein kann die Art des Meilensteins tragen (REQ-051 v1.3).
- [ ] **acceptance-6** Ereignisse werden mit dem Mandanten gelöscht, der Akteur (Nutzerbezug und Namensangabe) wird bei Kontolöschung feldgenau entfernt, sie erscheinen in der Datenauskunft des Nutzers und sind vom Mandanten-Archiv ausgeschlossen (Neuaufbau nach Import über F-26); REQ-055 §37 ist entsprechend angepasst.

## Test hooks

- **acceptance-1** — service tests per source incl. watering with several slots → one event per plant — pending
- **acceptance-2** — test: recorder failure after commit leaves the source document in place — pending
- **acceptance-3** — tests for payload_version, source_deleted_at and the plant delete cascade (`test_plant_instance_delete_cascade.py`) — pending
- **acceptance-4** — new guard after the pattern of `test_tenant_erasure_inventory_is_complete.py`; enum test for unknown types; payload field-class test — pending
- **acceptance-5** — diary tests incl. 422 `diary.milestone_kind_requires_milestone` — pending
- **acceptance-6** — erasure inventory/export guards, account-erasure field test, Art. 15 manifest test — pending

## Consistency notes

**Overlap with F-9 (proceed).** Established: F-9 moves care confirmation and
task completion into one stream transaction
(`atomic-completion-transition.md:55-59`), which writes the `care_done`
source (REQ-055 §11.2 `:443`); PS-EVT-015 (`:492`) forbids the recorder from
blocking the business write. Rationale for `proceed`: operator decision
2026-11-17 — the recorder runs after the commit, best-effort, and the F-26
reconciliation catches misses. F-25 therefore does not depend on F-9's
transaction and the order of F-9 and F-25 does not matter; the guard
(acceptance-4) anchors on the source collection, not on a service file, so it
survives F-9 moving the write. Unestablished: whether a failed insert inside
an ArangoDB stream transaction would abort F-9's transition — moot with the
after-commit call.

**Fan-out (drift, proceed).** Established: watering and feeding documents
cover several plants (`watering_event.py:33-37`, `feeding_event.py:39`) while
REQ-055's unique index (`:418`) assumes one event per source. Operator decision
2026-11-17: one event per plant, `plant_instance_key` joins the unique index,
slots are resolved to plants on write.

**Wave-1 sources (drift, proceed).** Established: §11.2 (`:436-464`) also
lists `identity_created` (wave 2), `digest` (wave 3) and the aliases
`germinated`/`flowering_started` of one phase document. Operator decision
2026-11-17: only existing sources; the aliases are labels of the phase change
(acceptance-1).

**moved (prior-art, proceed).** Established: there is no location history or
move time (`plant_instance_service.py:374-441`,
`v0112_placed_in_backfill.py:14`); since #2948 only slot moves write a
`placed_in` edge. Operator decision 2026-11-17: wave 1 records slot moves via
`placed_in` from introduction on (O-19, no backfill); location-only moves
follow with a location history.

**Inventory guards (prior-art, proceed).** Established: the erasure inventory
guard (`test_tenant_erasure_inventory_is_complete.py:68-69`) and the export
guard (`test_tenant_export_covers_the_inventory.py:6-25`) fail on any new
collection until classified; `source_ref.key`, `attachment_ids` and
`aggregated_into` need manual `references_of` entries.

**GDPR pulled into wave 1 (drift, proceed).** Established: §37 (`:2001`) puts
the field-level GDPR integration in wave 2, but the guards force it now;
PS-PRI-051 (`:963`) needs the Art. 15 manifest
(`data_export_engine.py:113`), and `performed_by_label` carries person names
(`watering_event.py:58-60`). Operator decision 2026-11-17: pulled forward,
excluded from the tenant archive and rebuilt after import, §37 amended
(acceptance-6).

**Plant delete cascade (prior-art, proceed).** Established: F-1
acceptance-6 hard-deletes a plant with its photos
(`plant-photo-upload.md:73`) and REQ-055 (`:982`) lets events follow the
plant; the cascade test is extended (acceptance-3).

**milestone_kind (prior-art, proceed).** Established: specified in REQ-051
v1.3 (`:876`), not implemented; `DiaryEntryType.MILESTONE` exists
(`enums.py:619`); the next free migration is v0115.

## Risks

- After-commit recording can miss events on a crash; the reconciliation interval bounds the gap.
- Origin `automation` for HA/actuator-triggered watering needs a source field that `watering_event.py` does not carry yet (unestablished, REQ-018 path not traced).

## References

- REQ-055 v1.5 §10, §11, §22, §24, §37; #2140/#2141 (later waves)
- Roadmap item R-23; requirement gate: operator override 2026-11-17 (REQ-055 v1.5 as basis)

## Betreiberentscheidungen 2026-11-27

- Wer ein Ereignis ausgeführt hat, wird nur nach der bestehenden Sichtbarkeitsmatrix gezeigt (`spec/privacy/05-access-and-visibility.md`), nicht jedem Mitglied. Das Ereignis speichert die ausführende Person weiterhin; die Projektion für den Verlauf (F-27) entscheidet über die Anzeige.
