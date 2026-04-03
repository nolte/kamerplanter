# Pastinake — Pastinaca sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Pastinaken, Samen.de Pastinaken, Kraut&Rüben Pastinaken, LandBZL Pastinaken

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pastinaca sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Pastinake, Hammermöhre (Norddeutschland), Hirschmöhre; Parsnip | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Pastinaca | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | biennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis -15°C; Wurzeln im Boden überwintern problemlos; Frost verbessert Aroma (Stärke → Zucker); ideal für Norddeutschland; ganzjährige Ernte möglich | `species.hardiness_detail` |
| Heimat | Eurasien, Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (keine Vorkultur — Pfahlwurzel verträgt Verpflanzen nicht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -28 (Frühaussaat ab Februar/März möglich; langsamste Keimung aller Gemüse) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 2, 3, 4, 5, 6 | `species.direct_sow_months` |
| Erntemonate | 10, 11, 12, 1, 2, 3 (nach erstem Frost am süßesten; ganzjährig im Boden lassen) | `species.harvest_months` |
| Blütemonate | 6, 7 (2. Jahr; dann absterbend) | `species.bloom_months` |

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
| Giftige Pflanzenteile | Blätter und Stängel bei Sonnenkontakt (phototoxisch) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Furanocumarine (phototoxisch; Hautrötung/-blasen bei Sonnenkontakt nach Kontakt mit Blättern) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Phototoxizität bei Sonnenkontakt — Handschuhe beim Ernten tragen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Apiaceae-Kreuzallergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–15 in der Reihe; Reihenabstand 25–30 cm | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (ausschließlich Freilandkultur; tiefe Pfahlwurzel braucht lockeren, tiefen Boden) | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–28 | 1 | false | false | low |
| Sämling | 21–42 | 2 | false | false | medium |
| Vegetativ (Wurzelaufbau) | 90–130 | 3 | false | false | high |
| Reife | 30–90 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wurzelaufbau)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (trockenverträglich nach Keimung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.6 | 6.0–7.0 | 60 | 25 | — | 2 |
| Vegetativ | 1:1:2 | 0.8–1.2 | 6.0–7.0 | 100 | 40 | — | 2 |
| Reife | 0:1:2 | 0.6–0.8 | 6.0–7.0 | 80 | 30 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Reifer Kompost | eigen | organisch | 4–6 L/m² | Herbst vor Aussaatjahr | Wurzelgemüse |
| Horngrieß | Oscorna | organisch-N | 50–70 g/m² | Frühjahr | medium_feeder |

### 3.2 Besondere Hinweise zur Düngung

KEIN frischer Mist oder frischer Kompost — lockt Möhrenfliege an! Pastinaken brauchen lockeren, tief gegrabenen, steinfreien Boden für geradlinige Wurzeln. Auf humusreichem Boden, der im Vorjahr mit Kompost gedüngt wurde, ist meist keine weitere Düngung nötig. Stickstoff-Überschuss → üppiges Laub, kleine Wurzeln.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 (im Boden; natürliche Feuchtigkeit reicht) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig; Trockenheit verholzt Wurzeln; Staunässe verrottet sie | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (keine Saison-Düngung; Grundvorbereitung reicht) | `care_profiles.fertilizing_interval_days` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Nov (Vorjahr) | Kompostgabe | Reifen Kompost einarbeiten; tief lockern | mittel |
| Feb–Mär | Frühjahrsaussaat | Wenn Boden bearbeitbar; dünn säen; Keimung dauert 2–4 Wochen | hoch |
| Apr–Mai | Vereinzeln | Auf 10–15 cm ausdünnen (verdrängtes Kraut weggärtnern) | mittel |
| Apr | Insektennetz | Gegen Möhrenfliege; bei Befallsgefahr | hoch |
| Jul–Sep | Jäten | Unkraut; Pastinake ist langsam zu Beginn | niedrig |
| Okt–Mär | Ernte | Nach erstem Frost am süßesten; nach Bedarf ernten | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Möhrenfliege | Psila rosae | Fraßgänge in der Wurzel; brauner Mulm | root | vegetative, ripening | difficult |
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen | shoot | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Möhrenschwärze | fungal (Alternaria dauci) | Dunkle Blattflecken | Feuchtigkeit | 7–14 | vegetative |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 5–10 | vegetative, ripening |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz | cultural | — | 0,8 mm Maschenweite; ab Keimung | 0 | Möhrenfliege |
| Mischkultur Zwiebeln | cultural | — | Zwiebelduft verwirrt Möhrenfliege | 0 | Möhrenfliege |
| Fruchtwechsel | cultural | — | Keine Apiaceae auf gleicher Fläche | 0 | alle Krankheiten |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Doldenblütler (Apiaceae) |
| Empfohlene Vorfrucht | Leguminosen; Kohlgewächse (NICHT andere Apiaceae) |
| Empfohlene Nachfrucht | Starkzehrer (Kürbis, Kohl); kein Sellerie, Möhre, Fenchel |
| Anbaupause (Jahre) | 3–4 Jahre keine Apiaceae auf gleicher Fläche |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Zwiebel | Allium cepa | 0.9 | Möhrenfliegen-Abwehr durch Duft | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Möhrenfliegen-Abwehr | `compatible_with` |
| Porree | Allium porrum | 0.8 | Möhrenfliegen-Abwehr | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Bodenbeschattung; Platzsparend | `compatible_with` |
| Radieschen | Raphanus sativus var. sativus | 0.7 | Bodenlockerer; schnell wachsend | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Möhre | Daucus carota | Geteilter Schädling (Möhrenfliege) | severe | `incompatible_with` |
| Petersilie | Petroselinum crispum | Gleiche Familie; Möhrenfliege | severe | `incompatible_with` |
| Sellerie | Apium graveolens | Gleiche Familie; Konkurrenz | severe | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathie + geteilte Schädlinge | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Pastinake |
|-----|-------------------|-------------|------------------------------|
| Möhre | Daucus carota | Gleiche Familie; Wurzelgemüse | Schneller reif; vielseitiger |
| Sellerie | Apium graveolens | Gleiche Familie | Andere Verwendung; Stangensellerie |
| Petersilienwurzel | Petroselinum crispum var. tuberosum | Gleiche Familie | Intensiveres Aroma; kleiner |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Pastinaca sativa,"Pastinake;Hammermöhre;Parsnip",Apiaceae,Pastinaca,biennial,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Eurasien, Mittelmeer",no,no,no,false,false,medium_feeder,hardy,"2;3;4;5;6","10;11;12;1;2;3"
```

---

## Quellenverzeichnis

1. [Plantura Pastinaken](https://www.plantura.garden/gemuese/pastinaken/pastinaken-pflanzen) — Anbau, Mischkultur
2. [Samen.de Pastinaken](https://samen.de/blog/pastinaken-anbauen-vom-samen-zur-ernte.html) — Anbau, Pflege
3. [Kraut&Rüben Pastinaken](https://www.krautundrueben.de/steckbrief-pastinaken-saeen-pflegen-und-ernten-2547) — Steckbrief
4. [LandBZL Pastinaken](https://www.landwirtschaft.de/garten/selbst-anbauen/gemuesesteckbriefe/pastinaken-selbst-im-garten-anbauen) — Allgemein
