# Spezifikation: REQ-013 - Pflanzdurchlauf-Verwaltung & Batch-Operationen

```yaml
ID: REQ-013
Titel: Pflanzdurchlauf-Verwaltung & Batch-Operationen
Kategorie: Gruppenmanagement
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB
Status: Entwurf
Version: 2.0 (Run als primaere Verwaltungseinheit, Pflanzen-Tagebuch, kein Mixed-Culture)
```

## 1. Business Case

**User Story:** "Als Gaertner moechte ich zusammengehoerige Pflanzen als Gruppe anlegen und verwalten, um typische Praxis-Szenarien wie '20 Tomaten ins Hochbeet setzen' oder '10 Stecklinge fuer den naechsten Erntezyklus' effizient abzubilden, alle Operationen auf der Gruppe auszufuehren und bei Bedarf individuelle Beobachtungen pro Pflanze in einem Tagebuch festzuhalten."

**Beschreibung:**
Das System fuehrt den **Pflanzdurchlauf (Planting Run)** als **primaere Verwaltungseinheit** ein. Ein PlantingRun besitzt Phasen, Aufgaben, Naehrstoffplaene, Pflege, IPM-Inspektionen und Ernte. Innerhalb eines Runs gibt es **keine Einzelbearbeitung** — alle Operationen gelten fuer alle Pflanzen im Run gleichermassen. Die einzelne PlantInstance ist ein schlanker Inventar-Eintrag mit optionalem Tagebuch.

- **Run-Level-Management:** Phasenwechsel, Aufgaben, Duengung, Pflege, IPM und Ernte operieren auf dem Run — nicht auf einzelnen Pflanzen
- **Batch-Erstellung:** N Pflanzen in einer Operation mit auto-generierten IDs anlegen
- **Batch-Ernte:** HarvestBatch (REQ-007) direkt aus PlantingRun erstellen → Seed-to-Shelf-Traceability
- **Batch-Entfernung:** Run abschliessen und alle Pflanzen als entfernt markieren
- **Pflanzen-Tagebuch:** Individuelle Beobachtungen pro Pflanze dokumentierbar (einziges individuelles Feature)
- **Detach → Standalone:** Einzelne Pflanzen koennen jederzeit aus der Gruppe herausgeloest und als eigenstaendige PlantInstance weiterverwaltet werden

**Grundprinzipien:**

- **Primaere Verwaltungseinheit:** Ein PlantingRun besitzt Phasen, Tasks, Naehrstoffplaene, Pflege, IPM und Ernte. Alle Operationen gelten fuer den gesamten Run.
- **Schlanke Instanz:** PlantInstance innerhalb eines Runs ist ein Zaehler mit Slot-Zuweisung und optionalem Tagebuch — keine eigenen Phasen, Tasks oder Pflegeprofile.
- **Keine Doppelzugehoerigkeit:** Eine PlantInstance gehoert zu maximal einem aktiven PlantingRun (oder zu keinem).
- **Soft Binding:** Pflanzen koennen jederzeit vom Run abgetrennt (detached) werden. Die Pflanze erhaelt dabei die aktuelle Phase des Runs kopiert und wird zur eigenstaendigen PlantInstance.
- **Standalone-Modus:** Eine PlantInstance ohne aktiven Run (detached oder direkt erstellt) behaelt volle Management-Faehigkeiten (Phase, Tasks, Care etc.) — das Dual-Modell.
- **Seed-to-Shelf:** Direkte Verknuepfung zu HarvestBatch (REQ-007) fuer lueckenlose Rueckverfolgbarkeit

### 1.1 Dual-Modell: Run-Managed vs. Standalone

```
┌─────────────────────────────────────────────────┐
│  PlantInstance IN einem aktiven Run              │
│  ─────────────────────────────────────           │
│  • Phase: vom Run (run.current_phase_key)        │
│  • Tasks: vom Run (has_task: Run → Task)         │
│  • Care: vom Run (has_care_profile: Run → ...)   │
│  • Nutrient: vom Run (run_follows_plan)          │
│  • Eigene Features: nur Tagebuch + Slot          │
│  • Keine Einzelbearbeitung moeglich              │
└─────────────────────────────────────────────────┘

     │ detach
     ▼

┌─────────────────────────────────────────────────┐
│  PlantInstance STANDALONE (nicht in aktivem Run) │
│  ─────────────────────────────────────           │
│  • Phase: eigene (current_phase auf Plant)       │
│  • Tasks: eigene (has_task: Plant → Task)        │
│  • Care: eigene (has_care_profile: Plant → ...)  │
│  • Nutrient: eigene (follows_plan: Plant → ...)  │
│  • Tagebuch: ja                                  │
│  • Volle Einzelverwaltung                        │
└─────────────────────────────────────────────────┘
```

### 1.2 Drei Szenarien

**Szenario 1: Monokultur — 20 Tomaten San Marzano im Hochbeet A**
```
PlantingRun: "Tomaten Hochbeet A 2025"
  type: monoculture
  status: active
  current_phase: vegetative
  Entry: { species: Solanum lycopersicum, cultivar: San Marzano, quantity: 20 }
  Location: Hochbeet A
  Substrate: Bio-Erde Charge #2025-03
  Plants: HOCHBEETA_TOM_01 … HOCHBEETA_TOM_20 (auto-generiert, schlanke Inventar-Eintraege)
```

**Szenario 2: Klone — 10 Cannabis-Stecklinge im Growzelt**
```
PlantingRun: "White Widow Klone Runde 3"
  type: clone
  status: active
  current_phase: rooting
  Entry: { species: Cannabis sativa, cultivar: White Widow, quantity: 10 }
  Location: Grow Zelt 1
  Substrate: Coco-Perlite 70/30 Charge #2025-04
  source_plant_key: "GROWZELT1_MOTHER_WW01"  ← Mutterpflanze
  Plants: GROWZELT1_WW3_01 … GROWZELT1_WW3_10 (auto-generiert)
```

**Szenario 3: Detach → Standalone**
```
1. Pflanze HOCHBEETA_TOM_05 zeigt Krankheitssymptome
2. Gaertner loest sie vom Run ab (detach, category: disease)
3. Pflanze erhaelt current_phase_key = "vegetative" (kopiert vom Run)
4. Pflanze wird zur eigenstaendigen PlantInstance mit vollem Management
5. Gaertner kann IPM-Behandlung, separate Phasenwechsel etc. durchfuehren
6. Run zeigt active_plant_count: 19
```

<!-- Quelle: Outdoor-Garden-Planner Review G-008, G-009 -->
**Szenario 4: Sukzessions-Aussaat — "Alle 3 Wochen Salat nachsaeen"**
```
1. Gaertnerin Lisa erstellt einen Succession-Plan:
   name: "Salat-Staffel Beet C 2026"
   base_species: Lactuca sativa
   cultivar: "Lollo Rosso"
   interval_days: 21
   start_date: 2026-04-01
   end_date: 2026-08-31
   plants_per_batch: 12
   location: Beet C

2. System generiert automatisch 8 PlantingRuns:
   - "Salat-Staffel 1/8" (01.04.) → status: planned
   - "Salat-Staffel 2/8" (22.04.) → status: planned
   - "Salat-Staffel 3/8" (13.05.) → status: planned
   - ... bis "Salat-Staffel 8/8" (20.08.)

3. Jeder Run wird mit Erinnerung "Naechste Salat-Aussaat in 3 Tagen" angekuendigt
4. Lisa bestaetigt → Run-Status wechselt zu active, Phase wird gesetzt
5. Ernte-Ueberlappung: Waehrend Staffel 1 geerntet wird, waechst Staffel 3
```

**Hinweis Mischkultur:** Fuer Mischkultur-Szenarien (Tomate + Basilikum + Tagetes) werden **separate Runs pro Art** erstellt. Die Companion-Beziehungen werden ueber den Standort/Beet-Graphen modelliert (REQ-028 Mischkultur & Companion Planting). Grund: Verschiedene Arten haben unterschiedliche Phasen-Sequenzen, Naehrstoffplaene und Pflegezeitpunkte — ein gemeinsamer Run wuerde diese Unterschiede nicht abbilden koennen.

## 2. ArangoDB-Modellierung

### Nodes:

