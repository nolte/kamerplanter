# Restore drill — ArangoDB backup CronJob (#2122)

- **Date:** 2026-10-04
- **Branch:** `fix/2026-10-04-helm-readiness` (chart at the commit introducing `backup.*`)
- **Scope:** the chart's `arangodb-backup` CronJob scripts, exactly as rendered, against
  real ArangoDB 3.12.12 and an S3 endpoint; restore into an empty server following
  `docs/de/deployment/backup-restore.md` steps 3–5.
- **Not covered:** a Kubernetes scheduler run (CronJob controller, NetworkPolicy
  enforcement) — the drill runs the rendered containers in Docker with the same
  images, user, read-only root and capabilities; attachments (not part of this
  backup, see the runbook).

## Setup

| Part | How |
|---|---|
| Rendered manifests | `helm template kamerplanter helm/kamerplanter --set backup.enabled=true --set backup.s3.bucket=drill --set backup.s3.provider=Other --set backup.s3.endpointUrl=http://s3:8080 --set backup.s3.forcePathStyle=true --set backup.s3.serverSideEncryption=` |
| Scripts | `dump` = `initContainers[dump].args[0]`, `upload` = `containers[main].args[0]`, extracted from the render with `yq`; upload env from the rendered `env` list |
| Source database | `arangodb:3.12.12`, database seeded by the application's own startup (`ensure_collections`, migrations, seeds), plus one marker document `sites/drillmarker` written after seeding |
| S3 | `rclone serve s3` (rclone 1.71.2), bucket `drill` |
| Containers | `--read-only --tmpfs /tmp --user 1000:1000 --cap-drop ALL --security-opt no-new-privileges`, as the pod's security context |
| Target database | a second, empty `arangodb:3.12.12` |

## Backup

| Step | Result |
|---|---|
| Run 1: dump | exit 0 — 309 collections, 3.2 MB, 225.6 KB compressed |
| Run 1: upload | exit 0 — `backup 20261004T205040Z uploaded`; a pre-seeded `20200101T000000Z/` was purged (`expired (older than 30 days)`), a non-stamp directory `manual-keep/` was left alone |
| Run 2 (after the marker write): dump + upload | exit 0 — `backup 20261004T205151Z uploaded`; `LATEST` = `20261004T205151Z`; run 1's dump kept (younger than 30 days) |
| Password on a command line | none: `--server.password @ARANGODB_PASSWORD@` is expanded by arangodump from its environment |

## Restore (runbook steps 3–5)

1. Fresh install simulated: the application booted once against the empty target
   (creates and seeds its collections) — exit 0.
2. `LATEST` read from S3 (`20261004T205151Z`), the directory copied down with
   `rclone copy` (620 files, 2.8 MB) and into the container (`docker cp`, the
   `kubectl cp` equivalent).
3. `arangorestore --server.password @ARANGO_ROOT_PASSWORD@ --create-database true
   --include-system-collections true --overwrite true` inside the target container —
   exit 0, 309 collections restored.
4. Application booted again against the restored database — exit 0, 0 migrations
   applied (same version), marker document present.

## Comparison source ↔ target

| Measure | Source | Target |
|---|---|---|
| Collections | 309 | 309 |
| Documents (sum) | 8691 | 8691 |
| Collections whose count **or** index set differs | — | none |
| Named graphs | `kamerplanter_graph` | `kamerplanter_graph` |
| Marker `sites/drillmarker` | present | present |

**Verdict:** restore into an empty server works as documented; the recovery point is
readable from `LATEST` without cluster access (RPO = now − LATEST).

## Addendum — application account (#2126)

After #2126 the backup dumps with the application account (`kamerplanter`, `rw` on
the application database only), not root. Re-run against a fresh ArangoDB 3.12.12
pod simulation (server + the chart's rendered `app-user` script in a second
container sharing the network namespace, read-only root, uid 999, all
capabilities dropped):

| Step | Result |
|---|---|
| `app-user` while the server initialises | first attempt failed (`not connected`), retried after 15 s, then `created database kamerplanter` / `kamerplanter has rw on kamerplanter and no access to _system` |
| Account scope | `/_api/database/current`: 200 on `kamerplanter`, 401 ERR 11 on `_system` and on another database |
| Application boot under the account (connect, `ensure_collections`, migrations, seeds) | exit 0, 38.5 s including import, 309 collections |
| Rendered `dump` script with the account (`--include-system-collections true`) | exit 0, 309 collections, 3.2 MB |
| Upload with the scratch clean-up (`trap 'rm -rf /backup/*' EXIT`) | exit 0, `backup … uploaded`, `LATEST` written, 0 entries left in the scratch volume |
