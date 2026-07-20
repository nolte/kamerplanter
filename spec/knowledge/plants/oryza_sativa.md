# Reis — Oryza sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** IRRI (International Rice Research Institute), FAO Rice Crop Profile, USDA PLANTS Database, Bayerische LfL Sonderkultur Nassreis, University of Arkansas Division of Agriculture

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Oryza sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Reis, Asiatischer Reis; Asian Rice, Common Rice | `species.common_names` |
| Familie | Poaceae | `species.family` → `botanical_families.name` |
| Gattung | Oryza | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | grass <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher herb) --> | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false (einjährig; keine Endodormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tropisch/subtropisch; kein Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Kritische Tageslänge (critical day length, h) | 13.5 (fakultativer Kurztagblüher; Blüte beschleunigt unterhalb ~13,5 h) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 9a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frost-empfindlich; minimale Wachstumstemperatur 10°C; optimale Keimtemperatur 25–35°C; in Mitteleuropa nur im Gewächshaus oder wärmstem Sommer möglich (vereinzelte Freilandversuche in Südtirol und Baden bei Nassreis) | `species.hardiness_detail` |
| Heimat | Südost-/Ostasien (China, Indien); Domestizierung ca. 7.000–9.000 v. Chr. | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis für Mitteleuropa:** Nassreis (Sumpfreis, paddy rice) benötigt überflutete oder dauerfeucht-gesättigte Bedingungen und sehr hohe Temperaturen. In Mitteleuropa ist Anbau nur im Gewächshaus oder unter Vlies mit Wasserretentionsbecken möglich. Trockenreis (Upland Rice) ist weniger ertragreich, toleriert normale Bodenbedingungen. Beide Formen für den Kamerplanter primär als Bildungsprojekt / experimenteller Anbau relevant.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Anzucht im Warmhaus ab April) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14–21 (nur nach stabilem Sommereinbruch; min. 18°C Bodentemperatur) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (Mitteleuropa; Nassreis im Gewächshaus ab April) | `species.direct_sow_months` |
| Erntemonate | 9, 10 (bei Gewächshaus-Anbau; draußen nur in sehr warmen Jahren) | `species.harvest_months` |
| Blütemonate | 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Grundnahrungsmittel von 3,5 Milliarden Menschen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Gräser-Pollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stroheinarbeitung; Nassreis: Stoppel fluten oder einarbeiten) | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 (Nassreis in großem Wasserbehälter/Kübel mit Staunässe) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–180 (sortenabhängig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 × 20–30 cm (Pikiermethode) | `species.spacing_cm` |
| Indoor-Anbau | limited (Gewächshaus mit Wasserretention) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur wärmste Lagen; Staunässe-Behälter) | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Schwere lehmige Erde; wasserhaltendes Substrat; pH 5,5–6,5; KEINE durchlässige Erde | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 15 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 35 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 20–50 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | tolerant | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | 3.0 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 12 | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 5.5–7.0 | `species.soil_ph_preference` |

**Hinweis Lichtkompensationspunkt:** Gemessene Blatt-Werte liegen bei ~17–22 µmol/m²/s (paddy rice, Feldbedingungen); die Spanne 15–35 deckt schatten- bis sonnenakklimatisierte Blätter ab. Reis ist lichtbedürftig (Lichtsättigung erst bei ~1.500–1.800 µmol/m²/s); Beschattung senkt den Ertrag um 15–20 %. Der LCP-Wert beschreibt ausschließlich den Kompensationspunkt (Netto-Photosynthese = 0), nicht die Sättigung.

**Hinweis Wurzeltiefe:** FAO gibt die effektive Wurzeltiefe für Nassreis bei Ernte mit 50–75 cm an; der überwiegende Teil der aktiven Wurzelmasse konzentriert sich jedoch in den oberen 20–25 cm. Die angegebene Spanne 20–50 cm bildet die praktisch wirksame Hauptdurchwurzelung ab.

**Hinweis Salztoleranz:** Klassifikation nach Maas & Hoffman (FAO): Schwellen-ECe 3,0 dS/m (Bezug = Bodensättigungsextrakt ECe, NICHT Gießwasser-EC), Ertragsabnahme 12 % je dS/m oberhalb der Schwelle, Einstufung "sensitive". Reis ist besonders salzempfindlich im Sämlings- und Rispenanlagestadium; unter Flutung bezieht sich der ECe auf das Bodenwasser bei überstauten Pflanzen.

