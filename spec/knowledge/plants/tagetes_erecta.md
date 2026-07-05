# Aufrechte Studentenblume — Tagetes erecta

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Royal Horticultural Society, University of Florida IFAS Extension, USDA PLANTS Database, Rodale Institute Companion Planting, Colorado State University Extension

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tagetes erecta | `species.scientific_name` |
| Volksnamen (DE/EN) | Aufrechte Studentenblume, Afrikanische Studentenblume, Azteken-Ringelblume; African Marigold, Aztec Marigold, Big Marigold | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Tagetes | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchs (°C) | 10 | `species.base_temp` |
| Lebensdauer (Jahre) | — (einjährig; nicht zutreffend) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (tropisch-warmblütige Art ohne Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (nicht zutreffend) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 12 | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a–11b (als Einjährige in 2a–11b kultivierbar) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; stirbt bei Frost; in Mitteleuropa als robuste einjährige Sommerblume nach letztem Frost (Mitte Mai) bis Oktober; selbstaussaat in milden Wintern möglich | `species.hardiness_detail` |
| Heimat | Mexiko, Mittelamerika (Azteken-Kulturpflanze) | `species.native_habitat` |
| Allelopathie-Score | 0.5 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**IPM-Schlüsselpflanze:** Tagetes erecta ist eine der wichtigsten Begleitpflanzen im Gemüsegarten. Alpha-Terthienyl in den Wurzeln hemmt Wurzel-Nematoden (Meloidogyne spp.) wirksam — nachgewiesen in Feldversuchen. Blüten-Duftstoffe (Terpengemisch) wirken auf viele Schädlinge abstoßend oder verwirrend. Blüten locken Schwebefliegen, Marienkäfer und andere Nützlinge an.

**Allelopathie:** Positiver Allelopathie-Score — Tagetes fördert viele Nachbarn durch Schädlingsabwehr, hemmt aber einige empfindliche Arten (Hülsenfrüchte, Kohl in sehr dichter Nachbarschaft).

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Photoperiode & Photosynthese:** Tagetes erecta ist ein fakultativer Kurztagblüher (facultative short-day) mit einer kritischen Tageslänge (critical daylength) von etwa 12 h; unter Langtag verzögert sich die Blüte, geht aber nicht völlig aus (deshalb `photoperiod_type=short_day`, nicht `day_neutral`). Als Korbblütler (Asteraceae) betreibt die Art C3-Photosynthese (C3 ist innerhalb der Asteraceae der Regelfall; C4 ist auf wenige Gattungen wie *Flaveria* beschränkt, CAM kommt nicht vor).

**GDD-Basistemperatur (base temperature):** Für die GDD-Berechnung der warmen Hauptwuchsphase wird die für wärmeliebende, frostempfindliche Arten übliche Basis von ~10 °C angesetzt; unterhalb von ~10 °C stockt das Wachstum. Hinweis zur Abgrenzung: Floristikmodelle für die *Blührate* von Tagetes nennen ein deutlich tieferes statistisches Tmin von ~1–2 °C (z. B. *T. patula* Tmin ≈ 1,1 °C) — das ist die untere Asymptote des Blühratenmodells, NICHT die Wuchs-GDD-Basis und darf nicht als solche verwendet werden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 6–8 (Anzucht im Warmhaus ab März) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 7–14 (Direktsaat einfach; warm genug) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4 (Vorkultur); 5, 6 (Direktsaat Freiland) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Schnittblumen 6–10; Blüten essbar) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9, 10 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (Blüten essbar; in der Küche als Safran-Ersatz und Salatzugabe verwendet) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Alpha-Terthienyl (nematodenfeindlich; in Wurzeln; kein Risiko für Menschen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Pyrethrum-Verwandtschaft; Asteraceae-Allergen; manche Personen reagieren auf Hautkontakt) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Korbblütler-Pollen; mäßig; August-Oktober) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Deadheading; verblühte Köpfe entfernen verlängert Blütezeit) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8, 9 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–40 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr lichtbedürftig; kaum Indoor möglich ohne Kunstlicht) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige, leicht sandige Erde; pH 6,0–7,5; verträgt schwere Böden schlecht; Perlite-Anteil 15–20% | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.5 | `species.soil_ph_preference` |

