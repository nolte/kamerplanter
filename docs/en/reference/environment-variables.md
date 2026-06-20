# Environment Variables

All configuration parameters for the Kamerplanter backend are controlled via environment variables. Variables are loaded by `pydantic-settings` — case sensitivity is not relevant.

!!! tip "Local configuration"
    For the Docker Compose environment, add all values to a `.env` file in the repository root directory. A template is provided as `.env.example`:
    ```bash
    cp .env.example .env
    ```

---

## Database Connection

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `ARANGODB_HOST` | `localhost` | Yes | Hostname or IP address of the ArangoDB instance |
| `ARANGODB_PORT` | `8529` | No | TCP port of ArangoDB |
| `ARANGODB_DATABASE` | `kamerplanter` | Yes | Name of the target database |
| `ARANGODB_USERNAME` | `root` | Yes | Database user |
| `ARANGODB_PASSWORD` | — | Yes | Password for the database user |
| `ARANGO_ROOT_PASSWORD` | — | Yes* | Root password for the ArangoDB container (Docker only) |

*`ARANGO_ROOT_PASSWORD` is passed directly to the ArangoDB container and is required to start the database.

!!! warning "Production passwords"
    Never use the default value `rootpassword` in production environments. Generate secure passwords: `openssl rand -hex 32`

---

## Cache and Task Queue

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Yes | Connection URL for Redis or Valkey (Celery broker and backend cache) |

**Format:** `redis://[user]:[password]@[host]:[port]/[db]`

**Examples:**
```
redis://localhost:6379/0                    # Local without auth
redis://:mypassword@redis:6379/0            # With password
rediss://user:pass@redis-host:6380/1        # TLS (rediss://)
```

---

## Security and Authentication

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-in-production-...` | Yes | Secret key for JWT signing (HS256) |
| `JWT_ALGORITHM` | `HS256` | No | JWT signature algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | No | JWT access token validity in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | No | Refresh token validity in days |
| `FERNET_KEY` | — | No | Fernet key for encrypting OIDC provider secrets |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | No | Require email verification at registration |
| `HIBP_ENABLED` | `false` | No | Enable "Have I Been Pwned" check on password change |

!!! danger "Change JWT_SECRET_KEY in production"
    The default value `change-me-in-production-use-openssl-rand-hex-32` **must not** be used in production. Generate a secure value:
    ```bash
    openssl rand -hex 32
    ```
    Changing `JWT_SECRET_KEY` invalidates all active tokens — all users will be logged out.

---

## Operating Mode

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `KAMERPLANTER_MODE` | `full` | No | Operating mode: `full` (auth + tenants) or `light` (no auth, local single-user) |
| `DEBUG` | `false` | No | Enable debug logging (verbose — never use in production) |
| `FRONTEND_URL` | `http://localhost:5173` | No | Frontend URL (used for email links) |

### Light Mode (`KAMERPLANTER_MODE=light`)

In Light Mode, token authentication is disabled. The API is usable without login. This mode is intended for local single-user installations that are not exposed to the internet.

!!! danger "Do not expose Light Mode publicly"
    Light Mode disables all authentication layers. Never run it with a publicly accessible port.

---

## CORS Configuration

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | No | JSON array of allowed origins for CORS |

**Format:** Always as a JSON array in string format:
```bash
CORS_ORIGINS='["https://app.example.com","https://app2.example.com"]'
```

---

## Email

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `EMAIL_ADAPTER` | `console` | No | Email adapter: `console` (output to log), `smtp`, `resend` |
| `SMTP_HOST` | `localhost` | No | SMTP server hostname |
| `SMTP_PORT` | `587` | No | SMTP port |
| `SMTP_USERNAME` | — | No | SMTP username |
| `SMTP_PASSWORD` | — | No | SMTP password |
| `SMTP_FROM_EMAIL` | `noreply@kamerplanter.example` | No | Sender address for system emails |
| `SMTP_USE_TLS` | `true` | No | Enable STARTTLS for SMTP |

