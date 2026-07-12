# Zamioculcas — Zamioculcas zamiifolia

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [New York Botanical Garden](https://libguides.nybg.org/ZZPlant), [Gardening Know How](https://www.gardeningknowhow.com/houseplants/zz-plant/caring-for-zz-plant.htm), [Garden Design ZZ Plant](https://www.gardendesign.com/houseplants/zz-plant.html), [ASPCA](https://www.aspca.org/), [Joy Us Garden](https://www.joyusgarden.com/zz-plant-care-tips/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Zamioculcas zamiifolia | `species.scientific_name` |
| Volksnamen (DE/EN) | Zamioculcas, Glücksfeder, Eternityplant; ZZ Plant, Zanzibar Gem, Eternity Plant | `species.common_names` |
| Familie | Araceae | `species.family` → `botanical_families.name` |
| Gattung | Zamioculcas | `species.genus` |
| Ordnung | Alismatales | `botanical_families.order` |
| Wuchsform | succulent | `species.growth_habit` | <!-- A4 (#453 WP-10): CAM-Sukkulente mit sukkulenten Rhizomen/Knollen, war zuvor `herb` -->
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | cam (fakultatives, schwaches CAM — bei Trockenstress hochreguliert) | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 10 (wärmeliebende tropische Art; Wachstumsstillstand und Kälteschäden unterhalb ~10 °C / 50 °F) | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wurzeltyp | rhizomatous | `species.root_type` |
| Wurzelanpassungen | tuberous (sukkulente Rhizome/Knollen als Wasserspeicher) | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (h) | — (tagneutral, kein Kurz-/Langtagblüher → kein Stundenwert) <!-- DATEN FEHLEN: nicht zutreffend, photoperiod_type=day_neutral --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 8°C, optimal 18–26°C. Toleriert kurzzeitig 8°C ohne dauerhafte Schäden. | `species.hardiness_detail` |
| Heimat | Ostafrika (Tansania, Kenia, Malawi — trockene Regenwälder und Buschsavannen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Entfernte Schadstoffe | xylene, toluene, benzene | `species.removes_compounds` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Zamioculcas ist monotypisch — die einzige Art in ihrer Gattung. Die sukkulenten Rhizome (Knollen) dienen als Wasser- und Nährstoffspeicher, weshalb die Pflanze extreme Trockenheit übersteht. Zu den genügsamsten Zimmerpflanzen überhaupt — ideal für Menschen, die ihre Pflanzen regelmäßig vergessen zu gießen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Blüte Indoor extrem selten, bei reifen Pflanzen möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem, cutting_leaf | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis Vermehrung:** (1) Teilung beim Umtopfen — schnellste Methode. (2) Stängelstecklinge in Wasser oder Substrat — Bewurzelung 2–3 Monate. (3) Einzelblattstecklinge — dauert am längsten (4–6 Monate bis zur Knollenbildung), bilden zuverlässig neue Knollen. Alle Methoden erfolgreich, aber Geduld erforderlich — Zamioculcas wächst generell langsam.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems, roots | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_crystals | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Calciumoxalat-Kristalle bei Hautkontakt reizend — Handschuhe beim Umtopfen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt notwendig. Vergilbte oder beschädigte Triebe können an der Basis entfernt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 45–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (nur frostfreie Monate, kein Regen/Staunässe) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus-/Sukkulentenerde oder stark durchlässige Einheitserde (50% Erde + 50% Perlite/Grobsand). Guter Wasserabzug essentiell. Rhizome nicht vollständig mit Erde bedecken. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | — <!-- DATEN FEHLEN: kein peer-reviewter PPFD-LCP-Messwert für Z. zamiifolia auffindbar; als ausgesprochene Schwachlichtpflanze sehr niedrig --> | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | — <!-- DATEN FEHLEN --> | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz | partial_shade (natürlich unter Kronendach/Buschsavanne, dappled indirect light; verträgt Halbschatten) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | — <!-- DATEN FEHLEN: keine belegte Messung; flach wurzelndes Rhizomsystem, Wurzeltiefe topfabhängig --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz | sensitive (Rhizome faulen rasch bei Sauerstoffmangel; sehr durchlässiges Substrat zwingend) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse | sensitive (geringe Salztoleranz; Salzanreicherung aus Dünger/Hartwasser führt zu Blattrandnekrosen) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (dS/m, Substrat-ECe) | — <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-a-Wert; qualitativ <2 dS/m passend zur Klasse sensitive --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | — <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-b-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe (Wachstumsstillstand) | 120–150 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 30–50 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 30–55 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (CAM-Sukkulente; toleriert hohe Sättigungsdefizite via Wasserspeicher-Rhizome) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 24–27 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 (natürlicher Unterwuchs/Halbschatten, R:FR abgesenkt; FR(700–750nm)/(R(600–700nm)+FR)) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 30–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 2–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–45 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–45 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 2.4 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität | low (CAM-Sukkulente; in Ruhephase besonders trockenheitstolerant) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.55–0.65 (Unterwuchs/Halbschatten) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Aktives Wachstum | 1:1:1 | 0.4–0.8 | 6.0–7.0 | 60 | 20 | <!-- DATEN FEHLEN: kein artspezifischer Messwert --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> | <!-- DATEN FEHLEN --> |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 2 ml/L (halbe Dosis) | Wachstum |
| Zimmerpflanzen-Dünger (verdünnt) | Substral | base | 7-3-7 | 3 ml/L (1/3 Dosis) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |
| Hornspäne fein | Oscorna | organisch | 2 g/L Substrat | Frühling |

### 3.2 Besondere Hinweise

Zamioculcas ist ein extremer Schwachzehrer. Überdüngung schadet mehr als Unterdüngung. Maximal 3–4 Düngergaben pro Jahr. Niemals im Winter düngen. Bei verlangsamtem Wachstum (normal!) keine Düngersteigerung — Geduld ist gefragt.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | succulent | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; Staunässe unbedingt vermeiden | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Gießen reaktivieren | Erste Wassergabe nach trockenen Wintermonaten | mittel |
| Apr | Düngung starten | Erste schwache Düngergabe | niedrig |
| Apr–Sep | Wässern | Substrat vollständig austrocknen lassen vor dem nächsten Gießen | hoch |
| Sep | Düngung beenden | Letzte Düngergabe des Jahres | niedrig |
| Okt–Feb | Sehr sparsammes Gießen | Rhizome speichern Wasser — 1x gießen pro Monat reicht | hoch |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free (nicht frosthart; muss frostfrei im Haus überwintern) | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | Okt (vor erstem Frost / unter 12–15 °C hereinholen) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | Mai/Jun (nach den Eisheiligen, ab stabil >15 °C; langsam an Sonne gewöhnen) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | 15–22 (Minimum 8 °C, optimal 18 °C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | hell bis halbschattig; auch bei wenig Licht überwinterbar | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | sehr sparsam, ca. 1× pro Monat; Substrat fast abtrocknen lassen | `overwintering_profiles.winter_quarter_watering` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Blattvergilbung | leaf | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | leaf, stem | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Rhizomfäule | fungal (Pythium, Phytophthora) | Gelbe Triebe, weiche Knollen, fauler Geruch | Überbewässerung, Staunässe |
| Blattflecken | bacterial/fungal | Braune, nasse Flecken | Wasser auf Blättern + Wärme |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Systeminsektizid | chemical | Stäbchen ins Substrat | 14 Tage | Schmierläuse |
| Umtopfen | cultural | Befallene Knollen auf Fäule prüfen, abfaulige Teile entfernen | 0 | Rhizomfäule |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 2–50 Tiere/m², 1–2× wöchentlich wiederholen | 1–3 Wochen (wirksam 13–27 °C) |
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierläuse (Pseudococcus spp.) | ca. 5–10 Tiere/m² (0,5–1/sq.ft), 2–3 Teilfreilassungen | 4–8 Wochen |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Bogenhanf | Dracaena trifasciata | 0.9 | Identische Pflegeanforderungen |
| Aloe vera | Aloe vera | 0.9 | Gleiche Substrat- und Gießanforderungen |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Zamioculcas zamiifolia |
|-----|-------------------|-------------|------------------------------------------|
| Raven ZZ | Zamioculcas zamiifolia 'Raven' | Sorte mit fast schwarzen Blättern | Dramatische dunkle Blattfarbe |
| Bogenhanf | Dracaena trifasciata | Ähnliche Robustheit, anders geformt | Aufrechter Wuchs, sehr ähnliche Pflegeanforderungen |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Zamioculcas zamiifolia,"Zamioculcas;Glücksfeder;ZZ Plant;Zanzibar Gem",Araceae,Zamioculcas,perennial,day_neutral,succulent,rhizomatous,"9b;10a;10b;11a;11b",0.0,"Ostafrika (Tansania, Kenia)",yes,3-15,20,45-90,30-60,yes,limited,false,false,light_feeder
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Raven,Zamioculcas zamiifolia,"ornamental;black_leaves",clone
Zenzi,Zamioculcas zamiifolia,"ornamental;compact;curled_leaflets",clone
```

---

## Quellenverzeichnis

1. [New York Botanical Garden — ZZ Plant Guide](https://libguides.nybg.org/ZZPlant) — Botanische Hintergründe
2. [Gardening Know How — ZZ Plant](https://www.gardeningknowhow.com/houseplants/zz-plant/caring-for-zz-plant.htm) — Pflegehinweise
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Garden Design — ZZ Plant](https://www.gardendesign.com/houseplants/zz-plant.html) — Kulturdaten
5. [Patch Plants](https://www.patchplants.com/pages/plant-care/complete-guide-to-zamioculcas-zamiifolia-plant-care/) — Erfahrungswerte Pflege
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [Holtum & Winter (2007): Crassulacean acid metabolism in the ZZ plant, Zamioculcas zamiifolia (Araceae), American Journal of Botany 94(10):1670–1676](https://bsapubs.onlinelibrary.wiley.com/doi/pdf/10.3732/ajb.94.10.1670) — peer-reviewter Nachweis des CAM-Photosynthese-Typs (Photosynthese-Typ)
7. [Winter et al. (2014): Facultative crassulacean acid metabolism (CAM) plants, Journal of Experimental Botany 65(13):3425](https://academic.oup.com/jxb/article/65/13/3425/2877513) — fakultatives CAM bei Wasserstress (Bestätigung Photosynthese-Typ, VPD-Sensitivität)
8. [UF/IFAS Extension EP480: Florida Foliage House Plant Care: ZZ Plant](https://ask.ifas.ufl.edu/publication/EP480) — Temperatur-/Standortdaten (base_temp, Überwinterung)
9. [NC State Extension Gardener Plant Toolbox — Zamioculcas zamiifolia](https://plants.ces.ncsu.edu/plants/zamioculcas-zamiifolia/) — Standort, pH, Schatten-/Wärmetoleranz (shade_tolerance, soil_ph_preference)
10. [Iowa State University Extension — Using Growing Degree Days](https://yardandgarden.extension.iastate.edu/how-to/using-growing-degree-days-manage-home-garden) — GDD-Basistemperatur warm-season 10 °C (base_temp)
11. [Wikipedia — Growing degree-day](https://en.wikipedia.org/wiki/Growing_degree-day) — GDD-Basistemperatur-Konventionen (base_temp)
12. [Healthy Houseplants — ZZ Plant Care Guide](https://www.healthyhouseplants.com/indoor-houseplants/zz-plant-care-guide-growing-tips-for-the-zamioculcas-zamiifolia/) — geringe Salztoleranz, Salzanreicherung (salt_tolerance_class)
13. [Joy Us Garden — ZZ Plant Care](https://www.joyusgarden.com/zz-plant-care-tips/) — Salzanreicherung/Spülen, Staunässe (salt_tolerance_class, waterlogging_tolerance)
14. [Koppert — Phytoseiulus persimilis (Spidex)](https://www.koppert.com/spidex/) — Ausbringrate Raubmilbe (Nützlinge)
15. [Cornell NYSIPM — Phytoseiulus persimilis Biocontrol Fact Sheet](https://cals.cornell.edu/integrated-pest-management/outreach-education/fact-sheets/phytoseiulus-persimilis-predatory-mite) — Ausbringrate/Wirkbereich Raubmilbe (Nützlinge)
16. [Sound Horticulture — Cryptolaemus montrouzieri Tech Sheet](https://soundhorticulture.com/pages/cryptolaemus-montrouzieri) — Ausbringrate/Etablierungszeit Mealybug Destroyer (Nützlinge)
17. [Evergreen Growers — Mealybug Destroyer Cryptolaemus montrouzieri](https://www.evergreengrowers.com/mealybug-destroyer-cryptolaemus-montrouzieri-group-cryp.html) — Ausbringrate Mealybug Destroyer (Nützlinge)
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
