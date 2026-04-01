# Weißkohl — Brassica oleracea var. capitata f. alba

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Plantura Weißkohl-Anbau, Samen.de Weißkohl-Kultivierung, Das Grüne Archiv Weißkohl, effizientduengen.de Kopfkohl, Hortipendium Weißkohl IPM, Thüringer Landesanstalt TLL Kohlanbau, COMPO Kohlduengung

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Brassica oleracea var. capitata f. alba | `species.scientific_name` |
| Volksnamen (DE/EN) | Weißkohl, Weißkabis (CH), Kappes (regional); White Cabbage, Head Cabbage | `species.common_names` |
| Familie | Brassicaceae | `species.family` -> `botanical_families.name` |
| Gattung | Brassica | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual (Sommerkohl); biennial (Herbst-/Winterkohl) | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 1a; 2a; 2b; 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Sehr frosthart — ausgewachsene Koepfe vertragen bis -10°C kurzfristig; Winterkohl-Sorten bis -20°C; Jungpflanzen frost-empfindlicher (bis -3°C). Gehoert zu den winterhaertesten Gemuesen. | `species.hardiness_detail` |
| Heimat | Atlantik-Europa, Mittelmeer (Wildart: Brassica oleracea var. oleracea) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7–8).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Fruehjahrsvorkultur ab Mär.) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (frostverträglich; Direktsaat ab Mär.–Apr. moeglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3; 4 (Sommerkohl); 5; 6 (Herbstkohl); 7 (Winterkohl) | `species.direct_sow_months` |
| Erntemonate | 7; 8 (Sommerkohl); 9; 10; 11 (Herbstkohl); 11; 12; 1; 2 (Winterkohl) | `species.harvest_months` |
| Bluetemonate | 5; 6 (2. Jahr; bei Schoessern) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 15–20°C
- Minimale Keimtemperatur: 5°C (sehr langsam)
- Keimdauer: 4–7 Tage
- Saattiefe: 1–1.5 cm
- Wichtig: Vernalisation (Kältereiz) foerdert Kopfbildung. Ohne Vernalisation (> 3°C fuer mehrere Wochen) kein Schossen im Folgejahr.
- Jungpflanzen ab 5°C abhärten vor dem Auspflanzen

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Glucosinolate (in sehr hohen Mengen goitrogen; kein Gesundheitsrisiko bei normaler Ernaehrung) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | after_harvest | `species.pruning_type` |
| Rueckschnitt-Monate | 7; 8; 9; 10; 11 | `species.pruning_months` |

**Hinweis:** Kein aktiver Rueckschnitt noetig. Aeltere Aussenblätter regelmaessig entfernen (Krankeitsvorbeugung). Stumpf nach Ernte auf dem Beet stehen lassen oder entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Grosskoeprfige Sorten nicht; Miniatursorten moeglich mit >30 L) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–40 (nur kompakte Sorten) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 30–60 (Kopf; mit Strunk bis 80 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 50–60 (kleine Sorten); 60–80 (grosse Sorten) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur Miniatursorten; grosser Behaelter) | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Freilandkultur bevorzugt; GWH fuer Fruehkultur moeglich) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Naehrstoffreiche Gartenerde mit Kompost; pH 6.5–7.5; gut wasserspeichernd; schwerere Boeden bevorzugt | -- |

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 4–7 | 1 | false | false | medium |
| Saemling | 21–35 | 2 | false | false | low |
| Vegetativ / Rosettenstadium | 35–56 | 3 | false | false | medium |
| Kopfbildung | 21–42 | 4 | false | true | high |
| Reife / Lagerung | variabel | 5 | true | true | very_high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–5 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 75–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (Vorkultur)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.7 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ / Rosettenstadium

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–700 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kopfbildung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.1 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (gleichmaessige Bodenfeuchtigkeit!) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 600–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Kopfplatzen-Praevention:** Ungleichmaessige Wasserversorgung waehrend der Kopfbildung fuehrt zu Platzen des Kopfes. Gleichmaessig feuchter Boden ist entscheidend. Reife Koepfe durch leichtes Drehen des Strunkbereichs abschneiden (Wurzeln brechen; hemmt Wasseraufnahme).

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Saemling | 2:1:1 | 0.5–0.8 | 6.0–6.5 | 100 | 40 | — | 2 |
| Vegetativ | 3:1:2 | 1.0–1.6 | 6.5–7.0 | 150 | 50 | 20 | 3 |
| Kopfbildung | 2:2:3 | 1.2–1.8 | 6.5–7.0 | 150 | 60 | 30 | 2 |
| Reife | 1:1:3 | 0.8–1.2 | 6.5–7.0 | 100 | 40 | 20 | 1 |

