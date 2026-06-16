# Kamerplanter Inference Service

Self-hosted Pflanzen-Bilderkennung via **DINOv2-Embedding-Matching** gegen einen
kuratierten Referenz-Index (REQ-029-A, Aufgabe A). Der Service kapselt sowohl
die Embedding-Berechnung (ONNX Runtime, DINOv2 ViT-S/14) als auch die
Vektorsuche (pgvector / PostgreSQL). Er ist **intern** (ClusterIP) und wird vom
Hauptbackend ausschliesslich per HTTP angesprochen.

> **Architektur-Entscheidung (D-2/D-3):** Der Vektor-Store ist **pgvector**,
> nicht ArangoDB. Der inference-service besitzt die Tabelle
> `species_embeddings` exklusiv -- analog zum `knowledge-service`, der seine
> eigene pgvector-Connection haelt.

## Aufbau

```
src/inference-service/
  app/
    main.py            FastAPI + lifespan, Endpunkte, Singletons
    config.py          pydantic-settings (MODEL_*, VECTORDB_*, CONFIDENCE_*)
    preprocessing.py   Preprocessing-Contract (REQ-029-A 3.2) -- single source of truth
    embedder.py        ONNX InferenceSession, non-blocking Startup-Load, L2-Norm
    confidence.py      cosine_to_confidence() (REQ-029-A 3.5)
    schemas.py         Pydantic Request/Response-Modelle
    vectordb/
      connection.py    psycopg ConnectionPool
      schema.py        Migrations-Runner (inference_schema_migrations-Tracking)
      repository.py     upsert_reference / match / delete_by_species
      migrations/001_species_embeddings.sql
  scripts/
    export_dinov2_onnx.py   ONNX-Export (nicht im CI/Build des Service ausgefuehrt)
  tests/               pytest (Preprocessing-Determinismus, Confidence, /match, Health)
  Dockerfile / Dockerfile.dev / requirements.txt / pyproject.toml
```

## Preprocessing-Contract (VERBINDLICH)

`app/preprocessing.py` ist die **einzige Quelle der Wahrheit** fuer die
Bildvorverarbeitung. Referenz- und Query-Bilder MUESSEN exakt gleich
vorverarbeitet werden, sonst ist das Matching wertlos (REQ-029-A 3.2):

1. EXIF-Orientierung anwenden + RGB-Konvertierung (strippt Metadaten)
2. Resize kuerzere Kante auf `INPUT_SIZE` (224), Center-Crop 224x224
3. `/255.0`, ImageNet-Norm `(x - MEAN) / STD`
4. HWC -> CHW, Batch-Dim, float32 -> `(1, 3, 224, 224)`

Der Transform ist deterministisch: gleiche Bytes ergeben immer dasselbe Array.

## ONNX-Modell exportieren

Der Export ist ein **Build-Schritt**, kein Laufzeit-/CI-Schritt. `torch` wird
nur in der `model-export`-Stage des Dockerfiles benoetigt, nie im Runtime-Image.

```bash
pip install torch torchvision onnx
python scripts/export_dinov2_onnx.py --arch dinov2_vits14 --input-size 224 --output ./models/dinov2
```

Erzeugt:

- `models/dinov2/model.onnx` -- exportierter Graph
- `models/dinov2/modelinfo.json` -- `{ model, dim: 384, input_size: 224, license: "Apache-2.0", checksum }`

> **Lizenz-Hinweis (vor Produktivnahme RE-VERIFIZIEREN, REQ-029-A 2.3 / 5):**
> Das DINOv2-**Basis-Backbone** von Meta (`facebookresearch/dinov2`) ist
> Apache-2.0 (Meta hat von CC-BY-NC relizenziert). Pruefe das `LICENSE` im
> offiziellen Repo vor jedem Produktions-Build. Die PlantCLEF-2024-Fine-tune-
> Gewichte sind CC-BY-NC und duerfen **nicht** ausgeliefert werden.

Im Container-Build geschieht der Export automatisch (Multi-stage), das fertige
Artefakt wird in das Runtime-Image kopiert -- das Modell liegt nicht im Repo.

## HTTP-Endpunkte

Alle Endpunkte sind intern; Port **8000**.

