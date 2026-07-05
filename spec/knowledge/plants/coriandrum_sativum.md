# Koriander — Coriandrum sativum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Koriander pflanzen, COMPO Koriander, Gartenratgeber Koriander, Kiepenkerl Koriander, Fryd Koriander pflanzen

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Coriandrum sativum | `species.scientific_name` |
| Volksnamen (DE/EN) | Koriander, Korianderkraut; Coriander, Cilantro | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Coriandrum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4.4 (Kühljahreszeit-Apiaceae; Wert entspricht der kardinalen Minimaltemperatur der Keimung ≈ 4,37 °C nach Quelle #6 — eine separate Wuchs-GDD-Basis ist nicht eigenständig publiziert; ~4–5 °C ist als Wuchsbasis korpuskonsistent) | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (keine Vernalisation; fakultativer Langtagblüher) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | 12 (fakultativer Langtag; oberhalb ~12–14 h beschleunigtes Schossen) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | — (einjährig) | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt Leichtfrost bis ca. -5 °C; Aussaat ab April möglich; Herbstaussaat (September) für Überwinterung in milden Regionen; neigt bei langen Tagen und Wärme schnell zum Schossen | `species.hardiness_detail` |
| Heimat | Vorderasien, Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (keine Vorkultur; Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5, 6, 7, 8 (gestaffelt für kontinuierliche Ernte) | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9, 10 (Blätter; Samen August–Oktober) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 (weiße Doldenblüten; nach Schossen) | `species.bloom_months` |

**Sukzession:** Alle 3–4 Wochen nachsäen für kontinuierliche Blatternte. Koriander schosst schnell bei Wärme und langen Tagen — Schossen verringert Blattqualität (bitterer, weniger aromatisch).

**Nutzung:** Blätter = Frischkraut (Koriandergrün/Cilantro); Samen = Gewürz (Koriandersamen). Verschiedene Geschmacksprofile.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Koriander mag keine Verpflanzung (Pfahlwurzel). IMMER direkt säen, nicht vorziehen. Samenbeerenpaare (Doppelfrüchte) vor Aussaat auftrennen für bessere Keimung.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine (ätherische Öle; Linalool, Decyl-Aldehyd) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

**Hinweis:** Kontaktallergie möglich (Apiaceae-Querreaktion). Licht-Sensibilisierung durch Furanocumarine bei empfindlichen Personen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Keine Rückschnittmaßnahmen — Ernte durch Blätterernten (äußere Blätter). Bei Schossen: Blütenstand abschneiden verzögert Schossen etwas. Für Samenernte: Schossen erwünscht.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, durchlässige Kräutererde; pH 6,0–7,0; kein Staunässe; dünn säen | — |

**Für Blatternte:** Halbschattiger Standort bevorzugen (verzögert Schossen). **Für Samenernte:** Vollsonniger Standort.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> kein artspezifischer Messwert aus ≥2 seriösen Quellen | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade (Vollsonne bis Halbschatten; in heißen Lagen Halbschatten zur Schoss-Verzögerung) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 20–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (hohe Wurzelfäule-Gefahr bei „nassen Füßen“) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> nicht in FAO/Maas-Hoffman-Tabelle; vorhandene Studien beziehen sich auf Gießwasser-EC, nicht Substrat-ECe | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-Slope | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.2–6.8 | `species.soil_ph_preference` |

**Hinweis:** Klassifizierung *moderately_sensitive* gestützt auf Studien, in denen Koriander Gießwasser-EC bis ~2 dS/m ohne signifikanten Ertragsrückgang toleriert, darüber zunehmender Salzstress. Der pH-Vorzug 6,2–6,8 ist das Optimum innerhalb der in §1.6/§2.3 genannten verträglichen Spanne pH 6,0–7,0 (kein Widerspruch — Vorzug ⊂ Toleranzbereich).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 15 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 30 (Keimung generell 15–32°C möglich, Optimum 19–21°C bzw. bis 27°C für schnellere Keimung) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1.5 (½ inch ≈ 1.3 cm bis 2 cm Reihensaat) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (7–20 Tage, unterer Wert; abhängig von Temperatur) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (2–4 Jahre bei kühler, trockener, dunkler Lagerung in luftdichtem Behälter) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark | `species.seed_profile.light_germination` |
| Vorbehandlung | presoak, scarification (Einweichen 12–24 Std. und/oder Aufbrechen der Doppelfrucht/Mericarpien vor Aussaat verbessert Keimrate deutlich) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 10 (Spanne 7.6–13.6 g je nach Sorte/Studie, Mittelwert ~10 g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 200 (entspricht ca. 2,0 Mio. keimfähigen Samen/ha bei Reihensaat mit 30 cm Reihenabstand) | `species.seed_profile.sowing_density_per_m2` |

> **Hinweis:** Koriander ist ein Dunkelkeimer mit ausgeprägter Doppelfrucht (Mericarpium-Paar) — durch Zerdrücken/Aufbrechen der Fruchtschale vor der Aussaat wird die Keimrate deutlich erhöht (wirkt wie eine Skarifikation). Als Pfahlwurzler verträgt Koriander keine Verpflanzung — ausschließlich Direktsaat (siehe §1.3).

**Quellen (§1.8):**
- [Easyseeds — Coriandrum sativum (Coriander)](https://www.easyseeds.eu/en/coriandrum-sativum-coriander/) — Keimtemperatur 15–32°C, Dunkelkeimer, Saattiefe
- [analyzeseeds.com — Germination of Coriander Seed in 15C and 20-30C Temperatures (Laurie Conradson)](https://analyzeseeds.com/wp-content/uploads/2016/06/Germination_of_Coriander_Seed_in_15C_and_20-30C_2012.pdf) — ISTA-Prüftemperaturen 15°C und 20–30°C
- [ScienceDirect — Physical properties of coriander seeds](https://www.sciencedirect.com/science/article/abs/pii/S0260877406002226) und [Agronomy Society of NZ — Achievement of maximum seed yield in coriander](https://www.agronomysociety.org.nz/files/1997_8._Max_seed_yield_in_coriander.pdf) — Tausendkornmasse 7,6–13,6 g
- [ResearchGate — Effect of seed rate and sowing method on foliage production of coriander](https://www.researchgate.net/publication/360861385_EFFECT_OF_SEED_RATE_AND_SOWING_METHOD_ON_FOLIAGE_PRODUCTION_OF_DIFFERENT_GENOTYPES_OF_CORIANDER_Coriandrum_sativum_L) und [Province of Manitoba — Coriander](https://www.gov.mb.ca/agriculture/crops/crop-management/coriander.html) — Aussaatdichte 2,0–2,5 Mio. Samen/ha, Reihenabstand
- [Tower Landscape Design — How to Properly Store Coriander Seeds](https://towerlandscapedesign.com/how-to-store-coriander-seeds/) und [Todd's Seeds — How Long Do Coriander Seeds Last](https://toddsseeds.com/how-long-do-coriander-seeds-last/) — Keimfähigkeitsdauer 2–4 Jahre
- [Home Microgreens — Growing Cilantro From Seed: to Soak or Not to Soak](https://homemicrogreens.com/growing-cilantro-from-seed/) und [Matt Magnusson — Testing How To Best Germinate Coriander Seeds](https://mattmagnusson.com/germinate-coriander-seeds/) — Einweichen + Aufbrechen der Doppelfrucht (presoak + scarification)
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Jungpflanze | 14–21 | 2 | false | false | low |
| Vegetatives Wachstum (Ernte) | 30–60 | 3 | false | true | medium |
| Schossen / Blüte | 14–21 | 4 | false | true (Samen) | high |
| Samenreife | 21–35 | 5 | true | true (Samen) | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum (Blatternte)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 (halbschattig bis Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (kurze Tage verzögern Schossen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (VPD threshold, kPa) | 1.3 (kritischer Punkt stomatären Kollaps; oberer Zielwert 1,0 + ~0,3) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (photosynthesis temp optimum, °C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — |
| Vegetativ / Ernte | 1:0:1 | 0.4–0.8 | 6.0–7.0 | 60 | 30 | — | 1 |
| Blüte / Samen | 0:1:1 | 0.4–0.8 | 6.0–7.0 | 40 | 20 | — | 1 |

**Hinweis:** Zu viel Dünger verringert das Aroma! Koriander braucht mageren Boden für bestes Aroma. Kompost vor der Aussaat reicht völlig.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (ppm):**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) | KA-Feld |
|-------|----------|----------|----------|----------|---------|
| Vegetativ / Ernte | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm` |

Keine artspezifischen Mikronährstoff-Zielwerte (Mn/Zn/Cu/Mo) aus ≥2 seriösen Quellen für Koriander belegt; Werte daher offen gelassen statt zu schätzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif) | eigen | organisch | 1–2 L/m² | Vor Aussaat | Startdüngung |
| Kräuterdünger (niedrig dosiert) | Compo | organisch-mineralisch | 1/4 Empfehldosis | 1x im Monat | Topfkulturen |

### 3.2 Besondere Hinweise zur Düngung

Koriander im Beet braucht keinen extra Dünger — Kompost vor der Aussaat reicht. Im Topf monatlich sehr niedrig dosierter Kräuterdünger. Zu viel Stickstoff = kräftiger Wuchs, aber deutlich weniger Aroma.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig feucht; kein Staunässe; kein Laub benetzen bei Mehltaugefahr | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig; nicht umpflanzen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr–Mai | Erste Aussaat | Ab Mitte April (Direktsaat); ab Mitte Mai sicher | mittel |
| Apr–Aug | Nachsaaten | Alle 3–4 Wochen; gestaffelte Ernte | mittel |
| Laufend | Ernte | Äußere Blätter; Triebspitzen | hoch |
| Bei Schossen | Entscheidung | Blütenstand entfernen (Blätter) ODER stehen lassen (Samen) | mittel |
| Aug–Sep | Samenernte | Wenn Hüllen braun; Stiele trocknen lassen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schwarze Bohnenlaus | Aphis fabae | Kolonien an Triebspitzen; Honigtau | shoot | vegetative | easy |
| Weichwanzen | Lygus spp. | Saugschäden; Blattdeformation | leaf, shoot | vegetative | medium |
| Grüne Zikade | Empoasca spp. | Stippling (Punktfraß) auf Blättern | leaf | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trocken + warm; zu eng | 5–10 | vegetative |
| Falscher Mehltau (Doldenwelke) | fungal-like | Gelblich-braune Blätter; Dolden welken | Regenjahre; Feuchtigkeit | 7–14 | vegetative |
| Gelbwelke | bacterial (Pseudomonas) | Gelbe Blätter; Welken | Staunässe | 5–10 | alle |

**Hauptschutz:** Ausreichend Abstand (25–30 cm); gute Luftzirkulation; nicht zu viel gießen.

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Ausreichend Pflanzabstand | cultural | — | 25–30 cm Reihenabstand | 0 | Mehltau, Faulnis |
| Neemöl | biological | Azadirachtin | 0.5%; abends; Wartezeit bis Ernte! | 3 | Blattläuse |
| Insektenseife | biological | Kaliumsalze | Sprühen | 0 | Blattläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|-----------------------|---------------------|----------------|--------------|------------------|
| Marienkäfer (ladybird) | Adalia/Harmonia spp. | Blattläuse (Aphis fabae) | ~10 Adulte/m² (Gewächshaus) | ~1 Woche |
| Florfliege (green lacewing) | Chrysoperla carnea/rufilabris | Blattläuse | ~1 Larve/m² wöchentlich bis etabliert | 1–2 Wochen |
| Schlupfwespe (parasitic wasp) | Aphidius spp. | Blattläuse | ~1 Adult/15 m² | 2–3 Wochen (Mumienbildung) |

**Hinweis:** Werte für geschützten Anbau (Gewächshaus/Indoor). Im Freiland fördern Mischkultur und blühende Begleitpflanzen die natürliche Ansiedlung. Nützlingseinsatz mit Neemöl/Insektenseife abstimmen (Wartezeit beachten).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Kräuter / Apiaceae |
| Empfohlene Vorfrucht | Starkzehrer (Tomate, Kohl); Mittelzehrer |
| Empfohlene Nachfrucht | beliebig |
| Anbaupause (Jahre) | 3–4 Jahre zwischen Apiaceae (Karotte, Petersilie, Fenchel) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Gegenseitige Nützlingsförderung; Thrips-Abwehr | `compatible_with` |
| Kohl-Arten | Brassica oleracea | 0.8 | Schutz vor Kohlweißling | `compatible_with` |
| Thymian | Thymus vulgaris | 0.7 | Aromatische Abschirmung gegen Schädlinge | `compatible_with` |
| Oregano | Origanum vulgare | 0.7 | Gleiche Standortansprüche; Aromatische Synergie | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Alelopathische Hemmung; schlechte Nachbarschaft | moderate | `incompatible_with` |
| Liebstöckel | Levisticum officinale | Apiaceae-Familie; teilen Krankheiten/Schädlinge | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Hemmende Wirkung auf viele Kräuter | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Apiaceae | `shares_pest_risk` | Doldenwelke, Möhrenfliege (Psila rosae) | `shares_pest_risk` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months
Coriandrum sativum,"Koriander;Korianderkraut;Coriander;Cilantro",Apiaceae,Coriandrum,annual,long_day,herb,taproot,,0.1,"Vorderasien, Mittelmeerraum",yes,3,20,45,25,27,yes,yes,false,false,light_feeder,false,half_hardy,"4;5;6;7;8","5;6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Plantura — Koriander pflanzen](https://www.plantura.garden/kraeuter/koriander/koriander-pflanzen) — Standort, Aussaat
2. [COMPO — Koriander](https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/koriander) — Pflege, Düngung
3. [Gartenratgeber — Koriander](https://www.gartenratgeber.net/pflanzen/koriander.html) — Anbau, Pflege
4. [Kiepenkerl — Koriander Kulturanleitung](https://www.kiepenkerl.de/kulturanleitungen/koriander/) — Aussaatdaten
5. [Fryd — Koriander pflanzen](https://fryd.app/magazin/koriander-pflanzen) — Mischkultur
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [ResearchGate — Assessing Cardinal Temperature for Germination in Coriander (Coriandrum sativum)](https://www.researchgate.net/publication/273061347_Assessing_Cardinal_Temperature_for_Germination_in_Coriander_Coriandrum_sativum_Sainfoin_Onobrychis_vicifolia_and_Bitter_Vetch_Vicia_ervilia) — Kardinaltemperaturen (Basis ≈ 4,37 °C, Optimum ≈ 24,8 °C, Maximum ≈ 33,8 °C)
7. [USU Extension — Cilantro/Coriander in the Garden](https://extension.usu.edu/yardandgarden/research/cilantro-coriander-in-the-garden) — Standort (Vollsonne), Kühljahreszeit-Kultur, Schoss-Verhalten
8. [VeggieHarvest — Cilantro Growing and Harvest Information](https://veggieharvest.com/herbs/cilantro-growing-and-harvest-information/) — Wurzeltiefe (20–45 cm), Sonne/Halbschatten
9. [Springer — Growth and mineral content of coriander under mild salinity](https://link.springer.com/article/10.1007/s11738-018-2773-x) — Salztoleranz (Gießwasser-EC bis ~2 dS/m ohne signifikanten Rückgang)
10. [DPIRD NSW — Salinity tolerance in irrigated crops](https://www.dpird.nsw.gov.au/__data/assets/pdf_file/0005/523643/Salinity-tolerance-in-irrigated-crops.pdf) — Salztoleranz-Klassifizierung (moderately sensitive)
11. [Wisconsin Horticulture — Cilantro/Coriander](https://hort.extension.wisc.edu/articles/cilantro-coriander-coriandrum-sativum/) — fakultativer Langtagblüher, Schossen ab ~12–14 h Tageslänge + Wärme
12. [MDPI Horticulturae — Effects of Light Intensity and Photoperiod on Coriander](https://www.mdpi.com/2311-7524/10/3/215) — Photoperiode/Photosynthese, Schoss-Auslösung durch lange Tage
13. [Healthy Houseplants — Coriander (Cilantro) Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/coriander-cilantro-complete-care-guide-for-coriandrum-sativum/) — Staunässe-Empfindlichkeit, Drainage, pH 6,2–6,8
14. [UConn IPM — Biological Control of Aphids](https://ipm.cahnr.uconn.edu/ipm-biological-control-of-aphids/) — Nützlings-Ausbringraten/Etablierung
15. [MDPI Insects — Conditions for Successful Aphid Control by Ladybirds in Greenhouses](https://www.mdpi.com/2075-4450/8/2/38) — Marienkäfer ~10 Adulte/m², Etablierungszeit
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
