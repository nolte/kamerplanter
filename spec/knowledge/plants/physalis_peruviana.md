# Andenbeere — Physalis peruviana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Wikipedia Physalis peruviana, CABI Compendium Physalis peruviana, Purdue University Cape Gooseberry, Gardenia.net Physalis peruviana, CRFG Cape Gooseberry, GardenAndAllotment Cape Gooseberry Guide, Growables.org Cape Gooseberry, Floral Encounters Physalis

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Physalis peruviana | `species.scientific_name` |
| Volksnamen (DE/EN) | Andenbeere, Kapstachelbeere, Physalis; Cape Gooseberry, Golden Berry, Poha, Inca Berry | `species.common_names` |
| Familie | Solanaceae | `species.family` -> `botanical_families.name` |
| Gattung | Physalis | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher shrub) --> | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus (botanisch) | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor 2026-07 -- cycle_type ist strikt enum-wertig (Literal['annual','biennial','perennial'], REQ-001 SS LifecycleConfig) und darf keinen gemischten Text ("perennial (in Heimat); annual...") enthalten. Botanisch ist Physalis peruviana ein zaertlicher, halb-ausdauernder Kleinstrauch / tender perennial subshrub (PFAF, CABI Compendium, Purdue NewCrop, Fischer & Melgarejo 2020 -- bereits Quelle 8 dieses Dokuments), in Mitteleuropa jedoch wegen Frostempfindlichkeit einjaehrig kultiviert. Siehe cultivation_cycle_type unten fuer die Kulturpraxis-Ueberschreibung. -->
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Anbau-Zyklustyp (cultivation cycle type) | annual | `lifecycle_configs.cultivation_cycle_type` |
<!-- Quelle: growing-phase-auditor 2026-07 -- cultivation_cycle_type ueberschreibt die botanische cycle_type fuer Ueberwinterungs- und Saisonende-Logik (grown_as_annual = cultivation_cycle_type=='annual' and cycle_type!='annual' = true). Konsistent mit dem bereits im Repo etablierten Muster fuer Solanum lycopersicum (gleiche Familie, gleiche Kultur-vs-Botanik-Situation). -->
| Photoperiode | short_day (fakultativer/quantitativer Kurztagspflanze (facultative short-day plant); Bluetinduktion bei Tageslaengen < 12 h gefoerdert, 8-h-Photoperiode verkuerzt Juvenilphase ggue. 16 h) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | 6.3 (Wuchs-/Phaenologie-Basis fuer Knoten-/Sprossentwicklung; NICHT die Keim-Basistemperatur) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebensdauer (Jahre) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 2–3 (in Heimat halb-ausdauernd/semi-perennial; kommerzielle Fruchtproduktion ueber ~18 Monate; in Mitteleuropa einjaehrig) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> false (keine echte Dormanz; tropisch-andine Art ohne Ruhephase) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> false (kein Kaeltebedarf zur Bluetinduktion; Bluete kurztag- und thermalzeitgesteuert) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> — (entfaellt, vernalization_required=false) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (critical day length, h) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 12 (Kurztagschwelle; Bluetinitiation bei Tageslaengen < 12 h) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `lifecycle_configs.critical_day_length_hours` |
| USDA Zonen | 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. In Mitteleuropa als Einjährige kultiviert oder im Frühling als Kübelpflanze hereingeholt. Abstirben bei 0°C. In Heimat (Andenhochland) mehrjährig und buschfoermig bis 1.5m Hoehe. | `species.hardiness_detail` |
| Heimat | Andenhochland (Peru, Ecuador, Kolumbien) auf 500–3000 m Hoehe | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; fruit | `species.traits` |

