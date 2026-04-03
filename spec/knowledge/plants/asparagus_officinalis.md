# Spargel — Asparagus officinalis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Spargel, NaturaDB Asparagus officinalis, Pflanzen-für-dich.de Asparagus, Selbstversorger.de Spargel

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Asparagus officinalis | `species.scientific_name` |
| Volksnamen (DE/EN) | Spargel, Gemüsespargel; Asparagus, Garden Asparagus | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Asparagus | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Rhizome winterhart bis −25 °C; in Norddeutschland problemlos; junge Triebe frostempfindlich | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Westasien | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Kronen-Pflanzung; kein Aussaat nötig) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 4, 5, 6 (nicht vor dem 3. Jahr; traditionell bis Johannistag 24. Juni) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (Farnwedel-Phase nach Ernte) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division (Rhizom-Kronen), seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (Beeren und Laub) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (Beeren und Laub) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (Stangen essbar) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Beeren (rot, Oktober) und Laub | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Saponine (Asparagosid) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (für Tiere) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning (Farnwedel nach dem ersten Frost abschneiden) | `species.pruning_type` |
| Rückschnitt-Monate | 11, 12, 2 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no (braucht festes Beet, dauerhaft) | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 60 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–150 (Farnwedel) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 cm in Reihe, 120 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung | Sandiger, tiefgründiger, gut drainierter Boden; pH 6,5–7,5; tiefe Rigole | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Dauerkulturen-Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe / Dormanz | 90–120 | 1 | false | false | high |
| Austrieb & Ernte | 60–90 | 2 | false | true | medium |
| Farnwedel-Wachstum (Assimilation) | 120–150 | 3 | false | false | high |
| Herbst / Einzug | 30–60 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Austrieb & Ernte (April–Juni)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–15 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 (Boden mind. 10 °C für Austrieb) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |
| Austrieb | 2:1:2 | 1.0–1.5 | 6.5–7.5 | 100 | 50 | — | 2 |
| Farnwedel | 3:1:2 | 1.5–2.0 | 6.5–7.5 | 120 | 60 | — | 3 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Reifer Stallmist | — | organisch | 5–8 kg/m² | Herbst/Winter |
| Kompost | eigen | organisch | 5 L/m² | Herbst |
| Hornspäne | Oscorna | organisch-N | 80–100 g/m² | Frühjahr |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| NPK-Langzeitdünger | Compo | base | 12-8-16 | 80–100 g/m² | Frühjahr |
| Patentkali | K+S | supplement | 0-0-30+10MgO | 40 g/m² | Nach Ernte |

### 3.2 Besondere Hinweise zur Düngung

Spargel ist Starkzehrer mit langer Standzeit — Boden großzügig vorbereiten (tiefe Rigole 30–40 cm, Reifkompost einarbeiten). Wichtigste Düngephase ist NACH der Ernte (Juni–September) — dann treibt die Pflanze Assimilationsorgane aus, die die nächste Ernte aufbauen. Kalkversorgung wichtig (pH 6,5–7,5). Keine Stickstoffdüngung ab September — sonst mangelnde Abhärtung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 (kaum gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Feuchte; Staunässe vermeiden (Wurzelfäule!) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 6–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Dauerpflanze, Standzeit 15–25 Jahre) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Beet vorbereiten | Dünger einarbeiten; Boden lockern | hoch |
| Apr–Jun | Ernte | Stangen täglich stechen (morgens); bis Johannistag | hoch |
| Jun | Wachstum fördern | Bewässern + Düngen nach der Ernte | hoch |
| Jun–Sep | Farnwedel-Phase | Wachstum lassen; mäht Nährstoffe für nächste Saison | mittel |
| Sep | Letzte Düngung | Keine Stickstoffdüngung mehr | hoch |
| Nov | Rückschnitt | Farnwedel nach dem ersten Frost bodennah abschneiden | mittel |
| Nov–Feb | Mulchen | Stroh oder Rindenmulch als Frostschutz für Krone | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch (5–8 cm Stroh) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spargelkäfer | Crioceris asparagi | Fraßschäden an Trieben und Farnwedeln | stem, leaf | vegetative | easy |
| Zwölfpunkt-Spargelkäfer | Crioceris duodecimpunctata | Larven fressen in Beeren | fruit | ripening | medium |
| Spargelfliege | Platyparea poeciloptera | Larvenbefall in Stangen; Stangen knicken | stem | seedling, vegetative | hard |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Botrytis-Fäule | fungal (Botrytis cinerea) | Grauer Schimmel an Stangen und Trieben | Feuchtigkeit | 3–7 | all |
| Spargel-Rostpilz | fungal (Puccinia asparagi) | Orangerote Pusteln auf Farnwedeln | Feuchtigkeit, Wärme | 7–14 | vegetative |
| Fusarium-Welke | fungal (Fusarium oxysporum) | Vergilbung, Absterben | Staunässe, verletzter Boden | 14–28 | all |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Absammeln | mechanical | — | Käfer und Eier regelmäßig absammeln | 0 | Spargelkäfer |
| Pyrethrum | biological | Pyrethrin | Sprühen | 1 | Spargelkäfer |
| Drainage | cultural | — | Staunässe vermeiden | 0 | Fusarium |
| Fruchtfolge | cultural | — | 10–15 Jahre kein Spargel nach Spargel! | 0 | Fusarium, Bodenmüdigkeit |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Gegenseitige Förderung (Klassiker!) | `compatible_with` |
| Ringelblume | Calendula officinalis | 0.8 | Nematoden-Abwehr durch Wurzelausscheidungen | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Insektenabwehr | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.8 | Förderung des Spargelwachstums | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Zwiebeln | Allium cepa | Wurzelkonkurrenz | moderate | `incompatible_with` |
| Knoblauch | Allium sativum | Allelopathische Hemmung | moderate | `incompatible_with` |

---

## 7. CSV-Import-Daten

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months
Asparagus officinalis,"Spargel;Gemüsespargel;Asparagus;Garden Asparagus",Asparagaceae,Asparagus,perennial,day_neutral,herb,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Europa, Nordafrika, Westasien",no,60,150,80,35,no,no,false,false,heavy_feeder,hardy,"4;5;6"
```

---

## Quellenverzeichnis

1. [Plantura Spargel pflanzen](https://www.plantura.garden/gemuese/spargel/spargel-pflanzen) — Anbaupraxis
2. [NaturaDB Asparagus officinalis](https://www.naturadb.de/pflanzen/asparagus-officinalis/) — Stammdaten
3. [Pflanzen-für-dich.de Asparagus officinalis](https://pflanzen-fuer-dich.de/Asparagus-officinalis) — Pflegehinweise
4. [Selbstversorger.de Spargel anbauen](https://www.selbstversorger.de/spargel-anbauen/) — Praxis-Tipps
