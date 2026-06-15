# Umsetzungsplan — DINOv2 Self-Hosted Bilderkennung (REQ-029-A, Aufgabe A)

> **Branch:** `feat/dinov2-recognition` (von `develop` geforkt)
> **Quelle:** `spec/req/REQ-029-A_Self-Hosted-Bilderkennung-Referenzbild-Beschaffung.md` (v1.0),
> `spec/req/REQ-029_KI-Bilderkennung-Pflanzenidentifikation.md` (v1.0, Adapter-/Consent-/Frontend-Bausteine)
> **Stand:** 2026-06-15

## 0. Entscheidungen (Weichenstellungen)

| # | Entscheidung | Begründung |
|---|---|---|
| D-1 | **Phase-1-Basis wird in diesem Branch mitgebaut** | `feat/plant-identification` ist noch nicht in `develop`; der Branch wird self-contained. Adapter-Interface, Registry, `IdentificationService`, Request-Collections, Consent-Purpose, EXIF, Frontend-Dialog + `PlantNetAdapter`-Fallback werden hier neu implementiert. **Risiko:** Merge-Konflikt mit `feat/plant-identification` — Mitigation in §6. |
| D-2 | **Vektor-Store = pgvector** (statt ArangoDB `species_embeddings`) | pgvector (PostgreSQL 18, HNSW, Cosine) ist im `kamerplanter-ki`-Stack bereits deployt und produktionserprobt. ArangoDB 3.12.9 kann `APPROX_NEAR_COSINE` nur experimentell. **Abweichung von REQ-029-A §5 — Spec muss in §5.4 nachgezogen werden.** |
| D-3 | **`inference-service` kapselt Embedding *und* Vektorsuche** | Analog `knowledge-service` (besitzt pgvector-Connection, bietet `/search`). Hauptbackend bleibt frei von psycopg und spricht den Service nur per HTTP. |
| D-4 | **Scope = nur Aufgabe A (Artbestimmung)** | Aufgabe B (Krankheit/PlantDoc) und C (Phänologie) bleiben Backlog (`REQ-029-A §6`). |

## 1. Architektur (Ist → Soll)

```
React UI (PlantIdentificationDialog, NEU)
   │  multipart Foto + organ + Consent-Check
   ▼
Backend FastAPI  /api/v1/t/{slug}/identification/identify
   │  EXIF-Strip → IdentificationService → AdapterRegistry.get_preferred()
   ├─ Prio 1: LocalEmbeddingAdapter ───HTTP──▶ inference-service  POST /match
   │                                              │  preprocess → ONNX DINOv2 → Embedding
   │                                              │  → pgvector HNSW Top-k
   │                                              ▼  { species_key, score }[]
   │           ← reichert species_key mit ArangoDB-Stammdaten an
   └─ Prio 2: PlantNetAdapter (Fallback, Consent + Key, ≤500/Tag)

Beschaffung (Celery, Backend):
   GBIF Media-API → CC0/CC-BY-Filter → Kuratierung → inference-service /embed/batch
   → inference-service /reference (schreibt Embedding+Provenienz in pgvector)
   → reference_image_jobs (ArangoDB, Abdeckungs-Report)
```

**Komponenten-Eigentum:**
- `inference-service` (NEU, `src/inference-service/`): ONNX-Inferenz + pgvector-Tabelle `species_embeddings` + Vektorsuche. Zustandsbehaftet bzgl. pgvector, sonst stateless. ClusterIP-intern.
- Hauptbackend: Adapter, Service, API, Consent, EXIF, Beschaffungs-Celery-Task, `reference_image_jobs`-Protokoll (ArangoDB).
- pgvector-DB `kamerplanter_vectors`: neue Tabelle `species_embeddings` (eigene SQL-Migration im inference-service, getrennt vom knowledge-service-Schema).

## 2. Workstreams & Reihenfolge

### WS-1 — Phase-1-Basis (Voraussetzung, Backend)
Reihenfolge zuerst, da alles darauf aufbaut.

1. **Adapter-Interface** `src/backend/app/domain/interfaces/plant_identification_adapter.py`
   — ABC mit `identify()`, `diagnose()`, `health_check()`, Props `adapter_key`, `supports_health_assessment`, `rate_limit_per_day` (REQ-029 §3.1).
