# Lippenstift-Pflanze — Aeschynanthus radicans

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/aeschynanthus-radicans-lipstick-plant-grow-care-guide), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/lipstick-plant-care-guide-growing-aeschynanthus-radicans-indoors/), [NC State Extension](https://plants.ces.ncsu.edu/plants/aeschynanthus-radicans/), [Plant Care Today](https://plantcaretoday.com/lipstick-plant.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aeschynanthus radicans | `species.scientific_name` |
| Synonyme | Aeschynanthus lobbianus | — |
| Volksnamen (DE/EN) | Lippenstift-Pflanze, Lippenstift-Blume; Lipstick Plant, Lipstick Vine, Basket Vine | `species.common_names` |
| Familie | Gesneriaceae | `species.family` → `botanical_families.name` |
| Gattung | Aeschynanthus | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 13°C, optimal 18–27°C. Für Blütenbildung kurze Kühlphase (15°C) im Herbst günstig. | `species.hardiness_detail` |
| Heimat | Südostasien (Malaysia, Indonesien) — tropische Regenwälder, epiphytisch | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Lippenstift-Pflanze ist ein tropischer Epiphyt — in der Natur wächst sie auf Bäumen, nicht im Boden. Der Name kommt von den leuchtend roten Blüten, die aus einem dunkelroten Kelch herausragen und tatsächlich einem herausgeschraubten Lippenstift ähneln. Hängende Kultivierung in Ampeln ist ideal — die Triebe können 60–90 cm lang werden. Zum Blühen benötigt die Pflanze etwas kühlere Temperaturen (ca. 15°C) im Herbst und reduzierte Bewässerung, um die Knospenbildung zu triggern.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 4, 5, 6, 7, 8 (nach Kühlphase im Herbst/Winter) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Kopfstecklinge 7–10 cm in Wasser oder feuchtes Substrat (Perlite + Torf). Bewurzelung in 2–4 Wochen bei 22–25°C. Stecklinge im Frühjahr schneiden.

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
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (nach der Blütezeit, Triebe um 1/3 kürzen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–6 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 (hängend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (windgeschützt, frostfrei, Halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (Ampelpflanze) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr luftige, gut drainierte Orchideenerde oder Mix aus Torf + Perlite + Orchidenbark (je 1/3). pH 6.0–7.0. Als Epiphyt braucht die Pflanze hervorragende Drainage. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–180 | 1 | false | false | medium |
| Kühlphase / Knospenruhe (Herbst) | 45–60 | 2 | false | false | medium |
| Blüte (Winter/Frühjahr) | 60–90 | 3 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kühlphase (Oktober–November)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 13–18 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.6–1.0 | 6.0–7.0 | 60 | 25 |
| Kühlphase | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — |
| Blüte | 1:2:2 | 0.6–1.0 | 6.0–7.0 | 50 | 20 |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Compo | base | 5-8-10 | 3 ml/L (monatlich) | Wachstum |
| Orchideen-Dünger | Substral | base | 5-5-7 | 3 ml/L | Wachstum/Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer als Epiphyt. Monatlich Mai bis September bei halber Empfehlungsdosis. Oktober bis April kein Dünger — Ruhephase ist wichtig für Blütenbildung. Phosphat-betonter Dünger in der Blütephase unterstützt die Blütenbildung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat zwischen Güssen leicht antrocknen lassen; als Epiphyt sehr drainagebedürftig — keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Pseudococcus spp. | Wollflecken, besonders Triebspitzen | easy |
| Blattläuse | Aphis spp. | Klebrige Triebe, deformierte Knospen | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |
| Blütenausfall | physiologisch | Knospen fallen ab | Zu warm im Herbst, zu viel Wasser |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Alkohol 70% | mechanical | Wattestäbchen auf Schmierläuse | 0 | Wollschildläuse |
| Neemöl | biological | Sprühen 0.5% | 0 | Alle Schädlinge |
| Kühlphase einhalten | cultural | Oktober–November bei 15°C | 0 | Blütenausfall (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Columnea | Columnea x banksii | Gesneriaceae, Ampelpflanze | Ähnliche Blütenform |
| Hoya carnosa | Hoya carnosa | Ampelpflanze, Zimmerpflanze | Pflegeleichter |
| Tradescantia | Tradescantia zebrina | Ampelpflanze | Sehr robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Aeschynanthus radicans,"Lippenstift-Pflanze;Lippenstift-Blume;Lipstick Plant;Lipstick Vine;Basket Vine",Gesneriaceae,Aeschynanthus,perennial,short_day,vine,aerial,"10a;10b;11a;11b","Südostasien (Malaysia, Indonesien)",yes,2-6,15,30-90,30-60,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Aeschynanthus radicans](https://www.gardenia.net/plant/aeschynanthus-radicans-lipstick-plant-grow-care-guide) — Botanische Daten
2. [Healthy Houseplants — Lipstick Plant](https://www.healthyhouseplants.com/indoor-houseplants/lipstick-plant-care-guide-growing-aeschynanthus-radicans-indoors/) — Pflegehinweise
3. [NC State Extension — Aeschynanthus radicans](https://plants.ces.ncsu.edu/plants/aeschynanthus-radicans/) — Botanische Klassifikation
4. [Plant Care Today — Lipstick Plant](https://plantcaretoday.com/lipstick-plant.html) — Schädlinge, Blütensteuerung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
