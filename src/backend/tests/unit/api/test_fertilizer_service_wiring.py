"""The production factory of the fertilizer service wires the species repository (#2654).

The area-dosing API tests override ``get_fertilizer_service`` with a service built in the test, so they never reach
the factory. Without ``species_repo`` every request with a ``species_key`` would fail as a validation error while all
those tests stay green; this pins the wiring the production path uses.
"""

from unittest.mock import MagicMock

import pytest

from app.common import dependencies


def test_the_fertilizer_service_factory_wires_the_species_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dependencies, "get_db", lambda: MagicMock())

    service = dependencies.get_fertilizer_service()

    assert service._species_repo is not None