| Methode | Pfad | Request | Response |
|---|---|---|---|
| POST | `/embed` | multipart `image` | `{ embedding: float[], dim, model }` |
| POST | `/embed/batch` | multipart `images[]` | `{ embeddings: float[][], dim, model, count }` |
| POST | `/match` | multipart `image`, query `k` (1-50, default 5) | `{ suggestions: [{rank, species_key, scientific_name, score, confidence}], is_plant, model }` |
| POST | `/reference` | Form `species_key, scientific_name, source` (+ optional `organ, source_record_id, license, attribution, source_url`) und ENTWEDER multipart `image` ODER Form `embedding` (JSON-Float-Array) | `{ status, species_key, dim, model }` |
| DELETE | `/reference/{species_key}` | -- | `{ status, species_key, deleted }` |
| GET | `/health` | -- | `{ status, model_loaded, vectordb }` (Liveness, immer 200) |
| GET | `/ready` | -- | `{ status: "ok" }` oder **503** wenn Modell/DB nicht bereit |
| GET | `/modelinfo` | -- | `{ model, dim, input_size, license: "Apache-2.0", checksum }` |

`/reference` persistiert **nur** den Embedding-Vektor + Provenienz/Lizenz --
**kein** Originalbild (REQ-029-A 4.4 / AE-5).

## Konfiguration (Env-Vars, fuer WS-6 Helm/Skaffold)

| Env-Var | Default | Beschreibung |
|---|---|---|
| `MODEL_PATH` | `/app/models/dinov2` | Verzeichnis mit `model.onnx` + `modelinfo.json` |
| `MODEL_NAME` | `dinov2_vits14` | Modellbezeichner (in Responses + Index-Filter) |
| `MODEL_DIM` | `384` | Embedding-Dimension (ViT-S/14) |
| `INPUT_SIZE` | `224` | Quadratische Eingabegroesse (Vielfaches von 14) |
| `VECTORDB_HOST` | `localhost` | pgvector Host |
| `VECTORDB_PORT` | `5432` | pgvector Port |
| `VECTORDB_DATABASE` | `kamerplanter_vectors` | DB-Name (geteilt mit knowledge-service, eigene Tabelle) |
| `VECTORDB_USERNAME` | `postgres` | DB-User |
| `VECTORDB_PASSWORD` | `changeme` | DB-Passwort (im Cluster aus Secret) |
| `VECTORDB_POOL_MIN_SIZE` | `1` | Pool min |
| `VECTORDB_POOL_MAX_SIZE` | `5` | Pool max |
| `CONFIDENCE_AUTO_ACCEPT` | `0.85` | Cosine-Schwelle "direkt vorschlagen" (REQ-029-A 3.5) |
| `CONFIDENCE_SHOW_RESULTS` | `0.10` | Cosine-Schwelle "in Liste zeigen" |

**Port:** 8000 (FastAPI/uvicorn). Probes: `/health` (Liveness), `/ready`
(Readiness, 503 bis Modell geladen + DB erreichbar).

> Schwellenwerte sind Settings, **keine** Literaturwerte -- sie werden in WS-7
> an den eigenen ~210 Arten gemessen und justiert (REQ-029-A 7).

## Tests

```bash
cd src/inference-service
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio
pytest
```

Die Tests laufen **ohne** Netzwerk und **ohne** echtes ONNX-Modell: der
Embedder wird gemockt bzw. die `/match`-Tests nutzen einen Fake-Repository-
Fixture. Wenn `onnxruntime` in der Sandbox nicht installierbar ist, wird der
echte ONNX-Pfad in den Tests nicht beruehrt (nur das deterministische
Preprocessing, die Confidence-Mathematik und die FastAPI-Endpunkte mit
gemocktem Embedder/Repo).

## WS-3-Schnittstelle (LocalEmbeddingAdapter)

Der Backend-`LocalEmbeddingAdapter` (WS-3) ruft:

- `POST /match` (Bild -> Top-k `species_key` + `confidence`) im Identify-Pfad
- `POST /reference` und `POST /embed/batch` in der Beschaffungs-Pipeline (WS-4)
- `GET /ready` fuer `health_check()`
