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
| `MDNS_ENABLED` | `true` | No | Enable mDNS service announcement (`_kamerplanter._tcp.local.`) |
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
| Docker Compose / Bare Metal | `true` | Backend runs directly on the LAN — works out of the box |
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

# mDNS Discovery (LAN only, disable in K8s)
MDNS_ENABLED=true
INSTANCE_ID=

# Optional external APIs
PERENUAL_API_KEY=
HA_URL=
HA_ACCESS_TOKEN=

# Knowledge Service — Re-Ranking (empty = disabled)
RERANKER_URL=
RERANKER_INITIAL_K=20
RERANKER_TOP_K=5
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
