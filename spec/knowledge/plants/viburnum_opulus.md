# Gewöhnlicher Schneeball — Viburnum opulus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartenheinz Gemeiner Schneeball, Lubera Schneeballstrauch, Plantura Schneeball, Naturadb Viburnum opulus, Gartenratgeber Schneeball

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Viburnum opulus | `species.scientific_name` |
| Volksnamen (DE/EN) | Gewöhnlicher Schneeball, Gemeiner Schneeball; Guelder-rose | `species.common_names` |
| Familie | Adoxaceae | `species.family` → `botanical_families.name` |
| Gattung | Viburnum | `species.genus` |
| Ordnung | Dipsacales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; absolut winterhart in ganz Norddeutschland; einheimischer Wildstrauch | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Zentralasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Beeren für Wildvögel; rote Beeren Oktober–November giftig für Menschen) | `species.harvest_months` |
| Blütemonate | 5, 6 (Mai–Juni; weiße Doldenrispen) | `species.bloom_months` |

**Hinweis:** Viburnum opulus ist ein wichtiger Vogelnährgehölz — die roten Beeren werden von über 60 Vogelarten gefressen. Für Menschen und Haustiere giftig (roh; gekocht verarbeitet weniger problematisch).

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Halbverholzte Stecklinge im Juli/August, 15 cm lang, gut bewurzelnd. Absenker im Frühjahr.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Beeren (roh), Samen, Rinde; Blätter weniger | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Viburnin, Viopudsid (Cyanogene Glykoside) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Rohe Beeren verursachen Erbrechen und Durchfall. Nur wenige Beeren sind giftig — Kinder trotzdem fernhalten. Gekocht können Beeren verarbeitet werden (traditionell Marmelade in Osteuropa, mit Vorsicht).

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6 (nach der Blüte im Juni) | `species.pruning_months` |

**Hinweis:** Schneeball blüht auf vorjährigem Holz — Schnitt NUR direkt nach der Blüte. Kein Rückschnitt im Herbst oder Winter (vernichtet die Blütenknospen für nächstes Jahr). Verjüngungsschnitt alle 5–7 Jahre: älteste Triebe bodennah entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 200–500 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 200–400 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–300 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale, nährstoffreiche Gartenerde; pH 5,5–7,0; feuchtigkeitsspeichernd | — |

**Standort:** Sonne bis Halbschatten; feuchte bis nasse Böden; ideal an Teichrändern oder Gewässernähe. Heimisch in Erlenbrüchen und Feuchtgehölzen.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | high |
| Blüte | 21–30 | 2 | false | false | high |
| Vegetatives Wachstum | 90–120 | 3 | false | false | high |
| Beerenreife | 60–90 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 3000–8000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Blüte/Vegetativ | 1:1:1 | 0.6–1.0 | 5.5–7.0 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | organisch | 4–6 L/m² | März/Oktober | Bodenverbesserung |
| Mulch (Rindenmulch) | diverse | organisch | 5–8 cm Schicht | Frühjahr | Feuchtigkeitsspeicher |
| Hornspäne (bei Bedarf) | Oscorna | organisch | 30–50 g/m² | April | Nur bei Mangelsymptomen |

### 3.2 Besondere Hinweise zur Düngung

Viburnum opulus ist ein genügsamer Einheimischer und braucht auf normalen Gartenböden KEINE gezielte Düngung. Mulchen reicht völlig. Zu viel Stickstoff schadet (weiche Triebe, mehr Schädlingsbefall). Nur bei sichtbaren Mangelsymptomen düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 6.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; mag feuchte Standorte; bei Trockenheit gießen; optimal an Gewässernähe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 180 (kaum nötig) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 (kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jun | Schnitt nach Blüte | Leicht formen; älteste Triebe entfernen | mittel |
| Sep–Nov | Beeren reifen | Dekorativ; für Vögel lassen | niedrig |
| Mär | Verjüngungsschnitt | Alle 5–7 Jahre; alte Triebe bodennah | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schneeball-Blattläuse | Aphis viburni | Starke Kolonien; zusammengerollte Blätter; Honigtau; Ameisen | leaf, shoot | vegetative (Mai–Juni) | easy |
| Viburnum-Blattfloh | Psyllidae | Wachsartige Ausscheidungen; Blattschäden | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Wärme | 7–10 | vegetative (Sommer) |
| Blattflecken | fungal | Braune Flecken | Feuchtigkeit | 7–14 | vegetative |

**Blattläuse:** Schneeball-Blattläuse können massiv auftreten, schwächen aber selten die Pflanze ernsthaft. Starker Wasserstrahl zur Bekämpfung; Natürliche Feinde (Marienkäfer) fördern.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer | Blattläuse | natürliche Förderung | sofort |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Wasserstrahl | cultural | — | Kräftiger Strahl gegen Blattlauskolonien | 0 | Blattläuse |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse |
| Sonniger Standort | cultural | — | Sonne reduziert Mehltau | 0 | Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Heimische Sträucher |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Holunder | Sambucus nigra | 0.9 | Heimische Mischhecke; Insekten, Vögel | `compatible_with` |
| Weißdorn | Crataegus monogyna | 0.9 | Heimische Mischhecke; Bienenweide | `compatible_with` |
| Faulbaum | Frangula alnus | 0.8 | Feuchter Standort; heimisch | `compatible_with` |
| Schlehe | Prunus spinosa | 0.8 | Heimische Mischhecke | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Viburnum opulus |
|-----|-------------------|-------------|-----------------------------------|
| Wolliger Schneeball | Viburnum lantana | Gleiches Genus | Trockener Standort; kalkliebend |
| Duftschneeball | Viburnum carlesii | Gleiches Genus | Herrlicher Duft; kleinere Form |
| Winterschneeball | Viburnum x bodnantense | Gleiches Genus | Winterblüher Oktober–März |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Viburnum opulus,"Gewöhnlicher Schneeball;Gemeiner Schneeball;Guelder-rose",Adoxaceae,Viburnum,perennial,day_neutral,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Europa, Nordafrika, Zentralasien",limited,45,40,400,300,250,no,no,false,false,light_feeder,false,hardy,"5;6"
```

---

## Quellenverzeichnis

1. [Gartenheinz — Gemeiner Schneeball](https://www.gartenheinz.de/pflanzen/straeucher/schneeball/gemeiner-schneeball/) — Steckbrief
2. [Lubera — Schneeballstrauch](https://www.lubera.com/de/gartenbuch/schneeballstrauch-pflanzen-pflegen-p2910) — Pflege
3. [Plantura — Gewöhnlicher Schneeball](https://www.plantura.garden/gehoelze/schneeball/gewoehnlicher-schneeball) — Standort, Pflege
4. [Naturadb — Viburnum opulus](https://www.naturadb.de/pflanzen/viburnum-opulus/) — Ökologischer Wert
5. [Gartenratgeber — Schneeball](https://www.gartenratgeber.net/pflanzen/schneeball-duftschneeball-winterschneeball.html) — Kulturdaten
