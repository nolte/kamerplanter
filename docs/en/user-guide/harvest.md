# Harvest Management

Harvest management guides you from observing harvest maturity through documenting the harvest batch to quality assessment and yield metrics. An integrated safety system automatically checks whether active pest control treatments block the harvest.

---

## Prerequisites

- At least one plant in the flowering phase or approaching harvest
- All active pest control treatments must have completed their pre-harvest interval

---

## Recognising Harvest Maturity

### Expected Harvest Date

For plants with a harvest phase, Kamerplanter shows an **expected harvest date** on the plant detail page. It is calculated from the planting date plus the sum of the planned phase durations (growth phase management) and additionally shows the remaining days or an overdue indicator. No date appears for perennial plants, for species without a defined harvest phase, or for plant species that master data marks as not yielding a harvest at all (purely ornamental plants, for example). In these cases you rely entirely on on-site observation.

### Harvest Readiness Panel and Ripeness Observations

For species that yield a harvest, the plant detail page also shows a dedicated **Harvest Readiness** panel. It calculates an **overall score (0–100)**, a **recommendation** (for example "Optimal," "Approaching," or "Developing"), and an indicator breakdown with stage, individual score, reliability and weighted contribution per indicator — all from the ripeness observations you record (trichomes, brix, foliage die-back, colour, and others).

If no observations exist yet for the plant, the panel shows a corresponding hint instead of an uninformative score of 0. Use the **"Record Ripeness Observation"** button to enter a new measurement right here (indicator, observer, ripeness stage, estimated days to harvest, notes) — the panel then refreshes the assessment automatically.

!!! note "Panel does not appear for species without a harvest"
    If a species is explicitly marked in master data as not yielding a harvest, Kamerplanter hides the harvest readiness panel for that plant entirely, the same rule as for the expected harvest date above. If the field is missing, for imported species without a curated value, the plant counts as harvestable and the panel appears.

### Maturity Indicators by Plant Type

These guidelines help you assess maturity regardless of whether you record it in Kamerplanter:

**Flower heads (e.g. cannabis, hops):**
- Trichome colour under a loupe: milky white = peak compound content, amber = declining
- Pistil colouring: > 70 % brown / orange
- Calyx swelling: fully developed

**Fruiting vegetables (tomato, pepper, cucumber):**
- Colour change from green to the variety's final colour
- Slight give when pressed gently
- Glossy skin

**Root vegetables (potato, carrot):**
- More than 80 % dead foliage
- Hard, non-scrapable skin
- Variety-typical size reached

**Leafy vegetables (lettuce, spinach):**
- Firm head formation in heading varieties
- Crisp texture, no bitter taste
- Harvest before bolting

---

## Pre-Harvest Interval Check (Integrated Pest Management (IPM) Safety Gate)

!!! danger "Harvest blocked during active treatment"
    If a pest control treatment is still within its pre-harvest interval (PHI), Kamerplanter blocks the creation of the harvest batch. You will see a clear error message with the active ingredient and the remaining days.

The pre-harvest interval is the minimum waiting period after applying a plant protection product before the plant may be harvested. These intervals are legally regulated and stored in Kamerplanter per treatment agent.

**Example:** You applied a product with a 14-day PHI on 1 March. The earliest possible harvest date is 15 March. If you try to create a harvest batch on 10 March, the system blocks the creation.

More on pre-harvest intervals: [Integrated Pest Management (IPM)](pest-management.md)

---

## Creating a Harvest Batch

### Step 1: Create the Batch

1. Open **Harvest Batches** in the navigation (`/ernte/batches`).
2. Click **Create Harvest Batch**.
3. On save, the system automatically checks all pre-harvest intervals. If a treatment is still within its interval, an error message appears instead of the new batch.

### Step 2: Enter Harvest Details

| Field | Description |
|-------|-------------|
| Plant | The plant being harvested |
| Batch ID | Optional custom identifier, e.g. "HARVEST-2026-001". Leave empty to have a unique ID assigned automatically. |
| Harvest Type | **Partial harvest**, **Full harvest**, or **Continuous** |
| Harvest Date | Date and time of harvest (default: now) |
| Fresh Weight (g) | Weight of the harvest directly after cutting |
| Harvester | Who performed the harvest? |
| Notes | Observations, anything unusual |

