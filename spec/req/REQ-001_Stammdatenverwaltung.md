# Spezifikation: REQ-001 - Stammdatenverwaltung

```yaml
ID: REQ-001
Titel: Stammdatenverwaltung von Pflanzen-Entitätszyklen
Kategorie: Stammdaten
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 3.1 (Agrarbiologie-Review Korrekturen)
```

## 1. Business Case

**User Story:** "Als Systemadministrator möchte ich botanische Stammdaten und Lebenszyklus-Typen definieren, um automatisierte Pflegepläne basierend auf der Biologie der Pflanze zu generieren."

**Beschreibung:** 
Das System verwaltet die botanische Taxonomie und physiologische Charakteristika von Pflanzenarten als zentrale Wissensgrundlage. Es unterscheidet zwischen:
- **Einjährige (Annual):** Vollständiger Lebenszyklus in einer Vegetationsperiode, harter Abschluss nach Samenreife
- **Zweijährige (Biennial):** Vegetatives Wachstum im ersten Jahr, Blüte/Samenbildung im zweiten Jahr
- **Mehrjährige (Perennial):** Wiederkehrendes Wachstum über mehrere Jahre, mit Dormanz-/Winterruhe-Phasen

Zusätzlich erfasst das System:
- **Botanische Klassifikation** (Familie, Gattung, Art, Sorte)
- **Photoperiodismus** (Kurztagspflanze, Langtagspflanze, tagneutral)
- **Klimazone-Anforderungen** (Hardiness Zones nach USDA)
- **Wuchsform und Habitustypen** (Kraut, Strauch, Baum, Kletterpflanze)
- **Wurzelsystem-Typen** (Flachwurzler, Tiefwurzler, Pfahlwurzel)
- **Allelochemische Eigenschaften** (Allelopathie für Mischkultur-Planung)
<!-- Quelle: Outdoor-Garden-Planner Review G-001, G-006 -->
- **Freiland-Gartenplanung** (Aussaatkalender, Frostempfindlichkeit, Erntefenster)
- **Obstbau-Stammdaten** (Unterlage, Befruchtersorte, Alternanz, Standzeit)
- **Fruchtfolge-Attribute** (Nährstoffbedarf-Stufe, Gründüngungseignung)
<!-- /Quelle: G-001, G-006 -->

## 2. ArangoDB-Modellierung

### Nodes:
- **`:Species`** - Botanische Art
  - Properties: 
    - `scientific_name: str` (Binomiale Nomenklatur, z.B. "Solanum lycopersicum")
    - `common_names: list[str]` (Landessprachliche Namen)
    - `family: str` (Botanische Familie, z.B. "Solanaceae")
    - `genus: str`
    - `hardiness_zones: list[str]` (z.B. ["7a", "7b", "8a"])
    - `native_habitat: str`
    - `growth_habit: Literal['herb', 'shrub', 'tree', 'vine', 'groundcover']`
    - `root_type: Literal['fibrous', 'taproot', 'tuberous', 'bulbous', 'rhizomatous', 'aerial']` — `rhizomatous`: Rhizom-bildend (Calathea, Ingwer, Iris, viele Farne); `aerial`: Luftwurzeln/hemiepiphytisch (Monstera, Philodendron, Orchideen). Optional ergänzend: `root_adaptations: list[str]` für Arten mit Mehrfachzuweisung (z.B. Monstera hat Faserwurzeln UND Luftwurzeln).
    - `root_adaptations: list[str]` (z.B. `["aerial", "epiphytic", "stoloniferous"]` — ergänzende Wurzelanpassungen über den Primärtyp hinaus)
    - `allelopathy_score: float` (-1.0 = stark hemmend, 0 = neutral, 1.0 = fördernd) — generelle allelopathische Tendenz der Art. Hinweis: Allelopathische Wirkungen sind stark partnerabhängig (z.B. *Juglans nigra* hemmt *Solanum lycopersicum*, aber kaum *Phaseolus vulgaris*). Die paarspezifischen `compatible_with`/`incompatible_with`-Edges sind die autoritativen Daten; dieser Score dient nur als Erstindikator.
    - `toxicity: Optional[ToxicityInfo]` — Embedded-Objekt, siehe ToxicityInfo-Definition (U-001)
    - `air_purification_score: Optional[float]` (0.0–1.0; basiert auf NASA Clean Air Study / Wolverton 1989. 0.0 = keine nachgewiesene Wirkung, 1.0 = stark luftreinigend. Caveat: Bei realistischen Pflanzendichten in Wohnräumen vernachlässigbar — Cummings & Waring 2020.)
    - `removes_compounds: list[str]` (Schadstoffe die die Art nachweislich filtert, z.B. `["formaldehyde", "benzene", "trichloroethylene", "xylene", "toluene", "ammonia"]`)
    - `allergen_info: Optional[AllergenInfo]` — Embedded-Objekt mit Pollen-, Kontakt- und VOC-Allergenrisiko (siehe AllergenInfo-Definition)
    - `propagation_methods: list[str]` (Unterstützte Vermehrungsmethoden: `'seed'`, `'cutting_stem'`, `'cutting_leaf'`, `'division'`, `'offset'`, `'layering'`, `'grafting'`, `'spore'`)
    - `propagation_difficulty: Optional[Literal['easy', 'moderate', 'difficult']]` (Schwierigkeit für Einsteiger — wird im Beginner-Modus REQ-021 angezeigt)
    <!-- Quelle: Outdoor-Garden-Planner Review G-001, G-006 -->
    # Freiland-/Gartenplanung (Quelle: Outdoor-Garden-Planner Review G-001)
    - `frost_sensitivity: Optional[Literal['hardy', 'half_hardy', 'tender']]` (hardy = übersteht Frost, half_hardy = leichter Frost ok, tender = frostfrei halten)
    - `hardiness_detail: Optional[str]` (z.B. "Winterhart bis -15°C, Wurzelschutz empfohlen")
    - `sowing_indoor_weeks_before_last_frost: Optional[int]` (Voranzucht: Wochen vor letztem Frost, z.B. 8 für Tomaten)
    - `sowing_outdoor_after_last_frost_days: Optional[int]` (Direktsaat: Tage nach letztem Frost, z.B. 0 für Erbsen, 14 für Bohnen)
    - `direct_sow_months: Optional[list[int]]` (Monate für Direktsaat, z.B. [3,4,5] für Möhren)
    - `harvest_months: Optional[list[int]]` (Erntemonate, z.B. [7,8,9] für Tomaten)
    - `nutrient_demand_level: Optional[Literal['heavy_feeder', 'medium_feeder', 'light_feeder', 'nitrogen_fixer']]` (Starkzehrer/Mittelzehrer/Schwachzehrer/Stickstoff-Fixierer für Fruchtfolge-Planung)
    - `green_manure_suitable: bool = False` (Eignung als Gründüngung — z.B. Phacelia, Senf, Lupine)
    - `pruning_months: Optional[list[int]]` (Empfohlene Schnittmonate, z.B. [2,3] für Kernobst)
    - `pruning_type: Optional[Literal['winter_pruning', 'summer_pruning', 'after_harvest', 'spring_pruning', 'none']]`
    - `bloom_months: Optional[list[int]]` (Blütemonate — für Blühkalender und Bestäuber-Planung)
    <!-- /Quelle: G-001, G-006 -->
    <!-- Quelle: Agrarbiologie-Review AB-004, 2026-03 -->
    - `traits: Optional[list[str]]` (Tags auf Species-Ebene, z.B. `['ornamental']`. Analog zu Cultivar.traits, aber für art-übergreifende Eigenschaften. Gültige Werte: `'ornamental'`, `'edible'`, `'medicinal'`, `'fragrant'`, `'bee_friendly'`, `'native'`. Validierung identisch zu Cultivar.traits-Validator.)

- **`:Cultivar`** - Sorte/Zuchtform
  - Properties:
    - `name: str` (z.B. "San Marzano")
    - `breeder: str`
    - `breeding_year: int`
    - `traits: list[str]` (z.B. ["disease_resistant", "high_yield", "compact"])
    - `patent_status: str`
    <!-- Quelle: Cannabis Indoor Grower Review G-009 -->
    - `photoperiod_type: Optional[Literal['photoperiodic', 'autoflower', 'day_neutral']]` — Lichtreaktion auf Cultivar-Ebene (überschreibt Species-Level `PhotoperiodType` wenn gesetzt):
      - `photoperiodic`: Blüte wird durch Lichtperiodenwechsel ausgelöst (z.B. 12/12 bei Cannabis). Standard für die meisten Cannabis-Sorten.
      - `autoflower`: Blüte nach Alter (unabhängig von Lichtperiode), typisch bei Cannabis-ruderalis-Hybriden. Durchgehend 20/4 oder 18/6 Licht, kürzerer Gesamtzyklus (60–90 Tage), keine Topping-Empfehlung.
      - `day_neutral`: Tagneutrale Pflanzen (z.B. bestimmte Erdbeersorten, immertragende Sorten). Blüte unabhängig von Tageslänge.
    - `autoflower_days_to_flower: Optional[int]` — Nur bei `photoperiod_type='autoflower'`: Tage nach Keimung bis zum automatischen Blüte-Eintritt (typisch 21–30 Tage)
    - `autoflower_total_cycle_days: Optional[int]` — Nur bei `photoperiod_type='autoflower'`: Erwartete Gesamtdauer Keimung bis Ernte (typisch 60–90 Tage)
    <!-- /Quelle: G-009 -->
    <!-- Quelle: Outdoor-Garden-Planner Review G-001, G-006 -->
    # Obstbau & Dauerkulturen (Quelle: Outdoor-Garden-Planner Review G-006)
    - `rootstock: Optional[str]` (Unterlage bei Obstbäumen, z.B. "M9" für Zwergwuchs, "M26" für Halbstamm)
    - `requires_pollinator: Optional[bool]` (Benötigt Befruchtersorte — z.B. true für die meisten Apfelsorten)
    - `pollinator_group: Optional[str]` (Befruchtungsgruppe, z.B. "3" — kompatible Gruppen: n-1, n, n+1)
    - `compatible_pollinators: Optional[list[str]]` (Empfohlene Befruchtersorten, z.B. ["Goldparmäne", "James Grieve"])
    - `years_to_first_harvest: Optional[int]` (Jahre bis Erstertrag, z.B. 3-5 bei Apfel auf M9)
    - `biennial_bearing: Optional[bool]` (Alternanz — Tendenz zu Ertragsschwankungen jedes 2. Jahr)
    - `berry_type: Optional[Literal['summer_bearing', 'autumn_bearing', 'everbearing']]` (Himbeeren: Sommer- vs. Herbsthimbeere — unterschiedliche Schnittregeln!)
    - `max_stand_years: Optional[int]` (Maximale Standzeit, z.B. 3-4 für Erdbeeren, dann neu pflanzen)
    - `seed_type: Optional[Literal['open_pollinated', 'f1_hybrid', 'f2', 'landrace', 'clone']]` (samenfest vs. F1-Hybrid — relevant für eigene Saatgutgewinnung)
    <!-- /Quelle: G-001, G-006 -->

