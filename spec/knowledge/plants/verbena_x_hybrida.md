# Garten-Verbene — Verbena × hybrida

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Royal Horticultural Society, University of Florida IFAS Extension, USDA PLANTS Database, Ball Horticulture Verbena Production Guide, Bayerische Gartenakademie

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Verbena × hybrida | `species.scientific_name` |
| Volksnamen (DE/EN) | Garten-Verbene, Eisenkraut; Garden Verbena, Annual Verbena | `species.common_names` |
| Familie | Verbenaceae | `species.family` → `botanical_families.name` |
| Gattung | Verbena | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial (botanisch kurzlebige/frostzarte Staude); in Mitteleuropa einjährig kultiviert | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Anbau-Zyklustyp (cultivation cycle type) | annual | `lifecycle_configs.cultivation_cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | 5 (MSU-Blüh-/Entwicklungsmodell: 41–44 °F ≈ 5–7 °C für zwei V.-×-hybrida-Sorten; unterer Wert als kältetolerante Einordnung) | `species.base_temp` |
| Lebensdauer (Jahre) | — (botanisch kurzlebige Staude, ca. 2–4 Jahre in frostfreiem Klima/USDA 9–10; in Mitteleuropa einjährig kultiviert, kein belastbarer Jahres-Einzelwert für Mitteleuropa) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false (keine echte Winterruhe; frostbedingtes Absterben, kein Kältebedarf) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tagneutral; Blüte temperatur-/lichtgesteuert, kein Kältereiz nötig) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (entfällt) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — <!-- DATEN FEHLEN: tagneutral, kein Kurztag-/Langtag-Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 8a–11b (als Einjährige in 4a–11b) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; stirbt bei Frost; in Mitteleuropa als einjährige Sommerblume; Überwinterung im frostfreien Quartier (5–10°C) möglich; Stecklinge überwintern besser als ganze Pflanzen | `species.hardiness_detail` |
| Heimat | Hybride südamerikanischer Elternarten (Argentinien, Uruguay, Brasilien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hybridcharakter:** Verbena × hybrida ist eine Gartenhybride aus mehreren südamerikanischen Wildarten (v.a. Verbena peruviana, V. incisa, V. phlogiflora). Alle modernen Balkon- und Beetverbenen gehören zu dieser Hybridgruppe. Die Art ist steril oder schwach fertil — Vermehrung meist vegetativ.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–14 (lange Anzuchtzeit; früh starten!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (Direktsaat möglich aber unüblich; lieber Stecklinge kaufen) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 2, 3 (im Warmhaus ab Februar) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; kontinuierlich blühend) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (nach dem Frost bis Herbst) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Stecklingsvermehrung:** Triebspitzenstecklinge (5–8 cm) im August/September nehmen; in Stecksubstrat; bei 18–22°C; wurzeln in 3–4 Wochen. Überwinterung als Stecklinge einfacher als ganze Pflanze.

**Saatgut-Hinweis:** Dunkelkeimer-Tendenz (Keimung verbessert sich bei Lichtausschluss, aber nicht obligat — Keimung auch ohne Abdeckung moeglich). Kuehle Stratifikation (5°C fuer 1–2 Wochen) verbessert Keimrate. Keimung unregelmaessig; Geduld noetig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (geringe Toxizität; bei großer Aufnahme Magenbeschwerden möglich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Iridoid-Glykoside (geringe Mengen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Rückschnitt fördert Neuaustrieb und Blüte) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8 (nach Blütenanfall um 1/3 zurückschneiden) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–45 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 (hängend bis 80 cm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–35 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr lichtbedürftig; Fensterbrett nur Süd/West) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (außer Anzucht) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (hängende/kriechende Wuchsform; selbstdeckend) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Balkonblumenerde; pH 5,8–6,5; leicht sauer; Perlite-Anteil 20% für bessere Drainage | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 20 (typischer Bereich sonnenadaptierter C3-Krautpflanzen; netto-Photosynthese = 0) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 40 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (Sonnenliebhaber; 6–10 h direkte Sonne; toleriert keinen Schatten) | `species.shade_tolerance` |
| Effektive Wurzeltiefe min (cm) | 15 (flaches faseriges System; Min.-Topftiefe der Art = 15 cm) | `species.effective_root_depth_cm` |
| Effektive Wurzeltiefe max (cm) | 30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (braucht dränierenden Boden; Wurzelfäule bei nassem Substrat) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (Gattung gilt als gering bis mäßig salzverträglich; kein art-spezifischer Maas-Hoffman-Datensatz) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | — <!-- DATEN FEHLEN: kein belegter Maas-Hoffman a-Wert für V. × hybrida --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN: kein belegter Maas-Hoffman b-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.8–6.5 (leicht sauer; quellentreu, harmonisiert mit §1.6/§2.3; Gesamttoleranz der Art reicht bis ~7.0) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 18 (Gardening Know How nennt 65–75 °F ≈ 18–24 °C als Boden-Zieltemperatur) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 26 (Ball Horticultural Seed Crop Information Guide: 75–80 °F ≈ 24–26 °C professionelle Produktionsvorgabe) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.3 (nur dünn mit Substrat bedecken, ca. 1/16–1/8 Zoll; Ball-Guide führt Verbena mit „Cover Seed: Yes") | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14 (Spanne 14–28 Tage — Verbene keimt notorisch langsam und ungleichmäßig; einzelne Quellen nennen bis zu 40 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | <!-- DATEN FEHLEN: keine zwei unabhängigen, art-spezifischen Quellen zur Lagerfähigkeit von Verbena-×-hybrida-Saatgut gefunden; nur generische Aussagen zu Papiertüten-Saatgut allgemein --> | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark (Ball-Seed-Produktionsdaten: Pflicht-Abdeckung „Cover Seed: Yes" ohne Lichtkeim-Vermerk; mehrere Konsumentenquellen bestätigen eine Dunkelkeim-Präferenz mit Keimhemmung durch Licht) | `species.seed_profile.light_germination` |
| Vorbehandlung | cold_stratification (Kühlschrank-Kältebehandlung ca. 10 Tage bis 4 Wochen vor der Aussaat verbessert nachweislich die Keimrate und -gleichmäßigkeit) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 2.9 (Ball-Seed-Katalog: 350 Samen/g ≈ 2,9 g/1000 Korn; unabhängig bestätigt durch Ideal-Florist-Hybrid-Verbena-Saatgut mit ebenfalls ca. 350 Samen/g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Beet-/Balkonpflanze, die einzeln als Jungpflanze/Plug pikiert und ausgepflanzt wird (Pflanzabstand 25–35 cm, siehe §1.6); keine Reihen-/Flächen-Direktsaatdichte publiziert --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Die von mehreren Konsumentenquellen berichtete Widersprüchlichkeit ("braucht Dunkelheit" vs. "braucht Licht an der Oberfläche") spiegelt sich auch im bestehenden §1.3-Text wider ("Dunkelkeimer-Tendenz... aber nicht obligat"). Für die professionelle Plug-Produktion (Ball Horticultural, 288er-Zelltrays) gilt die Abdeckungspflicht als Standard, weshalb `dark` als praxisrelevante Einstufung gewählt wurde; die Keimung gelingt in der Praxis aber auch bei leichter Lichtexposition, sodass keine strikte, absolute Lichtabhängigkeit vorliegt.

Quellen (§1.8): [Ball Horticultural Company — Seed Crop Information Guide (Verbena-Zeile: 10.000 Samen/oz, 350 Samen/g, Cover Seed: Yes, 75–80 °F, Sow-to-Transplant 35–42 Tage)](https://www.panamseed.com/media/culture/pas/seedcropchart_ball.pdf); [Gardening Know How — Verbena Seed Germination: How To Grow Verbena From Seed](https://www.gardeningknowhow.com/ornamental/flowers/verbena/verbena-seed-germination.htm); [Sow Right Seeds — Grow Vibrant Verbena Flowers That Beat the Summer Heat](https://sowrightseeds.com/blogs/planters-library/how-to-grow-verbena-flowers-from-seed); [Bright Lane Gardens — How Long to Cold Stratify Seeds for Successful Germination](https://brightlanegardens.com/native-plants/seed-starting/how-long-to-cold-stratify-seeds/); [OSC Seeds — Ideal Florist Mixed Hybrid Verbena Seeds (Seed count ~350/g)](https://www.oscseeds.com/product/ideal-florist-mixed-hybrid-verbena-seeds-6277/); [Park Seed — Know Before You Grow: Verbena Plant](https://www.parkseed.com/blogs/park-seed-blog/know-before-you-grow-verbena-plant)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–28 | 1 | false | false | low |
| Sämling / Anzucht | 21–42 | 2 | false | false | low |
| Vegetativ / Abhaertung | 14–28 | 3 | false | false | medium |
| Hauptblüte | 60–120 | 4 | false | false | medium |
| Herbstblüte (nach Rückschnitt) | 30–60 | 5 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 (Dunkelkeimer; Licht hemmt Keimung!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–3 (Keimung lichtunabhängig/dunkel; minimaler DLI) <!-- Quelle: Steckbrief-Erweiterung 2026-06 / DLI-Keimung --><!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75–90 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.2–0.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 0.8 (kritischer Punkt oberhalb des feuchteliebenden Keim-Korridors; Oberkante 0.5 + ~0.3) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium (C3-Krautpflanze) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Anzuchtdunkel/diffus; Tageslicht-Anker, R:FR≈1.1–1.3) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2 (gleichmäßig feucht; nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | — (Substrat feucht halten) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling / Anzucht

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (oberhalb des Zielkorridors; Oberkante 0.9 + ~0.3) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 21–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Vollsonne/offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptblüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 (tagneutral; Licht fördert Blüte quantitativ) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (stomatärer Kollaps deutlich oberhalb des Korridors; Oberkante 1.4 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 (wärmetolerant; gute Leistung bis ~35 °C) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-Vollsonne; R:FR≈1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Balkon: täglich im Sommer; Trockenheit schadet Blüte) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 5.8–6.5 | — | — |
| Sämling | 1:1:1 | 0.4–0.8 | 5.8–6.5 | 50 | 20 |
| Vegetativ | 2:1:2 | 0.8–1.4 | 5.8–6.5 | 80 | 30 |
| Hauptblüte | 1:2:2 | 1.0–1.8 | 5.8–6.5 | 80 | 35 |
| Herbstblüte | 1:2:2 | 0.8–1.4 | 5.8–6.5 | 60 | 25 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (Mn/Zn/Cu/Mo, ppm):** <!-- DATEN FEHLEN --> Keine art-spezifisch belegten Mn-/Zn-/Cu-/Mo-Sollwerte für *Verbena × hybrida* in der Nährlösung auffindbar; allgemeine Floriculture-Standardbereiche existieren, sind aber nicht artspezifisch validiert. Felder `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm` bleiben bis zur Belegung leer (Standard-Mikronährstoff-Mix des Volldüngers verwenden).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Balkon/Gewächshaus)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Flüssig-Balkonblumendünger | Compo/Substral | Flüssig | 8-8-6 | 0.20 | 3 | Blüte |
| Blaudünger / Osmocote | Osmocote | Slow-Release | 15-9-12 | je Depot | 1 | alle |
| Fertilizer für Blühpflanzen | Canna Bio Boost | Flüssig | 2-1-3 | 0.15 | 4 | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee | eigen | flüssig organisch | 1:10 verdünnt; 2×/Woche | Jun–Sep |
| Hornmehl | diverse | organisch | 5 g/L Substrat | Substrat-Mix |

### 3.2 Mischungsreihenfolge

1. Stammlösung Blütendünger
2. CalMag (falls Kalkwasser)
3. Weitere Additive
4. pH-Korrektur zuletzt

### 3.3 Besondere Hinweise zur Düngung

Verbene ist nicht anspruchsvoll, aber kontinuierliches Blühen braucht regelmäßige Nährstoffzufuhr. Kalium fördert Blütenbildung. Slow-Release-Dünger im Substrat praktisch für Balkon. KEIN übermäßiges Stickstoff (üppiges Blattwerk statt Blüten). Bei vergilbenden Blättern: Eisenmangel prüfen (pH zu hoch). Abblühende Köpfchen regelmäßig entfernen (Deadheading) verlängert Blütezeit erheblich.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 1–2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.3 (Überwinterungspflanze; minimal gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkreiches Wasser kann Chlorosen verursachen; pH prüfen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7–10 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig; kein Umtopfen nötig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Saatgut | Im Warmhaus bei 20–25°C; Dunkelkeimer; Folie drüber | hoch |
| Mär–Apr | Pikierung | Wenn 2. Blattpaar erscheint; in 9-cm-Töpfe | hoch |
| Mai | Abhärtung | 1–2 Wochen langsam ans Freie gewöhnen | hoch |
| Mai–Jun | Auspflanzung | Nach letztem Frost; vollsonniger Standort | hoch |
| Jun–Aug | Deadheading | Verblühte Blütenköpfe abzwicken; fördert Nachblüte | mittel |
| Jul–Aug | Rückschnitt | Um 1/3 kürzen wenn Blüte nachlässt; fördert Neuaustrieb | mittel |
| Aug | Stecklinge | Triebspitzenstecklinge für Überwinterung | niedrig |
| Sep–Okt | Winterquartier | Stecklinge oder Mutterpflanzen ins Haus (5–10°C; hell) | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; Gelbflecken; bronzefarbene Blätter | Blatt | Blüte (trocken-warm) |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau; Rußtau; fliegende Wolke | Blatt | alle (Gewächshaus) |
| Blattläuse | Myzus persicae | Kolonien; Vergilbung; Deformation | Trieb | Sämling, Frühblüte |
| Thripse | Frankliniella occidentalis | Silber-weiße Flecken; Blütendeformation | Blatt, Blüte | Hauptblüte |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal (Erysiphe spp.) | Weißgrauer Belag auf Blättern | trocken-warm; dichte Bestände |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Pilzrasen auf Blüten/Blättern | kühl-feucht; schlechte Luftzirkulation |
| Peronospora (Falscher Mehltau) | fungal (Peronospora sparsa) | Gelbliche Flecken oben; grauviolett unten | kühl-feucht |
| Verbena-Mosaik | viral | Mosaikflecken; Deformation | Blattlausübertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5–10 | 14–21 |
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Aphidius colemani | Blattläuse | 3–5 | 14 |
| Amblyseius cucumeris | Thripse | 25–50 | 10–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Spinnmilben, Thripse, Blattläuse |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen | 14 | Echter Mehltau |
| Backpulver-Lösung | cultural | NaHCO₃ | Sprühen 1% | 0 | Echter Mehltau (präventiv) |
| Pyrethrin | biological | Pyrethrine | Sprühen | 3 | Blattläuse, Weiße Fliege |
| Befallene Teile entfernen | cultural | — | Sofort | 0 | Grauschimmel, Mehltau |
| Luftzirkulation verbessern | cultural | — | Pflanzabstand | 0 | Mehltau, Grauschimmel |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zierpflanze; Balkon/Beet-Annuelle |
| Empfohlene Vorfrucht | — (Einjährige Zierpflanze; keine klassische Fruchtfolge) |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | 2–3 Jahre Pause auf gleicher Beetfläche (Botrytis) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes | Tagetes patula/erecta | 0.9 | Bestäuber-Anlockung; Nematoden-Abwehr; Farbkontrast | `compatible_with` |
| Geranien | Pelargonium × hortorum | 0.8 | Ästhetisch; gleiche Pflegebedürfnisse | `compatible_with` |
| Petunie | Petunia × hybrida | 0.8 | Gleiche Standortansprüche; Bestäuberfreundlich | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bestäuber-Anlockung; Trockenheitstoleranz | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Bestäuber; essbar; Farbkontrast | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung vieler Pflanzen | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Verbena hybrida |
|-----|-------------------|-------------|-----------------------------------|
| Echte Eisenkraut | Verbena officinalis | Gleiche Gattung; mehrjährig | Winterharter; Heilpflanze; weniger Schaueffekt |
| Lila Eisenkraut | Verbena rigida | Gleiche Gattung | Kompakter; Freiland in milden Regionen |
| Landverbene | Glandularia × hybrida | Nah verwandte Gattung | Sehr hängend; Ampelfüllung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Verbena × hybrida,"Garten-Verbene;Eisenkraut;Garden Verbena;Annual Verbena",Verbenaceae,Verbena,annual,day_neutral,herb,fibrous,"8a;8b;9a;9b;10a;10b;11a;11b",0.0,"Südamerika (Hybride)",yes,limited,yes,false,false,medium_feeder,false,tender,"2;3","","5;6;7;8;9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Lanai Red,Verbena × hybrida,"trailing;red;heat_tolerant;powdery_mildew_resistant",75,hybrid
Aztec Pink Magic,Verbena × hybrida,"compact;fragrant;multicolor;heat_tolerant",80,hybrid
Superbena Coral Red,Verbena × hybrida,"trailing;large_flower;vegetative;heat_tolerant",70,vegetative_only
```

