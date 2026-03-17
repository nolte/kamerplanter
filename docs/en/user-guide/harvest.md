# Harvest Management

Harvest management guides you from recognising harvest maturity through documenting the harvest batch to quality assessment. An integrated safety system automatically checks whether active pest control treatments block the harvest.

---

## Prerequisites

- At least one plant in the "Harvest" phase or approaching it (flowering phase)
- All active pest control treatments must have completed their pre-harvest interval

---

## Recognising Harvest Maturity

Kamerplanter shows a maturity forecast for each plant based on days spent in the flowering phase and Growing Degree Days (GDD). This forecast is a guideline — the actual decision is yours as the grower.

### Maturity Indicators by Plant Type

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

## Pre-Harvest Interval Check (IPM Safety Gate)

!!! danger "Harvest blocked during active treatment"
    If a pest control treatment is still within its pre-harvest interval (PHI), Kamerplanter blocks harvest batch creation. You will see a clear error message with the date from which harvesting is possible.

The pre-harvest interval is the minimum waiting period after applying a plant protection product before the plant may be harvested. These intervals are legally regulated and stored in Kamerplanter per treatment agent.

**Example:** You applied a product with a 14-day PHI on 1 March. The earliest possible harvest date is 15 March. If you try to create a harvest batch on 10 March, an error message appears.

More on pre-harvest intervals: [Integrated Pest Management (IPM)](pest-management.md)

---

## Creating a Harvest Batch

### Step 1: Start the Harvest

1. Open the plant or planting run under **Plants** or **Runs**.
2. Click **Start Harvest** or **Create Harvest Batch**.
3. The system automatically checks all pre-harvest intervals. If a treatment is still within its interval, a message appears.

### Step 2: Enter Harvest Details

| Field | Description |
|-------|-------------|
| Harvest Date | Date of harvest (default: today) |
| Harvest Method | Full harvest or partial harvest |
| Fresh Weight (g) | Weight of the harvest directly after cutting |
| Harvest Type | Flower, fruit, leaf, root, seed |
| Notes | Observations, anything unusual |

**Harvest methods:**
- **Full harvest**: The entire plant is harvested. The plant moves to "Completed" status afterwards.
- **Partial harvest** (staggered): Only part is harvested (e.g. top buds first). The plant remains active for further harvests.

### Step 3: Quality Assessment (optional)

Enter an optional quality rating:

| Rating | Description |
|--------|-------------|
| A+ | Exceptional quality |
| A | High quality, no defects |
| B | Good quality, minor defects |
| C | Acceptable quality, notable defects |

Additional fields (depending on plant type):
- Aroma intensity (1–10)
- Visual rating (1–10)
- Remarks (e.g. "No pest damage", "Slight botrytis on one branch tip")

---

## Documenting the Drying Phase

After harvest, many crops (e.g. herbs, cannabis) go through a drying phase. You can track this in Kamerplanter:

1. Open the harvest batch under **Harvest**.
2. Click **Start Drying Phase**.
3. Enter start weight, target moisture, and storage conditions.
4. Regularly record the current dry weight — Kamerplanter calculates drying progress.

**Optimal drying conditions (guidelines for herbs and cannabis):**
- Temperature: 18–22 °C
- Humidity: 45–55 % rH
- Duration: 7–14 days

---

## Yield Metrics and Analysis

After completing a harvest batch, Kamerplanter calculates automatically:

- **Dry weight** (after entering the final weight)
- **Drying loss** (% weight loss through drying)
- **Yield per m²** (g/m², based on growing area)
- **Yield per plant** (g/plant)
- **Yield per day in the flowering phase**

These metrics help you improve your growing technique across multiple cycles.

!!! tip "Compare metrics"
    In the harvest overview you can compare batches. This shows which planting run, substrate, or nutrient plan delivered the best yield.

---

## Pre-Harvest Protocols

### Flush Phase

Some growers perform a flush before harvest to wash excess salts from the substrate. Kamerplanter offers this protocol as an option.

!!! note "Flushing is scientifically disputed"
    Studies (e.g. University of Guelph, 2020) found no significant difference between flushed and unflushed plants. For living soil, flushing is explicitly not recommended as it damages the microbiome.

1. Open the plant.
2. Click **Start Flush Protocol**.
3. The system recommends a flush duration based on substrate.
4. During flushing you receive watering tasks with plain pH-adjusted water.

More on flush protocols: [Fertilization](fertilization.md)

### Dark Period

Some growers maintain a dark period of 24–48 hours immediately before harvest. Kamerplanter can remind you:

1. Open the planting run.
2. Click **Plan Dark Period**.
3. Choose date and duration.
4. A task is created: "Turn off lighting — dark period begins".

---

## Frequently Asked Questions

??? question "Can I undo a harvest?"
    No. Harvest batches cannot be deleted after creation, as they are part of the complete growing documentation. You can, however, correct notes and weight values afterwards.

??? question "What happens to a plant after a full harvest?"
    The plant automatically moves to "Completed" status. It is no longer active and no longer appears in the task queue. Master data and phase history are retained for analysis.

??? question "Why is the harvest blocked even though I haven't treated in a long time?"
    Check the **Pest Management** (IPM) tab for the full list of treatments and their pre-harvest intervals. Sometimes older treatments are still recorded with unexpired intervals. If a treatment was entered by mistake, you can correct it under Pest Management.

??? question "Can I perform a partial harvest multiple times?"
    Yes. For staggered harvests you can create any number of partial harvest batches for one plant until you complete the full harvest or manually mark the plant as complete.

---

## See Also

- [Pest Management (IPM)](pest-management.md)
- [Growth Phases](growth-phases.md)
- [Fertilization](fertilization.md)
- [Planting Runs](planting-runs.md)
