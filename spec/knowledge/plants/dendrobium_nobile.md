# Dendrobium-Orchidee, Edle Dendrobie — Dendrobium nobile

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/dendrobium-nobile-orchid-care/), [Gardening Know How](https://www.gardeningknowhow.com/ornamental/orchids/dendrobium-nobile-orchid-care), [UK Houseplants](https://www.ukhouseplants.com/plants/dendrobiums), [Carter & Holmes](https://www.carterandholmes.com/pages/dendrobium-nobile-and-ise-care-sheet), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dendrobium nobile | `species.scientific_name` |
| Synonyme | Dendrobium nobile var. nobilius (Cultivare im Handel sind meist Hybriden) | — |
| Volksnamen (DE/EN) | Dendrobium-Orchidee, Edle Dendrobie, Bambusorchidee; Noble Dendrobium, Noble Rock Orchid | `species.common_names` |
| Familie | Orchidaceae | `species.family` → `botanical_families.name` |
| Gattung | Dendrobium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (base temp, °C) | <!-- DATEN FEHLEN --> kein belegter phänologischer Wuchs-/GDD-Basiswert für diese tropisch-subtropische Epiphytenart auffindbar; Blühsteuerung erfolgt nicht über Wärmesummen, sondern über Kühlphase (Vernalisation/Chilling) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Kühl-/Vernalisationsphase; in der Nobile-Dendrobium-Literatur als "vernalization" geführt, physiologisch Kältereiz zur Blühinduktion) | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage (min days) | 21–42 (≥ 3 Wochen bei 13–15 °C bzw. 2–6 Wochen bei ~10 °C, kultivarabhängig) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral; Blühinduktion temperatur-, nicht photoperiodengesteuert — keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Kühle Herbst-/Wintertemperaturen (7–15°C) sind für Blütenbildung obligat — ohne Kühlung keine Blüten. | `species.hardiness_detail` |
| Heimat | Nepal, Indien, China, Myanmar, Thailand — Himalaya-Ausläufer, felsige Standorte, Epiphyt | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Dendrobium nobile ist nach Phalaenopsis die zweitbekannteste Zimmerpflanze-Orchidee und unterscheidet sich grundlegend in der Kultur: Sie bildet sympodiale Bulben (Pseudobulben) und benötigt im Herbst/Winter eine ausgeprägte Kühlphase (7–15°C) mit reduzierter Bewässerung — nur dann blüht sie verlässlich im Winter/Frühjahr. Im Handel sind fast ausschließlich Hybridkultivare erhältlich, die etwas robuster als die Wildart sind. Die Blüten erscheinen entlang der Bulben, nicht auf einzelnen Blütenstielen wie bei Phalaenopsis.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 1, 2, 3, 4 (Hauptblütezeit Winter/Frühjahr nach Kühlung) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung alter Bulbenstöcke beim Umtopfen — jede Sektion mit mindestens 2–3 Bulben. Keiki (Ableger auf der Bulbe) können abgetrennt und eingetopft werden sobald eigene Wurzeln entwickelt sind (mind. 3 cm Wurzellänge).

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
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 (verblühte Bulben können nach Blüte belassen werden) | `species.pruning_months` |

**Hinweis:** Alte Bulben NICHT abschneiden — sie dienen als Nährstoffspeicher und können Keiki (Jungpflanzen) entwickeln. Nur wenn Bulben vollständig eingetrocknet sind, können sie entfernt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 (kleine Töpfe) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, nach Eisheiligen, halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Orchidenbark-Mix (grobkörnig). pH 5.5–6.5. Kleine Töpfe bevorzugt — eng eingetopft blüht Dendrobium besser. Niemals normale Einheitserde. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 8–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe, dS/m) | 2.0 | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-Slope für Dendrobium auffindbar | `species.salt_tolerance_slope_pct` |
| Boden-/Substrat-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis (LCP):** Als CAM-Epiphyt liegt der Lichtkompensationspunkt niedrig (Netto-Photosynthese = 0 bei ~5–20 µmol/m²/s, wie für CAM-Orchideen typisch). Davon zu trennen sind Sättigungs-/Photoinhibitions-Werte: In Kultur sind 200–500 µmol/m²/s das Optimum (siehe §2.2); ab ~1000 µmol/m²/s wird die nächtliche Stomataöffnung (CAM) gehemmt, im Hochsommer drohen Blattverbrennungen (daher ~30 % Schattierung).

