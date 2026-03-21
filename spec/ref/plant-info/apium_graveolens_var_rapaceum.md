# Knollensellerie -- Apium graveolens var. rapaceum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** samen.de, grove.eco, garten-wissen.com, gartenratgeber.net, hausgarten.net, plantura.garden, beetfreunde.de, sativa-rheinau.ch, pflanzenkrankheiten.ch, bioaktuell.ch, ponicslife.com, hydrobuilder.com, ASPCA

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Apium graveolens var. rapaceum | `species.scientific_name` |
| Volksnamen (DE/EN) | Knollensellerie; Wurzelsellerie; Zeller; Celeriac; Turnip-rooted Celery | `species.common_names` |
| Familie | Apiaceae | `species.family` -> `botanical_families.name` |
| Gattung | Apium | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous (Hypokotylknolle) | `species.root_type` |
| Lebenszyklus | biennial (in Kultur als annual genutzt -- Ernte im 1. Jahr vor Bluete) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- Bluetenbildung nach Vernalisation und Langtag im 2. Jahr; Vorzeitiges Schossen bei zu fruehen Kaltphasen in der Jungpflanzenphase) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | moderate | `species.frost_sensitivity` |
| Winterhaerte-Detail | Vertraegt leichte Froeste bis ca. -5 degC (ausgewachsene Pflanzen mit Knolle). Jungpflanzen sind frostempfindlich und duerfen erst nach den Eisheiligen ins Freiland. Laengere Kaltphasen unter 10 degC in der Jungpflanzenphase loesen unerwuenschtes Schossen (Vernalisation) aus. | `species.hardiness_detail` |
| Heimat | Europa, Mittelmeerraum, Vorderasien (Wildform: Sumpfpflanze an Kuesten und Flussufern) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10--12 (sehr lange Kulturzeit! Aussaat ab Mitte Februar) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (Direktsaat nicht empfohlen wegen langer Keimdauer und Kulturzeit) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | -- (keine Direktsaat) | `species.direct_sow_months` |
| Erntemonate | 9; 10; 11 | `species.harvest_months` |
| Bluetemonate | -- (Bluete unerwuenscht im 1. Kulturjahr; im 2. Jahr: 6; 7; 8) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | intermediate | `species.propagation_difficulty` |

Hinweis: Knollensellerie hat eine der laengsten Kulturzeiten im Gemueseanbau (180--200 Tage vom Samen bis zur Ernte). Die Aussaat erfolgt daher sehr frueh (Mitte Februar bis Anfang Maerz) in beheizten Raeumen. Die Keimung ist langsam und ungleichmaessig (2--3 Wochen). Achtung: Jungpflanzen duerfen NICHT unter 10 degC kommen, da dies Vernalisation ausloest und die Pflanzen im 1. Jahr schossen (in Bluete gehen statt Knollen zu bilden).

