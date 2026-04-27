---
review-type: agent-review
target: ".claude/agents/smart-home-ha-reviewer.md"
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

# Agent Review: smart-home-ha-reviewer

## Scope

Target: `.claude/agents/smart-home-ha-reviewer.md` (frontmatter + body, ~432 lines, no sibling assets under `.claude/agents/smart-home-ha-reviewer/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior of the agent, Vale/markdown style, Home-Assistant-specific factual correctness, the dispatching skill (none declared).

## Summary

- BLOCKER: 5
- WARNING: 5
- SUGGESTION: 1
- INFO: 3

Go/no-go: FAIL — multiple MUST violations: read-only-shaped persona-review agent declares `Write` (write-tool BLOCKER per `agent-review`), body is German, no rationale section, no upfront output contract, write-effect goals/preconditions for the report file are not documented. Plus a material thematic overlap with `ha-integration-requirements-engineer`.
Next concrete action: author addresses the five BLOCKERs (drop `Write` or refactor into skill-orchestrates-agent, translate body, add rationale, lift output contract, document the report-file write goals/preconditions explicitly) and clarifies the boundary against `ha-integration-requirements-engineer`.

## Findings

### BLOCKER

- [ ] [agent-review.read-only-no-write-tools] Description verbs ("Prüft Anforderungsdokumente aus der Perspektive eines Smart-Home-Enthusiasten") and the entire body are review/research-shaped (no edits to source code anywhere); yet `tools` declares `Write`. `agent-review` MUST forbid write tools on read-only agents.
      Where: `.claude/agents/smart-home-ha-reviewer.md:5` (`tools: Read, Write, Glob, Grep`).
      Fix: Remove `Write` from `tools`. The Phase 3 instruction "Erstelle `spec/analysis/smart-home-ha-integration-review.md`" should be refactored: either (a) the agent returns the report content as its structured deliverable and an orchestrating skill persists it (skill-vs-agent hybrid pattern), or (b) — if persistence stays on the agent — note that the read-only invariant nevertheless forbids `Write`; the right fix is the orchestrator pattern.
      Verify: `tools` lists `Read, Glob, Grep` only; `grep -E "^tools:" .claude/agents/smart-home-ha-reviewer.md` shows no write tool; the body's persistence step is rephrased to return content rather than write.

- [ ] [agent-management.english-body] Frontmatter `description` and the entire body are German (the file uses Unicode escape sequences like `ü` etc. in some places but the content is German); `agent-management` Structure-MUST requires English content.
      Where: `.claude/agents/smart-home-ha-reviewer.md:4` (description) and lines 10-432 (entire body).
      Fix: Translate description, persona paragraph, all phase headings ("Phase 1: Dokumente einlesen" → "Phase 1: Read requirement documents"), three-side model section A/B/C, integration tables, and the Phase 3 report skeleton to English. Keep German only when literally quoting REQ/NFR identifiers or German UI literals.
      Verify: A `lang detect` pass on body returns >95% English; section headings read `## Phase 1:` etc. in English.

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432` (no rationale section anywhere).
      Fix: Add a short rationale paragraph or 2-4-bullet list near the top naming decisive dimensions — most plausibly *specialization* (Smart-Home-Enthusiast persona sharpens the HA-integration view), *context-window protection* (large reads of `spec/req/`, `spec/nfr/`, `spec/ui-nfr/`, `spec/stack.md`), and *parallelism* (can run alongside other persona reviewers). Cite at least one counter-dimension.
      Verify: Section reading "## Rationale" or equivalent exists naming ≥1 decisive dimension; grep returns ≥1 hit for "specialization" or "context-window".

- [ ] [agent-management.output-shape] Expected output shape is described only in Phase 3 as a Markdown report skeleton at `spec/analysis/smart-home-ha-integration-review.md` plus the Phase 4 chat summary; the file lacks an upfront "Output contract" stating what the parent caller receives.
      Where: `.claude/agents/smart-home-ha-reviewer.md:236-432`.
      Fix: Add an "Output contract" section near the top stating: (a) what the parent receives (path + chat summary), (b) the report's seven required structural sections (zwei-seiten-modell, integrations-architektur, integrationslandkarte A/B/C, fehlt-komplett, unvollständig, gut-gelöst, optionalitäts-checkliste), (c) explicit acknowledgement of the file-write side effect.
      Verify: A "Output contract" section exists near the top; reading it tells a parent caller the deliverable shape.

- [ ] [agent-management.write-effects-documented] Even if `Write` is dropped per the read-only BLOCKER, the body still imperatively says "Erstelle `spec/analysis/smart-home-ha-integration-review.md`"; per `agent-management.acceptance` write goals and preconditions MUST be documented when the agent performs side effects (or the side effect must be removed).
      Where: `.claude/agents/smart-home-ha-reviewer.md:236-237` ("Erstelle `spec/analysis/smart-home-ha-integration-review.md`").
      Fix: Replace the imperative with "Return the following report shape to the caller; the orchestrating skill is responsible for persistence." Alternatively, if writes stay (and `Write` is kept), document goals/preconditions per `agent-management.acceptance`. The orchestrator option is the lower-friction fix.
      Verify: Phase 3 instruction either no longer uses imperative "Erstelle" + path, or the body documents file-write goals/preconditions explicitly.

### WARNING

- [ ] [agent-review.duplicate-prevention] Material capability overlap with peer `ha-integration-requirements-engineer`: both surface HA-specific requirement work. The boundary "review the HA integration spec" vs. "derive HA requirements" is subtle but described differently across artifacts. The `verify-ha`, `deploy-ha`, and `ha-derive` skills are also in this cluster.
      Where: `.claude/agents/smart-home-ha-reviewer.md:4` (description) vs. peer `ha-integration-requirements-engineer` and skills `verify-ha`, `deploy-ha`, `ha-derive`.
      Fix: Add explicit negative triggers to `description` ("don't use for deriving new HA requirements from scratch — use `ha-integration-requirements-engineer` or the `ha-derive` skill; don't use for verifying or deploying the HA integration — use `verify-ha` / `deploy-ha`"). Per `skill-vs-agent.duplicate-prevention` plausibly-overlapping artifacts SHOULD propose a clearer split.
      Verify: `description` contains "don't use for" naming at least the closest peer agent and the two closest skills.

- [ ] [agent-management.prompt-structure-order] System prompt opens with the persona, then the Smart-Home profile, then the three-side model, then phases; the role-then-output-then-method ordering required by `agent-management.recommendations` SHOULD is fragmented — output shape only emerges in Phase 3.
      Where: `.claude/agents/smart-home-ha-reviewer.md:10-432`.
      Fix: Restructure: persona paragraph → "Output contract" → method (three-side model + phases). Move the persona-detail bullets after the contract.
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; tags `review` and `audience` would apply per `agent-management.tag-vocabulary` SHOULD (this agent is a persona/audience-review artifact in the same cluster as the other persona reviewers).
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, audience]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.length-target] Body is ~432 lines — over the ~200-line soft target in `agent-management.recommendations`; the three-side model A/B/C blocks and the report skeleton would factor cleanly into `agents/smart-home-ha-reviewer/` siblings.
      Where: `.claude/agents/smart-home-ha-reviewer.md:30-432`.
      Fix: Move the three-side model details and the Phase 3 report skeleton into `.claude/agents/smart-home-ha-reviewer/` referenced by relative path; keep the procedure spine inline.
      Verify: Body is ≤300 lines; sibling assets exist and are referenced relatively.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches; the description and body are review-shaped but the imperative "Erstelle …" creates ambiguity. Per `agent-management.recommendations` SHOULD the distinction must be visible at dispatch time.
      Where: `.claude/agents/smart-home-ha-reviewer.md:10-432`.
      Fix: Add a one-line statement near the top after the BLOCKER fix is in place: "This agent researches and emits a structured report — it does not modify source code or write files; the orchestrator is responsible for persistence."
      Verify: One sentence near the top declares "researches", "no writes", and the orchestrator-persists boundary.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named per `skill-vs-agent`; for this agent a plausible counter is *interactivity* (a smart-home power user might want to confirm the integration map mid-flow), which would push toward a skill.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432` (will be addressed once rationale section exists).
      Fix: Within the rationale section, add one bullet naming interactivity (mid-flow confirmation) as the counter-dimension and the reason it was outweighed (e.g. fire-and-forget review with post-hoc inspection).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` and the comment line states a rationale ("Persona-basierter Anforderungs-Review aus Smart-Home-Sicht (HA-Trennung, MQTT, Aktorik); sonnet adaequat"), satisfying `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/smart-home-ha-reviewer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; matches project-scoped reuse.
      Where: `.claude/agents/smart-home-ha-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/smart-home-ha-reviewer.md:1-432`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
