# Klapperschlangen-Calathea — Goeppertia lancifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net](https://www.gardenia.net/plant/calathea-lancifolia-rattlesnake-plant), [NC State Extension](https://plants.ces.ncsu.edu/plants/goeppertia-insignis/), [Smart Garden Guide](https://smartgardenguide.com/rattlesnake-plant-care-calathea-lancifolia/), [Plant Care Today](https://plantcaretoday.com/rattlesnake-plant.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Goeppertia lancifolia | `species.scientific_name` |
| Synonyme | Calathea lancifolia (Handelsname), Calathea insignis (älteres Synonym) | — |
| Volksnamen (DE/EN) | Klapperschlangen-Calathea, Lanzettblatt-Calathea; Rattlesnake Plant, Rattlesnake Calathea | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Goeppertia | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (°C) | <!-- DATEN FEHLEN --> keine belegte Wuchs-GDD-Basis für diese tropische Zierstaude; Art wird nicht über Wärmesummen (Growing Degree Days) kultiviert | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Vernalisation Mindest-Tage | — (entfällt, tropisch, kein Kältebedarf) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | — (tagneutral / day_neutral, kein Kurztag-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 11a, 11b, 12a, 12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 16°C, optimal 18–27°C. | `species.hardiness_detail` |
| Heimat | Brasilien — tropische Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Klapperschlangen-Calathea ist eine der schattentoleranten und robusten Vertreter der Marantaceen. Die langen, lanzettlichen Blätter mit dem welligen Rand und dem dunkelgrünen Schuppenmuster (erinnert an Schlangenhaut) sind charakteristisch. Zeigt ausgeprägte Nyktinastie. Im Vergleich zu anderen Calathea-Arten etwas pflegeleichter. Botanischer Hinweis: Der akzeptierte Name (Kew/POWO) ist Goeppertia lancifolia (Petersen) Borchs. & S.Suárez. Im Handel wird die Pflanze meist noch als Calathea lancifolia geführt.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
<!-- Quelle: growing-phase-auditor 2026-07 -->
| Blütemonate | 5, 6, 7 (kleine, unscheinbare gelbe bis gelb-orange Blüten in konischen Ähren; in Zimmerkultur sehr selten) | `species.bloom_months` |
<!-- /Quelle: growing-phase-auditor 2026-07 -->

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Rhizom-Teilung beim Umtopfen im Frühjahr — Abschnitte mit 2–3 Blättern. Hohe Luftfeuchtigkeit nach der Teilung.

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

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 45–75 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no (zu empfindlich) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, humusreiche, gut drainierte Erde mit leichter Feuchtigkeitsspeicherung. pH 6.0–7.0. Mix aus Einheitserde + Perlite (20%) + Kokosfaser (15%). | — |

### 1.7 Umgebungs-Physiologie & Standortqualität

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (PPFD µmol/m²/s) | 50–100 | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-Schwellenwert für diese Art; Klasse sensitive entspricht qualitativ einer niedrigen Schwelle (< 2 dS/m Substrat-ECe) | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> kein belegter Maas-Hoffman-Slope für diese Art | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt (light compensation point, LCP, Netto-Photosynthese = 0) ist aus Messungen an *Calathea insignis* (= älteres Synonym für *G. lancifolia*) mit 100 µmol/m²/s und der nahverwandten *C. makoyana* mit 50 µmol/m²/s belegt; die Spanne 50–100 deckt beide Marantaceen-Messwerte ab. Der Lichtsättigungspunkt (light saturation point) liegt bei *C. insignis* bei rund 600 µmol/m²/s, bei *C. makoyana* bei 400 — diese Sättigungswerte gehören NICHT ins LCP-Feld. Typische Schattenpflanze (shade plant) des Regenwald-Unterwuchses, daher `shade` (kein partial_shade). Salzempfindlichkeit: Calathea reagiert auf Fluorid, Chlorid und harte Wassersalze mit Tip-Burn (Blattspitzennekrose), daher Salztoleranz-Klasse `sensitive`; Bezugsgröße bei einem etwaigen ECe-Wert wäre die Substrat-ECe, nicht die Gießwasser-EC. Boden-pH 6.0–6.5 ist quellentreu (leicht sauer); breiterer tolerierter Bereich bis 7.0 deckt sich mit §1.6/§2.3.
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
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–13 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–30 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | <!-- DATEN FEHLEN --> kein artspezifischer Messwert; als Regenwald-Unterwuchspflanze unter Blätterdach tendenziell FR-angereichert (> 0.5 unter dichtem Kronendach), aber ohne belegte Messung für G. lancifolia nicht quantifiziert | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 60–200 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 3–9 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 50 | 20 | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich, halbdosiert) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis August, halbe Empfehlungsdosis. Oktober bis März kein Dünger. Weiches Wasser bevorzugen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser bevorzugt; gleichmäßig feucht; hohe Luftfeuchtigkeit (Luftbefeuchter, Kieselsteinschale) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.3 Überwinterung

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung | frost_free | `overwintering_profile.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profile.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost / Nachttemperaturen < 16 °C) | `overwintering_profile.winter_action_month` |
| Frühjahrs-Maßnahme | move_outdoors | `overwintering_profile.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mitte/Ende Mai, nach den Eisheiligen) | `overwintering_profile.spring_action_month` |
| Winterquartier Temperatur (°C) | 16–22 | `overwintering_profile.winter_quarter_temp_c` |
| Winterquartier Licht | hell, indirekt (PPFD 60–200 µmol/m²/s); kein direktes Sonnenlicht | `overwintering_profile.winter_quarter_light` |
| Winterquartier Gießen | reduziert, gleichmäßig leicht feucht (Gießintervall 10–14 Tage); Staunässe vermeiden, weiches/kalkarmes Wasser | `overwintering_profile.winter_quarter_watering` |

