# Kaffeepflanze — Coffea arabica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide – Coffea arabica](https://smartgardenguide.com/coffee-plant-care-indoors/), [Plantophiles – Coffee Plant Care](https://plantophiles.com/plant-care/coffee-plant-care/), [Bloomscape – Coffee Plant 101](https://bloomscape.com/plant-care-guide/coffee-plant/), [UK Houseplants – Coffee Plants](https://www.ukhouseplants.com/plants/coffee-plants-coffea-arabica)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Coffea arabica | `species.scientific_name` |
| Volksnamen (DE/EN) | Kaffeepflanze, Arabica-Kaffee; Coffee Plant, Arabian Coffee | `species.common_names` |
| Familie | Rubiaceae | `species.family` → `botanical_families.name` |
| Gattung | Coffea | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Kälteempfindlich; unter 15°C drohen irreversible Blattschäden | `species.hardiness_detail` |
| Heimat | Äthiopien, Jemen (Ursprung), tropisches Hochland | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Kaffeebohnen erst nach 3–4 Jahren; Reife Okt–Jan) | `species.harvest_months` |
| Blütemonate | 4, 5, 6 (nach Erreichen der Reife ca. 3–4 Jahre) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Blätter, Stängel, unreife Beeren (Kaffeebohnen sind unbedenklich geröstet) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Coffein, Theobromin (in Blättern/Schalen) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (in Natur bis 900 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Saure, humusreiche Erde; pH 6.0–6.5; gute Drainage; z.B. Rhododendronerde + 20% Perlite | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 30–60 | 1 | false | false | low |
| Jugendphase | 365–730 (1–2 Jahre) | 2 | false | false | low |
| Vegetativ (Wachstum) | 365–730 (Folgejahre) | 3 | false | false | medium |
| Blüte & Fruchtreife | 270–365 | 4 | false | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–21 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte & Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.1 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Jugendphase | 3:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 50 | — | 3 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 6.0–6.5 | 150 | 60 | — | 3 |
| Blüte & Frucht | 2:2:3 | 1.2–1.8 | 6.0–6.5 | 120 | 60 | — | 2 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung → Jugendphase | time_based | 30–60 Tage | Keimblätter entfaltet |
| Jugendphase → Vegetativ | time_based | 365–730 Tage | Mehrere Laubblattpaar-Etagen |
| Vegetativ → Blüte | time_based | 1095–1460 Tage (3–4 Jahre) | Pflanze ausreichend groß, Reife |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Acidic Plant Fertilizer | Schultz | base | 11-8-11 | 7 Tropfen/L | 1 | vegetativ, blüte |
| Rhododendron-Dünger | Compo | base | 12-4-8 | 5 ml/L | 1 | alle |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kaffeesatz | — | organisch | 1–2 TL ins Substrat | Frühjahr | medium_feeder |
| Rhododendron-Langzeitdünger | Cuxin | organisch/langsam | 30–50 g/10L Topf | Apr–Sep | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–12 | Keimung/Jugend | 0.8–1.2 | 6.2 | — | Nur bei aktivem Wachstum |
| 13+ | Vegetativ | 1.2–1.8 | 6.2 | 5 | Alle 2–4 Wochen Apr–Sep |
| Blüte | Fruchtphase | 1.2–1.8 | 6.2 | 5 | Regelmäßig, kaliumreich |
| Okt–Feb | Ruhephase | — | — | — | Kein Dünger |

### 3.3 Mischungsreihenfolge

1. Wasser
2. Säuernder Dünger oder Rhododendron-Dünger
3. pH-Kontrolle (Ziel: 6.0–6.5)

### 3.4 Besondere Hinweise zur Düngung

Coffea arabica bevorzugt leicht saure Substrate (pH 6.0–6.5). Normales Leitungswasser (oft pH 7.0+) sollte mit Regenwater gemischt oder leicht angesäuert werden. Gelblich-chlorotische Blätter deuten auf Eisenmangel durch falschen pH hin — Rhododendron-Dünger enthält sequestiertes Eisen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser; pH 6.0–6.5; Regenwasser ideal | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Ruhephase | Sparsam gießen, nicht düngen, 15–18°C | niedrig |
| Feb–Mär | Rückschnitt | Formschnitt, abgestorbene Äste entfernen | mittel |
| Mär | Umtopfen | In frisches saures Substrat bei Bedarf | mittel |
| Apr | Düngung beginnen | Rhododendron-Dünger oder Azaleendünger | hoch |
| Mai–Sep | Hauptwachstum | Regelmäßig gießen und düngen | hoch |
| Jun–Sep | Beregnung erhöhen | Hohe Luftfeuchtigkeit wichtig (Besprühen) | mittel |
| Okt | Einwintern | Ins Warme, Düngung einstellen | hoch |
| Nov–Dez | Winterpflege | Heller, warmer Standort, sparsam gießen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 15 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 20 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelb-gesprenkelte Blätter | leaf | alle | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen auf Ästen | stem | alle | difficult |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Blattläuse | Aphis spp. | Deformierte Triebspitzen, Honigtau | stem | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kaffeerost | fungal (Hemileia vastatrix) | Orange-gelbe Pusteln auf Blattunterseite | high_humidity, warm_nights | 7–14 | alle |
| Chlorose | physiological | Gelbe Blätter, grüne Adern | wrong_pH, iron_deficiency | — | alle |
| Wurzelfäule | fungal | Welke, vergilbte Blätter | overwatering | 7–14 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Aphidius colemani | Blattläuse | 5–10 | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Spinnmilben, Wollläuse |
| Eisendünger (chelat) | cultural | EDTA-Eisen | Gießen 2–5 ml/L | 0 | Chlorose |
| Pflanzenstärkungsmittel | biological | Kaliseife | Sprühen 2% | 0 | Blattläuse |

### 5.5 Anfälligkeiten der Art

| Anfälligkeit | Typ | KA-Edge |
|-------------|-----|---------|
| Kaffeerost (Hemileia vastatrix) — C. arabica ist deutlich anfälliger als C. canephora (Robusta) | Krankheit | `susceptible_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Coffea arabica |
|-----|-------------------|-------------|------------------------------|
| Robusta-Kaffee | Coffea canephora | Gleiche Gattung | Robuster, weniger kälteempfindlich |
| Liberica-Kaffee | Coffea liberica | Gleiche Gattung | Größere Blätter, seltener als Zimmerpflanze |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Coffea arabica,Kaffeepflanze;Arabica-Kaffee;Coffee Plant,Rubiaceae,Coffea,perennial,day_neutral,shrub,fibrous,10a;10b;11a;11b;12a;12b,0.1,Äthiopien tropisches Hochland,yes,15,25,200,100,—,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Smart Garden Guide – Coffea arabica](https://smartgardenguide.com/coffee-plant-care-indoors/) — Indoor Care
2. [Plantophiles – Coffee Plant Care Guide](https://plantophiles.com/plant-care/coffee-plant-care/) — Vollständige Pflegeanleitung
3. [Bloomscape – Coffee Plant 101](https://bloomscape.com/plant-care-guide/coffee-plant/) — Grundpflege
4. [UK Houseplants – Coffea arabica](https://www.ukhouseplants.com/plants/coffee-plants-coffea-arabica) — Detailed Care Guide
5. [Healthy Houseplants – Coffea arabica](https://www.healthyhouseplants.com/indoor-houseplants/coffee-plant-care-guide-growing-coffea-arabica-indoors-and-out/) — Indoor & Outdoor
