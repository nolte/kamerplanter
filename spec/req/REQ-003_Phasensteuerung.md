# Spezifikation: REQ-003 - Phasensteuerung

```yaml
ID: REQ-003
Titel: Phänologische Phasensteuerung & Ressourcen-Profile
Kategorie: Wachstumslogik
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 2.8 (Spec-Audit D-Umsetzung: kanonisches PhaseType, Biennial-Zyklus, monokarpe Terminal-Transition, Juvenil-Skip, Post-Harvest-Handoff)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 2.8 | 2026-07-02 | **Spec-Audit D-Umsetzung (vollständige Lebenszyklus-Abbildung über Arten):** (1) **B1/D2** — kanonisches `PhaseType`-Literal um `germination`, `rooting` + `bolting` ergänzt (17 Werte), einzige maßgebliche Phasen-Wertliste. (2) **D6** — monokarpe Terminal-Transition: `flowering_strategy=monocarpic` (REQ-001) erzwingt terminale Nach-Blüte-Seneszenz statt `is_cycle_restart`. (3) **D1** — Biennial-Lebenszyklus: `CyclicLifecycleEngine` (ehem. `PerennialCycleEngine`) unterstützt `cycle_type IN ('perennial','biennial')`; Biennial-Phasentemplate (Jahr 1 → Dormanz → Jahr 2 Schossen/Blüte/Samen → terminal). (4) **D4** — Juvenil-Skip als maturity-gated `conditional`-Transition (mehrwertige `next_phase` + `required_conditions`). (5) **D3** — expliziter Post-Harvest-Handoff Lifecycle→REQ-008-Batch. Quelle: `.audits/spec-audit/lifecycle-audit-report.md`. |
| 2.7 | 2026-06-15 | **Phase A — Lebenszyklus-Felder (Plan WP-3/WP-4):** `LifecycleConfig.flowering_strategy` (`monocarpic`/`polycarpic`) als eigene Reproduktions-Achse — „blüht einmal, stirbt dann" (Agave, viele Bambusse) auch bei mehrjährigem Wuchs. `cultivation_cycle_type` trennt die Kultur-Praxis von der botanischen `cycle_type`. Beide optional, non-breaking. Quelle: `spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` §2.1/§2.2. _(v2.8: Felder in REQ-001 v4.5 im Body umgesetzt; Phasen-Logik hier ergänzt.)_ |
| 2.6 | 2026-06-11 | **Umgebungs-Physiologie (Plant-Profile Environmental Research):** `requirement_profiles` um `vpd_threshold_kpa` + `vpd_sensitivity` (artspezifische VPD-Schwelle als echter Automatik-Trigger), `photosynthesis_temp_opt_c` (T_opt getrennt vom Tag-Zielwert) und `far_red_fraction` (phytochrom-prädiktive Shade-Avoidance-Metrik, ableitbar aus `light_spectrum`) erweitert. Quelle: `spec/analysis/plant-profile-completeness-research.md`. |
| 2.5 | 2026-04-27 | **ADR-003 (W-014 Sensor-Retention für Perennials):** SeasonalCycle um `sensor_aggregates`, `aggregate_computed_at`, `aggregate_computed_by`, `aggregate_source_retention_horizon`, `aggregate_config` erweitert. Neue `SensorAggregateEngine` mit avg/min/max/p10/p90 für Quantile-Sensoren und sum/avg_per_day für DLI. Celery-Task `compute_seasonal_aggregates_task` triggert beim Saisonende. Lazy Re-Computation bei Sensor-Drift. Backfill-Migration für bestehende Saisons. |
| 2.4 | 2026-04-27 | **W-003 Fix (Run-Membership-Guard):** Direkter Phasenwechsel auf einer `PlantInstance`, die Mitglied eines aktiven `PlantingRun` ist (`run_contains` mit `detached_at = null`, `run.status = 'active'`), wird abgelehnt. `PhaseTransitionEngine.assert_transition_allowed()` führt einen AQL-Lookup durch und wirft `RunMembershipConflictError` → API liefert HTTP 409 mit strukturiertem Fehler-Body. Batch-Phasenwechsel ist All-or-Nothing. Drei neue DoD-Punkte (§6). |
| 2.3 | (vorher) | DORMANCY-Phase für perenniale Zimmerpflanzen, Abgrenzung FLUSHING vs. DORMANCY. |

## 1. Business Case

**User Story:** "Als Gärtner möchte ich, dass das System die aktuelle Wachstumsphase automatisch erkennt und Ressourcen (Licht, Wasser, Nährstoffe) dynamisch anpasst, um optimale Wachstumsbedingungen zu gewährleisten."

**Beschreibung:**
Das System implementiert eine State-Machine für phänologische Phasenübergänge mit:
- **Automatische Transitions:** Zeitbasiert (nach N Tagen) oder ereignisgesteuert (manuelle Blüte-Einleitung)
- **Phasenspezifische Ressourcen-Profile:** Für Licht (PPFD, Spektrum, Photoperiode), Wasser (Frequenz, Volumen), Nährstoffe (NPK-Ratio, EC-Zielwerte)
- **Rückwärts-Kompatibilität:** Support für Spezies ohne definierte Phasen (Standardprofil)
- **Stress-Phasen:** Temporäre Zustände wie Hardening-Off, Drought-Stress für Terpen-Induktion

Typische Phasen-Sequenzen:
- **Annuelle (Ernte):** Keimung → Sämling → Vegetativ → Blüte → Fruchtreife → Seneszenz
- **Annuelle (Zierpflanze):** Keimung → Sämling → Vegetativ → Abhärtung → Blüte → Seneszenz (kein Ernte-Schritt; `allows_harvest: false` auf allen Phasen, `is_terminal: true` auf Seneszenz). Die `hardening_off`-Phase (7–14 Tage) ist obligatorisch bei Indoor-Voranzucht → Outdoor-Auspflanzung (AB-009).
<!-- Quelle: Agrarbiologie-Review AB-008, AB-009, 2026-03 -->
> **Pikier-Übergang (AB-008):** Der Übergang `seedling → vegetative` entspricht dem Pikieren. Nach dem Pikieren benötigen Zierpflanzen 3–5 Tage Erholungszeit (erhöhte Luftfeuchtigkeit 70–80%, gedämpftes Licht ~100 µmol/m²/s). Dies wird als Stress-Phase-Annotation auf dem Phasenübergang modelliert (analog `repotting_recovery` bei Zimmerpflanzen), nicht als eigene Phase.
- **Perenniale (Outdoor):** [Keimung → ...] → Dormanz → Neuaustrieb → [Wiederholt Vegetativ/Blüte]
- **Bienniale:** Jahr 1: Keimung → Vegetativ → Dormanz | Jahr 2: Neuaustrieb → Blüte → Samenreife
<!-- Quelle: Nährstoffplan-Review Monstera 2026-03 -->
- **Perenniale Zimmerpflanze (Indoor):** Bewurzelung → Juvenil → [Aktives Wachstum (Mär-Okt) → Dormanz (Nov-Feb)] ↻. Kein Ernteziel, kein Flushing im Hydro-Sinne. Die Dormanz-Phase (`dormancy`) bildet die saisonale Ruhephase ab: reduzierter Stoffwechsel, keine Düngung, verlängertes Gießintervall. `is_recurring: true` auf den zyklischen Phasen. Beispiel-Arten: Monstera, Ficus, Alocasia, Calathea.
- **Abgrenzung DORMANCY vs. FLUSHING:** `dormancy` ist biologisch bedingt (Photoperiode, Temperatur, genetisches Programm) und wiederholt sich saisonal. `flushing` ist eine aktive Kulturmaßnahme (Pre-Harvest-Flush, Substrat-Entsalzung) mit definiertem Anfang und Ende. Eine Zimmerpflanze in Winterruhe befindet sich in `dormancy`, nicht in `flushing`. Beide Phasen haben gemeinsam, dass keine oder minimale Düngung erfolgt, unterscheiden sich aber in Ursache und Kontext.
<!-- Quelle: Cannabis Indoor Grower Review G-009 -->
- **Autoflower (Cultivar-Level):** Keimung (3–5d) → Sämling (7–10d) → Vegetativ (14–21d) → Blüte (35–56d) → Ernte. Verkürzte Gesamtdauer (60–90 Tage). Übergang Vegi→Blüte ist zeitgesteuert (nach `autoflower_days_to_flower` Tagen), kein manueller/photoperiodischer Trigger. Lichtprofil bleibt durchgehend bei 20/4 oder 18/6 (kein Wechsel auf 12/12).
<!-- /Quelle: G-009 -->

**Dauerkulturen-Modus (Perennial):**
Mehrjährige Pflanzen (Obstbäume, Beerensträucher, Stauden) durchlaufen jährlich wiederkehrende
Zyklen statt eines einmaligen linearen Durchlaufs. Das System unterstützt:
- **Saisonale Zyklen:** Jedes Jahr bildet eine eigene Saison mit eigenem Phasen-Durchlauf
  (Dormanz → Austrieb → Vegetativ → Blüte → Fruchtentwicklung → Reife → Seneszenz → Dormanz)
- **Reifegrad-Tracking:** Juvenile Phase (kein Ertrag), Produktive Phase, Ertragsrückgang
- **Saison-Vergleich:** Ertrag und Performance über Jahre hinweg vergleichbar
- **Vernalisierung:** Kältestunden-Akkumulation pro Saison (nutzt VernalizationTracker aus REQ-001)

## 2. ArangoDB-Modellierung

### Dokumentsammlungen (Collections):
- **`growth_phases`** - Wachstumsphase
  - Properties:
    - `name: str` (z.B. "vegetative", "flowering", "dormancy", "ripening"). **Kanonischer Wertebereich = `PhaseType`-Literal (siehe Abschnitt 3, „TransitionTriggerType / PhaseType").** <!-- Spec-Audit 2026-07-02 B1: Diese Prosa-Liste war früher eine abweichende 7er-Teilmenge. Maßgeblich ist das kanonische `PhaseType`-Literal (17 Werte, inkl. der 2026-07-02 ergänzten `germination`, `rooting` und `bolting`). `harvest` ist dort bewusst NICHT enthalten (= Ernte-Event REQ-007, keine Phase); `drying`/`curing` sind Post-Harvest-Batch-Zustände (REQ-008), keine `growth_phases`. -->
    - `display_name: str` (z.B. "Vegetative Wachstumsphase")
    - `typical_duration_days: int`
    - `sequence_order: int`
    - `is_terminal: bool` (Letzte Phase vor Ernte/Tod — bei annuellen Zierpflanzen ist `senescence` terminal ohne `is_cycle_restart`)
    - `allows_harvest: bool` (Bei Zierpflanzen durchgehend `false`)
    - `allows_disposal: bool` (Default: `false`. Bei `true` kann die Pflanze nach Abschluss dieser Phase als entsorgt markiert werden — relevant für annuelle Zierpflanzen nach der Blüte/Seneszenz)
    - `stress_tolerance: Literal['low', 'medium', 'high']`
    - `is_recurring: bool` — Phase wiederholt sich jährlich (true für Dauerkulturen-Phasen)

- **`requirement_profiles`** - Ressourcen-Anforderungen
  - Properties:
    - `light_ppfd_target: int` (μmol/m²/s)
    - `dli_target_mol: Optional[float]` (Daily Light Integral in mol/m²/Tag — DLI = PPFD × h × 3600 / 1.000.000; Zimmerpflanzen Niedriglicht: 2-5, Zimmerpflanzen Mittellicht: 5-12, Zimmerpflanzen Hochlicht: 12-20, Salate: 12-17, Kräuter: 15-20, Tomaten: 20-30, Cannabis: 35-45. Hinweis: Nordfenster Deutschland Winter ≈ 1-2 mol/m²/d — unter Minimum für fast alle Zimmerpflanzen.)
    - `dli_min_mol: Optional[float]` (Minimaler DLI unter dem die Pflanze langfristig Schaden nimmt. Zimmerpflanzen: Schattentolerante 1.5, Halbschatten 3.0, Helles Licht 5.0, Volle Sonne 10.0)
    - `photoperiod_hours: float`
    - `light_spectrum: dict` (z.B. {"blue": 0.25, "green": 0.20, "red": 0.45, "far_red": 0.10}. Zimmerpflanzen: Breitbandiges Weißlicht (2700–6500K CCT) empfohlen. Tropische Grünpflanzen: hoher Blauanteil (400–500nm) für kompakten Wuchs. Sukkulenten: hoher Rotanteil + UV für Stressfärbung. Kurztagspflanzen (Kalanchoe, Schlumbergera): R:FR > 1.5 für Kompaktheit, Far-Red (730nm) für Blüteninduktion.)
    - `temperature_day_c: float`
    - `temperature_night_c: float`
    - `humidity_day_percent: int`
    - `humidity_night_percent: int`
    - `vpd_target_kpa: float`
    <!-- Quelle: Plant-Profile Environmental Research 2026-06 (spec/analysis/plant-profile-completeness-research.md) -->
    - `vpd_threshold_kpa: Optional[float]` (Art-/phasenspezifische VPD-Obergrenze, ab der die stomatäre Leitfähigkeit kollabiert und Photosynthese/Wachstum einbrechen (Carbon-Starvation/hydraulischer Stress). Ergänzt den `vpd_target_kpa`-Zielwert um eine individuelle Schwelle → echter Automatik-Trigger statt globalem Korridor. Einheit: kPa.)
    - `vpd_sensitivity: Optional[Literal['low', 'medium', 'high']]` (Stomatäre Empfindlichkeit gegenüber VPD-Schwankungen — `high` = enger Korridor, vorsichtigere Entfeuchtung/Bewässerung.)
    - `photosynthesis_temp_opt_c: Optional[float]` (Temperaturoptimum der Photosynthese (T_opt) für diese Phase, getrennt von `temperature_day_c`. Akklimatisationsplastisch — verschiebt sich mit der Wuchstemperatur (kalt gewachsen → niedrigeres Optimum). Steuert die Klima-Feinregelung in kontrollierten Umgebungen. Einheit: °C.)
    - `far_red_fraction: Optional[float]` (Dunkelrot-Anteil FR/(R+FR), 0–1 — phytochrom-prädiktive Metrik für Shade-Avoidance/Streckung/Blüteinduktion. Robuster als das R:FR-Verhältnis, das unter schmalbandigem LED gegen unendlich geht. Ableitbar aus `light_spectrum`. Offenes Tageslicht ≈ 0.5; hoher FR-Anteil fördert Streckung.)
    <!-- /Quelle: Plant-Profile Environmental Research 2026-06 -->
    - `co2_ppm: Optional[int]`
    - `irrigation_frequency_days: float`
    - `irrigation_volume_ml_per_plant: int`

- **`nutrient_profiles`** - NPK und Mikronährstoffe
  - Properties:
    - `npk_ratio: tuple[int, int, int]` (z.B. (3, 1, 2) für Vegi)
    - `target_ec_ms: float`
    - `target_ph: float`
    - `calcium_ppm: Optional[int]`
    - `magnesium_ppm: Optional[int]`
    - `micro_nutrients: dict[str, int]`

- **`phase_transition_rules`** - Übergangslogik
  - Properties:
    - `trigger_type: Literal['time_based', 'manual', 'event_based', 'conditional', 'gdd_based']`
    - `auto_transition_after_days: Optional[int]`
    - `gdd_threshold: Optional[float]` — Growing Degree Days bis Transition (z.B. Tomate Transplant→Blüte: ~300 GDD). Biologisch akkurater als Kalendertage, da temperaturabhängig.
    - `gdd_base_temp_c: Optional[float]` — Basistemperatur für GDD-Berechnung (Tomate: 10°C, Mais: 10°C, Weizen: 0°C). GDD_tag = max(0, (T_max + T_min) / 2 - T_base)
    - `required_conditions: Optional[dict]` (z.B. {"min_height_cm": 30})
    - `notification_before_days: int` (Warnung vor Auto-Transition)
    - `is_cycle_restart: bool` — Transition startet einen neuen saisonalen Zyklus
      (erlaubt Rückwärts-Transition bei Dauerkulturen, z.B. Seneszenz → Dormanz)
      <!-- Spec-Audit 2026-07-01 C1: Dieselbe zyklische Wiederholung wird auf der
           Nährstoff-/Visualisierungs-Ebene als Integer `cycle_restart_from_sequence`
           auf dem `NutrientPlan` modelliert (REQ-004, Feld
           `NutrientPlan.cycle_restart_from_sequence` = `sequence_order` der
           Wiederhol-Startphase). Beide Darstellungen MÜSSEN konsistent sein: die
           Phase, ab der `NutrientPlan.cycle_restart_from_sequence` zurückspringt,
           entspricht dem `next_phase`-Ziel der Transition mit `is_cycle_restart=true`.
           UI-NFR-016/020 rendern aus dem REQ-004-Feld. -->

- **`phase_histories`** - Historie für Analysen
  - Properties:
    - `entered_at: datetime`
    - `exited_at: Optional[datetime]`
    - `actual_duration_days: Optional[int]`
    - `transition_reason: str`
    - `performance_score: Optional[float]` (0-100, basierend auf Yield/Health)

- **`seasonal_cycles`** - Saisonaler Zyklus (nur Dauerkulturen)
  - Properties:
    - `plant_instance_key: str` — Referenz auf die Pflanze
    - `season_year: int` — Kalenderjahr (z.B. 2025)
    - `season_number: int` — Laufende Saison-Nummer (1-basiert, 1 = erste Saison der Pflanze)
    - `started_at: datetime` — Beginn (typisch: Austrieb nach Dormanz)
    - `ended_at: Optional[datetime]` — Ende (typisch: Eintritt in Dormanz)
    - `maturity_stage: Literal['juvenile', 'productive', 'declining']`
    - `chill_hours_accumulated: int` — Kältestunden der vorangegangenen Dormanz
    - `yield_kg: Optional[float]` — Gesamtertrag der Saison
    - `fruit_count: Optional[int]` — Anzahl Früchte (wenn zählbar)
    - `performance_notes: Optional[str]`
    <!-- Quelle: ADR-003 / W-014 -->
    - `sensor_aggregates: dict` (Default: `{}`) — Saisonale Sensor-Aggregate für Trendanalysen über Pflanzenleben hinweg. Format pro Sensor-Typ: `{"avg": float, "min": float, "max": float, "p10": float, "p90": float, "samples": int}` (für `temperature`, `humidity`, `vpd`, `soil_moisture`); `{"sum": float, "avg_per_day": float, "samples": int}` für `dli` (kumulativ statt Durchschnitt). Wird vom Celery-Task `compute_seasonal_aggregates_task` beim Saisonende berechnet und ist DSGVO-rechtlich unkritisch (keine Anwesenheits-Indikatoren, anonymisiert via `aggregate_computed_by`-Field bei User-Löschung, NFR-011 R-19a).
    - `aggregate_computed_at: Optional[datetime]` — Zeitpunkt der Aggregat-Berechnung. Bei `null` ist die Saison entweder noch aktiv oder das Aggregat wurde noch nicht berechnet.
    - `aggregate_computed_by: Optional[str]` — User-Key des auslösenden Anwenders (Audit). Bei User-Löschung wird auf `null` anonymisiert (NFR-011 R-19a).
    - `aggregate_source_retention_horizon: Optional[Literal['90d', '2y', '5y', '10y', '20y']]` — Bis wann die zugrundeliegenden Rohdaten/Stundenmittel/Tagesmittel zum Berechnungszeitpunkt verfügbar waren. Dokumentiert die Datenquelle für Audit-Zwecke.
    - `aggregate_config: Optional[dict]` — Tenant-spezifische Aggregat-Konfiguration (welche Sensor-Typen, welche Quartile etc.). `null` = Default-Set aus ADR-003.
    <!-- /Quelle: ADR-003 / W-014 -->

### Edge Collections:
```
consists_of:        lifecycle_configs  -> growth_phases         (Attribute: sequence)
next_phase:         growth_phases      -> growth_phases
governed_by:        growth_phases      -> phase_transition_rules
requires_profile:   growth_phases      -> requirement_profiles
uses_nutrients:     requirement_profiles -> nutrient_profiles
current_phase:      planting_runs|plant_instances  -> growth_phases       (Dual-Support: Run primaer, standalone Plant als Fallback; REQ-013 v2.0)
phase_history:      planting_runs|plant_instances  -> phase_histories     (Dual-Support)
was_phase:          phase_histories                -> growth_phases
has_season:         planting_runs|plant_instances  -> seasonal_cycles     (Dual-Support)
season_history:     seasonal_cycles    -> phase_histories    (Zuordnung Phase-History zu Saison)
```

### AQL-Beispiellogik:

**Naechste Phase mit Ressourcen-Profil laden:**

> **Dual-Support (REQ-013 v2.0):** `@entity_id` kann ein `planting_runs/{key}` oder ein `plant_instances/{key}` sein. Innerhalb eines aktiven Runs wird die Phase auf dem Run verwaltet; standalone PlantInstances verwalten ihre eigene Phase.

```aql
LET entity = DOCUMENT(@entity_id)   // planting_runs/... oder plant_instances/...

