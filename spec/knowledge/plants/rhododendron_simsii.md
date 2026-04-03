# Zimmerazalee, Topf-Azalee — Rhododendron simsii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Hausgarten.net — Zimmerazalee](https://www.hausgarten.net/zimmerazalee-pflegen/), [Pflanzen-Kölle — Azalee](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-azalee-richtig/), [Baldur-Garten — Azalee](https://www.baldur-garten.de/onion/content/pflege-tipps/zimmerpflanzen/azalee), [ASPCA](https://www.aspca.org/), [Gardenia.net](https://www.gardenia.net/plant/rhododendron-simsii)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Rhododendron simsii | `species.scientific_name` |
| Synonyme | Azalea indica (veraltet, Handelsname), Azalea simsii | — |
| Volksnamen (DE/EN) | Zimmerazalee, Indische Azalee, Topf-Azalee; Sims Azalea, Pot Azalea, Indian Azalea | `species.common_names` |
| Familie | Ericaceae | `species.family` → `botanical_families.name` |
| Gattung | Rhododendron | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–20+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 7b, 8a, 8b, 9a, 9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Im Topf frostempfindlich — überwintert kühl (5–10°C) aber frostfrei. Als Kübelpflanze. Die Kühle triggert die Knospenbildung. | `species.hardiness_detail` |
| Heimat | China, Taiwan, Myanmar — subtropische Bergwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die im Handel als "Zimmerazalee" verkaufte Pflanze ist in der Regel ein Simsii-Hybrid. Sie benötigt kühle Temperaturen (12–15°C) während und nach der Blüte, um die Knospen zu erhalten. Zu warme Zimmertemperaturen (über 18°C) verkürzen die Blütezeit drastisch. Nach der Blüte kann sie als Freiluftpflanze kultiviert werden. Azaleen brauchen UNBEDINGT saures Substrat (pH 4.0–5.5) und kalkfreies Wasser — kalkreiches Leitungswasser führt innerhalb weniger Wochen zu Chlorose und Absterbeereignissen.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 1, 2, 3, 4 (Hauptblüte Winter/Frühjahr) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Halbholzige Kopfstecklinge im Sommer (Juni–August), 7–10 cm lang, Substrat aus Torf + Perlite, Bewurzelung 4–8 Wochen unter Folie bei 20–22°C. Schwierig für Einsteiger.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | all (Blätter, Blüten, Nektardrüsen — alle Teile) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | grayanotoxins (Diterpene — Andromedotoxin) | `species.toxicity.toxic_compounds` |
| Schweregrad | severe | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

**Sicherheitshinweis:** Alle Pflanzenteile des Rhododendron sind stark giftig. Grayanotoxine können Herzrhythmusstörungen, Erbrechen, Lähmungserscheinungen verursachen. Sofort Tierarzt/Notarzt bei Verdacht auf Aufnahme.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6 (direkt nach der Blüte) | `species.pruning_months` |

**Hinweis:** Direkt nach der Blüte alle verblühten Triebe um 1/3 zurückschneiden — nur bis Juli, danach werden Blütenknospen für die nächste Saison gebildet. Kein Schnitt nach August.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Halbschatten, Sommer) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Azaleen-/Rhododendronerde (pH 4.0–5.5). Nur Rhododendronerde oder Moorbeeterde verwenden — normale Gartenerde ist ungeeignet. Gute Drainage wichtig. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte (Winter/Frühjahr) | 30–60 | 1 | false | false | low |
| Erholung/Austrieb (Frühling) | 60–90 | 2 | false | false | medium |
| Sommerwachstum (Draußen) | 120–150 | 3 | false | false | medium |
| Knospenruhe (Herbst/Winter) | 60–90 | 4 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte (Januar–April)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 12–16 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–12 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sommerwachstum (Mai–September, Draußen)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 3–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Knospenruhe (Oktober–Dezember)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 5–12 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Blüte | 1:2:2 | 0.6–1.0 | 4.5–5.5 | 40 | 20 |
| Austrieb/Sommerwachstum | 2:1:2 | 0.8–1.4 | 4.5–5.5 | 50 | 25 |
| Knospenruhe | 0:0:0 | 0.0–0.2 | 4.5–5.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Rhododendron-Flüssigdünger | Compo | base | 7-3-6 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Azaleen-Dünger | Substral | base | 7-4-7 | 5 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Rhododendronrinde (Mulch) | – | organisch | 3–5 cm Schicht | ganzjährig |
| Kiefernnadeln | – | organisch | 3–5 cm Schicht | ganzjährig |

