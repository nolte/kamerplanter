"""NFR-016 M-1 — version discovery and strict sequence validation."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from app.migrations import versions as versions_pkg
from app.migrations.framework.discovery import load_migrations, normalize_version, validate_sequence
from app.migrations.framework.report import MigrationDiscoveryError

_VERSIONS_DIR = Path(next(iter(versions_pkg.__path__)))

# Deliberately LOOSER than discovery's own `_MODULE_RE` (#1469). Everything named
# `v*` in the package is meant to be a migration, so an entry the strict pattern
# rejects (`v0049-slug.py`, `v49_slug.py`, `V0049_Slug.py`) has to surface here as
# something discovery skipped in silence, instead of disappearing from both sides
# of the comparison. The glob does not end in `.py` on purpose: discovery drops
# sub-PACKAGES (`if info.ispkg: continue`), so a migration authored as
# `v0049_slug/__init__.py` would be invisible to a `*.py` glob and to discovery
# alike — it is picked up here and then fails `test_discovers_every_version_module`.
_VERSION_ENTRY_GLOB = "v*"
_VERSION_FILENAME_RE = re.compile(r"^v(?P<number>\d{4})_[a-z0-9_]+$")

# The lowest acceptable highest version — a RATCHET, not a pin (#1469).
#
# The expectations below are derived from the `versions/` directory, and a
# derivation cannot see a DELETION of the highest module: the derived set shrinks
# with the directory, `validate_sequence` still sees a gapless 0001..N, and the
# runner never checks that an applied version still has a module. The hand-kept
# list this replaced was the only signal for that class, so it is kept here —
# without being the line every migration PR has to edit, which is what turned two
# parallel migration branches into a guaranteed textual conflict.
#
# Because the sequence is gapless from 0001, `highest >= floor` is *exactly* the
# old list's lower bound: every version up to the floor must still exist. What it
# drops is the upper bound ("and nothing beyond"), which is the half no
# legitimate change could keep. Adding v0049 does not touch this constant. Raise
# it whenever convenient; never lower it without deleting a migration on purpose.
_HIGHEST_VERSION_FLOOR = "0048"


def _version_file_stems() -> list[str]:
    """Every ``v*`` module stem in ``versions/``, ascending.

    A directory contributes its own name, so a migration authored as a package
    counts as present here even though discovery refuses to look inside it.
    """
    return sorted(path.name if path.is_dir() else path.stem for path in _VERSIONS_DIR.glob(_VERSION_ENTRY_GLOB))


def _versions_from_filenames() -> list[str]:
    """The version numbers the *filenames* claim, ascending.

    Skips nothing: a stem that does not parse contributes the stem itself, so the
    comparison it breaks names the offending file.
    """
    numbers: list[str] = []
    for stem in _version_file_stems():
        match = _VERSION_FILENAME_RE.match(stem)
        numbers.append(match.group("number") if match else stem)
    return sorted(numbers)


class TestNormalizeVersion:
    @pytest.mark.parametrize(("value", "expected"), [("1", "0001"), ("0002", "0002"), ("42", "0042")])
    def test_zero_pads(self, value, expected):
        assert normalize_version(value) == expected


class TestVersionFiles:
    """The invariants the hand-kept list used to assert implicitly (#1469).

    These read the directory, not `load_migrations()`, so they hold independently
    of whether discovery decides to look at a given file at all.
    """

    def test_every_version_file_follows_the_naming_rule(self):
        offenders = [stem for stem in _version_file_stems() if not _VERSION_FILENAME_RE.match(stem)]

        assert offenders == [], (
            f"{offenders} do not match vNNNN_<lowercase_slug> — discovery skips such a file "
            "without a word, so its migration would never run"
        )

    def test_filenames_carry_no_duplicate_version(self):
        numbers = _versions_from_filenames()

        assert len(set(numbers)) == len(numbers), f"Duplicate version numbers among version files: {numbers}"

    def test_filenames_form_a_gapless_sequence_from_0001(self):
        numbers = _versions_from_filenames()

        # Asserted on the filenames rather than through load_migrations(), which
        # validates the same rule itself — a test that only re-ran the validator
        # would stay green if the validator were removed.
        assert numbers == [f"{n:04d}" for n in range(1, len(numbers) + 1)]

    def test_declared_version_matches_the_filename(self):
        """A module's ``version`` string must be the number in its filename.

        Nothing else enforces this: discovery captures the filename number and
        then never compares it. A ``v0049_*.py`` declaring ``"0048"`` produces a
        version set that is still gapless, so `validate_sequence` passes and the
        module the operator thinks is v0049 is tracked, skipped and checksummed
        as v0048.
        """
        mismatches: list[str] = []
        for stem in _version_file_stems():
            match = _VERSION_FILENAME_RE.match(stem)
            if match is None:
                continue  # reported by test_every_version_file_follows_the_naming_rule
            module = importlib.import_module(f"{versions_pkg.__name__}.{stem}")

            declared = getattr(getattr(module, "migration", None), "version", None)
            if declared != match.group("number"):
                mismatches.append(f"{stem}.py declares version {declared!r}")

        assert mismatches == []

    def test_highest_version_does_not_fall_below_the_recorded_floor(self):
        """The one thing a derived expectation cannot see: a deleted migration.

        See `_HIGHEST_VERSION_FLOOR`. Adding a migration never touches this;
        only removing one can trip it.
        """
        numbers = _versions_from_filenames()

        assert numbers, "versions/ holds no migration modules at all"
        assert numbers[-1] >= _HIGHEST_VERSION_FLOOR, (
            f"Highest migration is {numbers[-1]}, below the recorded floor {_HIGHEST_VERSION_FLOOR} — "
            "a migration module was removed. Migrations are append-only (M-7); if the removal is "
            "deliberate, say so and lower the floor in the same change."
        )


class TestLoadMigrations:
    def test_discovers_every_version_module(self):
        """Discovery must see exactly the files on disk — no more, no fewer."""
        versions = sorted(m.version for m in load_migrations())

        assert versions == _versions_from_filenames()

    def test_loads_a_contiguous_sequence(self):
        migrations = load_migrations()

        validate_sequence(migrations)
        assert [m.version for m in migrations] == sorted(m.version for m in migrations)

    def test_only_the_baseline_is_reversible(self):
        migrations = load_migrations()

        # Baseline is the only reversible migration.
        assert migrations[0].reversible is True
        assert all(m.reversible is False for m in migrations[1:])


class TestValidateSequence:
    def test_accepts_contiguous(self, make_migration):
        validate_sequence([make_migration("0001"), make_migration("0002"), make_migration("0003")])

    def test_rejects_duplicate(self, make_migration):
        with pytest.raises(MigrationDiscoveryError):
            validate_sequence([make_migration("0001"), make_migration("0001")])

    def test_rejects_gap(self, make_migration):
        with pytest.raises(MigrationDiscoveryError):
            validate_sequence([make_migration("0001"), make_migration("0003")])

    def test_rejects_not_starting_at_one(self, make_migration):
        with pytest.raises(MigrationDiscoveryError):
            validate_sequence([make_migration("0002"), make_migration("0003")])
