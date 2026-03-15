# Korallenmyrte, Spitzblume — Ardisia crenata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gartenflora — Ardisia crenata](https://www.gartenflora.de/gartenwissen/pflanzenlexikon/spitzblume-ardisia-crenata/), [Zimmerpflanzen-Portal](https://www.zimmerpflanzen-portal.de/ardisia-crenata-spitzblume/), [Baldur-Garten — Ardisia](https://www.baldur-garten.de/onion/content/pflege-tipps/zimmerpflanzen/ardisia), [PictureThis](https://www.picturethisai.com/de/wiki/Ardisia_crenata.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ardisia crenata | `species.scientific_name` |
| Synonyme | Ardisia crenulata, Icacorea crenulata | — |
| Volksnamen (DE/EN) | Korallenmyrte, Spitzblume, Korallenbeere, Ardisie; Coral Ardisia, Coralberry, Spiceberry | `species.common_names` |
| Familie | Primulaceae | `species.family` → `botanical_families.name` |
| Gattung | Ardisia | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — als Zimmerpflanze kultiviert. Im Winter kühl stellen (12–16°C) für Ruhephase und bessere Beerenentwicklung. | `species.hardiness_detail` |
| Heimat | Ostasien — Japan, China, Taiwan, subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Korallenmyrte ist eine der wenigen Zimmerpflanzen, die im Herbst/Winter mit roten Beeren dekoriert. Die kleinen, stern- bis sternförmigen weißen bis hellrosa Blüten erscheinen im Sommer, die leuchtend roten (gelegentlich weißen oder gelben) Beeren reifen im Herbst und bleiben bis ins Frühjahr am Strauch. Sie ist NICHT giftig im Sinne von akuter Gefährlichkeit, aber die Beeren sollten trotzdem nicht in großen Mengen gegessen werden — insbesondere von Kleinkindern fernhalten. In Nordamerika wird sie als invasive Pflanze eingestuft (Florida, Hawaii).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt (Zierpflanze — Beeren) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (kleine weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Samen aus reifen Beeren — Fruchtfleisch entfernen, frisch aussäen (Keimung in 4–8 Wochen bei 20–22°C). Stecklinge 8–10 cm im Sommer, mit Bewurzelungshormon. Pflanzen aus Samen entwickeln erst nach 2–3 Jahren die charakteristischen Beeren.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | berries, leaves (Beeren bei Massenverzehr) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | ardisiacrispin_A_B (Saponine), bergenin | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (nach der Beerenperiode) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 50–100 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, humusreiche Kübelpflanzenerde. pH 6.0–6.5. Einheitserde + 15% Perlite. Leicht saure Substrate werden toleriert. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Wachstum/Blüte (Frühling/Sommer) | 150–180 | 1 | false | false | medium |
| Beerenreife (Herbst) | 60–90 | 2 | false | false | medium |
| Winterruhe (Winter) | 90–120 | 3 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum/Blüte (März–August)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Wachstum/Blüte | 2:1:2 | 0.6–1.0 | 6.0–6.5 | 60 | 25 |
| Beerenreife | 1:2:2 | 0.6–1.0 | 6.0–6.5 | 60 | 25 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 5 ml/L | Blüte/Beere |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Alle 14 Tage März bis August. September bis Oktober reduzieren. November bis Februar kein Dünger. Die Winterkühlephase (12–16°C) ist wichtig für die Knospenbildung der Blüten und damit die spätere Beerenentwicklung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat leicht feucht halten — nicht austrocknen, keine Staunässe; im Winter deutlich weniger gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Planococcus citri | Wollflecken, besonders im Winter | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder an Trieben | medium |
| Spinnmilbe | Tetranychus urticae | Gespinste bei trockener Heizungsluft | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |
| Blattflecken | fungal | Braune Flecken | Staunässe, nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Schale mit Kieselsteinen + Wasser | 0 | Spinnmilben (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen auf Schildläuse | 0 | Schildläuse, Wollläuse |
| Neemöl | biological | Sprühen 0.5% | 0 | Alle Schädlinge |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Ilex | Ilex aquifolium | Winterbeeren, ähnliche Ästhetik | Für Freiland, härter |
| Skimmia | Skimmia japonica | Winterbeerenstrauch | Balkon, robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Ardisia crenata,"Korallenmyrte;Spitzblume;Korallenbeere;Ardisie;Coral Ardisia;Coralberry",Primulaceae,Ardisia,perennial,day_neutral,shrub,fibrous,"8a;8b;9a;9b;10a;10b;11a","Ostasien (Japan, China, Taiwan)",yes,3-10,20,50-100,30-60,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gartenflora — Ardisia crenata](https://www.gartenflora.de/gartenwissen/pflanzenlexikon/spitzblume-ardisia-crenata/) — Pflege, Botanische Einordnung
2. [Zimmerpflanzen-Portal — Ardisia](https://www.zimmerpflanzen-portal.de/ardisia-crenata-spitzblume/) — Kulturdaten
3. [Baldur-Garten — Ardisia](https://www.baldur-garten.de/onion/content/pflege-tipps/zimmerpflanzen/ardisia) — Pflegetipps
4. [PictureThis — Ardisia crenata](https://www.picturethisai.com/de/wiki/Ardisia_crenata.html) — Invasivität, Verbreitung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (leicht giftig — Saponine)
