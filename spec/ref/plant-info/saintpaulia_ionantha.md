# Usambaraveilchen — Streptocarpus ionanthus (syn. Saintpaulia ionantha)

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smithsonian Gardens](https://gardens.si.edu/learn/educational-resources/plant-care-sheets/care-of-african-violets/), [UF/IFAS Extension](https://edis.ifas.ufl.edu/publication/EP360), [Clemson Extension IPM](https://hgic.clemson.edu/factsheet/african-violet-diseases-insect-pests/), [Cornell Greenhouse Horticulture](https://greenhouse.cornell.edu/pests-diseases/diseases-of-specific-crops/african-violet-saintpaulia-ionantha/), [African Violet Society of America](https://africanvioletsocietyofamerica.org/learn/violets-101/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Streptocarpus ionanthus | `species.scientific_name` |
| Synonyme | Saintpaulia ionantha (Handelsname, taxonomisch veraltet seit Nishii et al. 2015) | — |
| Volksnamen (DE/EN) | Afrikanisches Veilchen, Usambaraveilchen; African Violet | `species.common_names` |
| Familie | Gesneriaceae | `species.family` → `botanical_families.name` |
| Gattung | Streptocarpus | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 11a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 13°C; ausschließlich Zimmerpflanze | `species.hardiness_detail` |
| Heimat | Tansania, Kenia (Usambaragebirge, Ostafrika) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant (Zimmer) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | nicht relevant | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 (ganzjährig möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_leaf; seed; division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Blattschnittling-Methode:** Blatt mit 3–4 cm Blattstiel schräg abschneiden, in angefeuchtetes Substrat stecken (Perlit/Torf 1:1), bei 22–24°C und hoher Luftfeuchtigkeit (70–80%) bewurzeln. Jungpflanzen erscheinen nach 6–8 Wochen an der Stielbase. Blattschnittlinge sind die Standardmethode und gelingen sehr zuverlässig (Erfolgsrate >90%).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannten Giftstoffe | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Pflege-Hinweis:** Verblühte Blütenstiele regelmäßig abzwicken (Entfernen), absterbende Außenblätter entfernen. Keine eigentliche Schnittmaßnahme erforderlich. Bei zu langen Blattstielen (Hals) kann die Pflanze umgetopft und tiefer eingesetzt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–1.5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 8–20 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, nährstoffreiche Spezialerde (African Violet Mix): Torf/Perlit/Vermiculit 2:1:1; pH 6.0–6.5; guter Wasserabzug zwingend | — |

**Topfgröße-Regel:** Topfbreite = 1/3 der Blattspreizung der Pflanze. Zu große Töpfe führen zu Wurzelfäule und reduzierter Blütenbildung.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung | 42–56 | 1 | false | false | low |
| Jungpflanze | 56–84 | 2 | false | false | low |
| Vegetativ | 28–56 | 3 | false | false | medium |
| Blüte | 30–90 | 4 | false | true | medium |
| Ruhephase | 21–42 | 5 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Bewurzelung (Blattschnittling)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–100 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 22–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 20–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 70–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 70–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.7 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 (Substrat nie austrocknen, nie nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Jungpflanze

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 7–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–21 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–80 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–16 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–21 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 13–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 (mind. 8h Dunkelheit) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–8 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–100 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Ruhephase (nach intensiver Blüteperiode)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 7–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.1 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 30–70 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Bewurzelung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Jungpflanze | 2:1:1 | 0.5–0.8 | 6.0–6.5 | 60 | 30 | — | 2 |
| Vegetativ | 3:1:2 | 0.8–1.2 | 6.0–6.5 | 100 | 50 | — | 2 |
| Blüte | 1:2:2 | 0.8–1.2 | 6.0–6.5 | 100 | 50 | — | 2 |
| Ruhephase | 0:0:0 | 0.0–0.4 | 6.0–6.5 | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/Bedingungen |
|------------|---------|-----------------|
| Bewurzelung → Jungpflanze | time_based | 42–56 Tage; Jungpflanzen an Stielbase sichtbar |
| Jungpflanze → Vegetativ | manual | Umtopfen in eigenen 5–6 cm Topf |
| Vegetativ → Blüte | conditional | Photoperiode >14h; Temperatur stabil 20–24°C |
| Blüte → Ruhephase | event_based | Blüten verblüht, Rücklicht Herbst |
| Ruhephase → Vegetativ | time_based | 3–6 Wochen; im Frühjahr wieder Düngen beginnen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Spezialdünger)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| African Violet Food | Miracle-Gro | Spezialdünger | 8-14-9 | 1 ml/L | 1 | Blüte |
| Blumendünger flüssig | Compo | Universaldünger | 4-3-6 | 2 ml/L | 1 | Vegetativ, Blüte |
| Düngestäbchen für Blühpflanzen | COMPO | slow release | 8-12-16 | 1 Stäbchen/Monat | 1 | Vegetativ, Blüte |
| Liquid Fertilizer 20-20-20 | Peters Professional | Universaldünger | 20-20-20 | 0.5 g/L (verdünnt) | 1 | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Guano-Flüssigdünger | Guano Gold | organisch | 2 ml/L | Frühling–Herbst | Vegetativ |
| Komposttee (verdünnt) | eigen | organisch | 5 ml/L | Frühling–Sommer | alle |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Dünger (Dosierung) | Hinweise |
|-------|-------|---------|-----|---------------------|----------|
| 1–8 | Bewurzelung | 0.0 | 6.0–6.5 | kein Dünger | Nur Wasser, kein Dünger bis erste Jungpflanzen |
| 9–20 | Jungpflanze | 0.5–0.8 | 6.0–6.5 | 1/4 Normaldosis | Beginne mit 1/4 der empfohlenen Dosis |
| 21–28 | Vegetativ | 0.8–1.2 | 6.0–6.5 | 1/2 Normaldosis alle 14d | Wechsle zu ausgewogenem NPK |
| 29+ | Blüte | 0.8–1.2 | 6.0–6.5 | Blühdünger 14-tägig | Phosphorbetonter Dünger |
| Ruhephase | Ruhe | 0.0 | 6.0–6.5 | kein Dünger | Nov–Feb: Ruhepause, kein Düngen |

### 3.3 Mischungsreihenfolge

> **Wichtig:** Verdünnter Flüssigdünger immer mit der vollen Wassermenge anmischen.

1. Lauwarmem Wasser bereitstellen (ca. 25°C, kalkarm oder gefiltert)
2. Flüssigdünger in kleiner Menge Wasser vorverdünnen
3. In Gießkanne auffüllen
4. Vorsichtig von unten gießen (Untersetzer-Methode empfohlen)

### 3.4 Besondere Hinweise zur Düngung

**Niemals zu stark düngen:** EC über 1.5 mS/cm führt zu Blattrandverbrennung. Im Zweifelsfall lieber verdünnter. Für dauerhaft blühende Exemplare empfiehlt sich die "Wenig-aber-oft"-Methode: jede zweite Woche mit 1/4 Dosis des empfohlenen Düngers.

**Wasserqualität:** Kalkfreies oder weiches Wasser verwenden. Kalkhaltiges Leitungswasser erhöht den pH und führt zu Chlorose. Regenwasser oder gefiltertes Wasser ist ideal.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies, zimmerwarmes Wasser; Leitungswasser mindestens 24h stehen lassen; Wasser auf Blättern führt zu dauerhaften Flecken | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Ruhephase | Wenig Wasser, kein Dünger, Standort überprüfen (mind. 10h Licht) | niedrig |
| Feb | Blattschnittlinge vorbereiten | Gesunde Blätter als Schnittlinge abscheiden, Bewurzelungsphase starten | mittel |
| Mär | Düngen beginnen | Beginne mit 1/4 Dosis; Blühinduktion durch Lichterhöhung | hoch |
| Apr | Umtopfen | Jährliches Umtopfen in frische African-Violet-Erde; Topfgröße kontrollieren | hoch |
| Mai–Sep | Aktive Blüte | Regelmäßig düngen, abgestorbene Blüten entfernen, Seitentriebe (Ausläufer) entfernen | mittel |
| Okt | Düngen reduzieren | Dosis halbieren, Gießintervall verlängern | mittel |
| Nov–Feb | Ruhephase | Kein Dünger, reduziertes Gießen, Standort nicht ändern | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (Zimmerpflanze) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | — | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | none | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | — | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 15 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 20 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Wollläuse | Planococcus citri | Watteartige Wollknäuel, Honigtau, Wachstumsrückstand | stem, leaf, root | alle | easy |
| Zyklamen-Milbe | Phytonemus pallidus | Verkümmerte, gekräuselte Herzblätter, deformierte Blüten | leaf, flower | vegetative, flowering | difficult |
| Blattläuse | Aphidoidea | Klebrige Honigtauablagerungen, deformierte Blätter | leaf, stem | alle | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbliche Punkte, Blattverfärbung | leaf | vegetative | medium |
| Thripse | Thysanoptera | Silbrige Streifen auf Blüten, verformte Knospen | flower, leaf | flowering | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Wurzelfäule | fungal (Pythium, Phytophthora) | Welke, schwarze Basis, verrottete Wurzeln | Staunässe, zu kaltes Wasser | 5–14 | alle |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Schimmelbelag auf Blättern und Blüten | Hohe Luftfeuchtigkeit, schlechte Belüftung | 3–7 | flowering |
| Echter Mehltau | fungal (Oidium) | Weißer Mehlbelag auf Blättern | Trockene Luft, geringe Luftzirkulation | 5–10 | vegetative |
| Impatiens Necrotic Spot Virus | viral (INSV) | Braune Ringe, Nekrosen, Wachstumsstopp | Thripse als Überträger | 10–21 | alle |
| Blattfleckenkrankheit | fungal | Braune Flecken mit gelbem Rand | Wasser auf Blättern, kühle Temperaturen | 5–14 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Neoseiulus californicus | Zyklamen-Milbe, Spinnmilbe | 50–100 | 14–21 |
| Amblyseius cucumeris | Thripse | 50–100 | 14–21 |
| Aphidoletes aphidimyza | Blattläuse | 5–10 Gallmücken | 10–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | biological | Isopropylalkohol | Wattestäbchen auf Wollläuse | 0 | Wollläuse |
| Neemöl | biological | Azadirachtin | Sprühen 0.5%, alle 7 Tage, 3x | 3 | Blattläuse, Thripse |
| Spezial-Milbenmittel | chemical | Abamectin | Sprühen; 3 Behandlungen im 7-Tage-Abstand | 7 | Zyklamen-Milbe |
| Trennschicht Perlit | cultural | — | 1 cm Perlit auf Substrat verhindert Sciarid-Eier | 0 | Trauermücken |
| Gelbfallen | cultural | — | Klebefallen aufstellen | 0 | Thripse, Trauermücken |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Keine bekannten Resistenzen | — | — |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanzen (kein Freilandanbau) |
| Empfohlene Vorfrucht | nicht relevant |
| Empfohlene Nachfrucht | nicht relevant |
| Anbaupause (Jahre) | nicht relevant |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Fittonia | Fittonia albivenis | 0.7 | Ähnliche Feuchtigkeitsanforderungen, optische Ergänzung | `compatible_with` |
| Streptocarpus | Streptocarpus hybridus | 0.8 | Gleiche Familie (Gesneriaceae), identische Pflegebedingungen | `compatible_with` |
| Peperomia | Peperomia spp. | 0.7 | Ähnliche Licht- und Temperaturanforderungen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kakteen/Sukkulenten | diverse | Gegensätzliche Feuchtigkeitsanforderungen | moderate | `incompatible_with` |
| Orchideen (Phalaenopsis) | Phalaenopsis spp. | Phalaenopsis benötigt andere Substrate und Gießrhythmus | mild | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Saintpaulia ionantha |
|-----|-------------------|-------------|---------------------------------------|
| Kap-Primel | Streptocarpus hybridus | Gleiche Familie, ähnliche Blüten | Robuster, toleriert Trockenheit besser |
| Gloxinie | Sinningia speciosa | Gleiche Familie, ähnliche Pflege | Größere, spektakulärere Blüten |
| Episcia | Episcia cupreata | Gleiche Familie | Interessantes Blattmuster, kriechend |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Streptocarpus ionanthus,"Usambaraveilchen;Afrikanisches Veilchen;African Violet",Gesneriaceae,Streptocarpus,perennial,long_day,herb,fibrous,11a;11b;12a;12b,0.0,"Tansania, Kenia",yes,1,8,20,40,15,yes,no,false,false
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Optimara Little Maya,Streptocarpus ionanthus,miniature;compact;pink_flowers,90,–,cultivar
Rob's Sassy Kassy,Streptocarpus ionanthus,semi_miniature;chimera;pink_white_stripes,90,–,cultivar
Ness Golden Chalice,Streptocarpus ionanthus,standard;frilled;yellow_toned_white,90,–,cultivar
```

---

## Quellenverzeichnis

1. [Smithsonian Gardens — African Violet Care](https://gardens.si.edu/learn/educational-resources/plant-care-sheets/care-of-african-violets/) — Grundlegende Pflegehinweise
2. [UF/IFAS Extension EP360](https://edis.ifas.ufl.edu/publication/EP360) — Kommerzielle Produktionsrichtlinien inkl. EC/pH-Werte
3. [Clemson Extension — African Violet Diseases & Insect Pests](https://hgic.clemson.edu/factsheet/african-violet-diseases-insect-pests/) — IPM-Daten
4. [Cornell Greenhouse Horticulture](https://greenhouse.cornell.edu/pests-diseases/diseases-of-specific-crops/african-violet-saintpaulia-ionantha/) — Krankheitsbilder
5. [African Violet Society of America — Violets 101](https://africanvioletsocietyofamerica.org/learn/violets-101/) — Allgemeine Kulturhinweise
6. [UMN Extension — African Violets](https://extension.umn.edu/houseplants/african-violets) — Kulturhinweise für Haushalt
