# Tomate -- Solanum lycopersicum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-01
> **Quellen:** PFAF, RHS, UMN Extension, Ohio State University, Plantura, Koppert, fryd.app, LfL Bayern, ASPCA, COMPO Expert

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Solanum lycopersicum | `species.scientific_name` |
| Volksnamen (DE/EN) | Tomate; Tomato; Paradeiser | `species.common_names` |
| Familie | Solanaceae | `species.family` -> `botanical_families.name` |
| Gattung | Solanum | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a; 9b; 10a; 10b; 11a; 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, wird in Mitteleuropa als Einjaehrige kultiviert. Abstirben bei Temperaturen unter 0 degC. | `species.hardiness_detail` |
| Heimat | Suedamerika, westliche Anden (Peru, Ecuador) | `species.native_habitat` |
| Allelopathie-Score | -0.2 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (keine Direktsaat empfohlen, zu lange Kulturdauer) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | -- (nur Vorkultur sinnvoll) | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9; 10 | `species.harvest_months` |
| Bluetemonate | 5; 6; 7; 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem; grafting | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

Hinweis: Stecklingsvermehrung (Geiztriebe in Wasser bewurzeln) ist sehr einfach und ermoeglicht eine Vervielfaeltigung waehrend der Saison. Veredelung (Grafting) auf robuste Unterlagen (z.B. *Solanum lycopersicum* x *S. habrochaites*) verbessert Krankheitsresistenz und Ertrag.

**Keimhinweise:**
- Optimale Keimtemperatur: 22--25 degC (Heizmatte empfohlen)
- Minimale Keimtemperatur: 14 degC (sehr langsame Keimung)
- Maximale Keimtemperatur: 35 degC (Keimrate sinkt ab 30 degC)
- Keimdauer: 5--10 Tage
- Saattiefe: 0.5--1 cm (lichtunabhaengige Keimung; Abdeckung aus praktischen Gruenden empfohlen, biologisch aber nicht zwingend)
- Vorkultur ist Standard -- Direktsaat in Mitteleuropa nicht praktikabel (zu lange Kulturdauer)
- Substrat: naehrstoffarme Aussaaterde, gleichmaessig feucht, nie nass

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | true (gruene Pflanzenteile und Blaetter; reife Fruechte unbedenklich) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves; stems; unripe_fruits | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | alpha-tomatin; solanin (Spuren) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Kontaktdermatitis durch Blatttrichome moeglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

Quelle: ASPCA Animal Poison Control. Reife Fruechte sind ungiftig. Blaetter und gruene Fruechte enthalten alpha-Tomatin (Glykoalkaloid), das bei Katzen und Hunden gastrointestinale Beschwerden ausloesen kann. Solanin kommt nur in Spuren vor (primaer ein Kartoffelalkaloid).

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 5; 6; 7; 8; 9 | `species.pruning_months` |

