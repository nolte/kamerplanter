# Küchenzwiebel — Allium cepa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Floragard Allium cepa, Bio-Gärtner.de Zwiebeln, Utopia.de, Samen.de Mischkultur

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Allium cepa | `species.scientific_name` |
| Volksnamen (DE/EN) | Küchenzwiebel, Speisezwiebel; Onion | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` → `botanical_families.name` |
| Gattung | Allium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
| Lebenszyklus | biennial (als Gemüse einjährig kultiviert) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Steckzwiebeln überwintern im Boden bis −10 °C; Winterzwiebeln (Allium fistulosum-Hybriden) härter | `species.hardiness_detail` |
| Heimat | Zentralasien (Iran, Afghanistan) | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat in Wärme ab Januar/Februar) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (verträgt leichten Frost) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Steckzwiebeln auch 3–4 und 9–10) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (Steckzwiebel Juli, Saatzwiebel August–September) | `species.harvest_months` |
| Blütemonate | 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, offset (Steckzwiebeln) | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (in normalen Mengen; roh große Mengen problematisch) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile für Katzen und Hunde (Thiosulfate) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | N-Propyl-Disulfid, Allicin (für Tiere) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (für Tiere: severe) | `species.toxicity.severity` |
| Kontaktallergen | true (Zwiebelwasser reizt Augen und Haut) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Balkonkästen für Schnittlauchzwiebeln) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–15 cm in Reihe, 25–30 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, nährstoffreiche Erde, pH 6,0–7,0; gute Drainage | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | low |
| Sämling / Jungpflanze | 21–42 | 2 | false | false | low |
| Vegetativ (Blattwachstum) | 28–56 | 3 | false | false | medium |
| Zwiebelbildung | 28–56 | 4 | false | true | medium |
| Reife / Einzug | 14–21 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Blattwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag fördert Zwiebelbildung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Zwiebelbildung & Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (Reife: Wasser reduzieren für Lagerqualität) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 2:1:1 | 0.8–1.2 | 6.0–7.0 | 80 | 30 | — | 2 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 6.0–7.0 | 100 | 40 | 20 | 3 |
| Zwiebelbildung | 1:2:3 | 1.5–2.0 | 6.0–7.0 | 100 | 50 | 25 | 2 |
| Reife | 0:0:1 | 0.5–1.0 | 6.0–7.0 | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung → Sämling | time_based | 7–14 Tage | Keimblatt sichtbar |
| Sämling → Vegetativ | time_based | 21–42 Tage | Pflanze hat 2–3 Blätter, Pikierbereit |
| Vegetativ → Zwiebelbildung | event_based | Tageslänge >14h | Langtag-Trigger in Norddeutschland ab Juni |
| Zwiebelbildung → Reife | event_based | — | Laub knickt ein, wird gelblich |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|---------|--------|
| Zwiebel- und Knoblauch-Dünger | Compo | base | 7-5-10 | 40–60 g/m² | Pflanzung |
| Kali-Magnesia | K+S | supplement | 0-0-30+10MgO | 30 g/m² | Zwiebelbildung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–4 L/m² | Frühjahr |
| Hornspäne | Oscorna | organisch-N | 60–80 g/m² | Pflanzung |

### 3.2 Besondere Hinweise zur Düngung

Zwiebeln sind Mittelzehrer. Überdüngung (besonders Stickstoff) fördert Blattwachstum auf Kosten der Zwiebelbildung und verschlechtert die Lagerfähigkeit. Kein Frischdünger. Ab der Zwiebelbildungsphase Stickstoff reduzieren und Kalium erhöhen. Frischen Stallmist meiden — erhöht Fäulnis-Risiko.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Vorkultur (Saatzwiebel) | Aussaat in Anzuchtschalen bei 15–18 °C | mittel |
| Mär–Apr | Steckzwiebeln pflanzen | 5 cm tief, Spitze knapp über dem Boden | hoch |
| Apr | Jäten | Zwiebelfeind Nummer 1 ist Unkraut; regelmäßig jäten | hoch |
| Mai | Hackschicht aufrechterhalten | Lockere Oberfläche gegen Austrocknung | mittel |
| Jun | Langtag beobachten | Zwiebelbildung beginnt selbständig | niedrig |
| Jul | Frühzwiebeln ernten | Steckzwiebeln sind reif wenn Laub knickt | mittel |
| Aug | Haupternte | Saatzwiebeln ernten; 1–2 Wochen nachtrocknen lassen | hoch |
| Sep | Lagerung | Kühl, trocken, luftig einlagern (5–10 °C) | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Zwiebelfliege | Delia antiqua | Larven in Zwiebel, Fäulnis; gelbes Laub | root, stem | seedling, vegetative | difficult |
| Thripse | Thrips tabaci | Silbrige Streifen auf Laub, Wachstumsrückstand | leaf | vegetative | medium |
| Zwiebelblattlaus | Neotoxoptera formosana | Gekräuseltes Laub, Honigtau | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | fungal (Peronospora destructor) | Grauer Pilzrasen auf Laub, Einrollen | Feuchtigkeit, kühle Nächte | 7–14 | vegetative |
| Zwiebelbotrytis (Halsgrau) | fungal (Botrytis allii) | Grauer Belag am Blattansatz, Fäulnis | Feuchte, Verletzungen | 5–10 | ripening, storage |
| Zwiebelbrand | fungal (Urocystis cepulae) | Schwarze Streifen in Keimblättern | infizierter Boden | 7–21 | seedling |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinernema feltiae | Zwiebelfliegen-Larven | 500.000/m² | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Engmaschiges Netz ab Pflanzung | 0 | Zwiebelfliege, Thripse |
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 3 | Thripse, Blattläuse |
| Zwiebeln anhäufeln | cultural | — | Lockere Erdschicht über Zwiebeln | 0 | Zwiebelfliege |
| Fruchtfolge | cultural | — | 3 Jahre keine Lauchgewächse | 0 | Boden-Pathogene, Nematoden |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Lauchgewächse (Amaryllidaceae/Alliaceae) |
| Empfohlene Vorfrucht | Tomaten, Kohlarten (Starkzehrer) |
| Empfohlene Nachfrucht | Salat, Spinat, Möhren |
| Anbaupause (Jahre) | 3 Jahre selbe Familie |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Möhre | Daucus carota | 0.9 | Gegenseitige Schädlingsabwehr (Zwiebelfliege ↔ Möhrenfliege) | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Platzsparend, keine Konkurrenz | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Zwiebelduft hält Schädlinge fern | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Gegenseitig förderlich | `compatible_with` |
| Erdbeere | Fragaria × ananassa | 0.8 | Zwiebelduft hält Grauschimmel fern | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Erbse | Pisum sativum | Zwiebelduft hemmt Erbsenwachstum | moderate | `incompatible_with` |
| Bohne | Phaseolus vulgaris | Gegenseitige Wachstumshemmung | moderate | `incompatible_with` |
| Knoblauch | Allium sativum | Gleiche Familie, gleiche Schädlinge; zu dicht = Konkurrenz | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Zwiebel |
|-----|-------------------|-------------|--------------------------|
| Schalotte | Allium cepa var. ascalonicum | Fast identisch | Feineres Aroma, bessere Lagerfähigkeit |
| Lauch | Allium porrum | Gleiche Familie | Kältetoleranter, längere Erntezeit |
| Schnittlauch | Allium schoenoprasum | Gleiche Familie | Perennial, kein Aufwand für Knollen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Allium cepa,"Küchenzwiebel;Speisezwiebel;Onion",Amaryllidaceae,Allium,biennial,long_day,herb,bulbous,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.3,"Zentralasien",limited,15,20,60,15,12,no,limited,false,false,medium_feeder,half_hardy,"3;4","7;8;9"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Stuttgarter Riesen,Allium cepa,–,–,"classic;round;good_storage",120,,open_pollinated
Red Baron,Allium cepa,Bejo,–,"red;medium_early",110,,f1_hybrid
Sturon,Allium cepa,–,–,"long_storage;classic_round",120,,open_pollinated
```

---

## Quellenverzeichnis

1. [Zwiebeln — Der Bio-Gärtner](https://www.bio-gaertner.de/Pflanzen/Zwiebeln) — Anbaupraxis, Bio-Tipps
2. [Zwiebeln pflanzen — Utopia.de](https://utopia.de/ratgeber/zwiebeln-pflanzen-anbauzeit-pflege-und-ernte_76710/) — Anbauzeit, Pflege
3. [Zwiebel-Mischkultur — Samen.de](https://samen.de/blog/mischkultur-mit-zwiebeln-optimale-partnerpflanzen.html) — Mischkultur-Partner
4. [Floragard Allium cepa](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/gemuese/allium-cepa) — Pflegehinweise
