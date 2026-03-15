# Erbse -- Pisum sativum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, Hortipendium, Bio-Gaertner, Seedforward, LfL Bayern, fryd.app, naturadb.de, pflanzen-lexikon.com, gartenjournal.net, grove.eco, Koraylights, MechaTronix

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pisum sativum | `species.scientific_name` |
| Volksnamen (DE/EN) | Erbse; Gartenerbse; Garden Pea; Green Pea | `species.common_names` |
| Familie | Fabaceae | `species.family` -> `botanical_families.name` |
| Gattung | Pisum | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- Bluete wird durch laenger werdende Tage im Fruehjahr ausgeloest) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | moderate | `species.frost_sensitivity` |
| Winterhaerte-Detail | Keimlinge vertragen leichte Froeste bis -4 degC. Ausgewachsene Pflanzen sind frostempfindlich. In Mitteleuropa einjaehrig kultiviert (Freiland Maerz--Juli). Kuehle Temperaturen (12--18 degC) sind ideal; Hitze ueber 25 degC fuehrt zu Ertragsdepression und vorzeitigem Absterben. | `species.hardiness_detail` |
| Heimat | Vorderasien (Fruchtbarer Halbmond), Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | -0.3 (Stickstofffixierung verbessert Boden fuer Nachkulturen) | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light (Schwachzehrer -- Stickstofffixierung durch Rhizobium-Symbiose) | `species.nutrient_demand_level` |
| Gruenduengung geeignet | true (Leguminose, hervorragende Gruenduengung und Vorfrucht) | `species.green_manure_suitable` |
| Traits | edible; nitrogen_fixing | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4--6 (moeglich, aber Direktsaat bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat bereits 6--8 Wochen VOR letztem Frost moeglich, da Keimlinge frosthart) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 6 | `species.direct_sow_months` |
| Erntemonate | 5; 6; 7; 8; 9 | `species.harvest_months` |
| Bluetemonate | 5; 6; 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 8--15 degC (kuehle Keimer!)
- Minimale Keimtemperatur: 4 degC (sehr langsame Keimung)
- Maximale Keimtemperatur: 20 degC (ueber 20 degC sinkt die Keimrate)
- Keimdauer: 7--14 Tage
- **Dunkelkeimer** -- Samen 3--5 cm tief in die Erde legen
- Saatgut vor der Aussaat 12--24 Stunden in lauwarmem Wasser einweichen (beschleunigt die Keimung)
- Impfung mit Rhizobium leguminosarum empfohlen bei erstmaligem Erbsenanbau auf einer Flaeche
- Substrat: lockere, kalkhaltige Gartenerde, pH 6.0--7.5

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine; rohe Samen enthalten geringe Mengen Lektine und Protease-Inhibitoren, die durch Kochen inaktiviert werden) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (Lektine, Protease-Inhibitoren in Spuren -- vernachlaessigbar bei normaler Ernaehrung) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Pisum sativum (Garden Pea) als ungiftig fuer Katzen und Hunde. ACHTUNG: Nicht verwechseln mit der Duftwicke (Lathyrus odoratus / Sweet Pea), die giftig ist!

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | -- (kein Rueckschnitt noetig; Entspitzen der Triebspitzen foerdert Verzweigung) | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Erbsen werden nicht zurueckgeschnitten. Regelmaessiges Ernten der Huelsen foerdert den Neuansatz. Verwelkte untere Blaetter koennen entfernt werden, um die Luftzirkulation zu verbessern.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in tiefen Toepfen/Balkonkaesten, aber Freiland bevorzugt) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--20 (fuer 3--5 Pflanzen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 50--200 (sortenabhaengig: Zwergsorten 40--60 cm, Hohe Sorten bis 200 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15--30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5--8 (in der Reihe), Reihenabstand 30--50 cm | `species.spacing_cm` |
| Indoor-Anbau | no (zu hoher Lichtbedarf, Erbsen brauchen kuehle Temperaturen und natuerlichen Wind fuer stabile Stiele) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Zwergsorten moeglich, sonniger Standort noetig) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Erbsen bevorzugen kuehle Temperaturen; Gewaechshaus wird zu warm) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (ab 50 cm Wuchshoehe, Reisig, Maschendraht oder Schnuere als Kletterhilfe) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, humose Gartenerde mit guter Drainage. Kalkhaltig (pH 6.0--7.5). Keine stickstoffreiche Erde noetig (Stickstofffixierung). | -- |

