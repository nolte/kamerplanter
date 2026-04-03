# Dahlie 'Hapet Daydream' — Dahlia 'Hapet Daydream'

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:** RHS Plant Finder, ASPCA Toxic Plant Database, UC IPM Dahlia, Missouri Botanical Garden, American Dahlia Society, Longfield Gardens, Old Farmer's Almanac, Plantura.garden, PFAF Database, Dahlia Doctor

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dahlia pinnata Cav. | `species.scientific_name` |
| Volksnamen (DE/EN) | Dahlie 'Hapet Daydream'; Dahlia 'Hapet Daydream' | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Dahlia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | `herb` (krautig, aufrecht; Knollenstaude) | `species.growth_habit` |
| Wurzeltyp | `tuberous` (speichernde Knollenwurzeln; bilden jährlich neue Tochterknolle) | `species.root_type` |
| Lebenszyklus | `perennial` (botanisch mehrjährig durch Knollen; in Zone 7 und kälter als frostempfindliche Pflanze behandelt — Knollen jährlich ausgraben) | `lifecycle_configs.cycle_type` |
| Photoperiode | `short_day` (fakultativ; Blüteninitiierung bei Nachtlänge > 12 h gefördert, Dahlien blühen jedoch auch unter Langtagbedingungen; Tuberisierung eindeutig kurztaggesteuert bei Nacht > 12 h) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a (Freiland-Überwinterung der Knollen; in Zone 7 mit dichter Mulchschicht grenzwertig möglich) | `species.hardiness_zones` |
| Frostempfindlichkeit | `tender` (oberirdische Teile sterben bei leichtem Frost; Knollen überstehen kurze Bodenfröste bis ca. -5 °C — in Zone 7 und kälter ausgraben) | `species.frost_sensitivity` |
| Winterhärte-Detail | Kraut friert bereits bei leichtem Frost (0 °C bis -2 °C) ab. Knollen im Boden überstehen nur Zonen 8–11 zuverlässig. In Mitteleuropa (Zone 7–8): Knollen nach erstem Frost ausgraben, trocken bei 5–10 °C lagern, im Mai wieder auspflanzen. | `species.hardiness_detail` |
| Heimat | Elternarten stammen aus den Hochlagen Mexikos (1.800–3.000 m, kühle Eichen-/Kiefernwälder). Züchtungsursprung: Niederlande, ca. 2020 | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral — keine bekannten allelopathischen Wirkungen bei Dahlien) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | `heavy_feeder` (Starkzehrer — hoher Bedarf, besonders in der Blütephase; Kalium und Phosphor besonders wichtig) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | `['ornamental', 'bee_friendly', 'fragrant']` (dekorativer Schnittblumen-Dauerblüher, Bienenweide, leicht duftend) | `species.traits` |

**Sortenspezifika 'Hapet Daydream':**
- Blütentyp: Dekorative Dahlie (Decorative type), mit Tendenz zum Pompon/Ball-Typ (Blütendurchmesser 8–9 cm)
- Farbe: Vivid Fuchsia-Pink mit goldenem bis cremefarbenem Zentrum; RHS-Farbcode: strong purplish red 61B (Oberseite), brilliant greenish yellow 2B (Basis)
- Wuchshöhe: 100–120 cm; Wuchsbreite: ca. 60–70 cm
- Blütezeit: Juli bis zum ersten Frost (typisch November)
- Eingeführt: Niederlande, ca. 2020 (noch selten im deutschen Fachhandel)

### 1.2 Aussaat- & Erntezeiten

Mitteleuropa (Zone 7–8), Bezugspunkt: letzter Frost Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Knollen ab März/April vorkeimen; Aussaat aus Samen unüblich bei Sorten-Dahlien, da keine Sortenechte Reproduktion) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 (Knollen direkt nach letztem Frost auspflanzen, ab Bodentemperatur ≥ 12 °C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (Mai–Juni, nach letztem Frost) | `species.direct_sow_months` |
| Erntemonate | null (Zierpflanze / Schnittblume, keine Ernte im Nutzpflanzen-Sinne; `allows_harvest: false`. Schnittblumen-Ernte kontinuierlich Juli–Oktober) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 (Hauptblüte Juli bis Oktober; bei Frostschutz bis November) | `species.bloom_months` |

**Hinweis zur Vorkultur:** Knollen von 'Hapet Daydream' können ab Ende März in Töpfen (Ø 15 cm) unter Glas vorgekeimt werden, um 3–4 Wochen Blütezeit zu gewinnen. Vorkeimtemperatur: 15–18 °C.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | `tuberous` (Knollenteilung), `cutting_stem` (Stecklinge aus Vortrieb), `seed` (nur bei Artdahlien / nicht sortenecht) | `species.propagation_methods` |
| Schwierigkeit | `easy` (Knollenteilung ist Standard und zuverlässig; Stecklinge moderat) | `species.propagation_difficulty` |

**Knollenteilung (empfohlene Methode):**
- Zeitpunkt: März/April beim Vorkeimen oder Auspflanzen
- Jedes Teilstück muss mindestens 1 Augenpunkt (Knospe) und einen Abschnitt der Hauptknolle tragen
- Schnittflächen mit Holzkohle oder Fungizid-Pulver behandeln

**Stecklinge:**
- Zeitpunkt: Februar/März, wenn Triebe 8–10 cm Länge erreicht haben
- Substrat: Torffreie Anzuchterde + 30 % Perlite
- Bewurzelung: 3–4 Wochen bei 18–20 °C unter Folie
- Kein Blütenansatz im ersten Jahr garantiert

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (ASPCA: Dahlien sind für Katzen giftig — milde gastrointestinale Symptome) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (ASPCA: Dahlien sind für Hunde giftig — milde gastrointestinale Symptome) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (RHS: Keine dokumentierten Toxizitätsfälle beim Menschen) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Pflanzenteile, insbesondere Blätter, Stängel und Knollen | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Sesquiterpen-Laktone (nicht vollständig identifiziert); ätherische Öle und saure Reizstoffe (Asteraceae-typisch) | `species.toxicity.toxic_compounds` |
| Schweregrad | `mild` (leichte GI-Symptome: Erbrechen, Durchfall, Speichelfluss; Hautrötung bei Kontakt möglich) | `species.toxicity.severity` |
| Kontaktallergen | true (Sesquiterpen-Laktone können Kontaktdermatitis bei empfindlichen Personen auslösen — typisch für Asteraceae) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzreaktionen mit anderen Asteraceae wie Chrysantheme, Kamille möglich; Entomophilie verringert Luftpollen-Belastung) | `species.allergen_info.pollen_allergen` |

