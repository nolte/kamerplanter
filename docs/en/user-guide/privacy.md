# Privacy & GDPR

!!! note "Partially available"
    The GDPR data subject rights are fully implemented and production-ready as an **API self-service under `/api/v1/privacy/`**. The **graphical interface** is now available as well — reachable from the user menu (click your profile picture or initials) > **Privacy**, in Full mode only (not in anonymous [Light mode](light-mode.md)). It covers the main flows: requesting a data export, deleting your account, creating a processing restriction, and viewing consents. A few sub-steps (e.g. revoking consent with a click, changing your email address) are currently only possible via the API — flagged at the relevant spot on this page (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)). <!-- REQ-025 -->

Kamerplanter is built on the principle of **Privacy by Design**. You have full control over your personal data: you can export, correct or have it deleted at any time. All data subject rights under GDPR Art. 15–21 are available as self-service features.

---

## For Technical Users / Self-Hosters

This section is aimed at technical users and self-hosters. All GDPR features described below are available as REST endpoints under `/api/v1/privacy/`. Some of them are also directly usable in the graphical interface (see the relevant sections below); a few endpoints — email change, objection, granting/revoking consent with a click, lifting a restriction, export status/download — are currently reachable only via the API. A logged-in session (bearer token) is required, except for `GET /api/v1/privacy/policy`.

