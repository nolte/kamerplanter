# Sommer-Bohnenkraut — Satureja hortensis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Wikipedia DE – Sommer-Bohnenkraut](https://de.wikipedia.org/wiki/Sommer-Bohnenkraut), [NC State Extension](https://plants.ces.ncsu.edu/plants/satureja-hortensis/), [PFAF Plant Database](https://pfaf.org/user/Plant.aspx?LatinName=Satureja+hortensis), [RHS](https://www.rhs.org.uk/plants/16483/satureja-hortensis/details), [grove.eco Mischkultur](https://www.grove.eco/en/plants/satureja-hortensis/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Satureja hortensis | `species.scientific_name` |
| Volksnamen (DE/EN) | Sommer-Bohnenkraut; Summer Savory | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Satureja | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–11b (annual) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Einjährig — stirbt nach erstem Frost; Winter-Bohnenkraut (S. montana) ist winterhart bis -15°C | `species.hardiness_detail` |
| Heimat | Östliches Mittelmeergebiet, Kleinasien | `species.native_habitat` |
| Allelopathie-Score | 0.2 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis zu verwandten Arten:** Satureja montana (Winter-Bohnenkraut) ist mehrjährig und winterhart bis -15°C. S. hortensis (Sommer-Bohnenkraut) ist einjährig und frostempfindlich. Beide werden in der Küche verwendet; S. montana hat ein intensiveres, schärferes Aroma.

### 1.2 Aussaat- & Erntezeiten

*Für Norddeutschland (Zone 7b–8a), letzter Frost ca. 15. Mai (Eisheiligen).*

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 7–14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 | `species.harvest_months` |
| Blütemonate | 7, 8, 9 | `species.bloom_months` |

**Hinweis:** Direktsaat ist dem Pikieren vorzuziehen, da junge Pflanzen Umpflanzen schlecht vertragen. Sukzessionsaussaat alle 4 Wochen von Mai bis Juli verlängert die Ernteperiode. Beste Aromenqualität kurz vor und zu Blühbeginn — zu diesem Zeitpunkt ernten für Trocknung.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Als einjährige Pflanze ausschließlich durch Samen. Keimtemperatur 18–20°C; Lichtkeimer — Samen nur leicht andrücken, nicht abdecken. Keimung in 10–14 Tagen. Samen 2–3 Jahre keimfähig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Sommer-Bohnenkraut ist als Küchenkraut unbedenklich. Die ätherischen Öle (Carvacrol, Thymol) können in hohen Konzentrationen (Aromatherapie, konzentrierte Extrakte) schleimhautreizend wirken — im normalen Küchengebrauch kein Risiko.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | – | `species.pruning_months` |

**Hinweis:** Als einjährige Pflanze kein klassischer Rückschnitt. Regelmäßiges Ernten/Entspitzen fördert buschiges Wachstum und verzögert das Schossen. Blütenansätze entfernen verlängert die Blatternteperiode.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–25 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20–25 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Kräutererde mit 20–30 % Perlite oder Grobsand; pH 6.5–7.5; keine nährstoffreiche Universalerde | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–14 | 1 | false | false | low |
| Sämling | 14–21 | 2 | false | false | low |
| Vegetativ | 21–35 | 3 | false | true | medium |
| Blüte/Reife | 28–56 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–100 (Lichtkeimer, kein Abdecken) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Substrat feucht halten) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (zwischen Gaben gut abtrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte/Reife

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–28 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–55 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (trockener Standort bevorzugt) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0–0.4 | 6.0–6.5 | – | – | – | – |
| Sämling | 1:1:1 | 0.4–0.8 | 6.0–6.8 | 50 | 20 | – | 1 |
| Vegetativ | 2:1:1.5 | 0.8–1.2 | 6.0–7.0 | 80 | 30 | – | 1.5 |
| Blüte/Reife | 1:1:2 | 0.6–1.0 | 6.0–7.0 | 60 | 25 | – | 1 |

**Hinweis:** Zu viel Stickstoff fördert übermäßiges Blattwachstum auf Kosten des Aromas. Der Carvacrol- und Thymolgehalt ist bei leicht gestresstem, magerbodenwachsendem Bohnenkraut am höchsten. EC-Werte niedrig halten!

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Keimung → Sämling | time_based | 10–14 Tage | Keimblätter vollständig entfaltet |
| Sämling → Vegetativ | time_based | 14–21 Tage | 3–4 echte Blattpaare; Pflanze 5–8 cm |
| Vegetativ → Blüte/Reife | event_based | ab 45–60 Tagen | Erste Blütenknospen sichtbar; Tageslänge nimmt ab |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet — bevorzugt für Kräuter)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost reif | eigen/Gartencenter | organisch | 1–2 L/m² | Frühjahr vor Aussaat | light_feeder |
| Hornspäne | – | organisch | 20–40 g/m² | Einmalig Frühjahr | light_feeder |
| Kräuterdünger | Neudorff Organic Herbs, Substral Naturen | organisch-mineralisch | 1× im Frühjahr | April–Mai | Kräuter allgemein |
| Algenkalk | – | Bodenverbesserer | 100–150 g/m² | Herbst oder Frühjahr | pH-Erhöhung bei saurem Boden |

