# Rucola -- Eruca vesicaria

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** NaturaDB, Hortipendium, Meine-Ernte, Plantura, Derkleinegarten, Mein-gartenexperte, pflanzenfreunde.com, mein-garten.info

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Eruca vesicaria | `species.scientific_name` |
| Volksnamen (DE/EN) | Rucola; Senfrauke; Garten-Senfrauke; Rucolasalat; Rocket; Arugula; Roquette; Garden Rocket | `species.common_names` |
| Familie | Brassicaceae | `species.family` -> `botanical_families.name` |
| Gattung | Eruca | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual (in milden Wintern auch biennial moeglich) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Schoessung durch lange Tage ausgeloest; schnell bolting in Sommerhitze) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy (vertraegt leichte Froeste bis -5 degC; Herbst-/Winteranbau moeglich) | `species.frost_sensitivity` |
| Winterhaerte-Detail | Uebersteht leichte Froeste (bis -5 degC). Winteranbau im Kalthaus oder unter Vlies moeglich. Im milden Winter ueberwintert Rucola im Freien in Zone 7+. | `species.hardiness_detail` |
| Heimat | Mittelmeerraum; Vorderasien; Nordafrika | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic; cut_and_come_again | `species.traits` |

**Wichtige Unterscheidung:** Die im Handel als "Rucola" angebotene Pflanze ist meist *Eruca vesicaria* subsp. *sativa* (Garten-Senfrauke) mit breiteren, milderen Blaettern. Der "Wilde Rucola" ist *Diplotaxis tenuifolia* (Schmalblättrige Doppelsame) und gehoert einer anderen Gattung an -- deutlich staerkeres Aroma, mehrjaehrig.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8). Rucola ist ein Sukzessionsgemuese par excellence -- alle 3--4 Wochen neu saeen!

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | -- (keine Vorkultur noetig; Direktsaat bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (kann direkt nach letztem Frost gesaet werden; Kaltkeimer) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 8; 9; 10 (Vorsaison + Herbstsaison bevorzugt; Sommer-Aussaat schosst schnell) | `species.direct_sow_months` |
| Erntemonate | 4; 5; 6; 9; 10; 11; 12 (Fruehjahr und Herbst beste Qualitaet; Sommer: bitterer und schosst schnell) | `species.harvest_months` |
| Bluetemonate | 5; 6; 7; 8 (Schoessung besonders bei Hitze und langen Tagen) | `species.bloom_months` |

**Sukzessions-Empfehlung:** Alle 3--4 Wochen neu saeen fuer kontinuierliche Ernte. Erste Ernte nach 3--5 Wochen. Herbst-Aussaat (Aug/Sep) liefert beste Qualitaet ohne Bitterkkeit und hält bis Winterbeginn.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy (schnell keimend; robust; auch Anfaenger problemlos) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 10--20 degC (Kaltkeimer; Keimt auch bei 6 degC!)
- Keimdauer: 3--7 Tage
- Direktsaat in Reihen oder als Streusaat (Breitwurf)
- Saattiefe: 0.5--1 cm
- Auch als Microgreens nach 7--10 Tagen erntbar
- Kein Pikieren; Bestandsdichte durch Ausdunnen regulieren

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Glucosinolate (Isothiocyanate; typisch Brassicaceae) -- bei normaler Verzehrmenge unbedenklich; potentiell goitrogen bei exzessivem Konsum | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzreaktion mit anderen Brassicaceae-Pollen moeglich) | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | after_harvest | `species.pruning_type` |
| Rueckschnitt-Monate | 4; 5; 6; 8; 9; 10; 11 | `species.pruning_months` |

**Cut-and-Come-Again:** Aeuessere Blaetter einzeln ernten (Pflanze weiterwachsen lassen) oder Pflanze 3--4 cm ueber Boden abschneiden (Wiederaustrieb in 2--3 Wochen). Bluetentriebe entfernen verlaengert die Ernte-Saison.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (hervorragend im Topf und Kistchen; Balkon; Fensterbrett) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3--10 (je nach Anzahl Pflanzen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 20--60 (ohne Schoessen 20--30 cm; geschosst bis 60 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15--25 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5--10 in der Reihe; 20 cm Reihenabstand (oder Streusaat) | `species.spacing_cm` |
| Indoor-Anbau | yes (Fensterbrett mit Suedausrichtung gut; als Microgreens) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Balkonkasten; halbschattig im Sommer besser als Vollsonne) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freiland bevorzugt; Gewaechshaus fuer Winteranbau nuetzlich) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Leichte bis mittelschwere, gut drainierte Kraeutererde. pH 5.5--7.0. Moderate Naehrstoffversorgung -- Ueberduentung foerdert milden Geschmack statt Aromatik! | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 3--7 | 1 | false | false | medium |
| Saemling (seedling) | 7--14 | 2 | false | false | medium |
| Blattentwicklung/Ernte (leaf_development) | 14--35 | 3 | false | true | high |
| Schoessen (bolting) | 7--21 | 4 | true | limited | high |

