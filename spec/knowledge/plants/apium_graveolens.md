# Sellerie -- Apium graveolens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Hortipendium, Hausgarten.net, NaturaDB, samen.de, bio-gaertner.de, Bildungs- und Beratungszentrum Arenenberg Kulturblatt Sellerie, Plantura, Pflanzio

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Apium graveolens | `species.scientific_name` |
| Volksnamen (DE/EN) | Sellerie; Knollensellerie; Stangensellerie; Schnittsellerie; Celery; Celeriac; Smallage | `species.common_names` |
| Familie | Apiaceae | `species.family` -> `botanical_families.name` |
| Gattung | Apium | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | biennial (im Anbau meist als annual kultiviert -- Knollenbildung im 1. Jahr) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day (Schoessung im 2. Jahr durch lange Tage und Kaeltereiz ausgeloest) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Jungpflanzen koennen durch Frost (< -5 degC) zur Schoessung angeregt werden (Vernalisation). Ausgewachsene Knollen halten leichte Froeste bis -5 degC kurzfristig aus. Schoesslingsgefahr bei zu frueh gesaeten und vernalisierten Pflanzen. | `species.hardiness_detail` |
| Heimat | Mitteleuropa; Mittelmeerraum; Westasien (Wildform in feuchten Niederungen) | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible; aromatic; medicinal | `species.traits` |

**Varietaeten:**
- **var. rapaceum** -- Knollensellerie (kultivierte Knolle; wichtigste Anbauform in Deutschland)
- **var. dulce** -- Stangensellerie (Bleichsellerie; lange dicke Blattstiele)
- **var. secalinum** -- Schnittsellerie (Suppengruen; krautige Blaetter; einfachste Kultur)

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7--8), letzter Frost ca. Mitte Mai. Nur Vorkultur (Knollen- und Stangensellerie sind Lichtkeimer mit sehr kleinen Samen).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10--12 (Aussaat Februar/Maerz -- Sellerie hat extrem lange Vorkulturzeit!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -- (Direktsaat nicht praxistauglich bei Knollen- und Stangensellerie) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4; 5 (nur Schnittsellerie; mehrfach direkt saeend) | `species.direct_sow_months` |
| Erntemonate | 9; 10; 11 (Knollensellerie); 6; 7; 8; 9; 10 (Schnittsellerie) | `species.harvest_months` |
| Bluetemonate | 6; 7 (nur im 2. Standjahr oder bei schoessenden Pflanzen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult (Lichtkeimer; sehr feine Samen; lange Keimung; kaelteempfindlich) | `species.propagation_difficulty` |

**Keimhinweise:**
- **Lichtkeimer** -- Samen NICHT mit Erde bedecken; nur leicht andrucken!
- Optimale Keimtemperatur: 18--22 degC
- Keimdauer: 14--21 Tage (langsam und ungleichmaessig)
- Heizmatte und Abdeckfolie bis Keimung (Feuchte halten)
- Nach Keimung zuerst 14--16 h Licht, Temperatur auf 16--18 degC
- Pikieren sehr sorgfaeltig (feine Wurzeln) -- 2 Mal pikieren empfohlen (erst in Saatschale, dann in 9-cm-Topf)
- **Vernalisationsgefahr:** Jungpflanzen nicht unter 10 degC -- sonst Schoessung!

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false (leichte Magenprobleme bei grossen Mengen moeglich) | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | -- | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Furocumarine (Psoralene) in rohen Blaettern -- Photosensibilisierung; Sellerie-Allergen Apg r 1 | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Furocumarine + Sonnenlicht = Phototoxische Reaktion; besonders bei Wildform und Blaettern) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Sellerie-Beifuss-Birken-Syndrom; Kreuzallergie mit Birke und Beifuss-Pollen) | `species.allergen_info.pollen_allergen` |

**Wichtiger Hinweis:** Sellerie ist einer der 14 deklariationspflichtigen Hauptallergene der EU (Lebensmittelkennzeichnungsverordnung). Das sogenannte Sellerie-Beifuss-Birken-Syndrom betrifft einen signifikanten Anteil der Birkenpollen-Allergiker.

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | -- | `species.pruning_months` |

