---
review-type: agent-review
target: ".claude/agents/selenium-test-reviewer.md"
target-kind: agent
specs-applied:
  - slug: agent-management
    revision: "7772341"
  - slug: skill-vs-agent
    revision: "0e3b6f9"
  - slug: review-plan
    revision: "0e3b6f9"
  - slug: agent-review
    revision: "7772341"
repo-revision: "728ac421"
created: "2026-04-28"
status: open
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: selenium-test-reviewer

## Scope

Iteration 2 of this plan. The `agent-management` and `agent-review` specs have been revised: a project-distribution agent in a project whose root convention file (`CLAUDE.md`) authorizes a non-English documentation language for agent prose may author its `description` and body in that language. Kamerplanter's `CLAUDE.md` lines 9-11 explicitly authorize German for `.claude/agents/`, so what was a German-prose BLOCKER in iteration 1 demotes to INFO here.

Target: `.claude/agents/selenium-test-reviewer.md` (frontmatter + body, ~295 lines, no sibling assets under `.claude/agents/selenium-test-reviewer/`).
Specs applied: `agent-management` rev 7772341, `skill-vs-agent`, `review-plan`, `agent-review` rev 7772341 (revisions in frontmatter).
Narrowing: none — full review surface.
Explicitly out of scope: runtime behavior, Vale/markdown style, factual correctness of the embedded code samples, the dispatching skill (none declared but `selenium-test-generator` is the obvious peer agent).

## Summary

- BLOCKER: 3
- WARNING: 5
- SUGGESTION: 1
- INFO: 4

Go/no-go: FAIL — three remaining MUST violations after the language relaxation: missing rationale section, missing upfront output contract, and consolidated write-effect goals/preconditions for the `Edit`-tool surface (the agent legitimately rewrites tests/e2e/ files and may create missing files).
Next concrete action: author addresses the three remaining BLOCKERs (rationale section anchored in `skill-vs-agent`; explicit Output contract block; consolidated write-effects section for the Edit/Bash surface) and clarifies the boundary against `selenium-test-generator`.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.rationale-section] Body lacks a rationale section naming at least one decisive dimension for the agent-over-skill choice; this is a MUST per `skill-vs-agent` and an explicit BLOCKER per `agent-review`.
      Where: `.claude/agents/selenium-test-reviewer.md:1-295` (no "Why this is an agent" section).
      Fix: Add a short rationale paragraph or 2-4 bullet list near the top naming decisive dimensions — most plausibly tool restriction (`Edit` only, no `Write`), specialization (NFR-008/NFR-008a checklist), and self-contained input/output (compliance report). Important given the peer `selenium-test-generator` agent.
      Verify: A "Rationale" section near the top names ≥1 decisive dimension; grep returns ≥1 hit for "specialization", "tool-restriction", or "self-contained".

- [ ] [agent-management.output-shape] Expected output shape is described only in Step 6 as a Markdown report skeleton; the file lacks an upfront "Output contract" stating what the parent caller receives and what files (if any) are modified.
      Where: `.claude/agents/selenium-test-reviewer.md:223-273`.
      Fix: Add an "Output contract" section near the top stating (a) what the parent receives (chat-rendered compliance report), (b) the report's required tables, (c) any modified files (in-place edits to `tests/e2e/` and possibly newly created `base_page.py`/`protocol_plugin.py`), (d) overwrite policy.
      Verify: An "Output contract" section exists near the top; reading it tells a parent caller every deliverable and side-effect target.

- [ ] [agent-management.write-effects-documented] Agent declares `Edit` and `Bash` and the closing "Wichtige Prinzipien" lines explicitly say the agent *creates* missing files (`base_page.py`, `protocol_plugin.py`) and *migrates* `selenium_tests/` → `tests/e2e/`. These write effects are not consolidated upfront per `agent-management` acceptance.
      Where: `.claude/agents/selenium-test-reviewer.md:5` (tools) vs. body lines 287-294 (Wichtige Prinzipien) — write effects scattered.
      Fix: Add a "File outputs" / write-effects section consolidating: every potentially modified path (`tests/e2e/conftest.py`, `tests/e2e/protocol_plugin.py`, `tests/e2e/pages/base_page.py`, `tests/e2e/test_*.py`), preconditions (NFR-008 violation found, minimal-change principle), and the explicit invariant that frontend/backend production code is never modified.
      Verify: Body contains a single consolidated write-effects section naming target paths and preconditions; grep for "tests/e2e" returns hits in that section.

### WARNING

