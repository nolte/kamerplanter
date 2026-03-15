# Pfauenblume / Tigerblume -- Tigridia pavonia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:** Wikipedia (Tigridia pavonia), Pacific Bulb Society, Gardeners Path, Gardening Know How, Gardenmarkt.de, Hortica.de, Floragard, PFAF Database, NC State Extension, Gardenia.net, procvetok.com, plantcaretoday.com, harvesttotable.com

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tigridia pavonia | `species.scientific_name` |
| Volksnamen (DE/EN) | Pfauenblume; Tigerblume; Tiger Flower; Mexican Shell Flower; Peacock Flower; Jockey's Cap Lily | `species.common_names` |
| Familie | Iridaceae | `species.family` → `botanical_families.name` |
| Gattung | Tigridia | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | corm (Korm — solides Speicherorgan ohne Schalen; bildet jährlich Tochterkormen an der Basis; keine echte Zwiebel) | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Knollen nicht frosthart in Mitteleuropa (Zone 7--8). Schaeden ab ca. -2 degC. In USDA Zone 7--8 koennen Knollen mit starker Mulchschicht von 15--20 cm ueberwintern, ist jedoch risikoreich. Sicherer: Knollen nach dem ersten Frost ausgraben und frostfrei bei 10--13 degC einlagern. In Zone 9--10 koennen Knollen im Boden verbleiben. | `species.hardiness_detail` |
| Heimat | Mexiko, Guatemala, Kolumbien; Kiefer- und Eichenwald-Zonen auf 2000--3000 m Hoehe | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental; bee_friendly | `species.traits` |

Hinweis: Tigridia pavonia ist ein knollenbildendes Geophyt der Familie Iridaceae (Schwertliliengewaechse). Die kurzlebigen Blueten -- jede Einzelbluete oeffnet nur einen einzigen Tag -- erscheinen nacheinander ueber mehrere Wochen. Gegen Ende der Vegetationsperiode erschoepft sich die Mutterknolle vollstaendig und wird von bis zu 5 Tochterzwiebeln ersetzt. Dies ist ein wichtiger Unterschied zu echten Zwiebelpflanzen (Tulpe, Narzisse): Bei Tigridia handelt es sich botanisch korrekt um eine Knolle (Corm), nicht um eine echte Zwiebel. Allelopathische Wirkung ist bisher nicht nachgewiesen (Neutralwert 0.0).

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6--8 (Voranzucht ab Maerz innen moeglich, nicht notwendig) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0--14 (Pflanzung der Knollen direkt nach letztem Frost, sobald Bodentemperatur > 12 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 (Knolle direkt ins Beet, nicht Samen) | `species.direct_sow_months` |
| Erntemonate | -- (Zierpflanze, keine Nahrungsernte; Knollenernte nach Bluetenende: 9; 10) | `species.harvest_months` |
| Bluetemonate | 7; 8; 9 | `species.bloom_months` |

Hinweis: "Direktsaat" ist hier ungenau -- gemeint ist die Pflanzung der Knollen (Corms). Knolle wird 8--10 cm tief und 10--15 cm Abstand gesetzt. Eine echte Samenvermehrung ist fuer den Freilandanbau unueblich, da Samen erst im 2. Jahr blueht. Knolle im Herbst nach dem ersten Frost ausgraben (Oktober), 2--4 Wochen luftig bei Zimmertemperatur trocknen, dann bei 10--13 degC dunkel und trocken bis Mai einlagern.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset; division; seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Die einfachste und gaengigste Methode ist die Teilung der Tochterknollen (Offset) beim Ausgraben im Herbst. Jede Mutterknolle bildet 2--5 Tochterknollen. Samenanzucht ist moeglich (Keimzeit ca. 25--35 Tage bei 15--18 degC), die Pflanzen bluehen jedoch erst im 2. Jahr. Bei Aussaat im Maerz in Innenraeumen koennen kraeftige Samlinge unter idealen Bedingungen noch im ersten Jahr bluehen. Keinerlei Kreuzungsbarrieren zwischen Sorten vorhanden.

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine; rohe Knollen koennen Mundreizungen verursachen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (keine bekannten Toxine; rohe Knollen enthalten Reizstoff) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (rohe Knolle: Mundreizung moeglich; gekochte Knolle essbar) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Insektenbestaeubung; Pollen nicht aerogen) | `species.allergen_info.pollen_allergen` |

Quelle: Tigridia pavonia ist in der ASPCA-Toxizitaetsliste nicht als giftig gelistet. Die Knollen wurden traditionell von indigenen Voelkern Mexikos und Kolumbiens als Nahrungsmittel genutzt (Roestknolle mit kastanienaehnlichem Geschmack). Rohe Knollen koennen jedoch Mundschleimhaut-Irritationen verursachen (brennendes Gefuehl). Schwerwiegende Vergiftungen sind nicht bekannt. Bei Haustieren, die Knollen ausgraben und roh verzehren, sind gastrointestinale Beschwerden moeglich.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | after_harvest | `species.pruning_type` |
| Rueckschnitt-Monate | 9; 10 | `species.pruning_months` |

