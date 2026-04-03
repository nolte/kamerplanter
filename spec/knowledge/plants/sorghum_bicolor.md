# Sorghum / Hirse — Sorghum bicolor

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, FAO Sorghum Crop Profile, University of Nebraska-Lincoln Extension, ICRISAT (International Crops Research Institute for Semi-Arid Tropics), Bayerische LfL Sorghumhirse

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Sorghum bicolor | `species.scientific_name` |
| Volksnamen (DE/EN) | Sorghum, Mohrenhirse, Großhirse; Sorghum, Great Millet, Guinea Corn | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Sorghum | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 7a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; Keimtemperatur min. 15°C (Bodentemperatur); optimale Wachstumstemperatur 25–35°C; stirbt bei Frost; in Mitteleuropa als Sommerkorn ab Ende Mai | `species.hardiness_detail` |
| Heimat | Nordostafrika (Äthiopien, Sudan); domestiziert ca. 3000–4000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.4 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**Allelopathie-Hinweis:** Sorghum bildet Sorgoleone (allelochemischer Stoff) im Wurzelsekret — hemmt Unkrautkeimung wirksam. Als Mulch und Gründüngung daher als natürlicher Unkrautunterdrücker wertvoll. Effekt hält 2–4 Wochen nach Einarbeitung an.