**Bor-Bedarf:** Weißkohl hat wie alle Brassicaceae einen erhoehten Borbedarf. Bormangel fuehrt zu Herz- und Trockenheit (Hohlstiel). 1–2 g Borax/m² als Blattduengung falls Symptome auftreten.

**Kalk-pH-Bedeutung:** Kohlhernie (*Plasmodiophora brassicae*) tritt bei pH < 6.5 auf. Kalk vor der Pflanzung einarbeiten, um pH auf 7.0–7.5 zu heben. Doppelkohlensaurer Kalk (granuliert) ist am wirksamsten.

### 2.4 Phasenubergangsregeln

| Von -> Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung -> Saemling | time_based | 5–7 Tage | Keimblätter sichtbar |
| Saemling -> Vegetativ | time_based | 21–35 Tage | 4–6 Blätter; Auspflanzen nach Abhaertung |
| Vegetativ -> Kopfbildung | event_based | — | Kopfansatz beginnt sich zu schliessen |
| Kopfbildung -> Reife | conditional | — | Kopf fest; Sorte typische Groesse erreicht |

---

## 3. Düngung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Organisch (Outdoor/Beet) — bevorzugt

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch-N | 80–120 g/m² | Pflanzung + 3 Wochen danach | heavy_feeder |
| Kompost reif | eigen | organisch | 5–8 L/m² | Herbst-Einarbeitung | Bodenverbesserung |
| Vinasse-Fluessigduenger | Oscorna Animalin | organisch-fluessig N | 30 ml/10 L | Hauptwachstum | Starkzehrer |
| Gruenguellduenger Bio | Hauert | organisch-komplettduenger | 20 ml/5 L | Kopfbildungsphase | Kohl allg. |

#### Mineralisch (Ergaenzung / schnelle Versorgung)

| Produkt | Marke | Typ | NPK | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Blaukorn | Compo | mineralisch | 12-12-17+2 | 1 | Vegetativ |
| Kali-Magnesia (Patentkali) | K+S | K+Mg | 0-0-30+10 Mg | 1 | Kopfbildung |
| Kalkstickstoff | Perlka | mineralisch-N | 20-0-0 | 1 | Bodenvorber. |
| Borax (Bor-Ergaenzung) | div. | Mikronaehrstoff | — | — | Bei Bormangel |

### 3.2 Duengungsplan

| Woche | Phase | Massnahme | Produkt | Menge | Hinweise |
|-------|-------|----------|---------|-------|----------|
| 0 | Pflanzung | Grundduengung | Kompost + Hornspäne | 6 L/m² + 100 g/m² | Tief einarbeiten (20 cm) |
| 1 | Pflanzung | Kalkgabe falls pH < 6.5 | Dolomitkalk oder Algenkalk | 200–400 g/m² | pH auf 7.0 anheben |
| 4–5 | Vegetativ | Stickstoff-Schub 1 | Hornspäne oder Vinasse | 80 g/m² oder 30 ml/10 L | Blattapparat aufbauen |
| 8–10 | Kopfbild. | Stickstoff-Schub 2 | Hornspäne | 60 g/m² | Letzter N-Schub vor Kopf |
| 10–12 | Kopfbild. | Kaliumgabe | Patentkali | 40 g/m² | Kopffestigkeit + Lagerfaehigkeit |

