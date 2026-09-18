"""v0050's class source is immutable, because ``checksum()`` hashes it (M-7, #1505).

``Migration.checksum()`` is ``sha256(inspect.getsource(type(self)))``
(``framework/base.py``), and the runner compares it against the value stored in
``schema_migrations`` when the migration was applied. Editing the class of a
migration that has already run therefore makes **every** such installation log
``migration_checksum_drift`` on every boot, for good: applied migrations are
immutable and a correction ships as a new version.

This is not hypothetical. The first draft of #1505 extracted a seam from v0050's
class so v0051 could subclass it and override one method — a clean-looking
refactor that would have broken the checksum of an applied migration on every
installation that had run #1507. The shared machinery now lives in
``app/migrations/support/care_profile_recompute.py`` instead, and this test is what
keeps the next such refactor from landing quietly.

Scope, deliberately narrow
==========================

Only v0050 is pinned here, not every version module. Widening the pin to all 51 is
the right shape for the class and is left as a follow-up on purpose: it is a
ratchet that every new migration has to feed, and three open PRs are adding
migrations right now — this PR is not the place to make them all fail. v0050 is
pinned because this PR is the one that was about to edit it.

v0051 is **not** pinned: it has not shipped anywhere yet, and its version number
is still being negotiated with the other open migration PRs.
"""

from __future__ import annotations

import hashlib
import inspect

from app.migrations.versions.v0050_repair_care_profiles_family_and_guide import (
    RepairCareProfilesFamilyAndGuideMigration,
    migration,
)

#: sha256 of ``inspect.getsource(RepairCareProfilesFamilyAndGuideMigration)`` as the
#: class shipped in #1507. Recording a *new* value here is never the fix for a red
#: run — the fix is to put the change in a new migration or in
#: ``app/migrations/support/``.
_V0050_CLASS_CHECKSUM = "892c3c60092029ce0f8736c07a3ab697e5f126ca4c18299e92d5e4e51c83eaf0"


def test_v0050_class_source_has_not_been_edited() -> None:
    source = inspect.getsource(RepairCareProfilesFamilyAndGuideMigration)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert digest == _V0050_CLASS_CHECKSUM, (
        "v0050's class source changed. It has been applied on real installations, so "
        "Migration.checksum() will now report migration_checksum_drift there on every "
        "boot (M-7). Put the change in a new version module, or — if it is machinery a "
        "later migration needs — in app/migrations/support/. Updating the constant in "
        "this test is not the fix."
    )


def test_the_pinned_value_is_the_one_checksum_actually_uses() -> None:
    """The pin has to measure the same expression the runner compares.

    A guard that hashed, say, the module source while the runner hashes the class
    source would be green through exactly the edit it exists to catch.
    """
    assert migration.checksum() == _V0050_CLASS_CHECKSUM
