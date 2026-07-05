# Weather Sources per Location

For every outdoor or greenhouse site, you decide where Kamerplanter gets its weather data from: a public weather service or your own Home Assistant installation. You can add several sources and prioritize them, so that if your preferred source becomes unavailable, another one automatically takes over. <!-- REQ-046 -->

!!! note "Partially available: forecast display"
    The source configuration, the connection test, and the automatic, prioritized background fetching are fully implemented. A dedicated view that continuously displays the fetched forecast (e.g. in the "Weather forecast" dashboard widget) does not exist yet — it currently only links to this setup page. You can already see live values via the [test the connection](#test-the-source) feature. <!-- REQ-046 -->

---

## Prerequisites

- A site of type **Outdoor** or **Greenhouse** — indoor sites (grow tent, room, balcony, …) don't show the "Weather Source" section, since you already measure there via [sensors](sensors.md) or Home Assistant.
- **GPS coordinates** for this site. Without stored coordinates, Kamerplanter shows a hint that you first need to add the coordinates.
- Your role in the tenant is **Grower** or **Admin** (see [Tenants & Gardens](tenants.md#roles-and-permissions)) — as a **Viewer** you can only see the configuration, not change it.
- For the Home Assistant option, additionally: a stored Home Assistant access token (see [Home Assistant Integration](../guides/home-assistant-integration.md#setting-up-tokens)).

!!! info "For technical users"
    GPS coordinates are currently only editable via the API — the site form does not yet have an input field for this. See [Locations & Substrates](locations-substrates.md#creating-a-new-site) for details.

---

## Adding a Weather Source

### Step 1: Navigate to the Site

Under **Locations**, open your outdoor or greenhouse site. At the end of the detail page you'll find the **Weather Source** section.

### Step 2: Open "Add Source"

Click **Add Source**. A dialog opens with a choice between two kinds of weather sources: **Public Service** and **Home Assistant**.

### Step 3a: Choose a Public Weather Service (Default Path)

For most outdoor growers, a public weather service is the simplest path — it works immediately, without any hardware of your own:

| Weather service | Sign-up needed? | Note |
|------------------|:---:|--------|
| **Open-Meteo** | No | Recommended — free, worldwide, no registration required. |
| **German Weather Service (DWD)** | No | Best coverage in German-speaking regions. |
| **OpenWeatherMap** | Yes | Worldwide, requires your own API key. |

Select the desired service from the list. If you choose **OpenWeatherMap**, you also enter your personal API key (which you can create for free on the OpenWeatherMap website).

!!! info "Your API key stays secret"
    The OpenWeatherMap key is stored encrypted and is never shown to you again in plain text — only a "Key stored" note confirms it has been saved. If you edit the source later, simply leave the field empty to keep the stored key unchanged.

### Step 3b: Or Use Home Assistant as a Source

If you already have weather sensors or a weather integration in Home Assistant, you can use those instead. The **Home Assistant** option is only selectable once you have stored a Home Assistant access token — if it's missing, the option is greyed out and links you directly to the relevant settings.

Then choose one of the two modes:

=== "One Weather Entity"
    The simpler choice if your Home Assistant installation already provides a ready-made `weather.*` entity (e.g. via the Met.no integration). Select the matching entity from the list — Kamerplanter automatically picks up temperature, precipitation, and other values from it.

=== "Map Individual Sensors"
    Map individual `sensor.*` entities to the matching weather fields instead, grouped by **Temperature** (minimum, maximum, current), **Precipitation & Wind** (precipitation, wind speed, wind gusts), and **Other readings** (humidity, pressure). You don't need to map every field — at least one mapped sensor is enough.

!!! tip "Which mode to use?"
    Use **one weather entity** if you have one available — it delivers a ready-made daily forecast in one click. Use **individual sensors** if you want to integrate your own weather-station sensors (e.g. a private weather station) but don't have a ready-made `weather.*` entity.

### Step 4: Test the Source {#test-the-source}

Before saving, you can check any source via the flask icon **Test Source** — including sources you've already saved. Kamerplanter checks reachability and, if GPS coordinates are stored, shows you a preview of the next three days (minimum/maximum temperature, precipitation) including the [provenance label](#understanding-weather-data-provenance). If the source is unreachable, an error message appears instead of the preview.

### Step 5: Add More Sources and Prioritize Them

You can add as many sources as you like — for example, Open-Meteo as your primary source and Home Assistant as a supplement. Each entry shows its position in the list as a number (**#1** = highest priority). Use the **up** and **down** arrow icons to change the order.

**Understanding priority and fallback:** Kamerplanter always tries the highest-priority source (#1) first. If it's currently unreachable, the next active source in the list automatically takes over — without any action needed from you. Use the switch next to each entry to temporarily disable a source without deleting it.

!!! example "Example: two sources as a safety net"
    You first add **Open-Meteo** (priority #1) and then a **Home Assistant weather station** (priority #2). As long as Open-Meteo works normally, Kamerplanter uses its forecast. If the service is ever unreachable, your Home Assistant source automatically takes over.

### Step 6: Save

Click **Save** to apply your entire source list. To edit an existing source afterward, open it via the gear icon — note that the kind (public/Home Assistant) and the provider cannot be changed after creation. To switch, delete the source via the trash icon and add it again.

---

## Understanding Weather Data Provenance {#understanding-weather-data-provenance}

For every value, Kamerplanter shows you how it came about:

| Label | Meaning |
|---------------|-----------|
| **Forecast** | A computed expected value for a future date — not yet a measurement. |
| **Observed** | An actually measured value, for example from a Home Assistant sensor — not an estimate. |
| **Reanalysis** | Historical data derived from weather models — neither a live measurement nor a forecast. |

!!! tip "Why this matters"
    An observed value from your own sensor exactly reflects the conditions at your location. A forecast, on the other hand, comes from the service's nearest weather station and can differ somewhat from your actual site (e.g. a sheltered spot or a microclimate).

---

## Attribution of Weather Data

Below the source list, Kamerplanter shows the attribution notices for the services in use: German Weather Service (under the Geodatennutzungsverordnung, GeoNutzV), Open-Meteo (CC BY 4.0 license), and OpenWeatherMap under its terms of use.

---

## Frequently Asked Questions

??? question "Why is the 'Home Assistant' option greyed out?"
    Home Assistant is only selectable as a weather source once you've stored a Home Assistant access token in your account settings. The dialog links you directly there. Home Assistant is optional — all weather features work fully without it, using only a public service like Open-Meteo.

??? question "Do I have to use Home Assistant to get weather data?"
    No. Open-Meteo works without sign-up, without an API key, and without any hardware of your own. Home Assistant is an additional option for anyone who already runs their own weather station or weather integration.

??? question "What happens if none of my sources are reachable?"
    Then no new weather data is available for the site for that period. In that case, use **Test Source** to check which source is causing the error, and add an additional fallback source if needed.

??? question "Where do I see the actual weather forecast for my site?"
    A continuous forecast view is not implemented yet. Currently, **Test Source** gives you a preview of the next three days; the "Weather forecast" dashboard widget currently only links to this setup page.

??? question "Can I add the same weather service twice?"
    No, each provider can only be added once per site. If you want to compare two different perspectives, combine a public service with your Home Assistant source instead.

---

## See Also

- [Locations & Substrates](locations-substrates.md) — creating sites and GPS coordinates
- [Sensors and Measurement Data](sensors.md) — other data sources for climate and substrate values
- [Home Assistant Integration](../guides/home-assistant-integration.md) — setting up an access token
- [Personalizing Your Dashboard](dashboard-personalization.md) — the "Weather forecast" widget
- [Climate Zones & Hardiness](../guides/climate-zones.md)
