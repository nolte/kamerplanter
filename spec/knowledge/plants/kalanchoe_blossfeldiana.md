# Flammendes Käthchen — Kalanchoe blossfeldiana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardening Know How](https://www.gardeningknowhow.com/houseplants/kalanchoe/growing-flaming-katy.htm), [Gardenia.net](https://www.gardenia.net/plant/kalanchoe-blossfeldiana-flaming-katy), [Guide to Houseplants](https://www.guide-to-houseplants.com/flaming-katy.html), [House Plants Expert](https://houseplantsexpert.com/flaming-katy.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Kalanchoe blossfeldiana | `species.scientific_name` |
| Volksnamen (DE/EN) | Flammendes Käthchen, Kalanchoe; Flaming Katy, Christmas Kalanchoe, Florist Kalanchoe | `species.common_names` |
| Familie | Crassulaceae | `species.family` → `botanical_families.name` |
| Gattung | Kalanchoe | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 2–5 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für K. blossfeldiana auffindbar; vorhandene Literatur betrifft Keim-/Blühinduktion, nicht die GDD-Wuchsbasis --> | `species.base_temp` |
| Kritische Tageslänge (critical day length, h) | 12 | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–27°C. Winterblüher der kühle Nächte für Blütenbildung braucht. | `species.hardiness_detail` |
| Heimat | Madagaskar — trockene Felsen, sukkulente Busch-Savanne | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Kalanchoe blossfeldiana ist Kurztagspflanze — Blütenbildung erfordert mind. 6 Wochen mit weniger als 12 Stunden Licht pro Tag. Im Handel werden Pflanzen durch künstliche Kurztag-Behandlung ganzjährig blühend angeboten. Für Wiederblüte: August/September in komplett dunklen Raum (kein Kunstlicht!) für 6 Wochen stellen (Langzeit-Dunkelperiode). Danach: heller Standort und erste Knospen erscheinen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 11, 12, 1, 2, 3 (bei korrekter Kurztag-Behandlung; im Handel auch andere Monate) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (5–8 cm) an der Luft 1–2 Tage trocknen lassen (Callus bildet sich), dann in trockenes Substrat stecken. Bei 22–24°C, Bewurzelung in 2–3 Wochen. Nicht zu viel gießen bis Widerstand beim Zupfen spürbar.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, flowers, stems (alle Pflanzenteile) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | bufadienolides (herzwirksame Glykoside) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe (bei Tieren; herzrhythmusstörend) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**WICHTIGER HINWEIS:** Bufadienolide (herzwirksame Glykoside) können bei Tieren (besonders Katzen und Hunde) schwere Herzrhythmusstörungen verursachen — auch in kleinen Mengen lebensbedrohlich. Diese Pflanze unbedingt von Haustieren fernhalten!

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 (nach der Blüte) | `species.pruning_months` |

