# Erdbeere -- Fragaria x ananassa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** PFAF, NC State Extension, Haifa Group, OSU Extension, Plantura, Koppert, fryd.app, LfL Bayern, ASPCA, Greenway Biotech, Science in Hydroponics

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Fragaria x ananassa | `species.scientific_name` |
| Volksnamen (DE/EN) | Erdbeere; Gartenerdbeere; Strawberry; Garden Strawberry | `species.common_names` |
| Familie | Rosaceae | `species.family` -> `botanical_families.name` |
| Gattung | Fragaria | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | groundcover | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (sortenabhaengig: June-bearing = short_day, Everbearing/Day-neutral = day_neutral) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Pflanze winterhart bis ca. -15 bis -20 degC (sortenabhaengig). Blueten frostempfindlich -- Spaetfroeste ab -2 degC schaedigen offene Blueten. Wurzelstock uebersteht mitteleuropaeische Winter mit Mulchschutz zuverlaessig. Wirtschaftliche Nutzung 3--4 Jahre, danach Neupflanzung empfohlen. | `species.hardiness_detail` |
| Heimat | Hybride -- entstanden im 18. Jahrhundert in Europa aus Kreuzung von Fragaria virginiana (Nordamerika) und Fragaria chiloensis (Suedamerika/Chile) | `species.native_habitat` |
| Allelopathie-Score | -0.4 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

Hinweis: Erdbeeren sind oktoploid (8N = 56 Chromosomen). Der Allelopathie-Score ist negativ, da Erdbeeren phenolische Saeuren (p-Hydroxybenzoeaesure, Ferulasaeure, Zimtsaeure, p-Cumarsaeure) ueber Wurzelausscheidungen abgeben, die bei Nachbau auf gleicher Flaeche (Replant-Problem/Bodenmuedigkeit) das eigene Wachstum hemmen (Autotoxizitaet).

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10--12 (Aussaat Januar--Februar fuer Ernte im selben Jahr, nur bei Samenanzucht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (Direktsaat unueblich, Pflanzung von Jungpflanzen/Auslaeufern bevorzugt) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | -- (nicht empfohlen) | `species.direct_sow_months` |
| Erntemonate | 5; 6; 7 (einmaltragend); 5; 6; 7; 8; 9; 10 (immertragend) | `species.harvest_months` |
| Bluetemonate | 4; 5; 6 (einmaltragend); 4; 5; 6; 7; 8; 9 (immertragend) | `species.bloom_months` |

Hinweis: Die gaengigste Vermehrung erfolgt vegetativ ueber Auslaeufer (Runner), nicht ueber Samen. Pflanzzeit fuer Frigo-Pflanzen: April--Mai. Pflanzzeit fuer Gruenpflanzen/Topfpflanzen: Juli--August (fuer Ernte im Folgejahr).

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset; division; seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Vermehrung ueber Auslaeufer (Runner/Offset) ist die Standardmethode -- genetisch identische Klone. Die Mutterpflanze bildet im Sommer Auslaeufer mit Tochterpflanzen, die bei Bodenkontakt bewurzeln. Kronenteilung (Division) ist moeglich bei mehrjährigen Pflanzen mit mehreren Kronen, jedoch weniger gaengig. Saatgut-Vermehrung ist bei F. x ananassa unzuverlaessig, da Hybridsorten nicht samenecht fallen. Ausnahme: Spezielle samenechte Sorten wie 'Alexandria' (Walderdbeere F. vesca).

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (keine) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Insektenbestaeubung, Pollen kaum in der Luft) | `species.allergen_info.pollen_allergen` |
| Nahrungsmittelallergen | true (OAS bei Birkenpollenallergikern durch Kreuzreaktion Fra a 1 / Bet v 1 Homolog in Erdbeerfruechten moeglich) | `species.allergen_info.food_allergen` |

Quelle: ASPCA Animal Poison Control listet Fragaria x ananassa als ungiftig fuer Katzen, Hunde und Pferde. Fruechte, Blaetter und Auslaeufer sind unbedenklich. Bei uebermassigem Verzehr durch Haustiere sind leichte Magen-Darm-Beschwerden moeglich.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | after_harvest | `species.pruning_type` |
| Rueckschnitt-Monate | 7; 8 | `species.pruning_months` |

