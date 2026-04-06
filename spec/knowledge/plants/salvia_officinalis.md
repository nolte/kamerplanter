# Echter Salbei — Salvia officinalis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Compo Salbei, Samen.de Salbei, Gartenratgeber Salbei, Pflanzen-Kölle Salbei

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Salvia officinalis | `species.scientific_name` |
| Volksnamen (DE/EN) | Echter Salbei, Küchensalbei, Heilsalbei; Common Sage, Garden Sage | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Salvia | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -15°C (Sorte 'Berggarten' bis -20°C); in Norddeutschland Zone 7b-8a mit leichtem Mulchschutz zuverlässig; bei Kahlfrösten ohne Schneebedeckung gelegentliche Ausfälle | `species.hardiness_detail` |
| Heimat | Mittelmeerraum (Dalmatien, Balkan) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Vorkultur Feb–Mär; Keimtemperatur 18–22°C) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (Blätter ganzjährig erntbar; aromatischste vor Blüte) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Thujone in ätherischem Öl: in großen Destillat-Mengen problematisch; Küchenmenge unbedenklich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Thujone (in Küchenmengen harmlos) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (Rückschnitt nach dem Winter; NIE ins alte Holz) | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (nach letztem Frost; bei neuem Austrieb) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kalkhaltige, durchlässige Kräutererde mit Sand; pH 6,5–7,5; kein Torf | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–21 | 1 | false | false | low |
| Sämling | 28–42 | 2 | false | false | low |
| Vegetativ (Aufbau) | 56–90 | 3 | false | true | medium |
| Blüte | 28–42 | 4 | false | true | medium |
| Reife/Dormanz | 90–180 (Winter) | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Aufbau 1. Jahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (trockenverträglich; Staunässe vermeiden) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.6 | 6.5 | 60 | 20 | — | 1 |
| Vegetativ | 1:0:1 | 0.6–1.0 | 6.5–7.0 | 80 | 30 | — | 1 |
| Blüte | 0:1:1 | 0.5–0.8 | 6.5–7.0 | 60 | 30 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kräuterdünger organisch | Neudorff Azet | organisch | 40–60 g/Pflanze | April | mediterrane Kräuter |
| Reifer Kompost | eigen | organisch | 1–2 L/Pflanze | Frühjahr | alle |
| Horngrieß | Oscorna | organisch-N | 30–50 g/Pflanze | Frühjahr | light_feeder |

#### Mineralisch (bei Bedarf)

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Kräuterdünger flüssig | Compo | mineralisch | 7-3-6 | 1 | Vegetativ |

### 3.2 Besondere Hinweise zur Düngung

