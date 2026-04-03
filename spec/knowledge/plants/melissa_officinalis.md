# Zitronenmelisse — Melissa officinalis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Melissa officinalis, Plantura Lemon Balm, Wisconsin Horticulture Extension, Pflanzen-Kölle Zitronenmelisse, RHS Melissa officinalis

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Melissa officinalis | `species.scientific_name` |
| Volksnamen (DE/EN) | Zitronenmelisse, Gartenmelisse; Lemon Balm | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Melissa | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; oberirdische Teile sterben ab, Rhizom überwintert sicher; in Norddeutschland problemlos im Freiland | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Zentralasien; eingebürgert in Mitteleuropa | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (mehrfach je Saison; vor Blüte höchster Aromagehalt) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine; Rosmarin- und Kaffeesäure therapeutisch genutzt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 3 | `species.pruning_months` |

**Hinweis:** Vor der Blüte auf 10 cm zurückschneiden fördert frischen, aromatischen Austrieb. Nach der Ernte Ende August/September nochmals bodennah schneiden — treibt im Frühjahr kräftig aus. Verwilderte Pflanzen im März bodennah erneuern.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, humusreiche Kräutererde; pH 6,0–7,0; gute Drainage; kein Staunässe | — |

**Wichtig:** Melissa officinalis breitet sich durch Rhizome und Selbstaussaat stark aus. Im Beet Rhizomsperre oder regelmäßiges Ausgraben empfehlenswert. Im Topf gezügelt.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–14 | 1 | false | false | low |
| Sämling | 21–35 | 2 | false | false | low |
| Vegetativ (Frühjahr) | 28–42 | 3 | false | false | medium |
| Ernte-/Blütephase | 30–60 | 4 | false | true | medium |
| Rückschnitt & Regeneration | 21–35 | 5 | false | true | high |
| Winterruhe | 120–150 | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–100 (Lichtkeimer — nicht abdecken) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Substrat gleichmäßig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Frühjahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Ernte-/Blütephase

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | – | – | – | – |
| Sämling | 1:1:1 | 0.4–0.6 | 6.0–6.5 | 60 | 30 | – | 1 |
| Vegetativ | 2:1:1 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | – | 2 |
| Ernte-/Blüte | 1:1:2 | 0.8–1.0 | 6.0–6.5 | 80 | 40 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung → Sämling | time_based | 12–14 Tage | Keimblätter vollständig entwickelt |
| Sämling → Vegetativ | time_based | 28–35 Tage | 3–4 echte Blattpaare sichtbar |
| Vegetativ → Ernte/Blüte | time_based | 35–42 Tage | Pflanze 20–30 cm hoch; Ernte jederzeit möglich |
| Ernte/Blüte → Regeneration | event_based | – | Rückschnitt auf 10 cm durchgeführt |
| Regeneration → Winterruhe | time_based | 35 Tage | Temperatur < 5°C, Tage kürzer als 10h |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch | 30–50 g/m² | März–April | Frühjahrsstart |
| Kräuterdünger | Neudorff Azet | organisch | 30 g/m² | April, Juni | light_feeder |
| Kompost | eigen | organisch | 2–3 L/m² | März | Bodenverbesserung |
| Balkonpflanzen-Dünger flüssig | Substral | organisch-mineral | 10 ml/10L alle 14 Tage | April–August | Topfkultur |

#### Hinweis zur Düngung

Zitronenmelisse ist ein ausgesprochener Schwachzehrer. Zu viel Stickstoff fördert üppiges Wachstum, vermindert aber den ätherischen Ölgehalt (Citral, Citronellal) und damit das Aroma. Einmalige Kompostgabe im Frühjahr reicht für Freilandpflanzen. Topfpflanzen alle 3–4 Wochen schwach düngen.

### 3.2 Besondere Hinweise zur Düngung

