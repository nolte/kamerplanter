# Weihnachtskaktus — Schlumbergera truncata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardening Know How](https://www.gardeningknowhow.com/ornamental/cacti-succulents/christmas-cactus/advice-for-christmas-cactus-care.htm), [Old Farmer's Almanac](https://www.almanac.com/plant/christmas-cactus), [NCSU Extension](https://plants.ces.ncsu.edu/plants/schlumbergera/), [University of Minnesota Extension](https://extension.umn.edu/houseplants/holiday-cacti), [RHS](https://www.rhs.org.uk/plants/christmas-cactus/how-to-grow)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Schlumbergera truncata | `species.scientific_name` |
| Volksnamen (DE/EN) | Weihnachtskaktus, Gliederkaktus; Thanksgiving Cactus, Crab Cactus, Lobster Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Schlumbergera | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN — kein belegter Wuchs-/Phänologie-GDD-Basiswert auffindbar; vorhandene Studien (ISHS 'Madisto') modellieren temperaturabhängige Blühinitiation zwischen 12–24°C, liefern aber keine umetikettierbare GDD-Wuchsbasis --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 20–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Ruheperiode nach der Blüte wichtig für nächste Blütenbildung) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Anmerkung: streng genommen kühl-induzierter Blühreiz / „chilling", kein klassischer Vernalisationsbedarf — Nachttemperaturen 10–15°C plus Kurztag induzieren die Blüte) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindestdauer (Tage) | 42–56 | `lifecycle_configs.vernalization_min_days` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (critical day length, h) | 12 (Kurztagblüher: Blüteninduktion bei ≤ 12 h Licht bzw. ≥ 13 h ununterbrochener Dunkelheit über ~6 Wochen) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart (tropischer Epiphyt). Optimal 18–24°C; zur Blüteninduktion 10–15°C für 6–8 Wochen. | `species.hardiness_detail` |
| Heimat | Brasilianisches Küstengebirge (Serra dos Órgãos, Rio de Janeiro) — feuchte Bergwälder, epiphytisch auf Bäumen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Physiologie (CAM):** *Schlumbergera* betreibt CAM-Photosynthese (Crassulacean Acid Metabolism). Als tropischer Epiphyt öffnet sie ihre Spaltöffnungen (stomata) überwiegend nachts (CO₂-Fixierung über PEPC, Speicherung als Apfelsäure/Malat), um Wasserverluste im luftigen Baumkronen-Standort zu minimieren. Konsequenz für die Pflege: geringe VPD-Sensitivität, Trockenheitstoleranz, aber empfindlich gegen Staunässe (waterlogging).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis Taxonomie:** Im Handel oft fälschlicherweise als *Schlumbergera x buckleyi* (echter Weihnachtskaktus, runde Gliedersegmente) verkauft, obwohl es sich überwiegend um *S. truncata* (Thanksgiving-Kaktus, gezackte Segmente) handelt. Beide Arten sehr ähnlich in der Pflege; *S. truncata* blüht etwas früher (November) als *S. x buckleyi* (Dezember/Januar). Im Volksmund werden beide "Weihnachtskaktus" genannt.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 11, 12, 1 (Kurztag+Kühlreiz-induzierte Winterblüte; Blühbeginn typischerweise Mitte/Ende November, verifiziert 2026-07) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Glieder-Stecklinge: 2–3 Segmente abdrehen (nicht abschneiden) und 1–2 Tage antrocknen lassen. Dann in feuchtes Kakteensubstrat stecken. Bewurzelung 3–4 Wochen bei 20–22°C. Stecklinge im Frühsommer nehmen (nach der Blüte, Frühling).

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

**Hinweis:** Schlumbergera gilt als nicht giftig — ideal für Haushalte mit Haustieren. Bei Hunden und Katzen können große Mengen zu leichter Übelkeit führen, aber keine ernsthaften Vergiftungen bekannt.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 (nach der Blüte) | `species.pruning_months` |

