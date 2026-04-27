---
review-type: agent-review
target: ".claude/agents/rag-eval-runner.md"
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

# Agent Review: rag-eval-runner

## Scope

Target: `.claude/agents/rag-eval-runner.md` (frontmatter + 348-line body, no sibling assets under `agents/rag-eval-runner/`).
Specs applied: `agent-management`, `skill-vs-agent`, `review-plan`, `agent-review` (revisions in frontmatter).
Narrowing: none — full review.
Explicitly out of scope: runtime correctness of the eval script itself, the downstream `knowledge-chunk-author` agent (peer in pipeline, reviewed separately), the dispatching skill (none documented).

## Summary

- BLOCKER: 4
- WARNING: 4
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — body language, missing rationale, and read-only-vs-write tool mismatch block dispatch readiness.
Next concrete action: rewrite system prompt in English, add rationale section, and reconcile the Reporter role with the declared `Write`/`Edit`/`Bash` write tools.

## Findings

### BLOCKER

- [ ] [agent-management.Structure.MUST-english] Agent body is authored entirely in German, including section headings ("Phase 1: Infrastruktur-Check", "Fehler-Klassifizierung (Deterministischer Entscheidungsbaum)", "Ausfuehrungsrichtlinien") and rules.
      Where: `.claude/agents/rag-eval-runner.md:14-348`.
      Fix: rewrite the system prompt in English; the agent may still produce German report text where appropriate, but the prompt scaffolding must be English per `agent-management` MUST.
      Verify: `rg -n '[äöüÄÖÜß]' .claude/agents/rag-eval-runner.md` returns hits only inside quoted German example strings.

- [ ] [skill-vs-agent.Rationale-documentation.MUST] The body has no rationale section that names a decisive dimension for the agent-over-skill choice.
      Where: `.claude/agents/rag-eval-runner.md` (entire body, no rationale block detected).
      Fix: add a short rationale section naming at least one decisive dimension — likely "context-window protection" (eval JSON output is large) plus "specialization" (failure-classification decision tree benefits from a narrow system prompt).
      Verify: a paragraph or bulleted list explicitly stating the skill-vs-agent dimensions exists in the body.

- [ ] [agent-review.Checks-derived-from-agent-management.MUST-readonly-tools] Description self-describes the agent as "ausfuehren, interpretieren, klassifizieren, vorschlagen" — a reporting/research role — but `tools` declares `Write`, `Edit`, and `Bash`, which the agent-only invariants reject for read-only agents.
      Where: `.claude/agents/rag-eval-runner.md:5-10` description vs `:10` tools list.
      Fix: either drop `Write`/`Edit` and let the calling skill persist the report (read-only research stance), or rewrite the role section to authorize specific writes — Phase 5 writes `test-reports/rag-eval/eval_report.md`, Phase 6 may edit `spec/rag-eval/topic_synonyms.yaml` and `benchmark_questions.yaml` (human-in-the-loop "nur nach Ruecksprache").
      Verify: tools list and role match — either both read-only or both authoring with target paths declared.

- [ ] [agent-management.Recommendations.SHOULD-writes-vs-research] The system prompt does not state up front that the agent writes a report file and may edit YAML config files (Phases 5–6).
      Where: `.claude/agents/rag-eval-runner.md:1-15` (frontmatter + opening role).
      Fix: add an explicit sentence in the role block listing every write target — `test-reports/rag-eval/eval_report.md`, `test-reports/rag-eval/eval_results_prev.json` (cp), `spec/rag-eval/topic_synonyms.yaml`, `spec/rag-eval/benchmark_questions.yaml` — and the human-approval gate for the latter two.
      Verify: the role section names each side effect and target path.

### WARNING

- [ ] [skill-vs-agent.Duplicate-prevention.MUST] Agent dispatches/recommends `knowledge-chunk-author` (Phase 6) — sibling pipeline stage, no overlap; description does not name the downstream sibling.
      Where: `.claude/agents/rag-eval-runner.md:5-10`.
      Fix: extend description with explicit "after this agent's report, dispatch `knowledge-chunk-author` for KNOWLEDGE_GAP / RETRIEVAL_MISS / Chunk-Kontamination fixes" and note the auto-applied SYNONYM_GAP/QUESTION_AMBIGUITY fixes are this agent's scope.
      Verify: description names the pipeline successor explicitly.

- [ ] [agent-management.Recommendations.SHOULD-length] Body is 348 lines (~1.7× the ~200-line soft target); the decision-tree diagram, classification table, and report template could move into siblings.
      Where: `.claude/agents/rag-eval-runner.md:130-198` (decision tree + tables), `:200-260` (report template).
      Fix: factor the failure-classification decision tree, the classification examples, and the report template into `agents/rag-eval-runner/` siblings referenced by relative path.
      Verify: body line count drops below ~200 after factoring.

- [ ] [agent-review.Tool-scope.SHOULD-bash-vs-dedicated] Bash is declared and used heavily for service health checks (curl), DB ping (psql), `cp` of result JSON, and `python tools/rag-eval/eval_rag.py` invocations — the eval script invocation is a legitimate Bash use case; the file copy could be a dedicated tool.
      Where: `.claude/agents/rag-eval-runner.md:10,38-65`.
      Fix: keep Bash for the eval invocation and the curl/psql health checks; document the rationale; replace `cp ...eval_results.json ...prev.json` with a `Read`+`Write` pair if that fits the workflow.
      Verify: every Bash invocation in the body has an external-CLI rationale.

- [ ] [agent-management.Recommendations.SHOULD-negative-triggers] Description has only positive triggers; with overlap risk against future RAG-quality skills and the `knowledge-chunk-author` agent, negative cases would help routing.
      Where: `.claude/agents/rag-eval-runner.md:4-10`.
      Fix: add explicit "don't use for chunk authoring (use `knowledge-chunk-author`); don't use for ingestion (separate)".
      Verify: description contains explicit negative-trigger phrasing.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary.MAY] Agent has no `tags` frontmatter field; tagging it (e.g. `[review, quality-gate]` or `[audit, knowledge]`) would cluster it with peers.
      Where: `.claude/agents/rag-eval-runner.md:1-13`.
      Fix: add `tags: [audit, knowledge]` (each ≤30 chars, list ≤5).
      Verify: frontmatter parses with valid `tags`.

### INFO

- [ ] [agent-review.Checks-derived-from-skill-vs-agent.MUST-no-skill-dispatch] No `Skill(`, `Skill tool`, or `Skill <name>` invocations were found in the body — agent recommends the user dispatch the `knowledge-chunk-author` agent next, which is allowed.
      Where: full body grep clean for skill dispatch.
      Fix: n/a (observation).
      Verify: n/a.

- [ ] [agent-management.Model-selection.MAY] `model: sonnet` is pinned with a one-line rationale comment ("Eval-Ausfuehrung + Fehlerklassifikation … sonnet adaequat fuer Reporting") — meets the rationale SHOULD; reporting + classification on sonnet is plausible.
      Where: `.claude/agents/rag-eval-runner.md:11-12`.
      Fix: n/a (observation).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
