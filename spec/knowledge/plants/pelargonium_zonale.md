# Zimmerpelargonie, Geranie — Pelargonium zonale

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Ellis' Garten](https://www.ellis-garten.de/geranie-pelargonium-zonale-wissenswertes-zu-pflege-verwendung/), [Floragard](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/beet-balkon/pelargonium-zonale), [Pflanzenfreunde.com](https://www.pflanzenfreunde.com/pelargonium.htm), [Die Grüne Welt](https://www.diegruenewelt.de/pflanze/stehende-geranien-pelargonium.html), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Pelargonium zonale | `species.scientific_name` |
| Synonyme | Pelargonium x hortorum (Hybrid-Arten im Handel); "Geranie" ist volkstümlicher Falschname | — |
| Volksnamen (DE/EN) | Zimmerpelargonie, Zonale Geranie, Stehende Geranie; Zonal Geranium, Horseshoe Geranium, Garden Geranium | `species.common_names` |
| Familie | Geraniaceae | `species.family` → `botanical_families.name` |
| Gattung | Pelargonium | `species.genus` |
| Ordnung | Geraniales | `botanical_families.order` |
| Wuchsform | shrub | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Anbau-Zyklustyp (cultivation cycle type) | annual | `lifecycle_configs.cultivation_cycle_type` |
| Typische Lebensdauer (Jahre) | 3–10+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| GDD-Basistemperatur (base temp, °C) | 5 | `species.base_temp` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurz-/Langtag-Schwellenwert --> | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | tender | `species.frost_sensitivity` |
| Winterhaerte-Detail | Nicht frosthart. Als Zimmerpflanze ganzjährig, als Balkonpflanze Überwinterung bei 5–10°C notwendig. | `species.hardiness_detail` |
| Heimat | Südafrika — Kapregion | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | heavy_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** "Geranie" ist botanisch unkorrekt — echte Geranien (Storchschnäbel) sind eine andere Gattung. Pelargonien sind Südafrikaner und vertragen keine Staunässe. Als Zimmerpflanze bei ausreichend Licht ganzjährig blühend. Das charakteristische Ringmuster (Hufeisenmuster) auf den Blättern ist namengebend für "zonale" Pelargonien. Sehr beliebte Balkonpflanze in Deutschland, kommt aber auch als langlebige Zimmerpflanze vor.

<!-- AB-003: Pelargonium zonale ist botanisch perennial, wird in DE aber oft als Einjaehrige behandelt (frost_sensitivity: tender). Fuer das Care-Preset gilt: Standard-Nutzung als Balkonpflanze → outdoor_annual_ornamental Preset passt. Ueberwinterungsszenario (hell, 5-10°C, reduziertes Giessen, Rueckschnitt im Fruehjahr, jaehrliches Umtopfen) erfordert ein dediziertes OverwinteringProfile (REQ-022) oder ein Perennial-Preset -- das ist NICHT im outdoor_annual_ornamental Preset abgedeckt. Im Onboarding-Kit balkon-blumen den Hinweis ergaenzen: "Geranien koennen eingewintert werden (hell, 5-10°C) oder werden jaehrlich neu gekauft." -->

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | 10–14 (Aussaat im Januar/Februar für Balkon-Saison) | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | 5, 6, 7, 8, 9, 10 <!-- Quelle: growing-phase-auditor 2026-07 — korrigiert von "4, 5, 6, 7, 8, 9, 10 (als Zimmerpflanze ganzjährig möglich)": 4/4 Quellen bestätigen Blüte Mai–Oktober für Balkon-/Beetkultur (primärer Anbaukontext, cultivation_cycle_type: annual); die pauschale "ganzjährig"-Angabe für Zimmerkultur war durch keine der Quellen belegt und widersprach ihnen --> | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | cutting_stem, seed | `species.propagation_methods` |
| Schwierigkeit | easy | `species.propagation_difficulty` |

**Hinweis:** Stecklinge 7–10 cm lang, 24 Stunden abtrocknen lassen (Wundverschluss), in Sandsubstrat stecken. Bewurzelung in 2–3 Wochen. Sehr einfach — ideal für Anfänger.

