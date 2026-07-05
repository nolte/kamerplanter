# Vielblättrige Lupine — Lupinus polyphyllus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Lupinus polyphyllus, Samen.de Lupinen, Winterharte-Stauden Lupinus, Gartenfreud-Gartenleid Lupinus

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lupinus polyphyllus | `species.scientific_name` |
| Volksnamen (DE/EN) | Vielblättrige Lupine, Gartenlupine; Garden Lupin, Large-leaved Lupin | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Lupinus | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4 | `species.base_temp` |
| Lebensdauer (Jahre) (lifespan) | 2–5 (kurzlebige Staude / short-lived perennial) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (Winterruhe / dormancy) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (min days) | 42–56 (6–8 Wochen Kälte/chilling für zuverlässige Blüte) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) (critical day length) | <!-- DATEN FEHLEN: Langtagpflanze (long-day) bestätigt, aber kein belegter numerischer Stunden-Schwellenwert für L. polyphyllus auffindbar --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–7b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25 bis -35°C; in Norddeutschland absolut winterhart; Staunässe im Winter ist das größte Problem (tiefe Pfahlwurzel verottet bei Nässe) | `species.hardiness_detail` |
| Heimat | Nordamerika (Pazifikküste); eingebürgert in Europa | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Aussaat direkt ins Freiland ab März/April; tiefe Pfahlwurzel — Umverpflanzen schlecht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (auch im Herbst aussäbar: September/Oktober; früher Vorsprung) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5, 9, 10 | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze/Gründüngung; Samen giftig, nicht essbar) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (zweites Jahr ab Aussaat) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Samen, Kraut (ALLE Teile) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Lupinin, Lupanin, Anagyrin (Quinolizidinalcaloide) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WICHTIGE WARNUNG:** Lupinus polyphyllus enthält giftige Alkaloide in Samen und Kraut. Bei Verdacht auf Aufnahme sofort Arzt aufsuchen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (nach Blüte; verhindert Aussaat und fördert 2. Blüte) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 (tiefe Pfahlwurzel) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (hohe Sorten können bei Wind kippen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, sandige, leicht saure Erde; pH 5,5–6,5; kalkfrei; durchlässig; KEIN Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP-Wert für L. polyphyllus aus 2 unabhängigen Quellen belegbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (wächst in lichtem Halbschatten, blüht dort aber spärlich) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) (effective root depth) | 30–50 (tiefe Pfahlwurzel / taproot, Bodenlockerung 30–51 cm empfohlen) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (Pfahlwurzel fäult bei Nässe; scharfe Drainage zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive (meidet auch schwach saline Standorte) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: qualitativ salzsensitiv belegt, aber kein quantitativer Maas-Hoffman-Schwellenwert (Substrat-ECe) für L. polyphyllus auffindbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) (soil pH preference) | 5.5–6.5 (Kalkflieher/calcifuge; harmonisiert mit §1.6/§2.3) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 12 (12–18°C / 55–65°F optimales Bodentemperaturfenster) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 18 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1 (flach, 0,3–1 cm je nach Quelle; nicht tiefer als 1 cm) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 8 (7,9 Tage bis zur ersten Keimung unter Laborbedingungen nach Vorbehandlung; unbehandelt 14–60 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 20 (harte, wasserundurchlässige Samenschale ermöglicht extreme Langlebigkeit; dokumentiert 75 % Keimfähigkeit nach 49 Jahren Raumtemperatur-Lagerung — Harrington 1972) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | indifferent (Aussaat flach bedeckt bei 1 cm Tiefe wird durchgängig empfohlen und funktioniert zuverlässig; kein Hinweis auf obligate Lichtkeimung) | `species.seed_profile.light_germination` |
| Vorbehandlung | scarification, cold_stratification (harte Samenschale — Heißwasser-/mechanische Skarifikation plus kalte Stratifikation deutlich keimfördernd) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: kein art-spezifischer TKG-Wert für Lupinus polyphyllus aus zwei unabhängigen Quellen; nur Werte verwandter Arten (z.B. L. perennis ≈ 21,7 g) verfügbar, nicht direkt übertragbar --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Zierstaude/Einzelpflanzung im Garten (§1.6: 40–60 cm Pflanzabstand), keine Flächen-/Reihensaat mit belegter Kornzahl je m² --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
1. [Almanac / West Coast Seeds — How to Grow Lupins](https://www.westcoastseeds.com/blogs/wcs-academy/grow-lupin) — Bodentemperatur 55–65°F (12–18°C), Saattiefe flach
2. [Johnny's Selected Seeds — Lupine Key Growing Information](https://www.johnnyseeds.com/growers-library/flowers/lupine/lupine-key-growing-information.html) — Saattiefe ~1 cm, Keimdauer 7–21 Tage
3. [Biology Insights — How to Scarify Lupine Seeds for Better Germination](https://biologyinsights.com/how-to-scarify-lupine-seeds-for-better-germination/) — Heißwasser-Skarifikation, anschließendes 12–24 h Einweichen
4. [Wellfield Gardens — Stratification and Scarification: A Seed's Path to Germination](https://www.wellfieldgardens.org/post/stratification-and-scarification-a-seed-s-path-to-germination) — Lupine als Beispielart für kombinierte Skarifikation + kalte Stratifikation
5. [ISTA/Propagation Protocol via NRCS — Lupinus sericeus](https://www.nrcs.usda.gov/plantmaterials/wapmcmt7129.pdf) — Keimtemperatur/Vorbehandlungs-Analogie innerhalb der Gattung Lupinus (cross-check)
6. [MDPI Diversity 13(6):264 — Risk of Invasive Lupinus polyphyllus Seed Survival in Biomass Treatment Processes](https://www.mdpi.com/1424-2818/13/6/264) — Harrington (1972): 75 % Keimfähigkeit nach 49 Jahren Raumtemperatur-Lagerung; kurzfristige Bodensamenbank-Persistenz vs. jahrzehntelange Laborlagerung
7. [Biological Flora of Central Europe – Lupinus polyphyllus Lindley (ScienceDirect, bereits in §Quellenverzeichnis zitiert)](https://www.sciencedirect.com/science/article/pii/S1433831922000579) — Cross-Check Samenschale/Langlebigkeit, Vernalisationsverhalten
8. §1.3/§1.6 dieses Steckbriefs (bereits zitierte Quellen) — Cross-Check Direktsaat, keine Vorkultur wegen Pfahlwurzel
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Rosette (1. Jahr) | 60–120 | 2 | false | false | high |
| Blüte (ab 2. Jahr) | 28–42 | 3 | false | false | medium |
| 2. Blüte (nach Schnitt) | 21–35 | 4 | true | false | medium |
| Winterruhe | 120–180 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) (VPD threshold, stomatärer Kollaps) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) (photosynthesis T_opt) | 18–22 (kühl-liebende Leguminose / cool-season legume) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-Vollsonne / open full sun) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Lupine als Stickstoff-Fixiererin NICHT mit Stickstoff düngen! Sie fixiert selbst aus der Luft (Symbiose mit Rhizobium-Bakterien). Auf nährstoffarmen Böden besonders wertvoll. Düngung kontraproduktiv — fördert weiches Gewebe, das anfälliger für Schädlinge ist. Kompost im ersten Jahr bei der Pflanzung ausreichend.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies/kalkarmes Wasser; pH 5,5–6,5; Staunässe absolut vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (keine Düngung) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Direktsaat | 2–3 cm tief; Reihenabstand 40–60 cm | hoch |
| Jun | Verblühten Rispenschnitt | Sofort nach erster Blüte; fördert Zweitblüte | mittel |
| Sep | Herbst-Aussaat | Für 1. Blüte im Folgejahr (früherer Zeitplan) | mittel |
| Nov | Alte Triebe stehen lassen | Stängel als Überwinterungsschutz | niedrig |
| Mär (Folgejahr) | Rückschnitt | Alte Stängel bodennah; Neuaustrieb fördern | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | — | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis lupinorum | Kolonien an Triebspitzen | shoot | vegetative | easy |
| Schnecken | Arion spp. | Fraß an Jungpflanzen | leaf, stem | seedling | easy |
| Lupinenblattstecher | Sitona spp. | Randständige Blattfraßmuster | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 5–10 | vegetative (späte Saison) |
| Wurzelfäule | fungal (Phytophthora spp.) | Welke, absterbende Triebe | Staunässe | 7–14 | alle |
| Lupinen-Anthraknose | fungal (Colletotrichum lupini) | Braune Flecken, Stängelnekrosen | Nässe | 5–10 | vegetative, flowering |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung / Biological Control)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (pro m²) | Etablierungszeit |
|----------|--------------------|----------------|------------------------|------------------|
| Schlupfwespe (parasitoid wasp) | Aphidius colemani | Blattläuse (Aphis lupinorum) | 0,1–0,5/m² präventiv; 1–3/m² kurativ; 2 Freilassungen im Wochenabstand | 10–14 Tage bis Mumienbildung (10 % Mumien = Population kollabiert bald) |
| Gallmücke (predatory gall midge) | Aphidoletes aphidimyza | Blattläuse (Aphis lupinorum) | 1–5/m²/Freilassung, wöchentlich wiederholt; alt.: 2–5 Puppen/m² | ~7–14 Tage; wirksam 20–30 °C |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (nitrogen_fixer) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kohl, Kürbis); nährstoffarme Böden |
| Empfohlene Nachfrucht | Alle Starkzehrer profitieren vom hinterlassenen Stickstoff |
| Anbaupause (Jahre) | 3–4 Jahre auf gleicher Fläche (Anthraknose-Prävention) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Echinacea | Echinacea purpurea | 0.8 | Gleiche Standortansprüche; optisch harmonisch | `compatible_with` |
| Rittersporn | Delphinium elatum | 0.8 | Gleiche Saison; Höhenschichten | `compatible_with` |
| Phlox | Phlox paniculata | 0.8 | Optisch; ähnliche Bedürfnisse | `compatible_with` |
| Ziergräser | Miscanthus sinensis | 0.7 | Naturgarten-Effekt | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Lupinus polyphyllus |
|-----|-------------------|-------------|--------------------------------------|
| Gelbe Lupine | Lupinus luteus | Gleiche Gattung | Einjährig; höherer N-Ertrag im Acker |
| Sandlupine | Lupinus nootkatensis | Gleiche Gattung | Kurzlebige Staude; robust |
| Engelmann-Lupine | Lupinus × regalis (Russell-Hybriden) | Züchtung | Farbenpracht; Gartenkultur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Lupinus polyphyllus,"Vielblättrige Lupine;Gartenlupine;Garden Lupin",Fabaceae,Lupinus,perennial,long_day,herb,taproot,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b",0.0,"Nordamerika, Pazifikküste",limited,25,40,150,80,50,no,limited,false,false,nitrogen_fixer,true,hardy,"5;6;7"
```

---

## Quellenverzeichnis

1. [Naturadb Lupinus polyphyllus](https://www.naturadb.de/pflanzen/lupinus-polyphyllus/) — Steckbrief
2. [Samen.de Lupinen](https://samen.de/blog/lieblingspflanze-der-gaertner-lupinen-richtig-aussaeen-und-pflegen.html) — Aussaat, Pflege
3. [Winterharte-Stauden Lupinus polyphyllus](https://winterharte-stauden.com/lupinus-polyphyllus-lupine/) — Winterhärte, Anbau
4. [Gartenfreud-Gartenleid Lupinus](https://www.gartenfreud-gartenleid.de/lupinus.php) — Steckbrief, Eigenschaften
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Biological Flora of Central Europe – Lupinus polyphyllus Lindley (ScienceDirect, peer-reviewed)](https://www.sciencedirect.com/science/article/pii/S1433831922000579) — Salzmeidung (salt-avoidance), Wurzelsystem (Pfahlwurzel + Nodulation), Ökologie
6. [Where Do Lupines Grow Best? Soil, Sun, and Climate (Biology Insights)](https://biologyinsights.com/where-do-lupines-grow-best-soil-sun-and-climate/) — Vollsonne, pH 5,5–7,0 (calcifuge), Pfahlwurzeltiefe 12–20 Zoll, Staunässe-Empfindlichkeit
7. [Lupines: Annual vs Perennial (Alibaba LifeTips)](https://lifetips.alibaba.com/plant-care/lupines-annual-perennial) — Vernalisation 6–8 Wochen Kälte, kurzlebige Staude 2–4 Jahre, Mindest-Direktsonne
8. [Are Lupines Perennials or Annuals? (The Plant Aide)](https://www.theplantaide.com/articles/108025.html) — Lebensdauer 3–5 Jahre, kurzlebige Staude
9. [Growth and yield of white lupin (Lupinus albus): effect of sowing date (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/0378429094900574) — GDD-Basistemperatur 4 °C für Lupinus, thermische Zeit
10. [Germination of Three Native Lupinus Species in Response to Temperature (Northwest Science, BioOne)](https://bioone.org/journals/Northwest-Science/volume-85/issue-2/046.085.0223/Germination-of-Three-Native-Lupinus-Species-in-Response-to-Temperature/10.3955/046.085.0223.pdf) — Kühltemperatur-Präferenz, Chilling-Begünstigung
11. [Aphidius colemani Tech Sheet (Sound Horticulture)](https://soundhorticulture.com/pages/aphidius-colemani-tech-sheet) — Ausbringrate Blattlaus-Schlupfwespe, Mumien-Etablierung
12. [Aphidoletes aphidimyza (Koppert)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/aphidoletes-aphidimyza/) — Ausbringrate Gallmücke gegen Blattläuse, Temperaturoptimum 20–30 °C
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
