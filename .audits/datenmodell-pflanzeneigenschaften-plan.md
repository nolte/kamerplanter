---
plan-type: data-model-implementation
title: Umsetzungsplan — vollständige Datenmodell-Abbildung der Pflanzen-Eigenschaftsreferenz
quelle: spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md
betroffene-reqs: REQ-001, REQ-003, REQ-007, REQ-008, REQ-017, REQ-021
status: partially-implemented (Phase A+B via #192)
created: 2026-06-15
fortsetzung: abgeschlossen via #453 (Backfill WP-10, Toxizitäts-Badge WP-7, Härtung)
hinweis: >-
  Phase A (additive Felder/Enums) und die breaking Phase B (propagation_configs)
  sind via #192 umgesetzt; der Feld-Backfill (WP-10 A1-A4), das Toxizitäts-Badge
  (WP-7) und die Härtung (WP-6f SeedType-Enum, WP-9 Enum-Sync-Gate) sind über
  #453 nachgezogen. Verbliebener A1-Rest (leek/beetroot/Brussels sprouts in
  adventskalender.yaml + Loader-Whitelist) via #453 geschlossen.
---

# Umsetzungsplan: Pflanzen-Eigenschaften vollständig im Datenmodell abbilden

**Zweck.** Dieser Plan stellt sicher, dass **jede** Erkenntnis aus der art-übergreifenden Referenz
(`spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md`) **lückenlos** ins Datenmodell überführt wird, und
bildet die verbindliche Grundlage für die nachgelagerte Backend- und Frontend-Entwicklung. Er ist
**code-geerdet**: jedes Arbeitspaket nennt die real betroffenen Dateien, Enums, Schichten, die
Seed-Backfill-Strategie für die ~200 Bestandsarten, die Frontend-Kaskade inkl. Erfahrungsstufe und die
Definition of Done.