**N-Gesamtbedarf Weißkohl:** 250–350 kg N/ha (Richtwert nach effizientduengen.de). Aufteilen in 3 Gaben: Grundduengung (30%) + Kopfduengung 1 (40%) + Kopfduengung 2 (30%).

### 3.3 Besondere Hinweise zur Düngung

Weißkohl ist ein extremer Starkzehrer mit dem hoechsten Stickstoffbedarf aller Gemuese-Brassicaceae. Borversorgung ist kritisch — Bormangel zeigt sich als Hohlstiel (braune, korkige Innenflaeche des Strunkbereichs). Bei Stickstoffueberschuss bilden sich lockere, nicht lagerfaehige Koepfe. Herbstkohlsorten brauchen weniger N als Sommerkohlsorten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.3 (Winterkohl braucht kaum Giessen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Gleichmaessig feucht; kein Wasser auf die Koepfe gießen; Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 4, 5, 6, 7, 8, 9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig bis zweijährig) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur starten | Aussaat bei 15–18°C; lichtreich (Fensterbank mit Zusatzlicht) | hoch |
| Mär–Apr | Pikieren | Bei 4 Blättern in 9 cm Toepfe; 12–15°C abhaerten | hoch |
| Apr–Mai | Abhaertung | Jungpflanzen zunehmend ins Freie; Frostschutz nachts | mittel |
| Mai | Auspflanzen (Sommerkohl) | Ab Mitte Mai; 50–60 cm Abstand; Insektennetz sofort! | hoch |
| Jun–Jul | Auspflanzen (Herbstkohl) | Direktsaat oder Vorkultur; Netz erneut | mittel |
| Mai–Sep | Regelmaessig waessern | Gleichmaessige Feuchtigkeit; kein Sprinkler | hoch |
| Jun–Aug | Unkraut jaeten | Flach hacken; Bodenlockerung foerdert Aeration | mittel |
| Jul–Okt | Ernte Sommerkohl | Kopf fest; Schnittstelle beim Strunk | hoch |
| Okt–Dez | Ernte Herbst-/Winterkohl | Spaete Sorten nach Frost noch fester; bis Januar lagern | hoch |
| Okt–Nov | Beetvorbereitung | Gruenduengung oder Kompost einarbeiten; Kohlhernie-Prophylaxe | mittel |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Kohlweissling | Pieris brassicae / P. rapae | Lochfrass; Raupen in/unter Blaettern; weisse Eier-Cluster | leaf | vegetative, heading | easy |
| Kohlfliege | Delia radicum | Welke trotz Waessern; Fraß an Wurzeln; Maden | root, stem_base | seedling, vegetative | difficult |
| Kohleule | Mamestra brassicae | Nachtfrass; Raupen versteckt; Kothaufen | leaf, head | heading | medium |
| Kohlmotte | Plutella xylostella | Minierfraß innen; kleine Schmetterlinge | leaf | vegetative | difficult |
| Grüne Kohlblattlaus | Brevicoryne brassicae | Graue wachsige Kolonien; Schmaechung | leaf, shoot | seedling, vegetative | easy |
| Erdfloehe | Phyllotreta spp. | Winzige Loecher (Schrotschusskrankheit); Adulte springen | leaf | seedling | medium |
| Schnecken | Arion spp. / Deroceras spp. | Grossflaechiger Fraß; Schleimspuren | leaf | seedling | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Kohlhernie | Plasmodiophora brassicae | Ruesselfoermige Wurzelgallen; Welke; Verkuemmerung | pH < 6.5; Staunaesse; befallene Erde | 14–28 | seedling, vegetative |
| Falscher Mehltau | Peronospora parasitica | Gelbliche Blattflecken oben; weisser Belag unten | hohe Luftfeuchtigkeit; kuehles Wetter | 5–10 | seedling, vegetative |
| Ringfleckenkrankheit | Mycosphaerella brassicicola | Konzentrische braune Ringe; gelbe Hoefe | Feuchtigkeit; Waerme | 7–14 | vegetative, heading |
| Grauschimmel | Botrytis cinerea | Grauer Faulbelag; foetige Naesse | Staunaesse; Verletzungen; Kaelte | 3–7 | heading |
| Adernschwärze | Xanthomonas campestris pv. campestris | Schwarze Adern; V-foermige gelbe Flecken | Wärme; Feuchtigkeit; Samen | 5–10 | vegetative, heading |
| Kopffaeule (Schleimfluss) | Erwinia spp. (Bakterien) | Weiche, schleimige Faeulnis im Kopf; foetig | Verletzungen; Feuchtigkeit; Hitzestress | 3–7 | heading |