!!! info "API only / operator configuration"
    The easiest way to try the endpoints is through the interactive API documentation at `/docs` (OpenAPI/Swagger), where requests can be executed directly in the browser. Alternatively via `curl`, e.g. for a data export:
    ```bash
    curl -X POST https://<your-instance>/api/v1/privacy/export \
      -H "Authorization: Bearer <your-access-token>"
    ```

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/privacy/export` | Request a data export (Art. 15/20) |
| `GET /api/v1/privacy/export/{export_key}` | Check export status |
| `GET /api/v1/privacy/export/{export_key}/download` | Download the export |
| `POST /api/v1/privacy/email-change` | Request an email change (Art. 16) |
| `POST /api/v1/privacy/email-change/confirm` | Confirm an email change via token |
| `POST /api/v1/privacy/erasure` | Request account erasure (Art. 17) |
| `GET /api/v1/privacy/erasure/{erasure_key}` | Check erasure status |
| `POST /api/v1/privacy/restrict` | Restrict processing (Art. 18) |
| `DELETE /api/v1/privacy/restrict/{restriction_key}` | Lift a restriction |
| `POST /api/v1/privacy/object` | File an objection (Art. 21) |
| `GET /api/v1/privacy/consents` | List consents (Art. 7) |
| `POST /api/v1/privacy/consents` | Grant consent |
| `DELETE /api/v1/privacy/consents/{purpose}` | Revoke consent |
| `GET /api/v1/privacy/policy` | Retrieve the privacy policy (no login needed) |

---

## Opening Privacy Settings

Here's how to open the privacy area:

1. Click your profile picture or initials in the top right
2. Click **Privacy** in the menu

The privacy area has four tabs: **Consents**, **Data Export**, **Delete Account** and **Restrict Processing**.

!!! note "Full mode only"
    The **Privacy** menu item only appears in **Full mode** with a registered account. In anonymous [Light mode](light-mode.md) there is no user account, and therefore no privacy area.

---

## Exporting Your Data (GDPR Art. 15 & 20)

You have the right to know what data the system has stored about you and to receive it in a machine-readable format.

### Requesting a Data Export

1. Navigate to **Privacy** > the **Data Export** tab
2. Click **Request Export**
3. The interface confirms the request with its current status

The export then runs asynchronously in the background (takes 1–5 minutes depending on data volume); the resulting download link is valid for **72 hours**.

!!! info "API only: Checking status & downloading the file"
    Checking the progress of a running export request and downloading the finished file is not yet wired up in the interface — for now this only works via the API: `GET /api/v1/privacy/export/{export_key}` returns the status, `GET /api/v1/privacy/export/{export_key}/download` returns the download metadata (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

The export contains all data the system knows about you:
- Profile data (name, email, settings)
- All created plants, locations, tasks and harvests
- Care reminders and confirmation history
- Sensor data (if you have any)
- Consent history

!!! tip "Data portability"
    The JSON export file complies with GDPR Art. 20 (data portability). You can use it to transfer your data to another system.

---

## Changing Your Email Address (GDPR Art. 16)

You have the right to have your data corrected.

!!! info "API only: Changing your email address"
    Account settings currently show your email address as read-only — changing it is, for now, only possible via the API: `POST /api/v1/privacy/email-change` initiates the change and sends a **verification link to the new address**, `POST /api/v1/privacy/email-change/confirm` confirms it via token (no login needed). Details in [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).

The new email becomes active once confirmed — all active sessions are ended.

!!! note "Security notice"
    After confirming the new email, all open sessions (browser, app) are terminated. You need to log in again. Your old email receives an information email about the change.

---

## Restricting Processing (GDPR Art. 18)

You can restrict the processing of your data for certain purposes — for example if you dispute the accuracy of your data or consider the processing unlawful.

1. Navigate to **Privacy** > the **Restrict Processing** tab
2. Enter the affected data scope (e.g. `sensor_data`, `harvest_records`, `treatment_records`) and choose a reason
3. Click **Restrict**

The created restriction then appears in the **Active Restrictions** list on the same tab. During a restriction the affected data is no longer actively processed.

!!! info "API only: Lifting a restriction"
    Lifting an existing restriction is not yet wired up in the interface — for now this only works via the API: `DELETE /api/v1/privacy/restrict/{restriction_key}` (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

---

## Managing Consents (GDPR Art. 7)

No optional consent is needed for the core functions of the system. However, some additional features require your agreement.

### Types of Consent

| Purpose | Type | Revocable |
|---------|------|:---------:|
| **Core functions** (plant management, reminders) | Required | No |
| **Error tracking (Sentry)** | Optional | Yes |
| **HaveIBeenPwned password check** | Optional | Yes |
| **External master data enrichment** (GBIF, Perenual) | Optional | Yes |
| **Photo identification** (Pl@ntNet) | Optional | Yes |
| **Cloud-based pest detection** (Kindwise plant.health) | Optional | Yes |
| **Photo contribution to plant recognition** (own reference photos) | Optional | Yes |

### Revoking Consent

The **Consents** tab in the privacy area shows an overview of all processing purposes with your current status (**Granted** / **Not granted**) and, for required consents, a **Required** label.

!!! info "API only: Granting and revoking consent with a click"
    The tab is currently **read-only** — there is no toggle in the interface yet to directly grant or revoke a consent. Until then, this only works via the API: `POST /api/v1/privacy/consents` grants a consent, `DELETE /api/v1/privacy/consents/{purpose}` revokes it, taking effect immediately with a timestamp. `GET /api/v1/privacy/consents` returns the same data the tab displays (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

!!! warning "Effects of revoking consent"
    If you revoke consent for external master data enrichment, no new data will be fetched from GBIF or Perenual. Existing enriched data is retained.

### Photo Identification (plant_identification)

[Plant recognition by photo](plant-identification.md) sends your image to Pl@ntNet (CIRAD/INRIA, France/EU) for analysis. Consent is required because the photo briefly leaves the Kamerplanter instance.

!!! note "Consent behaviour per deployment mode"
    **Full mode:** Consent is stored as a consent record in the backend (see table below) and persists across browsers and devices. The Consents tab in the privacy interface shows the current status; revoking it currently only works via the API: `DELETE /api/v1/privacy/consents/plant_identification` (see [Revoking Consent](#revoking-consent)).

    **Light mode:** The consent subsystem is not available in [Light mode](light-mode.md). Consent is instead obtained and stored **client-side in the browser** (localStorage). The consent dialog appears on the first upload in the respective browser session. The same transparency information (photo is sent to Pl@ntNet/France, EXIF data is removed, no permanent storage) is shown in both modes.

**What happens when you revoke:**

- All camera buttons are immediately hidden
- New photo requests are rejected with HTTP 403 (Full mode) or blocked in the browser (Light mode)
- Your identification history is retained (it contains no photos, only results)
- You can grant consent again at any time

**Data flow when consent is active:**

| Data | Storage location | Retention |
|------|-----------------|-----------|
| Image data | RAM only during the API call | No permanent storage |
| Image checksum (SHA-256 hash) | `identification_requests` collection | 90 days, then automatically deleted |
| Recognition result (species suggestions) | `identification_requests` collection | 90 days, then automatically deleted |
| Selected species | Link to the created plant | Lifetime of the plant |

All EXIF metadata is removed before transmission to Pl@ntNet (GPS coordinates, camera model, capture time).

### Cloud-Based Pest Detection (pest_detection_cloud)

[Pest detection by photo](pest-detection.md) sends your image — depending on the operator's configuration — either to a self-hosted recognizer (no consent required) or to the Kindwise plant.health cloud service. This consent is only required when the cloud adapter is active. As with plant identification, the photo is stripped of EXIF metadata before sending and is not stored permanently.

---

## Objecting to Processing (GDPR Art. 21)

You can object to the processing of your data for certain purposes where processing is based on legitimate interest.

!!! info "API only: Filing an objection"
    There is currently no dedicated area in the interface for filing an objection — it can be filed via `POST /api/v1/privacy/object` (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

The system reviews the objection. For processing based on GDPR Art. 6(1)(f) (legitimate interest), processing will cease unless compelling legitimate reasons are present.

---

## Deleting Your Account (GDPR Art. 17)

You have the right to erasure of your data.

!!! danger "Account deletion is permanent"
    Deletion cannot be undone. Download your data export first if you want to save your data.

### Deletion Process

1. Navigate to **Privacy** > the **Delete Account** tab
2. Click **Delete Account**
3. In the confirmation dialog, click **Yes, Delete Account**

The same action can also be triggered directly via the API: `POST /api/v1/privacy/erasure` starts the deletion, `GET /api/v1/privacy/erasure/{erasure_key}` returns the status (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

What happens next:

```
Immediately:
- Soft-delete of the account (status: deleted)
- All active sessions are terminated
- You can no longer log in

