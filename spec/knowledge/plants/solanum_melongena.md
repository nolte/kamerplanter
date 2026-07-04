# Aubergine — Solanum melongena

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** RHS Aubergine Detail, PFAF Solanum melongena, Deep Green Permaculture Growing Guide, First Tunnels Top Of The Crops Aubergines, USDA PLANTS Database Solanum melongena, Plantura, Compo, LfL Bayern Aubergine

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Solanum melongena | `species.scientific_name` |
| Volksnamen (DE/EN) | Aubergine, Eierpflanze; Eggplant, Aubergine, Brinjal | `species.common_names` |
| Familie | Solanaceae | `species.family` -> `botanical_families.name` |
| Gattung | Solanum | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus (botanisch) | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor 2026-07 -- Korrektur von 'annual (in Mitteleuropa); perennial (Tropen)' auf botanisch korrektes 'perennial'; siehe Quellen 19-22 -->
| Anbau-Zyklustyp (cultivation cycle type) | annual | `lifecycle_configs.cultivation_cycle_type` |
<!-- Quelle: growing-phase-auditor 2026-07 -- Aubergine ist botanisch eine kurzlebige/zaertliche Staude (tender perennial) in frostfreien Klimazonen, wird in Mitteleuropa aber wegen Frostempfindlichkeit einjaehrig kultiviert. cultivation_cycle_type ueberschreibt die botanische cycle_type fuer Ueberwinterungs- und Saisonende-Logik (grown_as_annual = true). Siehe Quellen 19-22. -->
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10–11 (Wuchs-/Phänologie-Basis der Hauptwuchsphase; warmliebende Solanaceae) | `species.base_temp` |
| Lebensdauer (Jahre, nur perennial) | 2–3 (kurzlebige Staude in frostfreien Tropen/Subtropen; in Mitteleuropa einjährig) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false (tropische Art ohne Kältedormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tagneutrale Art ohne Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | — (entfällt; false) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (critical day length, h) | <!-- DATEN FEHLEN: tagneutral, kein Kurztag-/Langtag-Schwellenwert; Photoperiodik über photoperiod_type=day_neutral abgebildet --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Wird in Mitteleuropa als einjährige Kultur angebaut. Abstirben bei Temperaturen unter 2°C. In subtropischen Klimazonen mehrjährig. | `species.hardiness_detail` |
| Heimat | Suedost-Asien (Indien, Burma), kultiviert seit >4000 Jahren | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7–8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat Feb.–Mär.; Auberginen brauchen laenger als Tomaten) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (keine Direktsaat sinnvoll; Kulturdauer zu lang) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — (nur Vorkultur) | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate (empfindlichere Keimung als Tomate) | `species.propagation_difficulty` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Befruchter erforderlich (requires pollinator) | false (selbstfruchtbar; zwittrige „perfekte" Blueten mit Staub- und Fruchtblatt) | `species.requires_pollinator` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Bestaeubungs-Hinweis (kein KA-Feld):** Aubergine ist selbstfruchtbar und benoetigt KEINE Befruchtersorte (`pollinator_group` bleibt leer — kein Obst-Fremdbefruchter). Im Gewaechshaus ohne Insekten verbessert Vibrationsbestaeubung (leichtes Schuetteln der Bluetenstaende, „buzz pollination") den Fruchtansatz.

**Keimhinweise:**
- Optimale Keimtemperatur: 25–30°C (Heizmatte fast unverzichtbar)
- Minimale Keimtemperatur: 18°C (sehr langsam)
- Keimdauer: 7–14 Tage
- Saattiefe: 0.5–1 cm
- Substrat: Naehrstoffarme Anzuchterde; gleichmaessig feucht; Abdeckplatte/Haube waehrend Keimung
- Wichtig: Mehr Waerme und Licht als Tomaten; Vorkultur im beheizten Zimmer oder auf Heizmatte

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (alle gruenen Pflanzenteile enthalten Solanin) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true (gruene Teile; reife Fruechte unbedenklich) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves; stems; unripe_fruits | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Solanin; Solasonin; Solamargin | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Blatttrichome; Kontaktdermatitis moeglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7; 8 | `species.pruning_months` |

