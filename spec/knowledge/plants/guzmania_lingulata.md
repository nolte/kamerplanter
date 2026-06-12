# Bromelie (Scharlachrote Guzmanie) -- Guzmania lingulata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** ASPCA, Bromeliads.info, UKHouseplants, PlantCareToday, Thursd.com, JoyUsGarden, Clemson University Extension

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Guzmania lingulata | `species.scientific_name` |
| Volksnamen (DE/EN) | Bromelie, Guzmanie, Scharlachrote Guzmanie; Scarlet Star, Tufted Airplant, Droophead Tufted Airplant | `species.common_names` |
| Familie | Bromeliaceae | `species.family` -> `botanical_families.name` |
| Gattung | Guzmania | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Wurzelanpassungen | epiphytic | `species.root_adaptations` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 (constitutiv; nur fakultativ/schwach CAM unter Trockenstress -- anders als die meisten Bromelien, die konstitutiv CAM sind. Guzmania lingulata assimiliert CO2 als Adult und Juvenil primaer ueber C3, kann unter Wasserdefizit jedoch CAM-Zuege ausbilden.) | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phaenologie-GDD-Basiswert fuer diese tropische Zierbromelie auffindbar; nur Optimal-/Minimaltemperaturen dokumentiert (Min. 13-15 C, optimal 18-27 C). Keimungs-Kardinaltemperaturen wurden bewusst NICHT als Wuchsbasis umetikettiert. --> | `species.base_temp` |
| Kritische Tageslaenge (h) | -- (day_neutral / tagneutral -- kein Kurztag-/Langtag-Bluehverhalten; Bluete wird ueber Reife + Ethylen ausgeloest, nicht ueber Photoperiode) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial (Hinweis: Mutterpflanze ist monokarp -- stirbt nach einmaliger Bluete; das Pflanzensystem ist durch Kindel-Bildung perennial; cycle_type=perennial gilt fuer das Gesamtsystem) | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 2-3 (Mutterpflanze; Kindel ueberdauern) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b, 12a, 12b | `species.hardiness_zones` |
| Frostempfindlichkeit | sensitive | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15 C, optimal 18-27 C. Keine Temperaturen unter 13 C. | `species.hardiness_detail` |
| Heimat | Tropische Regenwaelder Mittel- und Suedamerikas (Mexiko bis Bolivien), Karibik | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Besonderheit Lebenszyklus:** Guzmania lingulata ist eine **monokarpe** (einmal bluehende) Bromelie. Die Mutterpflanze stirbt nach der Bluete innerhalb von 1-2 Jahren ab, bildet aber vorher 1-5 Ableger (Kindel, Pups), die den Lebenszyklus fortsetzen. Der gesamte Zyklus von Kindel bis Bluete dauert ca. 2-3 Jahre.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfaellt (reine Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Entfaellt | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | Entfaellt | `species.direct_sow_months` |
| Erntemonate | Entfaellt | `species.harvest_months` |
| Bluetemonate | Bluete Indoor moeglich, haeufig im Spaetsommer/Herbst. Bluetenstand haelt 2-4 Monate. | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Die primaere Vermehrungsmethode ist ueber Kindel (Offsets/Pups). Die Mutterpflanze bildet nach der Bluete 1-5 Kindel an der Basis. Diese koennen abgetrennt werden, sobald sie ca. 1/3 bis 1/2 der Groesse der Mutterpflanze erreicht haben und eigene Wurzeln gebildet haben. Samen-Vermehrung ist moeglich, aber sehr langwierig (3-4 Jahre bis zur Bluete) und in der Praxis unueblich.

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Haustierfreundlich:** Guzmania lingulata ist nach ASPCA-Daten ungiftig fuer Katzen und Hunde. Die Pflanze ist daher eine ausgezeichnete Wahl fuer Haushalte mit Haustieren, die trotzdem eine attraktive tropische Zimmerpflanze wuenschen.

### 1.5 Luftreinigung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Luftreinigungs-Score | 0.3 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde | `species.removes_compounds` |

**Hinweis:** Bromelien werden in der erweiterten Forschung als maessige Luftreiniger eingestuft. Guzmania lingulata war nicht direkt in der originalen NASA Clean Air Study (Wolverton 1989) enthalten, andere Bromeliaceae (Guzmania spp. allgemein) wurden jedoch spaeter untersucht. Die Filterwirkung ist aufgrund der relativ kleinen Blattflaeche begrenzt. Hauptmechanismus: Absorption von Formaldehyd ueber die Blattoberflaeche. Caveat: Bei realistischen Pflanzendichten in Wohnraeumen ist der Effekt vernachlaessigbar (Cummings & Waring 2020).

### 1.6 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

**Hinweis:** Kein Rueckschnitt moeglich oder noetig. Verblühten Bluetenstand kann man abschneiden, sobald er unansehnlich wird. Abgestorbene Blaetter der Mutterpflanze nach und nach entfernen. Die Mutterpflanze NICHT entfernen, solange sie Kindel versorgt -- sie gibt Naehrstoffe an die Ableger weiter.

### 1.7 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1--2 (kleiner Topf genuegt; Epiphyt mit minimalem Wurzelsystem) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 (flaches Wurzelsystem) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfaellt (reine Zimmerpflanze in Mitteleuropa) | `species.spacing_cm` |
| Indoor-Anbau | yes (ideale Zimmerpflanze fuer helle bis halbschattige Standorte) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Sommer, Halbschatten, kein Regen in den Trichter, kein Wind) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (optimale Luftfeuchtigkeit) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Sehr durchlaessiges Bromeliensubstrat: Orchideenrinde (50%), Torf/Kokos (30%), Perlite (20%). Alternativ epiphytisch auf Rinde oder Ast montiert (ohne Topf). | -- |

