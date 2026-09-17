---
title: Agent and Skill Workflows
description: Decision guide and typical scenarios for Claude Code agents and skills in the Kamerplanter project
---

# Agent and Skill Workflows

When do you use which agent or skill? This page complements the automatically generated [Skills catalog](../../skills/) and [Agents catalog](../../agents/) with project-specific usage recommendations, typical workflows, and model-selection hints.

!!! info "Catalog vs. Workflows"
    - The **[Skills catalog](../../skills/)** and **[Agents catalog](../../agents/)** are generated automatically from the source files in `.claude/skills/`, `.claude/agents/`, and the `nolte-shared` plugin.
    - **This page** is hand-maintained and describes the Kamerplanter-specific context for using them.

---

## Decision Guide

!!! tip "Which agent/skill for my task?"

    **By workflow phase:**

    | Phase | Agent/Skill |
    |-------|-------------|
    | Write requirements | `tech-stack-architect`, `/review-spec` |
    | Review requirements | `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`, `casual-houseplant-user-reviewer` |
    | Implement | `fullstack-developer`, `/implement` |
    | Test locally | `unit-test-runner`, `/nolte-engineering:quality-gate` |
    | Review code | `nolte-engineering:code-security-reviewer`, `frontend-usability-optimizer` |
    | Write docs | `mkdocs-documentation` |
    | Check docs | `/nolte-shared:docs-freshness-checker` |
    | Prepare PR | `/nolte-engineering:quality-gate` → `pr-to-develop` → `/nolte-shared:pull-request-create` (see [the pre-PR chain](#the-pre-pr-chain)) |
    | Audit test tiers | `/nolte-engineering:test-pyramid-check` |
    | E2E tests | `nolte-engineering:test-case-extractor` → `nolte-engineering:e2e-test-generator` |
    | E2E results | `nolte-engineering:e2e-result-reviewer` |
    | HA integration | `ha-integration-requirements-engineer` → `ha-integration-developer` |
    | Deploy HA | `/deploy-ha` |
    | Knowledge base | `/gen-knowledge`, `knowledge-chunk-author` |
    | RAG quality | `rag-eval-runner` |
    | CVE scan | `/nolte-engineering:dependency-audit` |

---

## Typical Scenarios

### Scenario 1: Implement a feature (spec → code → PR)

1. Check the specification: `tech-stack-architect`
2. Review requirements: `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`
3. Implement: `fullstack-developer`
4. Test locally: `/nolte-engineering:quality-gate`
5. Review security: `nolte-engineering:code-security-reviewer`
6. Optimize the UI: `frontend-usability-optimizer`
7. Documentation: `mkdocs-documentation`
8. Prepare the PR: [the pre-PR chain](#the-pre-pr-chain), then `/nolte-shared:pull-request-create`

### Scenario 2: E2E tests for a feature

1. Derive test cases: `nolte-engineering:test-case-extractor`
2. Generate tests: `nolte-engineering:e2e-test-generator` (NFR-008 compliant)
3. Review tests: `nolte-engineering:e2e-test-reviewer`
4. Analyze results: `nolte-engineering:e2e-result-reviewer`

### Scenario 3: Review a requirement

1. Technical feasibility: `tech-stack-architect`
2. Botanical correctness: `agrobiology-requirements-reviewer`
3. IT security & GDPR: `it-security-requirements-reviewer`
4. Contradictions: `requirements-contradiction-analyzer`
5. User perspectives: `casual-houseplant-user-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`

### Scenario 4: Extend the Home Assistant integration

1. Derive requirements: `ha-integration-requirements-engineer`
2. Review HA: `smart-home-ha-reviewer`
3. Implement: `ha-integration-developer`
4. Sync with the backend: `ha-integration-sync`
5. Deploy: `/deploy-ha`

### Scenario 5: Improve the RAG system

1. Benchmark quality: `rag-eval-runner`
2. Close gaps: `knowledge-chunk-author`
3. Re-test: `rag-eval-runner`

---

## The Pre-PR Chain

Until #1405 two project-local skills covered this, `check-test-pyramid` and
`pre-pr`. Both are gone: they shadowed plugin capabilities, which
CLAUDE.md §"Claude Code plugin adoption" rules out, and each plugin pendant does
more than the local original did.

!!! info "Why the two skills were retired"
    `check-test-pyramid` checked that all four test tiers were *present*.
    `/nolte-engineering:test-pyramid-check` checks the same against a five-tier
    taxonomy **and** additionally runs a falsifiability sweep per
    `spec/project/test-falsifiability/` (T-categories: assertion-free tests,
    tautological assertions, swallowed failure signals, duplicate selectors).
    Measured against three closed issues of exactly that class — #1056, #802,
    #1153 — the local skill reports **none** and the plugin pendant reports
    **#1056 and #1153**. #802 (a captured before-state never compared) is caught
    in this repository by `ruff` via `F841`, configured in `tests/e2e/ruff.toml`
    — the static-analysis tier the spec routes that detection to anyway, and it
    is untouched.

    `pre-pr` bundled five lint/test commands plus three agent dispatches.
    `/nolte-engineering:quality-gate` does the five better: it prefers this
    repository's declared Taskfile targets instead of hard-wiring `ruff`,
    `pytest` and `npm`, and it distinguishes "skipped" from "passed".

### The decision on the three extras

`pre-pr` additionally started three agents. All three are plugin agents and
directly invocable; the local skill was an ordering, not a capability. They
therefore did **not** move into a shrunken local skill but into this chain — a
local orchestration skill wrapping three foreign agents would re-create exactly
the coupling #1405 dissolves:

| Extra | Owned by | When |
|---|---|---|
| i18n completeness | `nolte-engineering:i18n-completeness-checker` | on frontend changes |
| Security review | `nolte-engineering:code-security-reviewer` | on changes under `src/backend/app/` |
| Docs freshness | `nolte-shared:docs-freshness-checker` | on changes to the API, domain models, frontend pages, `docs/` or `spec/` |

### The order

1. `/nolte-engineering:quality-gate` — lint, typecheck, tests.
2. On test changes, additionally `/nolte-engineering:test-pyramid-check <module>`.
3. The three agents above, by relevance — they are independent and run in parallel.
4. `pr-to-develop` — kamerplanter's own gates (`act`, hadolint, `docker build`,
   `helm lint`, Conventional Commits).
5. `/nolte-shared:pull-request-create`.

!!! warning "What no guard sees"
    `task check:plugin-shadowing` (#1405) goes red when a local skill or agent
    carries the same name as a plugin asset — or the same name tokens in another
    order, which is what the `check-test-pyramid` / `test-pyramid-check` pair is.
    A shadow under an *unrelated* name, which is precisely the `pre-pr` over
    `quality-gate` shape, is invisible there and still needs a reading pass.

---

## Model Selection

| Model | Use | Example |
|--------|---------|----------|
| **opus** | Complex generation, architecture decisions, extensive analyses | `fullstack-developer`, `ha-integration-developer`, `casual-houseplant-user-reviewer`, `tech-stack-architect`, `nolte-engineering:e2e-test-generator` |
| **sonnet** | Default: balance of quality and speed | Most agents (reviews, code fixes, documentation) |

---

## Output Directories

| Output type | Directory |
|------------|------------|
| Analysis reports | `spec/analysis/` |
| Test-case specifications | `spec/e2e-testcases/` |
| E2E test reports | `test-reports/` |
| Documentation | `docs/de/`, `docs/en/` |
| Design prompts | `spec/design/` |
| Seed data | `src/backend/app/migrations/seed_data/` |
| Knowledge base | `spec/knowledge/rag/` |
| Code | `src/backend/`, `src/frontend/` |
| HA integration | `custom_components/kamerplanter/` |

---

## Tips

- **Start an agent:** Call the agent's name in the Claude Code chat.
- **Run a skill:** Type `/skillname` (project-local) or `/nolte-shared:skillname` (shared) in the chat.
- **Agents in parallel:** Agents have no dependencies and can run in parallel.
- **English code, German docs:** NFR-003 — source code MUST be in English.
- **Keep the catalog current:** The skill and agent catalog is regenerated automatically from the source files on every `task docs:build`; no manual upkeep needed.