- **`:PlantingRun`** — Pflanzdurchlauf (primaere Verwaltungseinheit)
  - Collection: `planting_runs`
  - Properties:
    - `name: str` (Benutzerfreundlicher Name, z.B. "Tomaten Hochbeet A 2025")
    - `run_type: Literal['monoculture', 'clone']`
    - `status: Literal['planned', 'active', 'harvesting', 'completed', 'cancelled']`
    - `planned_quantity: int` (Geplante Gesamtanzahl Pflanzen)
    - `actual_quantity: int` (Tatsaechlich erzeugte Pflanzen, berechnet)
    - `current_phase_key: Optional[str]` (Aktuelle Wachstumsphase des gesamten Runs — alle Pflanzen im Run teilen diese Phase)
    - `current_phase_started_at: Optional[datetime]` (Wann der Run in die aktuelle Phase eingetreten ist)
    - `lifecycle_config_key: Optional[str]` (Referenz auf Lifecycle-Konfiguration fuer Phase-Sequenz)
    - `planned_start_date: Optional[date]` (Geplantes Startdatum)
    - `started_at: Optional[datetime]` (Tatsaechlicher Start)
    - `completed_at: Optional[datetime]` (Abschluss-Zeitpunkt)
    - `source_plant_key: Optional[str]` (Nur bei `clone`: Key der Mutterpflanze)
    - `clone_generation: Optional[int]` (Nur bei `clone`: 1 = direkt von Saat-Pflanze, 2+ = Klon vom Klon. Vigor kann ueber Generationen nachlassen.)
    - `propagation_method: Optional[Literal['seed', 'cutting', 'tissue_culture', 'air_layer', 'division']]` (Vermehrungsmethode — beeinflusst Wurzelsystem-Qualitaet und Erfolgsrate)
    - `clone_from_run_key: Optional[str]` (Key eines bestehenden Runs als Vorlage — fuer Staffelanbau/Succession Planting und **Jahreswiederholung**: nur Konfiguration wird kopiert, nicht die Pflanzen)
    <!-- Quelle: Zierpflanzen-Analyse Stiefmuetterchen-Use-Case 2026-03 -->
    - `annual_repeat: bool` (Default: `false`. Wenn `true`, wird der Run im Kalender als jaehrlich wiederkehrend markiert und im Aussaatkalender (REQ-015) als Vorschlag fuer das Folgejahr angezeigt.)
    - `repeat_month: Optional[int]` (Monat (1–12) in dem der Run jaehrlich wiederholt werden soll. Nur relevant wenn `annual_repeat == true`.)
    - `previous_run_key: Optional[str]` (Referenz auf den Run des Vorjahres — ermoeglicht Jahresvergleich: Keimrate, Ueberlebensrate, Bluehdauer)
    <!-- /Quelle: Zierpflanzen-Analyse Stiefmuetterchen-Use-Case 2026-03 -->
    - `germination_count: Optional[int]` (Bei Saat: Anzahl tatsaechlich gekeimter Samen — nachtraeglich erfasst)
    - `rooting_count: Optional[int]` (Bei Klonen: Anzahl erfolgreich bewurzelter Stecklinge)
    - `survival_rate: Optional[float]` (actual_quantity / planned_quantity — berechnet nach Run-Abschluss)
    - `primary_loss_reason: Optional[str]` (Haeufigste Ausfallursache — fuer Planung zukuenftiger Runs)
    - `nutrient_plan_key: Optional[str]` (Denormalisierte Referenz auf NutrientPlan aus REQ-004; Plan fuer den gesamten Run. Wird ueber `RUN_FOLLOWS_PLAN`-Edge normalisiert in der Graph-Schicht, hier denormalisiert fuer performante Abfrage)
    - `notes: Optional[str]`
    <!-- Quelle: Outdoor-Garden-Planner Review G-009 -->
    - `succession_plan_key: Optional[str]` (Referenz auf uebergeordneten Succession-Plan)
    - `succession_sequence: Optional[int]` (Laufende Nummer in der Staffel, z.B. 3 von 8)
    - `succession_total: Optional[int]` (Gesamtanzahl Staffeln)
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:PlantingRunEntry`** — Artenzusammensetzung eines Durchlaufs
  - Collection: `planting_run_entries`
  - Properties:
    - `species_key: str` (Referenz auf Species)
    - `cultivar_key: Optional[str]` (Referenz auf Cultivar, optional)
    - `quantity: int` (Geplante Anzahl fuer diese Art)
    - `id_prefix: Optional[str]` (Praefix fuer auto-generierte Pflanzen-IDs, z.B. "TOM", "WW3")
    - `spacing_cm: Optional[int]` (Empfohlener Pflanzabstand)
    - `notes: Optional[str]`

- **`:PlantInstance`** (innerhalb eines Runs) — Schlanker Inventar-Eintrag
  - Collection: `plant_instances` (bestehend)
  - Properties (Run-Kontext — nur diese Felder relevant):
    - `instance_id: str` (Eindeutige ID, z.B. "HOCHBEETA_TOM_01")
    - `species_key: str` (Denormalisiert vom Entry)
    - `cultivar_key: Optional[str]`
    - `slot_key: Optional[str]` (Individuelle Slot-Zuweisung)
    - `planted_on: date`
    - `removed_on: Optional[date]` (Soft-Deletion)
    - `plant_name: Optional[str]` (Optionaler Benutzername)
    - `created_at: datetime`
    - `updated_at: datetime`
  - **Hinweis:** Felder wie `current_phase_key`, `current_phase_started_at` existieren weiterhin auf dem Model fuer den Standalone-Modus, werden aber ignoriert solange die Pflanze Mitglied eines aktiven Runs ist.

- **`:PlantDiaryEntry`** — Individuelles Pflanzen-Tagebuch
  - Collection: `plant_diary_entries`
  - Properties:
    - `entry_type: Literal['observation', 'problem', 'milestone', 'measurement', 'photo', 'note']`
    - `title: Optional[str]` (Kurztitel, max 200 Zeichen)
    - `text: str` (Freitext, max 5000 Zeichen)
    - `photo_refs: list[str]` (S3-URLs, max 5 Bilder)
    - `tags: list[str]` (Freitext-Tags fuer Filterung)
    - `measurements: Optional[dict]` (Strukturierte Messwerte: `height_cm`, `leaf_count`, `branch_count`, `stem_diameter_mm`, `canopy_width_cm` etc.)
    - `created_by: str` (user_key)
    - `created_at: datetime`
    - `updated_at: datetime`

<!-- Quelle: Outdoor-Garden-Planner Review G-009 -->
- **`:SuccessionPlan`** — Staffelanbau-Plan (generiert automatisch PlantingRuns)
  - Collection: `succession_plans`
  - Properties:
    - `name: str` (z.B. "Salat-Staffel Beet C 2026")
    - `species_key: str` (Referenz auf Species)
    - `cultivar_key: Optional[str]` (Referenz auf Cultivar)
    - `interval_days: int` (Tage zwischen Staffeln, z.B. 21 fuer Salat)
    - `start_date: date` (Erste Aussaat)
    - `end_date: date` (Letzte Aussaat)
    - `plants_per_batch: int` (Pflanzen pro Staffel)
    - `total_batches: int` (Berechnet: ceil((end_date - start_date) / interval_days))
    - `completed_batches: int` (Abgeschlossene Staffeln)
    - `status: Literal['planned', 'active', 'completed', 'cancelled']`
    - `reminder_days_before: int` (Erinnerung N Tage vor naechster Aussaat, Default: 3)
    - `notes: Optional[str]`
    - `created_at: datetime`
    - `updated_at: datetime`

### Konfigurationsregeln:

| Run-Type | Entries | Constraint |
|----------|---------|------------|
| `monoculture` | Genau 1 | Genau ein Entry mit species_key |
| `clone` | Genau 1 | Genau ein Entry; `source_plant_key` auf PlantingRun erforderlich |

### Edges (ArangoDB Edge Collections):

**Run-Membership:**

- **`run_contains`**: `PlantingRun → PlantInstance`
  - Properties:
    - `added_at: datetime` (Wann wurde die Pflanze dem Run zugeordnet)
    - `detached_at: Optional[datetime]` (Wann wurde die Pflanze abgetrennt; `null` = aktiv)
    - `detach_category: Optional[Literal['disease', 'pest', 'stunted', 'male_plant', 'selection', 'transplant', 'death', 'other']]` (Strukturierte Kategorie fuer Auswertung)
    - `detach_reason: Optional[str]` (Freitext-Details, z.B. "Braunfaeule an Staengelbasis")

**Run-Infrastruktur:**

- **`run_at_location`**: `PlantingRun → Location` (Multi-Edge moeglich: Anzuchtort → Endstandort)
  - Properties:
    - `assigned_at: datetime`
    - `removed_at: Optional[datetime]`
    - `location_role: Literal['propagation', 'final', 'temporary']`
    - `notes: Optional[str]`

- **`run_uses_substrate`**: `PlantingRun → SubstrateBatch`
  - Properties:
    - `assigned_at: datetime`
    - `volume_liters: Optional[float]` (Verbrauchte Menge)

- **`has_entry`**: `PlantingRun → PlantingRunEntry`
  - Properties: (keine)

- **`entry_for_species`**: `PlantingRunEntry → Species`
  - Properties: (keine)

- **`entry_for_cultivar`**: `PlantingRunEntry → Cultivar` (optional)
  - Properties: (keine)

**Run-Level-Management (Dual-Support: Run ODER standalone PlantInstance):**

Die folgenden Edges werden primaer auf PlantingRun angelegt. Fuer standalone PlantInstances (nicht in einem aktiven Run) werden dieselben Edge-Collections verwendet, aber mit `plant_instances` als Quell-Vertex.

- **`current_phase`**: `PlantingRun|PlantInstance → GrowthPhase` (REQ-003)
- **`phase_history`**: `PlantingRun|PlantInstance → PhaseHistory` (REQ-003)
- **`has_season`**: `PlantingRun|PlantInstance → SeasonalCycle` (REQ-003)
- **`has_task`**: `PlantingRun|PlantInstance → Task` (REQ-006)
- **`follows`**: `PlantingRun|PlantInstance → WorkflowTemplate` (REQ-006)
- **`executing`**: `PlantingRun|PlantInstance → WorkflowExecution` (REQ-006)
- **`has_care_profile`**: `PlantingRun|PlantInstance → CareProfile` (REQ-022)
- **`has_overwintering_profile`**: `PlantingRun|PlantInstance → OverwinteringProfile` (REQ-022)
- **`inspected_by`**: `PlantingRun|PlantInstance → Inspection` (REQ-010)
- **`observed_for_harvest`**: `PlantingRun|PlantInstance → HarvestObservation` (REQ-007)
- **`underwent_protocol`**: `PlantingRun|PlantInstance → PreHarvestProtocol` (REQ-007)

**Run-Level-Management (nur Run):**

- **`run_follows_plan`**: `PlantingRun → NutrientPlan` (REQ-004)
  - Properties: `assigned_at: datetime`, `assigned_by: str`
- **`run_produced`**: `PlantingRun → Batch` (REQ-007)
  - Properties: `harvested_at: datetime`, `plant_count: int`, `notes: Optional[str]`
- **`training_on`**: `TrainingEvent → PlantingRun` (REQ-006)
- **`has_canopy_measurement`**: `PlantingRun → CanopyMeasurement` (REQ-006)
- **`to_run`**: `TreatmentApplication → PlantingRun` (REQ-010, ex `to_plant`)
- **`notification_for_run`**: `Notification → PlantingRun` (REQ-030)

**Standalone-Management (nur PlantInstance):**

- **`follows_plan`**: `PlantInstance → NutrientPlan` (REQ-004, nur standalone)
- **`fed_by`**: `PlantingRun|PlantInstance → FeedingEvent` (REQ-004)

**Edges die immer auf PlantInstance bleiben (unabhaengig von Run):**

- **`placed_in`**: `PlantInstance → Slot` (Individuelle Slot-Zuweisung)
- **`succeeds`**: `PlantInstance → PlantInstance` (Crop Rotation per Beet-Position)
- **`descended_from`**: `PlantInstance → PlantInstance` (Genetische Linie, REQ-017)
- **`grafted_onto`**: `PlantInstance → PlantInstance` (Veredelung, REQ-017)
- **`has_phenotype`**: `PlantInstance → PhenotypeNote` (Phaenotyp, REQ-017)
- **`propagated_from`**: `PropagationEvent → PlantInstance` (Vermehrung, REQ-017)
- **`resulted_in`**: `PropagationEvent → PlantInstance` (Vermehrung, REQ-017)
- **`grown_in`**: `PlantInstance → SubstrateBatch` (Substrat, REQ-019)
- **`hermie_on_plant`**: `HermaphroditismFinding → PlantInstance` (IPM individual, REQ-010)
- **`pollination_affected`**: `PollinationCheck → PlantInstance` (IPM individual, REQ-010)
- **`has_diary_entry`**: `PlantInstance → PlantDiaryEntry` (Tagebuch)

**Sukzession:**

<!-- Quelle: Outdoor-Garden-Planner Review G-009 -->
- **`has_succession_plan`**: `SuccessionPlan → PlantingRun` (1:N, Plan generiert Runs)
- **`succession_at`**: `SuccessionPlan → Location` (N:1, Staffelanbau an Standort)

### AQL-Beispielqueries (ArangoDB 3.11+):

**1. PlantingRun mit Phase, Entries und Pflanzen laden:**
```aql
LET run = DOCUMENT("planting_runs", @run_key)

