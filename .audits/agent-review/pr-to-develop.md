---
review-type: agent-review
target: ".claude/agents/pr-to-develop.md"
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

# Agent Review: pr-to-develop

## Scope

Target: `.claude/agents/pr-to-develop.md` (frontmatter + 272-line body, no sibling assets under `agents/pr-to-develop/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent` (rev 0e3b6f9), `review-plan` (rev 0e3b6f9), `agent-review` (rev 7772341).
Narrowing: none — full re-review (Iteration 2). The relaxed language SHOULD applies; Kamerplanter `CLAUDE.md` lines 9-11 authorize German body+description, so language drops from BLOCKER to INFO. The orchestrator-as-agent BLOCKER from `skill-vs-agent.Primary-decision-rule` is NOT addressed by Quick-Wins and remains BLOCKER.
Explicitly out of scope: runtime behavior of `act`, Vale/markdown style, GitHub CI green/red status.

## Summary

- BLOCKER: 3
- WARNING: 2
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — three BLOCKERs (orchestrator-as-agent, duplicate, rationale section).
Next concrete action: convert this agent into a skill (deprecate the agent), or merge with `nolte-shared` skills `pull-request-create` / `pull-request-merge` to remove the duplicate.

## Findings

### BLOCKER

- [ ] [skill-vs-agent.Primary-decision-rule] The artifact is structurally an orchestrator (multi-step procedure with mid-flow user gating, dispatches the `unit-test-runner` agent via `Agent(subagent_type=...)`, manages PR-creation flow). `skill-vs-agent` MUSTs an orchestrator be a skill, not an agent.
      Where: body Schritt 2 (line ~37 `Agent(subagent_type="unit-test-runner", ...)`) + the entire 11-step workflow.
      Fix: Re-author as a skill under `nolte-shared` (or as a project-local skill) and deprecate this agent file with a pointer, per `skill-vs-agent.Portfolio-wide-consistency` ("reclassification ... ships as a new artifact plus a deprecation note on the old one").
      Verify: `pr-to-develop.md` carries a deprecation banner and a new skill exists; or the agent body is gone and a skill replaces it.

- [ ] [skill-vs-agent.Duplicate-prevention] Plausible capability overlap with `nolte-shared/skills/pull-request-create` and `pull-request-merge` — both author Conventional-Commits PRs with structured bodies and CI gating.
      Where: frontmatter `description` line 4 vs. the two `nolte-shared` skill descriptions.
      Fix: Either (a) deprecate `pr-to-develop` and use the upstream skills, or (b) document the project-specific delta (act-validation, REQ-/NFR-numbering, German body) explicitly to justify the project-local copy.
      Verify: Body or frontmatter records the relationship to the upstream skills, or this file is deprecated.

- [ ] [skill-vs-agent.Rationale-documentation] No rationale section names a decisive skill-vs-agent dimension for the agent-over-skill choice — and the choice is in fact wrong (see BLOCKER above), so adding a rationale alone does not close this.
      Where: body (no "Begruendung"/"Rationale" section).
      Fix: Either remove the agent (see first BLOCKER) or, if a project-local agent must remain temporarily, add a rationale section that explicitly acknowledges the conflict with `skill-vs-agent` and links to a follow-up issue.
      Verify: `grep -i 'rationale\|begruendung\|skill-vs-agent'` returns a body-level match, and the conflict is named.

### WARNING

- [ ] [agent-management.Tools-bash-preference] `Bash` is declared and heavily used for git/gh/act/docker/helm shell calls; the body justifies it implicitly but never states why no dedicated tool covers these (correct, but per spec the rationale should be visible).
      Where: frontmatter line 5 — body Schritt 1-10 uses Bash extensively.
      Fix: Add a paragraph in the body noting that `Bash` is required because no dedicated tool covers `git`, `gh`, `act`, `docker`, `helm`.
      Verify: Body contains the bash-rationale paragraph.

- [ ] [agent-management.Side-effects-documentation] `tools` declares `Bash` (and `Agent`); side effects include git pushes, GitHub PR creation, docker image build/cleanup, but no dedicated section lists targets and preconditions.
      Where: frontmatter line 5 — Schritt 5 (`git push`), Schritt 9 (`gh pr create`), Schritt 4 (`docker build`/`docker rmi`).
      Fix: Add a "Side Effects" subsection naming git push targets (only the current branch, never main/develop), GitHub side effects (PR creation, never merge), docker image lifecycle (test-only, cleaned up after).
      Verify: Body contains an explicit side-effects section.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary] No `tags` field; cluster membership with `pull-request-create`/`pull-request-merge` (starter tag `pull-request`) is not machine-checkable.
      Where: frontmatter (no `tags` key).
      Fix: Add `tags: [pull-request, quality-gate]` from the starter vocabulary.
      Verify: Frontmatter parses with a `tags` list of <=5 entries.

### INFO

- [ ] [agent-management.Structure-language] Description and body authored in German; "Wichtige Regeln" line 5 explicitly mentions "Deutsche Beschreibung — die PR-Beschreibung ist auf Deutsch (Dokumentationssprache)".
      Where: frontmatter `description` line 4 + entire body.
      Fix: n/a — Kamerplanter `CLAUDE.md` lines 9-11 authorize German prose for `distribution: project` agents.
      Verify: n/a.

- [ ] [agent-management.Tools-bidirectional] `Agent` tool is declared and used (Schritt 2 dispatches `unit-test-runner`); `Read`, `Bash`, `Glob`, `Grep` all have body usage. Tool-declaration matches body usage.
      Where: frontmatter line 5 — body Schritt 1-10.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
