# Luzerne — Medicago sativa

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Medicago sativa, Samen.de Luzerne Gründüngung, Demonet-kleeluzplus Steckbrief Luzerne, Transgen Luzerne

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Medicago sativa | `species.scientific_name` |
| Volksnamen (DE/EN) | Luzerne, Ewiger Klee; Alfalfa, Lucerne | `species.common_names` |
| Familie | Fabaceae | `species.family` → `botanical_families.name` |
| Gattung | Medicago | `species.genus` |
| Ordnung | Fabales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–10b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; tief Pfahlwurzel bis 10 m; gut etablierte Pflanzen sehr winterhart | `species.hardiness_detail` |
| Heimat | Vorderasien (Iran, Zentralasien); weltweit kultiviert | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | nitrogen_fixer | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Direktsaat) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 5, 8 | `species.direct_sow_months` |
| Erntemonate | 5, 6, 7, 8, 9 (Futterpflanze: 2–4 Schnitte/Jahr; Gründüngung: einarbeiten) | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (essbar; Keime und Blätter beliebt) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Saponine in Samen (in normalen Mengen unbedenklich) | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | true | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 5, 6, 7, 8 (Mahd regt Neuaustrieb an) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — (extrem tiefe Pfahlwurzel: >1 m) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5–15 (Flächenansaat: 15–20 g/m²) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (keine Topfkultur; Freilandeinsatz als Gründüngung) | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 5–10 | 1 | false | false | low |
| Jungpflanze (1. Jahr) | 60–90 | 2 | false | false | medium |
| Etablierungsphase | 90–120 | 3 | false | false | high |
| Produktionsphase | fortlaufend (mehrjährig) | 4 | true | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Produktionsphase

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–800 (vollsonnig optimal) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 45–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.6 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | — (Niederschlag; sehr trockenheitsresistent durch Tiefwurzel) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | — | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5–7.5 | – | – | – | – |
| Jungpflanze | 0:1:1 (KEIN N; fixiert selbst) | 0.5–0.8 | 6.5–7.5 | 80 | 30 | – | 1 |
| Produktion | 0:1:2 | 0.6–1.0 | 6.5–7.5 | 120 | 50 | – | 2 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Gründüngungsleistung

| Parameter | Wert |
|-----------|------|
| N-Fixierung (gesamt) | 300–600 kg N/ha/Jahr (Wurzel + Spross) |
| N-Fixierung (für Folgekultur verfügbar) | 100–200 kg N/ha |
| Einarbeitungszeitpunkt | Ende der Blüte; vor Samenreife (max. N-Gehalt) |
| Einarbeitungstiefe | 20–25 cm; Tiefpflügen sinnvoll |
| Wartezeit vor Folgekultur | 4–6 Wochen nach Einarbeitung |
| Gründüngungsleistung vs. Rotklee | Höher (mehr Biomasse, tiefere Wurzeln) |

### 3.2 Begleitdüngung

Grundsätzlich KEIN Stickstoff. Nur bei Anlage auf sehr armen Böden Startgabe P und K:

| Produkt | Marke | Typ | Ausbringrate | Saison | Hinweis |
|---------|-------|-----|-------------|--------|---------|
| Rohphosphat oder Superphosphat | – | mineral/organisch | 30–40 g/m² | vor Aussaat | Nur auf P-armen Böden |
| Kaliumsulfat | – | mineral | 20–30 g/m² | vor Aussaat | Nur auf K-armen Böden |
| Kalk | – | mineral | 100–200 g/m² | vor Aussaat | Bei pH < 6,5 unbedingt kalken |
| Rhizobium meliloti Impfpräparat | – | biologisch | nach Hersteller | zur Aussaat | Bei Erstanbau auf neuem Boden empfohlen |

### 3.3 Besondere Hinweise zur Düngung

