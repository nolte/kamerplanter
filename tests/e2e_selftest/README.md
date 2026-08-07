# E2E harness self-tests

Browser-free unit tests for the *logic* inside the page-object base layer:

- `tests/e2e/pages/base_page.py` — branch resolution, the settled-state
  contract, the loud-failure messages.
- `tests/e2e/pages/_element_proxy.py` — the re-resolving element reference:
  what it heals, what it must **not** heal, and the budget that bounds it.

They live **outside** `tests/e2e/` on purpose:

- `tests/e2e/` is the browser-driven tier. Everything under it needs a Selenium
  Grid plus the composed application stack, and `pytest --collect-only` from that
  directory is used as a change-surface check ("the suite still collects N
  tests"). Adding browser-free tests there would pollute both.
- These are unit tests by `spec/project/test-pyramid-foundation/` — same tier as
  `src/backend/tests/unit/`, different subject (the test harness itself).

Run them with no stack and no browser:

```bash
task test:e2e:selftest
# or
python -m pytest tests/e2e_selftest
```

The only dependency is `selenium` (for the exception and `By` symbols
`base_page` imports), i.e. `tests/e2e/requirements.txt` minus the grid.

## Where this runs besides your machine

The `e2e-selftest` pre-commit hook runs this tier, and `Static CI Tests` — the
required check — is a pre-commit run, so the tier gates every PR (~17 s). The
hook is filtered to changes under `tests/e2e_selftest/`, `tests/e2e/pages/` and
`tests/e2e/requirements.txt`, and pins `language_version: python3.14`: the page
objects use PEP 758 (unparenthesized multi-type `except`), which is a
`SyntaxError` on 3.13 and older, so an unpinned hook would fail to even import
its subject wherever pre-commit itself runs on an older interpreter.

Until #835 nothing ran these tests but a developer. That mattered most for
`_element_proxy.py`, which reads Selenium internals that are not public API —
a Renovate minor is free to move them, and without a gate the breakage would be
silent.