**Hinweis:** Guzmania lingulata ist ein Epiphyt, der in der Natur auf Aesten waechst. Das Wurzelsystem dient primaer der Verankerung, nicht der Naehrstoffaufnahme (Naehrstoffe werden ueber den Blatttrichter aufgenommen). Daher genuegt ein sehr kleiner, flacher Topf. Alternativ kann die Pflanze auf Rinde, Ast oder Moosstab montiert werden -- eine dekorative und artgerechte Kulturmethode. Staunaesse ist toedlich fuer Bromelien.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.8 Umgebungs-Physiologie & Standortqualitaet

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | 20 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 5--10 | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten (Substrat-ECe) fuer diese epiphytische Zierbromelie publiziert; qualitativ als "highly salt sensitive" belegt, aber kein numerischer ECe-Schwellenwert auffindbar. --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope publiziert. --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min--max) | 5.5--6.0 | `species.soil_ph_preference` |

**Hinweis (Lichtkompensationspunkt):** Der angegebene Bereich 10--20 umol/m2/s ist ein funktions-/standorttypischer Wert fuer stark schattentolerante tropische Verstandsarten (shade-tolerant understory), kein artspezifischer Einzelmesswert fuer Guzmania lingulata (publizierte Gattungs-Photosynthesemessungen liegen fuer G. monostachia vor, nicht als LCP fuer G. lingulata). Schattentolerante Verstandsarten zeigen LCP von 10--50 umol/m2/s; fuer die stark schattenangepasste Epiphyt-Rosette wurde die Untergrenze als Spanne verwendet. Saettigung und Photoinhibition (direkte Sonne >250 umol/m2/s verbrennt die Blaetter) sind separat in den Phasenprofilen (2.2) abgebildet und gehoeren NICHT in das Kompensationspunkt-Feld.

**Hinweis (Salz- & Staunaesse-Toleranz):** Guzmania zaehlt zu den salzempfindlichsten Bromelien (Trichome werden durch Salz-/Kalkablagerungen verstopft; Chlorid/Fluorid verursachen Blattspitzennekrosen). Bezugsgroesse der Salzempfindlichkeit ist die Substrat-/Trichterloesung, nicht eine pauschale Giesswasser-EC -- siehe auch Wasserqualitaet in 4.1. Als flachwurzelnder Epiphyt mit verankerndem (nicht saugendem) Wurzelsystem ist die Art extrem staunaesseempfindlich; Wurzel- und Trichterfaeule sind die haeufigsten Todesursachen (siehe 5.2). Der pH-Vorzug 5.5--6.0 ist quellentreu uebernommen und liegt innerhalb des in 2.3/3.2 genannten Substrat-pH-Korridors 5.0--6.0 (kein Widerspruch).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

