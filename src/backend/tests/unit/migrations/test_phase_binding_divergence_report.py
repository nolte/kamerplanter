"""The seed reports bindings that no longer match the resolver (#1146).

`verify_all_species_bound` checks **presence**. A species bound to the *wrong*
sequence passes it — `Yucca gigantea` did, while sitting on the 126-day annual
`indoor_default` cycle that `phase_sequence_resolver`'s own docstring names as the
thing #949 fixed. Fixed in the classifier, not in the data.

The gap is structural, not an oversight. Both binding paths are skip-if-bound —
the seed linker's `if existing: continue` and `bind_default`'s
`if get_sequence_by_species(...) is not None: return None` — and idempotency is
the right property for both. What was missing is anything *else*: the only
re-homing mechanism is a hand-enumerated migration, so every resolver improvement
reaches new species and leaves existing ones behind, monotonically, with nothing
reporting it. (This session added v0039, which is one more instance of exactly
that pattern.)

These tests cover the report, not a repair. Re-homing changes plant-visible
lifecycle state and belongs in a versioned migration with a dry-run; what the
report gives that migration is its work-list, and what it gives an operator is the
divergence on the next boot.

The `manual` case matters most and is the one with no live data behind it:
overrides are not writable yet (#1099 measured both candidate endpoints silently
dropping the field), so the exclusion is written *before* it can be exercised in
production — precisely so a future repair pass cannot revert a user's choice.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.phase_sequence_repository import BOUND_BY_MANUAL, BOUND_BY_SEED
from app.migrations import seed_data


class _Aql:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return list(self._rows)


class _Db:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.aql = _Aql(rows)


class _LifecycleRepo:
    def __init__(self, lifecycles: dict[str, Any] | None = None) -> None:
        self._lifecycles = lifecycles or {}

    def get_lifecycle_by_species(self, species_key: str) -> Any:
        return self._lifecycles.get(species_key)


def _lifecycle(cycle_type: str = "perennial", **extra: Any) -> SimpleNamespace:
    return SimpleNamespace(
        cycle_type=cycle_type,
        cultivation_cycle_type=None,
        grown_as_annual=False,
        flowering_strategy=extra.get("flowering_strategy", "polycarpic"),
        photoperiod_type=extra.get("photoperiod_type", "day_neutral"),
    )


def _row(**overrides: Any) -> dict[str, Any]:
    """A joined species+edge+sequence row as the AQL returns it."""
    row = {
        "species_key": "sp1",
        "scientific_name": "Yucca gigantea",
        "photosynthesis_type": None,
        "growth_habit": "tree",
        "bound_to": "indoor_default",
        "bound_by": BOUND_BY_SEED,
    }
    row.update(overrides)
    return row


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch):
    """Wire the module's two data accessors; returns a setter for the scenario."""

    def _apply(rows: list[dict[str, Any]], lifecycles: dict[str, Any] | None = None) -> None:
        monkeypatch.setattr(seed_data, "get_db", lambda: _Db(rows))
        monkeypatch.setattr(seed_data, "get_lifecycle_repo", lambda: _LifecycleRepo(lifecycles))

    return _apply


def test_the_yucca_case_is_reported(wired) -> None:
    """The measured instance: a polycarpic perennial tree on the annual blanket.

    The resolver reaches rule 5 (`any remaining perennial →
    evergreen_foliage_perennial`) on these attributes — not even the step-7 safety
    fallback, the ordinary perennial rule. The stored edge says `indoor_default`.
    """
    wired([_row()], {"sp1": _lifecycle()})

    diverging = seed_data.report_binding_divergence()

    assert diverging == [
        {
            "scientific_name": "Yucca gigantea",
            "bound_to": "indoor_default",
            "resolver_says": "evergreen_foliage_perennial",
        }
    ]


