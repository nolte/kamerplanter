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

1. Select a species from the dropdown. Kamerplanter shows two cards: **Compatible Species** and **Incompatible Species**.
2. Click **Add Compatibility**, choose the partner species, and assign a **score** between 0.1 (weak) and 1.0 (strong) — this is the compatibility score, such as the 0.9 score used for tomato and basil.
3. Click **Add Incompatibility**, choose the partner species, and enter a short **reason** (e.g. "allelopathy").

!!! note "Family-level fallback"
    If no entry exists yet for a specific species pair, Kamerplanter automatically looks for a matching compatibility at the **family level** when you request a recommendation. Such a fallback match is reduced by 20% in score (score × 0.8) and marked "family level" instead of "species level".

!!! info "Who maintains this data?"
    Compatibility and incompatibility entries are global master data, visible to all users. They are therefore maintained by **platform admins** — a corresponding permission guard for the underlying interface is currently being added. You can still record your own, plant-specific observations independently in the plant diary, once a user interface for it is available (see [Planting Runs: Plant Diary](../user-guide/planting-runs.md#plant-diary-currently-api-only)).

<!-- Source: src/frontend/src/pages/stammdaten/CompanionPlantingPage.tsx, src/backend/app/api/v1/companion_planting/router.py -->

---

## Automatic Check When Creating a Plant (Slot Neighborhood)

When you create a **single plant** via **Plants → Plant Instances → New Plant** and assign it a **slot**, Kamerplanter automatically checks the directly adjacent slots:

- If an **incompatible** species is already planted there, Kamerplanter rejects the creation with an error message.
- If a **compatible** species is planted there, this is recorded internally as a benefit.

!!! warning "Does not apply to plants from a planting run"
    The neighborhood check currently only applies when you create a plant individually via the **Plant Instances** master-data page. When plants are created automatically from a [planting run's](../user-guide/planting-runs.md) entries, **no** compatibility check takes place.

<!-- Source: src/backend/app/domain/engines/companion_planting_engine.py, src/backend/app/domain/services/plant_instance_service.py -->

---

## Crop Rotation

Crop rotation means deliberately alternating botanical families on a slot over the years — this prevents one-sided nutrient depletion and the buildup of family-specific pests and diseases in the soil.

### Maintaining successor master data

- Navigation: **Master Data → Crop Rotation**. Alternatively, on the species detail page: the **Crop Rotation** tab ("Expert" experience level), pre-selected with that species' family.

1. Select a **source family**. Kamerplanter shows the already recorded **successor families**.
2. Click **Add Successor**, choose the target family, and enter the **wait time in years** (1–10). This is how long to wait before a plant of the source family is grown on the same slot again.

### Automatic check

When you create a **single plant** with a slot, Kamerplanter also checks that slot's planting history over a default period of **3 years**:

| Result | Meaning |
|--------|---------|
| **Critical** (blocks creation) | The same botanical family was already grown on the same slot within the last 3 years |
| **Warning** | The planned family shares a high pest/disease risk with a family previously grown there |
| **Positive** | The planned family is recorded as a recommended successor of a family previously grown there (including a nitrogen-benefit note for nitrogen-fixing predecessors) |
| **No indication** | No matching data available for this combination |

A critical result blocks the plant's creation with an error message. As with the companion-planting check, this only applies to individually created plants, not to those created automatically from a planting run.

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
    The user interface for this (**Master Data → Companion Planting**) is open to all users; however, maintenance is intended for **platform admins**, since the data applies globally across all tenants. You should record your own, plant-specific observations in the plant diary instead.

## See Also

- [Planting Runs](../user-guide/planting-runs.md)
- [Locations & Substrates](../user-guide/locations-substrates.md)
- [Master Data: Plant Species](../user-guide/plant-management.md)
- [Pest Management (IPM)](../user-guide/pest-management.md)
- [GDD Calculation](gdd-calculation.md)
