<!-- REQ-030 -->
# Notifications

Kamerplanter can keep you informed about due care tasks, sensor alarms, tank levels, and other important events — not only when you open the app, but actively through one or more channels of your choice. This page covers the notification center and how to set up the four available delivery channels.

---

## Prerequisites

- A Kamerplanter account with access to **Settings → Notifications** (`/settings#notifications`)
- For the **Home Assistant** channel: an already configured Home Assistant connection (see [Home Assistant Integration](../guides/home-assistant-integration.md))
- For the **Browser Push** channel: a Kamerplanter instance with Web Push enabled (see [Setting Up Browser Push](../guides/browser-push-setup.md)) — your operator sets this up once
- For the **Apprise** channel: at least one valid Apprise URL for the service you want (e.g. Telegram, ntfy, Gotify)

---

## The Notification Center

The **bell icon** in the top-right corner of the app shows how many unread notifications you have. Clicking it opens the notification list as a side drawer.

1. **Open** — Click the bell icon. The badge number refreshes automatically about once a minute.
2. **Read** — Clicking a notification marks it as read and opens the related page if one exists (e.g. the care overview for a watering reminder).
3. **Mark all as read** — Use the **Mark all read** button at the top of the drawer.
4. **Load more** — The list initially shows the newest 20 entries; use **Load more** to page further back.

Each card has a colored left border indicating urgency:

| Color | Urgency |
|-------|---------|
| Red | Critical (e.g. frost warning) |
| Orange | High |
| Blue | Normal |
| Gray | Low |

!!! note "Unread count is independent of the delivery channel"
    A notification appears in the notification center as soon as it is created — regardless of whether delivery through an external channel (see below) succeeded. This way you won't miss anything even if, for example, Home Assistant is temporarily unreachable.

---

## The Four Delivery Channels

Open **Settings → Notifications** to enable channels. Each channel can be toggled independently. If multiple channels are enabled at the same time, every notification is delivered to **all** enabled channels in parallel (there is no fallback to a "next" channel on failure — if one channel fails, the others still receive the message).

The status chip next to each channel shows **Available** or **Not configured**, depending on whether the channel is set up on the server side.

### Home Assistant

The recommended primary channel for users with smart-home integration. Requires your operator to have configured the backend's Home Assistant connection (see [Environment Variables](../reference/environment-variables.md#home-assistant-integration-req-005)).

Available options:

- **HA Persistent Notifications** — the message appears as a banner in the Home Assistant frontend (default: on)
- **Mobile Push (Companion App)** — sends to all companion app devices registered in Home Assistant (default: on)
- **Text-to-Speech (TTS)** — reads the message aloud through a selected speaker entity (e.g. `media_player.kitchen`); disabled by default and requires specifying the entity ID

Additionally, Kamerplanter fires a Home Assistant event for every notification (e.g. `kamerplanter_care_due`), which you can use to trigger your own HA automations — for example, opening an irrigation valve on a watering reminder.

!!! tip "Multiple reminders are bundled"
    If several care reminders occur at the same time, the Home Assistant channel merges them into a single summary message instead of overwhelming you with many individual notifications.

### Email

Enter your email address and choose the delivery mode:

- **Immediate** — every notification is sent as a separate email
- **Daily digest** — all of the day's notifications are bundled into a single email