FOR current_phase IN 1..1 OUTBOUND entity GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['current_phase'] }
    FOR next IN 1..1 OUTBOUND current_phase GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['next_phase'] }
        FOR req IN 1..1 OUTBOUND next GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['requires_profile'] }
            FOR nutr IN 1..1 OUTBOUND req GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['uses_nutrients'] }
                LET rules = (
                    FOR rule IN 1..1 OUTBOUND next GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['governed_by'] }
                        RETURN rule
                )
                RETURN { next, req, nutr, rule: FIRST(rules) }
```

**Auto-Transition Kandidaten finden (zeitbasiert):**

> **Dual-Support (REQ-013 v2.0):** Primaer werden aktive PlantingRuns iteriert. Zusaetzlich standalone PlantInstances (nicht in aktivem Run).

```aql
// 1. Aktive Runs pruefen
FOR run IN planting_runs
    FILTER run.status IN ['active', 'harvesting']
    FOR phase IN 1..1 OUTBOUND run GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['current_phase'] }
        FOR rule IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['governed_by'] }
            FILTER rule.trigger_type == 'time_based'
            FOR history IN 1..1 OUTBOUND run GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['phase_history'] }
                FILTER history.exited_at == null
                FOR hist_phase IN 1..1 OUTBOUND history GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['was_phase'] }
                    FILTER hist_phase._id == phase._id
                    LET actual_duration = DATE_DIFF(history.entered_at, DATE_NOW(), 'days')
                    FILTER actual_duration >= rule.auto_transition_after_days
                    RETURN {
                        entity_type: 'run',
                        entity_key: run._key,
                        current_phase: phase.name,
                        planned_duration: rule.auto_transition_after_days,
                        actual_duration: actual_duration
                    }

// 2. Standalone Plants pruefen (nicht in aktivem Run)
// Analog mit FOR plant IN plant_instances, gefiltert auf Plants ohne aktive run_contains-Edge
```

**VPD-Optimierung fuer aktuelle Phase:**

> **Dual-Support:** `@entity_id` = Run oder standalone Plant. Location wird bei Runs ueber `run_at_location` aufgeloest, bei standalone Plants ueber `placed_in` → Slot → Location.

```aql
LET entity = DOCUMENT(@entity_id)   // planting_runs/... oder plant_instances/...
LET one_hour_ago = DATE_SUBTRACT(DATE_NOW(), 1, 'hours')

FOR phase IN 1..1 OUTBOUND entity GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['current_phase'] }
    FOR req IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['requires_profile'] }
        // Location-Aufloesung: Run → run_at_location → Location, oder Plant → placed_in → Slot → Location
        FOR location IN 1..2 OUTBOUND entity GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['run_at_location', 'placed_in', 'has_slot'] }
            FOR location IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['has_slot'] }
                FOR sensor IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['has_sensor'] }
                    FOR obs IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['recorded'] }
                        FILTER obs.timestamp > one_hour_ago
                        LET temp = obs.temperature_c
                        LET rh = obs.humidity_percent
                        // Leaf-VPD: Blatttemperatur typisch 2°C unter Lufttemperatur
                        LET leaf_temp = temp - 2.0
                        LET svp_leaf = 610.7 * POW(10, (7.5 * leaf_temp / (237.3 + leaf_temp)))
                        LET avp = 610.7 * POW(10, (7.5 * temp / (237.3 + temp))) * (rh / 100)
                        LET current_vpd = (svp_leaf - avp) / 1000
                        RETURN {
                            target_vpd: req.vpd_target_kpa,
                            current_vpd_kpa: current_vpd,
                            vpd_deviation: ABS(req.vpd_target_kpa - current_vpd)
                        }
```

**Saison-Vergleich für Dauerkultur:**
```aql
// Vergleicht Ertrag und Phasen-Dauern über mehrere Saisons einer Pflanze
FOR season IN seasonal_cycles
    FILTER season.entity_key == @entity_key   // planting_run_key oder plant_instance_key (Dual-Support)
    SORT season.season_number ASC
    LET phase_durations = (
        FOR history IN phase_histories
            FOR edge IN season_history
                FILTER edge._from == season._id AND edge._to == history._id
                RETURN {
                    phase: history.phase_name,
                    duration_days: history.actual_duration_days
                }
    )
    RETURN {
        season: season.season_number,
        year: season.season_year,
        maturity: season.maturity_stage,
        yield_kg: season.yield_kg,
        chill_hours: season.chill_hours_accumulated,
        phases: phase_durations
    }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

