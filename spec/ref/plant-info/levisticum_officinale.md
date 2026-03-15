# Liebstöckel — Levisticum officinale

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Naturadb Levisticum officinale, Plantura Liebstöckel, Samen.de Liebstöckel, Lubera Liebstöckel

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Levisticum officinale | `species.scientific_name` |
| Volksnamen (DE/EN) | Liebstöckel, Maggikraut, Suppengrün; Lovage | `species.common_names` |
| Familie | Apiaceae | `species.family` → `botanical_families.name` |
| Gattung | Levisticum | `species.genus` |
| Ordnung | Apiales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | taproot | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -25°C; oberirdische Teile sterben im Winter ab; Wurzeln überdauern sicher; in ganz Norddeutschland problemlos | `species.hardiness_detail` |
| Heimat | Südwestasien (Iran, Afghanistan); eingebürgert in Mitteleuropa | `species.native_habitat` |
| Allelopathie-Score | -0.1 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

**Wichtig:** Apiaceae — enthält Furanocumarine (phototoxisch bei Kontakt mit Pflanzensäften im Sonnenlicht). Beim Ernten Handschuhe empfehlenswert.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 8–10 | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | 0 | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 3, 4, 8, 9 | `species.direct_sow_months` |
| Erntemonate | 4, 5, 6, 7, 8, 9 (junge Triebe und Blätter; Samen August–September) | `species.harvest_months` |
| Blütemonate | 6, 7, 8 | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed, division | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine (essbar; in großen Mengen photosensiblisierend) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Furanocumarine (phototoxisch bei Hautkontakt + Sonne, nicht bei oraler Aufnahme in normalen Mengen) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Furanocumarine; phototoxische Dermatitis möglich) | `species.allergen_info.contact_allergen` |
| Pollenallergen | true (Apiaceae-Pollen) | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 8, 9, 3 | `species.pruning_months` |

**Hinweis:** Blütenstände abschneiden, wenn keine Samengewinnung gewünscht — verhindert Verwilderung durch Selbstaussaat. Im März altes Laub bodennah entfernen. Liebstöckel treibt jedes Jahr kräftiger aus — großer Platz einplanen (ca. 1 m²/Pflanze).

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 30–50 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 50 (tiefe Pfahlwurzel) | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 100–200 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80–100 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (Blütenstände können bei Wind umknicken) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, tiefgründige Erde; pH 6,5–7,5; kein Staunässe; große Pflanzgefäße nötig | — |

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Keimung | 14–21 | 1 | false | false | low |
| Sämling (1. Jahr) | 60–90 | 2 | false | false | medium |
| Vegetativ (ab 2. Jahr) | 60–90 | 3 | false | true | high |
| Blüte & Samenreife | 42–60 | 4 | false | true | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Vegetativ (Hauptwachstum)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 250–500 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 18–28 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 15–22 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 8–15 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–75 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Keimung | 0:0:0 | 0.0 | 6.5 | – | – | – | – |
| Sämling | 1:1:1 | 0.5–0.8 | 6.5 | 60 | 30 | – | 1 |
| Vegetativ | 2:1:1 | 1.0–1.4 | 6.5–7.0 | 100 | 50 | – | 2 |
| Blüte/Samen | 1:2:2 | 0.8–1.2 | 6.5–7.0 | 80 | 40 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März–April | Frühjahrsstart |
| Kompost gut verrottet | eigen | organisch | 3–5 L/m² | März, Oktober | Bodenverbesserung |
| Kräuter-Langzeitdünger | Neudorff Azet | organisch | 50 g/m² | April | medium_feeder |
| Brennnessel-Jauche | selbst hergestellt | organisch | 1:10 verdünnt; 1–2×/Saison | Mai, Juli | Stickstoffboost |

### 3.2 Besondere Hinweise zur Düngung

