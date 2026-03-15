# Dahlie 'Lavender Perfection' — Dahlia pinnata 'Lavender Perfection'

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:** American Dahlia Society, UC IPM Dahlia Guide, Longfield Gardens, Missouri Botanical Garden, ASPCA Toxic Plants Database, Swan Island Dahlias, Gardenia.net, Holland Bulb Farms, Floret Flower Farm Library

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dahlia pinnata Cav. | `species.scientific_name` |
| Volksnamen (DE/EN) | Dinner-Plate-Dahlie Lavendel, Grossblumige Dahlie Lavendel; Lavender Perfection Dinnerplate Dahlia | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Dahlia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | `herb` (krautige Staude mit aufrechtem Stängel) | `species.growth_habit` |
| Wurzeltyp | `tuberous` (Knollenbildung als Speicherorgan; Fiberwurzeln zusätzlich an der Knolle) | `species.root_type` |
| Lebenszyklus | `perennial` (botanisch mehrjährig; in Mitteleuropa Zone 6–7 als Sommerknollen-Pflanze kultiviert — Knollen müssen frostfrei überwintert werden) | `lifecycle_configs.cycle_type` |
| Photoperiode | `short_day` (fakultativ; Blüteninitiierung bei Nachtlänge > 12 h gefördert, Dahlien blühen jedoch auch unter Langtagbedingungen; Tuberisierung eindeutig kurztaggesteuert bei Nacht > 12 h; in Mitteleuropa natürlicher Blühbeginn ab Mitte/Ende Juli) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a, 8b, 9a, 9b, 10a, 10b, 11a (winterhart in Boden); Zonen 3a–7b: Knollen ausgraben | `species.hardiness_zones` |
| Frostempfindlichkeit | `tender` (Knollen erfrieren bereits bei leichtem Bodenfrost; oberirdische Triebe bei 0 °C) | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht winterhart unter Zone 8. Knollen erfrieren ab -2 °C im Boden. In Mitteleuropa (Zone 6–7) Knollen nach dem ersten Frost ausgraben, bei 4–10 °C frostfrei und dunkel lagern. Auspflanzen erst nach dem letzten Frost (Mitte Mai). | `species.hardiness_detail` |
| Heimat | Gartenherkunft (Kulturhybride von Dahlia pinnata Cav.). Elternarten stammen aus Mexiko und Guatemala (Hochland, 1500–3000 m ü. NN). Synonyme: Dahlia x hybrida (Handelsbezeichnung), Dahlia variabilis Willd. (veraltet). | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral — keine allelopathischen Wirkungen nachgewiesen) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | `heavy_feeder` (Starkzehrer — grosse Blüten und aktives Knollenwachstum erfordern kontinuierliche Nährstoffversorgung; insbesondere P und K) | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | `['ornamental', 'bee_friendly', 'fragrant']` (Hauptsaechlich Zierpflanze; Bienenmagnete wenn Blüten zugänglich; leichter Duft bei einigen Exemplaren) | `species.traits` |

**Sortenbeschreibung 'Lavender Perfection':**
Grosse Dinner-Plate-Dahlie (Dekorative Grossblumendahlie, Formal Decorative Type) mit vollgefüllten Blüten von 20–25 cm Durchmesser in lavendel-pink bis mauve-lila Farbtönen. Die breiten, flachen, leicht gewellten Blütenblätter (Ray Florets) sind an den Spitzen abgerundet. Exzellente Schnittblumen-Eigenschaft; hitzetolerant; stark verzweigend bei korrektem Pinching. Reife 80–100 Tage nach Auspflanzen.

### 1.2 Aussaat- & Erntezeiten

Mitteleuropa (Zone 6–7), Bezugspunkt: letzter Frost Mitte Mai.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 4–6 (Knollenvorkultur im Topf ab Mitte März; Samenanzucht ab Februar möglich, aber bei Hybriden nicht sortenecht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (Knollen direkt auspflanzen nach letztem Frost, Boden min. 15 °C) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5 (Auspflanzen der Knollen in Mitteleuropa ab Mitte Mai) | `species.direct_sow_months` |
| Erntemonate | null (Zierpflanze; `allows_harvest: false` auf Wachstumsphasen; Schnittblumen-Ernte: 7, 8, 9, 10) | `species.harvest_months` |
| Blütemonate | 7, 8, 9, 10 (Blühbeginn Mitte Juli bis zum ersten Frost, typisch Oktober in Mitteleuropa) | `species.bloom_months` |

**Hinweis Schnittblumenernte:** Als Schnittblume geerntet werden Stiele von 40–60 cm Länge. Erntezeitpunkt: Wenn 2–3 äussere Blütenreihen vollständig geöffnet sind, Blüte noch nicht voll aufgegangen. Früh morgens schneiden. Im Wasser sofort in kühle Umgebung (4–8 °C) stellen. Haltbarkeit: 5–8 Tage.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | `cutting_stem`, `division` (Knollenteilung im Frühjahr ist Standard; Stecklinge vom austreibenden Knollenauge März–April ebenfalls möglich; Samen = nicht sortenecht bei Hybriden) | `species.propagation_methods` |
| Schwierigkeit | `moderate` (Knollenteilung erfordert Erfahrung: jedes Teilstück muss mindestens ein Auge haben; Stecklinge bewurzeln zuverlässig bei 18–20 °C Bodentemperatur) | `species.propagation_difficulty` |

**Knollenteilung (empfohlene Methode):**
1. Knollenstock im März/April bei Austreibung unter Licht in feuchtes Substrat legen
2. Wenn Augen ca. 1–2 cm sichtbar: Teilung mit scharfem, desinfizierten Messer
3. Jedes Teilstück braucht Augenpunkt an der Basis des Hauptstängels (Hals)
4. Schnittstellen mit Holzkohlepulver oder Cinnamon bestäuben, antrocknen lassen
5. Separation: Einzelknollen ohne Auge sind wertlos — nicht einpflanzen

**Stecklinge:**
- Triebspitzen von 8–10 cm Länge vom vortreibenden Knollenstock schneiden
- Substrat: Perlite/Kokos 50/50, Bodenheizung 20 °C
- Bewurzelung: 14–21 Tage, hohe Luftfeuchtigkeit (Abdeckung)
- Sortenechte Kopien möglich (identisch mit Mutterpflanze)

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false (ASPCA: unbedenklich für Menschen; nur mild toxisch für Haustiere) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Pflanzenteile (Blätter, Blüten, Knollen); Knollen enthalten höchste Konzentration | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Unbekanntes Toxin (Polyacetylene vermutet); verursacht milde Gastroenteritis und Kontaktdermatitis bei Tieren | `species.toxicity.toxic_compounds` |
| Schweregrad | `mild` (ASPCA: milde GI-Symptome bei Tieren — Erbrechen, Speichelfluss, Durchfall; keine lebensbedrohlichen Fälle dokumentiert) | `species.toxicity.severity` |
| Kontaktallergen | true (Pflanzensaft kann bei Gärtnern Kontaktdermatitis auslösen; Handschuhe bei der Arbeit mit Knollen empfehlenswert) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Insektenbestäubung; gefüllte Blüten setzen wenig Pollen frei in die Luft) | `species.allergen_info.pollen_allergen` |

