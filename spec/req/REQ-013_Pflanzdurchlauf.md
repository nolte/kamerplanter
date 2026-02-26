# Spezifikation: REQ-013 - Pflanzdurchlauf-Verwaltung & Batch-Operationen

```yaml
ID: REQ-013
Titel: Pflanzdurchlauf-Verwaltung & Batch-Operationen
Kategorie: Gruppenmanagement
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich zusammengehörige Pflanzen als Gruppe anlegen und verwalten, um typische Praxis-Szenarien wie '20 Tomaten ins Hochbeet setzen' oder '10 Stecklinge für den nächsten Erntezyklus' effizient abzubilden, Batch-Operationen auf die Gruppe anzuwenden und die Rückverfolgbarkeit von der Aussaat bis zur Ernte sicherzustellen."

**Beschreibung:**
Das System führt den **Pflanzdurchlauf (Planting Run)** als leichtgewichtigen Gruppierungs-Container ein. Aktuell werden Pflanzen (`PlantInstance`) einzeln angelegt und verwaltet — es fehlt ein Gruppenkonzept für typische Praxis-Szenarien. Der PlantingRun schließt diese Lücke mit:

- **Batch-Erstellung:** N Pflanzen in einer Operation mit auto-generierten IDs anlegen
- **Batch-Phasenübergang:** Alle berechtigten Pflanzen gemeinsam zur nächsten Phase überführen
- **Batch-Ernte:** HarvestBatch (REQ-007) direkt aus PlantingRun erstellen → Seed-to-Shelf-Traceability
- **Batch-Entfernung:** Run abschließen und alle Pflanzen als entfernt markieren
- **Individuelle Autonomie:** Einzelne Pflanzen können jederzeit aus der Gruppe herausgelöst und unabhängig verwaltet werden

**Grundprinzipien:**

- **Leichtgewichtiger Container:** Ein PlantingRun gruppiert, kontrolliert aber nicht — jede PlantInstance behält ihre volle Eigenständigkeit
- **Keine Doppelzugehörigkeit:** Eine PlantInstance gehört zu maximal einem PlantingRun (oder zu keinem)
- **Soft Binding:** Pflanzen können jederzeit vom Run abgetrennt (detached) werden, ohne gelöscht zu werden
- **Typsicherheit:** Monokultur/Klon-Runs erzwingen genau eine Art, Mischkultur-Runs erlauben mehrere
- **Seed-to-Shelf:** Direkte Verknüpfung zu HarvestBatch (REQ-007) für lückenlose Rückverfolgbarkeit

### 1.1 Drei Szenarien

**Szenario 1: Monokultur — 20 Tomaten San Marzano im Hochbeet A**
```
PlantingRun: "Tomaten Hochbeet A 2025"
  type: monoculture
  status: active
  Entries: [{ species: Solanum lycopersicum, cultivar: San Marzano, quantity: 20, role: primary }]
  Location: Hochbeet A
  Substrate: Bio-Erde Charge #2025-03
  Plants: HOCHBEETA_01 … HOCHBEETA_20 (auto-generiert)
```

**Szenario 2: Klone — 10 Cannabis-Stecklinge im Growzelt**
```
PlantingRun: "White Widow Klone Runde 3"
  type: clone
  status: active
  Entries: [{ species: Cannabis sativa, cultivar: White Widow, quantity: 10, role: primary }]
  Location: Grow Zelt 1
  Substrate: Coco-Perlite 70/30 Charge #2025-04
  source_plant_key: "GROWZELT1_MOTHER_WW01"  ← Mutterpflanze
  Plants: GROWZELT1_WW3_01 … GROWZELT1_WW3_10 (auto-generiert)
```

**Szenario 3: Mischkultur — Tomate + Basilikum + Tagetes im Beet B**
```
PlantingRun: "Mischkultur Beet B Sommer 2025"
  type: mixed_culture
  status: active
  Entries:
    - { species: Solanum lycopersicum, cultivar: Roma, quantity: 8, role: primary }
    - { species: Ocimum basilicum, cultivar: Genovese, quantity: 12, role: companion }
    - { species: Tagetes patula, cultivar: Naughty Marietta, quantity: 6, role: trap_crop }
  Location: Beet B
  Substrate: Living Soil Charge #2025-02
  Plants: BEETB_TOM_01…08, BEETB_BAS_01…12, BEETB_TAG_01…06 (auto-generiert)
```

## 2. GraphDB-Modellierung

### Nodes:

- **`:PlantingRun`** — Pflanzdurchlauf (Gruppierungs-Container)
  - Collection: `planting_runs`
  - Properties:
    - `name: str` (Benutzerfreundlicher Name, z.B. "Tomaten Hochbeet A 2025")
    - `run_type: Literal['monoculture', 'clone', 'mixed_culture']`
    - `status: Literal['planned', 'active', 'harvesting', 'completed', 'cancelled']`
    - `planned_quantity: int` (Geplante Gesamtanzahl Pflanzen)
    - `actual_quantity: int` (Tatsächlich erzeugte Pflanzen, berechnet)
    - `planned_start_date: Optional[date]` (Geplantes Startdatum)
    - `started_at: Optional[datetime]` (Tatsächlicher Start)
    - `completed_at: Optional[datetime]` (Abschluss-Zeitpunkt)
    - `source_plant_key: Optional[str]` (Nur bei `clone`: Key der Mutterpflanze)
    - `notes: Optional[str]`
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:PlantingRunEntry`** — Artenzusammensetzung eines Durchlaufs
  - Collection: `planting_run_entries`
  - Properties:
    - `species_key: str` (Referenz auf Species)
    - `cultivar_key: Optional[str]` (Referenz auf Cultivar, optional)
    - `quantity: int` (Geplante Anzahl für diese Art)
    - `role: Literal['primary', 'companion', 'trap_crop']`
    - `id_prefix: Optional[str]` (Präfix für auto-generierte Pflanzen-IDs, z.B. "TOM", "BAS")
    - `spacing_cm: Optional[int]` (Empfohlener Pflanzabstand)
    - `notes: Optional[str]`

### Konfigurationsregeln:

| Run-Type | Entries | Constraint |
|----------|---------|------------|
| `monoculture` | Genau 1 | `role` muss `primary` sein |
| `clone` | Genau 1 | `role` muss `primary` sein; `source_plant_key` auf PlantingRun erforderlich |
| `mixed_culture` | ≥ 2 | Mindestens 1 `primary`; mindestens 1 `companion` oder `trap_crop` |

### Edges (ArangoDB Edge Collections):

