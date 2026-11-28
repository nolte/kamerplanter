---
number: 4
status: closed
started: 2026-11-27
ended: 2026-11-28
value_statement: Gärtner werden beim Nachpflanzen gezielt gewarnt, wenn ein Beet einen bestätigten bodenbürtigen Erreger trägt – für die betroffenen Wirtspflanzen und nur so lange, wie die belegte Anbaupause reicht.
artifact_ref: develop@98a4e850 (PR #3167)
last_commit: 98a4e8503f1c99ac6ecd8edf0ff6d452e9e11887
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

- [F-18](../features/soil-hazard-knowledge.md) — status: done
- [F-19](../features/failure-cause-class.md) — status: done
- [F-20](../features/bed-soil-hazards.md) — status: done
- [F-21](../features/soil-aware-replant-hint.md) — status: done

## Out of scope

- Nachrecherche fehlender Werte (§7.12 Punkt 2) — neue Werte sind reine Datenänderungen nach F-18 `acceptance-4`, kein Teil dieses Sprints.
- Meldepflichtige Quarantäne-Schaderreger und der REQ-054-Anbauplaner, der `soil_hazards[]` später liest.
- R-19, R-21/R-22, R-23, R-27 — eigene Sprints.

## Review notes

**Abschluss (sprint-review, 2026-11-28): `closed`.** Freigabe durch den Betreiber
am 2026-11-27 (Partition vom 2026-11-27, Sprint-Schritte ausdrücklich eingeschlossen).

**Artefakt-Validierung (Schritt 3).** Projekttyp `python-application` (Override
`.github/release-skill-layer.yml`); self-hosted Anwendung mit kontinuierlichem
Deploy aus `develop`, kein Release-Cut pro Sprint. Artefakt-Konvention wie in den
Sprints 1 bis 3 (`develop@<sha> (PR #N)`).
- `artifact_ref: develop@98a4e850 (PR #3167)` ist der Squash-Merge des letzten
  Sprint-Codes (F-21).
- `git rev-parse 98a4e8503` löst auf `98a4e8503f1c99ac6ecd8edf0ff6d452e9e11887`
  auf, gleich `last_commit`; `git merge-base --is-ancestor 98a4e8503 origin/develop`
  liefert Exit 0 (**REACHABLE**).

**Mehrwert-Verifizierer (Schritt 4).** Genau ein `verifies_sprint_value` über die
vier Features: **F-21 (`features/soil-aware-replant-hint.md`) `acceptance-1`**.
Ist die gewählte Pflanze Wirt einer Bodengefahr des Beets, zeigt der Pflanzdialog
innerhalb der belegten Anbaupause eine überstimmbare Warnung mit Zeitangabe,
danach bis zur maximalen Überdauerung einen Hinweis, auch bei ausgeschalteter
Fruchtfolge. Der Bullet ist `[x]`; belegt durch
`test_crop_rotation_validator_soil_hazards.py::TestAHostOfTheBedsSoilHazard`,
`test_soil_hazard_planting_engine.py` und `PlantingDialog.soilHazards.test.tsx`
(alle in der CI von #3167 grün) sowie im Browser durch
`test_tc_053_111_soil_hazard_in_the_dialog_is_the_planting_checks_answer`
(E2E-Lauf 46113460121 auf `98a4e8503`, alle sechs Profile grün; der Test ist im
Profil `light` laut JUnit `passed`). Alle vier Features sind `done`
(F-18 #3145, F-19 #3151, F-20 #3154, F-21 #3167), ohne offene Kriterien und ohne
`pending`- oder `failing`-Hooks.

**Release-Verkettung (Schritt 5): übersprungen.** Grund: self-hosted Anwendung
mit kontinuierlichem Deploy aus `develop` und ohne eigenen Release-Cut pro
Sprint. `release-notes-curate` und `release-publish-trigger` wurden nicht
angestoßen; über die Veröffentlichung (offener Draft `v0.5.1`, #3133) entscheidet
der Betreiber gesondert.

**Roadmap.** R-20 (F-18 bis F-21) geht auf `done`, weil alle Features `done` sind
und der Sprint `closed` ist.

**Offen über den Sprint hinaus (kein Abschlusshindernis).**
- Folgeänderungen aus den Betreiberentscheidungen vom 2026-11-27 an F-20
  (Juglon an Flächentypen, `irrigation_system` vom Eltern-Standort, Protokoll
  beim Entfernen) laufen als eigener PR.
- Zwei Betreiberfragen aus dem Review von F-21 stehen in
  `features/soil-aware-replant-hint.md`: wer „Substrat erneuert am“ setzen darf,
  und ob ein Anbaufenster von bis zu 1095 Tagen eine mehrjährige Standzeit aus
  der Fruchtfolge ausblenden darf.
- Eine ersetzte Pflanze ohne Sorte fällt auf die Kalenderjahr-Regel zurück
  (`days_to_maturity` liegt an der Sorte, nicht an der Art; REQ-053 v1.59).

**Blog-Trigger-Deferrals.** Keine offenen (`project/blog-triggers/` nicht vorhanden).