Hinweis: Bei indeterminierten (Stab-)Tomaten ist regelmaessiges Ausgeizen (Entfernung der Seitentriebe aus den Blattachseln) waehrend der gesamten Vegetationsperiode essenziell. Determinierte (Busch-)Tomaten werden nicht ausgegeizt.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (determinierte/Busch-Sorten gut, indeterminierte/Stab-Sorten eingeschraenkt) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--20 (min. 10 L fuer Determinate, 15--20 L fuer Indeterminate) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 50--200 (sortenabhaengig: Buschtomaten 50--80, Stabtomaten 150--200) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40--60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50--80 | `species.spacing_cm` |
| Indoor-Anbau | limited (nur Gewaechshaus oder kuenstliche Belichtung -- Lichtbedarf sehr hoch, min. 600 PPFD) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Balkontomaten/determinierte Sorten; volle Sonne erforderlich, Regen- und Windschutz empfohlen) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (optimale Kulturbedingungen, Schutz vor Braunfaeule) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (Stabtomate: Spiralstab oder Schnur; Buschtomate: bei Fruchtlast Stuetze empfohlen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose Pflanzerde (Tomatenerde) mit gutem Wasserhaltvermoegens. Drainage am Topfboden wichtig. | -- |

**Hinweis:** Tomaten sind Starkzehrer und benoetigen in Topfkultur regelmaessige Duengung und gleichmaessige Wasserversorgung. Ungleichmaessiges Giessen fuehrt zu Bluetenendfaeule (BER) und Platzfruechten. Selbstbewurzelte Tomaten im Kuebel sind anfaelliger fuer Welkekrankheiten als im Freiland -- Gewaechshaus bietet beste Ergebnisse.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--10 | 1 | false | false | low |
| Saemling (seedling) | 14--28 | 2 | false | false | low |
| Vegetativ (vegetative) | 28--42 | 3 | false | false | medium |
| Bluete (flowering) | 21--35 | 4 | false | false | medium |
| Fruchtreife (ripening) | 30--60 | 5 | false | true | high |
| Seneszenz (senescence) | 14--21 | 6 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0--50 (lichtunabhaengige Keimung; ab Keimblaetter 100--150) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0, dann 5--8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0, dann 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 (optimal 25) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4--0.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung genuegt) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (Substrat gleichmaessig feucht halten) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 20--25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65--75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70--80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 20--30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 800--1200 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 25--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.5 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 800--1200 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Temperaturen ueber 32 degC Tag bzw. ueber 25 degC Nacht verursachen Bluetenabwurf (Pollensterilitaet). Ruetteln/Vibrieren der Bluetenstaende (z.B. elektrische Zahnbuerste) verbessert die Bestaeubung unter Glas.

#### Phase: Fruchtreife (ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 25--35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.9--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 1000--2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Tagtemperatur-Differenz (DIF) von 6--8 degC zwischen Tag und Nacht foerdert die Fruchtfaerbung ueber Lycopin-Synthese. Ueber 30 degC wird die Lycopin-Synthese gehemmt (Fruechte bleiben gelb/orange).

#### Phase: Seneszenz (senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | natuerlich | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | -- | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natuerlich (10--12, Herbst) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | -- (natuerlich, Herbst) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | -- | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | -- | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | -- | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | -- | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Umgebung) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 (reduziert) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--500 (stark reduziert) | `requirement_profiles.irrigation_volume_ml_per_plant` |

Hinweis: Pflanze wird nicht mehr aktiv gepflegt. Letzte gruene Fruechte ernten und drinnen nachreifen lassen. Pflanze nach letzter Ernte entfernen, nicht kompostieren bei Krankheitsbefall (Phytophthora, Fusarium). Bewaesserung nur noch minimal, um letzte Fruechte auszureifen.

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.5--0.8 | 5.8--6.2 | 80 | 40 | 30 | 2 |
| Vegetativ | 3-1-2 | 1.2--1.8 | 5.8--6.2 | 150 | 50 | 50 | 3 |
| Bluete | 2-3-3 | 1.6--2.2 | 5.8--6.5 | 180 | 60 | 60 | 3 |
| Fruchtreife | 1-2-4 | 1.8--2.5 | 6.0--6.5 | 200 | 60 | 50 | 2 |
| Seneszenz | 0-0-0 | 0.0--0.4 | 6.0--6.5 | -- | -- | -- | -- |

