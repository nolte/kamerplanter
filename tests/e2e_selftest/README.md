# E2E harness self-tests

Browser-free unit tests for the *logic* inside `tests/e2e/pages/base_page.py` —
branch resolution, the settled-state contract, the loud-failure messages.

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
