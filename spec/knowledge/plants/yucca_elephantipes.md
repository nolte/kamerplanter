# Yucca-Palme, Elefantenfuß-Yucca — Yucca elephantipes

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Wikipedia Yucca gigantea](https://en.wikipedia.org/wiki/Yucca_gigantea), [Missouri Botanical Garden](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b538), [OurHouseplants](https://www.ourhouseplants.com/plants/yucca), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/yucca-elephantipes-the-architectural-desk-gem/), [ASPCA Toxicity](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/yucca), [Gardening Know How IPM](https://www.gardeningknowhow.com/ornamental/foliage/yucca/yucca-plant-bugs.htm), [NC State Extension](https://plants.ces.ncsu.edu/plants/yucca-gigantea/), [Plantophiles](https://plantophiles.com/plant-care/yucca-elephantipes/), [Gardenia.net](https://www.gardenia.net/plant/yucca-elephantipes), [GBIF](https://www.gbif.org/species/2775716)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Yucca elephantipes | `species.scientific_name` |
| Synonym | Yucca gigantea Lem. (akzeptierter Name nach APG IV; Y. elephantipes ist der gebräuchliche Handelsnamen) | — |
| Volksnamen (DE/EN) | Yucca-Palme, Elefantenfuß-Yucca, Riesen-Yucca; Spineless Yucca, Stick Yucca, Giant Yucca, Soft-Tip Yucca | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Unterfamilie | Agavoideae | — |
| Gattung | Yucca | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam (schwach/fakultativ ausgeprägt — weak/facultative CAM) | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 50–150+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur Wuchs (°C) | <!-- DATEN FEHLEN — kein publizierter Wuchs-/Phänologie-GDD-Basiswert für Y. elephantipes/gigantea auffindbar; Wachstum stoppt praktisch unter ~10°C, Kälteschäden ab ~4°C, aber dies sind Minimal-/Schadschwellen, KEINE belegte GDD-Basis und werden daher nicht als base_temp eingetragen --> | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- entfällt: tagneutral (day_neutral) — kein Kurztag-/Langtagblüher, daher kein numerischer Stunden-Schwellwert; siehe lifecycle_configs.photoperiod_type --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich — übersteht keine anhaltenden Minustemperaturen. Kurzzeitig bis -2°C möglich, darunter Kälteschäden. In Mitteleuropa (USDA 7–8) zwingend als Kübelpflanze mit Winterquartier kultivieren. | `species.hardiness_detail` |
| Heimat | Mexiko (Veracruz, Oaxaca, Chiapas) und Zentralamerika (Guatemala, Belize, Honduras) — tropische und subtropische Trockenwälder, Halbwüsten | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |
| Luftreinigung-Score | 0.2 | `species.air_purification_score` |
| Entfernt Schadstoffe | formaldehyde (geringer Nachweis; nicht Teil der originalen NASA Clean Air Study 1989) | `species.removes_compounds` |

**Hinweis:** *Yucca gigantea* ist der botanisch korrekte und akzeptierte Name nach APG IV (Lemaire, 1859). Im Handel und in der gärtnerischen Praxis wird jedoch fast ausschließlich *Yucca elephantipes* verwendet — dieser Name bleibt deshalb als primary scientific_name im System. Die Pflanze ist KEINE echte Palme, sondern ein Verwandter der Agaven (Agavoideae). Im Freiland erreicht sie 8–12 m Höhe; als Zimmerpflanze bleibt sie bei 1,5–3 m. Wächst sehr langsam (15–30 cm/Jahr unter optimalen Bedingungen). Die stumpfen, weichen Blattspitzen — im Gegensatz zur stachelbewehrten *Yucca filamentosa* — gaben ihr den Beinamen "Spineless Yucca".

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt (Zierpflanze) | `species.harvest_months` |
| Blütemonate | Entfällt für Zimmerkultur (blüht in Mitteleuropa als Zimmerpflanze extrem selten; outdoor in Zone 10+ Juni–August) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Stecklingsmethode (empfohlen):** Stammstücke von 15–30 cm Länge aus verholztem Material schneiden. Schnittflächen 1–2 Stunden an der Luft trocknen lassen. In leicht feuchtes Kakteensubstrat oder reines Perlite stecken. Bei 22–26°C und indirektem Licht wurzeln in 6–12 Wochen. Marktübliche Ware besteht häufig aus importierten Stammstücken aus Zentralamerika, die direkt verholzt geliefert werden.

**Ableger-Methode (einfachste):** Natürlich entstehende Seitentriebe an der Stammbasis (Pups) mit scharfem, sauberem Messer abtrennen wenn 15+ cm groß. Schnittfläche mit Holzkohle oder Zimtpulver behandeln. In Kakteensubstrat pflanzen.

**Saatgut:** Möglich, aber sehr zeitaufwändig (Keimung in 3–4 Wochen, mehrere Jahre bis zur vorzeigbaren Pflanze). In Mitteleuropa kaum praxisrelevant.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Pflanzenteile, insbesondere Blätter, Stamm und Wurzeln | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Steroidal-Saponine (steroidal saponins) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Die ASPCA listet Yucca als toxisch für Hunde und Katzen. Symptome bei Ingestion: Erbrechen, Durchfall, Speichelfluss, Schwäche, Koordinationsprobleme, bei Katzen auch erweiterte Pupillen. Die Konzentration der Saponine ist gering — schwere Vergiftungen sind selten, aber Tierarztbesuch bei Verdacht auf Ingestion empfehlenswert. Für Kinder gelten ähnliche Risiken (GI-Beschwerden). Die spitzen, harten Blattspitzen der Zimmervariante sind zwar weicher als bei anderen Yucca-Arten, können jedoch bei Kleinkindern zu Augen- und Hautverletzungen führen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Rückschnitt nur bei zu groß gewordenen Exemplaren nötig. Stamm kann auf gewünschte Höhe eingekürzt werden (ca. 5 cm oberhalb einer Blattnarbe schneiden) — treibt aus dem Stammstumpf neu aus. Abgestorbene und vergilbte untere Blätter regelmäßig entfernen; nach unten biegen und abreißen (nicht schneiden, um Basalstumpfe zu vermeiden). Schutzhandschuhe tragen (Blattkanten können schneiden).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–30 (ausgewachsene Pflanze) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) — Indoor | 100–300 | `species.mature_height_cm` |
| Wuchshöhe (cm) — Outdoor | 800–1200 | — |
| Wuchsbreite (cm) | 80–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 200–400 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässiges Kakteensubstrat oder Allzweckerde (70%) gemischt mit Perlite (20%) und grobem Sand (10%). pH 6,0–7,0. Topf mit Drainageloch ist Pflicht — Staunässe ist der häufigste Todesgrund. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN — kein artspezifisch belegter Kompensationspunkt für Y. elephantipes/gigantea auffindbar; als lichtbedürftige Sonnenpflanze (full_sun) eher im oberen Bereich von Sonnenpflanzen, aber nicht aus 2 seriösen Quellen artgenau belegbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN — s. min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–60 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe, Maas-Hoffman a) | <!-- DATEN FEHLEN — keine quantitativen Maas-Hoffman-ECe-Werte für Y. elephantipes publiziert; qualitativ als küsten-/salztolerant eingestuft (Klasse tolerant), Schwellwert daher nicht belegbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m, Maas-Hoffman b) | <!-- DATEN FEHLEN — kein publizierter Slope-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweis:** *Yucca elephantipes* ist ausgesprochen lichtbedürftig und bevorzugt vollsonnige Standorte (mindestens 6 h direkte Sonne); Halbschatten wird toleriert, führt aber zu vergeiltem (spindeligem) Wuchs — daher `shade_tolerance: full_sun`. Das Wurzelsystem ist faserig (fibrous) und mittelflach; die Hauptwurzelzone liegt effektiv bei rund 30–60 cm (Container-Mindesttiefe 30 cm, im Freiland tiefere Verankerung). Gegenüber Staunässe ist die Art sehr empfindlich (`sensitive`) — Wurzel-/Stammfäule ist die häufigste Todesursache. Bezüglich Bodensalzgehalt gilt sie als salztolerant und küstentauglich (`tolerant`), quantitative ECe-Schwellen (Maas-Hoffman) sind jedoch nicht publiziert. Der pH-Vorzug 6,0–7,5 ist quellentreu (porös, durchlässig, schwach sauer bis neutral) und deckt die in §1.6 und §2.3 genannte engere Spanne 6,0–7,0 ab.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