**Pruning-Hinweis:** Auberginen auf 3–4 Hauptaeste begrenzen (Pinzieren des Haupttriebs nach 4–5 Blattpaaren foerdert Verzweigung). Fruechte auf max. 4–6 pro Pflanze begrenzen fuer optimale Fruchtgroesse. Regelmaessiges Entfernen abgestorbener Blaetter.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–25 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 60–120 (sortenabhaengig) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50–60 | `species.spacing_cm` |
| Indoor-Anbau | limited (nur unter kuenstlicher Belichtung; sehr hoher Lichtbedarf) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (sehr gut geeignet; braucht Waerme und Schutz vor Wind) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (optimale Kulturbedingungen in Mitteleuropa; deutlich besserer Ertrag) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Fruchtlast kann Aeste brechen; Spiralstab oder Schnur) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose Pflanzerde (Tomatenpflanzerde geeignet) mit gutem Wasserhaltvermoegens; pH 5.8–6.8; gute Drainage. Kompostbeimischung 20–30% empfohlen. | -- |

### 1.7 Umgebungs-Physiologie & Standortqualitaet

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (mind. 6–8 h direkte Sonne; nicht schattentolerant) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–60 (Pfahlwurzel bis ~60 cm; aktive Hauptzone obere 30–45 cm) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz (waterlogging tolerance) | sensitive (gedeiht nicht auf schlecht drainierten Boeden; gute Drainage erforderlich) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (Maas & Hoffman) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 1.1 (Substrat-ECe im Saettigungsextrakt; Maas-Hoffman a) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 6.9 (Maas-Hoffman b; Ertragsrueckgang je dS/m oberhalb Schwelle) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.8–6.8 | `species.soil_ph_preference` |

**Hinweis (kein KA-Feld):** Der Lichtkompensationspunkt steigt mit der Blatttemperatur; bei >30 °C liegt er hoeher. Die Lichtsaettigung liegt mit ~1000–1100 µmol/m²/s sehr hoch (linearer Anstieg der Nettophotosynthese bis dahin) — dieser Wert gehoert NICHT in das Kompensationspunkt-Feld, sondern erklaert den hohen Lichtbedarf der Art.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | low |
| Saemling | 21–42 | 2 | false | false | low |
| Vegetativ | 28–42 | 3 | false | false | medium |
| Bluete | 14–28 | 4 | false | false | medium |
| Fruchtbildung / Reife | 30–60 | 5 | false | true | high |
| Seneszenz | 14–21 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–5 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 22–26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht-Anker; bei FR-armem LED-Spektrum niedriger) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Substrat feucht halten; nie austrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht-Anker; bei FR-armem LED-Spektrum niedriger) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht-/Vollsonnen-Anker; bei FR-armem LED-Spektrum niedriger) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–32 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 26–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht-/Vollsonnen-Anker; bei FR-armem LED-Spektrum niedriger) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–700 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Bluetenansatz-Hinweis:** Unterhalb 15°C und ueber 35°C Tagestemperatur faellt die Bluete ab und es bilden sich keine Fruechte. Bestaeuben durch leichtes Schuetteln der Pflanze (besonders im Gewaechshaus ohne Insekten).

#### Phase: Fruchtbildung / Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–32 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 26–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht-/Vollsonnen-Anker; bei FR-armem LED-Spektrum niedriger) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (regelmaessig; Trockenheit foerdert Bitterkeit) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–900 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

<!-- Mn/Zn/Cu/Mo-Spalten: Quelle: Steckbrief-Erweiterung 2026-06 -->
| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0 | — | — | — | — | — | — | — | — |
| Saemling | 2:1:1 | 0.6–0.8 | 5.8–6.2 | 100 | 40 | 20 | 2 | 0.4 | 0.08 | 0.04 | 0.04 |
| Vegetativ | 3:1:2 | 1.2–1.8 | 5.8–6.2 | 150 | 50 | 25 | 3 | 0.6 | 0.10 | 0.05 | 0.05 |
| Bluete | 1:2:3 | 1.4–2.0 | 6.0–6.5 | 130 | 60 | 30 | 2 | 0.6 | 0.10 | 0.05 | 0.05 |
| Fruchtreife | 1:2:3 | 1.4–2.0 | 6.0–6.5 | 120 | 60 | 25 | 2 | 0.6 | 0.10 | 0.05 | 0.05 |
| Seneszenz | 0:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | 15 | 1 | 0.3 | 0.06 | 0.03 | 0.03 |

