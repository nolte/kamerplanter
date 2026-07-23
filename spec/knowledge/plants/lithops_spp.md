# Lebende Steine — Lithops spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/lithops-living-stones), [Succulents Box](https://succulentsbox.com/blogs/blog/how-to-care-for-lithops), [UK Houseplants](https://www.ukhouseplants.com/plants/lithops-living-stones), [Wisconsin Horticulture Extension](https://hort.extension.wisc.edu/articles/living-stones-lithops/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Lithops spp. (Gattung, ~145 Arten/Varietäten) | `species.scientific_name` |
| Volksnamen (DE/EN) | Lebende Steine, Steinpflanzen; Living Stones, Pebble Plants | `species.common_names` |
| Familie | Aizoaceae | `species.family` → `botanical_families.name` |
| Gattung | Lithops | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | succulent <!-- KORREKTUR #680: an Seed-SSOT angeglichen (vorher herb); Lithops sind Blattsukkulenten --> | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Lithops auffindbar; keine Keim-Basistemperatur umetikettiert --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Sommer- und Winterdormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), Zyklus saisonal über Temperatur/Feuchte gesteuert, nicht photoperiodisch — kein Stundenwert anwendbar --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 4°C. Optimal 18–27°C im Wachstum, 10–15°C in der Winterruhe. | `species.hardiness_detail` |
| Heimat | Südafrika, Namibia — Kieswüsten, trockene Felsebenen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Lithops sind die extremsten Sukkulenten — ihre Tarnfarbe imitiert perfekt Kieselsteine in ihrer Heimat Südafrika/Namibia. Das Hauptproblem für Einsteiger ist Überwässerung: falsch gegossen führen Lithops zur Spalte auf (platzen). Der Gießkalender ist strikt jahreszeitlich — im Winter (Hüllblatt-Wechsel läuft) und im Sommer (Hochsommerdormanz) NICHT gießen. Aktive Wachstumsperioden: Frühling und Herbst. Nach der Blüte (Herbst) entwickelt sich das neue Blattpaar innerhalb des alten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 9, 10, 11 (weiße oder gelbe Gänseblümchen-ähnliche Blüten; erscheinen aus der Mittelspalte) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Samen bei 22–28°C, sehr fein, auf Substratoberfläche ohne Bedeckung. Keimung in 7–21 Tage. Teilung beim Aufteilen von Kopf-Clustern möglich (selten). Sämlinge brauchen 3–5 Jahre bis zur Blühreife.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Niemals eingreifen. Das alte Blattpaar (vertrocknete Hülle) niemals vor dem vollständigen Absterben entfernen — das neue Blattpaar bezieht Wasser und Nährstoffe aus der alten Hülle.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.2–1 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 (tiefe Pfahlwurzeln) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 2–5 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 2–5 pro Körper | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (kein Regen! Volle Sonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | 80% mineralisch (Quarzsand, Perlite, Bimssplit) + 20% Kakteenerde. pH 6.5–7.5. Extrem schnelldränierende Mischung. Hohes Topf (10+ cm tief) für Pfahlwurzel. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch belegter Netto-Null-Kompensationspunkt (LCP) für Lithops auffindbar --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 7–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (a) für Lithops; Klasse sensitive qualitativ belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope (b) für Lithops --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Lithops sind volle Sonne (full sun) gewohnt (Kieswüsten Südafrika/Namibia, kein Kronendach), benötigen aber im Mitteleuropa-Sommer Schutz vor intensiver Mittagssonne (40% Schattiergewebe April–September) zur Vermeidung von Verbrennungen — das ist Stressschutz, keine echte Schattentoleranz. Lichtkompensationspunkt (light compensation point, LCP): CAM-Sukkulenten haben sehr niedrige LCP-Werte, ein artspezifischer Wert für Lithops ist aber nicht belegt. Salztoleranz: Lithops reagieren empfindlich (sensitive) auf Dünger-/Salzanreicherung im Substrat; Symptome (gelbe Körper, weiße Salzkruste, braune Spitzen) treten schon bei geringer Überdüngung auf — quantitative ECe-Schwellen (Substrat-ECe, nicht Gießwasser-EC) sind in der Literatur nicht belegt. Boden-pH 6.0–7.0 (quellentreu); dies überschneidet sich mit der in §1.6/§2.3 genannten Spanne 6.5–7.5 — der konsensgestützte Optimalbereich liegt bei 6.5–7.0. <!-- W-013 -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 20 (Tag; Nachttemperatur 10–15°C — Temperaturwechsel fördert Keimung) | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 28 (obere Konsensgrenze aus §1.3 22–28°C und Beci-Lithops-Tagesspanne 20–25°C) | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Lichtkeimer; nur auf feuchtes Substrat andrücken, nicht bedecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (Spanne 7–24 Tage; vereinzelte Samen keimen erst nach Wochen bis Monaten) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 10 (bei kühler, dunkler, trockener Lagerung; viele Arten bleiben deutlich länger keimfähig) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (keine Stratifikation/Skarifikation dokumentiert) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: kein belegter TKG-Wert für Lithops spp. aus zwei unabhängigen Quellen auffindbar; Samen extrem klein/staubfein --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Aussaat erfolgt in Anzuchtschalen/Töpfen (kein Feld-/Reihenanbau); kein Flächendichte-Wert anwendbar --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):**
1. [Beci Lithops — How To Grow Lithops From Seed](https://www.lithops.me/en/how-to-grow-lithops-from-seed/) — Keimtemperatur (Tag 20–25°C, Nacht 10–15°C), Keimdauer (7–24 Tage), Aussaat auf Substratoberfläche ohne Bedeckung
2. [World of Succulents — How to Grow Lithops from Seed](https://worldofsucculents.com/grow-lithops-seed/) — Keimdauer (bis zu 6 Wochen, vereinzelt länger), Lichtbedarf beim Keimen
3. [BCSS Forum — Growing Lithops from seed](https://forum.bcss.org.uk/viewtopic.php?t=144166) — Keimfähigkeitsdauer > 10 Jahre bei kühler, trockener, dunkler Lagerung
4. §1.3 dieses Steckbriefs (bereits zitierte Quellen: Samen bei 22–28°C, Keimung 7–21 Tage, Substratoberfläche ohne Bedeckung) — Cross-Check Keimtemperatur/-tiefe
<!-- /Quelle: Seed-Profile-Backfill (Issue #301, Batch 8) 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrs-Wachstum (März–Mai) | 60–90 | 1 | false | false | very high |
| Hochsommer-Dormanz (Juni–August) | 60–90 | 2 | false | false | very high |
| Herbst-Wachstum + Blüte (Sept–Nov) | 60–90 | 3 | false | false | very high |
| Winter-Hüllblattwechsel (Dez–Feb) | 60–90 | 4 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum (Frühjahr/Herbst)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 500–2000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–55 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 10–30 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.5–3.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 4.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–60 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Dormanz (Sommer + Winter-Hüllblattwechsel)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–1000 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–27 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 4.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 15–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 60–90 (gar nicht gießen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 0 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Wachstum | 0:1:1 | 0.2–0.4 | 6.5–7.5 | 20 | 8 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Dormanz | 0:0:0 | 0.0 | 6.5–7.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Für Lithops (extremer Schwachzehrer, light feeder) sind keine artspezifischen Mikronährstoff-Sollwerte (Mn/Zn/Cu/Mo in ppm) aus seriösen Quellen belegt. Bedarf wird über das jährliche Umtopfen in frisches mineralisches Substrat sowie eine sehr verdünnte (¼–½ Dosis) Herbst-Düngung gedeckt; eigene Mikronährstoff-Zugaben werden nicht empfohlen (Salzanreicherungs-/Überdüngungsrisiko, salt_tolerance_class = sensitive). Daher Mn/Zn/Cu/Mo als DATEN FEHLEN markiert statt geschätzt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 1 ml/L (1×/Saison) | Herbst-Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Frisches Substrat | — | — | Jährliches Umtopfen gibt ausreichend Nährstoffe | Frühjahr |

### 3.2 Besondere Hinweise

Extremer Schwachzehrer. Höchstens 1× pro Jahr düng im Herbst (sehr verdünnt). Frisches Substrat beim Umtopfen liefert genügend Nährstoffe. Überdüngung führt zu unkontrolliertem Wachstum und Platzen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 60–90 (Sommer = Dormanz = NICHT gießen) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.0 (Winter = Hüllblattwechsel = NICHT gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; GIESSK ALENDER strikt einhalten: nur Frühjahr (März–Mai) und Herbst (Sept–Nov) gießen; Sommer und Winter KEIN Wasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 365 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–15 (Minimum 8) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (Südfenster oder Pflanzenlicht, 10–12 h/Tag; Vergeilung/Etiolierung vermeiden) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | none (komplett trocken halten; November–März kein Wasser) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Lithops sind nicht frosthart (frost_sensitivity = tender) und müssen in Mitteleuropa (USDA 6–8) frostfrei drinnen überwintern — Einstufung frost_free (nicht hardy/needs_protection, da keine Freiland-Überwinterung möglich). In die Winterruhe fällt der Hüllblattwechsel: das alte Blattpaar trocknet ein, das neue zieht Wasser daraus; Gießen während dieser Phase führt zu Fäulnis/Platzen. Hell, kühl (10–15 °C), absolut trocken halten. <!-- W-013 -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in der Mittelspalte | medium |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Pflanze kollabiert, weiche Basis | Überwässerung |
| Platzen/Splitting | physiologisch | Körper reißt auf | Zu viel Wasser während Dormanz |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Gießplan einhalten | cultural | Jahreszeitlichen Kalender strikt befolgen | 0 | Platzen, Wurzelfäule (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|--------------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10 Käfer/m²/Freilassung (bei Befall bis 25–35/Pflanze); 3 Gaben im Abstand von 1–2 Wochen | ca. 3–6 Wochen (Generationszyklus ~7 Wochen) |
| Raubmilbe (Hypoaspis) | Stratiolaelaps scimitus (syn. Hypoaspis miles) | Trauermücken-Larven (Bradysia spp.) | 100–500 Milben/m²; 2 Gaben im Abstand von 2–3 Wochen, präventiv früh ausbringen | 2–3 Wochen |
| Insektenpathogene Nematoden | Steinernema feltiae | Trauermücken-Larven (Bradysia spp.) | ca. 0,5 Mio. infektiöse Juvenile/m² (Bodenausbringung mit Gießwasser) | 1–2 Wochen |

**Hinweis:** Nützlingseinsatz bei Lithops eher selten nötig (geschlossene Sukkulenten-Sammlung). Cryptolaemus montrouzieri und Wattestäbchen-Alkohol (§5.3) gegen Schmierläuse in der Mittelspalte; Stratiolaelaps scimitus / Steinernema feltiae gegen Trauermücken im Substrat (treten v. a. bei zu feuchtem Substrat auf — primäre Maßnahme bleibt der strikte Gießkalender). Nematoden benötigen ausnahmsweise leicht feuchtes Substrat zur Ausbringung. <!-- W-013 -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze. Ideal für Sukkulenten-Arrangements mit anderen Wüstenpflanzen.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Plebejum | Conophytum spp. | Aizoaceae, ähnliche Steinmimikry | Etwas robuster |
| Titanopsis | Titanopsis spp. | Aizoaceae, Steinmimikry | Beginner-freundlicher |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Lithops spp.,"Lebende Steine;Steinpflanzen;Living Stones;Pebble Plants",Aizoaceae,Lithops,perennial,day_neutral,herb,taproot,"10a;10b;11a;11b","Südafrika, Namibia (Kieswüsten)",yes,0.2-1,10,2-5,2-5,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Lithops Living Stones](https://www.gardenia.net/plant/lithops-living-stones) — Botanische Daten
2. [Succulents Box — Lithops Care](https://succulentsbox.com/blogs/blog/how-to-care-for-lithops) — Pflegehinweise, Gießkalender
3. [UK Houseplants — Lithops](https://www.ukhouseplants.com/plants/lithops-living-stones) — Kulturdaten
4. [Wisconsin Horticulture Extension — Lithops](https://hort.extension.wisc.edu/articles/living-stones-lithops/) — Wissenschaftliche Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Wikipedia — Crassulacean acid metabolism (CAM)](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Photosynthese bei Wüstensukkulenten (Lithops als CAM-Pflanze)
7. [ScienceDirect — Crassulacean Acid Metabolism Plant (Overview)](https://www.sciencedirect.com/topics/pharmacology-toxicology-and-pharmaceutical-science/crassulacean-acid-metabolism-plant) — Bestätigung CAM-Photosynthesetyp bei Sukkulenten/Lithops
8. [Beci Lithops — Cultivation and care fundamentals](https://www.lithops.me/en/lithops-cultivation-and-care-fundamentals/) — Boden-pH (6–7), Lichtbedarf/Sonnenschutz, Wurzeltiefe (≥7 cm, Pfahlwurzel), Düngung (½ Dosis)
9. [Planteria Latina — Best Soil for Lithops](https://planterialatina.com/best-soil-for-lithops/) — Boden-pH (5,5–7), Drainage/Substrat
10. [Greg.app — Lithops Light Requirements](https://greg.app/lithops-light-requirements/) — Lichtbedarf, volle Sonne mit Mittagsschutz
11. [Quest Climate — Vapor Pressure Deficit (Part 1)](https://www.questclimate.com/vapor-pressure-deficit-indoor-growing-part-1-vpd/) — Sukkulenten/CAM tolerieren hohe VPD (niedrige VPD-Sensitivität)
12. [Cdnsciencepub — VPD and diffusion resistance in Opuntia compressa](https://cdnsciencepub.com/doi/abs/10.1139/b75-321) — CAM-Stomataverhalten unter VPD (Beleg geringe VPD-Empfindlichkeit)
13. [Cactus-online — Winter Care for Lithops and Succulents](https://www.cactus-online.net/winter-care-for-lithops-and-succulents-maintenance-without-watering/) — Überwinterung (frostfrei, kein Wasser)
14. [Succulentwise — Lithops Dormancy and Winter Care](https://succulentwise.com/lithops-dormancy-and-winter-care/) — Winterquartier 10–15 °C (Min. 8 °C), hell, trocken
15. [Live to Plant — Guide to Fertilizing Your Lithops](https://livetoplant.com/guide-to-fertilizing-your-lithops-plant/) — Salzempfindlichkeit/Überdüngungssymptome (salt_tolerance_class sensitive)
16. [University of Maryland Extension — Mineral and Fertilizer Salt Deposits on Indoor Plants](https://extension.umd.edu/resource/mineral-and-fertilizer-salt-deposits-indoor-plants) — Salzanreicherung im Substrat (Stützbeleg sensitive)
17. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Ausbringrate gegen Schmierläuse (2–10/m², Wiederholung)
18. [Koppert — Stratiolaelaps scimitus (Hypoaspis miles)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/stratiolaelaps-scimitus-hypoaspis-miles/) — Raubmilbe gegen Trauermücken
19. [Penn State Extension — Stratiolaelaps scimitus (Hypoaspis miles)](https://extension.psu.edu/all-about-stratiolaelaps-scimitus-hypoaspis-miles-predatory-mites) — Ausbringrate/Etablierung (100–500/m², 2 Gaben)
20. [Bugs for Growers — Biocontrol agents for fungus gnats (Steinernema feltiae)](https://blog.bugsforgrowers.com/natural-predators/entomopathogenic-nematodes/beneficial-nematodes/two-biocontrol-agents-for-effective-control-of-fungus-gnats/) — Nematoden gegen Trauermücken-Larven
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
