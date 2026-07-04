# Care Reminders

Kamerplanter automatically reminds you which plants need water, fertiliser, or other care today — without needing to know cron expressions or workflow templates. A single tap is enough to confirm. The system learns from your care behaviour and adjusts intervals automatically.

---

## Prerequisites

- At least one plant is created
- The plant instance has a care profile assigned (created automatically on first access)

---

## Care Reminders in the Task Area

Care reminders do not have their own menu entry — they appear together with your other tasks under **Tasks** (`/aufgaben/queue`). Choose **Care** in the **Source** filter to see only automatic care reminders.

Cards are sorted by urgency and colour-coded:

| Colour | Meaning |
|--------|---------|
| Red | Overdue |
| Orange | Due today |
| Yellow | Due soon (within the next 1–2 days) |

!!! note "No green state"
    Recently cared-for plants do not produce a card at all — they only reappear once a reminder is due soon, due today, or overdue. There are therefore only the three urgency levels listed above, no per-plant "all good" indicator.

### Confirming Care

Every care card offers three actions:

1. **Edit** (pencil icon) — opens this plant's care profile.
2. **Done** (checkmark icon) — confirms the care. The system records the time and calculates the next appointment.
3. **Later** (snooze icon) — postpones the reminder by one day by default, without changing the time of your last confirmation.

!!! tip "Adaptive learning"
    If you consistently water a plant 8 instead of 7 days after the last confirmation, the system adjusts the interval automatically after 3 consecutive confirmations. The learning effect is limited to ±1 day per step and can change the interval by a maximum of ±30 % relative to the base interval.

---

## Care Profiles

Each plant has a **care profile** with the care intervals for that specific plant. The profile is automatically generated from the species or botanical family master data and can be adjusted afterwards.

### Opening a Care Profile

1. Navigate to **Plants** > desired plant
2. Click the **Care** tab
3. Click **Edit Care Profile**

In the edit dialog you enable or disable each reminder type individually (toggle) and adjust its interval with a slider; for watering you additionally choose the watering method, for fertilizing the active months.

### Care Style Presets

The system knows predefined care styles for typical houseplant groups. Use the **Care Style** field in the edit dialog to choose one of the following nine presets — the base values apply to summer; in winter the watering interval is multiplied by the winter factor:

<!-- Source: src/backend/app/domain/engines/care_reminder_engine.py (CARE_STYLE_PRESETS) -->

| Care Style | Watering Interval (Summer) | Winter Factor | Watering Method | Typical Plants |
|------------|------------------------------|----------------|------------------|----------------|
| Tropical (`tropical`) | Every 7 days | 1.5× | Top watering | Monstera, Philodendron, Ficus |
| Succulent (`succulent`) | Every 14 days | 3.0× | Drench & drain | Echeveria, Haworthia, Aloe |
| Orchid (`orchid`) | Every 7 days | 2.0× | Soak | Phalaenopsis, Dendrobium |
| Calathea (`calathea`) | Every 5 days | 1.5× | Bottom watering | Calathea, Maranta, Ctenanthe |
| Tropical Herbs (`herb_tropical`) | Every 5 days | 1.5× | Top watering | Basil, Mint, Coriander |
| Mediterranean (`mediterranean`) | Every 10 days | 2.0× | Drench & drain | Rosemary, Lavender, Thyme |
| Fern (`fern`) | Every 4 days | 1.5× | Top watering | Nephrolepis, Adiantum, Asplenium |
| Cactus (`cactus`) | Every 21 days | 4.0× | Drench & drain | Cacti (Cactaceae) |
| Custom (`custom`) | Starts at 7 days, freely adjustable | Starts at 1.5×, freely adjustable | Freely selectable | — |

!!! warning "Not all succulents are cacti"
    Cacti (Cactaceae) and succulents like Echeveria or Haworthia belong to different families. The `cactus` care style applies only to true cacti. Echeveria and Haworthia use `succulent`. Lithops and other Mesembs (Aizoaceae) require even more specific logic and should be configured with `custom`.

!!! info "Water quality"
    For Calatheas and Orchids the system recommends rainwater or filtered water — these plants are sensitive to lime in tap water (brown leaf tips).

---

## Automatic Reminder Types

Kamerplanter generates reminders for the following six care tasks:

<!-- Source: src/backend/app/domain/engines/care_reminder_engine.py (ReminderType, should_generate_reminder) -->

| Reminder Type | Trigger |
|---------------|---------|
| **Watering** | Interval since last confirmation, seasonally adjusted |
| **Fertilizing** | Interval + only within the care style's active months, only if a nutrient plan is assigned |
| **Repotting** | Months since last repotting |
| **Pest Check** | Fixed interval (varies by care style, default 14 days) |
| **Location Check** | Optionally enabled, can be restricted to specific months |
| **Humidity Check** | Optionally enabled, fixed interval |

Automatically created care tasks start with priority "Medium"; if a reminder is already overdue, the resulting task is created with priority "High".

### Why a Reminder Might Not Appear

The most common reason for a "missing" reminder is one of the following:

- **Active watering schedule**: If the plant already has an active automatic watering schedule via a planting run, Kamerplanter suppresses additional manual watering and fertilizing reminders for that plant.
- **Nutrient plan requirement**: Fertilizing reminders only occur if a nutrient plan is assigned to the plant — regardless of care style.
- **Dormant phase**: If the plant is in a dormant phase (winter dormancy, senescence, hardening-off, acclimatization, repotting recovery), all reminders except pest check are suppressed.
- **Active months**: If the current month is outside the care style's active months (e.g. November–February for most houseplants), no fertilizing reminder is generated.
- **On/off toggles**: Each reminder type can be individually disabled in the care profile.

