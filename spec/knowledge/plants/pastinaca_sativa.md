# Pastinake — Pastinaca sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Pastinaken, Samen.de Pastinaken, Kraut&Rüben Pastinaken, LandBZL Pastinaken

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pastinaca sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Pastinake, Hammermöhre (Norddeutschland), Hirschmöhre; Parsnip | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Pastinaca | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | biennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photoperiode | day_neutral (Blüte ist vernalisationsgesteuert, nicht photoperiodisch — bei eng verwandter Möhre konditioniert die Tageslänge nach Vernalisation die Blüte nachweislich NICHT; im Anbau wird ohnehin im 1. Jahr vor jeder Blüte geerntet) | `lifecycle_configs.photoperiod_type` |
| Photosynthese-Typ (photosynthesis pathway) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur Hauptwuchs (base temp, °C) | 4–6 (Kühlsaison-Apiaceae; Tbase der Möhre als Familien-Proxy 4–6 °C; kein Keimwert) | `species.base_temp` |
| Dormanz erforderlich (dormancy required) | false (Wurzel überdauert im Boden ohne erzwungene Dormanzphase; ganzjährig erntbar) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | true | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (min days) | 14 (2–12 Wochen Kälte bei ~2–9 °C im 2. Jahr lösen Schossen/Blüte aus; juvenile Mindestgröße zusätzlich nötig) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN: kein echter Kurz-/Langtagblüher; Blüte vernalisationsgesteuert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 4a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Sehr winterhart bis -15°C; Wurzeln im Boden überwintern problemlos; Frost verbessert Aroma (Stärke → Zucker); ideal für Norddeutschland; ganzjährige Ernte möglich | `species.hardiness_detail` |
| Heimat | Eurasien, Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (keine Vorkultur — Pfahlwurzel verträgt Verpflanzen nicht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -28 (Frühaussaat ab Februar/März möglich; langsamste Keimung aller Gemüse) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 2, 3, 4, 5, 6 | `species.direct_sow_months` |
| Erntemonate | 10, 11, 12, 1, 2, 3 (nach erstem Frost am süßesten; ganzjährig im Boden lassen) | `species.harvest_months` |
| Blütemonate | 6, 7 (2. Jahr; dann absterbend) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Blätter und Stängel bei Sonnenkontakt (phototoxisch) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Furanocumarine (phototoxisch; Hautrötung/-blasen bei Sonnenkontakt nach Kontakt mit Blättern) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Phototoxizität bei Sonnenkontakt — Handschuhe beim Ernten tragen!) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Apiaceae-Kreuzallergie) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 10–15 in der Reihe; Reihenabstand 25–30 cm | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (ausschließlich Freilandkultur; tiefe Pfahlwurzel braucht lockeren, tiefen Boden) | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (LCP, PPFD µmol/m²/s) | 10 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (LCP, PPFD µmol/m²/s) | 40 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun (volle Sonne für optimale Wurzelbildung; leichter Halbschatten am Nachmittag wird toleriert, starker Schatten mindert Wurzelgröße/Ertrag) | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive (anhaltende Staunässe → Wurzelfäule; gute Drainage essenziell) | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | sensitive (FAO-Einstufung; Apiaceae-Familie durchgängig salzempfindlich) | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: Pastinake nur qualitativ "sensitive" gelistet, keine eigenen Maas-Hoffman-Zahlen; Familien-Proxy Möhre = 1.0 dS/m, aber nicht art-spezifisch belegt --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein art-spezifischer Maas-Hoffman-Slope für Pastinake belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 6.0–7.5 (harmonisiert mit §2.3 pH 6.0–7.0 und §1.6; RHS/PFAF/Extension nennen 6.0–7.5, Optimum 6.5–7.0) | `species.soil_ph_preference` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–28 | 1 | false | false | low |
| Sämling | 21–42 | 2 | false | false | medium |
| Vegetativ (Wurzelaufbau) | 90–130 | 3 | false | false | high |
| Reife | 30–90 | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wurzelaufbau)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 14–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kritischer Wert, kPa) | 1.4 (deutlich oberhalb des Zielkorridors; stomatärer Kollaps-Punkt = oberer Zielwert 1.0 + ~0.4) | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (sensitivity) | medium (C3-Kühlsaison-Wurzelgemüse) | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 (Kühlsaison-Apiaceae; oberhalb 24 °C sinkt Netto-Assimilation) | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 (Freiland-Vollsonne; offenes Tageslicht ≈ 0.5, R:FR ≈ 1.1) | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–14 (trockenverträglich nach Keimung) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
| Keimung | 0:0:0 | 0.0 | 6.0–7.0 | — | — | — | — | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.6 | 6.0–7.0 | 60 | 25 | — | 2 | 0.5 | 0.25 | 0.05 | 0.05 |
| Vegetativ | 1:1:2 | 0.8–1.2 | 6.0–7.0 | 100 | 40 | — | 2 | 0.5 | 0.25 | 0.05 | 0.05 |
| Reife | 0:1:2 | 0.6–0.8 | 6.0–7.0 | 80 | 30 | — | 1 | 0.5 | 0.25 | 0.05 | 0.05 |
<!-- Mikronährstoffe Mn/Zn/Cu/Mo ergänzt. Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- nutrient_profiles.manganese/zinc/copper/molybdenum_ppm -->
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Keimung 0:0:0 ohne Mikronährstoffgabe (reines Quellwasser). -->


