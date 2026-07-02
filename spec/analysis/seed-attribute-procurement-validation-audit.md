# Audit: Beschaffungs- & Validierungs-Strategie je Seed-Attribut

**Erstellt von:** Agent/Skill-Audit (Claude Code)
**Datum:** 2026-07-02
**Frage:** Existiert für **jedes** Attribut des Seed-Datenmodells eine (a) **Beschaffungsstrategie** (welcher Agent/Skill recherchiert/erzeugt es) und (b) **Validierungsstrategie** (Schema/Struktur + fachliche/semantische Prüfung)?
**Nachfolge zu:** `spec/analysis/seed-pipeline-agent-review.md` (PR #300)

> **Umsetzungs-Status:** Alle hier dokumentierten Lücken **G1–G7 wurden aufgearbeitet** (siehe Abschnitt „Empfehlungen" → jeweils umgesetzt): Generator um Family-Stammdaten + Cultivar-Qualitätsfelder + `KA-Feld`-Anker erweitert (G1/G2); Validator-Plausibilitätstabelle auf aktuelle Feldnamen korrigiert + um Physiologie/Salz/Saatgut erweitert (G3/G4); Cross-Field-Konsistenzregeln ergänzt (G5); neuer fachlicher Prüf-Skill `check-seed-data` analog `check-pest-data` (G6/G7). Der folgende Text beschreibt den **Ausgangszustand** (vor der Aufarbeitung).

---

## Methode & Scope

**Autoritativer Attribut-Bestand:** `plant_info.schema.yaml`, `species.schema.yaml`, `_defs.schema.yaml` + die Pydantic-Modelle (`species.py`, `phase.py`, `ipm.py`, …). Die Coverage-Matrix wurde **deterministisch per Whole-Word-Grep** über die Agent-/Skill-Dateien erstellt (nicht geschätzt).

**Beteiligte Agenten & Skills:**

| Rolle | Artefakt | Beitrag |
|------|----------|---------|
| **Beschaffung** | `plant-info-document-generator` (Agent) | Primär: recherchiert Species/Cultivar/Phasen/Nährstoffe/IPM/Companion → Markdown-Steckbrief |
| Beschaffung (Subset) | `growing-phase-auditor` (Agent) | Nur Phasen-Monate (`bloom_/direct_sow_/harvest_months`, `sowing_indoor/outdoor`, `frost_sensitivity`) prüfen/korrigieren |
| Transport/Mapping | `plant-info-to-seed-yaml` (Agent) | Markdown → schema-konforme YAML (kein Beschaffer, sondern Carrier) |
| **Validierung (strukturell)** | `seed-data-validator` (Agent) + JSON-Schema + Pydantic | Schema-Konformität, Enums, Pflichtfelder, referenzielle Integrität, Duplikate |
| **Validierung (fachlich)** | `check-pest-data` (Skill) | Tiefe biologische Prüfung **nur** IPM (Pest/Disease/Treatment) |
| Validierung (fachlich, Spec) | `agrobiology-requirements-reviewer` (Agent) | `[AGROBIO-CHECK]`-Findings verifizieren (Spec-Ebene) |
| — (außerhalb) | `gen-knowledge` (Skill) | RAG-Wissensdokumente, **keine** Seed-Attribute |

**Zwei Validierungs-Ebenen werden unterschieden** — das ist der Kern der Analyse:

- **Strukturell** = Schema-Constraint (`enum`/`minimum`/`maximum`/`required`/`pattern`) + Pydantic-Validierung beim Import. Greift **automatisch für jedes schema-definierte Feld**.
- **Semantisch/fachlich** = biologische Plausibilität (Wertebereich sinnvoll für die Art), Cross-Field-Konsistenz, taxonomische Korrektheit. Greift **nur** dort, wo ein Agent/Skill es explizit prüft.

**Legende Matrix:** `✓`/`·` = Attribut-Token im jeweiligen Artefakt vorhanden.
`G`=Generator (Beschaffung) · `C`=Converter (Mapping) · `V`=Validator (explizite Erwähnung) · `P`=PhaseAuditor · `K`=check-pest-data.

> **Wichtige Lesehilfe:** Ein `·` in Spalte **G** bedeutet nicht immer „nicht beschafft". Der Generator beschafft Phasen-Kernfelder (`duration_days`, `sequence_order` …) und Nährstoffe (`npk_ratio`, EC, pH) über **deutsche Tabellen-Spaltenüberschriften ohne `KA-Feld`-Token** — sie werden recherchiert, aber ohne maschinenlesbares Mapping-Anker (siehe Lücke **G2**).

---

## Coverage-Matrix (verdichtet)

### Species — Kern, Ernte, Standort
Nahezu vollständig beschafft **und** strukturell validiert (nach PR #300).

| Klasse | Beschaffung (G) | Struktur-Validierung | Semantische Validierung |
|--------|----------------|----------------------|--------------------------|
| Kern (`scientific_name`, `common_names`, `genus`, `growth_habit`, `root_type`, `family`, `hardiness_zones`, `plant_category`, `nutrient_demand_level`, `frost_sensitivity`, `base_temp`, `green_manure_suitable`) | ✓ Generator | ✓ Schema-Enums/Pattern/Required | Teilweise: Taxonomie/Familie via `[AGROBIO-CHECK]`; `frost_sensitivity` via PhaseAuditor. `base_temp`/`allelopathy_score`/`native_habitat`: **nur strukturell** |
| Ernte/Aussaat (`*_months`, `sowing_*`, `harvest_pattern`, `harvested_part`, `climacteric`) | ✓ Generator + ✓ PhaseAuditor (Monate) | ✓ Schema (Monate 1–12, Enums) | Monate: ✓ PhaseAuditor (biologisch). `harvest_pattern`/`harvested_part`/`climacteric`: **nur strukturell**, keine Cross-Field-Prüfung |
| Container/Standort (`*_container_*`, `mature_*`, `spacing_cm`, `indoor/balcony_suitable`, `greenhouse_recommended`, `support_required`) | ✓ Generator | ✓ Schema (Enums/Ranges) | **Keine** semantische Prüfung |

### Species — Physiologie & Saatgut (REQ-001 v4.2 / B7)
Beschaffung ✓, Struktur ✓, **semantische Validierung fehlt fast durchgängig**.

| Attribut | G | C | V | Semantische Validierung |
|----------|---|---|---|--------------------------|
| `photosynthesis_type`, `shade_tolerance`, `waterlogging_tolerance`, `salt_tolerance_class` | ✓ | ✓ | ✓ (erwähnt) | Enum-strukturell; **keine** Plausibilität |
| `light_compensation_point_ppfd_min/max`, `effective_root_depth_cm`, `soil_ph_preference` | ✓ | ✓ | teils | Schema-Range; **keine** Plausibilität/Cross-Field |
| `salt_tolerance_ece_threshold_ds_m`, `salt_tolerance_slope_pct` | ✓ | ✓ | · | Schema `min 0`; **keine** Konsistenz mit `salt_tolerance_class` |
| `seed_profile.*` (`germination_temp_min/max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`, `light_germination`, `pretreatment`, `thousand_seed_weight_g`, `sowing_density_per_m2`) | ✓ | ✓ | teils (V listet, keine Range) | **Keine** Plausibilität, **keine** Cross-Field (`min<max`, Lichtkeimer→`sowing_depth≈0`) |

### Phasen, Nährstoffe
| Bereich | Beschaffung | Struktur | Semantik |
|---------|-------------|----------|----------|
| `requirement_profile.*` (15 Felder) | ✓ Generator (mit `KA-Feld`) | ✓ (offenes Profil) | Teilweise (Plausibilitätstabelle — **aber auf tote Felder gerichtet**, s. G3) |
| `phase_entry` Kernfelder (`display_name`, `duration_days`, `sequence_order`, `stress_tolerance`, `is_terminal`) | ⚠ Generator **ohne `KA-Feld`-Spalte** (G2) | ✓ Schema-Required | `duration_days`: Plausibilitäts-Range vorhanden; Sequenz-Lückenlosigkeit + Terminal-Eindeutigkeit: ✓ Converter/Validator |
| `nutrient_profile` (`npk_ratio`, `target_ec_ms`, `target_ph`) | ⚠ Generator **ohne `KA-Feld`-Spalte** (G2) | ✓ Schema-Range | EC/NPK/pH: Plausibilitäts-Range + EC↔Dünger-Cross-Check (Phase 3.3) |

### Cultivar, Botanical Family, IPM, Companion
| Bereich | Beschaffung | Validierung |
|---------|-------------|-------------|
| Cultivar `breeder`/`days_to_maturity`/`traits`/`seed_type`/`cycle_type` | ✓ Generator (CSV 8.2) — **ohne `KA-Feld`** (G2) | Struktur ✓ |
| Cultivar `typical_yield`/`flavor_profile`/`flower_color`/`fruit_color`/`resistance_to` | ✗ **nicht beschafft** (G1) | Struktur ✓ (optional), sonst — |
| Botanical Family `typical_nutrient_demand`/`frost_tolerance`/`typical_root_depth`/`typical_growth_forms`/`pollination_type`/`rotation_category` | ✗ **nicht beschafft** (Converter erwartet sie → `MISSING`) (G1) | Struktur ✓ (required) |
| Family `common_pests`/`common_diseases` | ✗ **nicht beschafft** (G1) | — |
| Pest (`pest_type`, `lifecycle_days`, `optimal_temp_*`, `detection_difficulty`) | teils Generator | Struktur ✓ **+ ✓ tiefe Fachprüfung `check-pest-data`** |
| Disease (`pathogen_type`, `symptoms`, `affected_parts`, `optimal_humidity_*`) | teils Generator | Struktur ✓ + teils `check-pest-data`; `pathogen_type` Oomycet-Check (PR #300) |
| Treatment (`treatment_type`, `active_ingredient`, `application_method`, `safety_interval_days`) | teils Generator | Struktur ✓; `safety_interval_days` Plausibilität + `check-pest-data` |
| Companion (`compatible`/`incompatible`/`species_a/b`/`score`/`reason`) | ✓ Generator | Struktur ✓ + **Bidirektionalitäts-Check** (Phase 3.3) |

---

## Gap-Katalog

### 🔴 G1 — Attribute ganz ohne Beschaffungsstrategie
Kein Agent-Template recherchiert diese; der Converter würde sie als `# MISSING` markieren oder sie fehlen ganz:
- **Cultivar-Qualitätsfelder:** `typical_yield`, `flavor_profile`, `flower_color`, `fruit_color`, `resistance_to` (die CSV-Sektion 8.2 des Generators kennt sie nicht).
- **Botanical-Family-Attribute:** `typical_nutrient_demand`, `frost_tolerance`, `typical_root_depth`, `typical_growth_forms`, `pollination_type`, `rotation_category`, `common_pests`, `common_diseases` — der Converter-`new_families`-Block **erwartet** sie (required), der Generator **liefert** sie nicht → Beschaffungs-/Contract-Bruch auf Familienebene.
- `allows_harvest` (Species) — nicht als Recherche-Feld geführt (nur ableitbar).

### 🔴 G3 — Semantische Validierung auf tote Feldnamen (residualer Drift aus B5)
Die Plausibilitätstabelle des Validators (Phase 3.2) prüft `temp_min_c`, `temp_max_c`, `humidity_min_percent`, `light_min_ppfd`, `ph_min`/`ph_max` — **diese Felder existieren im aktuellen Modell nicht** (korrekt: `temperature_day_c`, `humidity_day_percent`, `light_ppfd_target` auf `requirement_profile`). PR #300 hat nur Phase 1.1/2.1 korrigiert, **nicht** die Plausibilitätstabelle. Folge: der einzige generische Plausibilitäts-Check für Umweltparameter **greift ins Leere**.

### 🟠 G2 — Prozedurale Beschaffungs-Schwäche: fehlende `KA-Feld`-Anker
Generator-Tabellen für **Phasen-Kernfelder (2.1)**, **Nährstoffprofil (2.3)** und **Cultivar (8.2)** haben **keine `KA-Feld`-Spalte** (0 Tokens gemessen). Der Converter mappt primär über die `KA-Feld`-Spalte (Phase 2); für diese Bereiche muss er auf Header-Inferenz zurückfallen → fragilerer Beschaffung→Konvertierung-Contract.

### 🟠 G4 — Attribute mit NUR struktureller, ohne semantischer Validierung
Große Klasse — Schema-Range existiert teils, aber keine fachliche Plausibilität/Cross-Field:
`allelopathy_score`, `base_temp`, `salt_tolerance_ece_threshold_ds_m`, `salt_tolerance_slope_pct`, `effective_root_depth_cm`, `light_compensation_point_ppfd_min/max`, alle Container-Maße, alle `seed_profile.*`-Werte, `critical_day_length_hours`, `vernalization_min_days`, `photosynthesis_type`/`shade_tolerance`/`waterlogging_tolerance` (Enum-strukturell, keine Art-Plausibilität).

### 🟠 G5 — Fehlende Cross-Field-Konsistenzregeln
Der Validator (Phase 3.3) prüft Phasendauer-Summe, Companion-Bidirektionalität und EC↔Dünger — aber **nicht**:
- `germination_temp_min_c < germination_temp_max_c`
- `salt_tolerance_class` ↔ `salt_tolerance_ece_threshold_ds_m` (S/MS/MT/T-Schwellen konsistent?)
- `light_germination = light` ⇒ `sowing_depth_cm ≈ 0` (Lichtkeimer nicht bedecken)
- `harvested_part`/`harvest_pattern`/`climacteric` Konsistenz (z.B. `climacteric` nur sinnvoll bei `harvested_part = fruit`)
- `seed_profile` gesetzt ⇒ `propagation_configs` enthält `seed`

### 🟡 G6 — Ungleiche fachliche Validierungs-Tiefe
IPM (Pest/Disease/Treatment) hat mit **`check-pest-data`** die mit Abstand tiefste fachliche Validierung (8 Dimensionen, Indoor/Outdoor-Matrix). Für **Species-Physiologie und Saatgut** existiert **kein analoger fachlicher Skill/Agent** — nur die generische (und derzeit tote, G3) Plausibilitätstabelle. Die neuen `seed_profile`-Attribute (PR #300) haben damit **Beschaffung ohne fachliche Validierung**.

---

## Empfehlungen (priorisiert)

1. **(G3, schnell)** Validator-Plausibilitätstabelle (Phase 3.2) auf aktuelle Feldnamen umschreiben (`requirement_profile.temperature_day_c`, `humidity_day_percent`, `light_ppfd_target`, `soil_ph_preference.min_ph/max_ph`) — sonst ist der einzige generische Umwelt-Plausibilitätscheck wirkungslos.
2. **(G2)** `KA-Feld`-Spalten in die Generator-Tabellen für Phasen (2.1), Nährstoffe (2.3) und Cultivar (8.2) aufnehmen → maschinenlesbarer Mapping-Anker für den Converter.
3. **(G1)** Cultivar-Qualitätsfelder + Botanical-Family-Attribute in das Generator-Template aufnehmen (Family-Recherche-Sektion), damit der `new_families`-Contract des Converters erfüllbar wird.
4. **(G6/G7)** Für die neuen `seed_profile`-Attribute eine Validierungsstrategie ergänzen: entweder Plausibilitätsbereiche in Validator Phase 3.2 (Keimtemperatur 2–40 °C, Saattiefe 0–10 cm, Viabilität 1–20 J, TKM > 0) **oder** — analog zu `check-pest-data` — einen fachlichen `check-seed-data`-Skill.
5. **(G5)** Cross-Field-Konsistenzregeln in Validator Phase 3.3 ergänzen (siehe Liste oben).

---

## Fazit

- **Beschaffung:** Für Species (inkl. Physiologie/Saatgut) nach PR #300 **nahezu vollständig**; klare Lücken bei **Cultivar-Qualitätsfeldern** und **Botanical-Family-Attributen** (G1) sowie ein fragiler Mapping-Contract für Phasen/Nährstoffe/Cultivar (G2).
- **Strukturelle Validierung:** Durch Schema + Pydantic **nahezu vollständig** — jedes schema-definierte Feld ist strukturell abgedeckt.
- **Semantische/fachliche Validierung:** **Die eigentliche Lücke.** Nur IPM (via `check-pest-data`) und Phasen-Monate (via `growing-phase-auditor`) sind fachlich tief validiert. Der generische Plausibilitäts-Check läuft aktuell auf tote Felder (G3), und Physiologie/Saatgut/viele Zahlwerte haben **keine** semantische Prüfung (G4/G5/G6).

**Kurzantwort auf die Ausgangsfrage:** Eine **Beschaffungs**strategie existiert für fast jedes Attribut (Ausnahmen: G1). Eine **strukturelle Validierung** existiert für praktisch jedes schema-definierte Attribut. Eine **fachlich-semantische Validierung** existiert **nur für eine Minderheit** der Attribute — und ist für Umweltparameter derzeit durch einen Feldnamen-Drift funktionslos.
