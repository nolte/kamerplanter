# Kiosk Mode

Kiosk Mode optimizes the interface for hands-on use right at the growing site — in a greenhouse, grow room, or on a balcony. Large buttons, a simplified start page and a high-contrast design keep the app usable with gloves, dirty hands, or in direct sunlight. <!-- UI-NFR-019 -->

---

## Prerequisites

- You are logged in (Full mode) or use a local instance in [Light Mode](light-mode.md).
- Kiosk Mode works especially well on a tablet permanently mounted in a greenhouse or grow room.

---

## What Kiosk Mode Is For

Greenhouses and grow rooms come with special conditions: soil, nutrient solution and water on your hands, gloves that reduce touch precision, and lighting that swings from glaring sun to dark corners. Kiosk Mode provides a dedicated, reduced interface for exactly this, so you can handle key tasks on the spot without washing your hands or taking off your gloves first.

!!! note "Partially available: Kiosk Mode"
    Kiosk Mode is still being expanded. This page describes the functionality currently available (start page, activation, high-contrast display, inactivity warning). Further stages are described in [What's Coming Next](#whats-coming-next).

---

## Enabling Kiosk Mode

### Step 1: Open Account Settings

Click your **profile picture** or initials in the top right and choose **Account Settings**. Switch to the **Kiosk mode** tab.

### Step 2: Turn Kiosk Mode On

Enable the **Enable kiosk mode** switch. The app switches to Kiosk Mode immediately — no page reload needed. Turning it on also automatically enables the high-contrast display (see [High-Contrast Display](#high-contrast-display)).

Use the **Open kiosk start page** button to jump straight to the start page at `/kiosk`.

!!! tip "The setting persists"
    Kiosk Mode survives a page reload. In Light Mode the setting is stored in your browser (`localStorage`); in Full Mode it is additionally stored on your account — so it is available again after signing in on another device, once the server data has loaded.

---

## The Kiosk Start Page

Once Kiosk Mode is active, the permanent **Home** button always takes you back to the kiosk start page (`/kiosk`). It shows four large tiles for the most important tasks, plus a status overview.

### Quick-Action Tiles

| Tile | Action |
|------|--------|
| **Scan plant** | Opens photo-based plant identification |
| **Log watering** | Opens the watering log |
| **Start round** | Opens the task queue for your next round |
| **Report problem** | Opens photo-based pest/problem detection |

### Current Status

Below the tiles, the start page shows your number of open tasks and any warnings (e.g. overdue tasks) at a glance.

---

## High-Contrast Display

The high-contrast display uses pure black and white with a particularly strong contrast (WCAG AAA — the highest accessibility level of the Web Content Accessibility Guidelines, at least a 7:1 contrast ratio for text) and drops subtle greys, shadows and gradients. This significantly improves readability, for example in direct sunlight in a greenhouse.

It is enabled by default as soon as you turn on Kiosk Mode. You can also use it **independently** of Kiosk Mode — for example on the balcony in bright daylight: enable the separate **Use high-contrast design** switch in the **Kiosk mode** tab of Account Settings.

---

## Automatic Inactivity Warning

To prevent a fixed-installation kiosk station from leaving a previous user's inputs open, Kiosk Mode automatically detects inactivity:

1. After **120 seconds** without a touch, a large warning overlay appears, asking "Still there?" with a countdown.
2. If you don't respond, the app automatically returns to the kiosk start page after another **30 seconds**.
3. Tapping **Keep working** dismisses the warning and restarts the inactivity timer.

Any touch on the screen outside the warning also resets the inactivity timer.

!!! warning "The warning cannot be dismissed by tapping away"
    The warning overlay cannot be closed by tapping elsewhere or pressing Escape — only via the **Keep working** button. This prevents the warning from being accidentally missed.

---

## Leaving Kiosk Mode

Tap **Exit kiosk** in the kiosk header bar. You return to the dashboard, and Kiosk Mode is disabled (the high-contrast display stays on if you had enabled it separately before). Alternatively, turn Kiosk Mode off any time via the **Kiosk mode** tab in Account Settings.

While Kiosk Mode is active, the kiosk badge and Home button stay permanently visible — even when a tile navigates you into another part of the app.

---

## What's Coming Next

!!! note "Not yet implemented"
    Further planned stages of Kiosk Mode are not yet implemented and will be added in the future: simplified sub-forms with quick-select tiles for common readings (e.g. electrical conductivity (EC), pH value, temperature), touch debouncing against accidental double-taps, stronger confirmation protection for critical actions (long-press), and a screensaver mode after the automatic return to the start page. <!-- UI-NFR-019 -->

---

## Frequently Asked Questions

??? question "Can I use Kiosk Mode in Light Mode too?"
    Yes. In Light Mode your setting is stored locally in the device's browser — ideal for a tablet that stays permanently mounted at one location.

??? question "Does Kiosk Mode affect other devices or users?"
    In Full Mode the setting is tied to your account and additionally stored on the server. Other members of your garden are not affected — everyone enables Kiosk Mode individually for themselves.

??? question "Why do I still see the regular navigation when I navigate from a kiosk tile?"
    Some tiles (e.g. "Scan plant") take you into the regular part of the app so you can use that page's full functionality. The kiosk badge and Home button stay visible throughout, so you can always find your way back to the kiosk start page.

---

## See Also

- [Light Mode](light-mode.md)
- [Watering Log](watering-log.md)
- [Identify a Plant by Photo](plant-identification.md)
- [Detecting Pests by Photo](pest-detection.md)
- [Tasks](tasks.md)
- [Account & Login](account.md)
