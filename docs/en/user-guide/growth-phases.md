# Growth Phases

Every plant in Kamerplanter passes through a sequence of growth phases. The system automatically adjusts recommendations for watering, fertilization, light, and climate to the current phase. This ensures each plant receives exactly what it needs at its current stage of development.

---

## Prerequisites

- At least one plant set up (via planting runs or individually)
- Helpful: matching nutrient plans for the respective phases (optional but recommended)

---

## The 10 Phase Types

Kamerplanter ships with ten pre-built phase types. Each plant species only uses the subset that makes sense for it — which subset that is depends on the assigned **phase sequence** (see the next section).

<!-- Source: src/backend/app/migrations/seed_data/phase_sequences.yaml (phase_definitions) -->

| Phase type | Description | Typical duration |
|-----------|-------------|----------------|
| **Germination** | Seed germinates, first roots form | 7 days |
| **Seedling** | Establishment after germination, still delicate | 14 days |
| **Vegetative** | Active leaf and stem growth | 45 days |
| **Flowering** | Flower formation and pollination | 30 days |
| **Fruiting** | Fruit development after pollination | 75 days |
| **Ripening** | Final maturation before harvest | 14 days |
| **Dormancy** | Rest period for perennial plants | 120 days |
| **Sprouting** | New growth after dormancy | 21 days |
| **Senescence** | Leaf fall, preparation for dormancy | 21 days |
| **Flushing** | Pre-harvest flush with plain water | 14 days |

The listed duration is a guideline from the phase definition — individual phase sequences can override it (see below).

!!! note "\"Harvest\" is no longer its own phase"
    Unlike earlier versions, there is no separate phase called "Harvest". Instead, each phase definition **within a sequence** marks via an "allows harvest" flag whether harvesting is permitted during it — usually the **Ripening** phase, and for some perennial crops **Fruiting** itself. This also correctly represents plants with continuous harvest (e.g. tomatoes that ripen continuously over weeks).

---

## Phase Sequences: How a Species Moves Through Phases

A **phase sequence** is an ordered chain of phase types that makes sense for a plant species or a group of similar species. Kamerplanter ships with 11 pre-built sequences, for example:

| Sequence | For | Example phase chain |
|--------|-----|---------------------|
| **Indoor Default Cycle** | Cannabis and similar indoor crops | Seedling → Vegetative → Flowering → Flushing → Ripening (harvest) |
| **Annual Harvest Crop** | Lettuce, herbs | Germination → Seedling → Vegetative → Ripening (harvest) → Senescence |
| **Standard Perennial** | Perennial ornamentals | Dormancy → Sprouting → Vegetative → Flowering → Senescence (repeats) |
| **Full Fruit Cycle Perennial** | Fruit trees with multi-year fruiting | Dormancy → Sprouting → Vegetative → Flowering → Fruiting → Ripening (harvest) → Senescence (repeats) |
| **Biennial with Vernalization** | Biennial vegetables (e.g. carrot, onion grown for seed) | Germination → Seedling → Vegetative → Dormancy (cold period) → Flowering → Ripening (harvest) |

<!-- Source: src/backend/app/migrations/seed_data/phase_sequences.yaml (phase_sequences) -->

For every phase, a sequence defines whether it is **recurring** (perennial plants go through the cycle again), whether it is a **terminal phase** (the sequence ends there), and whether **harvest is allowed** during it. Which sequence a plant species uses is part of the species' lifecycle configuration in the master data.

<!-- diagram-source: derived from phase_sequences.yaml — indoor_default and perennial_standard sequence patterns -->
```mermaid
stateDiagram-v2
    [*] --> Seedling
    Seedling --> Vegetative
    Vegetative --> Flowering : Photoperiod change or manual
    Flowering --> Flushing
    Flushing --> Ripening : Harvest allowed
    Ripening --> [*]

    Vegetative --> Dormancy : Perennial sequence
    Dormancy --> Sprouting
    Sprouting --> Vegetative
```

