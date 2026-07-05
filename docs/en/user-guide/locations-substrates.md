# Locations and Substrates

Locations describe where your plants grow — from your entire garden down to a single pot slot. Substrates define the growing medium. Both concepts form the spatial foundation for all other features in Kamerplanter.

---

## Prerequisites

- A Kamerplanter account with at least one tenant (created automatically during onboarding)
- For substrates: at least one location already set up

---

## Understanding the Location Hierarchy

Kamerplanter organises locations in a tree structure with three levels:

```
Site (facility)
  └── Location (area)
        └── Slot (plant spot)
```

**Site** is your top-level facility — for example "My Garden" or "Berlin Apartment". At the site level you store the water source, climate zone, and total area.

**Location** is a concrete area within a site — for example "Grow Tent A", "Raised Bed 1", or "South Balcony". Locations can contain further locations: you can model "House" → "Living Room" → "South Window Sill".

**Slot** is a single planting spot — for example "TENT01_A1" for spot A1 in grow tent 1. Slots are always the bottom level and can be assigned to exactly one plant.

!!! tip "How deep should the structure be?"
    For simple setups (balcony, one grow tent) it is sufficient to create sites and locations. Slots are useful when you have many plants in the same area and want to track each spot individually.

---

## Creating a New Site

### Step 1: Navigate to Location Management

Click **Locations** in the left navigation. The overview page shows all your sites.

### Step 2: Create a New Site

Click **Add Site** (top right). A form opens.

### Step 3: Fill in Basic Data

| Field | Description | Example |
|-------|-------------|---------|
| Name | Site name | "My Indoor Garden" |
| Climate Zone | Location climate zone in USDA hardiness-zone format | "8a" |
| Total Area (m²) | Total growing area | 12 |
| Timezone | Timezone for tasks and calendar | "Europe/Berlin" |

