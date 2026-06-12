# Drachenpalmen — Dracaena spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-04-02
> **Fokus-Arten:** *Dracaena marginata* Lam. (Drachenbaum) und *Dracaena fragrans* (L.) Ker Gawl. (Duftdracaena/Grünlilie-Dracaena)
> **Quellen:** USDA Plants Database, Missouri Botanical Garden, NC State Extension, Penn State Extension, ASPCA, NASA Clean Air Study (Wolverton 1989), Gardener's Path, Gardening Know How, Plants For All Seasons

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung — *Dracaena marginata* (Drachenbaum)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dracaena marginata Lam. | `species.scientific_name` |
| Synonyme | Cordyline marginata, Dracaena concinna (partim) | — |
| Volksnamen (DE/EN) | Drachenbaum, Rotkantiger Drachenbaum; Dragon Tree, Madagascar Dragon Tree | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Ordnung | Asparagales | `botanical_families.order` |
| Gattung | Dracaena | `species.genus` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | 15–30 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht zutreffend, tropisch) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Keinerlei Frosttoleranz; Schäden ab +5 °C möglich, Absterben unter 0 °C | `species.hardiness_detail` |
| Heimat | Madagaskar (trockene bis feuchte Waldränder) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |
| Luftreinigungsgrad (NASA 1989) | 0.7 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, xylene, trichloroethylene | `species.removes_compounds` |

**Hinweis zur Taxonomie:** Die Gattung *Dracaena* wurde lange in die Familie Dracaenaceae oder Ruscaceae eingeordnet. Nach aktuellem APG-IV-System (2016) gilt Asparagaceae (Unterfamilie Nolinoideae) als korrekte Zuordnung. Ältere Literatur und Handelsnamen verwenden noch die veraltete Einordnung.

---

