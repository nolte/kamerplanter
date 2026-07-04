# Fertilization

Kamerplanter calculates precise mixing ratios for nutrient solutions, monitors your EC budget, and reminds you of watering schedules. Whether you are running hydroponics with EC calculation or organic outdoor growing — the system supports both approaches.

---

## Prerequisites

- At least one fertilizer added under **Fertilization → Fertilizers**
- At least one plant with an active growth phase
- Recommended: water source configured on the site (for automatic EC calculation)

!!! info "Some calculators are only visible from a given experience level"
    Some of the calculator sections described below (Water Mixer, EC Budget Calculator, Delivery Channels) only appear from the **Intermediate** or **Expert** UI experience level upward. If you can't find a card or section, check your experience level under **Settings**.

---

## Understanding the Basics

### Electrical Conductivity (EC)

Electrical Conductivity (EC) measures the concentration of dissolved nutrients in the watering solution in millisiemens per centimetre (mS/cm). It is the most important indicator for nutrient dosing:

- **Too low**: Plant starves, deficiency symptoms possible
- **Optimal**: Best possible growth
- **Too high**: Salt stress, root damage, nutrient lockout

Typical EC target ranges that Kamerplanter validates your calculated final EC against:

<!-- Source: src/backend/app/domain/engines/ec_budget_engine.py EC_MAX_TABLE (REQ-004-A §4.2) -->

| Substrate | Seedling (mS/cm) | Vegetative (mS/cm) | Flowering (mS/cm) | Flushing (mS/cm) |
|-----------|------------------|--------------------|--------------------|-------------------|
| Hydroponics | 0.8 – 1.2 | 1.6 – 2.4 | 1.8 – 2.8 | 0.0 – 0.3 |
| Coco | 0.8 – 1.0 | 1.6 – 2.0 | 1.8 – 2.4 | 0.0 – 0.3 |
| Soil | 0.4 – 0.6 | 0.8 – 1.4 | 1.0 – 1.6 | 0.0 – 0.3 |

These values are identical to the table in the [Nutrient Mixing guide](../guides/nutrient-mixing.md#ec-target-substrate) — both are derived from the same source in the code so they cannot drift apart.

### EC Budget

The **EC budget** is the difference between the EC target for the current phase and the EC value of your source water. Kamerplanter distributes this budget across the individual fertilizer components.

**Example:**
- EC target for flowering: 1.8 mS/cm
- Tap water EC: 0.4 mS/cm
- EC budget for nutrients: 1.4 mS/cm

!!! tip "RO water has virtually no base EC"
    With pure reverse osmosis water (EC ≈ 0) the entire EC budget is available for nutrients. This gives more control but also more responsibility — especially regarding calcium and magnesium.

### Alkalinity and pH Reserve

In the **nutrient calculator** (**Fertilization → Nutrient Calculations → Mixing Protocol**) you now also enter your water's **alkalinity** (carbonate hardness, measured in ppm CaCO₃ — often listed on your water supplier's data sheet, or measurable yourself with a KH drop test). The higher the alkalinity, the more acid is later needed for pH correction.

From the alkalinity value, Kamerplanter calculates the **pH reserve** — the portion of your EC budget that stays reserved for the later pH correction and is therefore no longer available for nutrients:

| Alkalinity | Classification | pH Reserve |
|-----------|----------------|-----------|
| < 50 ppm | Soft | 0.02 mS/cm |
| 50–150 ppm | Medium | 0.03 mS/cm |
| > 150 ppm | Hard | 0.05 mS/cm |

After calculating, the mixing protocol shows you three transparent values:

- **Net EC budget** (`ec_net`): EC target minus base water EC — the headroom generally available for nutrients.
- **pH reserve** (`ec_ph_reserve`): the portion deducted from it for pH correction (see table above).
- **Recipe valid**: whether the calculated final EC stays within the upper limit for substrate and phase.

!!! note "Why calculated dosages are sometimes lower than before"
    Kamerplanter now correctly deducts the pH reserve from the available EC budget before calculating fertilizer dosages. Previously, this buffer was not accounted for, which meant the final EC after pH correction could slightly exceed the target. The new ml/L values are somewhat lower as a result, but more accurate — your nutrient solution now hits its EC target more reliably.

    Detailed explanation of the full calculation: [Nutrient Mixing](../guides/nutrient-mixing.md).

---

## Adding Fertilizers

### Step 1: Navigate to Fertilization

