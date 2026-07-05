# Riesenkürbis / Hokkaido — Cucurbita maxima

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Bio-Gärtner.de Kürbis, Plantura Kürbis, Oekolandbau.de, Floragard Cucurbita maxima

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cucurbita maxima | `species.scientific_name` |
| Volksnamen (DE/EN) | Riesenkürbis, Hokkaido-Kürbis; Winter Squash, Pumpkin | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` → `botanical_families.name` |
| Gattung | Cucurbita | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchsphase (base temp, °C) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | — (einjährig, nicht zutreffend) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht zutreffend) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | — (tagneutral / day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich ab 0 °C; alle Pflanzenteile; typisch nach Eisheiligen (Mitte Mai) auspflanzen | `species.hardiness_detail` |
| Heimat | Südamerika (Peru, Bolivien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Befruchter-Sorte erforderlich (requires pollinator) | false | `species.requires_pollinator` |
| Kreuzbefruchtungsgruppe (pollinator group) | — (kein Obst-Fremdbefruchter; selbstkompatibel, leer) | `species.pollinator_group` |
| Kompatible Befruchter-Sorten | — (nicht zutreffend) | `species.compatible_pollinators` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> Bestäubungshinweis: *Cucurbita maxima* ist einhäusig (monoecious) mit getrennten männlichen und weiblichen Blüten und selbstkompatibel — es ist daher **keine** zweite Befruchter-Sorte (pollenizer cultivar) nötig (`requires_pollinator = false`, keine pomologische Kreuzbefruchtungsgruppe). Der Fruchtansatz ist jedoch **insektenbestäubt** und ohne Bienen-/Hummelflug stark eingeschränkt (ohne Insektenbesuch kein Fruchtansatz); bei schlechtem Bestäuberflug morgens manuell bestäuben (vgl. §4.2). Bestäubende Insekten gehören in diesen Freitext, nicht in das Sortenfeld `compatible_pollinators`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3–4 (Vorkultur April in Töpfe) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 9, 10 | `species.harvest_months` |
| Blütemonate | 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Vorsicht: bittere Kürbisse (Cucurbitacin) NICHT essen | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Cucurbitacin (in bitteren Exemplaren; kann durch Einkreuzung entstehen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Triebspitzen zur Fruchtförderung) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (nur Buschsorten in min. 60 L) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 60–100 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–50 (kriechend bis 300–500 cm Länge) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–300 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 150–200 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Buschsorten, rankend über Geländer) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (für rankende Sorten über Gestell) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr nährstoffreiche, lockere Erde mit viel Kompost; pH 6,0–6,8 | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein cucurbita-spezifischer Wert aus ≥2 unabhängigen seriösen Quellen belegt | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein cucurbita-spezifischer Wert aus ≥2 unabhängigen seriösen Quellen belegt | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 100–150 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | moderate | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe, dS/m) | 3.2 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | 16 | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–6.8 | `species.soil_ph_preference` |

> Hinweis: Effektive Wurzeltiefe nach FAO-56 Tab. 22 (Pumpkin/Winter Squash 1,0–1,5 m); überwiegend flach- bis mittelwurzelnd mit weit streichendem Wurzelsystem. Salztoleranz-Kennwerte (ECe-Schwelle, Slope) sind Maas-Hoffman-Werte für Squash/Kürbis (FAO/Ayers & Westcot, Substrat-Sättigungsextrakt-ECe), nicht Gießwasser-EC. C. maxima gilt innerhalb der Gattung als vergleichsweise salzrobust, in der absoluten FAO-Klassifikation jedoch als mäßig empfindlich (moderately_sensitive).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 21 (70°F, gängige Untergrenze für zügige Keimung; absolute Keimung ab ca. 18°C/65°F möglich, aber deutlich langsamer) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 29 (85°F Optimalbereich; Toleranz bis 38°C/100°F dokumentiert) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 2 (¾–1 Zoll ≈ 1.9–2.5 cm) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 3 (3–10 Tage, unterer Wert bei optimaler Wärme) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (3–6 Jahre bei kühler, trockener, dunkler Lagerung; bis zu 4 Jahre unter guten Bedingungen sicher belegt) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | <!-- DATEN FEHLEN: keine explizite, artspezifisch bestätigte Aussage zu Licht-/Dunkelkeimung von Cucurbita maxima gefunden --> | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (Warmkeimer ohne Stratifikations- oder Skarifikationsbedarf) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 100 (Spanne ca. 65–125 g, aus Samenzahl 8–15 Samen/g errechnet — großes, sortenabhängiges Saatgut) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Kürbis wird als Hügel-/Horstkultur mit sehr weitem Pflanzabstand (150–200 cm) angebaut, keine Reihenkultur mit dokumentierter Flächen-Aussaatdichte --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
- [MSU Extension — How to Grow Pumpkin and Squash](https://www.canr.msu.edu/resources/how_to_grow_pumpkin_and_squash) — Keimtemperatur 65–100°F, Keimdauer 3–10 Tage
- [Oklahoma State University Extension — Squash and Pumpkin Production (HLA-6026)](https://extension.okstate.edu/fact-sheets/print-publications/hla/squash-and-pumpkin-production-hla-6026.pdf) — Optimaltemperatur 70–85°F (bereits im Hauptdokument als Quelle #9 geführt)
- [Pumpkin Nook — Pumpkin Seed Germination](https://www.pumpkinnook.com/howto/germinat.htm) und [Grow Pittsburgh — How-To: Testing Seed Viability](http://www.growpittsburgh.org/wp-content/uploads/How-To-Testing-Seed-Viability.pdf) — Keimfähigkeitsdauer 3–6 Jahre, bis 4 Jahre unter guten Bedingungen
- [Vital Seeds — Seeds per Gram](https://vitalseeds.co.uk/growing-resources/seed-saving-resources/seeds-per-gram/), [Osborne Seed — Seed Count Chart](https://www.osborneseed.com/pages/seed-count-chart), [Farmers Stop — Seeds Per Gram for Common Vegetables](https://www.farmersstop.com/blogs/news/seeds-per-gram-for-common-vegetables-fruits-and-others) — Samenzahl 8–15 Samen/g (TKG-Ableitung)
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ (Rankenbildung) | 21–42 | 3 | false | false | medium |
| Blüte & Fruchtansatz | 21–35 | 4 | false | false | medium |
| Fruchtreife | 42–70 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (vpd threshold, kPa) | 2.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp opt, °C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 (offenes Tageslicht/Vollsonne ≈ 0.5) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (Reifeförderung durch leichten Trockenstress) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.8–1.2 | 6.0–6.8 | 80 | 40 | — | 2 | 0.4–0.5 | 0.1–0.3 | 0.03–0.05 | 0.02–0.05 |
| Vegetativ | 3:1:2 | 1.5–2.5 | 6.0–6.8 | 150 | 60 | 20 | 3 | 0.5–0.8 | 0.3–0.5 | 0.05–0.1 | 0.03–0.05 |
| Blüte | 1:2:3 | 1.5–2.0 | 6.0–6.8 | 120 | 70 | — | 2 | 0.5–0.8 | 0.3–0.5 | 0.05–0.1 | 0.03–0.05 |
| Fruchtreife | 0:1:3 | 1.0–1.5 | 6.0–6.8 | 100 | 50 | — | 1 | 0.4–0.5 | 0.1–0.3 | 0.03–0.05 | 0.02–0.05 |

> Mikronährstoff-Spannen (Mn/Zn/Cu/Mo) nach cucurbit-spezifischen Nährlösungsempfehlungen (Haifa Cucumber Crop Guide, Cornell Greenhouse Hydroponic Recipes; KA-Felder `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 8–10 L/Pflanzloch | Pflanzung |
| Hornspäne | Oscorna | organisch-N | 100–150 g/Pflanzloch | Pflanzung |
| Brennnesseljauche | selbst | organisch-N | 1:10 verdünnt, 2L/Pflanze | alle 2–3 Wochen Jul–Aug |

