# Kissenkaktus, Warzenkaktus — Mammillaria spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/mammillaria/), [Gardenia.net](https://www.gardenia.net/genus/mammillaria), [World of Succulents](https://worldofsucculents.com/grow-care-mammillaria/), [Plant Care Today](https://plantcaretoday.com/mammillaria-cactus.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Mammillaria spp. (Gattung, ~147 Arten) | `species.scientific_name` |
| Volksnamen (DE/EN) | Kissenkaktus, Warzenkaktus, Nippelkaktus; Pincushion Cactus, Nipple Cactus, Fishhook Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Mammillaria | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Winterdormanz für Blüteninduktion) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Artabhängig — viele Arten tolerieren kurze Fröste bis -5°C (trocken). Mindesttemperatur 5°C empfohlen. Winterdormanz bei 7–13°C fördert Blüte. | `species.hardiness_detail` |
| Heimat | Mexiko, südwestliche USA — Wüsten und Halbwüsten | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Mammillaria ist eine der artenreichsten Kakteengattungen (147 akzeptierte Arten). Charakteristisch: spiralförmig angeordnete Warzen (Tuberkel) anstelle der sonst üblichen Rippen. Die kleinen, ringförmig angeordneten Blüten erscheinen an der Warzenbasis. Sehr beliebt für Einsteiger und Kakteensammlungen. Häufig angebotene Arten: M. hahniana ("Alte Dame"), M. elongata ("Fingerkaktus"), M. prolifera ("Traubenform"). Schlüssel für Blüte: kühle, trockene Winterruhe.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 2, 3, 4, 5 (nach kühler Winterruhe — oft ringförmige Blüten in Weiß/Rosa/Rot) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) im Frühjahr/Sommer abtrennen, 1–2 Tage Schnittstelle trocknen lassen, in trockenes Kakteensubstrat pflanzen. Samen bei 22–28°C, Keimung in 1–3 Wochen.

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

**Hinweis:** Nicht giftig — aber mechanische Verletzungsgefahr durch Stacheln! Stacheln können sich in Haut einbohren. Gartenhandschuhe beim Umtopfen verwenden.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.3–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–30 (artabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 3–20 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, trocken, frostfreie Monate oder frosttolerant je Art) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde mit 50–70% mineralischem Material (Perlite, grober Sand, Bimssplit). pH 6.0–7.0. Hervorragende Drainage zwingend. Flache Tontöpfe bevorzugt. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterdormanz | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–2000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–55 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 10–30 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–3.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterdormanz (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 7–13 (kühle Winterruhe) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–10 | `requirement_profiles.temperature_night_c` |
| Gießintervall (Tage) | 42–90 (fast trocken) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0–20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.0–7.0 | 30 | 10 |
| Winterdormanz | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (alle 4–6 Wochen) | Wachstum |
| Kakteendünger | Substral | base | 3-6-7 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 5% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Alle 4–6 Wochen April bis September, halbe Empfehlungsdosis. Oktober bis März: kein Dünger. Überdüngung fördert "Weichheit" und verringert Stacheln-Qualität.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 (extrem wenig im Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; vollständig durchgießen, dann KOMPLETT abtrocknen; im Winter fast komplett trocken | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors (helles, kühles Zimmer) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken an Stacheln und Warzen | easy |
| Spinnmilbe | Tetranychus urticae | Braune Punkte, Gespinste (selten) | difficult |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal/bacterial | Weicher, brauner Stammsockel | Überwässerung, bes. im Winter |
| Schorf | fungal | Braune Flecken auf Körper | Hohe Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Gießintervall verlängern | 0 | Wurzelfäule (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen (vorsichtig wegen Stacheln) | 0 Tage | Schmierlaus, Schildlaus |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze/Balkonpflanze (Sukkulenten-Arrangement).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Echinopsis | Echinopsis spp. | Cactaceae, Kugelkaktus | Größere, spektakuläre Blüten |
| Gymnocalycium | Gymnocalycium spp. | Cactaceae, Kugelkaktus | Toleriert Halbschatten |
| Feigenkaktus | Opuntia spp. | Cactaceae | Rustikaler, flache Glieder |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Mammillaria spp.,"Kissenkaktus;Warzenkaktus;Nippelkaktus;Pincushion Cactus;Nipple Cactus",Cactaceae,Mammillaria,perennial,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b","Mexiko, südwestliche USA",yes,0.3-2,8,5-30,3-20,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [NC State Extension — Mammillaria](https://plants.ces.ncsu.edu/plants/mammillaria/) — Botanische Daten, USDA-Zonen
2. [Gardenia.net — Mammillaria](https://www.gardenia.net/genus/mammillaria) — Gattungsübersicht
3. [World of Succulents — Mammillaria](https://worldofsucculents.com/grow-care-mammillaria/) — Kulturdaten
4. [Plant Care Today — Mammillaria](https://plantcaretoday.com/mammillaria-cactus.html) — Schädlinge, Pflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
