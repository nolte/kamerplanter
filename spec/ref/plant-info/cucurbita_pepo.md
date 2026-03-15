# Zucchini -- Cucurbita pepo

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** bio-gaertner.de, grove.eco, samen.de, fryd.app, Hortipendium, plantura.garden, gartenjournal.net, beetliebe.de, kiepenkerl.de, sperli.de, ResearchGate, ScienceDirect, igworks.com, Food Safety News

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cucurbita pepo | `species.scientific_name` |
| Volksnamen (DE/EN) | Zucchini; Gartenküuerbis; Courgette; Zucchini Squash; Summer Squash | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` -> `botanical_families.name` |
| Gattung | Cucurbita | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (Tagesneutral -- Bluete weitgehend unabhaengig von der Taglaenge, primaer temperatur- und altersgesteuert) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, stirbt bei ersten Nachtfroesten ab. Mindesttemperatur fuer Wachstum ca. 10 degC. In Mitteleuropa einjaehrig kultiviert (Freiland Mitte Mai--Oktober). | `species.hardiness_detail` |
| Heimat | Mittelamerika, Mexiko (domestiziert vor ca. 7.000--10.000 Jahren) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; high_yield | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3--4 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (erst bei Bodentemperatur > 15 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 | `species.direct_sow_months` |
| Erntemonate | 6; 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8; 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Zucchini werden ausschliesslich generativ ueber Samen vermehrt. Sehr einfache und zuverlaessige Keimung. ACHTUNG bei Saatgutgewinnung: Cucurbita-Arten kreuzen sich leicht untereinander (Bienen-Fremdbestaeubung mit Zierküuerbissen). Hybride koennen giftige Cucurbitacine bilden! Nur Saatgut von kontrollierten, isolierten Bestaaeubungen oder zertifiziertem Saatgut verwenden.

**Keimhinweise:**
- Optimale Keimtemperatur: 22--25 degC (Heizmatte empfohlen)
- Minimale Keimtemperatur: 15 degC (sehr langsame Keimung)
- Keimdauer: 7--14 Tage (bei optimaler Temperatur 5--8 Tage)
- **Dunkelkeimer** -- Samen 2--3 cm mit Erde bedecken
- Samen einzeln in Toepfe (8--10 cm) oder 2 Samen pro Topf (schwaecheren Keimling entfernen)
- Substrat: naehrstoffarme Aussaaterde, gleichmaessig feucht, warm
- Saemlinge nicht pikieren (empfindliche Wurzeln) -- direkt in Einzeltoepfe saeen

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false (normale Kulturzucchini) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false (normale Kulturzucchini) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (normale Kulturzucchini) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | fruit (NUR bei Cucurbitacin-haltigen Exemplaren -- bitter schmeckende Fruechte!) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Cucurbitacine (nur bei Rueckkreuzung mit Wildformen oder Zierküerbissen; normale Kulturzucchini sind cucurbitacin-frei) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (bei Cucurbitacin-Vergiftung: heftiges Erbrechen, Durchfall, Kolikschmerzen; selten toedlich) | `species.toxicity.severity` |
| Kontaktallergen | true (Blatthare koennen Kontaktdermatitis ausloesen bei empfindlichen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG Cucurbitacin-Vergiftung:** Wenn Zucchini extrem bitter schmecken, NICHT essen! Bittere Zucchini koennen toedliche Mengen Cucurbitacin enthalten. Ursache: unkontrollierte Kreuzung mit Zierküerbissen (Bienen-Fremdbestaeubung) oder Stressreaktion. Immer VOR dem Kochen ein kleines Stueck roh probieren -- bei Bitterkeit sofort entsorgen. Cucurbitacine werden durch Kochen NICHT zerstoert.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | -- (kein Rueckschnitt ueblich) | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Zucchini werden normalerweise nicht zurueckgeschnitten. Abgestorbene oder mehltaubefallene Blaetter werden laufend entfernt, um die Luftzirkulation zu verbessern. Bei sehr wuechsigen Pflanzen koennen aeltere, bodennahe Blaetter entfernt werden. Fruechte regelmaessig ernten (bei 15--25 cm Laenge), um Fruchtansatz und Ertrag zu foerdern.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (sehr grosse Pflanzen, mind. 40 L Topfvolumen; Kompaktsorten besser geeignet) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40--60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 40--80 (buschig; Rankformen bis 200) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100--150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80--100 | `species.spacing_cm` |
| Indoor-Anbau | no (zu gross, zu lichtbeduerftig, Bestaeubung noetig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Kompaktsorten in grossen Kuebeln; Handbestaeubung oft noetig) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (fruehere Ernte, waermer, Bestaeubung durch Hummeln oder Hand) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false (Buschtypen); true (Ranktypen/Kletterformen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose Gartenerde oder Kuebelpflanzenerde. Schwerer, lehmhaltiger Boden wird toleriert. Gute Drainage, aber hohe Wasserspeicherfaehigkeit. pH 6.0--7.0. | -- |

**Hinweis:** Zucchini sind wahre Ertragsmonster -- eine einzige Pflanze kann 5--15 kg Fruechte pro Saison liefern. Pflanzabstand nicht unterschaetzen (mind. 80 cm). Bestaeubung durch Insekten (Bienen, Hummeln) notwendig; bei schlechtem Fruchtansatz Handbestaeubung durchfuehren (maennliche Bluete abzupfen und auf weibliche Bluete druecken). Maennliche Blueten haben duenne Stiele, weibliche haben eine kleine Frucht am Stiel.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--14 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--35 | 3 | false | false | medium |
| Bluete (flowering) | 60--90 (Dauertraeger -- bluet und fruchtet gleichzeitig) | 4 | false | true | medium |
| Seneszenz (senescence) | 7--14 (nach erstem Frost oder Erschoepfung) | 5 | true | false | low |

Hinweis: Zucchini sind Dauertraeger -- nach Beginn der Bluete bilden sich laufend neue Blueten und Fruechte ueber die gesamte Saison (Indeterminate Growth). Regelmaessiges Ernten der Fruechte bei 15--25 cm Laenge ist entscheidend fuer anhaltenden Ertrag. Ueberreife Fruechte (>30 cm) signalisieren der Pflanze, die Fruchtproduktion einzustellen.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | -- (Dunkelkeimer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 (optimal 25) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--600 (volle Sonne, lichtbeduerftig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 (optimal 25) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Zucchini sind extrem wuchskraeftig und bilden in kurzer Zeit grosse Blattflaechen. Ausreichend Wasser und Naehrstoffe sind in dieser Phase entscheidend.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (hoher Wasserbedarf bei Fruchtbildung!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--2000 (grosse Pflanzen mit vielen Fruechten benoetigen bis zu 2L/Tag) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Während der Fruchtbildung ist der Wasser- und Naehrstoffbedarf am hoechsten. Ungleichmaessige Wasserversorgung fuehrt zu Bluetenendfaeule (Calcium-Mangel durch gestörte Transpiration) und deformierten Fruechten.

#### Phase: Seneszenz (senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -- (natuerlich, Herbst) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -- | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | -- (kein Giessen mehr noetig) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | -- | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Nach dem ersten Frost stirbt die Pflanze ab. Pflanzenreste kompostieren (nur bei gesunden Pflanzen; mehltaubefallene Reste in den Restmuell).

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.6--1.0 | 5.8--6.5 | 80 | 30 | 20 | 2 |
| Vegetativ | 3-1-2 | 1.6--2.2 | 5.8--6.5 | 150 | 50 | 40 | 4 |
| Bluete/Frucht | 2-3-4 | 2.0--2.8 | 5.8--6.5 | 180 | 60 | 50 | 4 |
| Seneszenz | 0-0-0 | 0.0 | -- | -- | -- | -- | -- |

Hinweis: Zucchini sind echte Starkzehrer und benoetigen durchgehend hohe Naehrstoffversorgung. Calcium ist besonders wichtig waehrend der Fruchtbildung -- Calciummangel fuehrt zu Bluetenendfaeule (braune, eingesunkene Stelle am Bluetenende der Frucht). EC ueber 3.0 mS vermeiden (Salztoxizitaet).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--14 Tage | Keimblaetter (Kotyledonen) voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 2--3 echte Blattpaare, kraeftiger Stiel |
| Vegetativ -> Bluete | time_based | 21--35 Tage nach Keimung (ca. 35--50 Tage nach Aussaat) | Erste Blueten sichtbar (maennliche Blueten erscheinen zuerst) |
| Bluete -> Seneszenz | event_based | Nach erstem Frost oder Erschoepfung der Pflanze | Blaetter welken, Fruchtansatz stoppt |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Aqua Flores A | Canna | base | 4-0-3 | 0.16 | 3 | Bluete/Frucht |
| Aqua Flores B | Canna | base | 0-4-3 | 0.14 | 4 | Bluete/Frucht |
| PK 13/14 | Canna | booster | 0-13-14 | 0.08 | 5 | Fruchtansatz |

Hinweis: Volle Herstellerdosierung verwenden (Starkzehrer).

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (grosszuegig einarbeiten) | heavy_feeder |
| Gut verrotteter Rindermist | div. | organisch | 3--5 L/m2 | Herbst/Fruehjahr (einarbeiten) | heavy_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 60--80 g/m2 | Fruehjahr (Einarbeitung) | heavy_feeder |
| Bio Tomatendunger (fluessig) | COMPO BIO | organisch | 30--40 ml / 10 L Giesswasser | Juni--September, alle 14 Tage | heavy_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 1 L/Pflanze | Juni--August, alle 14 Tage | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 1 L/Pflanze | Juli--September, alle 14 Tage | heavy_feeder (Fruchtbildung) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Zucchini Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--2 | Saemling | 0.5--0.8 | 6.0 | 0.3 | 0.4 | 0.4 | Nur Wasser erste 5 Tage |
| 3--4 | Saemling/Veg | 1.0--1.4 | 5.8--6.0 | 0.4 | 0.7 | 0.7 | EC zuegig steigern |
| 5--7 | Vegetativ | 1.6--2.2 | 5.8--6.2 | 0.5 | 1.0 | 1.0 | Volle Dosierung |
| 8--10 | Bluete/Frucht | 2.0--2.8 | 5.8--6.2 | 0.5 | 1.0 (Flores A) | 1.0 (Flores B) | Umstellen auf Blueteduenger, CalMag betonen |
| 11+ | Dauerertrag | 2.0--2.6 | 5.8--6.2 | 0.5 | 0.8 | 0.8 | Stabile Versorgung ueber gesamte Fruchtphase |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Flores A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Flores B (Phosphor + Schwefel + Magnesium)
5. PK-Booster (falls eingesetzt, z.B. PK 13/14)
6. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer!** Zucchini benoetigen von allen Kuechengewaechsen eine der hoechsten Naehrstoffversorgungen. Grosszuegig Kompost und organischen Dunger einarbeiten.
- **Calcium gegen Bluetenendfaeule:** Ca-Mangel (oder gestorte Ca-Aufnahme durch unregelmaessiges Giessen) fuehrt zum klassischen Problem der Bluetenendfaeule. CalMag IMMER zufuegen, gleichmaessig giessen.
- **Kalium fuer Fruchtqualitaet:** Ab Fruchtbeginn K-Versorgung erhoehen (Beinwelljauche, Patentkali, Holzasche).
- **Organische Duengung bevorzugt:** Zucchini gedeihen hervorragend auf gut kompostiertem Mistbeet. Klassischer "Kuuerbis-Huegel" auf verrottendem Material ist optimal.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 (hoher Wasserbedarf!) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Zimmerwarmes Wasser bevorzugt. Morgens giessen, direkt an den Wurzelbereich (nicht ueber Blaetter -- Mehltaugefahr). 1--2 L/Pflanze/Tag bei Fruchtbildung. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig, kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | -- | -- | -- |
| Feb | -- | -- | -- |
| Marz | -- | -- | -- |
| Apr | Vorkultur starten | Ab Mitte April: Aussaat einzeln in 8--10 cm Toepfe bei 22--25 degC auf Heizmatte | hoch |
| Mai | Abhaertung + Auspflanzen | 7--10 Tage abhaerten, nach Eisheiligen (ca. 15.05.) auspflanzen, Pflanzabstand 80--100 cm, Pflanzloch mit Kompost fuellen | hoch |
| Jun | Wachstum + Erste Ernte | Kraeftig giessen und duengen; erste Ernte ca. 5--6 Wochen nach Pflanzung; Fruechte bei 15--25 cm Laenge ernten | hoch |
| Jul | Haupternte | Alle 2--3 Tage ernten; auf Echten Mehltau achten; Blaetter mit Befall entfernen | hoch |
| Aug | Ernte + Mehltau-Management | Mehltau nimmt oft zu -- befallene Blaetter entfernen, Pflanze weiterkultivieren; Kaliumbicarbonat spruehen | hoch |
| Sep | Spaeternte | Letzte Ernte vor dem Frost; reife Fruechte fuer Saatgut ausreifen lassen (nur samenfeste Sorten!) | mittel |
| Okt | Saisonende | Pflanze nach erstem Frost raeumen, Reste kompostieren (nur gesunde Pflanzen) | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar -- Zucchini ist eine einjaehrige, frostempfindliche Nutzpflanze und stirbt beim ersten Frost ab.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaeuse (Aphids) | Aphis gossypii, Myzus persicae | Gekraeuselte Blaetter, Honigtau, Russtau, Virenuebertragung (Gurkenmosaikvirus) | leaf, stem, flower | vegetative, flowering | easy |
| Schnecken (Slugs/Snails) | Arion spp., Deroceras spp. | Lochfrass an Blaettern und jungen Fruechten, Schleimspuren | leaf, fruit | seedling, vegetative | easy |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Silbrige Punkte auf Blattunterseite, feine Gespinste | leaf | vegetative, flowering | medium |
| Weisse Fliege (Whitefly) | Trialeurodes vaporariorum | Weisse Fliegen an Blattunterseite, Honigtau | leaf | vegetative, flowering | easy |
| Minierfliege | Liriomyza spp. | Weisse Gaenge in Blaettern | leaf | vegetative | medium |
| Wuehlmaus (Vole) | Microtus arvalis | Angefressene Wurzeln und Stengelbasis, Pflanze kippt um | root, stem | vegetative, flowering | hard |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau (Powdery Mildew) | fungal | Weisser, mehliger Belag auf Blattoberseite und -unterseite, Blaetter vergilben und trocknen ein | warm_dry_conditions, temp_swing | 5--10 | vegetative, flowering |
| Grauschimmel (Grey Mold) | fungal | Grauer, pelziger Belag auf Fruechten und Blaettern, besonders an Verletzungsstellen | high_humidity, cool_temps, poor_airflow | 3--5 | flowering |
| Gurkenmosaikvirus (Cucumber Mosaic Virus) | viral | Mosaikartige Blattverfaerbung (gelb-gruen), Blaetter verkrueppelt, Wuchshemmung | aphid_transmission | 7--14 | vegetative, flowering |
| Bluetenendfaeule (Blossom End Rot) | physiological | Braune, eingesunkene Stelle am Bluetenende der Frucht | calcium_deficiency, uneven_watering | -- | flowering |
| Stengelfaeule / Schwarzbeinigkeit (Damping Off) | fungal | Saemling knickt an Basis um | overwatering, cold_wet_soil | 2--5 | seedling |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Coccinella septempunctata (Marienkaefer) | Blattlaeuse | 5--10 | 7--14 |
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |
| Encarsia formosa | Weisse Fliege | 3--5 | 21--28 |
| Steinernema feltiae (Nematode) | Trauermuecke (Bodenstadien) | 250.000/m2 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage, 3x wiederholen | 0 | Blattlaeuse, Weisse Fliege, Spinnmilbe |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Weisse Fliege |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau |
| Milch-Wasser-Loesung | cultural | Milchsaeurebakterien | 1:9 Milch:Wasser, Spruehung alle 3--5 Tage | 0 | Echter Mehltau (praeventiv) |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Mulchschicht (Stroh) | cultural | -- | 5--10 cm Strohmulch um Pflanzen | 0 | Schnecken (Barriere), Feuchtigkeitserhalt, Unkrautunterdrueckung |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen bei Mehltau, im Restmuell entsorgen | 0 | Echter Mehltau, Grauschimmel |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Echter Mehltau | Krankheit | Cultivare wie 'Partenon F1', 'Ismalia F1', 'Mastil F1' (tolerant, nicht vollstaendig resistent) | `resistant_to` |
| Gurkenmosaikvirus (CMV) | Krankheit | Cultivare wie 'Defender F1' (tolerant) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Kuerbisgewaechse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae), Gruenduengung, oder Lauchgewaechse |
| Empfohlene Nachfrucht | Mittel- oder Schwachzehrer (Salat, Moehren, Radieschen) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Cucurbitaceae auf gleicher Flaeche (inkl. Gurke, Kuerbis, Melone) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.9 | Klassische Milpa-Kultur; Mais als Windschutz, Zucchini als Bodendecker | `compatible_with` |
| Stangenbohne | Phaseolus vulgaris | 0.9 | Milpa-Triade; N-Fixierung, Mais als Rankhilfe fuer Bohne | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.8 | Insektenabwehr, gleiche Waermebeduerfnisse | `compatible_with` |
| Borretsch | Borago officinalis | 0.8 | Lockt Bestaeauber an, verbessert Fruchtansatz | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Fangpflanze fuer Blattlaeuse, lockt Bestauber an | `compatible_with` |
| Sellerie | Apium graveolens | 0.7 | Unterschiedliche Wurzeltiefen | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Schnelle Ernte vor der Zucchini-Ausbreitung, Bodenbeschattung | `compatible_with` |
| Zwiebel | Allium cepa | 0.7 | Schaedlingsabwehr durch aetherische Oele | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Gurke | Cucumis sativus | Gleiche Familie, geteilte Krankheiten (Mehltau, CMV), Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Starke Naehrstoffkonkurrenz (beide Starkzehrer), Kartoffelkaefer | moderate | `incompatible_with` |
| Tomate | Solanum lycopersicum | Naehrstoffkonkurrenz (beide Starkzehrer), Platzbedarf | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Cucurbitaceae (mit sich selbst) | `shares_pest_risk` | Echter Mehltau, Gurkenmosaikvirus (CMV), Blattlaeuse, Spinnmilben | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Zucchini |
|-----|-------------------|-------------|------------------------------|
| Patisson (Ufo-Kuerbis) | Cucurbita pepo var. patisson | Gleiche Art, flache Fruchtform | Dekorativer, dichteres Fruchtfleisch |
| Rondini (Kugelzucchini) | Cucurbita pepo 'Tondo' | Gleiche Art, runde Fruchtform | Kompakter Wuchs, ideal fuer Fuellungen |
| Spaghettiküuerbis | Cucurbita pepo subsp. pepo | Gleiche Art, faseriges Fruchtfleisch | Lagerfaehig, low-carb-Alternative zu Pasta |
| Butternut | Cucurbita moschata | Gleiche Familie, birnenfoermig | Lagerfaehig (Winterküuerbis), suesseres Aroma |
| Gurke | Cucumis sativus | Gleiche Familie, aehnliche Kultur | Andere Verwendung (roh/Salat), kompakterer Wuchs |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,direct_sow_months,harvest_months,bloom_months,sowing_indoor_weeks_before_last_frost,sowing_outdoor_after_last_frost_days
Cucurbita pepo,Zucchini;Gartenküuerbis;Courgette;Summer Squash,Cucurbitaceae,Cucurbita,annual,day_neutral,vine,fibrous,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a,0.0,"Mittelamerika, Mexiko",tender,heavy_feeder,false,edible;high_yield,5;6,6;7;8;9;10,6;7;8;9,3
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Black Beauty,Cucurbita pepo,,,dark_green;high_yield;compact,50,,open_pollinated
Defender F1,Cucurbita pepo,,,disease_resistant;parthenocarp;early_maturing,47,cucumber_mosaic_virus,f1_hybrid
Partenon F1,Cucurbita pepo,,,parthenocarp;disease_resistant,47,powdery_mildew,f1_hybrid
Ismalia F1,Cucurbita pepo,Kiepenkerl,,disease_resistant;high_yield,50,powdery_mildew,f1_hybrid
Romanesco,Cucurbita pepo,,,ribbed;italian_type;ornamental,55,,open_pollinated
Tondo di Nizza,Cucurbita pepo,,,round_fruit;compact;italian_type,45,,open_pollinated
Zuboda (Pötschke Historisch),Cucurbita pepo,Pötschke,,heirloom;high_yield,55,,open_pollinated
```

