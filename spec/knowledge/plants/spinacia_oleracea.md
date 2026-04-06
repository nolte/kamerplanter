# Spinat — Spinacia oleracea

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Spinat, Gartendialog.de, Samen.de, Meine-Ernte.de

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Spinacia oleracea | `species.scientific_name` |
| Volksnamen (DE/EN) | Spinat, Echter Spinat; Spinach | `species.common_names` |
| Familie | Amaranthaceae | `species.family` → `botanical_families.name` |
| Gattung | Spinacia | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterspinatsorten überstehen −10 °C bis −15 °C; schießt bei langen Tagen >14h schnell | `species.hardiness_detail` |
| Heimat | Westasien (Persien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -30 (kann 4–6 Wochen vor letztem Frost gesät werden) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 2, 3, 4, 5, 8, 9, 10 (Frühling und Herbst) | `species.direct_sow_months` |
| Erntemonate | 4, 5, 6, 9, 10, 11 | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (bei Langtag, schießen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Oxalsäure (bei sehr hohem Verzehr: Nierensteine-Risiko) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5, 9, 10 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–25 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 15–20 | `species.spacing_cm` |
| Indoor-Anbau | limited (Fensterbank) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (für Frühsaat empfehlenswert) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, lockere Erde; pH 6,5–7,5; gut durchlässig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Rosetten-Wachstum | 21–35 | 3 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Rosetten-Wachstum & Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 (Halbschatten toleriert!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–17 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 (verhindert Schießen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 (kühle Temperaturen bevorzugt) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 7.0 | — | — | — | — |
| Sämling | 2:1:1 | 0.8–1.2 | 6.5–7.0 | 80 | 30 | — | 2 |
| Rosetten-Wachstum | 3:1:2 | 1.0–1.5 | 6.5–7.5 | 100 | 40 | — | 3 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–4 L/m² | Vor der Aussaat |
| Brennnesseljauche | selbst | organisch-N | 1:10 verdünnt | 1× nach Auflaufen |

#### Mineralisch (nur bei Bedarf)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Blattdünger Blattgrün | Compo | supplement | 7-2-5 | 20 ml/10L | Wachstum |

### 3.2 Besondere Hinweise zur Düngung

Spinat tendiert zur Nitratspeicherung — daher organische Düngung bevorzugen und Mineraldünger mit hohem Stickstoffanteil meiden. Nitratgehalt im Spinat wird durch Ernte am Morgen, bei bewölktem Wetter oder vor Sonnenaufgang erhöht — Ernte am Nachmittag nach Sonnenstunden senkt den Nitratgehalt (Licht treibt Nitratreduktase). Kalkung bei pH unter 6,5. Spinat mag keine Staunässe.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig feucht; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–5, 8–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Frühaussaat | Im Frühbeet oder Gewächshaus direkt säen | mittel |
| Mär–Apr | Direktsaat Frühjahr | Im Freien 2 cm tief, 20 cm Reihen | hoch |
| Apr–Mai | Ernte Frühsatz | Blätter von außen nach innen ernten | hoch |
| Mai | Sommerspinat schießt | Schießende Pflanzen entfernen oder als Gründüngung einarbeiten | mittel |
| Aug–Sep | Herbstaussaat | Für Herbst- und Winterspinat | hoch |
| Sep–Nov | Herbst-Ernte | Laufend ernten bis Frost | hoch |
| Nov–Mär | Winterspinatsorten | Frostschutzsorten bleiben stehen; geschützt mit Vlies | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Myzus persicae u.a. | Kolonien, Kräuselung, Honigtau | leaf | vegetative | easy |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Gelbpunkte (bei Trockenheit) | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | fungal (Peronospora farinosa f.sp. spinaciae) | Gelbliche Flecken oben, violett-grauer Belag unten | Feuchtigkeit, kühle Nächte | 5–10 | seedling, vegetative |
| Schwarzbeinigkeit | fungal (Pythium spp.) | Einschnürung am Stängelgrund | Staunässe, kalt | 3–7 | seedling |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Reihenabstand einhalten | cultural | — | 20 cm Abstand | 0 | Mehltau, Luftzirkulation |
| Neemöl | biological | Azadirachtin | Sprühen, 0.3% | 3 | Blattläuse, Spinnmilbe |
| Fruchtfolge (2 Jahre) | cultural | — | Keine Amaranthaceen 2 Jahre | 0 | Mehltau-Dauersporen |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Fuchsschwanzgewächse (Amaranthaceae) |
| Empfohlene Vorfrucht | Tomaten, Kohlarten (Starkzehrer) |
| Empfohlene Nachfrucht | Bohnen, Erbsen (N-Fixierer) oder Kohlarten |
| Anbaupause (Jahre) | 2 Jahre keine Amaranthaceen (Spinat, Mangold, Rote Bete) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Erdbeere | Fragaria × ananassa | 0.8 | Bodenbeschattung, platzsparend | `compatible_with` |
| Zwiebeln | Allium cepa | 0.7 | Schädlingsabwehr | `compatible_with` |
| Radieschen | Raphanus sativus | 0.8 | Schnell-Ernte zwischen Spinatreihen | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Gleiche Bedürfnisse, gute Kombination | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Mangold | Beta vulgaris | Gleiche Familie, gleiche Krankheiten | moderate | `incompatible_with` |
| Rote Bete | Beta vulgaris | Gleiche Familie | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Spinat |
|-----|-------------------|-------------|--------------------------|
| Mangold | Beta vulgaris subsp. vulgaris | Ähnliche Verwendung | Wärmetoleranter, schießt nicht so schnell |
| Neuseeländer Spinat | Tetragonia tetragonioides | Ähnliche Verwendung | Wärmeliebend, schießt nicht |
| Guter Heinrich | Chenopodium bonus-henricus | Gleiche Familie | Perennial, pflegeleicht |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Spinacia oleracea,"Spinat;Echter Spinat;Spinach",Amaranthaceae,Spinacia,annual,long_day,herb,taproot,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Westasien (Persien)",yes,8,15,40,25,18,limited,yes,false,false,medium_feeder,hardy,"2;3;4;5;8;9;10","4;5;6;9;10;11"
```

---

## Quellenverzeichnis

1. [Spinat anbauen — Plantura](https://www.plantura.garden/gemuese/spinat/spinat-anbauen) — Anbaupraxis
2. [Spinat anbauen — Gartendialog.de](https://www.gartendialog.de/spinat-anbau/) — Pflege, Schädlinge
3. [Spinat optimal aussäen — Samen.de](https://samen.de/blog/spinat-optimal-aussaeen-fruehjahr-und-herbst-im-fokus.html) — Aussaatzeiten
4. [Spinat anbauen, pflegen, ernten — meine-ernte.de](https://www.meine-ernte.de/pflanzen-a-z/gemuese/spinat/) — Lagerung
