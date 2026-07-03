# Chinesische Fächerpalme — Livistona chinensis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Guide to Houseplants](https://www.guide-to-houseplants.com/chinese-fan-palm.html), [Tropical Plants of Florida](https://tropicalplantsofflorida.com/chinese-fan-palm-care-guide/), [Bouqs Blog](https://bouqs.com/blog/chinese-fan-palm-care/), [Gardenia.net](https://www.gardenia.net/plant/livistona-chinensis), [IFAS UF](https://hort.ifas.ufl.edu/database/documents/pdf/tree_fact_sheets/livchia.pdf)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Livistona chinensis | `species.scientific_name` |
| Volksnamen (DE/EN) | Chinesische Fächerpalme, Fächerpalme; Chinese Fan Palm, Fountain Palm | `species.common_names` |
| Familie | Arecaceae | `species.family` → `botanical_families.name` |
| Gattung | Livistona | `species.genus` |
| Ordnung | Arecales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Wuchsphase (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Livistona chinensis auffindbar; nur subjektive Kältegrenzen --> | `species.base_temp` |
| Lebensdauer (Jahre) | 50–150 | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation/Chilling erforderlich | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — (tropisch/subtropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral; kein Kurz-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kurzfristig bis -5°C; junge Pflanzen frostempfindlicher; als Zimmerpalme ganzjährig frostfrei halten | `species.hardiness_detail` |
| Heimat | China, Japan, Taiwan, Vietnam (subtropische bis tropische Regionen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant (Zimmerpalme) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 6, 7 (nur bei ausgewachsenen Freilandexemplaren; Zimmerpalmen blühen selten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Aussaat aus Samen:** Frische Samen in lauwarmem Wasser 24–48 Stunden einweichen. In Anzuchterde bei konstant 25–28°C aussäen. Keimung nach 1–3 Monaten. Sehr langsames Wachstum: 1–2 Blätter pro Jahr in den ersten Jahren.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine; Blattrippen haben scharfe Zähne (mechanische Verletzungsgefahr) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Nur vollständig abgestorbene, braune Wedel entfernen. Grüne oder teilgrüne Wedel NICHT entfernen — sie sind noch aktiv und entziehen ihrer Abspaltung Nährstoffe, die beim Sterben in die Pflanze zurückfließen. Das Entfernen noch lebender Wedel stresst die Palme dauerhaft.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–300 (Zimmer); bis 1500 cm Freiland | `species.mature_height_cm` |
| Wuchsbreite (cm) | 100–250 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 300–500 | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Torfbasierte Anzuchterde 2:1 mit grobem Sand/Perlit; pH 6.0–7.0; gute Drainage; schwerer Topf für Stabilität | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifischer LCP-Messwert für Livistona chinensis in seriösen Quellen; nur generische Palmen-Schattentoleranz belegt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: siehe min --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: kein belegter Messwert zur Durchwurzelungstiefe von Livistona chinensis --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: nur qualitative Angabe "moderately tolerant of salt spray", kein Maas-Hoffman-Schwellenwert belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis (Licht):** Livistona chinensis wächst laut RHS in voller Sonne und im Halbschatten; Jungpflanzen sind lichtempfindlicher und sollten partiell beschattet werden, ältere Exemplare vertragen mehr Sonne. Als Palme der schattigen Unterschicht tropischer Wälder ist sie gut schattenadaptiert, die Kultur als Zimmerpalme erfolgt aber idealerweise in hellem, indirektem Licht (RHS: "Full sun, Partial shade").

**Hinweis (Salz/Wasser):** Bezugsgröße der Salztoleranz ist Sprühnebel-/Substratsalzbelastung (salt spray); Gardenia/IFAS stufen die Art als "moderately tolerant of salt spray" ein. Staunässe wird schlecht vertragen — schlecht drainierte, vernässte Böden führen zu Wurzelverlust und Wurzelfäule (Phytophthora). Der pH-Vorzug ist quellentreu auf den mit §1.6 und §2.3 harmonisierten Korridor 6.0–7.0 gesetzt; RHS bestätigt zusätzlich eine Toleranz gegenüber leicht alkalischen Böden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 30–90 | 1 | false | false | low |
| Jungpalme | 730–1460 | 2 | false | false | low |
| Vegetativ (etabliert) | fortlaufend | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (etablierte Pflanze)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.50–0.60 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (obere Erdschicht 2–3 cm abtrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–2000 (je nach Topfgröße) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Jungpalme | 1:1:1 | 0.5–0.8 | 6.0–7.0 | 60 | 30 | 0.5 | 0.1 | 0.05 | 0.03 |
| Vegetativ | 3:1:3 | 0.6–1.2 | 6.0–7.0 | 100 | 50 | 0.5 | 0.1 | 0.05 | 0.05 |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe):** Palmen sind besonders Mangan- und Magnesium-empfindlich; ein Mn/Mg-haltiger Palmen-Spezialdünger beugt der bei Palmen häufigen Manganmangel-Aufhellung (gelbliche Jungblätter mit grünen Adern) vor. Die Mikronährstoff-Konzentrationen entsprechen Standardwerten für eine schwach zehrende (light feeder) Topfkultur-Nährlösung (Mn/Zn/Cu/Mo in Sulfat- oder Chelatform); IFAS empfiehlt für Containerpalmen einen 3N-1P₂O₅-2K₂O-Volldünger mit Mg und Mikronährstoffen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Palmendünger | Compo | Spezialdünger | 7-3-6 + Mg | 4 ml/L, alle 14d | Vegetativ |
| Langzeit-Palmen-Düngerstäbchen | Substral | slow release | 11-9-14 | 2 Stäbchen/2 Monate | Vegetativ |
| Palmen NPK Granulat | Scotts | Granulat | 6-3-9 | 30 g/Topf/3 Monate | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | diverse | organisch | 50 g/Topf/Saison | Frühjahr |
| Kompost (beim Umtopfen) | eigen | organisch | 20% Beimischung | Frühjahr |

### 3.2 Besondere Hinweise zur Düngung

Palmen sind Langsamwachser mit vergleichsweise geringem Nährstoffbedarf. Manganmangel ist bei Palmen häufig (gelbliche Jungblätter mit grünen Adern) — Palmen-Spezialdünger mit Mn verwenden. Überdüngung führt zu Blattrandverbrennung (Salzschäden).

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies oder gefiltertes Wasser bevorzugt; regelmäßiges Absprühen der Wedel gegen Staubablagerungen und Milben | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Wenig Wasser | Gießen stark reduzieren; kein Dünger | niedrig |
| Mär | Umtopfen (alle 2–3 J.) | Wurzeln prüfen; ggf. eine Topfgröße größer | mittel |
| Apr | Düngesaison beginnen | Ersten Dünger des Jahres; langsam steigern | mittel |
| Mai–Sep | Aktive Wachstumsphase | Alle 14 Tage düngen; Absprühen; Balkon möglich | hoch |
| Okt | Einholen (Balkon) | Vor dem ersten Frost wieder ins Warme | hoch |
| Nov–Jan | Winterruhe | Kühl, hell, wenig Wasser; kein Dünger | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` | <!-- Quelle: Steckbrief-Erweiterung 2026-06 — Korrektur: frostempfindliche Kübel-/Zimmerpalme, die frostfrei (move_indoors) drinnen überwintert → Enum frost_free statt der UI-nahen needs_protection-Ampelstufe; RHS-Hardiness H2 (1–5 °C, übersteht kein Einfrieren) -->
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Rote Spinne | Tetranychus urticae | Feine Gespinste, gelbliche Punkte auf Wedeln | leaf | medium |
| Schildläuse | Coccoidea | Braune Schuppen, Honigtau | leaf, stem | medium |
| Wollläuse | Planococcus citri | Weiße Wollmasse | stem, leaf | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Blattspitzendürre | physiologisch | Braune Blattspitzen | Zu trockene Luft, Wassermangel, Salze |
| Wurzelfäule | fungal (Phytophthora) | Welke trotz Feuchtigkeit | Staunässe |
| Palmblattflecken | fungal | Braune Flecken | Feuchtigkeit + geringe Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5%, alle 7d | 3 | Spinnmilben, Schildläuse |
| Regelmäßiges Absprühen | cultural | — | Wedel mit Wasser abbrausen | 0 | Milben-Prävention |
| Isopropanol | biological | Isopropylalkohol | Wattestäbchen | 0 | Schildläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|-----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilben (Tetranychus urticae) | 2–6 Tiere/m² (ab 20 °C) | 2–3 Wochen |
| Australische Marienkäfer | Cryptolaemus montrouzieri | Wollläuse (Planococcus citri) | 2–5 Käfer/m² | 3–4 Wochen |
| Schlupfwespe | Metaphycus helvolus | Weichschildläuse (Coccoidea/Coccidae) | 5–10 Tiere/m² | 3–6 Wochen |

**Hinweis:** Phytoseiulus persimilis benötigt höhere Luftfeuchte (> 60 %) und Temperaturen über 20 °C, was zur tropischen Kultur der Fächerpalme passt. Cryptolaemus montrouzieri ist gegen Woll- und Schmierläuse die erste Wahl. Metaphycus helvolus parasitiert Weichschildläuse (Coccidae); gegen Panzer-/Deckelschildläuse (Diaspididae) wären stattdessen Aphytis-Arten zu wählen — die Wirt-Zuordnung darf nicht vermischt werden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Chamaedorea | Chamaedorea elegans | 0.8 | Gleiche Familie, ähnliche Anforderungen | `compatible_with` |
| Howea | Howea forsteriana | 0.8 | Gleiche Familie, ähnliche Pflege | `compatible_with` |
| Dypsis | Dypsis lutescens | 0.7 | Gleiche Familie, komplementäre Ästhetik | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Bergpalme | Chamaedorea elegans | Kleiner, genügsamer | Ideal für dunkle Ecken, sehr robust |
| Kentia-Palme | Howea forsteriana | Elegantere Erscheinung | Sehr robust, verträgt Schattenplätze |
| Areca-Palme | Dypsis lutescens | Fiederpalme, gleiche Familie | Schnellwüchsiger, buschiger |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Livistona chinensis,Chinesische Fächerpalme;Fächerpalme;Chinese Fan Palm,Arecaceae,Livistona,perennial,day_neutral,tree,fibrous,9a;9b;10a;10b;11a;11b,0.0,"China, Japan, Taiwan",yes,20,30,300,250,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [Guide to Houseplants — Chinese Fan Palm](https://www.guide-to-houseplants.com/chinese-fan-palm.html) — Pflegehinweise Indoor
2. [Tropical Plants of Florida — Chinese Fan Palm](https://tropicalplantsofflorida.com/chinese-fan-palm-care-guide/) — Substrat, Dünger
3. [Bouqs Blog — Chinese Fan Palm Care](https://bouqs.com/blog/chinese-fan-palm-care/) — Temperatur, Gießen
4. [Gardenia.net — Livistona chinensis](https://www.gardenia.net/plant/livistona-chinensis) — Botanische Einordnung
5. [UF/IFAS Fact Sheet — Livistona chinensis](https://hort.ifas.ufl.edu/database/documents/pdf/tree_fact_sheets/livchia.pdf) — Wissenschaftliche Daten
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Livistona chinensis (Chinese fan palm)](https://www.rhs.org.uk/plants/10385/livistona-chinensis-chinese-fan-palm-chinese-fountain-palm/details) — Boden-pH (acid/neutral/alkaline), Exposition (full sun/partial shade), Feuchte (moist but well-drained), Winterhärte H2 (1–5 °C)
7. [UF/IFAS ENH-524/ST365 — Livistona chinensis](https://ask.ifas.ufl.edu/publication/ST365) — Lichtexposition ("light shade or full sunlight"), Salztoleranz ("moderately tolerant of salt spray"), Trockentoleranz
8. [ProjectPalm — Livistona chinensis](https://projectpalm.net/species/livistona-chinensis) — Boden-pH-Spanne (leicht sauer bis neutral, Toleranz 5.0–8.0), Sonnenbedarf, Trockentoleranz
9. [Marler & Cruz — Convergent Evolution towards High Net Carbon Gain Efficiency / Shade Tolerance of Palms (Arecaceae), PMC4604201](https://pmc.ncbi.nlm.nih.gov/articles/PMC4604201/) — C3-Stoffwechsel und Schattenadaptation der Arecaceae (Understory)
10. [UF/IFAS ENH1010/EP262 — Nutrition and Fertilization of Palms in Containers](https://ask.ifas.ufl.edu/publication/EP262) — 3N-1P₂O₅-2K₂O-Volldünger mit Mg + Mikronährstoffen (Mn/Zn/Cu/Fe in Sulfat-/Chelatform) für Containerpalmen
11. [Grossiord et al. — Plant responses to rising vapour pressure deficit, New Phytologist 2020](https://nph.onlinelibrary.wiley.com/doi/10.1111/nph.16485) — VPD-Stomata-Sensitivität tropischer (isohydrischer) Arten als Grundlage der VPD-Einstufung
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