---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Reifer Kompost | eigen | organisch | 4–6 L/m² | Herbst vor Aussaatjahr | Wurzelgemüse |
| Horngrieß | Oscorna | organisch-N | 50–70 g/m² | Frühjahr | medium_feeder |

### 3.2 Besondere Hinweise zur Düngung

KEIN frischer Mist oder frischer Kompost — lockt Möhrenfliege an! Pastinaken brauchen lockeren, tief gegrabenen, steinfreien Boden für geradlinige Wurzeln. Auf humusreichem Boden, der im Vorjahr mit Kompost gedüngt wurde, ist meist keine weitere Düngung nötig. Stickstoff-Überschuss → üppiges Laub, kleine Wurzeln.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 (im Boden; natürliche Feuchtigkeit reicht) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßig; Trockenheit verholzt Wurzeln; Staunässe verrottet sie | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — (keine Saison-Düngung; Grundvorbereitung reicht) | `care_profiles.fertilizing_interval_days` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Nov (Vorjahr) | Kompostgabe | Reifen Kompost einarbeiten; tief lockern | mittel |
| Feb–Mär | Frühjahrsaussaat | Wenn Boden bearbeitbar; dünn säen; Keimung dauert 2–4 Wochen | hoch |
| Apr–Mai | Vereinzeln | Auf 10–15 cm ausdünnen (verdrängtes Kraut weggärtnern) | mittel |
| Apr | Insektennetz | Gegen Möhrenfliege; bei Befallsgefahr | hoch |
| Jul–Sep | Jäten | Unkraut; Pastinake ist langsam zu Beginn | niedrig |
| Okt–Mär | Ernte | Nach erstem Frost am süßesten; nach Bedarf ernten | hoch |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