!!! tip "Leaving the Batch ID empty"
    If you leave the **Batch ID** field empty, Kamerplanter automatically assigns a unique identifier following the pattern `HARVEST-<date>-<plant>` (e.g. `HARVEST-20260315-tomato-01`). If you create another batch for the same plant on the same day, the system appends a running `-2`, `-3`, and so on — so you can record multiple partial harvest batches per day without inventing an identifier yourself.

!!! warning "Batch ID already taken"
    If you enter a Batch ID yourself that already exists, Kamerplanter rejects the creation: you see a hint directly on the field plus an error message, and the batch is not saved. Choose a different identifier, or leave the field empty so a unique ID is assigned automatically.

!!! note "Older batches without any identifier"
    Batches created before automatic ID assignment may carry no Batch ID at all. The batch overview shows an em dash ("—") for them, and the detail page uses the generic heading **Harvest Batch** instead of an identifier. The identifier cannot be added afterwards — the edit tab has no field for it. The uniqueness check only applies to identifiers that are actually set, so any number of batches may coexist without a Batch ID. <!-- REQ-007 -->

**Harvest types:**

- **Full harvest**: The entire plant is harvested at once.
- **Partial harvest**: Only part is harvested (e.g. top buds first). You can create as many partial harvest batches for the same plant as you like.
- **Continuous**: For "cut and come again" crops (e.g. cut lettuce, basil) where small amounts are harvested continuously.

!!! note "No automatic status or quality change"
    Neither the harvest type selection nor creating a batch automatically changes the plant's status — not even for "full harvest". You can create as many partial or continuous batches for the same plant as you like. A quality assessment is also not requested when creating the batch; it happens separately (see below). Once the plant is truly done for you, you end its lifecycle through the separate, explicit **Complete Harvest** action (see below) — unlike merely creating a batch, that action does change the status, and permanently so.

---

## Completing the Harvest (Terminal Plant State)

Creating harvest batches documents what you harvested — but as described above, it does not end the plant's lifecycle. That is what the dedicated **Complete Harvest** action is for.

### What happens

1. Open the harvest batch and switch to the **Details** tab.
2. In the **Complete Harvest** section, click the button of the same name.
3. Confirm the dialog — it explicitly warns that this step **cannot be undone**.

After confirming, the plant moves to its terminal "harvested" state: its phase history is closed, an occupied slot is freed, and the plant disappears from the active task queue. Existing harvest batches, quality assessments, and yield data are fully retained. Clicking the action again on an already-completed plant instead shows a notice that it is already completed and changes nothing further.

!!! danger "Cannot be undone"
    Unlike harvest batches or quality assessments, there is no correction or undo function for completing the harvest. Only use this action once you truly have no further partial harvests or observations planned for this plant.

Completing the harvest is different from **Remove Plant** on the plant detail page: "Complete Harvest" is the recommended path for an actually finished harvest and additionally records the harvest reason in the plant's history. "Remove Plant" remains available for all other cases (e.g. a plant that was not harvested but died or was given away).