LET current_phase = FIRST(
    FOR phase IN 1..1 OUTBOUND run current_phase
    RETURN phase
)

LET entries = (
    FOR v, e IN 1..1 OUTBOUND run has_entry
    LET species = FIRST(FOR s IN 1..1 OUTBOUND v entry_for_species RETURN s)
    LET cultivar = FIRST(FOR c IN 1..1 OUTBOUND v entry_for_cultivar RETURN c)
    RETURN MERGE(v, {
        species_name: species.scientific_name,
        species_common_names: species.common_names,
        cultivar_name: cultivar.name
    })
)

LET plants = (
    FOR v, e IN 1..1 OUTBOUND run run_contains
    FILTER e.detached_at == null
    RETURN {
        plant: v,
        added_at: e.added_at
    }
)

LET location = FIRST(
    FOR v, e IN 1..1 OUTBOUND run run_at_location
    FILTER e.removed_at == null
    RETURN v
)

LET substrate = FIRST(
    FOR v, e IN 1..1 OUTBOUND run run_uses_substrate
    RETURN MERGE(v, { volume_used: e.volume_liters })
)

RETURN MERGE(run, {
    current_phase: current_phase,
    entries: entries,
    plants: plants,
    active_plant_count: LENGTH(plants),
    location: location,
    substrate: substrate
})
```

**2. Run-Level Phasenwechsel — Phase auf dem Run aktualisieren:**
```aql
// Atomarer Phasenwechsel: alte current_phase-Edge entfernen, neue setzen, PhaseHistory schreiben
LET run = DOCUMENT("planting_runs", @run_key)

// Alte Phase-Edge entfernen
LET old_edge = FIRST(
    FOR v, e IN 1..1 OUTBOUND run current_phase
    RETURN e
)
LET removed = old_edge != null ? (REMOVE old_edge._key IN current_phase RETURN OLD) : null

// Neue Phase-Edge setzen
INSERT { _from: run._id, _to: CONCAT("growth_phases/", @target_phase_key) }
INTO current_phase

// PhaseHistory schreiben (alte Phase abschliessen)
FOR h IN phase_history
    FILTER h._from == run._id AND h.exited_at == null
    UPDATE h WITH { exited_at: DATE_NOW(), actual_duration_days: DATE_DIFF(h.entered_at, DATE_NOW(), "day") }
    IN phase_history

// Neue PhaseHistory anlegen
INSERT { _from: run._id, _to: CONCAT("growth_phases/", @target_phase_key), entered_at: DATE_NOW(), exited_at: null }
INTO phase_history

// Run-Dokument aktualisieren
UPDATE run._key WITH {
    current_phase_key: @target_phase_key,
    current_phase_started_at: DATE_NOW(),
    updated_at: DATE_NOW()
} IN planting_runs
```

**3. Alle aktiven Runs an einem Standort mit Statistiken:**
```aql
FOR run IN planting_runs
    FILTER run.status IN ["active", "harvesting"]

    LET location = FIRST(
        FOR v IN 1..1 OUTBOUND run run_at_location
        RETURN v
    )
    FILTER location._key == @location_key

    LET active_count = LENGTH(
        FOR plant, e IN 1..1 OUTBOUND run run_contains
        FILTER e.detached_at == null AND plant.removed_on == null
        RETURN 1
    )
    LET detached_count = LENGTH(
        FOR plant, e IN 1..1 OUTBOUND run run_contains
        FILTER e.detached_at != null
        RETURN 1
    )

    LET current_phase = FIRST(
        FOR phase IN 1..1 OUTBOUND run current_phase
        RETURN phase.name
    )

    RETURN {
        run_key: run._key,
        run_name: run.name,
        run_type: run.run_type,
        status: run.status,
        current_phase: current_phase,
        planned_quantity: run.planned_quantity,
        active_plants: active_count,
        detached_plants: detached_count,
        started_at: run.started_at
    }
```

**4. Seed-to-Shelf Traceability — Rueckverfolgung von Batch zu Run:**
```aql
LET batch = DOCUMENT("batches", @batch_key)

LET source_run = FIRST(
    FOR run, e IN 1..1 INBOUND batch run_produced
    RETURN { run, harvested_at: e.harvested_at, plant_count: e.plant_count }
)

LET run_detail = source_run != null ? (
    LET entries = (
        FOR entry IN 1..1 OUTBOUND source_run.run has_entry
        LET species = FIRST(FOR s IN 1..1 OUTBOUND entry entry_for_species RETURN s)
        LET cultivar = FIRST(FOR c IN 1..1 OUTBOUND entry entry_for_cultivar RETURN c)
        RETURN {
            species: species.scientific_name,
            cultivar: cultivar.name,
            quantity: entry.quantity
        }
    )
    LET location = FIRST(FOR v IN 1..1 OUTBOUND source_run.run run_at_location RETURN v)
    LET substrate = FIRST(FOR v IN 1..1 OUTBOUND source_run.run run_uses_substrate RETURN v)

    RETURN {
        run_key: source_run.run._key,
        run_name: source_run.run.name,
        run_type: source_run.run.run_type,
        entries: entries,
        location_name: location.name,
        substrate_batch_id: substrate.batch_id,
        source_plant_key: source_run.run.source_plant_key,
        started_at: source_run.run.started_at,
        harvested_at: source_run.harvested_at
    }
) : null

RETURN {
    batch_id: batch.batch_id,
    harvest_date: batch.harvest_date,
    quality_grade: batch.quality_grade,
    wet_weight_g: batch.wet_weight_g,
    traceability: run_detail
}
```

**5. Tagebuch-Eintraege einer Pflanze im Run laden:**
```aql
LET plant = DOCUMENT("plant_instances", @plant_key)

// Sicherstellen, dass Pflanze zum Run gehoert
LET in_run = LENGTH(
    FOR run, e IN 1..1 INBOUND plant run_contains
    FILTER run._key == @run_key AND e.detached_at == null
    RETURN 1
) > 0

FILTER in_run

FOR entry, e IN 1..1 OUTBOUND plant has_diary_entry
    SORT entry.created_at DESC
    LIMIT @offset, @limit
    RETURN entry
```

**6. Aggregiertes Tagebuch aller Pflanzen im Run:**
```aql
LET run = DOCUMENT("planting_runs", @run_key)

FOR plant, rc_edge IN 1..1 OUTBOUND run run_contains
    FILTER rc_edge.detached_at == null

    FOR diary, de IN 1..1 OUTBOUND plant has_diary_entry
        SORT diary.created_at DESC
        LIMIT @offset, @limit
        RETURN {
            plant_key: plant._key,
            plant_id: plant.instance_id,
            plant_name: plant.plant_name,
            diary_entry: diary
        }
```

### Seed-Daten:

**Szenario 1 — Monokultur (Tomate San Marzano):**
```json
// planting_runs collection
{
    "_key": "tomaten_hochbeet_a_2025",
    "name": "Tomaten Hochbeet A 2025",
    "run_type": "monoculture",
    "status": "active",
    "planned_quantity": 20,
    "actual_quantity": 20,
    "current_phase_key": "vegetative",
    "current_phase_started_at": "2025-06-01T09:00:00Z",
    "planned_start_date": "2025-05-01",
    "started_at": "2025-05-03T09:00:00Z",
    "completed_at": null,
    "source_plant_key": null,
    "notes": "Erste Runde San Marzano fuer Passata-Produktion",
    "created_at": "2025-04-15T10:00:00Z",
    "updated_at": "2025-06-01T09:00:00Z"
}

// planting_run_entries collection
{
    "_key": "tomaten_hba_entry_01",
    "species_key": "solanum_lycopersicum",
    "cultivar_key": "san_marzano",
    "quantity": 20,
    "id_prefix": "TOM",
    "spacing_cm": 50,
    "notes": null
}

// has_entry edge
{ "_from": "planting_runs/tomaten_hochbeet_a_2025", "_to": "planting_run_entries/tomaten_hba_entry_01" }

// entry_for_species edge
{ "_from": "planting_run_entries/tomaten_hba_entry_01", "_to": "species/solanum_lycopersicum" }

// entry_for_cultivar edge
{ "_from": "planting_run_entries/tomaten_hba_entry_01", "_to": "cultivars/san_marzano" }

// run_at_location edge
{ "_from": "planting_runs/tomaten_hochbeet_a_2025", "_to": "locations/hochbeet_a", "assigned_at": "2025-05-03T09:00:00Z" }

// run_uses_substrate edge
{ "_from": "planting_runs/tomaten_hochbeet_a_2025", "_to": "substrate_batches/bio_erde_2025_03", "assigned_at": "2025-05-03T09:00:00Z", "volume_liters": 200 }

