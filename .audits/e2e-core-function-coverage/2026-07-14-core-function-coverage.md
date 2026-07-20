---
title: E2E-Abdeckungs-Detail-Check der 5 Kernfunktionen
generated: 2026-07-14
scope: spec/e2e-testcases/TC-REQ-*.md (Spec-TCs) ↔ tests/e2e/test_req*.py (implementierte Selenium-Tests)
branch: feat/e2e-test-identifizierbarkeit
requirement: project/requirements/e2e-test-identifizierbarkeit.md (R5)
---

# E2E-Abdeckungs-Detail-Check der 5 Kernfunktionen

Dieser Report mappt die **implementierten Selenium-Testfunktionen** gegen die
**Spec-Testfälle** (`spec/e2e-testcases/TC-REQ-*.md`) und benennt echte Lücken.

**Abgrenzung zu `spec/e2e-testcases/COVERAGE-REPORT.md`:** Jener Report vergleicht
`spec/e2e-testcases/` gegen `spec/req/`/`spec/nfr/` (Spec-vs-Spec). **Dieser** Report
vergleicht die Spec-TCs gegen die **tatsächlich in `tests/e2e/` implementierten**
Testfunktionen (Spec-vs-Implementierung) — eine bisher nicht abgedeckte Ebene.

**Scope-Hinweis (R5):** Lücken werden **nur benannt**. Es werden in dieser Iteration
**keine neuen Tests** geschrieben; das Schließen ist separaten Issues/Iterationen vorbehalten.

## Zusammenfassung

| Kernfunktion | Ist-Testfunktionen | Spec-TCs (relevant) | Explizit gemappt | Grober Abdeckungsgrad | Kritischste Lücke |
|---|---:|---:|---:|---|---|
| Pflanzenerfassung | 19 (+8 themenfremd) | 4 (Journey-Kern) | 3 | Kern-Journey solide | `TC-001-032` (Anlage aus Species-Detail) |
| Gießen/Bewässerung | 18 | 8 | 2 | Journey abgedeckt, CRUD ohne Spec-Bezug | Gießplan-Gruppe `TC-004-055…060` |
| Düngen/Dünger | 79 | 83 | ~18 (~22 %) | breit, aber flach | Kern-Dosierlogik (Phase-Zuweisung, EC-Budget, WaterMix, NED) |
| Ernte | 33 | 47 (007) + 68 (008) | 23 (007) / 0 (008) | 007 solide, 008 ungetestet | `TC-007-013` Karenz-Gate, `TC-007-036` E2E-Journey, **REQ-008 komplett** |
| Aussaat/Kalender | 32 | 57 | 20 (~35 %) | Navigation solide, Rechenlogik ungetestet | Balken-Berechnungsregeln (Abschnitt J), Security `080–082` |

## Übergreifende Befunde (systemisch)

1. **TC-ID-Traceability driftet systemisch.** Die Testdateien vergeben **test-lokale**
   TC-IDs (`TC-REQ-004-W001`, `TC-REQ-001-PI-001`, `J079`), die überwiegend **nicht** den
   Spec-IDs (`TC-004-NNN`, `TC-001-NNN`) entsprechen. Mappings zeigen auf Wildcards
   (`TC-001-*`) oder sind semantisch falsch (Readiness-Tests, Feed-Cancel, Fertilizer-Suche).
   → Für **R4** (`record_property('tc_id', …)`) bedeutet das: die **test-deklarierte** TC-ID
   lässt sich maschinenlesbar ins Protokoll heben, aber die echte Rückverfolgbarkeit zur Spec
   bleibt schwach, bis die Mappings bereinigt sind (Folge-Issues).
2. **Fehlende „Spec-TC Mapping"-Header** in 2 Kern-Dateien:
   `test_req004_feeding_events.py` und `test_req008_post_harvest.py`.
3. **Fehl-Mappings auf Sammel-IDs:** Flushing-/Runoff-Tests in
   `test_req004_nutrient_calculations.py` verweisen pauschal auf `TC-004-028` (Seitenaufruf)
   statt auf die inhaltlich passenden `TC-004-043…047`.