Quellen: ASPCA Toxic and Non-Toxic Plants Database; Plant Addicts "Are Dahlias Poisonous?"

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | `after_harvest` (Rückschnitt im Herbst nach dem ersten Frost auf 10–15 cm Stumpf vor dem Ausgraben; kein Winterschnitt da Pflanze als Knolle überwintert) | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (Oktober nach erstem Frost; Stiele auf 10–15 cm kürzen, dann Knollen ausgraben) | `species.pruning_months` |

**Pinching (nicht Rückschnitt, sondern Kultivierungsmassnahme):**
Pinching im Frühjahr ist bei Dinner-Plate-Dahlien obligatorisch für optimale Verzweigung:
- Zeitpunkt: Wenn Trieb 4 Blattpaarpaare (ca. 25–30 cm Höhe) entwickelt hat
- Massnahme: Triebspitze über dem 3. Blattknotenpaar ausbrechen (Fingerkuppe)
- Effekt: 4–6 Seitentriebe bilden sich, jeder mit Blütenstiel
- Ohne Pinching: 1 Hauptblüte, weniger Gesamtertrag

**Disbudding (Blütenknospenausdünnen):**
Für maximale Blütengrösse bei Dinner-Plate-Typ:
- Pro Blütenstiel nur die zentrale Knospe behalten
- Die 2 flankierenden Seitenknospen direkt auskneifen
- Ergebnis: Weniger, aber deutlich grössere Blüten (typisch 20–25 cm bei 'Lavender Perfection')

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | `limited` (grosse Knollen brauchen mind. 30–40 L Topfvolumen; regelmässiges Gießen und Düngen intensiver) | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 (Knollen brauchen Tiefe und Stabilität; Kippgefahr bei schmalem Topf) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 90–150 (Longfield Gardens: 36–48"; American Meadows: bis 4–5 Fuss = 120–150 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–90 (nach Pinching stark verzweigend) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 60–90 (Pflanzenabstand Knollen-Mitte zu Knollen-Mitte; grosse Sorte braucht Raum) | `species.spacing_cm` |
| Indoor-Anbau | `no` (benötigt Vollsonne im Aussenbereich; Indoor nicht sinnvoll ausser Vorkultur) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | `limited` (nur auf grossen Balkonen mit mind. 30–50 L Töpfen und Südlage; Sturmgefahr durch Wuchshöhe) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (Freilanduflanze; Gewächshaus nur für Vorkultur und Überwindungsbetrieb sinnvoll) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Pflicht! Bei 'Lavender Perfection' bis 150 cm: Holzpfahl oder Metallstab mind. 150 cm, direkt beim Pflanzen einschlagen; Stängel locker anbinden) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, gut drainierte Kübelpflanzenerde; 20–30 % Perlite oder Bims beimengen gegen Verdichtung und Staunässe. pH 6.0–7.0. Kein Torfsubstrat pur (verdichtet). Für Freiland: Humose, gut durchlässige Gartenerde, pH 6.0–7.0 (Optimum 6.2–6.8; bei pH > 7.0 treten Fe/Mn-Mangel und Chlorose auf). | — |

---

## 2. Wachstumsphasen

Dahlia 'Lavender Perfection' wird in Mitteleuropa als Knollenstaude mit jährlichem Zyklus kultiviert. Die folgende Phasenstruktur beschreibt den vollständigen Jahreszyklus von der Vorkultur bis zur Knollen-Einlagerung.

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Vorkultur / Austrieb | 21–35 | 1 | false | false | low |
| Vegetatives Wachstum | 28–42 | 2 | false | false | medium |
| Knospenbildung | 14–21 | 3 | false | false | medium |
| Blüte | 56–84 | 4 | false | false | medium |
| Seneszenz / Absterbephase | 7–14 | 5 | false | false | high |
| Dormanz (Lagerung) | 120–180 | 6 | true | false | high |

**Hinweis zu `is_terminal` und `is_recurring`:** Die Dormanz-Phase ist die letzte Phase des Jahres-Zyklus. Da Dahlien in Mitteleuropa jährlich neu ausgepflanzt werden, ist `is_recurring: true` auf den Wachstumsphasen 1–5 (Wiederholung jedes Jahr) sinnvoll. Die Knollen-Dormanzphase ist `is_terminal: true` für den aktuellen Jahreszyklus, triggert aber durch `is_cycle_restart: true` den nächsten Saison-Zyklus.