### 1.4 Toxizität & Allergene

| Feld | Wert | KA-Feld |
|------|------|---------|
| Giftig für Katzen | true | `species.toxicity.is_toxic_cats` |
| Giftig für Hunde | true | `species.toxicity.is_toxic_dogs` |
| Giftig für Kinder | false | `species.toxicity.is_toxic_children` |
| Giftige Pflanzenteile | leaves, stems (Ätherische Öle, Geraniol, Linalool) | `species.toxicity.toxic_parts` |
| Giftige Inhaltsstoffe | geraniol, linalool, citronellol (ätherische Öle) | `species.toxicity.toxic_compounds` |
| Schweregrad | mild | `species.toxicity.severity` |
| Kontaktallergen | true (Blatthaare können Hautreizungen verursachen) | `species.allergen_info.contact_allergen` |
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | spring_pruning | `species.pruning_type` |
| Rückschnitt-Monate | 2, 3 (Rückschnitt vor dem Austrieb) | `species.pruning_months` |

**Hinweis:** Überwinterte Pflanzen im Februar/März auf 10–15 cm zurückschneiden. Während der Blüte regelmäßig Blütenköpfe entfernen (Deadheading) um Nachblüte zu fördern.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 3–10 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 15 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 30–70 | `species.mature_height_cm` |
| Wuchsbreite (cm) | 30–60 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | yes (Hauptanwendung!) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Lockere, gut drainierte Kübelpflanzenerde. pH 6.0–7.0. Spezielle Geranienerde (mit Langzeitdünger) oder Einheitserde + 20% Sand/Perlite. Kein Torf oder moorige Substrate. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min/max (light compensation point, PPFD µmol/m²/s) | <!-- DATEN FEHLEN: kein Pelargonium-spezifischer LCP-Wert aus 2 seriösen Quellen belegbar --> | `species.light_compensation_point_ppfd_min` / `_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | full_sun | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | 15–30 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_sensitive | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-a-Schwellenwert (Substrat-ECe) für Pelargonium --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein belegter Maas-Hoffman-b-Wert --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference, min–max) | 5.8–6.5 | `species.soil_ph_preference` |

**Hinweis:** Vollsonniger Standort (full sun) mit mind. 6 h Direktsonne fördert die reichste Blüte; Halbschatten wird toleriert, reduziert aber die Blütenzahl. Flaches, faseriges Wurzelsystem (≈ 15–30 cm) → empfindlich gegen Staunässe (waterlogging), Pythium-Wurzelfäule ist die häufigste Verlustursache. Salztoleranz: in der Floristik-Produktion als mäßig salzempfindlich (moderately_sensitive) eingestuft — bereits ab Substrat-ECe ≈ 3 dS/m sinken Wuchs, Blüte und Chlorophyllgehalt deutlich; präzise Maas-Hoffman-Parameter (a/b) sind für die Zierpflanze nicht publiziert. Der pH-Vorzug 5.8–6.5 (Optimum der Nährstoffverfügbarkeit, insbes. Fe/Mn) ist enger als der in §1.6/§2.3 genannte tolerierbare Korridor 6.0–7.0; unter pH 5.5 droht Fe/Mn-Toxizität, deutlich über 6.6 Fe-Mangel-Chlorose.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

<!-- Quelle: seed-profile-backfill 2026-07 -->
### 1.8 Saatgut & Keimung (Seed Profile)

| Feld | Wert | KA-Feld |
|------|------|---------|
| Keimtemperatur min (°C) | 18 | `species.seed_profile.germination_temp_min_c` |
| Keimtemperatur max (°C) | 25 | `species.seed_profile.germination_temp_max_c` |
| Saattiefe (cm) | 0.3 (ca. 1/8 inch; nur mit einer duennen Schicht feinen Substrats/Vermiculits bedecken) | `species.seed_profile.sowing_depth_cm` |
| Tage bis Keimung | 7 (Spanne 7–14 Tage; einzelne Quellen nennen bis zu 20 Tage) | `species.seed_profile.days_to_germination` |
| Keimfähigkeitsdauer (Jahre) | <!-- DATEN FEHLEN: keine artspezifische Angabe zur Lagerfähigkeit von Pelargonium-Saatgut in seriösen Quellen auffindbar --> | `species.seed_profile.seed_viability_years` |
| Licht-/Dunkelkeimer | light | `species.seed_profile.light_germination` |
| Vorbehandlung | scarification (mechanisches Anschleifen der harten Testa mit Sandpapier/Nagelfeile ODER 6–12h Einweichen in warmem Wasser steigert die Keimrate von <1% auf 90–100% innerhalb von 2 Wochen) | `species.seed_profile.pretreatment` |
| Tausendkornmasse (g) | <!-- DATEN FEHLEN: verfügbare Zahl (~220–225 Samen/g, entsprechend ~4.4 g TKG) stammt aus nur einer Produktquelle (Renee's Garden 'Fancy Pants') und ist nicht durch eine zweite, unabhängige Quelle bestätigt --> | `species.seed_profile.thousand_seed_weight_g` |
| Aussaatdichte (Korn/m²) | <!-- SECTION MISSING: kein Reihen-/Direktsaat-Feldanbau — Pelargonium zonale wird in Zellplatten/Einzeltöpfen ausgesät, keine Flächen-Aussaatdichte dokumentiert --> | `species.seed_profile.sowing_density_per_m2` |

**Hinweis:** Pelargonium-Samen besitzen eine harte, wasserundurchlässige Testa. Ohne Vorbehandlung keimen sie extrem schlecht (< 1 % innerhalb von 2 Wochen); durch leichtes Anschleifen der Samenschale (Scarifizierung) oder Einweichen in warmem Wasser (6–12 h) lässt sich die Keimrate auf 90–100 % steigern. Samen sind Lichtkeimer und werden daher nur hauchdünn bedeckt.

Quellen (§1.8): [Thompson & Morgan — Raising F1 Hybrid Geraniums from Seed](https://www.thompson-morgan.com/raising-f1-geraniums-from-seed); [Flower Patch Farmhouse — Grow Geraniums from Seed (Pelargoniums)](https://www.flowerpatchfarmhouse.com/grow-geraniums-from-seed-pelargoniums/); [Horticulture.co.uk — Seed Sowing Geraniums](https://horticulture.co.uk/geraniums/sowing/); [Dave's Garden — Propagation: Geranium seed germination](https://davesgarden.com/community/forums/t/1227563/); [Carol J. Michel — Pelargonium Seeds](https://caroljmichel.com/pelargonium-seeds/); [Scented Leaf — Growing pelargoniums from seeds](http://blog.scentedleaf.com/2010/12/growing-pelargoniums-from-seeds.html); [Senior Gardening — Growing Geraniums from Seed](http://www.senior-gardening.com/features/seed_geraniums-2009.html)
<!-- /Quelle: seed-profile-backfill 2026-07 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Blüte/Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | high |
| Winterruhe (November–Februar) | 90–120 | 2 | false | false | high |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Blüte/Wachstum (Mai–Oktober)
<!-- Quelle: growing-phase-auditor 2026-07 — korrigiert von "März–Oktober": Phasenüberschrift an korrigierte Blütemonate (§1.2, Mai–Okt) angeglichen; deckt sich mit angegebener Phasendauer 180–210 Tage (Mai–Okt ≈ 184–214 Tage, März–Okt ≈ 245 Tage passte nicht) -->


| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 300–800 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 15–30 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 14–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–26 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 15–20 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 40–60 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.8–1.5 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.9 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 21–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 3–7 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 200–600 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (November–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–300 | `requirement_profiles.light_ppfd_target` |
| Temperatur Tag (°C) | 5–12 | `requirement_profiles.temperature_day_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 3–6 | `requirement_profiles.dli_target_mol` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 12–18 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.5 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------------|---------|-----|----------|----------|----------|----------|----------|----------|
| Blüte/Wachstum | 1:1:2 | 1.0–2.0 | 6.0–7.0 | 80 | 30 | 0.55 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.26 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.03 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> | 0.05 <!-- Quelle: Steckbrief-Erweiterung 2026-06 --> |
| Winterruhe | 0:0:0 | 0.0–0.2 | 6.0–7.0 | — | — | — | — | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis zu Mikronährstoffen:** Werte = Standard-Nährlösungskonzentration für *Pelargonium × hortorum* nach Smith et al. (Mn 10 µM, Zn 4 µM, Cu 0.5 µM, Mo 0.5 µM; in ppm umgerechnet). Nur in der Blüte-/Wachstumsphase relevant — in der Winterruhe ohne Düngung. Wegen des pH-Vorzugs (§1.7) auf Substrat-pH ≥ 6.0 achten: unter pH 6.0 steigt die Mn-Löslichkeit, was bei Geranien zu Mn-Toxizität (braune Blattrandflecken) führen kann.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Geranien-Flüssigdünger | Compo | base | 5-8-10 | 10 ml/L (wöchentlich) | Blüte |
| Geranien-Dünger | Substral | base | 5-8-11 | 10 ml/L | Blüte |

