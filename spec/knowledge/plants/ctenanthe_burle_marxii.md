# Fischgräten-Gebetsblume — Ctenanthe burle-marxii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/ctenanthe-burle-marxii-care/), [Houseplant 411](https://www.houseplant411.com/houseplant/ctenanthe-plant-how-to-grow-care-for-ctenanthe-plants/), [Plant Care Today](https://plantcaretoday.com/ctenanthe-burle-marxii.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Ctenanthe burle-marxii | `species.scientific_name` |
| Synonyme | Ctenanthe burle-marxii 'Amagris' (häufige Handelsform) | — |
| Volksnamen (DE/EN) | Fischgräten-Gebetsblume, Ctenanthe; Fishbone Prayer Plant, Never Never Plant, Bamburanta | `species.common_names` |
| Familie | Marantaceae | `species.family` → `botanical_families.name` |
| Gattung | Ctenanthe | `species.genus` |
| Ordnung | Zingiberales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Reagiert empfindlich auf Kälte unter 13°C. | `species.hardiness_detail` |
| Heimat | Brasilien — tropische Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Ctenanthe burle-marxii zeigt das für Marantaceen typische Fischgräten-Muster auf den blaugrünen Blättern mit silbergrauen Streifen — die Blattunterseite ist leuchtend magentafarben. Wie alle Marantaceen zeigt die Pflanze ausgeprägte Nyktinastie (Blätter falten sich nachts auf). Im Vergleich zu Calathea/Goeppertia-Arten gilt sie als etwas robuster und anspruchsloser. Benannt nach dem brasilianischen Landschaftsarchitekten Roberto Burle Marx.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (kleine weiße Blüten bei älteren Pflanzen, selten in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Rhizom-Teilung beim Umtopfen im Frühjahr — Abschnitte mit mindestens 2–3 Blättern in feuchtes Substrat. Hohe Luftfeuchtigkeit nach der Teilung wichtig. Bewurzelung dauert 4–6 Wochen.

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

**Hinweis:** Kein Rückschnitt erforderlich. Nur komplett abgestorbene oder gelbe Blätter an der Basis entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 25–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no (zu empfindlich für direkte Sonne und Zugluft) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut drainierte, feuchtigkeitshaltende Erde. pH 6.0–7.0. Mix aus Einheitserde + Perlite (20%) + Kokosfaser (15%). Gute Drainage wichtig — keine Staunässe. | — |

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
| Licht PPFD (µmol/m²/s) | 80–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 60–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 60–180 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 6.0–7.0 | 50 | 20 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich, halbdosiert) | Wachstum |
| Zimmerpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich April bis August, halbe Empfehlungsdosis. September bis März kein Dünger. Weiches, kalkarmes Wasser bevorzugen (Regenwasser oder gefiltertes Wasser). Kalkreiches Leitungswasser kann Blattspitzenbraun verursachen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkarmes Wasser bevorzugt (Regenwasser, gefiltertes Wasser); Substrat gleichmäßig feucht halten; hohe Luftfeuchtigkeit notwendig (Luftbefeuchter oder Kieselsteinschale) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, Blätter vergilben, braune Ränder | medium |
| Schmierlaus | Pseudococcus spp. | Weißwollige Flecken in Blattachseln | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen, deformierte Blätter | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke trotz feuchtem Substrat, braune Wurzeln | Staunässe |
| Blattflecken | fungal | Braune Flecken mit gelbem Rand | Nasses Laub, schlechte Belüftung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Luftbefeuchter, Kieselsteinschale | 0 | Spinnmilbe (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Schmierläuse |
| Kaliseife | biological | Sprühen 1–2% | 0 Tage | Schmierläuse, Thrips |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Klapperschlangen-Calathea | Goeppertia lancifolia | Marantaceae, ähnliches Muster | Etwas bekannter, gut verfügbar |
| Korbmarante | Goeppertia makoyana | Marantaceae, Gebetsblume | Pfauenmuster, Nyktinastie |
| Stromanthe Triostar | Stromanthe sanguinea | Marantaceae | Dreifarbiges Laub |
| Gewöhnliche Gebetsblume | Maranta leuconeura | Marantaceae | Kompakter, robust |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Ctenanthe burle-marxii,"Fischgräten-Gebetsblume;Ctenanthe;Fishbone Prayer Plant;Never Never Plant;Bamburanta",Marantaceae,Ctenanthe,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Brasilien (tropische Regenwälder)",yes,2-8,15,25-50,30-60,yes,no,false,light_feeder
```

---

## Quellenverzeichnis

1. [Smart Garden Guide — Ctenanthe burle-marxii](https://smartgardenguide.com/ctenanthe-burle-marxii-care/) — Pflegehinweise, Kulturdaten
2. [Houseplant 411 — Ctenanthe](https://www.houseplant411.com/houseplant/ctenanthe-plant-how-to-grow-care-for-ctenanthe-plants/) — Botanische Daten, Schädlinge
3. [Plant Care Today — Ctenanthe burle-marxii](https://plantcaretoday.com/ctenanthe-burle-marxii.html) — Pflegedetails
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
