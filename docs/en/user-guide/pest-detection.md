# Pest Detection by Photo

With the pest detection feature you can take a photo of your plant and receive a confidence-weighted **assessment** of whether pests or typical damage patterns are visible — and which pests might be responsible. From a finding you can directly create a pest inspection in the [Pest Management (IPM)](pest-management.md) system.

!!! warning "Assessment — not a definitive identification"
    Pest detection is a tool, not a diagnostic instrument. The system always outputs a **disclaimer**. Every result is an assessment based on image data — please check the finding yourself before starting any treatment. An automatic treatment is **never** triggered.

!!! note "Optional feature — operator activation required"
    Pest detection is disabled by default and must be set up by the operator. If no adapter is active, the "Check for Pests" button is hidden — all other features continue to work without restriction. **Operators** can find the setup instructions in the [Enabling Pest Detection](admin.md#enabling-pest-detection) section.

!!! note "Available in full mode only"
    Pest detection requires an authenticated plant context. In **[Light mode](light-mode.md)** (anonymous access) the feature is unavailable — you will see the message "Please sign in to use pest detection".

---

## Prerequisites

- Authenticated user account (not Light mode)
- At least one plant added to your tenant
- Pest detection must be activated by the operator (adapter configured)
- For cloud detection (Kindwise, optional): one-time consent for the purpose `pest_detection_cloud`

---

## Two Detection Modes

The system uses two complementary methods, which are active depending on the configured adapter:

| Mode | When to use | What is detected |
|------|-------------|-----------------|
| **Direct detection** | You can see tiny insects directly on the plant | Pests/beneficial insects as objects, with highlighted locations in the image |
| **Damage pattern / symptom** | You see damage but no insect (webbing, honeydew, suction damage) | Damage patterns from which the likely culprit is inferred |

!!! tip "Damage pattern detection is the more robust starting point"
    Pests such as spider mites or thrips are often tiny and barely visible in photos. Damage pattern detection works reliably even when the insect itself is not visible.

---

## Starting a Pest Check

You start a pest check from the **detail page of a plant**:

### Step 1: Open the plant

1. Open the side menu and click on **Plant Master Data** or **Planting Runs**
2. Select the plant you want to inspect
3. You are now on the plant detail page

### Step 2: Start the check

Click the **Check for Pests** button on the plant detail page.

!!! note "Button not visible?"
    If the button is not visible, the operator of your instance has not enabled pest detection. Contact your administrator.

### Step 3: Take or upload a photo

The "Pest Check" dialog opens. You have three options:

=== "Camera (smartphone)"

    1. Tap **Take photo**
    2. Your device opens the camera app
    3. Photograph the affected area of the plant — clearly visible areas showing abnormalities
    4. Confirm the photo

=== "Camera (webcam, desktop)"

    1. Click **Take photo**
    2. Your browser asks for permission to use the camera — confirm this
    3. A live preview of your webcam opens
    4. Position the affected area in the frame and click **Capture**

=== "File upload"

    1. Click **Upload photo** or drag and drop an image file into the highlighted area
    2. Select a JPEG or PNG file (maximum 8 MB)

!!! tip "Tips for a meaningful photo"
    - Photograph the **affected area** directly: visible insects, webbing, sticky deposits, or leaf discolouration
    - Good light is essential — daylight or a direct lamp close to the subject
    - Hold the camera steady and close enough that details are visible
    - For tiny insects: use your smartphone's macro mode or zoom in close

### Step 4: Wait for the result

Analysis typically takes 2–10 seconds. The system internally divides your photo into overlapping tiles ("tiling") to detect even tiny objects — this is why processing may take slightly longer than with plant identification.

---

## Understanding the Result

### Findings with locations

If pests or damage patterns are detected, you will see:

- **Highlighted areas** in the photo: coloured bounding boxes (direct detection) or highlighted regions (damage pattern)
- **Name of the pest** (common name and, where available, species name)
- **Detection mode**: "Insect found" or "Damage pattern"
- **Confidence level** in percent — how certain the system is
- **IPM link**: if the detected pest is known in the pest management master data, a direct link appears along with a **More about this pest** link leading to the [pest detail page](pest-detail.md) with fact sheet, reference images, and control measures

!!! warning "Read the confidence level critically"
    Under real-world conditions, detection rates range from around 60–70 % depending on pest type and image quality. The system displays the confidence level transparently. High values (>75 %) indicate a clear finding; low values should prompt your own visual inspection.

### When no pests were detected

If the system shows "No pests detected", this does **not** mean the plant is pest-free. The photo might be out of focus, the affected area might be outside the frame, or the pest might be too small for the available image resolution.

> No finding is no proof of a pest-free plant.

Click **Take a new photo** and try again with a clearer image or a different angle.

### Abstention: "No reliable detection"

When the confidence level of all detected hints is below the internal safety threshold, the system shows:

> "No reliable detection — please inspect the plant manually."

This is the **correct behaviour under uncertainty**: the system prefers to make no statement rather than an overconfident wrong one. In this case, a manual inspection via the [IPM system](pest-management.md) is recommended.

### Beneficial insect detected — do not treat

If the system detects a **beneficial insect** (e.g. ladybird larva, lacewing, predatory mite), it shows:

> "This is likely a beneficial insect — please do not treat."

Beneficial insects are **never** presented as pests to be treated. The system reports them in their own category so that you do not accidentally eliminate your natural helpers.

---

## Next Steps After Detection

### Create an inspection (recommended)

The most important follow-up step is a manual pest inspection in the IPM system. Click **Create Inspection** below the result.

The system creates an [IPM inspection](pest-management.md) with the detected pest pre-filled. You then inspect the plant yourself and confirm or correct the finding in the inspection form.

!!! danger "No automatic treatment"
    Pest detection **never** triggers an automatic treatment. The pre-harvest interval gate (mandatory waiting period between treatment and harvest) remains active in every case. All treatment decisions are made by you through the [IPM system](pest-management.md).

### Provide feedback (human-in-the-loop)

Directly below the result there are three feedback buttons:

| Button | Meaning |
|--------|---------|
| **Correct** | The result is correct — you actually found the named pest |
| **Wrong** | The result is incorrect — you see no pest or a different one |
| **Was a beneficial insect** | The insect reported as a pest is actually a beneficial |

Your feedback improves detection quality over time and helps build the indoor pest model.

---

## Detection History

You can view all previous pest checks for a plant:

1. Open the plant detail page
2. Switch to the **Pest History** tab (or scroll down to the "Pest Detection" section)

The history shows date, detection mode, findings, and your feedback. **Photos are not stored** — only the image fingerprint (hash) is retained as a traceability marker; the original image cannot be recovered from it.

!!! note "Retention period"
    Detection records are automatically deleted after a configurable period (default: 90 days). The exact period is determined by the operator.

---

## Privacy and Consent

### Self-hosted detection (default)

If your operator has activated only **local pest detection**, your photo does **not** leave the Kamerplanter instance. No separate consent is required. EXIF metadata (GPS coordinates, camera model) is removed before any processing.

### Cloud detection (Kindwise — optional, opt-in)

If your operator has additionally activated **cloud detection** (Kindwise), this is disabled by default and requires your explicit consent:

- The first time you click "Check for Pests" (with an active cloud adapter), a consent dialog appears
- Without your agreement, the system sends **no photo** to any external service
- Consent is voluntary — you can revoke it at any time

**What you should know:**
- The photo is transmitted to the Kindwise service (Brno, Czech Republic — EU) and discarded after analysis
- EXIF data is removed twice before transmission (frontend + backend)
- The consent purpose is `pest_detection_cloud` and appears in your privacy settings

**Revoking consent:**

1. Click your profile picture in the top right
2. Select **Account Settings** > **Privacy**
3. Under **Consents**, click **Revoke** next to **Pest Detection (Cloud)**

After revoking, only the local adapter is used (if enabled), or the button is hidden.

---

## Frequently Asked Questions

??? question "Why is there no "Check for Pests" button?"
    The button is hidden when the operator of your Kamerplanter instance has not activated pest detection or no adapter is configured. Contact your administrator. All other features continue to work without restriction.

??? question "Are my photos stored?"
    No. The photo is used solely for analysis and immediately discarded afterwards. Only the detection result and an anonymous image fingerprint (SHA-256 hash) are stored — the original image cannot be recovered from this.

??? question "What does "No reliable detection" mean?"
    The system found hints in the photo but is not confident enough to make a specific statement. This is not an error but intentional behaviour (abstention): no statement is better than a wrong one. Inspect the plant yourself or create a manual IPM inspection.

??? question "The system detected a pest — do I have to treat now?"
    No. The result is an assessment, not a treatment order. Inspect the plant yourself first, and if necessary create an inspection via the IPM system. Whether and how to treat is your decision alone — the system at most suggests an inspection and always respects pre-harvest intervals.

??? question "Can the system report a beneficial insect as a pest?"
    The system has a dedicated category for beneficial insects (ladybirds, lacewings, predatory mites, etc.) and reports them explicitly with the message "Beneficial — do not treat". A beneficial insect is never listed in the "pest" category. If you do spot a misclassification, use the feedback button "Was a beneficial insect" — this directly improves the model.

??? question "How reliable is the detection?"
    Under real-world conditions, detection rates are significantly lower than in laboratory settings. Realistic accuracy is around 60–70 % — depending on image quality, pest species, and infestation level. The system is intended as an **early-detection aid**, not as a reliable standalone diagnosis. A finding should always be confirmed by your own visual inspection.

??? question "What is the difference between pest detection and plant identification?"
    [Plant identification by photo](plant-identification.md) identifies the **species** of an unknown plant. Pest detection analyses a photo of a **known plant** for infestation and damage patterns. Both features use different models and adapters.

??? question "I tried pest detection in Light mode and it's unavailable — why?"
    Pest detection requires an authenticated user and a plant context (which plant is being inspected?). Light mode does not provide such a context. Sign in to use the feature.

---

## See Also

- [Pest Management (IPM)](pest-management.md) — Inspections, treatments, pre-harvest intervals
- [Pest Detail Page](pest-detail.md) — fact sheet, reference images, control measures, and beneficials per pest
- [Identify Plant by Photo](plant-identification.md) — Species identification for unknown plants
- [Privacy (GDPR)](privacy.md) — Consents and data subject rights
- [Plant Photo Gallery](plant-photos.md) — Saving photos for a plant