def test_a_binding_that_matches_is_not_reported(wired) -> None:
    """The half that keeps this from being a report that always fires."""
    wired([_row(bound_to="evergreen_foliage_perennial")], {"sp1": _lifecycle()})

    assert seed_data.report_binding_divergence() == []


def test_a_manual_override_is_never_reported_as_drift(wired) -> None:
    """An override is a decision, not a defect — even when it disagrees.

    Written before overrides are writable (#1099), on purpose: the moment they
    become writable, a repair pass with no provenance would start reverting
    deliberate choices, and nothing would warn it.
    """
    wired([_row(bound_by=BOUND_BY_MANUAL)], {"sp1": _lifecycle()})

    assert seed_data.report_binding_divergence() == []


def test_an_annual_on_the_blanket_is_not_reported(wired) -> None:
    """The `None`-means-blanket translation, which is easy to get wrong.

    `resolve_phase_sequence_name` returns `None` for a known determinate cycle, and
    both binding paths translate that to `indoor_default`. Comparing the raw `None`
    against the stored name would report *every annual in the catalogue* as
    diverging — a report nobody could act on, and the fastest way to make this
    check ignored.
    """
    wired(
        [_row(scientific_name="Cannabis sativa", growth_habit="herb", bound_to="indoor_default")],
        {"sp1": _lifecycle(cycle_type="annual", photoperiod_type="short_day")},
    )

    assert seed_data.report_binding_divergence() == []


def test_a_species_without_a_lifecycle_is_handled(wired) -> None:
    """No `LifecycleConfig` is absence of an answer, and step 7 gives it the safe cycle.

    The species must still be comparable — a crash here would take out the report
    for the whole catalogue over one incomplete record.
    """
    wired([_row(bound_to="indoor_default")], {})

    diverging = seed_data.report_binding_divergence()

    assert [d["resolver_says"] for d in diverging] == ["evergreen_foliage_perennial"]


def test_the_report_is_sorted_and_capped_but_returns_everything(wired) -> None:
    """The log is capped; the return value is not.

    A caller (the repair migration's work-list) needs all of them; a log line needs
    to stay readable. Conflating the two would either truncate the work-list or
    dump the catalogue into the boot log.
    """
    rows = [
        _row(species_key=f"sp{i}", scientific_name=f"Species {i:02d}", bound_to="indoor_default") for i in range(30)
    ]
    wired(rows, {f"sp{i}": _lifecycle() for i in range(30)})

    diverging = seed_data.report_binding_divergence(limit=5)

    assert len(diverging) == 30
    assert [d["scientific_name"] for d in diverging] == sorted(d["scientific_name"] for d in diverging)


def test_an_empty_catalogue_reports_nothing(wired) -> None:
    wired([])

    assert seed_data.report_binding_divergence() == []


# ── provenance is actually written ───────────────────────────────────────────


def test_the_repository_stamps_who_bound_it() -> None:
    """A report that keys on `bound_by` is inert if nobody writes it.

    Asserted at the repository, because that is the one place all three binding
    paths funnel through — and because a provenance field nobody sets would make
    the `manual` exclusion above pass for the wrong reason forever.
    """
    from app.data_access.arango.phase_sequence_repository import ArangoPhaseSequenceRepository

    recorded: dict[str, Any] = {}

    class _Repo(ArangoPhaseSequenceRepository):
        def __init__(self) -> None:  # no database
            pass

        def get_sequence_by_species(self, species_key: str):
            return None

        def delete_edges(self, *args: Any, **kwargs: Any) -> None:
            pass

        def create_edge(self, collection: str, from_id: str, to_id: str, data: Any = None) -> None:
            recorded.update({"collection": collection, "data": data or {}})

    _Repo().set_species_sequence("sp1", "seq1", bound_by=BOUND_BY_SEED)

    assert recorded["collection"] == col.HAS_PHASE_SEQUENCE
    assert recorded["data"]["bound_by"] == BOUND_BY_SEED
    assert recorded["data"]["bound_at"], "bound_at must be recorded too, or 'when' is unanswerable"
