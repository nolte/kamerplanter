# Knoblauch — Allium sativum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Knoblauch, NaturaDB Allium sativum, OBI Knoblauch, Lubera Knoblauch pflanzen

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Allium sativum | `species.scientific_name` |
| Volksnamen (DE/EN) | Knoblauch, Echter Knoblauch; Garlic | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` → `botanical_families.name` |
| Gattung | Allium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
| Lebenszyklus | perennial (als Gemüse einjährig kultiviert) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −20 °C im Boden; Herbstpflanzung überwintert problemlos in Norddeutschland | `species.hardiness_detail` |
| Heimat | Zentralasien (Kirgistan, Tadschikistan) | `species.native_habitat` |
| Allelopathie-Score | 0.4 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Herbstpflanzung bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Frühjahrspflanzung möglich aber kleinere Ernte) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 9, 10, 11 (Herbst, optimal), 3, 4 (Frühjahr) | `species.direct_sow_months` |
| Erntemonate | 6, 7 (Herbstknoblauch), 8 (Frühjahrsknoblauch) | `species.harvest_months` |
| Blütemonate | 6, 7 (Scape = Knoblauchschaft) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset (Zehen aus der Knolle) | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (in normalen Mengen) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile für Katzen und Hunde | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Allicin, Alliin, Thiosulfate (für Tiere: hämolytische Anämie) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (Menschen); severe (Katzen/Hunde) | `species.toxicity.severity` |
| Kontaktallergen | true (Allicin-Kontaktdermatitis möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Scape/Blütenschaft abschneiden) | `species.pruning_type` |
| Rückschnitt-Monate | 6 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (Töpfe mind. 20 cm tief) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–15 cm in Reihe, 25–30 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | limited (Küchenfenster für Grün) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut drainierte Erde, pH 6,0–7,0; kein Staunässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Verwurzelung (Herbst) | 30–60 | 1 | false | false | medium |
| Winterruhe / Dormanz | 60–90 | 2 | false | false | high |
| Austrieb (Frühjahr) | 14–21 | 3 | false | false | medium |
| Vegetativ | 42–70 | 4 | false | false | medium |
| Reife (Einzug) | 14–21 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Frühjahr/Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (trockenverträglich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Verwurzelung | 1:2:1 | 0.5–0.8 | 6.0–7.0 | 60 | 30 | — | 1 |
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–7.0 | 80 | 40 | 20 | 2 |
| Reife | 0:0:1 | 0.5–0.8 | 6.0–7.0 | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 2–3 L/m² | Vor der Pflanzung |
| Hornmehl | Oscorna | organisch-N | 30–50 g/m² | Frühjahrsaustrieb |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Schwefelsaures Kali | diverse | supplement | 0-0-50+18S | 20–30 g/m² | Reife |

### 3.2 Besondere Hinweise zur Düngung

Knoblauch ist ein Schwachzehrer — bei gut versortem Boden ist keine Düngung notwendig. Überdüngung (N) fördert Blattwachstum und hemmt die Knollenbildung. Der Scape (Knoblauchschaft bei Hardneck-Sorten) sollte im Juni abgeschnitten werden, um die Energie in die Knolle zu leiten. Schwefeldüngung fördert die Aromastoffe (Allicin-Vorstufe).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 (kaum gießen im Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Staunässe unbedingt vermeiden; trockenverträglich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jährlich neue Zehen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Sep–Nov | Herbstpflanzung | Zehen 5 cm tief, Spitze nach oben, 15 cm Abstand | hoch |
| Nov–Feb | Winterpflege | Kaum Pflege nötig; bei starkem Frost leicht mulchen | niedrig |
| Mär | Austreiben beobachten | Erste grüne Triebe; ggf. Mulch entfernen | niedrig |
| Apr–Mai | Jäten | Unkrautfreihalten wichtig | mittel |
| Jun | Scape abschneiden | Bei Hardneck-Sorten Blütenschaft abschneiden für größere Knolle | hoch |
| Jun–Jul | Ernte | Wenn 2/3 des Laubs braun ist; trocken und sonnig ernten | hoch |
| Jul–Aug | Trocknung | 3–4 Wochen hängend oder auf Rost trocknen | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Zwiebelfliege | Delia antiqua | Larvenbefall in der Knolle, Fäulnis | root | seedling, vegetative | difficult |
| Thripse | Thrips tabaci | Silbrige Streifen, Wachstumsrückstand | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Weißfäule | fungal (Sclerotium cepivorum) | Weißes Myzel an Basis, Fäulnis | Feuchte Böden, Kälte | 14–28 | vegetative, ripening |
| Falscher Mehltau | fungal (Peronospora destructor) | Grau-violetter Belag auf Blättern | Feuchtigkeit | 7–14 | vegetative |
| Rost | fungal (Puccinia allii) | Orangefarbene Pusteln auf Blättern | Feuchtigkeit, Wärme | 7–14 | vegetative |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Fruchtfolge (3 Jahre) | cultural | — | Keine Lauchgewächse 3 Jahre | 0 | Weißfäule, Nematoden |
| Pflanzabstand einhalten | cultural | — | 15 cm zwischen Zehen | 0 | Mehltau |
| Knoblauchzehen-Beizung | biological | Trichoderma | Vor Pflanzung in Lösung tauchen | 0 | Weißfäule |
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 3 | Thripse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Lauchgewächse (Amaryllidaceae/Alliaceae) |
| Empfohlene Vorfrucht | Tomaten, Kohlarten, Kürbis |
| Empfohlene Nachfrucht | Möhren, Salat, Spinat |
| Anbaupause (Jahre) | 3 Jahre selbe Familie |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rose | Rosa spp. | 0.9 | Knoblauchduft schützt vor Läusen und Pilzen | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Fungizide Wirkung von Allicin | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Gegenseitige Schädlingsverwirrung | `compatible_with` |
| Erdbeere | Fragaria × ananassa | 0.8 | Schützt vor Grauschimmel | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Erbse | Pisum sativum | Knoblauchduft hemmt Keimung und Wachstum | moderate | `incompatible_with` |
| Bohne | Phaseolus vulgaris | Allelopathische Hemmung | moderate | `incompatible_with` |
| Kohl | Brassica oleracea | Konkurrenz bei engem Stand; in vielen Quellen jedoch als neutral bis förderlich bewertet (Knoblauchduft hält Kohlweißling fern) | mild | `neutral` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Knoblauch |
|-----|-------------------|-------------|------------------------------|
| Bärlauch | Allium ursinum | Mildes Knoblauch-Aroma | Waldpflanze, keine Pflanzung nötig, winterhart |
| Schnittknoblauch | Allium tuberosum | Ähnliches Aroma | Mehrjährig, Ernte des Grüns ganzjährig |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Allium sativum,"Knoblauch;Echter Knoblauch;Garlic",Amaryllidaceae,Allium,perennial,long_day,herb,bulbous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.4,"Zentralasien",yes,8,20,60,15,15,limited,yes,false,false,light_feeder,hardy,"9;10;11;3;4","6;7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Thermidrome,Allium sativum,–,–,"softneck;good_storage",240,,open_pollinated
Riesendornburger,Allium sativum,–,–,"hardneck;large_cloves",230,,open_pollinated
Morado de Pedroñeras,Allium sativum,–,–,"softneck;spanish",240,,open_pollinated
```

---

## Quellenverzeichnis

1. [Knoblauch pflanzen — Plantura](https://www.plantura.garden/gemuese/knoblauch/knoblauch-pflanzen) — Anbau, Pflege
2. [NaturaDB Allium sativum](https://www.naturadb.de/pflanzen/allium-sativum/) — Stammdaten
3. [OBI Knoblauch pflanzen](https://www.obi.de/magazin/garten/pflanzen/gemuesepflanzen/knoblauch-pflanzen) — Praxistipps
4. [Lubera Knoblauch](https://www.lubera.com/de/gartenbuch/knoblauch-pflanzen-p4430) — Anbau-Details
