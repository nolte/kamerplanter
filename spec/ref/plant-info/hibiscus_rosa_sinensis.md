# Zimmerhibiskus — Hibiscus rosa-sinensis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Pflanzen-Kölle – Zimmerhibiskus](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-zimmerhibiskus-richtig/), [Plantura – Hibiskus düngen](https://www.plantura.garden/gehoelze/hibiskus/hibiskus-duengen), [Gartendialog – Zimmerhibiskus](https://www.gartendialog.de/zimmerhibiskus-pflege/), [Gartencenter Lubera – Hibiscus](https://www.lubera.com/de/gartenbuch/hibiscus-rosa-sinensis-p1519)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hibiscus rosa-sinensis | `species.scientific_name` |
| Volksnamen (DE/EN) | Zimmerhibiskus, Chinesischer Roseneibisch; Chinese Hibiscus, Tropical Hibiscus | `species.common_names` |
| Familie | Malvaceae | `species.family` → `botanical_families.name` |
| Gattung | Hibiscus | `species.genus` |
| Ordnung | Malvales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; Überwinterung bei 10–15°C | `species.hardiness_detail` |
| Heimat | Asien (ursprünglich vermutlich China/Südostasien, genaue Herkunft unbekannt) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (lange Blütezeit im Sommer) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (nach ASPCA nicht giftig; bei grossem Verzehr leichte gastrointestinale Beschwerden möglich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–200 (in Natur bis 500 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, gut drainierte Kübelpflanzenerde; pH 6.0–7.0; jährliches Umtopfen im Frühjahr | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | medium |
| Austrieb (Frühling) | 21–42 | 2 | false | false | low |
| Blüte (Sommer) | 120–180 | 3 | false | false | medium |
| Abreife (Herbst) | 30–60 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — |
| Austrieb | 3:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 |
| Blüte | 1:2:3 | 1.5–2.5 | 6.0–6.5 | 150 | 60 | B: 0.5 | 3 |
| Abreife | 0:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | — | 1 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Austrieb | time_based | — | Temperaturanstieg März |
| Austrieb → Blüte | time_based | 21–42 Tage | Neue Knospen sichtbar |
| Blüte → Abreife | time_based | 120–180 Tage | Herbst, Temperaturen sinken |
| Abreife → Winterruhe | time_based | 30–60 Tage | Einwintern Oktober/November |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Kübel)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Hibiskus-Dünger | Compo | base | 8-6-11 + Spurenelemente | wöchentlich | 1 | blüte, austrieb |
| Blühpflanzendünger | Substral | base | 4-6-8 | 5 ml/L | 1 | blüte |

#### Organisch (Kübel)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | — | organisch | 80–120 g/10L Topf | Frühjahr | heavy_feeder |
| Kompost | eigen | organisch | 2–3 L/Topf | Frühjahr | alle |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| Jan–Feb | Winterruhe | 0.0 | — | Kein Dünger |
| Mär | Austrieb | 1.0–1.5 | 6.2 | Stickstoffreich starten |
| Apr–Sep | Blüte | 1.5–2.5 | 6.2 | Wöchentlich Flüssigdünger |
| Okt | Einwintern | 0.0 | — | Düngung einstellen |
| Nov–Dez | Winterruhe | 0.0 | — | Kein Dünger |

### 3.3 Mischungsreihenfolge

1. Wasser
2. Spurenelemente (CalMag)
3. Flüssigdünger (NPK)
4. pH-Kontrolle

### 3.4 Besondere Hinweise zur Düngung

Hibiscus rosa-sinensis ist ein ausgesprochener Starkzehrer — wöchentliche Düngung während der Blütezeit (April–Oktober) ist notwendig. Besonders auf Spurenelemente achten: Bor, Mangan, Molybdän. Eisenmangel (Chlorose) tritt bei zu hohem pH auf. Kein Dünger im Winter — dann ruht die Pflanze.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalk verträglich; Regenwasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (10–15°C), wenig Wasser, kein Dünger | mittel |
| Feb | Rückschnitt | Kräftiger Rückschnitt auf 30–50% der Triebe | hoch |
| Mär | Umtopfen + Düngung | Frisches Substrat, erste Düngergabe | hoch |
| Apr–Mai | Draußen stellen | Schrittweise abhärten ab 10°C | hoch |
| Jun–Sep | Blütezeit | Tägl./alle 2 Tage gießen, wöchentlich düngen, sonnig | hoch |
| Okt | Einwintern | Vor Frost hereinholen, gießen reduzieren | hoch |
| Nov–Dez | Winterpflege | Kühl, hell, minimal gießen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Gespinste, gelb-gesprenkelte Blätter | leaf | alle | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Weiße Fliegen aufgescheucht, Honigtau | leaf | vegetative, flowering | easy |
| Schildläuse | Coccus hesperidum | Braune Schuppen, klebrige Äste | stem | alle | difficult |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Gallmücken | Contarinia maculipennis | Knospen fallen ab ohne zu öffnen | flower | flowering | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Blattflecken (Cercospora) | fungal | Dunkle Flecken auf Blättern | high_humidity, waterlogging | 7–14 | alle |
| Botrytis | fungal | Grauer Schimmel auf Blüten/Knospen | high_humidity | 3–7 | flowering |
| Chlorose | physiological | Gelbe Blätter mit grünen Adern | iron/manganese_deficiency, wrong_pH | — | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Feltiella acarisuga | Spinnmilben | 10–20 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Spinnmilben, Weiße Fliege |
| Gelbkarten | cultural | — | Aufhängen | 0 | Weiße Fliege, Trauermücken |
| Duschen | mechanical | Wasser | Blätter abbrausen | 0 | Spinnmilben, Blattläuse |
| Pyrethrin | biological | Pyrethrum | Sprühen nach Anweisung | 1 | Weiße Fliege |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kübelpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Hibiscus rosa-sinensis |
|-----|-------------------|-------------|------------------------------|
| Gartenhybiskus | Hibiscus syriacus | Gleiche Gattung | Winterhart, kein Einwintern |
| Chinesische Rose | Rosa chinensis | Ähnliche Blüten | Kräftigere Rose, Dachterrasse |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Hibiscus rosa-sinensis,Zimmerhibiskus;Chinesischer Roseneibisch;Tropical Hibiscus,Malvaceae,Hibiscus,perennial,day_neutral,shrub,fibrous,9a;9b;10a;10b;11a;11b,0.0,Asien tropisch,yes,20,25,200,150,—,limited,yes,false,false
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle – Zimmerhibiskus Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-zimmerhibiskus-richtig/) — Pflege, Überwinterung
2. [Plantura – Hibiskus düngen](https://www.plantura.garden/gehoelze/hibiskus/hibiskus-duengen) — Düngung, NPK
3. [Gartendialog – Zimmerhibiskus Pflege](https://www.gartendialog.de/zimmerhibiskus-pflege/) — Vollständige Anleitung
4. [Lubera – Hibiscus rosa-sinensis](https://www.lubera.com/de/gartenbuch/hibiscus-rosa-sinensis-p1519) — Botanik, Kulturtipps
5. [Zimmerpflanzen-FAQ – Hibiscus rosa-sinensis](https://zimmerpflanzen-faq.de/hibiscus-rosa-sinensis/) — Steckbrief
