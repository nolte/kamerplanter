# Himbeere — Rubus idaeus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** NaturaDB Rubus idaeus, Baumschule Weber, Baumschule Newgarden, Plantura Himbeere

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rubus idaeus | `species.scientific_name` |
| Volksnamen (DE/EN) | Himbeere, Gemeine Himbeere; Raspberry | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Rubus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −25 °C; in Norddeutschland problemlos; Sommerhimbeeren benötigen anderen Schnitt als Herbsthimbeeren | `species.hardiness_detail` |
| Heimat | Europa, Asien | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Pflanzung von Wurzelausläufern) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (vegetative Vermehrung üblich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (Sommerhimbeere), 8, 9, 10 (Herbsthimbeere) | `species.harvest_months` |
| Blütemonate | 5, 6 (Sommerhimbeere), 7, 8 (Herbsthimbeere) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Stacheln) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Sommerhimbeere: nach Ernte fruktifizierende Ruten bodennah abschneiden; Herbsthimbeere: Ende Februar/März alle Ruten bodennah abschneiden) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (Sommerhimbeere nach Ernte), 2, 3 (Herbsthimbeere im Winter/Frühjahr) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (große Kübel, min. 40 L) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50 cm in Reihe, 150–200 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Drahtrahmen oder Pfosten 1,5 m hoch) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humose, leicht saure Erde pH 5,5–6,5; kein Kalk; Mulch auf Oberfläche | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe / Dormanz | 90–120 | 1 | false | false | high |
| Neuaustrieb | 21–42 | 2 | false | false | medium |
| Vegetativ (Rutenbildung) | 60–90 | 3 | false | false | high |
| Blüte | 21–28 | 4 | false | false | medium |
| Fruchtreife | 28–56 | 5 | false | true | high |
| Nachblüte / Erholungsphase | 30–60 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ & Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |
| Neuaustrieb | 3:1:2 | 1.0–1.5 | 5.5–6.5 | 100 | 50 | — | 3 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 5.5–6.5 | 120 | 60 | — | 3 |
| Fruchtreife | 1:2:3 | 1.0–1.5 | 5.5–6.5 | 100 | 50 | — | 2 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–5 L/m² | Frühjahr (Mulch-Schicht) |
| Hornspäne | Oscorna | organisch-N | 60–80 g/m² | Frühjahr |
| Heidelbeer-/Rhododendrondünger | diverse | organisch-sauer | nach Herstellerangabe | Frühjahr + Sommer |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Beerensträucher-Dünger | Compo | base | 10-4-20 | 60–80 g/m² | Frühjahr |
| Schwefelsaures Kali | diverse | supplement | 0-0-50+18S | 20–30 g/m² | Fruchtreife |

### 3.2 Besondere Hinweise zur Düngung

