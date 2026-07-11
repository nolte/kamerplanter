# Aquaponics

Aquaponics combines fish farming and plant growing in one closed water loop: your fish supply the fertilizer for the plants through their waste, and the plants clean the water for the fish in return. On this page you set up an aquaponic system, monitor the nitrogen cycle, and keep an eye on the water values that decide your fish's safety. <!-- REQ-026 -->

---

## What Is Aquaponics?

In an aquaponic system, fish live in a tank whose water circulates through a biofilter (a vessel containing beneficial bacteria) and a plant growbed before flowing back to the fish. Fish waste contains ammonia, which two bacterial groups in the biofilter convert into plant-available fertilizer — this process is called the **nitrogen cycle** (see below). The plants absorb the resulting fertilizer, filtering the water in the process so the fish stay healthy.

Kamerplanter distinguishes five system types, depending on how the fish tank, biofilter, and growbed are connected:

| System Type | Description | Suited For |
|-------------|-------------|-----------|
| **Media Bed** | A growbed filled with expanded clay that also serves as the biofilter — no separate biofilter needed | Beginners, hobby setups |
| **Deep Water Culture (DWC)** | Plants float on rafts in a separate body of water | Lettuce, herbs |
| **Nutrient Film Technique (NFT)** | A thin film of water flows over the roots | Herbs, leafy greens |
| **Hybrid** | A combination of media bed and DWC/NFT | Advanced setups |
| **Wicking Bed** | Wick irrigation from a reservoir | Outdoor, rugged setups |

DWC, NFT, hybrid, and wicking bed systems each need a **separate biofilter**, since there is no substrate to host the bacteria. Only the media bed's clay pebble substrate covers this function as well.

---

## The Nitrogen Cycle Explained

The nitrogen cycle is the biological core of every aquaponic system. It runs in three steps:

