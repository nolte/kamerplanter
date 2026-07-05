# Ringelblume — Calendula officinalis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Wikipedia Ringelblume, NaturaDB Calendula, Lichtnelke Heilpflanze Calendula, Manufactum Calendula

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Calendula officinalis | `species.scientific_name` |
| Volksnamen (DE/EN) | Ringelblume, Sonnenwende, Garten-Ringelblume; Pot Marigold, Common Marigold | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Calendula | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein konsistent belegter GDD-Basiswert für Calendula; kühle Jahreszeit legt ~5 °C nahe, aber keine 2 unabhängigen Primärquellen --> | `species.base_temp` |
| Lebensdauer (Jahre) | — (einjährig, nicht perennial) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht erforderlich) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral, kein Kurztag-/Langtag-Auslöser) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 2a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt leichte Fröste (−5 °C); selbst aussämend; in Norddeutschland problemlos als Einjährige | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Südeuropa | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (verträgt leichten Frost) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5 (und Herbst für Frühjahrserblühen) | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Blüten) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

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
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Harzallergene; besonders bei Korbblütler-Allergie) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Korbblütler-Allergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (verblühte Blüten regelmäßig entfernen = Deadheading) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9, 10 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–30 | `species.spacing_cm` |
| Indoor-Anbau | limited (Fensterbank, kühler Standort) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Normale Kräutererde; pH 5,5–7,0; durchlässig | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein speziesspezifischer LCP-Messwert für Calendula in seriösen Quellen --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 20–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe dS/m) | <!-- DATEN FEHLEN: keine etablierten Maas-Hoffman-Schwellenwerte für Calendula; Studien belegen nur Salzempfindlichkeit qualitativ --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN: kein publizierter Maas-Hoffman-Slope für Calendula --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.0 (Toleranz 4.5–8.3) | `species.soil_ph_preference` |