### 2.2 Phasen-Anforderungsprofile

#### Phase 1: Vorkultur / Austrieb (März–Mai indoor, dann Outdoor)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 (indoor Vorkultur); Vollsonne outdoor nach Abhärtung | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 (hell, aber noch kein Hochsommer-Tageslicht) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (natürliches Tageslicht März–Mai) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 (kühle Vorkultur verhindert Vergeilung; zu warm = schwache etiolierte Triebe) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Umgebungsluft, kein CO₂-Zusatz notwendig) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (Knollen nicht zu feucht — Fäulnisrisiko hoch bei kaltem Substrat) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 (je nach Topfgrösse; Substrat leicht feucht, nicht nass) | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Kulturhinweis:** Knollen nicht sofort nach dem Einpflanzen giessen — erst wenn erste Triebe sichtbar sind (ca. 2–3 cm). Staunässe vor dem Austrieb führt zu Knollenfäule (Sclerotinia, Pythium). Abhärtung (Hardening Off) 7–10 Tage bei 10–15 °C im Freien bevor Auspflanzen.

#### Phase 2: Vegetatives Wachstum (Mai–Juli, Outdoor)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (Vollsonne bevorzugt; mind. 6 Stunden direkte Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 (Hochsommersonne in Mitteleuropa) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (lange Sommertage; vegetatives Wachstum durch Langtag gefördert) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 (optimal; über 32 °C Hitzestress möglich) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (Freiland) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 (bei heissem Wetter täglich; Dahlien sind Starkwasserverbraucher) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–3000 (ausgewachsene Pflanze; Freiland tief giessen, nicht oberflächlich) | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Pinching-Zeitpunkt:** In dieser Phase, wenn Pflanze ca. 25–30 cm (4 Blattpaarpaare), wird gepincht.

#### Phase 3: Knospenbildung (Juli)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (Vollsonne weiter essenziell) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 13–14 (Tageslänge nimmt ab Juli ab — löst Blüteninduktion aus) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–16 (kühlere Nächte fördern Blütenbildung und Farbintensität) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.9–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Disbudding:** In dieser Phase werden Nebenknospen ausgebrochen für maximale Blütengrösse.

#### Phase 4: Blüte (Juli–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (Vollsonne; Schatten reduziert Blütengrösse und Farbintensität) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–28 (Herbst: DLI nimmt natürlich ab, Blüte bleibt bis Frost) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 (kürzere Tage halten Blüte aufrecht; zu kurze Tage < 10 h Seneszenz) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 (kühle Herbsttage fördern reichhaltige Blüte und Blütenfarbe) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 (Botrytis-Risiko bei hoher Luftfeuchte und kühlen Nächten beachten) | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (je nach Witterung; Herbst: Freiland benötigt weniger Wasser) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 800–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 5: Seneszenz / Absterbephase (nach erstem Frost, Oktober–November)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | irrelevant (Pflanze stirbt oberirdisch ab) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | irrelevant | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | irrelevant | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | -2–10 (Frost tötet Triebe; Knollen noch kurz im Boden lassen um "abzuhärten") | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | -5–5 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | irrelevant | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | irrelevant | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | irrelevant | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | irrelevant | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 0 (kein Giessen nach erstem Frost) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Kulturhinweis:** Nach dem ersten Frost (Triebe schwarz/weich) Stiele auf 10–15 cm kürzen. Knollen erst nach 7–10 Tagen ausgraben (Knollen "reifen" noch kurz nach), dann reinigen, markieren, trocknen lassen (24–48 h), in Lagermaterial (Perlite, Vermiculit, Styropor-Chips) einlagern.

#### Phase 6: Dormanz / Knollenlagerung (November–März)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0 (dunkel lagern) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 0 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 0 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 4–10 (kritisch: unter 0 °C Knollen erfrieren; über 15 °C vorzeitiger Austrieb) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 4–8 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 (zu trocken < 60% = Knollen schrumpeln; zu feucht > 80% = Botrytis-Fäulnis) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | irrelevant | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | irrelevant | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 0 (keine Bewässerung; Knollen nur auf Fäulnis kontrollieren) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Vorkultur/Austrieb | 1:1:1 | 0.4–0.8 | 6.0–6.5 | 80 | 30 | — | 2 |
| Vegetativ | 1:2:2 | 0.8–1.4 | 6.0–6.5 | 120 | 50 | — | 3 |
| Knospenbildung | 0:2:3 | 1.0–1.6 | 6.0–6.5 | 100 | 50 | — | 2 |
| Blüte | 0:2:3 | 1.0–1.6 | 6.0–6.5 | 100 | 50 | — | 2 |
| Seneszenz | 0:0:0 | — | — | — | — | — | — |
| Dormanz | 0:0:0 | — | — | — | — | — | — |