Hinweis: Ca-Mangel in der Fruchtphase fuehrt zu Bluetenendfaeule (Blossom End Rot, BER). Erhoehter Kalium-Bedarf ab Fruchtbildung fuer Geschmack und Fruchtfestigkeit.

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--10 Tage | Keimblaetter (Kotyledonen) voll entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--28 Tage | 2--4 echte Blattpaare, Pikieren abgeschlossen |
| Vegetativ -> Bluete | gdd_based | GDD ~200--450 (Basis 10 degC, sortenabhaengig) / 28--42 Tage | Erste Bluetenstaende sichtbar |
| Bluete -> Fruchtreife | event_based | 21--35 Tage nach Bluetebeginn | Erste Fruechte gebildet (Fruchtansatz sichtbar) |
| Fruchtreife -> Seneszenz | time_based | 30--60 Tage | Letzte Ernte durchgefuehrt, Pflanze erschoepft |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Hydro/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag Agent | Canna | supplement | 3.2-0-0 (+Ca 5.1%, Mg 1.5%) | 0.12 | 2 | alle |
| Aqua Vega A | Canna | base | 5-0-3 | 0.18 | 3 | Saemling, Vegetativ |
| Aqua Vega B | Canna | base | 0-4-2 | 0.14 | 4 | Saemling, Vegetativ |
| Aqua Flores A | Canna | base | 4-0-3 | 0.16 | 3 | Bluete, Frucht |
| Aqua Flores B | Canna | base | 0-4-5 | 0.14 | 4 | Bluete, Frucht |
| Hakaphos Rot 18-18-18 | COMPO Expert | base | 18-18-18 | ~0.15 | 3 | Saemling, Vegetativ |
| Hakaphos Naranja 15-5-30 | COMPO Expert | base | 15-5-30 | ~0.14 | 3 | Bluete, Frucht |
| PK 13-14 | Canna | booster | 0-13-14 | 0.10 | 5 | Bluete (Woche 3--5) |

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Hornspane | Oscorna / div. | organisch (N-Langzeit) | 80--120 g/m2 | Fruehjahr (Einarbeitung bei Pflanzung) | heavy_feeder |
| Reifkompost | Eigenerzeugung | organisch | 3--5 L/m2 | Fruehjahr/Herbst | alle |
| Tomatendunger (fluessig) | COMPO BIO | organisch | 30--50 ml / 10 L Giesswasser | Mai--September, alle 7--14 Tage | heavy_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N-betont) | 1:10 verduennt, 1 L/m2 | Mai--August, alle 14 Tage | heavy_feeder |
| Beinwell-Jauche | Eigenerzeugung | organisch (K-betont) | 1:10 verduennt, 1 L/m2 | Juni--August, alle 14 Tage (zur Fruchtphase) | heavy_feeder |
| Schafwollpellets | Oscorna / div. | organisch (N-Langzeit) | 100--150 g/m2 | Fruehjahr | heavy_feeder |

