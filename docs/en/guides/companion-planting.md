# Companion Planting & Crop Rotation

Kamerplanter helps you with two closely related growing decisions: **which plant species help or harm each other** (companion planting) and **which botanical family should follow which one on the same slot** (crop rotation). Both are managed through global master data and are partly checked automatically when you create a plant.

---

## Prerequisites

- Plant species with an assigned botanical family in master data
- For the automatic check: a location with slots set up

---

## What Is Companion Planting — and Why Does It Work?

Plants influence each other in various ways:

| Mechanism | Example | Effect |
|-----------|---------|--------|
| **Pest repellency** | Marigolds next to tomatoes | Nematodes repelled by root secretions |
| **Aromatic effect** | Basil next to tomatoes | Essential oils confuse whiteflies |
| **Nitrogen fixation** | Beans next to corn | Root bacteria fix atmospheric nitrogen |
| **Root zone use** | Onion + carrot | Different depths, no nutrient competition |
| **Shade effect** | Lettuce under tomatoes | Lettuce thrives in partial shade, soil stays moist |
| **Pollinator attraction** | Phacelia next to vegetable bed | Wild bees are attracted |

!!! tip "Companion planting is not a miracle cure"
    Companion planting supports your garden but does not replace good soil care,
    irrigation, and crop rotation. Treat it as one measure among several.

---

## Classic Combinations

### The Three Sisters (Corn, Beans, Squash)

One of the world's oldest companion planting systems — developed by the Haudenosaunee
(Iroquois):

```
Corn         → Climbing support for beans, shades squash soil
Beans        → Nitrogen fixation for corn and squash
Squash       → Large leaves shade the soil, retain moisture
```

Kamerplanter's master data marks all three pairings as compatible (corn + beans: 0.9 · corn + squash: 0.85 · beans + squash: 0.8). Set up a separate [planting run](../user-guide/planting-runs.md) for each of the three species at the same location — there is no dedicated "mixed culture" run type (see [What a Planting Run Is](../user-guide/planting-runs.md#what-is-a-planting-run)).

### Tomato & Basil

Probably the most well-known companion planting pair in greenhouse and outdoor growing:

- Basil acts as pest repellent (whitefly, aphids)
- Shared water needs and temperature requirements simplify care
- Both require a sunny location

**Compatibility score in Kamerplanter:** 0.9 (highly recommended)

### Carrot & Onion

Classic vegetable pairing (score 0.9):

- Onions and carrots use different soil layers
- Onion scent disrupts carrot fly oviposition
- Carrot foliage disrupts the onion fly

### Marigolds & Calendula as Universal Companions

Two flowers that can be used almost anywhere:

| Plant | Effect | Recommended neighbors |
|-------|--------|-----------------------|
| **Tagetes** (French marigold) | Nematodes, whiteflies, root secretions deter slugs | Tomatoes, peppers, lettuce |
| **Calendula** (pot marigold) | Aphid repellent, attracts beneficials (hoverflies, ladybugs) | Almost all vegetables |

!!! tip "Marigolds as bed border"
    Plant marigolds all around a vegetable bed as a living border. Even if you do not
    record data in Kamerplanter, the entire bed benefits from the protective effect.

### Herbs as Pest Control

| Herb | Effect |
|------|--------|
| Basil | Whitefly, aphids |
| Lavender | Mites, moths (scent) |
| Sage | Cabbage fly, caterpillars |
| Summer savory | Black bean aphid |
| Dill | Confuses carrot fly females; attracts hoverflies |
| Coriander | Repels aphids, attracts hoverflies |

---

## Bad Neighbors — What to Avoid

!!! danger "Fennel: The loner"
    Fennel is incompatible with nearly every other garden plant. It secretes allelopathic
    substances that inhibit the growth of tomatoes, peppers, bush beans, and lettuce.
    Plant fennel in its own bed or in a container at the edge of the garden.

| Incompatible pair | Reason | Recommendation |
|------------------|--------|---------------|
| Tomato + potato | Same Solanaceae family, shared diseases (late blight) | Keep at least 10 m apart |
| Fennel + tomato | Allelopathy from fennel secondary metabolites | Separate beds |
| Onion + peas | Growth inhibition of peas | Different bed sections |
| Potato + squash | Strong nutrient competition | Plan rotation accordingly |

<!-- Source: src/backend/app/migrations/seed_data/companion_planting.yaml -->

---

## Maintaining Compatibility Master Data

### Where to find it

- Navigation: **Master Data → Companion Planting** — global management, independent of a specific bed.
- Alternatively, directly on the species detail page: the **Companion Planting** tab (visible from the "Expert" experience level), pre-selected for that species.

### How it works

1. Open the **Select species** dropdown. For each species, Kamerplanter shows two counters before you even pick it: a green badge with the number of already recorded **compatible** species, and a red badge with the number of **incompatible** species. This lets you see at a glance which species already have companion-planting data, before you open them. A short legend below the field explains both colors. Species with no recorded relationships (0 compatible, 0 incompatible) are shown de-emphasized but remain fully selectable.
2. Select a species. Kamerplanter shows two cards: **Compatible Species** and **Incompatible Species**.
3. Click **Add Compatibility**, choose the partner species, and assign a **score** between 0.1 (weak) and 1.0 (strong) — this is the compatibility score, such as the 0.9 score used for tomato and basil.
4. Click **Add Incompatibility**, choose the partner species, and enter a short **reason** (e.g. "allelopathy").

!!! note "Family-level fallback"
    If no entry exists yet for a specific species pair, Kamerplanter automatically looks for a matching compatibility at the **family level** when you request a recommendation. Such a fallback match is reduced by 20% in score (score × 0.8) and marked "family level" instead of "species level".

