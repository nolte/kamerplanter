# Dahlie 'Great Silence' — Dahlia pinnata 'Great Silence'

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:** [RHS Plant Database](https://www.rhs.org.uk/plants/375276/dahlia-great-silence-(d)/details) | [American Dahlia Society](https://www.dahlia.org/guide/) | [Gardenia.net](https://www.gardenia.net/plant/dahlia-great-silence) | [Longfield Gardens](https://www.longfield-gardens.com/plantname/Dahlia-Decorative-Great-Silence) | [UC IPM Dahlia](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html) | [ASPCA Toxicity](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dahlia) | [American Meadows](https://www.americanmeadows.com/product/flower-bulbs/great-silence-decorative-dahlia)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dahlia pinnata 'Great Silence' | `species.scientific_name` (Cultivar-Ebene) |
| Art (Elternart) | Dahlia pinnata Cav. (Garten-Dahlie) | `species.scientific_name` |
| Volksnamen (DE/EN) | Dahlie 'Great Silence'; Dahlia 'Great Silence' | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Dahlia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| ADS-Klassifikation | 3113 — Informal Decorative, Ball-Size BB (10–15 cm), Dark Blend | Cultivar-Trait |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial (Knollenpflanze, in Mitteleuropa als Einjährige kultiviert) | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day (fakultativ; Blüteninitiierung bei Nachtlänge > 12 h gefördert, Dahlien blühen jedoch auch unter Langtagbedingungen; Tuberisierung eindeutig kurztaggesteuert bei Nacht > 12 h) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a–11b (in Zone 7 und kälter: Knollen ausgraben und einlagern) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Knollen sterben bei Dauerfrost unter -3 °C ab. In Mitteleuropa (Zone 7–8) müssen Knollen nach dem ersten Frost ausgegraben und frostfrei bei 4–10 °C eingelagert werden. Triebe erfrieren bereits bei 0 °C. | `species.hardiness_detail` |
| Heimat | Elternarten aus Mexico und Mittelamerika (Hochland); Zuchtsorte niederländisch-belgischer Züchtung | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral; keine bekannte allelopathische Wirkung der Dahlie) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder (Starkzehrer — insbesondere P und K in der Blütephase; N-Überschuss hemmt Blütenbildung) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, bee_friendly, fragrant (leicht), edible (Knollen bedingt essbar) | `species.traits` |

> **Sorteninformation:** 'Great Silence' ist eine Zuchtsorte (Cultivar) von Peter Komen (Niederlande), eingeführt 2018. ADS-Registrierung: Informal Decorative (ID), Blütendurchmesser 10–15 cm (BB-Klasse 4–6 Zoll), Farbklasse Dark Blend (DB) — korallrosa mit goldgelbem Herzbereich, die Petalen sind wellig und unregelmäßig angeordnet, typisch für informell-dekorative Sorten. RHS registriert als Bedding/D-Gruppe.

### 1.2 Aussaat- & Erntezeiten (Mitteleuropa, Zone 7–8)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Knollen ab März drinnen vortreiben) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (Knollen erst pflanzen, wenn Boden mind. 12 °C hat) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate (Freiland) | 5 (ab Mitte Mai, nach den Eisheiligen) | `species.direct_sow_months` |
| Ernte-/Blütemonate (Schnittblume) | 7, 8, 9, 10 (Juli bis Oktober/erster Frost) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 | `species.bloom_months` |

> **Hinweis Mitteleuropa:** Der letzte Frost fällt in Zone 7 typischerweise zwischen Mitte April und Mitte Mai. Die Eisheiligen (11.–15. Mai) gelten als volkstümliche Orientierung. Dahlien keinesfalls vor den Eisheiligen auspflanzen — schon eine Nacht unter 0 °C vernichtet den Austrieb. Knollen-Voranzucht ab Mitte März in Töpfen bei 16–18 °C ist für frühere Blüte (ab Ende Juni) empfehlenswert.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division (Knollenteilung), cutting_stem (Stecklinge aus Knospenaustrieb), seed (bei Artsorten, bei Cultivar kein Namenserhalt) | `species.propagation_methods` |
| Schwierigkeit | easy (Knollenteilung) / moderate (Stecklinge) | `species.propagation_difficulty` |

> **Praxis-Hinweis:** Knollenteilung ist die Standardmethode für Cultivar-Erhalt. Jede Teilung muss mindestens ein "Auge" (Knospe) am Kronenstumpf (Crown) haben — Knollen ohne Auge treiben nicht aus. Stecklinge werden im Frühjahr von den ersten Knospenaustrieben (5–8 cm Länge) geschnitten und in Perlite/Vermiculit bewurzelt. Samenanzucht liefert keine sortenechten Pflanzen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true (mild) | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true (mild) | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (als nicht toxisch für Menschen eingestuft) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile (Blätter, Stängel, Knollen) — Knollen am stärksten | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Unbekannte Verbindungen (keine Alkaloide bestätigt); vermutlich Sesquiterpenlactone und Polyacetylen-Derivate | `species.toxicity.toxic_compounds` |
| Schweregrad | mild (ASPCA: mild gastrointestinal signs and mild dermatitis bei Hund/Katze) | `species.toxicity.severity` |
| Kontaktallergen | true (Sesquiterpenlactone können Kontaktdermatitis auslösen, vor allem bei empfindlichen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Asteraceae-Pollen; Kreuzreaktionen mit anderen Korbblütlern möglich) | `species.allergen_info.pollen_allergen` |