**Hinweis pH-Vorzug:** Die hier eingetragene Quellen-Vorzugsspanne 5,5–7,0 (PFAF / FAO-Ecocrop) ist weiter als die in §1.6/§2.3 für die Topf-/Nährlösungssteuerung verwendete engere Spanne 5,5–6,5; beide sind konsistent (das Topf-Optimum liegt innerhalb des breiteren Standort-Vorzugs).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 35 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 2 (Flachsaat; > 5 cm Saattiefe hemmt Feldaufgang deutlich, siehe Hinweis) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 5 (unter Optimalbedingungen; volle Feldemergenz je nach Wasserstand/Temperatur bis zu 9–13 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 2 (bei trockener Lagerung noch hohe Keimrate bis ca. 3 Jahre; danach deutlicher Rückgang unter Praxis-Lagerbedingungen) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | indifferent (moderne Kultursorten keimen weitgehend lichtunabhängig; nur seltene photoblastische Wildreis-/Unkrautreis-Typen sind lichtabhängig) | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak (24–48 h Einweichen vor der Aussaat/Inkubation ist Standardpraxis bei Direktsaat-/Nassreisanbau) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 25 (Sortenspanne ca. 16–32 g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 250 (Direktsaat; abgeleitet aus IRRI-Aussaatrate 60–80 kg/ha bei TKG ~25 g) | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Reis wird kommerziell überwiegend nass vorbehandelt: 24–48 h Einweichen gefolgt von 24–48 h feuchter Inkubation ("pre-germination"/Vorkeimung) vor der Aussaat, um eine zügige und gleichmäßige Keimung zu erreichen — dies gilt vor allem für Direktsaat- und Nassreissysteme. Die Saattiefe sollte flach gehalten werden: Untersuchungen zeigen 12–22 % geringeren Feldaufgang bei 0,5–1 cm Saattiefe und 48–60 % geringeren Aufgang bei 2 cm kombiniert mit Überflutung — daher wird eine Saattiefe von ca. 2–3 cm bei guter Wasserführung als praktikabler Kompromiss angegeben. Die Keimfähigkeit sinkt unter typischen Farm-Lagerbedingungen (30 °C, 70 % rF) sehr schnell (von 95 % auf 1 % innerhalb von 5 Monaten), während trockene/kühle Lagerung (Genbank-Standard) die Lagerfähigkeit auf Jahrzehnte verlängert — der hier angegebene Wert von 2 Jahren bezieht sich auf praxisübliche, nicht klimatisierte Saatgutlagerung.

Quellen (§1.8): [ScialErt — Germination Characteristics of Korean and Southeast Asian Redrice (Oryza sativa L.) Seeds as Affected by Temperature](https://scialert.net/fulltext/?doi=ajps.2010.104.107); [PMC — Optimizing Sowing and Flooding Depth for Anaerobic Germination-Tolerant Genotypes to Enhance Crop Establishment in Dry-Seeded Rice (Oryza sativa L.)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6265439/); [IRRI Rice Knowledge Bank — Seed rate (High)](http://www.knowledgebank.irri.org/decision-tools/rice-doctor/rice-doctor-fact-sheets/item/seed-high-rate); [Wikifarmer — Rice Planting, Seeding Requirements — Seed Rate of Rice](https://wikifarmer.com/library/en/article/rice-planting-seeding-requirements-seed-rate-of-rice); [ScienceDirect — Association Mapping of Thousand Grain Weight using SSR and SNP Markers in Rice](https://link.springer.com/article/10.1007/s12042-021-09282-7); [Agronomy Journal — Photoblastism and Ecophysiology of Seed Germination in Weedy Rice](https://acsess.onlinelibrary.wiley.com/doi/abs/10.2134/agronj2003.1840); [Journal of Experimental Agriculture International — Improving Rice Seed Longevity: Impact of Storage Containers, Conditions and Seed Moisture during Storage](https://journaljeai.com/index.php/JEAI/article/view/3522); [Nature Scientific Reports — Benefits of rice seed priming are offset permanently by prolonged storage and the storage conditions](https://www.nature.com/articles/srep08101)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling / Anzucht | 21–35 | 2 | false | false | low |
| Vegetativ / Bestockung | 40–70 | 3 | false | false | medium |
| Rispenschieben / Blüte | 25–35 | 4 | false | false | low |
| Abreife | 30–45 | 5 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 25–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–28 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–90 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 28–32 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 1 (dauerfeucht; Nassreis in stehendem Wasser) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Sämling / Anzucht

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 26–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 22–26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–85 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 28–33 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 1 (Staunässe für Nassreis) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ / Bestockung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (Langtagbedingungen verzögern Blüte; kurze Tage induzieren) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–28 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 30–35 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 1–2 (Nassreis: Wasserstand 5–15 cm halten) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Rispenschieben / Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | ≤12 (Kurztagbedingungen zwingend für Blüteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 26–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 22–26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 28–33 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 1 (Wasserstand 5–10 cm) | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Abreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 20–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 (trocken für Drusch) | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–5 (Wasserabzug 2–3 Wochen vor Ernte) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 (Spalten Mn/Zn/Cu/Mo ergänzt) -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Si (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 5.5–6.5 | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.8 | 5.5–6.5 | 60 | 25 | — | 0.3 | 0.05 | 0.02 | 0.01 |
| Vegetativ | 3:1:2 | 1.0–1.8 | 5.5–6.5 | 120 | 50 | 50 | 0.5 | 0.10 | 0.03 | 0.02 |
| Blüte | 1:2:2 | 1.2–2.0 | 5.5–6.5 | 100 | 50 | 50 | 0.5 | 0.10 | 0.03 | 0.02 |
| Abreife | 0:1:2 | 0.6–1.2 | 5.5–6.5 | 60 | 30 | 30 | 0.3 | 0.05 | 0.02 | 0.01 |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Die Mn/Zn/Cu/Mo-Werte sind Nährlösungs-Zielkonzentrationen (Feed, ppm) im Bereich gängiger C3-Kultur-Rezepturen. Zinkmangel ist die weltweit häufigste Mikronährstoffstörung im Nassreis (Maßnahme: Zn-Aufdüngung bei alkalischen/überfluteten Böden).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis Silizium:** Reis hat einen sehr hohen Si-Bedarf (höchster Si-Bedarf unter allen Kulturpflanzen). Silizium erhöht Standfestigkeit, Krankheitsresistenz und Hitzestresstoleranz.

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Harnstoff | diverse | mineralisch | 46-0-0 | 8–15 g/m² | Bestockung |
| Kalisufit / K2SO4 | diverse | mineralisch | 0-0-50 | 10–15 g/m² | Grunddüngung |
| Calciumsilikat | diverse | Mineralzusatz | — | 50–100 g/m² | Grunddüngung |
| Nitrophoska | Compo | Granulat | 12-12-17 | 20–40 g/m² | Ansatz |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 4–6 L/m² | Vor Pflanzung |
| Hornmehl | diverse | organisch | 50–80 g/m² | Vor Pflanzung |
| Reisstroh (eingearbeitet) | — | organisch | vorhandene Ernte | Zwischen-Saison |

### 3.2 Besondere Hinweise zur Düngung

Nassreis wächst in anaeroben (sauerstoffarmen) Bedingungen — Stickstoff NICHT als Nitrat düngen (wird denitrifikativ abgebaut), sondern als Ammonium (z.B. Harnstoff). Geteilte N-Gaben wichtig: Basisdüngung vor Pflanzung + Bestockungsdüngung. Eisenmangel auf alkalischen Böden möglich (Nassreis versauert die Rhizosphäre, löst Fe aus).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 1 (Nassreis: tägliche Wasserstandskontrolle) | `care_profiles.watering_interval_days` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies Wasser bevorzugt (pH 5,5–6,5); kein hartes Leitungswasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21–28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Saatgutvorbereitung | Samen 24–48h einweichen; Keimung im Warmhaus (25–30°C) | hoch |
| Apr–Mai | Anzucht | Sämlinge in Saatschale; Wasserstand 1–2 cm; 28–32°C | hoch |
| Mai–Jun | Pikierung / Pflanzung | 21–30 cm Abstand; Nassreis in überflutetes Beet | hoch |
| Jun–Aug | Wasserstandskontrolle | Wasserstand 5–15 cm; Zufluss bei Verdunstung | hoch |
| Jul–Aug | Rispenschieben | Photoperiode auf ≤12h kürzen falls Gewächshaus | mittel |
| Sep–Okt | Ernte | Ähren goldgelb; Körner klingen beim Drücken; Wasser abziehen | hoch |
| Okt | Nachtrocknung | Rispenbündel 2–3 Wochen hängend trocknen | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Reishalm-Bohrwurm | Chilo suppressalis | Totes Herz; Weißähre | Halm, Ähre | Bestockung, Blüte |
| Reiskäfer | Sitophilus oryzae | Gelagerte Körner; Fraßschäden | Korn (Lager) | — (Lager) |
| Blattläuse | Rhopalosiphum rufiabdominale | Kolonien; Gelb-Vergilbung | Blatt | Sämling, Vegetativ |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Reisbrand (Rice Blast) | fungal (Magnaporthe oryzae) | Rautenförmige Blattflecken; Halsbrand | feucht-warm |
| Braunfleckigkeit | fungal (Cochliobolus miyabeanus) | Braune Flecken; Kornverfärbung | N-Mangel; hohe Feuchte |
| Scheidenfäule | fungal (Rhizoctonia solani) | Wässrige Läsionen am Halmansatz | hohe Temperatur + Nässe |
| Bakterienbrand | bacterial (Xanthomonas oryzae) | Blattrandvergilbung; Welke | warm; Wasser-Infektion |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Trifloxystrobin | chemical | Trifloxystrobin | Sprühen | 21 | Reisbrand, Braunflecken |
| Kupferpräparate | biological | Kupferhydroxid | Sprühen | 3 | Bakterienbrand |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Reisbrand |
| Wasserstandsmanagement | cultural | — | Intermittierendes Fluten | 0 | Scheidenfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Schlupfwespe (Eiparasitoid) | Trichogramma japonicum | Reishalm-Bohrwurm (Chilo suppressalis) und weitere Halmbohrer (Scirpophaga incertulas) | 5–20 Tiere/m² (50.000–200.000/ha) je Freisetzung, 4 Freilassungen im Wochenabstand | 1–2 Wochen (mehrere Generationen pro Saison) |
| Grüne Reiswanze (Eiräuber) | Cyrtorhinus lividipennis | Zikaden/Planthopper-Eier und -Junglarven (z.B. Nilaparvata lugens, Sogatella furcifera, Nephotettix virescens) | Förderung durch Blühpflanzen/Refugien (augmentative Freisetzung möglich) | 2–3 Wochen (etabliert sich entlang der Wasserlinie) |

**Hinweis:** Reishalm-Bohrwurm und Zikaden treten unter mitteleuropäischen Gewächshausbedingungen selten auf; der Nützlingseinsatz ist primär für tropisch-subtropische Nassreis-Systeme relevant und hier als Referenz dokumentiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Getreide (Poaceae); Nassreis Sonderstellung |
| Empfohlene Vorfrucht | Leguminosen (Azolla, Soja); Gründüngung |
| Empfohlene Nachfrucht | Gemüse; Leguminosen; Trockenfrüchte |
| Anbaupause (Jahre) | In traditionellen Systemen: 2 Reisernten/Jahr im Tropengürtel; in Mitteleuropa einmalig pro Jahr |

### 6.2 Mischkultur

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Azolla (Wasserfarn) | Azolla filiculoides | 0.9 | Biologische N-Fixierung im Reisfeld; traditionell Asien | `compatible_with` |
| Sojabohne | Glycine max | 0.7 | Fruchtfolge-Leguminose; N-Fixierung | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Nassreis |
|-----|-------------------|-------------|---------------------------|
| Afrikanischer Reis | Oryza glaberrima | Gleiche Gattung | Toleranter gegen Trockenheit |
| Wildreis | Zizania aquatica | Aquatisches Getreide | Heimisch in Nordamerika; pflegeleichter in Teichen |
| Hirse | Sorghum bicolor / Panicum miliaceum | Wärmeliebend | Trockentolerant; kein Staunässebedarf |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Oryza sativa,"Reis;Asiatischer Reis;Asian Rice;Common Rice",Poaceae,Oryza,annual,short_day,herb,fibrous,"9a;9b;10a;10b;11a;11b;12a;12b",0.3,"Südost-/Ostasien",limited,limited,limited,true,false,heavy_feeder,false,tender,"5;6","9;10","7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Japonica Koshihikari,Oryza sativa,"japonica_type;sticky;short_grain",130,open_pollinated
Basmati 370,Oryza sativa,"indica_type;long_grain;aromatic",140,open_pollinated
Arborio,Oryza sativa,"japonica_type;risotto;high_starch",135,open_pollinated
```

---

## Quellenverzeichnis

1. [IRRI — Oryza sativa](https://www.irri.org/research/varieties) — Sortendatenbank, Anbaupraxis
2. [FAO Rice Crop Profile](https://www.fao.org/rice) — Nährstoffbedarf, globale Anbausysteme
3. [USDA PLANTS Database — Oryza sativa](https://plants.usda.gov/plant-profile/ORSA) — Taxonomie
4. [University of Arkansas — Rice Production](https://www.uaex.uada.edu) — Düngung, IPM
5. [Bayerische LfL — Exotische Sonderkulturen](https://www.lfl.bayern.de) — Mitteleuropa-Anbau
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [MDPI Agriculture — Rice Growth Modeling Based on Growth Degree Day (GDD)](https://www.mdpi.com/2077-0472/12/1/59) — GDD-Basistemperatur 10 °C für Reisentwicklung
7. [FAO — Crop Salt Tolerance Data (Maas & Hoffman)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Salztoleranz: ECe-Schwelle 3,0 dS/m, Slope 12 %/dS/m, Einstufung "sensitive"
8. [PMC — Evaluating Photosynthetic Light Response Models for Leaf Photosynthetic Traits in Paddy Rice](https://pmc.ncbi.nlm.nih.gov/articles/PMC11723129/) — Lichtkompensationspunkt rice ~17–22 µmol/m²/s
9. [PFAF — Oryza sativa Plant Database](https://pfaf.org/user/Plant.aspx?LatinName=Oryza+sativa) — Boden-pH-Vorzug 5,5–7,0; C3-Krautpflanze
10. [FAO — Irrigation Schedule for Paddy Rice (Effective Rooting Depth)](https://www.fao.org/4/t7202e/t7202e07.htm) — effektive Wurzeltiefe Nassreis 0,5–0,75 m bei Ernte
11. [Frontiers in Plant Science — Bifunctional regulators of photoperiodic flowering in short day plant rice](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.1044790/full) — fakultativer Kurztagblüher, kritische Tageslänge ~13,5 h
12. [Springer/Rice — Mechanisms for Coping with Submergence and Waterlogging in Rice](https://link.springer.com/article/10.1186/1939-8433-5-2) — hohe Staunässe-/Überflutungstoleranz (Aerenchym, ROL-Barriere)
13. [PMC — Assessment of Trichogramma japonicum and T. chilonis as Biological Control Agents of Stem Borer in Rice](https://pmc.ncbi.nlm.nih.gov/articles/PMC5371947/) — Eiparasitoid gegen Halmbohrer, Ausbringraten 50.000–200.000/ha
14. [IRRI Rice Knowledge Bank — Biological Control of Rice Insect Pests](http://www.knowledgebank.irri.org/bioControl/module_3/06.htm) — Cyrtorhinus lividipennis als Eiräuber von Zikaden/Planthoppern
15. [MDPI Agronomy — Physiological Factors Limiting Leaf Net Photosynthetic Rate in C3 Crops like Rice](https://www.mdpi.com/2073-4395/12/8/1830) — Reis als C3-Kultur; Lichtsättigung ~1.500–1.800 µmol/m²/s; T_opt Photosynthese 30–35 °C
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: seed-profile-backfill 2026-07 -->
16. [ScialErt — Germination Characteristics of Korean and Southeast Asian Redrice (Oryza sativa L.) Seeds as Affected by Temperature](https://scialert.net/fulltext/?doi=ajps.2010.104.107) — Keimtemperaturoptimum 20–30 °C
17. [PMC — Optimizing Sowing and Flooding Depth for Anaerobic Germination-Tolerant Genotypes to Enhance Crop Establishment in Dry-Seeded Rice](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6265439/) — Saattiefen-Effekt auf Feldaufgang, Flutungsbedingungen
18. [IRRI Rice Knowledge Bank — Seed rate (High)](http://www.knowledgebank.irri.org/decision-tools/rice-doctor/rice-doctor-fact-sheets/item/seed-high-rate) — Aussaatrate 60–80 kg/ha Direktsaat, 40 kg/ha Transplantierung
19. [Wikifarmer — Rice Planting, Seeding Requirements — Seed Rate of Rice](https://wikifarmer.com/library/en/article/rice-planting-seeding-requirements-seed-rate-of-rice) — Aussaatrate-Bestätigung, Nursery-Saatmenge
20. [Springer Tropical Plant Biology — Association Mapping of Thousand Grain Weight in Rice](https://link.springer.com/article/10.1007/s12042-021-09282-7) — Tausendkornmasse Sortenspanne 16–32 g, Durchschnitt ~25 g
21. [Agronomy Journal — Photoblastism and Ecophysiology of Seed Germination in Weedy Rice](https://acsess.onlinelibrary.wiley.com/doi/abs/10.2134/agronj2003.1840) — moderne Kultursorten lichtunabhängig keimend (indifferent), Photoblastismus nur bei Wildreis-Typen
22. [Journal of Experimental Agriculture International — Improving Rice Seed Longevity: Impact of Storage Containers, Conditions and Seed Moisture during Storage](https://journaljeai.com/index.php/JEAI/article/view/3522) — Keimfähigkeit bei Praxis-Lagerung, ~3 Jahre bei trockener Lagerung
23. [Nature Scientific Reports — Benefits of rice seed priming are offset permanently by prolonged storage and the storage conditions](https://www.nature.com/articles/srep08101) — Keimfähigkeitsverlust unter Farm-Lagerbedingungen (30 °C/70% rF)
<!-- /Quelle: seed-profile-backfill 2026-07 -->