In development mode (`EMAIL_ADAPTER=console`), emails are not sent but printed to the backend log.

---

## External Data Enrichment (REQ-011)

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `PERENUAL_API_KEY` | — | No | API key for Perenual plant database |
| `TREFLE_API_KEY` | — | No | API key for Tréflé plant database |
| `ENRICHMENT_HTTP_TIMEOUT` | `30` | No | HTTP timeout for external API requests (seconds) |

GBIF is used without an API key (public API). Perenual and Tréflé require free registration.

---

## Knowledge Service — Re-Ranking (optional)

These variables configure the optional cross-encoder re-ranker of the Knowledge Service. When `RERANKER_URL` is empty, the Knowledge Service operates in hybrid-search-only mode (graceful degradation). See [ADR-007](../adr/007-cross-encoder-reranking.md).

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `RERANKER_URL` | `` (empty) | No | HTTP URL of the reranker microservice, e.g. `http://reranker-service:8081`. Empty = re-ranking disabled. |
| `RERANKER_INITIAL_K` | `20` | No | Number of chunks retrieved from the Hybrid Search step (over-retrieval). |
| `RERANKER_TOP_K` | `5` | No | Number of chunks passed to the LLM context after re-ranking. |
| `RERANKER_MODEL` | `bge-reranker-v2-m3` | No | ONNX model name in the reranker service container (directory under `/app/models/onnx/`). |

!!! note "RERANKER_MODEL belongs to the reranker service, not the knowledge service"
    `RERANKER_MODEL` is set as an environment variable on the `reranker-service` container — not on the `knowledge-service`. The other three variables (`RERANKER_URL`, `RERANKER_INITIAL_K`, `RERANKER_TOP_K`) belong to the Knowledge Service.

!!! tip "Resource requirements"
    The reranker service requires 1.5–4 GB RAM (depending on the model) and adds ~500ms latency per request. For Raspberry Pi and resource-constrained environments, it is recommended to leave `RERANKER_URL` empty.

---

## mDNS / Zeroconf Discovery

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `MDNS_ENABLED` | `false` | No | Enable mDNS service announcement (`_kamerplanter._tcp.local.`) |
| `INSTANCE_ID` | *(auto)* | No | Unique instance ID (e.g. `kp-abc123`). Auto-generated at startup if empty. |

When enabled, the backend announces a `_kamerplanter._tcp.local.` service on the local network. Home Assistant detects this service automatically and offers to set up the Kamerplanter integration.

!!! info "Stable Instance ID"
    The `INSTANCE_ID` is used for duplicate detection in Home Assistant. If left empty, a new ID is generated on every restart. For stable discovery, set a fixed value, e.g. `INSTANCE_ID=kp-my-server`.

### mDNS and Kubernetes

mDNS relies on Multicast UDP (port 5353) within the local Layer 2 network. In standard Kubernetes clusters, mDNS **does not work** because:

1. **Overlay network blocks multicast** — Standard CNIs (Calico, Cilium, Flannel) only route L3 traffic. Multicast packets from a pod never reach the physical LAN — Home Assistant cannot see the announcements.
2. **Pod IP is not LAN-reachable** — Even if multicast worked, the announced pod IP (e.g. `10.42.x.x`) would not be reachable from outside the cluster.

| Deployment | `MDNS_ENABLED` | Rationale |
|------------|:-----------:|-----------|
| Docker Compose / Bare Metal | `true` | Backend runs directly on the LAN — set `MDNS_ENABLED=true` |
| K3s / MicroK8s single-node + `hostNetwork: true` | `true` | Pod shares host network — multicast reaches the LAN |
| Standard K8s Cluster | `false` | Overlay network blocks multicast — use manual config flow in HA as fallback |
| Cloud (AWS, GCP, Azure) | `false` | No local network available |

!!! warning "hostNetwork is a trade-off"
    With `hostNetwork: true`, the pod shares the host's network namespace. Multicast works, but at the cost of network isolation (port conflicts possible, no NetworkPolicy enforcement). Only recommended for homelab / Raspberry Pi scenarios.