- [ ] [agent-review.duplicate-prevention] Material capability overlap with `selenium-test-generator` (peer agent, same NFR-008 surface). The reviewer creates missing files (per Wichtige Prinzipien lines 287-294), which crosses into generator territory. Per `agent-review.duplicate-prevention` this is a WARNING; the `description` does not declare negative triggers naming the peer.
      Where: `.claude/agents/selenium-test-reviewer.md:4` vs. peer `.claude/agents/selenium-test-generator.md`.
      Fix: Add explicit negative trigger to `description`: "nicht für initiale Test-Generierung — dafür `selenium-test-generator`; dieser Agent reviewt + repariert existierende Tests minimal-invasiv". Also clarify in the body that *creating* `base_page.py`/`protocol_plugin.py` is a remediation last resort, not a generation path.
      Verify: `description` contains "nicht für" naming the peer agent; body distinguishes review-fix from generation.

- [ ] [agent-management.prompt-structure-order] System prompt opens with persona, then references, then "Aufgabe", then 7 numbered steps; output shape only emerges in Step 6. Role-then-output-then-method ordering SHOULD is not honored.
      Where: `.claude/agents/selenium-test-reviewer.md:10-294`.
      Fix: Restructure: persona → "Output contract" → procedure (Schritte 1-7) → guardrails (Wichtige Prinzipien).
      Verify: Reading the first 60 lines reveals role → output shape → method in that order.

- [ ] [agent-management.tags] No `tags` field declared; `review` and `quality-gate` would apply per `agent-management.tag-vocabulary` SHOULD.
      Where: `.claude/agents/selenium-test-reviewer.md:1-8` (frontmatter).
      Fix: Add `tags: [review, quality-gate]` after existing fields.
      Verify: Frontmatter parses as YAML containing `tags` of length ≤5 with all entries lowercase ASCII kebab-case ≤30 chars.

- [ ] [agent-management.research-vs-writes] System prompt does not explicitly declare upfront whether the agent writes code or only researches. The body ultimately edits and creates files but the dispatch-time signal is missing.
      Where: `.claude/agents/selenium-test-reviewer.md:10-294`.
      Fix: Add one sentence near the top: "This agent reviews existing E2E tests and applies minimal-invasive edits to `tests/e2e/`; it may create `base_page.py`/`protocol_plugin.py` if missing, but never modifies frontend or backend production code."
      Verify: One sentence near the top names "minimal-invasive edits", "tests/e2e/", and "no production-code edits".

- [ ] [agent-management.bash-vs-dedicated] Schritt 7 prescribes `python -m pytest --collect-only` via Bash; this is legitimate execution. However, `Edit`+`Bash` together with the create-missing-files behavior pushes the agent close to a generator role; consider whether a stricter read-mostly tool surface (Read+Grep+Glob plus the syntax-check Bash) would better signal the review intent.
      Where: `.claude/agents/selenium-test-reviewer.md:5` (tools) vs. lines 277-285 (Schritt 7 syntax-check).
      Fix: Either document why `Edit` is essential and scope its uses (BLOCKER above already addresses this) or, if the create-missing-files behavior should move to `selenium-test-generator`, drop `Edit` here.
      Verify: Either tools list documents the boundary, or `Edit` is removed and the behaviour migrates to the generator agent.

### SUGGESTION

- [ ] [skill-vs-agent.rationale-counter-dimension] When the rationale section is added (BLOCKER above), a counter-dimension SHOULD also be named; for this agent a plausible counter is interactivity (the user might want to confirm proposed edits before they land).
      Where: `.claude/agents/selenium-test-reviewer.md:1-295` (will be addressed once rationale section is authored).
      Fix: Within the rationale section, add one bullet naming interactivity as the counter-dimension and explain why it was outweighed (e.g. all changes are minimal-invasive and revertable via git).
      Verify: Rationale section contains ≥2 bullets, one of which names a counter-dimension.

### INFO

- [ ] [agent-management.english-body] Description and body are German throughout; per the revised `agent-management.Structure` exception this is acceptable for `distribution: project` agents in a project whose `CLAUDE.md` authorizes German for agent prose. Kamerplanter's `CLAUDE.md` lines 9-11 declare German as the project documentation language. Recorded as INFO, not BLOCKER.
      Where: `.claude/agents/selenium-test-reviewer.md:4` (description), lines 10-294 (body).
      Fix: n/a (observation — language exception applies).
      Verify: n/a.

- [ ] [agent-management.model-rationale-present] Frontmatter pins `model: sonnet` with rationale ("Test-Code-Review gegen NFR-008-Konformitaet; sonnet adaequat fuer strukturierte Findings"); satisfies `agent-management.model-selection` SHOULD.
      Where: `.claude/agents/selenium-test-reviewer.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.distribution-correct] `distribution: project` is declared exactly once with a valid value; no plugin-co-located asset references appear.
      Where: `.claude/agents/selenium-test-reviewer.md:3`.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [skill-vs-agent.no-skill-dispatch] Body never invokes the Skill tool on behalf of the user; satisfies the `skill-vs-agent` BLOCKER invariant per `agent-review`.
      Where: `.claude/agents/selenium-test-reviewer.md:1-295`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
