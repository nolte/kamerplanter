# Schmetterlingsorchidee — Phalaenopsis spp.

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [American Orchid Society](https://www.aos.org/orchid-care/care-sheets/phalaenopsis-culture-sheet), [University of Maryland Extension](https://extension.umd.edu/resource/care-phalaenopsis-orchids-moth-orchids), [UConn Extension](https://homegarden.cahnr.uconn.edu/factsheets/orchid-care-and-repotting/), [Orchid Bliss](https://orchidbliss.com/phalaenopsis-orchid-care-for-beginners/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Phalaenopsis spp. | `species.scientific_name` |
| Volksnamen (DE/EN) | Schmetterlingsorchidee, Phalaenopsis; Moth Orchid | `species.common_names` |
| Familie | Orchidaceae | `species.family` → `botanical_families.name` |
| Gattung | Phalaenopsis | `species.genus` |
| Ordnung | Asparagales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Wurzelanpassungen | aerial, epiphytic | `species.root_adaptations` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Typische Lebensdauer (Jahre) | 15–25+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false (kein Vernalisationsreiz im botanischen Sinne; Blüteninduktion durch thermoperiodischen Kühlreiz: Nachttemperatur 13–16°C für 4–6 Wochen im Herbst) | `lifecycle_configs.vernalization_required` |
| USDA Zonen | 10a, 10b, 11a, 11b, 12a | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Mindesttemperatur 10°C, optimal Tages 21–27°C / Nachts 16–19°C. Für Blüteninduktion 4–6 Wochen Nachttemperatur 13–16°C (Herbst) wichtig. | `species.hardiness_detail` |
| Heimat | Tropisches Asien (Indien, China, Südostasien, Australien — epiphytisch auf Bäumen) | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental, fragrant | `species.traits` |

**Hinweis:** Phalaenopsis ist die weltweit meistverkaufte Orchideen-Gattung. Im Handel fast ausschließlich hybride Sortengemische (keine Rein-Arten). Wichtigster Pflegehinweis: Luftwurzeln NICHT in die Erde stecken — sie benötigen Luftzirkulation und Photosynthese (grüne Wurzeln = aktiv, silber = trocken, aber lebendig).

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 11, 12, 1, 2, 3, 4 (Hauptblütezeit Winter/Frühjahr; nach Blüteninduktion Sept–Nov) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | offset (Keikis = Kindpflanzen am Blütenspross) | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis Vermehrung:** Phalaenopsis bildet gelegentlich Keikis (Kindpflanzen) am Blütenspross oder an der Basis. Keikis erst ablösen wenn eigene Luftwurzeln min. 5 cm lang sind. Samenvermehrung ist Laborsache (Mykorrhiza-abhängig) — für Hobbyisten nicht praktikabel. In vitro Gewebekultur professionellen Betrieben vorbehalten.

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
| Pollenallergen | false (Orchideen verbreiten Pollen nicht über Wind, sondern als Pollinien über Insekten; Indoor-Allergierelevanz praktisch null) | `species.allergen_info.pollen_allergen` |

**Hinweis:** Phalaenopsis ist eine der wenigen ungiftigen Zimmerpflanzen — ideal für Haushalte mit Haustieren. Pestizide auf verkauften Pflanzen können aber für Katzen gefährlich sein — neue Orchideen vor Tierkontakt gründlich abwaschen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 4, 5 (nach Ende der Blüte) | `species.pruning_months` |

**Hinweis:** Nach der Blüte zwei Optionen: (1) Blütenspross über dem 2. Knoten abschneiden → fördert Seitentrieb und erneute Blüte (aber schwächer). (2) Blütenspross komplett an der Basis entfernen → Pflanze erholt sich besser, nächste Blüte reichlicher. Option 2 wird für optimale Langzeitgesundheit empfohlen.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 10 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–80 (mit Blütenspross) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–50 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | Entfällt | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | no (zu kälteempfindlich) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Blütenspross mit Bambusstab stützen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Spezielle Orchideenrinde (Pinienrinde, grob, pH 5.5–6.0). Kein normales Substrat! Transparenter Topf bevorzugt (Luftwurzeln brauchen Licht). Orchideen-Kunststofftöpfe mit vielen Löchern ideal. | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Vegetatives Wachstum (Sommer) | 150–180 | 1 | false | false | medium |
| Blüteninduktion (Herbst-Kühlreiz) | 30–45 | 2 | false | false | medium |
| Blütenspross-Entwicklung | 60–90 | 3 | false | false | medium |
| Vollblüte | 60–120 | 4 | false | false | low |
| Regenerationsphase | 60–90 | 5 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetatives Wachstum (Sommer, März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–250 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–12 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 21–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–250 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Blüteninduktion (Herbst, Oktober–November)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 10–14 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 80–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Vollblüte (November–April)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 6–10 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 16–19 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.5–1.0 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–600 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–200 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Vegetatives Wachstum | 3:1:1 (Stickstoff-betont) | 0.6–1.0 | 5.5–6.0 | 80 | 30 |
| Blüteninduktion | 1:3:2 (Phosphor-betont) | 0.4–0.8 | 5.5–6.0 | 60 | 25 |
| Vollblüte | 1:2:1 | 0.4–0.8 | 5.5–6.0 | 60 | 20 |
| Regeneration | 1:1:1 | 0.4–0.6 | 5.5–6.0 | 60 | 25 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Orchideen-spezifisch)

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Orchideen-Dünger | Compo | base | 7-5-6 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Orchideen-Wachstumsdünger | Substral | base | 8-4-7 | 5 ml/L | Wachstum |
| Orchideen-Blütendünger | Compo | bloom booster | 5-12-9 | 5 ml/L | Blüteninduktion |
| Peters Excel Orchid | ICL | base | 30-10-10 | 0.5 g/L | Wachstum (Rindenmix) |

#### Organisch

| Produkt | Marke | Typ | Dosierung | Saison |
|---------|-------|-----|-----------|--------|
| Orchideen-Dünger organisch | Bio Orchid | organisch | 5 ml/L | Wachstum |

### 3.2 Düngungsplan

| Zeitraum | Phase | Düngung | Hinweise |
|----------|-------|---------|----------|
| Mär–Sep | Wachstum | Alle 2 Wochen N-betont | "Weakly, weekly" Prinzip (sehr schwach dosieren) |
| Okt–Nov | Blüteninduktion | Alle 3 Wochen P-betont | Temperatur-Kühlreiz wichtiger als Düngung |
| Nov–Apr | Blüte | Monatlich ausgewogen | Überdüngung verkürzt Blütezeit! |
| Apr–Mai | Regeneration | Alle 3 Wochen ausgewogen | Nach Blütenspross-Entfernung |

### 3.3 Mischungsreihenfolge

1. Weiches Wasser (Osmose oder abgestanden)
2. Orchideen-Dünger
3. Keine pH-Korrektur nötig wenn weiches Wasser (pH sinkt durch Dünger auf ca. 5.5–6.0)

### 3.4 Besondere Hinweise

Orchideen in Rinde brauchen mehr Stickstoff (30-10-10) als in Torf. "Einmal im Monat flush" — einmal monatlich nur mit reinem Wasser gießen bis es aus dem Topf läuft (spült Salzansammlungen aus). Kein Dünger auf trockene Wurzeln — vorher wässern!

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.3 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | soak (Orchidee für 10–15 Min in Wasser tauchen, dann gut abtropfen lassen) | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser (unter 300 ppm) zwingend! Kalkhaltig → braune Blattspitzen, Salzakkumulation in Rinde. Regenwasser oder Osmosewasser ideal. | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 (Wachstum), 21 (Blüte) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 24–36 (wenn Rinde verrottet oder Wurzeln aus Topf drängen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär–Apr | Umtopfen (nach Blüte) | Rinde erneuern, tote Wurzeln entfernen, nächstgrößerer Topf | mittel |
| Mär–Apr | Blütenspross entfernen | Abgeblühten Spross an Basis abschneiden (Regeneration) | mittel |
| Apr–Sep | Aktiv wachsen lassen | Regelmäßig wässern und N-betont düngen | hoch |
| Sep | Kühlreiz vorbereiten | Pflanze ans offene Fenster (Nachttemperatur 13–16°C) | hoch |
| Okt–Nov | Blüteninduktion | Kühleres Fensterbrett ohne direkte Zugluft | hoch |
| Nov–Apr | Blüte genießen | Stabil stellen, nicht umstellen, mäßig wässern | mittel |
| Ganzjährig | Luftwurzeln belassen | Luftwurzeln NICHT in die Erde stecken, nicht abschneiden | hoch |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|------------------------|
| Schmierlaus | Pseudococcus spp. | Watteartige Flecken in Blattachseln, an Wurzeln | leaf, root, flower | easy |
| Spinnmilbe | Tetranychus urticae | Feine Gespinste, silbrige Punkte | leaf | medium |
| Schildlaus | Coccus hesperidum | Braune flache Schilder auf Blättern/Stängeln | leaf, stem | medium |
| Trauermücke | Bradysia spp. | Larven in feuchter Rinde | root | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Phytophthora spp.) | Braun-schwarze, weiche Wurzeln; Pflanze kollabiert | Überbewässerung, Staunässe |
| Botrytis | fungal (Botrytis cinerea) | Braune Flecken auf Blüten, grauer Schimmelbelag | Hohe Luftfeuchte, schlechte Luftzirkulation |
| Bakterielle Fäule | bacterial | Wasserdurchtränte, übelriechende Flecken auf Blättern | Wasser steht in der Blattkrone |
| Crown Rot | bacterial/fungal | Herz der Pflanze fault, Blätter fallen ab | Wasser in der Blattkrone + Kälte |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|-----------|------------|-------|
| Neemöl | biological | Azadirachtin | Sprühen 0.3% (Blüten schützen!) | 0 Tage | Schmierläuse, Spinnmilbe |
| Alkohol 70% | mechanical | Isopropanol | Wattestäbchen | 0 Tage | Schmierläuse, Schildlaus |
| Zimt (Cinnamon) | cultural | Zimtaldehyd | Schnittflächen bestäuben | 0 | Bakterielle Fäule präventiv |
| Systeminsektizid | chemical | Imidacloprid | Stäbchen | 14 Tage | Schmierläuse, Schildlaus |

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

### 6.2 Mischkultur — Gute Nachbarn (Zimmerpflanze)

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen |
|---------|-------------------|----------------------|--------|
| Bromelien | Guzmania spp. | 0.7 | Ähnliche Luft-Feuchtigkeitsanforderungen |
| Farne | Nephrolepis exaltata | 0.7 | Erhöhen Luftfeuchtigkeit in Gruppe |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Dendrobium-Orchidee | Dendrobium spp. | Gleiche Familie | Kompakter, buschiger Wuchs |
| Cattleya-Orchidee | Cattleya spp. | Gleiche Familie | Intensiverer Duft, größere Blüten |
| Cymbidium | Cymbidium spp. | Gleiche Familie | Winterhärter (bis 5°C), eignet sich für kühle Räume |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level
Phalaenopsis spp.,"Schmetterlingsorchidee;Phalaenopsis;Moth Orchid",Orchidaceae,Phalaenopsis,perennial,day_neutral,herb,aerial,"10a;10b;11a;11b;12a",0.0,"Tropisches Asien (epiphytisch)",yes,0.5-2,10,30-80,20-50,yes,no,false,true,light_feeder
```

---

## Quellenverzeichnis

1. [American Orchid Society — Phalaenopsis Culture Sheet](https://www.aos.org/orchid-care/care-sheets/phalaenopsis-culture-sheet) — Kulturempfehlungen
2. [University of Maryland Extension — Phalaenopsis Care](https://extension.umd.edu/resource/care-phalaenopsis-orchids-moth-orchids) — Wachstumsphasen, Düngung
3. [UConn Extension — Orchid Care and Repotting](https://homegarden.cahnr.uconn.edu/factsheets/orchid-care-and-repotting/) — Umtopfen, Substrate
4. [Orchid Bliss — Beginner Care](https://orchidbliss.com/phalaenopsis-orchid-care-for-beginners/) — Praxishinweise
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizitätsdaten (nicht giftig)
