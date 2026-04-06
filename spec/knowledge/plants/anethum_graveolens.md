# Dill -- Anethum graveolens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, NCSU Extension, USU Extension, Gardenia.net, Plantura, fryd.app, Old Farmer's Almanac, Harvest to Table, DeepGreen Permaculture, Gardening Know How

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Anethum graveolens | `species.scientific_name` |
| Volksnamen (DE/EN) | Dill; Gewoehnlicher Dill; Gurkenkraut; Dill Weed | `species.common_names` |
| Familie | Apiaceae | `species.family` -> `botanical_families.name` |
| Gattung | Anethum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Langtagspflanze -- laengere Tage foerdern Bluetenbildung/Schossen; kurze Tage verzoegern Bluete und verlaengern die vegetative Erntephase) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a; 2b; 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Jungpflanzen vertragen leichte Froeste bis -3 degC. Saat ab April direkt ins Freiland moeglich. Bei starkem Frost (unter -5 degC) sterben die Pflanzen ab. Selbstaussaat moeglich -- ueberwintert als Samen im Boden. | `species.hardiness_detail` |
| Heimat | Suedwestasien, Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | 0.2 (leichte wachstumshemmende Wirkung auf einige Nachbarn wie Basilikum, Paprika) | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | -- (Direktsaat bevorzugt; Dill vertraegt kein Verpflanzen gut wegen Pfahlwurzel) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (kann bereits 2--4 Wochen VOR letztem Frost gesaet werden, ab Bodentemperatur 8 degC) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4; 5; 6; 7 (Staffelsaat alle 3--4 Wochen fuer kontinuierliche Ernte) | `species.direct_sow_months` |
| Erntemonate | 5; 6; 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8; 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy (unkomplizierte Direktsaat, keimt zuverlaessig, saeht sich leicht selbst aus) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 15--21 degC
- Minimale Keimtemperatur: 8 degC
- Keimdauer: 7--14 Tage
- **Lichtkeimer** -- Samen nur leicht andruecken oder duenn (max. 0.5 cm) mit feinem Sand bedecken
- Saattiefe: 0.5--1 cm
- Reihenabstand: 25--30 cm
- In der Reihe: 15--20 cm (nach Vereinzeln)
- Dill hat eine empfindliche Pfahlwurzel -- NICHT pikieren oder umtopfen
- Staffelsaat alle 3--4 Wochen fuer kontinuierliche Ernte (Dill schosst schnell!)

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- (keine) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- (keine; aetherische Oele Carvon + Limonen in normalen Mengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Furanocumarine im Pflanzensaft koennen bei empfindlichen Personen + Sonnenlicht phototoxische Reaktionen ausloesen -- Apiaceae-typisch) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzallergie mit Beifuss/Sellerie -- Sellerie-Beifuss-Gewuerz-Syndrom; selten) | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Anethum graveolens als ungiftig fuer Katzen und Hunde. Achtung: Verwechslung mit giftigen Doldenblutlern (Schierling, Hundspetersilie) bei Wildsammlung moeglich!

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7; 8; 9 | `species.pruning_months` |

Hinweis: Regelmaessiges Ernten der Blattspitzen verzoegert das Schossen (Bluetenbildung). Sobald der zentrale Bluetenstaengel erscheint, werden die Blaetter derber und weniger aromatisch. Fuer Dillblatt-Ernte: Staendig neue Saetze nachsaeen. Fuer Dillsamen-Ernte: Blueten stehen lassen bis Samen braun und trocken.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (flache Pfahlwurzel, schosst schnell; nur kompakte Sorten wie 'Bouquet' oder 'Fernleaf' empfohlen, Topf mind. 20 cm tief) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5--10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 60--120 (sortenabhaengig; Zwerg-Dill 'Fernleaf' 30--45 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20--30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 15--20 in der Reihe, 25--30 Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | limited (benoetigt viel Licht, schosst indoor noch schneller; nur mit starker Belichtung) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Wind knickt hohe Sorten leicht; windgeschuetzter Standort, Zwerg-Sorten bevorzugen) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freiland optimal; Gewaechshaus zu warm, schosst noch schneller) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (hohe Sorten 80--120 cm brauchen Stuetzstab oder windgeschuetzten Standort) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlaessige, humusreiche, leicht sandige Erde. Nicht zu naehrstoffreich. pH 5.5--6.5. Gute Drainage. | -- |

