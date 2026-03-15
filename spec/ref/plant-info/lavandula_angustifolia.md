# Lavendel — Lavandula angustifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-für-dich.de Lavandula, NaturaDB Lavandula angustifolia, Plantura Lavendel, Baumschule Horstmann

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lavandula angustifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Echter Lavendel, Schmalblättriger Lavendel; English Lavender, True Lavender | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Lavandula | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −15 °C; in Norddeutschland problemlos; bei anhaltend nasser Kälte empfindlich (Staunässe tötet mehr als Frost) | `species.hardiness_detail` |
| Heimat | Westliches Mittelmeer (Frankreich, Spanien, Nordafrika) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 12–16 (Aussaat schwierig; Kauf als Jungpflanze empfohlen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (Blüten für Duftsäcke, Kochen, Tee) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy (Stecklinge); difficult (Aussaat) | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (ätherische Öle, besonders Lavendelöl) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (in größeren Mengen) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (geringe Mengen harmlos) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile, insbesondere ätherisches Öl | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Linalool, Linalylacetat | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (um 2/3; nie ins alte Holz; sonst verholzt und wird kahl) | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4, 8 (nach der Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–60 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr lichthungrig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kalkhaltig, durchlässig, mager (30% Kies/Splitt); pH 6,5–8,0; KEIN Torf | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | high |
| Frühjahrswachstum | 60–90 | 2 | false | false | medium |
| Blüte | 42–70 | 3 | false | true | high |
| Nachblüte / Herbst | 60–90 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum & Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (Volllsonne; 6–8h täglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–55 (trockene Luft bevorzugt) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 (sehr trockenverträglich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |
| Wachstum | 1:1:1 | 0.6–0.9 | 6.5–8.0 | 80 | 40 | — | 1 |
| Blüte | 0:1:1 | 0.5–0.8 | 6.5–8.0 | 60 | 30 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (sehr sparsam)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Reife Kompost (sehr wenig) | eigen | organisch | 0.3 L/Pflanze | 1× Frühjahr |

#### Mineralisch (bei Bedarf, 1× jährlich)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kräuter-Langzeitdünger | Compo | base | 6-4-8 | 5 g/Pflanze | Frühjahr |

### 3.2 Besondere Hinweise zur Düngung

Lavendel braucht kaum Dünger — auf sehr mageren, kalkreichen Böden ist er am wohlsten und duftet am intensivsten. Überdüngung (N) führt zu üppigem, weichem Wachstum mit wenig Aroma. Bei Topfkultur 1× jährlich im Frühjahr düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 12 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Hartes (kalkhaltiges) Wasser ist kein Problem; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 180 (kaum düngen!) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Rückschnitt | Um 2/3 kürzen (grünes Holz); nicht ins altes Holz schneiden | hoch |
| Mai | Auspflanzen (Neupflanzungen) | Sehr durchlässigen Boden vorbereiten | mittel |
| Jun–Aug | Ernte | Blüten vor dem vollständigen Aufblühen schneiden (höchster Öl-Gehalt) | mittel |
| Aug | Rückschnitt nach Blüte | Verblühte Blütenstände und Triebspitzen kürzen | mittel |
| Nov | Wintervorbereitung | Topfpflanzen: frostfrei stellen; im Beet: gut drainiert | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (im Beet bei guter Drainage); Kübel: kühles Frostschutzhaus | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3, 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Zikadenart | Auchenorrhyncha | Gelbe Punkte, Blattverformung (selten) | leaf | vegetative | difficult |
| Blattläuse | div. Aphiidae | Kolonien (selten; Lavendelduft schützt) | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Phytophthora, Pythium) | Welke, braune Wurzeln | Staunässe, schwerer Boden | 5–14 | all |
| Echter Mehltau | fungal | Weißlicher Belag | Feuchtigkeit | 7–14 | vegetative |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Drainage optimieren | cultural | — | Kies/Split unter Pflanzung | 0 | Wurzelfäule |
| Standortwahl | cultural | — | Vollsonne, trockener Hang | 0 | alle Krankheiten |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rose | Rosa spp. | 0.9 | Klassische Kombination; Lavendel hält Blattläuse von Rosen fern | `compatible_with` |
| Salbei | Salvia officinalis | 0.9 | Gleiche Standortansprüche | `compatible_with` |
| Rosmarin | Salvia rosmarinus | 0.9 | Mediterrane Kombination | `compatible_with` |
| Thymian | Thymus vulgaris | 0.9 | Gleiche Bedürfnisse | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Minze | Mentha spicata | Minze braucht Feuchtigkeit; Lavendel Trockenheit | moderate | `incompatible_with` |
| Hortensie | Hydrangea macrophylla | Sehr unterschiedliche Feuchtigkeitsbedürfnisse | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Lavendel |
|-----|-------------------|-------------|---------------------------|
| Speik-Lavendel | Lavandula latifolia | Gleiche Gattung | Wärmeliebender, intensiverer Duft |
| Lavandin | Lavandula × intermedia | Hybrid | Kräftiger, längere Blütenstiele, mehr Öl |
| Salbei | Salvia officinalis | Gleiche Familie, mediterran | Essbar, etwas winterhärter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Lavandula angustifolia,"Echter Lavendel;Schmalblättriger Lavendel;English Lavender",Lamiaceae,Lavandula,perennial,day_neutral,shrub,taproot,"5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Westliches Mittelmeer",yes,10,20,80,80,50,limited,yes,false,false,light_feeder,hardy,"6;7;8","6;7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hidcote,Lavandula angustifolia,–,–,"compact;deep_violet;fragrant",–,,open_pollinated
Munstead,Lavandula angustifolia,–,1916,"compact;early;classic",–,,open_pollinated
Vera,Lavandula angustifolia,–,–,"tall;classic;oil_production",–,,open_pollinated
```

---

## Quellenverzeichnis

1. [Pflanzen-für-dich.de Lavandula angustifolia](https://pflanzen-fuer-dich.de/Lavandula-angustifolia) — Stammdaten, Winterhärte
2. [NaturaDB Lavandula angustifolia Rosea](https://www.naturadb.de/pflanzen/lavandula-angustifolia-rosea/) — Pflegehinweise
3. [Baumschule Horstmann Lavendel](https://www.baumschule-horstmann.de/rosabluehender-lavendel-rosea-697_44868.html) — Sortenwahl
4. [Plantura winterharte Kräuter](https://www.plantura.garden/kraeuter/kraeuter-anbauen/winterharte-kraeuter) — Winterhärte