---

## Quellenverzeichnis

1. [Royal Horticultural Society — Verbenas](https://www.rhs.org.uk/plants/verbena) — Gartenpraxis
2. [University of Florida IFAS — Verbena Production](https://edis.ifas.ufl.edu) — Gewächshauskultur
3. [Ball Horticulture Verbena Growing Guide](https://www.ballhort.com) — Produktionsanleitung
4. [USDA PLANTS — Verbena](https://plants.usda.gov) — Taxonomie
5. [Bayerische Gartenakademie — Balkonpflanzen](https://www.lwg.bayern.de/gartenakademie) — Balkon-Praxis
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [MSU Extension / Greenhouse Grower — Energy-Efficient Annuals: Pentas & Verbena (Blanchard, Vaid, Runkle)](https://www.canr.msu.edu/uploads/resources/pdfs/energy-efficient-annuals-pentas-and-verbena.pdf) — Basistemperatur Verbena × hybrida 41–44 °F (≈5–7 °C), Temperatur-/DLI-Blühmodell
7. [MSU Floriculture — Light and Temperature Responses of Bedding Plants (Runkle, Blanchard)](https://www.canr.msu.edu/floriculture/uploads/files/Light%20and%20temp%20on%20bedding.pdf) — Basistemperatur-Einordnung (kältetolerant/-sensitiv), Verbena im kältetoleranten Bereich
8. [RHS — How to grow verbena (Growing Guide)](https://www.rhs.org.uk/plants/verbena/growing-guide) — Vollsonne-Bedarf, dränierender Boden, Staunässe-Empfindlichkeit; bedding verbenas als "tender perennials", frostbedingtes Absterben, Aussaat Jan–Mär bei 21 °C, Stecklinge Frühjahr/Spätsommer
9. [Clemson HGIC — Verbena](https://hgic.clemson.edu/factsheet/verbena/) — Standort (full sun, keine Schattentoleranz), Drainageansprüche
10. [Gardenia.net — Verbena Growing Guide](https://www.gardenia.net/guide/verbena-plant-care-and-growing-guide) — Boden-pH-Vorzug, well-drained Substrat
11. [Oxford JXB / PMC — Canopy light, red:far-red ratio](https://pmc.ncbi.nlm.nih.gov/articles/PMC11805590/) — Tageslicht-Anker R:FR ≈ 1.1–1.3 → FR/(R+FR) ≈ 0.5; Anstieg unter Laubdach
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
12. [Proven Winners — Growing Verbena](https://www.provenwinners.com/learn/how-plant/verbena) — Verbena x hybrida als "long-blooming, heat-tolerant tender perennial", in kalten Zonen als Einjährige kultiviert
13. [Texas A&M AgriLife Extension / Henderson County Master Gardeners — Verbena Hybrid Mix](https://txmg.org/hendersonmg/plant-library/verbena-hybrid-mix/) — "short-lived perennial hardy only to USDA Zones 9 or 10", außerhalb dieser Zonen einjährig kultiviert
<!-- /Quelle: growing-phase-auditor 2026-07 -->