- **`:LifecycleConfig`** - Lebenszyklus-Konfiguration
  - Properties:
    - `cycle_type: Literal['annual', 'biennial', 'perennial']`
    - `typical_lifespan_years: Optional[int]`
    - `dormancy_required: bool`
    - `vernalization_required: bool` (Kälteperiode für Blüteninduktion)
    - `vernalization_min_days: Optional[int]`
    - `photoperiod_type: Literal['short_day', 'long_day', 'day_neutral']`
    - `critical_day_length_hours: Optional[float]`

- **`:GrowthPhase`** - Wachstumsphase
  - Properties:
    - `name: str` (z.B. "Keimung", "Vegetatives Wachstum", "Blüte", "Fruchtbildung")
    - `typical_duration_days: int`
    - `temperature_optimum_c: float`
    - `temperature_tolerance_range: tuple[float, float]`
    - `light_requirements_ppfd: int` (Photosynthetic Photon Flux Density)
    - `critical_for_yield: bool`

- **`:BotanicalFamily`** - Pflanzenfamilie
  - Properties:
    - `name: str` (z.B. "Brassicaceae", "Fabaceae") — muss auf "-aceae" enden
    - `common_name_de: str` (Deutscher Anzeigename, z.B. "Nachtschattengewächse")
    - `common_name_en: str` (Englischer Anzeigename, z.B. "Nightshade family")
    - `order: Optional[str]` (Taxonomische Ordnung, z.B. "Solanales") — muss auf "-ales" enden, wenn angegeben
    - `description: str` (Botanische Kurzbeschreibung)
    - `typical_nutrient_demand: Literal['light', 'medium', 'heavy']`
    - `nitrogen_fixing: bool` (default: false) — Stickstofffixierung (z.B. Fabaceae=true). Validierung: `nitrogen_fixing=true` + `typical_nutrient_demand='heavy'` ist ungültig (N-Fixierer sind Schwach-/Mittelzehrer)
    - `typical_root_depth: RootDepth` (Enum: SHALLOW / MEDIUM / DEEP)
    - `soil_ph_preference: Optional[PhRange]` (Embedded: min_ph, max_ph)
    - `frost_tolerance: FrostTolerance` (Enum: SENSITIVE / MODERATE / HARDY / VERY_HARDY)
    - `typical_growth_forms: list[GrowthHabit]` (Reuse bestehendes Enum)
    - `common_pests: list[str]`
    - `common_diseases: list[str]` (Pilz-/Bakterienkrankheiten, z.B. ["Mehltau", "Kraut- und Braunfäule"])
    - `pollination_type: list[PollinationType]` (Enum: INSECT / WIND / SELF)
    - `rotation_category: str` (Für Fruchtfolge)

### Edges (ArangoDB Edge Collections):

**Spezies-Kanten:**
- **`belongs_to_family`**: `Species → BotanicalFamily`
- **`has_cultivar`**: `Species → Cultivar`
- **`has_lifecycle`**: `Species → LifecycleConfig`
  - Properties: (keine)
- **`consists_of`**: `LifecycleConfig → GrowthPhase`
  - Properties: `sequence: int`
- **`compatible_with`**: `Species → Species` (Mischkultur)
  - Properties: `compatibility_score: float` (0.0–1.0)
- **`incompatible_with`**: `Species → Species` (Allelopathie)
  - Properties: `reason: str`

**Familien-Kanten:**
- **`rotation_after`**: `BotanicalFamily → BotanicalFamily` (gerichtet)
  - Richtung: `(A)-[:rotation_after]->(B)` = "A ist guter Nachfolger NACH B"
  - Properties:
    - `benefit_score: float` (0.0–1.0)
    - `benefit_reason: str` (z.B. "nitrogen_fixation", "soil_structure", "biofumigation", "pest_break")
- **`shares_pest_risk`**: `BotanicalFamily ↔ BotanicalFamily` (bidirektional)
  - Properties:
    - `shared_pests: list[str]` (gemeinsame Schädlinge)
    - `shared_diseases: list[str]` (gemeinsame Krankheiten)
    - `risk_level: Literal['low', 'medium', 'high']`
- **`family_compatible_with`**: `BotanicalFamily ↔ BotanicalFamily` (bidirektional)
  - Properties:
    - `benefit_type: str` (z.B. "nitrogen_fixation", "pest_deterrent", "pollinator_attraction")
    - `compatibility_score: float` (0.0–1.0)
    - `notes: str`
- **`family_incompatible_with`**: `BotanicalFamily ↔ BotanicalFamily` (bidirektional)
  - Properties:
    - `reason: str`
    - `severity: Literal['mild', 'moderate', 'severe']`

### AQL-Beispielqueries (ArangoDB 3.11+):

**1. Familie mit allen Beziehungen laden (Graph-Traversal):**
```aql
LET family = DOCUMENT("botanical_families", @family_key)

LET rotation_targets = (
    FOR v, e IN 1..1 OUTBOUND family rotation_after
    RETURN { family: v.name, benefit_score: e.benefit_score, benefit_reason: e.benefit_reason }
)

LET pest_risks = (
    FOR v, e IN 1..1 ANY family shares_pest_risk
    RETURN { family: v.name, shared_pests: e.shared_pests, shared_diseases: e.shared_diseases, risk_level: e.risk_level }
)

LET compatible = (
    FOR v, e IN 1..1 ANY family family_compatible_with
    RETURN { family: v.name, benefit_type: e.benefit_type, score: e.compatibility_score }
)

LET incompatible = (
    FOR v, e IN 1..1 ANY family family_incompatible_with
    RETURN { family: v.name, reason: e.reason, severity: e.severity }
)

RETURN MERGE(family, {
    rotation_targets,
    pest_risks,
    compatible_families: compatible,
    incompatible_families: incompatible
})
```

**2. Erweiterte Fruchtfolge-Validierung (mit Pest-Risiko):**

Hinweis: Fruchtfolge-Warnungen werden nur bei Outdoor-/Boden-basierten Standorten erzeugt. Bei Indoor-Hydroponik (Substrattyp `none`, `clay_pebbles`, `rockwool_slab`) und Zimmerpflanzen ist Fruchtfolge nicht anwendbar — das Substrat wird zwischen Zyklen gewechselt oder sterilisiert (siehe REQ-019). Die Validierung wird übersprungen wenn `site.type == 'indoor'` UND `substrate.type NOT IN ['soil', 'living_soil', 'coco']`.

```aql
// Guard: Fruchtfolge nur für bodenbasierte Standorte relevant
LET slot_substrate = FIRST(
    FOR sub IN 1..1 OUTBOUND DOCUMENT('slots', @slot_key) GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['filled_with'] }
        RETURN sub.type
)
LET slot_site = FIRST(
    FOR site IN sites FILTER site._key == @site_key RETURN site
)

// Überspringe Validierung bei Indoor-Hydroponik und Zimmerpflanzen
FILTER slot_site.type IN ['outdoor', 'greenhouse']
    OR slot_substrate IN ['soil', 'living_soil', 'coco']

LET current_species = FIRST(FOR s IN species FILTER s.scientific_name == @planned_species RETURN s)
LET previous_species = FIRST(FOR s IN species FILTER s.scientific_name == @last_species RETURN s)

LET f1 = FIRST(FOR v IN 1..1 OUTBOUND current_species belongs_to_family RETURN v)
LET f2 = FIRST(FOR v IN 1..1 OUTBOUND previous_species belongs_to_family RETURN v)

LET same_family = f1._id == f2._id

LET rotation_edge = FIRST(
    FOR v, e IN 1..1 OUTBOUND f2 rotation_after
    FILTER v._id == f1._id
    RETURN e
)

LET pest_risk = FIRST(
    FOR v, e IN 1..1 ANY f1 shares_pest_risk
    FILTER v._id == f2._id
    RETURN e
)

RETURN {
    status: same_family ? "CRITICAL" : (pest_risk.risk_level == "high" ? "WARNING" : (rotation_edge ? "OK" : "INFO")),
    message: same_family
        ? CONCAT("Gleiche Familie (", f1.name, ") — Mindestabstand 3 Jahre")
        : (pest_risk != null
            ? CONCAT("Gemeinsames Schädlingsrisiko: ", pest_risk.shared_pests, " (", pest_risk.risk_level, ")")
            : (rotation_edge != null
                ? CONCAT("Gute Nachfolge: ", rotation_edge.benefit_reason, " (Score: ", rotation_edge.benefit_score, ")")
                : "Keine spezifische Empfehlung")),
    nitrogen_benefit: f1.nitrogen_fixing ? "Stickstofffixierung: N-Düngung kann reduziert werden" : null,
    pest_risk: pest_risk,
    rotation_benefit: rotation_edge
}
```

