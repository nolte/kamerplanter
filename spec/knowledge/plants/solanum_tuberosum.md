# Kartoffel — Solanum tuberosum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Wikipedia Kartoffel, Plantura Frühkartoffeln, Bio-Gärtner.de, LfL Bayern

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Solanum tuberosum | `species.scientific_name` |
| Volksnamen (DE/EN) | Kartoffel, Erdapfel; Potato | `species.common_names` |
| Familie | Solanaceae | `species.family` → `botanical_families.name` |
| Gattung | Solanum | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 7 | `species.base_temp` |
| Lebensdauer (Jahre) | — (einjährig kultiviert) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (Knollendormanz vor Austrieb) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 12 (Knollenansatz wird durch Kurztag gefördert; moderne Sorten weitgehend tagneutral, Tuberisation aber durch Tageslängen < ca. 12 h beschleunigt) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Knollen nicht frosthart; Kraut stirbt bei −1 °C; Pflanzknollen im Freiland ab Bodentemperatur 8 °C | `species.hardiness_detail` |
| Heimat | Südamerika, Andenhochland (Peru, Bolivien) | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Vorkeimen ab März) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0–14 (Bodentemperatur mind. 8 °C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Frühkartoffel ab Juni, Spätkartoffel Oktober) | `species.harvest_months` |
| Blütemonate | 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | tuber (Pflanzknollen), seed (selten, für Züchtung) | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Blätter, Stängel, unreife und grüne Knollen, Beeren | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Solanin, Chaconin (Glykoalkaloid) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none (Kraut wird nach der Ernte kompostiert) | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Kübel mind. 40 L, Kartoffelsack) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–35 cm in Reihe, 70–80 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Kartoffelsack) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, sandig-lehmige Erde mit hohem Humusanteil, pH 5,5–6,5; kein Frischdünger | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (Vorkeimen) | 14–21 | 1 | false | false | low |
| Auflaufen & Sämling | 14–21 | 2 | false | false | low |
| Vegetativ (Krautwachstum) | 28–42 | 3 | false | false | medium |
| Knollenansatz | 21–35 | 4 | false | false | medium |
| Knollenfüllung & Reife | 28–56 | 5 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vorkeimen

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 (heller, kühler Raum) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.7 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | — (trocken lagern) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Krautwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 (Volllsonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Knollenansatz & Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (Kurztagsreaktion fördert Knollenansatz) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (gleichmäßige Feuchte wichtig — Stippigkeit vermeiden) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Vorkeimen | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
| Vegetativ | 3:1:2 | 1.5–2.0 | 5.5–6.5 | 100 | 50 | 30 | 3 | 0.62 | 0.11 | 0.02 | 0.05 |
| Knollenansatz | 1:2:3 | 1.5–2.5 | 5.5–6.5 | 100 | 60 | 30 | 2 | 0.62 | 0.11 | 0.02 | 0.05 |
| Reife | 0:1:2 | 1.0–1.5 | 5.5–6.5 | 80 | 40 | — | 1 | 0.5 | 0.1 | 0.02 | 0.05 |
<!-- KA-Felder: nutrient_profiles.manganese/zinc/copper/molybdenum_ppm — Nährlösungs-Zielwerte nach Steiner-Universallösung (100 %) -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Vorkeimen → Auflaufen | time_based | 14–21 Tage | Keimsprossen 1–3 cm sichtbar |
| Auflaufen → Vegetativ | time_based | 14–21 Tage | Triebe 10–15 cm, Zeit zum Anhäufeln |
| Vegetativ → Knollenansatz | event_based | Blüte sichtbar | Erster Blütenknopf sichtbar |
| Knollenansatz → Reife | time_based | 28–56 Tage | Kraut beginnt einzuziehen |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN — kein artspezifischer Beleg aus 2 Quellen --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN — kein artspezifischer Beleg aus 2 Quellen --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun (mind. 6–8 h Direktsonne; im Schatten kaum Knollenbildung) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 40–60 (FAO: 100 % Wasseraufnahme aus oberen 0,4–0,6 m, 70 % aus oberen 0,3 m) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (Staunässe fördert Knollenfäule/Wurzelfäule) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 1.7 (Substrat-ECe, Maas-Hoffman a) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 12 (Maas-Hoffman b) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.0–6.5 (FAO-Optimum 5,0–6,0; obere Grenze zur Schorf-Vermeidung möglichst unter 6,0 halten — konsistent mit §1.6/§3.3) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Feld/Hochbeet)

