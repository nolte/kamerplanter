# Blut-Storchschnabel — Geranium sanguineum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Storchschnabel, Pflanzen-Kölle Storchschnabel, Baldur-Garten Storchschnabel, Native Plants Geranium sanguineum

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Geranium sanguineum | `species.scientific_name` |
| Volksnamen (DE/EN) | Blut-Storchschnabel, Blutroter Storchschnabel; Bloody Cranesbill | `species.common_names` |
| Familie | Geraniaceae | `species.family` → `botanical_families.name` |
| Gattung | Geranium | `species.genus` |
| Ordnung | Geraniales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; sehr robust; in Norddeutschland problemlos; halbimmergrün (Laub bleibt bei mildem Winter) | `species.hardiness_detail` |
| Heimat | Europa, Westasien; heimisch in Deutschland (Kalkfelsen, Trockenrasen) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5 | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Wildkraut; Blätter essbar) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 (lange Blütezeit mit Herbstfärbung) | `species.bloom_months` |

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
| Giftige Pflanzenteile | keine (Blätter und Blüten essbar; Heilpflanze) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (nach Erstblüte; fördert Zweitblüte) | `species.pruning_months` |

**Hinweis:** Nach der Erstblüte (Juli) auf ca. 10 cm zurückschneiden — treibt kräftig neu aus und blüht bis in den Herbst weiter. Im Frühjahr (März) altes Laub entfernen. Selbstaussaat fördern oder durch Entfernen der Samenstände regulieren.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 (12–16 Stück/m²) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, mäßig nährstoffreiche Erde; pH 6,0–7,5; auch kalkhaltig; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | medium |
| Vegetatives Wachstum | 28–42 | 2 | false | false | high |
| Blüte (Frühjahr/Sommer) | 60–90 | 3 | false | false | high |
| Rückschnitt & Regeneration | 21–35 | 4 | false | false | high |
| Herbstblüte/-Färbung | 30–60 | 5 | false | false | high |
| Winterruhe | 120–150 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Hauptphase)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–700 (Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 1:1:1 | 0.5–0.8 | 6.0–7.5 | 60 | 30 | – | 1 |
| Blüte | 1:1:2 | 0.6–1.0 | 6.0–7.5 | 60 | 30 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornmehl | Oscorna | organisch | 20–30 g/m² | März (einmalig) | light_feeder |
| Kompost (dünn) | eigen | organisch | 1–2 L/m² | März | Bodenverbesserung |

### 3.2 Besondere Hinweise zur Düngung

Geranium sanguineum ist ein ausgesprochener Schwachzehrer. Zu viel Dünger produziert übergroße Pflanzen mit wenig Blüten. Auf mageren Böden (Kalk, Sandstein) zeigt er seine beste Blütenfülle. Einmalige schwache organische Düngung im Frühjahr ausreichend — auf nährstoffreichen Gartenböden sogar gänzlich verzichtbar.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 (trockenheitsresistent nach Etablierung) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; sehr trockenheitstolerant; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 (einmalig im Jahr) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–4 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Aufräumen | Altes Laub entfernen; schwache Düngung | mittel |
| Mai–Jul | Blüte (erste) | Pinkfarbene bis blutrote Blüten | – |
| Jul | Rückschnitt | Auf 10 cm; fördert dichte neue Blattmasse und Herbstblüte | hoch |
| Aug–Okt | Herbstblüte + -färbung | Leuchtend rot-orange Herbstfärbung | – |
| Nov | Selbstaussaat regulieren | Samenstände entfernen falls keine Ausbreitung gewünscht | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

Geranium sanguineum ist sehr robust und hat kaum Schädlingsprobleme. Gelegentlich:

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | spring | easy |
| Raupen | div. Lepidoptera | Gelegentlicher Blattfraß | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

Kaum Krankheitsprobleme. Bei schlechten Standortbedingungen gelegentlich:

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + warm | 7–10 | vegetative (Spätsommer) |
| Grauschimmel | fungal (Botrytis) | Schimmel | Staunässe | 3–7 | autumn |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gute Drainage | cultural | – | Standortwahl | 0 | Grauschimmel |
| Rückschnitt (Luftzirkulation) | cultural | – | Juli | 0 | Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rittersporn | Delphinium elatum | 0.9 | Fußraumbedeckung; ergänzende Höhe | `compatible_with` |
| Fetthenne | Sedum spp. | 0.8 | Gleiche trockene Standorte | `compatible_with` |
| Frauenmantel | Alchemilla mollis | 0.8 | Schattenbereich; ergänzend | `compatible_with` |
| Ziersalbei | Salvia nemorosa | 0.8 | Gleiche Trockenheitstolerantz; blauer Kontrast | `compatible_with` |
| Schafgarbe | Achillea millefolium | 0.8 | Gleiche Bedürfnisse; Nützlinge | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Geranium sanguineum |
|-----|-------------------|-------------|----------------------------------------|
| Wiesen-Storchschnabel | Geranium pratense | Gleiche Gattung | Höher (60 cm); blau-violett; mehr Schatten |
| Kleiner Storchschnabel | Geranium pusillum | Gleiche Gattung | Sehr kompakt; selbstaussäend | – |
| Himalaya-Storchschnabel | Geranium himalayense | Gleiche Gattung | Größere Blüten; robust | – |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Geranium sanguineum,"Blut-Storchschnabel;Blutroter Storchschnabel;Bloody Cranesbill",Geraniaceae,Geranium,perennial,long_day,herb,rhizomatous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Europa, Westasien",yes,8,20,40,60,35,no,yes,false,false,light_feeder,false,hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Plantura Storchschnabel](https://www.plantura.garden/blumen-stauden/storchschnabel/storchschnabel-pflanzen-pflegen) — Pflanzung, Pflege
2. [Pflanzen-Kölle Storchschnabel](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-storchschnabel-richtig/) — Pflege
3. [Baldur-Garten Storchschnabel](https://www.baldur-garten.de/onion/content/pflege-tipps/gartenstauden/storchschnabel) — Rückschnitt
4. [Native Plants Geranium sanguineum](https://www.native-plants.de/797/blut-storchschnabel) — Wildpflanzen-Steckbrief
