# Identify a Plant by Photo

With photo identification you can photograph an unknown plant and immediately find out what species it is — no botanical knowledge required. The system analyses your photo and suggests the most likely species with a confidence score. You select the matching result and add the plant directly to the system.

!!! note "Optional feature — operator activation required"
    Photo identification is only available if the operator of your Kamerplanter instance has configured a Pl@ntNet API key. If the feature is not set up, the camera buttons are hidden — all other features continue to work without restriction. **Operators** can find the setup instructions in the [Enabling Plant Photo Identification](admin.md#enabling-plant-photo-identification) section.

!!! note "Available in both deployment modes"
    Photo identification works in both **Full mode** (with user accounts) and **[Light mode](light-mode.md)** (anonymous access without login). The only difference is in how consent is handled: in Full mode your consent is stored as a consent record in the backend and can be revoked in the privacy settings. In Light mode consent is obtained and stored **client-side in the browser**. The transparency notice (photo is sent to Pl@ntNet/France, EXIF metadata is removed, no permanent storage) is shown in both modes before the first upload.

---

## Prerequisites

- Access to a Kamerplanter instance where the operator has enabled photo identification
- Consent to image transfer (a consent dialog is shown the first time you use the feature)
- A photo of the plant: webcam, smartphone rear camera, or an image file on your device (JPEG or PNG, maximum 10 MB)

---

## Adding a Plant by Photo

You can start photo identification in two ways:

**Way 1 — Plant master data overview:**
Open the master data section from the side menu. Next to the "New Plant" button you will find the **Add by Photo** button.

**Way 2 — Onboarding Wizard:**
When setting up your first plant, the Onboarding Wizard optionally offers a "Photograph your plant" step. You can skip this step and add the plant manually.

---

## Taking or Uploading a Photo

Once the identification dialog is open, you have three options:

=== "Camera (smartphone)"

    1. Tap **Take photo**
    2. Your device opens the camera app
    3. Photograph the plant — a clear leaf or the whole plant works best
    4. Confirm the photo

=== "Camera (webcam, desktop)"

    1. Click **Take photo**
    2. Your browser asks for permission to use the camera — confirm this
    3. A live preview of your webcam opens
    4. Position the plant in the frame and click **Capture**

=== "File upload"

    1. Click **Upload photo** or drag and drop an image file into the highlighted area
    2. Select a JPEG or PNG file (maximum 10 MB)

!!! tip "Tips for a good photo"
    - Photograph in good light — natural daylight is ideal
    - Hold the camera steady so the image is sharp
    - Show a single clearly visible leaf or the overall shape of the plant where possible
    - Avoid backgrounds with many other plants

---

## Specifying the Plant Part (optional)

If you know what is visible in the photo, you can give the system a hint. This improves recognition accuracy:

| Selection | Description |
|-----------|-------------|
| **Automatic** | The system detects what is in the image itself (default) |
| **Leaf** | A single leaf |
| **Flower** | A flower or blossom |
| **Fruit** | A fruit or berry |
| **Bark** | Tree bark |
| **Whole plant** | The whole plant in overview |

!!! note "Beginner mode"
    In beginner mode (the default for new users) this selection is hidden. The system works automatically. Experienced users can enable the selection in their account settings.

---

## Reviewing the Analysis Result

After uploading, the system analyses your photo — this usually takes 2–5 seconds. You then see a list of up to five suggestions:

Each suggestion shows:

- **Scientific name** of the species (e.g. *Monstera deliciosa*)
- **Common name** (e.g. Swiss Cheese Plant)
- **Confidence percentage** — how certain the system is
- **Reference image** — a comparison photo of the suggested species

!!! tip "How reliable is the recognition?"
    A confidence of 85 % or more means the system is very certain. Between 50 % and 85 % you should compare the reference image carefully. Below 50 % the recognition is uncertain — use the manual search in that case.

### If no plant material was detected

If the system displays "No plant material could be detected in the image", either the photo contains no visible plant or the image is too blurry. Click **Take new photo** and try again with a clearer image.

### If the recognition is uncertain

If all suggestions show less than 50 % confidence, the system displays an uncertainty notice. Click **Search manually** to find the species directly by name.

---

## Selecting a Suggestion and Adding a Plant

### Species already in the database

If the recognised species is known to the system, the **Add this plant** button appears:

1. Compare the reference image with your plant
2. Click **Add this plant**
3. A form opens with the species pre-filled — give your plant a name (e.g. "Monstera living room")
4. Optionally set location and substrate
5. Click **Save**

The plant is now in the system and automatically receives care suggestions based on the recognised species.

### Species not yet in the database

If the recognised species is unknown to the system, you see the notice "This species is not yet in the system". The button then reads **Add species and plant**:

1. Click **Add species and plant**
2. The system automatically creates the new species (scientific name, family, genus)
3. Then add your plant as described above

!!! note "New species"
    Newly created species initially only have basic data (name, family, genus). You can add care data and additional information later in the master data management section or by fetching it via external data enrichment.

---

## Identification History

You can view all your previous photo identifications:

1. Open the side menu and click **Master Data**
2. Click the **Identification History** tab at the top

The history shows the date, identified species and confidence score for each request. Photos are not stored — only the result and an anonymous checksum of the image (which cannot be used to reconstruct the original).

!!! note "Retention period"
    History entries are automatically deleted after 90 days.

---

## Daily Limit Reached

Pl@ntNet (free tier) allows a maximum of 500 identifications per day across the entire instance. When this limit is reached, the following message appears:

> "Daily identification limit reached. Available again tomorrow."

The limit applies to all users of the instance combined and resets daily at midnight (UTC). In the meantime you can add plants as usual using the manual species search.

---

## Revoking or Resetting Consent

If you revoke your consent to image transfer, all camera buttons are immediately hidden. Your identification history (without photos) is retained.

=== "Full mode"

    1. Click your profile picture in the top right
    2. Choose **Account Settings** > **Privacy**
    3. Under **Consents**, click **Revoke** next to **Photo Identification**

    The revocation is saved with a timestamp in the backend and takes effect immediately. You can grant consent again at any time.

=== "Light mode"

    Light mode has no server-side privacy settings. Your consent is stored in the **local browser storage**.

    1. Open **Account Settings** (top right)
    2. Click **Photo Identification** > **Reset Consent**
    3. The consent dialog will appear again the next time you try to upload a photo

    Alternatively: clearing your browser cache or website data will also reset the consent.

---

## Outlook: Offline Recognition (Phase 2)

A future phase plans to run image recognition entirely on your own server (without a third-party service). Photos would then never leave the instance. This feature is still under development and is not yet available.

---

## Frequently Asked Questions

??? question "Why don't I see a camera button?"
    Photo identification is only available if the operator of your Kamerplanter instance has configured a Pl@ntNet API key. Contact the administrator of your instance if you would like to use this feature.

??? question "Are my photos stored?"
    No. The photo is only sent to Pl@ntNet for analysis and discarded immediately after the response. It is not stored permanently on the Kamerplanter server or at Pl@ntNet. Only the recognition result and an anonymous image checksum are kept in the system.

??? question "What is Pl@ntNet?"
    Pl@ntNet is a plant identification service operated by French research institutions (CIRAD, INRAE, INRIA). Identification is performed via an API to which your photo is sent for analysis. Pl@ntNet does not store the image permanently. Your explicit consent is required because the photo briefly reaches the provider's servers in France (EU).

??? question "What happens to the GPS location in my photo?"
    All EXIF metadata is removed before transmission — this includes GPS coordinates, camera model and capture time. Pl@ntNet only receives the raw pixel data.

??? question "Can I identify a plant disease by photo?"
    Disease diagnosis by photo is not yet available in this phase. For diagnosing pests and diseases please use the [Pest Management (IPM)](pest-management.md) features with manual inspection.

??? question "I identified the wrong plant — what now?"
    Open the plant in the master data overview and change the assigned species manually. Click **Edit** and select a different species from the search.

---

## See Also

- [Plant Master Data](plant-management.md)
- [Onboarding Wizard](onboarding.md)
- [Privacy & GDPR](privacy.md)
- [Pest Management (IPM)](pest-management.md)
