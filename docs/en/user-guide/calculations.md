# Calculations

The **Calculations** section bundles five standalone calculation tools for climate, growth, lighting and planting layout. You don't need an existing plant or planting run for this — just enter values or pick them from ready-made options, and Kamerplanter computes the result server-side.

---

## Prerequisites

- Menu item: **Plants → Calculations** (page `/pflanzen/calculations`).
- The menu item is shown by default from the ["Expert" experience level](onboarding.md#step-1-choose-your-experience-level) onward. On a lower level, enable it manually via the **"Calculators (VPD/GDD/EC)"** module in the [module settings](module-visibility.md), set to "Always on".
- For the sun-times calculator: at least one [site](locations-substrates.md) with saved GPS coordinates, unless you'd rather enter the coordinates by hand.

!!! note "Standalone calculators, no link to your plants"
    The results on this page don't automatically feed into your plant data, nutrient plans or phase rules — they're quick reference tools. To configure automatic GDD-based phase transitions, do so directly in a plant species' master data instead, see [Growth Phases](growth-phases.md).

A separate calculator for nutrient solutions and dilution (EC budget, water mixer) lives under **Fertilization → Nutrient Calculations** — see [Fertilization Logic](fertilization.md#water-mixer-and-ec-budget-calculator) for details.

---

## VPD Calculator

Vapor pressure deficit (VPD) describes how "thirsty" the air is, and is the single most important value for your plants' transpiration. This calculator computes the current VPD from temperature and humidity and shows whether the result is optimal, too low, or too high for the selected growth phase.

**Inputs:**

- **Growth phase** — a dropdown (Seedling, Vegetative, Flowering, Flushing, Ripening, Dormancy). Once selected, the field immediately shows that phase's optimal VPD target band.
- **Temperature** and **Humidity** — each a numeric field paired with a slider for quick adjustment, with the unit shown (°C and %, respectively).

The result shows the computed VPD value in kPa, a classification (optimal/too low/too high), and the target band for your selected phase.

!!! tip "Background on the formula and phase target values"
    A detailed explanation of the VPD formula (Tetens approximation) and all target bands per growth phase is in the [VPD Optimization](../guides/vpd-optimization.md) guide.

---

## GDD Calculator

Growing degree days (GDD) sum up the usable heat a plant has accumulated since a starting point, and are a more reliable maturity indicator than plain calendar days.

**Inputs:**

- **Base temperature** — the temperature threshold below which a plant doesn't grow. A numeric field plus quick-pick preset chips with typical values per crop group (Cool season, Lettuce, Tomato, Maize, Warm season) fill the field for you.
- **Daily temperatures** — an editable row list with a minimum and maximum value per day. Use **Add day** to add more rows, and the trash-can icon to remove individual rows (at least one row is always kept). If a row's maximum is below its minimum, Kamerplanter flags the row as invalid and the calculation is blocked until it's fixed.

The result shows the accumulated GDD across all entered days, and how many days were counted.

!!! tip "Base temperatures, a worked example and comparison to calendar days"
    A table of base temperatures for common crops, a step-by-step worked example, and the comparison between GDD and plain calendar time are in the [GDD Calculation](../guides/gdd-calculation.md) guide. <!-- REQ-003 -->

---

## Photoperiod Transition & DLI Calculator

This calculator plans a gradual transition of the daily light period (for example, when switching from the vegetative phase to flowering) and additionally computes the daily light integral (DLI) — the total light received over the day — for each transition day.

**Inputs:**

- **Current** and **target light period** — each a slider from 0 to 24 hours.
- **Transition days** — the number of days over which the change is spread.
- **Light intensity (PPFD)** — your fixture's photosynthetic photon flux density (PPFD) in µmol/m²/s. Enter your own value or use the preset chips for typical phase values (200/400/600). Without an explicit entry, the calculation used to fall back silently to a default value — the field now makes that value visible and adjustable.
- **Lights on** — the time of day the lighting turns on.

The result is a table with one row per transition day: light period, on/off time, and the resulting DLI in mol/m²/d.

!!! example "Example: switching to 12/12"
    Current light period 18 h, target 12 h, 7 transition days: Kamerplanter spreads the reduction evenly across the 7 days and shows you the matching on/off time and the DLI at your entered PPFD for every day.

---

## Slot Capacity

Estimates how many plants fit on a given area at a chosen plant spacing — useful when planning a new bed, tent or table.

**Inputs:**

- **Area** in m².
- **Plant spacing** in cm — a selection field with typical row spacings (10–60 cm) that also accepts free-text custom values.

The result shows three metrics as tiles: the maximum possible plant count, a recommended optimal range, and plants per m².

---

## Sun Position Calculator

Computes sunrise, sunset, dawn and dusk, and the day length for a location and a date — useful for planning sowing dates or outdoor lighting schedules.

**Inputs:**

- **Use site** (optional) — only shown once you've created at least one site with GPS coordinates. Selecting a site automatically fills in latitude, longitude and timezone from its saved values.
- **Latitude** and **Longitude** — if you're not using a site, or want to adjust the coordinates.
- **Date** — a date field, prefilled with today by default.
- **Timezone** — a selection field listing all IANA time zones (e.g. `Europe/Berlin`) instead of a free-text field, so an invalid timezone can't be entered.

The result shows sunrise, sunset, dawn and dusk, and the computed day length in hours.

!!! tip "Use a site instead of manual coordinates"
    Set up your garden or grow tent once as a [site](locations-substrates.md) with GPS coordinates and timezone — after that, a single click on **Use site** in the sun-times calculator replaces looking up coordinates by hand every time.

---

## Frequently Asked Questions

??? question "Why don't I see the \"Calculations\" menu item?"
    By default, the menu item only appears from the "Expert" experience level onward. Either set your [experience level](onboarding.md) to "Expert", or turn on the "Calculators (VPD/GDD/EC)" module specifically via the [module settings](module-visibility.md) without changing the rest of the interface.

??? question "Does a calculation affect my plant data?"
    No. All five calculators are standalone reference tools — they don't read plant data, and they don't write results back into your plants, nutrient plans or phase rules. For automatic GDD-based phase transitions, configure the thresholds directly in a plant species' master data.

??? question "Where's the EC calculator for nutrient solutions?"
    The nutrient calculator (mixing protocol, area-based dosing, water mixer, EC budget calculator) lives on its own page under **Fertilization → Nutrient Calculations** — see [Fertilization Logic](fertilization.md#water-mixer-and-ec-budget-calculator) for details.

??? question "Why isn't a site selector shown in the sun-times calculator?"
    The site selector only appears once at least one [site](locations-substrates.md) with saved GPS coordinates exists. Without a matching site, simply enter latitude, longitude and timezone by hand.

---

## See also

- [VPD Optimization (guide)](../guides/vpd-optimization.md)
- [GDD Calculation (guide)](../guides/gdd-calculation.md)
- [Growth Phases](growth-phases.md)
- [Locations and Substrates](locations-substrates.md)
- [Fertilization Logic](fertilization.md)
- [Modules & Features](module-visibility.md)
