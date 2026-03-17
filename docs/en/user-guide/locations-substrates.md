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

**Slot** is a single planting spot — for example "Pot 3" or "Row 2, Position 4". Slots are always the bottom level and can be assigned to exactly one plant.

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
| Climate Zone | Location climate zone | "Cfb (Temperate oceanic)" |
| Total Area (m²) | Total growing area | 12 |
| Timezone | Timezone for tasks and calendar | "Europe/Berlin" |

!!! note "Experience levels"
    Depending on your experience level (Beginner / Intermediate / Expert, configurable in account settings) you will see more or fewer fields. Experts see additional fields for water source configuration, GPS coordinates, and frost dates.

### Step 4: Configure Water Source (optional, Intermediate and above)

If you use tap water or a reverse osmosis system, enter the water values. The system will later calculate your EC budget and CalMag requirements automatically:

- **Tap water EC** (mS/cm): Typically 0.3–0.8 in Central Europe
- **Tap water pH**: Typically 7.0–8.0
- **Has RO system**: Enable this if you have a reverse osmosis unit

!!! tip "Finding your water values"
    Your tap water EC can be found on your water supplier's website or measured with an inexpensive EC meter.

### Step 5: Save

Click **Save**. The site appears in the overview.

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

| Type | Description |
|------|-------------|
| Grow Tent | Enclosed grow tent with controlled climate |
| Greenhouse | Glass house or poly tunnel |
| Raised Bed | Elevated bed outdoors |
| Open Bed | Ground-level bed in the garden |
| Balcony | Balcony or terrace |
| Window Sill | Indoor window sill |
| Room | Whole room as an area |
| Hydroponic System | NFT, DWC, aeroponics, or similar |
| Shelf | Shelf or shelving unit |
| Other | User-defined type |

### Adding a Slot Within a Location

1. Open a location by clicking its name in the tree.
2. Click **Add Slot**.
3. Enter a label (e.g. "Pot 1" or "Row A, Position 3").
4. Optional: Enter the capacity (pot size in litres).

---

## Managing Substrates

A substrate describes the growing medium in which your plants root. Kamerplanter distinguishes between different substrate types and allows management of substrate batches.

### Creating a New Substrate

1. Navigate to **Locations → Substrates**.
2. Click **Add Substrate**.
3. Select the **substrate type** (see table).
4. Enter a name (e.g. "Organic Soil Batch March 2026").
5. Optional: Enter pH range, EC value, and capacity.

**Available Substrate Types:**

| Type | Description | Recommended Use |
|------|-------------|----------------|
| Soil (SOIL) | Standard garden soil | Outdoors, pot plants |
| Organic Soil | Organically enriched soil | Houseplants, herbs |
| Living Soil | Living soil with microbiome | Organic growing |
| Coco Coir | Coconut substrate | Indoor, hydroponic-like |
| Perlite | Volcanic mineral (drainage) | Always as an additive |
| Rockwool Slabs | Mineral wool for hydroponics | Hydro systems, cultivation |
| Rockwool Plugs | Small propagation blocks | Cuttings, germination |
| Raised Bed Mix | Special raised-bed soil | Raised beds |
| Peat | Peat-based (not recommended) | Historical use |
| Vermiculite | Expanded mineral | Propagation, additive |
| PON Mineral | LECA / expanded clay | Semi-hydroponics |
| Sphagnum | Peat moss | Orchids, epiphytes |

!!! warning "Coco Coir and CalMag"
    Coco coir actively binds calcium and magnesium. CalMag supplements are always recommended for coco substrates, even with hard tap water. Kamerplanter will warn you if a nutrient plan for coco plants contains no CalMag.

### Assigning a Substrate to a Slot

1. Open the desired slot.
2. Click **Assign Substrate**.
3. Select an existing substrate from the list.
4. The substrate is now linked to this slot.

### Preparing a Substrate for Reuse

After completing a growing cycle you can prepare a substrate for reuse:

1. Open the substrate in the detail view.
2. Click **Prepare for Reuse**.
3. The system checks pH standard deviation and EC drift from previous use.
4. If the drift is too large a warning appears — in this case, new substrate is recommended.

!!! note "Disposable substrates"
    Rockwool slabs and plugs are single-use substrates and are not offered for reuse.

---

## Tips for Location Structure

!!! example "Example: Balcony gardener"
    - Site: "Berlin Apartment"
    - Location: "South Balcony" (type: Balcony)
    - Location: "Kitchen Window Sill" (type: Window Sill)
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
    Choose the most suitable type when creating the substrate and describe the mix in the notes field. Expert users have access to additional fields for pH range, conductivity, and irrigation strategy.

---

## See Also

- [Tank Management](tanks.md)
- [Planting Runs](planting-runs.md)
- [Fertilization](fertilization.md)
