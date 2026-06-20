# Configure Storage (Object Storage)

Kamerplanter stores all binary data — photos, imports, exports, and backups — through an interchangeable storage adapter. As a platform admin, you choose the backend that suits your infrastructure: a local filesystem (recommended for self-hosted installations and Light Mode) or an S3-compatible object storage service (for production, community, and enterprise setups).

!!! note "Platform admins only"
    Storage settings are exclusively accessible to users with the platform role **admin**. In Light Mode, the page is available directly without login.

---

## Prerequisites

- Platform role **admin** (Full Mode) or Light Mode operation
- Access via **Admin Settings > Storage**

---

## The Two Storage Backends

| Backend | Key | Use Case |
|---------|-----|---------|
| **Local Filesystem** | `local-fs` | Light Mode, self-hosted, homelab, Raspberry Pi — no external dependency |
| **S3-compatible** | `s3` | Production, community garden, enterprise — AWS S3, MinIO, Hetzner Object Storage, Backblaze B2, Cloudflare R2, Wasabi, DigitalOcean Spaces, Google Cloud Storage (S3 API) |

The active backend is platform-wide. All tenants share the same storage adapter — tenant isolation is enforced through the key schema `t/{tenant_key}/...` in the storage.

---

## Configuring the Backend

Open **Admin Settings > Storage**. The page shows:

- The currently active backend (`local-fs` or `s3`)
- Connection status (green = reachable, red = error)
- The non-secret configuration fields for the active backend

### Local Filesystem (`local-fs`)

The local filesystem is the default backend and requires no external configuration. Files are stored on a persistent volume at the container path `/data/attachments`.

!!! tip "Light Mode and self-hosted"
    In Light Mode and on single-node installations, `local-fs` is the right choice. No cloud account, no API key — your data stays on your server.

**Limitation with multiple replicas (Kubernetes):**

When the backend runs with more than one replica, the persistent volume must support the `ReadWriteMany` (RWX) access mode (e.g., NFS, Longhorn, CephFS). With `ReadWriteOnce` (RWO), only one replica is possible.

!!! warning "Set a signing secret when using multiple replicas"
    Without a `STORAGE_LOCALFS_SIGNING_SECRET`, each backend pod generates its own ephemeral secret at startup. Token-based downloads fail when a request reaches a different pod than the one that created the signature. Set the secret as a Kubernetes Secret and reference it via `envFrom`.

### S3-compatible (`s3`)

The admin UI allows you to set all non-secret S3 parameters directly:

| Field | Description | Example |
|-------|-------------|---------|
| **Endpoint URL** | Full URL of the S3 endpoint | `https://s3.eu-central-1.amazonaws.com` |
| **Region** | AWS region or MinIO region | `eu-central-1` |
| **Bucket** | Bucket name (must be created beforehand) | `kamerplanter-prod` |
| **Path Style** | `true` for MinIO and most non-AWS providers | On/Off |
| **Force TLS** | Block plain HTTP (recommended: on) | On/Off |
| **KMS Key ID** | Optional customer-managed key for server-side encryption | ARN or key ID |

