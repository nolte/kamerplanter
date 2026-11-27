"""The frontend's termination-options fixture is what the API answers (#2888 F-19).

``src/frontend/src/test/fixtures/terminationOptions.json`` feeds the ``TerminationDialog`` vitest suites. A
hand-written fixture could invent a table the server never sends (a cause without a row, a wilt question on
frost) and the dialog tests would pass against it. This test builds the same two answers through the
production path — ``FailureCauseEngine.options`` and the route's ``termination_options_response`` mapping —
and requires the file to equal them. Regenerate the file from :func:`expected_fixture` when the table changes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.api.v1.plant_instances.tenant_router import termination_options_response
from app.domain.engines.failure_cause_engine import FailureCauseEngine
from app.domain.models.phase import PhaseHistory

_FIXTURE = (
    Path(__file__).resolve().parents[4] / "src" / "frontend" / "src" / "test" / "fixtures" / "terminationOptions.json"
)


def _premature_bolting() -> PhaseHistory:
    return PhaseHistory(
        _key="h-1",
        plant_instance_key="plant-1",
        phase_key="ph-bolting",
        phase_name="bolting",
        entered_at=datetime(2026, 6, 1, tzinfo=UTC),
        is_premature=True,
    )


def expected_fixture() -> dict[str, object]:
    """``default``: a lettuce (Asteraceae) in a regular phase; ``wiltProneBolting``: a nightshade that bolted early."""
    engine = FailureCauseEngine()
    return {
        "default": termination_options_response(engine.options(open_phase=None, family_name="Asteraceae")).model_dump(
            mode="json"
        ),
        "wiltProneBolting": termination_options_response(
            engine.options(open_phase=_premature_bolting(), family_name="Solanaceae")
        ).model_dump(mode="json"),
    }


def test_the_frontend_fixture_is_the_api_answer() -> None:
    assert json.loads(_FIXTURE.read_text(encoding="utf-8")) == expected_fixture(), (
        f"{_FIXTURE.name} drifted from the API; regenerate it from expected_fixture()"
    )


def test_the_two_variants_differ_where_the_dialog_tests_rely_on_it() -> None:
    fixture = expected_fixture()
    default, bolting = fixture["default"], fixture["wiltProneBolting"]
    assert isinstance(default, dict) and isinstance(bolting, dict)
    assert (default["suggested_cause"], bolting["suggested_cause"]) == (None, "bolting")
    assert (default["wilt_prone_family"], bolting["wilt_prone_family"]) == (False, True)