2. **DTOs** `IdentificationSuggestion`, `IdentificationResult`, `PlantOrgan`-Enum (domain/models).
3. **Registry** `IdentificationAdapterRegistry` (domain/services) — `register/get/get_available/get_preferred/all_keys`; Priorisierung via `IDENTIFICATION_PRIMARY_ADAPTER`-Setting.
4. **PlantNetAdapter** `data_access/external/plantnet_adapter.py` — httpx gegen Pl@ntNet v2, Rate-Limit-Tracking, Fallback (REQ-029 §3.3). Bei fehlendem Key `health_check()→False`.
5. **Collections** in `data_access/arango/collections.py`: `IDENTIFICATION_REQUESTS`, `DIAGNOSIS_REQUESTS`, `REFERENCE_IMAGE_JOBS` (+ Indizes). Repositories analog `base_repository`.
6. **Consent-Purpose** `plant_identification` als Konstante/Enum (privacy), in Consent-Prüfung verdrahtet (REQ-025).
7. **EXIF-Stripping** echte Implementierung (Pillow, `image.getexif()`-Strip + Orientierung anwenden) — gemeinsamer Helper, vom Service VOR jeder Weitergabe genutzt (REQ-029 §5.4).
8. **IdentificationService** `domain/services/identification_service.py` — Consent-Gate, EXIF-Strip, `get_preferred()`-Adapterwahl, Fallback-Kette, Request-Logging ohne Bildpersistenz.
9. **API-Router** `api/v1/recognition/router.py` ausfüllen: `POST identify`, `POST {key}/confirm`, `GET status`, `GET history` (REQ-029 §3.7), tenant-scoped.

### WS-2 — inference-service (NEU, `src/inference-service/`)
Struktur strikt analog `src/knowledge-service/` + ONNX-Pattern aus `docker/embedding-service/main.py`.

1. **Scaffold** `app/main.py` (FastAPI + lifespan), `app/config.py` (pydantic-settings), `Dockerfile`/`Dockerfile.dev`, `requirements.txt` (fastapi, uvicorn, onnxruntime, numpy, pillow, psycopg[binary], psycopg-pool, pydantic-settings, structlog).
2. **ONNX-Export-Skript** `scripts/export_dinov2_onnx.py` — lädt `facebookresearch/dinov2` ViT-S/14 (Apache-2.0), exportiert via `torch.onnx`/`optimum` nach `model.onnx`, schreibt `modelinfo.json` (model, dim=384, input_size=224, license, checksum). Multi-stage Dockerfile lädt das Artefakt (analog HF-Download im embedding-service). **LICENSE vor Build re-verifizieren (§5).**
3. **Preprocessing-Contract** `app/preprocessing.py` — RGB→resize(kürzere Kante)→center-crop(224)→ImageNet-Norm→CHW float32 (REQ-029-A §3.2). **Index- und query-identisch — single source of truth.**
4. **Inferenz** `app/embedder.py` — `ort.InferenceSession` (CPUExecutionProvider), Modell-Load im Startup-Thread (non-blocking), L2-Normalisierung des Embeddings.
5. **pgvector-Schicht** `app/vectordb/` (analog knowledge-service): `connection.py` (ConnectionPool), SQL-Migration `migrations/001_species_embeddings.sql` (`vector(384)`-Spalte, HNSW-Index `vector_cosine_ops`, Spalten species_key/scientific_name/organ/source/license/attribution/source_url/model/indexed_at), `repository.py` (`upsert_reference`, `match(vector,k)`).
6. **Endpunkte:** `POST /embed`, `POST /embed/batch`, `POST /match` (Bild→Top-k species+score), `POST /reference` (Embedding+Provenienz upsert), `DELETE /reference/{species_key}` (Re-Index), `GET /health`, `GET /ready`, `GET /modelinfo`.
7. **Konfidenz-Kalibrierung** `cosine_to_confidence()` — Schwellen `CONFIDENCE_AUTO_ACCEPT` (0.85), `CONFIDENCE_SHOW_RESULTS` (0.10) als Settings; finale Werte aus §4-Evaluierung (kein Literaturwert).

### WS-3 — LocalEmbeddingAdapter (Backend ↔ inference-service)
1. **HTTP-Client** `data_access/external/inference_service_client.py` (httpx, analog `knowledge_service_client.py`) — `match()`, `embed()`, `embed_batch()`, `upsert_reference()`, `is_ready()`.
2. **LocalEmbeddingAdapter** `data_access/external/local_embedding_adapter.py` (REQ-029-A §3.4) — `identify()` ruft `/match`, reichert `species_key`→ArangoDB-Stammdaten an, baut `IdentificationSuggestion`-Liste, `diagnose()→NotImplementedError`.
3. **Registrierung** in `IdentificationAdapterRegistry` als **Prio 1** vor PlantNet; Settings `inference_service_url`, `inference_service_enabled`.