### 3.2 Duengungsplan (Beispiel-NutrientPlan: "Tomate Standard Hydro/Coco")

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | PK 13-14 (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|-----------------|----------|
| 1--2 | Saemling | 0.4--0.6 | 5.8 | 0.3 | 0.5 | 0.5 | -- | Nur Wasser erste 5 Tage nach Keimung |
| 3--4 | Saemling/Veg | 0.8--1.0 | 5.8 | 0.5 | 1.0 | 1.0 | -- | EC langsam steigern |
| 5--7 | Vegetativ | 1.2--1.6 | 5.8--6.0 | 0.5 | 1.5 | 1.5 | -- | Vega A+B, hoher N-Anteil |
| 8--9 | Bluete frueh | 1.4--1.8 | 6.0 | 0.5 | 1.5 (Flores A) | 1.5 (Flores B) | -- | Umstellung auf Flores A+B |
| 10--12 | Bluete/Frucht | 1.8--2.2 | 6.0--6.2 | 0.5 | 1.5 | 1.5 | 0.5 | PK-Booster fuer Fruchtbildung |
| 13--16 | Fruchtreife | 2.0--2.5 | 6.0--6.5 | 0.5 | 1.2 | 1.5 | -- | Hoher K-Anteil fuer Geschmack |
| 17--18 | Flush | 0.0--0.4 | 6.0 | -- | -- | -- | -- | 7--14 Tage Klarwasser vor letzter Ernte |

### 3.3 Mischungsreihenfolge

> **Kritisch:** Die Reihenfolge verhindert Ausfaellungen (CalMag VOR Sulfaten!)

1. Wasser temperieren (18--22 degC)
2. CalMag Agent (Calcium + Magnesium -- verhindert Ca-P-Ausfaellungen bei spaeterer Base-B-Zugabe)
3. Base A -- Aqua Vega A / Aqua Flores A (Calcium + Mikronaehrstoffe)
4. Base B -- Aqua Vega B / Aqua Flores B (Phosphor + Schwefel + Magnesium)
5. PK 13-14 Booster (nur in Bluetephase Woche 3--5)
6. pH-Korrektur (pH Down / pH Up) -- IMMER als letzter Schritt

Wartezeit: Nach jeder Zugabe 1--2 Minuten ruehren/zirkulieren lassen, bevor das naechste Produkt hinzugefuegt wird.

### 3.4 Besondere Hinweise zur Duengung

- **Bluetenendfaeule (Blossom End Rot, BER):** Haeufigste physiologische Stoerung bei Tomaten. Ursache ist Ca-Transporterstoerung (nicht immer Ca-Mangel im Substrat!). Ausloeser: ungleichmaessige Bewaesserung, zu hohe EC, hohe Luftfeuchtigkeit. Gegenmassnahme: gleichmaessige Bewaesserung + Ca-Foliar-Spray (CalMag 0.5% Blattduengung) in frueher Fruchtphase.
- **EC nicht ueber 2.5 mS in der Fruchtphase** -- hemmt die Wasseraufnahme und verschlechtert Fruchtgroesse.
- **Kalium ist geschmacksbestimmend:** K:N-Verhaeltnis ab Fruchtphase mindestens 2:1 fuer optimalen Geschmack.
- **Organische Freiland-Duengung:** Starkzehrer benoetigen gut vorbereiteten Boden (Kompost + Hornspane bei Pflanzung), dann alle 14 Tage Brennnesseljauche (N-betont) und ab Fruchtbildung Beinwell-Jauche (K-betont).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 1--2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig, keine Winterpflege) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. Lauwarmes Wasser (18--22 degC) bevorzugt. Nie ueber die Blaetter giessen (Braunfaeule-Risiko). | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7--14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig, einmaliges Topfen/Pflanzen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan | Saatgut bestellen | Sorten auswaehlen, Saatgut-Pruefung | niedrig |
| Feb | -- | -- | -- |
| Marz | Vorkultur starten | Aussaat auf Heizmatte bei 22--25 degC, Samen 0.5 cm bedecken | hoch |
| Apr | Pikieren | In Einzeltoepfe (8--10 cm) umsetzen nach 2. Blattpaar, kuehlere Nachttemperaturen (16 degC) fuer stoeockigen Wuchs | hoch |
| Mai | Abhaertung + Auspflanzen | 7--10 Tage abhaerten, nach Eisheiligen (ca. 15.05.) auspflanzen, Stuetze setzen, Hornspane/Kompost einarbeiten | hoch |
| Jun | Ausgeizen + Anbinden | Regelmaessig Geiztriebe entfernen, an Staeben aufleiten, erste Duengergaben | hoch |
| Jul | Pflege + Ernte Beginn | Ausgeizen fortsetzen, regelmaessig giessen (morgens!), Mulchen, erste Fruechte ernten | hoch |
| Aug | Haupternte | Regelmaessig ernten, Blattkrankheiten kontrollieren, untere Blaetter entfernen fuer Luftzirkulation | hoch |
| Sep | Nachernte | Letzte Fruechte ernten, gruene Tomaten nachreifen lassen (Karton + Apfel-Trick mit Ethylen) | mittel |
| Okt | Saisonende | Pflanzen abbauen, Substrat entsorgen/kompostieren, Flaeche fuer naechstes Jahr planen | niedrig |

### 4.3 Ueberwinterung

