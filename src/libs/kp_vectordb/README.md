# kp_vectordb — geteilte pgvector-Infrastruktur

Single source of truth für die **Infrastruktur-Schicht** des pgvector-Zugriffs,
die zuvor doppelt unter `knowledge-service` und `inference-service` lag
(Code-Review AP-18c / Befund INF-D1).

Dedupliziert wird ausschließlich die generische Infrastruktur:

| Modul | Inhalt |
|-------|--------|
| `config.py` | `VectorDbConfig` — unveränderliches Verbindungs-Datenobjekt (ohne Passwort-Default) |
| `connection.py` | `VectorDbConnection` — psycopg-Connection-Pool-Verwaltung |
| `schema.py` | `run_migrations(pool, migrations_dir, *, migrations_table=...)` — idempotenter Migrations-Runner |

**Bewusst NICHT geteilt** (fachlich verschieden, bleiben pro Service):
`repository.py` (knowledge-service: Hybrid-Volltext/Umlaut-Logik),
`repository.py` + `pest_repository.py` (inference-service: Embedding-Lookups)
sowie die service-eigenen `migrations/`-Verzeichnisse und Tracking-Tabellen
(`schema_migrations` vs. `inference_schema_migrations`).

## Verteilungsmodell (Variante B — Sync statt geteilter Build-Context)

Die Docker-Build-Contexte bleiben pro Service (`src/knowledge-service`,
`src/inference-service`) **unverändert**. Die drei Module oben werden von hier
**byte-identisch** in `app/vectordb/` jedes Service kopiert. Damit bleibt der
Build risikolos (kein Umbau des mehrstufigen inference-service-Images, kein
Verschieben der `.dockerignore`, keine Änderung der Publish-Pipeline).

Warum nicht Variante A (geteiltes Paket via angehobenem Build-Context):
Der inference-service nutzt einen mehrstufigen Build mit ONNX-Model-Export und
eine context-lokale `.dockerignore` (schließt `models/`, `*.onnx`, `tests/`
aus). Ein angehobener Context (`src/`) würde diese `.dockerignore` still
unwirksam machen und alle `COPY scripts/...`-Pfade brechen — plus Anpassungen
an der fragilen `:latest`-Publish-Pipeline. Das übersteigt den Nutzen der
reinen Byte-Deduplizierung. Variante B dedupliziert die **Pflege** und sichert
sie per Drift-Guard ab.

### Workflow

Quelle bearbeiten (immer nur hier!), dann verteilen:

```bash
python src/libs/kp_vectordb/sync.py          # Kopien schreiben
python src/libs/kp_vectordb/sync.py --check   # nur prüfen (CI), Exit != 0 bei Drift
```

Der Drift wird zusätzlich in beiden Service-Test-Suites erzwungen
(`tests/test_vectordb_sync_guard.py`) — ein bestehender CI-Job schlägt fehl,
sobald eine Kopie von der Quelle abweicht. Es ist kein neuer CI-Job nötig.

**Regel:** Niemals `app/vectordb/{config,connection,schema}.py` direkt in einem
Service editieren — immer hier ändern und `sync.py` laufen lassen.

## Tests

```bash
cd src/libs/kp_vectordb && python -m pytest
```

Deckt Identifier-Validierung, Tabellennamen-Parametrisierung,
Kommentar-Stripping/Statement-Splitting des Migrations-Runners sowie die
Conninfo-Konstruktion des Connection-Pools ab (ohne echte Datenbank).
