# Cattleya-Orchidee — Cattleya hybrida

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [American Orchid Society — Cattleya Culture Sheet](https://www.aos.org/orchid-care/care-sheets/cattleya-culture-sheet), [AOS — Cattleya Culture Part 1](https://www.aos.org/all-abour-orchids/cattleya-culture-part-1), [Smithsonian Gardens — Cattleya Care](https://gardens.si.edu/collections/plants/orchids/orchid-care-sheets/cattleya/), [Orchid Bliss — Cattleya](https://orchidbliss.com/cattleya/), [OrchidWeb](https://www.orchidweb.com/orchid-care/cattleya-alliance-orchid-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cattleya hybrida | `species.scientific_name` |
| Volksnamen (DE/EN) | Cattleya-Orchidee, Korsagen-Orchidee; Corsage Orchid, Queen of Orchids | `species.common_names` |
| Familie | Orchidaceae | `species.family` → `botanical_families.name` |
| Gattung | Cattleya | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 10°C Nacht; Temperaturabfall Tag/Nacht essentiell für Blühinduktion | `species.hardiness_detail` |
| Heimat | Mittel- und Südamerika (tropische Wälder, Epiphyt) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam (Crassulaceen-Säurestoffwechsel / crassulacean acid metabolism; nächtliche CO₂-Fixierung über PEPC, tagsüber Refixierung durch Rubisco — typische Wasserspar-Anpassung dickblättriger epiphytischer Orchideen, in *Cattleya walkeriana* als konstitutiver CAM belegt) | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> (GDD-Konzept für tropische CAM-Epiphyten nicht etabliert; Wachstum kommt unterhalb ca. 13–15 °C zum Stillstand, jedoch keine belegte GDD-Basistemperatur aus seriösen Quellen) | `species.base_temp` |
| Typische Lebensdauer (Jahre) | 20–50+ (perennierende sympodiale Orchidee; gut gepflegte Teilstücke leben Jahrzehnte) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false (keine echte Dormanz; nach der Blüte nur eine wachstumsärmere Ruheperiode mit reduzierter Bewässerung) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (kein Vernalisationsreiz im botanischen Sinne; Blüteninduktion bei vielen Hybriden über thermoperiodischen Kühlreiz — abgesenkte Nachttemperatur 10–13 °C — sowie sortenabhängig Tageslängensignal, nicht über Kältestratifikation) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | <!-- DATEN FEHLEN --> (entfällt, da keine Vernalisation; Kühlreiz-Dauer sortenabhängig, kein peer-reviewed Mindestwert) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> (tagesneutral als Standardannahme; einzelne Cattleya-Arten/-Hybriden reagieren kurztägig — z. B. *C. trianae* ~ 11 h —, ein allgemeingültiger Schwellenwert für die Sammelart *Cattleya hybrida* ist jedoch nicht belegt) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis zu Hybriden:** Cattleya hybrida umfasst Tausende eingetragener Hybriden, entstanden durch Kreuzungen innerhalb der Cattleya-Alliance (Cattleya, Laelia, Sophronitis, Rhynchlaelia u.a.). Blütezeit, Farbe und Größe variieren stark nach Sorte. Die hier beschriebenen Pflegewerte gelten für Standard-Zimmerkulturhybriden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | sortenabhängig; typisch 2, 3, 4, 10, 11 (Frühjahr/Herbst) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division; offset | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Teilung:** Bei größeren Exemplaren Rhizom mit scharfem, sterilem Messer zwischen den Pseudobulben teilen. Jeder Teil muss mindestens 3–4 Pseudobulben haben. Schnittstellen mit Holzkohlepulver oder Zimt bestäuben. Bewurzelung in Orchideensubstrat bei 22–25°C.

**Keiki:** Manche Hybriden bilden Keikis (Kindpflanzen) auf alten Pseudobulben. Erst trennen wenn eigene Wurzeln >3 cm vorhanden.

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

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | variabel (nach Blüte) | `species.pruning_months` |

**Hinweis:** Verblühten Blütenstiel an der Basis abschneiden. Ältere Pseudobulben (Backbulbs) können belassen werden — sie speichern Reservestoffe. Nur vollständig eingeschrumpfte Pseudobulben entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Grobes Orchideensubstrat: Kiefernrinde (Gr. 1–2 cm) + Perlit (30%) + Torfmoos (20%); pH 5.5–6.5; exzellente Drainage und Belüftung obligatorisch | — |

**Topfmaterial:** Terrakotta oder speziell gelochte Orchideentöpfe bevorzugt — fördert schnellere Austrocknung und optimale Wurzelbelüftung (Luftwurzeln benötigen Sauerstoff).

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (PPFD µmol/m²/s) | 10–25 (niedrig; als dickblättrige CAM-Pflanze positive Netto-CO₂-Bilanz schon bei sehr geringem Licht. Hinweis: getrennt davon liegt der für vitales Wachstum nötige Bereich deutlich höher — Sättigung ~ 300–600, Photoinhibition erst > 1650 µmol/m²/s; diese Sättigungswerte gehören NICHT in das Kompensationspunkt-Feld) | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | partial_shade (Hochlicht-Orchidee; verträgt deutlich mehr Licht als Phalaenopsis — in Florida/Hawaii nahezu Vollsonne, in Mitteleuropa 40–50 % Sonnenlicht/helles diffuses Licht. In der Natur unter dem oberen Kronendach an Innenästen, vor direkter Mittagssonne geschützt) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–20 (epiphytisch/lithophytisch; velamenbedeckte Luft- und Rindenwurzeln, keine echte Bodenwurzelung — auf das Topfvolumen begrenzt) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive (Wurzeln müssen zwischen den Wassergaben praktisch abtrocknen; vollgesogenes Velamen unterbindet den Gasaustausch und führt rasch zu Wurzelfäule) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive (salzempfindlich; Richtwert Gießwasser < 500 ppm bzw. ≤ 0,5 dS/m, andernfalls Wurzelspitzen-Verbrennung und Mineralkruste; regelmäßiges Spülen des Substrats nötig) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> (kein Maas-Hoffman-Substrat-ECe-Schwellenwert für epiphytische Orchideen etabliert; lediglich Praxis-Richtwert Gießwasser-EC ≤ 0,5 dS/m, kein peer-reviewed ECe-Threshold) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> (kein Maas-Hoffman-Slope für Cattleya publiziert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 (Substrat-pH der Orchideenrinde; leicht sauer — konsistent mit §1.6 und §2.3 derselben Datei) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung/Etablierung | 30–60 | 1 | false | false | low |
| Vegetativ (Pseudobulben-Aufbau) | 90–180 | 2 | false | false | medium |
| Winterruhe/Blüteinduktion | 42–60 | 3 | false | false | medium |
| Blüte | 21–60 | 4 | false | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 (kritische Obergrenze für stomatären Kollaps/Wasserstress; deutlich oberhalb des 1.5-Zielkorridors. Cattleya als dickblättrige CAM-Pflanze etwas robuster als dünnblättrige Orchideen) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (CAM-/sukkulenzähnliche dickblättrige Epiphyte mit hoher Wasserspeicherung in Pseudobulben und Blättern) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–29 (warmes vegetatives Tagesoptimum für CAM-Nettofixierung; deckt sich mit der empfohlenen Tagestemperatur 21–29 °C) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Referenz offenes Tageslicht; kein artspezifisch belegter abweichender Zielwert für die vegetative Phase) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 (nach Trocknungszyklus: gründlich gießen, dann vollständig abtrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe/Blüteinduktion

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–13 (kritisch für Blühinduktion!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (kritische Obergrenze; in der kühleren Induktionsphase niedriger angesetzt als vegetativ, da reduzierte Transpiration und Wassergabe) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (dickblättrige CAM-Pflanze; Pseudobulben puffern Trockenstress) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 (während der herbstlichen Kühlinduktion am Tag abgesenkt; CAM bleibt aktiv) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Referenz offenes Tageslicht; kein belegter abweichender Zielwert für die Induktionsphase) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 (kritische Obergrenze; offene Blüten zusätzlich austrocknungs- und Botrytis-gefährdet, daher unterhalb der vegetativen Schwelle) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (Laubblätter/Pseudobulben CAM-robust; einzelne offene Blüten empfindlicher, dies bleibt aber Freitext-Hinweis) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 (kühlere Blütephase) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Referenz offenes Tageslicht; kein belegter abweichender Zielwert für die Vollblüte) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–350 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Etablierung | 1:1:1 | 0.4–0.6 | 5.5–6.5 | 60 | 30 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Vegetativ | 3:1:2 | 0.6–1.2 | 5.5–6.5 | 100 | 50 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 5.5–6.5 | — | — | — | — | — | — |
| Blüte | 1:2:2 | 0.4–0.8 | 5.5–6.5 | 80 | 40 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

**"Schwach aber oft" Prinzip (weakly weekly):** Cattleyen bekommen am besten wöchentlich eine sehr schwache Düngelösung (1/4 der empfohlenen Dosis) anstatt monatlich eine starke Gabe.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Für *Cattleya* liegen keine belastbaren, phasenspezifischen Mikronährstoff-Sollwerte (ppm) aus mindestens zwei unabhängigen seriösen Quellen vor → als `<!-- DATEN FEHLEN -->` markiert. In der Praxis werden Mn, Zn, Cu, Mo (sowie Fe und B) über komplette Orchideen-Volldünger in chelatierter Form (EDTA für Mn/Zn/Cu) in sehr geringer Konzentration im Rahmen der „weakly weekly“-Verdünnung zugeführt; die Spanne zwischen Mangel und Toxizität ist eng, daher keine Schätzwerte.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Vegetativ → Winterruhe | seasonal | Oktober; Tagtemperatur sinkt; Nachttemperatur auf 10–13°C |
| Winterruhe → Blüte | conditional | Scheidenscheide sichtbar, aufquellend |
| Blüte → Vegetativ | event_based | Blüten verblüht |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Orchideen)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Orchideen-Dünger flüssig | Substral | Spezialdünger | 5-5-7 | 3 ml/L (1/4 Dosis) | 1 | Vegetativ |
| ProTek Orchid | Peters Professional | Orchideendünger | 20-20-20 | 0.5 g/L | 1 | Vegetativ |
| Cal-Mag | diverse | Supplement | — | 1 ml/L | 2 | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Fischhydrolysat (verdünnt) | Plagron | organisch | 0.5 ml/L | Wachstumsphase |

