"""The seed must report the species it failed to bind (#1006).

``link_indoor_species_to_phase_sequence`` returns early when ``indoor_default`` is not
seeded yet — on a fresh install that is normal, because ``phase_sequences`` is seeded
*after* ``core_data`` in ``seeds/registry.py``. The recovery is real: the
``lifecycle_to_phase_sequence_reconcile`` job is the last data job and calls the linker
again once every species and every sequence exists, so the binding completes inside the
same seed run.

What was missing is the *check that it did*. The early return logged one warning naming
no species, so a run that bound nothing looked exactly like a run that had nothing to
bind — and an unbound species produces plants with ``current_phase_key: null``.

``verify_all_species_bound`` closes that: it runs at the end of the reconcile job, where
"unbound" can no longer be an ordering artefact, names the offenders and reports at
**error** level. Deliberately not fatal — refusing to finish the seed over a master-data
gap would cost the whole install.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.migrations.seed_data import verify_all_species_bound


def _db_returning(names: list[str]) -> MagicMock:
    db = MagicMock()
    db.aql.execute.return_value = iter(names)
    return db


class TestVerifyAllSpeciesBound:
    def test_unbound_species_are_reported_at_error_level_with_names(self) -> None:
        db = _db_returning(["Dracaena reflexa", "Yucca gigantea"])

        with (
            patch("app.migrations.seed_data.get_db", return_value=db),
            patch("app.migrations.seed_data.logger") as log,
        ):
            unbound = verify_all_species_bound()

        assert unbound == ["Dracaena reflexa", "Yucca gigantea"]
        log.error.assert_called_once()
        assert log.error.call_args.args[0] == "species_without_phase_sequence_after_seed"
        assert log.error.call_args.kwargs["count"] == 2
        # Names, not just a count — the log has to answer "which".
        assert "Dracaena reflexa" in log.error.call_args.kwargs["species"]

    def test_a_fully_bound_corpus_reports_success_and_no_error(self) -> None:
        db = _db_returning([])

        with (
            patch("app.migrations.seed_data.get_db", return_value=db),
            patch("app.migrations.seed_data.logger") as log,
        ):
            assert verify_all_species_bound() == []

        log.error.assert_not_called()
        assert log.info.call_args.args[0] == "all_species_bound_to_phase_sequence"

    def test_long_lists_are_truncated_but_the_count_is_not(self) -> None:
        db = _db_returning([f"Species {i:03d}" for i in range(40)])

        with (
            patch("app.migrations.seed_data.get_db", return_value=db),
            patch("app.migrations.seed_data.logger") as log,
        ):
            unbound = verify_all_species_bound(limit=5)

        assert len(unbound) == 40, "the return value is complete even when the log is capped"
        assert len(log.error.call_args.kwargs["species"]) == 5
        assert log.error.call_args.kwargs["count"] == 40
        assert log.error.call_args.kwargs["truncated"] == 35

    def test_the_query_is_parameterised(self) -> None:
        """AQL is bound, never interpolated (BACKEND.md; injection)."""
        db = _db_returning([])

        with patch("app.migrations.seed_data.get_db", return_value=db), patch("app.migrations.seed_data.logger"):
            verify_all_species_bound()

        query = db.aql.execute.call_args.args[0]
        bind_vars = db.aql.execute.call_args.kwargs["bind_vars"]
        assert set(bind_vars) == {"@species_col", "@edge_col", "species_prefix"}
        assert "@@species_col" in query
        assert "@@edge_col" in query


class TestReconcileJobWiring:
    def test_the_reconcile_step_verifies_after_linking(self) -> None:
        """A verification nobody calls is the failure class this fix is about.

        The reconcile job is the registry-final data step; the check belongs at its end,
        after the linker, or it measures an ordering artefact rather than a defect.
        """
        from app.migrations import migrate_lifecycle_to_phase_sequence as module

        source = module.run_migrate_lifecycle_to_phase_sequence.__code__.co_names
        assert "link_indoor_species_to_phase_sequence" in source
        assert "verify_all_species_bound" in source
