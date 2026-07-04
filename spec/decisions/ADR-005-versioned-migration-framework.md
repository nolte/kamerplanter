# ADR-005: Versioniertes Datenbank-Migrations-Framework

## Status

**Accepted** — *Entschieden: 2026-07-04, durch nolte*
*Erstellt: 2026-07-04*

## Context

Datenbank-Seeds und -Migrationen wurden bisher als lose Sammlung von Funktionen
in `app/migrations/` geführt und **einzeln, hartkodiert und ungeordnet** im
FastAPI-`lifespan` (`app/main.py`) aufgerufen — rund 18 Aufrufe hintereinander,
die bei **jedem** Startup laufen. Es fehlten:

1. **Tracking** — keine Aufzeichnung, welche Migration auf einer DB bereits lief.
   Jede Migration läuft bei jedem Start erneut; Korrektheit hängt allein an der
   Idempotenz jedes einzelnen Skripts.
2. **Fehler-Isolation** — eine einzige Exception in irgendeinem Skript bricht den
   **gesamten** Startup ab (`Application startup failed. Exiting.`, Pod `0/1`).
3. **Deklarierte Reihenfolge / Abhängigkeiten** — die Ordnung steckt implizit in
   der `main.py`-Aufrufsequenz; ein Umsortieren ist unsichtbar riskant.
4. **Einheitliche Konventionen** — mal `run_migrate_X()`, mal `run(db, dry_run)`,
   uneinheitliche Report-Typen, kein Standard für `--dry-run`.
5. **Versionierung / Rollback** — kein Konzept für „welcher Stand liegt vor",
   kein kontrolliertes Vor-/Zurückrollen für Ops.

Diese Lücken schlugen real zu: Am 2026-07-04 crashte der Backend-Pod zweimal beim
Startup — einmal an einem seit Issue #306 abgeschafften Enum-Wert (`harvest`), für
den **keine Daten-Migration** existierte und den der Seed-Read strikt validierte;
danach an einem SSRF-geblockten HA-Endpoint. Beide Male riss ein einzelner Schritt
den ganzen Startup mit (siehe NFR-016 §Motivation).

**Constraints:**
- **Polyglot-Persistenz, ArangoDB als Primär-DB** (ADR-001): schemalos, kein
  Alembic/SQL-DDL. Ein Migrations-Framework muss ArangoDB-nativ (AQL) sein.
