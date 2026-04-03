# Frauenhaarfarn — Adiantum raddianum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/adiantum-raddianum/), [Gardeners World](https://www.gardenersworld.com/house-plants/how-to-grow-maidenhair-fern-adiantum-raddianum/), [Guide to Houseplants](https://www.guide-to-houseplants.com/maidenhair-fern.html), [Plant Care Today](https://plantcaretoday.com/maidenhair-fern.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Adiantum raddianum | `species.scientific_name` |
| Volksnamen (DE/EN) | Frauenhaarfarn, Delta-Frauenhaarfarn; Maidenhair Fern, Delta Maidenhair Fern | `species.common_names` |
| Familie | Pteridaceae | `species.family` → `botanical_families.name` |
| Gattung | Adiantum | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal 18–24°C. Zieht bei Kälte ein und kann sich erholen. | `species.hardiness_detail` |
| Heimat | Tropisches und subtropisches Amerika (Brasilien, Andes) — feuchte Wälder, felsige Bachufer | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Frauenhaarfarn ist einer der anspruchsvollsten Zimmerfarne — er reagiert äußerst empfindlich auf Lufttrockenheit, direkte Zugluft und unregelmäßiges Gießen. Wilkt der Farn ein, kann er sich bei sofortiger Bewässerung und erhöhter Luftfeuchtigkeit noch erholen — aber ist stark gestresst. Das schwarze, drahtartige Stängel-System (Adiantum = "nicht benetzt") ist charakteristisch: Wasser perlt ab. Ideal für Badezimmer oder auf feuchten Kieselsteinen. Als Sterbenmuster gilt: braune, trockene Wedel = zu trocken oder zu warm.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farn — keine Blüten, Sporenbildung April–Oktober) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, spore | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung beim Umtopfen im Frühjahr — Rhizom mit mehreren Wedeln abtrennen, in feuchtes Substrat pflanzen. Sporenvermehrung möglich aber langwierig (mehrere Monate). Teilung ist die praktikabelste Methode.

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
| Pollenallergen | true (Sporen können bei empfindlichen Personen reagieren) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (alle abgestorbenen Wedel entfernen, fördert Neuaustrieb) | `species.pruning_months` |

**Hinweis:** Bei stark ausgetrockneten Pflanzen alle Wedel bis zur Erdbasis abschneiden und feucht halten — oft erholt sich die Pflanze vollständig.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–45 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, windgeschützt, frostfrei) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Humusreiche, gut durchlässige aber feuchtigkeitshaltende Erde. pH 6.0–7.0. Torffreier Anzuchtmix mit Perlite, Kokosfaser und Lauberde. Nie austrocknen lassen. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–180 | 1 | false | false | low |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–4 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 15–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

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
| Grünpflanzen-Flüssigdünger | Compo | base | 7-3-6 | 3 ml/L (monatlich, halbe Dosis) | Wachstum |
| Farn- und Zimmerpflanzendünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Komposttee | Eigenherstellung | organisch | 1× monatlich gießen | Wachstum |

### 3.2 Besondere Hinweise

Sehr leichter Zehrer. Nur monatlich düngen, niemals in der Winterruhe. Immer halbe Empfehlungsdosis. Überdüngung und Salze im Substrat schädigen die feinen Wurzeln und führen zu Blattbräunung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser (Regenwasser ideal). Nie austrocknen lassen, aber keine Staunässe. Erhöhte Luftfeuchtigkeit ist wichtiger als häufiges Gießen. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Blätter vergilben, Gespinste (bei Trockenheit) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, braune Stängelbasis | Staunässe |
| Blatttrockenheit | physiologisch | Braune, knusprige Wedel | Zu wenig Luftfeuchtigkeit, Zugluft |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Luftfeuchtigkeit erhöhen | cultural | Luftbefeuchter, Kieselsteinschale | 0 | Spinnmilbe, Blatttrockenheit (Prävention) |
| Neemöl | biological | Sprühen 0.3% (verdünnt) | 0 Tage | Spinnmilbe, Schmierläuse |
| Giesshygiene | cultural | Staunässe vermeiden | 0 | Wurzelfäule (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze (ideal für Terraria und Badezimmer-Arrangements).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Nordafrikanischer Frauenhaarfarn | Adiantum capillus-veneris | Gleiche Gattung | Ähnliche Pflege, etwas robuster |
| Nestfarn | Asplenium nidus | Farn, Zimmerpflanze | Viel robuster, toleriert Trockenheit besser |
| Schwertfarn | Nephrolepis exaltata | Farn, Zimmerpflanze | Robuster, toleriert mehr Licht |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Adiantum raddianum,"Frauenhaarfarn;Delta-Frauenhaarfarn;Maidenhair Fern;Delta Maidenhair",Pteridaceae,Adiantum,perennial,day_neutral,herb,rhizomatous,"10a;10b;11a;11b","Tropisches Amerika (Brasilien)",yes,1-5,12,20-45,20-40,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [NC State Extension — Adiantum raddianum](https://plants.ces.ncsu.edu/plants/adiantum-raddianum/) — Botanische Basisdaten, USDA-Zonen
2. [Gardeners World — Maidenhair Fern](https://www.gardenersworld.com/house-plants/how-to-grow-maidenhair-fern-adiantum-raddianum/) — Pflegehinweise
3. [Guide to Houseplants — Maidenhair Fern](https://www.guide-to-houseplants.com/maidenhair-fern.html) — Kulturdaten
4. [Plant Care Today — Maidenhair Fern](https://plantcaretoday.com/maidenhair-fern.html) — Schädlinge, Propagation
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