**Hinweise zu §1.7:**
- *Sonnentoleranz (shade tolerance):* Vollsonnenart — PFAF: „cannot grow in the shade", NC State Extension: „dislikes full shade". Mind. 6 h direkte Sonne nötig; in Mitteleuropa (USDA 6–8) leichte Mittagsbeschattung im Hochsommer toleriert, aber kein Schattenstandort.
- *Lichtsättigung:* Die maximale Lutein-Bildung der Blüte liegt bei ≈500 µmol/m²/s (Lichtsättigungs-/Optimumwert) — NICHT der Kompensationspunkt; daher nicht ins LCP-Feld eingetragen. Ein artspezifischer Kompensationspunkt (Netto-Photosynthese = 0) ist in den Quellen nicht belegt → DATEN FEHLEN.
- *Staunässe (waterlogging):* Hohe Empfindlichkeit; Wurzelfäule (Pythium) bei Nässe, durchlässiger Boden zwingend (PFAF, NC State Extension, Gartenia).
- *Salztoleranz (salt tolerance):* Als „moderately tolerant" eingestuft, da Wachstum erst bei Gießwasser-EC (ECw) > ~8 dS/m signifikant zurückgeht (USDA-ARS Niu et al. 2018; USDA Salt Tolerance Chapter). Diese Schwelle bezieht sich auf die Gießwasser-Leitfähigkeit (ECw), NICHT auf die Maas-Hoffman-Bezugsgröße Substrat-ECe (Sättigungsextrakt). Ein belegter Maas-Hoffman-ECe-Schwellenwert (a) bzw. Slope (b) für *T. erecta* liegt nicht vor → beide DATEN FEHLEN.
- *Boden-pH:* Mild sauer bis mild alkalisch toleriert; Vorzug 6,0–7,5 (harmonisiert mit §1.6 Substrat-Empfehlung und §2.3 Nährstoffprofilen). Unterhalb pH ~5,5 droht Mangan-Toxizität (Mn-empfindliche Art), daher untere Grenze nicht weiter absenken.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-07 (Batch 11, Issue #301 seed-profile-backfill) -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 21 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 24 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.6 (¼ Zoll) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 4 (unterer Wert; Spanne 4–14 Tage bei Optimaltemperatur) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | 2 (Spanne 2–3; höchste Keimrate im ersten Jahr) | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | indifferent (Licht für Keimung nicht zwingend erforderlich; Saatgut wird praxisüblich dünn mit Vermiculit abgedeckt) | `species.seed_profile.light_germination` |
| Vorbehandlung | keine (kein Stratifizierungs- oder Skarifizierungsbedarf) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: nur ein Katalogwert (218 Korn/g, Crackerjack-Sorte) auffindbar, kein zweiter unabhängiger Beleg zur Cross-Validierung --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- DATEN FEHLEN: Kultur erfolgt praxisüblich über Vorkultur/Transplant, keine belegte Flächen-Aussaatdichte für Direktsaat --> | `species.seed_profile.sowing_density_per_m2` |

**Quellen (§1.8):** [Tagetes Plant Growing Guide — GardenersHQ](https://www.gardenershq.com/Tagetes-Marigold.php) (Keimtemperatur 22–24 °C, Saattiefe ¼ Zoll, Licht nicht zwingend, Vermiculit-Abdeckung); [Crackerjack African Marigold Seeds — Everwilde](https://www.everwilde.com/store/African-Marigold-Crackerjack-Wildflower-Seeds.html) und [Marigolds Are Easily Grown From Seed — Horticulture.co.uk](https://horticulture.co.uk/marigolds/sowing/) (Keimdauer 4–14 Tage); [How to Save Marigold Seeds for Next Year — Ramniwas Bagh](https://ramniwasbagh.com/how-to-save-marigold-seeds-for-next-year/) und [Seed storage of African marigold (Tagetes erecta L.) for ex-situ conservation — Ingenta/Seed Science and Technology](https://www.ingentaconnect.com/content/ista/sst/2004/00000032/00000002/art00020) (Keimfähigkeitsdauer 2–3 Jahre).
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | medium |
| Vegetativ | 14–28 | 3 | false | false | high |
| Knospenansatz | 14–21 | 4 | false | false | high |
| Hauptblüte | 60–120 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 (Lichtkeimer; Licht hilfreich) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | >13 (lange Tage verhindern vorzeitige Blüte; Kurztagblüher) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.7 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptblüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | ≤13 (kürzere Tage ab August; Blüteninduktion) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.9–1.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.50 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.5 | — | — |
| Sämling | 1:1:1 | 0.4–0.8 | 6.0–7.5 | 50 | 20 |
| Vegetativ | 2:1:1 | 0.6–1.0 | 6.0–7.5 | 70 | 25 |
| Blüte | 1:2:2 | 0.8–1.4 | 6.0–7.5 | 70 | 30 |

**Hinweis:** Tagetes ist ein Leichtezer — zu viel Dünger (v.a. N) erzeugt viel Blattwerk auf Kosten der Blüten. Lieber wenig düngen; Blütenqualität wichtiger als Wachstum.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo):** Artspezifische Phasen-Sollwerte (ppm) für Mangan (`nutrient_profiles.manganese_ppm`), Zink (`nutrient_profiles.zinc_ppm`), Kupfer (`nutrient_profiles.copper_ppm`) und Molybdän (`nutrient_profiles.molybdenum_ppm`) sind für *T. erecta* nicht aus zwei unabhängigen seriösen Quellen belegt → DATEN FEHLEN. Fachlich gesichert ist lediglich die Mangan-Empfindlichkeit der Art: Bei Substrat-pH < 5,5 wird Mn übermäßig löslich und kann Mn-Toxizität auslösen (Korbblütler/Marigold gelten als Mn-empfindlich). Praxisempfehlung: pH ≥ 6,0 halten (siehe §1.7 und §2.3-pH-Spalte), dann tritt weder Mn-Toxizität noch Fe/Mn-Mangel auf. <!-- DATEN FEHLEN: Mn/Zn/Cu/Mo ppm je Phase -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Keimung → Sämling | time_based | 5–10 Tage; Keimblätter sichtbar |
| Sämling → Vegetativ | time_based | 14–21 Tage; 2 echte Blattpaare |
| Vegetativ → Blüte | event_based | Kurztagbedingungen (≤13h) oder Pikierung/Auspflanzung Stress |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Ausbringrate | Phasen |
|---------|-------|-----|-----|-------------|--------|
| Blumendünger flüssig | Compo | Flüssig | 6-3-6 | 5 ml/L alle 2 Wochen | Blüte |
| Osmocote 3–4 Monate | Osmocote | Slow-Release | 14-13-13 | 3–5 g/L Substrat | Pflanzung |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee | eigen | flüssig organisch | 1:10; 2×/Monat | Jun–Sep |
| Hornmehl | diverse | organisch | 2–3 g/L Substrat | Substrat-Mix |

### 3.2 Besondere Hinweise zur Düngung

Weniger ist mehr bei Tagetes. Gut angereicherte Gartenerde oder Kompost-basiertes Substrat reichen oft ohne Nachdüngung aus. Wöchentliche Flüssigdüngung im Balkonkasten sinnvoll (Auswaschung durch Gießen). Hohe P/K-Ratio fördert Blütenreichtum. Überdüngung mit N führt zu üppigem grünen Wachstum ohne Blüten.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig; kein Winter) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkwasser verträglich; pH-Toleranz bis 7,5 | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Anzucht | Im Warmhaus; 20–25°C; Direktsaat auf Substrat; 1 cm Erde; Licht | hoch |
| Apr–Mai | Pikierung / Abhärtung | In Einzel-Töpfe pikieren; langsam abhärten | mittel |
| Mai | Auspflanzung | Nach letztem Frost; sonniger Standort | hoch |
| Jun–Sep | Deadheading | Verblühte Köpfe regelmäßig abzwicken — verlängert Blüte bis Oktober | hoch |
| Aug | Saatgut gewinnen | Verwelkte Köpfe reifen lassen; Samen ernten und trocknen | niedrig |
| Sep–Okt | Saisonende | Nach erstem Frost; Pflanzen kompostieren; Beet räumen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; gelbliche Blätter bei Trockenheit | Blatt | Blüte (heiß-trocken) |
| Blattläuse | Macrosiphum euphorbiae | Kolonien; weniger häufig als bei anderen Arten | Trieb | Sämling |
| Tausendfüßer | Scutigerella immaculata | Wurzelfraß; Welke | Wurzel | Keimling |

