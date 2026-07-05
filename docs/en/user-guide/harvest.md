# Harvest Management

Harvest management guides you from observing harvest maturity through documenting the harvest batch to quality assessment and yield metrics. An integrated safety system automatically checks whether active pest control treatments block the harvest.

---

## Prerequisites

- At least one plant in the flowering phase or approaching harvest
- All active pest control treatments must have completed their pre-harvest interval

---

## Recognising Harvest Maturity

### Expected Harvest Date

For plants with a harvest phase, Kamerplanter shows an **expected harvest date** on the plant detail page. It is calculated from the planting date plus the sum of the planned phase durations (growth phase management) and additionally shows the remaining days or an overdue indicator. For perennial plants or species without a defined harvest phase, no date appears — here you rely entirely on on-site observation.

!!! info "Maturity observation system — API only"
    Kamerplanter also provides a data model for plant-specific ripeness indicators (trichomes, brix, foliage die-back, colour, and others) with individual observations and a weighted readiness score. This system is fully usable via the API but is not yet wired up to a frontend surface — you cannot currently operate it through menus. Until it is connected, use the manual maturity indicators below.

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
| Batch ID | Optional custom identifier, e.g. "HARVEST-2026-001" |
| Harvest Type | **Partial harvest**, **Full harvest**, or **Continuous** |
| Harvest Date | Date and time of harvest (default: now) |
| Fresh Weight (g) | Weight of the harvest directly after cutting |
| Harvester | Who performed the harvest? |
| Notes | Observations, anything unusual |

**Harvest types:**

- **Full harvest**: The entire plant is harvested at once.
- **Partial harvest**: Only part is harvested (e.g. top buds first). You can create as many partial harvest batches for the same plant as you like.
- **Continuous**: For "cut and come again" crops (e.g. cut lettuce, basil) where small amounts are harvested continuously.

!!! note "No automatic status or quality change"
    Neither the harvest type selection nor creating a batch automatically changes the plant's status — not even for "full harvest". A quality assessment is also not requested when creating the batch; it happens separately (see below).

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

!!! note "Partially available"
    Kamerplanter currently only offers a single field, **Actual Dry Weight (g)**, in the Edit tab of the harvest batch — you enter it manually once drying is complete. A dedicated drying workflow interface with start/target moisture, ongoing weight tracking, and automatic progress or drying-loss calculation is specified as a planned feature but not yet built. <!-- REQ-008 -->

For guidance on drying (target values for temperature, humidity, and duration), see the post-harvest guide.

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
    No. Harvest batches cannot be deleted after creation, as they are part of the complete growing documentation. You can, however, correct notes and weight values afterwards.

??? question "Does a plant automatically change status after a full harvest?"
    No. Creating a harvest batch with harvest type "full harvest" does not automatically change the plant's status. If the plant is done for you, remove it manually via [**Remove Plant**](growth-phases.md#pflanze-entfernen) on its detail page — you can optionally record that it was harvested. Only then does it disappear from the active task queue; its master data and history are retained.

??? question "Why is the harvest blocked even though I haven't treated in a long time?"
    Check the **Pest Management** (IPM) tab for the full list of treatments and their pre-harvest intervals. Sometimes older treatments are still recorded with unexpired intervals. If a treatment was entered by mistake, you can correct it under Pest Management.

??? question "Can I perform a partial harvest multiple times?"
    Yes. You can create as many partial harvest batches for one plant as you like, e.g. to harvest the top buds first and the lower ones later.

---

## See Also

- [Pest Management (IPM)](pest-management.md)
- [Growth Phases](growth-phases.md)
- [Fertilization](fertilization.md)
- [Planting Runs](planting-runs.md)
- [Post-Harvest: Drying, Curing & Storage](../guides/post-harvest.md)