**Keimhinweise:**
- Optimale Keimtemperatur: 20--22 degC (konstant!)
- Minimale Keimtemperatur: 16 degC (sehr langsame Keimung)
- Keimdauer: 14--28 Tage (langsam und oft ungleichmaessig)
- **Lichtkeimer** -- Samen NUR leicht andruecken, NICHT mit Erde bedecken
- Hohe Luftfeuchtigkeit foerderlich: Abdeckung mit Klarsichtfolie oder Haube (taeglich lueften)
- Substrat: naehrstoffarme Aussaaterde, gleichmaessig feucht, Staunaesse vermeiden
- ACHTUNG Schoss-Gefahr: Temperaturen unter 10 degC fuer laengere Zeit (>10 Tage) in der Jungpflanzenphase loesen Vernalisation aus!

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine; alle Pflanzenteile essbar: Knolle, Stiel, Blaetter) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (keine; Furanocumarine in Blaettern koennen bei intensivem Hautkontakt + Sonnenlicht Photosensibilisierung ausloesen -- Sellerie-Dermatitis bei Feldarbeitern) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (Nahrungsmittel; Sellerie-Allergie ist haeufig, aber nicht toxisch) | `species.toxicity.severity` |
| Kontaktallergen | true (Furanocumarine in Blaettern/Stielen koennen Photodermatitis ausloesen; Sellerie-Allergie: eine der haeufigsten Nahrungsmittelallergien in Mitteleuropa, kreuzreaktiv mit Beifuss-Pollen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Sellerie (Apium graveolens) als nicht toxisch fuer Katzen und Hunde. Sellerie-Allergie (Beifuss-Sellerie-Syndrom) ist in Mitteleuropa die zweithaeufigste Nahrungsmittelallergie nach Haselnuss. Kreuzreaktion mit Beifuss (Artemisia vulgaris), Birke, Karotte, Anis, Fenchel. Furanocumarine (Psoralen, Bergapten) in den Blaettern koennen bei Hautkontakt + UV-Exposition Blasenbildung und Hautverfaerbung verursachen (Phytophotodermatitis).

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 7; 8; 9 | `species.pruning_months` |

Hinweis: Ab Mitte Juli die aeusseren, aelteren Blaetter abbrechen (nicht schneiden -- Bruchstelle heilt besser). Dies foerdert die Knollenentwicklung. Seitenwurzeln an der Knollenoberseite regelmaeassig abschneiden, damit die Knolle glatt und rund waechst. Nie mehr als 1/3 der Blaetter auf einmal entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (tiefe, grosse Gefaesse noetig fuer Knollenentwicklung; Ertrag im Topf deutlich geringer) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15--20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--50 (Blattrosette) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 35--40 | `species.spacing_cm` |
| Indoor-Anbau | no (sehr lange Kulturzeit, hoher Lichtbedarf, kein Indoor-Gemuese) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur in sehr grossen Kuebeln, Ertrag bescheiden) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (fuer die Vorkulturphase; Freilandkultur ab Mai) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgruendige, nahrstoffreiche, humose Erde mit guter Wasserhaltefaehigkeit. Keine Staunaesse. Lehmig-humoser Boden ideal. pH 6.0--7.0. | -- |

**Hinweis:** Knollensellerie ist ein anspruchsvolles Gemuese mit langer Kulturzeit (180--200 Tage). Der Boden muss mindestens 30 cm tief gelockert sein. Gleichmaessige Wasserversorgung ist entscheidend -- Trockenheit fuehrt zu holzigen, rissigen Knollen. Flacher Anbau: Die Knolle waechst zur Haelfte ueber der Erde, NICHT mit Erde anhaeufeln (im Gegensatz zu Kartoffel).

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 14--28 | 1 | false | false | low |
| Saemling (seedling) | 42--56 (lange Jungpflanzenphase bis Mai!) | 2 | false | false | low |
| Vegetativ (vegetative) | 60--90 (Blattrosetten-Aufbau, Knollenbeginn) | 3 | false | true (Blaetter) | medium |
| Knollenbildung (Vegetativ spaet) | 60--90 (Hauptknollenwachstum) | 4 | false | true | medium |
| Ernte (harvest) | 1--14 | 5 | true | true | high |