Guzmania lingulata hat als monokarpe Bromelie einen einzigartigen Lebenszyklus: Nach der Bluete stirbt die Mutterpflanze, die Ableger (Kindel) setzen den Zyklus fort.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Kindel-Etablierung (Pup Establishment) | 30-60 | 1 | false | false | low |
| Vegetatives Wachstum (Vegetative Growth) | 365-730 (1-2 Jahre) | 2 | false | false | medium |
| Bluete (Flowering) | 60-120 | 3 | false | false | medium |
| Kindel-Bildung (Offset Production) | 90-180 | 4 | false | false | low |
| Seneszenz (Senescence, Mutterpflanze stirbt) | 90-365 | 5 | true | false | low |

**Anmerkung:** Der Zyklus ist linear und endet mit dem Absterben der Mutterpflanze (`is_terminal: true` bei Seneszenz). Die Kindel starten einen neuen Zyklus als eigenstaendige Pflanzen. Dies ist ein Sonderfall im KA-Phasenmodell: Keine jaehrlich wiederkehrende Phase, sondern ein einmaliger Lebenszyklus.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Kindel-Etablierung (Pup Establishment)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50-100 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3-5 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 22-27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60-80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60-75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5-0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (C) | 22-26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: kein artspezifischer FR/(R+FR)-Messwert fuer Guzmania lingulata publiziert. Naturhabitat ist Kronendach-/Verstandsschatten mit erhoehtem Far-Red-Anteil (FR/(R+FR) tendenziell >0.5), Kultur erfolgt jedoch unter indirektem Tageslicht/Kunstlicht (~0.5); kein belegter Einzelwert. --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | Trichter 1/4 voll halten, Substrat leicht feucht | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30-50 (Trichter) + 50-100 (Substrat) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetatives Wachstum (1-2 Jahre)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 75-200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 4-8 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 20-27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-21 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50-70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (C) | 22-27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: kein artspezifischer Messwert (siehe Hinweis Kindel-Etablierung). --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7-10 (Trichter alle 1-2 Wochen erneuern) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50-80 (Trichter) + 100-200 (Substrat) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (Flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100-250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 5-10 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 3.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 20-27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-21 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50-65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (C) | 22-27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: kein artspezifischer Messwert (siehe Hinweis Kindel-Etablierung). --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7-10 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50-80 (Trichter) + 100-200 (Substrat) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kindel-Bildung & Seneszenz

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 75-150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 4-8 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 20-26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50-65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (C) | 22-26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN: kein artspezifischer Messwert (siehe Hinweis Kindel-Etablierung). --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 10-14 (reduziert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50-100 (Substrat, Trichter trocknet aus) | `requirement_profiles.irrigation_volume_ml_per_plant` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (VPD-Sensitivitaet & -Schwelle):** Die VPD-Sensitivitaet wurde mit `medium` gesetzt -- bewusst NICHT mit der CAM-Faustregel `low`. Guzmania lingulata ist eine konstitutive **C3**-Bromelie (kein konstitutiver CAM-Typ); tank-epiphytische C3-Bromelien zeigen laut Males et al. 2017 (Plant, Cell & Environment) eine ausgepraegt schnelle, hohe stomataere Empfindlichkeit gegenueber dem Saettigungsdefizit (feedforward-Antwort der Transpiration auf VPD). Praxisnah im stabilen Innenraumklima wird `medium` angesetzt. Die VPD-Schwelle (`vpd_threshold_kpa`) liegt jeweils deutlich oberhalb des `vpd_target`-Korridors (kritischer Punkt des stomataeren Kollaps): in der feuchteliebenden Kindel-Etablierung niedriger (1.1 kPa), in den robusteren Folgephasen hoeher (1.5 kPa).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS/cm) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|-----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Kindel-Etablierung | 0:0:0 | 0.0 | 5.0-6.0 | -- | -- | -- | -- | -- | -- | -- | -- |
| Vegetatives Wachstum | 1:1:1 | 0.2-0.5 | 5.0-6.0 | 20 | 10 | -- | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Bluete | 1:2:1 | 0.2-0.5 | 5.0-6.0 | 20 | 15 | -- | 1 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Kindel-Bildung/Seneszenz | 0:0:0 | 0.0 | 5.0-6.0 | -- | -- | -- | -- | -- | -- | -- | -- |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronaehrstoffe Mn/Zn/Cu/Mo):** Fuer Guzmania lingulata sind keine artspezifischen Mangan-, Zink-, Kupfer- oder Molybdaen-Sollwerte (ppm) in serioeser Literatur publiziert; sie sind daher als DATEN FEHLEN markiert. Als extremer epiphytischer Schwachzehrer wird die Pflanze ohnehin nur mit stark verduenntem Voll-/Orchideenduenger (1/4-Dosis) versorgt, der Mikronaehrstoffe bereits ausgewogen enthaelt -- eine separate Mikronaehrstoff-Dosierung ist weder noetig noch belegt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis:** Bromelien sind extreme Schwachzehrer (epiphytisch -- natuerlich auf Naehrstoffarmut eingestellt). Duenger IMMER auf 1/4 der Herstellerangabe verduennen. Ueberdüngung fuehrt zu Wurzelfaeule und Verbrennungen. Duenger kann ins Giesswasser des Trichters oder als Blattduengung gegeben werden. Keine Duengung in den Trichter bei kuehlen Temperaturen (unter 18 C).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Kindel-Etablierung -> Vegetativ | conditional | 30-60 Tage | Eigene Wurzeln gebildet, 3+ Blaetter |
| Vegetativ -> Bluete | time_based / conditional | 365-730 Tage | Pflanze adult (12+ Blaetter), ausreichend Licht. Ethylen-Trick: reifer Apfel in Tuete mit Pflanze fuer 10 Tage kann Bluete ausloesen. |
| Bluete -> Kindel-Bildung | time_based | 60-120 Tage | Bluetenstand verblueht |
| Kindel-Bildung -> Seneszenz | time_based | 90-180 Tage | Kindel abgetrennt oder gross genug |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Zimmerpflanzen-Fluessigduenger)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideenduenger | COMPO | Fluessigduenger | 3-4-5 | 2 ml / 1 L Wasser (Viertel-Dosis!) | Vegetativ, Bluete |
| Orchideen-Nahrung | Substral | Fluessigduenger | 3-3-5 | 2 ml / 1 L Wasser (Viertel-Dosis!) | Vegetativ, Bluete |