<!-- Quelle: Widerspruchsanalyse W-003 -->
**1a. Run-Membership-Guard (W-003):**

REQ-013 v2.0 etabliert den `PlantingRun` als primäre Verwaltungseinheit für die Phase. Solange eine `PlantInstance` Mitglied eines aktiven Runs ist (`run_contains`-Edge mit `detached_at = null`, Run-Status `active`), wird ihre Phase **ausschließlich** über den Run gesteuert. Direkte Phasenwechsel auf der einzelnen PlantInstance MÜSSEN technisch abgelehnt werden.

**Wo der Guard sitzt:** Engine-only — die `PhaseTransitionEngine` ist die einzige Stelle, an der ein Phasenwechsel ausgeführt wird; jeder Code-Pfad (Direct-API, Batch-Endpoint, Celery-Task, interne Service-Aufrufe) läuft durch sie hindurch.

**Verhalten bei Verstoß:**

```json
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "error_code": "phase.run_owned",
  "message": "Phase wird vom PlantingRun verwaltet.",
  "run_key": "tomaten-hochbeet-a-2025",
  "plant_key": "HOCHBEETA_TOM_05",
  "remediation": "PUT /api/v1/t/{tenant_slug}/planting-runs/{run_key}/phase"
}
```

Der Frontend-Code kann `error_code='phase.run_owned'` abfangen, dem Anwender die Run-Sicht öffnen und den Phasenwechsel dort anstoßen.

**Lookup-Query (AQL):**

```aql
LET active_run = FIRST(
  FOR rc IN run_contains
    FILTER rc._to == @plant_id
    FILTER rc.detached_at == null
    LET run = DOCUMENT(rc._from)
    FILTER run.status == "active"
    RETURN run
)
RETURN active_run
```

