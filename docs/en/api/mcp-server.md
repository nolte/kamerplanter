# MCP Server (Model Context Protocol)

!!! note "Partially available"
    The MCP framework, authentication, the permission model and a first core tool set are implemented and usable today. The full tool catalog envisioned by the specification (around 30 tools, including setup macros, bulk plant creation, IPM/harvest write tools and the knowledge-base bridge) as well as a standalone MCP process with its own Helm chart are not yet implemented — the server currently runs **in-process with the backend** (internal reference: REQ-033). The affected sections are marked individually below.

The MCP server exposes selected Kamerplanter capabilities to external LLM clients (e.g. Claude Desktop, Claude Code, custom agents) via the open [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), a protocol that lets language models call a system's structured "tools". This lets an LLM client ask directly "Which plants do I need to water today?" and get a structured answer from your real data — without opening a separate app.

---

## What is the MCP server?

Unlike the generic REST API, the MCP server does **not** mirror 1:1 CRUD endpoints — it exposes a curated, semantically high-level tool palette. A tool like `get_due_care_tasks` encapsulates a whole use case and returns compact, LLM-friendly JSON, instead of the LLM having to chain several REST calls together.

The MCP server is a **complementary, purely machine-to-machine interface** for external clients — it does not replace the [AI assistant](../user-guide/ai-assistant.md) built into the app, which supports Kamerplanter users directly with knowledge questions and chat. The two are complementary: the AI assistant is *internal*, for app users; the MCP server is the *external* interface through which third-party LLM clients use Kamerplanter as a tool.

## Enabling

The MCP server is disabled by default. As long as `MCP_SERVER_ENABLED` is not set to `true`, **all** `/mcp/*` endpoints answer `404 Not Found` — the interface effectively does not exist, mirroring the AI assistant's own opt-in mechanism. See [Environment Variables — MCP Server](../reference/environment-variables.md#mcp-server) for details on the variable.

## Transport & Endpoints

The MCP server runs in-process with the backend and exposes its tools under `/api/v1/mcp/`:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/mcp/tools` | REST-friendly tool listing — shows the tools the caller's roles unlock, plus the gardens the key covers |
| `POST` | `/mcp/tools/{tool_name}` | REST-friendly tool call with a JSON body as arguments |
| `POST` | `/mcp` | **The MCP endpoint**: JSON-RPC 2.0 over Streamable HTTP — `initialize`, `tools/list`, `tools/call`, `ping` |
| `GET` | `/mcp` | `405` — this server sends no server-initiated messages, an answer the transport explicitly permits |
| `DELETE` | `/mcp` | Terminates the session named in the `Mcp-Session-Id` header |
| `POST` | `/mcp/rpc` | Retained alias of `POST /mcp` (deprecated) |

!!! info "API only / operator configuration: transport"
    A standalone `stdio` transport (the server started locally by the client, typical for Claude Desktop configurations) is specified but not yet implemented — currently only Streamable HTTP is available. An MCP client connects to the full backend URL, e.g. `https://api.kamerplanter.example.com/api/v1/mcp`.

## Authentication: your own API key

The MCP server accepts **API keys** — your personal one just as much as a service account's. What it never accepts is a JWT access token or an interactive session. The key is sent as an `X-API-Key` header or as `Authorization: Bearer kp_...` and always carries the `kp_` prefix (see also [Authentication — API Keys (M2M Integration)](authentication.md#api-keys-m2m-integration)).

You create your personal key yourself via `POST /api/v1/auth/api-keys` and can revoke it individually at any time, without changing your password.

!!! warning "An API key is a long-lived credential"
    Unlike a login token, an API key does not expire after minutes — which is exactly what makes it suitable for a permanently running MCP client. Treat it like a password: whoever holds it can do everything you can do in your gardens. Create a separate key per client so you can revoke them individually.

### You only ever see your own data

A key grants exactly the gardens (tenants) its account is an **active member** of, resolved from the same source the regular API uses. Nothing is reachable over MCP that you could not see in the web UI. A garden you are not a member of behaves exactly as if it did not exist (`not_found`) — the interface will not even reveal that it is there.

Inside a garden, normal visibility applies: in a community garden every member sees the same plants, in the app as well as over MCP.

