# Tabak — Nicotiana tabacum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** USDA PLANTS Database, University of Kentucky College of Agriculture Tobacco Production, FAO Tobacco Crop Profile, North Carolina State University Extension, Royal Horticultural Society

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Nicotiana tabacum | `species.scientific_name` |
| Volksnamen (DE/EN) | Tabak, Virginischer Tabak; Common Tobacco, Virginia Tobacco | `species.common_names` |
| Familie | Solanaceae | `species.family` → `botanical_families.name` |
| Gattung | Nicotiana | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | 10–13 (Wuchs der Hauptphase wird unter 10–13 °C eingeschränkt; wärmeliebende Art; NICHT der Keim-Basiswert von 13–19 °C) | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral) — kein Kurztag-/Langtag-Blüher, daher kein numerischer Stunden-Schwellwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 9a–11b (als Jahrespflanze in 5a–11b kultivierbar) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frost-empfindlich; stirbt bei Frost ab; in Mitteleuropa als einjährige Sommerkultur; Vorkultur im Warmhaus ab März–April; Auspflanzung nach letztem Frost | `species.hardiness_detail` |
| Heimat | Südamerika (Bolivien, Argentinien, Andenregion) | `species.native_habitat` |
| Allelopathie-Score | -0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Allelopathie-Hinweis:** Tabak-Wurzelsekrete (Solanesol, Chlorogensäure) hemmen benachbarte Pflanzen. Außerdem akkumuliert Nicotiana tabacum Tabak-Mosaik-Virus (TMV) — gefährlicher Vektori für benachbarte Solanaceen (Tomate, Paprika, Aubergine). Nicht neben Solanaceen pflanzen!

