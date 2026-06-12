# Geweihfarn — Platycerium bifurcatum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Old Farmer's Almanac](https://www.almanac.com/plant/staghorn-fern-care-growing-platycerium-bifurcatum), [Gardenia.net](https://www.gardenia.net/plant/platycerium-bifurcatum-staghorn-fern), [NC State Extension](https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/), [Guide to Houseplants](https://www.guide-to-houseplants.com/staghorn-fern.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Platycerium bifurcatum | `species.scientific_name` |
| Volksnamen (DE/EN) | Geweihfarn, Hirschgeweihfarn; Staghorn Fern, Common Staghorn Fern, Elkhorn Fern | `species.common_names` |
| Familie | Polypodiaceae | `species.family` → `botanical_families.name` |
| Gattung | Platycerium | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Typische Lebensdauer (Jahre) | 20–50+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage (vernalization min days) | — (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN — keine belegte Wuchs-GDD-Basis für Platycerium in der Literatur; tropischer Epiphyt, Wuchs-Phänologie nicht GDD-modelliert --> | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN — tagneutral (day_neutral), kein echter Kurz-/Langtagblüher; keine kritische Photoperiode --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart — Mindesttemperatur 5°C, optimal 16–24°C. Kurze Fröste bis -2°C werden nur ausnahmsweise toleriert; dauerhaft frostfreie Haltung erforderlich. | `species.hardiness_detail` |
| Heimat | Australien, Südostasien — epiphytisch auf Bäumen in tropischen/subtropischen Wäldern | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Geweihfarn ist ein Epiphyt (Aufsitzerpflanze) — er wächst natürlich auf Baumrinde, nicht in Erde. Zwei Blatttypen: Schildwedel (braun, schildförmig — wichtige Schutzstruktur, NIEMALS entfernen!) und Sporentragende Wedel (grün, geweihförmig). Am besten als Wandmontage auf Holz/Kork. In Töpfen entwickelt er schnell Wurzelfäule. Kann über 50 Jahre mit guter Pflege leben.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Photosynthese-Typ:** Platycerium bifurcatum betreibt fakultativen, schwachen CAM (crassulacean acid metabolism). Belegt sind diurnale Malat-Oszillationen ausschließlich in den **Schildwedeln** (cover leaves) unter Trockenstress und Starklicht; die grünen, sporentragenden Wedel (sporotrophophyll) arbeiten primär im **C3**-Modus. Das KA-Feld `species.photosynthesis_type` ist auf `cam` gesetzt, weil die wassersparende CAM-Komponente das pflegerelevante Verhalten (geringe VPD-Sensitivität, Trockenstresstoleranz, seltenes Gießen) prägt. Quellen: Rut et al. 2008 (Photosynthetica); Wai et al. 2023 (Plant Communications, „weak CAM"). <!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farn — keine Blüten, Sporenproduktion ganzjährig möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, spore | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) an der Pflanzenbasis bei 5–8 cm Größe vorsichtig mit Spatel abtrennen und auf ein neues Holzbrett montieren. Sporenvermehrung sehr langwierig (6–12 Monate bis zur erkennbaren Pflanze).

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

**Hinweis:** Kein Rückschnitt. Niemals die braunen Schildwedel entfernen — sie sind lebenswichtig für die Pflanze (Wasser- und Nährstoffspeicher, Wurzelschutz). Nur vollständig abgestorbene grüne Wedel entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited (Wandmontage stark bevorzugt) | `species.container_suitable` |
| Empf. Topfvolumen (L) | — (Montage auf 30×30 cm Holzbrett empfohlen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–90 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Wandmontage oder Hängekorb) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Epiphytisches Substrat: Sphagnum-Moos, Baumfarn-Chips, Kokoshäcksel. Niemals normale Erde. Bei Wandmontage: Sphagnum-Moos zwischen Pflanze und Brett. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 2–8 (flaches, dichtes Haftwurzelpolster auf Montagefläche) | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN — keine Maas-Hoffman-Daten (a) für Platycerium publiziert; Epiphyt, salzempfindlich --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN — kein Maas-Hoffman-b-Wert publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis 1.7:** Der Lichtkompensationspunkt ist für *Platycerium bifurcatum* nicht direkt publiziert; der angegebene Bereich (10–25 µmol/m²/s) ist aus dem Kompensationspunkt stark schattenadaptierter Epiphyten-/Farn-Niche abgeleitet (schattenadaptierte Farne liegen typisch < 50 µmol/m²/s, sehr schattenadaptierte filmy ferns ≤ 51 µmol/m²/s für PPFD bei 95 % Sättigung; reiner LCP deutlich darunter). Lichtsättigung liegt deutlich höher (Photosynthese-Messungen bei 100 µmol/m²/s, Photoinhibition/Starklichtstress ab ≈ 800 µmol/m²/s) — diese Sättigungs-/Inhibitionswerte gehören NICHT ins LCP-Feld. Salztoleranz: Epiphyt mit sehr geringer Salzpufferung, empfindlich gegenüber Salzanreicherung im Substrat; daher Dünger stets halbkonzentriert und Montagefläche regelmäßig mit salzarmem Wasser durchspülen. Boden-pH-Vorzug quellentreu auf 6.0–7.0 gesetzt (slightly acidic to neutral) und mit §2.3 (pH 6.0–7.0) harmonisiert; einzelne Quellen nennen auch 5.5–6.5 (leicht sauer bevorzugt).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–14 (Tauchbad 20 min) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 (Tauchbad) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 4–9 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 13–20 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | low | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 (Tauchbad) | `requirement_profiles.irrigation_frequency_days` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum | 2:1:2 | 0.3–0.6 | 6.0–7.0 | 40 | 15 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe:** Für *Platycerium bifurcatum* sind keine artspezifischen Mikronährstoff-Zielkonzentrationen (Mn/Zn/Cu/Mo) aus seriösen Quellen belegt — der Geweihfarn ist ein Schwachzehrer (light feeder) und wird in der Praxis mit stark verdünntem Volldünger (½ Konzentration) versorgt, der Spurenelemente bereits ausgewogen enthält. Daher bewusst als DATEN FEHLEN markiert statt artfremde Hydroponik-Standardwerte zu übernehmen. In der Winterruhe keine Düngung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L im Tauchwasser (monatlich) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Bananenblätter/Banane | Eigenherstellung | organisch | 1 reife Banane hinter Schildwedel legen | Frühjahr |
| Wurmhumus-Tee | Eigenherstellung | organisch | Im Tauchwasser verdünnt | Wachstum |

### 3.2 Besondere Hinweise

Monatliche Düngung im Wachstum, keine Düngung im Winter. Banane oder organische Materie hinter den Schildwedeln legen (natürliche Ernährungsweise). Niemals Dünger direkt auf die Wedel sprühen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | soak (Tauchbad 20 Minuten) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Raumtemperatur-Wasser; nach dem Tauchen gut abtropfen lassen — nie Wasser im Schildwedel stehenlassen (Fäulnis) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (nur wenn Pflanze Brett überwächst) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost / wenn Nachttemp. < 10 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier-Temperatur (°C) | 13–18 (Minimum 10, nie unter 5) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier-Licht | hell, indirekt (bright indirect) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier-Gießen | stark reduziert — nur alle 2–3 Wochen kurzes Tauchbad; Substrat zwischen den Gaben antrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis 4.3:** *Platycerium bifurcatum* ist nicht frosthart und überwintert in Mitteleuropa (USDA 6–8) zwingend frostfrei im Haus (`frost_free`) — KEINE Ausgraben/Einlagern-Strategie (`dig_and_store`), da Epiphyt ohne Knolle/Rhizomspeicher. Diese Art ist zwar die kältetoleranteste Platycerium-Art (kurzzeitig bis ≈ -1 °C), doch dauerhaft frostfreie Haltung ist Pflicht; Schäden ab Dauer­temperaturen unter 5 °C, irreversible Schäden unter ≈ 4 °C. Brauner Schildwedel-Wechsel und leichtes Wedelabwerfen im Winter sind normale Ruhe-Erscheinungen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken zwischen Wedeln | medium |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Wedeln | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Schwarzfäule | fungal | Schwarze, weiche Stellen auf Schildwedeln | Staunässe nach Tauchen |
| Rhizoctonia-Fäule | fungal | Braune Flecken an Wedelbasis | Dauernasse Montagefläche |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (auf grüne Wedel) | 0 Tage | Schmierläuse, Schildlaus |
| Gut abtrocknen lassen | cultural | Nach Tauchbad vollständig trocknen | 0 | Fäule (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|--------------------|----------------|-----------------|------------------|
| Australischer Marienkäfer (Mealybug destroyer) | *Cryptolaemus montrouzieri* | Schmierläuse (*Pseudococcus* spp., Pseudococcidae) | 2–5 Käfer/m² | mehrere Wochen bis Monate (Generationszyklus ≈ 31 Tage bei 27 °C) |
| Schlupfwespe (soft-scale parasitoid) | *Metaphycus helvolus* | Weichschildläuse (*Coccus hesperidum*, Coccidae) | 5–10 je Befallsherd, ≈ 5–10/m², 2–3 Freilassungen im 2–3-Wochen-Takt | 2–6 Wochen (mehrere Freilassungen nötig) |

**Hinweis 5.4:** Nützling-Wirt-Zuordnung fachlich getrennt: *Cryptolaemus montrouzieri* gegen Schmierläuse (Wollläuse), *Metaphycus helvolus* gegen Weichschildläuse (*Coccus hesperidum*, Coccidae) — NICHT gegen Panzer-/Deckelschildläuse (dafür wären *Aphytis*-Arten zuständig). Einsatz bevorzugt im warmen Innenraum/Gewächshaus (> 20 °C). Bei Braunen Weichschildläusen im Interiorscape kann *M. helvolus* durch Einkapselung der Wespenlarve geschwächt sein; mehrfache Freilassungen einplanen. Vorsicht beim Ausbringen direkt auf die empfindlichen Schildwedel.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze (epiphytisch, Wandmontage).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Großer Geweihfarn | Platycerium superbum | Gleiche Gattung | Spektakulärer, bis 1,5 m Wedelbreite |
| Nestfarn | Asplenium nidus | Einfache Zimmerpflanze | Robuster, Topfhaltung möglich |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Platycerium bifurcatum,"Geweihfarn;Hirschgeweihfarn;Staghorn Fern;Elkhorn Fern",Polypodiaceae,Platycerium,perennial,day_neutral,herb,aerial,"10a;10b;11a;11b","Australien, Südostasien (epiphytisch)",limited,,, 30-90,30-90,yes,limited,true,light_feeder
```

---

## Quellenverzeichnis

1. [Old Farmer's Almanac — Staghorn Fern](https://www.almanac.com/plant/staghorn-fern-care-growing-platycerium-bifurcatum) — Pflegehinweise
2. [Gardenia.net — Platycerium bifurcatum](https://www.gardenia.net/plant/platycerium-bifurcatum-staghorn-fern) — Botanische Daten
3. [NC State Extension — Platycerium bifurcatum](https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/) — USDA-Zonen, Botanik
4. [Guide to Houseplants — Staghorn Fern](https://www.guide-to-houseplants.com/staghorn-fern.html) — Kulturdaten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Rut et al. 2008, Photosynthetica — Crassulacean acid metabolism in the epiphytic fern Platycerium bifurcatum](https://link.springer.com/article/10.1007/s11099-008-0026-8) — Beleg CAM (Malat-Oszillation in Schildwedeln, C3 in Sporotrophophyll); Gaswechsel bei PFD 100 µmol/m²/s
7. [Wai et al. 2023, Plant Communications — Diel dynamics of multi-omics in elkhorn fern provide new insights into weak CAM photosynthesis](https://www.sciencedirect.com/science/article/pii/S2590346223001050) — Zweite unabhängige Bestätigung „weak CAM"
8. [Water-Deficit Stress in the Epiphytic Elkhorn Fern: Insight into Photosynthetic Response (PMC10418323)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10418323/) — Photosynthese unter Trockenstress, Starklicht ≈ 800 µmol/m²/s, R:FR-Effekt (Schatten → größere Wedel)
9. [Light and desiccation responses of Hymenophyllaceae (PubMed 22334496) / Photosynthetic light responses of fern species](https://pubmed.ncbi.nlm.nih.gov/22334496/) — Referenz Lichtkompensationspunkt schattenadaptierter Farne (< 50 µmol/m²/s)
10. [Healthy Houseplants — Staghorn Fern Care](https://www.healthyhouseplants.com/indoor-houseplants/staghorn-fern-platycerium-bifurcatum-care-growth-and-more/) — Temperatur-Optimum (15–27 °C), Mindesttemperatur, pH
11. [Gardening Know How — Overwintering Staghorn Ferns / Cold Hardiness](https://www.gardeningknowhow.com/ornamental/foliage/staghorn-fern/overwintering-staghorn-fern.htm) — Überwinterung, Kältetoleranz (bifurcatum bis ≈ -1 °C), Wintergießen
12. [Wisconsin Horticulture Extension — Staghorn Fern, Platycerium bifurcatum](https://hort.extension.wisc.edu/articles/staghorn-fern-platycerium-bifurcatum/) — Lichtbedarf, Halbschatten, Kultur
13. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Ausbringrate 2–5/m² (Innenraum/Gewächshaus), Entwicklungszyklus
14. [University of Hertfordshire AERU / Wikipedia — Metaphycus helvolus](https://sitem.herts.ac.uk/aeru/bpdb/Reports/2258.htm) — Ausbringrate 5–10/m², Zielwirt Coccus hesperidum (Weichschildlaus)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
