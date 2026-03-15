# Fleißiges Lieschen — Impatiens walleriana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Hortica — Impatiens walleriana](https://hortica.de/pflanzen/fleissiges-lieschen/), [Pflanzen-Kölle](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-mein-fleissiges-lieschen-richtig/), [Pflanzen-Deutschland](https://www.pflanzen-deutschland.de/Impatiens_walleriana.html), [ASPCA](https://www.aspca.org/), [Plant Addicts — Toxicity](https://plantaddicts.com/are-impatiens-poisonous/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Impatiens walleriana | `species.scientific_name` |
| Synonyme | Impatiens sultanii, Impatiens holstii | — |
| Volksnamen (DE/EN) | Fleißiges Lieschen, Springkraut; Busy Lizzie, Touch-me-not, Patient Lucy | `species.common_names` |
| Familie | Balsaminaceae | `species.family` → `botanical_families.name` |
| Gattung | Impatiens | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 1 (als Einjährige) oder 2–3 (überwintert als Zimmerpflanze) | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Als Zimmerpflanze bei mindestens 15°C überwintern. Als Balkonpflanze einjährig. | `species.hardiness_detail` |
| Heimat | Ostafrika (Tansania, Mosambik) — feuchte Bergwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Das Fleißige Lieschen ist eine der beliebtesten Schatten- und Halbschatten-Balkonpflanzen Deutschlands. Es blüht pausenlos von Mai bis Oktober und benötigt kaum Pflege. Besonders wertvoll für schattige Balkon- und Terrassenstandorte, wo andere Blühpflanzen versagen. Als Zimmerpflanze kann es mit genügend Licht ganzjährig blühen. Der Volksname "Fleißiges Lieschen" bezieht sich auf die unermüdliche Blütenproduktion. Achtung: Seit 2011 grassiert der Impatiens-Falsche-Mehltau (Plasmopara obducens) in Mitteleuropa und hat viele Bestände vernichtet — Impatiens New Guinea-Hybriden sind resistent.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–12 (Aussaat Februar/März, Samen lichtkeimend) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 (bis Frost) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge 7–10 cm in Wasser bewurzeln (1–2 Wochen). Samen (Lichtkeimer) auf Substrat-Oberfläche legen, nicht bedecken.

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
| Rückschnitt-Typ | summer_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8 (leichter Rückschnitt für kompakteren Wuchs) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–50 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Hauptanwendung — Halbschatten!) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, humusreiche, feuchtigkeitshaltende Erde. pH 6.0–7.0. Einheitserde + 10% Kokosfaser. Regelmäßige Feuchtigkeit wichtig. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–14 | 1 | false | false | low |
| Wachstum/Blüte (Mai–Oktober) | 150–180 | 2 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Wachstum/Blüte (Mai–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 2–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Wachstum/Blüte | 1:2:2 | 0.8–1.4 | 6.0–7.0 | 70 | 25 |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Flüssigdünger | Compo | base | 5-8-10 | 5 ml/L (alle 14 Tage) | Blüte |
| Balkonpflanzen-Dünger | Substral | base | 5-8-11 | 5 ml/L | Blüte |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Blaukorn | – | mineralisch Langzeit | 3–5 g/L Substrat | einmalig beim Einpflanzen |

### 3.2 Besondere Hinweise

Mittelzehrer. Alle 14 Tage von Mai bis September. Phosphat-betonter Dünger unterstützt Blütenbildung. Sensibel gegenüber Überdüngung — halbe Empfehlungsdosis ist sicherer.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 2–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; Substrat gleichmäßig feucht halten — verträgt weder Austrocknung noch Staunässe; NIE auf Blätter gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 5–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Punkte, welke Blätter | medium |
| Blattläuse | Aphis spp. | Klebrige Triebe, Blattrollungen | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Impatiens-Falscher-Mehltau | oomycete (Plasmopara obducens) | Blattunterseite weißer Belag, Blätter fallen ab | Feuchtigkeit, kühle Nächte |
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel | Nässe, schlechte Belüftung |
| Wurzelfäule | fungal | Welke | Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Impatiens New Guinea kaufen | cultural | Resistente Sortengruppe | 0 | Falscher Mehltau (Prävention) |
| Befallene Pflanzen entfernen | cultural | Sofort entfernen und entsorgen (kein Kompost) | 0 | Falscher Mehltau |
| Neemöl | biological | Sprühen 0.5% | 0 | Blattläuse, Spinnmilben |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Balkon-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Neuguinea-Impatiens | Impatiens hawkeri | Gleiche Gattung | Resistent gegen Falschen Mehltau |
| Wachsbegonie | Begonia semperflorens | Ähnliche Nutzung | Weniger Krankheitsanfällig |
| Fuchsia | Fuchsia x hybrida | Halbschatten-Blüher | Robuster |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Impatiens walleriana,"Fleißiges Lieschen;Springkraut;Busy Lizzie;Touch-me-not",Balsaminaceae,Impatiens,annual,day_neutral,herb,fibrous,"10a;10b;11a;11b","Ostafrika (Tansania, Mosambik)",yes,2-8,15,20-60,20-50,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Hortica — Impatiens walleriana](https://hortica.de/pflanzen/fleissiges-lieschen/) — Pflege, Kulturdaten
2. [Pflanzen-Kölle — Fleißiges Lieschen](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-mein-fleissiges-lieschen-richtig/) — Pflegetipps
3. [Pflanzen-Deutschland — Impatiens walleriana](https://www.pflanzen-deutschland.de/Impatiens_walleriana.html) — Botanische Daten
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
5. [Plant Addicts — Are Impatiens Poisonous?](https://plantaddicts.com/are-impatiens-poisonous/) — Toxizitätsdaten