**Hinweis:** Verblühte Stängel bis auf 2–3 cm über dem Blattwerk kürzen — fördert neue Triebe. Danach: Kurztag-Behandlung für Wiederblüte (August–Oktober).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–45 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–35 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, frostfreie Monate) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- oder Sukkulentenerde mit zusätzlichem Perlite-Anteil (1:1). pH 6.0–7.0. Sehr gute Drainage. Kleiner Topf bevorzugt. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert für K. blossfeldiana belegt; generische CAM-/Sukkulenten-Werte nicht übertragbar --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer Messwert für K. blossfeldiana belegt --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | <!-- DATEN FEHLEN: flaches Wurzelsystem belegt, aber kein quantitativer cm-Bereich aus zwei unabhängigen Quellen --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Schwellenwert (a) für K. blossfeldiana --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-Slope (b) --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Sukkulente CAM-Pflanze mit flachem, salzempfindlichem Wurzelsystem; Überdüngung führt zu Salzakkumulation (sichtbarer weißer Belag auf Substrat/Topfrand) und Wurzelschäden — daher Einstufung `moderately_sensitive`. Standort: helles indirektes Licht bzw. Halbschatten (partial sun); direkte Mittagssonne kann Blätter verbrennen. pH-Vorzug 6.0–7.0 ist konsistent mit §1.6 (Substrat) und §2.3 (Nährstoffprofile).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Vegetative Wachstumsphase | 90–120 | 1 | false | false | high |
| Blüteninduktionstruktur (Kurztag) | 42–56 | 2 | false | false | high |
| Blütezeit | 60–90 | 3 | false | false | medium |
| Ruhephase nach Blüte | 60–90 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüteninduktion (Kurztag — August bis Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | max. 10–11 (Dunkelperiode min. 13h!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–16 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Blütezeit

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 8–14 | `requirement_profiles.dli_target_mol` |
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetatives Wachstum | 2:1:2 | 0.6–1.0 | 6.0–7.0 | 60 | 25 |
| Blüteninduktion | 0:2:1 | 0.4–0.8 | 6.0–7.0 | 50 | 20 |
| Blütezeit | 1:3:2 | 0.6–1.0 | 6.0–7.0 | 70 | 30 |
| Ruhephase | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (ppm):**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Vegetatives Wachstum | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüteninduktion | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blütezeit | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |

**Hinweis:** Für die Mikronährstoffe Mangan (Mn), Zink (Zn), Kupfer (Cu) und Molybdän (Mo) sind keine artspezifischen Sollwerte für *Kalanchoe blossfeldiana* aus zwei unabhängigen seriösen Quellen belegt. Generische Nährlösungswerte (z.B. Hoagland) sind nicht ohne Beleg auf diese leichtzehrende Sukkulente übertragbar; Felder daher als DATEN FEHLEN markiert (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 3 ml/L (alle 4 Wochen, Wachstum) | Wachstum |
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 3 ml/L | Blütezeit |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Während Blüteninduktion NICHT düngen. Blütezeit: P-K-betonte Formel. Wachstumsphase: ausgewogen oder leicht N-betont. Während Ruhephase nach Blüte: kein Dünger.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; obere 2 cm Erde zwischen Güssen trocknen lassen; Staunässe ist gefährlich | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 (Wachstumsphase; nicht während Blüte oder Induktion) | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 10–16 (min. 10, nicht unter 10 fallen lassen) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell; 6–8 h direktes/helles Licht täglich | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sparsam; alle 3–4 Wochen, obere 2–5 cm Substrat zwischen Güssen vollständig abtrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Frostempfindliche Kübel-/Zimmerpflanze (USDA 10–11). In Mitteleuropa (USDA 6–8) NICHT winterhart — vor dem ersten Frost (Oktober) frostfrei ins Haus holen, ab den Eisheiligen (Mitte Mai) wieder ins Freie. Im Winterquartier nicht düngen und nicht in Fensternähe mit Kaltlufteinfall stellen. Einstufung `frost_free`, da die Pflanze frostfrei drinnen überwintert (keine Knollen zum Ausgraben → nicht `dig_and_store`).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blattverfärbung | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Blattlaus | Aphididae | Kolonien an Knospen und Blättern | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, verfärbter Stamm | Überwässerung |
| Botrytis | fungal | Grauschimmel auf Blüten | Hohe Feuchtigkeit, schlechte Luftzirkulation |
| Echter Mehltau | fungal | Weißer Belag | Trockene Luft, feuchte Blätter |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |
| Weniger gießen | cultural | Intervall erhöhen | 0 | Wurzelfäule (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 5–20 /m² (≈0.5–2 /sq ft), wöchentlich nach Bedarf | ca. 1–2 Wochen; optimal 20–27 °C |
| Australischer Marienkäfer | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | 2–10 /m² je Ausbringung (Cryptobug), abends an Befallsherden | mehrere Freilassungen über 3–6 Wochen; wirksam April–Oktober |
| Schlupfwespe | Aphidius colemani | Blattläuse (Aphididae) | 0.25–4 /m² je Ausbringung, 7–14-tägig wiederholt | 14–21 Tage (Mumienbildung), mind. 3 Freilassungen |

**Hinweis:** Nützling-Wirt-Zuordnung fachlich geprüft: *Phytoseiulus persimilis* → Spinnmilben, *Cryptolaemus montrouzieri* → Schmierläuse, *Aphidius colemani* → Blattläuse. Da Kalanchoe primär als Zimmer-/Topfpflanze kultiviert wird, eignen sich Nützlinge vor allem im Gewächshaus oder bei größeren Beständen; bei Einzelpflanzen sind mechanische/biologische Methoden aus §5.3 meist praktikabler.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Weihnachtskaktus | Schlumbergera truncata | Kurztagsblüher, Sukkulente | Weniger toxisch für Haustiere |
| Crassula | Crassula ovata | Gleiche Familie | Langlebiger, weniger Giftrisiko |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Kalanchoe blossfeldiana,"Flammendes Käthchen;Kalanchoe;Flaming Katy;Christmas Kalanchoe",Crassulaceae,Kalanchoe,perennial,short_day,herb,fibrous,"10a;10b;11a;11b","Madagaskar",yes,1-3,10,15-45,15-35,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardening Know How — Flaming Katy](https://www.gardeningknowhow.com/houseplants/kalanchoe/growing-flaming-katy.htm) — Pflegehinweise, Blüte
2. [Gardenia.net — Kalanchoe blossfeldiana](https://www.gardenia.net/plant/kalanchoe-blossfeldiana-flaming-katy) — Botanische Daten
3. [Guide to Houseplants — Flaming Katy](https://www.guide-to-houseplants.com/flaming-katy.html) — Kulturdaten
4. [House Plants Expert — Flaming Katy](https://houseplantsexpert.com/flaming-katy.html) — Schädlinge, Toxizität
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (bufadienolides)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Cowan-Turner et al. 2024 — Development of *Kalanchoë blossfeldiana* as a C3, CAM comparative tool (PLANTS, PEOPLE, PLANET)](https://nph.onlinelibrary.wiley.com/doi/full/10.1002/ppp3.10517) — Photosynthese-Typ (CAM, photoperiod-induzierbar)
7. [PubMed — Stimulation of CAM Photosynthesis in *Kalanchoë blossfeldiana*](https://pubmed.ncbi.nlm.nih.gov/16666163/) — Bestätigung CAM-Stoffwechsel
8. [MDPI Antioxidants 2022 — Low-Intensity Blue Light Induces Flowering in Kalanchoe (PMC9137757)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9137757/) — obligate Kurztagspflanze, kritische Tageslänge ~12 h
9. [Missouri Botanical Garden — Kalanchoe blossfeldiana Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=279373) — Standort (Halbschatten/helles Licht), Kulturansprüche
10. [Clemson HGIC — Kalanchoe Factsheet](https://hgic.clemson.edu/factsheet/kalanchoe/) — Mindesttemperatur, Überwinterung, Standort
11. [The Practical Planter — Kalanchoe Winter Care](https://thepracticalplanter.com/kalanchoe-winter-care/) — Überwinterung (Temperatur, Gießen, Licht)
12. [New York Botanical Garden — Houseplant Care: Kalanchoe](https://libguides.nybg.org/kalanchoe) — Überwinterung, Kulturhinweise
13. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling-Ausbringrate Schmierläuse
14. [Koppert — Aphidius colemani (Aphipar)](https://www.koppert.com/aphipar/) — Nützling-Ausbringrate Blattläuse, Etablierungszeit
15. [Cornell NYSIPM — Phytoseiulus persimilis Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Nützling gegen Spinnmilben, Ausbringrate
16. [South El Monte Hydroponics — Kalanchoe blossfeldiana](https://southelmontehydroponics.com/kalanchoe-blossfeldiana/) — Boden-pH 6.0–7.0
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