**Vollständigkeits-Garantie.** §9 enthält eine Traceability-Matrix, die jede Referenz-Erkenntnis genau
einem Arbeitspaket (oder dem Status „bereits abgedeckt") zuordnet. Kein Befund fällt durch.

---

## 1. Architektur-Randbedingungen (gelten für ALLE Arbeitspakete)

Aus der Code-Kartierung verifizierte Invarianten — sie bestimmen Aufwand und Reihenfolge:

1. **Enum-Single-Source ist dreifach zu pflegen.** Ein kontrolliertes Vokabular lebt an drei Stellen, die
   synchron bleiben **müssen**:
   - `src/backend/app/common/enums.py` (Python `StrEnum`, Code-Wahrheit)
   - `src/backend/app/migrations/seed_data/schemas/_defs.schema.yaml` (`$defs`, von allen `*.schema.yaml` per `$ref` genutzt)
   - `src/frontend/src/api/types.ts` (TS-Union, **manuell** — es gibt **kein** OpenAPI-Codegen)
   → Jeder neue Enum-Wert = 3 Stellen + i18n (de/en) + lokale Frontend-Konstante (z. B. `PROPAGATION_METHODS` in `SpeciesDetailPage.tsx`).
2. **ArangoDB ist schemalos.** Kein `ALTER TABLE`/keine DB-Migration. Neue **optionale** Felder sind für
   Bestandsdokumente unkritisch (Pydantic setzt Defaults). Der reale Aufwand ist die **fachliche
   Befüllung** der ~200 Bestandsarten (Seed-YAML + Pipeline).
3. **Keine separaten DTOs/Mapper.** Domain-Pydantic-Modelle werden direkt serialisiert. API-Request/Response
   liegen getrennt in `api/v1/species/schemas.py` (`SpeciesCreate`/`SpeciesResponse`) und müssen mitgezogen werden.
4. **Frontend-Kaskade je Feld** (verifiziert am `propagation_methods`-Vorbild): `api/types.ts` →
   `SpeciesDetailPage.tsx` (Zod-Schema + Formfeld + Card) → ggf. `GrowingPeriodsSection.tsx` →
   `config/fieldConfigs.ts` (Erfahrungsstufe) → `i18n/locales/{de,en}/translation.json` → Tests.
5. **Erfahrungsstufen-Gating** ist deklarativ: `config/fieldConfigs.ts` (`level: beginner|intermediate|expert`)
   + `ExpertiseFieldWrapper` + `useExpertiseLevel()` (Redux `userPreferences.experience_level`).
6. **CI / Definition of Done:** Backend `ruff` + `pytest` Coverage ≥ 60 %; Frontend `tsc` + ESLint + Vitest
   Coverage ≥ 80 % + Build; Security-Scans; Claude-Code-Review. **Spec-Validierung und i18n-Vollständigkeit
   sind aktuell KEIN CI-Gate** (siehe WP-9, optionale Härtung).
7. **Spec-Pflege:** REQ-Dokumente unter `spec/req/` werden bei Modelländerung mit **Versions-Bump +
   Changelog-Zeile + Feld-Tabelle** aktualisiert. Architektonisch signifikante Änderungen → ADR unter
   `spec/decisions/`.
8. **Seed-Pipeline für Bestandsdaten:** `spec/knowledge/plants/*.md` (210 Steckbriefe) → Agent
   `plant-info-to-seed-yaml` → `src/backend/app/migrations/seed_data/plant_info*.yaml` → Loader
   `seed_plant_info*.py`; Validierung via Agent `seed-data-validator` (3-Quellen-Regel).

---

## 2. Ausgangslage — was schon abgedeckt ist (kein Code nötig, nur Spec-Doku)

Damit der Plan nicht Vorhandenes neu baut: Folgende Referenz-Befunde sind im realen Modell **bereits korrekt** umgesetzt:

| Referenz-Befund | Bestehendes Feld / Struktur | Aktion |
|---|---|---|
| Nutzungstyp mehrwertig (Zier/Nutz/Heil…) | `Species.traits: list[PlantTrait]` (ornamental, edible, medicinal, …) | nur in REQ-001 als Erfüllung des Befunds dokumentieren |
| Winterhärte Zone + Sensitivität | `Species.hardiness_zones`, `frost_sensitivity (FrostTolerance)`, `hardiness_detail` | dokumentieren |
| Familie als Lookup + Fruchtfolge | `BotanicalFamily` (`rotation_category`, `nitrogen_fixing`, `common_pests/diseases`) | dokumentieren |
| Lebensdauer Grundklassen | `LifecycleConfig.cycle_type (CycleType)` + `dormancy_required`, `vernalization_required` | dokumentieren; Erweiterung in WP-3/WP-4 |
| Samenfest vs. F1 | `Cultivar.seed_type` (**als `str`, nicht Enum** → WP-6f Härtung) | tightening optional |
| Post-Harvest Curing/Lagerung | Harvest-Protokolle (`drying/curing/aging/hardening/storage`) | dokumentieren |
| Karenz/PHI an Behandlung | IPM/REQ-010 (mittel × kultur), ADR-001 Karenz-Gate | dokumentieren (richtig verortet) |
| Anbau-Kernparameter Licht/Wasser/pH/Photoperiode | `shade_tolerance`, `watering_guide`, `soil_ph_preference`, `nutrient_demand_level`, `photoperiod_type` | Gating-Audit in WP-7 |

---

## 3. Gap → Arbeitspaket-Übersicht

| WP | Referenz (§/E) | Inhalt | Breaking? | Backfill 200 Arten? | Backend-Aufwand | Phase |
|----|----------------|--------|:---------:|:-------------------:|-----------------|:-----:|
| **WP-1** | §1.2 / E1 | `GrowthHabit` erweitern (Gras, Sukkulente, Geophyt, Farn, Wasser, Epiphyt, Halbstrauch) | nein (additiv) | Reklassifizierung (Qualität) | gering | A |
| **WP-2** | §1.1 / 1A | Gemüse-Untergruppe / `harvested_part` als Verwendungs-Facette | nein | ja (Nutzpflanzen) | gering | A (mit WP-6b) |
| **WP-3** | §2.1 / E2 | Lebensdauer-Split „botanisch vs. in Kultur" | nein | Teilmenge (tender perennials) | gering | A |
| **WP-4** | §2.2 / E3 | Blüh-Strategie `monocarpic/polycarpic` | nein | Teilmenge | gering | A |
| **WP-5** | §3.3 / E4 | Vermehrung **pro Methode** (`propagation_configs`) + Enum-Drift-Fix | **JA** | logische Migration (~200) | hoch (~2,5–3 T) | **B (Entscheidung)** |
| **WP-6** | §4 / E5 | Ernte: `harvest_pattern`, `harvested_part`, `dtm_reference`, `climacteric`, Ertragsbeginn | nein | ja (Nutz/Obst) | mittel | A |
| **WP-7** | §5–6 / A-Klasse | Pflicht-Parameter-Audit + Toxizitäts-Badge stufenunabhängig + A/B/C-Tiering | nein | nein | gering (FE-lastig) | A |
| **WP-8** | §10 / E6 | Quelle/Methode pro strittigem Wert (Provenienz) | nein | optional | gering | C (optional) |
| **WP-9** | §0/§10 | Spec-/ADR-Pflege + Enum-Single-Source-Reconciliation + optionale CI-Gates | nein | – | gering–mittel | quer |
| **WP-10** | quer | **Daten-Backfill der 210 Arten** über Pipeline (dominanter Aufwand) | nein | ja (alle) | hoch (Recherche-gebunden) | C |

---

## 4. Arbeitspakete im Detail

> Konvention je WP: **Ziel · Datenmodell · Enum/Schema · API · Frontend (inkl. Stufe) · Seed/Backfill · Spec · Tests · DoD · Aufwand · Abhängigkeiten.**

### WP-1 — Wuchsform-Enum vollständig (E1, §1.2)

- **Ziel:** `GrowthHabit` deckt die reale botanische Vielfalt ab; kontextuelle Pflege-UI (Stütze, Pflanztiefe, Bewässerungs-Default) kann daran ansetzen.
- **Datenmodell:** `Species.growth_habit` (Typ bleibt `GrowthHabit`) — keine Modelländerung, nur Enum-Erweiterung.
- **Enum/Schema:** in `common/enums.py` ergänzen: `SUBSHRUB`, `GRASS`, `SUCCULENT`, `BULB_GEOPHYTE`, `FERN`, `AQUATIC`, `EPIPHYTE`. Spiegeln in `_defs.schema.yaml` (`growth_habit`-Wertliste). `plant_info.schema.yaml` nutzt `$ref` → keine Änderung.
- **API:** automatisch (Enum-Serialisierung als String).
- **Frontend:** `api/types.ts` (`GrowthHabit`-Union) + lokale Options-Quelle in `SpeciesDetailPage.tsx` + i18n `enums.growthHabit.*` (de+en, 7 neue Keys). Stufe: bestehend (`growth_habit` ist Grundfeld, Anfänger-sichtbar).
- **Seed/Backfill:** additiv → kein Pflicht-Backfill. **Daten-Qualität:** Bestandsarten, die heute in `herb/shrub` gezwängt sind (Kakteen, Zwiebelpflanzen, Farne, Wasserpflanzen), in WP-10 reklassifizieren.
- **Spec:** REQ-001 Versions-Bump + Changelog + `growth_habit`-Wertliste.
- **Tests:** Enum-Konvertierungs-Cases (Backend); Frontend-Optionsrendering.
- **DoD:** 3 Enum-Stellen synchron, i18n vollständig, Tests grün.
- **Aufwand:** Backend ~1 h, Frontend ~1 h (+ Reklassifizierung in WP-10).
- **Abhängigkeiten:** keine.

### WP-2 — Gemüse-Untergruppe / Verwendungs-Facette (1A, §1.1)

- **Ziel:** Die essbarteil-basierte Gemüse-Systematik abbilden, **ohne** die Familie (Fruchtfolge) zu vermischen — die Referenz zeigt, dass beide widersprechen dürfen (Rettich = Wurzelgemüse *und* Brassica).
- **Entscheidung:** Keine eigene Gemüse-Untergruppen-Enum nötig — sie ist aus `harvested_part` (WP-6b) + `BotanicalFamily` ableitbar. **Diese WP geht in WP-6b auf**; hier nur die Doku-Festlegung „Verwendung ≠ Familie sind getrennte Felder, Widerspruch erlaubt".
- **Spec:** REQ-001 Hinweis; Validierung: `rotation_category` (Familie) und `harvested_part` (Verwendung) **nicht** gegeneinander constrainen.
- **Aufwand:** trivial (Doku).

### WP-3 — Lebensdauer „botanisch vs. in Kultur" (E2, §2.1)

- **Ziel:** „einjährig in Kultur" / tender perennial korrekt abbilden (Tomate botanisch mehrjährig, in Kultur einjährig) → korrekte Überwinterungs- und Saison-Ende-Hinweise.
- **Datenmodell:** `LifecycleConfig.cycle_type` bleibt = **botanische** Lebensdauer. Neu: `cultivation_cycle_type: CycleType | None` (überschreibt für die Kultur-Praxis). Abgeleitetes Read-Flag `grown_as_annual = cultivation_cycle_type == ANNUAL and cycle_type != ANNUAL`.
- **Enum/Schema:** wiederverwendet `CycleType` (kein neuer Enum). Feld in `_defs`/`plant_info.schema.yaml` + Pydantic.
- **API/Frontend:** Feld in `LifecycleConfig`-Schema + Lifecycle-Tab in `SpeciesDetailPage.tsx`; i18n; Stufe `intermediate`.
- **Seed/Backfill:** Teilmenge (frostempfindliche Dauerkulturen) in WP-10.
- **Spec:** REQ-001 + REQ-003 Bump.
- **Tests:** Validator (cultivation ≠ botanical), Flag-Ableitung.
- **Aufwand:** Backend ~1,5 h, Frontend ~1,5 h.
- **Abhängigkeiten:** keine.

### WP-4 — Blüh-Strategie monokarp/polykarp (E3, §2.2)

- **Ziel:** „blüht einmal, stirbt danach" abbilden (Agave, viele Bambusse), damit ein scheinbar dauerhafter Bestand das Terminal-Ereignis kennt.
- **Datenmodell:** `LifecycleConfig.flowering_strategy: FloweringStrategy | None`.
- **Enum/Schema:** neuer `FloweringStrategy(StrEnum)` = `monocarpic`, `polycarpic` (3 Single-Source-Stellen).
- **API/Frontend:** Lifecycle-Tab; i18n `enums.floweringStrategy.*`; Stufe `expert`.
- **Phasen-Logik:** bei `monocarpic` + `is_terminal`-Phase → UI-Hinweis „blüht einmal, stirbt danach" (Hook an bestehende `GrowthPhase.is_terminal`).
- **Seed/Backfill:** Teilmenge in WP-10.
- **Spec:** REQ-003 Bump.
- **Tests:** Enum + Terminal-Hinweis-Render.
- **Aufwand:** Backend ~1 h, Frontend ~1 h.

### WP-5 — Vermehrung: Parameter pro Methode (E4, §3.3) — **BREAKING, Entscheidungs-Gate**

> **Dies ist der einzige strukturelle Umbau und der wichtigste Plan-Entscheidungspunkt — siehe §5.**

- **Ziel:** Zeitfenster/Hinweise gehören an die **Methode**, nicht an die Art. Heute koppeln die flachen
  `propagation_months`/`propagation_notes` die Monate fälschlich an die ganze Art (Weichholzsteckling
  Mai–Juli *vs.* Teilung Herbst lassen sich nicht trennen).
- **Datenmodell (Zielstruktur):**
  ```python
  class PropagationConfig(BaseModel):
      method: PropagationMethod
      months: list[int] = Field(default_factory=list)   # 1..12, dedupliziert/sortiert
      wood_stage: WoodStage | None = None               # softwood|semi_hardwood|hardwood|herbaceous (nur cutting)
      difficulty: PropagationDifficulty | None = None
      notes: str | None = Field(default=None, max_length=1000)

  class Species(...):
      propagation_configs: list[PropagationConfig] = Field(default_factory=list)
      # ENTFERNT: propagation_methods, propagation_months, propagation_notes
  ```
  Empfehlung gegen Enum-Explosion: Stecklings-Reifegrad als **Parameter** `wood_stage` statt als eigene
  `PropagationMethod`-Werte (die Referenz erlaubt beides; Parameter ist wartungsärmer).
- **Enum-Drift-Fix (Pflicht):** `enums.py` und `_defs.schema.yaml` mit der REQ-017-Liste angleichen —
  fehlen aktuell `air_layering`, `tissue_culture`, `bulbil`, `water_propagation`. `propagation_difficulty`
  von `str` → `PropagationDifficulty(StrEnum)` (`easy|moderate|difficult`).
- **API:** `SpeciesCreate`/`SpeciesResponse` umbauen (breaking) — `propagation_configs` statt drei Felder.
- **Migration (schemalos, daher logisch):** Seeder-Transform flach → `propagation_configs`; Einmal-Skript/AQL
  `UPDATE` über alle ~200 Dokumente (methods × months auf ein Config-Objekt mit gemeinsamen months mappen,
  notes übernehmen) — **fachliche Aufteilung methodenspezifischer Monate** erfolgt in WP-10 (Daten-Qualität).
- **Frontend:** `api/types.ts` (neuer `PropagationConfig`-Typ); `SpeciesDetailPage.tsx` `FormMultiSelectField`
  → **wiederholbarer Config-Editor** (Methode + Monatsgrid + wood_stage + notes je Zeile); `GrowingPeriodsSection.tsx`
  Propagations-Card auf per-Methode-Anzeige umstellen; i18n; Stufe `intermediate`.
- **Spec:** REQ-001 **und** REQ-017 Bump; **ADR-004** „Vermehrung als strukturierte per-Methode-Objekte"
  (architektonisch signifikant, ersetzt öffentliches API-Schema).
- **Tests:** ~100 Cases neu (Model, Seeder-Transform, API, FE-Editor).
- **DoD:** flache Felder entfernt, Migration idempotent, alle Bestandsdaten transformiert, FE-Editor +
  Tests grün, ADR-004 merged.
- **Aufwand:** ~17–24 h (2,5–3 Tage) inkl. Frontend.
- **Abhängigkeiten:** **Branch-Timing** — am billigsten *jetzt*, solange `feat/species-propagation-methods`
  frisch ist und kein Consumer auf die flachen Felder festgelegt ist.

### WP-6 — Ernteverhalten vollständig (E5, §4)

Modular; jedes Teilpaket ist eine eigene additive Erweiterung.

- **WP-6a `harvest_pattern: HarvestPattern`** = `single | continuous | perennial` (Lebens-Muster).
  ⚠ **Abgrenzung dokumentieren:** das **bestehende** `HarvestType` (`partial/final/continuous`) beschreibt
  den **einzelnen Erntevorgang**, nicht das Lebensmuster — beide Felder koexistieren. Feld auf `Species`.
- **WP-6b `harvested_part: HarvestedPart`** = `fruit | seed | leaf | root | tuber | bulb | flower_bud | flower | stem | whole_plant`. Feld auf `Species`. (Erfüllt zugleich WP-2.) ⚠ orthogonal zu `harvest_pattern`.
- **WP-6c `dtm_reference: DtmReference`** = `direct_seed | transplant`, Begleiter zum bestehenden
  `Cultivar.days_to_maturity` (ohne Bezugspunkt ist DTM mehrdeutig — Quellenkonvention divergiert nachweislich).
- **WP-6d `climacteric: ClimactericClass`** = `climacteric | non_climacteric | atypical` (**dritter Wert ist
  Pflicht** — Honigmelone/Blaubeere/Paprika/Feige sind echte Grenzfälle). Feld auf `Species`; steuert Nachreif-/Lagerlogik.
- **WP-6e Ertragsbeginn:** `Cultivar.years_to_first_harvest` existiert → als Korridor `bearing_start_year_min/max`
  präzisieren (unterlagen-/pflanzgutabhängig). Nur bei `harvest_pattern = perennial`.
- **WP-6f (optional) `Cultivar.seed_type`** von `str` → `SeedType(StrEnum)` härten (`open_pollinated|f1_hybrid|f2|landrace|clone`).
- **Enum/Schema:** 4 neue Enums (`HarvestPattern`, `HarvestedPart`, `DtmReference`, `ClimactericClass`) je 3 Stellen.
- **Frontend:** Felder in `SpeciesDetailPage.tsx` (Card „Ernte"); i18n; Stufen: `harvest_pattern`/`harvested_part`
  `intermediate`, `climacteric`/`dtm_reference` `expert`.
- **Seed/Backfill:** Nutz-/Obstarten in WP-10 (climacteric nur Obst).
- **Spec:** REQ-007 + REQ-008 Bump.
- **Tests:** Enums, Orthogonalitäts-Validator (pattern × part frei kombinierbar), perennial-Guard für Ertragsbeginn.
- **Aufwand:** Backend ~4 h, Frontend ~4 h.

### WP-7 — Pflicht-Anbau-Parameter & Sicherheits-Badge (A-Klasse, §5–6)

- **Ziel:** Garantieren, dass die als **zwingend** (Klasse A) klassifizierten Parameter erfasst **und** für
  Anfänger sichtbar sind; Toxizität ist stufenunabhängig prominent.
- **Audit (Backend, meist vorhanden):** Licht → `shade_tolerance` (full_sun…deep_shade) ✅; Wasser →
  `watering_guide` ✅; Frost → `frost_sensitivity`/`hardiness_zones` ✅; Drainage → `waterlogging_tolerance` ✅;
  Toxizität → `ToxicityInfo` ✅; Standortbindung → **prüfen**, ob explizites `site_type`/`PlantCategory`-Feld
  am Species hängt, sonst ergänzen.
- **Frontend (Kern dieser WP):**
  - `config/fieldConfigs.ts` konsequent nach **A=beginner / B=intermediate / C=expert** ausrichten (A1–A6 → beginner).
  - **Toxizitäts-Badge** über `ExpertiseFieldWrapper` hinweg **immer** rendern (Sonderregel: schützt Mensch/Tier,
    nicht die Pflanze) — explizite Ausnahme im Gating-Code.
  - Anfänger-Skalen qualitativ halten (Symbole/Stufen), numerische Skalen erst ab `intermediate`.
- **Spec:** REQ-021 Bump (A/B/C-Mapping + Toxizitäts-Sonderregel dokumentieren).
- **Tests:** Stufen-Sichtbarkeit (`createStoreWithExpertise`), Badge bei `beginner` sichtbar.
- **Aufwand:** Backend ~1 h (Audit/ggf. site_type), Frontend ~3 h.

### WP-8 — Provenienz pro strittigem Wert (E6, §10) — optional

- **Ziel:** Bei quellenabhängig strittigen Werten (Klimakterik, GDD-Basistemperatur, Standjahre) Herkunft/Methode
  speicherbar machen.
- **Datenmodell:** leichtgewichtiges Muster `*_source: str | None` an den betroffenen Feldern **oder** generisches
  `field_provenance: dict[str,str]`. Pro Sorte überschreibbar.
- **Priorität:** niedrig; erst nach WP-6 sinnvoll. Kann als Doku-Konvention starten.
- **Aufwand:** ~2 h, falls umgesetzt.

### WP-9 — Spec-/ADR-Pflege & Enum-Single-Source-Reconciliation (quer)

- **Spec-Bumps:** REQ-001, REQ-003, REQ-007, REQ-008, REQ-017, REQ-021 (je Versions-Bump + Changelog +
  Feld-Tabellen) — gebündelt pro WP-PR, nicht separat.
- **ADR-004** für WP-5 (breaking).
- **Enum-Reconciliation:** `enums.py` ↔ `_defs.schema.yaml` ↔ `api/types.ts` für alle berührten Enums in
  Einklang bringen; REQ-017-Drift (air_layering, tissue_culture, bulbil, water_propagation) schließen.
- **Optionale CI-Härtung (Empfehlung):** zwei fehlende Gates ergänzen — (a) Enum-Sync-Check
  (enums.py vs. `_defs.schema.yaml`), (b) i18n-Vollständigkeit (de↔en) via Agent `i18n-completeness-checker`.
  Verhindert genau die Drift-Klasse, die dieser Plan adressiert.
- **Aufwand:** Spec ~3 h; CI-Gates ~0,5 Tag (optional).

### WP-10 — Daten-Backfill der 210 Bestandsarten (dominanter Aufwand)

- **Ziel:** Jedes neue/erweiterte Feld bekommt für die Bestandsarten **fachlich verifizierte** Werte — sonst
  ist die Modellabbildung formal, aber nicht „vollständig".
- **Felder mit Backfill-Bedarf:** Wuchsform-Reklassifizierung (WP-1), `cultivation_cycle_type` (Teilmenge),
  `flowering_strategy` (Teilmenge), `propagation_configs` fachliche Methoden-Monate (WP-5),
  `harvest_pattern`/`harvested_part` (alle Nutzarten), `climacteric` (Obst), `dtm_reference` (Kulturen mit DTM).
- **Pipeline:** je Batch (Zimmer/Outdoor) `plant-info-document-generator` (Recherche, 3-Quellen) → Markdown-Update
  (`spec/knowledge/plants/*.md`, neue Tabellen-Spalten + KA-Feld-Mapping) → `plant-info-to-seed-yaml` →
  `plant_info*.yaml` → `seed-data-validator` (Plausibilität/Referenzintegrität) → Loader-UPSERT.
- **Reihenfolge:** **nach** Schema-Stabilisierung (alle Enums/Felder gemerged), sonst doppelte Recherche.
- **Aufwand:** hoch, recherche-gebunden (~60 % Daten, 40 % Mechanik) — als eigene Batch-Serie planen.
- **Abhängigkeiten:** WP-1, WP-3, WP-4, WP-5, WP-6.

---

## 5. Entscheidungspunkt WP-5 (E4): jetzt umbauen oder flach belassen?

**Empfehlung: WP-5 jetzt durchführen** — auf bzw. unmittelbar nach `feat/species-propagation-methods`,
**vor** weiterem Daten-Backfill (WP-10) und vor neuen Consumern der flachen Felder.

**Begründung (evidenzbasiert):**
- Die flachen Felder wurden gerade erst durch alle 5 Schichten + ~200 Seed-Datensätze + Tests gezogen. Die
  Daten sind frisch und in **einem** Bearbeitungskontext — die fachliche Re-Aufteilung der Monate pro Methode
  ist jetzt am billigsten.
- Jeder weitere Tag erhöht die Kosten: zusätzliche Consumer (Frontend, Export, Knowledge-Service) verfestigen
  das flache Schema; späteres Aufbrechen ist teurer und riskanter (echter Breaking Change mit Migrationspfad).
- Der Umbau ist begrenzt (~2,5–3 Tage) und vollständig spezifiziert (WP-5). ArangoDB-Schemalosigkeit macht die
  Migration zu einer reinen Logik-Transformation ohne DB-Downtime.

**Alternative (falls abgelehnt):** flache Felder belassen, WP-5 zurückstellen — dann muss WP-10 die
methodenspezifischen Monate in `propagation_notes` als Freitext kodieren (Informationsverlust, nicht
abfragbar). Diese Option ist nur vertretbar, wenn die Vermehrungs-Zeitfenster kurzfristig nicht
programmatisch genutzt werden.

> Diese Entscheidung gehört dem Maintainer; der Plan ist für **„jetzt umbauen"** optimiert (Phase B vor C).

---

## 6. Sequenzierung & PR-Schnitt

**Phase A — additive, nicht-breaking (parallelisierbar):** WP-1, WP-2(=WP-6b), WP-3, WP-4, WP-6, WP-7.
Reine Enum-/Feld-Erweiterungen; kein Consumer bricht.

**Phase B — breaking (Entscheidungs-Gate, §5):** WP-5 + ADR-004. Möglichst direkt nach Phase A, vor WP-10.

**Phase C — Daten & Härtung:** WP-10 (nach Schema-Stabilisierung), WP-8 (optional), WP-9 CI-Gates (optional).

**Quer:** WP-9 Spec-Bumps gebündelt in den jeweiligen WP-PRs.

**PR-Schnitt je WP** (nach Repo-Konvention):
1. Backend: Enum + Domain-Modell + API-Schema + Unit-Tests (+ ADR bei WP-5)
2. Seed-Schema: `_defs.schema.yaml` + `plant_info.schema.yaml` + `seed-data-validator`-Anpassung
3. Frontend: `api/types.ts` + Komponente + `fieldConfigs.ts` + i18n (de/en) + Vitest
4. Seed-Daten: `plant_info*.yaml`-Batch + Loader (Teil von WP-10)
5. E2E: Selenium-Journey für die neue UI

Conventional-Commit-Titel mit REQ- und Versions-Referenz, z. B.
`feat(species): add harvest_pattern and harvested_part (REQ-007 v2.4→2.5)`.

---

## 7. Definition of Done (pro Arbeitspaket, verbindlich)

- [ ] Enum an **allen drei** Single-Source-Stellen synchron (`enums.py`, `_defs.schema.yaml`, `api/types.ts`)
- [ ] Pydantic-Domain-Modell + `SpeciesCreate`/`SpeciesResponse` aktualisiert, Validatoren ergänzt
- [ ] `plant_info.schema.yaml` per `$ref` korrekt; `seed-data-validator` kennt das Feld
- [ ] Frontend-Kaskade vollständig: Typ, Formfeld, Card, `fieldConfigs.ts`-Stufe, i18n **de + en**
- [ ] Backend-Unit-Tests, Coverage ≥ 60 %; Frontend-Vitest, Coverage ≥ 80 %
- [ ] REQ-Dokument: Versions-Bump + Changelog-Zeile + Feld-Tabelle; ADR bei architektonischer Signifikanz
- [ ] CI grün (ruff, pytest, tsc, ESLint, Build, Security, Claude-Review)
- [ ] Bestandsdaten-Strategie geklärt (sofort-Backfill in WP-10 verlinkt oder bewusst additiv-leer)

---

## 8. Aufwands-Summe (Backend+Frontend, ohne WP-10-Daten)

| WP | Backend | Frontend | Summe |
|----|:-------:|:--------:|:-----:|
| WP-1 | 1 h | 1 h | 2 h |
| WP-3 | 1,5 h | 1,5 h | 3 h |
| WP-4 | 1 h | 1 h | 2 h |
| WP-5 (breaking) | 10 h | 7 h | **17 h** |
| WP-6 | 4 h | 4 h | 8 h |
| WP-7 | 1 h | 3 h | 4 h |
| WP-9 (Spec, ohne CI-Gates) | 3 h | – | 3 h |
| **Σ Code** | | | **≈ 39 h (≈ 5 Tage)** |
| WP-10 Daten-Backfill | recherche-gebunden, Batch-Serie | | **dominanter Posten, separat** |
| WP-8 / WP-9-CI-Gates | optional | | +0,5–1 Tag |

---

## 9. Traceability-Matrix — jede Referenz-Erkenntnis → Arbeitspaket

| Referenz (Abschnitt / Empfehlung) | Erkenntnis | Abbildung |
|---|---|---|
| §0 / Kernprinzip | Orthogonale Dimensionen = getrennte Felder | strukturgebend für WP-3/4/6 (keine Sammel-Enums) |
| §1.1 / 1A | Nutzungstyp mehrwertig | **abgedeckt** (`traits`) + Doku WP-2 |
| §1.1 Quellenabweichung | Verwendung ≠ Familie (Rettich) | WP-2 (kein Cross-Constraint) |
| §1.2 / E1 | Wuchsform-Enum zu eng | **WP-1** |
| §1.2 Raunkiær | optionales wissenschaftliches Lebensform-Feld | WP-1 (optional, dokumentiert) |
| §1.3 | Standortklasse + Winterhärte getrennt | **abgedeckt** + Audit WP-7 |
| §1.4 | Familie als Lookup, Vererbung Art→Sorte | **abgedeckt** (`BotanicalFamily`, `Cultivar`) |
| §2.1 / E2 | Lebensdauer botanisch vs. in Kultur | **WP-3** |
| §2.2 / E3 | monokarp/polykarp | **WP-4** |
| §2.3 | Frost/Blattverhalten/Dormanz/Vernalisation | Frost+Dormanz **abgedeckt**; Blattverhalten optional (WP-9-Doku) |
| §3.1 | Aussaat-Parameter, samenfest/F1 | `seed_type` **abgedeckt** (Härtung WP-6f) |
| §3.3 / E4 | Vermehrung pro Methode | **WP-5** (breaking) |
| §3 / Enum-Drift | REQ-017 > enums.py Werte | **WP-5 / WP-9** |
| §4.1 / E5 | Erntemuster single/continuous/perennial | **WP-6a** |
| §4.2 | geernteter Teil, orthogonal | **WP-6b** |
| §4.3 / E5 | DTM-Bezugspunkt | **WP-6c** |
| §4.3 / E5 | Klimakterik 3-wertig | **WP-6d** |
| §4.3 | Ertragsbeginn nach Standjahren | **WP-6e** |
| §4.4 | Post-Harvest Curing/PHI | **abgedeckt** (Protokolle, ADR-001) |
| §5 A-Klasse | zwingende Anbau-Parameter | **WP-7** (Audit + Gating) |
| §5 A5 | Toxizität sicherheitskritisch, immer sichtbar | **WP-7** (Badge-Sonderregel) |
| §6 | Erfahrungsstufen-Mapping A/B/C | **WP-7** (`fieldConfigs.ts`) |
| §8 | UI-Implikationen (datengetriebene Formulare) | WP-5/6/7 Frontend |
| §10 / E6 | Quelle/Methode pro strittigem Wert | **WP-8** (optional) |
| §10 | Backfill regionaler/strittiger Werte | **WP-10** (3-Quellen-Pipeline) |

---

## 10. Risiken & offene Entscheidungen

1. **WP-5 Breaking-Timing** (§5) — Maintainer-Entscheidung; Plan empfiehlt „jetzt".
2. **Enum-Single-Source ohne Codegen** — manueller 3-Stellen-Sync ist fehleranfällig; WP-9-CI-Gate empfohlen.
3. **WP-10 ist der reale Kostentreiber** — die Code-WPs sind klein (~5 Tage), die fachliche Befüllung der 210
   Arten dominiert; früh als eigene Batch-Serie einplanen, nicht unterschätzen.
4. **Stecklings-Granularität** (WP-5) — `wood_stage` als Parameter statt Enum-Werte empfohlen (wartungsärmer); bei Bedarf umkehrbar.
5. **Backfill-Pflicht vs. additiv-leer** — neue Felder sind technisch optional; „vollständige Abbildung"
   verlangt die Befüllung. Pro WP entscheiden, was sofort (WP-10) vs. später befüllt wird.

---

*Grundlage: `spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` (verifizierte Domänenreferenz). Dieser Plan ist
art-übergreifend; sortenspezifische Werte bleiben an der `Cultivar`-Ebene bzw. in den Per-Art-Steckbriefen.*
