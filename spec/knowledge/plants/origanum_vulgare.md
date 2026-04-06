# Oregano / Wilder Majoran — Origanum vulgare

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Oregano, Gartenrat.de Oregano, Bio-Gärtner Oregano, Naturadb Oregano

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Origanum vulgare | `species.scientific_name` |
| Volksnamen (DE/EN) | Oregano, Wilder Majoran, Dost; Oregano, Wild Marjoram | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Origanum | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Griechischer Oregano (ssp. hirtum) bis -15°C; Norddeutschland zuverlässig überwinternder Dauerstaude; mit Reisig-Abdeckung sicherer | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Vorderasien | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Aussaat Feb–Mär bei 18–22°C; sehr kleines Saatgut, nicht bedecken) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (frisch oder getrocknet; aromatischste kurz vor Blüte) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem, division | `species.propagation_methods` |
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
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Magere, kalkhaltige, durchlässige Kräutererde; pH 6,5–8,0; kein Torf; Drainagschicht | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | low |
| Sämling | 21–35 | 2 | false | false | low |
| Vegetativ (Aufbau) | 42–90 | 3 | false | true | high |
| Blüte | 42–70 | 4 | false | true | high |
| Winterruhe | 90–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Aufbau)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (ausgesprochen trockenverträglich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 7.0 | — | — | — | — |
| Sämling | 1:1:1 | 0.3–0.5 | 6.5–7.0 | 40 | 15 | — | 1 |
| Vegetativ | 1:0:1 | 0.5–0.8 | 6.5–7.5 | 60 | 25 | — | 1 |
| Blüte | 0:1:1 | 0.4–0.6 | 6.5–7.5 | 50 | 20 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Oregano ist Schwachzehrer und gedeiht auf mageren, kalkreichen Böden am besten. Auf fetten, nährstoffreichen Böden wächst er üppig, aber sein Aroma (Carvacrol, Thymol) ist deutlich schwächer. Maximal 1× jährlich im Frühjahr eine leichte organische Düngung. Niemals mineralischen Stickstoffdünger — macht Oregano wässrig und artenarm. Kalkgabe fördert das Aroma.

### 3.2 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kräuter-Dünger organisch | Neudorff Azet | organisch | 20–30 g/Pflanze | April | mediterrane Kräuter |
| Kompost (reif) | eigen | organisch | 0,5–1 L/Pflanze | April | alle Kräuter |

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 8 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Sehr trockenverträglich; eher zu wenig als zu viel; Staunässe ist fatal; leicht kalkig verträglich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 28 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Aussaat | Bei 18–22°C innen; Samen sehr klein, andrücken nicht eindecken | mittel |
| Apr | Zurückschneiden | Überwinterte Pflanzen auf neuen Austrieb kürzen | mittel |
| Mai (nach 15.) | Auspflanzen | Sonniger, magerer, kalkiger Standort | hoch |
| Jun–Aug | Ernte vor Blüte | Triebspitzen abschneiden; höchster Ölgehalt kurz vor/bei Blüte | hoch |
| Sep | Trocknen | Büschel kopfüber in warmem Luftzug trocknen | mittel |
| Okt | Winterschutz | Reisig über Pflanze legen; nicht herausschneiden | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

Oregano ist sehr robust. Starke Aromastoffe (Carvacrol, Thymol) wirken als natürliche Abwehr gegen die meisten Schädlinge.

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste (indoor/trocken) | leaf | vegetative (Trockenheit) | medium |
| Blattläuse | Aphis spp. | Kleine Kolonien (selten) | shoot | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 5–10 | vegetative |
| Wurzelfäule | fungal (Pythium spp.) | Welke, schwarze Wurzeln | Staunässe | 3–7 | alle |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Mediterrane Kräuter (Lamiaceae) |
| Empfohlene Vorfrucht | Beliebig |
| Empfohlene Nachfrucht | Beliebig |
| Anbaupause (Jahre) | keine |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Aromaverbesserung; Schädlingsabwehr | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Möhrenfliegen-Abwehr durch Duft | `compatible_with` |
| Porree | Allium porrum | 0.8 | Gegenseitige Förderung | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.8 | Kräuterbeet; Schädlingsabwehr | `compatible_with` |
| Kohl | Brassica oleracea | 0.7 | Kohlweißling-Abwehr | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Bestäuber anlocken durch Blüten | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Fenchel hemmt Lamiaceae | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Oregano |
|-----|-------------------|-------------|---------------------------|
| Griechischer Oregano | Origanum vulgare ssp. hirtum | Unterart | Stärkeres Aroma; für Pizza-Küche |
| Majoran | Origanum majorana | Gleiche Gattung | Milder; wärmeliebender; einjährig |
| Thymian | Thymus vulgaris | Gleiche Familie | Ähnliche Standortansprüche; anderes Aroma |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Origanum vulgare,"Oregano;Wilder Majoran;Dost;Wild Marjoram",Lamiaceae,Origanum,perennial,long_day,herb,rhizomatous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.1,"Mittelmeerraum, Vorderasien",yes,6,15,60,50,35,yes,yes,false,false,light_feeder,hardy,"5;6;7;8;9","6;7;8;9"
```

---

## Quellenverzeichnis

1. [Plantura Oregano](https://www.plantura.garden/kraeuter/oregano/oregano-pflegen) — Pflege, Schnitt, Überwinterung
2. [Gartenrat.de Oregano](https://gartenrat.de/oregano/) — Anbau, Trocknen
3. [Bio-Gärtner Oregano](http://www.bio-gaertner.de/pflanzen/Oregano/Anbau) — Ökologischer Anbau
4. [Naturadb Origanum vulgare](https://www.naturadb.de/pflanzen/origanum-vulgare/) — Steckbrief, Eigenschaften
