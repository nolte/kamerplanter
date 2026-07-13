# Flammenblume — Phlox paniculata

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** Lubera Phlox paniculata, Plantura Phlox, COMPO Phlox, Pflanzen-Kölle Phlox

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Phlox paniculata | `species.scientific_name` |
| Volksnamen (DE/EN) | Flammenblume, Hoher Stauden-Phlox; Garden Phlox | `species.common_names` |
| Familie | Polemoniaceae | `species.family` → `botanical_families.name` |
| Gattung | Phlox | `species.genus` |
| Ordnung | Ericales | `botanical_families.order` |
| Wuchsform | herb | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
<!-- Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Blühstrategie (flowering strategy) | polycarpic (ausdauernd, blüht wiederholt über mehrere Jahre) | `lifecycle_configs.flowering_strategy` |
<!-- /Quelle: growing-phase-auditor (WP-10 flowering-strategy backfill #453) -->
| Photoperiode | long_day | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | 5 | `species.base_temp` |
| Lebensdauer (Jahre) | <!-- DATEN FEHLEN --> | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | true | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false | `lifecycle_configs.vernalization_required` |
| Vernalisation Mindest-Tage (vernalization min days) | — (nicht erforderlich; Kältereiz fördernd ≥ 6 Wochen / ~42 Tage bei 2–7 °C) | `lifecycle_configs.vernalization_min_days` |
| Kritische Tageslänge (h) | 14 | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

| USDA Zonen | 4a–8b | `species.hardiness_zones` |
| Frostempfindlichkeit | hardy | `species.frost_sensitivity` |
| Winterhärte-Detail | Winterhart bis -30°C; keine Schutzmaßnahmen in Norddeutschland nötig | `species.hardiness_detail` |
| Heimat | östliches Nordamerika | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | medium_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | — (Teilung bevorzugt) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat nach letztem Frost (Tage) | — | `species.sowing_outdoor_after_last_frost_days` |
| Direktsaat-Monate | — | `species.direct_sow_months` |
| Erntemonate | — (Zierpflanze; Schnittblume möglich) | `species.harvest_months` |
| Blütemonate | 7, 8, 9 | `species.bloom_months` |

**Hinweis:** Sehr lange Blütezeit von Juli bis September. Als Schnittblume haltbar ca. 7–10 Tage in der Vase.

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | division, cutting_stem | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Teilung im Frühjahr oder Herbst alle 3–4 Jahre empfohlen — verjüngt die Pflanze und reduziert Mehltauanfälligkeit. Wurzelstecklinge im Februar möglich.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | false | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | false | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | keine bekannt | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | keine | `species.toxicity.toxic_compounds` |
| Schweregrad | none | `species.toxicity.severity` |
| Kontaktallergen | false | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | after_harvest | `species.pruning_type` |
| Rückschnitt-Monate | 10, 11 (Herbst nach Blüte) ODER 3 (Frühjahr) | `species.pruning_months` |

**Hinweis:** Rückschnitt auf 5–10 cm nach der Blüte im Herbst, oder alternativ im Frühjahr. Nicht zu tief schneiden — ein kurzer Stumpf schützt vor Frost. Verblühte Blütenstände sofort entfernen, um Selbstaussaat und Versamung (Stängelqualität verschlechtert sich) zu verhindern.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | limited | `species.container_suitable` |
| Empf. Topfvolumen (L) | 15–25 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 60–120 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 40–60 | `species.mature_width_cm` |
| Platzbedarf Freiland (cm) | 45–60 | `species.spacing_cm` |
| Indoor-Anbau | no | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Nährstoffreiche, humusreiche, gut feuchtigkeitsspeichernde Erde; pH 6,0–7,0; keine Staunässe | — |

**Standort-KRITISCH:** Eher lichten Halbschatten bevorzugen — pralle Mittagssonne fördert Mehltau. Vollsonnig nur mit ausreichend Wasserversorgung.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 15 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 35 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 30–45 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis (Lichtkompensationspunkt):** Generischer LCP-Bereich für temperate C3-Halbschatten-/Sonnenstauden (15–35 µmol/m²/s); art-spezifische Messwerte für *Phlox paniculata* liegen nicht vor. Dies ist NUR der Kompensationspunkt (Netto-Photosynthese = 0); Lichtsättigung liegt deutlich höher und gehört nicht in dieses Feld.

**Hinweis (Salztoleranz):** Jersey-Friendly-Yards-Datenbank stuft *Phlox paniculata* als "medium" salztolerant ein → `moderately_sensitive`. Maas-Hoffman-Parameter (ECe-Schwelle, Slope) sind für die Art nicht publiziert. Bezugsgröße der Klasse ist die Substrat-Salinität (ECe), nicht die Gießwasser-EC.

**Hinweis (pH):** Quellentreuer Vorzugsbereich pH 6,0–7,0 (slightly acidic to neutral), konsistent mit §1.6 und §2.3. Einzelne Quellen nennen eine Toleranz bis pH 8,0 — der bevorzugte Korridor bleibt 6,0–7,0.

<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Frühjahrsaustrieb | 14–21 | 1 | false | false | medium |
| Vegetatives Wachstum | 56–90 | 2 | false | false | medium |
| Blüte | 42–70 | 3 | false | false | medium |
| Nachblüte / Abreife | 30–45 | 4 | false | false | high |
| Winterruhe | 120–150 | 5 | true | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 200–500 (lichte Halbschatten bis Sonne) | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 12–25 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–24 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 12–16 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–65 | `requirement_profiles.humidity_day_percent` |
| Luftfeuchtigkeit Nacht (%) | 55–70 | `requirement_profiles.humidity_night_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 22–25 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 3–5 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 500–1500 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | S (ppm) | Fe (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|---------|----------|----------|----------|----------|----------|
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Frühjahrsaustrieb | 2:1:1 | 0.8–1.2 | 6.0–7.0 | 100 | 50 | — | 2 | 0.5 | 0.25 | 0.05 | 0.05 |
| Vegetativ | 2:1:2 | 1.0–1.4 | 6.0–7.0 | 120 | 60 | — | 3 | 0.5 | 0.25 | 0.05 | 0.05 |
| Blüte | 1:2:2 | 1.0–1.4 | 6.0–7.0 | 100 | 50 | — | 2 | 0.5 | 0.25 | 0.05 | 0.05 |
| Winterruhe | 0:0:0 | 0.0 | — | — | — | — | — | — | — | — | — |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

**WICHTIG:** Kein Überschuss-Stickstoff! Zu viel N erhöht die Mehltauanfälligkeit erheblich.

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis (Mikronährstoffe Mn/Zn/Cu/Mo):** Es liegen keine art-spezifisch publizierten Mikronährstoff-Zielwerte für *Phlox paniculata* vor. Die angegebenen Mn-/Zn-/Cu-/Mo-Konzentrationen sind allgemeine Richtwerte aus Hoagland-typischen Nährlösungsrezepturen für Zierstauden und gelten über die aktiven Wuchsphasen hinweg konstant; in der Winterruhe entfällt jede Düngung.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung & Nährstoffversorgung

### 3.1 Empfohlene Düngerprodukte

#### Organisch (Freiland)

| Produkt | Marke | Typ | Ausbringrate | Saison | Geeignet für |
|---------|-------|-----|-------------|--------|-------------|
| Compo Stauden-Langzeitdünger | Compo | organisch-mineralisch | 80 g/m² | April, Juni | medium_feeder |
| Hornspäne | Oscorna | organisch | 40–60 g/m² | April | Stickstoff-Startdüngung |
| Kompost (reif) | eigen | organisch | 3–4 L/m² | März/Oktober | Bodenverbesserung |
| Kalibetonter Düng. z.B. Patentkali | ICL Specialty Fertilizers | mineralisch | 30–40 g/m² | Juli (einmalig) | Triebausreifung |

### 3.2 Düngungsplan

| Monat | Phase | Produkt | Menge | Hinweise |
|-------|-------|---------|-------|----------|
| April | Austrieb | Hornspäne + Kompost | 50 g/m² + 3 L/m² | Zweites Standjahr (erstes Jahr: leicht düngen) |
| Juni | Vegetativ | Staudendünger organisch | einmalig | Nicht zu stickstoffreich! |
| Juli | Blüte | Kalibetonter Dünger | einmalig | Letzte Düngung der Saison |

**Hinweis:** Kein Dünger ab August — Triebe müssen ausreifen.

### 3.3 Besondere Hinweise zur Düngung

Phlox reagiert empfindlich auf zu hohen Stickstoffgehalt — dies fördert üppiges, weiches Gewebewachstum, das für Echten Mehltau besonders anfällig ist. Daher immer mit niedrig dosiertem, ausgewogenem Dünger arbeiten. Kein intensives Flüssigdüngen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | outdoor_perennial | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 4 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 5.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | top_water | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Normales Leitungswasser; NIEMALS Laub benetzen — Mehltauförderung; nur an der Wurzel gießen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 56 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–7 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 42 (alle 3–4 Jahre teilen) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Pflegearbeiten im Jahresverlauf

| Monat | Arbeitsschritt | Beschreibung | Priorität |
|-------|---------------|--------------|-----------|
| Mär | Rückschnitt (falls Herbst ausgelassen) | Auf 10 cm zurückschneiden; Kompost einarbeiten | hoch |
| Apr | Düngung starten | Hornspäne + Kompost; niedrig dosieren | mittel |
| Mai–Jun | Wachstum beobachten | Mehltau-Früherkennung! Gut lüften durch Abstand | hoch |
| Jul–Sep | Blüte | Verblühtes sofort entfernen; nicht zu trocken | mittel |
| Sep–Okt | Rückschnitt | Auf 5–10 cm zurück nach Blüte | mittel |
| Alle 3–4 J. | Teilung | Frühjahr; Pflanzen verjüngen; Mehltauanfälligkeit sinkt | hoch |

### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | hardy | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | none | `overwintering_profiles.winter_action` |
| Frühlings-Maßnahme | prune | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 3 | `overwintering_profiles.spring_action_month` |
| Winter-Gießen | none | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Betroffene Teile | Anfällige Phasen | Erkennungsschwierigkeit |
|-----------|-------------------|----------|-------------------|-------------------|------------------------|
| Blattläuse | Aphis spp. | Kolonien an Triebspitzen; Honigtau | shoot | vegetative (Frühjahr) | easy |
| Schnecken | Arion rufus | Fraß an Jungpflanzen | shoot, leaf | Frühjahrsaustrieb | easy |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser | Inkubation (Tage) | Anfällige Phasen |
|-----------|-----------|----------|----------|-------------------|------------------|
| Echter Mehltau | fungal (Golovinomyces magnicellulatus) | Weißer, mehliger Belag auf Blättern und Stängeln | Trockene Luft, Wärme tagsüber, kühle Nächte; Laub befeuchten; zu eng gepflanzt; zu viel N | 5–10 | vegetative (Juli–September) |
| Phlox-Rost | fungal (Coleosporium phloxidis) | Gelbliche Flecken oben, orangerote Sporenlager unten | Feuchtigkeit | 7–14 | flowering |
| Stängelfäule | fungal (Sclerotinia) | Weißes Myzel an Stängelbasis | Staunässe, kühle Feuchtigkeit | 14 | Frühjahr |

**Mehltau-Vorbeugung (PRIORITÄT 1):**
- Standort mit guter Luftzirkulation; ausreichend Abstand (45–60 cm)
- Nur bodennah gießen, Laub NICHT benetzen
- Mehltau-resistente Sorten wählen: 'David' (weiß), 'Blue Paradise', 'Uspech', 'Eva Cullum'
- Alte Triebe nach der Blüte vollständig entfernen und NICHT kompostieren

### 5.3 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (/m²) | Etablierungszeit (Tage) |
|----------|---------------|---------------------|------------------------|
| Chrysoperla carnea | Blattläuse | 5–10 | 14 |
| Marienkäfer (Coccinella septempunctata) | Blattläuse | natürliche Förderung | sofort |

### 5.4 Behandlungsmethoden

| Methode | Typ | Wirkstoff | Anwendung | Karenzzeit (Tage) | Gegen |
|---------|-----|-----------|-----------|-------------------|-------|
| Backpulver-Lösung | biological | Natriumhydrogencarbonat | 10 g/L Wasser; sprühen | 0 | Echter Mehltau (Früherkennung) |
| Neemöl | biological | Azadirachtin | 0.5%; abends sprühen | 3 | Mehltau, Blattläuse |
| Schwefel-Präparate (z.B. Netzschwefel) | chemical | Schwefel | sprühen bei ersten Symptomen | 14 | Mehltau, Rost |
| Resistente Sorten | cultural | — | Sortenwahl | 0 | Mehltau |

### 5.5 Resistenzen der Art

| Resistenz gegen | Typ | KA-Edge |
|----------------|-----|---------|
| Sorte 'David': Mehltauresistent | Krankheit | `resistant_to` |
| Sorte 'Blue Paradise': Mehltauresistent | Krankheit | `resistant_to` |

---

## 6. Fruchtfolge & Mischkultur

### 6.1 Fruchtfolge-Einordnung

| Feld | Wert |
|------|------|
| Nährstoffbedarf | Mittelzehrer |
| Fruchtfolge-Kategorie | Gartenstauden |
| Empfohlene Vorfrucht | — (Mehrjährig; kein Fruchtwechsel) |
| Anbaupause (Jahre) | Mindestens 3–4 Jahre an gleichem Standort sinnvoll; dann teilen |

### 6.2 Mischkultur — Gute Nachbarn

| Partner | Wissenschaftl. Name | Kompatibilitäts-Score | Nutzen | KA-Edge |
|---------|-------------------|----------------------|--------|---------|
| Rittersporn | Delphinium elatum | 0.8 | Klassische Sommerstauden-Kombination; ergänzende Höhen | `compatible_with` |
| Hemerocallis | Hemerocallis spp. | 0.8 | Gleiche Standortansprüche; ergänzende Texturen | `compatible_with` |
| Lavendel | Lavandula angustifolia | 0.7 | Bestäuber anlocken; gut lüftend | `compatible_with` |
| Echinacea | Echinacea purpurea | 0.8 | Gleiche Blütezeit; Nützlingsförderung | `compatible_with` |

### 6.3 Mischkultur — Schlechte Nachbarn

| Partner | Wissenschaftl. Name | Grund | Schweregrad | KA-Edge |
|---------|-------------------|-------|-------------|---------|
| Aster | Symphyotrichum novae-angliae | Teilen Mehltaupilz-Sporen; gegenseitige Infektionsgefahr | moderate | `incompatible_with` |

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil gegenüber Phlox paniculata |
|-----|-------------------|-------------|-------------------------------------|
| Polster-Phlox | Phlox subulata | Gleiches Genus; niedrig | Kaum Mehltau; Frühjahrsblüher |
| Waldsalbei | Salvia nemorosa | Ähnliche Farbpalette, ähnliche Blütezeit | Mehltau-unempfindlich; trockenheitstoleranter |
| Kokardenblume | Gaillardia grandiflora | Ähnliche Sommerblüte | Deutlich mehltaufreier; Hitzetoleranter |

---

## 8. CSV-Import-Daten (KA REQ-012 kompatibel)

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,allelopathy_score,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,greenhouse_recommended,support_required,nutrient_demand_level,green_manure_suitable,frost_sensitivity,bloom_months
Phlox paniculata,"Flammenblume;Hoher Stauden-Phlox;Garden Phlox",Polemoniaceae,Phlox,perennial,long_day,herb,fibrous,"4a;4b;5a;5b;6a;6b;7a;7b;8a;8b",0.0,"östliches Nordamerika",limited,20,30,100,50,50,no,limited,false,false,medium_feeder,false,hardy,"7;8;9"
```

---

## Quellenverzeichnis

1. [Lubera — Phlox paniculata Pflege](https://www.lubera.com/de/gartenbuch/phlox-paniculata-pflege-standort-und-vermehrung-p5402) — Standort, Pflege, Vermehrung
2. [Plantura — Phlox paniculata](https://www.plantura.garden/blumen-stauden/phlox/phlox-paniculata) — Steckbrief, Sorten
3. [Plantura — Phlox pflegen](https://www.plantura.garden/blumen-stauden/phlox/phlox-pflegen) — Gießen, Düngen, Schneiden
4. [COMPO — Phlox](https://www.compo.de/ratgeber/pflanzen/gartenpflanzen/phlox) — Düngung, IPM
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
5. [Runkle, Heins, Cameron & Carlson — Flowering of Phlox paniculata Is Influenced by Photoperiod and Cold Treatment, HortScience 33(7):1172–1174 (1998)](https://www.researchgate.net/publication/277865552_Flowering_of_Phlox_paniculata_Is_Influenced_by_Photoperiod_and_Cold_Treatment) — quantitativer Langtag, kritische Tageslänge ~13–14 h, Kältereiz fördernd (≥ 6 Wochen, 2–7 °C), nicht erforderlich
6. [NC State Extension Gardener Plant Toolbox — Phlox paniculata](https://plants.ces.ncsu.edu/plants/phlox-paniculata/) — Lichtbedarf (full sun bis partial shade), Boden-pH, Drainage
7. [ForwardPlant — Optimal Soil for Garden Phlox](https://www.forwardplant.com/care/soil/phlox-paniculata/) — Boden-pH 6,0–7,0, Wurzeltiefe 30–45 cm, Staunässe-Empfindlichkeit
8. [Biology Insights — Phlox Roots: Depth, Planting, and Common Problems](https://biologyinsights.com/phlox-roots-depth-planting-and-common-problems/) — Wurzelsystem-Tiefe (≈30–38 cm)
9. [Jersey-Friendly Yards — Phlox paniculata](https://www.jerseyyards.org/plant/phlox-paniculata/) — Salztoleranz "medium" (→ moderately_sensitive), Licht, Bodenfeuchte
10. [Yard & Garden, Iowa State Extension — Using Growing Degree Days](https://yardandgarden.extension.iastate.edu/how-to/using-growing-degree-days-manage-home-garden) — GDD-Basistemperatur 5 °C für kühl-temperate Arten
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
