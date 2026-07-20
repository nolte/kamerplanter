# Riemenblume — Clivia miniata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardeners World – Clivia](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-and-care-for-clivia/), [Guide to Houseplants – Clivia miniata](https://www.guide-to-houseplants.com/clivia-miniata.html), [Wisconsin Horticulture – Clivia](https://hort.extension.wisc.edu/articles/clivia/), [UK Houseplants – Clivia](https://www.ukhouseplants.com/plants/clivia-natal-or-bush-lily)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Clivia miniata | `species.scientific_name` |
| Volksnamen (DE/EN) | Riemenblume, Klivie; Natal Lily, Kaffir Lily, Bush Lily | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` → `botanical_families.name` |
| Gattung | Clivia | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | bulb_geophyte | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: keine artspezifische, belegte GDD-Basistemperatur für Clivia miniata; Art wird nicht GDD-gesteuert kultiviert --> | `species.base_temp` |
| Lebensdauer (Jahre) | 10–20 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization, hier Kälte-Blühinduktion) | true | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 42 (6–8 Wochen bei 10–13°C als Blühinduktion) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9b–11b | `species.hardiness_zones` |
<!-- Quelle: growing-phase-auditor 2026-07 — Korrektur half_hardy → tender: RHS-Einstufung H1c (5–10°C Minimum, "kann im Sommer draußen stehen"), gemäß projektinterner Zuordnung tender = RHS H1a–H2 (PFLANZEN-EIGENSCHAFTEN-REFERENZ.md §1.3); Gardeners World "frost-tender house plant"; Wisconsin Horticulture Extension "hardy only in zones 9 and 10... must bring in before freezing weather"; Missouri Botanical Garden Zone 9–11. 4/4 Quellen stimmen überein (✅ GESICHERT). -->
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
<!-- /Quelle: growing-phase-auditor 2026-07 -->
<!-- OFFENER BEFUND (nicht korrigiert, ⚠ WAHRSCHEINLICH 2/3): "-3°C"-Angabe steht in Spannung zur RHS-H1c-Einstufung (Minimum 5–10°C, kein Frost) und zur Wisconsin-Extension-Aussage ("must bring in before freezing weather", Toleranz nur bis ~2°C); Missouri Botanical Garden nennt hingegen "tolerates only light frosts" am Naturstandort. Da 2 Quellen (RHS, Wisconsin) gegen 1 abweichende Quelle (MOBOT) stehen, keine 3/3-Bestätigung — Originalwert gemäß Konfidenzregel beibehalten, manuelle Prüfung empfohlen. -->
| Winterhärte-Detail | Übersteht kurzzeitig leichten Frost (bis -3°C); Wurzeln frostempfindlich | `species.hardiness_detail` |
| Heimat | Südafrika (KwaZulu-Natal, Ostkap) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 2, 3, 4, 5 (Frühjahrsblüher nach Winterkühle) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, division, seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, besonders Wurzeln und Beeren | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Lycorin, Clivacin (Alkaloide) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (nach Verblühen) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 45–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gut drainierte, nährstoffreiche Zimmerpflanzenerde; Clivien mögen enge Töpfe — erst umtopfen wenn Wurzeln aus dem Topf wachsen | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch gemessener LCP für Clivia miniata; als schattenverträglicher Waldbodenherb physiologisch niedrig (Größenordnung < 20 µmol/m²/s), aber kein belegter Messwert --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: siehe min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine belegten Maas-Hoffman-Parameter (ECe-Schwelle) für Clivia miniata --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: keine belegten Maas-Hoffman-Parameter (Slope) für Clivia miniata --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

> **Hinweise (Freitext, nicht in KA-Felder):**
> - **Schattenverträglichkeit:** Clivia miniata stammt aus dem Waldboden-Unterwuchs (woodland understory) Südafrikas und toleriert tiefen Schatten (deep_shade) als Standort; für zuverlässige Blüte ist jedoch helles indirektes Licht / lichter Halbschatten besser — daher Klassen-Einordnung `shade` (toleriert tiefen Schatten, bevorzugt aber heller).
> - **Photosynthese-Typ:** Als Waldboden-Geophyt der Amaryllidaceae betreibt die Art C3-Photosynthese (kein CAM/Sukkulenz — die fleischigen Wurzeln dienen der Wasserspeicherung im Unterwuchs, nicht einem CAM-Stoffwechsel).
> - **Salztoleranz:** Salzempfindlich; Düngersalz-Anreicherung führt zu braunen Blattspitzen (leaf tip burn). Bezugsgröße der (fehlenden) Schwelle wäre Substrat-ECe, nicht Gießwasser-EC.
> - **Boden-pH:** Der pH-Vorzug 5.5–6.5 deckt den in §2.3 / §3 verwendeten Korridor 6.0–6.5 ab und harmonisiert mit diesem.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 29 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 1.5 (1–2 cm; Samen werden flach in die Erde eingebettet/angedrückt) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 28 (4–8 Wochen, unterer Wert; typisch 4–8 Wochen bis Keimblatt sichtbar, teils bis zu 3 Monate) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | <!-- DATEN FEHLEN: Quellen bestätigen nur qualitativ "frisch geerntete Samen keimen deutlich besser als ältere", ohne belegte Jahreszahl --> | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | indifferent (Samen werden flach angedrückt/leicht bedeckt und in hellem indirektem Licht gehalten — keine Quelle fordert explizit Dunkelheit oder Licht als Keimbedingung) | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (Frischsaat direkt nach Ernte ohne Stratifikation empfohlen; keine Kalt-/Warmstratifikation oder Skarifikation dokumentiert) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: keine Quelle mit TKG-Wert für Clivia miniata gefunden --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Einzelsaat in Töpfen/Schalen, keine Reihen-/Flächenkultur mit dokumentierter Aussaatdichte --> | `species.seed_profile.sowing_density_per_m2` |

> **Hinweis:** Clivia-Samen sind großkörnige, fleischige Beerensamen mit hohem Wassergehalt; Keimtemperatur 27–29 °C (80–85 °F) wird von mehreren Anzucht-Ratgebern genannt, während ein weiterer Ratgeber ein Optimum von 20–25 °C nennt — daher die Spanne 20–29 °C. Keimung ist stark asynchron und kann sich über mehrere Monate hinziehen.

**Quellen (§1.8):**
- [Plant Grower World — Growing Clivias from Seed: A Step-by-Step Guide](https://plantgrowerworld.com/growing-clivias-from-seed/) — Keimtemperatur 80–85°F, Keimdauer 6–8 Wochen
- [Garden Lovers Club — How to Germinate Clivia Seeds](https://www.gardenloversclub.com/houseplants/clivia/germinate-clivia-seeds/) — Saattiefe 1–2 cm, Keimdauer 4–8 Wochen, helles indirektes Licht während Keimung
- [Wilson Garden Pots — A Gardener's Guide to Growing Clivias from Seeds](https://www.wilsongardenpots.com/a/growing-clivias-from-seeds) — Optimale Keimtemperatur 20–25°C, Frischsaat-Empfehlung
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill Batch 5) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Winterruhe | 60–90 | 1 | false | false | high |
| Blütenaustrieb | 14–21 | 2 | false | false | low |
| Blüte | 28–42 | 3 | false | false | medium |
| Vegetativ (Sommer) | 150–210 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Winterruhe — Okt bis Jan

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–13 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | <!-- DATEN FEHLEN: kein belegter Photosynthese-Temperaturoptimum für die kühle Ruhephase; aktiver Optimumwert siehe Vegetativ-Phase --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Sommer)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

<!-- Mikronährstoff-Spalten Mn/Zn/Cu/Mo ergänzt — Quelle: Steckbrief-Erweiterung 2026-06 -->
| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Winterruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — | — |
| Blütenaustrieb | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — | — |
| Blüte | 0:1:2 | 0.5–0.8 | 6.0–6.5 | 80 | 40 | — | 1 | <!--DATEN FEHLEN--> | <!--DATEN FEHLEN--> | <!--DATEN FEHLEN--> | <!--DATEN FEHLEN--> |
| Vegetativ | 2:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 50 | — | 2 | <!--DATEN FEHLEN--> | <!--DATEN FEHLEN--> | <!--DATEN FEHLEN--> | <!--DATEN FEHLEN--> |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Winterruhe → Blütenaustrieb | time_based | 60–90 Tage | Temperaturanstieg auf 18°C, Blütenstiel erscheint |
| Blütenaustrieb → Blüte | time_based | 14–21 Tage | Blüten öffnen |
| Blüte → Vegetativ | time_based | 28–42 Tage | Blüten verblüht |
| Vegetativ → Winterruhe | time_based | 150–210 Tage | Herbst, Temperatur senken |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Substral | base | 4-6-8 | 5 ml/L | 1 | blüte, vegetativ |
| Zimmerpflanzendünger | Compo | base | 7-4-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Guano-Blumendünger | Gardol | organisch | 2 ml/L | Apr–Sep | light_feeder |
| Langzeitdünger Stäbchen | Substral | langsam | 1 Stäbchen/Topf | Apr–Sep | light_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| Okt–Jan | Winterruhe | 0.0 | — | Kein Dünger |
| Feb–Apr | Blüte | 0.5–0.8 | 6.2 | Sehr sparsam |
| Mai–Sep | Vegetativ | 0.8–1.2 | 6.2 | Alle 4–6 Wochen |
| Okt | Einwintern | 0.0 | — | Letzte Düngung |

### 3.3 Besondere Hinweise zur Düngung

Clivia ist ein Schwachzehrer. Zu viel Dünger verhindert die Blütenbildung. Die Winterkühle (10–13°C) für 6–8 Wochen ist die entscheidende Voraussetzung für die Blüteninduktion — nicht die Düngung. Wer diese Kältephase einhält, hat fast immer gute Blüten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 8 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Kühl (10–13°C), wenig gießen, nicht düngen | hoch |
| Feb | Blütenanzeichen | Blütenstiel wächst — Pflanze an hellen Platz stellen | hoch |
| Mär–Apr | Blüte | Regelmäßig gießen, Blätter nicht benetzen | mittel |
| Apr–Mai | Nach Blüte | Verblühte Blütenstiele entfernen (knapp über der Erde) | mittel |
| Jun–Sep | Wachstum | Regelmäßig gießen, monatlich düngen | hoch |
| Okt | Einwintern | Kühlen Standort suchen (10–13°C), Wasser reduzieren | hoch |
| Nov–Jan | Winterruhe | Minimal gießen, kein Dünger, keine Wärme | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 — Korrektur: hardiness_rating war "needs_protection" (gültiger Enum, aber unpassend); frostempfindliche Zimmer-/Kübelpflanze mit frostfreier Innen-Überwinterung (move_indoors, 8–13°C) = frost_free -->
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem, leaf | alle | medium |
| Schildläuse | Coccus hesperidum | Braune Schuppen | stem | alle | difficult |
| Spinnmilben | Tetranychus urticae | Gelb-gesprenkeltes Laub | leaf | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Anthraknose | fungal | Braune Blattränder, dunkle Flecken | high_humidity, overwatering | 7–14 | alle |
| Bakterienfäule (Erwinia) | bacterial | Weiche, nasse Fäule am Blattansatz | waterlogging, wounds | 3–7 | alle |
| Wurzelfäule | fungal | Welke Blätter trotz Wasser | overwatering | 7–21 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wollläuse | 1–2 Käfer/Pflanze | 14 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Wollläuse, Spinnmilben |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Schildläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Clivia miniata |
|-----|-------------------|-------------|------------------------------|
| Clivia nobilis | Clivia nobilis | Gleiche Gattung | Nickende Blüten, seltener |
| Amaryllis | Hippeastrum hybridum | Gleiche Familie | Größere Blüten, Winter-Blüher |
| Agapanthus | Agapanthus africanus | Blaue Blüten, ähnliche Kultur | Blau blühend, halbhardy |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,photosynthesis_type,shade_tolerance,effective_root_depth_cm,waterlogging_tolerance,salt_tolerance_class,soil_ph_preference
Clivia miniata,Riemenblume;Klivie;Natal Lily,Amaryllidaceae,Clivia,perennial,day_neutral,bulb_geophyte,rhizomatous,9b;10a;10b;11a;11b,0.0,Südafrika KwaZulu-Natal,yes,10,20,60,60,—,yes,limited,false,false,c3,shade,15-30,sensitive,sensitive,5.5-6.5
```
<!-- CSV-Zeile um photosynthesis_type, shade_tolerance, effective_root_depth_cm, waterlogging_tolerance, salt_tolerance_class, soil_ph_preference erweitert — Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## Quellenverzeichnis

