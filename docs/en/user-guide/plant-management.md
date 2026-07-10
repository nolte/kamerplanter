# Managing Master Data

Kamerplanter stores all basic plant data — species, cultivars, and botanical families — as **master data**. This forms the basis for planting runs, nutrient plans, phase control, and care reminders.

## Overview

Master data is the central knowledge base of the system. Each plant species is captured with up to 80+ structured fields:

| Entity | Description | Example |
|--------|------------|---------|
| **Botanical Family** | Plant family with crop rotation category | Solanaceae (nightshades) |
| **Species** | Botanical species with taxonomy, climate, light, propagation | *Solanum lycopersicum* (tomato) |
| **Cultivar** | Breeding variety with cultivar-specific properties | San Marzano, Cherry Roma |

The hierarchy is: Family → Species → Cultivar. Each cultivar belongs to exactly one species, each species to exactly one family.

## Managing Species

### Creating a Species

1. Navigate to **Master Data** > **Species**
2. Click **New Species**
3. Fill in at least the required fields:
    - **Scientific Name** (e.g. *Solanum lycopersicum*)
    - **Common Names** (e.g. Tomato, Tomate)
    - **Family** (e.g. Solanaceae)
    - **Genus** (e.g. Solanum)

!!! tip "Expertise levels affect field visibility"
    In **Beginner mode**, only the most important fields are shown. Advanced fields like allelopathy score, photoperiodism, or root type only appear in **Intermediate** or **Expert mode**. You can always access all fields via the "Show all fields" toggle, even in Beginner mode.

### Key Species Fields

Field labels in the UI are shown in German (or English, depending on your language setting); you'll find the internal field name (code name) in parentheses, e.g. for API access or CSV import.

| Field | Description | Example |
|-------|------------|---------|
| Lifecycle (`cycle_type`, part of the lifecycle configuration — see [Growth Phases](growth-phases.md)) | Annual, Biennial, or Perennial | Annual |
| Growth Habit (`growth_habit`) | Herb, Shrub, Tree, Vine, ... | Herb |
| Root Type (`root_type`) | Fibrous, Taproot, Tuberous, Bulbous, Corm | Fibrous |
| Frost Sensitivity (`frost_sensitivity`) | Sensitive, Moderate, Hardy, Very hardy | Very hardy |
| Nutrient Demand (`nutrient_demand_level`) | Heavy feeder, Medium feeder, Light feeder, Nitrogen fixer | Heavy feeder |
| Photoperiodism (`photoperiod_type`, part of the lifecycle configuration) | Short-day, Long-day, Day-neutral | Day-neutral |
| Toxicity (`toxicity_severity`) | Toxicity for cats/dogs (ASPCA data; ASPCA = American Society for the Prevention of Cruelty to Animals) | Toxic to cats |
| **Propagation Methods** (`propagation_methods`) | One or more typical propagation methods (multi-select) | Seed, Cutting |

!!! note "Not all fields are available in the create dialog"
    The **New Species** dialog only covers the required fields from step 3 plus growth habit and root type. The remaining fields in this table are set afterwards on the species detail page.

### Toxicity Warning on the Species Detail Page

For species with toxicity data on file, the **species detail page** shows a warning above the tabs, listing the affected groups, the severity, and the toxic plant parts and compounds — a safety notice for the humans and pets in your household.

!!! warning "Always visible — regardless of expertise level"
    The toxicity warning appears at **every expertise level**, including Beginner mode, and cannot be hidden. Unlike most advanced fields, it is deliberately not gated behind the usual expertise-level visibility logic, because it protects children and pets. <!-- REQ-001 / REQ-021 -->

Where the data is available, the warning shows:

- **Affected groups** — children, cats, and/or dogs, shown as coloured chips
- **Severity** — Mildly toxic, Moderately toxic, or Severely toxic. Severely toxic species are additionally highlighted with a higher-contrast red warning colour instead of the usual amber/yellow, so they stand out at a glance.
- **Toxic plant parts** — e.g. leaves, seeds, root
- **Toxic compounds** — the named toxic substances, where documented

If a species is verifiably non-toxic, or no toxicity data is recorded for it, no warning appears — so there is no false alarm for harmless species.