### 5.3 Nuetzlinge

| Nuetzling | Ziel-Schaedling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Trichogramma brassicae (Schlupfwespe) | Kohlweissling-Eier | 5–10 Karten (je 500 Eier) | 7–14 |
| Bacillus thuringiensis subsp. kurstaki | Raupen allg. (Bt) | Spruehbehandlung 0.5–1% | sofort |
| Cotesia glomerata (Schlupfwespe) | Kohlweissling-Raupen | natuerlich foerdern | — |
| Steinernema carpocapsae (Nematoden) | Kohlfliegen-Larven | 500.000/m² Bewaeserung | 3–7 |
| Orius laevigatus | Thrips | 2–3 | 14 |
| Igel, Kroetenf, Laufkaefer | Schnecken | natuerliche Einwanderer | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Insektenschutznetz | cultural | — | Maschenweite ≤ 0.8 mm; ab Pflanzung dauerhaft | 0 | Kohlfliege, Kohlweissling, Erdfloehe |
| Bacillus thuringiensis | biological | Bt-Toxin | Abends spruehen; bei Raupenbefall | 0 | Raupen allg. |
| Rapsöl-Emulsion | biological | Pflanzenöl | 1% Loesung spruehen | 0 | Blattlaeuse |
| Kalk (Kalkung) | cultural | CaCO3/CaMg(CO3)2 | Boden-pH > 7.0 anheben vor Pflanzung | — | Kohlhernie-Prophylaxe |
| Schneckenkorn Ferramol | biological | Eisenphosphat | 5 g/m² streuen nach Regen | 0 | Schnecken |
| Kupferpraeparate | chemical | Kupferhydroxid | Spruehen bei erstem Befall | 7 | Adernschwärze, Falscher Mehltau |

### 5.5 Resistenzen

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Kohlhernie-Resistenz (CR-Gene; Sorten: Kilaton, Kilaxy) | Krankheit | `resistant_to` |
| Ringflecken-Toleranz (einige Zuechtersorten) | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Kohlgewaechse (Brassicaceae) |
| Empfohlene Vorfrucht | Huelsenfrüchte (Leguminosen: Erbse, Bohne, Klee) |
| Empfohlene Nachfrucht | Schwachzehrer (Salat, Spinat, Zwiebeln) oder Gruenduengung (Phacelia) |
| Anbaupause (Jahre) | 3–4 Jahre (kein Kreuzblütler auf selber Flaeche — Kohlhernie!) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sellerie | Apium graveolens | 0.9 | Kohlfliege-Abwehr durch Duft; gegenseitig foerderlich | `compatible_with` |
| Dill | Anethum graveolens | 0.7 | Nützlinge anlocken; Feindinsekten stören | `compatible_with` |
| Salat | Lactuca sativa | 0.8 | Bodenschutz; Lueckenfuller; wenig Konkurrenz | `compatible_with` |
| Mangold | Beta vulgaris var. cicla | 0.7 | Bodenbeschattung; Naehrstoffergaenzung | `compatible_with` |
| Kamille | Matricaria chamomilla | 0.7 | Nützlingsfoerderung; Bodengesundheit | `compatible_with` |
| Thymian | Thymus vulgaris | 0.8 | Kohlfliegen-Abwehr durch Duft; Bodentrocknen | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Nuetzlingsanlockung; Duftabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Alle anderen Brassicaceae | div. | Gleiche Schaedlinge + Kohlhernie-Risiko; Ressourcen | severe | `incompatible_with` |
| Erdbeere | Fragaria x ananassa | Allelopathische Hemmung; Bodenkonkurrenz | mild | `incompatible_with` |
| Zwiebeln (Sortenabhaengig) | Allium cepa | Teilweise Bodenkonkurrenz; chemische Hemmstoffe | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Brassicaceae | `shares_pest_risk` | Kohlhernie, Kohlweissling, Kohlfliege, Falscher Mehltau | `shares_pest_risk` |

