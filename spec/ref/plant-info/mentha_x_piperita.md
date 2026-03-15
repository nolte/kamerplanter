# Pfefferminze / Minze — Mentha × piperita

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Mentha spicata, Bio-Gärtner Pfefferminze, Gartenblues Pfefferminze, Gruenes-Archiv Minze

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Mentha × piperita | `species.scientific_name` |
| Volksnamen (DE/EN) | Pfefferminze, Minze; Peppermint | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Mentha | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis -25°C; Rhizome überstehen auch harte Winter; oberirdische Teile sterben ab; Neuaustrieb im Frühjahr | `species.hardiness_detail` |
| Heimat | Hybride (Mentha aquatica × Mentha spicata); Kulturpflanze; Europa | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**WICHTIG — Ausbreitung:** Pfefferminze verbreitet sich aggressiv über unterirdische Rhizome. Immer mit Rhizomsperre pflanzen (versenkter Topf ohne Boden, mind. 20 cm tief) oder in Kübel kultivieren!

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (keine Aussaat — ausschließlich vegetative Vermehrung bei Mentha × piperita; Samen kommen nicht sortenecht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (keine Direktsaat; Ableger/Topf ab April) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9, 10 (Blätter vor Blüte aromatischsten) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (Menthol kann Katzen schaden; große Mengen gefährlich) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false (geringe Mengen unbedenklich; große Mengen Magenproblem) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile (für Katzen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Menthol, Menthon (für Katzen in großen Mengen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (nach Ernte-Zyklen; nach Blüte zurückschneiden für 2. Trieb) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 (mit Rhizomsperre) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 (mit Rhizomsperre) | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humose, feuchtigkeitshaltende Kräutererde; pH 6,0–7,0; Feuchtigkeit wichtig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Neuaustrieb (Frühjahr) | 14–28 | 1 | false | false | medium |
| Vegetativ | 42–70 | 2 | false | true | high |
| Blüte | 28–42 | 3 | false | true | high |
| Rückschnitt/2. Trieb | 28–42 | 4 | false | true | high |
| Winterruhe | 90–150 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (liebt Feuchtigkeit) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Neuaustrieb | 2:1:1 | 0.6–0.8 | 6.0–7.0 | 80 | 30 | — | 2 |
| Vegetativ | 2:1:2 | 0.8–1.2 | 6.0–7.0 | 100 | 40 | — | 2 |
| Blüte | 1:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 | — | 1 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 3–4 L/m² | Frühjahr | perennial herbs |
| Horngrieß | Oscorna | organisch-N | 30–50 g/m² | Frühjahr + nach Ernte | Kräuter |
| Kräuterdünger | Neudorff Azet | organisch | 50 g/m² | April, Juli | Kräuter |

### 3.2 Besondere Hinweise zur Düngung

Pfefferminze ist mittelstark zehrend und braucht etwas mehr Nährstoffe als mediterrane Kräuter (Thymian, Rosmarin). Zu viel Stickstoff fördert üppiges Blattwachstum auf Kosten der ätherischen Öle. Maßstab: 1–2× jährliche organische Düngung im Frühjahr, nach starker Ernte etwas Horngrieß.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 (Rhizome im Boden; kaum gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Liebt Feuchtigkeit; jedoch Staunässe vermeiden; kalkarmes Wasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4, 7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 (Rhizome füllen Topf schnell) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Rhizom-Teilung | Alte Pflanzen teilen und neu einpflanzen; alle 3–4 Jahre | mittel |
| Apr | Neuaustrieb fördern | Alte Triebe bodennah abschneiden | mittel |
| Mai–Jun | Erste Ernte | Vor Blüte: aromatischste Phase | hoch |
| Jun–Aug | Blütentriebe entfernen | Fördert Blattwachstum und 2. Trieb | mittel |
| Aug–Sep | 2. Ernte | Nach Rückschnitt wieder gewachsene Triebe | mittel |
| Okt | Rückschnitt | Bodennah zurückschneiden vor Winter; Mulch | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (draußen; sehr winterhart) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste bei Trockenheit (Indoor) | leaf | vegetative (trocken) | medium |
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen | shoot | vegetative | easy |
| Pfefferminzrost | Puccinia menthae | Orange-braune Pusteln | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Pfefferminzrost | fungal (Puccinia menthae) | Orange Sporenpusteln; Blattfall | Feuchtigkeit | 7–14 | vegetative, flowering |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 5–10 | vegetative |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Befallene Triebe entfernen | cultural | — | Sofortmaßnahme bei Rost | 0 | Pfefferminzrost |
| Neupflanzung (alle 3–4 Jahre) | cultural | — | Rhizomteilung; neue Stelle | 0 | Rost-Dauersporenlager |
| Neemöl | biological | Azadirachtin | 0,5% Lösung | 3 | Blattläuse, Spinnmilben |
| Rasierklingen-Schnecken | cultural | — | Manuelle Entfernung | 0 | Schnecken meiden Minze |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Mediterrane Kräuter (Lamiaceae) |
| Empfohlene Vorfrucht | Beliebig; bevorzugt feuchten Standort |
| Empfohlene Nachfrucht | Beliebig |
| Anbaupause (Jahre) | Alle 3–4 Jahre Stelle wechseln (Rost-Sporen) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kohl | Brassica oleracea | 0.8 | Kohlweißling-Abwehr; Minze-Duft verwirrt Falter | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Schädlingsabwehr durch Minze-Aroma | `compatible_with` |
| Möhre | Daucus carota | 0.7 | Möhrenfliegen-Abwehr | `compatible_with` |
| Brennnessel | Urtica dioica | 0.7 | Beide wuchsstark; gegenseitige Konkurrenz nötig | `compatible_with` |

**Praxistipp:** Minze immer IN einem Topf oder mit Rhizomsperre (20 cm tiefer versenkter Eimer ohne Boden) pflanzen! Sonst überwuchert sie das gesamte Beet.

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Alle zartblättrigen Kräuter | div. | Minze verdrängt durch Rhizome | severe | `incompatible_with` |
| Petersilie | Petroselinum crispum | Konkurrenz und Unterdrückung | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Pfefferminze |
|-----|-------------------|-------------|-------------------------------|
| Grüne Minze | Mentha spicata | Gleiche Gattung | Weniger intensiv; mildes Aroma; kochgeeignet |
| Marokkanische Minze | Mentha spicata 'Marokko' | Gleiche Gattung | Teeminze; feines Aroma |
| Zitronenmelisse | Melissa officinalis | Gleiche Familie | Zitronen-Aroma; weniger invasiv |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Mentha × piperita,"Pfefferminze;Minze;Peppermint",Lamiaceae,Mentha,perennial,long_day,herb,rhizomatous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.2,"Europa (Hybride)",yes,8,20,80,60,35,yes,yes,false,false,medium_feeder,hardy,"5;6;7;8;9;10","6;7;8"
```

---

## Quellenverzeichnis

1. [Plantura Mentha spicata](https://www.plantura.garden/kraeuter/minze/mentha-spicata) — Anbau, Pflege, Sorten
2. [Bio-Gärtner Pfefferminze](https://www.bio-gaertner.de/pflanzen/Pfefferminze) — Ökologischer Anbau
3. [Gartenblues Pfefferminze](https://gartenblues.de/pfefferminze-mentha-x-piperita-sorten-pflanzung-schnitt-und-krankheiten/) — Sorten, Pflanzung, Krankheiten
4. [Gruenes-Archiv Minze](https://www.gruenes-archiv.de/minze-standort-anbau-und-pflege/) — Anbau, Verwendung
