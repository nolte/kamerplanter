# Wachsblume — Hoya carnosa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NCSU Plant Toolbox](https://plants.ces.ncsu.edu/plants/hoya-carnosa/), [Gardenia.net](https://www.gardenia.net/plant/hoya-carnosa-wax-plant-all-you-need-to-know), [Planet Natural](https://www.planetnatural.com/hoya-carnosa/), [Epic Gardening](https://www.epicgardening.com/hoya-plant/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/hoya-carnosa-a-comprehensive-guide/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hoya carnosa | `species.scientific_name` |
| Volksnamen (DE/EN) | Wachsblume, Porzellanblume; Wax Plant, Honey Plant, Porcelain Flower | `species.common_names` |
| Familie | Apocynaceae | `species.family` → `botanical_families.name` |
| Gattung | Hoya | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–40+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–24°C. Kurze Kühle im Winter (12–15°C nachts) kann Blütenbildung fördern. | `species.hardiness_detail` |
| Heimat | Ostasien (China, Indien, Australien — tropische Regenwälder, epiphytisch) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, fragrant | `species.traits` |

**Hinweis:** Hoya carnosa ist für ihr zartes, schokoladig-vanilleartiges Duft bekannt (besonders nachts). Die sternförmigen Blüten hängen in kugelig-runden Blütendolden (Umbellen). Wichtig: Alte Blütenstiele (Pedunclen) NIEMALS entfernen — sie sind mehrjährig und bilden jede Saison neue Knospen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 (bei reifen Pflanzen ab ca. 3–5 Jahren) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–3 Blättern und mindestens einem Knoten. In Wasser (4–6 Wochen) oder direkt in leichtem Substrat bewurzeln. Luftschichtung (Air Layering) bei dicken Trieben möglich. Wichtig: Kein Blütenstiel als Steckling verwenden!

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Hoya carnosa gilt als haustierfreundlich. Der milchige Saft kann bei manchen Menschen leichte Hautirritation verursachen, ist aber nicht klassifiziert toxisch. Ideal für Haushalte mit Tieren und Kindern.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (nach Winterruhe, vor neuem Austrieb) | `species.pruning_months` |

**Wichtig:** Blütenstiele (Pedunclen) NICHT abschneiden — sie blühen jedes Jahr erneut an derselben Stelle. Nur Wildtriebe und zu lange Ranken kürzen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (als Kletterpflanze) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, windgeschützt, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Rankgitter, Moosstab oder Bogen — Pflanze rankt sehr gerne) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr durchlässiges Substrat: Orchideenrinde + Perlite + etwas Kakteenerde (1:1:1). pH 6.0–7.0. Staunässe führt schnell zu Wurzelfäule. Kleiner Topf fördert Blüte (pot-bound). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Blüte | 60–120 | 2 | false | false | low |
| Winterruhe | 120–150 | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Gießintervall (Tage) | 21–35 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:1:1 | 0.6–1.0 | 6.0–7.0 | 60 | 25 |
| Blüte | 1:2:1 (P-betont) | 0.4–0.8 | 6.0–7.0 | 50 | 20 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L | Wachstum |
| Blühpflanzen-Dünger | Compo | bloom | 5-8-10 | 3 ml/L | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Für Blüteninduktion: im Winter Bewässerung stark reduzieren (1x/3 Wochen) und kühle Temperaturen (12–15°C nachts). Kein Dünger Okt–Feb. Ab März wieder Wachstumsdünger. Zu viel N fördert Blattmasse statt Blüten. Kleine Töpfe und "pot-bound"-Bedingungen fördern Blüte!

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; abgestandenes Wasser bevorzugt; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (Hoya blüht besser in engem Topf!) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken, Honigtau | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blattvergilbung (bei trockener Luft) | medium |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Stängeln | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, faulende Wurzeln | Überbewässerung, Staunässe |
| Botrytis | fungal | Grauer Schimmel auf Blüten | Hohe Luftfeuchte, schlechte Zirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (Blüten meiden!) | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse, Schildlaus |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Hoya kerrii | Hoya kerrii | Gleiche Gattung | Herzförmige Blätter; populär als Valentinstagspflanze |
| Hoya bella | Hoya bella | Gleiche Gattung | Kleinblättriger, kompakter; zierliche Blüten |
| Hoya pubicalyx | Hoya pubicalyx | Gleiche Gattung | Schneller wachsend, leichter zu blühen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Hoya carnosa,"Wachsblume;Porzellanblume;Wax Plant;Honey Plant",Apocynaceae,Hoya,perennial,day_neutral,vine,fibrous,"9a;9b;10a;10b;11a;11b","Ostasien (epiphytisch)",yes,2-8,15,60-200,40-100,yes,limited,false,true,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Tricolor,Hoya carnosa,"ornamental;variegated;pink_cream_green",clone
Krimson Queen,Hoya carnosa,"ornamental;variegated;cream_edge",clone
Krimson Princess,Hoya carnosa,"ornamental;variegated;cream_center",clone
Compacta,Hoya carnosa,"ornamental;curled_leaves;compact",clone
```

---

## Quellenverzeichnis

1. [NCSU Extension — Hoya carnosa](https://plants.ces.ncsu.edu/plants/hoya-carnosa/) — Botanische Einordnung
2. [Gardenia.net — Wax Plant](https://www.gardenia.net/plant/hoya-carnosa-wax-plant-all-you-need-to-know) — Kulturdaten
3. [Planet Natural](https://www.planetnatural.com/hoya-carnosa/) — Pflegehinweise
4. [Epic Gardening — Hoya Plant](https://www.epicgardening.com/hoya-plant/) — Sorten, Blüteninduktion
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/hoya-carnosa-a-comprehensive-guide/) — Ganzjahrespflege
