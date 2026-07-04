# Rosmarin — Salvia rosmarinus (syn. Rosmarinus officinalis)

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Rosmarin, NaturaDB Rosmarinus officinalis, Samen.de mediterrane Kräuter, Plantura winterharte Kräuter

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Salvia rosmarinus (Syn. Rosmarinus officinalis) | `species.scientific_name` |
| Volksnamen (DE/EN) | Rosmarin, Echter Rosmarin; Rosemary | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Salvia | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 7a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Standard-Rosmarin winterhart bis −10 °C; Sorte 'Arp' bis −20 °C; in Norddeutschland ohne Schutz nur in geschützten Lagen; Vliesschutz empfohlen | `species.hardiness_detail` |
| Heimat | Mittelmeerraum (Südeuropa, Nordafrika) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 (mediterraner Hartlaubstrauch; weder C4 noch CAM) | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> kein art-spezifischer Wuchs-/Phänologie-Basiswert aus zwei unabhängigen seriösen Quellen belegbar; Keim-/Optimumwerte nicht als Wuchs-GDD-Basis übernommen | `species.base_temp` |
| Lebensdauer (Jahre) | 10–20 (unter idealen Bedingungen bis 30+) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false (immergrün; keine echte Endodormanz, nur kältebedingte Wachstumsruhe) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (keine Kältepflicht zur Blühinduktion) | `lifecycle_configs.vernalization_required` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> nicht zutreffend — tagneutrale Blüte (siehe `photoperiod_type` = day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat Februar/März, schwierig) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (kaum üblich — Kauf als Jungpflanze empfohlen) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 | `species.direct_sow_months` |
| Erntemonate | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 (ganzjährig) | `species.harvest_months` |
| Blütemonate | 4, 5, 6 (manchmal auch Herbst) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed (aufwändig) | `species.propagation_methods` |
| Schwierigkeit | easy (Stecklinge), difficult (Aussaat) | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (ätherische Öle in großen Mengen) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (in großen Mengen) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (kulinarische Mengen unbedenklich) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile; besonders ätherische Öle | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Campher, 1,8-Cineol, Borneol | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (nach der Blüte; nie ins alte Holz) | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–60 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr viel Licht nötig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr durchlässig; Kräutererde mit 30% Perlite/Kies; pH 6,0–7,5; NIEMALS Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein art-spezifischer LCP-Wert aus zwei unabhängigen seriösen Quellen belegbar (Rosmarin ist Heliophyt mit hohem LCP, aber konkrete µmol-Werte nicht zuverlässig auffindbar) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> siehe oben | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun (RHS/PFAF: voller Sonnenstand, „cannot grow in the shade") | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive (Staunässe = Haupttodesursache, Wurzelfäule) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant (Maas 1990) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 6 (Maas-Hoffman a, bezogen auf Substrat-ECe — NICHT Gießwasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-b-Wert auffindbar | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 (schwach sauer bis schwach alkalisch, kalktolerant) | `species.soil_ph_preference` |

Freitext-Hinweis (gehört NICHT in die KA-Felder oben): Die Netto-Photosynthese sättigt erst bei sehr hohem PPFD (~800–1000 µmol/m²/s); oberhalb von ~33–34 °C Blatttemperatur fällt sie auf unter die Hälfte des Maximums (Photoinhibition/Hitzestress). Salztoleranz-Klasse und ECe-Schwelle stammen aus der Maas-Hoffman-Klassifikation (Maas 1990: „moderately tolerant", 6–8 dS/m); cultivar-abhängige Unterschiede sind dokumentiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzeln (Neupflanzung) | 21–42 | 1 | false | false | low |
| Aktives Wachstum (Apr–Sep) | 180–210 | 2 | false | true | high |
| Blüte | 21–42 | 3 | false | true | high |
| Winterruhe (Okt–Mär) | 150–180 | 4 | false | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (Volllsonne!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–60 (trockene Luft bevorzugt) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.2 (deutlich oberhalb des Zielkorridors; kritischer Punkt stomatären Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (mediterrane Trockenstress-Anpassung, gute Stomata-Regulation) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-Vollsonne; R:FR ≈ 1.1–1.3) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (zwischen den Wassergaben gut abtrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 5–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 0–8 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (oberhalb des Winter-Zielkorridors; niedrigere Schwelle als in der Wuchsphase) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 10–18 (reduzierte Aktivität in der Kühlruhe) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Winterquartier hell; bei reiner LED-Beleuchtung spektrumabhängig) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Einwurzeln | 1:2:1 | 0.6–0.8 | 6.0–7.5 | 60 | 30 | — | 1 | 0.5 | 0.05 | 0.02 | 0.01 |
| Aktives Wachstum | 1:1:1 | 0.8–1.2 | 6.0–7.5 | 80 | 40 | — | 1 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
Mikronährstoffwerte (Mn/Zn/Cu/Mo) folgen der etablierten Hoagland-Vollnährlösung (Hoagland & Arnon 1933/1950: Mn 0.5 ppm, Zn 0.05 ppm, Cu 0.02 ppm, Mo 0.01 ppm) als allgemeiner Pflanzen-Referenz; art-spezifische Rosmarin-Optima sind nicht belegt. Als Leichtzehrer (`nutrient_demand_level` = light_feeder) eher am unteren Rand dosieren. KA-Felder: `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm`, `nutrient_profiles.molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (sehr sparsam)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kräuter-Langzeitdünger | Compo | base | 14-7-14 | 1 g/L Substrat (1× im Frühjahr!) | Austrieb |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost (sehr wenig) | eigen | organisch | 0.5 L/Pflanze | Frühjahr |
| Kaffeesatz (pH-Puffer) | — | organisch | Dünn um Pflanze | Sommer |

### 3.2 Besondere Hinweise zur Düngung

Rosmarin ist äußerst sparsam zu düngen — überdüngter Rosmarin verliert Aromastoffe und wird weich und anfällig. Magerer Boden fördert den Ätherisch-Öl-Gehalt. Im Topf reicht eine Düngegabe pro Jahr im Frühjahr. Staunässe ist die Haupttodesursache — niemals Überdüngung mit stickstoffbetonten Düngern.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser geeignet; Rosmarin toleriert Kalk gut (Mittelmeer-Kalkstein-Standort); zwischen den Gaben vollständig abtrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Überwinternde Pflanzen kontrollieren | Tote Äste entfernen; nicht zu früh rausstellen | mittel |
| Apr | Rückschnitt nach Blüte | Eintriebslanges Zurückschneiden; nie ins alte Holz | hoch |
| Apr | Frühjahrsdüngung | Einmalig Langzeitdünger | mittel |
| Mai | Auspflanzen (Topf) | Nach Eisheiligen ins Freie; sonnigster Standort | hoch |
| Jun–Sep | Ernte | Regelmäßig junge Triebe ernten; fördert Verzweigung | mittel |
| Okt | Winterschutz vorbereiten | Vlies, in Norddeutschland reinbringen oder schützen | hoch |
| Nov–Mär | Überwinterung | Kühl und hell (5–15 °C); kaum gießen; kein Heizungsstandort | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | fleece (oder move_indoors in Zone 7b) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors, prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4, 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 2 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Gelbpunkte (bei Trockenheit) | leaf | all (besonders Winter) | medium |
| Rosmarinblattlaus | Dysaphis foeniculus | Kolonien, Kräuselung | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Phytophthora, Pythium) | Welke trotz feuchtem Boden; braune Wurzeln | Staunässe | 5–14 | all |
| Echter Mehltau | fungal | Weißer Belag | Feucht-warme Bedingungen | 7–14 | vegetative |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Drainage verbessern | cultural | — | Substrat mit Kies/Perlite mischen | 0 | Wurzelfäule |
| Neemöl | biological | Azadirachtin | Sprühen, 0.5% | 3 | Spinnmilbe, Blattläuse |
| Schmierseife | biological | Kaliumoleat | Sprühen, 1% | 1 | Blattläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.5 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit | Hinweis |
|----------|----------------|-----------------|------------------|---------|
| Raubmilbe *Phytoseiulus persimilis* | Gemeine Spinnmilbe (*Tetranychus urticae*) | 2–20 Tiere/m² (kurativ, je nach Befall; ggf. 1–2× wöchentlich wiederholen) | 2–3 Wochen | Kurativer Einsatz bei vorhandenem Befall; bevorzugt höhere Luftfeuchte |
| Schlupfwespe *Aphidius colemani* | Blattläuse (u. a. *Dysaphis foeniculus*) | 0.5–3 Tiere/m² (vorbeugend bis kurativ) | 2–3 Wochen | Bildet Mumien; mehrere Freilassungen im Abstand von 1–2 Wochen |
| Gallmücke *Aphidoletes aphidimyza* | Blattläuse | 1–5 Larven/m² | 2–3 Wochen | Larven fressen Blattläuse; benötigt Nachtdunkelheit zur Eiablage |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Lippenblütengewächse (Lamiaceae) |
| Empfohlene Vorfrucht | — (Dauerpflanze) |
| Empfohlene Nachfrucht | — (Dauerpflanze) |
| Anbaupause (Jahre) | keine (Dauerpflanze) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Lavendel | Lavandula angustifolia | 0.9 | Gleiche Standortansprüche, optisch schön | `compatible_with` |
| Thymian | Thymus vulgaris | 0.9 | Gleiche Standortansprüche | `compatible_with` |
| Salbei | Salvia officinalis | 0.8 | Gleiche Familie, gut kombinierbar | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Rosmarin-Duft schützt vor Schädlingen | `compatible_with` |
| Bohne | Phaseolus vulgaris | 0.8 | Gegenseitige Förderung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Rosmarin zu dominant; trockener Standort vs. Feucht | mild | `incompatible_with` |
| Minze | Mentha spicata | Minze breitet sich aus, hemmt Rosmarin | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Rosmarin |
|-----|-------------------|-------------|---------------------------|
| Thymian | Thymus vulgaris | Mediterran, gleiche Familie | Winterhärter bis −20 °C; kompakter |
| Salbei | Salvia officinalis | Gleiche Familie, mediterran | Robuster in Norddeutschland |
| Lavendel | Lavandula angustifolia | Gleicher Standort | Spektakulärere Blüte |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Salvia rosmarinus,"Rosmarin;Echter Rosmarin;Rosemary",Lamiaceae,Salvia,perennial,day_neutral,shrub,fibrous,"7a;7b;8a;8b;9a;9b;10a;10b",0.2,"Mittelmeerraum",yes,10,20,150,100,50,limited,yes,false,false,light_feeder,half_hardy,"3;4;5","1;2;3;4;5;6;7;8;9;10;11;12"
```

---

## Quellenverzeichnis

1. [Winterharte Kräuter — Plantura](https://www.plantura.garden/kraeuter/kraeuter-anbauen/winterharte-kraeuter) — Winterhärte-Übersicht
2. [NaturaDB Rosmarinus officinalis](https://www.naturadb.de/pflanzen/rosmarinus-officinalis/) — Stammdaten
3. [Mediterrane Kräuter — Samen.de](https://samen.de/blog/mediterrane-kraeuter-im-garten-erfolgreich-anbauen-und-pflegen.html) — Anbaupraxis
4. [Voigt Pflanzenhof Rosmarinus](https://www.voigt-pflanzenhof.de/artikel/848/rosmarinus-officinalis) — Pflegehinweise
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [PFAF — Rosmarinus officinalis](https://pfaf.org/user/plant.aspx?latinname=Rosmarinus+officinalis) — Boden-pH, Sonnenstand (full sun, „cannot grow in the shade"), Salzspray-/Maritimtoleranz, Drainage
6. [HortGuide — Rosmarinus officinalis Plant Profile](https://hortguide.com/library/plants/rosmarinus-officinalis/) — Mindest-Wurzeltiefe (14 inch ≈ 35 cm), Staunässe-Intoleranz, Salz-/Trockentoleranz
7. [WateReuse — Salinity Management Guide: salt-tolerant plants](https://watereuse.org/salinity-management/cp/cp_7.html) — Salztoleranz-Einstufung Rosmarin
8. [USDA-ARS — Plant Salt Tolerance (Maas-Klassifikation)](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — Maas (1990): Rosmarin „moderately tolerant", ECe 6–8 dS/m
9. [Photosynthetica — Adaptive photosynthetic strategies of Mediterranean maquis species](http://ps.ueb.cas.cz/artkey/phs-200404-0012_adaptive-photosynthetic-strategies-of-the-mediterranean-maquis-species-according-to-their-origin.php) — Nettophotosynthese ~7.8 µmol CO₂/m²/s, Hitze-Photoinhibition >33.6 °C, T-Optimum mediterraner Arten
10. [MSU Extension — A Closer Look at Far-Red Radiation](https://www.canr.msu.edu/uploads/resources/pdfs/fr-radiation.pdf) — R:FR-Verhältnis Vollsonne vs. Schatten (Far-Red-Fraction-Anker)
11. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Referenzkonzentrationen (Mn/Zn/Cu/Mo ppm)
12. [Koppert — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate und Etablierungszeit Spinnmilben-Raubmilbe
13. [Whyfarmit — Rosemary Plants Average Lifespan](https://whyfarmit.com/rosemary-plants-lifespan/) — Lebensdauer Rosmarin (10–20, bis 30+ Jahre)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