**Warum Orchideenduenger?** Bromelien und Orchideen sind beides tropische Epiphyten mit sehr niedrigem Naehrstoffbedarf. Orchideenduenger hat bereits eine schwache Konzentration und ist ideal fuer Bromelien. Normale Zimmerpflanzenduenger sind zu stark konzentriert.

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Orchideenduenger | COMPO BIO | Bio-Fluessigduenger | 2 ml / 1 L | Maerz-September | Epiphyten |
| Wurmtee (verduennt) | diverse | organisch, fluessig | 1:10 verduennt als Blattduengung | Sommer | Alle Bromelien |

### 3.2 Duengungsplan (Beispiel-NutrientPlan)

| Zeitraum | Phase | EC (mS/cm) | pH | Orchideenduenger (ml/L) | Hinweise |
|----------|-------|---------|-----|-------------------------|----------|
| Maerz-April | Wachstumsbeginn | 0.1-0.2 | 5.0-6.0 | 1-2 (Viertel-Dosis) | Vorsichtig starten |
| Mai-August | Hauptwachstum | 0.2-0.5 | 5.0-6.0 | 2 (Viertel-Dosis) | Alle 3-4 Wochen, alternierend Trichter/Substrat |
| September | Wachstumsende | 0.1-0.2 | 5.0-6.0 | 1 | Letzte Duengung |
| Oktober-Februar | Ruheperiode | 0.0 | 5.0-6.0 | 0 | Keine Duengung |

### 3.3 Mischungsreihenfolge

Bei Bromelien-Duengung unkompliziert:

1. Frisches, weiches Wasser (Regenwasser oder abgestandenes Leitungswasser, Zimmertemperatur) vorbereiten
2. Orchideenduenger auf 1/4 Dosis einmischen
3. Wahlweise in den Trichter giessen ODER als Blattduengung aufspruehen
4. Trichter-Wasser alle 4-6 Wochen komplett austauschen (Bakterien- und Algenbildung vermeiden)

### 3.4 Besondere Hinweise zur Duengung

