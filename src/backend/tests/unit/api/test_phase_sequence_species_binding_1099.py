"""Issue #1099 defect group A — silent field drops behind a 200.

Two repair scripts reported success while persisting nothing, because the write
answered ``200`` yet a subsequent read did not reflect the submitted field. These
tests are submit -> read-reflects assertions (not just a status check), so a
regression back to the silent-drop behaviour fails here.

* **WP-1 (1a)** ``PUT /phase-sequences/{key}`` accepts ``species_key`` and stores
  it on the document, but ``GET /phase-sequences/{key}`` hand-built its response
  from a field subset that omitted ``species_key`` (and every perennial/photoperiod
  field). The stored value existed; the GET reported ``species_key: ""``. Fixed by
  mapping the whole model through ``to_response``. The service also re-points the
  ``HAS_PHASE_SEQUENCE`` edge so the binding is applied end-to-end.

* **WP-2 (1b)** ``PUT /species/{species_key}/lifecycle/{key}`` — ``phase_sequence_key``
  was already added to the write schema and wired through ``assign_phase_sequence``
  by the #949/#974 work that predates this branch. The test here is a guard proving
  the binding still round-trips; it is not red against current code (see the report).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.api.v1.lifecycle_configs.router import update_lifecycle
from app.api.v1.lifecycle_configs.schemas import LifecycleCreate
from app.api.v1.phase_sequences.router import get_phase_sequence, update_phase_sequence
from app.api.v1.phase_sequences.schemas import PhaseSequenceUpdate
from app.common.enums import CycleType
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase_sequence import PhaseSequence
from app.domain.services.phase_sequence_service import PhaseSequenceService


class TestPhaseSequenceSpeciesKeyRoundTrips:
    """WP-1: submitting ``species_key`` is reflected by a subsequent GET."""

    def test_get_reflects_the_stored_species_key(self) -> None:
        # The GET reads what the PUT stored. Before the fix the router copied a field
        # subset that excluded species_key, so this asserted "11507159" but got "".
        service = MagicMock()
        service.get_full_sequence.return_value = {"entries": []}
        service.get_sequence.return_value = PhaseSequence(
            _key="26733338",
            name="staude_evergreen",
            display_name_de="Immergrüne Staude",
            species_key="11507159",
            tags=["perennial"],
        )

        response = get_phase_sequence(key="26733338", _user=MagicMock(), service=service)

        assert response.species_key == "11507159", (
            "GET dropped species_key behind a 200 — the #1099 silent-field-drop defect."
        )
        # The two fields the repro said *did* land must still land (no regression).
        assert response.display_name_de == "Immergrüne Staude"
        assert response.tags == ["perennial"]

    def test_put_response_also_carries_species_key(self) -> None:
        # The PUT's own 200 body already reflected the field (it used to_response);
        # pin it so the GET and PUT views cannot drift apart again.
        service = MagicMock()
        service.get_full_sequence.return_value = {"entries": []}
        service.get_sequence.return_value = PhaseSequence(
            _key="26733338", name="staude_evergreen", species_key="11507159"
        )

        body = PhaseSequenceUpdate(species_key="11507159")
        response = update_phase_sequence(key="26733338", body=body, _user=MagicMock(), service=service)

        assert response.species_key == "11507159"


class TestUpdateSequenceRepointsTheBinding:
    """WP-1 (end-to-end): the field write also re-points the resolver's edge."""

    def _service(self) -> tuple[PhaseSequenceService, MagicMock]:
        repo = MagicMock()
        repo.get_sequence_by_key.return_value = PhaseSequence(_key="26733338", name="staude_evergreen")
        repo.update_sequence.side_effect = lambda _key, seq: seq
        return PhaseSequenceService(repo), repo

    def test_species_key_update_repoints_has_phase_sequence_edge(self) -> None:
        service, repo = self._service()

        service.update_sequence("26733338", {"species_key": "11507159"})

        # Writing the document field alone was the no-op behind the 200; the binding
        # the lifecycle engine resolves is the edge, so it must be re-pointed too.
        repo.set_species_sequence.assert_called_once_with("11507159", "26733338")

    def test_update_without_species_key_leaves_the_edge_untouched(self) -> None:
        service, repo = self._service()

        service.update_sequence("26733338", {"display_name_de": "Immergrüne Staude"})

        repo.set_species_sequence.assert_not_called()

    def test_empty_species_key_does_not_repoint(self) -> None:
        # An empty string clears the metadata field but is not a binding change:
        # unbinding is done by binding a different sequence, never by a blank.
        service, repo = self._service()

        service.update_sequence("26733338", {"species_key": ""})

        repo.set_species_sequence.assert_not_called()


class TestLifecyclePhaseSequenceKeyRoundTrips:
    """WP-2 guard: ``phase_sequence_key`` submitted through the PUT is reflected.

    Not red against current code — #949/#974 already added the field to the write
    schema and routed it through ``assign_phase_sequence``. This locks that in.
    """

    def test_put_binds_and_response_reflects_phase_sequence_key(self) -> None:
        service = MagicMock()
        service.update_lifecycle.return_value = LifecycleConfig(
            _key="lc-1",
            species_key="11507159",
            cycle_type=CycleType.PERENNIAL,
            phase_sequence_key="26733338",
        )

        body = LifecycleCreate(
            species_key="11507159",
            cycle_type=CycleType.PERENNIAL,
            phase_sequence_key="26733338",
        )
        response = update_lifecycle(species_key="11507159", key="lc-1", body=body, service=service)

        service.assign_phase_sequence.assert_called_once_with("11507159", "26733338")
        assert response.phase_sequence_key == "26733338"

    def test_phase_sequence_key_is_in_the_write_schema(self) -> None:
        assert "phase_sequence_key" in LifecycleCreate.model_fields