Hinweis: Nach der letzten Ernte (Juli/August bei einmaltragenden Sorten) werden alte, kranke und verfaerbte Blaetter bodennah abgeschnitten. Das Herz (Vegetationspunkt) darf NICHT verletzt werden. Auslaeufer, die nicht zur Vermehrung genutzt werden, konsequent entfernen -- sie kosten die Mutterpflanze Kraft und reduzieren den Ertrag im Folgejahr. Bei immertragenden Sorten erfolgt der Rueckschnitt erst im Spaetherbst (Oktober/November).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--5 (pro Pflanze) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 15--30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--45 (mit Auslaeufern) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25--35 (Reihenabstand 60--80 cm) | `species.spacing_cm` |
| Indoor-Anbau | limited (nur mit Zusatzbelichtung und manueller Bestaeubung; Blueteninitiierung benoetigt Kurztagbedingungen) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Ampeltoepfe, Erdbeertuerme, Balkonkaesten -- ideal fuer haengende/immertragende Sorten) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (Fruehkultur moeglich, verlaengerte Saison, Schutz vor Grauschimmel) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leicht saure (pH 5.5--6.5), humose Erde mit gutem Wasserhaltvermögen. Drainage am Topfboden wichtig. Ampeltoepfe/Erdbeertuerme ideal fuer haengende Sorten. Stroh-Mulch verhindert Fruchtfaeule. | -- |

**Hinweis:** Erdbeeren eignen sich ausgezeichnet fuer Topf- und Balkonkultur. Immertragende Sorten sind fuer Kuebel besonders empfehlenswert (laengere Ernteperiode). Hänge-Erdbeeren in Ampeln sind dekorativ und platzsparend. Im Topf ist gleichmaessige Wasserversorgung besonders wichtig -- Austrocknung fuehrt zu Missbildungen und kleinen Fruechten. Im Winter Toepfe frostgeschuetzt stellen oder mit Vlies umwickeln.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung/Etablierung (germination) | 14--30 (Samen) / 7--14 (Auslaeufer/Pflanzung) | 1 | false | false | low |
| Vegetativ (vegetative) | 60--120 | 2 | false | false | medium |
| Bluete (flowering) | 14--28 | 3 | false | false | low |
| Fruchtreife (ripening) | 21--35 | 4 | false | true | medium |
| Erholungsphase (recovery) | 30--60 | 5 | false | false | medium |
| Winterruhe (dormancy) | 60--120 | 6 | false | false | high |

Hinweis: Anders als einjaehrige Kulturen durchlaufen Erdbeeren einen zyklischen Phasenverlauf (perennial). Nach der Winterruhe beginnt der Zyklus erneut bei der vegetativen Phase. Immertragend Sorten koennen Bluete/Fruchtreife parallel zur vegetativen Phase durchlaufen. Die Erholungsphase nach der Ernte ist entscheidend fuer die Bluetenanlage des Folgejahres (Blueteninitiierung bei Kurztagbedingungen im Herbst).

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung/Etablierung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 6--10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70--80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75--85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht halten) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Bei Samenkeimung ist eine Kaeltestratifikation (4 Wochen bei 2--5 degC im feuchten Substrat) empfohlen, um die Keimrate zu erhoehen. Keimzeit bei Saatgut 14--30 Tage.

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: In der vegetativen Phase ist eine Tag-Nacht-Temperaturdifferenz (DIF) von mindestens 4--6 degC vorteilhaft fuer kompakten Wuchs. Erhoehte PPFD-Werte (bis 450 umol/m2/s) steigern linear die Kronendurchmesser und Biomasse.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--450 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 17--25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 800--1200 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Temperaturen ueber 30 degC Tag oder ueber 25 degC Nacht beeintraechtigen die Bestaeubung und den Fruchtansatz. Spaetfroeste unter -2 degC schaedigen offene Blueten irreversibel (Schwarze Mitte). Bestaeubung durch Insekten (v.a. Bienen, Hummeln) ist fuer gleichmaessige Fruchtform essenziell -- im Gewaechshaus ggf. Hummeln einsetzen oder manuell bestaeubung.

#### Phase: Fruchtreife (ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--450 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 17--25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Niedrigere Luftfeuchtigkeit (<65%) in der Fruchtreife reduziert Botrytis-Risiko erheblich. Strohunterlage unter den Fruechten verhindert Erdkontakt und damit Lederbeeren-/Bodenpilzinfektionen. Ernte nur bei Trockenheit, nicht bei Nass/Morgentau.

#### Phase: Erholungsphase (recovery)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 (natuerliche Kurztagbedingungen foerdern Blueteninitiierung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Blueteninitiierung bei einmaltragenden Sorten erfolgt unter Kurztagbedingungen (<14 Stunden Licht) und moderaten Temperaturen im Spaetsommer/Herbst. Duengung in dieser Phase ist entscheidend fuer den Ertrag des naechsten Jahres.