// current_phase edge (Run-Level!)
{ "_from": "planting_runs/tomaten_hochbeet_a_2025", "_to": "growth_phases/vegetative" }

// run_contains edges (Auszug)
{ "_from": "planting_runs/tomaten_hochbeet_a_2025", "_to": "plant_instances/HOCHBEETA_TOM_01", "added_at": "2025-05-03T09:00:00Z", "detached_at": null }
{ "_from": "planting_runs/tomaten_hochbeet_a_2025", "_to": "plant_instances/HOCHBEETA_TOM_02", "added_at": "2025-05-03T09:00:00Z", "detached_at": null }
// … bis HOCHBEETA_TOM_20
```

**Szenario 2 — Klone (Cannabis White Widow):**
```json
// planting_runs collection
{
    "_key": "ww_klone_runde3",
    "name": "White Widow Klone Runde 3",
    "run_type": "clone",
    "status": "active",
    "planned_quantity": 10,
    "actual_quantity": 10,
    "current_phase_key": "rooting",
    "current_phase_started_at": "2025-06-01T08:00:00Z",
    "planned_start_date": "2025-06-01",
    "started_at": "2025-06-01T08:00:00Z",
    "completed_at": null,
    "source_plant_key": "GROWZELT1_MOTHER_WW01",
    "notes": "Stecklinge von Mutterpflanze WW01, Bewurzelungsgel Clonex",
    "created_at": "2025-05-28T14:00:00Z",
    "updated_at": "2025-06-01T08:00:00Z"
}

// planting_run_entries collection
{
    "_key": "ww_klone_r3_entry_01",
    "species_key": "cannabis_sativa",
    "cultivar_key": "white_widow",
    "quantity": 10,
    "id_prefix": "WW3",
    "spacing_cm": 30,
    "notes": "Bewurzelungsgel: Clonex, Stecklinge 10–15 cm"
}

// has_entry edge
{ "_from": "planting_runs/ww_klone_runde3", "_to": "planting_run_entries/ww_klone_r3_entry_01" }

// current_phase edge (Run-Level!)
{ "_from": "planting_runs/ww_klone_runde3", "_to": "growth_phases/rooting" }

// run_contains edges (Auszug)
{ "_from": "planting_runs/ww_klone_runde3", "_to": "plant_instances/GROWZELT1_WW3_01", "added_at": "2025-06-01T08:00:00Z", "detached_at": null }
// … bis GROWZELT1_WW3_10
```

**Szenario 3 — Tagebuch-Eintraege:**
```json
// plant_diary_entries collection
{
    "_key": "diary_tom05_01",
    "entry_type": "problem",
    "title": "Braune Flecken an unteren Blaettern",
    "text": "Die unteren 3 Blaetter zeigen braune Flecken, moeglicherweise Septoria. Betroffene Blaetter entfernt.",
    "photo_refs": ["s3://kamerplanter/diary/tom05_01_a.jpg"],
    "tags": ["septoria", "blaetter", "krankheit"],
    "measurements": null,
    "created_by": "user_max",
    "created_at": "2025-07-15T14:30:00Z",
    "updated_at": "2025-07-15T14:30:00Z"
}

{
    "_key": "diary_tom05_02",
    "entry_type": "measurement",
    "title": "Woechentliche Messung",
    "text": "Pflanze hat sich nach Blattentfernung gut erholt.",
    "photo_refs": [],
    "tags": ["messung", "wachstum"],
    "measurements": {"height_cm": 85, "branch_count": 6, "stem_diameter_mm": 12},
    "created_by": "user_max",
    "created_at": "2025-07-22T10:00:00Z",
    "updated_at": "2025-07-22T10:00:00Z"
}

// has_diary_entry edges
{ "_from": "plant_instances/HOCHBEETA_TOM_05", "_to": "plant_diary_entries/diary_tom05_01" }
{ "_from": "plant_instances/HOCHBEETA_TOM_05", "_to": "plant_diary_entries/diary_tom05_02" }
```

## 3. Technische Umsetzung (Python)

### Enumerationen:

```python
from enum import StrEnum

class PlantingRunType(StrEnum):
    """Typ des Pflanzdurchlaufs"""
    MONOCULTURE = "monoculture"      # Eine Art, eine Sorte
    CLONE = "clone"                  # Stecklinge von einer Mutterpflanze

class PlantingRunStatus(StrEnum):
    """Status-State-Machine fuer Pflanzdurchlaeufe"""
    PLANNED = "planned"        # Geplant, noch nicht gestartet
    ACTIVE = "active"          # Pflanzen angelegt, Durchlauf laeuft
    HARVESTING = "harvesting"  # Erntephase (teil- oder komplett)
    COMPLETED = "completed"    # Abgeschlossen (alle Pflanzen entfernt/geerntet)
    CANCELLED = "cancelled"    # Abgebrochen (vor oder waehrend Durchlauf)

class DiaryEntryType(StrEnum):
    """Typ eines Tagebuch-Eintrags"""
    OBSERVATION = "observation"    # Allgemeine Beobachtung
    PROBLEM = "problem"            # Problem/Krankheit/Schaedling
    MILESTONE = "milestone"        # Meilenstein (erste Bluete, erste Frucht etc.)
    MEASUREMENT = "measurement"    # Strukturierte Messung
    PHOTO = "photo"                # Foto-Dokumentation
    NOTE = "note"                  # Freitext-Notiz
```

### Status-Transitions:

```python
ALLOWED_STATUS_TRANSITIONS: dict[PlantingRunStatus, list[PlantingRunStatus]] = {
    PlantingRunStatus.PLANNED: [
        PlantingRunStatus.ACTIVE,
        PlantingRunStatus.CANCELLED,
    ],
    PlantingRunStatus.ACTIVE: [
        PlantingRunStatus.HARVESTING,
        PlantingRunStatus.COMPLETED,
        PlantingRunStatus.CANCELLED,
    ],
    PlantingRunStatus.HARVESTING: [
        PlantingRunStatus.COMPLETED,
        PlantingRunStatus.CANCELLED,
    ],
    PlantingRunStatus.COMPLETED: [],   # Terminal
    PlantingRunStatus.CANCELLED: [],   # Terminal
}
```

### Pydantic-Modelle:

**1. PlantingRunEntry-Model:**
```python
from typing import Optional
from pydantic import BaseModel, Field

class PlantingRunEntryCreate(BaseModel):
    """Erstellt einen Eintrag fuer die Artenzusammensetzung"""

    species_key: str = Field(description="Key der Species in ArangoDB")
    cultivar_key: Optional[str] = Field(None, description="Key der Cultivar (optional)")
    quantity: int = Field(ge=1, le=1000, description="Geplante Anzahl Pflanzen fuer diese Art")
    id_prefix: Optional[str] = Field(
        None,
        max_length=5,
        pattern=r'^[A-Z]{2,5}$',
        description="Praefix fuer auto-generierte Pflanzen-IDs (z.B. 'TOM', 'WW3')"
    )
    spacing_cm: Optional[int] = Field(None, ge=5, le=300, description="Empfohlener Pflanzabstand in cm")
    notes: Optional[str] = Field(None, max_length=500)
```

**2. PlantingRun-Models:**
```python
from datetime import date, datetime
from typing import Optional

class PlantingRunCreate(BaseModel):
    """Erstellt einen neuen Pflanzdurchlauf"""

    name: str = Field(min_length=1, max_length=200, description="Benutzerfreundlicher Name")
    run_type: PlantingRunType
    planned_quantity: int = Field(ge=1, le=10000, description="Geplante Gesamtanzahl Pflanzen")
    planned_start_date: Optional[date] = Field(None, description="Geplantes Startdatum")
    source_plant_key: Optional[str] = Field(
        None, description="Mutterpflanze (nur bei clone-Typ)"
    )
    clone_generation: Optional[int] = Field(
        None, ge=1, le=50,
        description="Klon-Generation (1 = direkt von Saat-Pflanze, 2+ = Klon vom Klon)"
    )
    propagation_method: Optional[str] = Field(
        None,
        description="Vermehrungsmethode: 'seed', 'cutting', 'tissue_culture', 'air_layer', 'division'"
    )
    clone_from_run_key: Optional[str] = Field(
        None,
        description="Key eines bestehenden Runs als Vorlage (Staffelanbau/Succession Planting)"
    )
    location_key: Optional[str] = Field(None, description="Standort-Zuordnung")
    substrate_batch_key: Optional[str] = Field(None, description="Substrat-Charge")
    substrate_volume_liters: Optional[float] = Field(None, gt=0, description="Verbrauchte Substrat-Menge")
    entries: list[PlantingRunEntryCreate] = Field(min_length=1, max_length=1)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_run_type_constraints(self):
        """Validiert Typ-spezifische Constraints"""

        if self.run_type == PlantingRunType.CLONE:
            if not self.source_plant_key:
                raise ValueError(
                    "source_plant_key ist erforderlich fuer Clone-Durchlaeufe"
                )

        if len(self.entries) != 1:
            raise ValueError(
                f"{self.run_type}-Durchlaeufe erlauben genau 1 Entry, "
                f"erhalten: {len(self.entries)}"
            )

        # Quantity-Konsistenz
        total_entry_quantity = sum(e.quantity for e in self.entries)
        if total_entry_quantity != self.planned_quantity:
            raise ValueError(
                f"Summe der Entry-Quantities ({total_entry_quantity}) "
                f"muss planned_quantity ({self.planned_quantity}) entsprechen"
            )

        return self

