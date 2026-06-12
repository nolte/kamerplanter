# Dieffenbachie — Dieffenbachia seguine

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/dieffenbachia-seguine/), [Planet Natural](https://www.planetnatural.com/dieffenbachia/), [Gardeners.com](https://www.gardeners.com/blogs/houseplant-encyclopedia/dieffenbachia-care-9747), [Poison Control](https://www.poison.org/articles/dieffenbachia-and-philodendron-202), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dieffenbachia seguine | `species.scientific_name` |
| Volksnamen (DE/EN) | Dieffenbachie, Stumme Bohne; Dumb Cane, Leopard Lily | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Dieffenbachia | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN: kein belegter Wuchs-/Phänologie-GDD-Basiswert für Dieffenbachia auffindbar; Kälteschaden unterhalb ~13 °C (55 °F) belegt, aber das ist keine GDD-Basis --> | `species.base_temp` |
| Kritische Tageslänge (h) | day_neutral (tagneutral — keine kritische Tageslänge) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–30°C. Empfindlich gegen Zugluft und Kälte. | `species.hardiness_detail` |
| Heimat | Tropisches Amerika (Karibik, Mittel- und Südamerika — feuchte Tropenwälder) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**SICHERHEITSHINWEIS:** Dieffenbachia enthält Calciumoxalat-Raphiden (Nadelkristalle). Bei Kontakt mit Mund und Zunge: starkes Brennen, Schwellung, vorübergehender Sprachverlust (daher "Dumb Cane"). In schweren Fällen können Atemwege schwellen — ärztliche Behandlung erforderlich! Kinder und Tiere MÜSSEN von dieser Pflanze ferngehalten werden. NIEMALS ohne Handschuhe umtopfen oder schneiden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 4, 5, 6 (Spadix/Kolbenblüte, selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stängelstücke (5–10 cm, mit mind. 1 Auge) horizontal in feuchtes Substrat legen oder aufrecht einpflanzen. Bewurzelung bei 22–26°C in 3–6 Wochen. Handschuhe tragen! Alternativ: Basis-Triebe teilen.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, sap (alle Pflanzenteile) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides, proteolytic_enzymes | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | true (Saft — Handschuhe obligatorisch) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

**Hinweis:** Kahle Stiele (untere Blätter fallen mit der Zeit ab) auf 5–10 cm kürzen — treiben neu aus. HANDSCHUHE und Schutzbrille verwenden, Saft nicht in Augen/Mund. Schnittwerkzeug danach reinigen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–180 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 50–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 20–30% Perlite. pH 6.0–6.5 (leicht sauer, vgl. §1.7/§2.3). Hohe organische Substanz bevorzugt. Gute Drainage unerlässlich. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein artspezifisch belegter Kompensationspunkt (Netto-Photosynthese = 0) in 2 unabhängigen Quellen; UF/IFAS nennt 50 fc ≈ 10 µmol als Innenraum-Mindestlicht, das ist jedoch ein Pflegerichtwert, kein Kompensationspunkt --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | <!-- DATEN FEHLEN: s.o. --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | <!-- DATEN FEHLEN: keine belegte Wurzeltiefe in 2 unabhängigen Quellen; flach-faseriges Wurzelsystem, Min. Topftiefe 20 cm (s. §1.6) --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-ECe-Schwellenwert (a) publiziert; UF/IFAS nennt für die Innenraum-Kultur Substrat-Bodenlösung (pour-through) >1,0 dS/m = nicht düngen, >2,0 dS/m = spülen — das ist ein Kultur-Pflegerichtwert, kein Maas-Hoffman-ECe --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope (b) publiziert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–6.5 | `species.soil_ph_preference` |

**Hinweis (Salz):** Dieffenbachia gilt in der professionellen Innenraumkultur als salzempfindlich. UF/IFAS (EP137) empfiehlt, bei Substrat-Salzgehalten (pour-through) ab 1,0 dS/m nicht weiter zu düngen und ab 2,0 dS/m das Substrat zu spülen; Blattrandnekrosen sind ein typisches Salz-/Hartwasser-Symptom (vgl. §4.1 Wasserqualität-Hinweis). Diese Schwellen beziehen sich auf die Substrat-Bodenlösung (ECe-nah), NICHT auf die Gießwasser-EC.

**Hinweis (Licht):** Schattentolerante Aroide des tropischen Unterwuchs; verträgt sehr niedrige Innenraum-Lichtwerte (ab ~50 fc), bei Direktsonne drohen Blattverbrennungen. Lichtsättigung der Photosynthese liegt für verwandte Aroide deutlich höher (~1000 µmol/m²/s nur an Sonnenblättern) — diese Sättigungswerte gehören NICHT in das Kompensationspunkt-Feld.
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
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–30 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 17–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 (Schatten-/Unterwuchspflanze des Regenwaldunterstands; höher als offenes Tageslicht ≈ 0.5, da Blätterdach Rot stärker absorbiert) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (VPD sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 (Schatten-/Unterwuchspflanze des Regenwaldunterstands; höher als offenes Tageslicht ≈ 0.5, da Blätterdach Rot stärker absorbiert) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.8–1.4 | 6.0–6.5 | 100 | 40 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–6.5 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe (Nährlösungs-Zielkonzentration aktive Wachstumsphase)**

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Aktives Wachstum | 0.5 | 0.05 | 0.02 | 0.01 |
| Winterruhe | — | — | — | — |

KA-Felder: `nutrient_profiles.manganese_ppm` / `nutrient_profiles.zinc_ppm` / `nutrient_profiles.copper_ppm` / `nutrient_profiles.molybdenum_ppm`. Werte entsprechen der etablierten Standard-Nährlösung (Hoagland & Arnon) und sind konsistent mit den ebenfalls als Nährlösungskonzentration angegebenen Ca-/Mg-Werten oben; keine artspezifischen Dieffenbachia-Sufficiency-Ranges in der Literatur publiziert.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Guano-Flüssigdünger | Gardol | organisch | 4 ml/L | Wachstum |

### 3.2 Besondere Hinweise

Monatlich März bis September düngen. Oktober bis Februar: kein Dünger. Stickstoffbetonte Formel fördert das üppige, große Laub. Bei schlechtem Licht: Düngermenge reduzieren (Pflanze kann Nährstoffe nicht verwerten).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser; hartes Wasser führt zu Blattrandnekrosen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Bewertung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 9 (spätestens vor erstem Frost / Nachttemperaturen unter 13–15 °C) | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 6 (nach den Eisheiligen, stabil über 15 °C; langsam an Licht gewöhnen) | `overwintering_profiles.spring_action_month` |
| Winterquartier-Temperatur (°C) | 16–22 (nie unter 13 °C; Kälteschaden ab ~13 °C / 55 °F) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier-Licht | Hell, ohne direkte Sonne; ggf. Pflanzenlampe bei kurzen Wintertagen | `overwintering_profiles.winter_quarter_light` |
| Winterquartier-Gießen | Reduziert; Substrat oberflächlich abtrocknen lassen, Staunässe meiden, keine Düngung | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** Reine Zimmerpflanze; falls sie im Sommer ins Freie/auf den Balkon gestellt wird, muss sie frostfrei (`frost_free`) im warmen Innenraum überwintern. Kein Ausgraben/Einlagern (kein `dig_and_store`), keine Knollen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, gelbe Flecken | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |
| Blattlaus | Aphididae | Kolonien, Honigtau, Deformation | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Blätter, fauliger Geruch | Staunässe |
| Blattflecken | fungal/bacterial | Braune/gelbe Flecken | Nasses Laub, Luftzirkulation schlecht |
| Botrytis | fungal | Grauschimmel | Hohe Feuchtigkeit, schlechte Belüftung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% (HANDSCHUHE!) | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus, Schmierlaus |
| Drainage verbessern | cultural | Topf/Substrat wechseln | 0 | Wurzelfäule |
| Luftzirkulation | cultural | Ventilator aufstellen | 0 | Botrytis, Blattflecken |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|-----------------------|----------------|--------------|------------------|
| Phytoseiulus persimilis (Raubmilbe) | Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m² je Freilassung, 1–2× wöchentlich wiederholen | Befallsreduktion in 2–3 Wochen |
| Cryptolaemus montrouzieri (Marienkäfer, „Mealybug Destroyer") | Schmierläuse (Pseudococcus spp.) | ca. 2–5 Käfer/m² (Befallsnester) | 4–8 Wochen bis sichtbare Reduktion |
| Aphidius colemani (Schlupfwespe) | Blattläuse (Aphididae) | 0,25–4 Tiere/m² je Freilassung, mind. 3× wiederholen | 2–3 Wochen |

**Hinweis:** Nützlingseinsatz braucht warme, möglichst feuchte Bedingungen (P. persimilis bevorzugt 60–90 % rF, < 32 °C) — passt zum tropischen Pflegeprofil dieser Art. Bei Innenraumkultur Nützlinge gezielt an Befallsnestern ausbringen; keine breitwirksamen Insektizide parallel (töten die Nützlinge). Zuordnung Nützling↔Wirt fachlich getrennt: Raubmilbe gegen Spinnmilben, Mealybug Destroyer gegen Schmierläuse, Aphidius gegen Blattläuse.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Kompakte Dieffenbachie | Dieffenbachia compacta | Gleiche Gattung | Kleiner, kompakter |
| Büscheldieffenbachie | Dieffenbachia maculata | Gleiche Gattung | Auffällige Blattmusterung |
| Philodendron | Philodendron hederaceum | Ähnliches Erscheinungsbild | Weniger gefährlich bei Kontakt |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Dieffenbachia seguine,"Dieffenbachie;Stumme Bohne;Dumb Cane;Leopard Lily",Araceae,Dieffenbachia,perennial,day_neutral,herb,fibrous,"10a;10b;11a;11b","Tropisches Amerika",yes,5-15,20,60-180,50-100,yes,no,false,medium_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Camille,Dieffenbachia seguine,"ornamental;cream_center;green_edges",clone
Compacta,Dieffenbachia seguine,"ornamental;compact;green_white",clone
Tropic Snow,Dieffenbachia seguine,"ornamental;large;cream_variegated",clone
```

---

## Quellenverzeichnis

1. [NC State Extension — Dieffenbachia seguine](https://plants.ces.ncsu.edu/plants/dieffenbachia-seguine/) — Botanische Daten, Kulturdaten
2. [Planet Natural — Dieffenbachia](https://www.planetnatural.com/dieffenbachia/) — Pflegehinweise
3. [Gardeners.com — Dieffenbachia Care](https://www.gardeners.com/blogs/houseplant-encyclopedia/dieffenbachia-care-9747) — Licht, Gießen
4. [Poison Control — Dieffenbachia and Philodendron](https://www.poison.org/articles/dieffenbachia-and-philodendron-202) — Toxizitätsdetails
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [UF/IFAS EDIS EP137 — Cultural Guidelines for Commercial Production of Interiorscape Dieffenbachia](https://edis.ifas.ufl.edu/publication/EP137) — Temperatur (60–90 °F Produktion, Kälteschaden < 55 °F), pH 6.0–6.5, Salzgehalt/Salzempfindlichkeit (pour-through 1,0/2,0 dS/m), Innenraum-Lichttoleranz
7. [UF/IFAS Gardening Solutions — Dieffenbachia](https://gardeningsolutions.ifas.ufl.edu/plants/houseplants/dieffenbachia/) — Pflege, Schattentoleranz, Standortansprüche
8. [Lima et al., Brazilian Journal of Botany — Allomorphic growth of Epipremnum aureum (Araceae): leaf morphophysiology understory→canopy](https://link.springer.com/article/10.1007/s40415-016-0331-6) — C3-Photosynthese und Lichtsättigung verwandter Aroide (Beleg Photosynthese-Typ / Schattenanpassung)
9. [Gardening Know How — Dieffenbachia Winter Care / Overwintering](https://www.gardeningknowhow.com/houseplants/dumb-cane/dieffenbachia-care-in-winter.htm) — Überwinterung (frostfrei, > 16 °C, reduziert gießen, keine Düngung)
10. [Cafe Planta — Dieffenbachia Temperature Tolerance](https://cafeplanta.com/a/blog/dieffenbachia-temperature-tolerance-a-comprehensive-guide) — optimaler Temperaturbereich (18–24 °C), Mindesttemperatur 15 °C
11. [Wikipedia — Hoagland solution](https://en.wikipedia.org/wiki/Hoagland_solution) — Standard-Mikronährstoff-Nährlösung (Mn 0,5 / Zn 0,05 / Cu 0,02 / Mo 0,01 ppm)
12. [Koppert US — Phytoseiulus persimilis (Spidex)](https://www.koppertus.com/spidex/) — Ausbringrate Raubmilbe gegen Spinnmilben
13. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Etablierungszeit Raubmilbe (2–3 Wochen)
14. [Koppert Canada — Aphidius colemani](https://retail.koppert.ca/pages/beneficial-insects/aphidius-colemani) — Ausbringrate Schlupfwespe gegen Blattläuse
15. [FGMN Nursery — Cryptolaemus montrouzieri Guide](https://fgmnnursery.com/blogs/predatory-mite-matters/cryptolaemus-montrouzieri-the-mealybug-destroyer-guide) — Mealybug Destroyer gegen Schmierläuse (4–8 Wochen Etablierung)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
