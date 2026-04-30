# Nuclei Findings — Triage Workflow

This page is the operational playbook for findings produced by the Nuclei DAST scans defined in [NFR-014](../../spec/nfr/NFR-014_Nuclei-Security-Scanning.md). It tells the on-call security owner what to do when a SARIF entry lands in GitHub Code Scanning or a nightly run opens an issue.

## When findings appear

| Source | Trigger | First responder |
|---|---|---|
| PR-Gate workflow (Phase 2B) | Pull request against `develop` / `main` | PR author |
| Nightly workflow (Phase 2B) | Cron `0 0 * * *` against staging | Rotating security owner |
| Local run via `scripts/security/nuclei-local.sh` | Manual | Whoever invoked it |

GitHub Code Scanning shows every SARIF result as an inline annotation on the PR diff. The nightly workflow additionally opens a GitHub Issue per `High` / `Critical` finding with the labels `security`, `nuclei`, and `severity-{critical,high,medium,low}`.

## Severity matrix

Identical to NFR-014 §5.1 — repeated here for quick lookup:

| Severity | PR-Gate | Nightly | Patch SLA |
|---|---|---|---|
| Critical | Block merge | Block + Page | 24 h |
| High | Block merge | Block + Issue | 7 days |
| Medium | Warn | Warn + Issue | 30 days |
| Low | Info | Info | Best-effort |
| Info | Collect | Collect | — |

## Triage steps

```
                ┌─────────────────────────┐
                │  Finding observed       │
                └────────────┬────────────┘
                             │
         ┌───────────────────▼───────────────────┐
         │  Is the finding reproducible?         │
         │  Run scripts/security/nuclei-local.sh │
         │  --profile pr against the same target │
         └───────────────────┬───────────────────┘
              repro fails    │   repro succeeds
                             │
              ┌──────────────┴───────────────┐
              ▼                              ▼
     ┌──────────────────┐         ┌──────────────────┐
     │  False positive  │         │  Real finding    │
     │  / flake         │         │                  │
     └────────┬─────────┘         └────────┬─────────┘
              │                            │
              ▼                            ▼
     Open suppression PR           Open fix-forward PR
     against                       against the offending
     tests/security/               component. Reference
     nuclei-suppressions.yaml      the issue / SARIF row.
     (NFR-014 §6.1)                CI re-runs Nuclei after
                                   merge; the finding self-
                                   closes when the next
                                   nightly is clean.
```

### True-positive path

1. **Confirm reproduction** — run the same template locally:
   ```bash
   ./scripts/security/nuclei-local.sh --profile pr http://localhost:8000
   ```
2. **Open a fix-forward PR** that targets the affected component. Reference the GitHub-Issue or SARIF run in the PR description.
3. **Wait for the next nightly run** (or trigger it manually via `workflow_dispatch`). When the finding stops showing up, GitHub Code Scanning closes the alert automatically; if the nightly opened a GitHub Issue, close it manually with a reference to the merge commit.

### False-positive / flake path

1. **Capture the evidence** — copy the offending SARIF row or run-log into the PR description so a future reviewer can reconstruct why the suppression was approved.
2. **Open a suppression PR** that adds an entry to `tests/security/nuclei-suppressions.yaml`. Every entry **must** carry:

   | Field | Purpose |
   |---|---|
   | `template_id` | The Nuclei template that fired (e.g. `kamerplanter-source-map`). |
   | `matched_url` | Optional — restrict the suppression to a specific URL. |
   | `reason` | Concrete justification, never just "false positive". |
   | `expires` | ISO-8601 date, max 12 months out. |
   | `approved_by` | `security-officer`, `maintainer`, or a GitHub handle. |

   Example:
   ```yaml
   suppressions:
     - template_id: tech-detect-fastapi
       reason: "Tech stack disclosure is internally known and not security-relevant in this project."
       expires: 2026-12-31
       approved_by: security-officer
   ```

3. **Re-run the gate** to confirm the suppression took effect. The pre-commit hook (`nuclei-validate`) and the CI workflow both consume the file via `scripts/security/build-nuclei-flags.sh`.

## Suppression hygiene

- Suppressions **expire**. The build-flags helper warns when an entry is past `expires`, and after 30 days of grace the script exits non-zero — closing the build until the entry is renewed or removed.
- **Do not extend an old entry**: open a new entry with a fresh `expires` and `approved_by`. The audit trail in git history is the point.
- **No `template_id: *` entries**. Suppressions are per-template — never wholesale.

## Adding a new project-specific template

1. Drop the YAML under `tests/security/nuclei-templates/`. Tag with `kamerplanter` plus topic tags (`headers`, `tenant`, `req-024`, …).
2. Run `nuclei -validate -t tests/security/nuclei-templates/<file>.yaml` locally. The pre-commit hook will run it for you on commit if `nuclei` is on PATH.
3. Reference the spec section in the template `info.reference` block (`https://github.com/nolte/kamerplanter/blob/develop/spec/nfr/NFR-014_Nuclei-Security-Scanning.md`).
4. Add a one-line entry to the table in `tests/security/README.md`.

## Rotating security owner

The on-call rotation is tracked in `docs/security/rotation.md` (Phase 4 — TBD). Until that file lands, the `MAINTAINERS` field in this repository serves as the default escalation list.

## See also

- [NFR-014 — Nuclei spec](../../spec/nfr/NFR-014_Nuclei-Security-Scanning.md)
- [NFR-015 — OWASP ZAP spec](../../spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md) (complementary, deeper DAST)
- [`tests/security/README.md`](../../tests/security/README.md) — artefact index
- [`scripts/security/nuclei-local.sh`](../../scripts/security/nuclei-local.sh) — local reproduction
- [`scripts/security/build-nuclei-flags.sh`](../../scripts/security/build-nuclei-flags.sh) — suppression compiler