**Hinweis:** Erbsen sind klassische Freilandgemuese. Fruehe Aussaat ab Maerz moeglich, da Keimlinge leichten Frost vertragen. Waerme ueber 25 degC fuehrt zu Blueten- und Huelsenabwurf. In heissen Sommern ist der Anbau ab Juli nicht mehr sinnvoll. Optimale Kulturtemperatur: 12--18 degC.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 7--14 | 1 | false | false | medium |
| Saemling (seedling) | 14--21 | 2 | false | false | medium |
| Vegetativ (vegetative) | 21--35 | 3 | false | false | medium |
| Bluete (flowering) | 14--21 | 4 | false | false | low |
| Ernte (harvest) | 14--28 | 5 | true | true | low |

Hinweis: Erbsen sind Kuehlewetter-Kulturen. Die Gesamtkulturdauer betraegt 60--100 Tage je nach Sorte. Markerbsen reifen spaeter als Zuckererbsen. Bei Hitze ueber 25 degC werden Phasen beschleunigt und die Ertraege sinken stark.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (Dunkelkeimer, Samen im Boden) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 8--15 (optimal 10--12) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 4--10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70--85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (Boden gleichmaessig feucht, nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 (volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 (natuerlich, Fruehjahr) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 12--18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 6--12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (volle Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (Langtag foerdert Wachstum und Blueteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 14--20 (optimal 15--18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Erbsen klettern ueber Ranken (Blattranken). Rankhilfe ab ca. 15 cm Hoehe bereitstellen. Stickstoffduengung ist kontraproduktiv -- sie hemmt die Rhizobium-Symbiose und fuehrt zu ueppigem Blattwachstum bei reduziertem Huelsenansatz.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 14--20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (erhoehter Wasserbedarf waehrend Bluete und Huelsenbildung) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 150--300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Erbsen sind Selbstbestaeuber -- keine Insektenbestaebung noetig. Temperaturen ueber 25 degC waehrend der Bluete fuehren zu Bluetenabwurf und stark reduziertem Huelsenansatz. Ausreichende Wasserversorgung ist in dieser Phase kritisch.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Regelmaessiges Ernten (alle 2--3 Tage) foerdert den Neuansatz. Zuckererbsen ernten, wenn die Huelsen noch flach sind. Markerbsen ernten, wenn die Koerner in der Huelse deutlich vorgewoelbt aber noch gruen sind. Ueberreife Huelsen hemmen die Neubildung.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- |
| Saemling | 0-1-1 | 0.4--0.8 | 6.0--7.0 | 40 | 20 | 15 | 2 |
| Vegetativ | 0-1-2 | 0.6--1.0 | 6.0--7.0 | 60 | 30 | 20 | 2 |
| Bluete | 0-2-3 | 0.8--1.2 | 6.0--7.0 | 80 | 40 | 25 | 3 |
| Ernte | 0-1-2 | 0.6--1.0 | 6.0--7.0 | 60 | 30 | 20 | 2 |

Hinweis: Erbsen fixieren ihren eigenen Stickstoff ueber die Rhizobium-Symbiose. Stickstoffduengung (N) ist NICHT erforderlich und sogar kontraproduktiv, da sie die Knollchenbakterien-Bildung hemmt. Kalium und Phosphor foerdern Bluete und Huelsenbildung. pH muss im neutralen bis leicht sauren Bereich liegen (6.0--7.5), da die Rhizobium-Aktivitaet bei niedrigem pH stark eingeschraenkt ist.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 7--14 Tage | Keimblaetter und erstes echtes Blattpaar entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 3--4 Blattpaare, erste Ranken sichtbar, Pflanze greift nach Stuetze |
| Vegetativ -> Bluete | time_based / event_based | 21--35 Tage (Langtagreaktion) | Erste Bluetenknospen in den Blattachseln sichtbar |
| Bluete -> Ernte | time_based | 7--14 Tage nach Bluetebeginn | Erste Huelsen gebildet, Erntereife je nach Sorte (Zucker-/Markerbse) |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Hydro/Coco -- selten bei Erbsen)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | ab Saemling |
| Monocalciumphosphat | div. | supplement | 0-22-0 (+Ca 15%) | 0.10 | 3 | Bluete, Ernte |
| Kaliumsulfat | div. | supplement | 0-0-50 (+S 18%) | 0.08 | 4 | Vegetativ, Bluete |

Hinweis: Mineralische Duengung bei Erbsen ist normalerweise nicht noetig. KEIN Stickstoffduenger verwenden! Nur bei nachgewiesenem Kalium- oder Phosphormangel ergaenzen.

#### Organisch (Outdoor/Beet -- Standardkultur)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 | Herbst/Fruehjahr (Einarbeitung vor Aussaat) | alle |
| Holzasche (kalireich) | Eigenerzeugung | organisch (K-betont) | 50--100 g/m2 | Fruehjahr (Einarbeitung) | light_feeder |
| Algenkalk | div. | Bodenhilfsmittel | 100--200 g/m2 | Herbst (Kalkung bei saurem Boden) | alle |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 0.5 L/m2 | Mai--Juli, alle 21 Tage | light_feeder |
| Schachtelhalmbruehe | Eigenerzeugung | Pflanzenhilfsmittel | 1:5 verduennt, Blattspruehung | Mai--Juli, alle 14 Tage | alle (Pilzpraevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Erbse Standard Freiland")

| Woche | Phase | Massnahme | Hinweise |
|-------|-------|-----------|----------|
| 0 (Vorbereitung) | -- | 2--3 L/m2 Reifkompost einarbeiten, ggf. Algenkalk bei pH < 6.0 | Boden sollte locker und unkrautfrei sein |
| 1--2 | Keimung | Nur Wasser | Kein Duenger noetig |
| 3--5 | Saemling | Nur Wasser | Rhizobium-Knollchen beginnen sich zu bilden |
| 6--8 | Vegetativ | Optional: Beinwelljauche 1:10 | Nur bei sichtbarem Kaliummangel (gelbe Blattspitzen) |
| 9--12 | Bluete/Ernte | Optional: Beinwelljauche 1:10 | Kalium foerdert Huelsenbildung |

### 3.3 Mischungsreihenfolge

> **Bei mineralischer Duengung (selten noetig):**

1. Wasser temperieren (15--20 degC)
2. CalMag (Calcium + Magnesium) -- falls verwendet
3. Phosphatquelle (z.B. Monocalciumphosphat)
4. Kaliumsulfat
5. pH-Korrektur -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen.

### 3.4 Besondere Hinweise zur Duengung

- **KEINEN Stickstoff duengen!** Erbsen fixieren ihren Stickstoff selbst ueber die Symbiose mit Rhizobium leguminosarum. Stickstoffduengung hemmt die Knollchenbildung und fuehrt zu ueppigem Laub bei verringertem Huelsenansatz.
- **Kalium ist der wichtigste Naehrstoff** fuer Erbsen (Huelsenbildung, Krankheitsresistenz). Holzasche oder Beinwelljauche sind ideale organische Kaliumquellen.
- **Kalkbedarf:** Erbsen bevorzugen pH 6.0--7.5. Auf sauren Boeden (pH < 6.0) vor der Aussaat kalken, da die Rhizobium-Aktivitaet bei niedrigem pH stark eingeschraenkt ist.
- **Impfung:** Bei erstmaligem Erbsenanbau auf einer Flaeche ist die Impfung des Saatguts mit Rhizobium-Bakterien empfehlenswert.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Erbsen sind kalkvertraeglich und bevorzugen leicht alkalisches Wasser. Morgens giessen, moeglichst nicht ueber die Blaetter (Mehltau-Gefahr). Gleichmaessige Bodenfeuchte waehrend Bluete und Huelsenbildung kritisch -- Trockenheit fuehrt zu Huelsenabwurf. Staunaesse vermeiden (Wurzelfaeule). | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | -- (keine regelmaessige Duengung noetig) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | -- | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig, Direktsaat) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Beetvorbereitung | Boden lockern, Kompost einarbeiten, ggf. kalken | mittel |
| Marz | Fruehe Aussaat | Direktsaat ins Freiland ab Bodentemperatur 5 degC, Saattiefe 3--5 cm, Reihenabstand 30--40 cm | hoch |
| Apr | Rankhilfe aufstellen + Nachsaat | Reisig oder Maschendraht aufstellen, 2. Satz nachsaeen fuer verlaengerte Ernte | hoch |
| Mai | Pflege | Hacken, Unkraut entfernen, gleichmaessig giessen, auf Blattlaeuse kontrollieren | mittel |
| Jun | Erntebeginn | Zuckererbsen bei flachen Huelsen, Markerbsen bei vorgewoelbten gruenen Koernern ernten, alle 2--3 Tage durchpfluecken | hoch |
| Jul | Haupternte + Saisonende | Letzte Ernte, danach Pflanzen als Gruenduengung in den Boden einarbeiten (Stickstoff!) | hoch |
| Aug | Nachfrucht | Beet fuer Nachfrucht vorbereiten (Salat, Radieschen, Feldsalat profitieren von der Stickstoffanreicherung) | mittel |

### 4.3 Ueberwinterung

Nicht anwendbar -- Erbsen sind einjaehrige Kulturpflanzen. Die Pflanzen sterben nach der Ernte ab. Pflanzenreste in den Boden einarbeiten (Stickstofffixierung nutzen) oder kompostieren.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Erbsenblattlaus (Pea Aphid) | Acyrthosiphon pisum | Grosse gruene Blattlaeuse an Triebspitzen und Huelsen, Honigtau, verkrueppelte Triebe | leaf, stem, flower | vegetative, flowering | easy |
| Erbsenwickler (Pea Moth) | Cydia nigricana | Bohrloecher in Huelsen, Raupenkot und Gespinste an den Koernern, angefressene Samen | fruit | flowering, harvest | medium |
| Blattrandkaefer (Pea Leaf Weevil) | Sitona lineatus | Halbkreisfoermiger Randfass an Blaettern (typisches Merkmal), Larven fressen an Wurzelknollchen | leaf, root | seedling, vegetative | easy |
| Erbsenkaefer (Pea Beetle) | Bruchus pisorum | Bohrloecher in reifen Samen, Larvenentwicklung im Korn | fruit | harvest | medium |
| Schnecken (Slugs/Snails) | Arion spp., Deroceras spp. | Lochfrass an jungen Blaettern und Keimlingen, Schleimspuren | leaf, stem | germination, seedling | easy |
| Thripse (Thrips) | Kakothrips pisivorus | Silbrige Saugschaden an Huelsen und Blaettern | leaf, fruit | flowering | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Brennfleckenkrankheit (Ascochyta Blight) | fungal | Hellbraune, eingesunkene Flecken mit dunklem Rand auf Blaettern, Staengeln und Huelsen | infected_seed, rain_splash, humid_conditions | 5--10 | vegetative, flowering |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser, mehliger Belag auf Blattoberseiten und Huelsen | warm_dry_days_cool_nights, poor_airflow | 7--14 | vegetative, flowering |
| Falscher Mehltau (Downy Mildew) | fungal (Oomycet) | Gelbe Flecken auf Blattoberseite, grauer Sporenbelag auf Blattunterseite | cool_wet_conditions, high_humidity | 5--10 | seedling, vegetative |
| Fusarium-Welke (Fusarium Wilt) | fungal | Welke der gesamten Pflanze, Vergilbung von unten nach oben, Staengelbasis verbaeunt | warm_soil, monoculture | 14--21 | vegetative, flowering |
| Grauschimmel (Grey Mold) | fungal | Grauer pelziger Belag auf Huelsen und Staengeln | high_humidity, dense_planting | 3--5 | flowering, harvest |
| Erbsenrost (Pea Rust) | fungal | Orangebraune Pusteln auf Blaettern und Staengeln | warm_humid_conditions | 7--14 | vegetative, flowering |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Erbsenblattlaus | 5--10 | 14 |
| Aphidius ervi (Schlupfwespe) | Erbsenblattlaus | 2--5 | 14--21 |
| Coccinella septempunctata (Marienkaefer) | Erbsenblattlaus | 5--10 | 7--14 |
| Steinernema feltiae (Nematode) | Schnecken (Bodenstadien) | 250.000/m2 | 7--14 |
| Trichogramma spp. (Eiparasitoid) | Erbsenwickler | 100--200 Puppen/m2 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetze | mechanical | -- | Netz (Maschenweite < 1.3 mm) ueber dem Bestand ab Bluetebeginn | 0 | Erbsenwickler |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage, 3x wiederholen | 0 | Erbsenblattlaus |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Thripse |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Spruehung 1:5 verduennt, alle 14 Tage praeventiv | 0 | Mehltau, Pilzkrankheiten |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau |
| Fruchtfolge (min. 4 Jahre) | cultural | -- | Keine Leguminosen auf gleicher Flaeche innerhalb von 4 Jahren | 0 | Fusarium, Brennfleckenkrankheit, Erbsenwickler |
| Zertifiziertes Saatgut | cultural | -- | Nur gesundes, anerkanntes Saatgut verwenden | 0 | Brennfleckenkrankheit (samenbuertig) |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Fusarium oxysporum f.sp. pisi (Rasse 1, 2) | Krankheit | Viele moderne Cultivare (z.B. 'Kelvedon Wonder', 'Ambassador') | `resistant_to` |
| Erysiphe pisi (Echter Mehltau) | Krankheit | Resistente Cultivare (z.B. 'Markana', 'Spring') | `resistant_to` |
| Pea enation mosaic virus (PEMV) | Krankheit | Einzelne Cultivare mit Virusresistenz | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light) -- durch Stickstofffixierung sogar bodenverbessernd |
| Fruchtfolge-Kategorie | Huelsenfruechte (Fabaceae) |
| Empfohlene Vorfrucht | Getreide, Kartoffeln, Kohl -- nach Starkzehrern die Stickstofffixierung nutzen |
| Empfohlene Nachfrucht | Starkzehrer (Kohl, Tomate, Kuerbis) -- profitieren von der Stickstoffanreicherung im Boden |
| Anbaupause (Jahre) | 4--5 Jahre fuer Fabaceae auf gleicher Flaeche (Fusarium, Ascochyta, Erbsenmuedigkeit) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Moehre / Karotte | Daucus carota | 0.9 | Verschiedene Wurzeltiefen, Erbsen liefern Stickstoff | `compatible_with` |
| Kopfsalat | Lactuca sativa var. capitata | 0.8 | Schnelle Zwischenkultur, Bodenbeschattung | `compatible_with` |
| Radieschen | Raphanus sativus var. sativus | 0.8 | Schnelle Markierungssaat, verschiedene Wurzeltiefen | `compatible_with` |
| Mais | Zea mays | 0.8 | Natuerliche Rankhilfe, Erbsen liefern Stickstoff (Milpa-Prinzip) | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Stickstoffversorgung durch Erbsen | `compatible_with` |
| Fenchel | Foeniculum vulgare | 0.7 | Verschiedene Wurzeltiefen, Nuetzlingsfoerderung | `compatible_with` |
| Kohl | Brassica oleracea | 0.7 | Stickstoffversorgung durch Erbsen | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Schnelle Zwischenkultur, Bodenbeschattung | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Nuetzlinge anlocken (Schwebfliegen), Blattlaus-Kontrolle | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Zwiebel | Allium cepa | Gegenseitige Wuchshemmung, Allicin hemmt Rhizobium-Aktivitaet | moderate | `incompatible_with` |
| Knoblauch | Allium sativum | Wie Zwiebel: Allicin hemmt Knollchenbakterien | moderate | `incompatible_with` |
| Lauch / Porree | Allium porrum | Wie andere Allium-Arten: negative Wechselwirkung mit Rhizobium | moderate | `incompatible_with` |
| Tomate | Solanum lycopersicum | Unterschiedliche Wasserbeduerfnisse, Erbsen moegen es kuehler | mild | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Konkurrenz um Platz und Licht, gemeinsame Bodenschaedlinge | mild | `incompatible_with` |
| Buschbohne / Stangenbohne | Phaseolus vulgaris | Gleiche Familie, Konkurrenz um Rhizobium-Staemme, gemeinsame Krankheiten | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Fabaceae (mit sich selbst) | `shares_pest_risk` | Fusarium, Ascochyta, Erbsenwickler, Erbsenmuedigkeit | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Gartenerbse |
|-----|-------------------|-------------|------------------------------|
| Kichererbse | Cicer arietinum | Gleiche Familie, Huelsenfrucht | Hitzevertraglicher, mediterran |
| Ackerbohne (Dicke Bohne) | Vicia faba | Gleiche Familie, aehnliche Kulturansprueche | Frosthaerter, hoehere Biomasse, bessere Gruenduengung |
| Buschbohne | Phaseolus vulgaris | Gleiche Familie, aehnliche Nutzung | Waermeliebend, hoehere Ertraege pro Flaeche |
| Linse | Lens culinaris | Gleiche Familie, Huelsenfrucht | Trockenheitsvertraglicher |
| Platterbse (Lathyrus sativus) | Lathyrus sativus | Gleiche Familie | Trockenheitsvertraglicher, Notnahrung |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Pisum sativum,Erbse;Gartenerbse;Garden Pea;Green Pea,Fabaceae,Pisum,annual,long_day,vine,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b,-0.3,"Vorderasien (Fruchtbarer Halbmond), Mittelmeerraum"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Markerbse 'Kelvedon Wonder',Pisum sativum,,1925,early_maturing;compact,65,fusarium,open_pollinated
Markerbse 'Ambassador',Pisum sativum,,,high_yield,75,fusarium,open_pollinated
Zuckererbse 'Norli',Pisum sativum,,,early_maturing;compact,55,,open_pollinated
Zuckererbse 'Oregon Sugar Pod',Pisum sativum,,,high_yield,65,,open_pollinated
Knackerbse 'Sugar Snap',Pisum sativum,,1979,high_yield,70,,open_pollinated
Markerbse 'Wunder von Kelvedon',Pisum sativum,,1925,early_maturing;compact;heirloom,65,fusarium,open_pollinated
Zuckererbse 'Ambrosia',Pisum sativum,,,early_maturing;high_yield,60,,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA -- Garden Pea nicht gelistet als giftig fuer Hunde/Katzen
2. Seedforward -- Erbsenkrankheiten und Erbsenschaedlinge: https://seedforward.com/de/blog/die-wichtigsten-erbsenkrankheiten-und-erbsenschaedlinge-im-ueberblick
3. LfL Bayern -- Grosskoernige Leguminosen: https://www.lfl.bayern.de/ips/blattfruechte/182266/index.php
4. pflanzenkrankheiten.ch -- Erbsen: https://www.pflanzenkrankheiten.ch/krankheiten-an-kulturpflanzen/huelsenfruechte/erbsen-pisum-sativum
5. Bio-Gaertner -- Erbsen: https://www.bio-gaertner.de/Pflanzen/Erbsen
6. naturadb.de -- Erbse: https://www.naturadb.de/pflanzen/pisum-sativum/
7. gartenjournal.net -- Erbsen Schaedlinge: https://www.gartenjournal.net/erbsen-schaedlinge-krankheiten
8. grove.eco -- Erbse: https://www.grove.eco/pflanzen/pisum-sativum/
9. MechaTronix -- PPFD/DLI per Crop: https://www.horti-growlight.com/en/typical-ppfd-and-dli-values-per-crop
10. Koraylights -- Indoor cultivation PPFD and DLI: https://koraylights.com/how-much-light-do-your-plants-need-indoor-cultivation-ppfd-and-dli/
11. hoklartherm.de -- Mischkultur Tabelle: https://www.hoklartherm.de/ratgeber/mischkultur-im-gemuesegarten-was-vertraegt-sich/