**Hinweis:** Rucola hat einen sehr kurzen Lebenszyklus. Bei Hitze (>25 degC) und langen Tagen schoesst die Pflanze innerhalb von 4--6 Wochen. Die Blattentwicklungsphase ist die Erntephase. Nach dem Schoessen werden Blaetter sehr bitter -- Neuaussaat empfohlen.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0--100 (Kaltkeimer; Licht nicht erforderlich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0--5 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | beliebig | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 10--20 (optimal 15--18; kühle Temperaturen bevorzugt!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (feucht halten) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100--250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 6--12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 (kurze Tage verzoegern Schoessen!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 12--20 (kuehl halten; > 22 degC: Schoessgefahr steigt) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--40 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blattentwicklung/Ernte (leaf_development)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--350 (Halbschatten im Sommer bremst Schoessen!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 (je kuerzer, desto laenger bis Schoessen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 12--22 (optimal 15--18; ueber 25 degC = Schoessen in Tagen!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Ernte:** Blaetter ab 7--10 cm Groesse erntbar. Aeuessere Blaetter einzeln abschneiden oder Pflanze 3 cm ueber Boden abschneiden. Erste Ernte 3--5 Wochen nach Aussaat. Bis zu 3--4 Ernten moeglich.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- |
| Saemling | 1-0.5-1 | 0.4--0.8 | 5.5--7.0 | 40 | 20 | -- | 1 |
| Blattentwicklung | 2-0.5-1 | 0.8--1.4 | 5.5--7.0 | 60 | 25 | 20 | 2 |

**Hinweis:** Rucola ist ein Schwachzehrer. Ueberduentung (insbesondere zu viel Stickstoff) macht die Blaetter zwar gross, aber geschmacklos und mild -- der typische nussig-pfeffrige Rucolafgeschmack kommt von mildem Naehrstoffstress. Organische Duengung (Kompost) genuegt fuer die meisten Standorte.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 3--7 Tage | Keimblaetter sichtbar |
| Saemling -> Blattentwicklung | time_based | 7--14 Tage | 2--3 echte Blaetter; Ausdunnen auf 5--10 cm Abstand |
| Blattentwicklung -> Schoessen | event_based | -- | Taglaenge > 14 h; Temperaturen > 25 degC dauerhaft; Neuaussaat empfohlen |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Topf/Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Kraeuterduenger | Floria / div. | base | 6-4-6 | 0.5--0.8 g/L | 2 | Blattentwicklung |
| Volduenger Blau | Compo | base | 12-8-16 | Granulat 10--15 g/m2 | 1 | Aussaat-Vorbereitung |

#### Organisch (Freiland bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 | Vor Aussaat einarbeiten | light_feeder |
| Hornmehl | Oscorna | organisch (N, schnell) | 20--30 g/m2 | Bei Aussaat einstreuen | Blattentwicklung |
| Brennnesseljauche | Eigenerzeugung | organisch (N) | 1:20 verduennt (sehr schwach!) | alle 14 Tage | Blattentwicklung |

**Hinweis:** In humusreichen Boeden oder nach Kompostduengung ist oft keinerlei zusaetzliche Duengung noetig. Rucola neigt bei zu viel N zu uebermassigem Blattwachstum mit mildem Geschmack.

### 3.2 Duengungsplan (vereinfacht)

| Woche | Phase | Massnahme | Menge | Hinweise |
|-------|-------|-----------|-------|----------|
| 0 | Aussaat-Vorbereitung | Kompost einarbeiten | 2--3 L/m2 | Genuegt oft fuer die gesamte Kulturzeit |
| 2--3 | Saemling | Keine Duengung | -- | Substrat-Naehrstoffe genuegen |
| 4--6 | Blattentwicklung | Optionale Kraeuterduengung | 1:20 Brennnesseljauche | Nur wenn Pflanze blass oder langsam waechst |

### 3.3 Mischungsreihenfolge

1. Wasser temperieren (Zimmertemperatur genuegt; 15--20 degC)
2. Organischen Fluessigduenger (Brennnesseljauche sehr stark verduennt 1:20)
3. pH pruefen (toleriert 5.5--7.0)

### 3.4 Besondere Hinweise zur Duengung

- **Weniger ist mehr:** Zu viel Stickstoff = grosser Rucolasalat ohne Biss und Wuezze. Magere Boeden foerdern intensiveres Aroma.
- **Nitratakkumulation vermeiden:** Bei Kunstlicht oder wenig Sonne sowie hoher N-Duengung reichert Rucola Nitrat an. Vor Ernte 4--6 h Licht (Abbauprozess).
- **Bodenfeuchte gleichmaessig:** Trockenstress beschleunigt Schoessen und macht Blaetter bitter; Staunaesse foerdert Umfallkrankheit.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 (regelmaessig aber nicht uebergiessen) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 (Winterrucola sparsamer giessen) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Normaltemperatur (15--20 degC). Blaetter koennen befeuchtet werden. Gleichmaessige Feuchte. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 (oder gar nicht bei humusreichem Boden) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 8; 9; 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; bei neuem Aussaat-Zyklus neues Substrat) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Maerz | 1. Aussaat | Direktsaat im Freiland unter Vlies; oder Fensterbrett | hoch |
| Apr | Ernte 1 | Erste Ernte 3--5 Wochen nach Aussaat; aeuessere Blaetter | hoch |
| Apr | 2. Aussaat | Sukzession: Nochmals saeen fuer Folge-Ernte | mittel |
| Mai | Schoessen-Management | Bei Hitze: Bluetentriebe entfernen verlaengert Saison | mittel |
| Jun--Jul | Sommer-Pause | Hitze und lange Tage foerdern Schoessen; Pause oder Halbschatten-Standort | niedrig |
| Aug | Herbst-Aussaat | Beste Aussaatzeit fuer lange Herbsternte; Aug/Sep | hoch |
| Sep--Nov | Herbsternte | Beste Qualitaet; wenig Schoessneigung; mild + aromatisch | hoch |
| Nov--Feb | Winterrucola | Im Kalthaus oder unter Vlies; minimales Giessen | niedrig |

### 4.3 Ueberwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | fleece | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Fruehjahrs-Massnahme | uncover | `overwintering_profiles.spring_action` |
| Fruehjahrs-Massnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (degC) | 2 (Kalthaus oder Kaltgewächshaus) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (degC) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Erdfloeh | Phyllotreta spp. | Viele kleine Loecher in den Blaettern (typisches Schrotschuss-Muster) | leaf | seedling; leaf_development | easy |
| Weisse Fliege | Trialeurodes brassicae | Honigtau; weisse Fliegen an Blattunterseite | leaf | leaf_development | easy |
| Blattlaeuse | Brevicoryne brassicae | Kolonien an Triebspitzen; Honigtau; Wachstumshemmung | leaf; shoot | leaf_development | easy |
| Kohldrehherzmücke | Contarinia nasturtii | Deformierte Herzlaetter | shoot | seedling; leaf_development | difficult |
| Schnecken | Arion spp. | Frasslocher; Keimlingszerstoerung | leaf | seedling | easy |
| Kohlweissling | Pieris brassicae | Skelettfraß; Blattloecher | leaf | leaf_development | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | oomycete (Peronospora parasitica) | Gelbliche Flecken; grauweisser Belag Blattunterseite | high_humidity; cool_wet | 4--8 | seedling; leaf_development |
| Umfallkrankheit (Damping Off) | fungal (Pythium; Rhizoctonia) | Saemling knickt um; Stengelbasis verfault | overwatering; cold_wet | 2--5 | seedling |
| Kohlhernie | oomycete (Plasmodiophora brassicae) | Wurzelgallen; Welke; Blattvergelbung | acidic_soil; contaminated | 14--28 | leaf_development |
| Blattfleckenkrankheit | fungal (Alternaria brassicola) | Dunkle konzentrische Flecken | warm_wet | 5--10 | leaf_development |
| Weissrost | oomycete (Albugo candida) | Weisse warzenartige Flecken | cool_wet | 7--14 | leaf_development |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea | Blattlaeuse | 5--10 Larven/m2 | 7--14 |
| Marienkaefer (Coccinella) | Blattlaeuse | Spontan durch Begleitpfl. | -- |
| Schneckenkoerner (Ferramol) | Schnecken | 5 g/m2 | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz | cultural | -- | 0.8 mm engmaschig | 0 | Erdfloehe (sehr effektiv!); Schmetterling; Mücken |
| Kalkmilch (Anstrich) | cultural | Calciumhydroxid | Pflanzen bestauben | 0 | Erdfloehe |
| Pyrethrum | approved_organic | Pyrethrine | Bei Befall spruehen | 3 | Erdfloehe; Blattlaeuse |
| Neemoelextrakt | biological | Azadirachtin | 0.3% spruehen abends | 3 | Blattlaeuse; Weisse Fliege |
| pH-Anhebung (Kalk) | cultural | Kalk | Boden pH > 7.0 halten | 0 | Kohlhernie-Praevention |
| Ferramol (Schneckenkorn) | approved_organic | Eisen(III)-phosphat | 5 g/m2 streuen | 0 | Schnecken |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Kohlhernie (partiell) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Kohl-/Kreuzbluetengewaechse (Brassicaceae) |
| Empfohlene Vorfrucht | Leguminosen (Erbsen, Bohnen); Gruenduengung; Zwiebeln |
| Empfohlene Nachfrucht | Tomate; Paprika; Aubergine (Starkzehrer nach Rucola-Erschoepfung minimal) |
| Anbaupause (Jahre) | 2--3 Jahre fuer Brassicaceae (Kohlhernie-Praevention) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Basilikum | Ocimum basilicum | 0.8 | Gegenseitige Aromaverbesserung; Nuetzlingsanlocken | `compatible_with` |
| Zwiebeln | Allium cepa | 0.8 | Blattlaus-Abwehr durch Schwefelverbindungen; Erdfloh-Verwirrung | `compatible_with` |
| Sellerie | Apium graveolens | 0.7 | Erdfloh-Abschreckung durch Sellerieduft | `compatible_with` |
| Ringelblume | Calendula officinalis | 0.7 | Nuetzlingsanlocken; Blattlaus-Abwehr | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.7 | Pilzpraevention; Blattlaus-Abwehr; Compactheit | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.6 | Unterschiedliche Naehrstoffaufnahme; nutzt Raum gut aus | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Andere Brassicaceae | Brassica oleracea; Raphanus sativus | Gleiche Schaderreger (Kohlhernie; Falscher Mehltau; Kohlweissling); Naehrstoffkonkurrenz | severe | `incompatible_with` |
| Erdbeere | Fragaria x ananassa | Konkurrenz; Boden-Pilz-Uebertragung moeglich | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Brassicaceae | `shares_pest_risk` | Kohlhernie (Plasmodiophora brassicae); Falscher Mehltau; Erdfloehe; Kohlweissling; Weissrost | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Rucola |
|-----|-------------------|-------------|--------------------------|
| Wilder Rucola | Diplotaxis tenuifolia | Aehnliches Aroma; Blattform schmaler | Mehrjaehrig; toleranter; intensiveres Aroma; hitzeresistenter |
| Senf (Blattsenf) | Brassica juncea | Gleiche Familie; Salatblatt | Groessere Ernte; winterharter; andere Aromarichtung |
| Feldsalat | Valerianella locusta | Aehnliche Ernte-Saison (Herbst/Winter) | Winterhaerter; weniger Bitterkeit; andere Textur |
| Brunnenkresse | Nasturtium officinale | Aehnlich pfeffrig-scharf | Mehrjaehrig; wasserliebend; kein Schoessen-Problem |

---

## 8. Sorten / Cultivars

| Sorte | Typ | Blattform | Schossneigung | Besonderheiten |
|-------|-----|-----------|--------------|----------------|
| Rucola Selezione | Standard | breit; gelappt | mittel | Ga Standardsorte; milde Wuerze |
| Slow Bolt | Schoss-verzogert | breit | niedrig | Bleibt laenger erntbar; fuer Sommersaison |
| Wasabi Rocket | Scharf | schmal; tief gelappt | mittel | Intensiver Wasabi-Note; wilder Typ |
| Runway | F1 Hybrid | breit | niedrig | Sehr hoher Ertrag; laengere Saison |
| Wild Rocket | Wildtyp (D. tenuifolia) | schmal; fein gelappt | niedrig (mehrjaehrig) | Aufrecht; intensiveres Aroma; mehrjaehrig |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity
Eruca vesicaria,Rucola;Senfrauke;Rocket;Arugula,Brassicaceae,Eruca,annual,long_day,herb,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.1,Mittelmeerraum; Vorderasien,yes,3,15,40,20,8,yes,yes,false,false,light_feeder,hardy
```

---

## Quellenverzeichnis

1. [NaturaDB -- Eruca vesicaria subsp. sativa](https://www.naturadb.de/pflanzen/eruca-vesicaria-ssp-sativa/) -- Botanische Grunddaten; Standort
2. [Hortipendium -- Rucola](https://hortipendium.de/Rucola) -- Professioneller Anbau; Schädlinge
3. [Meine-Ernte -- Rucola](https://www.meine-ernte.de/pflanzen-a-z/gemuese/rucola/) -- Praxis-Anbauguide
4. [Derkleinegarten.de -- Rucola anbauen](https://www.derkleinegarten.de/nutzgarten-kleingarten/gemuesegarten-anlegen/blattgemuese/rucola-anbauen.html) -- Anbau; Schossung; Saison
5. [Mein-gartenexperte.de -- Rucola pflanzen](https://www.mein-gartenexperte.de/rucola-pflanzen) -- Standort; Pflege
6. [Pflanzenfreunde.com -- Rucola](https://www.pflanzenfreunde.com/garten/kraeutergarten/rucola-salat-pflanze.htm) -- Kuebelanbau; Winterrucola
7. [Mein-garten.info -- Rucola pflanzen](https://mein-garten.info/rucola-pflanzen-pflegen-und-ernten/) -- Companion Planting; Sorten
