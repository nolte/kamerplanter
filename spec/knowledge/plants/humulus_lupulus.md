# Hopfen -- Humulus lupulus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** MSU Extension (canr.msu.edu), Gardening Know How, PFAF Plant Database, Plantura, Hausgarten.net, MDPI Agriculture, Gardenia.net, University of Florida EDIS

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Humulus lupulus | `species.scientific_name` |
| Volksnamen (DE/EN) | Hopfen; Echter Hopfen; Hop; Common Hop; European Hop | `species.common_names` |
| Familie | Cannabaceae | `species.family` -> `botanical_families.name` |
| Gattung | Humulus | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day (Doldenbildung wird durch abnehmende Taglaenge ausgeloest — Kurztagspflanze) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Winterhart bis -35 degC (Zone 3). Oberirdische Triebe sterben nach erstem Frost ab. Rhizom ueberwintert sicher im Boden bis Zone 3. In Zone 8 kann Sommerruhe bei Hitze auftreten. | `species.hardiness_detail` |
| Heimat | Europa, Westasien, Nordamerika | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic; medicinal; beer_brewing | `species.traits` |

**Besonderheit:** Humulus lupulus ist eine zweihaeusige Pflanze (dioecieus). Nur weibliche Pflanzen bilden die aromatischen Hopfendolden (Cones) mit den Lupulindrüsen (Bitterstoff Humulon, Aromastoffe Myrcen, Linalool). Fuer die Bierproduktion und Ernte werden ausschliesslich weibliche Pflanzen kultiviert. Pflanzen aus Rhizomen sind immer weiblich.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte April bis Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | -- (Aussaat aus Samen selten; Rhizome ab Maerz pflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (Rhizom-Pflanzung nach letztem starken Frost, ca. April) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | -- (keine Direktsaat; Rhizom-Pflanzung: 3, 4) | `species.direct_sow_months` |
| Erntemonate | 8; 9 (sortenabhaengig; Fruehsorten ab Mitte August, Spaetsorten bis September) | `species.harvest_months` |
| Bluetemonate | 6; 7 (weibliche Bluetenstände; Doldenbildung Juli--August) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem; division (Rhizomteilung im Fruehjahr, bevorzugte Methode) | `species.propagation_methods` |
| Schwierigkeit | easy (Rhizomteilung im Maerz/April sehr erfolgreich) | `species.propagation_difficulty` |

**Vermehrungshinweise:**
- **Rhizomteilung:** Im Fruehjahr (Maerz/April) Rhizome ausgraben und in 10--15 cm lange Stuecke teilen. Jedes Stueck muss mindestens 1--2 Knospen (Augen) aufweisen. 3--5 cm tief einpflanzen, horizontal oder leicht schraeg.
- **Stecklinge:** Gruene Triebstecklinge (10--15 cm) im Fruehjahr, in Anzuchtsubstrat mit Hormonpulver bewurzeln (2--3 Wochen).
- **Aussaat:** Aus Samen moeglich, aber zeitaufwaendig, Sortenreinheit nicht garantiert, und Geschlecht erst nach Bluete bestimmbar. Daher in der Praxis kaum verwendet.
- Rhizome von namhaften Vermehrungsbetrieben beziehen (garantiert weiblich, Sortentreue).

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (Hopfendolden stark giftig fuer Hunde und Katzen: Malignes Hyperthermie-Syndrom moeglich!) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (Hohe Gefahr: Hyperthermie, Krampfanfaelle, Tod moeglich -- ASPCA-gelistet) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (geringe Toxizitaet fuer Menschen; Hopfen wird in Lebensmitteln/Bier verwendet) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | cone; leaf (fuer Tiere) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Humulon; Lupulon; 2-Methyl-3-butenol (fuer Hunde/Katzen toxisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe (fuer Tiere -- insbesondere Hunde: sofortige tieraerztliche Behandlung noetig) | `species.toxicity.severity` |
| Kontaktallergen | true (Hopfenpollen und Lupulin koennen Kontaktdermatitis und Atemwegsbeschwerden ausloesen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Hopfenpollen als Luftpollen relevant; Kreuzreaktion mit Hanf-Pollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 3; 4 (Auslichten der Triebe im Fruehjahr; nur 3--5 kraeftigste Triebe je Rhizom aufleiten) | `species.pruning_months` |

**Rueckschnitthinweise:**
- Im Fruehjahr alle Triebe bis auf 3--5 kraeftigste entfernen (Selektion foerdert starke Doldenbildung)
- Im Herbst nach Ernte alle oberirdischen Triebe bodennah abschneiden oder stehen lassen bis Frost sie abtoetest
- Jedes Jahr neue Triebe aus dem Rhizom -- kein Stammschnitt noetig
- Erster Rueckschnitt: Wenn Triebe 30--40 cm hoch sind, schwache Triebe entfernen, starke aufleiten

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in sehr grossen Kuebeln 40+ L, aber extreme Wuchshoehe von 4--7 m erfordert stabile Rank-Konstruktion) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40--80 (Mindestanforderung fuer mehrjaehrigen Topfanbau) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 (Rhizome brauchen Tiefe) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 400--700 (4--7 m pro Saison; sehr aggressiver Kletterer) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100--200 (Ranktriebe breiten sich aus wenn keine Kletterstuetze vorhanden) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 100--150 (kommerziell 90--120 cm in der Reihe, 3 m zwischen Reihen) | `species.spacing_cm` |
| Indoor-Anbau | no (Wuchshoehe und Lichtbedarf nicht indoor erreichbar) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Suedbalkon mit stabiler Rank-Konstruktion, Kuebel mind. 50 L, sehr pflegeintensiv) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (braucht Kaltperiode fuer Dormanz; Freiland bevorzugt) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (kritisch! Rankt sich im Uhrzeigersinn; braucht Draehte oder Stangen ab 4--6 m Hoehe) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlaessige, naehrstoffreiche Garten-/Beeterdegemisch mit Kompost-Anteil (30%). pH 6.0--8.0 toleriert, optimal 6.5--7.5. Guter Wasserabzug wichtig -- keine Staunaesse. | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

Hopfen ist eine Staude mit jaehrlichem Neuaustrieb aus dem Rhizom. Die Phasen wiederholen sich jedes Jahr. Im 1. Standjahr geringere Ertraege, volle Ernte ab 2.--3. Standjahr.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Dormanz (dormancy) | 90--150 (Winter, Nov--Feb/Maerz) | 1 | false | false | high |
| Austrieb (bud_break) | 14--28 (Maerz--April) | 2 | false | false | medium |
| Vegetativ (vegetative) | 60--90 (April--Juni) | 3 | false | false | medium |
| Doldenbildung (cone_formation) | 30--50 (Juli--August) | 4 | false | false | medium |
| Reife/Ernte (harvest) | 14--21 (August--September) | 5 | true | true | medium |
| Abreife/Seneszenz (senescence) | 21--42 (September--Oktober) | 6 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Dormanz (dormancy)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | -- (keine Anforderungen; Rhizom unter Erde) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | -- | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -10 bis 5 (Kaeltereiz notwendig fuer Dormanzunterbrechung) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -15 bis 0 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- (Freilandbedingungen) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | -- | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 0 (kein Giessen; Winterregen genuegt) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Austrieb (bud_break)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (Freiland im Fruehjahr; 2--4 h direktes Sonnenlicht genuegt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 (zunehmende Taglaenge als Austriebssignal) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 8--15 (Austrieb beginnt ab ca. 5 degC Bodentemperatur) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 2--8 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--70 (Freilandbedingungen) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Aussenluft) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7--14 (sparsam, je nach Niederschlag) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--800 (Vollsonne; min. 6--8 h direkte Sonne taeglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 25--40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (lange Tage foerdern vegetatives Wachstum) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--26 (optimal 20--24) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--7 (je nach Niederschlag und Temperatur) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 2000--5000 (grosse Pflanzen mit grossem Blattvolumen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Hinweis:** Hopfen waechst in der Vegetationsphase sehr schnell -- bis 30 cm/Tag unter optimalen Bedingungen. Regelmaessiges Aufleiten der Ranktriebe ist noetig.

#### Phase: Doldenbildung (cone_formation)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--800 (Vollsonne weiterhin wichtig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 (abnehmende Taglaenge nach Sommersonnenwende loest Doldenbildung aus) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--24 (kuehlere Temperaturen foerdern Qualitaet und Aromastoffe) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 (Temperaturdifferenz Tag/Nacht foerdert Aromastoffe) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--60 (trockener als Vegetativphase; Feuchtigkeit foerdert Mehltau!) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 4--10 (gleichmaessige Feuchte, kein Trockenstress) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 2000--4000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Reife/Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 18--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--13 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7--14 (Wasser reduzieren foerdert Harzbildung und Aromadichte) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 1000--3000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Ernte-Indikatoren:**
- Dolden fuehlen sich papierartig und trocken an (nicht mehr saftig/weich)
- Lupulin (gelbes Harspulver) gut sichtbar beim Oeffnen der Dolde
- Dolden leicht begruenung noch erhalten (nicht braun oder duenkel)
- Charakteristischer Hopfenduft intensiv (sortentypisch)
- Stiele zwischen Dolde und Rispe beginnen zu trocknen

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Dormanz | 0-0-0 | 0.0 | 6.5--7.5 | -- | -- | -- | -- |
| Austrieb | 2-1-1 | 0.8--1.2 | 6.0--7.0 | 80 | 30 | -- | 2 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 6.0--7.0 | 150 | 50 | 30 | 3 |
| Doldenbildung | 1-2-3 | 1.4--2.0 | 6.0--7.0 | 120 | 50 | 30 | 2 |
| Ernte | 0-1-2 | 0.8--1.4 | 6.0--7.0 | 80 | 40 | -- | 1 |

**Stickstoffbedarf:** Im kommerziellen Anbau werden 120--150 kg N/ha empfohlen, aufgeteilt auf mindestens 3 Gaben zwischen April und Anfang Juli (MSU Extension). Zu viel N foerdert Blattwachstum auf Kosten der Dolden.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Dormanz -> Austrieb | time_based / gdd_based | GDD-Basistemp 5 degC; GDD ~50--100 | Bodentemperatur > 5 degC, Tageslaenge > 10 h |
| Austrieb -> Vegetativ | time_based | 14--28 Tage nach Austrieb | Erste Blaetter entfaltet, Triebe aufleiten |
| Vegetativ -> Doldenbildung | event_based | Sommersonnenwende (21. Juni) +/- 2 Wochen | Abnehmende Taglaenge loest Bluete aus |
| Doldenbildung -> Ernte | manual / conditional | 30--50 Tage nach Bluetebeginn | Dolden-Trockentest, Lupulin-Check |
| Ernte -> Seneszenz | time_based | 14--28 Tage nach Erntebeginn | Ernte abgeschlossen, Laubfaerbung einsetzt |
| Seneszenz -> Dormanz | event_based | Erster Frost | Triebe absterben, Rueckschnitt |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Topf/Freiland intensiv)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Hakaphos Blau | Compo Expert | base | 15-10-15+3MgO | nach Packung | 2 | Austrieb, Vegetativ |
| Nitrophoska Speed | Compo | base | 12-8-16+3MgO | nach Packung | 2 | Vegetativ |
| Blaukorn | Compo / Hauert | base | 12-8-16 | Granulat, 40 g/m2 | 1 (einarbeiten) | Fruehjahr |
| Kalisulfat | div. | supplement | 0-0-50+S | 30--40 g/m2 | 1 (einarbeiten) | Doldenbildung |

#### Organisch (Freiland bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (Maerz/April um Rhizom) | heavy_feeder |
| Hornspäne (grob) | Oscorna / Hauert | organisch (N-Langzeit) | 100--150 g/m2 | Maerz/April | heavy_feeder (N-Grundversorgung) |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 3--5 L/m2 | Mai--Juli alle 14 Tage | vegetative Phase |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 2--3 L/m2 | Juli--August | Doldenbildung (Kalium fuer Aroma) |
| Algenkalk / Dolomitkalk | Oscorna | pH-Puffer + Ca/Mg | 200--300 g/m2 | Herbst oder Fruehjahr | bei pH < 6.0 |

### 3.2 Duengungsplan (Freiland, etablierte Pflanze ab 2. Standjahr)

| Monat | Phase | Massnahme | Menge | Hinweise |
|-------|-------|-----------|-------|----------|
| Maerz | Austrieb | Kompost einarbeiten | 5--8 L/m2 | Um Rhizom herum aufbringen |
| April | Austrieb | Hornspäne | 100--150 g/m2 | Einharken, dann giessen |
| April/Mai | Vegetativ | 1. Mineraldunger | 30--40 g/m2 Blaukorn | N-betont fuer Triebwachstum |
| Juni | Vegetativ | 2. Duengung | Brennnesseljauche 1:10 | Fliessig, grosszuegig |
| Anfang Juli | Vegetativ/Dold. | 3. Duengung | 30 g/m2 Blaukorn reduziert | Letzte N-Gabe vor Doldenbildung |
| Juli--Aug | Doldenbildung | Kaliduengung | Beinwelljauche 1:10 | K foerdert Lupulin und Aroma |
| Ab August | Keine Duengung | -- | -- | Keine N-Duengung mehr! |

### 3.3 Mischungsreihenfolge (Fluessigduengung)

1. Wasser temperieren (18--22 degC)
2. Eventuell Algenkalk/Dolomitkalk aufloesen (separate Anwendung auf Boden)
3. Hauptduenger (Basis, N-P-K)
4. Spurenelemente / CalMag (falls separate Gabe)
5. pH-Kontrolle (Freiland: pH 6.0--7.5 toleriert; optimal 6.5--7.0)

### 3.4 Besondere Hinweise zur Duengung

- **Stickstoff-Timing ist entscheidend:** Keine N-Duengung nach Anfang Juli! Zu viel N in der Doldenbildungsphase = weniger Dolden, mehr Blattmasse, anfaelliger fuer Krankheiten.
- **Kalium foerdert Qualitaet:** Kalibetonter Duenger ab Doldenbildung (Juli) verbessert Lupulingehalt, Alphasaeuregehalt und Aromaintensitaet.
- **1. Standjahr:** Nur halbe Duengermengen -- Rhizome zuerst etablieren lassen. Erster Ertrag gering.
- **pH-Puffer:** Hopfen vertraegt pH 6.0--8.0, aber pH unter 6.0 foerdert Aluminium-Toxizitaet. Kalk bei Bedarf einarbeiten.
- **Mikronährstoffe:** Bor, Zink und Mangan beachten -- Maengel zeigen sich als Internodien-Veraenderungen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 4--7 (je nach Niederschlag; Freiland meist durch Regen ausreichend) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0 (kein Giessen im Winter; Dormanz) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Leitungswasser geeignet. pH 6.0--8.0 toleriert. Niederschlagswasser bevorzugt. Staunaesse vermeiden -- Wurzelfaeule. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 (organische Fluessigduengung alle 2 Wochen April--Juli) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 6; 7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36--48 (Freilandpflanze; Topfpflanze alle 2--3 Jahre umtopfen, Rhizome zurueckschneiden) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 (insbesondere auf Blattlaeuse, Spinnmilben und Falschen Mehltau achten) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false (Freilandpflanze; Luftfeuchtigkeit nur relevant fuer Mehltau-Monitoring) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | Winterruhe | Keine Massnahmen; Rhizom ueberwintert im Boden | niedrig |
| Feb | Planung | Sorten recherchieren, Rank-Konstruktion vorbereiten | niedrig |
| Maerz | Fruehjahrsduengung | Kompost und Hornspäne einarbeiten; erste Triebe sichtbar | hoch |
| Apr | Austrieb aufleiten | Kraeftigste 3--5 Triebe aufleiten, Rest entfernen; 1. Mineralduengung | hoch |
| Mai | Aufleiten + Pflege | Triebe wachsen bis 30 cm/Tag; taeglich kontrolliern und aufleiten | hoch |
| Jun | Pflege + 2. Duengung | Letzte N-Gabe Anfang Juli; Mehltau und Blattlaeuse pruefen | hoch |
| Jul | Doldenbildung | Kaliduengung; Dolden sichtbar; keine N-Duengung mehr | hoch |
| Aug | Ernte | Doldenreife pruefen; bei Reife sofort ernten; Ernte haengt von Sorte ab | hoch |
| Sep | Nachernte | Spaetsorten ernten; Triebe nach Ernte zurueckschneiden oder stehen lassen | mittel |
| Okt | Rueckschnitt | Alle Triebe bodennah entfernen; Rhizombereich mulchen | mittel |
| Nov | Wintervorbereitung | Mulchschicht (Laub/Stroh) ueber Rhizom, besonders in Zone < 5 | niedrig |
| Dez | Winterruhe | Keine Massnahmen | niedrig |

### 4.3 Ueberwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Fruehjahrs-Massnahme | uncover | `overwintering_profiles.spring_action` |
| Fruehjahrs-Massnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (degC) | -- (Freiland; kein Winterquartier noetig) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (degC) | -- | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | -- (Freiland) | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Hopfenblattlaus | Phorodon humuli | Gekraeuselte Blaetter, Honigtau, Wachstumshemmung, Dolden kontaminiert | leaf; cone | vegetative; cone_formation | easy |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, stippenartige Blattvergilbung, Trockenheits-Symptome | leaf | vegetative; cone_formation | medium |
| Blattlaeuse (gemischt) | Myzus persicae | Honigtau, Virusuebertraeger, Knospenbefall | leaf; shoot | bud_break; vegetative | easy |
| Zwiebelfliege / Hopfenerdfloh | Psylliodes attenuata | Lochfrass an jungen Blaettern und Trieben | leaf; shoot | bud_break; vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | oomycete (Pseudoperonospora humuli) | Gelbliche Flecken Blattobereseite; grau-violetter Rasen Blattunterseite; Dolden braun und trocken | high_humidity; poor_airflow; rainy_cool | 3--7 | vegetative; cone_formation |
| Echter Mehltau | fungal (Podosphaera macularis) | Weisser mehliger Belag auf Blaettern und Dolden | dry_warm; poor_airflow | 5--10 | cone_formation; harvest |
| Verticillium-Welke | fungal (Verticillium albo-atrum) | Einseitige Blattwelke; Staengel-Bräunung; Wilt | contaminated_soil; wet_cold | 14--28 | vegetative; cone_formation |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmelbelag auf Dolden; Dolden faulen | high_humidity; cool; senescence | 3--7 | harvest |
| Hopfenvirosen (diverse) | viral | Mosaik-Muster; Ringflecken; Wuchshemmung | aphid_vectors | -- | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Aphidoletes aphidimyza | Hopfenblattlaus | 5--10 Muecken/m2 | 14--21 |
| Chrysoperla carnea (Florfliege) | Blattlaeuse; Spinnmilben | 5--10 Larven/m2 | 7--14 |
| Phytoseiulus persimilis | Spinnmilbe | 10--20/m2 | 10--14 |
| Marienkaefer (Coccinella) | Blattlaeuse | Spontanansiedelung durch Begleitpflanzen | -- |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoelextrakt | biological | Azadirachtin | Spruehanwendung 0.3--0.5%, abends | 3 | Blattlaeuse; Spinnmilben |
| Schwefel-Praeparat (Netzschwefel) | chemical | Schwefel | Spruehen; Stauben | 14 | Echter Mehltau |
| Kupferkalkbruehe (Bordeaux) | biological/approved | Kupfer(II)sulfat | 0.5% Spruehanwendung | 7 | Falscher Mehltau |
| Kaliseife (Insektizidseife) | biological | Kaliumsalze der Fettseuren | 2% Spruehanwendung | 3 | Blattlaeuse; Spinnmilben |
| Knoblauchsud | cultural | Schwefelverbindungen | 1:10 verduennt, spruehen | 0 | Blattlaeuse; Mehltau-Praevention |
| Schnittmassnahmen | cultural | -- | Dichte Triebe auslichten | 0 | Mehltau-Praevention (Luftzirkulation) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Verticillium (sortenabhaengig) | Krankheit | `resistant_to` |
| Echter Mehltau (Sorte Hallertauer Tradition) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Stauden / Dauerkulturen |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae); Gruenduengung (Phacelia, Lupine) |
| Empfohlene Nachfrucht | -- (Dauerpflanze; kein Standortwechsel vorgesehen; Pause nach Rodung: 3--4 Jahre fuer Cannabaceae) |
| Anbaupause (Jahre) | 4--5 Jahre (fuer Familienmitglieder Cannabaceae nach Rodung) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Schnittlauch | Allium schoenoprasum | 0.8 | Blattlaus-Abwehr; Schutz der Dolden vor Aphiden | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Spinnmilben- und Blattlaus-Abwehr durch Aromastoffe | `compatible_with` |
| Schafgarbe | Achillea millefolium | 0.8 | Foerdert Marienkaefer und Nuetzlingswespen; kompostierbar als Duengungs-Tee | `compatible_with` |
| Mais (Zucker-/Popcorn-) | Zea mays | 0.6 | Aehnliche Kulturanforderungen; stabil genug fuer Rankverhalten; Windschutz | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr; Bestaeuberforderung | `compatible_with` |
| Phacelia | Phacelia tanacetifolia | 0.8 | Gruenduengung in Baumschatten; Nuetzlinge anlocken | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung vieler Pflanzen durch Fenchel-Exsudate | moderate | `incompatible_with` |
| Andere Klettergewaechse | div. | Hopfenranken verdraengen und erdrossen konkurrierenden Kletterpflanzen | severe | `incompatible_with` |
| Cannabis | Cannabis sativa | Gemeinsame Schaderreger (Spinnmilben, Mehltau); gleiche Familie | moderate | `incompatible_with` |
| Ziergehoelze (kleinwuechsig) | div. | Hopfenranken wuergen kleinere Gehoelze | severe | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Cannabaceae | `shares_pest_risk` | Spinnmilben; Mehltau; Blattlaeuse; Verticillium | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Hopfen |
|-----|-------------------|-------------|--------------------------|
| Japanischer Hopfen | Humulus japonicus | Dekorativer Kletterer; gleiche Familie | Schneller wachsend; nur fuer Zierde; keine Ernte; einjährig |
| Wilder Wein | Parthenocissus tricuspidata | Kletterpflanze fuer Fassaden | Keine Ernte; rein ornamental; pflegeleichter |
| Hopfenbuche | Ostrya carpinifolia | Hopfenaehnliche Fruechte (optisch) | Baum; keine Verwendung als Bier-Hopfen |

---

## 8. Sorten / Cultivars

### Brau-Hopfensorten (Auswahl fuer Hausgarten Deutschland)

| Sorte | Typ | Verwendung | Alphasaeure (%) | Reifezeit | Eigenschaften |
|-------|-----|-----------|----------------|-----------|---------------|
| Hallertauer Mittelfrüh | Aromasorte | Bier (Bittere + Aroma) | 3--5 | Mittelfrüh (Mitte Aug.) | Klassische Bairische Sorte; feines Hopfenaroma; Mehltau-empfindlich |
| Hallertauer Tradition | Aromasorte | Bier (Aroma) | 4--7 | Mittelfrüh | Mehltau-toleranter als Mittelfrüh; guter Ertrag |
| Cascade | Aromasorte (US) | Craft-Bier; Hopfentee | 4--7 | Mittelfrüh-Spaet | Ausgepraegtes Zitrus-/Grapefruit-Aroma; gut fuer Hausgarten; robust |
| Centennial | Aromasorte (US) | Craft-Bier (IPA) | 9--11 | Mittelfrüh | Intensiv florale Note; hoher Alphasaeuregehalt |
| Nugget | Bitterhopfen | Bier (Bittere) | 12--14 | Frueh | Sehr ertragreiche; robuste Sorte; wenig Aroma |
| Hersbrucker Spät | Aromasorte | Bier (mildes Aroma) | 2--5 | Spaet (September) | Angenehm mild; kuehleretoleranter |
| Tettnanger | Aromasorte | Pilsner; Weizenbier | 3--5 | Frühzeitig | Fein-wuerziges Aroma; anspruchsvoll; empfindlich |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,pruning_type,pruning_months
Humulus lupulus,Hopfen;Echter Hopfen;Hop;Common Hop,Cannabaceae,Humulus,perennial,long_day,vine,rhizomatous,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b,-0.1,Europa; Westasien; Nordamerika,limited,40,50,400,150,120,no,limited,false,true,heavy_feeder,false,hardy,spring_pruning,3;4
```

### 9.2 Cultivar CSV-Zeilen

```csv
name,parent_species,breeder,traits,days_to_maturity,disease_resistances,seed_type,notes
Hallertauer Mittelfrüh,Humulus lupulus,Bayerische Landesanstalt,aromatic;traditional_german,85,low_mildew_resistance,vegetative,Klassische bayerische Aromasorte
Hallertauer Tradition,Humulus lupulus,HVG Hallertau,aromatic;mildew_tolerant,85,powdery_mildew,vegetative,Nachfolger Mittelfrueher; robuster
Cascade,Humulus lupulus,USDA,aromatic;citrus_aroma,90,moderate_resistance,vegetative,US-Craft-Bier Sorte; Zitrusnoten; sehr beliebt
Nugget,Humulus lupulus,USDA,bittering;high_alpha,75,good_resistance,vegetative,Bitterhopfen; hoher Ertrag; robust
Centennial,Humulus lupulus,S. T. Carpenter,aromatic;high_alpha,90,moderate_resistance,vegetative,Intensive florale Note; IPA-Sorte
```

---

## Quellenverzeichnis

1. [MSU Extension -- Michigan Fresh: Growing Hops](https://www.canr.msu.edu/resources/michigan_fresh_growing_hops) -- Naehrstoffbedarf, NPK-Mengen, Kulturkalender
2. [Gardening Know How -- Fertilizing Hops](https://www.gardeningknowhow.com/edible/vegetables/hops/hops-plant-fertilizer.htm) -- Duengungshinweise
3. [Gardening Know How -- Companion Plants for Hops](https://www.gardeningknowhow.com/edible/vegetables/hops/hops-companion-plants.htm) -- Mischkultur
4. [Gardening Know How -- Propagating Hops](https://www.gardeningknowhow.com/edible/vegetables/hops/propagating-hops-plants.htm) -- Rhizom-Vermehrung
5. [PFAF Plant Database -- Humulus lupulus](https://pfaf.org/user/plant.aspx?latinname=Humulus+lupulus) -- Botanische Stammdaten, Toxizitaet
6. [Gardenia.net -- Humulus lupulus](https://www.gardenia.net/plant/humulus-lupulus) -- USDA-Zonen, Grunddaten
7. [MDPI Agriculture -- Hops as Multipurpose Crop](https://www.mdpi.com/2077-0472/11/6/484) -- Wachstumsphasen, Ertragsoptimierung
8. [University of Florida EDIS -- Hops](https://edis.ifas.ufl.edu/publication/EP488) -- Anbaugrundlagen
9. [Plantura -- Hopfenpflanzenportrait](https://www.plantura.garden/kraeuter/hopfen/hopfen-pflanzenportrait) -- Deutschsprachige Praxisinformationen
