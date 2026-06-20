# Setting Up Plant Identification (Inference Service)

This page describes how to set up the `inference-service` for self-hosted plant identification (REQ-029-A). The inference service is an optional component — Kamerplanter works fully without it; plant identification will be unavailable.

---

## Overview: What Gets Installed?

The inference service (`src/inference-service/`) is a standalone FastAPI microservice that:

- loads the DINOv2 model (ViT-S/14, Apache-2.0, ~21 M parameters) as an ONNX artefact,
- preprocesses images and converts them into embedding vectors (384 dimensions),
- matches these vectors against a **reference index** in pgvector and returns the most similar plant species.

The service is an **optional, standalone** module. There are two deployment topologies:

- **Development (Skaffold):** The service runs in its own Helm release `kamerplanter-recognition` (Skaffold profile `recognition`) and shares the pgvector store with the knowledge service (`kamerplanter-ki` release, database `kamerplanter_vectors`, its own table `species_embeddings`). The `kamerplanter-ki` vectordb must be running when the `recognition` profile starts.
- **Production (ArgoCD, single-release):** The inference service and a **dedicated** pgvector instance run in the **same** Helm release as the backend and frontend (`kamerplanter`). No separate release, no shared pgvector store with the knowledge service. Available from image tag **v0.0.17** onwards (CI publishes the `kamerplanter-inference-service` image to GHCR starting from this release).

In both topologies the service is only reachable within the cluster (Kubernetes `ClusterIP`).

---

## Activation Order

!!! warning "Follow the order"
    Execute the three steps in the order shown. If you set `INFERENCE_SERVICE_ENABLED=true` before the reference index is populated, local identification is unavailable — the backend then falls back directly to Pl@ntNet (only if a `PLANTNET_API_KEY` is configured; see the Environment Variables table).

### Step 1: Start the Inference Service — Development (Skaffold)

```bash
# In the project directory (development):
# The recognition profile shares the pgvector DB with the ki stack,
# so start both modules together:
skaffold dev -m ki -m recognition
```

The `recognition` profile starts only the `inference-service` (its own release `kamerplanter-recognition`); the `ki` profile provides the shared pgvector DB. On first start, the ONNX model is exported during the build step — this takes 5–15 minutes depending on your hardware (see Resource Requirements below).

!!! tip "Model export is cached"
    After the first build, the model lives in the layer cache. Subsequent starts complete in seconds.

**Check that the service is running:**

```bash
# Port-forward (local development):
kubectl port-forward svc/kamerplanter-recognition 8090:8000 -n default

# Check readiness (is the model loaded?):
curl http://localhost:8090/ready
# Expected response: {"status": "ok"}

# Retrieve model information:
curl http://localhost:8090/modelinfo
# Response includes: model, dim, input_size, license, checksum
```

### Step 2: Populate the Reference Index

The reference index contains embedding vectors for all plant species from the master data. It is populated by a Celery task that fetches reference images from GBIF and Wikimedia Commons (CC0/CC-BY licences only), embeds them, and stores the vectors in pgvector. **Original images are not stored.**

