# Süßkirsche — Prunus avium

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Gartenratgeber Kirschbaum, Lubera Kirschbaum, Pflanzeninfothek Prunus avium, Baldur-Garten Kirschbaum, Naturadb Prunus avium

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Prunus avium | `species.scientific_name` |
| Volksnamen (DE/EN) | Süßkirsche, Vogelkirsche; Sweet Cherry, Wild Cherry | `species.common_names` |
| Familie | Rosaceae | `species.family` → `botanical_families.name` |
| Gattung | Prunus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- KORREKTUR: war long_day. Süßkirsche ist photoperiodisch insensitiv (day-neutral); Wachstum, Knospenruhe und Blühinduktion werden durch Temperatur/Chilling gesteuert, nicht durch Tageslänge. Quellen: Heide 2008 (Interaction of photoperiod and temperature in Prunus); Beck et al. 2019 (Temperature effects on floral initiation in P. avium) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Laubbaum der Rosaceae; C3-Stoffwechsel (kein C4/CAM) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (°C) | 4.5 | `species.base_temp` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Wuchs-/Phänologie-GDD-Basis (cumulative degree-days ab swollen-bud), mehrfach in P.-avium-Phänologiemodellen verwendet (T0 = 4.5 °C); KEIN Keim-Basiswert --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebensdauer (Jahre) | 30–50 | `lifecycle_configs.typical_lifespan_years` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Standzeit am Standort (konsistent mit §6.1); 15–30 produktive Jahre auf schwachen Unterlagen --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Echte Endodormanz der Knospen über Winter --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation/Chilling erforderlich | true (chilling) | `lifecycle_configs.vernalization_required` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Streng genommen Chilling/Endodormanz-Bruch, nicht klassische Vernalisation --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Chilling-Mindestdauer (Tage) | 60–90 | `lifecycle_configs.vernalization_min_days` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Entspricht dem belegten Chilling-Requirement von ~1100–1600 h bei ≤7 °C (sortenabhängig); als Kälteperioden-Dauer konservativ in Tagen abgebildet --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: nicht zutreffend, day-neutral --> | `lifecycle_configs.critical_day_length_hours` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Kein Kurztag-/Langtagblüher; Feld bleibt leer --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; Blüten empfindlich gegen Spätfrost; starkwüchsig (15–30 m) bei Sämlings-Unterlage; auf Gisela-Unterlagen kompakter (4–6 m) | `species.hardiness_detail` |
| Heimat | Europa, Westasien | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (veredelte Containerpflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7 (Juni–Juli; je nach Sorte) | `species.harvest_months` |
| Blütemonate | 4, 5 (April–Mai; gleichzeitig mit/kurz nach Apfel; Spätfrostgefahr!) | `species.bloom_months` |
| Befruchter erforderlich | true | `species.requires_pollinator` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Fast alle Süßkirschen sind gametophytisch selbstinkompatibel (selbstunfruchtbar); Fremdbefruchtung nötig --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Befruchtungsgruppe (S-Allel/Blühzeit) | <!-- DATEN FEHLEN: sortenspezifisch, nicht auf Artebene definierbar --> | `species.pollinator_group` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Pomologische Kreuzbefruchtungsgruppe (S-Allel-/Blühzeitgruppe) ist eine SORTEN-Eigenschaft (z.B. 'Kordia' Gruppe III, 'Regina' Gruppe IV), nicht artweit; daher auf Species-Ebene leer --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Empf. Befruchter-Sorten | ["Regina","Kordia","Schneiders Knorpelkirsche","Burlat"] | `species.compatible_pollinators` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- BEFRUCHTER-SORTEN (Cultivars) mit überlappender Blütezeit und kompatiblem S-Allel; KEINE Insektenarten. Hinweis: Honigbienen/Wildbienen sind als bestäubende Insekten zwingend erforderlich, gehören aber nicht in dieses Sorten-Feld --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Befruchter KRITISCH:** Fast alle Süßkirschen sind SELBSTUNFRUCHTBAR. Ohne passenden Befruchter keine oder wenig Ernte. Ausnahmen: 'Lapins', 'Stella' (selbstfruchtbar). Empfohlene Befruchterkombinationen: 'Kordia' + 'Regina', 'Burlat' + 'Schneiders Knorpelkirsche'. Gleiche Blütezeit ist PFLICHT (Gruppe A, B oder C prüfen).

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | grafting | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Unterlagen:** Vogelkirsche (Sämling: stark, 15–20 m); Gisela 5 (schwach-mittel: 4–6 m, früh tragend, empfehlenswert für Gärten); Maxma 14 (mittel-stark).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Kerne und Blätter enthalten Amygdalin; Früchte sicher | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Amygdalin (Kerne; bei Knacken freigesetzt) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (Juli–August nach der Ernte) | `species.pruning_months` |

**KRITISCH:** Kirschbäume NUR im Sommer schneiden (August–September nach Ernte) — NIEMALS im Winter oder Frühjahr! Wundverschluss durch Cambium-Aktivität im Sommer schneller; Infektionsrisiko durch Holzschutzkrankheiten (Nectria, Scharkavirus-Eintritt durch Wunden) im Winter viel höher.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 100–200 (nur auf schwachen Unterlagen wie Gisela 5) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 60 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 400–800 (Gisela 5: 400–600) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 400–800 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 500–800 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgründige, nährstoffreiche Erde; pH 6,0–7,5; gut durchlässig; kein Staunässe | — |

### 1.7 Umgebungs-Physiologie & Standortqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein belegter cherry-spezifischer LCP-Zahlenwert in 2 unabhängigen Quellen --> | `species.light_compensation_point_ppfd_min` / `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 40–80 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: FAO/USDA führen Süßkirsche nur als Schätzung ("sensitive") ohne eigene Maas-Hoffman-Zahlen --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: keine artspezifischen Maas-Hoffman-b-Werte für P. avium --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweise (Freitext, nicht in KA-Feld):**
- *Schatten:* Süßkirsche toleriert lichten Halbschatten ("succeeds in light shade"), fruchtet aber deutlich besser in voller Sonne — für Ertrag full_sun anstreben.
- *Wurzeltiefe:* Etablierte Bäume bilden überwiegend einen flach streichenden Wurzelteller; die Feinwurzel-Hauptmasse liegt in den oberen 40–80 cm. Die anfängliche Pfahlwurzel (`root_type: taproot`) reicht auf Sämlingsunterlage tiefer, ist für die effektive Wasser-/Nährstoffaufnahme etablierter Bäume aber weniger maßgeblich.
- *Salztoleranz:* Bewässerungswasser ab ~4 dS/m verursacht schwere Schäden bis Absterben auf Mazzard-Unterlagen; verwandte Prunus-Arten liegen bei einer Substrat-ECe-Schwelle von 1.5–1.7 dS/m (Mandel/Aprikose/Pfirsich), was die Einordnung "sensitive" stützt. Bezugsgröße ist die Substrat-ECe (Sättigungsextrakt), NICHT die Gießwasser-EC.
- *pH:* Kern-Vorzug 6.0–7.0; toleriert leicht saure bis schwach alkalische Böden bis ~7.5 (harmonisiert mit §1.6/§2.3); auf stark alkalischen Böden steigt das Risiko von Eisen-/Mangan-Chlorose.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte | 7–14 | 1 | false | false | low |
| Fruchtansatz / Vegetativ | 60–90 | 2 | false | false | medium |
| Fruchtreife | 14–30 | 3 | false | true | high |
| Sommerwachstum / Blütenanlage | 90–120 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtreife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (vollsonnig; Reife-Beschleunigung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Beschreibt die natürliche Sommertaglänge (Lichtangebot/DLI), KEIN photoperiodischer Blühtrigger — Art ist day-neutral; Phasenübergänge sind temperatur-/chilling-gesteuert --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.4 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Kritische Schwelle des stomatären Kollaps, deutlich oberhalb der vpd_target-Oberkante (1.4 + ~0.4); in der trockenheitsexponierten Reifephase --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- C3-Laubbaum, mesophil; keine sukkulente Wasserspeicherung --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Netto-Photosynthese bei 25/15 °C deutlich höher als bei 35/25 °C; gemäßigtes C3-Optimum, konsistent mit Tag-Temp 18–28 °C --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Vollsonnige Freilandkultur; direkte Sonnenstrahlung FR-Fraction ≈ 0.46–0.5 (R:FR ≈ 1.1–1.3); NICHT das R:FR-Verhältnis --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 10000–30000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**WICHTIG:** Kein Starkregen in der Reifephase (Platzen der Früchte). Witterungsschutz durch Überdachung bei Tafelkirschen-Kulturen.

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Blüte/Fruchtansatz | 1:2:1 | — | 6.0–7.5 | 150 | 60 | — | 3 | 40–150 | 20–50 | 6–16 | <1 |<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vegetativ | 2:1:1 | — | 6.0–7.5 | 120 | 60 | — | 3 | 40–150 | 20–50 | 6–16 | <1 |<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Fruchtreife | 1:1:2 | — | 6.0–7.5 | 100 | 50 | — | 2 | 40–150 | 20–50 | 6–16 | <1 |<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> Mikronährstoffe Mn/Zn/Cu/Mo (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`) als Blatt-Gewebe-Suffizienzbereiche (Steinobst/Kirsche): Mn 40–150, Zn 20–50, Cu 6–16, Mo <1 ppm. Mangelschwellen: Zn <20 ppm, Mn <40 ppm (Sommerblattprobe). Auf alkalischen Böden Mn-/Zn-Mangel ("Kleinblättrigkeit", interkostale Chlorose) beachten. <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Obstbaum-Langzeitdünger | Compo | organisch-mineralisch | 100–150 g/m² | März–April | medium_feeder |
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März–April | Stickstoff |
| Kompost (reif) | eigen | organisch | 4–6 L/m² | Oktober/März | Bodenverbesserung |
| Jauche / Brennnesseljauche | — | organisch | 1:10 verdünnt; gießen | Mai–Juni | Stickstoff, Vitalisierung |

### 3.2 Besondere Hinweise zur Düngung

Kirschbäume brauchen weniger Stickstoff als Birnen. Überdüngung fördert starkes Triebwachstum auf Kosten der Fruchtbildung und erhöht Monilia-Anfälligkeit (weiches Gewebe). Kein Dünger nach Ende Juni.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; bei Trockenheit gießen; in der Reifephase KEIN Starkregen (Platzen); eventuell überdachen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 0 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr–Mai | Blüte / Bestäubung | Spätfrostschutz bei Bedarf; Befruchter-Blüte kontrollieren | hoch |
| Jun | Ernte Frühsorten | Vögel schützen (Netz); Ernte morgens | hoch |
| Jul–Aug | Ernte Spätsorten | Vollreif ernten; Regenschutz beachten | hoch |
| Aug–Sep | Schnitt NACH Ernte | NUR im Sommer schneiden! Werkzeuge desinfizieren | hoch |
| Ganzjährig | Monilia-Kontrolle | Befallene Früchte sofort entfernen + vernichten | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |
| Winter-Maßnahme Monat | — (keine; ausgepflanzt winterhart) | `overwintering_profiles.winter_action_month` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Ausgepflanzter, voll winterharter Baum (bis ~-25 °C); keine schützende Winter-Maßnahme nötig. Ausnahme nur Kübelkultur auf Gisela 5: Topf frostfrei stellen/einpacken (winter_action wrap, Nov) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Frühjahrs-Maßnahme | prune (Sommerschnitt vorbereiten), Spätfrostschutz Blüte | `overwintering_profiles.spring_action` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Kein Abdecken nötig; im Frühjahr nur Spätfrostschutz der Blüte (Apr–Mai). Schnitt erst nach Ernte (Sommer, §1.5) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Frühjahrs-Maßnahme Monat | 4–5 (Spätfrostschutz Blüte) | `overwintering_profiles.spring_action_month` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterquartier Temp/Licht | nicht zutreffend (Freiland) | `overwintering_profiles.winter_quarter` |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Kein Winterquartier; nur bei Kübelhaltung Topf vor Durchfrieren schützen (geschützter Standort, kein Heizbedarf, gelegentlich frostfrei wässern) --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis:** Süßkirsche ist als ausgepflanzter Baum vollständig winterhart (`hardiness_rating: hardy`) und benötigt keine Überwinterungsmaßnahme. Frostkritisch ist nicht der Winter, sondern Spätfrost zur Blüte (April–Mai). Nur in Kübelkultur (schwache Unterlagen) den Topfballen vor Durchfrieren schützen.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kirschfruchtfliege | Rhagoletis cerasi | Maden in Früchten; weiße Maden in Kirschen | fruit | Fruchtreife | difficult |
| Spinnmilbe | Tetranychus urticae | Blattvergilbung; Gespinste | leaf | vegetative (Hitze) | medium |
| Kirschenblattlaus | Myzus cerasi | Kolonien; eingerollte Blätter | leaf, shoot | vegetative (Frühjahr) | easy |
| Vögel | Sturnus vulgaris, Turdus spp. | Fruchtschäden, Anpicken | fruit | Fruchtreife | easy |

**Kirschfruchtfliege:** Gelbtafeln aufhängen ab Ende Mai; Befallstoleranzschwelle: 2 Fliegen/Tafel; bei Überschreitung Behandlung. Alternativ: Ernte vor Madenbefall (frühe Sorten!).

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Monilia-Spitzendürre | fungal (Monilinia laxa) | Welkende Blütenstände; "Braunfäule"; Triebsterben | Feuchte Witterung zur Blüte | 5–10 | Blüte |
| Monilia-Fruchtfäule | fungal (Monilinia fructicola) | Braune Faulflecken auf Früchten | Feuchtigkeit, Verletzungen | 7–14 | Fruchtreife |
| Kirschensprühfleckenkrankheit | fungal (Blumeriella jaapii) | Rote Flecken auf Blättern; Blätter fallen früh | Feuchtigkeit | 14–21 | vegetative |
| Scharkavirus | viral (PPV = Plum Pox Virus) | Ringen und Flecken auf Früchten und Blättern; keine direkte Behandlung | Blattläuse (Übertragung) | — | alle |

**Monilia:** Befallene Triebe mind. 30 cm ins gesunde Holz schneiden. Schnittstellen desinfizieren.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Vogelschutznetze | Vögel | — (physischer Schutz) | sofort |
| Schlupfwespen | Fruchtfliege | natürliche Förderung | — |
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |
| Aphidius colemani | Kirschenblattlaus (Myzus cerasi) | 0.5–2 (Schlupfwespen-Parasitoid) | 14–21 |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Aphidius/Aphidoletes → Blattläuse (korrekte Wirt-Zuordnung); ergänzt den bestehenden Blattlaus-Nützling Chrysoperla --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aphidoletes aphidimyza | Kirschenblattlaus (Myzus cerasi) | 1–4 (Gallmücken-Larven) | 14 |<!-- Quelle: Steckbrief-Erweiterung 2026-06 --> <!-- Räuberische Gallmücke gegen Blattläuse --> <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Vogelschutznetze | cultural | — | Ab Fruchtfärbung | 0 | Vögel |
| Gelbtafeln | cultural | — | Aufhängen Ende Mai | 0 | Kirschfruchtfliege |
| Natrium-Bentonit (Surround WP) | biological | Kaolin | Sprühen; Film auf Früchten | 0 | Fruchtfliege |
| Kupfer-Fungizid | chemical | Kupferoxydul | Vor Blüte; nach Blüte | 14 | Monilia, Sprühflecken |
| Sommer-Schnitt | cultural | — | Luftzirkulation verbessern | 0 | Monilia |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Steinobst (Rosaceae) |
| Anbaupause (Jahre) | Mehrjährig; Standort dauerhaft; 30–50 Jahre Standzeit |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestäuber | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlausabwehr | `compatible_with` |
| Knoblauch | Allium sativum | 0.7 | Pilzvorbeugung (umstritten) | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Pflaume | Prunus domestica | Scharkavirus-Übertragung; gleiche Pilzkrankheiten | severe | `shares_pest_risk` |
| Aprikose | Prunus armeniaca | Gleiche Krankheiten; Scharkavirus | moderate | `shares_pest_risk` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Rosaceae (Steinobst) | `shares_pest_risk` | Monilia, Scharkavirus, Rindenerkrankungen | `shares_pest_risk` |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,harvest_months
Prunus avium,"Süßkirsche;Vogelkirsche;Sweet Cherry",Rosaceae,Prunus,perennial,day_neutral,tree,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",-0.1,"Europa, Westasien",limited,150,60,700,600,600,no,no,false,true,medium_feeder,false,hardy,"4;5","6;7"
```

---

## Quellenverzeichnis

1. [Gartenratgeber — Kirschbaum](https://www.gartenratgeber.net/pflanzen/kirschbaum-prunus-cerasus-avium.html) — Düngen, Schnitt
2. [Lubera — Kirschbaum pflanzen](https://www.lubera.com/de/gartenbuch/kirschbaum-pflanzen-p2245) — Unterlagen, Befruchter
3. [Pflanzeninfothek — Prunus avium](https://www.pflanzeninfothek.de/artikel/2629/prunus-avium) — Steckbrief
4. [Baldur-Garten — Kirschbaum schneiden](https://www.baldur-garten.de/onion/content/pflege-tipps/obst/kirschbaum-(prunus-avium)) — Schnitt-Zeitpunkt
5. [Naturadb — Prunus avium](https://www.naturadb.de/pflanzen/prunus-avium/) — Ökologie
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [ScienceDirect — Phenological models for sweet cherry (P. avium), Mediterranean climate](https://www.sciencedirect.com/science/article/abs/pii/S0304423823008798) — GDD-Basistemperatur 4.5 °C, Phänologiemodelle
7. [ISHS — Chilling unit accumulation and degree-day requirements of four sweet cherry cultivars](https://ishs.org/ishs-article/1020_29/) — Chilling-Requirement, Endodormanz, GDD
8. [ISHS — Chilling requirements of sweet cherries and interspecific hybrids](https://www.ishs.org/ishs-article/169_40) — Chilling ~1100–1600 h ≤7 °C
9. [Heide (2008), ScienceDirect — Interaction of photoperiod and temperature in dormancy of Prunus species](https://www.sciencedirect.com/science/article/abs/pii/S0304423807003421) — Photoperiod-Insensitivität (day-neutral), Temperatursteuerung
10. [ScienceDirect — Temperature effects on growth and floral initiation in sweet cherry](https://www.sciencedirect.com/science/article/abs/pii/S030442381930648X) — Blühinduktion temperaturgesteuert, T_opt-Bereich
11. [FAO — Crop salt tolerance data (Maas-Hoffman, Annex 1)](https://www.fao.org/4/y4263e/y4263e0e.htm) — Salztoleranz Kirsche = sensitive (S), Prunus-Schwellen 1.5–2.6 dS/m
12. [USDA-ARS — Plant Salt Tolerance (Maas & Grattan)](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — Süßkirsche sensitiv (Blattschäden)
13. [PFAF — Prunus avium](https://pfaf.org/user/Plant.aspx?LatinName=Prunus+avium) — Schattentoleranz (partial_shade), pH, Staunässe, Flachwurzler
14. [Penn State Extension — Orchard Nutrition: An Overview](https://extension.psu.edu/orchard-nutrition-an-overview) — Blatt-Suffizienzbereiche Mn/Zn/Cu/B für Kirsche
15. [WSU Tree Fruit — Micronutrients](https://treefruit.wsu.edu/micronutrients/) — Mangelschwellen Zn <20, Mn <40 ppm
16. [Garden Oracle — Growing Sweet Cherry: Prunus avium](https://gardenoracle.com/images/prunus-avium.html) — Lebensdauer 15–30 produktive Jahre, pH 6.0–7.0
17. [HortiDaily — Ratios in the light spectrum (R:FR, far-red fraction)](https://www.hortidaily.com/article/9089222/ratios-in-the-light-spectrum-a-brief-overview/) — Vollsonne FR-Fraction ≈ 0.46–0.5
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