#### Mineralisch (Topfkultur/Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Terra Grow | Plagron | base | 3-1-3 | 1–1.5 ml/L → EC 0.8–1.0 | 3 | vegetativ |
| Kräuter-Flüssigdünger | Compo, Neudorff | base | 4-3-5 | nach Etikett, 1/4 Dosis | 2 | vegetativ |
| CalMag | Plagron, GHE | supplement | – | 0.5–1 ml/L | 2 | alle |

### 3.2 Düngungsplan (Freiland)

| Zeitpunkt | Phase | Maßnahme | Produkt | Menge | Hinweise |
|-----------|-------|----------|---------|-------|----------|
| Vor Aussaat | – | Grundversorgung | Reifer Kompost | 1–2 L/m² einarbeiten | Ausreichend für die gesamte Saison |
| April/Mai | Sämling | Optional: Startdüngung | Hornspäne | 20–30 g/m² | Nur bei sehr mageren Böden |
| Juni–August | Vegetativ | KEIN Stickstoffdünger | – | – | Zu viel N = artenärmer, weich, pilzanfällig |
| Topf: alle 4 Wochen | Vegetativ | Flüssigdüngung | Kräuter-Flüssigdünger | 1/4–1/3 der empf. Dosis | Wässrig-wüchsig → geringeres Aroma |

### 3.3 Mischungsreihenfolge (Topfkultur, mineralisch)

> **Hinweis:** Bei Kräutern generell konservative EC-Werte anstreben — Aroma entsteht bei leichtem Nährstoffstress.

1. Wasser (Ausgangs-EC messen)
2. CalMag (wenn nötig bei weichem Wasser)
3. Basisdünger
4. pH-Korrektur (IMMER zuletzt) → Ziel pH 6.0–7.0

### 3.4 Besondere Hinweise zur Düngung

Sommer-Bohnenkraut ist ein typischer Magerstandort-Bewohner des Mittelmeerraums. Hohe Nährstoffgaben, besonders Stickstoff, führen zu:
- Geringerem Gehalt ätherischer Öle (Carvacrol, Thymol, p-Cymol)
- Weicherem Gewebe mit erhöhter Pilzanfälligkeit
- Schlechterem Aroma und weniger ausgeprägtem Geschmack

