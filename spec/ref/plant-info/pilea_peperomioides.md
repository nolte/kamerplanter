# Chinesische Geldpflanze — Pilea peperomioides

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [BBC Gardeners World](https://www.gardenersworld.com/house-plants/how-to-grow-pilea-peperomioides/), [Savvy Gardening](https://savvygardening.com/pilea-peperomioides-care/), [PLNTS.com](https://plnts.com/en/care/houseplants-family/pilea), [The Little Botanical](https://thelittlebotanical.com/how-to-care-for-the-chinese-money-plant/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pilea peperomioides | `species.scientific_name` |
| Volksnamen (DE/EN) | Chinesische Geldpflanze, Bauchnabelpflanze; Chinese Money Plant, Pancake Plant, UFO Plant | `species.common_names` |
| Familie | Urticaceae | `species.family` → `botanical_families.name` |
| Gattung | Pilea | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 13–30°C. Sehr anpassungsfähig an normale Zimmertemperaturen. | `species.hardiness_detail` |
| Heimat | Südchina (Yunnan-Provinz) — feuchte Bergwälder auf 1500–3000 m ü.M. | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Pilea peperomioides erlangte ihre Popularität durch Weitergabe von Stecklingen unter Pflanzenenthusiasten — ursprünglich verbreitete ein norddeutscher Missionar die Pflanze in Europa in den 1970ern. Die charakteristischen runden, tellerförmigen Blätter an langen Stielen sind unverwechselbar. Die Pflanze dreht sich zum Licht — regelmäßiges Drehen verhindert einseitiges Wachstum.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (kleine, unauffällige Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) entstehen spontan an der Basis oder am Stängel — bei 5–7 cm ablösen (mit scharfem Messer), kurz trocknen lassen, in Wasser oder feuchtem Substrat bewurzeln. Sehr einfach und zuverlässig.

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

**Hinweis:** Pilea peperomioides ist nicht giftig — ideal für Haushalte mit Kindern und Haustieren.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt nötig. Ableger bei Bedarf entfernen, damit Mutterpflanze nicht zu dicht wird.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–50 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, gut durchlässige Einheitserde mit 20% Perlite. pH 6.0–7.0. Kokosfaser-basierte Mischungen funktionieren gut. Kleiner Topf bevorzugt — mag nicht zu viel Erdvolumen. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–250 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 13–22 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 4 ml/L | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen März bis September. Kein Dünger Oktober bis Februar. Überdüngung → kahle Stiele (sog. "leggy"), kleine Blätter. Helles Licht ist wichtiger als Dünger für große, gesunde Blätter.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; abgestandenes Wasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Düngung starten | Erste Düngergabe nach dem Winter | mittel |
| Apr–Sep | Regelmäßig drehen | Topf jede Woche um 90° drehen für gleichmäßiges Wachstum | mittel |
| Apr–Sep | Ableger entnehmen | Kindpflanzen ab 5 cm Höhe ablösen | optional |
| Sep | Düngung beenden | — | niedrig |
| Okt–Feb | Reduzieres Gießen | Substrat zwischen Güssen mehr antrocknen lassen | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Trauermücke | Bradysia spp. | Larven in Substrat, Adulte fliegend | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, gelbe Punkte (bei trockener Luft) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Überbewässerung |
| Blattflecken | fungal/bacterial | Braun-gelbe Flecken | Nasses Laub, schlechte Zirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke |
| Nematoden | biological | Gießen | 0 | Trauermücke (Larven) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Pilea cadierei | Pilea cadierei | Gleiche Gattung | Silbermuster auf Blättern |
| Pilea mollis | Pilea mollis | Gleiche Gattung | Samtartige Textur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Pilea peperomioides,"Chinesische Geldpflanze;Bauchnabelpflanze;Chinese Money Plant;UFO Plant",Urticaceae,Pilea,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Südchina (Yunnan-Provinz)",yes,1-5,12,20-50,20-50,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [BBC Gardeners World — Chinese Money Plant](https://www.gardenersworld.com/house-plants/how-to-grow-pilea-peperomioides/) — Pflegehinweise
2. [Savvy Gardening](https://savvygardening.com/pilea-peperomioides-care/) — Kulturdaten
3. [PLNTS.com — Pilea Care](https://plnts.com/en/care/houseplants-family/pilea) — Ganzjahrespflege
4. [The Little Botanical](https://thelittlebotanical.com/how-to-care-for-the-chinese-money-plant/) — Praxiswissen
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
