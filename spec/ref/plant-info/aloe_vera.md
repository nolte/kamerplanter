# Aloe vera — Aloe vera

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Old Farmer's Almanac](https://www.almanac.com/plant/aloe-vera), [South Dakota State University Extension](https://extension.sdstate.edu/aloe-vera-houseplant-how), [Bloomscape](https://bloomscape.com/plant-care-guide/aloe/), [ASPCA](https://www.aspca.org/), [Soltech](https://soltech.com/products/aloe-plant-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Aloe vera | `species.scientific_name` |
| Volksnamen (DE/EN) | Echte Aloe, Aloe vera; Aloe Vera, True Aloe, Barbados Aloe | `species.common_names` |
| Familie | Asphodelaceae | `species.family` → `botanical_families.name` |
| Gattung | Aloe | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 5–25+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 9a, 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 4°C (Kälteschäden unter 4°C, Erfrierung unter 0°C), optimal 15–29°C. | `species.hardiness_detail` |
| Heimat | Arabische Halbinsel (Jemen, Oman); weltweite Naturalisierung in trockenen Tropen/Subtropen | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, medicinal | `species.traits` |

**Medizinische Hinweise:** Aloe-vera-Gel (inneres klares Gel) hat nachgewiesene Wirksamkeit bei Verbrennungen 1. und 2. Grades (Cochrane Review). Das äußere Blattgewebe (Latex/Alooin) ist dagegen oral giftig. Viele Fertigprodukte im Handel verwenden Gel nach industrieller Verarbeitung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt (Ableger-Vermehrung standard) | `species.direct_sow_months` |
| Erntemonate | Ganzjährig (Blätter nach Bedarf) | `species.harvest_months` |
| Blütemonate | 4, 5, 6, 7 (selten Indoor, nur bei sehr hellen Standorten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Primäre Methode ist die Ableger-Vermehrung: Kindpflanzen (Pups) an der Mutterpflanzenbasis bei 5–10 cm Höhe ablösen, 1–2 Tage Schnittstelle trocknen lassen, dann in trockenes Kakteensubstrat pflanzen. Samenvermehrung möglich aber langsam.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true (Blattlatex — Gel ist sicher, Latex nicht!) | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves (nur Latex/Alooin im äußeren Blattgewebe; inneres Gel unbedenklich) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | anthraquinones (alooin, aloe-emodin) | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | true (Latex kann Kontaktdermatitis auslösen bei empfindlichen Personen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Symptome bei Verschlucken (Latex):** Starke Diarrhö, Krämpfe, Elektrolytentgleisungen. Bei Tieren: Erbrechen, Durchfall, Lethargie. Das transparente innere Gel ist nicht giftig.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Äußere, abgestorbene oder beschädigte Blätter an der Basis entfernen. Blütenstand nach der Blüte abschneiden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 2–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–90 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–80 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt in DE | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Sommer, windgeschützt, volle Sonne) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kaktus- und Sukkulentenerde oder Einheitserde mit 50% Perlite/Grobsand. Sehr durchlässig — kein Staunasser Topf. Terrakotta-Töpfe ideal für bessere Austrocknung. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | true | very high |
| Winterruhe (Wachstumsstillstand) | 120–150 | 2 | false | true | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–29 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 25–40 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 25–40 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.0–2.5 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–600 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–20 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 8–12 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–18 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 20–35 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 20–35 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 1.2–3.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 28–42 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 1:2:2 (P/K-betont für Sukkulenten) | 0.4–0.8 | 6.0–7.0 | 40 | 15 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Kakteen & Sukkulenten Dünger | Compo | base | 4-6-7 | 3 ml/L (alle 8 Wochen) | Wachstum |
| Kakteen Dünger | Substral | base | 3-6-7 | 3 ml/L (alle 8 Wochen) | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 10% Substratanteil | Umtopfen |

### 3.2 Besondere Hinweise

Aloe vera ist ein extremer Schwachzehrer. Nur 2–3 Düngergaben pro Wachstumssaison. Überdüngung führt zu schnellem, aber weichem, wenig wirkstoffreichem Blattwachstum. Niemals im Winter düngen. Für medizinische Nutzung des Gels minimale Düngung bevorzugen (natürlicherer Wuchs).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | cactus | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 14–21 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 3.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser gut verträglich; Staunässe ist die häufigste Todesursache | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–8 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Apr | Sommer vorbereiten | Standort mit vollem Sonnenlicht wählen oder Balkon | mittel |
| Apr | Gießen reaktivieren | Erste Wassergabe; Substrat auf Austrocknung prüfen | mittel |
| Apr–Jun | Ableger trennen | Kindpflanzen bei 5–10 cm Höhe ablösen | optional |
| Mai–Sep | Balkon möglich | Volle Sonne, windgeschützt; vor Starkregen schützen | optional |
| Sep | Einräumen | Vor ersten Nachtfrösten hereinholen | hoch |
| Okt–Mär | Winterruhe | Sehr wenig gießen, kein Dünger | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Schmierlaus | Pseudococcus spp. | Wollflecken in Blattachseln | leaf, stem | easy |
| Spinnmilbe | Tetranychus urticae | Punkte, Gespinste bei trockener Luft | leaf | medium |
| Wurzelschmierlaus | Rhizoecus spp. | Weißes Pulver an Wurzeln (sichtbar bei Umtopfen) | root | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Phytophthora, Fusarium) | Weiche braune Basis, Blätter werden gelb-braun | Überbewässerung, Staunässe, kalter Standort |
| Blattbasisfäule | bacterial | Weiche, verfärbte Blattbasis, Faulgeruch | Wasser in der Blattkrone + Kälte |
| Aloe Rust | fungal (Phakopsora spp.) | Orangebraune Flecken auf Blättern | Selten Indoor; hohe Luftfeuchtigkeit |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schmierläuse |
| Umtopfen + Austrocknen | cultural | Faule Wurzeln entfernen, 3–5 Tage trocknen vor Rückpflanzen | 0 | Wurzelfäule |
| Staunässe beseitigen | cultural | Topf mit Abzugslöchern; Untersetzer leeren | 0 | Prävention Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze in DE.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Bogenhanf | Dracaena trifasciata | 0.9 | Identische Pflegeanforderungen |
| Kakteen | diverse | 0.9 | Identische Substrat- und Gießanforderungen |
| Echeveria | Echeveria spp. | 0.8 | Gleiche Pflegeanforderungen |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Aloe vera |
|-----|-------------------|-------------|------------------------------|
| Tiger-Aloe | Gonialoe variegata (syn. Aloe variegata) | Verwandte Gattung | Kompakter, dekorativ gefleckte Blätter |
| Spiral-Aloe | Aloe polyphylla | Gleiche Gattung | Spektakuläre Spiralform |
| Haworthia | Haworthiopsis fasciata (syn. Haworthia fasciata) | Ähnliche Wuchsform | Mehr Schattenverträglich, ideal für dunkle Standorte |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Aloe vera,"Echte Aloe;Aloe vera;True Aloe;Barbados Aloe",Asphodelaceae,Aloe,perennial,day_neutral,herb,fibrous,"9a;9b;10a;10b;11a;11b",0.0,"Arabische Halbinsel (Jemen, Oman)",yes,2-10,15,30-90,30-80,yes,yes,false,false,light_feeder
```

---

## Quellenverzeichnis

1. [Old Farmer's Almanac — Aloe Vera](https://www.almanac.com/plant/aloe-vera) — Kulturempfehlungen
2. [South Dakota State University Extension](https://extension.sdstate.edu/aloe-vera-houseplant-how) — Haushaltsnutzung, Pflege
3. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität
4. [Bloomscape — Aloe Care Guide](https://bloomscape.com/plant-care-guide/aloe/) — Pflegehinweise
5. [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/aloe-vera-care-guide-growing-and-maintaining-this-healing-succulent/) — Ganzjahrespflege
