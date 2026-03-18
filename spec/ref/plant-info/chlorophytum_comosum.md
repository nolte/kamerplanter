# Gruenlilie -- Chlorophytum comosum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** ASPCA, NASA Clean Air Study (Wolverton 1989), NC State Extension, Wisconsin Horticulture Extension, Missouri Botanical Garden, Royal Horticultural Society, Cummings & Waring 2020

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Chlorophytum comosum | `species.scientific_name` |
| Volksnamen (DE/EN) | Gruenlilie, Brautschleppe, Graslilie; Spider Plant, Airplane Plant, Ribbon Plant, Spider Ivy | `species.common_names` |
| Familie | Asparagaceae | `species.family` -> `botanical_families.name` |
| Gattung | Chlorophytum | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Wurzelanpassungen | tuberous | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20+ (Indoor: 10-20, optimal bis 50) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | sensitive | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 7 C, optimal 18-24 C. Bei unter 10 C Wachstumsstillstand. Kurzzeitig bis 2 C ueberlebensfaehig, aber mit Schaeden. | `species.hardiness_detail` |
| Heimat | Tropisches und suedliches Afrika (West-Tropisches Afrika bis Kamerun, Aethiopien bis Suedafrika) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfaellt (Zimmerpflanze, Vermehrung ueber Kindel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Entfaellt | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | Entfaellt | `species.direct_sow_months` |
| Erntemonate | Entfaellt (Zierpflanze, keine Ernte) | `species.harvest_months` |
| Bluetemonate | 5, 6, 7, 8 (Indoor bei ausreichend Licht und leichtem Stress, ab 1+ Jahr) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, division, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Die Gruenlilie ist eine der am einfachsten zu vermehrenden Zimmerpflanzen. Die primaere Methode ist das Abtrennen der Kindel (Spiderettes/Plantlets), die an langen Stolonen (Auslaeufer) wachsen. Kindel koennen direkt in feuchtes Substrat gesetzt oder zunaechst in Wasser bewurzelt werden (1-2 Wochen). Alternativ koennen Kindel noch an der Mutterpflanze haengend in einen Nebentopf geleitet werden (Absenker-Methode) -- die Erfolgsrate liegt bei 90-95%. Teilung aelterer Pflanzen ist ebenfalls problemlos moeglich (Erfolgsrate 80-90%). Aussaat ist moeglich, aber unueblich und deutlich langsamer.

**Wichtig:** Die Bildung von Stolonen und Kindeln ist lichtabhaengig -- sie werden ausgeloest, wenn die Pflanze mindestens 3 Wochen lang weniger als 12 Stunden Licht pro Tag erhaelt (Kurztagsreaktion).

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Chlorophytum comosum ist laut ASPCA als ungiftig fuer Katzen und Hunde eingestuft. Bei Verschlucken groesserer Mengen (insbesondere durch Katzen, die von den haengenden Blaettern angezogen werden) kann es zu leichter, voruebergehender Magen-Darm-Reizung kommen (Speichelfluss, Erbrechen), die aber nicht als Vergiftung einzustufen ist. Die Gruenlilie gilt als eine der sichersten Zimmerpflanzen fuer Haushalte mit Haustieren und Kindern.

### 1.5 Luftreinigung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Luftreinigungs-Score | 0.8 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, xylene, toluene, carbon_monoxide | `species.removes_compounds` |

**Hinweis:** Chlorophytum comosum war Teil der originalen NASA Clean Air Study (Wolverton 1989) und wurde als einer der effektivsten Luftreiniger unter den getesteten Zimmerpflanzen eingestuft. Die NASA listet die Gruenlilie unter den Top 3 bei der Formaldehyd-Entfernung. Die Pflanze absorbiert ausserdem Xylol, Toluol und Kohlenmonoxid. Caveat: Bei realistischen Pflanzendichten in Wohnraeumen ist der messbare Effekt auf die Luftqualitaet vernachlaessigbar (Cummings & Waring 2020).

### 1.6 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 3, 4, 5 | `species.pruning_months` |

**Hinweis:** Im Fruehjahr braune oder vertrocknete Blattspitzen mit einer scharfen Schere schraeg abschneiden (natuerliche Blattform erhalten). Ueberzaehlige oder erschoepfte Stolonen (Auslaeufer) entfernen, um die Mutterpflanze zu entlasten. Abgestorbene Blaetter an der Basis abreissen. Kein starker Rueckschnitt noetig -- die Pflanze reguliert sich weitgehend selbst.

### 1.7 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2--5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--60 (Blattlaenge, ohne haengende Auslaeufer) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--60 (ohne Auslaeufer; mit Auslaeufer bis 100 cm Durchmesser) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfaellt (reine Zimmerpflanze in Mitteleuropa) | `species.spacing_cm` |
| Indoor-Anbau | yes (extrem anpassungsfaehig, toleriert Halbschatten bis helles Licht) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Sommer, Halbschatten, kein direktes Sonnenlicht) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (nicht noetig, gedeiht problemlos als Zimmerpflanze) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Standard-Zimmerpflanzenerde, anspruchslos. Leicht durchlaessig. Ampeltopf ideal fuer haengende Auslaeufer mit Kindeln. | -- |