**3. Familien-Level Mischkultur-Fallback:**
```aql
// Wenn keine Spezies-Level compatible_with-Kante existiert,
// Fallback auf Familien-Level family_compatible_with
LET species = DOCUMENT("species", @species_key)
LET family = FIRST(FOR v IN 1..1 OUTBOUND species belongs_to_family RETURN v)

// Spezies-Level Matches
LET species_matches = (
    FOR v, e IN 1..1 OUTBOUND species compatible_with
    RETURN { species: v.scientific_name, score: e.compatibility_score, level: "species" }
)

// Familien-Level Fallback (nur wenn Spezies-Level leer)
LET family_matches = LENGTH(species_matches) == 0 ? (
    FOR fam, e IN 1..1 ANY family family_compatible_with
    FOR s IN 1..1 INBOUND fam belongs_to_family
    RETURN DISTINCT {
        species: s.scientific_name,
        score: e.compatibility_score * 0.8,  // 20% Abschlag für Familien-Level
        level: "family",
        benefit_type: e.benefit_type
    }
) : []

RETURN {
    matches: LENGTH(species_matches) > 0 ? species_matches : family_matches,
    match_level: LENGTH(species_matches) > 0 ? "species" : "family"
}
```

**4. Optimale Rotationssequenz-Empfehlung (3-Jahres-Plan):**
```aql
// Erstellt einen optimalen 3-Jahres-Rotationsplan basierend auf der aktuellen Familie
LET current_family = DOCUMENT("botanical_families", @current_family_key)

LET year1_options = (
    FOR v, e IN 1..1 OUTBOUND current_family rotation_after
    SORT e.benefit_score DESC
    RETURN { family: v, score: e.benefit_score, reason: e.benefit_reason }
)

LET best_year1 = FIRST(year1_options)

LET year2_options = best_year1 != null ? (
    FOR v, e IN 1..1 OUTBOUND best_year1.family rotation_after
    FILTER v._id != current_family._id  // Nicht zurück zur Ausgangsfamilie
    SORT e.benefit_score DESC
    RETURN { family: v, score: e.benefit_score, reason: e.benefit_reason }
) : []

RETURN {
    current: { name: current_family.name, common_name_de: current_family.common_name_de },
    year1: best_year1 != null ? { name: best_year1.family.name, common_name_de: best_year1.family.common_name_de, score: best_year1.score, reason: best_year1.reason } : null,
    year2: LENGTH(year2_options) > 0 ? { name: FIRST(year2_options).family.name, common_name_de: FIRST(year2_options).family.common_name_de, score: FIRST(year2_options).score, reason: FIRST(year2_options).reason } : null,
    alternatives_year1: SLICE(year1_options, 1, 3)
}

### Seed-Daten: BotanicalFamily

Die folgenden 9 Pflanzenfamilien bilden die initiale Datenbasis:

| name | common_name_de | common_name_en | order | typical_nutrient_demand | nitrogen_fixing | typical_root_depth | frost_tolerance | pollination_type |
|------|---------------|---------------|-------|------------------------|----------------|-------------------|----------------|-----------------|
| Solanaceae | Nachtschattengewächse | Nightshade family | Solanales | heavy | false | MEDIUM | SENSITIVE | INSECT, SELF |
| Brassicaceae | Kreuzblütler | Mustard family | Brassicales | heavy | false | MEDIUM | HARDY | INSECT |
| Fabaceae | Hülsenfrüchtler | Legume family | Fabales | light | true | DEEP | MODERATE | INSECT, SELF |
| Cucurbitaceae | Kürbisgewächse | Gourd family | Cucurbitales | heavy | false | SHALLOW | SENSITIVE | INSECT |
| Apiaceae | Doldenblütler | Carrot family | Apiales | medium | false | DEEP | HARDY | INSECT |
| Asteraceae | Korbblütler | Daisy family | Asterales | medium | false | MEDIUM | MODERATE | INSECT, WIND |
| Poaceae | Süßgräser | Grass family | Poales | medium | false | SHALLOW | VERY_HARDY | WIND, SELF |
| Lamiaceae | Lippenblütler | Mint family | Lamiales | light | false | SHALLOW | MODERATE | INSECT |
| Cannabaceae | Hanfgewächse | Hemp family | Rosales | heavy | false | DEEP | SENSITIVE | WIND |
| Violaceae | Veilchengewächse | Violet family | Malpighiales | light | false | SHALLOW | HARDY | INSECT, SELF |

<!-- Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->
### Seed-Daten: Zierpflanzen-Species

Die folgenden Zierpflanzen-Species erweitern die initiale Datenbasis um gängige Balkon- und Beetpflanzen:

| scientific_name | common_names (DE) | family | growth_habit | root_type | frost_sensitivity | cycle_type | sowing_indoor_weeks_before_last_frost | bloom_months | nutrient_demand_level | traits |
|----------------|-------------------|--------|-------------|-----------|-------------------|-----------|--------------------------------------|-------------|----------------------|--------|
| *Viola x wittrockiana* | Stiefmütterchen, Gartenstiefmütterchen | Violaceae | herb | fibrous | hardy | annual | 12 | [3, 4, 5, 6, 9, 10] | light_feeder | ornamental |
| *Viola cornuta* | Hornveilchen | Violaceae | herb | fibrous | hardy | perennial | 12 | [3, 4, 5, 6, 7, 8, 9, 10] | light_feeder | ornamental |
| *Petunia x hybrida* | Petunie | Solanaceae | herb | fibrous | tender | annual | 10 | [5, 6, 7, 8, 9, 10] | medium_feeder | ornamental |
| *Pelargonium zonale* | Geranie, Stehende Geranie | Geraniaceae | herb | fibrous | tender | perennial | 12 | [5, 6, 7, 8, 9, 10] | medium_feeder | ornamental |
| *Tagetes patula* | Studentenblume, Tagetes | Asteraceae | herb | fibrous | tender | annual | 6 | [6, 7, 8, 9, 10] | light_feeder | ornamental |
| *Lobelia erinus* | Männertreu, Blaue Lobelie | Campanulaceae | herb | fibrous | tender | annual | 10 | [5, 6, 7, 8, 9] | light_feeder | ornamental |
| *Osteospermum ecklonis* | Kapkörbchen, Kapmargerite | Asteraceae | herb | fibrous | half_hardy | perennial | 8 | [5, 6, 7, 8, 9, 10] | medium_feeder | ornamental |
| *Impatiens walleriana* | Fleißiges Lieschen | Balsaminaceae | herb | fibrous | tender | annual | 10 | [5, 6, 7, 8, 9, 10] | light_feeder | ornamental |
| *Calibrachoa × hybrida* | Zauberglöckchen, Calibrachoa | Solanaceae | herb | fibrous | tender | annual | 10 | [5, 6, 7, 8, 9, 10] | heavy_feeder | ornamental |
| *Primula vulgaris* | Primel, Kissenprimel | Primulaceae | herb | fibrous | hardy | perennial | 10 | [2, 3, 4, 5] | light_feeder | ornamental |

<!-- Quelle: Agrarbiologie-Review AB-011, AB-012, AB-013, 2026-03 -->
**Korrekturen gegenüber v3.0:**
- **AB-001:** *Calibrachoa* → *Calibrachoa × hybrida* (Hybridzeichen nach APG IV Binomialnomenklatur)
- **AB-011:** *Lobelia erinus* `frost_sensitivity` von `half_hardy` → `tender` (Sämlinge sind frostempfindlich; Auspflanzen erst nach Eisheiligen)
- **AB-012:** *Viola x wittrockiana* + *Viola cornuta* `sowing_indoor_weeks_before_last_frost` von `8` → `12` (8 Wochen ergibt zu kleine Pflanzen; kommerzieller Standard: 12–16 Wochen)
- **AB-004:** `traits`-Spalte ergänzt — alle Zierpflanzen-Species erhalten `ornamental` (lowercase, konsistent mit Cultivar.validate_traits)

**Ergänzende Direktsaat-Daten (AB-013):**
- *Tagetes patula*: `direct_sow_months: [5, 6]` — Direktsaat nach Eisheiligen möglich, Blüte ca. 2–3 Wochen später als bei Voranzucht

**Artspezifische Keimtemperaturen (AB-007):**

| Species | Keimtemperatur optimal (°C) | Keimtemperatur min (°C) | Besonderheit |
|---------|----------------------------|------------------------|-------------|
| *Viola x wittrockiana* | 15–18 | 10 | Thermoinhibition ab 22°C — NICHT auf Heizmatte! Lichtkeimer. |
| *Viola cornuta* | 15–18 | 10 | Wie Viola x wittrockiana |
| *Petunia x hybrida* | 22–25 | 18 | Bodenwärme empfohlen (Heizmatte). Lichtkeimer. |
| *Tagetes patula* | 20–25 | 15 | Schnelle Keimung (3–5 Tage). Dunkelkeimer. |
| *Lobelia erinus* | 20–22 | 16 | Lichtkeimer — Samen nur andrücken, nicht bedecken. Keimdauer 14–21 Tage. |
| *Impatiens walleriana* | 22–25 | 18 | Lichtkeimer. Keimdauer 10–14 Tage. |
| *Calibrachoa × hybrida* | 22–25 | 18 | Lichtkeimer. Professionelle Anzucht empfohlen. |
| *Primula vulgaris* | 12–15 | 5 | Kaltkeimer — 2–4 Wochen Stratifikation bei 0–5°C förderlich. Lichtkeimer. |

Zusätzliche BotanicalFamily-Einträge für Zierpflanzen (sofern nicht bereits vorhanden):

| name | common_name_de | common_name_en | order | typical_nutrient_demand | nitrogen_fixing | typical_root_depth | frost_tolerance | pollination_type |
|------|---------------|---------------|-------|------------------------|----------------|-------------------|----------------|-----------------|
| Geraniaceae | Storchschnabelgewächse | Geranium family | Geraniales | medium | false | SHALLOW | SENSITIVE | INSECT |
| Campanulaceae | Glockenblumengewächse | Bellflower family | Asterales | light | false | SHALLOW | MODERATE | INSECT |
| Balsaminaceae | Balsaminengewächse | Balsam family | Ericales | light | false | SHALLOW | SENSITIVE | INSECT |
| Primulaceae | Primelgewächse | Primrose family | Ericales | light | false | SHALLOW | HARDY | INSECT, SELF |

<!-- Quelle: Agrarbiologie-Review AB-002, 2026-03 -->
> **Taxonomie-Hinweis (APG IV):** *Primulaceae* und *Balsaminaceae* gehören seit APG III (2009) zur Ordnung **Ericales** (nicht zur historischen Ordnung Primulales bzw. einer eigenen Ordnung). Dies ist korrekt nach aktuellem molekulargenetischem Stand.

<!-- Quelle: Agrarbiologie-Review AB-015, 2026-03 -->
**Toxizitätsdaten: Zierpflanzen-Species**

| Species | is_toxic_cats | is_toxic_dogs | is_toxic_children | toxic_compounds | toxic_parts | severity | source |
|---------|:---:|:---:|:---:|---------|---------|----------|--------|
| *Viola x wittrockiana* | false | false | false | – | – | none | ASPCA |
| *Viola cornuta* | false | false | false | – | – | none | ASPCA |
| *Petunia x hybrida* | false | false | false | – | – | none | ASPCA |
| *Pelargonium zonale* | true | true | false | geraniol, linalool | leaves, stems | mild | ASPCA |
| *Tagetes patula* | true | true | false | thiophene_derivatives | leaves, flowers | mild | ASPCA |
| *Lobelia erinus* | true | true | true | lobeline (alkaloid) | all, especially seeds | moderate | Giftnotruf Bonn |
| *Osteospermum ecklonis* | false | false | false | – | – | none | ASPCA |
| *Impatiens walleriana* | false | false | false | saponins (trace) | all | none | ASPCA |
| *Calibrachoa × hybrida* | false | false | false | – | – | none | ASPCA |
| *Primula vulgaris* | false | true | false | primin (contact dermatitis) | leaves, stems | mild | ASPCA |
<!-- /Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->

**Seed-Daten: rotation_after-Kanten (~16 gerichtete Kanten):**

| Von (Nachfolger) | Nach (Vorgänger) | benefit_score | benefit_reason |
|-------------------|-------------------|--------------|----------------|
| Fabaceae | Solanaceae | 0.95 | nitrogen_fixation |
| Fabaceae | Brassicaceae | 0.90 | nitrogen_fixation |
| Fabaceae | Cucurbitaceae | 0.90 | nitrogen_fixation |
| Fabaceae | Cannabaceae | 0.90 | nitrogen_fixation |
| Brassicaceae | Fabaceae | 0.85 | soil_structure |
| Apiaceae | Brassicaceae | 0.80 | pest_break |
| Solanaceae | Fabaceae | 0.85 | nitrogen_fixation |
| Cucurbitaceae | Fabaceae | 0.85 | nitrogen_fixation |
| Cannabaceae | Fabaceae | 0.85 | nitrogen_fixation |
| Asteraceae | Solanaceae | 0.75 | pest_break |
| Lamiaceae | Solanaceae | 0.70 | pest_break |
| Poaceae | Brassicaceae | 0.80 | soil_structure |
| Brassicaceae | Poaceae | 0.75 | biofumigation |
| Apiaceae | Cucurbitaceae | 0.70 | pest_break |
| Cucurbitaceae | Poaceae | 0.75 | soil_structure |
| Asteraceae | Cucurbitaceae | 0.70 | pest_break |

**Seed-Daten: shares_pest_risk-Kanten (~7 bidirektionale Paare):**

| Familie A | Familie B | shared_pests | shared_diseases | risk_level |
|-----------|-----------|-------------|-----------------|------------|
| Solanaceae | Cucurbitaceae | Blattläuse, Weiße Fliege | – | medium |
| Solanaceae | Solanaceae | Kartoffelkäfer, Blattläuse | Kraut- und Braunfäule, Fusarium | high |
| Brassicaceae | Brassicaceae | Kohlweißling, Erdflöhe | Kohlhernie, Mehltau | high |
| Cucurbitaceae | Cucurbitaceae | Spinnmilben, Blattläuse | Mehltau, Falscher Mehltau | high |
| Brassicaceae | Apiaceae | Blattläuse | Mehltau | low |
| Cannabaceae | Cannabaceae | Spinnmilben, Thripse, Trauermücken | Botrytis, Mehltau, Fusarium | high |
| Cannabaceae | Cucurbitaceae | Spinnmilben, Blattläuse | Mehltau | medium |

**Seed-Daten: family_compatible_with-Kanten (~8 bidirektionale Paare):**

| Familie A | Familie B | benefit_type | compatibility_score | notes |
|-----------|-----------|-------------|--------------------|----|
| Fabaceae | Solanaceae | nitrogen_fixation | 0.85 | N-Fixierung verbessert Starkzehrer-Versorgung |
| Fabaceae | Brassicaceae | nitrogen_fixation | 0.80 | N-Fixierung nach Starkzehrer |
| Fabaceae | Cannabaceae | nitrogen_fixation | 0.85 | N-Fixierung verbessert Starkzehrer-Versorgung |
| Lamiaceae | Solanaceae | pest_deterrent | 0.75 | Ätherische Öle wirken abschreckend |
| Lamiaceae | Brassicaceae | pest_deterrent | 0.70 | Basilikum/Minze gegen Kohlweißling |
| Lamiaceae | Cannabaceae | pest_deterrent | 0.70 | Ätherische Öle gegen Spinnmilben und Thripse |
| Asteraceae | Cucurbitaceae | pollinator_attraction | 0.65 | Blüten locken Bestäuber an |
| Apiaceae | Asteraceae | pollinator_attraction | 0.60 | Komplementäre Blütenbesucher |

**Seed-Daten: family_incompatible_with-Kanten (~3 bidirektionale Paare):**

| Familie A | Familie B | reason | severity |
|-----------|-----------|--------|----------|
| Solanaceae | Solanaceae | Selbstinkompatibilität: gemeinsame Krankheiten und Schädlinge | severe |
| Brassicaceae | Brassicaceae | Kohlhernie-Risiko bei wiederholtem Anbau | severe |
| Cucurbitaceae | Cucurbitaceae | Fusarium-Akkumulation im Boden | moderate |

### Seed-Daten: Species-Toxizität

Die folgenden Toxizitätsdaten werden als `ToxicityInfo`-Objekt im jeweiligen Species-Dokument gespeichert. Primärquellen: ASPCA Animal Poison Control (aspca.org), Giftinformationszentrale Bonn (gizbonn.de).

**Zimmerpflanzen (aus Starter-Kit `zimmerpflanzen` und `zimmerpflanzen-haustierfreundlich`):**

| Species | is_toxic_cats | is_toxic_dogs | is_toxic_children | toxic_compounds | toxic_parts | severity | source |
|---------|:---:|:---:|:---:|---------|---------|----------|--------|
| *Monstera deliciosa* | true | true | true | calcium_oxalate_raphides | leaves, stems | moderate | ASPCA |
| *Ficus lyrata* | true | true | true | ficin, furocoumarins | leaves, stems, sap | moderate | ASPCA |
| *Epipremnum aureum* | true | true | true | calcium_oxalate_raphides | leaves, stems | moderate | ASPCA |
| *Dracaena trifasciata* | true | true | true | saponins | leaves | mild | ASPCA |
| *Chlorophytum comosum* | false | false | false | – | – | none | ASPCA |
| *Chamaedorea elegans* | false | false | false | – | – | none | ASPCA |
| *Pilea peperomioides* | false | false | false | – | – | none | ASPCA |
| *Maranta leuconeura* | false | false | false | – | – | none | ASPCA |

**Nutzpflanzen (aus Starter-Kits):**

| Species | is_toxic_cats | is_toxic_dogs | is_toxic_children | toxic_compounds | toxic_parts | severity | source |
|---------|:---:|:---:|:---:|---------|---------|----------|--------|
| *Solanum lycopersicum* | true | true | false | solanin, tomatidin | leaves, stems, unripe_fruits | mild | ASPCA |
| *Cannabis sativa* | true | true | true | THC, CBD | flowers, leaves | moderate | ASPCA |
| *Capsicum chinense* | false | false | false | capsaicin | fruits | none | Giftnotruf Bonn |
| *Ocimum basilicum* | false | false | false | – | – | none | ASPCA |
| *Mentha spicata* | false | false | false | – | – | none | ASPCA |
| *Lactuca sativa* | false | false | false | – | – | none | ASPCA |

**Weitere häufige Zimmerpflanzen (nicht in Starter-Kits, aber oft manuell angelegt):**

| Species | is_toxic_cats | is_toxic_dogs | is_toxic_children | toxic_compounds | toxic_parts | severity | source |
|---------|:---:|:---:|:---:|---------|---------|----------|--------|
| *Dieffenbachia seguine* | true | true | true | calcium_oxalate_raphides, proteolytic_enzymes | leaves, stems, sap | severe | ASPCA |
| *Spathiphyllum wallisii* | true | true | true | calcium_oxalate_raphides | leaves, stems | moderate | ASPCA |
| *Zamioculcas zamiifolia* | true | true | true | calcium_oxalate_raphides | all | moderate | ASPCA |
| *Euphorbia pulcherrima* | true | true | true | diterpen_esters | sap, leaves | mild | Giftnotruf Bonn |
| *Aloe vera* | true | true | false | anthraquinones, saponins | gel, sap | mild | ASPCA |
| *Philodendron hederaceum* | true | true | true | calcium_oxalate_raphides | leaves, stems | moderate | ASPCA |
| *Nerium oleander* | true | true | true | oleandrin, neriine | all | severe | Giftnotruf Bonn |

Hinweis: Bei manuell angelegten Species ohne Toxizitätsdaten zeigt das System den Hinweis: „Toxizitätsdaten unbekannt — Vorsicht bei Haustieren und Kleinkindern." Die externe Stammdatenanreicherung (REQ-011) kann Toxizitätsdaten automatisch über die ASPCA-API oder ähnliche Quellen nacherfassen.

### Seed-Daten: Luftreinigungseigenschaften (U-006)

Basierend auf der NASA Clean Air Study (Wolverton et al. 1989). Caveat: Bei realistischen Pflanzendichten in Wohnräumen (< 1 Pflanze/m²) ist der Luftreinigungseffekt vernachlässigbar (Cummings & Waring, 2020). Die Daten dienen primär als Zusatzinformation, nicht als Gesundheitsversprechen.

| Species | air_purification_score | removes_compounds |
|---------|:---:|---------|
| *Spathiphyllum wallisii* | 0.9 | formaldehyde, benzene, trichloroethylene, xylene, ammonia |
| *Chlorophytum comosum* | 0.8 | formaldehyde, xylene, toluene |
| *Epipremnum aureum* | 0.8 | formaldehyde, benzene, xylene |
| *Dracaena trifasciata* | 0.7 | formaldehyde, benzene, trichloroethylene, xylene, toluene |
| *Ficus lyrata* | 0.5 | formaldehyde |
| *Monstera deliciosa* | 0.3 | – (keine NASA-Studie, geringe Evidenz) |
| *Chamaedorea elegans* | 0.7 | formaldehyde, xylene |
| *Philodendron hederaceum* | 0.7 | formaldehyde |
| *Aloe vera* | 0.5 | formaldehyde, benzene |
| *Maranta leuconeura* | 0.2 | – (keine belastbare Evidenz) |

### Seed-Daten: Allergenpotenzial (U-007)

Primärquellen: European Aeroallergen Network (EAN), ECHA-Datenbank, Fachpublikationen zu Indoor-Allergenen.

| Species | latex_sap | contact_allergen | pollen_allergen | allergenic_compounds | cross_reactive_with |
|---------|:---:|:---:|:---:|---------|---------|
| *Ficus lyrata* | true | false | false | latex_proteins, furocoumarins | latex (Latex-Frucht-Syndrom) |
| *Ficus benjamina* | true | false | true | latex_proteins (Raumluft-Emission!) | latex |
| *Euphorbia pulcherrima* | true | true | false | diterpen_esters | latex |
| *Monstera deliciosa* | false | true | false | calcium_oxalate_raphides | – |
| *Dieffenbachia seguine* | false | true | false | calcium_oxalate_raphides, proteolytic_enzymes | – |
| *Epipremnum aureum* | false | true | false | calcium_oxalate_raphides | – |
| *Philodendron hederaceum* | false | true | false | calcium_oxalate_raphides | – |
| *Chlorophytum comosum* | false | false | false | – | – |
| *Chamaedorea elegans* | false | false | false | – | – |
| *Dracaena trifasciata* | false | false | false | – | – |

Hinweis: *Ficus benjamina* emittiert nachweislich Latexproteine in die Raumluft — bei Latexallergikern (1–3% der Bevölkerung) können Kreuzreaktionen auftreten. Das System zeigt bei `latex_sap: true` den Hinweis: „Enthält Milchsaft — Vorsicht bei Latexallergie."

### Seed-Daten: Vermehrungsmethoden (U-008)

| Species | propagation_methods | propagation_difficulty |
|---------|---------|:---:|
| *Monstera deliciosa* | cutting_stem, layering | easy |
| *Epipremnum aureum* | cutting_stem | easy |
| *Chlorophytum comosum* | offset, division | easy |
| *Ficus lyrata* | cutting_stem | moderate |
| *Dracaena trifasciata* | cutting_leaf, division | easy |
| *Pilea peperomioides* | offset | easy |
| *Maranta leuconeura* | division | easy |
| *Chamaedorea elegans* | seed | difficult |
| *Philodendron hederaceum* | cutting_stem, layering | easy |
| *Spathiphyllum wallisii* | division | easy |
| *Zamioculcas zamiifolia* | cutting_leaf, division | moderate |
| *Aloe vera* | offset | easy |
| *Dieffenbachia seguine* | cutting_stem | moderate |
| *Nerium oleander* | cutting_stem | moderate |
| *Solanum lycopersicum* | seed, cutting_stem, grafting | easy |
| *Cannabis sativa* | seed, cutting_stem | easy |
| *Ocimum basilicum* | seed, cutting_stem | easy |

Hinweis: Im Einsteiger-Modus (REQ-021) werden nur Arten mit `propagation_difficulty: 'easy'` als Vermehrungskandidaten vorgeschlagen. Detaillierte Vermehrungsanleitungen werden über REQ-017 (Vermehrungsmanagement) abgebildet.

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Dormanz-Trigger für mehrjährige Pflanzen:**
```python
from datetime import datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