Quellen: ASPCA Toxic Plant Database, RHS, Wagwalking.com Dahlia Poisoning

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | `none` (kein Formschnitt; stattdessen kontinuierliches Ausgeizen und Deadheading während der Vegetationsperiode) | `species.pruning_type` |
| Rückschnitt-Monate | null | `species.pruning_months` |

**Pinching (Herzausbrechen):** Obligatorisch bei Sorten-Dahlien dieser Größe. Nach Erreichen von 5–6 Blattpaaren den Haupttrieb über dem 3.–4. Blattknoten kappen. Ergebnis: 4–6 Seitentriebe, buschigerer Wuchs, mehr Blüten. Zeitpunkt: 2–3 Wochen nach dem Austreiben (typisch Mai/Juni).

**Deadheading:** Verblühte Blüten wöchentlich entfernen — verlängert Blütezeit erheblich und verhindert Samenbildung, die die Pflanze schwächt.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | `limited` (möglich, aber Platzbedarf ist groß; Mindestgefäßgröße 20–25 L bei dieser Wuchshöhe) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 35 (Knollen brauchen Tiefe; flache Töpfe riskieren Kippleistung bei Windlast) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–75 (empfohlener Pflanzabstand für gute Durchlüftung und Blütenqualität) | `species.spacing_cm` |
| Indoor-Anbau | `no` (nicht geeignet für dauerhaften Indoor-Anbau; Lichtbedarf und Größe unpraktisch) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | `limited` (auf großen Terrassen in 25-L-Kübeln möglich; Windschutz und regelmäßiges Gießen wichtig) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (Freilandpflanze; Gewächshaus nur für Vorkeimen im März/April) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (bei 100–120 cm Wuchshöhe obligatorisch; Bambusstab oder Dahlienkäfig, mind. 120 cm) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, nährstoffreiche Kübelpflanzenerde mit 20–30 % Perlite oder Blähton für gute Drainage; pH 6,0–7,0. Keine reine Torferde (Verdichtung, pH-Probleme). | — |

---

## 2. Wachstumsphasen

Dahlien als Knollenstauden werden im Jahresrhythmus betrieben. Der Zyklus beginnt mit dem Auspflanzen der Knolle im Frühjahr und endet mit dem Ausgraben nach dem ersten Frost. Die Phasen beziehen sich auf den aktiven Vegetationszyklus (Mai–November in Mitteleuropa).

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Austrieb (Sprouting) | 14–28 | 1 | false | false | low |
| Vegetativ (Vegetative) | 28–42 | 2 | false | false | medium |
| Abhärtung (Hardening Off) | 7–14 | 3 | false | false | low |
| Vorblüte (Pre-flowering) | 14–21 | 4 | false | false | medium |
| Vollblüte (Flowering) | 70–120 | 5 | false | false | medium |
| Seneszenz (Senescence) | 14–21 | 6 | true | false | high |
| Dormanz (Dormancy / Knollenlagerung) | 150–180 | 7 | false | false | low |

**Hinweise zu den Phasen:**
- Phase "Abhärtung" nur relevant bei Indoor-Vorkultur vor Freilandauspflanzung (AB-009)
- Phase "Dormanz" entspricht der Knollenlagerung über Winter (5–10 °C, dunkel, frostfrei)
- `is_recurring: true` auf den Phasen Vegetativ bis Dormanz (Dauerkulturen-Modus, jährlicher Zyklus)
- `allows_disposal: true` auf der Seneszenz-Phase (Möglichkeit, Knollen als entsorgt zu markieren statt auszugraben)

### 2.2 Phasen-Anforderungsprofile

