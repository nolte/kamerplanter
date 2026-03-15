# Paprika -- Capsicum annuum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-03
> **Quellen:** ASPCA, Haifa Group, ICL, Gardenia.net, Plantura, fryd.app, Hortipendium, NCSU Extension, Old Farmer's Almanac, Mein schoener Garten, Gartenjournal

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Capsicum annuum | `species.scientific_name` |
| Volksnamen (DE/EN) | Paprika; Gemuese-Paprika; Peperoni; Bell Pepper; Sweet Pepper; Chili Pepper | `species.common_names` |
| Familie | Solanaceae | `species.family` -> `botanical_families.name` |
| Gattung | Capsicum | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual (in Mitteleuropa; in Tropen kurzlebig perennial) | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (fakultativ; Fruchtansatz nicht streng taglaengenabhaengig, aber kurze Tage koennen Bluete beschleunigen) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, stirbt bei Temperaturen unter 5 degC ab. In Mitteleuropa streng einjaehrig kultiviert (Freiland Juni--Oktober). Vorkultur ab Februar/Maerz zwingend noetig (lange Kulturzeit 120--180 Tage). | `species.hardiness_detail` |
| Heimat | Mittel- und Suedamerika (Mexiko, Guatemala) | `species.native_habitat` |
| Allelopathie-Score | 0.15 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; heat_tolerant | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8--12 (sehr lange Vorkulturzeit, Aussaat ab Mitte Februar) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (Direktsaat in Mitteleuropa nicht praktikabel, Kulturzeit zu lang) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | -- (keine Direktsaat in Mitteleuropa) | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 6; 7; 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate (lange Vorkultur, Waermekeimer, langsame Jugendentwicklung) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 25--28 degC (Heizmatte empfohlen, hohe Waerme kritisch!)
- Minimale Keimtemperatur: 18 degC (sehr langsame, ungleichmaessige Keimung)
- Keimdauer: 10--21 Tage (sortenabhaengig, Cayenne schneller als Gemuese-Paprika)
- **Dunkelkeimer** -- Samen 0.5--1 cm tief mit Erde bedecken
- Hohe Bodenfeuchtigkeit noetig, Substrat gleichmaessig feucht halten
- Substrat: naehrstoffarme Aussaaterde, nach Keimung Temperatur auf 20--22 degC absenken
- Pikieren nach dem 2. echten Blattpaar in 9-cm-Toepfe

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true (ASPCA: Ornamental Pepper -- Solanin + Capsaicin) | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true (Solanin in Blaettern/unreifen Fruechten; Capsaicin reizend) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false (reife Fruechte essbar; Blaetter/unreife Fruechte Solanin-haltig) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaf; stem (Solanin); fruit (unreif: Solanin; scharf: Capsaicin reizt Schleimhaeute) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Solanin (Glykoalkaloid); Capsaicin (bei Scharfsorten) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (gastrointestinale Beschwerden, Schleimhautreizung) | `species.toxicity.severity` |
| Kontaktallergen | true (Capsaicin kann Hautreizung verursachen -- Handschuhe bei scharfen Sorten!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA listet Capsicum annuum (Ornamental Pepper) als giftig fuer Katzen und Hunde. Reife suesse Fruechte sind fuer Menschen unbedenklich. Blaetter und unreife Fruechte enthalten Solanin.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7; 8 | `species.pruning_months` |

Hinweis: Ausgeizen der untersten Triebe bis zur Verzweigungsgabel (Koenigsbluete) foerdert Fruchtgroesse und Luftzirkulation. Bei Gemuese-Paprika: Koenigsbluete ausbrechen fuer staerkere Pflanze. Bei Cayenne: Koenigsbluete stehen lassen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes (Kuebel ab 10 L, sonniger Standort, gut fuer Balkon) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 40--80 (Gemuese-Paprika); 50--100 (Cayenne) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40--50 | `species.spacing_cm` |
| Indoor-Anbau | limited (nur mit starker Zusatzbelichtung > 400 PPFD und langer Kulturzeit moeglich) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (sonniger, windgeschuetzter, warmer Standort; mind. 6 h Sonne) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (optimale Waerme, lange Saison, hoehere Ertraege) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (ab Fruchtansatz Stuetzstab empfohlen, Fruchtgewicht knickt Triebe) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose, durchlaessige Gemuese-/Tomatenerde. pH 6.0--6.8. Drainage am Topfboden (Blaehton). Staunaesse vermeiden. | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 10--21 | 1 | false | false | low |
| Saemling (seedling) | 28--42 | 2 | false | false | low |
| Vegetativ (vegetative) | 35--56 | 3 | false | false | medium |
| Bluete (flowering) | 21--42 | 4 | false | true | medium |
| Ernte (harvest) | 42--84 | 5 | true | true | medium |

Hinweis: Paprika hat eine der laengsten Kulturzeiten im Gemuesesortiment (120--180 Tage Aussaat bis Ernte). Die Bluete- und Erntephase ueberlappen -- die Pflanze blueht und fruchtet gleichzeitig ueber einen langen Zeitraum.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Dunkelkeimer, Abdeckung bis Keimung) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 (dunkel bis Keimung, danach sofort 14--16 h) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--28 (optimal 27) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 22--25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 20--50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 (optimal 400) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 15--25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 (optimal 25) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 100--300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Paprika waechst in der Jugendphase langsam. Temperaturen unter 15 degC fuehren zu Wachstumsstopp und violetter Blattverfaerbung (Phosphormangel-Symptom durch kaeltebedingt eingeschraenkte Aufnahme).

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 (optimal 24--26; ueber 32 degC: Bluetenabwurf!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 17--20 (Nachtabsenkung foerdert Fruchtansatz) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Temperaturen ueber 32 degC und unter 15 degC fuehren zu Bluetenabwurf. Gleichmaessige Wasserversorgung ist kritisch -- Trockenstress verursacht Bluetenendstueckfaeule (Blossom End Rot / BER) durch Calcium-Mangel.

#### Phase: Ernte (harvest)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 17--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--800 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 300--600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Die Erntephase ist bei Paprika lang (6--12 Wochen). Regelmaessiges Ernten foerdert Neuansatz. Gruene Fruechte sind bereits essbar, volle Farbausreifung (rot/gelb/orange) dauert 2--3 Wochen laenger, ergibt aber deutlich hoehere Vitamin-C-Gehalte und mehr Aroma.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.6--1.0 | 5.8--6.2 | 80 | 30 | 25 | 2 |
| Vegetativ | 3-1-2 | 1.4--1.8 | 5.8--6.2 | 120 | 50 | 40 | 3 |
| Bluete | 2-2-3 | 1.8--2.2 | 5.8--6.2 | 150 | 50 | 40 | 3 |
| Ernte | 1-2-3 | 1.8--2.5 | 5.8--6.2 | 180 | 60 | 45 | 3 |

Hinweis: Paprika ist ein Starkzehrer und benoetigt deutlich mehr Naehrstoffe als Basilikum oder Salat. Calcium ist besonders kritisch -- Mangel fuehrt zu Bluetenendstueckfaeule (BER). Kalium wird ab Fruchtansatz erhoet benoetigt (Farbausreifung, Geschmack). pH unter 5.8 foerdert Mikro-Toxizitaet, ueber 6.5 blockiert Eisenaufnahme.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 10--21 Tage | Keimblaetter voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 28--42 Tage | 4--6 echte Blaetter, kraeftiger Stiel, Pflanze 10--15 cm hoch |
| Vegetativ -> Bluete | event_based | 35--56 Tage nach Pikierung | Erste Bluetenknospen sichtbar (Koenigsbluete an der Verzweigungsgabel) |
| Bluete -> Ernte | time_based | 21--42 Tage nach Bluetebeginn | Erste Fruechte in Erntegroesse, regelmaessiger Neuansatz |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Aqua Flores A | Canna | base | 4-0-3 | 0.16 | 3 | Bluete, Ernte |
| Aqua Flores B | Canna | base | 0-4-3 | 0.14 | 4 | Bluete, Ernte |
| PK 13/14 | Canna | booster | 0-13-14 | 0.10 | 5 | Ernte (Fruchtreife) |

#### Organisch (Outdoor/Beet/Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Tomatendunger (fluessig) | COMPO BIO / Neudorff | organisch | 30--50 ml / 10 L Giesswasser | Juni--September, woechentlich | heavy_feeder |
| Reifkompost | Eigenerzeugung | organisch | 4--6 L/m2 | Fruehjahr (Pflanzlochfuellung) | alle |
| Hornspäne (grob) | Oscorna / div. | organisch (N-Langzeit) | 80--120 g/m2 | Fruehjahr (Einarbeitung bei Pflanzung) | heavy_feeder |
| Gesteinsmehl | Oscorna / div. | mineralisch-natuerlich | 100--200 g/m2 | Fruehjahr | alle (Spurenelemente, Kieselsaeure) |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 1 L/Pflanze | Juni--August, alle 14 Tage | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 1 L/Pflanze | Juli--September, alle 14 Tage | heavy_feeder (Kalium fuer Frucht) |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Paprika Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Booster (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------------|----------|
| 1--3 | Saemling | 0.4--0.8 | 5.8--6.0 | 0.3 | 0.4 | 0.4 | -- | Nur Wasser erste 7 Tage nach Keimung |
| 4--6 | Saemling/Veg | 0.8--1.2 | 5.8--6.0 | 0.4 | 0.6 | 0.6 | -- | EC langsam steigern |
| 7--10 | Vegetativ | 1.4--1.8 | 5.8--6.0 | 0.5 | 0.8 | 0.8 | -- | Volle Dosierung, N-betont |
| 11--14 | Bluete | 1.8--2.2 | 5.8--6.0 | 0.5 | 0.8 (Flores A) | 0.8 (Flores B) | -- | Umstellung auf Bluete-Rezeptur |
| 15--20 | Ernte | 1.8--2.5 | 5.8--6.2 | 0.5 | 0.8 (Flores A) | 0.8 (Flores B) | 0.3 PK 13/14 | Kalium-Boost fuer Farbausreifung |
| 21+ | Spaetphase | 1.5--2.0 | 6.0 | 0.4 | 0.6 (Flores A) | 0.6 (Flores B) | -- | EC leicht reduzieren, letzte Fruechte ausreifen |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium)
3. Base A -- z.B. Aqua Vega/Flores A (Calcium + Mikronaehrstoffe)
4. Base B -- z.B. Aqua Vega/Flores B (Phosphor + Schwefel + Magnesium)
5. Booster -- z.B. PK 13/14 (wenn Fruchtphase)
6. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer!** Paprika benoetigt aehnlich viel Naehrstoffe wie Tomate. Unterduengung zeigt sich als helle Blaetter, langsames Wachstum, wenig Fruchtansatz.
- **Calcium kritisch:** Gleichmaessige Calciumversorgung verhindert Bluetenendstueckfaeule (BER). CalMag bei jedem Giessgang. Schwankende Wasserversorgung verstaerkt BER.
- **Kalium ab Frucht:** Ab Fruchtansatz Kalium erhoehen -- foerdert Farbausreifung, Geschmack und Lagerfaehigkeit.
- **Magnesium-Mangel:** Relativ haeufig bei Paprika -- gelbe Blaetter mit gruenen Adern (Interkostal-Chlorose). Bittersalz (Epsom Salt) 0.1% als Blattduengung kann schnell helfen.
- **Organische Topfkultur:** Tomaten-/Paprika-Fluessigduenger woechentlich ab Bluete.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | herb_tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1 (bei Hitze taeglich, im Kuebel ggf. 2x taeglich) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Zimmerwarmes Wasser (18--22 degC). Morgens giessen. Blaetter nicht benetzen. Gleichmaessige Feuchtigkeit kritisch -- Wechsel zwischen trocken und nass verursacht BER und Fruchtplatzer. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7 (woechentlich ab Bluete) | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4; 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; einmal Umtopfen nach Pikierung, dann Endtopf) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Vorkultur starten | Aussaat in Schalen bei 25--28 degC auf Heizmatte, 0.5--1 cm tief, feucht halten | hoch |
| Marz | Pikieren | Saemlinge in Einzeltoepfe (9 cm) nach 2. echtem Blattpaar | hoch |
| Apr | Umtopfen + Abhaerten | In groessere Toepfe (12--14 cm), ab Mitte April langsam abhaerten (tagesueber raus) | hoch |
| Mai | Auspflanzen | Nach Eisheiligen (ca. 15.05.) ins Freiland/auf Balkon, Pflanzabstand 40--50 cm, Stuetzstab setzen | hoch |
| Jun | Ausgeizen + Erste Blueten | Seitentriebe unter Koenigsbluete entfernen, Koenigsbluete bei Gemuesepaprika ausbrechen | hoch |
| Jul | Erntebeginn + Duengung | Erste gruene Fruechte erntereif, woechentlich duengen, gleichmaessig giessen | hoch |
| Aug | Haupternte | Groesste Erntephase, regelmaessig ernten foerdert Neuansatz, auf BER und Sonnenbrand achten | hoch |
| Sep | Nachernte + Farbausreifung | Letzte Fruechte am Strauch ausreifen lassen (rot/gelb), Duengung reduzieren | mittel |
| Okt | Saisonende | Letzte Ernte vor erstem Frost, Pflanzen raeumen und kompostieren | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar -- Paprika wird in Mitteleuropa einjaehrig kultiviert und ueberlebt keine Temperaturen unter 5 degC. Theoretisch mehrjaehrig moeglich bei Ueberwinterung im Haus bei 10--15 degC (hell, wenig giessen, nicht duengen), Rueckschnitt auf 15--20 cm im Oktober. Ertrag im 2. Jahr oft geringer.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaeuse (Aphids) | Myzus persicae, Aphis gossypii | Gekraeuselte Blaetter, Honigtau, Wuchshemmung | leaf, stem | vegetative, flowering | easy |
| Weisse Fliege (Whitefly) | Trialeurodes vaporariorum | Honigtau, weisse Fliegen an Blattunterseite, Russtau | leaf | vegetative, flowering | easy |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Flecken, verkrueppelte Blaetter, Virusuebertraeger | leaf, flower | vegetative, flowering | medium |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, silbrige Punkte auf Blattunterseite | leaf | vegetative, flowering | medium |
| Schnecken (Slugs/Snails) | Arion spp. | Lochfrass an Blaettern und jungen Fruechten | leaf, fruit | seedling, vegetative | easy |
| Trauermucke (Fungus Gnat) | Bradysia spp. | Larven schaedigen Wurzeln, besonders bei Saemlingen | root | seedling | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Bluetenendstueckfaeule (BER) | physiological | Braune, eingesunkene Flecken an der Fruchtspitze | calcium_deficiency, irregular_watering | 7--14 | flowering, harvest |
| Grauschimmel (Botrytis) | fungal | Grauer pelziger Belag auf Fruechten und Staengeln | high_humidity, poor_airflow | 3--7 | flowering, harvest |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser mehliger Belag auf Blattoberseite | dry_warm_conditions, poor_airflow | 5--10 | vegetative, flowering |
| Verticillium-Welke | fungal | Einseitige Blattwelke, Staengel verbräunt | contaminated_soil, cool_wet | 14--28 | vegetative, flowering |
| Tabakmosaikvirus (TMV) | viral | Mosaikartige Blattmusterung, verkrueppelte Fruechte | insect_vectors, mechanical_transmission | 10--21 | alle |
| Damping Off (Umfallkrankheit) | fungal | Saemling knickt an Basis um | overwatering, cold_wet_soil | 2--5 | seedling |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Aphidius colemani (Schlupfwespe) | Blattlaeuse | 2--5 | 14--21 |
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |
| Encarsia formosa | Weisse Fliege | 3--5 | 21--28 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Macrolophus pygmaeus | Weisse Fliege, Blattlaeuse | 2--5 | 28--42 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kaliseife (Schmierseife) | biological | Kaliumsalze der Fettsaeuren | Spruehung 1--2%, alle 5--7 Tage, 3x | 0 | Blattlaeuse, Weisse Fliege, Spinnmilbe |
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Weisse Fliege, Thripse |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau |
| Schneckenkorn (Ferramol) | biological | Eisen-III-Phosphat | Streuen um Pflanzen, 5 g/m2 | 0 | Schnecken |
| Gute Luftzirkulation | cultural | -- | Pflanzabstand 40--50 cm, ausgeizen | 0 | Grauschimmel, Mehltau |
| Gleichmaessig giessen | cultural | -- | Tropfbewaesserung, Mulch | 0 | BER-Praevention |

