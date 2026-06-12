# Zichorie / Wegwarte -- Cichorium intybus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** naturadb.de, kiepenkerl.de, sperli.de, samen.de, lubera.com, kraeuter-buch.de, plantura.garden, Wikipedia, Yara UK, CropNerd, ISHS, avogel.ch, Springer (Acta Physiologiae Plantarum, Plant Growth Regulation), ScienceDirect

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cichorium intybus | `species.scientific_name` |
| Volksnamen (DE/EN) | Wegwarte; Zichorie; Gemeine Wegwarte; Chicory; Coffeeweed; Blue Daisy | `species.common_names` |
| Familie | Asteraceae | `species.family` -> `botanical_families.name` |
| Gattung | Cichorium | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 (Asteraceae-Blattkultur ohne C4-/CAM-Anatomie; eng verwandt mit Salat, der gesichert C3 ist) | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial (Wildform mehrjaehrig; Kulturformen wie Chicoree/Radicchio oft als biennial oder annual kultiviert) | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebensdauer (Jahre, perennial) | 3--7 (Wildform am Standort haeufig laenger; Kultur-/Futterzichorie produktiv 3--7 Jahre) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true (oberirdische Teile sterben im Herbst ab, Wurzel ueberwintert, Neuaustrieb im Fruehjahr) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true (obligater Kaeltereiz fuer Bluetenbildung) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 42 (ca. 6 Wochen bei 4--5 degC wirksam; sortenabhaengig 3--16 Wochen bei 0--12 degC) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (h) | 14--16 (Langtag-Schwellbereich: bei 12 h nur vegetatives Wachstum, ab 16 h obligate Bluetenstandbildung nach Vernalisation; kritischer Uebergang liegt zwischen 12 und 16 h, 16 h voll induktiv -- in-vitro-Photoperiodestudie an Wurzelexplantaten) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | long_day (Langtagspflanze -- Bluetenbildung durch Langtag ab dem zweiten Jahr nach Vernalisation ausgeloest) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, degC) | 3.5 (Keim-Basistemperatur nach Acta Physiol. Plant. 2019; eine separate Wuchs-/GDD-Basistemperatur ist fuer Cichorium intybus nicht eigenstaendig publiziert. Der Wert liegt im fuer kuehlliebende Arten plausiblen Bereich (~4--5 degC) und wird hilfsweise als Wuchsbasis verwendet) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Gut winterhart bis ca. -20 degC. Die tiefe Pfahlwurzel uebersteht strenge Winter problemlos. Oberirdische Teile sterben im Herbst ab und treiben im Fruehjahr aus der Wurzel neu aus. Kulturformen (Chicoree, Radicchio) sind weniger frosthart als die Wildform. | `species.hardiness_detail` |
| Heimat | Europa, Westasien, Nordafrika (Wildform; weltweit eingebuergert) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; medicinal | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4--6 (Direktsaat bevorzugt wegen Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat ab Mai moeglich, Pflanze ist frosthart) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10; 11 (Blaetter ab Juli; Wurzeln ab Oktober) | `species.harvest_months` |
| Bluetemonate | 6; 7; 8; 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Zichorie wird fast ausschliesslich ueber Samen vermehrt. Die Pflanze bildet eine kraeftige Pfahlwurzel und vertraegt Verpflanzung schlecht -- daher Direktsaat stark bevorzugt. Bei Vorkultur spaetestens 4 Wochen nach Aussaat auspflanzen, bevor die Pfahlwurzel sich verkruemmt.