**Wichtigste Nährstoffregel:** Dahlien benötigen NIEDRIG Stickstoff (N), HOCH Phosphor (P) und Kalium (K). Zuviel N = grosses Laub, wenig Blüten, weiche Stängel, schwache Knollen. Empfohlene NPK-Produkt-Verhältnisse: 5-10-10, 2-4-4, 4-18-38, 6-30-30. N sollte maximal halb so hoch sein wie P und K.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/Bedingung | Bedingungen |
|------------|---------|----------------|-------------|
| Vorkultur → Vegetativ | `event_based` | nach Abhärtung (7–10 Tage) | Letzter Frost überschritten; Boden min. 15 °C |
| Vegetativ → Knospenbildung | `time_based` / `event_based` | 28–42 Tage; erste Knospen sichtbar | Pinching abgeschlossen; erste Knospensätze erkennbar |
| Knospenbildung → Blüte | `event_based` | 14–21 Tage | Erste Blüten öffnen sich |
| Blüte → Seneszenz | `event_based` | erster Frost | Triebe schwarz/weich nach Frost |
| Seneszenz → Dormanz | `event_based` | 7–10 Tage nach Frost | Knollen ausgegraben, gereinigt, eingelagert |
| Dormanz → Vorkultur | `time_based` / `manual` | März (Monat 3) | Lagertemperatur auf 15 °C erhöhen; Knollen auf Austrieb prüfen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Topfkultur / ergänzend Freiland)

| Produkt | Marke | Typ | NPK | EC/ml/L ca. | Mischpriorität | Phasen |
|---------|-------|-----|-----|-------------|-----------------|--------|
| Blaukorn / Blühdünger | Hakaphos / Compo | base | 5-10-10 | — | 1 | vegetativ, blüte |
| Flüssig-Blühpflanzendünger | Compo Blühpflanzen | base | 3-7-7 | 0.10 | 2 | knospe, blüte |
| CalMag | Plagron/Canna | supplement | — | 0.05 | 1 | vegetativ, knospe |
| Tomatendünger (NPK 4-8-16) | Substral / Compo | base | 4-8-16 | 0.12 | 2 | knospe, blüte |

**Hinweis Tomatendünger:** Der Tomatendünger mit niedrigem N und hohem K eignet sich hervorragend für Dahlien in der Blüte- und Knospenphase (American Dahlia Society, Swan Island Dahlias).

#### Organisch (Freiland-Beet, empfohlen)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornmehl (schnell) | Oscorna / Compo | organisch N | 30–60 g/m² | Frühjahr (Mai) | Startphase Vegetativ |
| Hornspäne (langsam) | Oscorna / Compo | organisch N | 60–80 g/m² | Frühjahr (Mai) | Depot bis Sommer |
| Kompost (reif) | eigen / Compo | Bodenverbesserer | 3–5 L/m² | Frühjahr (April) vor Auspflanzen | alle Phasen |
| Blaukorn-Granulat (alternativ) | Yara / Hakaphos | mineralisch granuliert | 30–50 g/m² | Mai–August alle 4 Wochen | vegetativ, blüte |
| Brennnesseljauche | eigen | organisch flüssig | 1:10, 1 L/m² | alle 2 Wochen Juni–August | vegetativ (N-Boost) |
| Algenkalk / Urgesteinsmehl | Oscorna | Bodenverbesserer | 100–200 g/m² | Herbst / Frühjahr | Bodenkorrektur pH |

**Kritische Warnung:** Kein Hühnermist oder hoher N-Organik-Dünger nach dem Pinching — fördert übermässiges Blattwachstum auf Kosten der Blüten. Beinwelljauche (kaliumreich) ist organisch ideal ab Knospenphase.

### 3.2 Düngungsplan Freiland (Empfehlung Mitteleuropa)

| Zeitraum | Phase | Massnahme | Produkt / Rate | Hinweise |
|----------|-------|-----------|----------------|----------|
| April (vor Auspflanzen) | Vorbereitung | Bodenverbesserung | Kompost 3–5 L/m², Hornspäne 60–80 g/m² | Gut einarbeiten, 2 Wochen vor Auspflanzen |
| Mitte Mai | Vorkultur/Austrieb | Startdüngung | Hornmehl 40 g/m² | Nur wenn Kompost knapp; sonst weglassen |
| Ende Mai–Juni (Vegetativ) | Vegetativ | Flüssigdüngung | Brennnesseljauche 1:10, alle 14 Tage | NPK ca. 2-1-1 aus Jauche — moderat N |
| Juli (Knospenbildung) | Knospe | Blüh-Boost | Beinwelljauche 1:10 oder Tomatendünger | Jetzt K und P erhöhen, N reduzieren |
| Juli–September (Blüte) | Blüte | Blühdüngung | Flüssig-Blühpflanzendünger alle 3–4 Wochen | NPK 0-2-3 bis 1-3-3, kein Stickstoff-Dünger mehr |
| Oktober (Seneszenz) | Ende | Stopp | Keine Düngung | Stiele kürzen, Knollen ausgraben |

### 3.3 Mischungsreihenfolge (Topfkultur / Hydro-Ergänzung)

> **Kritisch:** Reihenfolge verhindert Ausfällungen

1. Wasser (18–22 °C) vorlegen
2. CalMag (falls Osmosewasser oder weiches Leitungswasser)
3. Blüh-Basis A (Calcium + Mikronährstoffe)
4. Blüh-Basis B (Phosphor + Kalium + Magnesium)
5. Booster (Wurzelstimulator, Humin-/Fulvinsäure)
6. pH-Korrektur IMMER ZULETZT (pH-Ziel: 6.0–6.5 für Boden/Topf)

### 3.4 Besondere Hinweise zur Düngung

**Stickstoff-Überschuss ist der häufigste Fehler bei Dahlien.** Symptome: riesige dunkle Blätter, wenig Blüten, aufgeplatzte Blütenzentren ("blown center"), weiche schwankende Stängel, schlechte Knollenentwicklung.

**Phosphor:** Dahlien brauchen P in der Knospen- und Blütephase; aber Boden bindet P stark. Bodenanalyse vor Saison empfohlen — Über-P-Versorgung blockiert Zink und Eisen-Aufnahme.

**Kalium:** Essenziell für Knollenentwicklung, Stängelsteifigkeit und Blütenfarbe. K-Bedarf ab Knospenphase am höchsten.