Click **Fertilization → Fertilizers** in the navigation.

### Step 2: Create a New Fertilizer

Click **Add Fertilizer**.

### Step 3: Enter Fertilizer Data

| Field | Description |
|-------|-------------|
| Name | Product name (e.g. "Canna Coco A") |
| Type | Base nutrient, supplement, booster, biological, **CalMag** |
| NPK Ratio | Nitrogen / phosphorus / potassium shares |
| EC Contribution | EC increase per ml/L (shown on label or data sheet) |
| Mixing Priority | Free number from 1–100. Lower number = mixed in earlier (default: 50) |
| Max. Dosage (ml/L) | Manufacturer upper limit; Kamerplanter caps the calculated dose and warns above it |
| Tank-Safe | Whether the fertilizer can be stored unchanged in a reservoir tank |
| Dosage (ml/L) | Standard dosage per litre of water |

!!! tip "Dedicated CalMag fertilizer type"
    Choose the **CalMag** type for pure calcium-magnesium supplements. Kamerplanter automatically places fertilizers of this type at the correct point in the mixing order (see below) and in the CalMag demand calculation.

#### Additional Fields for Organic Outdoor Fertilizers

For fertilizers intended for outdoor use (compost, horn shavings, plant teas) you also enter these fields — they are used for [area-based dosing](#area-based-dosing-calculation-nutrient-calculator):

| Field | Description |
|-------|-------------|
| Area Rate (g/m²) | Application rate in grams per square metre for solid fertilizers (e.g. horn shavings) |
| Area Rate (L/m²) | Application rate in litres per square metre for compost or liquid fertilizers |
| Dilution Ratio | For plant teas and slurries, e.g. "1:10" (1 part concentrate to 10 parts water) |
| Nutrient Release Speed | Immediate, weeks, months, or season-long — how quickly the nutrients become plant-available |

!!! danger "Mixing order matters — critical!"
    The order in which fertilizers are added to water is chemically significant. Incorrect mixing can cause precipitates that make nutrients unavailable. When calculating a mixing guide, Kamerplanter automatically sorts your selected fertilizers by their **Mixing Priority** (field above) — there is no order hard-coded in the code.

    **Recommended mixing-priority convention** (freely adjustable per fertilizer):
    1. Water at room temperature (18–22 °C)
    2. Silicon additives (if used)
    3. **CalMag** (always before sulfates!)
    4. Base A (calcium + micronutrients)
    5. Base B (phosphorus + sulfur + magnesium)
    6. Further supplements and boosters
    7. pH correction (pH Down / pH Up) — always last

    For this order to actually be followed, each fertilizer's mixing priority must be set accordingly (e.g. CalMag = 10, Base A = 20, Base B = 30). New fertilizers default to 50 — adjust it when creating a fertilizer if it needs to be mixed first or last.

---

## Fertilizer Stock, Incompatibilities, and Usage

The fertilizer detail page (**Fertilization → Fertilizers** → click a fertilizer) has three further areas:

### Stock (tab "Stock")

Here you record individual containers/purchases of this fertilizer:

| Field | Description |
|-------|-------------|
| Current Volume (ml) | Remaining amount in the bottle/canister |
| Purchase Date | When the container was bought |
| Expiry Date | Best-before date, if given |
| Batch Number | Manufacturer batch number |
| Cost/Liter (€) | For cost overview and average price |

Kamerplanter shows a summary (total volume, average cost/liter, entry count) and a warning when a container is due to expire within the next 30 days.

### Incompatibilities

If a fertilizer is marked incompatible with another one (e.g. CalMag with a sulfate supplement), the detail page shows a warning with reason and severity.

!!! info "Incompatibilities are currently API-only"
    Creating and removing incompatibility entries between two fertilizers is currently only possible via the REST API (`POST /fertilizers/{key}/incompatibilities`) — the UI only displays existing entries. If needed, ask your operator or note the combination in the fertilizer's free-text notes field.

### Usage in Nutrient Plans

The "Usage" section shows which nutrient plans use this fertilizer — as a Gantt chart across the phases of each plan. This lets you see at a glance in which plans and phases a fertilizer appears before you delete it or change its dosage.

---

## Creating a Nutrient Plan

A nutrient plan defines the dosages of all fertilizers for each growth phase. It is the centerpiece of the fertilization logic.

### Step 1: Create a New Nutrient Plan

Navigate to **Fertilization → Nutrient Plans** and click **New Plan**.

### Step 2: Name the Plan and Choose Substrate

Enter a name (e.g. "Tomatoes Raised Bed 2026") and select the substrate type (soil, coco, hydroponics). The substrate influences EC tolerance and CalMag recommendations.

### Step 3: Add Phase Entries

The new plan opens on the **Phase Entries** tab — it shows the phases as a Gantt timeline. For each growth phase add the fertilizer dosages:

1. Click **Add Phase**.
2. Select the phase (Germination, Vegetative, Flowering, etc.).
3. Enter the dosage in ml/L for each fertilizer.
4. The system instantly calculates total EC and shows whether the budget is met.

!!! warning "EC budget exceeded"
    If your entered dosages exceed the EC budget, a warning appears. Kamerplanter provides an adjustment suggestion where individual components are reduced proportionally.

### Step 4: Assign the Plan to a Planting Run

1. Open the desired **Planting Run** under **Runs** and switch to the **Fertilization & Watering** tab.
2. Click **Assign Nutrient Plan**.
3. Select the plan from the list.

All plants in this run will now use this plan for their watering recommendations.

---

## Delivery Channels (Multi-Channel Delivery) {#delivery-channels-multi-channel-delivery}

From the **Intermediate** experience level upward, you can define multiple **delivery channels** for a phase entry instead of a single dosage — for example an automatic fertigation channel through the drip tank plus an occasional foliar feed. Each channel has its own application method, its own fertilizer dosages, and optionally its own schedule.

### Creating a channel

1. Open the nutrient plan and click **Add Channel** on a phase entry.
2. Assign a **Channel ID** and choose the **application method**:

| Method | Meaning | Typical Parameters |
|--------|---------|---------------------|
| Fertigation | Automated dosing through a tank | Runs/day, pump duration (s), flow rate (ml/min), optional linked tank |
| Drench | Manual watering with a can or hose | Volume per feeding (L) |
| Foliar | Foliar feeding via the leaf surface | Volume per spray (L) |
| Top-Dress | Sprinkling solid fertilizer | Grams per plant, grams per m² |

3. Optionally enter a target EC and target pH for this channel.
4. If needed, enable a **dedicated watering schedule** for the channel (weekdays or interval, preferred time, reminder hours before) — without a dedicated schedule, the plan default applies.
5. Assign the desired fertilizers with ml/L dosages under **Fertilizers** (each can be marked "optional" if it may be omitted when needed).

### Channel validation

Kamerplanter checks the channels against the phase's EC budget and shows on the **Validation** tab whether all channels are valid or whether there are issues (including the tolerance range).

### Logging a watering from a channel

The **"Log watering for this channel"** button opens a pre-filled watering log entry (application method, target EC/pH, and fertilizer dosages are already populated) — see [Watering Log](watering-log.md).

!!! note "Existing single-fertilizer plans keep working"
    Plans without delivery channels continue to work unchanged (legacy mode). **"Convert to multi-channel"** lets you turn an existing phase entry into a standard delivery channel — this cannot be undone.

---

## Duplicating and Validating a Plan

- **Clone**: Click the copy icon in the nutrient plan list to create a copy of a plan under a new name — useful as a starting point for a variant of a proven plan.
- **Validate**: The **Validation** tab in the plan detail view automatically checks, as soon as you open it, whether the plan is complete (all phases covered) and whether the EC budgets per phase are respected.
- **Dosage Calculator**: The **Dosage Calculator** tab computes the exact amounts for this plan for a specific location or watering volume — handy for quickly determining the actual amount needed before mixing.

---

## Logging a Watering

After every watering or feeding session you document it in the **Watering Log**. This helps track actual nutrient delivery and substrate EC over time. See [Watering Log](watering-log.md) for the full field list, recording, and evaluation — here just the two entry points:

### Quick entry via the Planting Run

1. Open a **Planting Run** and switch to the **Fertilization & Watering** tab — it shows the upcoming watering dates from the watering schedule.
2. Click **Quick Confirm** on a date, or open **Confirm Watering** to adjust actual EC/pH and volume beforehand.

### Detailed entry

1. Open the **Watering Log** menu item (a dedicated top-level menu item, not under Fertilization).
2. Click **Log Watering**.
3. Select plant(s) and/or slots, application method, volume, and optionally fertilizers with dosages.
4. Optionally record EC/pH before and after, and runoff EC/pH (for runoff analysis).

!!! tip "Measuring runoff EC"
    For pot and coco grows, runoff EC (the water draining from the bottom of the pot) indicates salt accumulation in the substrate. If runoff EC is significantly higher than input EC, it is time for a flush.

---

## Calculating a Flush {#calculating-a-flush}

Before harvest a flush can help wash excess salts from the substrate. Kamerplanter provides a **calculator** for this — there is currently no button on the plant that "starts" a flush or automatically creates watering tasks.

!!! note "Scientific status"
    Flushing is widely practised among growers, but scientific evidence for improved taste is disputed. For living soil and organic growing it is explicitly not recommended as the microbiome is damaged.

### Using the calculator

1. Open **Fertilization → Nutrient Calculations** and the **Flushing** card.
2. Enter the current EC of your nutrient solution and the number of days until the planned harvest.
3. Click **Calculate**.

The result shows the recommended flush duration, the start day (today plus remaining days minus flush duration), and a day-by-day plan with target EC, action (e.g. "quarter-strength flush"), and dosage percentage — the final 40 % of the flush duration runs on plain water (0 mS/cm).

!!! info "Substrate is not currently selectable"
    The card currently has no substrate selector — the calculator assumes Coco server-side (flush duration 10–21 days). For hydroponics or soil, use the table below instead.

**Recommended flush duration by substrate:**

<!-- Source: src/backend/app/domain/engines/nutrient_engine.py FlushingProtocol.FLUSH_DURATIONS -->

| Substrate | Flush Duration |
|-----------|---------------|
| Hydroponics / clay pebbles / perlite / rockwool | 7–14 days |
| Coco | 10–21 days |
| Soil / Living Soil | 14–30 days |

!!! warning "Values differ from earlier statements"
    Earlier versions of this page listed 21–42 days for soil — that did not match the actual configured value. The table above is now consistent with the [Nutrient Mixing guide](../guides/nutrient-mixing.md#flush-substrate).

---

## Organic Outdoor Fertilization

For outdoor gardens with soil, raised-bed mix, or living soil Kamerplanter recommends area-based organic fertilization rather than EC calculation.

### Fertilizer Categories Outdoors

| Category | Typical Products | When to Apply |
|----------|-----------------|---------------|
| Compost | Mature compost | Spring (2–4 L/m²) |
| Horn products | Horn shavings, horn meal | Spring / summer |
| Plant teas | Nettle tea, comfrey tea | May–August |
| Mineral amendments | Rock dust, algae lime | Spring |

### Recommendation by Nutrient Demand

Kamerplanter shows the nutrient demand of the plant (from master data) in the plant detail view and provides a recommendation:

| Nutrient Demand | Example Plants | Recommendation |
|----------------|----------------|---------------|
| Heavy feeder | Tomato, courgette, cabbage | Compost 3–4 L/m² + horn shavings 80 g/m² |
| Medium feeder | Carrot, lettuce, fennel | Compost 2–3 L/m² + horn shavings 40 g/m² |
| Light feeder | Herbs, beans, peas | Compost 1–2 L/m², no further fertilizer |
| Nitrogen fixer | Beans, peas, lupins | No N fertilizer! Only P and K if needed |

!!! warning "Do not fertilize nitrogen fixers with nitrogen"
    Legumes such as beans and peas fix nitrogen from the air themselves. Applying nitrogen fertilizer does more harm than good and suppresses natural N fixation.

#### Area-Based Dosing Calculation (Nutrient Calculator) {#area-based-dosing-calculation-nutrient-calculator}

Instead of deriving dosages by hand from the tables above, let Kamerplanter calculate them precisely:

1. Open **Fertilization → Nutrient Calculations** and select the **Area Dosing (Outdoor)** card.
2. Enter the keys of the desired fertilizers (comma-separated), e.g. compost and horn shavings.
3. Either enter the **bed area in m²** directly, or enter a **location** instead. If an area is entered, it takes precedence — the location is then ignored. If the area field is left empty, Kamerplanter uses the area stored for the selected location.
4. Optionally select the plant's **nutrient demand** (heavy/medium/light feeder, nitrogen fixer) — this provides additional guidance but does not replace the amount calculation itself.
5. Click **Calculate**.

The result shows, per fertilizer, the total amount in grams or litres for the given area, the stored dilution ratio, the nutrient release speed, and additional notes.

!!! tip "Area comes from the location or is entered manually"
    If you have already stored a bed size under **Locations → Sites**, you can leave the area field empty and enter the location key instead — the area is picked up automatically.

---

## CalMag: When and How Much?

CalMag supplements (calcium-magnesium supplements, commonly abbreviated CalMag) are important with soft tap water and reverse osmosis water, since these lack natural minerals.

Kamerplanter calculates CalMag requirements automatically when you have entered the water source on your site:

- **100 % RO water**: Full CalMag supplement (~0.5–1.5 ml/L depending on phase)
- **50/50 mix (RO + tap)**: Half CalMag amount
- **Hard tap water** (EC > 0.5 mS/cm): Often no CalMag needed

---

## Water Mixer and EC Budget Calculator {#water-mixer-and-ec-budget-calculator}

Under **Fertilization → Nutrient Calculations** you find, next to the mixing protocol and area dosing, two further cards that appear depending on your experience level:

### Water Mixer (from Intermediate)

Enter your tap water's EC, its alkalinity, and your desired target EC for the blended water, and the Water Mixer calculates in reverse the **RO water percentage** needed to reach exactly that target EC — along with the resulting effective water EC.

### EC Budget Calculator (from Expert)

The EC Budget Calculator is the most detailed variant of the mixing protocol. In addition to target EC, substrate, phase, and volume, you can pre-deduct CalMag and silicate fertilizers with a fixed dose, and specify the number of substrate cycles already used (for the automatic coco CalMag boost). You can also enter a **measured EC value together with the water temperature**.

!!! tip "EC temperature correction (EC@25)"
    Electrical conductivity depends on water temperature — the same nutrient solution shows a higher EC at 30 °C than at 20 °C. If you enter your measured EC value **and** the water temperature in the EC Budget Calculator, Kamerplanter automatically converts it to the 25 °C reference temperature (`EC@25 = EC_measured / (1 + 0.02 × (T − 25))`) and shows this corrected value in the result. This keeps measurements taken at different temperatures comparable.

The result shows a colored EC-budget bar (base water/silicate/CalMag/fertilizers/pH reserve), warnings, a dosage table, and a numbered mixing guide — identical calculation logic to the mixing protocol, just with more input options.

---

## Frequently Asked Questions

??? question "What is the difference between a nutrient plan and a watering log entry?"
    A **nutrient plan** is the recipe — it defines which fertilizers to use in which amounts for each phase. A **watering log entry** is the record of an actual watering or fertilization session. One is planning, the other is documentation — see the [Watering Log](watering-log.md) for details.

??? question "Do I have to record every watering?"
    No, it is optional. Kamerplanter works without complete feeding documentation. If you want to track runoff EC or optimize nutrient delivery, thorough recording pays off.

??? question "Why does the system suggest CalMag when I have hard water?"
    When coco coir is set as the substrate, Kamerplanter always recommends CalMag — regardless of water hardness. Coco coir actively binds calcium and magnesium, so the demand is higher than with soil.

??? question "Can I reuse an existing nutrient plan for new planting runs?"
    Yes. When assigning a plan to a planting run you choose from all existing plans. This lets you apply a proven plan to multiple runs.

??? question "Why is my calculated dosage in the mixing protocol now lower than before?"
    Kamerplanter now correctly deducts the pH reserve from the EC budget before calculating fertilizer dosages. This reserve was previously not accounted for, which meant the actual final EC after pH correction could slightly exceed the target. The new, somewhat lower ml/L values hit your EC target more reliably.

??? question "What is alkalinity and where do I find the value for my water?"
    Alkalinity (also called carbonate hardness or KH) describes how strongly your water resists a change in pH — measured in ppm CaCO₃. You can often find the value on your local water supplier's data sheet, or measure it yourself with a KH drop test from an aquarium supply shop. Tap water typically ranges between 50 and 250 ppm.

??? question "Can I set both g/m² and L/m² for one outdoor fertilizer?"
    Yes. Both fields are independent and optional — use g/m² for solids (e.g. horn shavings) and L/m² for liquid or compost fertilizers. The area dosing calculator automatically uses whichever field is set for each fertilizer.

---

## See Also

- [My Plant Doesn't Look Well — Symptom Diagnosis](plant-health-troubleshooting.md)
- [Watering Log](watering-log.md)
- [Tank Management](tanks.md)
- [Growth Phases](growth-phases.md)
- [Guides: Mixing Nutrient Solutions](../guides/nutrient-mixing.md)
- [Guides: VPD Optimization](../guides/vpd-optimization.md)