class DormancyTrigger(BaseModel):
    """Steuerung der Winterruhe bei mehrjährigen Pflanzen"""
    
    trigger_type: Literal['temperature', 'photoperiod', 'manual']
    temperature_threshold_c: Optional[float] = Field(None, ge=-20, le=25)
    consecutive_days_required: int = Field(default=7, ge=1)
    photoperiod_threshold_hours: Optional[float] = Field(None, ge=0, le=24)
    
    @field_validator('temperature_threshold_c')
    @classmethod
    def validate_temp_trigger(cls, v, info):
        if info.data.get('trigger_type') == 'temperature' and v is None:
            raise ValueError("Temperatur-Schwelle erforderlich für temperature-Trigger")
        return v
    
    def is_triggered(
        self, 
        observations: list[dict],  # Letzte N Tage Sensor-Daten
        current_daylight_hours: float
    ) -> tuple[bool, str]:
        """
        Prüft ob Dormanz-Bedingungen erfüllt sind
        Returns: (is_dormancy_triggered, reason)
        """
        if self.trigger_type == 'manual':
            return False, "Manuelle Steuerung aktiv"
        
        if self.trigger_type == 'temperature':
            recent_temps = [obs['temperature_c'] for obs in observations[-self.consecutive_days_required:]]
            if len(recent_temps) < self.consecutive_days_required:
                return False, "Nicht genügend Temperatur-Daten"
            
            if all(temp < self.temperature_threshold_c for temp in recent_temps):
                return True, f"Temperatur < {self.temperature_threshold_c}°C für {self.consecutive_days_required} Tage"
        
        if self.trigger_type == 'photoperiod':
            if current_daylight_hours < self.photoperiod_threshold_hours:
                return True, f"Tageslänge < {self.photoperiod_threshold_hours}h"
        
        return False, "Bedingungen nicht erfüllt"