**Knollennährstoffe:** In den letzten 4 Wochen der Blütephase (September) baut die Pflanze Stärke in Knollen ein — jetzt kein Stickstoff mehr, da sonst Knollenqualität sinkt.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `frost_tender_tuber` (Knollenstaude — muss ausgegraben werden; Sommerwachstum + Winterlagerung) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2 (bei heissem Wetter täglich; Dahlien sind grosse Wasserverbraucher) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0 (keine Bewässerung während Dormanz/Lagerung) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | `drench_and_drain` (tief giessen bis Wasser unten austritt, dann vollständig ablaufen lassen — Staunässe = Knollenfäule) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | null (Dahlien sind nicht kalkempfindlich; Leitungswasser ist geeignet) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 (alle 3 Wochen Flüssigdünger; im Freiland alle 4 Wochen Granulat) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5, 6, 7, 8, 9 (Mai bis September; Oktober: nur noch Wasser oder gar nichts) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jährlich neu auspflanzen nach Winter-Lagerung) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 (wöchentlich; Blattläuse und Ohrwürmer entwickeln sich schnell) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Freilandpflanze; Luftfeuchte im Freiland witterungsbedingt) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Knollen-Lagerungskontrolle | Knollen auf Fäulnis und Austrocknung kontrollieren; schrumplige Knollen leicht anfeuchten | mittel |
| Feb | Knollen-Lagerungskontrolle | Zweite Kontrolle; Fäulnisstellen grosszügig herausschneiden, Wunde mit Holzkohle behandeln | mittel |
| Mär | Vorkultur starten | Knollen in Anzuchtschalen auf feuchtes Substrat legen; warm (15–18 °C) und hell stellen für Augenentwicklung | hoch |
| Mär | Knollenteilung | Wenn Augen 1–2 cm sichtbar: Knollen teilen; Werkzeug desinfizieren; Wunden antrocknen | hoch |
| Apr | Vorkultur / Topfkultur | Geteilte Knollen in 3-L-Töpfe einpflanzen; Bodenheizung 18 °C; hell, aber nicht zu warm | hoch |
| Mai | Abhärtung (Hardening Off) | Ab Mitte Mai: Pflanzen täglich 1–2 Std. ins Freie; nach 7–10 Tagen auspflanzen | kritisch |
| Mai | Auspflanzen + Stäben | Nach dem letzten Frost (Zone 7: ~15. Mai): Pflanzen mit 60–90 cm Abstand; sofort Pflanzstab (150 cm) setzen | kritisch |
| Mai/Jun | Pinching | Wenn Pflanze 4 Blattpaar-Sets hat (~25 cm): Triebspitze über dem 3. Blattknotenpaar ausbrechen | hoch |
| Jun | Vegetative Pflege | Gießen 2–3 täglich; Unkraut jäten; Mulch auflegen (5 cm Stroh) für Feuchtigkeitserhalt | mittel |
| Jul | Erste Düngung Blüh-Boost | Ab Knospenbildung: auf kaliumreichen Dünger wechseln; Disbudding für Dinner-Plate-Grösse | hoch |
| Jul–Sep | Blütenmanagement | Verblühte Blüten umgehend entfernen (Deadheading) für kontinuierliche Blüte; regelmässig binden | mittel |
| Sep | Endphase Düngung | Letzter Blühdünger; ab Oktober keine Düngung mehr | niedrig |
| Okt | Absterbephase | Nach erstem Frost: Stiele auf 10–15 cm kürzen; Knollen 7–10 Tage im Boden lassen | hoch |
| Okt/Nov | Knollen ausgraben | Mit Grabgabel vorsichtig ausgraben; nicht beschädigen; Knollen beschriften (Sortenname!) | kritisch |
| Nov | Einlagerung | 24–48 h trocknen; in Perlite/Vermiculit/Styropor-Chips einlagern; kühles Lager (4–10 °C) | kritisch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | `dig_and_store` (Knollen müssen ausgegraben werden in Zone 3–7; in Zone 8–10 mulchen möglich) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | `dig_store` (Knollen ausgraben, reinigen, beschriften, in Lagermaterial einpacken) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober nach erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | `replant` (Knollen vorkeimen lassen März, dann auspflanzen Mai) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 (Auspflanzen nach letztem Frost, Mitteleuropa Mitte Mai) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 4 (unter 0 °C erfrieren Knollen unwiderruflich) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 (über 15 °C vorzeitiger Austrieb, schwächt Knolle) | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | `dark` (Dunkel lagern; Licht triggert Austrieb) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | `none` (absolut kein Giessen; nur alle 4 Wochen Zustand prüfen) | `overwintering_profiles.winter_watering` |

**Lagermaterialien (geprüfte Praxis):**
- Perlite (lose, trocken): Beste Feuchtigkeitsregulation
- Vermiculit (leicht angefeuchtet): Hält Knollen vor Austrocknung
- Torfmoos: Traditionell, aber Fäulnisrisiko bei zu feuchter Einlagerung
- Styropor-Chips (trocken): Günstig, isoliert gut, aber keine Feuchtigkeitsregulation
- Zeitungspapier: Geeignet bei trockenen Kellern (unter 60 % rel. Luftfeuchtigkeit)