| Produkt | Marke | Typ | NPK | Ausbringrate | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Kartoffeldünger granuliert | Compo | base | 7-5-16+2MgO | 80–100 g/m² | 1 | Pflanzung |
| Kali-Magnesia (Patentkali) | K+S | supplement | 0-0-30+10MgO | 50–80 g/m² | 2 | Knollenansatz |

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 5–8 L/m² | Herbst/Frühjahr | Bodenverbesserung |
| Hornspäne | Oscorna | organisch-N | 80–100 g/m² | Pflanzung | Stickstoffversorgung |
| Kali-Hornmehl | diverse | organisch | 60–80 g/m² | Pflanzung | Grunddüngung |

### 3.2 Düngungsplan (Freiland)

| Zeitpunkt | Maßnahme | Produkt | Menge | Hinweise |
|-----------|---------|---------|-------|----------|
| Herbst/Frühjahr | Bodenverbesserung | Kompost | 5–8 L/m² | Einarbeiten |
| Pflanzung (April) | Grunddüngung | Hornspäne + Patentkali | je 60 g/m² | In Furche oder ums Pflanzloch |
| Anhäufeln (Mai) | Stickstoff-Nachschub | Hornmehl | 40 g/m² | Oberflächlich einarbeiten |
| Knollenansatz (Juni) | Kalium-Boost | Patentkali | 30 g/m² | Fördert Stärkeeinlagerung |

### 3.3 Besondere Hinweise zur Düngung

Kartoffeln reagieren empfindlich auf frischen Stallmist (fördert Schorf). Kein Kalk direkt vor dem Anbau (erhöht Schorf-Risiko, pH unter 6,0 halten). Hoher Kalibedarf in der Knollenfüllungsphase. Stickstoffüberschuss führt zu üppigem Krautwachstum auf Kosten der Knollen. Magnesiumdüngung (Patentkali) ist wichtig für Chlorophyllbildung und Stärketransport.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkwasser verträglich; gleichmäßige Feuchte wichtig gegen Stippigkeit | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21–28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Saatgut bestellen | Pflanzkartoffeln (zertifiziert) kaufen | mittel |
| Mär | Vorkeimen | Pflanzkartoffeln hell und kühl (10–15 °C) auskeimen lassen | hoch |
| Apr | Pflanzen | Wenn Boden 8 °C, in Furchen 8–10 cm tief legen | hoch |
| Mai | Anhäufeln (1.) | Triebe bis auf 10 cm mit Erde abdecken — schützt vor Spätfrösten | hoch |
| Mai | Anhäufeln (2.) | 2–3 Wochen nach erstem Anhäufeln wiederholen | hoch |
| Jun | Bewässerung | Gleichmäßig feucht halten, Austrocknen vermeiden | mittel |
| Jun–Jul | Frühkartoffel-Ernte | Wenn Kraut gelblich: Frühsorten ernten | mittel |
| Aug–Sep | IPM-Kontrolle | Krautfäule täglich beobachten; befallenes Kraut sofort entfernen | hoch |
| Sep–Okt | Haupternte | Kraut abschneiden, 2 Wochen warten, dann Knollen ernten | hoch |
| Okt–Nov | Bodenverbesserung | Kompost oder Gründüngung für nächste Saison einarbeiten | mittel |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-07 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | dig_and_store | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | dig_store (Knollen nach dem Absterben des Krauts ausgraben und frostfrei einlagern) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, Haupternte) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | replant (vorgekeimte Pflanzkartoffeln auslegen) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 4 (April) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 4 (unter 4 °C Erfrierungsgefahr) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 8 (über 8–10 °C treiben Knollen vorzeitig aus) | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark (dunkel lagern; Licht führt zu Ergrünen/Solanin) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | none (trocken lagern; Lagermedium nur bei Schrumpeln minimal anfeuchten) | `overwintering_profiles.winter_watering` |
| Lagermedium | dunkler, frostfreier Keller in luftigen Kisten (nicht neben Äpfeln/Ethylen) | `overwintering_profiles.storage_medium` |
| Lager-Kontrollintervall (Tage) | 30 (monatlich auf Fäulnis/Keimung prüfen) | `overwintering_profiles.storage_check_interval_days` |
| Knollen-Status | stored | `overwintering_profiles.tuber_status` |

