# Rote Bete -- Beta vulgaris subsp. vulgaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** Hortipendium, Wikipedia, Bio-Gaertner, fryd.app, samen.de, gartenratgeber.net, grove.eco, hortica.de, pflanzenkrankheiten.ch, Koraylights, ResearchGate, eat.de

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Beta vulgaris subsp. vulgaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Rote Bete; Rote Ruebe; Rote Beete; Rahne; Beetroot; Red Beet; Table Beet | `species.common_names` |
| Familie | Amaranthaceae (frueher Chenopodiaceae) | `species.family` -> `botanical_families.name` |
| Gattung | Beta | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot (Ruebe = verdickte Pfahlwurzel + Hypokotyl) | `species.root_type` |
| Lebenszyklus | biennial (wird als Einjaehrige kultiviert; Bluete im 2. Jahr nach Vernalisation) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- lange Tage und Kaelteexposition koennen im 1. Jahr Schossen ausloesen; Bluete erst nach Vernalisation im 2. Jahr) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | moderate | `species.frost_sensitivity` |
| Winterhaerte-Detail | Keimlinge vertragen leichte Froeste bis -3 degC. Ausgewachsene Pflanzen tolerieren Froeste bis -6 degC. Rueben koennen mit Stroh-/Laub-Abdeckung bis in den Winter im Boden bleiben. Bei laengerem Frost (unter -10 degC) Rueben ernten und kuhl lagern (Erdmiete, Keller). | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Westasien (abgeleitet von Beta vulgaris subsp. maritima -- Wilde Ruebe) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium (Mittelzehrer) | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4--6 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat ab Mitte April moeglich, wenn Bodentemperatur > 8 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4; 5; 6; 7 | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10; 11 | `species.harvest_months` |
| Bluetemonate | 6; 7 (nur bei Schossern oder 2. Jahr) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 10--20 degC (optimal 15)
- Minimale Keimtemperatur: 8 degC
- Keimdauer: 10--14 Tage
- **Dunkelkeimer** -- Samen 2--3 cm tief saeen
- Rote-Bete-"Samen" sind eigentlich Knauelfruchte (2--4 Samen pro Knauel) -- nach dem Aufgehen auf 1 Pflanze pro Stelle vereinzeln!
- Saatgut vor Aussaat 12--24 Stunden in lauwarmem Wasser einweichen (beschleunigt Keimung)
- Monogerm-Sorten (Einzelkorn) ersparen das Vereinzeln

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false (aber oxalsaeurehaltig -- in grossen Mengen problematisch) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false (aber oxalsaeurehaltig -- in grossen Mengen Magen-Darm-Reizung) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (Vorsicht bei Saeuglingen: hoher Nitratgehalt kann Methaemoglobinaemie ausloesen) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (grundsaetzlich ungiftig, aber Oxalsaeure in Blaettern; Nitrat in Rueben) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Oxalsaeure (180 mg/100 g in der Ruebe; hoeher in Blaettern); Nitrat (300--3000 mg/kg je nach Duengung) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (bei normaler Ernaehrung unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | false (roter Saft kann Haut und Kleidung faerben, ist aber kein Allergen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Hinweis: Rote Bete ist fuer Erwachsene und aeltere Kinder unbedenklich. Personen mit Neigung zu Nierensteinen (Calciumoxalat) sollten den Konsum einschraenken. Fuer Saeuglinge unter 6 Monaten wegen des Nitratgehalts nicht geeignet. Kochen reduziert den Oxalsaeuregehalt (geht ins Kochwasser ueber). Hunde und Katzen koennen kleine Mengen gekochte Rote Bete fressen; in grossen Mengen kann die Oxalsaeure den Magen-Darm-Trakt reizen.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | -- (kein Rueckschnitt; einzelne aeussere Blaetter koennen als "Blattgemuese" geerntet werden ohne die Ruebe zu schaedigen) | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Die Blaetter sind essbar und naehrstoffreich (wie Mangold -- gleiche Art!). Maximal 2--3 aeussere Blaetter pro Pflanze ernten, damit die Ruebe weiter gut waechst. Bluetenstaende bei Schossern sofort entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (in tiefen Toepfen/Kuebeln gut moeglich) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5--10 (fuer 3--5 Pflanzen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 (Ruebe braucht Tiefe!) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--40 (Blattrosette) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15--25 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10--15 (in der Reihe), Reihenabstand 25--30 cm | `species.spacing_cm` |
| Indoor-Anbau | limited (moeglich unter starker Beleuchtung, aber Freiland bevorzugt) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (in tiefen Kuebeln oder Balkonkaesten gut moeglich) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freiland genuegt, Gewaechshaus nur fuer Voranzucht) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgruendige, humose, lockere Erde. Keine Steine (deformierte Rueben). pH 6.0--7.5. Mittlerer Naehrstoffgehalt. Staunaesse vermeiden. | -- |

**Hinweis:** Rote Bete ist eine dankbare Anfaengerkultur. Kurze Kulturzeit (50--70 Tage), anspruchslos, toleriert Halbschatten. Kleine Rueben (Babybeets) sind zarter und koennen schon nach 6--8 Wochen geerntet werden. Zu dichte Aussaat oder zu spaete Vereinzelung fuehrt zu kleinen, deformierten Rueben.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 10--14 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 35--60 | 3 | false | true (Blaetter) | medium |
| Ernte (harvest) | 14--30 (Erntefenster) | 4 | true | true | medium |

Hinweis: Die Ruebe bildet sich waehrend der vegetativen Phase. Erntezeitpunkt ist flexibel -- kleine Rueben (4--6 cm Durchmesser, "Babybeets") sind zarter, grosse Rueben (8--12 cm) haben mehr Ertrag aber groebere Textur. Rueben koennen bis zum ersten starken Frost im Boden bleiben.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | -- (Dunkelkeimer, Samen im Boden) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 12--20 (optimal 15) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65--80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70--85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--25 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 14--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Vereinzeln (Ausdunnung), wenn Saemlinge 5 cm hoch sind! Pro Knauel nur die kraeftigste Pflanze stehen lassen (Abstand 10--15 cm). Die entfernten Saemlinge koennen vorsichtig an andere Stellen verpflanzt werden.

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (volle Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 (natuerlich) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--24 (optimal 18--20) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.3 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (gleichmaessig feucht, Trockenheit fuehrt zu holzigen Rueben und Rissen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Gleichmaessige Wasserversorgung ist entscheidend! Wechsel zwischen Trockenheit und Naesse fuehrt zu Rissen in den Rueben und Holzigkeit. Mulchen hilft, die Bodenfeuchte zu regulieren.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 5--20 (Herbst; Rueben vertragen leichte Froeste) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -6 -- 12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- (natuerlich) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (reduziert, Herbst) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Rueben mit einer Grabegabel vorsichtig aus dem Boden heben (nicht ziehen -- bricht ab). Blaetter 2--3 cm ueber der Ruebe abdrehen (nicht schneiden -- Ruebe blutet aus). Lagerung: kuehler Keller (2--5 degC) in feuchtem Sand, haelt 3--5 Monate.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 6.0--7.0 | 60 | 30 | 20 | 2 |
| Vegetativ | 2-1-3 | 1.0--1.6 | 6.0--7.0 | 100 | 50 | 30 | 3 |
| Ernte | 1-1-2 | 0.6--1.0 | 6.0--7.0 | 80 | 30 | 20 | 2 |

Hinweis: Rote Bete ist ein Mittelzehrer mit hohem Kaliumbedarf (K foerdert Ruebenwachstum und Zuckergehalt). Bor-Mangel ist ein haeufiges Problem (verursacht schwarze Stellen im Rueben-Inneren -- "Trockenfaeule"). Bei Bor-Verdacht: Borax-Loesung 1 g/10 L als Blattspruehung. Stickstoff nicht ueberdosieren (Nitratanreicherung!).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 10--14 Tage | Keimblaetter (Kotyledonen) voll entfaltet, Vereinzeln noetig |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 4--6 echte Blaetter, Ruebe beginnt sich sichtbar zu verdicken |
| Vegetativ -> Ernte | time_based / manual | 35--60 Tage | Ruebe hat gewuenschte Groesse (4--12 cm Durchmesser, oberirdisch sichtbar) |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Hydro/Coco -- moeglich aber unueblich)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |
| Kaliumsulfat | div. | supplement | 0-0-50 (+S 18%) | 0.08 | 5 | Vegetativ (Ruebenwachstum) |
| Borax-Loesung | div. | supplement | -- (+B) | -- | 6 | Vegetativ (bei Bor-Mangel) |

#### Organisch (Outdoor/Beet -- Standardkultur)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 3--5 L/m2 | Herbst/Fruehjahr (Einarbeitung vor Aussaat) | medium_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 50--70 g/m2 | Fruehjahr (Einarbeitung) | medium_feeder |
| Holzasche (kalireich) | Eigenerzeugung | organisch (K-betont) | 100--150 g/m2 | Fruehjahr (Einarbeitung) | medium_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 0.5 L/m2 | Mai--Aug, alle 21 Tage | medium_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 0.5 L/m2 | Jun--Sep, alle 21 Tage | medium_feeder |
| Algenkalk | div. | Bodenhilfsmittel | 100--150 g/m2 | Herbst (Kalkung + Spurenelemente inkl. Bor) | alle |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Rote Bete Standard Freiland")

| Woche | Phase | Massnahme | Hinweise |
|-------|-------|-----------|----------|
| 0 (Vorbereitung) | -- | 3--5 L/m2 Reifkompost + 50--70 g/m2 Hornmehl + 100 g/m2 Holzasche einarbeiten | Boden tiefgruendig lockern, Steine entfernen |
| 1--2 | Keimung | Nur Wasser | Kein Duenger noetig |
| 3--4 | Saemling | Nur Wasser, Vereinzeln | Saemlinge auf 10--15 cm Abstand ausdunnen |
| 5--8 | Vegetativ | Brennnesseljauche 1:10 alle 3 Wochen | N-Versorgung fuer Blattmasse |
| 9--12 | Vegetativ/Ernte | Beinwelljauche 1:10 alle 3 Wochen | Kalium fuer Ruebenwachstum |
| 12+ | Ernte | Keine Duengung mehr | Ernte nach Bedarf |

### 3.3 Mischungsreihenfolge

> **Bei mineralischer Duengung (selten noetig):**

1. Wasser temperieren (15--20 degC)
2. CalMag (Calcium + Magnesium)
3. Base A (Calcium + Mikronaehrstoffe)
4. Base B (Phosphor + Schwefel + Magnesium)
5. Kaliumsulfat
6. Bor-Zusatz (nur bei nachgewiesenem Mangel)
7. pH-Korrektur -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren.

### 3.4 Besondere Hinweise zur Duengung

- **Mittelzehrer mit hohem K-Bedarf:** Kalium foerdert Ruebenwachstum und Zuckergehalt. Holzasche oder Beinwelljauche sind ideale Kaliumquellen.
- **Bor-Mangel beachten!** Bor ist ein Spurenelement, das fuer Ruebengewaechse besonders wichtig ist. Bor-Mangel verursacht schwarze, korkige Stellen im Rueben-Inneren ("Trockenfaeule" / "Herz- und Trockenfaeule"). Bei Verdacht: Borax 1 g in 10 L Wasser als Blattspruehung. Algenkalk enthaelt Spurenelemente inkl. Bor.
- **Stickstoff nicht ueberdosieren:** Zu viel N fuehrt zu Nitrat-Akkumulation in den Rueben (gesundheitlich bedenklich, EU-Grenzwerte). Moderate N-Versorgung genuegt.
- **Kein Frischmist!** Frischer Mist foerdert Schorf und Deformationen an den Rueben.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 (gleichmaessig!) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig; bei Lagerrueben im Boden: natuerlicher Niederschlag) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Morgens giessen, bodennah. Gleichmaessige Bodenfeuchte ist entscheidend -- Wechsel zwischen nass und trocken fuehrt zu Rissen und Holzigkeit. Mulchen mit Stroh oder Grasschnitt hilft enorm. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig, Direktsaat bevorzugt) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Marz | Vorkultur (optional) | Aussaat in Topfplatten bei 15--18 degC, Saemlinge bei 4--6 Blaettern auspflanzen | mittel |
| Apr | 1. Direktsaat | Ab Mitte April bei Bodentemperatur > 8 degC, Saattiefe 2--3 cm, Reihenabstand 25--30 cm | hoch |
| Mai | Vereinzeln + 2. Saat | Saemlinge auf 10--15 cm Abstand ausdunnen (wichtig!), 2. Satz fuer spaetere Ernte saeen | hoch |
| Jun | Pflege | Hacken, Unkraut entfernen, Mulchen, gleichmaessig giessen, auf Erdfloh achten | mittel |
| Jul | Erntebeginn Babybeets + 3. Saat | Erste kleine Rueben (6--8 Wochen nach Aussaat), letzten Satz fuer Herbsternte saeen | hoch |
| Aug | Haupternte | Rueben in gewuenschter Groesse ernten, Blaetter fuer Salat mitverwenden | hoch |
| Sep | Ernte fortsetzen | Spaetere Saetze ernten, auf Cercospora-Blattflecken achten | hoch |
| Okt | Herbsternte + Einlagerung | Vor dem ersten starken Frost Rueben ernten und einlagern (Erdmiete, Keller bei 2--5 degC in feuchtem Sand) | hoch |
| Nov | Letzte Ernte | Restliche Rueben aus dem Boden holen, bei mildem Klima mit Frostschutz auch laenger moeglich | mittel |

### 4.3 Ueberwinterung

Rote Bete kann mit Frostschutz (Stroh, Laub, Vlies) bis in den fruehen Winter im Boden bleiben. Bei laengerem Frost (unter -6 degC) Rueben ernten und in feuchtem Sand kuhl lagern (Keller, Erdmiete). Lagertemperatur: 2--5 degC, Luftfeuchtigkeit: 90--95%. Haltbarkeit: 3--5 Monate. Im Fruehjahr des 2. Jahres wuerden die Rueben schossen -- fuer Saatgutgewinnung eine Ruebe ueberwint

ern und im Fruehjahr wieder einpflanzen.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Ruebenfliege (Beet Leaf Miner) | Pegomya hyoscyami | Blattminen (durchscheinende Flecken), Larven fressen im Blattgewebe | leaf | vegetative | medium |
| Erdfloh (Flea Beetle) | Chaetocnema concinna | Kleine runde Loecher in Blaettern (Lochfrass), besonders an Keimlingen | leaf | seedling, vegetative | easy |
| Schnecken (Slugs/Snails) | Arion spp. | Lochfrass an Blaettern und jungen Rueben, Schleimspuren | leaf, root | seedling | easy |
| Schwarze Bohnenlaus (Black Bean Aphid) | Aphis fabae | Dichte Kolonien an Blattunterseiten und Blattstielen, Blattkraeuselung | leaf, stem | vegetative | easy |
| Drahtwuermer (Wireworm) | Agriotes spp. | Fraessgaenge in Rueben | root | vegetative | hard |
| Ruebennematoden | Heterodera schachtii | Wuchshemmung, gelbe Blaetter, Zysten an Wurzeln | root | vegetative | hard |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Cercospora-Blattflecken (Cercospora Leaf Spot) | fungal | Kleine runde Flecken mit rotem/violettem Rand und grauem Zentrum auf Blaettern; bei starkem Befall Blattverlust bis 40% | warm_humid_conditions, rain_splash | 7--14 | vegetative |
| Ramularia-Blattflecken | fungal | Braune, unregelmaeessige Blattflecken, aehnlich Cercospora | humid_conditions | 7--14 | vegetative |
| Falscher Mehltau (Downy Mildew) | fungal (Oomycet) | Gelbe Flecken auf Blattoberseite, grauer Belag auf Unterseite | cool_wet_conditions | 5--10 | seedling, vegetative |
| Schwarzbeinigkeit (Damping Off) | fungal | Saemlinge knicken an Basis um | overwatering, cold_wet_soil | 2--5 | seedling |
| Herz- und Trockenfaeule (Boron Deficiency) | physiological | Schwarze, korkige Stellen im Rueben-Inneren, rissige Oberflaeche | boron_deficiency | -- | vegetative |
| Schorf (Common Scab) | bacterial / fungal | Raue, korkige Stellen auf der Ruebenoberflaeche | alkaline_soil, dry_conditions | 14--28 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Schwarze Bohnenlaus | 5--10 | 14 |
| Coccinella septempunctata (Marienkaefer) | Schwarze Bohnenlaus | 5--10 | 7--14 |
| Steinernema feltiae (Nematode) | Ruebenfliege (Bodenstadien), Schnecken | 250.000/m2 | 7--14 |
| Phasmarhabditis hermaphrodita (Nematode) | Nacktschnecken | 300.000/m2 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetze | mechanical | -- | Feinmaschiges Netz ueber Bestand ab Aussaat | 0 | Ruebenfliege, Erdfloh |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Schwarze Bohnenlaus |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Erdfloh |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Spruehung 1:5 verduennt, alle 14 Tage praeventiv | 0 | Cercospora, Pilzkrankheiten |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen, im Restmuell entsorgen (nicht Kompost!) | 0 | Cercospora, Ramularia |
| Fruchtfolge (min. 3--4 Jahre) | cultural | -- | Keine Chenopodiaceae/Amaranthaceae auf gleicher Flaeche | 0 | Cercospora, Nematoden |
| Borax-Blattspruehung | cultural | Bor | 1 g Borax / 10 L Wasser, 1x Blattspruehung | 0 | Herz- und Trockenfaeule (Bor-Mangel) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Cercospora beticola (Toleranz) | Krankheit | Einige Cultivare zeigen bessere Toleranz (z.B. 'Boro F1', 'Pablo F1') | `resistant_to` |
| Schossen (Bolting Resistance) | physiologisch | Cultivare mit guter Schossfestigkeit (z.B. 'Boro F1', 'Chioggia') | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium) |
| Fruchtfolge-Kategorie | Gaensefussgewaechse (Amaranthaceae/Chenopodiaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae), Getreide, Kartoffeln -- lockerer, stickstoffreicher Boden |
| Empfohlene Nachfrucht | Schwachzehrer (Feldsalat, Radieschen) oder Gruenduengung |
| Anbaupause (Jahre) | 3--4 Jahre fuer Amaranthaceae (Rote Bete, Mangold, Spinat, Zuckerruebe) auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Zwiebel | Allium cepa | 0.9 | Gegenseitige Schaedlingsabwehr (Erdfloh), Dufttarnung | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Pilzabwehr durch Allicin, Schaedlingsabwehr | `compatible_with` |
| Buschbohne | Phaseolus vulgaris | 0.8 | Stickstoffversorgung, verschiedene Wurzeltiefen | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.8 | Verschiedene Reifzeiten, gute Platznutzung | `compatible_with` |
| Kopfsalat | Lactuca sativa var. capitata | 0.8 | Schnelle Zwischenkultur, Bodenbeschattung | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Nuetzlinge anlocken (Schwebfliegen), Blattlaus-Kontrolle | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Nuetzlingsfoerderung, Bodenbeschattung | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Verschiedene Wuchshoehen, gute Platznutzung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Mangold | Beta vulgaris subsp. vulgaris (Blatt) | Gleiche Art, gemeinsame Schaedlinge/Krankheiten (Cercospora, Nematoden), Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Spinat | Spinacia oleracea | Gleiche Familie, gemeinsame Krankheiten (Falscher Mehltau), Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Beide Knollengewaechse, Konkurrenz um Platz im Boden, gemeinsame Bodenschaedlinge | mild | `incompatible_with` |
| Lauch / Porree | Allium porrum | Naehrstoffkonkurrenz (beide brauchen viel Kalium) | mild | `incompatible_with` |
| Mais | Zea mays | Starke Beschattung, Wasserkonkurrenz | mild | `incompatible_with` |
| Karotte | Daucus carota subsp. sativus | Naehrstoffkonkurrenz um Bor und Mangan im Wurzelbereich; beide tiefwurzelnde Gemuese verdraengen sich gegenseitig bei geringer Bodentiefe | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Amaranthaceae (mit sich selbst) | `shares_pest_risk` | Cercospora, Ramularia, Ruebennematoden (Heterodera schachtii), Ruebenfliege | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Rote Bete |
|-----|-------------------|-------------|------------------------------|
| Mangold | Beta vulgaris subsp. vulgaris (Blattgruppe) | Gleiche Art! Blattkultur statt Ruebenkultur | Mehrfache Ernte, dekorative Sorten, weniger Oxalsaeure |
| Gelbe Bete | Beta vulgaris subsp. vulgaris 'Burpee's Golden' | Gleiche Art, gelbe Ruebe | Faerbt nicht, milder Geschmack, weniger "erdig" |
| Chioggia-Bete | Beta vulgaris subsp. vulgaris 'Chioggia' | Gleiche Art, ringfoermig rot-weiss gestreifte Ruebe | Dekorativ, milder Geschmack |
| Pastinake | Pastinaca sativa | Aehnliche Kultur (Wurzelgemuese) | Winterhart, suesserer Geschmack nach Frost |
| Moehre | Daucus carota | Aehnliche Kultur (Wurzelgemuese) | Kuerzere Kulturzeit, vielseitiger verwendbar |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Beta vulgaris subsp. vulgaris,Rote Bete;Rote Ruebe;Rote Beete;Rahne;Beetroot;Red Beet;Table Beet,Amaranthaceae,Beta,biennial,long_day,herb,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b,0.0,"Mittelmeerraum, Westasien"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Boro F1,Beta vulgaris subsp. vulgaris,Bejo,,high_yield;disease_resistant,55,cercospora,f1_hybrid
Pablo F1,Beta vulgaris subsp. vulgaris,Bejo,,high_yield;disease_resistant,58,cercospora,f1_hybrid
Chioggia,Beta vulgaris subsp. vulgaris,,,ornamental;heirloom,55,,open_pollinated
Tonda di Chioggia,Beta vulgaris subsp. vulgaris,,,ornamental;heirloom,55,,open_pollinated
Detroit Dark Red,Beta vulgaris subsp. vulgaris,,1892,heirloom;high_yield,60,,open_pollinated
Rote Kugel 2,Beta vulgaris subsp. vulgaris,,,compact;heirloom,60,,open_pollinated
Cylindra,Beta vulgaris subsp. vulgaris,,,high_yield;heirloom,60,,open_pollinated
Burpee's Golden,Beta vulgaris subsp. vulgaris,Burpee,,ornamental;heirloom,55,,open_pollinated
Bull's Blood,Beta vulgaris subsp. vulgaris,,,ornamental;heirloom,60,,open_pollinated
```

---

## Quellenverzeichnis

1. Hortipendium -- Speise Bete Pflanzenschutz: https://hortipendium.de/Speise_Bete_Pflanzenschutz
2. Wikipedia -- Rote Bete: https://de.wikipedia.org/wiki/Rote_Bete
3. Bio-Gaertner -- Rote Bete: https://www.bio-gaertner.de/Pflanzen/Rote-Bete
4. fryd.app -- Mischkultur mit Rote Bete: https://fryd.app/magazin/mischkultur-mit-rote-bete
5. samen.de -- Rote Bete in Mischkultur: https://samen.de/blog/rote-bete-in-mischkultur-vielfalt-im-gemuesebeet.html
6. samen.de -- Rote Bete Fruchtfolge: https://samen.de/blog/rote-bete-im-fruchtwechsel-gesunde-ertraege-ernten.html
7. gartenratgeber.net -- Rote Bete: https://www.gartenratgeber.net/pflanzen/rote-bete-ruebe.html
8. pflanzenkrankheiten.ch -- Cercospora: https://www.pflanzenkrankheiten.ch/krankheiten-an-kulturpflanzen-2/weitere-ackerkulturen/zuckerrueben/cercospora-beticola
9. schadbild.com -- Blattflecken an Roter Bete: https://www.schadbild.com/gem%C3%BCse/rote-bete/blattflecken/
10. eat.de -- Rote Beete gefaehrlich: https://eat.de/magazin/rote-beete-gefaehrlich/
11. grove.eco -- Rote Bete: https://www.grove.eco/pflanzen/beta-vulgaris-vulgaris-conditiva/
12. Koraylights -- Indoor cultivation PPFD and DLI: https://koraylights.com/how-much-light-do-your-plants-need-indoor-cultivation-ppfd-and-dli/
