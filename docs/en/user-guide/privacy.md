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
| `POST /api/v1/privacy/email-change` | Request an email change (Art. 16) — step-up body `{password}` or `{step_up_code}`, see below |
| `POST /api/v1/privacy/email-change/confirm` | Confirm an email change via token |
| `POST /api/v1/privacy/erasure` | Request account erasure (Art. 17) — body `{confirm_email, password?}`, see below |
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

The export contains the data Kamerplanter attributes to you as a person:

- your account: profile, sign-in methods, sessions, API keys (without the secret key itself), personal preferences, setup progress, favourites
- your memberships in gardens, invitations and your personal garden
- your privacy requests: consents, restrictions, erasure, export and email-change requests
- what you recorded: tasks and comments, diary entries, harvests and quality assessments, inspections and treatments, plant identifications and diagnoses, pest detections, attachments and contributed reference images, imports
- your conversations with the AI assistant, dismissed tips and the related logs
- notifications and their settings, calendar feeds, weather sources and manual device overrides

Plants, locations and sensor data belong to the garden, not to one person, so they are not part of your personal export. Location assignments hang off your membership; your garden's lead can show you which locations are assigned to you.

!!! tip "Data portability"
    The JSON export file complies with GDPR Art. 20 (data portability). You can use it to transfer your data to another system.

---

## Changing Your Email Address (GDPR Art. 16)

You have the right to have your data corrected.

!!! info "API only: Changing your email address"
    Account settings currently show your email address as read-only — changing it is, for now, only possible via the API: `POST /api/v1/privacy/email-change` initiates the change and sends a **verification link to the new address**, `POST /api/v1/privacy/email-change/confirm` confirms it via token (no login needed). Details in [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).

