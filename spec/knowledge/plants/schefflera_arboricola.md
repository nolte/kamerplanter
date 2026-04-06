# Zwergschefflera — Schefflera arboricola

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Bloomscape](https://bloomscape.com/plant-care-guide/schefflera/), [Almanac.com](https://www.almanac.com/plant/umbrella-plant-care-guide-schefflera), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/umbrella-plant-schefflera-arboricola-care-guide/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-a-schefflera), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Schefflera arboricola | `species.scientific_name` |
| Volksnamen (DE/EN) | Zwergschefflera, Strahlenaralie; Dwarf Umbrella Tree, Umbrella Plant | `species.common_names` |
| Familie | Araliaceae | `species.family` → `botanical_families.name` |
| Gattung | Schefflera | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 12°C, optimal 18–27°C. Toleriert kurze Abkühlungen auf 10°C. | `species.hardiness_detail` |
| Heimat | Taiwan und Hainan (Südchina) — tropische und subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Schefflera arboricola (Zwergform) und S. actinophylla (große Form, "Sonnenschirm-Pflanze") werden oft verwechselt. Beide sind als Zimmerpflanzen beliebt, aber arboricola bleibt kompakter (bis 2 m Indoor). Sehr tolerant gegenüber schwächerem Licht, was sie für dunklere Zimmerecken qualifiziert. Kann als Bonsai kultiviert werden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Halbholzige Stecklinge (8–12 cm) bei 22–26°C und hoher Luftfeuchtigkeit bewurzeln. Bewurzelung in 4–8 Wochen. Abmoosen (Luftabsenker) ist zuverlässiger für Stämme.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, berries | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides, saponins | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Saft — bei empfindlichen Personen Hautreizungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Verträgt starken Rückschnitt gut — treibt zuverlässig neu aus. Im Frühjahr auf gewünschte Form bringen. Regelmäßiges Pinzen der Triebspitzen fördert buschigen Wuchs.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–200 (Indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–120 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (frostfreie Monate, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Einheitserde mit 20% Perlite. pH 6.0–6.5. Gute Drainage wichtig. Tongefäße bevorzugt (verhindert Überwässerung). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–350 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–6.5 | 100 | 40 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Hornmehl | – | organisch | 30–50 g/Topf | Frühjahr |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Stickstoffbetonte Formel für üppiges Blattwerk. Bei wenig Licht: Düngermenge auf 1/4 reduzieren.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; gleichmäßige Feuchtigkeit, keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |
| Blattlaus | Aphididae | Kolonien an Triebspitzen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, Blattverlust | Staunässe |
| Alternaria-Blattflecken | fungal | Braune Flecken | Nasses Laub, hohe Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Sprühen | 3 Tage | Blattläuse, Schildläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Große Schefflera | Schefflera actinophylla | Gleiche Gattung | Eindrucksvolleres Erscheinungsbild |
| Fatsia | Fatsia japonica | Gleiche Familie | Frostharder, für kühlere Räume |
| Monstera | Monstera deliciosa | Großblättrig, tropisch | Spektakulärer, ähnlich pflegeleicht |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Schefflera arboricola,"Zwergschefflera;Strahlenaralie;Dwarf Umbrella Tree;Umbrella Plant",Araliaceae,Schefflera,perennial,day_neutral,shrub,fibrous,"9b;10a;10b;11a;11b","Taiwan, Hainan (Südchina)",yes,5-20,25,80-200,60-120,yes,yes,false,medium_feeder,0.6
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Gold Capella,Schefflera arboricola,"ornamental;variegated;yellow_green",clone
Trinette,Schefflera arboricola,"ornamental;variegated;cream_green",clone
Renate,Schefflera arboricola,"ornamental;compact;dark_green",clone
```

---

## Quellenverzeichnis

1. [Bloomscape — Schefflera Care](https://bloomscape.com/plant-care-guide/schefflera/) — Pflegehinweise
2. [Almanac.com — Umbrella Plant](https://www.almanac.com/plant/umbrella-plant-care-guide-schefflera) — Kulturdaten
3. [Healthy Houseplants — Schefflera arboricola](https://www.healthyhouseplants.com/indoor-houseplants/umbrella-plant-schefflera-arboricola-care-guide/) — Schädlinge, Krankheiten
4. [The Sill — Schefflera](https://www.thesill.com/blogs/plants-101/how-to-care-for-a-schefflera) — Gießen, Licht
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