#### Phase: Winterruhe (dormancy)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Freiland: natuerliches Winterlicht) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (8--10 Stunden) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -5--5 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -15--0 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- (nicht steuerungsrelevant) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- (nicht steuerungsrelevant) | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (nicht steuerungsrelevant) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | -- (natuerlicher Niederschlag; bei Kuebel: alle 14--21 Tage pruefen ob Substrat nicht komplett austrocknet) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | -- (minimal) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Erdbeeren benoetigen eine Kaelteperiode (Vernalisation) von mindestens 200--400 Stunden unter 7 degC fuer optimale Bluetenentwicklung im Fruehjahr. Ohne ausreichende Kaelteexposition (z.B. in Tropenregionen oder ganzjaehrigem Indoor-Anbau) ist der Ertrag deutlich reduziert. Frigo-Pflanzen (bei -1.5 degC gelagerte Jungpflanzen) umgehen dieses Problem.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung/Etablierung | 0-0-0 | 0.0 | 5.8--6.2 | -- | -- | -- | -- |
| Vegetativ | 3-1-3 | 0.8--1.2 | 5.5--6.0 | 120 | 40 | 30 | 3 |
| Bluete | 2-2-4 | 1.0--1.4 | 5.5--6.0 | 140 | 50 | 40 | 3 |
| Fruchtreife | 1-2-5 | 1.2--1.8 | 5.5--6.2 | 160 | 50 | 40 | 5 |
| Erholungsphase | 2-3-3 | 0.8--1.2 | 5.8--6.2 | 120 | 40 | 30 | 2 |
| Winterruhe | 0-0-0 | 0.0 | -- | -- | -- | -- | -- |

Hinweis: Erdbeeren sind kaliumliebend -- K:N-Verhaeltnis ab Bluetenphase mindestens 1.5:1, in der Fruchtreife 2:1 bis 3:1 fuer optimalen Geschmack und Festigkeit. Optimales K:Ca-Verhaeltnis 1:1 bis 1.4:1, K:Mg-Verhaeltnis ca. 4:1. EC-Werte ueber 2.0 mS reduzieren die Fruchtgroesse, verbessern aber den Geschmack (Brix-Wert) -- Abwaegung je nach Ziel. Erdbeeren bevorzugen leicht sauren pH (5.5--6.5, optimal 5.8--6.0).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung/Etablierung -> Vegetativ | time_based | 14--30 Tage (Samen) / 7--14 Tage (Pflanzung) | Neue Blaetter sichtbar, Wurzeln etabliert |
| Vegetativ -> Bluete | gdd_based / event_based | GDD ~250--350 (Basis 5 degC) | Erste Bluetenknospen sichtbar, abhaengig von Sortentyp und Vernalisation |
| Bluete -> Fruchtreife | event_based | 21--35 Tage nach Bestaeubung | Fruechte gebildet, Farbumschlag beginnt (weiss -> rosa -> rot) |
| Fruchtreife -> Erholungsphase | event_based | nach letzter Ernte | Keine weiteren Fruechte vorhanden, Pflanze bildet Auslaeufer |
| Erholungsphase -> Winterruhe | conditional | Kurztagbedingungen + Temperatur < 10 degC | Blaetter beginnen zu vergilben, Wachstum stellt ein |
| Winterruhe -> Vegetativ | conditional | Vernalisation abgeschlossen (>200 h < 7 degC) + Temperatur steigt > 10 degC | Neuer Blatttrieb im Fruehjahr |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Vegetativ |
| Aqua Flores A | Canna | base | 4-0-3 | 0.16 | 3 | Bluete, Frucht |
| Aqua Flores B | Canna | base | 0-4-5 | 0.14 | 4 | Bluete, Frucht |
| Strawberry Fertilizer 8-12-32 | Greenway Biotech | specialty | 8-12-32 | ~0.12 | 3 | Bluete, Frucht (Solo-Duenger) |
| Hakaphos Rot 18-18-18 | COMPO Expert | base | 18-18-18 | ~0.15 | 3 | Vegetativ |
| PK 13-14 | Canna | booster | 0-13-14 | 0.10 | 5 | Fruchtreife (2--3 Wochen) |
| Kaliumsulfat (Patentkali) | div. | supplement | 0-0-30 (+Mg 10%, S 17%) | ~0.10 | 5 | Bluete, Frucht |

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 3--5 L/m2 | Fruehjahr (Maerz/April) + nach Ernte (August) | alle |
| Hornspane | Oscorna / div. | organisch (N-Langzeit) | 50--80 g/m2 | Fruehjahr (Maerz) | medium_feeder |
| Beerenduenger (organisch) | Plantura / COMPO BIO | organisch (NPK 5-2-8) | 100--150 g/m2 | Fruehjahr + nach Ernte | medium_feeder |
| Beinwell-Jauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 1 L/m2 | Mai--Juli, alle 14 Tage | medium_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:20 verduennt, 1 L/m2 | April--Juni (nur vegetativ) | medium_feeder |
| Holzasche (kalireich) | Eigenerzeugung | organisch (K-Supplement) | 50--100 g/m2 | Fruehjahr | medium_feeder |

