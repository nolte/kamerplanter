"""Every shipped migration's class source is immutable, because ``checksum()`` hashes it.

NFR-016 M-7 / ADR-005 §4, issue #1536. Widened from the single-version pin
``tests/unit/migrations/versions/test_v0050_source_is_frozen.py`` (#1524), which this
module replaces — the same statement is not made twice.

WHY THE PIN EXISTS
==================

``Migration.checksum()`` is ``sha256(inspect.getsource(type(self)))``
(``app/migrations/framework/base.py``), and ``MigrationRunner._warn_checksum_drift``
compares it against the value ``schema_migrations`` stored when the migration was
applied. Editing the class of a migration that has already run therefore makes every
such installation log ``migration_checksum_drift`` on every boot, for good, and that
log line is indistinguishable from a real tamper. Applied migrations are immutable;
a correction ships as a new version module, and machinery a later migration needs
belongs in ``app/migrations/support/`` — never in the class body of a shipped one.

The runner only warns, by design: it cannot refuse to boot a customer's installation
over a refactor. This module is the half that *can* refuse — it goes red in the
required, unfiltered ``Write-route and tree guards`` lane at the moment the edit is
proposed, which is the only moment anyone can still put it somewhere else.

IT HAS ALREADY CAUGHT TWO
=========================

Not hypothetically. #1505's first draft extracted a seam from v0050's class so v0053
could subclass it — a clean-looking refactor that would have broken the checksum on
every installation that had run #1507; the shared machinery lives in
``app/migrations/support/care_profile_recompute.py`` instead. And #1521 (#1506) then
edited v0050's class on ``develop`` anyway: the ``_PRESERVED_FIELDS`` literal became
the shared ``SEASON_STATE_FIELDS`` and the docstring was rewritten. That edit is
behaviour-preserving — the parity suite in ``tests/unit/migrations/support/`` still
matches the support module against v0050 field for field — but the checksum is not:
``892c3c60…`` (as #1507 shipped it) became ``b70783de…``. Installations that applied
v0050 report drift for it from ``c5c5438a9`` onwards. That drift is **accepted as
known** (#1536): no migration re-stamps a stored checksum, and the pin below records
``develop``'s value, not the one v0.4.1 shipped. This module exists so there is no
third one.

WHERE THE "SHIPPED" BOUNDARY IS DRAWN, AND HOW IT IS MEASURED
=============================================================

``_PINNED_THROUGH`` is the highest version that has reached an installation. Two
candidate measurements, taken on 2026-09-19:

* by release tag — ``git ls-tree --name-only v0.4.1 app/migrations/versions/`` tops
  out at ``v0050``;
* by ``develop`` — ``versions/`` holds ``v0001`` … ``v0054``, and the cluster runs
  the ``:latest`` images built from ``develop``, so an installation tracking it has
  applied all 54.

The second is used: **merged to ``develop`` is shipped.** Its version SET contains
the tag's — every version v0.4.1 shipped is also on ``develop`` — so no version the
tag measurement would pin is left unpinned. That containment is about versions only,
and one pin makes the difference visible (SCR-009): v0050's row records ``develop``'s
value, **not** the one v0.4.1 shipped. It cannot record both, the drift between them
is the accepted one recorded in ``runner._warn_checksum_drift``, and pinning the
shipped value would mean this guard demanded a source nobody has. ``_PINNED_THROUGH``
is therefore the highest version present when this guard landed.

A NEW MIGRATION FEEDS NOTHING
=============================

A migration authored after this commit takes the next free number, which is *above*
``_PINNED_THROUGH``, and the rules below leave it alone: unpinned is the correct and
required state for it. No migration pull request edits this file, so two migration
branches open at once cannot conflict in it — the same reason
``test_discovery._HIGHEST_VERSION_FLOOR`` is a floor and not a list (#1469).

Raising ``_PINNED_THROUGH`` (plus ``_PINNED_COUNT_FLOOR`` and the new rows) is a
separate, deliberate act, best paid at release time: it is a one-line-per-version
change to one file that no feature branch touches. Until it is paid, the versions
above the boundary carry the runner's warning and nothing more — the window is
deliberate, and it is the price of the ratchet never blocking a migration.

WHAT THIS PIN DOES *NOT* SEE
============================

Exactly what ``Migration.checksum()`` does not see: a shipped migration whose
behaviour changes because a module it *imports* changed (``app/migrations/support/``,
``app/data_access/``). The stored checksum is over the class source alone, so a pin
over anything wider would report drift the runner never reports — and a pin over
anything narrower (the module source, ``up`` alone) would be green through exactly
the edit it exists to catch. Behaviour drift through shared helpers is the parity
suite's job (``tests/unit/migrations/support/``), not this module's.
"""

