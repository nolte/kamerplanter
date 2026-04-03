# Gelbsenf / Weißer Senf — Sinapis alba

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Agrarshop-online Gelbsenf, Samen.de Gelbsenf, Naturadb Sinapis alba, Gartensaatgut.de Gelbsenf

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Sinapis alba | `species.scientific_name` |
| Volksnamen (DE/EN) | Gelbsenf, Weißer Senf; White Mustard, Yellow Mustard | `species.common_names` |
| Familie | Brassicaceae | `species.family` → `botanical_families.name` |
| Gattung | Sinapis | `species.genus` |
| Ordnung | Brassicales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | annual | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 2a–9b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kälteverträglich bis ca. -5°C; stirbt bei Frost ab (Gründüngungseffekt: Biomasse gefriert zu Mulch); Herbstaussaat bis September möglich | `species.hardiness_detail` |
| Heimat | Mittelmeer, Vorderasien | `species.native_habitat` |
| Allelopathie-Score | 0.3 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | true | `species.green_manure_suitable` |

**WICHTIG — Kohlhernie:** Gelbsenf gehört zu den Kreuzblütlern (Brassicaceae) und kann Kohlhernie (Plasmodiophora brassicae) im Boden anreichern! NICHT auf Flächen aussäen, auf denen Kohlgewächse geplant sind. Für Kohlbauern ist Phacelia (Boraginaceae) als Gründüngung besser geeignet.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 0 (Direktsaat; keine Vorkultur) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | -14 (kältetolerante Frühaussaat ab April möglich) | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 4, 5, 6, 7, 8, 9 (Staffelaussaat; letzter Termin Mitte September) | `species.direct_sow_months` |
| Erntemonate | — (Gründüngung wird eingearbeitet; keine Ernte) | `species.harvest_months` |
| Blütemonate | 6, 7, 8, 9 (je nach Aussaatzeitpunkt; gelbe Blüten; Bienenweide) | `species.bloom_months` |

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
| Giftige Pflanzenteile | — (Samen sind Nahrungsmittel; Senfgewürz) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | — | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | true (Senfpollen; Senf-Allergie möglich; Mustard ist großer EU-Allergen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Kreuzblütler-Pollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none (Einarbeitung als Gründüngung vor Samenreife) | `species.pruning_type` |
| Rückschnitt-Monate | 7, 8, 9 (vor Einarbeitung) | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | no | `species.container_suitable` |
| Empf. Topfvolumen (L) | — | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 50–100 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 5–15 (Gründüngung: Breitwurf 2–3 g/m²) | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | — (ausschließlich Freilandkultur) | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 4–10 | 1 | false | false | high |
| Rosetten-Wachstum | 14–21 | 2 | false | false | high |
| Vegetativ | 14–28 | 3 | false | false | high |
| Blüte (Bienenweide) | 14–28 | 4 | true | false | high |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Besondere Hinweise zur Düngung

Als Gründüngungspflanze braucht Gelbsenf keine Düngung. Im Gegenteil: Die Pflanze soll den Boden begrünen und Nährstoffe binden. Ihre Stärke ist die extrem schnelle Keimung und Bodenbegrünung — sie schließt Flächen nach Ernte von Frühgemüse. Senf bindet Nährstoffe im Aufwuchs und gibt sie beim Einarbeiten zurück. Die tiefe Pfahlwurzel lockert den Boden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | — (Regen reicht; keine Bewässerung nötig) | `care_profiles.watering_interval_days` |
| Düngeintervall (Tage) | — (kein Dünger) | `care_profiles.fertilizing_interval_days` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr–Sep | Direktsaat | Breitwurf 2–3 g/m²; einrechen; kein Abdecken | hoch |
| Jun–Aug | Einarbeitung | Vor Samenreife mulchen und einarbeiten (Schlegelmähder/Spaten) | hoch |
| Aug–Sep | Herbst-Nachsaat | Lücken nach Sommerernte begrünen | mittel |
| Nov | Frost-Einarbeitung | Abgestorbene Biomasse in Boden einarbeiten | niedrig |

---

## 5. Schädlinge & Krankheiten

Gelbsenf ist robust und schnellwüchsig. Als Gründüngungskultur ist der Befall kaum relevant.

### 5.1 Relevante Aspekte

- Kohlhernie (Plasmodiophora brassicae): Gelbsenf kann als Wirtspflanze dienen und Kohlhernie-Sporen im Boden anreichern. NICHT vor Kohlgemüse aussäen!
- Kohlweißling (Pieris spp.): Kann Eier auf Gelbsenf legen; als Lockkulturfunktion genutzt.

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Gründüngung (Brassicaceae) |
| Empfohlene Vorfrucht | Starkzehrer (Kürbis, Mais, Kohlrabi) |
| Empfohlene Nachfrucht | Alles AUSSER Kreuzblütler (kein Kohl!); Hülsenfrüchte, Salat, Möhren ideal |
| Anbaupause (Jahre) | 3–4 Jahre vor/nach Kreuzblütlern auf gleicher Fläche |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Phacelia | Phacelia tanacetifolia | 0.8 | Blühende Mischung; Bienenweide | `compatible_with` |
| Buchweizen | Fagopyrum esculentum | 0.8 | Bienenweide; Gründüngungsmix | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Kohl | Brassica oleracea spp. | Gleiche Familie; Kohlhernie-Anreicherung | severe | `incompatible_with` |
| Brokkoli | Brassica oleracea var. italica | Gleiche Familie | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Gelbsenf |
|-----|-------------------|-------------|---------------------------|
| Phacelia | Phacelia tanacetifolia | Gründüngung | Keine Brassicaceae; universal einsetzbar; stärker Nematoden-hemmend |
| Rotklee | Trifolium pratense | Gründüngung | Stickstoff-Fixierung! Langzeit-Wirkung |
| Buchweizen | Fagopyrum esculentum | Gründüngung + Bienenweide | Essbar; Wärmeliebend; anderes Nährstoffprofil |
| Winterraps | Brassica napus | Gleiche Familie | Überwintert; aber Kohlhernie-Risiko |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,direct_sow_months,bloom_months
Sinapis alba,"Gelbsenf;Weißer Senf;White Mustard;Yellow Mustard",Brassicaceae,Sinapis,annual,long_day,herb,taproot,"2a;2b;3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b;9a;9b",0.3,"Mittelmeer, Vorderasien",no,no,no,false,false,light_feeder,true,half_hardy,"4;5;6;7;8;9","6;7;8;9"
```

---

## Quellenverzeichnis

1. [Agrarshop-online Gelbsenf](https://www.agrarshop-online.com/weisser-senf-gelbsenf.php) — Agrarpraxis, Aussaatmengen
2. [Samen.de Gelbsenf Gründüngung](https://samen.de/blog/gruenduengung-mit-senf.html) — Gründüngungspraxis
3. [Naturadb Sinapis alba](https://www.naturadb.de/pflanzen/sinapis-alba/) — Steckbrief
4. [Gartensaatgut.de Gelbsenf](https://www.gartensaatgut.de/anbau-von-krautern/aussaat-und-anbau-gelbsenf/) — Anbauanleitung
