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
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN — kein belegter Wuchs-/Phänologie-GDD-Basiswert für Streptocarpus auffindbar; nur Kulturtemperatur-Optima (12–21 °C aktiv, Schaden > 24 °C) verfügbar, die nicht als GDD-Basis umetikettiert werden dürfen --> | `species.base_temp` |
| Lebensdauer (Jahre, perennial) | <!-- DATEN FEHLEN — Quellen nennen nur „evergreen perennial / many years“ ohne belegte Jahreszahl; Verjüngung durch Teilung üblich --> | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | — (tropisch/subtropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN — Hobbyquelle nennt ~13 h als Blühtrigger, aber nur einfach belegt und professionelle Quellen berichten ganzjährige Blüte; kein doppelt-seriös belegter Stundenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 8–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN — keine Maas-Hoffman-Daten für Streptocarpus; Quellen belegen nur qualitative Salzempfindlichkeit (Spülen/Leaching nötig) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-Slope für diese Zierart --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 5.5–6.5 | `species.soil_ph_preference` |

> Hinweis: Der LCP-Bereich nennt ausschließlich den Lichtkompensationspunkt (Netto-Photosynthese = 0) und ist mit einer schattentoleranten C3-Waldbodenpflanze konsistent (typischer LCP schattenadaptierter Arten 10–25 µmol/m²/s). Lichtsättigung liegt deutlich höher und ist nicht in diesem Feld abgebildet. Streptocarpus toleriert laut NCSU „deep shade“ bis „partial shade“; gewählt wurde die Hauptklasse `shade`. Salzempfindlichkeit erfordert regelmäßiges Durchspülen (Leaching) des Substrats; Bezugsgröße der (fehlenden) Schwelle wäre Substrat-ECe, nicht Gießwasser-EC.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 14–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Etablierung | 1:1:1 | 0.4–0.6 | 5.5–6.5 | 60 | 30 | — | 1 | 0.3 | 0.03 | 0.01 | 0.01 |
| Vegetativ/Blüte | 1:2:1 | 0.8–1.2 | 5.5–6.5 | 80 | 40 | — | 2 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Mn/Zn/Cu/Mo: allgemeine Mikronährstoff-Richtwerte für eine schwachzehrende Topf-/Hydrokultur (Hoagland-abgeleitete Größenordnung), keine streptocarpus-spezifischen Messwerte verfügbar. Werte bewusst niedrig (light_feeder, salzempfindlich). -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Okt) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen — nur falls im Sommer im Freien) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 12–15 | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (keine direkte Sonne); Tageslicht oder LED | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam, oberste Substratschicht abtrocknen lassen; nie ganz austrocknen (kein Rhizom/Knolle) | `overwintering_profiles.winter_quarter_watering` |

> Hinweis: Streptocarpus ist eine ausschließlich frostfrei zu haltende Zimmerpflanze (frost_sensitivity = tender). Sie bildet keine Speicherorgane (Rhizom/Knolle) und darf daher nicht vollständig austrocknen. Eine kurze, kühle Winterruhe (≈ 12–15 °C, reduziertes Gießen/Düngen) fördert die Blühinduktion im Frühjahr; daher `dormancy_required: true`. `move_indoors`/`move_outdoors` greifen nur, wenn die Pflanze im Sommer im Freien (Halbschatten) kultiviert wurde — andernfalls ganzjährig Innenkultur.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NC State Extension – Streptocarpus Plant Toolbox](https://plants.ces.ncsu.edu/plants/streptocarpus/) — Schattentoleranz (deep shade–partial shade), pH (acid <6.0), Staunässe-/Überwässerungsempfindlichkeit (root/crown rot), Temperaturen
7. [New York Botanical Garden – African violet (Streptocarpus) Research Guide](https://libguides.nybg.org/africanviolet) — Taxonomie (Gesneriaceae), Kulturtemperatur-Optima
8. [Plantly – Streptocarpus Plant Care](https://plantly.io/plant-care/streptocarpus/) — flaches Wurzelsystem, gut durchlässiges Substrat, pH, Überwässerungsempfindlichkeit
9. [Clemson HGIC – Cape Primrose (Streptocarpus saxorum)](https://hgic.clemson.edu/cape-primrose-streptocarpus-saxorum-how-to-grow-this-easy-houseplant/) — Salzempfindlichkeit (Fertilizer-Salt-Build-up, Leaching), perennierende Kultur
10. [FEBS Letters / Wiley – Photosynthesis under far-red light (Amelii 2026)](https://febs.onlinelibrary.wiley.com/doi/10.1002/1873-3468.70191) — R:FR-Abfall im Unterwuchs (Kronendach 1.2 → Boden 0.1), FR-Anreicherung im Schatten als Grundlage der Far-Red-Fraction
11. [frillfree – Flowering Streptocarpus](https://www.frillfree.com/flowering-streptocarpus.html) — Blühverhalten, Tageslängen-/Lichtmengen-Hinweis (Hobbyquelle, nur einfach belegt)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