### 5.5 Resistenzen der Art

Capsicum annuum hat je nach Cultivar unterschiedliche Resistenzniveaus. Wildtyp-Arten haben generell hoehere Toleranz.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Tabakmosaikvirus (TMV/ToMV) | Krankheit | Viele moderne F1-Hybriden (z.B. 'Palermo F1', 'Mavras F1') | `resistant_to` |
| Verticillium dahliae | Krankheit | Einige Cultivare, Veredelung auf Unterlage | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Nachtschattengewaechse (Solanaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) oder Gruenduengung -- Stickstoff-Anreicherung, lockerer Boden |
| Empfohlene Nachfrucht | Mittelzehrer (Moehren, Zwiebeln) oder Schwachzehrer (Salat, Radieschen) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Solanaceae auf gleicher Flaeche (Verticillium, Nematoden, bodenbuertige Viren) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Basilikum | Ocimum basilicum | 0.9 | Weisse-Fliege-Abwehr, aehnliche Standortansprueche, traditionelle Aromafoerderung | `compatible_with` |
| Moehre | Daucus carota | 0.7 | Platzausnutzung (Tiefwurzler + Flachwurzler), Bodenbeschattung | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes patula | 0.8 | Nematoden-Abwehr, Bestauber anlocken, Blattlaus-Abwehr | `compatible_with` |
| Schnittlauch / Zwiebel | Allium spp. | 0.7 | Pilzabwehr, Blattlaus-Abwehr | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Bodenbeschattung, schnelle Ernte, gute Raumausnutzung | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Unterpflanzung, Bodenbeschattung, schnelle Ernte | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.7 | Nuetzlingsanreicherung, Bodenbeschattung | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung, hemmt Wachstum von Paprika | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gleiche Familie (Solanaceae) -- gemeinsame Krankheiten (Krautfaeule, Verticillium), Naehrstoffkonkurrenz | severe | `incompatible_with` |
| Tomate | Solanum lycopersicum | Gleiche Familie -- theoretisch gemeinsame Krankheiten; in der Praxis aber haeufig zusammen kultiviert (Gewaechshaus) | mild | `incompatible_with` |
| Gurke | Cucumis sativus | Unterschiedliche Feuchtigkeitsbeduerfnisse (Gurke = sehr feucht, Paprika = maessig) | mild | `incompatible_with` |
| Dill | Anethum graveolens | Kann Paprikawachstum hemmen | mild | `incompatible_with` |
| Kohlrabi / Brassicaceae | Brassica oleracea | Hoher Naehrstoffbedarf beider Parteien, Platzkonkurrenz | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Solanaceae (mit sich selbst) | `shares_pest_risk` | Verticillium, Kraut-/Braunfaeule, TMV, Nematoden, Weisse Fliege | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Standard-Paprika |
|-----|-------------------|-------------|------------------------------|
| Chili (Cayenne-Typ) | Capsicum annuum var. acuminatum | Gleiche Art, scharf | Kompakter, hoehere Hitzetoleranz, laengere Haltbarkeit |
| Habanero | Capsicum chinense | Gleiche Gattung, sehr scharf | Tropisch-fruchtig, sehr hoher Capsaicin-Gehalt |
| Jalapeño | Capsicum annuum 'Jalapeño' | Gleiche Art | Kompakt, frueh reif, gut fuer Kuebel |
| Mini-Paprika / Snackpaprika | Capsicum annuum (div. Cultivare) | Gleiche Art | Kompakter, fruehr reif, ideal fuer Balkon |
| Aubergine | Solanum melongena | Gleiche Familie (Solanaceae) | Aehnliche Kultur, waermeliebend, dekorative Fruechte |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Capsicum annuum,Paprika;Gemuese-Paprika;Peperoni;Bell Pepper;Sweet Pepper;Chili Pepper,Solanaceae,Capsicum,annual,day_neutral,herb,fibrous,9a;9b;10a;10b;11a;11b,0.15,"Mittel- und Suedamerika (Mexiko, Guatemala)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Gemuese-Paprika (Blockpaprika),Capsicum annuum,,,high_yield;compact,120,,open_pollinated
Cayenne-Paprika,Capsicum annuum,,,heat_tolerant;long_season,90,,open_pollinated
Yolo Wonder,Capsicum annuum,,1952,high_yield;disease_resistant,75,tmv,open_pollinated
California Wonder,Capsicum annuum,,,high_yield;heirloom,75,,open_pollinated
Hungarian Wax,Capsicum annuum,,,heat_tolerant;early_maturing,65,,open_pollinated
Palermo F1,Capsicum annuum,Enza Zaden,,high_yield;disease_resistant,85,tmv;tobamovirus,f1_hybrid
Snackpaprika (Mini),Capsicum annuum,,,compact;high_yield;early_maturing,60,,f1_hybrid
```

---

## Quellenverzeichnis

1. ASPCA -- Ornamental Pepper (Capsicum annuum): https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/ornamental-pepper
2. Haifa Group -- Pepper Crop Guide: https://www.haifa-group.com/sites/default/files/guide/Pepper_0.pdf
3. ICL Growing Solutions -- Pepper Nutrition: https://icl-growingsolutions.com/agriculture/crops/pepper/
4. Gardenia.net -- Capsicum annuum: https://www.gardenia.net/plant/capsicum-annuum
5. Plantura -- Pepper Companion Planting: https://plantura.garden/uk/vegetables/peppers/pepper-companion-planting
6. fryd.app -- Companion Plants for Chilies & Peppers: https://fryd.app/en/magazine/companion-planting-chili-peppers
7. MechaGrow -- Typical PPFD/DLI values per crop: https://www.horti-growlight.com/en/typical-ppfd-and-dli-values-per-crop
8. Mars Hydro -- PPFD for Indoor Plants: https://www.mars-hydro.com/info/post/how-much-ppfd-for-indoor-plants-in-each-growth-stage
9. NCSU Extension -- Capsicum annuum: https://plants.ces.ncsu.edu/plants/capsicum-annuum/
10. Old Farmer's Almanac -- Peppers: https://www.almanac.com/plant/peppers
