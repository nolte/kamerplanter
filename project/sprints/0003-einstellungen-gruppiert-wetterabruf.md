---
number: 3
status: closed
started: 2026-11-22
ended: 2026-11-24
value_statement: Nutzer finden jede Einstellung in einer von sechs Gruppen statt in einer Leiste mit 14 Tabs, und Betreiber stellen dort das Intervall für den Wetterabruf ein und starten einen Abruf von Hand.
artifact_ref: develop@e074bde9 (PR #3109)
last_commit: e074bde9ad0bce8d39c946dcc647803e0a720702
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

- [F-12](../features/platform-settings-in-admin.md) — status: done
- [F-11](../features/settings-grouped-navigation.md) — status: done
- [F-13](../features/weather-fetch-scheduling.md) — status: done
- [F-14](../features/weather-fetch-settings-ui.md) — status: done

## Out of scope

- R-19 (Mandanten-Export/-Import), R-20 (Bodengefahren), R-21/R-22 (Multi-Dashboard), R-23 (Plant Social Welle 1) — eigene Sprints.
- Issue #3002 (gemessener Niederschlag im Bewässerungsbedarf) — eigenes Roadmap-Item, Interview am 2026-11-17.

## Review notes

**Abschluss (sprint-review, 2026-11-24): `closed`.** Freigabe durch den Betreiber am 2026-11-24.

**Artefakt-Validierung (Schritt 3).** Projekttyp `python-application` (Override
`.github/release-skill-layer.yml`); self-hosted Anwendung mit kontinuierlichem
Deploy aus `develop`, kein Release-Cut pro Sprint. Artefakt-Konvention wie
Sprint 1 und 2 (`develop@<sha> (PR #N)`).
- `artifact_ref: develop@e074bde9 (PR #3109)` ist der Squash-Merge des letzten
  Sprint-Codes (F-11: offene Gruppe bleibt über den md-Breakpoint gemountet).
- `git rev-parse e074bde9a` löst auf `e074bde9ad0bce8d39c946dcc647803e0a720702`
  auf, gleich `last_commit`; `git merge-base --is-ancestor e074bde9a origin/develop`
  liefert Exit 0 (**REACHABLE**).

**Mehrwert-Verifizierer (Schritt 4).** Genau ein `verifies_sprint_value` über die
vier Features: **F-14 (`features/weather-fetch-settings-ui.md`) `acceptance-2`**.
„Jetzt abrufen“ zeigt Fortschritt und anschließend das Ergebnis; ein abgelehnter
Abruf zeigt, ab wann ein neuer Abruf möglich ist. Der Bullet ist `[x]`, der
Test-Hook `components/admin/WeatherFetchPanel.test.tsx` ist `passing` (#3108).
Alle vier Features sind `done`, ohne offene Kriterien und ohne `pending`- oder
`failing`-Hooks.

**Release-Verkettung (Schritt 5): übersprungen.** Grund: self-hosted Anwendung
mit kontinuierlichem Deploy aus `develop` und ohne eigenen Release-Cut pro
Sprint. `release-notes-curate` und `release-publish-trigger` wurden nicht
angestoßen; die Veröffentlichung (offener Draft `v0.5.1`) entscheidet der
Betreiber gesondert. Das Deployment läuft über die bestehende
docker-publish/ArgoCD-Pipeline (wie in Sprint 1 und 2).

**Roadmap.** R-17 (F-11, F-12) und R-18 (F-13, F-14) gehen auf `done`, weil alle
ihre Features `done` sind und der Sprint `closed` ist.

**Blog-Trigger-Deferrals.** Keine offenen (`project/blog-triggers/` nicht vorhanden).
