---
review-type: agent-review
target: ".claude/agents/rag-eval-runner.md"
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
status: in-progress
supersedes: "previous iteration of this plan — see git history of this file"
---

# Agent Review: rag-eval-runner

## Scope

Target: `.claude/agents/rag-eval-runner.md` (frontmatter + 348-line body, no sibling assets under `agents/rag-eval-runner/`).
Specs applied: `agent-management` (rev 7772341), `skill-vs-agent` (rev 0e3b6f9), `review-plan` (rev 0e3b6f9), `agent-review` (rev 7772341).
Narrowing: none — full re-review (Iteration 2). The relaxed language SHOULD applies; Kamerplanter `CLAUDE.md` lines 9-11 authorize German body+description, so language drops from BLOCKER to INFO. The agent description names read-only verbs ("Fuehrt ... aus, interpretiert, klassifiziert, schlaegt ... vor"), so the read-only-tools rule applies — but the body actually performs write side effects (SYNONYM_GAP fixes, report writing), creating a description/tools mismatch.
Explicitly out of scope: runtime behavior, Vale/markdown style, eval-script correctness.

## Summary

- BLOCKER: 2
- WARNING: 3
- SUGGESTION: 1
- INFO: 2

Go/no-go: FAIL — description names read-only verbs but tools and body perform writes. Either reframe the description to a write-author, or split into a read-only reporter agent + a separate fixer skill.

## Findings

### BLOCKER

- [x] [agent-review.Read-only-tools-rule] Description names only read-only verbs ("Fuehrt ... aus, interpretiert, klassifiziert, schlaegt ... vor"), but `tools` declares `Edit`, `Write`, and `Bash` — per `agent-review.Checks-derived-from-agent-management` ("read-only agents MUST NOT receive write, edit, or execution tools"), this is a BLOCKER.
      Where: frontmatter `description` lines 4-9 + `tools` line 10.
      Fix: Either (a) extend the description to name the write actions ("schreibt Report nach `test-reports/rag-eval/eval_report.md`, wendet SYNONYM_GAP-Fixes auf `spec/rag-eval/topic_synonyms.yaml` an"), or (b) remove `Edit`/`Write` and split out the fixer step into a separate skill that the reporter dispatches.
      Verify: Description and tools agree on read-only vs. write — either both read-only (no Edit/Write/Bash) or description explicitly names write outputs.
      Resolution (Iter 2): Description rewritten to name write actions explicitly: report writing to `test-reports/rag-eval/eval_report.md`, SYNONYM_GAP fixes in `spec/rag-eval/topic_synonyms.yaml`, QUESTION_AMBIGUITY fixes in `spec/rag-eval/benchmark_questions.yaml`. Now an Implementer-Reporter, not a read-only Reporter — Edit/Write/Bash are legitimate.

- [x] [skill-vs-agent.Rationale-documentation] No rationale section names a decisive skill-vs-agent dimension for the agent-over-skill choice.
      Where: body (no "Begruendung"/"Rationale" section).
      Fix: Add a short "Skill-vs-Agent-Begruendung" section naming the decisive dimensions (e.g. context-window protection during full benchmark output parsing, specialization for failure-classification entscheidungsbaum). Note: the agent also dispatches `knowledge-chunk-author`, which by `skill-vs-agent.Hybrid-pattern` should ideally be a skill orchestrating the agent — flag this as part of the rationale.
      Verify: `grep -i 'rationale\|begruendung\|skill-vs-agent'` returns a body-level match.
      Resolution (Iter 2): Rationale section added naming Specialization (entscheidungsbaum), Context-window protection (full benchmark output parsing), Self-contained-mit-Side-Effects; counter-dimension acknowledges Hybrid-pattern violation in Phase 6 (`knowledge-chunk-author` dispatch), reframes to "recommend, not dispatch" with follow-up note.

### WARNING