**Hinweis:** Reine Zimmer-/Kübelpflanze ohne Frosttoleranz (Mindesttemperatur 16 °C). Daher `frost_free` (frostfreies Überwintern im Innenraum), KEIN Ausgraben/Einlagern (`dig_and_store` wäre nur für Knollengewächse korrekt). Ein sommerlicher Aufenthalt im Freien (Schatten/Halbschatten) ist optional; in Mitteleuropa (USDA 6–8) muss die Pflanze ganzjährig bzw. spätestens ab Oktober frostfrei im Haus stehen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, punktförmige Gelbfärbung | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Blattläuse | Aphis spp. | Klebrige Triebe | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke trotz feuchtem Substrat | Staunässe |
| Blattflecken | fungal | Braune Flecken mit gelbem Hof | Nasses Laub |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Luftbefeuchter | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Schmierläuse |

### 5.4 Nützlinge (Biologische Bekämpfung)

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Nützling | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|----------------|--------------|------------------|
| Raubmilbe *Phytoseiulus persimilis* | Spinnmilbe (*Tetranychus urticae*) | 2–50 Stück/m² je Ausbringung, wöchentlich wiederholen bis Befall erloschen | 2–3 Wochen (optimal 17–28 °C, > 60 % rel. Luftfeuchte) |
| Australischer Marienkäfer *Cryptolaemus montrouzieri* (Schmierlaus-Räuber) | Schmierlaus (*Pseudococcus* spp.) | ca. 5 Käfer/befallene Pflanze; 2–3 kleinere Ausbringungen besser als eine große | 4–8 Wochen bis sichtbare Reduktion |
| Schlupfwespe *Aphidius colemani* | Blattläuse (*Aphis* spp.) | 0,25–4 Tiere/m² je Ausbringung, mind. 2–3 Ausbringungen im Wochenabstand | ca. 2 Wochen (überlappende Generationen) |

