# Kentia-Palme — Howea forsteriana

> **Import-Ziel:** Kamerplanter Stammdaten (REQ-001, REQ-003, REQ-004, REQ-010, REQ-013, REQ-022)
> **Erstellt:** 2026-03-11
> **Quellen:** [Healthy Houseplants](https://www.healthyhouseplants.com/indoor-houseplants/kentia-palm-howea-forsteriana-care-guide-and-plant-information/), [Gardenia.net](https://www.gardenia.net/plant/howea-forsteriana-kentia-palm-grow-and-care-tips), [Gardening Know How](https://www.gardeningknowhow.com/houseplants/kentia-palm/howea-forsteriana-kentia-palm.htm), [NC State Extension](https://plants.ces.ncsu.edu/plants/howea-forsteriana/), [ASPCA](https://www.aspca.org/)

---

## 1. Taxonomie & Stammdaten

### 1.1 Botanische Einordnung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Wissenschaftlicher Name | Howea forsteriana | `species.scientific_name` |
| Volksnamen (DE/EN) | Kentia-Palme, Paradiespalme; Kentia Palm, Sentry Palm, Paradise Palm | `species.common_names` |
| Familie | Arecaceae | `species.family` → `botanical_families.name` |
| Gattung | Howea | `species.genus` |
| Ordnung | Arecales | `botanical_families.order` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Photosynthese-Typ (photosynthesis type) | c3 | `species.photosynthesis_type` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Wuchsform | tree | `species.growth_habit` |
| Wurzeltyp | fibrous | `species.root_type` |
| Lebenszyklus | perennial | `lifecycle_configs.cycle_type` |
| Blühstrategie (flowering strategy) | polycarpic (mehrjährig wiederholt blühend) | `lifecycle_configs.flowering_strategy` |
| Typische Lebensdauer (Jahre) | 50–100+ | `lifecycle_configs.typical_lifespan_years` |
| Photoperiode | day_neutral | `lifecycle_configs.photoperiod_type` |
| Dormanz erforderlich | false | `lifecycle_configs.dormancy_required` |
| Vernalisation erforderlich | false | `lifecycle_configs.vernalization_required` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| Kritische Tageslänge (critical day length, h) | <!-- DATEN FEHLEN: tagneutral (day_neutral), kein Kurz-/Langtag-Schwellenwert; numerisches Feld bleibt leer --> | `lifecycle_configs.critical_day_length_hours` |
| GDD-Basistemperatur (base temp, °C) | 10 | `species.base_temp` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| USDA Zonen | 9b, 10a, 10b, 11a, 11b | `species.hardiness_zones` |
| Frostempfindlichkeit | half_hardy | `species.frost_sensitivity` |
| Winterhaerte-Detail | Halbfrosthart — toleriert kurze Fröste bis -3°C (25°F). Mindesttemperatur 5°C, optimal 18–27°C. | `species.hardiness_detail` |
| Heimat | Lord-Howe-Insel (Australien) — subtropischer Regenwald | `species.native_habitat` |
| Allelopathie-Score | 0.0 | `species.allelopathy_score` |
| Nährstoffbedarf-Stufe | light_feeder | `species.nutrient_demand_level` |
| Gründüngung geeignet | false | `species.green_manure_suitable` |
| Traits | ornamental | `species.traits` |

**Hinweis:** Die Kentia-Palme ist die eleganteste und robusteste Zimmerpalme — seit dem Viktorianischen Zeitalter eine beliebte Innenraumpflanze. Sie toleriert niedrige Lichtverhältnisse besser als fast alle anderen Palmen und stellt keine hohen Ansprüche. Wächst sehr langsam (6–12 cm/Jahr) und kann Jahrzehnte im gleichen Topf verbringen. Schlüsselschwäche: empfindlich gegenüber Fluorid und Salzansammlungen im Substrat — Leitungswasser über Nacht stehen lassen oder gefiltertes Wasser verwenden.

### 1.2 Aussaat- & Erntezeiten

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vorkultur (Wochen vor letztem Frost) | Entfällt | `species.sowing_indoor_weeks_before_last_frost` |
| Direktsaat-Monate | Entfällt | `species.direct_sow_months` |
| Erntemonate | Entfällt | `species.harvest_months` |
| Blütemonate | Entfällt (blüht nicht zuverlässig in Zimmerkultur) | `species.bloom_months` |

### 1.3 Vermehrung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Vermehrungsmethoden | seed | `species.propagation_methods` |
| Schwierigkeit | difficult | `species.propagation_difficulty` |

**Hinweis:** Nur durch Samen vermehrbar (keine Teilung oder Stecklinge). Samen langsam in warmem Substrat (25–30°C) säen, Keimung 3 Monate bis zu mehreren Jahren. Kommerziell werden mehrere Sämlinge pro Topf gesetzt für einen buschigeren Wuchs.

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
| Pollenallergen | false | `species.allergen_info.pollen_allergen` |

**Hinweis:** ASPCA listet Howea forsteriana als nicht giftig für Katzen und Hunde. Eine der haustierfreundlichsten Palmen.

### 1.5 Rückschnitt

| Feld | Wert | KA-Feld |
|------|------|---------|
| Rückschnitt-Typ | none | `species.pruning_type` |
| Rückschnitt-Monate | — | `species.pruning_months` |

**Hinweis:** Kein Rückschnitt. Nur vollständig abgestorbene, braune Wedel an der Basis entfernen. Niemals grüne oder noch teilweise grüne Wedel schneiden — das schadet der Pflanze dauerhaft.

### 1.6 Anbaubedingungen

| Feld | Wert | KA-Feld |
|------|------|---------|
| Topfkultur geeignet | yes | `species.container_suitable` |
| Empf. Topfvolumen (L) | 10–30 | `species.recommended_container_volume_l` |
| Min. Topftiefe (cm) | 30 | `species.min_container_depth_cm` |
| Wuchshöhe (cm) | 150–300 (indoor, sehr langsam) | `species.mature_height_cm` |
| Wuchsbreite (cm) | 80–150 | `species.mature_width_cm` |
| Indoor-Anbau | yes | `species.indoor_suitable` |
| Balkon-/Terrassenanbau | limited (Halbschatten, frostfrei, windgeschützt) | `species.balcony_suitable` |
| Gewächshaus empfohlen | false | `species.greenhouse_recommended` |
| Rankhilfe/Stütze nötig | false | `species.support_required` |
| Substrat-Empfehlung (Topf) | Gute, lockere Palmenerde oder Einheitserde mit 20% Perlite. pH 6.0–7.0. Gute Drainage. Nicht zu häufig umtopfen — mag leicht beengte Wurzeln. | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 1.7 Umgebungs-Physiologie & Standortqualität

| Feld | Wert | KA-Feld |
|------|------|---------|
| Lichtkompensationspunkt min (light compensation point, PPFD µmol/m²/s) | 5 | `species.light_compensation_point_ppfd_min` |
| Lichtkompensationspunkt max (PPFD µmol/m²/s) | 25 | `species.light_compensation_point_ppfd_max` |
| Schatten-/Sonnentoleranz (shade tolerance) | partial_shade | `species.shade_tolerance` |
| Effektive Wurzeltiefe (effective root depth, cm) | <!-- DATEN FEHLEN: keine quantitative Wurzeltiefen-Angabe in geprüften Quellen; fibröses, bruchempfindliches Flachwurzelsystem, Mindest-Topftiefe 30 cm --> | `species.effective_root_depth_cm` |
| Staunässe-Toleranz (waterlogging tolerance) | sensitive | `species.waterlogging_tolerance` |
| Salztoleranz-Klasse (salt tolerance class) | moderately_tolerant | `species.salt_tolerance_class` |
| Salztoleranz ECe-Schwelle (Substrat-ECe, dS/m) | <!-- DATEN FEHLEN: Quellen belegen nur aerosole Salzsprüh-Toleranz (salt spray), keine Maas-Hoffman-ECe-Schwelle für Substrat-Salinität --> | `species.salt_tolerance_ece_threshold_ds_m` |
| Salztoleranz Slope (%/dS/m) | <!-- DATEN FEHLEN: kein Maas-Hoffman-Slope belegt --> | `species.salt_tolerance_slope_pct` |
| Boden-pH-Vorzug (soil pH preference) | 6.0–7.0 | `species.soil_ph_preference` |

**Hinweis:** Der Lichtkompensationspunkt (light compensation point) ist quellenseitig nicht artspezifisch für *Howea forsteriana* gemessen; angegeben ist der für schattentolerante Unterwuchs-Arten (shade-tolerant understory) belegte Bereich (5–25 µmol/m²/s, im Waldunterwuchs meist < 20 µmol/m²/s). Palmen erreichen ihre ausgeprägte Schattentoleranz physiologisch primär über sehr niedrige Dunkelatmung (dark respiration), nicht über maximale Photosynthese. Die Salztoleranz-Klasse `moderately_tolerant` bezieht sich auf **aerosole Salzsprüh-Belastung** (salt spray, z.B. Küstenlage), nicht auf Substrat-Salinität — gegenüber Salzansammlung im Wurzelballen (Gießwasser-Salze, Fluorid) ist die Art empfindlich (siehe §1.6, §3.2).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 2. Wachstumsphasen

### 2.1 Phasenübersicht

| Phase | Dauer (Tage) | Reihenfolge | Terminal | Ernte erlaubt | Stresstoleranz |
|-------|-------------|-------------|----------|---------------|----------------|
| Aktives Wachstum (Frühling/Sommer) | 180–210 | 1 | false | false | medium |
| Winterruhe (Wachstum verlangsamt) | 120–150 | 2 | false | false | medium |

### 2.2 Phasen-Anforderungsprofile

#### Phase: Aktives Wachstum (März–September)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 100–400 | `requirement_profiles.light_ppfd_target` |
| DLI (mol/m²/Tag) | 8–18 | `requirement_profiles.dli_target_mol` |
| Photoperiode (Stunden) | 12–16 | `requirement_profiles.photoperiod_hours` |
| Temperatur Tag (°C) | 18–27 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 14–22 | `requirement_profiles.temperature_night_c` |
| Luftfeuchtigkeit Tag (%) | 50–70 | `requirement_profiles.humidity_day_percent` |
| VPD-Ziel (kPa) | 0.6–1.2 | `requirement_profiles.vpd_target_kpa` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.6 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 25–28 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 7–10 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 300–800 | `requirement_profiles.irrigation_volume_ml_per_plant` |

#### Phase: Winterruhe (Oktober–Februar)

| Parameter | Wert | KA-Feld |
|-----------|------|---------|
| Licht PPFD (µmol/m²/s) | 80–300 | `requirement_profiles.light_ppfd_target` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| DLI (mol/m²/Tag) | 5–12 | `requirement_profiles.dli_target_mol` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Temperatur Tag (°C) | 12–20 | `requirement_profiles.temperature_day_c` |
| Temperatur Nacht (°C) | 10–16 | `requirement_profiles.temperature_night_c` |
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
| VPD-Schwelle (kPa) | 1.3 | `requirement_profiles.vpd_threshold_kpa` |
| VPD-Sensitivität (vpd sensitivity) | medium | `requirement_profiles.vpd_sensitivity` |
| Photosynthese-T_opt (°C) | 18–22 | `requirement_profiles.photosynthesis_temp_opt_c` |
| Far-Red-Fraction FR/(R+FR) | 0.6–0.7 | `requirement_profiles.far_red_fraction` |
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
| Gießintervall (Tage) | 14–21 | `requirement_profiles.irrigation_frequency_days` |
| Gießmenge (ml/Pflanze) | 150–400 | `requirement_profiles.irrigation_volume_ml_per_plant` |

### 2.3 Nährstoffprofile je Phase

| Phase | NPK-Verhältnis | EC (mS) | pH | Ca (ppm) | Mg (ppm) |
|-------|----------------|---------|-----|----------|----------|
| Aktives Wachstum | 3:1:2 | 0.6–1.0 | 6.0–7.0 | 80 | 30 |
| Winterruhe | 0:0:0 | 0.0 | 6.0–7.0 | — | — |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
**Mikronährstoffe je Phase (Aktives Wachstum)** — `nutrient_profiles.*`:

| Mikronährstoff | Wert (ppm) | KA-Feld |
|----------------|-----------|---------|
| Mangan (Mn) | <!-- DATEN FEHLEN: keine artspezifische Lösungs-ppm belegt; UF/IFAS empfiehlt Mikronährstoff-Blend (Sulfatformen Mn/Zn/Cu/Fe) im Substrat — Palmen sind Mn-empfindlich (Frizzletop), Mn-Versorgung sicherstellen --> | `nutrient_profiles.manganese_ppm` |
| Zink (Zn) | <!-- DATEN FEHLEN: keine artspezifische Lösungs-ppm belegt; im Mikronährstoff-Blend (Sulfatform) enthalten --> | `nutrient_profiles.zinc_ppm` |
| Kupfer (Cu) | <!-- DATEN FEHLEN: keine artspezifische Lösungs-ppm belegt; im Mikronährstoff-Blend (Sulfatform) enthalten --> | `nutrient_profiles.copper_ppm` |
| Molybdän (Mo) | <!-- DATEN FEHLEN: keine artspezifische Lösungs-ppm belegt; Palmen selten Mo-limitiert --> | `nutrient_profiles.molybdenum_ppm` |

**Hinweis:** Palmen sind ausgeprägt **Mangan-empfindlich** — Mn-Mangel verursacht „Frizzletop" (gekräuselte, deformierte Jungwedel), begünstigt durch hohen pH und kalte Wurzeltemperaturen. UF/IFAS empfiehlt für Topf-Palmen einen vollständigen Mikronährstoff-Blend mit Sulfatformen von Mn, Zn, Cu und Fe; artspezifische Lösungs-ppm-Werte für *Howea forsteriana* sind in den geprüften Quellen nicht belegt.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 3. Düngung

### 3.1 Empfohlene Düngerprodukte

#### Mineralisch

| Produkt | Marke | Typ | NPK | Dosierung | Phasen |
|---------|-------|-----|-----|-----------|--------|
| Palmen-Dünger | Compo | base | 7-3-7 | 5 ml/L (alle 2 Wochen) | Wachstum |
| Grünpflanzen-Dünger | Substral | base | 7-3-7 | 4 ml/L | Wachstum |

#### Organisch

| Produkt | Marke | Typ | Ausbringrate | Saison |
|---------|-------|-----|-------------|--------|
| Wurmhumus | Eigenherstellung | organisch | 15% Substratanteil | Umtopfen |
| Langzeitdünger-Stäbchen | Compo | organisch-mineralisch | 3–4 Stäbchen/Topf | Frühjahr |

### 3.2 Besondere Hinweise

Alle 2 Wochen März bis September. Oktober bis Februar: kein Dünger (Düngung im Winter schadet). Nur halbe Empfehlungsdosis verwenden — Kentia ist empfindlich gegen Überdüngung und Salzansammlungen. Wasser über Nacht stehen lassen (Chlor + Fluorid reduzieren) oder gefiltertes/destilliertes Wasser verwenden.

---

## 4. Pflegehinweise

### 4.1 Care-Profil

| Feld | Wert | KA-Feld |
|------|------|---------|
| Pflege-Stil | tropical | `care_profiles.care_style` |
| Gießintervall Sommer (Tage) | 7–10 | `care_profiles.watering_interval_days` |
| Winter-Multiplikator | 2.0 | `care_profiles.winter_watering_multiplier` |
| Gießmethode | drench_and_drain | `care_profiles.watering_method` |
| Wasserqualität-Hinweis | Fluoridarmes Wasser (gefiltertes oder abgestandenes Leitungswasser); zu viel Fluorid/Salz verursacht braune Blattspitzen | `care_profiles.water_quality_hint` |
| Düngeintervall (Tage) | 14 | `care_profiles.fertilizing_interval_days` |
| Dünge-Aktivmonate | 3–9 | `care_profiles.fertilizing_active_months` |
| Umtopfintervall (Monate) | 36–48 (sehr langsam wachsend) | `care_profiles.repotting_interval_months` |
| Schädlingskontroll-Intervall (Tage) | 14 | `care_profiles.pest_check_interval_days` |
| Luftfeuchtigkeitsprüfung | true | `care_profiles.humidity_check_enabled` |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 4.3 Überwinterung

| Feld | Wert | KA-Feld |
|------|------|---------|
| Winterhärte-Einstufung (hardiness rating) | frost_free | `overwintering_profiles.hardiness_rating` |
| Winter-Maßnahme (winter action) | move_indoors | `overwintering_profiles.winter_action` |
| Winter-Maßnahme Monat | 10 (Oktober, vor erstem Frost) | `overwintering_profiles.winter_action_month` |
| Frühjahrs-Maßnahme (spring action) | move_outdoors | `overwintering_profiles.spring_action` |
| Frühjahrs-Maßnahme Monat | 5 (Mai, nach den Eisheiligen) | `overwintering_profiles.spring_action_month` |
| Winterquartier-Temperatur (°C) | 10–18 (Minimum 5°C, nie unter -3°C) | `overwintering_profiles.winter_quarter_temp_c` |
| Winterquartier-Licht | hell bis halbschattig; helles Fenster oder Wintergarten, kein direktes Sommer-Mittagslicht | `overwintering_profiles.winter_quarter_light` |
| Winterquartier-Gießen | sparsam, Substrat antrocknen lassen; Gießintervall 14–21 Tage (siehe §2.2 Winterruhe) | `overwintering_profiles.winter_quarter_watering` |

**Hinweis:** In Mitteleuropa (USDA 6–8) ist die Kentia-Palme **nicht winterhart** und muss als Kübelpflanze frostfrei (frost_free) überwintert werden — keine Auspflanzung im Freiland. Sie verträgt allenfalls kurze, leichte Fröste bis -3°C, dauerhaft sollte die Temperatur nicht unter 5°C fallen. Ideal ist ein helles, kühles bis temperiertes Winterquartier (10–18°C). Den Sommer kann sie an einem halbschattigen, windgeschützten Platz im Freien verbringen (Ausräumen nach den Eisheiligen, Einräumen vor dem ersten Herbstfrost), wobei sie vor direkter Mittagssonne langsam abgehärtet (harden off) werden sollte.
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 5. Schädlinge & Krankheiten

### 5.1 Häufige Schädlinge

| Schädling | Wissenschaftl. Name | Symptome | Erkennungsschwierigkeit |
|-----------|-------------------|----------|------------------------|
| Spinnmilbe | Tetranychus urticae | Gespinste, Wedel vergilben und vertrocknen | medium |
| Schmierlaus | Pseudococcus spp. | Wollflecken in Wedelbasisachseln | easy |
| Schildlaus | Coccus hesperidum | Braune Schilder auf Blattstielen | medium |

### 5.2 Häufige Krankheiten

| Krankheit | Erregertyp | Symptome | Auslöser |
|-----------|-----------|----------|----------|
| Wurzelfäule | fungal | Welke, gelbe Wedel, weiche Stängelbasis | Staunässe |
| Fluorid-/Salztoxizität | physiologisch | Braune Blattspitzen | Fluorid/Salz im Gießwasser |
| Blattflecken | fungal | Braune Flecken mit gelbem Rand | Nasses Laub, Staunässe |

### 5.3 Behandlungsmethoden

| Methode | Typ | Anwendung | Karenzzeit | Gegen |
|---------|-----|-----------|------------|-------|
| Neemöl | biological | Sprühen 0.5% | 0 Tage | Spinnmilbe, Schmierläuse |
| Alkohol 70% | mechanical | Wattestäbchen | 0 Tage | Schildlaus |
| Gefiltertes Wasser | cultural | Wasserquelle wechseln | 0 | Fluoridtoxizität (Prävention) |
| Weniger gießen | cultural | Gießintervall verlängern | 0 | Wurzelfäule (Prävention) |

<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
### 5.4 Nützlinge (Biologische Bekämpfung)

| Nützling (beneficial) | Wissenschaftl. Name | Ziel-Schädling | Ausbringrate (pro m²) | Etablierungszeit |
|-----------------------|---------------------|----------------|-----------------------|------------------|
| Raubmilbe | Phytoseiulus persimilis | Spinnmilbe (Tetranychus urticae) | 100–200 | ca. 1–2 Wochen |
| Australischer Marienkäfer (Mealybug Destroyer) | Cryptolaemus montrouzieri | Schmierlaus (Pseudococcus spp.) | 2–5 (bis 10 bei starkem Befall) | ca. 4 Wochen (Ei→Adult), 3 Ausbringungen im 1–2-Wochen-Takt |
| Schlupfwespe (Weichschildlaus-Parasitoid) | Metaphycus helvolus | Weichschildlaus (Coccus hesperidum) | 5 (3 Ausbringungen im 14-Tage-Takt) | ca. 2–4 Wochen |

**Hinweis:** Nützling-Wirt-Zuordnung beachten — *Metaphycus helvolus* parasitiert **Weichschildläuse** (Coccidae, z.B. *Coccus hesperidum*), nicht Panzer-/Deckelschildläuse. *Cryptolaemus montrouzieri* ist auf **Schmierläuse** (Pseudococcidae) spezialisiert. *Phytoseiulus persimilis* benötigt Luftfeuchte > 60% und Temperaturen 18–27°C, die in der tropischen Kentia-Kultur ohnehin angestrebt werden. Im Innenraum sind biologische Maßnahmen vor allem in Wintergärten/Gewächshäusern praktikabel; einzelne Zimmerexemplare werden meist mechanisch/mit Neemöl behandelt (siehe §5.3).
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->

---

## 6. Fruchtfolge & Mischkultur

Entfällt — reine Zimmerpflanze.

---

## 7. Ähnliche Arten & Alternativen

| Art | Wissenschaftl. Name | Ähnlichkeit | Vorteil |
|-----|-------------------|-------------|---------|
| Stubenpalme | Chamaedorea elegans | Arecaceae, kompaktere Palme | Viel kleiner, für beengte Räume |
| Areka-Palme | Dypsis lutescens | Arecaceae, ähnlicher Look | Schneller wachsend, buschiger |
| Livistona-Palme | Livistona rotundifolia | Arecaceae, Fächerpalme | Runde Wedel, andere Textur |

---

## 8. CSV-Import-Daten

### 8.1 Species CSV-Zeile

```csv
scientific_name,common_names,family,genus,cycle_type,photoperiod_type,growth_habit,root_type,hardiness_zones,native_habitat,container_suitable,recommended_container_volume_l,min_container_depth_cm,mature_height_cm,mature_width_cm,indoor_suitable,balcony_suitable,support_required,nutrient_demand_level
Howea forsteriana,"Kentia-Palme;Paradiespalme;Kentia Palm;Sentry Palm",Arecaceae,Howea,perennial,day_neutral,tree,fibrous,"9b;10a;10b;11a;11b","Lord-Howe-Insel (Australien)",yes,10-30,30,150-300,80-150,yes,limited,false,light_feeder
```

---

## Quellenverzeichnis

1. [Healthy Houseplants — Kentia Palm](https://www.healthyhouseplants.com/indoor-houseplants/kentia-palm-howea-forsteriana-care-guide-and-plant-information/) — Pflegehinweise, Fluoridsensitivität
2. [Gardenia.net — Howea forsteriana](https://www.gardenia.net/plant/howea-forsteriana-kentia-palm-grow-and-care-tips) — Botanische Daten, USDA-Zonen
3. [Gardening Know How — Kentia Palm](https://www.gardeningknowhow.com/houseplants/kentia-palm/howea-forsteriana-kentia-palm.htm) — Allgemeine Pflege
4. [NC State Extension — Howea forsteriana](https://plants.ces.ncsu.edu/plants/howea-forsteriana/) — Wissenschaftliche Basisdaten; Boden-pH (Acid <6.0 / Neutral 6.0–8.0), Licht (Dappled/Partial Shade), Salztoleranz (salt spray), Bodentexturen
5. [ASPCA Animal Poison Control](https://www.aspca.org/) — Toxizität (nicht giftig)
<!-- Quelle: Steckbrief-Erweiterung 2026-06 -->
6. [UF/IFAS — Howea forsteriana: Sentry Palm (ENH456/ST297)](https://ask.ifas.ufl.edu/publication/ST297) — Boden-pH-Anpassung, Salzsprüh-Toleranz (moderately tolerant), Schatten-/Vollsonne-Toleranz, USDA-Zonen
7. [Wikipedia — Arecaceae](https://en.wikipedia.org/wiki/Arecaceae) — Palmen als Monokotyledonen mit C3-Photosynthese
8. [Renninger & Phillips, „Convergent Evolution towards High Net Carbon Gain Efficiency Contributes to the Shade Tolerance of Palms" (PMC4604201)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4604201/) — Schattentoleranz der Palmen über niedrige Dunkelatmung (C3-konsistent)
9. [ScienceDirect Topics — Light Compensation Point](https://www.sciencedirect.com/topics/engineering/light-compensation) — Lichtkompensationspunkt schattentoleranter Unterwuchs-Arten (10–50 µmol/m²/s; Unterwuchs < 20)
10. [Wikipedia — Growing degree-day](https://en.wikipedia.org/wiki/Growing_degree-day) — GDD-Basistemperatur 10°C für wärmeliebende Arten (warm-season)
11. [Suresh et al. 2021, „Phenological stages and degree days of oil palm" (Ann. Appl. Biol.)](https://onlinelibrary.wiley.com/doi/10.1111/aab.12641) — GDD-Phänologie tropischer Palmen (Basistemperatur warm-season)
12. [UF/IFAS — Nutrition and Fertilization of Palms in Containers (ENH1010/EP262)](https://ask.ifas.ufl.edu/publication/ep262) — Mikronährstoff-Blend (Sulfatformen Mn/Zn/Cu/Fe) für Topf-Palmen, 3-1-2-NPK-Verhältnis
13. [UF/IFAS — Manganese Deficiency in Palms (ENH1015/EP267)](https://ask.ifas.ufl.edu/publication/EP267) — Mn-Empfindlichkeit der Palmen, „Frizzletop", pH/Wurzeltemperatur-Einfluss
14. [Koppert — Cryptolaemus montrouzieri](https://www.koppert.com/crop-protection/biological-pest-control/predatory-insects/cryptolaemus-montrouzieri/) — Nützling gegen Schmierläuse, Ausbringrate
15. [Interiorlandscaping.co.uk — Biological Controls](http://www.interiorlandscaping.co.uk/Biologica.htm) — Ausbringraten Phytoseiulus persimilis, Metaphycus helvolus, Cryptolaemus montrouzieri
<!-- /Quelle: Steckbrief-Erweiterung 2026-06 -->
