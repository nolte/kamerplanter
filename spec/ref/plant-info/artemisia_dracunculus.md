# Estragon — Artemisia dracunculus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Ellis Garten Estragon, Plantura Estragon pflegen, Gartenrat Estragon, Hausgarten Estragon, Kiepenkerl Estragon

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Artemisia dracunculus | `species.scientific_name` |
| Volksnamen (DE/EN) | Estragon, Bertram, Dragon; Tarragon | `species.common_names` |
| Familie | Asteraceae | `species.family` → `botanical_families.name` |
| Gattung | Artemisia | `species.genus` |
| Ordnung | Asterales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | rhizomatous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 5a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Französischer Estragon: winterhart bis -11°C; in Norddeutschland Frostschutz nötig; Russischer Estragon (var. inodorus): robuster bis -25°C, aber schlechteres Aroma | `species.hardiness_detail` |
| Heimat | Zentralasien, Sibirien | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**WICHTIG:** Es gibt zwei Varietäten mit SEHR unterschiedlicher Qualität:
- **Artemisia dracunculus var. sativus** (Französischer Estragon): Intensiv aromatisch (Anis, Fenchel); STERIL (keine Samen); nur durch Stecklinge/Teilung vermehrbar
- **Artemisia dracunculus** (Russischer Estragon): Milderes, oft bitteres Aroma; bildet Samen; aus Samen züchtbar; robuster

