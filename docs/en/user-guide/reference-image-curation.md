# Curating Reference Images

Plant identification works by comparing a user's uploaded photo against a stored **reference index**: for each plant species, several license-clean reference images are stored as feature vectors (DINOv2 embeddings). The more carefully this index is curated, the more accurately the recognition engine performs.

As a **platform admin**, you can manually **deselect** individual reference images after a visual inspection so they no longer influence recognition results. Deselected images are retained in the system (audit trail) and can be reactivated at any time.

!!! note "Platform admins only"
    Curation is exclusively available to users with the platform role **admin**. Regular users see only active reference images in the public gallery.

---

## Why do poor reference images affect recognition?

The system compares the user's photo against every individual reference image of a species — not a single prototype. If a reference image is unsuitable, it can cause incorrect matches:

| Image problem | Possible effect |
|--------------|----------------|
| **Blurry image** | Feature vectors are non-specific; the engine may favour randomly similar species |
| **Wrong organ** (e.g. bark instead of leaf) | The system matches on the wrong plant feature |
| **Wrong species** shown | All results for this species are "polluted" by a misidentified specimen |
| **Duplicate** (same photo more than once) | One particular perspective is over-represented |
| **Irrelevant content** (soil, pot, background only) | No plant feature present; adds noise to the index |

By selectively deselecting such images you improve recognition accuracy for the affected species without permanently losing any data.

---

## Opening the Reference Image Gallery

1. Sign in as a platform admin.
2. Open the **Plant Master Data** section from the side menu.
3. Click on a **plant species** (e.g. *Monstera deliciosa*) to open the species detail page.
4. Switch to the **Reference Images** tab.

The gallery shows all reference images for this species. Deselected images appear greyed out and carry the label **Deselected**.

!!! tip "Hide deselected"
    As soon as at least one image is deselected, a **Hide deselected images** toggle appears at the top. When enabled, the gallery shows only the active images currently used in recognition. If this leaves no images visible, a corresponding hint is shown.

!!! tip "Jump to the image source"
    Each image tile has an **open icon** (↗) in the bottom right. Clicking it opens the image's original source (GBIF, Wikimedia, etc.) in a new tab — handy for checking the license, author, and higher-resolution variants.

---

## Deselecting an Image

### Step 1: Assess the image visually

Look carefully at the reference image. Typical reasons for exclusion:

- The image is blurry or too dark
- The wrong plant part is shown (e.g. the pot instead of a leaf)
- The plant in the image looks like a different species
- The same image appears more than once in the gallery (duplicate)
- The image content is not botanically relevant (e.g. label photo, pure habitat shot)

### Step 2: Open the deselect dialog

On the image tile, click the **Deselect icon** (crossed-out eye) in the bottom right. The deselect dialog opens.

### Step 3: Select the reason

In the dialog, choose the appropriate exclusion reason:

| Reason | When to use |
|--------|------------|
| **Blurry** (`blurry`) | Image too blurry to provide a meaningful feature |
| **Wrong plant organ** (`wrong_organ`) | Does not show the expected organ (leaf, flower, fruit, bark) |
| **Wrong species** (`wrong_species`) | A different species is depicted |
| **Duplicate** (`duplicate`) | This image already exists in another form in the gallery |
| **Irrelevant** (`irrelevant`) | No usable plant content (soil, pot, pure habitat shot) |
| **Manual** (`manual`) | Other reason not covered by the above |

### Step 4: Confirm the deselection

Click **Confirm**. The following notice is shown:

!!! warning "Effect of deselection"
    This image will be removed from plant identification. It remains stored in the system and can be reactivated at any time.

After confirmation the image is immediately excluded from the active recognition index. The change takes effect for all new identification requests — any requests already in progress are not affected.

---

## Responding to Coverage Warnings

If the number of active reference images for a species drops below **5** through deselection, the gallery displays the following warning:

!!! warning "Recognition coverage reduced"
    This species has only **[n] active reference images** (minimum threshold: 5). Recognition may become unreliable or return no results for this species.

From this point on, users are informed transparently during photo identification that this species may not be reliably recognised. To restore full coverage you can:

- Reactivate previously deselected images (if sufficient suitable ones remain)
- Re-populate the reference index for this species (see [Setting Up Plant Identification](../deployment/inference-service.md))

---

## Reactivating a Deselected Image

1. Open the reference image gallery for the affected species (tab **Reference Images**).
2. Deselected images are visible by default (grey tile with the **Deselected** label). If the **Hide deselected images** toggle is on, switch it off.
3. On the grey tile, click the **Reactivate icon** (restore) in the bottom right.

The image is immediately active again and will be included in the next identification request.

!!! note "Audit trail"
    Every deselection and reactivation is recorded with a timestamp, the exclusion reason, and the acting user. The log is accessible under **Admin > Activity Log**.

---

## API Access (for automation)

If you want to perform curation actions via script (e.g. batch deselection after an automated quality scan), the following endpoints are available:

**Retrieve all reference images for a species (including deselected):**

```
GET /admin/reference-images/{species_key}/images
```

The response field `is_active: false` identifies deselected images. `exclusion_reason` contains the stored reason and `marked_at` the timestamp of the last curation action.

**Deselect or reactivate an image:**

```
PATCH /admin/reference-images/{species_key}/images/{id}
```

Request body (deselect):

```json
{
  "is_active": false,
  "reason": "wrong_organ"
}
```

Request body (reactivate):

```json
{
  "is_active": true,
  "reason": null
}
```

!!! note "Authentication"
    Both endpoints require a valid JWT with the platform role **admin**. For automated access a [Service Account](../api/service-accounts.md) is recommended.

---

## Frequently Asked Questions

??? question "Is the image permanently deleted when I deselect it?"
    No. Deselection is a soft delete: the image remains in the system with all its metadata (source, licence, attribution, embedding vector). Only the `is_active` flag is set to `false`. You can reactivate the image at any time.

??? question "What happens to identification requests that are already in progress?"
    Requests that have already started are not affected. The deselected image will no longer be used in any requests started after the deselection. The change takes effect immediately for new requests.

??? question "Can regular users see deselected images?"
    No. The public gallery (species detail page visible to all users) shows only active reference images. Deselected images are only visible in the admin curation view.

??? question "How many reference images does a species need for reliable recognition?"
    The minimum threshold is 5 active reference images. 10–30 images per species from different angles and growth stages are recommended. Below 5 images, the system displays an uncertainty notice during recognition.

??? question "How were the reference images obtained?"
    Reference images are sourced automatically from GBIF and Wikimedia Commons — exclusively images under CC0 or CC-BY licences. The acquisition pipeline filters by quality criteria (minimum resolution, aspect ratio), but cannot detect all content issues. Manual curation complements this automatic pre-selection.

??? question "Can I automate a quality scan and use the API?"
    Yes. The `PATCH` endpoint is designed exactly for this use case. Create a service account with the admin role, run your quality scan, and call the endpoint for each image you want to deselect.

---

## See Also

- [Identify Plant by Photo](plant-identification.md) — End-user guide
- [Plant Photo Gallery](plant-photos.md) — how users see reference images of the species in their own photo gallery
- [Setting Up Plant Identification](../deployment/inference-service.md) — Populating and updating the reference index
- [Platform Admin Area](admin.md) — Overview of all admin functions
- [Service Accounts](../api/service-accounts.md) — Automated API access
