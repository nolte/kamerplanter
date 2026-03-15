# Efeutute — Epipremnum aureum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Wikipedia Epipremnum aureum](https://en.wikipedia.org/wiki/Epipremnum_aureum), [Clemson University Extension](https://hgic.clemson.edu/factsheet/how-to-grow-pothos-indoors-epipremnum-spp-care-cultivars-and-common-problems/), [ASPCA Toxicity](https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants), [University of Florida IFAS Extension](https://edis.ifas.ufl.edu/), [New York Botanical Garden](https://libguides.nybg.org/pothos)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Epipremnum aureum | `species.scientific_name` |
| Volksnamen (DE/EN) | Efeutute, Goldene Efeutute; Golden Pothos, Devil's Ivy | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Epipremnum | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic, stoloniferous | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–29°C. Unter 10°C kommt es zu Kälteschäden (Blattflecken, Verfärbungen). | `species.hardiness_detail` |
| Heimat | Salomoninseln (Ozeanien), naturalisiert in tropischen Regionen weltweit | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, xylene, toluene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Epipremnum aureum wurde lange als *Scindapsus aureus* oder *Pothos aureus* geführt. Der verbreitete Handelsname "Pothos" ist botanisch irreführend (echte Pothos-Gattung ist eine separate Gattung). Im Handel auch als "Devil's Ivy" bekannt, da extrem widerstandsfähig auch unter schlechten Bedingungen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt (reine Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Entfällt | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor nie; Blüte an natürlichem Standort selten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit mindestens 2 Knoten (Nodes) in Wasser oder direkt in feuchtem Substrat bewurzeln. Bewurzelung in Wasser innerhalb 2–4 Wochen. Extrem hohe Erfolgsrate, ideal für Einsteiger. Variegierte Sorten wie 'Marble Queen' können durch Stecklinge an Variegation verlieren — nur von stark variegierten Trieben steckeln.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, roots | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft kann Kontaktdermatitis bei empfindlichen Personen auslösen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken:** Brennen und Schwellung im Mund- und Rachenraum, vermehrter Speichelfluss, Übelkeit. Bei Haustieren: Pfoten am Maul reiben, Erbrechen, Schluckbeschwerden. Quelle: ASPCA Animal Poison Control.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 (hängend/kletternd bis 200+) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 (je nach Haltungsform) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Monate, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (optional — Moosstab fördert größere Blätter) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, durchlässige Einheitserde mit 20–30% Perlite. Leicht saures bis neutrales Substrat (pH 6.1–6.5). Guter Wasserabzug wichtig. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung (nach Steckling) | 14–28 | 1 | false | false | low |
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 2 | false | false | high |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Etablierung (nach Steckling/Umtopfen)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Aktives Wachstum (Frühling/Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Nov–Feb)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 2–6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 1:1:1 | 0.4–0.8 | 6.0–6.5 | 60 | 20 | — | 1 |
| Aktives Wachstum | 3:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0–0.4 | 6.0–6.5 | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/Bedingungen |
|------------|---------|------------------|
| Etablierung → Aktives Wachstum | time_based | 21–28 Tage; erste neue Blätter sichtbar |
| Aktives Wachstum → Winterruhe | time_based | Oktober/November; Tageslichtstunden <10h |
| Winterruhe → Aktives Wachstum | time_based | März/April; Tageslichtstunden >12h |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Zimmerpflanze)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L | 1 | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | 1 | Wachstum |
| Hydro-Dünger | Compo | base | 6-3-6 | 5 ml/L | 1 | Wachstum (Hydro) |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Wurmhumus | Bio-Eigenherstellung | organisch | 10–20% Substratanteil | Umtopfen | alle |
| Hornspäne fein | Oscorna | organisch | 2–3 g/L Substrat | Frühling | alle |

### 3.2 Düngungsplan

| Monat | Phase | Maßnahme | Hinweise |
|-------|-------|----------|----------|
| Mär–Sept | Aktives Wachstum | Flüssigdünger alle 4 Wochen | Halbdosis bei Schwachlicht-Standorten |
| Okt–Feb | Winterruhe | Kein Dünger | Überdüngung bei reduziertem Licht schadet |

### 3.3 Besondere Hinweise zur Düngung

Efeututen sind ausgesprochene Schwachzehrer — Überdüngung führt zu Blattverbrennungen (braune Spitzen, Blattrandnekrosen) und fördert Schädlingsbefall. Variegierte Sorten (Marble Queen, Neon) benötigen noch weniger Dünger als die Grundart, da sie weniger Chlorophyll für die Photosynthese nutzen können. Bei Hydrokultur EC-Wert 0.8–1.2 mS einhalten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; abgestandenes Wasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Umtopfen prüfen | Wurzeln am Topfboden? Topfgröße um 2–3 cm erhöhen | mittel |
| Mär | Rückschnitt | Lange Triebe auf gewünschte Länge kürzen, Stecklinge gewinnen | mittel |
| Mär | Düngung starten | Erste Düngergabe nach Winterpause | mittel |
| Apr–Aug | Wässern | Oberstes Erdreich (ca. 2 cm) zwischen Gießgängen trocknen lassen | hoch |
| Sep | Düngung reduzieren | Düngeintervall verlängern | niedrig |
| Okt–Feb | Minimalpflege | Deutlich seltener gießen, kein Dünger | hoch |
| Ganzjährig | Blätter reinigen | Staubige Blätter mit feuchtem Tuch abwischen | niedrig |

