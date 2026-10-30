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

### Step 3: Fill in Basic Data {#filling-in-basic-data}

| Field | Description | Example |
|-------|-------------|---------|
| Name | Site name | "My Indoor Garden" |
| Type | Determines which features are available for this site (see table below) | "Outdoor" |
| Latitude / Longitude (GPS) | GPS coordinates of the site — fill in both fields together or leave both empty | 52.52 / 13.40 |
| Climate Zone | Location climate zone in USDA hardiness-zone format | "8a" |
| Total Area (m²) | Total growing area | 12 |
| Timezone | Timezone for tasks and calendar | "Europe/Berlin" |

**Available site types:**

| Type | Description |
|------|-------------|
| Outdoor | An open-air site — unlocks weather sources and [overwintering automation](overwintering.md) |
| Greenhouse | Glass house or poly tunnel — unlocks weather sources and [overwintering automation](overwintering.md) |
| Indoor | A room or living space with no direct outdoor climate exposure |
| Windowsill | A window spot with indirect outdoor climate exposure |
| Balcony | Balcony — a frost-exposed outdoor site: unlocks GPS coordinates, weather sources, and [overwintering automation](overwintering.md), just like Outdoor and Greenhouse |
| Grow Tent | Enclosed grow tent with controlled climate |

!!! info "Why USDA zones and not Köppen climate classification?"
    Kamerplanter expects the climate zone in **USDA Plant Hardiness Zone** format (a number from 1–13, optionally with an "a" or "b" suffix, e.g. "8a"), not the Köppen climate classification (e.g. "Cfb"). The reason: the hardiness data for plant species in the master data (`hardiness_zones`) uses the same format — this is what later allows Kamerplanter to check automatically whether a species can overwinter outdoors at your location. You can look up the matching zone for your area via the official [USDA Plant Hardiness Zone Map](https://planthardiness.ars.usda.gov/) or comparable hardiness zone maps for your region.

!!! tip "Why GPS coordinates matter"
    Only once GPS coordinates are stored can Kamerplanter automatically fetch weather data and calculate frost warnings for Outdoor, Greenhouse, and Balcony sites — a balcony counts as a frost-exposed outdoor location and is therefore treated exactly like Outdoor and Greenhouse. If you enter coordinates for a different type (e.g. Indoor) anyway, they remain unused for now — if you later switch the type to Outdoor, Greenhouse, or Balcony, they take effect automatically.

!!! tip "The climate zone can be derived automatically"
    For Outdoor and Greenhouse sites with GPS coordinates, Kamerplanter already computes this zone automatically in the background from your site's long-term climate data and keeps this field in sync — you don't have to look it up yourself in that case. For details on the computation, manually overriding it, and the current state of the web interface, see [Climate Zones & Hardiness](../guides/climate-zones.md). <!-- REQ-039 -->

!!! note "Experience levels"
    Depending on your experience level (Beginner / Intermediate / Expert, configurable in account settings) you will see more or fewer fields. Name and type are already visible at Beginner level; GPS coordinates, water source configuration, climate zone, and total area are added from Intermediate level upward; the timezone is an Expert-level field.

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
    Besides name, type, GPS coordinates, climate zone, area, and timezone, a site also tracks average frost dates (last spring frost, first autumn frost, and the German "Eisheilige" date) in the background. This setting is currently only available via the API — it is not yet editable in the site form. The benefit: once a site has a GPS position, Kamerplanter can calculate the actual day length at your location and correctly evaluate automatic, photoperiod-triggered phase transitions (e.g. flower onset for outdoor short-day plants) — see [Automatic Phase Transitions](growth-phases.md#automatic-phase-transitions). Frost dates also feed into the sowing calendar.

!!! tip "GPS coordinates unlock weather sources"
    For sites of type Outdoor, Greenhouse, or Balcony, a stored GPS position also unlocks the **Weather Source** section on the site detail page — there you select and prioritize public weather services or a Home Assistant source, see [Weather Sources per Location](weather-sources.md).

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
| Bed | No | Ground-level bed outdoors |
| Raised Bed | No | Elevated, framed bed |
| Greenhouse Bed | No | Bed inside a greenhouse |
| Cold Frame | No | Covered box for early propagation |
| Planter | No | Movable planter or a group of pots planned like a bed |
| Shelf | Yes | Shelf or shelving unit |
| Container Group | No | Grouping of several pots or containers in one place |

!!! info "For technical users"
    The sixteen types listed above are pre-installed system types. Kamerplanter already supports custom, additional location types internally. This setting is currently only available via the API — there is no dedicated management page for it in the UI yet.

### Setting Frost Exposure for a Location {#setting-frost-exposure-for-a-location}

Whether a plant counts as frost-exposed normally depends on the **type of the parent site**: Outdoor, Greenhouse, and Balcony are automatically treated as frost-exposed, while Indoor, Windowsill, and Grow Tent are not (see [Available site types](#creating-a-new-site)). For each individual location within a site, you can override this classification in the **Frost exposure** field — useful, for example, when a single location differs from the rest of the site.

The form for creating or editing a location offers three options:

| Option | Effect |
|--------|--------|
| Inherit from site (default) | Uses the parent site type's classification — matches previous behaviour with no override. |
| Outdoor – frost-exposed | The location counts as frost-exposed regardless of the site type. |
| Indoor – protected | The location counts as protected, even if the parent site is set up as Outdoor, Greenhouse, or Balcony. |

A location's frost exposure determines both whether plants at that location receive an [overwintering plan](overwintering.md) and whether they're covered by [season automation](season-automation.md) — winter approach, dormancy care, and spring reactivation. Both follow the same classification consistently: a location that counts as frost-exposed gets the full automation, even if it sits on an otherwise indoor site; a location classified as protected is never put into winter dormancy, even if other locations on the same site are frost-exposed. <!-- REQ-047 -->

!!! example "A balcony underneath a heated apartment"
    If your balcony sits underneath another, heated apartment, it is often noticeably warmer than a free-standing balcony. Kamerplanter still marks it as frost-exposed by default, since the site is set up with type "Balcony". If you want to override this for just this one location, open it and select **"Indoor – protected"** under **Frost exposure** — plants at this location then no longer receive an overwintering plan, even though other areas of the same site remain frost-exposed. Conversely, you can mark a particularly exposed location (e.g. a free-standing window sill in an unheated stairwell) as frost-exposed even when the parent site is set up as Indoor.

!!! tip "Undoing an override at any time"
    When editing a location, you can switch freely between all three options at any time — including back to **"Inherit from site"**. This removes the override entirely; the location then automatically follows the parent site type's classification again.

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

## Bed View {#bed-view}

If you open a location whose type is a bed (Bed, Raised Bed, Greenhouse Bed, Cold Frame or Planter), Kamerplanter shows the bed view instead of the regular location page. It brings everything important about a bed together in one place.

### Summary above the tabs

Above the tabs you see at a glance: area, type, status, soil type, sun exposure, active plants, open tasks, last care, next due date and who is responsible for the bed. Use the **season selector** to switch the year; it appears in the address as `?year=`.

!!! warning "Not yet implemented"
    Showing the previous year's crop in the summary is not implemented yet. Until then, Kamerplanter shows a placeholder line there. **Clear bed** will also only be available in a later version.

### The tabs

The active tab is part of the address (e.g. `#plan` or `#soil`), so you can share links to a specific tab.

| Tab | Content |
|-----|---------|
| Plan | Bed frame with places, rows or zones and plant markers. Tap a plant and the bed offers **Correct position** and **Transplant to …**. **Open in garden plan** takes you to the garden plan for editing the bed frame. |
| Care | Open and overdue tasks of the bed and its plants, completing them, suggestions and the care log (see [Care on the bed](#care-on-the-bed)). |
| Planting | Planned and standing plants of the bed, the **Plant** button and the actions on a plant (see [Planting a bed](#planting-a-bed)). |
| History | A timeline of what stood in the bed in earlier years, and the list of all care entries and plantings (see [History of the bed](#history-of-the-bed)). |
| Soil | The bed's soil profile (see below). |
| Details | The previous location page, unchanged. |

### Planting a bed {#planting-a-bed}

On the **Planting** tab, **Plant** opens the planting dialog. It is available from the "grower" role and needs the bed to be drawn on the garden plan. The bed must not be retired.

1. **Choose species and cultivar.** Your favourites come first. Below the choice you see the species' mature height and width and whether it needs a support.
2. **Read the hints.** As soon as you have chosen a species, Kamerplanter checks **crop rotation** and the **neighbours** in the bed. Every hint has a strength (no issue, info, warning, critical) and a reason, for example "The family Solanaceae stood in this bed 1 year(s) ago. The rotation pause is 4 years". A hint blocks nothing. A **site** hint comes with them, see [Sun and shade of a bed](#sun-and-shade-of-a-bed).
3. **Choose number and layout.** Either **As many as fit** or a fixed number. The layout is **Grid**, **Rows**, **Staggered**, **Zone** (for direct sowing) or **Free positions** (for woody plants).
4. **Check the spacings.** Kamerplanter prefills the plant spacing and row spacing from the species profile and says where the value comes from. If the profile has none, Kamerplanter uses the value you used last for this species. If there is none either, the field stays empty and you enter the spacing yourself. Under **More options** you set the row direction and the edge margins.
5. **Look at the preview.** The bed shows at once where the plants would stand, and below it you see how many there are and how many fit at most. The server confirms the number a moment later. If its answer differs, its answer counts.
6. **Plan or record.** **Plan planting** creates a planned run and reserves the places from the planting date. If you have planted already, switch on **I have planted already**. The plants are then created at once on the calculated positions.

**Several species (mixed culture).** **Add another species** adds up to four species to the same planting. If all are laid out in rows, Kamerplanter spreads the rows **alternately** over the species, say carrot in every second row with onion in between. The row and edge settings of species 1 then apply to all; only the spacing within the row stays per species. If Kamerplanter rates a combination as incompatible, a hint appears.

**Free positions.** With **Free positions** you tap the planting places onto the bed. Dragging moves a place, a number below the preview deletes it. If two places are closer together than the minimum spacing, both get a **yellow ring**. That is a hint; you can still plant.

**Plant anyway.** From the strength **warning** on, you switch on **Plant anyway** and give a **reason**. The reason is stored with the planting, and the bed carries the **Crop rotation hint** in its overview for as long as the planting runs.

**Pot volume.** For species with a recommended pot volume you can enter the volume of your pot under **More options**. If it is smaller than recommended, Kamerplanter warns you.

**Correct position.** For a standing plant (on the **Planting** tab or after a tap on the plan), **Correct position** moves its place: by dragging, with the arrow buttons in steps of 1 cm, or by typing the coordinates. The care log records the correction together with the plant. Plants in a zone have no single place and cannot be moved.

**Transplant to …** You do not move a plant to another bed by dragging. **Transplant to …** creates the "Transplant" task for the plant, with the target bed in its text. You complete it once you have moved the plant.

!!! warning "Not yet implemented"
    The **Crop rotation hint** appears only in the bed overview so far, not on the bed in the garden plan. It is set only for plantings you started despite a hint. Planned, still empty places appear on the plan as dashed circles without species and date. Your browser, not your account, remembers the spacings you used last. A bed that is not on the garden plan cannot be planted through the dialog yet. <!-- REQ-053 GP-FR-132, GP-FR-061 -->

### Plant state and plant info {#plant-state}

On the **Plan** tab every standing plant shows its state right on the marker, so you see at a glance whether something needs doing.

- **Disc:** the colour is the growth phase, the letter the species. Zoomed in far, an arc around the disc shows how far the phase has progressed.
- **Ring:** it tells the state of the planting. Dashed and faint means planned, dotted with seed dots means sown, solid means growing, a double ring means harvesting, and a cross on an empty ring means failed.
- **Sign at the top right:** at most one appears, the most urgent: a triangle for an open finding, a hexagon with a star for frost risk, a circle with an exclamation mark for an overdue task, a drop for watering due and a square with a check mark for ready to harvest. All other reasons are listed in the plant info.

Ring and sign differ without colour too, so you can tell them apart in greyscale and with red-green weakness. The collapsible **Legend** under the plan explains every sign.

**Plant info.** Rest the mouse on a plant for 0.3 seconds and an info bubble shows species, cultivar, phase and progress, age, position, last care, next task and the reasons it needs attention. The bubble stays while the pointer is on the plant or the bubble and closes with **Esc**. With the keyboard you get the same info through focus on the marker. On a touch screen, tap the plant to open a sheet at the bottom with the cover photo and a **Details** button. Hovering sends no request: Kamerplanter loads the states of all plants of a bed once, after every action on the bed and when you come back to the tab.

!!! warning "Not implemented yet"
    **Frost risk** is not shown yet; it arrives with the bed's site features. **Watering due** currently comes only from a watering task that is due today, not from the irrigation demand. Planned places are still drawn without species and date. <!-- REQ-053 GP-FR-190, GP-UX-061 -->

You see the same discs, rings and signs in the garden plan for the whole site when you switch on the **Show plant state** layer there; it is described with the layers further down.

### Care on the bed {#care-on-the-bed}

The **Care** tab lists every open task attached to the bed or to a plant in it. **Overdue** tasks come first and are marked red, followed by the other open tasks. With the "viewer" role you see the list read-only.

**Completing a task.** Tap **Done**. A short dialog opens that asks only for what fits the kind of task:

| Kind of task | Fields |
|--------------|--------|
| Watering, flushing | Amount (litres, millilitres or litres per m²) and water source |
| Feeding | Product (from the catalogue or free text), amount and unit |
| Soil amendment, liming | Material, amount and unit |
| Mulching | Material and thickness in centimetres |
| Covering, uncovering | Material (fleece, net, foil, frost cover) |
| Harvest | Weight |
| All others | Note |

Every field is optional, so you can tap **Complete** without entering anything. **When** defaults to now; you can backdate up to 365 days, but never into the future. The details go into the bed's care log. A double tap counts once.

**Undo.** After every action a message with **Undo** stays for eight seconds. It reopens the task and takes the log entry back. As the author you can do this for ten minutes; the "lead" role can do it at any time.

**New task.** **New task** creates a task for the bed. If you choose **Every plant in the bed**, each plant standing there gets its own task and the task for the whole bed is dropped. The categories on offer follow the bed: flushing, EC check and pH adjustment exist only for beds with a substrate, hilling, tillage and liming not for pure substrate beds, ventilating only in a greenhouse, cold frame or tent.

**Logging care without a task.** **Log care** records what you just did ("I mulched") when no task exists for it. Plant protection treatments are not logged here; use the plant protection form, because the care log is not proof of a treatment.

**Suggestions.** Tasks proposed by the system appear in their own **Suggestions** section with the reason. **Do now** carries out the suggestion and completes it, **Dismiss** rejects it. Nothing happens until you decide.

!!! warning "Partly available: suggestions"
    The system does not generate suggestions yet. The section is in place and appears as soon as suggestions exist. A separate **Accept** without completing at the same time is not possible yet. <!-- REQ-053 GP-FR-086 -->

**Several beds at once.** On the garden plan page, the button **Complete tasks on several beds** sits above the bed list. You pick a kind of task (for example watering) and the beds. Kamerplanter finds every open task of that kind on those beds and their plants and completes them in one step with the same details for all. One step takes at most 200 tasks; Kamerplanter reports whatever could not be completed.

**Task counter on the plan.** On the garden plan, each bed with open tasks shows a number in its top-right corner, red if tasks are overdue. A tap on it opens the bed's Care tab. By keyboard you reach it through the **Care** button in the properties of the selected bed, or through the number in the "Open tasks" column of the bed list. <!-- REQ-053 GP-FR-083, GP-FR-088, GP-FR-089, GP-FR-090 -->

!!! info "Colour by priority"
    The counter distinguishes only "open" and "overdue" so far. Colouring by task priority follows once the plan delivers the priority.

### Sun and shade of a bed {#sun-and-shade-of-a-bed}

You record how much direct sunlight a bed gets with five **tiles**. Each tile shows an icon, the name and the definition:

| Tile | Meaning |
|------|---------|
| Full sun | more than 6 hours of direct sunlight on a summer day |
| Partial shade | 3–6 hours |
| Shade | 2–3 hours |
| Deep shade | less than 2 hours |
| Unknown | not recorded yet (default) |

The hours follow the Royal Horticultural Society definition, measured at midsummer.

- **In the bed view:** next to the sun exposure in the overview, **Change sun** opens the tiles. This needs the "grower" role.
- **In the garden plan:** when you select a bed, the properties panel shows the tiles. When you select several beds (frame selection or the Shift key), **Set the sun for all selected beds** sets the value at once. Locked beds stay as they are. You can take the step back with **Undo**, and it only counts once you save the plan.

**Sun window and leaf shade.** On top of the tile you record **when** the sun reaches the bed: morning, midday, afternoon, all day or changing. The hours of direct sun in summer are optional, a rough guess is enough. The **Leaf shade in summer** switch notes that the bed is sunny in spring and later shaded by the leaves of trees. You find the fields in the **Change sun** dialog of the bed view and, in field mode, in the bed sheet (with large buttons, every change is saved at once). The entries appear on one line under the sun exposure in the bed overview. Kamerplanter calculates nothing from them, and leaf shade is a note only: it does not change the site hint when planting. <!-- REQ-053 GP-FR-158, GP-FR-159, GP-UX-057 -->

In the garden plan, the properties panel of a selected bed shows the same fields under the tiles; a change there becomes part of the plan save, and you can take it back with **Undo**.

**Site hint when planting.** In the planting dialog Kamerplanter compares the sun of the bed with the **light requirement** of the species (full sun, partial shade or shade) and shows a traffic light with plain text, for example "Bed: Shade — Tomato needs full sun". Green means well suited, yellow only partly suited, red poorly suited. Yellow also appears when the bed is one step shadier than the requirement and the species profile says the species takes that much shade; if that value is missing, the text says "Tolerance unknown". If the sun of the bed or the light requirement of the species is not recorded, no hint appears. The hint blocks nothing and asks for no reason.

!!! note "Frost risk"
    The frost risk of a bed (low, normal, high) will be maintained next to the sun. Kamerplanter copies existing **frost exposure** settings over automatically (yes becomes high, no becomes low); until then, the frost exposure setting stays the one that counts. <!-- REQ-053 GP-FR-157, GP-FR-160, GP-FR-162 -->

**Sun window, drainage and frost risk layers in the garden plan.** In the layer group of the view bar you can show three more layers: **Show sun window** (when direct sun reaches the bed), **Show drainage** (poor, moderate, good) and **Show frost risk** (low, normal, high). Every value has its own pattern, so you can tell them apart without colour. The pattern is always shown; once you zoom in far enough for the bed names to appear, a small symbol for the value joins it at the bottom edge of the bed, where the bed has room for it; the legend below the view bar explains every layer that is on. A bed without a recorded value stays without a pattern. All three layers start switched off, and your browser remembers your choice for you. The frost layer shows the stored frost risk; for overwintering, the frost exposure stays the setting that counts. <!-- REQ-053 GP-FR-169, GP-FR-047 -->

**Plant state layer and filter in the garden plan.** With **Show plant state** in the same layer group you see the state of your plants without opening a bed. Once you zoom close enough to a bed for the single plants to appear, every plant carries disc, ring and sign as in the bed's **Plan** tab: the colour shows the growth phase, the ring how far the planting is, the sign at the top right the most urgent reason to act. Further out each bed sums up its plants as a circle with a number; if you have seen a bed close enough before, Kamerplanter knows its states: the circle then shows the most urgent sign, and the screen reader names the number of all plants in the bed and how many of them need attention. Next to it sits the switch **Only show plants that need attention**: it hides every plant whose state is known and that carries no sign. A plant whose state is not loaded yet stays visible. The circle of a bed then shows only the plants that remain, and it disappears only once every state of the bed is known and no plant needs attention; the bed itself stays visible, and the screen reader still names the number of all plants. While the layer is off, the switch is disabled; you still reach it with the Tab key, and the screen reader tells you why it is disabled. The legend below the view bar explains rings and signs and lists the colours of the growth phases of the plants whose states are loaded, sorted alphabetically in your language. Kamerplanter loads the states only while the layer is on, only for the beds you currently see close enough, and at most four beds at a time. Each bed loads once and again when you come back to the tab, when you save the plan or a newer version of it loads, and after you changed a zone or logged a watering round in the irrigation panel. The layer and the filter start switched off; your browser remembers your choice. The info bubble on hovering a plant stays with the bed's **Plan** tab. <!-- REQ-053 GP-UX-061, GP-UX-060 -->

### History of the bed {#history-of-the-bed}

The **History** tab has two parts: the **timeline** on top and the **list** below it.

**Timeline.** It shows for each year which plant families stood in the bed, for at least the last five years and up to ten when a family needs a long rotation pause. Every family has its own colour and the entry always carries its name as well. Green manure and fallow years are marked. The timeline is the basis of the crop rotation check. For pots, tents and shelves that check is off; the history is still kept.

**What stood here?** To fill in a year from before you used the app, tap **Fill in {year}** at the year or **What stood here?** at the top. You choose the year, the plant family (or a species, which brings its family), the role (main crop, green manure or fallow) and optionally the season. The last ten years up to last year are allowed. A message with **Undo** follows. You take a filled-in entry back later with the **x** on the entry, as its author or in the "lead" role. It then stays in the care log as cancelled. Viewers see the timeline read-only.

**List.** The newest entries come first, 50 per page; **Load more** fetches the next ones. The list mixes care entries with planting events: plant planted or removed, run started or completed. You can filter by **category**, **period**, **plant** and **person**. Corrections are hidden at first: replaced entries and "Position corrected". **Show corrections** brings them back, marked "Corrected" or "Correction".

!!! info "Who may filter by person"
    The person filter is an activity profile and therefore restricted. With the "viewer" and "grower" roles you filter only by yourself. The "lead" role and members with the `management` admin scope can filter by any member. Members who left show as "anonymised" and cannot be filtered.

**History of all beds.** **History of all beds** opens the care history of the whole tenant at `/standorte/historie`. It shows the last 90 days unless you choose another period and offers the same filters plus **Bed**. The plant filter is available once a bed is chosen.

### Maintaining the soil profile

In the **Soil** tab you record: filling, soil type (with a finger test as help if you are unsure of the type), drainage, site moisture, conditions, as well as pH, EC (electrical conductivity) and humus content. If you optionally pick a [substrate](#managing-substrates), Kamerplanter pre-fills its pH and EC. The drainage also appears in the bed overview once you have recorded it. As a viewer (role "viewer") you see the profile read-only.

### Changing the bed status

- **Planned → Active**: possible from the "grower" role.
- **Retire and reactivate**: only with the "lead" role.
- To retire a bed you need a **reason**, and the bed must contain no plants. The reason is written to the care log.

!!! tip "Tip: empty the bed first, then retire it"
    If plants are still in the bed, Kamerplanter rejects retiring it. Remove or harvest them first.

---

## Bed List on the Garden Plan {#bed-list-on-the-garden-plan}

Below the plan on the garden plan page, a table lists your beds: name (a link to the bed view), type, area, status, responsible person, plants, open tasks (including overdue ones) and next due date. Retired beds are hidden by default. The **My beds** switch filters to your own beds and requires that beds are assigned to you.

If you click a row or press Enter, the bed is selected on the plan and the view zooms to it. The number in the "Open tasks" column is a link to the bed's Care tab. From the "grower" role on, the button **Complete tasks on several beds** sits above the table (see [Care on the bed](#care-on-the-bed)).

---

## Field mode in the garden {#field-mode-in-the-garden}

Field mode is made for the phone at the bed: large buttons (at least 64 pixels), strong contrast for sunlight and only what you need outside. On a narrow screen (below 600 pixels wide) the garden plan page opens in field mode right away. On any device you switch with **Field mode** or **Planning mode** at the top of the page; the address then carries `?mode=field` or `?mode=plan`.

**My beds · due today.** Field mode starts with the list of your beds. Beds assigned to you come first (marked **Mine**), then beds with overdue tasks or tasks due today, then the rest by their next due date. A task is overdue when its due day lies before today; a task due today does not count as overdue yet. Retired beds are left out. The **Map** tab shows the plan without tools, grid or handles. **Zoom in**, **Zoom out** and **Whole plan** change the view. If you tap a bed, or just next to it, the map zooms to the bed and opens it.

**The bed sheet.** A tap on a bed opens a sheet at the bottom with the bed's name, the quick log, the tasks and the plants. Tasks come in the order **Overdue**, **Due today**, **Later**. Plants are grouped by species, count and phase; the phase colour always has a black outline and the phase name next to it.

- **Done** opens the short dialog with the optional fields (quantity, note). **Finish** saves. That is two taps after choosing the bed. A double tap counts once, and the buttons stay locked until the answer has arrived.
- **Quick log:** **Watered**, **Sown** and **Weeded/Mulched** save a care entry with one tap. **Harvested** and **Note** open the short form (quantity or text; for the note you can use your keyboard's voice input). **Planted** opens the planting dialog with **I have planted already** switched on; the plants are created at once. This needs a bed that is drawn on the plan.
- After **Done** and after every quick log entry you see **Undo** for eight seconds. It takes the entry back.
- **Show plants** lists the single plants of a group. **Correct position** moves a plant with the arrows in 10 cm steps; you can drag the marker only after holding it for half a second. **Photo** takes a picture for the plant's gallery.

Deleting, clearing a bed, export and import are not available in field mode; switch to planning mode for them. With the "viewer" role you see tasks and plants read-only. Your browser, not your account, remembers the tenant, site, tab and map view; if someone else signs in on the device, field mode starts fresh for them. If a remembered map view would show hardly any of the plan on the current screen – after turning the phone, for example – the map opens on the whole plan.

!!! warning "Not implemented yet"
    Without a connection field mode shows a notice and locks **Done** and the quick log; entries are not yet stored on the device and sent later. Photos are attached to a plant for now, not to the bed. **Planted** has no **Undo**. GPS help, the QR code on the bed and the "last watered" layer follow later. <!-- REQ-053 GP-UX-020…031, GP-FR-149 -->

---

## Working faster in the garden plan {#plan-comfort}

This section describes the aids that save you manual work in planning mode.

**A bed from a template.** In the tool bar, **From template** puts a bed on the plan with one click. You pick a template, turn it in 90-degree steps with **Rotate** if needed, and click where the bed should go (the lower-left corner of a rectangle, the centre of a circle). A dashed preview shows where it lands. Without a mouse, **Place at view centre** puts the bed in the middle of the view. The bed gets the template's name, type, shape and height and is saved at once; Kamerplanter saves your unsaved changes first. This step cannot be taken back with **Undo**. If you do not want the bed, delete it. **Esc** or another tool ends the template choice.

**Standard sizes.** In the **Add with dimensions** dialog, a standard size fills shape, size, bed type and height in one go, for example the raised bed 1.2 × 2.4 m, the raised bed 2 × 1 × 0.8 m or a planter. You can still change every value afterwards. The height is optional.

**Save as template.** With exactly one bed selected, **Save as template** stores its shape, type and height as a template of your garden. Plants, tasks and notes are not part of it, and the template only carries planting distances or soil values if you enter them yourself. Growers and leads create templates.

**Snapping to other objects.** When you move or draw, the plan snaps to corners and edges of other objects before it snaps to the grid. A green line shows the edge you are on. The Alt key or the **Snap** switch turns snapping off. With a pen or a finger the catch zone is larger.

**Align and distribute.** With at least two beds or objects selected, **Align** lines them up on the left, right, top or bottom edge or on the centre. From three objects on, **Distribute evenly** spreads them with equal gaps. Locked objects stay where they are and do not count. Each of these actions is a single step for **Undo**.

**Overview map.** When the garden is much larger than the visible section (more than four times), a small map appears at the bottom right of the plan with the section as a rectangle. A click on it jumps the view there. With the keyboard you keep moving the plan with the arrow keys.

**Auto-save.** The **Auto-save** switch next to **Save** saves your changes two seconds after the last change. It is off by default and applies only to you in this browser. On a conflict or a refused save it pauses and tells you so. Field mode does not have it: every action is sent at once there.

**Duplicate several times.** From the **⋯** menu or the context menu, **Duplicate several times** makes several copies of the selected beds in a row: count, direction, spacing and a naming scheme such as "Plot {n}" (up to 100 copies). That is handy for the plots of a community garden. Kamerplanter first checks that the copies fit completely into the garden and that the limit of 500 beds and objects is enough; if not, nothing is created. One **Undo** takes all copies back. Planting positions, plants and tasks are not copied; you lay out a planting grid for each bed afterwards. <!-- REQ-053 GP-FR-025, GP-FR-029, GP-FR-043, GP-FR-044, GP-FR-045, GP-FR-154, GP-UX-004, GP-UX-014 -->

---

## Export the plan and restore a backup {#plan-export-import}

On the garden plan page, **Export & import** opens two dialogs.

**Export plan** comes as a PDF (the plan to scale, for printing), an SVG (vector graphic) and a backup (JSON). You choose paper, orientation, scale and layers; a preview shows what you get. With **Automatic**, Kamerplanter takes the finest scale that fits the sheet and suggests A3 when A4 would get too coarse. If a fixed scale does not fit the sheet, the dialog says so and lets you choose a coarser scale or A3. On a phone there is only PDF and backup with the standard options. The export holds no member names and no assignments.

In the PDF and the SVG every plant shows its state as on the plan: the disc in the colour of its growth phase, a ring for how far it is (a thick ring means *harvesting*) and at most one sign for the most urgent matter, such as a triangle for an open finding or a drop when watering is due. The legend lists the growth phases, rings and signs that occur on the plan. Of the growth phases it names at most the six with the most plants; if there are more, one entry such as "+3 more phases" sums up the rest, so the plan still fits the page at the chosen scale. A long phase name is shortened with "…". Plants of a species with its own phase sequence carry the same colour as on the plan. From 2,000 plants on, each bed shows only the number of its plants instead. <!-- REQ-053 GP-UX-005, GP-UX-059, GP-UX-060 -->

The **backup** holds beds, garden objects, plant places, soil profiles, site features and the garden boundary, but no plants and no tasks. If you have selected beds or garden objects on the plan, you can limit the backup to **Selection only** or **Selection with everything below**. Such a partial backup has no garden boundary, and references to things that are not in the file are dropped. Every role may read it.

**Restore a backup** leads through the import in three steps. Only a lead can do this.

1. **Choose file:** The file may be at most 5 MB. Kamerplanter checks it right away without writing anything.
2. **Check report:** You see how much would be created and deleted, which references are not carried over (for example an irrigation zone that does not exist here) and which problems the file has, such as overlapping beds. With problems you cannot continue.
3. **Mode:** *Add* creates the backup in addition to the existing plan. *Replace* swaps the plan of this site. For that you type the name of the site. Before that, Kamerplanter saves the previous plan as a snapshot in the change log. Download a current backup first anyway, to be safe.

In *Add* mode you can move every shape of the file by a distance (to the right and up, in metres), for example to put a bed somewhere else. **Where is the file going?** tells Kamerplanter whether the file comes from this site, another site or another garden account. For the last two, references that are not in the file are never resolved against this site: they are dropped and listed in the check report. Nothing is read from another account, the file is the transport; you need the lead role in the account you import into.

**Restore an earlier state:** In the first import step this button opens the list of plans that a *Replace* overwrote (kept for one year, lead only). You pick a state, read the check report and type the name of the site. Kamerplanter first saves the current plan as a state of its own, so the restore can be undone. Irrigation zones that the state does not name are removed, and technical zone bindings (actuator, Home Assistant flow) are not restored; set them up again afterwards. *Add* does not create a state.

!!! warning "Beds with active plants"
    A bed with a plant in it is never deleted. While such beds exist, *Replace* rejects the file. If you choose the option to keep those beds, they stay together with the locations above them, and the rest is replaced.

**New season from last year:** In the **Export & import** menu, **New season from last year …** re-creates last year's places as free slots for every bed without active plants (lead only, within the same site). You enter the year of the new season; the places come from what was finished in the year before. Kamerplanter checks first and shows what happens per bed: beds with active plants and retired beds are skipped and listed in the report, and so is a bed that would pass 2,000 slots with the new places. Places that already stand as a free slot are not created twice. Zones, plants, planting runs and history stay as they are; crop rotation and companion planting hints keep using last year's occupancy. **Show "Here stood …"** adds the plant family of last year to each bed, for orientation only. Only **Create free slots** writes, in one step with an entry in the change log; if the plan changed since the check, you check again. <!-- REQ-053 GP-FR-171 -->

All keys are newly assigned on import. Links to Home Assistant and to actuators are never carried over; set them up again afterwards. If you have unsaved changes to the plan, save or discard them first. In field mode, export and import are hidden.

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
- [Season Automation](season-automation.md) — how a location's frost exposure drives the season automation
- [Overwintering](overwintering.md) — the automatically created overwintering plan per plant
- [Plant Identification by Photo](plant-identification.md#assigning-a-location-optional) — assign a site, area, and slot directly when creating a plant
