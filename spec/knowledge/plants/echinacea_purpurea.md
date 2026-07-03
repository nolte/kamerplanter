# Purpur-Sonnenhut — Echinacea purpurea

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Sonnenhut, Compo Purpur-Sonnenhut, Lubera Roter Sonnenhut, Naturadb Echinacea purpurea

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Echinacea purpurea | `species.scientific_name` |
| Volksnamen (DE/EN) | Purpur-Sonnenhut, Roter Sonnenhut; Purple Coneflower | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Echinacea | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> (Korrektur: E. purpurea ist botanisch ein Zwischentagspflanze/intermediate-day plant — Blüte ist bei 13–15 h am vollständigsten und wird bei langen Tagen (LD, ≥16 h, rot-defizitär) gehemmt; die Blühinduktion ist primär vernalisationsgesteuert, nicht photoperiodisch. Da das KA-Enum kein `intermediate_day` kennt, ist `day_neutral` der korrekte konservative Wert; der frühere Wert `long_day` widerspricht der Quellenlage [Runkle et al. 2001].) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis -40°C (USDA 3a); in Norddeutschland absolute Dauerfrosteignung; Pflanzenstängel als Winterschutz stehen lassen (auch Vogelfutter) | `species.hardiness_detail` |
| Heimat | Nordamerika (Präriegebiete) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> krautige Prärie-Staude der Asteraceae; C3-Stoffwechsel (keine Sukkulente/CAM, kein C4-Gras) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> Kein quellengesicherter Wuchs-/Phänologie-GDD-Basiswert für E. purpurea aus ≥2 unabhängigen seriösen Quellen auffindbar (verbreitete Forcing-Modelle wie FlowersOnTime nennen keinen publizierten species-spezifischen Base-Wert). Nicht aus Keim-/Kardinaltemperaturen umetikettiert. <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebensdauer (Jahre) | 3–5 (kultiviert; durch Teilung alle 3–4 Jahre verlängerbar; Wildexemplare deutlich älter) | `lifecycle_configs.typical_lifespan_years` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->Gardenia, Old Farmer's Almanac<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->winterruhende krautige Staude (oberirdisches Absterben, Austrieb aus der Wurzel im Frühjahr)<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation erforderlich (vernalization) | true (Kältereiz, chilling) — Mindest-Kältephase ca. 6–10 Wochen bei ~5 °C beschleunigt/fördert die Blüte; Erstjahrsblüte ohne Vernalisation unzuverlässig | `lifecycle_configs.vernalization_required` / `lifecycle_configs.vernalization_min_days` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->MSU Floriculture (Vernalization-Serie), Runkle et al. 2001<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | — (day_neutral im KA-Modell; botanisch Zwischentagspflanze mit Optimum 13–15 h, aber keine echte Kurz-/Langtag-Kardinallänge — daher kein KA-Wert) | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->Runkle et al. 2001 (Photocontrol of flowering, J. Amer. Soc. Hort. Sci.)<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 (Vorkultur Feb–Mär; Kältebehandlung (Stratifikation) 2–3 Wochen bei 5°C fördert Keimung) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6 (Direktsaat ab Mai nach Frostende; keine Stratifikation zwingend erforderlich, fördert aber die Keimung — Korrektur des früheren, unbelegten Zusatzes „März bis Juli", der weder mit dem Zahlenwert noch mit den Quellen übereinstimmte) <!-- Quelle: growing-phase-auditor 2026-07 --><!-- /Quelle: growing-phase-auditor 2026-07 --> | `species.direct_sow_months` |
| Erntemonate | 6, 7, 8, 9, 10 (Blüten; Wurzeln erst ab 3. Jahr ernten) <!-- Quelle: growing-phase-auditor 2026-07 --> (Korrektur: Blühbeginn und damit Blütenernte bereits ab Juni, nicht erst Juli — siehe Blütemonate) <!-- /Quelle: growing-phase-auditor 2026-07 --> | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 <!-- Quelle: growing-phase-auditor 2026-07 --> (Korrektur: War zuvor "7,8,9,10"; Blühbeginn liegt bei etablierten Pflanzen (ab 2. Standjahr) bereits im Juni, nicht erst im Juli — Missouri Botanical Garden „June to August", NC State Extension „June to August / early summer through mid-fall", Kiepenkerl „durchgehend ab Juni bis Herbst", hausgarten.net „Juni bis September" stimmen überein. RHS „midsummer to autumn" und Compo „Juli bis September" sind damit vereinbar (midsummer ≈ Ende Juni). Hinweis: Die Direktsaat (Mai/Juni, Jahr 1) überschneidet sich kalendarisch mit dem Junibeginn der Blüte etablierter Pflanzen — das ist bei dieser mehrjährigen Staude kein Widerspruch (Regel-3-Ausnahme): frisch gesäte Jungpflanzen blühen i. d. R. erst im 2. Jahr, während im selben Kalendermonat bereits ältere Bestandspflanzen blühen.) <!-- /Quelle: growing-phase-auditor 2026-07 --> | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division, cutting (Wurzelschnittlinge, Spätherbst–Frühwinter bzw. ab Ende Februar; Teilung Frühjahr/Herbst alle 3–4 Jahre) <!-- Quelle: growing-phase-auditor 2026-07 --> (Korrektur: Ergänzung von „cutting" (Wurzelschnittlinge) — fehlte zuvor, obwohl neben Aussaat und Teilung die dritte gängige Vermehrungsmethode für E. purpurea. Kein eigener `root_cutting`-Enum-Wert im KA-Modell vorhanden, daher generisches `cutting` gemäß `PropagationMethod`-Enum.) <!-- /Quelle: growing-phase-auditor 2026-07 --> | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — (Alkylamide und Polysaccharide = Wirkstoffe; Phytopharmakon) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Korbblütler-Kreuzallergie möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (bei Asteraceae-Allergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning (NIE im Herbst; Stängel als Überwinterungsschutz und Vogelfutter; Rückschnitt erst im März) | `species.pruning_type` |
| Rückschnitt-Monate | 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 20–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, durchlässige Gartenerde mit Kompost; pH 6,0–7,0; sandiger Lehm | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point, PPFD µmol/m²/s) min | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt (PPFD µmol/m²/s) max | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (gedeiht in voller Sonne; toleriert lichten Halbschatten, blüht dort aber schwächer) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–40 (Boden zur Pflanzung 30–38 cm / 12–15 in lockern; faseriges Wurzelwerk, kein tiefer Pfahlwurzel-Typ wie E. angustifolia) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (benötigt durchlässigen Boden; Wurzelfäule bei stehender Nässe — vgl. §5.2) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive (NaCl-Stressstudien zeigen Wachstums-/Photosyntheserückgang bereits bei moderater Salinität; im Artvergleich deutlich salzempfindlicher als E. angustifolia; Landschaftsbau-Listen führen die Art zwar trockenheitstolerant, jedoch nicht als ausgesprochen salztolerant — daher Maas-Hoffman-Klasse MS statt MT) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m; Maas-Hoffman a) | <!-- DATEN FEHLEN --> (kein quellengesicherter Maas-Hoffman-Schwellenwert für E. purpurea; vorhandene Studien testen NaCl-Konzentrationen ohne abgeleitete ECe-Schwelle) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m; Maas-Hoffman b) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.0 (harmonisiert mit §1.6 Substrat-Empfehlung) | `species.soil_ph_preference` |

