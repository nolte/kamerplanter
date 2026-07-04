# Urnenpflanze — Aechmea fasciata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/aechmea-fasciata/), [OurHouseplants](https://www.ourhouseplants.com/plants/urn-plant), [Bromeliads.info](https://www.bromeliads.info/bromeliad-plant-growing-specifications-aechmea-fasciata/), [Portland Nursery](https://www.portlandnursery.com/houseplants/aechmea), [JoyUsGarden](https://www.joyusgarden.com/aechmea-plant-care-tips/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aechmea fasciata | `species.scientific_name` |
| Volksnamen (DE/EN) | Urnenpflanze, Lanzenrosette; Silver Vase Plant, Urn Plant | `species.common_names` |
| Familie | Bromeliaceae | `species.family` → `botanical_families.name` |
| Gattung | Aechmea | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | monocarpic (blüht einmal, dann Absterben) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 10°C; Zimmerpflanze | `species.hardiness_detail` |
| Heimat | Brasilien (Atlantischer Regenwald, Rio de Janeiro) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | 15 | `species.base_temp` |
| Lebensdauer (Jahre) | 3–5 (monokarpisch; Mutterpflanze stirbt nach Blüte) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | nicht relevant | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | nicht relevant (tagneutral; Blüte ethyleninduziert) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Photosynthese (CAM):** Aechmea fasciata betreibt Crassulaceen-Säurestoffwechsel (Crassulacean Acid Metabolism, CAM) — wie für die Gattung Aechmea und viele Bromelien belegt: nächtliche CO₂-Fixierung mit diurnaler Apfelsäure-Akkumulation, Stomata nachts geöffnet (~45–50 % gegen 4 Uhr), tagsüber weitgehend geschlossen (5–10 %). Diese Wasserspar-Strategie begründet die geringe VPD-Sensitivität und Trockenstress-Toleranz. Die GDD-Basistemperatur von 15 °C orientiert sich am unteren Ende des aktiven Wachstumsbereichs (Wachstumsstillstand unterhalb ~15 °C); unterhalb dieser Schwelle akkumuliert die Pflanze keine relevante Wärmesumme.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**Biologische Besonderheit — Monokarpie:** Aechmea fasciata ist monokarpisch. Die Mutterpflanze stirbt nach der Blüte ab, produziert vorher jedoch mehrere Kindel (Pups) an der Basis. Diese Kindel wachsen zu neuen blühfähigen Pflanzen heran (Lebenserwartung Kindel bis zur Blüte: 3–5 Jahre <!-- korrigiert 2026-07 von "2–4 Jahre": 4 unabh. Quellen (NC State Extension, JoyUsGarden, Bromeliads.info, PlantCareToday) nennen übereinstimmend 3–5 (mehrheitlich 3–4) Jahre, keine nennt 2 Jahre als Untergrenze -->).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | variabel (6–8 Wochen nach Ethylengasbehandlung; korrigiert 2026-07, siehe §1.3 & §2.4); typisch 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset; seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Kindel-Vermehrung:** Kindel (Pups) trennen, wenn sie 1/3 bis 1/2 der Mutterpflanzengröße erreicht haben (ca. 15 cm). Mit scharfem Messer vom Mutterstamm abtrennen. In Bromelien-/Orchideensubstrat einpflanzen. Bis zur Blüte des Kindels dauert es 3–5 Jahre.

**Blüteinduktion:** Kann durch Ethylengas ausgelöst werden. Praxismethode: Pflanze für 7–10 Tage in großen Plastikbeutel mit reifen Äpfeln einschließen (Äpfel produzieren Ethylen). Nach ca. 6–8 Wochen erscheinen erste Blütenstände.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine toxischen Inhaltsstoffe; Blattzähne können bei Kontakt kratzen | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | variabel | `species.pruning_months` |

