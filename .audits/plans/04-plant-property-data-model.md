---
plan-type: implementation-plan
title: Pflanzen-Eigenschaften-Datenmodell vervollständigen (Rest von WP-1..10)
epic: plant-property-data-model
covers: [WP-10, WP-7-rest, WP-6f, WP-8, WP-9-rest]
source-audit: .audits/datenmodell-pflanzeneigenschaften-plan.md
status: ready
created: 2026-07-10
verified-against: develop (Phase A+B DONE via #192)
parallelizable: true
specialist: fullstack-developer + seed-data pipeline agents
---

# Pflanzen-Eigenschaften-Datenmodell vervollständigen

## Ziel

Das Datenmodell der Pflanzen-Eigenschaften (`Species`/`Cultivar`, Enums, Frontend-Kaskade) ist
**strukturell fertig**: Phase A und die breaking Phase B des Ursprungsplans
`.audits/datenmodell-pflanzeneigenschaften-plan.md` wurden mit PR #192 (`050ba5664`) umgesetzt, der
3-Wege-Enum-Sync (`enums.py` ↔ `_defs.schema.yaml` ↔ `types.ts`) ist konsistent, ADR-004 ist Accepted.

Was **fehlt**, ist überwiegend keine Schema-Arbeit mehr, sondern:

1. Die **fachliche Befüllung** der neuen, additiv-leeren Felder über die ~196 Bestandsarten (WP-10) —
   der dominante Rest, recherche-gebunden.
2. Ein **einzelner echter Code-Gap mit Nutzerwirkung**: die vorhandene `Species.toxicity`-Struktur wird
   im Frontend gar nicht gerendert (WP-7-Rest, Toxizitäts-Badge).
3. **Optionale Härtung** (kein Nutzer-Blocker): `Cultivar.seed_type` → Enum, Feld-Provenienz, optionale
   CI-Gates, Spec-Bumps (WP-6f/WP-8/WP-9-Rest).
4. **Statuspflege** des Ursprungsplans, damit er nicht als komplett offen missverstanden wird.

Leitprinzip: Das Schema ist stabil und bleibt es. Alle vier Stränge sind additiv und voneinander
unabhängig, daher echt parallelisierbar.

## Ist-Stand (verifiziert 2026-07-10)

### DONE via #192 (`050ba5664`) — NICHT erneut umsetzen

| WP | Inhalt | Code-Anker (develop) |
|----|--------|----------------------|
| WP-1 | `GrowthHabit` StrEnum, 12 Werte (herb…epiphyte) | `common/enums.py:31-43` |
| WP-3 | `cultivation_cycle_type` Feld | `domain/models/lifecycle.py:42`; Feld auf `Species` |
| WP-4 | `FloweringStrategy` (monocarpic/polycarpic) | `common/enums.py:101-105` |
| WP-5 | `propagation_configs` (breaking; flache Felder entfernt) | `domain/models/species.py:140,289`; ADR-004 Accepted |
| WP-6a-e | `HarvestPattern`, `HarvestedPart`, `DtmReference`, `ClimactericClass`, `bearing_start_year_min/max` | `common/enums.py:108-150`; `domain/models/species.py:292-301` |
| WP-7-Tiering | Erfahrungsstufen-Gating der neuen Felder | `config/fieldConfigs.ts:28-38` (intermediate/expert) |
| WP-9-Enum-Sync | 3-Wege-Sync + ADR-004 | `enums.py` ↔ `seed_data/schemas/_defs.schema.yaml:25ff` ↔ `api/types.ts` |

### OFFEN — nur diese Arbeitspakete planen

**Seed-Befüllungszahlen** (verifiziert per `grep -o '^\s*<feld>:' plant_info*.yaml` in
`src/backend/app/migrations/seed_data/`, ~196 Arten gesamt):

| Feld | Befüllt | Bewertung |
|------|---------|-----------|
| `propagation_configs` | 183 / ~196 | gut — nicht im Fokus |
| `harvest_pattern` | 28 / ~196 | dünn — Fokus A1 |
| `harvested_part` | 28 / ~196 | dünn — Fokus A1 |
| `climacteric` | 13 | nur Obst, fachlich korrekt begrenzt — kein Fokus |
| `growth_habit` | 143 / ~196 | Reklassifizierungs-Qualität offen — Fokus A4 |
| `cultivation_cycle_type` | **0** (Zähler zeigt Feld nicht in `plant_info*.yaml`) | leer — Fokus A3 |
| `flowering_strategy` | **0 / ~196** | leer — Fokus A2 |

> Hinweis: `cultivation_cycle_type` erscheint in `lifecycle.py`/`Species`, ist aber in den
> `plant_info*.yaml`-Seeds noch nicht materialisiert (Zähler = 0). A3 legt es dort an.

**Code-Gaps (verifiziert):**

- `Species.toxicity: Toxicity | None` existiert (`domain/models/species.py:265-273`), wird aber im
  Frontend **nirgends gerendert** — `grep toxicity src/frontend/src/pages/stammdaten/SpeciesDetailPage.tsx`
  → NONE; kein `ToxicityBadge`; keine `alwaysVisible`-Ausnahme. `types.ts` kennt nur `toxicity_warning:boolean`
  (`api/types.ts:3691`), nicht die strukturierte `Toxicity`. → WP-7-Rest.
- `Cultivar.seed_type: str = ""` (`domain/models/species.py:81`) — Freitext statt Enum. → WP-6f.
- Provenienz nur record-level (`origin: DataOrigin`, `species.py:107,390`); kein feldweises
  `field_provenance`/`*_source`. → WP-8.
- CI: Enum-Sync und i18n-Vollständigkeit sind **kein** Gate (Ursprungsplan §1.6). → WP-9-Rest.
- Specs REQ-008/017/021 referenzieren die neuen Felder noch nicht. → WP-9-Rest.

## Arbeitspakete

### WP-10 — Daten-Backfill der neuen Felder (dominanter Rest)

**Problem.** Das Schema trägt die neuen Felder, aber die fachliche Befüllung über die ~196 Bestandsarten
fehlt weitgehend (siehe Tabelle). Additiv-leere Felder brechen keinen Consumer — daher ist der Backfill
nach **Zielfeld** schneidbar (A1-A4) und je Feld **echt parallel** ausführbar, nicht nach Art.

**Pipeline je Sub-Paket (pro Indoor-/Outdoor-Batch identisch):**
`plant-info-document-generator` (3-Quellen-Recherche pro Art) → Steckbrief-Update
`spec/knowledge/plants/*.md` → `plant-info-to-seed-yaml` → Ziel-`plant_info*.yaml` → `seed-data-validator`
→ Loader (`seed_plant_info.py` / `seed_plant_info_extended.py`).

**Betroffene Dateien/Pipeline.**
- Steckbriefe: `spec/knowledge/plants/*.md` (210 Dokumente, ~196 mit Seed-Eintrag)
- Seeds: `src/backend/app/migrations/seed_data/plant_info_indoor_{1..4}.yaml`,
  `plant_info_outdoor_{1..3}.yaml`, `plant_info_supplement_1.yaml`
- Schema (nur Lesen, keine Änderung): `seed_data/schemas/_defs.schema.yaml`,
  `seed_data/schemas/plant_info.schema.yaml`
- Loader: `src/backend/app/migrations/seed_plant_info.py`, `seed_plant_info_extended.py`
- Agenten: `plant-info-document-generator`, `plant-info-to-seed-yaml`, `seed-data-validator`,
  ggf. `growing-phase-auditor` (für A3/A4 biologische Konsistenz)

#### Sub A1 — `harvest_pattern` + `harvested_part` für alle Nutzarten
- **Umzusetzen:**
  - Alle Nutz-/Ernte-Arten (Gemüse, Kräuter, Obst) mit `harvest_pattern` (single/continuous/perennial)
    und `harvested_part` (fruit/leaf/root/…) belegen; reine Zierpflanzen bleiben leer (kein Erntebezug).
  - Beide Felder je Art gemeinsam recherchieren (ein Steckbrief-Durchgang).
- **Akzeptanzkriterien:** `harvest_pattern`- und `harvested_part`-Abdeckung für **alle Nutzarten**
  (Ziel ≥ 90 % der als `outdoor_vegetable`/`herb`/Obst kategorisierten Arten); `seed-data-validator` grün;
  Loader lädt ohne Enum-Fehler.
- **Spezialist:** Seed-Pipeline-Agenten. **Aufwand:** L. **Abhängigkeiten:** keine.

#### Sub A2 — `flowering_strategy` (monokarpe Arten)
- **Umzusetzen:**
  - Monokarpe Arten explizit als `monocarpic` markieren (Agave, Bambus-Arten, Bromelien/Aechmea u. a.);
    langlebige Perennials auf `polycarpic` setzen, wo relevant.
  - Fokus liegt auf der **korrekten Identifikation der monokarpen Arten** (fachliches Risiko), nicht auf
    flächiger Befüllung aller ~196 Arten.
- **Akzeptanzkriterien:** `flowering_strategy=monocarpic` für **≥ 8** eindeutig monokarpe Arten befüllt
  (Agave, ≥ 2 Bambus, ≥ 2 Bromelien) + `seed-data-validator` grün; keine polycarpe Art fälschlich als
  monocarpic markiert (Stichprobe im Validator-Report).
- **Spezialist:** Seed-Pipeline-Agenten + `agrobiology-requirements-reviewer` (Plausibilität).
  **Aufwand:** M. **Abhängigkeiten:** keine.

#### Sub A3 — `cultivation_cycle_type` (frostempfindliche Dauerkulturen)
- **Umzusetzen:**
  - Feld erstmals in `plant_info*.yaml` materialisieren (Zähler aktuell 0).
  - Frostempfindliche Dauerkulturen, die botanisch perennierend, im Freiland aber einjährig gezogen werden
    (Tomate, Paprika, Chili, Basilikum, Aubergine u. a.), mit dem passenden `cultivation_cycle_type`
    belegen (Abgrenzung botanischer `cycle_type` vs. Kultur-Zyklus, vgl. lifecycle-Override-Architektur).
- **Akzeptanzkriterien:** `cultivation_cycle_type` für **≥ 10** frostempfindliche Dauerkulturen befüllt +
  `seed-data-validator` grün + `growing-phase-auditor` meldet keine `cycle_type`↔`cultivation_cycle_type`-
  Inkonsistenz.
- **Spezialist:** Seed-Pipeline-Agenten + `growing-phase-auditor`. **Aufwand:** M.
  **Abhängigkeiten:** keine (unabhängig von A2, da anderes Feld).

#### Sub A4 — `growth_habit`-Reklassifizierung
- **Umzusetzen:**
  - Arten, die pauschal als `herb`/`shrub` klassifiziert sind, aber einer spezifischeren Kategorie
    angehören, reklassifizieren: Kakteen/Sukkulenten → `succulent`, Zwiebel-/Knollenpflanzen →
    `bulb_geophyte`, Farne → `fern`, Wasserpflanzen → `aquatic`, Epiphyten → `epiphyte`.
  - Bestehende 143 belegte Werte auf Qualität prüfen; die ~53 leeren Arten mit `growth_habit` ergänzen.
- **Akzeptanzkriterien:** Keine Sukkulente/Kaktee/Zwiebel/Farn/Wasserpflanze mehr fälschlich als
  `herb`/`shrub`; `growth_habit`-Abdeckung ≥ 90 % (~176/196); `seed-data-validator` grün.
- **Spezialist:** Seed-Pipeline-Agenten + `agrobiology-requirements-reviewer`. **Aufwand:** M-L.
  **Abhängigkeiten:** keine.

### WP-7-Rest — Toxizitäts-Badge im Frontend rendern

**Problem.** `Species.toxicity` (strukturierte `Toxicity`, `domain/models/species.py:265-273`) trägt
Mensch/Tier-relevante Sicherheitsdaten, wird aber im Frontend **gar nicht** angezeigt. `types.ts` kennt
nur das flache `toxicity_warning`. Das ist der einzige echte Code-Gap mit direkter Nutzerwirkung.

**Umzusetzen.**
- `Toxicity`-Typ in `src/frontend/src/api/types.ts` ergänzen (Felder gemäß Backend `Toxicity`-Modell:
  `severity`, betroffene Spezies/Symptome etc.) und in `Species`-Typ referenzieren.
- Neue Komponente `ToxicityBadge` (z. B. unter `components/common/` oder `pages/stammdaten/species-detail/`)
  und in `SpeciesDetailPage.tsx` / `SpeciesCultivationPanel.tsx` einbinden.
- **Sonderregel Sichtbarkeit:** Badge **immer** rendern — über `ExpertiseFieldWrapper`/`fieldConfigs`-Gating
  hinweg (schützt Mensch/Tier, nicht die Pflanze). Also **nicht** in `fieldConfigs.ts` als
  stufengegatetes Feld führen, sondern hart sichtbar (analog einer `alwaysVisible`-Ausnahme).
- i18n de/en für Badge-Label, Severity-Stufen und Tooltip
  (`i18n/locales/{de,en}/translation.json`, Namensraum `enums.*` bzw. `pages.stammdaten.*`).
- Vitest: Badge ist auch bei `experience_level='beginner'` sichtbar, wenn `species.toxicity` gesetzt ist;
  Badge fehlt, wenn `toxicity` `null` ist.

**Betroffene Dateien.**
- `src/frontend/src/api/types.ts`
- `src/frontend/src/pages/stammdaten/SpeciesDetailPage.tsx` (+ `species-detail/SpeciesCultivationPanel.tsx`)
- neu: `ToxicityBadge.tsx` (+ Testdatei)
- `src/frontend/src/i18n/locales/{de,en}/translation.json`

**Akzeptanzkriterien.**
- `ToxicityBadge` erscheint auf der Species-Detailseite für eine Art mit gesetztem `toxicity`,
  **unabhängig** von der Erfahrungsstufe (Vitest bei `beginner` grün).
- i18n de/en vollständig (kein fehlender Key beim Rendern).
- `tsc` + ESLint + Vitest + Build grün; kein `useMemo`-Verstoß bei zurückgegebenen Objekten/Arrays.

**Spezialist:** `fullstack-developer` (FE) + nachgelagert `frontend-usability-optimizer`/UI-Review.
**Aufwand:** S-M. **Abhängigkeiten:** keine (unabhängig von WP-10 und Härtung).

### WP-Rest — optionale Härtung (gebündelt, niedrig)

**Problem.** Kein Nutzer-Blocker, aber Modell-/Prozess-Qualität. Gebündelt, damit der Backfill (WP-10)
davon profitiert, dass danach keine weitere Schemaänderung mehr kommt.

**Umzusetzen (Bullets).**
- **WP-6f `Cultivar.seed_type` → Enum:** neuer `SeedType(StrEnum)` in `common/enums.py`
  (`open_pollinated | f1_hybrid | f2 | landrace | clone`), `Cultivar.seed_type: str` (`species.py:81`)
  auf `SeedType | None` umstellen — **additiv/abwärtskompatibel** (Freitext-Bestand tolerieren oder
  einmalig mappen). 3-Wege-Sync mitziehen: `_defs.schema.yaml`, `types.ts`, i18n de/en, ggf. FE-Konstante.
- **WP-8 Feld-Provenienz:** feldweise Herkunft ergänzen — entweder `field_provenance: dict[str, DataOrigin]`
  oder gezielte `*_source`-Felder — zusätzlich zum bestehenden record-level `origin` (`species.py:107,390`).
  Additiv, optional; Consumer bleiben unberührt.
- **WP-9-Rest CI-Gates (optional):** Enum-Sync-Check `enums.py` ↔ `_defs.schema.yaml` (und idealerweise
  `types.ts`) als CI-Step/pre-commit; i18n-Completeness de ↔ en (vorhandener
  `i18n-completeness-checker`-Agent als Vorlage). Nur additiv, nicht als required-Gate erzwingen, solange
  Bestand nicht grün.
- **WP-9-Rest Spec-Bumps:** REQ-008/017/021 um die neuen Felder ergänzen (Versions-Bump + Changelog-Zeile
  + Feld-Tabelle), da sie diese noch nicht referenzieren.

**Betroffene Dateien.**
- `src/backend/app/common/enums.py`, `src/backend/app/domain/models/species.py`
- `src/backend/app/migrations/seed_data/schemas/_defs.schema.yaml`
- `src/frontend/src/api/types.ts`, `i18n/locales/{de,en}/translation.json`
- `.github/workflows/` (optionaler Sync-/i18n-Check), ggf. `.pre-commit-config.yaml`
- `spec/req/REQ-008*.md`, `spec/req/REQ-017*.md`, `spec/req/REQ-021*.md`

**Akzeptanzkriterien.**
- `SeedType`-Enum an allen 3 Sync-Stellen + i18n; Bestandsdaten laden weiterhin (kein Enum-Load-Crash).
- Provenienz-Feld additiv vorhanden, Default gesetzt, kein Consumer bricht (`pytest` grün).
- Optionaler Enum-Sync-Check schlägt bei absichtlicher Drift-Injektion an (Test/Demo im PR).
- REQ-008/017/021 nennen die neuen Felder + Changelog-Zeile.

**Spezialist:** `fullstack-developer` (BE) + `spec`-Skill für die REQ-Bumps.
**Aufwand:** M. **Abhängigkeiten:** keine harten; sollte **vor** großen WP-10-Batches landen, damit
`SeedType`-Umstellung nicht mitten in laufende Seed-Befüllung fällt.

### WP-Statuspflege — Ursprungsplan-Header aktualisieren

**Problem.** `.audits/datenmodell-pflanzeneigenschaften-plan.md` trägt `status: backlog` und liest sich als
komplett offen, obwohl Phase A+B via #192 erledigt sind.

**Umzusetzen.**
- Frontmatter `status: backlog` → `status: partially-implemented (Phase A+B via #192)`.
- WP-1/WP-3/WP-4/WP-5/WP-6a-e in den betreffenden Abschnitten als erledigt markieren (z. B. `[DONE #192]`),
  ohne inhaltliche Passagen zu löschen.
- **Datei NICHT löschen**, nur Status/Marker aktualisieren; Verweis auf diesen Umsetzungsplan als
  Fortsetzung ergänzen.

**Betroffene Dateien.** `.audits/datenmodell-pflanzeneigenschaften-plan.md`.

**Akzeptanzkriterien.** Header zeigt `partially-implemented (Phase A+B via #192)`; alle erledigten WP sind
sichtbar markiert; die Datei existiert weiterhin vollständig.

**Spezialist:** `fullstack-developer` (oder direkter Edit). **Aufwand:** S. **Abhängigkeiten:** keine.

## Parallelisierungs-Strategie

Das Schema ist stabil; alle Stränge sind additiv und unabhängig → drei parallele Spuren:

- **Spur FE:** WP-7-Badge (`fullstack-developer` FE, isolierter Frontend-Scope).
- **Spur BE:** optionale Härtung WP-6f/WP-8/WP-9-Rest (`fullstack-developer` BE + `spec`).
- **Spur Seed:** WP-10 A1-A4, je Zielfeld eine eigene parallele Pipeline
  (`plant-info-*` → `seed-data-validator` → Loader), da additiv-leer und feldweise disjunkt.

Regeln:
- Schreibende Seed-Agenten auf gemeinsamem Tree **sequenziell pro Datei** oder je Batch in eigener
  `isolation: worktree`, sonst git-stash-Recovery-Konflikte (Memory: parallele Agenten auf shared tree).
- Härtung-Spur (WP-6f `SeedType`) **vor** großen WP-10-Batches abschließen, damit die Seed-Befüllung nicht
  gegen ein wechselndes Enum läuft; A1-A4 selbst berühren `seed_type` nicht und sind davon entkoppelt.
- WP-Statuspflege kann jederzeit unabhängig laufen.

## Definition of Done

- **WP-10:** A1-A4 Akzeptanzkriterien erfüllt (`harvest_pattern`/`harvested_part` ≥ 90 % der Nutzarten;
  `flowering_strategy` ≥ 8 monokarpe Arten; `cultivation_cycle_type` ≥ 10 Dauerkulturen; `growth_habit`
  reklassifiziert, ≥ 90 % Abdeckung); `seed-data-validator` grün; Loader (`seed_plant_info*.py`) laden
  ohne Enum-/Schema-Fehler.
- **WP-7-Badge:** immer-sichtbarer `ToxicityBadge` auf Species-Detailseite; i18n de/en; Vitest grün;
  `tsc`/ESLint/Build grün; UI-Review durchlaufen.
- **Härtung:** `SeedType`-Enum an 3 Sync-Stellen + i18n; Provenienz-Feld additiv; optionale CI-Gates
  vorhanden (nicht-required, wenn Bestand nicht grün); REQ-008/017/021 gebumpt.
- **Statuspflege:** Ursprungsplan-Header + WP-Marker aktualisiert.
- **Global:** Backend `ruff` + `pytest` (Coverage-Gate); Frontend `tsc`/ESLint/Vitest/Build; Security-Scans;
  Claude-Code-Review. `static` ist der einzige required Check; Coverage-Fails sind bekanntes non-required
  Flake (Memory).

## Risiko-Hinweise

- **3-Wege-Enum-Sync ist manuell.** Kein OpenAPI-Codegen: jeder neue Enum-Wert (`SeedType`) muss in
  `enums.py`, `_defs.schema.yaml` **und** `types.ts` **plus** i18n de/en gepflegt werden. Drift bricht
  entweder Seed-Load (Backend) oder stille FE-Fehldarstellung. Das optionale CI-Gate (WP-9-Rest) mindert
  genau dieses Risiko — daher bevorzugt zusammen mit WP-6f einführen.
- **WP-10 ist recherche-gebunden und damit der Kostentreiber.** Der Aufwand steckt nicht im Code, sondern
  in der 3-Quellen-Recherche pro Art über ~196 Steckbriefe. Nach Zielfeld schneiden hält die Batches klein
  und parallel; nicht versuchen, alle Felder je Art in einem Durchgang zu erschlagen.
- **3-Quellen-Regel (`seed-data-validator`).** Neue Werte müssen belegbar sein; `plant-info-to-seed-yaml`
  **erfindet keine Werte** — fehlende Angaben bleiben als Kommentar markiert. Fachlich heikle Felder
  (`flowering_strategy` monokarp, `growth_habit`-Reklassifizierung, `cultivation_cycle_type`) zusätzlich
  durch `agrobiology-requirements-reviewer` bzw. `growing-phase-auditor` gegenprüfen, sonst botanische
  Fehlklassifikation.
- **Additiv-leer schützt Consumer.** Solange Backfill-Werte nur ergänzt (nie umbenannt/entfernt) werden,
  bricht kein Consumer — deshalb die feldweise Parallelität. Sobald WP-6f ein Enum verengt, gilt das nicht
  mehr für `seed_type`: Freitext-Bestand vor der Verengung mappen oder tolerant lesen.
