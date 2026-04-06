# Weihnachtskaktus — Schlumbergera truncata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardening Know How](https://www.gardeningknowhow.com/ornamental/cacti-succulents/christmas-cactus/advice-for-christmas-cactus-care.htm), [Old Farmer's Almanac](https://www.almanac.com/plant/christmas-cactus), [NCSU Extension](https://plants.ces.ncsu.edu/plants/schlumbergera/), [University of Minnesota Extension](https://extension.umn.edu/houseplants/holiday-cacti), [RHS](https://www.rhs.org.uk/plants/christmas-cactus/how-to-grow)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Schlumbergera truncata | `species.scientific_name` |
| Volksnamen (DE/EN) | Weihnachtskaktus, Gliederkaktus; Thanksgiving Cactus, Crab Cactus, Lobster Cactus | `species.common_names` |
| Familie | Cactaceae | `species.family` → `botanical_families.name` |
| Gattung | Schlumbergera | `species.genus` |
| Ordnung | Caryophyllales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 20–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Ruheperiode nach der Blüte wichtig für nächste Blütenbildung) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true (Kälte und Kurztag für Blüteninduktion) | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindestdauer (Tage) | 42–56 | `lifecycle_configs.vernalization_min_days` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart (tropischer Epiphyt). Optimal 18–24°C; zur Blüteninduktion 10–15°C für 6–8 Wochen. | `species.hardiness_detail` |
| Heimat | Brasilianisches Küstengebirge (Serra dos Órgãos, Rio de Janeiro) — feuchte Bergwälder, epiphytisch auf Bäumen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis Taxonomie:** Im Handel oft fälschlicherweise als *Schlumbergera x buckleyi* (echter Weihnachtskaktus, runde Gliedersegmente) verkauft, obwohl es sich überwiegend um *S. truncata* (Thanksgiving-Kaktus, gezackte Segmente) handelt. Beide Arten sehr ähnlich in der Pflege; *S. truncata* blüht etwas früher (November) als *S. x buckleyi* (Dezember/Januar). Im Volksmund werden beide "Weihnachtskaktus" genannt.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 10, 11, 12, 1 (je nach Art/Sorte und Blüteninduktion) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Glieder-Stecklinge: 2–3 Segmente abdrehen (nicht abschneiden) und 1–2 Tage antrocknen lassen. Dann in feuchtes Kakteensubstrat stecken. Bewurzelung 3–4 Wochen bei 20–22°C. Stecklinge im Frühsommer nehmen (nach der Blüte, Frühling).

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

**Hinweis:** Schlumbergera gilt als nicht giftig — ideal für Haushalte mit Haustieren. Bei Hunden und Katzen können große Mengen zu leichter Übelkeit führen, aber keine ernsthaften Vergiftungen bekannt.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 (nach der Blüte) | `species.pruning_months` |