!!! tip "Completing an entire planting run at once"
    If the plant belongs to a [Planting Run](planting-runs.md), you don't have to complete each plant individually: on the run's detail page, **Complete harvest** completes every still-active plant of the whole run in a single step. See [Completing a run's harvest](planting-runs.md#ernte-abschliessen) for details.

<!-- Source: src/frontend/src/pages/ernte/HarvestBatchDetailPage.tsx, src/frontend/src/pages/durchlaeufe/PlantingRunDetailPage.tsx, src/backend/app/domain/services/harvest_service.py (complete_harvest / complete_harvest_for_run), src/backend/app/api/v1/harvest/tenant_router.py -->

---

## Quality Assessment

Open the harvest batch and switch to the **Quality** tab to record an assessment.

| Field | Description |
|-------|-------------|
| Assessed By | Name of the person assessing |
| Appearance Score | 0–100 points |
| Aroma Score | 0–100 points |
| Colour Score | 0–100 points |
| Defects | Freely entered keywords |
| Notes | Additional remarks |

Kamerplanter automatically calculates an **overall score (0–100)** and a **grade**:

| Overall Score | Grade |
|----------------|-------|
| ≥ 90 | A+ |
| ≥ 75 | A |
| ≥ 55 | B |
| ≥ 35 | C |
| < 35 | D |

The overall score weights appearance (30 %), aroma (25 %), and colour (20 %) and subtracts points for recognised defects.

<!-- Source: src/backend/app/domain/engines/quality_scoring_engine.py -->

!!! tip "Defect keywords with score penalties"
    Some defect keywords are weighted particularly heavily by the system, including `mold` (−50), `hermaphrodite` (−40), `pests` (−30), `seeded` (−25). Others (`nutrient_burn`, `light_burn`: −15 each; `foxtailing`, `discoloration`: −10 each; `mechanical_damage`: −5) carry less weight. Unknown keywords are scored at a flat −5.

---

## Documenting Drying

For the actual drying, curing, and storage workflow — with start/target moisture, ongoing weight tracking, automatic progress and recommendations, and mold alerts — take the harvest batch into the dedicated **Post-Harvest** processing. The **Actual Dry Weight (g)** field in the harvest batch's Edit tab remains available alongside it for a quick, one-off retroactive entry.

More: [Post-Harvest](post-harvest.md)

For guidance on drying (target values for temperature, humidity, and duration), also see the post-harvest guide.

More: [Post-Harvest: Drying, Curing & Storage](../guides/post-harvest.md)

---

## Yield Metrics

Open the harvest batch and switch to the **Yield** tab to enter yield data manually:

| Field | Description |
|-------|-------------|
| Yield per Plant (g) | Total yield of this plant |
| Yield per m² (g) | Yield relative to the growing area |
| Total Yield (g) | Total weight of the batch |
| Trim Waste (%) | Share of trim waste in the total yield |
| Usable Yield (g) | Usable amount after trimming |

!!! note "Manual entry — no automatic calculation"
    Kamerplanter does not calculate these values itself from fresh/dry weight or growing area. You enter them yourself after weighing and processing. A comparison or analysis view across multiple batches and planting runs does not yet exist — the harvest batch overview only lists batches in a table.

---

## Pre-Harvest Protocols

### Flush Phase

Some growers perform a flush before harvest to wash excess salts from the substrate.

!!! note "Partially available"
    There is no button on the plant that starts a flush protocol or automatically creates watering tasks. Instead, Kamerplanter offers a standalone **flush calculator** among the nutrient calculators, which suggests a recommended flush duration based on substrate. You create the watering tasks during flushing manually as usual, or handle them through your existing watering routine.

!!! note "Flushing is scientifically disputed"
    Studies (e.g. University of Guelph, 2020) found no significant difference between flushed and unflushed plants. For living soil, flushing is explicitly not recommended as it damages the microbiome.

More on the flush calculator: [Fertilization](fertilization.md)

### Dark Period

Some growers maintain a dark period of 24–48 hours immediately before harvest.

!!! warning "Not yet implemented"
    A planned dark period with an automatic lighting task will be available in a future version. For now, note the lighting schedule yourself or create your own task under [Tasks](tasks.md).

---

## Frequently Asked Questions

??? question "Can I undo a harvest?"
    No. Harvest batches cannot be deleted after creation, as they are part of the complete growing documentation. You can, however, correct notes and weight values afterwards. The separate **Complete Harvest** step also cannot be undone — check before confirming that no further partial harvests are planned.

??? question "Does a plant automatically change status after a full harvest?"
    No. Creating a harvest batch with harvest type "full harvest" does not automatically change the plant's status. You have two ways to close it out: the harvest-specific **Complete Harvest** step on the harvest batch's detail page (see above), or [**Remove Plant**](growth-phases.md#pflanze-entfernen) on the plant's detail page, where you can optionally record that it was harvested. Both end the lifecycle permanently and irreversibly: the plant disappears from the active task queue and the occupied slot is freed; its master data and history are retained.

??? question "Why is the harvest blocked even though I haven't treated in a long time?"
    Check the **Pest Management** (IPM) tab for the full list of treatments and their pre-harvest intervals. Sometimes older treatments are still recorded with unexpired intervals. If a treatment was entered by mistake, you can correct it under Pest Management.

??? question "Can I perform a partial harvest multiple times?"
    Yes. You can create as many partial harvest batches for one plant as you like, e.g. to harvest the top buds first and the lower ones later.

??? question "Do I have to assign my own Batch ID for every batch?"
    No. If you leave the **Batch ID** field empty, Kamerplanter automatically assigns a unique ID — even when you create several batches for the same plant on the same day. A custom identifier is only needed if you want to follow a particular naming convention, e.g. for an external system.

---

## See Also

- [Pest Management (IPM)](pest-management.md)
- [Growth Phases](growth-phases.md)
- [Fertilization](fertilization.md)
- [Planting Runs](planting-runs.md)
- [Post-Harvest](post-harvest.md)
- [Post-Harvest: Drying, Curing & Storage](../guides/post-harvest.md)