### 3.2 Besondere Hinweise

Mittelzehrer. AUSSCHLIESSLICH Azaleen-/Rhododendron-Spezialdünger verwenden — normale Dünger sind zu basisch. Düngung März bis August, alle 14 Tage. September bis Februar kein Dünger. Niemals mit kalkhaltigem Leitungswasser gießen — Regenwasser oder entkalktes Wasser (Brita-Filter) verwenden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | custom | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | NUR weiches, kalkfreies Wasser (Regenwasser, gefiltertes Wasser) — kalkreiches Leitungswasser zerstört die Pflanze durch Chlorose; pH des Gießwassers idealerweise 5.0–5.5 | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 (nur nach der Blüte) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter vergilben | medium |
| Blattläuse | Aphis spp. | Klebrige Triebe, deformierte Blüten | easy |
| Wollschildlaus | Planococcus citri | Wollflecken | easy |
| Azaleen-Mottenschildlaus | Dialeurodes chittendeni | Weiße Fliegen an Blättern | medium |
| Rhododendronwanze | Stephanitis rhododendri | Silbrige Flecken Oberseite, schwarze Punkte Unterseite | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Chlorose | physiologisch | Gelbfärbung Blätter bei grünen Adern | Kalkwasser, falscher pH |
| Wurzelfäule | fungal (Phytophthora cinnamomi) | Welke, braune Wurzeln | Staunässe |
| Blattgallenpilz | fungal (Exobasidium vaccinii) | Aufgetriebene bleiche Blattteile | hohe Feuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Azallit (Azaleen-Dünger) | cultural | Regelmäßige saure Düngung | 0 | Chlorose (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilben, Blattläuse |
| Insektizidseife | biological | Sprühen 1% | 0 | Wollschildläuse |
| Systemisches Insektizid | chemical | Stäbchen nach Packungsangabe | 14 | Mottenschildlaus, Wanzen |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Kübel-/Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Japanische Azalee | Rhododendron obtusum | Gleiche Gattung | Robuster, für Freiland geeignet |
| Cyclamen | Cyclamen persicum | Winterblüher | Weniger giftig, ähnliche Saison |
| Kalanchoe | Kalanchoe blossfeldiana | Winterblüher | Pflegeleichter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Rhododendron simsii,"Zimmerazalee;Indische Azalee;Topf-Azalee;Sims Azalea;Indian Azalea",Ericaceae,Rhododendron,perennial,short_day,shrub,fibrous,"7b;8a;8b;9a;9b","China, Taiwan",yes,2-10,15,30-90,30-80,yes,yes,false,medium_feeder
```

---

## Quellenverzeichnis

1. [Hausgarten.net — Zimmerazalee](https://www.hausgarten.net/zimmerazalee-pflegen/) — Pflege von A–Z
2. [Pflanzen-Kölle — Azalee](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meine-azalee-richtig/) — Kulturdaten
3. [Baldur-Garten — Azalee](https://www.baldur-garten.de/onion/content/pflege-tipps/zimmerpflanzen/azalee) — Pflegetipps
4. [Gardenia.net — Rhododendron simsii](https://www.gardenia.net/plant/rhododendron-simsii) — Botanische Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (stark giftig — Grayanotoxine)
