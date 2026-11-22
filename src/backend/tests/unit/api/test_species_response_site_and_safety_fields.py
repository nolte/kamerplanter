"""The species response serves ``waterlogging_tolerance`` (GP-FR-161) and ``toxicity`` (REQ-001).

Both sat on the model and the client type read them, but ``SpeciesResponse`` dropped them, so the planting dialog's
waterlogging hint and the species detail page's toxicity warning were inert (found by the REQ-053 wave-8 E2E run,
#2674). The class guard is ``tests/unit/guards/test_species_response_serves_the_client_type.py``.
"""

from __future__ import annotations

from app.api.mapping import to_response
from app.api.v1.species.schemas import SpeciesResponse
from app.domain.models.species import Species


def _species(**fields: object) -> Species:
    return Species(scientific_name="Solanum lycopersicum", genus="Solanum", **fields)  # type: ignore[arg-type]


def test_the_waterlogging_tolerance_and_the_toxicity_reach_the_response() -> None:
    """#2674 run: both sat on the model, the client read them, the response dropped them (GP-FR-161, REQ-001)."""
    response = to_response(
        _species(
            waterlogging_tolerance="sensitive",
            toxicity={"is_toxic_cats": True, "toxic_parts": ["leaves"]},
        ),
        SpeciesResponse,
    )

    assert response.waterlogging_tolerance == "sensitive"
    assert response.toxicity is not None
    assert (response.toxicity.is_toxic_cats, response.toxicity.toxic_parts) == (True, ["leaves"])
