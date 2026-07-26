# Datenbank-Migrationen & Seeds — Autoren-Leitfaden

Verbindliche Grundlage: **ADR-005** (`spec/decisions/ADR-005-versioned-migration-framework.md`)
und **NFR-016** (`spec/nfr/NFR-016_Datenbank-Migrationsstrategie.md`). Dieser
Leitfaden fasst die Praxis zusammen; im Konfliktfall gelten ADR-005 / NFR-016.

## Migration vs. Seed — die zentrale Abgrenzung

| | **Migration** | **Seed** |
|---|---|---|
| Zweck | Einmalige Transformation **bestehender** Daten/Struktur | Idempotenter Upsert von **Referenzdaten** (YAML → DB) |
| Ausführung | **Genau einmal** pro DB (in `schema_migrations` getrackt) | Bei **jedem** Startup |
| Ort | `versions/vNNNN_<slug>.py` | `seed_*.py` + Eintrag in `seeds/registry.py` |
| Reihenfolge | Strikt linear, versioniert | Deklarative Registry-Reihenfolge |
| Fehler-Policy | **Fatal** — Startup bricht ab | Referenzdaten **non-fatal**, strukturell notwendige `fatal=True` |
| Beispiel | `retire_harvest_phase`, `backfill_tenant_key` | `seed_plagron`, `seed_plant_info` |

Faustregel: Transformierst du **vorbestehende** Nutzerdaten? → Migration.
Lädst/aktualisierst du **Referenzdaten aus dem Repo**? → Seed. Reconcilest du
Daten, die **andere Seeds** gerade erzeugt haben (z. B. Edges zwischen zwei
Seed-Outputs)? → **Seed** (Post-Seed-Schritt in der Registry), keine Migration —
siehe `lifecycle_to_phase_sequence_reconcile`.

## Startup-Verdrahtung

`app/main.py` (`lifespan`) ruft nach `ensure_collections(db)` genau zwei Dinge auf
(NFR-016 O-1 — erst Migrationen, dann Seeds):

```python
run_pending_migrations(db)  # versioniert, getrackt, mit Lock — FATAL bei Fehler
run_seeds(db)  # Registry, je Seed isoliert — Referenzdaten non-fatal
```

## Eine neue Migration schreiben

1. **Scaffolden:**

   ```bash
   cd src/backend
   python -m app.migrations create <slug>   # z. B. retire_legacy_flag
   ```

   Erzeugt die nächste `versions/vNNNN_<slug>.py` aus der Vorlage (up/down-Stubs,
   `MigrationReport`, Docstring). Versionsnummer = höchste bestehende + 1,
   nullgepolstert.

2. **`up(db, *, dry_run=False)` implementieren.** Pflichten:
   - **Idempotent (M-3):** Nur Dokumente anfassen, die noch geändert werden
     müssen. Ein Re-Run MUSS ein No-op sein (`report.changed == 0`).
   - **Dry-Run (M-5):** Bei `dry_run=True` den Report berechnen, aber **nichts**
     schreiben.
   - **Parametrisiert (Sicherheit):** AQL immer mit `bind_vars`, nie mit
     f-Strings über Nutzerdaten interpolieren.
   - **Report zurückgeben:** `MigrationReport(version, name, scanned, changed,
     dry_run, details=...)`.

3. **Reversibilität ehrlich deklarieren (M-6):** Standard ist `reversible = False`
   und ein `down`, das `IrreversibleMigrationError` wirft. Nur wenn du die
   Transformation wirklich umkehren kannst, `reversible = True` setzen und `down`
   implementieren.

4. **Enum-/Feld-Rückbau (M-9):** Wird ein persistierter Enum-Wert oder ein Feld
   entfernt/umbenannt, MUSS **dieselbe** Änderung eine Migration mitliefern, die
   Bestandsdokumente überführt (Lehre aus Issue #306).

5. **Bestehende Logik wiederverwenden:** Große Transformationen dürfen als reine
   Funktion in einem eigenen Modul liegen; der Version-Wrapper ruft sie nur auf
   (siehe `v0002`–`v0005`). Logik **nicht** duplizieren.

6. **Unveränderlichkeit (M-7):** Eine bereits angewandte Migration wird **nie**
   editiert — Korrekturen kommen als **neue** Version. Der Framework-Checksum
   (SHA-256 des `up`-Quelltexts) erkennt Drift und warnt beim Start.

7. **Test beilegen:** Unter `tests/unit/migrations/versions/` — mindestens ein
   Smoke-Test (up idempotent/No-op, dry-run schreibt nicht, down verhält sich
   gemäß Reversibilität).

## Eine neue Seed schreiben

1. `seed_<name>.py` mit idempotentem Upsert (S-1). Unbekannte Quellfelder mit
   Warnung überspringen, nicht die ganze Datei verwerfen (S-3).
2. In `seeds/registry.py` einen `SeedJob` an der korrekten Stelle ergänzen.
   Signatur vereinheitlichen: der Job wird immer als `run(db)` aufgerufen — Seeds
   ohne Argument via `lambda db: run_seed_x()` kapseln.
3. **`fatal`** nur setzen, wenn der Seed strukturell notwendig ist
   (z. B. Location-Types, Auth-Bootstrap). Referenzdaten bleiben `fatal=False` (S-2).

## CLI-Referenz (NFR-016 O-2)

```bash
cd src/backend
python -m app.migrations upgrade                 # alle ausstehenden anwenden
python -m app.migrations upgrade --to 0004       # bis Version 0004 (inkl.)
python -m app.migrations upgrade --dry-run       # nur Report, nichts schreiben
python -m app.migrations downgrade --to 0003     # bis 0003 zurückrollen
python -m app.migrations downgrade --to 0003 --dry-run
python -m app.migrations current                 # höchste angewandte Version
python -m app.migrations history                 # angewandte Migrationen + Zeitstempel
python -m app.migrations create <slug>           # nächste Migration scaffolden
```

## Concurrency & Ops

- **Lock (M-8):** `upgrade`/`downgrade` laufen unter einem `__lock__`-Dokument in
  `schema_migrations`. Ein zweiter Runner wird blockiert; `run_pending_migrations`
  überspringt bei gehaltenem Lock (der gewinnende Runner migriert). Ein Lock, das
  älter als 5 Minuten ist, gilt als verwaist und wird übernommen.
- **Zielbild (O-3):** Migrationen sollen mittelfristig als dediziertes
  Kubernetes-Job / Helm-Hook laufen (nicht in jedem App-Pod). Der
  CLI-Entrypoint `python -m app.migrations upgrade` ist die Grundlage; bis dahin
  schützt der Lock den Startup-Pfad.