**Hinweis:** Dill schosst (geht in Bluete) bei Hitze, Trockenheit und langen Tagen sehr schnell. Fuer Blatternten: Staffelsaat alle 3--4 Wochen und kuehlen, halbschattigen Standort waehlen. Fuer Samen/Doldenernten: Sonniger Standort, Schossen erwuenscht.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 7--14 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--42 | 3 | false | true | medium |
| Bluete (flowering) | 14--28 | 4 | false | true (Dillsamen) | medium |
| Seneszenz (senescence) | 7--14 | 5 | true | true (Samenreife) | low |

Hinweis: Die vegetative Phase ist die produktivste fuer Blatternten (Dillkraut). Dill hat eine kurze Gesamtkulturzeit (60--90 Tage) und neigt stark zum Schossen. Durch konsequentes Ernten der Triebspitzen und Staffelsaat kann die Versorgung ueber die gesamte Saison sichergestellt werden.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50--100 (Lichtkeimer!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3--6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (12--16 h im Fruehjahr) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--21 (optimal 18) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70--85 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 (gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich / 100--200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 15--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich / 200--400 (optimal 250; volle Sonne bis Halbschatten) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 (kuerzere Tage verzoegern Schossen) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--25 (optimal 20--22; ueber 30 degC: beschleunigtes Schossen!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 12--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--4 (maessig feucht, keine Staunaesse) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Dill vertraegt Halbschatten -- halbschattige Standorte verzoegern sogar das Schossen und verlaengern die Blatterntezeit. Staunaesse foerdert Wurzelfaeule. Nicht zu naehrstoffreich kultivieren -- ueberduengter Dill schmeckt fad.

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich / 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (Langtag foerdert Bluete) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.3 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (reduziert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--60 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Dillblueten sind wichtige Nuetzlings-Anlocker (Schwebfliegen, Schlupfwespen, Marienkaefer). Im Mischkulturbeet deshalb einige Pflanzen bluehen lassen. Dillsamen (Dillfruchte) koennen geerntet werden, wenn sie braun und trocken sind (August/September).

#### Phase: Seneszenz (senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -- (natuerlich, Spaetsommer/Herbst) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -- | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 5--7 (stark reduziert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Samen von trockenen Dolden sammeln, Pflanze danach entfernen. Dill saeht sich bereitwillig selbst aus -- wenn unerwuenscht, Samendolden vor der Reife entfernen.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 5.5--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.3--0.6 | 5.8--6.5 | 50 | 25 | 15 | 2 |
| Vegetativ | 2-1-2 | 0.6--1.0 | 5.8--6.5 | 80 | 35 | 25 | 2 |
| Bluete | 1-1-2 | 0.6--0.8 | 5.8--6.5 | 60 | 30 | 20 | 2 |
| Seneszenz | 0-0-0 | 0.0 | 6.0 | -- | -- | -- | -- |

Hinweis: Dill ist ein Schwachzehrer -- wenig Duenger genuegt. Ueberduengung (besonders Stickstoff) verursacht weiches, geschmacksloses Kraut mit reduziertem Aromaoel-Gehalt. EC ueber 1.2 mS vermeiden.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 7--14 Tage | Keimblaetter voll entfaltet |
| Saemling -> Vegetativ | time_based | 14--21 Tage | 3--4 echte, gefiederte Blaetter, Pflanze 5--8 cm hoch |
| Vegetativ -> Bluete | time_based / event_based | 21--42 Tage (Langtagreaktion -- laenger werdende Tage im Sommer + Waerme beschleunigen Bluete) | Zentraler Bluetenstaengel beginnt zu strecken, Doldenansatz sichtbar |
| Bluete -> Seneszenz | time_based | 14--28 Tage nach Bluetebeginn | Samen reifen (braun, trocken), Blaetter vergilben |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Flora Micro | General Hydroponics | base | 5-0-1 | 0.15 | 3 | alle |
| Flora Gro | General Hydroponics | base | 2-1-6 | 0.12 | 4 | Vegetativ |

Hinweis: Fuer Dill reichen 1/3 bis 1/2 der Standarddosis fuer Starkzehrer.

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 2--3 L/m2 | Fruehjahr (Einarbeitung vor Saat) | light_feeder |
| Bio Kraeuterdunger (fluessig) | COMPO BIO | organisch | 10--15 ml / 10 L Giesswasser | Mai--August, alle 3--4 Wochen | light_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:20 verduennt, 0.5 L/m2 | Juni--Juli, max. 2x | light_feeder |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Dill Standard Freiland")

| Zeitpunkt | Phase | Massnahme | Hinweise |
|-----------|-------|-----------|----------|
| Vor Saat (April) | Vorbereitung | 2--3 L/m2 Kompost einarbeiten | Keine weitere Grundduengung noetig |
| 4 Wochen nach Saat | Saemling/Veg | ggf. 1x Bio-Kraeuterdunger | Nur bei sichtbarem Naehrstoffmangel |
| Ab Juni | Vegetativ | Schachtelhalmbruehe alle 14 Tage | Praevention Mehltau |
| Ab Bluete | Bluete | Keine Duengung | Aromagehalt soll hoch bleiben |

### 3.3 Mischungsreihenfolge

Bei der seltenen Hydrokultur-Variante:

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag (falls noetig)
3. Basis A (Calcium + Mikronaehrstoffe)
4. Basis B (Phosphor + Schwefel + Magnesium)
5. pH-Korrektur -- IMMER als letzter Schritt

### 3.4 Besondere Hinweise zur Duengung

- **Schwachzehrer!** Dill benoetigt kaum Duengung. Gut mit Kompost versorgter Boden reicht fuer die gesamte Kulturzeit.
- **Stickstoff minimal:** Zu viel N foerdert weiches, geschmacksloses Kraut und beschleunigt das Schossen.
- **Kalium-betont:** Wenn ueberhaupt geduengt wird, dann kalibetont (foerdert Aromaoel-Produktion und Standfestigkeit).
- **pH 5.5--6.5:** Dill bevorzugt leicht saure bis neutrale Boeden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | top_water | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Maessig giessen, Staunaesse vermeiden. Dill vertraegt kurze Trockenheit besser als zu viel Naesse (Wurzelfaeule). Nicht ueber das Kraut giessen (Mehltau-Gefahr). | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | -- (Grundduengung mit Kompost genuegt; max. 1x fluessig nachduengen) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4; 5; 6 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (Direktsaat, kein Umtopfen wegen Pfahlwurzel) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Apr | Erste Aussaat | Direktsaat ab Bodentemperatur 8 degC, Reihenabstand 25 cm | hoch |
| Mai | Vereinzeln + Zweite Saat | Auf 15--20 cm vereinzeln, Staffelsaat fuer kontinuierliche Ernte | hoch |
| Jun | Erntebeginn + Dritte Saat | Blatternten beginnen (Triebspitzen ernten), Staffelsaat | hoch |
| Jul | Haupternte + Nuetzlinge | Regelmaessig Blattspitzen ernten, einige Pflanzen bluehen lassen (Nuetzlingsanziehung) | hoch |
| Aug | Ernte + Samenernte | Letzte Blatternten, reife Dillsamen von trockenen Dolden ernten | mittel |
| Sep | Samenreife + Saisonende | Restliche Samen sammeln, Pflanzen entfernen oder fuer Selbstaussaat stehen lassen | niedrig |
| Okt | Aufraumen | Abgestorbene Pflanzen kompostieren | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar -- Dill ist eine einjaehrige Pflanze. Saeht sich jedoch bereitwillig selbst aus und erscheint im naechsten Fruehjahr von alleine. Samen koennen bei Raumtemperatur trocken gelagert werden (Keimfaehigkeit 2--3 Jahre).

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaeuse (Aphids) | Myzus persicae, Cavariella aegopodii | Gekraeuselte Blaetter, Honigtau, Virusuebertraeger (Carrot Motley Dwarf) | leaf, stem | vegetative | easy |
| Schwalbenschwanzraupe (Swallowtail Caterpillar) | Papilio machaon | Frass an Blaettern und Staengeln, auffaellig schwarz-gruen-gelb gestreift | leaf | vegetative, flowering | easy |
| Raupen (Armyworm, Cutworm) | Spodoptera spp., Agrotis spp. | Blattfrass, abgebissene Staengel | leaf, stem | seedling, vegetative | medium |
| Moehrenfliege (Carrot Fly) | Psila rosae | Fraessgaenge in der Wurzel (selten bei Dill, haeufiger bei Moehren) | root | vegetative | medium |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, silbrige Punkte auf Blattunterseite | leaf | vegetative | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau (Downy Mildew) | fungal | Gelbe Flecken auf Blattoberseite, weisser Belag auf Blattunterseite | high_humidity, cool_nights, poor_airflow | 5--10 | vegetative |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser mehliger Belag auf Blaettern und Staengeln | dry_warm, poor_airflow | 7--14 | vegetative, flowering |
| Cercospora-Blattflecken | fungal | Braune nekrotische Flecken mit Halo | high_humidity | 5--10 | vegetative |
| Carrot Motley Dwarf (Viruskomplex) | viral | Gelb-rote Blattverfaerbung, Zwergwuchs | aphid_transmission | 14--28 | vegetative |
| Wurzelfaeule (Root Rot) | fungal | Pflanze welkt trotz feuchtem Boden, Wurzel braun/weich | overwatering, heavy_soil | 7--14 | alle |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5--10 | 14 |
| Coccinella septempunctata (Marienkaefer) | Blattlaeuse | 5--10 | 7--14 |
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |

Hinweis: Dill ist selbst ein hervorragender Nuetzlingsanlocker! Bluehender Dill zieht Schwebfliegen, Schlupfwespen und Marienkaefer an -- daher im Mischkulturbeet immer einige Pflanzen bluehen lassen.

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage | 0 | Blattlaeuse, Spinnmilbe |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse |
| Bacillus thuringiensis (Bt) | biological | Bt-Toxin | Spruehung nach Herstellerangabe | 0 | Raupen |
| Schachtelhalmbruehe | cultural | Kieselsaeure | Blattspruehung 1:5, alle 14 Tage | 0 | Mehltau-Praevention |
| Gute Luftzirkulation | cultural | -- | Pflanzabstand einhalten, nicht zu dicht | 0 | Mehltau, Grauschimmel |
| Befallene Blaetter entfernen | cultural | -- | Sofort entfernen, Restmuell | 0 | Cercospora, Mehltau |

### 5.5 Resistenzen der Art

Dill hat generell wenig natuerliche Resistenzen. Die Hauptstrategie ist schnelle Kulturzeit und Staffelsaat.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Schossen-Toleranz | Eigenschaft | Sorten wie 'Fernleaf', 'Dukat', 'Hera' (langsamer schossend) | -- |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Doldenblutler (Apiaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kohl, Tomate) oder Huelsenfruechte |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Radieschen) oder Gruenduengung |
| Anbaupause (Jahre) | 3--4 Jahre fuer Apiaceae (Moehre, Sellerie, Petersilie, Fenchel) auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Gurke | Cucumis sativus | 0.9 | Klassische Mischkultur! Dill zieht Bestauber und Nuetzlinge an, foerdert Gurkenertrag | `compatible_with` |
| Kohl (alle Brassicaceae) | Brassica oleracea | 0.8 | Dill vertreibt Kohlweisslingsraupen und Kohlmotten | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Gute Raumausnutzung, Dill vertreibt Blattlaeuse | `compatible_with` |
| Zwiebel | Allium cepa | 0.7 | Gegenseitige Schaedlingsabwehr | `compatible_with` |
| Erbse | Pisum sativum | 0.7 | N-Fixierung, Dill lockt Nuetzlinge an | `compatible_with` |
| Bohne | Phaseolus vulgaris | 0.7 | N-Fixierung, Dill lockt Nuetzlinge an | `compatible_with` |
| Sonnenblume | Helianthus annuus | 0.7 | Windschutz fuer hohen Dill, Bestauber anlocken | `compatible_with` |
| Mais | Zea mays | 0.7 | Stuetzfunktion, Windschutz | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Moehre | Daucus carota | Gleiche Familie -- Kreuzbestaeubung moeglich (bitter schmeckende Moehrensamen), gemeinsame Schaedlinge (Moehrenfliege) | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Gleiche Familie + Kreuzbestaeubung + allelopathische Hemmung | severe | `incompatible_with` |
| Basilikum | Ocimum basilicum | Unterschiedliche Wasserbeduerfnisse (Dill = maessig/trocken, Basilikum = feucht); Dill beschattet Basilikum durch schnelles Hoehenwachstum | mild | `incompatible_with` |
| Paprika | Capsicum annuum | Dill kann Paprikawachstum hemmen (leichte allelopathische Wirkung) | mild | `incompatible_with` |
| Tomate | Solanum lycopersicum | Umstritten: junge Dillpflanzen foerdern Tomaten, reifer/bluehender Dill hemmt sie | mild | `incompatible_with` |
| Lavendel | Lavandula angustifolia | Gegensaetzliche Wasserbeduerfnisse (Lavendel = trocken/mager) | mild | `incompatible_with` |
| Petersilie | Petroselinum crispum | Gleiche Familie (Apiaceae) -- gemeinsame Schaedlinge (Moehrenfliege), Naehrstoffkonkurrenz | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Apiaceae (mit sich selbst) | `shares_pest_risk` | Moehrenfliege, Alternaria, Cercospora, Carrot Motley Dwarf | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Standard-Dill |
|-----|-------------------|-------------|------------------------------|
| Fenchel (Krautfenchel) | Foeniculum vulgare var. dulce | Gleiche Familie, aehnliche Verwendung | Mehrjaehrig, staerkeres Anis-Aroma, robuster |
| Kerbel | Anthriscus cerefolium | Gleiche Familie, Kuechenkraut | Schattenverlraeglicher, elegantes Aroma |
| Koriander | Coriandrum sativum | Gleiche Familie, Kuechenkraut | Andere Geschmacksrichtung, aehnliche Kultur |
| Thai-Basilikum | Ocimum basilicum var. thyrsiflora | Anderes Aroma, aehnliche Verwendung | Waermeliebender, Anis-Aroma wie Dill |
| Zwerg-Dill 'Fernleaf' | Anethum graveolens 'Fernleaf' | Gleiche Art, kompakt | Langsamer schossend, ideal fuer Topf/Balkon |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Anethum graveolens,Dill;Gewoehnlicher Dill;Gurkenkraut;Dill Weed,Apiaceae,Anethum,annual,long_day,herb,taproot,2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b,0.2,"Suedwestasien, Mittelmeerraum"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Tetra-Dill,Anethum graveolens,,,high_yield;heirloom,55,,open_pollinated
Fernleaf,Anethum graveolens,,1992,compact;early_maturing,45,,open_pollinated
Dukat (Dill),Anethum graveolens,,,high_yield;long_season,50,,open_pollinated
Mammut,Anethum graveolens,,,high_yield;long_season,65,,open_pollinated
Hera,Anethum graveolens,,,long_season,55,,open_pollinated
Bouquet,Anethum graveolens,,,compact;early_maturing,45,,open_pollinated
```

---

## Quellenverzeichnis

1. ASPCA -- Dill (Anethum graveolens): https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dill
2. NCSU Extension -- Anethum graveolens: https://plants.ces.ncsu.edu/plants/anethum-graveolens/
3. USU Extension -- Dill in the Garden: https://extension.usu.edu/yardandgarden/research/dill-in-the-garden
4. Gardenia.net -- Anethum graveolens: https://www.gardenia.net/plant/anethum-graveolens
5. Old Farmer's Almanac -- Dill: https://www.almanac.com/plant/dill
6. Harvest to Table -- How to Plant, Grow, and Harvest Dill: https://harvesttotable.com/how_to_grow_dill/
7. DeepGreen Permaculture -- Dill Growing Guide: https://deepgreenpermaculture.com/2025/04/02/dill-growing-guide/
8. Gardening Know How -- Dill Plant Diseases: https://www.gardeningknowhow.com/edible/herbs/dill/dill-plant-diseases.htm
9. Green Garden Guide -- Top Companion Plants for Dill: https://greengardenguide.com/top-companion-plants-for-dill-boosting-growth-and-flavor/
10. La Ferme de Sainte Marthe -- Growing Dill: https://www.fermedesaintemarthe.com/en/blogs/comment-reussir-la-culture-de/reussir-la-culture-de-laneth
