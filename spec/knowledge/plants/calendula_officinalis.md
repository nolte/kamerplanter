# Ringelblume — Calendula officinalis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Wikipedia Ringelblume, NaturaDB Calendula, Lichtnelke Heilpflanze Calendula, Manufactum Calendula

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Calendula officinalis | `species.scientific_name` |
| Volksnamen (DE/EN) | Ringelblume, Sonnenwende, Garten-Ringelblume; Pot Marigold, Common Marigold | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Calendula | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt leichte Fröste (−5 °C); selbst aussämend; in Norddeutschland problemlos als Einjährige | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Südeuropa | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (verträgt leichten Frost) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 (und Herbst für Frühjahrserblühen) | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Blüten) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

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
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Harzallergene; besonders bei Korbblütler-Allergie) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Korbblütler-Allergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (verblühte Blüten regelmäßig entfernen = Deadheading) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9, 10 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 | `species.spacing_cm` |
| Indoor-Anbau | limited (Fensterbank, kühler Standort) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Kräutererde; pH 5,5–7,0; durchlässig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 21–35 | 3 | false | false | high |
| Blüte & Ernte | 60–120 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte & Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (sonnig bis halbschattig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–22 (kühle Temperaturen bevorzugt) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 1:1:1 | 0.6–0.9 | 6.0–7.0 | 60 | 30 | — | 1 |
| Vegetativ | 2:1:2 | 0.8–1.2 | 5.5–7.0 | 80 | 40 | — | 2 |
| Blüte | 1:2:2 | 0.8–1.0 | 5.5–7.0 | 70 | 35 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Ringelblume ist Schwachzehrer und gedeiht auf mageren bis mittleren Böden am besten. Auf sehr nährstoffreichen Böden oder bei starker Düngung entsteht viel Blattwerk auf Kosten der Blüten. 1× Kompost-Grunddüngung im Frühjahr reicht vollständig. Keine weiteren Dünger notwendig.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Moderat feucht; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (kaum düngen) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 (nur Pflanzung) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Direktsaat | Direkt ins Beet; kaum deckend | hoch |
| Mai | Vereinzeln | Auf 25–30 cm Abstand ausdünnen | mittel |
| Jun–Okt | Deadheading | Verblühte Blüten wöchentlich entfernen — fördert Nachblüte | hoch |
| Aug | Samen reifen lassen | Für nächstes Jahr Samen sammeln oder selbst aussieben | niedrig |
| Okt | Abräumen | Vor dem Winter kompostieren | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis fabae u.a. | Kolonien, Kräuselung, Honigtau | leaf, stem | vegetative, flowering | easy |
| Schnecken | Arion spp. | Fraßschäden an Keimlingen | all | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißer Belag auf Blättern | Trockene Hitze | 5–10 | vegetative |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel an Blüten | Feuchtigkeit | 3–7 | flowering |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Marienkäfer freilassen | biological | — | 5–10 Tiere/m² | 0 | Blattläuse |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | 5 g/m² | 0 | Schnecken |
| Deadheading | cultural | — | Wöchentlich | 0 | Grauschimmel (Belüftung) |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Ringelblume lockt Schwebfliegen an; hält Weiße Fliege fern | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Möhrenfliege-Abwehr | `compatible_with` |
| Spargel | Asparagus officinalis | 0.8 | Nematoden-Abwehr durch Wurzelausscheidungen | `compatible_with` |
| Zwiebeln | Allium cepa | 0.7 | Gegenseitige Förderung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Bodenbeschattung; Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kohl | Brassica oleracea | Kohl-Aphiden werden angezogen (Ringelblume als Wirtspflanze) | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ringelblume |
|-----|-------------------|-------------|-------------------------------|
| Studentenblume | Tagetes patula | Ähnliche Funktion; Asteraceae | Stärkere Nematoden-Abwehr; intensiverer Duft |
| Kapuzinerkresse | Tropaeolum majus | Ähnliche Funktion als Begleitpflanze | Essbar (alle Teile); schöne Blüten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Calendula officinalis,"Ringelblume;Sonnenwende;Pot Marigold;Common Marigold",Asteraceae,Calendula,annual,day_neutral,herb,taproot,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b",0.3,"Mittelmeerraum",yes,7,20,60,40,25,limited,yes,false,false,light_feeder,half_hardy,"3;4;5","6;7;8;9;10","6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Wikipedia Ringelblume](https://de.wikipedia.org/wiki/Ringelblume) — Taxonomie, Verwendung
2. [NaturaDB Calendula officinalis](https://www.naturadb.de/pflanzen/calendula-officinalis/) — Pflegedaten
3. [Lichtnelke Heilpflanze Calendula](https://www.lichtnelke.de/ringelblume-heilpflanze-calendula.html) — Anbau, Ernte
4. [Maria Laach Ringelblume](https://www.maria-laach.de/klosterbetriebe/klostergaertnerei/service/ringelblume.html) — Heilpflanzenkunde