**Hinweise zu §4.3:**
- Die Kartoffel ist frostempfindlich (`tender`); nur die Knolle überwintert, die Pflanze stirbt ab. Daher `dig_and_store`: Knollen ausgraben und frostfrei (4–8 °C), dunkel und trocken einlagern.
- Während des Wachstums schützt das **Anhäufeln** (`earth_up`, Mai) die Triebe vor Spätfrösten — das ist eine Kultur-, keine Überwinterungsmaßnahme.
- Speisekartoffeln nicht neben Äpfeln lagern (Ethylen fördert Keimung). Pflanzkartoffeln im März hell und kühl **vorkeimen** (`pre_sprouting`) vor dem Auslegen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kartoffelkäfer | Leptinotarsa decemlineata | Kahlfraß an Blättern, orange-schwarz gestreifte Käfer und rote Larven | leaf | vegetative, flowering | easy |
| Blattläuse | Myzus persicae u.a. | Kräuseln, Honigtau, Virusübertragung | leaf, stem | seedling, vegetative | medium |
| Drahtwurm | Agriotes spp. | Fraßgänge in Knollen | root | ripening | difficult |
| Kartoffelnematode | Globodera rostochiensis | Kümmerwuchs, Knollensterben | root | all | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kraut- und Braunfäule | fungal (Oomycet) | Braune, ölige Flecken auf Blättern, weißer Sporenrasen unterseitig; Knollenfäule | Feuchtigkeit >90%, 15–22 °C | 3–7 | vegetative, ripening |
| Echter Schorf | bacterial (Streptomyces scabies) | Korkige Warzenhaut auf Knollen | pH >6.0, Trockenheit nach Pflanzung | 14–21 | ripening |
| Schwarzbeinigkeit | bacterial (Pectobacterium) | Schwarze Stängelbasis, Welke, Fäule | Nässe, Wunden | 5–14 | vegetative |
| Virosen (Y, X, S) | viral | Mosaikmuster, Kräuseln, Stauchung | Blattlausübertragung | variabel | seedling, vegetative |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Steinernema feltiae (Nematoden) | Drahtwurm | 500.000/m² | 14–21 |
| Marienkäfer (Coccinella septempunctata) | Blattläuse | 5–10 | 7–14 |
| Florfliege (Chrysoperla carnea) | Blattläuse | 5–10 | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Absammeln | mechanical | — | Täglich Käfer und Eipakete absammeln | 0 | Kartoffelkäfer |
| Spinosad | biological | Spinosad | Sprühen, 0.024% | 3 | Kartoffelkäfer-Larven |
| Kupferpräparat (Cuprozin) | chemical | Kupferhydroxid | Sprühen, 3 kg/ha, max. 3× | 7 | Kraut- und Braunfäule |
| Mulchen | cultural | — | Strohdecke 5–8 cm | 0 | Bodenfeuchtigkeit, Schorf |
| Fruchtfolge | cultural | — | 3–4 Jahre keine Solanaceen | 0 | Nematoden, Schorf, Kartoffelkäfer |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| — (sortenabhängig; Sorte 'Sarpo Mira' extrem krautfäuleresistent) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Nachtschattengewächse (Solanaceae) |
| Empfohlene Vorfrucht | Hülsenfrüchte (Leguminosen), Kleegras |
| Empfohlene Nachfrucht | Wurzelgemüse (Möhre, Pastinake), Salat, Spinat |
| Anbaupause (Jahre) | 3–4 Jahre selbe Familie (Solanaceae) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Meerrettich | Armoracia rusticana | 0.8 | Soll Kartoffelkäfer abhalten | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Insektenabwehr | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Ablenkpflanze | `compatible_with` |
| Bohnenkraut | Satureja hortensis | 0.7 | Vertreibt Kartoffelkäfer | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Gleiche Krankheiten (Phytophthora), erhöhtes Infektionsrisiko | severe | `incompatible_with` |
| Aubergine | Solanum melongena | Gleiche Familie, gleiche Schädlinge | severe | `incompatible_with` |
| Paprika | Capsicum annuum | Gleiche Familie | moderate | `incompatible_with` |
| Kürbis | Cucurbita maxima | Konkurrenz um Nährstoffe und Platz | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Solanaceae | `shares_pest_risk` | Phytophthora, Kartoffelkäfer, Nematoden | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Kartoffel |
|-----|-------------------|-------------|------------------------------|
| Topinambur | Helianthus tuberosus | Knollengemüse, ähnliche Kultur | Winterhart, kein Krautfäule-Risiko, mehrjährig |
| Süßkartoffel | Ipomoea batatas | Knollengemüse | Kein Solanin; andere Familie |
| Rote Bete | Beta vulgaris | Wurzelgemüse | Sehr robust, kaum Krankheiten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Solanum tuberosum,"Kartoffel;Erdapfel;Potato",Solanaceae,Solanum,annual,short_day,herb,tuberous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",-0.1,"Südamerika, Andenhochland",limited,50,40,80,60,35,no,limited,false,false,heavy_feeder,tender,"3;4;5","6;7;8;9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Belana,Solanum tuberosum,Böhm-Nordkartoffel,2000,"festkochend;high_yield",95,,open_pollinated
Linda,Solanum tuberosum,Böhm-Nordkartoffel,1974,"festkochend;classic",110,,open_pollinated
Sarpo Mira,Solanum tuberosum,Sárvári Research Trust,2002,"late;phytophthora_resistant",140,phytophthora,open_pollinated
Annabelle,Solanum tuberosum,Agrico,2003,"very_early;festkochend",75,,open_pollinated
```

---

## Quellenverzeichnis

1. [Kartoffel — Wikipedia](https://de.wikipedia.org/wiki/Kartoffel) — Taxonomie, Inhaltsstoffe, Geschichte
2. [Frühkartoffeln: Sorten, Anbau & Ernte — Plantura](https://www.plantura.garden/gemuese/kartoffeln/fruehkartoffeln) — Anbaupraxis
3. [Kartoffeln — Der Bio-Gärtner](https://www.bio-gaertner.de/Pflanzen/Kartoffeln) — Bio-Anbau, Fruchtfolge
4. [LfL Bayern — Krautfäule](https://www.lfl.bayern.de/) — Phytophthora, IPM
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [FAO Land & Water — Potato Crop Information](https://www.fao.org/land-water/databases-and-software/crop-information/potato/en/) — Effektive Wurzeltiefe (0,4–0,6 m), Boden-pH (5–6), optimale Temperaturen
6. [Shannon & Grieve — Tolerance of vegetable crops to salinity (USDA-ARS)](https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P1567.pdf) — Salztoleranz, Maas-Hoffman-Parameter
7. [Salt tolerance of crops — Wikipedia](https://en.wikipedia.org/wiki/Salt_tolerance_of_crops) — Bestätigung Kartoffel ECe-Schwelle 1,7 dS/m, Slope 12 %/dS/m (moderately sensitive)
8. [Effects of Light, CO₂ and Temperature on Photosynthesis in Solanum tuberosum — Plant Physiol. (PubMed 16659958)](https://pubmed.ncbi.nlm.nih.gov/16659958/) — C3-Stoffwechsel, Photosynthese-Temperaturoptimum 16–25 °C
9. [Crop physiology of potato: responses to photoperiod and temperature — Springer](https://link.springer.com/chapter/10.1007/978-94-011-0051-9_2) — Kurztag-Förderung der Tuberisation, Entwicklungs-Basistemperatur
10. [The Five Key Stages of Potato Growth — ScienceInsights](https://scienceinsights.org/the-five-key-stages-of-potato-growth/) — Basistemperatur/Schwelle ~7 °C (45 °F) für Wachstum
11. [Calculating Growing Degree Days — Potato Grower Magazine](https://www.potatogrower.com/2022/06/calculating-growing-degree-days) — GDD-Berechnung Kartoffel
12. [Steiner, A.A. (1961) A Universal Method for Preparing Nutrient Solutions — Plant and Soil 15:134-154](https://www.scirp.org/reference/referencespapers?referenceid=1818327) — Mikronährstoff-Zielwerte Nährlösung (Mn 0,62; Zn 0,11; Cu 0,02; Mo 0,05 ppm)
13. [Secondary and Micro-nutrients for Vegetable and Field Crops — MSU Extension E486](https://www.canr.msu.edu/resources/secondary_and_micro_nutrients_for_vegetable_and_field_crops_e486) — Mikronährstoff-Suffizienzbereiche (Blattgewebe) zur Plausibilisierung
14. [The R to FR Ratio — Greenhouse Product News](https://gpnmag.com/article/r-fr-ratio/) — R:FR ≈ 1,1–1,4 bzw. FR-Fraction ≈ 0,5 in offenem Tageslicht/Vollsonne
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
