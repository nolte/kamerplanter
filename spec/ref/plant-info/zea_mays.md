# Mais (Zuckermais) — Zea mays

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Plantura Mais Anbau, Samen.de Maisanbau-Anleitung und Klimabedingungen, Meine-Ernte Zuckermais, Wikipedia Maize, USDA PLANTS Zea mays, Gartenpaten Mais, Samen.de Mischkultur mit Mais

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Zea mays | `species.scientific_name` |
| Volksnamen (DE/EN) | Mais, Zuckermais, Koemelkolben; Maize, Corn, Sweet Corn | `species.common_names` |
| Familie | Poaceae | `species.family` -> `botanical_families.name` |
| Gattung | Zea | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (Zuckermais-Sorten; Wildtyp urspruenglich short_day) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a; 2b; 3a; 3b; 4a; 4b; 5a; 5b; 6a; 6b; 7a; 7b; 8a; 8b; 9a; 9b; 10a; 10b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Keimung erst ab +10°C Bodentemperatur. Froezte vernichten Jungpflanzen. Ausgewachsene Pflanzen sterben nach dem ersten Herbstfrost ab. | `species.hardiness_detail` |
| Heimat | Mesoamerika (Mexico, Guatemala) — kultiviert seit ca. 9000 Jahren | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Naehrstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gruenduengung geeignet | false | `species.green_manure_suitable` |
| Traits | edible | `species.traits` |

**Besonderheit C4-Photosynthese:** Mais nutzt den C4-Photosyntheseweg (im Gegensatz zum C3-Weg der meisten Gemuese). C4-Pflanzen sind deutlich effizienter bei hoher Lichtintensitaet, Hitze und trockenem Wetter. Mais kann bei 1000–2000 µmol/m²/s PPFD noch effektiv photosynthetisieren (kein Lichtsaettigungspunkt wie bei C3-Pflanzen).

### 1.2 Aussaat- & Erntezeiten