Die Yucca elephantipes ist eine mehrjährige Zimmerpflanze ohne klassischen Ernte-Zyklus. Das Phasenmodell orientiert sich an der saisonalen Aktivität und der Etablierungsphase junger Pflanzen.

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 60–120 | 1 | false | false | low |
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 2 | false | false | medium |
| Sommerpause (Hitze-Plateau) | 30–60 | 3 | false | false | high |
| Winterruhe | 90–120 | 4 | false | false | high |
| Reife Dauerkultur | 365+ (wiederkehrend) | 5 | true | false | high |

**Hinweis:** Die Phasen 2–4 werden bei etablierten Pflanzen jährlich zyklisch durchlaufen. Phase 5 ("Reife Dauerkultur") modelliert den stabilen Langzeitzustand für ältere Exemplare ohne ausgeprägten Saisonrhythmus — entspricht dem `perennial`-Zyklus mit `cycle_restart: true`.

### 2.2 Phasen-Anforderungsprofile

#### Phase: Etablierung (Neukauf oder frisch umgetopft)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | <!-- DATEN FEHLEN — für Sukkulenten-Typ ca. 0.8–1.5 kPa geschätzt --> | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 (Schwelle stomatären Kollaps; deutlich oberhalb des feuchteliebenden Etablierungs-Korridors) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (CAM-/Sukkulenten-Typ mit nächtlichem Stomata-Öffnen → geringe VPD-Empfindlichkeit) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 (offenes Tageslicht/helles indirektes Licht; R:FR ≈ 1.1–1.2) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Hinweis:** In der Etablierungsphase keine Düngung. Substrat nur leicht feucht halten — die Pflanze fokussiert Energie auf Wurzelwachstum. Indirektes, helles Licht bevorzugt (kein direktes Mittagssonnenlicht in den ersten 4 Wochen nach Umtopfen).