### WS-4 — Referenzbild-Beschaffung (Lizenz-konform, Kern)
1. **GBIF-Media-Client** erweitern (`gbif_adapter.py` oder neuer `gbif_media_adapter.py`): `taxonKey → /occurrence/search?mediaType=StillImage` mit Lizenz-Metadaten (httpx, vorhandenes Rate-Limit-Pattern).
2. **Lizenz-Filter** (verbindlich): nur `CC0` + `CC-BY` übernehmen; `CC-BY-NC`, `CC-BY-SA`, unklar → verwerfen (REQ-029-A §4.1). Lizenz-Mapping-Tabelle (GBIF liefert URIs/Strings normalisieren).
3. **Kuratierung** `domain/services/reference_image_service.py`:
   - Mindestauflösung + Seitenverhältnis-Plausibilität.
   - Optional: Embedding-Ausreißer-Filter (Distanz zum Art-Clusterzentroid) — verwirft Habitat-/Beleg-Fotos.
   - n_max pro Art (Default 40), Ziel 10–30 brauchbare.
4. **Indexierung:** EXIF-Strip → inference-service `/embed/batch` → `/reference` (Embedding+Provenienz in pgvector). **Kein Originalbild persistieren** (REQ-029-A §4.4, AE-5).
5. **Abdeckungs-Protokoll** `reference_image_jobs` (ArangoDB): candidates_found/accepted/rejected_license/rejected_quality/license_breakdown/usable_for_recognition. Arten mit `< 5` Referenzen → `usable_for_recognition=false` (im Frontend ehrlich kommuniziert).
6. **Celery-Task** `tasks/reference_image_tasks.py` — pro Species iterierbar, Batch-Skript + optionaler Beat-Eintrag (kein Default-Schedule; manuell/initial-Lauf). Idempotent (Re-Index pro Art).

### WS-5 — Frontend (`src/frontend/`)
1. **PlantIdentificationDialog** (REQ-029 §4.1) in `pages/ki-recognition/` — Webcam (`getUserMedia`), Smartphone (`<input capture="environment">`), Drag&Drop-Upload, Organ-Auswahl-Chips, Top-k-Ergebnis-Cards, explizite Nutzerwahl (`select_result(rank)`, kein Auto-Anlegen).
2. **Consent-Gate** vor Fallback-Nutzung; ehrliche Kommunikation bei „nicht erkennbar"/niedriger Konfidenz.
3. **API-Layer** (RTK Query slice) + **i18n** `pages.plantIdentification.*` (DE/EN), `enums.plantOrgan.*`.
4. **Onboarding-/IPM-Einstiegspunkte** optional (REQ-020/REQ-010-Synergie) — nur falls günstig, sonst Backlog.

### WS-6 — Helm / Skaffold / Deployment
1. **Helm:** `inference-service`-Controller in `values-dev-ki.yaml` (Image, Probes `/health`+`/ready`, Resources CPU-Baseline, Env `VECTORDB_*`, `MODEL_*`), Service (ClusterIP :8000), NetworkPolicy (Ingress nur von backend; Egress pgvector + DNS).
2. **Skaffold:** Artefakt `kamerplanter-inference-service` im `ki`-Profil (context `src/inference-service`, `Dockerfile.dev`, sync `app/**/*.py`), Port-Forward.
3. **Backend-Settings:** `inference_service_url` default `http://kamerplanter-ki-inference-service:8000`.
4. **pgvector-DB** mitbenutzt (`kamerplanter_vectors`) — eigene Tabelle, keine Kollision mit knowledge-service-Schema.