> **ASPCA-Einstufung:** Dahlia spp. sind als toxisch für Hunde, Katzen und Pferde gelistet. Symptome: Erbrechen, Durchfall, Hautreizung, Speichelfluss. Nicht lebensbedrohlich, aber Tierarzt-Rücksprache empfohlen. Für Menschen gelten Dahlienblüten traditionell als essbar (Zierblume im Salat), Knollen wurden historisch als Nahrungsmittel genutzt.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest (Stängel nach erstem Frost oder Ende der Saison auf 10–15 cm zurückschneiden vor dem Ausgraben) | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (Oktober/November nach erstem Frost) | `species.pruning_months` |

> **Zusätzliche Kulturmaßnahmen:** Pinching (Entspitzen) bei ca. 30 cm Höhe und 4 Blattpaarpaaren fördert buschigen Wuchs und mehr Blütentriebe. Disbudding (Knospenselektion) — Entfernung der Seitenknöpfe je Trieb — ergibt größere Einzelblüten (wichtig für Schnittblumen/Ausstellungen). Laufendes Deadheading (Blütenentfernung nach Verblühen) verlängert die Blütezeit erheblich.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (BB-Sorten im großen Kübel möglich, aber anspruchsvoll) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–40 (mindestens 30 L für eine Knolle; Topf muss stabil genug für 80–120 cm Wuchshöhe sein) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 35 (Knollen brauchen 10–15 cm Pflanztiefe + Wurzelraum darunter) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 90–120 (typisch; bei gutem Boden und Pinching 80–100 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–70 (ausladend durch Seitentriebe nach Pinching) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–80 (Reihenabstand 60 cm, Pflanzenabstand 60–80 cm) | `species.spacing_cm` |
| Indoor-Anbau | no (Außenpflanze; kein sinnvoller Indoor-Anbau ohne Kunstlicht-Volllicht) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (im großen Kübel, windgeschützter Standort; Stütze nötig) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (liebt volle Sonne und Freiluft; Treibhaus nur für Voranzucht) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Stab oder Käfig direkt beim Pflanzen setzen, vor allem bei BB/Dinnerplate-Sorten) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, humusreiche Pflanzerde (z. B. Kübelpflanzenerde + 20 % Perlite). pH 6,2–6,8. Keine staunasse Erde — Knollenfäule! Im Kübel Drainageschicht (Blähton, 3–5 cm) am Boden. | — |
| Substrat-Empfehlung (Freiland) | Lockerer, humusreicher, gut drainierter Lehmboden. pH 6,0–7,0. Vor dem Pflanzen 5–8 cm Kompost einarbeiten. Sandige Böden mit Kompost verbessern, schwere Lehmböden auflockern. Staunässe ist tödlich für die Knollen. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht (Jahresrhythmus Mitteleuropa)

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz | is_recurring |
|-------|-------------|-------------|----------|---------------|----------------|--------------|
| Knospen-Erwachen (Austrieb aus Knolle) | 14–28 | 1 | false | false | low | true |
| Sämling/Jungpflanze | 21–35 | 2 | false | false | low | true |
| Vegetativ (Vegetatives Wachstum) | 28–42 | 3 | false | false | medium | true |
| Knospenansatz (Blütenvorbereitung) | 14–21 | 4 | false | false | medium | true |
| Blüte (Flowering) | 56–98 | 5 | false | true | medium | true |
| Seneszenz (nach erstem Frost) | 7–14 | 6 | true | false | high | true |
| Dormanz (Knolleneinlagerung) | 120–180 | 7 | false | false | high | true |

> **Perennial-Modus:** 'Great Silence' ist eine Knollenpflanze mit jährlich wiederkehrendem Zyklus. `is_recurring: true` auf allen Phasen. Der Zyklus beginnt jedes Jahr neu mit dem Knospen-Erwachen der eingelagerten Knolle (März/April) bzw. dem Vorziehen. Die `dormancy`-Phase entspricht der frostfreien Knolleneinlagerung im Winter (November bis März).

### 2.2 Phasen-Anforderungsprofile

#### Phase: Knospen-Erwachen / Austrieb

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 (helles, indirektes Licht beim Vorziehen innen; volle Sonne sobald draußen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 (innen mit Kunstlicht oder Fensterbank) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (natürliches Frühlingslicht; kein künstlicher Zusatz nötig) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Außenluft; kein Zusatz) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (sparsam! Knolle fault bei Staunässe) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (wenig bis Austrieb sichtbar) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Jungpflanze (nach Auspflanzen / Abhärtung)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (volle Sonne ab Freilandpflanzung anstreben) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 (volle Außensonne Mai/Juni) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (natürliches Frühsommerlicht) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 (je nach Regen und Wärme) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

