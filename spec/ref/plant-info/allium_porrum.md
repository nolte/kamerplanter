# Porree / Lauch -- Allium porrum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, Hortipendium, Wikipedia, Bio-Gaertner, naturadb.de, gartenratgeber.net, samen.de, pflanzenkrankheiten.ch, schadbild.com, gartenjournal.net, Koraylights

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Allium porrum (syn. Allium ampeloprasum var. porrum; akzeptierter Name nach POWO: Allium ampeloprasum) | `species.scientific_name` |
| Volksnamen (DE/EN) | Porree; Lauch; Winterlauch; Leek; Garden Leek | `species.common_names` |
| Familie | Amaryllidaceae | `species.family` -> `botanical_families.name` |
| Gattung | Allium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | biennial (wird als Einjaehrige kultiviert; Bluete im 2. Jahr nach Vernalisation) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- lange Tage foerdern Wachstum; Bluete im 2. Jahr durch Langtag nach Vernalisation) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Winterlauch-Sorten vertragen Froeste bis -15 degC und koennen den ganzen Winter im Boden stehen bleiben. Sommerlauch-Sorten sind weniger frosthart (bis -5 degC). In Mitteleuropa je nach Sorte ganzjaehrig im Freiland kultivierbar (Sommer- und Wintertypen). | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Vorderasien (abgeleitet von Allium ampeloprasum) | `species.native_habitat` |
| Allelopathie-Score | 0.2 (leichte Hemmwirkung auf Leguminosen durch Allicin-aehnliche Verbindungen) | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder (Starkzehrer) | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10--12 (Aussaat Januar--Maerz) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat ab Maerz unter Glas moeglich; Pflanzung bevorzugt) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5 (Pflanzung 5; 6; 7) | `species.direct_sow_months` |
| Erntemonate | 8; 9; 10; 11; 12; 1; 2; 3 (Winterlauch!) | `species.harvest_months` |
| Bluetemonate | 6; 7 (nur 2. Jahr oder bei Schossern) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | medium (lange Kulturzeit, Voranzucht empfohlen) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 15--20 degC
- Minimale Keimtemperatur: 8 degC
- Keimdauer: 10--20 Tage
- **Dunkelkeimer** -- Samen 1--2 cm tief saeen
- Vorkultur in Topfplatten oder Saatschalen ab Januar/Februar
- Auspflanzen, wenn Saemlinge bleistiftdick sind (ca. 15--20 cm hoch)
- Pflanzung in vorgestochene Loecher (10--15 cm tief) oder Furchen mit anhaeufelnd

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (alle Allium-Arten sind giftig fuer Katzen!) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (alle Allium-Arten sind giftig fuer Hunde!) | `species.toxicity.is_toxic_dogs` |
| Giftige Pflanzenteile | leaf; stem; root (gesamte Pflanze) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | N-Propyl-Disulfid (verursacht oxidative Schaedigung der roten Blutkoerperchen) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (haemolytische Anaemie bei Katzen/Hunden) | `species.toxicity.severity` |
| Giftig fuer Kinder | false (als Lebensmittel in normalen Mengen unbedenklich) | `species.toxicity.is_toxic_children` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Allium porrum (Leek) als giftig fuer Hunde, Katzen und Pferde. Toxisches Prinzip: N-Propyl-Disulfid. Klinische Symptome: Erbrechen, Abbau roter Blutkoerperchen (haemolytische Anaemie, Heinz-Koerper-Anaemie), Blut im Urin, Schwaeche, erhoehte Herzfrequenz. ALLE Allium-Arten (Zwiebel, Knoblauch, Schnittlauch, Lauch) sind fuer Katzen und Hunde giftig -- roh, gekocht, getrocknet oder fluessig.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | -- (kein Rueckschnitt; Blaetter koennen bei Pflanzung auf 2/3 gekuerzt werden fuer besseres Anwachsen) | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Beschaedigte oder gelbe Aussenblaetter regelmaessig entfernen. Bluetenstaende bei Schossern sofort entfernen (Energieverschwendung). Ansonsten kein Rueckschnitt noetig.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in tiefen Toepfen, aber Freiland bevorzugt wegen langer Kulturzeit) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--15 (fuer 3--5 Pflanzen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 (tiefe Pflanzung fuer lange Schaefte!) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 40--80 (Blattteil), Schaftlaenge 15--30 cm (der weisse Teil) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 5--10 (pro Pflanze) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 15--20 (in der Reihe), Reihenabstand 30--40 cm | `species.spacing_cm` |
| Indoor-Anbau | no (zu grosse Pflanze, zu lange Kulturzeit) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur in sehr tiefen Gefaessen und mit viel Geduld) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freiland genuegt; Gewaechshaus nur fuer Voranzucht) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, tiefgruendige, humose Erde mit guter Drainage. pH 6.0--7.5. Starkzehrer -- vor Pflanzung Kompost einarbeiten. | -- |

