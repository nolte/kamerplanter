# Spanisches Moos — Tillandsia usneoides

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Gardenia.net – Tillandsia usneoides](https://www.gardenia.net/plant/tillandsia-usneoides-spanish-moss), [Missouri Botanical Garden – Tillandsia usneoides](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=f427), [USDA Plant Guide – Tillandsia usneoides](https://plants.usda.gov/DocumentLibrary/plantguide/pdf/pg_tius.pdf), [Air Plant City – Care Guide](https://www.airplantcity.com/pages/air-plant-care)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Tillandsia usneoides | `species.scientific_name` |
| Volksnamen (DE/EN) | Spanisches Moos, Louisianamoos; Spanish Moss, Old Man's Beard | `species.common_names` |
| Familie | Bromeliaceae | `species.family` → `botanical_families.name` |
| Gattung | Tillandsia | `species.genus` |
| Ordnung | Poales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | aerial | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 8a–11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Kurze Fröste bis -5°C möglich; in Mitteleuropa Zimmer/Gewächshaus | `species.hardiness_detail` |
| Heimat | Südosten USA, Mexiko, Mittel- und Südamerika, Karibik | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Biologische Besonderheit:** Epiphytische Bromeliade ohne funktionale Wurzeln — nimmt Wasser und Nährstoffe ausschließlich über spezialisierte Trichome (Schuppenhaare) auf. Kein Substrat erforderlich. Parasitiert keine Wirtsbäume — nur mechanische Befestigung.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Zimmerpflanze) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (kleine, duftende gelblich-grüne Blüten) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine bekannt | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Wichtiger Hinweis:** In der Natur kann Spanisches Moos als Lebensraum für Bisse verursachende Insekten (Chiggers, Redbugs) dienen — keine Toxizität der Pflanze selbst.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | — (kein Substrat nötig; Aufhängen) | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | — | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–600 (hängend, je nach Bedingungen) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 10–30 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | — | `species.spacing_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true | `species.support_required` |
| Substrat-Empfehlung (Topf) | Kein Substrat! Aufhängen an Ästen, Drahtrahmen oder dekorativen Trägern; gute Luftzirkulation unbedingt erforderlich | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Etablierung | 14–30 | 1 | false | false | low |
| Vegetativ (Wachstum) | 180–270 | 2 | false | false | medium |
| Blüte | 30–60 | 3 | false | false | medium |
| Ruhephase | 90–120 | 4 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Wachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–14 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 13–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–75 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 60–80 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 (Tauchbad 20–30 Min. 1×/Woche oder Sprühen 2–3×/Woche) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 100–300 (Tauchen, dann vollständig trocknen!) | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Vegetativ | 1:1:1 | 0.1–0.3 | 5.5–7.0 | 20 | 10 | — | 0.5 |
| Blüte | 0:1:1 | 0.1–0.2 | 5.5–7.0 | 15 | 10 | — | 0.3 |
| Ruhephase | 0:0:0 | 0.0 | — | — | — | — | — |

### 2.4 Phasenübergangsregeln

| Von → Nach | Trigger | Tage/GDD | Bedingungen |
|------------|---------|----------|-------------|
| Etablierung → Vegetativ | time_based | 14–30 Tage | Neues Wachstum sichtbar |
| Vegetativ → Blüte | time_based | 180–270 Tage | Frühsommer |
| Blüte → Ruhephase | time_based | 30–60 Tage | Herbst |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch (Indoor)

| Produkt | Marke | Typ | NPK | EC/ml/L | Mischpriorität | Phasen |
|---------|-------|-----|-----|---------|-----------------|--------|
| Orchideendünger (stark verdünnt) | Substral | base | 5-5-5 | 1/4 Normaldosis | 1 | vegetativ |
| Air Plant Fertilizer | Tillandsia-Spezial | base | 17-8-22 | 1/4 Normaldosis | 1 | vegetativ |

### 3.2 Düngungsplan

| Monat | Phase | EC (mS) | Hinweise |
|-------|-------|---------|----------|
| Apr–Sep | Vegetativ | 0.1–0.3 | Alle 2–4 Wochen beim Tauchen, stark verdünnt |
| Okt–Mär | Ruhephase | 0.0 | Kein Dünger |

### 3.3 Besondere Hinweise zur Düngung

Tillandsia usneoides nimmt alle Nährstoffe über spezialisierte Trichome (Schuppenhaare) auf Blatt- und Stängeloberfläche auf — **nie in Substrat düngen** (kein Substrat vorhanden). Düngerlösung beim Tauchbad verwenden: 1/4 der empfohlenen Dosis eines Bromelien- oder Orchideendüngers ins Tauchwasser geben. Nach dem Tauchen muss die Pflanze vollständig trocknen (max. 4 Stunden) — Nasse Pflanze in schlecht belüfteter Position fault!

---

## 4. Pflegehinweise

### 4.1 Care-Profil (KA CareProfile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | orchid | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3 (Sprühen 2–3×/Woche oder Tauchen 1×/Woche; bei niedriger Luftfeuchte <50% häufiger) | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | soak | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Weiches Wasser oder Regenwasser; kein chloriertes Leitungswasser; nach dem Tauchen vollständig trocknen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 28 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (kein Topf) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 21 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Jan–Feb | Winterpflege | Gießintervall erhöhen, Tauchbad 1x/Monat | niedrig |
| Mär | Frühjahrspflege | Häufigeres Tauchen (2x/Monat), Licht erhöhen | mittel |
| Apr | Düngung | Beim Tauchen Dünger beimengen | mittel |
| Mai–Sep | Wachstum | 1–2x/Woche Tauchen oder Besprühen + 1x/Monat Tauchen | hoch |
| Okt | Einwintern | Gießen reduzieren | mittel |
| Nov–Dez | Ruhephase | Minimal Tauchen (1x/Monat) | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | needs_protection | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | move_outdoors | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 20 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Spinnmilben | Tetranychus urticae | Feine Gespinste, Trichome beschädigt | stem, leaf | alle | medium |
| Wollläuse | Pseudococcus spp. | Weißer Wollbelag | stem | alle | medium |
| Schildläuse | Coccus spp. | Braune Schuppen | stem | alle | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|-------------------|
| Fäule (Braun/Schwarz) | fungal/bacterial | Braune, weiche Bereiche | wet_no_airflow, too_long_wet | 3–7 | alle |

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Phytoseiulus persimilis | Spinnmilben | 20–50 | 14 |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Tauchbad mit Insektizid-Seife | biological | Kaliseife | Tauchen 30 Min. in 1% Lösung | 0 | Spinnmilben, Wollläuse |
| Luftzirkulation verbessern | cultural | — | Ventilator, weniger dichte Aufhängung | 0 | Fäule |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Schwachzehrer |
| Fruchtfolge-Kategorie | Zimmerpflanze, Epiphyt |
| Anbaupause (Jahre) | — |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Air Plants | Tillandsia ionantha | 0.9 | Gleiche Pflege, gleiche Familie | `compatible_with` |
| Orchideen | Phalaenopsis spp. | 0.7 | Ähnliche Licht-/Luftfeuchtebedürfnisse | `compatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Tillandsia usneoides |
|-----|-------------------|-------------|------------------------------|
| Veilchen-Tillandsie | Tillandsia ionantha | Gleiche Gattung | Kompakter, bunte Blüten |
| Ionantha | Tillandsia cyanea | Gleiche Gattung | Einfacher zu handhaben |
| Guzmania | Guzmania lingulata | Gleiche Familie | Topf-kultivierbar |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required
Tillandsia usneoides,Spanisches Moos;Louisianamoos;Spanish Moss,Bromeliaceae,Tillandsia,perennial,day_neutral,herb,aerial,8a;8b;9a;9b;10a;10b;11a;11b,0.0,Südosten USA Mittelamerika,yes,0,0,600,30,—,yes,limited,false,true
```

---

## Quellenverzeichnis

1. [Gardenia.net – Tillandsia usneoides](https://www.gardenia.net/plant/tillandsia-usneoides-spanish-moss) — Care Guide
2. [Missouri Botanical Garden – Tillandsia usneoides](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?kempercode=f427) — Botanik
3. [USDA Plant Guide – Tillandsia usneoides](https://plants.usda.gov/DocumentLibrary/plantguide/pdf/pg_tius.pdf) — Wissenschaftlich fundiert
4. [Air Plant City – Care Guide](https://www.airplantcity.com/pages/air-plant-care) — Tillandsia Care
5. [Houseplant Central – Tillandsia usneoides](https://houseplantcentral.com/tillandsia-usneoides-care-info/) — Indoor Care
