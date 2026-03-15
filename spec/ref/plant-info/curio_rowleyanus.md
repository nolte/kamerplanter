# Perlenschnur — Curio rowleyanus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Plantura – Erbsenpflanze](https://www.plantura.garden/zimmerpflanzen/erbsenpflanze/erbsenpflanze-pflanzenportrait), [PLNTS.com – Senecio](https://plnts.com/de/care/houseplants-family/senecio), [Feey – Erbsenpflanze](https://www.feey-pflanzen.de/pages/erbsenpflanze), [Pflanzenfreunde](https://www.pflanzenfreunde.com/lexika/sukkulenten/senecio-rowleyanus.htm)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Curio rowleyanus | `species.scientific_name` |
| Volksnamen (DE/EN) | Perlenschnur, Erbsenpflanze; String of Pearls, Rosary Plant | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Curio | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9b–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostfrei halten, keine Temperaturen unter 5°C | `species.hardiness_detail` |
| Heimat | Südafrika (Namaqualand, Kapprovinz) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis:** Ältere Literatur verwendet noch den Synonym Senecio rowleyanus. Aktuell gültige Bezeichnung (APG IV): Curio rowleyanus.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 12, 1, 2 (Winterblüher) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Pyrrolizidinalkaloide | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–10 (Hängelänge bis 90 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde oder Zimmerpflanzenerde + 50% Perlite; hervorragende Drainage; flache Schale besser als tiefer Topf | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 21–42 | 1 | false | false | low |
| Vegetativ (Wachstum) | 150–240 | 2 | false | false | medium |
| Blüte | 30–60 | 3 | false | false | medium |
| Sommerruhe | 60–90 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sommerruhe (Sommer-Trockenperiode)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–1.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–35 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Vegetativ | 2:1:3 | 0.5–0.8 | 6.0–6.5 | 60 | 30 | — | 1 |
| Blüte | 1:2:2 | 0.6–1.0 | 6.0–6.5 | 60 | 30 | — | 1 |
| Sommerruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 21–42 Tage | Neue Triebe gebildet |
| Vegetativ → Blüte | time_based | 150–240 Tage | Winterblüher — kurze Tage im Herbst |
| Blüte → Sommerruhe | time_based | 30–60 Tage | Sommer, Hitze |
| Sommerruhe → Vegetativ | time_based | 60–90 Tage | Herbst, kühlere Temperaturen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Cactus Focus | Growth Technology | base | 3-1-5 | 1 ml/L | 1 | vegetativ, blüte |
| Succulent Fertilizer | Miracle-Gro | base | 2-2-3 | halbe Dosierung | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kakteendünger Stäbchen | Substral | organisch/langsam | 1 Stäbchen/Topf | Apr–Sep | light_feeder |
| Algendünger (flüssig) | Hesi | organisch | 0.5 ml/L | Mai–Aug | light_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–6 | Etablierung | 0.0 | — | — | Kein Dünger |
| 7–24 | Vegetativ | 0.5–0.8 | 6.2 | 1.0 | Alle 4–6 Wochen |
| Okt–Feb | Blüte | 0.6–1.0 | 6.2 | 0.5 | Sehr sparsam |
| Jun–Aug | Sommerruhe | 0.0 | — | — | Kein Dünger |

### 3.3 Mischungsreihenfolge

1. Wasser
2. Flüssigdünger (stark verdünnt, max. halbe Herstellerempfehlung)

### 3.4 Besondere Hinweise zur Düngung

Die Perlenschnur kommt aus einer nährstoffarmen Heimat (Namaqualand) — sie ist ein ausgesprochener Schwachzehrer. Wurzelfäule durch Überwässerung und Überdüngung ist der häufigste Todesgrund. Im Sommer halbiert sich die Aktivität (natürliche Ruhephase) — kein Dünger von Juni bis August.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes, kalkarmes Wasser bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–5, 9–11 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Blütezeit genießen | Minimales Gießen, kühler Standort fördert Blüte | niedrig |
| Feb | Leicht mehr gießen | Blüte verblüht, Vorbereitung Wachstum | niedrig |
| Mär | Umtopfen | Bei Bedarf, Substrat erneuern | mittel |
| Apr | Düngung beginnen | Erste Düngung mit sehr verdünntem Sukkulentendünger | mittel |
| Mai–Jun | Wachstumsphase | Regelmäßig gießen, Substrate vollständig austrocknen lassen | hoch |
| Jul–Aug | Sommerruhe | Stark reduziertes Gießen, kein Dünger, Halbschatten | hoch |
| Sep | Gießen wieder erhöhen | Herbstwachstum beginnt | mittel |
| Okt | Stecklinge | Beste Zeit für Stecklingsvermehrung | niedrig |
| Nov | Gießen reduzieren | Blütevorbereitung durch Kälte und Trockenheit | mittel |
| Dez | Blüteknospen beobachten | Wenig gießen, cool und hell halten | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Wollläuse | Pseudococcus spp. | Weiße Wollklumpen in Blattachseln | stem, leaf | alle | medium |
| Blattläuse | Aphis spp. | Junge Triebe deformiert, Honigtau | stem | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Perlen werden faltig, Triebe welken | overwatering | 7–21 | alle |
| Bodenpilz | fungal | Weißes Geflecht auf Substratoberfläche | overwatering, poor_drainage | 7–14 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wollläuse | 1–2 Käfer/Pflanze | 14–21 |
| Aphidius colemani | Blattläuse | 5–10 | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 0 | Wollläuse, Blattläuse |
| Alkohol (70%) | mechanical | Isopropanol | Wattestäbchen auf Schädlinge | 0 | Wollläuse |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Generell schädlingsresistent bei trockenen Bedingungen | — | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Ceropegia woodii | Ceropegia woodii | 0.8 | Gleiche Pflegebedürfnisse | `compatible_with` |
| Kakteen | Mammillaria spp. | 0.7 | Gleiche Substratanforderungen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Farne | Nephrolepis exaltata | Feuchtigkeitsbedarf viel zu unterschiedlich | severe | `incompatible_with` |
| Calathea | Goeppertia makoyana | Feuchtigkeitsbedarf zu unterschiedlich | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Curio rowleyanus |
|-----|-------------------|-------------|------------------------------|
| Perlenkette (Bananenform) | Curio herreianus | Gleiche Gattung | Ovale Perlen, robuster |
| Leuchterblume | Ceropegia woodii | Hängepflanze, sukkulent | Herzförmige Blätter, eleganter |
| Fischschwanzpflanze | Curio radicans | Gleiche Gattung | Cylindrische Blätter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Curio rowleyanus,Perlenschnur;Erbsenpflanze;String of Pearls,Asteraceae,Curio,perennial,day_neutral,vine,fibrous,9b;10a;10b;11a;11b;12a;12b,0.0,Südafrika Namaqualand,yes,2,8,10,90,—,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Plantura – Erbsenpflanze Portrait](https://www.plantura.garden/zimmerpflanzen/erbsenpflanze/erbsenpflanze-pflanzenportrait) — Botanik, Toxizität, Pflege
2. [PLNTS.com – Senecio Pflege](https://plnts.com/de/care/houseplants-family/senecio) — Pflegeprofile
3. [Feey – Erbsenpflanze](https://www.feey-pflanzen.de/pages/erbsenpflanze) — Steckbrief
4. [Pflanzenfreunde – Senecio rowleyanus](https://www.pflanzenfreunde.com/lexika/sukkulenten/senecio-rowleyanus.htm) — Kulturtipps
5. [PictureThis – Senecio rowleyanus](https://www.picturethisai.com/de/wiki/Senecio_rowleyanus.html) — Taxonomie
