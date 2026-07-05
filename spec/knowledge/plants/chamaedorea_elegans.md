# Stubenpalme — Chamaedorea elegans

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/chamaedorea-elegans-parlor-palm), [OurHouseplants](https://www.ourhouseplants.com/plants/parlour-palm), [Greenery Unlimited](https://greeneryunlimited.co/blogs/plant-care/neanthe-bella-palm-care), [Joy Us Garden](https://www.joyusgarden.com/neanthe-bella-palm-care-tips-for-this-table-top-palm/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Chamaedorea elegans | `species.scientific_name` |
| Volksnamen (DE/EN) | Stubenpalme, Bergpalme; Parlor Palm, Neanthe Bella Palm | `species.common_names` |
| Familie | Arecaceae | `species.family` → `botanical_families.name` |
| Gattung | Chamaedorea | `species.genus` |
| Ordnung | Arecales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 20–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–27°C. Verträgt normale Zimmertemperaturen sehr gut. | `species.hardiness_detail` |
| Heimat | Mexiko, Guatemala, Belize — tropische Bergregenwälder, Unterwuchs | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.6 | `species.air_purification_score` |
| Entfernte Schadstoffe | benzene, formaldehyde, trichloroethylene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Stubenpalme (Neanthe Bella) ist eine der wenigen echten Palmen, die auch bei weniger Licht gedeiht und damit ideal für Innenräume ist. NASA Clean Air Study bestätigt gute Luftreinigungseigenschaften. Wichtig: Palmen mögen keine drastischen Standortwechsel und sollten nicht von stark wechselnden Lichtverhältnissen ausgesetzt werden. Wächst sehr langsam.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 3, 4, 5 (gelbe Rispenkätzchen; bei adulten Pflanzen in Zimmerkultur möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Ausschließlich über Samen. Frische Samen (nicht älter als 3 Monate) bei 27–32°C und feuchtem Substrat. Keimung in 3–6 Monate. Kein vegetativer Vermehrungsweg. Im Handel erhältliche Pflanzen stammen aus Samen-Kultivierung.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Früchte/Fruchtsaft kann leichte Hautreizungen verursachen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Chamaedorea elegans ist NICHT giftig — ASPCA listet die Pflanze als sicher für Katzen, Hunde und Kinder.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Abgestorbene oder braune Wedel an der Basis entfernen. Niemals grüne Wedel schneiden — Palmen können nicht nachwachsen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (indoor, sehr langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–120 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige Palmenerde oder Einheitserde mit 20% Perlite + 10% Sand. pH 6.0–7.0. Gute Drainage unerlässlich. Nie umtopfen wenn nicht notwendig (Palmen sind störungssensitiv). | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | deep_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Echte Schatten-/Unterwuchs-Pflanze (deep_shade) — als C3-Pflanze mit niedrigem Lichtkompensationspunkt (light compensation point, LCP) typisch für tiefschattenadaptierte tropische Understory-Arten (Spanne schattentoleranter Arten 10–50 µmol/m²/s; hier unteres Band). Der LCP (Netto-Photosynthese = 0) ist NICHT mit Sättigungs-/Optimumwerten zu verwechseln; bestes Wachstum bei hellem indirektem Licht (PPFD-Ziel siehe §2.2). Flaches Wurzelsystem (shallow roots), daher staunässeempfindlich (Wurzelfäule-Risiko). Salzempfindlich: gedeiht nicht in salzigen Böden, hohe Dünger-/Salzfrachten schädigen die Wurzeln; eine quantitative ECe-Schwelle (Maas-Hoffman a) ist für diese Art nicht belastbar belegt. pH-Vorzug quellentreu auf 6.0–7.0 begrenzt (harmonisiert mit §1.6 und §2.3); breitere Toleranz (leicht sauer bis neutral, ~pH 5.1–8.0) wird in Quellen genannt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill, Batch 4) -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 29 (85 °F; unterhalb dessen verlangsamt sich die Keimung deutlich und Krankheitsrisiko steigt) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 35 (95 °F; Optimum ca. 90 °F/32 °C laut mehreren Palmensamen-Anbietern) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | -- <!-- DATEN FEHLEN: keine 2 unabhängigen Quellen mit konkreter cm-Angabe; Praxis: Samen nur oberflächlich/knapp bedeckt aussäen --> | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 42 (6–14 Wochen It. Fachhandel; Palmensamen keimen notorisch langsam und uneinheitlich, teils bis 6 Monate bei älterem Saatgut, vgl. S.1.3) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 0.5 (Frischsamen: höchste Keimrate direkt nach Ernte; Keimfähigkeit hält sich nur ca. 4–6 Monate — Chamaedorea-Samen gelten als kurzlebig/rekalzitrant, kein Langzeit-Lagersaatgut) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | -- <!-- DATEN FEHLEN: kein Licht-/Dunkelkeimungs-Nachweis aus 2 unabhängigen Quellen für Chamaedorea elegans auffindbar --> | `species.seed_profile.light_germination` |
| Vorbehandlung | scarification, presoak (Samenschale anfeilen/anritzen + 1–7 Tage in Wasser einweichen, taeglich Wasser wechseln; teils zusaetzlich GA3-Behandlung in der Praxis) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 167 (ca. 6.000 Samen/kg It. Fachhandelsangaben; grosse, harte Palmensamen) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | -- <!-- DATEN FEHLEN: Chamaedorea wird einzeln in Toepfen/Schalen ausgesaet, keine Reihen-/Direktsaat mit definierter Endabstands-Flaechendichte --> | `species.seed_profile.sowing_density_per_m2` |

Quellen (S.1.8):
1. Interne Keiminfos S.1.3 dieses Dokuments (frische Samen bei 27–32 degC, Keimung 3–6 Monate) -- bereits als Quelle im Dokument gefuehrt.
2. VIRIAR -- Chamaedorea elegans, Parlor Palm (Seeds) / Growing Guide: Keimtemperatur 85–95 degF, Keimdauer 4–6 Wochen bis deutlich laenger, hoechste Keimrate bei sofortiger Aussaat nach Ernte, Keimfaehigkeit nur 4–6 Monate: https://www.viriar.com/products/chamaedorea-elegans-parlor-palm-20-x-fresh-seeds ; https://www.viriar.com/blogs/palms-tree-encyklopedia/chamaedorea-elegans-parlor-palm
3. FSHS (Florida State Horticultural Society) -- Temperature and Desiccation Affect the Germination of Chamaedorea Palm Seeds: 90 degF (32 degC) fuer schnellste, gleichmaessigste Keimung; Keimverzoegerung/Krankheitsrisiko bei niedrigeren Temperaturen: https://journals.flvc.org/fshs/article/download/92298/88490/0
4. Plant World Seeds -- Chamaedorea elegans Seeds (Parlour Palm): Vorbehandlung Anfeilen der Samenschale + Einweichen 24–48 h: https://www.plant-world-seeds.com/store/view_seed_item/7049/chamaedorea-elegans-seeds
5. Sheffield's Seed Company -- Chamaedorea elegans: Samenzaehlung ca. 6.000 Samen/kg: https://sheffields.com/seeds/Chamaedorea/elegans
6. TropicalSeeds.com -- Chamaedorea elegans: Keimdauer 6–14 Wochen, Vorbehandlung Einweichen 1–7 Tage: https://www.tropicalseeds.com/chamaedorea-elegans
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 (seed-profile-backfill, Batch 4) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 4–10 | `requirement_profiles.dli_target_mol` |
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:3 (K-betont, typisch für Palmen) | 0.6–1.0 | 6.0–7.0 | 80 | 30 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu Mikronährstoffen:** Artspezifische ppm-Zielwerte für Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) sind für Chamaedorea elegans nicht aus mindestens zwei unabhängigen seriösen Quellen belegt und daher als fehlend markiert. Praktisch werden sie über handelsübliche Palmen-/Zimmerpflanzen-Volldünger mit Spurenelement-Chelaten abgedeckt; Mn-Mangel (Frizzletop) und K-/Mg-Mangel sind bei Palmen die häufigsten Mikro-/Makronährstoff-Defizite. `nutrient_profiles.manganese_ppm` / `_zinc_ppm` / `_copper_ppm` / `_molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Palmen-Dünger | Compo | base | 5-3-7 | 5 ml/L (monatlich) | Wachstum |
| Zimmerpflanzen-Flüssigdünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Monatlich März bis September. Oktober bis Februar: kein Dünger. Palmen brauchen etwas mehr Kalium und Magnesium als typische Zimmerpflanzen. Fluorid schadet (Blattspitzenverbrennung) — kalkfreies Wasser bevorzugt. Spezielle Palmendünger sind empfehlenswert.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes, weiches Wasser bevorzugt (Fluorid schadet!); Staunässe vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (min. 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell bis halbschattig (kein direktes Wintersonnenlicht) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert: Substrat nur leicht feucht halten, Staunässe vermeiden | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Frostempfindliche Kübel-/Zimmerpalme (USDA 10–11). In Mitteleuropa (USDA 6–8) ganzjährig frostfrei kultivieren: außerhalb der frostfreien Monate zwingend ins Haus holen (frost_free, nicht hardy). Kein echter Kältereiz/keine Dormanz nötig (vgl. §1.1 `dormancy_required = false`) — die „Winterruhe" ist nur eine lichtbedingte Wachstumsverlangsamung. Im Winterquartier bei Zimmertemperatur halten; Heizungsnähe (trockene Luft, Spinnmilbengefahr) meiden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Wedel | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Hohe Luftfeuchtigkeit | cultural | Regelmäßig sprühen | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Raubmilbe (predatory mite) | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | ~5–20/m² (bei Befall), ggf. alle 3–5 Wochen wiederholen | 2–3 Wochen |
| Australischer Marienkäfer / Schmierlaus-Jäger (mealybug destroyer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | ~2–5/m² (mehrere Teilfreilassungen) | 4–8 Wochen |

**Hinweis:** Phytoseiulus persimilis benötigt > 60 % relative Luftfeuchte und 17–28 °C (optimal) — passt gut zum tropischen Care-Profil der Stubenpalme. Cryptolaemus montrouzieri arbeitet am besten bei 25–28 °C und moderater bis hoher Luftfeuchte; 2–3 kleinere Freilassungen sind einer großen vorzuziehen. Ausbringraten herstellerseitig meist in „Stück pro Pflanze/ft²" angegeben (≈ 0.5–4/ft²); hier auf m² umgerechnet und nach Befallsstärke zu skalieren.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kentia-Palme | Howea forsteriana | Palme, Zimmerkultur | Robuster bei niedrigen Temperaturen |
| Areca-Palme | Dypsis lutescens | Palme, Zimmerkultur | Schneller wachsend |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Chamaedorea elegans,"Stubenpalme;Bergpalme;Parlor Palm;Neanthe Bella Palm",Arecaceae,Chamaedorea,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Mexiko, Guatemala, Belize",yes,3-15,20,60-200,40-120,yes,limited,false,light_feeder,0.6
```

---

## Quellenverzeichnis

1. [Gardenia.net — Chamaedorea elegans](https://www.gardenia.net/plant/chamaedorea-elegans-parlor-palm) — Botanische Daten, Kulturdaten
2. [OurHouseplants — Parlour Palm](https://www.ourhouseplants.com/plants/parlour-palm) — Detaillierte Pflegehinweise
3. [Greenery Unlimited — Neanthe Bella Palm](https://greeneryunlimited.co/blogs/plant-care/neanthe-bella-palm-care) — Pflegehinweise
4. [Joy Us Garden — Neanthe Bella Palm](https://www.joyusgarden.com/neanthe-bella-palm-care-tips-for-this-table-top-palm/) — Praxiswissen
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NC State Extension — Chamaedorea elegans Plant Toolbox](https://plants.ces.ncsu.edu/plants/chamaedorea-elegans/) — Boden-pH (acid–neutral, 6.0–8.0), Lichtbedarf (deep shade / dappled sunlight), Drainage/Feuchte-Toleranz, Wuchsmaße (University Extension)
7. [Sterck et al. 2013, Journal of Ecology — Light compensation point in tropical forest understorey species](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — Lichtkompensationspunkt schattentoleranter Understory-Arten (10–50 µmol/m²/s), C3-Physiologie (peer-reviewed)
8. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Spinnmilben-Raubmilbe: Ausbringung, Etablierungszeit, Klimaansprüche (University IPM)
9. [UC IPM — Mealybug Destroyer (Cryptolaemus montrouzieri)](https://ipm.ucanr.edu/natural-enemies/mealybug-destroyer/) — Schmierlaus-Nützling: Freilassungsrate, Etablierungszeit, optimale Bedingungen (University IPM)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
