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

## See also

- [Kubernetes Deployment](kubernetes.md) — Step-by-step guide
- [Environment Variables](../reference/environment-variables.md) — Full reference of all environment variables
