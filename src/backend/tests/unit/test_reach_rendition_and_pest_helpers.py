"""The parsing halves of the #1759 / #1760 reach helpers.

``scripts/reach/observe_rendition_residue.py`` and
``scripts/reach/observe_pest_prototypes.py`` are proven by the real run against
the reach stack; pinned here is what can be checked without it: measured state
to member lines, refusing unreadable answers and keys outside the storage root,
and that an observation never prints nothing. Loaded through a fixture that
asserts the script exists, so a deleted helper turns these red, not skipped.
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
def renditions() -> ModuleType:
    return _load("reach/observe_rendition_residue")


@pytest.fixture(scope="module")
def pest() -> ModuleType:
    return _load("reach/observe_pest_prototypes")


def test_rendition_members_name_deleted_kept_and_partial(renditions):
    counts = {"pest_reference": (0, 3), "diary": (3, 3), "plant": (1, 3)}

    assert renditions.members(counts) == [
        "renditions-kept/diary",
        "renditions-deleted/pest_reference",
        "renditions-partial/plant=1/3",
        "seeded/9",
    ]


def test_present_counts_reads_the_files_under_the_storage_root(renditions, tmp_path):
    (tmp_path / "t" / "x").mkdir(parents=True)
    (tmp_path / "t" / "x" / "a_t128.webp").write_bytes(b"w")
    files = [
        {"category": "diary", "renditions": ["t/x/a_t128.webp", "t/x/a_t512.webp"]},
        {"category": "pest_reference", "renditions": ["t/x/b_t128.webp"]},
    ]

    assert renditions.present_counts(tmp_path, files) == {"diary": (1, 2), "pest_reference": (0, 1)}


def test_a_rendition_key_cannot_leave_the_storage_root(renditions, tmp_path):
    with pytest.raises(renditions.ReachError):
        renditions.present_counts(tmp_path, [{"category": "diary", "renditions": ["../escape.webp"]}])


def test_a_seed_without_renditions_is_refused_not_read_as_deleted(renditions, tmp_path):
    with pytest.raises(renditions.ReachError):
        renditions.present_counts(tmp_path, [{"category": "diary", "storage_key": "t/x/a.jpg"}])


@pytest.mark.parametrize(
    ("state", "first"),
    [
        ((False, 0, True), "erased/pest_embeddings"),
        ((True, 1, True), "residue/pest_embeddings=1"),
        ((False, 2, True), "residue/pest_embeddings=2"),
    ],
)
def test_pest_members_name_the_state(pest, state, first):
    lines = pest.members(state, 2)

    assert lines[0] == first
    assert lines[1:] == ["kept/curated", "seeded/2"]


def test_a_deleted_curated_row_is_reported(pest):
    assert "deleted/curated" in pest.members((False, 0, False), 2)


@pytest.mark.parametrize("line", ["", "t|x|f", "t|1", "yes|1|f"])
def test_pest_parse_state_refuses_an_unreadable_answer(pest, line):
    with pytest.raises(pest.ReachError):
        pest.parse_state(line)


def test_pest_parse_state_reads_the_psql_row(pest):
    assert pest.parse_state("f|0|t\n") == (False, 0, True)


def test_the_pest_seed_takes_keys_as_psql_variables_not_text():
    vectordb = _load("reach/vectordb")
    sql = vectordb.PEST_SEED_SQL
    assert ":'contribution_key'" in sql and ":'contribution_url'" in sql
    assert "'user_contributed'" in sql and "false)" in sql