Pastinaken sind sehr winterhart (frosthart bis ca. -15 °C); die Wurzeln überwintern problemlos im Freilandboden und werden durch Frost süßer (Stärke → Zucker). Eine Einlagerung ist nicht nötig — geerntet wird laufend „aus dem Beet". Im 2. Jahr nicht geerntete Wurzeln schossen im Frühjahr und werden holzig/ungenießbar; daher spätestens vor dem Austrieb räumen.

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | mulch (Stroh-/Laubmulch erleichtert die Ernte bei gefrorenem Boden und markiert die Reihen) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 11 (November) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | uncover (Mulch abräumen; verbliebene Wurzeln vor dem Schossen ernten) | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 3 (März) | `overwintering_profiles.spring_action_month` |
| Winterquartier Temperatur (°C) | — (verbleibt im Freilandboden; kein frostfreies Quartier nötig) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier Licht | — (Freiland) | `overwintering_profiles.winter_quarter_light` |
| Winterquartier Gießen | — (natürliche Bodenfeuchte genügt; nicht zusätzlich gießen) | `overwintering_profiles.winter_quarter_watering` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Möhrenfliege | Psila rosae | Fraßgänge in der Wurzel; brauner Mulm | root | vegetative, ripening | difficult |
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen | shoot | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Möhrenschwärze | fungal (Alternaria dauci) | Dunkle Blattflecken | Feuchtigkeit | 7–14 | vegetative |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 5–10 | vegetative, ripening |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Kulturschutznetz | cultural | — | 0,8 mm Maschenweite; ab Keimung | 0 | Möhrenfliege |
| Mischkultur Zwiebeln | cultural | — | Zwiebelduft verwirrt Möhrenfliege | 0 | Möhrenfliege |
| Fruchtwechsel | cultural | — | Keine Apiaceae auf gleicher Fläche | 0 | alle Krankheiten |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit | KA-Edge |
|----------|--------------------|-----------------|--------------|------------------|---------|
| Insektenpathogene Nematoden | Steinernema feltiae | Möhrenfliege (Psila rosae) — Larven/Puppen im Boden | 250.000–500.000 /m² als Bodengießung | wenige Tage (Boden feucht halten; wirksam 14–26 °C) | `controlled_by` |
| Blattlaus-Schlupfwespe | Aphidius colemani | Blattläuse (Aphis spp.) | 0,25–4 /m² je Freilassung, 3× wiederholen | 2–4 Wochen (vorbeugend nach Aufgang starten) | `controlled_by` |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse (Aphis spp.) | 2–5 Puppen /m² | 2–4 Wochen | `controlled_by` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Doldenblütler (Apiaceae) |
| Empfohlene Vorfrucht | Leguminosen; Kohlgewächse (NICHT andere Apiaceae) |
| Empfohlene Nachfrucht | Starkzehrer (Kürbis, Kohl); kein Sellerie, Möhre, Fenchel |
| Anbaupause (Jahre) | 3–4 Jahre keine Apiaceae auf gleicher Fläche |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Zwiebel | Allium cepa | 0.9 | Möhrenfliegen-Abwehr durch Duft | `compatible_with` |
| Knoblauch | Allium sativum | 0.8 | Möhrenfliegen-Abwehr | `compatible_with` |
| Porree | Allium porrum | 0.8 | Möhrenfliegen-Abwehr | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Bodenbeschattung; Platzsparend | `compatible_with` |
| Radieschen | Raphanus sativus var. sativus | 0.7 | Bodenlockerer; schnell wachsend | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Möhre | Daucus carota | Geteilter Schädling (Möhrenfliege) | severe | `incompatible_with` |
| Petersilie | Petroselinum crispum | Gleiche Familie; Möhrenfliege | severe | `incompatible_with` |
| Sellerie | Apium graveolens | Gleiche Familie; Konkurrenz | severe | `incompatible_with` |
| Fenchel | Foeniculum vulgare | Allelopathie + geteilte Schädlinge | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Pastinake |
|-----|-------------------|-------------|------------------------------|
| Möhre | Daucus carota | Gleiche Familie; Wurzelgemüse | Schneller reif; vielseitiger |
| Sellerie | Apium graveolens | Gleiche Familie | Andere Verwendung; Stangensellerie |
| Petersilienwurzel | Petroselinum crispum var. tuberosum | Gleiche Familie | Intensiveres Aroma; kleiner |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Pastinaca sativa,"Pastinake;Hammermöhre;Parsnip",Apiaceae,Pastinaca,biennial,day_neutral,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.0,"Eurasien, Mittelmeer",no,no,no,false,false,medium_feeder,hardy,"2;3;4;5;6","10;11;12;1;2;3"
```

---

## Quellenverzeichnis

1. [Plantura Pastinaken](https://www.plantura.garden/gemuese/pastinaken/pastinaken-pflanzen) — Anbau, Mischkultur
2. [Samen.de Pastinaken](https://samen.de/blog/pastinaken-anbauen-vom-samen-zur-ernte.html) — Anbau, Pflege
3. [Kraut&Rüben Pastinaken](https://www.krautundrueben.de/steckbrief-pastinaken-saeen-pflegen-und-ernten-2547) — Steckbrief
4. [LandBZL Pastinaken](https://www.landwirtschaft.de/garten/selbst-anbauen/gemuesesteckbriefe/pastinaken-selbst-im-garten-anbauen) — Allgemein
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [RHS — Pastinaca sativa](https://www.rhs.org.uk/plants/24473/pastinaca-sativa/details) — Boden-pH 6.0–7.5, Standort volle Sonne/leichter Halbschatten
6. [PFAF — Pastinaca sativa](https://pfaf.org/user/plant.aspx?LatinName=Pastinaca+sativa) — Boden (leicht/mittel/schwer), gut drainiert, Halbschatten-Toleranz, pH-Vorzug
7. [SDSU Extension — Parsnips: How to Grow It](https://extension.sdstate.edu/parsnips-how-grow-it) — Vernalisation, Schossen im 2. Jahr, Kühlsaison-Charakter
8. [MSU Extension — Bolting in spring vegetables](https://www.canr.msu.edu/news/bolting-in-spring-vegetables) — Vernalisation Pastinake 2–12 Wochen bei ~2–9 °C, juvenile Mindestgröße
9. [MDPI Plants 2022 — Vernalization Requirement, but Not Post-Vernalization Day Length, Conditions Flowering in Carrot](https://www.mdpi.com/2223-7747/11/8/1075) — Apiaceae-Proxy: Blüte vernalisations-, nicht photoperiodengesteuert (Begründung day_neutral)
10. [ScienceDirect — Base and upper temperature thresholds for GDD (FAO56rev review)](https://www.sciencedirect.com/science/article/pii/S037837742500469X) — Möhren-Tbase 4–6 °C als Apiaceae-Familien-Proxy für base_temp
11. [FAO — Annex 1. Crop salt tolerance data](https://www.fao.org/4/y4263e/y4263e0e.htm) — Pastinake „sensitive" (geschätzt); Möhre ECe 1.0 dS/m, Slope 14 %
12. [USDA-ARS Shannon & Grieve — Tolerance of vegetable crops to salinity](https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P1567.pdf) — Apiaceae durchgängig salzempfindlich
13. [ScienceDirect Topics — Light Compensation](https://www.sciencedirect.com/topics/engineering/light-compensation) — LCP krautiger C3-Pflanzen 8–12 (Einzelblatt) bis 30–70 (Gesamtpflanze) µmol/m²/s
14. [PSU Extension — Hydroponics Systems: Nutrient Solution Programs and Recipes](https://extension.psu.edu/hydroponics-systems-nutrient-solution-programs-and-recipes) — Mikronährstoff-Richtbereiche Mn/Zn/Cu/Mo
15. [Koppert — Entonem (Steinernema feltiae)](https://www.koppert.com/entonem/) — Ausbringrate 250.000–500.000/m², Bodenfeuchte/Temperatur
16. [Warwick (Acta Hortic.) — Steinernema feltiae als Mittel gegen Psila rosae](https://www.actahort.org/books/1393/1393_15.htm) — Nematode gegen Möhrenfliege-Larven
17. [Koppert — Aphidius colemani](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Blattlaus-Schlupfwespe, Freilassungsraten
18. [Sound Horticulture — Aphid Tech Sheet](https://soundhorticulture.com/pages/aphids) — Aphidius/Aphidoletes Ausbringraten und Etablierung
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
