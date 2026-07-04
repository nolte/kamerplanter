# Zebrapflanze (Glanzkölbchen) — Aphelandra squarrosa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [PLNTS.com – Aphelandra](https://plnts.com/de/care/houseplants-family/aphelandra), [Feey – Zebrapflanze](https://feey.ch/pages/zebrapflanze), [Plant Circle – Aphelandra](https://plantcircle.com/de-eu/blogs/plant-care-tips/aphelandra-care-tips), [Pflanzenfreunde – Aphelandra](https://www.pflanzenfreunde.com/aphelandra-glanzkoelbchen.htm)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aphelandra squarrosa | `species.scientific_name` |
| Volksnamen (DE/EN) | Zebrapflanze, Glanzkölbchen; Zebra Plant | `species.common_names` |
| Familie | Acanthaceae | `species.family` → `botanical_families.name` |
| Gattung | Aphelandra | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 11a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Ausschließlich als Zimmerpflanze; Temperaturen unter 13°C vermeiden | `species.hardiness_detail` |
| Heimat | Brasilien (Atlantischer Regenwald) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 13 | `species.base_temp` |
| Lebensdauer (Jahre, perennial) | 2–3 (durch Stecklinge faktisch unbegrenzt verlängerbar) | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false (Wachstumsverlangsamung im Winter, aber keine echte Zwangsruhe) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization) | false (tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage | — | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral; Blühinduktion über Lichtintensität, nicht Photoperiode) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (gelbe Blütenähre, nach guter Pflege) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | nicht bekannt toxisch | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 9, 10 (nach Blüte) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 (in Natur bis 180 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut drainierte Zimmerpflanzenerde; hohe Luftfeuchtigkeit essenziell; kalkfreies Wasser verwenden | — |

### 1.7 Umgebungs-Physiologie & Standortqualität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 10–25 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | — <!-- DATEN FEHLEN: kein quantitativer Maas-Hoffman-Schwellwert für die Art belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope für die Art belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.5–6.5 | `species.soil_ph_preference` |

> **Hinweise:**
> Der Lichtkompensationspunkt (light compensation point, LCP) ist nicht artspezifisch gemessen; angegeben ist die für tropische Unterwuchs-/Schattenpflanzen typische Gilden-Spanne (10–50 µmol/m²/s), nach unten eingeengt, da *A. squarrosa* eine ausgeprägte Schattenpflanze des atlantischen Regenwald-Unterwuchses ist. Der Lichtsättigungspunkt liegt deutlich höher (helles indirektes Licht, ~1.500–2.500 fc ≈ 150–270 µmol/m²/s am Blatt) — dieser gehört NICHT ins LCP-Feld.
> Die Salztoleranz-Klasse ist qualitativ als `sensitive` belegt (Blattspitzenverbrennung [leaf tip burn] bei Salzaufbau, regelmäßiges Spülen/Leaching empfohlen). Ein quantitativer ECe-Schwellwert (Maas-Hoffman a/b) liegt für die Art nicht vor und ist daher nicht eingetragen.
> Der pH-Vorzug 5.5–6.5 (sauer bis schwach sauer) harmonisiert mit dem Nährlösungs-pH 6.0–6.5 in §2.3.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 21–42 | 1 | false | false | low |
| Vegetativ | 150–240 | 2 | false | false | low |
| Blüte | 30–60 | 3 | false | false | medium |
| Ruhephase | 60–90 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.2 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (tagneutral; Blühinduktion über ausreichende Lichtintensität/Pflanzenreife, nicht über Tageslänge) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 65–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–26 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.45–0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Etablierung | 1:1:1 | 0.5–0.8 | 6.0–6.5 | 80 | 40 | — | 1 | 0.5 | 0.3 | 0.1 | 0.05 |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 | 0.5 | 0.5 | 0.1 | 0.05 |
| Blüte | 1:2:2 | 1.0–1.5 | 6.0–6.5 | 100 | 50 | — | 2 | 0.5 | 0.5 | 0.1 | 0.05 |
| Ruhephase | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
> **Mikronährstoff-Hinweis:** Mn/Zn/Cu/Mo sind nicht artspezifisch gemessen, sondern generische Standardwerte einer Nährlösung für Zier-/Blattpflanzen (`nutrient_profiles.manganese_ppm` / `zinc_ppm` / `copper_ppm` / `molybdenum_ppm`). Sie liegen am unteren bis mittleren Rand der gängigen Hydroponik-Empfehlungen (Mn 0.5–1, Zn 0.5–1, Cu 0.1–0.5, Mo 0.02–0.05 ppm), da *A. squarrosa* als Blattpflanze einen moderaten Bedarf hat. In der Ruhephase erfolgt keine Düngung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 21–42 Tage | Neue Blätter |
| Vegetativ → Blüte | time_based | 150–240 Tage | Ausreichende Pflanzenreife + helle Lichtintensität (ca. 3 Monate; tagneutral, kein Kurztag-Trigger) |
| Blüte → Ruhephase | time_based | 30–60 Tage | Nach Verblühen |
| Ruhephase → Vegetativ | time_based | 60–90 Tage | Frühjahrsaustrieb |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Zimmerpflanzendünger | Compo | base | 7-4-7 | 5 ml/L | 1 | vegetativ, blüte |
| Blühpflanzendünger | Substral | base | 4-6-8 | 5 ml/L | 1 | blüte |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Pflanzendünger organisch | Biobizz Top Max | organisch | 2 ml/L | Apr–Sep | medium_feeder |
| Langzeitdünger | Osmocote | organisch/langsam | 3 g/L Substrat | Apr–Jun | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–4 | Etablierung | 0.5–0.8 | 6.2 | 2.5 | Hälfte der Normaldosis |
| 5–26 | Vegetativ | 1.0–1.5 | 6.2 | 5 | Alle 4–6 Wochen |
| 27–34 | Blüte | 1.0–1.5 | 6.2 | 5 | Phosphorlastig |
| Nov–Feb | Ruhephase | 0.0 | — | — | Kein Dünger |

### 3.3 Besondere Hinweise zur Düngung

Aphelandra ist empfindlich gegen Überdüngung. Kalkarmes oder weiches Wasser ist wichtig — Kalk verklebt die feinen Wurzeln und hemmt die Nährstoffaufnahme. Hohe Luftfeuchtigkeit (>60%) ist für die Gesundheit der Pflanze wichtiger als die Düngung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkarmes Wasser zwingend; weiches Wasser oder Regenwasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Ruhephase | Warm halten (>18°C), wenig gießen | mittel |
| Mär | Umtopfen | Frisches Substrat; Stecklinge nehmen | hoch |
| Apr | Düngung beginnen | Schwache Düngergabe | mittel |
| Mai–Sep | Wachstum | Regelmäßig gießen, hohe Luftfeuchte sichern | hoch |
| Aug–Sep | Blüte | Blütenähre erscheint — Highlight der Pflanze | niedrig |
| Okt | Rückschnitt | Nach der Blüte zurückschneiden | mittel |
| Nov–Dez | Winterruhe | Warm, hell, wenig gießen, nicht düngen | niedrig |

### 4.3 Überwinterung
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors (ganzjährig drinnen; bei Sommerstand im Freien spätestens September einräumen) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors (optional; erst nach den Eisheiligen) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 13–18 (nie unter 13 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (moderates Licht, nicht dunkel) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | reduziert; Substrat leicht feucht halten, nie ganz austrocknen lassen | `overwintering_profiles.winter_quarter_watering` |

> **Hinweis:** *A. squarrosa* ist nicht winterhart (USDA 11–12) und wird ganzjährig als Zimmerpflanze frostfrei (frost_free) überwintert. Nach der Herbstblüte folgt eine ca. 2-monatige, etwas kühlere Ruhephase (Minimum 13 °C) mit reduzierter Wassergabe; sie ist keine echte Zwangsdormanz und kein Kältereiz zur Blühinduktion.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbe Punkte auf Blättern | leaf | alle | medium |
| Blattläuse | Aphis spp. | Deformierte Triebspitzen | stem | vegetative | easy |
| Wollläuse | Pseudococcus spp. | Weißes Gespinst | stem, leaf | alle | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal | Welke Blätter | overwatering | 7–14 | alle |
| Blattflecken | fungal | Gelblich-braune Flecken | overwatering, waterlogging | 7–14 | alle |
| Grauschimmel | fungal (Botrytis) | Grauer Belag | high_humidity + poor_airflow | 3–7 | flowering |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Aphidius colemani | Blattläuse | 5–10 | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Spinnmilben, Wollläuse |
| Insektizide Seife | biological | Kaliseife | Sprühen 2% | 0 | Blattläuse, Spinnmilben |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Aphelandra squarrosa |
|-----|-------------------|-------------|------------------------------|
| Calathea | Goeppertia spp. | Markante Blattzeichnung | Einfacher in der Pflege |
| Fittonia | Fittonia albivenis | Auffällige Blattadern | Kleiner, pflegeleichter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Aphelandra squarrosa,Zebrapflanze;Glanzkölbchen;Zebra Plant,Acanthaceae,Aphelandra,perennial,day_neutral,shrub,fibrous,11a;11b;12a;12b,0.0,Brasilien Atlantischer Regenwald,yes,7,15,60,50,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [PLNTS.com – Aphelandra Pflege](https://plnts.com/de/care/houseplants-family/aphelandra) — Pflegetipps, Toxizität
2. [Feey – Zebrapflanze](https://feey.ch/pages/zebrapflanze) — Steckbrief
3. [Plant Circle – Aphelandra Care Tips](https://plantcircle.com/de-eu/blogs/plant-care-tips/aphelandra-care-tips) — Detaillierte Pflege
4. [Pflanzenfreunde – Aphelandra](https://www.pflanzenfreunde.com/aphelandra-glanzkoelbchen.htm) — Botanik, Kulturtipps
5. [Living at Home – Glanzkölbchen](https://www.livingathome.de/balkon-garten/blumen-im-haus/12778-rtkl-aphelandra-squarrosa-glanzkoelbchen) — Porträt
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NC State Extension – Aphelandra squarrosa](https://plants.ces.ncsu.edu/plants/aphelandra-squarrosa/) — Lichtansprüche (partial shade, kein Vollsonne), saurer pH (<6.0), Wuchsgröße, Wuchsrate
7. [Missouri Botanical Garden – Aphelandra squarrosa Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=275287) — Standort, Pflege, Wuchsdaten
8. [UK Houseplants – Aphelandra squarrosa Care Guide](https://www.ukhouseplants.com/plants/aphelandra-squarrosa) — Lebensdauer (1–2 Jahre nach Blüte), Überwinterung, Lichtintensität als Blühtrigger, partielle Sonnentoleranz
9. [Healthy Houseplants – Zebra Plant Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/zebra-plant-aphelandra-squarrosa-care-guide/) — Salzaufbau/Leaching, Lichtbedarf in fc, Winterruhe-Temperatur
10. [PLNTS.com (EN) – Aphelandra Care](https://plnts.com/en/care/houseplants-family/aphelandra) — fibröses, flaches Wurzelsystem, Staunässe-/Wurzelfäule-Empfindlichkeit, Drainage
11. [Greg – Zebra Plant Roots](https://greg.app/zebra-plant-roots/) — flaches fibröses Wurzelsystem (obere Bodenschicht), Drainagebedarf
12. [Plants Rescue – Aphelandra squarrosa](https://www.plantsrescue.com/posts/aphelandra-squarrosa) — Winterruhe (kühl, nicht unter 12 °C), Lebensdauer, Pflege
13. [Wikipedia – Aphelandra squarrosa](https://en.wikipedia.org/wiki/Aphelandra_squarrosa) — Herkunft (atlantischer Regenwald Brasilien), Botanik
14. [Sterck et al. 2013, Journal of Ecology – Light compensation point in tropical forest understorey shrubs](https://besjournals.onlinelibrary.wiley.com/doi/10.1111/1365-2745.12076) — LCP-Spanne tropischer Schatten-/Unterwuchspflanzen (Gilden-Referenz)
15. [Journals of the University of Chicago – Origin of C4 Photosynthesis in Acanthaceae (Blepharis)](https://www.journals.uchicago.edu/doi/full/10.1086/683011) — Acanthaceae überwiegend C3, C4 nur in Sektion Acanthodium (Beleg C3 für Aphelandra)
16. [Penn State Extension – Hydroponics: Essential Nutrients](https://extension.psu.edu/hydroponics-systems-and-principles-of-plant-nutrition-essential-nutrients-function-deficiency-and-excess) — Mikronährstoff-Referenzbereiche Mn/Zn/Cu/Mo
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

> **Nachtrag (Steckbrief-Erweiterung 2026-06):** Die Photoperiode wurde von `short_day` auf `day_neutral` korrigiert. *A. squarrosa* blüht durch **Lichtintensität** (ca. 3 Monate helles Licht → natürliche Herbstblüte) getriggert, nicht durch Tageslänge; sie ist nach übereinstimmenden Quellen tagneutral. Korrektur in §1.1 und in der CSV-Importzeile (§8.1) durchgeführt.
