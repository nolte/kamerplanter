# Plant Identification

The plant identification feature in Kamerplanter lets you identify an unknown plant from a photo — entirely on your own hardware, at no cost, and without your photo ever leaving the instance.

---

## Prerequisites

- A Kamerplanter instance with the inference service enabled (see [Setting Up Plant Identification](../deployment/inference-service.md))
- At least one [species master record](plant-management.md) with indexed reference images
- Camera, smartphone upload, or image file (JPEG, PNG; max. 10 MB)

!!! tip "Works offline"
    The primary path runs entirely locally. No external API key, no data transfer — even on an isolated home network.

---

## How to Identify a Plant

### Step 1: Open Plant Identification

Click **Identify Plant** in the navigation or open the dialog via the **"Identify Plant"** button on the master data page.

!!! info "Screenshot pending"
    This screenshot will be added in a future version.

### Step 2: Take or Upload a Photo

Choose one of three input methods:

=== "Webcam"

    Click **Use Camera**. The browser will ask for camera permission.
    Point the camera at the plant and click **Capture**.

=== "Smartphone"

    Tap **Take Photo**. Your smartphone opens the camera app directly.
    Photograph the plant and confirm the image.

=== "Upload File"

    Drag an image file into the highlighted area or click **Select File**.
    Supported formats: JPEG, PNG (max. 10 MB).

!!! tip "Better identification quality"
    Photograph a single, well-lit organ (leaf, flower, fruit) against a clean background if possible. The clearer the subject, the more accurate the result.

### Step 3: Select the Plant Organ

Specify which part of the plant you photographed. This improves matching accuracy.

| Organ | Choose when photographing... |
|-------|------------------------------|
| Leaf | Leaf blade, petiole, leaf veins |
| Flower | Flower, bud |
| Fruit | Fruit, berry, seed |
| Bark / Stem | Stem, branch, bark texture |
| Root | Root, rhizome |
| Whole plant | Entire plant, multiple organs visible |

### Step 4: Start Identification and Review the Result

Click **Identify Plant**. Depending on your hardware, identification takes a few seconds.

The system displays a suggestion list with the most similar species and a confidence score (0–100 %).

!!! info "Screenshot pending"
    This screenshot will be added in a future version.

**What the confidence scores mean:**

| Confidence range | Meaning | Recommendation |
|:----------------:|---------|---------------|
| 85 % and above | High match | Accept directly |
| 50–84 % | Moderate match | Review and confirm |
| 10–49 % | Uncertain match | Seek a second opinion |
| Below 10 % | No reliable result | Retake photo or search manually |

### Step 5: Confirm the Result

Click the suggestion that best matches your plant. The system does **not** create a plant record automatically — you decide explicitly whether to link the plant to this species.

Click **Create with this species** to start a new planting run with the identified species directly.

---

## When Identification is Uncertain

Not all species are equally well represented in the reference index. The system communicates gaps transparently:

!!! warning "Species with insufficient reference images"
    If fewer than 5 reference images have been indexed for a species, it will **not** appear in the suggestion list — even if the species exists in the system. In this case, the system offers:

    - **Retake the photo** from a different angle or with a different organ
    - **Manual search** in the master data
    - **Second opinion via Pl@ntNet** (only with your consent — see the "Pl@ntNet Fallback" section below)

### What you can do

1. Try photographing a different plant organ (e.g., flower instead of leaf).
2. Ensure good lighting and a neutral background.
3. Search for the species manually via **Master Data > Search** using the scientific or common name.
4. Enable the Pl@ntNet fallback for a second opinion (see below).

---

## Pl@ntNet Fallback

When local identification does not yield reliable results (confidence below threshold), the system can optionally query **Pl@ntNet** as an external second opinion.

!!! warning "Your photo leaves the instance"
    When using the Pl@ntNet fallback, your photo is transmitted to the external Pl@ntNet service (France). Pl@ntNet is free of charge (up to 500 requests/day), but your image leaves your network.

    **Kamerplanter asks for your explicit consent before the first use.** You can revoke this consent at any time under **Settings > Privacy**.

### Granting Pl@ntNet consent

1. Open **Settings > Privacy**.
2. Enable **"Pl@ntNet fallback for plant identification"**.
3. Read the privacy notice and confirm.

Once consent has been granted, the option **"Ask Pl@ntNet"** appears automatically in the identification dialog when local confidence is too low.

---

## Privacy at a Glance

| Aspect | Primary path (local) | Pl@ntNet fallback |
|--------|:--------------------:|:-----------------:|
| Photo leaves the instance | No | Yes |
| Photo is stored | No | No |
| Third-country transfer | No | Yes (France, EU) |
| Cost | €0 | €0 (up to 500/day) |
| Consent required | No | Yes |
| EXIF data (GPS, camera data) | Removed | Removed before transfer |

!!! note "No photo is stored"
    Kamerplanter never stores your photo permanently. The image is held in memory only during processing and discarded afterwards. The identification log records only which species was identified — no image.

---

## Frequently Asked Questions

??? question "Why does identification return no results for my plant?"
    Possible reasons: (1) The species is not in the master data — so no reference index can exist. (2) Fewer than 5 reference images are indexed for the species (coverage gap). (3) The photo quality is too low. Try a sharper photo of a different organ.

??? question "How accurate is the identification?"
    Accuracy depends on the quality and number of reference images. For common houseplants, vegetables, and herbs, coverage is high (80–90 %). For exotic or rare species, results may be less certain. The system always shows the confidence score transparently.

??? question "Can the identification distinguish cultivars (varieties)?"
    No. Identification works at species level, not cultivar level. The reason: license-free, cultivar-specific reference images do not exist in sufficient quantity. To identify a specific cultivar, use the manual search in master data.

??? question "Are my photos used to train AI models?"
    No. Kamerplanter uses your photos exclusively for the current identification request. They are neither stored nor used for training or any other purpose.

??? question "Can I use identification without an internet connection?"
    Yes — the primary path (local DINOv2 inference) works entirely offline. Only the Pl@ntNet fallback requires an internet connection, and only if you have manually activated it.

??? question "I accidentally uploaded a photo with GPS data — was my location saved?"
    No. Kamerplanter automatically removes all EXIF metadata (including GPS coordinates) before any processing. Location data is never read or stored.

---

## See Also

- [Plant Master Data — Adding Species](plant-management.md)
- [Starting a Planting Run](planting-runs.md)
- [Privacy (GDPR)](privacy.md)
- [Setting Up Plant Identification (Deployment)](../deployment/inference-service.md)
- [Image Recognition Architecture](../architecture/ai-architecture.md#image-recognition-dinov2)