!!! note "Two distinct toxicity fields"
    The warning is based on the structured `toxicity` field (scale: non-toxic/mildly/moderately/severely toxic, with affected groups, plant parts, and compounds). This is **not the same** as the `toxicity_severity` field listed in the field table above (scale: low/moderate/high, focused only on cats/dogs). Both fields are maintained independently and are not automatically converted into each other.

### Propagation Methods (propagation_methods)

The **Propagation Methods** field is a multi-select that records how a species is typically propagated. It is visible in **Intermediate mode** and above. <!-- REQ-021 -->

This information feeds into care reminders, propagation planning, and the AI knowledge assistant. All bundled crop species master data already includes the standard propagation methods. <!-- REQ-017 -->

| Value | Label | Description |
|-------|-------|-------------|
| `seed` | Seed | Generative propagation from seeds |
| `cutting` | Cutting | Rooted shoot taken from a mother plant (clone) |
| `division` | Division | Plant split into several parts |
| `rhizome_division` | Rhizome Division | Division of underground storage shoots (e.g. ginger, bamboo) |
| `bulb` | Bulb | Propagation via bulblets or daughter bulbs |
| `tuber` | Tuber | Propagation via daughter tubers (e.g. dahlia, potato) |
| `offset` | Offset | Side shoots / pups (e.g. aloe vera, bromeliad) |
| `grafting` | Grafting | Scion onto rootstock (e.g. tomato onto tomatillo) |
| `layering` | Layering | Root a shoot while still attached, then separate |
| `spore` | Spore | Generative propagation for ferns and mosses |
| `runner` | Runner | Creeping stolons (e.g. strawberry, pothos) |
| `leaf_cutting` | Leaf Cutting | Root a leaf or leaf segment (e.g. begonia, sansevieria) |
| `self_seeding` | Self-seeding | Plant self-seeds without human intervention (e.g. borage, calendula) |

!!! tip "Multiple methods possible"
    A species can have several propagation methods at the same time. Tomato, for example, uses `seed` (for growing from seed) and `cutting` (for year-round greenhouse production via cuttings).

!!! note "Visibility by expertise level"
    The **Propagation Methods** field appears from the **Intermediate** expertise level onward. In Beginner mode it is hidden but can be revealed via **Show all fields**.

!!! note "Propagation methods visible in the \"Sowing & Harvest\" tab"
    On the **species detail page** (Master Data > Species) the **Sowing & Harvest** tab (sowing overview) now displays the configured propagation methods as chips — `seed` is highlighted in green. If a species is propagated **exclusively by vegetative means** (e.g. cutting or division only, no `seed` entry), a notice appears explaining that no sowing windows are expected for this species. **Missing sowing data is not a data error in this case** — it simply reflects that the species is not propagated from seed.

### Best Propagation Time (propagation_months)

The **propagation_months** field (Best Propagation Time) adds a timing dimension to propagation methods: in which months is vegetative propagation — division, taking cuttings, removing offsets or runners — most likely to succeed?

The field is also a multi-select; the stored values are month numbers 1 (January) through 12 (December), deduplicated and sorted.

**Where in the UI:** In the **Sowing & Harvest** tab on the species detail page, in two places:

1. **Propagation card** — The card has a read/edit toggle (pencil icon in the top right):
    - **Read view:** "Best propagation time: March–April" (condensed month display)
    - **Edit mode:** 12 clickable month chips — click the desired months, then **Save**

2. **Monthly timeline (bar chart)** — The topmost row of the timeline is labelled **"Propagation"** and displays the stored months as a coloured bar (teal). This row is **read-only** — editing is done exclusively via the Propagation card (pencil icon). If no months are stored, the row remains empty.

!!! example "Example: Japanese anemone (*Anemone hupehensis*)"
    The Japanese anemone forms dense rhizome clumps and divides best **in early spring**, before new growth begins. Kamerplanter stores this as `propagation_months: [3, 4]` — March and April. The UI displays this as "Best propagation time: March–April".

!!! note "Distinction from sowing fields"
    The `propagation_months` field applies **exclusively to vegetative propagation** (division, cuttings, offsets, runners, layers). Sowing windows (generative propagation from seed) remain the responsibility of the separate fields `direct_sow_months`, `indoor_start_months`, and `transplant_months`. Both can be populated simultaneously when a species can be grown from seed and propagated vegetatively.

!!! tip "Care reminders benefit automatically"
    Once `propagation_months` is populated, the AI knowledge assistant (and, in a future release, care reminders) can provide concrete hints about the optimal propagation window — without you needing to keep track of the calendar yourself. <!-- REQ-017 -->

