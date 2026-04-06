# Zebra-Hauswurz — Haworthiopsis fasciata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Joy Us Garden](https://www.joyusgarden.com/zebra-succulent-care-a-beginners-haworthia-growing-guide/), [NC State Extension](https://plants.ces.ncsu.edu/plants/haworthiopsis-fasciata/), [Epic Gardening](https://www.epicgardening.com/haworthiopsis-fasciata/), [Succulents and Sunshine](https://www.succulentsandsunshine.com/types-of-succulents/haworthia-fasciata-zebra-plant/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Haworthiopsis fasciata | `species.scientific_name` |
| Synonyme | Haworthia fasciata (älterer, noch gebräuchlicher Name) | — |
| Volksnamen (DE/EN) | Zebra-Hauswurz, Zebra-Haworthia; Zebra Plant, Zebra Cactus, Zebra Haworthia | `species.common_names` |
| Familie | Asphodelaceae | `species.family` → `botanical_families.name` |
| Gattung | Haworthiopsis | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — toleriert kurze Fröste bis -1°C trocken. Mindesttemperatur 5°C dauerhaft, optimal 15–27°C. Bei Nässe frostempfindlich. | `species.hardiness_detail` |
| Heimat | Südafrika (Ostkap-Provinz) — Felsen und Buschland | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Haworthiopsis fasciata ist eine der schattenverträglichsten Sukkulenten — ideal für Windowsills ohne direkte Mittagssonne. Verwechslungsgefahr mit Haworthia attenuata (ebenfalls als "Zebra-Haworthia" gehandelt) — bei H. fasciata sind die weißen Querstreifen glatter und punktförmig auf der Blattunterseite, bei H. attenuata sind sie rauer und auch auf der Blattoberseite. Sehr geeignet für Anfänger.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6 (weiß-rosa Röhrenblüten auf langen Stängeln) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) entstehen spontan an der Basis. Bei 4–5 cm Größe abtrennen, 1–2 Tage Schnittstelle trocknen lassen, in trockenes Kakteensubstrat pflanzen. Bewurzelung in 3–5 Wochen.

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
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–20 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–20 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde mit 30% Perlite. pH 6.5–7.5. Sehr gute Drainage. Flache Schalen bevorzugt. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Herbst) | 180–210 | 1 | false | false | very high |
| Sommer-Dormanz / Winterruhe | 90–120 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–Mai, September–November)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sommer-Dormanz/Winterruhe (Juni–August, Dezember–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–20 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.5–7.5 | 30 | 10 |
| Dormanz/Ruhe | 0:0:0 | 0.0 | 6.5–7.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (1–2×/Saison) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Extrem leichter Zehrer. Nur 1–2 Düngergaben pro Jahr im Frühjahr ausreichend. Kein Dünger im Sommer (Dormanz) und Winter. Überdüngung ist die häufigste Pflegefehler-Ursache.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 21–28 (Sommer = Halbdormanz) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; vollständig abtrocknen lassen vor nächstem Gießen; nicht auf die Blätter gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 90 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–5, 9–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Weiche, braune Basis, Pflanze löst sich | Überwässerung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Intervall verlängern | 0 | Wurzelfäule (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Rauhe Haworthia | Haworthiopsis attenuata | Gleiche Gattung | Ähnliche Pflege, rauere Querstreifen |
| Aloe vera | Aloe vera | Gleiche Familie | Größer, medizinische Nutzung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Haworthiopsis fasciata,"Zebra-Hauswurz;Zebra-Haworthia;Zebra Plant;Zebra Cactus",Asphodelaceae,Haworthiopsis,perennial,day_neutral,herb,fibrous,"9b;10a;10b;11a;11b","Südafrika (Ostkap-Provinz)",yes,0.5-2,8,10-20,10-20,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Joy Us Garden — Zebra Succulent](https://www.joyusgarden.com/zebra-succulent-care-a-beginners-haworthia-growing-guide/) — Pflegehinweise
2. [NC State Extension — Haworthiopsis fasciata](https://plants.ces.ncsu.edu/plants/haworthiopsis-fasciata/) — Botanische Daten
3. [Epic Gardening — Haworthiopsis fasciata](https://www.epicgardening.com/haworthiopsis-fasciata/) — Kulturdaten
4. [Succulents and Sunshine — Haworthia fasciata](https://www.succulentsandsunshine.com/types-of-succulents/haworthia-fasciata-zebra-plant/) — Artunterschiede
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
