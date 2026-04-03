# Knollenfenchel — Foeniculum vulgare var. azoricum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Plantura Fenchel, Samen.de Fenchel, Kraut&Rüben Fenchel, Bio-Gärtner Fenchel

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Foeniculum vulgare var. azoricum | `species.scientific_name` |
| Volksnamen (DE/EN) | Knollenfenchel, Gemüsefenchel, Fenchel; Florence Fennel, Finocchio | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Foeniculum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Verträgt leichte Fröste bis -5°C; Kälteexposition (Vernalisation) fördert Schossen bei nachfolgendem Langtag → schossfeste Sorten bei früher Aussaat wählen | `species.hardiness_detail` |
| Heimat | Mittelmeerraum | `species.native_habitat` |
| Allelopathie-Score | -0.5 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Wichtiger Hinweis:** Fenchel ist stark allelopathisch und hemmt viele Pflanzen durch Wurzelausscheidungen (v.a. Terpenoide). Im Mischkulturbeet immer am Rand platzieren oder im Einzelbeet.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat bevorzugt; Knollenfenchel verträgt Verpflanzen schlecht) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 14 (frühester Termin Mitte Mai; bei Frühaussaat Schießen-Gefahr) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 5, 6, 7 (ab Juni für beste Ergebnisse in Norddeutschland) | `species.direct_sow_months` |
| Erntemonate | 8, 9, 10 | `species.harvest_months` |
| Blütemonate | 7, 8, 9 (zweijährige Pflanze: Blüte erst im 2. Jahr; bei früher Aussaat schießt sie durch) | `species.bloom_months` |

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
| Giftige Pflanzenteile | — | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Estragol (in großen Mengen kanzerogen; normale Küchenmengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Apiaceae-Kreuzallergie möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzreaktion mit Birken- und Beifußpollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–20 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 40–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 25–30 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, lockere Gartenerde; pH 6,0–7,5; tief durchlässig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 7–14 | 1 | false | false | medium |
| Sämling | 14–21 | 2 | false | false | low |
| Knollenentwicklung | 42–70 | 3 | false | false | medium |
| Reife | 14–21 | 4 | true | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Knollenentwicklung

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 20–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 (Langtag fördert Schießen; Kurztagsarten für frühe Aussaat) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.7–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | — | — | — | — |
| Sämling | 1:1:1 | 0.4–0.6 | 6.0–6.5 | 80 | 30 | — | 2 |
| Knollenentwicklung | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 |
| Reife | 1:2:2 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 1 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Outdoor/Beet)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Reifer Kompost | eigen | organisch | 3–5 L/m² | Frühjahr, Einarbeitung | medium_feeder |
| Horngrieß | Oscorna | organisch-N | 50–80 g/m² | Pflanzung | medium_feeder |
| Gemüsedünger organisch | Neudorff Azet | organisch | 60–80 g/m² | Vegetativ | Gemüse allg. |

### 3.2 Besondere Hinweise zur Düngung

