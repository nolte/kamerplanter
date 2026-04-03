# Riemenblume — Clivia miniata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardeners World – Clivia](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-and-care-for-clivia/), [Guide to Houseplants – Clivia miniata](https://www.guide-to-houseplants.com/clivia-miniata.html), [Wisconsin Horticulture – Clivia](https://hort.extension.wisc.edu/articles/clivia/), [UK Houseplants – Clivia](https://www.ukhouseplants.com/plants/clivia-natal-or-bush-lily)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Clivia miniata | `species.scientific_name` |
| Volksnamen (DE/EN) | Riemenblume, Klivie; Natal Lily, Kaffir Lily, Bush Lily | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` → `botanical_families.name` |
| Gattung | Clivia | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9b–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Übersteht kurzzeitig leichten Frost (bis -3°C); Wurzeln frostempfindlich | `species.hardiness_detail` |
| Heimat | Südafrika (KwaZulu-Natal, Ostkap) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 2, 3, 4, 5 (Frühjahrsblüher nach Winterkühle) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, division, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, besonders Wurzeln und Beeren | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Lycorin, Clivacin (Alkaloide) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (nach Verblühen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 45–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gut drainierte, nährstoffreiche Zimmerpflanzenerde; Clivien mögen enge Töpfe — erst umtopfen wenn Wurzeln aus dem Topf wachsen | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 60–90 | 1 | false | false | high |
| Blütenaustrieb | 14–21 | 2 | false | false | low |
| Blüte | 28–42 | 3 | false | false | medium |
| Vegetativ (Sommer) | 150–210 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Winterruhe — Okt bis Jan

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–13 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Blütenaustrieb | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Blüte | 0:1:2 | 0.5–0.8 | 6.0–6.5 | 80 | 40 | — | 1 |
| Vegetativ | 2:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 50 | — | 2 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Blütenaustrieb | time_based | 60–90 Tage | Temperaturanstieg auf 18°C, Blütenstiel erscheint |
| Blütenaustrieb → Blüte | time_based | 14–21 Tage | Blüten öffnen |
| Blüte → Vegetativ | time_based | 28–42 Tage | Blüten verblüht |
| Vegetativ → Winterruhe | time_based | 150–210 Tage | Herbst, Temperatur senken |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Substral | base | 4-6-8 | 5 ml/L | 1 | blüte, vegetativ |
| Zimmerpflanzendünger | Compo | base | 7-4-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Guano-Blumendünger | Gardol | organisch | 2 ml/L | Apr–Sep | light_feeder |
| Langzeitdünger Stäbchen | Substral | langsam | 1 Stäbchen/Topf | Apr–Sep | light_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| Okt–Jan | Winterruhe | 0.0 | — | Kein Dünger |
| Feb–Apr | Blüte | 0.5–0.8 | 6.2 | Sehr sparsam |
| Mai–Sep | Vegetativ | 0.8–1.2 | 6.2 | Alle 4–6 Wochen |
| Okt | Einwintern | 0.0 | — | Letzte Düngung |

### 3.3 Besondere Hinweise zur Düngung

Clivia ist ein Schwachzehrer. Zu viel Dünger verhindert die Blütenbildung. Die Winterkühle (10–13°C) für 6–8 Wochen ist die entscheidende Voraussetzung für die Blüteninduktion — nicht die Düngung. Wer diese Kältephase einhält, hat fast immer gute Blüten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 8 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (10–13°C), wenig gießen, nicht düngen | hoch |
| Feb | Blütenanzeichen | Blütenstiel wächst — Pflanze an hellen Platz stellen | hoch |
| Mär–Apr | Blüte | Regelmäßig gießen, Blätter nicht benetzen | mittel |
| Apr–Mai | Nach Blüte | Verblühte Blütenstiele entfernen (knapp über der Erde) | mittel |
| Jun–Sep | Wachstum | Regelmäßig gießen, monatlich düngen | hoch |
| Okt | Einwintern | Kühlen Standort suchen (10–13°C), Wasser reduzieren | hoch |
| Nov–Jan | Winterruhe | Minimal gießen, kein Dünger, keine Wärme | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen | stem | alle | difficult |
| Spinnmilben | Tetranychus urticae | Gelb-gesprenkeltes Laub | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Anthraknose | fungal | Braune Blattränder, dunkle Flecken | high_humidity, overwatering | 7–14 | alle |
| Bakterienfäule (Erwinia) | bacterial | Weiche, nasse Fäule am Blattansatz | waterlogging, wounds | 3–7 | alle |
| Wurzelfäule | fungal | Welke Blätter trotz Wasser | overwatering | 7–21 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wollläuse | 1–2 Käfer/Pflanze | 14 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Wollläuse, Spinnmilben |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Schildläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Clivia miniata |
|-----|-------------------|-------------|------------------------------|
| Clivia nobilis | Clivia nobilis | Gleiche Gattung | Nickende Blüten, seltener |
| Amaryllis | Hippeastrum hybridum | Gleiche Familie | Größere Blüten, Winter-Blüher |
| Agapanthus | Agapanthus africanus | Blaue Blüten, ähnliche Kultur | Blau blühend, halbhardy |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Clivia miniata,Riemenblume;Klivie;Natal Lily,Amaryllidaceae,Clivia,perennial,day_neutral,herb,rhizomatous,9b;10a;10b;11a;11b,0.0,Südafrika KwaZulu-Natal,yes,10,20,60,60,—,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Gardeners World – Clivia Care](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-and-care-for-clivia/) — Pflege, Überwinterung
2. [Guide to Houseplants – Clivia miniata](https://www.guide-to-houseplants.com/clivia-miniata.html) — Indoor Care
3. [Wisconsin Horticulture – Clivia](https://hort.extension.wisc.edu/articles/clivia/) — University Extension Service
4. [UK Houseplants – Clivia](https://www.ukhouseplants.com/plants/clivia-natal-or-bush-lily) — Detailed Care
5. [Old Farmer's Almanac – Clivia](https://www.almanac.com/plant/clivia) — Growing Tips