**Hinweis:** Nützling-Wirt-Zuordnung fachlich getrennt: *Phytoseiulus persimilis* ausschließlich gegen Spinnmilben, *Cryptolaemus montrouzieri* gegen Schmierläuse (Wollläuse), *Aphidius colemani* gegen Blattläuse. Im Wohnraum sind Nützlinge nur eingeschränkt praktikabel (Flugverhalten, Luftfeuchte); Einsatz primär im Gewächshaus oder isolierten Quarantänebereich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Calathea orbifolia | Goeppertia orbifolia | Marantaceae | Größere Rundblätter |
| Pfauenkorb-Marante | Goeppertia makoyana | Marantaceae | Pfauenmuster |
| Ctenanthe | Ctenanthe burle-marxii | Marantaceae | Robuster, Fischgrätenmuster |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Goeppertia lancifolia,"Klapperschlangen-Calathea;Lanzettblatt-Calathea;Rattlesnake Plant;Rattlesnake Calathea",Marantaceae,Goeppertia,perennial,day_neutral,herb,rhizomatous,"11a;11b;12a;12b","Brasilien (tropische Regenwälder)",yes,3-10,15,45-75,30-60,yes,no,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardenia.net — Calathea lancifolia](https://www.gardenia.net/plant/calathea-lancifolia-rattlesnake-plant) — Botanische Daten
2. [NC State Extension — Goeppertia insignis](https://plants.ces.ncsu.edu/plants/goeppertia-insignis/) — Aktuelle Nomenklatur
3. [Smart Garden Guide — Rattlesnake Plant](https://smartgardenguide.com/rattlesnake-plant-care-calathea-lancifolia/) — Pflegehinweise
4. [Plant Care Today — Rattlesnake Plant](https://plantcaretoday.com/rattlesnake-plant.html) — Schädlinge
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [NCBI/PMC — Biochemical and Physiological Characteristics of Photosynthesis in Plants of Two Calathea Species](https://pmc.ncbi.nlm.nih.gov/articles/PMC5877565/) — Lichtkompensationspunkt (LCP) *C. insignis* 100 / *C. makoyana* 50 µmol/m²/s, Lichtsättigung 600 / 400 µmol/m²/s, Schattenpflanzen-Charakteristik
7. [Springer/Oecologia — Comparative life history and physiology of two understory Neotropical herbs](https://link.springer.com/article/10.1007/BF00320821) — *Calathea* als schattentolerante Regenwald-Unterwuchsstaude (shade tolerance)
8. [Wikipedia / e-monocot — Marantaceae (Zingiberales, Monokotyledonen)](http://families.e-monocot.org/classification/marantaceae) — taxonomische Einordnung, C3-Stoffwechsel (keine CAM-/C4-Sukkulentenfamilie)
9. [Agri Farming — Calathea Brown Tips: Humidity vs Water Quality](https://www.agrifarming.in/calathea-brown-tips-fixes) — Salz-/Fluorid-Empfindlichkeit (sensitive), Tip-Burn durch harte Wassersalze
10. [Healthy Houseplants — Rattlesnake Plant Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/rattlesnake-plant-calathea-lancifolia-care-guide/) — Staunässe-Empfindlichkeit (Wurzelfäule bei waterlogging), Boden-pH leicht sauer
11. [Greg.app — Soil for Calathea Rattlesnake](https://greg.app/calathea-rattlesnake-soil/) — Boden-pH-Vorzug 6.0–6.5, gut drainiert
12. [Koppert — Phytoseiulus persimilis (Spinnmilben-Raubmilbe)](https://www.koppert.com/crop-protection/biological-pest-control/predatory-mites/phytoseiulus-persimilis/) — Ausbringrate/Etablierung Spinnmilbenkontrolle
13. [Koppert — Aphidius colemani (Blattlaus-Schlupfwespe)](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Ausbringrate/Etablierung Blattlauskontrolle
14. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet (Schmierlaus-Räuber)](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Ausbringrate/Etablierung Schmierlauskontrolle
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
15. [Missouri Botanical Garden — Plant Finder: Calathea lancifolia](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=244436) — Blütenfarbe gelb, Blühzeit später Frühling/Frühsommer, seltene Blüte an Zimmerpflanzen
16. [Gardening Know How — Calathea Rattlesnake Plant Care](https://www.gardeningknowhow.com/houseplants/calathea-plants/calathea-rattlesnake-plant-care.htm) — Blütenfarbe gelb-orange, seltene Blüte an Zimmerpflanzen
<!-- /Quelle: growing-phase-auditor 2026-07 -->
