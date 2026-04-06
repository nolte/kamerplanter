# Schwammgurke -- Luffa aegyptiaca

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Plantura, fryd.app, Floraspora, Freudengarten, Lubera, OMAFRA, NC State Extension, Missouri Botanical Garden, ForwardPlant

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Luffa aegyptiaca | `species.scientific_name` |
| Volksnamen (DE/EN) | Schwammgurke; Luffagurke; Schwammkürbis; Luffa; Loofah; Sponge Gourd; Smooth Luffa; Egyptian Cucumber | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` -> `botanical_families.name` |
| Gattung | Luffa | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day (Bluetenbildung wird durch kuerzerenr Tage ausgeloest; tropischer Ursprung) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Sehr frostempfindlich. Braucht 150--200 frostfreie Tage fuer Schwammreife. In Mitteleuropa (Zone 7--8) nur im Gewaechshaus oder bei sehr fruehzeitiger Vorkultur (Feb/Maerz) erfolgreich kultivierbar. | `species.hardiness_detail` |
| Heimat | Tropisches Asien (Indien, Suedostasien); Nordafrika | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible (jung); fiber_plant; sustainable_sponge; ornamental | `species.traits` |

**Verwendung:** Junge Fruechte (unter 15 cm) sind als Gemuese essbar (asiatische Kueche). Ausgereifte Fruechte liefern den natuerlichen Luffa-Schwamm (Fasergeruest = Xylem). Die Pflanze ist damit Nahrungspflanze UND Industrierohstoff.

**Synonym:** *Luffa cylindrica* (L.) Roem. — weitgehend synonym; POWO bevorzugt *L. aegyptiaca*; in wissenschaftlichen Quellen weiterhin als *L. cylindrica* anzutreffen.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai. Sehr fruehe Vorkultur entscheidend fuer Schwammreife!

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8--10 (Aussaat Februar/Maerz -- sehr frueh; lange Kulturdauer!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (nur in Zone 8+; Boden mind. 20 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 (nur in warmen Gebieten oder Gewaechshaus) | `species.direct_sow_months` |
| Erntemonate | 9; 10 (fuer Schwamm: Fruechte muessen vollstaendig ausreifen und trocknen) | `species.harvest_months` |
| Bluetemonate | 7; 8 (Kurztagspflanze; bluetet erst bei abnehmender Taglaenge) | `species.bloom_months` |

**Kritischer Hinweis:** In Mitteleuropa bluetet Luffa oft erst im August/September (wenn Tage kuerzter werden), was die Zeit fuer Fruchtentwicklung und Schwammreife stark einschraenkt. Fuer Schwammernte unbedingt Gewaechshaus oder Folientunnel verwenden.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate (Waermekeimer; empfindlich beim Verpflanzen; lange Kulturdauer) | `species.propagation_difficulty` |

**Keimhinweise:**
- Samen vor Aussaat 24--48 Stunden in lauwarmem Wasser einweichen (foerdert Keimung)
- Optimale Keimtemperatur: 24--30 degC (Heizmatte empfohlen)
- Keimdauer: 7--14 Tage (nach Einweichen schneller)
- Einzelaussaat in 9-cm-Toepfe oder Jiffy-Toepfe (keine Pikierung)
- Saattiefe: 1.5--2 cm; Samen seitlich legen
- Substrat: Locker, gut drainiert, naehrstoffarm

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (junge Fruechte essbar; reife Fruechte nicht mehr) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaf; seed (Saatgut enthaelt Saponine -- nicht in grossen Mengen essen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Cucurbitacine (Blaetter; Samen); Luffin (Samen -- Ribosom-inhibierendes Protein; nicht direkt giftig bei normaler Exposition) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Trichome auf Blaettern und Stengeln verursachen Hautreizungen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7; 8 | `species.pruning_months` |

**Triebfuehrung:**
- Haupttrieb bis 2--3 m aufleiten; dann entspitzen (foerdert Seitentriebe)
- Seitentriebe tragen weibliche Blueten (Hauptertragstraeger)
- Seitentriebe auf 3--4 Blaetter kuerzen
- Im Gewaechshaus (Mitteleuropa): Bluetentriebe ab August/September maximieren fuer Fruchtansatz

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (moeglich in 15--20 L Behaelter; aber Rank-Konstruktion bis 3 m noetig) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15--30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 35 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 200--600 (rankende Kletterpflanze; braucht Kletterstruktur) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100--300 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60--100 in der Reihe; 150--200 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | no (zu grosse Wuchshoehe; zu wenig Licht; Bestaeubungsprobleme) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Suedbalkon mit starker Rank-Konstruktion; grosse Kuebelanlage) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (in Mitteleuropa zwingend fuer Schwammreife; Kalthaus mind. Mai--Oktober) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Luffa ist aggressiver Kletterer; braucht Drahtgeruest oder Ranknetz 3--5 m hoch) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, lockere, sehr gut drainierte Erde mit hohem Kompostanteil (30%). Sandige Anteile foerdern Drainage. pH 6.5--7.5. | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 7--14 | 1 | false | false | low |
| Saemling (seedling) | 21--35 | 2 | false | false | low |
| Vegetativ (vegetative) | 42--70 | 3 | false | false | medium |
| Bluete (flowering) | 21--35 | 4 | false | true (jung-Gemuese) | medium |
| Fruchtentwicklung (fruit_development) | 30--50 | 5 | false | true (jung-Gemuese) | medium |
| Trocknung/Schwamm-Reife (sponge_ripening) | 21--42 | 6 | true | true (Schwamm) | high |

**Hinweis:** Die Kulturdauer von Aussaat bis Schwamm-Ernte betraegt 150--200 Tage. Fuer die Gemuese-Nutzung (junge Fruechte) ist Ernte bereits ab Fruchtentwicklung nach ca. 80--100 Tagen moeglich.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer; mit Erde bedecken) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--32 (Heizmatte unbedingt noetig!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 22--26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.7 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (feucht; keine Staunaesse) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (lange Tage halten Pflanze in vegetativem Wachstum) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 24--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 (Vollsonne; Luffa ist sehr lichtbeduerftigt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 22--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (lange Tage = rein vegetativ; so lange wie moeglich fuer Biomasse-Aufbau) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 26--35 (optimal 28--32; Waermebedarf sehr hoch!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 20--25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.5 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1200 (Gewaechshaus-CO2-Anreicherung sinnvoll) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--13 (kuerzere Tage loesen Bluete aus -- ab Juli/August in Mitteleuropa automatisch) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Bestaeubungshinweis:** Weibliche Blueten (mit kleiner Frucht am Ansatz) oeffnen sich morgens und sind nur wenige Stunden empfaengnisbereit. Im Gewaechshaus manuelle Bestaeubung oder Hummeln unbedingt noetig.

#### Phase: Fruchtentwicklung (fruit_development)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 18--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 26--35 (hohe Waerme foerdert Faserbildung im Inneren) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--2.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 600--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Schwamm-Reife (sponge_ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10--13 (Herbst; abnehmende Tage okay) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--55 (trocken fuer Schwammtrocknung!) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45--60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.5--2.5 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 7--14 (wenig giessen; Fruechte sollen abtrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Ernte-Indikatoren (Schwamm):**
- Schale braun und trocken; rasselt beim Schuetteln (Samengeraeusch)
- Frucht leicht; Innen-Faser sichtbar wenn man auf die Schale drueckt
- Schale loest sich leicht von Fasergeruest
- Gesamtgewicht der Frucht deutlich reduziert gegenueber gruener Phase
- Bei Kalteinbruch Fruechte ernten und weitertocknen lassen (drinnen)

**Schwamm-Aufbereitung:** Schale in kaltem Wasser einweichen (2--4 h); dann abschaelen; Samen ausspuelen; ggf. bleichen (H2O2 3% fuer 30 min); trocknen. Fertig!

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.5--7.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.8--1.2 | 6.5--7.0 | 80 | 30 | 20 | 2 |
| Vegetativ | 3-1-2 | 1.4--2.2 | 6.5--7.0 | 120 | 50 | 30 | 3 |
| Bluete | 2-2-3 | 1.8--2.6 | 6.5--7.0 | 150 | 60 | 30 | 3 |
| Fruchtentwicklung | 1-2-4 | 2.0--3.0 | 6.5--7.0 | 150 | 60 | 35 | 2 |
| Schwamm-Reife | 0-1-2 | 0.8--1.5 | 6.5--7.0 | 80 | 40 | -- | 1 |

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 7--14 Tage | Keimblaetter entfaltet |
| Saemling -> Vegetativ | manual | 21--35 Tage | 3--4 echte Blaetter; Auspflanzen nach Frost |
| Vegetativ -> Bluete | event_based | -- | Taglaenge < 13 h (automatisch ab Juli/August in Mitteleuropa) |
| Bluete -> Fruchtentwicklung | event_based | -- | Bestaeubung; Fruchtansatz sichtbar |
| Fruchtentwicklung -> Schwamm-Reife | time_based / conditional | 30--50 Tage | Frucht > 30 cm; Schwarz-gelbe Schale |
| Schwamm-Reife -> Ernte | conditional | -- | Schalen-Trocknung und Rasseln |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Gewaechshaus/Topf)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag | Canna | supplement | Ca+Mg | 0.12 | 2 | alle |
| Terra Vega | Canna | base | 3-1-4 | 0.18 | 3 | Vegetativ |
| Terra Flores | Canna | base | 2-2-4 | 0.18 | 3 | Bluete; Frucht |
| PK 13/14 | Canna | booster | 0-13-14 | 0.10 | 5 | Fruchtentwicklung |

#### Organisch (Freiland/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (tief eingraben) | heavy_feeder |
| Hornspäne | Oscorna | organisch (N-Langzeit) | 100--150 g/m2 | Mai (Auspflanzen) | Vegetativphase |
| Brennnesseljauche | Eigenerzeugung | organisch (N) | 1:10, 2 L/Pflanze | Jun--Jul alle 14 Tage | Vegetativ |
| Beinwelljauche | Eigenerzeugung | organisch (K) | 1:10, 2 L/Pflanze | Jul--Sep alle 14 Tage | Bluete; Frucht |
| Tomaten-/Kuerbisduenger | Neudorff / COMPO BIO | organisch | 30--50 ml / 10 L | woechentlich Jul--Sep | heavy_feeder |

### 3.2 Duengungsplan

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base (ml/L) | Booster (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|-------------|----------------|----------|
| 1--2 | Saemling | 0.6--1.0 | 6.5 | 0.2 | 0.4 | -- | Schwache Duengung; nur Keimsubstrat |
| 3--6 | Vegetativ (Vorkultur) | 1.2--1.8 | 6.5 | 0.4 | 0.8 Vega | -- | Aufbau starker Pflanzenmasse |
| 7--12 | Vegetativ (Freiland/GWH) | 1.8--2.2 | 6.5 | 0.5 | 1.0 Vega | -- | Maximale N-Versorgung |
| 13--15 | Bluete | 1.8--2.6 | 6.5 | 0.5 | 0.8 Flores | -- | Auf Flores umstellen |
| 16--20 | Fruchtentw. | 2.0--3.0 | 6.5 | 0.5 | 0.8 Flores | 0.3 PK | Kali-Boost fuer Faserbildung |
| 21--25 | Schwamm-Reife | 0.8--1.5 | 6.5 | 0.2 | 0.4 Flores | -- | Stark reduzieren |

### 3.3 Mischungsreihenfolge

1. Wasser temperieren (22--26 degC; Luffa mag warmes Wasser!)
2. CalMag (VOR Sulfaten!)
3. Base A (Terra Vega oder Flores A)
4. Base B (Terra Flores B)
5. PK-Booster (nur in Fruchtphase)
6. pH-Korrektur (Luffa: pH 6.5--7.5; IMMER zuletzt)

### 3.4 Besondere Hinweise zur Duengung

- **Waerme = Wachstum:** Luffa ist einer der waermebeduerftigen Kulturpflanzen. Unterhalb 20 degC praktisch kein Wachstum; unterhalb 15 degC Stresssymptome. Naehrstoffgaben erst bei ausreichender Waerme wirksam.
- **Ab Bluete Kalium erhoehen:** Kalium foerdert die Faserbildung im Fruchtinneren -- essentiell fuer Schwammqualitaet.
- **Erste 3 Wochen organisch:** In der Anzucht (Keimung bis erste Wochen Saemling) reichen sehr geringe organische Konzentrationen. Zu viele Naehrstoffe in der Fruehphase foerdern Wurzelfaeule.
- **CO2-Anreicherung im GWH:** Luffa reagiert sehr gut auf erhoehte CO2-Konzentrationen (800--1200 ppm) mit stark verbessertem Wachstum -- dies macht die Pflanze interessant fuer professionelle Gewaechshaus-Kultur.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | herb_tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--4 (gleichmaessig feucht; Staunaesse vermeiden) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Warmes Wasser (> 20 degC). Kaltes Wasser stresst die Pflanze stark! Blaetter trockenhalten. Keine Staunaesse. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7--10 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; 1x pikieren, 1x Endtopf) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Aussaat | Samen einweichen (24 h); Einzeltoepfe; Heizmatte 28 degC | hoch |
| Maerz | Vorkultur | In groessere Toepfe umsetzen; Licht 14--16 h; Waerme halten | hoch |
| Apr | Weitertopfen | In 15-L-Toepfe; Rank-Konstruktion vorbereiten | hoch |
| Mai | Auspflanzen | Erst nach Eisheiligen und Bodentemperatur > 20 degC | hoch |
| Jun | Aufleiten | Triebe aufleiten; Haupttrieb nach 2--3 m entspitzen | hoch |
| Jul | Bluete/Bestaeubung | Manuelle Bestaeubung morgens; Hummeln einsetzen | hoch |
| Aug | Fruchtentwicklung | Fruechte am Netz stuetzen (koennen sehr schwer werden!) | hoch |
| Sep | Schwamm-Reife | Giessen reduzieren; Truechte trocknen lassen | hoch |
| Okt | Ernte | Vor Frost: alle Fruechte ernten; auch halbtrockene aufbewahren | hoch |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Gurkenkaefer | Diabrotica spp. | Lochfrass; gelbe-braune Flecken; Virusvektoren | leaf | vegetative; flowering | medium |
| Spinnmilbe | Tetranychus urticae | Gespinste; stippenartige Blaettervergilbung | leaf | vegetative; fruit_development | medium |
| Blattlaeuse | Aphis gossypii | Honigtau; Triebdistortion; Virusvektoren | leaf; shoot | seedling; vegetative | easy |
| Thripse | Frankliniella occidentalis | Silbrige Blattflecken; Bluetenschaeden | flower; leaf | flowering | medium |
| Kuerbiskaefer | Acalymma vittatum | Lochfrass; Blaetter | leaf | vegetative | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Podosphaera xanthii) | Weisser Belag auf Blaettern; Blaetter sterben ab | dry_warm; poor_airflow; shade | 5--10 | vegetative; flowering |
| Falscher Mehltau | oomycete (Pseudoperonospora cubensis) | Gelbliche Flecken; grauer Belag Blattunterseite | cool_wet; high_humidity | 4--8 | vegetative; fruit_development |
| Fusarium-Welke | fungal (Fusarium oxysporum) | Welke; Stengel-Verbräunung; Pflanze stirbt ab | contaminated_soil | 14--28 | vegetative; fruit_development |
| Alternaria-Blattflecken | fungal (Alternaria cucumerina) | Braun-schwarze konzentrische Flecken | warm_wet | 3--7 | vegetative; fruit_development |
| Zucchini-Gelbmosaik-Virus (ZYMV) | viral | Mosaikgelbe Blaetter; Fruchtdeformationen | aphid_vectors | 7--14 | alle |
| Phytophthora-Faeule | oomycete | Stengel- und Wurzelfaeule | waterlogging | 3--7 | seedling; vegetative |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10--20 | 10--14 |
| Aphidoletes aphidimyza | Blattlaeuse | 5--10 | 14--21 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Bombus terrestris | Bestaeubung | 1 Volk / 150--200 m2 | -- |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoelextrakt | biological | Azadirachtin | 0.3--0.5% abends spruehen | 3 | Spinnmilben; Blattlaeuse; Thripse |
| Netzschwefel | chemical | Schwefel | Stauben / Spruehen | 14 | Echter Mehltau |
| Kaliumbicarbonat | approved_organic | Kaliumbicarbonat | 0.5--1.0% spruehen | 0 | Mehltau-Praevention |
| Kupfer-Fungizid | approved_organic | Kupfer | 0.3% spruehen nach Regen | 7 | Falscher Mehltau; Alternaria |
| Tropfbewaesserung | cultural | -- | Blaetter trocknen | 0 | Mehltau-Praevention |
| Belichtungsoptimierung | cultural | -- | Schatten minimieren | 0 | Mehltau-Praevention (Licht kritisch!) |

### 5.5 Resistenzen der Art

<!-- DATEN FEHLEN -- Keine zuverlaessigen Daten zu sortenspezifischen Resistenzen bei Luffa aegyptiaca verfuegbar -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kuerbisgemaechse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Leguminosen (Bohnen; Erbsen); Gruenduengung; Salat |
| Empfohlene Nachfrucht | Feldsalat; Moehren; Zwiebeln (Schwachzehrer) |
| Anbaupause (Jahre) | 3--4 Jahre (Fusarium und Bodenpilze; gleiche Standorte vermeiden) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mais | Zea mays | 0.7 | Windschutz; Kletterhilfe; aehnliche Waermeansprueche | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Ablenkung; Bestaeubungsfoerderung | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeubungsanlocken | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.6 | Thripse-Abwehr; Aromafoerderung | `compatible_with` |
| Buschbohnen | Phaseolus vulgaris | 0.6 | N-Fixierung; Bodenbeschattung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Andere Cucurbitaceae | Cucumis sativus; Cucumis melo; Cucurbita spp. | Gleiche Schaderreger; Mehltau; Blaettlaeuse als Virusvektoren; Bestaeubungskonkurrenz | severe | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gemeinsame Bodenpilze (Fusarium; Phytophthora) | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung durch Fenchel-Exsudate | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Cucurbitaceae | `shares_pest_risk` | Echter Mehltau (Podosphaera xanthii); Falscher Mehltau; ZYMV; Spinnmilben; Gurkenkaefer; Fusarium | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Luffa aegyptiaca |
|-----|-------------------|-------------|-------------------------------------|
| Rippen-Luffa | Luffa acutangula | Gleiche Gattung; aehnliche Kultur | Essbarer (vor allem als Gemuese); kuerzeere Kulturdauer |
| Gurke | Cucumis sativus | Gleiche Familie; Kletterpflanze | Kuerzeere Kulturdauer; weniger Waermebedarf; bekannter im Anbau |
| Zucchini | Cucurbita pepo | Gleiche Familie | Viel einfacher; kuerzere Kulturdauer; kein Spezial-Equipment |

---

## 8. Sorten / Cultivars

| Sorte | Typ | Kulturdauer (Tage) | Fruchtlaenge (cm) | Verwendung | Besonderheiten |
|-------|-----|--------------------|-------------------|-----------|----------------|
| Luffa aegyptiaca Standard | Grundsorte | 150--180 | 30--60 | Schwamm; Gemuese (jung) | Klassischer Anbau; grosse Schwaemme |
| Vietnamese Early | Fruehsorte | 120--140 | 25--40 | Gemuese; Schwamm | Kuerzere Kulturdauer; fuer Mitteleuropa besser geeignet |
| Smooth Luffa (Chinese) | Asiatischer Typ | 130--160 | 30--50 | Gemuese bevorzugt | Zartes Fleisch; haeufig in der asiatischen Kueche |
| Short Luffa | Kompaktsorte | 120--150 | 15--25 | Gemuese und Schwamm | Kompaktere Fruechte; einfachere Handhabung |
| Goa Bean Luffa | Tropischer Typ | 150--180 | 40--70 | Schwamm | Sehr grosser Schwamm; wenig praktisch fuer Mitteleuropa |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity
Luffa aegyptiaca,Schwammgurke;Luffagurke;Luffa;Loofah;Sponge Gourd,Cucurbitaceae,Luffa,annual,short_day,vine,fibrous,7a;7b;8a;8b;9a;9b;10a;10b,-0.1,Tropisches Asien; Nordafrika,limited,15,35,400,200,80,no,limited,true,true,heavy_feeder,tender
```

