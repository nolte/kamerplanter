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
    The specification envisions roughly 30 tools (including setup macros for apartment/growbox/outdoor garden, bulk plant creation, IPM inspections, harvest recording, feeding events and a bridge to the RAG knowledge base). The following core tool set is implemented so far — expansion is a documented follow-up.

### Read tools (`mcp.read`)

| Tool | Purpose |
|------|---------|
| `list_tenants` | List your gardens with the role you hold in each — supplies the slugs for the `tenant` parameter |
| `list_plants` | List plants, optionally filtered by name — this is how "my tomato" becomes the `plant_key` the write tools need |
| `get_plant` | One plant in detail: species (with resolved name), phase, location, planting and removal dates |
| `get_plant_care_log` | A plant's care history — with `reminder_type: "watering"` this is the watering log |
| `list_plants_at_location` | All plants at a given site, bed or slot |
| `list_nutrient_plans` | Available nutrient plans — your own plus global templates |
| `get_nutrient_plan` | One plan with every phase: NPK ratio, target EC, nutrients, week window |
| `get_plant_nutrient_plan` | The plan that applies to a specific plant |
| `get_sowing_calendar` | Sowing, planting-out and harvest windows per species, shifted against your site's frost dates |
| `list_species` | List the plant species catalog (paginated) |
| `get_species_info` | Return master data for a species incl. companion-planting hints |
| `list_planting_runs` | List the tenant's planting runs, optionally filtered by status |
| `list_tasks` | List the tenant's tasks, optionally filtered by status |
| `get_due_care_tasks` | Today's / overdue care reminders, grouped by urgency |
| `get_harvest_readiness` | Harvest-readiness overview across all active plants |
| `get_mcp_activity` | This account's own MCP call history (self-service view, see below) |

### Write tools (`mcp.write`)

| Tool | Purpose |
|------|---------|
| `confirm_care_task` | Confirm a care reminder for a plant ("I have watered it") |
| `archive_plant` | Mark a plant as disposed / given away / died — **never** a hard delete, history is retained |
| `set_plant_location` | Move a plant to another site / location / slot |

### Setup tool (`mcp.setup`)

| Tool | Purpose |
|------|---------|
| `create_site` | Create a site root (apartment, garden, balcony, greenhouse, windowsill, grow tent) |

Every tool validates referenced keys (plant, site, location, slot) against the tenant resolved for that call. A foreign key from another tenant consistently returns `not_found` — never `permission.denied` — so no tool ever discloses the existence of another tenant's resources.

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
- [AI Assistant — User Guide](../user-guide/ai-assistant.md)
- [Environment Variables — MCP Server](../reference/environment-variables.md#mcp-server)
- [Privacy & GDPR](../user-guide/privacy.md)
- [Error Handling](error-handling.md)
- [MCP Tools for Development (not to be confused)](../development/mcp-tools.md)
