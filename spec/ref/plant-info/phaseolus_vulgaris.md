# Gartenbohne -- Phaseolus vulgaris

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, NCSU Extension, Purdue University, Gardenia.net, Plantura, fryd.app, Gardener's Path, Gardening Know How, PlantVillage, Seed Savers Exchange, Old Farmer's Almanac

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Phaseolus vulgaris | `species.scientific_name` |
| Volksnamen (DE/EN) | Gartenbohne; Gruene Bohne; Buschbohne; Stangenbohne; Fisole; Common Bean; French Bean; Green Bean; Snap Bean | `species.common_names` |
| Familie | Fabaceae | `species.family` -> `botanical_families.name` |
| Gattung | Phaseolus | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (die meisten modernen Sorten; einige tropische Landsorten sind kurztagsempfindlich) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, stirbt bei Temperaturen unter 2 degC ab. Keimt erst ab 10 degC Bodentemperatur (optimal 18--22 degC). In Mitteleuropa Freiland-Kultur Mitte Mai bis September/Oktober. | `species.hardiness_detail` |
| Heimat | Mittel- und Suedamerika (Mexiko, Guatemala, Anden) | `species.native_habitat` |
| Allelopathie-Score | -0.2 (positiver Effekt auf Nachfolgekultur durch N-Fixierung) | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light | `species.nutrient_demand_level` |
| Gruenduengung geeignet | true (hervorragende Vorfrucht, Stickstoff-Fixierung ueber Knollchenbakterien, Wurzelrueckstaende bereichern den Boden) | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 2--3 (moeglich, aber Direktsaat bevorzugt; Bohnen vertragen Verpflanzen schlecht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0--14 (ab Bodentemperatur 10 degC, optimal 15 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6; 7 (Staffelsaat alle 3--4 Wochen bis Mitte Juli fuer Buschbohnen) | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy (grosse Samen, einfache Direktsaat, schnelle Keimung) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 18--25 degC
- Minimale Keimtemperatur: 10 degC (unter 10 degC faulen die Samen in nasser Erde)
- Keimdauer: 5--10 Tage
- **Dunkelkeimer** -- Samen 3--5 cm tief in die Erde druecken
- Bohnen NICHT vorquellen (Erstickungsgefahr der Samen, Faeulnis)
- Reihenabstand: 40--50 cm (Buschbohne), 60--80 cm (Stangenbohne)
- In der Reihe: 5--8 cm (Buschbohne), 10--15 cm (Stangenbohne, an Stange)
- Stangenbohnen: Rankhilfe (2 m Stangen, Wigwam, Netz) VOR der Saat aufstellen
- Bohnen-Saatgut NICHT in nassen, kalten Boden saeen -- Faeulnis ist die haeufigste Ursache fuer Auflaufprobleme
- Impfung mit Rhizobium-Bakterien kann bei erstmaligem Anbau die N-Fixierung verbessern

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (Phasin/Phytohaemagglutinin in rohen Bohnen) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (Phasin/Phytohaemagglutinin in rohen Bohnen) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true (rohe Bohnen giftig! Bereits 5--6 rohe Bohnen koennen bei Kindern schwere Vergiftung ausloesen) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | fruit (roh: Samen und Huelsen); leaf (roh) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Phasin (Phytohaemagglutinin / PHA, ein Lektin); Blausaeureverbindungen (in manchen Sorten) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (roh: Uebelkeit, Erbrechen, Durchfall, Bauchkraempfe 1--3 Stunden nach Verzehr; bei grossen Mengen: Hospitalisierung noetig; 10 Minuten Kochen zerstoert Phasin vollstaendig) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WARNUNG: Rohe Bohnen sind giftig!** Das Lektin Phasin (Phytohaemagglutinin) wird erst durch mindestens 10 Minuten Kochen bei 100 degC vollstaendig zerstoert. Niemals roh essen! Einweichwasser wegschuetten. Kinder, Katzen und Hunde besonders gefaehrdet. In Deutschland 13 Krankenhauseinweisungen von Kindern in 5 Jahren dokumentiert.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Kein Rueckschnitt noetig. Bei Stangenbohnen: Triebspitze kappen, wenn die Pflanze die Stange ueberragt (ca. 2--2.5 m), um die Energie in die Fruchtbildung umzulenken. Nach der Ernte: Pflanzen abschneiden, Wurzeln im Boden belassen (Knollchenbakterien + Stickstoff fuer Nachfolgekulturen).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Buschbohnen moeglich in 10--15 L Kuebel; Stangenbohnen brauchen sehr grosse Gefaesse + stabile Rankhilfe) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--15 (Buschbohne, 3--4 Pflanzen/Topf); 20--30 (Stangenbohne) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 (Buschbohne); 25 (Stangenbohne) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--50 (Buschbohne); 200--300 (Stangenbohne) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20--35 (Buschbohne); 30--50 (Stangenbohne am Spalier) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40--50 Reihenabstand (Buschbohne), 60--80 (Stangenbohne) | `species.spacing_cm` |
| Indoor-Anbau | no (hoher Lichtbedarf, Bestaeubung, Platzanspruch) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Buschbohnen im Kuebel moeglich; Stangenbohnen nur mit stabilem Spalier) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freilandkultur optimal; Gewaechshaus nur fuer sehr fruehe Saetze sinnvoll) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false (Buschbohne); true (Stangenbohne: 2--2.5 m Stangen, Netz, Wigwam) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlaessige, humose Gemuese-Erde. Nicht zu naehrstoffreich (N-Fixierung!). pH 6.0--6.8. Keine schweren Tonboeden. | -- |

