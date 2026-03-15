# Einblatt -- Spathiphyllum wallisii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** ASPCA, NASA Clean Air Study (Wolverton 1989), Missouri Botanical Garden, NCSU Plant Toolbox, Old Farmer's Almanac, Cummings & Waring 2020

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Spathiphyllum wallisii | `species.scientific_name` |
| Volksnamen (DE/EN) | Einblatt, Blattfahne, Friedenslilie, Scheidenblatt; Peace Lily, White Sails, Spathe Flower | `species.common_names` |
| Familie | Araceae | `species.family` -> `botanical_families.name` |
| Gattung | Spathiphyllum | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Wurzelanpassungen | -- | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10-20 (Indoor) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10b, 11a, 11b, 12a, 12b | `species.hardiness_zones` |
| Frostempfindlichkeit | sensitive | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 13 C, optimal 18-24 C. Kaelteschaden ab unter 10 C. | `species.hardiness_detail` |
| Heimat | Tropische Regenwaelder Kolumbiens und Venezuelas | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfaellt (reine Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Entfaellt | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | Entfaellt | `species.direct_sow_months` |
| Erntemonate | Entfaellt | `species.harvest_months` |
| Bluetemonate | Bluete Indoor moeglich bei ausreichend Licht, typisch Fruehjahr-Sommer (4, 5, 6, 7, 8) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Spathiphyllum wird ausschliesslich durch Teilung vermehrt. Reife Pflanzen bilden Ableger (Kindel) am Rhizom, die im Fruehjahr vorsichtig abgetrennt werden koennen. Jede Teilung muss eigene gesunde Wurzeln und mindestens 2-3 Blaetter haben. Stecklingsvermehrung ist nicht moeglich. Vermehrung durch Samen ist theoretisch moeglich, aber in der Praxis nicht ueblich und aeusserst langwierig.

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken:** Identisch mit anderen Araceae -- Brennen und Schwellung im Mund- und Rachenraum, Speichelfluss, Schluckbeschwerden, Erbrechen durch Calciumoxalat-Raphiden. Bei Katzen und Hunden: orale Reizung, Pfoten am Maul reiben, Appetitlosigkeit. Quelle: ASPCA Animal Poison Control.

**Pollenallergie:** Die Bluetenkolben (Spadix) produzieren Pollen, der bei empfindlichen Personen allergische Reaktionen ausloesen kann. In Haushalten mit Pollenallergikern: Bluetenkolben vor dem Oeffnen abschneiden.

### 1.5 Luftreinigung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Luftreinigungs-Score | 0.9 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, trichloroethylene, xylene, ammonia | `species.removes_compounds` |

**Hinweis:** Spathiphyllum war einer der Spitzenreiter in der NASA Clean Air Study (Wolverton 1989). Es ist eine der wenigen Pflanzen, die alle fuenf getesteten Schadstoffe filtern, einschliesslich Ammoniak. Die Phytoremediation erfolgt sowohl ueber die Blaetter als auch ueber die Wurzelzone (Rhizosphaere). Caveat: Bei realistischen Pflanzendichten in Wohnraeumen ist der Effekt vernachlaessigbar (Cummings & Waring 2020).

### 1.6 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

**Hinweis:** Kein regulaerer Rueckschnitt noetig. Verblühte Bluetenstaende und vergilbte oder braune Blaetter an der Basis abschneiden. Blatttriebe nicht kuerzen -- Spathiphyllum regeneriert nicht aus gekuerzten Blaettern.

### 1.7 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2--5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfaellt (reine Zimmerpflanze in Mitteleuropa) | `species.spacing_cm` |
| Indoor-Anbau | yes (ideale Zimmerpflanze, toleriert wenig Licht) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Sommer, Halbschatten, kein direktes Sonnenlicht, kein Wind) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, humose Zimmerpflanzenerde mit Perlite-Anteil (10--20%) fuer gute Drainage. Leicht sauer (pH 5.5--6.5). | -- |

