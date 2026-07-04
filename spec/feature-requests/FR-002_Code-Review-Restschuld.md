# Feature-Request: FR-002 — Code-Review-Restschuld (verhaltensändernde Refactoring-Vervollständigung)

```yaml
ID: FR-002
Titel: Vervollständigung der zurückgestellten, nicht-verhaltensneutralen Refactorings aus dem Fable-5-Code-Review
Typ: Feature-Request (technische Qualität / Wartbarkeit)
Status: Vorgeschlagen
Eingereicht: 2026-07-04
Betroffene Zielgruppen: Entwicklung & Wartung (kein direkter Endnutzer-Impact)
Verwandte Anforderungen: NFR-001 (5-Schicht-Architektur), NFR-003 (Code-Sprache/-Qualität); Review-Findings DUP-B1/B6 (Base-Repository), FE-D5 (List-Slice-Factory)
Herkunft: Code-Review-Report spec/analysis/code-review-fable5-2026-07.md; Umsetzungspläne spec/analysis/code-review-fable5-plans/
Resultierende Spezifikation: — (dieser Request ist zugleich die Arbeitsbeschreibung; keine eigene REQ nötig)
GitHub-Issue: https://github.com/nolte/kamerplanter/issues/350
Tracking-Kontext: https://github.com/nolte/kamerplanter/issues/318 (AP-1..21 + Follow-ups, alle gemergt)
```

## Problem / Motivation

Der Fable-5-Code-Review (AP-1..21) und seine sieben dokumentierten Follow-ups sind
vollständig umgesetzt und gemergt. Bei drei Arbeitspaketen haben die
Implementierungs-Agenten jedoch bewusst eine **letzte Schicht abgegrenzt**, weil sie
— anders als die gelieferten Änderungen — **nicht verhaltensneutral** ist oder
**Vorarbeit** benötigt. Diese Restschuld ohne besondere Regressionssicherung im
selben Durchgang mitzunehmen hätte die harte Vorgabe „bestehende Tests/Selektoren
unverändert grün" verletzt.

Der Rest ist echte, benannte Technik-Schuld: Er verkleinert die Duplikation weiter
und schärft Sicherheits-/Konsistenz-Garantien — trägt aber Regressionsrisiko und
gehört daher in ein eigenes, sorgfältig abgesichertes Arbeitspaket.

## Vorschlag

Die verbleibenden Punkte in **drei abgrenzbaren Teil-Initiativen** umsetzen, jeweils
mit koordinierten Test-Anpassungen und voller Regressionssicherung (Backend-Suite /
vitest grün als Gate).

### A) Base-Repository-Vollendung (AP-15-Rest, DUP-B1/B6)

1. **`get_or_raise` in die Interface-ABCs** (`domain/interfaces/*_repository.py`, NFR-001 §9.1)
   heben, damit die typisierte API auch auf ABC-Ebene sichtbar ist. Betroffene
   Test-Fakes müssen die Methode nachimplementieren (heute über die Base zur Laufzeit
   erfüllt).
2. **~92 verbleibende `get_or_raise`-Kandidaten** umstellen. Diese sind heute nicht
   rein mechanisch ersetzbar, weil:
   - Facade-Repos Sekundär-Entities über eigene Methoden laden
     (`get_schedule_by_key` → „MaintenanceSchedule", `get_disease_by_key` → „Disease"),
     während `get_or_raise` den **Primär**-`_model_cls.__name__` würfe → braucht
     `_entity_name`-Plumbing bzw. Zugriff über die Composed-Views.
   - manche Blöcke auf ungebundenen Repos liegen oder abweichende Semantik haben
     (Tenant-Mismatch-als-None, `verify_tenant_ownership`-Kopplung).
