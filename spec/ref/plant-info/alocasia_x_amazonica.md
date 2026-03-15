# Elefantenohr, Afrikanische Maske — Alocasia × amazonica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Garden Betty](https://gardenbetty.com/alocasia-polly/), [Smart Garden Guide](https://smartgardenguide.com/alocasia-amazonica-care/), [Bloomscape](https://bloomscape.com/plant-care-guide/alocasia/), [ASPCA](https://www.aspca.org/), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-an-alocasia)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Alocasia × amazonica | `species.scientific_name` |
| Volksnamen (DE/EN) | Elefantenohr, Afrikanische Maske; African Mask Plant, Elephant Ear, Kris Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Alocasia | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Wurzelanpassungen | tuberous (Rhizomknollen als Wasserspeicher) | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (saisonale Ruhephase im Winter häufig, besonders bei kühlem Standort) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Unter 15°C Wachstumsstillstand und mögliche Dormanz. | `species.hardiness_detail` |
| Heimat | Hybride Gartenzüchtung (Alocasia longiloba × Alocasia sanderiana, Südostasien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis Taxonomie:** Alocasia × amazonica ist eine Hybridpflanze, die in den 1950er Jahren in Florida gezüchtet wurde — trotz des Namens hat sie nichts mit dem Amazonas zu tun. Die Sorte 'Polly' ist die kompaktere Züchtung der × amazonica und heute die am häufigsten im Handel erhältliche Variante. Dormanz-Phasen (Blätter absterben, Knolle überwintert) sind normal und kein Anzeichen des Absterbens.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (selten Indoor; calla-ähnliche Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, offset | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Ableger (Kindknollen) an der Mutterknolle beim Umtopfen abtrennen. Jede Kindknolle mit eigenem Triebansatz einzeln einpflanzen. Bewurzelung bei 22–24°C Bodentemperatur und hoher Luftfeuchtigkeit (80%). Dormierende Knollen im Substrat belassen — sie treiben im Frühling neu aus.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, roots | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides, oxalate_crystals | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Calciumoxalat-Kristalle verursachen Hautreizungen und Kontaktdermatitis) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WICHTIG:** Alocasia ist für Kleinkinder und Haustiere besonders gefährlich. Die Calciumoxalat-Raphiden können schwere Schwellungen im Mund- und Rachenraum verursachen (Atemwegsschwellung möglich). Bei Verdacht auf Verschlucken sofort Arzt/Tierarzt aufsuchen. In Haushalten mit Kleinkindern oder Tieren möglichst auf andere Pflanzen ausweichen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Abgestorbene Blätter an der Stängelbasis abschneiden. Keine Stumpfe stehen lassen — können faulen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–12 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 ('Polly') bis 90+ | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, windgeschützt, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockeres, gut drainiertes Substrat: Einheitserde + 30% Perlite + 10% Orchideenrinde. pH 5.5–7.0. Guter Wasserabzug zwingend (kein Staunasser Topf!). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–210 | 1 | false | false | low |
| Dormanz (Herbst/Winter — optional) | 60–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 5.5–7.0 | 100 | 50 |
| Dormanz | 0:0:0 | 0.0 | 5.5–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 2–4 Wochen in der Wachstumsphase. Im Herbst/Winter kein Dünger. Überdüngung führt zu Blattrandnekrosen. Stickstoff fördert großes, sattgrünes Laub.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser bevorzugt; Raumtemperatur; kein kaltes Leitungswasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 10 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blattvergilbung | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Blattlaus | Aphididae | Kolonien an Neutrieben | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, faulende Knollen | Überbewässerung, Staunässe |
| Blattflecken | fungal/bacterial | Braune/schwarze Flecken | Wasser auf Blättern |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Luftfeuchtigkeit erhöhen | cultural | Befeuchter | 0 | Spinnmilbe (Prävention) |
| Umtopfen | cultural | Faule Teile entfernen | 0 | Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Zebrapflanze | Alocasia zebrina | Gleiche Gattung | Auffällige Zebrastreifen-Stängel |
| Colocasia | Colocasia esculenta | Gleiche Familie, ähnliche Wuchsform | Robuster, essbare Knolle (Taro) |
| Caladium | Caladium bicolor | Gleiche Familie | Farbenfrohere Blätter, Sommerkultur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Alocasia × amazonica,"Elefantenohr;Afrikanische Maske;African Mask Plant;Elephant Ear",Araceae,Alocasia,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Hybridgartenzüchtung (A. longiloba x A. sanderiana, Suedostasien)",yes,3-12,20,30-90,30-60,yes,limited,false,medium_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Polly,Alocasia × amazonica,"ornamental;compact;dark_leaves",clone
```

---

## Quellenverzeichnis

1. [Garden Betty — Alocasia Polly](https://gardenbetty.com/alocasia-polly/) — Pflegehinweise, Dormanz
2. [Smart Garden Guide](https://smartgardenguide.com/alocasia-amazonica-care/) — Wachstumsparameter
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Bloomscape — Alocasia Care Guide](https://bloomscape.com/plant-care-guide/alocasia/) — Pflegehinweise
5. [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-an-alocasia) — Praxiswissen
