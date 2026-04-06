# Pink Jasmin — Jasminum polyanthum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Jasminum polyanthum](https://www.gardenia.net/plant/jasminum-polyanthum-pink-jasmine), [Guide to Houseplants – Jasmine](https://www.guide-to-houseplants.com/jasmine-plant.html), [Forward Plant – Jasminum polyanthum](https://www.forwardplant.com/plant-info/jasminum-polyanthum/), [Wikipedia – Jasminum polyanthum](https://en.wikipedia.org/wiki/Jasminum_polyanthum)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Jasminum polyanthum | `species.scientific_name` |
| Volksnamen (DE/EN) | Pink Jasmin, Vielblütiger Jasmin; Pink Jasmine, Chinese Jasmine | `species.common_names` |
| Familie | Oleaceae | `species.family` → `botanical_families.name` |
| Gattung | Jasminum | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kurze Fröste bis -5°C tolerierend; in Mitteleuropa Überwinterung bei 5–10°C | `species.hardiness_detail` |
| Heimat | China (Yunnan), Myanmar | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze/Kübel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 2, 3, 4, 5 (intensiver Duft, rosa-weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

**Hinweis:** Der intensive Duft kann für empfindliche Personen oder in geschlossenen Räumen überwältigend sein.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (nach Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 300–600 (Kletterpflanze) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–300 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gut drainierte Kübelpflanzenerde; pH 6.0–7.0; Rankgitter oder Spalier | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | medium |
| Blüte (Winter–Frühjahr) | 60–90 | 2 | false | false | medium |
| Vegetativ (Sommer) | 150–210 | 3 | false | false | high |
| Herbstreife | 30–60 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Winter–Frühjahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 6–8 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — |
| Blüte | 1:2:2 | 0.8–1.2 | 6.0–7.0 | 80 | 40 | — | 1 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 6.0–7.0 | 120 | 50 | — | 2 |
| Herbstreife | 0:1:2 | 0.6–1.0 | 6.0–7.0 | 60 | 30 | — | 1 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Blüte | time_based | — | Winter/Frühjahr, kurze Tage + Kühle |
| Blüte → Vegetativ | time_based | 60–90 Tage | Nach Rückschnitt |
| Vegetativ → Herbstreife | time_based | 150–210 Tage | Herbst, Temperaturen sinken |
| Herbstreife → Winterruhe | time_based | 30–60 Tage | Einwintern Oktober/November |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Kübel)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Compo | base | 4-6-8 | 5 ml/L | 1 | blüte |
| Kübelpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Kübel)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | — | organisch | 50 g/10L Topf | Frühjahr | medium_feeder |
| Kompost | eigen | organisch | 2–3 L/Topf | Frühjahr | medium_feeder |

### 3.2 Besondere Hinweise zur Düngung

Die Überwinterung bei 5–10°C ist der Schlüssel für die Blüteninduktion — Jasmin blüht nur nach Kälteschlaf. Während der Blüte (Feb–Mai) nicht oder nur sehr wenig düngen. Hauptdüngung während der vegetativen Phase (Jun–Sep) für den nächsten Triebaufbau. Nach dem Rückschnitt im Mai/Juni stickstofflastig düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normal; kein besonderer Bedarf | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Blütevorbereitung | Kühl halten, Knospen entstehen | hoch |
| Feb–Apr | Blütezeit | Genießen, wenig düngen | niedrig |
| Mai | Rückschnitt | Kräftiger Rückschnitt nach Blüte | hoch |
| Jun | Düngung | Stickstofflastige Düngung für Triebaufbau | hoch |
| Jun–Sep | Wachstum draußen | Sonniger Balkon, regelmäßig gießen | hoch |
| Okt | Einwintern | Vor Frost rein, Gießen reduzieren | hoch |
| Nov–Dez | Winterruhe | Kühl (5–10°C), minimal gießen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Deformierte Triebe, Honigtau | stem | vegetative | easy |
| Schildläuse | Coccus hesperidum | Braune Schuppen | stem | alle | difficult |
| Weiße Fliege | Trialeurodes vaporariorum | Weiße Fliegen, Honigtau | leaf | alle | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste | leaf | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Welke Blätter, schlechtes Wachstum | overwatering | 7–14 | alle |
| Blattflecken | fungal | Gelblich-braune Flecken | high_humidity | 7–14 | alle |
| Rostpilz | fungal | Orangefarbene Rostflecken | poor_airflow | 7–14 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Aphidius colemani | Blattläuse | 5–10 | 7–14 |
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Blattläuse, Spinnmilben |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Weiße Fliege |
| Abbrausen | mechanical | Wasser | Blätter abbrausen | 0 | Blattläuse, Spinnmilben |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kübelpflanze |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Jasminum polyanthum |
|-----|-------------------|-------------|------------------------------|
| Echter Jasmin | Jasminum officinale | Gleiche Gattung | Winterhärter (bis Zone 7) |
| Stephanotis | Stephanotis floribunda | Duftende Kletterpflanze | Eher statisch, keine Überwinterung |
| Trachelospermum | Trachelospermum jasminoides | Duftend, kletternd | Winterhärter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Jasminum polyanthum,Pink Jasmin;Vielblütiger Jasmin;Chinese Jasmine,Oleaceae,Jasminum,perennial,short_day,vine,fibrous,8a;8b;9a;9b;10a;10b,0.0,China Myanmar,yes,15,20,600,300,—,limited,yes,false,true
```

---

## Quellenverzeichnis

1. [Gardenia.net – Jasminum polyanthum](https://www.gardenia.net/plant/jasminum-polyanthum-pink-jasmine) — Care Guide
2. [Guide to Houseplants – Jasmine](https://www.guide-to-houseplants.com/jasmine-plant.html) — Indoor Care
3. [Forward Plant – Jasminum polyanthum](https://www.forwardplant.com/plant-info/jasminum-polyanthum/) — Pests, Diseases
4. [Wikipedia – Jasminum polyanthum](https://en.wikipedia.org/wiki/Jasminum_polyanthum) — Taxonomie, USDA Zones
5. [The Green Thumbler – Pink Jasmine](https://www.thegreenthumbler.com/jasminum-polyanthum-pink-jasmine/) — Growing Tips