**Keimhinweise:**
- Optimale Keimtemperatur: 18--20 degC
- Minimale Keimtemperatur: 10 degC
- Keimdauer: 10--21 Tage
- **Dunkelkeimer** -- Samen 1--2 cm mit Erde bedecken
- Substrat gleichmaessig feucht halten
- Saattiefe: 1--2 cm
- Reihenabstand: 30--40 cm, Pflanzabstand in der Reihe: 25--30 cm

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine; alle Pflanzenteile sind essbar) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (keine; Intybin verursacht den bitteren Geschmack, ist aber nicht toxisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (selten; Kontaktdermatitis bei empfindlichen Personen durch Sesquiterpenlactone moeglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: Die Wegwarte ist eine traditionelle Heil- und Nutzpflanze. Alle Teile sind essbar: junge Blaetter als Salat, Blueten als Dekoration, Wurzeln geroestet als Kaffee-Ersatz (Muckefuck). Medizinisch eingesetzt bei Verdauungsbeschwerden (Bitterstoff Intybin regt Gallenfluss an). Keine Toxizitaet fuer Haustiere bekannt. Vorsicht: bei empfindlichen Personen koennen Sesquiterpenlactone (Asteraceae-typisch) Kontaktallergien ausloesen.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7; 8; 9 | `species.pruning_months` |

Hinweis: Regelmaessiges Ernten der aeusseren Blaetter foerdert Nachwuchs. Fuer Blatternte Bluetenstaende entfernen; fuer Wurzelnutzung (Chicoree-Treiberei, Kaffee-Ersatz) Bluete im ersten Jahr komplett unterdruecken, damit die Kraft in die Wurzel geht. Wildform: nach der Bluete zurueckschneiden fuer zweite Blattrosette.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Pfahlwurzel benoetigt tiefe Gefaesse; Blatternte im Topf moeglich, Wurzelbildung eingeschraenkt) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--120 (mit Bluetenstaenden bis 150) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25--30 | `species.spacing_cm` |
| Indoor-Anbau | limited (nur Chicoree-Treiberei im Dunkeln moeglich; Blattpflanze braucht viel Licht) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (tiefe Gefaesse noetig, Wildform wird sehr hoch) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false (Wildform kann hoch werden, steht aber selbstaendig) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgruendige, humusreiche, durchlaessige Erde. Lehmig-sandiger Boden ideal. pH 5.5--7.0. Keine Staunaesse. | -- |

**Hinweis:** Die Wegwarte ist eine aeusserst genuegsame Wildpflanze und gedeiht sogar auf Schotterwegen und Wegrandern. Im Garten bevorzugt sie sonnige Standorte mit tiefgruendigem Boden fuer die Pfahlwurzelentwicklung. Als Kulturzichorie (Radicchio, Zuckerhut, Chicoree) gelten hoehere Ansprueche an Boden und Wasser.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualitaet

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | 15 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | 35 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (vertraegt keinen Schatten; PFAF "no shade") | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 60--120 (aktive Hauptwasser-/Naehrstoffzone; einzelne Pfahlwurzeln erreichen >2 m) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz (waterlogging tolerance) | sensitive (trockenheitsadaptierte Pfahlwurzel, fault bei Staunaesse) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (analog Salat/Blattgemuese) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 1.3 (Substrat-ECe, Maas-Hoffman a; Salat-Referenzwert fuer Blattgemuese, keine chicory-spezifische Messung) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 13 (Maas-Hoffman b; Salat-Referenzwert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min--max) | 5.5--7.0 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) liegt fuer diese sonnenliebende C3-Blattkultur im typischen Bereich von Sonnenpflanzen-Blaettern (ca. 15--35 umol/m2/s). Lichtsaettigung tritt erst deutlich hoeher ein (mehrere hundert umol/m2/s) -- diese Saettigungswerte gehoeren nicht in das Kompensationspunkt-Feld. Die Salztoleranz ist quellentreu von der eng verwandten Blattkultur Salat (Lactuca sativa) abgeleitet, da fuer Cichorium intybus keine eigenstaendigen Maas-Hoffman-Parameter publiziert sind; Bezugsgroesse ist die elektrische Leitfaehigkeit des Saettigungsextrakts des Substrats (ECe), NICHT die Giesswasser-EC. Der pH-Vorzug 5.5--7.0 ist mit den Angaben in Sektion 1.6 und 2.3 dieser Datei harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 10--21 | 1 | false | false | low |
| Saemling (seedling) | 21--35 | 2 | false | false | low |
| Vegetativ (vegetative) | 60--90 (Blattrosetten-Aufbau, Wurzelwachstum) | 3 | false | true | high |
| Dormanz (dormancy) | 90--120 (1. Winter; Vernalisation) | 4 | false | false | high |
| Bluete (flowering) | 60--90 (2. Jahr, Juni--September) | 5 | false | true | medium |
| Seneszenz (senescence) | 14--28 | 6 | true | false | low |