Hinweis: Die Phaseneinteilung bei Knollensellerie ist vereinfacht. Die Knollenbildung beginnt ca. 10--12 Wochen nach der Pflanzung und setzt sich bis zum Frost fort. Es gibt keine echte Bluetephase im 1. Kulturjahr (Bluete nur im 2. Jahr nach Vernalisation, was unerwuenscht ist).

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50--100 (Lichtkeimer!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3--6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--22 (konstant! NICHT unter 16 degC) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--20 (NICHT unter 16 degC) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht, nie nass) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--10 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 (NICHT unter 10 degC -- Schoss-Gefahr!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 (NICHT unter 10 degC) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

ACHTUNG: Die Jungpflanzenphase ist die kritischste Phase. Temperaturen unter 10 degC fuer laengere Zeit (>10 Tage) loesen Vernalisation aus und die Pflanze wird im 1. Jahr schossen (Bluete statt Knollenbildung). Abhaertung vorsichtig durchfuehren -- Temperaturen nie unter 12 degC, idealerweise nur tagsueeber bei 15+ degC.

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (volle Sonne bis leichter Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (gleichmaessig feucht! Trockenheit fuehrt zu holzigen Knollen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Knollensellerie hat einen sehr hohen Wasserbedarf. Gleichmaessige Bodenfeuchte ist entscheidend. Trockenheit fuehrt zu Hohlraumen in der Knolle und holziger Textur. Mulchen mit Rasenschnitt oder Stroh hilft, die Feuchtigkeit zu halten.

#### Phase: Knollenbildung (vegetative spaet)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 (natuerlich abnehmend im Spaetsommer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 14--20 (kuehle Temperaturen foerdern Knollenentwicklung) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (weiterhin gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 300--600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Ab Mitte Juli aeussere Blaetter entfernen und Seitenwurzeln an der Knollenoberseite abschneiden. Dies foerdert eine glatte, runde Knolle. Kaliumdüungung betonen (Beinwelljauche, Patentkali) fuer Geschmack und Lagerfaehigkeit.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 5.8--6.5 | 80 | 30 | 20 | 2 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 5.8--6.5 | 150 | 50 | 40 | 4 |
| Knollenbildung | 2-1-4 | 1.8--2.4 | 5.8--6.5 | 180 | 60 | 50 | 4 |
| Ernte | 0-0-0 | 0.0 | -- | -- | -- | -- | -- |

Hinweis: Knollensellerie ist ein Starkzehrer mit besonders hohem Kalium- und Calciumbedarf waehrend der Knollenbildung. Bor-Mangel fuehrt zu Herzfaeule (braune, hohle Stellen im Knolleninneren) -- bei Verdacht Bor-Blattduengung durchfuehren (Borax 0.1% Loesung). Stickstoff ab August reduzieren, um die Knollenreife und Lagerfaehigkeit zu foerdern.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 14--28 Tage | Keimblaetter voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 42--56 Tage (Mai, Auspflanzung nach Eisheiligen) | 4--6 echte Blaetter, kraeftige Pflanze, Temperaturen stabil ueber 12 degC |
| Vegetativ -> Knollenbildung | time_based | 60--90 Tage nach Pflanzung (Juli/August) | Knolle sichtbar ueber der Erde, Durchmesser ca. 3--5 cm |
| Knollenbildung -> Ernte | manual / event_based | 60--90 Tage (September--November) | Knolle hat Erntereife erreicht (10--15 cm Durchmesser), vor starkem Frost ernten |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Saemling, Vegetativ |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10 | 5 | Knollenbildung |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (grosszuegig einarbeiten) | heavy_feeder |
| Gut verrotteter Rindermist | div. | organisch | 3--5 L/m2 | Herbst (einarbeiten) | heavy_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 60--80 g/m2 | Fruehjahr (Einarbeitung) | heavy_feeder |
| Kalimagnesia (Patentkali) | div. | mineralisch-organisch | 40--50 g/m2 | Juni/Juli (zur Knollenbildung) | heavy_feeder |
| Bio Tomatendunger (fluessig) | COMPO BIO | organisch | 30--40 ml / 10 L Giesswasser | Mai--August, alle 14 Tage | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 1 L/Pflanze | Juli--September, alle 14 Tage | heavy_feeder (Knollenentwicklung) |
| Borax-Loesung | div. | Spurenelement | 0.1% Loesung, Blattspruehung | Juni, einmalig | alle (Bor-Mangel-Praevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Knollensellerie Standard Hydro")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--4 | Saemling | 0.3--0.5 | 6.0 | 0.2 | 0.3 | 0.3 | Nur Wasser erste 14 Tage; Temperatur nicht unter 16 degC |
| 5--8 | Saemling spaet | 0.6--1.0 | 5.8--6.2 | 0.3 | 0.5 | 0.5 | EC langsam steigern |
| 9--14 | Vegetativ | 1.4--2.0 | 5.8--6.2 | 0.4 | 0.8 | 0.8 | Volle Dosierung |
| 15--22 | Knollenbildung | 1.8--2.4 | 5.8--6.2 | 0.5 | 0.8 (Bloom) | 0.8 (Bloom) | K betonen, N leicht reduzieren |
| 23+ | Spaetphase | 1.4--1.8 | 6.0 | 0.4 | 0.6 | 0.6 | N weiter reduzieren fuer Lagerfaehigkeit |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Flora Micro (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Flora Gro / Flora Bloom (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer!** Knollensellerie gehoert zu den anspruchsvollsten Gemuesearten. Grosszuegige Grundduengung mit Kompost und Mist ist essenziell.
- **Bor-Mangel beachten:** Herzfaeule (braune, hohle Stellen im Knolleninneren) ist ein klassisches Bor-Mangelsymptom. Praeventive Bor-Blattduengung im Juni empfohlen.
- **Kalium fuer Knollenqualitaet:** Ab Knollenbeginn K-Versorgung erhoehen (Beinwelljauche, Patentkali). K verbessert Geschmack, Festigkeit und Lagerfaehigkeit.
- **Calcium durchgehend:** Gleichmaessige Ca-Versorgung verhindert Schwarzherz (Calcium-Mangelkrankheit). Gleichmaessiges Giessen ist ebenso wichtig wie die Ca-Duengung selbst.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 (gleichmaessig feucht! hoher Wasserbedarf) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (Ernte vor Winter; Lagerung bei 0--2 degC) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Morgens giessen, moeglichst direkt an die Wurzel. Gleichmaessige Wasserversorgung ist der Schluessel zu guter Knollenqualitaet. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig/zweijaehrig, kein Umtopfen nach Pflanzung) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | -- | -- | -- |
| Feb | Aussaat starten | Ab Mitte Februar: Aussaat in Schalen bei 20--22 degC, Lichtkeimer! Temperaturen NICHT unter 16 degC | hoch |
| Marz | Pikieren | Saemlinge nach 2. echtem Blattpaar in Einzeltoepfe (6--8 cm), Temperatur weiterhin ueber 12 degC halten | hoch |
| Apr | Jungpflanzen pflegen | Gute Belichtung, gleichmaessig giessen, NICHT abhaerten unter 12 degC (Schoss-Gefahr!) | hoch |
| Mai | Auspflanzen | Nach Eisheiligen (ca. 15.05.) ins Freiland, Pflanzabstand 35--40 cm, FLACH pflanzen (Knolle ueber der Erde) | hoch |
| Jun | Wachstum foerdern | Regelmaessig giessen und duengen, mulchen, Bor-Blattspruehung | hoch |
| Jul | Blaetter + Seitenwurzeln entfernen | Aeussere Blaetter abbrechen, Seitenwurzeln an Knollenoberseite abschneiden | hoch |
| Aug | Knollenwachstum | Weiter gleichmaessig giessen und duengen; K betonen, N reduzieren | hoch |
| Sep | Erntebeginn | Erste Knollen ernten bei Bedarf; Haupternte Oktober/November | mittel |
| Okt | Haupternte | Knollen mit Grabgabel vorsichtig aus dem Boden heben, VOR starkem Frost ernten | hoch |
| Nov | Lagerung | Blaetter auf ca. 5 cm kuerzen, Knollen in feuchtem Sand bei 0--2 degC lagern (haelt 4--6 Monate) | hoch |
| Dez | Lager kontrollieren | Gelagerte Knollen regelmaessig auf Faeulnis pruefen | niedrig |

### 4.3 Ueberwinterung

Knollensellerie wird vor dem Winter geerntet und eingelagert. Ausgewachsene Pflanzen vertragen leichte Froeste bis ca. -5 degC, sollten aber vor staerkerem Frost geerntet werden. Lagerung: Blaetter bis auf 5 cm kuerzen, Knollen in feuchtem Sand in einem kuehlen (0--2 degC), dunklen Raum (Erdkeller) lagern. Haltbarkeit: 4--6 Monate.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Selleriefliege (Celery Fly) | Euleia heraclei (syn. Acidia heraclei) | Miniergaenge in Blaettern (Blaetter werden braun und welken), Larven im Blattgewebe | leaf | vegetative | medium |
| Moehrenfliege (Carrot Fly) | Psila rosae | Frassgaenge in Wurzeln/Knollen, braune Gaenge, Pflanze kuemmert | root | vegetative | hard |
| Blattlaeuse (Aphids) | Aphis spp. | Gekraeuselte Blaetter, Honigtau, Wuchshemmung | leaf | vegetative | easy |
| Schnecken (Slugs/Snails) | Arion spp. | Lochfrass an Blaettern und Knollenansatz | leaf, root | seedling, vegetative | easy |
| Wanzen (Capsid Bug) | Lygus spp. | Deformierte Blaetter, kleine braune Einstichstellen | leaf | vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Septoria-Blattfleckenkrankheit | fungal | Gelbe bis braune Flecken mit schwarzen Pyknidien (Punkten) auf Blaettern und Stielen | warm_wet_conditions, seed_contamination | 10--14 | vegetative |
| Cercospora-Blattfleckenkrankheit | fungal | Runde, braune Flecken mit dunklem Rand auf Blaettern | high_humidity, warm_temps | 7--14 | vegetative |
| Schorf (Scab) | fungal | Raue, korkartige Flecken auf Knollenoberflaeche | high_humidity, waterlogging | 14--21 | vegetative (spaet) |
| Herzfaeule (Heart Rot) | physiological | Braune, hohle Stellen im Knolleninneren (nur bei Ernte sichtbar) | boron_deficiency | -- | vegetative (spaet) |
| Schwarzherz (Black Heart) | physiological | Schwarze Verfaerbung im Knolleninneren | calcium_deficiency, uneven_watering | -- | vegetative (spaet) |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Kulturschutznetz | Selleriefliege, Moehrenfliege | 1 Netz/Beet | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz (0.8 mm) | cultural | -- | Netz ueber Bestand spannen, Mai--September | 0 | Selleriefliege, Moehrenfliege |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen, im Restmuell entsorgen | 0 | Septoria, Cercospora |
| Heisswasser-Saatgutbehandlung | cultural | -- | Saatgut 30 Min. bei 48 degC in Wasser | 0 | Septoria (samenbuertige Infektion) |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Borax-Blattspruehung | cultural | Bor | 0.1% Loesung, einmalig im Juni | 0 | Herzfaeule (Praevention) |
| Gleichmaessig giessen | cultural | -- | Nie austrocknen lassen, Mulchschicht | 0 | Schwarzherz, holzige Knollen |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Septoria-Blattfleckenkrankheit | Krankheit | Cultivare wie 'Monarch', 'President' (tolerant) | `resistant_to` |
| Schossen (Bolting Resistance) | Stress | Cultivare wie 'Mars', 'Monarch' (schossfest) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Doldenblueuter (Apiaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) oder Gruenduengung |
| Empfohlene Nachfrucht | Mittel- oder Schwachzehrer (Salat, Radieschen, Spinat) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Apiaceae auf gleicher Flaeche (inkl. Moehre, Petersilie, Fenchel, Pastinake, Dill) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Lauch / Porree | Allium porrum | 0.9 | Klassische Mischkultur; Lauch vertreibt Selleriefliege, Sellerie vertreibt Lauchmotte | `compatible_with` |
| Kohl (alle Arten) | Brassica oleracea | 0.8 | Sellerie-Duft schreckt Kohlweisslinge ab, unterschiedliche Wurzeltiefen | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Sellerie-Duft vertreibt Weisse Fliege an Tomaten | `compatible_with` |
| Buschbohne | Phaseolus vulgaris | 0.8 | N-Fixierung, gute Platzausnutzung | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.7 | Allium-Duft schreckt Selleriefliege ab | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Schnelle Zwischenkultur, Bodenbeschattung | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Gute Platzausnutzung, aehnlicher Wasserbedarf | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Moehre | Daucus carota | Gleiche Familie (Apiaceae), geteilte Schaedlinge (Moehrenfliege, Selleriefliege), Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Petersilie | Petroselinum crispum | Gleiche Familie, geteilte Krankheiten (Septoria) | moderate | `incompatible_with` |
| Pastinake | Pastinaca sativa | Gleiche Familie, geteilte Schaedlinge und Krankheiten | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Starke Naehrstoffkonkurrenz (beide Starkzehrer), Platzbedarf | mild | `incompatible_with` |
| Kopfsalat | Lactuca sativa | Schnecken werden angezogen, Wachstumshemmung beobachtet | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Apiaceae (mit sich selbst) | `shares_pest_risk` | Septoria, Cercospora, Selleriefliege (Euleia heraclei), Moehrenfliege (Psila rosae) | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Knollensellerie |
|-----|-------------------|-------------|------------------------------|
| Stangensellerie (Bleichsellerie) | Apium graveolens var. dulce | Gleiche Art, andere Nutzung (Stiele statt Knolle) | Kuerzere Kulturzeit, einfacherer Anbau |
| Schnittsellerie (Blattsellerie) | Apium graveolens var. secalinum | Gleiche Art, Blatternte | Sehr einfacher Anbau, schnelle Ernte, mehrfach schneidbar |
| Petersilie (Wurzelpetersilie) | Petroselinum crispum var. tuberosum | Gleiche Familie, Wurzelgemuese | Kuerzere Kulturzeit, weniger anspruchsvoll |
| Pastinake | Pastinaca sativa | Gleiche Familie, Wurzelgemuese | Frosthaerter, lagerfaehiger, weniger anspruchsvoll |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,harvest_months,sowing_indoor_weeks_before_last_frost
Apium graveolens var. rapaceum,Knollensellerie;Wurzelsellerie;Zeller;Celeriac;Turnip-rooted Celery,Apiaceae,Apium,biennial,long_day,herb,tuberous,5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.1,"Europa, Mittelmeerraum, Vorderasien",moderate,heavy_feeder,false,edible;aromatic,9;10;11,10
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Prager Riesen,Apium graveolens var. rapaceum,,,large_root;heirloom,180,,open_pollinated
Monarch,Apium graveolens var. rapaceum,,,disease_resistant;smooth_skin;compact,190,septoria,open_pollinated
Mars,Apium graveolens var. rapaceum,,,bolt_resistant;smooth_skin,185,,open_pollinated
President,Apium graveolens var. rapaceum,,,disease_resistant;high_yield,190,septoria,f1_hybrid
Diamant,Apium graveolens var. rapaceum,,,smooth_skin;white_flesh,185,,open_pollinated
Knollensellerie (Pötschke Historisch),Apium graveolens var. rapaceum,Pötschke,,heirloom;aromatic,190,,open_pollinated
```

---

## Quellenverzeichnis

1. samen.de -- Knollensellerie Bewaesserung und Duengung: https://samen.de/blog/optimale-bewaesserung-und-duengung-fuer-gesunden-knollensellerie.html
2. samen.de -- Knollensellerie Anbau: https://samen.de/blog/knollensellerie-vom-anbau-zur-ertragreichen-ernte.html
3. samen.de -- Knollensellerie schuetzen: https://samen.de/blog/knollensellerie-schuetzen-krankheiten-und-schaedlinge-erkennen.html
4. samen.de -- Knollensellerie in Mischkultur: https://samen.de/blog/knollensellerie-in-mischkultur-ertragreich-und-gesund.html
5. grove.eco -- Knollensellerie: https://www.grove.eco/pflanzen/apium-graveolens-rapaceum/
6. garten-wissen.com -- Knollensellerie: https://www.garten-wissen.com/pflanzen/knollensellerie/
7. gartenratgeber.net -- Knollensellerie Pflege: https://www.gartenratgeber.net/pflanzen/knollensellerie-pflanzen-anbau-und-pflege-im-garten.html
8. plantura.garden -- Knollensellerie: https://www.plantura.garden/gemuese/sellerie/knollensellerie
9. pflanzenkrankheiten.ch -- Septoria: https://www.pflanzenkrankheiten.ch/krankheiten-an-kulturpflanzen-2/gemuese-offcanvas/sellerie-menu-offcanvas/septoria-apiicola
10. bioaktuell.ch -- Blattfleckenkrankheit bei Sellerie: https://www.bioaktuell.ch/pflanzenbau/gemuesebau/blattfleckenkrankheit-bei-sellerie
11. ponicslife.com -- Hydroponic Celery: https://ponicslife.com/hydroponic-celery-a-quick-and-easy-grow-guide/
12. hydrobuilder.com -- Hydroponic Celery: https://hydrobuilder.com/learn/hydroponic-celery/
