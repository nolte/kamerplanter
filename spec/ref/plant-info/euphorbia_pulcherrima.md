# Weihnachtsstern — Euphorbia pulcherrima

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Pflanzen-Kölle – Weihnachtsstern](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-weihnachtsstern-richtig/), [PlantFrand – Euphorbia pulcherrima](https://www.plantfrand.com/pflanzen/euphorbiaceae/euphorbia-pulcherrima/), [Feey – Weihnachtsstern](https://feey.ch/pages/weihnachtsstern), [Zimmerpflanzen-Portal](https://www.zimmerpflanzen-portal.de/weihnachtsstern-euphorbia-pulcherrima/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Euphorbia pulcherrima | `species.scientific_name` |
| Volksnamen (DE/EN) | Weihnachtsstern, Poinsettie; Poinsettia, Christmas Star | `species.common_names` |
| Familie | Euphorbiaceae | `species.family` → `botanical_families.name` |
| Gattung | Euphorbia | `species.genus` |
| Ordnung | Malpighiales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | short_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | In Mitteleuropa nur als Zimmerpflanze; Frostgrenze ca. +5°C | `species.hardiness_detail` |
| Heimat | Mexiko, Mittelamerika | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 11, 12, 1 (Kurztagspflanze, Weihnachtszeit) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | alle Pflanzenteile, insbesondere Milchsaft (Latex) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Euphorbon (Diterpen-Ester), Milchsaft-Latex | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Der Milchsaft kann Hautreizungen und Schleimhautentzündungen verursachen. Die Toxizität wurde in der Vergangenheit überschätzt — für Erwachsene sind größere Mengen nötig für ernste Vergiftungserscheinungen. Bei Kindern und Haustieren dennoch Vorsicht geboten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4 | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 (in Natur bis 400 cm) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Zimmerpflanzenerde; keine Staunässe; pH 6.0–6.5 | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Akklimatisierung | 14–21 | 1 | false | false | low |
| Vegetativ (Wachstum) | 180–210 | 2 | false | false | medium |
| Blüteinduktion (Kurztag) | 42–63 | 3 | false | false | low |
| Blüte/Hochblätter | 60–90 | 4 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum) — Frühjahr bis Herbst

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–65 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüteinduktion (Kurztag) — ab Oktober

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | max. 10 (strikt!) | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–60 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 50–60 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.9–1.3 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 4–6 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Akklimatisierung | 0:0:0 | 0.0 | 6.0–6.5 | — | — | — | — |
| Vegetativ | 2:1:2 | 1.0–1.5 | 6.0–6.5 | 120 | 50 | — | 2 |
| Blüteinduktion | 1:2:3 | 0.8–1.2 | 6.0–6.5 | 100 | 40 | — | 2 |
| Blüte | 0:1:2 | 0.6–1.0 | 6.0–6.5 | 80 | 30 | — | 1 |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Akklimatisierung → Vegetativ | time_based | 14–21 Tage | Neue Blätter sichtbar |
| Vegetativ → Blüteinduktion | event_based | — | Tageslänge unter 10 Stunden (Anfang Oktober) |
| Blüteinduktion → Blüte | time_based | 42–63 Tage | Hochblätter färben sich |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Blühpflanzendünger | Compo | base | 4-6-8 | 5 ml/L | 1 | blüteinduktion, blüte |
| Grünpflanzendünger | Substral | base | 7-3-7 | 5 ml/L | 1 | vegetativ |

#### Organisch (Topf)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Blumendünger flüssig | Guano Kalong | organisch | 2 ml/L | Apr–Sep | medium_feeder |
| Langzeitdünger Stäbchen | Compo Sana | organisch/langsam | 1 Stäbchen alle 3 Monate | Apr–Sep | medium_feeder |

### 3.2 Düngungsplan

| Woche | Phase | EC (mS) | pH | Produkt A (ml/L) | Hinweise |
|-------|-------|---------|-----|-------------------|----------|
| 1–3 | Akklimatisierung | 0.0 | — | — | Kein Dünger, Stressvermeidung |
| 4–26 | Vegetativ | 1.0–1.5 | 6.2 | 5 | Monatlich düngen |
| Okt–Nov | Blüteinduktion | 0.8–1.2 | 6.2 | 5 | Alle 4 Wochen, phosphorlastig |
| Dez–Jan | Blüte | 0.6–1.0 | 6.2 | — | Kein Dünger nötig |

### 3.3 Mischungsreihenfolge

1. Wasser (Raumtemperatur, nie kalt)
2. Flüssigdünger

### 3.4 Besondere Hinweise zur Düngung

