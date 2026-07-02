# Review: Seed-Informations-Pipeline (3 Agenten)

**Erstellt von:** Agent-Review (Claude Code)
**Datum:** 2026-07-02
**Geprüfte Agenten:** `plant-info-document-generator` → `plant-info-to-seed-yaml` → `seed-data-validator`
**Autoritative Spec:** `src/backend/app/migrations/seed_data/schemas/plant_info.schema.yaml`, `species.schema.yaml`, `_defs.schema.yaml`
**Evidenzbasis:** 9× `plant_info_*.yaml`, `species.yaml` (Feld-Zählungen via Grep, Stand 2026-07-02)
**Externe Verifikation:** Multi-Source-Websuche (der Deep-Research-Harness brach in der Scope-Phase infrastrukturbedingt ab — StructuredOutput-Retry-Cap; die 6 Prüffragen wurden daher direkt gegen unabhängige Quellen verifiziert, siehe Abschnitt „Externe Verifikation")

---

## Gesamturteil

Die Pipeline ist **konzeptionell solide** (klare Rollentrennung Author/Author/Reviewer, „keine-Halluzination"-Regel, 3-Quellen-Verifikation, konfigurierbare `mixing_priority`), deckt die Anforderungen aus der Spec aber **nicht vollständig** ab. Es bestehen drei systemische Lücken:

1. **Zweiseitige Coverage-Lücke** zwischen den Agent-Templates und den Schemas (Schema-Felder fehlen in Templates; Template-Felder fehlen im Schema).
2. **Schema-vs-Daten-Drift**: die realen Seed-Daten nutzen Felder, die kein Schema validiert.
3. **Fehlende echte Saatgut-Attribute** — für etwas namens „Seed-Informationen" existiert keine Aussaat-/Keim-Metadatenschicht.

Zusätzlich ein extern belegter **Fachfehler** in einem Generator-Beispiel (Pathogen-Klassifikation).

| Schwere | Befunde |
|---------|---------|
| 🔴 Kritisch | B1 (Schema-Felder fehlen in Templates), B2 (Daten-Felder ohne Schema), B7 (keine Saatgut-Attribute), B8 (Pathogen falsch klassifiziert) |
| 🟠 Wichtig | B3 (Enum-Drift Generator), B4 (Converter-Template reduziert), B5 (Validator-Vokabular veraltet), B6 (`requirement_profile`-Schema-Inkonsistenz) |

---

## Befunde

### 🔴 B1 — Schema-definierte, real genutzte Felder fehlen in den Agent-Templates

Felder sind im Schema definiert **und** in den Daten massiv im Einsatz, werden aber von Generator- und/oder Converter-Template nicht erzeugt:

| Feld | Vorkommen (Daten) | Generator-Template | Converter-Template | Spec |
|------|------------------:|:---:|:---:|---|
| `plant_category` | 208 | ❌ | ❌ | species.schema, plant_info.schema |
| `propagation_configs` (strukturiert) | 207 | ❌ (nur deprecated `propagation_methods`) | ❌ (kein Propagations-Block) | REQ-017 |
| `base_temp` (GDD) | 97 | ❌ | ❌ | species.schema |
| `harvest_pattern` | 78 | ❌ | ❌ | REQ-007 |
| `harvested_part` | 78 | ❌ | ❌ | REQ-007 |
| `climacteric` | 21 | ❌ | ❌ | REQ-007 |

**Beleg-Detail:** `propagation_methods` (die einzige vom Generator dokumentierte Form) hat **0** Treffer in den Daten; `propagation_configs` hat 207. Die dokumentierten Output-Contracts der Agenten sind damit hinter dem realen Ziel-Schema zurück.

### 🔴 B2 — Agenten/Daten erzeugen Felder, die kein Schema validiert

Umgekehrt produzieren Generator/Daten Felder, die in keinem Schema als `properties` definiert sind (nur via `additionalProperties: true` geduldet), während das jeweilige Schema-Pendant faktisch tot ist:

| Feld in Daten | Vorkommen | Schema-Pendant | Pendant genutzt |
|---|---:|---|---:|
| `pruning_type` / `pruning_months` | 72 / 66 | `pruning` (Objekt: `pruning_required`/`_season`/`_notes`) | **1×** |
| `green_manure_suitable` | 83 | `green_manure` (bool) | **0×** |
| `toxicity.is_toxic_*` + `toxicity_severity` | 15 / 16 | — (nirgends definiert) | — |

Toxizität existiert in **drei** widersprüchlichen Konventionen: Generator (`toxicity.is_toxic_cats`), Validator-Checkliste (`toxicity_cat`/`toxicity_human`), Schema (gar nicht). Die 3-Quellen-Regel schützt die Datenqualität nicht, wenn das Feld anschließend unvalidiert im YAML landet.

### 🟠 B3 — Enum-Drift im Generator-Template

- **`growth_habit`:** Template listet 5 Werte (`herb/shrub/tree/vine/groundcover`); die Daten nutzen **alle 12** (`subshrub`, `grass`, `succulent`, `bulb_geophyte`, `fern`, `aquatic`, `epiphyte` zusätzlich). Ein template-treuer Generator könnte diese Arten nicht einordnen.
- **`root_type`:** Template listet `rhizomatous`/`aerial` — **beide nicht** im Schema-Enum `[fibrous, taproot, tuberous, bulbous, corm]`. Latent (bisher keine Daten), aber ein Bug, sobald z.B. Ingwer/Bambus erzeugt wird; der Converter hat keine Mapping-Regel dafür.
- **`frost_sensitivity`:** Template sagt `tender`/`half_hardy` (nicht im Schema); nur durch die Converter-Mapping-Tabelle gerettet. Generator-Alleinlauf ⇒ ungültige Enums.

### 🟠 B4 — Converter-Template ist eine reduzierte Teilmenge

Der `new_species`- und der `requirement_profile`-Block im Converter listen nur ~22 bzw. 8 Felder und lassen die Physiologie-Sektion komplett weg: `photosynthesis_type` (201×), `salt_tolerance_class` (173×), `shade_tolerance` (203×), `effective_root_depth_cm` (129×), `soil_ph_preference` (255×), LCP-min/max. Ein Haiku-Modell, das dem Template wörtlich folgt, **verwirft vom Generator recherchierte Daten**. Phase 2 („extrahiere ALLE Zeilen") widerspricht dem Template.

### 🟠 B5 — Validator prüft gegen ein veraltetes Feld-Vokabular

`seed-data-validator` Phase 1.1/2.1 referenziert `common_name_de/en`, `family_key`, `plant_type`, `phase_type`, `light_min_ppfd`, `temp_min_c`, `toxicity_human`, `frost_sensitivity: NONE/LOW/MEDIUM/HIGH` — das entspricht **weder** dem `plant_info`- **noch** dem `species`-Seed-Schema (`common_names`-Array, Family-Map, `plant_category`/`cycle_type`, `requirement_profile.*`, `frost_sensitivity: sensitive/moderate/hardy/very_hardy`). Der Validator prüft damit die falschen Feldnamen. Ironisch: Seine eigene Phase 0.2 (`[SCHEMA-FIELD-MISSING]`) sollte die B2-Drifts fangen — die Checkliste ist aber selbst Teil des Problems.

### 🟠 B6 — Schema-Inkonsistenz `requirement_profile`

`species.schema.yaml` (`default_phase.requirement_profile`) verlangt strikt `vpd_range` (Array) mit `additionalProperties: false`; die Daten nutzen **300×** `vpd_target_kpa` (nur 5× `vpd_range`). Weil `plant_info`-Phasen ein offenes Profil haben, fällt das nicht auf — die beiden Phasen-Modelle divergieren dennoch.

### 🔴 B7 — Kein einziges echtes Saatgut-Attribut

Für ein „Seed-Informations"-Modell fehlen **alle** Standard-Saatgut-Metadaten (0 Treffer im gesamten Modell): Keimtemperatur, Saattiefe, Tage-bis-Keimung, Keimfähigkeitsdauer/Viabilität, Licht-/Dunkelkeimer, Stratifikation/Skarifikation, Tausendkornmasse, Aussaatdichte. `germination` existiert nur als Phasen-Name. Das Modell ist rein kulturzentriert; die Aussaat-Vorbereitung ist nicht abbildbar.

### 🔴 B8 — Fachlich falsche Pathogen-Klassifikation im Generator-Beispiel (extern belegt)

Das Generator-Template führt „Kraut- und Braunfäule" (Phytophthora infestans) unter Erregertyp `fungal`. Extern verifiziert: Phytophthora ist ein **Oomycet** (Oomycota, Reich Stramenopila, Zellulose-Zellwand), **kein** echter Pilz. Das `disease`-Schema hat den korrekten Enum-Wert `oomycete`. Gleiches gilt für Falschen Mehltau und Pythium. Das Beispiel lehrt eine falsche Einordnung.

---

## Externe Verifikation

| # | Prüfannahme | Ergebnis | Quellen |
|---|---|---|---|
| 1 | Taxonomie-Autoritäten GBIF/WFO/IPNI maßgeblich | ✅ **POWO/WCVP** ist der geteilte Konsens-Backbone (GBIF, CoL, WFO); IPNI = nomenklatorischer Unterbau | Kew POWO/WCVP |
| 2 | Phytophthora = Oomycet, nicht „fungal" | ✅ Bestätigt (Stramenopila, kein Pilz); gilt auch für Falschen Mehltau & Pythium | APSnet, Wikipedia |
| 3 | `climacteric`-Enum etabliert | ✅ Tomate/Apfel/Banane klimakterisch; Erdbeere/Traube/Zitrus/Paprika nicht-klimakterisch | PostHarvest, Wikipedia |
| 4 | Maas-Hoffman + S/MS/MT/T Standard | ✅ Agronomisches Standardmodell (Schwelle+Steigung), FAO-Referenz | Maas-Hoffman (Wikipedia), FAO |
| 5 | Mischreihenfolge „CalMag vor Sulfaten" | ⚠️ Silikat-zuerst & Ca/Sulfat-Trennung korrekt; CalMag-**vor**-Base nur bei RO-Wasser Konsens, sonst umstritten | Toledo Indoor Garden, Hydrobuilder |
| 6 | Fehlende Saatgut-Attribute sind Standard | ✅ Keimtemperatur, Saattiefe, Licht-/Dunkelkeimung, Stratifikation sind etablierte, dokumentierte Parameter | NCBI/PMC-Studien; horticultural consensus |

**Quellen:**
- [APSnet: Why are Phytophthora and other Oomycota not true Fungi?](https://www.apsnet.org/edcenter/Pages/Oomycetes.aspx)
- [Wikipedia: Phytophthora infestans](https://en.wikipedia.org/wiki/Phytophthora_infestans)
- [Wikipedia: Climacteric (botany)](https://en.wikipedia.org/wiki/Climacteric_(botany))
- [PostHarvest: climacteric vs non-climacteric](https://www.postharvest.com/blog/what-are-climacteric-and-non-climacteric-fresh-produce/)
- [Wikipedia: Maas–Hoffman model](https://en.wikipedia.org/wiki/Maas%E2%80%93Hoffman_model)
- [FAO: Crop salt tolerance data](https://www.fao.org/4/y4263e/y4263e0e.htm)
- [Kew: About WCVP / POWO](https://powo.science.kew.org/about-wcvp)
- [Toledo Indoor Garden: Nutrient Mixing Order](https://toledoindoorgarden.com/mixing-guide)
- [Hydrobuilder: mixing plant nutrients & lockout](https://hydrobuilder.com/learn/mixing-plant-nutrients/)

---

## Umsetzungsplan

Ziel: die Befunde **konsequent** und in einer Reihenfolge einarbeiten, die Rückschritte vermeidet. Leitprinzip: **erst das Schema als Wahrheit festlegen (Schema-vs-Daten-Drift auflösen), dann Generator + Converter darauf synchronisieren, dann den Validator als Guard scharf stellen.** So verhindert am Ende die Maschine (Schema + Validator), dass die Drifts wiederkehren.

Jede Phase ist eigenständig als PR umsetzbar (`feat/…`-Branch von `develop`, per Projekt-Konvention).

### Phase 0 — Entscheidungen fixieren (kein Code)

Blockiert alle folgenden Phasen. Pro Drift-Feld genau eine Richtung wählen:

| Entscheidung | Optionen | Empfehlung |
|---|---|---|
| `pruning` | (a) Schema auf `pruning_type`/`pruning_months` umstellen · (b) Daten auf `pruning`-Objekt migrieren | **(a)** — Daten (72×/66×) sind die De-facto-Wahrheit; `pruning`-Objekt ist quasi tot (1×) |
| `green_manure` | (a) Schema-Feld → `green_manure_suitable` · (b) Daten umbenennen | **(a)** — 83× vs. 0× |
| `toxicity` | ein kanonisches Sub-Schema definieren (`toxicity.is_toxic_cats/dogs/children`, `toxic_parts`, `toxic_compounds`, `severity`) | Generator-Konvention als Kanon; Validator-Checkliste anpassen |
| `requirement_profile` VPD | `vpd_target_kpa` (300×) als Kanon; `vpd_range` als optionale Ableitung | `vpd_target_kpa` |
| Saatgut-Schicht | neues `seed_profile`-Sub-Objekt an `species` | umsetzen (B7) |

Deliverable: kurzer Entscheidungs-Append in diesem Report oder ein ADR unter `spec/` (falls Struktur vorhanden).

### Phase 1 — Schema als Wahrheit (löst B2, B6, B7)

Datei: `src/backend/app/migrations/seed_data/schemas/{plant_info,species,_defs}.schema.yaml` — **rein additiv**, keine Removals (Validator-Invariante).

1. **B2:** real genutzte Felder als `properties` aufnehmen: `pruning_type` (Enum), `pruning_months` (Array 1–12), `green_manure_suitable` (bool), `toxicity` (Sub-Objekt, siehe Phase 0), `toxicity_severity`. Die toten Pendants (`pruning`-Objekt, `green_manure`) als `deprecated` markieren (nicht entfernen).
2. **B6:** `vpd_target_kpa` (+ `vpd_threshold_kpa`, `vpd_sensitivity`) offiziell in `requirement_profile` aufnehmen; `vpd_range` als optional behalten.
3. **B7:** neues `seed_profile`-Sub-Objekt an `species`: `germination_temp_min_c`/`_max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`, `light_germination` (Enum `light/dark/indifferent`), `pretreatment` (Array: `cold_stratification/warm_stratification/scarification/presoak`), `thousand_seed_weight_g`, `sowing_density_per_m2`. Alle nullable.
4. Pydantic-Modelle in `src/backend/app/domain/models/` spiegeln (Import-Layer + DB-Layer).
5. **Verifikation:** `python -c "import yaml; yaml.safe_load(...)"` je Schema; bestehende Seed-YAMLs müssen weiter validieren.

### Phase 2 — Generator synchronisieren (löst B1, B3, B8)

Datei: `.claude/agents/plant-info-document-generator.md`

1. **B1:** Template-Tabellen um `plant_category`, `base_temp`, `harvest_pattern`, `harvested_part`, `climacteric` erweitern; Propagations-Sektion (1.3) auf **strukturiertes** `propagation_configs` umstellen (Methode + `months` + `wood_stage` + `difficulty` + `notes`) statt Flat-Liste.
2. **B3:** Enum-Listen im Template vervollständigen: `growth_habit` alle 12 Werte, `root_type` ohne `rhizomatous`/`aerial` (bzw. Mapping-Regel ergänzen), `frost_sensitivity` direkt auf `sensitive/moderate/hardy/very_hardy`.
3. **B7:** Steckbrief-Vorlage um Sektion „Saatgut/Keimung" (die `seed_profile`-Felder) erweitern; Recherche-Phase 2 um Keim-Parameter ergänzen; Quellen ISTA/RHS/Extension aufnehmen.
4. **B8:** IPM-Beispiel korrigieren — „Kraut-/Braunfäule" → `oomycete`; Hinweis ergänzen, dass Phytophthora/Falscher Mehltau/Pythium Oomyceten sind.
5. Optional (Verifikation #1): POWO/WCVP zur Quellen-Hierarchie ergänzen.

### Phase 3 — Converter synchronisieren (löst B1, B4)

Datei: `.claude/agents/plant-info-to-seed-yaml.md`

1. **B4:** `new_species`-Template um die vollständige Physiologie-Sektion (`photosynthesis_type`, `shade_tolerance`, `effective_root_depth_cm`, `waterlogging_tolerance`, `salt_tolerance_*`, `soil_ph_preference`, LCP) + `plant_category` + `base_temp` erweitern; `requirement_profile`-Template um die vollen Felder (`dli_target_mol`, `vpd_threshold_kpa`, `vpd_sensitivity`, `far_red_fraction`, `irrigation_*`) ergänzen.
2. **B1:** Propagations-Block ergänzen (`propagation_configs`); `harvest_pattern`/`harvested_part`/`climacteric` aufnehmen; `seed_profile`-Mapping ergänzen.
3. Enum-Mapping-Tabelle um die neuen Felder ergänzen; Widerspruch „Template vs. Phase-2-`extrahiere ALLE`" beseitigen (Template als vollständige Referenz, nicht als Teilmenge).

### Phase 4 — Validator scharf stellen (löst B5, sichert B1/B2 dauerhaft)

Datei: `.claude/agents/seed-data-validator.md`

1. **B5:** Phase-1.1/2.1-Checklisten auf das aktuelle Seed-Vokabular umschreiben (`common_names`, Family-Map, `plant_category`/`cycle_type`, `requirement_profile.*`, korrekte `frost_sensitivity`-Enums, kanonische `toxicity`-Felder).
2. Phase 0.2 (`[SCHEMA-FIELD-MISSING]`/`[SCHEMA-ENUM-MISSING]`) als **verpflichtenden Gate** betonen, sodass künftige Template-/Daten-Drifts automatisch auffallen.
3. IPM-Plausibilitätscheck um Pathogen-Typ-Verifikation (Oomycet vs. Pilz) ergänzen.

### Phase 5 — Daten-Backfill & Verifikation (optional, datengetrieben)

1. Bestehende `plant_info_*.yaml` mit den neuen `seed_profile`-Feldern nachziehen (per Batch über den Generator→Converter-Lauf, priorisiert nach häufigen Arten).
2. `seed-data-validator` über den Gesamtbestand laufen lassen → `spec/analysis/seed-data-validation-report.md` sollte 0 `[SCHEMA-FIELD-MISSING]` melden.
3. Backend-Tests (`pytest`) für den Seed-Import grün; ggf. `unit-test-runner`.

### Reihenfolge & Abhängigkeiten

```
Phase 0 (Entscheidungen)
   └─> Phase 1 (Schema)  ──┬─> Phase 2 (Generator)
                           ├─> Phase 3 (Converter)
                           └─> Phase 4 (Validator)
                                      └─> Phase 5 (Backfill + Gesamt-Verifikation)
```

Phase 2–4 können nach Phase 1 parallel laufen (drei separate PRs). Phase 5 erst danach.

### Abnahmekriterien (Definition of Done)

- [ ] Jedes in den Daten genutzte Feld ist als Schema-`property` definiert (kein reines `additionalProperties`-Feld mehr für Kern-Attribute).
- [ ] Generator- und Converter-Template enthalten jedes required/häufige Schema-Feld inkl. vollständiger Enum-Listen.
- [ ] `seed_profile`-Schicht existiert und ist in beiden Templates dokumentiert.
- [ ] Generator-IPM-Beispiel nutzt `oomycete` korrekt.
- [ ] Validator-Checklisten referenzieren ausschließlich aktuelle Feldnamen; Phase-0-Drift-Gate aktiv.
- [ ] `seed-data-validator`-Gesamtlauf: 0 strukturelle Fehler, 0 `[SCHEMA-FIELD-MISSING]`.
- [ ] Backend-Seed-Import-Tests grün.

---

## Traceability

| Befund | Betroffene Dateien | Behoben in Phase |
|--------|--------------------|------------------|
| B1 | Generator- + Converter-Template | 2, 3 |
| B2 | `plant_info`/`species`/`_defs`.schema.yaml, Pydantic-Modelle | 0, 1 |
| B3 | Generator-Template | 2 |
| B4 | Converter-Template | 3 |
| B5 | `seed-data-validator.md` | 4 |
| B6 | `species.schema.yaml`, `plant_info.schema.yaml` | 1 |
| B7 | Schema + beide Templates + Daten | 1, 2, 3, 5 |
| B8 | Generator-Template | 2 |
