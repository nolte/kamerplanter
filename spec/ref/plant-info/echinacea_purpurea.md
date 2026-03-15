# Purpur-Sonnenhut — Echinacea purpurea

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Sonnenhut, Compo Purpur-Sonnenhut, Lubera Roter Sonnenhut, Naturadb Echinacea purpurea

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Echinacea purpurea | `species.scientific_name` |
| Volksnamen (DE/EN) | Purpur-Sonnenhut, Roter Sonnenhut; Purple Coneflower | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Echinacea | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis -40°C (USDA 3a); in Norddeutschland absolute Dauerfrosteignung; Pflanzenstängel als Winterschutz stehen lassen (auch Vogelfutter) | `species.hardiness_detail` |
| Heimat | Nordamerika (Präriegebiete) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 (Vorkultur Feb–Mär; Kältebehandlung (Stratifikation) 2–3 Wochen bei 5°C fördert Keimung) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (März bis Juli im Freiland möglich) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9, 10 (Blüten; Wurzeln erst ab 3. Jahr ernten) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (Alkylamide und Polysaccharide = Wirkstoffe; Phytopharmakon) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Korbblütler-Kreuzallergie möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Asteraceae-Allergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (NIE im Herbst; Stängel als Überwinterungsschutz und Vogelfutter; Rückschnitt erst im März) | `species.pruning_type` |
| Rückschnitt-Monate | 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, durchlässige Gartenerde mit Kompost; pH 6,0–7,0; sandiger Lehm | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–21 | 1 | false | false | medium |
| Sämling (1. Jahr) | 60–90 | 2 | false | false | medium |
| Vegetativ (2. Jahr+) | 42–70 | 3 | false | false | high |
| Blüte | 56–84 | 4 | false | true | high |
| Winterruhe | 120–180 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (trockenverträglich nach Etablierung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 3–5 L/m² | Frühjahr | Stauden allg. |
| Hornspäne | Oscorna | organisch-N | 30–50 g/m² | April | light_feeder |

### 3.2 Besondere Hinweise zur Düngung

Echinacea ist Schwachzehrer und gedeiht auf mäßig nährstoffreichen Böden (nach dem natürlichen Prärielebensraum). Auf zu fetten Böden wächst sie üppig, fällt aber öfter um und ist weniger kompakt. Jährliche Kompostgabe im Frühjahr reicht. Im ersten Jahr nach Pflanzung keine Düngung notwendig wenn Boden vorbereitet wurde.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Trockenverträglich nach Etablierung; junger Pflanzen im 1. Jahr regelmäßig gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 (1× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur | Aussaat mit 2–4 Wochen Stratifikation (Kühlschrank) | mittel |
| Mär | Rückschnitt | Alte Stängel bodennah entfernen | mittel |
| Apr | Kompostgabe | 1–2 Handvoll Kompost pro Pflanze | niedrig |
| Mai–Jun | Auspflanzen | Sonniger bis halbschattiger Standort | hoch |
| Jul–Okt | Blüte genießen | Bienenpflanze; Samenstände als Vogelfutter | niedrig |
| Okt–Mär | Stängel stehen lassen | Überwinterungsstruktur + Vogelfutter (Körnerfresser) | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | — | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

Echinacea ist sehr robust und kaum von Schädlingen oder Krankheiten befallen.

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Gelegentlich kleine Kolonien | shoot | seedling (selten) | easy |
| Schmierläuse | Pseudococcidae | Wachsige Kolonien (sehr selten) | stem | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Hitze | 5–10 | vegetative (selten) |
| Wurzelfäule | fungal | Welke; schwarze Wurzeln | Staunässe | 7–14 | seedling |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Stauden (Asteraceae) |
| Empfohlene Vorfrucht | Beliebig; bevorzugt nährstoffarmer Standort |
| Empfohlene Nachfrucht | Beliebig |
| Anbaupause (Jahre) | Keine; Dauerstaude (8–10+ Jahre Standzeit) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rudbeckia | Rudbeckia fulgida | 0.9 | Gleiche Ökologie; optisch harmonisch | `compatible_with` |
| Fetthenne | Sedum spectabile | 0.8 | Bestäuber-Magnet; gleichzeitig Blütezeit | `compatible_with` |
| Astern | Aster spp. | 0.8 | Nachblüte; Spätsommerstaude | `compatible_with` |
| Gräser (Ziergräser) | Miscanthus, Pennisetum | 0.8 | Naturgarten-Charakter; Bodenbefestigung | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bienenweide; Trockenheit-tolerant | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Echinacea purpurea |
|-----|-------------------|-------------|--------------------------------------|
| Schmaler Sonnenhut | Echinacea angustifolia | Gleiche Gattung | Stärkere Heilwirkung; schmalere Blätter |
| Blasser Sonnenhut | Echinacea pallida | Gleiche Gattung | Hellrosa Blüten; etwas weniger robust |
| Sonnenauge | Rudbeckia fulgida | Gleiche Familie | Gelbe Blüten; früher blühend |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Echinacea purpurea,"Purpur-Sonnenhut;Roter Sonnenhut;Purple Coneflower",Asteraceae,Echinacea,perennial,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Nordamerika, Prärie",limited,25,30,120,60,45,no,limited,false,false,light_feeder,hardy,"7;8;9;10","7;8;9;10",spring_pruning,"3"
```

---

## Quellenverzeichnis

1. [Plantura Sonnenhut](https://www.plantura.garden/blumen-stauden/sonnenhut/sonnenhut-pflanzenportrait) — Pflege, Schnitt, Überwinterung
2. [Compo Purpur-Sonnenhut](https://www.compo.de/ratgeber/pflanzen/balkon-kuebelpflanzen/purpur-sonnenhut) — Anbau, Pflege
3. [Lubera Roter Sonnenhut](https://www.lubera.com/de/gartenbuch/roter-sonnenhut-echinacea-pflege-p2744) — Pflege, Verwendung
4. [Naturadb Echinacea purpurea](https://www.naturadb.de/pflanzen/echinacea-purpurea/) — Steckbrief, Eigenschaften