### Propagation Notes (propagation_notes)

The **Propagation Notes** field is a free-text field for expert knowledge (max. 1,000 characters) that explains **how** propagation works in practice for this species — which steps require particular care, which mistakes are common, and what makes the difference between success and failure.

The field complements the structured fields `propagation_methods` (techniques) and `propagation_months` (optimal timing) with the practical, hands-on detail that cannot be captured in a simple multi-select list.

**Where in the UI:** In the **Sowing & Harvest** tab on the species detail page, in the **Propagation** card — directly below the propagation method chips and the best propagation time. Switch to edit mode via the pencil icon in the top right of the card:

- **Read view:** The text appears as a distinct callout block, visually separated from the surrounding content. If no text has been entered, the area remains empty.
- **Edit mode:** A multi-line text field with a character counter (max. 1,000 characters). The text is saved together with the other fields in the section via the **Save** button.

!!! tip "What belongs in this field?"
    Record concrete practical tips: substrate temperature for rooting, recommended rooting hormone dose, light requirements immediately after rooting, acclimatisation steps when moving from in-vitro to ex-vitro conditions, or the most common reason cuttings fail for this particular species. General advice that applies equally to all species does not belong here.

!!! note "Visibility by expertise level"
    The **Propagation Notes** field appears from the **Intermediate** expertise level onward. In Beginner mode it is hidden but can be revealed via **Show all fields**.

All bundled species with populated propagation methods already have an expert notes text.

### Editing a Species

1. Click on a species in the list
2. On the detail page you can edit all fields
3. The detail page also shows associated cultivars, growth phases, and nutrient plans

---

## Reference Images in the Species View

Kamerplanter displays reference images for each plant species. These images are automatically sourced from public image databases (GBIF, Wikimedia Commons) and help you quickly recognise a species — even without a botanical background.

### Where do reference images appear?

**In the species list (overview):** A small thumbnail appears in the left column for each species. If no reference image is available for a species yet, you will see a subtle plant icon as a placeholder — this is not an error; it simply means that the reference image acquisition run has not yet found a suitable licence-free image for this species.

**On the species detail page (Overview tab):** A large hero image appears at the top. Below it, the **reference image gallery** shows all available images for the species, sorted by plant organ (leaf, flower, fruit, whole plant).

