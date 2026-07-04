# Moehre -- Daucus carota subsp. sativus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, Johnny's Seeds, NCSU Extension, UF/IFAS Extension, Plantura, fryd.app, Hortipendium, Mein schoener Garten, Gartenjournal, Old Farmer's Almanac, DeepGreen Permaculture, MDPI Plants, FAO (Salztoleranz), Wikipedia (Salt tolerance of crops), GrowVeg

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Daucus carota subsp. sativus | `species.scientific_name` |
| Volksnamen (DE/EN) | Moehre; Karotte; Mohrrube; Gelbe Ruebe; Carrot | `species.common_names` |
| Familie | Apiaceae | `species.family` -> `botanical_families.name` |
| Gattung | Daucus | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | biennial (Speicherwurzel im 1. Jahr, Bluete/Samenbildung im 2. Jahr; wird als einjaehrig kultiviert) | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | monocarpic (blüht einmal, dann Absterben) | `lifecycle_configs.flowering_strategy` |
| Anbau-Zyklustyp (cultivation cycle type) | biennial | `lifecycle_configs.cultivation_cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral (tagneutral -- die Bluete wird durch Vernalisation/Kaeltereiz induziert, NICHT durch die Tageslaenge; peer-reviewed bestaetigt: post-vernalisation day length nicht entscheidend. In der Literatur wurde die Moehre kontrovers als Langtag- ODER Tagneutralpflanze beschrieben; massgeblich ist der Vernalisationsbedarf) | `lifecycle_configs.photoperiod_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 (Apiaceae, kuehlliebendes C3-Gemuese) | `species.photosynthesis_type` |
| GDD-Basistemperatur (degC) | 4.5 (Wuchs-GDD-Basis der Hauptwuchsphase; belegter Bereich 4--6 degC fuer Moehre -- kuehlliebende Kultur. NICHT die Keim-Basistemperatur) | `species.base_temp` |
| Dormanz erforderlich | false (kein Dormanzbruch noetig) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Kaeltereiz < 10 degC loest die Bluete im 2. Jahr aus) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 42 (ca. 6--8 Wochen bei 2--5 degC / < 10 degC; genotypabhaengig) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (h) | -- (tagneutral -- keine kritische Tageslaenge; Bluete vernalisationsgesteuert) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Saemlinge vertragen leichte Froeste bis -3 degC. Reife Moehren koennen bei Abdeckung (Mulch/Vlies) bis -8 degC im Boden verbleiben. Starker Dauerfrost zerstoert die Wurzeln. | `species.hardiness_detail` |
| Heimat | Europa, Westasien (Wildform: Daucus carota subsp. carota) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | -- (Direktsaat bevorzugt; Moehren vertragen kein Pikieren/Umtopfen wegen Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (kann bereits 2--3 Wochen VOR letztem Frost gesaet werden, ab Bodentemperatur 5 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5; 6; 7 (Staffelsaat fuer kontinuierliche Ernte) | `species.direct_sow_months` |
| Erntemonate | 6; 7; 8; 9; 10; 11 | `species.harvest_months` |
| Bluetemonate | 5; 6; 7 (nur im 2. Kulturjahr -- im Gemuese-Anbau unerwuenscht) <!-- Quelle: growing-phase-auditor 2026-07 -- Korrektur von '6;7' auf '5;6;7'; deutschsprachige Kulturmoehre-Quellen datieren Bluetebeginn auf Mai, nicht erst Juni; siehe Quellen 21-23 --> | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy (Direktsaat, unkompliziert; gleichmaessige Keimung erfordert Geduld) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 10--20 degC (kuehler als die meisten Gemuese!)
- Minimale Keimtemperatur: 5 degC (sehr langsame Keimung)
- Maximale Keimtemperatur: 30 degC (Keimhemmung bei hohen Temperaturen!)
- Keimdauer: 10--21 Tage (Geduld noetig -- Moehren keimen langsam)
- **Dunkelkeimer** -- Samen mit 1--2 cm Erde abdecken (Licht hemmt die Keimung)
- Saatrillen 1--2 cm tief, nach Auflaufen auf 3--5 cm Abstand vereinzeln
- Reihenabstand: 25--30 cm
- Boden MUSS fein krumelig, steinfrei und locker sein (Steine/verdichteter Boden = krumme/gespaltene Moehren)
- Saatband erleichtert gleichmaessige Aussaat

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false (ASPCA: Daucus carota als ungiftig gelistet; Wildform mit Vorsicht) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (Kraut enthaelt Furanocumarine -- phototoxisch bei Hautkontakt + Sonnenlicht) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Falcarinol (Polyacetylen, Hautallergen); Furanocumarine (im Kraut, phototoxisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | none (Speicherwurzel essbar und unbedenklich) | `species.toxicity.severity` |
| Kontaktallergen | true (Falcarinol im Kraut kann Kontaktdermatitis ausloesen; Phototoxizitaet bei empfindlichen Personen + Sonnenlicht) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzallergie mit Birkenpollen -- Orales Allergiesyndrom bei rohen Moehren relativ haeufig, ca. 10% der Pollenallergiker) | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Daucus carota (Carrot Flower) als ungiftig fuer Katzen und Hunde. Achtung: Verwechslung mit giftiger Wilder Moehre (Daucus carota subsp. carota) oder Schierling moeglich. Moehren-Allergie (Kreuzreaktion Birke/Beifuss) ist die dritthaeufigste Nahrungsmittelallergie.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

Hinweis: Kein Rueckschnitt noetig. Kraut nicht abschneiden, da die Pflanze es fuer die Photosynthese und das Wurzelwachstum benoetigt. Wenn Moehren im 2. Jahr Bluetenstaengel bilden ("Schossen"), sofort entfernen -- die Wurzel wird holzig und ungeniessbar.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in tiefen Toepfen/Kuebeln ab 30 cm Tiefe; kurzwurzelige Sorten wie 'Pariser Markt' bevorzugen) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15--30 (Tiefe wichtiger als Breite) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 (fuer Nantes-Typen; 20 fuer Kurzmoehren) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--50 (Kraut) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15--25 (Kraut) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 3--5 in der Reihe, 25--30 Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no (benoetigt tiefe, lockere Boeden; Lichtverlhaeltnisse indoor unzureichend) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (tiefe Kuebel, kurzwurzelige Sorten) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freilandkultur optimal, Gewaechshaus zu warm) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Tiefgruendige, lockere, steinfreie, sandige Erde. Keine frische organische Duengung (foerdert Beinigkeit). Kompost nur gut abgelagert. pH 6.0--7.0. | -- |

