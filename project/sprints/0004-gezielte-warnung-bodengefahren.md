---
number: 4
status: planned
started: null
ended: null
value_statement: Gärtner werden beim Nachpflanzen gezielt gewarnt, wenn ein Beet einen bestätigten bodenbürtigen Erreger trägt – für die betroffenen Wirtspflanzen und nur so lange, wie die belegte Anbaupause reicht.
artifact_ref: null
last_commit: null
roadmap_items: [R-20]
features: [F-18, F-19, F-20, F-21]
---

## Goal

Fällt eine Pflanze aus, hält der Gärtner künftig fest, ob der Ausfall
bodenbürtig war (F-19). Ein bestätigter Befall mit einem dauerhaften
Bodenerreger wird als Bodengefahr des Beets gespeichert (F-20). Pflanzdialog
und Fruchtfolgeprüfung warnen dann gezielt für die Wirtspflanzen dieses
Erregers, innerhalb der belegten Anbaupause mit Zeitangabe, danach bis zur
maximalen Überdauerung als Hinweis, nie als harte Sperre (F-21). Grundlage ist
eine Wissenstabelle der Bodengefahren mit Belegstatus je Wert (F-18) (R-20,
Issue #2888).

Umsetzungsreihenfolge: **F-18 → F-19 → F-20 → F-21**, streng seriell. F-18
bringt das Spec-Update (REQ-003 E5, REQ-053 §11.3/§16, REQ-054 §5.2/H-10/AP-ACC-022,
TC-REQ-054) vor jedem Code-Commit. F-19 liefert Erreger und Bestätigung am
Ausfall, die F-20 für die Übernahme ins Beet braucht; F-21 liest beides.

Der value-verifizierende Nachweis ist **F-21 `acceptance-1`**: Ist die gewählte
Pflanze Wirt einer Bodengefahr des Beets, zeigt der Pflanzdialog innerhalb der
belegten Anbaupause eine überstimmbare Warnung mit Zeitangabe, danach einen
Hinweis, auch auf Beeten mit ausgeschalteter Fruchtfolge. Das Kriterium setzt
F-18 (Wissenstabelle) und F-20 (Bodengefahr am Beet) voraus und weist damit die
ganze Kette nach.

Betreiberentscheidungen vom 2026-11-22 für F-18 (offene Punkte aus
`spec/analysis/agrobiology-soil-hazards-research-2888.md` §7.12):

- **Spannen zählen als 3/3.** Liegt ein Wert in allen drei Quellangaben, auch
  wenn diese Spannen nennen, gilt er als 3/3-belegt; die Wissenstabelle weist
  den Belegtyp „Spanne“ aus. Das betrifft Kohlhernie (7 J.), Sclerotinia (5 J.)
  und Verticillium (4 J.). Die Konsistenznotiz in F-21 („clubroot: block
  duration 2/3“) wird dadurch zu 3/3; F-18 `acceptance-4` macht das zu einer
  reinen Datenänderung.
- **`soil_persistence_years` meint die Anbaupause**, nicht die
  Rotationslänge. Für den Rübenzystennematoden gilt die strengere Lesart
  (2–3 J. Pause); die Bewertung R-001.2 der Recherche wird entsprechend
  korrigiert.

Freigabe des Zuschnitts durch den Betreiber am 2026-11-22.

## Features

- [F-18](../features/soil-hazard-knowledge.md) — status: ready
- [F-19](../features/failure-cause-class.md) — status: ready
- [F-20](../features/bed-soil-hazards.md) — status: ready
- [F-21](../features/soil-aware-replant-hint.md) — status: ready

## Out of scope

- Nachrecherche fehlender Werte (§7.12 Punkt 2) — neue Werte sind reine Datenänderungen nach F-18 `acceptance-4`, kein Teil dieses Sprints.
- Meldepflichtige Quarantäne-Schaderreger und der REQ-054-Anbauplaner, der `soil_hazards[]` später liest.
- R-19, R-21/R-22, R-23, R-27 — eigene Sprints.

## Review notes

_Populated by `sprint-review` at closure._
