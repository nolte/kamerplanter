"""Guards over CI configuration that lives outside the backend package.

These tests assert on files no application code imports — workflow YAML, the ZAP
rule TSVs, the scan hook, `scripts/security/`. They are Python only because pytest
is where this repository keeps its mechanical checks; nothing here exercises the
application.

They live in their own directory because `backend-guards.yml` — the required
`Write-route and tree guards` lane — runs whole DIRECTORIES rather than named
files, for the reason that workflow states at length: a hand-maintained list is an
opt-in list, and a guard added outside the list is silently unenforced. Put a new
guard of this shape here and the required lane picks it up.

Why they are not in `tests/unit/api/`, the lane's other directory: that one holds
the write-route gate sweeps and runs with `KAMERPLANTER_MODE=full` for a reason
specific to route mounting. These read files off disk and care about neither.

Being in the required lane is the point. `backend.yml` is path-filtered and
advisory, so before #1376/#1389 a pull request could add an expired suppression,
drop `-c`'s absence, or remove the nightly's scan budget, turn Backend CI red and
merge anyway.
"""
