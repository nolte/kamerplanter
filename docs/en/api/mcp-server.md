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

The MCP server runs in-process with the backend and exposes its tools through three endpoints under `/api/v1/mcp/`:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/mcp/tools` | REST-friendly tool listing — shows only the tools the calling service account's role unlocks |
| `POST` | `/mcp/tools/{tool_name}` | REST-friendly tool call with a JSON body as arguments |
| `POST` | `/mcp/rpc` | MCP JSON-RPC 2.0 — `initialize`, `tools/list`, `tools/call`, `ping` — for protocol-native MCP clients |
| `GET` | `/mcp/sse` | SSE handshake for the HTTP+SSE transport: emits an `endpoint` event pointing at `/mcp/rpc` |

!!! info "API only / operator configuration: transport"
    A standalone `stdio` transport (the server started locally by the client, typical for Claude Desktop configurations) is specified but not yet implemented — currently only HTTP(+SSE) is available. An MCP client connects to the full backend URL, e.g. `https://api.kamerplanter.example.com/api/v1/mcp/rpc`.

## Authentication: service accounts only

The MCP server accepts **only** API keys from service accounts (`account_type: "service"`) — never a personal user account and never a JWT access token. The key is sent as an `X-API-Key` header or as `Authorization: Bearer kp_...` and always carries the `kp_` prefix (see also [Authentication — API Keys (M2M Integration)](authentication.md#api-keys-m2m-integration)).

```http
POST /api/v1/mcp/tools/get_due_care_tasks
X-API-Key: kp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{"urgency": "actionable"}
```

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
  "tenant_key": "t-home",
  "tenant_slug": "home",
  "role": "viewer",
  "mcp_permissions": ["mcp.read"]
}
```

An invalid, revoked or non-service key returns the same generic `401 Unauthorized` in both cases — the API never reveals whether a valid key with different properties exists.

### Obtaining a service-account key (current state)

!!! warning "Not yet implemented"
    Full, self-service service-account management (create, rotate, deactivate via the API — see [Service Accounts & API Keys](service-accounts.md)) is specified but not yet implemented. Today, creating a user account with `account_type: "service"` is an **operator step** outside the public API, not a self-service flow (internal reference: REQ-023). The points below describe the current state, not the future self-service experience.

For an MCP client to obtain a working key today, the following pieces are needed:

1. A user account with `account_type: "service"` (no password, no interactive login) — created by the instance operator.
2. A tenant membership for that account with exactly the role (`viewer`/`grower`/`admin`) matching the desired [permission level](#permission-model-mcpread-mcpwrite-mcpsetup) — a service account is always bound to **exactly one** tenant.
3. An API key for that account, technically the same mechanism described under [Service Accounts & API Keys — Using the API Key](service-accounts.md#using-the-api-key) — but since a service account is never logged in interactively, it cannot request the key itself via the `/auth/api-keys` endpoint; this step, too, currently runs through the operator.

## Permission model: `mcp.read` / `mcp.write` / `mcp.setup`

Every tool requires exactly one of three MCP permissions. These are not granted separately — they are bound directly to the service account's tenant role, the same role used for human members ([Tenants & Gardens](../user-guide/tenants.md)):

| Tenant role | `mcp.read` | `mcp.write` | `mcp.setup` | Typical use |
|-------------|:----------:|:-----------:|:-----------:|-------------|
| **viewer** | ✓ | ✗ | ✗ | Read-only diagnose bot |
| **grower** | ✓ | ✓ | ✗ | Day-to-day operation (confirm care, move/archive plants) |
| **admin** | ✓ | ✓ | ✓ | One-off onboarding, site creation |

A call without the required permission is rejected with the error code `permission.denied` and recorded in the audit log as `status: "denied"` (see [Audit Trail & Privacy](#audit-trail-and-privacy)). `mcp.setup` is deliberately the most restrictive class: it governs site creation — an action that can affect an entire plant-data hierarchy — and is therefore reserved for the `admin` role only.

## Tool Catalog (current state)

!!! note "Partially available: tool scope"
    The specification envisions roughly 30 tools (including setup macros for apartment/growbox/outdoor garden, bulk plant creation, IPM inspections, harvest recording, feeding events and a bridge to the RAG knowledge base). The following core tool set is implemented so far — expansion is a documented follow-up.

### Read tools (`mcp.read`)

| Tool | Purpose |
|------|---------|
| `list_species` | List the plant species catalog (paginated) |
| `get_species_info` | Return master data for a species incl. companion-planting hints |
| `list_planting_runs` | List the tenant's planting runs, optionally filtered by status |
| `list_tasks` | List the tenant's tasks, optionally filtered by status |
| `get_due_care_tasks` | Today's / overdue care reminders, grouped by urgency |
| `get_harvest_readiness` | Harvest-readiness overview across all active plants |
| `get_mcp_activity` | This service account's own MCP call history (self-service view, see below) |

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

Every tool validates referenced keys (plant, site, location, slot) against the calling service account's tenant. A foreign key from another tenant consistently returns `not_found` — never `permission.denied` — so no tool ever discloses the existence of another tenant's resources.

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

??? question "Can I sign in to the MCP server with my personal account?"
    No. The MCP server accepts only service-account API keys. An attempt with a personal account (`account_type: "user"`) is rejected.

??? question "Can an MCP client access several tenants at once?"
    No. A service account is always bound to exactly one tenant. Accessing several gardens requires several service accounts, each with its own key.

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
