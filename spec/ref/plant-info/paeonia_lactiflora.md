# Chinesische Pfingstrose — Paeonia lactiflora

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Winterharte-Stauden Paeonia lactiflora, Lubera Pfingstrosen, Staudengärtnerei Gaißmayer, Compo Pfingstrose

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Paeonia lactiflora | `species.scientific_name` |
| Volksnamen (DE/EN) | Chinesische Pfingstrose, Milchweiße Pfingstrose; Chinese Peony, Common Garden Peony | `species.common_names` |
| Familie | Paeoniaceae | `species.family` → `botanical_families.name` |
| Gattung | Paeonia | `species.genus` |
| Ordnung | Saxifragales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | tuberous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
| USDA Zonen | 3a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C und kälter; braucht kalten Winter für Blütenbildung (Vernalisierung); in ganz Norddeutschland problemlos | `species.hardiness_detail` |
| Heimat | China, Sibirien, Korea | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Teilung bevorzugt; Aussaat dauert 3–4 Jahre bis Blüte) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | 9 (Frischabsaat; lange Stratifikation nötig) | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Schnittblume Juni–Juli) | `species.harvest_months` |
| Blütemonate | 5, 6, 7 (je nach Sorte) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division | `species.propagation_methods` |
| Schwierigkeit | moderate | `species.propagation_difficulty` |

**Hinweis:** Teilung im Herbst (September–Oktober) — jedes Teilstück braucht mindestens 3–5 "Augen" (Knospen). Pflanztiefe der Augen: MAXIMAL 3–5 cm unter der Erde — tiefer = keine Blüte!

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | true | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | Alle Pflanzenteile (besonders Wurzeln und Samen) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | Paeonol, Paeoniflorin, Paeonin | `species.toxicity.toxic_compounds` |
| Schweregrad | moderate | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 | `species.pruning_months` |

**Hinweis:** Im Herbst bodennah zurückschneiden. Altes Laub entfernen (Pilzkrankheiten). Im Frühjahr NICHT schneiden — würde Blütenentwicklung stören. Einmal gepflanzte Pfingstrosen so wenig wie möglich stören — an einem guten Standort werden sie 50+ Jahre alt.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 40–60 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 40 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 60–100 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 80–100 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | true (schwere Blüten bei Regen umgeknickt; Staudenhalter empfohlen) | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, lehmig-humose, tiefgründige Erde; pH 6,5–7,0; gut durchlässig; kein Staunässe | — |

**Kritisch:** Standort einmal gewählt nicht mehr wechseln — Pfingstrosen brauchen 3–4 Jahre, um sich zu etablieren und blühen nach dem Umpflanzen jahrelang nicht.

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Einwurzelung (nach Teilung) | 28–60 | 1 | false | false | low |
| Frühjahrsaustrieb | 21–42 | 2 | false | false | medium |
| Knospenbildung | 14–21 | 3 | false | false | low |
| Blüte | 14–28 | 4 | false | true | low |
| Nach der Blüte (Reife) | 60–90 | 5 | false | false | high |
| Herbstrückzug | 21–35 | 6 | false | false | high |
| Winterruhe | 120–150 | 7 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Knospenbildung & Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 400–700 (Volllicht essenziell für Blüte) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 25–40 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.8–1.4 | `requirement_profiles.vpd_target_kpa` |
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 5–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 1000–2000 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|
| Einwurzelung | 0:1:1 | 0.6–0.8 | 6.5 | 60 | 30 | – | 1 |
| Frühjahrsaustrieb | 2:1:2 | 1.0–1.4 | 6.5–7.0 | 100 | 50 | – | 2 |
| Knospen/Blüte | 1:2:2 | 1.2–1.6 | 6.5–7.0 | 130 | 60 | – | 2 |
| Nach Blüte | 1:1:2 | 0.8–1.2 | 6.5–7.0 | 100 | 50 | – | 1 |
| Winterruhe | 0:0:0 | 0.0 | – | – | – | – | – |

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (bevorzugt)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Hornspäne | Oscorna | organisch | 60–80 g/m² | März (Austrieb) | N-Grundversorgung |
| Kompost (reif) | eigen | organisch | 3–5 L/m² | März, Oktober | Bodenverbesserung |
| Stauden-Dünger organisch | Neudorff Azet | organisch | 60 g/m² | April | medium_feeder |
| Knochenmehl | – | organisch | 50 g/m² | Herbst bei Pflanzung | P für Wurzelbildung |

**Hinweis:** Keine mineralischen Stickstoffdünger — reagieren oft mit gelben Blättern und kümmerlicher Blüte.

### 3.2 Düngungsplan

| Zeitpunkt | NPK-Fokus | Produkt | Menge | Hinweis |
|-----------|-----------|---------|-------|---------|
| März (Austrieb sichtbar) | N-ausgewogen | Hornspäne + Kompost | 70 g/m² + 4L/m² | Nicht direkt auf Augen |
| Mai (nach Blüte) | P/K-betont | Stauden-Dünger | 50 g/m² | Für Reservestoffe |
| Oktober (Herbst) | P/K | Kompost + Knochenmehl | 3L/m² + 40g/m² | Wintervorbereitung |

### 3.3 Besondere Hinweise zur Düngung