**Hinweis:** Bohnen sind ideal fuer Anfaenger -- schnelle Keimung, unkomplizierte Kultur, zuverlaessige Ernte. Buschbohnen sind kompakter und ernten frueher (50--60 Tage), Stangenbohnen tragen laenger und ertragreicher (60--90 Tage). "Drei Schwestern" (Mais + Bohne + Kuerbis) ist die klassische indigene Mischkultur.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--10 | 1 | false | false | low |
| Saemling (seedling) | 10--14 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--35 | 3 | false | false | medium |
| Bluete (flowering) | 7--14 | 4 | false | false | low |
| Ernte (harvest) | 21--42 | 5 | true | true | medium |

Hinweis: Bohnen wachsen schnell -- Buschbohnen koennen schon 50--60 Tage nach Aussaat geerntet werden. Stangenbohnen brauchen 60--90 Tage. Die Bluetephase ist kurz aber kritisch -- Hitze ueber 30 degC und Trockenheit verursachen Bluetenabwurf. Regelmaessiges Ernten verlaengert die Erntephase erheblich.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer, Samen 3--5 cm tief) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--25 (optimal 22; unter 10 degC: Faeulnis!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65--80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70--85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (maessig feucht, NICHT nass!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Bohnen faulen leicht in nasser, kalter Erde. NICHT vorquellen. Boden muss abgetrocknet und erwaermt sein (mind. 10 degC, besser 15 degC).

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (Freiland, volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich (mind. 12--15 mol/m2/d) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (14--16 h im Fruehsommer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (volle Sonne, mind. 6 h) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich (mind. 15--20 mol/m2/d) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (14--16 h) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--28 (optimal 24) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (maessig, Bohnen sind relativ trockentolerant) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Bohnen sind in der vegetativen Phase genuegsam. Stickstoff-Duengung ist kontraproduktiv -- foerdert ueppiges Laub auf Kosten der Huelsenbildung. Die Knollchenbakterien fixieren genug N aus der Luft.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich (mind. 15--20 mol/m2/d) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (14--16 h) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--28 (ACHTUNG: ueber 30 degC = Bluetenabwurf!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (in der Bluete erhoehter Wasserbedarf!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Die Bluetephase ist die kritischste! Hitze ueber 30 degC, Trockenheit und kalte Naechte unter 12 degC fuehren zu Bluetenabwurf (Abszission). Gleichmaessig giessen, morgens, nicht ueber die Blueten. Bohnen sind Selbstbestaeuber -- Insektenbestaeubung erhoet aber den Ertrag.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 80--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: REGELMAESSIG ERNTEN! Alle 2--3 Tage kontrollieren und pfluckreife Huelsen ernten. Wenn Samen in der Huelsse sichtbar werden (Ausbeulung), ist die Bohne ueberreif und faseriger. Ueberreife Huelsen an der Pflanze hemmen Neuansatz massiv. Morgens ernten (knackiger). Huelsen vorsichtig abknipsen oder abdrehen -- Pflanze nicht beschaedigen.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.8 | -- | -- | -- | -- |
| Saemling | 0-1-1 | 0.3--0.5 | 6.0--6.5 | 50 | 25 | 20 | 2 |
| Vegetativ | 0-1-2 | 0.4--0.8 | 6.0--6.5 | 80 | 35 | 25 | 2 |
| Bluete | 0-2-3 | 0.6--1.0 | 6.0--6.5 | 100 | 40 | 30 | 3 |
| Ernte | 0-1-2 | 0.4--0.8 | 6.0--6.5 | 80 | 35 | 25 | 2 |

Hinweis: Bohnen als Stickstoff-Fixierer (Knollchenbakterien/Rhizobien an den Wurzeln) brauchen KEINEN Stickstoff-Duenger. N-Duengung ist sogar schaedlich -- die Pflanze stellt die N-Fixierung ein und produziert ueppiges Laub statt Huelsen. Phosphor und Kalium foerdern Blute + Huelsenbildung.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--10 Tage | Keimblaetter (gross, fleischig) ueber Erdoberflaeche |
| Saemling -> Vegetativ | time_based | 10--14 Tage | Erste Fiederblatter (Dreiblatt) voll entfaltet |
| Vegetativ -> Bluete | time_based / event_based | 21--35 Tage (Buschbohne frueher, Stangenbohne spaeter) | Erste Bluetenknospen in den Blattachseln sichtbar |
| Bluete -> Ernte | time_based | 7--14 Tage nach Bluetebeginn | Erste Huelsen erreichen Erntelaenge (8--15 cm je Sorte) |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Organisch (Outdoor/Beet -- Standardkultur)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 | Fruehjahr (Einarbeitung vor Saat) | light (N-Fixierer) |
| Kalimagnesia (Patentkali) | K+S | mineralisch-natuerlich | 30--50 g/m2 | Fruehjahr (Einarbeitung) | light (N-Fixierer) |
| Gesteinsmehl (Basalt/Diabas) | Oscorna / div. | mineralisch-natuerlich | 100--150 g/m2 | Fruehjahr | alle (Spurenelemente) |
| Holzasche (unbehandelt) | Eigenerzeugung | mineralisch-natuerlich (K-betont) | 30--50 g/m2 | Herbst | light (N-Fixierer) |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 0.5 L/m2 | Juli--August, alle 21 Tage | light (N-Fixierer, K fuer Huelsenbildung) |

Hinweis: KEINEN Stickstoff-Duenger verwenden! Die Knollchenbakterien (Rhizobium leguminosarum) an den Bohnenwurzeln fixieren atmosphaerischen Stickstoff. Nur P + K + Spurenelemente zuführen.

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Bohne Standard Freiland")

| Zeitpunkt | Phase | Massnahme | Hinweise |
|-----------|-------|-----------|----------|
| Vor Saat (April/Mai) | Vorbereitung | 2--3 L/m2 Kompost + 30--50 g/m2 Patentkali einarbeiten | KEIN Stickstoff-Duenger! |
| Bei Saat (Mai) | Keimung | Ggf. Rhizobium-Impfmittel auf Saatgut | Bei erstmaligem Bohnenanbau auf der Flaeche empfohlen |
| Bluete (Juni/Juli) | Bluete | Ggf. 1x Beinwelljauche (K-Boost) | Nur bei sichtbarem Kaliummangel (Blattrandnekrose) |
| Nach Ernte | Nachkultur | Bohnenwurzeln im Boden belassen! | N-Anreicherung fuer Nachfolgekultur (Starkzehrer!) |

### 3.3 Mischungsreihenfolge

Bohnen im Freiland benoetigen in der Regel keine Fluessigduenger-Mischungen. Bei der seltenen Hydrokultur:

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag (falls noetig)
3. Basis-Naehrloesungs A (Ca, Mikro) -- KEIN oder minimaler N-Anteil!
4. Basis-Naehrloesungs B (P, K, S, Mg)
5. pH-Korrektur -- IMMER als letzter Schritt

### 3.4 Besondere Hinweise zur Duengung

- **Stickstoff-Fixierer!** Bohnen sind die klassische Gruenduengung im Gemuesebau. Die Knollchenbakterien (Rhizobium) binden 50--100 kg N/ha aus der Atmosphaere.
- **N-Duengung ist schaedlich:** Stickstoff-Duengung unterdrueckt die symbiotische N-Fixierung und foerdert Laubwachstum auf Kosten der Huelsen.
- **P + K genuegen:** Phosphor foerdert die Wurzelentwicklung und Bluete, Kalium die Huelsenbildung und -qualitaet.
- **Wurzeln im Boden lassen!** Nach der Ernte die Pflanzen abschneiden (nicht ausreissen) -- die Wurzeln mit ihren N-reichen Knoellchen bleiben im Boden und ernaehren die Nachfolgekultur.
- **pH 6.0--6.8:** Bohnen bevorzugen leicht saure bis neutrale Boeden. In sauren Boeden funktioniert die Rhizobium-Symbiose schlecht.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--4 (maessig, Bohnen sind relativ trockentolerant; in Bluete: 2 Tage) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Maessig giessen, Staunaesse vermeiden (Wurzelfaeule!). In der Bluete regelmaessiger giessen. Morgens giessen, nicht ueber Blaetter/Blueten (Grauschimmel, Rost). Bohnen vertragen kurze Trockenheit besser als Staunaesse. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | -- (Grundduengung genügt; N-Fixierung!) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (Direktsaat, kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Apr | Beetvorbereitung | Boden lockern, Kompost + Patentkali einarbeiten, Rankhilfe fuer Stangenbohnen aufstellen | hoch |
| Mai | Erste Aussaat | Ab Mitte Mai (nach Eisheiligen), Bodentemperatur mind. 10 degC, 3--5 cm tief | hoch |
| Jun | Zweite Saat (Staffel) + Pflege | Staffelsaat Buschbohnen, Anhaeufeln (5--8 cm Erde an Staengelbasis = Standfestigkeit + zusaetzliche Wurzeln) | hoch |
| Jul | Erntebeginn + Dritte Saat | Erste Buschbohnen erntereif, letzte Staffelsaat Buschbohnen (Mitte Juli), alle 2--3 Tage ernten | hoch |
| Aug | Haupternte | Alle 2--3 Tage ernten! Stangenbohnen-Ernte beginnt, Bohnenrost kontrollieren | hoch |
| Sep | Nachernte | Letzte Ernte, Duengung einstellen | mittel |
| Okt | Saisonende | Pflanzen abschneiden (Wurzeln im Boden lassen!), Beet fuer Nachkultur vorbereiten | mittel |

### 4.3 Ueberwinterung

Nicht anwendbar -- Gartenbohne ist eine einjaehrige Pflanze und ueberlebt keinen Frost. Trockene Bohnensamen koennen kuehl und trocken gelagert werden (Keimfaehigkeit 3--4 Jahre).

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schwarze Bohnenlaus (Black Bean Aphid) | Aphis fabae | Dichte Kolonien an Triebspitzen, Honigtau, Virusuebertraeger | leaf, stem, flower | vegetative, flowering | easy |
| Bohnenkaefer (Bean Weevil) | Acanthoscelides obtectus | Loecher in getrockneten Bohnen (Lagerschaedling) | fruit (Samen) | harvest (Lagerung) | easy |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, gelb-bronzefarbene Blaetter | leaf | vegetative | medium |
| Schnecken (Slugs/Snails) | Arion spp. | Frass an Keimblaettern und jungen Pflanzen | leaf, stem | seedling | easy |
| Bohnenfliege (Bean Fly) | Delia platura | Larven fressen an Keimblaettern unter der Erde, Auflaufprobleme | root, stem | seedling | difficult |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Flecken auf Blaettern, Bluetenschaeden | leaf, flower | flowering | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Bohnenrost (Bean Rust) | fungal | Rosbraune Pusteln auf Blattunterseite, Blattverlust | high_humidity, warm_temps | 7--14 | vegetative, flowering |
| Grauschimmel (Botrytis) | fungal | Grauer pelziger Belag auf Huelsen und Blaettern | high_humidity, cool_temps, poor_airflow | 3--7 | flowering, harvest |
| Anthraknose (Colletotrichum) | fungal | Runde braun-schwarze eingesunkene Flecken auf Huelsen und Blaettern | rain_splash, contaminated_seed | 5--10 | vegetative, harvest |
| Fettfleckenkrankheit (Halo Blight) | bacterial | Wassergetränkte Flecken mit gelbem Hof auf Blaettern | cool_wet, rain_splash, contaminated_seed | 5--10 | vegetative |
| Bohnenmosaikvirus (BCMV) | viral | Mosaikmuster, Blattdeformation, Zwergwuchs | seed_transmission, aphid_vectors | 14--21 | alle |
| Wurzelfaeule (Fusarium Root Rot) | fungal | Pflanze welkt, braune Wurzeln, Staengelbasis verfaerbt | overwatering, cold_wet_soil | 7--14 | seedling, vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Schwarze Bohnenlaus | 5--10 | 14 |
| Coccinella septempunctata (Marienkaefer) | Schwarze Bohnenlaus | 5--10 | 7--14 |
| Aphidius ervi (Schlupfwespe) | Schwarze Bohnenlaus | 2--5 | 14--21 |
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |
| Schneckenkorn (Ferramol) | Schnecken | 5 g/m2 | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Schwarze Bohnenlaus, Spinnmilbe |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Bohnenlaus |
| Netzschwefel | biological | Schwefel | Spruehung 0.2%, alle 7--10 Tage | 7 | Bohnenrost |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen, 5 g/m2 | 0 | Schnecken |
| Triebspitzen entfernen | cultural | -- | Befallene Triebspitzen (Blattlaus-Kolonien) abschneiden und entsorgen | 0 | Schwarze Bohnenlaus |
| Fruchtfolge + Hygiene | cultural | -- | 3 Jahre Anbaupause fuer Fabaceae, Saatgut-Gesundheit pruefen | 0 | Anthraknose, Fettflecken, Fusarium |
| Bohnenkraut als Begleitpflanze | cultural | -- | Bohnenkraut neben Bohnen pflanzen | 0 | Schwarze Bohnenlaus (traditionell) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Bohnenmosaikvirus (BCMV) | Krankheit | Viele moderne Sorten (z.B. 'Provider', 'Contender') | `resistant_to` |
| Anthraknose (Colletotrichum) | Krankheit | Cultivare wie 'Tendergreen Improved' | `resistant_to` |
| Bohnenrost (Uromyces) | Krankheit | Einige Cultivare (z.B. 'Kentucky Blue Pole') | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light; N-Fixierung ueber Rhizobium-Symbiose reduziert externen N-Bedarf) |
| Fruchtfolge-Kategorie | Huelsenfruechte (Fabaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kohl, Tomate, Kartoffel) -- Bohne als Regenerator nach Starkzehrern |
| Empfohlene Nachfrucht | Starkzehrer (Kohl, Tomate, Kartoffel) -- profitieren vom fixierten Stickstoff |
| Anbaupause (Jahre) | 3 Jahre fuer Fabaceae (Bohne, Erbse, Lupine) auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.9 | Klassische "Drei Schwestern"! Mais = Rankhilfe fuer Stangenbohne, Bohne fixiert N fuer Mais | `compatible_with` |
| Kuerbis / Zucchini | Cucurbita spp. | 0.9 | "Drei Schwestern"-Dritte: Bodenbeschattung, Unkrautunterdrueckung | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Bohne fixiert N, Gurke profitiert; Bohne lockert den Boden | `compatible_with` |
| Kartoffel | Solanum tuberosum | 0.8 | Bohne fixiert N, Kartoffelkraut beschattet Boden; Kartoffelkaefer meidet Bohnen | `compatible_with` |
| Sellerie | Apium graveolens | 0.7 | Aehnliche Standortansprueche, Sellerie vertreibt Bohnenkaefer | `compatible_with` |
| Bohnenkraut (Sommer) | Satureja hortensis | 0.9 | Traditionelle Begleitpflanze! Schwarze Bohnenlaus-Abwehr, kulinarische Ergaenzung | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr, Schaedlingsabwehr | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.7 | Gute Raumausnutzung (schnelle Ernte bevor Bohne Platz braucht) | `compatible_with` |
| Radieschen | Raphanus sativus | 0.7 | Reihenmarkierung, schnelle Ernte, Bodenlockerung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Zwiebel | Allium cepa | Allium-Ausscheidungen hemmen Knollchenbakterien, reduzieren N-Fixierung | moderate | `incompatible_with` |
| Knoblauch | Allium sativum | Wie Zwiebel -- hemmt Rhizobium-Symbiose | moderate | `incompatible_with` |
| Lauch | Allium porrum | Wie Zwiebel -- hemmt Rhizobium-Symbiose | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Gleiche Familie -- gemeinsame Krankheiten (Fusarium, BCMV), Konkurrenz um Rhizobium-Staemme | mild | `incompatible_with` |
| Sonnenblume | Helianthus annuus | Allelopathie (Sonnenblumen-Wurzelausscheidungen hemmen Bohnen) | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Fabaceae (mit sich selbst) | `shares_pest_risk` | Fusarium, Anthraknose, BCMV, Bohnenrost, Bohnenfliege | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Standard-Gartenbohne |
|-----|-------------------|-------------|------------------------------|
| Feuerbohne (Prunkbohne) | Phaseolus coccineus | Gleiche Gattung, Stangenbohne | Kaeltevertraeglicher, dekorative rote Blueten, mehrjaehrig moeglich |
| Ackerbohne (Dicke Bohne) | Vicia faba | Gleiche Familie | Viel kaeltevertraeglicher (Fruehjahrsaussaat Maerz!), hohes Protein |
| Spargelbohne (Yardlong Bean) | Vigna unguiculata ssp. sesquipedalis | Gleiche Familie, sehr lang | Extrem ertragreiche Stangenbohne, waermeliebend, dekorativ |
| Edamame (Sojabohne) | Glycine max | Gleiche Familie | Eiweissreicher, andere Verwendung |
| Augenbohne (Black-Eyed Pea) | Vigna unguiculata | Gleiche Familie | Hitze- und trockenheitstoleranter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Phaseolus vulgaris,Gartenbohne;Gruene Bohne;Buschbohne;Stangenbohne;Fisole;Common Bean;French Bean;Green Bean;Snap Bean,Fabaceae,Phaseolus,annual,day_neutral,herb,fibrous,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b,-0.2,"Mittel- und Suedamerika (Mexiko, Guatemala, Anden)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Buschbohne (generisch),Phaseolus vulgaris,,,high_yield;compact,55,,open_pollinated
Stangenbohne (generisch),Phaseolus vulgaris,,,high_yield;long_season,70,,open_pollinated
Provider,Phaseolus vulgaris,,,disease_resistant;early_maturing;compact,50,bcmv,open_pollinated
Contender,Phaseolus vulgaris,,,disease_resistant;high_yield;compact,55,bcmv;powdery_mildew,open_pollinated
Blauhilde,Phaseolus vulgaris,,,ornamental;high_yield;heirloom,65,,open_pollinated
Neckarkoenigin,Phaseolus vulgaris,,,high_yield;heirloom,65,,open_pollinated
Saxa,Phaseolus vulgaris,,,early_maturing;compact;heirloom,50,,open_pollinated
Kentucky Blue Pole,Phaseolus vulgaris,,1991,disease_resistant;high_yield,65,bean_rust,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA -- Phaseolus vulgaris Toxizitaet: Nicht als Art in der ASPCA-Datenbank gelistet; Phasin-Toxizitaet aus CFS Hong Kong + Cornell University Poison Plants
2. Cornell University -- Lectins Toxic Agents: https://poisonousplants.ansci.cornell.edu/toxicagents/lectins.html
3. CFS Hong Kong -- Phytohaemagglutinin Poisoning: https://www.cfs.gov.hk/english/multimedia/multimedia_pub/multimedia_pub_fsf_208_01.html
4. NCSU Extension -- Phaseolus vulgaris: https://plants.ces.ncsu.edu/plants/phaseolus-vulgaris/
5. Purdue University -- Phaseolus vulgaris: https://hort.purdue.edu/newcrop/duke_energy/Phaseolus_vulgaris.html
6. Gardenia.net -- Phaseolus vulgaris Green Beans: https://www.gardenia.net/plant/phaesolus-vulgaris-green-beans
7. Gardener's Path -- Bean Companion Plants: https://gardenerspath.com/plants/vegetables/bean-companion-plants/
8. PlantVillage -- Bean Diseases and Pests: https://plantvillage.psu.edu/topics/bean/infos
9. Seed Savers Exchange -- Growing Beans: https://shop.seedsavers.org/site/pdf/grow-save-beans.pdf
10. Old Farmer's Almanac -- Beans: https://www.almanac.com/plant/green-beans
11. Gardening Know How -- Common Bean Problems: https://www.gardeningknowhow.com/edible/vegetables/beans/information-on-common-bean-problems-tips-on-growing-beans.htm
