# Melone -- Cucumis melo

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Oklahoma State University Extension, Virginia Tech VCE Publications, UMass Amherst Extension, Plantura, Hortipendium, Agric4Profits, Grove.eco, ResearchGate (Hydroponik-Studie)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cucumis melo | `species.scientific_name` |
| Volksnamen (DE/EN) | Melone; Zuckermelone; Honigmelone; Netzmelone; Muskusmelone; Melon; Cantaloupe; Honeydew; Muskmelon | `species.common_names` |
| Familie | Cucurbitaceae | `species.family` -> `botanical_families.name` |
| Gattung | Cucumis | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (Fruchtansatz taglaengenunabhaengig; kurze Tage foerdern weibliche Bluetenbildung) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart, stirbt bei Temperaturen unter 10 degC in der Wachstumsphase ab. Kulturzeit 80--100 Tage. Vorkultur ab April zwingend fuer Mitteleuropa; Freilandanbau erst nach Eisheiligen (Mitte Mai). | `species.hardiness_detail` |
| Heimat | Suedwestasien; Nordafrika (Ursprung unklar; Domestizierung vermutlich Persien/Iran) | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; heat_tolerant | `species.traits` |

**Varietaeten-Uebersicht:** Cucumis melo umfasst zahlreiche Botanische Varietaeten: var. cantalupensis (Netzmelonen/Cantaloupe), var. inodorus (Wintermelone/Honigmelone/Galia), var. flexuosus (Schlangenmelone), var. conomon (Pickling Melon). Die meisten Gartenmelonen gehoeren zu var. cantalupensis oder var. reticulatus.

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 3--4 (Anzucht ab Anfang bis Mitte April; Melonen reagieren empfindlich auf Stauchen -- nicht zu frueh!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 7--14 (Direktsaat nur in Zone 7+ und Gewächshaus/Folientunnel sinnvoll) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 (im Freiland erst ab sicherer Waerme) | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9 (sortenabhaengig; Fruehsorten ab Mitte Juli; Spaetsorten bis September) | `species.harvest_months` |
| Bluetemonate | 6; 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate (Waermekeimer; empfindlich gegenueber Verpflanzen; Topf-Direktaussaat empfohlen) | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 25--30 degC (Heizmatte dringend empfohlen)
- Keimdauer: 5--10 Tage
- Direktaussaat in Jiffy-Toepfe oder kleine Einzeiltöpfe (vermeidet Wurzelschaeden)
- **Keine Koldepikierung** -- Melonen reagieren empfindlich auf Wurzelstoerung
- Substrat: Lockere, naehrstoffarme Anzuchterde
- Nach Keimung Temperatur auf 20--22 degC absenken (Etiolierung vermeiden)

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | -- | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Trichome auf Blaettern und Stengeln koennen milde Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Melonenfruechte koennen bei Latexallergie eine orale Allergie-Reaktion ausloesen (Kreuzreaktion mit Latex/Kiwi/Banane).

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rueckschnitt-Monate | 6; 7; 8 (Triebfuehrung und Fruchtausdunnung waehrend der gesamten Wachstumsphase) | `species.pruning_months` |

**Triebfuehrung:**
- Haupttrieb nach 5--6 Blattern entspitzen (foerdert Seitentrebe)
- Seitentriebe 1. Ordnung nach 2 Blaettern zurueckschneiden (Fruechte entstehen hauptsaechlich hier)
- Pro Pflanze max. 2--4 Fruechte stehen lassen (groessere Qualitaet)
- Ueberzaehlige weibliche Bluetenansaetze entfernen (erkenntlich an kleiner Knolle am Ansatz)

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (grosse Behaelter 20--40 L noetig; Kompaktsorten besser geeignet) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20--40 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30--50 (kriechend/rankend; effektive Laenge bis 200 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100--200 (Ranktriebe; bei Senkrechterziehung deutlich weniger Flaechenbedarf) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60--100 in der Reihe; 120--150 cm Reihenabstand | `species.spacing_cm` |
| Indoor-Anbau | limited (nur mit sehr starker Beleuchtung > 600 PPFD und guter Belueftung; aufwendig) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Suedbalkon; grosser Kuebel; senkrechte Erziehung; Fruchtnetz als Stuetze) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | true (Optimale Ertraege im Foliengewaechshaus oder Kalthaus; in Mitteleuropa empfohlen) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | true (bei senkrechter Erziehung; Fruechte mit Netzen stuetzen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, humose, hervorragend drainierte Gemuese-/Kraeutererde. pH 6.0--6.8. Grosse Kompost-Anteile (30%). Keine Staunaesse -- Melonen reagieren empfindlich auf nasse Boeden. | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 5--10 | 1 | false | false | low |
| Saemling (seedling) | 14--21 | 2 | false | false | low |
| Vegetativ (vegetative) | 21--35 | 3 | false | false | medium |
| Bluete/Fruchtansatz (flowering) | 14--21 | 4 | false | false | medium |
| Fruchtentwicklung (fruit_development) | 35--50 | 5 | false | false | medium |
| Reife (ripening) | 14--21 | 6 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 0 (Keimung im Dunkeln; Anzuchterde duenn bedecken) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 (dunkel bis Keimung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--30 (Heizmatte kritisch!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 22--26 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80--90 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 85--95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.7 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (feucht halten, keine Staunaesse) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--20 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 10--18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 22--26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 30--80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 350--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 18--28 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 24--30 (optimal 26--28) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8--1.4 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 300--600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bluete/Fruchtansatz (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 22--32 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--14 (kuehlere Naechte foerdern weibliche Bluetenbildung) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 18--22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 (zu hoch: Bestaeubungsprobleme und Botrytis) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--1000 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 400--700 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Bestaeubungshinweis:** Im Gewaechshaus keine Insekten vorhanden -- manuelle Bestaeubung oder Hummelkoenigin einsetzen. Maennliche Bluetenstaub von maennlicher Bluete (kein kleines Knoellchen am Ansatz) auf weibliche Bluete uebertragen.

#### Phase: Fruchtentwicklung (fruit_development)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 400--700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 22--32 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--32 (Zuckeranreicherung in der Frucht erfordert Waerme) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 16--20 (Temperaturdifferenz Tag/Nacht foerdert Zucker-Einlagerung) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0--1.8 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 600--800 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Reife (ripening)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 18--28 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 25--32 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 (starke Nachtabkuehlung foerdert Aromaintensitaet) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40--55 (trocken halten; Feuchtigkeit foerdert Faeulnis und reduziert Zucker) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45--60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2--2.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 4--7 (Wasser deutlich reduzieren in den letzten 2 Wochen vor Ernte -- foerdert Zucker!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 200--400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Ernte-Indikatoren:**
- Stiel loest sich leicht von der Frucht (Abreiszone bei Cantaloupes und Netzmelonen)
- Schale verfaerbt sich: gelbliche/cremefarbige Grundfaerbung
- Charakteristischer suesser Fruchtduft am Stielansatz erkennbar
- Frucht gibt leicht nach bei leichtem Druck am Bluetenboden
- Netzmelonen: Netzzeichnung vollstaendig ausgebildet

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.0--6.5 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.8--1.2 | 5.8--6.2 | 80 | 30 | 20 | 2 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 5.8--6.2 | 120 | 50 | 30 | 3 |
| Bluete/Fruchtansatz | 2-2-3 | 1.6--2.2 | 5.8--6.2 | 150 | 50 | 30 | 3 |
| Fruchtentwicklung | 1-2-3 | 2.0--2.8 | 6.0--6.5 | 150 | 60 | 35 | 2 |
| Reife | 0-1-3 | 1.4--2.0 | 6.0--6.5 | 100 | 40 | -- | 1 |

**Hinweis:** EC ueber 3.5 mS/cm reduziert die Fruchtgroesse signifikant (ResearchGate Hydroponik-Studie). EC-Management in der Reife wichtig fuer Brix (Zuckergehalt).

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 5--10 Tage | Keimblaetter vollstaendig entfaltet |
| Saemling -> Vegetativ | manual / conditional | 14--21 Tage | 2--3 echte Blaetter; Umpflanzen in Endstandort |
| Vegetativ -> Bluete | event_based | 21--35 Tage | Erste maennliche Blueten sichtbar; Triebfuehrung abgeschlossen |
| Bluete -> Fruchtentwicklung | event_based | 10--14 Tage nach Bluete | Bestaeubte weibliche Blueten sichtbar als Fruchtansaetze |
| Fruchtentwicklung -> Reife | time_based / gdd_based | 35--50 Tage | Sortenabhaengige Reifeindikatoren |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch (Indoor/Gewaechshaus/Coco)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| CalMag | Canna / BioBizz | supplement | Ca+Mg | 0.12 | 2 | alle |
| Vega A+B | Canna | base | -- | 0.15/0.15 | 3/4 | Saemling; Vegetativ |
| Flores A+B | Canna | base | -- | 0.15/0.15 | 3/4 | Bluete; Fruchtentwicklung |
| PK 13/14 | Canna | booster | 0-13-14 | 0.10 | 5 | Fruchtentwicklung |
| Ripener / Final Solution | House&Garden | flush/ripener | -- | -- | 5 | Reife |

#### Organisch (Freiland/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 5--8 L/m2 | Fruehjahr (Pflanzloch) | heavy_feeder |
| Hornspäne | Oscorna | organisch (N-Langzeit) | 80--120 g/m2 | Mai (einarbeiten) | heavy_feeder |
| Tomatendunger Fluessig | COMPO BIO | organisch | 30--50 ml / 10 L | woechentlich Jun--Aug | heavy_feeder |
| Beinwelljauche | Eigenerzeugung | organisch (K-betont) | 1:10, 1 L/Pflanze | Juli--August | Fruchtentwicklung |

### 3.2 Duengungsplan

| Woche | Phase | EC (mS) | pH | CalMag (ml/L) | Base A (ml/L) | Base B (ml/L) | Hinweise |
|-------|-------|---------|-----|---------------|---------------|---------------|----------|
| 1--2 | Saemling | 0.6--1.0 | 5.8 | 0.3 | 0.4 | 0.4 | Nur Wasser erste 5 Tage |
| 3--5 | Vegetativ | 1.2--1.6 | 5.8 | 0.4 | 0.8 | 0.8 | EC langsam steigern |
| 6--8 | Bluete | 1.6--2.2 | 5.8--6.0 | 0.5 | 0.8 (Flores A) | 0.8 (Flores B) | Auf Flores umstellen |
| 9--13 | Fruchtentw. | 2.0--2.8 | 6.0--6.5 | 0.5 | 0.8 (Flores A) | 0.8 (Flores B) | PK-Booster hinzufuegen |
| 14--15 | Reife | 1.4--2.0 | 6.0 | 0.3 | 0.5 (Flores A) | 0.5 (Flores B) | Giessen und EC reduzieren |
| Letzte 7 Tage | Reife | -- | -- | -- | -- | -- | Nur Wasser; foerdert Zucker |

### 3.3 Mischungsreihenfolge

1. Wasser temperieren (20--24 degC)
2. CalMag
3. Base A (Calcium + Mikronaehrstoffe)
4. Base B (Phosphor + Schwefel + Magnesium)
5. Booster (PK 13/14 nur in Fruchtphase)
6. pH-Korrektur (IMMER als letzter Schritt)

### 3.4 Besondere Hinweise zur Duengung

- **Wasser reduzieren vor Ernte:** In den letzten 7--10 Tagen vor Ernte nur minimal giessen -- foerdert Zucker-Konzentration (Brix-Wert) und vertieft das Aroma erheblich.
- **Calcium-Mangel:** Kann zu Stippigkeit und Fruchtplatzen fuehren -- CalMag regelmaessig einsetzen.
- **EC-Kontrolle:** EC ueber 3.5 mS/cm reduziert Fruchtgewicht (Virginia Tech). Im Hydroponik gezielt zwischen 2.0--2.8 mS/cm halten.
- **Organisch Freiland:** Bodenanalyse empfehlen -- Melonen profitieren von hohem Kali-Vorrat im Boden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | herb_tropical | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--3 (regelmaessig aber nicht zu viel; Staunaesse vermeiden) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (einjaehrig) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Zimmerwarmes Wasser (20--24 degC). Blaetter nicht benetzen (foerdert Mehltau). Morgens giessen. Staunaesse unbedingt vermeiden. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 7 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (einjaehrig; 1x in Endtopf) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Jan--Maerz | Planung | Sortenwahl; Saatgut bestellen; Gewaechshaus vorbereiten | niedrig |
| Apr | Vorkultur | Aussaat in Einzeltoepfe; Heizmatte 25--30 degC; keine Pikierung | hoch |
| Mai | Auspflanzen | Nach Eisheiligen (15.5.) in Gewaechshaus oder windgeschuetztes Beet | hoch |
| Mai/Jun | Triebfuehrung | Haupttrieb entspitzen; Seitentriebe aufleiten; Rank-Hilfen anbringen | hoch |
| Jun/Jul | Bestaeubung | Im Gewaechshaus: manuelle Bestaeubung oder Hummel-Einsatz | hoch |
| Jun/Jul | Fruchtausdunnung | Max. 2--4 Fruechte je Pflanze belassen; Rest entfernen | hoch |
| Jul--Aug | Ernte + Pflege | Reifekontrolle; woechentlich duengen; Wasser letzte Woche reduzieren | hoch |
| Sep | Saisonende | Letzte Fruechte ernten; Beete raeumen; kompostieren | mittel |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; stippige Blattvergilbung | leaf | vegetative; flowering; fruit_development | medium |
| Weisse Fliege | Trialeurodes vaporariorum | Honigtau; weisse Fliegen; Russtau | leaf | vegetative; flowering | easy |
| Blattlaeuse | Aphis gossypii | Gekraeuselte Blaetter; Honigtau; Virusvektoren | leaf; shoot | seedling; vegetative | easy |
| Thripse | Frankliniella occidentalis | Silbrige Flecken; verkrueppelte Fruechte | leaf; flower | flowering; fruit_development | medium |
| Gurkenkaefer | Diabrotica undecimpunctata | Lochfrass; Wurzelschaeden; Virusvektoren | leaf; root | alle | medium |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Podosphaera xanthii) | Weisser mehliger Belag; Blaetter koennen absterben | dry_warm; poor_airflow | 5--10 | vegetative; flowering |
| Falscher Mehltau | oomycete (Pseudoperonospora cubensis) | Gelbliche Flecken; gräulicher Belag Blattunterseite | high_humidity; cool | 4--8 | vegetative; fruit_development |
| Fusarium-Welke | fungal (Fusarium oxysporum f. sp. melonis) | Welke; Stengel-Verbräunung | contaminated_soil; warm_wet | 14--28 | vegetative; fruit_development |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Belag; Faeulnis an Fruechten | high_humidity; cool | 3--7 | flowering; ripening |
| Gurkenmosaik-Virus (CMV) | viral | Mosaikartige Blaetter; verkrueppelte Fruechte | aphid_vectors | 7--14 | alle |
| Alternaria-Blattflecken | fungal (Alternaria cucumerina) | Braune konzentrische Flecken auf Blaettern | warm_wet; high_humidity | 3--7 | vegetative; fruit_development |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10--20 | 10--14 |
| Encarsia formosa | Weisse Fliege | 5--10 | 21--28 |
| Aphidoletes aphidimyza | Blattlaeuse | 5--10 | 14--21 |
| Amblyseius cucumeris | Thripse | 50--100 | 14--21 |
| Hummeln (Bombus spp.) | Bestaeubung (kein Schaedling) | 1 Volk / 200 m2 | -- |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoelextrakt | biological | Azadirachtin | 0.3% Spruehbehandlung abends | 3 | Spinnmilben; Blattlaeuse |
| Netzschwefel | chemical | Schwefel | Stauben oder spruehen | 14 | Echter Mehltau |
| Bicarbonate-Loesung | cultural | Kaliumbicarbonat | 0.5% spruehen | 0 | Mehltau-Praevention |
| Kaliseife | biological | Kaliumsalze | 2% spruehen | 3 | Blattlaeuse; Spinnmilben |
| Kupferpraeparat | approved_organic | Kupfer | 0.5% spruehen nach Regen | 7 | Falscher Mehltau |
| Mulchen | cultural | -- | Stroh/Grasschnitt 5 cm | 0 | Spritzwasser; Bodenpilze |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Fusarium oxysporum Race 0; 1; 2 (sortenbhg.) | Krankheit | `resistant_to` |
| Echten Mehltau Race 1; 2 (sortenbhg.) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Kuerbisgemaechse (Cucurbitaceae) |
| Empfohlene Vorfrucht | Leguminosen (Erbsen, Bohnen); Getreide; Gruenduengung (Phacelia) |
| Empfohlene Nachfrucht | Feldsalat; Spinat; Zwiebeln (Schwachzehrer) |
| Anbaupause (Jahre) | 3--4 Jahre fuer Cucurbitaceae auf gleicher Flaeche |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Falle (Opferpflanze); zieht Aphiden ab | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeubungsfoerderung | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Angelockte Nuetzlinge (Schlupfwespen, Schwebfliegen) | `compatible_with` |
| Mais | Zea mays | 0.6 | Windschutz; gibt Struktur; kein Naehrstoffkonflikt | `compatible_with` |
| Zwiebeln | Allium cepa | 0.6 | Fernhaltung von Schnaecken; Pilzpraevention | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.6 | Bestaeubungsfoerderung; Aromaschutz | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Foerdert gemeinsame Bodenpilze (Fusarium) | moderate | `incompatible_with` |
| Andere Cucurbitaceae | Cucumis sativus; Cucurbita spp. | Gleiche Schaderreger (Mehltau; CMV); Kreuzbestaeubung moeglich | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Cucurbitaceae | `shares_pest_risk` | Echter Mehltau (Podosphaera xanthii); Falscher Mehltau; CMV; Spinnmilben | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Melone |
|-----|-------------------|-------------|--------------------------|
| Wassermelone | Citrullus lanatus | Gleiche Familie; aehnliche Kultur | Groessere Fruechte; laengere Haltbarkeit; andere Aromacharakter |
| Gurke | Cucumis sativus | Gleiche Gattung; sehr aehnliche Kultur | Schnellere Ernte (45--60 Tage); weniger Waermeanspruch |
| Zucchini | Cucurbita pepo | Gleiche Familie | Einfacher; kuerzere Kulturdauer; weniger Waerme noetig |

---

## 8. Sorten / Cultivars

| Sorte | Typ | Reifezeit (Tage) | Fruchtgewicht (kg) | Fleischfarbe | Besonderheiten |
|-------|-----|-----------------|-------------------|--------------|----------------|
| Charentais | Cantaloup (frz.) | 75--85 | 0.5--1.0 | Orange | Klassisch; intensivster Aroma; sehr beliebt in Europa |
| Galia | Netzmelone | 70--80 | 0.8--1.5 | Weissl.-gruen | Suesser Aroma; gute Transportfaehigkeit |
| Ananas | Netzmelone | 80--90 | 1.5--3.0 | Orange | Ananas-Aromanote; laengere Haltbarkeit |
| Honigmelone (Honeydew) | Inodorus | 90--100 | 2.0--4.0 | Hellgruen | Keine Abreiszone; Reife am Duft erkennbar |
| Hale's Best Jumbo | Cantaloup | 80--90 | 1.5--2.5 | Orange | Robust; hitzetolerant; Klassiker US-Anbau |
| Petit Gris de Rennes | Cantaloup | 70--80 | 0.5--0.8 | Orange | Spaetreif-resistent; gut fuer Mitteleuropa |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity
Cucumis melo,Melone;Zuckermelone;Honigmelone;Melon;Cantaloupe,Cucurbitaceae,Cucumis,annual,day_neutral,vine,fibrous,4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,-0.1,Suedwestasien; Nordafrika,limited,20,30,40,150,80,limited,limited,true,true,heavy_feeder,tender
```

---

## Quellenverzeichnis

1. [Oklahoma State University Extension -- Melon Production](https://extension.okstate.edu/fact-sheets/melon-production) -- Duengung; Bodenpflege; Sorten
2. [Virginia Tech VCE Publications -- Cucumis melo Physiology](https://www.pubs.ext.vt.edu/SPES/spes-507/spes-507.html) -- Biologie; Sexualexpression; Wachstumsphasen
3. [UMass Amherst Extension -- Melons Growing Tips](https://www.umass.edu/agriculture-food-environment/home-lawn-garden/fact-sheets/melons-growing-tips) -- Praktischer Anbau
4. [Hortipendium -- Melonen Erwerbsanbau](https://hortipendium.de/Melonen_Erwerbsanbau) -- Professioneller Anbau; EC; Duengung
5. [Plantura -- Honigmelonen pflanzen](https://www.plantura.garden/gemuese/melonen/honigmelonen-pflanzen) -- Praxis-Tipps Mitteleuropa
6. [Grove.eco -- Cucumis melo Nachbarn](https://www.grove.eco/en/plants/cucumis-melo/) -- Companion Planting; Fruchtfolge
7. [ResearchGate -- Melon production using hydroponic systems](https://www.researchgate.net/publication/283034211_Melon_production_using_four_hydroponic_systems) -- EC-Studie; Hydroponik-Daten
8. [Agric4Profits -- Melon Farming Guide](https://agric4profits.com/melon-farming-cucumis-melo-growing-guide/) -- Anbauguide; Sorten; Schädlinge
