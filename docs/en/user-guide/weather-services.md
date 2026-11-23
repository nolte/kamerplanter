# Configuring Weather Services

As a platform admin, this is where you set the **instance-wide default settings** for the public weather services offered to every site in [Weather Sources per Location](weather-sources.md): Open-Meteo, the German Weather Service (DWD), and OpenWeatherMap. <!-- REQ-046 -->

!!! note "Platform admins only"
    The weather services settings are only accessible to users with the platform role **admin**. In light mode, the page is reachable directly without login, since the instance's single user is treated as the operator there.

---

## Prerequisites

- Platform role **admin** (full mode) or light-mode operation
- Access via **Settings > Installation > Weather services**

---

## Where to find the settings

1. Open the **Settings** (click your profile picture in the top right).
2. Open the **Installation** group — it sits in the navigation under the **Operation** heading, set apart from your personal settings — and its **Weather services** section, right below **Storage**.

The page shows three areas: one card per weather service, the global OpenWeatherMap key, and the **Fetch settings** card with the fetch interval, the timeout, the default source, the fetch status and the **Fetch now** button.

---

## Enabling and Adjusting Weather Services

For each of the three services — **Open-Meteo**, the **German Weather Service (DWD)**, and **OpenWeatherMap** — a dedicated card shows:

