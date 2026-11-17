---
number: 3
status: planned
started: null
ended: null
value_statement: Nutzer finden jede Einstellung in einer von sechs Gruppen statt in einer Leiste mit 14 Tabs, und Betreiber stellen dort das Intervall für den Wetterabruf ein und starten einen Abruf von Hand.
artifact_ref: null
last_commit: null
roadmap_items: [R-17, R-18]
features: [F-12, F-11, F-13, F-14]
---

## Goal

Die Einstellungsseite verliert ihre horizontal scrollende Leiste mit bis zu 14
Tabs: Eine Seitennavigation (Desktop) bzw. eine Gruppenliste mit Detailansicht
(mobil) gliedert die Einstellungen in sechs Gruppen, die Plattform-Einstellungen
ziehen in den Admin-Bereich (R-17, Issue #2935). In der Betreiber-Gruppe
„Installation“ stellt der Betreiber das Abrufintervall des Wetters ein und
startet einen Abruf von Hand; nach jedem Abruf laufen Frostprüfung und
Bewässerungsbedarf (R-18, Issue #2934).

Umsetzungsreihenfolge: **F-12 → F-11 → F-14**; **F-13** (Backend) ist von F-12
und F-11 unabhängig und läuft parallel, muss aber vor F-14 gemergt sein.

Der value-verifizierende Nachweis ist **F-14 `acceptance-2`**: „Jetzt abrufen“
zeigt Fortschritt und Ergebnis, ein abgelehnter Abruf zeigt, ab wann ein neuer
möglich ist. Das Kriterium setzt F-13 (Abruf-API) und F-11 (Gruppe
„Installation“) voraus und weist damit die ganze Kette nach.

Freigabe des Zuschnitts durch den Betreiber am 2026-11-17.

## Features

- [F-12](`../features/platform-settings-in-admin.md`) — status: ready
- [F-11](`../features/settings-grouped-navigation.md`) — status: ready
- [F-13](`../features/weather-fetch-scheduling.md`) — status: ready
- [F-14](`../features/weather-fetch-settings-ui.md`) — status: ready

## Out of scope

- R-19 (Mandanten-Export/-Import), R-20 (Bodengefahren), R-21/R-22 (Multi-Dashboard), R-23 (Plant Social Welle 1) — eigene Sprints.
- Issue #3002 (gemessener Niederschlag im Bewässerungsbedarf) — eigenes Roadmap-Item, Interview am 2026-11-17.

## Review notes

_Populated by `sprint-review` at closure._
