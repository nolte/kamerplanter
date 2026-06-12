# Kulturbirne — Pyrus communis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Pyrus communis, Gartennatur Birne, Pflanzen-Kölle Birnenbaum, GartenVielfalt Pyrus communis

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pyrus communis | `species.scientific_name` |
| Volksnamen (DE/EN) | Kulturbirne, Gemeine Birne; Pear | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Pyrus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -20°C; Blüten empfindlich gegen Spätfrost (Eisheiligen!) — Hauptproblem in Norddeutschland; spätblühende Sorten wählen | `species.hardiness_detail` |
| Heimat | Westasien, Europa | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 4.5–5.6 (Wuchs-/Phänologie-GDD-Basis; mediterrane Schwellentemperatur-Studien melden für die Hitzephase nach Endodormanz bis 6.7–8.1 °C) | `species.base_temp` |
| Lebensdauer (Jahre) | 30–60 (produktiv; Einzelbäume auf Sämlingsunterlage deutlich älter, >100) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich (vernalization required, hier: Chilling/Endodormanz-Bruch) | true | `lifecycle_configs.vernalization_required` |
| Chilling Mindest-Dauer (Tage) | 33–63 (entspr. ~800–1500 Chilling-Stunden < 7 °C, sortenabhängig) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral, kein photoperiodischer Blühtrigger --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (veredelte Containerpflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 8, 9, 10 (sortenabhängig: Sommerbirnen Aug, Herbstbirnen Sep–Okt) | `species.harvest_months` |
| Blütemonate | 4, 5 (April–Mai; VOR oder mit Apfel; Spätfrostgefahr!) | `species.bloom_months` |

**WICHTIG für Norddeutschland:** Birnen blühen früher als Äpfel und sind daher spätfrostempfindlicher. Spätblühende Sorten wählen oder geschützter Standort (z.B. Spalier an Südwand). Eisheiligen (10.–15. Mai) können Blüten schädigen.

**Befruchter:** Fast alle Birnen sind selbstunfruchtbar! Befruchtersorte pflanzen: 'Conference' + 'Williams Christ' oder 'Gute Luise' + 'Alexander Lucas'. Biologisch: Wildbirne (Pyrus pyraster) als Befruchter geeignet.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Bestäubung (Pyrus communis ist überwiegend selbstinkompatibel / Fremdbefruchter):**

| Feld | Wert | KA-Feld |
|------|------|---------|
| Befruchter erforderlich (requires pollinator) | true | `species.requires_pollinator` |
| Kreuzbefruchtungsgruppe (pollinator group) | 3 (UK-Blühgruppe; gilt z. B. für 'Conference', 'Williams'/'Bartlett', 'Gute Luise'; kompatibel mit Gruppe 2/3/4) | `species.pollinator_group` |
| Empfohlene Befruchter-Sorten (compatible pollinators) | ["Williams Christ", "Gute Luise", "Conference", "Doyenné du Comice", "Louise Bonne of Jersey", "Packham's Triumph"] | `species.compatible_pollinators` |

**Hinweis (Insektenbestäubung):** Die Übertragung des Pollens zwischen den Befruchter-Sorten erfolgt durch Insekten (v. a. Honig- und Wildbienen, Hummeln) — diese sind Bestäuber-Vektoren, NICHT Befruchter-Sorten und gehören daher nicht in `compatible_pollinators`. 'Conference' kann durch Parthenokarpie teilweise ohne Bestäubung Früchte ansetzen, liefert aber mit Befruchter größere, gleichmäßigere Früchte.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | grafting | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Ausschließlich durch Veredelung auf Unterlage. Häufige Unterlagen: Quitte A/C (schwachwüchsig, Garten), Pyrus-Sämlinge (starkwüchsig, Streuobst). Kauf als Containerpflanze empfohlen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Kerne enthalten Amygdalin (geringe Mengen; unkritisch bei normalem Verzehr) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Amygdalin (Kerne, geringe Mengen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Februar–März; nach Frost, vor Blüte) | `species.pruning_months` |

**Hinweis:** Erziehungsschnitt in den ersten 3–5 Jahren wichtig (Spindelbusch oder flache Krone). Jährlich: Lichten, Kreuztriebe entfernen, Fruchtholz verjüngen. Kein Schnitt bei Frost. FEUERBRAND: Schnittgeräte nach jedem Schnitt in 70%igem Alkohol desinfizieren!

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 60–200 (auf Quitte-Unterlage) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 60 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 300–800 (auf Quitte: 300–400; Sämling: bis 1500) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 300–600 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 400–600 (Halbstamm: 500–800) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgründige, nährstoffreiche Erde; pH 6,0–7,0; gute Drainage; nicht zu trocken | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 35 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 40–70 (auf flachwurzelnder Quitte-Unterlage eher 40–60; Sämlingsunterlage tiefer) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | moderate | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe; Maas-Hoffman a) | ~2.5 (Bernstein 1965: 10 % Ertragsrückgang; FAO stuft pear als „sensitive“, ohne belastbaren a/b-Wert) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m; Maas-Hoffman b) | <!-- DATEN FEHLEN: FAO-Daten unzureichend zur Berechnung von Threshold/Slope --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 (RHS-Optimum 6.5) | `species.soil_ph_preference` |