Hinweis: Nach dem Ende der Bluehperiode (September/Oktober) das Laub stehen lassen, bis es vergilbt und abstirbt -- die Knolle benoetigt diese Zeit, um Reservestoffe zurueckzulagern. Erst dann Stiele auf 2--3 cm einkuerzen und Knollen ausgraben. Kein Winterrueckschnitt bei eingelagerten Knollen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5--10 (3--5 Knollen pro 10-L-Kuebelanpflanzung) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 (Knolle benoetigt min. 10 cm Bodenanschluss + 8--10 cm Pflanztiefe) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 45--75 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15--30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10--15 (Einzelknolle); empfohlen: Gruppen von 5--10 Knollen fuer dekorativen Effekt | `species.spacing_cm` |
| Indoor-Anbau | limited (als Topfpflanze moeglich, benoetigt hellen Fensterbankplatz oder Suedbalkon) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (ideal fuer Suedbalkon in Topf) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false (bei windigen Standorten optionale Stuetze bei > 60 cm Wuchshoehe empfehlenswert) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Locker-sandig-lehmige Erde (Verhaeltnis: 1 Teil Gartenboden, 1 Teil Sand/Perlite, 1 Teil Kompost). pH 6.0--6.5. Sehr gute Drainage zwingend -- Staunasse fuehrt zu Knollenfaeule. Alternativ: Standard-Balkonkaestenerde mit 30% Perlite-Zusatz. | -- |

---

## 2. Wachstumsphasen

Tigridia pavonia ist eine perenniale Knollenpflanze mit ausgepraegter Vegetationsruhe (Dormanz). Der jaehrliche Zyklus in Mitteleuropa umfasst folgende Phasen. Da die Knollen in Zone 7--8 ausgegraben und eingelagert werden, beginnt der Zyklus bei Auspflanzung.

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Austrieb / Bewurzelung | 14--28 | 1 | false | false | low |
| Vegetatives Wachstum | 30--50 | 2 | false | false | medium |
| Abhaertung (Hardening-Off) | 7--14 | 3 | false | false | medium |
| Knospenbildung | 14--21 | 4 | false | false | medium |
| Bluete | 42--63 | 5 | false | false | medium |
| Abreife / Knollenaufbau | 28--42 | 6 | false | false | high |
| Dormanz (Einlagerung) | 150--180 | 7 | false | false | high |

Hinweis: Phase 3 (Abhaertung) ist nur relevant fuer vorgezogene Innenpflanzen -- bei direkter Knolle ins Freiland entfaellt diese Phase. Die Dormanz (Phase 7) wird in Mitteleuropa kuenstlich erzeugt durch Ausgrabung und Trockenlagerung (Oktober--Mai).

### 2.2 Phasen-Anforderungsprofile

