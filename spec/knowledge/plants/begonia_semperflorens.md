# Wachsbegonie, Eisbegonie — Begonia semperflorens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net — Wax Begonia](https://www.gardenia.net/genus/begonia-semperflorens-cultorum-wax-begonia), [Smart Garden Guide](https://smartgardenguide.com/wax-begonia-care/), [Garden Design](https://www.gardendesign.com/plants/wax-begonia.html), [UMN Extension](https://extension.umn.edu/flowers/begonia), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Begonia semperflorens | `species.scientific_name` |
| Synonyme | Begonia semperflorens-cultorum (Hybridgruppe im Handel) | — |
| Volksnamen (DE/EN) | Wachsbegonie, Eisbegonie, Immerblühende Begonie; Wax Begonia, Bedding Begonia, Ever-Flowering Begonia | `species.common_names` |
| Familie | Begoniaceae | `species.family` → `botanical_families.name` |
| Gattung | Begonia | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 6 (≈ 43 °F; Hauptwuchs-/Blühphase) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 1 (als Annuelle) oder 3–5 (als Zimmerpflanze überwintert) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage | Entfällt (tropische Art ohne Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | Entfällt (tagneutral / day_neutral — Blüte temperatur- und lichtmengengesteuert, nicht photoperiodisch) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Als Einjährige kultiviert oder bei mindestens 10°C überwintern. | `species.hardiness_detail` |
| Heimat | Brasilien — tropische Regenwaldränder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Wachsbegonie gehört zu den vielseitigsten Balkonpflanzen Deutschlands — sie verträgt Sonne bis Halbschatten und blüht pausenlos von Mai bis Frost. Der Name "Wachsbegonie" bezieht sich auf den wachsartig glänzenden Blätter. Bronzeblättrige Sorten vertragen mehr Sonne als grünblättrige. Als Zimmerpflanze kann sie auch im Winter weiterblühen. Botanisch handelt es sich meist um Kultivare und Hybriden aus verschiedenen brasilianischen Wildarten.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 12–16 (Aussaat Januar/Februar, Samen sehr klein — Stecklinge bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (bis Frost) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge 5–7 cm in Wasser bewurzeln (4–6 Wochen) oder direkt in feuchtes Substrat. Samen extrem fein (staubkornfein) — Aussaat auf Oberfläche ohne Abdecken.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (besonders unterirdische Teile/Wurzeln) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides (besonders Wurzeln/Rhizome) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (leichter Rückschnitt für kompakteren Wuchs) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–45 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Hauptanwendung!) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, gut drainierte Blumenerde. pH 5.5–6.5. Fertige Begonienerde oder Einheitserde + 20% Perlite. Leicht feucht halten. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (LCP, PPFD µmol/m²/s) | 10–25 | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-a-Wert; Art als salzempfindlich beschrieben (qualitativ) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-b-Wert | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis:** Als schattenadaptierte Unterwuchspflanze (understory) hat die Wachsbegonie einen niedrigen Lichtkompensationspunkt (light compensation point) — geschätzt im Bereich 10–25 µmol/m²/s; bronzeblättrige Sorten liegen am oberen Rand, grünblättrige am unteren. Der hier genannte Wert ist NUR der Kompensationspunkt (Netto-Photosynthese = 0). Davon klar zu trennen sind der Lichtsättigungspunkt (Sättigung der Photosynthese, je nach Akklimatisation ~200–800 µmol/m²/s) und die Photoinhibitions-Schwelle (oberhalb ~1200 µmol/m²/s, in Vollsonne 2100 µmol/m²/s droht Photoschaden, Fv/Fm fällt auf 0.45–0.52). Wachsbegonien sind ausgesprochen salzempfindlich (Substrat-ECe, NICHT Gießwasser-EC) — kein verlässlicher quantitativer Maas-Hoffman-Schwellenwert publiziert; daher Schwelle/Slope als Daten fehlen markiert, Klasse aber qualitativ als `sensitive` belegbar.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.8 Saatgut & Keimung (Seed Profile)

<!-- Quelle: Seed-Profile-Backfill Batch 3 (2026-07-04) -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 21 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 27 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0 (Feinstsamen, Lichtkeimer — nicht abdecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 14–28 (KA-Feld: 14) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 3 | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | <!-- keine Vorbehandlung erforderlich --> | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | 0.0125–0.014 (extreme Feinstsamen; ca. 70.000–80.000 Samen/g) | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Aussaat erfolgt in Schalen/auf der Substratoberfläche mit anschließendem Pikieren/Verschulen und Auspflanzen als Jungpflanze — keine Direktsaat mit Feld-Enddichte --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):** [Neil Sperry's GARDENS — How many seeds per ounce?](https://neilsperry.com/2021/10/how-many-seeds-per-ounce/10-14-21-wax-begonia-seeds-low-res/); [HowStuffWorks — Wax Begonia, Fibrous Begonia: A Profile of Annuals](https://home.howstuffworks.com/define-wax-begonia-fibrous-begonia.htm); [Plant Care Today — Growing Wax Begonias from Seed](https://plantcaretoday.com/growing-wax-begonias-seed.html); [Little Yellow Wheelbarrow — Begonias from Seed](https://www.littleyellowwheelbarrow.com/grow-begonias-seed-indoors/); [Laidback Gardener — Successfully Sowing Begonias From Seed](https://laidbackgardener.blog/2017/01/08/successfully-sowing-begonias-from-seed/); [American Begonia Society — Seed Collection and Storage](https://www.begonias.org/seed-collection-and-storage/); [Live to Plant — All About Begonia Plant Seeds](https://livetoplant.com/all-about-begonia-plant-seeds-germination-storage-and-sowing/).
<!-- /Quelle: Seed-Profile-Backfill Batch 3 (2026-07-04) -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung/Jungpflanze | 20–40 | 1 | false | false | low |
| Wachstum/Hauptblüte (Frühling–Herbst) | 150–180 | 2 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum/Hauptblüte (Mai–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 (kritischer Punkt; ~0.3 kPa über oberem Zielwert) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (offenes Tageslicht) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.2–0.4 | 5.5–6.5 | — | — | — | — | — | — |
| Wachstum/Blüte | 1:2:2 | 0.8–1.5 | 5.5–6.5 | 70 | 30 | 0.5 | 0.25 | 0.05 | 0.05 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Wachstum/Blüte):** Manganese (Mn) 0.5 ppm, Zinc (Zn) 0.25 ppm, Copper (Cu) 0.05 ppm, Molybdenum (Mo) 0.05 ppm (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`). Werte folgen den Standard-Zielkonzentrationen für Floriculture-/Zierpflanzen-Nährlösungen. Bei Mediumkultur sind Mikronährstoffe meist über den Volldünger/das Substrat abgedeckt — die Toleranzspanne zwischen Mangel und Toxizität ist eng (pH 5.5–6.5 einhalten, sonst Mn-/Fe-Verfügbarkeit gestört).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Flüssigdünger | Compo | base | 5-8-10 | 5 ml/L (alle 14 Tage) | Blüte |
| Balkonpflanzen-Dünger | Substral | base | 5-8-11 | 5 ml/L | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Blaukorn | – | mineralisch Langzeit | 3–5 g/L Substrat | einmalig beim Einpflanzen |

### 3.2 Besondere Hinweise

Mittelzehrer. Alle 14 Tage ab Mai bis September. Phosphat-betonter Dünger fördert Blütenbildung. NIE auf trockenes Substrat düngen — zuerst leicht angießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; NIE auf Blätter gießen (Pilzanfälligkeit); zwischen Güssen leicht antrocknen lassen; keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost / vor < 10 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–16 (mind. 10 °C frostfrei; hell ~16 °C für Weiterblüte) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (bright); bei zurückgeschnittener Ruhe auch kühl-dunkel im frostfreien Keller/Garage möglich | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam; nur leicht feucht halten, Staunässe vermeiden; ab März wieder langsam steigern | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Die Wachsbegonie ist nicht frosthart (`frost_sensitivity: tender`) und kennt keine echte Dormanz. Sie wird daher als Kübel-/Zimmerpflanze **frostfrei drinnen** überwintert (`frost_free` — KEIN `dig_and_store`, da kein Knollen-Organ wie bei der Knollenbegonie). Vor dem ersten Frost bzw. bevor die Nachttemperaturen unter ~10 °C fallen (Oktober) ins Haus holen; im Mai nach den Eisheiligen wieder nach draußen (vorher abhärten/harden_off).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollschildlaus | Pseudococcus spp. | Wollflecken | easy |
| Weiße Fliege | Trialeurodes vaporariorum | Fliegen aufsteigen beim Berühren | easy |
| Blattläuse | Aphis spp. | Klebrige Triebe | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter matt | medium |
| Thrips | Frankliniella occidentalis | Silbrige Streifen | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Trockene Luft, Nachtfeuchte |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel | Feuchte, dichte Bepflanzung |
| Pythium Wurzelfäule | fungal | Welke, braune Wurzeln | Überwässerung |
| Bakterienblattkrankheit | bacterial | Wassergetränkte Flecken | Spritzwasser, Verletzungen |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| NIE auf Blätter gießen | cultural | Gießtechnik anpassen | 0 | Mehltau, Grauschimmel (Prävention) |
| Befallene Teile entfernen | cultural | Sofort abschneiden | 0 | Alle Pilzerkrankungen |
| Neemöl | biological | Sprühen 0.3% | 0 | Spinnmilben, Blattläuse |
| Insektizidseife | biological | Sprühen 1% | 0 | Schmierläuse, Thrips |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Schlupfwespe | Encarsia formosa | Weiße Fliege (Trialeurodes vaporariorum) | 1–10 / m² (alle 1–2 Wochen, mind. 5 Ausbringungen) | 1–2 Wochen (bei 20–25 °C) |
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 10–30 / m² (kurativ; 1 Räuber : 10 Milben) | 1–2 Wochen (optimal 20–27 °C, RLF > 60 %) |
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphis spp.) | 1–2 / m² (präventiv); höher bei Befall, mind. 2 Freilassungen | ca. 3 Wochen (überlappende Generationen aufbauen) |
| Raubmilbe | Neoseiulus (Amblyseius) cucumeris | Thrips (Frankliniella occidentalis) | 100–200 / m² (präventiv, wöchentlich) | 4–8 Wochen |

**Hinweis:** Nützlingseinsatz vor allem im Gewächshaus / Wintergarten sinnvoll. Encarsia und Phytoseiulus fliegen/agieren erst ab ~20 °C zuverlässig; bei kühler Überwinterung daher wenig wirksam. Nützlinge nicht mit Neemöl/Insektizidseife kombinieren (Kontaktwirkung schädigt auch die Räuber) — vor Ausbringung mind. die Karenzzeit der Spritzmittel abwarten.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Balkon-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Königsbegonie | Begonia rex-cultorum | Gleiche Gattung | Ausgezeichnetes Blattwerk |
| Knollenbegonie | Begonia tuberhybrida | Gleiche Gattung | Größere Blüten |
| Fleißiges Lieschen | Impatiens walleriana | Ähnliche Nutzung | Mehr Schattentoleranz, tierfreundlich |
| Pelargonium | Pelargonium zonale | Ähnliche Nutzung | Sonnenliebend, sehr robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Begonia semperflorens,"Wachsbegonie;Eisbegonie;Immerblühende Begonie;Wax Begonia;Bedding Begonia",Begoniaceae,Begonia,annual,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b","Brasilien",yes,2-8,15,20-50,20-45,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Wax Begonia](https://www.gardenia.net/genus/begonia-semperflorens-cultorum-wax-begonia) — Botanische Daten, Kulturbedingungen
2. [Smart Garden Guide — Wax Begonia](https://smartgardenguide.com/wax-begonia-care/) — Pflegehinweise
3. [Garden Design — Wax Begonias](https://www.gardendesign.com/plants/wax-begonia.html) — Standort, Sorten
4. [UMN Extension — Begonia](https://extension.umn.edu/flowers/begonia) — Schädlinge, Krankheiten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (leicht giftig — Calcium-Oxalate)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Blanchard & Runkle, MSU — Energy-Efficient Annuals: Vinca & Wax Begonia (PDF)](https://www.canr.msu.edu/uploads/resources/pdfs/10-begonia-and-vinca.pdf) — Basistemperatur (43 °F ≈ 6 °C), Tagneutralität, DLI ~10 mol/m²/d
7. [Greenhouse Grower — Energy-Efficient Annuals: Vinca and Wax Begonia](https://www.greenhousegrower.com/crops/energy-efficient-annuals-vinca-and-wax-begonia-2/) — Basistemperatur (43 °F), day-neutral, Blühentwicklung
8. [Blanchard & Runkle (2011), Quantifying the thermal flowering rates of eighteen species of annual bedding plants — ResearchGate](https://www.researchgate.net/publication/229133690_Quantifying_the_thermal_flowering_rates_of_eighteen_species_of_annual_bedding_plants) — Tmin/Topt-Modelle für Beetpflanzen
9. [Investigating Morphological and Physiological Responses to Stress in Begonia semperflorens — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12026712/) — Photoinhibition (Fv/Fm), Lichtsättigung, Vollsonnen-Stress (2100 µmol/m²/s)
10. [NC State Extension — Begonia, Wax Types](https://plants.ces.ncsu.edu/plants/begonia-wax-types/) — Boden-pH, Drainage/Staunässe-Empfindlichkeit, Schatten-/Sonnentoleranz, Wurzeltyp
11. [Gardener's Path — Grow Wax Begonias](https://gardenerspath.com/plants/flowers/grow-wax-begonias/) — Salzempfindlichkeit, Boden-pH 5.5–6.5, Standort
12. [Greg.app — Wax Begonia Roots](https://greg.app/wax-begonia-roots/) — effektive Wurzeltiefe 15–30 cm (fibrous)
13. [Plantura — Overwintering Begonias](https://plantura.garden/uk/flowers-perennials/begonias/overwintering-begonias) — Überwinterung Wachsbegonie (frostfrei, ~16 °C, sparsam gießen, ab März wieder)
14. [Gardening Know How — Wintering Begonias](https://www.gardeningknowhow.com/ornamental/flowers/begonia/wintering-begonias-overwintering-a-begonia-in-cold-climates.htm) — Indoor-Überwinterung, Mindesttemperatur
15. [UMass Extension — Biological Control: Greenhouse Pests and Natural Enemies](https://www.umass.edu/agriculture-food-environment/greenhouse-floriculture/fact-sheets/biological-control-greenhouse-pests-their-natural-enemies) — Nützlinge & Zielschädlinge
16. [Koppert — Neoseiulus cucumeris](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/neoseiulus-cucumeris/) — Ausbringraten Thrips-Raubmilbe
17. [Cornell NYSIPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Spinnmilben-Raubmilbe, Ausbringrate/Bedingungen
18. [PSU Extension — Hydroponics Nutrient Solution Programs and Recipes](https://extension.psu.edu/hydroponics-systems-nutrient-solution-programs-and-recipes) — Mikronährstoff-Zielkonzentrationen (Mn/Zn/Cu/Mo)
19. [Science in Hydroponics — Micro and Macro Nutrient Sufficiency Ranges](https://scienceinhydroponics.com/2017/03/hydroponic-micro-and-macro-nutrient-sufficiency-ranges.html) — Mikronährstoff-Zielbereiche
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
