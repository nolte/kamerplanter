# Watering Log

The Watering Log (WateringLog) is the central place where you document every watering and feeding session — whether plain irrigation or fertilization with nutrients. It replaces the earlier, separate models for irrigation and feeding events with a single entry type, giving you a complete history per plant, slot, or location.

---

## Prerequisites

- At least one plant **or** slot to assign the entry to (at least one of the two is required)

---

## A Note on the Data Model

Earlier versions of Kamerplanter used two separate models: `WateringEvent` (plain irrigation) and `FeedingEvent` (fertilization with nutrient data). Both are marked **deprecated** and are being phased out.

`WateringLog` replaces both models with a single entry type that covers plain irrigation as well as fertilization — depending on whether you enter fertilizers and measurements or not. It does **not aggregate** multiple individual events into a summary; every entry in the log is a standalone, immutable record of a single watering or feeding action.

!!! note "Legacy feeding events view"
    The old "Feeding Events" overview (`FeedingEvent`) remains reachable for backward compatibility but is no longer linked from the navigation — it only shows historical legacy entries. New entries are created exclusively in the Watering Log.

---

## Opening the Watering Log

The Watering Log is a **dedicated top-level menu item** — it does not live under "Fertilization", since it covers both plain irrigation and fertilization.

1. Click **Watering Log** in the navigation.
2. The list view shows all entries, sorted by timestamp descending by default.

Alternatively, you can reach filtered views from a plant's, slot's, or location's detail page.

---

## What the List Shows

Each entry shows the following columns (some only appear when at least one entry has a value for them):

| Column | Description |
|--------|-------------|
| Timestamp | When the event was logged |
| Plants | Linked plants (up to 3 as chips, rest as a counter) |
| Application Method | Fertigation (automated nutrient delivery through irrigation, see [Nutrient Mixing](../guides/nutrient-mixing.md)), Drench (watering can), Foliar, or Top-Dress |
| Volume (L) | Amount of water used |
| Fertilizers Used | Names of the fertilizers used (only shown when fertilizers were used) |
| EC Before / EC After | Measured conductivity (only shown when recorded) |
| pH Before / pH After | Measured pH value (only shown when recorded) |
| Water Source | Tank, tap water, RO water, rainwater, distilled, or well water (only shown when recorded) |

---

## Logging a Watering Manually

1. Click **Log Watering**.
2. **Basics**:
    - Select plant(s) (multi-select) and/or enter slot keys (comma-separated)
    - Choose the **application method** (Fertigation, Drench, Foliar, Top-Dress)
    - Enter the **water source** (optional)
    - Enter the **volume (L)**
    - Mark the event as **supplemental** if needed (an additional watering round outside the regular schedule)
3. **Measurements**: Optionally enter EC and pH before and after watering.
4. **Runoff values**: Optionally enter runoff EC, runoff pH, and runoff volume (for runoff analysis).
5. **Fertilizers used**: Use **Add Fertilizer** to add any number of fertilizers with their ml/L dosage.
6. Optionally record who performed the event and a note.
7. Click **Save**.

!!! warning "Plants or slots are required"
    An entry must reference at least one plant or slot — otherwise it cannot be saved. Supplemental waterings (**supplemental** enabled) also cannot use the **Fertigation** application method at the same time.

### Logging from a delivery channel

If a nutrient plan phase entry is linked to a [delivery channel](fertilization.md#delivery-channels-multi-channel-delivery), you can log the watering directly from the channel — the form is then pre-filled with the channel's application method, target EC/pH, and fertilizer dosages.

---

## Viewing and Editing an Entry

Click an entry in the list to open its detail page. It shows two tabs:

- **Details**: Linked plants/slots, measurement and runoff values, fertilizers used, and — if present — who performed the event, the associated delivery channel, and the linked nutrient plan.
- **Edit**: All fields except the linked plants/slots can be corrected afterward.

The detail page also has an **"Analyze Runoff"** button that runs a runoff analysis for this entry (requires EC/pH/volume for both input and runoff). It assesses EC drift, pH drift, and runoff volume and returns an overall assessment plus per-metric messages — see [Runoff Analysis](../guides/nutrient-mixing.md#runoff-analysis) for the underlying thresholds.

---

## Suggested Watering Volume {#suggested-watering-volume}

For plants with a growth phase set, Kamerplanter automatically suggests a watering volume — shown as a chip on the plant detail page and pre-filled when you confirm a due watering task. The suggestion takes into account:

- for planting runs at an outdoor or greenhouse site with stored GPS coordinates, the daily calculated **irrigation demand**: Kamerplanter derives evapotranspiration (**ET₀** for short — how much water evaporates from soil and leaves due to sun, wind and temperature) from the weather data, weights it with a species-specific factor (**Kc**), and subtracts any rain that has already fallen. When this value is available, it replaces the phase-based amount below,
- otherwise the current **growth phase** (see [Watering Volume per Phase](growth-phases.md#watering-volume-per-phase)),
- the plant species' **waterlogging tolerance** as an upper bound,
- a **live soil-moisture sensor** configured at the location (see [Sensors](sensors.md)): if the soil is already wet, Kamerplanter automatically reduces the volume — even one already based on irrigation demand — and shows a hint about it.

The suggestion is non-binding — you can always enter a different volume when logging the watering.

!!! tip "The suggested amount can drop to 0 on rainy days"
    If the site has already had enough rain, the calculated irrigation demand for the day can drop to 0 — Kamerplanter then suggests no additional watering. This also affects the watering care reminder, see [Care Reminders: Why a Reminder Might Not Appear](care-reminders.md#why-a-reminder-might-not-appear).

---

## Frequently Asked Questions

??? question "Are automatic irrigations via Home Assistant logged?"
    No, not currently. There is currently no automatic import of Home Assistant irrigation events into the watering log — entries are created through manual entry, by confirming a watering schedule date, or by confirming a care reminder (watering/fertilizing).

??? question "How long are watering log entries retained?"
    There is currently no dedicated automatic consolidation or deletion period for the watering log — entries remain until you delete them manually or have your data erased under your GDPR data-subject rights.

??? question "Can I correct entries in the log after the fact?"
    Yes. Open the entry and switch to the **Edit** tab.

??? question "Do I have to record every watering?"
    No, it is optional. Kamerplanter works without complete documentation. If you want to track runoff EC or optimize nutrient delivery, thorough recording pays off.

---

## See Also

- [My Plant Doesn't Look Well — Symptom Diagnosis](plant-health-troubleshooting.md)
- [Fertilization](fertilization.md) — Nutrient plans and delivery channels <!-- REQ-004 -->
- [Planting Runs](planting-runs.md) — Configuring a watering schedule
- [Tank Management](tanks.md) — Irrigation tanks and fills
- [Guides: Mixing Nutrient Solutions](../guides/nutrient-mixing.md) — Runoff analysis thresholds
- [Growth Phases](growth-phases.md#watering-volume-per-phase) — phase-dependent watering and feeding rules
- [Weather Sources per Location](weather-sources.md) — prerequisite for the ET₀-based irrigation demand at outdoor and greenhouse sites
