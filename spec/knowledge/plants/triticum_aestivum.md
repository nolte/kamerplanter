# Weizen — Triticum aestivum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, Bayerische LfL Weizenanbau, BBCH-Skala Getreide (Zadoks-Skala), FAO Crop Profiles, DLG-Merkblätter Pflanzenschutz

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Triticum aestivum | `species.scientific_name` |
| Volksnamen (DE/EN) | Weichweizen, Weizen, Brotweizen; Common Wheat, Bread Wheat | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Triticum | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| GDD-Basistemperatur (base temp, °C) | 0 | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation erforderlich (vernalization required) | true (nur Winterweizen; Sommerweizen false) | `lifecycle_configs.vernalization_required` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage (vernalization min days) | 50 (40–70 je nach Temp 0–8 °C; Winterweizen) | `lifecycle_configs.vernalization_min_days` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN: quantitativer Langtag-Schwellwert; Weizen ist quantitativer Langtagblüher ohne scharfe kritische Tageslänge --> | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sommerweizen: Frühjahrssaat; Winterweizen winterhart bis -20°C (unter Schneedecke), ohne Schnee bis -12°C; Vernalisation erforderlich für Wintertypen; Spätfrost-Schäden bei BBCH 49–55 | `species.hardiness_detail` |
| Heimat | Vorderer Orient (Fruchtbarer Halbmond); Domestizierung ca. 10.000–8.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis:** Triticum aestivum ist das weltweit meistangebaute Getreide und das wichtigste Backgetreide Mitteleuropas. Unterschieden werden Sommerweizen (März–April Saat; Juli–August Ernte) und Winterweizen (Oktober Saat; Juli Ernte). Winterweizen dominiert in Mitteleuropa aufgrund höherer Erträge.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -42 (Sommerweizen ab März; Winterweizen Oktober) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Sommerweizen); 9, 10 (Winterweizen) | `species.direct_sow_months` |
| Erntemonate | 7, 8 | `species.harvest_months` |
| Blütemonate | 5, 6 (Winterweizen); 6, 7 (Sommerweizen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |
| Bestäuber erforderlich (requires pollinator) | false | `species.requires_pollinator` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Bestäubung:** Weizen ist ein überwiegend selbstbefruchtender (autogamer) Kleistogamist; die Bestäubung erfolgt meist vor dem Öffnen der Blüten. `pollinator_group` und `compatible_pollinators` bleiben daher leer (keine pomologische Kreuzbefruchtungsgruppe, kein Befruchter-Sortenbedarf). Fremdbefruchtung (Windbestäubung) tritt nur in geringem Umfang auf.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Hauptnahrungsmittel der Menschheit; Mehl, Brot) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Gluten (Gliadin + Glutenin); Zöliakie-Auslöser; Weizenallergie möglich | `species.toxicity.toxic_compounds` |
| Schweregrad | none (außer Glutenunverträglichkeit/Zöliakie) | `species.toxicity.severity` |
| Kontaktallergen | true (Bäckerasthma; Berufsallergen; Weizenmehlstaub) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen; starkes Sommerallergen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stoppelbearbeitung, Strohmanagement) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 (Weizengras / Microgreens) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 70–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–15 (Einzelhalm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Drillsaat: Reihenabstand 10–15 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (Weizengras / Sprossen) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lehmige, nährstoffreiche Erde; pH 6,0–7,5; kalkverträglich | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein quantitativer Weizen-LCP aus zwei unabhängigen Quellen belegt; qualitativ höher als Gerste (Sonnenpflanze) --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 60–120 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | 6.0 (Maas-Hoffman a; bezieht sich auf Substrat-ECe, nicht Gießwasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | 7.1 | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweis:** Lichtsättigung (light saturation) der Photosynthese wird bei ~1000–1200 µmol/m²/s erreicht (90 % der Sättigung bei ~1000 µmol/m²/s); maximale Netto-Assimilation (Amax) 15–25 µmol CO₂/m²/s bei 20–25 °C. Diese Sättigungs-/Maximalwerte gehören NICHT in das Kompensationspunkt-Feld. Weizen ist schattenintolerant (im Vergleich zu Gerste höherer Lichtkompensationspunkt). Semi-Dwarf-Sorten sind salztoleranter (ECe-Schwelle ~8.6 dS/m, Slope ~3.0 %/dS/m); die Tabellenwerte gelten für Standard-Brotweizen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 4 (praktische Keimgrenze; Agri Farming nennt einen Keimbereich von 4–37 °C) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 35 (mittlere Kardinaltemperatur Tc laut Ali 1994; praktischer Bereich reicht bis ~37 °C) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 4 (Spanne 3–5 cm; deckt sich mit der Praxisangabe in §4.2) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (Spanne 7–10 Tage im Feld; ISTA-Testprotokoll zählt normale Keimlinge nach 8 Tagen aus) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (praktisches Nachbau-Fenster für farm-eigenes/„bin-run"-Saatgut: 1–3 Jahre, danach starker Sortenreinheits- und Vitalitätsverlust) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | <!-- DATEN FEHLEN: keine zwei unabhängigen, art-spezifischen Quellen zur Licht-/Dunkelkeimung von Weizen gefunden; allgemeine Aussagen zu Gräsern/Getreide sind nicht art-spezifisch belastbar --> | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (weder Stratifikation noch Skarifikation zur Keimung nötig; die Vernalisation in §1.1 betrifft die generative Entwicklung der Pflanze zur Blüteninduktion, nicht die reine Saatgutkeimung) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 45 (Mittelwert; europäische Winterweizen-Sorten 35,9–58,2 g, Mittel 45,4 g laut GWAS-Studie) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 400 (Zieldichte Drillsaat Winterweizen ca. 350–410 keimfähige Korn/m², abhängig von Feldverlust-Kalkulation) | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Die Vernalisationsanforderung von Winterweizen (§1.1) ist ein entwicklungsphysiologischer Kältereiz zur Blüteninduktion und unterscheidet sich klar von der reinen Saatgutkeimung — Weizensaatgut selbst benötigt keine Kältestratifikation, um zu keimen. Farm-eigenes ("bin-run") Saatgut wird laut US-Extension-Quellen praktisch 1–3 Jahre nachgebaut, wobei Sortenreinheit und Triebkraft von Jahr zu Jahr abnehmen; zertifiziertes Saatgut wird dagegen jährlich frisch bezogen und erreicht Keimraten ≥ 85–90 %.

Quellen (§1.8): [Agri Farming — Wheat Seed Germination, Time, Temperature, Procedure](https://www.agrifarming.in/wheat-seed-germination-time-temperature-procedure); [Ali (1994) — Variation in cardinal temperatures for germination among wheat (Triticum aestivum) genotypes, Annals of Applied Biology](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1744-7348.1994.tb04977.x); [ResearchGate — Wheat seed germination under the influence of temperature regimes (ISTA 8-Tage-Auszählung)](https://www.researchgate.net/publication/266463463_Wheat_seed_germination_under_the_influence_of_temperature_regimes); [PMC4555037 — Analysis of main effect QTL for thousand grain weight in European winter wheat](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4555037/); [Farmers Weekly — Why field loss is important for seed rate calculations](https://www.fwi.co.uk/arable/establishment/why-field-loss-is-important-for-seed-rate-calculations); [Nebraska CropWatch — Determining the Seeding Rate for Winter Wheat](https://cropwatch.unl.edu/determining-seeding-rate-your-winter-wheat/); [AgriLife Today — Farmer-saved wheat seed quality should be checked before planting](https://agrilifetoday.tamu.edu/2015/11/05/farmer-saved-wheat-seed-quality-should-be-checked-before-planting/); [Oklahoma State University Extension — Farmer-Saved Wheat Seed in Oklahoma: Questions and Answers](https://extension.okstate.edu/fact-sheets/farmer-saved-wheat-seed-in-oklahoma-questions-and-answers)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | high |
| Bestockung | 20–60 | 2 | false | false | high |
| Schossen | 21–35 | 3 | false | false | medium |
| Ährenschieben / Blüte | 14–21 | 4 | false | false | low |
| Milch- / Teigreife | 14–21 | 5 | false | false | medium |
| Vollreife / Ernte | 7–14 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–85 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 (Winterweizen: kurze Tage für Vernalisation) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 8–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 15–20 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Schossen

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–38 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Ährenschieben / Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | high (hitzeempfindlich zur Blüte; Pollensterilität) | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vollreife / Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 20–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 35–55 (trocken für Drusch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–2.5 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 2.9 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | low (Abreife; trockene Drusch-Bedingungen erwünscht) | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 (keine Bewässerung; Abreife trocken) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.5 | — | — | — | — | — | — | — |
| Bestockung | 3:1:2 | 0.8–1.4 | 6.0–7.5 | 80 | 30 | 20 | 0.5 | 0.05 | 0.02 | 0.01 |
| Schossen | 3:1:2 | 1.4–2.0 | 6.0–7.5 | 120 | 45 | 30 | 0.5 | 0.05 | 0.02 | 0.01 |
| Blüte | 1:2:2 | 1.2–1.8 | 6.0–7.5 | 100 | 50 | 25 | 0.5 | 0.05 | 0.02 | 0.01 |
| Reife | 0:1:2 | 0.6–1.0 | 6.0–7.5 | 60 | 30 | — | 0.3 | 0.05 | 0.02 | 0.01 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Mn/Zn/Cu/Mo-Werte (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`) orientieren sich an der Standard-Hoagland-Nährlösung (Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.01 ppm) als phasenübergreifende Referenz. Bei Boden-pH > 7.5 ist mit Mn-/Zn-/Cu-/Fe-Mangel zu rechnen; Mn ist im alkalischen Bereich kritisch (Blattaufhellung). Cu-Mangel betrifft besonders Sandböden und verursacht Ährenverkrüppelung ("Weißährigkeit"). Mo ist im sauren Bereich (pH < 5.5) kritisch.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Bestockung | time_based | 5–10 Tage; Keimblatt erscheint (BBCH 09–11) |
| Bestockung → Schossen | time_based | 20–60 Tage; nach Vernalisation; langer Tag (BBCH 30) |
| Schossen → Blüte | time_based | 21–35 Tage; Fahnenblatt voll entfaltet (BBCH 37) |
| Blüte → Reife | time_based | 14–21 Tage; Antheren sichtbar (BBCH 61); Korn setzt an |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kalkammonsalpeter (KAS) | diverse | Granulat | 27-0-0 | 40–60 g/m² | Schossen (EC 30) |
| Nitrophoska 12-12-17 | Compo | Granulat | 12-12-17 | 30–50 g/m² | Grunddüngung |
| Schwefel-Harnstoff | diverse | Granulat | 40-0-0+S | 25–40 g/m² | Schossen |
| Blattdünger Kalium | diverse | flüssig | 0-0-40 | 5–10 ml/L | Kornfüllungsphase |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 4–6 L/m² | Herbst-Grunddüngung |
| Rinderdung | diverse | organisch | 80–120 g/m² | Herbst |
| Hornmehl | diverse | organisch | 60–100 g/m² | Frühjahrssaat |
| Pflanzenkohle (Biochar) | diverse | Bodenverbesserer | 200–500 g/m² | Grunddüngung |

### 3.2 Besondere Hinweise zur Düngung

Weizen ist Starkzehrer mit dem höchsten N-Bedarf unter den Getreidearten (ca. 160–220 kg N/ha in der Landwirtschaft). Im Gartenbau gilt: Geteilte N-Gaben (Grunddüngung + Schossen-Gabe) verhindern Lagergefahr. Schwefel (S) ist wichtig für die Backqualität (Glutenbildung). Bei Bodenanalyse: pH 6,5–7,5 anstreben.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Sep–Okt | Winterweizen-Saat | Optimales Saatfenster 1.–25. Oktober; Saattiefe 3–5 cm | hoch |
| Mär | Sommerweizen-Saat | Frühsaat ab Ende Februar/Anfang März | hoch |
| Apr | N-Düngung Grundgabe | Stickstoff zur Vegetationsphase | mittel |
| Mai | N-Düngung Schossen | Qualitätsstickstoff bei BBCH 30–32 | hoch |
| Jun | Fungizidkontrolle | Ährengesundheit sichern (BBCH 51–65) | mittel |
| Jul–Aug | Ernte | Körnerfeuchte 13–14%; Sofortdrusch bei Wetter | hoch |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung (nur Winterweizen)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | none (im Feld; Schneedecke als natürlicher Schutz) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 (November; vor Wintereinbruch) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | none (Vegetationsstart bei Erwärmung; keine Abdeckung zu entfernen) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (März; Vegetationsbeginn, 1. N-Gabe) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | -20 bis +5 (Feld; winterhart bis -20 °C unter Schneedecke, ohne Schnee bis -12 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | natürliche Tageslänge (Freiland; keine Zusatzbeleuchtung) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | keine (natürlicher Niederschlag; Bestockung bei BBCH 13–25 vor Winter erwünscht) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Winterweizen überwintert als bestockte Jungpflanze direkt im Feld und benötigt die Kälteperiode zur Vernalisation (siehe §1.1). Es handelt sich NICHT um eine frostfreie Innenüberwinterung (`frost_free`) oder Knollen-Einlagerung (`dig_and_store`), sondern um winterharte Feldüberdauerung (`hardy`). Bei Topfkultur (Weizengras) entfällt die Überwinterung, da nur die annuelle Sommerweizen-/Microgreen-Nutzung relevant ist. Auswinterungsrisiko bei Kahlfrost ohne Schneedecke und bei Spätsaat (zu schwach entwickelte Bestände).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Getreideblattlaus | Sitobion avenae | Kolonie auf Ähren; Honigtau; BYDV-Vektor | Ähre, Blatt | Schossen, Blüte |
| Getreidehähnchen | Oulema melanopus | Blattfraß in Streifen | Blatt | Schossen |
| Weizengallmücke | Sitodiplosis mosellana | Kleinkörnige Ähren; Kornabtrieb | Ähre | Blüte |
| Hessische Gallmücke | Mayetiola destructor | Halmnekrose; Blattverformung | Halm, Blatt | Bestockung |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Septoria-Blattdürre | fungal (Zymoseptoria tritici) | Hellbraune Flecken; Pyknidien | feucht-kühl |
| Gelbrost | fungal (Puccinia striiformis) | Gelbe Pustelstreifen | kühl-feucht |
| Braunrost | fungal (Puccinia triticina) | Braune Pusteln; Ertragsverlust | warm-feucht |
| Echter Mehltau | fungal (Blumeria graminis f.sp. tritici) | Weißgrauer Belag | trocken-warm |
| Ährenfusarium | fungal (Fusarium graminearum) | Weißähren; Mykotoxine (DON, ZEA) | feucht zu Blüte |
| Steinbrand | fungal (Tilletia caries) | Stinkende Sporenlager in Körnern | Saatgut |

**KRITISCH — Ährenfusarium:** Mykotoxine (Deoxynivalenol DON, Zearalenon ZEA) gefährden Lebensmittel- und Futterqualität. Monitoring und resistente Sorten zwingend. Befallenes Erntegut nicht für Nahrungsmittel verwenden.

### 5.3 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Nützling | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|---------------|-----------------|------------------|
| Brackwespe (Aphidius ervi) | Getreideblattlaus (Sitobion avenae) | 0.25–2 Tiere/m²/Freilassung (wöchentlich wiederholen) | ca. 14 Tage (erste Mumien sichtbar; T_opt 20–25 °C) |
| Marienkäfer (Coccinella septempunctata, Adalia bipunctata) | Blattläuse | 2–10 Larven/m² je nach Befall | wenige Tage (Larven fressen sofort) |
| Florfliege (Chrysoperla carnea) | Blattläuse | 5–10 Larven/m² | wenige Tage (Larven fressen sofort) |
| Ohrwurm (Forficula auricularia) | Blattläuse, Insekteneier | nicht kommerziell ausgebracht; Förderung durch Habitatangebot | saisonal (Naturpopulation) |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Triazol-Fungizid | chemical | Tebuconazol | Sprühen BBCH 31–65 | 35 | Rost, Septoria, Ährenfusarium |
| Strobilurin-Fungizid | chemical | Azoxystrobin | Sprühen BBCH 32–49 | 35 | Rost, Mehltau, Septoria |
| Saatgutbeizung | chemical | Tebuconazol + Fludioxonil | Beize | — | Brandkrankheiten |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Rost, Septoria, Mehltau |
| Weite Fruchtfolge | cultural | — | Max. 50% Getreide | 0 | Halmbasiserkrankungen |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Getreide (Poaceae) |
| Empfohlene Vorfrucht | Raps (beste Vorfrucht!), Hülsenfrüchte, Zuckerrübe, Kartoffel |
| Empfohlene Nachfrucht | Raps, Sommergerste, Leguminosen |
| Anbaupause (Jahre) | 2 Jahre Pause empfohlen; maximal 50% Getreide in Fruchtfolge |

**Stoppelweizen (Weizen nach Weizen):** Stark erhöhtes Krankheitsrisiko (Septoria, Ährenfusarium, Halmbasis); vermeiden! Raps als Vorfrucht steigert Ertrag um 10–15% (Rapsvorfruchteffekt).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kleearten | Trifolium spp. | 0.8 | Untersaat; N-Fixierung; Erosionsschutz nach Ernte | `compatible_with` |
| Ackererbse | Pisum sativum | 0.7 | Gemengepartner (Weizen-Erbsen-Gemenge); N-Fixierung | `compatible_with` |
| Luzerne | Medicago sativa | 0.7 | Untersaat; tiefe Bodenlockerung; N-Fixierung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Gerste | Hordeum vulgare | Gleiche Pathogene (Mehltau, Rost); Konkurrenz | moderate | `incompatible_with` |
| Mais | Zea mays | Fusarium-Suszeptibilität beider; Inokulum-Anreicherung | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Weichweizen |
|-----|-------------------|-------------|-------------------------------|
| Dinkel | Triticum spelta | Engste Verwandtschaft (Unterart) | Robuster; Nischenmarkt; ohne Fusarium-Toleranz |
| Emmer | Triticum turgidum subsp. dicoccum | Urgetreide | Historisch; Nischenmarkt |
| Durum-Weizen | Triticum turgidum subsp. durum | Hartweizen | Nudelqualität; Mediterran |
| Triticale | × Triticosecale | Roggen-Weizen-Kreuzung | Robuster auf schwachen Böden |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Triticum aestivum,"Weichweizen;Weizen;Brotweizen;Common Wheat;Bread Wheat",Poaceae,Triticum,annual,long_day,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.2,"Vorderer Orient",limited,limited,limited,false,false,heavy_feeder,false,half_hardy,"3;4;9;10","7;8","5;6;7"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Julius,Triticum aestivum,"winter_wheat;high_yield;good_baking_quality",270,septoria;yellow_rust,certified
RGT Sacramento,Triticum aestivum,"winter_wheat;high_yield;early",265,fusarium;yellow_rust,certified
Alixan,Triticum aestivum,"summer_wheat;baking_quality;medium_early",110,fusarium_tolerant,certified
```

---

## Quellenverzeichnis

1. [USDA PLANTS Database — Triticum aestivum](https://plants.usda.gov/plant-profile/TRAE) — Taxonomie
2. [Bayerische LfL — Winterweizenanbau](https://www.lfl.bayern.de/ipz/getreide) — Anbaupraxis, Sorten
3. [BBCH-Skala Getreide (Meier 2001)](https://www.bba.de) — Entwicklungsstadien
4. [DLG Merkblatt Ährenfusarium](https://www.dlg.org) — Mykotoxin-Risiko, Bekämpfung
5. [Saaten-Union Weizensortenkatalog](https://www.saaten-union.de) — Sortenbeschreibungen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [FAO — Wheat growth and physiology (Acevedo, Silva & Silva)](https://www.fao.org/4/y4011e/y4011e06.htm) — Photosynthese-Optimum 20–25 °C, Amax 15–25 µmol CO₂/m²/s, Lichtsättigung ~1000 µmol/m²/s
7. [FAO — Annex 1: Crop salt tolerance data](https://www.fao.org/4/y4263e/y4263e0e.htm) — Maas-Hoffman ECe-Schwelle 6.0 dS/m, Slope 7.1 %, Rating MT (moderately tolerant)
8. [USDA-ARS / Wikipedia — Salt tolerance of crops (Maas & Hoffman 1977)](https://en.wikipedia.org/wiki/Salt_tolerance_of_crops) — Bestätigung Salztoleranzklasse Weizen
9. [Frontiers / PMC — Shade tolerance in wheat (photosynthetic limitation & acclimation)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11655228/) — Weizen schattenintolerant (full_sun), höherer Lichtkompensationspunkt als Gerste
10. [Herzog et al. 2016, Plant Cell & Environment — Mechanisms of waterlogging tolerance in wheat](https://onlinelibrary.wiley.com/doi/10.1111/pce.12676) — Staunässe-Empfindlichkeit (sensitive)
11. [Frontiers / DOAJ — Can Growing Degree Days and Photoperiod Predict Spring Wheat Phenology?](https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2017.00057/full) — GDD-Basistemperatur 0 °C, Langtag-Photoperiode
12. [OSU Agronomic Crops Network — Vernalization Requirements for Winter Wheat](https://agcrops.osu.edu/newsletter/corn-newsletter/2020-04/vernalization-requirements-winter-wheat) — Vernalisation 40–70 Tage (~50 Tage Standard)
13. [PMC — Effect of photoperiod on wheat vernalization genes VRN1/VRN2](https://pmc.ncbi.nlm.nih.gov/articles/PMC4739792/) — Langtag-Einstufung, Vernalisationsbedarf Wintertypen
14. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Referenz Mn 0.5 / Zn 0.05 / Cu 0.02 / Mo 0.01–0.048 ppm
15. [Koppert — Aphidius ervi (parasitic wasp)](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-ervi/) — Ausbringrate 0.25–2/m²/Freilassung
16. [Plant Protection Science — Effect of temperature on development & parasitism of Aphidius ervi](https://www.agriculturejournals.cz/publicFiles/01157.pdf) — Etablierung ~14 Tage (erste Mumien), T_opt 20–25 °C
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
