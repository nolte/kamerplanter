# Echter Salbei — Salvia officinalis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Compo Salbei, Samen.de Salbei, Gartenratgeber Salbei, Pflanzen-Kölle Salbei

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Salvia officinalis | `species.scientific_name` |
| Volksnamen (DE/EN) | Echter Salbei, Küchensalbei, Heilsalbei; Common Sage, Garden Sage | `species.common_names` |
| Familie | Lamiaceae | `species.family` → `botanical_families.name` |
| Gattung | Salvia | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für S. officinalis auffindbar; Keim-Kardinaltemperaturen NICHT als Wuchsbasis übernommen --> | `species.base_temp` |
| Lebensdauer (Jahre) | 3–5 (kurzlebige Staude/subshrub; nach 3–4 Jahren verholzt und weniger ertragreich) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false (immergrüner Halbstrauch/evergreen subshrub; keine obligate Dormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (tagneutraler Blüher; blüht ab 2. Jahr an reifen Trieben ohne Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (entfällt; vernalization_required = false) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN: tagneutral, kein Kurztag-/Langtag-Schwellenwert; photoperiod_type = day_neutral --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy [KORRIGIERT 2026-07: war half_hardy — inkonsistent mit USDA-Zone 4a-8b und RHS H5-Rating; siehe Audit-Quellen] | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -15°C (Sorte 'Berggarten' bis -20°C); RHS-Rating H5 („hardy in most places throughout the UK even in severe winters", -15 bis -10°C); in Norddeutschland Zone 7b-8a mit leichtem Mulchschutz zuverlässig; bei Kahlfrösten ohne Schneebedeckung gelegentliche Ausfälle | `species.hardiness_detail` |
| Heimat | Mittelmeerraum (Dalmatien, Balkan) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Vorkultur Feb–Mär; Keimtemperatur 18–22°C) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (Haupterntefenster; aromatischste Blätter vor der Blüte; vereinzelte Winterernte an frostfreien Tagen möglich, schwächt die Pflanze jedoch [KORRIGIERT 2026-07: „ganzjährig erntbar" widersprach eigener Reife/Dormanz-Phase in §2.1 (Ernte erlaubt: false) und Pflegekalender §4.2 „Nov–Feb Winterruhe"]) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Thujone in ätherischem Öl: in großen Destillat-Mengen problematisch; Küchenmenge unbedenklich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Thujone (in Küchenmengen harmlos) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (Rückschnitt nach dem Winter; NIE ins alte Holz) | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (nach letztem Frost; bei neuem Austrieb) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kalkhaltige, durchlässige Kräutererde mit Sand; pH 6,5–7,5; kein Torf | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein exakter numerischer Kompensationspunkt für S. officinalis veröffentlicht; Studie zeigt bei ~5 % Vollsonne Annäherung an den Kompensationspunkt (Netto-Photosynthese ~0), aber ohne absoluten µmol-Wert --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: siehe min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (verträgt partial_shade, vergeilt dann jedoch; PFAF: „cannot grow in the shade") | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–60 (Bodenbearbeitung ~25–30 cm empfohlen; etablierte Pflanze tiefer wurzelnd, trockenheitstolerant) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (intolerant gegenüber nassen/schlecht drainierten Böden; Staunässe tödlich) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant (Studien: keine nachteiligen Effekte bis ~10–12 dS/m Substrat-ECe) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: kein publizierter Maas-Hoffman-a-Schwellenwert für S. officinalis; die 12,3 dS/m aus Einzelstudie ist kein Maas-Hoffman-Threshold --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein publizierter Maas-Hoffman-b-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 (Bestaroma 6,0–7,0; verträgt mild alkalisch bis ~7,8; kalkliebend, meidet sauer) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–21 | 1 | false | false | low |
| Sämling | 28–42 | 2 | false | false | low |
| Vegetativ (Aufbau) | 56–90 | 3 | false | true | medium |
| Blüte | 28–42 | 4 | false | true | medium |
| Reife/Dormanz | 90–180 (Winter) | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Aufbau 1. Jahr)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8–2.0 (stomatärer Kollaps deutlich oberhalb des Zielkorridors; oberer Zielwert + ~0,3–0,5 kPa) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium (C3-Mediterrankraut, trockenheitsadaptiert, aber kein CAM) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 (optimale Tagestemperatur 21–29°C) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-/Vollsonne-Anker; R:FR ≈ 1,1; Vollsonnen-Kultur) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (trockenverträglich; Staunässe vermeiden) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.6 | 6.5 | 60 | 20 | — | 1 | 0.5 | 0.25 | 0.05 | 0.02 |
| Vegetativ | 1:0:1 | 0.6–1.0 | 6.5–7.0 | 80 | 30 | — | 1 | 0.5–1.0 | 0.25–0.5 | 0.05–0.1 | 0.02–0.05 |
| Blüte | 0:1:1 | 0.5–0.8 | 6.5–7.0 | 60 | 30 | — | 1 | 0.5–1.0 | 0.25–0.5 | 0.05–0.1 | 0.02–0.05 |
<!-- Mikronährstoffe Mn/Zn/Cu/Mo ergänzt — Quelle: Steckbrief-Erweiterung 2026-06 (light_feeder-angepasste Hydroponik-Richtwerte) -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kräuterdünger organisch | Neudorff Azet | organisch | 40–60 g/Pflanze | April | mediterrane Kräuter |
| Reifer Kompost | eigen | organisch | 1–2 L/Pflanze | Frühjahr | alle |
| Horngrieß | Oscorna | organisch-N | 30–50 g/Pflanze | Frühjahr | light_feeder |

#### Mineralisch (bei Bedarf)

| Produkt | Marke | Typ | NPK | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|--------|
| Kräuterdünger flüssig | Compo | mineralisch | 7-3-6 | 1 | Vegetativ |

### 3.2 Besondere Hinweise zur Düngung

Salbei WENIG düngen! Auf mageren, gut kalkhaltig-durchlässigen Böden bildet er die meisten aromatischen ätherischen Öle (Thujon, Camphor, Cineol). Überdüngung macht die Blätter groß und wässrig — Aroma leidet stark. Im ersten Jahr einmalige Kompostgabe bei der Pflanzung ausreichend. Im zweiten und dritten Jahr jährlich eine leichte Frühjahrsdüngung. Niemals im Herbst düngen — fördert weiches, frostanfälliges Holz.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 (sehr selten bis gar nicht gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Trocken bevorzugt; Staunässe ist tödlich; kalkhaltiges Wasser verträglich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 (1× jährlich im Frühjahr) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3, 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur | Aussaat bei 18–22°C; Keimung langsam (14–21 Tage) | mittel |
| Mär–Apr | Rückschnitt | Überwinterte Pflanzen: auf neuen Austrieb hin zurückschneiden; nie ins alte Holz | hoch |
| Mai (nach 15.) | Auspflanzen | Jungpflanzen ab 10 cm; sonniger, kalkiger Standort | hoch |
| Mai–Jun | Blüte | Optional: Blütentriebe entfernen für mehr Blattwachstum; oder für Bienen blühen lassen | niedrig |
| Jun–Aug | Ernte | Triebspitzen abschneiden; fördert Buschigkeit | mittel |
| Okt | Wintervorbereitung | Mulch aus Laub/Reisig um den Stamm; Topfpflanzen schützen | mittel |
| Nov–Feb | Winterruhe | Kaum gießen; kein Düngen; hell und kühl bei Topfpflanze | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy [KORRIGIERT 2026-07: war needs_protection — inkonsistent mit USDA-Zone 4a-8b/RHS H5; analog zu Lavandula angustifolia und Thymus vulgaris (gleiche/geringere Winterhärte, ebenfalls "hardy" trotz Mulchschutz)] | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | — (draußen mit Mulchschutz) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | — | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | — | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste; Silberflecken auf Blättern | leaf | vegetative (Trockenheit) | medium |
| Wanzenwanzen | Lygus spp. | Deformierte Blätter | leaf, shoot | vegetative | difficult |
| Schnecken | Arion spp. | Fraß an Jungpflanzen | leaf | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag, v.a. oben | Trockenheit + Wärme | 5–10 | vegetative, flowering |
| Grauschimmel | fungal (Botrytis cinerea) | Grau-brauner Schimmel | Feuchtigkeit, enge Pflanzung | 3–7 | seedling, dormancy |
| Salbei-Rost | fungal (Puccinia labiatarum) | Orange-braune Pusteln | Feuchtigkeit | 7–14 | vegetative, flowering |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0,5% Sprühlösung | 3 | Spinnmilben, Mehltau |
| Schnittmaßnahmen | cultural | — | Befallene Triebe entfernen | 0 | Grauschimmel, Rost |
| Schwefelspritzung | chemical | Schwefel | 0,3–0,5% Lösung | 14 | Mehltau, Rost |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|--------------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 20–30/m², ggf. alle 2 Wochen wiederholen | ~2–3 Wochen |
| Raubmilbe | Neoseiulus (Amblyseius) californicus | Spinnmilbe (Tetranychus urticae) | 20–50/m² (präventiv geringer) | ~2–4 Wochen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphidoidea) | 1–10/m², 2–3× im Abstand von 7–10 Tagen | ~2–3 Wochen |
| Schlupfwespe | Aphidius colemani | Blattläuse (z.B. Myzus persicae, Aphis gossypii) | 0,5–1/m², 2–3× wöchentlich bis Mumienbildung | ~2–3 Wochen |

> Hinweis: Gegen Wanzen (Lygus spp.) und Schnecken gibt es keine etablierten kommerziellen Antagonisten dieser Tabelle; hier greifen kulturelle Maßnahmen (Kulturschutznetz, Schneckenkragen). Larvale Florfliegen (Chrysoperla carnea) und Marienkäfer ergänzen die Blattlausregulierung im Freiland.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | Mediterrane Kräuter (Lamiaceae) |
| Empfohlene Vorfrucht | Beliebig; kein spezieller Vorfrucht-Anspruch |
| Empfohlene Nachfrucht | Beliebig; Starkzehrer profitieren von Nährstoff-arm bleibendem Boden |
| Anbaupause (Jahre) | keine Beschränkung |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Möhre | Daucus carota | 0.8 | Abwehr der Möhrenfliege durch Salbei-Duft | `compatible_with` |
| Kohl | Brassica oleracea | 0.8 | Kohlweißling-Abwehr durch Salbei-Duft | `compatible_with` |
| Rosmarin | Salvia rosmarinus | 0.9 | Gleiche Familie; gleicher Standortbedarf | `compatible_with` |
| Thymian | Thymus vulgaris | 0.9 | Gleiche Standortbedürfnisse; Kräuterbeet | `compatible_with` |
| Tomate | Solanum lycopersicum | 0.7 | Schädlingsabwehr; Aromaförderung | `compatible_with` |
| Rose | Rosa spp. | 0.7 | Schädlingsabwehr durch Salbei-Duft | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Basilikum | Ocimum basilicum | Konkurrierende Aromastoffe; keine gegenseitige Förderung | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Fenchel hemmt Wachstum von Lamiaceae | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Salbei |
|-----|-------------------|-------------|--------------------------|
| Ziersalbei | Salvia officinalis 'Purpurascens' | Gleiche Art | Dekorativ; ähnliches Aroma |
| Ananas-Salbei | Salvia elegans | Gleiche Gattung | Fruchtiges Aroma; nur Balkon/Topf |
| Oregano | Origanum vulgare | Gleiche Familie | Wärmeliebender; ähnliche Standortansprüche |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Salvia officinalis,"Echter Salbei;Küchensalbei;Common Sage;Garden Sage",Lamiaceae,Salvia,perennial,day_neutral,shrub,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Mittelmeerraum, Dalmatien",yes,8,20,80,70,45,limited,yes,false,false,light_feeder,hardy,"5;6;7;8;9","5;6;7",spring_pruning,"3;4"
```

---

## Quellenverzeichnis

1. [Compo Salbei](https://www.compo.de/ratgeber/pflanzen/kraeuter-obst-gemuese/salbei) — Anbau, Pflege, Düngung
2. [Samen.de Salbei](https://samen.de/blog/tipps-fuer-den-erfolgreichen-salbei-anbau.html) — Anbau-Praxis
3. [Gartenratgeber Salbei](https://www.gartenratgeber.net/pflanzen/salbei.html) — Pflege, Rückschnitt, Überwinterung
4. [Samen.de Begleitpflanzen Salbei](https://samen.de/blog/ideale-begleitpflanzen-fuer-salbei-im-kraeutergarten.html) — Mischkultur
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [NC State Extension — Salvia officinalis](https://plants.ces.ncsu.edu/plants/salvia-officinalis/) — Lichtbedarf (full sun/partial shade), Boden-pH 6.0–8.0, Drainage, kurzlebige Staude
6. [PFAF — Salvia officinalis](https://pfaf.org/user/Plant.aspx?LatinName=Salvia+officinalis) — Schatten („cannot grow in the shade"), pH-Vorzug neutral/alkalisch, Bodenfeuchte
7. [Wisconsin Horticulture — Sage (Salvia officinalis)](https://hort.extension.wisc.edu/articles/sage-salvia-officinalis/) — Lebensdauer 3–5 Jahre, Verholzung, immergrüner Halbstrauch
8. [Wikipedia — Salvia officinalis](https://en.wikipedia.org/wiki/Salvia_officinalis) — immergrüner Halbstrauch, Blütezeit Mai–Juli, C3-Lamiaceae
9. [Canadian Journal of Plant Science — Photosynthesis & low-light response of sage](https://cdnsciencepub.com/doi/10.4141/cjps-2014-010) — Lichtkompensationspunkt-Kontext, Photosynthese unter Schwachlicht
10. [Greg.app — Salvia temperature range](https://greg.app/salvia-temperature/) — optimale Photosynthese-Tagestemperatur 21–29°C
11. [ScienceDirect — Sage under salt stress (essential oil/fruits)](https://www.sciencedirect.com/science/article/abs/pii/S0926669009000867) — Salztoleranz bis ~10–12 dS/m
12. [Chem. Biol. Technol. Agric. — Salinity tolerance in S. officinalis](https://chembioagro.springeropen.com/articles/10.1186/s40538-021-00221-y) — Salzstress-Antwort, moderate Toleranz
13. [Buglogical — Phytoseiulus persimilis](https://www.buglogical.com/spider-mite-predator/phytoseiulus-persimilis/) — Ausbringrate Spinnmilben-Raubmilbe
14. [Sound Horticulture — Phytoseiulus persimilis Tech Sheet](https://soundhorticulture.com/pages/phytoseiulus-persimilis-spider-mite-predator) — Ausbringrate/Etablierung Spinnmilben-Raubmilbe
15. [Koppert — Aphidoletes aphidimyza](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/aphidoletes-aphidimyza/) — Blattlaus-Gallmücke, Ausbringrate/Etablierung
16. [Sound Horticulture — Aphidius colemani Tech Sheet](https://soundhorticulture.com/pages/aphidius-colemani-tech-sheet) — Blattlaus-Schlupfwespe, Ausbringrate
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor Audit 2026-07 -->
17. [RHS — Salvia officinalis (common sage)](https://www.rhs.org.uk/plants/16356/salvia-officinalis/details) — RHS-Hardiness-Rating H5 ("hardy in most places throughout the UK even in severe winters", -15 bis -10°C), Blütezeit early summer
18. [Missouri Botanical Garden — Salvia officinalis Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=m260) — USDA-Zone 4-8, Blütezeit late spring
19. [nachhaltigleben.ch — Salbei ernten: Fast ganzjährig im eigenen Garten anbauen](https://www.nachhaltigleben.ch/garten/salbei-ernten-fast-ganzjaehrig-im-eigenen-garten-anbauen-2502) — Haupt-Wachstum April–September, eingeschränkte Winterernte an frostfreien Tagen
20. [Kistengrün — Kann man frischen Salbei im Winter ernten?](https://www.kistengruen.de/wp/2019/11/salbei-im-winter-ernten/) — Winterernte nur sparsam/frostfrei, Pflanze zieht sich in Ruhemodus zurück
<!-- /Quelle: growing-phase-auditor Audit 2026-07 -->