!!! info "This step also populates the UI images in the species view"
    After the task completes, thumbnails appear in the **species list** and a full **reference image gallery** appears on each **species detail page**. Before the first acquisition run, both views show a placeholder notice. Licence attribution (CC-BY) is stored automatically in the metadata and displayed in the UI. For more information: [Reference Images in the Species View](../user-guide/plant-management.md#reference-images-in-the-species-view).

```bash
# Start the Celery task for all species (one-time run; takes several hours):
kubectl exec -it deploy/kamerplanter-backend -n default -- \
  celery -A app.tasks call \
  app.tasks.reference_image_tasks.acquire_all_reference_images_task

# Alternatively: via the backend API (admin endpoint):
curl -X POST http://localhost:8000/api/v1/admin/reference-images/acquire \
  -H "Authorization: Bearer <admin-token>"
```

**Monitor progress:**

```bash
# Query the coverage report (how many species are identifiable?):
curl http://localhost:8000/api/v1/admin/reference-images/coverage \
  -H "Authorization: Bearer <admin-token>"
```

The response shows per species how many reference images were accepted and whether the species is considered "identifiable" (`usable_for_recognition`, at least 5 accepted references):

```json
{
  "total_species": 66,
  "usable_species": 48,
  "entries": [
    {
      "species_key": "species_alocasia_zebrina",
      "scientific_name": "Alocasia zebrina",
      "accepted": 2,
      "candidates_found": 7,
      "usable_for_recognition": false,
      "license_breakdown": {"CC0": 1, "CC_BY": 1}
    }
  ]
}
```

!!! note "Coverage gaps"
    Species with fewer than 5 accepted reference images do not appear in identification results. The system communicates this honestly in the UI. Common causes for gaps: rare species, exotic houseplants, or species without CC0/CC-BY photos in GBIF.

**Admin API endpoints for reference image acquisition (overview):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/reference-images/acquire` | Start an acquisition run for all species |
| `POST` | `/api/v1/admin/reference-images/acquire/{species_key}` | Start or repeat the acquisition run for a single species |
| `GET` | `/api/v1/admin/reference-images/coverage` | Coverage report: identifiable species, species below threshold |

All three endpoints require a valid admin token (`Authorization: Bearer <admin-token>`). They are accessible via the regular backend ingress — no separate port-forward is needed.

### Step 3: Enable the Local Path

Set the environment variable in the backend:

```bash
# Backend env (values-dev.yaml) or environment variable:
INFERENCE_SERVICE_ENABLED=true
```

!!! danger "Only enable once the index is populated"
    If `INFERENCE_SERVICE_ENABLED=true` is set and the reference index is empty, the system falls back to Pl@ntNet — but **only if a Pl@ntNet key is configured and consent has been granted**. If neither is the case, identification returns no results.

---

## Helm Configuration

### Development (Skaffold)

In the development workflow the inference service is started via the Skaffold profile `recognition` as a separate Helm release `kamerplanter-recognition`. Configuration lives in `helm/kamerplanter/values-dev-recognition.yaml` — the pgvector store is shared with the `kamerplanter-ki` release (see Overview above).

### Production (ArgoCD — Single-Release)

!!! warning "Minimum image tag: v0.0.17"
    The CI image `ghcr.io/nolte/kamerplanter-inference-service` is only published from release **v0.0.17** onwards (this is the first release that includes the `build-inference-service` CI job). ArgoCD Applications must pin to `v0.0.17` or later — earlier tags do not contain the image.

In production the inference service and a **dedicated** pgvector instance (`vectordb`) run inside the **same** Helm release as the backend and frontend (release name `kamerplanter`). The chart `helm/kamerplanter/values.yaml` ships two additional controllers that are disabled by default: `vectordb` and `inference-service`. The operator enables them via `valuesObject` in the ArgoCD Application.

!!! warning "One Secret key: `POSTGRES_PASSWORD`"
    Before the first deployment the operator sets exactly **one** key in `kamerplanter-secrets`: `POSTGRES_PASSWORD`. The `vectordb` container (PostgreSQL 18) mandates that name; the `inference-service` derives its own `VECTORDB_PASSWORD` from the **same** key via `secretKeyRef` (the chart wires this up). No password is ever inlined in the chart or in Git, and both containers pull just that one key — not the whole Secret via `envFrom`.

    Generate and set the key (existing Secret keys are preserved):

    ```bash
    PW=$(openssl rand -base64 24)
    kubectl patch secret kamerplanter-secrets -n kamerplanter --type merge \
      -p "{\"stringData\":{\"POSTGRES_PASSWORD\":\"$PW\"}}"
    ```

    If `kamerplanter-secrets` does not exist yet:

    ```bash
    kubectl create secret generic kamerplanter-secrets -n kamerplanter \
      --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)"
    ```

    When `kamerplanter-secrets` is fed by ESO / Sealed Secrets / Vault, add `POSTGRES_PASSWORD` at that source instead.

**ArgoCD Application — `spec.sources[].helm.valuesObject`:**

```yaml
controllers:
  vectordb:
    enabled: true
  inference-service:
    enabled: true
  backend:
    containers:
      main:
        env:
          INFERENCE_SERVICE_ENABLED: "true"
          INFERENCE_SERVICE_URL: "http://kamerplanter-inference-service:8000"
service:
  vectordb:
    enabled: true
  inference-service:
    enabled: true
persistence:
  inference-service-tmp:
    enabled: true
networkpolicies:
  vectordb:
    enabled: true
  inference-service:
    enabled: true
```

Resources and security context (chart defaults — do not override unless necessary):

| Component | CPU request/limit | RAM request/limit | Notes |
|-----------|-------------------|-------------------|-------|
| `vectordb` | 50m / 500m | 128Mi / 512Mi | StatefulSet, 5Gi PVC (`/var/lib/postgresql/data`, `PGDATA` = `.../pgdata`), uid/gid/fsGroup 999 (postgres), `helm.sh/resource-policy: keep` |
| `inference-service` | 250m / 2 | 512Mi / 2Gi | `readOnlyRootFilesystem: true`, memory-backed `/tmp` emptyDir |

In-cluster service hostnames (release name `kamerplanter`):

- Backend → inference service: `http://kamerplanter-inference-service:8000`
- Inference service → pgvector: `kamerplanter-vectordb:5432` (chart default for `VECTORDB_HOST`)

### Activation Order in Production

!!! warning "Follow the order (production)"
    Deploy the stack (vectordb + inference-service) and populate the reference index **before** setting `INFERENCE_SERVICE_ENABLED=true`. Otherwise recognition finds no reference index and returns no results.

1. Deploy the ArgoCD Application with the `valuesObject` fields shown above (without `INFERENCE_SERVICE_ENABLED: "true"`). Wait until `kamerplanter-vectordb` and `kamerplanter-inference-service` are `Ready`.
2. Populate the reference index (identical to Step 2 in the development path above — the `kubectl exec` target is `deploy/kamerplanter-backend`).
3. Add `INFERENCE_SERVICE_ENABLED: "true"` to the `valuesObject` and synchronise the Application.

### Resource Requirements

