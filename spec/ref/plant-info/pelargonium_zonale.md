# Zimmerpelargonie, Geranie — Pelargonium zonale

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Ellis' Garten](https://www.ellis-garten.de/geranie-pelargonium-zonale-wissenswertes-zu-pflege-verwendung/), [Floragard](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/beet-balkon/pelargonium-zonale), [Pflanzenfreunde.com](https://www.pflanzenfreunde.com/pelargonium.htm), [Die Grüne Welt](https://www.diegruenewelt.de/pflanze/stehende-geranien-pelargonium.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pelargonium zonale | `species.scientific_name` |
| Synonyme | Pelargonium x hortorum (Hybrid-Arten im Handel); "Geranie" ist volkstümlicher Falschname | — |
| Volksnamen (DE/EN) | Zimmerpelargonie, Zonale Geranie, Stehende Geranie; Zonal Geranium, Horseshoe Geranium, Garden Geranium | `species.common_names` |
| Familie | Geraniaceae | `species.family` → `botanical_families.name` |
| Gattung | Pelargonium | `species.genus` |
| Ordnung | Geraniales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 3–10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Als Zimmerpflanze ganzjährig, als Balkonpflanze Überwinterung bei 5–10°C notwendig. | `species.hardiness_detail` |
| Heimat | Südafrika — Kapregion | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** "Geranie" ist botanisch unkorrekt — echte Geranien (Storchschnäbel) sind eine andere Gattung. Pelargonien sind Südafrikaner und vertragen keine Staunässe. Als Zimmerpflanze bei ausreichend Licht ganzjährig blühend. Das charakteristische Ringmuster (Hufeisenmuster) auf den Blättern ist namengebend für "zonale" Pelargonien. Sehr beliebte Balkonpflanze in Deutschland, kommt aber auch als langlebige Zimmerpflanze vor.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–14 (Aussaat im Januar/Februar für Balkon-Saison) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 4, 5, 6, 7, 8, 9, 10 (als Zimmerpflanze ganzjährig möglich) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge 7–10 cm lang, 24 Stunden abtrocknen lassen (Wundverschluss), in Sandsubstrat stecken. Bewurzelung in 2–3 Wochen. Sehr einfach — ideal für Anfänger.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems (Ätherische Öle, Geraniol, Linalool) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | geraniol, linalool, citronellol (ätherische Öle) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Blatthaare können Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Rückschnitt vor dem Austrieb) | `species.pruning_months` |

**Hinweis:** Überwinterte Pflanzen im Februar/März auf 10–15 cm zurückschneiden. Während der Blüte regelmäßig Blütenköpfe entfernen (Deadheading) um Nachblüte zu fördern.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–70 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Hauptanwendung!) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut drainierte Kübelpflanzenerde. pH 6.0–7.0. Spezielle Geranienerde (mit Langzeitdünger) oder Einheitserde + 20% Sand/Perlite. Kein Torf oder moorige Substrate. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte/Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (November–Februar) | 90–120 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte/Wachstum (März–Oktober)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 5–12 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Blüte/Wachstum | 1:1:2 | 1.0–2.0 | 6.0–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Geranien-Flüssigdünger | Compo | base | 5-8-10 | 10 ml/L (wöchentlich) | Blüte |
| Geranien-Dünger | Substral | base | 5-8-11 | 10 ml/L | Blüte |

#### Langzeit / Ergänzung

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | – | organisch | 50 g/Topf | Frühjahr |
| Blaukorn | Haifa | mineralisch Langzeit | 5 g/L Substrat | einmalig Pflanzung |

### 3.2 Besondere Hinweise

Starkzehrer! Wöchentliche Düngung während der Blühperiode (April bis Oktober). Spezielle Geraniendünger mit erhöhtem Kaliumanteil verwenden — Kalium fördert die Blütenbildung und Standfestigkeit. Oktober bis Februar kein Dünger. Staunässe ist die häufigste Todesursache — lieber zu wenig als zu viel gießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; gründlich gießen und komplett ablaufen lassen; obere Erdschicht zwischen Güssen antrocknen lassen — Staunässe tötet die Pflanze | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Weiße Fliege | Trialeurodes vaporariorum | Weißliche Fliegen, Honigtau | easy |
| Blattläuse | Aphis spp. | Klebrige Triebe, Blattrollungen | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Silberpunkte | medium |
| Frankliniella (Thrips) | Frankliniella occidentalis | Silbrige Flecken | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel auf Blüten/Blättern | Hohe Feuchtigkeit, Staunässe |
| Geranienrost | fungal (Puccinia pelargonii-zonalis) | Braune Rostflecken auf Blattunterseite | Feuchtigkeit, dichte Bepflanzung |
| Wurzelfäule | fungal | Welke trotz Wasser | Staunässe |
| Bakterienfäule | bacterial | Schwarze Stängelflecken, süßlicher Geruch | Verletzungen, Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Befallene Triebe entfernen | cultural | Sofort abschneiden | 0 | Grauschimmel, Fäulen |
| Abstand vergrößern | cultural | Luftzirkulation verbessern | 0 | Grauschimmel (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 | Blattläuse, Spinnmilben |
| Gelbklebfallen | mechanical | Aufstellen | 0 | Weiße Fliege (Monitoring) |
| Fungizid Kupfer | chemical | Sprühen nach Packungsangabe | 3 | Geranienrost |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Kübel-/Balkongpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Efeupelargonie | Pelargonium peltatum | Gleiche Gattung | Hängend, Ampelpflanze |
| Duftpelargonie | Pelargonium graveolens | Gleiche Gattung | Aromatisch, Kräuteranwendung |
| Wachsbegonie | Begonia semperflorens | Ähnliche Nutzung (Beet/Balkon) | Halbschatten-tolerant |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Pelargonium zonale,"Zimmerpelargonie;Zonale Geranie;Stehende Geranie;Zonal Geranium;Horseshoe Geranium",Geraniaceae,Pelargonium,perennial,day_neutral,shrub,fibrous,"10a;10b;11a;11b","Südafrika (Kapregion)",yes,3-10,15,30-70,30-60,yes,yes,false,heavy_feeder
```

---

## Quellenverzeichnis

1. [Ellis' Garten — Geranie](https://www.ellis-garten.de/geranie-pelargonium-zonale-wissenswertes-zu-pflege-verwendung/) — Pflege & Verwendung
2. [Floragard — Pelargonium zonale](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/beet-balkon/pelargonium-zonale) — Kulturdaten
3. [Pflanzenfreunde.com — Pelargonium](https://www.pflanzenfreunde.com/pelargonium.htm) — Pflege, Überwinterung
4. [Die Grüne Welt — Stehende Geranien](https://www.diegruenewelt.de/pflanze/stehende-geranien-pelargonium.html) — Schädlinge, Krankheiten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig für Katzen/Hunde — ätherische Öle)
