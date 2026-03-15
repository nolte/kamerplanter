# Mistelkaktus — Rhipsalis baccifera

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [OurHouseplants](https://www.ourhouseplants.com/plants/mistletoe-cactus-rhipsalis-baccifera), [Gardenia.net](https://www.gardenia.net/plant/rhipsalis-baccifera-mistletoe-cactus-grow-care-guide), [NC State Extension](https://plants.ces.ncsu.edu/plants/rhipsalis-baccifera/), [Smart Garden Guide](https://smartgardenguide.com/rhipsalis-care-mistletoe-cactus/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/how-to-grow-and-care-for-the-mistletoe-cactus-rhipsalis-baccifera/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rhipsalis baccifera | `species.scientific_name` |
| Volksnamen (DE/EN) | Mistelkaktus, Spaghetti-Kaktus; Mistletoe Cactus, Spaghetti Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Rhipsalis | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 10°C; einziger Kaktus mit natürlichem Verbreitungsgebiet außerhalb Amerikas (Afrika, Sri Lanka) | `species.hardiness_detail` |
| Heimat | Tropisches Amerika, Westafrika, Sri Lanka (epiphytisch in Baumkronen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit:** Rhipsalis baccifera ist ein epiphytischer Kaktus tropischer Regenwälder. Im Gegensatz zu Wüstenkakteen liebt er höhere Luftfeuchtigkeit und indirektes Licht. Er wächst natürlich in Baumgabeln auf organischem Detritus, nicht in Wüstenböden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant | `species.harvest_months` |
| Blütemonate | 12, 1, 2, 3 (winzige weiße Blüten; Fruchtentwicklung weiße Mistelbeeren) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Stecklinge:** 10–15 cm Triebstücke abschneiden. Wundstelle 24–48 Stunden abtrocknen lassen (kurzes Kallieren). In leicht feuchtes Orchideen- oder Kakteensubstrat stecken. Bei 20–25°C und höherer Luftfeuchtigkeit bewurzelt in 3–5 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine; Beeren können bei Massenkonsum geringe Reizwirkung haben | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine signifikanten Giftstoffe | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Zu lange Triebe können jederzeit eingekürzt werden. Die abgeschnittenen Stücke können als Stecklinge genutzt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–20 (hängend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–90 (hängende Triebe bis 100 cm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Orchideen-Substrat mit Perlit (1:1) oder Kakteenerde + Torfmoos + Perlit; pH 6.0–7.0; hervorragende Drainage; leicht feucht-luftig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung | 21–42 | 1 | false | false | medium |
| Vegetativ | 90–365 | 2 | false | false | high |
| Blüte (Winter) | 30–60 | 3 | false | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (Substrat oben leicht abtrocknen lassen, aber nie komplett) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (Winter)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 13–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetativ | 1:1:1 | 0.4–0.8 | 6.0–7.0 | 60 | 30 |
| Blüte | 0:1:1 | 0.3–0.6 | 6.0–7.0 | 40 | 20 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideendünger (stark verdünnt) | Substral | Flüssigdünger | 7-5-6 | 1 ml/L alle 4 Wochen | Vegetativ |
| Kaktusdünger (sehr verdünnt) | Compo | Flüssigdünger | 2-6-12 | 1 ml/L alle 4 Wochen | Vegetativ |

### 3.2 Besondere Hinweise zur Düngung

Rhipsalis als Epiphyt mit sehr geringem Nährstoffbedarf. Nur April bis September leicht düngen (einmal pro Monat, halbe Dosis). Im Winter (Oktober bis März) keinen Dünger. Stickstoff fördert übermäßiges grünes Wachstum auf Kosten der Blütenbildung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 8 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.8 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes, weiches Wasser bevorzugt; kein Kalk; Luftwurzeln können auch besprüht werden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Dez–Feb | Blütezeit | Wenig Wasser; kein Dünger; kühler Standort fördert Blüte; nicht umstellen | mittel |
| Mär | Düngesaison beginnen | Ersten Dünger nach Blüte; Gießen normalisieren | mittel |
| Apr–Sep | Aktive Wachstumsphase | Regelmäßig wässern; monatlich dünn düngen | hoch |
| Okt | Abdrosseln | Gießen reduzieren; Dünger einstellen; kühler Standort (15–18°C) | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollmasse, Honigtau | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbliche Punkte | medium |
| Trauermücken | Bradysia spp. | Larven im feuchten Substrat | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Pythium) | Welke, schwarze Triebbasen | Staunässe |
| Stammfäule | fungal | Braune, eingesunkene Stellen | Verletzungen + Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Wollläuse, Milben |
| Trockenperlite-Schicht | cultural | — | 1 cm auf Substrat | 0 | Trauermücken |
| Stecklinge retten | cultural | — | Gesunde Triebe abschneiden, neu bewurzeln | 0 | Fäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Hoya | Hoya carnosa | 0.7 | Beide epiphytisch; ähnliche Pflege | `compatible_with` |
| Epipremnum | Epipremnum aureum | 0.7 | Ähnliche Wuchsform, Hänger | `compatible_with` |
| Schlumbergera | Schlumbergera truncata | 0.9 | Gleiche Familie, Waldkaktus | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Wüstenkakteen | Opuntia spp., Mammillaria spp. | Rhipsalis braucht mehr Feuchtigkeit und weniger Licht | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Korallenkaktus | Rhipsalis cereuscula | Gleiche Gattung | Kompaktere, korallenartige Triebsegmente |
| Weihnachtskaktus | Schlumbergera truncata | Gleiche Familie, ähnlicher Waldkaktus-Charakter | Spektakulärere Blüte |
| Hoya | Hoya carnosa | Ähnliche Hängeform | Schöne Blüten, duftend |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Rhipsalis baccifera,Mistelkaktus;Spaghetti-Kaktus;Mistletoe Cactus,Cactaceae,Rhipsalis,perennial,day_neutral,herb,fibrous,10a;10b;11a;11b;12a;12b,0.0,"Tropisches Amerika, Westafrika, Sri Lanka",yes,3,12,20,90,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [OurHouseplants — Mistletoe Cactus](https://www.ourhouseplants.com/plants/mistletoe-cactus-rhipsalis-baccifera) — Pflegehinweise
2. [Gardenia.net — Rhipsalis baccifera](https://www.gardenia.net/plant/rhipsalis-baccifera-mistletoe-cactus-grow-care-guide) — Kulturdaten
3. [NC State Extension — Rhipsalis baccifera](https://plants.ces.ncsu.edu/plants/rhipsalis-baccifera/) — Botanische Einordnung
4. [Smart Garden Guide — Rhipsalis Care](https://smartgardenguide.com/rhipsalis-care-mistletoe-cactus/) — Substrat, Schädlinge
5. [Healthy Houseplants — Mistletoe Cactus](https://www.healthyhouseplants.com/indoor-houseplants/how-to-grow-and-care-for-the-mistletoe-cactus-rhipsalis-baccifera/) — Temperatur, Feuchtigkeit
