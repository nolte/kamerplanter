# Leuchterblume — Ceropegia woodii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Plantura – String of Hearts](https://www.plantura.garden/zimmerpflanzen/leuchterblumen/string-of-hearts), [PLNTS.com – Ceropegia Pflege](https://plnts.com/de/care/houseplants-family/ceropegia), [PlantFrand – Ceropegia woodii](https://www.plantfrand.com/pflanzen/apocynaceae/ceropegia-woodii/), [Die Grüne Welt](https://www.diegruenewelt.de/pflanze/leuchterblume-ceropegia-woodii.html)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ceropegia woodii | `species.scientific_name` |
| Volksnamen (DE/EN) | Leuchterblume; String of Hearts, Rosary Vine | `species.common_names` |
| Familie | Apocynaceae | `species.family` → `botanical_families.name` |
| Gattung | Ceropegia | `species.genus` |
| Ordnung | Gentianales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostfrei halten; keine Temperaturen unter 8°C | `species.hardiness_detail` |
| Heimat | Südafrika (KwaZulu-Natal, Swasiland, Simbabwe) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division, offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine signifikanten bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–10 (hängend bis 90 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–90 (Hängelänge) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässiges Kakteensubstrat oder 60% Zimmerpflanzenerde + 40% Perlite; sehr gute Drainage zwingend | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 30–60 | 1 | false | false | low |
| Vegetativ (Wachstum) | 180–270 | 2 | false | false | medium |
| Blüte | 60–120 | 3 | false | false | medium |
| Winterruhe | 90–120 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Etablierung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 19–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Wachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–55 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.9–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–35 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 1:1:1 | 0.4–0.6 | 6.0–6.5 | 60 | 30 | — | 1 |
| Vegetativ | 2:1:2 | 0.6–1.0 | 6.0–6.5 | 80 | 40 | — | 2 |
| Blüte | 1:2:2 | 0.6–0.8 | 6.0–6.5 | 80 | 40 | — | 1 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 30–60 Tage | Neue Triebe sichtbar, Knollchen gebildet |
| Vegetativ → Blüte | time_based | 180–270 Tage | Sommer, lange Tageslänge |
| Blüte → Winterruhe | time_based | 60–120 Tage | Temperaturabfall unter 15°C |
| Winterruhe → Vegetativ | time_based | 90–120 Tage | Frühjahr, Temperaturanstieg |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Liquid Fertilizer Succulents | Substral | base | 4-3-5 | niedrige Dosierung (halbe Empfehlung) | 1 | vegetativ, blüte |
| Cactus Focus | Growth Technology | base | 3-1-5 | 1–2 ml/L | 1 | vegetativ, blüte |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Guano Dünger | Plagron/Biobizz | organisch | 1–2 ml/L | Apr–Sep | light_feeder |
| Kakteendünger Stäbchen | Substral | organisch/langsam | 1 Stäbchen/Topf | Apr–Sep | light_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–4 | Etablierung | 0.4–0.6 | 6.2 | 0.5 | Sehr schwach düngen |
| 5–26 | Vegetativ | 0.6–1.0 | 6.2 | 1.0 | Alle 4 Wochen |
| 27–34 | Blüte | 0.6–0.8 | 6.2 | 1.0 | Kaliumbetonter Dünger |
| Nov–Feb | Winterruhe | 0.0 | — | — | Kein Dünger |

### 3.3 Mischungsreihenfolge

1. Wasser (Raumtemperatur)
2. Flüssigdünger (stark verdünnt)
3. pH-Kontrolle (nicht korrigieren nötig bei Leitungswasser)

### 3.4 Besondere Hinweise zur Düngung

Ceropegia woodii ist ein Schwachzehrer. Überdüngung führt zu Wurzelfäule und Verlust der attraktiven Blattzeichnung. Im Winter komplett auf Düngung verzichten. Die kleinen Knollchen (Tuberkeln) entlang der Triebe sind natürliche Wasserspeicher — ein gutes Zeichen für ausreichende Versorgung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; leicht kalkempfindlich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe halten | Minimal gießen, nicht düngen, kühler Standort (12–15°C) möglich | niedrig |
| Feb | Erste Kontrolle | Auf neue Triebe prüfen, Gießrhythmus leicht erhöhen | mittel |
| Mär | Wachstum anregen | Düngung beginnen, hellen Standort sichern | hoch |
| Apr | Umtopfen | Bei Bedarf in leicht größeren Topf mit frischem Substrat | mittel |
| Mai | Vermehrung | Stecklinge aus Kettentrieben schneiden, Knollchen abtrennen | niedrig |
| Jun–Sep | Blütezeit | Regelmäßig gießen (Substrat zu 2/3 trocken), düngen | hoch |
| Okt | Einwintern | Gießen reduzieren, Dünger einstellen | mittel |
| Nov–Dez | Ruhephase | Sehr sparsam gießen, nicht düngen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag, Honigtau | stem, leaf | alle | medium |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbliche Blätter | leaf | vegetative | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen, klebrige Ausscheidungen | stem | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Welke Triebe, schwarze Wurzeln | overwatering, poor_drainage | 7–14 | alle |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmelbelag | high_humidity, poor_airflow | 3–7 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wollläuse | 1–2 Käfer/Pflanze | 14–21 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 0 | Wollläuse, Spinnmilben |
| Alkohol (70%) | mechanical | Isopropanol | Tupfer auf Schädlinge | 0 | Wollläuse, Schildläuse |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Spinnmilben, Blattläuse |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Allgemein schädlingsresistent bei guter Pflege | — | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze (keine Fruchtfolge relevant) |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Echeveria | Echeveria elegans | 0.8 | Gleiche Pflegebedürfnisse, trockenes Substrat | `compatible_with` |
| Haworthia | Haworthiopsis fasciata | 0.8 | Gleiche Licht- und Wasserbedürfnisse | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Farne | Nephrolepis exaltata | Feuchtigkeitsbedarf zu unterschiedlich | moderate | `incompatible_with` |
| Calathea | Goeppertia spp. | Feuchtigkeitsbedarf zu unterschiedlich | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ceropegia woodii |
|-----|-------------------|-------------|------------------------------|
| Ceropegia linearis | Ceropegia linearis | Gleiche Gattung | Noch schmalblättriger, ähnliche Pflege |
| Perlenschnur | Curio rowleyanus (syn. Senecio rowleyanus) | Hängepflanze, sukkulent | Spektakulärere Blattform (Perlenform) |
| Hoya | Hoya carnosa | Kletterer/Hänger, Apocynaceae | Duftende Blüten, etwas robuster |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Ceropegia woodii,Leuchterblume;String of Hearts;Rosary Vine,Apocynaceae,Ceropegia,perennial,day_neutral,vine,tuberous,10a;10b;11a;11b;12a;12b,0.0,Südafrika,yes,2,10,10,90,—,yes,limited,false,false
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Ceropegia woodii var. variegata,Ceropegia woodii,—,—,variegated;ornamental,—,—,open_pollinated
Silver Glory,Ceropegia woodii,—,—,silver_leaf;compact,—,—,open_pollinated
```

---

## Quellenverzeichnis

1. [Plantura – String of Hearts Pflege](https://www.plantura.garden/zimmerpflanzen/leuchterblumen/string-of-hearts) — Detaillierte Pflegeanleitung DE
2. [PLNTS.com – Ceropegia Expertentipps](https://plnts.com/de/care/houseplants-family/ceropegia) — Pflege, Toxizität, Schädlinge
3. [PlantFrand – Ceropegia woodii](https://www.plantfrand.com/pflanzen/apocynaceae/ceropegia-woodii/) — Botanik, Pflege
4. [Die Grüne Welt – Leuchterblume](https://www.diegruenewelt.de/pflanze/leuchterblume-ceropegia-woodii.html) — Steckbrief
5. [Pflanzenfreunde – Ceropegia](https://www.pflanzenfreunde.com/lexika/sukkulenten/ceropegia.htm) — Kulturtipps