#### Langzeit / Ergänzung

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Hornspäne | – | organisch | 50 g/Topf | Frühjahr |
| Blaukorn | Haifa | mineralisch Langzeit | 5 g/L Substrat | einmalig Pflanzung |

### 3.2 Besondere Hinweise

Starkzehrer! Wöchentliche Düngung während der Blühperiode (April bis Oktober). Spezielle Geraniendünger mit erhöhtem Kaliumanteil verwenden — Kalium fördert die Blütenbildung und Standfestigkeit. Oktober bis Februar kein Dünger. Staunässe ist die häufigste Todesursache — lieber zu wenig als zu viel gießen.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | mediterranean | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 3–7 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.5 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Leitungswasser geeignet; gründlich gießen und komplett ablaufen lassen; obere Erdschicht zwischen Güssen antrocknen lassen — Staunässe tötet die Pflanze | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 7 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 4–10 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 12 | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | false | `care_profiles.humidity_check_enabled` |

### 4.2 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Rating | frost_free <!-- Quelle: Steckbrief-Erweiterung 2026-06 — korrigiert von needs_protection: nicht frostharte Kübel-/Zimmerpflanze, die frostfrei (5–12 °C) drinnen überwintert = frost_free --> | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 | `overwintering_profiles.winter_action_month` |
| Frühlings-Maßnahme | harden_off | `overwintering_profiles.spring_action` |
| Frühlings-Maßnahme Monat | 5 | `overwintering_profiles.spring_action_month` |
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 12 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | minimal | `overwintering_profiles.winter_watering` |

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Weiße Fliege | Trialeurodes vaporariorum | Weißliche Fliegen, Honigtau | easy |
| Blattläuse | Aphis spp. | Klebrige Triebe, Blattrollungen | easy |
| Spinnmilbe | Tetranychus urticae | Gespinste, Silberpunkte | medium |
| Frankliniella (Thrips) | Frankliniella occidentalis | Silbrige Flecken | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Grauschimmel | fungal (Botrytis cinerea) | Graubrauner Schimmel auf Blüten/Blättern | Hohe Feuchtigkeit, Staunässe |
| Geranienrost | fungal (Puccinia pelargonii-zonalis) | Braune Rostflecken auf Blattunterseite | Feuchtigkeit, dichte Bepflanzung |
| Wurzelfäule | fungal | Welke trotz Wasser | Staunässe |
| Bakterienfäule | bacterial | Schwarze Stängelflecken, süßlicher Geruch | Verletzungen, Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Befallene Triebe entfernen | cultural | Sofort abschneiden | 0 | Grauschimmel, Fäulen |
| Abstand vergrößern | cultural | Luftzirkulation verbessern | 0 | Grauschimmel (Prävention) |
| Neemöl | biological | Sprühen 0.5% | 0 | Blattläuse, Spinnmilben |
| Gelbklebfallen | mechanical | Aufstellen | 0 | Weiße Fliege (Monitoring) |
| Fungizid Kupfer | chemical | Sprühen nach Packungsangabe | 3 | Geranienrost |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Ziel-Schädling | Ausbringrate (pro m²) | Etablierungszeit |
|----------|----------------|-----------------------|------------------|
| Encarsia formosa (Schlupfwespe) | Weiße Fliege (Trialeurodes vaporariorum) | 1–10 (wöchentl., 3×) | 2–3 Wochen |
| Phytoseiulus persimilis (Raubmilbe) | Gemeine Spinnmilbe (Tetranychus urticae) | 10–32 | 1–2 Wochen |
| Aphidius colemani (Schlupfwespe) | Blattläuse (Aphis spp.) | 0.25–4 (wöchentl., ≥2×) | ca. 2 Wochen |

