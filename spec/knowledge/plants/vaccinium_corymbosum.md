# Kulturheidelbeere — Vaccinium corymbosum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-für-dich.de Vaccinium, Bruns Pflanzen Vaccinium, Baumschule Horstmann Bluecrop, Bellaflora Vaccinium

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Vaccinium corymbosum | `species.scientific_name` |
| Volksnamen (DE/EN) | Kulturheidelbeere, Amerikanische Heidelbeere, Strauchheidelbeere; Highbush Blueberry | `species.common_names` |
| Familie | Ericaceae | `species.family` → `botanical_families.name` |
| Gattung | Vaccinium | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (ausdauernd, blüht wiederholt über mehrere Jahre) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–7b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −20 °C; Blüten können durch Spätfröste geschädigt werden; in Norddeutschland problemlos | `species.hardiness_detail` |
| Heimat | Nordamerika (östliche USA, Kanada) | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 7 (Phänologie-/Wuchs-Basis; nicht Keim-Basistemperatur) | `species.base_temp` |
| Lebensdauer (Jahre) | 20–30 (Northern Highbush meist 15–25; Vollertrag ab Jahr 5–7) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich | true (Endodormanz-Bruch durch Chilling, keine echte Vernalisation) | `lifecycle_configs.vernalization_required` |
| Chilling-Mindestbedarf (Tage) | 33–42 (= 800–1000 h < 7 °C bei Northern Highbush; Bluecrop hochchillig) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurz-/Langtag-Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
| Bestäuber erforderlich | false (selbstfruchtbar/self-compatible) | `species.requires_pollinator` |
| Pomologische Befruchtungsgruppe | <!-- leer: selbstfruchtbar, keine pomologische Kreuzbefruchtungsgruppe --> | `species.pollinator_group` |
| Empfohlene Befruchter-Sorten | ["Bluegold","Spartan"] (Fremdbestäubung mit anderer Sorte steigert Fruchtansatz/-größe um ~10–20 %) | `species.compatible_pollinators` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Pflanzung als Strauch) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (je nach Sorte, Frühsorten ab Juli) | `species.harvest_months` |
| Blütemonate | 4, 5 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning (ab 3. Jahr Auslichtungsschnitt; alte Triebe bodennah entfernen) | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (Spezialsubstrat nötig) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 100–150 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Kübel) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf/Beet) | Saures Spezialsubstrat (Rhododendronerde) oder Hochmoor-Substrat; pH 4,0–5,5; NUR kalkarmes Wasser/Regenwasser! Kein Kalk! | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP belegt; Lichtsättigung liegt bei 400–500 µmol/m²/s (nicht in dieses Feld eintragen) --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade (Vollsonne bevorzugt für Ertrag; bis ~50 % Schatten tolerierbar, Ertrag sinkt) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–40 (flach; Hauptwurzelmasse in oberen 30 cm, vereinzelt bis 60) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-a-Wert publiziert; Praxis-Obergrenze Substrat-/Gießwasser-EC ~1.0 dS/m (UGA) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-b-Wert publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 4.5–5.5 (Substrat-Ansäuerung praxisüblich ab 4.0; vgl. §1.6/§2.3) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Dauerkulturen-Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | high |
| Blüte | 21–35 | 2 | false | false | low (Spätfrost-Risiko!) |
| Fruchtentwicklung | 42–70 | 3 | false | false | medium |
| Fruchtreife & Ernte | 28–56 | 4 | false | true | high |
| Herbst / Einzug | 42–60 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte & Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (Halbschatten toleriert) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (kritischer stomatärer Kollaps; oberhalb des Zielkorridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium (Assimilation sinkt deutlich mit steigendem Blatt-VPD) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 (Netto-CO₂-Assimilation fällt von 20 → 30 °C deutlich ab) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-Vollsonne/offenes Tageslicht; im Halbschatten höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH (Substrat) | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|---------------|----------|----------|---------|----------|----------|----------|----------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
| Austrieb | 2:1:1 | 0.6–1.0 | 4.0–5.5 | 30 | 30 | — | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.05<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.02<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.005<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Fruchtentwicklung | 2:1:2 | 0.8–1.2 | 4.0–5.5 | 40 | 40 | — | 3 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.6<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.06<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.03<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.004<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Fruchtreife | 1:1:2 | 0.6–0.9 | 4.0–5.5 | 30 | 30 | — | 2 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.4<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.04<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.02<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.003<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> Mikronährstoff-Werte als Düngelösungs-Zielkonzentration (mg/L ≈ ppm), angelehnt an eine Ericaceen-/Blaubeer-Nährlösung und die modifizierte Hoagland-Standardlösung; Mn/Zn/Cu/Mo phasenadaptiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch/Sauer-Dünger (PFLICHT — kein pH-erhöhender Dünger!)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Rhododendron-/Heidelbeerdünger | Compo | organisch-sauer | nach Herstellerangabe | März und Juni |
| Nadelstreu-Mulch | — | organisch | 5–8 cm | Frühjahr |
| Schwefel (zur pH-Senkung) | diverse | supplement | 20–30 g/m² | Frühjahr (wenn pH zu hoch) |

#### Mineralisch (nur sauere Produkte!)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Blaubeer-Dünger | Oscorna | base | 5-2-6+Fe+S | nach Angabe | Frühjahr bis Sommer |

### 3.2 Besondere Hinweise zur Düngung

**Kritisch:** NUR kalkarmes Wasser verwenden — Leitungswasser erhöht den pH und schadet der Pflanze dauerhaft. Regenwasser ideal. Keine Düngung mit Kalk oder kalkhaltigen Produkten. pH-Kontrolle regelmäßig (mindestens 1× pro Jahr). Bei pH > 5,5: Mit Schwefel oder Rhododendronerde-Zuschlag korrigieren. Heidelbeeren können Mykorrhiza-Pilze bilden — diese nicht durch Fungizide schädigen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | NUR kalkarmes Wasser (pH <6.0); Regenwasser ideal; Leitungswasser kann Pflanze langfristig schädigen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 (Kübel) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Schnitt | Ab 3. Jahr: 1–2 älteste Triebe bodennah entfernen | hoch |
| Apr | Spätfrost-Schutz | Blüten bei Frost mit Vlies abdecken | hoch |
| Apr | pH prüfen | pH-Wert messen; bei Bedarf korrigieren | hoch |
| Apr–Mai | Düngung | Blaubeer-/Rhododendron-Dünger ausbringen | hoch |
| Apr–Mai | Mulchen | Nadelstreu oder Rindenmulch 5–8 cm | mittel |
| Jun | 2. Düngung | Letzter Dünger vor der Ernte | mittel |
| Jul–Sep | Ernte | Täglich reifen Früchte ernten (tiefblau, lösen sich leicht) | hoch |
| Okt–Nov | Wintervorbereitung | Im Kübel: frostfrei stellen oder einpacken | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy (im Beet); needs_protection (im Kübel) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (Beet); fleece oder move_indoors (Kübel) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | −5 (Kübel) | `overwintering_profiles.winter_quarter_temp_min` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Vögel | div. | Fressen Früchte | fruit | ripening | easy |
| Gallmilbe | Eriophyes spp. | Aufgetriebene Knospen (Big Bud) | leaf, bud | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißlicher Belag | Trockene Wärme | 5–10 | vegetative |
| Chlorose (Eisenmangel) | physiologisch | Gelbliche Blätter (Eisenmangel durch falschen pH) | pH zu hoch | — | all |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schutznetz | cultural | — | Feinmaschiges Vogelnetz | 0 | Vögel |
| Eisenchelat-Dünger | chemical | Fe-EDDHA (stabil bei pH 4,0–9,0; Fe-EDTA bei pH <6 instabil) | Flüssig gießen | 0 | Chlorose (Eisenmangel) |
| pH senken | cultural | Schwefel | 20–30 g/m²; einarbeiten | 0 | Chlorose (pH-Ursache) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.5 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilben (Tetranychus urticae) | 2–6 Tiere/m² (kurativ bis 20/m²) | 2–4 Wochen |
| Raubmilbe | Neoseiulus (Amblyseius) californicus | Spinn-/Gallmilben (präventiv, hitzetolerant) | 25–50 Tiere/m² | 3–5 Wochen |
| Raubmilbe | Amblyseius andersoni | Spinn-/Eriophyiden-/Gallmilben (breit, weiter Temp-Bereich) | 50–100 Tiere/m² | 3–6 Wochen |
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphididae) | 0.5–2 Tiere/m² | 2–4 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphididae) | 1–4 Larven/m² | 2–3 Wochen |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rhododendron | Rhododendron spp. | 0.9 | Gleiche Bodenansprüche (sauer); optisch schön | `compatible_with` |
| Blaubeere (andere Sorten) | Vaccinium corymbosum | 0.9 | Kreuzbestäubung verbessert Erntemengen erheblich! | `compatible_with` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Hinweis (Freitext, NICHT ins KA-Feld compatible_pollinators): Wichtigste bestäubende Insekten sind Hummeln (Bombus spp.) und Wildbienen; sie sind durch Buzz-Pollination effektiver als Honigbienen. Eine zweite Sorte als Pollenspender erhöht Fruchtansatz und Beerengröße. -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kiefer / Nadelgehölze | div. | 0.7 | Nadelstreu hält pH sauer | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Alle kalkliebenden Pflanzen | div. | pH-Konflikt; Konkurrenz | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Kulturheidelbeere |
|-----|-------------------|-------------|--------------------------------------|
| Niedrige Heidelbeere | Vaccinium angustifolium | Gleiche Gattung | Kompakter; für Container |
| Moosbeere | Vaccinium oxycoccos | Gleiche Gattung | Winterhart; Moorbeete |
| Johannisbeere | Ribes nigrum | Ähnliche Funktion | Weniger pH-anspruchsvoll |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months
Vaccinium corymbosum,"Kulturheidelbeere;Amerikanische Heidelbeere;Highbush Blueberry",Ericaceae,Vaccinium,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b",-0.1,"Nordamerika",yes,40,40,200,150,125,no,limited,false,false,light_feeder,hardy,"7;8;9"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type,years_to_first_harvest
Bluecrop,Vaccinium corymbosum,USDA,1952,"classic;high_yield;mid_season",–,,open_pollinated,3
Bluegold,Vaccinium corymbosum,USDA,1989,"compact;late_season;good_flavor",–,,open_pollinated,3
Spartan,Vaccinium corymbosum,USDA,1978,"large_fruit;early;excellent_flavor",–,,open_pollinated,3
```

---

## Quellenverzeichnis

1. [Pflanzen-für-dich.de Vaccinium corymbosum](https://pflanzen-fuer-dich.de/Vaccinium-corymbosum) — Pflegedaten
2. [Bruns Pflanzen Vaccinium corymbosum](https://www.bruns.de/2015/08/01/vaccinium-corymbosum-garten-heidelbeere-amerikanische-kulturheidelbeere/) — Sortenwahl
3. [Baumschule Horstmann Heidelbeere Bluecrop](https://www.baumschule-horstmann.de/shop/exec/product/57/2452/Heidelbeere-Bluecrop.html) — Anbauhinweise
4. [Bellaflora Vaccinium corymbosum](https://www.bellaflora.at/pflanzen/gartenpflanzen/beerenstraeucher/heidelbeeren/vaccinium-corymbosum) — Pflegetipps
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [ASHS HortScience 47(9): Predicting Flower Phenology of Highbush Blueberry](https://journals.ashs.org/hortsci/view/journals/hortsci/47/9/article-p1291.xml) — GDD-Basistemperatur (~7 °C), Bloom-Phänologie
6. [Leaftide — Chill Hours for Blueberries (Variety Guide)](https://leaftide.com/learn/chill-hours-for-blueberries/) — Chilling-Bedarf Northern/Southern Highbush
7. [Oklahoma State Extension — Blueberry Production for the Home Garden](https://extension.okstate.edu/fact-sheets/blueberry-production-for-the-home-garden) — Chilling 400–800 h, Standort
8. [PMC5972668 — Photosynthetic limitation in highbush blueberries (J. Exp. Bot.)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5972668/) — Lichtsättigung 400–500 µmol/m²/s, T-Optimum
9. [Gardener's Path — Grow Highbush Blueberries](https://gardenerspath.com/plants/fruit/grow-highbush-blueberries/) — Vollsonne/Halbschatten, flaches Wurzelsystem
10. [UMD Extension — Growing Blueberries in a Home Garden](https://extension.umd.edu/resource/growing-blueberries-home-garden) — Standort, Wurzeltiefe, Schattentoleranz
11. [UGA CAES — Blueberry Irrigation Water Quality](https://fieldreport.caes.uga.edu/publications/C1105/blueberry-irrigation-water-quality/) — Salzempfindlichkeit (EC-Obergrenze ~1.0 dS/m)
12. [FAO — Salt tolerance of crops (Annex 1)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Maas-Hoffman-Methodik (kein Blaubeer-Wert gelistet)
13. [PNW Pest Management Handbooks — Blueberry incorrect soil pH](https://pnwhandbooks.org/plantdisease/host-disease/blueberry-vaccinium-corymbosum-incorrect-soil-ph) — pH-Optimum 4.5–5.5
14. [Patent CN102101803A — Water culture nutrient solution of blueberry](https://patents.google.com/patent/CN102101803A/en) — Mikronährstoff-Lösung Mn/Zn/Cu/Mo (mg/L)
15. [USDA-ARS — Modified Hoagland's Standard Nutrient Recipe](https://www.ars.usda.gov/ARSUserFiles/50820500/gprg/control.pdf) — Mikronährstoff-Standardkonzentrationen
16. [Koppert — Blueberry pests, diseases & biological control](https://www.koppertus.com/crops/fruits/blueberry/) — Nützling-Wirt-Zuordnung
17. [Sound Horticulture — Amblyseius andersoni](https://soundhorticulture.com/blogs/news/andersoni) — Raubmilbe gegen Spinn-/Gallmilben
18. [Bee Health Extension — Pollinating Highbush Blueberries](https://bee-health.extension.org/pollinating-highbush-blueberries/) — Selbstfruchtbarkeit, Hummel-/Wildbienen-Bestäubung
19. [MSU Extension — Invest in pollination for highbush blueberries](https://www.canr.msu.edu/news/invest_in_pollination_for_success_with_highbush_blueberries) — Cross-Pollination-Ertragsvorteil
20. [Biology Insights — How Long Do Blueberry Bushes Live?](https://biologyinsights.com/how-long-do-blueberry-bushes-live/) — Lebensdauer 20–30 Jahre
21. [GPN — The R to FR Ratio](https://gpnmag.com/article/r-fr-ratio/) — R:FR / Far-Red-Fraktion Vollsonne vs. Schatten
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
