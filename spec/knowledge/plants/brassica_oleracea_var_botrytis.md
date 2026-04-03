# Blumenkohl — Brassica oleracea var. botrytis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Blumenkohl, Hortipendium Blumenkohl Erwerbsanbau, Naturadb Brassica oleracea var. botrytis, Mein-Gartenexperte Blumenkohl

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. botrytis | `species.scientific_name` |
| Volksnamen (DE/EN) | Blumenkohl, Karfiol; Cauliflower | `species.common_names` |
| Familie | Brassicaceae | `species.family` → `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a–11b (jährlich angebaut) | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Jungpflanzen frostempfindlich; reife Köpfe vertragen -3°C; Herbsternte bis November in Norddeutschland | `species.hardiness_detail` |
| Heimat | Kultivierte Form; Ursprung Mittelmeer (wie alle Brassica oleracea) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 (innen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5, 7 | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10, 11 (je nach Saison; Früh-, Sommer-, Herbstsorten) | `species.harvest_months` |
| Blütemonate | — (Ernte vor Blüte) | `species.bloom_months` |

**Anbaustaffeln Norddeutschland:**
- Frühkultur: Vorkultur Januar–Februar innen; Pflanzung März–April; Ernte Mai–Juni
- Hauptkultur: Vorkultur März–April; Pflanzung Mai; Ernte Juli–August
- Herbstkultur: Aussaat Juli; Pflanzung August; Ernte Oktober–November

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (vollständig essbar) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Blattblenden: Äußere Blätter über den weißen Kopf legen oder binden — schützt vor Gelbverfärbung durch Licht ("Blenden"). Kompakte, cremeweiße Köpfe durch Lichtausschluss.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50–60 × 50–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | true (für Frühkultur) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, wasserhaltende Komposterde; pH 6,0–7,5; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling (Vorkultur) | 28–42 | 2 | false | false | low |
| Jungpflanzen-Aufbau | 21–35 | 3 | false | false | medium |
| Vegetatives Wachstum (Blattmasse) | 28–42 | 4 | false | false | medium |
| Kopfbildung | 21–35 | 5 | false | false | medium |
| Reife & Ernte | 7–14 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kopfbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 (kritisch: > 25°C führt zu Schossung!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–4 (gleichmäßig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1500–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | – | – | – | – |
| Sämling | 1:1:1 | 0.6–0.8 | 6.0–6.5 | 80 | 40 | – | 2 |
| Vegetativ | 3:1:2 | 1.4–2.0 | 6.0–7.0 | 160 | 80 | – | 3 |
| Kopfbildung | 2:2:2 | 1.6–2.2 | 6.0–7.0 | 180 | 100 | 50 | 3 |
| Reife | 1:1:2 | 1.2–1.8 | 6.0–7.0 | 140 | 80 | – | 2 |

**Wichtig:** Bormangel führt zu Braunverfärbungen im Kopf ("Braunfärbigkeit"). Bei B-Mangel: 0,5–1 g Borax/m² zur Erde. Molybdänmangel → "Peitschenstiel" (Geiztriebe). Schwefel wichtig für Glucosinolat-Bildung.

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch | 100–150 g/m² | vor Pflanzung | heavy_feeder |
| Kompost | eigen | organisch | 5–8 L/m² | vor Pflanzung | Bodenverbesserung |
| Gemüse-Dünger | Neudorff Azet | organisch | 80 g/m² | alle 3 Wochen | heavy_feeder |

#### Mineralisch

| Produkt | Marke | Typ | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----------|-----------------|--------|
| Kohl-Kopfdünger | Compo | mineral | 60 g/m² | 1 | Kopfbildung |
| Kaliumnitrat | Hauert | mineral | nach Etikett | 1 | Vegetativ |
| Bittersalz | Hauert | mineral | 15 g/m² | 2 | Bei Mg-Mangel |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| Bodenvorbreitung | N-P-K | Kompost + Hornspäne | 7 L/m² + 120 g/m² | 2–3 Wochen vor Pflanzung |
| 3 Wochen nach Pflanzung | N-betont | Gemüse-Dünger | 80 g/m² | Schnelles Wachstum |
| Kopfbildungsbeginn | ausgewogen | Kohl-Kopfdünger | 60 g/m² | Letzte Düngung! |

### 3.3 Besondere Hinweise zur Düngung

Blumenkohl ist der anspruchsvollste der Kohlarten — sehr empfindlich auf Nährstoffmangel. Kalk essenziell gegen Kohlhernie (pH > 6,5). Calcium-Mangel → Blattrandverbrennung. Schwefelmangel → blasse Köpfe. Letzter Dünger ca. 4 Wochen vor Ernte (Nitratabbau).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; gleichmäßige Feuchtigkeit essenziell für gleichmäßige Köpfe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Vorkultur (Frühkultur) | Bei 18–22°C; Pikieren nach 2 Wochen | hoch |
| Mär–Apr | Pflanzung (Frühkultur) | Nach letztem Frost (Eisheiligen berücksichtigen) | hoch |
| Mai | Pflanzung (Hauptkultur) | 50 × 60 cm Abstand; Tiefpflanzen | hoch |
| Mai–Jun | Blenden | Äußere Blätter bei Kopfgröße 5–8 cm über Kopf binden | mittel |
| Jun–Jul | Ernte Frühkultur | Bei Kopfdurchmesser 15–20 cm; schnell ernten | hoch |
| Jul | Nachsaat Herbstkultur | Für Oktober–November-Ernte | mittel |
| Aug | Pflanzung Herbstkultur | Jungpflanzen einsetzen | hoch |
| Okt–Nov | Herbsternte | Köpfe noch kompakt; bei Frost Vlies schützen | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweißling | Pieris brassicae, P. rapae | Fraß an Blättern; Raupen; gelblich-weiße Eier auf Blattunterseite | leaf | vegetative | easy |
| Kohlfliege | Delia radicum | Welke; Larven an Wurzeln | root | seedling, vegetative | difficult |
| Kohlblattlaus | Brevicoryne brassicae | Grau-blaue Kolonien; Wachstum gehemmt | leaf, shoot | vegetative | easy |
| Erdflöhe | Phyllotreta spp. | Viele kleine Löcher in Blättern | leaf | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Kohlhernie | Plasmodiophora brassicae | Knollige Wurzelanschwellungen; Welke; Vergilben | pH < 6,5; Staunässe | 14–28 | alle |
| Echter Mehltau (Kohl) | fungal (Erysiphe cruciferarum) | Weißer Belag | Trockenheit | 5–10 | vegetative |
| Ringfleckenkrankheit | fungal (Mycosphaerella brassicicola) | Schwarze Ringflecken auf Blättern | Feuchte | 7–14 | vegetative |
| Blattdürre | fungal (Alternaria spp.) | Braune Flecken; konzentrische Ringe | Feuchtigkeit | 5–10 | all phases |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Trichogramma brassicae | Kohlweißling-Eier | 3–5 Karten/m² | sofort |
| Diadegma insulare | Kohlmottenraupen | natürlich vorkommend | – |
| Steinernema feltiae (Nematoden) | Kohlfliege (Larven) | nach Etikett; bodenfeucht | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kalkung | cultural | CaCO3 | pH auf 7,0–7,5 anheben | 0 | Kohlhernie |
| Kulturschutznetz | cultural | – | Direkt nach Pflanzung | 0 | Kohlfliege, Kohlweißling |
| Bacillus thuringiensis | biological | Bt | Sprühen auf Raupen | 0 | Kohlweißling |
| Trichogramma | biological | Schlupfwespe | Bei Eiablage | 0 | Kohlweißling |
| Neem-Öl | biological | Azadirachtin | 0.5% Lösung | 3 | Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Kreuzblütler (Brassicaceae) |
| Empfohlene Vorfrucht | Leguminosen (Erbse, Bohne); Gründüngung |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Feldsalat) |
| Anbaupause (Jahre) | 4–5 Jahre selbe Familie (Brassicaceae) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sellerie | Apium graveolens | 0.9 | Klassische Kombination; gegenseitige Stärkung | `compatible_with` |
| Dill | Anethum graveolens | 0.8 | Zieht Nützlinge an; lockert auf | `compatible_with` |
| Zitronenmelisse | Melissa officinalis | 0.8 | Verwirrt Kohlfliege durch Aroma | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematodenabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Erdbeere | Fragaria × ananassa | Geteilte Bodenerkrankungen | moderate | `incompatible_with` |
| Zwiebeln/Lauch | Allium spp. | Hemmen Kohlwachstum | moderate | `incompatible_with` |
| Alle Brassicaceae | Brassica spp. | Kohlhernie-Infektionsdruck | severe | `incompatible_with` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Brassica oleracea var. botrytis,"Blumenkohl;Karfiol;Cauliflower",Brassicaceae,Brassica,annual,long_day,herb,taproot,"2a;3a;4a;5a;6a;7a;8a;9a;10a;11a",0.0,"Kultiviert, Mediterran",limited,25,30,80,80,55,no,limited,true,false,heavy_feeder,false,half_hardy,""
```

---

## Quellenverzeichnis

1. [Plantura Blumenkohl Portrait](https://www.plantura.garden/gemuese/blumenkohl/blumenkohl-pflanzenportrait) — Steckbrief, Pflege
2. [Hortipendium Blumenkohl Erwerbsanbau](https://hortipendium.de/Blumenkohl) — Fachliche Daten, NPK
3. [Naturadb Brassica oleracea var. botrytis](https://www.naturadb.de/pflanzen/brassica-oleracea-var-botrytis/) — Stammdaten
4. [Mein-Gartenexperte Blumenkohl](https://www.mein-gartenexperte.de/pflanzen/blumenkohl) — Pflege, Schädlinge
