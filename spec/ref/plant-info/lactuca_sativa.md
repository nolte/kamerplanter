# Salat -- Lactuca sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** Hortipendium, Wikipedia, Bio-Gaertner, fryd.app, samen.de, naturadb.de, grove.eco, effizientduengen.de, Nature Scientific Reports (DLI Lettuce), ResearchGate, Koraylights

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lactuca sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Salat; Gartensalat; Kopfsalat; Lattich; Lettuce; Garden Lettuce | `species.common_names` |
| Familie | Asteraceae | `species.family` -> `botanical_families.name` |
| Gattung | Lactuca | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- lange Tage und hohe Temperaturen loesen "Schiessen" / Bluete aus; kurze Tage und kuehle Temperaturen foerdern Blattbildung) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | moderate | `species.frost_sensitivity` |
| Winterhaerte-Detail | Vertraegt leichte Froeste bis -5 degC. Junge Pflanzen frosthaerter als aeltere. In Mitteleuropa ganzjaehrig mit Schutz (Vlies, Fruehbeet, Gewaechshaus) anbaubar. Hitze ueber 25 degC fuehrt zu Schiessen (Bluetenbildung) und Bitterkeit. | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Vorderasien | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium (Mittelzehrer -- Kopfsalat eher Mittelzehrer, Schnittsalat eher Schwachzehrer) | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4--6 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat ab Maerz unter Vlies/Folie moeglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 6; 7; 8 | `species.direct_sow_months` |
| Erntemonate | 4; 5; 6; 7; 8; 9; 10; 11 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8 (unerwuenscht -- "Schiessen") | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 10--16 degC (Kaltkeimer!)
- Maximale Keimtemperatur: 25 degC (ueber 25 degC Keimhemmung -- Thermodormanz!)
- Keimdauer: 5--10 Tage
- **Lichtkeimer** -- Samen nur leicht andruecken oder hoechstens 0.5 cm bedecken
- Bei Sommeraussaat: Saatgut vor Aussaat 24 h im Kuehlschrank lagern (Thermodormanz brechen)
- Substrat: naehrstoffarme, feine Aussaaterde, gleichmaessig feucht

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (Lactucin in Milchsaft -- in Kultursorten vernachlaessigbar gering; leicht sedierend in hohen Dosen bei Wildsorten) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Hinweis: Salat ist fuer Menschen und Haustiere unbedenklich. Der Milchsaft (Latex) enthaelt Lactucin mit leicht beruhigender Wirkung, die in modernen Kultursorten minimal ist. Wildsalat (Lactuca virosa) enthaelt dagegen deutlich mehr Lactucin.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | -- (kein Rueckschnitt; Pfluecksalat: aeussere Blaetter pfleuecken; Kopfsalat: ganzen Kopf ernten) | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Bei Pflueck- und Schnittsalat einzelne aeussere Blaetter pfleuecken; das Herz waechst nach ("Cut-and-Come-Again"-Methode). Kopfsalat wird als ganzer Kopf geerntet. Beim "Schiessen" (Bluetenstiel bildet sich) Pflanze sofort entfernen -- Blaetter werden bitter.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (ideal fuer Balkon, Fensterbank, Hochbeet) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--5 (pro Kopf) oder Balkonkasten | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 20--30 (Rosette), 60--100 (Bluetenstiel bei Schiessen) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20--35 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25--30 (Kopfsalat), 15--20 (Pfluecksalat) | `species.spacing_cm` |
| Indoor-Anbau | yes (ideal fuer Indoor-Hydro/LED-Kultur; DLI ab 10 mol/m2/Tag genuegt) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (sonnig bis halbschattig, ideal fuer Fruehlings- und Herbstanbau) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (ganzjaehriger Anbau moeglich, Hitzeschutz im Sommer noetig) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humose, naehrstoffreiche, lockere Erde. Gleichmaessige Feuchtigkeit wichtig. Staunaesse vermeiden (Faeulnis). pH 6.0--7.0. | -- |

**Hinweis:** Salat ist eine der besten Einsteiger-Kulturen und ideal fuer Hydroponic, Indoor-Gardening und kleine Flaechen. Sehr kurze Kulturdauer (30--60 Tage) erlaubt mehrere Saetze pro Saison. Hitzeschutz im Sommer (Schattierung, Mulch) verzoegert das Schiessen.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--10 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--45 | 3 | false | true | medium |
| Ernte (harvest) | 7--14 (Erntefenster) | 4 | true | true | low |

