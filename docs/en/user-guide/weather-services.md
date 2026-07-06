# Configuring Weather Services

As a platform admin, this is where you set the **instance-wide default settings** for the public weather services offered to every site in [Weather Sources per Location](weather-sources.md): Open-Meteo, the German Weather Service (DWD), and OpenWeatherMap. <!-- REQ-046 -->

!!! note "Platform admins only"
    The weather services settings are only accessible to users with the platform role **admin**. In light mode, the page is reachable directly without login, since the instance's single user is treated as the operator there.

---

## Prerequisites

- Platform role **admin** (full mode) or light-mode operation
- Access via **Account Settings > Weather Services**

---

## Where to find the settings

1. Open **Account Settings** (click your profile picture in the top right).
2. Select the **Weather Services** tab — it appears in the same place as the **Storage** tab, right next to it.

The page shows three areas: one card per weather service, the global OpenWeatherMap key, and the general fetch settings.

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
| **Timeout** | Maximum wait time per weather request in seconds (1–120). If a service does not respond within this time, the request is considered failed and Kamerplanter — if configured — tries the next source in that site's priority list. |
| **Default Source** | The public weather service Kamerplanter suggests when a site has not defined its own priority list yet. |

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
| `WEATHER_DEFAULT_PUBLIC_SOURCE` | `open-meteo` | Default Source |

A value set via the UI takes effect immediately, without a backend restart. Resetting a base URL to empty via the UI editor clears the database override again — the environment-variable default then applies once more.

!!! info "SSRF protection for base-URL overrides"
    A base URL set via the UI is validated server-side (scheme allowlist, no private/internal addresses) before it is persisted — the same check used for the storage and Home Assistant settings. This prevents a misconfigured base URL from redirecting the backend to an unintended internal target.

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
