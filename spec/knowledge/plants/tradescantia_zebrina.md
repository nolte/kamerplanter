# Dreimasterblume, Silbrige Tradescantie — Tradescantia zebrina

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Ohio Tropics](https://www.ohiotropics.com/2021/04/17/tradescantia-zebrina-care/), [Bloomscape](https://bloomscape.com/plant-care-guide/tradescantia/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-a-tradescantia), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/silver-inch-plant-tradescantia-zebrina-care-guide-wandering-jew/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tradescantia zebrina | `species.scientific_name` |
| Volksnamen (DE/EN) | Dreimasterblume, Silbrige Tradescantie, Wandernder Jude; Wandering Dude, Silver Inch Plant, Spiderwort | `species.common_names` |
| Familie | Commelinaceae | `species.family` → `botanical_families.name` |
| Gattung | Tradescantia | `species.genus` |
| Ordnung | Commelinales | `botanical_families.order` |
| Wuchsform | groundcover | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 3–10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 7°C, optimal 15–27°C. Verträgt kurze Kühle bis 5°C ohne Dauerschäden. | `species.hardiness_detail` |
| Heimat | Mexiko, Guatemala und Mittelamerika — tropische/subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 4, 5, 6, 7, 8 (kleine violette Blüten; häufig bei hellem Standort) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–4 Knoten in Wasser (1–2 Wochen) oder direkt in feuchtem Substrat. Extrem hohe Erfolgsrate. Gehört zu den einfachsten Zimmerpflanzen überhaupt zu vermehren.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | unknown_sap_compounds (Saft enthält reizende Kristalle) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Saft verursacht Kontaktdermatitis bei empfindlichen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Regelmäßiges Rückschneiden (mehrfach pro Jahr!) verhindert "leggy" Wuchs und fördert dichte, farbintensive Triebe. Hintere/kahle Triebe auf 5–10 cm zurückschneiden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 (hängend bis 60) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Einheitserde mit 20% Perlite. pH 6.0–7.0. Sehr anpassungsfähig. Ampelkultivierung beliebt. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 4–12 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen April bis September. Kein Dünger Oktober bis März. Überdüngung → gelbliche, statt violett-silberne Blätter (Farbverlust!). Helles Licht für intensive Blattfarben wichtiger als Düngung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; regelmäßig gießen, nicht austrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Farbverlust der Blätter | medium |
| Blattlaus | Aphididae | Kolonien, Honigtau | easy |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, fahle Blätter | Staunässe |
| Botrytis | fungal | Grauer Schimmel | Schlechte Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Blattläuse |
| Nematoden | biological | Gießen (Steinernema feltiae) | 0 Tage | Trauermücke |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Fluminensis | Tradescantia fluminensis | Gleiche Gattung | Grün-weißes Laub, noch pflegeleichter |
| Purpurea | Tradescantia pallida | Gleiche Gattung | Kräftig lila Blätter |
| Nanouk | Tradescantia albiflora 'Nanouk' | Gleiche Gattung | Pink-weiße Farben, kompakter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Tradescantia zebrina,"Dreimasterblume;Silbrige Tradescantie;Wandering Dude;Silver Inch Plant",Commelinaceae,Tradescantia,perennial,day_neutral,groundcover,fibrous,"9a;9b;10a;10b;11a;11b","Mexiko, Guatemala, Mittelamerika",yes,1-5,12,15-60,40-100,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Ohio Tropics — Tradescantia zebrina](https://www.ohiotropics.com/2021/04/17/tradescantia-zebrina-care/) — Pflegehinweise
2. [Bloomscape — Tradescantia Care](https://bloomscape.com/plant-care-guide/tradescantia/) — Allgemeine Pflege
3. [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-a-tradescantia) — Praxiswissen
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/silver-inch-plant-tradescantia-zebrina-care-guide-wandering-jew/) — Ganzjahrespflege
