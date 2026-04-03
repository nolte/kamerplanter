# Garten-Verbene — Verbena × hybrida

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-28
> **Quellen:** Royal Horticultural Society, University of Florida IFAS Extension, USDA PLANTS Database, Ball Horticulture Verbena Production Guide, Bayerische Gartenakademie

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Verbena × hybrida | `species.scientific_name` |
| Volksnamen (DE/EN) | Garten-Verbene, Eisenkraut; Garden Verbena, Annual Verbena | `species.common_names` |
| Familie | Verbenaceae | `species.family` → `botanical_families.name` |
| Gattung | Verbena | `species.genus` |
| Ordnung | Lamiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a–11b (als Einjährige in 4a–11b) | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Frostempfindlich; stirbt bei Frost; in Mitteleuropa als einjährige Sommerblume; Überwinterung im frostfreien Quartier (5–10°C) möglich; Stecklinge überwintern besser als ganze Pflanzen | `species.hardiness_detail` |
| Heimat | Hybride südamerikanischer Elternarten (Argentinien, Uruguay, Brasilien) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hybridcharakter:** Verbena × hybrida ist eine Gartenhybride aus mehreren südamerikanischen Wildarten (v.a. Verbena peruviana, V. incisa, V. phlogiflora). Alle modernen Balkon- und Beetverbenen gehören zu dieser Hybridgruppe. Die Art ist steril oder schwach fertil — Vermehrung meist vegetativ.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–14 (lange Anzuchtzeit; früh starten!) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (Direktsaat möglich aber unüblich; lieber Stecklinge kaufen) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 2, 3 (im Warmhaus ab Februar) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; kontinuierlich blühend) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (nach dem Frost bis Herbst) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Stecklingsvermehrung:** Triebspitzenstecklinge (5–8 cm) im August/September nehmen; in Stecksubstrat; bei 18–22°C; wurzeln in 3–4 Wochen. Überwinterung als Stecklinge einfacher als ganze Pflanze.

**Saatgut-Hinweis:** Dunkelkeimer-Tendenz (Keimung verbessert sich bei Lichtausschluss, aber nicht obligat — Keimung auch ohne Abdeckung moeglich). Kuehle Stratifikation (5°C fuer 1–2 Wochen) verbessert Keimrate. Keimung unregelmaessig; Geduld noetig.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | — (geringe Toxizität; bei großer Aufnahme Magenbeschwerden möglich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Iridoid-Glykoside (geringe Mengen) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | summer_pruning (Rückschnitt fördert Neuaustrieb und Blüte) | `species.pruning_type` |
| Rückschnitt-Monate | 6, 7, 8 (nach Blütenanfall um 1/3 zurückschneiden) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–45 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 (hängend bis 80 cm) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–35 | `species.spacing_cm` |
| Indoor-Anbau | limited (sehr lichtbedürftig; Fensterbrett nur Süd/West) | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false (außer Anzucht) | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false (hängende/kriechende Wuchsform; selbstdeckend) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Balkonblumenerde; pH 5,8–6,5; leicht sauer; Perlite-Anteil 20% für bessere Drainage | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–28 | 1 | false | false | low |
| Sämling / Anzucht | 21–42 | 2 | false | false | low |
| Vegetativ / Abhaertung | 14–28 | 3 | false | false | medium |
| Hauptblüte | 60–120 | 4 | false | false | medium |
| Herbstblüte (nach Rückschnitt) | 30–60 | 5 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Keimung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 0–50 (Dunkelkeimer; Licht hemmt Keimung!) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | — | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 20–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 18–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 75–90 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.2–0.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2 (gleichmäßig feucht; nicht nass) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | — (Substrat feucht halten) | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sämling / Anzucht

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–15 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–75 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–0.9 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–3 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Hauptblüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–35 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 (tagneutral; Licht fördert Blüte quantitativ) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 1–2 (Balkon: täglich im Sommer; Trockenheit schadet Blüte) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Keimung | 0:0:0 | 0.0 | 5.8–6.5 | — | — |
| Sämling | 1:1:1 | 0.4–0.8 | 5.8–6.5 | 50 | 20 |
| Vegetativ | 2:1:2 | 0.8–1.4 | 5.8–6.5 | 80 | 30 |
| Hauptblüte | 1:2:2 | 1.0–1.8 | 5.8–6.5 | 80 | 35 |
| Herbstblüte | 1:2:2 | 0.8–1.4 | 5.8–6.5 | 60 | 25 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor/Balkon/Gewächshaus)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Flüssig-Balkonblumendünger | Compo/Substral | Flüssig | 8-8-6 | 0.20 | 3 | Blüte |
| Blaudünger / Osmocote | Osmocote | Slow-Release | 15-9-12 | je Depot | 1 | alle |
| Fertilizer für Blühpflanzen | Canna Bio Boost | Flüssig | 2-1-3 | 0.15 | 4 | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee | eigen | flüssig organisch | 1:10 verdünnt; 2×/Woche | Jun–Sep |
| Hornmehl | diverse | organisch | 5 g/L Substrat | Substrat-Mix |

