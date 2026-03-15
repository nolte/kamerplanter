# Kohlrabi — Brassica oleracea var. gongylodes

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Kohlrabi, Bio-Gärtner.de, LWK Niedersachsen, Beetfreunde.de

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. gongylodes | `species.scientific_name` |
| Volksnamen (DE/EN) | Kohlrabi, Oberrübe; Kohlrabi, Turnip Cabbage | `species.common_names` |
| Familie | Brassicaceae | `species.family` → `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | biennial (als Gemüse einjährig kultiviert) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Jungpflanzen frostempfindlich; ausgewachsene Pflanzen überstehen −5 °C; Frühkohlrabi März–April mit Vlies | `species.hardiness_detail` |
| Heimat | Kultiviert (Wildform: Mittelmeerraum) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkultur Februar–März) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5, 6, 7, 8 (Staffelaussaat möglich) | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9, 10 (Frühsorten ab Mai) | `species.harvest_months` |
| Blütemonate | 5, 6 (zweites Jahr, falls nicht geerntet) | `species.bloom_months` |

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
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (mind. 10 L, kompakte Sorten) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 25–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche Kräutererde, pH 6,0–7,5; gleichmäßig feucht halten | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ / Knollenbildung | 30–60 | 3 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ & Knollenbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (gleichmäßige Feuchte → kein Platzen der Knolle) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 2:1:1 | 0.8–1.2 | 6.5–7.0 | 80 | 40 | — | 2 |
| Knollenbildung | 2:1:2 | 1.2–1.8 | 6.5–7.5 | 120 | 50 | 20 | 2 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 3–4 L/m² | Vor der Aussaat |
| Hornmehl | Oscorna | organisch-N | 40–60 g/m² | Vor der Pflanzung |

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Gemüsedünger | Compo | base | 12-7-14 | 30–50 g/m² | Wachstum |

### 3.2 Besondere Hinweise zur Düngung

Kohlrabi ist Mittelzehrer und braucht keine intensive Düngung bei gutem Boden. Zu viel Stickstoff führt zu übermäßigem Blattwachstum. Gleichmäßige Wasserversorgung ist entscheidend — Trockenheit gefolgt von starker Bewässerung führt zum Platzen der Knolle. Kalkversorgung für Calciumaufnahme sicherstellen (verhindert Herzfäule).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig feucht — kein Austrocknen; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur | Aussaat in Anzuchttöpfe bei 15–18 °C | mittel |
| Apr | Auspflanzen (Frühsatz) | Mit Vlies vor Frost schützen | hoch |
| Mai–Jun | Jäten und Gießen | Unkrautfreihalten; gleichmäßig gießen | mittel |
| Jun–Jul | Ernte Frühsatz | Knolle bei 5–8 cm Durchmesser ernten | hoch |
| Jul–Aug | Nachsatz aussäen | Für Herbst-Kohlrabi | mittel |
| Sep–Okt | Herbst-Ernte | Spätsorten vor starkem Frost ernten | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweißling | Pieris brassicae / P. rapae | Kahlfraß, Kotspuren | leaf | vegetative | easy |
| Erdfloh | Phyllotreta spp. | Kleine Löcher (Schrotschuss-Muster) | leaf | seedling | medium |
| Mehlige Kohlblattlaus | Brevicoryne brassicae | Weißliche Kolonien, Kräuselung | leaf | vegetative | easy |
| Kohlfliege | Delia radicum | Larvenbefall an Wurzeln, Welke | root | seedling | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Clubwurzel (Kohlhernie) | protist (Plasmodiophora brassicae, Phytomyxea; KEIN Pilz) | Knollenartige Wurzelwucherungen | saurer Boden (pH < 6,5) | 14–21 | all |
| Falscher Mehltau | fungal | Gelbe Flecken, weißer Belag | Feuchtigkeit | 5–10 | seedling |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Feinmaschig | 0 | Kohlweißling, Kohlfliege, Erdfloh |
| Bt-Präparat | biological | Bacillus thuringiensis | Sprühen | 0 | Kohlweißling |
| Kalkung | cultural | Algenkalk | 100 g/m² | 0 | Clubwurzel |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kreuzblütengewächse (Brassicaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte, Erbsen |
| Empfohlene Nachfrucht | Möhren, Zwiebeln, Salat |
| Anbaupause (Jahre) | 3–4 Jahre keine Brassicaceen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sellerie | Apium graveolens | 0.8 | Gegenseitige Förderung, Erdfloh-Abwehr | `compatible_with` |
| Dill | Anethum graveolens | 0.8 | Nützlingsförderung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Platzsparend, Bodenbeschattung | `compatible_with` |
| Zwiebeln | Allium cepa | 0.7 | Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Schlechte Verträglichkeit | moderate | `incompatible_with` |
| Alle Brassicaceen | Brassica spp. | Gleiche Schädlinge, Clubwurzel | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Kohlrabi |
|-----|-------------------|-------------|---------------------------|
| Brokkoli | Brassica oleracea var. italica | Gleiche Familie | Höherer Nährwert, länger haltbar |
| Steckrübe | Brassica napus | Knollengemüse | Winterhärter, lagerfähiger |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Brassica oleracea var. gongylodes,"Kohlrabi;Oberrübe;Turnip Cabbage",Brassicaceae,Brassica,biennial,long_day,herb,fibrous,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Kultiviert (Wildform: Mittelmeerraum)",yes,15,20,50,40,28,no,yes,false,false,medium_feeder,half_hardy,"4;5;6;7;8","5;6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Plantura Kohlrabi](https://www.plantura.garden/gemuese/kohlrabi) — Anbau, Erntezeit, Pflege
2. [Beetfreunde.de Kohlgemüse](https://www.beetfreunde.de/magazin/kohlgemuese/) — Sortenüberblick
3. [LWK Niedersachsen](https://www.lwk-niedersachsen.de/) — Regionaler Anbau Norddeutschland
4. [Heimbiotop.de Brassica](https://www.heimbiotop.de/brassica.html) — Kohl-Übersicht