Der Weihnachtsstern ist als Kurztagspflanze auf exakt gesteuerte Beleuchtung angewiesen — für die Wiederblüte nach dem Kauf müssen ab Oktober täglich mindestens 14 Stunden vollständige Dunkelheit garantiert werden (auch künstliche Lichtquellen verhindern Blüteinduktion!). Düngung spielt gegenüber der Lichtsteuerung eine untergeordnete Rolle.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes Wasser, keine Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 30 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan | Blüte beobachten | Wenig gießen, nicht düngen, Zugluft vermeiden | niedrig |
| Feb | Rückschnitt vorbereiten | Blüte verblüht, Pflanze beginnt einzuziehen | mittel |
| Mär | Rückschnitt | Stark zurückschneiden (auf 15 cm), frische Erde | hoch |
| Apr | Umtopfen | In frisches Substrat, Düngung beginnen | hoch |
| Mai–Aug | Wachstum | Regelmäßig gießen und düngen, heller Standort | hoch |
| Sep | Wachstum beenden | Letzte Düngung | mittel |
| Okt | Kurztag-Behandlung | Ab 1. Oktober tägl. 14 Stunden Dunkelheit (Karton) | hoch |
| Nov | Blüteinduktion kontrollieren | Hochblätter müssen sich färben | hoch |
| Dez | Dekorativer Höhepunkt | Zimmerwarm, heller Standort, sparsam gießen | niedrig |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Weiße Fliege | Trialeurodes vaporariorum | Weiße Fliegen bei Berühren, Honigtau | leaf | alle | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste, gelbfleckige Blätter | leaf | vegetative | medium |
| Schmierläuse | Pseudococcus longispinus | Weiße Wollflecken, Honigtau | stem, leaf | alle | medium |
| Trauermücken | Sciara spp. | Larven in Substrat | root | alle | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Grauschimmel (Botrytis) | fungal | Grauer Schimmelbelag | high_humidity, poor_airflow | 3–7 | flowering |
| Wurzelfäule | fungal | Welke Blätter, schwarze Wurzeln | overwatering | 7–14 | alle |
| Bakterielle Weichfäule | bacterial | Weiche, nasse Stellen am Stängel | waterlogging, wounds | 3–7 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Encarsia formosa | Weiße Fliege | 3–5 | 21–28 |
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |
| Steinernema feltiae | Trauermückenlarven | 0.5 Mio. Nematoden/m² | 7 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gelbkarten | mechanical | — | Aufhängen neben Pflanze | 0 | Weiße Fliege, Trauermücken |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 0 | Weiße Fliege, Spinnmilben |
| Pyrethrin | chemical | Pyrethrum | Sprühen nach Anweisung | 1 | Weiße Fliege, Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze |
| Empfohlene Vorfrucht | — |
| Empfohlene Nachfrucht | — |
| Anbaupause (Jahre) | — |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Euphorbia pulcherrima |
|-----|-------------------|-------------|------------------------------|
| Weihnachtskaktus | Schlumbergera truncata | Kurztagspflanze, Winterblüher | Langlebiger, pflegeleichter |
| Kalanchoe | Kalanchoe blossfeldiana | Kurztagspflanze, Winterblüher | Robuster, weniger anspruchsvoll |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Euphorbia pulcherrima,Weihnachtsstern;Poinsettie;Christmas Star,Euphorbiaceae,Euphorbia,perennial,short_day,shrub,fibrous,9a;9b;10a;10b;11a;11b,0.0,Mexiko Mittelamerika,yes,3,15,60,40,—,yes,no,false,false
```

---

## Quellenverzeichnis

1. [Pflanzen-Kölle – Weihnachtsstern Pflege](https://www.pflanzen-koelle.de/ratgeber/pflanzen-a-z/wie-pflege-ich-meinen-weihnachtsstern-richtig/) — Pflege, Standort
2. [PlantFrand – Euphorbia pulcherrima](https://www.plantfrand.com/pflanzen/euphorbiaceae/euphorbia-pulcherrima/) — Botanik, Toxizität
3. [Feey – Weihnachtsstern](https://feey.ch/pages/weihnachtsstern) — Steckbrief, Überwinterung
4. [Zimmerpflanzen-Portal](https://www.zimmerpflanzen-portal.de/weihnachtsstern-euphorbia-pulcherrima/) — Schädlinge, Krankheiten
5. [Landwirtschaft BW – Nützlinge Weihnachtsstern](https://www.landwirtschaft-bw.de/site/pbs-bw-new/get/documents/MLR.LEL/PB5Documents/ltz_ka/Arbeitsfelder/Pflanzenschutz/N%C3%BCtzlinge/Zierpflanzenbau/Gesch%C3%BCtzter%20Anbau%20(Gew%C3%A4chshaus)/Sch%C3%A4dlinge%20und%20N%C3%BCtzlingseinsatz%20weihnachtsstern.pdf) — Biologischer Pflanzenschutz
