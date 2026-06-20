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

You will see all uploaded photos as thumbnail images. If no photo has been uploaded yet, a neutral placeholder is shown.

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
    The Photos tab always appears on the detail page of a plant *instance*. If it is missing, check that you have opened a **plant instance** (not the species page under Master Data). Species pages show reference images from public databases, not a personal gallery.

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

---

## See Also

- [Managing Master Data](plant-management.md) — Reference images for plant species (not instance photos)
- [Identify a Plant by Photo](plant-identification.md) — Determine the species of an unknown plant
- [Privacy (GDPR)](privacy.md) — EXIF handling, deletion behaviour, consents
- [Configure Storage](object-storage.md) — Operator documentation for the storage backend