Luzerne fixiert bis zu 600 kg N/ha/Jahr — mehr als alle anderen Leguminosen. pH-Wert MUSS über 6,5 liegen — bei saureren Böden funktioniert die Rhizobium-Symbiose nicht. Auf typischen norddeutschen Sandböden pH vor Anbau prüfen und ggf. kalken. Luzerne erschließt durch ihre bis zu 10 m tiefen Pfahlwurzeln Nährstoffe aus Schichten, die andere Pflanzen nicht erreichen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 (sehr trockenheitsresistent) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; verträgt Trockenheit sehr gut; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | — | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | — | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Gründüngungsplan im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Mai | Frühjahrsaussaat | Saatbett gut vorbereiten; pH prüfen; 15–20 g/m²; 1 cm tief | hoch |
| Mär–Apr | Kalkgabe (bei Bedarf) | Kohlensaurer Kalk; 100–200 g/m²; mindestens 4 Wochen vor Aussaat | hoch |
| Jun–Jul (1. Jahr) | Erste Mahd (optional) | Gründüngungssaison; oder wachsen lassen | niedrig |
| Aug–Sep | Einarbeitung (Gründüngung) | Vor Samenreife eingraben; 20–25 cm tief; Mulchen möglich | hoch |
| Sep | Herbstaussaat (Folgekultur) | Nach Einarbeitung 4–6 Wochen warten | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 4 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Luzerneblattkäfer | Hypera postica | Fraßschäden; Larvenfraß innen | leaf, stem | vegetative | medium |
| Blattläuse | Acyrthosiphon pisum | Kolonien; Welke | shoot | spring, summer | easy |
| Kleespitzmaus | Apion spp. | Samenfraß | flower, seed | flowering | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal (Erysiphe pisi) | Weißer Belag | Trockenheit | 5–10 | vegetative |
| Luzernewelke | fungal (Fusarium spp.) | Welken, Wurzelfäule | Staunässe | 14–21 | alle |
| Blattflecken | fungal (Pseudopeziza medicaginis) | Braune Flecken | Feuchte | 7–14 | vegetative |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Fruchtfolge (5–6 Jahre) | cultural | – | Keine Luzerne auf luzernemüdem Boden | 0 | Fusarium |
| pH korrekt einstellen | cultural | – | Kalkung bei pH < 6,5 | 0 | allgemein |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Stickstoff-Fixierer (nitrogen_fixer) |
| Fruchtfolge-Kategorie | Leguminosen (Fabaceae) |
| Empfohlene Vorfrucht | Getreide, Hackfrüchte |
| Empfohlene Nachfrucht | Alle Kulturen; besonders Getreide, Kohl, Rüben |
| Anbaupause (Jahre) | 5–6 Jahre auf gleicher Fläche (Luzernewelke-Prävention) |

### 6.2 N-Hinterlassenschaft für Nachkulturen

| Folgekultur | N-Verfügbar (kg N/ha) | Empfehlung |
|------------|----------------------|------------|
| Winterweizen | 100–200 | Stark reduzierter Düngebedarf |
| Mais | 100–150 | Ideale Vorkultur |
| Kohlrabi/Brokkoli | 120–200 | Sehr starker Effekt |
| Kartoffeln | 80–150 | Rhizoctonia-Risiko prüfen |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Medicago sativa |
|-----|-------------------|-------------|-----------------------------------|
| Rotklee | Trifolium pratense | Gleiche Familie; Gründüngung | Weniger Ansprüche an pH; auch saure Böden; kürzer |
| Inkarnatklee | Trifolium incarnatum | Gleiche Familie | Winterzwischenfrucht; frostgar |
| Weißklee | Trifolium repens | Gleiche Familie | Permanent; Untergrasansaat möglich |
| Gelbsenf | Sinapis alba | Gründüngung | Schnell; kein pH-Problem; nur einjährig |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Medicago sativa,"Luzerne;Ewiger Klee;Alfalfa;Lucerne",Fabaceae,Medicago,perennial,long_day,herb,taproot,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b;10a;10b",-0.1,"Vorderasien, Zentralasien",no,,,90,40,10,no,no,false,false,nitrogen_fixer,true,hardy,"5;6;7;8;9"
```

---

## Quellenverzeichnis

1. [Naturadb Medicago sativa](https://www.naturadb.de/pflanzen/medicago-sativa/) — Steckbrief, Standort
2. [Samen.de Luzerne Gründüngung](https://samen.de/blog/luzerne-der-bodenverbesserer-im-garten.html) — Gründüngungsleistung
3. [Demonet-kleeluzplus Steckbrief Luzerne](https://www.demonet-kleeluzplus.de/mam/cms15/dateien/steckbrief_luzerne.pdf) — N-Fixierung, Anbaudaten
4. [Transgen Luzerne Lexikon](https://www.transgen.de/lexikon-nutzpflanzen/1861.luzerne.html) — Allgemein
