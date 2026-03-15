# Hasenohren-Kaktus, Bunny Ears — Opuntia microdasys

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/opuntia-microdasys-bunny-ears), [NC State Extension](https://plants.ces.ncsu.edu/plants/opuntia-microdasys/), [Epic Gardening](https://www.epicgardening.com/opuntia-microdasys/), [Plant Care Today](https://plantcaretoday.com/opuntia-microdasys.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Opuntia microdasys | `species.scientific_name` |
| Synonyme | Opuntia microdasys var. albispina (weißhöckrige Variante) | — |
| Volksnamen (DE/EN) | Hasenohren-Kaktus, Bunny Ears, Polka-Dot-Kaktus; Bunny Ears Cactus, Angel Wings, Polka Dot Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Opuntia | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 15–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht für Mitteleuropäische Freiland. Im Topf bei 7–13°C überwintern — kühle Winterruhe für optimale Gesundheit. | `species.hardiness_detail` |
| Heimat | Nordmexiko — trockene Hochplateaus, Chihuahua-Wüste | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Hasenohren-Kaktus ist einer der beliebtesten Feigenkakteen für die Zimmerpflanzenpflege. Die runden, abgeflachten Kaktuspaddes haben statt langer Stacheln kleine Büschel aus winzigen Widerhaken (Glochiden). ACHTUNG: Diese Glochiden sind besonders tückisch — sie sind mikroskopisch klein, brechen leicht ab und verursachen extremen Juckreiz in Haut und Augen. Die Pflanze IMMER mit Handschuhen anfassen. Im Sommer können gelbe Blüten erscheinen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (gelbe Blüten bei älteren Pflanzen und genügend Sonne) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, offset | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Kaktuspadde mit Pinzette (niemals mit bloßen Händen!) abbrechen, 1–2 Wochen trocknen lassen (Wundverschluss), dann in Kakteenerde stecken. Bewurzelung in 3–6 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Glochiden = winzige Widerhaken verursachen extremen Juckreiz/Verletzungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Sicherheitshinweis:** GLOCHIDEN SIND GEFÄHRLICH — die winzigen Widerhaken können sich in Haut, Augen und Schleimhäute bohren und sind sehr schwer zu entfernen. Immer mit dicken Lederhandschuhen anfassen. Kinder und Haustiere fernhalten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde oder Einheitserde + 50% Sand/Perlite. pH 6.0–7.5. Sehr gute Drainage essentiell. Terrakotta-Töpfe bevorzugt (bessere Feuchtigkeitsregulation). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum/Blüte (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 10–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–3.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 7–13 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 42–60 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:7:7 | 0.4–0.8 | 6.0–7.5 | 50 | 20 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen-Flüssigdünger | Compo | base | 5-3-8 | 3 ml/L (monatlich) | Wachstum |
| Sukkulenten-Dünger | Substral | base | 3-8-10 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kakteenerde mit Mineralanteil | Fertigsubstrat | organisch-mineralisch | 100% | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis August. September bis März kein Dünger. Kakteendünger mit erhöhtem Kalium- und Phosphatanteil bevorzugen — stickstoffreiche Dünger führen zu weichem, schlaff wirkendem Wuchs.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat VOLLSTÄNDIG austrocknen zwischen Güssen; im Winter fast kein Wasser (alle 6–8 Wochen) — Überwässerung ist häufigste Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 7 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Pseudococcus spp. | Weiße Wollflocken | easy |
| Schildlaus | Coccus spp. | Braune Schilder am Padde | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzel-/Stängelfäule | fungal | Braune weiche Stellen | Staunässe |
| Sonnenbrand | physiologisch | Braune Verfärbungen | Direktes Sonnenlicht nach Dunkelphase |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Alkohol 70% | mechanical | Wattestäbchen mit Pinzette | 0 | Schildläuse, Wollläuse |
| Weniger gießen | cultural | Substrat komplett austrocknen | 0 | Fäule (Prävention) |
| Langsame Eingewöhnung | cultural | Schritt für Schritt an Sonne gewöhnen | 0 | Sonnenbrand |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze/Kübelpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Feigenkaktus | Opuntia ficus-indica | Gleiche Gattung | Größer, essbare Früchte |
| Gymnocalycium | Gymnocalycium mihanovichii | Cactaceae, Zimmerkaktus | Stachellos, kompakt |
| Echinopsis | Echinopsis oxygona | Cactaceae | Schöne große Blüten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Opuntia microdasys,"Hasenohren-Kaktus;Bunny Ears;Polka-Dot-Kaktus;Bunny Ears Cactus;Angel Wings",Cactaceae,Opuntia,perennial,day_neutral,shrub,fibrous,"9a;9b;10a;10b;11a;11b","Nordmexiko (Chihuahua-Wüste)",yes,3-15,15,40-90,60-150,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Opuntia microdasys](https://www.gardenia.net/plant/opuntia-microdasys-bunny-ears) — Botanische Daten
2. [NC State Extension — Opuntia microdasys](https://plants.ces.ncsu.edu/plants/opuntia-microdasys/) — Kulturdaten
3. [Epic Gardening — Opuntia microdasys](https://www.epicgardening.com/opuntia-microdasys/) — Pflegehinweise
4. [Plant Care Today — Opuntia microdasys](https://plantcaretoday.com/opuntia-microdasys.html) — Schädlinge, Glochiden-Warnung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig — Glochiden mechanisch gefährlich)