**Hinweis:** Tagetes erecta ist generell robust und wenig schädlingsanfällig. Der intensive Duft hält viele Insekten fern. In der Praxis kaum IPM-Maßnahmen nötig.

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal (Erysiphe cichoracearum) | Weißgrauer Belag | trocken-warm; Spätsommer |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Pilzbefall; feuchte Blüten | kühl-feucht; alte Blüten |
| Wurzelfäule | fungal (Pythium spp.) | Welke; Wurzelnekrose | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Spinnmilben, Blattläuse |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen | 14 | Echter Mehltau |
| Befallene Teile entfernen | cultural | — | Sofort | 0 | Grauschimmel |
| Drainage verbessern | cultural | — | Substrat anpassen | 0 | Wurzelfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–10 Tiere/m² (Wiederholung wöchentlich bei Bedarf) | Kontrolle in ~14 Tagen bei < 30 °C und > 60 % rF |
| Schlupfwespe | Aphidius colemani | Blattläuse (Macrosiphum euphorbiae) | 0,1–3 Tiere/m², 2 Freilassungen im Wochenabstand | Erste Mumien nach 10–14 Tagen |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (ergänzend zu A. colemani) | 1–3 Larven/m² | Larvenfraß ab ~3–5 Tagen <!-- DATEN FEHLEN: exakte Etablierungszeit --> |