### 4.3 Überwinterung

Nicht erforderlich — Zimmerpflanze. Bei Balkonhaltung ab Oktober hereinholen (Temperatur unter 15°C meiden).

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, gelbliche Punkte auf Blättern, Blätter vergilben | leaf | alle (besonders bei trockener Luft) | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau, Rußtaupilz, kleine weiße Fliegen beim Berühren | leaf | aktives Wachstum | easy |
| Schmierlaus | Pseudococcus longispinus | Watteartige Wollflecken in Blattachseln und Stielen | leaf, stem | alle | easy |
| Trauermücke | Bradysia spp. | Larven schädigen Wurzeln, Adulte lästig | root | alle (besonders bei Überbewässerung) | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|
| Wurzelfäule | fungal (Pythium, Phytophthora) | Welke trotz feuchter Erde, braune Wurzeln, fauler Geruch | Überstauung, schlechte Drainage | alle |
| Blattfleckenkrankheit | bacterial/fungal | Braune, nasse Flecken mit gelbem Rand | Hohe Luftfeuchtigkeit + Wasser auf Blättern | aktives Wachstum |
| Pythium-Stängelfäule | fungal (Pythium spp.) | Stängelbase schwarzfaul, Pflanze kollabiert | Überbewässerung, schlechte Drainage | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10–20 | 14–21 |
| Chrysoperla carnea (Larven) | Schmierläuse, Weiße Fliege | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl-Lösung | biological | Azadirachtin | Sprühen, 0.5%, alle 7 Tage | 0 | Spinnmilbe, Weiße Fliege, Schmierläuse |
| Insektizidseife | biological | Kaliseife | Sprühen, alle 5–7 Tage | 0 | Spinnmilbe, Blattläuse, Weiße Fliege |
| Gelbtafeln | mechanical | — | Aufhängen über Pflanze | 0 | Trauermücke, Weiße Fliege |
| Nematoden (Steinernema feltiae) | biological | — | Gießen ins Substrat | 0 | Trauermücke (Larven) |
| Systemisches Insektizid | chemical | Imidacloprid | Stäbchen ins Substrat | 14 | Schmierläuse, Weiße Fliege |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

Entfällt — reine Zimmerpflanze ohne Freiland-Fruchtfolge-Relevanz.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Philodendron | Philodendron spp. | 0.9 | Gleiche Pflegebedürfnisse, hohe Luftfeuchtigkeit zusammen |
| Spathiphyllum | Spathiphyllum wallisii | 0.8 | Feuchtigkeitsbedarf ähnlich, gegenseitige Luftbefeuchterung |
| Monstera | Monstera deliciosa | 0.8 | Gleiche Familie, ähnliche Ansprüche |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad |
|---------|-------------------|-------|-------------|
| Sukkulenten/Kakteen | diverse | Komplett gegensätzliche Feuchteansprüche | moderate |
| Calathea | Calathea spp. | Epipremnum kann Schädlinge auf empfindlichere Calathea übertragen | mild |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Epipremnum aureum |
|-----|-------------------|-------------|--------------------------------------|
| Herzblatt-Philodendron | Philodendron hederaceum | Sehr ähnliche Wuchsform, kletternd | Größere Blätter, oft kräftigeres Wachstum |
| Seidenpflanze | Scindapsus pictus | Verwandt, silber-gefleckte Blätter | Dekorativeres Blattmuster |
| Teufelssaat | Epipremnum pinnatum | Gleiche Gattung | Größere, fiederteilige Blätter mit Reife |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,air_purification_score
Epipremnum aureum,"Efeutute;Goldene Efeutute;Golden Pothos;Devil's Ivy",Araceae,Epipremnum,perennial,day_neutral,vine,aerial,"10a;10b;11a;11b;12a",0.0,"Salomoninseln (Ozeanien)",yes,2-10,15,20-200+,40-100,,yes,limited,false,false,light_feeder,0.6
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Golden Pothos,Epipremnum aureum,"ornamental;vigorous_grower",clone
Marble Queen,Epipremnum aureum,"ornamental;variegated;slow_grower",clone
Neon,Epipremnum aureum,"ornamental;chartreuse_leaves",clone
N'Joy,Epipremnum aureum,"ornamental;variegated;compact",clone
Pearls and Jade,Epipremnum aureum,"ornamental;variegated;compact",clone
```

---

## Quellenverzeichnis

1. [Wikipedia — Epipremnum aureum](https://en.wikipedia.org/wiki/Epipremnum_aureum) — Taxonomie, Verbreitung, Naturstandort
2. [Clemson University Extension — Pothos](https://hgic.clemson.edu/factsheet/how-to-grow-pothos-indoors-epipremnum-spp-care-cultivars-and-common-problems/) — Kulturansprüche, Sorten, Schädlinge
3. [ASPCA Animal Poison Control](https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants) — Toxizitätsdaten
4. [New York Botanical Garden Research Guide](https://libguides.nybg.org/pothos) — Botanische Hintergründe
5. [NASA Clean Air Study (Wolverton 1989)](https://ntrs.nasa.gov/citations/19930073077) — Luftreinigungskapazität
