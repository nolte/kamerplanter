# Drachenbaum — Dracaena marginata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Epic Gardening](https://www.epicgardening.com/dracaena-marginata-madagascar-dragon-tree/), [Gardenia.net](https://www.gardenia.net/plant/dracaena-marginata-dragon-tree), [Bloomscape](https://bloomscape.com/plant-care-guide/dracaena/), [ASPCA](https://www.aspca.org/), [Ohio Tropics](https://www.ohiotropics.com/2022/04/15/dracaena-marginata-care/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dracaena marginata | `species.scientific_name` |
| Volksnamen (DE/EN) | Madagassischer Drachenbaum, Rotsaum-Drachenbaum; Madagascar Dragon Tree, Red-Edged Dracaena | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Dracaena | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur Wuchs (base temp, °C) | <!-- DATEN FEHLEN --> kein publizierter Wuchs-/Phänologie-GDD-Basiswert für diese tropische Zierart auffindbar (nur Wuchs-Optimum 18–27 °C, Schadschwelle ~13 °C belegt — das ist KEINE GDD-Basis) | `species.base_temp` |
| Kritische Tageslänge (critical day length, h) | Entfällt — day_neutral (tagneutral), keine Photoperioden-induzierte Blüte | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–27°C. Fluoridsensitiv — Leitungswasser mit Fluorid verursacht braune Blattspitzen. | `species.hardiness_detail` |
| Heimat | Madagaskar, Mauritius, La Réunion | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.7 | `species.air_purification_score` |
| Entfernte Schadstoffe | formaldehyde, benzene, trichloroethylene, xylene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Dracaena marginata ist ein Klassiker unter den Büropflanzen — verträgt Vernachlässigung und Schwachlicht. Sehr charakteristischer, baumartiger Wuchs mit büschelartigen Blattrosetten an den Triebspitzen. Bei ausreichend Licht bildet die Pflanze einen markanten, verzweigten Stamm.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor sehr selten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Kopfstecklinge (10–15 cm) mit Blattrosette in Substrat stecken. Alternativ: Stammstücke (5–10 cm) ohne Blätter flach oder aufrecht in feuchtes Substrat — bilden an Knoten neue Triebe. Bewurzelung bei 22–25°C Bodentemperatur in 4–6 Wochen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate (für Katzen — Ätherische Öle verursachen Pupillenerweiterung, Erbrechen) | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Besonderer Hinweis für Katzen:** Dracaena ist für Katzen deutlich gefährlicher als für Hunde oder Menschen. Saponine + Ätherische Öle können bei Katzen zu Erbrechen, Speichelfluss, Muskelschwäche und Pupillenerweiterung führen. Von Katzenhaushalten fernhalten oder ersetzen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kappen des Haupttriebs fördert Verzweigung. Abgestorbene untere Blätter abzupfen — charakteristischer Stamm bildet sich so besser aus.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–300 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Zimmerpflanzenerde mit guter Drainage, 20–30% Perlite. Fluoridarm wenn möglich. pH 6.0–7.0. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | <!-- DATEN FEHLEN --> keine quantifizierte Wurzeltiefe für diese Topf-Zierart publiziert (Wurzelsystem als extensiv/zweistufig beschrieben, aber ohne cm-Angabe); Bezug: Min. Topftiefe 20 cm | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Maas-Hoffman a, Substrat-ECe dS/m) | <!-- DATEN FEHLEN --> keine Maas-Hoffman-Daten für diese Zierart; Salzempfindlichkeit qualitativ vielfach belegt (Fluorid + lösliche Salze → Blattspitzennekrose), aber kein numerischer ECe-Schwellenwert | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (Maas-Hoffman b, %/dS/m) | <!-- DATEN FEHLEN --> kein publizierter Maas-Hoffman-Slope für diese Art | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Dracaena marginata ist eine tropische Unterwuchs-Art (understory) mit dünner Kutikula und auf schwaches Dauerlicht optimierten Chloroplasten — daher der sehr niedrige Lichtkompensationspunkt (10–25 µmol/m²/s, typisch für schattentolerante Unterwuchspflanzen). Der Kompensationspunkt markiert die Netto-Photosynthese = 0; das Pflege-Optimum liegt deutlich höher bei 100–300 µmol/m²/s (vgl. §2.2). Die Einstufung `shade` (nicht `deep_shade`): Die Pflanze überlebt in echtem Schwachlicht, verliert dort aber Panaschierung, lässt Blätter fallen und stockt im Wuchs. Salzempfindlichkeit und Staunässe-Empfindlichkeit sind eng mit der dokumentierten Fluorid-/Salz-Toleranz (§1.4, §3.2) und der Wurzelfäule-Neigung (§5.2) verknüpft.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.3 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.4–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–12 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 20–24 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.4–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 21–28 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.6–1.0 | 6.0–6.5 | 80 | 30 | 0.5 | 0.3 | 0.1 | 0.05 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Mn/Zn/Cu/Mo, ppm):** Werte aus den allgemeinen Foliage-/Hydroponik-Empfehlungsspannen abgeleitet (Mangan/manganese 0.5–2, Zink/zinc 0.5–2, Kupfer/copper 0.1–0.5, Molybdän/molybdenum 0.02–0.05) und für den `light_feeder` Dracaena an die untere Spanne gelegt: `nutrient_profiles.manganese_ppm` 0.5, `nutrient_profiles.zinc_ppm` 0.3, `nutrient_profiles.copper_ppm` 0.1, `nutrient_profiles.molybdenum_ppm` 0.05. Wegen Fluorid-/Salzempfindlichkeit (§3.2) Mikronährstoffe nicht überdosieren.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->


