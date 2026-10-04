# Backup & Restore (Kubernetes)

The Helm chart ships a backup of the ArangoDB database: a CronJob that dumps the application database with `arangodump` and uploads the dump to an S3 bucket. This page shows you how to switch the backup on, how to check the latest recovery point and how to restore a backup into an empty namespace.

For Docker Compose see [Docker Compose permanent operation](docker-dauerbetrieb.md).

---

## What is backed up — and what is not

| Data | Backed up by | Note |
|---|---|---|
| ArangoDB (all domain data, accounts, tenants) | CronJob `kamerplanter-arangodb-backup` | Dump of the application database including the graph definition and indexes |
| Attachments (photos, exports) with `storage.backend: s3` | Bucket versioning or replication | Configure on the bucket, not in the chart |
| Attachments with `storage.backend: local-fs` | **not** by the chart | VolumeSnapshot of the `backend-attachments` PVC through your CSI driver |
| `kamerplanter-secrets` | **not** by the chart | Back it up separately, e.g. in the secret store of the External Secrets Operator |
| TimescaleDB | **not** by the chart | Not part of the chart's production values |
| Valkey | not needed | Cache and task queue, no domain data |

!!! danger "Without the old secrets a restore is incomplete"
    Some fields in the database are encrypted with `FERNET_KEY` (for example stored credentials for Home Assistant or weather services), and erasure records depend on `ERASURE_TOMBSTONE_SALT`. If you restore a dump with newly generated values, those fields can no longer be read. Back up `kamerplanter-secrets` together with the dumps and provide the same values when you restore.

---

## Switch the backup on

### 1. Prepare the bucket and the credentials

Create a bucket (versioning and default encryption on the bucket are recommended) and an access key that may only read, write, list and delete in that bucket. The chart does not create the bucket.

```bash
kubectl create secret generic kamerplanter-backup-s3 \
  --namespace kamerplanter \
  --from-literal=AWS_ACCESS_KEY_ID="your-access-key" \
  --from-literal=AWS_SECRET_ACCESS_KEY="your-secret-key"
```

For GitOps, create the Secret with the External Secrets Operator instead (see [ArgoCD](argocd.md)).

### 2. Set the values

```yaml title="values-production.yaml"
backup:
  enabled: true
  schedule: "15 2 * * *"        # daily at 02:15 (cluster time zone)
  retentionDays: 30             # older dumps are deleted, the newest never
  scratchSize: 10Gi             # room for one dump on the node disk
  s3:
    provider: AWS               # rclone provider name: AWS, Minio, Ceph, Cloudflare, Other
    endpointUrl: https://s3.eu-central-1.amazonaws.com
    region: eu-central-1
    bucket: my-kamerplanter-backup
    prefix: kamerplanter/arangodb
    serverSideEncryption: AES256   # or aws:kms with kmsKeyId, or "" for providers without SSE
    credentialsRef:
      secretName: kamerplanter-backup-s3
```

Without `backup.s3.bucket` the render aborts with a message — an enabled backup without a target would silently fail every night.

How a run works:

1. The init container `dump` (the same ArangoDB image as the database) dumps the application database with the application's account to `/backup/<timestamp>/`.
2. The `main` container (rclone) uploads the dump to `s3://<bucket>/<prefix>/<timestamp>/` and writes the timestamp to `<prefix>/LATEST`. It then deletes the dump from the pod's scratch volume — also when the upload fails — so no copy of the data stays behind on the node.
3. It then deletes dump directories older than `retentionDays` — never the one it just wrote. If the backup fails for a longer period, the last good dump is therefore kept.

No password appears on a command line; `arangodump` reads it from its own environment. The pods run without root privileges on a read-only file system with their own NetworkPolicy (ArangoDB, DNS and port 443 outbound).

!!! warning "S3 inside the cluster or on a private network"
    Like the backend's, the backup pod's NetworkPolicy excludes the private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) and `169.254.0.0/16`. A MinIO or Ceph RGW inside the cluster is only reachable with an additional egress rule in `networkpolicies.arangodb-backup.rules.egress`.