Like account deletion, the request is behind a step-up: your current password, if your account has one — otherwise a fresh sign-in at your linked provider, or, only if you sign in exclusively through GitHub/Apple, the confirmation code (see [API documentation](../api/authentication.md#signing-in-again-to-confirm-oidc)). Your **current** email address is notified as soon as the change is requested.

The new email becomes active once confirmed — all active sessions are ended.

!!! note "Security notice"
    After confirming the new email, all open sessions (browser, app) are terminated. You need to log in again. Your old email receives an information email about the change.

!!! warning "A password reset or password change cancels a pending change"
    If you reset your password, change it in account settings, or sign out everywhere, a not-yet-confirmed email change is automatically withdrawn — the link in the verification email stops working afterwards. This protects you if someone else initiated a change in your name.

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
| **AI disease diagnosis** (image recognition for diseases/deficiencies) | Optional | Yes |
| **Photo contribution to plant recognition** (own reference photos) | Optional | Yes |
| **AI access to your plant data** (`ai_tenant_data_access`) | Optional | Yes |
| **AI processing via cloud provider** (`ai_cloud_processing`) | Optional | Yes |
| **Release diary entries for AI analysis** (`diary_ai_analysis`) | Optional | Yes |

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

### AI Access to Your Plant Data (ai_tenant_data_access)

The [AI Assistant](ai-assistant.md) answers plain knowledge questions without this consent. As soon as an answer is meant to use your specific plant context — for chat, future tip cards, the tip of the day, and "why?" explanations — this consent is required.

Only master values are transmitted: scientific plant name, current phase, substrate, EC/pH readings, and aggregated counters (e.g. "3 overdue tasks"). Your name, e-mail address, and free-text notes from your plant diary are **never** transmitted.

!!! note "Revocation"
    After revoking, tip cards are hidden, "why?" buttons become invisible, and chat refuses new messages. Existing chat history remains visible.

### AI Processing via Cloud Provider (ai_cloud_processing)

Required in addition to the previous consent when your instance uses an external cloud provider (e.g. Anthropic, OpenAI) instead of a locally run model (Ollama) for the AI Assistant — this is decided by the platform operator. Cloud providers may involve a third-country data transfer. Local providers do not need this consent.

### Releasing Diary Entries for AI Analysis (diary_ai_analysis)

Lets you release individual [diary entries](plant-diary.md), including free text and photos, for analysis. The analysis is performed by an AI agent that **you** operate yourself, which fetches the data using your own API key — Kamerplanter itself never calls a language model. Nothing is ever analysed automatically: you have to mark every single entry yourself. Only downscaled image renditions without capture location or device identifier are transmitted.

This path is **independent** of the `ai_tenant_data_access` consent above: `ai_tenant_data_access` covers only master values sent server-side to the knowledge base, and explicitly excludes free text from your diary. `diary_ai_analysis` is the only path through which diary content ever leaves a Kamerplanter instance at all — and even then it does not go to a service Kamerplanter operates, but to your own agent.

!!! note "Revoking"
    Revoking this consent prevents new markings; existing analysis results are unaffected and remain visible.

### AI Disease Diagnosis (plant_diagnosis) {#ai-disease-diagnosis-plant_diagnosis}

!!! note "Not yet available in the interface"
    The CV-based **disease and deficiency diagnosis** is implemented as a backend feature but is not yet reachable via a button in the interface (internal reference: REQ-038). The following describes how consent behaves once the feature is enabled.

Analyses your leaf photo to produce a suspected-cause list for **diseases and nutrient deficiencies** — distinct from [Pest Detection](pest-detection.md). Unlike plant identification and cloud-based pest detection, this analysis runs **exclusively self-hosted** on your own Kamerplanter infrastructure: there is no cloud adapter, and your photo never leaves the instance. Consent is still requested because a photo of yours is processed. As with pest detection, the photo is stripped of EXIF metadata before processing and is **never stored permanently** — only a SHA-256 fingerprint is retained for traceability. Every result is explicitly only a hypothesis; a treatment is never triggered automatically.

!!! note "Consent behaviour per deployment mode"
    **Full mode:** The server-side consent check is mandatory — without a granted consent, the backend rejects a diagnosis request.

    **Light mode:** The consent subsystem is not available in [Light mode](light-mode.md); the server-side check is skipped there (as with plant identification).

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
3. In the confirmation dialog, type your **own email address** back in. For accounts with a **local password**, also enter your **current password** (to authorize the deletion). If you sign in through Google or a generic OIDC provider, you instead click **Sign in again** and confirm with a fresh sign-in at that provider; only if you sign in exclusively through GitHub or Apple, click **Send code by email** and enter the confirmation code it mails you.
4. In the confirmation dialog, click **Yes, Delete Account**

!!! info "Confirming with email and password"
    If the email you type doesn't match your own, the dialog shows an error. For local-password accounts, entering the current password is also mandatory — if it's wrong, the dialog stays open and shows an error. In both cases, the account is **not** deleted.

!!! warning "Locked out after too many attempts"
    After several wrong password attempts, the system locks the confirmation for 15 minutes — repeated failures double the wait time up to 4 hours; the dialog shows the remaining wait time. This lock applies account-wide to all confirmations of this kind (deleting your account, deleting a tenant, changing your password) together, but does **not** affect signing in: you can still sign in normally, end individual sessions in the **Sessions** tab (see [Account & Sign-In](account.md#viewing-and-ending-active-sessions)), or reset your password by email.

The same action can also be triggered directly via the API: `POST /api/v1/privacy/erasure` expects the same request body as `DELETE /api/v1/users/me` (see [Deleting Your Account](account.md#deleting-your-account)) — `{"confirm_email": "...", "password": "..."}`, where `password` is only required for a local password. `GET /api/v1/privacy/erasure/{erasure_key}` returns the status (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)).

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

!!! danger "Your personal garden is deleted with it"
    If you are the only active member of your personal garden, it is irreversibly deleted with everything in it — unless someone else is also a member of it; then it is kept for them without your name. Details: [Data Retention — What happens to your personal garden](../guides/data-retention.md#what-happens-to-your-personal-garden).

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
| **Personal photos** (profile picture, private notes) | Hard deleted — the original file, its generated preview images (WebP, 128/512/1280 px) and the metadata entry are removed |
| **Documentary photos** (diary entries, IPM inspections, harvest photos, plant photos) | Retained but decoupled from your account — `created by` is set to `_anonymized`. If EXIF data is present, it is stripped at this step. |

Files are retained because they belong to the plant record and may be subject to statutory retention obligations (CanG, PflSchG). Your name is no longer linked to the photos after anonymization.

!!! note "When another member uploaded the identical file"
    If another member of your garden uploads exactly the same file (identical byte content), each person gets their own entry — but the file itself is stored once and shared. If you delete your account, only your own entry is affected: the stored file and its preview images remain in place as long as at least one other member's entry still points to them, and are only removed once the last entry pointing to them is deleted. Your own entries are always reached by account deletion — regardless of who uploaded the file first.

!!! note "Order of deletion"
    Storage cleanup (step 0) happens before database cleanup. This is the only way the system can still retrieve the metadata needed to map file to user.

If you [contributed your own photos as reference images for plant recognition](plant-identification.md#assigning-the-photo-to-the-new-plant), those contributions are removed on account deletion too: the system deletes the feature vector computed from them from the recognition base. Curated reference images contributed by other users are unaffected.

The same applies to your own [contributed pest photos](pest-detail.md#contribute-your-own-photos): if such a photo was ever promoted by a platform admin for pest recognition, account deletion removes the recognition vector computed from it — regardless of whether the promotion was still active or had already been reverted at the time of deletion.

### Tenant Deletion

When a tenant is deleted (by the platform admin or by a member with the Management extra permission), the system first creates a deletion record and immediately deactivates every membership — nobody has access to the tenant anymore after that. Every reference-image and pest-image vector contributed by a member of that tenant is then removed from the recognition base, followed by all binary data for that tenant — regardless of the backend in use (local-fs or S3) — by deleting all objects with the prefix `t/{tenant_key}/` — and every sensor reading of the tenant from the time-series database.

A single database transaction then removes every domain record the tenant holds: sites, plants, planting runs, diary entries, tasks, tanks, sensors, feeding and watering logs, notifications, calendar feeds, its own master-data entries (e.g. species, fertilizers or nutrient plans it created itself), memberships, invitations, location assignments and API keys restricted to the tenant — together with every link to a deleted record — and finally the tenant record itself.

One exception applies: harvest and treatment documentation (harvest batches, quality assessments, treatments, inspections) must be kept for several years under statutory law (CanG, German Plant Protection Act; see [Statutory Minimum Retention Periods](../guides/data-retention.md#statutory-minimum-retention-periods)). On these records, each member's account reference is replaced by the same tombstone hash account erasure uses, and name fields (harvester, applicator, inspector, assessor) are emptied — the records themselves remain. The AI call log and the MCP call log are likewise retained until their own retention window expires.

After the transaction, the system checks that nothing still references the tenant. If not everything could be removed, or a step failed (e.g. an external service was unreachable), the deletion stays recorded and is retried automatically every day with a growing delay, until it completes fully. The result is documented in the deletion record.

The members' own accounts are not affected — they keep their account and their memberships in other tenants. A member's personal tenant is not removed by a tenant deletion.

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
| AI chat conversations | 90 days | Storage limitation — daily cleanup |
| AI tip cards (cache) | 7 days | Storage limitation |
| AI call log (hashed, no plain text) | 30 days | Storage limitation — daily cleanup |

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
- [AI Assistant](ai-assistant.md)
