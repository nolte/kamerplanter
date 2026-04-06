# Alpenveilchen — Cyclamen persicum

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/cyclamen-care-guide-how-to-grow-and-maintain-cyclamen-plants/), [Missouri Botanical Garden](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a444), [UK Houseplants](https://www.ukhouseplants.com/plants/cyclamen), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cyclamen persicum | `species.scientific_name` |
| Volksnamen (DE/EN) | Alpenveilchen; Cyclamen, Persian Cyclamen, Florist's Cyclamen | `species.common_names` |
| Familie | Primulaceae | `species.family` → `botanical_families.name` |
| Gattung | Cyclamen | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 3–10 | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true (Sommerdormanz) | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — Knollen überstehen kurze leichte Fröste bis -5°C. Mindesttemperatur 5°C. Bevorzugt kühle Temperaturen (10–18°C) in der Blütezeit. | `species.hardiness_detail` |
| Heimat | Mittelmeerraum, Naher Osten (Türkei, Israel) — felsige Hänge | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Das Alpenveilchen ist eine klassische Winterblüte (Oktober–März) und bevorzugt kühle Temperaturen — im typisch warmen Zimmer (>20°C) geht es schnell ein. Idealer Standort: kühler Fensterplatz (12–16°C), keine direkte Mittagssonne. Nach der Blütezeit zieht es ins Sommer-Dormanzstadium ein (Blätter welken, Knollen im kühlen Keller lagern) und kann im Herbst neu austreiben — allerdings schwieriger als für Anfänger erwartet.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 10, 11, 12, 1, 2, 3 (Herbst bis Frühjahr) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Vermehrung durch Samen möglich aber zeitaufwändig (12–18 Monate bis zur blühfähigen Pflanze). Samen bei Dunkelheit, 18–20°C, Keimung in 4–6 Wochen. Praxistipp: Kaufpflanzen in Gärtnereien sind effizienter.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | tubers (Knollen — stark giftig), leaves, flowers (schwächer) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | saponins (Cyclamin, Cyclamiretin) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** Besonders die Knollen sind giftig und können Erbrechen, Durchfall und Herzrhythmusstörungen verursachen. Aus Reichweite von Haustieren und Kindern halten.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 3, 4, 5 (verblühte Stiele und gilbende Blätter entfernen — drehen, nicht schneiden) | `species.pruning_months` |

**Hinweis:** Verblühte Stiele und gelbe Blätter nicht abschneiden, sondern durch Drehen an der Basis herausreißen — das verhindert, dass Stümpfe faulen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–3 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 12 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 15–30 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 15–30 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (kühler, geschützter Standort, kein Frost, kein Regen) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Hochwertige, gut durchlässige Blumenerde mit 20% Perlite. pH 5.5–6.5. Nicht zu viel Erde über der Knolle (obere Knollenhälfte herausschauen lassen). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Vegetatives Wachstum (Herbst) | 30–60 | 1 | false | false | medium |
| Blütezeit (Winter) | 60–120 | 2 | false | false | low |
| Sommerdormanz (Mai–September) | 120–150 | 3 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum / Blütezeit (Oktober–März)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–14 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.4–0.9 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 4–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Sommerdormanz (Mai–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–150 (kühles Halbdunkel) | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–18 (kühler Keller oder Kühlraum) | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 21–42 (sehr wenig) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 20–50 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetativ/Blüte | 1:2:2 | 0.4–0.8 | 5.5–6.5 | 50 | 20 |
| Sommerdormanz | 0:0:0 | 0.0 | 5.5–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Blühpflanzen-Dünger | Substral | base | 5-8-10 | 2 ml/L (alle 2–3 Wochen) | Blütezeit |
| Zimmerpflanzen-Dünger | Compo | base | 7-3-6 | 2 ml/L | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Beim Umtopfen im Herbst |

### 3.2 Besondere Hinweise

Alle 2–3 Wochen während der aktiven Wachstums-/Blütezeit (Oktober–März), halbe Dosis. Im Sommer (Dormanz) nicht düngen. Stickstoffarme, P-K-reiche Formel für Blütenbildung.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 28–42 (Dormanz — sehr wenig) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 0.2 (Winter = Hauptblütezeit = mehr gießen) | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water (von unten! Wasser NIE auf Knolle/Blattachsen) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; Unterbewässerung von unten (Knolle nicht nass machen — Fäulnis!); Erde zwischen Güssen leicht antrocknen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14–21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 10–3 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 (jedes Jahr im Herbst, Knollen herausnehmen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 7 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung (Sommerdormanz)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | dig_store (nach Blüte einziehen lassen, Knolle trocken lagern) | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 5 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | replant (im Herbst neu einpflanzen) | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 9 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | dark | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Alpenveilchen-Milbe | Phytonemus pallidus | Deformierte Blüten und Blätter, verkümmerte Knospen | difficult |
| Blattläuse | Myzus persicae | Klebrige Blätter, deformierte Triebe | easy |
| Trauermücke | Bradysia spp. | Larven im Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Grauschimmel (Botrytis) | fungal | Grauer Schimmelbelag auf Blüten und Blättern | Nasses Laub, zu feuchte Luft, Staunässe |
| Knollenfäule | fungal | Weiche, braune Knollenbasis | Gießen von oben, Staunässe |
| Fusarium-Welke | fungal | Einseitiges Welken | Belastetes Substrat |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Von unten gießen | cultural | Gießtechnik ändern | 0 | Botrytis, Knollenfäule (Prävention) |
| Gut belüften | cultural | Standort mit Luftzirkulation | 0 | Botrytis (Prävention) |
| Kupfermittel | biological | Sprühen 0.1% | 3 Tage | Botrytis |
| Abgestorbene Blüten entfernen | cultural | Täglich kontrollieren | 0 | Botrytis (Prävention) |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmer-/Balkonpflanze (saisonale Winterblüte).

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Efeu-Alpenveilchen | Cyclamen hederifolium | Gleiche Gattung | Frosthart (USDA 5–9), für den Garten |
| Primel | Primula acaulis | Primulaceae, Winterblüte | Günstiger, einfacher zu halten |
| Kalanchoe | Kalanchoe blossfeldiana | Winterblüte | Pflegeleichter, mehr Farbvielfalt |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Cyclamen persicum,"Alpenveilchen;Cyclamen;Persian Cyclamen",Primulaceae,Cyclamen,perennial,day_neutral,herb,tuberous,"9a;9b;10a;10b;11a","Mittelmeerraum, Naher Osten",yes,0.5-3,12,15-30,15-30,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Cyclamen Care](https://www.healthyhouseplants.com/indoor-houseplants/cyclamen-care-guide-how-to-grow-and-maintain-cyclamen-plants/) — Pflegehinweise, Dormanz
2. [Missouri Botanical Garden — Cyclamen persicum](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=a444) — Botanische Daten
3. [UK Houseplants — Cyclamen](https://www.ukhouseplants.com/plants/cyclamen) — Kulturdaten, Schädlinge
4. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig — Saponine)
