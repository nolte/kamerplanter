# Calendar

The calendar shows all planned and past activities in one central view: tasks, phase transitions, watering forecasts, Integrated Pest Management (IPM) appointments, harvests, and tank maintenance — as a month grid, list, phase timeline, sowing calendar, or season overview. Events can be subscribed to as an iCal feed in external calendar apps.

---

## Prerequisites

- At least one active plant or planting run
- For external calendar integration: a calendar feed must be set up

---

## Opening the Calendar

Click **Calendar** in the navigation. The view opens in month view by default.

---

## The Five Views

Switch between five views using the tabs at the top of the calendar:

| Tab | Description |
|-----|-------------|
| **Month View** | Month grid with up to three events per day; additional ones are collapsed into a "+N" indicator |
| **List View** | Tabular list of all filtered events in the current month, sortable |
| **Phase Timeline** | Bar chart of phase transitions per planting run/plant for the current month |
| **Sowing Calendar** | Week-precise outdoor growing calendar spanning the whole year |
| **Season Overview** | A 12-month tile grid showing sowing, harvest, and bloom counts per month |

!!! note "No week or day view"
    Kamerplanter does not currently offer a dedicated week or day view. For a narrow time range, the list view works best.

---

## Event Categories and Color Coding

Each of the eleven event categories has its own colour for quick visual orientation. Use the filter chips above the calendar to show or hide individual categories:

| Category | Description |
|----------|-------------|
| Training | High-/low-stress training (HST/LST) measures |
| Pruning | Trimming, defoliation |
| Transplanting | Repotting appointments |
| Feeding | Fertilization events |
| IPM / Pest Control | IPM inspections and treatments |
| Harvest | Planned and completed harvests |
| Maintenance | General care tasks |
| Phase Transitions | Planned or completed phase changes |
| Tank Maintenance | Water changes, calibrations |
| Watering Forecast | Precomputed watering dates from active watering schedules |
| Custom | Free/custom events |

<!-- Source: src/frontend/src/pages/kalender/CalendarPage.tsx (ALL_CATEGORIES) -->

---

## Filtering Events

In the month, list, and phase timeline views, two filters are available:

- **Category**: Click a category chip to show or hide it. Multiple categories can be combined.
- **Plant / Run**: The filter tree on the right (from tablet width) lists all planting runs with their plants, each with a checkbox.

For the sowing calendar and season overview, a **site** filter is available instead.

!!! note "No priority or status filters"
    A filter by priority or by status (open/completed/overdue) does not exist in the calendar. You will find these filters in the [Task overview](tasks.md) instead.

---

## Viewing Events

Click a single event in the month view to open a detail popover with title, category, date, and description. For watering forecast events, the popover additionally shows target EC, target pH, and the fertilizers to mix; use **Mark as watered** to confirm the watering directly from the popover.

Click a day with multiple events to see all of that day's events in a day popover — phase transitions are grouped by planting run.

Use **View details** to jump from an event to its associated task or plant.

!!! note "No direct completion or creation in the calendar"
    The calendar itself does not offer a "mark as complete" button for regular tasks (that only applies to watering forecast events), nor a quick-creation dialog for new tasks. Both are done in the [Task overview](tasks.md).

---

## Phase Timeline

The phase timeline shows one row per planting run and standalone plant, with coloured bars per growth phase for the currently displayed month. Bars are rendered differently depending on their status (completed / current / projected). Use the **Filter runs** and **Filter plants** controls to hide individual groups.

---

## Sowing Calendar (Outdoor)

For outdoor gardeners, Kamerplanter provides a week-precise sowing calendar spanning the entire calendar year.

### Layout

Each row shows a species with its cultivation bars across 52 weeks:

| Bar | Meaning |
|-----|---------|
| Indoor Sowing | Sowing indoors (before the last frost) |
| Outdoor Planting | Direct sowing or planting out into the bed |
| Growth | Period between sowing/planting out and harvest/bloom, filled automatically from gaps |
| Harvest | Harvest window |
| Flowering | Bloom window (used instead of Harvest for ornamentals) |

Use the category chips (e.g. Vegetable, Herb, Balcony Plant, Bulb / Tuber) to filter the displayed species. Use the star icon to mark favourites — the **Favorites only** option hides the rest. Use the magnifying-glass icon to open the species detail page. A dashed line marks the **Ice Saints** (default: 15 May), and a highlighted stripe marks the current week.

<!-- Source: src/backend/app/domain/engines/sowing_calendar_engine.py -->

