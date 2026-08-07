# Diary

Record what you notice about each plant — with photos, tags and measurements — and keep an overview across all your plants of where an AI assessment is already available. Optionally, you can mark individual entries for analysis by your own AI agent.

---

## Prerequisites

- You are signed in (or using [Light Mode](light-mode.md) on a local device) and have created at least one plant instance.
- To create, edit, delete and mark entries you need the **Grower** or **Lead** role in your tenant. As a **Viewer** you can read every entry and analysis result, but you cannot create or mark any of them.
- To mark an entry you additionally need the consent "Individual diary entries may be analysed by my AI agent" (granted automatically in Light Mode, see [Light Mode](#light-mode) below).
- To actually run an analysis you need **your own, self-operated AI agent** — without one, a marked entry simply sits there (see [Kamerplanter does not run the analysis itself](#kamerplanter-does-not-run-the-analysis-itself)).

---

## What is the diary?

The diary exists in two places with different jobs:

| | Location | Purpose |
|---|----------|---------|
| **Capture** | The **Diary** tab on a plant's detail page | Create, edit, delete and mark entries for that one plant, with attached photos |
| **Review** | The **Diary** page in the navigation (every plant in your garden) | See every entry of every plant together, filter it, and check the analysis status at a glance |

This split is deliberate: you capture where you already have the plant open, and you review where you see all your plants together — without clicking through them one by one.

---

## Adding an entry on a plant

1. Open the side menu and navigate to your **Plants**.
2. Click the plant you want to open its detail page.
3. Select the **Diary** tab.
4. Click **Add entry**.

In the dialog you fill in:

- **Entry type** — Observation, Problem, Milestone, Measurement, Photo or Note.
- **Title** — optional; without a title the entry type is shown instead.
- **Description** — the only required value; describe freely what you observe.
- **Tags** — free-form keywords, confirmed with Enter.
- **Measurements** — optional numbers or short values, e.g. height in cm or leaf count.
- **Conditions at the time of the entry** — the sensor values covering your plant. Kamerplanter reads these itself; the dialog only shows them so you can check them (see below).
- **Photos** — up to **5 photos** per entry, captured via webcam, phone camera or file upload.

!!! note "Privacy: EXIF data"
    Photos are downscaled and stripped of EXIF metadata before upload — including GPS coordinates, camera model and capture time.

New entries appear in reverse chronological order, newest first.

### The environment is recorded automatically {#environment}

An entry records *what* you noticed. Just as important is *under which conditions* the plant was standing when you noticed it — "lower leaves drooping" reads very differently at 31 °C and 28 % humidity than at 19 °C and 65 %.

That is why Kamerplanter reads the sensor values covering your plant when an entry is **created**, and stores them with it. You do not have to type anything. Under **"Conditions at the time of the entry"** the dialog shows exactly the values that will be stored — as a preview, not as input fields.

The search runs in this order, and per individual value:

1. **Location** — sensors at your plant's location (e.g. in the tent, the greenhouse, at the raised bed).
2. **Site** — sensors at the site, for whatever the location does not cover. If the location only carries a thermometer, the site still supplies the humidity.
3. **Weather service** — for outdoor sites, the current outdoor conditions from your weather service, when no sensor answered.
4. **Nothing** — if nothing is found, the field stays empty. **No** value is estimated or invented.

Every value states where it came from (location, site or weather service) and **when it was measured**. The measurement time is almost always a little older than your entry, and that is deliberate: it is the only way to tell later whether a value really matches your observation.

!!! note "Old values are dropped, not polished"
    A reading older than one hour is not taken over at all. An entry claiming "22 °C" from a sensor that last spoke yesterday would be worse than an entry with no climate values at all.

!!! note "Separate from your own measurements"
    Automatically read values **never** land in the "Measurements" field. That one stays yours: what you enter there, you measured. It is the only way to tell afterwards what a device reported and what you noted yourself. For the same reason an automatic value cannot be edited — if you want to correct it, that is a measurement of your own and belongs under "Measurements".

**Not storing them:** the checkbox **"Store the environment values with this entry"** switches the capture off for this one entry. Your own measurements are unaffected.

**If nothing is shown**, the dialog tells you why:

| Message | Meaning | What you can do |
|---------|---------|-----------------|
| No current sensor values available | No sensor covers this plant. | Add a sensor at the [location or site](sensors.md). |
| Sensors could not be reached | The sensors did not answer just now. | Check the connection to Home Assistant. The entry can still be saved. |

The entry can **always** be saved — even if not a single sensor answers. Documenting a problem is precisely the worst moment for an error message.

!!! warning "Only on creation"
    The environment values are captured on **creation** only. If you edit an entry's text later, they stay as they are — otherwise your entry would end up carrying a climate that never held while you were observing.

### Editing or deleting an entry

Every entry in the "Diary" tab carries its own edit and delete controls — provided you have write permission in this tenant.

!!! warning "Deleting is final"
    Deleting an entry also deletes all attached photos and any analysis result. This cannot be undone.

---

## Every entry at a glance: the diary overview

The **Diary** navigation entry takes you to a list that combines the entries of **every** plant in your garden in reverse chronological order:

| Column | Content |
|--------|---------|
| Date | When the entry was created |
| Plant | Name of the plant instance, linked to its detail page |
| Species | Scientific or common name |
| Type | Observation, Problem, Milestone, Measurement, Photo or Note |
| Title / Excerpt | Title, otherwise the start of the description |
| Photos | Number of attached photos, with a thumbnail preview |
| Analysis | The analysis state, see below |

You can filter and sort, among other things:

- **By analysis state**, with the two most common quick filters shown directly: **"With result only"** and **"Waiting only"**.
- By plant, species, entry type, tag and date range. On small screens these additional filters are collapsed behind **"More filters"**.
- Via **free-text search**, which searches the title and description of every entry — not just the currently displayed page.
- By creation date (default) or analysis timestamp.

Clicking a row opens the complete entry with its photos and — where one exists — the analysis result. The overview does not reload itself; use the **Refresh** button to fetch the current state.

!!! note "In a shared garden you also see other members' entries"
    The overview is tenant-wide: in a shared garden it also shows entries from other members. You can still only mark your own — a row belonging to someone else shows the analysis state but no marking control (exception: the Lead role, see [Who may mark an entry?](#who-may-mark-an-entry)).

---

## Marking an entry for AI analysis

Open an entry — on the plant's "Diary" tab or in the overview — and click **Analyse**. The entry switches to "Waiting for analysis". While it stays in that state you can undo the marking with **Withdraw marking**; once an agent has claimed the entry, that is no longer possible.

Nothing is **ever** analysed automatically — there is no automatism, no "analyse everything" default and no rule set that selects entries by keyword. You mark every single entry yourself, deliberately.

### Kamerplanter does not run the analysis itself {#kamerplanter-does-not-run-the-analysis-itself}

!!! warning "Without your own agent, nothing happens"
    Kamerplanter itself never calls **any** language model — your instance has no model key, no outgoing call and no cost arising from this feature. The actual analysis is performed by an **external agent that you operate yourself**, which fetches your marked entries using your own API key. Without a running agent, a marked entry stays "Waiting for analysis" — indefinitely, until you start an agent. That is a deliberate property of this feature, not a bug: it keeps your instance operable without a model key and without outbound network access.

    A matching agent recipe lives in a separate repository, apart from Kamerplanter itself. If you want to set up your own agent, the technical interface for it is documented under [MCP Server](../api/mcp-server.md).

!!! note "No promise about processing time"
    "Waiting for analysis" means exactly that — there is no progress bar and no estimate of how long it takes. It depends entirely on when your own agent next runs.

### Who may mark an entry? {#who-may-mark-an-entry}

- **Viewers** can read entries and results, but cannot mark anything.
- **Growers** can only mark entries they **authored themselves**.
- **Leads** can mark any entry in the tenant, including those of other members.

This restriction applies in addition to the consent — both conditions must hold before an entry can be marked: the right role or authorship, **and** the granted consent "Individual diary entries may be analysed by my AI agent". If either condition is missing, the control is either hidden or the request is refused.

### The five analysis states

| State | Meaning |
|-------|---------|
| Not marked | No analysis has been requested for this entry. |
| Waiting for analysis | Marked, but not yet claimed by an agent — with no promise about when that happens. |
| Being analysed | An agent has claimed the entry and is analysing it right now. |
| Result available | The analysis is complete; the result is attached to the entry. |
| Analysis failed | The agent reported an error; you can mark the entry again. |

---

## What goes into the analysis

The **entire entry** is analysed, not just a single photo: title and description, entry type and tags, the recorded measurements, the [automatically captured environment values](#environment), all attached photos, and the plant context (species, cultivar, current phase, location, planting date) — because the same discolouration means something different on a seedling than on a plant in bloom, and different at 31 °C than at 19 °C.

!!! note "Only downscaled image renditions, never the original"
    Only downscaled image renditions without EXIF data are sent to your agent and on to your language model — never the original photo, and never the capture location or device identifier.

---

## Reading the result

Once an analysis is complete, the entry shows:

1. A **summary** first.
2. An expandable **finding list** — each finding with a label, a confidence and a rationale. Confidence always appears as a number **and** in words (e.g. "72 % — fairly likely"), because a bare percentage suggests a precision a language model does not have.
3. **Recommended actions** as a list.
4. **Provenance**: the model used, the recipe version, the analysis timestamp, and which photos were actually evaluated.

!!! warning "The disclaimer is always visible"
    "This assessment comes from a language model, is a hypothesis and does not replace a professional inspection." — this notice appears with every result, never hidden behind a collapsible element. An analysis result is an assessment, not a diagnosis, and does not replace your own professional judgement.

---

## Analysing again

For a completed or failed entry you can choose **Analyse again**. This resets the entry to "Waiting for analysis"; a new result **overwrites** the previous one completely — there is currently no history of multiple analyses.

---

## Diary photos and gallery photos

Photos on a diary entry are a **separate category** of their own — independent of the photos in the [plant photo gallery](plant-photos.md). A gallery photo shows a plant's growth over time; a diary photo belongs to exactly one entry and its observation. Both areas can be used independently and share neither photos nor the diary's 5-photo limit.

---

## Managing or withdrawing consent

You find the consent "Individual diary entries may be analysed by my AI agent" in the **Consents** tab of the privacy area (profile picture or initials in the top right → **Privacy**) — see [Privacy (GDPR) — Managing Consents](privacy.md#managing-consents-gdpr-art-7).

Withdrawing it takes effect immediately: you can no longer mark new entries afterwards. Existing analysis results are unaffected and remain visible.

---

## Light Mode

In [Light Mode](light-mode.md) there are no user accounts and therefore no consent mechanism — consent for AI analysis is considered granted automatically. The restriction "mark only your own entries" also does not apply: in a light instance every entry belongs to the same system user anyway.

---

## For Technical Users / Self-Hosters {#for-technical-users-self-hosters}

For your own agent to fetch, claim and write back results for entries, it needs a personal API key (**Account settings → API keys → create**) and access to five dedicated MCP tools. The complete tool contract with error codes and the configuration variable for the maximum image payload is documented under [MCP Server — Diary Analysis](../api/mcp-server.md#diary-analysis-external-agents).

---

## Showing or hiding the module

The diary is its own, hideable module (`diary`, category "Care & Planning", shown by default from the Beginner experience level onward). You can hide or show it like any other non-essential module — see [Modules & Features](module-visibility.md).

---

## Frequently asked questions

??? question "Why are the sensor values not listed under my measurements?"
    Because nobody could tell afterwards what a device reported and what you measured yourself. Your measurements stay yours; the automatic ones sit next to them, with their origin and measurement time.

??? question "The dialog showed 22 °C, but 22.4 °C was stored. Is that a bug?"
    No. The preview shows the state when the dialog was opened; what is stored is the state at the moment of saving. The entry records what held when it was written — not what the dialog painted a minute earlier.

??? question "Can I correct an automatically captured value?"
    Not directly. A corrected value is a measurement of its own — enter it under "Measurements". The automatic value stays next to it, so the difference remains visible.

??? question "I marked an entry, but nothing happens. Why?"
    That is expected. Kamerplanter does not analyse entries itself — that requires an agent that you operate. As long as none is running, the entry stays "Waiting for analysis". Once you start your agent, it fetches marked entries on its own.

??? question "How long does an analysis take?"
    There is no promise about that. It depends entirely on when your own agent runs — not on Kamerplanter.

??? question "Can I mark other members' entries in a shared garden?"
    Only with the Lead role. With the Grower role you can only mark entries you authored yourself.

??? question "Are my original photos sent to a language model?"
    No. Only downscaled image renditions without EXIF data leave the instance — never the original, never the capture location or device identifier.

??? question "Is the analysis result a reliable diagnosis?"
    No. It is a hypothesis from a language model and does not replace a professional inspection. This disclaimer is shown with every result.

??? question "What happens to an existing result if I withdraw consent?"
    It remains and stays visible. Withdrawing consent only prevents you from marking new entries going forward.

??? question "Why do I see entries in the overview that aren't mine?"
    The diary overview is tenant-wide — in a shared garden it shows the entries of every member. This matches the general visibility inside a garden: all members see the same data, regardless of role (see [Roles & Permissions](../reference/roles-and-permissions.md)).

??? question "Can I cancel a running analysis?"
    No. Once an agent has already claimed the entry ("Being analysed"), the marking can no longer be withdrawn. Withdrawing only works while the entry is still "Waiting for analysis".

---

## See also

- [Plant Photo Gallery](plant-photos.md) — record a plant's growth in photos
- [Privacy (GDPR)](privacy.md) — consents, retention and your rights
- [Modules & Features](module-visibility.md) — show or hide functional areas
- [Roles & Permissions](../reference/roles-and-permissions.md) — who can do what in your garden
- [Planting Runs](planting-runs.md) — group management for plants
- [MCP Server](../api/mcp-server.md) — technical interface for building your own analysis agent
