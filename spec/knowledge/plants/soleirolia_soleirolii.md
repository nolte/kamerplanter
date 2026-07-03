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
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
| GDD-Basistemperatur (base temp, °C) | <!-- DATEN FEHLEN --> kein belegter Wuchs-/Phänologie-GDD-Basiswert publiziert | `species.base_temp` |
| Lebensdauer (Jahre, lifespan) | <!-- DATEN FEHLEN --> mattenbildende Staude, langlebig; keine zwei unabhängigen Quellen für konkrete Jahreszahl | `lifecycle_configs.typical_lifespan_years` |
| Dormanz erforderlich (dormancy required) | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich (vernalization required) | false (mediterrane, frostempfindliche Art ohne Kältebedarf) | `lifecycle_configs.vernalization_required` |
| Kritische Tageslänge (h) | <!-- DATEN FEHLEN --> nicht zutreffend (tagneutral, kein Kurz-/Langtagblüher) | `lifecycle_configs.critical_day_length_hours` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
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
| Direktsaat-Monate | Entfällt (Vermehrung ausschließlich vegetativ — Teilung/Stecklinge, siehe §1.3; keine gängige Aussaatpraxis) [KORRIGIERT 2026-07: war "3, 4, 5" — inkonsistent mit `propagation_methods` (division; cutting_stem, kein seed) und mit dem Muster aller vergleichbaren vegetativ vermehrten Zimmer-/Terrarienpflanzen im Bestand (z.B. Fittonia albivenis, Ceropegia woodii); siehe Audit-Quellen] | `species.direct_sow_months` |
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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 20 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (cm) | 5–15 | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | <!-- DATEN FEHLEN --> keine belegbare Einstufung | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (min–max) | 5.0–6.5 | `species.soil_ph_preference` |

**Hinweis Licht:** Bubikopf ist eine ausgesprochene Schattenpflanze (deep-shade-tolerant) und überlebt in Unterwuchs-Lichtniveaus von 1–2 % des vollen Sonnenlichts. Der Lichtkompensationspunkt (Netto-Photosynthese = 0) liegt im untersten Bereich schattentoleranter Arten (10–50 µmol/m²/s). Direktsonne verbrennt das Laub. Aktives Wachstum (≠ Kompensationspunkt) setzt erst ab ca. 50–200 µmol/m²/s ein (siehe §2.2).

**Hinweis pH:** Vorzug leicht sauer (5.0–6.0 nach EpicGardening/Florgeous); harmonisiert mit der Substrat-/Nährlösungsangabe pH 5.5–6.5 in §1.6 und §2.3. Die RHS führt die Art als gegenüber pH adaptabel (acid/neutral/alkaline), der Wachstums-Vorzug bleibt im sauren Bereich.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.1 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | high | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 16–20 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.75 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| CO₂ (ppm) | 400–800 | `requirement_profiles.co2_ppm` |
| Gießintervall (Tage) | 2–4 (Substrat gleichmäßig feucht halten, nie austrocknen) | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 50–150 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Etablierung | 0:0:0 | 0.0 | 5.5–6.5 | — | — |
| Vegetativ | 2:1:2 | 0.4–0.8 | 5.5–6.5 | 60 | 30 |
| Blüte | 1:1:1 | 0.3–0.6 | 5.5–6.5 | 40 | 20 |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (ppm):** Richtwerte für einen Schwachzehrer (light feeder) im leicht sauren Bereich, am unteren Rand üblicher Hydro-/Topfkultur-Mikronährstoffspannen gehalten.

| Phase | Mn (ppm) | Zn (ppm) | Cu (ppm) | Mo (ppm) |
|-------|----------|----------|----------|----------|
| Etablierung | — | — | — | — |
| Vegetativ | 0.3 | 0.15 | 0.04 | 0.03 |
| Blüte | 0.2 | 0.1 | 0.03 | 0.02 |