### 2.4 Phasenubergangsregeln

| Von -> Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung -> Saemling | time_based | 7–14 Tage | Keimblätter voll entfaltet |
| Saemling -> Vegetativ | time_based | 21–42 Tage | 4–6 echte Blätter; Pikieren oder Topfen |
| Vegetativ -> Bluete | event_based | — | Erste Bluetenknospen sichtbar |
| Bluete -> Fruchtreife | event_based | — | Erste Fruechte bilden sich |
| Fruchtreife -> Seneszenz | event_based | — | Ernte abgeschlossen; Pflanze stellt Wachstum ein |

---

## 3. Düngung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Topf)

| Produkt | Marke | Typ | NPK | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Hakaphos Rot | ICL / Compo Expert | base | 12-12-17+2 | 1 | Vegetativ |
| Hakaphos Violet | ICL / Compo Expert | base | 13-5-26+3 | 1 | Bluete, Frucht |
| Compo Duenger Gemuese Fluessig | Compo | NPK fluessig | 7-3-7 | 1 | alle Phasen |
| CalMag Plus | diverse | supplement | 4-0-0+Ca+Mg | 2 | alle |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | Oscorna | organisch-N | 80–120 g/m² | Pflanzung + 4 Wochen danach |
| Kompost | eigen | organisch | 5–8 L/m² | Herbst/Fruehjahr |
| Tomatendünger Bio | Plantura | organisch-fluessig | 25 ml/5 L Giesswasser | Vegetativ bis Frucht |
| Bananenschalenpulver | DIY / Planterra | organisch-K | 10–20 g/Pflanze | Bluetephase |

### 3.2 Düngungsplan

| Woche | Phase | Massnahme | Produkt | Menge | Hinweise |
|-------|-------|----------|---------|-------|----------|
| 0 | Auspflanzen | Grundduengung | Kompost + Hornspäne | 6 L/m² + 100 g/m² | Einarbeiten |
| 2–4 | Vegetativ | Fluessigduengung | Gemuese-Fluessigduenger N-betont | 14-taeglich | pH 6.0–6.5 pruefen |
| 6–8 | Vorblüte | Umstellen auf P/K | PK-betonter Duenger | 14-taeglich | N reduzieren |
| 8–16 | Frucht | Kaliumgabe + CaMag | Patentkali + CaMag | 7–14-taeglich | BER-Praevention |

### 3.3 Mischungsreihenfolge

1. CalMag-Supplement als erstes in Giesswasser
2. Grundduenger (N-P-K)
3. Booster / Zusaetze
4. pH-Korrektur (immer zuletzt)

### 3.4 Besondere Hinweise

Auberginen reagieren aehnlich wie Tomaten auf Calciummangel (Bluetenendfaeule / BER bei Wasserstress). Gleichmaessige Bewaesserung ist entscheidend. Bitter schmeckende Fruechte entstehen bei Hitzestress, unregelmäßiger Bewässerung oder zu später Ernte. Kalium ist besonders wichtig fuer die Fruchtqualitaet.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig in DE) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Gleichmaeßig feucht; Trockenheitsperioden vermeiden; lauwarmes Wasser bevorzugen (KaltwasskälteSchock vermeiden) | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5, 6, 7, 8, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Vorkultur starten | Aussaat bei 25–28°C auf Heizmatte | hoch |
| Mär | Pikieren | Bei 2–3 echten Blattpaaren in 9cm-Toepfe | hoch |
| Apr | Umtopfen | In 15–20 cm Toepfe; weiter im Haus oder Gewaechshaus | mittel |
| Mai (nach 15.) | Auspflanzen | Nach den Eisheiligen; Abstand 50–60 cm | hoch |
| Mai–Sep | Regelmaessig waessern | Nie Boden austrocknen lassen; Wurzeln trockenheitsempfindlich | hoch |
| Jun–Sep | Duengen | 14-taeglich mit Fluessigduenger | mittel |
| Jun–Sep | Pinzieren und Stuetzen | Auf 3–4 Haupttriebe; Fruechte begrenzen auf 4–6 | mittel |
| Jul–Okt | Ernte | Vor voller Reife (Farbe sortentypisch; Haut glänzt noch) | hoch |

