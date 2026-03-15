# Croton, Wunderstrauch — Codiaeum variegatum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/codiaeum-variegatum/), [Gardenia.net](https://www.gardenia.net/plant/codiaeum-variegatum-croton), [Epic Gardening](https://www.epicgardening.com/crotons/), [Old Farmer's Almanac](https://www.almanac.com/plant/croton), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Codiaeum variegatum | `species.scientific_name` |
| Volksnamen (DE/EN) | Croton, Wunderstrauch; Croton, Garden Croton, Joseph's Coat, Fire Croton | `species.common_names` |
| Familie | Euphorbiaceae | `species.family` → `botanical_families.name` |
| Gattung | Codiaeum | `species.genus` |
| Ordnung | Malpighiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 11a, 11b, 12a, 12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10–13°C, optimal 18–27°C. Wirft Blätter bei Kälte, Zugluft und Standortwechsel. | `species.hardiness_detail` |
| Heimat | Südostasien (Indonesien, Malaysia, Pazifik) — tropischer Regenwald | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Croton ist bekannt für sein spektakuläres, buntfarbiges Laub (Rot, Orange, Gelb, Grün, Lila in vielen Mustern). Braucht sehr viel Licht für intensive Blattfärbung — wenig Licht = Blätter werden grün und fade. Häufigste Pflegefehler: Standortwechsel (Blattabwurf), Zugluft, Temperaturschock. Wächst im Sommer optimal (19–27°C + helle Sonne) und ist im Winter bei niedrigen Temperaturen oder trockener Heizungsluft stressanfällig.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (3–4 cm, halbholzig) im Sommer mit Bodenwärme (25–30°C) und hoher Luftfeuchtigkeit (Folienzelt). Schnittfläche mit Holzkohle bestreuen um Latex-Bluten zu stoppen. Bewurzelung in 4–8 Wochen. Ableger (Air Layering) im Frühjahr ebenfalls möglich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (Milchsaft/Latex, Blätter, Samen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | croton_oil (Diterpen-Ester), saponins | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Latex-Milchsaft verursacht Hautreizungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Bei Gartenarbeiten Handschuhe tragen — das Croton-Öl im Milchsaft kann Hautreizungen, Bläschen und gastrointestinale Beschwerden verursachen. Bei Tieren vor allem Erbrechen und Durchfall.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Verträgt Rückschnitt gut — fördert buschigeren Wuchs. Im Frühjahr überlange Triebe kürzen. Beim Schneiden Handschuhe und Augenschutz tragen (Latex spritzt).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 50–150 (indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (volle Sonne bis Halbschatten, kein Regen, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, humusreiche Einheitserde mit 20% Perlite. pH 4.5–6.5. Gut drainiert. Leicht feuchtigkeitshaltend. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:3 | 0.8–1.4 | 4.5–6.5 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 4.5–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | – | organisch | 30 g/Topf | Frühjahr |
| Wurmhumus | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 2 Wochen März bis September. Oktober bis Februar kein Dünger. Ausgewogene NPK-Formel; leicht erhöhter Kaliumanteil fördert intensive Blattfärbung. Überdüngung führt zu Salzschäden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; gleichmäßig feucht halten — weder austrocknen noch Staunässe. Besprühen der Blätter erhöht Luftfeuchtigkeit und hält Spinnmilben fern. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter verlieren Farbe | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |
| Thrips | Frankliniella occidentalis | Silbrige Streifen, Blätter deformiert | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Blattflecken | fungal/bacterial | Braune nasse Flecken | Nasses Laub |
| Echter Mehltau | fungal | Weißer Belag | Trockene Blätter, warme Tage |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse, Thrips |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |
| Luftfeuchtigkeit erhöhen | cultural | Regelmäßig besprühen | 0 | Spinnmilbe (Prävention) |
| Kaliumbicarbonat | biological | Sprühen 0.5% | 0 | Echter Mehltau |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Drachenbaum | Dracaena marginata | Buntlaubige Zimmerpflanze | Robuster, toleriert weniger Licht |
| Aglaonema 'Red Siam' | Aglaonema commutatum cv. | Rotes Buntlaub | Schattentoleranter |
| Cordyline australis | Cordyline australis | Rosetten-Buntlaub | Ähnliche Farbwirkung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Codiaeum variegatum,"Croton;Wunderstrauch;Garden Croton;Joseph's Coat",Euphorbiaceae,Codiaeum,perennial,day_neutral,shrub,fibrous,"11a;11b;12a;12b","Südostasien (Indonesien, Malaysia)",yes,5-20,20,50-150,40-80,yes,limited,false,medium_feeder
```

---

## Quellenverzeichnis

1. [NC State Extension — Codiaeum variegatum](https://plants.ces.ncsu.edu/plants/codiaeum-variegatum/) — Botanische Daten, USDA-Zonen
2. [Gardenia.net — Codiaeum variegatum](https://www.gardenia.net/plant/codiaeum-variegatum-croton) — Kulturdaten
3. [Epic Gardening — Crotons](https://www.epicgardening.com/crotons/) — Schädlinge, Pflege
4. [Old Farmer's Almanac — Croton](https://www.almanac.com/plant/croton) — Allgemeine Pflegehinweise
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