!!! info "Who maintains this data?"
    Compatibility and incompatibility entries are global master data, visible to all users. Only **platform admins** may create or change them — regular user accounts still see the edit controls, but saving fails with an "Unauthorized" error. You can still record your own, plant-specific observations independently in the plant diary (see [Diary](../user-guide/plant-diary.md)).

<!-- Source: src/frontend/src/pages/stammdaten/CompanionPlantingPage.tsx, src/backend/app/api/v1/companion_planting/router.py -->

---

## Automatic Check When Creating a Plant (Slot Neighborhood)

Whenever a plant is assigned a **slot** — whether created individually via **Plants → Plant Instances → New Plant**, or in bulk while creating the plants of a [planting run](../user-guide/planting-runs.md) — Kamerplanter automatically checks the directly adjacent slots:

- If an **incompatible** species is already planted there, Kamerplanter rejects the creation with an error message.
- If a **compatible** species is planted there, this is recorded internally as a benefit.

!!! note "Planting runs are checked as a whole batch"
    When you create plants using the **Create Plants** button of a planting run (see [Planting Runs, Step 6](../user-guide/planting-runs.md)), Kamerplanter checks every slot-assigned plant individually, exactly as it does for a single plant. Unlike a single plant, though, a single conflict here blocks the creation of the **entire run** — as soon as one entry triggers an incompatibility, no plant of the run is created at all. Existing plants you bring into a run via **Adopt existing plants** do not go through this check again, since they do not receive a new slot assignment.

<!-- Source: src/backend/app/domain/engines/companion_planting_engine.py, src/backend/app/domain/services/plant_instance_service.py, src/backend/app/domain/services/planting_run_service.py (_validate_batch_planting) -->

---

## Crop Rotation

Crop rotation means deliberately alternating botanical families on a slot over the years — this prevents one-sided nutrient depletion and the buildup of family-specific pests and diseases in the soil.

### Maintaining successor master data

- Navigation: **Master Data → Crop Rotation**. Alternatively, on the species detail page: the **Crop Rotation** tab ("Expert" experience level), pre-selected with that species' family.

1. Above the family picker you'll find a **filter bar**: Favorites, Has rotation, Nitrogen-fixing, Frost-hardy, plus a dropdown for nutrient demand (Heavy Feeder / Medium Feeder / Light Feeder). Clear active filters again via **Reset filters**.
2. Open the **From Family** dropdown. For every botanical family, Kamerplanter already shows, before you even select it, how many recommended **successor families** are on record — a short legend below the field explains the number. Families without recorded successors are shown in a muted color but remain fully selectable. The star next to each family lets you mark it as a **favorite** (keyboard shortcut: Shift+F on the family currently highlighted in the dropdown); favorites then sort to the top of the list and can be shown in isolation via the **Favorites** filter.
3. Select a **source family**. Kamerplanter shows the already recorded **successor families**.
4. Click **Add Successor**, choose the target family, and enter the **wait time in years** (1–10). This is how long to wait before a plant of the source family is grown on the same slot again.

<!-- Source: src/frontend/src/pages/stammdaten/CropRotationPage.tsx, src/frontend/src/api/endpoints/cropRotation.ts, src/frontend/src/hooks/useFamilyFavorites.ts, src/backend/app/api/v1/crop_rotation/router.py -->

### Automatic check

Whenever a plant is assigned a slot — created individually or in bulk via a planting run's plant creation — Kamerplanter also checks that slot's planting history over a default period of **3 years**:

| Result | Meaning |
|--------|---------|
| **Critical** (blocks creation) | The same botanical family was already grown on the same slot within the last 3 years |
| **Warning** | The planned family shares a high pest/disease risk with a family previously grown there |
| **Positive** | The planned family is recorded as a recommended successor of a family previously grown there (including a nitrogen-benefit note for nitrogen-fixing predecessors) |
| **No indication** | No matching data available for this combination |

A critical result blocks the plant's creation with an error message. As with the companion-planting check, this applies equally to plants created in bulk through a planting run: a single critical conflict blocks the creation of the entire run.

<!-- Source: src/backend/app/domain/engines/crop_rotation_validator.py, src/backend/app/config/constants.py (DEFAULT_ROTATION_WINDOW_YEARS = 3) -->

---

## Frequently Asked Questions

??? question "What does 'allelopathy' mean?"
    Allelopathy describes the ability of plants to release chemical compounds that
    inhibit or promote the growth of neighboring plants. Fennel is the best-known
    example of negative allelopathy in the garden.

??? question "Does companion planting work in greenhouses and indoors?"
    Yes, with limitations. Aromatic pest repellency works indoors too. However, space
    is often limited, and some companions (e.g. tall marigold varieties) can hinder
    air circulation. The bundled compatibility data is compiled primarily for
    outdoor food crops.

??? question "Where does the compatibility data come from?"
    The bundled master data is based on established gardening references and
    recognized companion-planting recommendations. The interface currently does not
    show a source citation per individual entry.

??? question "Can I add my own compatibility pairs?"
    Only if you are a **platform admin** — the data applies globally across all tenants and is therefore write-protected for regular user accounts. You should record your own, plant-specific observations in the plant diary instead.

## See Also

- [Planting Runs](../user-guide/planting-runs.md)
- [Locations & Substrates](../user-guide/locations-substrates.md)
- [Master Data: Plant Species](../user-guide/plant-management.md)
- [Pest Management (IPM)](../user-guide/pest-management.md)
- [GDD Calculation](gdd-calculation.md)
