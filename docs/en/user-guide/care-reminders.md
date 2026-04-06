# Care Reminders

Kamerplanter automatically reminds you which plants need water, fertiliser or care today — without needing to know cron expressions or workflow templates. A single tap is enough to confirm. The system learns from your care behaviour and adjusts intervals automatically.

---

## Prerequisites

- At least one plant is created
- The plant instance has a care profile assigned (created automatically on first access)

---

## The Care Dashboard

Navigate to **Care** > **Due Today** to see all plants that need attention today. Cards are sorted by urgency:

| Colour | Meaning |
|--------|---------|
| Red | Overdue (plant may be suffering) |
| Orange | Due today |
| Yellow | Due soon (1–2 days) |
| Green | Recently cared for |

### Confirming Care

1. Click on the care card for the plant
2. Click the large **Done** button
3. That is it — the system records the time and calculates the next appointment

!!! tip "Adaptive learning"
    If you consistently water a plant 8 instead of 7 days after the last confirmation, the system adjusts the interval automatically after 3 consecutive confirmations. The learning effect is limited to ±1 day per step and can change the interval by a maximum of ±30%.

---

## Care Profiles

Each plant has a **care profile** with the care intervals for that specific plant. The profile is automatically generated from the species master data and can be adjusted afterwards.

### Opening a Care Profile

1. Navigate to **Plants** > desired plant
2. Click the **Care** tab
3. Click **Edit Care Profile**

### Care Style Presets

The system knows predefined care styles for typical plant groups:

| Care style | Watering (summer) | Winter factor | Typical plants |
|------------|------------------|---------------|----------------|
| `tropical` | Every 7 days | 1.5× | Monstera, Philodendron, Ficus |
| `succulent` | Every 14 days | 2.5× | Echeveria, Haworthia, Aloe |
| `orchid` | Every 7 days (soaking) | 1.5× | Phalaenopsis, Dendrobium |
| `calathea` | Every 5 days | 1.3× | Calathea, Maranta, Ctenanthe |
| `herb_tropical` | Every 3 days | 1.5× | Basil, Mint, Coriander |
| `mediterranean` | Every 10 days | 2.0× | Rosemary, Lavender, Thyme |
| `fern` | Every 4 days | 1.3× | Nephrolepis, Adiantum, Asplenium |
| `cactus` | Every 21 days | 3.0× | Cacti (Cactaceae) |
| `custom` | Freely configurable | Free | — |

!!! warning "Not all succulents are cacti"
    Cacti (Cactaceae) and succulents like Echeveria or Haworthia belong to different families. The `cactus` care style applies only to true cacti. Echeveria and Haworthia use `succulent`. Lithops and other Mesembs (Aizoaceae) require even more specific logic and should be configured with `custom`.

### Watering Instructions

The care profile shows not just *when* but also *how* to water:

| Care style | Watering method |
|------------|----------------|
| `tropical` | Water from above until water drains from the bottom. Empty the saucer after 30 min. |
| `orchid` | Soak: place pot in lukewarm water for 10–15 min, then let drain. |
| `calathea` | Water from above with low-lime water. Do not wet the leaves. |
| `cactus` | Water thoroughly, let dry completely before the next watering. |

!!! info "Water quality"
    For Calatheas and Orchids the system recommends rainwater or filtered water — these plants are sensitive to lime in tap water (brown leaf tips).

---

## Automatic Reminder Types

The system generates daily reminders for the following care tasks:

| Reminder type | Trigger | Priority |
|---------------|---------|---------|
| **Watering** | Interval since last confirmation | High |
| **Fertilising** | Interval + only in active months | Medium |
| **Repotting** | Months since last repotting | Low |
| **Pest check** | Fixed interval (default: 14 days) | Medium |
| **Location check** | Seasonal: October + March | Medium |
| **Humidity check** | Heating period (Oct–Mar) | Medium |
| **Winter protection** | October (northern hemisphere) | High |
| **Spring uncovering** | March (northern hemisphere) | High |
| **Tuber digging** | Before first frost (October) | Critical |

### Fertilising Guard (Dormancy Guard)

Fertilising reminders are **not** generated if:
- The current month is outside the `active months` of the care style (e.g. November–February for most houseplants)
- The plant is in a dormant phase (winter dormancy, senescence, hardening-off phase)

!!! tip "Why no fertiliser in winter?"
    With reduced light in winter, the photosynthesis rate drops. Houseplants cannot absorb nutrients — fertiliser accumulates as salt in the substrate and damages the roots.