### 3. Trigger a run right away

```bash
kubectl create job --namespace kamerplanter \
  --from=cronjob/kamerplanter-arangodb-backup kamerplanter-arangodb-backup-manual
kubectl logs --namespace kamerplanter job/kamerplanter-arangodb-backup-manual -c main
```

Expected last line: `backup <timestamp> uploaded`.

---

## Check the recovery point (RPO)

The timestamp in `<prefix>/LATEST` is the recovery point. Its distance to the current time is your actual RPO:

```bash
# With a locally configured rclone remote "backup"
rclone cat backup:my-kamerplanter-backup/kamerplanter/arangodb/LATEST

# Or in the cluster
kubectl get cronjob --namespace kamerplanter kamerplanter-arangodb-backup \
  -o jsonpath='{.status.lastSuccessfulTime}'
```

With a daily schedule the RPO is at most 24 hours plus the run time. For a shorter RPO set `backup.schedule` accordingly (for example `"15 * * * *"` for hourly).

---

## Restore into an empty namespace

These steps restore a backup into a fresh installation. They were run through on 2026-10-04 (dump, upload, download, `arangorestore`, application restart; all 309 collections with identical document counts and identical indexes).
<!-- #2122; protocol: test-reports/backup-restore/2026-10-04-arangodb-restore-drill.md -->

!!! warning "ArgoCD: pause automatic sync"
    If ArgoCD manages the namespace, pause the Application's automatic sync (and `selfHeal`) during the restore. Otherwise ArgoCD scales the deployments from step 2 straight back up.

### 1. Install the chart

Create `kamerplanter-secrets` with **the same values** as in the backed-up installation and install the chart as described in [Kubernetes deployment](kubernetes.md). Wait until `kamerplanter-arangodb-0` is ready.

### 2. Stop the application

```bash
kubectl scale deployment --namespace kamerplanter \
  kamerplanter-backend kamerplanter-celery-worker kamerplanter-celery-beat --replicas=0
```

### 3. Fetch the dump

On your workstation, with an rclone remote `backup` pointing at the same bucket:

```bash
STAMP="$(rclone cat backup:my-kamerplanter-backup/kamerplanter/arangodb/LATEST)"
rclone copy "backup:my-kamerplanter-backup/kamerplanter/arangodb/${STAMP}" "./restore/${STAMP}"
kubectl cp --namespace kamerplanter "./restore/${STAMP}" kamerplanter-arangodb-0:/tmp/restore -c main
```

For an older state replace `STAMP` with one of the directory names under `<prefix>/`.

### 4. Restore

`arangorestore` runs in the ArangoDB container, which already has the root password in its environment; `@ARANGO_ROOT_PASSWORD@` reads it from there without putting it on the command line:

```bash
kubectl exec --namespace kamerplanter kamerplanter-arangodb-0 -c main -- \
  arangorestore \
    --server.endpoint tcp://127.0.0.1:8529 \
    --server.username root \
    --server.password @ARANGO_ROOT_PASSWORD@ \
    --server.database kamerplanter \
    --create-database true \
    --include-system-collections true \
    --overwrite true \
    --input-directory /tmp/restore

kubectl exec --namespace kamerplanter kamerplanter-arangodb-0 -c main -- rm -rf /tmp/restore
```

`--overwrite true` replaces the collections the fresh installation created on its first start.

### 5. Start the application

```bash
kubectl scale deployment --namespace kamerplanter kamerplanter-backend --replicas=1
kubectl scale deployment --namespace kamerplanter kamerplanter-celery-worker kamerplanter-celery-beat --replicas=1
```

On start the backend checks the migration state; a dump from the same version applies no migration, an older dump is migrated to the current state. Then switch automatic sync in ArgoCD back on.

---

## Practise the restore

Run the restore regularly (for example quarterly) into a test namespace and compare the document count per collection between source and target. A backup whose restore was never practised is not a reliable backup.

## See also

- [Helm charts — storage configuration](helm.md#storage-configuration-nfr-013)
- [Kubernetes deployment](kubernetes.md)
- [ArgoCD](argocd.md)
