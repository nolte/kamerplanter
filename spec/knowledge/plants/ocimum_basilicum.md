# Basilikum -- Ocimum basilicum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** ASPCA, RHS, UMN Extension, Plantura, Koppert, fryd.app, Hortipendium, Upstart Farmers, Johnny's Seeds, NCSU Extension, Samen.de

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ocimum basilicum | `species.scientific_name` |
| Volksnamen (DE/EN) | Basilikum; Basil; Koenigskraut; Sweet Basil | `species.common_names` |
| Familie | Lamiaceae | `species.family` -> `botanical_families.name` |
| Gattung | Ocimum | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day (Kurztagspflanze -- Bluetenbildung durch Kurztag ausgeloest; lange Sommertage verzoegern Bluete und verlaengern die vegetative Erntephase) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, stirbt bei Temperaturen unter 5 degC ab. In Mitteleuropa einjaehrig kultiviert (Freiland Mai--September) oder ganzjaehrig auf der Fensterbank/im Gewaechshaus. | `species.hardiness_detail` |
| Heimat | Tropisches Asien (Indien, Suedostasien) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6--8 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (erst nach Bodentemperatur > 15 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 | `species.direct_sow_months` |
| Erntemonate | 6; 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 7; 8; 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Basilikum laesst sich sehr einfach aus Stecklingen (Triebspitzen 8--10 cm, untere Blaetter entfernen) in Wasser oder feuchtem Substrat bewurzeln. Bewurzelung innerhalb von 7--14 Tagen.

**Keimhinweise:**
- Optimale Keimtemperatur: 20--25 degC (Heizmatte empfohlen)
- Minimale Keimtemperatur: 12 degC (sehr langsame, ungleichmaessige Keimung)
- Keimdauer: 5--10 Tage
- **Lichtkeimer** -- Samen nur leicht andruecken, NICHT mit Erde bedecken
- Hohe Luftfeuchtigkeit foerderlich: Abdeckung mit Klarsichtfolie oder Haube (taeglich lueften)
- Substrat: naehrstoffarme Aussaaterde, gleichmaessig feucht, Staunaesse vermeiden (Umfallkrankheit!)

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
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA Animal Poison Control listet Ocimum basilicum als ungiftig fuer Katzen und Hunde. Achtung: Basilikum-aetherisches Oel (konzentriert) kann fuer Katzen problematisch sein -- hier geht es nur um die frische Pflanze.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7; 8; 9 | `species.pruning_months` |

Hinweis: Regelmaessiges Ernten/Entspitzen ueber den Blattknoten foerdert buschigen Wuchs und verzoegert die Bluete. Bluetenstaende immer sofort entfernen (Pinzieren), da nach der Bluete die Blattqualitaet (Aromaoele) deutlich abnimmt und die Pflanze seneszent wird.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (klassische Topf- und Fensterbankpflanze) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20--35 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25--30 | `species.spacing_cm` |
| Indoor-Anbau | yes (sonnige Fensterbank, ganzjaehrig moeglich; Zusatzbelichtung im Winter empfohlen) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (sonniger, windgeschuetzter Standort) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (optimale Waerme und Lichtverhaeltnisse) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, durchlaessige Kraeutererde. Staunaesse unbedingt vermeiden (Umfallkrankheit, Wurzelfaeule). Drainage am Topfboden wichtig. | -- |

**Hinweis:** Basilikum ist eine der beliebtesten Topfkraeuter und ideal fuer Fensterbank, Balkon und Kuechennaehe. Supermarkt-Basilikum ist fuer sofortigen Verbrauch gezuechtet (zu dicht gesaet) -- fuer laengere Kultur die Pflanzen teilen oder aus Samen/Stecklingen ziehen. Mindestens 6 Stunden direkte Sonne taeglich. Im Topf regelmaessig giessen, aber Staunaesse vermeiden.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--10 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 28--56 | 3 | false | true | medium |
| Bluete (flowering) | 14--28 | 4 | false | true | medium |
| Seneszenz (senescence) | 7--14 | 5 | true | false | low |

Hinweis: Die vegetative Phase ist die produktivste Erntephase. Durch konsequentes Entspitzen kann die Bluete um Wochen verzoegert werden. Sobald die Bluete einsetzt, sinkt der Gehalt an aetherischen Oelen in den Blaettern.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50--100 (Lichtkeimer!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3--6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 (optimal 25) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht, nie nass) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (optimal 250) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Basilikum reagiert empfindlich auf Staunaesse (Fusarium, Pythium). Substrat muss gut drainiert sein. Temperatur unter 12 degC verursacht Wachstumsstopp und Blattverfaerbungen.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 (Kurztagspflanze -- kuerzere Tage foerdern Bluete; lange Tage verzoegern sie) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--800 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Wenn die Pflanze auf Saatgutgewinnung kultiviert wird, Bluete zulassen. Fuer Blatternten: Bluetenstaende konsequent entfernen.

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
| Giessintervall (Tage) | 2--3 (reduziert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 (stark reduziert) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Blatternten in der Seneszenz lohnen nicht -- Aromagehalt ist stark reduziert, Blaetter werden duenn und gelblich. Saatgut von reifen Bluetenstaenden sammeln (braun und trocken), Pflanze danach entfernen. Bei Topfkultur Substrat kompostieren.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.4--0.8 | 5.8--6.2 | 60 | 30 | 20 | 2 |
| Vegetativ | 3-1-2 | 1.0--1.4 | 5.8--6.2 | 100 | 40 | 30 | 3 |
| Bluete | 2-2-2 | 1.0--1.4 | 5.8--6.2 | 80 | 40 | 30 | 2 |
| Seneszenz | 0-0-0 | 0.0 | 6.0 | -- | -- | -- | -- |

Hinweis: Basilikum ist ein Schwachzehrer -- uebermaessige Stickstoffduengung fuehrt zu schnellem Wachstum mit duennen Blaettern und reduziertem Aromaoelgehalt (bis zu 28% weniger aetherische Oele bei Ueberduengung). EC ueber 1.6 mS vermeiden. pH unter 5.8 verursacht Eisen/Mangan-Toxizitaet (braune bis schwarze Flecken an den Blattrandern).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--10 Tage | Keimblaetter (Kotyledonen) voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 2--3 echte Blattpaare, kraeftiger Stiel |
| Vegetativ -> Bluete | time_based / event_based | 28--56 Tage (Kurztagreaktion -- kuerzer werdende Tage im Spaetsommer foerdern Bluete) | Erste Bluetenansaetze an den Triebspitzen sichtbar |
| Bluete -> Seneszenz | time_based | 14--28 Tage nach Bluetebeginn | Samenkapseln reifen, Blattqualitaet sinkt deutlich |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Hakaphos Gruen 20-5-10 | COMPO Expert | base | 20-5-10 | ~0.15 | 3 | Vegetativ |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |

Hinweis: Fuer Basilikum reichen halbe Dosen im Vergleich zu Starkzehrern wie Tomate. Lieber unterdosieren als ueberdosieren.

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Kraeuterdunger (fluessig) | COMPO BIO | organisch | 15--25 ml / 10 L Giesswasser | Mai--September, alle 14--21 Tage | light_feeder |
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 | Fruehjahr (Einarbeitung bei Pflanzung) | alle |
| Wurmkompost-Tee | Eigenerzeugung | organisch | 1:5 verduennt, 0.5 L/m2 | Mai--August, alle 14 Tage | light_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 30--50 g/m2 | Fruehjahr (Einarbeitung) | light_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:20 verduennt, 0.5 L/m2 | Juni--August, alle 21 Tage | light_feeder |
| Schachtelhalmbruehe | Eigenerzeugung | Pflanzenhilfsmittel | 1:5 verduennt, Blattpruehung | Mai--September, alle 14 Tage | alle (Pilzpraevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Basilikum Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--2 | Saemling | 0.3--0.5 | 5.8 | 0.2 | 0.3 | 0.3 | Nur Wasser erste 5 Tage nach Keimung |
| 3--4 | Saemling/Veg | 0.6--0.8 | 5.8--6.0 | 0.3 | 0.5 | 0.5 | EC langsam steigern |
| 5--8 | Vegetativ | 1.0--1.4 | 5.8--6.0 | 0.3 | 0.7 | 0.7 | Halbe Dosierung gegenueber Starkzehrern |
| 9--12 | Vegetativ (Ernte) | 1.0--1.2 | 5.8--6.0 | 0.3 | 0.6 | 0.6 | Regelmaessiges Entspitzen und Ernten |
| 13+ | Spaetphase | 0.8--1.0 | 6.0 | 0.2 | 0.5 | 0.5 | Bei Bluetenansatz: EC leicht reduzieren |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Vega A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Schwachzehrer!** Basilikum benoetigt deutlich weniger Naehrstoffe als Tomate oder Paprika. Ueberduengung ist haeufiger als Unterduengung und fuehrt zu waerigem, aromarmem Kraut.
- **Ammonium-Stickstoff vermeiden:** Zu viel NH4-N foerdert uebertriebenes Blattwachstum, reduziert die aetherische Oelproduktion um bis zu 28% und verschlechtert den Geschmack.
- **Eisen-/Mangan-Toxizitaet bei niedrigem pH:** Bei pH unter 5.8 werden Fe und Mn uebermaessig verfuegbar -- Symptom: braune bis schwarze Blattrandnekrosen. pH regelmaessig kontrollieren.
- **Organische Topfkultur:** Bio-Kraeuterdunger alle 2--3 Wochen genuegt. Schachtelhalmbruehe als Blattspruehung beugt Falschem Mehltau vor (Kieselsaeure festigt die Zellwaende).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | herb_tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege; bei Fensterbank-Kultur: 2.0) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Zimmerwarmes Wasser (18--22 degC) bevorzugt. Morgens giessen, nie ueber die Blaetter (Pilzgefahr). Substrat darf zwischen Giessen leicht abtrocknen -- Staunaesse ist der haeufigste Pflegefehler. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14--21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4; 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; bei Fensterbank-Kultur: 3--4 Monate nach Kauf umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | -- | -- (Freiland: keine Aktivitaet; Indoor: laufende Pflege) | -- |
| Feb | -- | -- | -- |
| Marz | Vorkultur starten | Aussaat in Schalen bei 22--25 degC auf Heizmatte, Lichtkeimer: Samen nur andruecken | hoch |
| Apr | Pikieren / Umtopfen | Saemlinge in Einzeltoepfe (9 cm), nach 2. echtem Blattpaar | hoch |
| Mai | Abhaertung + Auspflanzen | 7--10 Tage abhaerten, nach Eisheiligen (ca. 15.05.) ins Freiland oder auf Balkon, Pflanzabstand 25--30 cm | hoch |
| Jun | Erntebeginn + Entspitzen | Regelmaessig Triebspitzen ernten (immer ueber einem Blattpaar schneiden), Bluetenansaetze entfernen | hoch |
| Jul | Haupternte | Groesste Erntephase, regelmaessig ernten = buschiger Wuchs, Schachtelhalmbruehe spruehen (Mehltau-Praevention) | hoch |
| Aug | Ernte + Schaedlingskontrolle | Auf Falschen Mehltau achten (Blattoberseite gelbe Flecken, Unterseite grau-violetter Belag), Blattlaeuse kontrollieren | hoch |
| Sep | Letzte Ernte / Saatgut | Letzte Ernte vor dem ersten Kalteinbruch, ggf. Saatgut von Bluetenstaenden sammeln | mittel |
| Okt | Saisonende | Pflanzen raeumen, Substrat kompostieren, Saatgut trocknen und lagern | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar -- Basilikum ist eine einjaehrige Nutzpflanze und ueberlebt keine Temperaturen unter 5 degC. Ganzjahreskultur nur indoor (Fensterbank, Gewaechshaus) unter kuenstlicher Belichtung moeglich.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaeuse (Aphids) | Myzus persicae, Aphis gossypii | Gekraeuselte Blaetter, Honigtau, Russtau, Wuchshemmung | leaf, stem | vegetative, flowering | easy |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, silbrige Punkte auf Blattunterseite, Blattverfaerbung | leaf | vegetative | medium |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Flecken, verkrueppelte junge Blaetter | leaf | vegetative, flowering | medium |
| Weisse Fliege (Whitefly) | Trialeurodes vaporariorum | Honigtau, weisse Fliegen an Blattunterseite, Russtau | leaf | vegetative, flowering | easy |
| Schnecken (Slugs/Snails) | Arion spp., Deroceras spp. | Lochfrass, Schleimspuren, bevorzugt junge Pflanzen | leaf, stem | seedling, vegetative | easy |
| Minierfliege (Leafminer) | Liriomyza spp. | Weisse Miniergaenge in Blaettern | leaf | vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau (Downy Mildew) | fungal (Oomycet) | Gelbe Flecken auf Blattoberseite, grau-violetter Sporenrasen auf Blattunterseite, Blattverlust | high_humidity, poor_airflow, cool_nights | 5--10 | vegetative, flowering |
| Fusarium-Welke (Fusarium Wilt) | fungal | Einseitige Blattwelke, Staengel verbräunt/abgeschnuert an Basis, Pflanze kippt um | warm_wet_soil, soil_contamination | 10--21 | seedling, vegetative |
| Grauschimmel (Grey Mold) | fungal | Grauer pelziger Belag auf Staengeln und Blaettern | high_humidity, poor_airflow, cool_temps | 3--5 | vegetative, flowering |
| Stengelfaeule / Schwarzbeinigkeit (Damping Off) | fungal | Saemling knickt an Basis um, Staengel duenn und braun | overwatering, cold_wet_soil | 2--5 | seedling |
| Blattfleckenkrankheit (Cercospora Leaf Spot) | fungal | Runde braune Flecken mit hellem Zentrum auf Blaettern | high_humidity, rain_splash | 5--10 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Coccinella septempunctata (Siebenpunkt-Marienkaefer) | Blattlaeuse | 5--10 | 7--14 |
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |
| Encarsia formosa | Weisse Fliege | 3--5 | 21--28 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Steinernema feltiae (Nematode) | Trauermuecke (Bodenstadien) | 250.000/m2 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage, 3x wiederholen | 0 | Blattlaeuse, Weisse Fliege, Spinnmilbe |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Weisse Fliege, Thripse |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Falscher Mehltau (praeventiv/frueh) |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Spruehung 1:5 verduennt, alle 14 Tage praeventiv | 0 | Pilzkrankheiten allgemein |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Gute Luftzirkulation | cultural | -- | Pflanzabstand 25--30 cm, nicht zu dicht pflanzen | 0 | Falscher Mehltau, Grauschimmel |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen und im Restmuell (nicht Kompost) entsorgen | 0 | Falscher Mehltau, Cercospora |

### 5.5 Resistenzen der Art

Basilikum (Ocimum basilicum) als Art hat kaum natuerliche Resistenzen. Die groesste Bedrohung ist der Falsche Mehltau (Peronospora belbahrii), gegen den seit ca. 2010 weltweit selektiert wird.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Peronospora belbahrii (Falscher Mehltau) | Krankheit | Cultivare wie 'Rutgers Obsession DMR', 'Prospera', 'Eleonora' | `resistant_to` |
| Fusarium oxysporum f.sp. basilici | Krankheit | Cultivare wie 'Nufar F1', 'Aroma 2' | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Lippenbluetler (Lamiaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) oder Gruenduengung -- lockerer, naehrstoffreicher Boden |
| Empfohlene Nachfrucht | Schwachzehrer (Radieschen, Salat) oder Gruenduengung |
| Anbaupause (Jahre) | 2--3 Jahre fuer Lamiaceae auf gleicher Flaeche (Fusarium-Problematik) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Weisse-Fliege-Abwehr durch aetherische Oele, traditionelle Aromafoerderung, gleiche Waermebeduerfnisse | `compatible_with` |
| Paprika | Capsicum annuum | 0.8 | Aehnliche Standortansprueche, Blattlaus-Abwehr | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Aehnliche Waerme-/Feuchtigkeitsbeduerfnisse, Platzausnutzung (Hochwuchs + Bodendecker) | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.7 | Gleiche Kultur, gute Raumnutzung | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.7 | Schnelle Ernte, Bodenbeschattung durch Basilikum | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes patula | 0.8 | Nematoden-Abwehr, Bestauber anlocken | `compatible_with` |
| Kamille | Matricaria chamomilla | 0.7 | Foerdert aetherische Oelproduktion in Nachbarschaft | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.7 | Pilzabwehr durch Allicin, Bestauber anlocken | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Salbei | Salvia officinalis | Unterschiedliche Boden-/Wasserbeduerfnisse (Salbei = trocken/mager, Basilikum = feucht/naehrstoffreich), Konkurrenz um Standort | moderate | `incompatible_with` |
| Raute (Weinraute) | Ruta graveolens | Allelopathische Hemmung, aetherische Oele der Raute hemmen Basilikum-Wachstum | moderate | `incompatible_with` |
| Thymian | Thymus vulgaris | Gegensaetzliche Wasserbeduerfnisse (Thymian = trocken, Basilikum = feucht) | mild | `incompatible_with` |
| Rosmarin | Salvia rosmarinus | Gegensaetzliche Wasserbeduerfnisse (Rosmarin = trocken/mager) | mild | `incompatible_with` |
| Melisse (Zitronenmelisse) | Melissa officinalis | Starke Ausbreitung, Konkurrenz um Licht und Naehrstoffe | mild | `incompatible_with` |
| Dill | Anethum graveolens | Unterschiedliche Wasserbeduerfnisse (Dill = maessig/trocken, Basilikum = feucht); Dill kann durch schnelles Hoehenwachstum Basilikum beschatten | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Lamiaceae (mit sich selbst) | `shares_pest_risk` | Falscher Mehltau (Peronospora), Fusarium | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Basilikum |
|-----|-------------------|-------------|------------------------------|
| Thai-Basilikum | Ocimum basilicum var. thyrsiflora | Gleiche Art, wuerziger, Anisaroma | Hitzevertraglicher, widerstandsfaehiger gegen Falschen Mehltau |
| Zitronenbasilikum | Ocimum x citriodorum | Gleiche Gattung, Zitrusaroma | Robuster, andere Aromanuance |
| Griechisches Strauch-Basilikum | Ocimum basilicum var. minimum | Gleiche Art, Zwergform | Kompakter, Topf-/Balkonkultur, dekorativ |
| Afrikanisches Basilikum (African Blue) | Ocimum kilimandscharicum x basilicum | Hybrid | Perennial (merhjaehrig), robuster, bienenfreundlich |
| Perilla (Shiso) | Perilla frutescens | Gleiche Familie (Lamiaceae) | Kaeltevertraglicher, andere Aromanuance, rote Blattvariante |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Ocimum basilicum,Basilikum;Basil;Koenigskraut;Sweet Basil,Lamiaceae,Ocimum,annual,short_day,herb,fibrous,10a;10b;11a;11b,0.1,"Tropisches Asien (Indien, Suedostasien)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Genovese,Ocimum basilicum,,,large_leaf;italian_type;aromatic,70,, open_pollinated
Nufar F1,Ocimum basilicum,Genesis Seeds,,large_leaf;vigorous;disease_resistant,72,fusarium,f1_hybrid
Siam Queen,Ocimum basilicum,,,thai_type;purple_stems;anise_aroma,60,,open_pollinated
Dark Opal,Ocimum basilicum,University of Connecticut,1962,purple_leaf;ornamental;aromatic,65,,open_pollinated
Prospera,Ocimum basilicum,Genesis Seeds,,large_leaf;disease_resistant,75,downy_mildew,f1_hybrid
Griechisches Strauchbasilikum,Ocimum basilicum var. minimum,,,compact;small_leaf;ball_shape,55,,open_pollinated
Cinnamon Basil,Ocimum basilicum 'Cinnamon',,,purple_stems;cinnamon_aroma,60,,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Basil: https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/basil
2. NCSU Extension -- Ocimum basilicum: https://plants.ces.ncsu.edu/plants/ocimum-basilicum/
3. Johnny's Seeds -- Hydroponic Basil Guide: https://www.johnnyseeds.com/growers-library/herbs/basil/hydroponic-container-basil-guide.html
4. Upstart Farmers -- Growing Hydroponic Basil: https://university.upstartfarmers.com/blog/hydroponic-basil
5. Hortipendium -- Basilikum Pflanzenschutz: https://www.hortipendium.de/Basilikum_Pflanzenschutz
6. Samen.de -- Krankheiten und Schaedlinge bei Basilikum: https://samen.de/blog/krankheiten-und-schaedlinge-bei-basilikum-erkennen-und-behandeln.html
7. Bioaktuell.ch -- Falscher Mehltau bei Basilikum: https://www.bioaktuell.ch/pflanzenbau/kraeuteranbau/pflanzenschutz/allgemein/mehltau-bei-basilikum
8. Gartenjournal -- Basilikum gute Nachbarn: https://www.gartenjournal.net/basilikum-gute-nachbarn
9. Gardenia.net -- Companion Plants for Basil: https://www.gardenia.net/guide/companion-plants-for-basil
10. Koraylights -- Indoor cultivation PPFD and DLI: https://koraylights.com/how-much-light-do-your-plants-need-indoor-cultivation-ppfd-and-dli/
11. ScienceDirect -- Optimization of basil in LED environments: https://www.sciencedirect.com/science/article/pii/S0304423821005938
12. Old Farmer's Almanac -- Basil: https://www.almanac.com/plant/basil