#### Phase 1: Austrieb / Bewurzelung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200--400 (Volllicht, aber Jungpflanzen noch nicht direktem Mittagssonnenbrand aussetzen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15--22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 (natuerlisches Tageslicht Mai; tagneutral) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Aussenluft; keine Erhoehung noetig) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5--7 (Boden leicht feucht halten; Knolle braucht kaum Wasser vor Austreiben) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 2: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500--800 (volle Sonne; suedexponiert) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25--40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (natuerlisches Sommerlicht; keine Steuerung noetig) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Aussenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2--4 (gleichmaessig feucht; Substrat zwischen Gaben nicht vollstaendig austrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200--400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 3: Abhaertung (Hardening-Off, nur bei Voranzucht)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400--700 (zunehmende Direkssonnenexposition ueber 7--14 Tage) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--15 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--24 (wechselnd innen/aussen) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3--5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150--300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 4: Knospenbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600--900 (volle Sonne zwingend fuer optimale Bluetenbildung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 30--45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Aussenluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2--3 (regelmaessig giessen; Trockenheit in dieser Phase verzoegert Bluetenbildung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 250--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 5: Bluete

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600--900 (volle Sonne; jede Einzelbluete oeffnet nur 1 Tag) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 30--45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 13--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--60 (nicht zu hoch -- Botrytis-Risiko an Bluetenblaettern) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2--3 (bei Hitze taeglich; morgens giessen, niemals auf Blueten) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300--500 (bei Hitze > 28 degC erhoehen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 6: Abreife / Knollenaufbau

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400--700 (Herbstsonne reicht aus) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15--25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--13 (abnehmende Taglaenge) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4--7 (reduzieren; Boden trockener halten fuer Knollenreife) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150--300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 7: Dormanz (Einlagerung)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 (Dunkel- oder Halbdunkellagerung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 (keine Lichtanforderung waehrend Dormanz) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 10--13 (Lagertemperatur konstant; kein Temperaturunterschied Tag/Nacht) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--13 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 (zu trocken = Knollen schrumpfen; zu feucht = Faeulnis) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (keine aktive Steuerung) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | -- (keine Anforderung) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 0 (kein Gießen waehrend Dormanz -- Knollen trocken lagern) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Austrieb | 1:1:1 | 0.4--0.8 | 6.0--6.5 | 60 | 20 | -- | 1 |
| Vegetativ | 2:1:1 | 0.8--1.2 | 6.0--6.5 | 100 | 30 | -- | 2 |
| Abhaertung | 1:1:1 | 0.6--1.0 | 6.0--6.5 | 80 | 25 | -- | 1 |
| Knospenbildung | 1:2:2 | 1.0--1.4 | 6.0--6.5 | 80 | 35 | -- | 1 |
| Bluete | 0:2:2 | 0.8--1.2 | 6.0--6.5 | 60 | 30 | -- | 1 |
| Abreife | 0:1:2 | 0.4--0.8 | 6.0--6.5 | 40 | 20 | -- | -- |
| Dormanz | 0:0:0 | 0.0 | -- | -- | -- | -- | -- |

Hinweis: Tigridia pavonia ist ein Schwach- bis Mittelzehrer. Die haeufigste Pflegefehlerquelle ist Ueberdungung mit Stickstoff, die ueppiges Blattwachstum auf Kosten der Knollenentwicklung und Bluetenbildung foerdert. In der Knospen- und Bluetephase ist Phosphor und Kalium (P, K) wichtiger als Stickstoff. Keine Duengung waehrend der Dormanz.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/Bedingung | Bedingungen |
|------------|---------|----------|-------------|
| Dormanz -> Austrieb | time_based / manual | 14--28 Tage nach Auspflanzung | Bodentemperatur > 12 degC; letzte Frost vorbei (Zone 7--8: ab Mitte Mai) |
| Austrieb -> Vegetativ | time_based | 14--28 Tage | Erste schwertfoermige Blaetter voll entfaltet (3--5 cm) |
| Vegetativ -> Abhaertung | manual | 7--14 Tage | Nur bei Voranzucht; sukzessive Aussenexposition |
| Vegetativ -> Knospenbildung | event_based | -- | Erste Knospenanlagen sichtbar (Juni--Juli) |
| Abhaertung -> Knospenbildung | event_based | -- | Nach vollstaendiger Abhaertung; erste Knospen erkennbar |
| Knospenbildung -> Bluete | time_based | 14--21 Tage | Erste Bluete oeffnet sich |
| Bluete -> Abreife | event_based | -- | Letzte Blaettenspitze an Stiel verblueht; September--Oktober |
| Abreife -> Dormanz (Ausgraben) | manual | 28--42 Tage | Nach Laubgelbfaerbung Knollen ausgraben; 2--4 Wochen Trocknung bei Zimmertemperatur |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Topfkultur / Balkon)

| Produkt | Marke | Typ | NPK | Dosierung | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Compo Bluehpflanzendünger | Compo | Fluessigduenger | 5-8-10 | 15--20 ml / 5 L | 3 | Knospenbildung, Bluete |
| Hakaphos Blau (Bluetenduenger) | Compo Expert | Wasserloeslich | 6-12-36 | 2--3 g / L | 3 | Knospenbildung, Bluete |
| Compo Gruenpflanzenduenger | Compo | Fluessigduenger | 5-2-5 | 10--15 ml / 5 L | 3 | Austrieb, Vegetativ |
| Substral Langzeitduenger Bluehpflanzen | Substral | Depot-Langzeitduenger | 6-4-8 | 3--5 g / L Substrat | -- | Saison gesamt |

#### Organisch (Freilandbeet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Hornspaene | Hamann Agrar / allg. | organisch-stickstoffbetont | 30--50 g / m² | Maerz--April (vor Pflanzung) | Austrieb, Vegetativ |
| Kompost | eigen / allg. | organisch | 2--3 L / m² | Maerz--April (einarbeiten) | alle Phasen (Bodenverbesserung) |
| Blaukorn / Blumenduenger granuliert | Compo / Substral | Volldünger Granulat | 20--30 g / m² | April--Juni | Vegetativ, Knospenbildung |
| Kalimagnesia | allg. (Patentkali) | Kali-Magnesia-Mineralsalz | 20--30 g / m² | vor und waehrend Bluete | Knospenbildung, Bluete, Abreife |

### 3.2 Duengungsplan (Freiland-Beet, Mitteleuropa)

| Monat | Phase | Massnahme | Produkt (Beispiel) | Hinweise |
|-------|-------|-----------|-------------------|----------|
| April / Maerz | Bodenvorbereitung | Einarbeitung vor Pflanzung | Kompost 2--3 L/m²; Hornspane 40 g/m² | Substrat lockern, pH pruefen (Ziel: 6.0--6.5) |
| Mai / Juni | Austrieb + Vegetativ | Erste Gabe nach Austreiben | Blaukorn 20 g/m² oder Compo Gruenpflanzend. 10 ml/5 L | Nicht ueberdungen -- Wurzeln noch empfindlich |
| Juni / Juli | Vegetativ + Knospenbildung | Wechsel auf bluetebetonte Duengung | Hakaphos Blau 2 g/L alle 14 Tage | NPK-Verhaeltnis auf P + K umstellen |
| Juli / August | Bluete | Fluessigduenger bluetenfoerdernd | Compo Bluehpflanzenduenger 15 ml/5 L alle 14 Tage | Nicht mehr stickstoffbetont duengen |
| August / September | Ausklang Bluete / Abreife | Letzte Gabe Kalimagnesia | Patentkali 25 g/m² | Knollenstabilisierung foerdern |
| Oktober | Abreife / Ausgraben | Keine Duengung mehr | -- | Wasser reduzieren; Laub abwarten |

### 3.3 Mischungsreihenfolge (bei Einsatz mehrerer Fluessigduenger)

> **Wichtig:** Tigridia pavonia wird typischerweise mit einem einzigen Bluetenduenger versorgt -- komplexe Mehrkomponenten-Mischungen sind fuer diese Art unnoetig. Bei kombiniertem Einsatz gilt:

1. Silikat-Zusaetze (falls verwendet)
2. Mikronährstoff-Ergaenzung (CalMag, falls Mangel erkennbar)
3. Basis-Bluetenduenger (NPK-Konzentrat)
4. pH-Korrektur (Zitronensaeure oder pH-Down; IMMER zuletzt)

### 3.4 Besondere Hinweise zur Duengung

Tigridia pavonia ist kein Starkzehrer. Die haeufigste Falle ist uebermassiger Stickstoffeinsatz (N), der zu folgenden Problemen fuehrt:

- **Blattueppigkeit statt Bluetenbildung:** N-Ueberschuss foerdert vegetatives Wachstum auf Kosten der Knospenbildung. Charakteristisches Bild: gruene, kräftige Pflanze -- aber keine Blueten.
- **Schwache Knolle:** Zu viel N fuehrt zu schlechter Knollenentwicklung, die Tochterknollen sind kleiner und schwaecher.
- **Stickstoffsensitiv in der Bluetephase:** Ab Knospenbildung KEINEN stickstoffbetonten Duenger mehr verwenden.

Empfehlung: NPK-Verhaeltnis waehrend der Bluehphase max. 1:3:3. Phosphor (P) und Kalium (K) sind die Schluessel zu reicher Bluete. Kein Duengen nach September -- die Knolle muss sich auf die Dormanz vorbereiten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2--3 (Hauptbluetenzeit Juli--August; bei Hitze taeglich) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (kein Giessen waehrend Dormanz; Knollen trocken einlagern) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain (kraeftig durchgiessen, kein Staunasser Untersetzer; morgens giessen) | `care_profiles.watering_method` |
| Wasserqualitaets-Hinweis | Leitungswasser geeignet; bei hartem Wasser (> 15 dH) leicht saurerem Gieswasser (pH 6.2--6.5) bevorzugen | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 (Bluehphasen); 30 (Wachstum) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jaehrlich neue Erde; Knollen im Fruehling neu setzen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false (Freilandpflanze; kein aktives LF-Management noetig) | `care_profiles.humidity_check_enabled` |

Hinweis zu "mediterranean" als care_style: Tigridia pavonia stammt aus hoch gelegenen Wald- und Savannengebieten Mexikos mit mediterranem Klima (trockener Sommer, kalter Winter). Der care_style `mediterranean` trifft das Gießverhalten (durchdringend giessen, dann gut abtrocknen lassen, keine Staunasse) am besten. Die Schluessel-Parallele zu mediterranen Kraeuter-Pflanzen: trockene Ruhephase, Vollsonne, gut drainiertes Substrat.

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Januar | Knollenkontrolle | Eingelagerte Knollen auf Faule und Austrocknung pruefen; faule Teile entfernen | mittel |
| Februar | Knollenkontrolle | Wiederholung; bei vorzeitigem Austreiben Knollen in frostefreien Raum bringen | niedrig |
| Maerz | Voranzucht (optional) | Knollen ab Maerz in Innenraeumen vortreiben (10 cm Tiefe, 15--18 degC); gibt 3--4 Wochen Vorsprung | niedrig |
| April | Bodenvorbereitung | Beet mit Kompost und Hornspanen anreichern; pH-Test (Ziel: 6.0--6.5); Drainage pruefen | mittel |
| Mai | Auspflanzung | Nach letztem Frost (Zone 7--8: Mitte Mai) Knollen 8--10 cm tief pflanzen; Gruppen zu 5--10 Knollen | hoch |
| Mai / Juni | Abhaertung | Vorgezogene Innenpflanzen schrittweise an Aussen-Sonnenlicht gewoehnen (7--14 Tage) | mittel |
| Juni | Erste Duengung | Wachstumsbetonte Duengung starten (NPK 2:1:1); Beet feucht halten | mittel |
| Juli | Knospen / Bluete | Auf erste Knospen achten; Duengung umstellen auf bluetebetont (NPK 1:2:2); regelmaessig giessen | hoch |
| August | Hauptbluete | Abgebluehte Blaettenstaengel nicht entfernen -- naechste Knospen wachsen aus dem gleichen Stiel | hoch |
| September | Ausklang Bluete | Letzte Gabe Kalimagnesia (Knollenaufbau); Wasser schrittweise reduzieren | mittel |
| Oktober | Ausgraben | Nach erstem Frost oder Laubgelbfaerbung Knollen ausgraben; Laub auf 2--3 cm einkuerzen | hoch |
| Oktober / November | Trocknungsphase | Knollen 2--4 Wochen luftig bei 15--20 degC trocknen; Erde abraeumen; kranke Knollen aussondern | hoch |
| November | Einlagerung | Gesunde Knollen in Saegemehl, Kokosfaser oder Papiertuecher einwickeln; bei 10--13 degC dunkel lagern | hoch |
| Dezember | Ruhephase | Knollen monatlich kontrollieren (Faeulnis, Schimmel); kein Giessen | niedrig |

### 4.3 Ueberwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Rating | dig_and_store | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | dig_store (Knollen ausgraben und trocken lagern) | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 10 (nach erstem Frost oder Laubgelbfaerbung) | `overwintering_profiles.winter_action_month` |
| Fruehlings-Massnahme | replant (Knollen nach Frost wieder auspflanzen) | `overwintering_profiles.spring_action` |
| Fruehlings-Massnahme Monat | 5 (nach letztem Frost; Mitte Mai fuer Zone 7--8) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (degC) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (degC) | 13 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark (Dunkel- oder Halbdunkellagerung; kein Licht noetig) | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | none (absolut kein Wasser; Knollen muessen trocken bleiben) | `overwintering_profiles.winter_watering` |

**Wichtig:** Tigridia-Kormen NICHT gemeinsam mit Dahlienknollen bei 4–8 °C lagern. Tigridia benötigt 10–13 °C; tiefere Temperaturen schädigen die Kormen. Idealer Lagerort: frostfreier Keller oder kühler Raum (10–15 °C, nicht kalt).

Hinweis: Die korrekte Lagerung ist entscheidend fuer den Erfolg im naechsten Jahr. Haeufige Fehler: (1) Knollen zu frueh ausgraben (Knolle muss noch Reserven einlagern -- Laub muss erst vollstaendig gelb werden). (2) Zu feuchte Lagerung (Botrytis-Faeulnis). (3) Zu warme Lagerung (> 15 degC foerdert vorzeitiges Austreiben). (4) Laetzte Knollen mit feuchter Erde einlagern (Faeulnis). Empfohlenes Lagermedium: trockenes Saegemehl, Kokosfaser, Zeitungspapier oder Perlite. In Zone 9--10 koennen Knollen mit 10--15 cm Mulchschicht im Boden verbleiben.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste an Blattunterseiten; gelbe Stippung; Blaetter vergrauen | leaf | vegetative, flowering | medium |
| Schwarze Bohnenlaus | Aphis fabae | Kolonien an Triebspitzen und Blattstielen; Honigtau; Rußtau | leaf, stem | vegetative, flowering | easy |
| Gruene Pfirsichblattlaus | Myzus persicae | Kolonien; Blattkraeuselung; Honigtau; Virusuebertragung | leaf | vegetative | easy |
| Thripse (Westlicher Bluetenthips) | Frankliniella occidentalis | Silbergraue Flecken auf Bluetenblaettern; Blaetter verbraeunt | leaf, flower | flowering | difficult |
| Wuehlmaus / Erdmaus | Arvicola terrestris | Knollen werden von unten angefressen und verschwinden (Freiland) | corm | dormancy, sprouting | difficult |

Hinweis: Spinnmilben sind bei Tigridia unter Hitzestress (> 30 degC) und niedriger Luftfeuchte (< 40%) besonders haeufig. Hitzewellen im Juli--August sind der haeufigste Ausloser. Wuehlmausbefall ist bei Freilandkultur ein unterschaetztes Risiko -- die Knollen werden gerne als Wintervorrat gefressen. Physische Schutzmaßnahmen (Pflanzkorb aus Drahtgeflecht) sind die effektivste Vorbeugung.

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Knollenfaeule / Corm Rot | fungal (Fusarium oxysporum; Penicillium spp.) | Braune, weiche Faulstellen an Knolle; Pflanze knickt ein | Staunasse; schlecht drainierendes Substrat; verletzte Knollen | 7--21 | sprouting, dormancy |
| Grauschimmel | fungal (Botrytis cinerea) | Grau-braune Flecken auf Bluetenblaettern und Blatt; Sporenstaub bei Beruehrung | hohe Luftfeuchte > 80%; Schwuelwetter; dichte Bepflanzung | 2--5 | flowering, storage |
| Echter Mehltau | fungal (Podosphaera xanthii; ehem. Sphaerotheca sp.) | Weißes Pulveriges Belag auf Blattoberfläche | trockene warme Tage + kühle Naechte; schlechte Durchlueftung | 5--10 | vegetative, flowering |
| Viruskrankheiten (Mosaikviren) | viral | Blattflecken; Mosaikmuster; Wuchsdepression; deformierte Blueten | Blattlaus-Uebertragung; infiziertes Pflanzgut | variabel | vegetative |

Hinweis: Knollenfaeule ist die gefaehrlichste Erkrankung und oft erst bei Ausgrabung im Herbst sichtbar. Praeventive Massnahme: Knollen vor Pflanzung in Fungizidloesung (Thiram oder Captan) kurz eintauchen. Botrytis ist in feuchten Sommern und bei zu dichter Bepflanzung das haeufigste Bluetenproblem -- gute Durchlueftung (Abstand 10--15 cm) ist die beste Vorbeugung.

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe | 20--50 | 14--21 |
| Neoseiulus californicus (Raubmilbe) | Spinnmilbe | 25--50 | 14--21 |
| Aphidius colemani (Schlupfwespe) | Gruene Pfirsichblattlaus | 3--5 | 14--21 |
| Chrysoperla carnea (Florfliege-Larven) | Blattlaeuse allgemein | 5--10 | 10--14 |
| Orius laevigatus (Raubwanze) | Thripse | 1--2 | 14--21 |

Hinweis: Fuer den Freilandgarten ist der Einsatz kommerzieller Nuetzlinge nur bei starkem Befall wirtschaftlich. Im Normalfall reichen folgende Massnahmen: Spinnmilben mit starkem Wasserstrahl von Blattunterseiten abspuelen; Blattlaeuse von Hand abstreifen oder mit Seifenlosung behandeln; Nützlinge foerdern durch Bluehmischungen in der Naeher (Tagetes, Ringelblume, Dill).

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoel-Loesung | biological | Azadirachtin | Sprueher, 0.3--0.5% Loesung; abends anwenden (Bienenschutz) | 3 | Blattlaeuse, Spinnmilben, Thripse |
| Schmierseifenloesung | biological | Kaliseife | 1--2% Loesung sprueher; bei Blattlaus-Befall | 0 | Blattlaeuse, Spinnmilben |
| Wasserdruck-Behandlung | cultural | -- | Starker Wasserstrahl auf Blattunterseiten | 0 | Spinnmilben (mechanisch) |
| Kupferkalkbrueher (Bordelaiser Mischung) | biological/chemical | Kupfersulfat + Kalk | 0.5% Sprueher; max. 6 kg Cu/ha/Jahr; OEKO zulässig | 21 | Botrytis, Mehltau (praeventiv) |
| Schwefel-Spritzpulver | chemical | Schwefel | Stauben/Spritzen; bei trockenem Wetter > 18 degC | 14 | Echter Mehltau |
| Fungizid (Thiram-basiert) | chemical | Thiram | Knollenbeize vor Pflanzung (10 min Tauchbad 0.3%) | -- (Bodenbehandlung) | Knollenfaeule (Fusarium, Penicillium) |
| Insektizid-Spray (Pyrethrin) | chemical | Pyrethrin (natuerlich) | Abends sprueher; Bienenschutz beachten | 2--3 | Blattlaeuse, Thripse |
| Schutznetz fuer Wuehlmaeuse | cultural | -- | Pflanzkorb aus Kaninchendraht (Maschenweite 1 cm) | 0 | Wuehlmaus |
| Mulchschicht | cultural | -- | 5--8 cm Rindenmulch oder Strohmulch | 0 | Bodenfeuchtigkeit; reduziert Spritzwasser-Botrytis |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Mehltau (hohe natuuerliche Toleranz verglichen mit anderen Iridaceae) | Krankheit | `resistant_to` |

Hinweis: Tigridia pavonia zeigt generell eine recht gute Robustheit gegen die meisten Blattpilze, solange fuer gute Durchlueftung und trockene Blaetter gesorgt wird. Die groeßte natuerliche Schwaeche liegt bei Knollenfaeule (Feuchte) und Virusinfektionen (Blattlaus-Vektoren).

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Knollen- und Zwiebelpflanzen (Iridaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae: Erbse, Bohne) wegen Stickstoffanreicherung; oder Rueckduengungsbrache |
| Empfohlene Nachfrucht | Blattgemuese (Salat, Spinat -- Schwachzehrer); oder weiterer Sommerblueher (nicht Iridaceae) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Iridaceae auf gleicher Flaeche (Fusarium-Akkumulation im Boden) |

Hinweis: Tigridia teilt Bodenpathogene (insbesondere Fusarium oxysporum) mit anderen Iridaceae (Gladiolen, Iris, Freesia). Fruchfolge-Pausen von 3--4 Jahren pro Flaeche sind wichtig, um Boden-Fusarium-Akkumulation zu vermeiden. Gladiolae sollten sogar 6 Jahre Pause haben -- Tigridia ist weniger empfindlich, aber gleiches Prinzip.

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes (Studentenblume) | Tagetes patula / T. erecta | 0.9 | Nematodenabwehr (Alpha-Terthienyl); Thrips-Teilabwehr; Bestaeuberfoedrung | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.8 | Bestaeuberfoedrung; Schaedlingsabwehr durch aetherische Oele; aehnliche Standortansprueche (Sonne, Drainage) | `compatible_with` |
| Agastache (Duftnessel) | Agastache foeniculum | 0.8 | Bestaeuberfoedrung; Blattlaus-Abwehr; aehnliche Standortansprueche | `compatible_with` |
| Saponaria (Seifenkraut) | Saponaria officinalis | 0.7 | Bodendecker verhindert Bodenverdichtung; niedriger Wuchs ueberdeckt duenne Tigerblumen-Staengel | `compatible_with` |
| Niedriger Ziergras-Horst | Festuca glauca / Stipa tenuissima | 0.7 | Sichtschirmung der duennen Staengel; aehnliche Standortansprueche; kein Naehrstoffkonkurrenz | `compatible_with` |
| Ziersalbei | Salvia nemorosa | 0.8 | Bestaeuberfoedrung; Schaedlingsabwehr; Sonne + gute Drainage = gleiche Ansprueche | `compatible_with` |
| Amaryllis belladonna | Amaryllis belladonna | 0.6 | Beide profitieren von Sommerbewässerung; Amaryllis ist im Sommer aktiv, im Fruehling/Herbst dormant -- komplementaere Gießrhythmen | `compatible_with` |

Hinweis: Tigridia hat relativ schmale, schwertfoermige Blaetter (Wuchsform aehnlich Gladiole). In der Beet-Planung immer in Gruppen (5--10 Knollen) pflanzen und mit buschigeren Nachbarn kombinieren, die die Staengelbasis kaschieren. Die Einzelblueten halten nur einen Tag -- Gruppen aus mehreren Knollen stellen sicher, dass immer mehrere Pflanzen gleichzeitig bluehen.

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Gladiole | Gladiolus hybridus | Gleiche Bodenpathhogene (Fusarium, Thripse); gemeinsamer Befall verstaerkt sich | moderate | `incompatible_with` |
| Schwertlilie (Iris) | Iris germanica | Gleiche Familie, gleiche Pathogene (Fusarium, Iris-Borer); kein Mischkultur-Vorteil | moderate | `incompatible_with` |
| Freesie | Freesia refracta | Iridaceae-Familienmitglied; Pathogen-Naehe; keine Mischkultur-Synergie | low | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathisch hemmend auf viele Begleiter; Wachstumshemmung moeglich | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Iridaceae (eigene Familie) | `shares_pest_risk` | Fusarium oxysporum, Thripse (Frankliniella), Corm Rot | `shares_pest_risk` |
| Liliaceae | `shares_pest_risk` | Zwiebelfaule (Botrytis, Fusarium), Lilienhähnchen moeglich | `shares_pest_risk` |
| Asteraceae | `family_compatible_with` | Tagetes als Begleitpflanze (Nematoden, Bestaeuberfoedrung) | `family_compatible_with` |
| Lamiaceae | `family_compatible_with` | Salbei, Lavendel, Agastache als Begleiter (Bestaeuberfoedrung, Schaedlingsabwehr) | `family_compatible_with` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Tigridia pavonia |
|-----|-------------------|-------------|------------------------------|
| Gladiole | Gladiolus hybridus | Knolle, Schwertblatt, Sommerbluete, gleiche Kultur | Laengere Bluetenstaende; jede Einzelbluete haelt 2--4 Tage; mehr Sortenvielfalt |
| Montbretia / Crocosmia | Crocosmia x crocosmiiflora | Iridaceae, Knollengeophyt, Sommerbluete | Winterhareter (Zone 6--7 mit Mulch); laengere Bluete am Stiel; naturalisierende Massenpflanzung |
| Ixia | Ixia maculata | Iridaceae, aehnliche Knolle, Sommerbluete | Mehr Einzelblueten pro Stiel (5--12); Blueten halten 2--3 Tage; eleganter Wuchs |
| Babiana | Babiana stricta | Iridaceae, Knolle, Fruehsommerbluete | Kompakterer Wuchs (20--30 cm); frueher bluehend (Mai--Juni) |
| Iris (Zwiebel-Iris) | Iris reticulata | Iridaceae, Zwiebel, frueh bluehend | Extrem robust und winterhart; Vorfruehlingsblueher -- ergaenzt Tigridia in Saisonplanung |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,frost_sensitivity,nutrient_demand_level,green_manure_suitable,pruning_type,pruning_months,bloom_months,sowing_indoor_weeks_before_last_frost,sowing_outdoor_after_last_frost_days,direct_sow_months,traits
Tigridia pavonia,"Pfauenblume;Tigerblume;Tiger Flower;Mexican Shell Flower;Peacock Flower;Jockey's Cap Lily",Iridaceae,Tigridia,perennial,day_neutral,herb,corm,"7a;7b;8a;8b;9a;9b;10a;10b",0.0,"Mexiko;Guatemala;Kolumbien;Kiefer-Eichenwald 2000-3000m",yes,5,20,75,30,15,limited,yes,false,false,tender,light_feeder,false,after_harvest,"9;10","7;8;9",6,0,"5;6","ornamental;bee_friendly"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
'Aurea',Tigridia pavonia,--,--,"ornamental;yellow_flowers",90,--,open_pollinated
'Lilacea',Tigridia pavonia,--,--,"ornamental;purple_flowers",90,--,open_pollinated
'Canariensis',Tigridia pavonia,--,--,"ornamental;pink_yellow_flowers",90,--,open_pollinated
'Alba',Tigridia pavonia,--,--,"ornamental;white_flowers",90,--,open_pollinated
'Speciosa',Tigridia pavonia,--,--,"ornamental;red_flowers",90,--,open_pollinated
```

---

## Quellenverzeichnis

1. Wikipedia -- Tigridia pavonia: [https://en.wikipedia.org/wiki/Tigridia_pavonia](https://en.wikipedia.org/wiki/Tigridia_pavonia) — Taxonomie, Heimat, Botanik, historische Verwendung
2. Pacific Bulb Society -- Tigridia pavonia: [https://www.pacificbulbsociety.org/pbswiki/index.php/Tigridia_pavonia](https://www.pacificbulbsociety.org/pbswiki/index.php/Tigridia_pavonia) — Vermehrung, Keimung, Knollenentwicklung
3. Gardeners Path -- Grow Tiger Flowers: [https://gardenerspath.com/plants/flowers/grow-tiger-flowers/](https://gardenerspath.com/plants/flowers/grow-tiger-flowers/) — Anbauanleitung, Pflanztiefe, Schaedlinge
4. Gardening Know How -- Tiger Flower: [https://www.gardeningknowhow.com/ornamental/bulbs/tiger-flower/growing-tiger-flowers.htm](https://www.gardeningknowhow.com/ornamental/bulbs/tiger-flower/growing-tiger-flowers.htm) — Pflegehinweise, Ueberwinterung, Duengung
5. Gardenmarkt.de -- Tigerblume Sorten und Pflege: [https://www.gardenmarkt.de/de/news/tigerblume-tigridia-pavonia-sorten-einpflanzen-und-pflege.html](https://www.gardenmarkt.de/de/news/tigerblume-tigridia-pavonia-sorten-einpflanzen-und-pflege.html) — Pflanztermine Mitteleuropa, Duengung, Gießen
6. Hortica.de -- Tigerblume Pflege A-Z: [https://hortica.de/pflanzen/tigerblumen/](https://hortica.de/pflanzen/tigerblumen/) — Jahreszeitliche Pflege, Ueberwinterung
7. Floragard -- Tigerblume: [https://www.floragard.de/de-de/pflanzeninfothek/pflanze/zwiebel-und-knollenpflanzen/tigerblume](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/zwiebel-und-knollenpflanzen/tigerblume) — Substrat, Topfkultur
8. PFAF Plant Database -- Tigridia pavonia: [https://pfaf.org/User/plant.aspx?latinname=Tigridia+pavonia](https://pfaf.org/User/plant.aspx?latinname=Tigridia+pavonia) — Essbare Teile, Standort, Bodenansprueche
9. Gardenia.net -- Tigridia pavonia Tiger Flower: [https://www.gardenia.net/genus/tigridia-pavonia-tiger-flower](https://www.gardenia.net/genus/tigridia-pavonia-tiger-flower) — Ueberblick Sorten (Aurea, Lilacea, Canariensis)
10. NC State Extension -- Tigridia: [https://plants.ces.ncsu.edu/plants/tigridia/](https://plants.ces.ncsu.edu/plants/tigridia/) — Mischkultur-Partner, botanische Klassifikation
11. plantcaretoday.com -- Mexican Tiger Flower: [https://plantcaretoday.com/mexican-tiger-flower-care-tigridia.html](https://plantcaretoday.com/mexican-tiger-flower-care-tigridia.html) — Schaedlinge, Behandlungen
12. procvetok.com -- Tigridiya Knollenentwicklung: [https://procvetok.com/en/plants/lukovichnye-rasteniya-tigridiya/](https://procvetok.com/en/plants/lukovichnye-rasteniya-tigridiya/) — Knolle-Entwicklungszyklus, Duengungsplan
13. harvesttotable.com -- Grow Tigridia: [https://harvesttotable.com/how-to-grow-tigridia/](https://harvesttotable.com/how-to-grow-tigridia/) — NPK-Empfehlungen, Bluehfoerderung
14. highcountrygardens.com -- Growing Tigridia: [https://www.highcountrygardens.com/content/gardening/growing-tigridia-tiger-flowersmexican-shell-flower](https://www.highcountrygardens.com/content/gardening/growing-tigridia-tiger-flowersmexican-shell-flower) — USDA-Zone, Mischkultur