#### Phase: Aktives Wachstum (Frühling/Sommer, März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | <!-- DATEN FEHLEN --> | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (kritischer Punkt; bei sukkulentem CAM-Typ hoch angesetzt) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.46–0.50 (direkte Vollsonne; R:FR ≈ 1.1–1.2) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Hinweis:** In dieser Phase entfaltet sich das Hauptwachstum. Direktsonne (auch Mittagssonne) wird toleriert und fördert das Wachstum. Für Terrassen-/Balkonaufstellung ab Mai bis Ende September geeignet. Gießen wenn die oberen 3–5 cm der Erde trocken sind — "Fingertest".

#### Phase: Sommerpause (Hitze-Plateau, Juli–August)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 25–35 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–25 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 20–40 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | <!-- DATEN FEHLEN --> | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 (höchste Schwelle; trockenheits-/hitzetolerante CAM-Phase) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 26–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.46–0.50 (direkte Vollsonne; R:FR ≈ 1.1–1.2) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Hinweis:** Bei extremer Hitze (>35°C) wird das Wachstum gedrosselt. Gießintervall trotz Hitze nicht verkürzen — die Pflanze steuert über ihre Kauleszenzen (verdickte Stammstrukturen) die Wasserversorgung selbst. Keine Blattsprays bei direkter Sonneneinstrahlung (Verbrennungsgefahr durch Wasserlinsen).

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | <!-- DATEN FEHLEN --> | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 (niedrigere Schwelle in kühler, lichtarmer Ruhephase) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.55 (heller Innenstandort/Winterlicht, mehr diffuse Anteile; R:FR leicht reduziert) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–35 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

**Hinweis:** Keine Düngung in dieser Phase. Gießintervall stark reduzieren — Überwässerung im Winter bei niedrigen Temperaturen ist die häufigste Ursache für Wurzelfäule. Kühlere Überwinterung (10–15°C) ist möglich und sogar förderlich für die Gesundheit der Pflanze. Minimum: 7°C (kurzfristig tolerierbar). Standort hell halten — auch im Winter braucht die Yucca so viel Licht wie verfügbar.

#### Phase: Reife Dauerkultur (etablierte mehrjährige Pflanze)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | <!-- DATEN FEHLEN --> | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 (gemittelt über Jahreszyklus der etablierten Pflanze) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.46–0.52 (je nach Sommer-Vollsonne vs. heller Innenstand im Winter) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14 (Sommer) / 28 (Winter) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 (je nach Topfgröße) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Etablierung | 0:0:0 (kein Dünger) | 0.0 | 6.0–7.0 | — | — | — | — |
| Aktives Wachstum | 1:1:1 (ausgewogen, leicht) | 0.4–0.8 | 6.0–7.0 | 40–80 | 20–40 | — | 1–2 |
| Sommerpause | 1:1:1 (reduziert) | 0.3–0.6 | 6.0–7.0 | 30–60 | 20–30 | — | 1 |
| Winterruhe | 0:0:0 (kein Dünger) | 0.0 | 6.0–7.0 | — | — | — | — |
| Reife Dauerkultur | 1:1:1 (saisonal) | 0.4–0.8 | 6.0–7.0 | 40–80 | 20–40 | — | 1–2 |

**Hinweis:** Yucca elephantipes ist ein ausgeprägter Schwachzehrer. Überdüngung führt zu Blattspitzenverbrennung und Salzakkumulation im Substrat. EC-Werte sind für Topfkultur mit Kakteenerde / Perlite-Mischung angegeben. In reiner Erde (ohne Nährstoff-Analyse) ist deutlich vorsichtigere Düngung ratsam.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (Mn/Zn/Cu/Mo):**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Etablierung | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Aktives Wachstum | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Sommerpause | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Reife Dauerkultur | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

KA-Felder: `nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`.

**Hinweis zu Mikronährstoffen:** Für *Yucca elephantipes* sind keine artspezifischen Mn-/Zn-/Cu-/Mo-Sollkonzentrationen (ppm) aus seriösen Quellen belegbar. Als Schwachzehrer in Topfkultur deckt ein handelsüblicher Kakteen-/Grünpflanzen-Volldünger den Mikronährstoffbedarf im Spurenbereich vollständig ab; eine separate Mikronährstoff-Dosierung ist nicht erforderlich und ein Überangebot (besonders Cu/Mn) eher schädlich. Daher bleiben die Felder mit `<!-- DATEN FEHLEN -->` markiert, statt unbelegte Werte einzutragen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Zeitraum/Bedingungen |
|------------|---------|----------------------|
| Etablierung → Aktives Wachstum | time_based | 60–120 Tage; neue Blätter sichtbar, Wurzeln am Topfboden |
| Aktives Wachstum → Sommerpause | time_based | Monate 7–8; Wachstum verlangsamt sich bei >30°C |
| Sommerpause → Winterruhe | time_based | Oktober; Temperaturen <15°C nachts |
| Winterruhe → Aktives Wachstum | time_based | März–April; Temperaturen steigen, mehr Licht verfügbar |
| Aktives Wachstum → Reife Dauerkultur | manual | Nach 3–5 Jahren; Pflanze hat stabiles Stammsystem ausgebildet |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch / Flüssig (Indoor/Topf)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 7-4-6 | 2–3 ml/L (halbe Dosierung) | 2 | aktives Wachstum |
| Liquid Fertilizer for Cacti | Green24 / Dehner | base | 5-5-7 | 2 ml/L | 2 | aktives Wachstum |
| Grünpflanzendünger flüssig | Substral | base | 7-3-6 | 2 ml/L (halbe Dosierung) | 2 | aktives Wachstum |
| Wuxal Zimmerpflanzen | Neudorff | supplement | 10-5-7 | 2–3 ml/L | 2 | aktives Wachstum |