from __future__ import annotations

import hashlib
import inspect
import re
import sys
from pathlib import Path

from arango.database import StandardDatabase

from app.migrations import versions as versions_pkg
from app.migrations.framework.base import Migration
from app.migrations.framework.discovery import load_migrations
from app.migrations.framework.report import MigrationReport

_VERSIONS_DIR = Path(next(iter(versions_pkg.__path__)))

# Same LOOSE glob as `tests/unit/migrations/framework/test_discovery.py` and for the
# same reason (#1469): everything named like a version entry in the package is meant
# to be a migration, and an entry the strict pattern rejects — or a migration
# authored as a sub-PACKAGE, which `load_migrations` skips outright — has to surface
# as an offender here instead of vanishing from both sides of the comparison.
#
# The character class is this module's own, not test_discovery's `v*`: that glob is
# case-sensitive, so `V0049_Slug.py` is invisible to it. Named rather than silently
# widened, because test_discovery still carries the narrow form.
_VERSION_ENTRY_GLOB = "[vV]*"
_VERSION_FILENAME_RE = re.compile(r"^v(?P<number>\d{4})_[a-z0-9_]+$")

#: The highest version that had reached an installation when this guard landed.
#: See the module docstring for how the boundary is measured. Raise it (together
#: with the rows and the count floor) when a release is cut; never lower it.
#:
#: NOTHING MEASURES THAT IT KEEPS UP — #1562, deliberately out of scope here. Every
#: expectation below is derived FROM this constant, so a boundary left behind a
#: release is green: the versions above it count as "new", stay unpinned, and can be
#: edited years later without a red run — the #1521 → #1536 sequence one number
#: higher. #1562 proposes measuring it against the highest version in the most recent
#: release tag, which the lane can read (`fetch-depth: 0`, as
#: `test_model_field_renames_have_migrations.py` already does).
_PINNED_THROUGH = "0054"

#: A RATCHET over the size of the table below, independent of `_PINNED_THROUGH`.
#: Set equality against the directory (`test_pins_cover_exactly_the_shipped_versions`)
#: is satisfied by *lowering* `_PINNED_THROUGH` and deleting the rows above it — the
#: pin table can shrink to a single row, or to none, and every derived expectation
#: shrinks with it. This floor is the one statement that does not: it can only ever
#: be raised. 54 = the number of version modules on `develop` on 2026-09-19.
_PINNED_COUNT_FLOOR = 54