Angaben fuer Mitteleuropa (Zone 7–8).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 2–3 (optional; direkte Uebertragung schlecht — Mais mag kein Umpflanzen) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (nach Eisheiligen; Bodentemperatur min. 10°C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5; 6 (frueh ist besser) | `species.direct_sow_months` |
| Erntemonate | 7; 8; 9 (sortenabhaengig; Zuckermais 70–90 Tage nach Aussaat) | `species.harvest_months` |
| Bluetemonate | 7; 8 (Maennliche Rispe oben blueht zuerst; weibliche Faeden an Kolben folgen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Keimhinweise:**
- Optimale Keimtemperatur: 18–25°C (Bodentemperatur min. 10°C)
- Keimdauer: 4–10 Tage
- Saattiefe: 3–5 cm
- Pflanzabstand: 30–40 cm in der Reihe; 50–70 cm Reihenabstand
- **Wichtig fuer Bestaeubing:** Mais ist windbestaeubt. Mindestens 4–5 Reihen in einem Block pflanzen (nicht in langen Einzelreihen), damit die Pollen die weiblichen Blueten (Faeden/Narben am Kolben) erreichen. Zu wenig Pollen-Kontakt fuehrt zu lueckigen Kolben.
- Zuckermais separat von Koernermais und Popcorn-Mais pflanzen (Kreuzbestaeubing veraendert den Zuckergehalt)

### 1.4 Toxizitaet & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig fuer Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig fuer Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig fuer Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Maispollen koennen Allergien ausloesen; hohe Pollenkonzentration) | `species.allergen_info.pollen_allergen` |

### 1.5 Rueckschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rueckschnitt-Typ | none | `species.pruning_type` |
| Rueckschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rueckschnitt erforderlich. Ausser: Seitentriebe ("Geizaugen"/Seitenkolben) koennen bei schwachen Sorten entfernt werden um den Hauptkolben zu staerken — bei modernen Sorten nicht noetig.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no (zu grosser Platzbedarf; tiefe Bewaesserung noetig; ungeeignet fuer Bestaeubing) | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 (falls unbedingt versucht) | `species.min_container_depth_cm` |
| Wuchshoehe (cm) | 150–250 (Zuckermais); 200–300 (Futterkoernermais) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 30–40 (innerhalb Reihe); 50–70 (Reihenabstand) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewaechshaus empfohlen | false (Bestaeubing problematisch) | `species.greenhouse_recommended` |
| Rankhilfe/Stuetze noetig | false (standfest; aber bei Sturm unterstuetzen: Anhaeufen um Stumpf) | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (keine Topfkultur empfohlen) | -- |

**Freiland-Substrat:** Tiefgruendiger, warmer Boden mit guter Wasserspeicherung und Drainage. pH 6.0–7.0. Humusreicher Lehmboden ist ideal. Sandige Boeden benoetigen mehr Waesserung und Duengung.

---

## 2. Wachstumsphasen

### 2.1 Phasenuebersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 4–10 | 1 | false | false | low |
| Saemling (VE1–V4) | 14–21 | 2 | false | false | low |
| Vegetativ / Blattetagen (V5–VT) | 30–45 | 3 | false | false | medium |
| Rispenblüte / Bestaeubing (VT–R1) | 7–14 | 4 | false | false | high |
| Kolbenbildung / Milchreife (R1–R3) | 14–28 | 5 | false | true | medium |
| Teig-/Vollreife (R4–R6) | 14–28 | 6 | true | true | high |

**BBCH-Hinweis:** Maisphysiologie wird in der Landwirtschaft nach dem V/R Staging-System (Vegetative/Reproductive Stages) oder dem BBCH-Code beschrieben.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–100 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 (im Boden) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (Boden gleichmaessig feucht) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 (Bereich um Saatkorn) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Saemling (VE bis V4)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 13–16 (Outdoor Tageslicht) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (V5 bis VT)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 800–2000 (C4-Pflanze; kein Lichtsaettigungspunkt!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 40–60 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 13–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (tiefgruendig; 30–40 cm tief) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Bestaeubing / Rispenblüte (VT bis R1)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 800–2000 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 40–60 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 13–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (kritische Phase; Wasserdefizit = Luecken im Kolben) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Kritische Phase:** Blaete und Bestaeubing ist die wasserempfindlichste Phase. Trockenheitsstress waehrend der Fadenbildung (Silking) fuehrt direkt zu Ertragsausfaellen (fehlende Koerner = "skip rows").

#### Phase: Kolbenbildung / Milchreife (R1–R3)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 35–50 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO2 (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 800–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Naehrstoffprofile je Phase

| Phase | NPK-Verhaeltnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Saemling | 2:1:1 | 0.5–0.8 | 6.0–7.0 | 80 | 30 | 15 | 2 |
| Vegetativ | 4:1:2 | 1.0–1.8 | 6.0–7.0 | 150 | 50 | 25 | 3 |
| Bestaeubing | 3:2:3 | 1.2–2.0 | 6.0–7.0 | 130 | 60 | 25 | 2 |
| Kolbenbildung | 1:2:4 | 1.0–1.6 | 6.0–7.0 | 100 | 50 | 20 | 2 |
| Reife | 0:1:2 | 0.6–1.0 | 6.0–7.0 | 60 | 30 | 15 | 1 |

**Stickstoff-Bedarf:** Mais hat den hoechsten N-Bedarf aller haeufigen Gartengemuese. Ca. 200–250 kg N/ha im Landwirtschaftsmassstab. Im Hausgarten entspricht dies ca. 20–25 g N/m².

### 2.4 Phasenubergangsregeln

| Von -> Nach | Trigger | Tage | Bedingungen |
|------------|---------|------|-------------|
| Keimung -> Saemling | time_based | 4–10 Tage | Erstes Blatt durchstoesst Boden (VE) |
| Saemling -> Vegetativ | time_based | 14–21 Tage | 4–5 Blätter entfaltet (V4–V5) |
| Vegetativ -> Bestaeubing | event_based | — | Rispe (Tassel) voll entfaltet; Pollen freigesetzt |
| Bestaeubing -> Kolbenbildung | time_based | 7–14 Tage | Seidenfäden braun; Kolbenansatz wächst |
| Kolbenbildung -> Ernte | conditional | 18–25 Tage | Milchreife: Koerner milchig-weiss; Seidenfäden braun-vertrocknet |

---

## 3. Düngung & Naehrstoffversorgung

### 3.1 Empfohlene Duengerprodukte

#### Organisch (Outdoor/Beet) — bevorzugt fuer Hausgarten

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet fuer |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch-N | 100–150 g/m² | Vor Aussaat + 4 Wochen danach | heavy_feeder |
| Stallmist (verrottet) | eigen | organisch | 3–5 kg/m² | Herbst-Einarbeitung | Bodenverbesserung |
| Kompost | eigen | organisch | 5–8 L/m² | Herbst/Fruehjahr | Humus-Aufbau |
| Biobizz Grow | Biobizz | organisch-fluessig | 2–4 ml/L | Vegetative Phase | Starkzehrer |

#### Mineralisch (Ergaenzung)

| Produkt | Marke | Typ | NPK | Mischprioritaet | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Maisduenger | Agrosil/Haifa | mineralisch komplex | 15-15-15+Mg | 1 | Aussaat-Vorbereitung |
| Kalkammonsalpeter (KAS) | div. | mineralisch-N | 27-0-0 | 1 | Vegetativ (Kopfduengung) |
| Patentkali (K+Mg) | K+S | mineralisch-K | 0-0-30+10Mg | 1 | Kolbenbildung |

### 3.2 Düngungsplan

| Woche | Phase | Massnahme | Produkt | Menge | Hinweise |
|-------|-------|----------|---------|-------|----------|
| 0 (Herbst) | Vorbereitung | Grundduengung | Stallmist + Kompost | 3 kg/m² + 5 L/m² | Herbsteinarbeitung |
| 0 | Aussaat | Startduenger | Hornspäne | 120 g/m² | Flaechig einarbeiten |
| 4 | Saemling | Stickstoff-Booster | Hornspäne oder Flüssig-N | 80 g/m² oder Giesskanne | Erste Kopfduengung |
| 6–7 | Vegetativ | Zweite Kopfduengung | Hornspäne oder KAS | 60–80 g/m² | Vor Rispenschieben |
| 9–10 | Kolbenbildung | Kaliumgabe | Patentkali | 30–40 g/m² | Lagerf., Kolbenqualitaet |

### 3.3 Besondere Hinweise zur Düngung

Mais ist ein klassischer Starkzehrer. Der hohe N-Bedarf wird am besten mit organischen Duengern gedeckt (Hornspäne, Stallmist). Bohnen als Dreischwestern-Partner fixieren Stickstoff und reduzieren den Duengerbedarf erheblich. Mais zeigt fruehzeitig N-Mangel an: Blätter werden hellgruen bis gelb, beginnend von der Blattspitze, V-foermig (Stickstoff-Mangelsymptom). Zink-Mangel zeigt sich als weiß-gestreifte Blaetter.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 (tief waessern; nicht flach und haeufig) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualitaet-Hinweis | Tiefgruendige Bewaesserung; Wurzeln gehen bis 150 cm tief; Verdunstungsschutz durch Mulchen | `care_profiles.water_quality_hint` |
| Duengeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Duenge-Aktivmonate | 5, 6, 7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig; kein Umtopfen) | `care_profiles.repotting_interval_months` |
| Schaedlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitspruefung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Prioritaet |
|-------|---------------|--------------|-----------|
| Apr | Bodentemperatur pruefen | Direktsaat erst ab 10°C Bodentemperatur | hoch |
| Mai (nach 15.) | Direktsaat | 3–5 cm tief; 30–40 cm Abstand in Reihen; 5–7 Reihen fuer Bestaeubing | hoch |
| Mai–Jun | Giessen und Abdecken | Gleichmaessig feucht bis Keimung; Voegel sind Bedrohung — Saatgut abdecken | mittel |
| Jun | Ausduennen | Auf staerkste Pflanze pro Saatpunkt ausduennen; schwache Konkurrenten entfernen | mittel |
| Jun–Jul | Erde anhaeufen | Stahl um Stumpf anhaeufen wenn 50 cm hoch (Standfestigkeit + Luftwurzeln) | mittel |
| Jun–Aug | Tiefes Giessen | Besonders vor und waehrend Rispenblüte kritisch! | hoch |
| Jul | Bestaeubing pruefen | Haelt die Rispe Pollen bereit? Seidenfaeden der Kolben? | mittel |
| Aug–Sep | Ernte Zuckermais | Milchreife: 18–25 Tage nach Bestaeubing; Schalen noch gruen; Koerner milchig | hoch |

---

## 5. Schaedlinge & Krankheiten

### 5.1 Haeufige Schaedlinge

| Schaedling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfaellige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Maiszuensler | Ostrinia nubilalis | Bohrloecher im Stengel; Raupen fressen sich durch; Stengel bricht | stem, ear | vegetative, reproductive | difficult |
| Maisblaetterblattlaus | Rhopalosiphum maidis | Kolonie an Blaettern; Honigtau | leaf, ear | vegetative | medium |
| Fritfliege | Oscinella frit | Herz-Blatt wird gelb und fault ("Totes Herz") | shoot | seedling | medium |
| Drahtwurm | Agriotes spp. (Elateridae) | Keimling von unten angefressen; Lueeken in Reihen | root, stem_base | seedling | difficult |
| Voegel (Kraehen, Tauben) | div. | Saatgut ausgraben; Koerner aus Kolben picken | seed, ear | germination, ripening | easy |
| Maiszapfenruesskaefer | Rhynchophorus ferrugineus (europ. Art: Sitophilus zeamais) | Fraß im Kolben | ear | ripening | difficult |
| Wildschwein | Sus scrofa | Vollstaendige Vernichtung; Umbruch ganzer Reihen | ear, whole plant | ripening | easy |

### 5.2 Haeufige Krankheiten

| Krankheit | Erregertyp | Symptome | Ausloser | Inkubation (Tage) | Anfaellige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Maisbeulenbrand | Ustilago maydis | Grosse graue-weisse Beulen an Kolben, Blaettern, Stengeln | Verletzungen; Duerre-Stress | 7–14 | vegetative, reproductive |
| Maisblaetterduerre (Northern Corn Leaf Blight) | Setosphaeria turcica | Laengliche braune Blattflecken | Feuchtes Wetter | 5–10 | vegetative |
| Pythium-Sämlingskrankheit | Pythium spp. | Keimling fault im Boden; schlechte Keimrate | Kalte, nasse Boeden | 3–7 | germination, seedling |
| Stengelfaeule | Fusarium graminearum | Rosafarbene Faerbung des Stengel-Inneren; Umfallen | Stressbedingungen | 7–14 | reproductive |
| Kolbenfaeule | Fusarium verticillioides | Rosa-weisser Schimmel an Koernern | Feuchtes Erntewetter; Insektenfrass | 5–14 | ripening |

### 5.3 Nuetzlinge

| Nuetzling | Ziel-Schaedling | Ausbringrate | Etablierungszeit (Tage) |
|----------|---------------|-------------|------------------------|
| Trichogramma brassicae | Maiszünsler-Eier | 5–10 Karten/100m² | 7–14 |
| Bacillus thuringiensis var. kurstaki | Raupen allg. | Spruehbehandlung | sofort |
| Chrysoperla carnea (Florfliegenlarve) | Blattlaeuse | 5–10 Larven/m² | 7 |
| Raubkaefer (Carabidae) | Drahtwurm, Schnecken | natuerl. foerdern | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Vogelnetz / Drahtgeflecht | cultural | — | Saatgut abdecken bis Keimung | 0 | Voegel |
| Trichogramma-Karten | biological | Parasitoide Eier | Karten ans Blatt heften; 2x im Abstand 7 Tage | 0 | Maiszuensler |
| Bacillus thuringiensis | biological | Bt-Toxin | Spruehen wenn Raupen sichtbar | 0 | Maiszuensler-Raupen |
| Sortenwahl | cultural | — | Maisbrandresistente Hybriden waehlen | — | Ustilago-Praevention |
| Fruchtfolge | cultural | — | Mais nicht oefters als jedes 3. Jahr | — | Fusarium, Ustilago |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Naehrstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Suessgräser (Poaceae) |
| Empfohlene Vorfrucht | Huelsenfrüchte (Leguminosen: Bohne, Erbse, Luzerne) |
| Empfohlene Nachfrucht | Schwachzehrer oder Gruenduengung (Phacelia, Senf) |
| Anbaupause (Jahre) | 2–3 Jahre (Fusarium, Beulenbrand-Sporen im Boden) |

### 6.2 Drei-Schwestern-Mischkultur (Milpa)

Die Drei-Schwestern-Mischkultur ist das bekannteste und wirkungsvollste Mischkultursystem fuer Mais:

| Partner | Wissenschaftl. Name | Rolle | Nutzen |
|---------|-------------------|-------|--------|
| Stangenbohne | Phaseolus vulgaris (Klett.) | Schleicher | N-Fixierung; klettert am Mais hoch; keine Konkurrenz |
| Kuerbis | Cucurbita pepo / C. maxima | Bodendecker | Beschattet Boden; haelt Feuchtigkeit; stachelige Blaetter halten Schaedlinge fern |

### 6.3 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitaets-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Stangenbohne | Phaseolus vulgaris | 1.0 | N-Fixierung; symbiotisch (Drei Schwestern) | `compatible_with` |
| Kuerbis / Zucchini | Cucurbita spp. | 0.9 | Bodenbeschattung; Unkrautunterdrueckung (Drei Schwestern) | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematoden-Abwehr; Bestaeuberforderung | `compatible_with` |
| Borretsch | Borago officinalis | 0.7 | Bestaeuberforderung; Boden-Kali-Foerderung | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Untersaat; nutzt Schatten; Lueckenfüller | `compatible_with` |
| Dill | Anethum graveolens | 0.6 | Nuetzlingsanlockung; Bestaeuber | `compatible_with` |

### 6.4 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Konkurrenz um Licht + Naehrstoffe; geteilte Schaedlinge | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung aller Nachbarn | severe | `incompatible_with` |
| Rote Beete | Beta vulgaris | Bodekonkurrenz; hemmende Ausscheidungen | mild | `incompatible_with` |

### 6.5 Familien-Kompatibilitaet

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|-----------------|---------|
| Poaceae | `shares_pest_risk` | Maiszuensler, Fusarium, Ustilago | `shares_pest_risk` |

---

## 7. Ernte-Indikatoren Zuckermais

**Richtige Ernte-Indikatoren (kritisch fuer Zuckermais):**
- Seidenfäden (Narben) sind braun-vertrocknet (ca. 18–25 Tage nach Bestaeubing)
- Schalen sind noch grün und feucht
- Beim Einstechen eines Korns tritt milchig-weisser Saft aus (Milchreife R3)
- Finger-Nageltest: Koerner geben nach; keine glasige, haerte Schale
- Kolben ist vollstaendig ausgebildet; Kolbenhülle eng anliegend
- **Nie ueberreif ernten:** Koerner werden mehlig und Zucker wandelt sich in Staerke um. Zuckermais innerhalb von 24 Stunden nach Ernte verbrauchen oder kuehlstellen!

---

## 8. Aehnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Aehnlichkeit | Vorteil gegenueber Zuckermais |
|-----|-------------------|-------------|------------------------------|
| Super-Sweet-Mais (Sh2-Gen) | Zea mays var. saccharata (Sh2) | Selbe Art; anderer Zuckergen | Noch suesser; laengere Haltbarkeit nach Ernte |
| Popcorn | Zea mays var. everta | Selbe Art; Popcorn-Verwendung | Dekorativ; getrocknete Kolben; Lagerfaehig |
| Bunte Ziermais | Zea mays var. japonica | Selbe Art; Dekoration | Dekorativ; Ziermotiv fuer Herbst |
| Teosinte (Vorfahre) | Zea mays subsp. mexicana | Stammform; kein Kolben | Historisch interessant; nicht fuer Garten geeignet |

---

## 9. CSV-Import-Daten (KA REQ-012 kompatibel)

### 9.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Zea mays,Mais;Zuckermais;Maize;Sweet Corn,Poaceae,Zea,annual,short_day,herb,fibrous,2a–10b,0.1,Mesoamerika,no,—,50,150–250,30–50,30–40,no,no,false,false,heavy_feeder
```

### 9.2 Cultivar CSV-Zeilen

```csv
name,parent_species,days_to_maturity,traits,seed_type,notes
Goldrush,Zea mays,70–75,sweet;yellow_kernels;good_yield,hybrid F1,Klassischer Zuckermais; gelbe Koerner; sehr beliebt
Bicolor Mirai,Zea mays,70–80,bicolor_yellow_white;super_sweet;sh2,hybrid F1,Zweifarbig; extra-suss; laengere Haltbarkeit
Strawberry Popcorn,Zea mays,100–110,red_kernels;popcorn;decorative,open_pollinated,Kleiner roter Kolben; Popcorn + Deko
Blaue Hopi,Zea mays,90–100,blue_kernels;traditional;heirloom,open_pollinated,Traditionelle Hopi-Sorte; blau-lila Koerner; Mehlmais
Noa (suedtirol),Zea mays,85–95,yellow;field_corn;regional,open_pollinated,Regionaler Feldmais; traditionell Suedtirol
```

---

## Quellenverzeichnis

1. Plantura — Mais pflanzen: Anbau, Pflege und Erntezeit — https://www.plantura.garden/gemuese/mais/mais-pflanzen
2. Samen.de — Schritt-fuer-Schritt Anleitung zum Maisanbau — https://samen.de/blog/anleitung-maisanbau-fuer-jedermann-von-der-saat-bis-zur-ernte.html
3. Samen.de — Optimale Klimabedingungen fuer Mais — https://samen.de/blog/optimale-klimabedingungen-fuer-mais.html
4. Samen.de — Mischkultur mit Mais: Partnerpflanzen fuer reiche Ernte — https://samen.de/blog/mischkultur-mit-mais-partnerpflanzen-fuer-reiche-ernte.html
5. Meine-Ernte — Zuckermais anbauen, pflegen, ernten und lagern — https://www.meine-ernte.de/pflanzen-a-z/gemuese/zuckermais/
6. Gartenpaten — Mais vom Kern zum Kolben — https://www.gartenpaten.org/tipps-tricks/mais-vom-kern-zum-kolben
7. Wikipedia — Maize/Zea mays — https://en.wikipedia.org/wiki/Maize
