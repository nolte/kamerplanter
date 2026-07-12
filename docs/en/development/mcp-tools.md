---
tags:
  - claude-code
  - mcp
  - debugging
  - tooling
---

# MCP Tools

This page describes the **MCP servers (Model Context Protocol)** configured for the project that Claude Code can use in addition to the codebase. It shows **how to use them, what concrete value they provide, how the workflow looks without them**, and **what limitations the manual variant has**.

Authoritative specification: [`spec/dev-tooling/MCP-SERVERS.md`](https://github.com/nolte/kamerplanter/blob/main/spec/dev-tooling/MCP-SERVERS.md) (DEVTOOL-001).

!!! info "Selenium remains unchanged"
    MCP tools **do not replace E2E tests**. The `tests/e2e/` suite and `docker-compose.e2e.yml` remain — per [NFR-008a](https://github.com/nolte/kamerplanter/blob/main/spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md) — the sole source of truth for E2E. MCP servers are **debug and research aids** for development.

!!! note "Not to be confused with the Kamerplanter MCP server for end users"
    This page describes MCP servers that **Claude Code** uses during development. Kamerplanter itself also ships its own **[MCP server](../api/mcp-server.md)**, through which external LLM clients (Claude Desktop, Claude Code, custom agents) can act as users against your garden — two independent, identically-named concepts.

---

## Quick start

```bash
# 1. One-off: download Playwright Chromium + warm npx caches
task mcp:setup

# 2. Start Chrome with the debug port (for chrome-devtools-mcp)
task mcp:chrome

# 3. Check status of all MCP prerequisites
task mcp:status

# 4. Start Claude Code — on the first invocation of an MCP tool
#    Claude asks once for permission
claude

# 5. Check available servers
/mcp
```

The `.mcp.json` is committed in the repo — Claude Code loads it automatically.

### Available tasks

| Task | Purpose |
|------|---------|
| `task mcp:setup` | One-off: download Playwright browser, warm npx cache for all MCP packages |
| `task mcp:chrome` | Start Chrome with `--remote-debugging-port=9222` and isolated profile |
| `task mcp:chrome:stop` | Stop the debug Chrome |
| `task mcp:status` | Overview: Chrome port, kubectl context, Playwright cache, context7 reachability |
| `task mcp:e2e:debug` | Start E2E-stack frontend with published port `:8080` for live debugging |

`task mcp:chrome` accepts variables:

```bash
# Use a different start URL
MCP_CHROME_URL=http://localhost:8080 task mcp:chrome

# Use a different profile directory
MCP_CHROME_PROFILE=/tmp/my-debug task mcp:chrome
```

Configured servers:

| Server | Purpose | Prerequisite |
|--------|---------|---------------|
| `chrome-devtools` | Read browser console / network / stack traces | Chrome with `--remote-debugging-port=9222` |
| `playwright` | Click through the UI remotely, screenshots, locate selectors | Chromium binary (downloaded automatically on first run) |
| `context7` | Up-to-date, version-specific library docs | Internet connection |
| `kubernetes` | Pod logs, status, describe (read-only) on the Skaffold/Kind cluster | Working `kubectl` context |

---

## chrome-devtools-mcp

### Value

Claude can **look directly into your running browser** — console errors, network requests, stack traces, DOM state. A typical "the phase detail page crashes for me" turns into a concrete diagnosis instead of guesswork.

| Task | With `chrome-devtools` | Without |
|------|--------------------------|----------|
| Diagnose a frontend crash | Stack trace + console error read automatically | You must transcribe the trace or share a screenshot |
| Analyse a failed API call | Status, headers, request and response body are read | You manually open the network tab and copy |
| State verification after action | DOM, localStorage, cookies inspected directly | You describe what you see |

### Usage

```bash
# Start Chrome with the debug port (once per session)
task mcp:chrome
```

The task starts Chrome in the background with `--remote-debugging-port=9222` and an isolated profile under `/tmp/chrome-debug`. If the Vite dev server (port 5173) is running, the app opens directly.

In Claude Code: just say "look in the browser, there's an error". Claude connects to `localhost:9222`, lists open tabs, reads console + network.

```bash
# Check status
task mcp:status

# Stop Chrome again
task mcp:chrome:stop
```

!!! warning "Isolated browser profile"
    `task mcp:chrome` automatically uses `--user-data-dir=/tmp/chrome-debug`. **Never** use your personal Chrome profile — otherwise Claude potentially gains access to your full browser history, cookies, and password material.

### Without chrome-devtools-mcp

1. Open DevTools manually (`F12`).
2. Photograph or copy the console / network tab.
3. Paste into Claude.

**Limitations:**

- **Time loss** — manual copy-paste loop on every iteration step.
- **Incomplete** — stack trace is often collapsed, source maps are forgotten, network body is not copied.
- **No live state** — Claude only sees the browser state at the moment of your screenshot, cannot "look again".

---

## @playwright/mcp

### Value

Claude can **click through the UI on its own**, fill out forms, take screenshots, and locate selectors for tests. Instead of describing "click the button, then the dropdown" Claude can play the workflow directly and reports what happened.

| Task | With `playwright` | Without |
|------|---------------------|----------|
| Quick visual check of new UI | Claude opens the page, takes a screenshot, describes | You start the browser, click, describe |
| Locate selectors for a new Selenium test | Claude inspects the DOM, suggests stable `data-testid` selectors | You open DevTools, search manually |
| Reproduce a failed Selenium test | Claude walks the same path live, compares with test expectation | You reproduce manually, describe diff |
| Visual regression after a UI change | Before/after screenshots of the same page | Manual screenshots in multiple places |

### Usage

Connection to the application:

| Source | URL |
|--------|-----|
| Vite dev server (Skaffold/Kind) | `http://localhost:5173` |
| Vite dev server (local `npm run dev`) | `http://localhost:5173` |
| E2E Compose stack (live debug) | `http://localhost:8080` (see "Live debug against the E2E stack" below) |

In Claude Code: "Open the phase detail page and check whether the save button is hidden for system phases."

### Live debug against the E2E stack

If a Selenium test in `docker-compose.e2e.yml` fails and you want to see the exact state live:

```bash
task mcp:e2e:debug
```

The task starts the frontend from `docker-compose.e2e.yml` with published port `8080` — **without** modifying the Compose file. Stop with `Ctrl+C`. Playwright-MCP then points to `http://localhost:8080`.

### Without @playwright/mcp

1. Start a browser, open the application manually.
2. Click through the workflow by hand.
3. Hand the description of the observation back to Claude.

**Limitations:**

- **Selector guesswork** — when writing new Selenium tests Claude often has to guess selectors, or you need to look them up manually in the DevTools inspector.
- **No roundtrip** — Claude can suggest a fix but cannot itself verify whether the fix actually repairs the UI — you must manually verify after every patch.
- **Fragmented screenshots** — no consistent before/after documentation.

!!! note "Relationship to Selenium"
    Playwright-MCP is **not a test framework swap**. NFR-008a still requires pytest + Selenium for every E2E requirement. Playwright-MCP only helps Claude **diagnose** and **prepare** these tests.

---

## context7

### Value

Provides **up-to-date, version-specific doc snippets** for libraries in the stack — prevents code that writes against outdated or hallucinated APIs.

Concrete examples from the Kamerplanter stack where this makes the difference:

| Problem without context7 | Solution with context7 |
|---------------------------|------------------------|
| MUI 7: `<Grid item xs={12}>` instead of `<Grid size={{ xs: 12 }}>` (breaking change in v7) | Current example pulled from MUI 7 docs |
| React 19: wrong `use()` hook signature | Live example from React 19 docs |
| Pydantic v2: `@validator` instead of `@field_validator` | Correct Pydantic 2 annotation |
| FastAPI ≥ 0.115: deprecated lifespan pattern | Current `lifespan` context manager form |
| Authlib instead of python-jose (per stack decision) | Authlib-specific JWT code samples |

### Usage

Implicit — Claude reaches for it on its own when using a library API. You can request explicitly: "Use context7 for the correct MUI 7 Grid syntax."

### Without context7

1. Manual research in the official docs.
2. Trial and error with linter/compiler feedback.
3. Search Stack Overflow or GitHub issues.

**Limitations:**

- **Hallucination risk** — LLMs produce plausible-looking but factually wrong API calls, especially for recently released versions or migrations (MUI 5 → 7, React 18 → 19).
- **Outdated training cut-off** — the LLM training cut-off is static; context7 hangs on the live docs state.
- **Iteration cost** — every "doesn't work, try again" roundtrip costs time and tokens.

---

## kubernetes-mcp-server

### Value

Claude gains **read-only access to the local Kind cluster** — pod status, logs, describe, events. Kamerplanter's Skaffold workflow (see [Local setup](local-setup.md)) deploys backend, frontend, ArangoDB, Valkey and HA integration into `default` — when debugging the cluster state becomes Claude's live data source.

| Task | With `kubernetes` | Without |
|------|---------------------|----------|
| Diagnose backend crash loop | Pod status + last 100 log lines fetched directly | `kubectl logs ...` via Bash, manual scrolling |
| InitContainer issues with HA integration | Pod describe shows InitContainer status immediately | Manual `kubectl describe pod ...` |
| Service unreachable | Endpoint list + service status at a glance | Several `kubectl get` calls |
| Check ArangoDB PVC status | PVC + pod mount state in one step | Combine multiple kubectl commands |

### Usage

In Claude Code: "Look in the cluster, why isn't the backend pod coming up" or "Show me the last 50 log lines from the Celery worker".

Prerequisite — working `kubectl` context:

```bash
kubectl config current-context     # expected: kind-kamerplanter or similar
kubectl get pods -n default        # must show backend/frontend/ArangoDB
```

!!! danger "Read-only is mandatory"
    The server runs intentionally with `--read-only`. The rule documented in [`CLAUDE.md`](https://github.com/nolte/kamerplanter/blob/main/CLAUDE.md) — **"`kubectl delete pod` forbidden for Home Assistant — use `kill 1`"** — is structurally enforced this way. Write operations (`apply`, `delete`, `exec`) remain visible in `Bash` calls with explicit permission prompt.

!!! warning "Skaffold remains the only deploy tool"
    `kubernetes-mcp-server` is **not** a deploy tool. Image builds and rollouts continue exclusively via Skaffold (see [Local setup](local-setup.md)). The MCP server only reads — it does not change anything in the cluster.

### Without kubernetes-mcp-server

1. Invoke Bash commands `kubectl get pods`, `kubectl logs`, `kubectl describe` manually.
2. Hand the output back to Claude (copy-paste or repeated Bash execution).

**Limitations:**

- **Multiple roundtrips** — find the pod name, then fetch logs, then describe — three separate Bash calls instead of one MCP call.
- **No state snapshot** — for intermittent issues (crash loop) you must poll manually multiple times.
- **No automatic cross-reference** — Claude has to ask explicitly for each piece of information instead of correlating multiple resources in parallel.

---

## Typical workflows

### Workflow 1: diagnose a frontend crash

```
1. You:    "Look in the browser, there was a crash"
2. Claude → chrome-devtools: reads console, fetches stack trace
3. Claude → Read: reads the file + line named in the trace
4. Claude → context7: checks whether the API used is still current
5. Claude → Edit: fix
6. Claude → playwright: navigates to the page, verifies the crash is gone
7. You:    confirm and commit
```

**Without MCP:** Steps 2, 4 and 6 require manual actions from you.

### Workflow 2: write a new Selenium test

```
1. You:    "Create an E2E test for the new phase detail page"
2. Claude → playwright: opens the page, clicks through the happy path
3. Claude → playwright: identifies stable data-testid selectors
4. Claude → Read: looks at the PageObject conventions from NFR-008a
5. Claude → Write: creates PageObject + pytest file
6. You:    docker compose -f docker-compose.e2e.yml up e2e-tests
7. Selenium test runs in the Compose stack — unchanged as always
```

**Without MCP:** You must perform steps 2 and 3 manually and hand the selectors to Claude.

### Workflow 3: library migration (e.g. MUI 7)

```
1. You:    "Migrate PhaseDefinitionDetailPage to the new Grid API"
2. Claude → context7: fetches current MUI 7 Grid docs
3. Claude → Read: reads existing code
4. Claude → Edit: adjusts syntax
5. Claude → Bash: npm run typecheck && npm run lint
6. Claude → playwright: visually checks that the layout is intact
```

**Without MCP:** Step 2 falls away — Claude guesses the new API with ~50% probability of being correct; step 6 is replaced by manual clicking.

---

## Setup details

### What is already configured

`.mcp.json` (committed in the repo):

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--browser", "chromium"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubernetes-mcp-server@latest", "--read-only"]
    }
  }
}
```

### Prerequisites

| Tool | Version requirement | Note |
|------|---------------------|------|
| Node.js | ≥ 20 | Already covered by frontend toolchain |
| `npx` | ships with Node.js | — |
| Chrome / Chromium | current | For `chrome-devtools-mcp` |
| `kubectl` with valid context | — | For `kubernetes-mcp-server` |
| Internet connection | — | For `context7` and the initial `npx` download |

### First invocation

On the first start of each MCP server `npx` downloads the package (10–30 s) and Claude Code asks once for permission. Confirm with `Allow always` for regular use.

`@playwright/mcp` additionally downloads a Chromium binary (~200 MB) on first run into `~/.cache/ms-playwright/`.

### Check status

In Claude Code:

```
/mcp
```

Lists active servers and their connection status.

---

## Optional extensions

The following servers are documented in [DEVTOOL-001 §4.5–4.9](https://github.com/nolte/kamerplanter/blob/main/spec/dev-tooling/MCP-SERVERS.md) and can be added on demand to `~/.claude.json` (user scope, **do not** commit to the repo because of tokens):

| Server | When useful |
|--------|--------------|
| `github-mcp-server` | PR / issue / workflow management without `gh` CLI roundtrip |
| `postgres-mcp` | Ad-hoc queries against TimescaleDB (once REQ-005 is implemented) |
| `sentry-mcp` | Pull frontend / backend errors from Sentry directly (REQ-025 compliant) |

---

## Security and privacy notes

| Risk | Mitigation |
|------|-------------|
| Secrets in `.mcp.json` | **Forbidden** — tokens live in `~/.claude.json` |
| Personal browser profile | Always `--user-data-dir=/tmp/chrome-debug` (or similarly isolated) |
| Cluster write access | `kubernetes-mcp-server` only with `--read-only` |
| Personal production data | Never leak to external MCP servers (context7, sentry-mcp) — GDPR / REQ-025 applies |
| `npx` supply chain | `@latest` is convenient; pin to a concrete version for stable setups |

---

## When to skip MCP tools

Kamerplanter development is fully possible without MCP extensions. The manual variant is perfectly sufficient when:

- You write **only backend code** validated through `pytest` and pod logs.
- You make **short, isolated changes** whose verification fits into one iteration.
- The **task is spec-driven** (REQ/NFR implementation) and does not require live browser feedback.
- You work in a **restricted environment** (CI container, air-gapped setup).

In all other cases — especially for iterative UI work, library migrations, or hard-to-reproduce frontend bugs — the minimal stack (chrome-devtools + playwright + context7 + kubernetes) noticeably accelerates the development loop.

---

## Further references

- Specification: [`spec/dev-tooling/MCP-SERVERS.md`](https://github.com/nolte/kamerplanter/blob/main/spec/dev-tooling/MCP-SERVERS.md) (DEVTOOL-001)
- Test strategy: [`spec/nfr/NFR-008_Teststrategie-Testprotokoll.md`](https://github.com/nolte/kamerplanter/blob/main/spec/nfr/NFR-008_Teststrategie-Testprotokoll.md)
- E2E conventions: [`spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md`](https://github.com/nolte/kamerplanter/blob/main/spec/nfr/NFR-008a_E2E-Selenium-Teststandard.md)
- Local setup: [Local setup](local-setup.md)
- Debugging overview: [Debugging](debugging.md)
- MCP standard: <https://modelcontextprotocol.io/>
