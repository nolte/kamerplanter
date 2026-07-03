# Mosaik-Pflanze, Aderblatt — Fittonia albivenis

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/fittonia-albivenis-nerve-plant-grow-and-care-tips), [Smart Garden Guide](https://smartgardenguide.com/nerve-plant-care/), [Soltech](https://soltech.com/products/nerve-plant-care), [Terrarium Tribe](https://terrariumtribe.com/terrarium-plants/fittonia-albivenis-nerve-plant/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Fittonia albivenis | `species.scientific_name` |
| Volksnamen (DE/EN) | Mosaik-Pflanze, Aderblatt, Filigranpflanze; Nerve Plant, Mosaic Plant, Net Plant | `species.common_names` |
| Familie | Acanthaceae | `species.family` → `botanical_families.name` |
| Gattung | Fittonia | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | groundcover | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 3–10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | day_neutral (tagneutral — kein Kurztag-/Langtag-Blühverhalten; keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein publizierter Wuchs-/Phänologie-Basiswert für Fittonia albivenis auffindbar | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (tropische Art ohne Kältebedarf) | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–26°C. Extrem empfindlich gegen Kälte, Zugluft und trockene Luft. | `species.hardiness_detail` |
| Heimat | Peru, Kolumbien, Ecuador — Unterwuchs tropischer Regenwälder, bodennah | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Fittonia ist der Drama-Queen unter den Zimmerpflanzen — sie lässt bei Trockenstress dramatisch die Blätter hängen (komplett kollabieren), erholt sich aber bei sofortiger Wässerung fast vollständig. Dieser "Fainting"-Effekt ist ein zuverlässiger Feuchtigkeits-Anzeiger. Ideal für Terrarien (feuchtes Mikroklima, kein Zugluft-Problem). Im normalen Zimmerklima ist konstante hohe Luftfeuchtigkeit die größte Herausforderung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 7, 8 (kleine, unauffällige gelb-weiße Ährenblüten; werden oft entfernt um Blattenergie zu erhalten; in Zimmerkultur selten blühend) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge (3–5 cm, 2–3 Blattpaare) im Wasser oder direkt in feuchtem Substrat bei hoher Luftfeuchtigkeit. Mit Plastikbeutel oder Glasglocke abdecken. Bewurzelung in 2–4 Wochen. Sehr einfach — Fittonia bewurzelt fast von selbst.

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

**Hinweis:** Fittonia albivenis ist nicht giftig — sicher für Haushalte mit Haustieren und Kindern.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Regelmäßiges Pinzen der Triebspitzen fördert dichten, kompakten Wuchs und verhindert leggy-Wuchs. Blütenstände entfernen (verbraucht Energie). Im Frühjahr auf Basis zurückschneiden bei ausgezehrter Pflanze.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 10–15 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Feuchtigkeitshaltende, gut durchlässige Torfmischung: Einheitserde + 10% Perlite + 10% Torf/Kokoserde. pH 6.0–7.0. Alternativ: Terrarium-Substrat mit hohem organischen Anteil. Klein-Töpfe bevorzugt. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 30 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 8–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN --> kein artspezifischer Maas-Hoffman-Schwellenwert (Substrat-ECe) für Fittonia publiziert; Klasse "sensitive" impliziert grob < 2 dS/m | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein artspezifischer Maas-Hoffman-Slope publiziert | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Fittonia albivenis ist eine schattentolerante Unterwuchspflanze (understory) tropischer Regenwälder. Ein artspezifisch gemessener Lichtkompensationspunkt (light compensation point, Netto-Photosynthese = 0) ist nicht publiziert; der angegebene Bereich 10–30 µmol/m²/s ist aus der Physiologie schattentoleranter Unterwuchsarten abgeleitet (Literaturspanne 10–50 µmol/m²/s, tiefe Schattenpflanzen am unteren Ende). Lichtsättigung und Photoinhibition liegen deutlich oberhalb und sind hier bewusst NICHT eingetragen — Fittonia bleicht/verbrennt bei direkter Sonne. Die Pflanze nutzt im Unterwuchs angereichertes Fernrot-Licht (far-red) effizient (PSI-Emissionsmaximum λmax 753 nm). Effektive Wurzeltiefe abgeleitet aus min. Topftiefe 8 cm und flachem, mattenbildendem Faserwurzelsystem. Staunässe und Salzanreicherung (hartes Leitungswasser, Überdüngung) führen rasch zu Wurzelfäule bzw. braunen Blatträndern. Der pH-Vorzug 6.0–6.5 ist quellentreu; er liegt innerhalb der in §1.6/§2.3 genannten weiteren Spanne 6.0–7.0.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.2–0.6 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 17–23 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 2–5 | `requirement_profiles.dli_target_mol` |
| VPD-Schwelle (kPa) | 0.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5–0.6 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum | 2:1:2 | 0.3–0.6 | 6.0–7.0 | 60 | 20 | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Mikronährstoffe (Mn/Zn/Cu/Mo):** Werte entsprechen der Standard-Hoagland-Referenz (`nutrient_profiles.manganese/zinc/copper/molybdenum_ppm`) und sind für eine leichtzehrende Foliage-Art (light_feeder) plausibel; bei der hier praktizierten Viertel-Dosis (EC 0.3–0.6 mS) liegen die effektiv ausgebrachten Spurenelement-Konzentrationen entsprechend niedriger.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 2 ml/L (Viertel-Dosis, alle 4 Wochen) | Wachstum |
| Orchideen-Dünger | Substral | base | 7-5-6 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Nur mit 1/4 der normalen Düngerkonzentration düngen. Alle 4–6 Wochen März bis August. Überdüngung führt schnell zu Salzschäden (braune Ränder). Oktober bis Februar: kein Dünger.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser. Untersetzer-Methode ideal — Boden nie nass lassen, aber nie vollständig austrocknen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mitte/Ende Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 17–23 (nie unter 15; unter 10 °C tödlich) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (bright indirect); ggf. Pflanzenlampe bei kurzen Tagen | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert, gleichmäßig feucht halten; Staunässe vermeiden | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Fittonia albivenis ist eine nicht frostharte Tropenpflanze und überwintert als Zimmer-/Kübelpflanze ganzjährig frostfrei im Innenraum (hardiness_rating = frost_free). Ein Sommer-Aufenthalt im Freien (Schatten, windgeschützt) ist möglich, muss aber spätestens bei Nachttemperaturen unter ~15 °C beendet werden. Keine Knollen-/Einlagerungsruhe (kein dig_and_store), keine Endo-/Kältedormanz.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben (bei trockener Luft) | medium |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | easy |
| Blattlaus | Aphididae | Kolonien, Honigtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke trotz feuchter Erde | Staunässe, schlechte Drainage |
| Botrytis | fungal | Grauschimmel auf Blättern | Übermäßige Feuchtigkeit, Luftstagnation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Humidifier | cultural | Luftfeuchtigkeit erhöhen | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Blattläuse |
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke (Adulte) |
| Nematoden | biological | Gießen | 0 | Trauermücke (Larven) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate/m² | Etablierungszeit |
|----------|----------------|-----------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 2–50/m² je Befallsdruck, ggf. wöchentlich wiederholen | 1–2 Wochen |
| Aphidius colemani (Schlupfwespe) | Blattlaus (Aphididae) | 0,25–4/m² je Ausbringung, mind. 3× wiederholen | 2–3 Wochen |
| Aphidoletes aphidimyza (Gallmücke) | Blattlaus (Aphididae) | 1–10/m² kurativ bzw. 0,25–0,5/m² präventiv wöchentlich | 2–3 Wochen |
| Steinernema feltiae (Nematode) | Trauermücke (Bradysia spp.), Larven | 250.000–500.000/m² (Bodengießung) | 1–2 Wochen |

**Hinweis:** Nützlinge sind im geschlossenen, feuchtwarmen Mikroklima (Terrarium, Vitrine) gut etablierbar. Phytoseiulus persimilis benötigt hohe Luftfeuchte (> 60 %), die für Fittonia ohnehin gegeben ist. Nützlingseinsatz und Neem-/Spritzbehandlungen (§5.3) sollten zeitlich getrennt werden, da Wirkstoffe die Nützlinge schädigen können.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Weiße Aderblatt | Fittonia albivenis 'White Anne' | Gleiche Art | Weiße Adern, spektakulär |
| Rote Aderblatt | Fittonia albivenis 'Red Threads' | Gleiche Art | Rote Adern, intensiv |
| Maranta | Maranta leuconeura | Ähnliche Ansprüche (Marantaceae) | Größer, robuster |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Fittonia albivenis,"Mosaik-Pflanze;Aderblatt;Nerve Plant;Mosaic Plant",Acanthaceae,Fittonia,perennial,day_neutral,groundcover,fibrous,"11a;11b;12a","Peru, Kolumbien, Ecuador",yes,0.5-2,8,10-15,20-40,yes,no,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
White Anne,Fittonia albivenis,"ornamental;white_veins;compact",clone
Red Threads,Fittonia albivenis,"ornamental;red_veins;compact",clone
Pink Angel,Fittonia albivenis,"ornamental;pink_veins",clone
Skeleton,Fittonia albivenis,"ornamental;white_veins;large_leaf",clone
```

---

## Quellenverzeichnis

1. [Gardenia.net — Fittonia albivenis](https://www.gardenia.net/plant/fittonia-albivenis-nerve-plant-grow-and-care-tips) — Botanische Daten, Kulturdaten
2. [Smart Garden Guide — Nerve Plant](https://smartgardenguide.com/nerve-plant-care/) — Detaillierte Pflegehinweise
3. [Soltech — Nerve Plant Care](https://soltech.com/products/nerve-plant-care) — Lichtanforderungen
4. [Terrarium Tribe — Fittonia albivenis](https://terrariumtribe.com/terrarium-plants/fittonia-albivenis-nerve-plant/) — Terrarium-Kultivierung
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Sayood et al. (2025), PubMed 40793932 — Utilising Far-Red Light: Photosynthetic and Physiological Adaptations in Shade-Tolerant Fittonia albivenis](https://pubmed.ncbi.nlm.nih.gov/40793932/) — Schattentoleranz, Fernrot-Nutzung (far-red), Wachstumslicht 20 µmol/m²/s
7. [Nature Communications (2024) — Structure of the red-shifted Fittonia albivenis photosystem I (PMC11282222)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11282222/) — Unterwuchs-/Far-Red-Adaption, PSI λmax 753 nm, FR-Anreicherung im Kronendach
8. [Sage et al. (2011), J. Exp. Bot. — C4 plant lineages of planet Earth](https://academic.oup.com/jxb/article/62/9/3155/474202) — Acanthaceae als eudikotyle C3-Familie (nur Gattung Blepharis C4); Beleg Photosynthese-Typ c3
9. [Wikipedia — List of C4 plants / Acanthaceae](https://en.wikipedia.org/wiki/List_of_C4_plants) — Acanthaceae nicht CAM, ganz überwiegend C3
10. [Sterck et al. (2013), Journal of Ecology — Light compensation point in tropical forest understorey shrubs](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — LCP-Spanne schattentoleranter Unterwuchsarten (10–50 µmol/m²/s)
11. [Gardening Know How — Nerve Plant Care](https://www.gardeningknowhow.com/houseplants/nerve-plant/growing-nerve-plants.htm) — Staunässe-/Salzempfindlichkeit, Mindesttemperatur, frostfreie Überwinterung
12. [Smart Garden Guide / Between Two Thorns — Nerve Plant Care](https://www.betweentwothorns.com/blogs/news/fittonia-nerve-plant-care-guide) — Boden-pH 6.0–6.5, Salzanreicherung, well-draining, Kälteempfindlichkeit
13. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Mikronährstoff-Referenz Mn 0.5 / Zn 0.05 / Cu 0.02 / Mo 0.01 ppm
14. [Koppert — Biologische Bekämpfung (Phytoseiulus persimilis, Aphidius colemani, Aphidoletes aphidimyza, Steinernema feltiae)](https://www.koppert.com/) — Nützling-Wirt-Zuordnung und Ausbringraten
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: Growing-Phase-Audit 2026-07 -->
15. [NC State Extension Gardener Plant Toolbox — Fittonia albivenis](https://plants.ces.ncsu.edu/plants/fittonia-albivenis/) — Blüte Juli–August, Lebenszyklus "Perennial", Vermehrung "Stem Cutting"
16. [Floragard — Fittonie 'White Star'](https://www.floragard.de/de-de/fittonie-white-star) — Blüte "Von Juli bis August"
17. [Mauk Gartenwelt — Fittonia albivenis (Fittonie)](https://www.mauk-gartenwelt.de/fittonia-albivenis-fittonie) — Blüte "Von Juli bis August", gelbe Blüten, immergrüne Zimmerpflanze
18. [Gardening Know How — Growing Nerve Plants](https://www.gardeningknowhow.com/houseplants/nerve-plant/growing-nerve-plants.htm) — "spreading evergreen perennial", Stecklingsvermehrung
19. [Plantura — Mosaikpflanze Pflanzenportrait](https://www.plantura.garden/zimmerpflanzen/mosaikpflanze/mosaikpflanze-pflanzenportrait) — Vermehrung Stecklinge, Teilung, Aussaat; Blüte in Zimmerkultur selten
20. [Rural Sprout — Fittonia Nerve Plant Care & Propagation](https://www.ruralsprout.com/fittonia-nerve-plant/) — Vermehrung per Teilung (Root Division) und Stecklingen
<!-- /Quelle: Growing-Phase-Audit 2026-07 -->