Salbei WENIG düngen! Auf mageren, gut kalkhaltig-durchlässigen Böden bildet er die meisten aromatischen ätherischen Öle (Thujon, Camphor, Cineol). Überdüngung macht die Blätter groß und wässrig — Aroma leidet stark. Im ersten Jahr einmalige Kompostgabe bei der Pflanzung ausreichend. Im zweiten und dritten Jahr jährlich eine leichte Frühjahrsdüngung. Niemals im Herbst düngen — fördert weiches, frostanfälliges Holz.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 (sehr selten bis gar nicht gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Trocken bevorzugt; Staunässe ist tödlich; kalkhaltiges Wasser verträglich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 (1× jährlich im Frühjahr) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur | Aussaat bei 18–22°C; Keimung langsam (14–21 Tage) | mittel |
| Mär–Apr | Rückschnitt | Überwinterte Pflanzen: auf neuen Austrieb hin zurückschneiden; nie ins alte Holz | hoch |
| Mai (nach 15.) | Auspflanzen | Jungpflanzen ab 10 cm; sonniger, kalkiger Standort | hoch |
| Mai–Jun | Blüte | Optional: Blütentriebe entfernen für mehr Blattwachstum; oder für Bienen blühen lassen | niedrig |
| Jun–Aug | Ernte | Triebspitzen abschneiden; fördert Buschigkeit | mittel |
| Okt | Wintervorbereitung | Mulch aus Laub/Reisig um den Stamm; Topfpflanzen schützen | mittel |
| Nov–Feb | Winterruhe | Kaum gießen; kein Düngen; hell und kühl bei Topfpflanze | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (draußen mit Mulchschutz) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | — | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | — | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste; Silberflecken auf Blättern | leaf | vegetative (Trockenheit) | medium |
| Wanzenwanzen | Lygus spp. | Deformierte Blätter | leaf, shoot | vegetative | difficult |
| Schnecken | Arion spp. | Fraß an Jungpflanzen | leaf | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag, v.a. oben | Trockenheit + Wärme | 5–10 | vegetative, flowering |
| Grauschimmel | fungal (Botrytis cinerea) | Grau-brauner Schimmel | Feuchtigkeit, enge Pflanzung | 3–7 | seedling, dormancy |
| Salbei-Rost | fungal (Puccinia labiatarum) | Orange-braune Pusteln | Feuchtigkeit | 7–14 | vegetative, flowering |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0,5% Sprühlösung | 3 | Spinnmilben, Mehltau |
| Schnittmaßnahmen | cultural | — | Befallene Triebe entfernen | 0 | Grauschimmel, Rost |
| Schwefelspritzung | chemical | Schwefel | 0,3–0,5% Lösung | 14 | Mehltau, Rost |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Mediterrane Kräuter (Lamiaceae) |
| Empfohlene Vorfrucht | Beliebig; kein spezieller Vorfrucht-Anspruch |
| Empfohlene Nachfrucht | Beliebig; Starkzehrer profitieren von Nährstoff-arm bleibendem Boden |
| Anbaupause (Jahre) | keine Beschränkung |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Möhre | Daucus carota | 0.8 | Abwehr der Möhrenfliege durch Salbei-Duft | `compatible_with` |
| Kohl | Brassica oleracea | 0.8 | Kohlweißling-Abwehr durch Salbei-Duft | `compatible_with` |
| Rosmarin | Salvia rosmarinus | 0.9 | Gleiche Familie; gleicher Standortbedarf | `compatible_with` |
| Thymian | Thymus vulgaris | 0.9 | Gleiche Standortbedürfnisse; Kräuterbeet | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Schädlingsabwehr; Aromaförderung | `compatible_with` |
| Rose | Rosa spp. | 0.7 | Schädlingsabwehr durch Salbei-Duft | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Konkurrierende Aromastoffe; keine gegenseitige Förderung | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Fenchel hemmt Wachstum von Lamiaceae | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Salbei |
|-----|-------------------|-------------|--------------------------|
| Ziersalbei | Salvia officinalis 'Purpurascens' | Gleiche Art | Dekorativ; ähnliches Aroma |
| Ananas-Salbei | Salvia elegans | Gleiche Gattung | Fruchtiges Aroma; nur Balkon/Topf |
| Oregano | Origanum vulgare | Gleiche Familie | Wärmeliebender; ähnliche Standortansprüche |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Salvia officinalis,"Echter Salbei;Küchensalbei;Common Sage;Garden Sage",Lamiaceae,Salvia,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Mittelmeerraum, Dalmatien",yes,8,20,80,70,45,limited,yes,false,false,light_feeder,half_hardy,"5;6;7;8;9","5;6;7",spring_pruning,"3;4"
```

---

## Quellenverzeichnis

1. [Compo Salbei](https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/salbei) — Anbau, Pflege, Düngung
2. [Samen.de Salbei](https://samen.de/blog/tipps-fuer-den-erfolgreichen-salbei-anbau.html) — Anbau-Praxis
3. [Gartenratgeber Salbei](https://www.gartenratgeber.net/pflanzen/salbei.html) — Pflege, Rückschnitt, Überwinterung
4. [Samen.de Begleitpflanzen Salbei](https://samen.de/blog/ideale-begleitpflanzen-fuer-salbei-im-kraeutergarten.html) — Mischkultur