#: ``sha256(inspect.getsource(<migration class>))`` per shipped version — the exact
#: expression ``Migration.checksum()`` computes and the runner compares.
#:
#: Recording a *new* value for an existing row is never the fix for a red run. The
#: fix is to put the change in a new version module, or — if it is machinery a later
#: migration needs — in ``app/migrations/support/``. The one row that was ever
#: rewritten is v0050's, and the module docstring spends a section on why.
_PINNED_CLASS_CHECKSUMS: dict[str, str] = {
    "0001": "2b189f8d8b2560c23caf8ee21933f0fd57461174ef7f65120b1f26053ee9bda3",
    "0002": "70860f5becac9764cc57fad91816f39626197da3b1270fbeb88f2664aa8ea0fa",
    "0003": "e6a836a54e77b8577ea4c41d9cf95726856718c58220f57ef70ec4738977862e",
    "0004": "a1567e5e77ee1aca8395cfa265b24da1d19238a87b6c74005ef1633cdf15a729",
    "0005": "34105d74a41f621cead201efa475c9ae11fb46e7f7c15d8b997b11f839f3aade",
    "0006": "9fad6963f790bb42c9db48655d15b2079b9cb4a060cc627380144ac2e3268cf1",
    "0007": "7216736cdcd583a3577c0c5a4523257aac674f858619984606e80766fecc369b",
    "0008": "5532f13a22d19767462b44fa4d21b28fd2b2b2b8c8fa9275c79a2c66877370ea",
    "0009": "d1c6ae4efad29ebe440339017923bdea6d7a4b0a5d6050e53366125b18b829bc",
    "0010": "f08dea82d9de3a5df5bc2b50007d47ae30f1ad78aa37f1cc0f17625f18fecf89",
    "0011": "e971122b498b7aa05d3b0c81c0e25de5fe33b52ed21d29f1e306a3ee6e32570e",
    "0012": "7ae8ea40ef61b6004bd5c05227bcd3f6158069fe8a93f63d2028241fe42b342e",
    "0013": "5555890b1a2814a2db6424a3e2057315e6be59ecff0ae4fe33bda22678a84473",
    "0014": "081ef0e15d08546f00214733f728c56ccef6e38b0628baba66ed60a87e05b7e4",
    "0015": "c7dbbe052830a6139b81ee6db86c6c140cfaa7fd2f7bd4022b183c4aab4b712f",
    "0016": "e2d4cc69f5c50e7e7a8b1967f3dbeb89a5205fb25b1c733314c3d9175b1cb0a8",
    "0017": "4779a95f7bcced0e7ddd0b8d1c5a880a6670930cd16af23b3763f167da728523",
    "0018": "083754ef60ac184c03b3b8fbfb35ad2d7f9e18fb0405f32418f2133b54545795",
    "0019": "c0942b149893743b70e77c39b115e81ed062da5d175c4e41f583be92e5de6c88",
    "0020": "9d2e76f84ad6fe5d49b9ea339fc4e7d4fd2754e9945802005573661c0b5642b3",
    "0021": "025158a6af5d2933b292e859a1da8308ed610b6dec005642bbba7edac2c0981d",
    "0022": "dc8dc16bb3a96fec3bdd5b112ee7d80aaf73498f85f9aa301c634601392f02d9",
    "0023": "e1dec43c5cf834f06351defa319bf256860369ae982b70870acfd7c410b7c3bb",
    "0024": "5333c410a5a147da729d1d33732e4b9bc4bb61bff87e12d28ee3770f1b3b4dc5",
    "0025": "abb226eb05893dded7f02c5a24a80b9763a8dbb52acad735739a5e8368717700",
    "0026": "7d85bbd7882b78cf89342e223de5d3bafc1bd56fed93888febeb6ef7e341bfe9",
    "0027": "d6ae7f62b1d9a4926c270b1100a82e7168beadec7699e132427a1ce7c034e518",
    "0028": "f8e0e214c17c2a3ce0067aeae1eef7fd7910fb502ba16a563338b610eccaab3c",
    "0029": "c52faeb717e2f0809563f048e9ae1569e562d7e3c1b4b9b10dd98028bd3590b7",
    "0030": "de210445cb896bbb6013696e94d20b89aeb0a5a3b99ae071babb45d57d554476",
    "0031": "36a6fc85195e96abf77c5474ec04fa788e1282c5ebc9b4e5a3515a0b3da5c1bd",
    "0032": "b990652829d0c698a66c358b9ac1a6b6756137491058ed4d839495ce9d1674ae",
    "0033": "2ba273d6f76c228ed968c3b73d901277b38229438690c2789f920b01dc996b76",
    "0034": "ed2f29671e5cd2fb7bd8896c1dce86c124e9de74ea7707e81fd5aab94d2b4c52",
    "0035": "f6a8b8b86ba2674cb3cb31f7245cd20e242e8629220dea4d684d8940813cdd86",
    "0036": "bbfc21f80223ede7e08b95d7a9930776c5021b41e04acaf00e55a7c65e390f03",
    "0037": "afa60e96d94646183e6e6a6ff7261bc6dfb59541b5f5a041961665d792bceafa",
    "0038": "6f08303cfb01f13176c3ff5f15d6a303f1f269d79e4798fcc396a72f1f435780",
    "0039": "c22fc3ac7adfd41603d298425ff26a16aec914280091035ffbd5faaadd8b617c",
    "0040": "a9d17aac489110aa2a5d5fabfe9f41bd2cf1b0f19a220e9b88f2f09f87b83442",
    "0041": "b1bdb35112fd489b7395c905f9745fd8773ac672ebf4b8a047cc1d9e1e929adc",
    "0042": "113cc02491c7e67da498f74f9ffe8450a736d7a6b0b055373550b604b8928d4b",
    "0043": "10cd52c99dfc701c778dea80838fef65b2fc516a6d92d151a684f3f1413e45ef",
    "0044": "60251de9c120f43835ed514dfdafda2aa601463c5f25baeed20b15585ec844d0",
    "0045": "96ea077ebc195cb1eaa4959ec203bbb86fe0f7ecaf64e65b02f32f5938b12b4a",
    "0046": "4e1cc3febd8208a020a3ce95631aac3b629e7be2aa71d5d76f29b714aee046d2",
    "0047": "3aa01651cf6e8d7ce9bc7ee1e167837b89e747286459f81e5db294f269ee3a7f",
    "0048": "75545a0c18cd64d77dd75f58ea087fe0e34b1b4f8e9f08c9e09f03f5e27eea15",
    "0049": "e7ff2779e93a831c30860bf197747c97a19189a53269cfd9d2c1f6e9d39b9547",
    # v0050's pin has been rewritten once, by #1524, after #1521 edited the class on
    # `develop`. See the module docstring — that rewrite is the reason this file
    # covers all 54 versions instead of one.
    "0050": "b70783de9d802ce60bad38c9c29bf4599f0d8a0ad3c52e97524200d0887a39ed",
    "0051": "c1c1334c0b8dd45f1faa162eeeb06478e470741b8c88b5888d8148073706f20b",
    "0052": "19d07b7e823278b6548d6a8a121e189a6c1018a4a4999481fc2021b73419035f",
    "0053": "38a0d78661da3e0e3b1ff20aef388539c466f44752af784b7b5ff1847d8c975d",
    "0054": "cd346e49926930705b8a102c034776a6620edeae93a954e1e15791c416669dad",
}