**Hinweis (Salz):** Die ECe-Schwelle bezieht sich auf die **Substrat-Leitfähigkeit (ECe)**, nicht auf die Gießwasser-EC. Empfindlichkeit gegen Versalzung ist hoch — bereits ab 2 dS/m sinken Blatt- und Blütenzahl; ab 4 dS/m leiden Pseudobulben/Infloreszenzen. Konsistent mit dem light_feeder-Status (§1.1) und der niedrigen Nährlösungs-EC (0.4–0.8 mS, §2.3).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktivwachstum / Bulbenentwicklung (Frühling/Sommer) | 150–180 | 1 | false | false | medium |
| Kühlphase / Ruhephase (Herbst/Winter) | 60–90 | 2 | false | false | high |
| Blüte (Winter/Frühjahr) | 45–90 | 3 | true | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktivwachstum (April–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (halbschattiger Epiphytenstandort; offenes Tageslicht ≈ 0.5, lichter Baumkronenschatten höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kühlphase (Oktober–Dezember — KRITISCH für Blüte)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 9–17 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 7–13 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 12–17 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (halbschattiger Epiphytenstandort; offenes Tageslicht ≈ 0.5, lichter Baumkronenschatten höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–120 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (Januar–April)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.5 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–23 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 (halbschattiger Epiphytenstandort; offenes Tageslicht ≈ 0.5, lichter Baumkronenschatten höher) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktivwachstum | 20:20:20 ausgewogen | 0.4–0.8 | 5.5–6.5 | 40 | 20 | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->0.5 | 0.05 | 0.02 | 0.01<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Kühlphase | 0:0:0 | 0.0–0.2 | 5.5–6.5 | — | — | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->— | — | — | —<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Blüte | 0:0:0 | 0.0–0.2 | 5.5–6.5 | — | — | <!-- Quelle: Steckbrief-Erweiterung 2026-06 -->— | — | — | —<!-- /Quelle: Steckbrief-Erweiterung 2026-06 --> |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Werte als Richtwerte einer ausgewogenen, stark verdünnten Vollnährlösung für leichtzehrende Epiphyten (Mangan/manganese, Zink/zinc, Kupfer/copper, Molybdän/molybdenum). Mikronährstoffe werden ausschließlich in der Aktivwachstumsphase zugeführt; in Kühl- und Blütephase erfolgt keine Düngung (0:0:0). Bei reinem Regen-/RO-Wasser einen Orchideen-Volldünger mit Spurenelementen verwenden, niemals überdosieren (Versalzungsgefahr, siehe §1.7 Salztoleranz).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideen-Flüssigdünger | Substral | base | 7-5-6 | 3 ml/L (alle 2 Wochen, halbdosiert) | Wachstum |
| Balance-Orchideendünger | Compo | base | 5-5-7 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | – | organisch | Nicht empfohlen für Epiphyten | — |

### 3.2 Besondere Hinweise

Leichter Zehrer. Alle 14 Tage April bis September bei halber Empfehlungsdosis. Oktober bis März KEIN Dünger. Ausgewogenes NPK-Verhältnis (20-20-20 oder ähnlich) wird empfohlen. NIEMALS auf trockene Wurzeln düngen — zuerst mit reinem Wasser gießen, dann düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | soak | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser bevorzugt (Regenwasser, RO-Wasser); Topf tauchen bis Blasen aufhören, dann vollständig abtropfen; NIE Staunässe; in der Kühlphase auf fast trocken stellen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor erstem Frost / Ende Eisheilige-Saison hereinholen) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach Eisheiligen, abgehärtet) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 7–15 (Kühlphase obligat für Blüte; Nacht 7–13 °C, Tag 10–18 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell (heller Standort, kein Schatten im Winter; PPFD 150–400 µmol/m²/s) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | stark reduziert (alle 14–21 Tage, fast trocken halten; kein Dünger) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Dendrobium nobile ist frostempfindlich (`tender`, §1.1) und überwintert in Mitteleuropa (USDA 6–8) zwingend frostfrei im Haus → Einstufung `frost_free` (kein Ausgraben/Einlagern wie bei Knollen, kein Winterschutz im Freiland). Anders als bei reinen Zimmerpflanzen ist die kühle, helle, trockene Überwinterung hier **funktional notwendig**: Ohne den Kältereiz (7–15 °C) im Herbst/Winter bleibt die Blüte aus. Ein zu warmer Wohnraum (> 18 °C nachts) im Winter verhindert die Blühinduktion.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter punktförmig | medium |
| Wollschildlaus | Pseudococcus spp. | Wollflecken an Bulben/Blättern | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Braune, weiche Wurzeln | Staunässe, fehlende Drainage |
| Keimi-/Knospenausfall | physiologisch | Knospen fallen ab ohne aufzublühen | Zu warm im Herbst, zugig, Umzug |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Kühlphase einhalten | cultural | Herbst: 10°C Nacht | 0 | Blütenausfall (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen | 0 | Wollschildläuse, Schildläuse |
| Neemöl | biological | Sprühen 0.3% | 0 | Spinnmilben |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m² (1–2× wöchentlich wiederholen) | 2–4 Wochen |
| Australischer Marienkäfer (Mealybug destroyer) | Cryptolaemus montrouzieri | Woll-/Schmierläuse (Pseudococcus spp.) | 2–10 Tiere/m² (bei Bedarf wiederholen) | 3–6 Wochen |
| Schlupfwespe | Metaphycus helvolus | Weichschildlaus (Coccus hesperidum) | 1–5 Tiere/m² (mehrfach im 1–2-Wochen-Takt) | 3–5 Wochen |

**Hinweis:** Nützlingseinsatz ist v. a. im Wintergarten/Gewächshaus oder bei Sommerstand im Freien sinnvoll; im trockenen Wohnraum etablieren sich Raubmilben schlecht. Nützling-Wirt-Zuordnung beachten: *Phytoseiulus persimilis* nur gegen Spinnmilben (kein Alternativwirt), *Cryptolaemus montrouzieri* gegen Woll-/Schmierläuse, *Metaphycus helvolus* gegen Weichschildläuse (Coccidae, z. B. *Coccus hesperidum*) — **nicht** gegen Panzer-/Deckelschildläuse (dafür wären *Aphytis*-Arten zuständig).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Phalaenopsis | Phalaenopsis spp. | Orchidaceae | Pflegeleichter, kein Kühlbedarf |
| Cymbidium | Cymbidium spp. | Orchidaceae, sympodial | Robuster, auch für draußen |
| Oncidium | Oncidium spp. | Orchidaceae | Häufige Blüten, aromatisch |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Dendrobium nobile,"Dendrobium-Orchidee;Edle Dendrobie;Bambusorchidee;Noble Dendrobium",Orchidaceae,Dendrobium,perennial,day_neutral,herb,aerial,"10a;10b;11a;11b","Nepal, Indien, China, Myanmar",yes,1-3,10,30-60,20-40,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Smart Garden Guide — Dendrobium nobile](https://smartgardenguide.com/dendrobium-nobile-orchid-care/) — Pflegehinweise, Kühlphasen
2. [Gardening Know How — Dendrobium nobile](https://www.gardeningknowhow.com/ornamental/orchids/dendrobium-nobile-orchid-care) — Kulturdaten
3. [UK Houseplants — Dendrobiums](https://www.ukhouseplants.com/plants/dendrobiums) — Schädlinge, Phasen
4. [Carter & Holmes — Nobile Dendrobium](https://www.carterandholmes.com/pages/dendrobium-nobile-and-ise-care-sheet) — Professionelle Pflegekarte
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Zhang et al. 2019, J. Exp. Bot. 70(22):6611 — CAM evolution in Dendrobium](https://academic.oup.com/jxb/article/70/22/6611/5592895) — Beleg Photosynthese-Typ CAM in der Gattung Dendrobium
7. [BMC Plant Biology 2023 — Chloroplast genomic evolution of Dendrobium among photosynthetic pathways](https://bmcplantbiol.biomedcentral.com/articles/10.1186/s12870-023-04186-y) — Beleg CAM/fakultative CAM bei Dendrobium
8. [HortScience 43(6) 2008 — Effects of Cooling Temperature and Duration on Flowering of the Nobile Dendrobium Orchid](https://journals.ashs.org/hortsci/view/journals/hortsci/43/6/article-p1765.xml) — Kühl-/Vernalisationsdauer (≥3 Wochen 13–15 °C; 2–6 Wochen 10 °C)
9. [Scientia Horticulturae 2011 — Deferring flowering of nobile dendrobium hybrids after vernalization](https://www.sciencedirect.com/science/article/abs/pii/S0304423811004493) — Bestätigung Vernalisations-/Kühlbedarf, Mindestdauer kultivarabhängig
10. [Frontiers Plant Sci. 2022 — Salinity stress mechanisms in facultative CAM Dendrobium officinale](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.1028245/full) — Salzempfindlichkeit, Schwellen ≥2 / ≥4 dS/m
11. [Abdullakasim & Kongpaisan — Physiological responses of potted Dendrobium orchid to salinity stress](https://www.researchgate.net/publication/326068718_Physiological_responses_of_potted_Dendrobium_orchid_to_salinity_stress) — ECe-Schwellenwerte Topf-Dendrobium
12. [Scientific Reports 2025 — Photosynthetic acclimation of CAM orchid Phalaenopsis to light level](https://www.nature.com/articles/s41598-025-96167-4) — niedriger Lichtkompensationspunkt bei CAM-Orchideen (Vergleichsbeleg)
13. [Zhen & Bugbee 2020, Frontiers Plant Sci. — Substituting Far-Red for PAR photons](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.581156/full) — Far-Red-Fraction-Methodik/Anker (offenes Tageslicht vs. direkte Sonne)
14. [OrchidWeb — Nobile Type Dendrobium Orchid Care](https://www.orchidweb.com/orchid-care/nobile-type-dendrobium-orchid-care) — Substrat-pH 5.5–6.5, hohe Lichtansprüche, Sommerschattierung
15. [Floricultura — Cultivation manual Dendrobium nobile pot plant 2021](https://www.floricultura.com/media/5298/dendrobium-nobile-pot-plant-cultivation-manual-2021_en.pdf) — Substrat, pH, Kulturführung Topfpflanze
16. [New York Botanical Garden — Nobile Dendrobium Hybrids](https://libguides.nybg.org/c.php?g=1285826&p=9477919) — Winter-Ruhetemperaturen, Blühinduktion durch kühle Nächte
17. [Koppert — Phytoseiulus persimilis (Spidex)](https://www.koppert.com/spidex/) — Ausbringrate Raubmilbe gegen Spinnmilben
18. [Koppert — Cryptolaemus montrouzieri (Cryptobug)](https://www.koppert.com/cryptobug/) — Ausbringrate gegen Woll-/Schmierläuse
19. [UF/IFAS ENY-2114 — Orchid Insect and Mite Pests in South Florida](https://ask.ifas.ufl.edu/publication/IN1433) — Schädlings-/Nützling-Zuordnung bei Orchideen
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