**Rechtlicher Hinweis:** Anbau von Tabak für den Eigenbedarf ist in Deutschland erlaubt, jedoch steuerlich komplex (Tabaksteuer). Gewerblicher Anbau bedarf einer Genehmigung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 (Tabakanzucht dauert lange; sehr kleines Saatgut) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14–21 (nur Gewächshaus; zu feines Saatgut für Freiland-Direktsaat) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Vorkultur im Warmhaus) | `species.direct_sow_months` |
| Erntemonate | 7, 8, 9 (Blattern von unten nach oben) | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (Rispenpflanze; gekappt = Sucker-Triebe; Geiz entfernen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Saatgut-Hinweis:** Tabaksamen sind extrem klein (10.000–20.000 Samen/g). Nicht eingraben — Samen benötigen Licht zur Keimung (Lichtkeimer). Auf feuchtes Substrat streuen; Folie oder Glas drüber; 25–30°C.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Bestäubungs-Hinweis:** Nicotiana tabacum ist selbstbestäubend und selbstfruchtbar (self-pollinating, self-fertile); die Blütenstruktur (Antheren nahe der Narbe) ermöglicht autonome Selbstbestäubung. Es ist KEIN Obst-Fremdbefruchter — daher bleiben `species.requires_pollinator` (= false), `species.pollinator_group` und `species.compatible_pollinators` leer/ungesetzt. Insektenbesuch (Bienen, Hummeln, nachts Schwärmer) steigert lediglich die genetische Vielfalt, ist aber für den Samenansatz nicht erforderlich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | ALLE Teile (besonders frische Blätter; Grüner Tabak-Vergiftung bei Verarbeitern) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Nikotin (0,5–8% in Blättern; stark giftig; LD50 40–60 mg für Erwachsene); Anabasin, Nornicotikin (weitere Alkaloide) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Grüner-Tabak-Krankheit = Green Tobacco Sickness; Nikotinaufnahme durch Haut bei feuchten Blättern) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**KRITISCHE SICHERHEITSWARNUNG:** Nikotin ist eines der giftigsten Alkaloide bekannt. Bei der Verarbeitung von Tabakblättern IMMER wasserdichte Handschuhe tragen — Nikotin wird über feuchte Haut resorbiert. Grüner-Tabak-Krankheit (Übelkeit, Erbrechen, Tachykardie) ist bei Tabakerntearbeitern bekannt. Pflanze außerhalb der Reichweite von Kindern und Tieren halten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Topping = Rispenkappung; Geizen = Sucker entfernen) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (Topping wenn 50–75% der gewünschten Blätter entwickelt) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–40 (große, tiefe Töpfe für volle Blatentwicklung) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–250 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–80 × 90–100 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (Gewächshaus; sehr lichtbedürftig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (windgeschützt; sonnig) | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte, nährstoffreiche Erde; pH 5,8–6,5; leicht sauer; durchlässig; Substrat wie für Tomaten | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein tabak-spezifischer Kompensationspunkt aus ≥2 seriösen Quellen belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein tabak-spezifischer Kompensationspunkt aus ≥2 seriösen Quellen belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (benötigt mind. 6 h volle Sonne; FAO: gut belüftete, sonnige Standorte) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 50–100 (FAO: D = 0,5–1,0 m; 75 % der Wasseraufnahme in den oberen 30 cm) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (FAO: sehr empfindlich gegen Staunässe; 2+ Tage Vernässung schädigen/töten die Pflanze) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive (FAO: geringe Salztoleranz; Bodensalinität mindert die Blattqualität) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: Tabak ist nicht in der FAO/Maas-Hoffman-Salztoleranztabelle gelistet; kein belegter Schwellwert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope für Tabak --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.0–6.5 (FAO-Optimum; Feinabstimmung 5,8–6,5 wie in §1.6/§2.3) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 21 (70–80°F laut Univ. Kentucky Tobacco Production Guide, konstant über 10–14 Tage; unter 65°F/18°C deutlich verlangsamt) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 30 (§1.3 nennt 25–30°C als Praxisoptimum) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer; nicht eingraben, §1.3) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (unter optimalen Bedingungen 7–10 Tage; §2.1-Phasendauer 10–21 Tage deckt auch suboptimale Anzuchtbedingungen ab) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 5 (praktische Lagerung bei Zimmertemperatur/Kühlschrank; Genbank-Studien zeigen bei -15/-18°C Tiefkühllagerung Haltbarkeit von 30 bis über 50 Jahren) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light (§1.3 bereits belegt: Lichtkeimer, nicht eingraben) | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (für Standardanzucht nicht erforderlich; wissenschaftliche Studie zeigt, dass Vorkühlung/cold-stratification die Keimrate zusätzlich verbessern kann, ist aber keine Voraussetzung) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 0.05–0.12 (extrem kleines Saatgut; §1.3: 10.000–20.000 Samen/g ≈ 0,05–0,1 g/1000 Korn; Saatguthandel nennt teils 0,12 g/1000 Korn — Sortenvariation) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Anzucht erfolgt in Aussaatschalen zur späteren Pikierung/Auspflanzung (§1.6: 60–80 × 90–100 cm Pflanzabstand), keine Flächen-/Reihensaat mit belegter Kornzahl je m² --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
1. §1.3 dieses Steckbriefs (bereits zitierte Quellen: 10.000–20.000 Samen/g, Lichtkeimer, 25–30°C) — Cross-Check
2. [University of Kentucky — Tobacco Production Guide](https://tobacco.ca.uky.edu) (bereits im Quellenverzeichnis zitiert) — Keimtemperatur konstant 70–80°F (21–27°C) über 10–14 Tage
3. [TrueLeafMarket — Ideal Germination Conditions for Tobacco Seeds](https://trueleafmarket.com/blogs/articles/ideal-germination-conditions-for-tobacco-seeds) — Keimdauer 7–10 Tage unter Idealbedingungen, Lichtkeimer-Bestätigung
4. [OnlineTobaccoSeedStore — Storing Your Seeds](https://www.onlinetobaccoseedstore.com/storing-your-seeds/) — Keimfähigkeitsdauer praktisch 2–5+ Jahre bei kühler/dunkler Lagerung, ca. 10 % Keimratenverlust pro Jahr
5. [Weberseeds/UF Seeds/Various Seed Catalogs — Nicotiana tabacum](https://weberseeds.nl/eshop/en/Seeds/Seeds-A-Z/Nicotiana-tabacum-Tobacco::110.html) — Tausendkornmasse ≈ 0,12 g (Cross-Check TKG)
6. [Suppression of LOX activity enhanced seed vigour and longevity of tobacco (Nicotiana tabacum L.) seeds during storage, PMC6161406](https://pmc.ncbi.nlm.nih.gov/articles/PMC6161406/) (bereits im Quellenverzeichnis zitiert) — Langzeit-Keimfähigkeit bei Tiefkühllagerung (-15/-18°C): 30–50+ Jahre
7. [CORESTA — Pre-chilling improves tobacco (Nicotiana tabacum L.) seed germination](https://www.coresta.org/abstracts/pre-chilling-improves-tobacco-nicotiana-tabacum-l-seed-germination-27921.html) — Vorkühlung verbessert Keimrate zusätzlich (optional, nicht obligatorisch)
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–21 | 1 | false | false | low |
| Sämling | 28–42 | 2 | false | false | low |
| Vegetativ / Rosette | 21–42 | 3 | false | false | medium |
| Streckungsphase | 21–35 | 4 | false | false | medium |
| Blüte / Topping | 14–21 | 5 | false | true | medium |
| Blatternte | 35–60 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 (Lichtkeimer; Licht nötig!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75–90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 (deutlich oberhalb des Zielkorridors; kritischer Punkt für stomatären Kollaps der feuchteliebenden Keimphase) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high (junge Keimlinge reagieren empfindlich auf Austrocknung) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 28–32 (Netto-CO₂-Assimilations-Optimum für N. tabacum, Kubien 2008) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: stark vom Anzuchtspektrum abhängig; unter Vollspektrum-/Tageslicht ≈ 0.5, unter FR-armer roter LED < 0.3 --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2 (feucht halten; nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 24–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 (oberer Zielwert + ~0.4 kPa; stomatärer Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 28–32 (Netto-CO₂-Assimilations-Optimum für N. tabacum, Kubien 2008) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: spektrumabhängig; Tageslicht/Vollspektrum ≈ 0.5, FR-arme rote LED < 0.3 --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–1000 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ / Streckung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 26–34 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–24 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (oberer Zielwert + ~0.4 kPa; stomatärer Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 28–32 (Netto-CO₂-Assimilations-Optimum für N. tabacum, Kubien 2008) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freilandkultur unter offener Vollsonne; R:FR ≈ 1,1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 800–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blatterntefase

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 30–45 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 26–32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.0 (oberer Zielwert + ~0.4 kPa; abgehärtete Blattmasse, stomatärer Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low (ausgereifte Blätter toleranter gegenüber höherem VPD) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 26–30 (Abreifephase; etwas niedriger für optimale Blattqualität, 22–28 °C Feldwachstumsoptimum) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freilandkultur unter offener Vollsonne; R:FR ≈ 1,1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 800–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | K-Betonung |
|-------|----------------|---------|-----|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 5.8–6.2 | — | — | — |
| Sämling | 2:1:2 | 0.6–1.0 | 5.8–6.2 | 60 | 25 | mittel |
| Vegetativ | 3:1:3 | 1.2–1.8 | 5.8–6.5 | 120 | 50 | hoch |
| Streckung | 2:1:4 | 1.4–2.2 | 5.8–6.5 | 150 | 60 | sehr hoch |
| Blatternte | 1:1:3 | 1.0–1.6 | 5.8–6.5 | 100 | 50 | hoch |

**Besonderheit:** Tabak hat einen extrem hohen Kalium-Bedarf — Kalium beeinflusst Verbrennungseigenschaften und Blattqualität. Chlorid-freies Kalium (K₂SO₄) verwenden, da Chlorid die Blattqualität mindert.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo):**

| Mikronährstoff | Wert | KA-Feld |
|----------------|------|---------|
| Mangan (Mn, ppm) | <!-- DATEN FEHLEN: tabak-spezifischer Nährlösungs-Sollwert nicht aus ≥2 Quellen belegt. Belegt ist nur der Blattgewebe-Suffizienzbereich 20–250 ppm (NC State Extension), >1000 ppm toxisch --> | `nutrient_profiles.manganese_ppm` |
| Zink (Zn, ppm) | <!-- DATEN FEHLEN: kein belegter Sollwert; Zn-Mangel bei Tabak laut NC State Extension extrem selten --> | `nutrient_profiles.zinc_ppm` |
| Kupfer (Cu, ppm) | <!-- DATEN FEHLEN: kein belegter Sollwert; Cu-Mangel bei Tabak laut NC State Extension extrem selten --> | `nutrient_profiles.copper_ppm` |
| Molybdän (Mo, ppm) | <!-- DATEN FEHLEN: kein tabak-spezifischer Sollwert aus ≥2 Quellen belegt --> | `nutrient_profiles.molybdenum_ppm` |

Hinweis: Die belegten Werte sind Blattgewebe-Suffizienzbereiche (tissue sufficiency), nicht Nährlösungs-Konzentrationen — daher nicht direkt in die phasenbezogenen Lösungs-ppm-Felder übernommen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Sämling | time_based | 10–21 Tage; 2 Keimblätter entwickelt |
| Sämling → Vegetativ | time_based | 28–42 Tage; 5–6 echte Blätter; Pikierung |
| Vegetativ → Streckung | time_based | 21–42 Tage; Pflanzung ins Freiland; Streckung setzt ein |
| Streckung → Blatternte | event_based | Topping (Rispenentfernung); Seitenaustriebe kappen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Gewächshaus)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15–0.25 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.15–0.20 | 4 | vegetativ |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10–0.15 | 4 | streckung, ernte |
| CalMag | diverse | supplement | 2-0-0 | 0.15–0.20 | 2 | alle |
| Kaliumsulfat K2SO4 | diverse | supplement | 0-0-50 | 0.10–0.15 | 5 | streckung |

#### Organisch / Freiland

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Kompost | eigen | organisch | 4–6 L/m² | Vor Pflanzung |
| Hornmehl | diverse | organisch | 60–100 g/m² | Vor Pflanzung |
| Kaliumsulfat (granuliert) | diverse | mineralisch | 20–30 g/m² | Grunddüngung + Streckung |
| Leachate / Wurmtee | diverse | organisch | 1:10 verdünnt | 2× wöchentlich |

### 3.2 Mischungsreihenfolge

1. Silikat-Zusätze (falls verwendet)
2. CalMag
3. Flora Micro / Base A
4. Flora Gro oder Flora Bloom (je Phase)
5. Kaliumsulfat (separat auflösen)
6. pH-Korrektur (IMMER zuletzt)

### 3.3 Besondere Hinweise zur Düngung

Hoher Kalium-Bedarf — KEIN Kaliumchlorid (KCl) verwenden (Chlorid verschlechtert Verbrennungseigenschaften). Calcium essentiell für Blattqualität. Übermäßige N-Düngung ergibt rohen, scharfen Tabak mit schlechten Brenneigenschaften — N in der Abreife reduzieren.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser bevorzugt (EC <0.3 mS); pH 5,8–6,5 | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7–14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Saatgutaussaat | Sehr feines Saatgut auf feuchtes Substrat streuen; 25–30°C; Lichtkeimer | hoch |
| Apr | Pikierung | Sämlinge pikieren wenn 3–4 cm groß; einzeln in 6-cm-Töpfe | hoch |
| Mai–Jun | Abhärtung / Auspflanzung | Langsam abhärten; nach letztem Frost auspflanzen | hoch |
| Jul | Topping | Rispe kappen wenn 50–75% der Blätter erwünscht; sofort Geizen (Sucker entfernen) | hoch |
| Jul–Aug | Blatternten | Unterste reife Blätter (gelb-grün) zuerst ernten; ca. 2–3 Blätter/Woche | hoch |
| Aug–Sep | Letzte Ernte | Obere Blätter noch unreifer; trocknen separat | mittel |
| Sep–Okt | Trocknung | Blätter aufhängen; 30–40°C; 4–8 Wochen | mittel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

Nicht zutreffend: Nicotiana tabacum ist in Mitteleuropa eine einjährige (annual) Sommerkultur und stirbt beim ersten Frost ab (`species.frost_sensitivity` = tender). Es findet keine Überwinterung der Pflanze statt; eine erneute Kultur erfolgt jährlich über Aussaat. Daher werden `hardiness_rating`, `winter_action` und `spring_action` für diese Art nicht gesetzt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Tabakblattlaus | Myzus persicae | Kolonien; virusübertrager; Vergilbung | Blatt, Trieb | Sämling, Vegetativ |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; Gelbflecken; Austrocknung | Blatt | Streckung, Ernte |
| Minierfliege | Liriomyza trifolii | Minen/Gänge in Blättern | Blatt | Vegetativ |
| Tabakraupen | Manduca sexta, M. quinquemaculata | Großer Fraß; Kotklumpen | Blatt | Blüte, Ernte |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau; Rußtau | Blatt | Alle (Gewächshaus) |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Tabak-Mosaik-Virus (TMV) | viral | Mosaikflecken; Blasen; Wuchshemmung | mechanische Übertragung |
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißgrauer Belag | trocken-warm |
| Blauer Schimmel | fungal (Peronospora tabacina) | Gelbliche Flecken oben; blauer Belag unten | kühl-feucht |
| Braunfleckigkeit | fungal (Alternaria alternata) | Braune Flecken; Blattfall | alt/geschwächt; feucht |
| Schwarzbeinigkeit | fungal (Pythium, Rhizoctonia) | Halsnekrose; Keimlingsfäule | übermäßige Nässe |

**WICHTIG — TMV:** Tabak-Mosaik-Virus überlebt in Tabakprodukten (Zigaretten!). Nie Tabak verarbeitende Personen sollten ohne Handwaschen Tabakpflanzen anfassen. TMV kann auf Tomaten, Paprika, Auberginen übertragen werden.

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5–10 | 14–21 |
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Aphidius colemani | Blattläuse | 3–5 | 14 |
| Steinernema carpocapsae | Tabakraupen (Boden) | 50 Nematoden/m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Blattläuse, Spinnmilben |
| Pyrethrin | biological | Pyrethrine | Sprühen | 3 | Blattläuse, Weiße Fliege |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen | 14 | Mehltau, Blauer Schimmel |
| Spinosad | biological | Spinosad | Sprühen | 3 | Tabakraupen |
| Kupferfungizid | biological/chemical | Kupferhydroxid | Sprühen | 7 | Blauer Schimmel |
| Bacillus thuringiensis | biological | Bt var. kurstaki | Sprühen | 0 | Tabakraupen |
| Befallenes Material entfernen | cultural | — | Sofortentfernung | 0 | TMV, Viruskrankheiten |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Wildtyp-TMV Resistenz (sortenabhängig; N-Gen) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Solanaceen (Solanaceae) |
| Empfohlene Vorfrucht | Getreide, Gräser, Hülsenfrüchte |
| Empfohlene Nachfrucht | Getreide; KEINE Solanaceen (TMV-Risiko); KEIN Kohl |
| Anbaupause (Jahre) | 4 Jahre vor erneuten Solanaceen (TMV, Nematoden) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Fangpflanze; schützt Tabak | `compatible_with` |
| Tagetes | Tagetes erecta / patula | 0.7 | Nematoden-Abwehr; Bestäuber | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.6 | Thrips-Abwehr (anekdotisch) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | TMV-Vektorrisiko; gleiche Krankheiten | severe | `incompatible_with` |
| Paprika | Capsicum annuum | TMV-Vektorrisiko; gleiche Familie | severe | `incompatible_with` |
| Aubergine | Solanum melongena | Gleiche Familie; gleiche Schädlinge/Krankheiten | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gleiche Familie; Nematoden; TMV | severe | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Solanaceae | `shares_pest_risk` | TMV, Blattläuse (Myzus persicae), Spinnmilben | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tabak |
|-----|-------------------|-------------|------------------------|
| Bauern-Tabak | Nicotiana rustica | Gleiche Gattung | Höherer Nikotingehalt; robuster |
| Ziertabak | Nicotiana alata / sylvestris | Gleiche Gattung | Keine Nikotinproduktion; Zierpflanze |
| Ziertabak | Nicotiana x sanderae | Gattung | Farbenfrohe Hybriden; Zierwert |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Nicotiana tabacum,"Tabak;Virginischer Tabak;Common Tobacco;Virginia Tobacco",Solanaceae,Nicotiana,annual,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b",-0.3,"Südamerika",limited,limited,limited,true,false,heavy_feeder,false,tender,"3;4","7;8;9","7;8;9"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Virginia Gold,Nicotiana tabacum,"virginia_flue_cured;golden_leaf;high_sugar",100,open_pollinated
Burley KY14,Nicotiana tabacum,"burley_type;air_cured;high_nicotine",110,open_pollinated
Oriental Izmir,Nicotiana tabacum,"oriental_type;aromatic;small_leaf;sun_cured",120,open_pollinated
```

---

## Quellenverzeichnis

1. [University of Kentucky — Tobacco Production Guide](https://tobacco.ca.uky.edu) — Anbaupraxis, Düngung
2. [USDA PLANTS — Nicotiana tabacum](https://plants.usda.gov/plant-profile/NITA2) — Taxonomie
3. [FAO Tobacco Crop Profile](https://www.fao.org/tobacco) — Globale Anbausysteme
4. [North Carolina State University Extension — Tobacco IPM](https://entomology.ces.ncsu.edu) — IPM, Schädlinge
5. [RHS — Growing Tobacco as a Garden Plant](https://www.rhs.org.uk) — Gartenkultur
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [FAO Land & Water — Tobacco Crop Information](https://www.fao.org/land-water/databases-and-software/crop-information/tobacco/en/) — Effektive Wurzeltiefe (0,5–1,0 m), Boden-pH 5,0–6,5, Staunässe-Empfindlichkeit, geringe Salztoleranz
7. [Springer/Planta — Inhibition of oxygen release in a C3-plant (Nicotiana tabacum cv. Wisconsin 38)](https://link.springer.com/article/10.1007/BF00387973) — Photosynthese-Typ C3
8. [Frontiers in Plant Science (PMC5121285) — Eucalyptus camaldulensis and herbaceous Nicotiana tabacum photosynthesis](https://pmc.ncbi.nlm.nih.gov/articles/PMC5121285/) — Tabak als krautige C3-Pflanze
9. [PMC5799153 — Effects of different growth temperatures on growth and development of tobacco](https://pmc.ncbi.nlm.nih.gov/articles/PMC5799153/) — Wuchsbeschränkung unter 10–13 °C (GDD-Wuchsbasis), Absterben bei 2–3 °C
10. [Kubien et al. 2008, Plant Cell & Environment — Temperature response of photosynthesis in tobacco with reduced Rubisco](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1365-3040.2008.01778.x) — Photosynthese-T_opt 30–32 °C (Netto-CO₂-Assimilation)
11. [NC State Extension — Tobacco Fertility / Nutrients & Manganese Deficiency](https://tobacco.ces.ncsu.edu/tobacco-fertility-nutrients/) — Mn-Blattgewebe-Suffizienz 20–250 ppm, Zn/Cu-Mangel selten
12. [Greg.app — Pollinating Tobacco](https://greg.app/pollinate-tobacco/) — Selbstbestäubung/Selbstfruchtbarkeit von N. tabacum
13. [FAO — Crop salt tolerance data (Annex 1)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Beleg, dass Tabak NICHT in der Maas-Hoffman-Salztoleranztabelle gelistet ist
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
14. [TrueLeafMarket — Ideal Germination Conditions for Tobacco Seeds](https://trueleafmarket.com/blogs/articles/ideal-germination-conditions-for-tobacco-seeds) — Keimtemperatur/-dauer, Lichtkeimer
15. [OnlineTobaccoSeedStore — Storing Your Seeds](https://www.onlinetobaccoseedstore.com/storing-your-seeds/) — Keimfähigkeitsdauer, Lagerungsempfehlungen
16. [Suppression of LOX activity enhanced seed vigour and longevity of tobacco (Nicotiana tabacum L.) seeds during storage, PMC6161406](https://pmc.ncbi.nlm.nih.gov/articles/PMC6161406/) — Langzeit-Keimfähigkeit bei Tiefkühllagerung (30–50+ Jahre bei -15/-18°C)
17. [CORESTA — Pre-chilling improves tobacco seed germination](https://www.coresta.org/abstracts/pre-chilling-improves-tobacco-nicotiana-tabacum-l-seed-germination-27921.html) — Optionale Vorkühlung als Keimförderung
18. [Weberseeds — Nicotiana tabacum, Tobacco](https://weberseeds.nl/eshop/en/Seeds/Seeds-A-Z/Nicotiana-tabacum-Tobacco::110.html) — Tausendkornmasse Cross-Check
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