3. **Fail-Fast des ungebundenen Legacy-Dict-Modus.** Aktuell arbeitet
   `BaseArangoRepository` ohne gebundenes `_model_cls` im Dict-Modus, damit legitime
   ungebundene Instanzen weiterlaufen. Diese zuerst migrieren, dann den Dict-Modus
   auf `TypeError`/Fail-Fast verschärfen:
   - `graph_repository`, `phase_sequence_repository` (reine Custom-AQL / Dict-Rückgaben),
   - service-eingebettete `BaseArangoRepository(db, col)` (`user_preference_service`,
     `onboarding_service`, `starter_kit_service`, `seed_starter_kits.py`),
   - `task`-Sekundär-Collections — `create_audit_entry` setzt **kein**
     `created_at`/`updated_at`, weshalb die Base-`create` das Dokument verändern würde.

### B) List-Slice-Factory-Vollendung (AP-16-Rest, FE-D5)

Die `createListSlice`-Factory schreibt fest in `state.items`/`state.current`. Nur
Slices mit dieser kanonischen Form konnten migrieren; die ~14 domänenbenannten
List-Slices (`s.tanks.tanks`, `s.nutrientPlans.plans`, `s.fertilizers.fertilizers`,
`s.plantingRuns.runs`, `s.feedingEvents.events`, `s.wateringLogs.logs`,
`s.wateringEvents.events` …) lesen eigene State-Feldnamen. Voll-Migration erfordert
**eine** von zwei Optionen:

- **Option 1 (empfohlen, kleineres Risiko):** Factory um ein optionales
  Feld-Mapping erweitern (`itemsField`/`currentField`), sodass die Slices ohne
  Feld-Rename adoptieren können.
- **Option 2:** State-Felder auf `items`/`current` umbenennen und **alle**
  Page-Selektoren + Reducer-Tests koordiniert nachziehen (nicht verhaltensneutral).

### C) Kleinteiliges

- **`FertilizerSnapshotData`** um die W-013-Felder (`application_rate_g_per_m2` etc.)
  erweitern, falls Nährstoffplan-Snapshots diese abbilden sollen.
- **FE-L5 auf die Session-Slices** (`tenant`, `onboarding`, `userPreferences`) — die
  restlichen rohen `'Failed to load …'`-Fallbacks auf `errors.*`-i18n-Keys umstellen.
- **Vorbestehendes `E501`** in `knowledge-service/app/service.py:81` (unrelated,
  bislang nicht CI-gegated) beheben.

## Erwarteter Nutzen

- **Weniger Duplikation** in der Data-Access-Schicht (die generische Base greift
  überall) und im Redux-Store (eine Factory statt ~14 Boilerplate-Slices).
- **Stärkere Invarianten:** Fail-Fast verhindert versehentliche Dict-Modus-Nutzung;
  einheitliche `get_or_raise`-Semantik in den Services.
- **Konsistente, lokalisierte Fehlertexte** über alle Slices (auch Session-Bereich).

## Abgrenzung (was dieser Request NICHT ist)

- **Kein neues Nutzer-Feature** — reine interne Qualität/Wartbarkeit; keine API-Vertrags-
  oder UI-Verhaltensänderung nach außen (die Slice-/Snapshot-Änderungen bleiben
  fachlich äquivalent).
- **Keine Neuauflage des Reviews** — der AP-1..21-Katalog und die verhaltensneutralen
  Follow-ups sind bereits abgeschlossen (#318); dies ist ausschließlich der bewusst
  zurückgestellte Rest.

## Umsetzungshinweise

- Jede Teil-Initiative als eigener PR mit **voller Regressionssicherung** (Backend
  `tests/unit`+`tests/api` bzw. `vitest run` grün als Gate); Teil A und B ändern
  Tests koordiniert mit.
- Reihenfolge in A beachten: erst ungebundene Repos migrieren, **dann** Fail-Fast
  aktivieren.
- Für B Option 1 bevorzugen (verhaltensneutral); Option 2 nur, wenn eine
  Feld-Vereinheitlichung ohnehin gewünscht ist.