#### Phase: Austrieb (Sprouting)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 (gedämpftes Licht; direkte Mittagssonne vermeiden bis Blätter ausgebildet) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag fördert vegetatives Wachstum, verhindert zu frühe Blühinduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Freiland-Standard) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (sparsam gießen bis Augen sichtbar — Staunässe fördert Knollenfäule!) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ (Vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (volle Sonne bevorzugt, min. 6–8 h direkte Sonne täglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (Langtag für starkes vegetatives Wachstum; kurze Nächte verzögern Blühinduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (regelmäßig; Substrat zwischen den Gaben leicht antrocknen lassen, aber nie komplett austrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1.000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Abhärtung (Hardening Off)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–600 (beginnend unter Schattierung, stufenweise an Volllicht gewöhnen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 (kurze Nächte unter 10 °C vermeiden) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 400–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vorblüte (Pre-flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1.000 (Volllicht; mind. 6–8 h direkte Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (Übergang zu kürzeren Tagen ab Juli fördert Blühinduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Wasserverbrauch steigt mit zunehmender Pflanzengröße erheblich) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 800–1.500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vollblüte (Flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–1.200 (Volllicht für maximale Blütenproduktion; bei Hitze > 32 °C leichte Schattierung vorteilhaft) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 (natürliche Verkürzung ab August; Kurztagspflanze blüht bei Nachtlänge > 10–11 h) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 (kühle Nächte verbessern Blütenfarbe und -haltbarkeit erheblich) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–60 (unter 80 % RH halten — Botrytis-Risiko bei feuchten Blüten!) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (täglich an Hitzetagen; Knollen reagieren empfindlich auf Trockenstress in der Blüte — kleinere Blüten, schnelleres Verblühen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1.000–2.000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Seneszenz (Senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 (natürliche Herbstbedingungen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 9–12 (Herbst) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 8–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 2–10 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (Gießen reduzieren, Knolle ausreifen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz / Knollenlagerung (Dormancy)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 (dunkel lagern) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 (Dunkelheit) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 5–10 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–8 (nie unter 2 °C — Knolle erfriert!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 (zu trocken = Austrocknung der Knolle; zu feucht = Fäulnis) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | null (nicht anwendbar — Knollen ohne aktiven Gaswechsel; kein Steuerungsparameter) | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Keller-Standard) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 30 (monatliche Sichtkontrolle; bei Schrumpfen leicht anfeuchten, nie nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0–50 (nur bei sichtbarer Austrocknung leicht besprühen) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS/cm) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|-----------|-----|----------|----------|---------|----------|
| Austrieb | 1:1:1 | 0.6–0.8 | 6.0–6.5 | 60 | 30 | — | 2 |
| Vegetativ | 3:1:2 | 1.2–1.6 | 6.0–6.5 | 120 | 50 | — | 3 |
| Vorblüte | 1:2:3 | 1.4–1.8 | 6.0–6.5 | 100 | 50 | — | 2 |
| Vollblüte | 1:3:4 | 1.2–1.8 | 6.0–7.0 | 80 | 40 | — | 2 |
| Seneszenz | 0:1:3 | 0.4–0.6 | 6.0–7.0 | 40 | 20 | — | 1 |
| Dormanz | 0:0:0 | 0.0 | — | — | — | — | — |

**Wichtig:** Dahlien reagieren empfindlich auf Stickstoffüberschuss — üppiges Blattwerk auf Kosten der Blüte ist das typische Symptom. Ab Vorblüte Stickstoff deutlich reduzieren, Kalium und Phosphor betonen.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Austrieb → Vegetativ | `time_based` | 14–28 Tage | Erste Laubblätter entfaltet, Knospen treiben aus |
| Vegetativ → Abhärtung | `conditional` | — | Nur bei Indoor-Vorkultur: Auspflanzung geplant, kein Frost mehr zu erwarten |
| Abhärtung → Vorblüte | `time_based` | 7–14 Tage | Pflanze ist abgehärtet, im Freiland etabliert |
| Vegetativ → Vorblüte | `event_based` | — | Pinching abgeschlossen; erste Blütenansätze (bypasses Abhärtung bei Direktpflanzung) |
| Vorblüte → Vollblüte | `event_based` | — | Erste Blüten öffnen sich |
| Vollblüte → Seneszenz | `event_based` | — | Erster Frost schwärzt das Laub (typically Oktober/November) |
| Seneszenz → Dormanz | `time_based` / `manual` | 7–14 Tage nach Frost | Knollen ausgraben, trocknen, einlagern; `is_cycle_restart: true` |
| Dormanz → Austrieb | `time_based` / `manual` | 150–180 Tage | Knollen aus Lager, Vorkeimen oder direkt auspflanzen ab Mai |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland / Standard-Anbau)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | (verschiedene, z.B. Hauert, Neudorff, Cuxin) | organisch/N-Langzeit | 80–120 g/m² | Pflanzung (Mai), ggf. Nachdüngung Juni | Vegetative Phase, N-Grundversorgung |
| Kompost (reif) | Eigenerzeugnis oder Sackware | organisch/Bodenverbesserung | 3–5 L/m² | Frühjahr (Pflanzung), Herbst (Einarbeiten) | Alle Phasen, Bodenstruktur |
| Beinwelljauche | Eigenerzeugnis / Lebendige Erde | organisch/K-reich | 1:10 verdünnt, 2 L/m² alle 2–3 Wochen | Juli–September | Blütephase (Kalium-Boost) |
| Schafwoll-Pellets | (z.B. Oscorna, Hauert Vital) | organisch/N-Langzeit | 50–80 g/m² | Pflanzung | Vegetative Phase |

**Freiland-Düngeempfehlung nach `heavy_feeder`-Schema (REQ-004):**
- Pflanzung (Mai): Hornspäne 100 g/m² + Kompost 4 L/m² in den Boden einarbeiten
- Juni (Vegetativ): Optional Brennnesseljauche 1:10 alle 3 Wochen
- Juli–September (Blüte): Beinwelljauche oder kaliumbetonter Blütendünger alle 2 Wochen
- September (Knolle stärken): Letzte Düngung kaliumreich (für Knollenreifung)
- Oktober: Keine Düngung mehr