### 3.2 Besondere Hinweise zur Düngung

**Kein Dünger auf trockene Wurzeln:** Immer erst gründlich wässern, dann nach einigen Stunden dünn düngen. Trockene Wurzeln plus Düngelösung = Wurzelbrand.

**Flussprinzip:** Cattleyen in Töpfen müssen regelmäßig "gespült" werden (alle 3–4 Monate mit klarem Wasser durchfluten ohne Dünger), um Salze auszuwaschen. Salzanreicherung im Substrat schädigt Luftwurzeln.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies, zimmerwarmem Wasser (>20°C); Regenwasser, destilliertes Wasser oder RO-Wasser optimal; nie unter 15°C | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7 (sehr schwach) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Blüte (wenn induziert) | Blüten genießen; wenig Wasser; keine Dünger | mittel |
| Mär | Frühjahrs-Repot | Alle 2 Jahre umtopfen in frisches Substrat | mittel |
| Apr–Sep | Vegetative Phase | Regelmäßig gießen (trocknen lassen), wöchentlich schwach düngen | hoch |
| Okt | Blüteinduktion | Nachttemperatur auf 10–13°C senken; Gießen reduzieren; kein Dünger | hoch |
| Nov–Jan | Kühlphase | Nachttemperatur kalt; Blütenansatz beobachten | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors (frostempfindliche Kübel-/Zimmerpflanze; falls im Sommer draußen, rechtzeitig vor Frost ins frostfreie, helle Quartier) | `overwintering_profiles.winter_action` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme Monat | 10 (Oktober; vor erstem Frost und passend zur Kühlinduktion) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors (nach den Eisheiligen ggf. wieder an geschützten, hellen Außenstandort; an direkte Sonne langsam gewöhnen) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Schildläuse | Coccoidea | Braune Schuppen, Honigtau | leaf, pseudobulb | medium |
| Wollläuse | Planococcus citri | Weiße Wollmasse, Honigtau | stem, root | easy |
| Thripse | Thysanoptera | Silbrige Streifung auf Blütenblättern | flower | medium |
| Schnecken | Gastropoda | Fraßspuren an Wurzeln und Trieben | root, new_growth | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Schwarzfäule | fungal (Phytophthora, Pythium) | Schwarze Flecken, Triebschwarzfärbung | Staunässe, kaltes Wasser |
| Blattflecken | fungal (Cercospora) | Gelbliche, eingesunkene Flecken | Hohe Feuchtigkeit + schlechte Belüftung |
| Viruserkrankungen | viral (ORSV, CymMV) | Mosaik-Muster auf Blättern, Blütenverfärbung | Kontaktübertragung durch Werkzeug |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wollläuse | 3–5 Tiere/Pflanze | 14–21 |
| Metaphycus helvolus | Schildläuse | 5–10 | 21–28 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | mechanical | Isopropylalkohol | Wattestäbchen | 0 | Schildläuse, Wollläuse |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Thripse, Schildläuse |
| Werkzeug sterilisieren | cultural | Isopropanol/Feuer | Nach jedem Schnitt | 0 | Virusübertragung |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Phalaenopsis | Phalaenopsis spp. | 0.6 | Gleiche Familie; etwas anderen Pflegeansprüchen | `compatible_with` |
| Dendrobium | Dendrobium nobile | 0.8 | Gleiche Familie; ähnliche Pflegebedingungen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sukkulenten | diverse | Cattleya braucht höhere Luftfeuchtigkeit | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Phalaenopsis | Phalaenopsis spp. | Gleiche Familie | Einfacher zu pflegen; länger blühend |
| Dendrobium | Dendrobium nobile | Gleiche Familie, ähnliche Blütenpracht | Verträgt trockenere Luft |
| Epidendrum | Epidendrum radicans | Gleiche Familie | Robuster, blüht öfter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Cattleya hybrida,Cattleya-Orchidee;Korsagen-Orchidee;Corsage Orchid,Orchidaceae,Cattleya,perennial,day_neutral,herb,aerial,10a;10b;11a;11b;12a;12b,0.0,"Mittel- und Südamerika",yes,3,15,60,60,yes,limited,true,true
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Pot Paradiso 'Free Spirit',Cattleya hybrida,compact;fragrant;purple_white,365,–,cultivar
Blc. Pamela Hetherington 'Coronation' FCC/AOS,Cattleya hybrida,award_winning;fragrant;yellow,365,–,cultivar
```

---

## Quellenverzeichnis

1. [American Orchid Society — Cattleya Culture Sheet](https://www.aos.org/orchid-care/care-sheets/cattleya-culture-sheet) — Grundlegende Kulturdaten
2. [AOS — Cattleya Culture Part 1](https://www.aos.org/all-abour-orchids/cattleya-culture-part-1) — Licht, Temperatur, PPFD
3. [Smithsonian Gardens — Cattleya Care](https://gardens.si.edu/collections/plants/orchids/orchid-care-sheets/cattleya/) — Pflegehinweise
4. [Orchid Bliss — Cattleya Guide](https://orchidbliss.com/cattleya/) — Blüteinduktion, Temperatur
5. [OrchidWeb — Cattleya Alliance Care](https://www.orchidweb.com/orchid-care/cattleya-alliance-orchid-care) — Schädlinge, Krankheiten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Silvera et al. — Crassulacean Acid Metabolism and Epiphytism Linked to Adaptive Radiations in the Orchidaceae (PMC2663729)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2663729/) — CAM-Photosynthese-Typ in Orchidaceae, *Cattleya walkeriana* als konstitutiver CAM
7. [Annals of Botany 112(1) 2013 — Spatial patterns of photosynthesis in thin- and thick-leaved epiphytic orchids: C3–CAM plasticity (PMC3690981)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3690981/) — CAM in dickblättrigen Orchideen, niedriger Lichtkompensationspunkt
8. [American Orchid Society — Cattleya Culture Part 1 (Licht/Temperatur)](https://www.aos.org/all-abour-orchids/cattleya-culture-part-1) — Hochlicht-Toleranz (40–50 % bis nahezu Vollsonne), Tag-/Nacht-Temperaturdifferenz, T_opt
9. [Slippertalk Orchid Forum — Cattleya/Catasetum PPFD & DLI Experiment](https://www.slippertalk.com/threads/experiment-on-light-levels-on-cattleya-and-catasetum-species-ppfd-and-dli.59750/) — PPFD/DLI-Bereiche, Photoinhibition > 1650 µmol/m²/s
10. [St. Augustine Orchid Society — Water Quality and Salt Stress](https://staugorchidsociety.org/PDF/200711Tips-WaterQuality.pdf) — Salzempfindlichkeit, Gießwasser < 500 ppm / ≤ 0,5 dS/m
11. [Besgrow Orchiata — Cattleya Growing Guide (PDF)](https://besgrow.com/wp-content/uploads/2018/06/Besgrow-Orchiata-Cattleya-growing-guide.pdf) — Staunässe-Empfindlichkeit, Velamen-Gasaustausch, Wurzelbelüftung
12. [UF/IFAS Extension Charlotte County — Cattleya Care](https://blogs.ifas.ufl.edu/charlotteco/2026/03/05/cattleya-hard-to-go-wrong-with-this-orchid/) — Salz-/Wasserqualität, leichte Düngung (~50 ppm N), Substrat
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