> **Abhärtung (Hardening-off):** 7–10 Tage vor der endgültigen Auspflanzung die Voranzucht täglich für einige Stunden ins Freie stellen (schrittweise Gewöhnung an Wind, Sonne, Temperaturschwankungen). REQ-003 AB-009 Pikier-Übergang-Annotation anwendbar.

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–900 (volle Sonne, min. 6 Stunden direkte Sonne täglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 (Freiland Volllicht) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (je nach Temperatur; Dahlien sind relativ durstig) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2000 (Boden gleichmäßig feucht halten, nie staunass) | `requirement_profiles.irrigation_volume_ml_per_plant` |

> **Pinching-Zeitpunkt:** In dieser Phase (bei ca. 30 cm / 4 Blattpaarpaaren) den Haupttrieb auf 2–4 Blattpaarpaare entspitzen. Fördert 4–8 Seitentriebe statt einem Hauptstängel.

#### Phase: Knospenansatz

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–900 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (abnehmende Tageslänge ab Juli fördert Blütenansatz) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1500–2500 (Dahlien brauchen in der Blütephase viel Wasser) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (Hauptphase)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 600–900 (volle Sonne unbedingt) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 (auch bei kürzeren Herbsttagen noch ausreichend) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 (Kurztagspflanze blüht bei unter 14 Stunden Tageslicht) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 (Hitzestress über 30 °C hemmt Blütenöffnung) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 (hohe Luftfeuchtigkeit fördert Mehltau!) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (bei Hitze täglich kontrollieren) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–3000 (in Blüte und bei Hitze maximal wasserversorgend) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Seneszenz (nach erstem Frost bis Ausgraben)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | null (Seneszenz — Freiland, kein Lichtmanagement; Pflanze stirbt ab) | `requirement_profiles.light_ppfd_target` |
| Gießintervall (Tage) | 0 (kein Gießen; Stängel werden abgeschnitten) | `requirement_profiles.irrigation_frequency_days` |
| Temperatur Tag (°C) | 0–10 (Übergangsphase; Frost beendet Vegetationsperiode) | `requirement_profiles.temperature_day_c` |

#### Phase: Dormanz (Knolleneinlagerung)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 (dunkel einlagern) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag/Nacht (°C) | 4–10 (Optimum 7 °C; unter 0 °C = Knolle erfriert und stirbt) | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit (%) | 60–75 (zu trocken < 60% = Knolle schrumpelt; zu feucht > 80% = Botrytis-Fäulnis) | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 0 (kein Gießen während Dormanz; nur gelegentlich auf Fäulnis kontrollieren) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | K (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|---------|
| Austrieb | 1:0:0 (kein oder minimaler N; Knolle versorgt sich selbst) | 0.0–0.4 | 6.0–6.8 | — | — | — | — |
| Jungpflanze | 2:1:1 (moderat N für Aufbau) | 0.6–1.0 | 6.2–6.8 | 80 | 30 | — | — |
| Vegetativ | 3:1:2 (N-betont; Hornspäne oder organischer N) | 0.8–1.4 | 6.0–6.8 | 100 | 40 | — | — |
| Knospenansatz | 1:2:3 (Umstieg auf P/K-Betonung) | 1.0–1.4 | 6.0–6.5 | 80 | 50 | — | — |
| Blüte | 1:3:3 (Niedrig-N, hoch P+K; z. B. 5-10-10 oder 0-10-10) | 0.8–1.2 | 6.0–6.5 | 80 | 50 | — | — |
| Seneszenz | 0:0:1 (K für Knollenaufbau; ab August wöchentlich) | 0.4–0.8 | 6.0–6.5 | — | — | — | — |
| Dormanz | 0:0:0 (kein Dünger) | 0.0 | — | — | — | — | — |

> **Wichtig:** Die häufigste Fehldüngung bei Dahlien ist zu viel Stickstoff in der Blütephase — das Ergebnis sind prächtige Büsche mit wenigen oder gar keinen Blüten. Ab Knospenansatz (ca. 4–6 Wochen nach Auspflanzung) auf N-arme, P/K-reiche Formulierungen wechseln.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Zeitrahmen/Bedingung | Bedingungen |
|------------|---------|----------|-------------|
| Dormanz → Austrieb | time_based / manual | März–April (Bodentemp. > 10 °C) | Sichtbare Knospen an Kronenstumpf |
| Austrieb → Jungpflanze | time_based | 14–28 Tage nach Aktivierung | Erstes echtes Blattpaar sichtbar, Pflanzung ins Freiland |
| Jungpflanze → Vegetativ | manual | 21–35 Tage nach Auspflanzung | Pflanze 20–30 cm hoch, gut etabliert |
| Vegetativ → Knospenansatz | event_based / time_based | 28–42 Tage nach Auspflanzung | Erste Blütenknospen sichtbar (Erbsengröße) |
| Knospenansatz → Blüte | event_based | 14–21 Tage nach Knospenansatz | Erste Blüte geöffnet |
| Blüte → Seneszenz | event_based | Erster Frost (unter 0 °C) Oktober/November | Frost schwärzt Triebe; sofort auf 10–15 cm zurückschneiden |
| Seneszenz → Dormanz | manual | 7–14 Tage nach Frost | Knollen ausgraben, trocknen (2–5 Tage), einlagern |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch / Flüssigdünger (Topf und Freiland ergänzend)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Flüssig-Blühdünger 5-10-10 | Compo / Manna | base | 5-10-10 | 5 ml/L alle 2–3 Wo. | 2 | Blüte |
| Kalidünger (Kaliumsulfat) | Haifa / Compo | supplement | 0-0-50 | 1–2 g/m² monatlich | 3 | Blüte, Seneszenz |
| Tomaten-Dünger flüssig | Compo Expert | base | 8-12-24 (plus Mg) | 10 ml/10 L alle 2 Wo. | 2 | Knospenansatz, Blüte |
| Seramis Blühpflanzendünger | Seramis | base | 6-4-7 | 5 ml/L wöchentlich | 2 | Vegetativ |

#### Organisch (Freiland — empfohlen als Hauptversorgung)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne (langsamer N) | Oscorna / Cuxin | organisch | 60–80 g/m² | Frühjahr (April) | Vegetativphase |
| Kompost (reif) | eigen | organisch | 5–8 L/m² | Frühjahr vor Pflanzung | Bodenverbesserung, alle Phasen |
| Guano-Granulat | Plantafol / Cuxin | organisch | 50 g/m² | April–Juni | Vegetativ |
| Kaliumsulfat-Granulat (Patentkali) | K+S / Kali-Produkte | mineralisch | 20–30 g/m² | Juli–August | Knospenansatz, Blüte, Knollenaufbau |
| Brennnesseljauche (1:10) | eigen / Dehner | organisch | 2 L/m² | Mai–Juli (alle 2 Wo.) | Vegetativ (N-Ergänzung) |

### 3.2 Düngungsplan (Freiland — Mitteleuropa, Saisonverlauf)

| Zeitraum | Phase | Dünger | Menge/Methode | Hinweise |
|----------|-------|--------|--------------|----------|
| April (vor Pflanzung) | — | Kompost + Hornspäne | 5 L/m² Kompost + 70 g/m² Hornspäne einarbeiten | Basisdüngung für gesamte Saison |
| Mai–Juni | Jungpflanze/Vegetativ | Brennnesseljauche 1:10 | 2 L/m² alle 14 Tage | Förderung des vegetativen Aufbaus |
| Mitte Juni | Vegetativ | Guano-Granulat | 50 g/m², einarbeiten | Letzter N-betonter Schub vor Umstieg |
| Ab ca. 4.–6. Woche nach Pflanzung | Knospenansatz | Umstieg auf Tomaten-Dünger oder 5-10-10 | 10 ml/10 L, wöchentlich | Kein N-betonter Dünger mehr ab jetzt! |
| Juli–September | Blüte | 5-10-10 flüssig oder Patentkali | alle 2–3 Wo. flüssig / 25 g/m² Granulat monatlich | P/K-Fokus; laufend Deadheaden |
| August–Oktober | Blüte + Knollenaufbau | Patentkali | 25 g/m² | Kalium fördert Knollenentwicklung für Überwinterung |
| Oktober/November | Seneszenz | Kein Dünger mehr | — | Erste Fröste; Stängel kürzen; Ausgraben vorbereiten |

### 3.3 Mischungsreihenfolge (Flüssigdünger im Kübel)

> **Kritisch:** Reihenfolge verhindert Ausfällungen

1. Wasser mit Raumtemperatur (18–20 °C) bereitstellen
2. Ggf. Silikat-Additive (selten bei Dahlien notwendig)
3. CalMag (falls Osmosewasser oder sehr weiches Wasser; Dahlien bevorzugen kein extrem weiches Wasser)
4. Haupt-Blühdünger (z. B. 5-10-10 flüssig) einrühren
5. Eventuelle Kalium-Supplemente
6. pH-Kontrolle und Korrektur (Ziel: 6,2–6,8)

### 3.4 Besondere Hinweise zur Düngung

**Stickstoff-Falle:** Die häufigste Fehldüngung! N-reiche Allzweckdünger (z. B. 20-20-20 oder Rasendünger) führen zu massivem Blattwuchs mit wenigen Blüten. Dahlien brauchen nur in den ersten 4–6 Wochen nach Auspflanzung moderat Stickstoff. Danach strikt auf P/K-betonte Produkte umsteigen.

**Biologischer Anbau:** Mit Hornspänen + Kompost + Brennnesseljauche + Patentkali lässt sich 'Great Silence' vollständig biologisch und ertragsreich kultivieren — die organischen Dünger werden empfohlen.

**Kübel-Dahlien:** Kübelpflanzen brauchen häufigere Düngung (alle 1–2 Wochen flüssig) da Nährstoffe durch häufiges Gießen ausgewaschen werden. Langsam-Dünger-Tabletten (Osmocote o. ä.) können als Grundversorgung eingearbeitet werden.

**Kalkempfindlichkeit:** Dahlien reagieren auf extremes Gießwasser (pH > 8,0 oder hohe Kalk-EC) mit Eisenmangel (Chlorose zwischen Blattadern). Regenwasser oder kalkärmeres Wasser ist vorzuziehen. Bei hartem Leitungswasser pH-senkende Bodenhilfsstoffe (Schwefelkalk, saurer Torf) verwenden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom (eigenes Outdoor-Profil; kein Standardpreset passend für Knollenpflanzen) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–3 (bei Hitze täglich kontrollieren) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0 (kein Gießen während Dormanz-Einlagerung) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain (tief durchgießen, Staunässe vermeiden; Tröpfchenbewässerung ideal) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leicht saures bis neutrales Wasser bevorzugt (pH 6,0–7,0). Bei hartem Leitungswasser (EC > 0,8 mS) Regenwasser zumischen. Nie auf Blüten spritzen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 (flüssig); 30 (Granulat) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5, 6, 7, 8, 9 (Mai bis September) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jährliches Neu-Einpflanzen nach Dormanz) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wöchentlich auf Blattläuse, Ohrwürmer, Spinnmilben kontrollieren) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Outdoor; nicht steuerbar; aber bei zu hoher LF Mehltau-Prävention) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Knollenkontrolle | Eingelagerte Knollen auf Fäulnis, Austrocknung und Schimmel prüfen. Weiche oder schwarze Stellen herausschneiden, mit Holzkohlepulver desinfizieren. | mittel |
| Feb | Knollenkontrolle + Saatgutbestellung | Letzte Kontrolle; ggf. neue Sorten bestellen | niedrig |
| Mär | Voranzucht starten | Knollen in Töpfe (Mindestgröße 15 cm Ø) mit leicht feuchter Erde setzen, bei 16–18 °C hell stellen. Erste Triebe nach 2–4 Wochen. | hoch |
| Apr | Pikieren / Topf aufstellen | Bei mehreren Augen pro Knolle: in Jungpflanzentöpfe pikieren. Frühester Auspflanztermin in geschützten Lagen (Südlage, Folien-Tunnel). | hoch |
| Mai (nach 15.) | Auspflanzen ins Freiland | Nach den Eisheiligen in vorbereitetes Beet pflanzen (Tiefe: 8–10 cm Knollenoberkante). Stütze sofort setzen. Tröpfchenbewässerung verlegen. | sehr hoch |
| Mai–Jun | Pinching | Bei 30 cm und 4 Blattpaarpaaren Haupttrieb entspitzen. Fördert 4–8 Seitentriebe. | hoch |
| Jun | Vegetative Düngung, Mulchen | Brennnesseljauche oder organischer N-Dünger; 5 cm Mulch gegen Austrocknung und Unkraut. | mittel |
| Jul | Beginn Blütendüngung, Disbudding | Umstieg auf P/K-Dünger. Disbudding für große Blüten (Seitenknöspchen entfernen). Laufendes Deadheading. | hoch |
| Aug | Blütepflege, Schnittblumenernte | Regelmäßig Blüten schneiden (morgens mit langem Stiel), um Neubildung anzuregen. Kaliumdüngung für Knollenaufbau. | hoch |
| Sep | Letzte Ernte, Schädlingskontrolle | Auf Botrytis und Mehltau achten (Herbstnebel). Letzte Blüten ernten. | mittel |
| Okt | Auf Frost warten + Ausgraben | Nach dem ersten Frost (der Laub schwärzt) 7–14 Tage warten, dann Stängel auf 10–15 cm kürzen und Knollen sorgfältig ausgraben. | sehr hoch |
| Nov | Knollen trocknen und einlagern | 2–5 Tage kopfüber trocknen lassen, dann in Kisten mit Vermiculit, Perlite oder Sägemehl bei 4–10 °C dunkel einlagern. Keine Plastiktüten! | sehr hoch |
| Dez | Ruhe / Kontrolle | Ggf. erste Knollenkontrolle. Saisons-Auswertung, neue Sorten planen. | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | dig_and_store (Standardvorgehen für Mitteleuropa Zone 7–8) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | dig_store (Knollen ausgraben, trocknen, einlagern) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, nach erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | replant (Knollen aus Lager nehmen, vorziehen und wieder auspflanzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 (März: Voranzucht starten) / 5 (Mai: Auspflanzung) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 4 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark (dunkel; kein Licht nötig im Ruhezustand) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | none (kein Gießen; nur Kontrollblick auf Fäulnis/Austrocknung) | `overwintering_profiles.winter_watering` |

> **Einlagerungs-Protokoll:**
> 1. Stängel nach erstem Frost auf 10–15 cm zurückschneiden
> 2. Knollen sorgfältig (mind. 30 cm Abstand vom Stängel) ausgraben
> 3. Erde abschütteln (nicht waschen! Nur grobe Klumpen entfernen)
> 4. Kopfüber 2–5 Tage trocknen lassen (Restfeuchtigkeit aus den Hohlräumen läuft ab)
> 5. In offenen Kisten oder Netzen mit trockenem Vermiculit, Perlite, Sägemehl oder Kokosfasern einbetten
> 6. Frostfrei bei 4–10 °C dunkel lagern (Keller, frostfreie Garage, Gewächshaus mit Heizung)
> 7. Monatlich kontrollieren; weiche/faule Stellen sofort herausschneiden
>
> **Zone-8-Alternative:** In milden Regionen (Zone 8, Winterminima selten unter -5 °C) können Knollen mit 20–30 cm Mulchdecke (Stroh, Laub) im Boden überwintern — aber nur auf gut drainiertem Boden, da Staunässe im Winter tödlicher ist als Kälte.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Myzus persicae / Macrosiphum euphorbiae | Kräuselnde, verklebte Blätter; Honigtaubelag; Rußtau-Bildung; Virusübertragung | leaf, stem, bud | Jungpflanze, Vegetativ | easy |
| Ohrwürmer | Forficula auricularia | Unregelmäßige Fraßlöcher an Blüten und Blättern, besonders nachts; ambivalent — fressen auch Blattläuse und Schildläuse (Nützlingswirkung); Bekämpfung abwägen | flower, leaf | Blüte | medium (nachtaktiv) |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, silbrig-punktierte Blätter (Stippling), Blattunterseite befallen; bei Hitze und Trockenheit | leaf | Vegetativ, Blüte (Hitze) | medium |
| Thripse | Frankliniella occidentalis | Silbrig-weiße Flecken/Streifenmuster auf Blütenblättern, verkümmerte Blüten, Narben | flower, leaf | Blüte | difficult |
| Schnecken & Nacktschnecken | Arion spp. / Deroceras spp. | Fraß an jungen Trieben und Blättern (charakteristische Fraßspur mit Schleimspur) | leaf, stem | Austrieb, Jungpflanze | easy |
| Drahtwurm (Larve Saatschnellkäfer) | Agriotes spp. | Fraß an Knollen und Wurzeln; Einlagerungsverluste | root/tuber | Dormanz, Austrieb | difficult |
| Weichhautzikaden | Empoasca spp. | Blattrandbräunung (Hopperburn), Vergilbung | leaf | Vegetativ, Blüte | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau (Powdery Mildew) | fungal (Erysiphe cichoracearum) | Weißer, mehliger Belag auf Blattoberseite; Blätter vergilben und fallen ab | Trockene Luft + hohe Luftfeuchtigkeit nachts; kein Luftzug | 5–10 | Blüte (Spätsommer/Herbst) |
| Grauschimmel (Botrytis) | fungal (Botrytis cinerea) | Grauer, fluffiger Schimmel auf Blüten und Stängeln; Blüten verfaulen; nasse Stellen an Stängeln | Hohe Luftfeuchtigkeit, schlechte Luftzirkulation, Regen auf Blüten, Verletzungen | 3–7 | Blüte (Herbst, Regen) |
| Dahlia-Mosaikvirus (DMV) | viral (Dahlia mosaic virus) | Mosaik-/Schachbrettmuster auf Blättern; Chlorose entlang Blattadern; Kümmerwuchs, reduzierte Blütenbildung | Blattläuse als Vektoren; infiziertes Vermehrungsmaterial; kontaminierte Werkzeuge | variabel | alle Phasen |
| Tomatenbronzefleckenvirus (TSWV) | viral (Tomato spotted wilt virus) | Gelb-braune konzentrische Ringe auf Blättern; Nekrosen; Triebspitzenschaden | Thripse als Vektoren | variabel | alle Phasen |
| Knollenfäule / Schwarzbeinigkeit | bacterial/fungal (Erwinia, Pythium, Rhizoctonia) | Stängel-Basis schwärzt und fault; Knolle weich, übel riechend | Staunässe, Verletzungen beim Einpflanzen/Ausgraben | 5–14 | Austrieb, Dormanz |
| Verticillium-Welke | fungal (Verticillium dahliae) | Einseitiges Welken; braune Vaskulatur im Stängel-Querschnitt; Blattchlorose | Kontaminierter Boden; Staunässe | 7–21 | Vegetativ, Blüte |
| Dahlia-Stengelräude (Dahlia Smut) | fungal (Entyloma dahliae) | Rundliche weiße bis braune Flecken auf Blättern; selten; primär ältere Literatur | Feuchtwarmes Klima | 10–20 | Vegetativ |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea (Florfliege) | Blattläuse, Thripse, Spinnmilben (Larven) | 10–20 Eier oder Larven/m² | 7–14 |
| Coccinella septempunctata (Marienkäfer) | Blattläuse | 5–10 Adulte/m² | sofort wirksam |
| Aphidius colemani (Schlupfwespe) | Blattläuse | 5–10/m² | 7–14 |
| Steinernema feltiae (Nematoden) | Trauermückenlarven, Drahtwurm, Ohrwurm-Larven | 0,5–1 Mio./m² (Gießen) | 3–7 |
| Amblyseius cucumeris (Raubmilbe) | Thripse, Spinnmilben | 50–100/m² | 14–21 |
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilben | 5–10/m² | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff / Mittel | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl / Neem-Extrakt | biological | Azadirachtin | 0,5–1 % Spritzbrühe alle 7–10 Tage | 3 | Blattläuse, Spinnmilben, Thripse, Mehltau |
| Kaliumbicarbonat (z. B. Karma) | biological | Kaliumhydrogencarbonat | 0,5 % Spritzbrühe, alle 7 Tage | 0 | Echter Mehltau |
| Insektizide Seife (Schmierseife) | biological | Kaliumoleat | 1–2 % Spritzbrühe, alle 5–7 Tage | 1 | Blattläuse, Spinnmilben, Weiße Fliege |
| Spinosad (z. B. Neudosan) | biological | Spinosad | Sprühen nach Anleitung | 3 | Thripse, Ohrwürmer |
| Pyrethrum | biological | Pyrethrine (Pyrethrumextrakt) | Sprühen am Abend (Bienenschutz!) | 1 | Blattläuse, Thripse |
| Kupferfungizid (z. B. Cueva) | chemical/biological | Kupferhydroxid | 0,1–0,2 % alle 10–14 Tage | 7 | Botrytis (vorbeugend), Bakterielle Fäulen |
| Schwefelkalkbrühe | cultural/biological | Schwefel | Frühjahr auf Knollen vor Pflanzung | 0 | Pilzsporen, Insekteneier |
| Ohrwurm-Falle (Tontopf mit Stroh) | mechanical | — | Tontopf auf Stab, täglich leeren | 0 | Ohrwürmer |
| Schneckenkorn (Eisenphosphat) | biological | Eisen(III)-phosphat (z. B. Ferramol) | 3–5 g/m² ausstreuen | 0 | Schnecken, Nacktschnecken |
| Mulch (Stroh, Kokosfaser) | cultural | — | 5 cm am Boden | 0 | Bodenfeuchtigkeit, Bodenpilze, Schnecken (gemischt) |

> **Virus-Management:** Für DMV und TSWV gibt es keine Behandlung. Befallene Pflanzen sofort entfernen (nicht kompostieren!). Werkzeuge mit 10 % Bleichmittel-Lösung desinfizieren. Neue Knollen nur von zertifiziert virusfreien Quellen kaufen. Blattläuse (DMV-Vektor) und Thripse (TSWV-Vektor) konsequent bekämpfen.

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | Anmerkung | KA-Edge |
|----------------|-----|-----------|---------|
| Keine bekannten spezifischen Sortenresistenzen für 'Great Silence' | — | Als Cultivar keine publizierten Resistenzangaben; allgemein gilt Dahlia als mäßig anfällig für Mehltau und Viren | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Asteraceae / Korbblütler |
| Empfohlene Vorfrucht | Hülsenfrüchte (Fabaceae: Erbsen, Bohnen) — hinterlassen Stickstoff und lockern Boden; Salate (Schwachzehrer) |
| Empfohlene Nachfrucht | Brassica-Arten (Kohlgemüse; Starkzehrer nutzen das verbesserte Bodengefüge), Wurzelgemüse (Möhren, Sellerie) |
| Anbaupause (Jahre) | 3 Jahre selbe Stelle für Asteraceae (Verticillium-Prophylaxe) |

> **Hinweis:** Da Dahlien als Knollen jährlich ausgegraben werden, ist die klassische Fruchtfolge bei der Beetplanung zu berücksichtigen: nicht jedes Jahr an denselben Platz und nicht nach anderen Asteraceae (Chrysanthemen, Sonnenblumen, Artischocken) pflanzen — geteilte Verticillium-Anfälligkeit.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Studentenblume (Tagetes) | Tagetes patula | 0.9 | Nematoden-Abwehr im Boden; lockt Bestäuber an; Blattläuse-Abwehr durch Duft | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.8 | Blattlaus-Fangpflanze (Aphid trap crop); Bestäuber-Magnet; essbare Blüten | `compatible_with` |
| Koriander | Coriandrum sativum | 0.7 | Zieht Schlupfwespen und Schwebfliegen an (Blattlaus-Feinde); repelliert Blattläuse | `compatible_with` |
| Süßes Alyssum | Lobularia maritima | 0.8 | Zieht Nützlinge an (Schwebfliegen, Parasitoide); Bodenbeschattung | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bestäubermagnet; Duft soll Schädlinge irritieren | `compatible_with` |
| Cosmos | Cosmos bipinnatus | 0.8 | Klassische Dahlienkombination; Bestäuber; Schnittblumen-Ergänzung | `compatible_with` |
| Borretsch | Borago officinalis | 0.7 | Lockt Hummeln an (Bestäubung); Schneckenabwehr (rauer Stängel) | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Starker Duft hält Blattläuse und andere Schädlinge auf Abstand | `compatible_with` |
| Schnittlauch | Allium schoenoprasum | 0.7 | Wie Knoblauch; Pilzabwehr durch Schwefelverbindungen; kompakter Wuchs | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Verbindungen hemmen viele Pflanzennachbarn; Fenchel ist eine Problemstaude im Mischkulturbeet | moderate | `incompatible_with` |
| Andere Asteraceae (Sonnenblumen, Chrysanthemen) | Helianthus, Chrysanthemum | Geteilte Pilzkrankheiten (Verticillium, Botrytis, Echte Mehltau-Erysiphe-Arten); geteilte Schädlingspopulationen | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Geteilte TSWV-Anfälligkeit; Thripse als gemeinsamer Vektor; Bodenpathogene | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Asteraceae (Korbblütler) | `shares_pest_risk` | Verticillium dahliae, Erysiphe cichoracearum, DMV-Vektoren (Blattläuse), TSWV-Vektoren (Thripse) | `shares_pest_risk` |
| Fabaceae (Hülsenfrüchte) | `family_compatible_with` | Stickstoff-Vorfrucht; keine geteilten Hauptschädlinge | `family_compatible_with` |
| Apiaceae (Doldenblütler) | `family_compatible_with` | Nützlingsförderung durch Doldenblüten (Schlupfwespen, Schwebfliegen) | `family_compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art / Sorte | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber 'Great Silence' |
|-------------|-------------------|-------------|-----------------------------------|
| Dahlie 'Café au Lait' | Dahlia × pinnata 'Café au Lait' | Große Informal Decorative, ähnliche Farbpalette (Creme-Pfirsich) | Sehr trend-orientiert, ausgezeichnete Schnittblume; etwas robuster im Schaft |
| Dahlie 'Wizard of Oz' | Dahlia × pinnata 'Wizard of Oz' | BB Informal Decorative, ähnliche warme Töne | Kompakterer Wuchs |
| Dahlie 'Labyrinth' | Dahlia × pinnata 'Labyrinth' | BB Informal Decorative, Apricot/Lachs-Töne | Sehr lang haltbar als Schnittblume |
| Pompon-Dahlie 'Omo' | Dahlia × pinnata 'Omo' | Klein, kugelig, weiß | Kompakter, kein Stützbedarf; einfacher zu kultivieren |
| Einfache Dahlie (Single-Dahlie) | Dahlia × pinnata, einfache Sorten | Bienenfreundlich, offen | Wesentlich mehr Bestäuber-Attraktivität durch offene Blüte |
| Georgine (Pompon/Kugel) | Dahlia × pinnata, Kugel-Typen | Kugelige Blütenform; kompakter | Oft wetterresistenter; weniger Stützaufwand |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile (Elternart)

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,frost_sensitivity,nutrient_demand_level,green_manure_suitable,pruning_type,pruning_months,bloom_months,harvest_months,direct_sow_months,sowing_indoor_weeks_before_last_frost
Dahlia pinnata,Dahlie;Garten-Dahlie;Dahlia;Garden Dahlia,Asteraceae,Dahlia,perennial,short_day,herb,tuberous,"8a;8b;9a;9b;10a;10b;11a;11b",0.0,"Mexiko, Mittelamerika (Hochland)",limited,30,35,90-120,50-70,60,no,limited,false,true,tender,heavy_feeder,false,after_harvest,"10;11","7;8;9;10","7;8;9;10",5,4
```

### 8.2 Cultivar CSV-Zeile ('Great Silence')

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type,photoperiod_type
Great Silence,Dahlia pinnata,Peter Komen,2018,"informal_decorative;dark_blend;coral_pink;golden_center;long_stems;bee_friendly;cut_flower",90,,clone,
```

> **ADS-Klassifikation 'Great Silence':** 3113 (3 = Informal Decorative; 1 = Bloom-Größe BB 10–15 cm; 1 = Dark Blend Farbe; 3 = Dritte Untergruppe). RHS-Registrierung: Dahlia 'Great Silence' (D) — Bedding/Dekorative Gruppe.

---

## 9. Knollen-Zyklus (REQ-022 Sondererfassung)

> **Gemäß REQ-022 User Story Knollen-Zyklus** wird der vollständige Jahreszyklus von Dahliensorten explizit im System abgebildet:

| Status | Zeitraum (Mitteleuropa) | Maßnahme | Erinnerungstyp |
|--------|------------------------|----------|----------------|
| Einlagern | Oktober–November | Ausgraben, Trocknen, in Kisten einlegen | `overwintering_reminder` |
| Eingelagert | November–Februar | Monatliche Kontrolle auf Fäulnis/Austrocknung | `overwintering_check` |
| Vorziehen | März–April | In Töpfe setzen, ins Gewächshaus/Fensterbank | `spring_reminder` |
| Auspflanzen | Mai (nach Eisheiligen) | Freilandpflanzung, Stütze setzen | `spring_reminder` |
| Wachstum | Mai–Juli | Pinching, Düngen, Mulchen | `care_reminder` |
| Blüte | Juli–Oktober | Deadheading, Ernten, Disbudding | `harvest_reminder` |
| Ausgraben vorbereiten | Oktober | Auf Frost warten (ca. 7–14 Tage nach erstem Frost) | `overwintering_reminder` |

---

## Quellenverzeichnis

1. [RHS Plant Database — Dahlia 'Great Silence' (D)](https://www.rhs.org.uk/plants/375276/dahlia-great-silence-(d)/details) — Botanische Einordnung, Kulturhinweise
2. [American Dahlia Society — ADS Classification Guide](https://www.dahlia.org/guide/) — ADS-Klassifikation 3113, Blütentyp, Sortenregistrierung
3. [American Dahlia Society — Nutrients for Dahlias](https://www.dahlia.org/docsinfo/articles/nutrients-for-dahlias/) — NPK-Empfehlungen, Düngungsstrategie
4. [Dahlia Doctor — Don't Fear Nitrogen](https://www.dahliadoctor.com/blogs/second-blog/dont-fear-nitrogen-feed-your-dahlias-right-from-the-start) — Phasenspezifische NPK-Empfehlungen
5. [Gardenia.net — Dahlia 'Great Silence'](https://www.gardenia.net/plant/dahlia-great-silence) — Sortencharakteristik, Wuchsform, Farbdescription
6. [Longfield Gardens — Dahlia Great Silence](https://www.longfield-gardens.com/plantname/Dahlia-Decorative-Great-Silence) — Kultivierungsdetails, Größenangaben
7. [American Meadows — Great Silence Decorative Dahlia](https://www.americanmeadows.com/product/flower-bulbs/great-silence-decorative-dahlia) — Sorteninfo, Pflanzhinweise
8. [UC IPM — Managing Pests in Gardens: Dahlia](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html) — IPM-Strategien, Schädlinge, Behandlungsmethoden
9. [ASPCA — Toxic and Non-toxic Plants: Dahlia](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dahlia) — Toxizitäts-Einstufung
10. [Longfield Gardens — How to Overwinter Dahlias](https://www.longfield-gardens.com/article/how-to-overwinter-dahlias) — Überwinterungsprotokoll
11. [Gardener's Path — Dahlia Companion Plants](https://gardenerspath.com/plants/flowers/dahlia-companion-plants/) — Mischkultur-Empfehlungen
12. [Epic Gardening — Dahlia Companion Plants](https://www.epicgardening.com/dahlia-companion-plants/) — Mischkultur-Empfehlungen
13. [American Dahlia Society — Dahlia Mosaic Virus](https://dahlia.org/wp-content/uploads/2018/01/ADS-DMV_Symptoms_Slides.pdf) — Virus-Erkennung und -Management
14. [Old Farmer's Almanac — Dahlias Growing Guide](https://www.almanac.com/plant/dahlias) — Allgemeine Kulturhinweise Mitteleuropa-Adaption
15. [Missouri Botanical Garden — Dahlia (group)](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a445) — Taxonomische Einordnung
16. [Longfield Gardens — How to Pinch and Stake Dahlias](https://www.longfield-gardens.com/article/how-to-pinch-and-stake-dahlias/) — Pinching, Disbudding, Staking
17. [Dahlias.com — Dahlia Fertilizing Tips (Swan Island)](https://www.dahlias.com/blog/growing-tips/dahlia-fertilizing-tips/) — Düngungsplan, Produktempfehlungen
