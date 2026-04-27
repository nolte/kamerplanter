---
review-type: agent-review
target: ".claude/agents/pr-to-develop.md"
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

# Agent Review: pr-to-develop

## Scope

Target: `.claude/agents/pr-to-develop.md` (frontmatter + 272-line body, no sibling assets under `agents/pr-to-develop/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: GitHub-CLI behavior at runtime, the dispatched `unit-test-runner` agent (peer, reviewed separately), the `pull-request-create`/`pull-request-merge` skills available in the plugin (peer-cluster awareness only).

## Summary

- BLOCKER: 4
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language and orchestrator-as-agent shape conflict with skill-vs-agent rules.
Next concrete action: rewrite system prompt in English, add rationale section, and reconsider whether this should be a skill (per `skill-vs-agent` Primary decision rule: orchestrators are skills).

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body and frontmatter description are authored in German throughout, including section headings ("Workflow", "Schritt 1: Branch-Analyse", "Wichtige Regeln") and rules.
      Where: `.claude/agents/pr-to-develop.md:4` (description) and `:10-272` (entire body).
      Fix: rewrite the system prompt in English; PR titles/bodies may still be project-language as required, but the prompt scaffolding must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/pr-to-develop.md` returns hits only inside quoted German example strings.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice — and this choice is contestable per the Primary decision rule below.
      Where: `.claude/agents/pr-to-develop.md` (entire body, no rationale block detected).
      Fix: add a rationale section explicitly justifying agent-over-skill; if no decisive dimension can be named, reclassify as a skill per `skill-vs-agent` Primary decision rule MUST default-to-skill.
      Verify: rationale paragraph names ≥1 decisive dimension, or the artifact is reclassified.

- [ ] [skill-vs-agent.Primary-decision-rule.MUST-orchestrator-is-skill] The body documents an orchestrator workflow that dispatches another agent (`unit-test-runner`) and runs interactive multi-step procedures (push, watch CI, multi-loop test fixing) — this matches the "procedure itself dispatches one or more agents — the orchestrator is always a skill" MUST in `skill-vs-agent`.
      Where: `.claude/agents/pr-to-develop.md:36-50` (delegates to `unit-test-runner` agent), `:228-241` (CI watch loop).
      Fix: reclassify as a skill (e.g. `pr-to-develop` skill that dispatches the `unit-test-runner` agent and integrates with the existing `pull-request-create`/`pull-request-merge` skills); ship as a new artifact and deprecate the agent per the reclassification rule.
      Verify: artifact moves under `skills/pr-to-develop/SKILL.md` (or merges into `pull-request-create`); the orchestrator role lives in a skill, not an agent.

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] The system prompt does not state explicitly that the agent runs builds, pushes branches, and creates PRs (heavy side effects), even though `Bash` is declared.
      Where: `.claude/agents/pr-to-develop.md:1-12` (frontmatter + opening role).
      Fix: add an explicit sentence in the role block stating "this agent runs `act`, `docker build`, `helm lint`, pushes the current branch with `git push`, and creates a PR with `gh pr create`"; even if the artifact is reclassified as a skill, the same disclosure is required.
      Verify: the role section names every side effect and the target tool/CLI.

### WARNING

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] Plugin already provides `pull-request-create` and `pull-request-merge` skills covering PR-create and PR-merge; this agent overlaps with `pull-request-create` and partially with `pull-request-merge` (CI watch).
      Where: `.claude/agents/pr-to-develop.md:4` description vs the plugin skills `pull-request-create`, `pull-request-merge`.
      Fix: merge into `pull-request-create` (extending it to cover the local-act validation), or split: delegate PR creation to the existing skill and keep this artifact only as the act-validation step.
      Verify: capability statement of this artifact does not overlap with the existing PR-related skills.

- [ ] [agent-review.Tool-scope.SHOULD-bash-vs-dedicated] Bash is declared and heavily used; a few uses (`git log`, `git diff --stat`) could in principle be `Grep`/`Glob`, but the bulk (act, docker, helm, gh) genuinely needs the shell — document that.
      Where: `.claude/agents/pr-to-develop.md:5,18-32`.
      Fix: keep Bash but document the build/test/CLI rationale explicitly in the role block; replace `git log`/grep style readouts with `Grep` where they don't need shell features.
      Verify: every Bash invocation in the body has a build/CLI rationale that a dedicated tool wouldn't cover.

- [ ] [agent-review.Tool-scope.MUST-undeclared] The body invokes the `Agent` tool (Step 2 dispatches `unit-test-runner`); `Agent` is included in the `tools` list, so this is consistent — but spec note: `Agent`-tool invocations are allowed, only `Skill`-tool invocations are forbidden, so this is OK.
      Where: `.claude/agents/pr-to-develop.md:5,38` (`Agent(subagent_type="unit-test-runner", ...)`).
      Fix: confirm explicitly in the role block that this agent dispatches sibling agents (and does not dispatch skills); otherwise no change needed.
      Verify: a body sentence states "this agent may dispatch sibling agents via the Agent tool but never invokes the Skill tool".

- [ ] [agent-management.Recommendations.SHOULD-negative-triggers] Description has only positive triggers; given overlap with `pull-request-create`/`pull-request-merge` skills, negative cases are essential.
      Where: `.claude/agents/pr-to-develop.md:4`.
      Fix: add explicit "don't use for PR creation alone (use the `pull-request-create` skill); don't use for landing/merging (use `pull-request-merge`)".
      Verify: description contains explicit negative-trigger phrasing pointing at the peer skills.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; tagging it (e.g. `[pull-request, quality-gate]`) would cluster it with the PR-related skills.
      Where: `.claude/agents/pr-to-develop.md:1-8`.
      Fix: add `tags: [pull-request, quality-gate]` (each ≤30 chars, list ≤5).
      Verify: frontmatter parses with valid `tags`.

### INFO

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — only `Agent(...)` calls, which are allowed.
      Where: full body grep clean for skill dispatch.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.Model-selection.MAY] `model: sonnet` is pinned with a one-line rationale comment ("Orchestrator … kein opus-Reasoning noetig") — meets the rationale SHOULD; orchestrator on sonnet is plausible.
      Where: `.claude/agents/pr-to-develop.md:6-7`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
