# Rosenkohl -- Brassica oleracea var. gemmifera

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** grove.eco, naturadb.de, samen.de, fryd.app, floragard.de, Hortipendium, wurzelwerk.net, botanikguide.de, gruenundgesund.de, pflanzenkrankheiten.ch, Oregon State Extension, UGA Extension, Portland Nursery, FAO Land & Water, Ohio State Extension, MSU Extension, University of Delaware, SeedSavers, ScienceDirect <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. gemmifera | `species.scientific_name` |
| Volksnamen (DE/EN) | Rosenkohl; Kohlsprossen; Bruesseler Kohl; Brussels Sprouts; Sprouts | `species.common_names` |
| Familie | Brassicaceae | `species.family` -> `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 (Brassicaceae sind C3-Pflanzen) | `species.photosynthesis_type` |
| GDD-Basistemperatur (degC) | 4--5 (Hauptwuchsphase; kuehlliebende Kohlart -- Studienwerte mit Basis +5 degC, Cole-Crops-Reviews 3--5 degC) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | biennial (in Kultur als annual genutzt -- Ernte im 1. Jahr) | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (kein echter Kurz-/Langtagblueher; Bluete im 2. Jahr wird ueber Vernalisation/Kaeltereiz induziert, nicht ueber Tageslaenge -- Korpus-Konvention fuer vernalisationsgesteuerte Arten) | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false (keine echte Endodormanz; Pflanze waechst bei milder Witterung durch) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (echte Kaeltevernalisation -- Bluetenbildung im 2. Jahr nur nach Kaelteperiode) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | 14--56 (2--8 Wochen Kaelte bei ca. 1--4 degC; relevant nur fuer Samenbau im 2. Jahr, nicht fuer Roeschenernte) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslaenge (h) | -- (day_neutral: Roeschenbildung wird durch Temperatur/Frost ausgeloest, kein echter Kurztag-/Langtagblueher; Bluete benoetigt Vernalisation, nicht Photoperiode) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 2a; 2b; 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | very_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Der winterhaerteste aller Kohlarten. Ausgewachsene Pflanzen vertragen Temperaturen bis ca. -15 degC. Leichter Frost verbessert den Geschmack (Umwandlung von Staerke in Zucker). Jungpflanzen sind empfindlicher -- Spaetfrost unter -5 degC kann schaedigen. | `species.hardiness_detail` |
| Heimat | Nordwesteuropa (Belgien -- erste Zucht im 18. Jahrhundert; Urform: Wildkohl an Atlantikkuesten) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; cold_hardy | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6--8 (Aussaat ab Maerz/April) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Direktsaat ab April moeglich, Pflanzung bevorzugt) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4; 5 | `species.direct_sow_months` |
| Erntemonate | 10; 11; 12; 1; 2; 3 | `species.harvest_months` |
| Bluetemonate | -- (Bluete unerwuenscht im 1. Kulturjahr; im 2. Jahr: 4; 5; 6) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | intermediate | `species.propagation_difficulty` |

Hinweis: Rosenkohl wird ausschliesslich ueber Samen vermehrt. Die Kulturzeit betraegt ca. 165--200 Tage. Aussaat ab Maerz in Schalen oder Toepfe, Pflanzung ins Freiland ab Mai/Juni. Rosenkohl braucht eine lange, kuehle Wachstumsphase und Frost fuer die beste Qualitaet.

**Keimhinweise:**
- Optimale Keimtemperatur: 18--22 degC
- Minimale Keimtemperatur: 8 degC (sehr langsam)
- Keimdauer: 7--14 Tage (bei optimaler Temperatur 5--8 Tage)
- **Dunkelkeimer** -- Samen 1--2 cm mit Erde bedecken
- Substrat: naehrstoffarme Aussaaterde, gleichmaessig feucht
- Saemlinge pikieren bei 2--3 echten Blaettern in 6--8 cm Toepfe
- Abhaertung vor dem Auspflanzen: 7--10 Tage bei Aussentemperaturen

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (keine; Glucosinolate (Senfolglycoside) sind gesundheitsfoerdernd, koennen in extremen Mengen aber Schilddruesenfunktion beeinflussen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: Rosenkohl (Brassica oleracea) ist fuer Katzen und Hunde ungiftig. Geduensteter Rosenkohl in kleinen Mengen ist sogar als gelegentlicher Hundeleckerli geeignet. Groessere Mengen koennen Blaehungen verursachen (bei Mensch und Tier).

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 8; 9 | `species.pruning_months` |

Hinweis: Ab August/September die Triebspitze (Endknospe) kappen ("Koepfen"). Dies stoppt das Laengenwachstum und foerdert die gleichmaessige Roeschenentwicklung am gesamten Stamm. Unterste Blaetter regelmaessig entfernen (verbessert Luftzirkulation und erleichtert die Ernte). Seitentriebe an der Basis entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (grosse Pflanze, mind. 20 L Topfvolumen, Standfestigkeit problematisch) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20--30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 60--100 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50--60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50--70 | `species.spacing_cm` |
| Indoor-Anbau | no (lange Kulturzeit, hoher Platzbedarf, braucht Frost) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur in grossen Kuebeln; Standfestigkeit sichern) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Rosenkohl braucht Frost fuer guten Geschmack, Gewaechshaus kontraproduktiv) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (bei exponierten Standorten Stuetzpfahl empfohlen -- hohe Pflanzen mit Kopflast durch Roeschen koennen bei Sturm umknicken) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Schwerer, naehrstoffreicher, lehmig-humoser Boden. Gute Standfestigkeit ist wichtig. pH 6.5--7.5 (leicht kalkhaltig). Nicht zu locker -- Rosenkohl braucht festen Halt im Boden. | -- |

**Hinweis:** Rosenkohl ist das klassische Wintergemuese Mitteleuropas. Er braucht eine lange, kuehle Wachstumsphase und Frost verbessert den Geschmack (Staerke wird in Zucker umgewandelt). Pflanzabstand nicht unterschaetzen (50--70 cm). Pflanzen tief setzen (bis zum 1. Blattpaar) fuer bessere Standfestigkeit. Anhaeuufeln ab August foerdert zusaetzlich die Stabilitaet.

### 1.7 Umgebungs-Physiologie & Standortqualitaet

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD umol/m2/s) | 20 (C3-Sonnenblatt bei ca. 15 degC; Nettophotosynthese = 0) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD umol/m2/s) | 40 (steigt mit Blatttemperatur an) | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun (mind. 6 h direkte Sonne fuer feste Roeschen) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 40--50 (flachwurzelnde Cole-Crop; Hauptwurzelmasse in oberen 0.4--0.5 m, FAO Cabbage) | `species.effective_root_depth_cm` |
| Staunaesse-Toleranz | sensitive (Staunaesse foerdert Wurzelfaeule und Kohlhernie; braucht gut drainierten Boden) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | 1.8 (Substrat-ECe, Maas-Hoffman a; Bezug Bodensaettigungsextrakt, NICHT Giesswasser-EC) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | 9.7 (Maas-Hoffman b; Ertragsrueckgang je dS/m oberhalb der Schwelle) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug | 6.5--7.5 (Optimum 6.5--7.0; pH >= 6.5 unterdrueckt Kohlhernie; harmonisiert mit S.1.6 und S.2.3) | `species.soil_ph_preference` |

Hinweis: Der Lichtkompensationspunkt gibt nur den Nettonull-Punkt an. Lichtsaettigung liegt deutlich hoeher (Sonnenkultur), siehe PPFD-Zielwerte in S.2.2. Die ECe-Schwelle bezieht sich auf den Bodensaettigungsextrakt (ECe), nicht auf die Giesswasser-Leitfaehigkeit.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--14 | 1 | false | false | low |
| Saemling (seedling) | 28--42 | 2 | false | false | low |
| Vegetativ (vegetative) | 60--90 (Stengel- und Blattentwicklung) | 3 | false | false | medium |
| Roeschenbildung (vegetative spaet) | 60--90 (Herbst/Winter) | 4 | false | true | high |
| Ernte (harvest) | 30--90 (gestaffelte Ernte von unten nach oben) | 5 | true | true | high |

Hinweis: Rosenkohl hat keine echte Bluetephase im 1. Kulturjahr. Die Roeschenbildung beginnt an der Stengelbasis und schreitet nach oben fort. Ernte beginnt, wenn die unteren Roeschen ca. 2--3 cm Durchmesser haben und fest geschlossen sind. Gestaffelte Ernte von unten nach oben ueber mehrere Wochen/Monate.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | -- (Dunkelkeimer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 (optimal 20) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 (kritischer Punkt oberhalb des Zielkorridors; feuchteliebende Keimphase) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Blattgemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | -- (Dunkelkeimer; keine Photosynthese) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | -- (Dunkelkeimung) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (Substrat gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 (deutlich oberhalb des Korridors; stomataerer Kollaps) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Blattgemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--22 (kuehlliebend; Nettophotosynthese faellt ueber 25 degC) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Tageslicht-/Freiland-Naehe; bei reiner LED-Anzucht ggf. niedriger) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 (volle Sonne bevorzugt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 15--25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 (Langtag foerdert vegetatives Wachstum) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (oberer Zielwert + ~0.4; stomataerer Kollaps bei Hitze/Trockenheit) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Blattgemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 18--24 (kuehlliebend; Nettophotosynthese faellt steil ueber 25 degC) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Rosenkohl bevorzugt kuehle Temperaturen. Hitze ueber 25 degC fuehrt zu lockeren, qualitativ schlechten Roeschen. Ideale Wachstumstemperaturen liegen bei 15--20 degC.

#### Phase: Roeschenbildung (vegetative spaet)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 (natuerlich abnehmend im Herbst) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--14 (natuerlich kuerzere Tage foerdern Roeschenbildung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 10--18 (kuehl ist ideal!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 2--10 (Frost bis -5 degC verbessert Geschmack) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 (oberer Zielwert + ~0.4; in kuehler Herbstphase selten erreicht) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivitaet | medium (C3-Blattgemuese) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (degC) | 12--18 (kuehle Herbstphase; Roeschenqualitaet steigt bei niedrigen Temperaturen) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht/Freiland) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (natuerlicher Niederschlag oft ausreichend) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Kuehle Nachttemperaturen und leichter Frost sind ERWUENSCHT -- sie verbessern den Geschmack signifikant (Staerke-Zucker-Umwandlung). Rosenkohl ist die einzige gaertnerisch relevante Kultur, deren Qualitaet durch Frost VERBESSERT wird.

### 2.3 Naehrstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 (Spalten Mn/Zn/Cu/Mo) -->
| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0-0-0 | 0.0 | 6.5--7.0 | -- | -- | -- | -- | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.5--0.8 | 6.2--6.8 | 80 | 30 | 30 | 2 | 0.25 | 0.03 | 0.01 | 0.01 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 6.2--6.8 | 150 | 50 | 50 | 4 | 0.5 | 0.05 | 0.02 | 0.05 |
| Roeschenbildung | 2-2-3 | 1.6--2.2 | 6.2--6.8 | 180 | 60 | 50 | 4 | 0.5 | 0.05 | 0.02 | 0.05 |
| Ernte | 0-0-0 | 0.0 | -- | -- | -- | -- | -- | -- | -- | -- | -- |

Hinweis (Mikronaehrstoffe): Mn/Zn/Cu orientieren sich an Standard-Hoagland-Loesungskonzentrationen (Mn 0.5, Zn 0.05, Cu 0.02 ppm bei Vollversorgung). Brassicaceae haben einen ueberdurchschnittlich hohen Molybdaen-Bedarf -- Mo-Mangel verursacht "Whiptail" (deformierte, riemenfoermige Blaetter), besonders auf sauren Boeden; daher Mo gegenueber dem Hoagland-Standard (0.01 ppm) in der Hauptwuchsphase angehoben. Bor (B) ist bei Kohl ebenfalls kritisch (Hohlstrunk, braune Roeschen) -- siehe S.2.3-Hinweis und S.3.4.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 (Spalten Mn/Zn/Cu/Mo) -->

Hinweis: Rosenkohl ist ein Starkzehrer mit besonders hohem Stickstoff- und Kaliumbedarf. ACHTUNG: Ueberduengung mit Stickstoff fuehrt zu lockeren, qualitativ schlechten Roeschen und reduzierter Winterhaerte. N-Duengung ab August STOPPEN, damit die Roeschen fest und kompakt werden. Bor-Mangel kann zu hohlen Stengeln fuehren.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--14 Tage | Keimblaetter voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 28--42 Tage (Auspflanzung nach ca. 6 Wochen) | 4--6 echte Blaetter, kraeftige Pflanze ca. 10--15 cm hoch |
| Vegetativ -> Roeschenbildung | time_based / event_based | 60--90 Tage nach Pflanzung (August/September) | Erste Roeschenansaetze in den Blattachseln sichtbar, natuerlich kuerzere Tage |
| Roeschenbildung -> Ernte | manual | Ab ca. 165 Tage nach Aussaat (Oktober) | Untere Roeschen 2--3 cm Durchmesser, fest geschlossen |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |
| Flora Bloom | General Hydroponics | base | 0-5-4 | 0.10 | 5 | Roeschenbildung |

Hinweis: Hydroponischer Rosenkohl-Anbau ist unueblich, da die Pflanze Frost fuer guten Geschmack benoetigt.

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (grosszuegig einarbeiten) | heavy_feeder |
| Gut verrotteter Rindermist | div. | organisch | 3--5 L/m2 | Herbst/Fruehjahr (einarbeiten) | heavy_feeder |
| Hornmehl (fein) | Oscorna / div. | organisch (N-Langzeit) | 60--80 g/m2 | Fruehjahr (Einarbeitung) | heavy_feeder |
| Bio Tomatendunger (fluessig) | COMPO BIO | organisch | 30--40 ml / 10 L Giesswasser | Mai--Juli, alle 14 Tage | heavy_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 1 L/Pflanze | Juni--Juli, alle 14 Tage | heavy_feeder |
| Kalimagnesia (Patentkali) | div. | mineralisch-organisch | 40--50 g/m2 | August (Kalium fuer Roeschenqualitaet und Frosthaerte) | heavy_feeder |
| Algenkalk | div. | kalkduenger | 100--150 g/m2 | Fruehjahr | alle (pH-Anhebung, Kohlhernie-Praevention) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Rosenkohl Standard Organisch Freiland")

| Monat | Phase | Duengerprodukt | Menge | Hinweise |
|-------|-------|---------------|-------|----------|
| April | Bodenvorbereitung | Reifkompost + Hornmehl + Algenkalk | 5 L/m2 + 70 g/m2 + 100 g/m2 | Einarbeiten in obere 20 cm |
| Mai/Juni | Pflanzung | Bio Tomatendunger | 30 ml / 10 L | Angiessloesung bei Pflanzung |
| Juni | Vegetativ | Brennnesseljauche | 1:10, 1 L/Pflanze | Alle 14 Tage |
| Juli | Vegetativ | Bio Tomatendunger | 30 ml / 10 L | Letzte N-betonte Duengung |
| August | Roeschenbildung | Kalimagnesia (Patentkali) | 40 g/m2 | K foerdert Roeschenqualitaet und Frosthaerte; N-Duengung STOPPEN |
| Sep--Nov | Ernte | -- | -- | Keine weitere Duengung |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Flora Micro (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Flora Gro / Flora Bloom (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer!** Rosenkohl gehoert zu den naehrstoffhungrigsten Gemusearten. Boden muss gut mit Kompost und organischem Dunger versorgt sein.
- **N-Duengung ab August stoppen!** Zu spaete oder zu hohe Stickstoffduengung fuehrt zu lockeren, qualitativ schlechten Roeschen, die bitter schmecken und schlecht lagern. Ausserdem verringert hohe N-Versorgung die Winterhaerte.
- **Kalium fuer Qualitaet und Frosthaerte:** Kalimagnesia (Patentkali) im August foerdert feste Roeschen, guten Geschmack und verbessert die Frostresistenz.
- **Kalk gegen Kohlhernie:** Saure Boeden (pH < 6.5) foerdern Kohlhernie (Plasmodiophora brassicae). Regelmaessig kalken (Algenkalk, 100--150 g/m2 im Fruehjahr).
- **Bor-Mangel:** Hohle Stengel und braune Flecken in Roeschen koennen auf Bor-Mangel hindeuten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (Freiland im Winter; natuerlicher Niederschlag genuegt bei etablierten Pflanzen) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich (bevorzugt sogar leicht kalkhaltiges Wasser). Morgens giessen, direkt an den Wurzelbereich. Staunaesse vermeiden (Wurzelfaeule). | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 (Mai--Juli); dann Stopp | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8 (August nur Kalium) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig/zweijaehrig) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | Ernte (Spaetsorte) | Roeschen von unten nach oben ernten; bei strengem Frost Pflanzen mit Vlies schuetzen | mittel |
| Feb | Ernte + Raeumen | Letzte Ernte; abgeerntete Pflanzen roden, Strunk im Restmuell (nicht kompostieren bei Kohlhernie) | mittel |
| Marz | Aussaat starten | Aussaat in Schalen/Toepfe bei 18--20 degC | hoch |
| Apr | Pikieren | Saemlinge bei 2--3 echten Blaettern in Einzeltoepfe (8 cm) | hoch |
| Mai | Abhaertung + Auspflanzen | 7--10 Tage abhaerten; Pflanzung ins Freiland ab Ende Mai, 50--70 cm Abstand, TIEF setzen, Kulturschutznetz anbringen | hoch |
| Jun | Pflege + Duengung | Regelmaessig giessen, Brennnesseljauche alle 14 Tage, Unkraut jaeten, Kulturschutznetz kontrollieren | hoch |
| Jul | Duengung + Anhaeuufeln | Letzte N-Duengung; Erde um Stengelbasis anhaeuufeln fuer Standfestigkeit; Stuetzpfahl setzen | hoch |
| Aug | Koepfen + K-Duengung | Triebspitze kappen; Kalimagnesia streuen; unterste Blaetter entfernen; N-Duengung STOPPEN | hoch |
| Sep | Roeschenentwicklung beobachten | Erste Roeschen werden sichtbar; auf Kohlweisslinge und Blattlaeuse kontrollieren | mittel |
| Okt | Erntebeginn | Untere Roeschen ab 2--3 cm Durchmesser ernten (von unten nach oben); Frost abwarten fuer besten Geschmack | hoch |
| Nov | Ernte + Frostschutz | Ernte fortsetzen; bei strengem Frost (< -10 degC) Vlies umlegen | hoch |
| Dez | Ernte | Gestaffelte Ernte fortsetzen; der beste Geschmack ist nach mehreren Frostereignissen | hoch |

### 4.3 Ueberwinterung

Rosenkohl ist der winterhaerteste aller Kohlarten und uebersteht Temperaturen bis ca. -15 degC. Die Pflanzen bleiben den Winter ueber im Beet stehen und werden gestaffelt geerntet. Bei extremem Frost (unter -15 degC) schuetzt ein Vlies oder Frostschutzvlies die oberen Roeschen. Frost verbessert den Geschmack erheblich (Staerke-Zucker-Konversion). Pflanzen im Fruehjahr nach der letzten Ernte roden.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Einstufung | hardy (winterhart im Beet, bis ca. -15 degC; keine Einlagerung noetig) | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | none (Standard); bei strengem Kahlfrost < -15 degC: fleece (Vlies ueber die Pflanze) | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 11; 12; 1 (Vlies nur bei Bedarf) | `overwintering_profiles.winter_action_month` |
| Fruehjahrs-Massnahme | replant (abgeerntete Struenke roden, Flaeche fuer Folgekultur raeumen) | `overwintering_profiles.spring_action` |
| Fruehjahrs-Massnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (degC) | -- (keine Einlagerung; Pflanze bleibt im Freiland) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | -- (Freiland, natuerliches Tageslicht) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Giessen | -- (natuerlicher Niederschlag genuegt; nicht giessen bei Frost) | `overwintering_profiles.winter_quarter_watering` |

Hinweis: Rosenkohl wird NICHT eingelagert (kein `dig_and_store`) und NICHT ins Haus geholt (kein `frost_free`) -- er ist echt winterhart (`hardy`) und wird ueber den Winter direkt im Beet beerntet. Ein Vlies dient nur dem Schutz der oberen Roeschen bei extremem Kahlfrost, nicht dem Ueberleben der Pflanze.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweissling (Cabbage White) | Pieris brassicae, Pieris rapae | Raupen fressen Blaetter skelettartig ab; Eier (gelbe Gruppen) auf Blattunterseite | leaf | vegetative | easy |
| Kohlfliege (Cabbage Root Fly) | Delia radicum | Maden fressen an Wurzeln, Pflanze welkt und kuemmert | root | seedling, vegetative | hard |
| Erdfloh (Flea Beetle) | Phyllotreta spp. | Kleine runde Loecher in Blaettern (Fensterfrass), besonders an Jungpflanzen | leaf | seedling | easy |
| Kohlblattlaus (Mealy Cabbage Aphid) | Brevicoryne brassicae | Dichte Kolonien grau-gruener Laeuse unter Blaettern, Blaetter kraeueln sich | leaf | vegetative | easy |
| Kohlmotte (Diamondback Moth) | Plutella xylostella | Kleine gruene Raupen, "Fensterfrass" auf Blaettern (Epidermis bleibt stehen) | leaf | vegetative | medium |
| Kohleule (Cabbage Moth) | Mamestra brassicae | Grosse, gruene Raupen fressen an Blaettern und Roeschen | leaf, fruit (Roeschen) | vegetative | easy |
| Schnecken (Slugs/Snails) | Arion spp. | Lochfrass, Schleimspuren, bevorzugt Jungpflanzen | leaf | seedling | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kohlhernie (Clubroot) | protist (Plasmodiophora brassicae, Phytomyxea; KEIN Pilz) | Knotige, geschwollene Wurzeln; Pflanze welkt bei Hitze, kuemmert; KEIN Fungizid wirksam | acidic_soil (pH < 6.5), waterlogging | 21--42 | seedling, vegetative |
| Falscher Mehltau (Downy Mildew) | fungal (Oomycet) | Gelbe Flecken auf Blattoberseite, grau-weisser Sporenrasen auf Unterseite | high_humidity, cool_nights | 5--10 | vegetative |
| Grauschimmel (Grey Mold) | fungal | Grauer, pelziger Belag auf Roeschen und Blaettern | high_humidity, poor_airflow | 3--5 | vegetative (spaet) |
| Kohlschwarzringfleckigkeit (Ring Spot) | fungal | Runde, dunkelbraune Flecken mit konzentrischen Ringen auf Blaettern | high_humidity, rain_splash | 7--14 | vegetative |
| Bakterielle Schwarzfaeule (Black Rot) | bacterial | V-foermige, gelbe Blattnekrosen vom Rand her; Blattadern schwarz | warm_wet_conditions, seed_contamination | 7--14 | vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Trichogramma brassicae (Eiparasitoid) | Kohlweissling (Eier) | 1--3 Karten/Beet | 7--14 |
| Bacillus thuringiensis (Bt) | Kohlweissling-Raupen, Kohleule, Kohlmotte | Spruehung nach Herstellerangabe | 2--5 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Kulturschutznetz | Kohlfliege, Kohlweissling, Kohlmotte | 1 Netz/Beet | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz (0.8 mm Maschenweite) | cultural | -- | Netz direkt nach Pflanzung ueber Beet spannen, bis September | 0 | Kohlweissling, Kohlfliege, Kohlmotte, Erdfloh |
| Bacillus thuringiensis (Bt) | biological | Bt-Toxin (Cry1Ab) | Spruehung auf Raupen, alle 7 Tage bei Befall | 3 | Kohlweissling-Raupen, Kohlmotte, Kohleule |
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse, Erdfloh |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Algenkalk / Kalkung | cultural | CaCO3 | 100--150 g/m2 im Fruehjahr vor Pflanzung | 0 | Kohlhernie (Praevention durch pH > 7.0) |
| Kohlkragen (Kohlfliegen-Kragen) | cultural | -- | Pappscheibe um Stengelbasis, verhindert Eiablage | 0 | Kohlfliege |
| Absammeln | cultural | -- | Raupen und Eigelege per Hand absammeln, taeglich kontrollieren | 0 | Kohlweissling, Kohleule |
| Befallene Pflanzen roden + Restmuell | cultural | -- | Pflanzen mit Kohlhernie sofort roden, im Restmuell entsorgen (NICHT kompostieren!) | 0 | Kohlhernie |

### 5.5 Resistenzen der Art

Rosenkohl als Art hat moderate natuerliche Resistenzen. Die Glucosinolate (Senfolglycoside) wirken auf viele Insekten abschreckend; trotzdem sind spezialisierte Kohlschaedlinge (Kohlweissling, Kohlfliege) ein ernstes Problem.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Frost / Kaelte | Stressfaktor | Arteigen (winterhaertester Kohl, bis -15 degC) | -- |
| Kohlhernie | Krankheit | Cultivare wie 'Crispus F1', 'Nautic F1' (tolerant) | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Kreuzblueuter (Brassicaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae), Kartoffel, oder Gruenduengung |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Radieschen, Spinat) oder Gruenduengung |
| Anbaupause (Jahre) | 3--4 Jahre fuer Brassicaceae auf gleicher Flaeche (STRENG wegen Kohlhernie! Sporen ueberleben 20+ Jahre im Boden) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sellerie | Apium graveolens | 0.9 | Sellerie-Duft schreckt Kohlweisslinge ab (klassische Kohl-Sellerie-Mischkultur) | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Tomaten-Duft vertreibt Kohlweisslinge | `compatible_with` |
| Spinat | Spinacia oleracea | 0.8 | Bodenbeschattung, schnelle Zwischenkultur, unterschiedlicher Naehrstoffbedarf | `compatible_with` |
| Mangold | Beta vulgaris subsp. vulgaris | 0.7 | Ergaenzende Ernte, gute Raumnutzung | `compatible_with` |
| Moehre | Daucus carota | 0.7 | Unterschiedliche Wurzeltiefen, gute Platzausnutzung | `compatible_with` |
| Rote Beete | Beta vulgaris | 0.7 | Ergaenzende Kultur, Bodenbeschattung | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes patula | 0.8 | Nematoden-Abwehr, Bestauber anlocken | `compatible_with` |
| Ringelblume | Calendula officinalis | 0.7 | Nuetzlinge anlocken, Ablenkung fuer Schaedlinge | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Andere Kohlarten | Brassica oleracea (alle Varianten) | Gleiche Art, geteilte Schaedlinge und Krankheiten (Kohlhernie, Kohlweissling), Naehrstoffkonkurrenz | severe | `incompatible_with` |
| Senf | Sinapis alba | Gleiche Familie (Brassicaceae), geteilte Krankheiten (Kohlhernie) | moderate | `incompatible_with` |
| Rettich | Raphanus sativus | Gleiche Familie, Kohlhernie-Uebertragung | moderate | `incompatible_with` |
| Erdbeere | Fragaria x ananassa | Beide anfaellig fuer Schnecken, Naehrstoffkonkurrenz | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Brassicaceae (mit sich selbst) | `shares_pest_risk` | Kohlhernie (Plasmodiophora brassicae), Kohlweissling, Kohlfliege, Falscher Mehltau, Schwarzfaeule | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Rosenkohl |
|-----|-------------------|-------------|------------------------------|
| Gruenkohl (Krauskohl) | Brassica oleracea var. sabellica | Gleiche Art, aehnliche Winterhaerte | Einfacherer Anbau, weniger Schaedlingsprobleme, kuerzere Kulturzeit |
| Blumenkohl | Brassica oleracea var. botrytis | Gleiche Art, andere Nutzung | Kuerzere Kulturzeit, vielseitigere Kueche |
| Flower Sprouts (Kalettes) | Brassica oleracea var. gemmifera x sabellica | Kreuzung Rosenkohl x Gruenkohl | Milderer Geschmack, dekorativer, trendiger |
| Kohlrabi | Brassica oleracea var. gongylodes | Gleiche Art, Knollennutzung | Viel kuerzere Kulturzeit (8--10 Wochen), einfacher |
| Wirsing | Brassica oleracea var. sabauda | Gleiche Art, Kopfkohl | Kuerzere Kulturzeit, vielseitiger |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,frost_sensitivity,nutrient_demand_level,green_manure_suitable,traits,direct_sow_months,harvest_months,sowing_indoor_weeks_before_last_frost
Brassica oleracea var. gemmifera,Rosenkohl;Kohlsprossen;Bruesseler Kohl;Brussels Sprouts;Sprouts,Brassicaceae,Brassica,biennial,day_neutral,herb,taproot,2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.0,"Nordwesteuropa (Belgien)",very_hardy,heavy_feeder,false,edible;cold_hardy,4;5,10;11;12;1;2;3,6
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Groninger,Brassica oleracea var. gemmifera,,,heirloom;late_maturing,180,,open_pollinated
Roodnerf,Brassica oleracea var. gemmifera,,,heirloom;red_stalk;late_maturing,180,,open_pollinated
Crispus F1,Brassica oleracea var. gemmifera,,,disease_resistant;compact;early_maturing,150,clubroot,f1_hybrid
Nautic F1,Brassica oleracea var. gemmifera,,,disease_resistant;high_yield,160,clubroot,f1_hybrid
Igor F1,Brassica oleracea var. gemmifera,,,compact;high_yield;cold_hardy,165,,f1_hybrid
Hilds Ideal,Brassica oleracea var. gemmifera,,,heirloom;uniform_sprouts,175,,open_pollinated
Rosenkohl (Pötschke Historisch),Brassica oleracea var. gemmifera,Pötschke,,heirloom;cold_hardy,180,,open_pollinated
```