def _version_entries() -> list[str]:
    """Every version-shaped entry stem in ``versions/``, ascending — files and directories."""
    return sorted(path.name if path.is_dir() else path.stem for path in _VERSIONS_DIR.glob(_VERSION_ENTRY_GLOB))


def _classify_entries() -> tuple[list[str], list[str]]:
    """Split ``versions/`` into (version numbers, offending stems), each ascending.

    A stem the filename pattern rejects gets its **own** bucket rather than standing
    in for a version number, and this is the correction #1552's review forced (SCR-003).
    The earlier shape let a non-parsing stem represent itself among the numbers, on
    the theory that a comparison it breaks would then name the offending file. It
    breaks no comparison: every stem here starts with ``v`` or ``V``, and
    ``"v49_slug" > "0054"`` is true for any four-digit boundary (0x76 > 0x30), so a
    non-parsing entry sorted silently into "newer than the boundary" — the bucket
    that means "correctly unpinned". Exactly the entry the loose glob exists to
    surface was the one it swallowed.
    """
    numbers: list[str] = []
    offenders: list[str] = []
    for stem in _version_entries():
        match = _VERSION_FILENAME_RE.match(stem)
        if match is None:
            offenders.append(stem)
        else:
            numbers.append(match.group("number"))
    return sorted(numbers), sorted(offenders)


def _versions_on_disk() -> list[str]:
    """The version numbers the filenames claim, ascending — offenders excluded."""
    numbers, _ = _classify_entries()
    return numbers


class _ProbeMigration(Migration):
    """A throwaway migration used to pin what ``checksum()`` hashes. Never discovered.

    It lives outside ``app/migrations/versions/``, so ``load_migrations`` never sees
    it and it takes part in no sequence.
    """

    version = "9998"
    name = "probe_for_the_checksum_expression"
    description = "not a real migration"
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        return MigrationReport(version=self.version, name=self.name, changed=0, noop=True, dry_run=dry_run)


