---
review-type: agent-review
target: ".claude/agents/fullstack-developer.md"
target-kind: agent
specs-applied:
  - slug: agent-management
    revision: "0e3b6f9"
  - slug: skill-vs-agent
    revision: "0e3b6f9"
  - slug: review-plan
    revision: "0e3b6f9"
  - slug: agent-review
    revision: "0e3b6f9"
repo-revision: "c558f311"
created: "2026-04-27"
status: open
---

# Agent Review: fullstack-developer

## Scope

Target: `.claude/agents/fullstack-developer.md` (frontmatter + body; no sibling assets exist under `.claude/agents/fullstack-developer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review per `agent-review` Phase 1–4.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style (handled by linting), the orchestrator that dispatches this agent (no skill currently dispatches it by name).

## Summary

- BLOCKER: 2
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — language and missing skill-vs-agent rationale block acceptance.
Next concrete action: rewrite frontmatter `description` and the system-prompt body in English, then add a skill-vs-agent rationale section.

## Findings

### BLOCKER

- [ ] [agent-management.structure-language] Frontmatter `description` and the entire system-prompt body are written in German, contradicting the MUST that frontmatter and system-prompt content stay in English for token efficiency.
      Where: `.claude/agents/fullstack-developer.md:4` (description) and lines 10–246 (body).
      Fix: translate the `description` and the body to English; preserve the project-side instruction to respond to the user in German as a single explicit sentence ("respond to the user in German").
      Verify: `rg -P '[äöüÄÖÜß]' .claude/agents/fullstack-developer.md` returns no matches inside frontmatter or body sections.

- [ ] [skill-vs-agent.rationale] The body contains no rationale section that names a decisive dimension for the agent-over-skill choice; only a model-choice comment is present in the frontmatter.
      Where: `.claude/agents/fullstack-developer.md` (no rationale section anywhere in the body).
      Fix: add a short rationale section (paragraph or 2–4 bullets) naming at least one decisive dimension from the skill-vs-agent table (for example: context-window protection during multi-file edits, specialization via narrow stack focus); name at least one counter-dimension when the call was close.
      Verify: a section header or bullet list explicitly references one of the seven decision dimensions from `skill-vs-agent`.

### WARNING

- [ ] [agent-management.tools-bash-vs-dedicated] `Bash` is declared without the body documenting which operations require it beyond what `Read`/`Grep`/`Glob`/`Edit` already cover; running ruff/eslint/tsc is the only stated bash use.
      Where: `.claude/agents/fullstack-developer.md:5` (tools list) and lines 364–369 (only Bash use shown).
      Fix: add one sentence in the body justifying Bash (running lint/typecheck/test commands) so the SHOULD on preferring dedicated tools is met.
      Verify: the body contains a sentence naming the specific Bash operations the agent needs and confirming dedicated tools are used everywhere else.

- [ ] [agent-management.structure-prompt-order] System prompt does not open with role and boundaries followed by expected output format and only then the working method; the long "Pflichtlektuere" section (style guides, NFRs, UI-NFRs, project structure) precedes the output-shape statement at lines 137–141.
      Where: `.claude/agents/fullstack-developer.md:14–141` (procedure precedes output format).
      Fix: reorder so role/boundaries come first, then "Output (files + tests + ruff/eslint clean + tsc clean)", then the working method (style-guide reading, project structure, etc.).
      Verify: the first three top-level sections follow the role → output → procedure order.

- [ ] [agent-management.body-length-200] Body length is approximately 246 lines, exceeding the soft 200-line target without factoring long-form material (style-guide pointers, project tree, post-implementation handoff blocks) into `agents/fullstack-developer/` sibling files.
      Where: `.claude/agents/fullstack-developer.md` (file ends at line 246).
      Fix: move the project-tree diagram, the UI-NFR cheat-sheet, and the three downstream-handoff blocks (UI-Review, Security-Review, Documentation) into sibling files under `agents/fullstack-developer/` and reference them by relative path.
      Verify: `wc -l .claude/agents/fullstack-developer.md` reports ≤ 200 lines.

- [ ] [skill-vs-agent.duplicate-prevention] Capability statement overlaps with the `implement` skill ("Feature aus REQ implementieren") — both cover full-stack feature implementation from REQ documents, raising a duplicate-capability concern within the same plugin/project surface.
      Where: `.claude/agents/fullstack-developer.md:4` (description) vs. the `implement` skill listed in the available-skills set.
      Fix: either narrow the agent's `description` so its trigger surface no longer overlaps with `implement` (e.g., "execution layer dispatched by the `implement` skill, not invoked directly by the user"), or document the orchestration relationship explicitly in the rationale section.
      Verify: a side-by-side comparison of the two `description` lines shows no equivalent trigger phrasing.

### SUGGESTION

- [ ] [agent-management.tags-vocabulary] No `tags` field is declared, so the catalog and peer-cluster lookups (`skill-vs-agent` Portfolio-wide consistency) cannot place this agent in a functional cluster.
      Where: `.claude/agents/fullstack-developer.md:1–8` (frontmatter).
      Fix: add a `tags` list with at most five lowercase kebab-case entries (e.g., `[implementation, backend, frontend, fullstack]`); reuse starter-vocabulary terms where they fit.
      Verify: frontmatter contains a `tags` field whose entries each match `^[a-z][a-z0-9-]{0,29}$` and the list has ≤5 items.

### INFO

- [ ] [agent-management.distribution] `distribution: project` is declared and matches the file's residence under `.claude/agents/`; no plugin-bundle path is referenced from the body.
      Where: `.claude/agents/fullstack-developer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.model-rationale] `model: opus` is pinned with an inline rationale comment (line 6: complex multi-file changes, large context window); the rationale is plausible for an implementation agent.
      Where: `.claude/agents/fullstack-developer.md:6–7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
