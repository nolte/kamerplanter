# Helm Charts

The Kamerplanter Helm chart is based on the [bjw-s common library](https://bjw-s-labs.github.io/helm-charts/) and defines all Kubernetes resources in a single chart. Container images and the chart itself are published as OCI artifacts on the GitHub Container Registry.

---

## Registry overview

| Artifact | OCI URL |
|----------|---------|
| Helm chart | `oci://ghcr.io/nolte/kamerplanter-helm/kamerplanter` |
| Backend image | `ghcr.io/nolte/kamerplanter-backend` |
| Frontend image | `ghcr.io/nolte/kamerplanter-frontend` |

---

## Chart information

```yaml
name: kamerplanter
type: application
version: 0.2.0          # Chart version (Helm-specific)
appVersion: "1.0.0"     # Application version
```

### Dependencies

| Dependency | Version | Source | Purpose |
|-----------|---------|--------|---------|
| common (bjw-s) | 4.6.2 | bjw-s-labs Helm Charts | Library chart for standardized Kubernetes resources |
| valkey | 0.9.3 | OCI: ghcr.io/valkey-io/valkey-helm | Redis-compatible cache + Celery broker |

---

## Chart structure

```
helm/kamerplanter/
├── Chart.yaml            # Chart metadata and dependencies
├── Chart.lock            # Pinned dependency versions
├── values.yaml           # Default values (production)
├── values-dev.yaml       # Override for development
├── templates/
│   └── common.yaml       # bjw-s library loader
└── charts/
    ├── common-4.6.2.tgz  # bjw-s Common Library
    └── valkey-0.9.3.tgz  # Valkey sub-chart
```

The chart uses the bjw-s `common.loader.all` approach: all Kubernetes resources (Deployments, StatefulSets, Services, ConfigMaps, Ingress) are defined declaratively via `values.yaml` — there are no custom templates.

---

## Configuration reference

### Controllers (Deployments & StatefulSets)

#### Backend

```yaml
controllers:
  backend:
    type: deployment
    replicas: 2                    # Adjustable
    strategy: RollingUpdate
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-backend
          tag: latest              # In production: use a fixed version
        env:
          ARANGODB_HOST: "..."
          ARANGODB_PORT: "8529"
          ARANGODB_DATABASE: "kamerplanter"
          ARANGODB_USERNAME: "root"
          ARANGODB_PASSWORD: "..."
          REDIS_URL: "redis://kamerplanter-valkey:6379/0"
          CORS_ORIGINS: '["..."]'
          DEBUG: "false"
          KAMERPLANTER_MODE: "light"    # or "standard"
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: "1"
            memory: 512Mi
```

#### Frontend

```yaml
controllers:
  frontend:
    type: deployment
    replicas: 2
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-frontend
          tag: latest
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
```

The frontend is served behind nginx. The nginx configuration is automatically mounted as a ConfigMap and proxies `/api/` requests to the backend.

#### ArangoDB

```yaml
controllers:
  arangodb:
    type: statefulset
    replicas: 1                    # Single node (no cluster)
    containers:
      main:
        image:
          repository: arangodb
          tag: "3.11"
        env:
          ARANGO_ROOT_PASSWORD: "..."
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: "1"
            memory: 1Gi
    statefulset:
      volumeClaimTemplates:
        - name: data
          accessMode: ReadWriteOnce
          size: 5Gi                 # Adjustable
          globalMounts:
            - path: /var/lib/arangodb3
```

### Services

```yaml
service:
  backend:
    controller: backend
    ports:
      http:
        port: 8000
  frontend:
    controller: frontend
    ports:
      http:
        port: 80
  arangodb:
    controller: arangodb
    ports:
      http:
        port: 8529
```

### Ingress

```yaml
ingress:
  main:
    enabled: true                   # Default: disabled
    hosts:
      - host: plants.example.com
        paths:
          - path: /api
            pathType: Prefix
            service:
              identifier: backend
          - path: /
            pathType: Prefix
            service:
              identifier: frontend
```

!!! tip "TLS"
    For HTTPS, add a `tls` section and use e.g. cert-manager with Let's Encrypt:

    ```yaml
    ingress:
      main:
        enabled: true
        annotations:
          cert-manager.io/cluster-issuer: letsencrypt-prod
        hosts:
          - host: plants.example.com
            paths: [...]
        tls:
          - secretName: kamerplanter-tls
            hosts:
              - plants.example.com
    ```

### Valkey (Redis-compatible cache)

```yaml
valkey:
  dataStorage:
    enabled: true
    size: 1Gi
```

---

## Environment variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `ARANGODB_HOST` | Yes | — | Hostname of the ArangoDB service |
| `ARANGODB_PORT` | Yes | `8529` | Port of the ArangoDB service |
| `ARANGODB_DATABASE` | Yes | `kamerplanter` | Database name |
| `ARANGODB_USERNAME` | Yes | `root` | Database user |
| `ARANGODB_PASSWORD` | Yes | — | Database password |
| `ARANGO_ROOT_PASSWORD` | Yes | — | ArangoDB root password (must match `ARANGODB_PASSWORD`) |
| `REDIS_URL` | Yes | — | Valkey/Redis connection URL |
| `CORS_ORIGINS` | Yes | — | Allowed origins as JSON array |
| `DEBUG` | No | `false` | Enable debug mode |
| `KAMERPLANTER_MODE` | No | `light` | `light` (no auth) or `standard` (with auth) |
| `REQUIRE_EMAIL_VERIFICATION` | No | `false` | Email verification on registration |

---

## Development overrides (values-dev.yaml)

A separate values file exists for local development, used automatically by Skaffold:

| Setting | Production | Development |
|---------|-----------|-------------|
| Replicas (backend/frontend) | 2 | 1 |
| Update strategy | RollingUpdate | Recreate |
| DEBUG | false | true |
| Resource limits | Strict | Generous |
| Frontend port | 80 (nginx) | 5173 (Vite dev server) |
| ArangoDB PVC | 5 Gi | 2 Gi |
| Ingress host | (configurable) | `kamerplanter.local` |

---

## Common customizations

### Reduce resources (small cluster / Raspberry Pi)

```yaml
controllers:
  backend:
    replicas: 1
    containers:
      main:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
  frontend:
    replicas: 1
    containers:
      main:
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 250m
            memory: 128Mi
  arangodb:
    containers:
      main:
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Pin a specific image version

```yaml
controllers:
  backend:
    containers:
      main:
        image:
          tag: "1.2.3"    # Instead of "latest"
  frontend:
    containers:
      main:
        image:
          tag: "1.2.3"
```

!!! tip "Image tags"
    In production, always use fixed version tags instead of `latest`. This ensures that a `helm upgrade` deploys the expected version.

---

## Storage Configuration (NFR-013) {#storage-configuration-nfr-013}

Kamerplanter stores all binary data (photos, imports, exports) through an interchangeable storage adapter. The choice of backend and the associated Kubernetes persistence are fully controlled through `values.yaml`.

### Local Filesystem (Default)

In the default setup, the chart automatically creates the PVC `backend-attachments` and mounts it in the backend and Celery worker pods at `/data/attachments`.

```yaml
storage:
  backend: local-fs                  # Default; no external storage needed
  maxFileSizeMb: 25
  presignTtlSeconds: 900
  virusScan:
    enabled: false
    endpoint: ""

  localFs:
    root: /data/attachments           # Container-internal mount path
    pvc:
      size: 100Gi
      accessMode: ReadWriteOnce       # For single-replica (default)
      storageClass: ""                # Empty = cluster default
```

**Multi-replica operation** (backend replicas > 1):

```yaml
storage:
  localFs:
    pvc:
      accessMode: ReadWriteMany       # Requires an RWX-capable StorageClass
      storageClass: longhorn          # Or: nfs, cephfs, etc.
```

!!! warning "Signing secret required with RWX"
    With more than one backend replica, `STORAGE_LOCALFS_SIGNING_SECRET` must be set as a stable Kubernetes Secret. Without it, each pod generates its own ephemeral signing secret — token-based downloads fail when the validation request reaches a different pod than the one that signed the token.

    ```bash
    kubectl create secret generic kamerplanter-storage-signing \
      --from-literal=STORAGE_LOCALFS_SIGNING_SECRET="$(openssl rand -hex 32)" \
      --namespace kamerplanter
    ```

    Reference it in the chart via `envFrom`:

    ```yaml
    controllers:
      backend:
        containers:
          main:
            envFrom:
              - secretRef:
                  name: kamerplanter-storage-signing
    ```

### S3-compatible (Production)

Non-secret S3 parameters are set directly in `values.yaml`. Credentials come exclusively from the External Secrets Operator (ESO) — never as plain text in Git.

```yaml
storage:
  backend: s3
  maxFileSizeMb: 25
  presignTtlSeconds: 900

  s3:
    endpointUrl: https://s3.eu-central-1.amazonaws.com
    region: eu-central-1
    bucket: kamerplanter-prod
    usePathStyle: false               # true for MinIO and non-AWS providers
    forceTls: true
    kmsKeyId: ""                      # Optional: customer-managed key (SSE-KMS)

    # S3 credentials via External Secrets Operator (NEVER plain text)
    credentialsRef:
      secretName: storage-s3-credentials
      accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
      secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
```

**External Secrets Operator — ESO Secret:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: storage-s3-credentials
  namespace: kamerplanter
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend              # Or AWS Secrets Manager, etc.
    kind: ClusterSecretStore
  target:
    name: storage-s3-credentials
    creationPolicy: Owner
  data:
    - secretKey: STORAGE_S3_ACCESS_KEY_ID
      remoteRef:
        key: kamerplanter/storage
        property: access_key_id
    - secretKey: STORAGE_S3_SECRET_ACCESS_KEY
      remoteRef:
        key: kamerplanter/storage
        property: secret_access_key
```

!!! tip "Without ESO: manual Kubernetes Secret"
    If no External Secrets Operator is available, create the secret manually:
    ```bash
    kubectl create secret generic storage-s3-credentials \
      --from-literal=STORAGE_S3_ACCESS_KEY_ID="your-access-key" \
      --from-literal=STORAGE_S3_SECRET_ACCESS_KEY="your-secret-key" \
      --namespace kamerplanter
    ```
    The secret should come from a secure vault and must **never** be stored in Git.

#### NetworkPolicy for S3 Endpoints

The chart includes a NetworkPolicy that restricts outbound connections to the configured S3 endpoint and blocks access to the cloud metadata IP (`169.254.169.254`) (SSRF protection):

```yaml
networkPolicies:
  storage:
    enabled: true
    blockMetadataEndpoint: true      # Blocks 169.254.169.254 (default: true)
```

#### MinIO In-Cluster

```yaml
storage:
  backend: s3
  s3:
    endpointUrl: http://minio.kamerplanter.svc:9000
    region: us-east-1
    bucket: kamerplanter
    usePathStyle: true
    forceTls: false
    allowPrivateEndpoint: true       # Permits a non-publicly-reachable endpoint
    credentialsRef:
      secretName: storage-s3-credentials
      accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
      secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
```

### Virus Scanning (optional)

```yaml
storage:
  virusScan:
    enabled: true
    endpoint: http://clamav-rest.kamerplanter.svc:9000
```

ClamAV must run as a separate deployment in the cluster. The backend blocks an upload when the scanner reports a finding.

### Common Provider Configurations

=== "Hetzner Object Storage"

    ```yaml
    storage:
      backend: s3
      s3:
        endpointUrl: https://fsn1.your-objectstorage.com
        region: eu-central
        bucket: my-kamerplanter-bucket
        usePathStyle: false
        forceTls: true
        credentialsRef:
          secretName: storage-s3-credentials
          accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
          secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
    ```

=== "Cloudflare R2"

    ```yaml
    storage:
      backend: s3
      s3:
        endpointUrl: https://<account-id>.r2.cloudflarestorage.com
        region: auto
        bucket: kamerplanter
        usePathStyle: false
        forceTls: true
        credentialsRef:
          secretName: storage-s3-credentials
          accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
          secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
    ```

=== "Backblaze B2 (S3 API)"

    ```yaml
    storage:
      backend: s3
      s3:
        endpointUrl: https://s3.eu-central-003.backblazeb2.com
        region: eu-central-003
        bucket: kamerplanter
        usePathStyle: false
        forceTls: true
        credentialsRef:
          secretName: storage-s3-credentials
          accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
          secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
    ```

---

## See also

- [Kubernetes Deployment](kubernetes.md) — Step-by-step guide
- [Environment Variables](../reference/environment-variables.md) — Full reference of all environment variables
- [Configure Storage (Object Storage)](../user-guide/object-storage.md) — Admin UI and migration