KA-Felder: `nutrient_profiles.manganese_ppm`, `nutrient_profiles.zinc_ppm`, `nutrient_profiles.copper_ppm`, `nutrient_profiles.molybdenum_ppm`.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterhärte-Rating | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme + Monat | move_indoors (Okt) | `overwintering_profiles.winter_action` |
| Frühjahrs-Maßnahme + Monat | move_outdoors (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Winterquartier Temp min (°C) | 5 | `overwintering_profiles.winter_quarter_temp_min` |
| Winterquartier Temp max (°C) | 15 | `overwintering_profiles.winter_quarter_temp_max` |
| Winterquartier Licht | semi_bright | `overwintering_profiles.winter_quarter_light` |
| Winter-Gießen | reduced | `overwintering_profiles.winter_watering` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Hinweis Rating:** `frost_free` ist der korrekte Enum-Wert: Bubikopf ist in Mitteleuropa (USDA 6–8) nicht winterhart und wird als frostempfindliche Kübel-/Zimmerpflanze frostfrei (≥ 5 °C) drinnen überwintert. Nur in milden Regionen (USDA 9a–11b) bleibt er im Freiland; dort genügt eine Mulchauflage (`needs_protection` wäre dort die Alternative).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate | Etablierungszeit |
|----------|--------------------|----------------|--------------|------------------|
| Raubmilbe (Hypoaspis) | Stratiolaelaps scimitus | Trauermücken (Larven) | 100–250/m² präventiv, bis 1.000/m² kurativ | 2–3 Wochen |
| Insektenpathogener Nematode | Steinernema feltiae | Trauermücken (Larven) | ca. 250.000–500.000/m² (Substratdrench) | wenige Tage |
| Blattlaus-Schlupfwespe | Aphidius colemani | Blattläuse | 0,5–3/m² präventiv, wöchentlich bis etabliert | 2–3 Wochen (Mumienbildung) |
| Gallmücke | Aphidoletes aphidimyza | Blattläuse | 0,5–1/m², bei Befallsnestern höher | 2–3 Wochen |

**Hinweis:** Nützling-Wirt-Zuordnung passt zu den in §5.1 gelisteten Schädlingen (Trauermücken *Bradysia* spp. → *Stratiolaelaps* + *Steinernema feltiae*; Blattläuse → *Aphidius colemani* + *Aphidoletes aphidimyza*). Die dauerfeuchten Terrarium-/Topfbedingungen begünstigen Trauermücken; *Steinernema feltiae* und *Stratiolaelaps* werden bevorzugt kombiniert ausgebracht.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

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
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [RHS — Soleirolia soleirolii](https://www.rhs.org.uk/plants/17471/soleirolia-soleirolii/details) — pH-Adaptabilität, Sonne/Schatten, Feuchte (moist but well-drained), Hardiness H4
7. [Missouri Botanical Garden — Soleirolia soleirolii Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=287425) — Wasserbedarf, Staunässe-Intoleranz, Optimaltemperatur (Tag 16–18 °C / Nacht 10–13 °C), Frostintoleranz
8. [EpicGardening — Baby Tears Plant](https://www.epicgardening.com/baby-tears-plant/) — Boden-pH 5.0–6.0
9. [Florgeous — Baby's Tears Plant Care](https://florgeous.com/babys-tears-plant-care/) — Boden-pH (sauer < 6.0)
10. [Plantiary — Soleirolia soleirolii Care Guide](https://plantiary.com/plant/soleirolia-soleirolii_307.html) — flaches Wurzelsystem, Staunässe-Intoleranz
11. [Functional Plant Biology — Low-level CAM in Pilea peperomioides (Urticaceae)](https://www.publish.csiro.au/fp/fulltext/FP20151) — Urticaceae primär C3-Photosynthese (CAM nur bei sukkulenten Stress-Ausnahmen); Begründung Einstufung c3
12. [ScienceDirect — Light Compensation overview](https://www.sciencedirect.com/topics/engineering/light-compensation) — Lichtkompensationspunkt schattentoleranter Arten 10–50 µmol/m²/s
13. [Grokipedia — Compensation point](https://grokipedia.com/page/Compensation_point) — Unterwuchs-Lichtniveaus 1–2 % Volllicht, niedriger LCP schattentoleranter Arten
14. [Oxford Academic / Plant Physiology — Phytochrome B and low R:FR canopy shade](https://academic.oup.com/plphys/article/165/4/1698/6113297) — erhöhte Far-Red-Fraction (niedriges R:FR) im Schatten/Unterwuchs
15. [Bugs for Growers — Biocontrol of fungus gnats](https://blog.bugsforgrowers.com/natural-predators/entomopathogenic-nematodes/beneficial-nematodes/two-biocontrol-agents-for-effective-control-of-fungus-gnats/) — Steinernema feltiae + Stratiolaelaps scimitus Ausbringraten gegen Trauermücken
16. [UC IPM — Fungus Gnats](https://ipm.ucanr.edu/home-and-landscape/fungus-gnats/) — Nematoden-/Raubmilben-Ausbringung gegen Trauermückenlarven
17. [Sound Horticulture — Aphidius colemani / Aphidoletes aphidimyza Tech Sheets](https://soundhorticulture.com/pages/aphids) — Ausbringraten und Etablierungszeit Blattlaus-Nützlinge
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
<!-- Quelle: growing-phase-auditor 2026-07 -->
18. [Plantura — Bubikopf Pflanzenportrait](https://www.plantura.garden/zimmerpflanzen/bubikopf/bubikopf-pflanzenportrait) — Blütezeit April–Juni, Vermehrung ausschließlich Teilung/Stecklinge, "bedingt winterhart"
19. [Zimmerpflanzen-FAQ — Soleirolia soleirolii](https://zimmerpflanzen-faq.de/soleirolia-soleirolii/) — Vermehrung ausschließlich Teilung/Stecklinge (kein Saatgut)
<!-- /Quelle: growing-phase-auditor 2026-07 -->