#### Organisch / Festdünger (Topf und Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kakteendünger Stäbchen | Substral / Compo | organomineral | 1–2 Stäbchen/5 L Topfvolumen | Apr–Sep | Topfkultur |
| BioKraft Langzeitdünger | Compo | organisch | 20–30 g/Topf (15-L-Topf) | April | Topfkultur |
| Hornspäne | Beckmann / AS-Dünger | organisch | 20–30 g/Topf | März | Topfkultur und Kübel |
| Kompost reif | eigen | organisch | 1–2 L bei Umtopfen einarbeiten | Frühjahr | Freiland-Kübel |

### 3.2 Düngungsplan (Jahresplan Indoor)

| Monat | Phase | Dünger | Dosierung | Intervall | Hinweise |
|-------|-------|--------|-----------|-----------|----------|
| Jan–Feb | Winterruhe | keiner | — | — | Keine Düngung |
| März | Aktives Wachstum beginnt | Flüssigdünger (halb) | 2 ml/L | einmalig | Erst düngen wenn neue Blätter wachsen |
| Apr–Mai | Aktives Wachstum | Flüssigdünger | 2–3 ml/L | alle 4 Wochen | Normal dosieren |
| Jun–Aug | Aktives Wachstum / Sommerpause | Flüssigdünger | 2–3 ml/L | alle 4–6 Wochen | Bei Hitze-Stagnation aussetzen |
| Sep | Ausklang Wachstum | Flüssigdünger | 2 ml/L | einmalig | Letzte Düngung der Saison |
| Okt–Dez | Winterruhe | keiner | — | — | Keine Düngung |

### 3.3 Mischungsreihenfolge

> **Hinweis:** Da Yucca nur mit einfachen Flüssigdüngern gedüngt wird (kein Multi-Part-System), ist die Mischungsreihenfolge unkritisch. Wichtiger ist die Verdünnung:

1. Behälter mit Leitungswasser (Raumtemperatur, 18–22°C) füllen
2. Flüssigdünger in der angegebenen (halbierten!) Konzentration zugeben
3. Gut umrühren
4. Erst dann über das Substrat gießen — nie auf trockenes Substrat düngen (Wurzelverbrennung)

### 3.4 Besondere Hinweise zur Düngung

Yucca elephantipes reagiert sehr empfindlich auf Überdüngung. Häufigste Fehler:
- **Zu hohe Konzentration:** Immer auf halbe oder Viertel-Dosierung reduzieren
- **Düngung im Winter:** Absolut vermeiden — bei niedrigem Licht kann die Pflanze Nährstoffe nicht verwerten, Salzakkumulation schädigt die Wurzeln
- **Düngung bei Stress:** Bei Schädlingsbefall, nach Umtopfen oder bei Wachstumsstau keine Düngung — erst wenn die Pflanze sich erholt hat
- **Dünger auf trockenes Substrat:** Immer erst gießen, dann düngen — oder mit Gießwasser kombinieren
- **EC-Kontrolle:** Bei Salzablagerungen (weißlicher Belag auf der Erdoberfläche) vollständig durchspülen ("Flushen") und 6–8 Wochen pausieren

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 (→ 35 Tage) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | null (Leitungswasser toleriert) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