```http
POST /api/v1/mcp/tools/get_due_care_tasks
X-API-Key: kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{"urgency": "actionable", "tenant": "my-garden"}
```

### Several gardens: the `tenant` parameter

If you are a member of several gardens, your key covers all of them. Which one a call applies to is decided per call through the `tenant` argument (the garden's slug). With exactly one membership you may omit it; with several it is required — the server does not guess, it asks you to name the garden. The `list_tenants` tool tells you which slugs are available.

The order behind this matters: the server resolves the **garden first** and only **then** checks what you may do there. Your role can differ per garden — admin in your own, viewer in a community garden. Checked the other way round, you would hold your strongest role everywhere.

### Resolving a key's context (M2M)

A separate endpoint resolves a raw key into its context — useful for a future standalone MCP process (see the status note above) that cannot validate the key itself:

```http
POST /api/v1/auth/service-accounts/validate
Content-Type: application/json

{"api_key": "kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
```

**Response (200):**

```json
{
  "service_account_key": "sa-abc123",
  "display_name": "Diagnose-Bot",
  "tenants": [
    {
      "tenant_key": "t-home",
      "tenant_slug": "home",
      "role": "viewer",
      "mcp_permissions": ["mcp.read"]
    }
  ]
}
```

This endpoint is deliberately restricted to service accounts. An invalid, revoked or personal key returns the same generic `401 Unauthorized` here — the API never reveals whether a valid key with different properties exists. The MCP server itself carries no such restriction: your personal key works there.

### Obtaining a key

**Through the UI:** **Account settings → API keys → create.** The key is shown **exactly once** — afterwards only its hash is stored and it cannot be displayed again. Copy it and paste it straight into your client config. The same table lets you revoke any key individually.

**Through the API:** `POST /api/v1/auth/api-keys` with `{"label": "claude-code"}`. The key immediately covers all your gardens with exactly the roles you hold in each. Pass `tenant_scope` at creation to limit it to a single garden when a client should only work there.

!!! info "Available in light mode too"
    A light-mode instance has no user accounts — sign-in, sessions and security settings are deliberately absent there. **API key management is still present**, because it is the only credential the MCP server accepts. The key belongs to the system user, which is a member of the default garden. This grants no extra authority: anyone who can reach a light instance already has full access — the key merely makes that access usable from outside. Which is exactly why a light instance does not belong on the public internet.

**As a service account — operator step:**

!!! warning "Not yet implemented"
    Full, self-service service-account management (create, rotate, deactivate via the API — see [Service Accounts & API Keys](service-accounts.md)) is specified but not yet implemented. Today, creating a user account with `account_type: "service"` is an **operator step** outside the public API, not a self-service flow (internal reference: REQ-023).

For an MCP client to obtain a working key today, the following pieces are needed:

1. A user account with `account_type: "service"` (no password, no interactive login) — created by the instance operator.
2. A tenant membership for that account with exactly the role (`viewer`/`grower`/`admin`) matching the desired [permission level](#permission-model-mcpread-mcpwrite-mcpsetup).
3. An API key for that account, technically the same mechanism described under [Service Accounts & API Keys — Using the API Key](service-accounts.md#using-the-api-key) — but since a service account is never logged in interactively, it cannot request the key itself via the `/auth/api-keys` endpoint; this step, too, currently runs through the operator.

## Setting up a client (Claude Code)

Claude Code reads MCP servers from an `.mcp.json` in the project directory (or from your global configuration). Add the Kamerplanter server as an HTTP server:

```json
{
  "mcpServers": {
    "kamerplanter": {
      "type": "http",
      "url": "https://kamerplanter.example.com/api/v1/mcp",
      "headers": {
        "X-API-Key": "kp_your_personal_api_key"
      }
    }
  }
}
```

For a local development stack the URL is `http://localhost:8000/api/v1/mcp`.

!!! danger "The key sits in the file in plain text"
    Keep `.mcp.json` **out of** the git repository once it holds a real key — add it to `.gitignore` or use the global Claude Code configuration outside the project. Anyone who reads the file can do everything you can do in your gardens. You can revoke an individual key at any time.

### Check the connection first

Before adding the entry, a direct test is worth the minute — it shows immediately whether the URL and key are right:

```bash
# 1. Handshake: does the server answer as an MCP server?
curl -sS -X POST https://kamerplanter.example.com/api/v1/mcp \
  -H "X-API-Key: kp_your_personal_api_key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}'

# 2. Which tools does my key unlock?
curl -sS -X POST https://kamerplanter.example.com/api/v1/mcp \
  -H "X-API-Key: kp_your_personal_api_key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 3. A real call: which gardens does the key cover?
curl -sS -X POST https://kamerplanter.example.com/api/v1/mcp \
  -H "X-API-Key: kp_your_personal_api_key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_tenants","arguments":{}}}'
```

A `404` on step 1 means the MCP server is not enabled on that instance (`MCP_SERVER_ENABLED`). A `401` means the key is invalid, revoked or expired.

After that you can simply ask in conversation: *"Which plants do I need to water today?"* — Claude calls `get_due_care_tasks` itself. If your key covers several gardens, name the one you mean (*"…on my balcony"*) so the model can fill in the `tenant` parameter.

!!! info "Transport: Streamable HTTP"
    The server implements the **Streamable HTTP transport** (protocol revisions `2025-06-18`, `2025-03-26` and `2024-11-05`). On `initialize` it negotiates the revision with your client and issues an `Mcp-Session-Id` that the client then echoes; an expired session is answered with `404`, at which point the client re-initialises. Responses always come back as `application/json`, which the transport explicitly permits. It offers no server-initiated stream: `GET` on the endpoint answers `405`. That is the transport's sanctioned answer, and it means progress updates during long operations are not available yet.

!!! warning "Not yet implemented: Claude Desktop"
    Claude Desktop starts an MCP server as a local subprocess and talks to it over `stdio` — it cannot bind an HTTP URL directly. The thin bridge client needed for that is specified but not yet implemented (internal reference: REQ-033). The configuration above therefore applies to Claude Code and other clients with an HTTP transport.

## Permission model: `mcp.read` / `mcp.write` / `mcp.setup`

Every tool requires exactly one of three MCP permissions. These are not granted separately — they are bound to the role your account holds **in the garden being addressed**, the same role used for human members ([Tenants & Gardens](../user-guide/tenants.md)):

| Tenant role | `mcp.read` | `mcp.write` | `mcp.setup` | Typical use |
|-------------|:----------:|:-----------:|:-----------:|-------------|
| **viewer** | ✓ | ✗ | ✗ | Read-only diagnose bot |
| **grower** | ✓ | ✓ | ✗ | Day-to-day operation (confirm care, move/archive plants) |
| **admin** | ✓ | ✓ | ✓ | One-off onboarding, site creation |

A call without the required permission is rejected with the error code `permission.denied` and recorded in the audit log as `status: "denied"` (see [Audit Trail & Privacy](#audit-trail-and-privacy)). `mcp.setup` is deliberately the most restrictive class: it governs site creation — an action that can affect an entire plant-data hierarchy — and is therefore reserved for the `admin` role only.

Because the role applies per garden, the same key can write in your own garden and be refused the very same action in a community garden where you are only a viewer. The tool listing (`GET /mcp/tools`) therefore shows everything you may do **somewhere**; the binding check is the one made on the individual call.

## Tool Catalog (current state)

!!! note "Partially available: tool scope"
    56 tools are implemented, which covers reading fairly thoroughly, plus the five diary-analysis tools (see [Diary Analysis: External Agents](#diary-analysis-external-agents)) and the eight tools of the growth-phase layer (see [Growth Phases and Lifecycle](#growth-phases-and-lifecycle)). For the remaining **writing**, gaps remain: setup macros for apartment/growbox/outdoor garden, bulk plant creation, site and location management, and writing back a harvest (`record_harvest`) or an applied treatment (`apply_treatment`). Expansion is a documented follow-up.

!!! info "New: what an analysis agent can write back"
    Five tools were added that externally operated analysis agents needed. Each one ships paired with the read tool that finds its result again — a write no read tool surfaces afterwards counts as a defect here:

    - `record_feeding_event` records the **amount, EC and pH** of a feeding plus its tank reference. Until now the care log only said "confirmed" — a yes/no that cannot tell undersupply from oversupply, although the two are corrected in opposite directions. Visible through `get_plant_diagnostics`.
    - `get_plant_diagnostics` returns **the trend, not just the latest value**: EC and pH series over a window you choose (input, post-feed and runoff kept apart), a sensor snapshot, IPM inspections, the safety interval and recent care — in a single call.
    - `create_inspection` records an IPM inspection and keeps, per finding, the **confidence** and the **affected plant part**. Without it, a plant tended entirely through agents kept an empty pest history forever. Visible through `get_plant_inspections`.
    - `search_plant_knowledge` searches the knowledge base and returns **citable source references**, so a rationale can name where it came from.
    - `assign_nutrient_plan` binds an **existing** nutrient plan to a plant. *Editing* plans stays deliberately a job for the web UI. Visible through `get_plant_nutrient_plan`.

### Read tools (`mcp.read`)

| Tool | Purpose |
|------|---------|
| `list_tenants` | List your gardens with the role you hold in each — supplies the slugs for the `tenant` parameter |
| `list_plants` | List plants, optionally filtered by name — this is how "my tomato" becomes the `plant_key` the write tools need |
| `get_plant` | One plant in detail: species (with resolved name), phase, location, substrate (with resolved type and name), planting and removal dates |
| `get_plant_care_log` | A plant's care history — with `reminder_type: "watering"` this is the watering log |
| `get_plant_diagnostics` | A plant's diagnostic snapshot in **one** call: EC/pH **trend** over a window you choose (input, post-feed and runoff kept apart), sensor values at its location, IPM inspections, safety interval and recent care |
| `list_diary_entries` | Browse diary entries, filtered by plant, species, entry type, tag, analysis state and date range — newest first, with measurements, but without the free text |
| `list_plants_at_location` | All plants at a given site, bed or slot |
| `list_nutrient_plans` | Available nutrient plans — your own plus global templates |
| `get_nutrient_plan` | One plan with every phase: NPK ratio, target EC, nutrients, week window |
| `get_plant_nutrient_plan` | The plan that applies to a specific plant |
| `get_sowing_calendar` | Sowing, planting-out and harvest windows per species, shifted against your site's frost dates |
| `list_pests` / `get_pest` | Search pests — by damage symptom too. The detail view shows counter-measures (gentlest first) **and matching beneficial insects**, specialists first |
| `list_diseases` / `get_disease` | Diseases: pathogen, incubation period, triggering conditions, affected plant parts |
| `get_treatment` | One treatment in detail — with the **safety interval** before harvest, protective equipment and application |
| `get_plant_inspections` | A plant's IPM inspections: pressure level, findings, observed symptoms |
| `list_fertilizers` | Available fertilisers with EC contribution and maximum dose |
| `calculate_mixing_protocol` | Fertiliser calculator: per-product doses for your target volume and EC, in the correct mixing order |
| `list_cultivars` / `get_cultivar` | A species' cultivars: breeder, traits, seed type, days to maturity |
| `list_substrates` | Substrate catalogue: media and their properties |
| `list_overwintering_profiles` | Overwintering profiles: protection method, storage conditions, timing |
| `list_starter_kits` | Starter kits for getting going |
| `list_phase_definitions` | Growth-phase definitions behind the lifecycle logic — the individual building blocks, not the sequences |
| `get_species_phase_sequence` | The phase sequence a species actually runs on: cycle type, whether it repeats, whether a rest period is required — plus the ordered phases with their effective duration and the "terminal" and "harvest allowed" flags |
| `list_phase_sequences` | The catalogue of all phase sequences — so you can not only establish that an assignment is wrong but name the right one |
| `list_species_by_phase_sequence` | The reverse lookup: every species bound to one sequence. A houseplant sitting in the same bucket as Brussels sprouts and leeks is not a one-off, it is a template collision |
| `get_species_lifecycle` | A species' lifecycle: annual or perennial, whether it dies after flowering (monocarpic) or flowers again (polycarpic), life expectancy, dormancy requirement |
| `get_plant_phase_status` | A plant's phase state: days in phase, next phase, cycle number, whether a harvest is scheduled — plus a `phase_state` that tells "never started", "stuck in an unresolvable phase", "between cycles" and "running" apart |
| `get_plant_phase_history` | A plant's phase history with the reason, date and actual duration of each transition |
| `list_hardiness_zones` | Hardiness zones with their temperature ranges |
| `search_glossary` | Look up domain terms from the glossary (VPD, EC, safety interval …) |
| `search_plant_knowledge` | Search the knowledge base (RAG) — returns **citable** source references with a score, so a rationale can name where it came from. Tenant-independent; only the query itself leaves the instance |
| `list_species` | List the plant species catalog (paginated) |
| `get_species_info` | **Full** master data for one species: sowing, bloom and harvest windows, hardiness, frost sensitivity, nutrient demand, toxicity, companion-planting hints and its cultivars |
| `list_planting_runs` | List the tenant's planting runs, optionally filtered by status |
| `list_tasks` | List the tenant's tasks, optionally filtered by status |
| `get_due_care_tasks` | Today's / overdue care reminders, grouped by urgency |
| `get_harvest_readiness` | Harvest-readiness overview across all active plants |
| `get_mcp_activity` | This account's own MCP call history (self-service view, see below) |
| `list_pending_diary_analyses` | Work queue of diary entries marked for AI analysis — no free text, no images (see [Diary Analysis: External Agents](#diary-analysis-external-agents)) |
| `get_diary_entry` | One diary entry with its plant context, without image data |
| `get_diary_entry_photos` | A diary entry's photos as image content blocks — the only tool in the palette that returns anything other than text |

### Write tools (`mcp.write`)

| Tool | Purpose |
|------|---------|
| `confirm_care_task` | Confirm a care reminder for a plant ("I have watered it") |
| `archive_plant` | Mark a plant as disposed / given away / died — **never** a hard delete, history is retained |
| `set_plant_location` | Move a plant to another site / location / slot |
| `add_plant_diary_entry` | Record a diary entry (observation, problem, measurement) for a plant — text only, no photos. `measurements` now names the recognised quantities with their unit in the key (`ec_ms_cm`, `ph`, `temperature_c`, `humidity_percent`, `height_cm`, `leaf_count`) and still accepts any further key of your own |
| `claim_diary_analysis` | Exclusively claim a waiting diary entry (lease) |
| `submit_diary_analysis` | Write back the analysis result of a claimed diary entry |
| `record_feeding_event` | Record a feeding: litres applied, EC and pH before and after, runoff EC/pH, and the tank reference. The care log only knows "confirmed" — here are the numbers |
| `create_inspection` | Record an IPM inspection: pressure level, symptoms and **structured findings** with a confidence (0.0–1.0) and the affected plant part |
| `assign_nutrient_plan` | Bind an **existing** nutrient plan to a plant (your own or a global template). Creating or editing plans is deliberately not a tool |
| `transition_plant_phase` | Put a plant into a phase, or correct a wrong one. The target is validated against the sequence **that plant's species** runs on — a phase key from elsewhere would park the plant in a phase its lifecycle can never advance out of |

### Setup tools (`mcp.setup`)

| Tool | Purpose |
|------|---------|
| `create_site` | Create a site root (apartment, garden, balcony, greenhouse, windowsill, grow tent) |
| `assign_species_phase_sequence` | Bind a species to an **existing** phase sequence. Requires `mcp.setup` rather than just `mcp.write`, because species and sequences belong to the shared catalogue: a single binding changes the schedule of every plant of that species in *every* garden. *Defining* sequences stays deliberately a job for the web UI |

Every tool validates referenced keys (plant, site, location, slot) against the tenant resolved for that call. A foreign key from another tenant consistently returns `not_found` — never `permission.denied` — so no tool ever discloses the existence of another tenant's resources.

## Growth Phases and Lifecycle {#growth-phases-and-lifecycle}

The phase logic drives task scheduling, feeding windows, harvest readiness and overwintering (internal reference: REQ-003). Over MCP, only `list_phase_definitions` was visible of it for a long time — the catalogue of individual **building blocks**. Not the sequences they are assembled into, not which sequence applies to a species, and not the phase state of an actual plant. An ordinary question such as "is this plant running on the botanically correct phase sequence?" simply could not be answered through it.

Eight tools close that gap. Six read, two write — and each write tool is paired with the read tool that resolves its references **and** the one that surfaces its result:

| Write tool | Resolves its references | Surfaces its result |
|------------|-------------------------|---------------------|
| `transition_plant_phase` | `get_species_phase_sequence` (supplies the valid phase keys) | `get_plant_phase_status` |
| `assign_species_phase_sequence` | `list_phase_sequences` | `get_species_phase_sequence` |

### Why `phase_state` says more than "no phase"

For a plant without a phase, `get_plant` returns only `current_phase_key: null`. That conflates three different situations, each of which calls for something different:

| `phase_state` | Meaning | What to do |
|---------------|---------|------------|
| `never_initialised` | There is no phase history at all — the lifecycle was never started | Set a starting phase |
| `unresolved` | There is an open history record, but it points at no resolvable phase. The plant is standing still without it being noticeable | Correct it to a valid phase of its own sequence |
| `between_cycles` | Every phase is closed, none is open — a normal state for a perennial | Nothing; the next cycle starts on its own |
| `in_phase` | The plant is running | Nothing |

### How a species gets its sequence

If a species is not explicitly bound, Kamerplanter derives the sequence from its botanical attributes. The rules apply in this order; the first one that matches wins:

1. **Short-day ornamentals** that are perennial → photoperiodic ornamental cycle (poinsettia, Kalanchoe). Restricting this to perennials is deliberate: annual short-day *crops* must keep their harvest cycle.
2. **Monocarpic perennial epiphytes** (bromeliads) → offset cycle: the mother plant dies after flowering and its pups continue.
3. **CAM succulents** → cycle with a cool, dry winter rest.
4. **Growth habit**: ferns, bulb geophytes and palms each get their own cycle.
5. **Any other perennial** → evergreen foliage cycle (the largest indoor group).
6. **Known annual or biennial** → the annual default cycle, ending in a harvest.
7. **Anything else** → the evergreen, repeating cycle as well.

!!! warning "Missing data no longer leads to a harvest"
    Point 7 is a safety rule, not a botanical claim. If a species has no lifecycle record at all, that is **not an answer** and must not be read as "annual". Such a species used to land on the annual default cycle — 126 days, with a harvest and an end of life at the end. An evergreen, perennial Yucca tree was consequently scheduled to be harvest-ready and complete 126 days after planting.

    The two mistakes do not cost the same: an annual on a perennial cycle merely misses a harvest prompt you can still trigger yourself. A perennial on an annual cycle gets a harvest and an end of life invented for it that nobody asked for. The doubtful case therefore falls to the repeating cycle.

Which data feeds that decision — and what happens when a field is missing — is what `get_species_info` shows: it returns `plant_category`, `photosynthesis_type`, `growth_habit`, `indoor_suitable`, `mature_height_cm` and `frost_sensitivity`. Empty fields are omitted, so a sparse record also reads as sparse — which is itself the answer to "is this record complete enough for a reliable assignment?".

!!! warning "Exception: safety fields are never omitted"
    `toxicity`, `toxicity_severity`, `allergen_info` and `allows_harvest` are always part of the response — as `null` when nothing has been recorded. Otherwise "we hold no toxicity data on this species" would be indistinguishable from "this species is not toxic", and an agent would read the gap as an all-clear nobody gave. Only these four fields are exempt; everything else is still omitted when empty.

You correct a wrong assignment with `assign_species_phase_sequence`; `list_species_by_phase_sequence` tells you which other species sit on the same sequence.

## Diary Analysis: External Agents {#diary-analysis-external-agents}

The five `*_diary_*` tools are the complete technical contract for an externally operated AI agent that analyses diary entries a user has marked (internal reference: REQ-050). The end-user view — how you mark an entry and where you read a result — is documented under [Diary](../user-guide/plant-diary.md). This section covers the other side: the recipe of an agent that fetches, works on, and writes back results for these entries.

!!! info "Kamerplanter itself never calls a language model"
    These five tools are the only path through which a language model ever gets to see diary content at all — and even then the instance stays a pure data source and sink. There is neither a built-in model call nor a model key for this path. An agent recipe for this tool set lives in a separate repository apart from Kamerplanter (`kamerplanter-goose`) and is not part of this product.

### The flow

1. A user marks a diary entry in the web UI — the entry switches to the `requested` state.
2. `list_pending_diary_analyses` (`mcp.read`) returns the work queue — no free text, no images, so the response stays small.
3. `claim_diary_analysis` (`mcp.write`) exclusively claims an entry via a lease (default 15 minutes, ceiling 60 minutes) and returns a `lease_token`. A second claim attempt on the same entry fails with `conflict.already_claimed`. If the lease expires without a submitted result, the entry reappears in the work queue.
4. `get_diary_entry` (`mcp.read`) returns text, tags, measurements, the **environment snapshot** (`environment`) and the plant context — without image data. The snapshot lives in its **own** field next to `measurements`, never inside it: `measurements` is what a human typed, `environment` is what a device reported, and every reading carries `source`, `measured_at` and `origin` (`location` | `site` | `weather`). `environment_status` says what an empty list means — `no_source` ("nothing measures this plant") is a different statement from `unavailable` ("the reading did not get through").
5. `get_diary_entry_photos` (`mcp.read`) returns the photos as image content blocks, so an image-capable model sees them directly (see [Image delivery](#image-delivery) below).
6. The agent calls the language model that the user operates and pays for themselves.
7. `submit_diary_analysis` (`mcp.write`) writes back the result with a valid `lease_token` and sets the state to `completed` or `failed`.

### Image delivery {#image-delivery}

`get_diary_entry_photos` is the only tool in the palette whose payload is not entirely contained in `structuredContent`: the response additionally carries `image` content blocks (Base64, `mimeType: image/webp`), one per delivered photo, in the same order as the structured `photos` field.

Only the existing **512 px or 1280 px WebP renditions** are ever delivered — never the original photo. Renditions carry no EXIF data, even when the instance has set `STORAGE_STRIP_EXIF=false`; that setting only affects the original file (see [Environment Variables — Object Storage](../reference/environment-variables.md#object-storage-nfr-013)).

The total payload of one call is capped by `MCP_MAX_IMAGE_PAYLOAD_MB` (default 4 MB, Base64-encoded; see [Environment Variables — MCP Server](../reference/environment-variables.md#mcp-server)). Exceeding it returns `payload.too_large`, naming the affected photos and a smaller rendition that would fit — photos are **never** silently dropped. If a rendition does not exist yet, the affected photo appears in `pending` with `status: "thumbnail_pending"` (generation triggered, retry later) or `status: "unavailable"` (will never exist, e.g. because the attachment record is missing) — the call itself stays successful in both cases.

### Error codes

Every error from one of the five tools arrives as a tool result with `isError: true`, never as a JSON-RPC `error` — the same contract as the rest of the palette (see [Error Handling](error-handling.md)). `error_code` is machine-readable and stable, `message` is for humans and may change.

| `error_code` | Meaning |
|---------------|---------|
| `not_found` | The tenant or entry does not exist, or lies outside the resolved tenant — including for a foreign entry, never `permission.denied` |
| `permission.denied` | The role in the resolved tenant is not sufficient for this tool |
| `validation.error` | An input violates a field rule (e.g. `confidence` outside 0.0–1.0, missing `summary` for `status: completed`) |
| `validation.tenant_required` | `tenant` is missing although the key has more than one membership |
| `conflict.already_claimed` | The entry is already claimed and the lease is still valid |
| `conflict.concurrent_update` | The document revision changed between reading and writing — an immediate retry is correct here |
| `conflict.not_claimed` | `submit_diary_analysis` on an entry that is not `in_progress` |
| `conflict.lease_expired` | The `lease_token` no longer matches the current lease |
| `payload.too_large` | The call's image payload exceeds `MCP_MAX_IMAGE_PAYLOAD_MB` |

### What a recipe does not have to decide itself

- The **disclaimer** in the result is set server-side — an agent can neither omit nor soften it.
- Whether a user may mark an entry at all is checked server-side on every `mcp.write` call (role, authorship, `diary_ai_analysis` consent, operating mode) — a recipe does not need to rebuild that rule.
- An entry without photos is not an error case; `get_diary_entry_photos` then returns `photos: []` with only the text block.

### Writing an entry is a different job

`add_plant_diary_entry` (`mcp.write`) belongs to the general tool palette, not to the five above: it lets an agent **document** an observation — text, tags, measurements — instead of analysing one. Two boundaries follow from that:

- A newly written entry is **not** queued for analysis. Marking stays a user action, so an agent cannot create work for itself, and the consent gate on the marking path is never bypassed.
- The tool takes **no** photo references. Attaching a photo requires having uploaded it yourself (or being a garden lead), and MCP has no upload path — photos reach an entry through the web UI.

What was written is found again with `list_diary_entries` (`mcp.read`). It browses the garden's entries by plant, entry type, tag, analysis state and date range, and returns title, tags and measurements per row — but **not** the free text. That comes from `get_diary_entry`, a deliberate single read: a browsable list of every observation's prose is a different thing from reading one entry on purpose.

## Response Format

Every tool returns a compact, LLM-friendly JSON payload with three mandatory fields:

```json
{
  "summary": "3 plants need watering today.",
  "data": { "count": 3, "items": [ /* ... */ ] },
  "links": [
    { "type": "ui", "url": "/t/home/care" },
    { "type": "api", "url": "/api/v1/t/home/care/dashboard" }
  ]
}
```

`summary` is a one-sentence recap for the LLM, `data` is the structured result, `links` point the end user at the relevant place in the UI or the REST API.

## Dry Run and Idempotency

Every write tool accepts two additional, optional arguments:

- **`dry_run: bool`** (default `false`) — when `true`, only the planned effect is returned, without persisting anything. This lets an LLM client show a planned action to the human for confirmation before actually executing it.
- **`idempotency_key: str`** (optional) — identical keys from the same service account, tenant and tool return the original result again within 24 hours, instead of creating a second resource. This protects against duplicate actions on LLM retries (e.g. when a network response is lost).

A replayed response is recognizable by `"idempotent_replay": true`:

```json
{
  "summary": "Confirmed 'watering' for plant 'p-42'.",
  "data": { "plant_key": "p-42", "reminder_type": "watering" },
  "dry_run": false,
  "idempotency_key": "confirm-2026-07-12-001",
  "idempotent_replay": true,
  "links": [{ "type": "ui", "url": "/t/home/care" }]
}
```

Idempotency records are automatically deleted after 24 hours.

## Audit Trail and Privacy

Every tool call is logged — whether it succeeded, was denied for lacking permission, or was a `dry_run`. The entry records the service account, tenant, tool name, a **SHA-256 hash of the arguments** (never plaintext), response size, duration and status — never the API key itself, and no personal free-text content such as diary entries.

A service account can inspect its own call history via the `get_mcp_activity` tool or directly over REST:

```http
GET /api/v1/privacy/mcp-activity
Authorization: Bearer <access_token>
```

The response contains the most recent entries (tool name, status, response size, duration, error class, timestamp) — no plaintext arguments. Audit entries are automatically removed after 90 days (see [Privacy & GDPR](../user-guide/privacy.md)).

## Frequently Asked Questions

??? question "Can I use my personal account with the MCP server?"
    Yes — create an API key via `POST /api/v1/auth/api-keys` and send it as `X-API-Key`. What you cannot use is a JWT access token or an interactive session; MCP authenticates API keys only.

??? question "Can an MCP client access several tenants at once?"
    Yes, if the key's account is a member of several. The key then covers all of them, and each call names the acting garden via the `tenant` argument. To restrict a key to a single garden, set `tenant_scope` when creating it.

??? question "Can an MCP client see other people's gardens?"
    No. A key reaches exactly the gardens its account is an active member of. Naming any other garden returns `not_found` — the same answer as for a garden that does not exist, so the interface cannot be used to discover other users' gardens.

??? question "What happens if I accidentally reuse an `idempotency_key` I already used for a different tool?"
    Nothing incorrect — replay detection is additionally scoped by tool name and tenant. The same key used with a different tool or in a different tenant therefore never triggers a replay.

??? question "Does the MCP server run as its own process I can scale separately?"
    Not currently — the MCP server runs in the same backend process and shares its resources. A standalone process with its own Helm chart is planned as a follow-up (see the status note above).

## See Also

- [Service Accounts & API Keys](service-accounts.md)
- [Authentication](authentication.md)
- [Diary — User Guide](../user-guide/plant-diary.md)
- [AI Assistant — User Guide](../user-guide/ai-assistant.md)
- [Environment Variables — MCP Server](../reference/environment-variables.md#mcp-server)
- [Privacy & GDPR](../user-guide/privacy.md)
- [Error Handling](error-handling.md)
- [MCP Tools for Development (not to be confused)](../development/mcp-tools.md)