The Helm chart sets `MDNS_ENABLED` to `false` by default. The manual config flow in Home Assistant (URL input) works in every deployment scenario as a fallback.

---

## Home Assistant Integration (REQ-005)

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `HA_URL` | — | No | Home Assistant base URL, e.g. `http://homeassistant.local:8123` |
| `HA_ACCESS_TOKEN` | — | No | Long-Lived Access Token from Home Assistant |
| `HA_TIMEOUT` | `10` | No | HTTP timeout for HA requests (seconds) |

---

## Rate Limiting

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `RATE_LIMIT_AUTH` | `20/minute` | No | Rate limit for authentication endpoints |
| `RATE_LIMIT_GENERAL` | `100/minute` | No | Rate limit for general API endpoints |

**Format:** `[count]/[unit]` — units: `second`, `minute`, `hour`, `day`

---

## Uploads

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `UPLOAD_DIR` | `uploads/tasks` | No | Directory for file uploads (relative to backend working directory) |

---

## Nested Configuration (GBIF)

GBIF settings can be passed using the double-underscore delimiter for nesting:

| Variable | Default | Description |
|----------|---------|-------------|
| `GBIF__BASE_URL` | `https://api.gbif.org/v1` | GBIF API base URL |
| `GBIF__RATE_LIMIT_PER_MINUTE` | `60` | Requests per minute to GBIF |
| `GBIF__HTTP_TIMEOUT` | `30` | Timeout for GBIF requests (seconds) |

---

## Photo Identification (REQ-029)

