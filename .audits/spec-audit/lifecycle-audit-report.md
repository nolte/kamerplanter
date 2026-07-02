# Spec-Audit — Vollständiger Pflanzen-Lifecycle über alle Arten

```yaml
Audit: spec-audit (feat/spec-audit)
Datum: 2026-07-01
Anforderung: project/requirements/spec-audit.md (U_gate 0.78)
Achsen: Widerspruch · Readiness · Spec-vs-Code-Drift · Vollständigkeit
Linse: Modelliert die Spec den vollständigen Lebenszyklus, wenn unterschiedliche
       Arten unterschiedliche Lebenszyklen haben?
Methode: 3 Explore-Agenten (Fable 5) + direkte Verifikation jeder Fundstelle
Fix-Richtung: wahrheitsgetreue Korrektur (Spec-Hygiene) — siehe §4
```

Die Spec ist **reif**: REQ-003 v2.7 beschreibt viele Archetypen bereits (annuell,
biennial, perennial indoor/outdoor, Autoflower, monokarp/polykarp in Prosa). Der
Mehrwert dieses Audits liegt daher in **Konsistenz- und Vollständigkeitslücken**,
nicht in „ist es vorhanden". Der rote Faden aller schweren Funde: **Changelogs
und Visualisierungen behaupten ein Lebenszyklus-Modell, das der Spec-Body noch
nicht enthält.**

Jeder Fund ist mit `datei:zeile` verankert und verifiziert. Bereits gelöste
Widersprüche (`spec/analysis/requirements-contradictions-2026-04-26.md`, 22
W-Items) und Backlog-Positionen (`.audits/datenmodell-pflanzeneigenschaften-plan.md`,
WP-1..6) werden **referenziert, nicht dupliziert**.

---

## 1. Severity-Übersicht

| ID | Severity | Achse | Betroffene Archetypen | Kurzbeschreibung | Fix |
|----|----------|-------|-----------------------|------------------|-----|
| A1 | **Hoch** | Widerspruch (intra) | monokarp | `flowering_strategy` nur im REQ-003-Changelog, fehlt im Body | Changelog korrigieren |
| A2 | **Hoch** | Widerspruch (intra) | tender-perennial | `cultivation_cycle_type` nur in REQ-001/003-Changelog, fehlt im Body | Changelog korrigieren |
| A3 | **Hoch** | Widerspruch (intra) | bulb-geophyte, Gräser, Sukkulenten | `GrowthHabit`-Enum-Erweiterung nur im Changelog, Body hat 5 Werte | Changelog korrigieren |
| E1 | **Hoch** | Drift | succession, overwintering | Coverage-Aggregat meldet 100 %, Code hat weder `SuccessionPlan` noch `OverwinteringProfile`-Modell | Report + Coverage-Notiz |
| B1 | **Hoch** | Widerspruch (intra) | alle | Drei uneinige Phasen-Vokabulare in REQ-003 | Kanonischer Katalog + Cross-Ref |
| C1 | **Mittel** | Widerspruch (cross) | perennial, biennial | Zwei parallele Zyklus-Restart-Darstellungen (REQ-003 vs REQ-004) ohne Verknüpfung | Cross-Ref |
| B2 | **Mittel** | Readiness | alle | UI-NFR-016-Palette (22 Namen) ≫ State-Machine-Vokabular | Palette annotieren |
| D1 | Mittel | Vollständigkeit | biennial | Kein Zwei-Jahres-Phasenpfad; `PerennialCycleEngine` auf `perennial` festgetypt | ✅ Spec (§5) |
| D2 | Mittel | Vollständigkeit | Vermehrungslinien | Kein Phasen-Eintritt für 10 von 12 Vermehrungsmethoden; 3 Namen für „Steckling-Start" | ✅ Spec (§5) |
| D3 | Niedrig (bewusst) | Vollständigkeit | cannabis-cure, Lager | Post-Harvest/Cure außerhalb der State-Machine (REQ-008 auf `batches`) | ✅ Spec (§5) |
| D4 | Niedrig | Vollständigkeit | perennial (juvenil) | Juvenil-Phasen-Skip in Test unterstellt, nicht spezifiziert | ✅ Spec (§5) |
| D5 | Mittel | Vollständigkeit | overwintering, tender-perennial | Keine Invariante Dormanz ↔ Winterhärte; REQ-039 referenziert REQ-003 nicht | ✅ Spec (§5) |
| D6 | Niedrig | Vollständigkeit | monokarp | „blüht einmal, stirbt" ohne Terminal-Transition (folgt A1) | ✅ Spec (§5) |
| D7 | Niedrig | Vollständigkeit | bulb-geophyte | Knollenzyklus nur in `OverwinteringProfile.tuber_status`, entkoppelt von GrowthPhase | ✅ Spec (§5) |