Quellen: Missouri Botanical Garden Plant Finder; RHS; NC State Extension / NC State Salt-Tolerant-Plants-Liste; PubMed 27352527 (Salztoleranz-Studie); biorxiv 2022 (K⁺-Homöostase & Salztoleranz Echinacea).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 10–21 | 1 | false | false | medium |
| Sämling (1. Jahr) | 60–90 | 2 | false | false | medium |
| Vegetativ (2. Jahr+) | 42–70 | 3 | false | false | high |
| Blüte | 56–84 | 4 | false | true | high |
| Winterruhe | 120–180 | 5 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | day_neutral / kein Trigger <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> (Korrektur des früheren Werts „14–16": Blüte ist bei 13–15 h optimal und wird bei ≥16 h gehemmt — eine fixe 14–16-h-Vorgabe als Blüh-Trigger widerspricht der Quellenlage; Blühinduktion ist vernalisationsgesteuert, daher kein photoperiodischer Phasenübergangs-Trigger.) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photoperiod_hours` |
| VPD-Schwelle (kPa) | 1.8 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> (kritischer Punkt stomatären Kollaps, deutlich oberhalb des Ziel-Korridors 0.8–1.5; Oberkante 1.5 + ~0.3–0.5) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> (C3-Staude, keine Sukkulente/CAM) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> (warmgemäßigte C3-Sommerblüherin; deckt sich mit Tag-Temperatur-Optimum) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> (Freiland-Vollsonne-Anker nach Zhen & Bugbee; offenes Tageslicht/Vollsonne ≈ 0.5 bei R:FR ≈ 1.1 — Vollsonnen-Standort) <!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> | `requirement_profiles.far_red_fraction` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (trockenverträglich nach Etablierung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost | eigen | organisch | 3–5 L/m² | Frühjahr | Stauden allg. |
| Hornspäne | Oscorna | organisch-N | 30–50 g/m² | April | light_feeder |

### 3.2 Besondere Hinweise zur Düngung

Echinacea ist Schwachzehrer und gedeiht auf mäßig nährstoffreichen Böden (nach dem natürlichen Prärielebensraum). Auf zu fetten Böden wächst sie üppig, fällt aber öfter um und ist weniger kompakt. Jährliche Kompostgabe im Frühjahr reicht. Im ersten Jahr nach Pflanzung keine Düngung notwendig wenn Boden vorbereitet wurde.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Trockenverträglich nach Etablierung; junger Pflanzen im 1. Jahr regelmäßig gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 (1× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb–Mär | Vorkultur | Aussaat mit 2–4 Wochen Stratifikation (Kühlschrank) | mittel |
| Mär | Rückschnitt | Alte Stängel bodennah entfernen | mittel |
| Apr | Kompostgabe | 1–2 Handvoll Kompost pro Pflanze | niedrig |
| Mai–Jun | Auspflanzen | Sonniger bis halbschattiger Standort | hoch |
| Jul–Okt | Blüte genießen | Bienenpflanze; Samenstände als Vogelfutter | niedrig |
| Okt–Mär | Stängel stehen lassen | Überwinterungsstruktur + Vogelfutter (Körnerfresser) | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | — | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

Echinacea ist sehr robust und kaum von Schädlingen oder Krankheiten befallen.

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Gelegentlich kleine Kolonien | shoot | seedling (selten) | easy |
| Schmierläuse | Pseudococcidae | Wachsige Kolonien (sehr selten) | stem | vegetative | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit + Hitze | 5–10 | vegetative (selten) |
| Wurzelfäule | fungal | Welke; schwarze Wurzeln | Staunässe | 7–14 | seedling |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Schlupfwespe (parasitoid wasp) | Aphidius colemani | Blattläuse (Aphis spp.) | ~0,5–1 Tier/m² je Freilassung, mehrfach | ca. 2–3 Wochen |
| Gallmücke (predatory midge) | Aphidoletes aphidimyza | Blattläuse (Aphis spp.) | ~1–2 Larven/m² | ca. 2–3 Wochen |
| Marienkäfer (ladybird) | Adalia bipunctata / Hippodamia spp. | Blattläuse (Aphis spp.) | nach Befallsstärke (Eier/Larven) | ca. 1–2 Wochen |
| Australischer Marienkäfer / Mehlkäfer-Destroyer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcidae) | ~0,2–0,4 Käfer/m² (Freiland niedrig; Gewächshaus höher) | ca. 3–4 Wochen |

Hinweis: Nützling-Wirt-Zuordnung gilt für die in §5.1 gelisteten Schädlinge. Aphidius/Aphidoletes/Marienkäfer wirken gegen Blattläuse; Cryptolaemus montrouzieri ist der spezifische Gegenspieler von Schmier-/Wollläusen (Pseudococcidae) — nicht mit Schildlaus-Parasitoiden verwechseln. Echinacea blüht zudem als Nektar-/Pollenquelle und fördert natürlich vorkommende Blattlausräuber (Schwebfliegen, Florfliegen).

Quellen: RHS Aphid Predators; Koppert / UC IPM (Cryptolaemus montrouzieri); Evergreen Growers (Aphidius colemani/ervi).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Stauden (Asteraceae) |
| Empfohlene Vorfrucht | Beliebig; bevorzugt nährstoffarmer Standort |
| Empfohlene Nachfrucht | Beliebig |
| Anbaupause (Jahre) | Keine; Dauerstaude (8–10+ Jahre Standzeit) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rudbeckia | Rudbeckia fulgida | 0.9 | Gleiche Ökologie; optisch harmonisch | `compatible_with` |
| Fetthenne | Sedum spectabile | 0.8 | Bestäuber-Magnet; gleichzeitig Blütezeit | `compatible_with` |
| Astern | Aster spp. | 0.8 | Nachblüte; Spätsommerstaude | `compatible_with` |
| Gräser (Ziergräser) | Miscanthus, Pennisetum | 0.8 | Naturgarten-Charakter; Bodenbefestigung | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bienenweide; Trockenheit-tolerant | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Echinacea purpurea |
|-----|-------------------|-------------|--------------------------------------|
| Schmaler Sonnenhut | Echinacea angustifolia | Gleiche Gattung | Stärkere Heilwirkung; schmalere Blätter |
| Blasser Sonnenhut | Echinacea pallida | Gleiche Gattung | Hellrosa Blüten; etwas weniger robust |
| Sonnenauge | Rudbeckia fulgida | Gleiche Familie | Gelbe Blüten; früher blühend |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,harvest_months,bloom_months,pruning_type,pruning_months
Echinacea purpurea,"Purpur-Sonnenhut;Roter Sonnenhut;Purple Coneflower",Asteraceae,Echinacea,perennial,day_neutral,herb,fibrous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Nordamerika, Prärie",limited,25,30,120,60,45,no,limited,false,false,light_feeder,hardy,"6;7;8;9;10","6;7;8;9;10",spring_pruning,"3"
```

---

## Quellenverzeichnis

1. [Plantura Sonnenhut](https://www.plantura.garden/blumen-stauden/sonnenhut/sonnenhut-pflanzenportrait) — Pflege, Schnitt, Überwinterung
2. [Compo Purpur-Sonnenhut](https://www.compo.de/ratgeber/pflanzen/balkon-kuebelpflanzen/purpur-sonnenhut) — Anbau, Pflege
3. [Lubera Roter Sonnenhut](https://www.lubera.com/de/gartenbuch/roter-sonnenhut-echinacea-pflege-p2744) — Pflege, Verwendung
4. [Naturadb Echinacea purpurea](https://www.naturadb.de/pflanzen/echinacea-purpurea/) — Steckbrief, Eigenschaften
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Runkle et al. 2001 — Photocontrol of flowering and stem extension of the intermediate-day plant Echinacea purpurea (PubMed 11473702)](https://pubmed.ncbi.nlm.nih.gov/11473702/) — Photoperiod-Klassifikation (intermediate-day), Optimum 13–15 h, LD-Hemmung
6. [MSU Floriculture — Vernalization series](https://www.canr.msu.edu/resources/vernalization-part-3) — Vernalisation/Chilling-Bedarf, Forcing von Echinacea
7. [Missouri Botanical Garden — Echinacea purpurea Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=c580) — Sonne/Halbschatten, Boden, Trockenheit/Staunässe, Maße
8. [RHS — Echinacea purpurea](https://www.rhs.org.uk/plants/41568/echinacea-purpurea/details) — Standort, Boden-pH, Pflege
9. [NC State Extension — Echinacea purpurea Plant Toolbox](https://plants.ces.ncsu.edu/plants/echinacea-purpurea/) — Standort, Salztoleranz, Wuchsdaten
10. [PubMed 27352527 — Study on Salt Tolerance of Echinacea purpurea](https://pubmed.ncbi.nlm.nih.gov/27352527/) — Salzstress (NaCl-Konzentrationen), keine ECe-Schwelle
11. [bioRxiv 2022 — Potassium homeostasis and Echinacea salinity tolerance](https://www.biorxiv.org/content/10.1101/2022.10.10.511607.full.pdf) — Artvergleich Salztoleranz (purpurea salzempfindlicher als angustifolia)
12. [Gardenia — Echinacea (Coneflower) Grow & Care](https://www.gardenia.net/guide/echinacea-how-to-grow-and-care) — Lebensdauer, Teilung, Wurzeltiefe
13. [Old Farmer's Almanac — Coneflowers](https://www.almanac.com/plant/coneflowers) — Lebensdauer, Pflege, Wurzeltiefe
14. [RHS — Aphid Predators](https://www.rhs.org.uk/biodiversity/aphid-predators) — Nützlinge gegen Blattläuse
15. [Koppert / UC IPM — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Mehlkäfer-Destroyer, Ausbringrate gegen Schmierläuse
<!-- Quelle: growing-phase-auditor 2026-07 -->
16. [Kiepenkerl — Purpur-Sonnenhut Kulturanleitung](https://www.kiepenkerl.de/kulturanleitungen/purpur-sonnenhut/) — Aussaat, Blühbeginn ab Juni durchgehend bis Herbst
17. [Hausgarten.net — Roter Sonnenhut Pflege](https://www.hausgarten.net/pflanzen/staudenlexikon/roter-sonnenhut-pflege.html) — Blütezeit Juni–September, Vermehrung (Teilung, Aussaat, Wurzelschnittlinge)
18. [RHS — Echinacea purpurea Vermehrungshinweis](https://www.rhs.org.uk/plants/41568/echinacea-purpurea/details) — „Propagate by division in spring or autumn or by root cuttings from late autumn to early winter" (Wurzelschnittlinge)
19. [NC State Extension — Echinacea purpurea Plant Toolbox, Vermehrungsabschnitt](https://plants.ces.ncsu.edu/plants/echinacea-purpurea/) — Root Cutting als anerkannte Vermehrungsmethode
20. [Compo Purpur-Sonnenhut](https://www.compo.de/ratgeber/pflanzen/balkon-kuebelpflanzen/purpur-sonnenhut) — Direktsaat April–Mai (bereits als Quelle 2 gelistet, hier für Direktsaat-Zeitfenster referenziert)
<!-- /Quelle: growing-phase-auditor 2026-07 -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