> **Hinweise:** Wurzelmuster ist eine Herzwurzel (heart root), die sich aus der Pfahlwurzel verzweigt; die effektive durchwurzelte Tiefe bleibt flach bis mittel (20–30 cm). Calendula gilt als salzempfindlich (salt sensitive) — wächst noch bei niedriger bis mäßiger NaCl-Belastung, vegetatives Wachstum nimmt jedoch bereits ab etwa 50–100 mM NaCl deutlich ab. Belastbare Maas-Hoffman-Koeffizienten (Substrat-ECe, nicht Gießwasser-EC) sind nicht publiziert. Der pH-Optimumbereich 6,0–7,0 ist konsistent mit §1.6 (Topf pH 5,5–7,0) und §2.3 (Nährlösung pH 5,5–7,0).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill, Batch 4) -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 16 (Studien-Optimum 16–17 °C; extremer Toleranzbereich 2–32 °C) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 24 (praxisübliche Zielspanne 70–75 °F laut Saatgutanbietern) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.6 (dünn mit Erde bedecken, ca. 1/4 Zoll) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (7–14 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 (3–5 Jahre bei kühler, trockener Lagerung; unterer Wert verwendet) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | dark | `species.seed_profile.light_germination` |
| Vorbehandlung | — (keine Vorbehandlung erforderlich) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 10 (Sortenspanne ca. 9–14 g je 1000 Korn, abgeleitet aus Samenzahl-Angaben verschiedener Anbieter) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | 16 (Endabstand 25 cm x 25 cm It. S.1.6/S.4.2) | `species.seed_profile.sowing_density_per_m2` |

Quellen (§1.8):
1. ScienceDirect / Experts@Minnesota — "Seed germination of calendula in response to temperature": Kardinaltemperaturen 2–32 °C, Optimum 16–17 °C, Hitzeschock >35 °C reduziert Keimung: https://www.sciencedirect.com/science/article/abs/pii/S0926669013005839
2. Sow Right Seeds — How to Grow Calendula: Keimtemperatur 70–75 °F, Keimdauer 7–14 Tage, Dunkelheit für Keimung nötig: https://sowrightseeds.com/blogs/planters-library/how-grow-heirloom-calendula-from-seed
3. True Leaf Market — Calendula Pacific Beauty Mix Flower Seeds: ca. 2.100 Samen/Unze (≈ 74 Samen/g): https://trueleafmarket.com/products/calendula-pacific-beauty-mixture-flower-seeds
4. Nimrod Bio — Seeds Per Gram Chart (Calendula ca. 100–120 Samen/g): https://www.nimrod.bio/wp-content/uploads/2020/09/seedsPerGram.pdf
5. Meadowlark Journal — The Easiest Way to Grow Calendula from Seed: Keimfähigkeit 3–5 Jahre bei kühler, trockener Lagerung: https://meadowlarkjournal.com/blog/calendula-from-seed
6. Interne Pflegeangaben S.4.2 dieses Dokuments (Vereinzeln auf 25–30 cm Abstand) — bereits als Quelle im Dokument geführt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill, Batch 4) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 21–35 | 3 | false | false | high |
| Blüte & Ernte | 60–120 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte & Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (sonnig bis halbschattig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–22 (kühle Temperaturen bevorzugt) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (kritischer Punkt stomatären Kollaps; oberer Zielwert + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–25 (C3-typisch, Kühljahreszeit-Pflanze) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht; Freiland-Vollsonne) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.6–0.9 | 6.0–7.0 | 60 | 30 | — | 1 | 0.5 | 0.3 | 0.1 | 0.03 |
| Vegetativ | 2:1:2 | 0.8–1.2 | 5.5–7.0 | 80 | 40 | — | 2 | 0.5 | 0.3 | 0.1 | 0.03 |
| Blüte | 1:2:2 | 0.8–1.0 | 5.5–7.0 | 70 | 35 | — | 1 | 0.5 | 0.3 | 0.1 | 0.03 |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> **Mikronährstoffe (Mn/Zn/Cu/Mo):** Werte entsprechen typischen Bandbreiten allgemeiner Hydroponik-Nährlösungen (Mn 0,5–2; Zn 0,5–2; Cu 0,1–0,5; Mo 0,02–0,05 ppm). Für Calendula als Schwachzehrer (light feeder) ist der untere Bereich angesetzt; speziesspezifische Calendula-Optima sind nicht publiziert. `nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Ringelblume ist Schwachzehrer und gedeiht auf mageren bis mittleren Böden am besten. Auf sehr nährstoffreichen Böden oder bei starker Düngung entsteht viel Blattwerk auf Kosten der Blüten. 1× Kompost-Grunddüngung im Frühjahr reicht vollständig. Keine weiteren Dünger notwendig.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Moderat feucht; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (kaum düngen) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 (nur Pflanzung) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Direktsaat | Direkt ins Beet; kaum deckend | hoch |
| Mai | Vereinzeln | Auf 25–30 cm Abstand ausdünnen | mittel |
| Jun–Okt | Deadheading | Verblühte Blüten wöchentlich entfernen — fördert Nachblüte | hoch |
| Aug | Samen reifen lassen | Für nächstes Jahr Samen sammeln oder selbst aussieben | niedrig |
| Okt | Abräumen | Vor dem Winter kompostieren | niedrig |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

Calendula officinalis ist eine **einjährige (annual)** Pflanze: Die Mutterpflanze stirbt im Winter ab und wird abgeräumt (§4.2, Okt) — es findet **keine Pflanzen-Überwinterung** statt. Eine Überwinterungsplanung (winter_action / spring_action, Winterquartier) ist daher **nicht anwendbar**. Der Bestand erneuert sich über Selbstaussaat (self-seeding) oder gezielte Direktsaat im Folgejahr; in milden Lagen (USDA 8+) kann eine Herbstaussaat den Winter überdauern und früh im Jahr erblühen.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | needs_protection (nur als Samen/Selbstaussaat relevant; Mutterpflanze nicht überwinternd) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | none | `overwintering_profiles.winter_action` |
| Frühjahrs-Maßnahme (spring action) | replant (Neuaussaat im Folgejahr) + Monat 3–4 | `overwintering_profiles.spring_action` |
| Winterquartier (Temp/Licht/Gießen) | — (nicht zutreffend, keine Einlagerung) | `overwintering_profiles.winter_quarter_*` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis fabae u.a. | Kolonien, Kräuselung, Honigtau | leaf, stem | vegetative, flowering | easy |
| Schnecken | Arion spp. | Fraßschäden an Keimlingen | all | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißer Belag auf Blättern | Trockene Hitze | 5–10 | vegetative |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmel an Blüten | Feuchtigkeit | 3–7 | flowering |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|-------------------|----------------|--------------|------------------|
| Blattlaus-Schlupfwespe (parasitoid wasp) | Aphidius colemani | Blattläuse | 0,1–3 Tiere/m² (bzw. ~1/Pflanze) wöchentlich, 2–3 Wochen | 2–3 Wochen |
| Florfliege (green lacewing) | Chrysoperla carnea | Blattläuse | ~10 Larven/m² (kurativ, Hotspots) | 1–2 Wochen |
| Marienkäfer (ladybird) | Adalia bipunctata / Coccinella spp. | Blattläuse | 5–10 Tiere/m² | 1–2 Wochen |

> **Hinweis:** Calendula selbst wirkt als Nützlings-Magnet — sie lockt durch Nektar und das Anlocken von Blattläusen Schweb­fliegen (hoverflies), Florfliegen und Marienkäfer an und unterstützt so die biologische Kontrolle benachbarter Kulturen (vgl. §6.2). Optimale Etablierungsbedingungen für Aphidius: 18–25 °C, 60–80 % rF.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Marienkäfer freilassen | biological | — | 5–10 Tiere/m² | 0 | Blattläuse |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | 5 g/m² | 0 | Schnecken |
| Deadheading | cultural | — | Wöchentlich | 0 | Grauschimmel (Belüftung) |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Ringelblume lockt Schwebfliegen an; hält Weiße Fliege fern | `compatible_with` |
| Möhre | Daucus carota | 0.8 | Möhrenfliege-Abwehr | `compatible_with` |
| Spargel | Asparagus officinalis | 0.8 | Nematoden-Abwehr durch Wurzelausscheidungen | `compatible_with` |
| Zwiebeln | Allium cepa | 0.7 | Gegenseitige Förderung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Bodenbeschattung; Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kohl | Brassica oleracea | Kohl-Aphiden werden angezogen (Ringelblume als Wirtspflanze) | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ringelblume |
|-----|-------------------|-------------|-------------------------------|
| Studentenblume | Tagetes patula | Ähnliche Funktion; Asteraceae | Stärkere Nematoden-Abwehr; intensiverer Duft |
| Kapuzinerkresse | Tropaeolum majus | Ähnliche Funktion als Begleitpflanze | Essbar (alle Teile); schöne Blüten |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Calendula officinalis,"Ringelblume;Sonnenwende;Pot Marigold;Common Marigold",Asteraceae,Calendula,annual,day_neutral,herb,taproot,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b",0.3,"Mittelmeerraum",yes,7,20,60,40,25,limited,yes,false,false,light_feeder,half_hardy,"3;4;5","6;7;8;9;10","6;7;8;9;10"
```

---

## Quellenverzeichnis

1. [Wikipedia Ringelblume](https://de.wikipedia.org/wiki/Ringelblume) — Taxonomie, Verwendung
2. [NaturaDB Calendula officinalis](https://www.naturadb.de/pflanzen/calendula-officinalis/) — Pflegedaten
3. [Lichtnelke Heilpflanze Calendula](https://www.lichtnelke.de/ringelblume-heilpflanze-calendula.html) — Anbau, Ernte
4. [Maria Laach Ringelblume](https://www.maria-laach.de/klosterbetriebe/klostergaertnerei/service/ringelblume.html) — Heilpflanzenkunde
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [PFAF — Calendula officinalis](https://pfaf.org/User/Plant.aspx?LatinName=Calendula+officinalis) — pH-Toleranz (4.5–8.3), Schattentoleranz (semi-shade/no shade), Wurzelmuster (heart root), Feuchtebedarf, USDA-Zone
6. [Temperate Plants (Ferns) — Calendula officinalis](https://temperate.theferns.info/plant/Calendula+officinalis) — Optimaltemperatur 16–26 °C (tolerant 8–30 °C), pH-Vorzug
7. [Almanac — How to Grow Calendula](https://www.almanac.com/plant/how-grow-calendula-complete-guide) — Keimtemperatur, pH 6–7, Vollsonne, Kühljahreszeit-Charakter
8. [Wisconsin Horticulture Extension — Calendula](https://hort.extension.wisc.edu/articles/calendula-calendula-officinalis/) — Vollsonne, Kühljahreszeit, Anbaupraxis
9. [USU Extension — Calendula in the Garden](https://extension.usu.edu/yardandgarden/research/calendula-in-the-garden) — Kältetoleranz (~−4 °C), Temperaturpräferenz, Direktsaat
10. [Nature Scientific Data — Photosynthetic pathways survey](https://www.nature.com/articles/s41597-021-00877-z) — C3-Klassifikation Asteraceae
11. [MDPI Agronomy 15(8):1802 — Saline Water in Asteraceae Floriculture](https://www.mdpi.com/2073-4395/15/8/1802) — Salzempfindlichkeit von Calendula (Asteraceae-Vergleich)
12. [MDPI Horticulturae 10(12):1357 — Salinity Stress in Calendula officinalis](https://www.mdpi.com/2311-7524/10/12/1357) — NaCl-Schwellen, vegetatives Wachstum vs. Blütenertrag
13. [PMC12189887 — Far-Red Light & Nutrient Solution on Calendula in Plant Factory](https://pmc.ncbi.nlm.nih.gov/articles/PMC12189887/) — PPFD 300, DLI ~13, EOD-Far-Red, Kulturtemperatur
14. [ASHS JASHS 146(1) — Far-Red Fraction Metric](https://journals.ashs.org/view/journals/jashs/146/1/article-p3.xml) — FR/(R+FR) ~0.46 im direkten Sonnenlicht
15. [UConn IPM — Biological Control of Aphids (2019)](https://ipm.cahnr.uconn.edu/wp-content/uploads/sites/3216/2022/12/2019Biologicalcontrolofaphidsfinal3.pdf) — Florfliegen/Aphidius-Ausbringraten, Etablierung
16. [Sound Horticulture — Aphidius colemani Tech Sheet](https://soundhorticulture.com/pages/aphidius-colemani-tech-sheet) — Aphidius-Ausbringrate (0,1–3/m²), Etablierungsbedingungen
17. [Atlas Scientific — Nutrient Solution for Hydroponics](https://atlas-scientific.com/blog/nutrient-solution-for-hydroponics/) — typische Mikronährstoff-Bandbreiten (Mn/Zn/Cu/Mo ppm)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