**Hinweis:** Die Gruenlilie ist eine der anspruchslosesten Zimmerpflanzen und ideal fuer Anfaenger. Sie bildet fleischige Speicherwurzeln (Rhizome), die Wasser einlagern -- daher kurze Trockenperioden kein Problem. Ampeltoepfe oder erhoehte Standorte nutzen, damit die dekorativen Auslaeufer frei haengen koennen. Vorsicht: Die kraeftigen Wurzeln koennen Plastiktoepfe sprengen -- rechtzeitig umtopfen.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

Chlorophytum comosum ist eine perenniale Zimmerpflanze ohne Ernte-Ziel. Die Phasen beschreiben den Lebenszyklus von der Vermehrung bis zur etablierten Pflanze mit jaehrlich wiederkehrendem saisonalem Rhythmus.

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung (Propagation) | 7-21 | 1 | false | false | low |
| Juvenil (Juvenile) | 30-90 | 2 | false | false | medium |
| Aktives Wachstum (Active Growth, Maerz-Oktober) | saisonal, ca. 210 | 3 | false | false | high |
| Ruheperiode (Maintenance, November-Februar) | saisonal, ca. 120 | 4 | false | false | high |

**Anmerkung:** Die Phasen "Aktives Wachstum" und "Ruheperiode" wiederholen sich jaehrlich (`is_recurring: true`). Es gibt keine terminale Phase -- Gruenlilien sind langlebig. Die Stresstoleranz ist generell hoch; die Gruenlilie verzeiht Pflegefehler besser als die meisten Zimmerpflanzen.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Bewurzelung (Propagation)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50-100 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 2-4 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 1.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 20-24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 18-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50-70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50-70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6-0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | Substrat gleichmaessig feucht halten, nicht nass | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30-80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Juvenil (Juvenile)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 75-200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3-6 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 2.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 18-24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40-60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40-60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5-7 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50-150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Aktives Wachstum (Maerz-Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 100-400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 5-10 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 3.0 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 12-14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 18-26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 16-20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40-60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40-60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5-7 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100-300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Ruheperiode (November-Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50-150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 2-5 | `requirement_profiles.dli_target_mol` |
| DLI Minimum (mol/m2/Tag) | 1.5 | `requirement_profiles.dli_min_mol` |
| Photoperiode (Stunden) | 10-12 (natuerlich kuerzer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (C) | 16-22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (C) | 12-16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40-50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 40-55 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8-1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 10-14 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 80-200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS/cm) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|-----------------|---------|-----|----------|----------|---------|----------|
| Bewurzelung | 0:0:0 | 0.0 | 6.0-6.5 | -- | -- | -- | -- |
| Juvenil | 1:1:1 | 0.3-0.6 | 6.0-6.5 | 30 | 15 | -- | 1 |
| Aktives Wachstum | 3:1:2 | 0.6-1.0 | 6.0-6.5 | 60 | 30 | -- | 1.5 |
| Ruheperiode | 0:0:0 | 0.0 | 6.0-6.5 | -- | -- | -- | -- |

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Bewurzelung -> Juvenil | conditional | 7-21 Tage | Wurzeln 3+ cm, neues Blattwachstum sichtbar |
| Juvenil -> Aktives Wachstum | time_based | 30-90 Tage | Pflanze etabliert, 5+ Blaetter, stabiles Wurzelsystem |
| Aktives Wachstum -> Kindel-Bildung | event_based | photoperiod_trigger | Photoperiode < 12h fuer 21+ Tage loest Stolonenbildung aus; typisch natuerlich ab September/Oktober |
| Aktives Wachstum -> Ruheperiode | event_based | saisonal (November) | Tageslaenge/Temperatur sinken |
| Ruheperiode -> Aktives Wachstum | event_based | saisonal (Maerz) | is_cycle_restart: true |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Zimmerpflanzen-Fluessigduenger)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Gruenpflanzen- und Palmenduenger | COMPO | Fluessigduenger | 7-3-6 | 3-5 ml / 1 L Wasser (halbe Dosis) | Aktives Wachstum (Maerz-Oktober) |
| Gruenpflanzen-Nahrung | Substral | Fluessigduenger | 7-3-5 | 3-5 ml / 1 L Wasser (halbe Dosis) | Aktives Wachstum (Maerz-Oktober) |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Bio Gruenpflanzen- und Palmenduenger | COMPO BIO | Bio-Fluessigduenger | 3-5 ml / 1 L (halbe Dosis) | Maerz-Oktober | Alle Gruenpflanzen |
| Wurmhumus | diverse | organisch, fest | 10-15% Beimischung beim Umtopfen | Fruehling | Alle Zimmerpflanzen |

### 3.2 Duengungsplan (Beispiel-NutrientPlan)

| Zeitraum | Phase | EC (mS/cm) | pH | COMPO 7-3-6 (ml/L) | Hinweise |
|----------|-------|---------|-----|---------------------|----------|
| Maerz-April | Wachstumsbeginn | 0.4-0.6 | 6.0-6.5 | 2-3 (Vierteldosis) | Langsam einsteigen nach Winterpause |
| Mai-August | Hauptwachstum | 0.6-1.0 | 6.0-6.5 | 3-5 (halbe Dosis) | Alle 2-4 Wochen |
| September-Oktober | Wachstumsende | 0.3-0.5 | 6.0-6.5 | 2-3 (Vierteldosis) | Abklingen lassen |
| November-Februar | Ruheperiode | 0.0 | 6.0-6.5 | 0 | Keine Duengung |

### 3.3 Mischungsreihenfolge

Bei Zimmerpflanzen-Fluessigduengern ist die Mischungsreihenfolge weniger kritisch als bei Hydroponiksystemen, da Komplett-Duenger vorgemischt sind:

1. Frisches, temperiertes Wasser (Zimmertemperatur) vorbereiten -- bevorzugt Regenwasser oder abgestandenes Leitungswasser (Fluorid-Empfindlichkeit!)
2. Fluessigduenger einmischen und umruehren
3. pH-Korrektur bei Zimmerpflanzen in Erde normalerweise nicht noetig

### 3.4 Besondere Hinweise zur Duengung

- **Schwachzehrer:** Gruenlilien haben einen geringen Naehrstoffbedarf. IMMER halbe oder Vierteldosis verwenden. Ueberdosierung fuehrt zu Salzakkumulation und braunen Blattspitzen.
- **Fluorid-Empfindlichkeit:** Chlorophytum comosum reagiert empfindlich auf Fluorid im Leitungswasser und in manchen Duengern. Braune Blattspitzen sind das haeufigste Symptom. Bevorzugt Regenwasser, destilliertes Wasser oder abgestandenes Leitungswasser verwenden.
- **Salzempfindlichkeit:** Alle 3-4 Monate das Substrat gruendlich mit klarem Wasser (idealerweise Regenwasser) durchspuelen, um Salzansammlungen auszuwaschen.
- **Kalziumbedarf:** Gering. Die fleischigen Speicherwurzeln (Rhizotuberkeln) speichern Wasser und Naehrstoffe, weshalb die Pflanze auch laengere Trockenperioden und Duengepausen toleriert.
- **Keine Blattstarre-Duenger:** Kein Blattglaenzer oder Blattreiniger verwenden -- die feinen Blaetter vertragen das schlecht.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kein Fluorid! Regenwasser oder abgestandenes Leitungswasser bevorzugt. Braune Blattspitzen deuten auf Fluorid-/Chlor-Empfindlichkeit hin. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3, 4, 5, 6, 7, 8, 9, 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |
| Luftfeuchtigkeitspruefungs-Intervall (Tage) | -- | `care_profiles.humidity_check_interval_days` |

**Giessanleitung (top_water):** Von oben langsam und gleichmaessig giessen, bis Wasser aus den Abzugsloechern laeuft. Ueberschuss nach 30 Minuten entfernen. Die oberen 2-3 cm zwischen den Giessintervallen abtrocknen lassen (Fingerprobe). Die fleischigen Speicherwurzeln (Rhizotuberkeln) der Gruenlilie speichern Wasser, wodurch sie kurzfristige Trockenperioden gut uebersteht. Staunaesse unbedingt vermeiden -- sie fuehrt zu Wurzelfaeule.

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan-Feb | Blattpflege, Schaedlingskontrolle | Braune Blattspitzen abschneiden, auf Schaedlinge pruefen (trockene Heizungsluft beguenstigt Spinnmilben) | mittel |
| Maerz | Wachstumsstart | Duengung starten (Vierteldosis), ggf. Umtopfen wenn Wurzeln aus Abzugsloechern wachsen | hoch |
| April-Mai | Umtopfen und Teilen | Bei Bedarf umtopfen (alle 2 Jahre), grosse Pflanzen teilen, Kindel abnehmen | mittel |
| Mai-Aug | Hauptwachstum | Duengung alle 3-4 Wochen (halbe Dosis), regelmaessig giessen, Kindel bewurzeln | mittel |
| Sep-Okt | Wachstumsende | Duengung reduzieren, Giessintervalle verlaengern, letzte Kindel abnehmen | niedrig |
| Nov-Dez | Ruheperiode | Keine Duengung, reduziert giessen. Standort-Lichtcheck. Nicht unter 10 C. Vor Zugluft und Heizoerpernaehe schuetzen. | niedrig |

### 4.3 Ueberwinterung

Entfaellt -- reine Zimmerpflanze, ganzjaehrig Indoor bei Raumtemperatur. Im Winter lediglich Giessen reduzieren und Duengung einstellen. Pflanzen, die im Sommer auf Balkon oder Terrasse standen, vor dem ersten Frost (spaetestens bei 10 C Nachttemperatur) nach drinnen holen.

### 4.4 Standort-Empfehlungen

- **Optimal:** Helles Ost- oder Westfenster mit hellem, indirektem Licht
- **Akzeptabel:** Nordfenster (Wachstum langsamer, Panaschierung kann verblassen), leicht zurueckgesetzt an Suedfenster
- **Vermeiden:** Direkte Mittagssonne im Sommer (Blattverbrennungen), direkte Naeche zu Heizkoerpern, Zugluft
- **Ampelpflanze:** Ideal als Haengepflanze in Blumenampeln -- die ueberbogenden Blaetter und haengenden Kindel kommen besonders gut zur Geltung
- **Luftfeuchtigkeit:** 40-60% genuegt. Gruenlilien sind bezueglich Luftfeuchtigkeit anspruchslos und kommen mit normaler Raumluft gut zurecht
- **Temperatur:** 18-24 C optimal. Toleriert 10-30 C, Wachstumsstillstand unter 10 C

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste an Blattunterseiten, gelbe Stippen, fahle Blaetter | leaf | Alle (verstaerkt im Winter bei trockener Heizungsluft) | medium |
| Wolllaeusse (Mealybug) | Pseudococcidae | Weisse wachsartige Klumpen an Blattachseln und Blattbasen, Honigtau | leaf, stem | Alle | easy |
| Blattlaeusse (Aphid) | Aphidoidea | Verkrueppelte junge Blaetter, Honigtau, klebrige Blaetter | leaf | Aktives Wachstum (Fruehjahr) | easy |
| Schildlaeusse (Scale) | Coccoidea | Braune Hoecker an Blattstielen und -basen, Honigtau | stem, leaf | Alle | medium |
| Trauermuecken (Fungus Gnat) | Bradysia spp. | Kleine schwarze Fliegen ueber dem Substrat, Larven an Wurzeln | root | Bewurzelung, Juvenil | easy |
| Weisse Fliege (Whitefly) | Trialeurodes vaporariorum | Winzige weisse Fliegen an Blattunterseiten, Honigtau, Russtaupilze | leaf | Aktives Wachstum | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfaeule (Root Rot) | fungal | Welke trotz feuchtem Substrat, gelbe Blaetter, braune matschige Wurzeln, Faeulnisgeruch | overwatering, poor_drainage | 7-21 | Alle |
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
| Encarsia formosa | Weisse Fliege | 3-5 | 21-28 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoel | biological | Azadirachtin | Spruehen, 0.3-0.5% Loesung, alle 7 Tage | 0 (Zierpflanze) | Blattlaeusse, Wolllaeusse, Spinnmilben, Weisse Fliege |
| Schmierseife | biological | Kaliumsalze von Fettsaeuren | Spruehen, 1-2% Loesung | 0 | Blattlaeusse, Wolllaeusse, Spinnmilben |
| Alkohol-Abwischen | mechanical | Isopropanol 70% | Wattestab auf befallene Stellen | 0 | Wolllaeusse, Schildlaeusse |
| Gelbtafeln | mechanical | -- | Aufstellen neben Pflanze | 0 | Trauermuecken (Adulte), Weisse Fliege (Monitoring) |
| Blaetter abbrausen | cultural | -- | Lauwarme Dusche alle 2-4 Wochen | 0 | Spinnmilben, Staub, Blattlaeusse |
| Quarzsand-Abdeckung | cultural | -- | 1 cm Quarzsand auf Substrat | 0 | Trauermuecken (verhindert Eiablage) |

### 5.5 Resistenzen der Art

Chlorophytum comosum hat keine spezifischen Resistenzen gegen Krankheiten oder Schaedlinge. Allerdings ist die Pflanze generell robust und widerstandsfaehig. Gesunde, gut gepflegte Exemplare mit korrekter Bewaesserung (keine Staunaesse) und ausreichend Licht sind die beste Praevention. Die Gruenlilie erholt sich nach Schaedlingsbefall in der Regel schnell und zuverlaessig.

---

## 6. Fruchtfolge & Mischkultur

Entfaellt (reine Zimmerpflanze). Fruchtfolge und Mischkultur sind Konzepte des Freilandanbaus und haben fuer die Gruenlilie als Zimmerpflanze keine Relevanz.

### 6.1 Standort-Nachbarn (Indoor-Empfehlungen)

| Partner | Wissenschaftl. Name | Begruendung |
|---------|-------------------|-------------|
| Bogenhanf | Dracaena trifasciata | Aehnlich pflegeleicht, kontrastreiche Wuchsform (aufrecht vs. ueberbogend), gleiche Lichtansprueche (Synonym: Sansevieria trifasciata) |
| Efeutute | Epipremnum aureum | Aehnliche Licht- und Temperaturansprueche, dekorative Kombination als Ampelpflanzen |
| Drachenbaum | Dracaena marginata | Gleiche Familie (Asparagaceae), aehnliche Ansprueche, Formkontrast |
| Einblatt | Spathiphyllum wallisii | Aehnlicher Lichtbedarf, beide gute Luftreiniger (NASA-Studie) |
| Gummibaum | Ficus elastica | Unterschiedliche Wuchshoehe, aehnliche Pflegeansprueche, gute Raumkomposition |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Chlorophytum comosum |
|-----|-------------------|-------------|--------------------------------------|
| Zebrablatt-Gruenlilie | Chlorophytum laxum | Gleiche Gattung, kompakter | Kleiner, ideal fuer enge Raeume |
| Kapgruenlilie | Chlorophytum capense | Gleiche Gattung, groesser, ohne Kindel | Robuster, weniger Auslaeufer-Chaos |
| Bogenhanf | Dracaena trifasciata | Gleiche Familie (Asparagaceae), pflegeleicht (Synonym: Sansevieria trifasciata) | Noch anspruchsloser, toleriert Dunkelheit besser |
| Drachenbaum | Dracaena fragrans | Gleiche Familie (Asparagaceae), Gruenpflanze | Wird deutlich groesser, dekorativer Solitaer |
| Efeutute | Epipremnum aureum | Haengepflanze, pflegeleicht, luftreinigend | Kletternd und haengend einsetzbar, schnellwuechsig |
| Gruenblatt-Segge | Carex morrowii | Grasartige Optik, aehnliche Blattform | Winterhart (Outdoor moeglich), immergruen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,air_purification_score
Chlorophytum comosum,Gruenlilie;Spider Plant;Airplane Plant;Ribbon Plant,Asparagaceae,Chlorophytum,perennial,day_neutral,herb,tuberous,9b;10a;10b;11a;11b,0.0,Tropisches und suedliches Afrika,sensitive,light_feeder,false,ornamental,0.8
```

### 8.2 BotanicalFamily CSV-Zeile (falls noch nicht vorhanden)

```csv
name,common_name_de,common_name_en,order,typical_nutrient_demand,nitrogen_fixing,typical_root_depth,frost_tolerance,pollination_type
Asparagaceae,Spargelgewaechse,Asparagus family,Asparagales,low,false,MEDIUM,SENSITIVE,INSECT
```

### 8.3 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type
Vittatum,Chlorophytum comosum,--,--,variegated;central_white_stripe,clone
Variegatum,Chlorophytum comosum,--,--,variegated;white_margins;compact,clone
Bonnie,Chlorophytum comosum,--,--,variegated;curly_leaves;compact,clone
Ocean,Chlorophytum comosum,--,--,variegated;compact;short_leaves,clone
Green Orange,Chlorophytum comosum,--,--,green;orange_stems,clone
Hawaiian,Chlorophytum comosum,--,--,variegated;champagne_tint,clone
```

---

## Quellenverzeichnis

1. ASPCA Animal Poison Control -- Spider Plant (Chlorophytum comosum): https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/spider-plant
2. NC State Extension Gardener Plant Toolbox -- Chlorophytum comosum: https://plants.ces.ncsu.edu/plants/chlorophytum-comosum/
3. Wisconsin Horticulture Extension -- Spider plant: https://hort.extension.wisc.edu/articles/spider-plant-chlorophytum-comosum/
4. Missouri Botanical Garden Plant Finder -- Chlorophytum comosum: https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b547
5. NASA Clean Air Study (Wolverton 1989): https://ntrs.nasa.gov/citations/19930072988
6. Cummings & Waring (2020) -- Potted plants do not improve indoor air quality (Journal of Exposure Science & Environmental Epidemiology)
7. Wikipedia -- Chlorophytum comosum: https://en.wikipedia.org/wiki/Chlorophytum_comosum
8. Royal Horticultural Society -- Award of Garden Merit: https://www.rhs.org.uk/
9. COMPO Gruenpflanzen- und Palmenduenger: https://www.compo.de/
10. USDA Plants Database -- Chlorophytum comosum: https://plants.usda.gov/plant-profile/CHCO28
