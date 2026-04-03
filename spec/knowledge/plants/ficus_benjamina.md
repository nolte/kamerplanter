# Birkenfeige — Ficus benjamina

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Royal Horticultural Society](https://www.rhs.org.uk/), [Plantura Ficus benjamina care](https://plantura.garden/uk/houseplants/ficus-benjamina/ficus-benjamina-care), [Gardeners World BBC](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-weeping-fig/), [ASPCA](https://www.aspca.org/), [University of Florida IFAS](https://edis.ifas.ufl.edu/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ficus benjamina | `species.scientific_name` |
| Volksnamen (DE/EN) | Birkenfeige, Benjaminfeige, Zimmerficus; Weeping Fig, Benjamin Fig | `species.common_names` |
| Familie | Moraceae | `species.family` → `botanical_families.name` |
| Gattung | Ficus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20+ (Indoor: 10–15) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 13°C, optimal 18–24°C. Sehr empfindlich gegenüber Zugluft, Kälte und Standortwechsel — führt zu massivem Blattfall. | `species.hardiness_detail` |
| Heimat | Tropisches Asien (Indien, Sri Lanka, Südostasien, Australien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.7 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, trichloroethylene, xylene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Ficus benjamina ist bekannt für seine extreme Sensibilität gegenüber Standortwechseln. Ein einmaliges Umstellen kann massiven Blattfall (bis zu 50% der Blätter) auslösen — dies ist eine normale Stressreaktion und kein Zeichen des Absterbens. Nach 4–6 Wochen treibt die Pflanze am neuen Standort neu aus.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt (Früchte Indoor nie) | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor nicht) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (10–15 cm, halbverholzt) brauchen Bodenwärme (22–25°C) und Bewurzelungshormon. Bewurzelungszeit 4–8 Wochen. Luftschichtung (Air Layering) an älteren Zweigen möglich und zuverlässiger. Milchsaft nach dem Schnitt einige Minuten abtrocknen lassen, dann in feuchtes Substrat stecken.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, latex | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | ficin, ficusin, latex_proteins | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Latex/Milchsaft — Kreuzreaktion mit Latex-Allergie möglich!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Pollen kann Allergien auslösen, Indoor selten relevant) | `species.allergen_info.pollen_allergen` |

**Wichtig:** Bei bekannter Latex-Allergie (z.B. Chirurgenhandschuh-Allergie) besteht erhöhtes Risiko einer Kreuzreaktion auf Ficus-Latex. Handschuhe beim Schneiden tragen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

**Hinweis:** Rückschnitt im Frühjahr fördert buschigen Wuchs. Milchsaft austretende Schnittstellen mit Watte oder Holzkohle behandeln. Maximal 1/3 der Blattmasse pro Rückschnitt entfernen, sonst starker Blattverlust.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 (Indoor; in Natur bis 30 m) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Sommer, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Zimmerpflanzenerde mit guter Drainage, pH 6.0–6.5. 20–30% Perlite beimischen. Schwere Tonerde vermeiden. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–6.5 | 100 | 40 | 2 |
| Winterruhe | 0:0:0 | 0.0–0.4 | 6.0–6.5 | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne fein | Oscorna | organisch | 3 g/L Substrat | Frühling |
| Kompost (reif) | Eigenherstellung | organisch | 20% Substratanteil beim Umtopfen | Frühling |

### 3.2 Besondere Hinweise zur Düngung