class _OtherProbeMigration(Migration):
    """A second throwaway with a DIFFERENT class body, in the SAME module as the first."""

    version = "9999"
    name = "second_probe_for_the_checksum_expression"
    description = "not a real migration either, and deliberately worded differently"
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        return MigrationReport(version=self.version, name=self.name, changed=1, noop=False, dry_run=dry_run)


class TestChecksumHashesTheClassSource:
    """What ``checksum()`` hashes, pinned independently of any version (SCR-002, #1552).

    The 54 pins above are compared through ``migration.checksum()`` on purpose — a
    re-derived comparison would be green through exactly the edit it guards. That
    leaves a second question unasked, and until #1552 the deleted
    ``test_v0050_source_is_frozen.py`` was the only place in the repository that
    asked it: *what expression is that?* Nothing else pins it —
    ``framework/test_tracking.py`` and ``framework/conftest.py`` pass a
    ``checksum_override``, ``framework/test_runner.py`` drives a fake.

    Without this class, changing ``Migration.checksum()`` to hash the MODULE source
    (or ``up`` alone) and regenerating all 54 pins in the same pull request is green
    here — while every installation reports drift for every applied migration from
    the next boot, which is the largest possible form of the damage this module
    exists to prevent.
    """

    def test_checksum_is_the_sha256_of_the_class_source(self) -> None:
        expected = hashlib.sha256(inspect.getsource(_ProbeMigration).encode("utf-8")).hexdigest()

        assert _ProbeMigration().checksum() == expected, (
            "Migration.checksum() no longer returns sha256(inspect.getsource(type(self))). "
            "The stored values in schema_migrations were computed with the old expression, so "
            "every installation will report migration_checksum_drift for every applied "
            "migration from the next boot. Regenerating the pins above does not undo that."
        )

    def test_it_is_not_the_module_source(self) -> None:
        """The falsifier for the most plausible substitution.

        ``inspect.getsource(module)`` is a one-word edit away from
        ``inspect.getsource(type(self))`` and would still hash "the migration".
        """
        module_source = inspect.getsource(sys.modules[__name__])
        module_digest = hashlib.sha256(module_source.encode("utf-8")).hexdigest()

        assert _ProbeMigration().checksum() != module_digest

    def test_two_classes_in_one_module_hash_differently(self) -> None:
        """Per-class, not per-module — otherwise the pins would not be per-version.

        Both probes are defined in this file. A checksum over anything the two share
        (the module, the file path, the base class) returns one value for both.
        """
        assert _ProbeMigration().checksum() != _OtherProbeMigration().checksum()


