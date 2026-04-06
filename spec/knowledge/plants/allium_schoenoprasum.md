# Feinroehriger Schnittlauch -- Allium schoenoprasum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, Hortipendium, grove.eco, naturadb.de, bio-gaertner.de, fryd.app, samen.de, HydroponicsUp, Upstart University, kiepenkerl.de, schadbild.com

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Allium schoenoprasum | `species.scientific_name` |
| Volksnamen (DE/EN) | Schnittlauch; Feinroehriger Schnittlauch; Chives; Ciboulette | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` -> `botanical_families.name` |
| Gattung | Allium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | bulbous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- bluet bei laengeren Tagen ab Juni, vegetatives Wachstum im Fruehling durch zunehmende Taglaenge gefoerdert) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | very_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Vollstaendig winterhart bis ca. -30 degC. Oberirdische Teile ziehen im Herbst ein, Zwiebelbulben treiben im Fruehjahr zuverlaessig wieder aus. In Mitteleuropa problemlos mehrjaehrig (Freiland ganzjaehrig). | `species.hardiness_detail` |
| Heimat | Europa, Asien, Nordamerika (zirkumpolar, temperierte Zonen) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8--10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat ab Maerz moeglich, Schnittlauch ist frosthart) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 6; 7 | `species.direct_sow_months` |
| Erntemonate | 3; 4; 5; 6; 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 5; 6; 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Die einfachste Vermehrung erfolgt durch Teilung der Bulbenhorste im Fruehling oder Herbst. Horst ausgraben, in Teilstuecke mit je 5--10 Zwiebeln teilen und sofort wieder einpflanzen. Regelmaeassige Teilung (alle 3--4 Jahre) verhuetet Vergreisen und foerdert kraeftigen Austrieb.

**Keimhinweise:**
- Optimale Keimtemperatur: 18--25 degC
- Minimale Keimtemperatur: 10 degC (langsame Keimung)
- Keimdauer: 14--21 Tage (bei optimaler Temperatur 7--14 Tage)
- **Dunkelkeimer** -- Samen ca. 1--2 cm mit Erde bedecken
- Substrat gleichmaessig feucht halten, Staunaesse vermeiden
- Saattiefe: 1--2 cm
- Kaeltekeimer: Kaltphase (4--6 Wochen bei 5 degC) kann Keimrate verbessern, ist aber nicht zwingend noetig

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaf; stem; root (alle Pflanzenteile inkl. Zwiebel) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | N-Propyl-Disulfid; Organische Schwefelverbindungen (Thiosulfinate) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (haemolytische Anaemie bei Hunden/Katzen, Heinz-Koerper-Bildung) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA Animal Poison Control listet alle Allium-Arten (Zwiebel, Knoblauch, Schnittlauch, Lauch) als giftig fuer Katzen, Hunde und Pferde. N-Propyl-Disulfid schaedigt die Erythrozyten und fuehrt zu haemolytischer Anaemie. Schnittlauch ist weniger toxisch als Knoblauch oder Zwiebel, aber bei regelmaessiger Aufnahme durchaus gefaehrlich. Fuer Menschen ungefaehrlich und als Nahrungsmittel etabliert.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 3; 4; 5; 6; 7; 8; 9; 10 | `species.pruning_months` |

Hinweis: Regelmaessiges Schneiden (3--5 cm ueber Bodenniveau) foerdert den Neuaustrieb und haelt die Schlotten zart. Nach der Bluete Bluetenstaende abschneiden, um die vegetative Kraft zu erhalten. 2--3 komplette Rueckschnitte pro Saison sind moeglich; nach jedem Schnitt leicht duengen. Im Herbst die Pflanze einziehen lassen (nicht abschneiden), die Naehrstoffe wandern zurueck in die Zwiebel.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (klassisches Fensterbrett- und Balkonkraut) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 20--40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20--30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20--25 | `species.spacing_cm` |
| Indoor-Anbau | yes (sonnige Fensterbank, ganzjaehrig moeglich; Zusatzbelichtung im Winter empfohlen) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (sonniger bis halbschattiger Standort) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (nicht noetig, da vollstaendig winterhart) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose, durchlaessige Kraeutererde. Lehmhaltige Erde wird toleriert. Gute Drainage, Staunaesse vermeiden. pH 6.0--7.0. | -- |

**Hinweis:** Schnittlauch ist eines der anspruchslosesten Kuechenkraeuter. Vertraegt Sonne bis Halbschatten. Im Topf regelmaessig giessen, vertraegt kurze Trockenheit, bildet dann aber duenne Halme. Ideal als Beeteinfassung oder in Kraeuterspiralen. Im Erwerbsanbau werden Horste auch im Winter unter Glas getrieben (Treibkultur).

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 14--21 | 1 | false | false | low |
| Saemling (seedling) | 21--35 | 2 | false | false | low |
| Vegetativ (vegetative) | fortlaufend (mehrjaehrig) | 3 | false | true | high |
| Bluete (flowering) | 21--35 | 4 | false | true | medium |
| Dormanz (dormancy) | 90--120 (Winter) | 5 | false | false | high |

Hinweis: Schnittlauch ist mehrjaehrig und durchlaeuft jaehrlich den Zyklus Vegetativ -> Bluete -> Dormanz -> Vegetativ. Die vegetative Phase ist die Haupterntephase. Nach der Bluete koennen die Halme bitter werden; Bluetenstaende rechtzeitig entfernen oder fuer Dekor/Essig nutzen. Im Winter zieht die Pflanze oberirdisch ein und treibt im Fruehling aus den Zwiebeln neu aus.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | -- (Dunkelkeimer, Licht erst nach Keimung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--25 (optimal 20) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
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
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (optimal 250) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 14--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--24 (optimal 20) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Schnittlauch bevorzugt kuehle Temperaturen. Bei Hitze ueber 28 degC verlangsamt sich das Wachstum und die Halme werden duenn und gelblich. Halbschatten im Hochsommer ist vorteilhaft.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 14--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16+ (Langtagspflanze -- laengere Tage loesen Bluete aus) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Blueten (lila Kugelblueten) sind essbar und dekorativ. Fuer Blatternten Bluetenstaende frueh entfernen, da nach der Bluete die Halmqualitaet nachlasst. Zur Saatgutgewinnung Blueten ausreifen lassen (braune, trockene Kapseln).

#### Phase: Dormanz (dormancy)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (kurze Wintertage) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -- (natuerlich, Winter; frosthart bis -30 degC) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -- | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | -- (Freiland: natuerlicher Niederschlag genuegt; Topf: gelegentlich kontrollieren) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | minimal | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Oberirdische Teile sterben im Herbst ab. Zwiebeln im Boden belassen. Topfkultur frostfrei (aber kalt, 0--5 degC) ueberwintern oder draussen stehen lassen (frosthart). Kaltphase von mindestens 6--8 Wochen bei unter 5 degC ist fuer kraeftigen Fruehjahraustrieb notwendig (Vernalisation).

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 6.0--6.5 | 60 | 30 | 40 | 2 |
| Vegetativ | 3-1-2 | 0.8--1.4 | 6.0--6.5 | 100 | 40 | 50 | 3 |
| Bluete | 2-2-2 | 0.8--1.2 | 6.0--6.5 | 80 | 35 | 40 | 2 |
| Dormanz | 0-0-0 | 0.0 | -- | -- | -- | -- | -- |

Hinweis: Schnittlauch ist ein Schwachzehrer, benoetigt aber fuer die Aromaentwicklung gute Schwefelversorgung (S). Alle Allium-Arten nutzen Schwefel fuer die Synthese von Geschmacks- und Aromastoffen (Allicin und verwandte Thiosulfinate). EC ueber 2.0 mS vermeiden. pH-Optimum im leicht sauren bis neutralen Bereich (6.0--7.0).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 14--21 Tage | Keimblaetter voll entfaltet, erstes gruenes Halmpaar sichtbar |
| Saemling -> Vegetativ | manual / conditional | 21--35 Tage | 3--5 cm hohe Halme, eigenstaendiges Wachstum |
| Vegetativ -> Bluete | event_based | Langtagreaktion (Mai/Juni), ab ca. 16h Taglaenge | Erste Bluetenknospen sichtbar an den Halmspitzen |
| Bluete -> Dormanz | time_based | Herbst (Oktober/November) | Halme vergilben und trocknen ein |
| Dormanz -> Vegetativ | event_based | Fruehling (Februar/Maerz) | Neuaustrieb aus Zwiebeln bei steigenden Temperaturen und Taglaenge |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |

Hinweis: Fuer Schnittlauch ca. 50--75% der Herstellerdosierung verwenden (Schwachzehrer). Schwefelhaltige Duenger bevorzugen.

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 | Fruehjahr (Einarbeitung) | alle |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 30--50 g/m2 | Fruehjahr (Einarbeitung) | light_feeder |
| Bio Kraeuterdunger (fluessig) | COMPO BIO | organisch | 15--25 ml / 10 L Giesswasser | April--September, alle 4 Wochen | light_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:20 verduennt, 0.5 L/m2 | April--August, alle 4 Wochen | light_feeder |
| Schachtelhalmbruehe | Eigenerzeugung | Pflanzenhilfsmittel | 1:5 verduennt, Blattspruehung | Mai--September, alle 14 Tage | alle (Rost-Praevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Schnittlauch Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--3 | Saemling | 0.3--0.5 | 6.0 | 0.2 | 0.3 | 0.3 | Nur Wasser erste 7 Tage nach Keimung |
| 4--6 | Saemling/Veg | 0.6--0.8 | 6.0--6.5 | 0.3 | 0.4 | 0.4 | EC langsam steigern |
| 7--12 | Vegetativ | 0.8--1.2 | 6.0--6.5 | 0.3 | 0.5 | 0.5 | Hauptwachstum, nach jedem Ernteschnitt leicht aufduengen |
| 13+ | Vegetativ (Ernte) | 1.0--1.4 | 6.0--6.5 | 0.3 | 0.6 | 0.6 | Etablierte Pflanze, regelmaessige Ernte |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Vega A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Schwachzehrer!** Schnittlauch braucht wenig Duengung -- eine Kompostgabe im Fruehjahr reicht fuer die gesamte Saison.
- **Schwefel wichtig:** Alle Allium-Arten benoetigen Schwefel fuer die Synthese von Aromastoffen (Allicin). Schwefelhaltige Duenger oder Bittersalz (Magnesiumsulfat, 0.5 g/L) foerdern den Geschmack.
- **Stickstoff nicht uebertreiben:** Zu viel N fuehrt zu weichen, schlappen Halmen die leicht umfallen und anfaellig fuer Pilzkrankheiten werden.
- **Nach jedem Ernteschnitt:** Leicht nachduengen (organisch: Brennnesseljauche 1:20; mineralisch: EC um 0.2 erhoehen), da die Pflanze viel Blattmasse regenerieren muss.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (Freiland: Dormanz, kein Giessen; Topf: sehr selten, nur Austrocknung verhindern) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich (pH 6.0--7.0). Normale Leitungswasserqualitaet genuegt. Morgens giessen bevorzugt. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 28--42 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36--48 (alle 3--4 Jahre Horst teilen und umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | -- | Dormanz, keine Pflegearbeiten | -- |
| Feb | Treibkultur (optional) | Horste in Toepfe setzen und bei 15--20 degC antreiben fuer fruehen Schnittlauch | niedrig |
| Marz | Austrieb / Kompostgabe | Reifkompost (2--3 L/m2) um die Horste verteilen, Boden lockern | hoch |
| Apr | Erste Ernte | Ab ca. 15 cm Halmhoehe erste Ernte moeglich, 3 cm ueber Boden schneiden | hoch |
| Mai | Ernte + Bluete beobachten | Regelmaessig ernten; Bluetenknospen entfernen oder fuer Dekoration nutzen | hoch |
| Jun | Hauptblüüte + Ernte | Bluetenstaende essbar (Salat, Essig); nach der Bluete komplett zurueckschneiden | hoch |
| Jul | 2. Austrieb + Ernte | Nach Rueckschnitt treibt Schnittlauch kraeftig neu aus; leicht nachduengen | hoch |
| Aug | Ernte + Schaedlingskontrolle | Auf Rost achten (orangefarbene Pusteln auf Halmen); bei Befall befallene Halme entfernen | mittel |
| Sep | Letzte Ernte | Letzte Ernte vor dem Einziehen der Pflanze | mittel |
| Okt | Saisonende | Halme natuerlich einziehen lassen; Horst mit Kompost mulchen | niedrig |
| Nov | Vorbereitung Treibkultur | Optional: Horste ausgraben und fuer Winterantrieb in Toepfe setzen | niedrig |
| Dez | Dormanz | Keine Pflegearbeiten; Topf-Schnittlauch kuehl und dunkel lagern fuer Vernalisation | -- |

### 4.3 Ueberwinterung

Schnittlauch ist vollstaendig winterhart (bis ca. -30 degC) und benoetigt keine besondere Ueberwinterungspflege. Die oberirdischen Teile sterben im Herbst ab, die Zwiebelbulben ueberwintern im Boden. Eine leichte Kompost- oder Laubmulchschicht schuetzt vor extremen Kahlfroesten. Topfkultur: Topf draussen lassen (frosthart) oder frostfrei bei 0--5 degC lagern. Mindestens 6--8 Wochen Kaelteexposition unter 5 degC sind fuer kraeftigen Fruehjahraustrieb noetig (Vernalisation).

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Lauchminierfliege | Phytomyza gymnostoma | Miniergaenge in den Halmen, Puppen an der Halmbasis, Halme vergilben und knicken ab | leaf, stem | vegetative | medium |
| Thripse (Thrips) | Thrips tabaci | Silbriges Aussehen der Halme, feine helle Saugstellen | leaf | vegetative | medium |
| Blattlaeuse (Aphids) | Myzus ascalonicus, Neotoxoptera formosana | Saugende Insekten an Halmen und Bluetenknospen, Wuchshemmung | leaf, flower | vegetative, flowering | easy |
| Zwiebelfliege | Delia antiqua | Maden fressen an Zwiebeln, Halme vergilben und welken | root | vegetative | hard |
| Lauchmotte | Acrolepiopsis assectella | Raupen fressen Gaenge in Halme, Halme werden hohl | leaf, stem | vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Schnittlauch-Rost (Puccinia allii) | fungal | Orangebraune Rostpusteln (Uredosporen) auf Halmen, spaeter schwarze Teleutosporenlager | high_humidity, warm_temps (10--25 degC) | 7--14 | vegetative, flowering |
| Falscher Mehltau (Peronospora destructor) | fungal (Oomycet) | Blasse Flecken auf Halmen, grau-violetter Sporenrasen bei hoher Feuchtigkeit | high_humidity, cool_nights | 7--14 | vegetative |
| Zwiebelfaeule (Sclerotium cepivorum) | fungal | Weisser Mycelbelag an Zwiebelbasis, Halme vergilben und sterben ab | cool_wet_soil, soil_contamination | 14--28 | vegetative |
| Purpurfleckenkrankheit (Alternaria porri) | fungal | Dunkelbraune bis purpurrote Flecken auf Halmen | high_humidity, rain_splash | 5--10 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Steinernema feltiae (Nematode) | Lauchminierfliege (Puppen) | 250.000/m2 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage, 3x wiederholen | 0 | Blattlaeuse, Thripse |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Thripse |
| Kulturschutznetz (0.8 mm Maschenweite) | cultural | -- | Netz ueber Bestand spannen ab Maerz bis Oktober | 0 | Lauchminierfliege, Lauchmotte, Zwiebelfliege |
| Befallene Halme entfernen | cultural | -- | Sofort abschneiden und im Restmuell (nicht Kompost) entsorgen | 0 | Rost, Falscher Mehltau |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Spruehung 1:5 verduennt, alle 14 Tage praeventiv | 0 | Pilzkrankheiten allgemein |
| Anbaupause 5 Jahre | cultural | -- | Kein Anbau von Allium-Arten auf gleicher Flaeche fuer 5 Jahre | 0 | Zwiebelfaeule, Nematoden |

### 5.5 Resistenzen der Art

Schnittlauch hat als Art eine moderate natuerliche Widerstandsfaehigkeit gegen Schaedlinge -- die aetherischen Oele (Allicin und verwandte Schwefelverbindungen) wirken auf viele Insekten abschreckend. Gegen Rost (Puccinia allii) gibt es jedoch keine nennenswerte Resistenz.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Allgemeine Insektenabwehr | Schaedlinge | Art-eigene Schwefelverbindungen (Allicin) | -- |
| Schneckenfrass | Schaedlinge | Art-eigene Schwefelverbindungen, Schnecken meiden Allium | -- |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Lauchgewaechse (Amaryllidaceae / Allium) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) oder Gruenduengung |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Radieschen) oder Gruenduengung |
| Anbaupause (Jahre) | 4--5 Jahre fuer Allium-Arten auf gleicher Flaeche (Nematoden, Zwiebelfaeule) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Allicin-Abgabe hemmt Pilzkrankheiten an der Tomate (Braunfaeule) | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.9 | Klassische Mischkultur; Schnittlauch wehrt Grauschimmel ab | `compatible_with` |
| Moehre | Daucus carota | 0.9 | Schnittlauch-Duft vertreibt Moehrenfliege | `compatible_with` |
| Rose | Rosa spp. | 0.8 | Schnittlauch wehrt Blattlaeuse und Sternrusstau an Rosen ab | `compatible_with` |
| Sellerie | Apium graveolens | 0.7 | Gute Platzausnutzung, unterschiedliche Wurzeltiefen | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.7 | Gute Raumnutzung in Kraeuterbeet | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Bodenbeschattung durch Spinat, ergaenzende Ernte | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.7 | Allium-Duft schreckt Kohlweisslinge ab | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Gute Raumnutzung in Kraeuterbeet, ergaenzende Duftprofile | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Bohnen (Busch-/Stangenbohne) | Phaseolus vulgaris | Allicin hemmt Knuellchenbakterien (Rhizobien), reduziert N-Fixierung | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Wie Bohnen: Allicin hemmt Rhizobien | moderate | `incompatible_with` |
| Kopfkohl / Weisskohl | Brassica oleracea var. capitata | Naehrstoffkonkurrenz bei dichter Pflanzung, geteilte Schaedlinge (Thripse) | mild | `incompatible_with` |
| Rote Beete | Beta vulgaris | Wachstumshemmung durch Allium-Wurzelausscheidungen | mild | `incompatible_with` |
| Lauch / Porree | Allium porrum | Naehrstoffkonkurrenz und Schaedlingsuebertragung innerhalb der Gattung Allium | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Amaryllidaceae / Allium (mit sich selbst) | `shares_pest_risk` | Rost (Puccinia allii), Zwiebelfliege (Delia antiqua), Lauchminierfliege, Zwiebelfaeule (Sclerotium cepivorum) | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Schnittlauch |
|-----|-------------------|-------------|------------------------------|
| Knoblauch-Schnittlauch | Allium tuberosum | Gleiche Gattung, flache Blaetter, Knoblaucharoma | Hitzevertraglicher, anderes Aroma |
| Winterheckenzwiebel | Allium fistulosum | Gleiche Gattung, groeber, aehnliche Verwendung | Robuster, dickere Halme, staerkeres Aroma |
| Bärlauch | Allium ursinum | Gleiche Gattung, Knoblaucharoma, Wildkraut | Frueher Austrieb (Maerz), Bodendecker im Halbschatten |
| Lauch / Porree | Allium porrum | Gleiche Gattung, deutlich groesser | Hoehere Biomasse, vielseitiger in der Kueche |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,direct_sow_months,harvest_months,bloom_months,sowing_indoor_weeks_before_last_frost
Allium schoenoprasum,Schnittlauch;Feinroehriger Schnittlauch;Chives;Ciboulette,Amaryllidaceae,Allium,perennial,long_day,herb,bulbous,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.2,"Europa, Asien, Nordamerika (zirkumpolar)",very_hardy,light_feeder,false,edible;aromatic,3;4;5;6;7,3;4;5;6;7;8;9;10,5;6;7,8
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Staro,Allium schoenoprasum,Kiepenkerl,,aromatic;compact,75,,open_pollinated
Gonzales,Allium schoenoprasum,,,compact;fine_leaf,80,,open_pollinated
Polyvert,Allium schoenoprasum,,,vigorous;high_yield,60,,open_pollinated
Middleman,Allium schoenoprasum,,,medium_leaf;aromatic,70,,open_pollinated
Feinroehriger (Pötschke Historisch),Allium schoenoprasum,Pötschke,,fine_leaf;heirloom;aromatic,75,,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Chives: https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/chives
2. Hortipendium -- Schnittlauch Erwerbsanbau: https://hortipendium.de/Schnittlauch
3. Hortipendium -- Schnittlauch Pflanzenschutz: https://hortipendium.de/Schnittlauch_Pflanzenschutz
4. grove.eco -- Schnittlauch: https://www.grove.eco/pflanzen/allium-schoenoprasum/
5. naturadb.de -- Schnittlauch: https://www.naturadb.de/pflanzen/allium-schoenoprasum/
6. bio-gaertner.de -- Schnittlauch: https://www.bio-gaertner.de/Pflanzen/Schnittlauch
7. HydroponicsUp -- Hydroponic Chives Guide: https://hydroponicsup.com/hydroponic-cultivation/herbs/chives/
8. Upstart University -- Hydroponic Chives: https://university.upstartfarmers.com/blog/grow-hydroponic-chives
9. schadbild.com -- Krankheiten und Schaedlinge an Schnittlauch: https://www.schadbild.com/gem%C3%BCse/schnittlauch/
10. kiepenkerl.de -- Schnittlauch Kulturprobleme: https://www.kiepenkerl.de/kulturprobleme/beim-anbau-von-schnittlauch/
11. samen.de -- Schnittlauch schuetzen: https://samen.de/blog/schnittlauch-schuetzen-krankheiten-und-schaedlinge-erkennen.html
