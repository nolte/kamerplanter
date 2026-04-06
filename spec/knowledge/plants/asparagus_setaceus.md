# Federspargel (Plumosafarn) — Asparagus setaceus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Asparagus setaceus](https://www.gardenia.net/plant/asparagus-setaceus-asparagus-fern-grow-care-tips), [NC State Extension – Asparagus setaceus](https://plants.ces.ncsu.edu/plants/asparagus-setaceus/), [Leafyplace – Plumosa Fern](https://leafyplace.com/asparagus-plumosa-fern/), [Plantura – Zierspargel](https://www.plantura.garden/zimmerpflanzen/zierspargel/zierspargel-pflanzenportait)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Asparagus setaceus | `species.scientific_name` |
| Volksnamen (DE/EN) | Federspargel, Zierspargel, Plumosa-Farn; Asparagus Fern, Lace Fern, Plumosa Fern | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Asparagus | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Leichten Frost (bis -3°C) kurz tolerierend; Wurzeln frostempfindlich | `species.hardiness_detail` |
| Heimat | Südafrika (Ost-Kap, KwaZulu-Natal) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis:** Trotz des Namens "Farn" ist Asparagus setaceus kein echter Farn, sondern ein Verwandter des Speisespargels (Asparagus officinalis). Die federartigen Blätter sind reduzierte Phyllokladien (umgewandelte Stängel).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (kleine weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Beeren (rot, wenn reif) — führen zu Erbrechen, Durchfall | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Saponine, Asparagin | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 (kletternd bis 300 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut drainierte Zimmerpflanzenerde; leicht sauer (pH 6.0–6.5); hohe Luftfeuchtigkeit wichtig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 21–42 | 1 | false | false | low |
| Vegetativ (Wachstum) | 180–270 | 2 | false | false | medium |
| Blüte | 30–60 | 3 | false | false | medium |
| Winterruhe | 90–120 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 1:1:1 | 0.5–0.8 | 6.0–6.5 | 80 | 40 | — | 1 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 |
| Blüte | 1:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | — | 1 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 21–42 Tage | Neue Triebe |
| Vegetativ → Blüte | time_based | 180–270 Tage | Kleine Blüten erscheinen |
| Blüte → Winterruhe | time_based | 30–60 Tage | Herbst, Temperatursenkung |
| Winterruhe → Vegetativ | time_based | 90–120 Tage | Frühjahrsaustrieb |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Zimmerpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ, blüte |
| Balanced Fertilizer | Miracle-Gro | base | 10-10-10 | halbe Dosis | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Pflanzenerde mit Guano | Plagron | organisch | Beimischen 20% | Frühjahr | medium_feeder |
| Wormcast-Dünger | — | organisch | 1 TL/Topf | Apr–Sep | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| 1–3 | Etablierung | 0.5–0.8 | 6.2 | Hälfte der Normaldosis |
| 4–26 | Vegetativ | 1.0–1.5 | 6.2 | Alle 2–4 Wochen |
| 27–34 | Blüte | 0.8–1.2 | 6.2 | Normale Düngung |
| Nov–Feb | Winterruhe | 0.0 | — | Kein Dünger |

### 3.3 Besondere Hinweise zur Düngung

Hohe Luftfeuchtigkeit ist für Asparagus setaceus wichtiger als Düngung. Trockene Raumluft (unter 40%) führt zu gelbem Nadeln (Phyllokladien)-Abfall — das häufigste Problem. Regelmäßiges Besprühen oder ein Luftbefeuchter sind die wichtigste Maßnahme.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt; regelmäßig besprühen für Luftfeuchtigkeit | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Kühler Standort, wenig gießen | niedrig |
| Mär | Umtopfen | Rhizome teilen, frisches Substrat | hoch |
| Apr | Düngung | Wachstum beginnt, erste Düngung | hoch |
| Mai–Sep | Wachstum | Regelmäßig gießen, besprühen, düngen | hoch |
| Okt | Einwintern | Gießen reduzieren, kühleren Standort suchen | mittel |
| Nov–Dez | Ruhephase | Minimal gießen, kein Dünger | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Gelbe Nadeln, feine Gespinste | leaf | alle | medium |
| Blattläuse | Aphis spp. | Junge Triebe verformt | stem | vegetative | easy |
| Trauermücken | Sciara spp. | Larven im feuchten Substrat | root | alle | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Gelbe Nadeln, schlaffe Pflanze | overwatering | 7–14 | alle |
| Nadelfall | physiological | Massenhafter Abfall grüner Nadeln | dry_air, drought | — | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Steinernema feltiae | Trauermückenlarven | 0.5 Mio./m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Besprühen | cultural | Wasser | Täglich besprühen | 0 | Spinnmilben, Nadelfall |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Spinnmilben, Blattläuse |
| Gelbes Klebeband | mechanical | — | Aufhängen | 0 | Trauermücken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Farne | Nephrolepis exaltata | 0.8 | Ähnliche Licht- und Feuchte-Anforderungen | `compatible_with` |
| Tradescantia | Tradescantia zebrina | 0.7 | Ähnliche Feuchte-Toleranz | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Asparagus setaceus |
|-----|-------------------|-------------|------------------------------|
| Sprengerspargel | Asparagus densiflorus 'Sprengeri' | Gleiche Gattung | Robuster, weniger Luftfeuchte nötig |
| Sichelfarn | Asparagus falcatus | Gleiche Gattung | Größere Blätter, anspruchsloser |
| Nephrolepis | Nephrolepis exaltata | Echter Farn | Echter Farn, mehr Volumen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Asparagus setaceus,Federspargel;Plumosa-Farn;Asparagus Fern,Asparagaceae,Asparagus,perennial,day_neutral,vine,rhizomatous,9a;9b;10a;10b;11a;11b,0.0,Südafrika Ostkap,yes,7,15,60,60,—,yes,limited,false,true
```

---

## Quellenverzeichnis

1. [Gardenia.net – Asparagus setaceus](https://www.gardenia.net/plant/asparagus-setaceus-asparagus-fern-grow-care-tips) — Vollständige Pflegeanleitung
2. [NC State Extension – Asparagus setaceus](https://plants.ces.ncsu.edu/plants/asparagus-setaceus/) — Wissenschaftliche Grundlagen
3. [Leafyplace – Plumosa Fern](https://leafyplace.com/asparagus-plumosa-fern/) — Detaillierter Care Guide
4. [Plantura – Zierspargel](https://www.plantura.garden/zimmerpflanzen/zierspargel/zierspargel-pflanzenportait) — Deutschsprachige Pflege
5. [Pflanzenfreunde – Asparagus](https://www.pflanzenfreunde.com/asparagus-zierspargel.htm) — Kulturtipps