---

## Quellenverzeichnis

1. bio-gaertner.de -- Zucchini: https://www.bio-gaertner.de/pflanzen/zucchini
2. grove.eco -- Zucchini: https://www.grove.eco/pflanzen/cucurbita-pepo-pepo-giromontina/
3. samen.de -- Zucchini-Anbau: https://samen.de/blog/zucchini-anbau-tipps-fuer-reiche-ernte.html
4. fryd.app -- Zucchini pflanzen: https://fryd.app/magazin/zucchini-pflanzen-anzucht-pflege-ernte
5. Hortipendium -- Zucchini Pflanzenschutz: https://hortipendium.de/Zucchini_Pflanzenschutz
6. plantura.garden -- Zucchini pflegen: https://www.plantura.garden/gemuese/zucchini/zucchini-pflegen
7. gartenjournal.net -- Zucchini Krankheiten: https://www.gartenjournal.net/zucchini-krankheiten-schaedlinge
8. beetliebe.de -- Zucchini vorziehen: https://www.beetliebe.de/blog/zucchini-vorziehen/
9. kiepenkerl.de -- Zucchini Kulturanleitung: https://www.kiepenkerl.de/kulturanleitungen/zucchini/
10. ResearchGate -- Response of Zucchini to EC: https://www.researchgate.net/publication/276139259
11. Food Safety News -- Cucurbitacin Poisoning: https://www.foodsafetynews.com/2024/11/scientists-highlight-zucchini-poisoning-case/
12. igworks.com -- Hydroponic Squash and Zucchini: https://igworks.com/blogs/growing-guides/growing-hydroponic-squash-and-zucchini
