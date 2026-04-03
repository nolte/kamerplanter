# Königsbegonie — Begonia rex-cultorum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardeners Path](https://gardenerspath.com/plants/houseplants/grow-rex-begonia/), [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/rex-begonia-care-guide-growing-vibrant-begonia-rex-cultorum/), [Gardenia.net](https://www.gardenia.net/genus/begonia-rex-cultorum-rex-begonia-grow-and-care-tips), [The Sill](https://www.thesill.com/blogs/plants-101/how-to-care-for-rex-begonia), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Begonia rex-cultorum | `species.scientific_name` |
| Volksnamen (DE/EN) | Königsbegonie, Zierbegonie; Rex Begonia, King Begonia, Painted-leaf Begonia | `species.common_names` |
| Familie | Begoniaceae | `species.family` → `botanical_families.name` |
| Gattung | Begonia | `species.genus` |
| Ordnung | Cucurbitales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 3–5 (ab Teilung neu verjüngen) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 13°C, optimal 18–24°C. | `species.hardiness_detail` |
| Heimat | Ostindien (Assam) — ursprünglich, Hybridkultivare weltweit gezüchtet | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Begonia rex-cultorum ist kein Artname, sondern eine Kultivargruppe — alle modernen Sorten sind Kreuzungen und Hybriden. Das Blattspektrum ist unübertroffen: Silber, Purpur, Bronze, Schwarz, Rosa, Grün in unzähligen Mustern (Spiralen, Tupfen, Sterne). Primärer Dekorationswert liegt in den Blättern, nicht in den Blüten (die eher unscheinbar sind). Die Pflanze benötigt hohe Luftfeuchtigkeit aber gleichzeitig trockene Blätter — Blattnässe fördert Mehltau. Unterbewässerung ist besser als Überwässerung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8 (kleine, unscheinbare rosa-weiße Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_leaf, division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Blattstecklinge: Blatt ablegen, 4–5 Kerben in die Hauptadern schneiden (Unterseite), auf feuchtes Substrat legen. Bewurzelung und neue Pflänzchen in 6–12 Wochen. Oder: Blattstiel im 45°-Winkel in feuchtes Substrat stecken. Teilung des Rhizoms beim Umtopfen ebenfalls möglich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (besonders Rhizom/Rhizom — lösliche Calcium-Oxalate) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | calcium_oxalate_raphides (besonders in Rhizomen) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Rhizom zurückschneiden für kompakteren Wuchs) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 (flache Rhizome) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–50 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 25–50 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (windgeschützt, Halbschatten, kein Regen, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut durchlässige Einheitserde mit 25% Perlite. pH 5.5–6.5. Flache Schalen bevorzugt (Rhizom braucht Breite, nicht Tiefe). | — |

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
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.5–6.5 | 50 | 20 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 5.5–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 2 ml/L (monatlich) | Wachstum |
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Leichter Zehrer. Monatlich März bis September, halbe Empfehlungsdosis. Oktober bis Februar kein Dünger. Nie auf die Blätter düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | calathea | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; NIE auf Blätter gießen (Mehltau); Substrat leicht antrocknen lassen zwischen Güssen; Luftfeuchtigkeit mit Kieselstein-Schale erhöhen (nicht besprühen) | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter verblassen | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Thrips | Frankliniella occidentalis | Silbrige Streifen | medium |
| Blattläuse | Aphis spp. | Klebrige Triebe | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Echter Mehltau | fungal | Weißer Belag auf Blättern | Nasse Blätter, schlechte Belüftung |
| Grauschimmel | fungal | Graubrauner Schimmelbelag | Zu hohe Feuchtigkeit |
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Nie besprühen | cultural | Gießtechnik ändern | 0 | Mehltau, Grauschimmel (Prävention) |
| Neemöl | biological | Sprühen 0.3% (Unterseite) | 0 Tage | Spinnmilbe, Schmierläuse |
| Kaliumbicarbonat | biological | Sprühen 0.5% | 0 | Echter Mehltau |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Eisenbegonie | Begonia masoniana | Begoniaceae, Blattzierart | Markante Eisenkreuz-Musterung |
| Wachsbegonie | Begonia semperflorens | Begoniaceae | Mehr Blüten, kompakter |
| Calathea orbifolia | Goeppertia orbifolia | Buntlaub, Zimmerpflanze | Tierfreundlich |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Begonia rex-cultorum,"Königsbegonie;Zierbegonie;Rex Begonia;Painted-leaf Begonia",Begoniaceae,Begonia,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Ostindien (Hybridkultivare)",yes,1-5,10,20-50,25-50,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardeners Path — Rex Begonia](https://gardenerspath.com/plants/houseplants/grow-rex-begonia/) — Pflegehinweise, Blatt-Vermehrung
2. [Healthy Houseplants — Rex Begonia](https://www.healthyhouseplants.com/indoor-houseplants/rex-begonia-care-guide-growing-vibrant-begonia-rex-cultorum/) — Kulturdaten
3. [Gardenia.net — Rex Begonia](https://www.gardenia.net/genus/begonia-rex-cultorum-rex-begonia-grow-and-care-tips) — Botanische Daten
4. [The Sill — Rex Begonia](https://www.thesill.com/blogs/plants-101/how-to-care-for-rex-begonia) — Schädlinge, Pflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig — Calcium-Oxalate)