Pfingstrosen reagieren empfindlich auf zu viel Stickstoff — üppiges Laub, wenig Blüten. Organische Düngung mit Kompost und Hornspäne ist ideal. Nur 2× jährlich düngen reicht völlig aus. KEINE Düngung direkt auf die Augen (Knospen) — Verbrennungen möglich. Wichtig: Standortvorbreitung vor der Pflanzung mit Kompost anreichern (dauerhafter Standort).

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; gleichmäßig feucht bei Knospenentwicklung; kein Staunässe | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 60 (2–3× jährlich) | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Düngung | Hornspäne und Kompost um Pflanze herum | hoch |
| Apr–Mai | Knospenentwicklung | Staudenhalter aufstellen; gleichmäßig gießen | hoch |
| Mai–Jun | Blüte genießen | Geschnittene Knospen im Halboffenen Zustand für Vasen | mittel |
| Jun | Verblühte entfernen | Verwelkte Blüten; verhindert Krankheitseinfall | mittel |
| Sep | Nachblüte-Düngung | P/K-betont für Reservestoffspeicherung | mittel |
| Okt | Herbstschnitt | Bodennah; altes Laub entfernen und entsorgen | hoch |
| Okt | Teilung (wenn nötig) | Nur bei Platzmangel oder schwacher Blüte; alle 5–8 Jahre | niedrig |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | — | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | uncover | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

**Hinweis:** Pfingstrosen brauchen den Frost — er fördert die Blütenanlage (Vernalisierung). Kein Winterschutz nötig. Mulch kann die Knospen zu früh austreiben lassen — lieber weglassen.

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Ameisen | Lasius spp. | Ameisen auf Knospen (ernähren sich von Nektar; schaden NICHT der Pflanze) | flower | flowering | easy |
| Blattläuse | Aphis gossypii | Kolonien an Triebspitzen; selten | shoot | spring | easy |
| Thripse | Frankliniella occidentalis | Silbrige Flecken auf Blütenblättern | flower | flowering | difficult |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Pfingstrosenfäule (Botrytis) | fungal (Botrytis paeoniae) | Braune Triebe; Knospen fallen ab; grauer Schimmel | Feuchte; dichter Stand; altes Laub | 3–7 | spring, flowering |
| Echter Mehltau | fungal | Weißer Belag | Trockenheit Spätsommer | 5–10 | vegetative |
| Blattflecken | fungal (Cladosporium spp.) | Braune Flecken auf Blättern | Feuchtigkeit | 7–14 | vegetative |

**Hinweis zu Ameisen:** Ameisen auf Pfingstrosenknospen sind HARMLOS — sie ernähren sich von Nektardrüsen außen an den Knospen. Sie schaden der Pflanze nicht und müssen nicht bekämpft werden.

### 5.3 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Altes Laub entfernen | cultural | – | Herbst; Vernichten (nicht kompostieren) | 0 | Botrytis |
| Luftzirkulation verbessern | cultural | – | Ausreichend Abstand; ausgelichteter Stand | 0 | Botrytis, Mehltau |
| Kupferfungizid | chemical | Kupferhydroxid | Frühjahr prophylaktisch | 7 | Botrytis |
| Fungizid Tebuconazol | chemical | Triazol | Bei starkem Befall | 14 | Mehltau |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer (medium_feeder) |
| Fruchtfolge-Kategorie | Dauerstaude (kein Fruchtwechsel) |
| Anbaupause (Jahre) | Keine Neupflanzung in Pfingstrosenboden für 5 Jahre (Bodenerschöpfung) |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Echter Salbei | Salvia nemorosa | 0.7 | Ähnliche Blütezeit; Bodendecker | `compatible_with` |
| Iris | Iris germanica | 0.7 | Ergänzende Blütezeit; gleiche Standortansprüche | `compatible_with` |
| Katzenminze | Nepeta × faassenii | 0.8 | Bodendecker vor Pfingstrose | `compatible_with` |
| Allium | Allium hollandicum | 0.8 | Schädlingsabwehr; attraktive Kombination | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Gehölze und Hecken | diverse | Wurzelkonkurrenz; Pfingstrose mag keine Konkurrenz | moderate | `incompatible_with` |
| Bambus | Phyllostachys spp. | Übermächtige Wurzelkonkurrenz | severe | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Paeonia lactiflora |
|-----|-------------------|-------------|--------------------------------------|
| Strauchpfingstrose | Paeonia suffruticosa | Gleiche Gattung | Frühblüher; verholzend; andere Dimension |
| Baumartiger Rittersporn | Delphinium elatum | Keine Verwandtschaft | Höher; blauer; andere Optik |
| Pfingstrose 'Coral Charm' | Paeonia lactiflora Cultivar | Gleiche Art | Lachsfarbene Blüten; früh |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Paeonia lactiflora,"Chinesische Pfingstrose;Milchweiße Pfingstrose;Chinese Peony",Paeoniaceae,Paeonia,perennial,long_day,herb,tuberous,"3a;3b;4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"China, Sibirien, Korea",limited,50,40,120,100,90,no,limited,false,true,medium_feeder,false,hardy,"5;6;7"
```

---

## Quellenverzeichnis

1. [Winterharte-Stauden Paeonia lactiflora](https://winterharte-stauden.com/paeonia-lactiflora-pfingstrose/) — Steckbrief, Winterhärte
2. [Lubera Pfingstrosen](https://www.lubera.com/de/gartenbuch/pfingstrosen-pflanzen-pflegen-und-vermehren-p5486) — Anbau, Pflege, Teilung
3. [Staudengärtnerei Gaißmayer Pfingstrosen Pflege](https://www.gaissmayer.de/web/welt/pflanzenwissen/stauden/sortiment/pfingstrosen/pflanz-und-pflegetipps/) — Fachliche Tipps
4. [Compo Pfingstrose](https://www.compo.de/ratgeber/pflanzen/gartenpflanzen/pfingstrose) — Düngung, Krankheiten