**Gießmethode Detail:** Kräftig und gründlich durchgießen bis Wasser aus dem Drainageloch läuft. Untersetzer nach 15–20 Minuten leeren — Staunässe ist der Hauptfeind. Dann vollständig abtrocknen lassen bis die oberen 3–5 cm des Substrats trocken sind. Der "Fingertest" ist zuverlässiger als ein fixer Kalender. Im Winter sogar noch länger zwischen den Wassergaben warten.

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Standortcheck | Sicherstellen dass die Pflanze im Winter an einem hellen Fenster (Süd/West) steht. Gießen stark reduziert. | niedrig |
| Feb | Erster Gießcheck | Substrat auf Trockenheit prüfen. Wenn komplett trocken: sparsam gießen. Noch keine Düngung. | niedrig |
| Mär | Wachstumsstart | Wenn neue Blätter sichtbar: erste Düngung (halbe Dosis). Substrat auf Salzablagerungen prüfen. | mittel |
| Apr | Umtopfen (falls nötig) | Bei wurzelgebundener Pflanze: Topf eine Größe größer wählen. Frisches Kakteensubstrat. | hoch |
| Mai | Freiluft-Umzug | Kübel an Balkon/Terrasse umstellen. Standort mit mindestens 4–6 h Direktsonne. Langsam akklimatisieren (erst Halbschatten, dann volle Sonne über 2 Wochen). | hoch |
| Jun | Reguläre Pflege | Wöchentlich Gießbedarf prüfen. Düngung monatlich. Auf Schädlinge kontrollieren. | mittel |
| Jul | Hitzepflege | Bei extremer Hitze (>35°C): Standort in Halbschatten oder Schutz. Trotzdem nicht öfter gießen. | mittel |
| Aug | Schädlingscheck | Intensivere Kontrolle auf Spinnmilben (Trockenheit fördert Befall). Abgestorbene Blätter entfernen. | mittel |
| Sep | Letzte Düngung | Letzte Düngungsgabe der Saison. Gießintervall langsam verlängern. | mittel |
| Okt | Einwinterung | Vor ersten Nachtfrösten (<5°C) in Winterquartier holen. Standortwechsel: hell und kühl (10–15°C). | hoch |
| Nov | Winterruhe einleiten | Gießintervall auf 3–5 Wochen verlängern. Keine Düngung mehr. | niedrig |
| Dez | Ruhephase | Minimal gießen, nur wenn Substrat komplett ausgetrocknet ist. | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free <!-- Quelle: Steckbrief-Erweiterung 2026-06 — korrigiert von needs_protection: Y. elephantipes ist frostempfindlich (tender) und wird in Mitteleuropa zwingend frostfrei drinnen überwintert (winter_action=move_indoors), nicht nur mit Schutz im Freien; daher Enum frost_free statt needs_protection --> | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 7 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

**Winterquartier-Optionen (Mitteleuropa):**
- **Ideal:** Helles, kühles Treppenhaus oder Wintergarten (10–15°C, helles Licht)
- **Akzeptabel:** Helle Zimmerecke mit Temperaturen bis 20°C (dann öfter auf Austrocknung prüfen)
- **Kritisch:** Dunkler Keller ist NICHT geeignet — Yucca braucht auch im Winter Licht

**Akklimatisierung im Frühjahr:** Vor dem Stellen ins Freie 2 Wochen lang täglich ein paar Stunden direktem Außenlicht aussetzen (Härtephase). Direkter Wechsel von winterlichem Zimmer auf volle Frühjahrssonne verursacht Sonnenbrand (weiße/braune Blattflecken).

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, silbrig-gelbliche Punkte auf Blättern, später bronze-braune Verfärbung | leaf | alle, besonders Winterruhe (trockene Heizungsluft) | medium |
| Schildläuse | Diaspididae / Coccidae spp. | Braune/gelbliche Schildchen auf Stämmen und Blättern, Honigtau, klebrige Oberflächen | stem, leaf | alle | difficult |
| Schmierläuse (Wollläuse) | Pseudococcus spp. | Weißliche Wachswolle besonders in Blattachseln und Stammritzen, Honigtau | stem, leaf | alle | easy |
| Yucca-Wanze | Halticotoma valida | Silbrige Fraßflecken, gelbliche Blattflecken, schwarze Kotpunkte | leaf | aktives Wachstum | medium |
| Thripse | Thysanoptera spp. | Silbrige Streifenmuster, deformierte junge Blätter, schwarze Kotpunkte | leaf | aktives Wachstum | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Phytophthora-Fäule (Kronenfäule) | fungal (Phytophthora spp.) | Braune, weiche Stammpartien an der Basis, Welke trotz feuchter Erde, fauliger Geruch | Staunässe, schlechte Drainage, zu häufiges Gießen | 7–21 | alle, besonders Winterruhe |
| Pythium-Wurzelfäule | fungal (Pythium spp.) | Braune, schleimige Wurzeln, Welke, Wachstumsstillstand | Dauernasse Erde, schlechte Drainage | 7–14 | alle, besonders Winterruhe |
| Fusarium-Stängelfäule | fungal (Fusarium spp.) | Braune, eingesunkene Stellen am Stamm, Trockenheit der befallenen Bereiche | Verletzungen, feuchte Bedingungen bei Ablegeranzucht | 5–10 | Etablierung |
| Blattfleckenkrankheit | fungal (Cercospora spp., Colletotrichum spp.) | Braune Blattflecken mit gelblichem Rand | hohe Luftfeuchte, Nässe auf Blättern | 5–14 | aktives Wachstum |
| Sonnenbrand (abiotisch) | physiologisch | Weiße bis gelbbraune, trockene Flecken auf direkter Sonnenseite | Plötzliche Exposition gegenüber starker Direktsonne ohne Akklimatisierung | sofort | Etablierung, nach Standortwechsel |
| Kälteschäden (abiotisch) | physiologisch | Glasige, dann braune Blätter, welke Blattspitzen, bei starkem Frost Stammfäule | Temperaturen unter 5°C | sofort | Winterruhe |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 10–20 (bei aktiver Infektion) | 14–21 |
| Neoseiulus californicus | Spinnmilbe (breiteres Temperaturspektrum) | 10–25 | 14–21 |
| Cryptolaemus montrouzieri (Larven) | Schmierläuse, Wollläuse | 3–5 pro Pflanze | 21–28 |
| Lacewing-Larven (Chrysoperla carnea) | Schmierläuse, Blattläuse, Thripse | 10–20 | 14 |