**Kultivierungsbesonderheit:** Die Andenbeere stammt aus den kuehlen Andenhochlagen und bevorzugt maessige Temperaturen (15–25°C). Zu hohe Temperaturen (> 35°C) und Frost sind beide problematisch. Dies macht sie ideal fuer gemäßigtes Klima (Mitteleuropa). Die Frucht ist in der Papierhuelse (einem trockenen Kelch) eingeschlossen, was sie vor Schaedlingen und Fruehjahrsfroeisten schuetzt.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7–8).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat Feb.–Mär.; laengere Kulturzeit noetig) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (nur Vorkultur; Kulturdauer zu lang) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — (nur Vorkultur) | `species.direct_sow_months` |
| Erntemonate | 8; 9; 10 (Fruechte fallen wenn reif ab; Lese vom Boden moeglich; Ernte endet regulaer mit erstem Frost, ~Mitte Oktober in Mitteleuropa) | `species.harvest_months` |
<!-- Quelle: growing-phase-auditor 2026-07 -- Korrektur von [8,9,10,11] auf [8,9,10]: 4 unabhaengige Quellen (samen.de, beetfreunde.de, Purdue NewCrop "fruit in August ... until there is a strong frost", Lubera "fruehestens Ende August") beschreiben die Ernte fuer Mitteleuropa/temperierte Klimazonen uebereinstimmend als Aug-Okt, endend mit dem ersten Frost; November passt nicht zur eigenen Frost-Schutz-Angabe in SS4.2 (Okt: "Vor erstem Frost abernten"). Siehe Quellenverzeichnis Punkte 16-19 unten. -->
| Bluetemonate | 6; 7; 8; 9 | `species.bloom_months` |
<!-- Quelle: growing-phase-auditor 2026-07 -- Verifiziert, unveraendert: Lubera bestaetigt woertlich "Bluetezeit: Juni - September" (deckungsgleich); PFAF nennt "in flower from July to October" (leicht abweichend); samen.de-Rechnung (Ernte ab Ende August minus 8-9 Wochen Fruchtreifezeit) stuetzt Bluetebeginn im Juni/Juli. 2/3 Quellen bestaetigen den bestehenden Wert exakt, daher keine Aenderung (Konfidenz Original-Wert: GESICHERT). -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 20–25°C
- Keimdauer: 14–20 Tage (laenger als Tomate; Geduld erforderlich)
- Saattiefe: 3–5 mm
- Substrat: Naehrstoffarme Aussaaterde; gleichmaessig feucht; Abdeckhaube waehrend Keimung
- Stecklinge: Im Herbst vor Frost Triebspitzen abschneiden, innen halten und im naechsten Frühling als Mutterpflanze nutzen (Mehrjahrigkeit erhalten)

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (alle gruenen Pflanzenteile, Kelch; reife Fruechte unbedenklich) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (Solanin-Verwandte in Blaettern und Kelch) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true (gruene Pflanzenteile, unreife Fruechte — NICHT der trockene Papierkelch!) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves; stems; unripe_fruits; calyx (frischer Kelch) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Physalin; Solanin-Glykoalkaloide (in gruenen Teilen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Wichtig:** Nur die reifen, goldgelben Fruechte ohne Kelch essen. Unreife Fruechte (gruen) sind gering toxisch.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6 (Einpinzieren nach Auspflanzung zur Verzweigungsfoerderung) | `species.pruning_months` |

**Hinweis:** Junge Pflanzen nach dem Auspflanzen einpinzieren (Haupttrieb kuerzen) um buschigen Wuchs zu foerdern. Dies steigert den Ertrag erheblich. Ausgewachsene Pflanzen nicht stark zurueckschneiden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–25 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 80–150 (in Mitteleuropa einjährig eher 80–120 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–120 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 70–90 | `species.spacing_cm` |
| Indoor-Anbau | limited (nur unter Belichtung; Bluete braucht Kurztagbedingungen oder Kuehlreiz) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (gute Kuebelplanze; geschuetzte, sonnige Position) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (in Mitteleuropa; sichert Ertrag und verlaengert Saison) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Busch kann windanfaellig sein; Spiralstab oder Tomaten-Kaefig) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gut durchlaessige, naehrstoffreiche Pflanzerde (Tomatenpflanzerde); pH 5.5–7.0; leicht saurer Boden foerderlich; gute Drainage essentiell (Staunaesse = Wurzelfaeule) | -- |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualitaet

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | 12 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 15 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–60 | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 5.5–6.8 | `species.soil_ph_preference` |

**Hinweise zu §1.7:**
- **Lichtkompensationspunkt:** Belegter Messwert Ic = 13.645 µmol Photonen/m²/s (Feldbedingungen Bogota); hier als Spanne 12–15 angegeben. Zur Orientierung (NICHT in das LCP-Feld gehoerend): Lichtsaettigung bei ca. 208 µmol/m²/s, Photosyntheserate A ≈ 10.5 µmol CO2/m²/s — die Art gilt als lichtbeduerftig (light-demanding) und braucht 1.500–2.000 h direkte Sonne/Jahr.
- **Wurzeltiefe:** Quellen beschreiben einerseits ein flach-fibroeses, oberflaechennahes Wurzelsystem (daher Mulchbedarf), andererseits eine effektive Durchwurzelungstiefe von ~60 cm im Feldanbau; Spanne 30–60 cm deckt beide Angaben ab.
- **Salztoleranz:** Als "moderately tolerant to salinity" eingestuft; 30 mM NaCl (Naehrloesungs-EC ~3 dS/m) foerdert das Wachstum, bis ~60 mM (~6 dS/m) wird toleriert. Eine formale Maas-Hoffman-Analyse (ECe-Schwelle a / Slope b, Bezugsgroesse Substrat-ECe) liegt nicht vor — diese Felder daher als DATEN FEHLEN markiert; die belegte Toleranz stuetzt jedoch die Klasse moderately_tolerant.
- **Boden-pH:** Quellen nennen 5.5–7.0 bzw. 5.5–6.8; uebernommener Vorzugsbereich 5.5–6.8 harmonisiert mit §1.6 (5.5–7.0) und den Naehrstoffprofilen §2.3 (Wurzelzone 5.8–6.5).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (Seed-Profile-Backfill, Batch 10, Issue #301) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 29 (wissenschaftliche Studie belegt sogar Optimum bei 27–32 °C) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.5–2 | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14 (Spanne 14–20 Tage bei 20–25 °C, bis zu 42 Tage bei niedrigeren Temperaturen) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | <!-- DATEN FEHLEN: keine dual belegte Jahresangabe; Lagerungsstudie zeigt hohe Keimfähigkeit bis 16 Monate unter kühler/trockener Lagerung, keine belastbare Übertragung auf eine Standard-Jahresangabe --> | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Tausendkornmasse (g) | ca. 1 | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: ausschließlich Vorkultur in Presstöpfen/Anzuchtschalen (siehe §1.2), keine Reihen-/Direktsaat-Flächendichte dokumentiert --> | `species.seed_profile.sowing_density_per_m2` |

**Vorbehandlung:** Keine dokumentierte Vorbehandlung — Lichtkeimer, keine Stratifikation/Skarifikation in den Quellen genannt.

Quellen (§1.8):
1. [Germination Performance of Physalis peruviana L. Seeds under Thermal and Water Stress Conditions — MDPI Agronomy](https://www.mdpi.com/2073-4395/14/6/1213) — Keimtemperatur-Optimum 27–32 °C, Lichtbedarf (Dunkelheit hemmt Keimung signifikant), Saattiefe 1–2 cm
2. [Purdue University NewCrop — Cape Gooseberry](https://hort.purdue.edu/newcrop/morton/cape_gooseberry.html) / [Gardenia.net — Physalis peruviana](https://www.gardenia.net/plant/physalis-peruviana-gooseberry) — Keimtemperatur 20–25 °C, Keimdauer 14–20 Tage, helles Licht fördert Keimung (bereits §1.3)
3. [SciELO Brazil — Germination of Physalis peruviana L. seeds under varying conditions of temperature, light, and substrate](https://www.scielo.br/j/rca/a/d8cjK8DhMwjxjvdZQYpWwft/?lang=en) — TKG ≈1 g/1000 Samen (≈1000–1050 Samen/g)
4. [Association Study Reveals Novel Genes Related to Yield and Quality of Fruit in Cape Gooseberry — PMC5869928](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5869928/) — Samenzahl je Frucht, Saatgutgröße (Kontext TKG)
5. [Germination Eco-physiology and Emergence of Physalis peruviana Seedlings — ResearchGate](https://www.researchgate.net/publication/330559582_Germination_Eco-physiology_and_Emergence_of_Physalis_peruviana_Seedlings) — Lagerungsstudie: hohe Keimfähigkeit bis 16 Monate bei kühler/trockener Lagerung
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (Seed-Profile-Backfill, Batch 10, Issue #301) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–20 | 1 | false | false | low |
| Saemling | 28–42 | 2 | false | false | low |
| Vegetativ / Eingewoehnung | 28–42 | 3 | false | false | medium |
| Kurztagsreaktion / Bluete | 14–28 | 4 | false | false | medium |
| Fruchtbildung | 60–90 | 5 | false | true | high |
| Spaetreife / Abschluss | 14–28 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–5 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 0.9 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> medium <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 15–18 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 0.45–0.55 (Tageslicht/Vollsonne-Anker) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.far_red_fraction` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 1.2 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> medium <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 15–18 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 0.45–0.55 (Tageslicht/Vollsonne-Anker) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.far_red_fraction` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (nach Auspflanzung)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (volle Sonne; Langtagphasen nicht für Fruchtbildung noetig) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.2 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 1.6 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> medium <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 15–18 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 0.45–0.55 (Tageslicht/Vollsonne-Anker) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.far_red_fraction` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 22–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (Kurztag-Reaktion; ab August natuerlich kuerzer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 (kuehle Naechte foerdern Bluete und Fruchtansatz) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 1.8 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> medium <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 15–18 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 0.45–0.55 (Tageslicht/Vollsonne-Anker) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.far_red_fraction` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–700 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Kurtag-Hinweis:** Physalis peruviana ist eine (fakultative/quantitative) Kurztagpflanze. Fruchtansatz erst wenn Tage kuerzer als ~12 Stunden werden (ab Ende August/September in Mitteleuropa). <!-- Quelle: Steckbrief-Erweiterung 2026-06: Kurztagschwelle auf belegte 12 h harmonisiert --> Deshalb ist fruehes Auspflanzen (Mai) wichtig — die Pflanze baut vegetative Masse auf bis die Taglaenge abnimmt. Dann foelgt Bluete und Fruchtbildung.

#### Phase: Fruchtbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 1.8 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> medium <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 15–18 <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> 0.45–0.55 (Tageslicht/Vollsonne-Anker) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.far_red_fraction` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 (nicht zu feucht; Wurzelfaeulegefahr) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–700 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0 | — | — | — | — | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->—<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | — | — | — |
| Saemling | 2:1:1 | 0.5–0.8 | 5.8–6.5 | 80 | 30 | 20 | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |
| Vegetativ | 3:1:2 | 1.0–1.6 | 5.8–6.5 | 120 | 50 | 25 | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |
| Bluete | 1:2:3 | 1.2–1.8 | 5.8–6.5 | 100 | 50 | 25 | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |
| Fruchtbildung | 1:2:3 | 1.2–1.8 | 5.8–6.5 | 100 | 50 | 20 | 1 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |
| Spaetreife | 0:1:2 | 0.8–1.2 | 5.8–6.5 | 60 | 30 | 15 | 1 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.3<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronaehrstoff-Hinweis:** Die Werte fuer Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdaen (Mo) entsprechen dem etablierten Vollkonzentrations-Niveau einer Hoagland-Standardnaehrloesung (Mn 0.5; Zn 0.05; Cu 0.02; Mo 0.011 ppm), das fuer Solanaceae-Fruchtgemuese (z.B. Tomate) als Richtwert dient. Mikronaehrstoffe werden nicht phasenspezifisch variiert; in der Spaetreife/Flush-Phase wird Mn leicht reduziert. `nutrient_profiles.manganese_ppm` / `.zinc_ppm` / `.copper_ppm` / `.molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenubergangsregeln

| Von -> Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung -> Saemling | time_based | 14–20 Tage | Keimblätter entfaltet |
| Saemling -> Vegetativ | time_based | 28–42 Tage | 4–6 echte Blaetter; Auspflanzen nach Eisheiligen |
| Vegetativ -> Bluete | event_based | — | Erste Knospen/Bluete moeglich bereits ab Juni unter Langtagbedingungen (fakultative Kurztagpflanze, kein obligater Kurztagzwang); Bluetenbildung und Fruchtansatz verstaerken/beschleunigen sich deutlich sobald die Taglaenge < 12 Stunden faellt (Kurztagschwelle; ab Ende August/September in DE) <!-- Quelle: growing-phase-auditor 2026-07 -- Praezisierung: die urspruengliche Formulierung suggerierte einen obligaten Kurztag-Trigger, was der eigenen photoperiod_type=short_day-Einstufung als "fakultative/quantitative" Kurztagpflanze (SS1.1) und Bluetemonate=[6,7,8,9] (Lubera: "Juni-September") widersprach. Siehe Quellen 8 (Fischer & Melgarejo 2020) und 11 (Heinze & Midasch 1991), die beide eine foerdernde (nicht obligate) Kurztagwirkung belegen. --> |
| Bluete -> Fruchtbildung | event_based | — | Bestaeubing erfolgt; Fruchtansatz sichtbar unter Kelch |
| Fruchtbildung -> Spaetreife | event_based | — | Kelch trocknet; Frucht faellt ab oder leicht loesbar |

---

## 3. Düngung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | Oscorna | organisch-N | 60–80 g/Topf | Auspflanzung |
| Kompost | eigen | organisch | 20% Substratanteil | Grundsubstrat |
| Tomatendünger Bio | Plantura | organisch-fluessig | 15–20 ml/5 L | Bluete und Frucht |
| Kali-Vinasse | Compo | organisch-K | 20 ml/10 L | Fruchtphase |

#### Mineralisch (Ergaenzung)

| Produkt | Marke | Typ | NPK | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Hakaphos Violet | ICL / Compo Expert | mineralisch | 13-5-26 | 1 | Bluete, Frucht |
| CalMag | diverse | supplement | 4-0-0+Ca+Mg | 2 | alle |

### 3.2 Düngungsplan

| Woche | Phase | Massnahme | Produkt | Menge | Hinweise |
|-------|-------|----------|---------|-------|----------|
| 0 | Auspflanzung | Grundduengung | Kompost + Hornspäne (im Substrat) | 20%+60g/Topf | Im Substrat einarbeiten |
| 2–6 | Vegetativ | Fluessigduengung N-betont | Tomatendünger | 10–15 ml/5L wöchentl. | pH 5.8–6.5 pruefen |
| 7–12 | Bluete | Umstellen auf PK | Hakaphos Violet | 1–2 g/L | N reduzieren |
| 12–18 | Frucht | Kalium + Calcium | Kali-Vinasse + CalMag | 14-taeglich | BER-Praevention |

### 3.3 Mischungsreihenfolge

1. CalMag zuerst ins Giesswasser
2. Grundduenger
3. Booster / PK-Additiv
4. pH-Korrektur zuletzt

### 3.4 Besondere Hinweise

Andenbeere ist kein so intensiver Starkzehrer wie Tomate oder Aubergine. Zu viel Stickstoff foerdert ueppiges Blattwachstum auf Kosten des Fruchtertrags. Gleichmaessige Bewaesserung ist wichtig — Trockenheitsstress + Wiederbewaesserung fuehrt zu Fruchtplatzern. Fruechte mit der getrockneten Papier-Huelse (Kelch) koennen wochen-/monatelang gelagert werden. Kelch erst kurz vor dem Essen entfernen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.3 (falls als Kuebelplanze eingewintert) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Gleichmaessig feucht; Staunaesse unbedingt vermeiden (Wurzelfaeule!); keine Beregnung von oben | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5, 6, 7, 8, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (falls ueberwintert) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Vorkultur | Aussaat bei 20–22°C auf Heizmatte; geduldige Keimung (14–20 Tage) | hoch |
| Mär | Pikieren | Bei 3–4 echten Blättern in 9–12 cm Toepfe | hoch |
| Apr | Umtopfen | In groessere Toepfe; abhaerten | mittel |
| Mai (nach 15.) | Auspflanzen | Nach Eisheiligen; 70–90 cm Abstand; Stuetze sofort | hoch |
| Mai–Jun | Einpinzieren | Haupttrieb nach 30–40 cm kuerzen; buschigen Wuchs foerdern | hoch |
| Jun–Jul | Vegetative Phase | Pflanzen bauen Blattmasse auf; regelmaessig giessen und duengen | mittel |
| Aug | Blueteeinleitung | Ab August automatisch durch Taglaengenabnahme | beobachten |
| Aug–Okt | Fruchtbildung | Regelmaessig giessen; keine Staunässe; Fruechte sammeln wenn Kelch trocken | hoch |
| Okt | Frost-Schutz | Vor erstem Frost abernten oder unter Glasdach bringen | hoch |
| Okt–Nov | Ueberwinterung (optional) | Pflanze stark einpinzieren; bei 10–15°C Frostfreiheid ueberwinterung moeglich | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Rating | frost_free | `overwintering_profiles.hardiness_rating` | <!-- Quelle: Steckbrief-Erweiterung 2026-06: korrigiert von needs_protection auf frost_free — frostempfindliche Kuebelpflanze, die frostfrei drinnen ueberwintert wird (winter_action=move_indoors), entspricht laut KA-Enum frost_free, nicht needs_protection (= Schutz im Freiland) -->

| Winter-Massnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Massnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Massnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; gelbliche Flecken | leaf | vegetative, flowering | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Weisse Fliegen; Honigtau; Rußtau | leaf | all | easy |
| Blattlaus (Grüne Pfirsichlaus) | Myzus persicae | Kolonien; Honigtau; Schrumpfblatt | shoot, leaf | seedling, vegetative | easy |
| Coloradokaefer | Leptinotarsa decemlineata | Stark-Fraßschäden; oranfe-schwarz-Kaefer | leaf | all | easy |
| Erdfloh | Epitrix spp. | Kleine Loecherfraesse | leaf | seedling | medium |
| Fruchtmotte | Phthorimaea spp. | Fraß in Frucht unter Kelch; Larven | fruit | ripening | difficult |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | Leveillula taurica | Weisser Belag auf Blaettern | Trockenhitzephasen | 5–10 | vegetative, flowering |
| Wurzelfaeule | Pythium spp. | Braune faulige Wurzeln; Welke | Ueberwaesserung; Staunaesse | 3–10 | all |
| Grauschimmel | Botrytis cinerea | Grauer Schimmel an Kelchen und Fruechten | hohe Feuchtigkeit; Verletzungen | 3–7 | fruiting |
| Kraut- und Braunfaeule | Phytophthora infestans | Braune oelige Flecken; Welke | kuehles feuchtes Wetter | 3–7 | all |
| Virosen (Physalis Virus) | Diverse Viren (z.B. CMV) | Mosaik-Verfaerbung; Kraeuseln; Verkuemmerung | Blattlaeusse als Uebertraeger | latent | all |

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
| Neemöl | biological | Azadirachtin | 0.5% Spruehlosung | 7 | Spinnmilbe, Blattlaeuse, Weiße Fliege |
| Insektenseife | biological | Kaliumseife | 1.5% Loesung; direkt | 1 | Blattlaeuse, Weiße Fliege |
| Insektenschutznetz | cultural | — | Feinmaschig; Erdfloh-Schutz | 0 | Erdfloehe, Coloradokaefer |
| Gute Drainage sicherstellen | cultural | — | Substrat mit 20% Perlite; Topfloecher offen | 0 | Wurzelfaeule |
| Luft-Management | cultural | — | Locker pflanzen; keine Beregnung von oben | 0 | Mehltau, Grauschimmel |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Nachtschattengewaechse (Solanaceae) |
| Empfohlene Vorfrucht | Huelsenfrüchte (N-Fixierung); Getreide |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Kraeuter, Zwiebeln) |
| Anbaupause (Jahre) | 3–4 Jahre (Solanaceae-Pause; Verticillium, Phytophthora) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeuberforderung | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Schädlings-Repellenz; Aroma | `compatible_with` |
| Bohne | Phaseolus vulgaris | 0.7 | N-Fixierung; Bodenlockerung | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.6 | Bodenbedeckung; Nuetzlingsfoerderung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Gleiche Krankheiten (Phytophthora, Viren, Weiße Fliege) | severe | `incompatible_with` |
| Aubergine | Solanum melongena | Gleiche Familie; gleiche Schädlinge | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Phytophthora-Risiko | severe | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Solanaceae | `shares_pest_risk` | Phytophthora, Verticillium, Weiße Fliege, Spinnmilbe | `shares_pest_risk` |

---

## 7. Ernte-Indikatoren

**Richtige Ernte-Indikatoren Andenbeere:**
- Papier-Huelse (Kelch) ist vollstaendig trocken und braun-papierartig (nicht mehr gruen)
- Frucht ist goldgelb-orange unter dem Kelch sichtbar (wenn Kelch geoeffnet wird)
- Frucht loeest sich leicht vom Stiel (faellt bei voller Reife von selbst ab)
- Aroma: sueß-sauer, ananaesartig; leicht bitterer Unterton beim Kauen der Schale
- Lagerhinweis: **In der intakten Kelchhüse sind die Fruechte 3–4 Monate haltbar** (bei kuehl und trocken). Kelch erst direkt vor dem Verzehr entfernen.
- Unreife Fruechte sind gruen und sauer — nicht essen (schwach toxisch)

---

## 8. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Andenbeere |
|-----|-------------------|-------------|------------------------------|
| Tomatillo | Physalis philadelphica | Selbe Gattung; groessere Frucht; gruen | Wichtig in mexikanischer Kueche (Salsa Verde); robuster; schneller reifend |
| Erdkirsche | Physalis pruinosa | Selbe Gattung; kleiner; sueß | Niedrig-wachsend; fuer Beet; zuckersuessen Geschmack; keine Kurztagpflanze |
| Lampionblume | Physalis alkekengi | Selbe Gattung; dekorativ | Ausdauernde Staude; orangefarbene Dekoration; nicht essbar (mild toxisch) |
| Paprikaschoten | Capsicum annuum | Solanaceae; Fruchtgemuese | Einfacher Anbau; breitere Sortenauswahl; Mehrfachernte |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Physalis peruviana,Andenbeere;Kapstachelbeere;Cape Gooseberry;Golden Berry,Solanaceae,Physalis,perennial,short_day,shrub,fibrous,8a–11b,0.0,Andenhochland Peru/Ecuador,yes,15–25,30,80–150,60–120,70–90,limited,yes,true,true,medium_feeder
```

### 9.2 Cultivar CSV-Zeilen

```csv
name,parent_species,days_to_maturity,traits,seed_type,notes
Golden Nugget,Physalis peruviana,120–150,compact;sweet;high_yield,open_pollinated,Kompakte Sorte; suesses Aroma; gut fuer Topfkultur
Giant,Physalis peruviana,140–160,large_fruit;very_sweet;vigorous,open_pollinated,Grosse Fruechte bis 15g; suesser Geschmack; kräftiger Wuchs
Colombia Yellow,Physalis peruviana,120–140,medium_size;tropical_aroma;productive,open_pollinated,Aus kolumbianischem Anbau; tropisches Fruchtaroma
Aunt Molly's Ground Cherry,Physalis pruinosa (nahverw.),90–110,small_fruit;very_sweet;early,open_pollinated,Nahverwandte Art; sueß-vanillig; frueher reifend; delikat
```

---

## Quellenverzeichnis

1. Wikipedia — Physalis peruviana (Cape Gooseberry) — https://en.wikipedia.org/wiki/Physalis_peruviana
2. CABI Compendium — Physalis peruviana Steckbrief — https://www.cabidigitallibrary.org/doi/abs/10.1079/cabicompendium.40713
3. Purdue University NewCrop — Cape Gooseberry — https://hort.purdue.edu/newcrop/morton/cape_gooseberry.html
4. Gardenia.net — Physalis peruviana Cape Gooseberry Grow Care Fruit Guide — https://www.gardenia.net/plant/physalis-peruviana-gooseberry
5. California Rare Fruit Growers (CRFG) — Cape Gooseberry — https://crfg.org/homepage/library/fruitfacts/cape-gooseberry/
6. GardenAndAllotment — Ultimate Guide to Cape Gooseberry — https://gardenandallotment.com/the-ultimate-guide-to-cape-gooseberry-benefits-nutrition-cultivation-and-uses/
7. Growables.org — Cape Gooseberry (Physalis peruviana) — https://www.growables.org/informationVeg/CapeGooseberry.htm
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
8. Fischer, G. & Melgarejo, L.M. (2020) — The ecophysiology of cape gooseberry (Physalis peruviana L.) — an Andean fruit crop. A review. Rev. Colomb. Cienc. Hortic. 14(1):76-89 — peer-reviewed; Basistemperatur (6.3°C Spross, 1.9°C Frucht), fakultative Kurztagspflanze (<12 h), Lichtkompensationspunkt 13.645 µmol/m²/s, Lichtsaettigung ~208 µmol/m²/s, Staunaesse-Intoleranz >4 d, moderate Salztoleranz, lichtbeduerftig — https://revistas.uptc.edu.co/index.php/ciencias_horticolas/article/view/10893
9. Salazar, M.R. et al. (2006/2008) — Base temperature and simulation model for nodes appearance in cape gooseberry (Physalis peruviana L.) — Tb 6.29°C fuer Knotenerscheinung (Wuchs-GDD-Basis) — https://www.researchgate.net/publication/256475132
10. Aguilar-Carpio, C. et al. (2018) — Analysis of growth and yield of cape gooseberry grown hydroponically under greenhouse conditions. Rev. Chapingo Ser. Hortic. 24(3):191-202 — Basistemperatur 6.3°C fuer Spross-Waermesummenberechnung — https://doi.org/10.5154/r.rchsh.2017.07.024
11. Heinze, W. & Midasch, M. (1991) — Photoperiodische Reaktion von Physalis peruviana L. Gartenbauwiss. 56(6):262-264 — Kurztagsverhalten; 8-h-Photoperiode beschleunigt Bluetinduktion ggue. 16 h — https://www.semanticscholar.org/paper/8b056ac9812a5dc65ff77404b9af92644c692e57
12. Aldana, F., Garcia, P.N. & Fischer, G. (2014) — Effect of waterlogging stress on the growth, development and symptomatology of cape gooseberry (Physalis peruviana L.) plants — Staunaesse-Intoleranz >4 d — https://doi.org/10.18257/raccefyn.114
13. Miranda, D. et al. (2010) / Salt-stress-Studien (z.B. Effect of Salt Stress on Growth and Metabolite Profiles, PMC8125371) — moderate Salztoleranz; 30 mM NaCl (~3 dS/m) wachstumsfoerdernd, Toleranz bis ~60 mM (~6 dS/m) — https://pmc.ncbi.nlm.nih.gov/articles/PMC8125371/
14. Hoagland-Standardnaehrloesung (Mikronaehrstoff-Endkonzentrationen Mn 0.5 / Zn 0.05 / Cu 0.02 / Mo 0.011 ppm) — Richtwert fuer Solanaceae-Fruchtgemuese — https://en.wikipedia.org/wiki/Hoagland_solution
15. en.jardineriaon.com — Cape gooseberry cultivation guide — effektive Durchwurzelungstiefe >60 cm, Boden-pH 5.5–6.8, Vollsonne — https://en.jardineriaon.com/physalis-peruviana.html
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
16. PFAF (Plants For A Future) — Physalis peruviana — "a PERENNIAL ... usually grown as an annual" in UK-Klima; "in flower from July to October"; "seeds ripen from August to November"; frost tender, USDA 10-12 — https://pfaf.org/user/plant.aspx?LatinName=Physalis+peruviana
17. Lubera.com — Physalis pflanzen: Tipps fuer Anbau, Pflege und Ernte — Bluetezeit "Juni - September"; Erntereife "etwa acht bis neun Wochen nach der Bluetenbildung", "fruehestens Ende August"; mehrjaehrige Kuebelkultur moeglich, im Beet nicht winterhart — https://www.lubera.com/de/gartenbuch/physalis-pflanzen-p2879
18. samen.de — Physalis-Pflege: Von Aussaat bis Ernte — Erntezeit "August bis September", "zieht sich bis in den Oktober hinein"; Aussaat Mitte Februar bis Ende Maerz — https://samen.de/blog/die-richtige-pflege-fuer-physalis-pflanzen-von-anbau-bis-ernte.html
19. beetfreunde.de — Physalis anbauen, pflegen und ernten — "von August bis zum Frost ernten"; nicht frosthart, Auspflanzung erst nach den Eisheiligen — https://www.beetfreunde.de/physalis/
<!-- /Quelle: growing-phase-auditor 2026-07 -->
