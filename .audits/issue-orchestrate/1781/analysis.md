# Pre-analysis — #1781 privacy: account keys / e-mail addresses in log lines outside the privacy surface

- Issue: https://github.com/nolte/kamerplanter/issues/1781 (author: nolte, owner — trusted)
- Classification: `security` (secondary `bug`) — personal data (account key, e-mail, IP) reaching a log stream without retention (NFR-011, REQ-025).
- Requirements gate: operator override (autonomous sweep 2026-09-24/25, every gate pre-approved); the issue carries explicit acceptance criteria plus the owner's residue comment.
- Route: implement directly (one outcome, one PR strand, no roadmap item).

## Measurements (established)

Detector `_findings_in_source` of `tests/unit/guards/test_privacy_logs_carry_no_plaintext_subject.py` run over every `*.py` of `src/backend/app/` on `16667ac9a` (scratch script, output kept in the session scratchpad):

- 160 findings in 70 files: **45 identifier findings** (account key / e-mail) in 17 files, **113 exception-text** findings (`str(<name>)`), 2 in `scripts/` (outside `app/`).
- Issue said 51 in 18 files; the difference: `console_email_adapter` (3) and `smtp_email_adapter` (2) were repaired by #1786, `pest_image_service`/`reference_image_service`/`plant_diary_service` counts differ by the exception-text half added in #1786's review.
- Side services: `src/inference-service` 6, `src/knowledge-service` 2 findings — **all** `str(<path>)`/`str(exc)` of model files and ingestion errors; **no** account key or e-mail. Not added to the selector (they hold no account identity); recorded.
- IPs in log calls (AST scan, keyword/value names `ip|ip_address|client_ip|remote_addr|client.host`): only `auth_service.py` device-pairing lines 1156/1231/1250/1270.
- nginx (`src/frontend/nginx.conf`, image `nginx-unprivileged`): no `access_log` override → image default `main` format logs `$remote_addr` and `$http_x_forwarded_for` (the client IP behind Traefik), user agent, full request line incl. query string, to stdout.
- uvicorn access log: enabled (no `--no-access-log`), logs `client_addr` + request line incl. query string.
- `email_digest` (`app/common/decoys.py:37`): unkeyed sha256[:16]; read **only** by log calls (grep: auth_service, privacy_service, auth_tasks, console/smtp adapters). No stored value, no lookup → re-keying breaks no lookup; migration need: none (only cross-deploy log correlation breaks).
- The Redis stores `registration_notice_store._digest` / `unknown_account_store._digest` are separate unkeyed sha256 used as Redis keys (TTL-bounded) — not `email_digest`; out of scope, recorded as open question.
- **Refuted claim**: the guard docstring says `app/migrations/` is excluded because "an applied migration's source is frozen (`test_applied_migration_sources_are_frozen`)". That guard pins only `app/migrations/versions/` classes. `seed_auth.py`, `add_platform_admin.py`, `seed_e2e_platform_admin.py`, `framework/tracking.py`, `migrate_nutrient_phase_harvest.py` are seeds / framework code, freely editable. Only `versions/` is frozen (1 finding: `v0051_rename_cec_key.py:323`, inside the class body → allow-list with the frozen reason).
- Worker: `app/tasks/__init__.py` runs no secret check; Celery's `Signal.send` swallows `Exception` from handlers, so a fail-fast must raise `SystemExit` (to be verified by test). Compose `docker-compose.yml` / `docker-compose.release.yml` workers pass neither `DEBUG` nor the salt → need pass-through for parity with the backend.

## Work packages

| id | problem | acceptance | files | specialist | deps |
|---|---|---|---|---|---|
| WP1 | Shared log-privacy helpers + keyed `email_digest` + worker salt fail-fast + IP handling (device-pairing lines, nginx + uvicorn access logs) | red-first tests through production path; keyed digest HMAC(salt, purpose); worker exits without salt when not debug | `app/common/log_privacy.py` (new), `app/common/decoys.py`, `app/tasks/__init__.py`, `app/config/logging.py`, `auth_service.py`, `src/frontend/nginx.conf`, compose files | fullstack-developer | — |
| WP2 | Widen guard selector to all of `app/` (minus frozen `versions/`), fix all 45 identifier + 113 exception-text sites | guard red on the widened selector before the fix, green after; allow-list only with read-and-reasoned entries | guard + 60+ modules | fullstack-developer | WP1 |
| WP3 | NFR-011 / docs: log-pipeline retention requirement + open operator question | NFR-011 section + changelog | `spec/nfr/NFR-011_*.md` | generalist (spec edit) | WP1 |
| WP4 | Reviews: gdpr-data-protection-reviewer, code-security-reviewer, /code-review medium | findings addressed | — | reviewers | WP1-3 |

## Risks

- Other strands (#1769, #1784/#1782) touch privacy/retention code and NFR-011 → merge-update, don't reformat untouched code.
- Changing log keys (`user_key=` → `subject=`) may break dashboards/alerts keyed on them — none found in repo (grep helm/grafana).
