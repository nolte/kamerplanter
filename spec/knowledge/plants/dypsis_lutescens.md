# Areka-Palme, Goldfruchtpalme — Dypsis lutescens

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Our Houseplants](https://www.ourhouseplants.com/plants/areca-palm), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/areca-palm-care-guide-growing-dypsis-lutescens-indoors/), [Gardenia.net](https://www.gardenia.net/plant/dypsis-lutescens-areca-palm), [ASPCA](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/areca-palm)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dypsis lutescens | `species.scientific_name` |
| Synonyme | Chrysalidocarpus lutescens (älterer, noch gebräuchlicher Handelsname) | — |
| Volksnamen (DE/EN) | Areka-Palme, Goldfruchtpalme, Schmetterlingspalme; Areca Palm, Butterfly Palm, Golden Cane Palm | `species.common_names` |
| Familie | Arecaceae | `species.family` → `botanical_families.name` |
| Gattung | Dypsis | `species.genus` |
| Ordnung | Arecales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für D. lutescens; nur generische C3-Tropenpalmen-Spannen verfügbar, kein Keimwert als Wuchsbasis umetikettieren --> | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | — (tagneutrale Art, kein Kurz-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` |
| Vernalisation Mindest-Tage | — (tropische Art ohne Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 16–24°C. Kälte unter 10°C führt zu Verfärbung. | `species.hardiness_detail` |
| Heimat | Madagaskar — tropische/subtropische Wälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, air_purifying | `species.traits` |

**Hinweis:** Die Areka-Palme ist laut NASA Clean Air Study (1989) eine der besten Luftreinigungspflanzen für Innenräume und transpiriert große Mengen Wasser (natürlicher Luftbefeuchter). Sie ist wie viele Palmen empfindlich gegenüber Fluorid und Salzen im Gießwasser — braune Blattspitzen entstehen fast immer durch Fluoridschäden. Der Handelsname Chrysalidocarpus lutescens ist botanisch veraltet, aber in Gärtnereien noch häufig zu finden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nicht zuverlässig in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung von Büscheln beim Umtopfen möglich, aber Pflanzen etablieren sich langsam. Samen bei 27°C, Keimung in 4–6 Wochen. Kommerziell werden mehrere Triebe pro Topf gesetzt für dichteres Erscheinungsbild.

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

**Hinweis:** ASPCA listet Dypsis lutescens als vollständig ungiftig für Katzen und Hunde.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Nur vollständig abgestorbene, braune Wedel an der Basis entfernen. Niemals teilweise grüne Wedel kürzen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–250 (indoor) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–200 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gute Palmenerde oder Einheitserde mit 20% Perlite. pH 6.0–7.0. Gute Drainage. Leicht feuchtigkeitshaltend. Niemals staunass. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP-Messwert für D. lutescens publiziert --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP-Messwert für D. lutescens publiziert --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–60 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | moderate | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN: nur qualitative "moderate" Einstufung (UF/IFAS), kein Maas-Hoffman a-Wert publiziert --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman b-Wert publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** D. lutescens ist eine schattenadaptierte Unterwuchspalme (understory palm); Palmen erreichen Schattentoleranz über konsistent niedrige Dunkelatmung (dark respiration) und damit einen niedrigen Lichtkompensationspunkt (light compensation point), publizierte artspezifische LCP-Zahlen fehlen jedoch (Ng et al. 2015, PLOS ONE; Sterck et al. 2013 nennen für tropische Schattenpflanzen generell 10–50 µmol/m²/s, nicht artspezifisch). UF/IFAS klassifiziert den Standort als "full sun, partial sun, partial shade; shade tolerant"; als dokumentierter Vorzugswert für die Kübel-/Innenkultur wird `partial_shade` gesetzt. Die Salztoleranz ist nach UF/IFAS "moderate" (→ `moderately_tolerant`); die ECe-Schwelle bezieht sich auf die Substrat-Bodenlösung (saturated paste extract), NICHT auf die Gießwasser-EC. Der pH-Vorzug 6.0–7.0 ist mit §1.6 und §2.3 derselben Datei harmonisiert; bei pH > 6.5 treten in alkalischen Böden Mn/Fe-Chlorosen auf.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–24 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.55 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.55 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 | 0.5 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.3 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Die Mn/Zn/Cu/Mo-Werte sind Nährlösungs-Zielkonzentrationen (solution targets, mg/L) für die aktive Wachstumsphase, abgeleitet aus den üblichen Mikronährstoff-Korridoren für Zier-/Blattpflanzen (Mn 0.5–1, Zn 0.05–0.5, Cu 0.05–0.5, Mo 0.02–0.05 mg/L). Sie sind NICHT mit den Blatt-Gewebewerten (leaf tissue) zu verwechseln, die UF/IFAS für gesunde Areka-Palmen angibt (Mn 50–300 ppm, Zn 25–200 ppm, Cu 10–60 ppm Trockenmasse). Für Molybdän existiert kein artspezifischer Blattgewebe-Richtwert; der Lösungswert folgt dem generischen Blattpflanzen-Korridor. Palmen reagieren bei Substrat-pH > 6.5 empfindlich mit Mn-Mangel ("frizzletop"), da Mn dann ausfällt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Palmen-Dünger | Compo | base | 7-3-7 | 5 ml/L (alle 2–3 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | – | organisch | 30 g/Topf | Frühjahr |
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 2–3 Wochen März bis September. Im Winter kein Dünger. Fluoridarmes Wasser verwenden (destilliert oder gefiltertes Leitungswasser) — Fluorid ist häufigste Ursache für braune Blattspitzen. Hinweis: Leitungswasser über Nacht stehen lassen entfernt Chlor, aber nicht Fluorid.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Destilliertes oder gefiltertes Wasser dringend empfohlen — Fluorid im Leitungswasser verursacht braune Blattspitzen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Aktion (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Aktion Monat | 10 (Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Aktion (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Aktion Monat | 5 (Mai, nach Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier-Temperatur (°C) | 15–22 (nie unter 10) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier-Licht | hell, indirektes Licht; ggf. Pflanzenlampe | `overwintering_profiles.winter_quarter_light` |
| Winterquartier-Gießen | sparsam, oberste Substratschicht abtrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** D. lutescens ist nicht frosthart (`tender`) und wird als frostfrei überwinternde Kübel-/Zimmerpflanze geführt (→ `frost_free`, KEINE Knolle zum Ausgraben). Bereits Temperaturen unter 10 °C verursachen Kälteschäden und Verfärbung; leichter Frost kann die Pflanze töten. Sommerfrische auf Balkon/Terrasse ist möglich, dann vor dem ersten Herbstfrost (Oktober) ins frostfreie, helle Winterquartier holen und im Frühjahr nach den Eisheiligen (Mitte Mai) langsam wieder abhärten (harden off).
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
| Fluoridschaden | physiologisch | Braune Blattspitzen | Fluorid im Gießwasser |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |
| Gefiltertes Wasser | cultural | Wasserquelle wechseln | 0 | Fluoridschaden (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|----------------|--------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Gemeine Spinnmilbe (Tetranychus urticae) | 5–10 Tiere/m² (Befallsherd höher) | 2–3 Wochen bei 15–25 °C |
| Cryptolaemus montrouzieri (Australischer Marienkäfer) | Schmierläuse (Pseudococcus spp.) | 2–5 Käfer/m² | 4–6 Wochen |
| Metaphycus helvolus (Schlupfwespe) | Weichschildlaus / Braune Koffeeschildlaus (Coccus hesperidum) | 5 Tiere/m², 3 Freilassungen im 14-Tage-Abstand | 4–6 Wochen |

**Hinweis:** Nützlingseinsatz nur ohne vorausgegangene Breitband-Insektizide. Phytoseiulus benötigt hohe Luftfeuchte (60–95 %) und Temperaturen über 15 °C — passt gut zur tropischen Areka-Kultur. Cryptolaemus ist ein spezialisierter Schmierlaus-Prädator (Larve und Käfer fressen Eier/Larven); zu hohe Ausbringmengen führen zu Kannibalismus. Metaphycus helvolus parasitiert junge 2. Larvenstadien der Weichschildlaus und tötet zusätzlich durch Host-Feeding.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kentia-Palme | Howea forsteriana | Arecaceae, elegante Palme | Toleriert weniger Licht, robuster |
| Stubenpalme | Chamaedorea elegans | Arecaceae, kompakte Palme | Deutlich kleiner |
| Kentiapalme | Rhapis excelsa | Arecaceae, Fächerpalme | Sehr schattentoleriert |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Dypsis lutescens,"Areka-Palme;Goldfruchtpalme;Schmetterlingspalme;Areca Palm;Butterfly Palm",Arecaceae,Dypsis,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Madagaskar",yes,10-30,30,150-250,100-200,yes,limited,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Our Houseplants — Areca Palm](https://www.ourhouseplants.com/plants/areca-palm) — Detaillierte Kulturdaten
2. [Healthy Houseplants — Dypsis lutescens](https://www.healthyhouseplants.com/indoor-houseplants/areca-palm-care-guide-growing-dypsis-lutescens-indoors/) — Pflegehinweise, Fluorid
3. [Gardenia.net — Dypsis lutescens](https://www.gardenia.net/plant/dypsis-lutescens-areca-palm) — Botanische Daten
4. [ASPCA — Areca Palm](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/areca-palm) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [UF/IFAS ENH324/ST165 — Dypsis lutescens: Yellow Butterfly Palm](https://ask.ifas.ufl.edu/publication/ST165) — Lichtansprüche (full sun bis shade tolerant), Salztoleranz (moderate), pH-Vorzug, Wuchsgröße, "occasionally wet"
6. [UF/IFAS FOR247/FR309 — Dypsis lutescens, Areca Palm](https://ask.ifas.ufl.edu/publication/FR309) — Standort, Drainage, Bodenansprüche, Mn/Fe-Chlorose bei hohem pH
7. [UF/IFAS — Areca Palm Production Guide (MREC Foliage Notes)](https://mrec.ifas.ufl.edu/Foliage/folnotes/areca.htm) — Blatt-Gewebewerte Mn 50–300, Zn 25–200, Cu 10–60 ppm; Nährstoffmanagement
8. [Ng J. et al. 2015, PLOS ONE — Convergent Evolution towards High Net Carbon Gain Efficiency Contributes to the Shade Tolerance of Palms (Arecaceae)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4604201/) — Schattenadaption der Palmen über niedrige Dunkelatmung (LCP qualitativ)
9. [Sterck F. et al. 2013, Journal of Ecology — Light compensation point in tropical forest understorey](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — LCP-Spannen tropischer Schattenpflanzen (10–50 µmol/m²/s, nicht artspezifisch)
10. [Kruse J. et al. 2019, New Phytologist — Optimization of photosynthesis in date palm during heat acclimation](https://nph.onlinelibrary.wiley.com/doi/full/10.1111/nph.15923) — Photosynthese-T_opt-Korridor tropischer Palmen
11. [Clemson HGIC — Palm Diseases & Nutritional Problems](https://hgic.clemson.edu/factsheet/palm-diseases-nutritional-problems/) — Mn-Mangel ("frizzletop") ab pH > 6.5, Mikronährstoff-Symptomatik
12. [Koppert — Phytoseiulus persimilis](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate/Etablierung Raubmilbe gegen Spinnmilben
13. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Schmierlaus-Prädator, Ausbringung
14. [Metaphycus helvolus — Biological Controls (Interiorlandscaping)](http://www.interiorlandscaping.co.uk/Biologica.htm) — Ausbringrate 5/m², 3 Freilassungen, Ziel Coccus hesperidum
15. [Healthy Houseplants / Greg — Areca Palm Winter Care](https://greg.app/areca-palm-winter-care/) — Überwinterung, Mindesttemperatur, Wasser-/Lichtbedarf im Winter
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