These variables configure optional plant recognition by photo. If none of the API keys are set, the feature is completely disabled — all camera buttons are hidden and no consent dialog is shown.

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `PLANTNET_API_KEY` | — | No | API key for Pl@ntNet (free tier: ≤ 500 identifications/day). Register at [my.plantnet.org](https://my.plantnet.org). |
| `PLANTNET_BASE_URL` | `https://my-api.plantnet.org/v2` | No | Pl@ntNet API base URL. Only change for self-hosting or test endpoints. |
| `IDENTIFICATION_PRIMARY_ADAPTER` | `plantnet` | No | Preferred adapter. Possible values: `plantnet`. Extensible through future adapters. |
| `IDENTIFICATION_CONFIDENCE_AUTO_ACCEPT` | `0.85` | No | Confidence threshold (0–1) above which a suggestion is highlighted as "very certain". |
| `IDENTIFICATION_CONFIDENCE_MIN_SHOW` | `0.10` | No | Minimum confidence (0–1) required to show a suggestion. Results below this are filtered out. |
| `IDENTIFICATION_MAX_IMAGE_SIZE_MB` | `10` | No | Maximum image size in megabytes. Larger images are rejected with HTTP 400. |
| `IDENTIFICATION_RATE_LIMIT_PER_USER_DAY` | `0` | No | Maximum requests per user per day. `0` uses the adapter default limit (500 for Pl@ntNet). |

!!! warning "Pl@ntNet for non-commercial use only"
    The Pl@ntNet free tier is licensed for non-commercial use. For commercial instances review the terms of use at [my.plantnet.org](https://my.plantnet.org).

!!! tip "Kubernetes Secrets"
    The `PLANTNET_API_KEY` should be stored as a Kubernetes Secret:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: kamerplanter-identification
    type: Opaque
    stringData:
      PLANTNET_API_KEY: "your-api-key"
    ```

### Feature Toggle Logic

```
PLANTNET_API_KEY set?
  ├── Yes  → Pl@ntNet active (species identification, ≤ 500 IDs/day)
  └── No   → Feature completely disabled
             (camera buttons hidden, no consent dialog)
```

---

## Browser Push / PWA (VAPID)

These variables enable the browser push notification channel (`channel_key: "pwa"`). When all three variables are empty, the channel is disabled — the application remains fully functional and users see "Not configured" in their notification settings.

!!! tip "Step-by-step guide"
    The [Set Up Browser Push](../guides/browser-push-setup.md) guide walks through generating the key pair, storing it in Docker Compose or Kubernetes, and verifying the setup.

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `VAPID_PUBLIC_KEY` | — | No* | VAPID public key (Base64url, 87 characters). Sent to the browser and used in the PWA subscription. |
| `VAPID_PRIVATE_KEY` | — | No* | VAPID private key (Base64url or PEM). **Server-side only** — never expose in the frontend or logs. |
| `VAPID_CONTACT_EMAIL` | — | No* | Contact email for the push service (format: `mailto:admin@example.com`). Used by push services (FCM, APNS, Mozilla) to report issues. |

*All three variables must be set for the browser push channel to become active. If any variable is missing, the channel remains disabled.

### Generating a Key Pair

```bash
npx web-push generate-vapid-keys
```

Output:
```
Public Key:
BNm...

Private Key:
8Kv...
```

Alternatively with `pywebpush` (Python) — the `b64urlencode` step is required because `v.public_key`/`v.private_key` are key objects and only serialization yields the Base64url strings:
```bash
pip install pywebpush
python3 - <<'PY'
from py_vapid import Vapid
from py_vapid.utils import b64urlencode
from cryptography.hazmat.primitives import serialization

v = Vapid()
v.generate_keys()
pub_raw = v.public_key.public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint,
)
priv_raw = v.private_key.private_numbers().private_value.to_bytes(32, "big")
pub, priv = b64urlencode(pub_raw), b64urlencode(priv_raw)
assert pub_raw[0] == 0x04 and len(pub_raw) == 65 and len(pub) == 87, "invalid public key"
assert len(priv_raw) == 32 and len(priv) == 43, "invalid private key"
print("VAPID_PUBLIC_KEY =", pub)
print("VAPID_PRIVATE_KEY=", priv)
PY
```

!!! danger "Keep the private key server-side"
    The `VAPID_PRIVATE_KEY` must **never** appear in the frontend, in logs, or in public configuration files. Store it as a Kubernetes Secret or Docker Secret — analogous to `JWT_SECRET_KEY`.

!!! tip "Kubernetes Secret for VAPID"
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: kamerplanter-vapid
    type: Opaque
    stringData:
      VAPID_PUBLIC_KEY: "BNm..."
      VAPID_PRIVATE_KEY: "8Kv..."
      VAPID_CONTACT_EMAIL: "mailto:admin@example.com"
    ```

---

## Complete .env Example

```bash
# Database
ARANGO_ROOT_PASSWORD=secure-root-password
ARANGODB_HOST=arangodb
ARANGODB_PORT=8529
ARANGODB_DATABASE=kamerplanter
ARANGODB_USERNAME=root
ARANGODB_PASSWORD=secure-root-password

# Cache / Queue
REDIS_URL=redis://valkey:6379/0

# Security
JWT_SECRET_KEY=generate-with-openssl-rand-hex-32
REQUIRE_EMAIL_VERIFICATION=false

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Operating mode
KAMERPLANTER_MODE=full
DEBUG=false

# Email (development)
EMAIL_ADAPTER=console

# mDNS Discovery (LAN only, opt-in)
# MDNS_ENABLED=false
# INSTANCE_ID=

# Optional external APIs
PERENUAL_API_KEY=
HA_URL=
HA_ACCESS_TOKEN=

# Knowledge Service — Re-Ranking (empty = disabled)
RERANKER_URL=
RERANKER_INITIAL_K=20
RERANKER_TOP_K=5

# Photo identification (empty = feature disabled)
# PLANTNET_API_KEY=
# IDENTIFICATION_RATE_LIMIT_PER_USER_DAY=0

# Browser Push / PWA (empty = channel disabled)
# VAPID_PUBLIC_KEY=
# VAPID_PRIVATE_KEY=
# VAPID_CONTACT_EMAIL=mailto:admin@example.com
```

---

## Object Storage (NFR-013)

These variables configure the storage adapter for binary data (photos, imports, exports). The active backend is determined by `STORAGE_BACKEND`. By default, `local-fs` is active — no additional configuration required.

For background information, see [Configure Storage (Object Storage)](../user-guide/object-storage.md) and [Helm Charts — Storage Configuration](../deployment/helm.md#storage-configuration-nfr-013).

### General Storage Settings

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `STORAGE_BACKEND` | `local-fs` | No | Active backend: `local-fs` or `s3` |
| `STORAGE_MAX_FILE_SIZE_MB` | `25` | No | Maximum upload size in megabytes (applies to all categories, overridable per category) |
| `STORAGE_PRESIGN_TTL_SECONDS` | `900` | No | Validity period of pre-signed URLs in seconds (max. 3600) |
| `STORAGE_ALLOWED_MIME_TYPES` | *(list)* | No | Comma-separated global whitelist of allowed MIME types |
| `STORAGE_ALLOWED_MIME_TYPES_<CATEGORY>` | *(per category)* | No | Category-specific whitelist, e.g. `STORAGE_ALLOWED_MIME_TYPES_IMPORT=text/csv` |
| `STORAGE_VIRUS_SCAN_ENABLED` | `false` | No | Enable virus scanning via ClamAV REST wrapper |
| `STORAGE_VIRUS_SCAN_ENDPOINT` | *(empty)* | No | URL of the ClamAV REST wrapper |
| `STORAGE_KEEP_EXIF_<CATEGORY>` | `false` | No | Retain EXIF data for a category, e.g. `STORAGE_KEEP_EXIF_PLANT=true` |

**Default MIME whitelist per category:**

| Category | Allowed MIME types | Max size |
|---------|--------------------|---------|
| `diary`, `ipm`, `harvest`, `post_harvest`, `task`, `id_recognition`, `plant` | `image/jpeg`, `image/png`, `image/webp`, `image/heic` | 25 MB |
| `import` | `text/csv`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 50 MB |
| `export` | `application/pdf`, `text/csv`, `application/zip` | 200 MB |
| `tenant_export` | `application/zip` | 5 GB |

### Backend: Local Filesystem (`local-fs`)

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `STORAGE_LOCAL_FS_ROOT` | `/data/attachments` | No | Mount path inside the container |
| `STORAGE_LOCAL_FS_PUBLIC_BASE_URL` | *(empty)* | Yes* | Full URL of the token download endpoint, e.g. `https://api.kamerplanter.example.com/api/v1/attachments/token`. Must point to `https://<host>/api/v1/attachments/token`. |
| `STORAGE_LOCALFS_SIGNING_SECRET` | *(ephemeral)* | Yes** | Secret key for token signatures. **Required when running more than one replica**, otherwise tokens cannot be validated by other pods. |

*Required for local-fs token downloads to work.
**Required in multi-replica operation.

!!! warning "Store signing secret as a Kubernetes Secret"
    `STORAGE_LOCALFS_SIGNING_SECRET` is a cryptographic secret and must not be committed to `values.yaml` or Git in plain text. Create it as a Kubernetes Secret:
    ```bash
    kubectl create secret generic kamerplanter-storage-signing \
      --from-literal=STORAGE_LOCALFS_SIGNING_SECRET="$(openssl rand -hex 32)" \
      --namespace kamerplanter
    ```

### Backend: S3-compatible (`s3`)

| Variable | Default | Required | Description |
|----------|---------|---------|-------------|
| `STORAGE_S3_ENDPOINT_URL` | *(empty)* | Yes | Full endpoint URL, e.g. `https://s3.eu-central-1.amazonaws.com` |
| `STORAGE_S3_REGION` | *(empty)* | Yes | Region, e.g. `eu-central-1` (also required for MinIO) |
| `STORAGE_S3_BUCKET` | *(empty)* | Yes | Bucket name (must be created beforehand) |
| `STORAGE_S3_ACCESS_KEY_ID` | *(empty)* | Yes | Access key (from External Secrets Operator — never in plain text in Git) |
| `STORAGE_S3_SECRET_ACCESS_KEY` | *(empty)* | Yes | Secret access key (from External Secrets Operator — never in plain text in Git) |
| `STORAGE_S3_USE_PATH_STYLE` | `false` | No | `true` for MinIO and most non-AWS providers |
| `STORAGE_S3_FORCE_TLS` | `true` | No | Block plain HTTP; set to `false` in dev environments |
| `STORAGE_S3_KMS_KEY_ID` | *(empty)* | No | Optional customer-managed key for server-side encryption (SSE-KMS) |
| `STORAGE_S3_ALLOW_PRIVATE_ENDPOINT` | `false` | No | `true` for in-cluster MinIO that is not publicly reachable |

!!! danger "Never put S3 credentials in Git or values.yaml"
    `STORAGE_S3_ACCESS_KEY_ID` and `STORAGE_S3_SECRET_ACCESS_KEY` are secrets and must be provided exclusively through the External Secrets Operator (ESO) or Kubernetes Secrets. For details, see [Helm Charts — Storage Configuration](../deployment/helm.md#storage-configuration-nfr-013).

#### Example Configurations

=== "AWS S3 (eu-central-1)"

    ```bash
    STORAGE_BACKEND=s3
    STORAGE_S3_ENDPOINT_URL=https://s3.eu-central-1.amazonaws.com
    STORAGE_S3_REGION=eu-central-1
    STORAGE_S3_BUCKET=my-kamerplanter-bucket
    STORAGE_S3_ACCESS_KEY_ID=<from secret>
    STORAGE_S3_SECRET_ACCESS_KEY=<from secret>
    STORAGE_S3_USE_PATH_STYLE=false
    STORAGE_S3_FORCE_TLS=true
    ```

=== "MinIO in-cluster"

    ```bash
    STORAGE_BACKEND=s3
    STORAGE_S3_ENDPOINT_URL=http://minio.kamerplanter.svc:9000
    STORAGE_S3_REGION=us-east-1
    STORAGE_S3_BUCKET=kamerplanter
    STORAGE_S3_ACCESS_KEY_ID=<from secret>
    STORAGE_S3_SECRET_ACCESS_KEY=<from secret>
    STORAGE_S3_USE_PATH_STYLE=true
    STORAGE_S3_FORCE_TLS=false
    STORAGE_S3_ALLOW_PRIVATE_ENDPOINT=true
    ```

=== "Hetzner Object Storage"

    ```bash
    STORAGE_BACKEND=s3
    STORAGE_S3_ENDPOINT_URL=https://fsn1.your-objectstorage.com
    STORAGE_S3_REGION=eu-central
    STORAGE_S3_BUCKET=my-kamerplanter-bucket
    STORAGE_S3_ACCESS_KEY_ID=<from secret>
    STORAGE_S3_SECRET_ACCESS_KEY=<from secret>
    STORAGE_S3_USE_PATH_STYLE=false
    STORAGE_S3_FORCE_TLS=true
    ```

---

## Frequently Asked Questions

??? question "Can I store environment variables as Kubernetes Secrets?"
    Yes. Use Kubernetes Secrets for sensitive values (`ARANGODB_PASSWORD`, `JWT_SECRET_KEY`) and reference them in the Deployment manifest via `valueFrom.secretKeyRef`.

??? question "How can I verify which values the backend is actually using?"
    With `DEBUG=true`, the backend logs all loaded settings at startup. Alternatively, inside the container:
    ```bash
    docker compose exec backend python -c "from app.config.settings import settings; print(settings.model_dump())"
    ```
    Passwords and secrets are not shown in plain text.

---

## See Also

- [Local Setup](../development/local-setup.md)
- [Troubleshooting](../guides/troubleshooting.md)
- [Kubernetes Deployment](../deployment/kubernetes.md)