!!! note "Not all phases apply to every plant"
    Herbs such as basil or lettuce do not go through a pronounced flowering phase the way resin-producing plants do. Which phases a species goes through is determined entirely by its assigned phase sequence — not all ten phase types occur in every sequence.

---

## Managing Phase Definitions and Sequences

Advanced users can create their own phase types and sequences, or review the existing ones:

- **Phase Definitions** (`/phasen/definitionen`): a list of all phase types with name, typical duration, watering interval, and stress tolerance. The ten built-in phase types are marked as "system" entries and cannot be deleted while they are used in a sequence. Add your own via **Create Definition**.
- **Phase Sequences** (`/phasen/ablaeufe`): a list of all phase sequences with cycle type (annual, biennial, perennial), number of phases, and total duration. In a sequence's detail view you add phases, reorder them ("Move up"/"Move down"), and set per phase whether it is a **terminal phase**, **recurring**, or **allows harvest**. For repeating sequences you also choose which phase the cycle restarts at after the terminal phase.

Both pages are available in the navigation under **Phases**. Since they edit fundamental system data, they are — like other master data areas — intended primarily for advanced users.

---

## Viewing the Current Phase of a Plant

1. Navigate to **Plants** and open a plant by clicking its name.
2. The detail page shows the current phase with a colored chip at the top.
3. The **Growth Phases** tab shows the complete phase history with the date of each transition.

---

## Automatic Phase Transitions

In addition to the manual transition (see below), a phase transition within a sequence can also be triggered automatically. Kamerplanter supports three trigger types:

- **Time-based**: The transition fires automatically once a plant has spent a defined number of days in its current phase.
- **Photoperiod-based**: The transition to flowering fires once the day length at the plant's site drops below (short-day plants) or rises above (long-day plants) a species-specific threshold. This requires GPS coordinates to be configured for the site (see [Locations and Substrates](locations-substrates.md)).
- **Vernalization-based**: For biennial plants with a cold requirement (e.g. carrot grown for seed), Kamerplanter counts cold days; once the species-specific minimum is reached, the transition from dormancy to flowering is unlocked automatically.

!!! note "Partially available"
    The evaluation logic for automatic transitions is fully implemented. Whether and how often your Kamerplanter operator actually schedules the background check depends on the specific installation. To be safe, don't rely exclusively on automatic transitions — check your plants' phase status regularly and trigger transitions manually when needed (see below).

---

## Triggering a Phase Transition Manually

You can trigger a phase transition manually at any time, regardless of whether automatic transitions are also configured for the phase — for example, if you want to move a plant earlier or later than the system suggests, based on your own observation.

### Step 1: Open the Plant

Navigate to your plant and open the **Growth Phases** tab.

### Step 2: Trigger the Phase Transition

Click **Change Phase** (or the specific phase name, e.g. "Switch to Flowering"). A confirmation dialog appears.

### Step 3: Enter Details

In the dialog you can optionally enter:

- **Transition date**: Today by default, but can be set in the past
- **Notes**: Observations accompanying the transition (e.g. "First flower sites visible")

### Step 4: Confirm

Click **Save**. The phase changes immediately. Recommendations in the app adjust automatically.

!!! warning "Phase transitions are irreversible"
    Once a plant has moved to the next phase, this transition cannot be undone. Check carefully whether the plant is genuinely ready before confirming.

---

## Batch Phase Transition for Entire Groups

If a plant belongs to an active planting run, it shares its phase with all other plants in that run — the phase is tracked at the run level, not per individual plant. A phase change therefore always affects **all** plants in the run at once; there is no option to select individual plants for a batch transition.

1. Open the relevant **Planting Run** under **Runs**.
2. Click **Batch Phase Change**.
3. Select the target phase (e.g. "Vegetative" → "Flowering").
4. Confirm — all plants in the run transition together.

More information: [Planting Runs](planting-runs.md)

### Why plants in a run can't be transitioned individually