#### Mineralisch (Ergänzung)

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Kürbis-Dünger | Compo | base | 7-3-10 | 80–100 g/Pflanze | Wachstum |
| Patentkali | K+S | supplement | 0-0-30+10MgO | 40 g/Pflanze | Fruchtreife |

### 3.2 Besondere Hinweise zur Düngung

Kürbis ist Starkzehrer mit sehr hohem Nährstoffbedarf — das Pflanzloch vor dem Setzen großzügig mit Kompost und Hornspänen füllen. Magnesium-Mangel typisch (gelbliche Blätter mit grünen Adern) — mit Bittersalz oder Patentkali korrigieren. Zu viel Stickstoff fördert Ranken auf Kosten der Früchte. Blütenendenfäule durch Ca-Mangel oder Bewässerungsunregelmäßigkeiten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Große Mengen, direkt an die Wurzel; Blätter trocken halten (Mehltau) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Vorkultur | Einzeln in 10-cm-Töpfe bei 20–25 °C; nicht zu früh! | hoch |
| Mai (nach 15.) | Auspflanzen | Nach Eisheiligen; warm und frostfrei | hoch |
| Jun | Schneckenschutz | Junge Pflanzen massiv gefährdet | hoch |
| Jul | Rankenpflege | Triebspitzen pinzieren für mehr Früchte | mittel |
| Jul–Aug | Bestäubung | Bei Bedarf manuell bestäuben (morgens) | niedrig |
| Aug | Brett/Unterlage | Unter Früchte legen verhindert Fäulnis | mittel |
| Sep–Okt | Ernte | Stiel verholzt, hohl klingt, Schale hart | hoch |
| Okt | Winterlager | Kühl (10–15 °C), trocken, Frost vermeiden; hält Monate | mittel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | — (nicht zutreffend: einjährig, stirbt nach der Ernte ab) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | none | `overwintering_profiles.winter_action` |
| Frühjahrs-Maßnahme (spring action) | — (nicht zutreffend) | `overwintering_profiles.spring_action` |

