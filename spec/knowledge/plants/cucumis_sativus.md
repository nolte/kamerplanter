# Salatgurke -- Cucumis sativus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, NCSU Extension, Haifa Group, Cornell University, Gardenia.net, Plantura, fryd.app, Epic Gardening, Gardener's Path, Old Farmer's Almanac, MasterClass

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cucumis sativus | `species.scientific_name` |
| Volksnamen (DE/EN) | Gurke; Salatgurke; Schlangengurke; Einlegegurke; Cucumber; Garden Cucumber; Gherkin | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` -> `botanical_families.name` |
| Gattung | Cucumis | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (fakultativ; die meisten modernen Sorten sind tagneutral; einige Landsorten kurztagsempfindlich) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, stirbt bei Temperaturen unter 5 degC ab. Extrem kaelteempfindlich -- bereits Temperaturen unter 10 degC verursachen Wachstumsstopp und Kaelteschaeden (Blattverfaerbung, reduzierte Fruchtqualitaet). In Mitteleuropa Freiland-Kultur nur Mai--September. | `species.hardiness_detail` |
| Heimat | Suedostasien (Indien, Himalaya-Region) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3--4 (Gurken wachsen schnell, kurze Vorkultur genuegt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (erst nach Bodentemperatur > 15 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy (schnellwuechsig, unkomplizierte Keimung bei Waerme) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 25--30 degC (Waermekeimer, Heizmatte empfohlen)
- Minimale Keimtemperatur: 15 degC (sehr langsam)
- Keimdauer: 3--7 Tage (bei optimaler Temperatur sehr schnell!)
- **Dunkelkeimer** -- Samen 2--3 cm tief in Erde druecken
- Vorkultur: Einzeln in 8--10 cm Toepfe saeen (Gurken vertragen kein Pikieren -- empfindliche Wurzeln)
- Auspflanzen nach Eisheiligen, Pflanzabstand 60--100 cm (je nach Sorte, Rankgitter/Boden)
- Gurken-Samen nie unter 15 degC saeen -- faulen leicht in kalter, nasser Erde

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (Cucurbitacin in Bittergurken kann in hohen Konzentrationen magenreizend sein) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Cucurbitacin (nur in bitteren Fruechten/Wildformen -- moderne Sorten sind cucurbitacinfrei selektiert) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (moderne Kultursorten unbedenklich; bittere Fruechte NICHT essen!) | `species.toxicity.severity` |
| Kontaktallergen | false (Blaetter leicht stachelig/rauh -- mechanische Reizung, keine Allergie) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Cucumis sativus nicht als toxisch. Achtung: Bittere Gurken (Cucurbitacin-haltig) koennen Magen-Darm-Beschwerden verursachen. NIEMALS bitter schmeckende Ziergugewaechse essen -- Cucurbitacin-Vergiftung ist lebensgefaehrlich.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7; 8 | `species.pruning_months` |

Hinweis: Gewaechshaus-Gurken (Schlangengurken) werden an Schnur/Draht gezogen und regelmaessig ausgegeizt: Seitentriebe nach dem 1. Fruchtansatz zurueckschneiden, Haupttrieb an der Rankhilfe hochleiten. Freiland-/Einlegegurken brauchen weniger Schnitt -- nur bodenberuehrende, kranke Blaetter entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in grossen Kuebeln ab 20 L, Rankhilfe noetig; kompakte Sorten bevorzugen) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20--40 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 150--300 (an Rankhilfe; am Boden 30--50 cm hoch, 100--200 cm lang) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60--100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60--100 (an Rankhilfe enger; am Boden weiter) | `species.spacing_cm` |
| Indoor-Anbau | no (extrem hoher Licht- und Platzbedarf, nicht praktikabel) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (grosse Kuebel, Rankhilfe, sonnig + windgeschuetzt; Miniatur-Sorten besser geeignet) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (Schlangengurken/Salatgurken sind klassische Gewaechshauskulturen; optimale Waerme + Feuchtigkeit) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Rankgitter, Schnuere oder Spalier; Bodenkultivierung auch moeglich) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose, wasserhaltende Erde. Tomaten-/Gemuese-Substrat. pH 6.0--6.8. Staunaesse vermeiden trotz hohem Wasserbedarf -- gute Drainage. | -- |

**Hinweis:** Gurken sind waermeliebende Starkzehrer mit hohem Wasserbedarf. Im Gewaechshaus werden Salatgurken (parthenokarpe Sorten -- keine Bestaeubung noetig, kernlos) an Schnueren gezogen. Freiland-Einlegegurken am Boden oder an niedrigem Gitter. Mindestens 6 Stunden direkte Sonne. Hohe Luftfeuchtigkeit foerdert Wachstum, aber auch Mehltau-Risiko.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 3--7 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--35 | 3 | false | false | medium |
| Bluete (flowering) | 7--14 | 4 | false | true | medium |
| Ernte (harvest) | 42--84 | 5 | true | true | medium |

Hinweis: Gurken wachsen extrem schnell -- von Aussaat bis Ernte vergehen nur 50--70 Tage (sortenabhaengig). Die Bluete- und Erntephase ueberlappen stark -- die Pflanze blueht und fruchtet gleichzeitig ueber Wochen. Regelmaessiges Ernten ist kritisch -- ueberreife Gurken hemmen Neuansatz.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer, Abdeckung bis Keimung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 (dunkel bis Keimung, danach sofort 14--16 h) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--30 (optimal 28) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 22--25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65--80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70--85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 (optimal 400) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 24--28 (optimal 26) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (hoher Wasserbedarf!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Gurken brauchen VIEL Wasser -- die Frucht besteht zu 95% aus Wasser. Wasserstress fuehrt sofort zu bitteren, missgeformten Fruechten. Temperatur unter 14 degC verursacht Wachstumsstopp.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 24--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 300--600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Parthenokarpe Sorten (Gewaechshaus-Schlangengurken) benoetigen keine Bestaeubung. Freiland-Sorten benoetigen Insektenbestaeubung -- Dill als Nachbar lockt Bestauber an. Erste maennliche Blueten erscheinen vor den weiblichen (erkennbar an kleinem Fruchtansatz hinter der Bluete).

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.3 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--800 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (bei Hitze 2x taeglich!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1500 (Fruchtentwicklung = enormer Wasserbedarf) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: REGELMAESSIG ERNTEN! Alle 1--2 Tage kontrollieren. Ueberreife Gurken (gelb, dick) hemmen den Neuansatz massiv. Salatgurken bei 25--30 cm ernten, Einlegegurken bei 5--10 cm. Morgenfrueche Ernte ist optimal (hoechster Wassergehalt, knackig).

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 5.5--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.6--1.0 | 5.5--6.0 | 80 | 30 | 25 | 2 |
| Vegetativ | 3-1-2 | 1.5--2.0 | 5.5--6.0 | 150 | 50 | 40 | 3 |
| Bluete | 2-2-3 | 1.7--2.2 | 5.5--6.0 | 180 | 60 | 45 | 3 |
| Ernte | 1-2-3 | 1.7--2.5 | 5.5--6.0 | 200 | 60 | 45 | 3 |

Hinweis: Gurken sind Starkzehrer mit extrem hohem Kalium- und Calcium-Bedarf. Kaliummangel zeigt sich als Blattrandnekrose und missgeformte, birnenfoermige Fruechte. Calciummangel verursacht Bluetenendstueckfaeule (weniger haeufig als bei Tomate/Paprika). pH-Bereich 5.5--6.0 fuer Hydrokultur, 6.0--6.8 fuer Erdkultur.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 3--7 Tage | Keimblaetter (gross, rund) voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 3--5 echte Blaetter, Ranken beginnen sich zu bilden |
| Vegetativ -> Bluete | event_based | 21--35 Tage | Erste Bluetenknospen sichtbar |
| Bluete -> Ernte | time_based | 7--14 Tage nach Bluetebeginn | Erste Fruechte in Erntegroesse (Gurke waechst extrem schnell!) |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Gewaechshaus/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Aqua Flores A | Canna | base | 4-0-3 | 0.16 | 3 | Bluete, Ernte |
| Aqua Flores B | Canna | base | 0-4-3 | 0.14 | 4 | Bluete, Ernte |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Tomatendunger (fluessig) | COMPO BIO / Neudorff | organisch | 30--50 ml / 10 L Giesswasser | Juni--September, woechentlich | heavy_feeder |
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (Pflanzlochfuellung) | alle |
| Hornspäne (grob) | Oscorna / div. | organisch (N-Langzeit) | 80--120 g/m2 | Fruehjahr (Einarbeitung bei Pflanzung) | heavy_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 1 L/Pflanze | Juni--August, woechentlich | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 1 L/Pflanze | Juli--September, woechentlich | heavy_feeder (Kalium fuer Frucht) |
| Mulch (Stroh/Grasschnitt) | Eigenerzeugung | Bodenverbesserung | 5--10 cm Schicht | Mai--September | alle (Feuchtigkeitserhalt, Unkrautunterdrueckung) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Gurke Standard Gewaechshaus Hydro")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--2 | Saemling | 0.5--0.8 | 5.5--5.8 | 0.3 | 0.4 | 0.4 | Nur Wasser erste 3 Tage nach Keimung |
| 3--4 | Saemling/Veg | 1.0--1.5 | 5.5--5.8 | 0.5 | 0.6 | 0.6 | EC zuegig steigern, Gurken sind gefraessig |
| 5--7 | Vegetativ | 1.5--2.0 | 5.5--6.0 | 0.5 | 0.8 | 0.8 | Volle Dosierung, N-betont |
| 8--10 | Bluete/Ernte | 1.7--2.2 | 5.5--6.0 | 0.6 | 0.8 (Flores A) | 0.8 (Flores B) | Umstellung auf Bluete, K-betont |
| 11+ | Ernte | 1.7--2.5 | 5.5--6.0 | 0.6 | 0.8 (Flores A) | 0.8 (Flores B) | Hoher Wasserdurchsatz, EC stabil halten |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (20--24 degC -- Gurken moegen warmes Wasser!)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Vega/Flores A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega/Flores B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer!** Gurken brauchen aehnlich viel Naehrstoffe wie Tomate, bei noch hoeherem Wasserbedarf.
- **Kalium-Schwerpunkt ab Frucht:** K foerdert Fruchtentwicklung, Geschmack und Haltbarkeit. Kaliummangel = birnenfoermige, bittere Fruechte.
- **Calcium gleichmaessig:** Wie bei Tomate/Paprika ist gleichmaessige Ca-Versorgung wichtig. Bei Hydro: CalMag bei jedem Giessgang.
- **Warmes Giesswasser:** Gurken reagieren empfindlich auf kaltes Wasser (unter 15 degC). Giesswasser auf mindestens 18 degC temperieren.
- **Blattduengung vermeiden:** Nasse Blaetter foerdern Mehltau-Infektionen massiv.
- **Mulchen!** Mulch (Stroh, Grasschnitt) haelt die Bodenfeuchtigkeit gleichmaessig und reduziert Fruchtfaeule durch Bodenkontakt.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1 (bei Hitze taeglich, Gewaechshaus evtl. 2x taeglich) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Warmes Giesswasser (18--24 degC). Gleichmaessige Feuchtigkeit absolut kritisch -- Trockenstress = bittere, missgeformte Fruechte. Nicht ueber Blaetter giessen (Mehltau!). Tropfbewaesserung ideal. Mulchen hilft enorm. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7 (woechentlich ab Fruchtansatz) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; einmal Auspflanzen in Endtopf/Beet) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 5 (Gurken sind sehr schaedlingsanfaellig!) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Apr | Vorkultur starten | Aussaat einzeln in 8--10 cm Toepfe, 25--30 degC, Heizmatte | hoch |
| Mai | Auspflanzen + Rankhilfe | Nach Eisheiligen, 60--100 cm Abstand, Rankhilfe aufstellen, Mulch ausbringen | hoch |
| Jun | Pflege + Erste Blueten | Ausgeizen (Gewaechshaus-Sorten), erste Fruechte ansetzen, taeglich giessen | hoch |
| Jul | Haupternte | Alle 1--2 Tage ernten! Woechentlich duengen, auf Mehltau achten | hoch |
| Aug | Ernte + Schaedlingskontrolle | Regelmaessig ernten, Echter Mehltau kontrollieren, ggf. befallene Blaetter entfernen | hoch |
| Sep | Nachernte | Letzte Fruechte ernten, Duengung reduzieren | mittel |
| Okt | Saisonende | Pflanzen entfernen, Beet raeumen, Substrat kompostieren | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar -- Gurke ist eine einjaehrige Pflanze und ueberlebt keine Temperaturen unter 5 degC.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaeuse (Aphids) | Aphis gossypii, Myzus persicae | Gekraeuselte Blaetter, Honigtau, Virusuebertraeger (CMV) | leaf, stem | vegetative, flowering | easy |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, silbrige Punkte, Blattfall | leaf | vegetative, harvest | medium |
| Weisse Fliege (Whitefly) | Trialeurodes vaporariorum | Honigtau, weisse Fliegen an Blattunterseite | leaf | vegetative, flowering | easy |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Flecken, verkrueppelte Blaetter | leaf, flower | vegetative, flowering | medium |
| Gurkenkaefer (Cucumber Beetle) | Diabrotica spp., Acalymma spp. | Lochfrass an Blaettern und Fruechten, Virusuebertraeger (Gurkenwelke) | leaf, fruit | vegetative, harvest | easy |
| Schnecken (Slugs/Snails) | Arion spp. | Frass an Jungpflanzen und Fruechten | leaf, fruit | seedling, vegetative | easy |
| Minierfliege (Leafminer) | Liriomyza spp. | Weisse Miniergaenge in Blaettern | leaf | vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau (Powdery Mildew) | fungal | Weisser mehliger Belag auf Blaettern, Blattverlust | dry_warm_days, cool_nights, poor_airflow | 5--10 | vegetative, flowering, harvest |
| Falscher Mehltau (Downy Mildew) | fungal | Eckige gelbe Flecken auf Blattoberseite (adernbegrenzt!), grauer Sporenrasen unten | high_humidity, cool_nights | 5--10 | vegetative, harvest |
| Gurkenmosaikvirus (CMV) | viral | Mosaikartige Blattmusterung, verkrueppelte Fruechte, Zwergwuchs | aphid_transmission | 10--21 | alle |
| Gurkenwelke (Bacterial Wilt) | bacterial | Pflanze welkt ploetzlich, Leitbuendel braun, milchiger Saft beim Schnitttest | beetle_transmission | 7--14 | vegetative, harvest |
| Grauschimmel (Botrytis) | fungal | Grauer pelziger Belag auf Fruechten und Staengeln | high_humidity, cool_temps | 3--7 | flowering, harvest |
| Blattfleckenkrankheit (Angular Leaf Spot) | bacterial | Eckige, wassergetränkte Flecken, werden braun/papierig | rain_splash, high_humidity | 5--10 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10--20 | 14--21 |
| Amblyseius californicus | Spinnmilbe (praeventiv) | 5--10 | 14--21 |
| Encarsia formosa | Weisse Fliege | 3--5 | 21--28 |
| Aphidius colemani | Blattlaeuse | 2--5 | 14--21 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Macrolophus pygmaeus | Weisse Fliege, Blattlaeuse, Spinnmilbe | 2--5 | 28--42 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse, Weisse Fliege, Spinnmilbe |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Weisse Fliege |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau |
| Schwefelpraeparat | biological | Netzschwefel | Spruehung 0.2%, alle 7--10 Tage (ACHTUNG: nicht bei ueber 25 degC! Blattverbrennungen!) | 3 | Echter Mehltau |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen, 5 g/m2 | 0 | Schnecken |
| Mulch + Tropfbewaesserung | cultural | -- | Stroh/Grasschnitt-Mulch + Tropfschlauch | 0 | Mehltau-Praevention, Fruchtfaeule-Reduktion |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen, Restmuell | 0 | Mehltau, Virusverbreitung eindaemmen |

### 5.5 Resistenzen der Art

Moderne F1-Hybriden bieten Resistenzen gegen die wichtigsten Krankheiten.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Gurkenmosaikvirus (CMV) | Krankheit | Viele F1-Hybriden (z.B. 'Marketmore 76', 'Eureka F1') | `resistant_to` |
| Echter Mehltau (PM) | Krankheit | F1-Hybriden wie 'Picolino F1', 'Diamant F1' | `resistant_to` |
| Falscher Mehltau (DM) | Krankheit | Neuere Selektionen (z.B. 'Bristol F1') | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Kuerbisgew aechse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae, N-Anreicherung) oder Gruenduengung |
| Empfohlene Nachfrucht | Mittelzehrer (Moehren, Fenchel) oder Schwachzehrer (Salat, Radieschen) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Cucurbitaceae (Kuerbis, Zucchini, Melone, Gurke) auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Dill | Anethum graveolens | 0.9 | Klassische Mischkultur! Dill zieht Bestauber + Nuetzlinge an, foerdert Gurkenertrag | `compatible_with` |
| Bohne (Busch/Stange) | Phaseolus vulgaris | 0.8 | N-Fixierung, Bodenbeschattung | `compatible_with` |
| Erbse | Pisum sativum | 0.8 | N-Fixierung | `compatible_with` |
| Mais | Zea mays | 0.8 | Windschutz, Stuetzfunktion (traditionelle "Drei Schwestern") | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Bodenbeschattung, schnelle Ernte, Raumausnutzung | `compatible_with` |
| Sellerie | Apium graveolens | 0.7 | Aehnliche Standortansprueche (feucht, naehrstoffreich) | `compatible_with` |
| Sonnenblume | Helianthus annuus | 0.7 | Windschutz, Bestauber anlocken | `compatible_with` |
| Radieschen | Raphanus sativus | 0.8 | Gurkenkaefer-Abwehr, schnelle Ernte | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr, Schaedlings-Abwehr | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Naehrstoffkonkurrenz (beide Starkzehrer), erhoehtes Krautfaeule-Risiko fuer Kartoffeln | moderate | `incompatible_with` |
| Melone | Cucumis melo | Gleiche Familie -- gemeinsame Schaedlinge/Krankheiten, Kreuzbestaeubung moeglich | moderate | `incompatible_with` |
| Kuerbis / Zucchini | Cucurbita spp. | Gleiche Familie -- gemeinsame Schaedlinge, Platzkonkurrenz | moderate | `incompatible_with` |
| Aromatische Kraeuter (Salbei, Thymian) | Salvia, Thymus | Gegensaetzliche Wasserbeduerfnisse (trocken vs. feucht) | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Cucurbitaceae (mit sich selbst) | `shares_pest_risk` | Mehltau, CMV, Gurkenkaefer, Fusarium, Nematoden | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Standard-Salatgurke |
|-----|-------------------|-------------|------------------------------|
| Einlegegurke (Cornichon) | Cucumis sativus (Einlege-Sorten) | Gleiche Art | Robuster, Freiland-tauglich, kleinfruechtiger |
| Zucchini | Cucurbita pepo | Gleiche Familie, aehnliche Kultur | Robuster, hoehere Ertraege, frosttoleranter |
| Mexikanische Mini-Gurke | Melothria scabra | Aehnliche Frucht, andere Gattung | Robuster, zierlich, trockenheitsvertraeglicher |
| Luffa-Gurke (Schwammgurke) | Luffa aegyptiaca | Gleiche Familie, Rankpflanze | Dekorativ, Schwamm-Gewinnung, waermeliebend |
| Bittergurke (Karela) | Momordica charantia | Gleiche Familie | Medizinisch genutzt, sehr waermeliebend |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Cucumis sativus,Gurke;Salatgurke;Schlangengurke;Einlegegurke;Cucumber;Garden Cucumber;Gherkin,Cucurbitaceae,Cucumis,annual,day_neutral,vine,fibrous,4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b,0.1,"Suedostasien (Indien, Himalaya-Region)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Salatgurke (generisch),Cucumis sativus,,,high_yield,60,,open_pollinated
Marketmore 76,Cucumis sativus,Cornell University,1976,disease_resistant;high_yield;heirloom,65,cmv;scab,open_pollinated
Picolino F1,Cucumis sativus,,,compact;disease_resistant;high_yield,50,powdery_mildew,f1_hybrid
Vorgebirgstraube (Einlegegurke),Cucumis sativus,,,heirloom;high_yield,55,,open_pollinated
Diamant F1,Cucumis sativus,,,disease_resistant;high_yield,58,powdery_mildew;cmv,f1_hybrid
Chinese Slangen,Cucumis sativus,,,long_season;heirloom,65,,open_pollinated
```

