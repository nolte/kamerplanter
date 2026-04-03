# Bauernhortensie — Hydrangea macrophylla

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Hortensien, Lubera Bauernhortensie, Pflanzen-Kölle Hortensien, Gartenratgeber Hortensien

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hydrangea macrophylla | `species.scientific_name` |
| Volksnamen (DE/EN) | Bauernhortensie, Ballhortensie, Hortensie; Bigleaf Hydrangea, French Hydrangea | `species.common_names` |
| Familie | Hydrangeaceae | `species.family` → `botanical_families.name` |
| Gattung | Hydrangea | `species.genus` |
| Ordnung | Cornales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 6a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis ca. -15°C (alte Holzsorten); in Norddeutschland Zone 7b–8a empfehle Winterschutz für Blütenknospen; Knospen sind frostempfindlicher als der Strauch selbst; neue "winterharte" Sorten ('Endless Summer') blühen auch am Jahrestrieb | `species.hardiness_detail` |
| Heimat | Japan, China, Korea | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**BESONDERHEIT — Blütenfarbe:** Bei blauen/violetten Sorten bestimmt der pH-Wert und Aluminiumgehalt die Blütenfarbe. pH < 5,5 + Alaun = blaue Blüten; pH 6,5–7,0 = rosa Blüten. Regelmäßig Rhododendronerde oder Torf (pH 4,5–5,5) verwenden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Pflanzung als Containerpflanze; Mai oder September/Oktober) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Blüten für Trockengestaltung) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 (je nach Sorte) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Hydrangin, Cyanoglykoside | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Kontaktdermatitis möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (VORSICHT: Blüht am vorjährigen Holz! Nur tote Zweige und verblühte Blütenköpfe entfernen; NIE stark zurückschneiden) | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (verwelkte Blütenköpfe erst im Frühjahr entfernen — Winterschutz!) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–200 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 100–150 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Saure Rhododendronerde oder Moorbeete-Erde; pH 4,5–5,5 (blau) / 6,0–7,0 (rosa); kalkarmes Regenwasser | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–150 | 1 | false | false | high |
| Austrieb | 21–35 | 2 | false | false | low |
| Vegetativ | 42–70 | 3 | false | false | medium |
| Blüte | 60–120 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (Hortensien sind sehr durstig!) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hortensien-Dünger organisch | Compo Bio | organisch | 100–150 g/Pflanze | April–Juli | Hortensien |
| Rhododendron-Dünger | Neudorff Azet | organisch-sauer | 80–120 g/Pflanze | April, Juni | Sauerstoff-liebende Sträucher |

#### Mineralisch

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Hortensien-Blau-Dünger | Compo | mineralisch+Alaun | + Alaun | 1 | Blüte (für Blaufärbung) |
| Eisenchelat | Flori d'Or | Fe-Supplement | — | 2 | bei Chlorose |

### 3.2 Besondere Hinweise zur Düngung

Hortensien NUR zwischen April und Juli düngen. Kein Dünger nach August — Holzreife ist wichtig für Winterhärte. Für blaue Blüten: saure Rhododendronerde + Alaun 2–3 g/L Gießwasser monatlich. Chlorose (Gelbblätter) bei zu hohem pH → Eisenchelat + Rhododendron-Erde. IMMER mit kalkarmem Wasser (Regenwasser) gießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | temperate | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | NUR kalkarmes Wasser oder Regenwasser! Leitungswasser erhöht pH und macht Blüten rosa; verursacht Chlorose | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4, 6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Winterschutz entfernen | Nach letztem Frost; vorsichtig | hoch |
| Mär–Apr | Rückschnitt | NUR verblühte und tote Stiele; Schnitt so wenig wie möglich | hoch |
| Apr | Erste Düngung | Hortensien-Dünger | mittel |
| Apr | pH prüfen | Boden pH messen; bei Bedarf ansäuern | hoch |
| Jun | Zweite Düngung | Hortensien-Dünger | mittel |
| Jul–Okt | Blüte | Bewässerung nie vergessen; Hortensien welken schnell | hoch |
| Okt | Winterschutz | Blütenköpfe stehen lassen; Laub anhäufen; Topf isolieren | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 (Kübelpflanze) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Silbrig gepunktete Blätter | leaf | vegetative, flowering | medium |
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen | shoot | vegetative | easy |
| Schildlaus | Pulvinaria hydrangeae | Braune Schuppen am Holz | stem, bark | alle | difficult |
| Weichhautmilbe | Phytonemus pallidus | Verdrehte, kleine Blätter | shoot | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 5–10 | vegetative |
| Chlorose | physiologisch | Gelbe Blätter, grüne Adern | pH zu hoch; Fe-Mangel | — | alle |
| Grauschimmel | fungal (Botrytis) | Braune, faulende Blüten | Feuchtigkeit | 3–7 | flowering |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Gehölze (Hydrangeaceae) |
| Empfohlene Vorfrucht | — (Dauergehölz) |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | keine |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rhododendron | Rhododendron spp. | 0.8 | Gleiche Bodenvoraussetzungen; saure Erde | `compatible_with` |
| Farn | Dryopteris spp. | 0.8 | Gleiches Feuchtebedürfnis; Schattenpflanze | `compatible_with` |
| Astilbe | Astilbe spp. | 0.8 | Gleiches Standortprofil; Halbschatten | `compatible_with` |
| Hosta | Hosta spp. | 0.8 | Halbschatten; Bodendecker; feuchte Böden | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Lavendel | Lavandula angustifolia | Komplett unterschiedliche Standortansprüche (trocken vs. feucht) | severe | `incompatible_with` |
| Rosmarin | Salvia rosmarinus | Mediterran trocken vs. Hortensien feucht | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Hydrangea macrophylla |
|-----|-------------------|-------------|----------------------------------------|
| Rispenhortensie | Hydrangea paniculata | Gleiche Gattung | Winterhärter bis -30°C; keine Schnittprobleme |
| Gartenhortensie 'Endless Summer' | Hydrangea macrophylla | Gleiche Art | Blüht auch am Jahrestrieb; winterhärter |
| Kletterhortensie | Hydrangea anomala ssp. petiolaris | Gleiche Gattung | Kletterpflanze; sehr robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,bloom_months,pruning_type,pruning_months
Hydrangea macrophylla,"Bauernhortensie;Ballhortensie;Hortensie;Bigleaf Hydrangea",Hydrangeaceae,Hydrangea,perennial,day_neutral,shrub,fibrous,"6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Japan, China, Korea",yes,30,30,200,200,125,limited,yes,false,false,heavy_feeder,half_hardy,"6;7;8;9;10",spring_pruning,"3;4"
```

---

## Quellenverzeichnis

1. [Plantura Hortensien überwintern](https://www.plantura.garden/gehoelze/hortensien/hortensien-ueberwintern) — Winterschutz, Pflege
2. [Lubera Bauernhortensie](https://www.lubera.com/de/gartenbuch/bauernhortensie-pflege-schneiden-standort-ueberwintern-p3228) — Pflege, Schnitt, Überwinterung
3. [Pflanzen-Kölle Hortensien](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-hortensien-richtig/) — Pflege, Düngung
4. [Gartenratgeber Hortensien](https://www.gartenratgeber.net/pflanzen/hortensien-ueberwintern.html) — Überwinterung