!!! info "Why USDA zones and not Köppen climate classification?"
    Kamerplanter expects the climate zone in **USDA Plant Hardiness Zone** format (a number from 1–13, optionally with an "a" or "b" suffix, e.g. "8a"), not the Köppen climate classification (e.g. "Cfb"). The reason: the hardiness data for plant species in the master data (`hardiness_zones`) uses the same format — this is what later allows Kamerplanter to check automatically whether a species can overwinter outdoors at your location. You can look up the matching zone for your area via the official [USDA Plant Hardiness Zone Map](https://planthardiness.ars.usda.gov/) or comparable hardiness zone maps for your region.

!!! note "Experience levels"
    Depending on your experience level (Beginner / Intermediate / Expert, configurable in account settings) you will see more or fewer fields. Experts see additional fields for water source configuration, GPS coordinates, and frost dates.

### Step 4: Configure Water Source (optional, Intermediate and above)

If you use tap water or a reverse osmosis system, enter the water values. The system will automatically calculate your EC budget (EC = electrical conductivity, a measure of the nutrient-salt concentration of your solution — see [Fertilization](fertilization.md) for details), CalMag requirements, and mixing recommendations.

#### Tap Water Profile

| Field | Unit | Typical Range | Description |
|-------|------|--------------|-------------|
| EC | mS/cm | 0.3–0.8 | Electrical conductivity — indicates total mineral content |
| pH | — | 7.0–8.0 | Acidity of the water |
| General Hardness (GH) | ppm CaCO3 | 100–350 | Sum of dissolved minerals (Ca + Mg) |
| Carbonate Hardness (KH) | ppm CaCO3 | 80–250 | Buffer capacity of the water (Alkalinity) |
| Calcium (Ca) | mg/L | 30–120 | Important for CalMag calculation |
| Magnesium (Mg) | mg/L | 5–30 | Important for CalMag calculation |
| Chlorine | mg/L | 0–0.3 | At > 0.1 mg/L, let water stand or filter |
| Chloramine | mg/L | 0 | Rarely used in Europe |

#### Additional Options

- **Has RO system**: Enable this if you have a reverse osmosis unit. The system will then calculate mixing ratios for tap and RO water.
- **Measurement date**: Date of the water analysis. Kamerplanter warns you if the analysis is older than 12 months.
- **Source note**: Free text for the origin of the values (e.g. "City Water Report 2025").

!!! tip "Finding your water values"
    Your local water utility typically provides a free drinking water analysis — often as a PDF download on their website. In many countries, water suppliers are legally required to publish these values.

    **Examples (Germany):**

    - **Hamburg**: [hamburgwasser.de/wasser](https://www.hamburgwasser.de/wasser) — postal code lookup under "Mein Trinkwasser"
    - **Berlin**: berliner-wasserbetriebe.de — water quality by postal code
    - **Munich**: swm.de — drinking water analysis by supply area

    Alternatively, you can measure the values yourself: an EC/TDS meter (TDS = Total Dissolved Solids; from approx. 15 EUR) provides the EC value, a pH meter the pH. For calcium and magnesium, drop tests (GH/KH test kits from aquarium supplies, from approx. 8 EUR) are an affordable option.

!!! warning "Why accurate water values matter"
    Kamerplanter uses your water values to calculate the **EC budget** (how much room is left for fertilizer) and the **CalMag correction** (whether additional calcium/magnesium is needed). Inaccurate values lead to wrong fertilization recommendations — in the worst case, over- or under-fertilization.

### Step 5: Save

Click **Save**. The site appears in the overview.

!!! info "For technical users"
    Besides name, climate zone, area, and timezone, a site also tracks GPS coordinates and average frost dates (last spring frost, first autumn frost, and the German "Eisheilige" date) in the background. This setting is currently only available via the API — it is not yet editable in the site form. The benefit: once a site has a GPS position, Kamerplanter can calculate the actual day length at your location and correctly evaluate automatic, photoperiod-triggered phase transitions (e.g. flower onset for outdoor short-day plants) — see [Automatic Phase Transitions](growth-phases.md#automatic-phase-transitions). Frost dates also feed into the sowing calendar.

!!! tip "GPS coordinates unlock weather sources"
    For sites of type Outdoor or Greenhouse, a stored GPS position also unlocks the **Weather Source** section on the site detail page — there you select and prioritize public weather services or a Home Assistant source, see [Weather Sources per Location](weather-sources.md).

---

## Adding Locations and Slots

### Adding a Location Within a Site

1. Open a site by clicking its name.
2. In the **Locations** tab you see the location tree.
3. Click **Add Location**.
4. Select a **location type** from the list (see table below).
5. Enter a unique name.
6. Optional: Select a parent location (for nested structures).

**Available Location Types:**

<!-- Source: src/backend/app/migrations/seed_data/location_types.yaml -->

| Type | Indoor? | Description |
|------|:---:|-------------|
| Zone | — | Free-form subdivision without a fixed assignment, e.g. for rough area planning |
| Home | No | Top level for a private residence |
| Garden | No | The entire outdoor area |
| Greenhouse | No | Glass house or poly tunnel |
| Building | Yes | A building as an area, e.g. an outbuilding or shed |
| Room | Yes | A whole room as an area |
| Balcony | No | Balcony |
| Terrace | No | Terrace |
| Grow Tent | Yes | Enclosed grow tent with controlled climate |
| Bed | No | Ground-level or raised bed outdoors |
| Shelf | Yes | Shelf or shelving unit |
| Container Group | No | Grouping of several pots or containers in one place |

!!! info "For technical users"
    The twelve types listed above are pre-installed system types. Kamerplanter already supports custom, additional location types internally. This setting is currently only available via the API — there is no dedicated management page for it in the UI yet.

### Adding a Slot Within a Location

1. Open a location by clicking its name in the tree.
2. Click **Add Slot**.
3. Kamerplanter automatically suggests a **slot ID** in the format `AREA_POSITION` (e.g. "TENT01_A1"); you can adjust it, and it is automatically converted to uppercase on save.
4. Enter the **capacity** — the maximum number of plants this slot can hold at once (1–20, default: 1).

---

## Managing Substrates

A substrate describes the growing medium in which your plants root. Kamerplanter distinguishes between 14 substrate types, supports custom substrate mixes, and manages concrete **batches** of a substrate (e.g. "Organic soil, mixed March 2026") separately from the general substrate type.

### Creating a New Substrate

1. Navigate to **Locations → Substrates**.
2. Click **Add Substrate**.
3. Select the **substrate type** (see table).
4. Enter a name (German and English, e.g. "Organic Soil" / "Bio-Erde").
5. Optional: Enter base pH, base EC, water retention, air porosity, and buffer capacity.

**Available Substrate Types:**

<!-- Source: src/backend/app/common/enums.py (SubstrateType) -->

| Type | Description |
|------|-------------|
| Soil | Standard garden or potting soil |
| Coco | Coconut substrate (coco coir) |
| Clay Pebbles | Expanded clay pellets, mostly used in hydro systems |
| Perlite | Volcanic mineral, usually added for drainage |
| Living Soil | Soil with an active microbiome |
| Peat | Peat-based substrate |
| Rockwool Slab | Mineral wool slab for hydroponics |
| Rockwool Plug | Small mineral wool propagation cube for cuttings and germination |
| Vermiculite | Expanded mineral, usually added or used for propagation |
| No Substrate | For substrate-less systems (e.g. pure aeroponics) |
| Orchid Bark | Coarse bark chunks for epiphytes |
| PON Mineral Substrate | Mineral semi-hydro substrate (LECA-like) |
| Sphagnum Moss | Peat moss, commonly used for orchids and carnivorous plants |
| Hydro Solution | Pure nutrient solution with no solid substrate (e.g. DWC) |

!!! warning "Coco and CalMag"
    Coco substrate actively binds calcium and magnesium. CalMag supplements are always recommended for coco substrates, even with hard tap water. Kamerplanter will warn you if a nutrient plan for coco plants contains no CalMag.

### Creating Custom Substrate Mixes

Instead of using a single substrate type, you can combine several existing substrates into a custom mix (e.g. 70% soil + 20% perlite + 10% vermiculite):

1. Click **Create Mix** in the substrate overview.
2. Select at least two existing substrates (pure mixes cannot themselves be mixed again).
3. Distribute the shares in percent — **Distribute Evenly** splits them automatically. The total must add up to exactly 100%.
4. Click **Preview** to see the mix's calculated properties (base pH, base EC, water retention, air porosity, etc. — each as a weighted average of the components).
5. Enter a name (German/English) and click **Save**.

### Substrate Batches (Reuse, Assignment)

A **batch** is a concrete, physical quantity of a substrate with its own history — for example, a specific bag of soil reused across several growing cycles. For each batch, Kamerplanter tracks:

| Field | Description |
|-------|-------------|
| Batch ID | Freely chosen label, e.g. "SOIL-2026-03" |
| Volume (litres) | Amount of this batch |
| Mixed on | Date of preparation/purchase |
| Last amended | Date of the last nutrient/pH refresh |
| Cycles used | How many growing cycles this batch has already been used for |
| Current pH / EC | Latest measured values, including history |

**Preparing for reuse:** After completing a growing cycle, check whether a batch can be used again:

1. Open the substrate batch in the detail view.
2. Click **Check Reusability**. The system compares the batch's history against the substrate type's allowed reuse cycles.
3. If preparation is needed, Kamerplanter shows the required steps (e.g. flushing, re-fertilizing) along with an estimated duration and the earliest date the batch will be ready again.
4. Click **Prepare for Reuse** to log the preparation step.

!!! info "For technical users"
    Kamerplanter can already technically link a substrate batch to a slot. This setting is currently only available via the API — there is no UI for this yet. Until then, enter the substrate reference in the **Substrate Batch** field when creating a planting run (see [Planting Runs](planting-runs.md)).

---

## Tips for Location Structure

!!! example "Example: Balcony gardener"
    - Site: "Berlin Apartment"
    - Location: "South Balcony" (type: Balcony)
    - Location: "Kitchen" (type: Room)
    - Slots: "Pot Tomato", "Pot Basil", "Pot Parsley"

!!! example "Example: Indoor grower with two tents"
    - Site: "Indoor Garden"
    - Location: "Veg Tent" (type: Grow Tent)
      - Location: "Level 1"
        - Slots: "Pot 1" to "Pot 6"
    - Location: "Flower Tent" (type: Grow Tent)
      - Slots: "Spot 1" to "Spot 9"

---

## Frequently Asked Questions

??? question "Can I move a slot to a different location?"
    Yes. Open the slot, click **Edit**, and select a new parent location. A plant currently growing in the slot stays connected to the slot.

??? question "What happens if I delete a location that still contains plants?"
    Kamerplanter will not allow the deletion while plants or slots are still present in the location. Remove all plants and slots first.

??? question "Can I keep the location hierarchy flat?"
    Yes. You can assign plants directly to a location without creating slots. Slots are useful when you have many plants in one area and want to track each position precisely.

??? question "How do I record my own custom substrate mix?"
    Use the **Create Mix** feature in the substrate overview (see [Creating Custom Substrate Mixes](#creating-custom-substrate-mixes)). There you combine several existing substrates with percentage shares — Kamerplanter calculates the resulting properties automatically.

---

## See Also

- [Tank Management](tanks.md)
- [Planting Runs](planting-runs.md)
- [Fertilization](fertilization.md)
- [Growth Phases](growth-phases.md)
- [Weather Sources per Location](weather-sources.md)