---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne fein | Oscorna | organisch | 2 g/L Substrat | Frühling |

### 3.2 Besondere Hinweise

Fluoridsensitiv: Kein phosphatreicher Dünger (Fluorid als Verunreinigung in Phosphatdüngern). Gefilterte oder abgestandene Wasser bevorzugen. Braunfärbung der Blattspitzen ist oft Fluorid-Toxizität, kein Nährstoffmangel.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10–14 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gefiltertes oder abgestandenes Wasser empfohlen (Fluoridsensitiv). Kein kalkreiches Leitungswasser. Raumtemperatur. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28–35 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9–10 (vor erstem Frost / Nachttemperaturen unter 13 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5–6 (nach den Eisheiligen, langsam abhärten/harden_off) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 13–18 (Minimum 10 °C, niemals unter ~13 °C dauerhaft) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt; Süd-/Ostfenster, ggf. Pflanzenlicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert: obere 50 % des Substrats abtrocknen lassen, Intervall 21–28 Tage, keine Staunässe | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Dracaena marginata ist nicht frosthart (USDA 10–11) und wird in Mitteleuropa (USDA 6–8) als Kübel-/Zimmerpflanze frostfrei (frost_free) drinnen überwintert — KEINE Knolle zum Ausgraben (kein dig_and_store), kein Mulch/Vlies. Ein Sommer-Aufenthalt im Freien (windgeschützt, halbschattig) ist möglich; vor dem ersten Frost bzw. bei Nachttemperaturen unter ~13 °C zurück ins Haus. Im Frühjahr langsam ans Außenlicht gewöhnen (Sonnenbrandgefahr nach Winterstand).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blattvergilbung | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken, Honigtau | easy |
| Schildlaus | Coccus hesperidum | Braune Schalen auf Stängeln | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Fusarium-Stielwelke | fungal | Stängelbasis fault, Pflanze kippt | Überbewässerung |
| Fluoridtoxizität | physiologisch | Braune Blattspitzen, keine Ausbreitung | Fluorid/Chlorid im Wasser |
| Wurzelfäule | fungal | Gelbe Blätter, fauler Geruch | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus, Schmierlaus |
| Fluoridfreies Wasser | cultural | Regenwasser oder Filter | 0 | Fluoridtoxizität (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 5–20 Tiere/m² (leicht 2/m², stark bis 4/sq ft) | 2–3 Wochen; Optimum 20–27 °C, > 60 % rF |
| Australischer Marienkäfer / Mealybug Destroyer | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | 1–10 Tiere/m² (Schwerpunkte am Befall) | 3–4 Wochen; > 18 °C, hohe Luftfeuchte begünstigend |
| Erzwespe (Zehrwespe) | Metaphycus helvolus | Weichschildlaus (Coccus hesperidum, Coccidae) | 2–5 Tiere/m² je Freilassung, wöchentlich wiederholen | 3–6 Wochen; warm (> 20 °C), bei Befallsbeginn ausbringen |

**Hinweis:** Nützling-Wirt-Zuordnung beachten — *Metaphycus helvolus* parasitiert WEICHschildläuse (Coccidae, hier *Coccus hesperidum*), NICHT Panzer-/Deckelschildläuse (Diaspididae). Gegen Ameisen-Symbiose (Honigtau) vorgehen, da Ameisen die Nützlinge stören. Im Zimmer ist die Etablierung wegen geringer Befallsdichte und trockener Luft schwieriger als im Gewächshaus; bei Spinnmilben Luftfeuchte erhöhen, um *Phytoseiulus* zu unterstützen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Bogenhanf | Dracaena trifasciata | Gleiche Gattung | Kompakter, weniger Höhe |
| Dracaena fragrans | Dracaena fragrans | Gleiche Gattung | Breitere Blätter, duftende Blüten |
| Dracaena reflexa | Dracaena reflexa | Gleiche Gattung | Buschiger Wuchs |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Dracaena marginata,"Madagassischer Drachenbaum;Rotsaum-Drachenbaum;Madagascar Dragon Tree",Asparagaceae,Dracaena,perennial,day_neutral,tree,fibrous,"10a;10b;11a;11b","Madagaskar",yes,5-20,20,100-300,50-150,yes,limited,false,light_feeder,0.7
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Colorama,Dracaena marginata,"ornamental;pink_red_stripes",clone
Tricolor,Dracaena marginata,"ornamental;three_colored_stripes",clone
Bicolor,Dracaena marginata,"ornamental;two_toned",clone
```

---

## Quellenverzeichnis

1. [Epic Gardening — Dracaena marginata](https://www.epicgardening.com/dracaena-marginata-madagascar-dragon-tree/) — Pflegehinweise, Varianten
2. [Gardenia.net — Dragon Tree](https://www.gardenia.net/plant/dracaena-marginata-dragon-tree) — Wachstumsparameter, Standortdaten
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (besonders Katzen)
4. [Bloomscape — Dracaena Care Guide](https://bloomscape.com/plant-care-guide/dracaena/) — Allgemeine Dracaena-Pflege
5. [Ohio Tropics — Dracaena marginata Care](https://www.ohiotropics.com/2022/04/15/dracaena-marginata-care/) — Praxiswissen
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Clemson HGIC — Dracaena Factsheet](https://hgic.clemson.edu/factsheet/dracaena/) — Schwachlicht-Toleranz, Fluorid-/Salzempfindlichkeit, Boden-pH 6.0–6.5, Temperaturen (University Extension)
7. [Sterck et al. 2013, Journal of Ecology — Light compensation point in tropical forest understorey shrubs](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — Lichtkompensationspunkt schattentoleranter Unterwuchsarten (peer-reviewed), Beleg für niedrigen LCP-Bereich
8. [Response of Tropical Foliage Plants to Interior Low Light Conditions (ResearchGate)](https://www.researchgate.net/publication/265921672_Response_of_Tropical_Foliage_Plants_to_Interior_Low_Light_Conditions) — Foliage-Plant-Physiologie, Schatten-/C3-Einordnung, niedrige Lichtkompensation
9. [HomePlantBot — Dracaena & Dragon Trees Watering & salt sensitivity](https://homeplantbot.com/dracaena-dragon-trees-watering-salt-sensitivity/) — Salzempfindlichkeit, Staunässe-Empfindlichkeit, Gießpraxis
10. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Raubmilbe gegen Spinnmilben, Ausbringrate/Bedingungen (University Extension)
11. [Koppert — Brown soft scale (Coccus hesperidum) biocontrol](https://www.koppert.com/plant-pests/mealybugs-and-scales/brown-soft-scale/) — Metaphycus helvolus gegen Weichschildläuse, Wirtszuordnung
12. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Mealybug Destroyer gegen Schmierläuse, Ausbringrate
13. [Penn State Extension — Hydroponics Systems & Principles of Plant Nutrition](https://extension.psu.edu/hydroponics-systems-and-principles-of-plant-nutrition-essential-nutrients-function-deficiency-and-excess) — Mikronährstoff-Referenzspannen (Mn/Zn/Cu/Mo) (University Extension)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
