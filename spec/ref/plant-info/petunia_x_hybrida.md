# Garten-Petunie — Petunia × hybrida

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-04
> **Quellen:** Wikipedia (DE/EN), ASPCA, NC State Extension, Missouri Botanical Garden, UC IPM, Iowa State Extension, Gardening Know How, Epic Gardening, Proven Winners, MDPI Horticulturae

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Petunia × hybrida | `species.scientific_name` |
| Volksnamen (DE/EN) | Garten-Petunie; Garden Petunia | `species.common_names` |
| Familie | Solanaceae | `species.family` → `botanical_families.name` |
| Gattung | Petunia | `species.genus` |
| Ordnung | Solanales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual (in Mitteleuropa); perennial in USDA 9–11 | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral (die meisten Sorten; einige Sorten reagieren schwach langtagig) | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–11b (als Staude); 2a–9b (als einjährige Kultur) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Keine Frosttoleranz — Pflanze stirbt ab 0°C. Überwinterung nur frostfrei (mind. +5°C) als Stecklingspflanze oder in hellem Kalthaus möglich. In Mitteleuropa (USDA Zone 7–8) als einjährige Beetpflanze kultivieren. | `species.hardiness_detail` |
| Heimat | Südamerika (Elternarten P. axillaris und P. integrifolia aus Argentinien/Uruguay) | `species.native_habitat` |
| Allelopathie-Score | 0.0 (neutral — keine belegte allelopathische Wirkung) | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, bee_friendly | `species.traits` |

**Hinweis zur Taxonomie:** Petunia × hybrida entstand im 19. Jahrhundert in England aus Kreuzungen der Arten P. axillaris (weißblühend) und P. integrifolia (rotviolett blühend). Die Bezeichnung `×` kennzeichnet den Hybridursprung. Viele moderne Marktgruppen (Wave, Surfinia, Supertunia) sind vegetativ vermehrte oder F1-Saatgutsorten desselben Hybridkomplexes.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | Nicht empfohlen (Keimlinge zu filigran, Saison zu kurz) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — (nur Voranzucht sinnvoll) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze, keine Ernte) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 | `species.bloom_months` |

**Zeitplan für Mitteleuropa:**
- **Januar/Februar:** Voranzucht starten (Lichtkeimer! Samen nicht bedecken)
- **März:** Pikieren der Keimlinge in Einzeltöpfe
- **April:** Abhärten (Hardening-off) ab Mitte April; kein Frost mehr tolerierbar
- **Ab Mitte Mai** (nach Eisheiligen): Auspflanzen ins Freiland/auf den Balkon
- **Oktober/November:** Pflanze stirbt nach erstem Frost ab

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweise zur Vermehrung:**
- **Samenvermehrung:** Petuniensamen sind sehr fein (Staubsamen). Keimtemperatur 21–24°C, Keimung nach 7–14 Tagen. Licht ist für die Keimung notwendig — Samen nur andrücken, nicht abdecken. F1-Hybriden sind nicht sortenecht nachzuziehen.
- **Stecklingsvermehrung:** Für vegetativ vermehrte Sorten (Surfinia, Supertunia) Triebspitzenstecklinge 7–10 cm Länge, wurzeln bei 18–22°C in 14–21 Tagen. Patentschutz beachten — kommerzielle Vermehrung dieser Sorten ist ohne Lizenz unzulässig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannten toxischen Verbindungen | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Quellen:** ASPCA (American Society for the Prevention of Cruelty to Animals) listet Petunia × hybrida ausdrücklich als ungiftig für Katzen, Hunde und Pferde. Massive Aufnahme von Pflanzenmaterial kann bei Tieren und Kindern milde Verdauungsbeschwerden verursachen (mechanisch, nicht toxisch). Die klebrigen Trichome der Blätter können bei sensitiven Personen leichte Hautreizungen verursachen (mechanisch).

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8 | `species.pruning_months` |

