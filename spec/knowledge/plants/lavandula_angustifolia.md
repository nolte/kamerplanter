# Lavendel — Lavandula angustifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Pflanzen-für-dich.de Lavandula, NaturaDB Lavandula angustifolia, Plantura Lavendel, Baumschule Horstmann

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lavandula angustifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Echter Lavendel, Schmalblättriger Lavendel; English Lavender, True Lavender | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Lavandula | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | subshrub <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher shrub) --> | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- korrigiert von day_neutral: L. angustifolia ist fakultative Langtag-Pflanze (facultative long-day plant), Blüteförderung durch Tageslängen > ~12 h; belegt GPNmag/MSU Extension/PanAmSeed --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis −15 °C; in Norddeutschland problemlos; bei anhaltend nasser Kälte empfindlich (Staunässe tötet mehr als Frost) | `species.hardiness_detail` |
| Heimat | Westliches Mittelmeer (Frankreich, Spanien, Nordafrika) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert auffindbar; verfügbare 0–2.1 °C stammen aus Forcing-/Vernalisationsstudien (Keim-/Blühforcing, NICHT Wuchs-GDD) und werden bewusst nicht umetikettiert --> | `species.base_temp` |
| Lebensdauer (Jahre) | 10–15 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization) | true | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 56–70 (ca. 8–10 Wochen bei ~5 °C) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 12 | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 12–16 (Aussaat schwierig; Kauf als Jungpflanze empfohlen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (Blüten für Duftsäcke, Kochen, Tee) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy (Stecklinge); difficult (Aussaat) | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (ätherische Öle, besonders Lavendelöl) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (in größeren Mengen) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (geringe Mengen harmlos) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Teile, insbesondere ätherisches Öl | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Linalool, Linalylacetat | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (um 2/3; nie ins alte Holz; sonst verholzt und wird kahl) | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4, 8 (nach der Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–60 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr lichthungrig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kalkhaltig, durchlässig, mager (30% Kies/Splitt); pH 6,5–8,0; KEIN Torf | — |

### 1.7 Umgebungs-Physiologie & Standortqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein belastbarer LCP-PPFD-Wert aus 2 unabhängigen Quellen; veröffentlichte Modell-Fit-Werte (~0.01–0.03 µmol) sind physiologisch unplausibel/Fit-Artefakt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: kein belegter cm-Bereich; Quellen beschreiben tiefe Pfahlwurzel (taproot) qualitativ, ohne Zahlenangabe --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: Studien nur mit NaCl-Lösungen (50/100 mM), kein Maas-Hoffman-ECe-Schwellenwert publiziert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.5–7.5 (neutral bis leicht alkalisch; harmoniert mit §1.6/§2.3) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: seed-profile-backfill 2026-07 (Batch 7) -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 18 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 24 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer — nur andrücken, max. 0,3 cm falls überhaupt bedeckt) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14 (unterer Wert der artüblichen 14–60 Tage nach Stratifikation; einzelne Sorten wie 'Munstead' können ohne Stratifikation bereits in 3–7 Tagen keimen, siehe Hinweis) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 5 | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | cold_stratification (für gleichmäßige/zuverlässige Keimung empfohlen, für einzelne Sorten wie 'Munstead' nicht zwingend erforderlich) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 1.1 (ca. 900–1.000 Samen/g je nach Quelle/Sorte, entspricht ~1,0–1,1 g/1.000 Korn) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Lavendel wird kommerziell überwiegend über Stecklinge/Jungpflanzen kultiviert, keine belastbare Reihen-Direktsaat-Dichte (Korn/m²) aus den geprüften Quellen --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Cold Stratification ist nicht bei allen Sorten zwingend — 'Munstead' und einige weitere englische Sorten keimen auch ohne Kältebehandlung, wenn auch etwas langsamer und unregelmäßiger als mit Stratifikation.

Quellen (§1.8):
1. [Bloom Outlet — Lavandula angustifolia (English Lavender) Seed Guide](https://bloomoutlet.com/lavandula-angustifolia-english-lavender-seed-guide/) — Keimtemperatur, Stratifikation
2. [Twin Flame Lavender Farm — Comprehensive Guide for Successfully Germinating Lavender from Seed](https://twinflamelavender.farm/3-hacks-4-myths-busted-comprehensive-guide-for-successfully-germinating-lavender-from-seed-in-7-days/) — Keimdauer, sortenabhängige Stratifikationsanforderung, Lichtkeimer
3. [Gardenia.net — How to Grow Lavender from Seeds](https://www.gardenia.net/guide/how-to-grow-lavender-from-seeds-fragrant-flowers-made-simple) — Saattiefe/Lichtkeimer, Keimtemperatur
4. [Urban Farmer — English Lavender Seeds](https://www.ufseeds.com/product/english-lavender-seeds/LAEN.html) — Saatgutzähldichte (Samen/Gramm)
5. [Gardeners Basics — Flower Seed Viability Chart](https://www.gardenersbasics.com/tools/blog/flower-seed-viability-chart-for-gardeners) — Keimfähigkeitsdauer bis 5 Jahre

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Saisonaler Zyklus)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 90–120 | 1 | false | false | high |
| Frühjahrswachstum | 60–90 | 2 | false | false | medium |
| Blüte | 42–70 | 3 | false | true | high |
| Nachblüte / Herbst | 60–90 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum & Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (Volllsonne; 6–8h täglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–55 (trockene Luft bevorzugt) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 2.3 | `requirement_profiles.vpd_threshold_kpa` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- kritischer Punkt deutlich oberhalb des Zielkorridors (Oberkante 2.0 + ~0.3); mediterran/trockenheitstolerant --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- trockenheitstolerante mediterrane Art --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Optimaltemperatur Wuchs 15–30 °C; Netto-PS-Optimum als Spanne --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Vollsonnen-Standort (full_sun): offenes Tageslicht ≈ 0.5 (R:FR ≈ 1.1) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 (sehr trockenverträglich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
| Wachstum | 1:1:1 | 0.6–0.9 | 6.5–8.0 | 80 | 40 | — | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | 0:1:1 | 0.5–0.8 | 6.5–8.0 | 60 | 30 | — | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Spalten Mn/Zn/Cu/Mo ergänzt; keine art-spezifischen ppm-Werte aus 2 unabhängigen Quellen belegbar für L. angustifolia (Schwachzehrer/light_feeder) → DATEN FEHLEN statt generischer Halluzinationswerte --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (sehr sparsam)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Reife Kompost (sehr wenig) | eigen | organisch | 0.3 L/Pflanze | 1× Frühjahr |

#### Mineralisch (bei Bedarf, 1× jährlich)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kräuter-Langzeitdünger | Compo | base | 6-4-8 | 5 g/Pflanze | Frühjahr |

### 3.2 Besondere Hinweise zur Düngung

Lavendel braucht kaum Dünger — auf sehr mageren, kalkreichen Böden ist er am wohlsten und duftet am intensivsten. Überdüngung (N) führt zu üppigem, weichem Wachstum mit wenig Aroma. Bei Topfkultur 1× jährlich im Frühjahr düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 12 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Hartes (kalkhaltiges) Wasser ist kein Problem; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 180 (kaum düngen!) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Rückschnitt | Um 2/3 kürzen (grünes Holz); nicht ins altes Holz schneiden | hoch |
| Mai | Auspflanzen (Neupflanzungen) | Sehr durchlässigen Boden vorbereiten | mittel |
| Jun–Aug | Ernte | Blüten vor dem vollständigen Aufblühen schneiden (höchster Öl-Gehalt) | mittel |
| Aug | Rückschnitt nach Blüte | Verblühte Blütenstände und Triebspitzen kürzen | mittel |
| Nov | Wintervorbereitung | Topfpflanzen: frostfrei stellen; im Beet: gut drainiert | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (im Beet bei guter Drainage); Kübel: kühles Frostschutzhaus | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3, 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Zikadenart | Auchenorrhyncha | Gelbe Punkte, Blattverformung (selten) | leaf | vegetative | difficult |
| Blattläuse | div. Aphiidae | Kolonien (selten; Lavendelduft schützt) | leaf | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Phytophthora, Pythium) | Welke, braune Wurzeln | Staunässe, schwerer Boden | 5–14 | all |
| Echter Mehltau | fungal | Weißlicher Belag | Feuchtigkeit | 7–14 | vegetative |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Drainage optimieren | cultural | — | Kies/Split unter Pflanzung | 0 | Wurzelfäule |
| Standortwahl | cultural | — | Vollsonne, trockener Hang | 0 | alle Krankheiten |

### 5.5 Nützlinge (Biologische Bekämpfung)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Sektionsnummer 5.5 vergeben: 5.3 ist im Dokument frei, 5.4 ist bereits Behandlungsmethoden; gewählt wurde 5.5 zur eindeutigen Vermeidung jeder Kollision -->

| Nützling | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|----------------|------------------|------------------|
| Aphidoletes aphidimyza (Gallmücke) | Blattläuse (Aphididae) | ca. 1–3 Larven/m² | 2–3 Wochen |
| Aphidius colemani (Schlupfwespe) | Blattläuse (Aphididae) | ca. 0.5–1 Tier/m² | 2–4 Wochen |
<!-- Zuordnung Blattläuse → Aphidius/Aphidoletes fachlich korrekt; für Zikaden (Auchenorrhyncha) und Schaumzikaden ist kein etablierter kommerzieller Nützling belegt → bewusst nicht aufgeführt -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rose | Rosa spp. | 0.9 | Klassische Kombination; Lavendel hält Blattläuse von Rosen fern | `compatible_with` |
| Salbei | Salvia officinalis | 0.9 | Gleiche Standortansprüche | `compatible_with` |
| Rosmarin | Salvia rosmarinus | 0.9 | Mediterrane Kombination | `compatible_with` |
| Thymian | Thymus vulgaris | 0.9 | Gleiche Bedürfnisse | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Minze | Mentha spicata | Minze braucht Feuchtigkeit; Lavendel Trockenheit | moderate | `incompatible_with` |
| Hortensie | Hydrangea macrophylla | Sehr unterschiedliche Feuchtigkeitsbedürfnisse | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Lavendel |
|-----|-------------------|-------------|---------------------------|
| Speik-Lavendel | Lavandula latifolia | Gleiche Gattung | Wärmeliebender, intensiverer Duft |
| Lavandin | Lavandula × intermedia | Hybrid | Kräftiger, längere Blütenstiele, mehr Öl |
| Salbei | Salvia officinalis | Gleiche Familie, mediterran | Essbar, etwas winterhärter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months
Lavandula angustifolia,"Echter Lavendel;Schmalblättriger Lavendel;English Lavender",Lamiaceae,Lavandula,perennial,long_day,shrub,taproot,"5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Westliches Mittelmeer",yes,10,20,80,80,50,limited,yes,false,false,light_feeder,hardy,"6;7;8","6;7;8"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hidcote,Lavandula angustifolia,–,–,"compact;deep_violet;fragrant",–,,open_pollinated
Munstead,Lavandula angustifolia,–,1916,"compact;early;classic",–,,open_pollinated
Vera,Lavandula angustifolia,–,–,"tall;classic;oil_production",–,,open_pollinated
```

---

## Quellenverzeichnis

1. [Pflanzen-für-dich.de Lavandula angustifolia](https://pflanzen-fuer-dich.de/Lavandula-angustifolia) — Stammdaten, Winterhärte
2. [NaturaDB Lavandula angustifolia Rosea](https://www.naturadb.de/pflanzen/lavandula-angustifolia-rosea/) — Pflegehinweise
3. [Baumschule Horstmann Lavendel](https://www.baumschule-horstmann.de/rosabluehender-lavendel-rosea-697_44868.html) — Sortenwahl
4. [Plantura winterharte Kräuter](https://www.plantura.garden/kraeuter/kraeuter-anbauen/winterharte-kraeuter) — Winterhärte
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — Lavandula angustifolia](https://www.rhs.org.uk/plants/91398/lavandula-angustifolia/details) — Standort (full sun), Boden-pH (neutral bis alkalisch), Staunässe-Empfindlichkeit
6. [North Carolina Extension Gardener Plant Toolbox — Lavandula angustifolia](https://plants.ces.ncsu.edu/plants/lavandula-angustifolia/) — Wuchsform, Standort, Lebensdauer
7. [USU Extension — How to Grow English Lavender](https://extension.usu.edu/yardandgarden/research/english-lavender-in-the-garden) — Boden-pH 6.5–7.5, Drainage, Vollsonne
8. [Gardener Report — How Long do Lavenders Live](https://www.gardenerreport.com/how-long-do-lavenders-live/) — Lebensdauer 10–15 Jahre
9. [Gardenia.net — Is Lavender a Perennial](https://www.gardenia.net/guide/is-lavender-a-perennial) — Lebensdauer, Mehrjährigkeit
10. [Greenhouse Product News — L. angustifolia 'Hidcote Superior'](https://gpnmag.com/article/lavandula-angustifolia-hidcote-superior/) — Langtag-Bedürfnis (16 h), Vernalisation ≥ 10 Wochen Kälte
11. [MSU Extension — Vernalization Part 1 (Cameron et al.)](https://www.canr.msu.edu/resources/vernalization-part-1) — fakultativer Langtag + Vernalisationsbedarf, kritische Tageslänge ~12 h
12. [PanAmSeed — Lavandula Ellagance Series Culture (L. angustifolia)](https://www.panamseed.com/utility/CultureSheetPDF.aspx?pagename=culture.aspx&type=Per&txtphid=037304712) — Vernalisation 5 °C / 8–10 Wochen, Langtag-Forcing
13. [Frontiers in Plant Science 2023 — Photosynthesis under low temperature in L. angustifolia](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1268666/full) — Lichtsättigungspunkt ~1500 µmol, Temperatureffekte auf Netto-Photosynthese
14. [MDPI Plants 2020 — Effects of Drought and Salinity on Two Varieties of L. angustifolia](https://www.mdpi.com/2223-7747/9/5/637/htm) — Salztoleranz (50 mM → 21 % Biomasseverlust; weniger tolerant als Rosmarin)
15. [Frontiers in Plant Science 2018 — Responses of L. angustifolia to Salinity](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2018.00489/full) — Salztoleranz-Mechanismen, moderate Empfindlichkeit
16. [UMass Extension — Biological Control: Greenhouse Pests and Natural Enemies](https://www.umass.edu/agriculture-food-environment/greenhouse-floriculture/fact-sheets/biological-control-greenhouse-pests-their-natural-enemies) — Aphidius colemani / Aphidoletes aphidimyza gegen Blattläuse
17. [RHS — Aphid Predators](https://www.rhs.org.uk/biodiversity/aphid-predators) — natürliche Blattlausgegenspieler
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
