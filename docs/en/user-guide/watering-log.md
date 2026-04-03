# Watering Log

The watering log (WateringLog) is the central, unified record of all irrigation events in Kamerplanter. It combines both manually entered and automatically captured watering events, giving you a complete overview of your plants' irrigation history — as the basis for informed decisions about nutrient planning and substrate management.

---

## Prerequisites

- At least one planting run or plant configured
- Assigned substrate (recommended, for substrate moisture tracking)

---

## Distinction: WateringLog, WateringEvents, and FeedingEvents

Kamerplanter distinguishes three related concepts:

| Term | Description | Typical trigger |
|------|-------------|----------------|
| **WateringEvent** | A single irrigation event — timestamp, volume, source | Manual entry or watering schedule confirmation |
| **FeedingEvent** | A fertilization/irrigation event with nutrient data (EC, pH, dosages) | Fertilization according to a nutrient plan (REQ-004) |
| **WateringLog** | Unified log — aggregates WateringEvents and FeedingEvents in a single view | Aggregated automatically |

!!! note "Difference from FeedingEvents"
    FeedingEvents document irrigations where fertilizer was added — with the full nutrient profile (target EC, target pH, product dosages). The WateringLog shows both types side by side, so you can follow the irrigation history without switching context.

---

## Opening the Watering Log

1. Navigate to a **planting run** or **plant**.
2. Click the **Watering Log** (or **Irrigation**) tab.
3. The log view shows all irrigation events in chronological order.

!!! info "Screenshot pending"
    This screenshot will be added in a future version.

---

## What the Watering Log Displays

Each entry shows the following information:

| Field | Description |
|-------|-------------|
| **Date & Time** | Timestamp of the irrigation event |
| **Volume (liters)** | Irrigation volume in liters |
| **EC** | Electrical conductivity of the nutrient solution (if fertilizer was used) |
| **pH** | pH of the irrigation solution (if recorded) |
| **Type** | `Irrigation` or `Fertilization` |
| **Source** | Manual, watering schedule, automatic |
| **Note** | Optional free-text annotation |

---

## Entering a Watering Event Manually

1. Click **New Watering Event**.
2. Enter the volume and timestamp.
3. Optionally add EC, pH, and a note.
4. Click **Save**.

!!! tip "Use a watering schedule"
    If you have configured a watering schedule (WateringSchedule) for your planting run, Kamerplanter automatically creates tasks for due irrigations. Confirming these tasks automatically records the events in the log — no manual entry required.

---

## Watering Log and Nutrient Planning

The WateringLog is closely integrated with the fertilization logic (REQ-004):

- **EC trend** across multiple irrigation events is visible as a mini-chart in the log view (when data is available).
- **Flush detection**: When EC and pH are recorded, Kamerplanter can automatically flag flushing events.
- **Runoff analysis**: When runoff EC is recorded, nutrient accumulation in the substrate can be detected.

---

## Frequently Asked Questions

??? question "Are automatic irrigations (Home Assistant) also logged?"
    Yes. When Kamerplanter receives irrigation data via the Home Assistant integration, it is automatically recorded as WateringEvents in the log — with the source set to `automatic`.

??? question "How long are watering log entries retained?"
    Watering log entries are stored according to the data retention policy (NFR-011). By default, raw entries are kept for 90 days, after which they are consolidated into daily aggregates.

??? question "Can I correct entries in the log after the fact?"
    Yes. Click an entry and select **Edit**. Changes are recorded with a timestamp.

---

## See Also

- [Fertilization Logic](fertilization.md) — Nutrient plans and FeedingEvents (REQ-004)
- [Planting Runs](planting-runs.md) — Configuring a watering schedule
- [Tank Management](tanks.md) — Irrigation tanks and fills