**Neue Edge Collections:**

- **`run_contains`**: `PlantingRun → PlantInstance`
  - Properties:
    - `added_at: datetime` (Wann wurde die Pflanze dem Run zugeordnet)
    - `detached_at: Optional[datetime]` (Wann wurde die Pflanze abgetrennt; `null` = aktiv)
    - `detach_reason: Optional[str]` (z.B. "Krankheit", "Selektion", "Umtopfung")

- **`run_at_location`**: `PlantingRun → Location`
  - Properties:
    - `assigned_at: datetime`
    - `notes: Optional[str]`

- **`run_uses_substrate`**: `PlantingRun → SubstrateBatch`
  - Properties:
    - `assigned_at: datetime`
    - `volume_liters: Optional[float]` (Verbrauchte Menge)

- **`run_produced`**: `PlantingRun → Batch`
  - Properties:
    - `harvested_at: datetime`
    - `plant_count: int` (Anzahl geernteter Pflanzen aus diesem Run)
    - `notes: Optional[str]`

- **`has_entry`**: `PlantingRun → PlantingRunEntry`
  - Properties: (keine)

- **`entry_for_species`**: `PlantingRunEntry → Species`
  - Properties: (keine)

- **`entry_for_cultivar`**: `PlantingRunEntry → Cultivar` (optional)
  - Properties: (keine)

### AQL-Beispielqueries (ArangoDB 3.11+):

**1. PlantingRun mit allen Entries, Pflanzen und Standort laden:**
```aql
LET run = DOCUMENT("planting_runs", @run_key)

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
    LET current_phase = FIRST(
        FOR phase IN 1..1 OUTBOUND v current_phase
        RETURN phase.name
    )
    RETURN {
        plant: v,
        added_at: e.added_at,
        current_phase: current_phase
    }
)

LET location = FIRST(
    FOR v, e IN 1..1 OUTBOUND run run_at_location
    RETURN v
)

LET substrate = FIRST(
    FOR v, e IN 1..1 OUTBOUND run run_uses_substrate
    RETURN MERGE(v, { volume_used: e.volume_liters })
)

RETURN MERGE(run, {
    entries: entries,
    plants: plants,
    active_plant_count: LENGTH(plants),
    location: location,
    substrate: substrate
})
```

**2. Batch-Phasenübergang — alle berechtigten Pflanzen finden:**
```aql
// Findet alle Pflanzen im Run, die sich in der angegebenen Phase befinden
// und für eine Transition berechtigt sind
LET run = DOCUMENT("planting_runs", @run_key)

FOR plant, rc_edge IN 1..1 OUTBOUND run run_contains
    FILTER rc_edge.detached_at == null  // Nur aktive Run-Mitglieder

    // Aktuelle Phase der Pflanze
    LET current_phase = FIRST(
        FOR phase, cp_edge IN 1..1 OUTBOUND plant current_phase
        RETURN phase
    )
    FILTER current_phase.name == @from_phase

    // Nächste Phase ermitteln
    LET next_phase = FIRST(
        FOR np IN 1..1 OUTBOUND current_phase next_phase
        RETURN np
    )
    FILTER next_phase != null  // Keine Transition wenn keine nächste Phase

    // Transition-Regel prüfen
    LET rule = FIRST(
        FOR r IN 1..1 OUTBOUND current_phase governed_by
        RETURN r
    )

    RETURN {
        plant_key: plant._key,
        plant_id: plant.instance_id,
        current_phase: current_phase.name,
        next_phase: next_phase.name,
        transition_rule: rule,
        days_in_phase: DATE_DIFF(
            FIRST(
                FOR h IN phase_history
                    FILTER h._from == plant._id AND h.exited_at == null
                    RETURN h.entered_at
            ),
            DATE_NOW(),
            "day"
        )
    }
```

**3. Alle aktiven Runs an einem Standort mit Pflanzen-Statistiken:**
```aql
FOR run IN planting_runs
    FILTER run.status IN ["active", "harvesting"]

    LET location = FIRST(
        FOR v IN 1..1 OUTBOUND run run_at_location
        RETURN v
    )
    FILTER location._key == @location_key

    LET plant_stats = (
        FOR plant, e IN 1..1 OUTBOUND run run_contains
        FILTER e.detached_at == null
        COLLECT phase = FIRST(
            FOR p IN 1..1 OUTBOUND plant current_phase RETURN p.name
        ) WITH COUNT INTO count
        RETURN { phase, count }
    )

    LET total_active = SUM(plant_stats[*].count)
    LET detached_count = LENGTH(
        FOR plant, e IN 1..1 OUTBOUND run run_contains
        FILTER e.detached_at != null
        RETURN 1
    )

    RETURN {
        run_key: run._key,
        run_name: run.name,
        run_type: run.run_type,
        status: run.status,
        planned_quantity: run.planned_quantity,
        active_plants: total_active,
        detached_plants: detached_count,
        phase_distribution: plant_stats,
        started_at: run.started_at
    }
```

**4. Seed-to-Shelf Traceability — Rückverfolgung von Batch zu Run:**
```aql
// Von einem HarvestBatch zurück zum PlantingRun und dessen Ursprung
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
            role: entry.role,
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

**5. Mischkultur-Kompatibilitäts-Check für einen Run:**
```aql
// Prüft ob alle Entries in einem mixed_culture Run kompatibel sind
LET run = DOCUMENT("planting_runs", @run_key)
FILTER run.run_type == "mixed_culture"

LET entries = (
    FOR entry IN 1..1 OUTBOUND run has_entry
    LET species = FIRST(FOR s IN 1..1 OUTBOUND entry entry_for_species RETURN s)
    RETURN { entry_key: entry._key, species_id: species._id, species_name: species.scientific_name, role: entry.role }
)