Nicht anwendbar -- Tomate ist eine einjaehrige Nutzpflanze in Mitteleuropa. Keine Ueberwinterung moeglich.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaeuse (Aphids) | Myzus persicae, Macrosiphum euphorbiae | Blattrollungen, Honigtau, Virusvektor | leaf, stem | vegetative, flowering | easy |
| Weisse Fliege (Whitefly) | Trialeurodes vaporariorum | Honigtau, Russtau, Blattvergilbung | leaf | alle | easy |
| Spinnmilbe (Spider Mite) | Tetranychus urticae | Feine Gespinste, silbrige Punkte auf Blattunterseite | leaf | vegetative, flowering | medium |
| Tomatenminiermotte (Tomato Leafminer) | Tuta absoluta | Miniergaenge in Blaettern, Fruechte angebohrt | leaf, fruit | vegetative, flowering, ripening | medium |
| Thripse (Thrips) | Frankliniella occidentalis | Silbrige Flecken, verkrueppelte Blueten | leaf, flower | flowering | medium |
| Tomatenrostmilbe (Tomato Russet Mite) | Aculops lycopersici | Bronzefarbene Staengel, einrollende Blaetter von unten | stem, leaf | vegetative, flowering | difficult |
| Wurzelgallennematoden (Root-Knot Nematodes) | Meloidogyne spp. | Wurzelgallen, Kuemmerwuchs, Welke | root | alle | difficult |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kraut- und Braunfaeule (Late Blight) | fungal | Braun-schwarze Flecken an Blaettern/Staengeln, weisser Pilzrasen auf Blattunterseite, Fruchtfaeule | high_humidity, poor_airflow, rain | 3--7 | flowering, ripening |
| Echter Mehltau (Powdery Mildew) | fungal | Weisser Belag auf Blattoberseite, gelbe Flecken | dry_leaves, warm_days_cool_nights | 5--10 | vegetative, flowering |
| Fusarium-Welke (Fusarium Wilt) | fungal | Einseitige Blattwelke, braune Leitbuendel im Staengel | soil_contamination, warm_soil | 14--28 | vegetative, flowering |
| Grauschimmel (Grey Mold) | fungal | Grauer pelziger Belag auf Staengeln/Fruechten | high_humidity, poor_airflow | 3--5 | flowering, ripening |
| Bakterielle Welke (Bacterial Wilt) | bacterial | Ploetzliches Welken ganzer Pflanze ohne Vergilbung | warm_wet_soil | 5--14 | vegetative, flowering |
| Blattfleckenkrankheit (Septoria Leaf Spot) | fungal | Kleine runde Flecken mit dunklem Rand auf unteren Blaettern | rain_splash, high_humidity | 5--10 | vegetative, flowering |
| Tomaten-Mosaik-Virus (TMV) | viral | Mosaikartiges Blattmuster, Wuchshemmung | mechanical_transmission, contaminated_tools | 10--14 | alle |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5--10 | 14--21 |
| Encarsia formosa | Weisse Fliege | 3--5 | 21--28 |
| Macrolophus pygmaeus | Weisse Fliege, Tuta absoluta, Blattlaeuse | 2--5 | 28--42 |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse, Thripse | 5--10 | 14 |
| Feltiella acarisuga | Spinnmilbe | 3--5 | 14--21 |
| Steinernema feltiae (Nematode) | Trauermuecke, Thripse (Bodenstadien) | 250.000/m2 | 7--14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoel | biological | Azadirachtin | Spruehung 0.3--0.5%, alle 7 Tage | 3 | Blattlaeuse, Weisse Fliege, Thripse |
| Kaliumbicarbonat | biological | KHCO3 | Spruehung 0.5%, alle 7 Tage | 1 | Echter Mehltau |
| Kupferpraeparat (Bordeauxbruehe) | chemical | Kupferhydroxid | Spritzung praeventiv, alle 10--14 Tage | 14 | Kraut- und Braunfaeule |
| Schwefel | chemical | Schwefel | Staeubung/Spritzung | 14 | Echter Mehltau |
| Bacillus thuringiensis (Bt) | biological | Bt kurstaki Protein | Spritzung alle 7--10 Tage | 0 | Raupen, Tuta absoluta |
| Mulchen | cultural | -- | 5--8 cm Stroh um Stammfuss | 0 | Spritzwasser-Infektion (Septoria, Phytophthora) |
| Befallene Blaetter entfernen | cultural | -- | Regelmaessig untere Blaetter bis erste Fruchttraube entfernen | 0 | Verbesserung Luftzirkulation, Sporenreduktion |

