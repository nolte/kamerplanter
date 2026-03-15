# Rhabarber — Rheum rhabarbarum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Rhabarber, Lubera Rhabarber 13 Tipps, Pflanzen-Kölle Rhabarber, Meine-Ernte.de Rhabarber

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rheum rhabarbarum | `species.scientific_name` |
| Volksnamen (DE/EN) | Rhabarber, Gemüserhabarber; Rhubarb, Garden Rhubarb | `species.common_names` |
| Familie | Polygonaceae | `species.family` → `botanical_families.name` |
| Gattung | Rheum | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis −25 °C; benötigt Kältephasen für gutes Wachstum (Vernalisierung); ideal für Norddeutschland | `species.hardiness_detail` |
| Heimat | Zentralasien (China, Sibirien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Pflanzung von Rhizomteilen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 4, 5, 6 (traditionell bis Johannistag; erstes Jahr nicht ernten!) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (Blütenstand sollte abgeschnitten werden!) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true (BLÄTTER giftig — nur Stiele essbar!) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Blätter (hochgiftig!), Blüten; Stiele essbar | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Oxalsäure (Blätter: 0.5–1% Oxalsäure); Anthrachinone | `species.toxicity.toxic_compounds` |
| Schweregrad | severe (Blätter) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Blütenstände SOFORT abschneiden sobald sichtbar) | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6, 11 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (sehr große Kübel min. 50 L) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 50–80 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–120 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80–100 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung | Tiefgründige, humose, gut durchlässige Erde; pH 5,5–6,5; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe / Dormanz | 90–120 | 1 | false | false | high |
| Frühjahrsaustrieb | 21–35 | 2 | false | false | medium |
| Ernte-Phase | 42–60 | 3 | false | true | high |
| Sommer-Regeneration | 90–120 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Ernte-Phase (April–Juni)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 (halbschattig verträglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |
| Austrieb | 3:1:2 | 1.2–1.8 | 5.5–6.5 | 100 | 50 | — | 3 |
| Ernte | 2:1:2 | 1.0–1.5 | 5.5–6.5 | 80 | 50 | — | 2 |
| Regeneration | 3:1:2 | 1.5–2.0 | 5.5–6.5 | 120 | 60 | — | 3 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Reifer Stallmist | — | organisch | 5–10 L/m² | Herbst/Winter (um die Pflanze, NICHT aufs Herz!) |
| Kompost | eigen | organisch | 5–8 L/m² | Herbst |
| Hornspäne | Oscorna | organisch-N | 80–100 g/m² | Frühjahr nach der Ernte |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Gemüsedünger | Compo | base | 14-7-17 | 60–80 g/m² | Nach der Ernte (Jun) |

### 3.2 Besondere Hinweise zur Düngung

Rhabarber ist Starkzehrer mit hohem Stickstoffbedarf. Wichtig: Dünger NIE direkt auf das Herzstück legen (Fäulnis!). Die wichtigste Düngephase ist NACH der Ernte im Juni, wenn die Pflanze für die nächste Saison Reservestoffe aufbaut. Stallmist im Herbst und Hornspäne im Frühjahr sind die beste Strategie.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Regelmäßig feucht; bei Trockenheit verholzt der Stiel; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 6–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Standzeit 10 Jahre; alle 10 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Mulch entfernen | Auftauen lassen; Mulch zur Seite räumen | mittel |
| Mär | Frühjahrsdüngung | Hornspäne einarbeiten | hoch |
| Apr–Jun | Ernte | Stiele drehen (nicht abschneiden); immer 3–4 Stiele stehen lassen | hoch |
| Mai–Jun | Blütenstände abschneiden | Sofort abschneiden sobald sichtbar — spart Energie | hoch |
| Jun | Erntestopp | Johanni-Regel: nach dem 24. Juni Ernte beenden | hoch |
| Jun–Aug | Regeneration | Gut gießen und düngen; stehen lassen | mittel |
| Nov | Wintervorbereitung | Laub abschneiden; Kompost/Mist um die Krone legen | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch (Kompost/Mist um die Krone) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis fabae u.a. | Kolonien, Kräuselung | leaf | vegetative | easy |
| Schnecken | Arion spp. | Fraßschäden | leaf, stem | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Phytophthora) | Welke, braune Wurzeln | Staunässe | 7–14 | all |
| Echter Mehltau | fungal | Weißer Belag | Trockene Hitze | 7–14 | summer |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Spinat | Spinacia oleracea | 0.8 | Bodenbeschattung; gleiche Bedürfnisse | `compatible_with` |
| Zwiebeln | Allium cepa | 0.7 | Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Mangold | Beta vulgaris subsp. vulgaris | Ähnlich hoher Oxalsäuregehalt; Konkurrenz um Nährstoffe bei eng benachbarter Pflanzung | mild | `incompatible_with` |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months
Rheum rhabarbarum,"Rhabarber;Gemüserhabarber;Rhubarb;Garden Rhubarb",Polygonaceae,Rheum,perennial,long_day,herb,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Zentralasien",limited,65,40,150,120,90,no,limited,false,false,heavy_feeder,hardy,"4;5;6"
```

---

## Quellenverzeichnis

1. [Rhabarber Pflanzenportrait — Plantura](https://www.plantura.garden/gemuese/rhabarber/rhabarber-pflanzenportrait) — Stammdaten, Toxizität
2. [13 Tipps zum Rhabarber — Lubera](https://www.lubera.com/de/gartenbuch/die-13-wichtigsten-tipps-zum-rhabarber-rheum-rhabarbarum-p626) — Praxis-Tipps
3. [Rhabarber pflegen — Pflanzen-Kölle](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-rhabarber-richtig/) — Düngung
4. [Rhabarber — Meine-Ernte.de](https://www.meine-ernte.de/pflanzen-a-z/obst/rhabarber/) — Ernte, Lagerung