Ficus benjamina reagiert empfindlich auf Überdüngung mit Blattflecken und Blattfall. Dünger auf Maßstab der Pflanzengröße abstimmen. In der Wachstumsphase alle 3–4 Wochen düngen, im Winter komplett pausieren. Stickstoffbetonte Dünger (N-P-K 3:1:2) fördern dichtes Laubwerk.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.8 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Lauwarmes, abgestandenes Leitungswasser; keine kalten Wassergüsse (Kälteschock → Blattfall) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21–28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Rückschnitt | Korrekturrückschnitt vor Wachstumsbeginn | mittel |
| Mär | Umtopfen | Bei Bedarf (Wurzeln aus Topf) in nächstgrößeren Topf | niedrig |
| Mär | Düngung starten | Wachstumsphase beginnen | mittel |
| Apr–Sep | Regelmäßig gießen | Oberstes Erdreich leicht antrocknen lassen | hoch |
| Mai–Aug | Ggf. Sommerbalkon | Windgeschützter, halbschattiger Platz möglich | optional |
| Sep | Einräumen vorbereiten | Pflanzen akklimatisieren vor dem Einräumen | mittel |
| Okt | Einräumen | Vor Frost hereinholen, Standort NICHT mehr wechseln | hoch |
| Okt–Feb | Sparsameres Gießen | Substrat zwischen Güssen stärker antrocknen lassen | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Blattvergilbung | leaf | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken, Honigtau | leaf, stem | easy |
| Schildlaus | Coccus hesperidum | Braune Schalen auf Stängeln, Honigtau | stem, leaf | medium |
| Tripse | Frankliniella occidentalis | Silbrige Blattstreifen, Schwarzpunkte | leaf | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Verticillium-Welke | fungal (Verticillium dahliae) | Einzelne Äste welken, dunkle Verfärbung im Holz | Bodenpilz, Wunden |
| Anthraknose | fungal | Braune Blattränder/-spitzen, schwarze Ränder | Hohe Luftfeuchtigkeit |
| Rußtaupilz | fungal | Schwarzer Belag auf Blättern | Folge von Schildlausbefall |
| Wurzelfäule | fungal | Welke trotz feuchtem Substrat, fauler Geruch | Überbewässerung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5%, alle 7 Tage | 0 | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Kaliseife | Sprühen, alle 5–7 Tage | 0 | Spinnmilbe, Blattläuse |
| Paraffinöl | chemical | Paraffinöl | Einmalig im Winter | 0 | Schildläuse (überwinternde) |
| Systeminsektizid | chemical | Imidacloprid | Stäbchen ins Substrat | 14 | Schildläuse, Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ficus benjamina |
|-----|-------------------|-------------|----------------------------------|
| Geigenfeige | Ficus lyrata | Gleiche Gattung, dekorative Blätter | Weniger Blattfall bei Standortwechsel |
| Gummibaum | Ficus elastica | Gleiche Gattung, robuster | Deutlich pflegeleichter, weniger empfindlich |
| Ficus Daniella | Ficus benjamina 'Daniella' | Sorte mit dunkelgrünen, festeren Blättern | Weniger Blattfall bei Zugluft als die Grundart |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,air_purification_score
Ficus benjamina,"Birkenfeige;Benjaminfeige;Zimmerficus;Weeping Fig",Moraceae,Ficus,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b",0.0,"Tropisches Asien",yes,10-30,25,150-300,60-150,yes,limited,false,false,medium_feeder,0.7
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Danielle,Ficus benjamina,"ornamental;dark_leaves;robust",clone
Starlight,Ficus benjamina,"ornamental;variegated;cream_white",clone
Twilight,Ficus benjamina,"ornamental;variegated;small_leaves",clone
```

---

## Quellenverzeichnis

1. [Plantura — Ficus benjamina Pflege](https://plantura.garden/uk/houseplants/ficus-benjamina/ficus-benjamina-care) — Pflegehinweise, Rückschnitt
2. [BBC Gardeners World — Weeping Fig](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-weeping-fig/) — Kulturempfehlungen
3. [ASPCA Animal Poison Control](https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants) — Toxizität
4. [Mikrobs — Pests & Diseases Ficus benjamina](https://mikrobs.com/blogs/news/taking-care-of-ficus-benjamina) — Schädlings-/Krankheitsdaten
5. [Gardenia.net — Ficus benjamina](https://www.gardenia.net/plant/ficus-benjamina) — Standortdaten