### 1.1b Botanische Einordnung — *Dracaena fragrans* (Duftdracaena)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dracaena fragrans (L.) Ker Gawl. | `species.scientific_name` |
| Synonyme | Aletris fragrans, Pleomele fragrans | — |
| Volksnamen (DE/EN) | Duftdracaena, Maispalme, Glücksbambus-Dracaena; Corn Plant, Mass Cane, Happy Plant | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Ordnung | Asparagales | `botanical_families.order` |
| Gattung | Dracaena | `species.genus` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | 15–30 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht zutreffend, tropisch) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral, keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10b–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Keinerlei Frosttoleranz; Schäden ab +5 °C, Absterben unter 0 °C; tropische Heimat Sudan–Angola | `species.hardiness_detail` |
| Heimat | Tropisches Afrika (Sudan, Mosambik, Côte d'Ivoire, Angola) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, fragrant | `species.traits` |
| Luftreinigungsgrad (NASA 1989) | 0.75 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, trichloroethylene | `species.removes_compounds` |

---

### 1.2 Aussaat- & Erntezeiten

Dracaena spp. werden als Zimmerpflanzen nicht gesät und nicht geerntet. Die folgenden Felder gelten für die gärtnerische Vermehrung (Stecklingsvermehrung in Mitteleuropa).

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant (Stecklinge, kein Samenanbau) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | nicht relevant | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6 (selten in Zimmerkultur; braucht Stressfaktor) | `species.bloom_months` |

---

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Praxishinweis:** Stängelsegmente von 10–15 cm Länge (je mit 1–2 Blattknoten) werden aufrecht oder liegend in feuchtes Perlite oder Anzuchterde gesteckt. Bewurzelung bei 22–26 °C und indirektem Licht nach 4–8 Wochen. Alternativ: Kopfsteckling direkt in Wasser oder feuchtes Substrat stellen. Saatgutvermehrung ist möglich, aber für die Praxis irrelevant (sehr langsam, Sortenmerkmale werden nicht reinerbig weitergegeben).

---

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true (mild, aber Vorsicht) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle oberirdischen Pflanzenteile (Blätter, Stängel, Beeren) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Steroidsaponine (u. a. Dracogenin) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (Katzen/Hunde), mild (Kinder) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false (Blüte tritt in Zimmerkultur kaum auf) | `species.allergen_info.pollen_allergen` |

**Wichtige Hinweise Toxizität:**
- Katzen reagieren empfindlicher als Hunde; typische Symptome: Erbrechen (ggf. mit Blut), Speichelfluss, erweiterte Pupillen, Appetitverlust, Lethargie.
- Hunde: Erbrechen, Durchfall, Schwäche, Speichelfluss.
- Beim Verzehr durch Kinder oder Haustiere umgehend tierärztliche bzw. medizinische Beratung (Giftnotruf) einholen.
- Quelle: ASPCA Animal Poison Control Center (aspca.org/pet-care/aspca-poison-control)

---

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Praxishinweis:** Ein Rückschnitt ist nicht zwingend nötig, aber bei zu langen, blätterlosen Stämmen oder nach Schäden sinnvoll. Einfach den Stamm auf gewünschte Höhe kürzen — aus den verbliebenen Nodien treiben neue Blattrosetten aus. Abgeschnittene Stammstücke können als Stecklinge verwendet werden.

---

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) — D. marginata | 5–15 (je nach Stammgröße) | `species.recommended_container_volume_l` |
| Empf. Topfvolumen (L) — D. fragrans | 10–30 (größere Pflanze) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe im Zimmer (cm) — D. marginata | 100–300 (im Freiland bis 600 cm) | `species.mature_height_cm` |
| Wuchshöhe im Zimmer (cm) — D. fragrans | 150–300 (im Freiland bis 600 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Platzbedarf (cm) | 60 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Sommermonate, kein Direktsonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (bei sehr alten, schweren Pflanzen ggf. Stab) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Zimmerpflanzenerde (z. B. Kaktuserde 60 % + Perlite 30 % + feiner Bimssand 10 %); pH 6,0–6,5; kein torfreiches, dauerhaft feuchtes Substrat | — |

---

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (kein artspezifischer Messwert aus ≥2 unabhängigen Quellen) | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> (kein artspezifischer Messwert aus ≥2 unabhängigen Quellen) | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 20–40 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (Wasserstau) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> (kein belegter Maas-Hoffman-a-Wert; Quellen qualitativ „poor/sensitive") | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> (kein belegter Maas-Hoffman-b-Wert) | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweise zur Umgebungs-Physiologie:**
- *Schattentoleranz:* Beide Arten wachsen im Naturhabitat unter dem Kronendach (Waldränder, Savanne) und gelten als ausgeprägt schattentolerant; sie überstehen sehr lichtarme Innenräume (D. fragrans toleriert bis ~100 fc / ≈ 10–11 klx-Äquivalent gemessen als sehr niedriger PPFD), wachsen aber bei mehr indirektem Licht voller. Enum `shade` gewählt (zwischen `partial_shade` und `deep_shade`); Mittagsdirektsonne wird gemieden (Blattverbrennung). (Quellen 16, 17)
- *Lichtkompensationspunkt:* Für schattentolerante Interior-Foliage-Pflanzen (u. a. *Epipremnum*, *Ficus benjamina*, *Chlorophytum*) werden in der Literatur sehr niedrige LCPs von etwa 10–20 µmol/m²/s berichtet; ein art­spezifischer, doppelt belegter Messwert für *Dracaena marginata*/*fragrans* ist nicht auffindbar, daher die KA-Felder als DATEN FEHLEN markiert (Hinweis-Bereich nicht als Messwert in das Feld übernehmen). (Quellen 18, 19)
- *Salztoleranz:* UF/IFAS stuft *D. marginata* als salzempfindlich („poor salt tolerance") ein; die Art reagiert empfindlich auf Salz- und insbesondere Fluoridakkumulation (vgl. §2.3/§3.4). Bezugsgröße einer etwaigen ECe-Schwelle wäre die Substrat-Sättigungsextrakt-ECe (nicht die Gießwasser-EC), ein quantitativer Maas-Hoffman-Wert ist jedoch nicht belegt. (Quellen 16, 20)
- *Staunässe:* Wurzeln benötigen Sauerstoff; dauerhaft nasses Substrat führt zu Wurzelfäule (*Pythium*, *Erwinia*). Daher `sensitive`. (Quelle 21)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

Dracaena spp. durchlaufen als mehrjährige Zimmerpflanzen keine klar abgegrenzten phänologischen Phasen wie Kulturpflanzen. Das nachfolgende Modell orientiert sich an den biologisch sinnvollen Pflegephasen im Jahresverlauf und am Anwachsen nach dem Umtopfen.

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung (Steckling/Umtopfen) | 28–56 | 1 | false | false | low |
| Juvenil (Eingewöhnung, erste Saison) | 90–180 | 2 | false | false | low |
| Aktives Wachstum (Frühjahr–Sommer) | 180–210 | 3 | false | false | medium |
| Dormanz / Winterruhe | 90–120 | 4 | false | false | high |

**Hinweis zum Phasenmodell:** Da Dracaena perennial und day_neutral ist, wiederholt sich das Phasenpaar „Aktives Wachstum + Dormanz" jährlich. In Kamerplanter werden die Phasen 3–4 als Jahreszyklus konfiguriert; Phase 1–2 werden nur beim ersten Einpflanzen durchlaufen.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu `dormancy_required` (botanische Korrektur):** *Dracaena* ist eine immergrüne tropische Art ohne physiologisch erzwungene Ruhephase (keine Endodormanz, kein Kältebedarf). Das KA-Feld `lifecycle_configs.dormancy_required` ist daher korrekt `false` (siehe §1.1/§1.1b). Die in §2.1 gelistete „Winterruhe" (Phase 4) ist eine rein umweltbedingte Wachstumsverlangsamung durch reduziertes Winterlicht und Heizungsluft in Mitteleuropa (USDA 6–8 als Indoor-Standort) — kein obligater Dormanzzyklus. Pflegerelevant (weniger Gießen/Düngen im Winter), aber kein zu erzwingender Kältereiz.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zum Photosynthese-Typ:** *Dracaena marginata* und *D. fragrans* sind nicht-sukkulente, breitblättrige C3-Pflanzen (`photosynthesis_type: c3`). Sie sind NICHT mit dem fakultativen CAM-Stoffwechsel der sukkulenten *Dracaena trifasciata* (syn. *Sansevieria trifasciata*, Bogenhanf) zu verwechseln, die in derselben Gattung steht, aber als Blattsukkulente CAM betreibt. Gaswechsel-/CO₂-Assimilationsmessungen an *D. fragrans* dokumentieren C3-Verhalten (Quelle 15).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

### 2.2 Phasen-Anforderungsprofile

#### Phase 1: Bewurzelung (Steckling / Umtopfen)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–6 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 (Raumluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 (Substrat oben trocken, unten leicht feucht) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 2: Juvenil (Eingewöhnung)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 (Raumluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 3: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 (natürliches Tageslicht ausreichend) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 (Raumluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7 (Sommer; obere 50–75 % Substrat trocken) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 (je nach Topfgröße) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase 4: Dormanz / Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 (hellster verfügbarer Standort) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–11 (natürliches Tageslicht im Winter) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 (Heizungsluft ist kritisch: zu trockene Luft begünstigt Spinnmilben) | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.8 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 (Raumluft) | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 (obere 75 % Substrat vollständig trocken) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

---

### 2.3 Nährstoffprofile je Phase

<!-- Quelle: Steckbrief-Erweiterung 2026-06 (Spalten Mn/Zn/Cu/Mo ergänzt) -->
| Phase | NPK-Verhältnis | EC (mS/cm) | pH | Ca (ppm) | Mg (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|------------|-----|----------|----------|----------|----------|----------|----------|----------|
| Bewurzelung | 0:0:0 (kein Dünger) | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — |
| Juvenil | 3:1:2 (halbe Dosis) | 0.4–0.6 | 6.0–6.5 | 40–60 | 20–30 | 1–2 | 0.25–0.5 | 0.025–0.05 | 0.01–0.02 | 0.005–0.01 |
| Aktives Wachstum | 3:1:2 | 0.6–0.8 | 6.0–6.5 | 80–100 | 30–50 | 2–3 | 0.5 | 0.05 | 0.02 | 0.01 |
| Dormanz | 0:0:0 (keine Düngung) | 0.0 | 6.0–6.5 | — | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Die Werte für Mn/Zn/Cu/Mo (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`) orientieren sich an der Standard-Hoagland-Vollnährlösung (Mn 0,5 / Zn 0,05 / Cu 0,02 / Mo 0,01 ppm) und sind für die schwachzehrende *Dracaena* (light_feeder) in der Juvenilphase auf etwa halbe Konzentration reduziert. In handelsüblichen Volldüngern sind diese Spurenelemente bereits chelatiert enthalten; eine separate Gabe ist nur bei reiner Salz-/Osmosewasser-Rezeptur nötig. (Quelle 22)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


**Fluorid-Warnung (kritisch für Dracaena):** Beide Arten sind extrem fluoridempfindlich. Fluorid ab 0,25 ppm (wie in vielen Kommunalwassern auf 1 ppm dosiert) verursacht Blattspitzenverbrennung (Tip Burn) und Blattflecken. Daher:
- Kein Leitungswasser direkt verwenden — 24 h abstehen lassen oder Regenwasser/gefiltertes Wasser benutzen
- Keine Dünger mit Superphosphat (enthält Fluorid als Verunreinigung)
- Kein fluoridiertes Substrat (z. B. vermeiden: manche Perlite-Typen mit Flussmittelrückständen)
- Substrat-pH nicht unter 6,0 senken: bei saurem pH wird gebundenes Fluorid mobilisiert

---

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/Bedingung | Hinweise |
|------------|---------|----------------|----------|
| Bewurzelung → Juvenil | time_based | 28–56 Tage | Sichtbares Wurzelwachstum (Drainage), erste neue Blätter |
| Juvenil → Aktives Wachstum | time_based / seasonal | 90–180 Tage bzw. Monat März | Pflanze akklimatisiert, Tageslänge nimmt zu |
| Aktives Wachstum → Dormanz | seasonal | Monat Oktober | Tageslänge sinkt unter 11 h, Heizperiode beginnt |
| Dormanz → Aktives Wachstum | seasonal | Monat März | Tageslänge über 12 h, Temperaturen steigen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Zimmerpflanze / Topfkultur)

| Produkt | Marke | Typ | NPK | Empf. Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------------|----------------|--------|
| Zimmerpflanzendünger flüssig | Compo Sana | base | 7-3-6 | 5 ml/1 L Wasser, halbiert (2,5 ml/L) | 3 | Aktives Wachstum |
| Grünpflanzendünger | Substral | base | 7-2-7 | 5 ml/1 L Wasser, halbiert | 3 | Aktives Wachstum |
| Natrium- und fluoridfreier Flüssigdünger (urea-free) | Düngerform wählen: z. B. Green24 | base | 5-2-3 (oder ähnl.) | 2–3 ml/L | 3 | Aktives Wachstum |
| CalMag-Supplement | Canna CalMag Agent | supplement | — | 0,5–1,0 ml/L (nur bei Osmosewasser oder sehr weichem Leitungswasser) | 2 | Aktives Wachstum |

**Wichtig:** Dünger nur auf halbierter Empfehldosis anwenden (light_feeder). Kein Dünger in der Dormanz (Oktober–Februar) und in den ersten 6–8 Wochen nach dem Einpflanzen.

#### Organisch (Zimmerpflanze / Topfkultur)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Wurmhumus-Flüssigkeit | Plagron Pure Enzymes oder Eisenia-Fetida-Auszug | organisch | 5–10 ml/L, alle 4–6 Wochen | März–September | light_feeder |
| Langzeitdünger Stick (fluoridarm) | Compo Bio Düngestäbchen | organisch | 1 Stäbchen/10 cm Topfdurchmesser | einmalig im März | Aktives Wachstum |
| Bokashi-Flüssiganwendung | EM Chiemgau EM-Aktiv | organisch | 1:100 verdünnt | März–August | alle Topfpflanzen |
| Komposttee (hausgemacht) | — | organisch | 1:10 verdünnt, 1× im Monat | März–September | alle Topfpflanzen |

---

### 3.2 Düngungsplan (Zimmerpflanze, Jahresverlauf)

| Monat | Phase | Dosierung | Produkt-Empfehlung | Hinweise |
|-------|-------|-----------|-------------------|----------|
| Jan–Feb | Dormanz | Kein Dünger | — | Absolut keine Düngung — Salzakkumulation gefährdet Wurzeln |
| März | Übergang | 25 % Normaldosis | 1 Stäbchen ODER 1,5 ml/L Flüssig | Erste Düngung der Saison, vorsichtig |
| Apr–Jun | Aktives Wachstum | 50 % Normaldosis, alle 4 Wochen | Flüssigdünger 2,5 ml/L | Hauptwachstumsphase, regelmäßig kontrollieren |
| Jul–Aug | Aktives Wachstum | 50 % Normaldosis, alle 4 Wochen | Flüssigdünger 2,5 ml/L | Bei Hitze Düngung pausieren wenn Pflanze gestresst wirkt |
| Sep | Übergang | 25 % Normaldosis | Letzte Düngung der Saison | Düngung ausleiten |
| Okt–Dez | Dormanz | Kein Dünger | — | Ruhephase strikt einhalten |

---

### 3.3 Mischungsreihenfolge

> **Kritisch bei Verwendung von Flüssigdünger + CalMag:** Reihenfolge verhindert Ausfällungen

1. Leitungswasser 24 h abstehen lassen (Chlor ausgasen, Fluorid sedimentiert teilweise)
2. CalMag einrühren (falls Osmose/weiches Wasser)
3. Flüssigdünger einrühren
4. pH kontrollieren und falls nötig mit pH-Down (Phosphorsäurefrei) oder pH-Up korrigieren (Ziel: pH 6,0–6,5)
5. EC messen: Ziel-EC 0,6–0,8 mS/cm (inkl. Basiswasser)

---

### 3.4 Besondere Hinweise zur Düngung

**Fluorid-Problematik (artspezifisch, wichtig!):**
Dracaena spp. sind unter allen Zimmerpflanzen besonders anfällig für Fluoridherbstizid. Schäden zeigen sich als braune, eingetrocknete Blattspitzen (Tip Burn) und Chlorosen. Die Ursache wird häufig als Wassermangel fehldiagnostiziert. Abhilfe: Destilliertes Wasser, Regenwasser oder 24 h abgestandenes Leitungswasser verwenden; keinen Superphosphat-haltigen Dünger einsetzen; Substrat-pH über 6,0 halten.

**Überdüngung:** Dracaena reagiert empfindlich auf Salzakkumulation. Symptome: braune Ränder, gelbliche Blätter, weiße Salzkrusten auf der Erde. Abhilfe: Substrat alle 6 Monate mit Wasser durchspülen (Flush), dann trocknen lassen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0× (→ 14–21 Tage im Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Fluoridempfindlich! Regenwasser, gefiltertes oder mind. 24 h abgestandenes Leitungswasser verwenden. Kein frisches Leitungswasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 (alle 2–3 Jahre, nur wenn durchwurzelt) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 (im Winter alle 7 Tage wegen Spinnmilbengefahr bei Heizungsluft) | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

**Gießmethode — Anleitung:** Von oben mit abgestandenem Wasser gießen, bis etwas aus den Drainagelöchern läuft. Überschuss im Untersetzer nach 30 Minuten wegkippen. Niemals Staunässe stehen lassen — die häufigste Todesursache ist Wurzelfäule durch dauerhaft nasses Substrat.

---

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Schädlingskontrolle | Wöchentliche Inspektion auf Spinnmilben (Unterseite Blätter); Heizungsluft erhöht Befallsrisiko stark | hoch |
| Jan | Lichtoptimierung | Pflanze an hellsten Standort (Südwest-/Südfenster) stellen, ggf. Pflanzenlampe | mittel |
| Feb | Substrat-Check | Erde auf Salzkrusten und Compaction prüfen; ggf. Flush vorbereiten | niedrig |
| Mär | Erste Düngung | Saison-Start mit 25 % Dosis; Gießintervall vorsichtig verkürzen auf 10 Tage | hoch |
| Mär | Rückschnitt | Falls Pflanze zu lang/kahl: Stämme auf gewünschte Höhe kürzen; Schnittlinge als Stecklinge verwenden | mittel |
| Apr | Umtopfen (falls fällig) | Nur wenn Wurzeln aus Drainagelöchern wachsen; Topf nur 2–4 cm größer wählen | mittel |
| Apr | Standort wechseln | Heller Standort ohne direkte Mittagssonne; Balkon ab Anfang Mai möglich (keine Nächte unter 12 °C) | mittel |
| Mai–Jun | Vollbetrieb Pflege | Gießen alle 7 Tage; Düngen alle 4 Wochen (50 %); Schädlingskontrolle alle 14 Tage | hoch |
| Jul–Aug | Hitzeschutz | Bei über 32 °C Direktsonne vermeiden; Luftfeuchtigkeit durch Versprühen oder Luftbefeuchter erhöhen | mittel |
| Sep | Herbst-Vorbereitung | Letzte Düngung der Saison; Pflanze vor Heizungsbeginn von Zugluft und Heizungsnähe fernhalten | hoch |
| Okt | Überwintern einleiten | Keine Düngung mehr; Gießintervall auf 14–21 Tage reduzieren; Schädlingskontrolle intensivieren | hoch |
| Nov–Dez | Winterpflege | Gießen minimal; keine Düngung; Luftfeuchtigkeit regelmäßig messen (Ziel: >40 %) | mittel |

---

### 4.3 Überwinterung

Dracaena spp. sind vollständig frostunverträglich (tender) und verbringen den Winter als Zimmerpflanze in beheizten Räumen. Eine gesonderte Einlagerung oder ein Kaltquartier ist nicht nötig, aber bestimmte Winterbedingungen können der Pflanze schaden.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 (UI-Ampelfarbe entfernt; hardiness_rating ist maßgeblich) -->
| Winterhärte-Einstufung | frost_free — muss frostfrei (≥ 12 °C) im beheizten Innenraum überwintern; keinerlei Frosttoleranz | `overwintering_profiles.hardiness_rating` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme | none (Pflanze bleibt drinnen) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off (Balkon erst ab stabilen Nacht-Temp. >12 °C) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 12 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 22 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright (hellster verfügbarer Standort) | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced (alle 14–21 Tage; obere 75 % Substrat vollständig trocken) | `overwintering_profiles.winter_watering` |

**Winterprobleme und Gegenmaßnahmen:**
- **Heizungsluft (Hauptproblem):** Trockene Raumluft (<30 % rLF) begünstigt Spinnmilbenbefall und Blattspitzenbräunung massiv. Luftbefeuchter oder Schale mit Kieselsteinen und Wasser neben die Pflanze stellen. Regelmäßiges Absprühen der Blätter.
- **Zugluft:** Pflanze nicht neben schlecht isolierte Fenster oder Türen stellen; kurzzeitiger Kälteschock unter 10 °C schädigt Blätter dauerhaft.
- **Kalter Fensterbankstein:** Unterlage (z. B. Korkplatten) zwischen Topf und kaltem Stein; Wurzeln unter 10 °C stellen die Wasseraufnahme ein.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste unter Blättern, blasse/gelbgesprenkelte Flecken, Blattverlust bei schwerem Befall | leaf | Dormanz (Heizungsluft) | medium |
| Wollläuse | Pseudococcus longispinus / Planococcus citri | Watteähnliche weiße Wollknäuel in Blattachseln und auf Stammoberflächen, Honigtau | stem, leaf | Aktives Wachstum, Juvenil | medium |
| Schildläuse (Weichschild) | Coccus hesperidum | Braune, wachsartige Schilde auf Stämmen und Blattstielen; Honigtau, Rußtau | stem, leaf | alle | hard |
| Schildläuse (Hartschild) | Diaspis boisduvalii | Graue bis weiße Schildchen auf Stämmen; keine Honigtauproduktion | stem | alle | hard |
| Trauermücken (Larven) | Bradysia spp. | Larven fressen Feinwurzeln; Adulte als kleine schwarze Fliegen sichtbar; Pflanzenstress | root | Bewurzelung, Juvenil | easy (Adulte) / hard (Larven) |
| Thripse | Frankliniella occidentalis | Silbrige Schabespuren auf Blättern, schwarze Kotpunkte, Blattdeformationen | leaf | Aktives Wachstum | medium |

---

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Fusarium-Blattflecken | fungal (*Fusarium moniliforme*) | Wassergetränkte, dann rötlich-braune Flecken hauptsächlich auf Jungblättern; gelbe Ränder möglich | Staunässe, schlechte Belüftung, verletztes Gewebe | 5–14 | Juvenil, Aktives Wachstum |
| Weiche Stängelstängelfäule | bacterial (*Erwinia carotovora*) | Weiche, übelriechende, braune bis schwarze Faulstellen an Stammbasis; Pflanze kollabiert | chronische Überwässerung, Wunden | 3–10 | alle |
| Pythium-Wurzelfäule | fungal (*Pythium* spp.) | Wurzeln braun-schwarz, wässrig, übelriechend; Pflanze welkt trotz feuchtem Substrat | Staunässe, schlechte Drainage | 7–14 | Bewurzelung, Juvenil |
| Blattspitzenverbrennung / Tip Burn | physiologisch | Braun-trockene Blattspitzen; keine Faulnis | Fluorid im Gießwasser, Salzakkumulation, zu trockene Luft | sofort–14 | alle |
| Echter Bakterienblattfleck | bacterial (*Xanthomonas* spp.) | Ölfleckige, wassergetränkte Flecken die sich braun verfärben; gelber Halo | Überkopfbewässerung, Verwundungen | 5–14 | Aktives Wachstum |

---

### 5.3 Nützlinge (Biologische Bekämpfung — Zimmerpflanze)

| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit (Tage) |
|----------|---------------|-------------|------------------------|
| *Phytoseiulus persimilis* (Raubmilbe) | Spinnmilbe (*T. urticae*) | 5–10 Individuen/Pflanze | 14–21 |
| *Amblyseius californicus* (Raubmilbe) | Spinnmilbe (breites Temperaturspektrum, auch im Winter) | 5–10 Individuen/Pflanze | 14–21 |
| *Amblyseius cucumeris* (Raubmilbe) | Thripse (Larven), Weichhaut-Milben | 10–20 Individuen/Pflanze | 14–21 |
| *Cryptolaemus montrouzieri* (Australischer Marienkäfer) | Wollläuse | 2–5 Adulte/Pflanze | 21–42 |
| *Steinernema feltiae* (Nematoden) | Trauermückenlarven (Bradysia spp.) | 0,5 Mio. Nematoden/m² Topffläche, in Gießwasser | 7–14 |

**Hinweis zu Nützlingen in Zimmerkultur:** Raubmilben und -insekten sind für die Zimmerpflanzenpflege geeignet, wenn die Pflanze in einem Raum mit ausreichend Luftfeuchtigkeit steht. *P. persimilis* benötigt min. 60 % rLF. Alternativ: *A. californicus* übersteht auch trockenere Bedingungen.

---

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Absprühen mit Wasser (kräftiger Strahl) | cultural | — | Blätter-Unterseiten mit Druck absprühen | 0 | Spinnmilben (Frühinfektion) |
| Neemöl-Spray | biological | Azadirachtin | 1–2 % Neemöl-Emulsion (+ Tensid), wöchentlich 3× | 0 (Zierpflanze) | Spinnmilben, Wollläuse, Thripse, Schilde (weich) |
| Insektizide Seife | biological | Kaliseife | 1–2 % Lösung, direkt auf Schädlinge, 3× im Abstand von 7 Tagen | 0 (Zierpflanze) | Wollläuse, Thripse, Blattläuse |
| Spiritus (70 %)-Wattestäbchen | mechanical | — | Direkt auf Wollläuse/Schildläuse tupfen | 0 | Wollläuse, Schildläuse |
| Bacillus thuringiensis israelensis (Bti) | biological | Bti-Toxin | In Gießwasser (z. B. Gnatrol WDG, nach Anleitung) | 0 | Trauermückenlarven |
| Kupferhaltiges Fungizid (z. B. Cuprozin) | chemical | Kupferhydroxid | Sprühen auf befallene Stellen; Zierpflanzeneinsatz prüfen | 7–14 | Bakterien-Blattflecken |
| Bacillus subtilis-Präparat (z. B. Serenade) | biological | Bacillus subtilis QST 713 | Sprühen oder Gießen | 0 | Fusarium, Pythium (vorbeugend) |
| Gelbe Klebefallen | mechanical | — | Aufhängen nahe der Pflanze; 1 Falle/Pflanze | 0 | Trauermücken (Adulte), Thripse (Monitoring) |
| Kieselgur (Diatomit) | mechanical | Siliziumdioxid | Auf Substratoberfläche streuen (trocken halten) | 0 | Trauermücken, Bodenmilben |

---

### 5.5 Resistenzen der Art

Dracaena spp. gelten nicht als resistent gegen spezifische Schädlinge oder Pathogene. Folgende Empfindlichkeiten sind dokumentiert:

| Erhöhte Empfindlichkeit gegen | Typ | KA-Edge |
|------------------------------|-----|---------|
| Spinnmilbe (*Tetranychus urticae*) bei trockener Luft | Schädling | `vulnerable_to` |
| Fluoridtoxizität | physiologisch | — |
| Staunässefäule (*Pythium*, *Erwinia*) | Krankheit | `vulnerable_to` |
| Fusarium-Blattflecken (*Fusarium moniliforme*) | Krankheit | `vulnerable_to` |

---

## 6. Mischkultur & Zimmerpflanzen-Kombinationen

Klassische Freiland-Mischkulturregeln (Fruchtfolge, Stickstoffversorgung) gelten für Zimmerpflanzen nicht. Im Zimmerpflanzenkontext meint „Mischkultur" die Kombination verschiedener Arten in einem Pflanztopf oder die räumliche Aufstellung, die Schädlingsdruck, Pflegeaufwand und ästhetische Harmonie beeinflusst.

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer (light_feeder) |
| Fruchtfolge-Kategorie | nicht relevant (Dauerzimmerpflanze) |
| Empfohlene Vorfrucht | nicht relevant |
| Empfohlene Nachfrucht | nicht relevant |
| Anbaupause (Jahre) | nicht relevant |

---

### 6.2 Zimmerpflanzen-Kombinationen — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen / Begründung | KA-Edge |
|---------|-------------------|----------------------|---------------------|---------|
| Efeutute | Epipremnum aureum | 0.9 | Gleiche Licht- und Wasserbedürfnisse; kaskadierender Wuchs ergänzt aufrechte Dracaena ästhetisch; toleriert gleiche Vernachlässigung | `compatible_with` |
| Einblatt | Spathiphyllum wallisii | 0.8 | Ähnliche Temperatur- und Feuchtigkeitsansprüche; Einblatt signalisiert durch Hängen Wasserbedarf zuverlässig (als Gießindikator nutzbar) | `compatible_with` |
| Philodendron | Philodendron hederaceum | 0.85 | Gleiche Substrat- und Pflegelogik; beide sind light_feeder und reagieren ähnlich auf Überdüngung; ähnlicher Pflege-Stil tropical | `compatible_with` |
| Bogenhanf | Sansevieria trifasciata (Dracaena trifasciata) | 0.75 | Eng verwandt (gleiche Familie, gleiche Gattung nach neuem APG); ästhetische Kombinationen populär; Bogenhanf verträgt sogar noch mehr Trockenheit, daher bei Mischpflanzung separat gießen | `compatible_with` |
| Grünlilie | Chlorophytum comosum | 0.8 | Zeigerpflanze für Luftqualität; ähnliche Bedürfnisse; Spinnmilbenresistenz von Grünlilien kann benachbarte Dracaena schützen (anekdotisch) | `compatible_with` |

---

### 6.3 Zimmerpflanzen-Kombinationen — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kakteen / Echeveria | Cactaceae, Echeveria spp. | Grundlegend unterschiedliche Gießbedürfnisse — Dracaena benötigt deutlich mehr Wasser; Mischgefäß führt entweder zu Wurzelfäule der Dracaena oder Übertrocknung des Kaktus | severe | `incompatible_with` |
| Farne (z. B. Nephrolepis) | Nephrolepis exaltata | Farne bevorzugen gleichmäßig feuchtes Substrat und sehr hohe Luftfeuchtigkeit (>70 %); Dracaena braucht regelmäßige Austrocknung; zudem können Farne Trauermücken-Reservoir sein | moderate | `incompatible_with` |
| Orchideen | Phalaenopsis spp. | Orchideen benötigen ein spezifisches Orchideensubstrat (durchlässig, luftig) und das Tauchbad-Gießverfahren; Substrate und Gießrhythmus sind inkompatibel | moderate | `incompatible_with` |
| Oleander | Nerium oleander | Stark giftig; gemeinsame Aufstellung im Haushalt mit Kindern und Haustieren nicht empfehlenswert; keine direkte Pflegeinkompatibilität, aber Sicherheitsrisiko | moderate | `incompatible_with` |

---

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Asparagaceae (Sansevieria, Agave, Cordyline) | `shares_pest_risk` | Spinnmilben (*T. urticae*), Wollläuse (*Pseudococcus* spp.), Schildläuse — Monitoring für alle Gattungen gemeinsam | `shares_pest_risk` |
| Araceae (Philodendron, Monstera, Epipremnum) | `compatible_with` | Gleicher Schädlingsdruck; geteiltes Monitoring sinnvoll | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber D. marginata / D. fragrans |
|-----|-------------------|-------------|----------------------------------------------|
| Bogenhanf / Schwiegermutterzunge | Dracaena trifasciata (syn. Sansevieria trifasciata) | Gleiche Gattung (seit 2017); robustabler, noch trockenheitstoleranter | Ideale Alternative für Einsteiger oder Vergessliche; übersteht auch 3–4 Wochen ohne Gießen |
| Yuccapalme | Yucca elephantipes | Vergleichbares Erscheinungsbild (aufrecht, schwertblättrig); Asparagaceae | Noch trockenheitstoleranter; für sonnenreiche Standorte besser geeignet; nicht giftig |
| Cordyline | Cordyline australis | Eng verwandt, früher als Dracaena klassifiziert; ähnliche Pflegebedürfnisse | Mehr Farbvarianten (Purpur, Rosa); für Balkonkultur geeigneter |
| Schefflera / Strahlenaralie | Schefflera arboricola | Baumartig wie D. fragrans; deutlich breitere Krone | Schnellwüchsiger; ideal wenn mehr Volumen gewünscht; ähnliche Pflegekategorie `tropical` |
| Kentia-Palme | Howea forsteriana | Ähnliche Raumsituation (hoch, dekorativ, schattenverträglich) | Klassische Zimmerpalme, nicht giftig; ideal für Haushalte mit Haustieren |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeilen

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,frost_sensitivity,allelopathy_score,native_habitat,nutrient_demand_level,green_manure_suitable,pruning_type,pruning_months,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,traits,air_purification_score,removes_compounds
Dracaena marginata,"Drachenbaum;Rotkantiger Drachenbaum;Dragon Tree;Madagascar Dragon Tree",Asparagaceae,Dracaena,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b;12a;12b",tender,0.0,"Madagaskar",light_feeder,false,spring_pruning,"3;4",yes,"5;15",20,"100;300","40;100",60,yes,limited,false,false,ornamental,0.7,"formaldehyde;benzene;xylene;trichloroethylene"
Dracaena fragrans,"Duftdracaena;Maispalme;Corn Plant;Mass Cane",Asparagaceae,Dracaena,perennial,day_neutral,tree,fibrous,"10b;11a;11b;12a;12b",tender,0.0,"Tropisches Afrika",light_feeder,false,spring_pruning,"3;4",yes,"10;30",20,"150;300","50;100",80,yes,limited,false,false,"ornamental;fragrant",0.75,"formaldehyde;benzene;trichloroethylene"
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,breeder,breeding_year,traits,seed_type,notes
Tricolor,Dracaena marginata,–,–,"ornamental;variegated",open_pollinated,"Grüne Blätter mit gelben und roten Streifen; kompakter als Grundart"
Colorama,Dracaena marginata,–,–,"ornamental;variegated;red_dominant",open_pollinated,"Überwiegend rote/weinrote Blätter mit grünem Mittelstreifen; kräftigere Farbe"
Bicolor,Dracaena marginata,–,–,"ornamental;variegated",open_pollinated,"Grün-rote Blattfärbung, zweifarbig"
Massangeana,Dracaena fragrans,–,–,"ornamental;variegated;yellow_stripe",open_pollinated,"Heller Gelb-Streifen in Blattmitte; häufigste Handelsvariante (~90 % aller D. fragrans)"
Janet Craig,Dracaena fragrans,–,–,"ornamental;dark_green;compact",open_pollinated,"Breite, dunkelgrüne glänzende Blätter ohne Streifung; robuste Büroform"
Lemon Lime,Dracaena fragrans,–,–,"ornamental;variegated;yellow_green",open_pollinated,"Hellgrüne und gelbliche Streifenmusterung; leuchtend frische Optik"
Warneckii,Dracaena fragrans,–,–,"ornamental;variegated;white_stripe",open_pollinated,"Grüne Blätter mit weißen Randstreifen; schattentoleranter als andere Formen"
```

---

## 9. Diagnosetabelle — Symptome und Sofortmaßnahmen

Diese Tabelle dient als Schnell-Referenz für die häufigsten Probleme bei Dracaena in der Zimmerkultur.

| Symptom | Mögliche Ursachen (nach Wahrscheinlichkeit) | Sofortmaßnahme | Langfristige Maßnahme |
|---------|---------------------------------------------|----------------|----------------------|
| Braune, trockene Blattspitzen | 1. Fluorid/Chlor im Wasser; 2. Salzakkumulation; 3. Zu trockene Luft; 4. Zugluft | Gießwasser wechseln auf abgestandenes/gefiltertes Wasser; Luftfeuchtigkeit erhöhen | Substrat alle 6 Monate durchspülen (Flush); Raumluft-Feuchter aufstellen; Pflanze von Heizung fernhalten |
| Gelbe Blätter (untere/mittlere) | 1. Überwässerung (häufigste Ursache); 2. Normales Altern (älteste Blätter); 3. Staunässe | Gießrhythmus prüfen: Substrat muss oben 50–75 % trocken sein; gelbe Blätter entfernen | Substrat auf Drainage prüfen; ggf. umtopfen in durchlässigere Mischung |
| Gelbe Blätter (alle/jung) | 1. Überdüngung; 2. Wurzelfäule; 3. Zu wenig Licht | Düngung sofort stoppen; Substrat und Wurzeln kontrollieren | Bei Wurzelfäule: Faulendes entfernen, frisches Substrat, Bewurzelung-Phase neu starten |
| Weiche/faulige Stammbase | 1. Bakterienfäule (*Erwinia*); 2. *Pythium*-Wurzelfäule | Befallenen Bereich mit scharfem, desinfiziertem Messer entfernen; trocknen lassen; Kupferfungizid | Gießverhalten fundamental ändern; niemals Staunässe; ggf. Steckling retten bevor Pflanze stirbt |
| Weiße watteartige Flecken (Achseln) | Wollläuse (*Pseudococcus* spp.) | Mit 70 % Alkohol getränktem Wattestäbchen abtupfen; alle Achseln systematisch durcharbeiten | 3× wöchentlich Neemöl-Spray; *Cryptolaemus*-Nützlinge einsetzen; Pflanze isolieren |
| Feine Gespinste, gelbe Sprenkelung | Spinnmilben (*Tetranychus urticae*) | Blätter kräftig abbrausen; Luftfeuchtigkeit sofort auf >60 % erhöhen | Raubmilben (*Phytoseiulus* oder *Amblyseius*) einsetzen; Heizungsluft dauerhaft befeuchten |
| Braune Schilde/Wachsplatten auf Stamm | Schildläuse (*Coccus hesperidum*, *Diaspis* spp.) | Schildläuse mechanisch mit Bürste oder Tuch entfernen; danach Spiritus abtupfen | Neemöl-Spray 3× im Wochenabstand; hartnäckige Fälle: systemisches Insektizid (Imidacloprid — Zierpflanze, Innenraum, Fenster geschlossen) |
| Winzige schwarze Fliegen, Pflanzenstress | Trauermücken (*Bradysia* spp.) | Gelbe Klebefallen aufstellen; Substrat an der Oberfläche austrocknen lassen | *Steinernema feltiae*-Nematoden in Gießwasser; Kieselgur auf Substrat; weniger gießen |
| Wassergetränkte Flecken, Jungblätter | Fusarium-Blattflecken | Befallene Blätter entfernen; Pflanze trockener stellen; Luftzirkulation verbessern | Bacillus-subtilis-Präparat (Serenade) als vorbeugende Behandlung; keine Überkopfbewässerung |
| Pflanze welkt trotz feuchtem Substrat | Wurzelfäule (*Pythium*); Salzstress | Topf aus der Erde nehmen; Wurzeln begutachten; braune/faulige Wurzeln abschneiden; trocknen lassen | Umtopfen in frisches, durchlässiges Substrat; Gießrhythmus drastisch reduzieren |
| Blätter rollen sich ein, hängen | 1. Wassermangel; 2. Kälteschock; 3. Zugluft | Gießen prüfen; Standort kontrollieren (Fenster, Klimaanlage, Heizung) | Regelmäßigere Gießintervalle einhalten; Pflanze vor Zugluft schützen |
| Stammverlängerung ohne Blätter (Etiolierung) | Zu wenig Licht | Pflanze an helleren Standort stellen | Bei stark vergeilten Trieben: Rückschnitt im Frühjahr; Triebe als Stecklinge verwenden |

---

## Quellenverzeichnis

1. [USDA Plants Database — Dracaena marginata](https://plants.usda.gov/plant-profile/DRMA8) — Taxonomie, Hardiness Zones
2. [Missouri Botanical Garden Plant Finder — Dracaena marginata](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=b592) — Kulturanforderungen, Hardiness
3. [NC State Extension — Dracaena fragrans](https://plants.ces.ncsu.edu/plants/dracaena-fragrans/) — Morphologie, Kultivare, Toxizität
4. [Penn State Extension — Dracaena Diseases](https://extension.psu.edu/dracaena-diseases) — Krankheitsbilder, Fusarium, Bakterienfäule
5. [ASPCA Animal Poison Control — Dracaena](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/dracaena) — Toxizität Katzen/Hunde, Saponine
6. [Gardener's Path — How to Identify and Treat 9 Dracaena Diseases](https://gardenerspath.com/plants/houseplants/dracaena-diseases/) — Krankheitsdiagnose und Behandlung
7. [Gardening Know How — Common Pests Of Dracaena Plants](https://www.gardeningknowhow.com/houseplants/dracaena/dracaena-pest-control.htm) — Schädlingsübersicht und IPM
8. [Gardening Know How — Container Planting With Dracaena](https://www.gardeningknowhow.com/houseplants/dracaena/potted-dracaena-companions.htm) — Companion Planting Zimmerpflanzen
9. [Plants For All Seasons — Dracaena diseases and pests](https://www.plantsforallseasons.co.uk/blogs/dracaena-care/common-dracaena-diseases-and-pests-to-look-out-for) — Krankheitsbilder
10. [Pacific Northwest Pest Management Handbooks — Dracaena Tip Burn](https://pnwhandbooks.org/plantdisease/host-disease/dracaena-tip-burn) — Fluoridtoxizität, physiologische Störungen
11. [Wolverton, B.C. et al. (1989) — NASA Clean Air Study](https://en.wikipedia.org/wiki/NASA_Clean_Air_Study) — Luftreinigungswirkung; Caveat: Cummings & Waring (2020) relativieren den praktischen Nutzen bei normaler Raumventilation
12. [Bloomscape — Dracaena Care Guide](https://bloomscape.com/plant-care-guide/dracaena/) — Allgemeine Pflege, Temperaturen, Luftfeuchtigkeit
13. [Gardenia.net — Dracaena marginata](https://www.gardenia.net/plant/dracaena-marginata-dragon-tree) — Kulturdaten, Sorten, USDA Zones
14. [Wikipedia — Dracaena fragrans](https://en.wikipedia.org/wiki/Dracaena_fragrans) — Taxonomie, Heimat, Synonyme
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
15. [ScienceDirect — Light green leaf sectors of variegated *Dracaena fragrans* show similar rates of oxygenic photosynthesis (Journal of Plant Physiology 2024)](https://www.sciencedirect.com/science/article/abs/pii/S0981942824007083) — Netto-CO₂-Assimilation / Gaswechsel belegt C3-Photosynthese bei *D. fragrans* (Abgrenzung zu CAM)
16. [UF/IFAS Environmental Horticulture — *Dracaena marginata* Fact Sheet (FPS-185)](https://hort.ifas.ufl.edu/database/documents/pdf/shrub_fact_sheets/dramara.pdf) — geringe Salztoleranz („poor salt tolerance"), Licht/Schatten, Trockenheitstoleranz, Wuchshöhe
17. [Plants For All Seasons — Dracaena sunlight requirements: A complete guide](https://www.plantsforallseasons.co.uk/blogs/dracaena-care/dracaena-sunlight-requirements-a-complete-guide) — Schattentoleranz, indirektes Licht, Naturhabitat unter Kronendach, ~100 fc Minimum
18. [Frontiers in Plant Science (2023) — Method for selecting ornamental species for different shading intensity in urban green spaces](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1271341/full) — Lichtkompensationspunkte schattentoleranter Zierarten (10–15 µmol/m²/s für *Chlorophytum*, *Epipremnum*, *Ficus benjamina*)
19. [Conover, C.A. & Poole, R.T. (1984) — Acclimatization of Indoor Foliage Plants, Horticultural Reviews 6:119–154](https://onlinelibrary.wiley.com/doi/10.1002/9781118060797.ch4) — niedrige LCPs schattentoleranter Foliage-Pflanzen, Akklimatisierung von *Dracaena*
20. [PNW Pest Management Handbooks — Dracaena Tip Burn](https://pnwhandbooks.org/plantdisease/host-disease/dracaena-tip-burn) — Salz-/Fluoridakkumulation, Substrat-ECe-Bezug, physiologische Blattspitzenbräunung
21. [Cafe Planta — The Dangers of Overwatering Dracaena: Waterlogged Roots](https://cafeplanta.com/a/blog/the-dangers-of-overwatering-dracaena-how-to-prevent-waterlogged-roots) — Staunässeempfindlichkeit, Sauerstoffmangel der Wurzeln, Wurzelfäule (*Pythium*/*Erwinia*)
22. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Standard-Mikronährstoffkonzentrationen (Mn 0,5 / Zn 0,05 / Cu 0,02 / Mo 0,01 ppm) als Referenz für §2.3
23. [Yamori, W. et al. (2014) — Temperature response of photosynthesis in C3, C4, and CAM plants, Photosynthesis Research 119:101–117](https://link.springer.com/article/10.1007/s11120-013-9874-6) — Photosynthese-Temperaturoptimum tropischer C3-Pflanzen (Grundlage T_opt 25–30 °C)
24. [Foliage Friend — How Long Do Dracaena Plants Live](https://foliagefriend.com/how-long-do-dracaena-plants-live/) — Lebensdauer indoor 10–15 Jahre typisch, mehrere Jahrzehnte möglich
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