```

**2. Vernalisations-Tracker:**
```python
from datetime import date

class VernalizationTracker(BaseModel):
    """Tracking der Kälteperiode für blütenbildende Zweijährige"""
    
    required_days: int = Field(ge=0, le=180)
    temperature_range: tuple[float, float] = Field(default=(0.0, 10.0))
    accumulated_days: int = Field(default=0, ge=0)
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    
    def update(self, current_temp: float, observation_date: date) -> dict:
        """
        Aktualisiert den Vernalisations-Fortschritt
        Returns: Status-Update mit Fortschritt
        """
        if self.completion_date:
            return {
                'status': 'completed',
                'progress_percent': 100.0,
                'completed_on': self.completion_date
            }
        
        temp_in_range = self.temperature_range[0] <= current_temp <= self.temperature_range[1]
        
        if temp_in_range:
            if self.start_date is None:
                self.start_date = observation_date
            self.accumulated_days += 1
            
            if self.accumulated_days >= self.required_days:
                self.completion_date = observation_date
                return {
                    'status': 'completed',
                    'progress_percent': 100.0,
                    'completed_on': observation_date
                }
        
        progress = (self.accumulated_days / self.required_days * 100) if self.required_days > 0 else 0
        
        return {
            'status': 'in_progress' if self.accumulated_days > 0 else 'pending',
            'progress_percent': round(progress, 1),
            'accumulated_days': self.accumulated_days,
            'remaining_days': max(0, self.required_days - self.accumulated_days)
        }
```

**3. Photoperiod-Calculator:**
```python
import math
from datetime import date

class PhotoperiodCalculator:
    """Berechnet Tageslänge basierend auf Breitengrad und Datum"""
    
    @staticmethod
    def calculate_day_length(latitude: float, observation_date: date) -> float:
        """
        Berechnet Tageslänge in Stunden
        Args:
            latitude: Breitengrad in Dezimalgrad (-90 bis 90)
            observation_date: Datum der Berechnung
        Returns:
            Tageslänge in Stunden
        """
        # Vereinfachte Formel nach Forsythe et al. (1995)
        day_of_year = observation_date.timetuple().tm_yday
        
        # Deklination der Sonne
        declination = 23.44 * math.sin(math.radians((360/365) * (day_of_year - 81)))
        
        # Stundenwinkel
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        
        cos_hour_angle = -math.tan(lat_rad) * math.tan(dec_rad)
        
        # Grenzfälle (Polartag/-nacht)
        if cos_hour_angle > 1:
            return 0.0  # Polarnacht
        if cos_hour_angle < -1:
            return 24.0  # Polartag
        
        hour_angle = math.degrees(math.acos(cos_hour_angle))
        day_length = (2 * hour_angle) / 15  # 15° pro Stunde
        
        return round(day_length, 2)
    
    @staticmethod
    def is_critical_photoperiod(
        current_day_length: float,
        photoperiod_type: Literal['short_day', 'long_day', 'day_neutral'],
        critical_day_length: Optional[float]
    ) -> tuple[bool, str]:
        """
        Prüft ob kritische Photoperiode für Blüteninduktion erreicht ist
        """
        if photoperiod_type == 'day_neutral':
            return True, "Tagneutrale Pflanze - Photoperiode irrelevant"
        
        if critical_day_length is None:
            return False, "Kritische Tageslänge nicht definiert"
        
        if photoperiod_type == 'short_day':
            triggered = current_day_length < critical_day_length
            reason = f"Tageslänge {current_day_length}h {'<' if triggered else '>='} kritisch {critical_day_length}h"
            return triggered, reason
        
        if photoperiod_type == 'long_day':
            triggered = current_day_length > critical_day_length
            reason = f"Tageslänge {current_day_length}h {'>' if triggered else '<='} kritisch {critical_day_length}h"
            return triggered, reason
        
        return False, "Unbekannter Photoperiod-Typ"
```

**4. Species-Validator:**
```python
from typing import Optional
from pydantic import BaseModel, field_validator, Field

class ToxicityInfo(BaseModel):
    """Toxizitätsdaten auf Species-Ebene für Haustier-/Kindersicherheit.

    Primärquellen: ASPCA Animal Poison Control (aspca.org),
    Giftinformationszentrale Bonn (gizbonn.de).
    """
    is_toxic_cats: bool = False
    is_toxic_dogs: bool = False
    is_toxic_children: bool = False
    toxic_compounds: list[str] = Field(default_factory=list, description="z.B. ['calcium_oxalate_raphides', 'saponins']")
    toxic_parts: list[str] = Field(default_factory=list, description="z.B. ['leaves', 'stems', 'sap', 'roots', 'seeds', 'flowers']")
    severity: Literal['none', 'mild', 'moderate', 'severe'] = 'none'
    source: str = Field('', description="Datenquelle, z.B. 'ASPCA', 'Giftnotruf Bonn'")