**Hinweis:** Porree ist ein klassisches Freilandgemuese mit langer Kulturzeit (5--8 Monate). Der weisse Schaft entsteht durch Anhaeuefeln (Bleichen) -- regelmaessig Erde an den Schaft aufschuetten, um den weissen Teil zu verlaengern. Winterlauch-Sorten stehen den ganzen Winter im Beet und werden nach Bedarf geerntet.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 10--20 | 1 | false | false | low |
| Saemling (seedling) | 42--56 | 2 | false | false | low |
| Vegetativ (vegetative) | 90--150 | 3 | false | true | medium |
| Ernte (harvest) | 30--90 (Erntefenster, bei Winterlauch bis Maerz) | 4 | true | true | high |

Hinweis: Die vegetative Phase ist mit 90--150 Tagen aussergewoehnlich lang. Das Schaftwachstum (Dickenwachstum) findet vor allem in der zweiten Haelfte der vegetativen Phase statt. Anhaeuefeln ab einer Schaftdicke von ca. 2 cm.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | -- (Dunkelkeimer, Samen im Substrat) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich / kuenstlich 14--16 h nach Auflaufen | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--20 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 14--20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--40 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Saemlinge sind duenn und grasartig. Beim Pikieren oder vor der Pflanzung koennen Blatt- und Wurzelspitzen leicht gekuerzt werden (auf ca. 2/3 der Laenge) -- das foerdert kraeftiges Anwachsen.

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (natuerlich, Sommer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--24 (optimal 18--22) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.3 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (gleichmaessig feucht, besonders bei Hitze) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Anhaeuefeln (Erde am Schaft hochziehen) in 2--3 Etappen, je 5--10 cm, fuer weissen Schaft. Keine Erde ins Herz kommen lassen (Faeulnis!). Gleichmaessige Wasserversorgung ist entscheidend fuer dicke Schaefte.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (Herbst/Winter) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -15 -- 20 (Winterlauch ist extrem frosthart) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -15 -- 10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- (natuerlich) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | -- (natuerlich, bei Frostboden nicht giessen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | -- | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Winterlauch wird nach Bedarf geerntet. Bei anhaltendem Frost (Boden gefroren) kann nicht geerntet werden -- ggf. Vlies/Laub als Frostschutz auflegen, damit der Boden locker bleibt. Vor dem Schossen im Fruehjahr (Maerz/April) alle verbleibenden Pflanzen ernten.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.6--1.0 | 6.0--7.0 | 80 | 30 | 20 | 2 |
| Vegetativ | 3-1-3 | 1.4--2.0 | 6.0--7.0 | 120 | 50 | 35 | 3 |
| Ernte | 1-1-2 | 0.8--1.2 | 6.0--7.0 | 80 | 30 | 20 | 2 |

Hinweis: Porree ist ein Starkzehrer mit hohem Stickstoff- und Kaliumbedarf. N foerdert die Blattmasse und das Schaftwachstum; K verbessert die Frostresistenz (besonders wichtig bei Winterlauch). Kalibetonte Duengung ab Spaetsommer staerkt die Winterhaerte. Schwefel ist fuer alle Allium-Arten wichtig (Geschmack, Abwehrstoffe).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 10--20 Tage | Erstes echtes Blatt (grasartig) sichtbar |
| Saemling -> Vegetativ | manual / conditional | 42--56 Tage; Pflanzung ins Freiland | Saemling bleistiftdick (ca. 6--8 mm Durchmesser), 15--20 cm hoch |
| Vegetativ -> Ernte | time_based / manual | 90--150 Tage nach Pflanzung | Schaft hat gewuenschte Dicke erreicht (mind. 2--3 cm Durchmesser) |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Hydro/Coco -- selten bei Porree)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Vegetativ |
| Kaliumsulfat | div. | supplement | 0-0-50 (+S 18%) | 0.08 | 5 | Vegetativ spaet (Winterhaerte) |

Hinweis: Porree wird fast ausschliesslich im Freiland angebaut. Hydroponischer Anbau ist moeglich, aber unueblich.

#### Organisch (Outdoor/Beet -- Standardkultur)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 (Starkzehrer!) | Herbst/Fruehjahr (Einarbeitung vor Pflanzung) | heavy_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 80--120 g/m2 | Fruehjahr (Einarbeitung) | heavy_feeder |
| Hornspane (grob) | Oscorna / div. | organisch (N-Langzeit) | 80--100 g/m2 | Herbst (Einarbeitung) | heavy_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 1 L/m2 | Jun--Aug, alle 14 Tage | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 0.5 L/m2 | Jul--Sep, alle 14 Tage | heavy_feeder (Winterhaerte) |
| Holzasche (kalireich) | Eigenerzeugung | organisch (K-betont) | 100--150 g/m2 | Aug--Sep (Winterhaerte) | heavy_feeder |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Porree Standard Freiland")

| Woche | Phase | Massnahme | Hinweise |
|-------|-------|-----------|----------|
| 0 (Herbst/Fruehjahr) | Vorbereitung | 5--8 L/m2 Reifkompost + 80--100 g/m2 Hornspane einarbeiten | Tiefgruendige Bodenlockerung |
| 1--8 | Saemling (Voranzucht) | Nur Wasser; ggf. leichter Fluessigduenger 0.5x Dosis | Saemling in Topfplatten, wenig Naehrstoffbedarf |
| 9 (Pflanzung) | -- | 40--60 g/m2 Hornmehl in Pflanzfurche einarbeiten | Startduengung bei Pflanzung |
| 10--16 | Vegetativ frueh | Brennnesseljauche 1:10 alle 14 Tage | Stickstoff fuer Blattwachstum |
| 17--24 | Vegetativ Hauptwachstum | Brennnesseljauche + Beinwelljauche alternierend | Anhaeuefeln ab Woche 14 |
| 25--30 | Vegetativ spaet | Beinwelljauche 1:10 alle 14 Tage, Holzasche 100 g/m2 | Kalium-Betonung fuer Winterhaerte |
| 30+ | Ernte | Keine Duengung mehr | Erntefenster Oktober--Maerz |

### 3.3 Mischungsreihenfolge

> **Bei mineralischer Duengung (selten noetig):**

1. Wasser temperieren (15--20 degC)
2. CalMag (Calcium + Magnesium)
3. Base A (Calcium + Mikronaehrstoffe)
4. Base B (Phosphor + Schwefel + Magnesium)
5. Kaliumsulfat (nur in Spaetphase)
6. pH-Korrektur -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren.

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer!** Porree braucht viel Stickstoff und Kalium. Unterdosierung fuehrt zu duennen Schaeften.
- **Schwefel fuer Geschmack:** Alle Allium-Arten brauchen Schwefel fuer die Bildung der typischen Aromastoffe (Sulfide). Bei S-Mangel schmeckt der Lauch fade.
- **Kalium fuer Winterhaerte:** Ab August kalibetonte Duengung, damit der Winterlauch Froeste gut uebersteht. N-Duengung ab September einstellen (weiches Gewebe = Frostschaden).
- **Keine Frischdungung:** Frischer Mist foerdert Faeulnis und Schaedlingsbefall (Lauchmotte, Minierfliege).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (Winterlauch steht im Freiland, natuerliche Niederschlaege; bei Duerreperioden giessen) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Morgens giessen, moeglichst bodennah (nicht ins Herz -- Faeulnisgefahr). Gleichmaessige Bodenfeuchte foerdert dicke Schaefte. Staunaesse vermeiden. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (Freilandkultur, kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan--Feb | Voranzucht | Aussaat in Topfplatten bei 15--20 degC unter Glas | hoch |
| Marz | Saemlinge pflegen | Weiterwachsen lassen, abhaerten ab April | mittel |
| Apr | Abhaertung | Saemlinge nach draussen stellen, an Aussenklima gewoehnen | mittel |
| Mai--Jun | Auspflanzen | In Furchen oder Locher pflanzen (10--15 cm tief), Pflanzabstand 15 cm, Reihenabstand 30--40 cm | hoch |
| Jul | 1. Anhaeuefeln + Duengung | Erde an den Schaft anhaeuefeln (5--10 cm), Brennnesseljauche alle 14 Tage | hoch |
| Aug | 2. Anhaeuefeln + Kalium-Duengung | Erneut anhaeuefeln, Kalium-betonte Duengung beginnen (Winterhaerte) | hoch |
| Sep | 3. Anhaeuefeln + Kulturschutznetze | Letztes Anhaeuefeln, Netze gegen Lauchmotte/Minierfliege kontrollieren | hoch |
| Okt | Erntebeginn (Sommerlauch) | Sommerlauch-Sorten ernten, Winterlauch weiter stehen lassen | mittel |
| Nov--Dez | Winterernte bei Bedarf | Bei frostfreiem Boden ernten, Vlies/Laub als Frostschutz auflegen | mittel |
| Jan--Marz | Winterernte fortsetzen | Letzte Winterlauch-Ernte vor dem Schossen (Maerz/April) | mittel |

### 4.3 Ueberwinterung

Winterlauch-Sorten (z.B. 'Blaugruener Winter', 'Carentan') sind bis -15 degC winterhart und stehen den ganzen Winter im Beet. Schutz: Vlies oder Laubschicht auflegen, damit der Boden nicht komplett durchfriert (sonst ist die Ernte unmoeglich). Vor dem Schiessen im Fruehjahr (Maerz/April) alle verbleibenden Pflanzen ernten. Sommerlauch-Sorten sind weniger frosthart und sollten vor dem ersten starken Frost geerntet werden.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Lauchmotte (Leek Moth) | Acrolepiopsis assectella | Weisse Fraessgaenge in Blaettern und Schaft, Raupen (gelblich-gruen) im Pflanzeninneren, Faeulnis | leaf, stem | vegetative | medium |
| Lauchminierfliege (Allium Leafminer) | Phytomyza gymnostoma | Einstichloecher (weisse Punkte) in Blaettern, Miniergaenge, Maden in Schaft und Zwiebelbasis | leaf, stem | vegetative | medium |
| Zwiebelthrips (Onion Thrips) | Thrips tabaci | Silbrige Saugflecken auf Blaettern, Blattkruemmung | leaf | vegetative | medium |
| Blattlaeuse (Aphids) | Myzus persicae | Gekraeuselte Blaetter, Honigtau | leaf | vegetative | easy |
| Lauchminiermotte | Acrolepiopsis assectella | Wie Lauchmotte -- zweite Generation im Spaetsommer | leaf, stem | vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Porreerost (Leek Rust) | fungal | Orangerote Pusteln auf Blattober- und -unterseite, bei starkem Befall Blattverlust | warm_humid_conditions, poor_airflow | 7--14 | vegetative |
| Papierfleckenkrankheit (White Tip) | fungal (Oomycet) | Papierartige, weisslich-braune Verfaerbung der Blattspitzen, absteigend | cool_wet_conditions | 7--14 | vegetative |
| Purpurfleckenkrankheit (Purple Blotch) | fungal | Braun-violette Flecken auf Blaettern mit konzentrischen Ringen | warm_humid_conditions | 5--10 | vegetative |
| Samtfleckenkrankheit (Leaf Blotch) | fungal | Ovale, eingesunkene, olivgruene bis braune Flecken auf Blaettern | humid_conditions | 7--14 | vegetative |
| Fusarium-Faeule (Fusarium Basal Rot) | fungal | Gelblich-braune Verfaerbung der Schaftbasis, matschige Faeulnis, Pflanze fault von unten | warm_soil, waterlogging | 14--28 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Steinernema feltiae (Nematode) | Lauchminierfliege (Bodenstadien) | 250.000/m2 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetze | mechanical | -- | Feinmaschiges Netz (< 0.8 mm) ueber Bestand ab Pflanzung, lueckenlos verschliessen | 0 | Lauchmotte, Lauchminierfliege (wichtigste Massnahme!) |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Thripse, Blattlaeuse |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse, Thripse |
| Befallene Blaetter entfernen | cultural | -- | Befallene Aussenblaetter sofort entfernen und im Restmuell entsorgen | 0 | Porreerost, Lauchmotte (Puppen entfernen) |
| Fruchtfolge (min. 3 Jahre) | cultural | -- | Keine Allium-Arten auf gleicher Flaeche innerhalb von 3 Jahren | 0 | Porreerost, Minierfliege, Fusarium |
| Mischkultur mit Moehren | cultural | -- | Moehren zwischen Lauch-Reihen pflanzen | 0 | Lauchmotte/Minierfliege (Geruchstarnung) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Puccinia allii (Porreerost) | Krankheit | Einige Winterlauch-Cultivare zeigen bessere Toleranz (z.B. 'Blaugruener Winter', 'Carentan') | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Lauch-/Zwiebelgewaechse (Alliaceae/Amaryllidaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) oder Gruenduengung -- lockerer, stickstoffangereicherter Boden |
| Empfohlene Nachfrucht | Schwachzehrer (Feldsalat, Spinat) oder Mittelzehrer (Moehre, Salat) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Amaryllidaceae (Lauch, Zwiebel, Knoblauch, Schnittlauch) auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Moehre / Karotte | Daucus carota | 0.9 | Klassische Mischkultur! Gegenseitige Schaedlingsabwehr (Moehrenfliege vs. Lauchmotte) | `compatible_with` |
| Sellerie | Apium graveolens | 0.8 | Gegenseitige Schaedlingsabwehr, aehnliche Kulturbeduerfnisse | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.8 | Verschiedene Wurzeltiefen, gute Bodennutzung | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Aehnliche Standortansprueche, Lauch wehrt Weisse Fliege ab | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.7 | Verschiedene Kulturdauer, gute Platznutzung | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Schnelle Zwischenkultur zwischen den Lauch-Reihen | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.7 | Gute Raumnutzung, verschiedene Familien | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Erbse | Pisum sativum | Allicin-aehnliche Verbindungen hemmen Rhizobium-Aktivitaet der Erbsen | moderate | `incompatible_with` |
| Buschbohne / Stangenbohne | Phaseolus vulgaris | Wie Erbse: negative Wechselwirkung mit Knollchenbakterien | moderate | `incompatible_with` |
| Zwiebel | Allium cepa | Gleiche Familie, gemeinsame Schaedlinge und Krankheiten, Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Knoblauch | Allium sativum | Gleiche Familie, gemeinsame Schaedlinge | moderate | `incompatible_with` |
| Schnittlauch | Allium schoenoprasum | Gleiche Familie, gemeinsame Schaedlinge | mild | `incompatible_with` |
| Rote Bete | Beta vulgaris | Naehrstoffkonkurrenz (beide Starkzehrer) | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Amaryllidaceae (mit sich selbst) | `shares_pest_risk` | Porreerost, Lauchmotte, Lauchminierfliege, Fusarium | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Porree |
|-----|-------------------|-------------|------------------------------|
| Winterheckenzwiebel | Allium fistulosum | Gleiche Gattung, aehnliche Nutzung | Mehrjaehrig, winterhart, weniger Pflegeaufwand |
| Fruehlingszwiebel | Allium fistulosum (juv.) | Gleiche Gattung | Kuerzere Kulturzeit (8--10 Wochen), ideal als Zwischenkultur |
| Speisezwiebel | Allium cepa | Gleiche Gattung | Vielseitigere Verwendung, kuerzere Kulturzeit |
| Knoblauch | Allium sativum | Gleiche Gattung | Einfachere Kultur (Steckzwiebeln), winterhart |
| Elefantenknoblauch | Allium ampeloprasum | Gleiche Art | Milder Knoblauch-Geschmack, dekorativ |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Allium porrum,Porree;Lauch;Winterlauch;Leek;Garden Leek,Amaryllidaceae,Allium,biennial,long_day,herb,fibrous,5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.2,"Mittelmeerraum, Vorderasien"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Blaugruener Winter,Allium porrum,,,cold_hardy;long_season,180,,open_pollinated
Carentan 2,Allium porrum,,,cold_hardy;heirloom,170,,open_pollinated
Herbstriesen 2,Allium porrum,,,high_yield,140,,open_pollinated
Hannibal,Allium porrum,,,early_maturing;high_yield,100,,f1_hybrid
De Solaise,Allium porrum,,,cold_hardy;heirloom,160,,open_pollinated
Lancelot,Allium porrum,,,early_maturing;high_yield,95,,f1_hybrid
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Leek: https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/leek
2. naturadb.de -- Lauch: https://www.naturadb.de/pflanzen/allium-porrum/
3. gartenratgeber.net -- Porree: https://www.gartenratgeber.net/pflanzen/porree-lauch.html
4. Wikipedia -- Lauch: https://de.wikipedia.org/wiki/Lauch
5. Bio-Gaertner -- Porree: https://www.bio-gaertner.de/Pflanzen/Porree
6. samen.de -- Porree im Fruchtwechsel: https://samen.de/blog/porree-im-fruchtwechsel-optimale-anbauplanung-fuer-gesunde-boeden-und-reiche-ernten.html
7. pflanzenkrankheiten.ch -- Lauchmotte: https://www.pflanzenkrankheiten.ch/krankheiten-an-kulturpflanzen-2/gemuese-offcanvas/allium-sp/acrolepiopsis-assectella
8. schadbild.com -- Lauchminierfliege: https://www.schadbild.com/gem%C3%BCse/lauch-porree/lauchminierfliege/
9. gartenjournal.net -- Porree Schaedlinge: https://www.gartenjournal.net/porree-schaedlinge-krankheiten
10. samen.de -- Krankheiten und Schaedlinge bei Porree: https://samen.de/blog/haeufige-krankheiten-und-schaedlinge-bei-porree-erkennen-und-bekaempfen.html
11. Koraylights -- Indoor cultivation PPFD and DLI: https://koraylights.com/how-much-light-do-your-plants-need-indoor-cultivation-ppfd-and-dli/
