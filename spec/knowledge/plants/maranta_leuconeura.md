# Pfeilwurz, Gebet-Pflanze — Maranta leuconeura

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [PLNTS.com](https://plnts.com/en/care/houseplants-family/maranta), [Gardenia.net](https://www.gardenia.net/plant/maranta-leuconeura-prayer-plant-grow-care-tips), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/prayer-plant-maranta-leuconeura-care-guide/), [Old Farmer's Almanac](https://www.almanac.com/plant/prayer-plant-care-how-grow-healthy-happy-maranta), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Maranta leuconeura | `species.scientific_name` |
| Volksnamen (DE/EN) | Pfeilwurz, Gebet-Pflanze; Prayer Plant | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Maranta | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis pathway) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur Wuchs (°C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für M. leuconeura auffindbar. Warmtropische Art (Min. 15 °C, Optimum 18–27 °C) → wärmeliebende Konvention ~10 °C plausibel, jedoch nicht quellenbelegt. --> | `species.base_temp` |
| Vernalisation Mindest-Tage | — (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral) → kein numerischer Kurztag-/Langtag-Schwellenwert. --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Sehr empfindlich gegen Zugluft und Temperaturschwankungen. | `species.hardiness_detail` |
| Heimat | Tropisches Brasilien — Unterwuchs tropischer Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Gebet-Pflanze zeigt Nyktinastie — abends falten sich die Blätter senkrecht wie Gebetshände zusammen, morgens öffnen sie sich wieder. Dieses Verhalten ist ein guter Indikator für die Pflanzengesundheit: Wenn Blätter nachts geschlossen bleiben, ist etwas nicht in Ordnung. Gehört zur selben Familie wie Goeppertia (Calathea) und hat ähnliche Anforderungen — weicht aber im Detail ab (toleranter gegenüber weniger perfekten Bedingungen als echte Calatheas).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (kleine weiß-violette Blüten; in Zimmerkultur selten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen im Frühjahr ist am zuverlässigsten. Stängelstecklinge (5–8 cm, unterhalb eines Knotens) in Wasser bewurzeln (2–4 Wochen) oder direkt in feuchtes Perlite/Substrat stecken.

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

**Hinweis:** Maranta leuconeura ist nicht giftig — ASPCA listet die Pflanze als sicher für Katzen, Hunde und Kinder. Ideal für Haushalte mit Haustieren.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kein regelmäßiger Rückschnitt nötig. Abgestorbene oder beschädigte Blätter an der Basis entfernen. Überlange Triebe bei Bedarf kürzen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, feuchtigkeitshaltende aber gut durchlässige Erde: Einheitserde mit 20% Perlite + 10% Kokoserde. pH 5.5–6.5. Kein Kalk im Substrat. Mischung sollte Feuchtigkeit halten ohne zu verdichten. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 2 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 8 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–20 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Schwellenwert (ECe) für M. leuconeura belegt; qualitativ salzempfindlich (Blattspitzennekrose durch Salz/Fluorid). --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope belegt. --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

**Hinweis:** Schattenlaubpflanze (shade leaf) des tropischen Regenwald-Unterwuchses (understory) mit sehr niedrigem Lichtkompensationspunkt — der angegebene Bereich (2–8 µmol/m²/s) entspricht dem unteren Ende der C3-Spanne (8–16 µmol/m²/s) für Schattenblätter. NUR Kompensationspunkt; Lichtsättigung und Photoinhibition (direkte Sonne bleicht das Blattmuster aus) sind hier bewusst NICHT enthalten. Wurzeltiefe flach und breit-spreitend (rhizomatöser Horst) — konsistent mit Min. Topftiefe 12 cm (§1.6). Salzempfindlichkeit qualitativ stark belegt (Salz-/Fluoridschäden mit Blattspitzennekrose), jedoch ohne quantitativen ECe-Maas-Hoffman-Wert. Boden-pH-Vorzug 5.5–6.5 harmonisiert mit §1.6 (Substrat) und §2.3 (Nährstoffprofile).
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
| Licht PPFD (µmol/m²/s) | 50–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.8 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 2–7 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.0 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 60–180 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.5–6.5 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 5.5–6.5 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (active feeding solution, Phase Aktives Wachstum):**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Aktives Wachstum | 0.5 | 0.05–0.1 | 0.03–0.05 | 0.02–0.05 |
| Winterruhe | — | — | — | — |

**Hinweis:** Mikronährstoff-Richtwerte einer ausgewogenen Schwachzehrer-Nährlösung (light feeder, halbe Dosis). Mangan (manganese), Zink (zinc), Kupfer (copper) und Molybdän (molybdenum) liegen am unteren Rand üblicher Foliage-Solution-Bereiche, da M. leuconeura salzempfindlich ist und mit halber Düngerkonzentration kultiviert wird. Fluoridfreie Quellen verwenden.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideen-Dünger | Compo | base | 7-5-6 | 3 ml/L (halbe Dosis, alle 4 Wochen) | Wachstum |
| Zimmerpflanzen-Flüssigdünger | Substral | base | 7-3-7 | 3 ml/L (halbe Dosis) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4 Wochen März bis September — immer mit halber Konzentration. Kein Dünger Oktober bis Februar. Fluorid im Wasser oder Dünger schadet der Pflanze (Blattspitzenverbrennung). Weiches Wasser oder destilliertes Wasser empfohlen. Fluoridhaltige Dünger meiden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser zwingend. Regen- oder destilliertes Wasser bevorzugt. Fluorid schadet (Blattspitzenverbrennung). | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (September, bei Nachttemperaturen unter 15 °C) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 6 (Juni, nach den Eisheiligen, sobald >15 °C stabil) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–22 | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (kein direktes Sonnenlicht); ggf. Pflanzenlampe bei <50 µmol/m²/s | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert: alle 7–10 Tage, Substrat oberflächlich antrocknen lassen, nie austrocknen | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Maranta leuconeura ist nicht frosthart und überwintert als reine Zimmer-/Kübelpflanze frostfrei (frost_free) im warmen Innenraum — kein Auspflanzen, kein Einlagern von Knollen. Sie wird ganzjährig drinnen kultiviert; ein sommerlicher Aufenthalt im Freien (geschützter Halbschatten) ist optional und erfordert die Rückführung ins Haus, sobald Nachttemperaturen unter 15 °C fallen. Während der Winterruhe (§2.1) wird nicht gedüngt und seltener gegossen. Hohe Luftfeuchte trotz Heizungsluft sicherstellen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben (häufig bei trockener Luft) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Thrips | Frankliniella spp. | Silbrig-glänzende Streifen, Blätter deformiert | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken mit gelbem Hof | Nasses Laub |
| Echter Mehltau | fungal | Weißer Belag | Geringe Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Erhöhte Luftfeuchtigkeit | cultural | Humidifier, Kiesschale mit Wasser | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Sprühen | 3 Tage | Thrips, Blattläuse |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|---------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–6/m² präventiv, 20–50/m² kurativ; wöchentl. wiederholen | 2–3 Wochen |
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | 2–5 Käfer je befallener Pflanze (≈5/m²) | 3–4 Wochen |
| Raubmilbe | Neoseiulus (Amblyseius) cucumeris | Thrips (Frankliniella spp.) | 50–100/m² bzw. 1 Tüten-Depot je 1–2 m² | ~2 Wochen |

**Hinweis:** Nützlingseinsatz funktioniert am besten bei der für M. leuconeura ohnehin nötigen hohen Luftfeuchte (>55%). *Phytoseiulus persimilis* benötigt aktive Spinnmilbenpopulation als Nahrung (nicht rein präventiv ohne Beute). *Cryptolaemus montrouzieri* vertilgt alle Schmierlausstadien inkl. Eigelege. *Neoseiulus cucumeris* bekämpft junge Thripslarven; Slow-Release-Tüten geben über Wochen kontinuierlich Raubmilben ab. Keine Breitband-Insektizide parallel einsetzen (tötet Nützlinge).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Calathea/Goeppertia | Goeppertia orbifolia | Gleiche Familie | Noch spektakuläreres Blattmuster |
| Stromanthe | Stromanthe thalia | Gleiche Familie | Robuster, weniger anspruchsvoll |
| Ctenanthe | Ctenanthe burle-marxii | Gleiche Familie | Toleranter bei Trockenheit |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Maranta leuconeura,"Pfeilwurz;Gebet-Pflanze;Prayer Plant",Marantaceae,Maranta,perennial,day_neutral,herb,rhizomatous,"11a;11b;12a","Tropisches Brasilien",yes,1-5,12,15-30,30-60,yes,no,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Erythroneura,Maranta leuconeura,"ornamental;red_veins;herringbone_pattern",clone
Kerchoveana,Maranta leuconeura,"ornamental;rabbit_tracks;green_spots",clone
Massangeana,Maranta leuconeura,"ornamental;dark_green;silver_midrib",clone
```

---

## Quellenverzeichnis

1. [PLNTS.com — Maranta Care](https://plnts.com/en/care/houseplants-family/maranta) — Ganzjahrespflege
2. [Gardenia.net — Maranta leuconeura](https://www.gardenia.net/plant/maranta-leuconeura-prayer-plant-grow-care-tips) — Botanische Daten
3. [Healthy Houseplants — Prayer Plant](https://www.healthyhouseplants.com/indoor-houseplants/prayer-plant-maranta-leuconeura-care-guide/) — Schädlinge, Kulturdaten
4. [Old Farmer's Almanac — Prayer Plant](https://www.almanac.com/plant/prayer-plant-care-how-grow-healthy-happy-maranta) — Pflegehinweise
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Wikipedia — Maranta leuconeura](https://en.wikipedia.org/wiki/Maranta_leuconeura) — Marantaceae-Unterwuchs-Ökologie (tropischer Regenwald, Brasilien), Photosynthese-Kontext C3
7. [NC State Extension — Maranta leuconeura Plant Toolbox](https://plants.ces.ncsu.edu/plants/maranta-leuconeura/) — Lichtansprüche (Schatten/keine direkte Sonne), Hardiness Zonen, Wurzelrot bei Staunässe
8. [BestVA LED — Light Saturation Point / Light Compensation Point](https://www.bestvaled.com/blogs/horticulture-lighting-terms/what-the-light-saturation-point-and-light-compensation-point-are) — Lichtkompensationspunkt C3 (8–16 µmol, Schattenblätter unteres Ende)
9. [ScienceDirect Topics — Light Compensation Point overview](https://www.sciencedirect.com/topics/engineering/light-compensation) — LCP-Spannen schattentoleranter Unterwuchs-Arten (10–50 µmol)
10. [Healthy Houseplants — Maranta spp. Care](https://www.healthyhouseplants.com/indoor-houseplants/prayer-plant-maranta-spp-care-guide-tips-for-growing-vibrant-maranta/) — Salz-/Fluoridempfindlichkeit, Staunässe/Wurzelfäule, Blattspitzennekrose
11. [Plantophiles — Maranta leuconeura Care](https://plantophiles.com/plant-care/maranta-leuconeura/) — Boden-pH-Vorzug 5.5–6.5, Substratmischung
12. [Oxford Academic / Journal of Experimental Botany — Canopy light & shade avoidance](https://academic.oup.com/jxb/article/76/3/712/7727419) — R:FR-Abfall und Far-Red-Anreicherung im Unterwuchs (FR-Fraction > offenes Tageslicht ≈0.5)
13. [Koppert (US) — Phytoseiulus persimilis](https://www.koppertus.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate Raubmilbe gegen Spinnmilben
14. [Planet Natural — Cryptolaemus montrouzieri](https://www.planetnatural.com/beneficial-insects-101/cryptolaemus-montrouzieri/) — Ausbringrate Mealybug Destroyer gegen Schmierläuse
15. [Koppert — Neoseiulus (Amblyseius) cucumeris](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/neoseiulus-cucumeris/) — Ausbringrate Raubmilbe gegen Thrips
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
