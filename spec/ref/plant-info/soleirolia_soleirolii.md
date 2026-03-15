# Bubikopf — Soleirolia soleirolii

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [NC State Extension](https://plants.ces.ncsu.edu/plants/soleirolia-soleirolii/), [Epic Gardening](https://www.epicgardening.com/baby-tears-plant/), [Gardenia.net](https://www.gardenia.net/plant/soleirolia-soleirolii-baby-tears-grow-care-tips), [Plantophiles](https://plantophiles.com/plant-care/babys-tears-soleirolia-soleirolii/), [Guide to Houseplants](https://www.guide-to-houseplants.com/babys-tears.html)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Soleirolia soleirolii | `species.scientific_name` |
| Volksnamen (DE/EN) | Bubikopf, Zartmoos; Baby's Tears, Mind-Your-Own-Business, Irish Moss | `species.common_names` |
| Familie | Urticaceae | `species.family` → `botanical_families.name` |
| Gattung | Soleirolia | `species.genus` |
| Ordnung | Rosales | `botanical_families.order` |
| Wuchsform | groundcover | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 9a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kurzfristig bis -5°C; als Bodendecker in milden Regionen winterhart; in Mitteleuropa als Zimmerpflanze gehalten | `species.hardiness_detail` |
| Heimat | Korsika, Sardinien (Westliches Mittelmeer) | `species.native_habitat` |
| Allelopathie-Score | 0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | nicht relevant (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | 3, 4, 5 (im Freiland, Mitteleuropa) | `species.direct_sow_months` |
| Erntemonate | nicht relevant (Zierpflanze) | `species.harvest_months` |
| Blütemonate | 4, 5, 6, 7 (winzige, unscheinbare Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division; cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Teilungsmethode:** Die dichteste und einfachste Methode. Pflanze aus dem Topf nehmen, Wurzelballen in mehrere Teile zerteilen. Jeder Teil kann direkt eingetopft werden. Bewurzelungsrate nahezu 100%.

**Steckling:** Kurze Triebstücke (3–5 cm) ohne Wurzeln auf feuchtes Substrat legen — sie bewurzeln von selbst.

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
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt erforderlich. Übermäßig wachsende Bereiche können jederzeit zurückgestutzt werden.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 0.5–2 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 8 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 5–10 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 20–50 (breitet sich schnell aus) | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 20 (Bodendecker) | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, feuchtigkeitsspeichernde Erde; Torf-/Kompostmischung mit Perlite (3:1); pH 5.5–6.5; feucht aber nicht Staunässe | — |

**Terrarium/Flaschengarten:** Bubikopf ist eine ideale Terrariumpflanze — hohe Luftfeuchtigkeit und gleichmäßige Feuchtigkeit entsprechen seiner natürlichen Bergfelsen-Umgebung (Korsika, Sardinien).

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 14–28 | 1 | false | false | medium |
| Vegetativ | 60–365 | 2 | false | false | medium |
| Blüte (unscheinbar) | 30–60 | 3 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 50–200 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 5–14 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 10–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 16–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 60–80 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 65–85 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.4–0.8 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (Substrat gleichmäßig feucht halten, nie austrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Etablierung | 0:0:0 | 0.0 | 5.5–6.5 | — | — |
| Vegetativ | 2:1:2 | 0.4–0.8 | 5.5–6.5 | 60 | 30 |
| Blüte | 1:1:1 | 0.3–0.6 | 5.5–6.5 | 40 | 20 |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Universaldünger flüssig | Compo | Flüssigdünger | 7-3-6 | 1 ml/L, alle 14d | Vegetativ |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Komposttee (verdünnt) | eigen | organisch | 3 ml/L | Apr–Sep |
| Kompost (beim Umtopfen) | eigen | organisch | 20% Beimischung | Frühling |

### 3.2 Besondere Hinweise zur Düngung

Schwachzehrer — sehr zurückhaltend düngen. Überdüngung führt zu zu rapidem Wachstum und darauffolgendem Kollaps. Maximal alle 3–4 Wochen bei 1/4 bis 1/2 der empfohlenen Dosis.

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | fern | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 1.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | bottom_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Zimmerwarmes, kalkarmes Wasser; täglich einsprühen bei trockener Heizungsluft; niemals austrocknen lassen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 21 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Wenig Wasser | Substrat leicht feucht; kühler Standort bevorzugt | niedrig |
| Mär | Umtopfen/Teilen | Überfüllte Töpfe teilen; frische Erde | hoch |
| Apr–Sep | Aktive Wachstumsphase | Regelmäßig wässern; alle 3 Wochen dünn düngen | mittel |
| Okt–Nov | Reduzieren | Gießintervall leicht verlängern; Dünger einstellen | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none (Zimmer) oder mulch (Freiland) | `overwintering_profiles.winter_action` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Trauermücken | Bradysia spp. | Larven in feuchtem Substrat; Welke | medium |
| Blattläuse | Aphidoidea | Deformierte Triebe, Honigtau | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal (Pythium) | Brauner, matschiger Boden; Welke | Staunässe |
| Austrocknung | physiologisch | Blätter braun, schrumpfen | Substrat zu trocken |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Klebefallen gelb | cultural | — | Klebefalle über Topf | 0 | Trauermücken |
| Neemöl Gießen | biological | Azadirachtin | 0.3% Lösung in Substrat | 3 | Trauermücken-Larven |
| Substrat erneuern | cultural | — | Substrat komplett tauschen | 0 | Wurzelfäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Farne | Nephrolepis exaltata | 0.8 | Gleiche Feuchtigkeitsanforderungen, komplementärer Wuchs | `compatible_with` |
| Fittonia | Fittonia albivenis | 0.9 | Gleiche Feuchtigkeit, schöne Kombination | `compatible_with` |
| Peperomia | Peperomia spp. | 0.6 | Ähnliche Pflegebedürfnisse | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Sukkulenten | diverse | Diametral gegensätzliche Wasseransprüche | severe | `incompatible_with` |
| Kakteen | diverse | Bubikopf braucht konstante Feuchtigkeit, Kakteen nicht | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Moos-Fittonia | Fittonia albivenis | Ähnliche Bodendecker-Wuchsform | Dekorativere Blätter |
| Selaginella | Selaginella martensii | Ähnliche Terrarium-Eignung | Wächst etwas höher, 3D-Effekt |
| Irisches Moos | Sagina subulata | Echter Bodendecker | Für Freiland besser geeignet |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Soleirolia soleirolii,Bubikopf;Baby's Tears;Mind-Your-Own-Business,Urticaceae,Soleirolia,perennial,day_neutral,groundcover,fibrous,9a;9b;10a;10b;11a;11b,0.1,"Korsika, Sardinien",yes,1,8,10,50,yes,limited,false,false
```

---

## Quellenverzeichnis

1. [NC State Extension — Soleirolia soleirolii](https://plants.ces.ncsu.edu/plants/soleirolia-soleirolii/) — Botanische Einordnung, USDA Zone
2. [Epic Gardening — Baby Tears Plant](https://www.epicgardening.com/baby-tears-plant/) — Pflegehinweise
3. [Gardenia.net — Soleirolia soleirolii](https://www.gardenia.net/plant/soleirolia-soleirolii-baby-tears-grow-care-tips) — Kulturdaten
4. [Plantophiles — Soleirolia soleirolii](https://plantophiles.com/plant-care/babys-tears-soleirolia-soleirolii/) — Schädlinge, Krankheiten
5. [Guide to Houseplants — Baby's Tears](https://www.guide-to-houseplants.com/babys-tears.html) — Gießhinweise, Substrate
