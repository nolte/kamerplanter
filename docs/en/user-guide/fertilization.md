# Fertilization

Kamerplanter calculates precise mixing ratios for nutrient solutions, monitors your EC budget, and reminds you of watering schedules. Whether you are running hydroponics with EC calculation or organic outdoor growing — the system supports both approaches.

---

## Prerequisites

- At least one fertilizer added under **Fertilization → Fertilizers**
- At least one plant with an active growth phase
- Recommended: water source configured on the site (for automatic EC calculation)

---

## Understanding the Basics

### Electrical Conductivity (EC)

Electrical Conductivity (EC) measures the concentration of dissolved nutrients in the watering solution in millisiemens per centimetre (mS/cm). It is the most important indicator for nutrient dosing:

- **Too low**: Plant starves, deficiency symptoms possible
- **Optimal**: Best possible growth
- **Too high**: Salt stress, root damage, nutrient lockout

Typical EC targets:

| Phase | Hydroponics / Coco | Soil |
|-------|-------------------|------|
| Seedling | 0.4–0.8 mS/cm | 0.4–0.6 mS/cm |
| Vegetative | 1.2–1.8 mS/cm | 0.8–1.2 mS/cm |
| Flowering | 1.6–2.2 mS/cm | 1.0–1.4 mS/cm |
| Late Flowering | 0.6–1.0 mS/cm | — |

### EC Budget

The **EC budget** is the difference between the EC target for the current phase and the EC value of your source water. Kamerplanter distributes this budget across the individual fertilizer components.

**Example:**
- EC target for flowering: 1.8 mS/cm
- Tap water EC: 0.4 mS/cm
- EC budget for nutrients: 1.4 mS/cm

!!! tip "RO water has virtually no base EC"
    With pure reverse osmosis water (EC ≈ 0) the entire EC budget is available for nutrients. This gives more control but also more responsibility — especially regarding calcium and magnesium.

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
| Type | Base nutrient, supplement, booster, biological |
| NPK Ratio | Nitrogen / phosphorus / potassium shares |
| EC Contribution | EC increase per ml/L (shown on label or data sheet) |
| Mixing Priority | Order when mixing (lower number = added first) |
| Dosage (ml/L) | Standard dosage per litre of water |

!!! danger "Mixing order matters — critical!"
    The order in which fertilizers are added to water is chemically significant. Incorrect mixing can cause precipitates that make nutrients unavailable. Kamerplanter enforces the correct order automatically.

    **Correct mixing sequence:**
    1. Water at room temperature (18–22 °C)
    2. Silicon additives (if used)
    3. **CalMag** (always before sulphates!)
    4. Base A (calcium + micronutrients)
    5. Base B (phosphorus + sulphur + magnesium)
    6. Further supplements and boosters
    7. pH correction (pH Down / pH Up) — always last

---

## Creating a Nutrient Plan

A nutrient plan defines the dosages of all fertilizers for each growth phase. It is the centrepiece of the fertilization logic.

### Step 1: Create a New Nutrient Plan

Navigate to **Fertilization → Nutrient Plans** and click **New Plan**.

### Step 2: Name the Plan and Choose Substrate

Enter a name (e.g. "Tomatoes Raised Bed 2026") and select the substrate type (soil, coco, hydroponics). The substrate influences EC tolerance and CalMag recommendations.

### Step 3: Add Phase Entries

For each growth phase add the fertilizer dosages:

1. Click **Add Phase**.
2. Select the phase (Germination, Vegetative, Flowering, etc.).
3. Enter the dosage in ml/L for each fertilizer.
4. The system instantly calculates total EC and shows whether the budget is met.

!!! warning "EC budget exceeded"
    If your entered dosages exceed the EC budget, a warning appears. Kamerplanter provides an adjustment suggestion where individual components are reduced proportionally.

### Step 4: Assign the Plan to a Planting Run

1. Open the desired **Planting Run** under **Runs**.
2. Click **Assign Nutrient Plan**.
3. Select the plan from the list.

All plants in this run will now use this plan for their watering recommendations.

---

## Recording a Feeding Event

After every watering session you document a feeding event. This helps track actual nutrient delivery and substrate EC over time.

### Quick entry via the Planting Run

1. Open a **Planting Run**.
2. Click **Confirm Watering** (or **Quick Water**).
3. Confirm the suggested amount and EC — or adjust them.

### Detailed entry

1. Navigate to **Fertilization → Feeding Events**.
2. Click **New Event**.
3. Select plant(s) or planting run.
4. Enter the amounts actually used.
5. Optionally record actual EC in, pH, and runoff EC (for runoff analysis).

!!! tip "Measuring runoff EC"
    For pot and coco grows, runoff EC (the water draining from the bottom of the pot) indicates salt accumulation in the substrate. If runoff EC is significantly higher than input EC, it is time for a flush.

---

## Flush Protocol

Before harvest a flush can help wash excess salts from the substrate. Kamerplanter guides you through this process.

!!! note "Scientific status"
    Flushing is widely practised among growers, but scientific evidence for improved taste is disputed. For living soil and organic growing it is explicitly not recommended as the microbiome is damaged.

1. Open the plant and click **Start Flush Protocol**.
2. The system suggests a duration based on substrate type.
3. During flushing switch to plain pH-adjusted water.
4. Kamerplanter creates watering tasks automatically for the flush period.

**Recommended flush duration (guidelines):**

| Substrate | Flush Duration |
|-----------|---------------|
| Hydroponics | 7–14 days |
| Coco | 10–21 days |
| Soil | 21–42 days |
| Living Soil | Flushing not recommended |

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

---

## CalMag: When and How Much?

CalMag supplements (calcium-magnesium) are important with soft tap water and reverse osmosis water, since these lack natural minerals.

Kamerplanter calculates CalMag requirements automatically when you have entered the water source on your site:

- **100 % RO water**: Full CalMag supplement (~0.5–1.5 ml/L depending on phase)
- **50/50 mix (RO + tap)**: Half CalMag amount
- **Hard tap water** (EC > 0.5 mS/cm): Often no CalMag needed

---

## Frequently Asked Questions

??? question "What is the difference between a nutrient plan and a feeding event?"
    A **nutrient plan** is the recipe — it defines which fertilizers to use in which amounts for each phase. A **feeding event** is the record of an actual fertilization session. One is planning, the other is documentation.

??? question "Do I have to record every watering?"
    No, it is optional. Kamerplanter works without complete feeding documentation. If you want to track runoff EC or optimise nutrient delivery, thorough recording pays off.

??? question "Why does the system suggest CalMag when I have hard water?"
    When coco coir is set as the substrate, Kamerplanter always recommends CalMag — regardless of water hardness. Coco coir actively binds calcium and magnesium, so the demand is higher than with soil.

??? question "Can I reuse an existing nutrient plan for new planting runs?"
    Yes. When assigning a plan to a planting run you choose from all existing plans. This lets you apply a proven plan to multiple runs.

---

## See Also

- [Tank Management](tanks.md)
- [Growth Phases](growth-phases.md)
- [Guides: Mixing Nutrient Solutions](../guides/nutrient-mixing.md)
- [Guides: VPD Optimisation](../guides/vpd-optimization.md)