// Prüfe alle Paare auf Kompatibilität
LET compatibility_checks = (
    FOR e1 IN entries
        FOR e2 IN entries
            FILTER e1.entry_key < e2.entry_key  // Jedes Paar nur einmal

            // Spezies-Level: kompatibel?
            LET compat = FIRST(
                FOR v, edge IN 1..1 OUTBOUND DOCUMENT(e1.species_id) compatible_with
                FILTER v._id == e2.species_id
                RETURN edge
            )

            // Spezies-Level: inkompatibel?
            LET incompat = FIRST(
                FOR v, edge IN 1..1 OUTBOUND DOCUMENT(e1.species_id) incompatible_with
                FILTER v._id == e2.species_id
                RETURN edge
            )

            // Familien-Level Fallback
            LET f1 = FIRST(FOR f IN 1..1 OUTBOUND DOCUMENT(e1.species_id) belongs_to_family RETURN f)
            LET f2 = FIRST(FOR f IN 1..1 OUTBOUND DOCUMENT(e2.species_id) belongs_to_family RETURN f)

            LET family_compat = compat == null AND incompat == null ? FIRST(
                FOR v, edge IN 1..1 ANY f1 family_compatible_with
                FILTER v._id == f2._id
                RETURN edge
            ) : null

            LET family_incompat = compat == null AND incompat == null ? FIRST(
                FOR v, edge IN 1..1 ANY f1 family_incompatible_with
                FILTER v._id == f2._id
                RETURN edge
            ) : null

            RETURN {
                species_a: e1.species_name,
                species_b: e2.species_name,
                status: incompat != null ? "INCOMPATIBLE"
                    : (family_incompat != null ? "FAMILY_INCOMPATIBLE"
                    : (compat != null ? "COMPATIBLE"
                    : (family_compat != null ? "FAMILY_COMPATIBLE"
                    : "UNKNOWN"))),
                score: incompat != null ? 0.0
                    : (compat != null ? compat.compatibility_score
                    : (family_compat != null ? family_compat.compatibility_score * 0.8
                    : null)),
                detail: incompat != null ? incompat.reason
                    : (family_incompat != null ? family_incompat.reason
                    : (compat != null ? CONCAT("Spezies-Level, Score: ", compat.compatibility_score)
                    : (family_compat != null ? CONCAT("Familien-Level (", f1.name, " ↔ ", f2.name, "), Score: ", family_compat.compatibility_score * 0.8)
                    : "Keine Daten")))
            }
)

LET has_incompatible = LENGTH(
    FOR c IN compatibility_checks FILTER c.status IN ["INCOMPATIBLE", "FAMILY_INCOMPATIBLE"] RETURN 1
) > 0

RETURN {
    run_key: run._key,
    run_name: run.name,
    overall_status: has_incompatible ? "WARNING" : "OK",
    checks: compatibility_checks
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
    "planned_start_date": "2025-05-01",
    "started_at": "2025-05-03T09:00:00Z",
    "completed_at": null,
    "source_plant_key": null,
    "notes": "Erste Runde San Marzano für Passata-Produktion",
    "created_at": "2025-04-15T10:00:00Z",
    "updated_at": "2025-05-03T09:00:00Z"
}

// planting_run_entries collection
{
    "_key": "tomaten_hba_entry_01",
    "species_key": "solanum_lycopersicum",
    "cultivar_key": "san_marzano",
    "quantity": 20,
    "role": "primary",
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
    "role": "primary",
    "id_prefix": "WW3",
    "spacing_cm": 30,
    "notes": "Bewurzelungsgel: Clonex, Stecklinge 10–15 cm"
}

// has_entry edge
{ "_from": "planting_runs/ww_klone_runde3", "_to": "planting_run_entries/ww_klone_r3_entry_01" }

// entry_for_species edge
{ "_from": "planting_run_entries/ww_klone_r3_entry_01", "_to": "species/cannabis_sativa" }

// entry_for_cultivar edge
{ "_from": "planting_run_entries/ww_klone_r3_entry_01", "_to": "cultivars/white_widow" }

// run_at_location edge
{ "_from": "planting_runs/ww_klone_runde3", "_to": "locations/growzelt1", "assigned_at": "2025-06-01T08:00:00Z" }

// run_uses_substrate edge
{ "_from": "planting_runs/ww_klone_runde3", "_to": "substrate_batches/coco_perlite_2025_04", "assigned_at": "2025-06-01T08:00:00Z", "volume_liters": 50 }

// run_contains edges (Auszug)
{ "_from": "planting_runs/ww_klone_runde3", "_to": "plant_instances/GROWZELT1_WW3_01", "added_at": "2025-06-01T08:00:00Z", "detached_at": null }
// … bis GROWZELT1_WW3_10
```

**Szenario 3 — Mischkultur (Tomate + Basilikum + Tagetes):**
```json
// planting_runs collection
{
    "_key": "mischkultur_beet_b_2025",
    "name": "Mischkultur Beet B Sommer 2025",
    "run_type": "mixed_culture",
    "status": "active",
    "planned_quantity": 26,
    "actual_quantity": 26,
    "planned_start_date": "2025-05-15",
    "started_at": "2025-05-15T10:00:00Z",
    "completed_at": null,
    "source_plant_key": null,
    "notes": "Klassische Mischkultur-Kombination: Tomate-Basilikum-Tagetes",
    "created_at": "2025-05-10T16:00:00Z",
    "updated_at": "2025-05-15T10:00:00Z"
}

// planting_run_entries collection
{
    "_key": "misch_bb_entry_tom",
    "species_key": "solanum_lycopersicum",
    "cultivar_key": "roma",
    "quantity": 8,
    "role": "primary",
    "id_prefix": "TOM",
    "spacing_cm": 50,
    "notes": null
}
{
    "_key": "misch_bb_entry_bas",
    "species_key": "ocimum_basilicum",
    "cultivar_key": "genovese",
    "quantity": 12,
    "role": "companion",
    "id_prefix": "BAS",
    "spacing_cm": 25,
    "notes": "Zwischen Tomaten pflanzen — Blattlaus-Abwehr"
}
{
    "_key": "misch_bb_entry_tag",
    "species_key": "tagetes_patula",
    "cultivar_key": "naughty_marietta",
    "quantity": 6,
    "role": "trap_crop",
    "id_prefix": "TAG",
    "spacing_cm": 30,
    "notes": "Beetrand — lockt Blattläuse weg von Tomaten"
}

// has_entry edges
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "planting_run_entries/misch_bb_entry_tom" }
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "planting_run_entries/misch_bb_entry_bas" }
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "planting_run_entries/misch_bb_entry_tag" }

// entry_for_species edges
{ "_from": "planting_run_entries/misch_bb_entry_tom", "_to": "species/solanum_lycopersicum" }
{ "_from": "planting_run_entries/misch_bb_entry_bas", "_to": "species/ocimum_basilicum" }
{ "_from": "planting_run_entries/misch_bb_entry_tag", "_to": "species/tagetes_patula" }

// entry_for_cultivar edges
{ "_from": "planting_run_entries/misch_bb_entry_tom", "_to": "cultivars/roma" }
{ "_from": "planting_run_entries/misch_bb_entry_bas", "_to": "cultivars/genovese" }
{ "_from": "planting_run_entries/misch_bb_entry_tag", "_to": "cultivars/naughty_marietta" }

