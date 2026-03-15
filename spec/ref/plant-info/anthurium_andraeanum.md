# Flamingoblume — Anthurium andraeanum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [BBC Gardeners World](https://www.gardenersworld.com/house-plants/how-to-grow-anthurium/), [Bloomscape](https://bloomscape.com/plant-care-guide/anthurium/), [Gardenia.net](https://www.gardenia.net/plant/anthurium-andraeanum), [ASPCA](https://www.aspca.org/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/anthurium-anthurium-andraeanum-care-guide/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Anthurium andraeanum | `species.scientific_name` |
| Volksnamen (DE/EN) | Flamingoblume, Große Flamingoblume; Flamingo Flower, Anthurium, Painter's Palette | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Anthurium | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 21–29°C. Zugluft und Kälte führen zu Blattschäden. | `species.hardiness_detail` |
| Heimat | Kolumbien, Ecuador (tropische Regenwälder, epiphytisch auf Bäumen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | ammonia, formaldehyde, xylene, toluene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die bunten "Blüten" von Anthurium andraeanum sind eigentlich modifizierte Blätter (Spathen) — die eigentliche Blüte ist der zylindrische Kolben (Spadix). Die Pflanze kann bei richtiger Pflege nahezu ganzjährig blühen. Für mehr Blüten: helles Licht und moderate Phosphor-Düngung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 (Dauerblüher bei guten Bedingungen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung bei Umtopfen (Frühling). Stängelstecklinge (mit mindestens 2–3 Blättern und Luftwurzelansatz) in Orchideensubstrat. Bewurzelung bei 22–24°C Bodentemperatur und 70–80% Luftfeuchtigkeit.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, spathe, berries | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Sap verursacht Hautreizungen und Kontaktdermatitis — Handschuhe beim Umtopfen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (verblühte Spathen entfernen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–70 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockeres, luftiges Orchideen-/Epiphytensubstrat: Pinienrinde + Perlite + etwas Torf (2:1:1). pH 5.5–6.5. Kein schweres, dichtes Substrat. Luftwurzeln müssen Sauerstoff bekommen. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum + Blüte (Frühling/Sommer) | 210–240 | 1 | false | false | medium |
| Winterruhe (reduziertes Wachstum) | 90–120 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–350 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum + Blüte | 1:2:1 (P-betont für Blüte) | 0.6–1.0 | 5.5–6.5 | 80 | 35 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 5.5–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Compo | base | 5-8-10 | 5 ml/L (alle 6 Wochen) | Wachstum |
| Orchideen-Dünger | Compo | base | 7-5-6 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Phosphorbetonte Formel fördert Blütenbildung. Alle 6–8 Wochen März bis September. Kein Dünger November bis Februar. Weiches, kalkfreies Wasser bevorzugen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser zwingend. Raumtemperatur. Kalk führt zu Blattrandnekrosen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42–56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, gelbe Punkte | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Wurzeln | Überbewässerung |
| Bakterielle Welke | bacterial | Plötzliche Welke, verwässerte Stängel | Wunden, kontaminierte Erde |
| Blattflecken | fungal/bacterial | Dunkelbraune nasse Flecken | Wasser auf Blättern |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (Spathen schützen!) | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus, Schmierlaus |
| Drainage verbessern | cultural | Substrat wechseln, Topf mit Abzugslöchern | 0 | Wurzelfäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kleines Anthurium | Anthurium scherzerianum | Gleiche Gattung | Kompakter; toleriert weniger Licht |
| Samtanthurium | Anthurium magnificum | Gleiche Gattung | Imposante Samtblätter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Anthurium andraeanum,"Flamingoblume;Große Flamingoblume;Flamingo Flower;Anthurium",Araceae,Anthurium,perennial,day_neutral,herb,aerial,"11a;11b;12a","Kolumbien, Ecuador (Tropenwälder)",yes,2-8,15,30-70,30-60,yes,no,false,light_feeder,0.6
```

---

## Quellenverzeichnis

1. [BBC Gardeners World — Anthurium](https://www.gardenersworld.com/house-plants/how-to-grow-anthurium/) — Pflegehinweise
2. [Bloomscape — Anthurium Care Guide](https://bloomscape.com/plant-care-guide/anthurium/) — Wachstumsparameter
3. [Gardenia.net — Anthurium andraeanum](https://www.gardenia.net/plant/anthurium-andraeanum) — Botanische Daten
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/anthurium-anthurium-andraeanum-care-guide/) — Ganzjahrespflege