> **Statushinweis 2026-07-02:** Die „Fix"-Spalte oben nennt den **Befund**-Stand
> zum Audit-Zeitpunkt. A1/A2/A3 wurden zunächst nur als „geplant" markiert
> (2026-07-01), dann auf Maintainer-Wunsch (2026-07-02) mit **allen** D-Funden
> **auf Spec-Ebene tatsächlich umgesetzt** — siehe §4/§5. Code bleibt Backlog.

---

## 2. Lifecycle-Archetyp × Spec-Abdeckung

Legende: ✅ vollständig modellierbar · ⚠️ teilweise / mit Lücke · ❌ nicht modellierbar

| Archetyp | Klassifikation setzbar | Phasenpfad vollständig | Sonderlogik | Lücke |
|----------|------------------------|------------------------|-------------|-------|
| **Annuell (Ernte)** | ✅ `cycle_type='annual'` | ✅ Keimung→…→Seneszenz | ✅ `is_terminal`/`allows_disposal` | — |
| **Annuell (Zierpflanze)** | ✅ | ✅ (`allows_harvest:false`) | ✅ AB-009 hardening_off | — |
| **Perennial (Outdoor)** | ✅ `='perennial'` | ✅ `seasonal_cycles` + `is_cycle_restart` | ✅ chill_hours, Reifegrad | — |
| **Perennial (Zimmerpflanze)** | ✅ | ✅ Dormanz-Zyklus | ✅ DORMANCY vs FLUSHING | — |
| **Cannabis (photoperiodisch/auto)** | ✅ Cultivar-Level | ✅ Post-Harvest-Handoff (D3) | ✅ Autoflower-Preset, HST-Guard | ✅ D3 gelöst |
| **Biennial** | ✅ `='biennial'` | ✅ Biennial-Template + `CyclicLifecycleEngine` | ✅ `dormancy`=vernalisationsgatend; `cultivation_cycle_type` | ✅ D1 gelöst |
| **Tender-Perennial (annuell in Kultur)** | ✅ `cultivation_cycle_type` | ✅ | ✅ D5-Winter-Pfad-Invariante | ✅ A2/D5 gelöst |
| **Monokarp** | ✅ `flowering_strategy` | ✅ Terminal-Guard `should_restart_cycle` | ✅ D6 | ✅ A1/D6 gelöst |
| **Vermehrungslinie (Klon/Teilung/Pfropfung)** | ✅ 12-Methoden-Matrix | ✅ Eintritt je Methode (`rooting`/`vegetative`/`germination`) | ✅ Naming kanonisch `rooting` | ✅ D2 gelöst |
| **Bulb-Geophyt (Dahlie, Tulpe)** | ✅ `bulb_geophyte` habit | ✅ `tuber_status` ↔ `dormancy`/`seasonal_cycles` | ✅ D7-Anbindung | ✅ A3/D7 gelöst |