> *Cucurbita maxima* ist eine einjährige, frostempfindliche Kulturpflanze (annual, tender). Die **Pflanze selbst wird nicht überwintert** — sie stirbt nach der Fruchtreife bzw. beim ersten Frost ab; eine Überwinterung im KA-Sinne (mulch/fleece/move_indoors/dig_store) ist daher nicht zutreffend. Überwintert werden lediglich die **Früchte** als Lagergut (Winterlager kühl 10–15 °C, trocken, frostfrei; siehe §4.2) — das ist Post-Harvest-Lagerung, keine Pflanzen-Überwinterung. Die Vermehrung im Folgejahr erfolgt ausschließlich über Saatgut.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Nacktschnecke | Arion spp., Deroceras spp. | Riesige Fraßschäden an Jungpflanzen und Früchten | all | seedling, flowering | easy |
| Kürbisfliege | Dacus cucurbitae | Larven in Früchten (in DE selten) | fruit | ripening | difficult |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau, Schmutzpilze | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißes, mehligartiges Pulver auf Blättern | Trockene Tage, feuchte Nächte | 5–10 | vegetative, flowering |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel an Blüten und Früchten | Feuchtigkeit | 3–7 | flowering, ripening |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinernema feltiae | Schnecken-Larven im Boden | 500.000/m² | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen, 5 g/m² | 0 | Schnecken |
| Milch-Lösung (1:10) | biological | Milchsäure | Blattsprühmittel, wöchentlich | 0 | Echter Mehltau |
| Schwefel | chemical | Schwefel | Stäuben/Spritzen | 3 | Echter Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kürbisgewächse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte, Leguminosen |
| Empfohlene Nachfrucht | Salat, Spinat, Zwiebeln (Schwachzehrer) |
| Anbaupause (Jahre) | 3 Jahre keine Cucurbitaceen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.9 | Drei-Schwestern-Mischkultur; Mais gibt Rankstütze | `compatible_with` |
| Bohne | Phaseolus vulgaris | 0.9 | Drei-Schwestern; N-Fixierung | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Ablenkpflanze | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Konkurrenz, ähnliche Schädlinge | moderate | `incompatible_with` |
| Gurke | Cucumis sativus | Gleiche Familie, Mehltau-Übertragung | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Riesenkürbis |
|-----|-------------------|-------------|--------------------------------|
| Zucchini | Cucurbita pepo | Gleiche Familie, kompakter | Kürzere Reifezeit, platzsparend |
| Butternut-Kürbis | Cucurbita moschata | Ähnliche Kultur | Bessere Lagerfähigkeit |
| Patisson | Cucurbita pepo | Gleiche Familie | Kompakter, früher reif |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Cucurbita maxima,"Riesenkürbis;Hokkaido-Kürbis;Pumpkin;Winter Squash",Cucurbitaceae,Cucurbita,annual,day_neutral,vine,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Südamerika",limited,80,40,50,300,175,no,limited,false,true,heavy_feeder,tender,"5;6","9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hokkaido (Red Kuri),Cucurbita maxima,Japan,–,"red_skin;nutty_flavor;small",110,,open_pollinated
Atlantic Giant,Cucurbita maxima,–,–,"giant;exhibition",120,,open_pollinated
```

---

## Quellenverzeichnis

1. [Kürbisse — Der Bio-Gärtner](https://www.bio-gaertner.de/Pflanzen/Kuerbisse) — Bio-Anbau
2. [Kürbis pflanzen — Plantura](https://www.plantura.garden/gemuese/kuerbis/kuerbis-pflanzen) — Pflege, Zeitplan
3. [Ökologischer Kürbisanbau — oekolandbau.de](https://www.oekolandbau.de/landwirtschaft/pflanze/spezieller-pflanzenbau/gemuese/feldgemuesebau/kuerbisse/) — NPK, Anbau
4. [Floragard Cucurbita maxima](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/gemuese/cucurbita-maxima) — Pflanzendaten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [FAO — Annex 1: Crop salt tolerance data (Ayers & Westcot)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Salztoleranz Squash/Kürbis: ECe-Schwelle 3,2 dS/m, Slope 16 %/dS/m, Klasse moderately sensitive (Maas-Hoffman)
6. [FAO Irrigation & Drainage Paper 56, Table 22 — Maximum rooting depth (Nevada DWR mirror)](https://water.nv.gov/mapping/et/Docs/Annex_1.pdf) — Effektive Wurzeltiefe Pumpkin/Winter Squash 1,0–1,5 m
7. [Penn State Extension — Understanding Growing Degree Days](https://extension.psu.edu/understanding-growing-degree-days) — GDD-Basistemperatur warmer Saisongemüse 10 °C (50 °F)
8. [UMN Extension — Growing pumpkins and winter squash](https://extension.umn.edu/vegetables/pumpkins-and-winter-squash) — Wachstumsstopp unter 50 °F (10 °C), Optimaltemperaturen 24–29 °C
9. [Oklahoma State University Extension — Squash and Pumpkin Production (HLA-6026)](https://extension.okstate.edu/fact-sheets/print-publications/hla/squash-and-pumpkin-production-hla-6026.pdf) — Wachstum stoppt unter 50 °F, Optimaltemperaturen
10. [The Old Farmer's Almanac — Growing Pumpkins](https://www.almanac.com/plant/pumpkins) — Boden-pH 6,0–6,8, Vollsonne, Starkzehrer
11. [Mississippi State University Extension — Growing Pumpkins for the Home Garden](https://extension.msstate.edu/publications/growing-pumpkins-for-the-home-garden) — Boden-pH 6,0–6,8, Standort
12. [Haifa Group — Crop Guide: Nutrients for Cucumber](https://www.haifa-group.com/cucumber-0/crop-guide-nutrients-cucumber) — Mikronährstoff-Konzentrationen (Mn/Zn/Cu/Mo) in Cucurbit-Nährlösung
13. [Cornell Greenhouse — A Recipe for Hydroponic Success](http://hort.cornell.edu/greenhouse/crops/factsheets/hydroponic-recipes.pdf) — Hydroponik-Nährlösung mit Mikronährstoffen
14. [Zhen & Bugbee 2021, ASHS JASHS 146(1): Far-red Fraction — An Improved Metric for Characterizing Phytochrome Effects on Morphology](https://journals.ashs.org/view/journals/jashs/146/1/article-p3.xml) — Far-Red-Fraction-Anker: Tageslicht ≈ 0,5; direkte Sonne ≈ 0,2
15. [MDPI Plants 2025, 14(11):1674 — Salt Stress Leads to Morphological and Transcriptional Changes in Roots of Pumpkins (Cucurbita spp.)](https://www.mdpi.com/2223-7747/14/11/1674) — relative Salztoleranz C. maxima vs. C. moschata
16. [PMC3722171 — Pollination Services Provided by Bees in Pumpkin Fields](https://pmc.ncbi.nlm.nih.gov/articles/PMC3722171/) — Cucurbita einhäusig, insektenbestäubt, ohne Insektenbesuch kein Fruchtansatz
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
17. [MSU Extension — How to Grow Pumpkin and Squash](https://www.canr.msu.edu/resources/how_to_grow_pumpkin_and_squash) — Keimtemperatur, Keimdauer
18. [Pumpkin Nook — Pumpkin Seed Germination](https://www.pumpkinnook.com/howto/germinat.htm) — Keimfähigkeitsdauer, Keimbedingungen
19. [Grow Pittsburgh — How-To: Testing Seed Viability](http://www.growpittsburgh.org/wp-content/uploads/How-To-Testing-Seed-Viability.pdf) — Keimfähigkeitsdauer (Zweitbeleg)
20. [Vital Seeds — Seeds per Gram](https://vitalseeds.co.uk/growing-resources/seed-saving-resources/seeds-per-gram/) und [Osborne Seed — Seed Count Chart](https://www.osborneseed.com/pages/seed-count-chart) — Samenzahl je Gramm (TKG-Ableitung)
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