### 5.5 Resistenzen der Art

Tomate als Wildart hat keine nennenswerten Resistenzen. Resistenzen werden ueber Cultivar-Zuechtung (F1-Hybriden) erreicht.

| Resistenz gegen | Typ | Verfuegbar ueber | KA-Edge |
|----------------|-----|----------------|---------|
| Fusarium oxysporum (Rasse 1+2) | Krankheit | Cultivare mit "F" Resistenzkennung | `resistant_to` |
| Verticillium dahliae | Krankheit | Cultivare mit "V" Resistenzkennung | `resistant_to` |
| Tomaten-Mosaik-Virus (TMV) | Krankheit | Cultivare mit "T" Resistenzkennung | `resistant_to` |
| Nematoden (Meloidogyne) | Schaedling | Cultivare mit "N" Resistenzkennung | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Nachtschattengewaechse (Solanaceae) |
| Empfohlene Vorfrucht | Huelsenfruechte (Fabaceae) -- Stickstoff-Fixierung; Graeser/Getreide (Poaceae) -- Bodenstruktur |
| Empfohlene Nachfrucht | Salat, Spinat, Radieschen (Schwachzehrer); Bohnen, Erbsen (Fabaceae -- N-Fixierer) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Solanaceae auf gleicher Flaeche (Phytophthora, Fusarium, Nematoden-Belastung) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Basilikum | Ocimum basilicum | 0.9 | Weisse-Fliege-Abwehr durch aetherische Oele, Aromaverbesserung (traditionell) | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes patula | 0.9 | Nematoden-Abwehr (Thiophene aus Wurzeln), Bestauber anlocken | `compatible_with` |
| Karotte | Daucus carota | 0.8 | Bodenbeschattung, gute Raumnutzung (Flach- + Tiefwurzler) | `compatible_with` |
| Petersilie | Petroselinum crispum | 0.8 | Blattlaus-Abwehr durch aetherische Oele, gute Raumnutzung | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Pilz-/Schaedlingsabwehr durch Allicin | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Bodenbeschattung, keine Naehrstoffkonkurrenz (Schwachzehrer) | `compatible_with` |
| Kohlrabi | Brassica oleracea var. gongylodes | 0.7 | Gute Raumnutzung, schnelle Ernte | `compatible_with` |
| Spinat | Spinacia oleracea | 0.7 | Bodenbeschattung, Saponin-Abgabe foerdert Naehrstoffverfuegbarkeit | `compatible_with` |
| Rosenkohl | Brassica oleracea var. gemmifera | 0.8 | Tomaten-Duft vertreibt Kohlweisslinge | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Gleiche Familie: gemeinsame Krankheiten (Phytophthora, Fusarium, Alternaria) und Schaedlinge (Kartoffelkaefer) | severe | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung durch Anethole/Fenchon | moderate | `incompatible_with` |
| Aubergine | Solanum melongena | Gleiche Familie: gemeinsame Krankheiten, Naehrstoffkonkurrenz | moderate | `incompatible_with` |
| Paprika | Capsicum annuum | Gleiche Familie: Krankheitsuebertragung (Verticillium, Fusarium) | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Wuchshemmung durch Wurzelausscheidungen der Tomate | mild | `incompatible_with` |
| Rotkohl | Brassica oleracea var. capitata f. rubra | Starke Naehrstoffkonkurrenz (beide Starkzehrer) | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-------------------|---------|
| Solanaceae (mit sich selbst) | `shares_pest_risk` | Kartoffelkaefer, Blattlaeuse; Kraut- und Braunfaeule, Fusarium | `shares_pest_risk` |
| Cucurbitaceae | `shares_pest_risk` | Blattlaeuse, Weisse Fliege | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Tomate |
|-----|-------------------|-------------|------------------------------|
| Buschtomate (determiniert) | Solanum lycopersicum (det.) | Gleiche Art, kompaktere Form | Kein Ausgeizen noetig, Topf-/Balkonkultur, fruehere Ernte |
| Tomatillo | Physalis philadelphica | Gleiche Familie, aehnliche Kultur | Robuster gegen Krautfaeule, exotische Frucht |
| Paprika | Capsicum annuum | Gleiche Familie, aehnliche Ansprueche | Weniger krankheitsanfaellig, lange Ernteperiode |
| Aubergine | Solanum melongena | Gleiche Familie | Hitzevertraglicher, dekorative Fruechte |
| Physalis (Kapstachelbeere) | Physalis peruviana | Gleiche Familie, aehnliche Kultur | Robuster, selbstbestaeubend, weniger Pflegebedarf |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat
Solanum lycopersicum,Tomate;Tomato;Paradeiser,Solanaceae,Solanum,annual,day_neutral,herb,fibrous,9a;9b;10a;10b;11a;11b,-0.2,"Suedamerika, westliche Anden (Peru, Ecuador)"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
San Marzano,Solanum lycopersicum,,1770,determinate;paste_type,75,fusarium,open_pollinated
Moneymaker,Solanum lycopersicum,,1913,indeterminate;high_yield,80,,open_pollinated
Harzfeuer,Solanum lycopersicum,Erfurter Saatzucht,1953,indeterminate;cold_tolerant;early,65,,open_pollinated
Philovita F1,Solanum lycopersicum,De Ruiter Seeds,,indeterminate;cherry;disease_resistant,60,fusarium;cladosporium;verticillium;tmv,f1_hybrid
Ochsenherz (Cuore di Bue),Solanum lycopersicum,,,indeterminate;beefsteak,80,,open_pollinated
Roma VF,Solanum lycopersicum,USDA,,determinate;paste_type,75,fusarium;verticillium,open_pollinated
```

---

## Quellenverzeichnis

1. PFAF (Plants For A Future) -- Solanum lycopersicum: https://pfaf.org/user/Plant.aspx?LatinName=Solanum+lycopersicum
2. RHS (Royal Horticultural Society) -- Tomato growing guide: https://www.rhs.org.uk/vegetables/tomatoes/grow-your-own
3. Ohio State University -- Hydroponic Nutrient Solution: https://ohioline.osu.edu/factsheet/hyg-1437
4. ASPCA Animal Poison Control -- Solanum lycopersicum Toxizitaet
5. Plantura -- Tomaten-Schaedlinge: https://www.plantura.garden/gemuese/tomaten/tomaten-schaedlinge
6. Koppert Biological Systems -- Tomatenkultur: https://www.koppertbio.at/kulturpflanzen/gemuese-geschuetzter-anbau/tomaten/
7. fryd.app -- Mischkultur mit Tomaten: https://fryd.app/magazin/mischkultur-mit-tomaten
8. LfL Bayern -- Tomaten Krankheiten und Schaedlinge: https://www.lfl.bayern.de/ips/kleingarten/019401/index.php
9. COMPO Expert -- Hakaphos Produktlinie: https://compo-expert.com/products/hakaphos-calcidic-plus-k-14-5-24
10. Canna Research -- Naehrstoff-Leitfaden: https://www.canna.com/en/research
11. Haifa Group -- Tomato Crop Guide: https://www.haifa-group.com/crop-guide/vegetables/tomato/crop-guide-tomato-plant-nutrition
12. UMN Extension -- Tomato nutrient management: https://extension.umn.edu/vegetables/growing-tomatoes