#### Mineralisch (Kübel / Indoor-Vorkultur)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| COMPO Hakaphos Blumenprofi | COMPO | Volldünger wasserlöslich | 15-10-24 + Mg, Spurenelemente | 2–3 g/L, alle 2 Wochen | 2 | Vegetativ, Vorblüte |
| Blähom / Terrasan | Neudorff | organisch-mineralisch | 12-3-6 | 40–60 g/Gefäß (20 L) | 1 (Grunddüngung) | alle |
| Hakaphos Blau | COMPO EXPERT | mineralisch, Phosphor-betont | 13-40-13 + Spurenelemente | 1–2 g/L | 2 | Vorblüte, Vollblüte |
| Blütenpflanzendünger flüssig | Substral / Compo Sana | mineralisch-flüssig | 6-5-8 (typisch) | 20–25 ml/10 L | 3 | Vollblüte (wöchentlich) |

### 3.2 Düngungsplan (Beispiel für Kübelpflanzung, 25-L-Topf)

| Zeitraum | Phase | Produkt | Dosierung | Intervall | Hinweise |
|----------|-------|---------|-----------|-----------|----------|
| März–April | Austrieb (Vorkeimung) | Keine Düngung | — | — | Knolle hat eigene Reserven |
| Mai | Vegetativ | Terrasan Grunddüngung | 60 g/Topf einarbeiten | Einmalig | pH-Ziel 6,0–6,5 prüfen |
| Juni | Vegetativ | COMPO Hakaphos Blumenprofi | 2 g/L Gießwasser | Alle 2 Wochen | EC < 1,6 mS/cm halten |
| Juli | Vorblüte | Hakaphos Blau | 1,5 g/L Gießwasser | Wöchentlich | Stickstoff stark reduzieren |
| Aug–Sep | Vollblüte | Blütendünger flüssig | 25 ml/10 L | Wöchentlich | Deadheading parallel durchführen |
| Oktober | Seneszenz | Kaliumsulfat (ggf.) | 1–2 g/L einmalig | Einmalig | Knollenreifung fördern |
| Nov–Apr | Dormanz | Keine Düngung | — | — | Knollen trocken und kühl lagern |

### 3.3 Mischungsreihenfolge (Kübel/Mineralisch)

> **Kritisch:** Mischungsreihenfolge verringert Ausfällungen. Bei Dahlien in Kübeln mit mineralischen Düngern:

1. Gießwasser (18–20 °C Raumtemperatur)
2. CalMag (falls Osmose- oder sehr weiches Wasser verwendet wird)
3. Mineralischer Volldünger (Hakaphos Blumenprofi oder Blütendünger)
4. Spurenelemente-Ergänzung (falls separate Mikronährstofflösung)
5. pH-Korrektur (pH Down mit Zitronensäure oder Phosphorsäure, IMMER zuletzt)

**Ziel-pH für Dahlien im Kübel:** 6,0–6,5 (leicht sauer bis neutral). Bei zu hohem pH (> 7,0) treten Eisenmangel und Chlorose auf.

### 3.4 Besondere Hinweise zur Düngung

**Stickstoff-Falle:** Dahlien reagieren sehr sensibel auf zu viel Stickstoff. Typisches Schadbild: Großes, dunkelgrünes Blattwerk, wenige oder kleine Blüten, schwache Stängel. Daher: Ab Vorblüte (Knospenentwicklung) Stickstoff deutlich reduzieren — kein weiterer N-Volldünger in der Blüte.

**Kalium für Knollenqualität:** Eine letzte kaliumreiche Düngung im September (z.B. Beinwelljauche oder Kaliumsulfat) verbessert die Knollenreifung und damit die Überwinterungsqualität. Schlechte Knollenreifung = höhere Fäulnisgefahr bei der Lagerung.

**Kübelpflanzen-EC:** Bei regelmäßiger Mineraldüngung sollte die EC im Ablaufwasser gemessen werden. Werte > 2,5 mS/cm deuten auf Salzakkumulation hin — dann 2–3 x mit reinem Wasser durchspülen (Flush).

