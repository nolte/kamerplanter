# Federspargel (Plumosafarn) — Asparagus setaceus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Asparagus setaceus](https://www.gardenia.net/plant/asparagus-setaceus-asparagus-fern-grow-care-tips), [NC State Extension – Asparagus setaceus](https://plants.ces.ncsu.edu/plants/asparagus-setaceus/), [Leafyplace – Plumosa Fern](https://leafyplace.com/asparagus-plumosa-fern/), [Plantura – Zierspargel](https://www.plantura.garden/zimmerpflanzen/zierspargel/zierspargel-pflanzenportait)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Asparagus setaceus | `species.scientific_name` |
| Volksnamen (DE/EN) | Federspargel, Zierspargel, Plumosa-Farn; Asparagus Fern, Lace Fern, Plumosa Fern | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Asparagus | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | vine | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender <!-- Quelle: growing-phase-auditor 2026-07: Korrektur von half_hardy → tender; NC State Extension taggt die Art explizit "frost tender", Missouri Botanical Garden: "Intolerant of frost, with plants dying to the ground in light freezes", Plantura: "meist nicht winterhart", Schadschwelle bereits knapp über 10 °C (healthyhouseplants.com: Schäden unter 13 °C/55 °F) --> | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostintolerant — stirbt bereits bei leichten Frösten oberirdisch ab; Kälteschäden treten schon knapp über 10 °C auf, kein belastbarer Frosttoleranz-Nachweis für kurze Fröste <!-- Quelle: growing-phase-auditor 2026-07: Korrektur — vormalige Angabe "bis -3°C kurz tolerierend" widersprach 3 unabhängigen Quellen (s.o.) --> | `species.hardiness_detail` |
| Heimat | Südafrika (Ost-Kap, KwaZulu-Natal) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | 10–15 (bei optimaler Pflege bis zu mehreren Jahrzehnten) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false <!-- Quelle: growing-phase-auditor 2026-07: Korrektur von true → false; NC State Extension/healthyhouseplants.com: "does not have a true dormancy period, may slow growth in winter", Missouri Botanical Garden: Pflanze "appreciates a resting period" (fakultativ, nicht obligat), Plantura: "keine vollständige Dormanz" — nur reduzierte Aktivität, keine erzwungene Ruhephase --> | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht erforderlich) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (day_neutral, kein Photoperiodismus der Blüte) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Hinweis:** Trotz des Namens "Farn" ist Asparagus setaceus kein echter Farn, sondern ein Verwandter des Speisespargels (Asparagus officinalis). Die federartigen Blätter sind reduzierte Phyllokladien (umgewandelte Stängel).

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Physiologie):** Die Gattung *Asparagus* betreibt C3-Photosynthese — der CO₂-Kompensationspunkt der Phyllokladien-/Kladophyll-Mesophyllzellen reagiert klassisch C3-typisch auf O₂ und Temperatur (Photorespiration vorhanden), belegt für *A. officinalis* und *A. sprengeri* (kongenerisch zu *A. setaceus*); die CAM-Evolution innerhalb der Asparagaceae beschränkt sich auf die Unterfamilie Agavoideae, nicht auf *Asparagus*. Die GDD-Basistemperatur von ~10 °C spiegelt die wärmeliebende, subtropisch-tropische Herkunft (Optimum 15–24 °C, Wachstumsstopp unter ~10 °C) wider und ist bewusst höher als die ~4,5 °C des kühlliebenden Speisespargels. Die "Winterruhe" ist eine fakultative, durch sinkende Temperatur/Licht ausgelöste Quieszenz OHNE echte, obligate Dormanzphase (daher dormancy_required=false — Korrektur 2026-07, s. §1.1-Tabelle; ebenso vernalization_required=false; tropische Pflanze ohne Chilling-Anspruch). Die Pflanze verlangsamt lediglich ihr Wachstum bei sinkenden Temperaturen/Licht, benötigt aber keine erzwungene Ruhephase zum Wiederaustrieb.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (kleine weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Beeren (rot, wenn reif) — führen zu Erbrechen, Durchfall | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Saponine, Asparagin | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 (kletternd bis 300 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut drainierte Zimmerpflanzenerde; leicht sauer (pH 6.0–6.5); hohe Luftfeuchtigkeit wichtig | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | — <!-- DATEN FEHLEN: kein artspezifischer Messwert in 2 unabhängigen Quellen --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | — <!-- DATEN FEHLEN: kein artspezifischer Messwert in 2 unabhängigen Quellen --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | — <!-- DATEN FEHLEN: kein artspezifischer Wurzeltiefen-Messwert; fleischige Knollenwurzeln, Mindest-Topftiefe 15 cm --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | — <!-- DATEN FEHLEN: kein artspezifischer Maas-Hoffman-Wert für A. setaceus (4,1 dS/m gilt für A. officinalis, nicht übertragbar) --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN: kein artspezifischer Maas-Hoffman-Wert für A. setaceus --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** *A. setaceus* gedeiht im natürlichen Verbreitungsgebiet in halbschattiger bis lichtschattiger Lage (dappled/partial shade) und ist gegenüber direkter Mittagssonne empfindlich (Verbrennungsgefahr der Phyllokladien). Die fleischigen Knollenwurzeln speichern Wasser, reagieren aber empfindlich auf Staunässe und Überwässerung (Wurzelfäule). Die Pflanze ist salzempfindlich: weiches, kalkarmes Gießwasser wird bevorzugt, und Düngesalz-Akkumulation im Substrat führt zu Nadelbräune — daher Klasse `sensitive`. Quantitative Maas-Hoffman-Salztoleranzwerte (ECe-Schwelle ~4,1 dS/m) existieren nur für den Speisespargel *A. officinalis* und sind auf die Zierart NICHT übertragbar. Der Boden-pH-Vorzug 6.0–6.5 ist mit §1.6 (Substrat-Empfehlung) und §2.3 (Nährstoffprofile) harmonisiert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 21–42 | 1 | false | false | low |
| Vegetativ (Wachstum) | 180–270 | 2 | false | false | medium |
| Blüte | 30–60 | 3 | false | false | medium |
| Winterruhe | 90–120 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–350 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.55 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–10 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 14–16 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.55 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Etablierung | 1:1:1 | 0.5–0.8 | 6.0–6.5 | 80 | 40 | — | 1 | 0.25 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 | 0.5 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.1 | 0.05 | 0.02 |
| Blüte | 1:1:2 | 0.8–1.2 | 6.0–6.5 | 80 | 40 | — | 1 | 0.25 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Für *A. setaceus* existieren keine artspezifischen Mikronährstoff-Sollwerte. Die angegebenen Mangan- (Mn), Zink- (Zn), Kupfer- (Cu) und Molybdän-Werte (Mo) sind allgemeine Nährlösungs-Zielkonzentrationen für eine Pflanze mittleren Nährstoffbedarfs (medium_feeder), abgeleitet aus der Hoagland-Standardrezeptur (Mn 0,5 / Zn 0,05 / Cu 0,02 / Mo 0,01 ppm) und gängigen Mittelwerten kommerzieller Fertigation (Mn ~0,38 / Zn ~0,25 / Cu ~0,08 / Mo ~0,05 ppm). Für die Wachstumsphase (Vegetativ) gelten die höheren, für die reizärmeren Phasen (Etablierung, Blüte) die niedrigeren Werte; in der Winterruhe keine Düngung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 21–42 Tage | Neue Triebe |
| Vegetativ → Blüte | time_based | 180–270 Tage | Kleine Blüten erscheinen |
| Blüte → Winterruhe | time_based | 30–60 Tage | Herbst, Temperatursenkung |
| Winterruhe → Vegetativ | time_based | 90–120 Tage | Frühjahrsaustrieb |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Zimmerpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ, blüte |
| Balanced Fertilizer | Miracle-Gro | base | 10-10-10 | halbe Dosis | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Pflanzenerde mit Guano | Plagron | organisch | Beimischen 20% | Frühjahr | medium_feeder |
| Wormcast-Dünger | — | organisch | 1 TL/Topf | Apr–Sep | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Hinweise |
|-------|-------|---------|-----|----------|
| 1–3 | Etablierung | 0.5–0.8 | 6.2 | Hälfte der Normaldosis |
| 4–26 | Vegetativ | 1.0–1.5 | 6.2 | Alle 2–4 Wochen |
| 27–34 | Blüte | 0.8–1.2 | 6.2 | Normale Düngung |
| Nov–Feb | Winterruhe | 0.0 | — | Kein Dünger |

### 3.3 Besondere Hinweise zur Düngung

Hohe Luftfeuchtigkeit ist für Asparagus setaceus wichtiger als Düngung. Trockene Raumluft (unter 40%) führt zu gelbem Nadeln (Phyllokladien)-Abfall — das häufigste Problem. Regelmäßiges Besprühen oder ein Luftbefeuchter sind die wichtigste Maßnahme.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt; regelmäßig besprühen für Luftfeuchtigkeit | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Kühler Standort, wenig gießen | niedrig |
| Mär | Umtopfen | Rhizome teilen, frisches Substrat | hoch |
| Apr | Düngung | Wachstum beginnt, erste Düngung | hoch |
| Mai–Sep | Wachstum | Regelmäßig gießen, besprühen, düngen | hoch |
| Okt | Einwintern | Gießen reduzieren, kühleren Standort suchen | mittel |
| Nov–Dez | Ruhephase | Minimal gießen, kein Dünger | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free <!-- Quelle: Steckbrief-Erweiterung 2026-06: Korrektur von needs_protection → frost_free; frostempfindliche Kübel-/Zimmerpflanze, die frostfrei drinnen (8–15 °C) überwintert, vgl. winter_action=move_indoors --> | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Gelbe Nadeln, feine Gespinste | leaf | alle | medium |
| Blattläuse | Aphis spp. | Junge Triebe verformt | stem | vegetative | easy |
| Trauermücken | Sciara spp. | Larven im feuchten Substrat | root | alle | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Gelbe Nadeln, schlaffe Pflanze | overwatering | 7–14 | alle |
| Nadelfall | physiological | Massenhafter Abfall grüner Nadeln | dry_air, drought | — | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Steinernema feltiae | Trauermückenlarven | 0.5 Mio./m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Besprühen | cultural | Wasser | Täglich besprühen | 0 | Spinnmilben, Nadelfall |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Spinnmilben, Blattläuse |
| Gelbes Klebeband | mechanical | — | Aufhängen | 0 | Trauermücken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Farne | Nephrolepis exaltata | 0.8 | Ähnliche Licht- und Feuchte-Anforderungen | `compatible_with` |
| Tradescantia | Tradescantia zebrina | 0.7 | Ähnliche Feuchte-Toleranz | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Asparagus setaceus |
|-----|-------------------|-------------|------------------------------|
| Sprengerspargel | Asparagus densiflorus 'Sprengeri' | Gleiche Gattung | Robuster, weniger Luftfeuchte nötig |
| Sichelfarn | Asparagus falcatus | Gleiche Gattung | Größere Blätter, anspruchsloser |
| Nephrolepis | Nephrolepis exaltata | Echter Farn | Echter Farn, mehr Volumen |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,photosynthesis_type,base_temp,shade_tolerance,waterlogging_tolerance,salt_tolerance_class,soil_ph_preference
Asparagus setaceus,Federspargel;Plumosa-Farn;Asparagus Fern,Asparagaceae,Asparagus,perennial,day_neutral,vine,rhizomatous,9a;9b;10a;10b;11a;11b,0.0,Südafrika Ostkap,yes,7,15,60,60,—,yes,limited,false,true,c3,10,partial_shade,sensitive,sensitive,6.0-6.5
```
<!-- Quelle: Steckbrief-Erweiterung 2026-06: CSV um photosynthesis_type, base_temp, shade_tolerance, waterlogging_tolerance, salt_tolerance_class, soil_ph_preference erweitert -->

---

## Quellenverzeichnis

1. [Gardenia.net – Asparagus setaceus](https://www.gardenia.net/plant/asparagus-setaceus-asparagus-fern-grow-care-tips) — Vollständige Pflegeanleitung
2. [NC State Extension – Asparagus setaceus](https://plants.ces.ncsu.edu/plants/asparagus-setaceus/) — Wissenschaftliche Grundlagen
3. [Leafyplace – Plumosa Fern](https://leafyplace.com/asparagus-plumosa-fern/) — Detaillierter Care Guide
4. [Plantura – Zierspargel](https://www.plantura.garden/zimmerpflanzen/zierspargel/zierspargel-pflanzenportait) — Deutschsprachige Pflege
5. [Pflanzenfreunde – Asparagus](https://www.pflanzenfreunde.com/asparagus-zierspargel.htm) — Kulturtipps
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Plant Physiology / Oxford Academic – Effect of pH, O₂, and Temperature on the CO₂ Compensation Point of Isolated Asparagus Mesophyll Cells](https://academic.oup.com/plphys/article/83/1/113/6084028) — Beleg C3-Photosynthese der Gattung Asparagus (CO₂-Kompensationspunkt-Verhalten); auch [PMC1056307](https://pmc.ncbi.nlm.nih.gov/articles/PMC1056307/)
7. [Planta / Springer – Photosynthetic characteristics of mesophyll cells isolated from cladophylls of Asparagus officinalis](https://link.springer.com/article/10.1007/BF01369773) — C3-typische Photosynthese-Charakteristik der Kladophylle
8. [Annals of Botany / Oxford – The Agavoideae: an emergent model clade for CAM evolutionary biology](https://academic.oup.com/aob/article/132/4/727/7164427) — CAM-Evolution in Asparagaceae beschränkt auf Agavoideae (nicht Asparagus)
9. [NC State Extension – Asparagus setaceus (Cultural Conditions)](https://plants.ces.ncsu.edu/plants/asparagus-setaceus/) — Schattentoleranz (dappled/partial shade), pH, Knollenwurzeln
10. [Cafe Planta – The Lifespan of Asparagus Fern](https://cafeplanta.com/a/blog/the-lifespan-of-asparagus-fern-a-comprehensive-guide) — Lebensdauer 10–15 Jahre indoor
11. [Greg.app – Good Temperature Range for Your Asparagus](https://greg.app/asparagus-temperature/) und [Cafe Planta – Asparagus Fern Cold Tolerance](https://cafeplanta.com/blogs/resources/asparagus-fern-cold-tolerance) — Wärmeoptimum 15–24 °C, Kälteempfindlichkeit unter 10 °C (Basis GDD ~10 °C)
12. [Plantiary – Asparagus setaceus Care Guide](https://plantiary.com/plant/asparagus-setaceus_3275.html) und [Cafe Planta – Asparagus Fern Root Rot](https://cafeplanta.com/blogs/resources/asparagus-fern-root-rot) — Staunässe-Empfindlichkeit, Wurzelfäule bei Überwässerung
13. [Wikipedia – Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) und [Dickson 2018, NEGC – Managing nutrient solutions for hydroponic crops](https://www.negreenhouse.org/uploads/9/4/8/2/94821076/dickson_2018_negc_nutrient_and_ph_for_hydroponics.pdf) — Mikronährstoff-Zielkonzentrationen Mn/Zn/Cu/Mo
14. [New Phytologist (Zhen et al. 2022) – Photosynthesis in sun and shade: far-red photons](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.18375) und [Greenhouse Product News – The R:FR Ratio](https://gpnmag.com/article/r-fr-ratio/) — Tageslicht-FR-Fraktion ≈ 0,5; niedrigeres R:FR im Schatten/Unterwuchs
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor Audit 2026-07 -->
15. [Missouri Botanical Garden – Plant Finder: Asparagus setaceus](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b629) — Frostintoleranz ("dying to the ground in light freezes"), Blütezeit Sommer, USDA 9–12
16. [NC State Extension – Asparagus setaceus (Taxonomy Tags)](https://plants.ces.ncsu.edu/plants/asparagus-setaceus/) — Tag "frost tender"; Blüte unscheinbar, Sommer
17. [Healthy Houseplants – Asparagus Fern Complete Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/asparagus-fern-a-complete-care-guide/) — keine echte Dormanz, nur Wachstumsverlangsamung; Kälteschäden unter 13 °C (55 °F)
18. [Plantura – Zierspargel Pflanzenportrait](https://www.plantura.garden/zimmerpflanzen/zierspargel/zierspargel-pflanzenportait) — "meist nicht winterhart", keine vollständige Dormanz, Umzugsschwelle ~15 °C
<!-- /Quelle: growing-phase-auditor Audit 2026-07 -->