**Empfehlung:** Im Garten reicht eine Kompostgabe vor der Aussaat. In Töpfen sehr niedrig dosieren (1/4 der empfohlenen Dosis), da handelsübliche Kräutererde meist bereits gedüngt ist. Lieber magerer wachsen lassen — das Aroma dankt es.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4–6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | – (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkhaltiges Wasser toleriert; pH 6.5–7.5 bevorzugt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28–42 (sehr niedrig dosiert) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | – (einjährig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Saatgut bestellen | Sorten wählen: klassisch oder „Aromata" | niedrig |
| Mär | Vorkultur (optional) | Aussaat in Anzuchtschalen bei 18–20°C; Lichtkeimer — nicht abdecken | mittel |
| Apr | Vorkultur weiterführen | Pikieren bei 3–4 Blattpaaren; Abstand 5 cm | mittel |
| Mai (nach Eis.) | Direktsaat / Auspflanzen | Direktsaat 1–1.5 cm tief; Reihenabstand 25 cm; Vorkulturen auspflanzen nach Eisheiligen | hoch |
| Mai–Jul | Sukzessionsaussaat | Alle 4 Wochen nachs säen für kontinuierliche Ernte | mittel |
| Jun–Okt | Ernte | Triebspitzen 5–10 cm lang schneiden; vor Blühbeginn für höchstes Aroma; regelmäßig entspitzen | hoch |
| Jul–Aug | Blühbeginn | Wer Samen gewinnen möchte: ein Teil stehen lassen; Blüten für Bestäuber belassen | niedrig |
| Aug–Sep | Samenernte | Reife Samenstände abschneiden, trocknen, dreschen | niedrig |
| Sep–Okt | Trockenernte | Triebe vor erstem Frost für Wintervorrat bündeln und trocknen | mittel |
| Okt–Nov | Ende der Saison | Pflanze stirbt nach erstem Frost; Beete abräumen; Kompostierung | niedrig |

### 4.3 Überwinterung

Sommer-Bohnenkraut ist einjährig und wird nicht überwintert. Die Pflanze stirbt nach dem ersten Frost ab. Für mehrjährige Alternative: Satureja montana (Winter-Bohnenkraut) anpflanzen — überwintert bis -15°C bei Laubschutz.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Schwarze Bohnenlaus | Aphis fabae | Kolonien an Triebspitzen; Honigtau; Verkrümmungen | Triebspitzen, Blätter | vegetativ | easy |
| Grüne Zikaden | Cassida viridis, diverse | Silbrige Stippen auf Blättern; Saugschäden | Blätter | vegetativ, blüte | medium |
| Blattläuse (allgemein) | Aphididae | Klebrige Honigtauschicht; deformierte Blätter | Blätter, Triebe | sämling, vegetativ | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Falscher Mehltau | fungal | Hellgelbe Flecken oben, grauer Belag unten | hohe Luftfeuchte, Staunässe, Nässe | 5–10 | sämling, vegetativ |
| Grauschimmel | fungal | Grauer, watteartiger Pilzbelag; Fäulnis | kühle feuchte Witterung, enge Pflanzung | 3–7 | sämling, vegetativ |
| Wurzelfäule | fungal | Welke bei ausreichend Wasser; braune Wurzeln | Staunässe, schwerer Boden | 5–14 | alle |
| Rost | fungal | Orangebraune Pusteln auf Unterseite | Nässe, Wärme | 7–14 | blüte |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse allgemein | natürliche Population fördern | sofort |
| Chrysoperla carnea (Florfliege) | Schwarze Bohnenlaus, Blattläuse | 5–10 Larven/m² | 7–14 |
| Schlupfwespen (Aphidius colemani) | Blattläuse | 5–10/m² | 14–21 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% Sprühlösung, abends | 3 | Blattläuse, Zikaden |
| Kaliseife (Schmierseife) | biological | Kaliumoleat | 1–2% Sprühlösung | 1 | Blattläuse |
| Befallene Triebe entfernen | cultural | – | Abschneiden, entsorgen | 0 | Blattläuse, Mehltau |
| Weiter Pflanzabstand | cultural | – | 20–25 cm Abstand einhalten | 0 | Mehltau, Grauschimmel |
| Trocken gießen | cultural | – | Nur Bodenguss, kein Überbrausen | 0 | Falscher Mehltau, Grauschimmel |
| Kupferkalkbrühe | chemical | Kupferhydroxid | Sprühen bei ersten Symptomen | 14 | Falscher Mehltau |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Trockenheit | Stresstoleranz | `resistant_to` |
| Wärme | Stresstoleranz | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Kräuter / Labiaten |
| Empfohlene Vorfrucht | Hülsenfrüchte (Fabaceae) oder Brassicaceae; beliebig als Begleitpflanze |
| Empfohlene Nachfrucht | Beliebig — Bohnenkraut verbessert Bodenstruktur kaum, stört aber nicht |
| Anbaupause (Jahre) | 2–3 Jahre Pause für Lamiaceae auf gleicher Fläche (Bodenmüdigkeit, Welke-Pilze) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Bohne | Phaseolus vulgaris | 1.0 | Klassische Partnerschaft: hält Schwarze Bohnenlaus fern; verbessert Bohnengeschmack | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.8 | Repellent-Effekt gegen diverse Schadinsekten durch ätherische Öle | `compatible_with` |
| Zwiebel | Allium cepa | 0.8 | Gegenseitige Schädlingsabwehr; Platzsparend | `compatible_with` |
| Gurke | Cucumis sativus | 0.7 | Stärkung der Gurke; Schädlingsabwehr | `compatible_with` |
| Kohl | Brassica oleracea | 0.7 | Kohlweißling- und Kohlfliegenschutz durch ätherische Öle | `compatible_with` |
| Rose | Rosa spp. | 0.6 | Reduziert Mehltaubefall auf Rosen (empirisch beobachtet) | `compatible_with` |
| Möhre | Daucus carota | 0.7 | Möhrenfliegen-Verwirrung durch Duft | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Konkurrenz um Wasser und Nährstoffe; ähnliche Duftöle, kein Synergie-Effekt | mild | `incompatible_with` |
| Liebstöckel | Levisticum officinale | Liebstöckel wächst sehr dominant und beschattet Bohnenkraut; allelopathischer Verdacht | moderate | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathie: Fenchel hemmt viele Küchenkräuter | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Lamiaceae (alle) | `shares_pest_risk` | Echter/Falscher Mehltau, Bodenmüdigkeit bei enger Fruchtfolge | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Satureja hortensis |
|-----|-------------------|-------------|--------------------------------------|
| Winter-Bohnenkraut | Satureja montana | Gleiches Genus, ähnliches Aroma | Mehrjährig, winterhart bis -15°C; einmal pflanzen, viele Jahre ernten |
| Thymian | Thymus vulgaris | Lamiaceae, ähnliches Aroma, gleiche Kücheneinsatze | Sehr winterhart, mehrjährig; vielseitiger in der Küche |
| Oregano | Origanum vulgare | Lamiaceae, Mittelmeer, ätherische Öle | Mehrjährig; intensiveres Aroma für mediterrane Küche |
| Majoran | Origanum majorana | Nächster Verwandter; ähnliches Verwendungsprofil | Intensiveres, süßlicheres Aroma; komplementär zu Bohnenkraut |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Satureja hortensis,Sommer-Bohnenkraut;Summer Savory,Lamiaceae,Satureja,annual,long_day,herb,taproot,3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b;11a;11b,0.2,Östliches Mittelmeer; Kleinasien,yes,1,15,20,25,20,limited,yes,false,false
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Aromata,Satureja hortensis,–,–,compact;high_aroma_oil,55–65,–,open_pollinated
Saturn,Satureja hortensis,–,–,high_yield;aromatic,60–70,–,open_pollinated
```

---

## Quellenverzeichnis

1. [Wikipedia DE — Sommer-Bohnenkraut](https://de.wikipedia.org/wiki/Sommer-Bohnenkraut) — Taxonomie, Botanik, Inhaltsstoffe
2. [NC State Extension — Satureja hortensis](https://plants.ces.ncsu.edu/plants/satureja-hortensis/) — Kulturbedingungen, Boden, Licht
3. [PFAF Plant Database — Satureja hortensis](https://pfaf.org/user/Plant.aspx?LatinName=Satureja+hortensis) — Mischkultur, Anbau, Verwertung
4. [Royal Horticultural Society (RHS)](https://www.rhs.org.uk/plants/16483/satureja-hortensis/details) — Kultivierungshinweise
5. [grove.eco — Nachbarn und Fruchtfolge](https://www.grove.eco/en/plants/satureja-hortensis/) — Mischkultur-Daten, Aussaatzeiten
6. [Harvest to Table — Savory Growing Guide](https://harvesttotable.com/how_to_grow_savory/) — Wachstumsphasen, Ernte
7. [GartenVielfalt — Satureja hortensis](https://www.garten-vielfalt.de/de-de/gartenwelt/pflanzeninfothek/pflanzen/1313/satureja-hortensis) — Anbau Norddeutschland, Praxis