| Scenario | RAM | CPU | Latency/request |
|----------|-----|-----|----------------|
| DINOv2 ViT-S/14 | 512 MB – 1 GB | 0.5–2 cores | 500ms–2s (CPU) |

!!! tip "Raspberry Pi / ARM"
    DINOv2 ViT-S/14 runs on ARM64 (Raspberry Pi 4/5, Apple Silicon). Latency is higher (~3–8s) but sufficient for batch indexing and interactive identification.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `VECTORDB_HOST` | No | `localhost` | Hostname of the pgvector database. In-cluster value depends on topology: DEV/separate-release → `kamerplanter-ki-vectordb` (shared KI stack); production/single-release → `kamerplanter-vectordb` (dedicated, chart default) |
| `VECTORDB_PORT` | No | `5432` | Port of the pgvector database |
| `VECTORDB_DATABASE` | No | `kamerplanter_vectors` | Database name |
| `VECTORDB_USERNAME` | No | `postgres` | Database user |
| `VECTORDB_PASSWORD` | No | `changeme` | Database password. In production (single-release) derived via `secretKeyRef` from the **one** Secret key `POSTGRES_PASSWORD` — do not set separately |
| `MODEL_NAME` | No | `dinov2_vits14` | ONNX model name |
| `MODEL_PATH` | No | `/app/models/dinov2` | Directory containing the ONNX model artefact (`model.onnx`) |
| `CONFIDENCE_AUTO_ACCEPT` | No | `0.85` | Confidence threshold for direct acceptance |
| `CONFIDENCE_SHOW_RESULTS` | No | `0.10` | Minimum confidence to appear in the list |

| Variable (Backend) | Required | Default | Description |
|--------------------|:--------:|---------|-------------|
| `INFERENCE_SERVICE_ENABLED` | No | `false` | Enable the local inference path |
| `INFERENCE_SERVICE_URL` | No | `http://kamerplanter-recognition:8000` | Internal URL of the inference service |
| `PLANTNET_API_KEY` | No | — | Pl@ntNet API key for fallback (optional) |

---

## Inference Service Endpoints (Internal)

These endpoints are only reachable within the cluster and are not exposed via the ingress.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/embed` | Single image → embedding vector |
| `POST` | `/embed/batch` | Multiple images → embedding vectors (acquisition) |
| `POST` | `/match` | Image → top-k most similar species with confidence (query param `k`, default `5`, max `50`) |
| `POST` | `/reference` | Store embedding + provenance in pgvector |
| `GET` | `/reference/{species_key}` | Retrieve the indexed references for a species |
| `DELETE` | `/reference/{species_key}` | Delete references for a species (re-index) |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (model loaded?) |
| `GET` | `/modelinfo` | Model name, dimensions, input size, licence, checksum |

---

## Licences and Legal Notes

| Component | Licence | Note |
|-----------|---------|------|
| DINOv2 base backbone (Meta) | Apache-2.0 | Verify LICENSE in the official repo before production use |
| ONNX Runtime (Microsoft) | MIT | — |
| Reference images (GBIF) | CC0 / CC-BY | Only these licences are indexed |
| PlantCLEF fine-tuned weights | CC-BY-NC | **Not used** (non-commercial restriction) |
| Pl@ntNet API (fallback) | ToS, free ≤500/day | Only with user consent, only as fallback |

!!! danger "Do not use PlantCLEF weights"
    The DINOv2 weights fine-tuned on the PlantCLEF-2024 dataset are licensed under CC-BY-NC (non-commercial). These weights are **not** used. Kamerplanter exclusively uses the Apache-2.0-licensed base backbone from `facebookresearch/dinov2`.

---

## Troubleshooting

??? question "The inference service fails to start — error: model not found"
    The ONNX artefact may not have been exported. Check the build log of the `inference-service` image for the `export_dinov2_onnx.py` step. Run `skaffold build -m recognition` again.

??? question "Identification always returns 'no results' even though the service is running"
    Check whether the reference index is populated (`/api/v1/admin/reference-images/coverage`). An empty index produces no matches. Run `acquire_all_reference_images_task` (Step 2).

??? question "The Celery task runs for a very long time — is that normal?"
    Yes. Fetching GBIF data for all configured species — with up to 40 image candidates each, computing embeddings, and building the index — can take several hours depending on the number of species, hardware, and network speed. The task is idempotent — you can restart it if interrupted.

??? question "How do I update the reference index for a single species?"
    Use the admin endpoint `POST /api/v1/admin/reference-images/acquire/{species_key}` — it triggers the `acquire_reference_images_task` Celery task for that species internally.

---

## See Also

- [Plant Identification (User Guide)](../user-guide/plant-identification.md)
- [Image Recognition Architecture](../architecture/ai-architecture.md#image-recognition-dinov2)
- [Deployment Profiles](betriebsprofile.md) — Which AI components are included in which profile?
- [ArgoCD Deployment](argocd.md) — Production deployment with ArgoCD (Application configuration, sync strategies)
- [Helm Charts](helm.md) — General Helm configuration
- [Environment Variables](../reference/environment-variables.md)
