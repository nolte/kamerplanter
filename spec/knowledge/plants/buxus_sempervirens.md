# Buchsbaum — Buxus sempervirens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Buxus sempervirens, Plantura Buchsbaum-Pflege, Buchsbaumzuensler.net, Pflanzen-Kölle Buchsbaum

---

> **WICHTIGER HINWEIS:** Buxus sempervirens ist in Mitteleuropa seit ca. 2007 massiv durch den eingeschleppten Buchsbaumzünsler (Cydalima perspectalis) und seit 2004 durch den Pilz Cylindrocladium buxicola (Buchsbaum-Triebsterben) bedroht. Für Neuanpflanzungen in Deutschland wird von vielen Fachleuten inzwischen empfohlen, Alternativen wie Ilex crenata, Taxus baccata oder Euonymus zu wählen. Bestehende Buchsbäume können mit entsprechendem Aufwand erhalten werden.

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Buxus sempervirens | `species.scientific_name` |
| Volksnamen (DE/EN) | Buchsbaum, Gemeiner Buchsbaum; Common Box, European Boxwood | `species.common_names` |
| Familie | Buxaceae | `species.family` → `botanical_families.name` |
| Gattung | Buxus | `species.genus` |
| Ordnung | Buxales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: keine artspezifische GDD-Basis aus 2 unabhängigen seriösen Quellen belegbar --> | `species.base_temp` |
| Lebensdauer (Jahre, Kultur) | 70–150 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (kein Kältebedarf für Wachstum/Blüte) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 5a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis ca. -23°C (Zone 6a); frischer Austrieb im Frühjahr frostempfindlich (-3°C); Wintersonne und Windschutz bei Jungpflanzen empfehlenswert | `species.hardiness_detail` |
| Heimat | Südeuropa, Nordafrika, Vorderasien | `species.native_habitat` |
| Allelopathie-Score | -0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklingsvermehrung üblich; Aussaat dauert 2 Jahre) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; nicht essbar) | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (unscheinbare Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (10–15 cm, halbverholzt) im August/September in Anzuchterde; bewurzeln in 4–8 Wochen unter Folie. Aussaat aus Samen sehr langsam (2 Jahre bis pflanzfähige Pflanze).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | ALLE Pflanzenteile (Blätter, Rinde, Samen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Buxin (Steroidal-Alkaloid), Buxenin, Cyclobuxin | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Kontaktdermatitis möglich beim Schneiden) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Vergiftungssymptome: Brechreiz, Krämpfe, Lähmungserscheinungen. Beim Formschnitt Handschuhe tragen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6, 8 | `species.pruning_months` |

**Hinweis:** Formschnitt am besten im Juni (nach dem Johannistag, 24. Juni — traditionelle Regel); zweiter leichter Schnitt möglich Ende August. Nicht nach Ende August schneiden — frischer Austrieb erfriert im Winter. Bis zu 3× jährlich möglich.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–500 (je nach Schnitt 20–300 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–200 (je nach Schnitt) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–60 (Hecke: 30–40 cm Pflanzabstand) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, durchlässige Erde; pH 6,5–7,5; keine Staunässe; Balkonkastenerde mit Perlite | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: keine artspezifischen LCP-Messwerte aus 2 frei zugänglichen seriösen Quellen belegbar (Primärstudien paywall) --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: keine artspezifischen LCP-Messwerte aus 2 frei zugänglichen seriösen Quellen belegbar --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | deep_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine publizierte Maas-Hoffman-Schwelle für die Art (ornamental, nicht in Salztoleranz-Datensätzen quantifiziert) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein publizierter Maas-Hoffman-Slope für die Art --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.5–7.5 | `species.soil_ph_preference` |

**Hinweis (Lichtphysiologie):** Buxus sempervirens ist eine ausgesprochen schattentolerante (deep_shade) immergrüne Art und toleriert sogar tiefen Schatten unter Baumkronen; in voller Sonne nur bei zuverlässig feuchtem Boden, sonst Blattverbrennungen (leaf scorch). Die Art zeigt ein "Stress-Resistance-Syndrome" mit nur geringer Änderung der Netto-Photosynthese über einen weiten Lichtgradienten.

**Hinweis (Salz):** Über alle Salzquellen hinweg (Sprühsalz, Bodensalz, Auftausalz) als salzempfindlich (sensitive) eingestuft — ungeeignet für Küstenlagen und straßennahe Pflanzungen mit Auftausalzeintrag. Bezugsgröße der (hier nicht quantifizierbaren) Schwelle wäre Substrat-ECe, nicht die Gießwasser-EC.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzelung (Steckling) | 28–60 | 1 | false | false | low |
| Jungpflanze (1.–3. Jahr) | 365–1095 | 2 | false | false | medium |
| Etabliert (Schnittphase) | fortlaufend | 3 | true | false | high |
| Winterruhe | 90–120 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Jungpflanze (1.–3. Jahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 (Halbschatten bis Sonne; Jungpflanzen nicht in pralle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 5–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht / Halbschatten) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Etabliert (Schnittphase)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 (toleriert Halbschatten bis Vollsonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Jungpflanze | 2:1:1 | 1.0–1.4 | 6.5–7.0 | 100 | 50 | – | 2 |
| Wachstum (Frühjahr) | 3:1:2 | 1.2–1.6 | 6.5–7.0 | 120 | 60 | – | 3 |
| Formschnitt-Phase | 2:1:2 | 1.0–1.4 | 6.5–7.0 | 100 | 50 | – | 2 |
| Herbstvorbereitung | 1:1:3 | 0.8–1.2 | 6.5–7.0 | 80 | 50 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe Mn/Zn/Cu/Mo (ppm) je Phase:** <!-- DATEN FEHLEN: keine artspezifischen Ziel-ppm für Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) aus 2 unabhängigen seriösen Quellen für Buxus sempervirens belegbar. KA-Felder `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm` bleiben daher unbelegt. -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Einwurzelung → Jungpflanze | time_based | 42–60 Tage | Wurzeln sichtbar; Steckling treibt aus |
| Jungpflanze → Etabliert | time_based | 365–730 Tage (1–2 Jahre) | Formschnitt möglich ohne Substanz-Verlust |
| Etabliert → Winterruhe | time_based | Oktober | Temperatur < 5°C dauerhaft |
| Winterruhe → Etabliert | time_based | März–April | Temperaturen > 8°C; Neuaustrieb sichtbar |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch/Spezial (für Buchsbaum)

| Produkt | Marke | Typ | EC/Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-------------|-----------------|--------|
| Buchsbaum-Dünger | Compo Buxus | spezial | 80–100 g/m² | 1 | Frühjahr, Sommer |
| Buchsbaum-Langzeitdünger | Substral Osmocote | slow_release | 50 g/m² einarbeiten | 1 | April |
| Buchsbaum-Dünger granulat | Neudorff Azet | organisch-mineral | 60 g/m² | 1 | April, Juni |

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März–April | medium_feeder |
| Kompost | eigen | organisch | 3–4 L/m² | März | Bodenverbesserung |
| Kaliumsulfat | diverse | mineral | 30 g/m² | September | Winterhärtung |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| April (Vegetationsbeginn) | N-betont (3:1:2) | Buchsbaum-Spezial | 80–100 g/m² | Stickstoff für Triebwachstum |
| Juni (nach Formschnitt) | ausgewogen (2:1:2) | Langzeitdünger | 40–50 g/m² | Regeneration nach Schnitt |
| August | K-betont (1:1:3) | Kaliumsulfat | 30 g/m² | Winterhärtung; KEIN N mehr! |

### 3.3 Besondere Hinweise zur Düngung

Kein Stickstoff nach Ende Juli — sonst bildet Buchsbaum weiche, frostempfindliche Triebe. Zweimalige Düngung pro Jahr ausreichend. Eisen-Chlorose bei hohem pH (über 7,5) möglich — Bodenpflege mit Rhododendronerde oder Schwefel. Im Topf alle 3–4 Wochen schwach flüssig düngen (April–Juli).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Verträgt normales Leitungswasser; pH 6,5–7,5; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60–90 (2× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wegen Buchsbaumzünsler!) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Winterschutz entfernen | Vlies abnehmen; Austrieb prüfen | hoch |
| Apr | Erste Düngung | Buchsbaum-Spezial; mit Wasser einarbeiten | hoch |
| Apr–Mai | Buchsbaumzünsler-Kontrolle | Raupennester in Innentrieben suchen; erste Generation | hoch |
| Jun | Formschnitt (Johannistag, 24. Jun.) | Traditioneller Schnittzeitpunkt; zweiter leichter Schnitt möglich | hoch |
| Jun | Zweite Düngung | Nach Formschnitt; ausgewogenes NPK | mittel |
| Jul–Aug | Schädlingskontrolle | Buchsbaumzünsler 2. Generation (Juli–August) | hoch |
| Aug | Zweiter Formschnitt | Letzter Schnitt des Jahres; vor Ende August! | mittel |
| Sep | Kaliumbetonte Düngung | Winterhärtung; kein N mehr | mittel |
| Okt–Nov | Winterschutz | Jungpflanzen und Topfbuchsbaum schützen; Vlies bei -10°C | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | fleece | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (Freiland) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | — (Freiland) | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | — | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Buchsbaumzünsler | Cydalima perspectalis | Kahlfraß; Gespinste im Innern; grün-schwarze Raupen | leaf, shoot, bark | alle (Frühjahr–Herbst) | easy |
| Buchsbaumblattfloh | Psylla buxi | Löffelförmig eingerollte Blätter; weißliche Wachsfäden | shoot, leaf | spring | medium |
| Buchsbaumschildlaus | Parthenolecanium persicae | Braune Schuppen auf Ästen; Schäden durch Saugen | bark, shoot | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Buchsbaum-Triebsterben | fungal (Cylindrocladium buxicola / Calonectria pseudonaviculata) | Braune Streifen auf Stängeln; Blätter fallen ab; kahle Äste | Feuchtigkeit, dichter Stand | 7–21 | alle (Feuchteperioden) |
| Buchsbaum-Wurzelpilz | fungal (Phytophthora spp.) | Vergilben; Welken; braune Wurzeln | Staunässe | 14–28 | alle |
| Echter Mehltau | fungal (Erysiphe spp.) | Weißer Belag auf Trieben | Trockenheit, schlecht belüftet | 5–10 | Sommer |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Bacillus thuringiensis var. kurstaki (Bt) | Buchsbaumzünsler-Raupen | nach Etikett (Sprühlösung) | sofort wirksam |
| Trichogramma-Schlupfwespen | Buchsbaumzünsler-Eier | 3–5 Karten/m² | sofort bei Eiablage |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Bt-Präparate (XenTari, Dipel) | biological | Bacillus thuringiensis | Sprühen auf Raupen (L1–L3) | 0 | Buchsbaumzünsler |
| Neem-Präparate | biological | Azadirachtin | Frühbehandlung ab Austrieb | 3 | Zünsler (jung), Blattfloh |
| Trichogramma | biological | Parasitoide Wespe | Karten in Pflanzen hängen | 0 | Zünsler-Eier |
| Tefluthrin (Insektizid) | chemical | Pyrethroid | nach Etikett; nur bei starkem Befall | 14 | Buchsbaumzünsler |
| Fungizid Trifloxystrobin | chemical | Strobilurin | Sprühen bei Zylinderbefall | 14 | Cylindrocladium |
| Befallene Triebe entfernen | cultural | – | Sofortentfernung; Verbrennen | 0 | Cylindrocladium |
| Luftzirkulation verbessern | cultural | – | Auslichten bei dichtem Stand | 0 | Cylindrocladium, Mehltau |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine signifikante Resistenz gegen Cydalima perspectalis bekannt | Schädling | — |
| Buxus sempervirens 'Suffruticosa' weniger anfällig als 'Handsworthiensis' | — | — |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Dauergehölz (kein Fruchtwechsel relevant) |
| Empfohlene Vorfrucht | — (Dauergehölz) |
| Empfohlene Nachfrucht | — (Dauergehölz) |
| Anbaupause (Jahre) | Keine Neupflanzung in Buchsbaumboden (Cylindrocladium-Kontamination): 3–5 Jahre Pause |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Efeublättriger Storchschnabel | Geranium robertianum | 0.6 | Bodendecker; unterdrückt Unkraut | `compatible_with` |
| Taglilie | Hemerocallis spp. | 0.6 | Frühzeitiger Bodenschluss | `compatible_with` |
| Schafgarbe | Achillea millefolium | 0.6 | Trockenstresstoleranz; Nützlinge | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Taxus (als Heckenpartner) | Taxus baccata | Wurzelkonkurrenz bei engem Stand; Taxus verdrängt Buxus durch stärkeres Wurzelwerk | mild | `incompatible_with` |
| Farne | Dryopteris spp. | Teilen Feuchtestandort; fördern Pilzkrankheiten | mild | `incompatible_with` |

### 6.4 Alternativen zu Buxus sempervirens

> **Empfehlung für Norddeutschland:** Angesichts der Buchsbaumzünsler-Problematik und des Cylindrocladium-Risikos werden folgende Alternativen empfohlen:

| Alternative | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-------------|-------------------|-------------|---------|
| Japanische Stechpalme | Ilex crenata 'Dark Green' | Sehr ähnliches Aussehen | Buchsbaumzünsler-resistent; ähnlich schnittverträglich |
| Eibe | Taxus baccata | Formschnittgehölz | Sehr langlebig; toleriert tiefen Schatten |
| Euonymus | Euonymus fortunei | Immergrün | Robuster; Bodendecker möglich |
| Rhododendron 'Bloombux' | Rhododendron 'Bloombux' | Kompakt, immergrün | Zünsler-resistent; blüht |
| Zwergliguster | Ligustrum vulgare 'Lodense' | Niedriger Heckentipp | Robust; anspruchslos |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Buxus sempervirens,"Buchsbaum;Gemeiner Buchsbaum;Common Box",Buxaceae,Buxus,perennial,day_neutral,shrub,fibrous,"5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",-0.2,"Südeuropa, Nordafrika, Vorderasien",yes,22,30,300,150,40,no,yes,false,false,medium_feeder,false,hardy,"3;4;5"
```

---

## Quellenverzeichnis

1. [Naturadb Buxus sempervirens](https://www.naturadb.de/pflanzen/buxus-sempervirens/) — Steckbrief, Standort
2. [Plantura Buchsbaum-Pflege](https://www.plantura.garden/gehoelze/buchsbaum/buchsbaum-pflegen) — Schnitt, Düngung, Krankheiten
3. [Buchsbaumzuensler.net — Buchsbaum im Garten](https://www.buchsbaumzuensler.net/buchsbaeume-im-garten/) — Zünsler-Bekämpfung
4. [Buchsbaumersatz-Alternativen](https://www.buchsbaumzuensler.net/buchsbaum-alternativen/) — Alternativpflanzen
5. [Pflanzen-Kölle Buchsbaum-Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-buchs-richtig/) — Allgemeine Pflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Buxus sempervirens (common box)](https://www.rhs.org.uk/plants/2579/buxus-sempervirens/details) — Lichtansprüche/Schattentoleranz (deep_shade), Standort
7. [RHS — How to grow box (Growing Guide)](https://www.rhs.org.uk/plants/box/growing-guide) — Drainage/Staunässe-Empfindlichkeit, Sonnenbrand bei Trockenheit
8. [Purdue Extension — Salt Damage in Landscape Plants (ID-412-W)](https://www.extension.purdue.edu/extmedia/id/id-412-w.pdf) — Salzempfindlichkeit (sensitive) Buxus sempervirens
9. [Virginia Cooperative Extension — Trees and Shrubs that Tolerate Saline Soils and Salt Spray Drift](https://www.pubs.ext.vt.edu/430/430-031/430-031.html) — Salztoleranz-Einordnung Gehölze
10. [North Carolina Extension Gardener Plant Toolbox — Buxus sempervirens](https://plants.ces.ncsu.edu/plants/buxus-sempervirens/) — Wuchsform, immergrünes Breitblattgehölz (C3-Einordnung), Standort
11. [PFAF — Buxus sempervirens](https://pfaf.org/user/Plant.aspx?LatinName=Buxus+sempervirens) — pH-Spanne, alkalische Standorte, Standortansprüche
12. [Springer/Trees — Long-term acclimation of Buxus sempervirens to understory and canopy gap light](https://link.springer.com/article/10.1007/s00468-011-0609-z) — Schattentoleranz, Photosynthese-Licht-Reaktion (Stress-Resistance-Syndrome)
13. [Woodland Trust — Common Box (Buxus sempervirens)](https://www.woodlandtrust.org.uk/trees-woods-and-wildlife/british-trees/a-z-of-british-trees/box/) — Langlebigkeit/Lebensdauer
14. [PictureThis — Optimal Temperature for Common boxwood](https://www.picturethisai.com/care/temperature/Buxus_sempervirens.html) — Optimal-Temperaturband 15–24 °C (Grundlage Photosynthese-T_opt)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