// run_at_location edge
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "locations/beet_b", "assigned_at": "2025-05-15T10:00:00Z" }

// run_uses_substrate edge
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "substrate_batches/living_soil_2025_02", "assigned_at": "2025-05-15T10:00:00Z", "volume_liters": 300 }

// run_contains edges (Auszug)
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "plant_instances/BEETB_TOM_01", "added_at": "2025-05-15T10:00:00Z", "detached_at": null }
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "plant_instances/BEETB_BAS_01", "added_at": "2025-05-15T10:00:00Z", "detached_at": null }
{ "_from": "planting_runs/mischkultur_beet_b_2025", "_to": "plant_instances/BEETB_TAG_01", "added_at": "2025-05-15T10:00:00Z", "detached_at": null }
// … bis BEETB_TOM_08, BEETB_BAS_12, BEETB_TAG_06
```

## 3. Technische Umsetzung (Python)

### Enumerationen:

```python
from enum import StrEnum

class PlantingRunType(StrEnum):
    """Typ des Pflanzdurchlaufs"""
    MONOCULTURE = "monoculture"      # Eine Art, eine Sorte
    CLONE = "clone"                  # Stecklinge von einer Mutterpflanze
    MIXED_CULTURE = "mixed_culture"  # Mehrere Arten/Sorten (Mischkultur)

class PlantingRunStatus(StrEnum):
    """Status-State-Machine für Pflanzdurchläufe"""
    PLANNED = "planned"        # Geplant, noch nicht gestartet
    ACTIVE = "active"          # Pflanzen angelegt, Durchlauf läuft
    HARVESTING = "harvesting"  # Erntephase (teil- oder komplett)
    COMPLETED = "completed"    # Abgeschlossen (alle Pflanzen entfernt/geerntet)
    CANCELLED = "cancelled"    # Abgebrochen (vor oder während Durchlauf)

class EntryRole(StrEnum):
    """Rolle einer Art im Pflanzdurchlauf"""
    PRIMARY = "primary"          # Hauptkultur (Ernte-Ziel)
    COMPANION = "companion"      # Begleitpflanze (Nützlingsförderung, Düngung)
    TRAP_CROP = "trap_crop"      # Fangpflanze (lenkt Schädlinge ab)
```

### Status-Transitions:

```python
# Erlaubte Übergänge in der State-Machine
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
from pydantic import BaseModel, Field, model_validator