Hinweis: Als Kulturzichorie (einjaerig/zweijaehrig) entfaellt je nach Kulturart die Dormanz. Fuer Chicoree-Treiberei: Wurzeln im 1. Jahr aufbauen (vegetativ), im Herbst roden, dann dunkel bei 15--18 degC treiben (Etiolierung). Die Wildform ist mehrjaehrig und kehrt nach Seneszenz zur Dormanz zurueck.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | -- (Dunkelkeimer, Licht erst nach Keimung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 (optimal 20) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 (kritischer Punkt stomataeren Kollaps, deutlich ueber dem feuchteliebenden Keim-Korridor) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (mesophytische C3-Blattkultur) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Vollspektrum) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (Substrat gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (deutlich oberhalb des Saemlings-Zielkorridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--40 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (volle Sonne bevorzugt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 14--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (maessig giessen, Trockenheit wird gut toleriert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Zichorie ist sehr trockenheitsresistent dank der tiefen Pfahlwurzel. Uebermaessiges Giessen foerdert Faeulnis. Die Pflanze bevorzugt kuehle Temperaturen fuer die Blattqualitaet; bei Hitze ueber 25 degC koennen die Blaetter sehr bitter werden.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 14--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16+ (Langtagspflanze -- Bluete durch lange Tage nach Vernalisation) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ca. 0.4 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 20--25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Die himmelblauen Blueten oeffnen sich nur morgens und schliessen sich gegen Mittag. Attraktiv fuer Bienen und andere Bestauber. Saatgutreife ca. 4--6 Wochen nach Bluete.

#### Phase: Dormanz (dormancy)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (kurze Wintertage) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -- (natuerlich; winterhart bis -20 degC) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -- | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | -- (natuerlicher Niederschlag genuegt) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | -- | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Die Vernalisation (Kaeltereiz ueber mindestens 4--6 Wochen bei unter 5 degC) ist Voraussetzung fuer die Bluetenbildung im zweiten Jahr. Fuer reine Blatternte oder Chicoree-Treiberei im 1. Jahr ernten, bevor die Pflanze in Bluete geht.

### 2.3 Naehrstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 (Spalten Mn/Zn/Cu/Mo ergaenzt) -->
| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 6.0--6.5 | 60 | 30 | 20 | 2 | 0.25 | 0.1 | 0.03 | 0.02 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 6.0--7.0 | 120 | 40 | 30 | 3 | 0.5 | 0.13 | 0.05 | 0.03 |
| Bluete | 2-2-3 | 1.2--1.6 | 6.0--7.0 | 100 | 40 | 30 | 2 | 0.4 | 0.1 | 0.05 | 0.03 |
| Dormanz | 0-0-0 | 0.0 | -- | -- | -- | -- | -- | -- | -- | -- | -- |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

Mikronaehrstoff-Zielwerte (Mn/Zn/Cu/Mo) orientieren sich an etablierten Hydro-Naehrloesungsrezepturen fuer Blattgemuese (modifizierte Sonneveld-Loesung; typische Spannen Mn 0.25--0.5; Zn 0.05--0.13; Cu 0.02--0.1; Mo 0.02--0.05 ppm). Mn/Zn/Fe als Chelat zufuehren, da bei pH-Schwankungen schnell fixiert. <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

Hinweis: Zichorie ist ein Mittelzehrer. Uebermaessige Stickstoffduengung foerdert Blattwachstum auf Kosten der Wurzelentwicklung und erhoet den Nitratgehalt in den Blaettern. Kalium foerdert die Wurzelentwicklung (wichtig fuer Chicoree-Treiberei und Kaffee-Ersatz-Produktion).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 10--21 Tage | Keimblaetter voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 21--35 Tage | 4--6 echte Blaetter, Blattrosette erkennbar |
| Vegetativ -> Dormanz | time_based / event_based | Oktober/November (1. Jahr) | Blaetter welken, Pfahlwurzel hat volle Groesse erreicht |
| Dormanz -> Bluete | event_based | Fruehling (2. Jahr, nach Vernalisation) | Neuaustrieb mit Bluetenstaengelbildung |
| Bluete -> Seneszenz | time_based | 60--90 Tage nach Bluetebeginn | Samenkapseln reif, Pflanze verholzt |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10 | 5 | Bluete |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 3--4 L/m2 | Fruehjahr (Einarbeitung) | alle |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 40--60 g/m2 | Fruehjahr (Einarbeitung) | medium_feeder |
| Bio Universaldunger (fluessig) | COMPO BIO | organisch | 20--30 ml / 10 L Giesswasser | Mai--August, alle 3--4 Wochen | medium_feeder |
| Kalimagnesia (Patentkali) | div. | mineralisch-organisch | 30--40 g/m2 | Fruehjahr | medium_feeder (K-Versorgung fuer Wurzelentwicklung) |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 0.5 L/m2 | Mai--Juli, alle 3 Wochen | medium_feeder |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Zichorie Standard Hydro")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--3 | Saemling | 0.3--0.5 | 6.0 | 0.2 | 0.3 | 0.3 | Nur Wasser erste 7 Tage |
| 4--6 | Saemling/Veg | 0.6--1.0 | 6.0--6.5 | 0.3 | 0.5 | 0.5 | EC langsam steigern |
| 7--14 | Vegetativ | 1.4--2.0 | 6.0--6.5 | 0.3 | 0.8 | 0.8 | Hauptwachstum |
| 15--20 | Vegetativ (Spat) | 1.2--1.6 | 6.0--6.5 | 0.3 | 0.7 | 0.7 | N reduzieren fuer Wurzelaufbau |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Vega A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Mittelzehrer:** Zichorie steht in der Fruchtfolge ideal nach Starkzehrern (Kohl, Kartoffel) und profitiert von den Naehrstoff-Restbestaenden im Boden.
- **Stickstoff massvoll dosieren:** Zu viel N erhoet den Nitratgehalt in den Blaettern und foerdert Blattmasse auf Kosten der Wurzelentwicklung.
- **Kalium foerdern:** Fuer Wurzelzichorie (Chicoree, Kaffee-Ersatz) Kaliumduengung betonen -- K staerkt die Wurzelentwicklung und Einlagerung.
- **Bor-Empfindlichkeit:** Zichorie reagiert empfindlich auf Bor-Mangel (Herzfaeule, hohle Wurzeln). Bei Bedarf Bor-Blattduengung (Borax 0.1% Loesung).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 3--5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (Dormanz, kein Giessen im Freiland) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Anspruchslos. Normale Leitungswasserqualitaet genuegt. Kalkvertraeglich. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 21--28 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4; 5; 6; 7; 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (Freiland: mehrjaehrig am Standort; Topf: jaehrlich ernten) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | -- | Dormanz, keine Aktivitaet | -- |
| Feb | -- | Dormanz | -- |
| Marz | Bodenvorbereitung | Boden lockern, Kompost einarbeiten (3--4 L/m2) | hoch |
| Apr | Vorkultur (optional) | Bei Vorkultur: Aussaat in tiefe Toepfe bei 18--20 degC | mittel |
| Mai | Direktsaat | Samen 1--2 cm tief in Reihen (30--40 cm Abstand), ausdunnen auf 25--30 cm | hoch |
| Jun | Jungpflanzenpflege | Unkraut jaeten, bei Trockenheit giessen, Mulchen | mittel |
| Jul | Erste Blatternte | Aeussere Blaetter ernten, junge Herzblatter stehen lassen | hoch |
| Aug | Ernte + Schaedlingskontrolle | Blatternte fortsetzen, auf Blattlaeuse kontrollieren | mittel |
| Sep | Letzte Blatternte | Blaetter ernten; Wildform: Blueten fuer Saatgut ausreifen lassen | mittel |
| Okt | Wurzelernte (Chicoree) | Wurzeln roden fuer Chicoree-Treiberei oder Kaffee-Ersatz; Wildform: am Standort belassen | hoch |
| Nov | Chicoree-Treiberei starten | Gerodete Wurzeln in Sand/Erde bei 15--18 degC im Dunkeln treiben | mittel |
| Dez | Chicoree-Ernte | Chicoreezapfen nach ca. 3--4 Wochen Treiberei ernten | mittel |

### 4.3 Ueberwinterung

Die Gemeine Wegwarte ist winterhart bis ca. -20 degC und benoetigt keine besondere Ueberwinterungspflege im Freiland. Die oberirdischen Teile sterben im Herbst ab; die Pfahlwurzel uebersteht den Winter im Boden. Leichte Laubmulchschicht schuetzt vor extremen Kahlfroesten. Topfkultur: Topf an geschuetzten Ort stellen, Topf mit Vlies einwickeln oder eingraben.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Bewertung (hardiness rating) | hardy (winterhart bis ca. -20 degC, ueberwintert im Freiland) | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme (winter action) + Monat | mulch (leichte Laubmulchschicht gegen Kahlfrost); November | `overwintering_profiles.winter_action` |
| Fruehjahrs-Massnahme (spring action) + Monat | uncover (Mulch abraeumen, damit Neuaustrieb durchkommt); Maerz | `overwintering_profiles.spring_action` |
| Winterquartier Temperatur (degC) | -- (Freiland-Ueberwinterung; vertraegt Bodenfrost) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | -- (Freiland; im Winter oberirdisch eingezogen) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Giessen | none (natuerlicher Niederschlag genuegt; Staunaesse vermeiden) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Frostempfindlichere Kulturformen (Chicoree, Radicchio) werden in rauen Lagen mit Vlies (fleece) zusaetzlich geschuetzt; zur Chicoree-Treiberei werden die Wurzeln ohnehin im Herbst gerodet und frostfrei eingelagert (siehe Sektion 4.2, November). Fuer die Wildform ist `hardy` mit `mulch`/`uncover` die korrekte Einordnung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Zichorien-Blattlaus | Aphis cichorii | Gekraeuselte Blaetter, Honigtau, Wuchshemmung | leaf, stem | vegetative | easy |
| Schnecken (Slugs/Snails) | Arion spp., Deroceras spp. | Lochfrass an Blaettern, Schleimspuren, bevorzugt junge Pflanzen | leaf | seedling, vegetative | easy |
| Drahtwurm (Wireworm) | Agriotes spp. | Frassgaenge in der Wurzel, Kueumerwuchs | root | vegetative | hard |
| Minierfliege | Liriomyza spp. | Weisse Miniergaenge in Blaettern | leaf | vegetative | medium |
| Erdraupe (Cutworm) | Agrotis spp. | Abgefressene Saemlinge auf Bodenniveau | stem | seedling | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau (Powdery Mildew) | fungal | Weisser, mehliger Belag auf Blattoberseite | warm_dry_conditions, poor_airflow | 5--10 | vegetative |
| Falscher Mehltau (Downy Mildew) | oomycete (Bremia lactucae) | Gelbe Flecken auf Blattoberseite, grau-violetter Sporenrasen auf Blattunterseite | high_humidity, cool_nights | 5--10 | vegetative |
| Sklerotinia-Faeule (White Mold) | fungal | Weisser, watteartiger Belag an Stengelbasis, Pflanze welkt | cool_wet_conditions | 7--14 | vegetative |
| Bakterielle Weichfaeule | bacterial | Matschige, uebel riechende Stellen an Wurzel und Stengelbasis | overwatering, warm_wet_conditions | 3--7 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Coccinella septempunctata (Siebenpunkt-Marienkaefer) | Blattlaeuse | 5--10 | 7--14 |
| Schneckenkorn (Ferramol) | Schnecken | 5 g/m2 | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage, 3x wiederholen | 0 | Blattlaeuse |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Minierfliegen |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen und im Restmuell entsorgen | 0 | Mehltau, Sklerotinia |
| Weiter Pflanzabstand | cultural | -- | 25--30 cm Abstand fuer gute Luftzirkulation | 0 | Pilzkrankheiten allgemein |

### 5.5 Resistenzen der Art

Die Gemeine Wegwarte ist als Wildpflanze grundsaetzlich robust und wenig anfaellig. Kulturformen (Radicchio, Chicoree) sind empfindlicher als die Wildform.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Trockenheit | Stressfaktor | Arteigen (tiefe Pfahlwurzel) | -- |
| Wildverbiss | Schaedlinge | Arteigen (Bitterstoffe Intybin/Lactucopikrin schrecken Wildtiere ab) | -- |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Korbblueuter (Asteraceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kohl, Kartoffel) oder Huelsenfruechte |
| Empfohlene Nachfrucht | Schwachzehrer (Radieschen, Feldsalat) oder Gruenduengung |
| Anbaupause (Jahre) | 3--4 Jahre fuer Asteraceae auf gleicher Flaeche (inkl. Endivie, Chicoree, Radicchio, Sonnenblume) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Bohne (Buschbohne) | Phaseolus vulgaris | 0.8 | N-Fixierung bereichert Boden, unterschiedliche Wurzeltiefen | `compatible_with` |
| Erbse | Pisum sativum | 0.8 | N-Fixierung, gute Platzausnutzung | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Unterschiedliche Naehrstoffbeduerfnisse, gute Raumnutzung | `compatible_with` |
| Moehre | Daucus carota | 0.7 | Ergaenzende Wurzeltiefen, gute Bodenaufschliessung | `compatible_with` |
| Fenchel | Foeniculum vulgare | 0.7 | Aehnliche Standortansprueche, ergaenzende Ernte | `compatible_with` |
| Kopfsalat | Lactuca sativa | 0.6 | Schnelle Ernte als Zwischenkultur, Bodenbeschattung; ausreichend Abstand halten (gleiche Tribus Cichorieae) | `compatible_with` |
| Thymian | Thymus vulgaris | 0.7 | Schaedlingsabwehr durch aetherische Oele | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Endivie | Cichorium endivia | Gleiche Gattung, geteilte Schaedlinge/Krankheiten, Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Sonnenblume | Helianthus annuus | Starke Naehrstoffkonkurrenz, Beschattung | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Asteraceae (mit sich selbst) | `shares_pest_risk` | Sklerotinia, Blattlaeuse (Aphis cichorii), Mehltau | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Zichorie |
|-----|-------------------|-------------|------------------------------|
| Radicchio | Cichorium intybus var. foliosum | Gleiche Art, rote Blaetter, milder | Dekorativer, vielseitiger in Salaten |
| Chicoree (Witloof) | Cichorium intybus var. foliosum (Treibzichorie) | Gleiche Art, Etiolierung | Milder Geschmack durch Treiberei im Dunkeln |
| Zuckerhut | Cichorium intybus var. foliosum | Gleiche Art, aufrechte Koepfe | Weniger bitter, laengere Lagerfaehigkeit |
| Endivie (Escarole) | Cichorium endivia | Gleiche Gattung | Breitere Blaetter, milder, salattauglich |
| Loewenzahn (Kultur) | Taraxacum officinale | Gleiche Familie, aehnliche Verwendung | Einfacher Anbau, aehnliche Bitterstoffe |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,direct_sow_months,harvest_months,bloom_months,sowing_indoor_weeks_before_last_frost
Cichorium intybus,Wegwarte;Zichorie;Gemeine Wegwarte;Chicory;Coffeeweed,Asteraceae,Cichorium,perennial,long_day,herb,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a,0.1,"Europa, Westasien, Nordafrika",hardy,medium_feeder,false,edible;medicinal,5;6,7;8;9;10;11,6;7;8;9,4
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Catalogna (Blattzichorie),Cichorium intybus,,,large_leaf;italian_type,60,,open_pollinated
Zuckerhut,Cichorium intybus,,,compact;mild_flavor;long_storage,90,,open_pollinated
Rossa di Treviso,Cichorium intybus,,,red_leaf;italian_type;ornamental,85,,open_pollinated
Palla Rossa,Cichorium intybus,,,red_leaf;compact;ball_shape,80,,open_pollinated
Witloof (Brüsseler),Cichorium intybus,,,forcing_type;etiolated_culture,120,,open_pollinated
Wegwarte (Pötschke Historisch),Cichorium intybus,Pötschke,,heirloom;wild_type;medicinal,90,,open_pollinated
```

---

## Quellenverzeichnis

1. naturadb.de -- Wegwarte (Cichorium intybus): https://www.naturadb.de/pflanzen/cichorium-intybus/
2. kiepenkerl.de -- Zichorien Kulturanleitung: https://www.kiepenkerl.de/kulturanleitungen/zichorien/
3. sperli.de -- Zichorien Anbauexperte: https://www.sperli.de/anbauexperte/kulturanleitung-zichorien/
4. samen.de -- Zichorie und Chicoree: https://samen.de/blog/zichorie-und-chicoree-verwandte-im-gemuesebeet.html
5. samen.de -- Anbauanleitung fuer Zichorie: https://samen.de/blog/anbauanleitung-fuer-zichorie-von-der-aussaat-bis-zur-ernte.html
6. lubera.com -- Gewoehnliche Wegwarte: https://www.lubera.com/de/gartenbuch/gewoehnliche-wegwarte-p3424
7. kraeuter-buch.de -- Wegwarte: https://www.kraeuter-buch.de/kraeuter/Wegwarte.html
8. plantura.garden -- Wegwarte: https://www.plantura.garden/blumen-stauden/wegwarte/wegwarte-pflanzenportrait
9. Wikipedia -- Gemeine Wegwarte: https://de.wikipedia.org/wiki/Gemeine_Wegwarte
10. Yara UK -- Chicory Nutrient Requirements: https://www.yara.co.uk/crop-nutrition/novel-crops/chicory/
11. CropNerd -- Chicory Growing Guide: https://cropnerd.com/plants/vegetables/chicory
12. ISHS -- Cultivation of Chicory in Hydroponics: https://www.ishs.org/ishs-article/361_21
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
13. Acta Physiologiae Plantarum (Springer, 2019) -- Environmental factors' effect on seed germination and seedling growth of chicory (Cichorium intybus L.): Basistemperatur der Keimung 3.5 degC, Optimum 28.9 degC: https://link.springer.com/article/10.1007/s11738-019-2820-2
14. Plant Growth Regulation (Springer) -- Stem elongation and floral initiation on in vitro chicory root explants: influence of photoperiod: kritische Tageslaenge -- 12 h nur vegetativ, ab 16 h Bluetenstandbildung: https://link.springer.com/article/10.1007/BF00024778
15. ScienceDirect -- Impact of vernalization and heat on flowering induction, development and fertility in root chicory (Cichorium intybus L. var. sativum): obligate Vernalisation + Langtag-Requirement, ~6 Wochen bei 4 degC wirksam: https://www.sciencedirect.com/science/article/abs/pii/S0176161720301620
16. FAO -- Agricultural Drainage Water Management in Arid and Semi-Arid Areas (Maas-Hoffman Salztoleranz-Parameter, Salat/Blattgemuese ECe 1.3 dS/m): https://www.fao.org/4/y4263e/y4263e0e.htm
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