- [ ] [agent-management.Model-selection-justification] Pinned `model: sonnet` carries only a one-line frontmatter comment; the body never repeats the rationale.
      Where: frontmatter line 11 (comment) — body has no model-rationale paragraph.
      Fix: Add a body-level model-rationale (e.g. under "Ausfuehrungsrichtlinien"): "sonnet for entscheidungsbaum classification across many failures with reasoned suggestion priorities".
      Verify: `grep -i 'sonnet\|modell' .claude/agents/rag-eval-runner.md` returns a body-level mention.

- [ ] [agent-management.Side-effects-documentation] `tools` declares `Write`, `Edit`, and `Bash`; side effects include shell calls to `python eval_rag.py`, `curl`, `psql`, `cp`, plus writing `eval_report.md` and editing `topic_synonyms.yaml`/`benchmark_questions.yaml`. No dedicated section lists targets and preconditions.
      Where: frontmatter line 10 — body Phase 1-6 names targets informally.
      Fix: Add a "Schreibrechte und Bash-Nutzung" subsection naming write targets (`test-reports/rag-eval/eval_report.md`, `spec/rag-eval/topic_synonyms.yaml`, `spec/rag-eval/benchmark_questions.yaml`) and bash boundaries (only `python eval_rag.py`, service-readiness curls, `cp` of prior eval results).
      Verify: Body contains an explicit side-effects section.

- [ ] [skill-vs-agent.Hybrid-pattern] The agent dispatches `knowledge-chunk-author` ("knowledge-chunk-author Agent gestartet werden") which inverts the skill-orchestrates-agent rule (`skill-vs-agent.Hybrid-pattern` MUST: "an agent MUST NOT invoke the Skill tool on behalf of the user", and dispatching peer agents is the orchestrator role of a skill).
      Where: body Phase 6 lines 314-333.
      Fix: Move the orchestration into a skill that runs `rag-eval-runner` then `knowledge-chunk-author`; the agent should report and recommend, not dispatch.
      Verify: Body no longer dispatches peer agents directly; orchestration handled by a skill.

### SUGGESTION

- [ ] [agent-management.Tag-vocabulary] No `tags` field; the catalog cannot place this in a quality-gate or audit cluster.
      Where: frontmatter (no `tags` key).
      Fix: Add `tags: [audit, quality-gate]` from the starter vocabulary.
      Verify: Frontmatter parses with a `tags` list of <=5 entries.

### INFO

- [ ] [agent-management.Structure-language] Description and body authored in German.
      Where: frontmatter `description` lines 4-9 + entire body.
      Fix: n/a — Kamerplanter `CLAUDE.md` lines 9-11 authorize German prose for `distribution: project` agents.
      Verify: n/a.

- [ ] [agent-review.Review-procedure] Iteration 2 re-review applies the relaxed language SHOULD; previous language BLOCKER drops to INFO. The read-only-tools BLOCKER is a tightening: previously the description and tools were considered separately; the spec's MUST treats read-only-by-description with write-tools as a BLOCKER.
      Where: this plan's `## Scope`.
      Fix: n/a (procedural note).
      Verify: n/a.

## Processing log

<!-- Append one line per item closure: YYYY-MM-DD — <item-shorthand> — <action taken> — verified: <method> -->
2026-04-27 — Read-only-tools-rule — description rewritten to explicitly name write actions (Report-Schreiben, SYNONYM_GAP-/QUESTION_AMBIGUITY-Fixes); agent reclassified from read-only Reporter to Implementer-Reporter, Edit/Write/Bash now consistent with description — verified: description includes "schreibt ... Report" and "implementiert priorisierte Verbesserungsmassnahmen direkt"
2026-04-27 — Rationale-documentation — added "## Rationale: Skill vs Agent" naming Specialization, Context-window protection, Self-contained-with-Side-Effects; counter-dimension addresses Hybrid-pattern conflict for `knowledge-chunk-author` dispatch — verified: grep "Rationale" matches body
