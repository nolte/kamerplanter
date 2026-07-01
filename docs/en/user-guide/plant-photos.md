# Plant Photo Gallery

Every plant instance in Kamerplanter can have its own photo gallery. This lets you recognise your plants at a glance in the list view, and helps you document how they develop over time — from seedling to harvest.

---

## Prerequisites

- You are logged in to Kamerplanter and have at least one plant instance.
- To upload, delete, or set a cover photo you need the **Grower** or **Admin** role in your tenant. As a **Viewer** you can browse the gallery but cannot upload or delete photos.

---

## Opening the Gallery

1. Open the side menu and navigate to your **Plants**.
2. Click on the plant whose gallery you want to open.
3. Select the **Photos** tab.

You will see two separate sections: at the top, **Your own photos** — the images you have uploaded for this plant yourself — and, if available, **Reference images of the species** below them (see [Viewing Reference Images of the Species](#viewing-reference-images-of-the-species)). If no own photo has been uploaded yet, a neutral placeholder is shown.

---

## Uploading a Photo

Click **Add photo** in the Photos tab. A dialog opens with three capture options:

=== "Camera (smartphone)"

    1. Tap **Take photo**.
    2. Your device opens the camera app.
    3. Photograph your plant and confirm the shot.

=== "Camera (webcam, desktop)"

    1. Click **Take photo**.
    2. Your browser asks for camera permission — confirm it.
    3. A live preview of your webcam opens.
    4. Position the plant in the frame and click **Capture**.

=== "File upload"

    1. Click **Upload photo** or drag and drop an image file into the marked area.
    2. Supported formats: JPEG, PNG, WebP (up to 25 MB per image).

!!! tip "Tips for good plant photos"
    - Photograph in good daylight or close to a light source.
    - Keep the camera steady so the image is sharp.
    - A calm, uncluttered background makes the plant easier to see.
    - Several photos from different angles or at different growth stages are more useful than a single shot.

After uploading, the photo appears in the gallery immediately. The system automatically creates smaller preview versions in the background — this takes only a few seconds.

!!! note "Privacy: EXIF data"
    When a photo is uploaded, **all EXIF metadata is removed** — including GPS coordinates, camera model, and timestamp. Your location and device are not linked to the stored photo. For details on how photos are handled when an account is deleted, see: [Privacy (GDPR) — Photos and Attachments](privacy.md#photos-and-attachments-object-storage).

### Photo limit

By default, up to **50 photos** can be stored per plant instance. The operator can adjust this value in the server configuration. When the limit is reached, a notice appears — delete older photos to make room for new ones. For operators, see: [Configure Storage](object-storage.md).

---

## Viewing a Photo Full-Screen (Lightbox)

Click any photo in the gallery to open it in full-screen view. In the lightbox you can navigate between photos using the arrow keys (or swipe on mobile). Close the lightbox with **Esc** or the close button.

---

## Captioning Photos

For each photo you can add a **comment** (e.g. "first flower opened") and a **capture date**. This is useful when you upload photos retrospectively — for example, older pictures from your camera roll — where the actual date the photo was taken differs from the upload date.

### Editing a comment and capture date

1. Hover over the photo in the gallery (or press and hold on mobile).
2. In the photo menu, click **Edit**.
3. A dialog opens with two fields:
   - **Comment** — free text, max. 500 characters (e.g. growth status, notable observations).
   - **Capture date** — pre-filled with the upload date by default; you can change it to an earlier date. A date in the future is not permitted.
4. Click **Save**.

!!! note "Capture date after EXIF removal"
    When a photo is uploaded, all EXIF metadata — including the camera's technical timestamp — is removed (see [Privacy: EXIF data](#uploading-a-photo)). For this reason there is no automatically extracted capture date. You can set one manually at any time.

### Display in gallery and full-screen view

If a comment or capture date is set, it is shown **below the thumbnail** in the gallery and **in the lightbox**. Photos without any caption show only the upload date.

!!! tip "Build a visual growth log"
    If you regularly add a capture date and comment to your photos, you automatically create a visual growth record of your plant over time.

---

## Checking Image Quality

You can send a gallery photo to the plant recognition engine on demand to assess whether it is **sharp and representative enough**. The result appears as a coloured traffic-light badge on the photo and is saved — so you do not have to repeat the check every time.

!!! note "What is this useful for?"
    The quality check answers the question: "Would the plant recognition reliably identify my plant from this photo?" A photo taken from the wrong angle, in backlight, or severely out of focus will be rated "unsuitable" — telling you which photos to replace or supplement.

### Starting a quality check

1. Hover over the photo in the gallery (or press and hold on mobile).
2. In the photo menu, click **Check quality**.
3. Select the recognition path (see below) and confirm.
4. The check runs in the background; the result appears as a traffic-light badge on the photo.

You can repeat the check at any time — for example after replacing a photo.

### Recognition paths

=== "Pl@ntNet (external API)"

    Pl@ntNet is a scientific species recognition project. When you use this option, your photo is **sent to an external third party** (Pl@ntNet / Plantarium).

    !!! warning "Privacy notice: data leaves your instance"
        When you choose Pl@ntNet, the photo is transmitted to the Pl@ntNet API. Your Kamerplanter instance has no control over how Pl@ntNet processes or stores the photo. Please read [Pl@ntNet's privacy policy](https://plantnet.org/privacy-policy/) before using this option.

        - You must give **one-time consent** allowing your photos to be sent to Pl@ntNet for identification purposes (the same consent as for the plant identification feature).
        - You can revoke this consent at any time under **Account Settings → Privacy → Consents**.
        - In **Light mode** (anonymous access), Pl@ntNet is only available if the instance operator has explicitly enabled it.

=== "DINOv2 (self-hosted, not yet available)"

    DINOv2 is a self-hosted recognition engine with no data transfer to third parties. Your photo does not leave the Kamerplanter instance.

    !!! note "Not yet available — Phase 2 of plant recognition"
        DINOv2 is only available once **self-hosted plant recognition (Phase 2)** has been set up on your instance. The option is already visible in the menu but disabled — it will activate automatically once Phase 2 is live.

### Understanding the traffic-light result

| Rating | Meaning | Typical reason |
|--------|---------|----------------|
| Green — good | The plant was recognised with high confidence; the expected species ranked first. | Sharp, well-lit photo with a clear, typical view. |
| Yellow — fair | The expected species was recognised but did not rank first, or showed moderate confidence. | Unusual angle, slight blur, or atypical growth stage. |
| Red — unsuitable | The plant was not recognised, or the expected species does not appear in the results. | Strong blur, backlight, or wrong framing (e.g. only the pot, not the leaves). |

The result also includes the **three most likely recognised species** with confidence scores — even if your plant has no assigned species, you can see whether the photo was identified as a plant at all.

!!! note "No species comparison without an assigned species"
    If your plant does not yet have a species assigned (the Species field is empty), the expected-vs-actual comparison is skipped. The traffic light then relies solely on whether the image is recognised as a plant at all.

### Who can trigger a quality check?

Only users with the **Grower** or **Admin** role can start a new quality check. As a **Viewer** you can see an existing result saved on the photo, but you cannot trigger a new check.

---

## Setting a Cover Photo

A cover photo appears as a preview in the **Info tab** of the plant detail page and in the **plant list view**. This way you recognise your plant at a glance without opening the detail page.

To set a cover photo:

1. Hover over the desired photo in the gallery (or press and hold on mobile).
2. The photo menu appears — click **Set as cover**.
3. The photo is marked with a small star icon.

!!! tip "No cover photo set manually?"
    If you have not set a cover photo, the system uses the **first photo** in the gallery as the preview. Plants without any photo show a neutral placeholder.

---

## Deleting a Photo

To delete a single photo:

1. Hover over the photo (or press and hold on mobile).
2. In the photo menu, click **Delete**.
3. Confirm the prompt — this action cannot be undone.

The photo, all preview versions, and the link to the plant are removed completely. No image data remains in the system.

!!! warning "When deleting the plant"
    If you **delete a plant instance**, all associated photos and previews are automatically and completely removed as well.

---

## Viewing Reference Images of the Species

Below your own photos, another section may appear: **Reference images of the species**. These are **example images of the plant species** — not your own plant, but typical shots from public image archives (GBIF, Wikimedia Commons). They come from the same image collection used by the recognition engine for comparison, and they help you compare your plant against typical specimens of the species — for example, to check whether the leaf shape or flower colour matches the expected species.

!!! note "What is a reference image?"
    A **reference image** is an example photo of a plant species from a public, license-clean source (GBIF, Wikimedia Commons) — licensed either **CC0** (public domain, no attribution required) or **CC-BY** (free to use, attribution required). It shows an arbitrary, typical specimen of the species, never your own plant.

### When does the section appear?

- Your plant instance must have a **species** assigned (the "Species" field on the detail page is filled in).
- Reference images must already exist for that species in the system.

If either condition is not met, the section simply stays **hidden** — no error message or empty box is shown. Your own photo gallery works completely independently of this.

### Viewing licence and attribution

Hovering over a reference image (or tapping it briefly on mobile) reveals an info icon at the bottom of the image. It shows you:

- the **attribution** (author/source), where the licence requires it,
- the **licence** (e.g. "CC-BY 4.0" or "CC0"),
- for some images, the depicted **plant organ** (e.g. leaf, flower, fruit, bark).

!!! note "Why is the attribution shown? (CC-BY)"
    The **CC-BY licence** ("Creative Commons – Attribution") allows free use of an image but requires that the author be credited. Kamerplanter therefore displays this information directly on the image. Images under **CC0** are in the public domain — no attribution is required, though it may still be shown if the source provides one.

!!! tip "Read-only — cannot be edited"
    You can only **view** reference images. They cannot be edited, deleted, or set as a cover photo — those actions are only possible with your own photos (see above). Which reference images stay active for a species is decided exclusively by a platform admin on the master-data species page (see [Curating Reference Images](reference-image-curation.md)).

---

## Optional Contribution to Plant Recognition

Kamerplanter makes it possible to contribute a photo of a correctly identified plant as an additional reference for the **self-hosted plant recognition** system (DINOv2). This is voluntary, curated, and only active with your explicit consent.

!!! note "Not yet active — Phase 2 of plant recognition"
    The contribution feature is technically prepared but **only becomes active once the self-hosted recognition (Phase 2) is available on your instance**. As long as the operator has not set up the self-hosted recognition, this setting has no effect.

### How does the contribution work?

If you give consent and the self-hosted recognition is active, gallery photos of plants with a known species are automatically processed as additional references:

- The photo is analysed locally and a **feature vector** (embedding) is created.
- Only the vector is stored for plant recognition — **not the original photo**.
- The original photo stays exclusively in your gallery.
- Your contribution is **not public** and does not leave the Kamerplanter instance.
- New contributions are reviewed by the Platform Admin before they influence recognition quality.

### Giving or revoking consent

The consent for data contribution (`reference_contribution`) is found in the privacy settings:

1. Click your profile picture in the top right.
2. Select **Account Settings** > **Privacy** > **Consents**.
3. Enable or disable **Contribute to plant recognition**.

Revocation takes effect immediately for all future photo uploads. Already-created feature vectors are removed upon revocation and at the latest when the account is deleted.

!!! note "Light mode"
    In Light mode (anonymous access without login) data contribution to plant recognition is not available because the consent system is not active. The gallery works fully in Light mode.

---

## Frequently Asked Questions

??? question "Why don't I see a Photos tab on my plant?"
    The Photos tab always appears on the detail page of a plant *instance*. If it is missing, check that you have opened a **plant instance** (not the species page under Master Data).

??? question "Why don't I see 'Reference images of the species' on my plant?"
    There are two possible reasons: either your plant does not yet have a **species** assigned (the "Species" field on the detail page is empty), or no reference images exist yet for the assigned species. In either case, the section is simply hidden — your own photo gallery is unaffected and keeps working normally.

??? question "Do the reference images show my own plant?"
    No. Reference images show **other, typical specimens** of the plant species from public image archives (GBIF, Wikimedia Commons) — not your own specimen. They serve as a comparison basis, e.g. to check leaf shape or flower colour. Your own photos are found exclusively in the "Your own photos" section above.

??? question "Can I delete or edit a reference image?"
    No, reference images are **view-only** for regular users. Whether a reference image stays active for recognition or is deselected is decided exclusively by a platform admin on the master-data species page — see [Curating Reference Images](reference-image-curation.md).

??? question "Are my photos stored permanently?"
    Yes — this is the key difference from [identifying a plant by photo](plant-identification.md), where the photo is intentionally discarded after analysis. Gallery photos are stored permanently in the storage backend configured by the operator (local filesystem or S3). You can delete any photo individually.

??? question "What happens to my photos if I delete my account?"
    If you have uploaded photos to a **shared tenant** (e.g. a community garden), those photos remain as part of the plant record — your name is removed (anonymisation). In a **personal tenant**, the exact handling depends on the operator's configuration. Full details: [Privacy (GDPR) — Photos and Attachments](privacy.md#photos-and-attachments-object-storage).

??? question "How many photos can I upload per plant?"
    By default, up to **50 photos** per plant instance. The operator can configure this value.

??? question "Can I download my photos?"
    Click on the photo in the lightbox and use your browser's save option (right-click → "Save image"). A dedicated download button is not available in the current version.

??? question "Why does the photo upload dialog look the same as for plant identification?"
    The capture interface (webcam / smartphone camera / file upload) is the same component used for plant identification. The difference lies in the outcome: for identification the photo is discarded after analysis; for the gallery it is stored permanently.

??? question "Can I set a capture date in the past?"
    Yes — a date in the past is explicitly allowed so you can backfill photos from your camera roll with the actual date they were taken. A date in the future is rejected.

??? question "What happens to a comment and capture date when I delete a photo?"
    When you delete a photo, all associated data — original image, preview versions, and metadata (including comment and capture date) — is removed completely and cannot be undone.

??? question "Is my photo saved or shared when I run a quality check?"
    It depends on the recognition path you choose. With **DINOv2** (self-hosted), the photo stays on your instance and is not transmitted anywhere. With **Pl@ntNet**, the photo is sent to the external Pl@ntNet API — your consent is required for this. The **traffic-light result** (rating and top-3 species) is saved on the photo in your gallery so you do not need to repeat the check later.

??? question "What does 'Pl@ntNet must be enabled' mean in Light mode?"
    In Light mode (anonymous access without login), the individual consent mechanism is not active. The instance operator can enable Pl@ntNet for all gallery users globally — in that case no individual consent step is needed. If the operator has not done so, only DINOv2 (once available) can be used as a recognition path.

---

## See Also

- [Managing Master Data](plant-management.md) — Assigning a species to a plant instance
- [Curating Reference Images](reference-image-curation.md) — Admin guide: which reference images are active
- [Identify a Plant by Photo](plant-identification.md) — Determine the species of an unknown plant
- [Privacy (GDPR)](privacy.md) — EXIF handling, deletion behaviour, consents
- [Configure Storage](object-storage.md) — Operator documentation for the storage backend