- **Extreme Schwachzehrer:** Bromelien sind Epiphyten, die in der Natur von Regenwasser, zersetzten Blaettern und Insektenresten in ihrem Trichter leben. Kuenstlicher Duenger ist nur eine Ergaenzung.
- **Trichter-Duengung:** Fluessigduenger kann direkt in den zentralen Trichter (Tank) gegeben werden. Konzentration: maximal 1/4 der Herstellerangabe.
- **Blattduengung:** Bromelien koennen Naehrstoffe ueber spezielle Saugschuppen (Trichome) auf den Blaettern aufnehmen. Leichte Blattspeuelung mit stark verduenntem Duenger ist effektiv.
- **Kein Duenger in der Bluete-Phase auf Bluetenstaende:** Duengerloesung nicht auf den Bluetenstand giessen -- kann Flecken verursachen.
- **Wasserqualitaet kritisch:** Trichter: ausschliesslich kalkfreies Wasser (Regenwasser, destilliert)! Kalkablagerungen verstopfen die Trichome und die Pflanze kann keine Naehrstoffe mehr aufnehmen. Substrat: kalkvertraeglicher als der Trichter, aber weiches Wasser bevorzugt.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkempfindlich! Ausschliesslich Regenwasser, destilliertes Wasser oder gut abgestandenes weiches Leitungswasser verwenden. Kalkiges Wasser verstopft die Trichome und toetet die Pflanze langfristig. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3, 4, 5, 6, 7, 8, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |
| Luftfeuchtigkeitspruefungs-Intervall (Tage) | 14 | `care_profiles.humidity_check_interval_days` |

**Giessanleitung:** Guzmania hat eine **Trichter-Giesskultur** -- eine Besonderheit gegenueber normalen Zimmerpflanzen:

1. **Zentraler Trichter (Tank):** Den Trichter ca. 1/4 mit Wasser fuellen. Alle 4-6 Wochen das Wasser im Trichter komplett austauschen (kippen und frisch befuellen), um Bakterien- und Algenbildung zu vermeiden.
2. **Substrat:** Nur leicht feucht halten. Staunaesse vermeiden -- die Wurzeln dienen primaer der Verankerung, nicht der Wasseraufnahme. Substrat zwischen den Wassergaben leicht antrocknen lassen.
3. **Kein Wasser in den Trichter bei kuehlen Temperaturen:** Unter 18 C fuehrt stehendes Wasser im Trichter zu Faeulnis.

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan-Feb | Pflegeminimum | Reduziert giessen, kein Duenger, Trichterwasser reduzieren. Luftfeuchte pruefen. | niedrig |
| Maerz | Wachstumsstart | Trichter wieder befuellen, Duengung starten (1/4 Dosis) | mittel |
| April-Mai | Wachstum | Regelmaessig giessen, Trichter sauber halten | mittel |
| Jun-Aug | Hauptwachstum | Duengung alle 4 Wochen, auf Schaedlinge pruefen | mittel |
| Sep | Blueteanregung | Bei adulten Pflanzen: Ethylen-Trick (Apfel in Tuete) kann Bluete ausloesen | niedrig |
| Okt | Wachstumsende | Duengung einstellen, Trichterwasser reduzieren | niedrig |
| Nov-Dez | Ruheperiode | Wenig giessen, Trichter nur minimal Wasser. Nicht unter 16 C. | niedrig |

**Zusaetzlich bei blühenden/absterbenden Pflanzen:**

| Phase | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Bluete | Geniessen | Bluetenstand haelt 2-4 Monate. Nicht mehr umtopfen oder umstellen. | niedrig |
| Nach Bluete | Kindel beobachten | Kindel wachsen an der Basis. Mutterpflanze weiter giessen, auch wenn sie vergilbt. | mittel |
| Kindel gross genug | Kindel abtrennen | Bei 1/3-1/2 Groesse der Mutterpflanze mit eigenen Wurzeln abtrennen und einzeln topfen. | hoch |

### 4.3 Ueberwinterung