**Fäulnis-Prävention:** Knollen vor Einlagerung 24–48 Stunden trocknen lassen. Jegliche weichen oder faulen Stellen vor Einlagerung herausschneiden. Wunden mit Holzkohlepulver oder Schwefelstaub behandeln. Einzelne Knollen NICHT in luftundurchlässigen Plastikbeuteln lagern (Kondensation → Fäulnis).

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse (schwarz, grün) | Myzus persicae, Aphis fabae | Kolonien an Triebspitzen; klebrige Honigtau-Ablagerungen; Virustransmission | Triebspitze, Knospe, Blattunterseite | vegetativ, knospe | easy |
| Gemeiner Ohrwurm | Forficula auricularia | Zerfressene Blütenblätter und Blätter; unregelmässige Löcher an Blütenrand | Blüte, junges Laub | blüte | medium (nachtaktiv!) |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste Blattunterseite; gelbe Stippen; Blattvergilbung bei Massenbefall | Blattunterseite | vegetativ, knospe | medium |
| Thripse | Frankliniella occidentalis | Silbrige Streifen auf Blütenblättern; deformierte Blüten; Virustransmission | Blüte, junges Laub | knospe, blüte | difficult |
| Blattminierfliegen | Liriomyza spp. | Mäanderartige Fraßgänge in Blattspreite; Blatttod bei starkem Befall | Blatt | vegetativ | easy |

**Hinweis Ohrwurm:** Ohrwürmer sind tag/nachtaktiv und verstecken sich tagsüber in engen Spalten. Befallsdiagnose am besten früh morgens oder abends. Sie schädigen Blüten erheblich, kontrollieren aber gleichzeitig andere Schädlinge (Blattläuse, Wollläuse) — als Nützling-/Schädling-Balance behandeln, nicht pauschal bekämpfen.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weisses Mehlpuder auf Blattoberfläche; beginnt auf oberen Blättern | Trockene warme Tage + kühle feuchte Nächte; schlechte Luftzirkulation | 5–10 | vegetativ, knospe, blüte |
| Grauschimmel (Botrytis) | fungal (Botrytis cinerea) | Grau-brauner Flaum auf Blüten und Knospen; Knospenabsterben; feuchte Fäulnis | Hohe Luftfeuchte über 85 %; kühle Nächte; schlechte Luftzirkulation | 3–7 | blüte (Herbst!) |
| Pythium-Wurzelfäule | oomycete (Pythium ultimum) | Knollen und Wurzeln braun und weich; Pflanze welkt trotz Feuchte | Staunässe; zu frühes Pflanzen in kaltem Boden (< 12 °C) | 3–10 | vorkultur, vegetativ |
| Sclerotinia-Knollenfäule | fungal (Sclerotinia sclerotiorum) | Weisse baumwollartige Myzelien an Knollen; schwarze Sklerotien | Feuchtes kühles Lager; mechanische Verletzungen der Knolle | 5–14 | dormanz (Lagerung!) |
| Dahlia Mosaikvirus | viral (Dahlia mosaic virus, DMV) | Chlorotische Mosaik-Muster auf Blättern; Wachstumsdeformationen; Blattaufhellungen | Blattläuse (Vektoren); infiziertes Pflanzenmaterial | variabel | vegetativ, blüte |
| Verticillium-Welke | fungal (Verticillium dahliae) | Schlagartige einseitige Welke; braune Leitbündel im Querschnitt | Infizierter Boden; schlechte Fruchtfolge | 7–14 | vegetativ, knospe |

**Hinweis Mosaikvirus:** Kein Heilmittel. Infizierte Pflanzen sofort entfernen und vernichten (nicht kompostieren). Blattläuse konsequent bekämpfen (Virusvektor). Keine Stecklinge von infizierten Pflanzen nehmen.

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer (Larven + Adulte) | Blattläuse, Spinnmilben | 2–5 Adulte/m² | sofort aktiv |
| Florfliege (Chrysoperla carnea, Larven) | Blattläuse, Thripse, kleine Raupen | 5–10 Eier/m² | 7–14 |
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 10–25/m² | 14–21 |
| Orius insidiosus (Raubwanze) | Thripse | 1–3/m² | 14–21 |
| Schlupfwespen (Aphidius colemani) | Blattläuse | 5–10/m² | 7–14 |

**Nützlingshinweis Ohrwurm:** Forficula auricularia ist ein natürlicher Feind von Blattläusen und Schildläusen — nicht pauschal bekämpfen. Nur gezielt eingreifen wenn Blütenschäden inakzeptabel.

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Wasserstrahl | mechanical | — | Blattläuse mit starkem Wasserstrahl abspritzen | 0 | Blattläuse |
| Neemöl | biological | Azadirachtin | 0,5–1 % Sprühlösung, abends sprühen; alle 7–10 Tage | 3 | Blattläuse, Spinnmilben, Mehltau (präventiv), Thripse |
| Insektizide Seife / Kaliseife | biological | Kaliumsalze von Fettsäuren | 2 % Sprühlösung, Blattunterseite benetzen | 0 | Blattläuse, Spinnmilben, Thripse |
| Backpulver-Spray | cultural | Natriumbicarbonat | 5 g/L + paar Tropfen Öl, wöchentlich | 0 | Echter Mehltau (präventiv + kurativ) |
| Schwefelkalk-Brühe | chemical | Calcium-Polysulfid | Verdünnt sprühen; nur bei trockenem Wetter | 14 | Echter Mehltau, Spinnmilben |
| Kupfermittel (Cuprozin) | chemical | Kupferhydroxid | Nach Herstellerangabe; nicht bei Regen | 14 | Botrytis (präventiv), Grauschimmel |
| Ohrwurm-Fallen | mechanical | — | Umgekehrte Blumentöpfe mit feuchtem Stroh gefüllt; täglich ausleeren | 0 | Ohrwürmer (Freilandmethode) |
| Spinosad (Spritz) | biological | Spinosad | 0,025–0,05 % nach Herstellerangabe | 7 | Ohrwürmer, Thripse, Blattminierer |
| Abtrocknen / Luftzirkulation | cultural | — | Pflanzabstand einhalten; nicht abends gießen; Mulch | 0 | Botrytis, Mehltau |
| Mulchen (Stroh) | cultural | — | 5–8 cm Stroh um Basis | 0 | Bodenfeuchte, Spritzwasser, Pilzsporen |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine bekannten systemischen Resistenzen der Art | — | — |