!!! tip "Why no fertiliser in winter?"
    With reduced light in winter, the photosynthesis rate drops. Houseplants cannot absorb nutrients — fertiliser accumulates as salt in the substrate and damages the roots.

---

## Seasonal Adjustment

The system automatically adjusts watering intervals to the season:

- **Northern hemisphere**: Winter = December–February
- **Southern hemisphere**: Winter = June–August

The effective watering interval during winter months is calculated as:

```
Effective interval = base interval × winter factor
```

!!! example "Example: Monstera in winter"
    - Base interval (summer): 7 days
    - Winter factor (`tropical`): 1.5×
    - Effective interval (winter): 10–11 days

---

## Overwintering Management

!!! warning "Not yet implemented"
    A winter hardiness traffic light (colour rating based on frost sensitivity and climate zone), frost-forecast-driven reminders, and a tuber-cycle tab will be available in a future version. Five related reminder types (deadheading, tuber digging, storage check, spring uncovering, winter protection) already exist as a data model, but do not yet generate reminders — the evaluation logic is missing.

    For frost-tender outdoor plants you currently need to plan digging and storage dates yourself in the calendar or as a custom [task](tasks.md).

---

## Outdoor Care Styles

In addition to the nine houseplant styles, the data model knows ten outdoor presets:

<!-- Source: src/backend/app/domain/engines/care_reminder_engine.py (CARE_STYLE_PRESETS) -->

| Care Style | Watering Interval (Summer) | Winter Factor | Fertilizing Active | Typical Plants |
|------------|------------------------------|----------------|---------------------|-----------------|
| `outdoor_annual_veg` | Every 3 days | 1.0× | April–September | Outdoor vegetables (annual) |
| `outdoor_perennial` | Every 5 days | 2.0× | March–September | Perennials |
| `outdoor_annual_ornamental` | Every 3 days | 1.0× | April–September | Pansy, geranium, lobelia |
| `fruit_tree` | Every 14 days | 1.0× | March–May | Apple, pear, cherry |
| `berry_shrub` | Every 7 days | 1.0× | March–June | Raspberry, currant, gooseberry |
| `rose` | Every 7 days | 1.5× | April–July | Bed, shrub, and climbing roses |
| `frost_tender_tuber` | Every 5 days | 5.0× | May–August | Dahlia, gladiolus, canna |
| `frost_tender_container` | Every 5 days | 4.0× | April–September | Oleander, citrus, olive |
| `winter_vegetable` | Every 7 days | 2.0× | August–September | Kale, lamb's lettuce, winter purslane |
| `spring_bulb` | Every 14 days | 1.0× | March–May | Tulip, daffodil, crocus |

!!! info "Selectable only via the API"
    These ten outdoor presets are currently **not** available in the "Care Style" selector of the care profile dialog — the UI only offers the nine houseplant styles from the table above. Likewise, automatic family-based assignment (see below) never assigns an outdoor style to a plant. An outdoor preset can currently only be set via the technical API.

---

## Family-Based Care Assignment

The system knows the care requirements of 10 plant families and automatically assigns new plants to the matching care style:

<!-- Source: src/backend/app/domain/engines/care_reminder_engine.py (FAMILY_CARE_MAP) -->

| Family | Auto Style |
|--------|-----------|
| Araceae (arums) | `tropical` |
| Marantaceae (prayer plants) | `calathea` |
| Orchidaceae (orchids) | `orchid` |
| Cactaceae (cacti) | `cactus` |
| Crassulaceae (stonecrops) | `succulent` |
| Asphodelaceae (asphodels) | `succulent` |
| Polypodiaceae (polypody ferns) | `fern` |
| Lamiaceae (mints) | `herb_tropical` |
| Oleaceae (olive family) | `mediterranean` |
| Moraceae (fig family) | `tropical` |

For all unlisted families the fallback style `tropical` applies, unless a species-specific watering guide is available.

!!! tip "Automatic assignment"
    When you create a new plant instance, the system automatically assigns the matching care style based on the botanical family. You can override the style manually at any time.

---

## Frequently Asked Questions

??? question "The reminder appears too late — can I adjust this?"
    Yes. Open the plant's care profile and reduce the interval using the slider. Alternatively, the system will recognise the pattern after a few confirmations and adjust the interval automatically.

??? question "I forgot to water a plant — how do I reset the counter?"
    Confirm the care manually via **Done** in the task overview (Source "Care"). The system resets the time to "now", regardless of when the last confirmation was.

??? question "Why am I not getting a fertilising reminder for my Monstera in December?"
    That is correct — Monstera (`tropical`) has an active fertilising period of March–September. In December this period has ended, as houseplants cannot absorb nutrients in winter with reduced light.

??? question "What is the difference between \"Later\" and \"Skip\"?"
    "Later" (snooze) postpones a care reminder by one day without changing the time of your last confirmation — the reminder reappears the next day. There is currently no "Skip" action for care reminders like there is for regular tasks; use "Later" instead, or confirm the care as usual.

---

## See Also

- [Tasks](tasks.md)
- [Planting Runs](planting-runs.md)
- [Growth Phases](growth-phases.md)
- [Calendar](calendar.md)
