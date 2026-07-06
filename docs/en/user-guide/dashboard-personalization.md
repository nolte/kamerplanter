<!-- Quelle: src/frontend/src/config/dashboardWidgetCatalog.ts, src/frontend/src/pages/DashboardPage.tsx, src/frontend/src/pages/auth/DashboardSettingsTab.tsx, src/frontend/src/i18n/locales/en/translation.json -->

# Personalizing Your Dashboard

You build your own [dashboard](dashboard.md): choose widgets from a catalog, arrange them via drag-and-drop, resize them, and configure individual widgets — exactly to your own needs. <!-- REQ-045 -->

---

## Prerequisites

- You are signed in (or using [Light Mode](light-mode.md) on a local device).
- At least one widget must be available to you — some widgets require an enabled [module](module-visibility.md).

---

## Two Ways to Personalize

You can adjust your dashboard in two equivalent ways:

| Surface | Where | Highlight |
|---------|-------|-----------|
| **Settings → Dashboard** | Account settings, "Dashboard" tab | Fully keyboard-accessible: add/remove widgets, reorder and resize via buttons, configure, reset |
| **Edit mode** | Directly on the dashboard page | Move and resize widgets with the mouse or touch (drag-and-drop) |

Both surfaces save the same setting — changes made on one surface appear immediately on the other.

!!! tip "Quick access from the dashboard"
    Click the gear icon **"Manage widgets"** in the dashboard header to jump directly to the "Dashboard" tab in settings.

The very first time you visit the dashboard, a one-time notice tells you that you can personalize your dashboard. You can dismiss it via the close icon — it will not reappear afterwards.

---

## Adding and Removing Widgets in Settings

### Step 1: Open Settings

1. Click your **profile picture** or user icon in the top-right corner.
2. Select **Account Settings**.
3. Switch to the **Dashboard** tab.

### Step 2: Choose a widget