!!! danger "S3 credentials are NOT set through the UI"
    `Access Key ID` and `Secret Access Key` are secrets and are configured **exclusively** via environment variables or the External Secrets Operator (ESO) — never through the admin UI. For details, see [Environment Variables — Object Storage](../reference/environment-variables.md#object-storage-nfr-013) and [Helm Charts — Storage Configuration](../deployment/helm.md#storage-configuration-nfr-013).

#### Test Connection

After saving the S3 parameters, you can click **Test Connection**. The backend performs the following checks:

1. Connection to the endpoint (TLS handshake)
2. Checks whether the bucket is accessible (HEAD request)
3. Reports the target region (relevant for GDPR review)

The connection test does not write any data or alter bucket contents.

#### GDPR Note: Target Region

After a successful connection test, the admin UI displays the **target region** of the configured backend. For EU tenants, the region should be within the EU/EEA. For backends outside the EU, a Data Processing Agreement (DPA) with the provider is required (GDPR Art. 28, Art. 46).

---

## How Attachments Work in the System

The frontend knows neither bucket names nor S3 URLs. Users see only stable API addresses of the form:

```
/api/v1/t/{tenant-slug}/attachments/{attachment-id}
```

All uploads, downloads, and deletions go exclusively through the backend. Photos, import files, and exports are stored in the storage under the path schema:

```
t/{tenant_key}/{category}/{yyyy}/{mm}/{ulid}.{ext}
```

The category is one of: `diary`, `ipm`, `harvest`, `post_harvest`, `task`, `import`, `export`, `id_recognition`, `tenant_export`, `plant`.

!!! note "Thumbnails"
    When uploading images, Kamerplanter asynchronously generates up to three thumbnail variants (128 px, 512 px, 1280 px) and stores them in the same backend.

---

## Health Check and Monitoring

The storage status is part of the `/health/ready` endpoint. If the configured backend is unreachable, the endpoint responds with HTTP 503 — the pod is not marked as ready and receives no traffic.

Prometheus metrics (when enabled):

| Metric | Description |
|--------|-------------|
| `kp_storage_health_status` | 1 = reachable, 0 = error |
| `kp_storage_upload_total` | Uploads by backend, category, status |
| `kp_storage_upload_bytes` | Upload volume |
| `kp_storage_object_count` | Object count per tenant (daily) |

---

## Migrating Between Backends

When switching from `local-fs` to S3 (or vice versa), Kamerplanter provides a CLI migration script:

```bash
# Dry run: shows all operations without writing
python -m scripts.storage.migrate --from local-fs --to s3 --dry-run

# Lossless migration with checksum verification
python -m scripts.storage.migrate --from local-fs --to s3 --checksum-verify

# Provider switch within S3
python -m scripts.storage.migrate --from s3 --to s3 --target-bucket=new-bucket

# Rollback migration
python -m scripts.storage.migrate --from s3 --to local-fs --checksum-verify
```

The migration runs as a Celery task with progress tracking and can be resumed after interruption. An audit log documents every migrated object.

!!! warning "Switch the backend only after migration is complete"
    Only switch the backend in admin settings to the new target once the migration script has finished and the checksum comparison is green. Otherwise, new uploads land in the new backend while old files remain in the old one.

---

## Frequently Asked Questions

??? question "What happens to attachments when a tenant is deleted?"
    Kamerplanter deletes all binary data for the tenant via `delete_prefix("t/{tenant_key}/")` in the configured storage backend. This happens before ArangoDB entries are removed, so that metadata is still available for lookup. The result is documented in the audit log. For details, see [Privacy (GDPR) — Deleting Your Account](privacy.md#deleting-your-account-gdpr-art-17).

??? question "Can I use MinIO in-cluster as the S3 backend?"
    Yes. Set `STORAGE_S3_ENDPOINT_URL` to the internal MinIO address (e.g., `http://minio.kamerplanter.svc:9000`), set `STORAGE_S3_USE_PATH_STYLE=true`, and `STORAGE_S3_ALLOW_PRIVATE_ENDPOINT=true`. The latter variable permits the backend to connect to a private (not publicly reachable) endpoint. For details, see [Environment Variables — Object Storage](../reference/environment-variables.md#object-storage-nfr-013).

??? question "Do I need to create a PVC manually for local-fs?"
    No. The Helm chart automatically creates the PVC `backend-attachments` when `storage.backend: local-fs` is set. The default is 100 Gi with `ReadWriteOnce`. For multi-replica setups, set `storage.localFs.pvc.accessMode: ReadWriteMany` and a compatible storage class (e.g., `longhorn` or `nfs`).

??? question "How do I see how much storage is in use?"
    The admin statistics page shows estimated storage usage per tenant (based on the daily-updated Prometheus gauge `kp_storage_object_size_bytes`). For local filesystem, PVC usage can also be read directly from the Kubernetes dashboard or with `kubectl get pvc backend-attachments`.

??? question "Are EXIF data removed from photos?"
    Yes. On upload, the backend removes all EXIF metadata by default (GPS coordinates, camera model, timestamp). If a tenant wants to retain EXIF data (e.g., for professional documentation), this can be enabled per category via `STORAGE_KEEP_EXIF_<CATEGORY>=true`.

---

## See Also

- [Environment Variables — Object Storage](../reference/environment-variables.md#object-storage-nfr-013)
- [Helm Charts — Storage Configuration](../deployment/helm.md#storage-configuration-nfr-013)
- [Privacy (GDPR)](privacy.md) — Data deletion, EXIF strip, portability
- [Platform Admin](admin.md) — Admin area overview
- [Deployment Profiles](../deployment/betriebsprofile.md) — Which profile do I need?