Zitronenmelisse ist Lamiaceae — wie Salbei, Thymian und Oregano ein mediterran adaptiertes Schwachzehrer-Kraut. Der Aromagehalt steigt bei Nährstoffmangel. Zu reiche Böden produzieren zwar mehr Biomasse, aber weniger Citral. Im Topf minimale Flüssigdüngung (niedrige Konzentration) alle 2–3 Wochen während der Wachstumsphase ausreichend. Kein Dünger ab September.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser verträglich; pH 6,0–7,0; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Vorkultur starten | Innen bei 18–22°C; Lichtkeimer nicht abdecken | mittel |
| Mär | Freilandpflanzen schneiden | Alte Triebe bodennah; Neuaustrieb fördern | hoch |
| Apr | Auspflanzen | Ab 5°C Bodentemperatur; Abstand 30–40 cm | hoch |
| Mai | Erste Ernte | Triebspitzen ernten; Bücher frisch verwenden | mittel |
| Jun | Rückschnitt vor Blüte | Auf 10–15 cm; verhindert Selbstaussaat; fördert Aromagehu. | hoch |
| Jul–Aug | Laufende Ernte | Morgens ernten (höchster Ölgehalt); bis zu 3× pro Saison | mittel |
| Aug | Zweiter Rückschnitt | Nach zweiter Ernte; fördert frischen Herbstaustrieb | mittel |
| Okt | Ausläufer kontrollieren | Rhizomausbreitung einschränken; Ausdünnen | niedrig |
| Nov | Mulchen (Topf) | Topfpflanzen schützen oder ins Kalthaus (ab -5°C) | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen; klebrige Ausscheidungen | shoot, leaf | vegetative | easy |
| Zikaden | Empoasca spp. | Weißliche Stippen auf Blättern | leaf | vegetative, flowering | medium |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, Blattaufhellung | leaf | flowering (Trockenheit) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal (Erysiphe spp.) | Weißer mehliger Belag auf Blättern | Trockenheit + warme Tage | 5–10 | vegetative (späte Saison) |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel; Welke | Nässe, Staunässe | 3–7 | alle bei Feuchtigkeit |
| Rostpilz | fungal (Puccinia spp.) | Orangebraune Pusteln auf Blattunterseite | Hohe Luftfeuchtigkeit | 7–14 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliege) | Blattläuse | 5–10 Larven | 14 |
| Marienkäfer | Blattläuse | freilassen | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% Lösung sprühen | 3 | Blattläuse, Zikaden |
| Schmierseifenlösung | biological | Kaliumpalmitat | 1–2% sprühen | 1 | Blattläuse |
| Schwefelbrühe | biological | Schwefel | Stäuben/Spritzen | 3 | Mehltau |
| Standort verbessern | cultural | – | Luftzirkulation erhöhen | 0 | Mehltau, Botrytis |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Lippenblütler (Lamiaceae) |
| Empfohlene Vorfrucht | Leguminosen (Erbse, Bohne) oder nährstoffarme Parzellen |
| Empfohlene Nachfrucht | Starkzehrer (Kürbis, Kohl) profitieren von leicht verbessertem Boden |
| Anbaupause (Jahre) | 3 Jahre selbe Familie (Lamiaceae) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Melissendiff zieht Bestäuber; soll Tomatenaroma verbessern | `compatible_with` |
| Kohl (alle Arten) | Brassica oleracea | 0.8 | Zitronenaroma verwirrt Kohlfliege und Kohlmotte | `compatible_with` |
| Echinacea | Echinacea purpurea | 0.8 | Gleiche Standortansprüche; Bestäubermagnet | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Bestäuberanlockung; gute Nachbarschaft | `compatible_with` |
| Rosmarien | Salvia rosmarinus | 0.7 | Gleiche mediterrane Bedürfnisse | `compatible_with` |
| Kamille | Matricaria chamomilla | 0.8 | Gegenseitige Aromaförderung; Bestäuber | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Thymian | Thymus vulgaris | Konkurrenz um gleichen Nährstoffraum; ähnliche Ausbreitung | mild | `incompatible_with` |
| Salbei | Salvia officinalis | Gleiche Familie; Schädlingsdruck teilen | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Lamiaceae | `shares_pest_risk` | Mehltau, Blattläuse | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Melissa officinalis |
|-----|-------------------|-------------|--------------------------------------|
| Zitronenthymian | Thymus × citriodorus | Zitronenaroma | Kompakter; trockener Standort; weniger invasiv |
| Pfefferminze | Mentha × piperita | Gleiche Familie | Stärkeres Minzaroma; sehr pflegeleicht |
| Zitronenverbene | Aloysia citrodora | Zitronenaroma | Intensiveres Aroma; Topfkultur; nicht winterhart |
| Zitronenbasilikum | Ocimum × citriodorum | Zitronenaroma | Jährlich neu; kein Ausbreitungsproblem |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Melissa officinalis,"Zitronenmelisse;Gartenmelisse;Lemon Balm",Lamiaceae,Melissa,perennial,long_day,herb,rhizomatous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.1,"Mittelmeerraum, Zentralasien",yes,7,20,80,60,35,limited,yes,false,false,light_feeder,false,hardy,"6;7;8"
```

---

## Quellenverzeichnis

1. [Naturadb Melissa officinalis](https://www.naturadb.de/pflanzen/melissa-officinalis/) — Steckbrief, Winterhärte
2. [Plantura Lemon Balm Overview](https://plantura.garden/uk/herbs/lemon-balm/lemon-balm-overview) — Anbau, Pflege, Ernte
3. [Wisconsin Horticulture Extension — Lemon Balm](https://hort.extension.wisc.edu/articles/lemon-balm-melissa-officinalis/) — Kulturdaten
4. [Pflanzen-Kölle Zitronenmelisse](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-zitronenmelisse-richtig/) — Pflege, Düngung
5. [Lemon Balm Companion Plants — Cultivated Earth](https://cultivatedearth.com/en/herbs/lemon-balm-companion-plants/) — Mischkultur