1. [Gardeners World – Clivia Care](https://www.gardenersworld.com/how-to/grow-plants/how-to-grow-and-care-for-clivia/) — Pflege, Überwinterung
2. [Guide to Houseplants – Clivia miniata](https://www.guide-to-houseplants.com/clivia-miniata.html) — Indoor Care
3. [Wisconsin Horticulture – Clivia](https://hort.extension.wisc.edu/articles/clivia/) — University Extension Service
4. [UK Houseplants – Clivia](https://www.ukhouseplants.com/plants/clivia-natal-or-bush-lily) — Detailed Care
5. [Old Farmer's Almanac – Clivia](https://www.almanac.com/plant/clivia) — Growing Tips
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS – How to grow clivias](https://www.rhs.org.uk/plants/clivia/how-to-grow) — Tender-Einstufung, Licht (helles indirektes Licht), Winterruhe ~10°C für Blühinduktion, Substrat
7. [Wikipedia – Clivia miniata](https://en.wikipedia.org/wiki/Clivia_miniata) — Waldhabitat (woodland understory), Rhizom + fleischige Wurzeln, Frostempfindlichkeit (USDA 9–11)
8. [North Carolina Extension – Clivia miniata Plant Toolbox](https://plants.ces.ncsu.edu/plants/clivia-miniata/) — Lichtbedarf (dappled shade to deep shade), University-Extension-Quelle
9. [New York Botanical Garden – Clivia Houseplant Guide](https://libguides.nybg.org/Clivia) — Schattenstandort (deep/partial shade), Pflege
10. [Greg – Clivia Roots / Lifecycle](https://greg.app/clivia-roots/) — Wurzeltiefe (6–12 in ≈ 15–30 cm), Lebensdauer 10–20 Jahre
11. [ISHS Acta Horticulturae – Scheduling flowering in Clivia miniata](https://www.ishs.org/ishs-article/1171_6) / [ScienceDirect – Crassulacean Acid Metabolism overview](https://www.sciencedirect.com/topics/biochemistry-genetics-and-molecular-biology/crassulacean-acid-metabolism) — Kälte-Blühinduktion (Vernalisation) bzw. CAM-Familien-Abgrenzung (Amaryllidaceae-Geophyten = C3, kein CAM)
12. [Gardener's Path – Grow Clivia](https://gardenerspath.com/plants/flowers/grow-clivia/) — Salzempfindlichkeit (Düngersalz-Anreicherung, braune Blattspitzen), Staunässe-/Überwässerungsempfindlichkeit
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 (Lebenszyklus-Audit) -->
13. [RHS Plant Finder – Clivia miniata (Natal lily)](https://www.rhs.org.uk/plants/4036/clivia-miniata/details) — RHS-Hardiness-Rating H1c (5–10°C Minimum) → Basis der `frost_sensitivity: tender`-Korrektur
14. [Missouri Botanical Garden – Clivia miniata Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b549) — Blühzeit Dez–Apr, USDA-Zone 9–11, "tolerates only light frosts" (Naturstandort)
<!-- /Quelle: growing-phase-auditor 2026-07 -->