Delivery uses the SMTP server (mail-sending server) configured by your operator (see [Environment Variables — Email](../reference/environment-variables.md#email)). If no SMTP connection is configured, development mode only prints emails to the backend log.

### Browser Push (PWA)

Enables Web Push notifications directly in the browser or in the app when installed as a PWA (an installable web app) — even when Kamerplanter is not currently open. You activate this **per device**: click **Enable on this device** and grant the browser's notification permission.

!!! info "Requires operator setup"
    Browser push only works once your operator has provisioned a VAPID key pair (the cryptographic key for web push). If the channel shows **Not configured**, this has not happened yet — see [Setting Up Browser Push](../guides/browser-push-setup.md).

If the channel is not supported in this browser (e.g. an older browser) or you previously blocked notifications, the page shows an explanatory message instead of the enable button. Use **Disable** to remove this device's push registration.

### Apprise

Connects to more than 100 messaging services via the open-source [Apprise](https://github.com/caronc/apprise) library — for example Telegram, Slack, Discord, ntfy, Gotify, or Pushover. Enter one or more **Apprise URLs** (one per line), for example:

```
tgram://<bot-token>/<chat-id>
slack://<token-a>/<token-b>/<channel>
gotify://<hostname>/<token>
```

You can find the exact URL syntax for your desired service in the [Apprise documentation](https://github.com/caronc/apprise/wiki). Kamerplanter itself requires no additional operator configuration for this channel — you manage the target URLs entirely yourself in your notification settings.

!!! warning "Operator prerequisite: install the Apprise package"
    The Apprise channel is active on the server by default, but requires the `apprise` Python package, which is not shipped automatically with the backend image. If it is not installed, the channel shows **Not configured** and test messages fail with "apprise package is not installed". The operator needs to add the package to the backend image (`pip install apprise`).

---

## Sending a Test Notification

After enabling a channel, you can verify it directly in the notification settings:

1. Enable the desired channel and save any related details (email address, Apprise URLs, …).
2. Click **Send test** for that channel.
3. A success or error message appears as a brief notification (snackbar) at the bottom of the screen.

The test message itself has the lowest urgency level and does not appear in the notification center.

---

## Quiet Hours

Under **Quiet hours**, set a daily time window (default: 22:00–07:00) during which Kamerplanter does **not deliver notifications through external channels** — the notification is still created and appears in the notification center, just without push, email, HA notification, or Apprise delivery during that window.

- **Sensor alarms** and **frost warnings** always ignore quiet hours and are delivered immediately through all enabled channels — these two types are hard-coded and cannot be turned off.
- The time zone for quiet hours is currently fixed to `Europe/Berlin`.

!!! warning "Not yet implemented"
    Notifications withheld during quiet hours are not automatically re-delivered through external channels once the window ends. You will see them in the notification center, but you will not receive a delayed HA push, email, or Apprise message for them. Automatic re-delivery after quiet hours end will be available in a future version.

---

## Batching and Escalation

### Batching

Multiple reminders that fall due at the same time are combined into a single message within a batching window (default: 30 minutes, adjustable from 1 to 120 minutes) instead of being delivered individually.

### Daily Summary

Enabling **Daily summary** additionally sends you a once-daily overview of all pending and overdue care tasks through the selected channel, at the configured time.

### Escalation for Overdue Watering

If a watering reminder remains unconfirmed, Kamerplanter repeats it with increasing urgency:

| Time | Urgency |
|------|---------|
| +2 days overdue | High |
| +4 days overdue | Critical |
| +7 days overdue | Critical (final reminder) |

These escalation days are fixed and currently not individually configurable; you can, however, turn escalation for watering reminders on or off entirely. There is no escalation for other reminder types (fertilizing, repotting, pest check).

---

## Frequently Asked Questions

??? question "I enabled multiple channels — will I get every notification multiple times?"
    Yes, that's by design: if, for example, Home Assistant and Email are both enabled, you receive every notification through both channels. There is currently no "primary channel only" setting for individual notification types in the interface.

??? question "Can I choose a different channel for specific notification types than for others?"
    Not yet through the interface. You enable channels globally for all notification types. Finer control per notification type is prepared in the data model but not yet available in the notification settings.

??? question "Why does Home Assistant show 'Not configured' even though I use HA?"
    The channel checks your operator's backend configuration of the Home Assistant connection, not your personal HA instance. Contact your operator if this connection is still missing.

??? question "I see a notification in the center, but no push message arrived — why?"
    First check whether the notification was created during your configured quiet hours (see above) — in that case, it is intentionally shown only in the center. Otherwise, check the status chip of the relevant channel and send a test notification.

---

## See Also

- [Care Reminders](care-reminders.md) — the most common source of notifications
- [Setting Up Browser Push](../guides/browser-push-setup.md) — VAPID setup for the PWA channel
- [Home Assistant Integration](../guides/home-assistant-integration.md)
- [Environment Variables](../reference/environment-variables.md) — reference for all channel configuration variables
- [Tasks](tasks.md)
