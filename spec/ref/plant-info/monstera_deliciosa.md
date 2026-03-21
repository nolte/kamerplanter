# Fensterblatt -- Monstera deliciosa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** ASPCA, NASA Clean Air Study (Wolverton 1989), University of Minnesota Extension, NCSU Plant Toolbox, Royal Horticultural Society, Cummings & Waring 2020

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Monstera deliciosa | `species.scientific_name` |
| Volksnamen (DE/EN) | Fensterblatt, Koestliches Fensterblatt; Swiss Cheese Plant, Monstera, Fruit Salad Plant | `species.common_names` |
| Familie | Araceae | `species.family` -> `botanical_families.name` |
| Gattung | Monstera | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 40+ (Indoor: 10-20) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |

<!-- MN-001: dormancy_required: false ist biologisch korrekt -- Monstera hat keine obligate Ruhephase (keine Knospenruhe, kein Laubeinzug). Die saisonale Wachstumsverlangsamung im mitteleuropaeischen Winter (Nov-Feb) durch reduziertes Tageslicht (DLI 1-3 mol/m²/d) wird als kulturpraktische DORMANCY-Phase im Naehrstoffplan abgebildet (vgl. REQ-003 v2.3). -->
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b, 12a, 12b | `species.hardiness_zones` |
| Frostempfindlichkeit | sensitive | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10 C, optimal 18-27 C. Bei unter 12 C Wachstumsstillstand. | `species.hardiness_detail` |
| Heimat | Tropische Regenwaelder Suedmexikos bis Panama | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfaellt (reine Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Entfaellt | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | Entfaellt | `species.direct_sow_months` |
| Erntemonate | Entfaellt (Fruchtbildung Indoor extrem selten) | `species.harvest_months` |
| Bluetemonate | Entfaellt (Bluete Indoor aeusserst selten, nur nach 3+ Jahren bei optimalen Bedingungen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division, layering | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge muessen mindestens einen Knoten (Node) mit Achselknospe enthalten. Luftwurzeln am Steckling beschleunigen die Bewurzelung, sind aber nicht zwingend erforderlich. Bewurzelung in Wasser (2-4 Wochen) oder direkt im Substrat moeglich. Luftschichtung (Air Layering) ist die sicherste Methode mit geringstem Verlustrisiko.

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Calciumoxalat-Raphiden und Milchsaft koennen bei empfindlichen Personen Kontaktdermatitis ausloesen; Handschuhe beim Schneiden und Umtopfen empfohlen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken:** Brennen und Schwellung im Mund- und Rachenraum, vermehrter Speichelfluss, Schluckbeschwerden, Erbrechen. Die nadelfoermigen Calciumoxalat-Raphiden durchstechen die Schleimhaut und verursachen mechanische und chemische Reizung. Bei Haustieren: Pfoten am Maul reiben, Speichelfluss, Appetitlosigkeit. Quelle: ASPCA Animal Poison Control.

### 1.5 Luftreinigung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde | `species.removes_compounds` |

**Hinweis:** Monstera deliciosa war nicht direkt Teil der originalen NASA Clean Air Study (Wolverton 1989), wird aber in der breiteren Forschung als maessig luftreinigend eingestuft. Die grossen Blaetter ermoeglichen eine ueberdurchschnittliche Absorption von Formaldehyd. Caveat: Bei realistischen Pflanzendichten in Wohnraeumen ist der Effekt vernachlaessigbar (Cummings & Waring 2020).

### 1.6 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 3, 4, 5 | `species.pruning_months` |

**Hinweis:** Formschnitt im Fruehjahr zu Beginn der Wachstumsperiode. Zu lange Triebe kuerzen, immer oberhalb eines Knotens schneiden. Luftwurzeln koennen eingekuerzt, sollten aber nicht komplett entfernt werden (sie dienen der Naehrstoff- und Wasseraufnahme).

### 1.7 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--20 (je nach Alter und Groesse) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 100--300 (Indoor, an Kletterhilfe) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80--150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfaellt (reine Zimmerpflanze in Mitteleuropa) | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Sommer, geschuetzt, kein direktes Sonnenlicht) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Moosstab, Kokosstab oder Gitter -- Kletterpflanze mit Luftwurzeln) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Grobe, durchlaessige Mischung: Zimmerpflanzenerde (50--60%), Orchideenrinde (20--30%), Perlite (10--20%). Staunaesse unbedingt vermeiden. | -- |

**Hinweis:** Monstera deliciosa ist eine klassische Topf-/Zimmerpflanze. In Mitteleuropa ausschliesslich Indoor oder im beheizten Gewaechshaus. Der Topf sollte grosszuegig gewaehlt werden, da die Pflanze kraeftige Wurzeln bildet. Umtopfen alle 1--2 Jahre in einen ca. 5 cm groesseren Topf. Schwere Toepfe (Ton/Keramik) bieten bessere Stabilitaet fuer grosse Exemplare mit Kletterhilfe.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

Monstera deliciosa ist eine perenniale Zimmerpflanze ohne festes Ernte-Ziel. Die Phasen beschreiben den Lebenszyklus von der Vermehrung bis zur etablierten Pflanze mit jaehrlich wiederkehrendem saisonalem Rhythmus.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung (Propagation) | 14-28 | 1 | false | false | low |
| Juvenil (Juvenile) | 60-180 | 2 | false | false | low |
| Aktives Wachstum (Active Growth, Maerz-Oktober) | saisonal, ca. 210 | 3 | false | false | medium |
| Ruheperiode (Maintenance, November-Februar) | saisonal, ca. 120 | 4 | false | false | medium |

**Anmerkung:** Die Phasen "Aktives Wachstum" und "Ruheperiode" wiederholen sich jaehrlich (`is_recurring: true`). Es gibt keine terminale Phase -- Monstera ist langlebig.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Bewurzelung (Propagation)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50-100 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3-5 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 22-26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70-80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70-80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6-0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | Substrat konstant feucht, nicht nass | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50-100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Juvenil (Juvenile)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 75-150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 4-8 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 22-28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60-70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60-70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5-7 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100-200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Aktives Wachstum (Maerz-Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100-350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 6-12 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 3.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 22-28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55-70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5-7 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200-500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Ruheperiode (November-Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50-150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3-6 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 1.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 10-12 (natuerlich kuerzer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 18-24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40-60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45-60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 10-14 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 150-300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS/cm) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|-----------------|---------|-----|----------|----------|---------|----------|
| Bewurzelung | 0:0:0 | 0.0 | 5.5-6.5 | -- | -- | -- | -- |
| Juvenil | 1:1:1 | 0.4-0.8 | 5.5-6.5 | 40 | 20 | -- | 1 |
| Aktives Wachstum | 3:1:2 | 0.8-1.4 | 5.5-6.5 | 80 | 40 | -- | 2 |
| Ruheperiode | 0:0:0 | 0.0 | 5.5-6.5 | -- | -- | -- | -- |

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Bewurzelung -> Juvenil | conditional | 14-28 Tage | Wurzeln 5+ cm, neuer Trieb sichtbar |
| Juvenil -> Aktives Wachstum | time_based | 60-180 Tage | Pflanze etabliert, 3+ Blaetter |
| Aktives Wachstum -> Ruheperiode | event_based | saisonal (November) | Tageslaenge/Temperatur sinken |
| Ruheperiode -> Aktives Wachstum | event_based | saisonal (Maerz) | is_cycle_restart: true |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Zimmerpflanzen-Fluessigduenger)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Gruenpflanzen- und Palmenduenger | COMPO | Fluessigduenger | 7-3-6 | 7 ml / 1 L Wasser | Aktives Wachstum (Maerz-Oktober) |
| Gruenpflanzen-Nahrung | Substral | Fluessigduenger | 7-3-5 | 7 ml / 1 L Wasser | Aktives Wachstum (Maerz-Oktober) |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Gruenpflanzen- und Palmenduenger | COMPO BIO | Bio-Fluessigduenger | 7 ml / 1 L | Maerz-Oktober | Alle Gruenpflanzen |
| Wurmhumus | diverse | organisch, fest | 10-20% Beimischung beim Umtopfen | Fruehling | Alle Zimmerpflanzen |

### 3.2 Duengungsplan (Beispiel-NutrientPlan)

| Zeitraum | Phase | EC (mS/cm) | pH | COMPO 7-3-6 (ml/L) | Hinweise |
|----------|-------|---------|-----|---------------------|----------|
| Maerz-April | Wachstumsbeginn | 0.6-0.8 | 5.5-6.5 | 3-5 (halbe Dosis) | Langsam einsteigen nach Winterpause |
| Mai-August | Hauptwachstum | 0.8-1.4 | 5.5-6.5 | 7 (volle Dosis) | Alle 2 Wochen |
| September-Oktober | Wachstumsende | 0.4-0.8 | 5.5-6.5 | 3-5 (halbe Dosis) | Abklingen lassen |
| November-Februar | Ruheperiode | 0.0 | 5.5-6.5 | 0 | Keine Duengung |

### 3.3 Mischungsreihenfolge

Bei Zimmerpflanzen-Fluessigduengern ist die Mischungsreihenfolge weniger kritisch als bei Hydroponiksystemen, da Komplett-Duenger vorgemischt sind:

1. Frisches, temperiertes Wasser (Zimmertemperatur) vorbereiten
2. Fluessigduenger einmischen und umruehren
3. pH-Korrektur bei Zimmerpflanzen in Erde normalerweise nicht noetig

### 3.4 Besondere Hinweise zur Duengung

- **Ueberdosierung vermeiden:** Monstera reagiert empfindlich auf Salzueberschuss (braune Blattspitzen). Im Zweifel halbe Dosis verwenden.
- **Substrat-Spuelung:** Alle 3-4 Monate Substrat gruendlich mit klarem Wasser durchspuelen, um Salzakkumulationen auszuwaschen.
- **Kalzium-Bedarf:** Moderat. Bei kalkarmem Giesswasser (Regenwasser, Osmosewasser) gelegentlich Kalzium ergaenzen.
- **Blattpflege:** Grosse Blaetter regelmaessig mit feuchtem Tuch abwischen -- foerdert Lichtaufnahme und beugt Schaedlingsbefall vor.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | null (Leitungswasser OK) | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3, 4, 5, 6, 7, 8, 9, 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18 | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |
| Luftfeuchtigkeitspruefungs-Intervall (Tage) | 14 | `care_profiles.humidity_check_interval_days` |

**Giessanleitung (top_water):** Von oben langsam und gleichmaessig giessen, bis Wasser aus den Abzugsloechern laeuft. Ueberschuss nach 30 Minuten entfernen. Obere 3-5 cm zwischen den Giessintervallen abtrocknen lassen (Fingerprobe). Monstera vertraegt kurzfristige Trockenheit besser als dauerhafte Naesse.

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan-Feb | Blattpflege, Schaedlingskontrolle | Blaetter abstauben, auf Schaedlinge pruefen (trockene Heizungsluft) | mittel |
| Maerz | Wachstumsstart | Duengung starten (halbe Dosis), Rankhilfe pruefen | hoch |
| April | Umtopfen | Bei Bedarf umtopfen (alle 18-24 Monate), frisches Substrat | mittel |
| Mai-Aug | Hauptwachstum | Volle Duengung alle 2 Wochen, regelmaessig giessen | mittel |
| Sep-Okt | Wachstumsende | Duengung reduzieren, Giessintervalle verlaengern | niedrig |
| Nov-Dez | Ruheperiode | Keine Duengung, reduziert giessen. Standort-Lichtcheck. Nicht unter 16 C. | niedrig |

### 4.3 Ueberwinterung

Entfaellt -- reine Zimmerpflanze, ganzjaehrig Indoor bei Raumtemperatur. Im Winter lediglich Giessen reduzieren und Duengung einstellen.

### 4.4 Standort-Empfehlungen

- **Optimal:** Helles Ostfenster oder leicht zurueckgesetzt an Suedfenster (keine direkte Mittagssonne)
- **Akzeptabel:** Westfenster, Nordfenster mit Zusatzbeleuchtung
- **Vermeiden:** Direkte Suedsonnenexposition (Blattverbrennungen), Standort neben Heizkoerper, Zugluft
- **Kletterhilfe:** Moosstab, Kokosfaserstab oder Spalier -- foerdert groessere Blaetter mit mehr Fenestrierung (Blattlochbildung)
- **Luftfeuchtigkeit:** 50-70% optimal. Bei trockener Heizungsluft: Luftbefeuchter oder regelmaessig besprühen

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste an Blattunterseiten, gelbe Stippen, fahle Blaetter | leaf | Alle (verstaerkt bei trockener Heizungsluft im Winter) | medium |
| Thrips | Frankliniella occidentalis | Silbrige Streifen auf Blattoberseiten, schwarze Kotkrumel | leaf | Aktives Wachstum | medium |
| Wolllaeusse (Mealybug) | Pseudococcidae | Weisse wachsartige Klumpen an Blattachseln, Honigtau | leaf, stem | Alle | easy |
| Schildlaeusse (Scale) | Coccoidea | Braune Hoecker an Stielen und Blattadern, Honigtau, Russtaupilze | stem, leaf | Alle | medium |
| Trauermuecken (Fungus Gnat) | Bradysia spp. | Kleine schwarze Fliegen im Substrat, Larven an Wurzeln | root | Bewurzelung, Juvenil | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfaeule (Root Rot) | fungal | Welke trotz feuchtem Substrat, braune matschige Wurzeln, Faeulnisgeruch | overwatering, poor_drainage | 7-21 | Alle |
| Blattfleckenkrankheit (Leaf Spot) | fungal / bacterial | Braune oder schwarze Flecken mit gelbem Hof | high_humidity, poor_airflow, wet_leaves | 5-14 | Aktives Wachstum |
| Russtaupilze (Sooty Mold) | fungal | Schwarzer Belag auf Blaettern (Sekundaerbefall nach Schaedlingsbefall) | pest_honeydew | 3-7 | Alle |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5-10 | 14-21 |
| Amblyseius cucumeris | Thrips (Larven) | 50-100 (Streubeutel) | 14-28 |
| Cryptolaemus montrouzieri | Wolllaeusse | 2-5 | 14-21 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeusse, Wolllaeusse | 5-10 | 14 |
| Steinernema feltiae (Nematoden) | Trauermuecken-Larven | Giessbehandlung | 7-14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoel | biological | Azadirachtin | Spruehen, 0.3-0.5% Loesung, alle 7 Tage | 0 (Zierpflanze) | Blattlaeusse, Wolllaeusse, Spinnmilben, Thrips |
| Schmierseife | biological | Kaliumsalze von Fettsaeuren | Spruehen, 1-2% Loesung | 0 | Blattlaeusse, Wolllaeusse, Spinnmilben |
| Alkohol-Abwischen | mechanical | Isopropanol 70% | Wattestab auf befallene Stellen | 0 | Wolllaeusse, Schildlaeusse |
| Gelbtafeln | mechanical | -- | Aufstellen neben Pflanze | 0 | Trauermuecken (Adulte), Thrips (Monitoring) |
| Blaetter abbrausen | cultural | -- | Warme Dusche alle 2-4 Wochen | 0 | Spinnmilben, Staub |

### 5.5 Resistenzen der Art

Monstera deliciosa hat keine besonderen Resistenzen gegen Krankheiten oder Schaedlinge. Gesunde Pflanzen mit guter Luftzirkulation und korrekter Bewaesserung sind die beste Praevention.

---

## 6. Fruchtfolge & Mischkultur

Entfaellt (reine Zimmerpflanze). Fruchtfolge und Mischkultur sind Konzepte des Freilandanbaus und haben fuer Monstera als Zimmerpflanze keine Relevanz.

### 6.1 Standort-Nachbarn (Indoor-Empfehlungen)

| Partner | Wissenschaftl. Name | Begruendung |
|---------|-------------------|-------------|
| Herzblatt-Philodendron | Philodendron hederaceum | Gleiche Familie (Araceae), aehnliche Ansprueche |
| Nestfarn | Asplenium nidus | Aehnliche Luftfeuchtigkeitsansprueche, dekorativer Kontrast |
| Efeutute | Epipremnum aureum | Gleiche Familie (Araceae), kann am selben Moosstab klettern |
| Calathea | Calathea orbifolia | Aehnlicher Lichtbedarf, hoher Luftfeuchtigkeitsbedarf |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Monstera deliciosa |
|-----|-------------------|-------------|--------------------------------------|
| Monstera Monkey Mask | Monstera adansonii | Gleiche Gattung, kleinere Blaetter mit Loechern | Kompakter, besser fuer kleine Raeume |
| Mini-Monstera | Rhaphidophora tetrasperma | Aehnliche Blattform, gleiche Familie | Deutlich kompakter, schneller wachsend |
| Efeutute | Epipremnum aureum | Gleiche Familie, Kletterpflanze | Robuster, anspruchsloser, ideal fuer Anfaenger |
| Herzblatt-Philodendron | Philodendron hederaceum | Gleiche Familie, Kletterpflanze | Kompakter, haengende Wuchsform moeglich |
| Philodendron Xanadu | Philodendron xanadu | Gleiche Familie, gefiederte Blaetter | Selbsttragend, kein Klettern noetig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,air_purification_score
Monstera deliciosa,Fensterblatt;Swiss Cheese Plant;Monstera,Araceae,Monstera,perennial,day_neutral,vine,aerial,10a;10b;11a;11b;12a;12b,0.0,Tropische Regenwaelder Suedmexikos bis Panama,sensitive,medium_feeder,false,ornamental,0.5
```

### 8.2 BotanicalFamily CSV-Zeile (falls noch nicht vorhanden)

```csv
name,common_name_de,common_name_en,order,typical_nutrient_demand,nitrogen_fixing,typical_root_depth,frost_tolerance,pollination_type
Araceae,Aronstabgewaechse,Arum family,Alismatales,medium,false,SHALLOW,SENSITIVE,INSECT
```

### 8.3 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type
Thai Constellation,Monstera deliciosa,Tissue Culture Lab Thailand,2010,variegated;compact,clone
Albo Variegata,Monstera deliciosa,--,--,variegated,clone
Borsigiana,Monstera deliciosa,--,--,compact;fast_growing,clone
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Monstera deliciosa: https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants/cutleaf-philodendron
2. University of Minnesota Extension -- Propagating Monstera deliciosa: https://extension.umn.edu/houseplants/propagating-monstera-deliciosa
3. NASA Clean Air Study (Wolverton 1989): https://ntrs.nasa.gov/citations/19930072988
4. Cummings & Waring (2020) -- Potted plants do not improve indoor air quality (Journal of Exposure Science & Environmental Epidemiology)
5. NCSU Plant Toolbox -- Monstera: https://plants.ces.ncsu.edu/plants/monstera-deliciosa/
6. Royal Horticultural Society -- Monstera deliciosa: https://www.rhs.org.uk/plants/monstera-deliciosa
7. COMPO Gruenpflanzen- und Palmenduenger: https://www.compo.de/