4. **Test-ID-Kollision:** `feeding_events.py` nutzt `TC-REQ-004-040…057`, überschneidet sich
   mit dem Bereich von `nutrient_plan.py`.
5. **Schwache Assertions:** Mehrere Sowing-/Season-Tests sind Screenshot-only ohne Hard-Assert
   → nominell abgedeckt, faktisch Smoke-Level.

## Detail je Kernfunktion

### 1. Pflanzenerfassung
- **Ist-Tests:** `test_req001_plant_instance.py` (16), `test_req001_core_lifecycle_journey.py` (3, J079–J081).
  `test_req001_lifecycle.py` (8) ist **themenfremd** (Species-/GrowthPhase-Stammdaten, nicht Instanz).
- **Abgedeckt:** `TC-001-079` (Species/Sorte anlegen), `TC-001-080` (Instanz anlegen+verifizieren),
  `TC-001-081` (Attribute bearbeiten+Persistenz) — sauber traceable über die Journey-Tests;
  ergänzend breite funktionale PI-Tests (Liste/Detail/Suche/Sortierung/Validierung).
- **Lücke:** `TC-001-032` — Instanz-Anlage **aus der Species-Detailseite** (vorbelegtes Art-Feld);
  ungetesteter Einstiegspfad (alle Ist-Tests gehen über die Listenseite).
- **Traceability:** PI-Tests hängen nur an Wildcard-`TC-001-*`/`TC-003-*` statt an konkreten IDs.

### 2. Gießen/Bewässerung
- **Ist-Tests:** `test_req004_watering_log.py` (16), `test_req004_core_lifecycle_journey.py` (2 watering-Schritte).
- **Abgedeckt:** `TC-004-089`, `TC-004-090` (Core-Journey Gießen) — korrekt gemappt.
- **Lücke:** komplette Gruppe I **Gießplan/WateringSchedule** `TC-004-055…060` (6 TCs) ohne E2E.
- **Drift:** Die 16 Watering-Log-CRUD-Tests laufen unter **erfundenen** `W`-IDs
  (`TC-REQ-004-W001…W009`), die es in der Spec nicht gibt; es existiert keine dedizierte
  Spec-Gruppe für Watering-Log-CRUD (nur beiläufig über `TC-004-089/090`).

### 3. Düngen/Dünger
- **Ist-Tests:** `fertilizer.py` (23), `nutrient_plan.py` (21), `feeding_events.py` (14),
  `nutrient_calculations.py` (21) = 79 Funktionen.
- **Abgedeckt:** ~18 Spec-TCs explizit (~22 %) — List/Create/Detail-Smoke + funktionale Panels
  (`TC-004-001/002/006/007/008/009/010/012/013/015/016/017/021/027/028/029/031/032`).
- **Lücken (kern-fachlich):** Dünger↔Phase-Zuweisung (`019/020`), EC-Budget `022`, Plan
  klonen/zuweisen (`023/024/025/026`), WaterMix/CalMag (`034–037`), NED-Dosierungsrechner
  (`038–042`), Foliar-Warnungen (`049–051`), Gantt (`061–067`), Multi-Channel (`068–075`),
  EC-Budget-Mathematik REQ-004-A (`076–083`), Auth/Tenant (`084/085`), Responsive (`086/087`),
  organische Freiland-Düngung `088`, Core-Journey FeedingEvent `091`.
- **Drift:** Flushing/Runoff auf `TC-004-028` statt `043–047`; `feeding_events.py` ohne Header;
  Fertilizer-„Suche" auf `TC-004-002` (Typ-Filter) gemappt, testet aber Textsuche.

### 4. Ernte (REQ-007 + REQ-008)
- **Ist-Tests:** `harvest_list.py` (14), `harvest_detail.py` (15), `harvest_readiness.py` (3),
  `post_harvest.py` (1, self-skippender Scaffold) = 33 Funktionen.