**Organisch im Freiland:** Beinwelljauche ist der ideale biologische Blütendünger für Dahlien — kaliumreich, verfügbar, günstig. Selbst herstellen: 1 kg frische Beinwellblätter auf 10 L Wasser, 2–4 Wochen fermentieren, 1:10 verdünnt ausbringen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `outdoor_annual_veg` (behandelt wie einjährige Außenpflanze in Mitteleuropa, auch wenn botanisch perennial; alternativ: `custom` mit saisonalem Knollen-Zyklus) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 1–2 (in Vollblüte und Hitze täglich; im Freiland nach Niederschlag anpassen) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (Dahlien werden ausgegraben, nicht überwintert in Erde — Knollenlagerung statt Winter-Gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | `top_water` (von oben gießen, Blätter und Blüten nicht benetzen — Botrytis-Prävention) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | "Leitungswasser geeignet. Bei sehr hartem Wasser (> 300 ppm Ca) kann Chlorose auftreten — abgestandenes Wasser oder Regenwasser bevorzugen." | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 (Freiland organisch alle 2 Wochen; Kübel wöchentlich in Vollblüte) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–10 (Mai bis Oktober) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jährlich bei Kübelpflanzen — Knollen wachsen, neues Substrat nötig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wöchentliche Sichtprüfung, besonders auf Blattläuse, Ohrwürmer und Mehltau) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Freilandpflanze; Luftfeuchte nur bei Kübel auf Terrasse relevant) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Saatgut / Knollen-Inventur | Eingelagerte Knollen kontrollieren: Faulstellen entfernen, leicht schrumpfende Knollen leicht anfeuchten | mittel |
| Feb | Knollen-Sichtkontrolle II | Zweite Kontrolle; bei Schimmelbefall befallene Stellen wegschneiden, Wunde mit Holzkohle behandeln | mittel |
| Mär | Vorkeimen beginnen | Knollen in Töpfe (Ø 15 cm) mit feuchter Anzuchterde setzen; 15–18 °C, hell (Fensterbrett oder Gewächshaus) | hoch |
| Mär | Knollenteilung | Wenn Augenpunkte sichtbar: Knollen teilen für Vermehrung; Schnittflächen mit Fungizid behandeln | mittel |
| Apr | Vorkeimung fortsetzen | Töpfe hell und warm stellen; erste Triebe ausgeizen wenn > 5 Blattpaare (Pinching) | hoch |
| Apr | Stecklinge nehmen | Falls Stecklingsvermehrung gewünscht: Triebe mit 3 Blattknoten abschneiden, in Anzuchterde bewurzeln | niedrig |
| Mai | Abhärtung + Auspflanzen | Nach letztem Frost (Eisheiligen Mitte Mai beachten!): Pflanzen 10–14 Tage abhärten, dann auspflanzen | hoch |
| Mai | Pfähle setzen | Gleichzeitig mit Auspflanzen Stützpfähle (mind. 120 cm) setzen — nachträgliches Einstechen verletzt Knollen | hoch |
| Jun | Pinching (Herzausbrechen) | Haupttrieb über dem 3.–4. Blattknoten kappen für buschigeren Wuchs; nur wenn noch nicht im März gemacht | hoch |
| Jun | Erste Düngung | Organische Düngung mit Brennnesseljauche oder Hornmehlgabe; Gießrhythmus steigern | mittel |
| Jul | Deadheading beginnen | Verblühte Blüten wöchentlich entfernen — fördert Nachblüte erheblich; als Schnittblume nutzen | hoch |
| Jul–Aug | Blütedüngung | Kaliumreiche Düngung (Beinwelljauche, Blütendünger) alle 2 Wochen; Stickstoff vermeiden | hoch |
| Aug | Schädlingskontrolle | Intensivierte Kontrolle auf Spinnmilben, Blattläuse, Mehltau (Trocken-Heiß-Periode begünstigt Befall) | hoch |
| Sep | Letzte Düngung | Einmalig kaliumreich für Knollenreife; dann keine Düngung mehr | mittel |
| Okt | Erster Frost | Abwarten bis erster Frost das Laub schwärzt; Knollen 7–14 Tage danach erst ausgraben (Knolle reift nach) | hoch |
| Nov | Knollen ausgraben | Vorsichtig mit Grabegabel; 10–15 cm Stängelrest lassen; 1–2 Wochen an frostfreiem Ort trocknen | hoch |
| Nov | Knollen einlagern | In Holzkisten mit trockenem Torf, Perlite oder Zeitungspapier; 5–10 °C, dunkel, 60–75 % Luftfeuchte | hoch |
| Dez | Monatskontrolle | Knollen auf Fäulnis und Austrocknung prüfen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | `dig_and_store` (in Mitteleuropa Zone 7–8 obligatorisch ausgraben) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | `dig_store` (Knollen ausgraben, trocknen, einlagern) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 (November, nach erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | `replant` (Knollen vorkeimen und wieder auspflanzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 (März Vorkeimung, Mai Auspflanzung) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 4 (unter 2 °C erfrieren die Knollen) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 (über 12 °C beginnen Knollen zu treiben — unerwünscht) | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | `dark` (vollständige Dunkelheit — kein Licht nötig, da Knollen ruhen) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | `none` (keine Bewässerung; monatliche Sichtkontrolle auf Trockenheit) | `overwintering_profiles.winter_watering` |

**Knollen-Lagerung Schritt für Schritt:**
1. Nach erstem Frost 7–14 Tage warten (Knollenreife)
2. Vorsichtig ausgraben (Grabegabel, ca. 30 cm Abstand zur Pflanze)
3. Stängel auf 10–15 cm kürzen
4. Erde vorsichtig entfernen (nicht waschen — feucht = Faulnis!)
5. Kopfüber 1–2 Wochen trocknen (Wasser aus Hohlstängeln ablaufen lassen)
6. Einlagern in Kisten mit trockenem Torf, Perlite, Sägespäne oder Zeitungspapier
7. Monatlich kontrollieren: Schrumpfen = leicht besprühen; Schimmel = betroffene Stelle entfernen, mehr Luftzirkulation

**Winterhärte-Ampel für 'Hapet Daydream':**
- Zone 8–11: Gelb (Schutz empfohlen — dicke Mulchschicht von 15–20 cm)
- Zone 7: Rot (ausgraben obligatorisch — zuverlässige Überwinterung im Boden nicht gegeben)
- Zone ≤ 6: Rot (ausgraben obligatorisch)

**Knollen-Zyklus (REQ-022 Knollenpflege):**
`Auspflanzen (Mai) → Austreiben → Blühen → Ausgraben (November) → Trocknen → Einlagern → Monatskontrolle → Vorkeimen (März) → Auspflanzen`

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattlaus (verschiedene Arten) | Myzus persicae, Aphis gossypii | Gekräuselte Blätter, Honigtau, Rußtau; überträgt Mosaikviren | leaf, stem, flower_bud | vegetative, pre_flowering | easy |
| Ohrwurm | Forficula auricularia | Unregelmäßige, ausgefranste Löcher in Blättern und Blütenblättern; nachtaktiv; ambivalent — fressen auch Blattläuse (Nützlingswirkung); Bekämpfung abwägen | leaf, flower | flowering | medium (nachtaktiv) |
| Nacktschnecke | Arion spp., Deroceras spp. | Unregelmäßige Fraßlöcher, Schleimspuren; besonders an Jungtrieben | leaf, stem | sprouting, vegetative | easy (Schleimspuren) |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste auf Blattunterseite, gelbe/silbrige Punkte, bei Befall Blatt-Bräunung | leaf | flowering (Hitze/Trockenheit) | medium |
| Thrips | Frankliniella occidentalis | Silbrig-weiße Flecken auf Blättern und Blüten, dunkle Kotpunkte; überträgt TSWV | leaf, flower | flowering | difficult |
| Raupe (verschiedene Arten) | Agrotis spp., Autographa gamma | Fraßlöcher in Blättern; eingerollte Blätter als Versteck | leaf | vegetative, flowering | medium |
| Dahlien-Minierfliege | Liriomyza trifolii | Helle Minen (Gänge) in der Blattspreite | leaf | vegetative, flowering | easy (Minenmuster) |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißer, mehliger Belag auf Blättern und Stängeln | Warm/trocken tags + kühl nachts, schlechte Luftzirkulation | 5–10 | vegetative, flowering |
| Grauschimmel / Botrytis | fungal (Botrytis cinerea) | Grauer Pilzrasen auf Blüten und Stängeln; Fäulnis | Hohe Luftfeuchtigkeit > 85 %, kühle Temperaturen | 3–7 | flowering, senescence |
| Dahlien-Mosaikvirus | viral (DMV, TSWV) | Mosaikflecken auf Blättern, Wachstumshemmung, Verformung | Blattläuse und Thrips als Vektoren | 7–21 | alle |
| Knollenfäule | fungal (Fusarium oxysporum, Sclerotinia) | Braune, weiche Faulstellen an der Knolle; fauliger Geruch | Feuchte Lagerung, Verletzungen beim Ausgraben | — | dormancy |
| Pythium-Wurzelfäule | Oomycete (Pythium spp.) | Welke trotz feuchtem Substrat, braune Wurzeln | Staunässe, besonders bei frisch ausgepflanzten Knollen | 3–10 | sprouting |
| Blattflecken | fungal (Entyloma dahliae) | Cremeweiße, runde Flecken mit gelbem Rand auf Blättern | Feuchtwarmes Wetter, Benässung der Blätter | 7–14 | vegetative, flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse | 10–20 Imagines/m² | 7–14 |
| Florfliege (Chrysoperla carnea) | Blattläuse, Thrips | 5–10 Eier/m² | 7–14 |
| Raubmilbe (Amblyseius cucumeris) | Thrips (Larven), Spinnmilben | 50–100/m² | 14–21 |
| Schlupfwespe (Aphidius colemani) | Blattläuse | 5–10/m² | 14–21 |
| Steinernema feltiae (Nematoden) | Ohrwürmer, Sciaridenmücken (im Kübel) | 0,5 Mio./m² | 7–14 |
| Igel / Laufkäfer (Carabus spp.) | Nacktschnecken | Förderung durch Totholzhaufen | natürlich |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff / Mittel | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|--------------------|-----------|-------------------|-------|
| Neemöl (kaltgepresst) | biological | Azadirachtin | Sprühen 0,5 %, morgens oder abends | 3 | Blattläuse, Spinnmilben, Mehltau (präventiv) |
| Kaliumbicarbonat | biological/chemical | KHCO₃ | Sprühen 0,5 % Lösung (z.B. Natria Mehltau-Frei) | 0 | Echter Mehltau |
| Pyrethrum / Pyrethrine | biological | Pyrethrin (z.B. Neudosan, Spruzit) | Sprühen; nur abends (Bienenschutz!) | 1–3 | Blattläuse, Thrips |
| Bacillus thuringiensis (Bt) | biological | Cry-Proteine (z.B. XenTari) | Sprühen auf Blätter | 0 | Raupen, Minierfliegen |
| Schneckenkorn (Eisen-III-Phosphat) | biological | Fe₃(PO₄)₂ (z.B. Ferramol, Sluxx) | Streuen um Pflanzen | 0 | Nacktschnecken, Weinbergschnecken |
| Ohrwurm-Falle (Tontopf) | cultural | — | Tontopf mit Holzwolle kopfüber auf Stab; täglich leeren | 0 | Ohrwürmer |
| Mulchen mit Stroh/Holzhäckseln | cultural | — | 5–8 cm Schicht um Pflanzenbasis | 0 | Nacktschnecken, Spritzwasser-Pilze |
| Paraffinöl (Weißöl) | chemical | Mineralöl (z.B. Schädlingsfrei Careo Ölspray) | Sprühen | 7 | Spinnmilben, Blattläuse |
| Schwefel (Netzschwefel) | chemical | Schwefel (z.B. Kumulus DF) | Stäuben/Spritzen | 14 (Zierbereich) | Echter Mehltau |

**Hinweis Virus-Management:** Gegen Dahlienmosaikvirus gibt es keine Behandlung. Infizierte Pflanzen sofort entfernen und vernichten (nicht kompostieren). Prävention durch konsequente Blattlaus-/Thrips-Bekämpfung. Infizierte Knollen auf keinen Fall zur Vermehrung verwenden.

**Hinweis Knollenfäule:** Beim Einlagern verdächtige Knollen separieren. Schimmel-Stellen bis in gesundes Gewebe ausschneiden, Wunde mit Holzkohlepulver oder Thiram-Pulver behandeln. Bei > 30 % Faulflächenanteil Knolle vernichten.

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine bekannten spezifischen Resistenzen bei Dahlien dokumentiert | — | — |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (`heavy_feeder`) |
| Fruchtfolge-Kategorie | Korbblütler (Asteraceae) — Zierpflanzen-Rotation |
| Empfohlene Vorfrucht | Hülsenfrüchte (Fabaceae) als Gründüngung; Phacelia (Stickstoffanreicherung im Boden) |
| Empfohlene Nachfrucht | Schwachzehrer: Kräuter (Thymus, Salvia), Salate; nach Dahlien wird der Boden intensiv genutzt — leichte Begrünung ratsam |
| Anbaupause (Jahre) | 2–3 Jahre (keine Dahlien oder Asteraceae-Starkzehrer am selben Standort) |

**Hinweis:** Dahlien sind keine Gemüsepflanzen im klassischen Sinne, daher greift die typische 4-Jahres-Fruchtfolge hier nicht streng. In der Praxis: Standort jährlich wechseln oder nach 2–3 Jahren Dahlienanbau 1–2 Jahre Pause mit Hülsenfrüchten oder Gründüngung.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes (Studentenblume) | Tagetes patula, T. erecta | 0.9 | Nematoden-Abwehr (Wurzelsekrete hemmen Wurzelnematoden), Schneckenabschreckung, Bestäuber-Attraktion | `compatible_with` |
| Zinnie | Zinnia elegans | 0.8 | Ähnliche Kulturansprüche; gegenseitige Nematoden-Abwehr; Bestäuber-Attraktion | `compatible_with` |
| Cosmea / Schmuckkörbchen | Cosmos bipinnatus | 0.8 | Gleiche Wachstumsbedingungen; lockeres Wurzelsystem; zieht Nützlinge an | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Duft wirkt auf einige Schädlinge abschreckend; Wärme-Ansprüche ähnlich | `compatible_with` |
| Ringelblume | Calendula officinalis | 0.8 | Zieht Blattlaus-Feinde (Schwebfliegen, Schlupfwespen) an; Bodenpilz-hemmend | `compatible_with` |
| Knoblauch / Zwiebeln | Allium sativum, A. cepa | 0.7 | Duft wirkt auf Blattläuse und Spinnmilben abschreckend; Bodengesundheit | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.6 | Bestäuber-Attraktion; Duft hält manche Schädlinge fern; Trockenstress-toleranter | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kartoffel | Solanum tuberosum | Gemeinsame Virus-Vektoren (Potato Virus Y, PLRV); Blattläuse übertragen Viren zwischen beiden | severe | `incompatible_with` |
| Tomate | Solanum lycopersicum | Nährstoffkonkurrenz; geteilte Schädlinge (Spinnmilbe, Thrips); Virus-Übertragungsrisiko | moderate | `incompatible_with` |
| Chrysantheme | Chrysanthemum spp. | Gleiche Familie (Asteraceae); geteilte Schädlinge und Krankheiten (Mehltau, Blattläuse); Konkurrenz | moderate | `incompatible_with` |
| Gladiole | Gladiolus spp. | Geteilte Schädlinge (Thrips); Fusarium-Risiko durch Knollen-Erde-Kontamination | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Asteraceae (Korbblütler) | `shares_pest_risk` | Echter Mehltau (Erysiphe cichoracearum), Chrysanthemum-Blattlaus, Thrips | `shares_pest_risk` |
| Solanaceae (Nachtschattengewächse) | `shares_pest_risk` | Tomato Spotted Wilt Virus (TSWV), Thrips als gemeinsamer Vektor | `shares_pest_risk` |
| Fabaceae (Hülsenfrüchte) | `family_compatible_with` | Stickstoff-Anreicherung im Boden als Vorfrucht | `family_compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art / Sorte | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber 'Hapet Daydream' |
|-------------|-------------------|-------------|-------------------------------------|
| Dahlien (Pompon-Typ allgemein) | Dahlia-Sorten verschiedene | Gleiche Blütenform, kleiner (4–5 cm) | Kompakter, windfester, besser für Töpfe und Beetränder |
| 'Bishop of Llandaff' | Dahlia 'Bishop of Llandaff' | Ähnliche Höhe, rote Blüten, Bronzelaub | Markanteres Blattwerk, bekannter, robuster |
| 'Karma Choc' | Dahlia 'Karma Choc' | Dekorative Dahlie, dunkelrot-braun | Modernere Sorte, sehr beliebt als Schnittblume |
| Einfache Dahlien (Single-Typ) | Dahlia-Sorten (Single) | Einfachere, offene Blüten | Viel bienenfreundlicher (offen für Bestäuber), weniger anfällig für Botrytis |
| Tithonia (Mexikanische Sonnenblume) | Tithonia rotundifolia | Gleiche Familie, ähnliche Kulturansprüche | Robuster, kein Ausgraben nötig (Einjährige), wärmetoleranter |
| Canna (Indisches Blumenrohr) | Canna x generalis | Ähnlicher Knollen-Zyklus, tropisches Flair | Exotischeres Erscheinungsbild, robuster gegen Starkregen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months,pruning_type
Dahlia pinnata,Dahlie;Dahlia,Asteraceae,Dahlia,perennial,short_day,herb,tuberous,8a;8b;9a;9b;10a;10b;11a,-0.0,Mexiko (Hochlagen 1800-3000m),limited,25,35,120,70,70,no,limited,false,true,heavy_feeder,false,tender,7;8;9;10,none
```

### 8.2 Cultivar CSV-Zeile ('Hapet Daydream')

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hapet Daydream,Dahlia pinnata,Unbekannt (Niederlande),2020,ornamental;ball_type;bicolor;cutting_flower;heavy_feeder,90,,clone
```

**Hinweis:** `seed_type: clone` — Sorten-Dahlien werden vegetativ (Knollenteilung, Stecklinge) vermehrt; Samenreproduktion ist nicht sortenecht.

### 8.3 BotanicalFamily CSV-Zeile

```csv
name,common_name_de,common_name_en,order,description,typical_nutrient_demand,nitrogen_fixing,typical_root_depth,frost_tolerance,rotation_category
Asteraceae,Korbblütler,Daisy family,Asterales,Größte Pflanzenfamilie mit charakteristischen Blütenköpfen (Körbchen) aus Röhren- und Zungenblüten; umfasst Zierpflanzen (Dahlie, Chrysantheme, Sonnenblume) und Gemüsepflanzen (Artischocke, Salat),heavy,false,SHALLOW,MODERATE,Korbblütler
```

---

## Quellenverzeichnis

1. [RHS Plant Finder — Dahlia 'Hapet Daydream'](https://www.rhs.org.uk/plants/383289/dahlia-hapet-daydream-(d)/details) — Botanische Klassifikation, Farbcodes, Grunddaten
2. [ASPCA Toxic and Non-toxic Plants: Dahlia](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dahlia) — Toxizitätsangaben Katze/Hund
3. [UC IPM — Managing Pests in Gardens: Dahlia](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html) — IPM, Schädlinge, Krankheiten
4. [American Dahlia Society — Fundamentals of Growing Dahlias](https://www.dahlia.org/growing/fundamentals-of-growing-dahlias/) — Anbaugrundlagen, Phasen
5. [American Dahlia Society — Nutrients for Dahlias](https://www.dahlia.org/docsinfo/articles/nutrients-for-dahlias/) — NPK-Angaben, Düngungsplan
6. [Longfield Gardens — Common Dahlia Pests and Diseases](https://www.longfield-gardens.com/article/common-dahlia-pests-and-diseases) — Schädlings- und Krankheitsübersicht
7. [Longfield Gardens — How to Overwinter Dahlias](https://www.longfield-gardens.com/article/how-to-overwinter-dahlias) — Überwinterung, Lagerung
8. [Old Farmer's Almanac — Dahlias](https://www.almanac.com/plant/dahlias) — Pflanzabstand, Tiefe, Phasenzeiten
9. [Dahlia Doctor — The Dahlia Clock](https://www.dahliadoctor.com/blogs/second-blog/the-dahlia-clock-bringing-it-all-together) — Licht, PPFD, Photoperiode
10. [Dahlia Doctor — Grow Dahlias Using Artificial Lights](https://www.dahliadoctor.com/blogs/second-blog/using-artificial-light-to-grow-dahlias-leds-timing-and-spectrum) — Lichttechnik, DLI, Kurztagspflanze
11. [Plantura.garden — Dahlien düngen](https://www.plantura.garden/blumen-stauden/dahlien/dahlien-duengen) — Düngungsempfehlungen, NPK-Ratios, organische Dünger
12. [Plantura.garden — Dahlien überwintern](https://www.plantura.garden/blumen-stauden/dahlien/dahlien-ueberwintern) — Überwinterungsdetails Mitteleuropa
13. [Epic Gardening — Dahlia Companion Plants](https://www.epicgardening.com/dahlia-companion-plants/) — Mischkultur-Empfehlungen
14. [PFAF — Dahlia pinnata](https://pfaf.org/user/Plant.aspx?LatinName=Dahlia+pinnata) — Botanische Grunddaten, Heimat
15. [Missouri Botanical Garden — Dahlia (group)](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a445) — Wuchsform, Anbaubedingungen
16. [Greenhouse Grower — Focus On Dahlia Fertilizer](https://www.greenhousegrower.com/crops/focus-on-dahlia-fertilizer/) — Professionalfertiger-Daten, Hydro-EC/pH
17. [DahliaAddict — Hapet Daydream Suppliers](https://dahliaaddict.com/hapet-daydream/dahlia/3465) — Sorteninfos, Herkunft Niederlande 2020
18. [Promesse de Fleurs — Dahlia Hapet Daydream](https://www.promessedefleurs.ie/summer-flowering-bulbs/dahlias/pom-pom-dahlias/dahlia-hapet-daydream.html) — Höhe, Blütezeit, Sortenklassifikation
