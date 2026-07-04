# Efeu — Hedera helix

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/english-ivy-hedera-helix-plant-care-growing-guide/), [Guide to Houseplants](https://www.guide-to-houseplants.com/english-ivy.html), [Soltech](https://soltech.com/products/english-ivy-care), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Hedera helix | `species.scientific_name` |
| Volksnamen (DE/EN) | Gewöhnlicher Efeu; English Ivy, Common Ivy | `species.common_names` |
| Familie | Araliaceae | `species.family` → `botanical_families.name` |
| Gattung | Hedera | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 30–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein belegter Wuchs-GDD-Basiswert; nur Photosynthese-Temperaturoptima publiziert (kein Keimwert als Wuchsbasis umetikettiert) | `species.base_temp` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | entfällt (vernalization_required=false) | `lifecycle_configs.vernalization_min_days` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | entfällt (day_neutral — kein Kurztag-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a, 4b, 5a, 5b, 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Sehr winterhart bis -25°C (USDA Zone 4). Als Zimmerpflanze jedoch kühlere Temperaturen bevorzugt (12–18°C). Zu warm macht die Pflanze anfällig für Spinnmilben. | `species.hardiness_detail` |
| Heimat | Europa, Westasien — Wälder, Felsen, Mauern | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.8 | `species.air_purification_score` |
| Entfernte Schadstoffe | benzene, formaldehyde, trichloroethylene, xylene, toluene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Hedera helix ist einer der effektivsten Luftreiniger unter den Zimmerpflanzen (NASA Clean Air Study 1989). Als Zimmerpflanze braucht er kühlere Temperaturen als die meisten tropischen Zimmerpflanzen — warme, trockene Zimmerluft schwächt die Pflanze und macht sie anfällig für Spinnmilben. Für Zimmerhaltung kühle, helle Fensterbänke (Nord-/Ostfenster). In warmen, trockenen Wohnräumen schwer zu halten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 9, 10 (nur bei adulter Kletterpflanze, selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (8–10 cm mit 3–4 Blättern) in Wasser oder feuchtem Substrat bewurzeln. Extrem zuverlässig. Bevorzugt kühlere Bewurzelungstemperatur (16–20°C).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, berries, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins (hederacoside C), falcarinol | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Falcarinol-Kontaktdermatitis bei empfindlichen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Herbst-Pollen allergisch für manche Personen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

**Hinweis:** Verträgt starken Rückschnitt sehr gut. Überlange Triebe im Frühjahr kürzen. Triebe können auf beliebige Länge zurückgeschnitten werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–100 (hängend) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–150+ (kletternd) | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (winterhart, bevorzugt kühle Standorte) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Standard-Einheitserde mit 20% Perlite. pH 6.0–7.5. Verträgt normale Gartenerde. Gute Drainage wichtig (keine Staunässe). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 40 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | deep_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN --> kein quantitativ belegter cm-Wert aus 2 Quellen (flach-faseriges Wurzelsystem, dazu Haftwurzeln zum Klettern) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> kein publizierter Maas-Hoffman-Schwellenwert (a) für H. helix | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein publizierter Maas-Hoffman-Slope (b) für H. helix | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweis:** Hedera helix ist ein ausgesprochener Schattenspezialist (deep_shade): wächst in tiefem Laubwald-Schatten, hat einen niedrigen Lichtkompensationspunkt (light compensation point, ca. 30 µmol/m²/s PAR nach Metcalfe 2005) und erreicht 90 % der Maximal-Photosynthese bereits bei ~360 µmol/m²/s. Sättigungs- und Photoinhibitions-Werte gehören NICHT in das Kompensationspunkt-Feld. Salztoleranz: Die Art besiedelt Küstensäume und Salzmarsch-Ränder und gilt als tolerant gegenüber Salzdeposition (Einstufung moderately_tolerant), jedoch ohne publizierte ECe-Schwellenwerte. Staunässe wird gemieden (sensitive). Der pH-Vorzug 6.0–7.5 ist harmonisiert mit §1.6 und §2.3; ökologisch besiedelt die Art ein breiteres Spektrum (selten unter pH 4).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (kühle Periode) | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 20–30 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.55–0.70 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (aktives Wachstum):** Die VPD-Schwelle (1.6 kPa) liegt deutlich oberhalb des VPD-Zielkorridors (Oberkante 1.2 kPa) und markiert den kritischen Punkt des stomatären Kollaps, nicht die Korridor-Oberkante. Photosynthese-Temperaturoptimum 20–30 °C (Bauer 1978; Net-Assimilation fällt unter ~20 °C und über ~30 °C ab). Far-Red-Fraction: Als Waldboden-/Unterwuchs-Spezialist wächst Efeu unter laubverschattetem Licht mit erhöhtem Far-Red-Anteil (höher als offenes Tageslicht ≈ 0.5; ein wirklich dichtes Blätterdach kann FR/(R+FR) noch weiter anheben). NICHT mit dem R:FR-Verhältnis verwechseln (invers).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 8–16 | `requirement_profiles.temperature_day_c` |
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-T_opt (°C) | 15–22 | `requirement_profiles.photosynthesis_temp_opt_c` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Far-Red-Fraction FR/(R+FR) | 0.55–0.70 | `requirement_profiles.far_red_fraction` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 60–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Winterruhe):** Niedrigere VPD-Schwelle (1.2 kPa) in der kühlen, feuchteliebenden Ruhephase; das frostgehärtete Blatt verschiebt das Photosynthese-Optimum nach unten (15–22 °C). Werte für DLI an die reduzierte Tageslänge und niedrige PPFD angepasst.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.5 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.5 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Phase Aktives Wachstum):**

| Mikronährstoff | Wert (ppm) | KA-Feld |
|----------------|------------|---------|
| Mangan (Mn) | <!-- DATEN FEHLEN --> kein H.-helix-spezifischer, doppelt belegter Wert | `nutrient_profiles.manganese_ppm` |
| Zink (Zn) | <!-- DATEN FEHLEN --> kein H.-helix-spezifischer, doppelt belegter Wert | `nutrient_profiles.zinc_ppm` |
| Kupfer (Cu) | <!-- DATEN FEHLEN --> kein H.-helix-spezifischer, doppelt belegter Wert | `nutrient_profiles.copper_ppm` |
| Molybdän (Mo) | <!-- DATEN FEHLEN --> kein H.-helix-spezifischer, doppelt belegter Wert | `nutrient_profiles.molybdenum_ppm` |

**Hinweis:** Für die Mikronährstoff-Sollwerte (Mn/Zn/Cu/Mo) liegen keine art-spezifischen, aus zwei unabhängigen seriösen Quellen belegten ppm-Werte für Hedera helix vor; generische Zierpflanzen-Vollnährlösungen (z. B. Hoagland-Spurenmix) decken den Bedarf des Leichtzehrers ab.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Leichter Zehrer — halbe bis normale Dosis ausreichend. Stickstoffbetonte Formel für dichtes Laub.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; kühl und gleichmäßig feucht halten — nicht austrocknen, nicht staunass | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | prune | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 5–15 (nur Topfkultur, die nicht ausgepflanzt bleibt) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, kühles Fenster (Nord-/Ostfenster); im Freiland keine Beschattung nötig | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam, nur bei Antrocknen; Ballen nicht völlig austrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Hedera helix ist im Freiland voll winterhart (hardy, USDA-Zone 4, bis ca. −25 °C) und benötigt ausgepflanzt KEINE Winterschutz-Maßnahme (winter_action=none). Frisch gepflanzte oder im Kübel exponierte Jungpflanzen profitieren von Wurzelschutz (Vlies/Mulch). Im Topf gehaltene Zimmer-/Balkonpflanzen überwintern am besten kühl (5–15 °C) und hell — Wärme schwächt sie und fördert Spinnmilben. Die Frühjahrs-Maßnahme ist der Rückschnitt (prune, vgl. §1.5, Februar/März). Einstufung hardy (nicht frost_free), da die Art im Freiland ohne Schutz frosthart ist.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, gelbe Punkte (besonders bei warmer, trockener Luft) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |
| Blattlaus | Aphididae | Kolonien, Honigtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Botrytis | fungal | Grauschimmel | Hohe Feuchtigkeit, schlechte Luftzirkulation |
| Echter Mehltau | fungal | Weißer Belag | Warme, feuchte Blätter |
| Wurzelfäule | fungal | Welke | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Kühler, feuchter Standort | cultural | Standort optimieren | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Sprühen | 0 Tage | Blattläuse, Schildläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Gemeine Spinnmilbe (Tetranychus urticae) | 10–50/m² (kurativ; 2–10/m² präventiv), 1–2× wöchentlich wiederholen | ca. 2–3 Wochen (Optimum 20–25 °C, > 70 % rF) |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10/m² je nach Befall | ca. 3–4 Wochen |
| Zehrwespe | Aphidius colemani | Blattläuse (Aphididae) | 0,25–4/m², mind. 3× im Abstand wiederholen | ca. 2–3 Wochen |
| Erzwespe | Metaphycus helvolus | Braune Weichschildlaus (Coccus hesperidum) | <!-- DATEN FEHLEN --> kein standardisierter m²-Wert; mehrfache Freilassungen üblich | ca. 4–6 Wochen |

**Hinweis:** Nützling-Wirt-Zuordnung fachlich getrennt: Phytoseiulus persimilis → Spinnmilben; Cryptolaemus montrouzieri → Schmierläuse; Aphidius colemani → Blattläuse; Metaphycus helvolus → Weichschildläuse (Coccidae, hier Coccus hesperidum, vgl. §5.1). Phytoseiulus ist bei der für Efeu typischen warm-trockenen Spinnmilben-Problematik nur bei ausreichender Luftfeuchte (> 70 % rF) erfolgreich — vorrangig bleibt die kulturelle Maßnahme (kühler, feuchter Standort, vgl. §5.3).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — Zimmerpflanze (kann im Outdoor als Bodendecker im Staudenbeet eingesetzt werden, dort gute Bodendeckung unter Gehölzen).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Großblättriger Efeu | Hedera canariensis | Gleiche Gattung | Größere Blätter, für wärmere Räume |
| Efeutute | Epipremnum aureum | Hängende Ranke | Verträgt Wärme besser |
| Syngonium | Syngonium podophyllum | Ähnlicher Wuchs | Wärmeliebender |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Hedera helix,"Gewöhnlicher Efeu;English Ivy;Common Ivy",Araliaceae,Hedera,perennial,day_neutral,vine,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b","Europa, Westasien",yes,2-8,15,30-100,40-150,yes,yes,false,light_feeder,0.8
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Goldheart,Hedera helix,"ornamental;variegated;yellow_center",clone
Glacier,Hedera helix,"ornamental;variegated;silver_white_green",clone
Green Ripple,Hedera helix,"ornamental;ruffled_leaves;compact",clone
Needlepoint,Hedera helix,"ornamental;narrow_leaves;compact",clone
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — English Ivy](https://www.healthyhouseplants.com/indoor-houseplants/english-ivy-hedera-helix-plant-care-growing-guide/) — Pflegehinweise, Schädlinge
2. [Guide to Houseplants — English Ivy](https://www.guide-to-houseplants.com/english-ivy.html) — Kulturdaten
3. [Soltech — English Ivy Care](https://soltech.com/products/english-ivy-care) — Lichtbedarf
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Metcalfe, D. J. (2005): Hedera helix L. — Biological Flora of the British Isles. Journal of Ecology 93:632–648](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/j.1365-2745.2005.01021.x) — Lichtkompensationspunkt (PAR 30 µmol/m²/s), Schattentoleranz, Boden-pH, Staunässe-Abneigung
6. [PFAF — Hedera helix Plant Database](https://pfaf.org/User/Plant.aspx?LatinName=Hedera+helix) — Schattentoleranz (full shade/deep woodland), Boden-pH, Frosthärte, Staunässe-Abneigung
7. [USDA Forest Service FEIS — Hedera helix](https://www.fs.usda.gov/database/feis/plants/vine/hedhel/all.html) — Vorkommen an Küstensäumen/Salzmarsch-Rändern (Salztoleranz-Einstufung), Winterhärte USDA-Zone 4
8. [Oregon State University Landscape Plants — Hedera helix](https://landscapeplants.oregonstate.edu/plants/hedera-helix) — Bodentoleranz (sauer/alkalisch), Standort, Salzdeposition-Toleranz
9. [Bauer, H. (1978): Photosynthesis of Ivy Leaves (Hedera helix) after Heat Stress — Physiologia Plantarum 44:400–406](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1399-3054.1978.tb01645.x) — Photosynthese-Temperaturoptimum (~20–30 °C, Referenz 25 °C); C3-Pathway
10. [Cornell NYSIPM Biocontrol Fact Sheet — Phytoseiulus persimilis](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate Raubmilbe gegen Spinnmilbe
11. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate & Etablierungsbedingungen (Temperatur/Luftfeuchte)
12. [Koppert — Aphidius colemani](https://www.koppertus.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Ausbringrate Zehrwespe gegen Blattläuse
13. [Lucidcentral / Pacific Pests — Cryptolaemus montrouzieri (Biocontrol 395)](https://apps.lucidcentral.org/ppp/text/web_full/entities/biocontrol__cryptolaemus_montrouzieri_395.htm) — Ausbringung Marienkäfer gegen Schmierläuse
14. [Metaphycus helvolus — Wikipedia (parasitises Coccus hesperidum)](https://en.wikipedia.org/wiki/Metaphycus_helvolus) — Wirt-Zuordnung Erzwespe → Braune Weichschildlaus
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
