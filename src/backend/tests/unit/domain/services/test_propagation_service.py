"""Tests for the D10-minimal PropagationService (REQ-017).

Only ``record`` is implemented (persisting the monocarpic-mother→pup clone event);
listing / full lineage traversal remains a REQ-017 follow-up.
"""

from unittest.mock import MagicMock

import pytest

from app.domain.models.propagation import PropagationEvent
from app.domain.services.propagation_service import PropagationService


def _clone_event() -> PropagationEvent:
    return PropagationEvent(
        tenant_key="tenant-a",
        method="clone",
        parent_plant_keys=["mother-1"],
        child_plant_keys=["pup-1"],
    )


def test_record_persists_via_repo_and_stamps_happened_at() -> None:
    repo = MagicMock()
    repo.create.side_effect = lambda event: event
    service = PropagationService(repo)

    result = service.record(_clone_event())

    repo.create.assert_called_once()
    assert result.happened_at is not None  # stamped when unset
    assert result.method == "clone"


def test_record_without_repo_returns_event_unpersisted() -> None:
    service = PropagationService(None)

    result = service.record(_clone_event())

    assert result.happened_at is not None
    assert result.child_plant_keys == ["pup-1"]


def test_list_for_plant_is_out_of_scope() -> None:
    with pytest.raises(NotImplementedError):
        PropagationService().list_for_plant("pup-1")