**C4-Photosynthese:** Sorghum nutzt C4-Metabolismus — extrem effiziente Wassernutzung und Hitzetoleranz. Bei 35°C Tageshöchsttemperatur wächst Sorghum stärker als Mais. Ideal für trockene Standorte.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (Anzucht im Warmhaus; Umpflanzen nach Frostende) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14–21 (Bodentemperatur mind. 15°C; besser 18°C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 9, 10 | `species.harvest_months` |
| Blütemonate | 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (Jungpflanzen und gestresste Pflanzen; Dhurrin-Hydrolyse zu HCN) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (Jungpflanzen und gestresste Pflanzen; Dhurrin-Hydrolyse zu HCN) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Jungpflanzen (Dhurrin; cyanogenes Glycosid; bei Stress oder Frost; Weidehaltung beachten) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Dhurrin (cyanogenes Glycosid; v.a. in Jungpflanzen und Stresssituationen) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (nur Jungpflanzen / Stresssituation; ausgereifte Körner unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 (sehr tiefe Wurzeln) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–400 (sortenabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–60 × 70–90 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (hohe Sorten windgefährdet; aber Selbststützer) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lehmige Erde; pH 5,5–7,5; tiefe Töpfe; trockenheitstolerante Erde | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ / Bestockung | 30–60 | 3 | false | false | high |
| Rispenschieben / Blüte | 20–30 | 4 | false | false | low |
| Kornfüllung | 25–35 | 5 | false | false | medium |
| Reife | 14–21 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 22–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–28 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ / Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | >12 (Langtagbedingungen verzögern Blüte; Kurztagblüher) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 28–38 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–28 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–14 (sehr trockenheitstolerant) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1200 | `requirement_profiles.light_ppfd_target` |
| Photoperiode (Stunden) | ≤12 (Kurztagbedingungen für Blüteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 5.5–7.5 | — | — |
| Sämling | 2:1:2 | 0.6–1.0 | 5.5–7.5 | 60 | 25 |
| Vegetativ | 4:1:3 | 1.2–2.0 | 5.5–7.5 | 120 | 50 |
| Blüte | 1:2:3 | 1.0–1.8 | 5.5–7.5 | 100 | 50 |
| Reife | 0:1:2 | 0.6–1.0 | 5.5–7.5 | 60 | 30 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kalkammonsalpeter | diverse | Granulat | 27-0-0 | 30–50 g/m² | Vegetativ |
| NPK-Volldünger | diverse | Granulat | 14-14-14 | 30–50 g/m² | Grunddüngung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | diverse | organisch | 60–100 g/m² | Vor Saat |
| Kompost | eigen | organisch | 4–6 L/m² | Herbst/Frühjahr |

### 3.2 Besondere Hinweise zur Düngung

Sorghum hat einen sehr hohen Kalium-Bedarf. Trockenheitstoleranz bedeutet NICHT Nährstofftolerant — bei ausreichender Wasserversorgung ist der Nährstoffbedarf hoch. Überzeugend hohe Stickstoffeffizienz im Vergleich zu Mais.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 (sehr trockenheitstolerant) | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 21–28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Anzucht | Vorkultur im Warmhaus (28–32°C); Saattiefe 2–3 cm | mittel |
| Mai–Jun | Auspflanzung | Nach letztem Frost; Bodentemperatur >15°C | hoch |
| Jul | Düngung | N-Gabe zur Rispenschiebung vorbereiten | mittel |
| Aug–Sep | Blüte / Rispenschieben | Beobachtung; Vogelschutz (Vögel lieben Rispenhirse) | mittel |
| Sep–Okt | Ernte | Körner hart und trocken; Rispen schneiden | hoch |
| Okt–Nov | Einarbeitung | Biomasse hacken und einarbeiten; Sorgoleone-Effekt nutzen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Blattläuse | Schizaphis graminum | Kolonien; Gelbfärbung | Blatt | Sämling, Vegetativ |
| Hirse-Bohrwurm | Busseola fusca | Totes Herz; Fraß im Halm | Trieb, Halm | Sämling |
| Stare / Vögel | Sturnus vulgaris | Körnerfrass an der Rispe | Rispe | Reife |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Sorghumrost | fungal (Puccinia purpurea) | Rote-braune Pusteln auf Blättern | feucht-warm |
| Kornmutternkrankheit | fungal (Sporisorium spp.) | Befallene Körner durch Pilz ersetzt | Saatgutbefall |
| Echter Mehltau | fungal (Blumeria graminis) | Weißgrauer Belag | trocken-warm |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Saatgutbeizung | chemical | Fludioxonil | Beize | — | Kornmuttern |
| Vogelschutznetze | cultural | — | Rispe abnetzen | 0 | Vögel |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Rost, Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Getreide / Hirse (Poaceae) |
| Empfohlene Vorfrucht | Leguminosen (Soja, Erbse); Raps |
| Empfohlene Nachfrucht | Hülsenfrüchte; Gemüse; Leguminosen |
| Anbaupause (Jahre) | 2–3 Jahre auf gleichem Standort |

**Besonderheit Unkrautunterdrückung:** Sorghum-Biomasse (Mulch, Stroh) hemmt Unkrautkeimung durch Sorgoleone. Bei Einarbeitung als Gründüngung auf nächste Folgekulturen achten — Keimhemmung kann auch Nutzpflanzen betreffen (Möhren, Zwiebeln empfindlich).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sojabohne | Glycine max | 0.8 | Klassisches Getreide-Leguminosen-Gemenge; N-Fixierung | `compatible_with` |
| Schwarzaugenbohne | Vigna unguiculata | 0.8 | Trockenheitstolerantes Gemenge; tropisch | `compatible_with` |
| Sesam | Sesamum indicum | 0.7 | Trockenheitsangepasstes Gemenge; Insektenweide | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Möhre | Daucus carota | Sorgoleone hemmt Möhrenkeimung | moderate | `incompatible_with` |
| Kopfsalat | Lactuca sativa | Sorgoleone-Hemmung | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Sorghum |
|-----|-------------------|-------------|--------------------------|
| Mais | Zea mays | C4-Getreide; Sommeranbau | Höherer Kornertrag in Mitteleuropa |
| Rispenhirse | Panicum miliaceum | Kleines Korn; hitzetolerant | Frühere Reife; glutenfreies Korn |
| Zuckerhirse | Sorghum bicolor var. saccharatum | Unterart | Zuckerreicher Stängel für Saft/Sirup |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Sorghum bicolor,"Sorghum;Mohrenhirse;Großhirse;Great Millet;Guinea Corn",Poaceae,Sorghum,annual,short_day,herb,fibrous,"7a;7b;8a;8b;9a;9b;10a;10b;11a;11b",0.4,"Nordostafrika",limited,no,no,false,false,heavy_feeder,true,tender,"5;6","9;10","8;9"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Biomass 133,Sorghum bicolor,"biomass_type;tall;high_yield;drought_tolerant",120,hybrid
BMR-6,Sorghum bicolor,"forage_type;low_lignin;digestible",110,open_pollinated
Bepari,Sorghum bicolor,"grain_sorghum;medium_tall;early",105,open_pollinated
```

---

## Quellenverzeichnis

1. [ICRISAT Sorghum](https://www.icrisat.org/crop/sorghum/) — Taxonomie, Eigenschaften, globale Anbau
2. [USDA PLANTS — Sorghum bicolor](https://plants.usda.gov/plant-profile/SOBI2) — Taxonomie
3. [University of Nebraska Extension — Sorghum Production](https://extension.unl.edu) — Nährstoffbedarf
4. [FAO Sorghum Crop Profile](https://www.fao.org/sorghum) — Globale Anbausysteme
5. [Bayerische LfL — Sorghumhirse](https://www.lfl.bayern.de/ipz/getreide) — Mitteleuropa-Anbau
