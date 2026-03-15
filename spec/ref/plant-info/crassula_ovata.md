# Geldbaum — Crassula ovata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/jade-plant-crassula-ovata/), [Wikipedia Crassula ovata](https://en.wikipedia.org/wiki/Crassula_ovata), [Old Farmer's Almanac](https://www.almanac.com/plant/jade-plants), [ASPCA](https://www.aspca.org/), [Joy Us Garden](https://www.joyusgarden.com/jade-plant-care/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Crassula ovata | `species.scientific_name` |
| Volksnamen (DE/EN) | Geldbaum, Pfennigbaum, Jade-Pflanze; Jade Plant, Money Plant, Friendship Tree | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Crassula | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 50–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 5°C (Kältestress unter 10°C), optimal 15–29°C. Im Winter kühler Standort (10–15°C) fördert Blütenbildung. | `species.hardiness_detail` |
| Heimat | Südafrika (Mosambik, Ostkap-Region — trockene Buschsavanne) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Crassula ovata ist ein echter Sukkulentenstrauch und kann Indoor-Pflanzen der Jahrzehnte werden — bis zu 1 m Höhe und Stammdicken von 5–8 cm. Die Pflanze benötigt sehr viel Licht für guten Wuchs und Blüte. Kulturell bekannt als Glücksbringer in vielen asiatischen Kulturen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 11, 12, 1, 2 (bei reifen Pflanzen ab 5–7 Jahren bei kühlem Winterstandort) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge: 7–10 cm Ast abschneiden, 2–3 Tage Schnittfläche trocknen lassen (callus), dann in Kakteensubstrat stecken. Nicht gießen bis Widerststand beim Zupfen spürbar (Bewurzelung). Blattstecklinge: Einzelne Blätter abdrehen, trocknen lassen, auf feuchtes Substrat legen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | unknown_toxin (Wirkstoff nicht vollständig identifiziert) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken:** Übelkeit, Erbrechen, Depression bei Tieren. Quelle: ASPCA Animal Poison Control. Schweregrad gering bei normalen Mengen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Regelmäßiger Rückschnitt fördert buschigen Wuchs und verhindert "Leggy"-Wuchs. Im Frühling überlange Triebe um 1/3 kürzen. Bewurzelung der Schnittlinge möglich.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer, volle Sonne, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde oder Einheitserde mit 50% Perlite/Grobsand. Sehr gute Drainage. Tongefäße ideal. Kleiner Topf (root-bound fördert Blüte). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 (kurze Tage für Blüteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 7–13 | `requirement_profiles.temperature_night_c` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 (P/K-betont) | 0.4–0.8 | 6.0–7.0 | 40 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 3 ml/L (alle 6–8 Wochen) | Wachstum |
| Kakteen Dünger | Substral | base | 3-6-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Extremer Schwachzehrer. 2–3 Düngergaben pro Wachstumssaison ausreichend. Niemals im Winter düngen. Überdüngung führt zu weichem, anfälligem Gewebe.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; Staunässe ist häufigste Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste (bei sehr trockener Luft) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Weicher, verfärbter Stamm, Blätter fallen ab | Überbewässerung |
| Anthraknose | fungal | Braune, eingesunkene Flecken | Hohe Luftfeuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Gollum-Jade | Crassula ovata 'Gollum' | Gleiche Art, röhrenförmige Blätter | Skurrile Optik, pflegeleicht |
| Dickblatt | Crassula arborescens | Gleiche Gattung | Silbrig-grüne Blätter |
| Haworthia | Haworthiopsis fasciata | Asphodelaceae (nicht gleiche Familie) | Mehr schattenverträglich, kompakter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Crassula ovata,"Geldbaum;Pfennigbaum;Jade Plant;Money Plant",Crassulaceae,Crassula,perennial,short_day,shrub,fibrous,"10a;10b;11a;11b","Südafrika (Ostkap-Region)",yes,3-15,20,30-120,30-90,yes,yes,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Gollum,Crassula ovata,"ornamental;tubular_leaves",clone
Hobbit,Crassula ovata,"ornamental;curled_leaves",clone
Tricolor,Crassula ovata,"ornamental;variegated;green_white_pink",clone
```

---

## Quellenverzeichnis

1. [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/jade-plant-crassula-ovata/) — Kulturdaten
2. [Wikipedia — Crassula ovata](https://en.wikipedia.org/wiki/Crassula_ovata) — Taxonomie, Heimat
3. [Old Farmer's Almanac — Jade Plant](https://www.almanac.com/plant/jade-plants) — Pflegehinweise
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
5. [Joy Us Garden](https://www.joyusgarden.com/jade-plant-care/) — Vermehrung, Praxiswissen