Hinweis: Erdbeeren sind empfindlich gegenueber Ueberduengung, insbesondere mit Stickstoff -- zu viel N foerdert Blattwachstum auf Kosten der Fruchtbildung, erhoehte Botrytis-Anfaelligkeit und weiche, geschmackarme Fruechte. Frischer Mist ist ungeeignet (Verbrennung, Pilzinfektionen). Kalibetonte Duengung ab Bluetenbeginn ist entscheidend fuer Fruchtqualitaet.

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Erdbeere Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | PK 13-14 (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|-----------------|----------|
| 1--2 | Etablierung | 0.0--0.3 | 5.8 | -- | -- | -- | -- | Nur Klarwasser, Wurzeletablierung |
| 3--5 | Vegetativ frueh | 0.6--0.8 | 5.8 | 0.3 | 0.5 (Vega A) | 0.5 (Vega B) | -- | EC langsam steigern |
| 6--10 | Vegetativ | 0.8--1.2 | 5.8--6.0 | 0.5 | 1.0 (Vega A) | 1.0 (Vega B) | -- | Vega A+B, ausgewogener N-Anteil |
| 11--13 | Bluete | 1.0--1.4 | 5.8--6.0 | 0.5 | 1.0 (Flores A) | 1.2 (Flores B) | -- | Umstellung auf Flores A+B, K erhoehen |
| 14--18 | Fruchtreife | 1.2--1.8 | 5.8--6.0 | 0.5 | 1.0 | 1.2 | 0.3 | PK-Booster fuer Fruchtqualitaet |
| 19--20 | Erholung | 0.6--0.8 | 5.8 | 0.3 | 0.5 | 0.5 | -- | EC reduzieren, Nachernte-Duengung |
| 21+ | Winterruhe | 0.0 | -- | -- | -- | -- | -- | Keine Duengung waehrend Dormanz |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium -- verhindert Ca-P-Ausfaellungen bei spaeterer Base-B-Zugabe)
3. Base A -- Aqua Vega A / Aqua Flores A (Calcium + Mikronaehrstoffe)
4. Base B -- Aqua Vega B / Aqua Flores B (Phosphor + Schwefel + Magnesium)
5. PK 13-14 Booster (nur in Fruchtreifephase)
6. Kaliumsulfat (falls ergaenzend, aufloesung pruefen)
7. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **EC-Sensibilitaet:** Erdbeeren sind salzempfindlicher als Tomaten. EC ueber 2.0 mS kann zu Wurzelschaeden und Ertragsreduktion fuehren. Typischer Zielbereich 1.0--1.5 mS fuer Hydro, maximal 1.8 mS in der Fruchtreife.
- **Kalium ist qualitaetsbestimmend:** K:N-Verhaeltnis ab Bluetephase erhoehen. Hoher Kaliumanteil verbessert Fruchtfestigkeit, Haltbarkeit, Zuckergehalt (Brix) und Aromaintensitaet.
- **Phosphor zur Blueteninitiierung:** Erhoehter P-Bedarf in der Erholungsphase nach der Ernte -- Phosphor foerdert die Anlage neuer Bluetenknospen fuer das Folgejahr.
- **Calcium-Mangel:** Aeussert sich als Blattrandnekrose und verformte, weiche Fruechte. CalMag-Supplementierung insbesondere bei Hydrokultur und Coco-Substrat essenziell.
- **Organische Freiland-Duengung:** Hauptduengung im August/September nach der Ernte (3--5 L/m2 Kompost + 100 g/m2 Beerenduenger). Fruehjahrsgabe (Maerz) mit 50 g/m2 Hornspane + Kaliumsulfat. Waehrend der Fruchtreife keine stickstoffbetonte Duengung mehr.
- **Brix-Optimierung:** Leichter Trockenstress (reduzierte Bewaesserung um 20%) in der Endphase der Fruchtreife erhoht den Zuckergehalt, aber auf Kosten der Fruchtgroesse.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 (minimal, nur Kuebelpflanzen bei Trockenheit) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Leicht kalkempfindlich, pH 5.5--6.5. Morgens giessen, nicht ueber Blaetter/Fruechte giessen (Botrytis-Risiko). Tropfbewaesserung ideal. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14--21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (Kuebel: jaehrlich frisches Substrat oder alle 3 Jahre neue Pflanzen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | Saatgut/Pflanzen bestellen | Sorten auswaehlen, Frigo-Pflanzen oder Gruenpflanzen bestellen | niedrig |
| Feb | Samenaussaat (optional) | Aussaat samenechter Sorten bei 18--20 degC unter Kunstlicht mit Kaeltestratifikation | niedrig |
| Marz | Beete vorbereiten | Mulch entfernen, Kompost einarbeiten (3--5 L/m2), Hornspane streuen (50 g/m2), altes Laub abschneiden | hoch |
| Apr | Fruehjahrs-Pflege | Erdbeerflies bereitlegen bei Spaetfrostgefahr, Unkraut jaeten, Stroh unterlegen | hoch |
| Mai | Bluetenpflege + Frostschutz | Bei Spaetfrost Vlies/Folie abdecken, Auslaeufer entfernen, Bestaeubung unterstuetzen | hoch |
| Jun | Ernte (fruehtragend) | Taeglich ernten bei Trockenheit, morgens pfluecken, vollreife Fruechte mit Kelch abdrehen | hoch |
| Jul | Haupternte + Nachernte-Pflege | Ernte abschliessen (einmaltragend), sofortiger Rueckschnitt alter Blaetter, Duengung mit Kompost + Beerenduenger | hoch |
| Aug | Nachernte-Duengung + Neupflanzung | Hauptduengung (3--5 L/m2 Kompost + 100 g/m2 Beerenduenger), neue Gruenpflanzen setzen, Auslaeufer fuer Vermehrung bewurzeln | hoch |
| Sep | Auslaeufer-Vermehrung | Bewurzelte Auslaeufer abtrennen und verpflanzen, Unkraut entfernen | mittel |
| Okt | Wintervorbereitung | Letzte Duengung bei immertragenden Sorten, abgestorbene Blaetter entfernen | mittel |
| Nov | Winterschutz ausbringen | Stroh- oder Laubschicht (5--10 cm) um Pflanzen verteilen, Vlies bei Kahlfroeesten | mittel |
| Dez | Ruhe | Kontrolle Winterschutz, ggf. erneuern, sonst keine Massnahmen | niedrig |

### 4.3 Ueberwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Fruehlings-Massnahme | uncover | `overwintering_profiles.spring_action` |
| Fruehlings-Massnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (degC) | -20 (Freiland) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (degC) | 5 (Freiland) | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | -- (Freiland, nicht steuerbar) | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | minimal (nur Kuebel/Balkon, Substrat darf nicht vollstaendig austrocknen) | `overwintering_profiles.winter_watering` |

Hinweis: Erdbeerpflanzen sind grundsaetzlich winterhart, benoetigen aber Schutz gegen Kahlfroeste (Frost ohne Schneedecke). 5--10 cm Stroh-, Laub- oder Reisigmulch schuetzt Wurzeln und Krone. Vlies (17 g/m2) bei Temperaturen unter -10 degC ergaenzend. Folie vermeiden (Staunasse, Faeulunis). Kuebelpflanzen an geschuetzte Hauswand stellen und Topf mit Noppenfolie umwickeln.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Erdbeerbluetenstecher | Anthonomus rubi | Abgeknickte, vertrocknete Bluetenknospen, Eiablage in Knospe | flower | flowering | easy |
| Spinnmilbe (Gemeine Spinnmilbe) | Tetranychus urticae | Silbrig-gelbe Punkte auf Blattoberseite, feine Gespinste auf Blattunterseite | leaf | vegetative, flowering, ripening | medium |
| Erdbeermilbe (Weichhautmilbe) | Phytonemus pallidus | Gekraeuselte, verformte Herzblaetter, verkuemmerter Wuchs, braune Blattraender | leaf | vegetative, flowering | difficult |
| Blattlaeuse (Aphids) | Chaetosiphon fragaefolii, Myzus persicae | Blattkraeuseln, Honigtau, Virusvektor (Erdbeer-Mildes-Gulb-Virus) | leaf, flower | vegetative, flowering | easy |
| Dickmaulruessler | Otiorhynchus sulcatus | Halbkreisfoermiger Buchtfrass an Blattraendern (adulte Kaefer), Larven fressen an Wurzeln (fataler Schaden) | leaf, root | alle | medium (Buchtfrass), difficult (Larven) |
| Nacktschnecken | Arion vulgaris, Deroceras reticulatum | Lochfrass an Fruechten und Blaettern, Schleimspuren | fruit, leaf | ripening | easy |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Flecken auf Blaettern, verkrueppelte Blueten, Bronzierung | leaf, flower, fruit | flowering, ripening | medium |
| Erdbeer-Stengel-Nematode | Ditylenchus dipsaci | Aufgedunsene, verzerrte Blattstiele, Kuemmerwuchs | stem, leaf | vegetative | difficult |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel (Grey Mold / Botrytis) | fungal | Grauer pelziger Sporenrasen auf Fruechten, Blueten, Blaettern. Fruechte werden weich und matschig. | high_humidity, poor_airflow, rain | 2--5 | flowering, ripening |
| Lederbeerenfaeule (Leather Rot) | fungal (Oomycete) | Fruechte werden braun-lederig, gummiartig fest, bitterer Geschmack, typischer Geruch | rain_splash, soil_contact, waterlogging | 3--7 | ripening |
| Rhizomfaeule (Crown Rot) | fungal (Oomycete) | Welken einzelner Blaetter, braune Verfaerbung im Rhizom-Querschnitt, ploetzliches Absterben | waterlogging, contaminated_planting_material | 7--21 | vegetative, flowering |
| Verticillium-Welke (Verticillium Wilt) | fungal | Einseitige Blattwelke, gelb-braune Verfaerbung, reduzierter Wuchs, braune Leitbuendel | soil_contamination, warm_soil | 14--28 | vegetative, flowering |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser Belag auf Blattunterseite (untyisch: Unterseite!), Blattraender rollen sich nach oben, rosa Verfaerbung befallener Fruechte | dry_leaves, warm_days_cool_nights, poor_airflow | 5--10 | vegetative, flowering, ripening |
| Rotfleckenkrankheit (Leaf Scorch) | fungal | Dunkelrote bis purpurne Flecken auf Blaettern, bei starkem Befall Blattabsterben | high_humidity, rain_splash | 7--14 | vegetative, recovery |
| Weissfleckenkrankheit (Leaf Spot) | fungal | Kleine runde Flecken mit weissem Zentrum und rotem Rand auf Blaettern | high_humidity, rain_splash | 7--14 | vegetative, recovery |
| Erdbeer-Mildes-Gulb-Virus (Strawberry Mild Yellow Edge Virus) | viral | Blattvergilbung an Raendern, Zwergwuchs, Ertragsreduktion | aphid_transmission | 14--28 | alle |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |
| Amblyseius californicus | Spinnmilbe (praeventiv, auch bei niedrigem Befall) | 5--10 | 14--28 |
| Amblyseius cucumeris | Thripse, Erdbeermilbe | 50--100 (Streutuetenverfahren) | 14--21 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Aphidius colemani | Blattlaeuse (Schlupfwespe) | 1--3 | 14--21 |
| Steinernema kraussei (Nematode) | Dickmaulruessler-Larven | 500.000/m2 | 14--21 |
| Heterorhabditis bacteriophora (Nematode) | Dickmaulruessler-Larven | 500.000/m2 | 14--21 |
| Bombus terrestris (Erdhummel) | -- (Bestaeubung) | 1 Volk / 500--1000 m2 (Gewaechshaus) | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Spinnmilbe, Thripse |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau, Botrytis (praeventiv) |
| Netzschwefel | chemical | Schwefel | Spruehung 0.3--0.5%, alle 10--14 Tage | 7 | Echter Mehltau, Spinnmilbe |
| Kupferpraeparat (Kupferoxychlorid) | chemical | Kupferhydroxid | Spritzung praeventiv, vor der Bluete | 14 | Rotfleckenkrankheit, Weissfleckenkrankheit |
| Bacillus subtilis (z.B. Serenade ASO) | biological | Bacillus subtilis Lipopeptide | Spritzung alle 7--10 Tage | 0 | Botrytis, Mehltau |
| Stroh-Mulch | cultural | -- | 5--8 cm Stroh um Pflanzen und unter Fruechte | 0 | Lederbeerenfaeule (Spritzwasser-Schutz), Unkraut |
| Befallene Fruechte entfernen | cultural | -- | Taeglich bei Erntedurchgang | 0 | Botrytis-Sporenreduktion, Sekundaerinfektion verhindern |
| Schneckenkorn (Eisen-III-Phosphat) | biological | Eisen-III-Phosphat | 5 g/m2, nach Regen erneuern | 0 | Nacktschnecken |
| Milch-Wasser-Spritzung | cultural | Milchsaeurebakterien | 1:4 Milch:Wasser, alle 5--7 Tage | 0 | Echter Mehltau (Hausmittel) |

### 5.5 Resistenzen der Art

Fragaria x ananassa als Art hat keine ausgepraegten Resistenzen. Resistenzen werden ueber Sortenzuechtung erreicht.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Verticillium dahliae | Krankheit | Sorten wie 'Elsanta', 'Malwina' (teilweise), 'Honeoye' | `resistant_to` |
| Phytophthora cactorum (Rhizomfaeule) | Krankheit | Sorten wie 'Elsanta' (mittlere Toleranz), resistente Unterlagen | `resistant_to` |
| Botrytis cinerea | Krankheit | Keine vollstaendige Resistenz, aber Toleranz bei 'Malwina', 'Florence' | `resistant_to` |
| Podosphaera aphanis (Mehltau) | Krankheit | Sorten wie 'Malwina', 'Florence' (geringe Anfaelligkeit) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Rosengewaechse (Rosaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) -- Stickstoff-Fixierung, gute Bodenstruktur; Salat/Spinat (Schwachzehrer) -- keine gemeinsamen Krankheiten |
| Empfohlene Nachfrucht | Gruenduengung (Phacelia, Senf) -- Bodenregeneration; Huelsenfruechte (Fabaceae) -- N-Fixierung; Lauch/Zwiebel (Alliaceae) -- keine gemeinsamen Krankheiten |
| Anbaupause (Jahre) | 3--4 Jahre fuer Erdbeeren und andere Rosaceae (Himbeere, Brombeere, Rose) auf gleicher Flaeche (Verticillium, Phytophthora, Bodenmuedigkeit/Autotoxizitaet) |

Hinweis: Erdbeeren sind stark selbstunvertraeglich (Replant Disease). Phenolische Saeuren aus Wurzelausscheidungen hemmen das Wachstum nachfolgender Erdbeerpflanzen. Kartoffeln, Tomaten und andere Solanaceae sind als Vorfrucht ungeeignet, da sie Verticillium-Befall foerdern.

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.9 | Pilzkrankheiten-Abwehr durch Allicin, Verticillium-Reduktion, Erdbeerbluetenstecher-Abschreckung | `compatible_with` |
| Zwiebel | Allium cepa | 0.8 | Pilzabwehr, Schneckenabschreckung, gute Raumnutzung | `compatible_with` |
| Buschbohne | Phaseolus vulgaris | 0.9 | Stickstoff-Fixierung im Boden, keine gemeinsamen Krankheiten, gute Raumnutzung | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes patula | 0.9 | Nematoden-Abwehr durch Thiophene, Schnecken-Abschreckung, Bestauber anlocken | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Bodenbeschattung, keine Naehrstoffkonkurrenz (Schwachzehrer), schnelle Ernte | `compatible_with` |
| Spinat | Spinacia oleracea | 0.8 | Bodenbeschattung, Saponine foerdern Naehrstoffverfuegbarkeit | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.8 | Pilzabwehr, Bestauber anlocken, dekorativer Beetrand | `compatible_with` |
| Borretsch | Borago officinalis | 0.8 | Bestauber anlocken, Spurenelemente aus tieferen Bodenschichten, traditionelle Begleitpflanze | `compatible_with` |
| Radieschen | Raphanus sativus | 0.7 | Schnelle Ernte, Markierung der Reihen, lockert Boden | `compatible_with` |
| Ringelblume | Calendula officinalis | 0.7 | Nematoden-Abwehr, Bestauber, Bodenverbesserung | `compatible_with` |
| Stiefmuetterchen | Viola x wittrockiana | 0.7 | Locken Bestauber an, Bodenbedeckung im Fruehjahr, keine gemeinsamen Krankheiten | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.7 | Verschiedene Pflanzenfamilien, Petersilie lockt Nuetzlinge an, gute Bodenbedeckung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Verticillium-Wirt -- uebertraegt Verticillium dahliae auf Erdbeeren; gemeinsame Phytophthora-Anfaelligkeit | severe | `incompatible_with` |
| Kohl (alle Arten) | Brassica oleracea | Lockt Erdfloeche und Kohlfliege an, starke Naehrstoffkonkurrenz (Starkzehrer), unterschiedliche pH-Ansprueche | moderate | `incompatible_with` |
| Topinambur | Helianthus tuberosus | Extrem invasives Wurzelwachstum, ueberwuchert Erdbeeren, Naehrstoffentzug | severe | `incompatible_with` |
| Liebstoeckel | Levisticum officinale | Wachstumshemmende Wurzelausscheidungen (allelopathisch) | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung durch Anethole/Fenchon, hemmt Fruchtbildung | moderate | `incompatible_with` |
| Tomate | Solanum lycopersicum | Verticillium-Wirt, Phytophthora-Risiko, starke Naehrstoffkonkurrenz (Starkzehrer) | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Rosaceae (mit sich selbst) | `shares_pest_risk` | Verticillium, Phytophthora, Dickmaulruessler, Bodenmuedigkeit | `shares_pest_risk` |
| Solanaceae | `shares_pest_risk` | Verticillium dahliae, Phytophthora | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Erdbeere |
|-----|-------------------|-------------|------------------------------|
| Walderdbeere | Fragaria vesca | Gleiche Gattung, deutlich kleinere Fruechte, aehnliche Kultur | Robuster, schattenvertraeglicher, weniger krankheitsanfaellig, samenechte Vermehrung, Dauertraeger, aromatischer |
| Monatserdbeere | Fragaria vesca var. semperflorens | Walderdbeere-Variante, immertragende | Kompakter Wuchs, keine Auslaeufer, ideal fuer Toepfe/Balkon, selbstbefruchtend |
| Moschus-Erdbeere | Fragaria moschata | Historische Erdbeerart, groessere Fruechte als Walderdbeere | Intensives Muskataroma, schattenvertraeglicher, kaelteresistenter |
| Himbeere | Rubus idaeus | Gleiche Familie (Rosaceae), aehnliche Standortansprueche | Hoeher wachsend, mehrjaehrig ohne Replant-Problem, anderes Erntezeitfenster |
| Heidelbeere (Kultur-) | Vaccinium corymbosum | Aehnliche Fruchtgroesse und -verwendung | Langlebiger Strauch (15--20 Jahre), weniger Schaedlinge, saurer Boden bevorzugt |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Fragaria x ananassa,Erdbeere;Gartenerdbeere;Strawberry;Garden Strawberry,Rosaceae,Fragaria,perennial,day_neutral,groundcover,fibrous,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b,-0.4,"Hybride, Europa 18. Jh. (F. virginiana x F. chiloensis)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Senga Sengana,Fragaria x ananassa,Reinhold von Sengbusch,1954,june_bearing;high_yield;dark_red;aromatic;frost_hardy,85,botrytis_tolerant,open_pollinated
Elsanta,Fragaria x ananassa,Plant Research International Wageningen,1981,june_bearing;high_yield;firm_fruit;transport_stable,80,verticillium;phytophthora_tolerant,open_pollinated
Korona,Fragaria x ananassa,Plant Research International Wageningen,1972,june_bearing;large_fruit;aromatic;soft_fruit,80,,open_pollinated
Lambada,Fragaria x ananassa,Plant Research International Wageningen,1982,june_bearing;very_sweet;early,75,,open_pollinated
Malwina,Fragaria x ananassa,Peter Stoppel,2010,june_bearing;very_late;firm_fruit;disease_resistant;dark_red,95,mehltau;botrytis_tolerant,open_pollinated
Mieze Schindler,Fragaria x ananassa,Otto Schindler,1925,june_bearing;late;small_fruit;highly_aromatic;female_only;needs_pollinator,90,,open_pollinated
Ostara,Fragaria x ananassa,,1969,everbearing;day_neutral;continuous_fruiting;medium_fruit,70,,open_pollinated
Hummi Gento,Fragaria x ananassa,Hummel,1975,everbearing;climbing_trailing;large_fruit,75,,open_pollinated
Mara des Bois,Fragaria x ananassa,Andre Marionnet,1991,everbearing;day_neutral;walderdbeere_aroma;aromatic,70,,open_pollinated
```

---

## Quellenverzeichnis

1. PFAF (Plants For A Future) -- Fragaria x ananassa: https://pfaf.org/user/Plant.aspx?LatinName=Fragaria+x+ananassa
2. NC State Extension Gardener Plant Toolbox -- Fragaria x ananassa: https://plants.ces.ncsu.edu/plants/fragaria-x-ananassa/
3. ASPCA Animal Poison Control -- Strawberry (ungiftig): https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/strawberry
4. Haifa Group -- Strawberry Crop Guide & Fertilizer Recommendations: https://www.haifa-group.com/crop-guide/vegetables/strawberry-fertilizer/crop-guide-strawberry-1
5. OSU Extension -- Strawberry Nutrient Management: https://catalog.extension.oregonstate.edu/em9234/html
6. UMN Extension -- Strawberry Nutrient Management: https://extension.umn.edu/strawberry-farming/strawberry-nutrient-management
7. Science in Hydroponics -- Comparing Nutrient Solutions for Hydroponic Strawberry Production: https://scienceinhydroponics.com/2025/10/comparing-nutrient-solutions-for-hydroponic-strawberry-production.html
8. Greenway Biotech -- Best Fertilizer for Strawberries: https://www.greenwaybiotech.com/blogs/gardening-articles/best-fertilizer-for-strawberries
9. Koppert Biological Systems -- Erdbeerkultur: https://www.koppertbio.de/kulturpflanzen/obst/erdbeere/
10. LfL Bayern -- Erdbeeren Krankheiten und Schaedlinge: https://www.lfl.bayern.de/ips/kleingarten/135905/index.php
11. Plantura -- Erdbeeren duengen: https://www.plantura.garden/obst/erdbeeren/erdbeeren-duengen
12. Plantura -- Erdbeeren ueberwintern und schneiden: https://www.plantura.garden/obst/erdbeeren/erdbeeren-ueberwintern-und-schneiden
13. fryd.app -- Mischkultur mit Erdbeeren: https://fryd.app/magazin/mischkultur-mit-erdbeeren
14. erdbeerprofi.de -- Krankheiten und Schaedlinge bei Erdbeeren: https://erdbeerprofi.de/tipps-gemuesegarten/krankheiten
15. MDPI Plants -- Growth, Flowering, and Fruit Production of Strawberry 'Albion' in Response to Photoperiod and PPFD: https://www.mdpi.com/2223-7747/12/4/731
16. PMC -- Effects of long-term continuous cropping on soil nematode community and replant problem in strawberry habitat: https://pmc.ncbi.nlm.nih.gov/articles/PMC4978966/