**Hinweis:** Für Indoor-Zimmerpflanzen sind Nützlinge praktisch einsetzbar. Bei Schildläusen ist mechanische Entfernung (Alkohol-Wattestäbchen) oft effizienter. Nützlinge nur einsetzen wenn keine chemischen Mittel in den letzten 2–3 Wochen verwendet wurden.

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl 2% | biological | Azadirachtin | Sprühbehandlung aller Pflanzenteile, 3× im Abstand von 7 Tagen | 3 | Spinnmilben, Schmierläuse, Schildläuse (Crawler-Stadium), Thripse |
| Insektizide Seife | biological | Kalium-Fettsäuresalze | Sprühen (inkl. Blattunterseiten), 3× im Abstand von 5–7 Tagen | 0 | Spinnmilben, Schmierläuse, Thripse |
| Alkohol (70%) + Wattestäbchen | mechanical | Isopropylalkohol | Schildläuse und Schmierläuse manuell abtupfen | 0 | Schildläuse, Schmierläuse |
| Hornmilben-Bekämpfung (Raubmilben) | biological | — | Phytoseiulus/Neoseiulus freisetzen | 0 | Spinnmilben |
| Horticultural Oil | chemical | Mineralöl | Einsprühen, Abtöten durch Erstickung | 3 | Schildläuse, Spinnmilben |
| Imidacloprid (Stäbchen) | chemical | Imidacloprid (Neonicotinoid) | Stäbchen ins Substrat stecken, systemische Wirkung | 28 (Indoor-Pflanzung) | Schildläuse, Schmierläuse, Thripse |
| Fosetyl-Al (Aliette) | chemical | Fosetyl-Aluminium | Foliarspray, 1 oz/Gallone Wasser | 14 | Phytophthora (prophylaktisch) |
| Kupfersulfat / Bordeaux-Brühe | chemical | Kupfersulfat | Sprühen, wöchentlich bei starkem Befall | 14 | Pilzliche Blattfleckenkrankheiten |
| Kulturmaßnahme: Drainage | cultural | — | Topf mit Drainageloch, kein Untersetzer-Stau | 0 | Wurzelfäule (Prävention) |
| Kulturmaßnahme: Isolation | cultural | — | Befallene Pflanze sofort isolieren | 0 | Alle Schädlinge (Übertragung verhindern) |
| Luftfeuchte erhöhen | cultural | — | Luftbefeuchter oder feuchte Kiesel im Untersetzer | 0 | Spinnmilben (Prävention) |

**Hinweis Schimmel-Prävention:** Blätter beim Gießen nicht benetzen. Kein Sprühnebel auf Blätter im Winter. Gute Luftzirkulation sicherstellen. Bei Verdacht auf Phytophthora: Gießen sofort stoppen, Pflanze aus dem Topf nehmen, Wurzeln inspizieren, befallene Wurzeln entfernen, in frisches steriles Substrat umpflanzen.

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Trockenheit | abiotischer Stress | `resistant_to` |
| Salzböden (moderat) | abiotischer Stress | `resistant_to` |
| Direktsonne (akklimatisiert) | abiotischer Stress | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Entfällt (Dauerpflanze, keine Fruchtfolge im klassischen Sinne) |
| Empfohlene Vorfrucht | Entfällt |
| Empfohlene Nachfrucht | Entfällt |
| Anbaupause (Jahre) | Entfällt |

**Hinweis:** Als mehrjährige Zimmerpflanze unterliegt die Yucca-Palme keiner Fruchtfolgeplanung. Im Freiland-/Kübel-Bereich gilt: nach einer Yucca kann prinzipiell jede andere Pflanzenfamilie folgen, da Asparagaceae keine nennenswerten allelopathischen Substanzen oder bodenbildenden Krankheitserreger hinterlässt.