**Hinweis:** Nach der Blüte: Überlange Triebe zurückdrehen (keine Schere — Glieder an Verbindungsstellen abdrehen). Fördert buschigen Wuchs und mehr Blütenansätze im nächsten Jahr.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 (hängend bis 60) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer Halbschatten; Blüteninduktion im Herbst begünstigt durch kühle Nächte draußen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Orchideen-/Epiphytensubstrat (Pinienrinde + Perlite + Torf) oder leichte Kakteenerde mit Perlite. pH 5.5–6.5. Lockeres, luftiges Substrat wichtig (epiphytische Natur). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) | 10–25 (typischer Bereich schattenadaptierter Epiphyten; kein artspezifisch gemessener Schlumbergera-Wert publiziert — als Spanne für CAM-Schattenpflanzen unter Kronendach, nicht der Sättigungs-/Optimumwert) | `species.light_compensation_point_ppfd_min` / `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 10–15 (flaches, fibröses Wurzelwerk; breiter Topf besser als tiefer) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (Epiphyt; Glieder-/Wurzelfäule bei stehender Nässe) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive (Epiphyt; Salzanreicherung im Substrat verbrennt Wurzeln, regelmäßiges Ausspülen nötig) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-a-Wert (ECe-Schwelle) für Schlumbergera publiziert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN — kein belegter Maas-Hoffman-b-Wert publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 5.5–6.5 (leicht sauer; vigoröser bei pH 5.5–6.2) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–180 | 1 | false | false | medium |
| Ruheperiode (August/September) | 30–45 | 2 | false | false | high |
| Blüteninduktion (kurze Tage + Kühle) | 42–56 | 3 | false | false | medium |
| Vollblüte | 45–90 | 4 | false | false | low |
| Nachblüteruhe | 30–45 | 5 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–August)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 (kritischer Punkt deutlich oberhalb des Zielkorridors; oberer Zielwert 1.0 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low (CAM-Epiphyt) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 21–27 (warme Wuchssaison Apr–Sep) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 (helles indirektes Licht / Halbschatten unter Kronendach; FR-angereichert) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüteninduktion (September–Oktober — KRITISCH)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 (maximal! Mehr verhindert Blüte!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (kühle, eher feuchteliebende Induktionsphase → niedrigere Schwelle als Wuchsphase) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low (CAM-Epiphyt) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 (Blühinitiation, Optimum ~20°C nach ISHS 'Madisto') | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 (Halbschatten unter Kronendach) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vollblüte (November–Januar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–14 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low (CAM-Epiphyt; Knospenfall jedoch durch abrupte Standort-/Klimawechsel) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 (warm halten; keine Hitze > 32°C bei Knospen) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 1:1:1 | 0.6–1.0 | 5.5–6.5 | 80 | 30 | 0.2–0.3 | 0.02–0.05 | 0.01–0.02 | 0.005–0.01 |
| Ruheperiode | 0:0:0 | 0.0 | 5.5–6.5 | — | — | — | — | — | — |
| Blüteninduktion | 0:2:1 (P-betont) | 0.4–0.6 | 5.5–6.5 | 60 | 20 | 0.15–0.25 | 0.02–0.04 | 0.01 | 0.005 |
| Vollblüte | 0:1:1 | 0.4–0.6 | 5.5–6.5 | 60 | 20 | 0.15–0.25 | 0.02–0.04 | 0.01 | 0.005 |
| Nachblüteruhe | 0:0:0 | 0.0 | 5.5–6.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Für *Schlumbergera* sind keine artspezifischen Mikronährstoff-Konzentrationen publiziert. Die o.g. ppm-Werte sind als Schwachzehrer-Richtwerte (≈ 30–50 % einer Standard-Hoagland-Vollnährlösung: Mn 0.5 / Zn 0.05 / Cu 0.02 / Mo 0.01 mg/L) angesetzt — Epiphyten nehmen Mikronährstoffe nur in geringen Mengen auf, ein handelsüblicher Kakteen-/Orchideendünger mit Spurenelementen deckt den Bedarf. KA-Felder: `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Aktives Wachstum → Ruheperiode | time_based | August; Wässern reduzieren, kein Dünger |
| Ruheperiode → Blüteninduktion | event_based | September; Tageslicht < 12h; Nachtkühle < 15°C |
| Blüteninduktion → Vollblüte | event_based | Knospenbildung sichtbar; Standort NICHT mehr wechseln! |
| Vollblüte → Nachblüteruhe | time_based | Nach Ende der letzten Blüte (Jan/Feb) |
| Nachblüteruhe → Aktives Wachstum | time_based | März; Düngung und Gießen wieder aufnehmen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Compo | base | 5-8-10 | 5 ml/L (alle 2 Wochen) | Wachstum, Blüteninduktion |
| Kakteen-Dünger | Substral | base | 3-6-7 | 5 ml/L | Wachstum |
| Orchideen-Dünger (halbverdünnt) | Compo | base | 7-5-6 | 3 ml/L | Wachstum (Epiphyten-Ernährung) |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10–15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Schwachzehrer. Im Sommer alle 2 Wochen Dünger (ganzjährig außer Ruheperioden). Ab August bis Knospenentwicklung kein Dünger — dann bis Blüteende monatlich. Überdüngung verhindert Blüte. Wichtigstes Pflegewissen: Für Blüte sind Kurztag + Kühle ausschlaggebend, nicht Düngung!

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt (kalkarm); abgestandenes Leitungswasser; kein kaltes Wasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 (nach der Blüte, im Frühling) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Nachblüteruhe | Gießen stark reduzieren, kein Dünger | hoch |
| Mär | Wachstum reaktivieren | Düngung starten, Gießen normalisieren | mittel |
| Apr–Mai | Schnitt/Stecklinge | Überlange Triebe zurückdrehen; Stecklinge gewinnen | mittel |
| Mai–Jul | Sommer-Pflege | Regelmäßig wässern und düngen (alle 2 Wochen) | mittel |
| Aug | Sommer-Pause | Gießen reduzieren, Düngen stoppen (Ruhevorbereitung) | hoch |
| Sep | KURZTAG-KÜHLREIZ | Standort mit max. 12h Licht und Nachttemperatur 10–15°C | KRITISCH |
| Okt–Nov | Knospen entwickeln | Standort NICHT wechseln, Blüten fallen sonst ab | hoch |
| Nov–Jan | Vollblüte | Gleichmäßig wässern, monatlich düngen, warm stellen | mittel |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (spätestens vor erstem Frost / ab September für Kühlreiz draußen, dann hereinholen) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 (nach den Eisheiligen, Halbschatten) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–15 (Induktion Sep–Okt), danach 18–22 (Blüte) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; Sep–Okt ≤ 12 h Tageslicht (keine künstliche Beleuchtung am Abend) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam (Induktionsphase 14–21 Tage Intervall), zur Blüte wieder gleichmäßig feucht | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Nicht frosthart (tropischer Epiphyt, USDA 10–12). In Mitteleuropa (USDA 6–8) ausschließlich frostfreie Überwinterung im Haus. Eine kühle, kurztägige Phase im September/Oktober (Nachttemperatur 10–15°C, z.B. auf der Fensterbank eines ungeheizten Raums oder geschützt draußen vor erstem Frost) ist Voraussetzung für die Blütenbildung. Nach Knospenbildung Standort nicht mehr wechseln (Knospenfall).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Glieder schrumpfen | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Gelenken | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Gliederfäule | fungal (Fusarium) | Glieder werden weich, glasig | Überbewässerung |
| Wurzelfäule | fungal | Welke Glieder trotz feuchtem Substrat | Staunässe |
| Knospenfall | physiologisch | Knospen fallen vor Aufblühen ab | Standortwechsel, Zugluft, Temperaturschwankung, Trockenheit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.3% (Blüten schützen!) | 0 Tage | Spinnmilbe, Schmierläuse |
| Drainage verbessern | cultural | Durchlässigeres Substrat, kein Untersetzer-Staunasser | 0 | Wurzelfäule |
| Stabile Lage | cultural | Keine Standortwechsel nach Knospenbildung | 0 | Knospenfall (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–5 Käfer/m² (bzw. 1 Käfer je befallene Pflanze) | 2–4 Wochen |
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 2–6 Milben/m² (Befallsherde gezielt) | 2–3 Wochen |
| Zehrwespe | Metaphycus helvolus | Weiche Schildläuse / Braune Weichschildlaus (Coccus hesperidum, soft brown scale) | 1–3 Wespen/m² | 3–4 Wochen |
| Insektenpathogener Nematode | Steinernema feltiae | Trauermücken-Larven (Sciaridae, im Substrat) | 0.5 Mio./m² (50 000/m² Gießanwendung) | 1–2 Wochen |

**Hinweis:** Innenraum-/Interior-Plantscape-tauglich. *Cryptolaemus* überlebt keinen Frost und ist daher für die ganzjährige Zimmerkultur gut geeignet. Raubmilben und Schlupfwespen benötigen ausreichende Luftfeuchte (> 50 %) und Temperaturen über 18°C — in der warmen Wuchssaison gegeben. Während der Vollblüte sparsam und gezielt einsetzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Echter Weihnachtskaktus | Schlumbergera x buckleyi | Gleiche Gattung, runde Gliedersegmente | Blüht later (Dezember/Januar) = näher an Weihnachten |
| Osterkaktus | Hatiora gaertneri | Gleiche Familie | Blüht Frühling (April) |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Schlumbergera truncata,"Weihnachtskaktus;Gliederkaktus;Thanksgiving Cactus;Crab Cactus",Cactaceae,Schlumbergera,perennial,short_day,herb,fibrous,"10a;10b;11a;11b","Brasilianisches Küstengebirge",yes,1-5,12,20-60,30-60,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardening Know How — Christmas Cactus](https://www.gardeningknowhow.com/ornamental/cacti-succulents/christmas-cactus/advice-for-christmas-cactus-care.htm) — Pflegehinweise
2. [Old Farmer's Almanac](https://www.almanac.com/plant/christmas-cactus) — Blüteninduktion, Saisonkalender
3. [NCSU Extension — Schlumbergera](https://plants.ces.ncsu.edu/plants/schlumbergera/) — Botanische Einordnung
4. [University of Minnesota Extension](https://extension.umn.edu/houseplants/holiday-cacti) — Kurztag-Protokoll
5. [Royal Horticultural Society](https://www.rhs.org.uk/plants/christmas-cactus/how-to-grow) — Kulturempfehlungen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Wikipedia — Crassulacean acid metabolism](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Photosynthese, Epiphyten-Adaptation
7. [Caudexology — Crab Cactus Care: The Science of Schlumbergera Physiology](https://caudexology.com/2026/01/06/crab-cactus-care-the-science-of-schlumbergera-physiology-and-chemistry/) — CAM bei Schlumbergera, nächtliche Stomata, PEPC/Malat
8. [Missouri Botanical Garden — Schlumbergera truncata Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b669) — Part shade, kritische Tageslänge/Langnacht, USDA-Zonen 10–12, Winterpflege, Substrat
9. [Clemson HGIC — Thanksgiving & Christmas Cacti](https://hgic.clemson.edu/factsheet/thanksgiving-christmas-cacti/) — Lichtschatten (partial shade), Temperatur Wuchs/Blüte, Schädlingsliste
10. [ISHS Acta Horticulturae 272 — Temperature Effects Schlumbergera truncata 'Madisto' Flower Initiation](https://ishs.org/ishs-article/272_13/) — Blühinitiations-Optimum ~20°C, Temperaturmodell 12–24°C
11. [What Grows There — Photoperiodism Short Day/Long Day Plants](https://whatgrowsthere.com/grow/2016/12/07/photoperiodism-short-daylong-day-plants/) — Kurztag-Schwelle ~12 h / 13 h Dunkelheit
12. [Gardening Know How — Christmas Cactus Soil](https://www.gardeningknowhow.com/ornamental/cacti-succulents/christmas-cactus/christmas-cactus-soil.htm) — pH 5.5–6.5, epiphytisches Substrat, Salzanreicherung ausspülen
13. [Gardener's Path — Christmas Cactus Roots](https://gardenerspath.com/plants/houseplants/christmas-cactus-roots/) — flaches, fibröses Wurzelwerk, Staunässe-Empfindlichkeit
14. [RHS — Biological Control in the Garden](https://www.rhs.org.uk/prevention-protection/biological-control-garden) — Cryptolaemus, Phytoseiulus persimilis, Metaphycus, Steinernema feltiae Nützlinge
15. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Referenz-Mikronährstoffkonzentrationen Mn/Zn/Cu/Mo
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: growing-phase-auditor 2026-07 (Lebenszyklus-Audit §1.1/§1.2/§2/§4.3) -->
16. [NC State Extension Gardener Plant Toolbox — Schlumbergera truncata](https://plants.ces.ncsu.edu/plants/schlumbergera-truncata/) — Blüte "late November", Rebloom Februar, perennial, USDA 10–12, Stammstecklinge
17. [Clemson HGIC — Thanksgiving & Christmas Cacti](https://hgic.clemson.edu/factsheet/thanksgiving-christmas-cacti/) — Thanksgiving-Kaktus blüht "near Thanksgiving" (Ende Nov), 14h Dunkelheit ab Mitte September für 6 Wochen, Frostgrenze < 50°F, Vermehrung 3–5 Glieder/Steckling
18. [Wisconsin Horticulture Extension — Holiday Cactus](https://hort.extension.wisc.edu/articles/holiday-cactus/) — Gattung blüht "early November into January", Kühlreiz 55–60°F + Kurztag, keine Frosttoleranz, Glied-Stecklinge 2–3 Segmente
19. [Farmers' Almanac — Thanksgiving vs. Christmas Cactus](https://www.farmersalmanac.com/thanksgiving-cactus-christmas-cactus) — Thanksgiving-Kaktus "Bloom mid to late November", Christmas-Kaktus "mid to late December"
<!-- /Quelle: growing-phase-auditor 2026-07 -->