!!! note "Images appear only after the acquisition run"
    Immediately after installation, the gallery shows the message **"No reference images available yet"**. This disappears once an administrator has run the reference image acquisition job. See the [Sourcing Reference Images](#sourcing-reference-images) section below.

### Image sources and licences

Images are sourced exclusively from providers with publicly usable, licence-compliant photographs:

| Source | Licence | Note |
|--------|---------|------|
| GBIF (Global Biodiversity Information Facility) | CC0 / CC-BY | Primary backbone for species photos |
| Wikimedia Commons | CC0 / Public Domain | Curated, representative species images |

!!! warning "Attribution for CC-BY images (legally required)"
    Images under the **CC-BY** licence require visible attribution. Kamerplanter displays this attribution directly beneath each image in the gallery, for example:

    > © Jane Doe, via GBIF/iNaturalist · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

    This is generated automatically from the stored metadata. No manual entry is required.

    CC0 images (public domain) carry no attribution because the author has waived all rights.

### Sourcing reference images

Reference images are **not loaded automatically** when a species is created. They are produced by a one-time acquisition run triggered by an administrator. For normal operation this run is needed only once — it can be repeated as needed (for example, after importing new species).

!!! tip "For administrators"
    The acquisition run executes as a background process (Celery task) and may take several hours to complete. While it runs, images appear species by species in the UI. For technical details: [Setting Up Plant Identification](../deployment/inference-service.md#step-2-populate-the-reference-index).

**Which species receive images?** The acquisition run searches the image databases for all species in the master data. Species for which no CC0/CC-BY images can be found (rare or exotic plants) receive no entry — this is transparent system behaviour, not a data error.

### Connection to plant identification

The same reference images displayed in the species view also form the basis for **plant identification**. The DINOv2 recognition system compares a captured photo against the stored reference embeddings to determine the most likely species. <!-- REQ-029-A -->

See also: [Plant Identification](plant-identification.md)

## Managing Cultivars

Cultivars are breeding varieties within a species. They inherit base properties from the species and add cultivar-specific data.

### Creating a Cultivar

1. Navigate to a **Species detail page**
2. In the **Cultivars** section, click **New Cultivar**
3. Fill in the fields:
    - **Name** (e.g. San Marzano)
    - **Breeder** (optional)
    - **Traits** (e.g. disease-resistant, high-yield, compact)

## Botanical Families

Families group related species and form the basis for crop rotation planning. Kamerplanter comes pre-installed with the most common families (Solanaceae, Brassicaceae, Fabaceae, Cucurbitaceae, ...).

### Creating a Family

1. Navigate to **Master Data** > **Botanical Families**
2. Click **New Family**
3. Enter the name and optionally the crop rotation category

The actual crop-rotation planning (recommended successor families, wait times, automatic check when creating a plant) is managed separately under **Master Data → Crop Rotation** — see [Companion Planting & Crop Rotation](../guides/companion-planting.md#crop-rotation).

---

## Managing Activities

Besides botanical master data, Kamerplanter also maintains **Activities** as their own master data — reusable templates for care tasks such as topping, defoliation, repotting, or harvest preparation. They form the basis for the [activity plan tab of a planting run](planting-runs.md#activity-plan-tab) and for [workflow templates](tasks.md).

### Where to find them

Navigate to **Master Data → Activities**. Built-in system activities can be edited but not deleted.

### Creating an Activity

Click **Create Activity** and fill in the sections:

| Section | Fields |
|---------|--------|
| Identification | Name and description, both in German and English |
| Classification | Category (e.g. Training/HST [High-Stress Training], Training/LST [Low-Stress Training], Pruning, Defoliation, Transplanting, Harvest Prep, Propagation, General), skill level, stress level, recovery days |
| Execution | Estimated duration, required tools, whether photo documentation is required |
| Scope | **Compatible Species** — leave empty for the activity to apply to **all species** ("Universal"); add species to restrict it ("Species-Specific") |
| Phase Restrictions | **Forbidden Phases** (e.g. flowering, germination) and restricted sub-phases where the activity should only be used with caution |
| Tags & Sorting | Free-text tags and the display order in lists |

!!! tip "Species-specific instead of universal"
    Use **Compatible Species** to avoid accidentally suggesting a cannabis-specific training technique (high-stress training) for tomatoes or houseplants, for example.

<!-- Source: src/frontend/src/pages/stammdaten/ActivityCreateDialog.tsx, src/frontend/src/i18n/locales/de/translation.json (pages.activities) -->

---

## Preparing Master Data with AI

!!! tip "For advanced users"
    Manually compiling all plant data is time-consuming. For developers and advanced users, Kamerplanter offers an **AI-powered pipeline** (Claude Code agents) that automatically prepares and quality-checks new plant species. This is not required for everyday garden use — the bundled master data and CSV import cover most use cases. More details: [Preparing plant data with AI](../guides/ai-plant-data-pipeline.md).

---

## Importing Master Data via CSV

For initial setup or batch creation, you can also import species, cultivars, and botanical families via a CSV file instead of creating them one by one. The import runs through a secure two-phase process (validation report before the actual creation) and is described in full on its own page, [Master Data Import](import.md) — which also covers the supported columns per data type and how duplicates and validation errors are handled.

---

## Prerequisites

- Kamerplanter instance running and accessible
- For CSV import: see the prerequisites on the [Master Data Import](import.md) page

## See Also

- [Master Data Import](import.md) — Import species, cultivars, and families via CSV file
- [External Data Enrichment](../guides/data-enrichment.md) — Automatically fill in missing species data from GBIF and Perenual
- [Preparing plant data with AI](../guides/ai-plant-data-pipeline.md) — Detailed guide to the AI pipeline
- [Plant Identification](plant-identification.md) — Identify a species from a photo
- [Setting Up Plant Identification](../deployment/inference-service.md) — Start the reference image acquisition run (for administrators)
- [Growth Phases](growth-phases.md) — Phase control per species
- [Planting Runs](planting-runs.md) — Accompany plants from sowing to harvest, apply an activity plan
- [Companion Planting & Crop Rotation](../guides/companion-planting.md) — Compatibility and crop-rotation master data
- [Task Planning](tasks.md) — Workflow templates based on activities
- [Fertilization](fertilization.md) — Nutrient plans and feeding charts
- [Propagation Management](propagation.md) — Lineage graph, cuttings, grafting