### 6.2 Mischkultur — Gute Nachbarn (Outdoor/Kübel)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Sedum (Fetthenne) | Sedum spp. | 0.9 | Gleiche Trockenheitstoleranz, Bodendecker-Wirkung, kein Wasserkonkurrenz-Problem | `compatible_with` |
| Tagetes (Studentenblume) | Tagetes spp. | 0.7 | Attraktiv für Bestäuber, nematodenfeindlich, vergleichbare Sonnenliebe | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.8 | Ähnlicher Wasserbed arf, Bestäuber-Attraktion, mediterranes Ensemble | `compatible_with` |
| Agave | Agave spp. | 0.8 | Gleiche Familie (Agavoideae), gleiche Pflegeansprüche, gleiche Trockenheitspräferenz | `compatible_with` |
| Rudbeckia | Rudbeckia fulgida | 0.7 | Vergleichbare Sonnenpräferenz, blüht gleichzeitig, Bestäuber-Attraktion | `compatible_with` |
| Verbena | Verbena bonariensis | 0.7 | Trockenheitstolerant, ähnliche Lichtansprüche, Schmetterlingsmagnet | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Farne | Pteridophyta spp. | Extrem unterschiedliche Feuchtigkeitsbedürfnisse — Farne brauchen dauerhaft feuchtes Substrat, Yucca stirbt dabei | severe | `incompatible_with` |
| Calathea / Maranta | Goeppertia spp. | Konträre Wasserbedürfnisse und Humidität — eine der Pflanzen würde immer leiden | severe | `incompatible_with` |
| Ficus benjamina | Ficus benjamina | Konkurrierendes Wurzelwachstum, unterschiedliche Gieß-Anforderungen | moderate | `incompatible_with` |
| Impatiens (Fleißiges Lieschen) | Impatiens walleriana | Hoher Wasserbedarf konträr zur Yucca-Trockenheitspräferenz | moderate | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Asparagaceae (Beaucarnea, Dracaena) | `shares_pest_risk` | Schildläuse, Spinnmilben, Schmierläuse | `shares_pest_risk` |
| Agavoideae (Agave) | `shares_pest_risk` | Schildläuse, Sukkulentenfäulen (Phytophthora) | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Yucca elephantipes |
|-----|-------------------|-------------|--------------------------------------|
| Elefantenfuß | Beaucarnea recurvata | Gleiche Familie, ähnliches Erscheinungsbild, gleiche Pflege | Noch trockenheitstoleranter, bizarrere Stammform, für Sammler interessanter |
| Drachenbäumchen | Dracaena marginata | Gleiche Familie Asparagaceae, ähnliche Silhouette | Toleriert mehr Schatten, geringeres Verletzungsrisiko (keine scharfen Blattspitzen) |
| Aloe vera | Aloe vera | Ähnlicher Sukkulenten-Pflegestil, ähnliche Lichtansprüche | Medizinisch nutzbar, kompakter, keine Toxizität für Haustiere |
| Pandan | Pandanus spp. | Ähnliche Tuffwuchs-Form mit Stammbildung | Toleriert mehr Feuchtigkeit, für tropischere Wohnräume geeignet |
| Yucca filamentosa (Gartenyucca) | Yucca filamentosa | Gleiche Gattung | Winterhart bis -20°C, echte Freilandpflanze für Deutschland — aber gefährliche Blattspitzen! |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,pruning_type,pruning_months,traits
Yucca elephantipes,"Yucca-Palme;Elefantenfuß-Yucca;Riesen-Yucca;Spineless Yucca;Stick Yucca;Giant Yucca",Asparagaceae,Yucca,perennial,day_neutral,tree,fibrous,"9b;10a;10b;11a;11b",0.0,"Mexiko (Veracruz, Oaxaca, Chiapas), Zentralamerika",yes,20,30,150,120,300,yes,yes,false,false,light_feeder,false,tender,spring_pruning,"3;4",ornamental
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Jewel,Yucca elephantipes,unbekannt,,variegated;ornamental,,none,clone
Variegata,Yucca elephantipes,unbekannt,,variegated;ornamental;;none,clone
Silver Star,Yucca elephantipes,unbekannt,,variegated;ornamental;;none,clone
```

**Hinweis Sorten:** Yucca elephantipes-Sorten werden fast ausschließlich vegetativ (Stammstecklinge) vermehrt. Genaue Züchter/Herkunftsangaben sind für die Handelssorten 'Jewel', 'Variegata' und 'Silver Star' nicht vollständig dokumentiert — Angaben mit `<!-- DATEN FEHLEN -->` entsprechend markieren wenn Import präzise sein soll.

---

## 9. Praktische Import-Hinweise

**Botanical Family — Asparagaceae:** Wird wahrscheinlich bereits im System vorhanden sein (geteilt mit Beaucarnea recurvata, Dracaena marginata, Chlorophytum comosum). Vor dem Import prüfen ob die Familie bereits existiert und nur der `belongs_to_family`-Edge zu setzen ist.

**Care Style Mapping:** `succulent` (aus REQ-022 Preset-Tabelle) ist die passendste Zuordnung. Der Gießrhythmus der Yucca ist nahezu identisch mit dem Sukkulenten-Preset (14 Tage Sommer, 2.5× Winter). Abweichung: Yucca braucht signifikant mehr Licht als typische Sukkulenten.

**Lebenszyklus-Modellierung:** Die saisonalen Phasen (aktives Wachstum / Winterruhe) entsprechen dem `perennial`-Modell mit `cycle_restart: true`. Die Phase "Reife Dauerkultur" kann als einzige Phase für Langzeit-Zimmerpflanzen modelliert werden, falls der Nutzer keine saisonale Detailsteuerung wünscht.

**Toxizitäts-Warnung:** Bei der Anlage einer PlantInstance für Haushalte mit Katzen/Hunden sollte das System die ASPCA-Toxizität prominently anzeigen (nicht nur als verstecktes Feld).

---

## Quellenverzeichnis

1. [Wikipedia — Yucca gigantea](https://en.wikipedia.org/wiki/Yucca_gigantea) — Taxonomie, Synonyme, Verbreitung, Erstbeschreibung Lemaire 1859
2. [Missouri Botanical Garden — Yucca elephantipes](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b538) — Hardiness Zones, botanische Klassifikation
3. [OurHouseplants — Yucca Care Guide](https://www.ourhouseplants.com/plants/yucca) — Pflege, Gießen, Düngen, Vermehrung
4. [Healthy Houseplants — Yucca elephantipes](https://www.healthyhouseplants.com/indoor-houseplants/yucca-elephantipes-the-architectural-desk-gem/) — Detaillierte Pflegeangaben, Substrat, Überwinterung
5. [ASPCA — Yucca Toxicity](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/yucca) — Toxizität Katzen/Hunde (Steroidal-Saponine)
6. [Gardening Know How — Yucca Pests](https://www.gardeningknowhow.com/ornamental/foliage/yucca/yucca-plant-bugs.htm) — Schädlinge, IPM
7. [NC State Extension — Yucca gigantea](https://plants.ces.ncsu.edu/plants/yucca-gigantea/) — Taxonomie, Hardiness, Merkmale
8. [Plantophiles — Yucca elephantipes Care](https://plantophiles.com/plant-care/yucca-elephantipes/) — Pflege, Licht, Temperatur, Vermehrung
9. [Gardenia.net — Yucca elephantipes](https://www.gardenia.net/plant/yucca-elephantipes) — Übersicht, Companions
10. [Gardenia.net — Yucca Companion Plants](https://www.doityourself.com/stry/choosing-the-best-companion-plants-for-a-yucca) — Mischkultur
11. [Plant Addicts — Yucca Companion Plants](https://plantaddicts.com/yucca-companion-plants/) — Mischkulturpartner
12. [GBIF — Yucca gigantea](https://www.gbif.org/species/2775716) — Taxonomie, Verbreitungsdaten
13. [Gardenerdy — Yucca Plant Diseases](https://gardenerdy.com/yucca-plant-diseases/) — Pilzkrankheiten, Phytophthora, Pythium
14. [Pet Poison Helpline — Yucca](https://www.petpoisonhelpline.com/poison/yucca/) — Toxizität, klinische Zeichen
15. [PalmTalk Forum — Cold Hardiness Y. elephantipes](https://www.palmtalk.org/forum/topic/46928-true-cold-hardiness-of-yucca-elephantipes/) — Praxisbericht Winterhärte Zone 9b
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
16. [Heyduk et al. — Agavoideae: an emergent model clade for CAM evolutionary biology (Annals of Botany)](https://academic.oup.com/aob/article/132/4/727/7164427) — CAM-Evolution in Agavoideae/Yucca; obligate C3, fakultative/weak CAM und obligate CAM innerhalb der Gattung Yucca; Grundlage für Einordnung photosynthesis_type=cam (schwach/fakultativ)
17. [Heyduk et al. 2019 — Shared expression of CAM genes pre-dates the origin of CAM in Yucca (J. Exp. Botany / PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6883266/) — Yucca-Photosynthese-Spektrum (Y. aloifolia CAM, Y. filamentosa C3, Y. gloriosa C3+CAM); weak-CAM-Kontext
18. [Wikipedia — Yucca gigantea (Photosynthese-/Standort-/CAM-Kontext)](https://en.wikipedia.org/wiki/Yucca_gigantea) — semi-arider Standort, Trockenheitstoleranz, Wurzelfäule bei Überwässerung (Staunässe-Empfindlichkeit)
19. [ForwardPlant — Soil for Growing Yucca gigantea](https://www.forwardplant.com/care/soil/yucca-gigantea/) — Boden-pH 6.5–7.5, poröses durchlässiges Substrat, Drainage; Beleg soil_ph_preference
20. [UF/IFAS Gardening Solutions — Salt-Tolerant Plants](https://gardeningsolutions.ifas.ufl.edu/design/landscaping-for-specific-sites/salt-tolerant-plants/) — Yucca als salztolerante Küstenpflanze; Beleg salt_tolerance_class=tolerant
21. [Weekand — Yucca for Coastal Planting](https://www.weekand.com/home-garden/article/yucca-coastal-planting-18070346.php) — Giant Yucca (Y. elephantipes) salztolerant/küstentauglich; Beleg salt_tolerance_class=tolerant
22. [Planet Desert — Yucca Types, Care & Growing Guide](https://planetdesert.com/blogs/news/yucca-types-care-guide) — Lichtbedarf full sun (≥6 h Direktsonne), Staunässe-/Wurzelfäule-Empfindlichkeit; Beleg shade_tolerance=full_sun, waterlogging_tolerance=sensitive
23. [UF/IFAS Fact Sheet ST-675 — Yucca elephantipes](https://hort.ifas.ufl.edu/trees/YUCELEA.pdf) — Wuchs, Standort, Wurzel-/Containerangaben; Beleg effective_root_depth_cm
24. [allthingslighting.org — Far-Red Lighting and the Phytochromes](https://www.allthingslighting.org/far-red-lighting-and-the-phytochromes/) — Far-Red-Fraction FR/(R+FR) ≈ 0.46 / R:FR ≈ 1.1–1.2 in direkter Vollsonne, höher unter Schatten; Anker far_red_fraction
25. [Yamori et al. 2013 — Temperature response of photosynthesis in C3, C4, and CAM plants (Plant Cell Environ./UWO PDF)](https://publish.uwo.ca/~dway4/files/Yamori%20et%20al.%202013.pdf) — Temperaturoptima CAM-Photosynthese; Grundlage photosynthesis_temp_opt_c und vpd_sensitivity=low
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