class PlantingRunUpdate(BaseModel):
    """Aktualisiert einen bestehenden Pflanzdurchlauf"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    planned_start_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2000)

class PlantingRunResponse(BaseModel):
    """Antwort-Schema fuer einen Pflanzdurchlauf"""

    key: str
    name: str
    run_type: PlantingRunType
    status: PlantingRunStatus
    planned_quantity: int
    actual_quantity: int
    current_phase_key: Optional[str]
    current_phase_started_at: Optional[datetime]
    planned_start_date: Optional[date]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    source_plant_key: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
```

**3. Batch-Operation-Models:**
```python
class BatchCreatePlantsRequest(BaseModel):
    """Erstellt N Pflanzen fuer einen PlantingRun"""

    assign_to_slots: bool = Field(
        default=False,
        description="Automatisch freie Slots am Standort zuweisen"
    )
    planted_on: Optional[date] = Field(
        None,
        description="Pflanzdatum (Default: heute)"
    )

class BatchCreatePlantsResponse(BaseModel):
    """Ergebnis der Batch-Pflanzen-Erstellung"""

    run_key: str
    created_count: int
    plant_keys: list[str]
    assigned_slots: Optional[list[str]]
    warnings: list[str]

class AdoptPlantsRequest(BaseModel):
    """Nimmt bestehende standalone PlantInstances in den Run auf.

    Validierung:
    - Jede Pflanze darf nicht bereits in einem aktiven Run sein
    - Jede Pflanze darf nicht removed sein (removed_on == null)
    - Species der Pflanze muss zum Entry des Runs passen (Monokultur/Clone)
    - Run muss Status 'planned' oder 'active' haben
    """

    plant_keys: list[str] = Field(
        min_length=1,
        description="Keys der bestehenden PlantInstances die aufgenommen werden sollen"
    )

class AdoptPlantsResponse(BaseModel):
    """Ergebnis der Adopt-Operation"""

    run_key: str
    adopted_count: int
    adopted_keys: list[str]
    skipped: list[dict]  # [{ plant_key, reason }]
    run_status: str
    run_phase: Optional[str]

class RunTransitionRequest(BaseModel):
    """Run-Level Phasenwechsel — alle Pflanzen im Run wechseln gemeinsam.

    Kein exclude, kein per-Plant-Filter: der Run ist die Verwaltungseinheit.
    """

    target_phase_key: str = Field(description="Ziel-Phase Key (z.B. 'flowering')")
    target_phase_name: Optional[str] = Field(None, description="Ziel-Phase Name (fuer Anzeige)")
    override_reason: Optional[str] = Field(
        None,
        description="Grund fuer manuellen Override (ueberspringt Regel-Pruefung)"
    )

class RunTransitionResponse(BaseModel):
    """Ergebnis des Run-Level Phasenwechsels"""

    run_key: str
    previous_phase: Optional[str]
    new_phase: str
    transitioned_at: datetime

class BatchHarvestRequest(BaseModel):
    """Erstellt einen HarvestBatch aus einem PlantingRun"""

    harvest_type: str = Field(
        description="Ernte-Typ: 'partial' | 'final'"
    )
    wet_weight_g: float = Field(gt=0)
    per_plant_weights_g: Optional[dict[str, float]] = Field(
        None,
        description="Optionale Einzelgewichte pro Pflanze (plant_key → Gewicht in g). "
                    "Fuer Selektionsdaten und Ertragsverteilungs-Analyse."
    )
    quality_grade: Optional[str] = Field(
        None,
        pattern=r'^(A\+|A|B|C|D)$',
        description="Qualitaetsstufe"
    )
    harvester: str = Field(description="User-ID des Erntenden")
    weather_conditions: Optional[str] = None
    notes: Optional[str] = None

class BatchHarvestResponse(BaseModel):
    """Ergebnis der Batch-Ernte"""

    run_key: str
    batch_key: str
    batch_id: str
    harvested_plant_count: int
    wet_weight_g: float
    quality_grade: Optional[str]
    yield_statistics: Optional[dict] = Field(
        None,
        description="Ertragsverteilung wenn per_plant_weights angegeben: "
                    "{avg_g, min_g, max_g, median_g, stddev_g}"
    )
    run_status_after: PlantingRunStatus

class BatchRemoveRequest(BaseModel):
    """Entfernt alle Pflanzen aus dem Run und schliesst ihn ab"""

    reason: str = Field(
        min_length=1,
        description="Grund fuer die Entfernung (z.B. 'Saisonende', 'Krankheit')"
    )
    removed_on: Optional[date] = Field(
        None,
        description="Entfernungsdatum (Default: heute)"
    )

class BatchRemoveResponse(BaseModel):
    """Ergebnis der Batch-Entfernung"""

    run_key: str
    removed_count: int
    already_removed_count: int
    run_status_after: PlantingRunStatus

class DetachPlantRequest(BaseModel):
    """Trennt eine einzelne Pflanze vom Run ab.

    Die Pflanze erhaelt die aktuelle Phase des Runs kopiert und wird
    zur eigenstaendigen PlantInstance mit vollem Management.
    """

    category: str = Field(
        description="Strukturierte Detach-Kategorie: 'disease', 'pest', 'stunted', "
                    "'male_plant', 'selection', 'transplant', 'death', 'other'"
    )
    reason: str = Field(
        min_length=1,
        description="Freitext-Details zum Abtrennen (z.B. 'Braunfaeule am Staengel')"
    )
```

**4. Tagebuch-Models:**
```python
class PlantDiaryEntryCreate(BaseModel):
    """Erstellt einen Tagebuch-Eintrag fuer eine Pflanze"""

    entry_type: DiaryEntryType
    title: Optional[str] = Field(None, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    photo_refs: list[str] = Field(default_factory=list, max_length=5)
    tags: list[str] = Field(default_factory=list, max_length=20)
    measurements: Optional[dict] = Field(
        None,
        description="Strukturierte Messwerte: height_cm, leaf_count, branch_count, "
                    "stem_diameter_mm, canopy_width_cm etc."
    )

class PlantDiaryEntryUpdate(BaseModel):
    """Aktualisiert einen Tagebuch-Eintrag"""

    entry_type: Optional[DiaryEntryType] = None
    title: Optional[str] = Field(None, max_length=200)
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    photo_refs: Optional[list[str]] = Field(None, max_length=5)
    tags: Optional[list[str]] = Field(None, max_length=20)
    measurements: Optional[dict] = None

class PlantDiaryEntryResponse(BaseModel):
    """Antwort-Schema fuer einen Tagebuch-Eintrag"""

    key: str
    entry_type: DiaryEntryType
    title: Optional[str]
    text: str
    photo_refs: list[str]
    tags: list[str]
    measurements: Optional[dict]
    created_by: str
    created_at: datetime
    updated_at: datetime
```

### Engine-Logik:

**1. PlantingRunEngine — Batch-Erstellung:**
```python
from datetime import date, datetime
from typing import Optional

class PlantingRunEngine:
    """Kernlogik fuer Pflanzdurchlauf-Operationen"""

    @staticmethod
    def generate_plant_ids(
        location_key: str,
        entries: list[dict],
        existing_ids: set[str]
    ) -> list[dict]:
        """
        Generiert eindeutige Pflanzen-IDs basierend auf Location und Entry-Praefix.

        Format: {LOCATION}_{PREFIX}_{SEQ:02d}
        Beispiel: HOCHBEETA_TOM_01, HOCHBEETA_TOM_02, ...
        """
        result = []
        location_prefix = location_key.upper()

        for entry in entries:
            prefix = entry.get('id_prefix') or entry['species_key'][:3].upper()
            seq = 1

            for _ in range(entry['quantity']):
                while True:
                    instance_id = f"{location_prefix}_{prefix}_{seq:02d}"
                    if instance_id not in existing_ids:
                        break
                    seq += 1

                result.append({
                    'entry_key': entry['_key'],
                    'instance_id': instance_id,
                    'species_key': entry['species_key'],
                    'cultivar_key': entry.get('cultivar_key'),
                })
                existing_ids.add(instance_id)
                seq += 1

        return result

    @staticmethod
    def validate_status_transition(
        current: PlantingRunStatus,
        target: PlantingRunStatus
    ) -> None:
        """Prueft ob ein Status-Uebergang erlaubt ist"""
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise ValueError(
                f"Ungueltiger Status-Uebergang: {current} → {target}. "
                f"Erlaubt: {', '.join(str(s) for s in allowed) or 'keine (Terminal-Status)'}"
            )

    @staticmethod
    def calculate_batch_id(run_key: str, harvest_date: date, seq: int = 1) -> str:
        """
        Generiert eine Batch-ID fuer die Ernte.
        Format: RUN_{RUN_KEY}_{YYYYMMDD}_{SEQ}
        """
        return f"RUN_{run_key.upper()}_{harvest_date.strftime('%Y%m%d')}_{seq:02d}"
```

### Detach-Logik:

```python
class PlantingRunService:
    """Auszug: Detach-Logik mit Phase-Kopie"""

    async def detach_plant(
        self,
        run_key: str,
        plant_key: str,
        category: str,
        reason: str,
    ) -> None:
        """
        Trennt eine Pflanze vom Run ab und macht sie standalone.

        1. Setzt detached_at/detach_category/detach_reason auf run_contains-Edge
        2. Kopiert die aktuelle Run-Phase auf die PlantInstance:
           - plant.current_phase_key = run.current_phase_key
           - plant.current_phase_started_at = run.current_phase_started_at
        3. Erzeugt eine eigene current_phase-Edge fuer die PlantInstance
        4. Kopiert die offene PhaseHistory vom Run auf die PlantInstance
        5. Ab sofort ist die Pflanze eigenstaendig verwaltbar
        """
        run = await self.run_repo.get(run_key)
        plant = await self.plant_repo.get(plant_key)

        # 1. Edge aktualisieren
        await self.run_repo.update_run_contains_edge(
            run_key=run_key,
            plant_key=plant_key,
            detached_at=datetime.utcnow(),
            detach_category=category,
            detach_reason=reason,
        )

        # 2. Phase auf Plant kopieren
        if run.current_phase_key:
            plant.current_phase_key = run.current_phase_key
            plant.current_phase_started_at = run.current_phase_started_at
            await self.plant_repo.update(plant_key, plant)

            # 3. Eigene current_phase-Edge erzeugen
            await self.phase_repo.create_current_phase_edge(
                entity_id=f"plant_instances/{plant_key}",
                phase_key=run.current_phase_key,
            )

            # 4. Offene PhaseHistory kopieren
            await self.phase_repo.copy_open_phase_history(
                source_id=f"planting_runs/{run_key}",
                target_id=f"plant_instances/{plant_key}",
            )
```

### Datenvalidierung:

```python
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime

class PlantingRunDocument(BaseModel):
    """ArangoDB-Dokument-Schema fuer PlantingRun"""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    run_type: PlantingRunType
    status: PlantingRunStatus = PlantingRunStatus.PLANNED
    planned_quantity: int = Field(ge=1, le=10000)
    actual_quantity: int = Field(default=0, ge=0)
    current_phase_key: Optional[str] = None
    current_phase_started_at: Optional[datetime] = None
    lifecycle_config_key: Optional[str] = None
    planned_start_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    source_plant_key: Optional[str] = None
    clone_generation: Optional[int] = Field(None, ge=1, le=50)
    propagation_method: Optional[str] = None
    clone_from_run_key: Optional[str] = None
    germination_count: Optional[int] = Field(None, ge=0)
    rooting_count: Optional[int] = Field(None, ge=0)
    survival_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    primary_loss_reason: Optional[str] = Field(None, max_length=200)
    nutrient_plan_key: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode='after')
    def validate_clone_source(self):
        if self.run_type == PlantingRunType.CLONE and not self.source_plant_key:
            raise ValueError("Clone-Durchlaeufe erfordern source_plant_key")
        if self.run_type != PlantingRunType.CLONE and self.source_plant_key:
            raise ValueError("source_plant_key nur bei Clone-Durchlaeufen erlaubt")
        return self

    @model_validator(mode='after')
    def validate_status_dates(self):
        if self.status == PlantingRunStatus.ACTIVE and not self.started_at:
            raise ValueError("Aktive Durchlaeufe erfordern started_at")
        if self.status in (PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED):
            if not self.completed_at:
                raise ValueError(f"Status '{self.status}' erfordert completed_at")
        return self


class PlantingRunEntryDocument(BaseModel):
    """ArangoDB-Dokument-Schema fuer PlantingRunEntry"""

    key: Optional[str] = Field(None, alias='_key')
    species_key: str
    cultivar_key: Optional[str] = None
    quantity: int = Field(ge=1, le=1000)
    id_prefix: Optional[str] = Field(None, max_length=5, pattern=r'^[A-Z]{2,5}$')
    spacing_cm: Optional[int] = Field(None, ge=5, le=300)
    notes: Optional[str] = Field(None, max_length=500)


DetachCategory = Literal[
    'disease', 'pest', 'stunted', 'male_plant',
    'selection', 'transplant', 'death', 'other'
]

class RunContainsEdge(BaseModel):
    """ArangoDB-Edge-Schema fuer run_contains"""

    from_id: str = Field(alias='_from')
    to_id: str = Field(alias='_to')
    added_at: datetime = Field(default_factory=datetime.utcnow)
    detached_at: Optional[datetime] = None
    detach_category: Optional[DetachCategory] = None
    detach_reason: Optional[str] = Field(None, max_length=200)

    @model_validator(mode='after')
    def validate_detach(self):
        if self.detached_at and not self.detach_category:
            raise ValueError("detach_category erforderlich wenn detached_at gesetzt")
        if self.detached_at and not self.detach_reason:
            raise ValueError("detach_reason erforderlich wenn detached_at gesetzt")
        return self


class PlantDiaryEntryDocument(BaseModel):
    """ArangoDB-Dokument-Schema fuer PlantDiaryEntry"""

    key: Optional[str] = Field(None, alias='_key')
    entry_type: DiaryEntryType
    title: Optional[str] = Field(None, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    photo_refs: list[str] = Field(default_factory=list, max_length=5)
    tags: list[str] = Field(default_factory=list, max_length=20)
    measurements: Optional[dict] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

## 4. API-Endpunkte

### 4.1 CRUD — Pflanzdurchlaeufe (5 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/planting-runs` | Alle Durchlaeufe auflisten (Filter: status, run_type, location_key) | Mitglied |
| `POST` | `/api/v1/planting-runs` | Neuen Durchlauf anlegen (inkl. Entry) | Mitglied |
| `GET` | `/api/v1/planting-runs/{key}` | Einzelnen Durchlauf mit Entry, Pflanzen, Phase, Standort laden | Mitglied |
| `PUT` | `/api/v1/planting-runs/{key}` | Durchlauf-Metadaten aktualisieren (Name, Notizen, Startdatum) | Mitglied |
| `DELETE` | `/api/v1/planting-runs/{key}` | Durchlauf loeschen (nur Status `planned`, sonst 409 Conflict) | Admin |

### 4.2 Entries — Artenzusammensetzung (4 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/planting-runs/{key}/entries` | Alle Entries eines Durchlaufs | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/entries` | Entry hinzufuegen (nur Status `planned`) | Mitglied |
| `PUT` | `/api/v1/planting-runs/{key}/entries/{entry_key}` | Entry aktualisieren (nur Status `planned`) | Mitglied |
| `DELETE` | `/api/v1/planting-runs/{key}/entries/{entry_key}` | Entry entfernen (nur Status `planned`, Constraint-Pruefung) | Mitglied |

### 4.3 Run-Operationen (5 Endpunkte)

| Methode | Pfad | Beschreibung | Request-Body | Auth |
|---------|------|-------------|-------------|------|
| `POST` | `/api/v1/planting-runs/{key}/create-plants` | N Pflanzen aus Entry erzeugen, Run → active | `BatchCreatePlantsRequest` | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/adopt-plants` | Bestehende standalone PlantInstances dem Run zuordnen | `AdoptPlantsRequest` | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/transition` | **Run-Level Phasenwechsel** (alle Pflanzen im Run) | `RunTransitionRequest` | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/batch-harvest` | HarvestBatch erstellen | `BatchHarvestRequest` | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/batch-remove` | Alle Pflanzen entfernen, Run abschliessen | `BatchRemoveRequest` | Mitglied |

### 4.4 Pflanzen im Run (2 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/planting-runs/{key}/plants` | Alle Pflanzen im Run (Filter: detached=true/false) | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/plants/{plant_key}/detach` | Pflanze abtrennen → wird standalone mit Phase-Kopie | Mitglied |

### 4.5 Naehrstoffplan-Zuweisung (3 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/api/v1/planting-runs/{key}/nutrient-plan` | NutrientPlan dem Run zuweisen (erzeugt `RUN_FOLLOWS_PLAN`-Edge) | Mitglied |
| `GET` | `/api/v1/planting-runs/{key}/nutrient-plan` | Zugewiesenen NutrientPlan abrufen (inkl. WateringSchedule) | Mitglied |
| `DELETE` | `/api/v1/planting-runs/{key}/nutrient-plan` | NutrientPlan-Zuweisung entfernen | Mitglied |

### 4.6 Giesskalender (1 Endpunkt)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/planting-runs/{key}/watering-schedule` | Aufgeloester Giesskalender: naechste 14 Tage mit Dosierungen | Mitglied |

### 4.7 Pflanzen-Tagebuch (7 Endpunkte)

**Im Run-Kontext:**

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/planting-runs/{key}/plants/{plant_key}/diary` | Tagebuch einer Pflanze im Run | Mitglied |
| `POST` | `/api/v1/planting-runs/{key}/plants/{plant_key}/diary` | Tagebuch-Eintrag erstellen | Mitglied |
| `GET` | `/api/v1/planting-runs/{key}/plants/{plant_key}/diary/{entry_key}` | Einzelner Eintrag | Mitglied |
| `PUT` | `/api/v1/planting-runs/{key}/plants/{plant_key}/diary/{entry_key}` | Eintrag aktualisieren | Mitglied |
| `DELETE` | `/api/v1/planting-runs/{key}/plants/{plant_key}/diary/{entry_key}` | Eintrag loeschen | Mitglied |
| `GET` | `/api/v1/planting-runs/{key}/diary` | Aggregiertes Tagebuch aller Pflanzen im Run | Mitglied |

**Im Standalone-Kontext:**

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/plant-instances/{key}/diary` | Tagebuch einer standalone Pflanze | Mitglied |
| `POST` | `/api/v1/plant-instances/{key}/diary` | Eintrag erstellen | Mitglied |
| `GET` | `/api/v1/plant-instances/{key}/diary/{entry_key}` | Einzelner Eintrag | Mitglied |
| `PUT` | `/api/v1/plant-instances/{key}/diary/{entry_key}` | Eintrag aktualisieren | Mitglied |
| `DELETE` | `/api/v1/plant-instances/{key}/diary/{entry_key}` | Eintrag loeschen | Mitglied |

### Request/Response-Beispiele:

**POST `/api/v1/planting-runs` — Monokultur anlegen:**
```json
// Request
{
    "name": "Tomaten Hochbeet A 2025",
    "run_type": "monoculture",
    "planned_quantity": 20,
    "planned_start_date": "2025-05-01",
    "location_key": "hochbeet_a",
    "substrate_batch_key": "bio_erde_2025_03",
    "substrate_volume_liters": 200,
    "entries": [
        {
            "species_key": "solanum_lycopersicum",
            "cultivar_key": "san_marzano",
            "quantity": 20,
            "id_prefix": "TOM",
            "spacing_cm": 50
        }
    ],
    "notes": "Erste Runde San Marzano fuer Passata-Produktion"
}

// Response (201 Created)
{
    "key": "tomaten_hochbeet_a_2025",
    "name": "Tomaten Hochbeet A 2025",
    "run_type": "monoculture",
    "status": "planned",
    "planned_quantity": 20,
    "actual_quantity": 0,
    "current_phase_key": null,
    "current_phase_started_at": null,
    "planned_start_date": "2025-05-01",
    "started_at": null,
    "completed_at": null,
    "source_plant_key": null,
    "notes": "Erste Runde San Marzano fuer Passata-Produktion",
    "created_at": "2025-04-15T10:00:00Z",
    "updated_at": "2025-04-15T10:00:00Z"
}
```

**POST `/api/v1/planting-runs/{key}/create-plants` — Batch-Erstellung:**
```json
// Request
{
    "assign_to_slots": true,
    "planted_on": "2025-05-03"
}

// Response (201 Created)
{
    "run_key": "tomaten_hochbeet_a_2025",
    "created_count": 20,
    "plant_keys": [
        "HOCHBEETA_TOM_01", "HOCHBEETA_TOM_02", "...",
        "HOCHBEETA_TOM_20"
    ],
    "assigned_slots": [
        "HOCHBEETA_1", "HOCHBEETA_2", "...",
        "HOCHBEETA_20"
    ],
    "warnings": []
}
```
**Hinweis:** `create-plants` setzt den Run-Status auf `active` und die initiale Phase auf dem Run (aus Lifecycle-Config der Species). Es werden KEINE per-Plant Phase-Edges erzeugt — die Phase lebt auf dem Run.

**POST `/api/v1/planting-runs/{key}/transition` — Run-Level Phasenwechsel:**
```json
// Request
{
    "target_phase_key": "flowering",
    "target_phase_name": "Bluete"
}

// Response (200 OK)
{
    "run_key": "tomaten_hochbeet_a_2025",
    "previous_phase": "vegetative",
    "new_phase": "flowering",
    "transitioned_at": "2025-07-15T09:00:00Z"
}
```
**Hinweis:** Alle Pflanzen im Run teilen diese Phase. Kein exclude, kein per-Plant-Filter.

**POST `/api/v1/planting-runs/{key}/plants/{plant_key}/detach` — Pflanze abtrennen:**
```json
// Request
{
    "category": "disease",
    "reason": "Braunfaeule-Verdacht, zur separaten Behandlung"
}

// Response (200 OK)
{
    "plant_key": "HOCHBEETA_TOM_05",
    "detached_from_run": "tomaten_hochbeet_a_2025",
    "copied_phase": "vegetative",
    "standalone": true,
    "message": "Pflanze ist jetzt eigenstaendig verwaltbar"
}
```

**POST `/api/v1/planting-runs/{key}/plants/{plant_key}/diary` — Tagebuch-Eintrag:**
```json
// Request
{
    "entry_type": "problem",
    "title": "Braune Flecken an unteren Blaettern",
    "text": "Die unteren 3 Blaetter zeigen braune Flecken, moeglicherweise Septoria. Betroffene Blaetter entfernt.",
    "photo_refs": ["s3://kamerplanter/diary/tom05_01_a.jpg"],
    "tags": ["septoria", "blaetter", "krankheit"]
}

// Response (201 Created)
{
    "key": "diary_tom05_01",
    "entry_type": "problem",
    "title": "Braune Flecken an unteren Blaettern",
    "text": "Die unteren 3 Blaetter zeigen braune Flecken...",
    "photo_refs": ["s3://kamerplanter/diary/tom05_01_a.jpg"],
    "tags": ["septoria", "blaetter", "krankheit"],
    "measurements": null,
    "created_by": "user_max",
    "created_at": "2025-07-15T14:30:00Z",
    "updated_at": "2025-07-15T14:30:00Z"
}
```

### Fehlerbehandlung (NFR-006):

| HTTP-Status | Fehlerfall | Beispiel |
|-------------|-----------|---------|
| `400` | Validierungsfehler | Entry-Quantity stimmt nicht mit planned_quantity ueberein |
| `404` | Run/Entry/Plant nicht gefunden | Unbekannter run_key |
| `409` | Konfliktzustand | DELETE auf aktiven Run; Pflanze gehoert bereits zu anderem Run |
| `422` | Geschaeftslogik-Fehler | Clone-Run ohne source_plant_key; Transition auf Terminal-Status |

## 5. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt dokumentiert die Auth-Anforderungen
> gemaess REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung).

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Loeschen |
|---------------------------|-------|-----------|---------|
| PlantingRuns | Mitglied | Mitglied | Admin |
| PlantingRun-Eintraege | Mitglied | Mitglied | Mitglied |
| Run-Operationen | — | Mitglied | — |
| Pflanzen-Tagebuch | Mitglied | Mitglied | Mitglied |

## 6. Abhaengigkeiten

### Erforderliche Module:

| Modul | Abhaengigkeit | Prioritaet |
|-------|-------------|-----------|
| **REQ-001** (Stammdaten) | Species, Cultivar fuer Entry-Zuordnung | **HOCH** |
| **REQ-002** (Standort/Substrat) | Location fuer `run_at_location`; SubstrateBatch fuer `run_uses_substrate`; Slot fuer Pflanzen-Platzierung | **HOCH** |
| **REQ-003** (Phasensteuerung) | GrowthPhase, PhaseTransitionRule fuer Run-Level Phasenwechsel; `current_phase`-Edge (Dual-Support) | **HOCH** |
| **REQ-004** (Duenge-Logik) | NutrientPlan fuer `run_follows_plan`; WateringSchedule fuer Giesskalender | **HOCH** |

### Wird benoetigt von:

| Modul | Nutzung | Prioritaet |
|-------|---------|-----------|
| **REQ-006** (Aufgabenplanung) | Run-basierte Task-Generierung; `has_task`-Edge (Dual-Support) | **HOCH** |
| **REQ-007** (Erntemanagement) | `run_produced`-Edge fuer Batch-Ernte; Seed-to-Shelf-Traceability | **HOCH** |
| **REQ-009** (Dashboard) | Run-Uebersicht als Dashboard-Widget | **MITTEL** |
| **REQ-010** (IPM) | Run-weite IPM-Inspektionen; `inspected_by`-Edge (Dual-Support) | **NIEDRIG** |
| **REQ-014** (Tankmanagement) | Giessplan-Bestaetigungsflow nutzt Run + NutrientPlan | **HOCH** |
| **REQ-022** (Pflegeerinnerungen) | `has_care_profile`-Edge (Dual-Support) | **MITTEL** |
| **REQ-028** (Mischkultur) | Companion-Beziehungen ueber Standort-Graph (keine gemeinsamen Runs) | **NIEDRIG** |

### Grapherweiterungen am Named Graph `kamerplanter_graph`:

```json
{
    "new_document_collections": ["planting_runs", "planting_run_entries", "succession_plans", "plant_diary_entries"],
    "new_edge_collections": [
        {
            "name": "run_contains",
            "from": ["planting_runs"],
            "to": ["plant_instances"]
        },
        {
            "name": "run_at_location",
            "from": ["planting_runs"],
            "to": ["locations"]
        },
        {
            "name": "run_uses_substrate",
            "from": ["planting_runs"],
            "to": ["substrate_batches"]
        },
        {
            "name": "run_produced",
            "from": ["planting_runs"],
            "to": ["batches"]
        },
        {
            "name": "has_entry",
            "from": ["planting_runs"],
            "to": ["planting_run_entries"]
        },
        {
            "name": "entry_for_species",
            "from": ["planting_run_entries"],
            "to": ["species"]
        },
        {
            "name": "entry_for_cultivar",
            "from": ["planting_run_entries"],
            "to": ["cultivars"]
        },
        {
            "name": "run_follows_plan",
            "from": ["planting_runs"],
            "to": ["nutrient_plans"],
            "note": "NutrientPlan-Zuweisung auf Run-Ebene (REQ-004)"
        },
        {
            "name": "has_diary_entry",
            "from": ["plant_instances"],
            "to": ["plant_diary_entries"]
        },
        {
            "name": "has_succession_plan",
            "from": ["succession_plans"],
            "to": ["planting_runs"],
            "note": "Sukzessions-Plan generiert PlantingRuns"
        },
        {
            "name": "succession_at",
            "from": ["succession_plans"],
            "to": ["locations"],
            "note": "Staffelanbau an Standort"
        },
        {
            "name": "to_run",
            "from": ["treatment_applications"],
            "to": ["planting_runs"],
            "note": "IPM-Behandlungen auf Run-Ebene (REQ-010)"
        },
        {
            "name": "notification_for_run",
            "from": ["notifications"],
            "to": ["planting_runs"],
            "note": "Benachrichtigungen fuer Runs (REQ-030)"
        }
    ],
    "dual_support_edges": [
        {
            "name": "current_phase",
            "from": ["planting_runs", "plant_instances"],
            "to": ["growth_phases"],
            "note": "Run-Level primaer, PlantInstance nur standalone"
        },
        {
            "name": "phase_history",
            "from": ["planting_runs", "plant_instances"],
            "to": ["phase_histories"],
            "note": "Run-Level primaer, PlantInstance nur standalone"
        },
        {
            "name": "has_task",
            "from": ["planting_runs", "plant_instances"],
            "to": ["tasks"],
            "note": "Run-Level primaer, PlantInstance nur standalone"
        },
        {
            "name": "has_care_profile",
            "from": ["planting_runs", "plant_instances"],
            "to": ["care_profiles"],
            "note": "Run-Level primaer, PlantInstance nur standalone"
        },
        {
            "name": "inspected_by",
            "from": ["planting_runs", "plant_instances"],
            "to": ["inspections"],
            "note": "Run-Level primaer, PlantInstance nur standalone"
        },
        {
            "name": "fed_by",
            "from": ["planting_runs", "plant_instances"],
            "to": ["feeding_events"],
            "note": "Run-Level primaer, PlantInstance nur standalone"
        }
    ]
}
```

## 7. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **PlantingRun-CRUD:** Erstellen, Lesen, Aktualisieren, Loeschen von Pflanzdurchlaeufen funktioniert
- [ ] **Entry-Management:** Entry kann hinzugefuegt, bearbeitet und entfernt werden (nur im Status `planned`)
- [ ] **Typ-Validierung:** Genau 1 Entry pro Run; Clone erfordert source_plant_key
- [ ] **Quantity-Konsistenz:** Entry-Quantity muss `planned_quantity` entsprechen
- [ ] **Status-State-Machine:** Nur erlaubte Uebergaenge (planned→active→harvesting→completed; +cancelled) moeglich
- [ ] **Batch-Erstellung:** `create-plants` erzeugt N PlantInstances mit auto-generierten IDs und `run_contains`-Edges; setzt Run-Phase
- [ ] **ID-Generierung:** Pflanzen-IDs folgen dem Schema `{LOCATION}_{PREFIX}_{SEQ:02d}` ohne Kollisionen
- [ ] **Run-Level Phasenwechsel:** `/transition` aktualisiert `current_phase_key` auf dem Run; keine per-Plant Phase-Edges
- [ ] **Phase-History:** PhaseHistory wird auf dem Run (nicht auf Plants) geschrieben
- [ ] **Batch-Ernte:** `batch-harvest` erstellt eine `Batch`-Node (REQ-007), verknuepft ueber `run_produced`-Edge
- [ ] **Batch-Entfernung:** `batch-remove` setzt `removed_on` auf allen aktiven Pflanzen und schliesst den Run ab
- [ ] **Detach → Standalone:** `detach` kopiert Run-Phase auf PlantInstance, erzeugt eigene `current_phase`-Edge, Pflanze wird standalone
- [ ] **Keine Einzelbearbeitung im Run:** Tasks, Phasen, Care werden ausschliesslich auf Run-Ebene verwaltet
- [ ] **Standalone-Modus:** PlantInstance ohne aktiven Run behaelt volle Management-Faehigkeiten
- [ ] **Keine Doppelzugehoerigkeit:** Eine PlantInstance kann nur zu maximal einem aktiven PlantingRun gehoeren
- [ ] **Seed-to-Shelf:** Von Batch ueber `run_produced` → PlantingRun → Entry → Species/Cultivar lueckenlos navigierbar
- [ ] **Tagebuch-CRUD:** Erstellen, Lesen, Aktualisieren, Loeschen von Tagebuch-Eintraegen fuer einzelne Pflanzen
- [ ] **Tagebuch-Aggregation:** Aggregiertes Tagebuch aller Pflanzen im Run abrufbar
- [ ] **Tagebuch-Standalone:** Tagebuch funktioniert auch fuer standalone PlantInstances
- [ ] **Graph-Integration:** Alle neuen Edge Collections korrekt im Named Graph `kamerplanter_graph` registriert
- [ ] **Dual-Support-Edges:** `current_phase`, `phase_history`, `has_task`, `has_care_profile`, `inspected_by`, `fed_by` akzeptieren sowohl `planting_runs` als auch `plant_instances` als Quell-Vertex
- [ ] **NFR-006-Fehlerbehandlung:** Aussagekraeftige Fehlermeldungen bei Validierungsfehlern und Konfliktzustaenden
- [ ] **Klon-Metadaten:** clone_generation, propagation_method und rooting_count werden bei Clone-Runs erfasst
- [ ] **Detach-Kategorien:** Strukturierte Kategorie neben Freitext-Begruendung
- [ ] **Multi-Location:** run_at_location unterstuetzt Standortwechsel mit Zeitstempeln
- [ ] **Per-Plant-Harvest:** Optional pro-Pflanze-Gewichte in Batch-Ernte fuer Ertragsverteilungs-Analyse
- [ ] **Run-Klonen:** clone_from_run_key ermoeglicht Staffelanbau durch Kopieren der Run-Konfiguration
- [ ] **NutrientPlan-Zuweisung:** NutrientPlan kann einem PlantingRun zugewiesen werden (`RUN_FOLLOWS_PLAN`-Edge)
<!-- Quelle: Tabellen-Analyse UI-NFR-010 §7.2, §2.7 -->
- [ ] **Listenansicht-Filter:** PlantingRun-Liste bietet Status-Filter und optionalen Standort-Filter
- [ ] **Tablet-Spaltenprioritaeten:** PlantingRun-ListPage blendet auf Tablet Start-/Enddatum aus
<!-- Quelle: Outdoor-Garden-Planner Review G-009 -->
- [ ] **Sukzessions-Plan CRUD:** Erstellen, Lesen, Aktualisieren, Loeschen von SuccessionPlans funktioniert
- [ ] **Sukzessions-Run-Generierung:** System generiert automatisch N PlantingRuns basierend auf interval_days
- [ ] **Sukzessions-Erinnerung:** Erinnerung wird reminder_days_before Tage vor naechster Aussaat erzeugt

### Testszenarien:

**Szenario 1: Monokultur — Vollstaendiger Lebenszyklus**
```
GIVEN: Species "Solanum lycopersicum", Cultivar "San Marzano", Location "Hochbeet A"
WHEN: Nutzer erstellt PlantingRun (type: monoculture, planned_quantity: 20)
  UND ruft create-plants auf
THEN:
  - Run-Status wechselt von "planned" → "active"
  - Run erhaelt current_phase_key (initiale Phase aus Lifecycle-Config)
  - 20 PlantInstances mit IDs HOCHBEETA_TOM_01…20 werden erstellt
  - 20 run_contains-Edges verbinden Run mit Pflanzen
  - Pflanzen haben KEINE eigenen current_phase-Edges
  - actual_quantity des Runs = 20
```

**Szenario 2: Run-Level Phasenwechsel**
```
GIVEN: PlantingRun "Tomaten Hochbeet A" mit 20 Pflanzen, Run-Phase "vegetative"
WHEN: Nutzer ruft /transition (target_phase_key: "flowering") auf
THEN:
  - Run.current_phase_key wechselt zu "flowering"
  - PhaseHistory auf dem Run: "vegetative" wird abgeschlossen, "flowering" wird gestartet
  - Alle 20 Pflanzen teilen die neue Phase (keine eigenen Edges)
  - KEINE exclude-Moeglichkeit — der Run ist die Einheit
```

**Szenario 3: Detach → Standalone**
```
GIVEN: PlantingRun mit 20 Pflanzen, Run-Phase "flowering"
WHEN: Nutzer ruft detach (plant_key: "HOCHBEETA_TOM_05", category: "disease") auf
THEN:
  - run_contains-Edge wird mit detached_at gesetzt
  - Pflanze HOCHBEETA_TOM_05 erhaelt:
    - current_phase_key = "flowering" (kopiert vom Run)
    - eigene current_phase-Edge: plant_instances/HOCHBEETA_TOM_05 → growth_phases/flowering
    - eigene offene PhaseHistory
  - Pflanze kann ab sofort eigenstaendig verwaltet werden (Phase, Tasks, Care etc.)
  - Run zeigt active_plant_count: 19
```

**Szenario 4: Tagebuch innerhalb eines Runs**
```
GIVEN: PlantingRun mit 20 Pflanzen, Pflanze HOCHBEETA_TOM_05 noch im Run
WHEN: Nutzer erstellt Tagebuch-Eintrag fuer TOM_05 (type: problem, text: "Braune Flecken")
THEN:
  - PlantDiaryEntry wird erstellt
  - has_diary_entry-Edge: plant_instances/TOM_05 → plant_diary_entries/...
  - Eintrag erscheint im individuellen Tagebuch UND im aggregierten Run-Tagebuch
  - KEIN Einfluss auf Run-Management (Phase, Tasks etc. bleiben auf Run-Ebene)
```

**Szenario 5: Klon-Durchlauf**
```
GIVEN: Mutterpflanze "GROWZELT1_MOTHER_WW01" existiert
WHEN: Nutzer erstellt PlantingRun (type: clone, source_plant_key: "GROWZELT1_MOTHER_WW01")
THEN:
  - Run wird mit source_plant_key gespeichert
  - create-plants erzeugt 10 PlantInstances
  - Run erhaelt initiale Phase (z.B. "rooting" fuer Stecklinge)
WHEN: Nutzer versucht Clone-Run ohne source_plant_key
THEN:
  - Validierungsfehler 422: "Clone-Durchlaeufe erfordern source_plant_key"
```

**Szenario 6: Typ-Constraint-Verletzungen**
```
GIVEN: Kein bestehender PlantingRun
WHEN: Nutzer versucht Run mit 2 Entries zu erstellen
THEN:
  - Validierungsfehler 422: Runs erlauben genau 1 Entry

WHEN: Nutzer versucht PlantingRun mit Entry (quantity: 15) aber planned_quantity: 20
THEN:
  - Validierungsfehler 422: "Summe der Entry-Quantities (15) muss planned_quantity (20) entsprechen"
```

**Szenario 7: Batch-Ernte mit Seed-to-Shelf-Traceability**
```
GIVEN: Aktiver PlantingRun mit 20 Pflanzen, Run-Phase "ripening"
WHEN: Nutzer ruft batch-harvest (harvest_type: "final", wet_weight_g: 12500) auf
THEN:
  - Neuer Batch wird erstellt
  - run_produced-Edge verbindet Run mit Batch
  - Run-Status wechselt zu "completed"
  - Rueckverfolgung: Batch → PlantingRun → Entry → Species → Location
```

**Szenario 8: NutrientPlan zuweisen**
```
GIVEN: PlantingRun "Tomaten Hochbeet A" mit 20 aktiven Pflanzen
WHEN: POST nutrient-plan (nutrient_plan_key: "plan_tomato_coco")
THEN:
  - RUN_FOLLOWS_PLAN-Edge: PlantingRun → NutrientPlan erstellt
  - PlantingRun.nutrient_plan_key = "plan_tomato_coco"
  - KEINE per-Plant FOLLOWS_PLAN-Edges (Plan gilt fuer den ganzen Run)
```

---

**Hinweise fuer RAG-Integration:**
- Keywords: Pflanzdurchlauf, Planting Run, Batch-Operation, Gruppenmanagement, Monokultur, Klon, Batch-Erstellung, Run-Level Phasenwechsel, Batch-Ernte, Batch-Entfernung, Seed-to-Shelf, Traceability, Sukzessions-Aussaat, Staffelanbau, Dual-Modell, Standalone, Detach, Pflanzen-Tagebuch, Plant Diary
- Fachbegriffe: PlantingRun, PlantingRunEntry, PlantDiaryEntry, SuccessionPlan, Mutterpflanze, Steckling, Klon-Generation, Staffelanbau, Succession Planting, Detach-Kategorie, Male Plant, Bewurzelungsrate, Keimrate, HarvestBatch, State Machine, ID-Generierung, NutrientPlan-Zuweisung, RUN_FOLLOWS_PLAN, Dual-Support, current_phase, phase_history, has_task, has_care_profile
- Verknuepfung: Baut auf REQ-001 (Species/Cultivar), REQ-002 (Location/Substrate), REQ-003 (Phasensteuerung, Dual-Support), REQ-004 (NutrientPlan) auf; liefert an REQ-006 (Run-Tasks), REQ-007 (Batch-Ernte), REQ-009 (Dashboard), REQ-010 (IPM, Dual-Support), REQ-014 (Giessplan), REQ-022 (Care, Dual-Support), REQ-028 (Mischkultur ueber Standort-Graph)
