# Kap-Primel (Drehfrucht) — Streptocarpus hybridus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [UK Houseplants – Streptocarpus](https://www.ukhouseplants.com/plants/streptocarpus), [RHS – Streptocarpus](https://www.rhs.org.uk/plants/streptocarpus/growing-guide), [Gardening Know How – Streptocarpus](https://www.gardeningknowhow.com/houseplants/streptocarpus-plants/care-for-streptocarpus.htm), [Global Flowers – Streptocarpus](https://global.flowers/en/plants/streptocarpus/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Streptocarpus hybridus | `species.scientific_name` |
| Volksnamen (DE/EN) | Kap-Primel, Drehfrucht; Cape Primrose, Twisted Fruit | `species.common_names` |
| Familie | Gesneriaceae | `species.family` → `botanical_families.name` |
| Gattung | Streptocarpus | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Ausschließlich Zimmerpflanze; keine Temperaturen unter 10°C | `species.hardiness_detail` |
| Heimat | Südafrika, Tansania, Madagaskar | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 3, 4, 5, 6, 7, 8, 9, 10 (Langtagspflanze, fast ganzjährig blühend) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_leaf, seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (ältere Blätter entfernen, Ordnung schaffen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, durchlässige Erde für Afrikanische Veilchen oder Spezialsubstrat; pH 5.5–6.5; flache Töpfe bevorzugen (flaches Wurzelsystem) | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 21–42 | 1 | false | false | low |
| Vegetativ/Blüte | 180–270 | 2 | false | false | medium |
| Winterruhe | 60–90 | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ/Blüte (Hauptwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag für Blüte) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.1 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 1:1:1 | 0.4–0.6 | 5.5–6.5 | 60 | 30 | — | 1 |
| Vegetativ/Blüte | 1:2:1 | 0.8–1.2 | 5.5–6.5 | 80 | 40 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ/Blüte | time_based | 21–42 Tage | Neue Blätter, erste Knospen |
| Vegetativ/Blüte → Winterruhe | time_based | 180–270 Tage | Herbst, kurze Tage |
| Winterruhe → Vegetativ/Blüte | time_based | 60–90 Tage | Frühjahr, längere Tage |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Afrikanisches Veilchen-Dünger | Schultz | base | 8-14-9 | halbe Dosis | 1 | vegetativ/blüte |
| Zimmerpflanzendünger | Compo | base | 7-4-7 | halbe Dosis | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Biohumus (Wurmkompost) | — | organisch | 10% Beimischung | Frühjahr | light_feeder |
| Langzeitdünger | Osmocote | organisch/langsam | 2 g/L Substrat | Apr–Jun | light_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| 1–4 | Etablierung | 0.4–0.6 | 6.0 | Schwach, halbe Dosis |
| 5–36 | Vegetativ/Blüte | 0.8–1.2 | 6.0 | Alle 4 Wochen, phosphorlastig |
| Nov–Jan | Winterruhe | 0.0 | — | Kein Dünger |

### 3.3 Besondere Hinweise zur Düngung

Streptocarpus ist ein Schwachzehrer (light_feeder) — Überdüngung verbrennt die Blätter. Gießwasser sollte von unten oder am Blattrand gegeben werden — Wasser auf den Blättern und im Blattzentrum führt zu Fäulnis (wie bei Afrikanischen Veilchen). Weiches Wasser bevorzugt (kalkempfindlich).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser; nie auf die Blätter gießen! Unterbewässerung bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Kühl (12–15°C), wenig gießen, nicht düngen | niedrig |
| Mär | Umtopfen | Frisches Substrat, Teilung möglich | hoch |
| Apr | Düngung | Erste Gabe, hellen Platz sichern | hoch |
| Mai–Sep | Hauptblüte | Regelmäßig gießen (von unten!), Verblühtes entfernen | hoch |
| Sep–Okt | Herbstblüte | Noch Blüten möglich, Gießen reduzieren | mittel |
| Okt | Blattpflege | Ältere Blätter entfernen | niedrig |
| Nov–Dez | Winterruhe | Kühl stellen, wenig Wasser | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Deformierte Knospen, Honigtau | stem | alle | easy |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem | alle | medium |
| Tarsonemidmilben | Phytonemus pallidus | Verkrüppelte Blätter, verzerrte Triebe | leaf, stem | alle | difficult |
| Trauermücken | Sciara spp. | Larven im Substrat | root | alle | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Botrytis (Grauschimmel) | fungal | Grauer Belag auf Blüten/Blättern | high_humidity, poor_airflow | 3–7 | alle |
| Echter Mehltau | fungal | Weißer Belag | dry_leaves, poor_airflow | 5–10 | alle |
| Wurzelfäule | fungal | Welke Pflanze | overwatering | 7–14 | alle |
| Blattfäule | fungal | Braune, weiche Blattzentren | water_on_leaves | 3–7 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Amblyseius cucumeris | Tarsonemidmilben | 50–100 | 14 |
| Aphidius colemani | Blattläuse | 5–10 | 7–14 |
| Steinernema feltiae | Trauermückenlarven | 0.5 Mio./m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% (Blattunterseiten) | 0 | Blattläuse, Wollläuse |
| Luftzirkulation | cultural | — | Ventilator, weniger Pflanzendichte | 0 | Botrytis, Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Afrikanisches Veilchen | Streptocarpus ionanthus | 0.8 | Gleiche Familie, gleiche Pflege | `compatible_with` |
| Fittonia | Fittonia albivenis | 0.7 | Ähnliche Lichtbedürfnisse | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Streptocarpus hybridus |
|-----|-------------------|-------------|------------------------------|
| Afrikanisches Veilchen | Streptocarpus ionanthus | Gleiche Familie, ähnliche Pflege | Kompakter, stärker bekannte Zimmerpflanze |
| Episcia | Episcia cupreata | Gleiche Familie | Schöne Blattzeichnung, kriechend |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Streptocarpus hybridus,Kap-Primel;Drehfrucht;Cape Primrose,Gesneriaceae,Streptocarpus,perennial,long_day,herb,fibrous,10a;10b;11a;11b,0.0,Südafrika Tansania,yes,2,10,30,40,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [UK Houseplants – Streptocarpus](https://www.ukhouseplants.com/plants/streptocarpus) — Detailed Care Guide
2. [RHS – Streptocarpus Growing Guide](https://www.rhs.org.uk/plants/streptocarpus/growing-guide) — Royal Horticultural Society
3. [Gardening Know How – Streptocarpus](https://www.gardeningknowhow.com/houseplants/streptocarpus-plants/care-for-streptocarpus.htm) — Indoor Care
4. [Global Flowers – Streptocarpus](https://global.flowers/en/plants/streptocarpus/) — Botanik, Kulturtipps
5. [University of Vermont – Plant Profile Streptocarpus](https://www.uvm.edu/extension/news/plant-profile-streptocarpus) — Extension Service
