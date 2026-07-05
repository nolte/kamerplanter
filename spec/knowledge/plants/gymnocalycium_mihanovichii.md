# Mondkaktus — Gymnocalycium mihanovichii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/gymnocalycium-mihanovichii/), [Gardenia.net](https://www.gardenia.net/plant/gymnocalycium-mihanovichii-moon-cactus-grow-care-guide), [Wikipedia — Gymnocalycium](https://en.wikipedia.org/wiki/Gymnocalycium_mihanovichii), [Succulents and Sunshine](https://www.succulentsandsunshine.com/types-of-succulents/gymnocalycium-mihanovichii-moon-cactus/), [MasterClass Moon Cactus Care](https://www.masterclass.com/articles/moon-cactus-care-guide)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Gymnocalycium mihanovichii | `species.scientific_name` |
| Volksnamen (DE/EN) | Mondkaktus, Bunter Pfropfkaktus; Moon Cactus, Ruby Ball Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Gymnocalycium | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Gymnocalycium auffindbar; verfügbare Quellen nennen nur Survival-/CAM-Schwellen (Mindesttemperatur ~10°C, CAM-Stomata schließen >18°C Nacht), keine GDD-Basis --> | `species.base_temp` |
| Lebensdauer (Jahre) | veredelt ('Hibotan'-Pfropfung) 3–5; chlorophyllhaltige Wildform mehrere Jahrzehnte (≥ 20) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Kritische Tageslänge (h) | — (tagneutral; Blühinduktion durch kühle Trockenruhe, nicht über Photoperiode) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 10°C; Zimmerpflanze | `species.hardiness_detail` |
| Heimat | Paraguay, Bolivien, Nordargentinien (Unterholz-Kaktus; wächst natürlich im Schatten größerer Pflanzen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit — Veredelung:** Der im Handel erhältliche "Mondkaktus" ist ein veredelter Kaktus — ein Gymnocalycium mihanovichii 'Hibotan' (chlorophyll-freie Mutante in Rot, Orange, Gelb oder Violett) wird auf einen grünen Pfropfunterlage-Kaktus (häufig Hylocereus undatus = Drachenfrucht-Kaktus) aufgepfropft. Der bunte Scion ist vollständig von der Unterlage abhängig (kein Chlorophyll). Lebensdauer: 3–5 Jahre, da die Unterlage (Hylocereus) oft schneller wächst als der Scion.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Dormanz & Blühinduktion:** *Gymnocalycium* benötigt eine ausgeprägte kühle (5–12 °C), vollständig trockene, helle Winterruhe von 2–4 Monaten als zwingenden Auslöser der Blütenknospenbildung im Folgefrühjahr — ohne diese Ruhe wächst die Pflanze vegetativ weiter, blüht aber nicht (`dormancy_required: true`). Es handelt sich um eine kalt-trockene Ruhephase (Dormanz), nicht um eine Vernalisation im engeren Sinn (`vernalization_required: false`); die Blühinduktion läuft tagneutral, also nicht über die Photoperiode. Für das veredelte Hibotan-Produkt ist die kühle Ruhe weniger blührelevant (der chlorophyllfreie Scion blüht selten), bleibt aber für die Gesundheit des Pfropfsystems empfehlenswert. Lebensdauer-Spanne: veredeltes Exemplar 3–5 Jahre, chlorophyllhaltige Wildform mehrere Jahrzehnte.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (rosa bis weiße Blüten der Unterlage oder Scion) | `species.bloom_months` |

<!-- Quelle: growing-phase-auditor 2026-07 -->
**Korrektur 2026-07 (growing-phase-auditor):** Blütemonate von `4, 5, 6` auf `5, 6, 7` korrigiert. Vier unabhängige Quellen belegen übereinstimmend "späten Frühling bis Frühsommer"/Sommer als Blühzeitraum, keine nennt April: (1) NC State Extension — "flowers in late spring to early summer"; (2) Pflanzenfreunde.com — Blütezeit der Gattung Gymnocalycium "Mai–Juli"; (3) World of Succulents — Blüte "late spring to early summer", beobachtete Einzelfälle erste Juni- bis Mitte-Juli-Woche; (4) LLIFLE Encyclopedia of Cacti — *G. mihanovichii* als "summer grower", blüht bevorzugt im Sommer bei Kali-Düngung. Der bisherige Wert (April) ist in keiner der vier Quellen belegt und passt auch nicht zum dokumentierten Jahresverlauf in §4.2 ("Mär: Aufwecken" → 2 Monate vegetatives Wachstum vor Blütenbeginn ist plausibler als Blüte bereits einen Monat nach dem Aufwecken). Konfidenz: ✅ GESICHERT (4/4 Quellen stimmen überein).
<!-- /Quelle: growing-phase-auditor 2026-07 -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | grafting; offset | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Vermehrung:** Die bunte Hibotan-Mutante ist ohne Pfropfunterlage nicht lebensfähig. Pfropfen erfordert sterile Bedingungen, scharfes Messer und passendes Trägermaterial (Hylocereus-Unterlage). Manche Exemplare bilden Kindel, die ebenfalls gepfropft werden können. Heimvermehrung für den normalen Hobbybereich schwierig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine; Stacheln können zu mechanischen Verletzungen führen | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Bei zu schnellem Wachstum der Unterlage kann der Scion neu gepfropft werden (Repfropfen).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.3–1 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–15 (Gesamthöhe inkl. Pfropfkaktus) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 5–10 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Handelsübliche Kakteenerde; pH 6.0–7.0; exzellente Drainage obligatorisch; nie Staunässe | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt (light compensation point) min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 5–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe dS/m) | <!-- DATEN FEHLEN: kein artspezifischer Maas-Hoffman-Schwellenwert für Gymnocalycium belegt; Cactaceae generell salzempfindlich, aber kein quantitativer ECe-Schwellenwert in seriösen Quellen --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN: kein artspezifischer Maas-Hoffman-Slope belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweise zu 1.7:** Lichtkompensationspunkt aus Habitat-Einordnung abgeleitet — *G. mihanovichii* ist ein Unterholz-Kaktus (im natürlichen Bestand im Schatten größerer Pflanzen, vgl. §1.1), schattentolerante Arten zeigen niedrige LCP-Werte von 10–50 µmol/m²/s; die hier angegebene Spanne 10–30 ordnet die Art im schattentoleranten Bereich ein (nur Kompensationspunkt, nicht Sättigung/Photoinhibition). Kakteen tolerieren zwar hohe PPFD-Werte (bis nahe 2000 µmol/m²/s) ohne Photoinhibition, der chlorophyll-freie veredelte Scion verbrennt jedoch in direkter Mittagssonne — daher Halbschatten (`partial_shade`). Salztoleranz: Cactaceae reagieren generell empfindlich auf erhöhte Substrat-Salinität (ECe), *G. mihanovichii* ist kein Halophyt; die Bezugsgröße ist die Substrat-ECe (nicht die Gießwasser-EC). Boden-pH 6.0–7.5 harmonisiert mit §1.6 (Substrat-Empfehlung pH 6.0–7.0) und §2.3 (Nährlösung pH 6.0–7.0).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- SECTION MISSING: seed_profile — vegetativ vermehrt (Pfropfung) -->
### 1.8 Saatgut & Keimung (Seed Profile)

