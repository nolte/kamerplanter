"""REQ-047 §2.1 — unit tests for ArangoSeasonStateRepository.upsert (B3).

Focus: the create-race recovery. Two parallel evaluations of a state-less site
both reach the insert; the unique ``(tenant_key, site_key)`` index rejects the
loser. The loser must re-read the winner and update it in place instead of
propagating a 500.
"""

from unittest.mock import MagicMock

from app.common.exceptions import DuplicateError
from app.data_access.arango.season_state_repository import ArangoSeasonStateRepository
from app.domain.models.season_state import SeasonState


def _repo() -> ArangoSeasonStateRepository:
    return ArangoSeasonStateRepository(MagicMock())


def _state(**overrides) -> SeasonState:
    data = {"season_state_id": "s", "site_key": "site-1", "tenant_key": "tenant-1"}
    data.update(overrides)
    return SeasonState(**data)


class TestUpsertRace:
    def test_create_race_recovers_by_updating_winner(self) -> None:
        repo = _repo()
        incoming = _state()
        winner = _state(season_state_id="winner", _key="win-key")

        # First lookup: no state yet → take the create path. The insert loses the
        # unique race (DuplicateError). Second lookup: the winner now exists.
        repo.get_by_site = MagicMock(side_effect=[None, winner])
        repo._insert_doc = MagicMock(side_effect=DuplicateError("season_states", "key", "dup"))
        repo._update_doc = MagicMock(side_effect=lambda key, model: {**model.model_dump(by_alias=True), "_key": key})
        repo.create_edge = MagicMock()

        result = repo.upsert(incoming)

        assert result.key == "win-key"
        repo._update_doc.assert_called_once()
        # No edge is wired on the recovery path (the winner already has one).
        repo.create_edge.assert_not_called()

    def test_create_race_reraises_when_winner_vanishes(self) -> None:
        repo = _repo()
        repo.get_by_site = MagicMock(side_effect=[None, None])
        repo._insert_doc = MagicMock(side_effect=DuplicateError("season_states", "key", "dup"))

        try:
            repo.upsert(_state())
        except DuplicateError:
            pass
        else:  # pragma: no cover - defensive
            raise AssertionError("expected DuplicateError to propagate")

    def test_plain_create_wires_edge(self) -> None:
        repo = _repo()
        repo.get_by_site = MagicMock(return_value=None)
        repo._insert_doc = MagicMock(
            side_effect=lambda model, **_: {**model.model_dump(by_alias=True), "_key": "new-key"}
        )
        repo.create_edge = MagicMock()

        result = repo.upsert(_state())

        assert result.key == "new-key"
        repo.create_edge.assert_called_once()

    def test_existing_state_is_updated_in_place(self) -> None:
        repo = _repo()
        existing = _state(_key="existing")
        repo.get_by_site = MagicMock(return_value=existing)
        repo._update_doc = MagicMock(side_effect=lambda key, model: {**model.model_dump(by_alias=True), "_key": key})
        repo.create_edge = MagicMock()

        result = repo.upsert(_state(season_state_id="updated"))

        assert result.key == "existing"
        repo.create_edge.assert_not_called()