class TestShippedSourcesAreFrozen:
    def test_every_pinned_migration_still_hashes_to_its_pin(self) -> None:
        """The assertion is over ``migration.checksum()`` itself, not a re-derivation.

        A guard that re-implemented the hash — over the module source, say, or over
        ``up`` alone — would be green through exactly the edit it exists to catch, so
        it calls the same method ``_warn_checksum_drift`` calls.
        """
        drifted: list[str] = []
        for migration in load_migrations():
            pinned = _PINNED_CLASS_CHECKSUMS.get(migration.version)
            if pinned is None:
                continue
            current = migration.checksum()
            if current != pinned:
                drifted.append(f"v{migration.version} ({migration.name}): pinned {pinned}, now {current}")

        assert drifted == [], (
            "The class source of an already-shipped migration changed: "
            + "; ".join(drifted)
            + ". Migration.checksum() will report migration_checksum_drift for it on every "
            "boot of every installation that applied it, for good (NFR-016 M-7). Put the "
            "change in a new version module, or — if it is machinery a later migration "
            "needs — in app/migrations/support/. Rewriting the pin in this file is not the fix."
        )

    def test_pins_cover_exactly_the_shipped_versions(self) -> None:
        """Every version up to the boundary is pinned, and nothing above it is.

        Both halves matter. A missing row is a shipped migration left unguarded; a row
        *above* the boundary claims a version has shipped when it has not, which would
        make the next migration branch edit this file — the friction the boundary
        exists to avoid.

        The two sides are keyed differently and the bridge is worth naming (SCR-005):
        the expectation comes from FILENAMES, the pin rows are matched against
        ``migration.version`` in the checksum loop. What keeps the two from diverging
        inside this lane is ``validate_sequence``, which ``load_migrations`` runs on
        every call — a module whose declared version disagreed with its filename would
        duplicate another version or open a gap and raise there, in
        ``test_discovery_sees_every_pinned_version`` below. The stricter
        filename-declares-its-version check exists in ``test_discovery.py`` but runs in
        the advisory lane only.
        """
        on_disk = set(_versions_on_disk())
        expected = {version for version in on_disk if version <= _PINNED_THROUGH}
        pinned = set(_PINNED_CLASS_CHECKSUMS)

        assert pinned == expected, (
            f"Pin table out of step with versions/ at boundary {_PINNED_THROUGH}. "
            f"Shipped but unpinned: {sorted(expected - pinned)}. "
            f"Pinned but not on disk at or below the boundary: {sorted(pinned - expected)}."
        )

    def test_the_pin_table_cannot_shrink_to_nothing(self) -> None:
        """The one statement no derivation makes (NFR-018 §1).

        Every expectation above is derived from ``versions/`` and from
        ``_PINNED_THROUGH``, so lowering the boundary and deleting the rows above it
        leaves all of them green over a table of one row — or of none, which is a
        guard reporting green while measuring nothing.
        """
        assert _PINNED_CLASS_CHECKSUMS, "the pin table is empty — this guard would measure nothing"
        assert len(_PINNED_CLASS_CHECKSUMS) >= _PINNED_COUNT_FLOOR, (
            f"The pin table holds {len(_PINNED_CLASS_CHECKSUMS)} rows, below the recorded floor "
            f"{_PINNED_COUNT_FLOOR}. Pins are append-only: a shipped migration does not stop "
            "having shipped. If a version module was deleted on purpose, say so and lower the "
            "floor in the same change."
        )

        # The same floor on the other side of the comparison, so the table's size is
        # tied to the *directory's* and not only to itself. Set equality above already
        # goes red on a deleted module (its pin outlives the file), but it is derived
        # from `_PINNED_THROUGH`; this is not.
        on_disk = _versions_on_disk()
        assert len(on_disk) >= _PINNED_COUNT_FLOOR, (
            f"versions/ holds {len(on_disk)} version modules, below the recorded floor "
            f"{_PINNED_COUNT_FLOOR} — a migration module was removed. Migrations are append-only."
        )

    def test_every_version_entry_carries_a_parsable_version_number(self) -> None:
        """An entry that does not parse is an offender, not a version above the boundary.

        Without its own bucket the entry is worse than unguarded, it is *silently*
        unguardable: every stem the loose glob returns starts with ``v`` or ``V``, and
        ``"v49_slug" > "0054"`` holds for any four-digit boundary, so a non-parsing
        stem compares as "newer" — the bucket that means "correctly unpinned". The
        strict half exists in ``test_discovery.py`` (``test_every_version_file_follows_the_naming_rule``)
        and runs only in the path-filtered, advisory lane, which is precisely the gap
        this module was added to close, so it is measured here too.

        ``load_migrations`` walks past both shapes an offender can take — a stem the
        pattern rejects (``v0049-slug.py``, ``v49_slug.py``, ``V0049_Slug.py``) and a
        migration authored as a sub-package — so neither would ever reach the checksum
        loop to be missed there.
        """
        _, offenders = _classify_entries()

        assert offenders == [], (
            f"versions/ holds entries that are not named vNNNN_lower_snake: {offenders}. "
            "Discovery walks past them, so they are neither applied nor pinnable — and they "
            "sort as 'newer than the pin boundary', which reads as 'correctly unpinned'."
        )

    def test_discovery_sees_every_pinned_version(self) -> None:
        """A pin over a module the runner never loads would protect nothing.

        ``load_migrations`` is what the runner walks; the checksum assertion above is
        a loop over it, so a version that dropped out of discovery would make that
        loop skip it in silence rather than fail.
        """
        discovered = {migration.version for migration in load_migrations()}

        assert set(_PINNED_CLASS_CHECKSUMS) <= discovered, (
            f"Pinned versions that discovery does not load: {sorted(set(_PINNED_CLASS_CHECKSUMS) - discovered)}"
        )