### WS-7 — Tests & Evaluierung
1. **inference-service:** Embedding-Determinismus (gleiches Bild → identischer Vektor bis Rundung, Szenario A6), Preprocessing-Konsistenz, `/match` gegen Fixture-Index, Health/Ready.
2. **Backend:** Adapter (gemockter inference-client), Registry-Priorisierung, Fallback-Kette (Szenario A4), Consent-Gate, EXIF-Strip, Lizenz-Filter der Beschaffung (Szenario A3), `reference_image_jobs`-Report.
3. **Frontend:** vitest für Dialog (Capture-Modi, Ergebnis-Rendering, „nicht erkennbar").
4. **Eigen-Evaluierung (verbindlich):** Trefferquote an den ~210 eigenen Arten messen (insb. Cannabis/Tropen-Zimmerpflanzen — durch Quellen nicht belegt). Konfidenz-Schwellen (§WS-2.7) aus diesen Messungen justieren und dokumentieren.
5. **Pflicht-Kette nach Implementierung** (Projekt-Konvention): UI-Review → unit-test-runner → mkdocs-documentation.

## 3. Reihenfolge / Abhängigkeitsgraph

```
WS-1 (Phase-1-Basis) ─┬─▶ WS-3 (LocalEmbeddingAdapter) ─┐
WS-2 (inference-svc) ─┘                                  ├─▶ WS-5 (Frontend) ─▶ WS-7 (Tests/Eval)
WS-2 (inference-svc) ─────▶ WS-4 (Beschaffung) ──────────┘
WS-6 (Helm/Skaffold) parallel ab WS-2 lauffähig
```
Kritischer Pfad: **WS-2 (ONNX-Export + Preprocessing-Contract)** — alles Matching-Relevante hängt an dessen Determinismus.

## 4. Akzeptanzkriterien (DoD MVP — aus REQ-029-A §10)

- [ ] inference-service mit ONNX-DINOv2 (Apache-2.0), `/embed`, `/embed/batch`, `/match`, `/reference`, `/health`, `/ready`, `/modelinfo`
- [ ] Preprocessing-Contract zentral, index-/query-identisch (Determinismus-Test grün)
- [ ] ONNX-Export reproduzierbar dokumentiert (Build-Skript + modelinfo)
- [ ] pgvector `species_embeddings` + HNSW-Vektorsuche
- [ ] Beschaffungs-Pipeline: GBIF-Abfrage, CC0/CC-BY-Filter, Kuratierung, Embedding-Indexierung, Provenienz-Protokoll
- [ ] Abdeckungs-Report je Art; Arten < 5 Referenzen als „nicht erkennbar" markiert
- [ ] LocalEmbeddingAdapter Prio 1 vor Pl@ntNet; Fallback bei Konfidenz < Schwelle (Consent + Key)
- [ ] Nur Embeddings + Metadaten persistiert, keine fremden Originalbilder
- [ ] DSGVO: Nutzerfoto nicht persistiert, EXIF-Strip, kein Drittland-Transfer im Primärpfad
- [ ] Konfidenz-Kalibrierung an eigenen Arten gemessen & dokumentiert
- [ ] Frontend nutzt `PlantIdentificationDialog` über die Registry
- [ ] Tests (Service/Adapter/Vektorsuche/Lizenz-Filter) + Helm/Skaffold-Integration
- [ ] **Szenarien A1–A6** (REQ-029-A §10) als Tests abgebildet

## 5. Risiken & offene Punkte

| Risiko | Mitigation |
|---|---|
| **DINOv2-LICENSE** (Meta hat re-lizenziert) | Vor ONNX-Build `LICENSE` im `facebookresearch/dinov2`-Repo re-verifizieren; nur Apache-2.0-Basis-Backbone, **nie** PlantCLEF-Fine-tune (CC-BY-NC). |
| **Trefferquote unbelegt** für Cannabis/Tropen-Zimmerpflanzen | WS-7 Eigen-Evaluierung; betroffene Arten ehrlich als unsicher markieren; Pl@ntNet-Fallback. |
| **Spec-Drift D-2** (pgvector statt ArangoDB) | REQ-029-A §5 nachziehen + Begründung; Memory-Eintrag aktualisieren. |
| **Merge-Konflikt mit `feat/plant-identification`** | Phase-1-Bausteine an Spec-Signaturen halten (REQ-029 §3.1/§3.4); früh klären, welcher Branch zuerst nach develop geht. |
| **GBIF-Abdeckungslücken** (seltene Arten, Cannabis-Indoor) | Wikimedia-Ergänzung (CC0/PD), Lücken protokollieren, ehrliche UI. |
| **ONNX-Modellgröße im Image** | ViT-S/14 (~21M) als Baseline, CPU-Inferenz; Modell via Multi-stage-Build, nicht ins Repo. |

## 6. Nicht im Scope (Backlog)

- Aufgabe B — Krankheit/Schädling (PlantDoc-Klassifikator, REQ-010), REQ-029-A §6.1
- Aufgabe C — Phänologie/Zustand (REQ-003), REQ-029-A §6.2 — Forschungsstufe, braucht Eigenmaterial
- Cultivar-Erkennung (explizit out of scope, REQ-029-A §1.1)
- ArangoDB-Vektor-Index (durch D-2 ersetzt)