!!! tip "Priority rules for date calculation"
    - If explicit **direct-sow months** are set for a species, they take priority over the "days after last frost" calculation.
    - For **frost-sensitive** species, the planting-out date is automatically never placed before the Ice Saints.
    - **Growth** bars are automatically inserted into the gap between sowing/planting and harvest/bloom, unless explicit growth months are set.

### Choosing Year and Site

Use the year navigation at the top of the calendar to switch the displayed calendar year; use the site filter to restrict the view to one site.

!!! info "Frost data only configurable via the API"
    The last frost date and the Ice Saints are currently **not** maintained through a form field on the site — there is no corresponding input field in the site form. Without your own values, Kamerplanter uses fixed defaults for Central Europe (1 May last frost, 15 May Ice Saints). Anyone wanting to set custom values can currently only do so via the technical API.

---

## Season Overview

The season overview shows a tile grid with all twelve months of the selected year. Each tile shows the number of sowing, harvest, and bloom events from the sowing calendar for that month; the current month is highlighted. Clicking a tile jumps to the month view for that month.

!!! note "Task count not yet populated"
    The tile also shows a "Tasks" field — this is currently always 0, as the underlying per-month task aggregation is not yet wired up.

---

## Exporting the Calendar to External Apps (iCal)

You can subscribe to your Kamerplanter calendar in external calendar apps. This gives you reminders on your phone even when the Kamerplanter app is not open.

!!! note "Read-only — no two-way sync"
    The iCal feed is read-only. Changes made in Google Calendar or Apple Calendar are not synced back to Kamerplanter. New tasks are always created in Kamerplanter.

### Step 1: Create a Calendar Feed

1. Open the **iCal Feeds** section at the bottom of the calendar.
2. Click **Create Feed**.
3. Give the feed a name (e.g. "My Main Calendar"). The feed adopts your currently enabled category filters at the time of creation.

### Step 2: Copy the Feed URL

After saving, the feed appears in the list with its `webcal://` URL. Click **Copy URL**.

### Step 3: Subscribe in the External Calendar

=== "Google Calendar"

    1. Open Google Calendar on a desktop browser.
    2. Under "Other calendars" on the left, click the plus icon.
    3. Select **From URL**.
    4. Paste the `webcal://` URL.
    5. Click **Add Calendar**.

=== "Apple Calendar (macOS)"

    1. Open Apple Calendar.
    2. Click **File → New Calendar Subscription**.
    3. Paste the `webcal://` URL.
    4. Click **Subscribe**.

=== "Thunderbird (Lightning)"

    1. Open Thunderbird.
    2. In the Calendar tab click **New Calendar**.
    3. Select **On the Network**.
    4. Select **iCalendar (ICS)** and paste the URL.
    5. Click **Next** and enter a name.

=== "Android (Standard Calendar)"

    1. Install an app such as **ICSx5** from the Play Store.
    2. Add the `webcal://` URL as a new subscription.

### Regenerating the Feed Token

Every feed has a secret token embedded in its URL. Use **Regenerate Token** to generate a new token and, with it, a new feed URL.

!!! warning "The old link stops working immediately"
    As soon as you regenerate the token, the previous `webcal://` URL no longer works — the external app shows an error instead of new events. Update the URL in every app where you subscribed to the feed. Use this if you accidentally shared a feed link or want to revoke a former member's access.

### Deleting a Feed

Feeds can be deleted at any time under **iCal Feeds**. When deleted, the feed link becomes invalid — it must be removed from the external app as well.

!!! info "Expiry only via the API"
    Kamerplanter internally supports an optional expiry date for feeds — once expired, the feed endpoint returns an error (HTTP 410 "Gone") instead of events. An expiry date cannot currently be set through the UI, only via the technical API.

---

## Frequently Asked Questions

??? question "Why do I see a task in the calendar that I already ticked off?"
    Completed tasks continue to appear in the calendar. Hide them using the status filter in the [Task overview](tasks.md).

??? question "Can I add recurring events?"
    Yes — directly when creating a task, via the **Recurrence** field (daily/weekly/biweekly/monthly), visible from the "Intermediate" experience level onward. In addition, active care profiles automatically generate recurring watering and fertilizing reminders. Both sources appear in the calendar. More: [Tasks](tasks.md).

??? question "How often does the iCal feed update?"
    The iCal feed is generated in real time on every request from the external app. The refresh frequency depends on the external calendar app — Google Calendar refreshes approximately every 24 hours, Apple Calendar every 12 hours.

??? question "Can I split the calendar across multiple people in the garden?"
    Yes. You can create multiple feeds with different category filters and share the respective URL with different people.

---

## See Also

- [Tasks](tasks.md)
- [Care Reminders](care-reminders.md)
- [Dashboard](dashboard.md)
- [Planting Runs](planting-runs.md)