**Hinweis:** Verblühten Blütenstand und danach die absterbende Mutterpflanze entfernen, sobald Kindel gut etabliert sind.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–70 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockeres Bromelien-/Orchideensubstrat; Rindenmulch-/Perlit-Mischung; pH 5.5–6.5; sehr durchlässig — Staunässe ist tödlich | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 5–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweise zu §1.7:**
- *Lichtkompensationspunkt (light compensation point):* Als ausgeprägt schattentolerante CAM-Bromelie liegt der Kompensationspunkt (Netto-Photosynthese = 0) sehr niedrig (Größenordnung 10–25 µmol/m²/s, typisch für schattenadaptierte CAM-/Schwachlichtpflanzen). Davon zu trennen sind der Sättigungs-/Optimumbereich (vgl. §2.2 PPFD-Ziel 100–300) und die Photoinhibition bei voller Sonne — diese Werte gehören NICHT in das Kompensationspunkt-Feld.
- *Schattentoleranz (shade tolerance):* `partial_shade` — gedeiht bei hellem indirektem Licht bis Halbschatten; tiefer Schatten (deep_shade) verhindert Blüteninduktion, volle Sonne (full_sun) führt zu Blattbrand.
- *Effektive Wurzeltiefe (effective root depth):* Epiphytisches, flaches Haftwurzelsystem (Wasser-/Nährstoffaufnahme primär über die Blatt-Trichome, nicht über Wurzeln); ein 10-cm-Topf genügt.
- *Staunässe-Toleranz (waterlogging tolerance):* `sensitive` — Überwässerung/Staunässe im Substrat führt zu Wurzel- und Herzfäule (konsistent mit §1.6 „Staunässe ist tödlich“).
- *Salztoleranz (salt tolerance):* `sensitive` — Salze/Minerale aus hartem Leitungswasser verbrennen das empfindliche Trichom-/Trichtergewebe und lagern sich ab; Regen-, destilliertes oder gefiltertes Wasser empfohlen (konsistent mit Wasserqualität-Hinweis §4.1). Quantitative Maas-Hoffman-Parameter (ECe-Schwelle, Slope) liegen für diese Zier-Epiphyte nicht aus belastbaren Quellen vor — daher offen gelassen.
- *Boden-pH-Vorzug (soil pH preference):* 5.5–6.5 (sauer bis schwach sauer), harmonisiert mit Substrat-Empfehlung §1.6 und Nährstoffprofilen §2.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Kindel/Etablierung | 60–120 | 1 | false | false | low |
| Vegetativ | 915–1725 <!-- korrigiert 2026-07: rechnerisch aus Gesamtreifezeit Kindel→Blüte 3–5 Jahre (siehe §1.1/§1.3) abzüglich Kindel-/Etablierungsphase (60–120 Tage) und Blüteinduktionsphase (42–60 Tage); War: 180–730 --> | 2 | false | false | medium |
| Blüteinduktion | 42–60 | 3 | false | false | medium |
| Blüte | 90–180 | 4 | false | false | medium |
| Seneszenz (Ableben Mutter) | 60–120 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Hauptwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–21 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (Trichter gefüllt halten, Substrat trocken/feucht wechselnd) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 (im Trichter) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN --> | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–150 (im Trichter) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Kindel/Etablierung | 0:0:0 | 0.0 | 5.5–6.5 | — | — | — | — | — | — |
| Vegetativ | 1:1:1 | 0.4–0.8 | 5.5–6.5 | 60 | 30 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüteinduktion | 0:1:1 | 0.3–0.6 | 5.5–6.5 | 40 | 20 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | 0:0:0 | 0.0 | 5.5–6.5 | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (§2.3):** Aechmea fasciata wird ausschließlich stark verdünnt über den Blatttrichter ernährt (1/4-Dosis, EC < 0.8 mS). Phasenspezifische Mikronährstoff-Sollwerte (Mangan/Mn, Zink/Zn, Kupfer/Cu, Molybdän/Mo in ppm) sind für diese Zier-Epiphyte nicht aus belastbaren Quellen (Extension/peer-reviewed) belegbar; ein hochwertiger Bromelien-/Orchideen-Flüssigdünger deckt den Spurenelementbedarf in der angegebenen Verdünnung ab. Werte daher offen gelassen statt zu schätzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Kindel → Vegetativ | manual | Kindel eingetopft, 15+ cm Höhe |
| Vegetativ → Blüteinduktion | manual/event | 3–5 Jahre; Ethylenbehandlung optional |
| Blüteinduktion → Blüte | time_based | 42–60 Tage nach Ethylenbehandlung |
| Blüte → Seneszenz | event_based | Blüte verblüht, Mutterpflanze stirbt ab |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (für Trichterbeflutung)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Bromelien-Dünger | Compo | Spezialdünger | 7-4-7 | stark verdünnt 0.5 ml/L | Vegetativ |
| Orchideendünger (verdünnt) | Substral | Flüssigdünger | 7-5-6 | 0.5 ml/L | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee (stark verdünnt) | eigen | organisch | 1 ml/L | Frühling–Sommer |