**Hinweis (LCP):** Der angegebene Bereich 25–35 µmol/m²/s ist der reine Lichtkompensationspunkt (Netto-Photosynthese = 0) von Spur-/Sonnenblättern verwandter Kernobst-Rosaceae (Apfel; für Pyrus liegen kaum eigene LCP-Messungen vor). Die Lichtsättigung liegt deutlich höher bei ~700–800 µmol/m²/s und gehört nicht in das LCP-Feld.

**Hinweis (Staunässe):** Auf flachwurzelnder Quitte-Unterlage werden schwere, zeitweise nasse Böden besser toleriert als auf Pyrus-Sämling; dauerhafte Staunässe schädigt jedoch beide. Einstufung daher `moderate`, nicht `tolerant`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte | 10–20 | 1 | false | false | low |
| Vegetatives Wachstum / Fruchtansatz | 90–120 | 2 | false | false | medium |
| Fruchtreife | 60–90 | 3 | false | true | high |
| Winterruhe | 120–150 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (vollsonnig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (oberhalb des Zielkorridors; stomatärer Kollaps/Wasserstress) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland/Vollsonne, R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 10000–30000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Blüte/Fruchtansatz | 1:2:1 | — | 6.0–7.0 | 120 | 60 | — | 3 | 1–2 | 0.5–1 | 0.1–0.3 | 0.02–0.05 |
| Vegetativ | 2:1:1 | — | 6.0–7.0 | 120 | 60 | — | 3 | 1–2 | 0.5–1 | 0.1–0.3 | 0.02–0.05 |
| Fruchtreife | 1:1:2 | — | 6.0–7.0 | 100 | 50 | — | 2 | 1–2 | 0.5–1 | 0.1–0.3 | 0.02–0.05 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe Mn/Zn/Cu/Mo):** Die ppm-Werte entsprechen generischen Standard-Nährlösungsbereichen für vollständige Mikronährstoffversorgung (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`); art-spezifische Bedarfswerte für Pyrus communis in Nährlösung sind in der Literatur nicht belastbar quantifiziert. Im Freiland-Bodenanbau in der Regel nur bei nachgewiesenem Mangel gezielt ergänzen (Mn/Zn-Chlorose v. a. auf kalkreichen, hoch-pH-Böden).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Obstbaum-Langzeitdünger | Compo | organisch-mineralisch | 100–150 g/m² | März–April | medium_feeder |
| Hornspäne | Oscorna | organisch | 60–80 g/m² (um Stamm) | März | Stickstoff |
| Kompost (reif) | eigen | organisch | 4–6 L/m² | Oktober/März | Bodenverbesserung |
| Patentkali | ICL Specialty Fertilizers | mineralisch | 30–50 g/m² | Juli | Fruchtqualität |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| März–Apr | Austrieb | Obstbaumdünger + Hornspäne | nach Packung | Kreisförmig um Stamm; nicht direkt anlegen |
| Jun | Vegetativ | Optional: Kalkstickstoff | niedrig | Nur bei schwachem Wachstum |
| Jul | Fruchtreife | Kalibetonter Dünger | 30–40 g/m² | Fruchtqualität; Zucker; Aroma |
| KEIN | Ab August | — | — | Triebausreifung; Frostfestigkeit |

### 3.3 Besondere Hinweise zur Düngung

Junge Bäume brauchen mehr N für Wuchs; ältere Bäume mehr P+K für Fruchtbildung. Überdüngung mit N führt zu schlechtem Zucker-/Aromagehalt und erhöhter Feuerbrandanfälligkeit (weiches Gewebe).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; in Fruchtbildungsphase regelmäßig und gleichmäßig gießen (verhindert Fruchtfall) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Schnitt | Erziehungsschnitt; Fruchtholz verjüngen; Desinfektion der Geräte! | hoch |
| Apr–Mai | Blüte | Spätfrostschutz bei Bedarf (Vlies über Nacht) | hoch |
| Jun | Junifruchtfall | Normal; ggf. Fruchtausdünnung (auf 15–20 cm Abstand) | mittel |
| Jul | Kalibetonter Dünger | Fruchtqualität verbessern | mittel |
| Aug–Okt | Ernte | Reifekontrolle: Stiel löst sich leicht; Kerne braun | hoch |
| Ganzjährig | Feuerbrand-Kontrolle | Braun/schwarz verfärbte Triebe sofort entfernen; meldepflichtig! | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme Monat | — (etablierter Baum frei winterhart bis ~-20 °C, keine Maßnahme nötig) | `overwintering_profiles.winter_action` (Monat) |
| Frühjahrs-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 2, 3 (Februar–März; Winterschnitt nach starkem Frost, vor Blüte) | `overwintering_profiles.spring_action` (Monat) |
| Winterquartier (Temp/Licht/Gießen) | — (bleibt im Freiland; kein frostfreies Quartier erforderlich) | `overwintering_profiles.winter_quarter_*` |

**Hinweis:** Etablierte Bäume sind voll winterhart (`hardy`). Nur in den ersten 1–2 Standjahren und in kalten Lagen (USDA 4–5) empfiehlt sich Schutz der Veredelungsstelle durch Anhäufeln (`earth_up`) bzw. Mulch und Stammschutz gegen Frostrisse; im Frühjahr wieder entfernen (`uncover`, März). Hauptrisiko sind nicht Winterfröste, sondern Spätfröste während der Blüte (siehe §1.2).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Birnenblattsauger | Cacopsylla pyri | Honigtau; Rußtau; Blattdeformation | leaf | vegetative | medium |
| Blutlaus | Eriosoma lanigerum | Wolliger weißer Belag an Trieben | shoot, bark | vegetative | easy |
| Birnengallmücke | Dasineura pyri | Eingerollte, verdickte Blätter | leaf | vegetative (Frühjahr) | medium |
| Blattläuse | Aphis spp. | Kolonien; Honigtau | leaf, shoot | vegetative | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Feuerbrand | bacterial (Erwinia amylovora) | Triebe verbrannt-aussehend; braun/schwarz; "Hirtenstabkrümmung"; MELDEPFLICHTIG | Warm-feuchte Witterung während der Blüte | 5–14 | Blüte |
| Birnenschorf | fungal (Venturia pyrina) | Olivgrüne bis schwarze Flecken auf Früchten und Blättern | Feuchtigkeit | 7–14 | vegetative, fruit |
| Echter Mehltau | fungal | Weißer Belag | Trocken + warm | 7–10 | vegetative |
| Monilia-Fruchtfäule | fungal (Monilinia fructicola) | Braune Flecken auf Früchten; Schimmelkissen | Verletzungen | 7–14 | Fruchtreife |

**FEUERBRAND:** Befallene Triebe sofort 50 cm im gesunden Holz schneiden; Geräte desinfizieren (70% Ethanol); Schnittgut verbrennen (NICHT kompostieren). Befall MELDEPFLICHTIG bei Behörden!

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea | Blattläuse, Blattsauger | natürliche Förderung | sofort |
| Meisen, Vögel | diverse Schädlinge | Nistkasten fördern | — |
| Ohrwürmer | Blattläuse | Unterkunft fördern (Tontöpfe) | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kupfer-Fungizid | chemical | Kupferoxydul | Vorbeugend vor Blüte und nach Blüte | 14 | Schorf, Feuerbrand-Vorbeugung |
| Schwefelkalk | chemical | Schwefelkalk | Vor Blüte (Spinnmilben, Schorf) | 14 | Schorf, Überwinterungsformen |
| Schorfresistente Sorten | cultural | — | Sortenwahl | 0 | Schorf |
| Schnitt und Desinfizieren | cultural | 70% Ethanol | Sofortmaßnahme Feuerbrand | 0 | Feuerbrand |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Sorten 'Gute Luise', 'Conference': mäßig schorfanfällig | Krankheit | `resistant_to` |
| Sorte 'Charneux': feuerbrandtoleranter | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Kernobst (Rosaceae) |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft; 30–60 Jahre Standzeit |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlausabwehr; Bestäuber anlocken | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.8 | Bestäuber fördern; aromatisch | `compatible_with` |
| Ringelblume | Calendula officinalis | 0.8 | Nützlingsförderung | `compatible_with` |
| Knoblauch | Allium sativum | 0.7 | Schorfvorbeugung (umstritten) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Apfel | Malus domestica | Teilen Feuerbrand-Erreger; Schorf-Erreger unterschiedlich | moderate | `shares_pest_risk` |
| Weißdorn | Crataegus monogyna | Feuerbrand-Wirt; muss in Feuerbrand-Risikozonen entfernt werden | severe | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Rosaceae (Kernobst) | `shares_pest_risk` | Feuerbrand, Schorf, Monilia | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Pyrus communis |
|-----|-------------------|-------------|-----------------------------------|
| Quitte | Cydonia oblonga | Kernobst; Rosaceae | Sehr robust; wenig Schädlinge; dekorativ |
| Nashi-Birne | Pyrus pyrifolia | Gleiches Genus | Runde Früchte; mancherorts robuster |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,harvest_months
Pyrus communis,"Kulturbirne;Gemeine Birne;Pear",Rosaceae,Pyrus,perennial,day_neutral,tree,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Westasien, Europa",limited,100,60,700,500,500,no,no,false,true,medium_feeder,false,hardy,"4;5","8;9;10"
```

---

## Quellenverzeichnis

1. [Naturadb — Pyrus communis](https://www.naturadb.de/pflanzen/pyrus-communis/) — Steckbrief
2. [Gartennatur — Birne](https://www.gartennatur.com/birne) — Anbau, Feuerbrand
3. [Pflanzen-Kölle — Birnenbaum](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-birnenbaum-richtig/) — Pflege, IPM
4. [GartenVielfalt — Pyrus communis](https://www.garten-vielfalt.de/de-de/gartenwelt/pflanzeninfothek/pflanzen/1249/pyrus-communis) — Kulturdaten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Genetic and molecular regulation of chilling requirements in pear (PMC11082341)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11082341/) — Apfel/Birne photoperiod-insensitiv (day_neutral); Chilling/Endodormanz statt Vernalisation; Chilling-Stunden
6. [MDPI Agronomy 2023, 13(2):518 — Agroclimatic Requirements of Traditional European Pear Cultivars](https://www.mdpi.com/2073-4395/13/2/518) — Chilling Requirement (bis 850 CH > 7 °C), Hitze-Schwellentemperatur Hitzephase 6.7–8.1 °C, GDH-Heat-Requirements
7. [KU Leuven Lirias — Comparing Apple and Pear Phenology and Model](https://lirias.kuleuven.be/server/api/core/bitstreams/be401121-c0ae-4b5d-b6b0-5ea1956f8afb/content) — GDD-Phänologiemodelle Pyrus communis; Blühverfrühung 11.5 d
8. [MDPI Agriculture 2022, 12(11):1803 — Degree Days for Harvest Date of 'Conference' Pears](https://www.mdpi.com/2077-0472/12/11/1803) — Wärmesummen-Basistemperaturen für Birne (u. a. 4.0 / 5.0 °C)
9. [FAO Irrigation & Drainage Paper 61, Annex 1 — Crop salt tolerance data](http://www.fao.org/4/y4263e/y4263e0e.htm) — Pyrus (pear) Salztoleranz-Rating „S“ (sensitive); Threshold/Slope nicht berechenbar
10. [USDA-ARS — Plant Salt Tolerance (P2246) / Maas](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — Birne salzempfindlich; Bernstein 1965 ~2.5 dS/m für 10 % Ertragsrückgang
11. [RHS — Pyrus communis (common pear)](https://www.rhs.org.uk/plants/14227/pyrus-communis-(f)/details) — Boden-pH-Optimum 6.5, sonniger Standort, Drainage
12. [biorxiv 2024 — Conference pear shade-tolerant features / Agrivoltaics](https://www.biorxiv.org/content/10.1101/2024.04.24.590973.full.pdf) — Vollsonne bevorzugt, partielle Schattentoleranz ('Conference')
13. [Tartachnyk & Blanke 2004, New Phytologist — Apfelblatt-Photosynthese](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2004.01197.x) — Lichtkompensationspunkt Kernobst-Blätter 25–35 µmol/m²/s, Sättigung 700–800
14. [Frontiers in Plant Science 2019 — Self-Incompatibility in European Pear](https://www.frontiersin.org/articles/10.3389/fpls.2019.00407/full) — Selbstinkompatibilität, Befruchter-Notwendigkeit
15. [Keepers Nursery — Pollination partners for Conference](https://www.keepers-nursery.co.uk/searchpolpartner.aspx?id=CONFER) — Befruchter-Sortenliste, Blühgruppe Conference
16. [Ashridge Nurseries — Pear Tree Pollination Groups Chart UK](https://www.ashridgetrees.co.uk/blog/pear-tree-pollination-groups-chart/) — Blühgruppen: Conference/Williams Gruppe 3, Comice Gruppe 4
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