1. **Ammonia (TAN)** — Fish excrete ammonia through their gills and urine. Kamerplanter records this value as **TAN** (*Total Ammonia Nitrogen*).
2. **Nitrite (NO₂⁻)** — A first group of bacteria (*Nitrosomonas*) in the biofilter converts ammonia into nitrite. Nitrite is also toxic to fish because it blocks oxygen uptake in the blood.
3. **Nitrate (NO₃⁻)** — A second group of bacteria (*Nitrobacter*/*Nitrospira*) converts nitrite into nitrate. Nitrate is largely non-toxic to fish and the most important nitrogen fertilizer for your plants.

!!! danger "TAN and free ammonia are not the same thing"
    The TAN value you measure consists of two forms: harmless ammonium (NH₄⁺) and highly toxic free ammonia (NH₃). How much of it is present as toxic NH₃ depends strongly on **pH and water temperature** — at a high pH and high temperature, a much larger share is toxic, even if the TAN value stays the same. Kamerplanter automatically calculates **free ammonia** from your TAN, pH, and temperature readings. The safe limit for free ammonia is **below 0.02 mg/L** — above that, it becomes life-threatening for your fish.

---

## Prerequisites

- At least one location is set up (the aquaponic system is managed under it).
- Aquaponics is an expert feature area and hidden by default. Set your [experience level](onboarding.md) to **Expert**, or manually enable the **Aquaponics** module under [Modules & Features](module-visibility.md).
- Creating and editing systems, water tests, fish stocks, and feedings requires at least the tenant role **Grower** (see [Tenant Management](tenants.md)).

---

## Creating a New Aquaponic System

### Step 1: Navigate to the Aquaponics Overview

Click **Aquaponics** in the navigation. You see a list of your existing systems (empty at first) and the **Create System** button.

### Step 2: Enter Basic Data

| Field | Description | Example |
|-------|-------------|---------|
| Name | Label for the system | "Tilapia-Lettuce DWC" |
| System Type | One of the five system types (see above) | Deep Water Culture (DWC) |
| Total Water Volume | Combined water volume of all tanks, in liters | 630 |
| Grow Area | Total growbed area in m² | 4 |

### Step 3: Configure Biofilter & Operations

These values determine how the system processes the nitrogen cycle and which pH range it should run at.

| Field | Description |
|-------|-------------|
| Biofilter Type | Required for DWC, NFT, hybrid, and wicking bed — optional for media bed, since the substrate already integrates the biofilter. Options are: Integrated (Clay Pebbles), MBBR (K1 Media), Trickle Filter (Lava), and Fluidized Bed (Sand). |
| Daily Feed Target | Your planned daily feed amount in grams — serves as a reference value for later analysis |
| pH Target Range (min/max) | Defaults to 6.8–7.2 |

!!! info "Why the pH target range is a compromise"
    Fish prefer pH 7.0–8.0, plants take up nutrients best at pH 5.5–6.5, and the nitrifying bacteria in the biofilter work best at pH 7.0–8.0. The default range of 6.8–7.2 is a compromise that adequately serves all three system components.

### Step 4: Notes and Save

Optionally add free-text notes (e.g. filter manufacturer details). Click **Save** to finish — the system appears in your overview immediately.

---

## Biofilter Cycling: Breaking In Your System

Before you can stock fish at full density, a bacterial culture needs to build up in the biofilter that reliably breaks ammonia down to nitrate. This process is called **cycling** — it typically takes **4–8 weeks**.

Kamerplanter shows you the current cycling status for every system:

| Status | Meaning | Fish Allowed? |
|--------|---------|----------------|
| **New** | Biofilter freshly filled, no bacteria present yet | No — only as an ammonia source for cycling |
| **Cycling** | Bacteria are building up; typical ammonia and nitrite spikes | Only a few, hardy fish (at most 25% of the target stocking density) |
| **Cycled** | Stable nitrification, no more spikes measurable | Yes, full stocking density |
| **Dormant** | Bacteria are inactive at water temperatures below 10 °C | Reduced — the system must cycle again in spring |

In the system detail view you see the **cycling progress** as a progress bar with accompanying text. The biofilter counts as cycled once TAN stays below 0.25 mg/L **and** nitrite below 0.1 mg/L for **7 consecutive days**.

!!! warning "Never stock fish before cycling is complete"
    Stocking fish before the biofilter has cycled risks ammonia and nitrite spikes that are life-threatening for the animals. Start new systems **fishless** if possible (using a pure ammonia source), or with only a few, hardy fish and close water monitoring.

---

## Recording Water Tests and Understanding the Values

Regular water tests are the single most important routine in aquaponics — they show you early whether the nitrogen cycle is working and whether the values are safe for your fish.

### Step 1: Record a Water Test

Open a system and click **Record Water Test**.

### Step 2: Enter Nitrogen Cycle Values

These values decide your fish's safety — ammonia and nitrite should sit at 0 once the system has cycled.

| Field | Meaning | Guideline |
|-------|---------|-----------|
| Ammonia (TAN) | Total Ammonia Nitrogen — fish waste that starts the cycle | 0–0.5 mg/L (0 once cycled) |
| Nitrite | Toxic intermediate product of the nitrogen cycle | 0–0.1 mg/L (0 once cycled) |
| Nitrate | Non-toxic end product, the most important plant fertilizer in the system | 5–150 mg/L (system-dependent) |
| pH | Acidity of the water; together with temperature it determines the toxic free-ammonia share | 6.8–7.2 (default range) |

### Step 3: Enter Additional Water Values

| Field | Meaning | Guideline |
|-------|---------|-----------|
| Water Temperature | Affects fish metabolism, oxygen solubility, and ammonia toxicity | Depends on fish and plants |
| Dissolved Oxygen | Oxygen content in the water — fish and biofilter bacteria need it to breathe | 5–9 mg/L |
| Carbonate Hardness (KH) | Buffers the water against sudden pH crashes | Safe from 4 °dH upward; below that, a pH crash is a risk |
| Iron | The most common nutrient deficiency in aquaponic systems | 2–5 ppm |

### Step 4: Choose Source and Save

Choose how you determined the values (**Manual**, **Sensor**, or **Test Kit**), optionally add notes, and save. The test appears immediately in the history view.

!!! note "Free ammonia is calculated automatically"
    You only enter the TAN value — Kamerplanter automatically calculates the toxic **free ammonia** share from it together with pH and temperature, and shows it as its own reading in the water quality overview.

### Water Quality at a Glance

The system detail view shows all latest readings as colored chips with an icon:

| Color & Icon | Meaning |
|---------------|---------|
| Green, checkmark | Value within the safe range |
| Blue, info icon | Value outside the optimal range, but not a concern |
| Yellow/orange, warning triangle | Value in the stress range for your fish species — monitor and consider counter-measures |
| Red, exclamation mark | Critical value — immediate action required |

Critical values are additionally shown as a prominent alert at the top of the system detail view.

!!! danger "Ammonia spike — what to do?"
    If Kamerplanter shows you a critical ammonia or nitrite value, act immediately:

    1. **Stop feeding** until the values have recovered.
    2. **Perform a partial water change** (at most 20% of system volume at once).
    3. **Maximize aeration** — more dissolved oxygen reduces ammonia's toxic effect.

    Possible causes include overfeeding, a dead fish in the tank, or a biofilter failure (e.g. from chlorine or medication residue in the water).

!!! danger "Never use acids to lower pH"
    In aquaponic systems you must **never** use acids as a pH-down agent — they can harm your fish and the biofilter bacteria. The pH naturally drops through nitrification anyway; if it's too high, waiting is usually the right move. If the pH needs to be raised, do so alternately with potassium hydroxide (KOH) or calcium hydroxide (Ca(OH)₂) — this simultaneously supplies your plants with potassium and calcium.

---

## Fish Stock and Feeding

The system detail view shows an overview of your current fish stock: name, count, and estimated total biomass per stock. Fish species come from a global species catalog with species-specific limits for temperature, pH, oxygen, ammonia, and nitrite.

<!-- Source: src/backend/app/migrations/seed_data/fish_species.yaml (8 fish species) -->

| Fish Species | Temperature Zone | Optimal Temperature |
|--------------|-------------------|----------------------|
| Nile Tilapia | Warmwater | 26–30 °C |
| Rainbow Trout | Coldwater | 12–16 °C |
| Common Carp / Koi | Temperate | 20–28 °C |
| European Catfish / Wels | Temperate | 20–26 °C |
| European Perch | Temperate | 18–24 °C |
| Goldfish | Temperate | 18–22 °C |
| Pike-perch / Zander | Temperate | 18–22 °C |
| Arctic Char | Coldwater | 8–14 °C |

!!! tip "Choose a fish species that matches your desired plants"
    Water temperature has to suit both the fish and the plants. Warmwater fish like tilapia pair well with fruiting crops (tomatoes, peppers, basil), while coldwater fish like trout pair better with leafy salads and herbs that tolerate a cooler root zone.

Creating a new fish stock, as well as recording feedings and losses (mortality), is **not yet** possible through the user interface — see the section for technical users below.

---

## For Technical Users / Self-Hosters

The following functions are already fully implemented in the backend, but still **lack a user interface** — you can currently only reach them via the REST API. Write calls require at least the tenant role **Grower** (deleting a system: **Admin**).

!!! info "API only: Managing fish stock"
    `POST /aquaponics/systems/{key}/fish-stocks` creates a new fish stock, `PATCH`/`DELETE` on the same route edit or remove it. `POST .../fish-stocks/{stock_key}/mortality` records losses. `GET .../biomass-history` and `GET .../mortality-rate` return the respective history analysis.

!!! info "API only: Logging and analyzing feeding"
    `POST /aquaponics/systems/{key}/feeding-events` logs a feeding, `GET` on the same route lists the history. `GET .../feeding-recommendation` returns a temperature-corrected daily recommendation based on fish species, biomass, and cycling status. `GET .../fcr-analysis` evaluates the Feed Conversion Ratio (FCR) over a time period.

!!! info "API only: Nutrient deficiencies and supplementation"
    `GET /aquaponics/systems/{key}/deficiency-check` checks whether iron, potassium, calcium, and other nutrients are in the deficiency range. `POST`/`GET .../supplementation` logs or lists supplement applications (e.g. Fe-DTPA, potassium hydroxide).

!!! info "API only: Safety and health status"
    `GET /aquaponics/systems/{key}/safety-status` summarizes whether all water values are within fish-safe ranges. `GET .../fish-health` returns species-specific health warnings with a recommended action. `GET .../alerts` returns the same water quality evaluations shown as chips in the detail view, as raw data.

!!! info "API only: Manually setting cycling status and history chart"
    `POST /aquaponics/systems/{key}/cycling-status` manually overrides the automatically detected cycling status. `GET .../nitrogen-cycle-chart` returns the ammonia/nitrite/nitrate history over time as a data series for your own analysis.

!!! info "API only: Editing or deleting system data"
    `PATCH /aquaponics/systems/{key}` edits the basic data of an existing system. `DELETE /aquaponics/systems/{key}` deletes it irrevocably — this requires the tenant role **Admin**.

The global, tenant-independent fish species catalog (temperature zones, species-specific limits, fish-plant compatibility) is available under `GET /fish-species` and `GET /fish-species/{species_key}/compatible-plants`.

---

## Frequently Asked Questions

??? question "Why don't I see Aquaponics in the navigation?"
    Aquaponics is an expert feature area and hidden by default. Set your experience level to **Expert**, or manually enable the module under [Modules & Features](module-visibility.md).

??? question "How long does cycling a new system take?"
    Typically 4–8 weeks, depending on water temperature. At water temperatures below 15 °C it takes noticeably longer, since the bacterial culture builds up more slowly.

??? question "Can I use existing tanks from Tank Management in an aquaponic system?"
    A fish tank, biofilter, sump, and other tank roles of an aquaponic system build on the existing [Tank Management](tanks.md) infrastructure. Linking individual tanks to an aquaponic system is currently only possible via the API.

??? question "What do I do if the pH is too low?"
    A pH that is too low (below 6.5) combined with low carbonate hardness (KH) can indicate an impending pH crash — if alkalinity drops below 4 °dH, pH can drop abruptly, which damages the biofilter bacteria. In this case, buffer with potassium hydroxide (KOH) or calcium hydroxide (Ca(OH)₂).

---

## See Also

- [Tank Management](tanks.md)
- [Sensors](sensors.md)
- [Fertilization](fertilization.md)
- [Locations and Substrates](locations-substrates.md)
