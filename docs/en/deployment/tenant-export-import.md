# Exporting and importing a tenant (runbook)

A tenant export saves **one** garden (tenant) as an archive without touching the whole database. An import brings such an archive back as a **new** tenant — into the same or into another Kamerplanter installation. Use it to restore a single garden, to move it from a shared to its own installation, or to save it before its final deletion.

This page is for operators and platform admins. Backing up the whole installation is covered in [Backup & Restore](backup-restore.md).

!!! warning "Not yet implemented"
    A user interface for this will be available in the garden settings and the admin area; until then you use the API (internal reference: REQ-056 §15). Sensor readings from TimescaleDB are not carried yet, and the target plan's quotas are not checked before an import yet. <!-- REQ-056 / Issue #2138 -->

---

## What the archive holds — and what it does not

The archive is a ZIP file in the format `kamerplanter-tenant-export/1`. It holds everything deleting the tenant would remove — minus a fixed list of exclusions, which the archive itself names with their reasons (`manifest.json`, field `excluded`).

| Part | Content |
|---|---|
| `manifest.json` | format, the source's migration level, creation time, a random source id, row count and SHA-256 checksum per file, the list of exclusions |
| `tenant.json` | the garden's name, short name, description and settings |
| `collections/<name>.jsonl` | every record of the garden: sites, plants, runs, diary, tasks, tanks, sensors, harvest and treatment records, own species, cultivars, fertilizers, substrates and the rest |
| `edges/<name>.jsonl` | the links between these records and to global catalogue entries (species, families, pests …) |
| `members.jsonl` | per member: internal account id, display name, role, additional permissions, join date — **no** e-mail address |
| `objects/…` | the originals of the photos and attachments; previews are rendered again on first view after the import |

**Not** in the archive: accounts and credentials, sessions, API keys, invitations, encrypted integration credentials (AI providers, InvenTree), the Home Assistant entity grants, the security log and the other audit logs, notifications, iCal subscriptions, AI conversations and caches, plot assignments, export requests and recognition vectors.

!!! info "The archive contains personal data"
    Site coordinates, diary texts and the members' photos are part of it. Store the archive accordingly and delete it as soon as you no longer need it. Inside Kamerplanter it can be downloaded for 72 hours (`RETENTION_EXPORT_FILE_RETENTION_HOURS`); after that the installation deletes it.

---

## Exporting a garden

### Who may export

- A member with the **lead** role and the **management** permission, while the garden is active or scheduled for deletion.
- A **platform admin** in every state but deleted — also for a suspended or orphaned garden.

Both confirm with their own password (or, without a local password, with a fresh sign-in or an e-mail code). An API key or a service account can neither export nor list or download an archive. At most one export runs per garden at a time, and at most `TENANT_EXPORTS_PER_DAY` exports (default `3`) can be requested within 24 hours — failed ones count. With every export, all members with the management permission get an e-mail, and the security log records `tenant_export_requested`.

### Steps

1. Request the export:

    ```bash
    curl -X POST https://<your-instance>/api/v1/tenants/<slug>/exports \
      -H "Authorization: Bearer <access-token>" \
      -H "Content-Type: application/json" \
      -d '{"current_password": "<your password>"}'
    ```

    As a platform admin: `POST /api/v1/admin/platform/tenants/<tenant-key>/exports`. The answer is `202` with the export's key (`key`) and `status: pending`.

2. Wait until `status` is `completed`:

    ```bash
    curl https://<your-instance>/api/v1/tenants/<slug>/exports \
      -H "Authorization: Bearer <access-token>"
    ```

    The export runs in the background on the `bulk` queue. For large gardens this takes a few minutes. `failed` with `failure_reason: too_large` means the archive would be larger than the garden's storage quota plus 10 %.

3. Download the archive (only the person who requested the export):

    ```bash
    curl -o garden.zip https://<your-instance>/api/v1/tenants/<slug>/exports/<export-key>/download \
      -H "Authorization: Bearer <access-token>"
    ```

    The security log records every download (`tenant_export_downloaded`).

### Signature

Your installation signs every archive it writes (`manifest.json`, field `signature`). On import into the **same** installation the import reports `verified: true`: the archive is exactly the one written here. An archive from another installation, an unsigned one or one changed after export is imported with `verified: false` — its content is then only as trustworthy as the person who handed it to you. The signature key is derived from `JWT_SECRET_KEY`; if you rotate it, older archives read as unverified.

!!! warning "Not in the archive"
    The keys of integrations (for example the OpenWeatherMap key of a weather source) are removed from the archive. Set them up again in the target installation.

---

## Importing an archive (platform admin)

An import **always creates a new garden**. It never merges into an existing one, and every record gets a new internal id — so an archive cannot overwrite a record of another garden.

### Preparation

- **Map the members:** the archive knows the members only by their old internal id (`user_key` in `members.jsonl`). For every member who should be part of the new garden, you name the e-mail address of an **existing** account in the target installation (it must be **active** — the import refuses a deactivated account) **and the role and permissions** that person gets. The roles recorded in the archive are only a hint; the import takes yours. Unmapped members are dropped; entries they wrote then carry the pseudonym `_anonymized`.
- **Owner:** the new garden belongs to the longest-serving mapped member you gave lead and management — with exactly the permissions you give them (give only `management` and they do not also get `technical`). If there is none, it belongs to you with both permissions until you hand it over; this way every imported garden has someone who can manage it. In both cases the security log names you as the one who created every membership.
- **Catalogue:** the target installation needs every global catalogue entry the archive points at (species, families, pests …). If one is missing, the import refuses with the list and writes nothing.

