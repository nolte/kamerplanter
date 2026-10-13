"""The parsing halves of the #1771 orphan-sweep reach helpers.

``scripts/reach/observe_orphan_pest_prototypes.py`` and the
``seed-pest-orphans`` command of ``scripts/reach/vectordb.py`` are proven by the
real run against the reach stack; pinned here is what can be checked without
it: measured state to member lines, refusing unreadable answers, the shape of
the seeded rows, and that an observation never prints nothing. Loaded through a
fixture that asserts the script exists, so a deleted helper turns these red,
not skipped.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

REPO_ROOT = find_repo_root(Path(__file__).resolve())


def _load(stem: str) -> ModuleType:
    assert REPO_ROOT is not None, "checkout root not found"
    path = REPO_ROOT / "scripts" / f"{stem}.py"
    assert path.is_file(), f"{path} is missing"
    return load_repo_script(stem)


@pytest.fixture(scope="module")
def observe() -> ModuleType:
    return _load("reach/observe_orphan_pest_prototypes")


@pytest.fixture(scope="module")
def vectordb() -> ModuleType:
    return _load("reach/vectordb")


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ((0, True, True), ["erased/orphans", "kept/live", "kept/curated", "seeded/6"]),
        ((3, True, True), ["residue/orphans=3", "kept/live", "kept/curated", "seeded/6"]),
        ((0, False, False), ["erased/orphans", "deleted/live", "deleted/curated", "seeded/6"]),
    ],
)
def test_members_name_the_measured_state(observe, state, expected):
    assert observe.members(state, 6) == expected


@pytest.mark.parametrize("line", ["", "0|t", "x|t|t", "0|yes|t", "-1|t|f"])
def test_parse_state_refuses_an_unreadable_answer(observe, line):
    with pytest.raises(observe.ReachError):
        observe.parse_state(line)


def test_parse_state_reads_the_psql_row(observe):
    assert observe.parse_state("2|t|f\n") == (2, True, False)


def test_the_seed_writes_orphans_across_tenants_states_and_labels(vectordb):
    rows = vectordb.orphan_rows("tok", "t-subject", "live-key")

    orphans = [r for r in rows if r["role"] == "orphan"]
    (live,) = [r for r in rows if r["role"] == "live"]
    assert live == {
        "role": "live",
        "label": "spider_mite",
        "contribution_key": "live-key",
        "tenant_key": "t-subject",
        "active": "true",
    }
    assert {r["active"] for r in orphans} == {"true", "false"}
    assert {r["tenant_key"] for r in orphans} == {"t-subject", "reach-other-tenant-tok"}
    by_key: dict[str, set[str]] = {}
    for row in orphans:
        by_key.setdefault(row["contribution_key"], set()).add(row["label"])
    assert len(by_key) == 3
    assert max(len(labels) for labels in by_key.values()) == 2
    assert "live-key" not in by_key


def test_the_seed_takes_keys_as_psql_variables_not_text(vectordb):
    for sql in (vectordb.PEST_ORPHAN_ROW_SQL, vectordb.PEST_ORPHAN_CURATED_SQL):
        assert ":'contribution_key'" in sql
    assert "'user_contributed'" in vectordb.PEST_ORPHAN_ROW_SQL
    assert "'gbif'" in vectordb.PEST_ORPHAN_CURATED_SQL