class PlantingRunEntryCreate(BaseModel):
    """Erstellt einen Eintrag für die Artenzusammensetzung"""

    species_key: str = Field(description="Key der Species in ArangoDB")
    cultivar_key: Optional[str] = Field(None, description="Key der Cultivar (optional)")
    quantity: int = Field(ge=1, le=1000, description="Geplante Anzahl Pflanzen für diese Art")
    role: EntryRole = Field(description="Rolle im Durchlauf")
    id_prefix: Optional[str] = Field(
        None,
        max_length=5,
        pattern=r'^[A-Z]{2,5}$',
        description="Präfix für auto-generierte Pflanzen-IDs (z.B. 'TOM', 'BAS')"
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
    location_key: Optional[str] = Field(None, description="Standort-Zuordnung")
    substrate_batch_key: Optional[str] = Field(None, description="Substrat-Charge")
    substrate_volume_liters: Optional[float] = Field(None, gt=0, description="Verbrauchte Substrat-Menge")
    entries: list[PlantingRunEntryCreate] = Field(min_length=1)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_run_type_constraints(self):
        """Validiert Typ-spezifische Constraints"""

        if self.run_type == PlantingRunType.CLONE:
            if not self.source_plant_key:
                raise ValueError(
                    "source_plant_key ist erforderlich für Clone-Durchläufe"
                )

        if self.run_type in (PlantingRunType.MONOCULTURE, PlantingRunType.CLONE):
            if len(self.entries) != 1:
                raise ValueError(
                    f"{self.run_type}-Durchläufe erlauben genau 1 Entry, "
                    f"erhalten: {len(self.entries)}"
                )
            if self.entries[0].role != EntryRole.PRIMARY:
                raise ValueError(
                    f"{self.run_type}-Durchläufe erfordern Entry-Rolle 'primary'"
                )

        if self.run_type == PlantingRunType.MIXED_CULTURE:
            if len(self.entries) < 2:
                raise ValueError(
                    "Mischkultur-Durchläufe erfordern mindestens 2 Entries"
                )
            has_primary = any(e.role == EntryRole.PRIMARY for e in self.entries)
            has_secondary = any(
                e.role in (EntryRole.COMPANION, EntryRole.TRAP_CROP)
                for e in self.entries
            )
            if not has_primary:
                raise ValueError("Mindestens ein Entry muss die Rolle 'primary' haben")
            if not has_secondary:
                raise ValueError(
                    "Mindestens ein Entry muss die Rolle 'companion' oder 'trap_crop' haben"
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
    """Antwort-Schema für einen Pflanzdurchlauf"""

    key: str
    name: str
    run_type: PlantingRunType
    status: PlantingRunStatus
    planned_quantity: int
    actual_quantity: int
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
    """Erstellt N Pflanzen für einen PlantingRun"""

    assign_to_slots: bool = Field(
        default=False,
        description="Automatisch freie Slots am Standort zuweisen"
    )
    initial_phase: Optional[str] = Field(
        None,
        description="Initiale Wachstumsphase (Default: erste Phase des Lifecycle)"
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

class BatchTransitionRequest(BaseModel):
    """Batch-Phasenübergang für alle berechtigten Pflanzen"""

    target_phase: str = Field(description="Ziel-Phase (z.B. 'flowering')")
    override_reason: Optional[str] = Field(
        None,
        description="Grund für manuellen Override (überspringt Regel-Prüfung)"
    )
    exclude_plant_keys: list[str] = Field(
        default_factory=list,
        description="Pflanzen, die vom Batch-Übergang ausgeschlossen werden sollen"
    )

class BatchTransitionResponse(BaseModel):
    """Ergebnis des Batch-Phasenübergangs"""

    run_key: str
    transitioned_count: int
    skipped_count: int
    transitioned_plants: list[str]
    skipped_plants: list[dict]  # [{ key, reason }]
    target_phase: str

class BatchHarvestRequest(BaseModel):
    """Erstellt einen HarvestBatch aus einem PlantingRun"""

    harvest_type: str = Field(
        description="Ernte-Typ: 'partial' | 'final'"
    )
    wet_weight_g: float = Field(gt=0)
    quality_grade: Optional[str] = Field(
        None,
        pattern=r'^(A\+|A|B|C|D)$',
        description="Qualitätsstufe"
    )
    harvester: str = Field(description="User-ID des Erntenden")
    weather_conditions: Optional[str] = None
    notes: Optional[str] = None
    exclude_plant_keys: list[str] = Field(
        default_factory=list,
        description="Pflanzen, die von der Ernte ausgeschlossen werden sollen"
    )

class BatchHarvestResponse(BaseModel):
    """Ergebnis der Batch-Ernte"""

    run_key: str
    batch_key: str
    batch_id: str
    harvested_plant_count: int
    wet_weight_g: float
    quality_grade: Optional[str]
    run_status_after: PlantingRunStatus

class BatchRemoveRequest(BaseModel):
    """Entfernt alle Pflanzen aus dem Run und schließt ihn ab"""

    reason: str = Field(
        min_length=1,
        description="Grund für die Entfernung (z.B. 'Saisonende', 'Krankheit')"
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
    """Trennt eine einzelne Pflanze vom Run ab"""

    reason: str = Field(
        min_length=1,
        description="Grund für die Abtrennung"
    )
```

### Engine-Logik:

**1. PlantingRunEngine — Batch-Erstellung:**
```python
from datetime import date, datetime
from typing import Optional

class PlantingRunEngine:
    """Kernlogik für Pflanzdurchlauf-Operationen"""

    @staticmethod
    def generate_plant_ids(
        location_key: str,
        entries: list[dict],
        existing_ids: set[str]
    ) -> list[dict]:
        """
        Generiert eindeutige Pflanzen-IDs basierend auf Location und Entry-Präfix.

        Format: {LOCATION}_{PREFIX}_{SEQ:02d}
        Beispiel: HOCHBEETA_TOM_01, HOCHBEETA_TOM_02, ...

        Args:
            location_key: Key des Standorts (wird uppercase)
            entries: Liste der PlantingRunEntries mit quantity und id_prefix
            existing_ids: Bereits vergebene IDs am Standort (für Kollisionsvermeidung)

        Returns:
            Liste von { entry_key, instance_id, species_key, cultivar_key }
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
        """Prüft ob ein Status-Übergang erlaubt ist"""
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise ValueError(
                f"Ungültiger Status-Übergang: {current} → {target}. "
                f"Erlaubt: {', '.join(str(s) for s in allowed) or 'keine (Terminal-Status)'}"
            )

    @staticmethod
    def calculate_batch_id(run_key: str, harvest_date: date, seq: int = 1) -> str:
        """
        Generiert eine Batch-ID für die Ernte.
        Format: RUN_{RUN_KEY}_{YYYYMMDD}_{SEQ}
        """
        return f"RUN_{run_key.upper()}_{harvest_date.strftime('%Y%m%d')}_{seq:02d}"
```

**2. PlantingRunEngine — Batch-Phasenübergang:**
```python
    @staticmethod
    def filter_transition_eligible(
        plants: list[dict],
        target_phase: str,
        exclude_keys: list[str]
    ) -> tuple[list[dict], list[dict]]:
        """
        Filtert Pflanzen, die für einen Batch-Phasenübergang berechtigt sind.

        Args:
            plants: Liste von { plant_key, current_phase, next_phase, ... }
            target_phase: Ziel-Phase
            exclude_keys: Explizit ausgeschlossene Pflanzen-Keys

        Returns:
            (eligible, skipped) — jeweils Liste von Pflanzen-Dicts
        """
        eligible = []
        skipped = []

        for plant in plants:
            if plant['plant_key'] in exclude_keys:
                skipped.append({
                    'key': plant['plant_key'],
                    'reason': 'Explizit ausgeschlossen'
                })
                continue

            if plant.get('next_phase') != target_phase:
                skipped.append({
                    'key': plant['plant_key'],
                    'reason': (
                        f"Nächste Phase ist '{plant.get('next_phase')}', "
                        f"nicht '{target_phase}'"
                    )
                })
                continue

            eligible.append(plant)

        return eligible, skipped
```

**3. PlantingRunEngine — Mischkultur-Validierung:**
```python
    @staticmethod
    def validate_mixed_culture_compatibility(
        compatibility_results: list[dict]
    ) -> dict:
        """
        Bewertet die Kompatibilitäts-Ergebnisse einer Mischkultur.

        Args:
            compatibility_results: Ergebnisse aus der AQL-Kompatibilitäts-Abfrage

        Returns:
            { overall_status, score, warnings, recommendations }
        """
        incompatible = [
            r for r in compatibility_results
            if r['status'] in ('INCOMPATIBLE', 'FAMILY_INCOMPATIBLE')
        ]
        compatible = [
            r for r in compatibility_results
            if r['status'] in ('COMPATIBLE', 'FAMILY_COMPATIBLE')
        ]
        unknown = [
            r for r in compatibility_results
            if r['status'] == 'UNKNOWN'
        ]

        # Gewichteter Gesamt-Score
        scores = [r['score'] for r in compatibility_results if r['score'] is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        warnings = []
        recommendations = []

        for r in incompatible:
            warnings.append(
                f"INKOMPATIBEL: {r['species_a']} ↔ {r['species_b']} — {r['detail']}"
            )
            recommendations.append(
                f"Erwäge {r['species_b']} durch eine kompatible Art zu ersetzen"
            )

        for r in unknown:
            warnings.append(
                f"UNBEKANNT: Keine Kompatibilitätsdaten für "
                f"{r['species_a']} ↔ {r['species_b']}"
            )

        overall_status = (
            "INCOMPATIBLE" if incompatible
            else ("WARNING" if unknown else "COMPATIBLE")
        )

        return {
            'overall_status': overall_status,
            'average_score': round(avg_score, 2) if avg_score else None,
            'compatible_pairs': len(compatible),
            'incompatible_pairs': len(incompatible),
            'unknown_pairs': len(unknown),
            'warnings': warnings,
            'recommendations': recommendations,
        }
```

### Datenvalidierung:

```python
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from enum import StrEnum

# Enums (siehe oben)
# PlantingRunType, PlantingRunStatus, EntryRole

class PlantingRunDocument(BaseModel):
    """ArangoDB-Dokument-Schema für PlantingRun"""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    run_type: PlantingRunType
    status: PlantingRunStatus = PlantingRunStatus.PLANNED
    planned_quantity: int = Field(ge=1, le=10000)
    actual_quantity: int = Field(default=0, ge=0)
    planned_start_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    source_plant_key: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode='after')
    def validate_clone_source(self):
        if self.run_type == PlantingRunType.CLONE and not self.source_plant_key:
            raise ValueError("Clone-Durchläufe erfordern source_plant_key")
        if self.run_type != PlantingRunType.CLONE and self.source_plant_key:
            raise ValueError("source_plant_key nur bei Clone-Durchläufen erlaubt")
        return self

    @model_validator(mode='after')
    def validate_status_dates(self):
        if self.status == PlantingRunStatus.ACTIVE and not self.started_at:
            raise ValueError("Aktive Durchläufe erfordern started_at")
        if self.status in (PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED):
            if not self.completed_at:
                raise ValueError(f"Status '{self.status}' erfordert completed_at")
        return self


class PlantingRunEntryDocument(BaseModel):
    """ArangoDB-Dokument-Schema für PlantingRunEntry"""

    key: Optional[str] = Field(None, alias='_key')
    species_key: str
    cultivar_key: Optional[str] = None
    quantity: int = Field(ge=1, le=1000)
    role: EntryRole
    id_prefix: Optional[str] = Field(None, max_length=5, pattern=r'^[A-Z]{2,5}$')
    spacing_cm: Optional[int] = Field(None, ge=5, le=300)
    notes: Optional[str] = Field(None, max_length=500)


class RunContainsEdge(BaseModel):
    """ArangoDB-Edge-Schema für run_contains"""

    from_id: str = Field(alias='_from')
    to_id: str = Field(alias='_to')
    added_at: datetime = Field(default_factory=datetime.utcnow)
    detached_at: Optional[datetime] = None
    detach_reason: Optional[str] = Field(None, max_length=200)

    @model_validator(mode='after')
    def validate_detach(self):
        if self.detached_at and not self.detach_reason:
            raise ValueError("detach_reason erforderlich wenn detached_at gesetzt")
        return self
```

## 4. API-Endpunkte

### 4.1 CRUD — Pflanzdurchläufe (5 Endpunkte)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `GET` | `/api/v1/planting-runs` | Alle Durchläufe auflisten (Filter: status, run_type, location_key) |
| `POST` | `/api/v1/planting-runs` | Neuen Durchlauf anlegen (inkl. Entries) |
| `GET` | `/api/v1/planting-runs/{key}` | Einzelnen Durchlauf mit Entries, Pflanzen, Standort laden |
| `PUT` | `/api/v1/planting-runs/{key}` | Durchlauf-Metadaten aktualisieren (Name, Notizen, Startdatum) |
| `DELETE` | `/api/v1/planting-runs/{key}` | Durchlauf löschen (nur Status `planned`, sonst 409 Conflict) |

### 4.2 Entries — Artenzusammensetzung (4 Endpunkte)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `GET` | `/api/v1/planting-runs/{key}/entries` | Alle Entries eines Durchlaufs |
| `POST` | `/api/v1/planting-runs/{key}/entries` | Entry hinzufügen (nur Status `planned`) |
| `PUT` | `/api/v1/planting-runs/{key}/entries/{entry_key}` | Entry aktualisieren (nur Status `planned`) |
| `DELETE` | `/api/v1/planting-runs/{key}/entries/{entry_key}` | Entry entfernen (nur Status `planned`, Constraint-Prüfung) |

### 4.3 Batch-Operationen (4 Endpunkte)

| Methode | Pfad | Beschreibung | Request-Body |
|---------|------|-------------|-------------|
| `POST` | `/api/v1/planting-runs/{key}/create-plants` | N Pflanzen aus Entries erzeugen | `BatchCreatePlantsRequest` |
| `POST` | `/api/v1/planting-runs/{key}/batch-transition` | Batch-Phasenübergang | `BatchTransitionRequest` |
| `POST` | `/api/v1/planting-runs/{key}/batch-harvest` | HarvestBatch erstellen | `BatchHarvestRequest` |
| `POST` | `/api/v1/planting-runs/{key}/batch-remove` | Alle Pflanzen entfernen, Run abschließen | `BatchRemoveRequest` |

### 4.4 Pflanzen im Run (2 Endpunkte)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `GET` | `/api/v1/planting-runs/{key}/plants` | Alle Pflanzen im Run (Filter: detached=true/false, phase) |
| `POST` | `/api/v1/planting-runs/{key}/plants/{plant_key}/detach` | Einzelne Pflanze vom Run abtrennen |

### 4.5 Validierung (1 Endpunkt)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `POST` | `/api/v1/planting-runs/{key}/validate-compatibility` | Mischkultur-Kompatibilitäts-Check |

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
            "role": "primary",
            "id_prefix": "TOM",
            "spacing_cm": 50
        }
    ],
    "notes": "Erste Runde San Marzano für Passata-Produktion"
}

// Response (201 Created)
{
    "key": "tomaten_hochbeet_a_2025",
    "name": "Tomaten Hochbeet A 2025",
    "run_type": "monoculture",
    "status": "planned",
    "planned_quantity": 20,
    "actual_quantity": 0,
    "planned_start_date": "2025-05-01",
    "started_at": null,
    "completed_at": null,
    "source_plant_key": null,
    "notes": "Erste Runde San Marzano für Passata-Produktion",
    "created_at": "2025-04-15T10:00:00Z",
    "updated_at": "2025-04-15T10:00:00Z"
}
```

**POST `/api/v1/planting-runs/{key}/create-plants` — Batch-Erstellung:**
```json
// Request
{
    "assign_to_slots": true,
    "initial_phase": "seedling",
    "planted_on": "2025-05-03"
}

// Response (201 Created)
{
    "run_key": "tomaten_hochbeet_a_2025",
    "created_count": 20,
    "plant_keys": [
        "HOCHBEETA_TOM_01", "HOCHBEETA_TOM_02", "HOCHBEETA_TOM_03",
        "...",
        "HOCHBEETA_TOM_20"
    ],
    "assigned_slots": [
        "HOCHBEETA_1", "HOCHBEETA_2", "HOCHBEETA_3",
        "...",
        "HOCHBEETA_20"
    ],
    "warnings": []
}
```

**POST `/api/v1/planting-runs/{key}/batch-transition` — Batch-Phasenübergang:**
```json
// Request
{
    "target_phase": "flowering",
    "override_reason": null,
    "exclude_plant_keys": ["HOCHBEETA_TOM_05"]
}

// Response (200 OK)
{
    "run_key": "tomaten_hochbeet_a_2025",
    "transitioned_count": 18,
    "skipped_count": 2,
    "transitioned_plants": [
        "HOCHBEETA_TOM_01", "HOCHBEETA_TOM_02", "...", "HOCHBEETA_TOM_19"
    ],
    "skipped_plants": [
        { "key": "HOCHBEETA_TOM_05", "reason": "Explizit ausgeschlossen" },
        { "key": "HOCHBEETA_TOM_20", "reason": "Bereits in Phase 'flowering'" }
    ],
    "target_phase": "flowering"
}
```

**POST `/api/v1/planting-runs/{key}/batch-harvest` — Batch-Ernte:**
```json
// Request
{
    "harvest_type": "final",
    "wet_weight_g": 12500.0,
    "quality_grade": "A",
    "harvester": "user_max",
    "weather_conditions": "sonnig, 22°C",
    "notes": "Gute Ernte, keine Krankheiten",
    "exclude_plant_keys": []
}

// Response (201 Created)
{
    "run_key": "tomaten_hochbeet_a_2025",
    "batch_key": "RUN_TOMATEN_HOCHBEET_A_2025_20250915_01",
    "batch_id": "RUN_TOMATEN_HOCHBEET_A_2025_20250915_01",
    "harvested_plant_count": 20,
    "wet_weight_g": 12500.0,
    "quality_grade": "A",
    "run_status_after": "completed"
}
```

**POST `/api/v1/planting-runs/{key}/validate-compatibility` — Kompatibilitäts-Check:**
```json
// Response (200 OK)
{
    "run_key": "mischkultur_beet_b_2025",
    "overall_status": "COMPATIBLE",
    "average_score": 0.72,
    "compatible_pairs": 2,
    "incompatible_pairs": 0,
    "unknown_pairs": 1,
    "warnings": [
        "UNBEKANNT: Keine Kompatibilitätsdaten für Ocimum basilicum ↔ Tagetes patula"
    ],
    "recommendations": []
}
```

### Fehlerbehandlung (NFR-006):

| HTTP-Status | Fehlerfall | Beispiel |
|-------------|-----------|---------|
| `400` | Validierungsfehler | Entry-Quantity stimmt nicht mit planned_quantity überein |
| `404` | Run/Entry/Plant nicht gefunden | Unbekannter run_key |
| `409` | Konfliktzustand | DELETE auf aktiven Run; Pflanze gehört bereits zu anderem Run |
| `422` | Geschäftslogik-Fehler | Clone-Run ohne source_plant_key; Monokultur mit 2 Entries |

## 5. Abhängigkeiten

### Erforderliche Module:

| Modul | Abhängigkeit | Priorität |
|-------|-------------|-----------|
| **REQ-001** (Stammdaten) | Species, Cultivar für Entry-Zuordnung; BotanicalFamily für Kompatibilitäts-Check | **HOCH** |
| **REQ-002** (Standort/Substrat) | Location für `run_at_location`; SubstrateBatch für `run_uses_substrate`; Slot für Pflanzen-Platzierung | **HOCH** |
| **REQ-003** (Phasensteuerung) | GrowthPhase, PhaseTransitionRule für Batch-Phasenübergänge; `current_phase`-Edge | **HOCH** |

### Wird benötigt von:

| Modul | Nutzung | Priorität |
|-------|---------|-----------|
| **REQ-006** (Aufgabenplanung) | Run-basierte Task-Generierung (z.B. "Alle Tomaten im Run gießen") | **MITTEL** |
| **REQ-007** (Erntemanagement) | `run_produced`-Edge für Batch-Ernte; Seed-to-Shelf-Traceability via PlantingRun | **HOCH** |
| **REQ-009** (Dashboard) | Run-Übersicht als Dashboard-Widget; Phasen-Verteilung pro Run visualisieren | **MITTEL** |
| **REQ-010** (IPM) | Run-weite IPM-Inspektionen; Befallsausbreitung innerhalb eines Runs tracken | **NIEDRIG** |

### Grapherweiterungen am Named Graph `kamerplanter_graph`:

```json
{
    "new_document_collections": ["planting_runs", "planting_run_entries"],
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
        }
    ]
}
```

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **PlantingRun-CRUD:** Erstellen, Lesen, Aktualisieren, Löschen von Pflanzdurchläufen funktioniert
- [ ] **Entry-Management:** Entries können hinzugefügt, bearbeitet und entfernt werden (nur im Status `planned`)
- [ ] **Typ-Validierung:** Monokultur/Clone erfordern genau 1 Entry; Mischkultur erfordert ≥ 2 Entries mit korrekten Rollen
- [ ] **Clone-Validierung:** `source_plant_key` ist Pflicht bei Clone-Runs und wird gegen existierende PlantInstance geprüft
- [ ] **Quantity-Konsistenz:** Summe der Entry-Quantities muss `planned_quantity` entsprechen
- [ ] **Status-State-Machine:** Nur erlaubte Übergänge (planned→active→harvesting→completed; +cancelled) möglich
- [ ] **Batch-Erstellung:** `create-plants` erzeugt N PlantInstances mit auto-generierten IDs und `run_contains`-Edges
- [ ] **ID-Generierung:** Pflanzen-IDs folgen dem Schema `{LOCATION}_{PREFIX}_{SEQ:02d}` ohne Kollisionen
- [ ] **Batch-Phasenübergang:** `batch-transition` führt berechtigte Pflanzen zur Ziel-Phase über; nicht-berechtigte werden mit Begründung übersprungen
- [ ] **Batch-Ernte:** `batch-harvest` erstellt eine `Batch`-Node (REQ-007), verknüpft über `run_produced`-Edge
- [ ] **Batch-Entfernung:** `batch-remove` setzt `removed_on` auf allen aktiven Pflanzen und schließt den Run als `completed` ab
- [ ] **Individuelle Abtrennung:** `detach` setzt `detached_at` und `detach_reason` auf der `run_contains`-Edge, Pflanze bleibt bestehen
- [ ] **Keine Doppelzugehörigkeit:** Eine PlantInstance kann nur zu maximal einem aktiven PlantingRun gehören
- [ ] **Mischkultur-Validierung:** Kompatibilitäts-Check nutzt Spezies-Level und Familien-Level Fallback (Score × 0.8)
- [ ] **Seed-to-Shelf:** Von Batch über `run_produced` → PlantingRun → Entries → Species/Cultivar lückenlos navigierbar
- [ ] **Graph-Integration:** Alle 7 neuen Edge Collections korrekt im Named Graph `kamerplanter_graph` registriert
- [ ] **NFR-006-Fehlerbehandlung:** Aussagekräftige Fehlermeldungen bei Validierungsfehlern und Konfliktzuständen

### Testszenarien:

**Szenario 1: Monokultur — Vollständiger Lebenszyklus**
```
GIVEN: Species "Solanum lycopersicum", Cultivar "San Marzano", Location "Hochbeet A"
WHEN: Nutzer erstellt PlantingRun (type: monoculture, planned_quantity: 20)
  UND ruft create-plants auf
THEN:
  - Run-Status wechselt von "planned" → "active"
  - 20 PlantInstances mit IDs HOCHBEETA_TOM_01…20 werden erstellt
  - 20 run_contains-Edges (detached_at: null) verbinden Run mit Pflanzen
  - Alle Pflanzen sind in der initialen Wachstumsphase
  - actual_quantity des Runs = 20
```

**Szenario 2: Klon-Durchlauf mit Mutterpflanzen-Referenz**
```
GIVEN: Mutterpflanze "GROWZELT1_MOTHER_WW01" existiert als PlantInstance
WHEN: Nutzer erstellt PlantingRun (type: clone, source_plant_key: "GROWZELT1_MOTHER_WW01")
THEN:
  - Run wird mit source_plant_key gespeichert
  - create-plants erzeugt 10 PlantInstances mit IDs GROWZELT1_WW3_01…10
  - Alle Klone sind zur Mutterpflanze rückverfolgbar
WHEN: Nutzer versucht Clone-Run ohne source_plant_key zu erstellen
THEN:
  - Validierungsfehler 422: "Clone-Durchläufe erfordern source_plant_key"
```

**Szenario 3: Mischkultur — Kompatibilitäts-Prüfung**
```
GIVEN: PlantingRun (type: mixed_culture) mit Entries:
       - Solanum lycopersicum (primary, 8)
       - Ocimum basilicum (companion, 12)
       - Tagetes patula (trap_crop, 6)
WHEN: Nutzer ruft validate-compatibility auf
THEN:
  - System prüft alle Paar-Kombinationen (3 Paare)
  - Tomate ↔ Basilikum: COMPATIBLE (Spezies-Level oder Familien-Level Fallback)
  - Tomate ↔ Tagetes: Ergebnis abhängig von vorhandenen Kompatibilitätsdaten
  - Basilikum ↔ Tagetes: Ergebnis abhängig von vorhandenen Kompatibilitätsdaten
  - Overall-Status und Empfehlungen werden zurückgegeben
```

**Szenario 4: Batch-Phasenübergang mit Ausschlüssen**
```
GIVEN: PlantingRun "Tomaten Hochbeet A" mit 20 Pflanzen, davon:
       - 18 in Phase "vegetative"
       - 1 in Phase "flowering" (manuell vorgezogen)
       - 1 explizit ausgeschlossen (exclude_plant_keys)
WHEN: Nutzer ruft batch-transition (target_phase: "flowering") auf
THEN:
  - 18 Pflanzen werden zu "flowering" überführt
  - 1 Pflanze übersprungen: "Bereits in Phase 'flowering'"
  - 1 Pflanze übersprungen: "Explizit ausgeschlossen"
  - Response: transitioned_count=18, skipped_count=2
```

**Szenario 5: Batch-Ernte mit Seed-to-Shelf-Traceability**
```
GIVEN: Aktiver PlantingRun mit 20 Tomaten-Pflanzen in Phase "ripening"
WHEN: Nutzer ruft batch-harvest (harvest_type: "final", wet_weight_g: 12500) auf
THEN:
  - Neuer Batch (REQ-007) wird erstellt mit batch_id "RUN_TOMATEN_HOCHBEET_A_2025_20250915_01"
  - run_produced-Edge verbindet Run mit Batch (plant_count: 20)
  - Run-Status wechselt zu "completed"
  - Rückverfolgung: Batch → PlantingRun → Entries → Species (San Marzano) → Location (Hochbeet A)
```

**Szenario 6: Individuelle Pflanze vom Run abtrennen**
```
GIVEN: PlantingRun mit 20 Pflanzen, Pflanze HOCHBEETA_TOM_05 zeigt Krankheitssymptome
WHEN: Nutzer ruft detach (plant_key: "HOCHBEETA_TOM_05", reason: "Braunfäule-Verdacht") auf
THEN:
  - run_contains-Edge wird mit detached_at und detach_reason aktualisiert
  - Pflanze HOCHBEETA_TOM_05 bleibt als PlantInstance bestehen (nicht gelöscht)
  - Pflanze kann weiterhin individuell verwaltet werden (IPM-Behandlung, etc.)
  - Run zeigt active_plant_count: 19
```

**Szenario 7: Typ-Constraint-Verletzungen**
```
GIVEN: Kein bestehender PlantingRun
WHEN: Nutzer versucht Monokultur-Run mit 2 Entries zu erstellen
THEN:
  - Validierungsfehler 422: "monoculture-Durchläufe erlauben genau 1 Entry, erhalten: 2"

WHEN: Nutzer versucht Mischkultur-Run mit nur 1 Entry (role: primary) zu erstellen
THEN:
  - Validierungsfehler 422: "Mischkultur-Durchläufe erfordern mindestens 2 Entries"

WHEN: Nutzer versucht Mischkultur-Run mit 2 Entries (beide role: primary) zu erstellen
THEN:
  - Validierungsfehler 422: "Mindestens ein Entry muss die Rolle 'companion' oder 'trap_crop' haben"

WHEN: Nutzer versucht PlantingRun mit Entries (quantity: 8 + 12) aber planned_quantity: 25 zu erstellen
THEN:
  - Validierungsfehler 422: "Summe der Entry-Quantities (20) muss planned_quantity (25) entsprechen"
```

---

**Hinweise für RAG-Integration:**
- Keywords: Pflanzdurchlauf, Planting Run, Batch-Operation, Gruppenmanagement, Monokultur, Klon, Mischkultur, Batch-Erstellung, Batch-Phasenübergang, Batch-Ernte, Batch-Entfernung, Seed-to-Shelf, Traceability
- Fachbegriffe: PlantingRun, PlantingRunEntry, Mutterpflanze, Steckling, Companion Planting, Trap Crop, HarvestBatch, State Machine, Detach, ID-Generierung
- Verknüpfung: Baut auf REQ-001 (Species/Cultivar), REQ-002 (Location/Substrate), REQ-003 (Phasensteuerung) auf; liefert an REQ-007 (Batch-Ernte), REQ-006 (Run-Tasks), REQ-009 (Dashboard), REQ-010 (IPM)