| Field | Description |
|------|-------------|
| **Enabled** | Toggle for whether the service is available instance-wide. If you disable a service, it disappears immediately from the selection list in every site's weather source dialog — sources already configured for that service stop receiving new data until it is re-enabled here. |
| **Base URL (optional)** | Overrides the service's default address. Leave empty to use the default address. |
| **Attribution** | The attribution text Kamerplanter displays in the weather source dialog and in the preview (e.g. Open-Meteo's license notice). |

!!! info "What is a base-URL override?"
    The base URL is the address at which Kamerplanter reaches the weather service in the background (e.g. `https://api.open-meteo.com/v1/forecast`). An **override** is only needed in special cases — for example if you run a self-hosted mirror of a service, or need to route through an internal proxy in a locked-down network environment. For normal operation, leave the field empty.

### Testing the Connection

Click **Test** on a service to immediately check its reachability — regardless of whether any site already uses that service. Kamerplanter fetches sample weather data for a reference location and shows:

- **Service reachable** — including a short preview of the next three days (minimum/maximum temperature, precipitation)
- **Service not reachable** — with as specific an error message as possible (e.g. a timeout or an invalid key)

!!! tip "When to test"
    Test a service right after setting a base-URL override or entering the global OpenWeatherMap key — that way you catch typos or reachability problems immediately, instead of only once a site stops receiving weather data later on.

---

## Global OpenWeatherMap Key (Fallback)

OpenWeatherMap is the only one of the three services that requires a personal API key. So that not every site needs its own key, you can store an **instance-wide fallback key** here.

**How the fallback works:** If a user sets up an OpenWeatherMap source at their site without entering their own key, Kamerplanter automatically uses the global key stored here. If a site has set its own key, that key **takes precedence** over the global fallback.

!!! info "The key stays secret"
    The global key is stored encrypted and is **never shown in plain text** — neither in the UI nor in any API response. A status chip simply shows "Key stored" or "No key". If you leave the input field empty when saving, an already-stored key remains unchanged. Use the eye icon to double-check your freshly entered input in plain text before saving.

!!! warning "Cost control on shared instances"
    If you use the global key on an instance with multiple tenants (e.g. a community garden), all sites without their own key share the same OpenWeatherMap quota. With many active sites, this quota can be exhausted faster than with a single personal key. Check your usage quota directly in your OpenWeatherMap account if needed.

---

## Fetch Settings

| Field | Description |
|------|-------------|
| **Fetch interval** | How many hours lie between two fetches of the weather data of all sites: at least 6, at most 168 (one week). A value outside this range or a decimal number is marked red, and **Save** stays disabled. The interval is saved together with the other fields of the page. What the interval does is described under [Fetch interval and manual fetch](#fetch-interval-and-manual-fetch). |
| **Timeout per request** | Maximum wait time **per request** to a weather service in seconds (1–120) — not how often Kamerplanter fetches weather data; that is the [fetch interval](#fetch-interval-and-manual-fetch). If a service does not respond within this time, the request is considered failed and Kamerplanter — if configured — tries the next source in that site's priority list. |
| **Default Source** | The public weather service Kamerplanter suggests when a site has not defined its own priority list yet. |

---

## Fetch Interval and Manual Fetch {#fetch-interval-and-manual-fetch}

Kamerplanter fetches the weather data of all sites at a fixed **fetch interval**: every **6 hours** by default, so up to four times a day. Shorter than 6 hours is not possible — that protects the quota of paid keys such as OpenWeatherMap. Longer intervals (up to one week) are possible.

- **When it fetches:** At every full hour, Kamerplanter checks whether the interval has passed since the last successful fetch, and fetches if so. A changed interval applies from the next full hour, without a restart.
- **When a fetch fails:** A fetch counts as successful when it supplied at least one site with weather data. If not a single site gets data, Kamerplanter tries again at the next full hour.
- **What happens next:** After every successful fetch, Kamerplanter immediately recalculates the [frost early-warning](notifications.md#frost-early-warning) and the [irrigation demand](watering-log.md#suggested-watering-volume). In addition, both run once a day in the morning on the most recently fetched data — so an approaching frost night is not missed even with a long interval or a weather-service outage.
- **During a longer outage:** When three fetches in a row fail, the backend writes an error entry (`weather_fetch_outage`) to its log.
- **Manual fetch:** You can also start a fetch for all sites right away. It runs in the background; its result (success or failure, time, number of sites and of sites with errors) then appears in the fetch status. A successful manual fetch restarts the interval. While a fetch is running, another one is refused; after a manual fetch you have to wait 10 minutes before you start the next one. While the weather feature is switched off, no manual fetch is possible either.
- **Fetch status:** It shows the time and result of the last successful fetch and the next scheduled fetch.

### Reading the fetch status

Below the fields of the **Fetch settings** card you find the **fetch status**:

| Line | Meaning |
|------|-------------|
| **Last successful fetch** | Date and time, whether the fetch was scheduled or manual, and how many sites received new weather data (e.g. "2 of 3 sites updated"). If there was none yet, it says "No successful fetch yet". |
| **Next scheduled fetch** | When Kamerplanter fetches on its own next time. If the weather fetch is switched off on your installation, it says "None". |
| **Effective fetch interval** | The interval Kamerplanter currently works with. After you save, the card reads the status again and shows the new value along with the next fetch it moved. |

If the newest fetch failed, a red line below names the time and the number of sites with an error. The arrow icon at the top right refreshes the status.

### Fetch now

1. In the **Fetch settings** card, click **Fetch now**. The button acts at once; you do not need to save anything for it.
2. A progress bar shows that the fetch is running. Depending on the number of sites this takes a few seconds to a few minutes. You can leave the page meanwhile; the fetch keeps running in the background.
3. When the fetch has finished, the result appears:
    - **Fetch finished** — how many sites have new weather data and how many forecast days were stored. If individual sites returned an error, their number is shown below; Kamerplanter retries them with the next fetch.
    - **Fetch failed** — no site received weather data. Kamerplanter retries at the next full hour. Use **Test** on the individual services to check whether they are reachable.

If a fetch takes unusually long (more than 5 minutes), the card stops waiting and tells you that the result appears in the fetch status once it has finished.

**When the button is disabled or the fetch is refused**, the reason is shown right below it:

| Message | What you can do |
|------|-------------|
| A new fetch is possible from *time* | After a manual fetch you have to wait 10 minutes. From the time shown, the button becomes available again on its own. |
| A fetch is running | A scheduled or another manual fetch has not finished yet. Wait until it has finished, then refresh the status. If someone else started a fetch just before your click, the card follows that fetch and shows its result. |
| The weather fetch is switched off | Your installation sets `WEATHER_ENABLED=false`. Then there are neither scheduled nor manual fetches; switch the weather function back on in the configuration. |
| A background service is unreachable | Kamerplanter cannot check right now whether a fetch is already running, or cannot queue the fetch. Try again in a few minutes. |

---

## For Technical Users / Self-Hosters

Every value set here overrides the corresponding backend environment variable while it is set via the UI. If no value is stored in the database, the environment-variable default applies:

| Environment variable | Default | Corresponds to field |
|---|---|---|
| `OPEN_METEO_ENABLED` | `true` | Open-Meteo → Enabled |
| `OPEN_METEO_BASE_URL` | `https://api.open-meteo.com/v1/forecast` | Open-Meteo → Base URL |
| `DWD_ENABLED` | `true` | DWD → Enabled |
| `DWD_BASE_URL` | `https://api.brightsky.dev` | DWD → Base URL |
| `OPENWEATHERMAP_ENABLED` | `true` | OpenWeatherMap → Enabled |
| `OPENWEATHERMAP_BASE_URL` | `https://api.openweathermap.org/data/2.5` | OpenWeatherMap → Base URL |
| `WEATHER_FETCH_TIMEOUT_S` | `20` | Timeout |
| `WEATHER_FETCH_INTERVAL_HOURS` | `6` (minimum `6`, maximum `168`) | Fetch interval |
| `WEATHER_DEFAULT_PUBLIC_SOURCE` | `open-meteo` | Default Source |

A value set via the UI takes effect immediately, without a backend restart. Resetting a base URL to empty via the UI editor clears the database override again — the environment-variable default then applies once more.

!!! info "SSRF protection for base-URL overrides"
    A base URL set via the UI is validated server-side (scheme allowlist, no private/internal addresses) before it is persisted — the same check used for the storage and Home Assistant settings. This prevents a misconfigured base URL from redirecting the backend to an unintended internal target.

**Fetch interval and manual fetch through the API** (platform admin only):

| Call | Effect |
|---|---|
| `PUT /api/v1/admin/weather-providers` with `{"fetch_interval_hours": 12}` | Sets the fetch interval; the backend rejects values below `6` or above `168` with `422`. |
| `POST /api/v1/admin/weather-providers/fetch` | Starts a fetch for all sites and answers immediately with `202`. `409 WEATHER_FETCH_DISABLED` with `WEATHER_ENABLED=false`; `409` while a fetch is running; `429` with `Retry-After` (seconds) while fewer than 10 minutes have passed since the last manual fetch; `503` when Valkey or the task broker cannot be reached. |
| `GET /api/v1/admin/weather-providers/fetch-status` | Last run, last successful run (trigger, times, sites, sites with errors), next scheduled fetch (empty while the weather feature is switched off), whether a fetch is running right now and in how many seconds a manual fetch is possible again. |

---

## Frequently Asked Questions

??? question "What happens to existing site weather sources if I disable a service here?"
    Sites that have already configured this service as a weather source stop receiving new data through it from the moment it's disabled. The site-level configuration itself is kept (not deleted) — if you re-enable the service here later, the site's source works again without any further action.

??? question "Why don't I see a key field for Open-Meteo or DWD?"
    Open-Meteo and the German Weather Service don't require an API key — both services can be used without registration. Only OpenWeatherMap requires a key, either per site or via the global fallback key on this page.

??? question "Do I have to configure a global key?"
    No. Without a global key, OpenWeatherMap still works — but then every site that wants to use OpenWeatherMap must store its own personal key in the [weather source dialog](weather-sources.md).

??? question "Does a base-URL override affect all sites at once?"
    Yes. The base URL applies instance-wide for the given service and affects every site that uses it as a source. An individual site cannot override the base URL on its own.

---

## See Also

- [Weather Sources per Location](weather-sources.md) — setting up and prioritizing weather sources per site
- [Locations & Substrates](locations-substrates.md) — setting the site type and GPS coordinates
- [Platform Admin](admin.md) — overview of the admin area
- [Configure Storage](object-storage.md) — the analogous instance-wide setting for object storage
- [Environment Variables](../reference/environment-variables.md) — full variable reference