---

## Quellenverzeichnis

1. grove.eco -- Rosenkohl: https://www.grove.eco/pflanzen/brassica-oleracea-gemmifera/
2. naturadb.de -- Rosenkohl: https://www.naturadb.de/pflanzen/brassica-oleracea-var-gemmifera/
3. samen.de -- Rosenkohl anbauen: https://samen.de/blog/schritt-fuer-schritt-anleitung-zum-anbau-von-rosenkohl.html
4. samen.de -- Rosenkohl schuetzen: https://samen.de/blog/rosenkohl-schuetzen-krankheiten-und-schaedlinge-bekaempfen.html
5. samen.de -- Rosenkohl in Mischkultur: https://samen.de/blog/rosenkohl-in-mischkultur-ertragreiche-nachbarschaften.html
6. fryd.app -- Rosenkohl pflanzen: https://fryd.app/magazin/rosenkohl-anbauen
7. floragard.de -- Rosenkohl: https://www.floragard.de/de-de/pflanzeninfothek/pflanze/gemuese/brassica-oleracea-var-gemmifera
8. Hortipendium -- Rosenkohl Pflanzenschutz: https://www.hortipendium.de/Rosenkohl_Pflanzenschutz
9. wurzelwerk.net -- Rosenkohl: https://www.wurzelwerk.net/gemuesegarten/gemueseportraits/rosenkohl/
10. botanikguide.de -- Rosenkohl pflanzen: https://botanikguide.de/rosenkohl-pflanzen-so-gelingt-der-anbau-im-garten/
11. gruenundgesund.de -- Rosenkohl Mischkultur: https://gruenundgesund.de/magazin/naturgarten-selbstversorgung/rosenkohl-mischkultur/
12. pflanzenkrankheiten.ch -- Kohlgemuese: https://www.pflanzenkrankheiten.ch/krankheiten-an-kulturpflanzen-2/gemuese-offcanvas/brassica-arten-offcanvas/kohlgemuese-krankheiten-schaedlinge-einleitung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
13. FAO Land & Water -- Cabbage (Brassica oleracea): Wurzeltiefe 0.4--0.5 m, Salztoleranz ECe-Schwelle 1.8 dS/m, moderately sensitive, p=0.35: https://www.fao.org/land-water/databases-and-software/crop-information/cabbage/en/
14. Wikipedia -- Salt tolerance of crops: Brassica oleracea (cabbage) moderately sensitive, ECe-Schwelle ~1.8 dS/m, Slope ~9.7 %/dS/m (nach Maas & Hoffman): https://en.wikipedia.org/wiki/Salt_tolerance_of_crops
15. ResearchGate -- The Effect of Planting Times on Brussels Sprouts (Brassica oleracea var. gemmifera): thermische Zeit mit Basistemperatur +5 degC: https://www.researchgate.net/publication/46026707
16. ScienceDirect -- Base and upper temperature thresholds for GDD (FAO56rev): Cole-Crops-Basistemperatur ca. 3--5 degC: https://www.sciencedirect.com/science/article/pii/S037837742500469X
17. SeedSavers -- How to Grow & Save Brussels Sprouts: biennial, Vernalisation 2--8 Wochen Kaelte zur Bluetenbildung im 2. Jahr: https://shop.seedsavers.org/site/pdf/grow-save-brussels-sprouts.pdf
18. LearnSeedSaving -- Brussels Sprouts: Vernalisationsbedingungen (ca. 1--4 degC, 2--8 Wochen): https://www.learnseedsaving.com/brussels-sprouts/
19. ScienceDirect Topics -- Light Compensation Point: C3-Pflanzen LCP ~8--16 (Schatten) bis ~20--50 umol/m2/s (Sonne, temperaturabhaengig): https://www.sciencedirect.com/topics/engineering/light-compensation
20. ScienceDirect Topics -- Compensation Point (C3): LCP steigt von ca. 20 umol/m2/s bei 15 degC auf >50 bei 30 degC: https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/compensation-point
21. Portland Nursery -- Brussels Sprouts Site Requirements: full sun, gut drainierter Boden, pH 6.0--7.5: https://portlandnursery.com/docs/veggies/brussels-sprout.pdf
22. Ohioline (Ohio State University Extension) -- Growing Cabbage: Boden-pH ~6.8 optimal zur Kohlhernie-Vermeidung, Wachstumsoptimum 15--24 degC: https://ohioline.osu.edu/factsheet/hyg-1611
23. Hoagland solution (Wikipedia) -- Mikronaehrstoff-Standardkonzentrationen: Mn 0.5, Zn 0.05, Cu 0.02, Mo 0.01 ppm: https://en.wikipedia.org/wiki/Hoagland_solution
24. MSU Extension -- Commercial Vegetable Recommendations, Cole Crops: erhoehter Bor- und Molybdaen-Bedarf der Brassicaceae (Whiptail bei Mo-Mangel): https://www.canr.msu.edu/resources/commercial_vegetable_recommendations_cole_crops_e1591
25. University of Delaware Weekly Crop Update -- Calcium and Boron Deficiencies in Brassica Crops: hoher Bor-Bedarf, Hohlstrunk/braune Roeschen bei Mangel: https://sites.udel.edu/weeklycropupdate/?p=12446
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