Beim Kauf unbedingt Sorte beachten — Stecklinge/Topfpflanzen sind meist Französ. Estragon.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Stecklinge; Russischer: 6–8 Wochen Vorkultur) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — (Französ. Estragon: keine Aussaat möglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5 (nur Russischer Estragon) | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (Triebspitzen und Blätter vor der Blüte am aromatischsten) | `species.harvest_months` |
| Blütemonate | 7, 8 (unscheinbar; beim Französ. Estragon selten) | `species.bloom_months` |

**Ernte-Tipp:** Triebspitzen und junge Blätter ernten (5–10 cm). Beste Aromaentwicklung vor/während der Blüte. Regelmäßige Ernte fördert buschigen Wuchs und verzögert Verholzung.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge im Mai/Juni (10–15 cm, halbreif). Rhizomteilung im Frühjahr alle 3–4 Jahre empfohlen (verjüngt die Pflanze). Französ. Estragon NIEMALS aus Samen (steril).

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (in Küchenmengen sicher) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Estragol (bei sehr großen Mengen mutagen; in normalen Gewürzmengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10 (Herbst; auf 10–15 cm zurückschneiden für Winterschutz) | `species.pruning_months` |

**Hinweis:** Im Herbst (Oktober) auf 10–15 cm zurückschneiden. Kurzer Stumpf und Mulch/Reisig als Winterschutz für Französ. Estragon in Norddeutschland. Im Frühjahr (März) aufräumen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 5–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 40–50 | `species.spacing_cm` |
| Indoor-Anbau | limited | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Durchlässige Kräutererde mit Sandanteil; pH 6,0–7,5; sehr gute Drainage; keine Nässe | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–28 | 1 | false | false | low |
| Vegetatives Wachstum (Ernte) | 60–90 | 2 | false | true | medium |
| Blüte (gering) | 14–28 | 3 | false | true | high |
| Herbstabreife | 30–45 | 4 | false | true | high |
| Winterruhe | 120–150 | 5 | true | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum / Ernte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 (vollsonnig bis halbschattig) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–25 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Frühjahrsaustrieb | 1:0:1 | 0.4–0.8 | 6.0–7.5 | 60 | 30 | — | 2 |
| Vegetativ / Ernte | 1:0:1 | 0.4–0.8 | 6.0–7.5 | 60 | 30 | — | 2 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Kompost (reif, wenig) | eigen | organisch | 1–2 L/m² | März | Startdüngung |
| Kräuterdünger (stark verdünnt) | Compo Kräuter | organisch-mineralisch | 1/4 Empfehldosis | alle 4–6 Wochen | Topfkultur |

### 3.2 Besondere Hinweise zur Düngung

Estragon ist ein ausgeprägt schwacher Zehrer — zu viel Dünger führt zu kräftigem Wuchs mit weniger Aroma. Im Beet reicht einmalige Kompostgabe im Frühjahr. Im Topf sehr niedrig dosiert alle 4–6 Wochen. Kein Dünger ab August (Triebe sollen ausreifen).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 6 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 8.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Eher trocken halten; keine Staunässe; Topfoberfläche abtrocknen lassen vor dem Gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36 (alle 3 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Austrieb beobachten | Frostschutz entfernen; Kompost einarbeiten | mittel |
| Apr–Sep | Regelmäßige Ernte | Triebspitzen ernten; fördert buschigen Wuchs | hoch |
| Okt | Rückschnitt | Auf 10–15 cm zurückschneiden | hoch |
| Nov | Winterschutz | Reisig/Stroh über Wurzelbereich; Topf schützen | hoch |
| Alle 3 J. | Teilung | Frühjahr; verjüngt; Aroma verbessert sich | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 0 (frostfrei) | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 10 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

**Norddeutschland-Empfehlung:** Französ. Estragon (var. sativus) lieber in Topf pflanzen und im Winter in frostfreie Umgebung (Garage, kühles Treppenhaus) stellen. Alternativ: Russischer Estragon (robuster) für Freiland.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Selten; Kolonien | shoot | vegetative | easy |
| Spinnmilben | Tetranychus urticae | Feine Gespinste; Blattvergilbung | leaf | vegetative (Hitze/Trockenheit) | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trocken + warm | 7–10 | vegetative (Sommer) |
| Wurzelfäule | fungal (Pythium) | Welken; braune Wurzeln | Staunässe | 7–14 | alle |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Gute Drainage | cultural | — | Substrat verbessern; kein Staunässe | 0 | Wurzelfäule |
| Neemöl | biological | Azadirachtin | 0.5% sprühen; nicht auf Ernteblätter | 3 | Spinnmilben, Blattläuse |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Kräuter / Asteraceae |
| Empfohlene Vorfrucht | beliebig |
| Anbaupause (Jahre) | Mehrjährig; Standort 3–4 Jahre; dann teilen und umpflanzen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Klassische Paarung; Aromasynergie; Schädlingsabwehr | `compatible_with` |
| Kopfsalat | Lactuca sativa | 0.8 | Estragon lockert Boden; Schutz vor Schnecken | `compatible_with` |
| Möhre | Daucus carota | 0.7 | Aromawirkung; Möhrenfliegen-Verwirrung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| — | — | Keine bekannten starken Unverträglichkeiten | — | — |

---

## 7. CSV-Import-Daten (KA REQ-012 kompatibel)

### 7.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,harvest_months
Artemisia dracunculus,"Estragon;Bertram;Tarragon",Asteraceae,Artemisia,perennial,long_day,herb,rhizomatous,"5a;5b;6a;6b;7a;7b;8a;8b",0.1,"Zentralasien, Sibirien",yes,8,20,100,50,45,limited,yes,false,false,light_feeder,false,half_hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Ellis Garten — Estragon](https://www.ellis-garten.de/estragon-steckbrief-pflege-verwendung-der-artemisia-dracunculus/) — Steckbrief, Verwendung
2. [Plantura — Estragon pflegen](https://www.plantura.garden/kraeuter/estragon/estragon-pflegen) — Pflege, Überwintern
3. [Gartenrat — Estragon](https://gartenrat.de/estragon/) — Anbau, Ernte
4. [Hausgarten — Estragon](https://www.hausgarten.net/kraeuter-und-gewuerze/kraeuter-gartenkraeuter/estragon-anbau-ernte-verwendung.html) — Kulturdaten
5. [Kiepenkerl — Estragon Kulturanleitung](https://www.kiepenkerl.de/kulturanleitungen/estragon/) — Aussaatdaten