### 3.2 Besondere Hinweise zur Düngung

**Düngung nur über den Blatttrichter:** Dünger NIEMALS auf das Substrat gießen. Bromelieen nehmen Nährstoffe primär über die Trichterinnenwand (Sternhärchen = Trichome) auf. Sehr schwach konzentrierte Lösungen verwenden (1/4 der Normaldosis). Starke Düngung führt zur Schädigung der Trichome und zu Verbrennungen.

**Trichter-Pflege:** Den zentralen Blatttrichter stets mit Wasser gefüllt halten (ca. 2–3 cm). Alle 2–3 Wochen Trichter leeren und mit frischem Wasser befüllen — verhindert Fäulnis und Mückenlarven. In der Heizperiode öfter auffüllen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water (in Trichter) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies, zimmerwarmes Wasser bevorzugt; Leitungswasser stehen lassen; Trichter regelmäßig erneuern | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Wenig Wasser | Trichter alle 2–3 Wochen erneuern; kein Dünger | niedrig |
| Mär | Düngen beginnen | 1/4 Dosis Bromelien-Dünger in Trichter | mittel |
| Apr–Jun | Aktive Wachstumsphase | Regelmäßig wässern, leicht düngen; Ethylenbehandlung falls gewünscht | hoch |
| Jul–Sep | Blütezeit (wenn induktiert) | Trichter leicht feucht halten; Blüte genießen | mittel |
| Okt–Nov | Kindel abtrennen | Nach Absterben der Mutter Kindel mit scharfem Messer trennen | hoch |
| Dez | Ruhephase | Wenig Wasser, kein Dünger | niedrig |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Monat Winter-Maßnahme | 9–10 (vor erstem Frost / unter 10 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Monat Frühjahrs-Maßnahme | 5–6 (nach den Eisheiligen, frostfrei) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–20 (Minimum 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell; bright indirect light, Süd-/Ostfenster | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert: Trichter alle 2–3 Wochen erneuern, Substrat fast trocken halten, kein Dünger | `overwintering_profiles.winter_quarter_watering` |

**Hinweise zu §4.3:**
- Als nicht frostharte (frost-tender) tropische Kübel-/Zimmerpflanze überwintert *Aechmea fasciata* frostfrei im Haus (`frost_free`) — kein Ausgraben/Einlagern (kein `dig_and_store`), keine Vlies-/Mulch-Maßnahme im Freien.
- Mindesttemperatur 10 °C; darunter drohen Kälteschäden (braune Blattspitzen) und erhöhtes Herzfäule-Risiko bei stehendem Trichterwasser. Konsistent mit Winterhärte-Detail §1.1 und Frostempfindlichkeit `tender`.
- Ein Sommer-Aufenthalt im Freien (Halbschatten) ist nur in frostfreier Periode (Mitteleuropa ~Mitte Mai bis September) ratsam.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollknäuel, Honigtau | leaf, stem | easy |
| Schildläuse | Diaspididae | Braune Schuppen auf Blättern | leaf, stem | medium |
| Thripse | Thysanoptera | Silbrige Streifen, deformierte Blüten | flower, leaf | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Herzfäule | bakteriell/fungal | Braune, faulige Trichterbasis, Kollaps | Stehendes Wasser in Trichter bei Kälte |
| Blattflecken | fungal | Braune Flecken auf Blättern | Zu kühle Temperaturen + Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | biological | Isopropylalkohol | Wattestäbchen | 0 | Wollläuse, Schildläuse |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Thripse, Blattläuse |
| Trichter täglich spülen | cultural | — | Trichter leeren bei Herzfäule-Risiko | 0 | Herzfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|--------------------|----------------|-----------------|------------------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Wollläuse (Planococcus citri) | 2–5 Käfer/m² (bei Befall); 2–3 Teilfreilassungen | 3–6 Wochen |
| Florfliege (Lacewing) | Chrysoperla carnea | Wollläuse, Schild­läuse, Blattläuse, Thripse | 10–20 Larven/m² | 2–3 Wochen |
| Thrips-Raubmilbe | Amblyseius (Neoseiulus) cucumeris | Thripse (Thysanoptera) | 50–100 Milben/m² (vorbeugend); bis 500/m² bei Befall | 2–4 Wochen |

**Hinweise zu §5.3:**
- *Cryptolaemus montrouzieri:* Optimal bei 25–29 °C und 70–80 % rel. Luftfeuchte — passt gut zum Tropen-Mikroklima der Urnenpflanze. In Mitteleuropa nur April–Oktober wirksam aktiv. Mehrere kleine Freilassungen statt einer großen erhöhen die Etablierung.
- *Amblyseius cucumeris:* Vorbeugend in Tütchen (Sachets) ausbringen; benötigt > 65 % rel. Luftfeuchte zur Vermehrung — durch die hohe Luftfeuchte am Trichter begünstigt.
- Nützlingseinsatz ist v.a. bei Sammlungen / Gewächshauskultur sinnvoll; bei Einzelpflanzen genügt meist mechanische Bekämpfung (§5.3 oben, Isopropanol/Neem).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Guzmania | Guzmania lingulata | 0.9 | Gleiche Familie, identische Pflegebedingungen | `compatible_with` |
| Vriesea | Vriesea splendens | 0.9 | Gleiche Familie, ähnliche Kultur | `compatible_with` |
| Neoregelia | Neoregelia carolinae | 0.8 | Gleiche Familie, Trichter-Bromeliad | `compatible_with` |
| Chamaedorea | Chamaedorea elegans | 0.7 | Ähnliche Feuchtigkeitsanforderungen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kakteen | diverse | Völlig gegensätzliche Feuchtigkeitsanforderungen | severe | `incompatible_with` |
| Sukkulenten | diverse | Bromelieen benötigen höhere Luftfeuchtigkeit | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Guzmania | Guzmania lingulata | Gleiche Familie, Trichter-Bromeliad | Blüht etwas leichter ohne Ethylen-Behandlung |
| Vriesea | Vriesea splendens | Gleiche Familie | Aufrecht wachsender Blütenstand, dekorativere Blüte |
| Neoregelia | Neoregelia carolinae | Gleiche Familie, Trichter-Bromeliad | Niedrigeres Wachstum, spektakuläre Herzfärbung |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Aechmea fasciata,Urnenpflanze;Lanzenrosette;Silver Vase Plant;Urn Plant,Bromeliaceae,Aechmea,perennial,day_neutral,herb,aerial,10a;10b;11a;11b,0.0,"Brasilien, Atlantischer Regenwald",yes,3,15,60,70,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [NC State Extension — Aechmea fasciata](https://plants.ces.ncsu.edu/plants/aechmea-fasciata/) — Botanische Einordnung, Wachstumsbedingungen
2. [OurHouseplants — Urn Plant](https://www.ourhouseplants.com/plants/urn-plant) — Pflegehinweise
3. [Bromeliads.info — Aechmea fasciata Growing Specifications](https://www.bromeliads.info/bromeliad-plant-growing-specifications-aechmea-fasciata/) — Wissenschaftliche Anzuchtdaten
4. [JoyUsGarden — Aechmea Plant Care Tips](https://www.joyusgarden.com/aechmea-plant-care-tips/) — Vermehrung und Blüteinduktion
5. [Root & Reach Botanicals — Aechmea fasciata](https://rootandreachbotanicals.com/products/aechmea-fasciata-bromeliad-silver-vase-pet-safe) — Toxizitätsinformation
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [PNAS — Crayn, Winter & Smith: Multiple origins of CAM and the epiphytic habit in Bromeliaceae](https://www.pnas.org/doi/10.1073/pnas.0400366101) — CAM-Photosynthese-Typ der Bromeliaceae (peer-reviewed)
7. [ScienceDirect — Organic acid analysis and plant water status of two Aechmea cultivars (incl. A. fasciata)](https://www.sciencedirect.com/science/article/abs/pii/S0304423805000580) — CAM-Nachweis bei Aechmea (diurnale Apfelsäure, Stomata-Rhythmik), peer-reviewed
8. [IntechOpen — CAM Photosynthesis in Bromeliads and Agaves](https://www.intechopen.com/chapters/45242) — CAM in Bromelien, geringe VPD-Sensitivität, Schwachlicht-Plastizität
9. [OurHouseplants — Urn Plant (Temperatur, Wasserqualität)](https://www.ourhouseplants.com/plants/urn-plant) — Mindesttemperatur 15 °C, Hartwasser-/Salzempfindlichkeit, Überwinterung
10. [Bromeliads.info — Aechmea: The Beginner's Bromeliad](https://www.bromeliads.info/aechmea-starter-bromeliad/) — flaches epiphytisches Wurzelsystem, 10-cm-Topf, Aufnahme über Blätter
11. [Bromeliads.info — Common Bromeliad Care Mistakes](https://www.bromeliads.info/common-bromeliad-care-mistakes/) — Salz-/Mineralempfindlichkeit, Trichter-Spülung, Regen-/destilliertes Wasser
12. [greg.app — Aechmea fasciata Light Requirements](https://greg.app/aechmea-fasciata-light-requirements/) — Halbschatten/partial_shade, kein Tiefschatten, kein Vollsonnen-Standort
13. [Koppert — Cryptolaemus montrouzieri (Mealybug Destroyer)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Wollläuse, Ausbringrate, Etablierung
14. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Freilassungsraten/m², Klimaoptimum, Teilfreilassungen
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 (Lebenszyklus-/Phasen-Audit) -->
15. [PlantCareToday — Aechmea fasciata](https://plantcaretoday.com/aechmea-fasciata.html) — Blüteinduktion 6–8 Wochen nach Ethylenbehandlung, Lebensdauer 3–4 Jahre
16. [University of Florida IFAS Extension (EP447) — Using Gibberellic Acid and Ethephon to Induce Flowers on Tropical Foliage Plants](https://ask.ifas.ufl.edu/publication/EP447) — Bromeliaden-Blüteinduktion: sichtbare Knospe 3–8 Wochen, volle Blütenfärbung +4–6 Wochen nach Ethephon-Behandlung (peer-reviewed Extension-Publikation)
17. [Grow Queen — Aechmea Fasciata Care Guide](https://growqueen.com/blogs/plant-care-guide-by-species-and-sub-species/aechmea-fasciata-silver-vase-plant) — Blütezeit spät Frühling/Sommer, Mindesttemperatur 10 °C
18. [NC State Extension Gardener Plant Toolbox — Aechmea fasciata (Direktabfrage 2026-07)](https://plants.ces.ncsu.edu/plants/aechmea-fasciata/) — cycle_type perennial trotz monokarper Einzelrosette bestätigt, USDA-Zonen 10a–11b bestätigt, Blüte "in spring"
19. [OurHouseplants — Urn Plant (Direktabfrage 2026-07)](https://www.ourhouseplants.com/plants/urn-plant) — Mindesttemperatur 15 °C (widerspricht Quelle 17 „10 °C"; als ungeklärt dokumentiert, Originalwert 10 °C beibehalten)
<!-- /Quelle: growing-phase-auditor 2026-07 -->
