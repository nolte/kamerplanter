# Dashboard

!!! info "Partially implemented"
    The **care dashboard** (pending tasks, tank status) and **widget personalization** (choosing, arranging, and resizing widgets) are implemented. **Advanced analytics** (yield trends, sensor heatmaps, time-series charts) are planned but not yet built. <!-- REQ-009 -->

The dashboard is the home screen of Kamerplanter. It gives you a quick overview of your plants, upcoming tasks, active warnings, and key metrics — all at a glance without having to navigate through individual sections. You can fully [build your own selection of widgets](dashboard-personalization.md).

---

## Prerequisites

- At least one plant or an active planting run

---

## Opening the Dashboard

The dashboard opens automatically after logging in. You can reach it at any time via the Kamerplanter logo or the **Dashboard** navigation entry.

---

## Dashboard Sections at a Glance

### Active Plants and Growth Phase

The upper section shows an overview of all active plants with their current growth phase. Plants are color-coded by phase:

- Light green: Germination / Seedling
- Green: Vegetative phase
- Purple: Flowering phase
- Yellow: Harvest phase
- Grey: Dormancy (rest phase)

Click a plant to go directly to the plant detail page.

### Upcoming Tasks

The task block shows the next due tasks sorted by urgency:

- Overdue tasks appear in red at the top
- Tasks due today appear in orange
- Tasks for the next 7 days appear in the default color

Click a task to open it or mark it directly as complete.

!!! tip "Quick tick-off in the dashboard"
    For simple tasks such as "Watering confirmed" you can click the checkmark icon directly on the dashboard widget without opening the task.

### Warnings and Notices

The warning block shows active messages that need attention:

- **Red (critical)**: Harvest blocked by pre-harvest interval, sensor failed, tank empty
- **Orange (warning)**: Overdue tasks, EC outside target range, probe calibration due
- **Blue (info)**: Recommendations, notices about upcoming phase transitions

Click a warning to go directly to the affected area.

### Tank Quick Overview

If you have tanks configured, the dashboard shows the current state of your tanks:
- Fill level in % or litres
- Current EC value (with traffic-light indicator: green = in target range, yellow = deviation, red = outside range)
- pH value (with traffic-light indicator)
- Next water change

### Weather Forecast and Frost Early-Warning {#weather-forecast-and-frost-early-warning}

If you've set up a [weather source](weather-sources.md) for one of your outdoor or greenhouse sites, the **Weather forecast** widget shows its daily forecast: minimum and maximum temperature per day, each with the [provenance label](weather-sources.md#understanding-weather-data-provenance) of the underlying source (e.g. Open-Meteo, DWD, or your Home Assistant weather station). If you manage several sites, the widget shows the first site with stored GPS coordinates and a configured source; the site name is shown alongside it.

If a frost night is expected for that site within the forecast window, a prominently highlighted **frost early-warning** also appears, with the expected date and the predicted minimum temperature — before the temperature has actually dropped. Kamerplanter also actively informs you about the same frost night via [notification](notifications.md#frost-early-warning).

!!! tip "Early warning instead of a reaction"
    This early warning complements the existing, reactive frost signal, which is based on a currently measured temperature (e.g. from a sensor or Home Assistant) — it additionally protects you from noticing an upcoming frost night only once it's already too late to take protective measures.

Without a configured weather source, without stored GPS coordinates for the site, or as long as your operator hasn't enabled the weather forecast feature, the widget instead shows a hint with a link to the site setup.

---

## Care Reminders Dashboard

Alongside the main dashboard there is a dedicated **Care View** that groups your plants by urgency of the next care action:

- **Immediate**: Plants whose care interval expires today or has already passed
- **Today**: Plants that need attention today
- **This Week**: Plants with care needs in the next 7 days
- **No Need**: Plants with no planned care action in the near future

This view is especially useful for people with many houseplants who want to see quickly which plant needs water or fertilizer today.

---

## Dashboard Adaptation by Experience Level

The dashboard adapts to your experience level (configurable under **Account → Settings → Experience Level**):

**Beginner:**
- Simplified view focusing on care tasks
- No technical metrics (EC, VPD)
- Friendly phrasing ("Your tomatoes need water")

**Intermediate:**
- All care tasks plus tank status
- EC and pH as numbers (without deep analysis)
- Harvest forecasts

**Expert:**
- Full metrics view
- VPD display with target range
- Yield trends and comparisons

!!! tip "Show all fields"
    At any experience level you can toggle **"Show All Fields"** (top right on the dashboard) to temporarily switch to the full view without permanently changing your experience level.

---

## Frequently Asked Questions

??? question "Why do I see no sensor data on the dashboard?"
    Sensor data appears on the dashboard only when at least one sensor is configured and active. If you have no smart home integration, use manual measurements — these appear on the dashboard too, labelled "Manual".

??? question "Can I customize the dashboard or rearrange widgets?"
    Yes. Using the **Settings → Dashboard** tab or the **Edit** mode directly on the dashboard, you can choose widgets, arrange them via drag-and-drop (or via keyboard-operable buttons), and resize them. See [Personalizing Your Dashboard](dashboard-personalization.md) for details.

??? question "Why do some plants not appear on the dashboard?"
    The dashboard shows only **active** plants (not completed, not removed). Plants in a completed planting run no longer appear. If an active plant is missing, check that it is in the correct tenant.

---

## See Also

- [Personalizing Your Dashboard](dashboard-personalization.md) — choose, arrange, and configure widgets
- [Tasks](tasks.md)
- [Calendar](calendar.md)
- [Tank Management](tanks.md)
- [Sensors](sensors.md)
- [Weather Sources per Location](weather-sources.md) — set up the source for the "Weather forecast" widget
- [Notifications](notifications.md#frost-early-warning) — frost early-warning as an active notification
