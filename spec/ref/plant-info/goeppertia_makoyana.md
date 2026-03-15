# Pfauenpflanze (Korbmarante) — Goeppertia makoyana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NCSU Plant Toolbox](https://plants.ces.ncsu.edu/plants/goeppertia-makoyana/), [Smart Garden Guide](https://smartgardenguide.com/peacock-plant-care-calathea-makoyana/), [Gardenia.net](https://www.gardenia.net/plant/calathea-makoyana-peacock-plant), [Planet Natural](https://www.planetnatural.com/calathea-makoyana/), [Patch Plants](https://www.patchplants.com/pages/plant-care/complete-guide-to-calathea-care/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Goeppertia makoyana | `species.scientific_name` |
| Volksnamen (DE/EN) | Pfauenpflanze, Korbmarante; Peacock Plant, Cathedral Windows, Peacock Calathea | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Goeppertia | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–24°C. Zugluft und Temperaturschwankungen > 5°C schädlich. | `species.hardiness_detail` |
| Heimat | Tropisches Brasilien (feuchte Regenwälder, Unterholz) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis Taxonomie:** *Goeppertia makoyana* ist die aktuelle, korrekte Bezeichnung — früher als *Calathea makoyana* geführt. Im Handel wird weiterhin überwiegend der Name "Calathea" verwendet. Weitere Calathea-Arten wurden ebenfalls umbenannt (Goeppertia ornata, G. orbifolia etc.). Die beweglichen Blätter (Nyktinastie) — Blätter falten sich nachts zusammen — sind charakteristisch für alle Marantaceae.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6 (selten Indoor; kleine weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Ausschließlich durch Teilung beim Umtopfen (im Frühling). Jedes Teilstück muss mehrere Blätter und ein aktives Rhizomstück haben. Empfindliche Pflanze nach der Teilung — langsam bewurzeln bei hoher Luftfeuchtigkeit (60–80%) und Wärme (22–24°C).

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

**Hinweis:** Calathea/Goeppertia-Arten gelten als haustiersicher — ideal für Haushalte mit Katzen und Hunden.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Abgestorbene oder beschädigte Blätter an der Basis entfernen. Kein regelmäßiger Rückschnitt.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no (zu empfindlich für Außenbedingungen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, torffreie Einheitserde mit guter Wasserspeicherkapazität aber gleichzeitig guter Drainage. Mischung aus Kokosfaser + Perlite + Redekorholz-Mulch. pH 6.0–7.0. Kein schweres Substrat. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | low |
| Winterruhe (Wachstumsverlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 4–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.3–0.7 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–350 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–8 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 17–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–19 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 60 | 30 |
| Winterruhe | 0:0:0 | 0.0–0.3 | 6.0–7.0 | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Zimmerpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (halbe Dosis) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L (halbe Dosis) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposterde (reif) | Eigenherstellung | organisch | 20% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Schwachzehrer. Überdüngung führt zu Blattrandnekrosen und Salzakkumulation. Nur verdünnter Dünger (halbe Normaldosis) alle 4–6 Wochen März–September. Kalkhaltiges Leitungswasser vermeiden — Fluorid und Kalzium führen zu Blattrandnekrosen (braunen Blatträndern). Regenwasser oder gefiltertes Wasser verwenden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.8 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water (Wick-/Untersetzer-Methode verhindert Überbewässerung und Kalkflecken) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | ZWINGEND: Regenwasser, destilliertes oder gefiltertes Wasser. Leitungswasser verursacht braune Blattränder durch Fluorid und Kalk. Raumtemperatur — kein kaltes Wasser! | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12–18 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 10 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Umtopfen / Teilen | Frühling ist beste Zeit für Umtopfen und Teilung | hoch |
| Apr | Düngung starten | Erste (halbe) Düngergabe nach Frühlingsbeginn | mittel |
| Apr–Sep | Luftfeuchtigkeit sichern | Befeuchter oder Kiesschale verwenden; 60–80% RH sicherstellen | hoch |
| Apr–Sep | Wässern | Substrat gleichmäßig feucht (nicht nass!) halten | hoch |
| Sep | Düngung beenden | Letzte Düngergabe | niedrig |
| Okt–Feb | Reduziert gießen | Substrat leicht antrocknen lassen zwischen Güssen | mittel |
| Ganzjährig | Luftfeuchtigkeit | Heizungsluft (rel. Feuchte oft <30%) ergänzen! | hoch |
| Ganzjährig | Blätter reinigen | Staub mit feuchtem Tuch abwischen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, silbrige Punkte, Blattvergilbung | leaf (Unterseite) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | leaf, stem | easy |
| Trauermücke | Bradysia spp. | Adulte über Erde fliegend, Larven in feuchtem Substrat | root | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Pseudomonas-Blattflecken | bacterial | Braune, nasse, unregelmäßige Flecken mit gelbem Rand | Wasser auf Blättern, hohe Luftfeuchte + schlechte Zirkulation |
| Fusarium-Wurzelfäule | fungal | Welke, gelbe Blätter, braune Wurzeln | Überbewässerung |
| Helminthosporium-Blattfleck | fungal | Braune ovale Flecken mit gelbem Halo | Hohe Luftfeuchte, stagnierende Luft |

### 5.3 Nützlinge

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilbe | 10–20 | 14–21 |
| Steinernema feltiae | Trauermücke (Larven) | Gießen | 7–14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.3% (vorsichtig bei empfindlichen Blättern testen!) | 0 Tage | Spinnmilbe, Schmierläuse |
| Insektizidseife | biological | Sprühen, Unterseite der Blätter | 0 Tage | Spinnmilbe |
| Luftfeuchtigkeit erhöhen | cultural | Befeuchter, Kiesschale | 0 | Präventiv Spinnmilbe |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Maranta leuconeura | Maranta leuconeura | 0.9 | Gleiche Familie, identische Ansprüche |
| Farn | Nephrolepis exaltata | 0.8 | Erhöht Luftfeuchtigkeit, ähnliche Feuchteanforderungen |
| Spathiphyllum | Spathiphyllum wallisii | 0.7 | Ähnliche Feuchtigkeitsanforderungen |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad |
|---------|-------------------|-------|-------------|
| Sukkulenten/Kakteen | diverse | Gegensätzliche Luftfeuchtungsanforderungen | moderate |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Orbifolia | Goeppertia orbifolia | Gleiche Gattung | Robustere, größere Blätter |
| Goeppertia ornata | Goeppertia ornata | Gleiche Gattung | Pinke Streifen auf dunkelgrünen Blättern |
| Maranta leuconeura | Maranta leuconeura | Gleiche Familie | Etwas pflegeleichter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Goeppertia makoyana,"Pfauenpflanze;Korbmarante;Peacock Plant;Cathedral Windows",Marantaceae,Goeppertia,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Tropisches Brasilien",yes,2-8,15,30-60,30-60,yes,no,false,light_feeder
```

---

## Quellenverzeichnis

1. [NCSU Extension Plant Toolbox — Goeppertia makoyana](https://plants.ces.ncsu.edu/plants/goeppertia-makoyana/) — Botanische Einordnung, Taxonomie
2. [Smart Garden Guide — Peacock Plant Care](https://smartgardenguide.com/peacock-plant-care-calathea-makoyana/) — Pflegehinweise
3. [Gardenia.net](https://www.gardenia.net/plant/calathea-makoyana-peacock-plant) — Wachstumsparameter
4. [Planet Natural — Calathea makoyana](https://www.planetnatural.com/calathea-makoyana/) — Schädlinge, Krankheiten
5. [Patch Plants — Complete Calathea Guide](https://www.patchplants.com/pages/plant-care/complete-guide-to-calathea-care/) — Praxiswissen, Wasserqualität
