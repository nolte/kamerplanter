# Helm Charts

The Kamerplanter Helm chart is based on the [bjw-s common library](https://bjw-s-labs.github.io/helm-charts/) and defines all Kubernetes resources in a single chart. Container images and the chart itself are published as OCI artifacts on the GitHub Container Registry.

---

## Registry overview

| Artifact | OCI URL |
|----------|---------|
| Helm chart | `oci://ghcr.io/nolte/charts/kamerplanter` |
| Backend image | `ghcr.io/nolte/kamerplanter-backend` |
| Frontend image | `ghcr.io/nolte/kamerplanter-frontend` |

---

## Chart information

<!-- Source: helm/kamerplanter/Chart.yaml -->

```yaml
name: kamerplanter
type: application
version: 0.2.1-dev      # Chart version in the develop tree — pre-release channel
appVersion: "1.0.0"     # Application version
```

!!! danger "`-dev` is the development channel, not a release"

    The `-dev` suffix is not a typo. The `develop` tree always carries a
    pre-release with that suffix, and `helm push` derives the OCI tag verbatim
    from this line. The tag
    `oci://ghcr.io/nolte/charts/kamerplanter:0.2.1-dev` is therefore overwritten
    by every merge into `develop` that touches `helm/` — that is what the
    channel is for.

    A release, by contrast, publishes under the bare version without a suffix,
    for example `0.1.0`. The two channels are disjoint and cannot overlap: the
    `dev` pre-release identifier is refused on the release path, so a tag
    `v0.3.0-dev` is rejected. `-rc` and `-beta` remain legal.

    What is enforced is the `dev` identifier alone, not the number in front of
    it. `0.2.1` names the intended next release and nothing keeps it ahead of
    the published line — once `v0.2.1` ships, `0.2.1-dev` sorts below it, and no
    schedule bumps this value. That is deliberate: any `-dev` number is
    collision-proof, so a periodic bump would buy nothing.

    **Never use a `-dev` version in a deployment.** Pin a published version or
    the manifest digest. Why this is not theoretical, and how both channels are
    enforced: [CI/CD — Two channels](ci-cd.md#two-channels).
    <!-- #1222 -->

### Dependencies

| Dependency | Version | Source | Purpose |
|-----------|---------|--------|---------|
| common (bjw-s) | 5.2.1 | bjw-s-labs Helm Charts | Library chart for standardized Kubernetes resources |
| valkey | 0.12.0 | OCI: ghcr.io/valkey-io/valkey-helm | Redis-compatible cache + Celery broker |
| ollama | 1.87.0 | `otwld/ollama-helm` | Local LLM inference, off by default (`ollama.enabled: false`) |

<!-- Source: helm/kamerplanter/Chart.yaml -->

!!! note "Ollama subchart is off by default"
    The Ollama Helm chart (`otwld/ollama-helm`) is listed as the third dependency, but it only renders with `ollama.enabled: true`. Without that switch the release contains no Ollama; how the deployment profiles use Ollama is described under [Deployment Profiles → Professional](betriebsprofile.md#profi).

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
    ├── common-5.2.1.tgz  # bjw-s Common Library
    ├── valkey-0.12.0.tgz # Valkey sub-chart
    └── ollama-1.87.0.tgz # Ollama sub-chart (off by default)
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
    replicas: 1                    # Chart default; typically raised to 2 for production (see Kubernetes Deployment)
    strategy: RollingUpdate
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-backend
          tag: 0.2.1@sha256:af9bec…    # immutable digest, written by the release job — see "Pin a specific image version"
        envFrom:
          - secret: kamerplanter-secrets    # ARANGODB_PASSWORD, JWT_SECRET_KEY, FERNET_KEY, ERASURE_TOMBSTONE_SALT, LOG_PSEUDONYM_SALT
        env:
          ARANGODB_HOST: "..."
          ARANGODB_PORT: "8529"
          ARANGODB_DATABASE: "kamerplanter"
          ARANGODB_USERNAME: '{{ .Values.database.arangodb.appUsername }}'    # kamerplanter
          REDIS_URL: "redis://kamerplanter-valkey:6379/0"
          CORS_ORIGINS: '["..."]'
          DEBUG: "false"
          KAMERPLANTER_MODE: "light"    # or "full" (chart default)
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: "1"
            memory: 2Gi                 # Image uploads (REQ-034) decode in memory — 512Mi OOMKills on upload
```

!!! danger "`ARANGODB_PASSWORD`, `JWT_SECRET_KEY`, `FERNET_KEY`, `ERASURE_TOMBSTONE_SALT`, `LOG_PSEUDONYM_SALT` never come from `env:`"
    The real chart deliberately does **not** declare these five values under `env:` — they come exclusively via `envFrom: - secret: kamerplanter-secrets` from a secret you create beforehand. Without that secret (or with an unchanged default value inside it), the backend refuses to start when `DEBUG=false`; the Celery worker controller draws from the same secret and checks `LOG_PSEUDONYM_SALT` just as strictly. Details: [Kubernetes Deployment — Create the mandatory secrets](kubernetes.md), [Configuration Matrix — Mandatory secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

#### Celery worker {#celery-worker}

The worker processes three queues (issue #2128):

| Queue | Contents |
|---|---|
| `critical` | Retention periods and erasures (NFR-011), security and privacy sweeps, notifications, frost warnings, the actuator control loop |
| `celery` | everything else — Celery's default queue under its existing name |
| `bulk` | long, external runs: dataset and reference-image acquisition, master-data enrichment, glossary warm-up, storage migrations |

The chart starts the worker with `-Q critical,celery,bulk`. **A queue no worker reads keeps its tasks in Valkey forever** — without any error. If you override the worker `args` in your values, carry the queue list over completely or drop `-Q` altogether (the worker then reads every queue the application declares).

##### One worker per queue {#celery-worker-pro-queue}

One switch gives every queue a worker of its own:

```yaml
celeryWorkers:
  dedicatedQueues: true
```

| Deployment | Queue |
|---|---|
| `celery-worker` | `critical` |
| `celery-worker-default` | `celery` |
| `celery-worker-bulk` | `bulk` |

Without the switch (the default) the one `celery-worker` reads all three queues. A long run in `bulk` then occupies one of its two processes; the second keeps working. With the switch, a dataset or image acquisition can no longer hold up a reminder, an erasure or a frost warning at all.

The two additional workers are copies of `celery-worker`: the chart makes them at render time from the **merged** values. Whatever you set on `controllers.celery-worker` in an overlay, via `--set` or in an ArgoCD `valuesObject` (image, environment, `securityContext`, probes, resources, pod options) and on `networkpolicies.celery-worker` (egress) therefore applies to the copies too. Every policy that admits `celery-worker` as a peer (ArangoDB, Valkey, inference-service) admits the copies as well, and every volume of the worker is mounted into the copies. Only the queue differs. To tune one copy, set `controllers.<copy>.<key>`, e.g. `controllers.celery-worker-bulk.containers.main.resources`; the key is merged over that copy. Without the switch there are no copies and such keys have no effect.

!!! warning "Two more pods on the backend's node"
    Each additional worker requests 100m CPU and 512 Mi memory like `celery-worker` (limit 2 Gi). With the default `ReadWriteOnce` volume, every pod that mounts the attachments runs on **one** node — the backend's. Plan that node's memory for it, or switch to [S3](#storage-konfiguration-nfr-013); the workers then spread freely.

If a profile switches `celery-worker` off (the `ki` and `recognition` overlays), no copies are created either. If you override the worker `args` yourself, the rule still holds: every queue needs at least one worker that reads it.

**Acknowledged after the run.** Clean-up runs whose second pass finds nothing left (expired tokens, consents, audit entries, erasure records, IP anonymisation, expired overrides) acknowledge their message only once they are done. If a worker pod disappears mid-run, Valkey hands the message out again after the visibility timeout (just over four hours) instead of losing the run until the next day. Notifications, the actuator control loop and erasure runs still acknowledge on start — a second run there would notify or switch twice.

**Readiness (issue #2154).** The worker counts as ready only once it takes tasks: with `WORKER_READY_FILE` it checks its ArangoDB login at start (for up to 60 seconds), writes the file as soon as its consumer runs, and the startup and readiness probes test it (`test -f`, which costs next to nothing). If a new worker cannot log in after an upgrade — wrong password, application account not provisioned — it exits, never becomes ready, and the rollout keeps the old worker. The liveness probe asks its own worker with `inspect ping -d "celery@${HOSTNAME}"`; an `inspect ping` without a destination succeeds as long as any worker answers.

Every task has a time limit as a backstop: 30 minutes (soft, the task can clean up), after 35 minutes the process is ended. Runs that are resumable or started on purpose (erasure runs, data export, storage migration, dataset acquisition) get three hours. Each worker process now reserves one message ahead instead of four.

#### Frontend

```yaml
controllers:
  frontend:
    type: deployment
    replicas: 1                    # Chart default; typically raised to 2 for production
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-frontend
          tag: latest@sha256:fea5a3…
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
          tag: "3.12.9"
        env:
          ARANGO_ROOT_PASSWORD:             # only ARANGO_ROOT_PASSWORD, not the whole Secret
            valueFrom:
              secretKeyRef:
                name: '{{ .Values.database.arangodb.rootPasswordSecret }}'
                key: ARANGO_ROOT_PASSWORD
                optional: true
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
          advancedMounts:
            main:
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
        port: 80          # Service port stays 80 (Ingress/DNS)
        targetPort: 8080  # nginx-unprivileged container listens on 8080, not 80
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
    enabled: true                   # without hosts no Ingress is created
    hosts:
      - host: plants.example.com
        paths:
          - path: /              # /api too: the frontend nginx proxies it to the backend
            pathType: Prefix
            service:
              identifier: frontend
```

Do not route `/api` straight to the backend Service: the backend NetworkPolicy admits only the frontend on port 8000, and the frontend nginx applies the upload limit and the `X-Forwarded-For` entry that `TRUSTED_PROXY_HOPS: "1"` is set for.

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

#### Upload limit (request body)

The frontend nginx accepts request bodies up to `storage.maxFileSizeMb` + 1 MiB (default: `26m`). The extra MiB covers the multipart envelope of an upload: an attachment of the full allowed size reaches the backend, a slightly larger one gets a clear `413` answer from there, and anything above the limit is refused by nginx itself with `413`. Without this setting the limit was nginx's default of 1 MiB, and every larger upload failed at the proxy.

The chart sets the same limit on the ingress `main` as the annotation `nginx.ingress.kubernetes.io/proxy-body-size`, because ingress-nginx would otherwise cut at 1 MiB too. Both follow `storage.maxFileSizeMb`: when you raise the upload limit, nginx and the ingress grow with it. Traefik and Contour/Envoy do not read the annotation and set no body limit of their own; there the frontend nginx's limit applies, as long as `/` and `/api` go through the frontend. If you use an ingress under another key than `main` or your own `HTTPProxy`, set the limit there yourself to the same value.

The backend enforces the same limit again before it reads an upload. That matters when a request bypasses the frontend nginx — via `kubectl port-forward`, from inside the cluster or through an ingress without a body limit. An upload with a larger `Content-Length` gets `413` (`REQUEST_BODY_TOO_LARGE`) without the backend reading a byte; an upload without a declared length is cut off at the limit. Every other request (JSON, forms) may be at most 1 MiB.

While reading, the backend keeps uploads above 1 MiB in `/tmp`, a memory volume of 64 MiB in the chart. So that concurrent uploads cannot fill it, they share a budget of 52 MiB (`UPLOAD_SPOOL_BUDGET_MB`). It counts the bytes that already arrived: at the default limit two full uploads run at the same time, a further one waits up to 30 seconds (`UPLOAD_SPOOL_WAIT_SECONDS`) and then gets `503` with `Retry-After`. If you raise `storage.maxFileSizeMb` above 51, the chart sets the budget to one full upload, so only one large upload runs at a time. The size of `/tmp` does not follow automatically: from an upload limit of about 60 MiB you must raise `persistence.backend-tmp.sizeLimit` yourself.

### Valkey (Redis-compatible cache) {#valkey}

Valkey is both cache and Celery broker: the tasks wait in it for the worker. The chart ships these defaults for it:

```yaml title="values.yaml (default)"
valkey:
  deploymentStrategy: Recreate
  dataStorage:
    enabled: true
    requestedSize: 1Gi
    keepPvc: true
  valkeyConfig: |
    maxmemory 256mb
    maxmemory-policy noeviction
    appendonly yes
    appendfsync everysec
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      memory: 640Mi    # at least twice maxmemory
```

- **Own volume:** Valkey keeps its data on a `PersistentVolumeClaim` (`kamerplanter-valkey`, 1 GiB, `ReadWriteOnce`). It survives `helm uninstall`. The Valkey chart calls the size `requestedSize` — it does not read a `size` key.
- **`Recreate`:** the old Valkey pod ends before the new one starts. A `ReadWriteOnce` volume attaches to one node; a new pod next to the old one could not reach the volume from another node.
- **`noeviction` rather than an eviction policy:** when memory is full, Valkey refuses new writes instead of silently dropping waiting tasks. A full memory thus shows up as an error.
- **`appendonly yes`** records every change (written to disk once per second); after a restart the tasks of the last seconds are back too.
- **Memory limit at least twice `maxmemory`** (default 640 MiB for 256 MB): to rewrite the append-only file and to take snapshots, Valkey forks a child process that copies the data set; every page that changes meanwhile occupies memory twice. On top come the rewrite buffer and the client buffers, which do not count against `maxmemory`. With a tight limit, Kubernetes kills Valkey before Valkey itself can refuse. If you raise `maxmemory`, raise `resources.limits.memory` with it — the chart's render check requires at least twice.
- **Watch the memory:** with `noeviction` a full Valkey reports errors (`OOM command not allowed`) instead of losing tasks — backend and worker can then no longer queue tasks. Set up an alert on `used_memory` relative to `maxmemory` (for example from 80 %) so you can step in first.

!!! info "On upgrade"
    Up to this version Valkey's `/data` sat on an ephemeral `emptyDir`: the chart set `valkey.dataStorage.size`, a key the Valkey chart does not know, so no volume was created. Every Valkey restart lost the waiting tasks. The upgrade creates the volume and restarts Valkey once (`Recreate`).

    - **One-time loss of waiting tasks:** whatever is queued at the restart is lost. Let the queue drain first — for example scale Celery Beat to 0 (`kubectl scale deployment kamerplanter-celery-beat --replicas=0`), wait until the worker has processed everything, then upgrade; Beat starts again with the upgrade. Beat queues scheduled tasks again at their next run anyway.
    - **A StorageClass is a prerequisite:** the volume names no StorageClass. If your cluster has no default StorageClass, the volume — and with it Valkey — stays `Pending`; without the broker no component can queue tasks. Check with `kubectl get storageclass` (marked `(default)`), or name a StorageClass explicitly in `valkey.dataStorage.className`.
    - **Reinstallation:** the volume survives `helm uninstall`. On start Valkey replays its append-only file — including the tasks of an old installation. Delete the PVC `kamerplanter-valkey` before reinstalling if those should not run.

!!! warning "Valkey without password and without TLS"
    Backend, worker and beat connect through `REDIS_URL` (`redis://kamerplanter-valkey:6379/0`) without a password and without encryption; the Valkey chart runs with its default of no authentication (`auth.enabled: false`) and no TLS. Valkey is protected only by the chart's NetworkPolicies: only backend, worker and beat may reach the Valkey pod. So do not switch the NetworkPolicies off, and run Kamerplanter only in a cluster whose CNI enforces NetworkPolicies.

---

## Environment variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `ARANGODB_HOST` | Yes | — | Hostname of the ArangoDB service |
| `ARANGODB_PORT` | Yes | `8529` | Port of the ArangoDB service |
| `ARANGODB_DATABASE` | Yes | `kamerplanter` | Database name |
| `ARANGODB_USERNAME` | Yes | `kamerplanter` | Database user — in the chart the application account from `database.arangodb.appUsername`, which the `app-user` container in the ArangoDB pod creates (read/write on the application database only). `root` restores the old behaviour. |
| `ARANGODB_PASSWORD` | Yes | — | Database password. Comes from the `kamerplanter-secrets` secret (`envFrom`) in the chart, **not** from `env:`. |
| `ARANGO_ROOT_PASSWORD` | Yes | — | ArangoDB root password. Read by the ArangoDB pod only (Secret from `database.arangodb.rootPasswordSecret`, default `kamerplanter-secrets`). A value of its own, separate from `ARANGODB_PASSWORD`, is recommended. |
| `JWT_SECRET_KEY` | Yes | — | JWT signing key, from `kamerplanter-secrets`. Boot blocker with `DEBUG=false` if the chart-internal default is left unchanged. |
| `FERNET_KEY` | Yes | — | Encryption key for OIDC provider secrets, from `kamerplanter-secrets`. Boot blocker with `DEBUG=false` if empty or invalid — **also for the celery-worker controller**, which gets the same value as the backend via `envFrom` from `kamerplanter-secrets`; the backend and the celery worker must use the same key. |
| `ERASURE_TOMBSTONE_SALT` | Yes | — | GDPR pseudonymization salt (≥ 32 characters) for the tombstone hash, the erasure request key and the tenant slug digest, from `kamerplanter-secrets`. Boot blocker with `DEBUG=false` if empty or too short. Must never change once accounts have been erased. |
| `LOG_PSEUDONYM_SALT` | Yes | — | Salt (≥ 32 characters) that keys only the log pseudonyms (`subject=` references, `email_sha256` digests, `requested_by_subject`), from `kamerplanter-secrets`. Boot blocker with `DEBUG=false` if empty or too short — **also for the celery-worker controller**, which gets the same value via `envFrom`. Unlike `ERASURE_TOMBSTONE_SALT`, this value may be rotated. |
| `INTERNAL_SERVICE_TOKEN` | Conditional | — | Only required once `KNOWLEDGE_SERVICE_ENABLED=true` or `INFERENCE_SERVICE_ENABLED=true` is set, also from `kamerplanter-secrets`. For `INFERENCE_SERVICE_ENABLED`, the same requirement applies **to the celery-worker controller too** — it runs the scheduled GDPR erasure of contributed reference images and needs the same access as the backend that writes them (see [Setting Up Plant Identification](inference-service.md)). |
| `REDIS_URL` | Yes | — | Valkey/Redis connection URL |
| `CORS_ORIGINS` | Yes | — | Allowed origins as JSON array |
| `DEBUG` | No | `false` | Enable debug mode. Setting `true` also disables the boot blocker for the six rows above — **never** set this in production. |
| `KAMERPLANTER_MODE` | No | `full` | `light` (no auth, single user) or `full` (with JWT auth and tenant management). The chart does **not** set this variable on the backend controller by default — the Python-side default `full` applies. On the frontend init container it is hard-set to `full` and must be explicitly overridden for light mode. |
| `REQUIRE_EMAIL_VERIFICATION` | No | `true` | Email verification on registration. Without outbound mail (`EMAIL_ADAPTER` is `console`) set `false` explicitly — otherwise a self-registered account cannot sign in, because the confirmation mail never arrives. |

Full list of every mandatory secret per enabled feature: [Configuration Matrix — Mandatory secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

---

## Development overrides (values-dev.yaml)

A separate values file exists for local development, used automatically by Skaffold:

<!-- Source: helm/kamerplanter/values.yaml, helm/kamerplanter/values-dev.yaml -->

| Setting | Production (`values.yaml`) | Development (`values-dev.yaml`) |
|---------|-----------|-------------|
| Replicas (backend/frontend) | 1 (chart default — typically raised to 2 manually for production, see [Kubernetes Deployment](kubernetes.md)) | 1 |
| Update strategy | RollingUpdate | Recreate |
| DEBUG | false | true |
| Resource limits | Strict | Generous |
| Frontend port | 80 (nginx) | 5173 (Vite dev server) |
| ArangoDB PVC | 5 Gi (chart default) | 2 Gi |
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

A published chart already ships pinned digests (the release job writes them at packaging time) — override them only if you want a version other than the one the chart carries. In that case, override them completely, digest included:

```yaml
controllers:
  backend:
    containers:
      main:
        image:
          tag: "1.2.3@sha256:c6689b…"    # (1)!
  frontend:
    containers:
      main:
        image:
          tag: "1.2.3@sha256:6727d2…"
```

1. Resolve the digest with:
   `docker buildx imagetools inspect ghcr.io/nolte/kamerplanter-backend:1.2.3`

!!! danger "An override without a digest undoes the chart's pinning"
    The override beats the chart default. `tag: "1.2.3"` — without the part
    after the `@` — replaces an immutable reference with a name that can be
    re-pushed. Combined with `pullPolicy: IfNotPresent`, a node may then keep
    serving old bytes without that showing up anywhere. This is exactly what the
    `inference-service` incident hung on.

!!! tip "And do not use `latest` at all"
    `latest` moves on every push to `develop`. A reference that moves cannot be
    rolled back: "the previous image" resolves to the current one. See
    [Deployment and rollback](ci-cd.md#deployment-and-rollback).

---

## Storage Configuration (NFR-013) {#storage-configuration-nfr-013}

Kamerplanter stores all binary data (photos, imports, exports) through an interchangeable storage adapter. You choose the backend and the associated Kubernetes persistence with the `storage` block in your values: the chart derives the `STORAGE_*` variables of the backend and the Celery worker, the PVC and its mounts from it.

!!! warning "Older chart versions did not read the `storage` block"
    Older chart versions did not read the `storage` block: `storage.backend: s3` still shipped `local-fs` with a PVC. If you set up S3 with your own `env` entries (`STORAGE_BACKEND`, `STORAGE_S3_*`) and an extra `envFrom`, those entries keep working — they override the values derived from `storage`. Switch to `storage.backend: s3` on your next upgrade; otherwise the chart keeps creating the (then unused) PVC.

!!! danger "Shared operation: S3 is mandatory"
    The `backend-attachments` PVC is mounted by the backend **and** the Celery worker. A `ReadWriteOnce` volume attaches to exactly one node: a second pod scheduled onto another node stays in `ContainerCreating` with `Multi-Attach error`. For more than one backend or worker replica — and for any multi-tenant operation on a cluster with several nodes — use `storage.backend: s3`. The chart refuses to render when `controllers.backend.replicas` or `controllers.celery-worker.replicas` is greater than 1 and the attachments live on a `ReadWriteOnce` volume. Ways out without S3: `ReadWriteMany` with an RWX-capable StorageClass, or — only on a cluster with exactly one node — `storage.localFs.singleNode: true`.

    Even with a single replica on a multi-node cluster, the backend and the worker must run on the same node, and a rolling update (`maxSurge: 1`) only starts the new pod if it lands on that node. The chart takes care of that (issue #2153): backend and worker pods carry the label `kamerplanter.io/attachments-volume` and require, via `podAffinity`, a pod with that label on the same node (`topologyKey: kubernetes.io/hostname`). A new pod therefore lands on the node the volume is attached to, and the rolling update keeps its zero downtime — no `Recreate` needed. If the new pod no longer fits on that node (CPU, memory), it stays `Pending` with `FailedScheduling` instead of `Multi-Attach error`; the old pod keeps running. With `storage.backend: s3` or `ReadWriteMany` the term renders to `kubernetes.io/os` — a label with the same value on every node, i.e. no constraint.
    <!-- #2124 -->

### Local Filesystem (Default)

In the default setup, the chart automatically creates the PVC `backend-attachments` and mounts it in the backend and Celery worker pods at `/data/attachments`. The PVC carries `helm.sh/resource-policy: keep` and the ArgoCD sync option `Prune=false,Delete=false`: neither `helm uninstall` nor an ArgoCD prune (for example after switching to S3) nor deleting the ArgoCD Application deletes the attachments.

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
      size: 20Gi                      # Chart default; increase as needed
      accessMode: ReadWriteOnce       # For single-replica (default)
      storageClass: ""                # Empty = cluster default
    singleNode: false                 # true only on a cluster with exactly one node
```

**Multi-replica operation** (backend or worker replicas > 1) without S3:

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

Non-secret S3 parameters are set directly in `values.yaml`. Credentials come exclusively from a Secret — ideally produced by the External Secrets Operator (ESO), never as plain text in Git. The chart reads exactly the two keys named in `credentialsRef` (`secretKeyRef`), not the whole Secret. With `storage.backend: s3` the chart renders no PVC and no mount.

!!! warning "Migrate existing attachments first"
    When you switch from `local-fs` to `s3`, the existing files are still on the PVC. Copy them before switching with the migration tool in the backend pod (`python -m scripts.storage.migrate --from local-fs --to s3 --checksum-verify`, see [Configure storage](../user-guide/object-storage.md#migrating-between-backends)). Only then set `storage.backend: s3`; the old PVC stays (see above) and you delete it by hand once the checksum comparison is green.

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

    If the Secret is missing with `storage.backend: s3`, the pods still start (the references are `optional` so that a `local-fs` release does without this Secret), but the storage health check fails and the pod never becomes `Ready` — the rollout stops and the old pods keep serving.

#### NetworkPolicy for S3 Endpoints

There is no separate storage NetworkPolicy. The backend and the Celery worker reach a public S3 endpoint through their general egress rule (`networkpolicies.backend` and `networkpolicies.celery-worker`: ports 80/443 to `0.0.0.0/0` without the RFC1918 ranges and without `169.254.0.0/16` — the cloud metadata address stays blocked). An endpoint inside the cluster or on a private network (MinIO, Ceph RGW) is therefore **not** reachable: add an egress rule for exactly that endpoint to both policies in your values.

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

### Egress for notification channels (Apprise)

Kamerplanter checks Apprise targets when saving and again when sending (scheme allow-list, literal hosts, resolved addresses of Gotify, Matrix and ntfy servers). Two things lie **outside the process** and are up to the operator's network policy:

- Apprise follows HTTP redirects and performs Matrix `.well-known` discovery itself; neither can be controlled in the backend.
- A small window remains between the DNS check and the actual connection (DNS rebinding).

The DNS resolution behind this check is bounded so that a user with host names that never answer cannot slow others down: saving and sending each have their own pool of 8 threads, one user holds at most 3 of them at a time, and an answer must arrive within 3 s. Anything beyond that is refused at once (fail closed), not queued. When saving, answers are cached briefly per host name (60 s, a failure 10 s); when sending, Kamerplanter resolves fresh every time and takes only a refusal from the cache. The values are built in; there is no setting for them.

Targets in private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `100.64.0.0/10` and `fc00::/7`) are refused by default in `full` mode, when saving and when sending. Inside a cluster these are not home-network devices but the API server, ArangoDB and Valkey on pod IPs. `APPRISE_ALLOW_PRIVATE_TARGETS=true` allows them; in `light` mode they are allowed without any setting, and `false` refuses them there too. Loopback, link-local and cloud metadata stay refused in every case.

The chart therefore already restricts egress for `backend` and `celery-worker` (`networkpolicies.backend` and `networkpolicies.celery-worker` in `values.yaml`): destination `0.0.0.0/0` excluding `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` and `169.254.0.0/16`, on ports 80, 443, 465 and 587 only. This keeps cloud metadata and in-cluster targets out of reach even if a redirect leads there. `100.64.0.0/10` is not in that exception list; if your cluster's pods live there, only the backend check protects them.

!!! warning "A LAN Gotify or ntfy needs two opt-ins"
    Kamerplanter refuses a Gotify or ntfy on your home network (`192.168.x.x`) in `full` mode, and the chart's default egress blocks it as well. Set `APPRISE_ALLOW_PRIVATE_TARGETS=true` in the environment of `backend` and `celery-worker`, and add an egress rule for exactly that address and port to `networkpolicies.backend.rules.egress` and `networkpolicies.celery-worker.rules.egress` in your `valuesObject`. The opt-in applies to every user and every private address, pod IPs in the cluster included; the egress rule is then the actual barrier. Without a cluster NetworkPolicy (Docker Compose) no egress limit applies; only the backend check remains.

### Outbound connections to Home Assistant and InvenTree

Kamerplanter does not only check the Home Assistant and InvenTree URL when it is saved: every connection checks the addresses it opens to and connects only to one of them. A DNS answer that changes between the check and the connection (DNS rebinding) therefore does not lead to an internal address. Cloud metadata and link-local stay refused in every case, private addresses only with `HA_ALLOW_PRIVATE_ENDPOINT` or `INVENTREE_ALLOW_PRIVATE_ENDPOINT`. None of these connections follows a redirect, and neither does Web Push.

!!! warning "Web Push is not pinned"
    Kamerplanter checks the push endpoint when it is saved and before every send, but the name is resolved again when connecting. A name that then points at an internal address fails at the TLS certificate before any HTTP request is sent; the TCP connection to it is opened, though. The chart's egress rule (excluding `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`) is the actual barrier here.

!!! note "No HTTP proxy for these connections"
    `HTTP_PROXY` and `HTTPS_PROXY` do not apply to Home Assistant and InvenTree: a proxy would resolve the name itself, which is exactly what the connection must not hand over. If your cluster needs a proxy for outbound traffic, allow Home Assistant and InvenTree directly through an egress rule.

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

## Metrics (Prometheus) {#metrics-prometheus}

One switch: `monitoring.enabled: true`. The chart then sets `METRICS_PORT=9464` on the backend, adds the Service port `metrics`, renders a `ServiceMonitor` and the NetworkPolicy `backend-metrics`, which admits exactly the Prometheus pods to that port.

```yaml
monitoring:
  enabled: true
  scrapeInterval: 30s
  prometheus:
    namespace: monitoring          # namespace Prometheus runs in
    podName: prometheus            # value of the Prometheus pods' app.kubernetes.io/name label
    serviceMonitorLabels:
      release: kube-prometheus-stack   # what the operator's serviceMonitorSelector expects
```

!!! warning "Prometheus Operator required"
    The `ServiceMonitor` is a Prometheus Operator resource (`monitoring.coreos.com/v1`). Without its CRD in the cluster, an install with `monitoring` switched on fails. That is why the default is `false`.

The metrics are **not public**: they run on a port of their own, never as a route of the API. The ingress sends `/` and `/api` to the frontend nginx, which forwards to port 8000 only. The backend policy still admits only the frontend on 8000, so Prometheus cannot use the scrape path to reach the API around nginx.

Served are `http_request_duration_seconds` (histogram) and `http_requests_total` with the labels `method`, `handler` (route pattern, never the path; `unmatched` for a request no route matched) and `status`, `http_requests_in_progress`, and process metrics (memory, CPU, file descriptors). A tenant is deliberately **not** a label — it would multiply every series by the tenant count and disclose the tenant list to anyone allowed to scrape. For the per-tenant view, log lines carry `tenant=ten_…`.

Not included yet: metrics of the Celery worker, and the recording and alerting rules (`PrometheusRule`) of NFR-007.

## Scaling (HPA and PDB) {#scaling}

Without further settings every component runs one pod. You switch on an autoscaler (`HorizontalPodAutoscaler`) and a disruption budget (`PodDisruptionBudget`) per controller; the chart renders them only when you set them.

```yaml title="values-production.yaml (excerpt)"
storage:
  backend: s3                      # prerequisite for more than one backend pod
  # ...

controllers:
  backend:
    horizontalPodAutoscaler:
      minReplicas: 2               # replaces replicas
      maxReplicas: 6
      metrics:
        - type: Resource
          resource:
            name: cpu
            target:
              type: Utilization
              averageUtilization: 70
    podDisruptionBudget:
      minAvailable: 1
  frontend:
    replicas: 2
    podDisruptionBudget:
      minAvailable: 1
```

- **Autoscaler:** with `horizontalPodAutoscaler` the Deployment carries no `replicas`; `minReplicas` takes its role. So a `helm upgrade` or an ArgoCD sync does not reset the pod count to the fixed value. The autoscaler needs the metrics-server in the cluster.
- **A new backend pod only helps after its start** — up to a few minutes, see [Backend start-up time](kubernetes.md#backend-start-up-time). The autoscaler therefore does not absorb short load peaks.
- **Celery worker:** CPU is the wrong signal for the worker — it mostly waits for external services. An autoscaler on queue length needs the worker metrics, which are still missing. Until then set more worker pods with a fixed `replicas`.

The chart refuses to render (`helm template`, `helm upgrade`, ArgoCD) with a message when a setting would go wrong silently in the cluster:

| Setting | Why refused |
|---------|-------------|
| Backend or Celery worker with more than one pod (`replicas` or `maxReplicas`) on the default `ReadWriteOnce` volume | A second pod on another node never starts (`Multi-Attach error`). Fix: [S3](#storage-configuration-nfr-013) or `ReadWriteMany`. |
| More than one pod or an autoscaler for `celery-beat`, `arangodb`, `vectordb` or `timescaledb` | Two beat pods run every scheduled task twice, deletion and retention runs included. Two ArangoDB, VectorDB or TimescaleDB pods are two separate databases, not a cluster. |
| `podDisruptionBudget.minAvailable` equal to or above the pod count, also as a percentage (`"100%"`; Kubernetes rounds up to whole pods, `"50%"` of one pod is that pod), or `maxUnavailable: 0` or `"0%"` | Kubernetes may then evict no pod; every node drain and every cluster upgrade hangs. Percentages that still let at least one pod be evicted (`minAvailable: "50%"` with two pods, `maxUnavailable: "25%"`) are allowed. |

Celery beat always stays a single pod with the `Recreate` strategy: the old pod ends before the new one starts.

## Secrets from a secret store {#secrets-from-a-secret-store}

Instead of creating `kamerplanter-secrets` by hand, the [External Secrets Operator](https://external-secrets.io/) can write it from your secret store (Vault, AWS Secrets Manager, …). The chart ships an `ExternalSecret` for this, off by default:

```yaml title="values-production.yaml (excerpt)"
externalSecrets:
  app:
    enabled: true
    secretStoreRef:
      kind: ClusterSecretStore     # or a SecretStore in the same namespace
      name: my-secret-store
    dataFrom:
      - extract:
          key: kamerplanter/app    # store entry with the mandatory keys, without ARANGO_ROOT_PASSWORD
```

- Every key of the store entry becomes an entry of `kamerplanter-secrets`, and backend, worker and beat read that Secret in full through `envFrom`. So put only the mandatory keys into the entry ([mandatory secrets](kubernetes.md#2-create-the-mandatory-secrets)), **not** `ARANGO_ROOT_PASSWORD`: the root password belongs in a Secret of its own (its own store entry with a second `ExternalSecret`, or created by hand) that you name in `database.arangodb.rootPasswordSecret`.
- A `ClusterSecretStore` without restriction serves every namespace in the cluster. Restrict it to the Kamerplanter namespace through `spec.conditions` (`namespaces` or `namespaceSelector`), or use a `SecretStore` in the same namespace (`secretStoreRef.kind: SecretStore`).
- Without `secretStoreRef.name` the render stops with a message.
- The operator and its CRDs (`external-secrets.io/v1`) must be installed in the cluster.
- If the entry later disappears from the store, the last Secret is kept (`deletionPolicy: Retain`) — pods keep starting.
- `Retain` only covers a deleted store entry. On `helm uninstall` the `ExternalSecret` goes away, and because with `creationPolicy: Owner` it owns `kamerplanter-secrets`, Kubernetes garbage collection deletes the Secret with it. If you still need the values afterward, they are in the store.

!!! warning "Moving from a hand-made Secret"
    With `creationPolicy: Owner` (the default) the operator does not simply adopt an existing, hand-made `kamerplanter-secrets`. Delete the old Secret in the same step (running pods keep their values until their next restart), or set `externalSecrets.app.target.creationPolicy: Merge` — the operator then writes the keys into the existing Secret.

Further Secrets — the S3 credentials (`storage.s3.credentialsRef`), the backup (`backup.s3.credentialsRef`) and the database root password (`database.arangodb.rootPasswordSecret`) — are added the same way as further entries under `externalSecrets`.

## TimescaleDB (sensor data) {#timescaledb}

TimescaleDB stores sensor time series. It is optional and off by default; without it Kamerplanter runs without a time-series store. You switch it on with a single value:

```yaml title="values-production.yaml (excerpt)"
controllers:
  timescaledb:
    enabled: true
```

The chart then renders the database (StatefulSet, one pod, 10 GiB volume), its Service and its NetworkPolicy, and backend, worker and beat receive `TIMESCALEDB_ENABLED=true` together with the address. Only backend and worker may reach the database on port 5432.

Before that, add the key `TIMESCALEDB_PASSWORD` to `kamerplanter-secrets`:

```bash
kubectl patch secret kamerplanter-secrets -n kamerplanter --type merge \
  -p "{\"stringData\":{\"TIMESCALEDB_PASSWORD\":\"$(openssl rand -hex 24)\"}}"
```

- The database reads only this one key from the Secret; backend and worker receive it like every other key through `envFrom`.
- Without the key the database pod does not start (`CreateContainerConfigError`). The backend refuses to start on the built-in default password as soon as `DEBUG=false`.
- With `externalSecrets.app` you put the key into the same store entry as the other mandatory keys.
- The database runs without root privileges (user `postgres`, uid 70) on a read-only file system; only the data volume, the socket directory and `/tmp` are writable.
- More than one pod is not possible: a second pod would be a second, separate database. The chart refuses `replicas` above 1 and an autoscaler.
- The volume survives `helm uninstall`. The chart does not back up the time series (see [Backup and restore](backup-restore.md)).

## External databases {#external-databases}

Instead of the bundled ArangoDB and the Valkey subchart you can connect databases outside the chart, such as a managed service or an instance in another namespace. Both switches are off by default; without them the chart renders as before.

### ArangoDB

`database.arangodb.external.enabled: true` is the only switch. The ArangoDB StatefulSet, its service, its NetworkPolicy and its volumes are not rendered. Backend, Celery worker, Celery beat and the backup connect to `scheme://host:port`:

```yaml
database:
  arangodb:
    appUsername: kamerplanter
    external:
      enabled: true
      host: arango.example.net    # host name only, no scheme
      port: 8529
      scheme: https               # http | https
      cidr: 203.0.113.10/32       # address range of the database (NetworkPolicy)
```

- The chart creates nothing in an external database. The application database (`kamerplanter`) and the account from `appUsername` with read/write access to it must exist; `ARANGODB_PASSWORD` in `kamerplanter-secrets` is its password.
- `scheme: https` sets `ARANGODB_SCHEME=https`. The backend verifies the server certificate against the certificates in the image. For a private certificate authority, put its certificate into the container and name the path in `REQUESTS_CA_BUNDLE`. This covers the application only: the backup job's `arangodump` does not read that variable, so with a private certificate authority the backup is not covered by this chart.
- The backup (`backup.enabled`) then dumps the external database and connects over TLS with `https`.

### Valkey

`valkey.enabled: false` switches the Valkey subchart off. Backend, worker and beat then get `database.valkey.external.url` as `REDIS_URL`:

```yaml
valkey:
  enabled: false
database:
  valkey:
    external:
      url: "rediss://:$(VALKEY_PASSWORD)@valkey.example.net:6380/0"
      cidr: 203.0.113.20/32
```

- `redis://` and `rediss://` (TLS) are allowed.
- A password never goes into the values. Store it as a key in `kamerplanter-secrets` (here `VALKEY_PASSWORD`) and reference it as `$(KEY)`; Kubernetes inserts the value when the container starts. Percent-encode the characters `/ # ? @` in the password, otherwise the backend refuses to start.

### NetworkPolicies

Under the default-deny baseline the pods reach an external database only through an egress policy of its own. The chart renders it with the matching switch:

| Policy | Pods | Target | Ports |
|---|---|---|---|
| `arangodb-external` | backend, every Celery worker, backup | `database.arangodb.external.cidr` | 8529, 443 |
| `valkey-external` | backend, every Celery worker, Celery beat | `database.valkey.external.cidr` | 6379, 6380 |

- `cidr` is therefore required. If you reach the database through a namespace or pod selector, replace `networkpolicies.<policy>.rules.egress` with your rule, or switch the policy off with `enabled: false` and bring your own.
- If the database listens on another port, replace `rules.egress` as well. Ports in a NetworkPolicy must be numbers; a template would produce a string, which Kubernetes reads as a port name.

### Render checks

The chart refuses to render a combination that would fail silently in the cluster:

- an external ArangoDB without `host`, with a scheme inside `host`, with a scheme other than `http`/`https`, or together with `controllers.arangodb.enabled: true`
- `valkey.enabled: false` without `url` or with a URL that does not start with `redis://` or `rediss://`, and a `url` set while the Valkey subchart runs
- an egress policy without `cidr` or without the port you configured

## See also

- [Kubernetes Deployment](kubernetes.md) — Step-by-step guide
- [Environment Variables](../reference/environment-variables.md) — Full reference of all environment variables
- [Configure Storage (Object Storage)](../user-guide/object-storage.md) — Admin UI and migration