Entfaellt als Freilandueberwinterung -- reine Zimmerpflanze, ganzjaehrig Indoor. Im Winter Giessen stark reduzieren und Trichter-Wasser auf Minimum halten. Keine Duengung. Mindesttemperatur 15 C.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Einstufung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme + Monat | move_indoors -- spaetestens September/Oktober (wenn Naechte unter 13-15 C); ganzjaehrig drinnen bei reiner Zimmerkultur | `overwintering_profiles.winter_action` |
| Fruehjahrs-Massnahme + Monat | move_outdoors -- ab Mitte/Ende Mai (nach den Eisheiligen, nur halbschattig, regen-/windgeschuetzt) bei optionaler Sommerkultur auf Balkon/Terrasse | `overwintering_profiles.spring_action` |
| Winterquartier Temperatur (C) | min. 15 (nie unter 13); optimal 18-22 | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (Ost-/Westfenster); kein direktes Wintersonnenlicht noetig | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Giessen | stark reduziert; Trichter nur minimal/leer halten (Faeulnisschutz bei kuehleren Temperaturen), Substrat nur leicht feucht | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Die Einstufung `frost_free` (nicht `dig_and_store`, `needs_protection` oder `hardy`) gilt, weil Guzmania lingulata eine frostempfindliche tropische Kuebel-/Zimmerpflanze ist, die frostfrei im warmen Innenraum ueberwintert und keine Knollen zum Ausgraben/Einlagern bildet. Eine Sommerkultur im Freien ist nur als Option (limited, vgl. 1.7) vorgesehen; in Mitteleuropa (USDA 6-8) ist ganzjaehrige Zimmerkultur der Normalfall, dann entfaellt der Quartierwechsel.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 4.4 Standort-Empfehlungen

- **Optimal:** Helles indirektes Licht, Ost- oder Westfenster. Keine direkte Mittagssonne -- die Blaetter verbrennen schnell.
- **Akzeptabel:** Halbschattig, Nordfenster, Badezimmer mit Fenster (hohe Luftfeuchtigkeit)
- **Vermeiden:** Direkte Sonneneinstrahlung (Blattverbrennungen), Zugluft, kalte Fensterbank, Standort neben Heizkoerper
- **Substrat:** Extrem durchlaessig! Orchideensubstrat, Rindenmulch, oder Mischung aus Kokosfaser und Perlite. Normale Blumenerde ist zu dicht und fuehrt zu Wurzelfaeule.
- **Luftfeuchtigkeit:** 50-70% optimal. Bromelien lieben hohe Luftfeuchtigkeit. Im Winter: Luftbefeuchter oder regelmaessig besprühen.
- **Besonderheit:** Kann auch rein epiphytisch auf Rinde oder Holz aufgebunden kultiviert werden (ohne Topf).

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schildlaeusse (Scale) | Coccoidea | Braune Hoecker an Blattunterseiten und -raendern, Honigtau | leaf | Alle | medium |
| Wolllaeusse (Mealybug) | Pseudococcidae | Weisse wachsartige Klumpen in Blattachseln und Trichter | leaf, stem | Alle | easy |
| Blattlaeusse (Aphids) | Aphididae | Kolonie an jungen Blaettern, Honigtau, kraeuselende Blaetter | leaf | Vegetativ | easy |
| Trauermuecken (Fungus Gnat) | Bradysia spp. | Kleine schwarze Fliegen, Larven im Substrat | root | Alle (bei zu feuchtem Substrat) | easy |

**Anmerkung:** Bromelien sind vergleichsweise schaedlingsresistent. Der haeufigste Befall sind Schildlaeusse, die sich gerne in den Blattachseln und am Trichterrand verstecken.

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kern-/Trichterfaeule (Heart Rot) | fungal / bacterial | Trichter riecht faulig, innere Blaetter lassen sich leicht herausziehen, braune matschige Basis | stagnant_water_in_tank, cold_temperatures | 7-14 | Alle (besonders Winter) |
| Wurzelfaeule (Root Rot) | fungal (Pythium) | Welke, braune matschige Wurzeln | overwatering, poor_drainage, dense_substrate | 14-28 | Alle |
| Blattfleckenkrankheit (Leaf Spot) | fungal (Helminthosporium) | Braune Flecken mit gelbem Hof auf Blaettern | high_humidity, poor_airflow, wet_leaves | 7-14 | Vegetativ |

