# Süßkirsche — Prunus avium

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartenratgeber Kirschbaum, Lubera Kirschbaum, Pflanzeninfothek Prunus avium, Baldur-Garten Kirschbaum, Naturadb Prunus avium

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Prunus avium | `species.scientific_name` |
| Volksnamen (DE/EN) | Süßkirsche, Vogelkirsche; Sweet Cherry, Wild Cherry | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Prunus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; Blüten empfindlich gegen Spätfrost; starkwüchsig (15–30 m) bei Sämlings-Unterlage; auf Gisela-Unterlagen kompakter (4–6 m) | `species.hardiness_detail` |
| Heimat | Europa, Westasien | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (veredelte Containerpflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7 (Juni–Juli; je nach Sorte) | `species.harvest_months` |
| Blütemonate | 4, 5 (April–Mai; gleichzeitig mit/kurz nach Apfel; Spätfrostgefahr!) | `species.bloom_months` |

**Befruchter KRITISCH:** Fast alle Süßkirschen sind SELBSTUNFRUCHTBAR. Ohne passenden Befruchter keine oder wenig Ernte. Ausnahmen: 'Lapins', 'Stella' (selbstfruchtbar). Empfohlene Befruchterkombinationen: 'Kordia' + 'Regina', 'Burlat' + 'Schneiders Knorpelkirsche'. Gleiche Blütezeit ist PFLICHT (Gruppe A, B oder C prüfen).

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | grafting | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Unterlagen:** Vogelkirsche (Sämling: stark, 15–20 m); Gisela 5 (schwach-mittel: 4–6 m, früh tragend, empfehlenswert für Gärten); Maxma 14 (mittel-stark).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Kerne und Blätter enthalten Amygdalin; Früchte sicher | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Amygdalin (Kerne; bei Knacken freigesetzt) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (Juli–August nach der Ernte) | `species.pruning_months` |

**KRITISCH:** Kirschbäume NUR im Sommer schneiden (August–September nach Ernte) — NIEMALS im Winter oder Frühjahr! Wundverschluss durch Cambium-Aktivität im Sommer schneller; Infektionsrisiko durch Holzschutzkrankheiten (Nectria, Scharkavirus-Eintritt durch Wunden) im Winter viel höher.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 100–200 (nur auf schwachen Unterlagen wie Gisela 5) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 60 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 400–800 (Gisela 5: 400–600) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 400–800 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 500–800 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgründige, nährstoffreiche Erde; pH 6,0–7,5; gut durchlässig; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte | 7–14 | 1 | false | false | low |
| Fruchtansatz / Vegetativ | 60–90 | 2 | false | false | medium |
| Fruchtreife | 14–30 | 3 | false | true | high |
| Sommerwachstum / Blütenanlage | 90–120 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (vollsonnig; Reife-Beschleunigung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 10000–30000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**WICHTIG:** Kein Starkregen in der Reifephase (Platzen der Früchte). Witterungsschutz durch Überdachung bei Tafelkirschen-Kulturen.

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Blüte/Fruchtansatz | 1:2:1 | — | 6.0–7.5 | 150 | 60 | — | 3 |
| Vegetativ | 2:1:1 | — | 6.0–7.5 | 120 | 60 | — | 3 |
| Fruchtreife | 1:1:2 | — | 6.0–7.5 | 100 | 50 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Obstbaum-Langzeitdünger | Compo | organisch-mineralisch | 100–150 g/m² | März–April | medium_feeder |
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März–April | Stickstoff |
| Kompost (reif) | eigen | organisch | 4–6 L/m² | Oktober/März | Bodenverbesserung |
| Jauche / Brennnesseljauche | — | organisch | 1:10 verdünnt; gießen | Mai–Juni | Stickstoff, Vitalisierung |

### 3.2 Besondere Hinweise zur Düngung

Kirschbäume brauchen weniger Stickstoff als Birnen. Überdüngung fördert starkes Triebwachstum auf Kosten der Fruchtbildung und erhöht Monilia-Anfälligkeit (weiches Gewebe). Kein Dünger nach Ende Juni.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; bei Trockenheit gießen; in der Reifephase KEIN Starkregen (Platzen); eventuell überdachen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr–Mai | Blüte / Bestäubung | Spätfrostschutz bei Bedarf; Befruchter-Blüte kontrollieren | hoch |
| Jun | Ernte Frühsorten | Vögel schützen (Netz); Ernte morgens | hoch |
| Jul–Aug | Ernte Spätsorten | Vollreif ernten; Regenschutz beachten | hoch |
| Aug–Sep | Schnitt NACH Ernte | NUR im Sommer schneiden! Werkzeuge desinfizieren | hoch |
| Ganzjährig | Monilia-Kontrolle | Befallene Früchte sofort entfernen + vernichten | mittel |

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
| Kirschfruchtfliege | Rhagoletis cerasi | Maden in Früchten; weiße Maden in Kirschen | fruit | Fruchtreife | difficult |
| Spinnmilbe | Tetranychus urticae | Blattvergilbung; Gespinste | leaf | vegetative (Hitze) | medium |
| Kirschenblattlaus | Myzus cerasi | Kolonien; eingerollte Blätter | leaf, shoot | vegetative (Frühjahr) | easy |
| Vögel | Sturnus vulgaris, Turdus spp. | Fruchtschäden, Anpicken | fruit | Fruchtreife | easy |

**Kirschfruchtfliege:** Gelbtafeln aufhängen ab Ende Mai; Befallstoleranzschwelle: 2 Fliegen/Tafel; bei Überschreitung Behandlung. Alternativ: Ernte vor Madenbefall (frühe Sorten!).

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Monilia-Spitzendürre | fungal (Monilinia laxa) | Welkende Blütenstände; "Braunfäule"; Triebsterben | Feuchte Witterung zur Blüte | 5–10 | Blüte |
| Monilia-Fruchtfäule | fungal (Monilinia fructicola) | Braune Faulflecken auf Früchten | Feuchtigkeit, Verletzungen | 7–14 | Fruchtreife |
| Kirschensprühfleckenkrankheit | fungal (Blumeriella jaapii) | Rote Flecken auf Blättern; Blätter fallen früh | Feuchtigkeit | 14–21 | vegetative |
| Scharkavirus | viral (PPV = Plum Pox Virus) | Ringen und Flecken auf Früchten und Blättern; keine direkte Behandlung | Blattläuse (Übertragung) | — | alle |

**Monilia:** Befallene Triebe mind. 30 cm ins gesunde Holz schneiden. Schnittstellen desinfizieren.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Vogelschutznetze | Vögel | — (physischer Schutz) | sofort |
| Schlupfwespen | Fruchtfliege | natürliche Förderung | — |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Vogelschutznetze | cultural | — | Ab Fruchtfärbung | 0 | Vögel |
| Gelbtafeln | cultural | — | Aufhängen Ende Mai | 0 | Kirschfruchtfliege |
| Natrium-Bentonit (Surround WP) | biological | Kaolin | Sprühen; Film auf Früchten | 0 | Fruchtfliege |
| Kupfer-Fungizid | chemical | Kupferoxydul | Vor Blüte; nach Blüte | 14 | Monilia, Sprühflecken |
| Sommer-Schnitt | cultural | — | Luftzirkulation verbessern | 0 | Monilia |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Steinobst (Rosaceae) |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft; 30–50 Jahre Standzeit |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestäuber | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlausabwehr | `compatible_with` |
| Knoblauch | Allium sativum | 0.7 | Pilzvorbeugung (umstritten) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Pflaume | Prunus domestica | Scharkavirus-Übertragung; gleiche Pilzkrankheiten | severe | `shares_pest_risk` |
| Aprikose | Prunus armeniaca | Gleiche Krankheiten; Scharkavirus | moderate | `shares_pest_risk` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Rosaceae (Steinobst) | `shares_pest_risk` | Monilia, Scharkavirus, Rindenerkrankungen | `shares_pest_risk` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,harvest_months
Prunus avium,"Süßkirsche;Vogelkirsche;Sweet Cherry",Rosaceae,Prunus,perennial,long_day,tree,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",-0.1,"Europa, Westasien",limited,150,60,700,600,600,no,no,false,true,medium_feeder,false,hardy,"4;5","6;7"
```

---

## Quellenverzeichnis

1. [Gartenratgeber — Kirschbaum](https://www.gartenratgeber.net/pflanzen/kirschbaum-prunus-cerasus-avium.html) — Düngen, Schnitt
2. [Lubera — Kirschbaum pflanzen](https://www.lubera.com/de/gartenbuch/kirschbaum-pflanzen-p2245) — Unterlagen, Befruchter
3. [Pflanzeninfothek — Prunus avium](https://www.pflanzeninfothek.de/artikel/2629/prunus-avium) — Steckbrief
4. [Baldur-Garten — Kirschbaum schneiden](https://www.baldur-garten.de/onion/content/pflege-tipps/obst/kirschbaum-(prunus-avium)) — Schnitt-Zeitpunkt
5. [Naturadb — Prunus avium](https://www.naturadb.de/pflanzen/prunus-avium/) — Ökologie
