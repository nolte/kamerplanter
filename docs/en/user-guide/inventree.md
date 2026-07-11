# Equipment & Inventory (InvenTree)

On this page you manage your **equipment** — pumps, meters, tools, lighting, filters and cleaning agents — as standalone objects, and you can optionally link them to **InvenTree**, a separate, external inventory management system. The link saves you from maintaining data twice: stock levels and consumption are synced automatically between both systems. <!-- REQ-016 -->

!!! info "Optional integration"
    InvenTree is not a required component. Without an InvenTree connection, Kamerplanter keeps working without any limitation — you can manage equipment, fertilizers and tanks normally, just without automatic stock sync. If an already configured InvenTree instance goes down temporarily, that never blocks your work in Kamerplanter (graceful degradation).

---

## Prerequisites

- Access to **Inventory → Equipment** in the navigation — any tenant member can view equipment, the tenant role **Grower** or **Admin** is required to create and edit it, and **Admin** is additionally required to delete it
- For the InvenTree link, additionally: a reachable InvenTree instance with a valid API token, and the tenant role **Admin** to set up the connection (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters))

---

## What is InvenTree?

[InvenTree](https://github.com/inventree/inventree) is a separate, open-source inventory management system — a system you run in addition to Kamerplanter. Three terms matter for the link:

- **Part** — a single article in InvenTree, e.g. "BioBizz Bio-Bloom 1L" or "Bluelab pH Pen". Every part has a unique numeric ID.
- **Stock** — the quantity of a part currently on record in InvenTree, e.g. "12.5 liters" or "3 units".
- **Consumption tracking** — automatically reporting consumption (e.g. milliliters of fertilizer used during a feeding) back to InvenTree as a stock booking.

Kamerplanter can link three kinds of its own objects to an InvenTree part: **fertilizers**, **tanks** and **equipment**. For every link, Kamerplanter also keeps track of the stock level last pulled from InvenTree.

---

## Managing equipment

Equipment is your gear that is neither a fertilizer nor a tank: pumps, pH/EC meters, tools, lighting, filters and cleaning agents.

### Step 1: Navigate to the equipment overview

Click **Inventory → Equipment** in the navigation.

### Step 2: Add a new equipment item

Click **Add equipment** and fill in the form:

| Field | Description |
|------|-------------|
| Name | Name of the equipment item, e.g. "Bluelab pH Pen" |
| Type | Tool, consumable, sensor / meter, lighting, pump, filter, container, cleaning agent, or other |
| Status | Active, In maintenance, Stored, Defective, or Retired |
| Brand, Model | Optional, for your own overview |
| Serial number | Optional |
| Notes | Free text, e.g. calibration notes |

### Step 3: Optionally link it to InvenTree

In the **InvenTree link (optional)** section, enter the **InvenTree part ID** — the numeric ID of the matching part in your InvenTree instance.

!!! note "Partially available: InvenTree part ID on equipment"
    Entering the part ID stores the identifier directly on the equipment item (it shows as a chip in the overview table) — on its own, though, it doesn't create a synced link yet. For stock and consumption to actually sync with InvenTree automatically (stock sync), a reference also has to be created via the API (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)). A part search built directly into the Kamerplanter interface is planned but not yet implemented — for now you find the part ID in your InvenTree instance itself.

### Editing and deleting

Use the icons in the table row to edit or delete an equipment item. Deleting requires the tenant role **Admin**; editing is also open to the **Grower** role.

!!! info "Location, purchase date and warranty aren't editable in the interface yet"
    Kamerplanter can also store an assigned location, a purchase date and a warranty expiry date for each equipment item — these fields can currently only be set via the API, not through the create/edit form.

---

## Connection status on the overview page

At the top of the equipment page, a banner shows whether an active InvenTree connection exists:

- **"InvenTree connection … is active"** (green, when the last reachability check succeeded) — stock levels are synced automatically.
- **"No InvenTree connection configured"** — equipment can still be managed normally.

---

## Syncing stock levels (stock sync)

When an InvenTree connection is active and at least one link (reference) has been created, Kamerplanter automatically pulls current stock quantities from InvenTree:

- **Stock pull (read):** hourly, for all linked fertilizers, tanks and equipment.
- **Consumption push (write):** every 5 minutes, for pending stock bookings.

Both runs happen in the background without any action from you. If the newly pulled stock deviates by more than 20% from the last known value, Kamerplanter logs it internally as a warning — useful when someone withdrew or restocked a larger quantity directly in InvenTree.

---

## Tracking consumption automatically (consumption tracking)

!!! note "Partially available: Automatic consumption reporting"
    The mechanism for automatic consumption bookings is already fully built: a link can be marked with **auto-deduct**, every booking is traceably recorded in the immutable transaction log, and failed transfers are automatically retried up to three times. However, automatically **triggering** these bookings from a feeding event or a tank maintenance entry isn't yet wired into those workflows — in this version, no automatic bookings are created when you log a feeding or maintenance entry. The transaction log and the transfer mechanism can already be used via the API today, once bookings are created e.g. by your own script.

Once a link has **auto-deduct** enabled, Kamerplanter will automatically create a stock booking ("consumption") when you:

- log a **feeding event** (amount of each fertilizer used), or
- document a **maintenance** entry on a tank that used a linked consumable (e.g. a cleaning agent).

Every booking starts with the status **pending** and is sent to InvenTree on the next transfer run (at most 5 minutes later). If a transfer fails, Kamerplanter retries it up to three times before marking the booking as **failed**.

---

## For Technical Users / Self-Hosters {#for-technical-users-self-hosters}

The InvenTree integration is **disabled** by default and must be enabled by the operator of the instance.

| Environment variable | Default | Description |
|---|---|---|
| `INVENTREE_ENABLED` | `false` | Kill switch for the entire InvenTree integration. Without this variable, every InvenTree endpoint returns a "feature disabled" error (HTTP 409) instead of a server crash. |
| `INVENTREE_ALLOW_PRIVATE_ENDPOINT` | `false` | Allows an InvenTree instance on the local network or cluster (private/LAN address). Without this opt-in, Kamerplanter blocks connections to private addresses for security reasons (SSRF protection) — analogous to `HA_ALLOW_PRIVATE_ENDPOINT` for the Home Assistant integration. |

Once the integration is enabled, you set up connections and links via the REST API — there is no interface for this yet:

**1. Create a connection** (tenant role Admin):

```
POST /inventree/connections
{
  "name": "Main inventory",
  "base_url": "https://inventree.example.com",
  "api_token": "<your InvenTree API token>",
  "verify_ssl": true
}
```

The API token is stored Fernet-encrypted (AES-256) and never returned in plaintext — responses only contain the field `api_token_set: true`. `POST /inventree/connections/{key}/health-check` checks reachability without disclosing whether an auth failure or a wrong URL is the cause.

**2. Search for matching InvenTree parts** (any tenant member):

```
GET /inventree/browse/parts?query=BioBizz&limit=25
GET /inventree/browse/categories
```

**3. Link a Kamerplanter entity** (tenant role Grower or Admin):

```
POST /inventree/references/link
{
  "entity_collection": "fertilizers",
  "entity_key": "<key of the fertilizer>",
  "inventree_part_id": 42,
  "auto_deduct": true,
  "deduct_unit": "ml"
}
```

`entity_collection` only accepts `fertilizers`, `tanks` or `equipment` — any other value is rejected with HTTP 422.

**4. Trigger a manual sync:**

```
POST /inventree/sync/trigger
```

Immediately runs a combined stock pull and consumption push, outside the hourly/5-minute rhythm.

**5. View the transaction log:**

```
GET /inventree/transactions?status=pending
```

Lists all stock bookings with their status (`pending`, `synced`, `failed`).

!!! warning "Connection management is restricted to the tenant role Admin"
    Only members with the tenant role **Admin** may create, change or delete InvenTree connections. Linking individual fertilizers, tanks or equipment, as well as triggering a sync, is also open to the **Grower** role; deleting an equipment item likewise requires Admin.

---

## Frequently asked questions

??? question "Do I have to use InvenTree to manage equipment?"
    No. You can create, edit and delete equipment at any time without an InvenTree connection. The InvenTree link is a purely optional extra for automatic stock sync.

??? question "What happens if my InvenTree instance is unreachable?"
    That never blocks your work in Kamerplanter. Equipment, fertilizers and tanks you've already entered remain fully usable. The connection status shows "unreachable", and pending stock bookings wait until the connection is restored.

??? question "Where do I find the part ID in InvenTree?"
    Open the part you want in your InvenTree instance — the ID is shown in the URL address bar (e.g. `.../part/42/`) and usually also directly on the part's detail page.

??? question "Can I link fertilizers or tanks to InvenTree directly in the interface?"
    Not yet — for now, only the REST API supports that (see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters)). Only equipment already has an input field for the InvenTree part ID in the interface.

---

## See also

- [Fertilization Logic](fertilization.md)
- [Tank Management](tanks.md)
- [Locations & Substrates](locations-substrates.md)
- [Glossary: InvenTree](../reference/glossary.md#inventree)
- [Environment Variables: InvenTree Integration](../reference/environment-variables.md#inventree-integration-req-016)