The available widgets are grouped by category (see [Widget Catalog](#widget-catalog) below). Turn on the switch next to a widget to show it on your dashboard — turn it off to remove it again.

Unavailable widgets appear greyed out with a lock icon and a reason, for example "Module hidden" or "Not available in Light mode". Such a widget can only be enabled once the underlying condition is met (e.g. once the associated module is shown again).

### Step 3: Change order and size (accessible)

In the **"Arrange & size"** section you see your active widgets as a list. Each widget has buttons for:

- **Move up** / **Move down** — moves the widget in the order
- **Smaller** / **Larger** — changes the size within the limits allowed for that widget
- **Configure** (only for widgets with their own settings) — opens a configuration dialog

These buttons are fully keyboard-operable and work identically to drag-and-drop in edit mode.

!!! tip "Changes are saved immediately"
    Every change in the settings tab is applied immediately — there is no separate save button for this section.

### Step 4: Adjust separately for desktop, tablet, and mobile

The **"Desktop / Tablet / Mobile"** switch selects which screen size you are currently editing the order and size for. This lets you, for example, set a different arrangement on your phone than on a large screen.

If you have not yet adjusted a smaller device, Kamerplanter automatically takes over the desktop arrangement (stacked in a single column). Use the **"Apply to all"** button to copy the currently selected arrangement to the other screen sizes.

---

## Arranging Widgets Directly on the Dashboard (Edit Mode)

Besides the settings, you can also adjust your dashboard directly:

### Step 1: Start edit mode

Click **"Edit"** at the top right of the dashboard page.

### Step 2: Move and resize widgets

- Drag a widget with your mouse or finger to a new position.
- Drag the edge of a widget to resize it.
- Use the Desktop / Tablet / Mobile switch to decide which screen size the change applies to.

Every widget also has a **menu icon (⋮)** with the same actions available in the settings tab: move up/down, larger/smaller, configure, remove. This menu is the full keyboard alternative to dragging with the mouse.

!!! note "No drag-and-drop on smartphones"
    On small screens (below 600 pixels wide) dragging with your finger is disabled. Use the menu icon on each widget instead, or adjust the mobile arrangement in the settings tab.

### Step 3: Save or discard

Click **"Save"** to apply your changes, or **"Cancel"** to discard them and return to the last saved state.

---

## Widget Catalog

Kamerplanter currently offers 17 widgets across four categories. Which widgets are visible to you depends on your experience level, your enabled [modules](module-visibility.md), and your operating mode ([Light or Full mode](light-mode.md)).

<!-- Quelle: src/frontend/src/config/dashboardWidgetCatalog.ts, src/frontend/src/i18n/locales/en/translation.json (dashboard.widgets.*) -->

### Essentials

| Widget | Description |
|--------|-------------|
| Quick actions | Direct tiles to frequently used areas. |
| Tasks today | Tasks due and overdue today. |
| Care reminders | Upcoming care reminders. |
| Active plants | Overview of your active plants. |
| Setup progress | Your progress through initial setup (only shown while onboarding is incomplete). |

### Insights

| Widget | Description |
|--------|-------------|
| Tip of the day | Daily AI care tip for your plants. |
| Weather forecast | Links to the [weather source setup](weather-sources.md) for your outdoor/greenhouse locations; does not display forecast values directly in the widget yet. |
| Harvest forecast | Expected harvest dates (with timeframe configuration). |
| Community activity | Activity from your community gardens. |

### Cultivation

| Widget | Description |
|--------|-------------|
| Winter protection | Winter-hardiness traffic light of your plants, extended with the [season state](season-automation.md) of your outdoor/greenhouse sites (live weather, climate estimate, or calendar) and a frost countdown. |
| Plant-protection alerts | Current pest and disease alerts. |
| Next events | Your next calendar entries. |
| Phase timeline | Growth phases of your plants over time. |
| Plant grid | Tile overview of all your plants. |

### Monitoring

| Widget | Description |
|--------|-------------|
| Sensor live values | Current readings from your sensors (with location configuration). |
| Tank status | Fill levels of your nutrient tanks. |
| VPD gauge | Current vapour pressure deficit (VPD). |

!!! example "Example: a widget with its own configuration"
    The **Sensor live values** widget offers a configuration dialog where you enter a location. Click the gear icon next to the widget in the settings tab (or in the edit-mode menu) to open it.

---

## Default Selection by Experience Level

Without a personal adjustment, your dashboard shows a sensible base selection that depends on your [experience level](onboarding.md):

- **Beginner:** Quick actions, Tasks today, Care reminders, Active plants, Tip of the day, Winter protection, Weather forecast, Setup progress
- **Intermediate:** all Beginner widgets, plus Plant-protection alerts, Harvest forecast, Next events, Community activity
- **Expert:** all Intermediate widgets, plus Sensor live values, Tank status, Phase timeline, VPD gauge, Plant grid

### Restoring the default

Use the **"Restore default"** button (in the settings tab) to discard your personal adjustment and get back the base selection matching your experience level.

---

## When the Dashboard Is Empty

If you remove all widgets, the dashboard does not show a blank page but a notice with two options:

- **"Choose widgets"** — takes you directly to the settings tab
- **"Restore default"** — restores the base selection for your experience level

---

## Persistence and Tenants

Your dashboard layout is stored per user and per [tenant](tenants.md). If you switch between multiple gardens, each tenant shows its own, independent layout.

In [Light Mode](light-mode.md) — without registration — your layout is instead stored in your device's browser storage (localStorage). If you register later, Kamerplanter automatically migrates your local layout into your account once.

---

## Accessibility

- All actions (adding/removing widgets, reordering, resizing, configuring) are fully keyboard-operable — both in the settings tab and via the menu icon in edit mode.
- Changes to order or size are announced for screen readers (e.g. "Sensor live values moved up").
- The order in which screen readers and keyboard navigation read or jump between widgets always follows the visible arrangement on screen — on every screen size.
- If you prefer reduced motion (system setting "Reduce motion"), edit mode skips animations when moving widgets.

---

## Frequently Asked Questions

??? question "Why don't I see a widget I enabled?"
    Check whether the associated module is shown in your [module settings](module-visibility.md). A widget whose module has been hidden stays in your selection but is not displayed while the module is hidden — as soon as you show the module again, the widget reappears automatically.

??? question "Do I lose my personalization when I change my experience level?"
    No. Once you have personalized your dashboard yourself, your selection is kept regardless of your experience level. Only without a personal adjustment does the dashboard automatically follow the base selection for your current experience level.

??? question "Can I choose a completely different set of widgets for each screen size?"
    No. Which widgets are shown is the same across all screen sizes — only the arrangement and size of the widgets can be set separately for desktop, tablet, and mobile.

??? question "Can another user in the same garden see my dashboard layout?"
    No. Your dashboard layout is a personal setting per user and tenant. Other members in your garden have their own, independent arrangement.

---

## See Also

- [Dashboard](dashboard.md) — Overview of the dashboard sections
- [Modules & Features](module-visibility.md) — controls which widgets are selectable at all
- [Onboarding Wizard](onboarding.md) — Set your experience level
- [Light Mode](light-mode.md) — Run Kamerplanter without login
- [Tenant Management](tenants.md) — Manage multiple gardens
- [Weather Sources per Location](weather-sources.md) — set up the source for the "Weather forecast" widget