### 3.2 Mischungsreihenfolge

1. Stammlösung Blütendünger
2. CalMag (falls Kalkwasser)
3. Weitere Additive
4. pH-Korrektur zuletzt

### 3.3 Besondere Hinweise zur Düngung

Verbene ist nicht anspruchsvoll, aber kontinuierliches Blühen braucht regelmäßige Nährstoffzufuhr. Kalium fördert Blütenbildung. Slow-Release-Dünger im Substrat praktisch für Balkon. KEIN übermäßiges Stickstoff (üppiges Blattwerk statt Blüten). Bei vergilbenden Blättern: Eisenmangel prüfen (pH zu hoch). Abblühende Köpfchen regelmäßig entfernen (Deadheading) verlängert Blütezeit erheblich.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 1–2 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.3 (Überwinterungspflanze; minimal gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkreiches Wasser kann Chlorosen verursachen; pH prüfen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7–10 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (einjährig; kein Umtopfen nötig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Saatgut | Im Warmhaus bei 20–25°C; Dunkelkeimer; Folie drüber | hoch |
| Mär–Apr | Pikierung | Wenn 2. Blattpaar erscheint; in 9-cm-Töpfe | hoch |
| Mai | Abhärtung | 1–2 Wochen langsam ans Freie gewöhnen | hoch |
| Mai–Jun | Auspflanzung | Nach letztem Frost; vollsonniger Standort | hoch |
| Jun–Aug | Deadheading | Verblühte Blütenköpfe abzwicken; fördert Nachblüte | mittel |
| Jul–Aug | Rückschnitt | Um 1/3 kürzen wenn Blüte nachlässt; fördert Neuaustrieb | mittel |
| Aug | Stecklinge | Triebspitzenstecklinge für Überwinterung | niedrig |
| Sep–Okt | Winterquartier | Stecklinge oder Mutterpflanzen ins Haus (5–10°C; hell) | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen |
|-----------|-------------------|----------|------------------|------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste; Gelbflecken; bronzefarbene Blätter | Blatt | Blüte (trocken-warm) |
| Weiße Fliege | Trialeurodes vaporariorum | Honigtau; Rußtau; fliegende Wolke | Blatt | alle (Gewächshaus) |
| Blattläuse | Myzus persicae | Kolonien; Vergilbung; Deformation | Trieb | Sämling, Frühblüte |
| Thripse | Frankliniella occidentalis | Silber-weiße Flecken; Blütendeformation | Blatt, Blüte | Hauptblüte |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal (Erysiphe spp.) | Weißgrauer Belag auf Blättern | trocken-warm; dichte Bestände |
| Grauschimmel | fungal (Botrytis cinerea) | Grauer Pilzrasen auf Blüten/Blättern | kühl-feucht; schlechte Luftzirkulation |
| Peronospora (Falscher Mehltau) | fungal (Peronospora sparsa) | Gelbliche Flecken oben; grauviolett unten | kühl-feucht |
| Verbena-Mosaik | viral | Mosaikflecken; Deformation | Blattlausübertragung |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 5–10 | 14–21 |
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Aphidius colemani | Blattläuse | 3–5 | 14 |
| Amblyseius cucumeris | Thripse | 25–50 | 10–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0,5% | 3 | Spinnmilben, Thripse, Blattläuse |
| Schwefelkalk | chemical | Schwefelkalk | Sprühen | 14 | Echter Mehltau |
| Backpulver-Lösung | cultural | NaHCO₃ | Sprühen 1% | 0 | Echter Mehltau (präventiv) |
| Pyrethrin | biological | Pyrethrine | Sprühen | 3 | Blattläuse, Weiße Fliege |
| Befallene Teile entfernen | cultural | — | Sofort | 0 | Grauschimmel, Mehltau |
| Luftzirkulation verbessern | cultural | — | Pflanzabstand | 0 | Mehltau, Grauschimmel |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zierpflanze; Balkon/Beet-Annuelle |
| Empfohlene Vorfrucht | — (Einjährige Zierpflanze; keine klassische Fruchtfolge) |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | 2–3 Jahre Pause auf gleicher Beetfläche (Botrytis) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tagetes | Tagetes patula/erecta | 0.9 | Bestäuber-Anlockung; Nematoden-Abwehr; Farbkontrast | `compatible_with` |
| Geranien | Pelargonium × hortorum | 0.8 | Ästhetisch; gleiche Pflegebedürfnisse | `compatible_with` |
| Petunie | Petunia × hybrida | 0.8 | Gleiche Standortansprüche; Bestäuberfreundlich | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bestäuber-Anlockung; Trockenheitstoleranz | `compatible_with` |
| Kapuzinerkresse | Tropaeolum majus | 0.7 | Bestäuber; essbar; Farbkontrast | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Allelopathische Hemmung vieler Pflanzen | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Verbena hybrida |
|-----|-------------------|-------------|-----------------------------------|
| Echte Eisenkraut | Verbena officinalis | Gleiche Gattung; mehrjährig | Winterharter; Heilpflanze; weniger Schaueffekt |
| Lila Eisenkraut | Verbena rigida | Gleiche Gattung | Kompakter; Freiland in milden Regionen |
| Landverbene | Glandularia × hybrida | Nah verwandte Gattung | Sehr hängend; Ampelfüllung |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,harvest_months,bloom_months
Verbena × hybrida,"Garten-Verbene;Eisenkraut;Garden Verbena;Annual Verbena",Verbenaceae,Verbena,annual,day_neutral,herb,fibrous,"8a;8b;9a;9b;10a;10b;11a;11b",0.0,"Südamerika (Hybride)",yes,limited,yes,false,false,medium_feeder,false,tender,"2;3","","5;6;7;8;9;10"
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,days_to_maturity,seed_type
Lanai Red,Verbena × hybrida,"trailing;red;heat_tolerant;powdery_mildew_resistant",75,hybrid
Aztec Pink Magic,Verbena × hybrida,"compact;fragrant;multicolor;heat_tolerant",80,hybrid
Superbena Coral Red,Verbena × hybrida,"trailing;large_flower;vegetative;heat_tolerant",70,vegetative_only
```

---

## Quellenverzeichnis

1. [Royal Horticultural Society — Verbenas](https://www.rhs.org.uk/plants/verbena) — Gartenpraxis
2. [University of Florida IFAS — Verbena Production](https://edis.ifas.ufl.edu) — Gewächshauskultur
3. [Ball Horticulture Verbena Growing Guide](https://www.ballhort.com) — Produktionsanleitung
4. [USDA PLANTS — Verbena](https://plants.usda.gov) — Taxonomie
5. [Bayerische Gartenakademie — Balkonpflanzen](https://www.lwg.bayern.de/gartenakademie) — Balkon-Praxis
