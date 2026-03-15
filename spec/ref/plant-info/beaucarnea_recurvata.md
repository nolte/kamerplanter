# Elefantenfuß, Pferdeschwanzpalme — Beaucarnea recurvata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/ponytail-palm-beaucarnea-recurvata-care-guide-2/), [OurHouseplants](https://www.ourhouseplants.com/plants/ponytailpalm), [Gardenia.net](https://www.gardenia.net/plant/beaucarnea-recurvata-pony-tail-palm), [PLNTS.com](https://plnts.com/en/care/houseplants-family/beaucarnea), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Beaucarnea recurvata | `species.scientific_name` |
| Volksnamen (DE/EN) | Elefantenfuß, Pferdeschwanzpalme, Flaschenpalme; Ponytail Palm, Elephant Foot, Bottle Palm | `species.common_names` |
| Familie | Asparagaceae | `species.family` → `botanical_families.name` |
| Gattung | Beaucarnea | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 50–350+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — toleriert kurze Fröste bis -5°C. Mindesttemperatur 5°C, optimal 15–29°C. Verträgt Kälte und Trockenheit sehr gut. | `species.hardiness_detail` |
| Heimat | Östliches Mexiko (Tamaulipas, San Luis Potosí) — trockene Halbwüste, Felsspalten | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Elefantenfuß ist KEINE Palme (trotz des Namens), sondern ein Verwandter der Agaven. Die verdickte Stammbasis dient als Wasserspeicher — daher kann die Pflanze Wochen ohne Wasser überleben. Extrem langsam wachsend (ca. 15 cm/Jahr unter idealen Bedingungen). In Mexiko werden die Blätter als Viehfutter genutzt und die Pflanze ist wildlebend in Mexico als gefährdet eingestuft.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht erst nach Jahrzehnten; nur bei sehr alten, großen Exemplaren im Freiland) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Ableger (Pups) an der Stammbasis abtrennen (5+ cm groß), Schnittfläche trocknen lassen (1–2 Tage), in trockenes Kakteensubstrat pflanzen. Wurzelbildung in 4–8 Wochen bei 22–26°C. Samen ebenfalls möglich, aber sehr langsam.

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

**Hinweis:** Beaucarnea recurvata ist nicht giftig — ASPCA listet die Pflanze als sicher für Katzen und Hunde.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Abgestorbene Blätter vorsichtig von der Basis abziehen. Blätter niemals schneiden — Enden werden braun und sehen unschön aus.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–15 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 20 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–200 (indoor, sehr langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–100 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (volle Sonne, frostfreie Monate; im Sommer draußen empfehlenswert) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kakteenerde oder Einheitserde mit 50% Perlite/Grobsand. pH 6.5–7.5. Hervorragende Drainage zwingend erforderlich. Tongefäße bevorzugt (verhindert Überwässerung). Kleiner Topf (root-bound ist gut). | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | very high |
| Winterruhe | 120–150 | 2 | false | false | very high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–1000+ | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–45 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–40 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 10–30 | `requirement_profiles.dli_target_mol` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 | 0.3–0.6 | 6.5–7.5 | 40 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.5–7.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen- und Sukkulentendünger | Compo | base | 4-6-7 | 3 ml/L (alle 6–8 Wochen) | Wachstum |
| Kakteen Dünger | Substral | base | 3-6-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Extremer Schwachzehrer. Nur 2–4 Düngergaben pro Wachstumssaison ausreichend. Niemals im Winter düngen. Überdüngung schadet dauerhaft.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser ok; vollständig durchgießen, dann KOMPLETT abtrocknen lassen bis zur nächsten Wässerung | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste (selten) | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Weicher, verfärbter Stammsockel | Überwässerung, Staunässe |
| Blattendfäule | fungal | Braune Blattspitzen | Überwässerung |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Weniger gießen | cultural | Gießintervall erhöhen | 0 | Wurzelfäule (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Yucca | Yucca elephantipes | Asparagaceae, Baumform | Ähnlicher tropischer Look |
| Drachenbaum | Dracaena marginata | Asparagaceae, Baumform | Mehr Blattfarben, kompakter |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Beaucarnea recurvata,"Elefantenfuß;Pferdeschwanzpalme;Flaschenpalme;Ponytail Palm;Elephant Foot",Asparagaceae,Beaucarnea,perennial,day_neutral,tree,tuberous,"9a;9b;10a;10b;11a;11b","Östliches Mexiko",yes,3-15,20,60-200,40-100,yes,yes,false,light_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Ponytail Palm](https://www.healthyhouseplants.com/indoor-houseplants/ponytail-palm-beaucarnea-recurvata-care-guide-2/) — Pflegehinweise
2. [OurHouseplants — Ponytail Palm](https://www.ourhouseplants.com/plants/ponytailpalm) — Detaillierte Kulturdaten
3. [Gardenia.net — Beaucarnea recurvata](https://www.gardenia.net/plant/beaucarnea-recurvata-pony-tail-palm) — Botanische Daten
4. [PLNTS.com — Beaucarnea](https://plnts.com/en/care/houseplants-family/beaucarnea) — Ganzjahrespflege
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