class AllergenInfo(BaseModel):
    """Allergen-Potenzial einer Spezies.

    Primärquellen: ARIA (Allergic Rhinitis and its Impact on Asthma),
    European Aeroallergen Network (EAN), ECHA-Datenbank für Kontaktallergene.
    """
    latex_sap: bool = Field(False, description="Milchsaft vorhanden — Kontaktdermatitis-Risiko (z.B. Ficus, Euphorbia)")
    contact_allergen: bool = Field(False, description="Kontaktallergen, z.B. Calciumoxalat-Raphide (Dieffenbachia, Monstera)")
    pollen_allergen: bool = Field(False, description="Pollenallergen — relevant für blühende Zimmerpflanzen im Innenraum")
    allergenic_compounds: list[str] = Field(default_factory=list, description="z.B. ['latex_proteins', 'furocoumarins', 'linalool']")
    cross_reactive_with: list[str] = Field(default_factory=list, description="Kreuzreaktionen, z.B. ['latex'] bei Ficus (Latex-Frucht-Syndrom)")
    source: str = Field('', description="Datenquelle, z.B. 'EAN', 'ECHA'")

class SpeciesDefinition(BaseModel):
    """Vollständige Spezies-Definition für Stammdaten"""

    scientific_name: str = Field(regex=r'^[A-Z][a-z]+ [a-z]+$', description="Binomiale Nomenklatur")
    common_names: list[str] = Field(min_items=1)
    family: str
    genus: str
    cycle_type: Literal['annual', 'biennial', 'perennial']
    photoperiod_type: Literal['short_day', 'long_day', 'day_neutral']
    hardiness_zones: list[str] = Field(min_items=1)
    growth_habit: Literal['herb', 'shrub', 'tree', 'vine', 'groundcover']
    root_type: Literal['fibrous', 'taproot', 'tuberous', 'bulbous', 'rhizomatous', 'aerial']
    root_adaptations: list[str] = Field(
        default_factory=list,
        description="Ergänzende Wurzelanpassungen, z.B. ['aerial', 'epiphytic', 'stoloniferous']"
    )
    toxicity: ToxicityInfo = Field(default_factory=ToxicityInfo, description="Toxizitätsdaten für Haustiere und Kinder")
    air_purification_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="NASA Clean Air Study Bewertung (0=keine Wirkung, 1=stark luftreinigend). Caveat: Effekt bei realistischen Pflanzendichten vernachlässigbar."
    )
    removes_compounds: list[str] = Field(
        default_factory=list,
        description="Gefilterte Schadstoffe, z.B. ['formaldehyde', 'benzene', 'toluene']"
    )
    allergen_info: Optional[AllergenInfo] = Field(
        None,
        description="Allergenpotenzial — Pollen, Kontaktallergene, VOC-Emissionen"
    )
    propagation_methods: list[Literal[
        'seed', 'cutting_stem', 'cutting_leaf', 'division',
        'offset', 'layering', 'grafting', 'spore'
    ]] = Field(default_factory=list, description="Unterstützte Vermehrungsmethoden (REQ-017)")
    propagation_difficulty: Optional[Literal['easy', 'moderate', 'difficult']] = Field(
        None,
        description="Schwierigkeitsgrad für Einsteiger — wird im Beginner-Modus (REQ-021) angezeigt"
    )
    vernalization_required: bool = False
    vernalization_days: Optional[int] = Field(None, ge=0, le=180)

    # Freiland-/Gartenplanung (Quelle: Outdoor-Garden-Planner Review G-001)
    frost_sensitivity: Optional[Literal['hardy', 'half_hardy', 'tender']] = Field(
        None, description="hardy = übersteht Frost, half_hardy = leichter Frost ok, tender = frostfrei halten"
    )
    hardiness_detail: Optional[str] = Field(
        None, description="z.B. 'Winterhart bis -15°C, Wurzelschutz empfohlen'"
    )
    sowing_indoor_weeks_before_last_frost: Optional[int] = Field(
        None, ge=1, le=20, description="Voranzucht: Wochen vor letztem Frost, z.B. 8 für Tomaten"
    )
    sowing_outdoor_after_last_frost_days: Optional[int] = Field(
        None, ge=-30, le=90, description="Direktsaat: Tage nach letztem Frost, z.B. 0 für Erbsen, 14 für Bohnen"
    )
    direct_sow_months: Optional[list[int]] = Field(
        None, description="Monate für Direktsaat, z.B. [3,4,5] für Möhren"
    )
    harvest_months: Optional[list[int]] = Field(
        None, description="Erntemonate, z.B. [7,8,9] für Tomaten"
    )
    nutrient_demand_level: Optional[Literal['heavy_feeder', 'medium_feeder', 'light_feeder', 'nitrogen_fixer']] = Field(
        None, description="Starkzehrer/Mittelzehrer/Schwachzehrer/Stickstoff-Fixierer für Fruchtfolge-Planung"
    )
    green_manure_suitable: bool = Field(
        False, description="Eignung als Gründüngung — z.B. Phacelia, Senf, Lupine"
    )
    pruning_months: Optional[list[int]] = Field(
        None, description="Empfohlene Schnittmonate, z.B. [2,3] für Kernobst"
    )
    pruning_type: Optional[Literal['winter_pruning', 'summer_pruning', 'after_harvest', 'spring_pruning', 'none']] = None
    bloom_months: Optional[list[int]] = Field(
        None, description="Blütemonate — für Blühkalender und Bestäuber-Planung"
    )
    # /Quelle: Outdoor-Garden-Planner Review G-001

    # Quelle: Agrarbiologie-Review AB-004, 2026-03
    traits: list[str] = Field(
        default_factory=list,
        description="Tags auf Species-Ebene, z.B. ['ornamental']. Analog zu Cultivar.traits."
    )

    @field_validator('scientific_name')
    @classmethod
    def validate_scientific_name(cls, v):
        """Validiert Binomialnomenklatur und Hybridnotation.

        Akzeptiert:
        - "Genus species" (2 Teile, Standard-Binomial)
        - "Genus x species" oder "Genus × species" (3 Teile, Hybrid-Notation)
        """
        parts = v.split()
        if len(parts) == 3 and parts[1] in ('x', '×'):
            return v  # Gültige Hybrid-Notation (z.B. "Viola x wittrockiana", "Calibrachoa × hybrida")
        if len(parts) != 2:
            raise ValueError(
                "Wissenschaftlicher Name muss Binomialnomenklatur (Gattung Art) "
                "oder Hybridnotation (Gattung × Art) sein"
            )
        return v
    
    @field_validator('vernalization_days')
    @classmethod
    def validate_vernalization(cls, v, info):
        if info.data.get('vernalization_required') and v is None:
            raise ValueError("Vernalisations-Dauer erforderlich wenn vernalization_required=True")
        if not info.data.get('vernalization_required') and v is not None:
            raise ValueError("Vernalisations-Dauer nur bei vernalization_required=True")
        return v
    
    @field_validator('cycle_type')
    @classmethod
    def validate_biennial_vernalization(cls, v, info):
        if v == 'biennial' and not info.data.get('vernalization_required'):
            import warnings
            warnings.warn(
                "Zweijährige ohne Vernalisation — bitte prüfen. "
                "Die meisten Zweijährigen benötigen Vernalisation, aber nicht alle "
                "(z.B. Beta vulgaris kann unter Langtagsbedingungen auch ohne Kälteperiode schossen)."
            )
        return v

class CultivarDefinition(BaseModel):
    """Sorte/Zuchtform innerhalb einer Spezies"""

    name: str
    parent_species: str  # scientific_name der Stammspezies
    breeder: Optional[str] = None
    breeding_year: Optional[int] = Field(None, ge=1800, le=2100)
    traits: list[str] = Field(default_factory=list)
    days_to_maturity: Optional[int] = Field(None, ge=1, le=365)
    disease_resistances: list[str] = Field(default_factory=list)

    # Quelle: Cannabis Indoor Grower Review G-009
    photoperiod_type: Optional[Literal['photoperiodic', 'autoflower', 'day_neutral']] = None
    autoflower_days_to_flower: Optional[int] = Field(
        None, ge=14, le=45,
        description="Tage nach Keimung bis Blüte-Eintritt (nur bei autoflower)"
    )
    autoflower_total_cycle_days: Optional[int] = Field(
        None, ge=45, le=120,
        description="Erwartete Gesamtdauer Keimung bis Ernte (nur bei autoflower)"
    )
    # /Quelle: G-009

    # Obstbau & Dauerkulturen (Quelle: Outdoor-Garden-Planner Review G-006)
    rootstock: Optional[str] = Field(
        None, description="Unterlage bei Obstbäumen, z.B. 'M9' für Zwergwuchs, 'M26' für Halbstamm"
    )
    requires_pollinator: Optional[bool] = Field(
        None, description="Benötigt Befruchtersorte — z.B. true für die meisten Apfelsorten"
    )
    pollinator_group: Optional[str] = Field(
        None, description="Befruchtungsgruppe, z.B. '3' — kompatible Gruppen: n-1, n, n+1"
    )
    compatible_pollinators: Optional[list[str]] = Field(
        None, description="Empfohlene Befruchtersorten, z.B. ['Goldparmäne', 'James Grieve']"
    )
    years_to_first_harvest: Optional[int] = Field(
        None, ge=1, le=30, description="Jahre bis Erstertrag, z.B. 3-5 bei Apfel auf M9"
    )
    biennial_bearing: Optional[bool] = Field(
        None, description="Alternanz — Tendenz zu Ertragsschwankungen jedes 2. Jahr"
    )
    berry_type: Optional[Literal['summer_bearing', 'autumn_bearing', 'everbearing']] = Field(
        None, description="Himbeeren: Sommer- vs. Herbsthimbeere — unterschiedliche Schnittregeln!"
    )
    max_stand_years: Optional[int] = Field(
        None, ge=1, le=100, description="Maximale Standzeit, z.B. 3-4 für Erdbeeren, dann neu pflanzen"
    )
    seed_type: Optional[Literal['open_pollinated', 'f1_hybrid', 'f2', 'landrace', 'clone']] = Field(
        None, description="samenfest vs. F1-Hybrid — relevant für eigene Saatgutgewinnung"
    )
    # /Quelle: Outdoor-Garden-Planner Review G-006

    @field_validator('traits')
    @classmethod
    def validate_traits(cls, v):
        valid_traits = {
            'disease_resistant', 'pest_resistant', 'high_yield', 'compact',
            'drought_tolerant', 'cold_hardy', 'heat_tolerant', 'early_maturing',
            'long_season', 'ornamental', 'heirloom', 'hybrid', 'f1',
            'autoflower',  # Quelle: G-009
            'self_cleaning',  # Quelle: AB-016 — verblühte Blüten fallen von selbst (kein Deadheading nötig)
        }
        invalid = set(v) - valid_traits
        if invalid:
            raise ValueError(f"Ungültige Traits: {invalid}")
        return v

    # Quelle: Cannabis Indoor Grower Review G-009
    @model_validator(mode='after')
    def validate_autoflower_fields(self):
        """Autoflower-spezifische Felder nur bei photoperiod_type='autoflower' erlaubt"""
        if self.photoperiod_type != 'autoflower':
            if self.autoflower_days_to_flower is not None:
                raise ValueError(
                    "autoflower_days_to_flower nur bei photoperiod_type='autoflower' erlaubt"
                )
            if self.autoflower_total_cycle_days is not None:
                raise ValueError(
                    "autoflower_total_cycle_days nur bei photoperiod_type='autoflower' erlaubt"
                )
        else:
            # Bei Autoflower: Empfehlung, falls Gesamtzyklus nicht gesetzt
            if self.autoflower_days_to_flower and self.autoflower_total_cycle_days:
                if self.autoflower_days_to_flower >= self.autoflower_total_cycle_days:
                    raise ValueError(
                        "autoflower_days_to_flower muss kleiner als "
                        "autoflower_total_cycle_days sein"
                    )
        return self
    # /Quelle: G-009
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional
from enum import Enum