**Kritisch: Trichterfaeule** ist die haeufigste Todesursache bei Guzmania. Ursache: Stehendes Wasser im Trichter bei kuehlen Temperaturen (unter 18 C). Praevention: Im Winter den Trichter trocken oder nur minimal gefuellt halten.

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wolllaeusse | 2-5 | 14-21 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeusse, Wolllaeusse | 5-10 | 14 |
| Steinernema feltiae (Nematoden) | Trauermuecken-Larven | Giessbehandlung | 7-14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schmierseife | biological | Kaliumsalze von Fettsaeuren | Spruehen, 1% Loesung, NICHT in den Trichter | 0 | Blattlaeusse, Wolllaeusse, Schildlaeusse |
| Alkohol-Abwischen | mechanical | Isopropanol 70% | Wattestab auf befallene Stellen | 0 | Schildlaeusse, Wolllaeusse |
| Trichterwasser erneuern | cultural | -- | Stehendes Wasser austauschen, Trichter reinigen | 0 | Trichterfaeule (Praevention) |
| Substrat abtrocknen lassen | cultural | -- | Giessintervall verlaengern | 0 | Trauermuecken, Wurzelfaeule |

**Vorsicht mit Neemoel:** Neemoel kann bei Bromelien die empfindlichen Trichome (Saugschuppen) verstopfen. Nur in sehr niedriger Konzentration (0.1%) und nur auf Blaetter, NICHT in den Trichter anwenden.

### 5.5 Resistenzen der Art

Bromelien sind insgesamt robust gegenueber Schaedlingen -- die wachsartigen Blaetter und die Rosetten-Struktur bieten natuerlichen Schutz. Die haeufigsten Probleme sind Kulturfehler (Staunaesse, kaltes Trichterwasser), nicht Schaedlinge.

---

## 6. Fruchtfolge & Mischkultur

Entfaellt (reine Zimmerpflanze). Fruchtfolge und Mischkultur sind Konzepte des Freilandanbaus und haben fuer Guzmania als Zimmerpflanze keine Relevanz.

### 6.1 Standort-Nachbarn (Indoor-Empfehlungen)