**Hinweis:** Nach der Blüte: Überlange Triebe zurückdrehen (keine Schere — Glieder an Verbindungsstellen abdrehen). Fördert buschigen Wuchs und mehr Blütenansätze im nächsten Jahr.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–40 (hängend bis 60) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer Halbschatten; Blüteninduktion im Herbst begünstigt durch kühle Nächte draußen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Orchideen-/Epiphytensubstrat (Pinienrinde + Perlite + Torf) oder leichte Kakteenerde mit Perlite. pH 5.5–6.5. Lockeres, luftiges Substrat wichtig (epiphytische Natur). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 150–180 | 1 | false | false | medium |
| Ruheperiode (August/September) | 30–45 | 2 | false | false | high |
| Blüteninduktion (kurze Tage + Kühle) | 42–56 | 3 | false | false | medium |
| Vollblüte | 45–90 | 4 | false | false | low |
| Nachblüteruhe | 30–45 | 5 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–August)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüteninduktion (September–Oktober — KRITISCH)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–8 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 (maximal! Mehr verhindert Blüte!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–21 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vollblüte (November–Januar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–14 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:1:1 | 0.6–1.0 | 5.5–6.5 | 80 | 30 |
| Ruheperiode | 0:0:0 | 0.0 | 5.5–6.5 | — | — |
| Blüteninduktion | 0:2:1 (P-betont) | 0.4–0.6 | 5.5–6.5 | 60 | 20 |
| Vollblüte | 0:1:1 | 0.4–0.6 | 5.5–6.5 | 60 | 20 |
| Nachblüteruhe | 0:0:0 | 0.0 | 5.5–6.5 | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Aktives Wachstum → Ruheperiode | time_based | August; Wässern reduzieren, kein Dünger |
| Ruheperiode → Blüteninduktion | event_based | September; Tageslicht < 12h; Nachtkühle < 15°C |
| Blüteninduktion → Vollblüte | event_based | Knospenbildung sichtbar; Standort NICHT mehr wechseln! |
| Vollblüte → Nachblüteruhe | time_based | Nach Ende der letzten Blüte (Jan/Feb) |
| Nachblüteruhe → Aktives Wachstum | time_based | März; Düngung und Gießen wieder aufnehmen |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Compo | base | 5-8-10 | 5 ml/L (alle 2 Wochen) | Wachstum, Blüteninduktion |
| Kakteen-Dünger | Substral | base | 3-6-7 | 5 ml/L | Wachstum |
| Orchideen-Dünger (halbverdünnt) | Compo | base | 7-5-6 | 3 ml/L | Wachstum (Epiphyten-Ernährung) |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10–15% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Schwachzehrer. Im Sommer alle 2 Wochen Dünger (ganzjährig außer Ruheperioden). Ab August bis Knospenentwicklung kein Dünger — dann bis Blüteende monatlich. Überdüngung verhindert Blüte. Wichtigstes Pflegewissen: Für Blüte sind Kurztag + Kühle ausschlaggebend, nicht Düngung!

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt (kalkarm); abgestandenes Leitungswasser; kein kaltes Wasser | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 (nach der Blüte, im Frühling) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Feb | Nachblüteruhe | Gießen stark reduzieren, kein Dünger | hoch |
| Mär | Wachstum reaktivieren | Düngung starten, Gießen normalisieren | mittel |
| Apr–Mai | Schnitt/Stecklinge | Überlange Triebe zurückdrehen; Stecklinge gewinnen | mittel |
| Mai–Jul | Sommer-Pflege | Regelmäßig wässern und düngen (alle 2 Wochen) | mittel |
| Aug | Sommer-Pause | Gießen reduzieren, Düngen stoppen (Ruhevorbereitung) | hoch |
| Sep | KURZTAG-KÜHLREIZ | Standort mit max. 12h Licht und Nachttemperatur 10–15°C | KRITISCH |
| Okt–Nov | Knospen entwickeln | Standort NICHT wechseln, Blüten fallen sonst ab | hoch |
| Nov–Jan | Vollblüte | Gleichmäßig wässern, monatlich düngen, warm stellen | mittel |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Glieder schrumpfen | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Gelenken | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Gliederfäule | fungal (Fusarium) | Glieder werden weich, glasig | Überbewässerung |
| Wurzelfäule | fungal | Welke Glieder trotz feuchtem Substrat | Staunässe |
| Knospenfall | physiologisch | Knospen fallen vor Aufblühen ab | Standortwechsel, Zugluft, Temperaturschwankung, Trockenheit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.3% (Blüten schützen!) | 0 Tage | Spinnmilbe, Schmierläuse |
| Drainage verbessern | cultural | Durchlässigeres Substrat, kein Untersetzer-Staunasser | 0 | Wurzelfäule |
| Stabile Lage | cultural | Keine Standortwechsel nach Knospenbildung | 0 | Knospenfall (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Echter Weihnachtskaktus | Schlumbergera x buckleyi | Gleiche Gattung, runde Gliedersegmente | Blüht later (Dezember/Januar) = näher an Weihnachten |
| Osterkaktus | Hatiora gaertneri | Gleiche Familie | Blüht Frühling (April) |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Schlumbergera truncata,"Weihnachtskaktus;Gliederkaktus;Thanksgiving Cactus;Crab Cactus",Cactaceae,Schlumbergera,perennial,short_day,herb,fibrous,"10a;10b;11a;11b","Brasilianisches Küstengebirge",yes,1-5,12,20-60,30-60,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Gardening Know How — Christmas Cactus](https://www.gardeningknowhow.com/ornamental/cacti-succulents/christmas-cactus/advice-for-christmas-cactus-care.htm) — Pflegehinweise
2. [Old Farmer's Almanac](https://www.almanac.com/plant/christmas-cactus) — Blüteninduktion, Saisonkalender
3. [NCSU Extension — Schlumbergera](https://plants.ces.ncsu.edu/plants/schlumbergera/) — Botanische Einordnung
4. [University of Minnesota Extension](https://extension.umn.edu/houseplants/holiday-cacti) — Kurztag-Protokoll
5. [Royal Horticultural Society](https://www.rhs.org.uk/plants/christmas-cactus/how-to-grow) — Kulturempfehlungen
