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
    | Test locally | `unit-test-runner`, `/nolte-shared:quality-gate` |
    | Review code | `nolte-shared:code-security-reviewer`, `frontend-usability-optimizer` |
    | Write docs | `mkdocs-documentation` |
    | Check docs | `/nolte-shared:docs-freshness-checker` |
    | Prepare PR | `/pre-pr`, `pr-to-develop`, `/nolte-shared:pull-request-create` |
    | E2E tests | `e2e-testcase-extractor` → `selenium-test-generator` |
    | E2E results | `nolte-shared:e2e-result-reviewer` |
    | HA integration | `ha-integration-requirements-engineer` → `ha-integration-developer` |
    | Deploy HA | `/deploy-ha` |
    | Knowledge base | `/gen-knowledge`, `knowledge-chunk-author` |
    | RAG quality | `rag-eval-runner` |
    | CVE scan | `/nolte-shared:dependency-audit` |

---

## Typical Scenarios

### Scenario 1: Implement a feature (spec → code → PR)

1. Check the specification: `tech-stack-architect`
2. Review requirements: `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`
3. Implement: `fullstack-developer`
4. Test locally: `/nolte-shared:quality-gate`
5. Review security: `nolte-shared:code-security-reviewer`
6. Optimize the UI: `frontend-usability-optimizer`
7. Documentation: `mkdocs-documentation`
8. Prepare the PR: `/pre-pr`, `/nolte-shared:pull-request-create`

### Scenario 2: E2E tests for a feature

1. Derive test cases: `e2e-testcase-extractor`
2. Generate tests: `selenium-test-generator` (NFR-008 compliant)
3. Review tests: `selenium-test-reviewer`
4. Analyze results: `nolte-shared:e2e-result-reviewer`

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

## Model Selection

| Model | Use | Example |
|--------|---------|----------|
| **opus** | Complex generation, architecture decisions, extensive analyses | `fullstack-developer`, `ha-integration-developer`, `casual-houseplant-user-reviewer`, `tech-stack-architect`, `selenium-test-generator` |
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