Entfällt für den in diesem Steckbrief beschriebenen Gegenstand. Dieses Dokument bildet ausdrücklich den **im Handel erhältlichen, veredelten "Mondkaktus"** ab (§1.1: "Der im Handel erhältliche 'Mondkaktus' ist ein veredelter Kaktus…") — die chlorophyllfreie Hibotan-Mutante von *G. mihanovichii*, die ohne Pfropfunterlage nicht überlebensfähig ist. Konsistent damit führt §1.3 dieses Dokuments **ausschließlich** `grafting` und `offset` als Vermehrungsmethoden, explizit **kein** `seed`: "Die bunte Hibotan-Mutante ist ohne Pfropfunterlage nicht lebensfähig… Heimvermehrung für den normalen Hobbybereich schwierig." Ein Seed-Profil ist daher für den hier dokumentierten Kulturgegenstand nicht anwendbar.

Hinweis zur Abgrenzung: Die chlorophyllhaltige **Wildform** (grüne Reinart) von *Gymnocalycium mihanovichii* wird in der Kakteenzucht durchaus aus Samen gezogen — dies betrifft jedoch eine andere Kultur-/Handelsform als die in diesem Steckbrief primär beschriebene Handelsware. Sollte künftig ein eigener Steckbrief für die samenvermehrte, chlorophyllhaltige Wildform angelegt werden, ist dort ein vollständiges Seed-Profil zu recherchieren (Keimtemperatur, Saattiefe, Licht-/Dunkelkeimung etc. gemäß den für Kakteen üblichen Parametern).

