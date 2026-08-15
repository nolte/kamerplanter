"""A run entry may not point at a foreign tenant's cultivar (SEC-004, #1112).

``PlantingRunEntry.cultivar_key`` is body-sourced (``EntryCreate`` /
``EntryUpdate``) and was written with nothing checking it. There was no active
disclosure — ``EntryResponse`` echoes only the key the caller supplied, and name
resolution happens on materialised plant instances, which have been guarded since
#1090 C-9 — so the damage today is integrity plus a late 404 at materialisation.
The day anyone attaches a `_cultivar_summary` to an entry, that latency becomes a
leak.

**Why this needed more than the one-line declaration.** ``PlantingRunEntry`` had
no ``tenant_key``: it is tenant-verified through its parent run.
:meth:`BaseArangoRepository._verify_owned_references` compares a reference against
**the row's own** tenant and *skips a row that has none*. Declaring
``_owned_reference_fields`` alone would therefore have produced a guard that looks
implemented, passes review, and never runs — the failure class this repository has
shipped often enough to name. Three pieces are needed together, and each is
falsified separately below:

1. the model carries a ``tenant_key``;
2. the service stamps it from the parent run, on create **and** on update;
3. the sub-repository declares the reference — and the update path, which writes
   to the collection directly and so bypasses the base class's own hook, calls
   the verification explicitly.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.data_access.arango import planting_run_repository as repo_module
from app.data_access.arango.planting_run_repository import _PlantingRunEntryRepository
from app.domain.models.planting_run import PlantingRunEntry


class TestTheGuardHasSomethingToCompareAgainst:
    """Piece 1 — without a tenant on the row the declaration is inert."""

    def test_the_entry_model_carries_a_tenant_key(self) -> None:
        assert "tenant_key" in PlantingRunEntry.model_fields, (
            "PlantingRunEntry lost its tenant_key. _verify_owned_references skips a "
            "row that has none, so the cultivar_key declaration below silently stops "
            "checking anything — the exact inertness #1112 was filed to avoid."
        )

    def test_an_unstamped_entry_would_be_skipped_by_the_guard(self) -> None:
        """The behaviour that makes piece 2 load-bearing rather than tidy.

        This asserts the *base class's* documented rule, not our code: a row with
        an empty tenant is skipped. It is here so the reason the service stamps
        is visible next to the stamping test, instead of being a fact someone has
        to go and re-derive from ``base_repository``.
        """
        source = inspect.getsource(repo_module.BaseArangoRepository._verify_owned_references)

        assert "if not tenant_key:" in source and "return" in source


class TestTheServiceStampsTheParentRunsTenant:
    """Piece 2 — measured on the source, because the DB paths are not unit-testable here."""

    @staticmethod
    def _service_method(name: str) -> ast.FunctionDef:
        from app.domain.services import planting_run_service

        tree = ast.parse(Path(inspect.getsourcefile(planting_run_service)).read_text(encoding="utf-8"))
        return next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)

    @pytest.mark.parametrize("method", ["add_entry", "update_entry"])
    def test_both_write_paths_stamp_the_tenant(self, method: str) -> None:
        """Create *and* update.

        Stamping only on create would leave the row correct and the PATCH path
        unguarded — and PATCH is where a body-supplied ``cultivar_key`` is
        re-pointed, so it is the half that matters most. That asymmetry is
        precisely the #1090 C-9 defect on ``plant_instance``.
        """
        assigns = [
            node
            for node in ast.walk(self._service_method(method))
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Attribute) and t.attr == "tenant_key" for t in node.targets)
        ]

        assert assigns, f"{method} does not stamp tenant_key"
        source = ast.unparse(assigns[0])
        assert "run.tenant_key" in source, (
            f"{method} stamps tenant_key from {source!r} rather than from the parent run. "
            "Any other source — the request body above all — would let a caller "
            "choose which tenant their entry is verified against, which turns the "
            "guard into a formality."
        )

    def test_the_update_path_does_not_trust_the_stored_tenant(self) -> None:
        """A row predating the v0042 backfill carries ``""``.

        If ``update_entry`` merged the stored entry and kept its empty tenant, the
        guard would be skipped on exactly the legacy rows the migration exists to
        repair — and it would be skipped on the *re-point* path. Re-stamping from
        the run on every update is what makes the guard independent of whether the
        backfill has run.
        """
        source = ast.unparse(self._service_method("update_entry"))

        assert "merged.tenant_key = run.tenant_key" in source


class TestTheDeclarationIsOnAClassAndCoversBothWrites:
    """Piece 3 — the declaration, and the update path that bypasses its hook."""

    def test_the_reference_is_declared_as_owned(self) -> None:
        from app.data_access.arango import collections as col

        assert _PlantingRunEntryRepository._owned_reference_fields == {"cultivar_key": col.CULTIVARS}

    def test_the_declaration_lives_on_a_class_not_an_instance(self) -> None:
        """``_owned_reference_fields`` is a ``ClassVar``.

        Setting it on a ``BaseArangoRepository[PlantingRunEntry](...)`` instance
        type-checks and does nothing — which is why the sub-repository is a named
        subclass. ``PropagationEvent`` documented this same trap when it grew the
        same declaration.
        """
        assert "_owned_reference_fields" in vars(_PlantingRunEntryRepository)

    def test_the_run_repository_actually_uses_the_declaring_class(self) -> None:
        """The declaration is worthless on a class nothing instantiates."""
        source = inspect.getsource(repo_module.ArangoPlantingRunRepository.__init__)

        assert "_PlantingRunEntryRepository(" in source

    def test_the_update_path_verifies_explicitly(self) -> None:
        """``update_entry`` writes through the raw collection handle.

        So ``BaseArangoRepository.update`` — and with it the
        ``_verify_references_on_update`` hook — never runs on the live update path.
        Declaring the flag and stopping would have covered ``create_entry`` only,
        while reading as though both writes were covered. The call has to be here,
        and it has to come **before** the write.
        """
        source = inspect.getsource(repo_module.ArangoPlantingRunRepository.update_entry)

        assert "_verify_changed_owned_references" in source, (
            "update_entry no longer verifies the cultivar reference. Its own hook "
            "does not fire (it bypasses BaseArangoRepository.update), so removing "
            "this call leaves the re-point path open with nothing reporting it."
        )
        # Anchored on the *collection write* specifically. A bare ``.update(``
        # matches the prose above it too, and a test that measured the comment
        # rather than the call would happily pass with the order reversed.
        verify_at = source.index("_verify_changed_owned_references")
        write_at = source.index("PLANTING_RUN_ENTRIES).update(")
        assert verify_at < write_at, (
            "the verification runs after the write — a refused reference would already be stored by the time it raises"
        )
