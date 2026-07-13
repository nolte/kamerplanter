# Stachelbeere — Ribes uva-crispa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Ribes uva-crispa, Plantura Stachelbeeren-Düngung, Floragard Ribes uva-crispa, RHS Gooseberry

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ribes uva-crispa | `species.scientific_name` |
| Volksnamen (DE/EN) | Stachelbeere, Stachelbeerstrauch; Gooseberry | `species.common_names` |
| Familie | Grossulariaceae | `species.family` → `botanical_families.name` |
| Gattung | Ribes | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (ausdauernd, blüht wiederholt über mehrere Jahre) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; Blüten frostempfindlich (Spätfröste problematisch); Norddeutschland geeignet | `species.hardiness_detail` |
| Heimat | Europa, Nordafrika, Kaukasus | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein quellenbelegter Wuchs-GDD-Basiswert für Ribes uva-crispa auffindbar; Chilling-/Floral-Initiation-Temperaturen aus Heide & Sønsteby sind KEINE Wuchs-GDD-Basis --> | `species.base_temp` |
| Lebensdauer (Jahre) | 15–30 (produktiv 10–20, Strauch gesamt 30+) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation/Kältebedarf erforderlich | true (chilling/Endodormanz-Bruch, 800–1000 Chill Hours; KEINE klassische Vernalisation) | `lifecycle_configs.vernalization_required` |
| Mindest-Kältetage (chilling) | <!-- DATEN FEHLEN: Bedarf in Chill Hours (800–1000 h) belegt, aber kein quellenbelegter Tageswert --> | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 15–16 (obligater Kurztag-Blüher; Floral-Initiation unter kritischer Photoperiode) | `lifecycle_configs.critical_day_length_hours` |
| Bestäuber erforderlich (requires pollinator) | false | `species.requires_pollinator` |
| Kreuzbefruchtungsgruppe (pollinator group) | — (selbstfruchtbar; leer) | `species.pollinator_group` |
| Empfohlene Befruchter-Sorten | — (keine Befruchtersorte nötig; selbstfruchtbar) | `species.compatible_pollinators` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Bestäubung:** Ribes uva-crispa ist zwittrig und selbstfruchtbar — eine einzelne Pflanze trägt ohne Befruchtersorte. Insektenbestäubung (Bienen, Hummeln) verbessert jedoch Fruchtansatz, Fruchtgröße und Samenzahl spürbar; eine zweite Sorte kann den Ansatz weiter erhöhen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklingsvermehrung) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8 (je nach Sorte und Reife) | `species.harvest_months` |
| Blütemonate | 3, 4 (frühe Blüte; Spätfrostgefahr beachten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, layering | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (Früchte essbar) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Dornen! Schutzhandschuhe beim Ernten und Schneiden empfohlen. Sorte 'Captivator' und 'Hinnonmäki' nahezu dornenlos.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | winter_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Winterschnitt), 6 (Sommerschnitt zur Belüftung) | `species.pruning_months` |

