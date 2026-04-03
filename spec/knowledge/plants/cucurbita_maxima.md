# Riesenkürbis / Hokkaido — Cucurbita maxima

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Bio-Gärtner.de Kürbis, Plantura Kürbis, Oekolandbau.de, Floragard Cucurbita maxima

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cucurbita maxima | `species.scientific_name` |
| Volksnamen (DE/EN) | Riesenkürbis, Hokkaido-Kürbis; Winter Squash, Pumpkin | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` → `botanical_families.name` |
| Gattung | Cucurbita | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich ab 0 °C; alle Pflanzenteile; typisch nach Eisheiligen (Mitte Mai) auspflanzen | `species.hardiness_detail` |
| Heimat | Südamerika (Peru, Bolivien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (Vorkultur April in Töpfe) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 9, 10 | `species.harvest_months` |
| Blütemonate | 7, 8 | `species.bloom_months` |

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
| Giftige Pflanzenteile | Vorsicht: bittere Kürbisse (Cucurbitacin) NICHT essen | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Cucurbitacin (in bitteren Exemplaren; kann durch Einkreuzung entstehen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Triebspitzen zur Fruchtförderung) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (nur Buschsorten in min. 60 L) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 60–100 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–50 (kriechend bis 300–500 cm Länge) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–300 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 150–200 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Buschsorten, rankend über Geländer) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (für rankende Sorten über Gestell) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr nährstoffreiche, lockere Erde mit viel Kompost; pH 6,0–6,8 | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ (Rankenbildung) | 21–42 | 3 | false | false | medium |
| Blüte & Fruchtansatz | 21–35 | 4 | false | false | medium |
| Fruchtreife | 42–70 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (Reifeförderung durch leichten Trockenstress) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 1:1:1 | 0.8–1.2 | 6.0–6.8 | 80 | 40 | — | 2 |
| Vegetativ | 3:1:2 | 1.5–2.5 | 6.0–6.8 | 150 | 60 | 20 | 3 |
| Blüte | 1:2:3 | 1.5–2.0 | 6.0–6.8 | 120 | 70 | — | 2 |
| Fruchtreife | 0:1:3 | 1.0–1.5 | 6.0–6.8 | 100 | 50 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 8–10 L/Pflanzloch | Pflanzung |
| Hornspäne | Oscorna | organisch-N | 100–150 g/Pflanzloch | Pflanzung |
| Brennnesseljauche | selbst | organisch-N | 1:10 verdünnt, 2L/Pflanze | alle 2–3 Wochen Jul–Aug |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kürbis-Dünger | Compo | base | 7-3-10 | 80–100 g/Pflanze | Wachstum |
| Patentkali | K+S | supplement | 0-0-30+10MgO | 40 g/Pflanze | Fruchtreife |

### 3.2 Besondere Hinweise zur Düngung

Kürbis ist Starkzehrer mit sehr hohem Nährstoffbedarf — das Pflanzloch vor dem Setzen großzügig mit Kompost und Hornspänen füllen. Magnesium-Mangel typisch (gelbliche Blätter mit grünen Adern) — mit Bittersalz oder Patentkali korrigieren. Zu viel Stickstoff fördert Ranken auf Kosten der Früchte. Blütenendenfäule durch Ca-Mangel oder Bewässerungsunregelmäßigkeiten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Große Mengen, direkt an die Wurzel; Blätter trocken halten (Mehltau) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Vorkultur | Einzeln in 10-cm-Töpfe bei 20–25 °C; nicht zu früh! | hoch |
| Mai (nach 15.) | Auspflanzen | Nach Eisheiligen; warm und frostfrei | hoch |
| Jun | Schneckenschutz | Junge Pflanzen massiv gefährdet | hoch |
| Jul | Rankenpflege | Triebspitzen pinzieren für mehr Früchte | mittel |
| Jul–Aug | Bestäubung | Bei Bedarf manuell bestäuben (morgens) | niedrig |
| Aug | Brett/Unterlage | Unter Früchte legen verhindert Fäulnis | mittel |
| Sep–Okt | Ernte | Stiel verholzt, hohl klingt, Schale hart | hoch |
| Okt | Winterlager | Kühl (10–15 °C), trocken, Frost vermeiden; hält Monate | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Nacktschnecke | Arion spp., Deroceras spp. | Riesige Fraßschäden an Jungpflanzen und Früchten | all | seedling, flowering | easy |
| Kürbisfliege | Dacus cucurbitae | Larven in Früchten (in DE selten) | fruit | ripening | difficult |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau, Schmutzpilze | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißes, mehligartiges Pulver auf Blättern | Trockene Tage, feuchte Nächte | 5–10 | vegetative, flowering |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel an Blüten und Früchten | Feuchtigkeit | 3–7 | flowering, ripening |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinernema feltiae | Schnecken-Larven im Boden | 500.000/m² | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen, 5 g/m² | 0 | Schnecken |
| Milch-Lösung (1:10) | biological | Milchsäure | Blattsprühmittel, wöchentlich | 0 | Echter Mehltau |
| Schwefel | chemical | Schwefel | Stäuben/Spritzen | 3 | Echter Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kürbisgewächse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte, Leguminosen |
| Empfohlene Nachfrucht | Salat, Spinat, Zwiebeln (Schwachzehrer) |
| Anbaupause (Jahre) | 3 Jahre keine Cucurbitaceen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.9 | Drei-Schwestern-Mischkultur; Mais gibt Rankstütze | `compatible_with` |
| Bohne | Phaseolus vulgaris | 0.9 | Drei-Schwestern; N-Fixierung | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Ablenkpflanze | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Konkurrenz, ähnliche Schädlinge | moderate | `incompatible_with` |
| Gurke | Cucumis sativus | Gleiche Familie, Mehltau-Übertragung | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Riesenkürbis |
|-----|-------------------|-------------|--------------------------------|
| Zucchini | Cucurbita pepo | Gleiche Familie, kompakter | Kürzere Reifezeit, platzsparend |
| Butternut-Kürbis | Cucurbita moschata | Ähnliche Kultur | Bessere Lagerfähigkeit |
| Patisson | Cucurbita pepo | Gleiche Familie | Kompakter, früher reif |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Cucurbita maxima,"Riesenkürbis;Hokkaido-Kürbis;Pumpkin;Winter Squash",Cucurbitaceae,Cucurbita,annual,day_neutral,vine,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Südamerika",limited,80,40,50,300,175,no,limited,false,true,heavy_feeder,tender,"5;6","9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hokkaido (Red Kuri),Cucurbita maxima,Japan,–,"red_skin;nutty_flavor;small",110,,open_pollinated
Atlantic Giant,Cucurbita maxima,–,–,"giant;exhibition",120,,open_pollinated
```

---

## Quellenverzeichnis

1. [Kürbisse — Der Bio-Gärtner](https://www.bio-gaertner.de/Pflanzen/Kuerbisse) — Bio-Anbau
2. [Kürbis pflanzen — Plantura](https://www.plantura.garden/gemuese/kuerbis/kuerbis-pflanzen) — Pflege, Zeitplan
3. [Ökologischer Kürbisanbau — oekolandbau.de](https://www.oekolandbau.de/landwirtschaft/pflanze/spezieller-pflanzenbau/gemuese/feldgemuesebau/kuerbisse/) — NPK, Anbau
4. [Floragard Cucurbita maxima](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/gemuese/cucurbita-maxima) — Pflanzendaten