**Hinweis:** Moehren bevorzugen lockere, sandige Lehmboeden. Schwere Tonboeden und Steine verursachen verkrueppelte, gespaltene Wurzeln. Frische Stallmistduengung vermeiden -- foerdert Beinigkeit (verzweigte Wurzeln) und lockt Moehrenfliegen an.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualitaet

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | -- <!-- DATEN FEHLEN: keine zwei unabhaengigen carrot-spezifischen Messwerte fuer den Lichtkompensationspunkt auffindbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | -- <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun (volle Sonne, mind. 6 h direktes Sonnenlicht fuer kraeftige Wurzeln; vertraegt etwas Schatten, aber nicht optimal) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30--60 (medium-rooted; aktive Bewaesserungs-/Wurzelzone. Boden mind. 30 cm tief lockern, fuer lange Sorten bis ~46 cm) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz | sensitive (gute Drainage essenziell; staunasse Boeden verursachen Wurzelfaeule) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 1.0 (Maas-Hoffman a; Bezugsgroesse Substrat-ECe im Wurzelraum, NICHT Giesswasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 14 (Maas-Hoffman b; 14% Ertragsrueckgang je dS/m oberhalb der Schwelle) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min--max) | 6.0--6.8 (leicht sauer bis neutral; harmoniert mit pH 6.0--7.0 in 1.6/2.3) | `species.soil_ph_preference` |

Hinweis: Die Moehre ist salzempfindlich (sensitive) -- bereits ab einer Substrat-Leitfaehigkeit (ECe) von 1.0 dS/m sinkt der Ertrag um ca. 14% je weiterer dS/m (Maas & Hoffman). Die hier genannte effektive Wurzeltiefe ist die agronomisch aktive Zone der Wasseraufnahme; einzelne Wurzeln koennen unter guenstigen Bedingungen deutlich tiefer reichen (in Studien > 1 m).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

<!-- Quelle: growing-phase-auditor 2026-07 -- Klarstellung ergaenzt (analog apium_graveolens.md, petroselinum_crispum.md): Phasentabelle bildet nur das 1. Kulturjahr ab, in dem die Speicherwurzel vor jeder Bluete geerntet wird. Die Bluete (Bluetemonate 5;6;7 in §1.2) tritt erst im 2. Standjahr auf, wenn die Wurzel ueberwintert bzw. zur Saatgutgewinnung ausgepflanzt wird, und ist bewusst NICHT Teil dieser Phasenkette (Ernte bleibt terminal). -->
(Angaben fuer Kulturmoehre; im 1. Kulturjahr -- Speicherwurzel-Ernte vor jeder Bluete. Die Bluete im 2. Standjahr, siehe Bluetemonate in 1.2, ist nur bei Ueberwinterung/Samenbau relevant und nicht Teil dieser Phasenkette.)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 10--21 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 50--80 | 3 | false | true (Bundmoehren ab ca. Tag 60) | medium |
| Ernte (harvest) | 14--42 | 4 | true | true | high |