Das Query liefert maximal ein Run-Dokument zurück (Invariante REQ-013 §1: „PlantInstance gehört zu maximal einem aktiven PlantingRun"). Liefert es `null`, ist die Pflanze standalone — der Phasenwechsel verläuft regulär.

**Wann der Guard NICHT greift:**

| Zustand | Phasenwechsel auf PlantInstance |
|---------|--------------------------------|
| Plant hat keine `run_contains`-Edge | erlaubt (standalone) |
| Plant hat `run_contains`-Edge, aber `detached_at != null` | erlaubt (detached → standalone) |
| Plant hat aktive Edge, Run hat aber `status != 'active'` (`completed`, `cancelled`, `harvesting`) | erlaubt (Run-Lifecycle abgeschlossen) |
| Plant hat aktive Edge UND Run ist aktiv | **abgelehnt mit HTTP 409** |
| Phasenwechsel zielt auf den Run selbst (`entity_type='run'`) | erlaubt (Run-Phase ist immer erlaubt) |

**Batch-Phasenwechsel (All-or-Nothing):**

Der Batch-Endpoint (`POST /plant-instances/batch-transition`, REQ-013) MUSS denselben Guard für jede einzelne Plant in der Liste anwenden. Bei mindestens einem Konflikt wird der gesamte Batch mit HTTP 409 abgelehnt — keine Plant wird transitioniert. Response enthält die Liste aller konflikten Plants:

```json
HTTP/1.1 409 Conflict
{
  "error_code": "phase.batch_run_owned",
  "message": "Mindestens eine Pflanze ist Mitglied eines aktiven PlantingRun. Der gesamte Batch wurde abgelehnt.",
  "conflicts": [
    {"plant_key": "HOCHBEETA_TOM_05", "run_key": "tomaten-hochbeet-a-2025"},
    {"plant_key": "HOCHBEETA_TOM_07", "run_key": "tomaten-hochbeet-a-2025"}
  ]
}
```

Begründung: Phasenwechsel sind sicherheitsrelevant (Karenz-Gate REQ-010, Erntefreigabe REQ-007). Stilles Überspringen einzelner Plants im Batch wäre fehleranfällig — der Anwender hat 20 Pflanzen gemeint und soll explizit erfahren, welche nicht transitioniert wurden.
<!-- /Quelle: Widerspruchsanalyse W-003 -->

**1. State-Machine für Phasenübergänge:**
```python
from datetime import datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TransitionTrigger(str, Enum):
    TIME_BASED = "time_based"
    MANUAL = "manual"
    EVENT_BASED = "event_based"
    CONDITIONAL = "conditional"
    GDD_BASED = "gdd_based"  # Growing Degree Days — biologisch akkurater als Kalendertage

class PhaseTransitionEngine(BaseModel):
    """Steuert Uebergaenge zwischen Wachstumsphasen.

    Dual-Support (REQ-013 v2.0): entity_id kann ein planting_runs-Key oder
    ein plant_instances-Key sein. Bei Runs wird die Phase fuer alle Pflanzen
    im Run gesetzt; bei standalone Plants nur fuer die einzelne Pflanze.

    Run-Membership-Guard (W-003): Vor jedem Transition-Aufruf MUSS
    assert_transition_allowed() aufgerufen werden, das Run-gebundene
    PlantInstances mit RunMembershipConflictError abweist.
    """

    entity_id: str         # planting_runs/{key} oder plant_instances/{key}
    entity_type: str       # 'run' oder 'plant'
    current_phase: str
    phase_entered_at: datetime
    auto_transition_days: Optional[int] = None
    gdd_threshold: Optional[float] = None
    gdd_base_temp_c: Optional[float] = None
    accumulated_gdd: float = 0.0
    transition_trigger: TransitionTrigger

    # <!-- Quelle: Widerspruchsanalyse W-003 -->
    def assert_transition_allowed(self, plant_repo) -> None:
        """W-003 Guard: Verbietet direkte Phasenwechsel auf Run-Mitgliedern.

        Wird VOR jedem Phasenwechsel aufgerufen — sowohl bei Auto-Transition
        (Celery-Task) als auch bei manuellem API-Call (PUT /phase) und im
        Batch-Endpoint.

        Raises:
            RunMembershipConflictError: Wenn entity_type='plant' und die
                Plant Mitglied eines aktiven Runs ist (run_contains mit
                detached_at=null, run.status='active').
        """
        if self.entity_type != "plant":
            return  # Run-Phase ist immer erlaubt

        active_run = plant_repo.find_active_run_for_plant(self.entity_id)
        if active_run is not None:
            raise RunMembershipConflictError(
                error_code="phase.run_owned",
                message="Phase wird vom PlantingRun verwaltet.",
                run_key=active_run.key,
                plant_key=self.entity_id,
                remediation=(
                    f"PUT /api/v1/t/{{tenant_slug}}/planting-runs/"
                    f"{active_run.key}/phase"
                ),
            )


class RunMembershipConflictError(Exception):
    """W-003: Direkter Phasenwechsel auf Run-gebundener PlantInstance.

    Wird vom API-Layer in HTTP 409 Conflict mit strukturiertem Body
    übersetzt. Bei Batch-Operationen werden alle RunMembershipConflictErrors
    eines Batches gesammelt und in einer einzigen 409-Response als
    'phase.batch_run_owned' zurückgegeben (All-or-Nothing).
    """

    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        run_key: str,
        plant_key: str,
        remediation: str,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.run_key = run_key
        self.plant_key = plant_key
        self.remediation = remediation
        super().__init__(message)
    # <!-- /Quelle: Widerspruchsanalyse W-003 -->

    def check_transition_due(self) -> tuple[bool, str, Optional[str]]:
        """
        Returns: (should_transition, reason, next_phase_name)
        """
        days_in_phase = (datetime.now() - self.phase_entered_at).days

        if self.transition_trigger == TransitionTrigger.TIME_BASED:
            if self.auto_transition_days is None:
                return False, "Keine Auto-Transition konfiguriert", None

            if days_in_phase >= self.auto_transition_days:
                return True, f"Geplante Dauer erreicht ({self.auto_transition_days} Tage)", "next_phase"

            # Warnung 3 Tage vorher
            days_remaining = self.auto_transition_days - days_in_phase
            if days_remaining <= 3 and days_remaining > 0:
                return False, f"WARNUNG: Automatische Transition in {days_remaining} Tagen", None

        if self.transition_trigger == TransitionTrigger.GDD_BASED:
            if self.gdd_threshold is None:
                return False, "Kein GDD-Schwellenwert konfiguriert", None

            if self.accumulated_gdd >= self.gdd_threshold:
                return True, (
                    f"GDD-Schwellenwert erreicht ({self.accumulated_gdd:.0f} "
                    f"von {self.gdd_threshold:.0f} GDD)"
                ), "next_phase"

            gdd_remaining = self.gdd_threshold - self.accumulated_gdd
            # Grobe Warnung bei ~20% verbleibendem GDD
            if gdd_remaining <= self.gdd_threshold * 0.2:
                return False, (
                    f"GDD-Transition nähert sich: {self.accumulated_gdd:.0f}"
                    f"/{self.gdd_threshold:.0f} GDD"
                ), None

        if self.transition_trigger == TransitionTrigger.MANUAL:
            return False, "Manuelle Steuerung aktiv", None

        return False, "Transition-Bedingungen nicht erfüllt", None

    @staticmethod
    def calculate_daily_gdd(
        temp_max_c: float,
        temp_min_c: float,
        base_temp_c: float = 10.0
    ) -> float:
        """
        Berechnet Growing Degree Days für einen Tag.
        GDD = max(0, (T_max + T_min) / 2 - T_base)

        Typische Basistemperaturen:
        - Tomate, Paprika, Mais: 10°C
        - Weizen, Gerste: 0°C
        - Cannabis: 10°C (geschätzt)
        """
        return max(0.0, (temp_max_c + temp_min_c) / 2 - base_temp_c)

    def execute_transition(
        self,
        next_phase_name: str,
        arango_db,
        override_reason: Optional[str] = None
    ) -> dict:
        """
        Führt Phasenübergang durch und aktualisiert Graph
        """
        transition_timestamp = datetime.now()
        actual_duration = (transition_timestamp - self.phase_entered_at).days

        # 1. Schließe aktuelle Phase-History
        arango_db.aql.execute("""
            FOR plant IN plant_instances
                FILTER plant._key == @plant_id
                FOR history IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['phase_history'] }
                    FILTER history.exited_at == null
                    UPDATE history WITH {
                        exited_at: @exit_time,
                        actual_duration_days: @duration,
                        transition_reason: @reason
                    } IN phase_histories
        """,
        bind_vars={
            'plant_id': self.plant_id,
            'exit_time': transition_timestamp.isoformat(),
            'duration': actual_duration,
            'reason': override_reason or "Automatische Transition"
        })

        # 2. Aktualisiere CURRENT_PHASE (alte Edge entfernen, neue anlegen)
        arango_db.aql.execute("""
            FOR plant IN plant_instances
                FILTER plant._key == @plant_id
                FOR phase, edge IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['current_phase'] }
                    REMOVE edge IN current_phase
        """, bind_vars={'plant_id': self.plant_id})

        arango_db.aql.execute("""
            LET plant = DOCUMENT(CONCAT('plant_instances/', @plant_id))
            FOR next IN growth_phases
                FILTER next.name == @next_phase
                INSERT { _from: plant._id, _to: next._id } INTO current_phase
        """, bind_vars={'plant_id': self.plant_id, 'next_phase': next_phase_name})

        # 3. Erstelle neue Phase-History
        arango_db.aql.execute("""
            LET plant = DOCUMENT(CONCAT('plant_instances/', @plant_id))
            FOR phase IN growth_phases
                FILTER phase.name == @phase_name
                LET history = FIRST(
                    INSERT {
                        entered_at: @enter_time,
                        exited_at: null,
                        transition_reason: 'New phase started'
                    } INTO phase_histories
                    RETURN NEW
                )
                INSERT { _from: plant._id, _to: history._id } INTO phase_history
                INSERT { _from: history._id, _to: phase._id } INTO was_phase
        """,
        bind_vars={
            'plant_id': self.plant_id,
            'phase_name': next_phase_name,
            'enter_time': transition_timestamp.isoformat()
        })

        # 4. Hole neue Ressourcen-Profile
        cursor = arango_db.aql.execute("""
            FOR phase IN growth_phases
                FILTER phase.name == @phase_name
                FOR req IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['requires_profile'] }
                    FOR nutr IN 1..1 OUTBOUND req GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['uses_nutrients'] }
                        RETURN { req, nutr }
        """, bind_vars={'phase_name': next_phase_name})
        new_profile = next(cursor, None)

        return {
            'transition_completed': True,
            'previous_phase': self.current_phase,
            'new_phase': next_phase_name,
            'actual_duration_days': actual_duration,
            'new_requirements': new_profile['req'] if new_profile else None,
            'new_nutrients': new_profile['nutr'] if new_profile else None
        }
```

<!-- Quelle: Cannabis Indoor Grower Review G-009 -->
**1a. Autoflower-Transition-Logik:**

Autoflower-Cultivare (Cannabis-ruderalis-Hybriden) unterscheiden sich fundamental von
photoperiodischen Sorten in der Phasensteuerung. Das System erkennt den Cultivar-Level
`photoperiod_type='autoflower'` und passt die Transition-Logik entsprechend an:

```python
class AutoflowerTransitionPreset(BaseModel):
    """
    Vorgefertigte Phasendauern für Autoflower-Cultivare.

    Autoflower blühen altersbasiert (nicht lichtabhängig). Der Übergang
    Vegi → Blüte erfolgt automatisch nach `days_to_flower` Tagen ab Keimung.
    Es gibt keinen manuellen Blüte-Trigger und keinen Photoperioden-Wechsel.

    Typische Gesamtzyklen: 60–90 Tage (vs. 120–180 Tage photoperiodisch).
    """

    days_to_flower: int = Field(ge=14, le=45, description="Tage ab Keimung bis Auto-Blüte")
    total_cycle_days: int = Field(ge=45, le=120, description="Gesamtdauer Keimung→Ernte")
    photoperiod_hours: float = Field(default=20.0, ge=18.0, le=24.0,
        description="Durchgehende Photoperiode (Standard: 20/4, alternativ 18/6)")

    # Standard-Preset für typische Autoflower
    PRESET_FAST: ClassVar[dict] = {
        'germination_days': 3,
        'seedling_days': 7,
        'vegetative_days': 14,
        'flowering_days': 42,   # 6 Wochen
        'total_days': 66,
    }
    PRESET_STANDARD: ClassVar[dict] = {
        'germination_days': 5,
        'seedling_days': 10,
        'vegetative_days': 21,
        'flowering_days': 49,   # 7 Wochen
        'total_days': 85,
    }
    PRESET_LONG: ClassVar[dict] = {
        'germination_days': 5,
        'seedling_days': 10,
        'vegetative_days': 28,
        'flowering_days': 56,   # 8 Wochen
        'total_days': 99,
    }

    def get_phase_durations(self) -> dict[str, int]:
        """Berechnet Phasendauern aus Gesamtzyklus und days_to_flower"""
        flowering_days = self.total_cycle_days - self.days_to_flower
        return {
            'germination': 5,
            'seedling': max(7, self.days_to_flower - 18),
            'vegetative': self.days_to_flower - 12,  # Abzügl. Keimung+Sämling
            'flowering': flowering_days,
        }

    def get_transition_rules(self) -> list[dict]:
        """
        Alle Transitionen sind TIME_BASED — kein manueller Blüte-Trigger.

        Unterschiede zu photoperiodischen Sorten:
        1. Vegi→Blüte ist TIME_BASED (nicht MANUAL/EVENT_BASED)
        2. Photoperiode bleibt konstant (kein PhotoperiodManager-Aufruf)
        3. Kürzere Phasendauern insgesamt
        """
        durations = self.get_phase_durations()
        return [
            {
                'from_phase': 'germination',
                'to_phase': 'seedling',
                'trigger_type': 'time_based',
                'auto_transition_after_days': durations['germination'],
            },
            {
                'from_phase': 'seedling',
                'to_phase': 'vegetative',
                'trigger_type': 'time_based',
                'auto_transition_after_days': durations['seedling'],
            },
            {
                'from_phase': 'vegetative',
                'to_phase': 'flowering',
                'trigger_type': 'time_based',  # KEIN manueller Trigger!
                'auto_transition_after_days': durations['vegetative'],
                'notification_before_days': 2,
                '_note': 'Autoflower: Blüte wird NICHT durch Lichtwechsel ausgelöst',
            },
            {
                'from_phase': 'flowering',
                'to_phase': 'ripening',
                'trigger_type': 'time_based',
                'auto_transition_after_days': durations['flowering'],
            },
        ]


class AutoflowerTrainingGuard:
    """
    Warnung bei High-Stress-Training (HST) für Autoflower-Cultivare.

    Autoflower haben eine fest begrenzte vegetative Phase (14–28 Tage).
    HST-Techniken (Topping, FIM, Supercropping) benötigen 7–14 Tage
    Erholungszeit, die bei Autoflowern nicht zur Verfügung steht.

    - LST (Low-Stress-Training) bleibt ohne Einschränkung erlaubt.
    - HST wird nicht blockiert, aber mit deutlicher Warnung versehen.

    Cross-Ref: REQ-006 (Aufgabenplanung) — HSTValidator
    """

    HST_METHODS = {'topping', 'fim', 'supercropping', 'mainlining', 'manifolding'}
    LST_METHODS = {'lst', 'scrog', 'sog', 'bending', 'defoliation'}

    @staticmethod
    def check_training_allowed(
        training_method: str,
        cultivar_photoperiod_type: Optional[str],
        current_phase: str,
        days_in_veg: int,
    ) -> tuple[bool, Optional[str]]:
        """
        Returns: (is_allowed, warning_message)
        - HST bei Autoflower: allowed=True, aber Warnung
        - HST bei Autoflower in Blüte: allowed=False (wie bei allen Sorten)
        """
        if training_method.lower() in AutoflowerTrainingGuard.LST_METHODS:
            return True, None

        if current_phase != 'vegetative':
            return False, f"HST-Methode '{training_method}' nur in vegetativer Phase erlaubt"

        if cultivar_photoperiod_type == 'autoflower':
            return True, (
                f"WARNUNG: HST-Methode '{training_method}' bei Autoflower nicht empfohlen. "
                f"Autoflower haben eine begrenzte vegetative Phase ({days_in_veg} Tage bisher). "
                f"Erholungszeit nach {training_method} beträgt 7–14 Tage, was bei Autoflowern "
                f"den Ertrag reduzieren kann. LST (Low-Stress-Training) wird stattdessen empfohlen."
            )

        return True, None
```
<!-- /Quelle: G-009 -->

**2. VPD-Calculator:**
```python
import math
from typing import Literal

class VPDCalculator:
    """Berechnet Vapor Pressure Deficit für Transpirationssteuerung"""

    @staticmethod
    def calculate_vpd(
        temperature_c: float,
        relative_humidity_percent: float,
        leaf_temperature_offset_c: float = -2.0,
        ppfd: Optional[int] = None
    ) -> float:
        """
        Berechnet Leaf-to-Air VPD in kPa

        Args:
            temperature_c: Lufttemperatur
            relative_humidity_percent: Relative Luftfeuchte
            leaf_temperature_offset_c: Blatt-Luft-Differenz (Default: -2°C)
            ppfd: Aktuelle Lichtintensität (µmol/m²/s). Wenn angegeben,
                  wird der Blatttemperatur-Offset dynamisch angepasst:
                  - <200 PPFD: -1°C (wenig Strahlungsabsorption)
                  - 200-600 PPFD: -2°C (Standard)
                  - >800 PPFD: +1°C (starke Strahlungserwärmung)
        Returns:
            VPD in kPa (Leaf-to-Air, pflanzenwissenschaftlich relevant)
        """
        # Dynamischer Blatttemperatur-Offset bei bekannter PPFD
        if ppfd is not None:
            if ppfd < 200:
                leaf_temperature_offset_c = -1.0
            elif ppfd > 800:
                leaf_temperature_offset_c = 1.0
            # 200-800: Default -2.0 beibehalten
        # Sättigungsdampfdruck bei Lufttemperatur (in Pa)
        svp_air = 610.7 * (10 ** ((7.5 * temperature_c) / (237.3 + temperature_c)))

        # Tatsächlicher Dampfdruck
        avp = svp_air * (relative_humidity_percent / 100)

        # Sättigungsdampfdruck bei Blatttemperatur
        leaf_temp = temperature_c + leaf_temperature_offset_c
        svp_leaf = 610.7 * (10 ** ((7.5 * leaf_temp) / (237.3 + leaf_temp)))

        # VPD = Differenz in kPa
        vpd_kpa = (svp_leaf - avp) / 1000

        return round(vpd_kpa, 2)

    @staticmethod
    def get_vpd_recommendation(
        phase: str,
        current_vpd_kpa: float,
        species_type: str = 'default'
    ) -> tuple[str, str]:
        """
        Gibt Empfehlungen basierend auf Phase, Spezies-Typ und aktuellem VPD.
        species_type: 'default' (Cannabis/Nachtschatten), 'leafy', 'fruiting'
        Returns: (status, recommendation)
        """
        # Ziel-VPD nach Phase und Spezies-Typ
        # Cannabis/Nachtschatten (Default), Leafy Greens, Tropische Pflanzen
        target_ranges_by_type = {
            'default': {
                'seedling': (0.4, 0.8),
                'vegetative': (0.8, 1.2),
                'flowering': (1.0, 1.5),
                'late_flowering': (1.2, 1.6),
            },
            'leafy': {
                'seedling': (0.3, 0.6),
                'vegetative': (0.5, 1.0),
                'flowering': (0.5, 1.0),
                'late_flowering': (0.5, 1.0),
            },
            'fruiting': {
                'seedling': (0.4, 0.8),
                'vegetative': (0.8, 1.2),
                'flowering': (0.8, 1.3),
                'late_flowering': (1.0, 1.4),
            },
        }
        ranges = target_ranges_by_type.get(species_type, target_ranges_by_type['default'])
        target_min, target_max = ranges.get(phase, (0.8, 1.2))

        if current_vpd_kpa < target_min:
            return "ZU NIEDRIG", f"Erhöhe Temperatur oder senke Luftfeuchte. Ziel: {target_min}-{target_max} kPa"
        elif current_vpd_kpa > target_max:
            return "ZU HOCH", f"Senke Temperatur oder erhöhe Luftfeuchte. Ziel: {target_min}-{target_max} kPa"
        else:
            return "OPTIMAL", f"VPD im Zielbereich ({target_min}-{target_max} kPa)"
```

**3. Ressourcen-Profil-Generator:**
```python
from pydantic import BaseModel, Field

class ResourceProfileGenerator(BaseModel):
    """Generiert automatische Ressourcen-Profile wenn nicht manuell definiert"""

    phase_name: str
    species_type: Literal['leafy', 'fruiting', 'flowering', 'root']
    photoperiod_response: Literal['short_day', 'long_day', 'day_neutral'] = 'short_day'
    substrate_type: Literal['hydro', 'coco', 'soil', 'living_soil'] = 'coco'
    # Quelle: Cannabis Indoor Grower Review G-009
    cultivar_photoperiod_type: Optional[Literal['photoperiodic', 'autoflower', 'day_neutral']] = None
    # /Quelle: G-009

    def generate_light_profile(self) -> dict:
        """
        Generiert Lichtprofil basierend auf Phase, Typ und Photoperiod-Response.

        Photoperiod-Response bestimmt die Blüte-Tageslänge:
        - short_day: Blüte bei <12h (Cannabis, Chrysanthemen, Poinsettia)
        - long_day: Blüte bei >14h (Salat, Spinat, Radieschen)
        - day_neutral: Blüte unabhängig von Tageslänge (viele Tomaten, Erdbeeren)

        Bei Autoflower-Cultivaren (G-009) wird die Photoperiode durchgehend auf
        20h oder 18h gehalten — kein Wechsel auf 12/12 in der Blütephase.

        Spektrum enthält Grünlicht-Anteil: Grün (500-600nm) penetriert 50% tiefer
        in den Bestand und trägt bei dichten Pflanzungen 20-30% zur Photosynthese bei.
        """

        # PPFD-Basiswerte nach species_type (nicht nur Skalierungsfaktor)
        ppfd_by_type = {
            'leafy':     {'seedling':  80, 'vegetative': 250, 'flowering': 300, 'ripening': 200},
            'fruiting':  {'seedling': 200, 'vegetative': 500, 'flowering': 700, 'ripening': 500},
            'flowering': {'seedling': 200, 'vegetative': 400, 'flowering': 600, 'ripening': 400},
            'root':      {'seedling': 100, 'vegetative': 300, 'flowering': 400, 'ripening': 250},
        }

        ppfd = ppfd_by_type.get(self.species_type, ppfd_by_type['flowering']).get(
            self.phase_name, 400
        )

        # Quelle: Cannabis Indoor Grower Review G-009
        # Autoflower-Cultivare: Durchgehend 20/4 oder 18/6, kein Photoperioden-Wechsel
        if self.cultivar_photoperiod_type == 'autoflower':
            photoperiod = 20  # 20/4 Standard für Autoflower (alternativ 18/6)
        # /Quelle: G-009
        # Photoperiode nach Phase und Photoperiod-Response
        elif self.phase_name in ('flowering', 'ripening'):
            photoperiod = {
                'short_day': 12,     # Cannabis, Chrysanthemen
                'long_day': 16,      # Salat, Spinat — Blüte unter Langtag
                'day_neutral': 18,   # Keine Änderung nötig (Tomaten, Erdbeeren)
            }[self.photoperiod_response]
        else:
            photoperiod = 18  # Vegi/Seedling: immer Langtag

        # Spektrum mit Grünlicht-Anteil (Vollspektrum-Ansatz)
        spectra = {
            'seedling':    {'blue': 0.35, 'green': 0.20, 'red': 0.40, 'far_red': 0.05},
            'vegetative':  {'blue': 0.25, 'green': 0.20, 'red': 0.45, 'far_red': 0.10},
            'flowering':   {'blue': 0.15, 'green': 0.15, 'red': 0.50, 'far_red': 0.20},
            'ripening':    {'blue': 0.10, 'green': 0.15, 'red': 0.55, 'far_red': 0.20},
        }
        spectrum = spectra.get(self.phase_name, spectra['vegetative'])

        # DLI berechnen (Daily Light Integral)
        dli = round(ppfd * photoperiod * 3600 / 1_000_000, 1)

        return {
            'ppfd': ppfd,
            'photoperiod': photoperiod,
            'spectrum': spectrum,
            'dli_mol_per_m2_day': dli,
        }

    def generate_nutrient_profile(self) -> dict:
        """
        Generiert NPK-Verhältnis nach Phase und species_type.
        pH-Zielwerte sind substrat-abhängig.
        """

        # NPK nach species_type: Fruchtpflanzen brauchen auch in Reife N für
        # Blatterhalt und Zuckerproduktion; Blütenpflanzen (Cannabis) können auf 0 N gehen
        phase_nutrients_by_type = {
            'flowering': {  # Cannabis-like: aggressiver N-Abbau in Reife
                'seedling':   {'npk': (1, 1, 1), 'ec': 0.8},
                'vegetative': {'npk': (3, 1, 2), 'ec': 1.4},
                'flowering':  {'npk': (1, 3, 3), 'ec': 1.8},
                'ripening':   {'npk': (0, 2, 4), 'ec': 1.2},
                'flushing':   {'npk': (0, 0, 0), 'ec': 0.0},
            },
            'fruiting': {  # Tomate/Paprika: N weiterhin nötig für Fruchtentwicklung
                'seedling':   {'npk': (1, 1, 1), 'ec': 0.8},
                'vegetative': {'npk': (3, 1, 2), 'ec': 1.6},
                'flowering':  {'npk': (2, 3, 3), 'ec': 2.0},
                'ripening':   {'npk': (1, 2, 4), 'ec': 1.6},
                'flushing':   {'npk': (0, 0, 0), 'ec': 0.0},
            },
            'leafy': {  # Salat/Kräuter: gleichmäßig N-betont
                'seedling':   {'npk': (1, 1, 1), 'ec': 0.6},
                'vegetative': {'npk': (4, 1, 3), 'ec': 1.2},
                'flowering':  {'npk': (3, 1, 2), 'ec': 1.0},
                'ripening':   {'npk': (2, 1, 2), 'ec': 0.8},
                'flushing':   {'npk': (0, 0, 0), 'ec': 0.0},
            },
            'root': {  # Karotten/Radieschen: K-betont für Wurzelentwicklung
                'seedling':   {'npk': (1, 1, 1), 'ec': 0.6},
                'vegetative': {'npk': (2, 1, 3), 'ec': 1.2},
                'flowering':  {'npk': (1, 2, 4), 'ec': 1.4},
                'ripening':   {'npk': (1, 1, 4), 'ec': 1.0},
                'flushing':   {'npk': (0, 0, 0), 'ec': 0.0},
            },
        }

        nutrients = phase_nutrients_by_type.get(
            self.species_type, phase_nutrients_by_type['flowering']
        ).get(self.phase_name, {'npk': (3, 1, 2), 'ec': 1.4})

        # pH-Zielwerte substrat-abhängig
        ph_by_substrate = {
            'hydro':       {'seedling': 5.8, 'vegetative': 5.8, 'flowering': 5.9, 'ripening': 6.0, 'flushing': 5.8},
            'coco':        {'seedling': 6.0, 'vegetative': 5.8, 'flowering': 6.0, 'ripening': 6.2, 'flushing': 6.0},
            'soil':        {'seedling': 6.3, 'vegetative': 6.2, 'flowering': 6.3, 'ripening': 6.5, 'flushing': 6.5},
            'living_soil': {'seedling': 6.5, 'vegetative': 6.4, 'flowering': 6.5, 'ripening': 6.8, 'flushing': 6.5},
        }

        ph = ph_by_substrate.get(
            self.substrate_type, ph_by_substrate['coco']
        ).get(self.phase_name, 6.0)

        return {**nutrients, 'ph': ph}
```

**4. Photoperioden-Manager:**
```python
from datetime import time

class PhotoperiodManager(BaseModel):
    """Verwaltet Licht-Zyklen und automatische Umstellung"""

    current_photoperiod_hours: float
    target_photoperiod_hours: float
    transition_days: int = Field(default=7, description="Schrittweise Umstellung")

    def calculate_transition_schedule(self) -> list[dict]:
        """
        Erstellt graduellen Übergang zwischen Photoperioden
        (Vermeidet Stress durch abrupte Änderung)
        """
        hour_diff = self.target_photoperiod_hours - self.current_photoperiod_hours
        daily_increment = hour_diff / self.transition_days

        schedule = []
        for day in range(self.transition_days + 1):
            hours = self.current_photoperiod_hours + (daily_increment * day)
            minutes = int((hours % 1) * 60)
            full_hours = int(hours)

            schedule.append({
                'day': day,
                'photoperiod_hours': round(hours, 2),
                'lights_on_duration': f"{full_hours:02d}:{minutes:02d}",
                'change_from_previous': round(daily_increment, 2) if day > 0 else 0
            })

        return schedule

    @staticmethod
    def calculate_light_times(
        photoperiod_hours: float,
        preferred_lights_on: time = time(6, 0)
    ) -> dict:
        """Berechnet Licht-EIN und AUS Zeiten.

        `preferred_lights_on` wird aus dem Location-Model übernommen
        (Feld `lights_on`), falls gesetzt. Bei natürlichem Licht und
        `use_dynamic_sunrise=True` wird die berechnete Sonnenaufgangszeit
        aus dem SunCalculator (REQ-002) verwendet.
        Default bleibt 06:00 für Abwärtskompatibilität.
        """

        hours_on = int(photoperiod_hours)
        minutes_on = int((photoperiod_hours % 1) * 60)

        lights_on_dt = datetime.combine(datetime.today(), preferred_lights_on)
        lights_off_dt = lights_on_dt + timedelta(hours=hours_on, minutes=minutes_on)

        return {
            'lights_on': lights_on_dt.time(),
            'lights_off': lights_off_dt.time(),
            'duration': f"{hours_on}h {minutes_on}min"
        }
```

**5. Dauerkulturen-Zyklus-Engine:**
```python
class MaturityStage(str, Enum):
    JUVENILE = "juvenile"         # Kein Ertrag (z.B. Apfelbaum < 3 Jahre)
    PRODUCTIVE = "productive"     # Voller Ertrag
    DECLINING = "declining"       # Ertragsrückgang (Alter)

# Spec-Audit 2026-07-02 D1: verallgemeinert von PerennialCycleEngine auf zyklische UND
# begrenzt-zyklische (biennale) Lebenszyklen. `cycle_type` nicht mehr auf 'perennial' fixiert.
class CyclicLifecycleEngine(BaseModel):
    """Verwaltet wiederkehrende Phasenzyklen für Dauerkulturen UND den begrenzten
    Zwei-Jahres-Zyklus biennaler Arten (Jahr 1 vegetativ → Dormanz → Jahr 2
    Neuaustrieb → Schossen → Blüte → Samenreife → terminal). Bienniale sind monokarp:
    nach der Blüte/Samenreife im zweiten Jahr endet der Lebenszyklus (KEIN is_cycle_restart)."""

    plant_id: str
    cycle_type: Literal['perennial', 'biennial'] = 'perennial'
    current_season_number: int = Field(ge=1)
    planted_year: int
    first_bearing_year: Optional[int] = None  # Ab wann Ertrag erwartet
    expected_productive_years: Optional[int] = None
    # Spec-Audit 2026-07-02 D1: begrenzt-zyklische Semantik (Bienniale).
    max_seasons: Optional[int] = None       # None = unbegrenzt (perennial); 2 = biennial (terminal nach Saison 2)
    terminal_after_flowering: bool = False  # True bei biennial/monokarp: Blüte→Samen→terminal statt Neustart

    def get_maturity_stage(self, current_year: int) -> MaturityStage:
        """Bestimmt Reifegrad basierend auf Pflanzenalter"""
        plant_age = current_year - self.planted_year

        if self.first_bearing_year and plant_age < self.first_bearing_year:
            return MaturityStage.JUVENILE

        if self.expected_productive_years:
            productive_end = (self.first_bearing_year or 0) + self.expected_productive_years
            if plant_age > productive_end:
                return MaturityStage.DECLINING

        return MaturityStage.PRODUCTIVE

    def should_restart_cycle(
        self,
        current_phase: str,
        transition_rule: Optional[dict]
    ) -> tuple[bool, str]:
        """
        Prüft ob der saisonale Zyklus neu starten soll.
        Returns: (should_restart, reason)

        Spec-Audit 2026-07-02 D1/D6: Terminale Guard für begrenzt-zyklische und monokarpe
        Lebenszyklen. Bienniale (max_seasons=2) und monokarpe Arten
        (terminal_after_flowering=True) starten nach dem Blüh-/Samenzyklus NICHT neu,
        sondern gehen in eine terminale Seneszenz — auch wenn eine Transition-Regel
        fälschlich is_cycle_restart trüge.
        """
        # D1: Biennial/begrenzter Zyklus — nach der letzten erlaubten Saison kein Neustart.
        if self.max_seasons is not None and self.current_season_number >= self.max_seasons:
            return False, (
                f"Terminaler Lebenszyklus: letzte Saison {self.current_season_number} "
                f"von {self.max_seasons} erreicht (biennial/begrenzt) — kein Neustart, "
                f"Übergang in terminale Seneszenz"
            )
        # D6: Monokarp — nach Blüte/Samenreife terminal, kein Neustart.
        if self.terminal_after_flowering and current_phase in ('flowering', 'fruit_development', 'ripening'):
            return False, "Monokarpe Art: blüht einmal, terminale Seneszenz nach Samenreife"

        if transition_rule and transition_rule.get('is_cycle_restart'):
            return True, f"Saisonaler Neustart: Saison {self.current_season_number + 1}"
        return False, "Kein Zyklus-Neustart"

    def start_new_season(
        self,
        arango_db,
        season_year: int,
        chill_hours: int = 0
    ) -> dict:
        """
        Startet eine neue Saison: erstellt SeasonalCycle-Dokument,
        setzt Pflanze auf erste wiederkehrende Phase (typisch: dormancy oder bud_break).
        """
        new_season_number = self.current_season_number + 1
        maturity = self.get_maturity_stage(season_year)

        # Neuen SeasonalCycle anlegen
        cursor = arango_db.aql.execute("""
            LET plant = DOCUMENT(CONCAT('plant_instances/', @plant_id))
            LET season = FIRST(
                INSERT {
                    plant_instance_key: @plant_id,
                    season_year: @year,
                    season_number: @season_num,
                    started_at: DATE_ISO8601(DATE_NOW()),
                    maturity_stage: @maturity,
                    chill_hours_accumulated: @chill_hours
                } INTO seasonal_cycles
                RETURN NEW
            )
            INSERT { _from: plant._id, _to: season._id } INTO has_season
            RETURN season
        """, bind_vars={
            'plant_id': self.plant_id,
            'year': season_year,
            'season_num': new_season_number,
            'maturity': maturity.value,
            'chill_hours': chill_hours
        })

        return {
            'season_number': new_season_number,
            'season_year': season_year,
            'maturity_stage': maturity.value,
            'chill_hours': chill_hours
        }

    def get_season_comparison(self, arango_db) -> list[dict]:
        """Vergleicht Ertrag und Performance über alle Saisons"""
        cursor = arango_db.aql.execute("""
            FOR season IN seasonal_cycles
                FILTER season.plant_instance_key == @plant_id
                SORT season.season_number ASC
                RETURN {
                    season: season.season_number,
                    year: season.season_year,
                    maturity: season.maturity_stage,
                    yield_kg: season.yield_kg,
                    chill_hours: season.chill_hours_accumulated
                }
        """, bind_vars={'plant_id': self.plant_id})
        return list(cursor)


# Spec-Audit 2026-07-02 D1: Rückwärtskompatibler Alias — vor dem Audit hieß die Klasse
# PerennialCycleEngine (perennial-Sonderfall: max_seasons=None, terminal_after_flowering=False).
# Bestehende Referenzen bleiben gültig.
PerennialCycleEngine = CyclicLifecycleEngine
```

**Erweiterung des PhaseTransitionEngine für Dauerkulturen:**

Die bestehende Rückwärts-Transition-Sperre (`sequence_order`-Vergleich) wird für Dauerkulturen
erweitert: Wenn die `PhaseTransitionRule` das Flag `is_cycle_restart=true` hat, wird eine
Rückwärts-Transition erlaubt. Dies ist der einzige Fall, in dem `sequence_order` rückwärts
gehen darf — es handelt sich um den kontrollierten Saison-Neustart.

Pseudocode-Erweiterung:
```python
def validate_transition(self, plant_key: str, target_phase_key: str) -> list[str]:
    # ... bestehende Logik ...

    # Rückwärts-Check mit Dauerkulturen-Ausnahme
    if target_phase.sequence_order <= current_phase.sequence_order:
        transition_rule = self._find_transition_rule(current_phase.key, target_phase_key)
        if transition_rule and transition_rule.is_cycle_restart:
            warnings.append("Saisonaler Zyklus-Neustart")
        else:
            raise PhaseTransitionError("Rückwärts-Transition nicht erlaubt")
```

<!-- Quelle: ADR-003 / W-014 -->
**6. Saison-Aggregat-Engine (ADR-003):**

```python
from datetime import datetime
from celery import shared_task
from statistics import mean

class SensorAggregateEngine:
    """Berechnet saisonale Sensor-Aggregate für SeasonalCycle (ADR-003).

    Default-Aggregat-Set (Workshop-Frage 1):
      - temperature, humidity, vpd, soil_moisture: avg/min/max/p10/p90
      - dli: sum + avg_per_day (kumulativ statt Durchschnitt)
    """

    DEFAULT_QUANTILE_SENSORS = ("temperature", "humidity", "vpd", "soil_moisture")
    DEFAULT_CUMULATIVE_SENSORS = ("dli",)

    def compute(
        self,
        season: SeasonalCycle,
        sensor_data: dict[str, list[float]],
        config: Optional[dict] = None,
    ) -> dict:
        """Erzeugt sensor_aggregates-Dict für eine abgeschlossene Saison."""
        config = config or self._default_config()
        result = {}
        for sensor_type, values in sensor_data.items():
            if not values:
                continue
            if sensor_type in config.get("quantile_sensors", self.DEFAULT_QUANTILE_SENSORS):
                result[sensor_type] = self._aggregate_quantile(values)
            elif sensor_type in config.get("cumulative_sensors", self.DEFAULT_CUMULATIVE_SENSORS):
                result[sensor_type] = self._aggregate_cumulative(values, season)
        return result

    def _aggregate_quantile(self, values: list[float]) -> dict:
        sorted_v = sorted(values)
        n = len(sorted_v)
        return {
            "avg": mean(values),
            "min": sorted_v[0],
            "max": sorted_v[-1],
            "p10": sorted_v[int(n * 0.10)],
            "p90": sorted_v[int(n * 0.90)],
            "samples": n,
        }

    def _aggregate_cumulative(self, values: list[float], season: SeasonalCycle) -> dict:
        days = max(1, (season.ended_at - season.started_at).days) if season.ended_at else 1
        return {
            "sum": sum(values),
            "avg_per_day": sum(values) / days,
            "samples": len(values),
        }


@shared_task
def compute_seasonal_aggregates_task(season_key: str) -> None:
    """Celery-Task: Wird beim Setzen von SeasonalCycle.ended_at getriggert.

    Idempotent: Mehrfacher Aufruf erzeugt dasselbe Aggregat (deterministische
    Berechnung). Lazy-Update bei Sensor-Korrekturen (Workshop-Frage 4):
    Beim Lesezugriff vergleicht der Service `aggregate_computed_at` mit
    `last_modified_in_window` und triggert Re-Computation bei Drift.
    """
    season = season_repo.get(season_key)
    sensor_data = sensor_repo.fetch_for_season(season)  # Stufe 2 / Stufe 3
    aggregates = SensorAggregateEngine().compute(season, sensor_data, season.aggregate_config)
    season_repo.update(season_key, {
        "sensor_aggregates": aggregates,
        "aggregate_computed_at": datetime.utcnow(),
        "aggregate_source_retention_horizon": _detect_horizon(sensor_data),
    })
```

**Trigger:** Der Celery-Task wird automatisch ausgelöst, wenn `SeasonalCycle.ended_at` gesetzt wird (Saison endet, typisch: Übergang in Dormanz). Optional kann der Tenant-Admin den Task auch manuell für historische Saisons starten — solange Stufe-3-Tagesmittel noch verfügbar sind.

**Migration für bestehende Saisons:** Beim Deployment dieser Spec-Version läuft ein einmaliger Backfill-Task, der für alle abgeschlossenen `seasonal_cycles` ohne `aggregate_computed_at` die Aggregate aus den noch verfügbaren Stufe-2/3-Daten berechnet. Saisons, deren Daten bereits gelöscht wurden, behalten leere Aggregate (Datenverlust nicht reparierbar).
<!-- /Quelle: ADR-003 / W-014 -->

### Datenvalidierung:
```python
from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator

class RequirementProfileDefinition(BaseModel):
    """Ressourcen-Anforderungen einer Phase"""

    light_ppfd_target: int = Field(ge=0, le=2000, description="μmol/m²/s")
    dli_target_mol: Optional[float] = Field(
        None, ge=0.0, le=80.0,
        description="Daily Light Integral mol/m²/Tag. Zimmerpflanzen Niedriglicht: 2–5, Mittellicht: 5–12, Hochlicht: 12–20, Nutzpflanzen: 12–45"
    )
    dli_min_mol: Optional[float] = Field(
        None, ge=0.0, le=40.0,
        description="Minimaler DLI — unter diesem Wert nimmt die Pflanze langfristig Schaden"
    )
    light_spectrum: Optional[dict[str, float]] = Field(
        None,
        description="Spektrum-Anteile (Summe ≈ 1.0). Keys: blue, green, red, far_red. Zimmerpflanzen: Breitband-Weiß empfohlen."
    )
    photoperiod_hours: float = Field(ge=0, le=24)
    temperature_day_c: float = Field(ge=10, le=40)
    temperature_night_c: float = Field(ge=5, le=35)
    humidity_day_percent: int = Field(ge=20, le=95)
    humidity_night_percent: int = Field(ge=30, le=95)
    vpd_target_kpa: float = Field(ge=0.2, le=2.5)

    @field_validator('temperature_night_c')
    @classmethod
    def validate_temp_range(cls, v, info):
        day_temp = info.data.get('temperature_day_c')
        if day_temp and v > day_temp:
            raise ValueError("Nachttemperatur muss niedriger als Tagestemperatur sein")
        return v

    @field_validator('photoperiod_hours')
    @classmethod
    def validate_photoperiod(cls, v):
        """
        Photoperioden unter 8h sind kein Fehler — sie werden verwendet für:
        - Kurztagbehandlung bei Chrysanthemen (8-10h)
        - Vernalisierungs-Lichtregime (6-8h)
        - Forcing-Dunkelperioden (Rhabarber, Chicorée)
        Nur als Warnung loggen, nicht als Validierungsfehler.
        """
        import warnings
        if v < 8 and v > 0:
            warnings.warn(
                f"Photoperiode {v}h ist ungewöhnlich kurz. Normal für "
                f"Kurztagbehandlung oder Vernalisierung, kritisch für "
                f"reguläres Wachstum.", stacklevel=2
            )
        return v

class NutrientProfileDefinition(BaseModel):
    """Nährstoff-Profil für eine Phase"""

    npk_ratio: Tuple[int, int, int] = Field(description="Nitrogen-Phosphor-Kalium Verhältnis")
    target_ec_ms: float = Field(ge=0.0, le=4.0, description="Elektrische Leitfähigkeit in mS/cm")
    target_ph: float = Field(ge=4.0, le=8.0)

    @field_validator('npk_ratio')
    @classmethod
    def validate_npk(cls, v):
        if all(x == 0 for x in v):
            return v  # Flushing-Phase erlaubt
        if any(x < 0 for x in v):
            raise ValueError("NPK-Werte können nicht negativ sein")
        return v

TransitionTriggerType = Literal['time_based', 'manual', 'event_based', 'conditional', 'gdd_based']
# Spec-Audit 2026-07-02 B1/D2: Kanonisches Phasen-Vokabular. `germination` und `rooting`
# ergänzt, damit beide Lebenszyklus-Eintrittspunkte abgedeckt sind (Samen bzw. vegetative
# Vermehrung). Dies ist die EINZIGE maßgebliche Phasen-Wertliste; die frühere 7er-Prosa-Liste
# und die UI-NFR-016-Anzeige-Palette leiten sich hiervon ab. `harvest` ist KEINE Phase,
# sondern ein Ernte-Event (REQ-007); `drying`/`curing` sind Post-Harvest-Batch-Zustände (REQ-008).
PhaseType = Literal['germination', 'rooting', 'seedling', 'vegetative', 'bolting', 'flowering',
                    'ripening', 'dormancy', 'flushing', 'bud_break', 'fruit_development', 'senescence',
                    'hardening_off', 'acclimatization', 'active_growth', 'maintenance',
                    'repotting_recovery']
# germination: generative Keimung — Eintritt bei Samenvermehrung (seed_sowing/bulbil/tissue_culture, REQ-017 §D2)
# rooting: Einwurzelung vegetativer Vermehrung (Steckling/Ableger/Veredlung) — KANONISCH statt
#          der Synonyme 'Bewurzelung'/'Einwurzelung' bzw. 'seedling-für-Stecklinge' (REQ-017 §D2)
# bolting: Schossen — Streckung/Blütenstandsbildung im 2. Jahr biennaler Arten (Biennial-Template, §D1)
# hardening_off: Abhärtungsphase (Stress-Phase, s. Abschnitt "Stress-Phasen")
# acclimatization, active_growth, maintenance, repotting_recovery: Zimmerpflanzen-Phasen (REQ-020)

class SeasonalCycleDefinition(BaseModel):
    """Saisonaler Zyklus einer Dauerkultur"""

    plant_instance_key: str
    season_year: int = Field(ge=2000, le=2100)
    season_number: int = Field(ge=1)
    maturity_stage: Literal['juvenile', 'productive', 'declining']
    chill_hours_accumulated: int = Field(ge=0, default=0)
    yield_kg: Optional[float] = Field(None, ge=0)
    fruit_count: Optional[int] = Field(None, ge=0)

MaturityStage = Literal['juvenile', 'productive', 'declining']
```

**Standard-Phasen für Dauerkulturen (Perennial-Template):**

| Phase | `sequence_order` | `is_recurring` | `typical_duration_days` | `allows_harvest` | Beschreibung |
|---|---|---|---|---|---|
| `dormancy` | 0 | `true` | 90 (variabel) | `false` | Winterruhe, Kältestunden-Akkumulation |
| `bud_break` | 1 | `true` | 14 | `false` | Austrieb, Knospenöffnung |
| `vegetative` | 2 | `true` | 60 | `false` | Trieb- und Blattwachstum |
| `flowering` | 3 | `true` | 21 | `false` | Blüte, Bestäubung |
| `fruit_development` | 4 | `true` | 90 | `false` | Fruchtansatz und -wachstum |
| `ripening` | 5 | `true` | 30 | `true` | Fruchtreife, Ernte möglich |
| `senescence` | 6 | `true` | 30 | `false` | Blattfall, Einlagerung von Reservestoffen |

Transition `senescence → dormancy` hat `is_cycle_restart: true` und startet eine neue Saison.

Für immergrüne Dauerkulturen (z.B. Zitrus) entfällt `senescence`; `dormancy` kann optional sein.

<!-- Spec-Audit 2026-07-02 D1: Biennial-Template -->
**Standard-Phasen für Bienniale (Biennial-Template):**

Bienniale (Karotte, Petersilie, Sellerie, Rote Bete, Fingerhut) durchlaufen einen **begrenzten
Zwei-Saison-Zyklus** und sind **monokarp**: Blüte und Samenreife erfolgen erst im zweiten Jahr,
danach stirbt die Pflanze. Der `CyclicLifecycleEngine` bildet dies mit `cycle_type='biennial'`,
`max_seasons=2`, `terminal_after_flowering=True` ab.

| Phase | `sequence_order` | `season` | `is_recurring` | `typical_duration_days` | `allows_harvest` | Beschreibung |
|---|---|---|---|---|---|---|
| `germination` | 0 | 1 | `false` | 14 | `false` | Keimung (Jahr 1) |
| `seedling` | 1 | 1 | `false` | 21 | `false` | Jungpflanze |
| `vegetative` | 2 | 1 | `false` | 90 | `true` | Blatt-/Speicherorgan-Aufbau. **Ernte-Fenster für Wurzel-/Blattgemüse (Jahr 1) — siehe Kultur-Hinweis unten** |
| `dormancy` | 3 | 1→2 | `false` | 90 (Vernalisation) | `false` | Überwinterung; **Kältestunden erfüllen `vernalization_required` (REQ-001)** — Voraussetzung fürs Schossen |
| `bud_break` | 4 | 2 | `false` | 14 | `false` | Neuaustrieb (Jahr 2) |
| `bolting` | 5 | 2 | `false` | 21 | `false` | Schossen (Streckungswachstum, Blütenstandsbildung) |
| `flowering` | 6 | 2 | `false` | 30 | `false` | Blüte, Bestäubung |
| `ripening` | 7 | 2 | `false` | 45 | `true` | Samenreife (**Ernte = Saatgut**) |
| `senescence` | 8 | 2 | `false` | 14 | `false` | **`is_terminal: true`, `allows_disposal: true`** — Pflanze stirbt (monokarp) |

- Transition `ripening → senescence` ist **terminal** (`is_cycle_restart: false`); `should_restart_cycle()`
  gibt für Bienniale nach `max_seasons=2` bzw. `terminal_after_flowering` **kein** Neustart zurück.
- Neu im Vokabular: **`bolting`** (Schossen) ist eine biennial-/schossgefährdete-Kultur-Phase; sie ist als
  optionaler Phasenwert zu führen (Anzeige-Katalog UI-NFR-016). Kann bei nicht-schossrelevanten Bienalen entfallen.

> **Kultur-Hinweis (Karotte & Co. — verknüpft `cultivation_cycle_type`, REQ-001 §D2/A2):** Wird ein
> Bienniale für das **Speicherorgan** (Wurzel, Knolle, Blatt) angebaut, endet die Kultur mit der Ernte in
> **Saison 1** (Phase `vegetative`, `allows_harvest: true`) — die Pflanze wird als Einjährige geführt
> (`cultivation_cycle_type='annual'`, botanische `cycle_type='biennial'`), der Jahr-2-Blüh-/Samenpfad
> entfällt. Nur bei **Saatgutgewinnung** (oder Zierwert der Blüte) wird der volle Zwei-Jahres-Zyklus
> durchlaufen. Damit ist der frühere Widerspruch (Karotte `cycle_type='biennial'`, aber Phasen enden bei
> harvest; `vernalization_required=true` ohne gatende Phase) aufgelöst: die `dormancy`-Phase (seq 3) ist
> die vernalisationsgatende Phase, und `cultivation_cycle_type` entscheidet, ob Saison 2 überhaupt läuft.

<!-- Spec-Audit 2026-07-02 D4: Maturity-gated Phasenverzweigung (Juvenil-Skip) -->
**Reifegrad-abhängige Phasenverzweigung (Juvenil-Skip):**

Die Standard-`next_phase`-Kante ist einwertig — dadurch konnte der in **Szenario 5** (juveniler
Apfelbaum) geforderte Skip der reproduktiven Phasen bisher nicht strukturell abgebildet werden. Auflösung:
`next_phase` wird **mehrwertig** zugelassen und über `required_conditions` der zugehörigen
`phase_transition_rules` disambiguiert. Die Engine wählt aus den ausgehenden `next_phase`-Kanten die
erste, deren `required_conditions` erfüllt sind (deterministische Reihenfolge nach
`phase_transition_rules.priority`, höchste zuerst; die bedingungslose Default-Kante zuletzt).

Beispiel Dauerkultur-Phase `vegetative` mit zwei ausgehenden Kanten:

| Ziel-Phase | `trigger_type` | `required_conditions` | Bedeutung |
|---|---|---|---|
| `senescence` | `conditional` | `{"maturity_stage": "juvenile"}` | Juvenil: reproduktive Phasen (`flowering`/`fruit_development`/`ripening`) überspringen |
| `flowering` | `time_based`/`gdd_based` | – (Default) | Produktiv/declining: regulärer Blühpfad |

- Der Reifegrad kommt aus `CyclicLifecycleEngine.get_maturity_stage()`; `juvenile` (Pflanzenalter <
  `first_bearing_year`) ⇒ Skip-Kante, sonst Default-Kante. Der bisher nur im Test unterstellte Skip ist
  damit als maschinenlesbare Regel spezifiziert.
- Die Rückwärts-Sperre bleibt unberührt: `senescence` hat höheres `sequence_order` als `vegetative`; der
  anschließende `senescence → dormancy`-Neustart ist wie gehabt über `is_cycle_restart` gedeckt.
- Erweiterung des `phase_transition_rules`-Modells: neues optionales Feld
  `priority: int = 0` (höhere Zahl = früher geprüft) zur deterministischen Auswahl bei mehreren
  ausgehenden Kanten.

<!-- Spec-Audit 2026-07-02 D3: Post-Harvest-Handoff (Lifecycle → REQ-008-Batch) -->
**Post-Harvest-Handoff (Lifecycle → REQ-008):**

Trocknung/Curing/Lagerung sind bewusst **keine** `growth_phases`, sondern Post-Harvest-Zustände am
`batch` (REQ-008). Damit der Lebenszyklus dennoch lückenlos („kontinuierlich") ist, definiert dieser
Abschnitt den expliziten Übergabepunkt statt einer stillen Trennung:

- Erreicht eine Phase mit `allows_harvest: true` das Ernte-Event (REQ-007), erzeugt die Ernte einen
  `batch` (REQ-008); die Post-Harvest-Verantwortung für das geerntete Material (drying → curing → aging
  → storage) geht auf REQ-008 über. **Das Ernte-Event ist die Brücke, nicht eine Phase.**
- Was mit der **Pflanze** danach geschieht, hängt vom Archetyp ab:
  - **annuell / biennial / monokarp:** Transition auf `senescence` (`is_terminal: true`,
    `allows_disposal: true`) — Lebenszyklus endet.
  - **perennial (polykarp):** `ripening → senescence → dormancy` mit `is_cycle_restart: true` — die
    Pflanze lebt weiter; nur das geerntete Material wandert in den Post-Harvest-Batch.
  - **kontinuierliche Ernte** (cut & come again — Salat/Kräuter, REQ-007 `harvest_pattern='continuous'`):
    die Pflanze verbleibt in `vegetative`/`ripening`; jede Teil-Ernte erzeugt einen eigenen Batch **ohne**
    Phasenwechsel.
- Cross-Ref: die Phase-Filter-Chips `drying`/`curing` (Listenansicht, DoD) sind Anzeige-Aliasse für den
  Batch-Zustand, keine `growth_phase` (siehe B1).

<!-- Spec-Audit 2026-07-02 D7: Bulb-Geophyt-Zyklus an seasonal_cycles/dormancy angebunden -->
**Knollen-/Zwiebelgeophyten-Zyklus (Bulb-Geophyten):**

Für `growth_habit='bulb_geophyte'` (Dahlie, Gladiole, Tulpe) war der Jahreszyklus
dig → dry → store → pre-sprout bisher nur in `OverwinteringProfile.tuber_status` (REQ-022) geführt und
von `GrowthPhase`/`seasonal_cycles` entkoppelt. Anbindung:

- Die **Lager-/Ruheperiode** (`tuber_status='stored'`) entspricht der `dormancy`-GrowthPhase des
  jeweiligen `seasonal_cycles`-Eintrags. `dig_store` (REQ-022 Winter-Pfad B, D5) ist die **verlagerte**
  Ausprägung dieser `dormancy` — kein separater, konkurrierender Zyklus.
- `pre_sprouting`/Vortreiben (REQ-022 `tuber_status`) entspricht dem `bud_break` der Folgesaison; die Transition
  `dormancy (= Lager) → bud_break (= Austrieb)` trägt `is_cycle_restart: true` (perennierender Geophyt).
- Damit ist der D7-Bruch geschlossen: die `tuber_status`-Übergänge (REQ-022) und die Saison-Phasen
  (REQ-003) beschreiben denselben Zyklus auf zwei Ebenen und müssen konsistent sein (analog D5-Invariante).

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

Zustandslose Berechnungsendpunkte (VPD, GDD, Photoperiode) sind öffentlich zugänglich, da sie keine persistierten Daten lesen oder schreiben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| PlantInstances (Tenant-scoped) | Mitglied | Mitglied | Admin |
| GrowthPhases (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Phase-Transitions (Tenant-scoped) | — | Mitglied | — |
| Berechnungen (VPD, GDD, Photoperiode) | Nein | — | — |

## 5. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): LifecycleConfig (`cycle_type`, `dormancy_required`, `vernalization_required`),
  DormancyTrigger (Dormanz-Auslösung), VernalizationTracker (Kältestunden-Tracking),
  GrowthPhase-Definitionen, Cultivar `photoperiod_type` (photoperiodic/autoflower/day_neutral — G-009)
- REQ-002 (Standort): Slot-Zuordnung für Ressourcen-Steuerung
- REQ-005 (Sensorik): Klimadaten für VPD-Berechnung und Feedback-Loop

**Wird benötigt von:**
- REQ-004 (Düngung): NPK-Profile aus aktueller Phase
- REQ-006 (Tasks): Phasenspezifische Aufgaben (z.B. Topping nur in Vegi)
- REQ-007 (Ernte): Harvest-Permission nur in finalen Phasen
- REQ-010 (IPM): Phasenspezifische Vulnerabilitäten

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Phasen-State-Machine:** Graph-basierte Zustandsübergänge voll funktionsfähig
- [ ] **Auto-Transition:** Zeitbasierte Übergänge mit konfigurierbarer Vorwarnzeit
- [ ] **Manual-Override:** Manuelle Phasen-Einleitung (z.B. Blüte) jederzeit möglich
- [ ] **Ressourcen-Profile:** Jede Phase hat Light/Climate/Nutrient-Profile
- [ ] **VPD-Berechnung:** Echtzeit-VPD mit Zielbereich-Validierung
- [ ] **Photoperioden-Transition:** Gradueller Übergang (7 Tage) zwischen Licht-Zyklen
- [ ] **Phase-History:** Vollständiges Tracking aller Phasen mit Performance-Scores
- [ ] **NPK-Auto-Adjust:** Automatische Dünger-Anpassung bei Phasenwechsel
- [ ] **Stress-Phasen:** Support für temporäre Zustände (Hardening, Drought-Stress)
- [ ] **Rückwärts-Transition:** Verhinderung (Blüte → Vegi nicht erlaubt)
- [ ] **Multi-Phase-Harvests:** Support für kontinuierliche Ernte (z.B. Salat, Kräuter)
<!-- Quelle: Tabellen-Analyse UI-NFR-010 §7.2 -->
- [ ] **Listenansicht-Filter:** PlantInstance-Liste bietet Phase-Filter (Enum-Chip-Gruppe aus dem kanonischen `PhaseType`-Literal; `drying`/`curing` sind Post-Harvest-Zustände aus REQ-008 und nur als Anzeige-Chips zulässig, keine `growth_phases`) und Standort-Filter (Site-Dropdown); URL-Parameter `?phase=...&site_key=...` <!-- Spec-Audit 2026-07-01 B1 -->
- [ ] **Tablet-Spaltenprioritäten:** PlantInstance-ListPage blendet auf Tablet (≤1024px) Instanz-ID und Entfernt-am aus; nur Name, Sorte, Phase bleiben sichtbar (UI-NFR-010 §8.1)
- [ ] **Dashboard-Integration:** Visuelle Phase-Indikatoren mit Fortschrittsbalken
- [ ] **Notification-System:** Push bei anstehenden Auto-Transitions
- [ ] **Profile-Versionierung:** Änderungen an Standard-Profilen historisiert
- [ ] **Species-Override:** Spezies-spezifische Profile überschreiben Defaults
- [ ] **DLI-Berechnung:** Daily Light Integral (mol/m²/Tag) als Zielmetrik neben PPFD
- [ ] **GDD-Transition:** Growing Degree Days als biologisch akkurater Transition-Trigger neben Kalendertagen
- [ ] **Photoperiod-Response:** short_day/long_day/day_neutral bestimmt Blüte-Photoperiode pro Species
- [ ] **Spezies-VPD:** VPD-Zielbereiche nach species_type differenziert (leafy, fruiting, flowering)
- [ ] **Dauerkulturen-Zyklus:** Perenniale Pflanzen durchlaufen jährlich wiederkehrende Phasenzyklen
- [ ] **Zyklische Transition:** `is_cycle_restart`-Flag erlaubt kontrollierten Rückwärts-Übergang (Seneszenz → Dormanz)
- [ ] **Saisonales Tracking:** Jede Saison wird als `seasonal_cycles`-Dokument mit Jahr, Ertrag und Reifegrad erfasst
- [ ] **Reifegrad-Berechnung:** Automatische Bestimmung von juvenile/productive/declining basierend auf Pflanzenalter
- [ ] **Saison-Vergleich:** Ertrag und Phasen-Dauern sind über mehrere Jahre vergleichbar
- [ ] **Perennial-Phasen-Template:** Standard-Phasensequenz für Dauerkulturen (dormancy → bud_break → vegetative → flowering → fruit_development → ripening → senescence)
- [ ] **Kältestunden-Integration:** Chill-Hours pro Saison aus VernalizationTracker (REQ-001) übernommen
<!-- Quelle: Cannabis Indoor Grower Review G-009 -->
- [ ] **Autoflower-Transition:** Bei `cultivar_photoperiod_type='autoflower'` ist Vegi→Blüte automatisch zeitbasiert (kein manueller Trigger, keine Photoperioden-Änderung)
- [ ] **Autoflower-Lichtprofil:** Autoflower-Cultivare erhalten durchgehend 20/4 oder 18/6 Photoperiode — kein Wechsel auf 12/12 bei Blüte
- [ ] **Autoflower-Presets:** Drei Standard-Presets (Fast/Standard/Long) mit vorgefertigten Phasendauern verfügbar
- [ ] **Autoflower-HST-Warnung:** HST-Methoden (Topping/FIM/Supercropping) bei Autoflower-Cultivaren erzeugen Warnung (nicht Blockade) — cross-ref REQ-006
- [ ] **Autoflower-LST-Erlaubt:** LST-Methoden bei Autoflower ohne Einschränkung erlaubt
<!-- /Quelle: G-009 -->
<!-- Quelle: Widerspruchsanalyse W-003 -->
- [ ] **Run-Membership-Guard (Single):** Direkter Phasenwechsel auf einer `PlantInstance`, die Mitglied eines aktiven `PlantingRun` ist (`run_contains.detached_at = null`, `run.status = 'active'`), liefert HTTP 409 mit `error_code='phase.run_owned'` und enthält `run_key`, `plant_key` und `remediation` im Body.
- [ ] **Standalone-Phasenwechsel:** Direkter Phasenwechsel auf einer PlantInstance ohne aktive `run_contains`-Edge oder mit `detached_at != null` funktioniert regulär.
- [ ] **Detach-Recovery:** Nach `detach`-Operation (REQ-013 §3) ist der direkte Phasenwechsel auf der nun-standalone Pflanze wieder erlaubt.
- [ ] **Inactive-Run-Phasenwechsel:** Wenn der zugehörige Run `status` in `{completed, cancelled, harvesting}` hat, ist der direkte Phasenwechsel auf der PlantInstance erlaubt (Run-Lifecycle abgeschlossen).
- [ ] **Batch All-or-Nothing:** Der Batch-Phasenwechsel-Endpoint lehnt den gesamten Batch mit HTTP 409 `error_code='phase.batch_run_owned'` ab, sobald mindestens eine Pflanze in der Liste Mitglied eines aktiven Runs ist. Response enthält Liste aller `conflicts` mit `plant_key` und `run_key`. Keine Pflanze des Batches wird transitioniert.
- [ ] **Engine-only Guard:** `PhaseTransitionEngine.assert_transition_allowed()` ist die einzige Stelle mit Run-Membership-Check — der API-Layer wirft den Guard nicht direkt, sondern lässt `RunMembershipConflictError` bis zum Exception-Handler durchpropagieren.
<!-- /Quelle: Widerspruchsanalyse W-003 -->

### Testszenarien:

**Szenario 1: Automatische Vegi → Blüte Transition**
```
GIVEN: Cannabis in Vegi-Phase seit 28 Tagen (geplant: 28 Tage)
WHEN: Täglicher Scheduler läuft
THEN:
  - System initiiert Übergang zu Blüte-Phase
  - Photoperiode wechselt graduell von 18h auf 12h (über 7 Tage)
  - NPK-Ratio ändert sich von 3-1-2 zu 1-3-3
  - EC-Zielwert steigt von 1.4 auf 1.8 mS
  - Alert: "Blütephase gestartet - Überwache VPD (Ziel: 1.0-1.5 kPa)"
```

**Szenario 2: VPD außerhalb Zielbereich (Leaf-VPD)**
```
GIVEN: Pflanze in Blüte (species_type: flowering), Ziel-VPD: 1.0-1.5 kPa,
       aktuell: Temp 28°C, RLF 55%, Blatttemp-Offset -2°C
WHEN: System berechnet aktuellen Leaf-VPD
THEN:
  - SVP_leaf(26°C) = 3362 Pa, AVP(28°C, 55%) = 2081 Pa
  - Leaf-VPD: (3362 - 2081) / 1000 = 1.28 kPa (OPTIMAL)
  - Status: GRÜN
  - Keine Anpassungen erforderlich

WHEN: RLF steigt auf 80%
THEN:
  - AVP(28°C, 80%) = 3026 Pa
  - Neuer Leaf-VPD: (3362 - 3026) / 1000 = 0.34 kPa (ZU NIEDRIG)
  - Status: ROT
  - Empfehlung: "Senke RLF auf 55-60% oder erhöhe Temp auf 30°C"
```

**Szenario 3: Manuelle Blüte-Einleitung bei Photoperiod-neutraler Pflanze**
```
GIVEN: Autoflower-Cannabis (day_neutral), aktuell Vegi
WHEN: Nutzer klickt "Blüte einleiten"
THEN:
  - Sofortige Transition (keine Photoperioden-Änderung)
  - NPK-Wechsel zu Blüte-Profil
  - Phase-History dokumentiert: "Manual override by user"
  - Nächste Auto-Transition geplant für: +56 Tage (typische Blütedauer)
```

<!-- Quelle: Cannabis Indoor Grower Review G-009 -->
**Szenario 3a: Autoflower — Automatischer Vegi→Blüte Übergang**
```
GIVEN: Cannabis Cultivar "Northern Lights Auto" mit photoperiod_type='autoflower',
       autoflower_days_to_flower=25, autoflower_total_cycle_days=75
  - Aktuell in vegetativer Phase seit 25 Tagen
  - Lichtprofil: 20/4 durchgehend
WHEN: Täglicher Scheduler läuft
THEN:
  - System erkennt: days_in_veg (25) >= autoflower_days_to_flower (25)
  - Automatischer Übergang Vegi → Blüte (TIME_BASED, nicht MANUAL)
  - Lichtprofil bleibt bei 20/4 (KEIN Wechsel auf 12/12!)
  - NPK-Wechsel zu Blüte-Profil (N↓, P↑, K↑)
  - Nächste Auto-Transition: +50 Tage (75 - 25 = Blütephase)
  - Phase-History: "Autoflower auto-transition (25 Tage ab Keimung)"
```

**Szenario 3b: Autoflower — HST-Training-Warnung**
```
GIVEN: Cannabis Cultivar mit photoperiod_type='autoflower', aktuell Vegi seit 10 Tagen
WHEN: Nutzer erstellt Task "Topping" (HST-Methode) für diesen Cultivar
THEN:
  - System zeigt Warnung: "HST-Methode 'Topping' bei Autoflower nicht empfohlen.
    Autoflower haben eine begrenzte vegetative Phase (10 Tage bisher).
    Erholungszeit nach Topping beträgt 7–14 Tage, was bei Autoflowern den
    Ertrag reduzieren kann. LST (Low-Stress-Training) wird stattdessen empfohlen."
  - Task wird NICHT blockiert (Nutzer kann Warnung überstimmen)
  - Bei LST-Task ("Bending", "ScrOG"): Keine Warnung, direkt erlaubt
```

**Szenario 3c: Autoflower — Photoperiode bleibt konstant**
```
GIVEN: Cannabis Cultivar mit photoperiod_type='autoflower', Transition Vegi → Blüte steht an
WHEN: System führt Phasenwechsel durch
THEN:
  - PhotoperiodManager wird NICHT aufgerufen (kein gradueller Wechsel)
  - Photoperiode bleibt bei 20h (oder konfiguriertem Wert 18–24h)
  - ResourceProfileGenerator liefert photoperiod=20 für alle Phasen
  - DLI wird mit 20h berechnet (nicht 12h wie bei photoperiodischen Sorten)
```
<!-- /Quelle: G-009 -->

**Szenario 4: Gradueller Photoperioden-Wechsel**
```
GIVEN: Transition von 18h → 12h über 7 Tage
WHEN: Transition startet
THEN:
  - Tag 0: 18:00h
  - Tag 1: 17:09h (-51 min)
  - Tag 2: 16:17h (-51 min)
  - Tag 3: 15:26h (-51 min)
  - Tag 4: 14:34h (-51 min)
  - Tag 5: 13:43h (-51 min)
  - Tag 6: 12:51h (-51 min)
  - Tag 7: 12:00h (Ziel erreicht)
```

**Szenario 5: Apfelbaum — Erster Saisonzyklus (Juvenil)**
```
GIVEN: Apfelbaum (Malus domestica, 'Boskoop'), gepflanzt 2024,
       first_bearing_year: 3, LifecycleConfig: cycle_type=perennial
WHEN: Pflanze durchläuft Saison 1 (2024)
THEN:
  - Maturity-Stage: "juvenile" (Alter < 3 Jahre)
  - Phasen: dormancy → bud_break → vegetative → senescence → dormancy
  - Phasen flowering/fruit_development/ripening werden übersprungen (juvenil)
  - SeasonalCycle-Dokument: { season_number: 1, season_year: 2024, maturity_stage: "juvenile", yield_kg: null }
```

**Szenario 6: Apfelbaum — Produktive Saison mit Ernte**
```
GIVEN: Apfelbaum, gepflanzt 2020, aktuell Saison 5 (2025), maturity_stage: "productive"
       Durchlief: dormancy (90 Tage, 800 Kältestunden) → bud_break → vegetative → flowering → fruit_development → ripening
WHEN: Nutzer erfasst Ernte: 45 kg, 320 Äpfel
THEN:
  - SeasonalCycle wird aktualisiert: { yield_kg: 45.0, fruit_count: 320 }
  - Saison-Vergleich zeigt: 2023: 38 kg, 2024: 42 kg, 2025: 45 kg (steigend)
  - Nach Ernte: Transition zu senescence → dormancy (is_cycle_restart=true)
  - Neue Saison 6 (2026) wird angelegt
```

**Szenario 7: Zyklische Transition — Seneszenz → Dormanz**
```
GIVEN: Perenniale Pflanze in Phase "senescence" (sequence_order: 6)
WHEN: Transition zu "dormancy" (sequence_order: 0) wird ausgelöst
THEN:
  - Normale Rückwärts-Sperre wird NICHT ausgelöst (is_cycle_restart=true)
  - Aktuelle Saison wird geschlossen (ended_at gesetzt)
  - Neue Saison wird erstellt (season_number + 1)
  - Phase-History wird korrekt der neuen Saison zugeordnet
```

---

**Hinweise für RAG-Integration:**
- Keywords: Phasensteuerung, State-Machine, VPD, Photoperiode, NPK-Profil, Ressourcen, Dauerkultur, Perennial, Saisonzyklus, Reifegrad, Kältestunden, Obstbaum, Juvenil, Autoflower, HST-Warnung, Cultivar-Photoperiod-Type
- Fachbegriffe: Phänologie, Transpiration, Vapor Pressure Deficit, PPFD, DLI (Daily Light Integral), GDD (Growing Degree Days), Spektrum, Vernalisierung, Seneszenz, Austrieb, Chill-Hours, Fruchtentwicklung, Photoperiod-Response (short_day, long_day, day_neutral), Leaf-VPD, Autoflower (Cannabis ruderalis), HST (High-Stress-Training), LST (Low-Stress-Training)
- Verknüpfung: Zentral für REQ-004 (Düngung), REQ-005 (Sensorik), REQ-006 (Tasks)