Quellen (§1.8-Entscheidung): §1.1 und §1.3 dieses Dokuments (bereits oben zitiert); [Wikipedia — Gymnocalycium mihanovichii](https://en.wikipedia.org/wiki/Gymnocalycium_mihanovichii) (Pfropfung der Hibotan-Mutante, fehlendes Chlorophyll); [MasterClass — Moon Cactus Care Guide](https://www.masterclass.com/articles/moon-cactus-care-guide) (Vermehrung ausschließlich über Pfropfung/Kindel, keine Samenvermehrung des Handelsprodukts erwähnt)
<!-- /SECTION MISSING -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung (nach Kauf) | 14–28 | 1 | false | false | medium |
| Vegetativ | 90–365 | 2 | false | false | high |
| Blüte | 14–28 | 3 | false | true | high |
| Winterruhe | 60–90 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–50 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 (Substrat vollständig trocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–15 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 20–40 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.5–3.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 3.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 12–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 21–30 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 10–30 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Vegetativ | 0:1:1 | 0.3–0.6 | 6.0–7.0 | 40 | 20 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Blüte | 0:1:2 | 0.3–0.5 | 6.0–7.0 | 30 | 15 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu Mikronährstoffen (Mn/Zn/Cu/Mo):** Kakteen benötigen Mangan, Zink, Kupfer und Molybdän als Spurenelemente (trace elements) in sehr geringen Mengen; handelsübliche Kakteendünger (z.B. Compo, WUXAL) enthalten diese in chelatierter/sulfatierter Form. Quantitative, artspezifische ppm-Zielwerte für *G. mihanovichii* sind in seriösen Quellen jedoch nicht belegt — die Felder bleiben als `DATEN FEHLEN` markiert. In der Winterruhe wird nicht gedüngt (NPK 0:0:0), daher entfallen die Mikronährstoffe.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kaktusdünger | Compo | Flüssigdünger | 2-6-12 | 1 ml/L alle 4 Wochen | Vegetativ |
| Kakteendünger granuliert | Substral | slow release | 5-10-18 | 1 Msp./Monat | Vegetativ |

### 3.2 Besondere Hinweise zur Düngung

Sehr sparsam düngen — maximal einmal pro Monat während der Wachstumsphase (April bis September). Im Winter überhaupt kein Dünger. Überdüngung führt zum Platzen der Pfropfnaht oder zu übermäßigem Wachstum der Unterlage (die dann den Scion überwächst).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 12 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; Substrat zwischen den Gaben vollständig austrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterruhe | Kein Wasser (fast); kühler, heller Standort | niedrig |
| Mär | Aufwecken | Erstmals leicht wässern; Standort prüfen | mittel |
| Apr–Sep | Aktive Phase | Alle 10–14 Tage gießen; einmal/Monat düngen | mittel |
| Okt | Abdrosseln | Gießen einstellen; Winterstandort vorbereiten | mittel |
| Nov–Dez | Winterruhe | Kühler (10–15°C), hell; minimal wässern | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winter-Maßnahme Monat | 10 (Okt: an kühlen, hellen Winterstandort umstellen, Gießen einstellen) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (März: an wärmeren/helleren Standort zurück, langsam wieder angießen) | `overwintering_profiles.spring_action_month` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterquartier Temp min (°C) | 8 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Wollläuse | Planococcus citri | Weiße Wollmasse an Pfropfnaht und Areolen | medium |
| Wurzelmilben | Rhizoglyphus echinopus | Wachstumsstillstand, Substrat verkrustet | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Fäule Pfropfnaht | fungal/bakteriell | Schwarze, eingesunkene Stelle an Naht | Staunässe, Verletzungen |
| Wurzelfäule | fungal | Weiche Unterlage, Welke | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol | mechanical | Isopropylalkohol | Wattestäbchen | 0 | Wollläuse |
| Stumpf-Abtrennen | cultural | — | Faulige Stellen steril abschneiden; Holzkohle | 0 | Fäule |
| Substrat erneuern | cultural | — | Topf komplett neu | 0 | Wurzelfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Wollläuse (Planococcus citri) | 10–20 Käfer/m² (Spanne 5–40/m²), 2–3 Ausbringungen im Abstand von 1–2 Wochen | 2–4 Wochen; optimal bei 25–28°C |
| Raubmilbe (predatory soil mite) | Stratiolaelaps scimitus (syn. Hypoaspis miles) | Wurzelmilben (Rhizoglyphus echinopus), Trauermücken-Larven | 100–500 Milben/m² (vorbeugend), bodengestützt eingebracht | 2–3 Wochen |

**Hinweise zu 5.4:** *Cryptolaemus montrouzieri* (Mealybug Destroyer) ist der klassische Wolllaus-Antagonist (Larven und Adulte fressen Schmierläuse/Pseudococcidae); für den indoor gehaltenen Mondkaktus eher bei stärkerem Befall mehrerer Pflanzen sinnvoll. *Stratiolaelaps scimitus* lebt im oberen Substrat und erbeutet Wurzel-/Knollenmilben sowie Trauermückenlarven — passend gegen die in §5.1 gelistete Wurzelmilbe. Etablierung gelingt nur in feuchtem, nicht staunässendem Substrat; beim trocken gehaltenen Kaktus daher punktuell bei akutem Wurzelmilbenbefall einsetzen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Mammillaria | Mammillaria spp. | 0.8 | Gleiche Familie, gleiche Pflege | `compatible_with` |
| Opuntia | Opuntia microdasys | 0.7 | Gleiche Familie | `compatible_with` |
| Echeveria | Echeveria elegans | 0.7 | Sukkulente, ähnliche Pflege | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Gymnocalycium (grün) | Gymnocalycium mihanovichii | Die Wildform ist robust und chlorophyllhaltig | Ohne Pfropfung lebensfähig; langlebiger |
| Stachelloser Kaktus | Astrophytum myriostigma | Ähnlich klein, dekorativ | Kein Pfropfen nötig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Gymnocalycium mihanovichii,Mondkaktus;Bunter Pfropfkaktus;Moon Cactus,Cactaceae,Gymnocalycium,perennial,day_neutral,herb,fibrous,10a;10b;11a;11b;12a;12b,0.0,"Paraguay, Bolivien, Argentinien",yes,0.5,8,15,10,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [NC State Extension — Gymnocalycium mihanovichii](https://plants.ces.ncsu.edu/plants/gymnocalycium-mihanovichii/) — Botanische Einordnung
2. [Gardenia.net — Moon Cactus](https://www.gardenia.net/plant/gymnocalycium-mihanovichii-moon-cactus-grow-care-guide) — Kulturdaten
3. [Wikipedia — Gymnocalycium mihanovichii](https://en.wikipedia.org/wiki/Gymnocalycium_mihanovichii) — Taxonomie, Pfropfung
4. [Succulents and Sunshine — Moon Cactus](https://www.succulentsandsunshine.com/types-of-succulents/gymnocalycium-mihanovichii-moon-cactus/) — Pflegehinweise
5. [MasterClass — Moon Cactus Care Guide](https://www.masterclass.com/articles/moon-cactus-care-guide) — Vermehrung, Schädlinge
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Wikipedia — Crassulacean acid metabolism (CAM)](https://en.wikipedia.org/wiki/Crassulacean_acid_metabolism) — CAM-Photosynthese-Typ (>99 % der Cactaceae sind CAM)
7. [Henry Shaw Cactus and Succulent Society — C3, C4, CAM](https://hscactus.org/resources/digest/plant-info/c3-c4-cam/) — CAM-Einordnung Kakteen/Sukkulenten
8. [PubMed — CAM photosynthesis in columnar cactus seedlings (Am. J. Bot. 94:1344)](https://pubmed.ncbi.nlm.nih.gov/21636502/) — Lichtanspruch CAM-Kakteen, Toleranz hoher PPFD
9. [Springer/Oecologia — Water relations and photosynthesis of Ferocactus acanthodes](https://link.springer.com/article/10.1007/BF00345817) — CAM-Temperaturoptimum nächtlicher CO₂-Fixierung; stomatäre Reaktion auf Temperatur
10. [PlantIn — Moon Cactus Care](https://myplantin.com/plant/246) — Boden-pH 6.0–7.5, Standort/Drainage
11. [The Bloom UP — Gymnocalycium mihanovichii](https://www.thebloomup.com/gymnocalycium-mihanovichii/) — Substrat-pH, schnell drainierend
12. [growplants.org — Gymnocalycium mihanovichii](https://www.growplants.org/growing/gymnocalycium-mihanovichii) — flaches, feines Wurzelsystem; flache Töpfe
13. [Tula House — Gymnocalycium mihanovichii](https://tula.house/blogs/tulas-plant-library/gymnocalycium-mihanovichii) — flache Wurzeln, Topftiefe
14. [Semantic Scholar — Salinity Tolerance of Cacti and Succulents (Schuch & Kelly)](https://www.semanticscholar.org/paper/Salinity-Tolerance-of-Cacti-and-Succulents-Schuch-Kelly/ebde84504c21858024b88ba9006d7ec05ca6fa4f) — generelle Salzempfindlichkeit von Kakteen (ECe-Bezug)
15. [Gardenia.net — Moon Cactus (Temperatur)](https://www.gardenia.net/plant/gymnocalycium-mihanovichii-moon-cactus-grow-care-guide) — Wachstumstemperatur-Optimum 20–30 °C
16. [greg.app — Moon Cactus Temperature](https://greg.app/moon-cactus-temperature/) — Tag-/Nachttemperaturbereiche
17. [American Orchid Society — Humidity and VPD](https://www.aos.org/orchids/articles/humidity-and-vapor-pressure-deficit) — CAM-Pflanzen tolerieren hohe VPD (geringe VPD-Sensitivität)
18. [Zhen & Bugbee — Photosynthesis in sun and shade: far-red photons (New Phytologist 2022)](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.18375) — Far-Red-Anteil im Unterholz/Schatten
19. [Viriar — understory light quality / Far-Red](https://www.biorxiv.org/content/10.1101/829036v1.full) — erhöhter Far-Red-Anteil unter Kronendach (Unterholz-Habitat)
20. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Wolllaus-Nützling, Ausbringrate/Etablierung
21. [Koppert — Stratiolaelaps scimitus (Hypoaspis miles)](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/stratiolaelaps-scimitus-hypoaspis-miles/) — Raubmilbe gegen Wurzel-/Bodenmilben, Ausbringrate
22. [The Cactus Expert — Fertilizer / trace elements](https://www.cactusexpert.org/cultivation-of-cacti/fertilizer.html) — Mn/Zn/Cu/Mo als Spurenelemente bei Kakteen (qualitativ)
23. [Viriar — Gymnocalycium baldianum (Dormanz/Blüte)](https://www.viriar.com/blogs/cactus-encyclopedia/gymnocalycium-baldianum) — kühle, trockene Winterruhe als Blühtrigger; Cafe Planta/Cactus Classification — Lebensdauer
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: growing-phase-auditor 2026-07 -->
24. [NC State Extension — Gymnocalycium mihanovichii](https://plants.ces.ncsu.edu/plants/gymnocalycium-mihanovichii/) — Blütezeit "late spring to early summer" (Korrektur Blütemonate)
25. [Pflanzenfreunde.com — Gymnocalycium](https://www.pflanzenfreunde.com/lexika/kakteen/gymnocalycium.htm) — Blütezeit Gattung Mai–Juli; Winterruhe Nov–Mär bei 5–8°C
26. [World of Succulents — Gymnocalycium mihanovichii](https://worldofsucculents.com/gymnocalycium-mihanovichii-moon-cactus/) — Blüte "late spring to early summer", beobachtet Anfang Juni bis Mitte Juli
27. [LLIFLE Encyclopedia of Cacti — Gymnocalycium mihanovichii](https://llifle.com/Encyclopedia/CACTI/Family/Cactaceae/11929/Gymnocalycium_mihanovichii) — Sommerwachser/-blüher, trockene Winterruhe min. 0°C, Wildform frosttolerant bis -5°C trocken (USDA 9-10)
<!-- /Quelle: growing-phase-auditor 2026-07 -->
