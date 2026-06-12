# Geigenfeige — Ficus lyrata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Bloomscape](https://bloomscape.com/plant-care-guide/fiddle-leaf-fig/), [Planet Natural](https://www.planetnatural.com/ficus-lyrata/), [Lively Root](https://www.livelyroot.com/blogs/plant-care/ficus-lyrata-fiddle-leaf-fig-care-guide), [Soltech](https://soltech.com/products/fiddle-leaf-fig-care), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ficus lyrata | `species.scientific_name` |
| Volksnamen (DE/EN) | Geigenfeige; Fiddle Leaf Fig | `species.common_names` |
| Familie | Moraceae | `species.family` → `botanical_families.name` |
| Gattung | Ficus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Photosynthese-Typ | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- alle untersuchten Ficus-Arten sind C3 (Sternberg-Lab) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 25–50+ | `lifecycle_configs.typical_lifespan_years` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- wärmeliebende Tropenart: Wuchsstillstand unter ~10°C / 50°F --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Kritische Tageslänge (h) | Entfällt (tagneutral, kein Kurz-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- tropisch, kein Kältebedarf --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage | Entfällt | `lifecycle_configs.vernalization_min_days` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 12°C, optimal 18–24°C. Extrem empfindlich gegenüber Zugluft, Temperaturwechseln und Standortwechseln — führt zu Blattabwurf. | `species.hardiness_detail` |
| Heimat | Tropisches Westafrika (Sierra Leone bis DR Kongo — Regenwaldrandstreifen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Geigenfeige ist das Lieblingskind des Interior-Design-Instagram — und gleichzeitig eine der anspruchsvollsten Zimmerpflanzen. Der häufigste Fehler: Standort wechseln. Ficus lyrata hasst Ortswechsel und quittiert jeden mit massenweisem Blattabwurf. Einmal guten Platz gefunden — nie mehr bewegen. Helles Licht ist der Schlüsselfaktor; ohne ausreichend Licht stirbt die Pflanze langsam ab.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nur in natürlichem Habitat, nicht als Zimmerpflanze) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Stecklinge mit 2–3 Blättern bei 24–28°C und hoher Luftfeuchtigkeit (80%+). Abmoosen (Air Layering) ist zuverlässiger: Stamm anschneiden, feuches Sphagnum-Moos mit Folie umwickeln, nach 4–8 Wochen bewurzelt. Stecklinge im Wasser funktionieren selten gut. Sehr langsame Bewurzelung.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap (Milchsaft) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | ficin, ficusin (proteolytic_enzymes), latex_sap | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Milchsaft — Latexallergie-Kreuzreaktion möglich; Handschuhe beim Schneiden/Umtopfen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Nur im Frühjahr schneiden, wenn die Pflanze aktiv wächst. Schnittstellen mit Aktivkohle oder Wundverschlussmittel behandeln (Milchsaft staut sich). Topping (Haupttrieb kappen) fördert buschigen Wuchs.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 (Indoor, langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–180 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Qualitätserde mit hohem organischen Anteil. 60% Einheitserde + 20% Perlite + 20% Kokoserde. pH 6.0–7.0. Tongefäße mit guter Drainage bevorzugt. Nicht zu oft umtopfen (stresst die Pflanze). | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 25–40 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt (light compensation point, LCP — Netto-Photosynthese = 0) liegt im Bereich schattentoleranter tropischer Foliage-Arten; ein art-spezifischer Messwert für *Ficus lyrata* fehlt. Der Wert ist aus schatten-akklimatisierten Ficus-Foliage-Daten (Ficus benjamina) und dem allgemeinen Bereich schattentoleranter Arten (10–50 µmol/m²/s) abgeleitet. Lichtsättigung und Optimumbereich (300–800 PPFD, vgl. §2.2) gehören NICHT in das LCP-Feld. *Ficus lyrata* wächst als Jungpflanze (Hemiepiphyt) unter dem Regenwald-Kronendach (partial_shade), benötigt indoor aber helles indirektes Licht. Maas-Hoffman-Salztoleranzparameter (ECe-Schwelle, Slope) sind für die Art nicht publiziert; die qualitative Einstufung "sensitive" ist durch die dokumentierte Empfindlichkeit gegenüber Düngersalz-Akkumulation belegt (monatliches Durchspülen empfohlen). Der pH-Vorzug 6.0–7.0 ist konsistent mit §1.6 und §2.3; einzelne Extension-Quellen nennen einen leicht saureren Optimalbereich (pH < 6.0).

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- stomatärer Kollaps deutlich oberhalb des Zielkorridors (Oberkante 1.2 + ~0.3) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- C3-Tropenart, feuchteliebend, kein CAM --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- helles indirektes Licht ≈ offenes Tageslicht; unter Kronendach (Jungpflanze) höher --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Ruhephase niedrigere Schwelle (geringere Transpiration, trockenere Heizungsluft) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–7.0 | 100 | 40 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Mikronährstoffe Mn/Zn/Cu/Mo nach Hoagland-Standardlösung (kein art-spezifischer Wert für Ficus lyrata publiziert); Felder nutrient_profiles.manganese/zinc/copper/molybdenum_ppm --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15–20% Substratanteil | Umtopfen |
| Bokashi-Kompost | Eigenherstellen | organisch | 10% Substratanteil | Umtopfen/Frühjahr |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Überdüngung führt zu Blattrandnekrosen und -verbrennung. Bei Blattflecken: Dünger für 2 Monate aussetzen. Stickstoff für sattgrüne Blätter — aber maßvoll. Zu viel N macht Blätter weich und anfällig.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser. Staunässe ist tödlich. Obere 5 cm Erde sollten zwischen Güssen antrocknen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Standort prüfen | Licht ausreichend? Ggf. Pflanzenlampe ergänzen | hoch |
| Mär | Düngung starten | Erste Düngergabe nach Winterpause | mittel |
| Apr | Umtopfen (falls nötig) | Nur bei wurzelgebunden, max. 2 cm größerer Topf | mittel |
| Apr | Blätter reinigen | Feuchtes Tuch — verstopfte Stomata hemmen Photosynthese | mittel |
| Mai–Sep | Regelmäßig gießen | Nie austrocknen lassen, nie Staunässe | hoch |
| Sep | Düngung beenden | — | niedrig |
| Okt–Feb | Weniger gießen | Substrat zwischen Güssen deutlich abtrocknen | hoch |
| Ganzjährig | Standort NICHT wechseln | Kritischste Pflegemaßnahme | hoch |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–21 (min. 12) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; ggf. Pflanzenlampe ergänzen | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert, Substrat zwischen Güssen deutlich antrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** *Ficus lyrata* ist nicht frosthart (frost_free) — als Kübel-/Zimmerpflanze überwintert sie ganzjährig frostfrei drinnen. Falls im Sommer im Freien (geschützter, halbschattiger Stand), muss sie spätestens nach den Eisheiligen ausgeräumt und vor dem ersten Frost (Mitte Oktober, USDA 6–8) wieder eingeräumt werden. Mindesttemperatur 12°C, Optimum 16–24°C. Zugluft und plötzliche Temperaturwechsel beim Ein-/Ausräumen vermeiden — sie lösen Blattabwurf aus. Kein Knollen-Ausgraben (dig_and_store entfällt).

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, gelbe Tupfen, trockene Blätter | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Stängeln | medium |
| Weiße Fliege | Trialeurodes vaporariorum | Wolkenartige Fliegen beim Schütteln, Honigtau | easy |
| Blattlaus | Aphididae | Kolonien an Triebspitzen, Honigtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule (Phytophthora, Pythium) | fungal | Welke trotz feuchter Erde, schwarze Wurzeln, Blattverlust | Staunässe, schlechte Drainage |
| Bakterielle Blattflecken | bacterial | Braune, wässrige Flecken mit gelbem Hof | Nasses Laub, hohe Feuchtigkeit |
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Trockene Luft + feuchte Blätter |
| Physiologische Chlorose | physiological | Gelbe Blätter bei grünen Adern | Fe/Mg-Mangel, falscher pH |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 10–20 | 14–21 |
| Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | 2–5 | 21–28 |
| Metaphycus helvolus | Weichschildlaus (Coccus hesperidum, Coccidae) | 5–10 | 21–30 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Metaphycus → Weichschildläuse (Coccidae), korrekt zur in §5.1 gelisteten Coccus hesperidum --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Encarsia formosa | Weiße Fliege (Trialeurodes vaporariorum) | 3–6 | 14–21 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aphidius colemani | Blattlaus (Aphididae) | 0.5–2 | 14–21 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | — | Wattestäbchen | 0 | Schildlaus, Schmierlaus |
| Insektizidseife | biological | Kaliseife | Sprühen | 3 | Blattläuse, Weiße Fliege |
| Drainage verbessern | cultural | — | Substrat + Topf wechseln | 0 | Wurzelfäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Birkenfeige | Ficus benjamina | Gleiche Gattung | Kleiner, anpassungsfähiger |
| Gummibaum | Ficus elastica | Gleiche Gattung | Robuster, weniger lichtbedürftig |
| Monstera | Monstera deliciosa | Großblättrig, tropisch | Deutlich pflegeleichter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Ficus lyrata,"Geigenfeige;Fiddle Leaf Fig",Moraceae,Ficus,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Tropisches Westafrika",yes,10-30,30,150-300,80-180,yes,no,false,medium_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Bambino,Ficus lyrata,"ornamental;compact;dwarf",clone
Little Fiddle,Ficus lyrata,"ornamental;compact",clone
```

---

## Quellenverzeichnis

1. [Bloomscape — Fiddle Leaf Fig](https://bloomscape.com/plant-care-guide/fiddle-leaf-fig/) — Pflegehinweise
2. [Planet Natural — Ficus lyrata](https://www.planetnatural.com/ficus-lyrata/) — Kulturdaten, Schädlinge
3. [Lively Root — Fiddle Leaf Fig](https://www.livelyroot.com/blogs/plant-care/ficus-lyrata-fiddle-leaf-fig-care-guide) — Lichtanforderungen
4. [Soltech — Fiddle Leaf Fig Care](https://soltech.com/products/fiddle-leaf-fig-care) — Lichtbedarf
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
6. [NC State Extension — Ficus lyrata Plant Toolbox](https://plants.ces.ncsu.edu/plants/ficus-lyrata/) — Lichttoleranz (partial shade / bright indirect), Boden-pH, Habitat, Wuchs <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
7. [Sternberg Lab (Univ. of Miami) — Photosynthesis in hemiepiphytic species of Clusia and Ficus](https://biology.as.miami.edu/_assets/pdf/sternberg-lab/photosynthesis-in-hemiphiphytic-species.pdf) — Ficus = C3-Photosynthese <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
8. [UF/IFAS MREC — Acclimatization of Ficus benjamina](https://mrec.ifas.ufl.edu/foliage/resrpts/) — Lichtkompensationspunkt schatten-akklimatisierter Ficus-Foliage <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
9. [Hoagland solution — Wikipedia](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Standardkonzentrationen Mn/Zn/Cu/Mo <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
10. [PictureThis — How to Overwinter Ficus lyrata](https://www.picturethisai.com/care/overwinter/Ficus_lyrata.html) — Überwinterung, Mindesttemperatur <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
11. [Plant Addicts — Growing Ficus Outdoors](https://plantaddicts.com/growing-ficus-outdoors/) — Temperaturschwelle für Wuchsstillstand (~10°C) <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
12. [Zhen & Bugbee — Far-red / R:FR im Pflanzenbestand (Kontext Far-Red-Fraction)](https://academic.oup.com/jxb/article/76/3/712/7727419) — R:FR-Verhältnis offenes vs. Kronendach-Licht <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