**Rückschnitt-Praxis:** Einfachblühende Sorten regelmäßig ausgeizen (verblühte Blüten entfernen). Mitte Sommer (Juli) radikaler Rückschnitt um ca. ein Drittel der Triebe fördert kräftigen Neuaustrieb und zweite Blüteperiode. Großblumige Grandiflora-Typen deadheaden; Multiflora- und Wave-Typen sind weitgehend selbstreinigend.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 (je nach Sortengröße; hängende Sorten: 10–20 L Ampel) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 (aufrecht); 10–30 (hängend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 (Buschwuchs bis 150 cm bei Wave-Typen) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–40 | `species.spacing_cm` |
| Indoor-Anbau | limited (nur Überwinterung von Stecklingen; volle Blüte braucht Volllsonne outdoor) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (nur für Voranzucht und Überwinterung) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Balkon- und Kübelpflanzenerde mit guter Drainage; pH 5,5–6,2; Perlite-Zusatz 10–20% für verbesserte Drainage empfohlen; Langzeitdünger beim Einpflanzen untermischen | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Entsorgung erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|-------------------|----------------|
| Keimung (germination) | 7–14 | 1 | false | false | false | low |
| Sämling (seedling) | 21–35 | 2 | false | false | false | low |
| Vegetatives Wachstum (vegetative) | 14–21 | 3 | false | false | false | medium |
| Abhärtung (hardening_off) | 7–14 | 4 | false | false | false | low |
| Blüte (flowering) | 120–180 | 5 | false | false | false | medium |
| Seneszenz (senescence) | 14–21 | 6 | true | false | true | high |

**Hinweis:** Da Petunia × hybrida eine annuelle Zierpflanze ist, ist `allows_harvest: false` auf allen Phasen gesetzt. Die `hardening_off`-Phase ist obligatorisch nach Indoor-Voranzucht vor dem Auspflanzen ins Freiland (REQ-003 AB-009). Die Blütephase ist die ökologisch und ästhetisch bedeutsamste Phase und dauert bei guter Pflege von Mai bis Oktober.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung (germination)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 (Licht obligatorisch für Keimung — Lichtkeimer!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 80–95 (Keimschale abgedeckt halten) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 80–95 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (ambient) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Substrat gleichmäßig feucht — nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 5–20 (Sprühflasche, keine Überschwemmung) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling (seedling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Pikier-Übergang:** Nach Entwicklung des ersten Laubblatts (ca. 14–21 Tage nach Keimung) pikieren in Einzeltöpfe 7–9 cm. Nach dem Pikieren 3–5 Tage erhöhte Luftfeuchtigkeit (70–80%) und gedämpftes Licht (~100 µmol/m²/s) zur Erholung.

#### Phase: Vegetatives Wachstum (vegetative)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 16–18 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Abhärtung / Hardening-off

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (schrittweise ans Sonnenlicht gewöhnen) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 (stufenweise steigern) | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natürlicher Tageslichtrhythmus (12–14 im April/Mai) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–22 (Außentemperatur) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 (kein Frost!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 (Außenluft) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (ambient outdoor) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Wind trocknet Substrate schneller aus) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Praxis-Hinweis:** Pflanzen täglich für 1–2 Stunden nach draußen stellen, Expositionszeit über 7–14 Tage schrittweise steigern. Direkte Mittagssonne zunächst vermeiden. Nachts (Temperaturen < 10°C) wieder reinholen.

#### Phase: Blüte (flowering)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–1500 (Volllsonne, min. 6 Stunden täglich) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | natürlicher Tageslichtrhythmus (14–16 im Sommer) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–30 (optimal 22–28°C) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 (hohe Luftfeuchtigkeit > 80% Botrytis-Risiko) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–1.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 (ambient outdoor) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1 (Ampeln) bis 2 (Beete); bei Hitze täglich | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 (Ampeln deutlich mehr) | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Kritische Pflegehinweise in der Blüte:**
- Petunien in Ampeln und Kübeln haben durch beschränktes Substratvolumen einen sehr hohen Wasserbedarf. An heißen Sommertagen (>28°C) täglich gießen, ggf. morgens und abends.
- Regelmäßige Flüssigdüngung alle 7–14 Tage ist essenziell — Nährstoffe werden durch häufiges Gießen ausgewaschen.
- Eisenmangel (Chlorose) ist eine der häufigsten Mangelerscheinungen bei Petunien — gelbe Blätter bei grünen Blattadern.

#### Phase: Seneszenz (senescence)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | nicht relevant (Pflanze stirbt ab) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | — | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | < 10 (Frühfrost löst Seneszenz aus) | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | < 5 | `requirement_profiles.temperature_night_c` |
| Gießintervall (Tage) | 7 (minimieren) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Fe (ppm) | Hinweis |
|-------|----------------|---------|-----|----------|----------|---------|---------|
| Keimung | 0:0:0 | 0.0–0.3 | 5.5–5.8 | — | — | — | Nur klares Wasser, keine Düngung |
| Sämling | 1:1:1 | 0.4–0.8 | 5.5–5.8 | 60–80 | 25–40 | 1–2 | Schwache Anfangsdüngung (50 ppm N) |
| Vegetativ | 2:1:2 | 0.8–1.4 | 5.5–6.0 | 100–140 | 40–60 | 2–3 | Ausgewogene Vollversorgung, Kalzium-Betonung |
| Blüte | 1:2:3 | 1.2–2.0 | 5.5–6.2 | 120–160 | 50–70 | 2–4 | Kaliumbetonung für Blütenansatz und Farbe; Eisenversorgung kritisch |
| Seneszenz | 0:0:0 | 0.0 | — | — | — | — | Keine Düngung |

**Besonderer Hinweis Eisenbedarf:** Petunia × hybrida gehört zu den eisenbedürftigsten Balkonpflanzen. Bei pH > 6,5 wird Eisen in der Bodenmatrix unlöslich — Chlorose (Gelbfärbung jüngerer Blätter bei grünen Blattadern) als Folge. Substrat-pH unter 6,2 halten und bei erstem Chlorose-Symptom mit Eisenchelat-Dünger (Fe-EDTA oder Fe-HEEDTA) behandeln.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Zeitraum/Tage | Bedingungen |
|------------|---------|--------------|-------------|
| Keimung → Sämling | time_based | 7–14 Tage | Keimblätter vollständig entfaltet; Hypokotyl aufgerichtet |
| Sämling → Vegetativ | manual | 21–35 Tage | Erstes Laubblattpaar sichtbar; Pikieren durchgeführt |
| Vegetativ → Abhärtung | event_based | 14–21 Tage | Eisheiligen vorbei (Mitte Mai); Außentemperatur > 8°C nachts |
| Abhärtung → Blüte | time_based | 7–14 Tage | Erste Blütenknospen sichtbar; Auspflanzung abgeschlossen |
| Blüte → Seneszenz | event_based | Saisonende | Erster Frost (<0°C); Pflanze zeigt ausgedehnte Frostschäden |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch / Wasserlöslich (Kübel, Balkon, Hydroponik)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Flüssigdünger Balkon & Kübel | COMPO | base | 5-3-8 (+Fe) | 20 ml/3 L alle 7 Tage | 3 | Blüte |
| Wuxal Blühpflanzen | Hauert | base | 6-6-8 (+Spurenelm.) | 10 ml/1 L alle 7–14 Tage | 3 | Vegetativ, Blüte |
| Peters Professional 20-20-20 | ICL / Peters | base | 20-20-20 | 1 g/L | 3 | Vegetativ |
| Peters Professional 15-5-15 | ICL / Peters | base | 15-5-15 | 1–1.5 g/L | 3 | Blüte (Ca-betont) |
| Osmocote Exact 14-14-14 | ICL Osmocote | slow-release | 14-14-14 | 3–5 g/L Substrat | 1 (Pflanzung) | Gesamtsaison |
| Floranid Blumen | Compo | slow-release | 12-8-16 (+2MgO) | 6 g/L Substrat | 1 (Pflanzung) | Gesamtsaison |
| Eisen-Chelat Fe-EDTA | verschiedene | supplement | — | 0.5–1 g/10 L | 2 | bei Chlorose |

#### Organisch (Beet, Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch | 80–120 g/m² | Frühjahr vor Pflanzung | Stickstoffversorgung |
| Kali-Magnesia (Patentkali) | K+S Kali | mineralisch-organisch | 20–30 g/m² | Frühjahr/Sommer | Kalium-Boost Blütephase |
| Blumenerde Kompost-Gemisch | eigene Mischung | organisch | 3–5 L/m² | Herbst/Frühjahr | Bodenverbesserung |
| Hornmehl | Oscorna | organisch | 50–70 g/m² | Frühjahr | Schnellere N-Freisetzung als Hornspäne |

### 3.2 Düngungsplan (Kübel/Balkon, Flüssigdüngung)

| Zeitraum | Phase | EC (mS) | pH | Flüssigdünger (ml/L) | Häufigkeit | Hinweise |
|----------|-------|---------|-----|---------------------|------------|----------|
| Wochen 1–2 nach Auspflanzung | Eingewöhnung | — | — | 0 (nur Langzeitdünger aktiv) | — | Pflanze erholen lassen |
| Wochen 3–6 | Vegetativ/Knospen | 0.8–1.4 | 5.8 | 10–15 (ausgewogener Dünger) | alle 14 Tage | EC steigern |
| Juli–September (Hochblüte) | Blüte | 1.4–2.0 | 5.8–6.2 | 20 (kaliumbetonter Blütedünger) | alle 7 Tage | Eisenchelat bei Chlorose |
| Juli Mitte (Rückschnitt) | Regeneration | 0.8 | 5.8 | 10 | einmalig danach | Fördert Neutrieb |
| August–Oktober | Blüte/Ausklingen | 1.0–1.6 | 6.0 | 15 | alle 10–14 Tage | Ab Oktober einstellen |

### 3.3 Mischungsreihenfolge (für Flüssigdünger-Mischungen)

> **Kritisch bei Multi-Komponenten-Mischungen:** Die Reihenfolge verhindert Ausfällungen.

1. Klares Wasser (Zimmertemperatur, ca. 18–22°C)
2. Eisen-Chelat (Fe-EDTA) falls zugesetzt — reagiert am empfindlichsten auf pH-Schwankungen
3. CalMag-Supplement (falls Osmosewasser oder sehr weiches Leitungswasser verwendet wird)
4. Hauptdünger A (Stickstoff/Kalzium-betonte Komponente)
5. Hauptdünger B (Phosphor/Kalium-Komponente)
6. pH-Korrektür mit pH-Down (Zitronensäure oder Phosphorsäure) — IMMER als letztes

**Praxis-Hinweis Balkon:** Bei Einkomponenten-Flüssigdüngern (Wuxal, COMPO) entfällt die Mischungsreihenfolge. Dünger ins Gießwasser einrühren, dann pH prüfen und ggf. korrigieren.

### 3.4 Besondere Hinweise zur Düngung

**Eisenbedarf:** Petunien gehören zur Gruppe der eisenbedürftigen Balkonpflanzen (zusammen mit Calibrachoa, Pelargonien). Blattdüngung mit Fe-EDTA (Eisenchelat) bei ersten Chlorose-Zeichen; Chelatform sichert Bioverfügbarkeit auch bei pH 5.5–6.5. Substrat-pH dauerhaft unter 6.2 halten.

**Stickstoff-Balance:** Zu viel Stickstoff (> 200 ppm N) fördert üppiges Blattwachstum auf Kosten der Blüte. In der Blütephase auf kaliumbetonten Dünger (K > N) wechseln.

**Containerkultur:** Durch tägliches Gießen werden Nährstoffe aus dem begrenzten Substratvolumen ausgewaschen. Wöchentliche Düngung in der Hochsaison (Juli–August) ist daher keine Überdüngung, sondern notwendiger Ersatz.

**Bodenanalyse-Empfehlung Freiland:** Für Beetpflanzung ist der Boden-pH der wichtigste Parameter — bei pH > 6.5 Eisenmangel und Bor-Mangel vorprogrammiert. Boden vor Saisonstart mit Schwefel oder Torf ansäuern falls nötig.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | `custom` (kein vorhandenes Preset passt exakt; nächste Option: `herb_tropical` als Annäherung) | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 1–2 (Kübel/Ampeln täglich; Beete alle 2 Tage) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | nicht relevant (als Einjährige keine Überwinterung im Regelfall) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | `top_water` (von oben gießen, Blüten wenn möglich nicht benetzen) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | "Kalkreiches Wasser (> 14°dH) erhöht den pH-Wert des Substrats — regelmäßiger pH-Check empfohlen. Weiches Wasser oder leicht angesäuertes Wasser bevorzugt." | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7 (Hochsaison); 14 (Früh-/Spätsaison) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig, nicht relevant) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false (Außenpflanze) | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Saatgut bestellen | F1-Sorten bestellen; Substrat und Pflegemittel besorgen | niedrig |
| Jan | Stecklinge überwinternder Pflanzen kontrollieren | Überwinterte Stecklinge auf Schädlinge und Fäulnis kontrollieren | mittel |
| Feb | Voranzucht starten | Aussaat in Keimschalen; Wärme 22–24°C; Licht obligatorisch; Staubsamen nur andrücken | hoch |
| Mär | Pikieren | Nach Entwicklung 1. Laubblatt in 7-cm-Töpfe pikieren | hoch |
| Apr | Kulturkontrolle & Umtopfen | In größere Töpfe/Balkonkästen umtopfen; Substrat + Langzeitdünger vorbereiten | mittel |
| Apr/Mai | Abhärten (Hardening-off) | Schrittweise ans Freiluftklima gewöhnen; Frost-Frühwarnung beachten | hoch |
| Mai (nach Eisheiligen) | Auspflanzen | Nach Mitte Mai (letzter Frost Mitteleuropa) auspflanzen; Pflanzabstand 25–40 cm | hoch |
| Mai–Jun | Startdüngung | Erste Flüssigdüngung; pH-Wert des Substrats prüfen | mittel |
| Jun–Sep | Regelmäßiges Gießen | Täglich bei Hitze; Gießen möglichst morgens; Blüten nicht benetzen | hoch |
| Jun–Sep | Wöchentlich düngen | Blütedünger (kaliumbetont); Eisenchelat bei Chlorose-Anzeichen | hoch |
| Jul | Ausgeizen / Rückschnitt | Verblühtes regelmäßig entfernen; Mitte Juli radikaler Rückschnitt um 1/3 für Neubetrieb | mittel |
| Jul–Sep | Schädlingskontrolle | Wöchentlich auf Blattläuse, Thripse, Weiße Fliege kontrollieren | mittel |
| Sep/Okt | Saisonabschluss | Pflanzen sterben bei erstem Frost; Behälter reinigen und einlagern | niedrig |
| Okt (optional) | Stecklinge abnehmen | Für Überwinterung: 10 cm Triebspitzenstecklinge schneiden, bewurzeln | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors (nur bei Wunsch zur Überwinterung, sonst Entsorgung nach Frost) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor erstem Frost; Stecklinge abnehmen) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off, move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright (mindestens 6–8 Stunden indirektes Licht; Kunstlicht empfohlen) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal (alle 14 Tage sparsam gießen; kein Dünger) | `overwintering_profiles.winter_watering` |

**Praxis-Hinweis Überwinterung:** Die meisten Gärtner in Mitteleuropa kultivieren Petunien als Einjährige und entsorgen sie nach dem Frost. Überwinterung lohnt sich hauptsächlich für patentgeschützte vegetative Sorten (Surfinia, Supertunia), da deren Saatgut nicht erhältlich ist. Methode: Triebspitzenstecklinge 10 cm im September abnehmen, in Anzuchterde bewurzeln (18–20°C), dann in ein helles, kühles (5–10°C) Winterquartier (Kalthaus, helles Treppenhaus) bringen.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Grüne Pfirsichblattlaus | Myzus persicae | Klebrige Honigtau-Absonderungen; verformte Triebspitzen; Rußtaubefall; Kolonien an Blattunterseiten und Triebspitzen | leaf, stem | seedling, vegetative, flowering | easy |
| Schwarze Bohnenblattlaus | Aphis fabae | Schwarze Kolonien an Triebspitzen und Blattunterseiten; Triebverformung; Honigtau | leaf, stem | vegetative, flowering | easy |
| Weiße Fliege | Trialeurodes vaporariorum | Weiße 2–3 mm Fluginsekten; Honigtau; Rußtau; gelbliche Blattflecken | leaf | vegetative, flowering | medium |
| Thripse (Blasenfüße) | Frankliniella occidentalis | Silbrig-graue Streifen und Flecken auf Blättern und Blüten; verformte Blütenblätter; winzige schwarze Kotpunkte | leaf, flower | flowering | difficult |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste an Blattunterseiten; bronzefarbene Punktierung; bei Trockenheit und Hitze | leaf | flowering | difficult |
| Blattminierfliege | Liriomyza trifolii | Helle Minen (Gänge) im Blattgewebe sichtbar | leaf | vegetative, flowering | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel / Botrytis | fungal | Braun-grauer Schimmelbelag auf Blüten, Blättern und Stängeln; Fäulnis bei feuchter Witterung | Hohe Luftfeuchtigkeit > 85%, Temperaturen 15–25°C, stehende Luft, verletztes Gewebe | 2–5 | flowering, senescence |
| Echter Mehltau | fungal | Weißes mehliges Pulverbelag auf Blattoberseite; befallene Blätter vergilben und fallen ab | Warme Tage + kühle Nächte; wechselhafte Witterung; trockene Blätter | 5–10 | flowering |
| Pythium-Wurzelfäule | oomycete (fungal-like) | Welkesymptome trotz feuchtem Substrat; dunkle verfaulte Wurzeln; Absterben von Jungpflanzen | Überwässerung, schlechte Drainage, niedrige Temperaturen, verdichtetes Substrat | 3–7 | seedling, vegetative |
| Fusarium-Welke | fungal | Einseitiges Welken; braune Verfärbung des Leitgewebes im Querschnitt; Absterben der Pflanze | Infiziertes Substrat; hohe Bodentemperaturen; Stresssituationen | 7–21 | vegetative, flowering |
| Petunia Vein Clearing Virus (PVCV) | viral | Blattadern werden auffallend hell/durchsichtig; Mosaikmuster; Wuchshemmung | Übertragung durch Blattläuse; befallenes Pflanzgut | 14–28 | alle |
| Phytophthora-Stängelfäule | oomycete | Stängelabschnürung an der Bodenbasis; Schwarzfärbung; Pflanze kippt um | Nasse Böden; Spritzwasser; schlechte Drainage | 3–10 | seedling, vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Marienkäfer (Coccinella septempunctata) | Blattläuse | 2–5 Adulte/m² | 7–14 |
| Chrysoperla carnea (Florfliege, Larven) | Blattläuse, Thripse, Weiße Fliege | 5–10 Larven/m² | 7–14 |
| Aphidius colemani (Brackwespe) | Grüne Pfirsichblattlaus | 5–10/m² | 14–21 |
| Encarsia formosa (Schlupfwespe) | Weiße Fliege | 3–5 Puparienkärtchen/m² | 21–28 |
| Amblyseius cucumeris (Raubmilbe) | Thripse | 50–100/m² | 14–21 |
| Schwebfliegen (div. Syrphidae) | Blattläuse | Ansiedlung durch Blühpflanzen in der Nähe | variabel |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl (kaltgepresst) | biological | Azadirachtin | Sprühen 1–2%, 7-Tage-Intervall | 3 | Blattläuse, Weiße Fliege, Thripse |
| Kaliseife (Schmierseifenlösung) | biological | Kaliumoleat | Sprühen 2%, direkt auf Schädlinge | 1 | Blattläuse, Weiße Fliege |
| Pyrethrum | biological | Pyrethrine | Sprühen nach Anleitung; abends (Bienenschutz!) | 3 | Blattläuse, Thripse, Weiße Fliege |
| Kupferpräparat (Cueva) | chemical | Kupferoktanoat | Sprühen 0.3%, 7-Tage-Intervall | 7 | Pilzkrankheiten (Botrytis, Mehltau) |
| Schwefel-Spritzpulver | chemical | Schwefel | Stäuben/Spritzen bei trockenem Wetter | 14 | Echter Mehltau |
| Gießmittel Propamocarb | chemical | Propamocarb-HCl | Gießbehandlung nach Herstellervorgabe | 14 | Pythium, Phytophthora |
| Gelbtafeln / Gelbfallen | mechanical | — | Aufhängen in Pflanzennähe (1 Tafel/m²) | 0 | Weiße Fliege, Blattminierfliege |
| Abspritzen mit Wasserstrahl | cultural | — | Kräftiger Wasserstrahl auf Blattunterseiten | 0 | Blattläuse, Spinnmilben |
| Mulchen | cultural | — | 3–5 cm Mulchschicht | 0 | Spritzwasser-Pilzinfektionen |
| Krankes Pflanzenmaterial entfernen | cultural | — | Sofort entfernen und im Hausmüll entsorgen | 0 | Botrytis, Viren |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine bekannten artspezifischen Resistenzen; einige F1-Sorten züchterisch gegen Botrytis verstärkt | Krankheit | `resistant_to` |

**Hinweis Sortenresistenz:** Moderne F1-Sorten (z.B. Supertunia Vista, Success!-Serien von Benary) zeigen durch Züchtung verbesserte Toleranz gegenüber Hitze, Botrytis und rauen Witterungsbedingungen. Diese Information ist auf Cultivar-Ebene, nicht auf Artebene zu vermerken.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Starkzehrer (heavy_feeder) |
| Fruchtfolge-Kategorie | Nachtschattengewächse (Solanaceae) |
| Empfohlene Vorfrucht | Nicht relevant (einjährige Zierpflanze; klassische Fruchtfolge nur für Gemüsebeete) |
| Empfohlene Nachfrucht | Nicht relevant (einjährig; Beet wird neu bepflanzt) |
| Anbaupause (Jahre) | 2–3 Jahre am gleichen Standort empfohlen (Pythium, Fusarium im Boden) |

**Praxis-Hinweis Bodenruhe:** Bei Wiederholung an gleichem Standort über mehrere Jahre können sich bodenbürtige Erreger anreichern (Pythium, Fusarium). Substrat in Kübeln und Balkonkästen jährlich erneuern. Bei Beetanbau Standort rotieren oder Substrat mit Trichoderma-Präparaten behandeln.

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes (Studentenblume) | Tagetes patula | 0.9 | Nematoden-Abwehr im Boden; Weißfliegen-Ablenkung; Bestäuberförderung; ähnliche Licht- und Wasseransprüche | `compatible_with` |
| Pelargonie | Pelargonium × hortorum | 0.8 | Kombinierter Balkonkasten möglich; ähnliche Pflegeansprüche; ergänzendes Farbspektrum | `compatible_with` |
| Löwenmäulchen | Antirrhinum majus | 0.8 | Kein Konkurrenzdruck; Bestäubervielfalt; ergänzend im Beet | `compatible_with` |
| Ziertabak | Nicotiana alata | 0.7 | Thripsablenkung (Fanggärtner-Effekt); ähnliche Kulturansprüche; lockerer Wuchs überschattet Petunien nicht | `compatible_with` |
| Basilikum | Ocimum basilicum | 0.7 | Duft wirkt auf Blattläuse und Thripse abschreckend; kein Konkurrenzdruck | `compatible_with` |
| Tomate (im Gemüsebeet) | Solanum lycopersicum | 0.5 | Bestäubungsförderung durch Petunia-Blüten (nachgewiesen); ABER: geteilte Solanaceae-Schädlinge (Thripse, Myzus persicae, Pythium); geteiltes TSWV-Übertragungsrisiko; nur empfehlen mit gutem IPM-Management | `compatible_with` |
| Spargel | Asparagus officinalis | 0.7 | Petunien sollen Blattläuse vom Spargel fernhalten; Bestäuberförderung | `compatible_with` |
| Heliotrop | Heliotropium arborescens | 0.8 | Ähnliche Pflegeansprüche; duftergänzend; kombinierter Kübel möglich | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Blattlaus-Fangpflanze (trap crop); schützt Petunien durch Ablenkung; Bestäuberförderung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung durch Fenchel-Wurzelexsudate bekannt — hemmt Wachstum vieler Pflanzen | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Gleiche Familie (Solanaceae); teilt Phytophthora-Erreger; gegenseitige Krankheitsübertragung | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Solanaceae (Tomate, Kartoffel, Paprika, Aubergine) | `shares_pest_risk` | Tabakraupen (Manduca sexta), Blattläuse (Myzus persicae), Pythium, Fusarium, Viren (PVCV, TMV mögl. Kreuzreaktion) | `shares_pest_risk` |
| Solanaceae | `rotation_conflict` | Gleiches bodenbürtiges Erregerspektrum — Fruchtwechsel mit anderen Familien empfohlen | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Petunia × hybrida |
|-----|-------------------|-------------|-------------------------------------|
| Calibrachoa / Million Bells | Calibrachoa × hybrida | Sehr ähnliche Wuchsform und Blütenfarben; gleiche Familie (Solanaceae) | Kleinere Blüten; robuster bei Regen; weniger anfällig für Botrytis; keine Ausleizarbeiten; selbstreinigend |
| Stiefmütterchen | Viola × wittrockiana | Ähnliche Balkon-Verwendung; kühlere Saison | Frühjahrs- und Herbstblüher; frosttoleranter; gut für Vor- und Nachsaison |
| Pelargonie | Pelargonium × hortorum | Balkonpflanze; ähnliche Einsatzmöglichkeiten | Wassersparender; besser Überwinterbar; keine Eisenmangel-Problematik |
| Lobelia | Lobelia erinus | Überhängend; ähnlicher Einsatz in Ampeln | Blütenreicher bei Halbschatten; geringerer Wasserbedarf; kleinwüchsiger |
| Ziertabak | Nicotiana × hybrida | Gleiche Familie; ähnliche Kulturansprüche | Duftend; toleranter gegenüber Halbschatten; Hummelfutterpflanze |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,frost_sensitivity,hardiness_detail,allelopathy_score,native_habitat,nutrient_demand_level,green_manure_suitable,bloom_months,sowing_indoor_weeks_before_last_frost,pruning_type,pruning_months,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,propagation_methods,propagation_difficulty,toxicity_cats,toxicity_dogs,toxicity_children,toxicity_severity,traits
Petunia × hybrida,"Garten-Petunie;Garden Petunia",Solanaceae,Petunia,annual,day_neutral,herb,fibrous,"10a;10b;11a;11b",tender,"Keine Frosttoleranz. Stirbt ab 0°C. Überwinterung nur frostfrei (+5°C) möglich. In Mitteleuropa (USDA 7–8) als einjährige Beetpflanze kultivieren.",0.0,"Südamerika (P. axillaris und P. integrifolia aus Argentinien/Uruguay)",heavy_feeder,false,"5;6;7;8;9;10",10,summer_pruning,"6;7;8",yes,"5–20",20,"20–40","30–90","25–40",limited,yes,false,false,"seed;cutting_stem",moderate,false,false,false,none,"ornamental;bee_friendly"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Wave Purple,Petunia × hybrida,PanAmerican Seed,1995,"trailing;self_cleaning;heat_tolerant",75,–,f1_hybrid
Supertunia Vista Silverberry,Petunia × hybrida,Proven Winners,2015,"trailing;self_cleaning;heat_tolerant;botrytis_tolerant",80,botrytis_tolerant,clone
Surfinia Hot Pink,Petunia × hybrida,Suntory Flowers,1991,"trailing;vegetative;vigorous",70,–,clone
Easy Wave White,Petunia × hybrida,PanAmerican Seed,2000,"spreading;self_cleaning;compact",75,–,f1_hybrid
SUCCESS! 360 Deep Rose,Petunia × hybrida,Benary,2018,"trailing;rain_tolerant;vigorous",80,rain_tolerant,f1_hybrid
```

---

## Quellenverzeichnis

1. [Garten-Petunie – Wikipedia (DE)](https://de.wikipedia.org/wiki/Garten-Petunie) — Taxonomie, Systematik, Herkunft
2. [Petunien – Wikipedia (DE)](https://de.m.wikipedia.org/wiki/Petunien) — Gattungsübersicht, Botanik
3. [Petunia – Wikipedia (EN)](https://en.wikipedia.org/wiki/Petunia) — Erweiterte Taxonomie, Kultivierungsgeschichte
4. [Petunia x hybrida — NC State Extension Gardener Plant Toolbox](https://plants.ces.ncsu.edu/plants/petunia-x-hybrida/) — Anbaudaten, Klimaanforderungen, USDA-Zonen
5. [Petunia — Missouri Botanical Garden Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a601) — Kulturinformationen, Pflanzeeigenschaften
6. [ASPCA — Toxic and Non-toxic Plants: Petunia](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/petunia) — Toxizitätsangaben Katzen/Hunde
7. [UC IPM — Petunia Pest Management](https://ipm.ucanr.edu/PMG/GARDEN/FLOWERS/petunia.html) — IPM-Schädlinge und Krankheiten
8. [Iowa State Extension — How to Start Petunias from Seed Indoors](https://yardandgarden.extension.iastate.edu/how-to/how-start-petunias-seed-indoors) — Anzucht, Keimung, Keimtemperatur
9. [Epic Gardening — Petunia Companion Plants](https://www.epicgardening.com/petunia-companion-plants/) — Mischkultur-Empfehlungen
10. [Gardeners Path — Petunia Pests](https://gardenerspath.com/plants/flowers/petunia-pests/) — Schädlinge, Biologische Bekämpfung
11. [Proven Winners — Caring for Supertunias](https://www.provenwinners.com/Caring-for-Supertunias) — Düngung, Sorteneigenschaften
12. [Gardening Know How — Fertilize Petunias](https://www.gardeningknowhow.com/ornamental/petunia/fertilize-petunias) — NPK-Anforderungen, Düngungsintervalle
13. [MDPI Horticulturae — Substrate pH and Fertilizer Rate Modulate Petunia Responses](https://www.mdpi.com/2311-7324/12/3/280) — pH-Anforderungen, wissenschaftliche Daten
14. [Hortipendium — Petunia Schadbilder](https://www.hortipendium.de/Petunia_Schadbilder) — Krankheitsbilder, Schädlingsdiagnose
15. [Hausgarten.net — Petunien Krankheiten und Schädlinge](https://www.hausgarten.net/petunie-petunia-x-hybrida/) — Praxisnahe Pflege- und IPM-Hinweise
16. [Plantura — Petunien Pflanzenportrait](https://www.plantura.garden/blumen-stauden/petunien/petunien-pflanzenportrait) — Allgemeine Kulturinformation, Sorten
17. [Gardeners Path — Petunia Cold Hardiness](https://gardenerspath.com/plants/flowers/petunia-cold-hardiness/) — Frosttoleranz, Überwinterungshinweise
18. [Epic Gardening — Overwinter Potted Petunias](https://www.epicgardening.com/overwinter-potted-petunias/) — Überwinterungsmethoden