Hinweis: Salat hat keine echte Bluete-Phase im Nutzanbau -- das "Schiessen" ist unerwuenscht und markiert das Kulturende. Die vegetative Phase ist die produktive Hauptphase. Pfluecksalat erlaubt kontinuierliches Ernten waehrend der gesamten vegetativen Phase.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50--100 (Lichtkeimer!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3--6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 12--18 (optimal 15; ueber 25 degC Keimhemmung!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht, nie austrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 14--20 (optimal 16) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--40 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 (optimal 200--250) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--15 (ueber 14 DLI sinkt Frischgewicht -- Tipburn-Risiko steigt!) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (max. 16 h -- laengere Photoperioden foerdern Schiessen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 (Salat reagiert sehr positiv auf CO2-Erhoehung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (gleichmaessige Feuchtigkeit kritisch -- Trockenstress fuehrt zu Bitterkeit und Schiessen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Salat reagiert negativ auf zu hohe Lichtintensitaet (DLI > 14 mol/m2/Tag kann Tipburn und Blattrandnekrosen foerdern). Temperaturen ueber 22 degC tags und 16 degC nachts beschleunigen das Schiessen. Halbschatten im Sommer ist vorteilhaft.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich / wie vegetativ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Morgenernte liefert die besten Ergebnisse (hoechster Wassergehalt, knackigste Blaetter). Bei Kopfsalat den Kopf morgens schneiden, bei Pfluecksalat aeussere Blaetter laufend ernten.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 5.8--6.5 | 60 | 25 | 15 | 2 |
| Vegetativ | 3-1-2 | 1.0--1.6 | 5.8--6.5 | 120 | 40 | 25 | 3 |
| Ernte | 2-1-2 | 0.8--1.2 | 5.8--6.5 | 100 | 35 | 20 | 2 |

Hinweis: Calcium ist besonders wichtig fuer Salat -- Ca-Mangel verursacht Tipburn (Blattrandnekrose), das haeufigste physiologische Problem. EC ueber 1.8 mS vermeiden (Salzempfindlichkeit). Nitrat-Akkumulation bei uebertriebener N-Duengung beachten.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--10 Tage | Keimblaetter voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 4--6 echte Blaetter, Pflanze gut angewachsen |
| Vegetativ -> Ernte | time_based / manual | 21--45 Tage (sortenabhaengig) | Kopfsalat: fester Kopf gebildet; Pfluecksalat: erntefaehige Blattgroesse |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle (Tipburn-Praevention!) |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |
| Calciumnitrat | div. | supplement | 15.5-0-0 (+Ca 19%) | 0.10 | 2 | Vegetativ (gegen Tipburn) |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Gemueseduenger (fluessig) | COMPO BIO | organisch | 20--30 ml / 10 L Giesswasser | Apr--Okt, alle 14 Tage | medium_feeder |
| Reifkompost | Eigenerzeugung | organisch | 3--4 L/m2 | Fruehjahr (Einarbeitung vor Pflanzung) | alle |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 40--60 g/m2 | Fruehjahr (Einarbeitung) | medium_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:20 verduennt, 0.5 L/m2 | Apr--Sep, alle 21 Tage | medium_feeder |
| Algenkalk | div. | Bodenhilfsmittel | 100--150 g/m2 | Herbst (Kalkung bei saurem Boden, Ca-Versorgung) | alle |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Salat Standard Hydro/NFT")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--2 | Keimung/Saemling | 0.3--0.5 | 6.0 | 0.2 | 0.2 | 0.2 | Sehr schwach dosieren |
| 3--4 | Saemling/Veg | 0.6--0.8 | 5.8--6.0 | 0.3 | 0.4 | 0.4 | EC langsam steigern |
| 5--7 | Vegetativ | 1.0--1.4 | 5.8--6.2 | 0.4 | 0.6 | 0.6 | Calcium betonen (Tipburn) |
| 8--9 | Ernte | 0.8--1.2 | 5.8--6.2 | 0.3 | 0.5 | 0.5 | EC leicht reduzieren fuer milderen Geschmack |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (15--20 degC)
2. CalMag Agent (Calcium + Magnesium) -- besonders wichtig bei Salat (Tipburn!)
3. Base A -- z.B. Aqua Vega A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen.

### 3.4 Besondere Hinweise zur Duengung

- **Tipburn ist das #1 Problem bei Salat:** Verursacht durch Ca-Mangel in schnell wachsenden inneren Blaettern. Ursache ist oft nicht zu wenig Ca im Substrat, sondern zu geringe Transpiration (hohe Luftfeuchtigkeit, wenig Luftbewegung). Ausreichende Luftzirkulation und moderate Luftfeuchtigkeit sind mindestens so wichtig wie Ca-Duengung.
- **Nitrat-Akkumulation:** Uebermaessige N-Duengung fuehrt zu Nitrat-Anreicherung in den Blaettern (gesundheitlich bedenklich, EU-Grenzwerte beachten). EC nicht ueber 1.6 mS treiben.
- **Salzempfindlich:** Salat ist empfindlich gegenueber hohen EC-Werten. EC ueber 2.0 mS fuehrt zu Salzstress (braune Blattspitzen, Wuchshemmung).
- **Kein Frischdung!** Frischer Mist foerdert Pilzkrankheiten und verschlechtert den Geschmack.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 (gleichmaessige Feuchtigkeit kritisch) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 (bei Winteranbau unter Glas/Vlies) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich (Calcium ist sogar erwuenscht -- Tipburn!). Zimmerwarmes Wasser (15--20 degC). Morgens giessen, moeglichst nicht ueber die Blaetter (Pilzgefahr, Faeulnis). Gleichmaessige Bodenfeuchte ist entscheidend -- Trockenstress fuehrt zu Bitterkeit und Schiessen. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 6; 7; 8; 9; 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig, kurze Kulturzeit) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 5 (Salat ist Schnecken-Magnet!) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true (bei Indoor-/Gewaechshausanbau -- Tipburn!) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | 1. Satz Vorkultur | Vorkultur unter Glas bei 15 degC, Lichtkeimer: Samen nur leicht andruecken | hoch |
| Marz | Auspflanzen 1. Satz + 2. Satz saeen | 1. Satz unter Vlies/Fruehbeet auspflanzen, 2. Satz aussaeen | hoch |
| Apr | 2. Satz pflanzen + 3. Satz saeen | Staffelanbau alle 2--3 Wochen fuer kontinuierliche Ernte | hoch |
| Mai | Erntebeginn 1. Satz + Weitersaat | Erste Koepfe erntereif, Schneckenkontrolle beginnen, Mulchen | hoch |
| Jun | Ernte + Sommeraussaat | Hitzetolerante Sorten waehlen (Batavia, Romana), Schattierung bei Hitze | hoch |
| Jul | Sommerpause / Hitzeschutz | Schiess-Gefahr hoch -- Schattierung, Mulch, abends giessen, schiessresistente Sorten | mittel |
| Aug | Herbstaussaat starten | 1. Herbstsatz aussaeen, kurzere Tage und kuehle Naechte verringern Schiessen | hoch |
| Sep | Herbsternte | Herbstsaetze ernten, letzten Satz unter Vlies pflanzen | hoch |
| Okt | Letzte Ernte / Winterschutz | Feldsalat als Nachfrucht saeen, Vlies/Fruehbeet fuer Spaetherbst-Ernte | mittel |
| Nov | Winterernte (geschuetzt) | Unter Glas/Fruehbeet Ernte moeglich bis in den Winter | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar als typische Winterkultur. Winterkopfsalat (spezielle Sorten) kann ab September gepflanzt werden und ueberwintert mit Vliesschutz fuer Fruehjahrs-Ernte. Ansonsten ist Salat eine kurzlebige Kultur mit 30--60 Tagen Kulturdauer.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Nacktschnecken (Slugs) | Arion spp., Deroceras spp. | Lochfrass, Schleimspuren, ganze Jungpflanzen abgefressen | leaf, stem | seedling, vegetative | easy |
| Blattlaeuse (Aphids) | Nasonovia ribisnigri, Myzus persicae | Gekraeuselte Blaetter, Honigtau, Verkrueppelungen im Salatherz | leaf | vegetative | easy |
| Erdfloh (Flea Beetle) | Phyllotreta spp. | Kleine runde Loecher in Blaettern | leaf | seedling | easy |
| Drahtwuermer (Wireworm) | Agriotes spp. | Fraessgaenge im Wurzelbereich, Pflanze welkt ploetzlich | root | seedling, vegetative | hard |
| Minierfliege (Leafminer) | Liriomyza spp. | Weisse geschlaengelte Miniergaenge in Blaettern | leaf | vegetative | medium |
| Wuehlmaus (Vole) | Arvicola terrestris | Ganze Pflanze wird unteriridisch abgebissen und von unten abgezogen | root | vegetative | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau (Downy Mildew) | fungal (Oomycet) | Gelbe, eckige Flecken auf Blattoberseite (adernbegrenzt), weisser Sporenbelag auf Blattunterseite | cool_humid_conditions, overhead_watering | 5--10 | vegetative |
| Salatfaeule (Grey Mold) | fungal | Grauer, pelziger Belag, matschige Stellen an Blattbasis und Kopf | high_humidity, dense_planting, overhead_watering | 3--5 | vegetative, harvest |
| Ringfleckenvirus (Lettuce Mosaic Virus) | viral | Mosaik-artige Aufhellungen, Wuchsdeformationen, Zwergwuchs | aphid_transmission, infected_seed | 14--21 | vegetative |
| Schwarzbeinigkeit (Damping Off) | fungal | Saemling knickt an Basis um | overwatering, cold_wet_soil | 2--5 | seedling |
| Salatmehltau (Golovinomyces cichoracearum) | fungal | Weisser, mehliger Belag auf Blattoberseiten | warm_dry_days, poor_airflow | 5--10 | vegetative |
| Tipburn (Blattrandnekrose) | physiological | Braune Blattrandnekrose an inneren Blaettern | calcium_deficiency, high_humidity, low_airflow, rapid_growth | -- | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Aphidius colemani (Schlupfwespe) | Blattlaeuse (insb. Myzus persicae) | 2--5 | 14--21 |
| Phasmarhabditis hermaphrodita (Nematode) | Nacktschnecken | 300.000/m2 | 7--14 |
| Steinernema feltiae (Nematode) | Trauermuecken, Erdflohlarven | 250.000/m2 | 7--14 |
| Coccinella septempunctata (Marienkaefer) | Blattlaeuse | 5--10 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schneckenzaun | mechanical | -- | Kupfer- oder Kunststoffzaun um Beet | 0 | Schnecken |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse |
| Gute Luftzirkulation | cultural | -- | Pflanzabstand einhalten, nicht zu dicht pflanzen | 0 | Falscher Mehltau, Salatfaeule |
| Boden-/Tropfbewaesserung | cultural | -- | Nie ueber die Blaetter giessen | 0 | Falscher Mehltau, Salatfaeule |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen und im Restmuell entsorgen | 0 | Falscher Mehltau, Salatfaeule |
| Blattlausresistente Sorten | cultural | -- | Sorten mit Nr-Gen verwenden (z.B. 'Analena', 'Ovation') | 0 | Nasonovia ribisnigri (Blattlaus) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Nasonovia ribisnigri (Blattlaus) | Schaedling | Nr-Gen-Cultivare (z.B. 'Analena', 'Ovation', 'Salanova') | `resistant_to` |
| Bremia lactucae (Falscher Mehltau) | Krankheit | Bl-Gene (Bl:1 bis Bl:38) in resistenten Cultivaren; Resistenz wird regelmaessig durch neue Rassen durchbrochen | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium) |
| Fruchtfolge-Kategorie | Korbbluetler (Asteraceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae), Gruenduengung -- lockerer, stickstoffreicher Boden |
| Empfohlene Nachfrucht | Schwachzehrer (Radieschen, Feldsalat) oder Starkzehrer nach Kompostgabe |
| Anbaupause (Jahre) | 2 Jahre fuer Asteraceae auf gleicher Flaeche (Falscher Mehltau, Nematoden) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Erdbeere | Fragaria x ananassa | 0.9 | Ideale Unterpflanzung, verschiedene Wurzeltiefen | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.8 | Verschiedene Reifzeiten, gute Platznutzung | `compatible_with` |
| Radieschen | Raphanus sativus var. sativus | 0.8 | Schnelle Markierungssaat, verschiedene Wurzeltiefen, Ernte vor Salat-Reife | `compatible_with` |
| Erbse | Pisum sativum | 0.8 | Stickstoffversorgung, verschiedene Wuchshoehen | `compatible_with` |
| Lauch / Porree | Allium porrum | 0.8 | Gegenseitige Schaedlingsabwehr, verschiedene Kulturdauer | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Salat als Unterpflanzung, Tomate bietet Schatten im Sommer | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Salat als Unterpflanzung, Gurke bietet Schatten | `compatible_with` |
| Buschbohne | Phaseolus vulgaris | 0.7 | Stickstoffversorgung, Bodenbeschattung | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Aehnliche Kulturbeduerfnisse, gute Beetausnutzung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sellerie | Apium graveolens | Blattlaeuse werden gegenseitig angezogen, Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Petersilie | Petroselinum crispum | Naehrstoffkonkurrenz, aehnliche Wuchshoehe | mild | `incompatible_with` |
| Knollenfenchel | Foeniculum vulgare var. azoricum | Allelopathische Wechselwirkung, Wuchshemmung | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Asteraceae (mit sich selbst) | `shares_pest_risk` | Falscher Mehltau (Bremia lactucae), Lettuce Mosaic Virus | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Gartensalat |
|-----|-------------------|-------------|------------------------------|
| Feldsalat (Rapunzel) | Valerianella locusta | Aehnliche Nutzung, andere Familie | Winterhart, Anbau Oktober--Maerz, fuellt die Winterluecke |
| Endivie | Cichorium endivia | Gleiche Familie, aehnliche Kultur | Hitze- und kaeltetolerant, bitterer Geschmack |
| Radicchio | Cichorium intybus var. foliosum | Gleiche Familie | Winterhart, intensiver Geschmack |
| Rucola | Eruca vesicaria | Andere Familie (Brassicaceae) | Schnelle Kultur (25 Tage), wuerziger Geschmack |
| Asiasalate | Brassica rapa var. chinensis | Andere Familie (Brassicaceae) | Schnellwuechsig, hitzetolerant, kaeltetolerant |
| Spinat | Spinacia oleracea | Andere Familie (Amaranthaceae) | Frosthart, schnelle Ernte, hoehere Naehrstoffdichte |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Lactuca sativa,Salat;Gartensalat;Kopfsalat;Lattich;Lettuce;Garden Lettuce,Asteraceae,Lactuca,annual,long_day,herb,taproot,4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.0,"Mittelmeerraum, Vorderasien"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Kopfsalat 'Maikoenig',Lactuca sativa var. capitata,,,early_maturing;heirloom,55,,open_pollinated
Kopfsalat 'Attractie',Lactuca sativa var. capitata,,,high_yield,60,downy_mildew,open_pollinated
Kopfsalat 'Kagraner Sommer',Lactuca sativa var. capitata,,,heat_tolerant;heirloom,65,,open_pollinated
Pfluecksalat 'Lollo Rossa',Lactuca sativa var. crispa,,,ornamental;heirloom,50,,open_pollinated
Pfluecksalat 'Lollo Bionda',Lactuca sativa var. crispa,,,ornamental;heirloom,50,,open_pollinated
Pfluecksalat 'Salad Bowl',Lactuca sativa var. crispa,,,high_yield;heat_tolerant,45,,open_pollinated
Eissalat 'Eisberg',Lactuca sativa var. capitata,,,compact;high_yield,70,,open_pollinated
Romanasalat 'Valmaine',Lactuca sativa var. longifolia,,,high_yield;heat_tolerant,70,,open_pollinated
Batavia 'Grazer Krauthaeuptel',Lactuca sativa,,,heat_tolerant;heirloom,60,,open_pollinated
```

---

## Quellenverzeichnis

1. Hortipendium -- Salat Pflanzenschutz: https://www.hortipendium.de/Salat_Pflanzenschutz
2. Wikipedia -- Gartensalat: https://de.wikipedia.org/wiki/Gartensalat
3. Bio-Gaertner -- Gartensalat: https://www.bio-gaertner.de/pflanzen/Gartensalat
4. fryd.app -- Salat: https://fryd.app/lexikon/pflanzen/1-salat
5. samen.de -- Schaedlinge und Krankheiten bei Salaten: https://samen.de/blog/schaedlinge-und-krankheiten-bei-salaten-erkennen-und-bekaempfen.html
6. naturadb.de -- Salat: https://www.naturadb.de/pflanzen/lactuca-sativa/
7. effizientduengen.de -- Kopfsalat: https://www.effizientduengen.de/sonderkulturen/kopfsalat/
8. Nature Scientific Reports -- DLI for Indoor Lettuce: https://www.nature.com/articles/s41598-023-36997-2
9. ResearchGate -- Minimum Light Requirements Indoor Lettuce: https://www.researchgate.net/publication/336076588
10. grove.eco -- Kopfsalat: https://www.grove.eco/pflanzen/lactuca-sativa-capitata-butterhead/
11. Koraylights -- Indoor cultivation PPFD and DLI: https://koraylights.com/how-much-light-do-your-plants-need-indoor-cultivation-ppfd-and-dli/
12. fryd.app -- Mischkultur Salat: https://fryd.app/magazin/mischkultur-salat