| Partner | Wissenschaftl. Name | Begruendung |
|---------|-------------------|-------------|
| Orchidee (Phalaenopsis) | Phalaenopsis amabilis | Beide Epiphyten, aehnliche Ansprueche an Licht und Luftfeuchtigkeit |
| Tillandsie (Luftpflanze) | Tillandsia spp. | Gleiche Familie (Bromeliaceae), dekorativ als Gruppe |
| Nestfarn | Asplenium nidus | Aehnliche Luftfeuchtigkeitsansprueche, schoener Kontrast |
| Einblatt | Spathiphyllum wallisii | Aehnliche Licht- und Feuchtigkeitsansprueche |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Guzmania lingulata |
|-----|-------------------|-------------|--------------------------------------|
| Vriesea (Flammendes Schwert) | Vriesea splendens | Gleiche Familie, aehnliche Rosetten-Form, dekorative Bluetenstaende | Groessere Blattmuster, laengere Bluetenstanddauer |
| Aechmea (Lanzenrosette) | Aechmea fasciata | Gleiche Familie, robuster | Widerstandsfaehiger, toleriert mehr Trockenheit |
| Tillandsie | Tillandsia ionantha | Gleiche Familie, epiphytisch | Braucht kein Substrat, minimaler Pflegeaufwand |
| Neoregelia | Neoregelia carolinae | Gleiche Familie, auffaellige Blattfaerbung | Laengere Lebensdauer als Einzelpflanze, farbiges Laub statt Bluetenstand |
| Billbergia | Billbergia nutans | Gleiche Familie, aehnliche Kultur | Robuster, bildet schneller Kindel, blueht leichter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,air_purification_score
Guzmania lingulata,Bromelie;Guzmanie;Scarlet Star,Bromeliaceae,Guzmania,perennial,day_neutral,herb,fibrous,10a;10b;11a;11b;12a;12b,0.0,Tropische Regenwaelder Mittel- und Suedamerikas,sensitive,light_feeder,false,ornamental,0.3
```

### 8.2 BotanicalFamily CSV-Zeile (falls noch nicht vorhanden)

```csv
name,common_name_de,common_name_en,order,typical_nutrient_demand,nitrogen_fixing,typical_root_depth,frost_tolerance,pollination_type
Bromeliaceae,Bromeliengewaechse,Bromeliad family,Poales,light,false,SHALLOW,SENSITIVE,INSECT
```

### 8.3 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type
Luna,Guzmania lingulata,--,--,compact;red_bract,clone
Amaretto,Guzmania lingulata,--,--,compact;red_bract,clone
Tempo,Guzmania lingulata,--,--,yellow_bract,clone
Rana,Guzmania lingulata,--,--,orange_bract;compact,clone
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Guzmania lingulata: https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants (Bromeliad = non-toxic)
2. Bromeliads.info -- Getting to Know the Guzmania Bromeliad: https://www.bromeliads.info/guzmania-bromeliad/
3. UKHouseplants -- Guzmania & Bromelia: https://www.ukhouseplants.com/plants/bromelia-guzmania
4. PlantCareToday -- Guzmania Plant Care: https://plantcaretoday.com/guzmania-plant.html
5. Thursd.com -- Guzmania Bromeliad Care Guide: https://thursd.com/articles/guzmania-is-a-tropical-beauty
6. JoyUsGarden -- Guzmania Bromeliad Plant Care: https://www.joyusgarden.com/guzmania-bromeliad-plant-care-tips/
7. Clemson University Extension -- Bromeliads: https://hgic.clemson.edu/factsheet/bromeliads/
8. Cummings & Waring (2020) -- Potted plants do not improve indoor air quality (Journal of Exposure Science & Environmental Epidemiology)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
9. Maxwell, Griffiths et al. / Photosynthetica (2013) 51(1):55-62 -- "Juvenile tank-bromeliads lacking tanks: do they engage in CAM photosynthesis?" (G. lingulata, G. monostachia konstitutiv C3; fakultativ CAM unter Trockenstress): https://ps.ueb.cas.cz/pdfs/phs/2013/01/07.pdf
10. Crayn, Winter & Smith / Botanical Journal of the Linnean Society (2015) 178:169-221 -- "Photosynthetic pathways in Bromeliaceae ... CAM and C3 based on carbon isotope ratios for 1893 species" (in Tillandsioideae ist C3 vorherrschend, CAM auf Tillandsia beschraenkt): https://academic.oup.com/botlinnean/article-abstract/178/2/169/2416361
11. Pereira, Mercier et al. / Frontiers in Plant Science (2021) 12:715289 -- "Transcriptomic and Biochemical Analysis ... Guzmania monostachia (Bromeliaceae) Under Drought" (C3-zu-CAM-Umschaltung unter Trockenheit): https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.715289/full
12. Males & Griffiths / Plant, Cell & Environment (2017) 40:1428-1442 -- "Specialized stomatal humidity responses underpin ecological diversity in C3 bromeliads" (tank-epiphytische C3-Bromelien: hohe, schnelle stomataere VPD-Empfindlichkeit): https://pubmed.ncbi.nlm.nih.gov/28722113/
13. Missouri Botanical Garden -- Plant Finder, Guzmania lingulata (Exposition "Part shade to full shade", Wasserbedarf "Dry to medium", exzellente Drainage, USDA 10-12): https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=278139
14. North Carolina Extension Gardener Plant Toolbox -- Guzmania lingulata (Standort, Pflege, USDA-Zonen): https://plants.ces.ncsu.edu/plants/guzmania-lingulata/
15. Sterck et al. / Journal of Ecology (2013) 101:971-980 -- "Plasticity influencing the light compensation point ... in a tropical forest understorey" (schattentolerante Verstandsarten: LCP 10-50 umol/m2/s, Untergrenze fuer stark schattentolerante Arten): https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076
16. bromeliads.info -- Bromeliad Potting Soil / Guzmania-Growing-Specifications (Bromelien bevorzugen leicht sauren Boden pH 5-6; Guzmania 5.5-6.0; hohe Salz-/Kalkempfindlichkeit): https://www.bromeliads.info/bromeliad-potting-soil/ ; https://www.bromeliads.info/bromeliad-plant-growing-specifications-guzmania-lingulata-and-hybrids/
17. flowersgeek.com -- "How to Water Bromeliads" (Guzmania hochgradig salzempfindlich; Chlorid/Fluorid -> Trichom-Schaeden, Spitzennekrosen): https://flowersgeek.com/how-to-water-bromeliads-for-bold-color-and-long-lasting-blooms/
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