---

## Quellenverzeichnis

1. [Plantura -- Luffagurke](https://www.plantura.garden/gemuese/gurken/luffagurke) -- Anbau; Pflege; Ernte in Mitteleuropa
2. [fryd.app -- Schwammgurke](https://fryd.app/lexikon/pflanzen/6864-schwammgurke) -- Sorten; Companion Planting
3. [Floraspora -- Luffa-Gurken anbauen](https://www.floraspora.de/post/luffa-gurke-anbauen-pflegen-ernten-verarbeiten-natuerliche-schwaemme) -- Anbauanleitung; Schwammaufbereitung
4. [Freudengarten -- Luffa anbauen](https://freudengarten.de/show/1305/luffa-schwammgurke-anbauen-pflanzen-pflegen) -- Praxis-Tipps; Vorkultur
5. [Lubera -- Luffa selber anbauen](https://www.lubera.com/ch/gartenbuch/luffa-gurken-selber-anbauen-p5196) -- Kultivierung; Ernte
6. [OMAFRA -- Luffa](https://www.omafra.gov.on.ca/CropOp/en/spec_veg/cucurbits/luffa.html) -- Ontario Ministry of Agriculture; Professioneller Anbau
7. [NC State Extension -- Luffa aegyptiaca](https://plants.ces.ncsu.edu/plants/luffa-aegyptiaca/) -- Botanische Grunddaten; Taxonomie
8. [Missouri Botanical Garden -- Luffa aegyptiaca](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=364305) -- Botanische Klassifikation
9. [ForwardPlant -- Luffa aegyptiaca Care Guide](https://www.forwardplant.com/plant-info/luffa-aegyptiaca/) -- Schädlinge; Krankheiten; Pflege