Himbeeren bevorzugen leicht saure Böden (pH 5,5–6,5) — daher schwefelsaure Dünger statt Kalk. Mulchschicht aus Rindenmulch oder Stroh stabilisiert Bodenfeuchtigkeit und Bodenstruktur. Stickstoffbetonung im Frühjahr fördert Rutenbildung. Kalium-Schwerpunkt zur Fruchtreife.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies Wasser bevorzugt (erhöht pH); Regenwasser ideal | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Dauerpflanze; Verjüngung alle 8–10 Jahre) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Schnitt (Herbsthimbeere) | Alle Ruten bodennah abschneiden | hoch |
| Mär | Frühjahrsdüngung | Hornspäne + Kompost einarbeiten | hoch |
| Apr | Mulchen | 5–8 cm Stroh oder Rindenmulch | mittel |
| Mai–Jun | Triebpflege | Überschüssige Wurzelausläufer entfernen | mittel |
| Jun–Aug | Schnitt (Sommerhimbeere nach Ernte) | Abgeerntete zweijährige Ruten bodennah entfernen | hoch |
| Jun–Aug | Ernte | Täglich reife Früchte ernten | hoch |
| Sep–Okt | Ernte (Herbsthimbeere) | Herbstsorten bis Frost ernten | hoch |
| Nov | Wintervorbereitung | Junge Ruten an Spalier befestigen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (im Beet); Ruten ggf. mit Vlies | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune (Herbsthimbeere: alle Ruten) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2, 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Himbeerkäfer | Byturus tomentosus | Larven in Früchten (Made in der Frucht) | fruit | flowering, ripening | difficult |
| Blattlaus | Amphorophora idaei | Kolonien, Kräuselung, Virusübertragung | leaf, stem | vegetative | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Gelbpunkte (bei Trockenheit) | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel auf Früchten | Feuchtigkeit, Verletzungen | 3–7 | ripening |
| Echter Mehltau | fungal (Sphaerotheca macularis) | Weißer Belag auf Blättern | Trockene Tage | 7–14 | vegetative |
| Rutenkrankheit (Didymella) | fungal | Violette Flecken an Ruten, Absterben | Verletzungen, Feuchtigkeit | 14–21 | all |
| Himbeer-Ringfleckenvirus | viral | Mosaikmuster, Verkümmerung | Blattlausübertragung | — | all |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer | Blattläuse | 5–10 | 7–14 |
| Phytoseiulus persimilis | Spinnmilbe | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Befallene Ruten entfernen | cultural | — | Befallene Ruten sofort abschneiden | 0 | Rutenkrankheit |
| Kaolin-Ton | cultural | Kaolin | Sprühen auf Früchte | 0 | Himbeerkäfer |
| Pyrethrum | biological | Pyrethrin | Sprühen | 1 | Blattläuse, Himbeerkäfer |
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 3 | Blattläuse, Spinnmilbe |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Rosengewächse (Rosaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte oder Gründüngung |
| Empfohlene Nachfrucht | — (Dauerpflanze, Standzeit 10–15 Jahre) |
| Anbaupause (Jahre) | 5–7 Jahre nach Roden (Bodenmüdigkeit!) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Schützt vor Pilzkrankheiten | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Insektenabwehr, Bestäuberanlocken | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Gleiche Pilzkrankheiten möglich | moderate | `incompatible_with` |
| Tomate | Solanum lycopersicum | Gleiche Viren und Pilze | moderate | `incompatible_with` |
| Brombeere | Rubus fruticosus | Gleiche Schädlinge; Hybridisierung möglich | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Himbeere |
|-----|-------------------|-------------|---------------------------|
| Brombeere | Rubus fruticosus | Gleiche Gattung | Stärker, höherer Ertrag |
| Taybeere | Rubus fruticosus × idaeus | Hybrid | Größere Früchte, weniger Schädlinge |
| Stachelbeere | Ribes uva-crispa | Beerensträucher | Frühere Reifezeit |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Rubus idaeus,"Himbeere;Gemeine Himbeere;Raspberry",Rosaceae,Rubus,perennial,day_neutral,shrub,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",-0.1,"Europa, Asien",limited,50,40,200,100,50,no,limited,false,true,medium_feeder,hardy,"6;7;8;9;10","5;6;7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type,berry_type
Meeker,Rubus idaeus,WSU,1967,"high_yield;firm_fruit",–,,open_pollinated,summer_bearing
Autumn Bliss,Rubus idaeus,HRI East Malling,1983,"autumn;primocane",–,,open_pollinated,autumn_bearing
Glen Ample,Rubus idaeus,SCRI,1996,"spine_free;large_fruit",–,,open_pollinated,summer_bearing
```

---

## Quellenverzeichnis

1. [NaturaDB Rubus idaeus](https://www.naturadb.de/pflanzen/rubus-idaeus/) — Stammdaten
2. [Baumschule Weber Rubus idaeus](https://www.weber-baumschule.de/de-de/artikel/394/rubus-idaeus) — Pflegehinweise
3. [Baumschule Newgarden Himbeere](https://www.baumschule-newgarden.de/obst-fruechte/himbeere-rubus-idaeus/) — Sortenwahl
4. [Plantura Himbeere](https://www.plantura.garden/) — Schnittanleitung