As long as a plant belongs to an active or planned planting run, a direct phase change on that individual plant is blocked — the app reports a conflict in this case (error code `phase.run_owned`). The reasoning: the run and the individual plant should not drift apart. If you want to develop a plant independently of the group, detach it from the run first (see [Detaching Individual Plants from a Run](planting-runs.md#detaching-individual-plants-from-a-run)) and then change its phase individually.

---

## Phase Profiles and Recommendations

Each phase has its own resource profile. When you open the detail view of a phase (tab **Growth Phases** → click a phase), you see the target values:

### VPD Target (Vapor Pressure Deficit)

The Vapor Pressure Deficit (VPD) describes how strongly the air draws moisture from the leaves. Too high causes drought stress; too low promotes mould.

| Phase | VPD Target |
|-------|-----------|
| Germination / Seedling | 0.4–0.8 kPa |
| Vegetative | 0.8–1.2 kPa |
| Flowering | 1.0–1.5 kPa |

### Photoperiod

The day length (hours of light per day) controls the transition to flowering in many plants.

| Phase | Typical Photoperiod (short-day plants) |
|-------|---------------------------------------|
| Vegetative | 18/6 (18 h light, 6 h dark) |
| Flower induction | 12/12 (12 h light, 12 h dark) |

!!! tip "Automatic flower induction"
    For plants with defined phase data and a site with GPS coordinates, flowering can be triggered photoperiodically (see [Automatic Phase Transitions](#automatic-phase-transitions)).

### NPK Profile (Nutrient Ratio)

The nitrogen-phosphorus-potassium ratio changes across phases:

- **Vegetative**: High nitrogen (N) for leaf growth
- **Flowering**: Less nitrogen, more phosphorus (P) and potassium (K)
- **Late flowering**: Minimal nitrogen, high PK share

---

## Perennial Plants: Dormancy and Seasonal Cycles

Perennial plants (houseplants, berry bushes, fruit trees) use a recurring phase sequence instead of a single lifecycle ending in harvest — they go through dormancy, sprouting, growth, and flowering in a yearly loop.

### Activating the Dormancy Phase

1. Open the plant and navigate to **Growth Phases**.
2. Click **Enter Dormancy** (visible for perennial plants).
3. Confirm the start date of the rest phase.

During dormancy:
- Fertilization recommendations are suspended
- Watering intervals are extended
- Seasonal tasks appear (e.g. "Apply winter protection")

### Returning from Dormancy

Click **Resume Growth**. Kamerplanter resets the cycle to the vegetative phase (or sprouting, depending on the assigned sequence) and reactivates all recommendations.

---

## Frequently Asked Questions

??? question "What happens if I trigger the phase transition too early?"
    Recommendations adapt to the new phase immediately. Since transitions cannot be reversed it is worth being patient and observing the plant carefully. Notes on the transition help with later analysis.

??? question "Can I define custom phases?"
    Yes. Under **Phases → Phase Definitions** (`/phasen/definitionen`) you create your own phase types, and under **Phases → Phase Sequences** (`/phasen/ablaeufe`) you combine them into a custom sequence for one or more species.

??? question "Does Kamerplanter show when a plant is ready to harvest?"
    Kamerplanter does not calculate an automatic harvest date itself. Instead, you record ripeness observations (e.g. trichome colour, pistil colour, estimated days to harvest) — the app collects these in the plant's ripeness history as a decision aid. The final decision is yours. More information: [Harvest](harvest.md).

??? question "What is the difference between flushing and dormancy?"
    **Flushing** is a pre-harvest phase where nutrient supply is reduced before the plant is harvested. **Dormancy** is the natural rest phase of perennial plants in winter. Both are distinct phase types and are mutually exclusive within a sequence.

---

## See Also

- [Master Data: Plant Species](plant-management.md)
- [Fertilization](fertilization.md)
- [Harvest](harvest.md)
- [Planting Runs](planting-runs.md)