**Hinweis:** Schnittsellerie wird durch regelmäßige Ernte der äusseren Blattstiele genutzt (Cut-and-Come-Again-Methode). Knollensellerie: Blattkraut kann fuer Suppenwuerzung mitverwendet werden. Keine Rueckschnittmassnahmen benoetigt.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Schnittsellerie gut im Topf; Knollensellerie benoetigt grossen Behaelter) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10--20 (Schnittsellerie); 20--30 (Knollensellerie) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 25 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 50--80 (Knollensellerie); 40--60 (Schnittsellerie) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30--50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30--40 (Reihen 40--50 cm) | `species.spacing_cm` |
| Indoor-Anbau | limited (Schnittsellerie als Fensterbrett-Kraut moeglich) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Schnittsellerie gut; Knollensellerie bedingt) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freilandbeet bevorzugt; Gewaechshaus fuer Vorkultur bis Auspflanzen) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche, gut wasserhaltige (aber drainierte) Gemuese-/Kraeutererde. pH 6.5--7.0. Hohe Humusanteile. Gleichmaessige Feuchtigkeit wichtig -- Sellerie vertraegt weder Trockenheit noch Staunaesse. | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

(Angaben fuer Knollensellerie; im 1. Kulturjahr)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung (germination) | 14--21 | 1 | false | false | low |
| Saemling (seedling) | 28--42 | 2 | false | false | low |
| Jungpflanze (juvenile) | 28--42 | 3 | false | false | low |
| Vegetativ/Knollenansatz (vegetative) | 56--84 | 4 | false | false | medium |
| Knollenentwicklung (bulking) | 42--63 | 5 | false | true | medium |
| Erntereife (harvest) | 14--28 | 6 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 50--150 (Lichtkeimer -- Licht foerdert Keimung!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 3--8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 15--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75--85 (Aussaaterde gleichmaessig feucht halten) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80--90 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3--0.7 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1 (sehr feine Samen; Bodenfeuchte nie abreissen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 5--15 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 150--300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 8--15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--20 (NICHT unter 12 degC -- Vernalisationsgefahr!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--16 (IMMER ueber 12 degC halten) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5--0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 1--2 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 10--30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Jungpflanze (juvenile)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 200--400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 12--20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 16--22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 (Nachttemperatur mind. 12 degC; Vernalisation vermeiden!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400--600 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 2--3 | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 50--150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ/Knollenansatz (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 (Freiland; volle Sonne bevorzugt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 18--28 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14--16 (langer Tag foerdert vegetatives Wachstum) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 18--24 (optimal 20; Hitze > 30 degC stresst die Pflanze) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 14--18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 3--5 (gleichmaessige Feuchte; Trockenheit foerdert hohle Stiele) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 500--1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Knollenentwicklung (bulking)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (umol/m2/s) | 300--500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m2/Tag) | 15--25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12--16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (degC) | 15--22 (kuehlere Herbsttemperaturen foerdern Knolle!) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (degC) | 10--15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55--70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60--75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6--1.2 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Giessintervall (Tage) | 4--7 (groesster Wasserbedarf Mitte August bis Anfang Oktober!) | `requirement_profiles.irrigation_frequency_days` |
| Giessmenge (ml/Pflanze) | 800--1500 (Hauptwasserbedarfsphase: 15--20 L/m2) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0-0-0 | 0.0 | 6.5--7.0 | -- | -- | -- | -- |
| Saemling | 1-1-1 | 0.6--1.0 | 6.0--7.0 | 60 | 25 | -- | 2 |
| Jungpflanze | 2-1-1 | 1.0--1.4 | 6.5--7.0 | 80 | 30 | 20 | 2 |
| Vegetativ | 3-1-2 | 1.4--2.0 | 6.5--7.0 | 120 | 50 | 30 | 3 |
| Knollenentw. | 1-2-3 | 1.8--2.4 | 6.5--7.0 | 150 | 60 | 35 | 2 |
| Erntereife | 0-1-2 | 1.0--1.6 | 6.5--7.0 | 80 | 40 | -- | 1 |

### 2.4 Phasenuebergangsregeln

| Von -> Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung -> Saemling | time_based | 14--21 Tage | Keimblaetter sichtbar; 1. echtes Blattpaar |
| Saemling -> Jungpflanze | manual | 28--42 Tage | 3--4 echte Blaetter; 1. Pikierung |
| Jungpflanze -> Vegetativ | manual | 28--42 Tage | Auspflanzen nach letztem Frost (Mai) |
| Vegetativ -> Knollenentw. | event_based | -- | Knolle beginnt sich zu formen; Hochsommer vorbei |
| Knollenentw. -> Erntereife | time_based | 42--63 Tage | Knollendurchmesser > 10 cm; Herbst |

---

## 3. Duengung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischprioritaet | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Hakaphos Blau | Compo Expert | base | 15-10-15 | nach Packung | 2 | Vegetativ; Knollenansatz |
| Nitrophoska Perfect | Compo | base | 15-5-20+2MgO | Granulat 40 g/m2 | 1 | Fruehjahr/Auspflanzen |
| Bitsalz (Epsom Salt) | div. | supplement | 0-0-0 (Mg 13%) | 1--2 g/L | 4 | alle (Blattduengung moeglich) |

#### Organisch (Freiland bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Reifkompost | Eigenerzeugung | organisch | 6--8 L/m2 | Herbst/Fruehjahr | heavy_feeder; Bodenverbesserung |
| Hornspäne | Oscorna | organisch (N-Langzeit) | 80--120 g/m2 | Mai (Auspflanzen) | heavy_feeder |
| Gemueseduenger | COMPO BIO / Neudorff | organisch (Fluessig) | 25--40 ml / 10 L | woechentlich Jun--Sep | heavy_feeder |
| Brennnesseljauche | Eigenerzeugung | organisch (N) | 1:10, 1 L/Pflanze | Jun--Jul alle 14 Tage | Vegetativphase |
| Algenkalk | Oscorna | pH-Puffer + Calcium | 150--200 g/m2 | Herbst | pH < 6.5; Ca-Versorgung |

### 3.2 Duengungsplan (Freiland Knollensellerie)

| Monat | Phase | Massnahme | Menge | Hinweise |
|-------|-------|-----------|-------|----------|
| Herbst Vorjahr | Bodenvorb. | Kompost einarbeiten | 6--8 L/m2 | Tief unterheben (30 cm) |
| Maerz | Vorkultur | Vorkultur-Startduenger | 0.2 g/L Volduenger | Niedrige Dosierung Saemling |
| Mai (Pflanzung) | Auspflanzen | Hornspäne einarbeiten | 80--120 g/m2 | Pflanzlochsanreicherung |
| Jun | Vegetativ | 1. Fluessigduengung | Brennnesseljauche 1:10 | N-Schub fuer Wachstum |
| Jul | Vegetativ | 2. Fluessigduengung | Gemueseduenger | Kalibetont ab Mitte Juli |
| Aug | Knollenentw. | 3. Duengung | Gemueseduenger kalireich | Phosphor und Kali foerdern Knolle |
| Sep | Knollenentw. | Letzte Duengung | Reduziert | Keine N-Duengung mehr |
| Okt--Nov | Ernte | -- | -- | Knollenernte vor Dauerfrrost |

### 3.3 Mischungsreihenfolge

1. Wasser temperieren (18--22 degC)
2. Bittersalz (Magnesium, bei Bedarf)
3. Stickstoff-Betonte Duengelosung (Vega-Phase)
4. Kalibetonter Duenger (Knollenphase)
5. pH pruefen (Sellerie: pH 6.5--7.0 optimal)

### 3.4 Besondere Hinweise zur Duengung

- **Starkzehrer mit hohem Borensbedarf:** Bormangel zeigt sich als hohle Knolle (Sellerieholz-Krankheit). Borax 0.5--1.5 g/m2 vorbeugend ins Pflanzloch einarbeiten.
- **Calcium kritisch:** Calciumversorgung verhindert Herzfaeule (Blattfaeule im Herz). Regelmässige Kalkduengung (Algenkalk) empfohlen.
- **Keine Staunaesse:** Sellerie vertraegt keine Nassuebersaettigung trotz hohem Wasserbedarf. Gleichmaessige Feuchte am wichtigsten.
- **Voranstaerkung durch Kompost:** Sellerie profitiert enorm von gut reifem Kompost -- bis zu 8 L/m2 sind nicht zu viel.
- **Schoessling-Gefahr:** Zu fruehe N-Duengung + Kaeltestress kann Schoessing ausloesen -- erst nach sicherer Einwurzelung duengen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Giessintervall Sommer (Tage) | 2--4 (sehr gleichmaessige Feuchte; trockener Boden foerdert hohle Stiele) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | -- (im Freiland kein Giessen nach Ernte) | `care_profiles.winter_watering_multiplier` |
| Giessmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Kalkvertraeglich. pH 6.5--7.5 gut. Kaltes Wasser vermeiden. Gleichmaessige Wasserversorgung kritisch -- Trockenstress foerdert hohle Stiele und bitteren Geschmack. | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5; 6; 7; 8; 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | -- (Freilandpflanze; einmalig pikieren und auspflanzen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb | Aussaat (1.) | Lichtkeimer; Saatschale, nicht bedecken, Heizmatte 20 degC | hoch |
| Maerz | Pikieren (1.) | In Saatschalen oder Einzeltoepfe 4 cm; zartes Handling | hoch |
| Apr | Pikieren (2.) | In 9-cm-Toepfe; Temperatur MIND. 12 degC halten | hoch |
| Mai | Auspflanzen | Nach Eisheiligen; Pflanzabstand 30--40 cm; gut eingiessen | hoch |
| Jun--Jul | Giessen + Duengen | Feuchte halten; Brennnesseljauche alle 2 Wochen | hoch |
| Aug | Hauptbewaesserung | Groesster Wasserbedarf; 15--20 L/m2; 3. Duengung | hoch |
| Sep | Knollenreife | Herbstduengung reduzieren; Reife pruefen | mittel |
| Okt--Nov | Ernte | Vor Dauerfrrost ernten; Lager 1--3 degC dunkel | hoch |

### 4.3 Ueberwinterung (Lagerung geernteter Knollen)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhaerte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Massnahme | dig_and_store | `overwintering_profiles.winter_action` |
| Winter-Massnahme Monat | 10; 11 | `overwintering_profiles.winter_action_month` |
| Fruehjahrs-Massnahme | replant | `overwintering_profiles.spring_action` |
| Fruehjahrs-Massnahme Monat | -- (Neuaussaat im Fruehjahr) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (degC) | 1 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (degC) | 5 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark | `overwintering_profiles.winter_quarter_light` |
| Winter-Giessen | none | `overwintering_profiles.winter_watering` |

**Lagerung geernteter Knollen:** Knollen mit Laub auf 10 cm zurueckschneiden; in feuchtem Sand oder Saegemehl bei 1--5 degC lagern. Haltbarkeit bis April/Mai. Im Garten koennen Knollen mit dicker Laubschicht bis ca. -8 degC ueberwintern.

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Selleriefliege | Euleia heraclei | Minen in Blaettern; Blattfleisch ausgehoehlte helle Gaenge | leaf | vegetative; bulking | easy |
| Karottenblatfloh | Trioza apicalis | Verwachsungen; Nekrosen an Blaettern; Stauchung | leaf; shoot | juvenile; vegetative | difficult |
| Maedchenkaefer / Blattlaeuse | Cavariella aegopodii | Gekraeuselte Blaetter; Honigtau; Virusvektoren | leaf; shoot | vegetative | easy |
| Moehrenblattlaus | Semiaphis dauci | Honigtau; Wachstumsstoerung | leaf | vegetative | medium |
| Wuehlmaeuse | Arvicola terrestris | Frass an Knollen | root | bulking; harvest | difficult |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloeser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Septoria-Blattflecken | fungal (Septoria apiicola) | Braun-gelbe Flecken; Blaetter welken | warm_wet; high_humidity | 7--14 | vegetative; bulking |
| Sellerierost | fungal (Phoma apiicola) | Rote-braune Rostflecken auf Blaettern | warm_wet | 7--14 | vegetative |
| Fusarium-Welke | fungal (Fusarium oxysporum) | Welke; Stengel-Verbräunung | contaminated_soil | 14--28 | vegetative; bulking |
| Sellerischorf | fungal | Schorfig-korkige Stellen an der Knolle | contaminated_soil; wet | 14--21 | bulking |
| Herzfaeule (Calcium-Mangel) | physiological | Schwarzfaerbung des Herzblattbereiches | calcium_deficiency; irregular_watering | 3--7 | juvenile; vegetative |
| Holligkeit (Bor-Mangel) | physiological | Hohle braune Stiele und Knolle | boron_deficiency | 21--42 | bulking; harvest |
| Celeryvirus (CV) | viral | Mosaikmuster; Blattkraeuse | aphid_vectors | 7--14 | alle |

### 5.3 Nuetzlinge (Biologische Bekaempfung)

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m2) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea | Blattlaeuse | 5--10 Larven/m2 | 7--14 |
| Schlupfwespen (Aphidius colemani) | Blattlaeuse | 3--5/m2 | 14--21 |
| Schwebfliegen (diverse) | Blattlaeuse | Spontan durch Begleitpfl. | -- |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemoelextrakt | biological | Azadirachtin | 0.3% spruehen abends | 3 | Selleriefliege-Prävention; Blattlaeuse |
| Pyrethrum | approved_organic | Pyrethrine | Spruehen bei Befall | 7 | Blattlaeuse; Selleriefliege |
| Kaliseife | biological | Kaliumsalze | 2% spruehen | 3 | Blattlaeuse |
| Kulturschutznetz | cultural | -- | 0.8 mm Netz | 0 | Selleriefliege (mechanisch!) |
| Algenkalk (Boden) | cultural | Calcium | 150--200 g/m2 einarbeiten | 0 | Herzfaeule-Praevention |
| Borax-Einarbeitung | cultural | Bor | 0.5--1.5 g/m2 | 0 | Holligkeit-Praevention |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Fusarium (Schnittsellerie-Sorten teilweise) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer |
| Fruchtfolge-Kategorie | Doldenblueter (Apiaceae) |
| Empfohlene Vorfrucht | Getreide; Leguminosen (Erbsen, Bohnen); Gruenduengung (Lupine) |
| Empfohlene Nachfrucht | Schwachzehrer (Feldsalat, Postelein, Zwiebeln) |
| Anbaupause (Jahre) | 4--5 Jahre (Septoria bleibt im Boden; Fruchtfolge mit anderen Apiaceae einhalten) |

### 6.2 Mischkultur -- Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.9 | Gegenseitige Foerderung; Sellerie haelt Laeuse vom Tomatenbeet fern | `compatible_with` |
| Kohlgewaechse | Brassica oleracea | 0.8 | Kohlweissling wird durch Sellerie-Aromte abgelenkt | `compatible_with` |
| Buschbohnen | Phaseolus vulgaris | 0.7 | N-Fixierung; keine Naehrstoffkonkurrenz | `compatible_with` |
| Lauch | Allium porrum | 0.8 | Gegenseitiger Insektenschutz; Selleriefliege und Lauchmotte | `compatible_with` |
| Tagetes | Tagetes patula | 0.7 | Nematoden-Abwehr; Geruchsschutz | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Gute Raumnutzung; kein Wettbewerb | `compatible_with` |

### 6.3 Mischkultur -- Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Moehren | Daucus carota | Gleiche Schaderreger (Moehrenblattfloh; Blattlaeuse); gleiche Familie | moderate | `incompatible_with` |
| Pastinake | Pastinaca sativa | Gleiche Familie (Apiaceae); gemeinsame Krankheiten | moderate | `incompatible_with` |
| Petersilie | Petroselinum crispum | Gleiche Familie; Septoria-Uebertragung | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Foerdert gemeinsame Pilzkrankheiten im Boden | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Apiaceae | `shares_pest_risk` | Septoria; Selleriefliege; Karottenblatfloh; Fusarium | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Sellerie |
|-----|-------------------|-------------|----------------------------|
| Moehre | Daucus carota | Gleiche Familie; aehnliche Kultur | Einfacher; laengere Lagerung; haeufiger angebaut |
| Petersilie | Petroselinum crispum | Gleiche Familie; aehnliche Aromastoffe | Einfacher; auch als Topfpflanze |
| Lovage (Liebstoeckel) | Levisticum officinale | Aehnliches Aroma | Mehrjaehrig; pflegeleichter; robust |

---

## 8. Sorten / Cultivars

### Knollensellerie (var. rapaceum)

| Sorte | Typ | Knollengroesse | Tage bis Ernte | Besonderheiten |
|-------|-----|---------------|----------------|----------------|
| Monarch | Standard | mittelgross--gross | 100--120 | Feines Aroma; glatte Knolle; beliebt |
| Mars | Fruehsorte | mittelgross | 85--100 | Sehr spaet schossend; fuer Mitteleuropa gut geeignet |
| Prinz | Standard | gross | 110--125 | Hohe Ertraege; lagerfaehig |
| Giant Prague | Heirloom | sehr gross | 120--140 | Traditionelle Sorte; schoene Form |
| Balena | Resistenzsorte | mittelgross | 100--115 | Septoria-tolerant |

### Stangensellerie (var. dulce)

| Sorte | Typ | Stiel-Farbe | Tage bis Ernte | Besonderheiten |
|-------|-----|------------|----------------|----------------|
| Tango F1 | Modern | hellgruen | 85--100 | Selbstbleichend; kein Aufbinden noetig |
| Utah 52-70 | Standard | dunkelgruen | 100--120 | Kräftiges Aroma; klassische Sorte |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity
Apium graveolens,Sellerie;Knollensellerie;Stangensellerie;Celery;Celeriac,Apiaceae,Apium,biennial,long_day,herb,taproot,5a;5b;6a;6b;7a;7b;8a;8b;9a;9b,0.2,Mitteleuropa; Mittelmeer,limited,20,25,70,40,35,limited,limited,false,false,heavy_feeder,half_hardy
```

---

## Quellenverzeichnis

1. [Hortipendium -- Sellerie](https://www.hortipendium.de/Sellerie) -- Anbautechnik; Duengung; Schädlinge professionell
2. [Hausgarten.net -- Sellerie](https://www.hausgarten.net/sellerie/) -- Praxis-Tipps; Anbau Hobbygarten
3. [NaturaDB -- Apium graveolens](https://www.naturadb.de/pflanzen/apium-graveolens/) -- Botanische Grunddaten; Standort
4. [Samen.de -- Knollensellerie Schutzen](https://samen.de/blog/knollensellerie-schuetzen-krankheiten-und-schaedlinge-erkennen.html) -- Schädlinge und Krankheiten
5. [Samen.de -- Knollensellerie Bewaesserung und Duengung](https://samen.de/blog/optimale-bewaesserung-und-duengung-fuer-gesunden-knollensellerie.html) -- Bewässerung; Duengung
6. [BBZ Arenenberg -- Kulturblatt Sellerie](https://arenenberg.tg.ch/public/upload/assets/9009/2015_Kulturblatt_Sellerie.pdf) -- Professionelles Kulturblatt (Schweiz)
7. [Pflanzio -- Schnittsellerie](https://pflanzio.de/apium-graveolens/) -- Schnittsellerie-Anbau
8. [Bio-gaertner.de -- Sellerie](https://www.bio-gaertner.de/pflanzen/Sellerie) -- Biologischer Anbau; Mischkultur