**Schnittkonzept:** Erhaltungsschnitt: Nur 6–10 kräftige, gut verteilte Triebe stehen lassen. Äste über 4 Jahre alt entfernen. Jährlich 2–3 älteste Triebe bodennah herausnehmen; ebenso viele Jungtriebe als Ersatz stehen lassen. Offene Strauchform für bessere Belüftung (Mehltau-Prophylaxe).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 80–150 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–150 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 120–150 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, durchlässige Gartenerde; pH 6,0–6,5; leicht sauer; gute Drainage | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein Ribes-uva-crispa-spezifischer LCP-Messwert aus 2 Quellen auffindbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein Ribes-uva-crispa-spezifischer LCP-Messwert aus 2 Quellen auffindbar --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–40 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | <!-- DATEN FEHLEN: keine quantitative/eindeutige Salztoleranz-Einstufung für Ribes uva-crispa aus 2 Quellen auffindbar --> | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten für Ribes uva-crispa auffindbar --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: keine Maas-Hoffman-Daten für Ribes uva-crispa auffindbar --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis Standort:** Beste Erträge in voller Sonne; Halbschatten (z. B. unter lichten Obstbäumen, Nordwand) wird vertragen — daher `partial_shade`. Wurzelsystem fibrös und flach (Hauptmasse 20–40 cm), dadurch nicht trockenheitsfest und auf gleichmäßige Feuchte angewiesen, gleichzeitig staunässeempfindlich (gute Drainage bzw. Hochbeet bei schweren Böden). Der pH-Vorzug 6,0–7,0 umschließt das engere Düngeplan-Optimum 6,0–6,5 aus §1.6/§2.3; schwach alkalische (kalkhaltige) Böden werden noch toleriert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzelung (Steckling) | 42–60 | 1 | false | false | low |
| Jungpflanze (1.–2. Jahr) | 365–730 | 2 | false | false | medium |
| Blüte (Frühjahr) | 14–21 | 3 | false | false | low |
| Fruchtentwicklung | 60–90 | 4 | false | true | medium |
| Ernte | 14–28 | 5 | false | true | high |
| Sommerruhe & Rückschnitt | 30–60 | 6 | false | false | high |
| Winterruhe | 90–120 | 7 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Fruchtentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (kritischer Punkt stomatären Kollaps; Zieloberkante 1.4 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 (kühl-temperates Laubgehölz; C3) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland/Vollsonne; R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 2000–5000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Photoperiode/Blühinduktion:** `photoperiod_type = short_day`. Ribes uva-crispa ist ein obligater Kurztag-Blüher: Die Blütenanlage (floral initiation) wird im Spätsommer ausgelöst, wenn die Tageslänge unter die kritische Photoperiode von ~15–16 h fällt; die Blüte erscheint im Folgejahr nach Kältebruch (Endodormanz). Der oben gelistete `photoperiod_hours`-Wert von 14–16 h ist die Umgebungs-Tageslänge während der sommerlichen Fruchtentwicklung und steht nicht im Widerspruch zur Kurztag-Einstufung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Jungpflanze | 2:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | – | 2 | 0.5 | 0.05 | 0.05 | 0.05 |
| Blüte | 1:2:2 | 1.0–1.4 | 6.0–6.5 | 120 | 50 | – | 2 | 0.5 | 0.05 | 0.05 | 0.05 |
| Fruchtentwicklung | 1:2:3 | 1.2–1.6 | 6.0–6.5 | 140 | 60 | – | 2 | 0.5 | 0.05 | 0.05 | 0.05 |
| Ernte/Reife | 0:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | – | 1 | 0.3 | 0.05 | 0.02 | 0.05 |
| Winterruhe | 0:0:1 | 0.4–0.6 | – | – | – | – | – | – | – | – | – |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo):** Lösungs-Zielkonzentrationen je Phase ergänzt (`nutrient_profiles.manganese_ppm` / `.zinc_ppm` / `.copper_ppm` / `.molybdenum_ppm`). Werte orientieren sich an modifizierter Hoagland-/Steiner-Beerennährlösung (Mn ~0,5; Zn ~0,05; Cu ~0,02–0,05; Mo ~0,05) und liegen im selben Lösungsmaßstab wie das bereits gelistete Fe (~2 ppm). In reifenden/ruhenden Phasen reduziert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland, bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Beerenobst-Dünger | Compo Bio | organisch | 60–80 g/m² | Februar, April | medium_feeder |
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März | N-Grundversorgung |
| Kompost | eigen | organisch | 3–4 L/m² | März, Oktober | Bodenverbesserung |
| Obstbaum-Langzeitdünger | Substral Osmocote | slow_release | 50 g/m² | April | medium_feeder |

#### Mineralisch (bei Mangel)

| Produkt | Marke | Typ | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----------|-----------------|--------|
| Kaliumsulfat | Kali&Salz | mineral | 30 g/m² | 1 | Herbst (Winterhärtung) |
| Traubendünger | Compo | mineral | nach Etikett | 1 | Fruchtentwicklung |

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| Februar (Vegetationsbeginn) | N-betont | Hornspäne + Kompost | je 60 g/m² + 3L/m² | Vor Austrieb |
| April (nach Blüte) | ausgewogen | Beerenobst-Dünger | 60 g/m² | Nach Blütenfall |
| Ende Juli | KEIN N | Kaliumsulfat | 30 g/m² | Letzter Dünger! |

### 3.3 Besondere Hinweise zur Düngung