- **ADR docs/005** („YAML-Seed-Jobs beim Startup"): idempotente Referenzdaten-Seeds
  laufen bewusst bei jedem Startup — dieses Muster bleibt gültig und wird von
  einmaligen Migrationen **abgegrenzt**, nicht ersetzt.
- **Mehrere Backend-Replicas in Prod** (NFR-002): paralleler Startup mehrerer Pods
  darf keine doppelte/konkurrierende Migrationsausführung auslösen.

## Decision

Wir führen ein **versioniertes, getracktes Migrations-Framework** ein und trennen
sauber zwischen **Migrationen** (einmalig, versioniert) und **Seeds** (idempotent,
immer laufend).

### 1. Begriffliche Trennung Migration vs. Seed

| | **Migration** | **Seed** |
|---|---|---|
| Zweck | Einmalige Transformation **bestehender** Daten/Struktur | Laden/Upsert von **Referenzdaten** (YAML → DB) |
| Ausführung | **Genau einmal** pro DB (getrackt) | Bei **jedem** Startup (idempotent) |
| Reihenfolge | Strikt linear, versioniert | Deklarierte Registry-Reihenfolge |
| Fehler-Policy | **Fatal** (Startup bricht ab) | Strukturell fatal, Referenzdaten **non-fatal** |
| Beispiele | `retire_harvest_phase`, `backfill_tenant_key` | `seed_plagron`, `seed_plant_info` |

### 2. Verzeichnisstruktur

```
app/migrations/
  framework/
    base.py        # Migration-Protokoll: version, name, up(db), down(db), reversible
    runner.py      # MigrationRunner: plan / upgrade / downgrade / current / history
    tracking.py    # schema_migrations-Collection: record/query, Lock
    discovery.py   # lädt versions/vNNNN_*.py sortiert
    report.py      # einheitliche MigrationReport-Dataclass
    cli.py         # python -m app.migrations <cmd>
  versions/
    v0001_baseline.py                 # No-op-Baseline (markiert Pre-Framework-DBs)
    v0002_fertilizer_calmag_type.py
    v0003_normalize_photo_refs.py
    v0004_lifecycle_to_phase_sequence.py
    v0005_backfill_tenant_key.py
    v0006_retire_harvest_phase.py
  seeds/
    registry.py    # geordnete SeedJob-Liste + run_seeds(db) mit Fehler-Isolation
  seed_*.py        # bestehende Seed-Funktionen bleiben (Logik unverändert)
```

### 3. Tracking-Collection `schema_migrations`

Ein Dokument je angewandter Version:

```json
{ "_key": "0006", "version": "0006", "name": "retire_harvest_phase",
  "checksum": "<sha256 des up()-Quelltexts>", "applied_at": "<iso8601>",
  "duration_ms": 42, "status": "applied" }
```

- **Checksum-Drift-Erkennung:** Weicht die aktuelle Prüfsumme einer bereits
  angewandten Version vom aufgezeichneten Wert ab (Migration nachträglich
  editiert), wird eine **Warnung** geloggt — angewandte Migrationen sind
  unveränderlich.
- **Concurrency-Lock:** Ein `_key: "__lock__"`-Dokument (Insert schlägt bei
  Existenz fehl → nur ein Runner gewinnt) mit TTL/`acquired_at`. Konkurrierende
  Replicas warten bzw. überspringen. Verhindert Doppelausführung bei parallelem
  Pod-Start.

### 4. Migration-Protokoll & Runner

```python
class Migration:
    version: str            # "0006" — nullgepolstert, streng monoton
    name: str
    description: str
    reversible: bool = False
    def up(self, db) -> MigrationReport: ...
    def down(self, db) -> MigrationReport: ...   # sonst IrreversibleMigrationError
```

- **Strikt lineare History:** Ausstehende Versionen müssen ein lückenloses Suffix
  bilden. Eine unangewandte Version **vor** dem aktuellen Head ist ein Fehler
  (kein Out-of-order-Apply).
- **Runner-API:** `upgrade(db, target=None, dry_run=False)`,
  `downgrade(db, target, dry_run=False)`, `current(db)`, `history(db)`, `plan(db)`.
- **Rollback:** `down()` wird unterstützt; datentransformierende Migrationen
  deklarieren i. d. R. `reversible=False` und werfen `IrreversibleMigrationError`
  (ehrlich statt scheinbar-reversibel). Baseline-`down` ist ein No-op.

### 5. Baseline & Konvertierung der Bestands-Migrationen

Die vier bestehenden `migrate_*` plus `backfill_tenant_key` werden als
versionierte Migrationen `v0002`–`v0006` gekapselt (die reine Logik bleibt in den
bestehenden Modulen, die Version-Wrapper rufen sie auf). `v0001_baseline` ist ein
No-op-Marker. Da **alle** Bestands-Migrationen idempotent sind, ist der einmalige
Re-Run beim ersten Framework-Start auf einer Bestands-DB ein sicherer No-op, der
sie lediglich in `schema_migrations` einträgt.

### 6. Startup-Verdrahtung & Ausführungsort

`main.py` schrumpft auf zwei Aufrufe:

```python
run_pending_migrations(db)   # versioniert, getrackt, mit Lock — FATAL bei Fehler
run_seeds(db)                # Registry, je Seed isoliert — Referenzdaten non-fatal
```

- **Interim (jetzt):** Migrationen laufen weiter im `lifespan`, aber mit Lock und
  strikter Ordnung. Kompatibel zum bestehenden Seed-beim-Startup-Muster (docs/005).
- **Ziel (Folgearbeit):** Migrationen als **dediziertes Kubernetes-Job / Helm
  pre-upgrade-Hook** (nicht in jedem App-Pod), sodass App-Replicas nie migrieren.
  Der CLI-Entrypoint (`python -m app.migrations upgrade`) ist dafür bereits die
  Grundlage. Bis dahin schützt der Lock vor Replica-Races.

### 7. Autoren-Workflow

`python -m app.migrations create <slug>` scaffoldet die nächste
`vNNNN_<slug>.py` aus einer Vorlage (up/down-Stubs, Report, Docstring). Regeln:
idempotent schreiben, `--dry-run` unterstützen, Unit-Test unter
`tests/unit/migrations/versions/` beilegen. Details im Autoren-Leitfaden
`app/migrations/README.md` und normativ in NFR-016.

## Alternatives Considered

- **Leichtgewichtige Registry ohne Versionierung** (nur Fehler-Isolation +
  Tracking einmaliger Migrationen, Seeds always-run). Verworfen: der explizite
  Wunsch nach versionierter, rollback-fähiger History mit reproduzierbarem
  „welcher Stand liegt vor" ist damit nicht erfüllbar.
- **Reine Konventionen/Doku ohne Framework-Code.** Verworfen: löst die realen
  Startup-Crashes (fehlende Fehler-Isolation, kein Tracking) nicht.
- **Bestehendes Tool (Alembic/yoyo/…).** Verworfen: Alembic ist SQL/SQLAlchemy-
  gebunden; ArangoDB ist schemalos und AQL-basiert. Ein schlankes ArangoDB-natives
  Framework (~300 LOC) ist passgenauer als ein SQL-Tool zu verbiegen.
- **Migrationen ausschließlich als externes Job, nie im Startup.** Als **Zielbild**
  übernommen (§6), aber nicht als Sofort-Bruch: der Startup-Pfad mit Lock bleibt
  interim erhalten, um Dev-Workflow und docs/005-Muster nicht zu brechen.

## Consequences

- **Positiv:** Ein fehlgeschlagener Referenzdaten-Seed reißt den Startup nicht mehr
  mit (Fehler-Isolation); einmalige Migrationen laufen genau einmal, getrackt und
  geordnet; der DB-Stand ist per `current`/`history` inspizierbar; Replica-Races
  sind durch den Lock ausgeschlossen; `main.py` ist von ~90 Zeilen Inline-Aufrufen
  befreit; neue Migrationen folgen einem einheitlichen, getesteten Muster.
- **Negativ / Kosten:** Zusätzliche Framework-Komplexität (~300 LOC + Tests); eine
  neue Collection `schema_migrations`; Autoren müssen die Versionierungs- und
  Idempotenz-Regeln einhalten; die meisten Datentransformationen bleiben
  faktisch irreversibel (`down()` wirft) — Rollback ist kein Allheilmittel.
- **Folgemaßnahmen:** NFR-016 (neu) macht die Strategie normativ; docs/adr/005 wird
  um die Migration-vs-Seed-Abgrenzung ergänzt; als Folgearbeit die Migrationen in
  ein dediziertes K8s-Job/Helm-Hook auslagern (§6 Zielbild).

## Realisierung

- Backend: `app/migrations/framework/*` (base, runner, tracking, discovery, report,
  cli), `app/migrations/versions/v0001..v0006`, `app/migrations/seeds/registry.py`,
  `app/data_access/arango/collections.py` (Collection `schema_migrations`),
  `app/main.py` (Verdrahtung), `app/migrations/README.md` (Autoren-Leitfaden).
- Tests: `tests/unit/migrations/framework/` (Runner-Ordering, Tracking, Lock,
  Checksum-Drift, dry-run, downgrade/irreversibel), `tests/unit/migrations/versions/`.
- Doku: NFR-016, docs/{de,en}/adr/009-versioned-migration-framework.md.

## References

- NFR-016 Datenbank-Migrationsstrategie (normative Anforderung)
- ADR-001 ArangoDB als Multi-Modell-Datenbank (schemalose Persistenz)
- docs/adr/005 YAML-basierte Seed-Jobs beim Startup (abgegrenztes Seed-Muster)
- Issue #306 (Abschaffung der `harvest`-Phase — auslösender Incident)
- NFR-002 Kubernetes-Plattform (Replicas, Job/Hook-Zielbild), NFR-007 Betriebsstabilität