**Hinweis:** Nützlingseinsatz vor allem bei Indoor-/Gewächshauskultur sinnvoll; vorbeugend früh nach Befallsbeginn ausbringen. Optimaltemperatur Aphidius colemani 20–25 °C. Wiederholte Freilassungen, bis sich überlappende Generationen etabliert haben. Gelbtafeln (§5.3) dienen parallel dem Monitoring, nicht der Bekämpfung — bei Nützlingseinsatz nur als Köder-/Indikatorfallen sparsam einsetzen, da sie auch Nützlinge fangen.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Kübel-/Balkongpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Efeupelargonie | Pelargonium peltatum | Gleiche Gattung | Hängend, Ampelpflanze |
| Duftpelargonie | Pelargonium graveolens | Gleiche Gattung | Aromatisch, Kräuteranwendung |
| Wachsbegonie | Begonia semperflorens | Ähnliche Nutzung (Beet/Balkon) | Halbschatten-tolerant |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Pelargonium zonale,"Zimmerpelargonie;Zonale Geranie;Stehende Geranie;Zonal Geranium;Horseshoe Geranium",Geraniaceae,Pelargonium,perennial,day_neutral,shrub,fibrous,"10a;10b;11a;11b","Südafrika (Kapregion)",yes,3-10,15,30-70,30-60,yes,yes,false,heavy_feeder
```

---

## Quellenverzeichnis

1. [Ellis' Garten — Geranie](https://www.ellis-garten.de/geranie-pelargonium-zonale-wissenswertes-zu-pflege-verwendung/) — Pflege & Verwendung
2. [Floragard — Pelargonium zonale](https://www.floragard.de/de-de/pflanzeninfothek/pflanze/beet-balkon/pelargonium-zonale) — Kulturdaten
3. [Pflanzenfreunde.com — Pelargonium](https://www.pflanzenfreunde.com/pelargonium.htm) — Pflege, Überwinterung
4. [Die Grüne Welt — Stehende Geranien](https://www.diegruenewelt.de/pflanze/stehende-geranien-pelargonium.html) — Schädlinge, Krankheiten
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (giftig für Katzen/Hunde — ätherische Öle)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [MSU Floriculture — Estimated base temperature values (Blanchard & Runkle, basetemperature.pdf)](https://www.canr.msu.edu/uploads/resources/pdfs/basetemperature.pdf) — GDD-Basistemperatur Geranie (41 °F = 5 °C)
7. [Blanchard & Runkle (2011), Scientia Horticulturae — Quantifying the thermal flowering rates of eighteen species of annual bedding plants](https://www.sciencedirect.com/science/article/abs/pii/S0304423810005467) — Basistemperatur-Bereich (−3.9…13.8 °C) & Pelargonium-Topt ≈ 28 °C
8. [MSU Extension via greg.app — Geranium soil pH (6.0–6.5)](https://greg.app/geraniums-soil/) — Boden-pH-Vorzug, Fe/Mn-Toxizität < pH 6.0
9. [NC State Extension / e-GRO Geranium Nutrition (e-gro.org 2018_704)](https://www.e-gro.org/pdf/2018_704.pdf) — pH-Bereich 5.8–6.5, Fe/Mn-Management
10. [Smith et al. (1996), JASHS 121(1) — Micronutrient Toxicity in Seed Geranium](https://journals.ashs.org/jashs/view/journals/jashs/121/1/article-p77.xml) — Standard-Nährlösung Mn/Zn/Cu/Mo (10/4/0.5/0.5 µM)
11. [ScienceInsights — Geranium temperature tolerance / Photosynthese-Optimum 21–29 °C](https://scienceinsights.org/what-temperatures-can-geraniums-tolerate/) — Photosynthese-T_opt
12. [Annie's Annuals / Clemson HGIC — Geranium sun vs. shade](https://hgic.clemson.edu/factsheet/geranium/) — Schatten-/Sonnentoleranz (full_sun, 6+ h Direktsonne)
13. [My-Geranium / GardenersPath — Waterlogging & Pythium root rot](https://my-geranium.com/blog/four-things-that-geraniums-do-not-like-at-all/) — Staunässe-Empfindlichkeit (sensitive)
14. [GardenersPath / greg.app — Geranium root depth (6–12 inch)](https://gardenerspath.com/plants/flowers/grow-garden-geraniums/) — effektive Wurzeltiefe 15–30 cm
15. [Glutathione to ameliorate growth of geranium irrigated with salt water (PMC10368903)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10368903/) — Salztoleranz: Wuchs-/Blütehemmung ab ECe ≈ 3 dS/m
16. [Koppert — Encarsia formosa Ausbringrate (1–10/m²)](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/encarsia-formosa/) — Nützling Weiße Fliege
17. [Koppert — Aphidius colemani Ausbringrate (0.25–4/m²)](https://www.koppert.com/crop-protection/biological-pest-control/parasitic-wasps/aphidius-colemani/) — Nützling Blattläuse
18. [Phytoseiulus persimilis biological control on ivy geranium (ScienceDirect S104996440300183X) + Sound Horticulture (10–32/m²)](https://soundhorticulture.com/products/phytoseiulus-persimilis) — Nützling Spinnmilbe
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
19. [Garten-Land Wohlhüter — Pelargonium zonale](https://www.garten-land.de/pflanzen/beet-balkon/pelargonium-zonale) — Blütezeit Mai–Oktober
20. [Hauenstein AG — Geranie/Pelargonium](https://www.hauenstein-rafz.ch/de/pflanzenwelt/pflanzenportrait/sommerflor/Geranie-Pelargonium.php) — Blütezeit Mai–Oktober, Überwinterung ~10 °C
<!-- /Quelle: growing-phase-auditor 2026-07 -->
<!-- Quelle: seed-profile-backfill 2026-07 -->
21. [Thompson & Morgan — Raising F1 Hybrid Geraniums from Seed](https://www.thompson-morgan.com/raising-f1-geraniums-from-seed) — Keimtemperatur 18–20 °C, Lichtkeimer
22. [Flower Patch Farmhouse — Grow Geraniums from Seed (Pelargoniums)](https://www.flowerpatchfarmhouse.com/grow-geraniums-from-seed-pelargoniums/) — Saattiefe max. 1/8 inch
23. [Horticulture.co.uk — Seed Sowing Geraniums](https://horticulture.co.uk/geraniums/sowing/) — Lichtkeimer, harte Testa, hard-coated seeds germinate in 14 Tagen bei 20 °C
24. [Dave's Garden — Propagation: Geranium seed germination](https://davesgarden.com/community/forums/t/1227563/) — Praxiserfahrung Scarifizierung/Einweichen
25. [Carol J. Michel — Pelargonium Seeds](https://caroljmichel.com/pelargonium-seeds/) — Scarifizierungs-Technik, Keimraten-Vergleich (90–100% vs. <1%)
26. [Scented Leaf — Growing pelargoniums from seeds](http://blog.scentedleaf.com/2010/12/growing-pelargoniums-from-seeds.html) — Nick+Soak-Methode, Keimung in 2 Tagen nach Vorbehandlung
27. [Senior Gardening — Growing Geraniums from Seed](http://www.senior-gardening.com/features/seed_geraniums-2009.html) — Keimdauer bis 20 Tage, Anzuchtpraxis
<!-- /Quelle: seed-profile-backfill 2026-07 -->