Kein Stickstoff nach Ende Juli — fördert übermäßiges Triebwachstum auf Kosten der Holzreife und Winterhärte. Magnesium-Chlorose bei sandigen Böden möglich — Bittersalz (Magnesiumsulfat, 15 g/m²) im April. Frühjahrsdüngung VOR dem Austrieb — nicht wenn schon Blätter entfaltet.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 4.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; gleichmäßige Feuchtigkeit bei Fruchtentwicklung wichtig | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 (2–3× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 2–7 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Winterschnitt | Öffnende Strauchform; 6–10 Triebe; älteste 2–3 bodennah entfernen | hoch |
| Feb | Erste Düngung | Hornspäne + Kompost vor Austrieb | hoch |
| Mär–Apr | Frostschutz Blüte | Vlies bei Spätfrostwarnung (Blüte ab -1°C geschädigt) | hoch |
| Apr | Zweite Düngung | Nach Blüte; Beerenobstdünger | mittel |
| Jun | Sommerschnitt | Seitentriebe auf 5 Blätter einkürzen; Mehltauprophylaxe | mittel |
| Jun–Aug | Ernte | Früchte bei Weichheit; für Marmelade kurz vor Reife | hoch |
| Jul | Letzter Dünger | Kaliumsulfat; KEIN N mehr | mittel |
| Okt–Nov | Mulchen | Kompostdecke um den Strauch | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 2 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Stachelbeerblattwespe | Nematus ribesii | Kahlfraß durch grüne Larven | leaf | vegetative | easy |
| Johannisbeerblasenlaus | Cryptomyzus ribis | Rote Blattauftreibungen (Blasen) | leaf | spring | medium |
| Stachelbeer-Glasflügler | Synanthedon tipuliformis | Bohrgänge im Holz; Zweige welken | bark, shoot | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Amerikanischer Stachelbeermehltau | fungal (Podosphaera mors-uvae) | Weißgrauer Belag auf Trieben, Blättern, Früchten | warmes, feuchtes Wetter | 5–10 | vegetative, fruiting |
| Sternrußtau | fungal (Drepanopeziza ribis) | Kleine gelbe Flecken → Blattfall | Feuchtigkeit | 7–14 | vegetative |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Schlupfwespen (diverse) | Blattwespenlarven | natürlich fördern | – |
| Ohrwürmer | Blattläuse, Larven | Nisthilfen aufhängen | – |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Schwefel | biological | Schwefel | Stäuben/Spritzen ab Knospenaufbruch | 14 | Mehltau |
| Holzasche | cultural | K, Si | Oberflächliche Ausbringung | 0 | Mehltau (pilzhemmend) |
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattwespe, Blattläuse |
| Offene Strauchform | cultural | – | Jährlicher Auslichtungsschnitt | 0 | Mehltau (Luftzirkulation) |
| Resistente Sorten | cultural | – | 'Hinnonmäki', 'Invicta', 'Pax' (mehltautolerant) | 0 | Mehltau |

### 5.5 Resistente Sorten

| Sorte | Resistenz | Besonderheit |
|-------|-----------|-------------|
| Hinnonmäki Rot/Gelb | Mehltautolerant | Fast dornenlos; Norddeutschland geeignet |
| Pax | Mehltautolerant | Wenige Dornen; großfrüchtig |
| Captivator | Tolerant | Nahezu dornenlos |
| Resistenta | Mehltauresistent | Ertragreich; Norddeutschland geeignet |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Dauergehölz (Grossulariaceae) |
| Empfohlene Nachbarschaft | Von Knoblauch, Lavendel, Tagetes profitieren |
| Anbaupause (Jahre) | Keine Neupflanzung nach Stachelbeere/Johannisbeere: 3 Jahre Pause |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Knoblauch | Allium sativum | 0.8 | Schädlingsabwehr; soll Mehltau reduzieren | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Schädlingsabwehr; Bestäuber anlocken | `compatible_with` |
| Tagetes | Tagetes patula | 0.8 | Nematodenabwehr | `compatible_with` |
| Erdbeere | Fragaria x ananassa | 0.6 | Unterschiedliche Wurzeltiefe; nutzt Halbschatten unter Strauch | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Geteilte Bodenerkrankungen | mild | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathische Wirkung auf Ribes | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Ribes uva-crispa |
|-----|-------------------|-------------|--------------------------------------|
| Rote Johannisbeere | Ribes rubrum | Gleiche Gattung | Weniger Dornen; frühere Ernte; einfachere Pflege |
| Schwarze Johannisbeere | Ribes nigrum | Gleiche Gattung | Mehr Vitamine; intensiveres Aroma |
| Jostabeere | Ribes × nidigrolaria | Kreuzung | Dornenlos; mehltautolerant; großfrüchtig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Ribes uva-crispa,"Stachelbeere;Stachelbeerstrauch;Gooseberry",Grossulariaceae,Ribes,perennial,short_day,shrub,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"Europa, Nordafrika, Kaukasus",limited,40,40,150,150,130,no,limited,false,false,medium_feeder,false,hardy,"3;4"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,days_to_maturity,disease_resistances,seed_type
Hinnonmäki Rot,Ribes uva-crispa,,,"mehltautolerant;nahezu_dornenlos;mittelgroß",,,vegetatively_propagated
Hinnonmäki Gelb,Ribes uva-crispa,,,"mehltautolerant;nahezu_dornenlos;gelb",,,vegetatively_propagated
Captivator,Ribes uva-crispa,,,"nahezu_dornenlos;großfrüchtig",,,vegetatively_propagated
Resistenta,Ribes uva-crispa,,,"mehltauresistent;ertragreich",,,vegetatively_propagated
```

---

## Quellenverzeichnis

1. [Naturadb Ribes uva-crispa](https://www.naturadb.de/pflanzen/ribes-uva-crispa/) — Steckbrief, Standort
2. [Plantura Stachelbeeren düngen](https://www.plantura.garden/obst/stachelbeeren/stachelbeeren-duengen) — Düngung
3. [Floragard Ribes uva-crispa](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/beerenobst/ribes-uva-crispa) — Pflege, Schädlinge
4. [Gartendatenbank Ribes uva-crispa](http://www.gartendatenbank.de/wiki/ribes-uva_crispa) — Schnitt, Schädlinge, Krankheiten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Floral initiation in gooseberry (Ribes uva-crispa L.) and its control by daylength and temperature — Journal of Horticultural Science & Biotechnology (Tandfonline, 2021)](https://www.tandfonline.com/doi/full/10.1080/14620316.2021.2009743) — Kurztag-Einstufung (obligater short-day plant), kritische Photoperiode 15–16 h, Floral-Initiation-Temperaturen
6. [Chilling requirement of Ribes cultivars (PMC4285813)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4285813/) — Kältebedarf/Endodormanz-Bruch bei Ribes
7. [Deep Green Permaculture — Chill Hours for Currants and Gooseberries](https://deepgreenpermaculture.com/2024/10/05/the-essential-guide-to-chill-hours-for-growing-currants-and-gooseberries/) — Chilling 800–1000 Chill Hours
8. [USU Extension — Gooseberries in the Garden](https://extension.usu.edu/yardandgarden/research/gooseberries-in-the-garden) — pH 6.0–7.0, fibröse Flachwurzler, Halbschatten, Staunässe-Empfindlichkeit
9. [SDSU Extension — Gooseberry: How to Grow It](https://extension.sdstate.edu/gooseberry-how-grow-it) — Wurzeltiefe (Top 20–40 cm), Schattentoleranz, Bewässerung
10. [RHS — How to grow gooseberries](https://www.rhs.org.uk/fruit/gooseberries/grow-your-own) — Standort (volle Sonne/Halbschatten), Boden, keine Staunässe, pH
11. [UMN Extension — Growing currants and gooseberries in the home garden](https://extension.umn.edu/fruit/growing-currants-and-gooseberries-home-garden) — Selbstfruchtbarkeit, Insektenbestäubung, Produktivität/Lebensdauer
12. [Seeds of Diversity — Currants and Gooseberries (Pollination)](https://seeds.ca/pollinator/bestpractices/gooseberries.html) — Selbstfruchtbarkeit, Nutzen der Insektenbestäubung
13. [PSU Extension — Home Fruit Plantings: Gooseberries and Currants](https://extension.psu.edu/home-fruit-plantings-gooseberries-and-currants) — produktive Lebensdauer / Strauchalter
14. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Lösungskonzentrationen (Mn/Zn/Cu/Mo)
15. [Science in Hydroponics — Nutrient Solutions for Hydroponic Strawberry Production](https://scienceinhydroponics.com/2025/10/comparing-nutrient-solutions-for-hydroponic-strawberry-production.html) — Steiner-Beerennährlösung Mikronährstoff-Zielwerte
16. [Plants in Action 14.3.1 — Photosynthesis](https://rseco.org/content/1431-photosynthesis.html) — Photosynthese-Temperaturoptimum temperater C3-Gehölze (15–25 °C)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