---

## 7. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Weißkohl |
|-----|-------------------|-------------|------------------------------|
| Rotkohl | Brassica oleracea var. capitata f. rubra | Selbe Varient; rote Pigmentierung (Anthocyan) | Anthocyangehalt hoeh (gesundheitsfoerderlich); dekorativ |
| Spitzkohl | Brassica oleracea var. capitata f. alba (Sorten) | Selbe Art; spitzer Kopf | Zarter; frueher Anbau; kuerzere Kulturdauer; Delikatesse |
| Brokkoli | Brassica oleracea var. italica | Gleiche Art; Kopf-Bildung | Naehrstoffreicher; kuerzer Kulturdauer; keine Lagerfaehigkeit |
| Rosenkohl | Brassica oleracea var. gemmifera | Gleiche Art; viele kleine Koepfchen | Sehr winterhart; Ernte bis Januar; dekorativ |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Brassica oleracea var. capitata f. alba,Weißkohl;Weißkabis;White Cabbage,Brassicaceae,Brassica,annual,long_day,herb,taproot,1a–10b,0.0,Atlantik-Europa,limited,30–40,30,30–80,40–70,50–80,no,limited,false,false,heavy_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,days_to_maturity,traits,disease_resistances,seed_type,notes
Kilaton,Brassica oleracea var. capitata f. alba,90–100,clubroot_resistant;heads_firm,Plasmodiophora brassicae,hybrid F1,Kohlhernie-resistent (CR-Gene); Hauptsaison; sehr zu empfehlen
Spitzkohl Kalibos,Brassica oleracea var. capitata f. alba,60–75,pointed_head;early;tender,—,open_pollinated,Fruehe spitze Sorte; zartes Blatt; Delikatesse
Herbstkoenigin,Brassica oleracea var. capitata f. alba,95–120,large_heads;storage_type;hardy,—,open_pollinated,Klassische Lagersorte; bis 10 kg Koepfe moeglich
Quintal d'Alsace,Brassica oleracea var. capitata f. alba,100–120,very_large;storage;traditional,—,open_pollinated,Traditionelle franz. Sorte; bis 15 kg; fuer Sauerkraut
Dithmarscher Fruehkohl,Brassica oleracea var. capitata f. alba,60–75,early;compact;medium_size,—,open_pollinated,Norddeutsche Traditionssorte; frueher Sommerkohl
```

---

## Quellenverzeichnis

1. Plantura — Weißkohl anbauen: Aussaat, Pflege und Erntezeit — https://www.plantura.garden/gemuese/weisskohl/weisskohl-pflanzen
2. Samen.de — Weißkohl Kultivierung: Jahreszeitenguide — https://samen.de/blog/weisskohl-kultivierung-ein-jahreszeitenguide-fuer-hobbygaertner.html
3. Das Gruene Archiv — Weißkohl Anbau und Sorten — https://www.gruenes-archiv.de/weisskohl-anbau-pflege-und-ernte/
4. effizientduengen.de — Kopfkohl N-Bedarfswerte — https://www.effizientduengen.de/sonderkulturen/kopfkohl/
5. Thüringer Landesanstalt für Landwirtschaft (TLL) — Anbautelegramm Kohlarten — https://www.tlllr.de/
6. COMPO Expert — Kohlduengung Spezialempfehlungen — https://www.compo-expert.com/
7. Hortipendium — Weißkohl Pflanzenschutz — https://www.hortipendium.de/