**Hinweis zu §5.4:** Tagetes erecta ist von Natur aus robust und kaum schädlingsanfällig (siehe §5.1); Nützlingseinsatz ist nur unter Glas/Folie bei stärkerem Spinnmilben- oder Blattlausbefall relevant. Im Freiland fördert Tagetes selbst Nützlinge (Schwebefliegen, Marienkäfer) und braucht in der Regel keine gezielte Ausbringung. Die Nützling-Wirt-Zuordnung folgt der etablierten Praxis (Phytoseiulus → Spinnmilben; Aphidius/Aphidoletes → Blattläuse).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Leichtezer |
| Fruchtfolge-Kategorie | Einjährige Zierpflanze; Companion Plant |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | 2 Jahre empfohlen (Botrytis-Dauerformen) |

**Nematoden-Sanierung:** Tagetes erecta und T. patula wirken als biologische Nematizide. 3 Monate Tagetes-Anbau auf befallenen Flächen reduziert Meloidogyne-Populationen um 90%. Anschließend 4 Monate Brache für maximalen Effekt. Wissenschaftlich gut belegt (Ploeg & Maris 1999, Nematology).

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.95 | Klassischer Companion: Nematoden-Schutz; Thrips-Abwehr; Bestäuber | `compatible_with` |
| Aubergine | Solanum melongena | 0.9 | Nematoden-Schutz für Aubergine | `compatible_with` |
| Paprika | Capsicum annuum | 0.9 | Nematoden-Schutz; Schädlingsabwehr | `compatible_with` |
| Gurke | Cucumis sativus | 0.8 | Schwebefliegen-Anlockung; Bestäubung | `compatible_with` |
| Kürbis | Cucurbita spp. | 0.8 | Käferpopulations-Reduktion (anekdotisch); Nützlinge | `compatible_with` |
| Kohl | Brassica oleracea spp. | 0.8 | Schädlingsabwehr; Kohlweißling-Verwirrung | `compatible_with` |
| Karotte | Daucus carota | 0.7 | Möhrenfliegen-Verwirrung; Nützlinge | `compatible_with` |
| Rose | Rosa spp. | 0.8 | Blattlausabwehr; Blühharmonie | `compatible_with` |
| Sojabohne | Glycine max | 0.8 | Nematoden-Schutz; Schwebefliegen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Bohnen (Buschbohne) | Phaseolus vulgaris | Tagetes kann Bohnenentwicklung hemmen (Alpha-Terthienyl bei sehr dichtem Anbau) | mild | `incompatible_with` |
| Kohl (sehr dicht) | Brassica oleracea | Allelopathische Hemmung bei sehr dichtem Anbau möglich | mild | `incompatible_with` |