class GrowthHabit(str, Enum):
    HERB = "herb"
    SHRUB = "shrub"
    TREE = "tree"
    VINE = "vine"
    GROUNDCOVER = "groundcover"

class RootType(str, Enum):
    FIBROUS = "fibrous"
    TAPROOT = "taproot"
    TUBEROUS = "tuberous"
    BULBOUS = "bulbous"
    RHIZOMATOUS = "rhizomatous"  # Rhizom-bildend (Calathea, Ingwer, Farne)
    AERIAL = "aerial"            # Luftwurzeln/hemiepiphytisch (Monstera, Orchideen)

class PhotoperiodType(str, Enum):
    SHORT_DAY = "short_day"
    LONG_DAY = "long_day"
    DAY_NEUTRAL = "day_neutral"

# Quelle: Cannabis Indoor Grower Review G-009
class CultivarPhotoperiodType(str, Enum):
    """Cultivar-spezifische Lichtreaktion (überschreibt Species-Level PhotoperiodType)"""
    PHOTOPERIODIC = "photoperiodic"  # Blüte durch Lichtperiodenwechsel (z.B. 12/12)
    AUTOFLOWER = "autoflower"        # Blüte nach Alter, durchgehend 20/4 oder 18/6
    DAY_NEUTRAL = "day_neutral"      # Tagneutral (z.B. immertragende Erdbeeren)
# /Quelle: G-009

CycleType = Literal['annual', 'biennial', 'perennial']
NutrientDemand = Literal['light', 'medium', 'heavy']

class RootDepth(str, Enum):
    """Typische Wurzeltiefe einer Pflanzenfamilie"""
    SHALLOW = "shallow"      # < 30 cm
    MEDIUM = "medium"        # 30–60 cm
    DEEP = "deep"            # > 60 cm

class FrostTolerance(str, Enum):
    """Frosttoleranz-Stufe"""
    SENSITIVE = "sensitive"      # Schäden ab 0°C
    MODERATE = "moderate"        # Tolerant bis -2°C
    HARDY = "hardy"              # Tolerant bis -5°C
    VERY_HARDY = "very_hardy"    # Tolerant unter -5°C

class PollinationType(str, Enum):
    """Bestäubungstyp"""
    INSECT = "insect"    # Insektenbestäubung
    WIND = "wind"        # Windbestäubung
    SELF = "self"        # Selbstbestäubung
```

**Embedded Model — PhRange:**
```python
class PhRange(BaseModel):
    """pH-Bereich-Präferenz für Bodenmilieu"""

    min_ph: float = Field(ge=3.0, le=9.0, description="Minimaler pH-Wert")
    max_ph: float = Field(ge=3.0, le=9.0, description="Maximaler pH-Wert")

    @field_validator('max_ph')
    @classmethod
    def validate_ph_range(cls, v, info):
        if 'min_ph' in info.data and v < info.data['min_ph']:
            raise ValueError(f"max_ph ({v}) muss >= min_ph ({info.data['min_ph']}) sein")
        return v
```

**BotanicalFamily-Validator:**
```python
class BotanicalFamilyDefinition(BaseModel):
    """Vollständige Pflanzenfamilien-Definition mit erweiterten Attributen"""

    name: str = Field(description="Botanischer Familienname, muss auf '-aceae' enden")
    common_name_de: str = Field(description="Deutscher Anzeigename")
    common_name_en: str = Field(description="Englischer Anzeigename")
    order: Optional[str] = Field(None, description="Taxonomische Ordnung, muss auf '-ales' enden")
    description: str = Field(default="", description="Botanische Kurzbeschreibung")
    typical_nutrient_demand: NutrientDemand
    nitrogen_fixing: bool = Field(default=False, description="Stickstofffixierung (Fabaceae=true)")
    typical_root_depth: RootDepth
    soil_ph_preference: Optional[PhRange] = None
    frost_tolerance: FrostTolerance
    typical_growth_forms: list[GrowthHabit] = Field(min_items=1)
    common_pests: list[str] = Field(default_factory=list)
    common_diseases: list[str] = Field(default_factory=list)
    pollination_type: list[PollinationType] = Field(min_items=1)
    rotation_category: str

    @field_validator('name')
    @classmethod
    def validate_family_name(cls, v):
        if not v.endswith('aceae'):
            raise ValueError(f"Familienname '{v}' muss auf '-aceae' enden")
        return v

    @field_validator('order')
    @classmethod
    def validate_order_name(cls, v):
        if v is not None and not v.endswith('ales'):
            raise ValueError(f"Ordnungsname '{v}' muss auf '-ales' enden")
        return v

    @field_validator('nitrogen_fixing')
    @classmethod
    def validate_nitrogen_fixing_demand(cls, v, info):
        if v and info.data.get('typical_nutrient_demand') == 'heavy':
            raise ValueError(
                "nitrogen_fixing=true ist inkompatibel mit typical_nutrient_demand='heavy'. "
                "Stickstofffixierende Familien sind Schwach- oder Mittelzehrer."
            )
        return v
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

Stammdaten sind globale Referenzdaten und nicht Tenant-scoped. Lesezugriff ist öffentlich (kein Token erforderlich). Schreiboperationen erfordern einen authentifizierten Benutzer.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| BotanicalFamilies (globale Referenzdaten) | Nein | Ja | Ja |
| Species (globale Referenzdaten) | Nein | Ja | Ja |
| Cultivars (globale Referenzdaten) | Nein | Ja | Ja |
| CompanionPlanting (Graph-Beziehungen) | Nein | Ja | Ja |
| CropRotation (Graph-Beziehungen) | Nein | Ja | Ja |

## 5. Abhängigkeiten

**Erforderliche externe Datenquellen:**
- USDA Plant Database (Hardiness Zones, native Habitats)
- GRIN Taxonomy (Germplasm Resources Information Network)
- Sortenkataloge (EU-Sortenkatalog, nationale Register)

**Systemabhängigkeiten:**
- Keine - Dies ist das Fundament-Modul, auf dem alle anderen aufbauen

