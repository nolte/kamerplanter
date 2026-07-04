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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 5+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein publiziertes GDD-Modell für die tropische Zierpflanze; Wachstum stoppt unterhalb ~15 °C, Kälteschäden (chilling injury) unter ~12 °C — diese Werte sind keine GDD-Basis | `species.base_temp` |
| Kritische Tageslänge (h) | Entfällt — tagneutral (day_neutral), kein Kurztag-/Langtag-Blühreiz | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 2 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–25 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Maas-Hoffman a, Substrat-ECe) | <!-- DATEN FEHLEN --> kein publizierter Maas-Hoffman-Schwellenwert; konsistent mit Klasse `sensitive` (< 2 dS/m); empfohlene Nährlösungs-EC 1.0–1.5 mS/cm | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m, Maas-Hoffman b) | <!-- DATEN FEHLEN --> kein publizierter Maas-Hoffman-Slope (Schnittblumenertrag −22 % zwischen 4.0 und 9.8 dS/m, aber keine sauber abgeleitete Slope-Konstante) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis (Licht):** Der Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) liegt sehr niedrig (< 5 µmol/m²/s) — typisch für eine schattenadaptierte Regenwald-Unterwuchspflanze. Davon zu trennen: der Lichtsättigungspunkt (light saturation point) bei ca. 350–485 µmol/m²/s; oberhalb davon droht Photoinhibition/Blattverbrennung. Diese Sättigungs-/Optimumwerte gehören NICHT ins Kompensationspunkt-Feld.

**Hinweis (Salz):** Anthurium andraeanum gilt als salzempfindlichste der untersuchten Schnittblumen-Floristikkulturen (Sonneveld; HortTechnology 2011), mit spezifischer Natriumchlorid-Empfindlichkeit. Bezugsgröße der Schwellenangaben ist die Substrat-ECe, nicht die Gießwasser-EC.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–350 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 0.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum + Blüte | 1:2:1 (P-betont für Blüte) | 0.6–1.0 | 5.5–6.5 | 80 | 35 | 0.5 | 0.1 | 0.03 | 0.025 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 5.5–6.5 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Mangan/Zink/Kupfer/Molybdän (manganese/zinc/copper/molybdenum) folgen der Standard-Gewächshaus-Nährlösung für Zierpflanzen (Sonneveld & Voogt; ScienceDirect Anthurium-soilless-Studie). Werte gelten für die aktive Wachstums-/Blühphase; in der Winterruhe wird nicht gedüngt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor Nachttemperaturen < 15 °C) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 6 (Juni, nach den Eisheiligen / stabil > 15 °C) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 18–22 (Minimum 15 °C; Kälteschäden unter ~12 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, ohne direkte Mittagssonne (100–300 µmol/m²/s); ggf. Pflanzenlampe | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert, Substrat zwischen den Gaben antrocknen lassen (Intervall 10–14 Tage) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Anthurium andraeanum ist nicht frosthart (frost_free) und verbringt den Winter zwingend frostfrei im Innenraum. Ein Sommeraufenthalt im Freien (Juni–September, halbschattig, windgeschützt) ist in Mitteleuropa (USDA 6–8) möglich, aber kein Muss — als reine Zimmerpflanze kann sie ganzjährig drinnen bleiben. Wichtig sind Zugluftschutz und Luftfeuchtigkeit über trockener Heizungsluft.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|--------------------|----------------|-----------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 (je nach Befallsdichte) | ca. 2–3 Wochen (wöchentl. wiederholen) |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10 (Adulte) | ca. 3–4 Wochen (3× im Abstand 1–2 Wo.) |

**Hinweis:** Phytoseiulus persimilis arbeitet optimal bei 15–25 °C und > 65 % Luftfeuchte — das passt gut zum tropischen Anthurium-Klima. Cryptolaemus montrouzieri bevorzugt 25–28 °C (Minimum 16 °C). Beide nur im Innenraum/Gewächshaus gegen aktiven Befall ausbringen; Ausbringraten je nach Befallsdichte und Klima anpassen (Koppert).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Photosynthetic Responses of Anthurium × 'Red' under Different Light Conditions (PMC8145403)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8145403/) — Lichtkompensationspunkt (< 5 µmol/m²/s), Lichtsättigungspunkt (347–484 µmol/m²/s)
7. [Distribution and photosynthetic assimilation of rosulate aroid epiphytes (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0367253021000694) — Araceae ohne CAM (C3), Schattenadaptation epiphytischer Aronstabgewächse
8. [Assessing Tolerance to Sodium Chloride Salinity in Fourteen Floriculture Species, HortTechnology 21(5) 2011](https://journals.ashs.org/horttech/view/journals/horttech/21/5/article-p539.xml) — Anthurium als salzempfindlichste Floristikkultur (salt tolerance class sensitive)
9. [Studies on the salt tolerance of some flower crops grown under glass (Sonneveld, Plant and Soil)](https://link.springer.com/article/10.1007/BF02178738) — NaCl-Empfindlichkeit, EC-Bereich, Salzklassifikation
10. [Nutrient solution effects on the development and yield of Anthurium andreanum in tropical soilless conditions (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S030442380500052X) — Anthurium-Nährlösung (N-Obergrenze, EC, Mikronährstoffkontext)
11. [Nutrient Solutions for Greenhouse Crops (Eurofins/Sonneveld-Manual)](https://cdnmedia.eurofins.com/corporate-eurofins/media/12142795/160825_manual_nutrient_solutions_digital_en.pdf) — Standard-Mikronährstoffe (Mn/Zn/Cu/Mo ppm) für Gewächshaus-Zierpflanzen
12. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Spinnmilben-Raubmilbe (2–50/m²), Klimaansprüche
13. [Koppert — Cryptolaemus montrouzieri](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate Schmierlaus-Marienkäfer (2–10/m² Adulte), Etablierung
14. [PMC — Cultivar/chilling sensitivity & Anthurium temperature data](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.00846/full) — Kälteempfindlichkeit (chilling injury < 12 °C), Mindesttemperatur ~15 °C
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
