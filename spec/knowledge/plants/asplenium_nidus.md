# Nestfarn — Asplenium nidus

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/birds-nest-fern-care-guide-asplenium-nidus/), [Clemson HGIC](https://hgic.clemson.edu/how-to-grow-and-care-for-birds-nest-fern-asplenium-nidus/), [Planet Natural](https://www.planetnatural.com/birds-nest-fern/), [NC State Extension](https://plants.ces.ncsu.edu/plants/asplenium-nidus/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Asplenium nidus | `species.scientific_name` |
| Volksnamen (DE/EN) | Nestfarn, Vogelnestfarn; Bird's Nest Fern | `species.common_names` |
| Familie | Aspleniaceae | `species.family` → `botanical_families.name` |
| Gattung | Asplenium | `species.genus` |
| Ordnung | Polypodiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–15+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 15°C, optimal 18–27°C. Reagiert empfindlich auf Kälte unter 13°C und Zugluft. | `species.hardiness_detail` |
| Heimat | Tropisches Asien, Australien, Ostafrika — epiphytisch in Baumkronen tropischer Regenwälder | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Luftreinigungs-Score | 0.5 | `species.air_purification_score` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Der Nestfarn ist einer der wenigen Farne, die als robuste Zimmerpflanze bestehen können. Im Gegensatz zu anderen Farnen (z.B. Adiantum) verträgt er auch mal ein Vergessen beim Gießen. Die trichterförmige Blattrosette sammelt natürlich Wasser und organisches Material — daher die Bezeichnung "Vogelnest". Wichtig: Wasser niemals direkt in die Mitte gießen (Fäulnis-Gefahr). Die zuerst aufrollenden Blattwedel sind extrem empfindlich — niemals berühren.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (Farne blühen nicht — Vermehrung über Sporen) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | spore | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Ausschließlich über Sporen (braune Sporenlager unter den Wedeln). Sporen auf steriles feuchtes Torfsubstrat aufstreuen, mit Klarsichtfolie abdecken, bei 22–24°C halten. Nach 4–6 Wochen Protallen sichtbar; nach 3–6 Monaten erste echte Wedel. Sehr langsam. Teilung ist bei monotypischen Rosetten nicht möglich. Im Handel werden Pflanzen vegetativ via Gewebezucht (Meristeming) vermehrt.

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
| Pollenallergen | true (Sporen können bei Farnsporen-Allergikern reagieren) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Abgestorbene Wedel an der Basis entfernen. Niemals junge, aufrollende Wedel beschädigen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–8 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–80 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–80 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, feuchtigkeitshaltende aber gut durchlässige Farnerde: Einheitserde mit 20% Perlite + 20% Torf oder Kokoserde. pH 5.5–7.0. Epiphytensubstrat mit Pinienrinde ist ebenfalls geeignet. Kein schweres, kompaktes Substrat. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 3–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.2–0.6 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Luftfeuchtigkeit Tag (%) | 55–75 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 2:1:2 | 0.4–0.8 | 5.5–7.0 | 70 | 25 |
| Winterruhe | 0:0:0 | 0.0 | 5.5–7.0 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Farn- und Palmendünger | Compo | base | 7-4-5 | 3 ml/L (halbe Dosis, alle 4 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 3 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Alle 4–6 Wochen April bis August — halbe Dosierung! Farne sind sehr salzempfindlich. Kein Dünger September bis März. Fluorid im Wasser schadet (Blattspitzenverbrennung) — weiches, kalkfreies Wasser empfohlen. Nie Düngerlösung direkt in die Blatttrichter gießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser bevorzugt; NICHT in die Blattmitte gießen! Vom Rand her wässern. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 42 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 18–24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben | medium |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Stielen | medium |
| Trauermücke | Bradysia spp. | Larven in feuchtem Substrat | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Herzfäule | fungal | Braun-matschige Blattmitte, Fäulnisgeruch | Wasser in der Blatttrichter |
| Wurzelfäule | fungal | Welke, gelbe Wedel | Staunässe |
| Blattflecken | fungal/bacterial | Braune Flecken | Nasse Blätter, schlechte Luftzirkulation |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Nie in Mitte gießen | cultural | Gießtechnik ändern | 0 | Herzfäule (Prävention) |
| Neemöl | biological | Sprühen 0.3% | 0 Tage | Spinnmilbe, Schildlaus |
| Gelbtafeln | mechanical | Aufhängen | 0 | Trauermücke |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Wellenblättriger Nestfarn | Asplenium nidus 'Crispy Wave' | Gleiche Art | Gewellte Wedel, dekorativ |
| Lanzettfarn | Asplenium scolopendrium | Gleiche Gattung | Winterharter (für Außenbereich) |
| Schwertfarn | Nephrolepis exaltata | Verschiedene Familie | Robuster, einfacher zu vermehren |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level,air_purification_score
Asplenium nidus,"Nestfarn;Vogelnestfarn;Bird's Nest Fern",Aspleniaceae,Asplenium,perennial,day_neutral,herb,fibrous,"11a;11b;12a","Tropisches Asien, Australien, Ostafrika",yes,2-8,15,30-80,30-80,yes,no,false,light_feeder,0.5
```

### 8.2 Cultivar CSV-Zeilen

```csv
name,parent_species,traits,seed_type
Crispy Wave,Asplenium nidus,"ornamental;wavy_fronds;compact",clone
Osaka,Asplenium nidus,"ornamental;narrow_fronds;upright",clone
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Bird's Nest Fern](https://www.healthyhouseplants.com/indoor-houseplants/birds-nest-fern-care-guide-asplenium-nidus/) — Pflegehinweise, Schädlinge
2. [Clemson HGIC — Asplenium nidus](https://hgic.clemson.edu/how-to-grow-and-care-for-birds-nest-fern-asplenium-nidus/) — Kulturdaten
3. [Planet Natural — Bird's Nest Fern](https://www.planetnatural.com/birds-nest-fern/) — Pflegehinweise
4. [NC State Extension — Asplenium nidus](https://plants.ces.ncsu.edu/plants/asplenium-nidus/) — Botanische Daten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
