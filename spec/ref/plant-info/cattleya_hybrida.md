# Cattleya-Orchidee — Cattleya hybrida

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [American Orchid Society — Cattleya Culture Sheet](https://www.aos.org/orchid-care/care-sheets/cattleya-culture-sheet), [AOS — Cattleya Culture Part 1](https://www.aos.org/all-abour-orchids/cattleya-culture-part-1), [Smithsonian Gardens — Cattleya Care](https://gardens.si.edu/collections/plants/orchids/orchid-care-sheets/cattleya/), [Orchid Bliss — Cattleya](https://orchidbliss.com/cattleya/), [OrchidWeb](https://www.orchidweb.com/orchid-care/cattleya-alliance-orchid-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Cattleya hybrida | `species.scientific_name` |
| Volksnamen (DE/EN) | Cattleya-Orchidee, Korsagen-Orchidee; Corsage Orchid, Queen of Orchids | `species.common_names` |
| Familie | Orchidaceae | `species.family` → `botanical_families.name` |
| Gattung | Cattleya | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 10a–12b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhärte-Detail | Nicht frosthart; Mindesttemperatur 10°C Nacht; Temperaturabfall Tag/Nacht essentiell für Blühinduktion | `species.hardiness_detail` |
| Heimat | Mittel- und Südamerika (tropische Wälder, Epiphyt) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Hinweis zu Hybriden:** Cattleya hybrida umfasst Tausende eingetragener Hybriden, entstanden durch Kreuzungen innerhalb der Cattleya-Alliance (Cattleya, Laelia, Sophronitis, Rhynchlaelia u.a.). Blütezeit, Farbe und Größe variieren stark nach Sorte. Die hier beschriebenen Pflegewerte gelten für Standard-Zimmerkulturhybriden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | nicht relevant | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | sortenabhängig; typisch 2, 3, 4, 10, 11 (Frühjahr/Herbst) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division; offset | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Teilung:** Bei größeren Exemplaren Rhizom mit scharfem, sterilem Messer zwischen den Pseudobulben teilen. Jeder Teil muss mindestens 3–4 Pseudobulben haben. Schnittstellen mit Holzkohlepulver oder Zimt bestäuben. Bewurzelung in Orchideensubstrat bei 22–25°C.

**Keiki:** Manche Hybriden bilden Keikis (Kindpflanzen) auf alten Pseudobulben. Erst trennen wenn eigene Wurzeln >3 cm vorhanden.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | variabel (nach Blüte) | `species.pruning_months` |

**Hinweis:** Verblühten Blütenstiel an der Basis abschneiden. Ältere Pseudobulben (Backbulbs) können belassen werden — sie speichern Reservestoffe. Nur vollständig eingeschrumpfte Pseudobulben entfernen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–5 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 20–60 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | nicht relevant | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | true | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Grobes Orchideensubstrat: Kiefernrinde (Gr. 1–2 cm) + Perlit (30%) + Torfmoos (20%); pH 5.5–6.5; exzellente Drainage und Belüftung obligatorisch | — |

**Topfmaterial:** Terrakotta oder speziell gelochte Orchideentöpfe bevorzugt — fördert schnellere Austrocknung und optimale Wurzelbelüftung (Luftwurzeln benötigen Sauerstoff).

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Bewurzelung/Etablierung | 30–60 | 1 | false | false | low |
| Vegetativ (Pseudobulben-Aufbau) | 90–180 | 2 | false | false | medium |
| Winterruhe/Blüteinduktion | 42–60 | 3 | false | false | medium |
| Blüte | 21–60 | 4 | false | true | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–1200 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–10 (nach Trocknungszyklus: gründlich gießen, dann vollständig abtrocknen lassen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe/Blüteinduktion

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–13 (kritisch für Blühinduktion!) | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 45–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–350 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Etablierung | 1:1:1 | 0.4–0.6 | 5.5–6.5 | 60 | 30 |
| Vegetativ | 3:1:2 | 0.6–1.2 | 5.5–6.5 | 100 | 50 |
| Winterruhe | 0:0:0 | 0.0 | 5.5–6.5 | — | — |
| Blüte | 1:2:2 | 0.4–0.8 | 5.5–6.5 | 80 | 40 |

**"Schwach aber oft" Prinzip (weakly weekly):** Cattleyen bekommen am besten wöchentlich eine sehr schwache Düngelösung (1/4 der empfohlenen Dosis) anstatt monatlich eine starke Gabe.

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Bedingungen |
|------------|---------|-------------|
| Vegetativ → Winterruhe | seasonal | Oktober; Tagtemperatur sinkt; Nachttemperatur auf 10–13°C |
| Winterruhe → Blüte | conditional | Scheidenscheide sichtbar, aufquellend |
| Blüte → Vegetativ | event_based | Blüten verblüht |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Orchideen)

| Produkt | Marke | Typ | NPK | Dosierung | Mischpriorität | Phasen |
|---------|-------|-----|-----|-----------|-----------------|--------|
| Orchideen-Dünger flüssig | Substral | Spezialdünger | 5-5-7 | 3 ml/L (1/4 Dosis) | 1 | Vegetativ |
| ProTek Orchid | Peters Professional | Orchideendünger | 20-20-20 | 0.5 g/L | 1 | Vegetativ |
| Cal-Mag | diverse | Supplement | — | 1 ml/L | 2 | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Fischhydrolysat (verdünnt) | Plagron | organisch | 0.5 ml/L | Wachstumsphase |

### 3.2 Besondere Hinweise zur Düngung

**Kein Dünger auf trockene Wurzeln:** Immer erst gründlich wässern, dann nach einigen Stunden dünn düngen. Trockene Wurzeln plus Düngelösung = Wurzelbrand.

**Flussprinzip:** Cattleyen in Töpfen müssen regelmäßig "gespült" werden (alle 3–4 Monate mit klarem Wasser durchfluten ohne Dünger), um Salze auszuwaschen. Salzanreicherung im Substrat schädigt Luftwurzeln.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Kalkfreies, zimmerwarmem Wasser (>20°C); Regenwasser, destilliertes Wasser oder RO-Wasser optimal; nie unter 15°C | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7 (sehr schwach) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Blüte (wenn induziert) | Blüten genießen; wenig Wasser; keine Dünger | mittel |
| Mär | Frühjahrs-Repot | Alle 2 Jahre umtopfen in frisches Substrat | mittel |
| Apr–Sep | Vegetative Phase | Regelmäßig gießen (trocknen lassen), wöchentlich schwach düngen | hoch |
| Okt | Blüteinduktion | Nachttemperatur auf 10–13°C senken; Gießen reduzieren; kein Dünger | hoch |
| Nov–Jan | Kühlphase | Nachttemperatur kalt; Blütenansatz beobachten | mittel |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (kühler, heller Winterstandort) | `overwintering_profiles.winter_action` |
| Winterquartier Temp min (°C) | 10 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 18 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Schildläuse | Coccoidea | Braune Schuppen, Honigtau | leaf, pseudobulb | medium |
| Wollläuse | Planococcus citri | Weiße Wollmasse, Honigtau | stem, root | easy |
| Thripse | Thysanoptera | Silbrige Streifung auf Blütenblättern | flower | medium |
| Schnecken | Gastropoda | Fraßspuren an Wurzeln und Trieben | root, new_growth | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Schwarzfäule | fungal (Phytophthora, Pythium) | Schwarze Flecken, Triebschwarzfärbung | Staunässe, kaltes Wasser |
| Blattflecken | fungal (Cercospora) | Gelbliche, eingesunkene Flecken | Hohe Feuchtigkeit + schlechte Belüftung |
| Viruserkrankungen | viral (ORSV, CymMV) | Mosaik-Muster auf Blättern, Blütenverfärbung | Kontaktübertragung durch Werkzeug |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Cryptolaemus montrouzieri | Wollläuse | 3–5 Tiere/Pflanze | 14–21 |
| Metaphycus helvolus | Schildläuse | 5–10 | 21–28 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Isopropanol 70% | mechanical | Isopropylalkohol | Wattestäbchen | 0 | Schildläuse, Wollläuse |
| Neemöl | biological | Azadirachtin | Sprühen 0.5% | 3 | Thripse, Schildläuse |
| Werkzeug sterilisieren | cultural | Isopropanol/Feuer | Nach jedem Schnitt | 0 | Virusübertragung |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Phalaenopsis | Phalaenopsis spp. | 0.6 | Gleiche Familie; etwas anderen Pflegeansprüchen | `compatible_with` |
| Dendrobium | Dendrobium nobile | 0.8 | Gleiche Familie; ähnliche Pflegebedingungen | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sukkulenten | diverse | Cattleya braucht höhere Luftfeuchtigkeit | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Phalaenopsis | Phalaenopsis spp. | Gleiche Familie | Einfacher zu pflegen; länger blühend |
| Dendrobium | Dendrobium nobile | Gleiche Familie, ähnliche Blütenpracht | Verträgt trockenere Luft |
| Epidendrum | Epidendrum radicans | Gleiche Familie | Robuster, blüht öfter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Cattleya hybrida,Cattleya-Orchidee;Korsagen-Orchidee;Corsage Orchid,Orchidaceae,Cattleya,perennial,day_neutral,herb,aerial,10a;10b;11a;11b;12a;12b,0.0,"Mittel- und Südamerika",yes,3,15,60,60,yes,limited,true,true
```

### 8.2 Cultivar CSV-Zeilen (bekannte Sorten)

```csv
name,parent_species,traits,days_to_maturity,disease_resistances,seed_type
Pot Paradiso 'Free Spirit',Cattleya hybrida,compact;fragrant;purple_white,365,–,cultivar
Blc. Pamela Hetherington 'Coronation' FCC/AOS,Cattleya hybrida,award_winning;fragrant;yellow,365,–,cultivar
```

---

## Quellenverzeichnis

1. [American Orchid Society — Cattleya Culture Sheet](https://www.aos.org/orchid-care/care-sheets/cattleya-culture-sheet) — Grundlegende Kulturdaten
2. [AOS — Cattleya Culture Part 1](https://www.aos.org/all-abour-orchids/cattleya-culture-part-1) — Licht, Temperatur, PPFD
3. [Smithsonian Gardens — Cattleya Care](https://gardens.si.edu/collections/plants/orchids/orchid-care-sheets/cattleya/) — Pflegehinweise
4. [Orchid Bliss — Cattleya Guide](https://orchidbliss.com/cattleya/) — Blüteinduktion, Temperatur
5. [OrchidWeb — Cattleya Alliance Care](https://www.orchidweb.com/orchid-care/cattleya-alliance-orchid-care) — Schädlinge, Krankheiten