**Wird benötigt von:**
- REQ-002 (Standortverwaltung) - Familie für Fruchtfolge; **HOCH:** shares_pest_risk + nitrogen_fixing für erweiterte Rotation-Validierung nutzen
- REQ-003 (Phasensteuerung) - Lifecycle für Phasen-Übergänge
- REQ-004 (Düngung) - Familie für Nährstoffbedarf; **MITTEL:** N-Reduktion bei nitrogen_fixing=true, soil_ph_preference als Default-Zielwert
- REQ-007 (Ernte) - Reife-Zeitpunkte
- REQ-010 (IPM) - Familienspezifische Schädlinge; **HOCH:** common_diseases + shares_pest_risk für automatische IPM-Inspektionsplanung
- REQ-011 (Externe Enrichment) - **MITTEL:** GBIF-Adapter: `order`-Feld mappen
- REQ-012 (CSV-Import) - **NIEDRIG:** Neue BotanicalFamily-Felder im Import unterstützen

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Taxonomische Vollständigkeit:** Mindestens 50 Spezies mit vollständigen botanischen Metadaten im System
- [ ] **Lifecycle-Konfiguration:** Jede Spezies hat eine valide LifecycleConfig mit mindestens 3 GrowthPhases
- [ ] **Familienbeziehungen:** Alle Spezies sind einer BotanicalFamily zugeordnet
- [ ] **Sortenvielfalt:** Mindestens 3 Cultivars pro häufiger Nutzpflanze (z.B. Tomate, Paprika, Salat)
- [ ] **Mischkultur-Matrix:** Kompatibilitäts-Beziehungen für mindestens 20 Spezies-Paare definiert
- [ ] **Fruchtfolge-Regeln:** Rotation-Empfehlungen zwischen den 9 wichtigsten Pflanzenfamilien
- [ ] **Erweiterte BotanicalFamily:** Alle 9 Seed-Familien mit vollständigen erweiterten Attributen (common_name_de/en, order, nitrogen_fixing, typical_root_depth, frost_tolerance, pollination_type, common_diseases, soil_ph_preference)
- [ ] **Familien-Kanten (rotation_after):** Mind. 16 gerichtete rotation_after-Kanten mit benefit_score und benefit_reason
- [ ] **Familien-Kanten (shares_pest_risk):** Mind. 7 bidirektionale shares_pest_risk-Kanten mit shared_pests/diseases und risk_level
- [ ] **Familien-Kanten (family_compatible_with):** Mind. 8 bidirektionale family_compatible_with-Kanten mit benefit_type und compatibility_score
- [ ] **Familien-Kanten (family_incompatible_with):** Mind. 3 bidirektionale family_incompatible_with-Kanten (Selbstinkompatibilitäten)
- [ ] **CropRotationValidator:** Differenzierte Warnungen (CRITICAL/WARNING/INFO) basierend auf Familien-Kanten und Pest-Risiko
- [ ] **CompanionPlantingEngine:** Family-Level Fallback wenn keine Spezies-Level Mischkultur-Kante existiert (Score × 0.8 Abschlag)
- [ ] **i18n-Anzeige:** common_name_de/en in UI je nach Spracheinstellung angezeigt
- [ ] **Validierung (BotanicalFamily):** Familienname endet auf "-aceae", Ordnungsname auf "-ales", nitrogen_fixing=true + heavy-Demand wird abgelehnt
<!-- Quelle: Cannabis Indoor Grower Review G-009 -->
- [ ] **Cultivar-Photoperiod-Type:** Cultivar-Feld `photoperiod_type` (photoperiodic/autoflower/day_neutral) überschreibt Species-Level `PhotoperiodType`
- [ ] **Autoflower-Validierung:** `autoflower_days_to_flower` und `autoflower_total_cycle_days` nur bei `photoperiod_type='autoflower'` akzeptiert
- [ ] **Autoflower-Trait:** Trait `'autoflower'` als valider Cultivar-Trait akzeptiert
<!-- /Quelle: G-009 -->
- [ ] **Photoperiod-Berechnung:** Automatische Tageslängen-Berechnung basierend auf Standort-Koordinaten
- [ ] **Vernalisations-Tracking:** System erkennt Kälteperioden und triggert Blüteninduktion bei Zweijährigen
- [ ] **Dormanz-Steuerung:** Automatischer Übergang in Winterruhe bei mehrjährigen Pflanzen
- [ ] **Validierung:** Import-Funktion prüft wissenschaftliche Namen gegen GRIN-Datenbank
- [ ] **Duplikatsprüfung:** System verhindert Mehrfach-Einträge derselben Spezies
- [ ] **Versionierung:** Änderungen an Spezies-Definitionen werden historisiert
- [ ] **API-Export:** GraphQL/REST-Endpoint für externe Nutzung der Stammdaten
- [ ] **Bulk-Import:** CSV/JSON-Import für initiale Datenbefüllung
- [ ] **Kulturdatenblätter:** Automatische Generierung von Pflege-Empfehlungen aus Stammdaten

### Testszenarien:

**Szenario 1: Einjährige Pflanze - Vollständiger Zyklus**
```
GIVEN: Basilikum (Ocimum basilicum) als einjährige Langtagspflanze
WHEN: Alle Phasen durchlaufen (Keimung → Vegi → Blüte → Samen)
THEN: 
  - System markiert Pflanze nach Samenernte als "Lifecycle Complete"
  - Standort wird für neue Anpflanzung freigegeben
  - Keine Dormanz-Phase wird generiert
```

**Szenario 2: Zweijährige mit Vernalisation**
```
GIVEN: Petersilie (Petroselinum crispum) als Zweijährige
WHEN: Erste Vegetationsperiode abgeschlossen, Winter mit 45 Tagen < 10°C
THEN:
  - VernalizationTracker zeigt 100% Fortschritt
  - System aktiviert Blüten-Phase für zweite Saison
  - Alert: "Petersilie schießt - Ernte nicht mehr möglich"
```

**Szenario 3: Mehrjährige Dormanz**
```
GIVEN: Erdbeere (Fragaria × ananassa) als mehrjährige Pflanze
WHEN: Temperatur < 5°C für 7 aufeinanderfolgende Tage im November
THEN:
  - DormancyTrigger aktiviert Winterruhe
  - Bewässerungs- und Dünge-Tasks werden pausiert
  - System plant Reaktivierung für März (basierend auf Klimazone)
```

**Szenario 4: Photoperiod-Blüte**
```
GIVEN: Cannabis (Cannabis sativa) als photoperiodische Kurztagspflanze, kritische Tageslänge: 12-13h
  - Vegetative Phase: ≥18h Licht / ≤6h Dunkelheit (Indoor-Standard 18/6)
  - Blüte-Phase: ≤12h Licht / ≥12h ununterbrochene Dunkelheit (Indoor-Standard 12/12)
  - Autoflowering-Sorten (ruderalis-Hybriden): tagneutral, blühen unabhängig von Photoperiode
WHEN: Tageslänge fällt unter 13h (Outdoor: ca. Mitte September, 50°N) ODER Indoor-Lichtzyklus wird auf 12/12 umgestellt
THEN:
  - System erkennt Blüten-Trigger
  - Automatischer Übergang von Vegi → Blüte-Phase
  - Düngeprofil wechselt zu Blüte-NPK
  - Bei Autoflowering: Phasenübergang nach konfigurierten GDD oder Kalendertagen
```

<!-- Quelle: Cannabis Indoor Grower Review G-009 -->
**Szenario 4a: Autoflower-Cultivar anlegen**
```
GIVEN: Nutzer erstellt Cultivar "Northern Lights Auto" für Species "Cannabis sativa"
  - photoperiod_type: 'autoflower'
  - autoflower_days_to_flower: 25 (Tage nach Keimung)
  - autoflower_total_cycle_days: 75
  - traits: ['autoflower', 'compact']
WHEN: Cultivar wird gespeichert
THEN:
  - System validiert autoflower-spezifische Felder (days_to_flower < total_cycle_days)
  - Species-Level PhotoperiodType (short_day) wird durch Cultivar-Level 'autoflower' überschrieben
  - REQ-003 verwendet autoflower_days_to_flower für automatischen Vegi→Blüte Übergang
  - REQ-003 setzt Lichtprofil auf 20/4 oder 18/6 durchgehend (kein 12/12 Wechsel)
  - REQ-006 zeigt Warnung bei HST-Tasks (Topping/FIM) für diesen Cultivar
```

**Szenario 4b: Photoperiodischer Cultivar (Standard)**
```
GIVEN: Nutzer erstellt Cultivar "Northern Lights" für Species "Cannabis sativa"
  - photoperiod_type: 'photoperiodic' (oder None → übernimmt Species-Level short_day)
WHEN: Cultivar wird gespeichert
THEN:
  - Kein autoflower_days_to_flower erlaubt (Validierungsfehler falls gesetzt)
  - REQ-003 verwendet manuelle oder photoperiod-basierte Blüte-Einleitung
  - Lichtprofil wechselt bei Blüte auf 12/12
  - HST-Tasks (Topping/FIM) sind ohne Einschränkung erlaubt in Vegi-Phase
```
<!-- /Quelle: G-009 -->

**Szenario 5: Fruchtfolge-Validierung**
```
GIVEN: Letzte Kultur war Tomate (Solanaceae), geplant ist Kartoffel (Solanaceae)
WHEN: Nutzer versucht Kartoffel am gleichen Slot zu pflanzen
THEN:
  - System zeigt CRITICAL-Warnung
  - Empfiehlt Mindestabstand: 3 Jahre
  - Schlägt alternative Familien vor (z.B. Fabaceae, Brassicaceae)
```

**Szenario 6: Stickstoff-Rotation-Empfehlung**
```
GIVEN: Letzte Kultur war Brokkoli (Brassicaceae, Starkzehrer)
WHEN: Nutzer fragt nach Rotationsempfehlung für nächste Saison
THEN:
  - System empfiehlt Fabaceae als Nachfolger (benefit_score: 0.90, reason: "nitrogen_fixation")
  - Hinweis: "Hülsenfrüchtler fixieren Stickstoff und regenerieren den Boden nach Starkzehrern"
  - 3-Jahres-Plan: Brassicaceae → Fabaceae → Solanaceae (basierend auf rotation_after-Ketten)
```

**Szenario 7: Familien-Level Pest-Warnung**
```
GIVEN: Vorkultur war Tomate (Solanaceae), geplant ist Gurke (Cucurbitaceae)
WHEN: Fruchtfolge-Validierung wird ausgeführt
THEN:
  - System zeigt WARNING (nicht CRITICAL, da verschiedene Familien)
  - Warnung: "Gemeinsames Schädlingsrisiko: Blattläuse, Weiße Fliege (medium)"
  - Quelle: shares_pest_risk-Kante zwischen Solanaceae und Cucurbitaceae
  - Empfehlung: "Schädlingsmonitoring verstärken oder Lamiaceae als Zwischenkultur"
```

**Szenario 8: Familien-Level Mischkultur-Fallback**
```
GIVEN: Spezies "Capsicum annuum" (Paprika) hat keine Spezies-Level compatible_with-Kante zu "Phaseolus vulgaris" (Buschbohne)
WHEN: Mischkultur-Empfehlung wird abgefragt
THEN:
  - Kein Spezies-Level Match gefunden
  - Fallback auf Familien-Level: family_compatible_with(Solanaceae, Fabaceae)
  - Empfehlung: "Buschbohne (Familien-Level: Fabaceae↔Solanaceae, Score: 0.68)"
  - Score = 0.85 × 0.8 (20% Familien-Level Abschlag)
  - match_level: "family" wird in der Antwort ausgewiesen
```

---

**Hinweise für RAG-Integration:**
- Keywords: Taxonomie, Lebenszyklus, Photoperiodismus, Vernalisation, Dormanz, Fruchtfolge, Mischkultur, Stickstofffixierung, Schädlingsrisiko, Familien-Kompatibilität
- Botanische Fachbegriffe: Binomiale Nomenklatur, Allelopathie, Vernalisation, Photoperiode, Hardiness Zones, Frosttoleranz, Bestäubungstyp, Wurzeltiefe
- Verknüpfung: Basis-Modul für alle REQ-002 bis REQ-012