---

## Seasonal Adjustment

The system automatically adjusts watering intervals to the season:

- **Northern hemisphere**: Winter = November–February, Summer = May–August
- **Southern hemisphere**: Winter = May–August, Summer = November–February

The hemisphere is derived from the plant's location (`Site.hemisphere`). The effective watering interval is calculated as:

```
Effective interval = base interval × winter factor
```

!!! example "Example: Monstera in winter"
    - Base interval (summer): 7 days
    - Winter factor (`tropical`): 1.5×
    - Effective interval (winter): 10–11 days

---

## Overwintering Management

For plants that need winter protection, Kamerplanter provides a complete overwintering system.

### Winter Hardiness Traffic Light

Each plant receives a colour rating based on its frost sensitivity and your climate zone:

| Light | Meaning | Typical plants |
|-------|---------|----------------|
| Green | Frost-hardy — no protection needed | Gooseberry, apple tree, tulips |
| Yellow | Needs protection — mulch or fleece | Roses, lavender, perennials |
| Red | Must overwinter frost-free | Oleander, citrus, dahlias |

!!! warning "Dahlias and tubers"
    Dahlias, gladioli and canna must be dug up before the first frost. The system sends a **critical reminder** with the tuber-digging notice as soon as the temperature forecast indicates frost.

### Tracking the Tuber Cycle

For plants with tubers or bulbs (dahlias, gladioli, canna, tulips) you can document the complete annual cycle:

1. Plant out → Bloom → Dig up → Dry → Store → Inspect → Pre-grow

Navigate to **Plants** > desired plant > **Overwintering** tab to manage the status.

### Outdoor Care Styles

In addition to houseplant styles, there are presets for outdoor plants:

| Care style | Winter action | Typical plants |
|------------|--------------|----------------|
| `outdoor_perennial` | Check winter protection (mulch, fleece) | Larkspur, Phlox, perennials |
| `frost_tender_tuber` | DIG UP + store frost-free | Dahlia, Gladiolus, Canna |
| `frost_tender_container` | Move to winter quarters (5–12°C, bright) | Oleander, Citrus, Olive |
| `fruit_tree` | Lime wash, trunk protection | Apple, Pear, Cherry |
| `spring_bulb` | Leave in ground (frost-hardy) | Tulip, Narcissus, Crocus |

---

## Family-Based Care Assignment

The system knows the care requirements of 10 plant families and automatically assigns new plants to the matching care style:

| Family | Auto style |
|--------|-----------|
| Araceae (arums) | `tropical` |
| Cactaceae (cacti) | `cactus` |
| Marantaceae (prayer plants) | `calathea` |
| Orchidaceae (orchids) | `orchid` |
| Crassulaceae (stonecrops) | `succulent` |
| Asphodelaceae (asphodels) | `succulent` |
| Lamiaceae (mints) | `mediterranean` |
| Polypodiaceae / Pteridaceae (ferns) | `fern` |
| Liliaceae / Amaryllidaceae (lilies) | `outdoor_perennial` |
| Solanaceae (nightshades) | `outdoor_annual_veg` |

!!! tip "Automatic assignment"
    When you create a new plant instance, the system automatically assigns the matching care style based on the botanical family. You can override the style manually at any time.

---

## Frequently Asked Questions

??? question "The reminder appears too late — can I adjust this?"
    Yes. Open the plant's care profile and reduce the interval. Alternatively, the system will recognise the pattern after a few confirmations and adjust the interval automatically.

??? question "I forgot to water a plant — how do I reset the counter?"
    Confirm the care manually in the care dashboard. The system resets the timer to "now", regardless of when the last confirmation was.

??? question "Why am I not getting a fertilising reminder for my Monstera in December?"
    That is correct — Monstera (care style: `tropical`) has an active fertilising period of March–October. In December this period has ended, as houseplants cannot absorb nutrients in winter with reduced light.

??? question "My dahlia has a green traffic light — but I know it needs protection."
    The light is calculated from the `frost_sensitivity` value of the species AND your climate zone. Check whether the correct climate zone is set for your location. You can also manually set the care style to `frost_tender_tuber`.

---

## See Also

- [Planting Runs](planting-runs.md)
- [Growth Phases](growth-phases.md)
- [Locations & Substrates](locations-substrates.md)
- [Calendar](calendar.md)
