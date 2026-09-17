# Gruppe `2026-09-17-task-queue-plant-scope`

Status: Analyse abgeschlossen · Write-Gate offen (Operator-Freigabe ausstehend)

Gemessen gegen `origin/develop` @ `0b4ce20bf` (2026-09-17). Transientes Artefakt.

## Die Frage

Ist das Pflanzen-Scoping der Aufgaben-Queue real (serverseitig) oder eine Behauptung (Client-Filter über einer gekappten Antwort) — und beschreibt die E2E-Selbstdiagnose den Zustand, der tatsächlich gilt?

## Die eine logische Änderung

Das Pflanzen-Scoping der Aufgaben-Queue wird real — die Seite fragt den Server mit `plant_key`, statt 200 gekappte Zeilen clientseitig zu filtern — und der E2E-Helfer diagnostiziert nur auf dieser gemessenen Basis.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1484** | `bug`, `frontend` | Anker | `src/frontend/src/pages/aufgaben/TaskQueuePage.tsx`: alle 9 `dispatch(fetchTaskQueue())` (Z. 250, 278, 294, 310, 327, 357, 432, 459, 485) ohne `filterPlantKey` (State Z. 223; Client-Filter Z. 518/555/616) |
| **#1485** | `test` | Abhängigkeitskette | `tests/e2e/_journey_helpers.py:329-331` („queue was scoped to that plant") und `tests/e2e/pages/task_queue_page.py:256-257` sind erst nach der Verdrahtung wahr; die Meldung muss den Nach-#1484-Zustand beschreiben |

## Messung vs. Issue-Text

- **Fläche kleiner als im Issue:** `store/slices/tasksSlice.ts:103-108` nimmt bereits `plantKey?`, `api/endpoints/tasks.ts:334-340` sendet bereits `plant_key`, Backend `tasks/tenant_router.py:465-473` akzeptiert `plant_key`. Der Defekt ist **allein** `TaskQueuePage.tsx`.
- #1486 hat die Vorbedingung für #1485 geliefert: die drei API-Aufrufe des Helfers drucken `body=`, und `test_care_provisioning_diagnostics.py` (Unit, +108) macht die Diagnosetexte ohne Docker prüfbar.
- `filter_took` (`task_queue_page.py:252-263` `filter_by_plant`) meldet nur die Autocomplete-Auswahl, nicht das Ergebnis — die Diagnose „look at the create" ist daraus nicht ableitbar.

## Strukturbefund (§E)

**Symptom-Cluster**, eine Ursache: eine Scoping-Behauptung ohne Scoping. Klasse: *Prüfung/Helfer leistet weniger als er behauptet* (MEMORY.md). Kein Prozessbefund über #1456 hinaus.

## Stufe

**Stufe 2** — kein veröffentlichter Vertrag, keine Datenänderung.

Design: `TaskQueuePage` reicht `filterPlantKey` in jeden `fetchTaskQueue`-Dispatch; der Client-Filter (Z. 518/555/616) entfällt — er hätte über einer serverseitig gefilterten Antwort nichts zu filtern und war der Ort, an dem die Kappung unsichtbar wurde. Der Helfer-Text in `_journey_helpers.py` nennt, was er weiß (Anzahl Zeilen nach Server-Filter, Pflanze, Antwort-Body) und behauptet nichts über den Create-Pfad.

## Modus und Scheiben

**Modus A** — nichts herauslösbar: eine Frontend-Datei + Helfer-Text, beides unit-testbar. Reihenfolge #1484 → #1485.

| Scheibe | Inhalt | Rot-zuerst |
|---|---|---|
| 1 | `TaskQueuePage.tsx`: `filterPlantKey` in jeden Dispatch; Client-Filter weg | Vitest: Filter gesetzt → `fetchTaskQueue` mit `plantKey` aufgerufen (alter Code: ohne); Mock mit 201 Aufgaben, gesuchte als 201. → sichtbar (alt: nicht) |
| 2 | `_journey_helpers.py` + `task_queue_page.py`-Docstring | Unit `test_care_provisioning_diagnostics.py`: Meldung enthält Zeilenzahl + Body, nicht „look at the create" |

## Vollständigkeitsmatrix

| Issue | AK | Scheibe | Nachweis |
|---|---|---|---|
| #1484 | Server-Filter aktiv bei jedem Reload/Refetch | 1 | Vitest über alle 9 Dispatch-Pfade (Tabellen-Test) |
| #1484 | Pflanze jenseits der 200-Kappung sichtbar | 1 | Vitest mit 201-Zeilen-Mock |
| #1485 | Diagnose behauptet nur Gemessenes | 2 | Unit |

## Verifikation

`tsc`, `eslint`, `vitest run` (Suite), `pytest tests/unit/e2e_support` bzw. wo `test_care_provisioning_diagnostics.py` liegt, `--max-skipped 0`. UI-Review (`frontend-usability-optimizer`) nur, falls sich das Filter-Verhalten für den Nutzer ändert (Leerzustand bei 0 Treffern). Dispatch: `nolte-engineering:fullstack-developer`, ein Kontext.