### 4.3 Ueberwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
In Mitteleuropa wird die Aubergine ueblicherweise einjaehrig kultiviert. Eine Ueberwinterung ist nur als frostfreie Kuebel-/Topfpflanze sinnvoll (in den Tropen mehrjaehrig); der Ertrag im Folgejahr ist meist geringer als bei Neuanzucht.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme (winter action) + Monat | move_indoors (Okt., vor erstem Frost) | `overwintering_profiles.winter_action` |
| Fruehjahrs-Massnahme (spring action) + Monat | move_outdoors (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action` |
| Winterquartier — Temperatur (°C) | 15–18 (frostfrei, hell und warm; unter 10 °C Wachstumsstillstand/Schaeden) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier — Licht | hell (Suedfenster oder Pflanzenlampe; Lichtmangel fuehrt zu Vergeilung) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier — Gießen | sparsam; Substrat nur leicht feucht halten; Staunaesse vermeiden | `overwintering_profiles.winter_quarter_watering` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste Blattunterseite; gelbliche Stippen | leaf | vegetative, flowering | medium |
| Blattlaus | Myzus persicae | Kolonien an Triebspitzen; Honigtau; Rußtau | shoot, leaf | seedling, vegetative | easy |
| Weiße Fliege | Trialeurodes vaporariorum | Winzige weiße Fliegen; Honigtau; Schwaechung | leaf | all | easy |
| Thrips | Frankliniella occidentalis | Silberne Raspelspuren; Deformation | leaf | vegetative, flowering | medium |
| Coloradokaefer | Leptinotarsa decemlineata | Stark-Fraßschäden; orange-schwarz-gestreifte Kaefer | leaf, stem | all | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kraut- und Braunfaeule | Phytophthora infestans | Braune oelige Flecken; Welke | Feuchtigkeit, Kaelte | 3–7 | all |
| Grauschimmel | Botrytis cinerea | Grauer Schimmelbelag; Faeulnis | hohe rLF, Verletzungen | 3–5 | flowering, ripening |
| Echter Mehltau | Leveillula taurica | Weisser Belag auf Blaettern | trockene Bedingungen | 5–10 | vegetative |
| Verticillium-Welke | Verticillium dahliae | Einseitiges Welken; braune Leitbuendel | Bodenpilz; Stress | 7–21 | vegetative, fruiting |
| Bluetenendfaeule (BER) | physiologisch (Ca-Mangel) | Dunkle, eingesunkene Flecken am Bluetenende der Frucht | Calciummangel + Wasserstreit | — | fruiting |

### 5.3 Nuetzlinge

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10–20 | 7–14 |
| Encarsia formosa | Weiße Fliege | 3–5 | 21 |
| Aphidoletes aphidimyza | Blattlaeuse | 2–5 | 7–14 |
| Amblyseius swirskii | Thrips, Weiße Fliege | 25–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5–1% Spruehloesung; Blattunterseite | 7 | Spinnmilbe, Blattlaeuse, Weiße Fliege |
| Insektenseife | biological | Kaliumseife | 1–2% Loesung; direkt aufspruehen | 1 | Blattlaeuse, Weiße Fliege |
| Pyrethrum | biological | Pyrethrine | Abends spruehen | 3 | Thrips, Blattlaeuse |
| Insektenschutznetz | cultural | — | Feinmaschig; ab Auspflanzung | 0 | Coloradokaefer, Weiße Fliege |
| Bodenlockerung + Kupfer | cultural | Kupferhydroxid | Boden; Vorbeugung | 3 | Verticillium (Bodenbehandlung) |

### 5.5 Resistenzen

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine bekannte Artenresistenz (Sorten zeigen variable Anfaelligkeit) | varietal | — |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Nachtschattengewaechse (Solanaceae) |
| Empfohlene Vorfrucht | Huelsenfrüchte (Leguminosen: Erbse, Bohne) |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Spinat) oder Gruenduengung |
| Anbaupause (Jahre) | 3–4 Jahre selbe Familie (Phytophthora, Verticillium) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Basilikum | Ocimum basilicum | 0.9 | Thrips-Repellenz; Aroma-Verbesserung | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeuberforderung | `compatible_with` |
| Bohne | Phaseolus vulgaris | 0.7 | N-Fixierung; Bodenstruktur | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.7 | Bodenbedeckung; Naehrstoff-Ergaenzung | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Bodenschutz; Untersaat; wenig Konkurrenzdruck | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Gleiche Familie; Phytophthora; Thrips; Ressourcenkonkurrenz | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gleiche Krankheiten (Phytophthora infestans) | severe | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Solanaceae | `shares_pest_risk` | Phytophthora, Verticillium, Coloradokaefer, Thrips | `shares_pest_risk` |

---

## 7. Ernte-Indikatoren

**Richtige Ernte-Indikatoren Aubergine:**
- Schale ist sortentypisch ausgefaerbt (dunkelviolett, weiss, gestreift je nach Sorte)
- Schale glaenzt intensiv (stumpfe Schale = ueberreif; bitterer Geschmack!)
- Frucht gibt bei leichtem Fingerdruck nach und springt zurueck (wie ein Tennisball)
- Stiel noch gruen; keine Verfaerbung
- Kernen sind noch hell (dunkle Kerne = ueberreif)
- **Nie uebereif ernten:** Fleisch wird holzig und extrem bitter. Lieber frueh ernten.

---

## 8. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Aubergine |
|-----|-------------------|-------------|------------------------------|
| Tomatillo | Physalis philadelphica | Solanaceae; aehnliche Kultur | Robuster; weniger Schädlingsanfaellig; Physalis-Familie |
| Paprika | Capsicum annuum | Gleiche Familie; aehnlicher Anbau | Weniger hitzebeduerftiger; breiter Sortensortiment |
| Thai-Aubergine (Erbsenaubergine) | Solanum torvum | Selbe Gattung | Deutlich robuster; hitzeliebend; asiatische Kueche |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Solanum melongena,Aubergine;Eierpflanze;Eggplant;Brinjal,Solanaceae,Solanum,annual,day_neutral,herb,fibrous,9a;9b;10a;10b;11a;11b,0.0,Suedostasien,yes,15–25,30,60–120,40–70,50–60,limited,yes,true,true,heavy_feeder
```

### 9.2 Cultivar CSV-Zeilen

```csv
name,parent_species,days_to_maturity,traits,seed_type,notes
Black Beauty,Solanum melongena,75–85,dark_purple;oval;classic,open_pollinated,Klassische Sorte; grosse ovale Fruechte; dunkelviolett
Listada de Gandia,Solanum melongena,75–80,purple_white_striped;italian_type,open_pollinated,Gestreift lila-weiss; milder Geschmack
Ping Tung Long,Solanum melongena,65–75,long_thin;asian_type;prolific,open_pollinated,Asiatische Sorte; lange schmale Fruechte; ertragreich
Rotonda Bianca Sfumata di Rosa,Solanum melongena,70–80,white_pink;round;mild_taste,open_pollinated,Weiss-rosafarbene runde Fruechte; sehr mild
Diamond F1,Solanum melongena,65–75,dark_purple;hybrid;disease_tolerant,hybrid F1,Hybrids mit gutem Krankheitswiderstand; ertragreich
```

---

## Quellenverzeichnis

1. RHS — Solanum melongena Aubergine Plant Detail — https://www.rhs.org.uk/plants/105486/solanum-melongena/details
2. PFAF — Solanum melongena Plant Database — https://pfaf.org/user/Plant.aspx?LatinName=Solanum+melongena
3. Deep Green Permaculture — Eggplant Aubergine Growing Guide — https://deepgreenpermaculture.com/2024/10/23/eggplant-aubergine-growing-guide/
4. First Tunnels — Top Of The Crops Aubergines — https://www.firsttunnels.co.uk/page/Top-Of-The-Crops-Aubergines
5. USDA Plant Materials — Solanum melongena Plant Guide — https://plants.sc.egov.usda.gov/DocumentLibrary/plantguide/pdf/pg_some.pdf
6. Purdue University Horticulture — Aubergine/Eggplant Growing Guide — https://hort.purdue.edu/newcrop/morton/cape_gooseberry.html
7. Plantura — Aubergine anbauen Sortenvergleich — https://www.plantura.garden/
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
8. ScienceDirect (Pereira et al. 2025) — Base and upper temperature thresholds for GDD (FAO56rev) Review; Eggplant Tbase zwischen 10–11 °C — https://www.sciencedirect.com/science/article/pii/S037837742500469X
9. Pioneer Agronomy — C3 and C4 Photosynthesis: Implications for Crop Production (Solanaceae/Gemuese als C3) — https://www.pioneer.com/us/agronomy/c3-c4-photosynthesis-crop-production.html
10. Heuvelink/de Koning (1996), ScienceDirect — Effects of Light and CO2 on Net Photosynthesis Rates of Aubergine (Lichtkompensationspunkt, Lichtsaettigung ~1100 µmol/m²/s) — https://www.sciencedirect.com/science/article/abs/pii/S0305736483710267
11. ScienceDirect Topics — Light Compensation (LCP-Definition, Spannen, Temperaturabhaengigkeit) — https://www.sciencedirect.com/topics/engineering/light-compensation
12. USDA-ARS (Heakal/Shalhevet; Plant and Soil) — Salt tolerance of eggplant: moderately sensitive, ECe-Schwelle 1.1 dS/m, Slope 6.9 %/dS/m (Maas-Hoffman) — https://link.springer.com/article/10.1007/BF02378847
13. USDA-ARS — Effects of Salinity on Eggplant (Solanum melongena L.) (Maas & Hoffman Klassifikation) — https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P2269.pdf
14. USU Extension — How to Grow Eggplant in Your Garden (Vollsonne, 6–8 h; nicht schattentolerant; Drainage) — https://extension.usu.edu/yardandgarden/research/eggplant-in-the-garden
15. The Old Farmer's Almanac — Planting and Growing Eggplant (Vollsonne; gut drainierter Boden; kein Staunaesse) — https://www.almanac.com/plant/eggplants
16. MU Extension — Eggplant Production (Pfahlwurzel ~50–60 cm; tiefwurzelndes Gemuese; pH-Vorzug) — https://extension.missouri.edu/publications/g6369
17. UF/IFAS EDIS HS796/CV216 — Nutrient Solution Formulation for Hydroponic Tomatoes (Mikronaehrstoff-Richtwerte Mn/Zn/Cu/Mo; auf Solanaceae-Fruchtgemuese uebertragbar) — https://edis.ifas.ufl.edu/publication/CV216
18. Gardener's Path — Tips for Pollinating Eggplant by Hand (selbstfruchtbar, zwittrige Blueten; Vibrationsbestaeubung) — https://gardenerspath.com/plants/vegetables/hand-pollinate-eggplant/
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -- botanischer Lebenszyklus (perennial vs. annual Kulturpraxis) -->
19. NC State Extension Gardener Plant Toolbox — Solanum melongena (Aubergine, Brinjal, Eggplant): "Annual or short-lived perennial plant that is very sensitive to cold temperatures"; "In North Carolina, eggplant is considered an annual" — https://plants.ces.ncsu.edu/plants/solanum-melongena/
20. PFAF — Solanum melongena (ergaenzender Zitatbeleg zu Quelle 2): "a PERENNIAL growing to 1m... usually cultivated as an annual... A short-lived perennial plant"; "is not frost-hardy, though it can be grown as an annual in temperate zones" — https://pfaf.org/user/Plant.aspx?LatinName=Solanum+melongena
21. Missouri Botanical Garden — Eggplant Factsheet: Eggplants "though perennial in warm areas, typically ... grown as warm-season annuals" in temperate climates — https://www.missouribotanicalgarden.org/Portals/0/Gardening/Gardening%20Help/Factsheets/Eggplant15.pdf
22. RHS — Solanum melongena (ergaenzender Zitatbeleg zu Quelle 1): "In the wild it is perennial, but in the UK it is treated as an annual as it isn't hardy" — https://www.rhs.org.uk/plants/105486/solanum-melongena/details
<!-- /Quelle: growing-phase-auditor 2026-07 -->
