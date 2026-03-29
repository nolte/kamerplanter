# Privacy & GDPR

Kamerplanter is built on the principle of **Privacy by Design**. You have full control over your personal data: you can export, correct or have it deleted at any time. All data subject rights under GDPR Art. 15–21 are available as self-service features directly in your account.

---

## Opening Privacy Settings

1. Click your profile picture or initials in the top right
2. Choose **Account Settings**
3. Click the **Privacy** tab

The privacy area has four tabs: **My Data**, **Consents**, **Restrict Processing** and **Delete Account**.

---

## Exporting Your Data (GDPR Art. 15 & 20)

You have the right to know what data the system has stored about you and to receive it in a machine-readable format.

### Requesting a Data Export

1. Navigate to **Privacy** > **My Data**
2. Click **Export Data**
3. The system creates the export asynchronously (takes 1–5 minutes depending on data volume)
4. You receive a notification (in-app or email) when the export is ready
5. Download the JSON file — the link is valid for **72 hours**

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

1. Navigate to **Privacy** > **My Data** > **Change Email**
2. Enter your new email address
3. The system sends a **verification link to the new address**
4. Click the link in the email
5. The new email is now active — all active sessions are ended

!!! note "Security notice"
    After confirming the new email, all open sessions (browser, app) are terminated. You need to log in again. Your old email receives an information email about the change.

---

## Restricting Processing (GDPR Art. 18)

You can restrict the processing of your data for certain purposes — for example if you dispute the accuracy of your data or consider the processing unlawful.

1. Navigate to **Privacy** > **Restrict Processing**
2. Choose the processing purpose from the list
3. Click **Restrict**

During a restriction the affected data is no longer actively processed. The restriction can be lifted at any time.

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

### Revoking Consent

1. Navigate to **Privacy** > **Consents**
2. You see all granted consents with their date
3. Click **Revoke** next to the optional consent
4. The revocation is saved with a timestamp and takes effect immediately

!!! warning "Effects of revoking consent"
    If you revoke consent for external master data enrichment, no new data will be fetched from GBIF or Perenual. Existing enriched data is retained.

---

## Objecting to Processing (GDPR Art. 21)

You can object to the processing of your data for certain purposes where processing is based on legitimate interest.

1. Navigate to **Privacy** > **Restrict Processing**
2. Choose the processing purpose
3. Click **Object to Processing**

The system reviews the objection. For processing based on GDPR Art. 6(1)(f) (legitimate interest), processing will cease unless compelling legitimate reasons are present.

---

## Deleting Your Account (GDPR Art. 17)

You have the right to erasure of your data.

!!! danger "Account deletion is permanent"
    Deletion cannot be undone. Download your data export first if you want to save your data.

### Deletion Process

1. Navigate to **Privacy** > **Delete Account**
2. Confirm with password (or OAuth re-authentication)
3. Click **Permanently Delete Account**

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
    The German Cannabis Act (CanG) and the Plant Protection Products Act (PflSchG) require that harvest and treatment data be retained for audit and verification purposes. Your name and contact details are removed; the quantity and treatment data remains as anonymised records. This is legally covered by GDPR Art. 17(3)(b).

---

## Data Retention and Retention Periods

Kamerplanter stores different data categories with different retention periods:

| Data category | Retention period | Reason |
|---------------|-----------------|--------|
| Personal profile data | Until deletion + 90 days | GDPR |
| Sensor data (raw) | 90 days | NFR-011 |
| Sensor data (hourly aggregate) | 2 years | NFR-011 |
| Sensor data (daily aggregate) | 5 years | NFR-011 |
| IP addresses | 7 days, then anonymised | Data minimisation |
| Harvest/treatment data | Legal minimum period | CanG / PflSchG |
| Consent log | 3 years after revocation | Accountability |
| Erasure audit log | 1 year | Accountability |

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

## IP Anonymisation

IP addresses are generally only stored in plain text for 7 days. After that they are anonymised to the /24 subnet (the last 8 bits set to 0), so that individual assignment is no longer possible.

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
    Depending on the data volume, the export takes 1–5 minutes. You receive a notification when it is complete. The download link is valid for 72 hours.

??? question "Can I delete individual plant records without deleting my account?"
    Yes. You can delete individual plants, locations and tasks at any time. Account deletion is only necessary if you want to remove all your data at once.

??? question "What happens to my data if the service is shut down?"
    You will be informed at least 30 days in advance and have the opportunity to export all your data. After shutdown all personal data will be deleted within 90 days.

---

## See Also

- [Account Settings](../api/authentication.md)
- [Tenants & Gardens](tenants.md)
