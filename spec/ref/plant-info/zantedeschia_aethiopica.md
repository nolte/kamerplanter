# Calla, Weiße Calla — Zantedeschia aethiopica

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/zantedeschia-aethiopica-calla-lily), [University of Florida IFAS](https://edis.ifas.ufl.edu/publication/FP065), [RHS — Royal Horticultural Society](https://www.rhs.org.uk/plants/zantedeschia/aethiopica/details), [ASPCA](https://www.aspca.org/), [NC State Extension](https://plants.ces.ncsu.edu/plants/zantedeschia-aethiopica/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Zantedeschia aethiopica | `species.scientific_name` |
| Synonyme | Calla aethiopica, Richardia africana | — |
| Volksnamen (DE/EN) | Calla, Weiße Calla, Zimmercalla, Sumpfcalla; Calla Lily, Arum Lily, White Arum Lily, Garden Calla | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Zantedeschia | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — im Kübel bei Frost reinbringen. Im Freiland in Zone 8+ mit Mulchschutz möglich. Rhizom verträgt kurze Fröste bis –5°C, aber keine Dauerfröste. | `species.hardiness_detail` |
| Heimat | Südafrika, Lesotho — feuchte Standorte, Flussufer, Sümpfe | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Calla ist botanisch kein Verwandter echter Lilien — sie gehört zur Araceae-Familie (Aronstabgewächse). Das weiße "Blütenblatt" ist kein Blütenblatt, sondern ein Hochblatt (Spatha), der eigentliche Blütenkolben (Spadix) ist der gelbe Stift im Inneren. GIFTIG — alle Pflanzenteile enthalten Calciumoxalat-Raphiden und sind für Haustiere und Kinder gefährlich (starke Schleimhautreizung, selten lebensbedrohlich). Bevorzugt feuchte bis nasse Standorte; im Topf darf das Substrat nie austrocknen. Sommerdormanz bei Trockenheit möglich, ist aber nicht obligat.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt (Rhizom-Pflanzung im Frühling) | `species.direct_sow_months` |
| Erntemonate | Entfällt (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6 (Hauptblütezeit Frühling bis Frühsommer) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Rhizomteilung beim Umtopfen im Herbst oder Frühjahr. Seitentriebe (Tochterpflanzen) vom Mutterrhizom trennen und einzeln einpflanzen. Bewurzelung schnell. Samenvermehrung möglich aber langsam (2–3 Jahre bis erste Blüte).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (alle Teile inkl. Rhizom, Spatha, Blätter) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (Calciumoxalat-Raphiden: starke Schleimhautreizung, Speichelfluss, Erbrechen; selten lebensbedrohlich) | `species.toxicity.severity` |
| Kontaktallergen | true (Pflanzensaft kann Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Sicherheitshinweis:** Sofort Tierarzt/Arzt kontaktieren bei Aufnahme. Beim Umtopfen Handschuhe tragen — Pflanzensaft ist ein Kontaktallergen. Symptome: Brennen im Mund, Speichelfluss, Erbrechen, Schwellungen der Schleimhäute.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (verblühte Blütenstände, Sommer nach der Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten bis Sonne, vor Frost schützen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Feuchtigkeitshaltende, humusreiche Erde. pH 6.0–6.5. Einheitserde + 20% Kokosfaser. Niemals austrocknen lassen — Calla liebt konstant feuchtes Substrat. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe / Einzug (Oktober–Februar) | 90–120 | 1 | false | false | medium |
| Austrieb / Vorblüte (Februar–März) | 30–45 | 2 | false | false | low |
| Hauptblüte (März–Juni) | 60–90 | 3 | false | false | medium |
| Nach der Blüte / Sommer (Juli–September) | 60–90 | 4 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 5–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 21–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptblüte (März–Juni)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–6.5 | — | — |
| Austrieb/Vorblüte | 3:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 30 |
| Hauptblüte | 1:2:2 | 1.0–1.8 | 6.0–6.5 | 100 | 40 |
| Nach der Blüte | 1:1:2 | 0.6–1.0 | 6.0–6.5 | 60 | 20 |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Flüssigdünger | Compo | base | 5-8-10 | 5 ml/L (alle 2 Wochen) | Blüte |
| Universaldünger | Substral | base | 7-3-7 | 5 ml/L | Austrieb |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | – | organisch | 50–80 g/Topf | Frühjahr |
| Kompost | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Mittelzehrer. Düngung von März bis August, alle 2 Wochen. In der Blütephase phosphat- und kalibetonten Dünger verwenden. Nach der Blüte bis Oktober reduzieren. Winterruhe ohne Dünger. Calla verträgt keine Trockenheit — Substrat während der Wachstumsphase immer feucht halten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat während der Wachstumsperiode konstant feucht halten — Calla liebt Wasser; in der Ruhephase stark reduzieren oder trockenstellen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Blattläuse | Aphis spp. | Klebrige Blätter, Honigtau, deformierte Blüten | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen auf Blättern | medium |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Weiche Rhizomfäule | bacterial (Pectobacterium spp.) | Fauliger Geruch, Rhizom braun-weich | Überfeuchte, hohe Temperaturen |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmelbelag auf Spatha/Blättern | Hohe Feuchtigkeit, schlechte Belüftung |
| Stängelfäule | fungal | Stängelbasis einschnürt sich, Welke | Überfeuchte, Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Befallene Teile entfernen | cultural | Sofort abschneiden und entsorgen | 0 | Grauschimmel, Fäulen |
| Bessere Belüftung | cultural | Abstand zwischen Pflanzen vergrößern | 0 | Grauschimmel (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Blattläuse, Thrips |
| Backpulverlösung | biological | Sprühen 0.5% | 0 | Grauschimmel |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zier-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Farbige Calla | Zantedeschia elliotiana | Gleiche Gattung | Gelbe/bunte Blüten, kompakter |
| Spathiphyllum | Spathiphyllum wallisii | Araceae, weiße Spatha | Pflegeleichter, weniger giftig |
| Anthurium | Anthurium andraeanum | Araceae, ähnliche Spatha | Langanhaltende Blüte, Indoor |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Zantedeschia aethiopica,"Calla;Weiße Calla;Zimmercalla;Sumpfcalla;Calla Lily;Arum Lily",Araceae,Zantedeschia,perennial,day_neutral,herb,rhizomatous,"8a;8b;9a;9b;10a;10b;11a","Südafrika, Lesotho",yes,5-15,20,60-120,40-80,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Zantedeschia aethiopica](https://www.gardenia.net/plant/zantedeschia-aethiopica-calla-lily) — Botanische Daten, Kulturbedingungen
2. [University of Florida IFAS](https://edis.ifas.ufl.edu/publication/FP065) — Wissenschaftliche Daten, Schädlinge
3. [RHS — Zantedeschia aethiopica](https://www.rhs.org.uk/plants/zantedeschia/aethiopica/details) — Winterhärte, Pflege
4. [NC State Extension — Zantedeschia aethiopica](https://plants.ces.ncsu.edu/plants/zantedeschia-aethiopica/) — Kulturdaten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (stark giftig — Calcium-Oxalate)