Hinweis: Moehren werden im 1. Kulturjahr vor der Bluete geerntet (Speicherwurzel). Die vegetative Phase ist die laengste und wichtigste -- hier bildet sich die Speicherwurzel. Fruehe Sorten (Nantes) sind nach 70--90 Tagen erntereif, spaete Lagersorten (Flakkee) nach 120--150 Tagen.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (Freiland-Direktsaat) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 10--20 (optimal 15) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 5--12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | -- <!-- DATEN FEHLEN: keine carrot-spezifische VPD-Kollaps-Schwelle aus zwei serioesen Quellen; zudem Freiland-Direktsaat ohne VPD-Steuerung --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Gemuese; feuchteliebende Keimphase) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 13--18 (kuehlliebende Keim-/Fruehphase) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | -- <!-- DATEN FEHLEN: kein belegter carrot-spezifischer Wert --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (Boden feucht halten bis Keimung!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 (feiner Spruehstrahl, Samen nicht ausschwemmen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Moehren keimen langsam (10--21 Tage). Boden MUSS in dieser Zeit gleichmaessig feucht bleiben -- Austrocknung fuehrt zu lueckigem Aufgang. Abdeckung mit Vlies oder Holzbrettern (vor Keimung entfernen) hilft.

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (Freiland) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich (mind. 12--15 mol/m2/d) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (12--16 h im Fruehjahr) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 8--14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | -- <!-- DATEN FEHLEN: keine carrot-spezifische VPD-Kollaps-Schwelle aus zwei serioesen Quellen; Freiland --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Gemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 15--20 (kuehlliebende Kultur) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | -- <!-- DATEN FEHLEN: kein belegter carrot-spezifischer Wert --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Vereinzeln auf 3--5 cm Abstand, sobald die Pflanzen 3--5 cm hoch sind. Nicht zu frueh und nicht zu spaet -- dichter Stand fuehrt zu kleinen, krummen Moehren.

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich (Freiland, volle Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich (mind. 15--20 mol/m2/d) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (14--16 h im Sommer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--24 (optimal 18--22) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 (kuehle Naechte foerdern Karotin-Einlagerung und Geschmack) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | -- <!-- DATEN FEHLEN: keine carrot-spezifische VPD-Kollaps-Schwelle aus zwei serioesen Quellen; Freiland --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Gemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--22 (agronomischer Optimumbereich der Wurzelbildung; Wuchsoptimum 15.5--21 degC) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | -- <!-- DATEN FEHLEN: kein belegter carrot-spezifischer Wert --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (gleichmaessig, nicht schwankend) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Gleichmaessige Wasserversorgung ist entscheidend. Schwankungen (trocken-nass-trocken) verursachen Aufplatzen der Wurzeln. In Trockenperioden regelmaessig giessen. Anhaeufeln (Erde an die Wurzelschulter ziehen) verhindert Vergruenen der Schulter.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | natuerlich | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 10--20 (kuehle Temperaturen fuer Lagermoehren ideal) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 5--12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- (natuerlich) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- (Freiland) | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | -- <!-- DATEN FEHLEN: keine carrot-spezifische VPD-Kollaps-Schwelle aus zwei serioesen Quellen; Freiland --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Gemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 13--18 (kuehle Endphase foerdert Zuckereinlagerung und Lagerfaehigkeit) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | -- <!-- DATEN FEHLEN: kein belegter carrot-spezifischer Wert --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (vor Ernte 2--3 Tage nicht giessen fuer bessere Lagerfaehigkeit) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 (reduziert) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Erntezeitpunkt nach Sortenbeschreibung. Bundmoehren koennen ab ca. 60 Tagen geerntet werden (Fingerstärke). Lagermoehren erst bei voller Ausfaerbung (90--150 Tage). Moehren bei trockenem Wetter ernten, Kraut abdrehen (nicht schneiden), kuhl und feucht lagern (0--2 degC, 95% Luftfeuchtigkeit -- in Sand einschlagen).

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--7.0 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.3--0.6 | 6.0--6.8 | 60 | 25 | 20 | 2 |
| Vegetativ | 1-1-2 | 0.8--1.4 | 6.0--6.8 | 100 | 40 | 30 | 3 |
| Ernte | 0-1-2 | 0.6--1.0 | 6.0--6.8 | 80 | 35 | 25 | 2 |

Hinweis: Moehren sind Mittelzehrer. Stickstoff-Ueberangebot foerdert ueppiges Kraut auf Kosten der Wurzelbildung und verschlechtert Lagerf aehigkeit. Kalium ist der wichtigste Naehrstoff fuer die Wurzelentwicklung (Geschmack, Farbe, Lagerfaehigkeit). Frischen Stallmist vermeiden -- foerdert Beinigkeit und Moehrenfliege.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronaehrstoffe (Mn/Zn/Cu/Mo):**

| Mikronaehrstoff | Wert (ppm) | KA-Feld |
|----------------|-----------|---------|
| Mangan (Mn) | -- <!-- DATEN FEHLEN: keine zwei unabhaengigen carrot-spezifischen Gewebe-Sufficiency-Werte auffindbar --> | `nutrient_profiles.manganese_ppm` |
| Zink (Zn) | -- <!-- DATEN FEHLEN --> | `nutrient_profiles.zinc_ppm` |
| Kupfer (Cu) | -- <!-- DATEN FEHLEN --> | `nutrient_profiles.copper_ppm` |
| Molybdaen (Mo) | -- <!-- DATEN FEHLEN --> | `nutrient_profiles.molybdenum_ppm` |

Hinweis: Carrot-spezifische Sufficiency-Bereiche fuer Mn/Zn/Cu/Mo liessen sich nicht aus zwei unabhaengigen serioesen Quellen (Extension-Gewebeanalyse) belegen und bleiben daher offen. Fachlich praxisrelevanter ist bei Moehren der Bor-Bedarf (Bor-Mangel -> Risse/Hohlraeume in der Wurzel, siehe 3.4) sowie ein Mn/Cu-Mangelrisiko bei pH > 7.5.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 10--21 Tage | Keimblaetter sichtbar (fadenfoermige, untypische Kotyledonen) |
| Saemling -> Vegetativ | time_based | 14--21 Tage | 3--4 echte, gefiederte Blaetter, Pflanze ca. 5 cm hoch |
| Vegetativ -> Ernte | time_based / manual | 50--80 Tage (sortenabhaengig) | Wurzeldurchmesser 2--4 cm (Nantes-Typ) bzw. nach Sortenbeschreibung |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (fuer Freiland-Beete)

| Produkt | Marke | Typ | NPK | Ausbringrate | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-------------|-----------------|--------|
| Patentkali | K+S | base | 0-0-30 (+Mg 10%, S 17%) | 50--80 g/m2 | 1 | Vegetativ (Einarbeitung vor Saat) |
| Thomaskali | div. | base | 0-8-15 (+Ca, Mg) | 60--100 g/m2 | 1 | Vegetativ (Herbst-Vorduengung) |
| Hakaphos Gruen 20-5-10 | COMPO Expert | base | 20-5-10 | 20--30 g/10 L | 3 | Saemling (nur bei Bedarf) |

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Gut abgelagerter Kompost | Eigenerzeugung | organisch | 3--4 L/m2 | Herbst (Einarbeitung vor Saat) | medium_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 40--60 g/m2 | Fruehjahr (Einarbeitung vor Saat) | medium_feeder |
| Kalimagnesia (Patentkali) | K+S | mineralisch-natuerlich | 50--80 g/m2 | Herbst oder Fruehjahr | medium_feeder |
| Holzasche (unbehandelt) | Eigenerzeugung | mineralisch-natuerlich (K-betont) | 30--50 g/m2 | Herbst | medium_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:20 verduennt, 0.5 L/m2 | Juni--Juli, max. 2x | medium_feeder |
| Schachtelhalmbruehe | Eigenerzeugung | Pflanzenhilfsmittel | 1:5 verduennt, Blattspruehung | Mai--August, alle 14 Tage | alle (Pilzpraevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Moehre Standard Freiland")

| Zeitpunkt | Phase | Massnahme | Hinweise |
|-----------|-------|-----------|----------|
| Herbst vor Saat | Vorbereitung | 3--4 L/m2 Kompost + 50 g/m2 Patentkali einarbeiten | KEIN frischer Stallmist! |
| Saat (Marz--April) | Keimung | 40--60 g/m2 Hornmehl einarbeiten | Stickstoff-Langzeitversorgung |
| 4--6 Wochen nach Saat | Saemling/Veg | ggf. 1x Brennnesseljauche 1:20 | Nur bei sichtbarem N-Mangel (blasse Blaetter) |
| Ab Juni | Vegetativ | Schachtelhalmbruehe alle 14 Tage | Praevention Alternaria, Mehltau |
| 4 Wochen vor Ernte | Ernte | Keine Duengung mehr | Lagerfaehigkeit verbessern |

### 3.3 Mischungsreihenfolge

Bei Moehren im Freiland entfaellt die typische Naehrloesungs-Mischung. Bei der seltenen Hydrokultur-Variante:

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag (falls noetig)
3. Basis-Naehrloesungs A (Ca, Mikro)
4. Basis-Naehrloesungs B (P, S, Mg)
5. pH-Korrektur -- IMMER als letzter Schritt

### 3.4 Besondere Hinweise zur Duengung

- **Mittelzehrer** mit Kalium-Schwerpunkt -- K foerdert Wurzelentwicklung, Geschmack und Farbe.
- **KEIN frischer Stallmist!** Organische Frischsubstanz verursacht Beinigkeit (verzweigte, missgeformte Wurzeln) und lockt die Moehrenfliege an.
- **Stickstoff massvoll:** Zu viel N foerdert ueppiges Kraut auf Kosten der Wurzel und verschlechtert Lagerfaehigkeit.
- **Bor-Empfindlichkeit:** Bor-Mangel verursacht Risse/Hohlraeume in der Wurzel. Bei bekanntem Mangel: 1 g Borax / 10 L Wasser als Blattspruehung.
- **pH 6.0--7.0:** Moehren bevorzugen leicht saure bis neutrale Boeden. Zu saure Boeden (pH < 5.5) kalken.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 3--5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrige Kultur, Ernte vor Winter) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Gleichmaessige Bodenfeuchtigkeit ist der wichtigste Pflegefaktor! Wechsel zwischen trocken und nass verursacht Aufplatzen der Wurzeln. Nicht ueber das Kraut giessen (Alternaria-Gefahr). Mulchen reduziert Verdunstung. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | -- (Grundduengung vor Saat genuegt; ggf. 1x Nachduengung) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 3; 4; 5; 6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (Direktsaat, kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Beetvorbereitung | Boden tiefgruendig lockern (30 cm), Steine entfernen, Kompost einarbeiten | hoch |
| Marz | Erste Aussaat | Fruehmoehren saeen (z.B. 'Nantes 2'), Reihenabstand 25 cm, Vliesabdeckung | hoch |
| Apr | Zweite Aussaat | Staffelsaat fuer kontinuierliche Ernte, Vereinzeln der Maerz-Saat (3--5 cm Abstand) | hoch |
| Mai | Dritte Aussaat + Pflege | Spaetmoehren saeen, Unkraut jaeten (vorsichtig! Moehrenwurzeln nicht verletzen), Mulchen | hoch |
| Jun | Pflege + Erntebeginn | Bundmoehren ernten, Moehrenfliege kontrollieren (gelbe Blaetter, Bohrmehl), Anhaeufeln | hoch |
| Jul | Haupternte Fruehmoehren | Ernte der Fruehsorten, Staffelsaat der letzten Runde | hoch |
| Aug | Pflege + Ernte | Gleichmaessig giessen, Alternaria-Blattflecken kontrollieren | mittel |
| Sep | Ernte Lagermoehren | Spaete Sorten ernten, Kraut abdrehen, kuhl lagern | hoch |
| Okt | Letzte Ernte | Vor erstem starken Frost ernten oder mit Mulch/Vlies schuetzen | hoch |
| Nov | Winterlagerung | Lagern bei 0--2 degC, 95% Luftfeuchtigkeit (Erdmiete, Sand, Kuehlraum) | mittel |

### 4.3 Ueberwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-07 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Bewertung | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | mulch (15--20 cm Stroh/Laub; Ruebe im Boden belassen) | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 11 (November, vor Dauerfrost) | `overwintering_profiles.winter_action_month` |
| Fruehjahrs-Massnahme | uncover (Mulch bei Austrieb / Nachernte abraeumen) | `overwintering_profiles.spring_action` |
| Fruehjahrs-Massnahme Monat | 3 (Maerz) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (degC) | — (Freilandueberwinterung; kein Quartier noetig) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Licht | — (Freiland) | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | none (Niederschlag genuegt) | `overwintering_profiles.winter_watering` |

**Hinweise zu §4.3:**
- Moehren sind zweijaehrig und halbfrosthart (`half_hardy`). Bei milder Witterung und Mulch-Abdeckung (15--20 cm Stroh/Laub) koennen sie bis Dezember/Januar im Boden verbleiben und laufend geerntet werden (`needs_protection` + `mulch`, Freilandueberwinterung).
- Bei starkem Dauerfrost (unter -8 degC) erfrieren die Rueben.
- Alternative sichere Lagerung: vor dem ersten starken Frost ernten und in feuchtem Sand bei 0--2 degC einschlagen (Erdmiete/Keller) — dann `dig_and_store` statt `mulch`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 -->

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Moehrenfliege (Carrot Fly) | Psila rosae | Rostbraune Fraessgaenge in der Wurzel, welkes/gelbes Kraut, Bohrmehl | root, leaf | vegetative, harvest | medium (Schaeden erst bei Ernte sichtbar) |
| Moehrenlaus (Carrot-Willow Aphid) | Cavariella aegopodii | Verkrueppelte, gelbe Blaetter, Wuchshemmung, Virusuebertraeger | leaf | vegetative | easy |
| Wuehlmaus (Vole) | Arvicola terrestris | Abgefressene Wurzeln, Erdgaenge | root | vegetative, harvest | medium |
| Drahtwurm (Wireworm) | Agriotes spp. | Bohrloecher in der Wurzel | root | vegetative | medium (erst bei Ernte sichtbar) |
| Schnecken (Slugs/Snails) | Arion spp. | Frass an jungen Blaettern und Wurzelschulter | leaf, root | seedling | easy |
| Nematoden (Root-Knot Nematode) | Meloidogyne spp. | Verdickungen/Gallen an Wurzeln, verkuemmertes Wachstum | root | vegetative | difficult |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Alternaria-Blattflecken (Alternaria Leaf Blight) | fungal | Braun-schwarze Laesionen an Blattrandern, Blaetter kraeuseln und sterben | warm_humid, rain_splash | 5--10 | vegetative |
| Cercospora-Blattflecken | fungal | Runde braune Flecken mit hellem Zentrum | high_humidity | 5--10 | vegetative |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser mehliger Belag auf Blaettern | dry_warm, poor_airflow | 7--14 | vegetative |
| Wurzelfaeule (Root Rot) | fungal | Weiche, braune Stellen an der Wurzel, Faeulnis | overwatering, heavy_soil | 7--14 | vegetative, harvest |
| Moehren-Schwarzfaeule (Black Rot) | fungal | Schwarze Flecken an der Wurzel, Lagerverluste | infected_soil, poor_storage | 14--28 | harvest (Lagerung) |
| Violette Wurzelfaeule (Violet Root Rot) | fungal | Violetter Pilzbelag auf der Wurzel, Faeulnisgeruch | acid_soil, waterlogging | 14--21 | vegetative, harvest |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Moehrenlaus | 5--10 | 14 |
| Coccinella septempunctata (Marienkaefer) | Moehrenlaus | 5--10 | 7--14 |
| Steinernema feltiae (Nematode) | Moehrenfliege (Larven), Drahtwurm | 500.000/m2 | 7--14 |
| Kulturschutznetz (insect net) | Moehrenfliege | 1 Netz/Beet (Maschenweite 0.8 mm) | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz | cultural | -- | Netz ueber Beet spannen ab Saat bis Ernte | 0 | Moehrenfliege (beste Methode!) |
| Mischkultur mit Zwiebeln | cultural | -- | Abwechselnde Reihen Moehren/Zwiebeln | 0 | Moehrenfliege (Duft-Verwirrung) |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Blattspruehung 1:5, alle 14 Tage | 0 | Alternaria, Mehltau |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Mehltau |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen, 5 g/m2 | 0 | Schnecken |
| Fruchtfolge + Hygiene | cultural | -- | 3--5 Jahre Anbaupause fuer Apiaceae, Erntereste entfernen | 0 | Alle bodenbürtigen Krankheiten |

### 5.5 Resistenzen der Art

Moehren haben je nach Cultivar unterschiedliche Resistenzen, besonders gegen Alternaria und Moehrenfliege.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Alternaria dauci (Blattflecken) | Krankheit | Cultivare wie 'Bolero', 'Maestro', 'Mokum' | `resistant_to` |
| Psila rosae (Moehrenfliege) | Schaedling | Teiltolerant: 'Flyaway', 'Resistafly' (Geruchsreduktion) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Doldenblutler (Apiaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kohl, Kartoffel, Tomate) oder Huelsenfruechte (N-Anreicherung) |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Radieschen, Krauter) oder Gruenduengung |
| Anbaupause (Jahre) | 3--5 Jahre fuer Apiaceae (Sellerie, Petersilie, Dill, Fenchel, Pastinake) auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Zwiebel | Allium cepa | 0.9 | Klassische Mischkultur! Zwiebelgeruch verwirrt Moehrenfliege, Moehrengeruch verwirrt Zwiebelfliege | `compatible_with` |
| Lauch | Allium porrum | 0.9 | Wie Zwiebel -- gegenseitige Fliegenabwehr | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Fliegenabwehr, Pilzabwehr | `compatible_with` |
| Erbse | Pisum sativum | 0.8 | N-Fixierung, lockerer Boden nach Ernte | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Gute Raumausnutzung, Bodenbeschattung zwischen Reihen | `compatible_with` |
| Radieschen | Raphanus sativus | 0.8 | Reihenmarkierung (schnellkeimend), Bodenlockerung | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Gegenseitige Schaedlingsabwehr (Tomate vertreibt Moehrenfliege) | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr im Boden | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.8 | Pilzabwehr, Fliegenabwehr | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Dill | Anethum graveolens | Gleiche Familie (Apiaceae) -- Kreuzbestaeubung moeglich, gleiche Schaedlinge/Krankheiten | moderate | `incompatible_with` |
| Sellerie | Apium graveolens | Gleiche Familie -- gemeinsame Krankheiten (Septoria, Alternaria), Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Petersilie | Petroselinum crispum | Gleiche Familie -- gemeinsame Schaedlinge (Moehrenfliege) und Krankheiten | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Gleiche Familie + allelopathische Wirkung, hemmt Moehrenwachstum | severe | `incompatible_with` |
| Rote Bete | Beta vulgaris subsp. vulgaris | Konkurrenz um Bor und Mangan im Wurzelbereich; beide tiefwurzelnde Gemuese verdraengen sich gegenseitig bei geringer Bodentiefe | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Apiaceae (mit sich selbst) | `shares_pest_risk` | Moehrenfliege (Psila rosae), Alternaria, Cercospora, Nematoden | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Standard-Moehre |
|-----|-------------------|-------------|------------------------------|
| Pastinake | Pastinaca sativa | Gleiche Familie, aehnliche Kultur | Frosthaerter, wuerziger, winterfest im Boden |
| Petersilienwurzel | Petroselinum crispum var. tuberosum | Gleiche Familie, Speicherwurzel | Intensiveres Aroma, doppelter Nutzen (Blatt + Wurzel) |
| Rote Bete | Beta vulgaris | Aehnliche Kultur, Wurzelgemuese | Schnellere Ernte, frosthaerter, auch Blaetter essbar |
| Schwarzwurzel | Scorzonera hispanica | Wurzelgemuese | Winterhart, mehrjaehrig moeglich, "Spargel des armen Mannes" |
| Radieschen | Raphanus sativus | Wurzelgemuese, gleiche Anbaulage | Sehr schnelle Ernte (25--30 Tage), gute Vorfrucht |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Daucus carota subsp. sativus,Moehre;Karotte;Mohrrube;Gelbe Ruebe;Carrot,Apiaceae,Daucus,biennial,day_neutral,herb,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b,0.1,"Europa, Westasien"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Moehre (generisch),Daucus carota subsp. sativus,,,high_yield,90,,open_pollinated
Nantes 2,Daucus carota subsp. sativus,,,high_yield;heirloom,80,,open_pollinated
Flakkee,Daucus carota subsp. sativus,,,high_yield;long_season,130,,open_pollinated
Pariser Markt,Daucus carota subsp. sativus,,,compact;early_maturing,65,,open_pollinated
Bolero,Daucus carota,Vilmorin,,disease_resistant;high_yield,75,alternaria,f1_hybrid
Flyaway,Daucus carota subsp. sativus,,,pest_resistant,85,carrot_fly,open_pollinated
Rodelika,Daucus carota,Bingenheim,,high_yield;heirloom,100,,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA -- Carrot Flower (Daucus carota): https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/carrot-flower
2. Johnny's Seeds -- Carrot Pests & Diseases: https://www.johnnyseeds.com/growers-library/vegetables/carrots/carrot-pests-diseases.html
3. NCSU Extension -- Daucus carota subsp. sativus: https://plants.ces.ncsu.edu/plants/daucus-carota-subsp-sativus/
4. UF/IFAS Extension -- Carrot Nitrogen Guidelines: https://edis.ifas.ufl.edu/publication/AE588
5. fryd.app -- Companion Plants for Carrots: https://fryd.app/en/magazine/companion-planting-carrots
6. DeepGreen Permaculture -- Carrots Growing Guide: https://deepgreenpermaculture.com/2024/04/23/carrots-growing-guide/
7. PlantVillage -- Carrot Diseases and Pests: https://plantvillage.psu.edu/topics/carrot/infos
8. Gartenjournal -- Moehren gute Nachbarn: https://www.gartenjournal.net/moehren-gute-nachbarn
9. Hortipendium -- Moehren: https://www.hortipendium.de/Moehren
10. Old Farmer's Almanac -- Carrots: https://www.almanac.com/plant/carrots
11. StonePost Gardens -- What to Plant After Carrots: https://stonepostgardens.com/what-to-plant-after-carrots/
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
12. MDPI Plants (2022) -- "Vernalization Requirement, but Not Post-Vernalization Day Length, Conditions Flowering in Carrot (Daucus carota L.)": https://www.mdpi.com/2223-7747/11/8/1075 -- Beleg fuer Photoperiode day_neutral (vernalisationsgesteuerte Bluete, Tageslaenge nicht massgeblich)
13. Nature Scientific Reports (2020) -- "The Response of COL and FT Homologues to Photoperiodic Regulation in Carrot": https://www.nature.com/articles/s41598-020-66807-y -- Beleg fuer kontroverse Langtag-/Tagneutral-Einstufung
14. FAO -- Annex 1: Crop salt tolerance data (Maas & Hoffman): https://www.fao.org/4/y4263e/y4263e0e.htm -- Beleg fuer Salztoleranz: ECe-Schwelle 1.0 dS/m, Slope 14%/dS/m, Rating sensitive
15. Wikipedia -- Salt tolerance of crops (Maas 1986, Carrot 1.0 dS/m / 14%): https://en.wikipedia.org/wiki/Salt_tolerance_of_crops -- zweite Quelle Salztoleranz
16. ScienceDirect (2025) -- "Base and upper temperature thresholds for GDD (FAO56rev) review": https://www.sciencedirect.com/science/article/pii/S037837742500469X -- Beleg GDD-Basistemperatur Moehre 4--6 degC
17. GrowVeg -- Vegetable Root Depths Revealed: https://www.growveg.com/guides/vegetable-root-depths-revealed-use-this-guide-to-make-smarter-planting-decisions/ -- Beleg effektive Wurzeltiefe (medium-rooted, ~46 cm)
18. Epic Gardening -- How to Vernalize Carrots / GroEat Vernalization: https://www.epicgardening.com/vernalizing-carrots/ -- Beleg Vernalisation 6--8 Wochen < 10 degC
19. Greg / The Corner Plot -- Optimal Temperature for Carrots (15.5--21 degC): https://thecornerplot.blog/2023/05/27/carrots-and-the-ideal-growing-temperature-what-you-need-to-know/ -- Beleg Photosynthese-/Wuchs-T_opt
20. Old Farmer's Almanac / Garden Tutor -- Carrot soil pH 6.0--6.8: https://www.almanac.com/plant-ph -- Beleg Boden-pH-Vorzug
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -- Korrektur Bluetemonate (6;7 -> 5;6;7) -->
21. Plantura -- Karotte: Herkunft, Bluete & Vermehrung: https://www.plantura.garden/gemuese/karotten/karotten-pflanzenportrait -- "Die Bluetezeit liegt zwischen Mai und Juli" (2. Standjahr, Kulturmoehre)
22. Floristik Haenni -- Karottenbluete: Wann und wie Moehren bluehen: https://floristikhaenni.ch/karotten-blume/ -- "Die Bluetezeit der Karotte liegt in der Regel zwischen Mai und Juli"
23. Wikipedia (DE) -- Moehre (Pflanzenart): https://de.wikipedia.org/wiki/M%C3%B6hre_(Pflanzenart) -- "Die Bluetezeit reicht von Mai bis Juli" (unterstuetzende Drittquelle, nicht alleinige Quelle)
<!-- Hinweis: agrarraum.info nennt abweichend "Bluetezeit beginnt im Juni" (https://www.agrarraum.info/lexikon/karotte) und Cornell/MSU Extension nennen fuer die nordamerikanische Wildform Juli-September (https://blogs.cornell.edu/weedid/wild-carrot/, https://www.canr.msu.edu/weeds/extension/wild-carrot) -- als abweichende Einzelquellen fuer den Bluetebeginn im Report dokumentiert, aber durch die 3 uebereinstimmenden Mitteleuropa-Kulturmoehre-Quellen 21-23 fuer den Start Mai nicht entkraeftet. -->
<!-- /Quelle: growing-phase-auditor 2026-07 -->