**Hinweis:** Spathiphyllum ist eine ideale Zimmerpflanze fuer schattige bis halbschattige Standorte. Sie eignet sich besonders fuer Badezimmer (hohe Luftfeuchtigkeit). Der Topf sollte nicht zu gross gewaehlt werden -- leicht eingeengte Wurzeln foerdern die Bluete. Umtopfen nur wenn die Wurzeln den Topf vollstaendig ausfuellen.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

Spathiphyllum wallisii ist eine perenniale Zimmerpflanze. Sie kann Indoor zur Bluete gebracht werden, wenn sie genuegend indirektes Licht erhaelt. Bluete ist bei Zimmerpflanzen jedoch kein Ernte-Ziel.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung (nach Teilung/Kauf) | 14-30 | 1 | false | false | low |
| Aktives Wachstum (Active Growth, Maerz-Oktober) | saisonal, ca. 210 | 2 | false | false | medium |
| Bluete (Flowering, bei ausreichend Licht) | 30-60 | 3 | false | false | medium |
| Ruheperiode (Maintenance, November-Februar) | saisonal, ca. 120 | 4 | false | false | medium |

**Anmerkung:** "Aktives Wachstum" und "Ruheperiode" sind wiederkehrend (`is_recurring: true`). Die Bluete ist optional und nicht garantiert -- sie tritt nur bei ausreichend Licht (helles indirektes Licht ueber laengeren Zeitraum) ein. Keine terminale Phase.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Etablierung (nach Teilung/Kauf)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 30-75 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 2-4 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 1.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 20-24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60-70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60-70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6-0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 4-5 (Substrat gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100-200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Aktives Wachstum (Maerz-Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50-200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3-8 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 20-26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50-65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5-7 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 150-400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (Flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100-250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 5-10 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 3.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 22-26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55-65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5-7 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 150-400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Ruheperiode (November-Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 30-100 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 2-4 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 1.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 10-12 (natuerlich kuerzer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 18-22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 15-18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40-60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45-60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7-10 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100-250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS/cm) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|-----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 0:0:0 | 0.0 | 5.5-6.5 | -- | -- | -- | -- |
| Aktives Wachstum | 3:1:2 | 0.4-0.8 | 5.5-6.5 | 40 | 20 | -- | 1 |
| Bluete | 2:3:2 | 0.4-0.8 | 5.5-6.5 | 40 | 25 | -- | 1 |
| Ruheperiode | 0:0:0 | 0.0 | 5.5-6.5 | -- | -- | -- | -- |

**Hinweis:** Spathiphyllum ist ein Schwachzehrer und reagiert empfindlich auf Ueberdüngung. Fluessigduenger immer auf halbe Konzentration verduennen. Bei EC ueber 1.0 mS drohen Blattrandnekrosen (braune Blattspitzen).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung -> Aktives Wachstum | conditional | 14-30 Tage | Keine Welke mehr, neuer Blattaustrieb |
| Aktives Wachstum -> Bluete | event_based | bei ausreichend Licht | DLI > 5 ueber mehrere Wochen, Pflanze muss adult sein |
| Aktives Wachstum -> Ruheperiode | event_based | saisonal (November) | Tageslaenge/Temperatur sinken |
| Bluete -> Aktives Wachstum | time_based | 30-60 Tage | Bluetenstand verblueht |
| Ruheperiode -> Aktives Wachstum | event_based | saisonal (Maerz) | is_cycle_restart: true |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Zimmerpflanzen-Fluessigduenger)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Bluehpflanzenduenger | COMPO | Fluessigduenger | 3-4-5 | 3-4 ml / 1 L Wasser (halbe Dosis!) | Bluete |
| Gruenpflanzen- und Palmenduenger | COMPO | Fluessigduenger | 7-3-6 | 3-4 ml / 1 L Wasser (halbe Dosis!) | Aktives Wachstum |
| Gruenpflanzen-Nahrung | Substral | Fluessigduenger | 7-3-5 | 3-4 ml / 1 L Wasser (halbe Dosis!) | Aktives Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Gruenpflanzen- und Palmenduenger | COMPO BIO | Bio-Fluessigduenger | 3-4 ml / 1 L (halbe Dosis!) | Maerz-September | Schwachzehrer |
| Wurmhumus | diverse | organisch, fest | 10% Beimischung beim Umtopfen | Fruehling | Alle Zimmerpflanzen |

### 3.2 Duengungsplan (Beispiel-NutrientPlan)

| Zeitraum | Phase | EC (mS/cm) | pH | COMPO 7-3-6 (ml/L) | Hinweise |
|----------|-------|---------|-----|---------------------|----------|
| Maerz-April | Wachstumsbeginn | 0.3-0.5 | 5.5-6.5 | 2-3 (Viertel-Dosis) | Vorsichtig starten |
| Mai-August | Hauptwachstum | 0.4-0.8 | 5.5-6.5 | 3-4 (halbe Dosis) | Alle 2-3 Wochen |
| September | Wachstumsende | 0.3-0.5 | 5.5-6.5 | 2-3 (Viertel-Dosis) | Abklingen lassen |
| Oktober-Februar | Ruheperiode | 0.0 | 5.5-6.5 | 0 | Keine Duengung |

### 3.3 Mischungsreihenfolge

Wie bei allen Zimmerpflanzen-Fluessigduengern:

1. Frisches, temperiertes Wasser (Zimmertemperatur) vorbereiten
2. Fluessigduenger einmischen und umruehren
3. pH-Korrektur bei Zimmerpflanzen in Erde normalerweise nicht noetig

### 3.4 Besondere Hinweise zur Duengung

- **Schwachzehrer:** Spathiphyllum braucht nur wenig Duenger. Ueberdüngung ist die haeufigste Fehlerquelle -- typisches Symptom: braune Blattspitzen.
- **Halbe Dosis:** Immer nur 50% der Herstellerangabe verwenden. Lieber oefter und duenner als selten und konzentriert.
- **Substrat-Spuelung:** Alle 2-3 Monate Substrat gruendlich mit klarem Wasser durchspuelen.
- **Bluetefoerderung:** Fuer Bluetenbildung kann im Fruehjahr kurzzeitig auf Bluehpflanzenduenger (hoeherer P-Anteil) umgestellt werden.
- **Bei braunen Blattspitzen:** Haeufigste Ursachen (in dieser Reihenfolge): 1. Ueberdüngung, 2. Trockene Luft, 3. Chlor/Fluor im Leitungswasser.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Weiches Wasser bevorzugt. Abgestandenes Leitungswasser oder Regenwasser verwenden -- reagiert empfindlich auf Chlor und Fluor. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3, 4, 5, 6, 7, 8, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18 | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |
| Luftfeuchtigkeitspruefungs-Intervall (Tage) | 14 | `care_profiles.humidity_check_interval_days` |

**Giessanleitung (top_water):** Von oben gleichmaessig giessen, bis Wasser aus den Abzugsloechern laeuft. Ueberschuss nach 30 Minuten entfernen. Obere 2-3 cm abtrocknen lassen -- Spathiphyllum zeigt Welke (haengende Blaetter) als natuerliches Durst-Signal. Pflanze erholt sich nach dem Giessen innerhalb weniger Stunden vollstaendig. Trotzdem nicht warten bis zur Welke, da wiederholter Trockenstress die Pflanze schwaecht.

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan-Feb | Blattpflege | Blaetter abstauben, Luftfeuchte pruefen (Heizungsluft). Verblühte Bluetenstaende entfernen. | mittel |
| Maerz | Wachstumsstart | Duengung starten (Viertel-Dosis), Teilung wenn Pflanze zu gross geworden ist | hoch |
| April | Umtopfen | Bei Bedarf umtopfen (alle 18 Monate), frisches Substrat | mittel |
| Mai-Aug | Hauptwachstum | Duengung alle 3 Wochen (halbe Dosis), regelmaessig giessen | mittel |
| Sep | Wachstumsende | Duengung einstellen | niedrig |
| Okt-Dez | Ruheperiode | Keine Duengung, reduziert giessen. Standort-Lichtcheck. Nicht unter 16 C. | niedrig |

### 4.3 Ueberwinterung

Entfaellt -- reine Zimmerpflanze, ganzjaehrig Indoor bei Raumtemperatur. Im Winter lediglich Giessen reduzieren und Duengung einstellen. Spathiphyllum ist kaelteempfindlicher als Monstera -- Minimum 15 C.

### 4.4 Standort-Empfehlungen

- **Optimal:** Halbschattiger bis schattiger Standort, Nord- oder Ostfenster, zurueckgesetzt vom Fenster. Ideal fuer lichtarme Raeume -- eine der wenigen Zimmerpflanzen die bei wenig Licht noch gedeiht (und sogar blueht).
- **Akzeptabel:** Badezimmer (hohe Luftfeuchtigkeit), Buero mit Kunstlicht
- **Vermeiden:** Direkte Sonneneinstrahlung (Blattverbrennungen), Zugluft, kalte Fensterbank im Winter
- **Luftfeuchtigkeit:** 50-60% optimal. Bei trockener Heizungsluft: Luftbefeuchter, Kiesbett mit Wasser unter dem Topf, regelmaessig besprühen
- **Besonderheit:** Hervorragende Badezimmerpflanze -- profitiert von der hohen Luftfeuchtigkeit und kommt mit wenig Licht zurecht

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, gelbe Stippen, fahle Blaetter | leaf | Alle (verstaerkt bei trockener Heizungsluft im Winter) | medium |
| Wolllaeusse (Mealybug) | Pseudococcidae | Weisse wachsartige Klumpen an Blattachseln und Blattunterseiten | leaf, stem | Alle | easy |
| Schildlaeusse (Scale) | Coccoidea | Braune Hoecker an Blattstielen und -adern | stem, leaf | Alle | medium |
| Blattlaeusse (Aphids) | Aphididae | Kolonie an jungen Trieben und Bluetenstielen, Honigtau, kraeuselende Blaetter | leaf, flower | Aktives Wachstum, Bluete | easy |
| Trauermuecken (Fungus Gnat) | Bradysia spp. | Kleine schwarze Fliegen, Larven an Wurzeln | root | Alle | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfaeule (Root Rot) | fungal | Welke trotz feuchtem Substrat, braune matschige Wurzeln, Faeulnisgeruch | overwatering, poor_drainage | 7-21 | Alle |
| Blattfleckenkrankheit (Leaf Spot) | fungal (Cylindrocladium) | Braune oder schwarze nasse Flecken | high_humidity, poor_airflow, wet_leaves | 5-14 | Aktives Wachstum |
| Rhizomfaeule | fungal (Phytophthora) | Gesamte Pflanze welkt, Rhizom ist weich und dunkel verfaerbt | overwatering, contaminated_substrate | 14-28 | Alle |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5-10 | 14-21 |
| Cryptolaemus montrouzieri | Wolllaeusse | 2-5 | 14-21 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeusse | 5-10 | 14 |
| Steinernema feltiae (Nematoden) | Trauermuecken-Larven | Giessbehandlung | 7-14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoel | biological | Azadirachtin | Spruehen, 0.3-0.5% Loesung, alle 7 Tage | 0 (Zierpflanze) | Blattlaeusse, Wolllaeusse, Spinnmilben |
| Schmierseife | biological | Kaliumsalze von Fettsaeuren | Spruehen, 1-2% Loesung | 0 | Blattlaeusse, Wolllaeusse, Spinnmilben |
| Alkohol-Abwischen | mechanical | Isopropanol 70% | Wattestab auf befallene Stellen | 0 | Wolllaeusse, Schildlaeusse |
| Gelbtafeln | mechanical | -- | Aufstellen neben Pflanze | 0 | Trauermuecken (Adulte) |
| Luftfeuchte erhoehen | cultural | -- | Besprühen, Luftbefeuchter, Kiesbett | 0 | Spinnmilben (Praevention) |
| Blattdusche | cultural | -- | Warme Dusche alle 2-4 Wochen | 0 | Spinnmilben, Staub |

### 5.5 Resistenzen der Art

Spathiphyllum wallisii hat keine besonderen Resistenzen. Die Art ist jedoch insgesamt robust und widerstandsfaehig, wenn Grundbeduerfnisse (indirektes Licht, gleichmaessige Feuchtigkeit, keine Staunaesse) erfuellt sind.

---

## 6. Fruchtfolge & Mischkultur

Entfaellt (reine Zimmerpflanze). Fruchtfolge und Mischkultur sind Konzepte des Freilandanbaus und haben fuer Spathiphyllum als Zimmerpflanze keine Relevanz.

### 6.1 Standort-Nachbarn (Indoor-Empfehlungen)

| Partner | Wissenschaftl. Name | Begruendung |
|---------|-------------------|-------------|
| Nestfarn | Asplenium nidus | Aehnliche Schattentoleranz und Luftfeuchtigkeitsansprueche |
| Calathea | Calathea orbifolia | Gleicher Halbschatten-Standort, hohe Luftfeuchtigkeit |
| Marante | Maranta leuconeura | Gleiche Standortansprueche, schoener Kontrast |
| Fensterblatt | Monstera deliciosa | Gleiche Familie (Araceae), aehnliche Ansprueche |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Spathiphyllum wallisii |
|-----|-------------------|-------------|------------------------------------------|
| Spathiphyllum 'Sensation' | Spathiphyllum 'Sensation' | Gleiche Gattung, deutlich groesser | Imposantere Erscheinung, groessere Blaetter (bis 50 cm) |
| Anthurie (Flamingoblume) | Anthurium andraeanum | Gleiche Familie (Araceae), aehnliche Bluetenform | Farbigere Bluetenhuellblaetter (rot, rosa, orange) |
| Schwertfarn | Nephrolepis exaltata | Aehnliche Schattentoleranz | Ungiftig fuer Haustiere, buschiger Wuchs |
| Grünlilie | Chlorophytum comosum | Aehnliche Anspruchslosigkeit | Ungiftig fuer Haustiere, NASA-Luftreiniger, pflegeleichter |
| Calathea | Calathea lancifolia | Aehnlicher Standort | Ungiftig, dekorative Blattmuster |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,air_purification_score
Spathiphyllum wallisii,Einblatt;Friedenslilie;Peace Lily;White Sails,Araceae,Spathiphyllum,perennial,day_neutral,herb,fibrous,10b;11a;11b;12a;12b,0.0,Tropische Regenwaelder Kolumbiens und Venezuelas,sensitive,light_feeder,false,ornamental,0.9
```

### 8.2 BotanicalFamily CSV-Zeile (identisch mit Monstera -- Araceae)

```csv
name,common_name_de,common_name_en,order,typical_nutrient_demand,nitrogen_fixing,typical_root_depth,frost_tolerance,pollination_type
Araceae,Aronstabgewaechse,Arum family,Alismatales,medium,false,SHALLOW,SENSITIVE,INSECT
```

### 8.3 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type
Chopin,Spathiphyllum wallisii,--,--,compact,clone
Sweet Silvio,Spathiphyllum wallisii,--,--,compact;variegated,clone
Domino,Spathiphyllum wallisii,--,--,variegated,clone
Sensation,Spathiphyllum wallisii,--,--,large_leaved,clone
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Spathiphyllum: https://www.aspca.org/pet-care/animal-poison-control/toxic-and-non-toxic-plants/peace-lily
2. NASA Clean Air Study (Wolverton 1989): https://ntrs.nasa.gov/citations/19930072988
3. Cummings & Waring (2020) -- Potted plants do not improve indoor air quality (Journal of Exposure Science & Environmental Epidemiology)
4. Missouri Botanical Garden -- Spathiphyllum: https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b568
5. NCSU Plant Toolbox -- Spathiphyllum: https://plants.ces.ncsu.edu/plants/spathiphyllum/
6. Old Farmer's Almanac -- Peace Lily Care: https://www.almanac.com/plant/peace-lilies
7. Wikipedia -- NASA Clean Air Study: https://en.wikipedia.org/wiki/NASA_Clean_Air_Study
