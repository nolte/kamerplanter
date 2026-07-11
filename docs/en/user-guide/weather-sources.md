# Weather Sources per Location

For every outdoor, greenhouse, or balcony site, you decide where Kamerplanter gets its weather data from: a public weather service or your own Home Assistant installation. You can add several sources and prioritize them, so that if your preferred source becomes unavailable, another one automatically takes over. <!-- REQ-046 -->

!!! tip "Forecast and Frost Early-Warning on the Dashboard"
    Once you've set up at least one source here, the "Weather forecast" dashboard widget shows the fetched daily forecast directly (minimum/maximum temperature per day, including the [provenance label](#understanding-weather-data-provenance)) — and proactively warns you when a frost night is expected within the forecast window. See [Dashboard: Weather Forecast and Frost Early-Warning](dashboard.md#weather-forecast-and-frost-early-warning) and [Notifications: Frost Early-Warning](notifications.md#frost-early-warning) for details. <!-- REQ-046 -->

---

## Prerequisites

- A site with the **type** **Outdoor**, **Greenhouse**, or **Balcony** — you set the type directly in the site form (see [Locations & Substrates](locations-substrates.md#filling-in-basic-data)). A balcony counts as a frost-exposed outdoor location and therefore gets the same weather and frost features as Outdoor and Greenhouse. For the other types (Indoor, Windowsill, Grow Tent) the "Weather Source" section doesn't appear, since you already measure there via [sensors](sensors.md) or Home Assistant.
- **GPS coordinates** (latitude and longitude) for this site — also editable directly in the site form. Without stored coordinates, Kamerplanter shows a hint that you first need to add the coordinates.
- Your role in the tenant is **Grower** or **Admin** (see [Tenants & Gardens](tenants.md#roles-and-permissions)) — as a **Viewer** you can only see the configuration, not change it.
- For the Home Assistant option, additionally: a stored Home Assistant access token (see [Home Assistant Integration](../guides/home-assistant-integration.md#setting-up-tokens)).

---

## Adding a Weather Source

### Step 1: Navigate to the Site

Under **Locations**, open your outdoor, greenhouse, or balcony site. At the end of the detail page you'll find the **Weather Source** section.

### Step 2: Open "Add Source"

Click **Add Source**. A dialog opens with a choice between two kinds of weather sources: **Public Service** and **Home Assistant**.

### Step 3a: Choose a Public Weather Service (Default Path)

For most outdoor growers, a public weather service is the simplest path — it works immediately, without any hardware of your own:

| Weather service | Sign-up needed? | Note |
|------------------|:---:|--------|
| **Open-Meteo** | No | Recommended — free, worldwide, no registration required. |
| **German Weather Service (DWD)** | No | Best coverage in German-speaking regions. |
| **OpenWeatherMap** | Yes | Worldwide, requires your own API key. |

Select the desired service from the list. If you choose **OpenWeatherMap**, you can also enter your personal API key (which you can create for free on the OpenWeatherMap website).

!!! info "Your API key stays secret"
    The OpenWeatherMap key is stored encrypted and is never shown to you again in plain text — only a "Key stored" note confirms it has been saved. If you edit the source later, simply leave the field empty to keep the stored key unchanged.

!!! tip "Don't have your own key?"
    If you leave the key field empty, OpenWeatherMap still works, provided your instance operator has configured a **global fallback key** (an instance-wide setting under **Weather Services**, see [Configuring Weather Services](weather-services.md)). If neither your own nor a global key is available, the connection test reports an error.

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

## Climate at the Site

Directly below the weather sources, Kamerplanter also shows the **Climate at the Site** section for outdoor, greenhouse, and balcony sites with stored GPS coordinates — twelve long-term monthly averages (**climate normals**) for average and minimum temperature, precipitation, and solar radiation, shown as a chart and as a table. <!-- REQ-041 -->

!!! tip "What are climate normals?"
    A climate normal is neither a current reading nor a forecast — it's a long-term average, e.g. "in January, the average temperature at this location is usually around -1 °C." Values like these help with decisions that go beyond the current day: when do you usually sow at this site? How much rain typically falls in a dry summer month? Does a plant typically survive winter outdoors at this site? Climate normals are therefore a **reanalysis** — see the explanation of this provenance label above under [Understanding Weather Data Provenance](#understanding-weather-data-provenance).

The data source is **NASA POWER**, NASA's satellite- and model-based reanalysis service — usable without sign-up or an API key, just like the other public weather services. Kamerplanter automatically fetches the climate normals for every eligible site once a month in the background; right after adding a site with GPS coordinates, it can therefore take a moment before the section shows values for the first time. As long as no data is available yet, this section shows a corresponding hint instead of the chart and table.

---

## Attribution of Weather Data

Below the source list, and below the climate chart, Kamerplanter shows the attribution notices for the services in use: German Weather Service (under the Geodatennutzungsverordnung, GeoNutzV), Open-Meteo (CC BY 4.0 license), OpenWeatherMap under its terms of use, and — for the climate normals in the "Climate at the Site" section — NASA POWER (CC BY 4.0 license).

The irrigation demand calculated from this weather data (evapotranspiration/ET₀, see [Watering Log: Suggested Watering Volume](watering-log.md#suggested-watering-volume)) uses the open-source library **aquacropeto** (BSD-3-Clause license) internally for the FAO-56 calculation — not a weather data source of its own, just the calculation formula. <!-- REQ-037 -->

---

## Frequently Asked Questions

??? question "Why is the 'Home Assistant' option greyed out?"
    Home Assistant is only selectable as a weather source once you've stored a Home Assistant access token in your account settings. The dialog links you directly there. Home Assistant is optional — all weather features work fully without it, using only a public service like Open-Meteo.

??? question "Do I have to use Home Assistant to get weather data?"
    No. Open-Meteo works without sign-up, without an API key, and without any hardware of your own. Home Assistant is an additional option for anyone who already runs their own weather station or weather integration.

??? question "What happens if none of my sources are reachable?"
    Then no new weather data is available for the site for that period. In that case, use **Test Source** to check which source is causing the error, and add an additional fallback source if needed.

??? question "Where do I see the actual weather forecast for my site?"
    In the "Weather forecast" dashboard widget (see [Dashboard](dashboard.md#weather-forecast-and-frost-early-warning)) — it shows the daily forecast (minimum/maximum temperature, provenance label) for your first outdoor, greenhouse, or balcony site with stored GPS coordinates, plus a frost early-warning whenever a frost night is expected within the forecast window. **Test Source** additionally gives you a preview of the next three days right on the setup page.

??? question "Can I add the same weather service twice?"
    No, each provider can only be added once per site. If you want to compare two different perspectives, combine a public service with your Home Assistant source instead.

??? question "Why doesn't 'Climate at the Site' show any values yet?"
    The climate normals are fetched automatically in the background once an outdoor, greenhouse, or balcony site has GPS coordinates — this can take a little while after adding or updating the coordinates, since the monthly background fetch doesn't run immediately after saving. First check whether coordinates are stored; if they are, a fetch simply hasn't run yet.

??? question "Do I need to set up 'Climate at the Site' myself?"
    No. It appears automatically for every outdoor, greenhouse, or balcony site with stored GPS coordinates — unlike the weather forecast, you don't need to add a separate source for it.

---

## See Also

- [Locations & Substrates](locations-substrates.md) — setting the site type and GPS coordinates
- [Configuring Weather Services](weather-services.md) — instance-wide defaults, global OpenWeatherMap fallback key (platform admin)
- [Sensors and Measurement Data](sensors.md) — other data sources for climate and substrate values
- [Home Assistant Integration](../guides/home-assistant-integration.md) — setting up an access token
- [Personalizing Your Dashboard](dashboard-personalization.md) — the "Weather forecast" widget
- [Dashboard: Weather Forecast and Frost Early-Warning](dashboard.md#weather-forecast-and-frost-early-warning)
- [Notifications: Frost Early-Warning](notifications.md#frost-early-warning)
- [Climate Zones & Hardiness](../guides/climate-zones.md)
