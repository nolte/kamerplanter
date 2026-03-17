# Calendar

The calendar shows all planned and past activities in one central view: tasks, phase transitions, watering events, IPM inspections, and tank maintenance. Feeds can be subscribed to as iCal links in Google Calendar, Apple Calendar, or Thunderbird.

---

## Prerequisites

- At least one active plant or planting run
- For external calendar integration: a calendar feed must be set up

---

## Opening the Calendar

Click **Calendar** in the navigation. The calendar opens in month view.

---

## View Modes

The calendar offers four view modes, switchable in the top right:

| Mode | Description |
|------|-------------|
| **Month** | Full month overview with events per day |
| **Week** | Detailed week view with timeline |
| **Day** | All events of a single day |
| **List** | Tabular list view of all upcoming events |

For daily use the **week** or **list view** is recommended.

---

## Event Categories and Colour Coding

Each event category has its own colour for quick visual orientation:

| Colour | Category | Description |
|--------|----------|-------------|
| Blue | Tasks | All scheduled care tasks |
| Green | Phase Transitions | Planned or completed phase changes |
| Teal | Watering Events | Documented watering sessions |
| Orange | IPM / Pest Control | Inspections and treatments |
| Red | Harvests | Planned and completed harvests |
| Grey | Tank Maintenance | Water changes, calibrations |

---

## Filtering Events

For large gardens with many plants the calendar can become busy quickly. Use the filter bar at the top:

- **Category**: Show only specific event types
- **Location**: Only events for a specific area
- **Plant / Run**: Only events for one plant or run
- **Priority**: Only critical or high priority
- **Status**: Only open, completed, or overdue tasks

!!! tip "Combining filters"
    You can have multiple filters active simultaneously. This lets you see, for example, only the critical open tasks for "Grow Tent A" in the next week.

---

## Completing a Task Directly from the Calendar

Click a task event in the calendar. A compact panel opens showing:

- Title and description of the task
- Associated plant(s)
- Button **Mark as Complete**

You can tick off tasks directly in the calendar without switching to the task list view.

---

## Creating a New Task from the Calendar

1. Click an empty day or time slot in the calendar.
2. A quick-creation dialog opens.
3. Enter title, type, and plant assignment.
4. Click **Create** — the task appears in the calendar immediately.

---

## Exporting the Calendar to External Apps (iCal)

You can subscribe to your Kamerplanter calendar in external calendar apps. This gives you reminders on your phone even when the Kamerplanter app is not open.

!!! note "Read-only — no two-way sync"
    The iCal feed is read-only. Changes made in Google Calendar or Apple Calendar are not synced back to Kamerplanter. New tasks are always created in Kamerplanter.

### Step 1: Create a Calendar Feed

1. Navigate to **Calendar → Feeds** (tab in the top right of the calendar).
2. Click **New Feed**.
3. Give the feed a name (e.g. "My Main Calendar" or "Grow Tent A only").

### Step 2: Configure the Feed

| Setting | Description |
|---------|-------------|
| Name | Display name in the external app |
| Categories | Which event types should the feed include? |
| Location Filter | Only events for a specific area |
| Priority Filter | Only from a certain priority level |

### Step 3: Copy the Feed URL

After saving, a `webcal://` URL appears. Copy this URL.

### Step 4: Subscribe in the External Calendar

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

### Updating or Deleting a Feed

Feeds can be edited or deleted at any time under **Calendar → Feeds**. When deleted, the feed link becomes invalid — it must be removed from the external app as well.

---

## Sowing Calendar (Outdoor)

For outdoor gardeners Kamerplanter provides an integrated sowing calendar that shows when to start propagation indoors, when direct sowing is possible, and when to plant out.

### Opening the Sowing Calendar

Click **Sowing Calendar** at the top of the calendar (tab).

The sowing calendar shows:
- **Indoor propagation window**: When to start seeds indoors
- **Direct sowing window**: When direct sowing into the bed is possible
- **Plant out**: When indoor-grown seedlings can go outside
- **Expected harvest**: Based on the variety's growth duration

### Configuring the Frost Date

For the sowing calendar to calculate correct dates, enter the last frost date for your location:

1. Open **Settings → Location** or the site detail page.
2. Under **Frost Data** enter the average last frost date (e.g. "15 April" for Central Europe).
3. The system calculates all sowing dates relative to this date.

---

## Frequently Asked Questions

??? question "Why do I see a task in the calendar that I already ticked off?"
    Completed tasks are not hidden by default; they are displayed with a completed marking. Enable **Only open tasks** in the filter to hide completed ones.

??? question "Can I add recurring events directly in the calendar?"
    Yes, but only via care profiles and workflow templates — not directly in the calendar. A care profile with a weekly fertilization interval automatically creates recurring tasks that appear in the calendar.

??? question "How often does the iCal feed update?"
    The iCal feed is generated in real time on every request from the external app. The refresh frequency depends on the external calendar app — Google Calendar refreshes approximately every 24 hours, Apple Calendar every 12 hours.

??? question "Can I split the calendar across multiple people in the garden?"
    Yes. You can create multiple feeds with different filters (e.g. by location or category) and share them with different people. Each tenant member gets their personalised calendar feed this way.

---

## See Also

- [Tasks](tasks.md)
- [Dashboard](dashboard.md)
- [Planting Runs](planting-runs.md)