**Hinweis:** 'Lavender Perfection' ist eine Zier-Hybride ohne dokumentierte Zucht-Resistenzen. Resistenzzüchtung bei Dahlien ist wenig entwickelt. Standortpflege, Fruchtfolge und biologische Kontrolle sind die Hauptprävention.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) — besonders P und K; N-Bedarf moderat |
| Fruchtfolge-Kategorie | Asteraceae (Korbblütler) |
| Empfohlene Vorfrucht | Hülsenfrüchte (Fabaceae: Bohnen, Erbsen, Lupinen) — N-Anreicherung im Boden; oder Gründüngung (Phacelia, Inkarnatklee) |
| Empfohlene Nachfrucht | Lauchgewächse (Alliaceae: Zwiebeln, Lauch, Knoblauch) — andere Familien, Schädlingsunterbrechung; oder Wurzelgemüse |
| Anbaupause (Jahre) | 3–4 Jahre (Verticillium und Sclerotinia können sich im Boden anreichern; Fruchtfolge unterbricht Erregerzyklus) |

**Fruchtfolge-Empfehlung für Dahlienbeet:**
- Jahr 1: Dahlie + Tagetes (Nematoden-Abwehr)
- Jahr 2: Hülsenfrüchte (Bohnen, Erbsen) — N-Aufbau
- Jahr 3: Gemüse aus anderer Familie (Brassica, Apiaceae)
- Jahr 4: Zwiebeln / Knoblauch — desinfizierend für Boden
- Dann wieder Dahlie (Jahr 5)

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes (Studentenblume) | Tagetes patula / T. erecta | 0.95 | Nematoden-Abwehr durch Wurzelexsudate; Aphid-Fallen-Pflanze; Bestäuber-Attraktor; klassische Dahlia-Begleitung | `compatible_with` |
| Calendula (Ringelblume) | Calendula officinalis | 0.85 | Blattlaus-Fallen-Pflanze; lockt Marienkäfer und Florfliegen an; optisch harmonisch mit Dahlien | `compatible_with` |
| Knoblauch | Allium sativum | 0.80 | Repellent gegen Blattläuse, Spinnmilben, Japankäfer; antimikrobiell gegen Bodenpilze; dezent einsetzen | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.75 | Thrips-Repellent; lockt Bestäuber an; Duft-Synergien; verträgliche Wasser-/Nährstoffansprüche | `compatible_with` |
| Kosmeen (Cosmea) | Cosmos bipinnatus | 0.85 | Bestäuber-Attraktor (besonders Hummeln, Schwebfliegen); gleiche Pflege-Anforderungen; klassische Gartenbegleitung | `compatible_with` |
| Sonnenblume | Helianthus annuus | 0.70 | Windschutz; lockt Bestäuber an; gleiche Familie (Asteraceae); Windschatten schützt Dahlienstiele; nicht zu dicht pflanzen | `compatible_with` |
| Artemisia / Beifuss | Artemisia absinthium | 0.70 | Schnecken-Repellent durch Duft; silbrige Laubstruktur als optischer Kontrast; kein Wasserwettbewerb | `compatible_with` |
| Koriander | Coriandrum sativum | 0.75 | Aphid-Repellent; lockt parasitische Wespen an; schnell und platzsparend | `compatible_with` |
| Sommerastern | Callistephus chinensis | 0.65 | Gleiche Wachstumsbedingungen; optisch ergänzend; aber: Aster-Welkekrankheit (Fusarium oxysporum f. sp. callistephi) im selben Beet beobachten | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Starke allelopathische Hemmung vieler Pflanzen durch Fenchen und andere Terpene; hemmt Keimung und Wachstum von Nachbarn | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Teilt Verticillium dahliae-Wirte — Kartoffel kann Verticillium-Inokulum im Boden aufbauen, das dann Dahlien befällt | severe | `incompatible_with` |
| Erdbeere | Fragaria x ananassa | Teilt Verticillium-Bodenanfälligkeit; Erdbeerpflanzen können Verticillium-Reservoir sein | moderate | `incompatible_with` |
| Andere Asteraceae-Massenbestände | Helianthus / Helenium / Rudbeckia (gross) | Gleiche Familie = geteilte Schädlinge und Krankheiten (Echter Mehltau, Verticillium); hohe Konkurrenz um Wasser und Nährstoffe bei Mischung | low | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Solanaceae (Nachtschattengewächse) | `shares_pest_risk` | Verticillium dahliae (beide anfällig) | `shares_pest_risk` |
| Rosaceae (Rosengewächse — Erdbeere) | `shares_pest_risk` | Verticillium dahliae, Botrytis cinerea | `shares_pest_risk` |
| Asteraceae (andere Korbblütler) | `shares_pest_risk` | Echter Mehltau (Erysiphe), Blattläuse, Thripse | `shares_pest_risk` |
| Fabaceae (Hülsenfrüchte) | `family_compatible_with` | N-Anreicherung, unterschiedliche Schädlinge | `family_compatible_with` |
| Alliaceae (Zwiebelgewächse) | `family_compatible_with` | Repellent-Wirkung gegen Bodenschädlinge und Pilze | `family_compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art / Sorte | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber 'Lavender Perfection' |
|-------------|-------------------|-------------|----------------------------------------|
| 'Mystery Day' (Dinner Plate) | Dahlia x hybrida 'Mystery Day' | Grosse dekorative Dahlie, ähnliche Grösse | Intensivere weinrote/lila Farbe; etwas robuster |
| 'Cafe au Lait' (Dekorativ) | Dahlia x hybrida 'Cafe au Lait' | Ähnliche Blütengrösse, pastelltöne | Extrem beliebte Hochzeitsblume; Cremeton; vielseitiger in Arrangements |
| 'Bishop of Llandaff' (Peonie) | Dahlia x hybrida 'Bishop of Llandaff' | Gleiche Familie, ähnliche Pflege | Rotes Laub als Zierelement; kleinere Blüten, aber kontrastreicher Auftritt; robuster |
| Garten-Dahlie (Ballendahlie) | Dahlia x hybrida (Kugeltyp) | Gleiche Art, anderer Blütentyp | Kompakter (60–90 cm), weniger Stützbedarf; runde Blüten kugelförmig |
| Pompon-Dahlie | Dahlia x hybrida (Pompon-Typ) | Gleiche Art, Miniaturblüten | Sehr kompakt; ideal für Beete und Balkon; kein Disbudding nötig |
| Cactus-Dahlie | Dahlia x hybrida (Kaktustyp) | Gleiche Art, gespitzte Blütenblätter | Windstabiler durch schmälere Blütenblätter; eleganter Habitus |
| Gartenstaude Echinacea | Echinacea purpurea | Gleiche Familie (Asteraceae); ähnliche Blütensaison | Winterhart (bis Zone 3), kein Ausgraben nötig; Bienenweide; perennial ohne Pflege |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,frost_sensitivity,nutrient_demand_level,green_manure_suitable,pruning_type,pruning_months,bloom_months,sowing_indoor_weeks_before_last_frost,direct_sow_months
Dahlia pinnata,'Dahlie;Garden Dahlia;Dinner Plate Dahlia',Asteraceae,Dahlia,perennial,short_day,herb,tuberous,'8a;8b;9a;9b;10a;10b',0.0,'Gartenherkunft; Heimat Elternarten Mexiko/Guatemala',limited,40,40,120,75,75,no,limited,false,true,tender,heavy_feeder,false,after_harvest,'10;11','7;8;9;10',4,'5'
```