Personal data (GDPR Art. 17):
- Anonymised immediately or deleted after 90 days

Legally protected data (GDPR Art. 17(3)(b)):
- Harvest documentation and IPM treatment records:
  Are anonymised (user reference removed),
  the data itself is retained (CanG, PflSchG)

After 90 days:
- Hard-delete of all remaining personal data
```

!!! note "Why are harvest records not fully deleted?"
    The CanG (German Cannabis Act) and the PflSchG (German Plant Protection Act) require that harvest and treatment data be retained for audit and verification purposes. Your name and contact details are removed; the quantity and treatment data remains as anonymized records. This is legally covered by GDPR Art. 17(3)(b).

---

## Photos and Attachments (Object Storage)

Kamerplanter stores photos and files through a storage adapter configured by the platform operator. As a user, the following points are relevant to you:

### EXIF Data

When uploading photos, the backend removes all EXIF metadata by default before storing the file. This includes:

- GPS coordinates (location where the photo was taken)
- Camera model and serial number
- Timestamp (from the EXIF header)

The operator may enable EXIF retention per category — this will be noted in the instance's privacy notice when enabled.

### Photos and Account Deletion

When you delete your account, the system distinguishes between two photo types:

| Photo type | What happens |
|-----------|-------------|
| **Personal photos** (profile picture, private notes) | Hard deleted — both the file in storage and the metadata entry are removed |
| **Documentary photos** (diary entries, IPM inspections, harvest photos, plant photos) | Retained but decoupled from your account — `created by` is set to `_anonymized`. If EXIF data is present, it is stripped at this step. |

Files are retained because they belong to the plant record and may be subject to statutory retention obligations (CanG, PflSchG). Your name is no longer linked to the photos after anonymization.

!!! note "Order of deletion"
    Storage cleanup (step 0) happens before database cleanup. This is the only way the system can still retrieve the metadata needed to map file to user.

### Tenant Deletion

When a tenant is deleted (by the platform admin or on request), all binary data for that tenant is completely removed from storage — regardless of the backend in use (local-fs or S3). This is done by deleting all objects with the prefix `t/{tenant_key}/`. The result is documented in the audit log.

### Data Portability (GDPR Art. 20)

Your data export includes all stored attachments as a ZIP archive. The archive contains:

- All files in the relative folder structure of the storage schema
- A `manifest.json` with the mapping `attachment_id → file path → metadata`

---

## Data Retention and Retention Periods

Kamerplanter stores different data categories with different retention periods:

| Data category | Retention period | Reason |
|---------------|-----------------|--------|
| Personal profile data | Until deletion + 90 days | GDPR |
| Sensor data (raw) | 90 days | Storage limitation |
| Sensor data (hourly aggregate) | 2 years | Storage limitation |
| Sensor data (daily aggregate) | 5 years | Storage limitation |
| IP addresses | 7 days, then anonymized | Data minimization |
| Harvest/treatment data | Legal minimum period | CanG / PflSchG |
| Consent log | 3 years after revocation | Accountability |
| Erasure audit log | 1 year | Accountability |

<!-- NFR-011 -->

### Sensor Data Downsampling

Sensor data is automatically compressed in stages:

```
0–90 days:       Raw data (every measurement)
90 days–2 years: Hourly aggregates (Min/Max/Avg)
2–5 years:       Daily aggregates (Min/Max/Avg)
After 5 years:   Automatic deletion
```

!!! info "Why downsampling?"
    Raw sensor data can take up a lot of storage. After 90 days, per-minute values are no longer relevant for most analyses. Downsampling significantly reduces storage consumption without losing important long-term trends.

---

## IP Anonymization

IP addresses are generally only stored in plain text for 7 days. After that they are anonymized to the /24 subnet (the last 8 bits set to 0), so that individual assignment is no longer possible.

---

## Sensor Data and Privacy (DPIA)

Certain sensor data can allow inferences about presence patterns (CO₂ concentration, motion detectors, manual overrides). A **Data Protection Impact Assessment (DPIA)** has been carried out for such data. The key measures:

- Sensor data is fundamentally **not** shared with other tenants or third parties
- The platform operator can only view sensor data after an explicit support request and with your consent
- Aggregated statistics (without personal reference) may be used for system improvement — you can disable this in the consents

---

## Frequently Asked Questions

??? question "Is my plant data used for commercial purposes?"
    No. Your plant data is not shared with third parties or used for commercial purposes. The privacy policy governs this bindingly.

??? question "How long does a data export take?"
    Depending on the data volume, the export takes 1–5 minutes. You currently check the status and download the finished file via the API (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)). The download link is valid for 72 hours.

??? question "Can I delete individual plant records without deleting my account?"
    Yes. You can delete individual plants, locations and tasks at any time. Account deletion is only necessary if you want to remove all your data at once.

??? question "What happens to my data if the service is shut down?"
    You will be informed at least 30 days in advance and have the opportunity to export all your data. After shutdown all personal data will be deleted within 90 days.

---

## See Also

- [Account & Sign-In](account.md)
- [Tenants & Gardens](tenants.md)