### Steps

```bash
curl -X POST https://<your-instance>/api/v1/admin/platform/tenant-imports \
  -H "Authorization: Bearer <access-token>" \
  -F "archive=@garden.zip" \
  -F 'member_mapping={"<old user_key>": {"email": "anna@example.com", "role": "lead", "admin_scopes": ["management"]}}' \
  -F "current_password=<your password>"
```

Optionally `-F "plan_key=<plan>"` picks the new garden's plan; otherwise it gets the default plan. Your confirmation is bound to this file: if you confirm with a fresh sign-in token instead of the password, request it for the target `archive:<the first 32 hex digits of the file's SHA-256>` (`sha256sum garden.zip | cut -c1-32`). The answer is `202` with the import's key and `verified` (see [Signature](#signature)).

While the import writes, the new garden has the state **importing**: nobody can open it yet, and the memberships only become active at the end. Read its state and, at the end, the report (counts per kind of record, no contents) like this:

```bash
curl https://<your-instance>/api/v1/admin/platform/tenant-imports/<import-key> \
  -H "Authorization: Bearer <access-token>"
```

Like the import itself, you read its state only signed in as a person, not with an API key (`403`).

`completed` names the new garden in `target_tenant_key`. The security log records `tenant_import_requested` and `tenant_imported` as well as every membership created. A refused or failed import is in it too, as `tenant_import_requested` with its outcome (`refused:<code>`, `failed:<code>`, `cleanup_pending:<code>`) and the archive's SHA-256, so you can trace who tried which archive.

### When the import refuses

| Answer | Meaning | What you do |
|---|---|---|
| `422 IMPORT_FORMAT_UNSUPPORTED` | no ZIP file, an unknown format, too many or too large files, an archive that would unpack too large (a file compressed more than 100-fold, more than 250,000 records in one file or 1,000,000 in all, more than 128 MiB of records or 1 GiB in all), a record that does not belong to the archived garden, a file of a type this installation does not accept (SVG for example), or the archive comes from a newer installation | use an archive Kamerplanter wrote; update the target installation |
| `422 IMPORT_CHECKSUM_MISMATCH` | a file in the archive does not match the checksum in `manifest.json` or is missing — the archive is damaged | use an undamaged copy |
| `422 IMPORT_UNDECLARED_REFERENCE` | the archive holds a reference field this installation does not know | bring both installations to the same version |
| `422 IMPORT_MISSING_CATALOG_ENTRIES` | catalogue entries are missing; `details` lists them | complete the target's catalogue (check the seed level) |
| `422 IMPORT_MEMBER_NOT_FOUND` | a mapping names no member of the archive or no existing, active account | correct the mapping |
| `413` | larger than `TENANT_IMPORT_MAX_UPLOAD_MB` — or than the general upload limit (see below) | raise the limit or reduce the garden |

If the import fails only while writing, it removes everything it created so far and reports `failed`. If that removal does not fully succeed (the database is unreachable for a moment, for example), it reports `cleanup_pending`: the half garden stays in the state **importing** and so unreachable, `target_tenant_key` names it, and the next hourly retention job deletes it through the regular garden deletion; the import then reads `failed`. If its run dies (a worker restart, for example), the hourly retention job deletes the half garden through the regular garden deletion after six hours without progress and reports `failed` with `IMPORT_ABANDONED`. No half garden is left behind; only the log entries of the memberships it created stay as proof.

!!! info "The checksums are no proof of origin"
    The checksums in `manifest.json` only reveal a damaged archive: whoever changes a file can recompute them. Whether an archive comes unchanged from your installation is told only by `verified`.

!!! warning "Restoring beside the original that still exists"
    If you import an archive into the **same** installation while the original garden still exists, the import fails on own species with the same scientific name (the database allows each name once) and is rolled back completely. For a single-garden restore the original is usually lost anyway; otherwise delete it first or import into another installation.

---

## Settings

| Variable | Default | Effect |
|---|---|---|
| `TENANT_EXPORTS_PER_DAY` | `3` | exports per garden in 24 hours |
| `TENANT_IMPORT_MAX_UPLOAD_MB` | `512` | largest archive an import accepts; whatever it is set to, an archive may unpack to at most 1 GiB |
| `RATE_LIMIT_TENANT_IMPORT` | `10/hour` | import requests per account |
| `RETENTION_EXPORT_FILE_RETENTION_HOURS` | `72` | how long an archive stays downloadable (also applies to the personal data export) |

!!! warning "The general upload limit applies to the import too"
    Every upload to the backend is limited to `STORAGE_MAX_FILE_SIZE_MB` plus 1 MiB (default: 26 MiB) — in front of every route, the import included. The backend refuses a larger archive with `413` even when `TENANT_IMPORT_MAX_UPLOAD_MB` is higher. For larger archives, raise `STORAGE_MAX_FILE_SIZE_MB`, `UPLOAD_SPOOL_BUDGET_MB` and your ingress's upload limit together — which then applies to every upload.

!!! info "Signing key"
    The archive signature is derived from `JWT_SECRET_KEY`. If you rotate that secret, older archives import as unverified (`verified: false`); they can still be imported.

---

## See also

- [Backup & Restore](backup-restore.md)
- [Platform administration](../user-guide/admin.md)
- [Environment variables](../reference/environment-variables.md)