---

## Quellenverzeichnis

1. NCSU Extension -- Cucumis sativus: https://plants.ces.ncsu.edu/plants/cucumis-sativus/
2. Haifa Group -- Cucumber Crop Guide: https://www.haifa-group.com/cucumber-fertilizer/crop-guide-growing-cucumbers
3. Cornell University -- Hydroponic Recipes: http://hort.cornell.edu/greenhouse/crops/factsheets/hydroponic-recipes.pdf
4. Gardenia.net -- Cucumis sativus: https://www.gardenia.net/plant/cucumis-sativus
5. Gardenia.net -- Best Companions for Cucumbers: https://www.gardenia.net/guide/best-worst-companions-for-cucumbers
6. Gardener's Path -- Cucumber Companion Plants: https://gardenerspath.com/plants/vegetables/cucumber-companion-plants/
7. Epic Gardening -- Growing Cucumbers: https://www.epicgardening.com/growing-cucumbers/
8. MasterClass -- Cucumber Companion Planting Guide: https://www.masterclass.com/articles/cucumber-companion-planting-guide
9. Old Farmer's Almanac -- Cucumbers: https://www.almanac.com/plant/cucumbers
10. GrowDirector -- Hydro Cucumbers Guide: https://growdirector.com/how-to-grow-hydro-cucumbers-case-based-guide-2024/