### 8.2 Cultivar CSV-Zeile

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Lavender Perfection,Dahlia pinnata,unbekannt,unbekannt,'ornamental;dinnerplate;formal_decorative;cut_flower;heat_tolerant',90,keine dokumentierten,clone
```

**Hinweis Seed Type:** 'Lavender Perfection' wird als Knolle (vegetativ) vermehrt und weitergegeben. Samen würden nicht sortenecht sein (Hybride). Daher `clone` als `seed_type` — vegetative Vermehrung via Knollenteilung oder Stecklinge.

---

## Quellenverzeichnis

1. [American Dahlia Society — Nutrients for Dahlias](https://www.dahlia.org/docsinfo/articles/nutrients-for-dahlias/) — NPK-Empfehlungen, Phosphor- und Kalium-Bedeutung
2. [American Dahlia Society — Digging, Dividing and Storing Tubers](https://www.dahlia.org/docsinfo/articles/digging-dividing-and-storing-tubers/) — Knollenpflege, Lagerung
3. [UC IPM — Managing Pests in Gardens: Dahlia](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/dahlia.html) — IPM-Schädlings- und Krankheitsmanagement
4. [Longfield Gardens — How to Overwinter Dahlias](https://www.longfield-gardens.com/article/how-to-overwinter-dahlias) — Lagerung, Härtezone, Temperaturen
5. [Longfield Gardens — Dahlia 'Lavender Perfection' (Produktseite)](https://www.longfield-gardens.com/plantname/Dahlia-Lavender-Perfection) — Sortendaten, Wuchshöhe, Blütezeit
6. [ASPCA Toxic and Non-Toxic Plants: Dahlia](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dahlia) — Toxizitätsangaben Tiere
7. [Swan Island Dahlias — Dahlia Fertilizing Tips](https://www.dahlias.com/blog/growing-tips/dahlia-fertilizing-tips/) — Düngungsplan, Produkt-Empfehlungen
8. [Swan Island Dahlias — Dahlia Pest & Disease Management](https://www.dahlias.com/blog/troubleshooting/dahlia-pest-disease-management/) — Schädlinge und Krankheiten
9. [Holland Bulb Farms — Lavender Perfection Dinnerplate Dahlia](https://www.hollandbulbfarms.com/spring-planting-bulbs/dahlias/dinnerplate-dahlias/lavender-perfection-dinnerplate-dahlia) — Sortendaten: Tage bis Reife, Blütengrösse, Höhe
10. [Floret Flower Farm Library — Dahlia Lavender Perfection](https://library.floretflowers.com/products/dahlia-lavender-perfection) — Schnittblumen-Eigenschaften, Blütenbeschreibung
11. [Gardeners Path — How to Identify and Control Dahlia Pests](https://gardenerspath.com/plants/flowers/control-dahlia-pests/) — Schädlings-Identifikation, biologische Kontrolle
12. [Epic Gardening — 17 Best Dahlia Companion Plants](https://www.epicgardening.com/dahlia-companion-plants/) — Mischkultur-Empfehlungen
13. [Brecks — Lifting & Storing Dahlias Winter](https://www.brecks.com/blogs/blog-post/lifting-storing-dahlias-winter) — Zonen 3–7 Winterschutz, Lagertemperaturen
14. [Gardening Know How — How to Fertilize Dahlias](https://www.gardeningknowhow.com/ornamental/bulbs/dahlia/how-to-fertilize-dahlias.htm) — NPK-Ratios, Düngeintervalle
15. [Missouri Botanical Garden — Dahlia Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a445) — Taxonomie, USDA-Zonen, Kulturbeschreibung