**Kernaussage (nach D-Umsetzung 2026-07-02):** Auf **Spec-Ebene** sind jetzt ALLE
Archetypen — annuell, biennial, perennial, tender-perennial, monokarp,
cannabis-cure, Vermehrungslinien, bulb-geophyt — durchgängig modellierbar. Die
Changelog-Überclaims wurden durch echte Body-Definitionen ersetzt (REQ-001 v4.5,
REQ-003 v2.8). **Offen (Backlog):** Code-/Seed-Umsetzung + Backfill der ~210
Bestandsarten (`datenmodell-pflanzeneigenschaften-plan.md` WP-1/3/4/5/10).

---

## 3. Detailfunde

### A — Changelog-vs-Body-Drift (höchste Konfidenz, verifiziert)

Alle drei Felder erscheinen **ausschließlich** in Changelog-Zeilen und in keiner
Property-Definition. `grep` bestätigt null Vorkommen außerhalb der Changelogs.

- **A1 · `LifecycleConfig.flowering_strategy` (monocarpic/polycarpic)**
  Behauptet: `REQ-003_Phasensteuerung.md:17` (v2.7 „Phase A"). Body: fehlt in der
  `:LifecycleConfig`-Property-Liste (`REQ-001_Stammdatenverwaltung.md:157-165`).
  Folge: „blüht einmal, stirbt dann" (Agave, Bambus) ist nicht ausdrückbar.
  Backlog: `datenmodell-pflanzeneigenschaften-plan.md` WP-4.

- **A2 · `LifecycleConfig.cultivation_cycle_type`**
  Behauptet: `REQ-001_Stammdatenverwaltung.md:18` (v4.4) und
  `REQ-003_Phasensteuerung.md:17` (v2.7). Body: fehlt (`REQ-001:157-165`).
  Folge: „botanisch perennial, in Kultur einjährig" (Tomate, Pelargonie) nicht
  ausdrückbar. Backlog: WP-3.

- **A3 · `GrowthHabit`-Enum-Erweiterung**
  Behauptet: `REQ-001_Stammdatenverwaltung.md:18` (+`subshrub`, `grass`,
  `succulent`, `bulb_geophyte`, `fern`, `aquatic`, `epiphyte`). Body: die
  `GrowthHabit`-Enum (`REQ-001:1229-1234`) sowie die Prosa-Property (`:79`, `:1012`)
  führen weiterhin nur `herb, shrub, tree, vine, groundcover`. Die KB-Referenz
  markiert dies offen (`spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` §9 E1).
  Folge: Bulb-Geophyten (Dahlie, Tulpe) können keinen korrekten Habitus setzen.
  Backlog: WP-1.

> **Warum Hoch:** Ein Changelog ist der Vertrauensanker für „was ist bereits
> spezifiziert". Ein Implementierer, der die Changelogs liest, baut gegen Felder,
> die es nicht gibt — oder hält die Lücke für geschlossen. Der Widerspruch ist
> intern (Changelog vs. Body derselben Datei) und damit eindeutig.

### E — Reconciliation: Coverage-Aggregat vs. Code (verifiziert)

- **E1 · Falsch-positives 100 % im Coverage-Aggregat.**
  `.audits/phase-0-drift-findings.md:58,152` listet `SuccessionPlan` (REQ-013) und
  `OverwinteringProfile` (REQ-022) als OFFEN/fehlend. `.audits/req-coverage-audit.md:47,57`
  meldet beide REQs mit **100 %**. Code-Verifikation:
  - `SuccessionPlan`/`succession_plan`: **0 Treffer** in `src/backend`.
  - `OverwinteringProfile` (Modellklasse): **0 Treffer**; nur die v2.5-Reminder-Typ-
    *Enums* sind gelandet (`src/backend/app/common/enums.py:670`,
    `tests/unit/common/test_care_enums_v25.py`).
  → Der phase-0-Befund gilt weiterhin. `run_audit.py` prüft nur Artefakt-*Präsenz*
  (Datei-Globs), nicht semantische Vollständigkeit — daher das irreführende 100 %.
  Diese beiden Lifecycle-Features (Staffelanbau, Überwinterungsprofil) sind real
  nicht implementiert.

### B — Phasen-Vokabular-Drift

- **B1 · Drei uneinige Phasen-Vokabulare in REQ-003.**
  1. `PhaseName-Enum` (Prosa, `REQ-003:62`): `germination, seedling, vegetative,
     flowering, flushing, dormancy, harvest` (7).
  2. `PhaseType` Literal (Code, `REQ-003:1306-1308`): `seedling, vegetative,
     flowering, ripening, dormancy, flushing, bud_break, fruit_development,
     senescence, hardening_off, acclimatization, active_growth, maintenance,
     repotting_recovery` (14 — ohne germination/harvest, dafür 8 weitere).
  3. DoD-Listen-Filter-Chips (`REQ-003:1390`): `germination, seedling, vegetative,
     flowering, harvest, drying, curing` — enthält `drying`/`curing`, die **keine**
     `growth_phases` sind (Post-Harvest, REQ-008).
  → Ein Implementierer kann nicht entscheiden, welche Menge kanonisch ist. Direkte
  Quelle von Enum-/Filter-Bugs.

- **B2 · UI-NFR-016-Palette ≫ State-Machine-Vokabular.**
  Die kanonische Phasen-Farbpalette (`UI-NFR-016:79-104`) definiert 22 Phasennamen
  (u. a. `climbing, mature, budding, pre_bloom, recovery, sprouting,
  tuber_formation, corm_ripening, establishment`), von denen die Mehrheit in
  REQ-003 undefiniert ist. UI-NFR-016 R-006 erklärt diese Palette für alle Views
  verbindlich, ohne dass REQ-003 einen passenden Phasen-Katalog liefert.

### C — Cross-Layer-Konsistenz (verifiziert & korrigiert)

- **C1 · Zwei parallele Zyklus-Restart-Darstellungen ohne Verknüpfung.**
  REQ-003 modelliert Zyklus-Neustart als **Boolean pro Transition**
  `phase_transition_rules.is_cycle_restart` (`REQ-003:111`, genutzt an :1066/1146/1338).
  REQ-004 modelliert ihn als **Integer auf dem NutrientPlan**
  `cycle_restart_from_sequence` (`REQ-004_Duenge-Logik.md:326`), und UI-NFR-016/020
  sowie die REQ-004-Timeline rendern daraus.
  → Beide beschreiben dasselbe Konzept (zyklische Wiederholung ab einer Phase) auf
  verschiedenen Entitäten und Layern, ohne Cross-Reference oder Konsistenz-Invariante.
  Divergenz zwischen State-Machine und Nährstoffplan/Visualisierung ist möglich.

  > Korrektur ggü. Erst-Explore: Das Feld ist **nicht** undefiniert — es lebt in
  > REQ-004, nicht in REQ-003. Der Fund ist ein Traceability-/Konsistenz-Gap,
  > keine fehlende Definition.

### D — Strukturelle Lifecycle-Lücken (2026-07-02 vollständig spezifiziert)

> **Scope-Update 2026-07-02:** Der Maintainer hat die Fix-Richtung von „nur
> dokumentieren" auf **„D vollständig umsetzen"** geändert. Alle D-Lücken sind
> jetzt auf **Spec-Ebene** geschlossen (Feld-/Enum-/Phasenlogik-Definitionen in
> den REQ-Dokumenten). Die nachgelagerte **Code-Umsetzung** (Backend/Frontend/
> Seed nach `.audits/datenmodell-pflanzeneigenschaften-plan.md`) bleibt Backlog —
> `src/` wurde nicht angefasst (NFR-003). Details je Fund unten + §5.

- **D1 · Biennial ohne Zuhause.** `cycle_type='biennial'` setzbar (`REQ-001:159`),
  aber kein Jahr-1→Überwinterung→Jahr-2-Pfad (Vernalisation→Schossen→Blüte→Samen).
  `PerennialCycleEngine.cycle_type` ist auf `Literal['perennial']` festgetypt
  (`REQ-003:1037`). Beleg: Karotte (`spec/knowledge/plants/daucus_carota.md:22`) ist
  biennial, aber die autorisierten Phasen enden bei harvest; `vernalization_required`
  gatet keine Phase. → Kandidat für eine `BiennialCycleEngine`/Template-Generalisierung.

- **D2 · Kein Vermehrungs-Eintrittsmatrix.** `REQ-017:1507` definiert nur
  seed→germination, cutting→seedling; die übrigen 10 `PropagationMethod`-Werte
  (`REQ-017:519-531`: division, offset, layering, air_layering, bulbil,
  water_propagation, grafting, stem_section, leaf_cutting, tissue_culture) haben
  keinen Phasen-Eintritt. Zusätzlich drei uneinige Namen für den Steckling-Start:
  `seedling` (REQ-017) vs `Bewurzelung` (`REQ-003:42`) vs `Einwurzelung`
  (`daucus`/`buxus`-KB). Backlog: WP-5.

- **D3 · Post-Harvest/Cure außerhalb der State-Machine.** Das Phasen-Enum endet bei
  harvest/ripening; Trocknung/Curing sind `batches`-gebundene Nodes in REQ-008
  (`REQ-008:127-145`). „Vollständiger Lebenszyklus" ist damit für Cannabis-Cure oder
  Zwiebel-curing→storage nicht durchgängig. (Bewusste Architektur-Trennung — als
  Kontext dokumentiert, kein Fehler.)

- **D4 · Juvenil-Phasen-Skip unspezifiziert.** Die Single-Successor-`next_phase`-Kette
  kann flowering/fruit_development für einen juvenilen Perennial nicht überspringen,
  obwohl Test-Szenario 5 (`REQ-003:1531`) genau das unterstellt.

- **D5 · Dormanz ↔ Winterhärte nicht verknüpft.** Keine Invariante bindet
  `OverwinteringProfile`/`frost_sensitivity` an eine `dormancy`-GrowthPhase; REQ-039
  (Klimazonen/Winterhärte) referenziert REQ-003 nicht (`REQ-039:11` nennt nur
  REQ-001/002/022/005/015-A). Die zwei Winter-Darstellungen können divergieren.

- **D6 · Monokarp-Terminal fehlt** (folgt A1): „blüht einmal, stirbt dann" hat keine
  Terminal-nach-Blüte-Transition. Backlog: WP-4.

- **D7 · Bulb-Geophyten-Zyklus entkoppelt** (folgt A3): dig→dry→store→pre-sprout
  lebt nur in `OverwinteringProfile.tuber_status` (`REQ-022:254`), nicht in
  GrowthPhase/seasonal_cycles. Backlog: WP-1.

---

## 4. Angewandte Fixes (wahrheitsgetreue Korrektur)

Entscheidung: **Spec-Hygiene** — Changelog-Überclaims + Enum-/Feld-Drift bereinigen;
strukturelle D-Lücken dokumentieren statt neu spezifizieren. Jeder Edit wurde als
Diff geprüft. `src/` bleibt unangetastet, NFR-003 (deutsche Doku) gewahrt.

| Fund | Aktion | Datei |
|------|--------|-------|
| A1/A2 | Changelog-Einträge REQ-003 v2.7 / REQ-001 v4.4 als **geplant (WP-3/4)** kennzeichnen, Body-Pointer auf Backlog | REQ-003:17, REQ-001:18 |
| A3 | Changelog REQ-001 v4.4 GrowthHabit-Erweiterung als **geplant (WP-1)** kennzeichnen | REQ-001:18 |
| B1 | REQ-003:62 auf kanonischen `PhaseType`-Katalog (1306) verweisen; `drying`/`curing` im DoD-Filter (1390) als Post-Harvest (REQ-008) markieren | REQ-003 |
| B2 | UI-NFR-016-Palette als Display-Katalog kennzeichnen; UI-only-Namen vs. growth_phases-gestützte trennen + Cross-Ref | UI-NFR-016 |
| C1 | Cross-Reference-Notiz an `is_cycle_restart` (REQ-003:111) ↔ `cycle_restart_from_sequence` (REQ-004:326) mit Konsistenz-Hinweis | REQ-003, REQ-004 |
| E1 | Notiz im Coverage-Aggregat, dass 100 % Artefakt-Präsenz ist (SuccessionPlan/OverwinteringProfile real fehlend) | .audits/req-coverage-audit.md |
| D1–D7 | **2026-07-02 auf Spec-Ebene umgesetzt** (siehe §5), nicht mehr nur dokumentiert | REQ-001/003/017/022/039 |

**Status A/B/C/E1 (2026-07-01):** Betroffene Dateien: `spec/req/REQ-001`,
`REQ-003`, `REQ-004`, `spec/ui-nfr/UI-NFR-016`, `.audits/req-coverage-audit.md`.
Bei der D-Umsetzung wurden die A1/A2/A3-„geplant"-Notizen zurückgenommen, weil die
Felder jetzt real im Body stehen (REQ-001 v4.5, REQ-003 v2.8).

## 5. D-Umsetzung auf Spec-Ebene (2026-07-02)

Fix-Richtung geändert auf **„Lücken schließen"**. Da D6 an A1 und D7 an A3 hängen,
wurden die A-Felder jetzt tatsächlich spezifiziert. **`src/` unangetastet**; die
Code-/Seed-Umsetzung folgt `.audits/datenmodell-pflanzeneigenschaften-plan.md`.

| Fund | Umsetzung (Spec) | Datei |
|------|------------------|-------|
| A3/D7 | `GrowthHabit` real auf 12 Werte erweitert (+geophyte etc.); Bulb-Geophyt-Zyklus (`tuber_status`) an `dormancy`/`seasonal_cycles` gebunden | REQ-001 v4.5, REQ-003 v2.8 |
| A2 | `LifecycleConfig.cultivation_cycle_type: Optional[CycleType]` + `grown_as_annual`-Flag | REQ-001 v4.5 |
| A1/D6 | Neuer Enum `FloweringStrategy` + `LifecycleConfig.flowering_strategy`; monokarpe Terminal-Guard in `should_restart_cycle` | REQ-001 v4.5, REQ-003 v2.8 |
| B1/D2 | Kanonisches `PhaseType` (17 Werte, +`germination`/`rooting`/`bolting`) | REQ-003 v2.8 |
| D1 | `PerennialCycleEngine`→`CyclicLifecycleEngine` (`cycle_type IN perennial/biennial`, `max_seasons`, `terminal_after_flowering`) + Biennial-Phasentemplate + Karotten-Widerspruch aufgelöst via `cultivation_cycle_type` | REQ-003 v2.8 |
| D2 | Vollständige Phasen-Eintrittsmatrix (12 `PropagationMethod`-Werte); Steckling-Start kanonisch `rooting` | REQ-017 v1.4 |
| D3 | Expliziter Post-Harvest-Handoff Lifecycle→REQ-008-Batch (Ernte-Event als Brücke, archetyp-abhängige Folgetransition) | REQ-003 v2.8 |
| D4 | Reifegrad-abhängige Phasenverzweigung (mehrwertige `next_phase` + `required_conditions` + `priority`) für Juvenil-Skip | REQ-003 v2.8 |
| D5 | Konsistenz-Invariante Winter-Pfad A (`dormancy` in-situ) vs. B (`OverwinteringProfile.winter_action`); 422-Guard; REQ-039↔REQ-003-Cross-Ref | REQ-022 v2.6, REQ-039 v1.2 |

**Verifikation D-Umsetzung:** `git diff --name-only | grep '^src/'` → 0 Treffer;
8 Spec-/Audit-Dateien geändert; alle Ergänzungen deutsch (NFR-003). Offen (bewusst,
Backlog): Code/Seed-Implementierung + Backfill der ~210 Bestandsarten (WP-10).
