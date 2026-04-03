# Dendrobium-Orchidee, Edle Dendrobie — Dendrobium nobile

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Smart Garden Guide](https://smartgardenguide.com/dendrobium-nobile-orchid-care/), [Gardening Know How](https://www.gardeningknowhow.com/ornamental/orchids/dendrobium-nobile-orchid-care), [UK Houseplants](https://www.ukhouseplants.com/plants/dendrobiums), [Carter & Holmes](https://www.carterandholmes.com/pages/dendrobium-nobile-and-ise-care-sheet), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Dendrobium nobile | `species.scientific_name` |
| Synonyme | Dendrobium nobile var. nobilius (Cultivare im Handel sind meist Hybriden) | — |
| Volksnamen (DE/EN) | Dendrobium-Orchidee, Edle Dendrobie, Bambusorchidee; Noble Dendrobium, Noble Rock Orchid | `species.common_names` |
| Familie | Orchidaceae | `species.family` → `botanical_families.name` |
| Gattung | Dendrobium | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 10–30+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | true | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Kühle Herbst-/Wintertemperaturen (7–15°C) sind für Blütenbildung obligat — ohne Kühlung keine Blüten. | `species.hardiness_detail` |
| Heimat | Nepal, Indien, China, Myanmar, Thailand — Himalaya-Ausläufer, felsige Standorte, Epiphyt | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Dendrobium nobile ist nach Phalaenopsis die zweitbekannteste Zimmerpflanze-Orchidee und unterscheidet sich grundlegend in der Kultur: Sie bildet sympodiale Bulben (Pseudobulben) und benötigt im Herbst/Winter eine ausgeprägte Kühlphase (7–15°C) mit reduzierter Bewässerung — nur dann blüht sie verlässlich im Winter/Frühjahr. Im Handel sind fast ausschließlich Hybridkultivare erhältlich, die etwas robuster als die Wildart sind. Die Blüten erscheinen entlang der Bulben, nicht auf einzelnen Blütenstielen wie bei Phalaenopsis.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 1, 2, 3, 4 (Hauptblütezeit Winter/Frühjahr nach Kühlung) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung alter Bulbenstöcke beim Umtopfen — jede Sektion mit mindestens 2–3 Bulben. Keiki (Ableger auf der Bulbe) können abgetrennt und eingetopft werden sobald eigene Wurzeln entwickelt sind (mind. 3 cm Wurzellänge).

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
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 (verblühte Bulben können nach Blüte belassen werden) | `species.pruning_months` |

**Hinweis:** Alte Bulben NICHT abschneiden — sie dienen als Nährstoffspeicher und können Keiki (Jungpflanzen) entwickeln. Nur wenn Bulben vollständig eingetrocknet sind, können sie entfernt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 1–3 (kleine Töpfe) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–40 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Sommer, nach Eisheiligen, halbschatten) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Orchidenbark-Mix (grobkörnig). pH 5.5–6.5. Kleine Töpfe bevorzugt — eng eingetopft blüht Dendrobium besser. Niemals normale Einheitserde. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktivwachstum / Bulbenentwicklung (Frühling/Sommer) | 150–180 | 1 | false | false | medium |
| Kühlphase / Ruhephase (Herbst/Winter) | 60–90 | 2 | false | false | high |
| Blüte (Winter/Frühjahr) | 45–90 | 3 | true | false | low |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktivwachstum (April–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–22 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 20–28 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| Gießintervall (Tage) | 5–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Kühlphase (Oktober–Dezember — KRITISCH für Blüte)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 150–400 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 10–18 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 7–13 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–120 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte (Januar–April)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Gießintervall (Tage) | 7–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktivwachstum | 20:20:20 ausgewogen | 0.4–0.8 | 5.5–6.5 | 40 | 20 |
| Kühlphase | 0:0:0 | 0.0–0.2 | 5.5–6.5 | — | — |
| Blüte | 0:0:0 | 0.0–0.2 | 5.5–6.5 | — | — |

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideen-Flüssigdünger | Substral | base | 7-5-6 | 3 ml/L (alle 2 Wochen, halbdosiert) | Wachstum |
| Balance-Orchideendünger | Compo | base | 5-5-7 | 2 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornmehl | – | organisch | Nicht empfohlen für Epiphyten | — |

### 3.2 Besondere Hinweise

Leichter Zehrer. Alle 14 Tage April bis September bei halber Empfehlungsdosis. Oktober bis März KEIN Dünger. Ausgewogenes NPK-Verhältnis (20-20-20 oder ähnlich) wird empfohlen. NIEMALS auf trockene Wurzeln düngen — zuerst mit reinem Wasser gießen, dann düngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | soak | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches, kalkfreies Wasser bevorzugt (Regenwasser, RO-Wasser); Topf tauchen bis Blasen aufhören, dann vollständig abtropfen; NIE Staunässe; in der Kühlphase auf fast trocken stellen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Blätter punktförmig | medium |
| Wollschildlaus | Pseudococcus spp. | Wollflecken an Bulben/Blättern | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Braune, weiche Wurzeln | Staunässe, fehlende Drainage |
| Keimi-/Knospenausfall | physiologisch | Knospen fallen ab ohne aufzublühen | Zu warm im Herbst, zugig, Umzug |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Kühlphase einhalten | cultural | Herbst: 10°C Nacht | 0 | Blütenausfall (Prävention) |
| Alkohol 70% | mechanical | Wattestäbchen | 0 | Wollschildläuse, Schildläuse |
| Neemöl | biological | Sprühen 0.3% | 0 | Spinnmilben |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Phalaenopsis | Phalaenopsis spp. | Orchidaceae | Pflegeleichter, kein Kühlbedarf |
| Cymbidium | Cymbidium spp. | Orchidaceae, sympodial | Robuster, auch für draußen |
| Oncidium | Oncidium spp. | Orchidaceae | Häufige Blüten, aromatisch |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Dendrobium nobile,"Dendrobium-Orchidee;Edle Dendrobie;Bambusorchidee;Noble Dendrobium",Orchidaceae,Dendrobium,perennial,day_neutral,herb,aerial,"10a;10b;11a;11b","Nepal, Indien, China, Myanmar",yes,1-3,10,30-60,20-40,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Smart Garden Guide — Dendrobium nobile](https://smartgardenguide.com/dendrobium-nobile-orchid-care/) — Pflegehinweise, Kühlphasen
2. [Gardening Know How — Dendrobium nobile](https://www.gardeningknowhow.com/ornamental/orchids/dendrobium-nobile-orchid-care) — Kulturdaten
3. [UK Houseplants — Dendrobiums](https://www.ukhouseplants.com/plants/dendrobiums) — Schädlinge, Phasen
4. [Carter & Holmes — Nobile Dendrobium](https://www.carterandholmes.com/pages/dendrobium-nobile-and-ise-care-sheet) — Professionelle Pflegekarte
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