**Hinweis:** Die "schlechten Nachbarn" sind wissenschaftlich nicht eindeutig belegt. Bei normalem Pflanzenabstand (30 cm) kaum negative Effekte. Tagetes ist einer der universellsten Begleitpflanzen.

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Asteraceae (Korbblütler) | `shares_pest_risk` | Echter Mehltau, Grauschimmel, Spinnmilben | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tagetes erecta |
|-----|-------------------|-------------|----------------------------------|
| Französische Studentenblume | Tagetes patula | Gleiche Gattung | Kompakter; stärkere Nematoden-Wirkung (T. patula > T. erecta) |
| Feinblättrige Studentenblume | Tagetes tenuifolia | Gleiche Gattung | Stark duftend; feinblättrig; Küchen-Tagetes |
| Azteken-Ringelblume | Tagetes minuta | Gleiche Gattung | Stärkste Nematoden-Wirkung aller Tagetes |
| Ringelblume | Calendula officinalis | Asteraceae; Kompagnon | Winterhart als Aussaat; medizinisch; andere Wirkungsweise |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Tagetes erecta,"Aufrechte Studentenblume;Afrikanische Studentenblume;African Marigold;Aztec Marigold",Asteraceae,Tagetes,annual,short_day,herb,fibrous,"9a;9b;10a;10b;11a;11b",0.5,"Mexiko;Mittelamerika",yes,limited,yes,false,false,light_feeder,false,tender,"3;4;5;6","","6;7;8;9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Inca Gold,Tagetes erecta,"tall;large_flower;golden_yellow;cut_flower",55,hybrid
Vanilla,Tagetes erecta,"cream_white;unique_color;tall",60,open_pollinated
American Giant Mix,Tagetes erecta,"very_tall;mixed_colors;cut_flower",65,open_pollinated
```

---

## Quellenverzeichnis

1. [Royal Horticultural Society — Tagetes](https://www.rhs.org.uk/plants/tagetes) — Gartenpraxis, Mischkultur
2. [Rodale Institute — Companion Planting Guide](https://rodaleinstitute.org) — IPM, Nützlinge
3. [University of Florida IFAS — Marigold Production](https://edis.ifas.ufl.edu) — Gewächshauskultur
4. [Ploeg & Maris (1999) — Nematology 1(5)](https://brill.com/view/journals/nemy) — Wissenschaftliche Nematoden-Wirkung
5. [Colorado State University Extension — Companion Plants](https://extension.colostate.edu) — Mischkultur-Empfehlungen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Plants For A Future (PFAF) — Tagetes erecta](https://pfaf.org/user/Plant.aspx?LatinName=Tagetes+erecta) — Boden-pH, Bodenart, Sonnen-/Schattentoleranz („cannot grow in the shade"), Feuchteansprüche
7. [NC State Extension — Tagetes erecta Plant Toolbox](https://plants.ces.ncsu.edu/plants/tagetes-erecta/) — Lichtbedarf (volle Sonne, „dislikes full shade"), Drainage, pH-Toleranz
8. [Niu et al. (2018) — Responses of Marigold Cultivars to Saline Water Irrigation, HortTechnology 28(2), USDA-ARS](https://www.ars.usda.gov/ARSUserFiles/50820500/GPRG/2018PublicationsandSummaries/2018_Responses%20of%20Marigold%20Cultivars%20to%20Saline%20Water%20Irrigation.pdf) — Salztoleranz „moderately tolerant", ECw-Schwelle ~8 dS/m
9. [USDA-ARS — Plant Salt Tolerance (Chapter 13)](https://www.ars.usda.gov/ARSUserFiles/20360500/pdf_pubs/P2246.pdf) — Maas-Hoffman-Bezugsgröße ECe vs. ECw, Salztoleranzklassen
10. [Blanchard & Runkle / MSU Floriculture — Growing Crops Above Their Base Temperature](https://www.canr.msu.edu/uploads/resources/pdfs/grow-crops-above-base-temp.pdf) — Basistemperatur-Konzept; statistisches Tmin der Marigold-Blührate (~1 °C) vs. Wuchs-GDD-Basis
11. [Blanchard, Runkle & Frantz (2007) — Modeling Temperature & DLI Effects on Tagetes patula, JASHS 132(3)](https://journals.ashs.org/jashs/view/journals/jashs/132/3/article-p283.xml) — Blührate, Tmin ≈ 1,1 °C (Blühratenmodell), DLI-Wirkung
12. [Turkish J. Agriculture (2018) — Effects of Photoperiodism on Tagetes erecta](https://agrifoodscience.com/index.php/TURJAF/article/view/1341) — fakultativer Kurztag, kritische Tageslänge ~12 h
13. [Yamori et al. (2013) — Temperature response of photosynthesis in C3, C4, CAM (Review)](https://publish.uwo.ca/~dway4/files/Yamori%20et%20al.%202013.pdf) — C3-Temperaturoptimum, Abgrenzung C3/C4/CAM
14. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/spidex/) & [Cornell NYSIPM Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Spinnmilben-Raubmilbe, Ausbringrate/Etablierung
15. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Blattlaus-Schlupfwespe, Ausbringrate/Etablierung
16. [PT Horticulture — Role of Manganese in Plant Culture](https://www.pthorticulture.com/en-us/training-center/role-of-manganese-in-plant-culture) — Mn-Empfindlichkeit Marigold, Mn-Toxizität bei pH < 5,5
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Steckbrief-Erweiterung 2026-07 (Batch 11, Issue #301 seed-profile-backfill) -->
17. [Tagetes Plant Growing Guide — GardenersHQ](https://www.gardenershq.com/Tagetes-Marigold.php) — Keimtemperatur, Saattiefe, Lichtangabe
18. [Crackerjack African Marigold Seeds — Everwilde](https://www.everwilde.com/store/African-Marigold-Crackerjack-Wildflower-Seeds.html) — Keimdauer, Saatgutkatalogdaten (218 Korn/g)
19. [Tagetes Marigolds Are Easily Grown From Seed — Horticulture.co.uk](https://horticulture.co.uk/marigolds/sowing/) — Keimdauer-Bestätigung
20. [How to Save Marigold Seeds for Next Year — Ramniwas Bagh](https://ramniwasbagh.com/how-to-save-marigold-seeds-for-next-year/) — Keimfähigkeitsdauer 2–3 Jahre
21. [Seed storage of African marigold (Tagetes erecta L.) for ex-situ conservation — Seed Science and Technology / Ingenta](https://www.ingentaconnect.com/content/ista/sst/2004/00000032/00000002/art00020) — Keimfähigkeitsdauer, Lagerbedingungen
<!-- /Quelle: Steckbrief-Erweiterung 2026-07 -->