Fenchel braucht mäßige Nährstoffe — auf zu nährstoffreichen Böden bildet er viel Kraut und wenig Knolle. Kompost als Grundversorgung reicht meist. Kaliumbetonung in der Knollenphase fördert aromatische Inhaltsstoffe. Kein mineralischer Stickstoff-Überschuss.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | — (einjährig) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Gleichmäßige Feuchte; Trockenheit fördert Schießen; kein Wasser auf Knolle direkt | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 6, 7, 8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mai (ab 20.) | Direktsaat | Nach Eisheiligen; Reihenabstand 30 cm; 1–2 cm tief | hoch |
| Jun–Jul | Hauptaussaatzeit | Optimale Norddeutschland-Aussaat; schießfeste Sorten | hoch |
| Jun–Aug | Jäten + Vereinzeln | Auf 25–30 cm ausdünnen | mittel |
| Aug–Okt | Ernte | Bei Knollendurchmesser 8–10 cm; knapp über Boden abschneiden | hoch |
| Okt | Beetpflege | Reste kompostieren; kein Fenchel auf gleicher Fläche im Folgejahr | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Möhrenfliege | Psila rosae | Larvenfraß an Knollenbasis | root, bulb | knollenentwicklung | difficult |
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen | shoot, leaf | seedling, vegetative | easy |
| Schnecken | Arion spp. | Fraß an Jungpflanzen | leaf | seedling | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Trockenheit + Wärme | 5–10 | vegetative |
| Fenchelfäule | bacterial | Braune, weiche Knollenteile | Verletzungen, Nässe | 3–7 | bulb |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Schwebfliegen (Syrphidae) | Blattläuse | natürlich anlocken durch Blüten | — |
| Schlupfwespen | Blattläuse | natürlich vorhanden | — |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Feinmaschiges Netz | cultural | — | 0,9 mm Maschenweite ab Keimung | 0 | Möhrenfliege |
| Neemöl | biological | Azadirachtin | 0,5% Sprühlösung | 3 | Blattläuse |
| Schneckenkorn | chemical | Eisenphosphat | 5 g/m² | 0 | Schnecken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Doldenblütler (Apiaceae) |
| Empfohlene Vorfrucht | Leguminosen; Starkzehrer (Kohl) |
| Empfohlene Nachfrucht | Leguminosen, Zwiebelgewächse |
| Anbaupause (Jahre) | 2–3 Jahre; keine Apiaceae auf gleicher Fläche (Möhrenrost, Fenchelfäule) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Kopfsalat | Lactuca sativa | 0.6 | Toleriert Fenchel-Geruch; Bodenschutz | `compatible_with` |
| Gurke | Cucumis sativus | 0.5 | Toleriert Fenchel besser als andere Gemüse | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Tomate | Solanum lycopersicum | Starke Wachstumshemmung durch Terpene | severe | `incompatible_with` |
| Kohl | Brassica spp. | Allelopathische Hemmung | moderate | `incompatible_with` |
| Kartoffel | Solanum tuberosum | Fenchel hemmt Keimung | severe | `incompatible_with` |
| Bohne | Phaseolus vulgaris | Ertragsdepression | moderate | `incompatible_with` |
| Möhre | Daucus carota | Geteilter Schädling (Möhrenfliege) | moderate | `incompatible_with` |
| Erbse | Pisum sativum | Wachstumshemmung | moderate | `incompatible_with` |

**Praxistipp:** Fenchel möglichst in einem eigenen Beet oder am Beetrand anpflanzen — die Allelopathie-Wirkung ist ausgeprägter als bei den meisten anderen Gemüsekräutern.

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Apiaceae | `shares_pest_risk` | Möhrenfliege, Selleriefliege | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Fenchel |
|-----|-------------------|-------------|---------------------------|
| Gewürzfenchel | Foeniculum vulgare var. vulgare | Gleiche Art, andere var. | Winterhart; kein Knollenfenchel; Samen/Kraut |
| Sellerie | Apium graveolens | Gleiche Familie | Besser in Mischkultur verträglich |
| Pastinake | Pastinaca sativa | Gleiche Familie | Winterhart; leicht anders im Anbau |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,frost_sensitivity,direct_sow_months,harvest_months
Foeniculum vulgare var. azoricum,"Knollenfenchel;Gemüsefenchel;Florence Fennel;Finocchio",Apiaceae,Foeniculum,annual,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",-0.5,"Mittelmeerraum",limited,18,30,80,30,28,no,limited,false,false,medium_feeder,half_hardy,"5;6;7","8;9;10"
```

---

## Quellenverzeichnis

1. [Plantura Fenchel](https://www.plantura.garden/gemuese/fenchel/fenchel-anpflanzen) — Anbau, Aussaat, Mischkultur
2. [Samen.de Fenchel](https://samen.de/blog/fenchel-erfolgreich-anbauen-umfassender-leitfaden-von-der-aussaat-bis-zur-ernte.html) — Anbaupraxis, Norddeutschland
3. [Kraut&Rüben Knollenfenchel](https://www.krautundrueben.de/steckbrief-knollenfenchel) — Steckbrief, Sortenempfehlungen
4. [Bio-Gärtner Fenchel](https://www.bio-gaertner.de/Pflanzen/Fenchel) — Ökologischer Anbau