- **Abgedeckt REQ-007:** 23/47 mit überwiegend sauberer 1:1-Referenzierung (Liste, Create-Dialog,
  Detail-Tabs, Edit, Quality, Yield).
- **Lücken REQ-007:** `TC-007-013` **Karenzzeit-Gate (Critical, REQ-010-Integration)**,
  `TC-007-036` **vollständige Ernte-Journey (Critical)**, Erntereife-Karten-Varianten
  (`032–034`), Ernte-Fenster-/GDD-Prognose (`043–047`), diverse Validierungen (`011/024/029/031`).
- **Lücke REQ-008:** **0/68 abgedeckt** — Post-Harvest faktisch ungetestet (Route `/post-harvest`
  laut Scaffold noch nicht verdrahtet). Betrifft Batch-Statusmaschine, Trocknung, Curing,
  Schimmel-Alert, Lager, Karenz-Gate (`008-002/003`) u. a.
- **Drift:** `harvest_readiness.py` referenziert `TC-007-036/037`, testet aber inhaltlich
  `TC-007-032…035` → die referenzierten TCs gelten trotzdem als **nicht** abgedeckt.

### 5. Aussaat-/Kalenderansicht
- **Ist-Tests:** `calendar.py` (17), `sowing_calendar.py` (9), `season_overview.py` (6) = 32.
- **Abgedeckt:** 20/57 (~35 %) — Ansichtswechsel (`001–007`), Filter-Chips (`010`),
  Feed-CRUD (`030/031/036`), Aussaat-Basis (`040/046/048/049`), Saisonübersicht (`060–062`).
- **Lücken:** Balken-**Berechnungsregeln** (REQ-015-A §3, Abschnitt J `100–104` komplett),
  GrowingPeriods/Wrap-around/annual_repeat (`050–053`), Zierpflanzen-Blüte (`043`),
  Timeline/Event (`020/021/023/024`), Feed-Token/Delete (`032–034`), Security (`080–082`),
  Responsive (`070–072`), i18n/Farben (`090/091`).
- **Drift:** 3 semantische Mapping-Ungenauigkeiten (Feed-Cancel→`035`, Kategorie-Chips→`046`);
  mehrere „abgedeckte" Sowing-Tests ohne Hard-Assert.

## Konsequenzen für die Identifizierbarkeit-Mechanik (nächster Schritt)

- **Feature-Marker-Startsatz bestätigt (A1):** `plant`, `watering`, `nutrient`, `harvest`, `calendar`.
- **Journey-Dateien sind cross-cutting:** `test_req004_core_lifecycle_journey.py` mischt
  `watering` + `nutrient`; `harvest` spannt über REQ-007 **und** REQ-008. → Die Datei-Level-
  Feature-Konstante (R2) muss **mehrere** Feature-Marker je Datei erlauben (Tupel/Liste), nicht
  nur einen. Zusätzlich empfiehlt sich ein `journey`-Marker für die Core-Lifecycle-Journeys.
- **record_property (R4)** hebt die test-deklarierte TC-ID; die Header-Bereinigung (Drift,
  fehlende Header in 2 Dateien) wird als Folge-Issue notiert, **nicht** in dieser Iteration gefixt.

## Empfohlene Folge-Issues (außerhalb dieser Iteration)

1. REQ-008 Post-Harvest: E2E-Abdeckung nach Verdrahtung der `/post-harvest`-Route aufbauen (68 TCs).
2. `TC-007-013` (Karenz-Gate) + `TC-007-036` (Ernte-Journey) als Critical schließen.
3. Dünger-Kernlogik: EC-Budget (REQ-004-A `076–083`), Phase-Zuweisung, WaterMix/NED.
4. Gießplan-Gruppe `TC-004-055…060`.
5. Kalender-Berechnungsregeln (Abschnitt J) + Security `080–082`.
6. Traceability-Sanierung: Drift-Mappings korrigieren, fehlende „Spec-TC Mapping"-Header
   in `feeding_events.py` + `post_harvest.py` ergänzen, erfundene `W`-/`PI`-IDs auf Spec-IDs rückmappen.
