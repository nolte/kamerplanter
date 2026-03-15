# Lebende Steine — Lithops spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/lithops-living-stones), [Succulents Box](https://succulentsbox.com/blogs/blog/how-to-care-for-lithops), [UK Houseplants](https://www.ukhouseplants.com/plants/lithops-living-stones), [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/living-stones-lithops/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lithops spp. (Gattung, ~145 Arten/Varietäten) | `species.scientific_name` |
| Volksnamen (DE/EN) | Lebende Steine, Steinpflanzen; Living Stones, Pebble Plants | `species.common_names` |
| Familie | Aizoaceae | `species.family` → `botanical_families.name` |
| Gattung | Lithops | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Sommer- und Winterdormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 4°C. Optimal 18–27°C im Wachstum, 10–15°C in der Winterruhe. | `species.hardiness_detail` |
| Heimat | Südafrika, Namibia — Kieswüsten, trockene Felsebenen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Lithops sind die extremsten Sukkulenten — ihre Tarnfarbe imitiert perfekt Kieselsteine in ihrer Heimat Südafrika/Namibia. Das Hauptproblem für Einsteiger ist Überwässerung: falsch gegossen führen Lithops zur Spalte auf (platzen). Der Gießkalender ist strikt jahreszeitlich — im Winter (Hüllblatt-Wechsel läuft) und im Sommer (Hochsommerdormanz) NICHT gießen. Aktive Wachstumsperioden: Frühling und Herbst. Nach der Blüte (Herbst) entwickelt sich das neue Blattpaar innerhalb des alten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 9, 10, 11 (weiße oder gelbe Gänseblümchen-ähnliche Blüten; erscheinen aus der Mittelspalte) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Samen bei 22–28°C, sehr fein, auf Substratoberfläche ohne Bedeckung. Keimung in 7–21 Tage. Teilung beim Aufteilen von Kopf-Clustern möglich (selten). Sämlinge brauchen 3–5 Jahre bis zur Blühreife.

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

**Hinweis:** Niemals eingreifen. Das alte Blattpaar (vertrocknete Hülle) niemals vor dem vollständigen Absterben entfernen — das neue Blattpaar bezieht Wasser und Nährstoffe aus der alten Hülle.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.2–1 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 (tiefe Pfahlwurzeln) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 2–5 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 2–5 pro Körper | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (kein Regen! Volle Sonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | 80% mineralisch (Quarzsand, Perlite, Bimssplit) + 20% Kakteenerde. pH 6.5–7.5. Extrem schnelldränierende Mischung. Hohes Topf (10+ cm tief) für Pfahlwurzel. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrs-Wachstum (März–Mai) | 60–90 | 1 | false | false | very high |
| Hochsommer-Dormanz (Juni–August) | 60–90 | 2 | false | false | very high |
| Herbst-Wachstum + Blüte (Sept–Nov) | 60–90 | 3 | false | false | very high |
| Winter-Hüllblattwechsel (Dez–Feb) | 60–90 | 4 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum (Frühjahr/Herbst)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–2000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–55 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 10–30 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–3.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–60 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz (Sommer + Winter-Hüllblattwechsel)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–27 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 60–90 (gar nicht gießen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Wachstum | 0:1:1 | 0.2–0.4 | 6.5–7.5 | 20 | 8 |
| Dormanz | 0:0:0 | 0.0 | 6.5–7.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 1 ml/L (1×/Saison) | Herbst-Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Frisches Substrat | — | — | Jährliches Umtopfen gibt ausreichend Nährstoffe | Frühjahr |

### 3.2 Besondere Hinweise

Extremer Schwachzehrer. Höchstens 1× pro Jahr düng im Herbst (sehr verdünnt). Frisches Substrat beim Umtopfen liefert genügend Nährstoffe. Überdüngung führt zu unkontrolliertem Wachstum und Platzen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 60–90 (Sommer = Dormanz = NICHT gießen) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.0 (Winter = Hüllblattwechsel = NICHT gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; GIESSK ALENDER strikt einhalten: nur Frühjahr (März–Mai) und Herbst (Sept–Nov) gießen; Sommer und Winter KEIN Wasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in der Mittelspalte | medium |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Pflanze kollabiert, weiche Basis | Überwässerung |
| Platzen/Splitting | physiologisch | Körper reißt auf | Zu viel Wasser während Dormanz |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Gießplan einhalten | cultural | Jahreszeitlichen Kalender strikt befolgen | 0 | Platzen, Wurzelfäule (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze. Ideal für Sukkulenten-Arrangements mit anderen Wüstenpflanzen.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Plebejum | Conophytum spp. | Aizoaceae, ähnliche Steinmimikry | Etwas robuster |
| Titanopsis | Titanopsis spp. | Aizoaceae, Steinmimikry | Beginner-freundlicher |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Lithops spp.,"Lebende Steine;Steinpflanzen;Living Stones;Pebble Plants",Aizoaceae,Lithops,perennial,day_neutral,herb,taproot,"10a;10b;11a;11b","Südafrika, Namibia (Kieswüsten)",yes,0.2-1,10,2-5,2-5,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Lithops Living Stones](https://www.gardenia.net/plant/lithops-living-stones) — Botanische Daten
2. [Succulents Box — Lithops Care](https://succulentsbox.com/blogs/blog/how-to-care-for-lithops) — Pflegehinweise, Gießkalender
3. [UK Houseplants — Lithops](https://www.ukhouseplants.com/plants/lithops-living-stones) — Kulturdaten
4. [Wisconsin Horticulture Extension — Lithops](https://hort.extension.wisc.edu/articles/living-stones-lithops/) — Wissenschaftliche Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