Liebstöckel ist ein kräftiger Mittelzehrer mit hohem Stickstoffbedarf für die üppige Blattmasse. Im ersten Jahr reicht Kompost; ab dem zweiten Jahr zweimal jährlich organisch düngen (Frühjahr + nach erster Ernte). Keine mineralische Stickstoffdüngung — fördert zu weiches Gewebe. Liebstöckel profitiert besonders von Hornspänen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_annual_veg | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 5 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; feuchter Boden gewünscht (nicht trocken); kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | — (Freilandstaude; nicht umtopfen nötig) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Rückschnitt | Altes Laub bodennah entfernen; Neuaustrieb beginnt | hoch |
| Mär–Apr | Erste Düngung | Kompost + Hornspäne einarbeiten | hoch |
| Apr–Jun | Erste Ernte | Junge Triebe und Blätter; immer nur 1/3 der Pflanze | mittel |
| Jun | Blütenstand entfernen | Falls keine Samengewinnung; fördert Blattwachstum | mittel |
| Jul | Zweite Düngung | Flüssigdünger oder Jauche | niedrig |
| Aug–Sep | Samengewinnung | Blütendolden ernten bei Reife (leicht braun) | niedrig |
| Okt | Mulchen | Kompostschicht 5 cm; Winterschutz für Wurzeln | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | mulch | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen; Wachstumshemmung | shoot | vegetative | easy |
| Schnecken | Arion spp. | Fraß an Jungpflanzen | leaf, stem | seedling | easy |
| Sellerieblattmotte | Depressaria radiella | Miniertunnel in Blättern | leaf | vegetative | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal | Weißer Belag | Trockenheit | 7–10 | vegetative (Spätsommer) |
| Blattflecken | fungal (Septoria spp.) | Gelblich-braune Flecken | Feuchte | 5–10 | vegetative |
| Wurzelfäule | fungal (Phytophthora) | Welke; braune Wurzeln | Staunässe | 14–21 | alle |

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Neemöl | biological | Azadirachtin | 0.5% sprühen | 3 | Blattläuse, Motte |
| Schmierseife | biological | Kaliumpalmitat | 1% sprühen | 1 | Blattläuse |
| Schneckenbarriere | cultural | – | Kupferband oder Schneckenkorn | 0 | Schnecken |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Doldenblütler (Apiaceae) |
| Empfohlene Vorfrucht | Leguminosen oder Gründüngung |
| Empfohlene Nachfrucht | Starkzehrer (Kohl) profitieren vom Humus-Aufbau |
| Anbaupause (Jahre) | 3–4 Jahre Apiaceae auf gleicher Fläche |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Tomate | Solanum lycopersicum | 0.8 | Soll Tomatenaroma verbessern; Apiaceaen-Duft verwirrt Schädlinge | `compatible_with` |
| Salat | Lactuca sativa | 0.7 | Liebstöckel spendet Schatten | `compatible_with` |
| Lilien | Lilium spp. | 0.7 | Tiefes Wurzelsystem ergänzt sich | `compatible_with` |
| Knoblauch | Allium sativum | 0.7 | Schädlingsabwehr | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Fenchel | Foeniculum vulgare | Konkurrenz; teilen Schädlingsdruck | mild | `incompatible_with` |
| Pastinake | Pastinaca sativa | Gleiche Familie; geteilte Krankheitsrisiken | mild | `incompatible_with` |

### 6.4 Familien-Kompatibilität

| Verwandte Familie | Beziehung | Geteilte Risiken | KA-Edge |
|-------------------|-----------|------------------|---------|
| Apiaceae | `shares_pest_risk` | Sellerieblattmotte, Möhrenfliege, Septoria | `shares_pest_risk` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Levisticum officinale |
|-----|-------------------|-------------|----------------------------------------|
| Sellerie | Apium graveolens | Gleiche Familie; ähnliches Aroma | Jährlich neu; kontrollierter Wuchs |
| Petersilie | Petroselinum crispum | Gleiche Familie; milder | Kompakt; einjährig; keine Ausbreitung |
| Kerbel | Anthriscus cerefolium | Gleiche Familie; zarter | Frühzeitig verwendbar; leichtes Aroma |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Levisticum officinale,"Liebstöckel;Maggikraut;Suppengrün;Lovage",Apiaceae,Levisticum,perennial,long_day,herb,taproot,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",-0.1,"Südwestasien, Vorderasien",limited,40,50,200,100,90,no,limited,false,true,medium_feeder,false,hardy,"6;7;8"
```

---

## Quellenverzeichnis

1. [Naturadb Levisticum officinale](https://www.naturadb.de/pflanzen/levisticum-officinale/) — Steckbrief, Winterhärte
2. [Plantura Liebstöckel pflanzen](https://www.plantura.garden/kraeuter/liebstoeckel/liebstoeckel-pflanzen) — Anbau, Standort
3. [Samen.de Liebstöckel im Kräutergarten](https://samen.de/blog/liebstoeckel-im-kraeutergarten-anbau-und-verwendung.html) — Anbau, Verwendung
4. [Lubera Liebstöckel](https://www.lubera.com/de/gartenbuch/liebstoeckel-anbau-p2616) — Kultivierung
5. [Hausgarten.net Zitronenmelisse Pflege](https://www.hausgarten.net/zitronenmelisse-pflege/) — Vergleichsdaten
