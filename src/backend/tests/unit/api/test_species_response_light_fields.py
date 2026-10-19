"""WP 3.9 (#2399): the species response carries the demand and the tolerance side of ``site_fit``.

The planting dialog compares the bed's sun class with ``Species.light_requirement`` and widens the
yellow zone by ``Species.shade_tolerance`` (GP-FR-160, E-05). Both sat on the model and in the seeds but
not in ``SpeciesResponse``, so the client could never see them; ``row_spacing_cm`` (GP-FR-061) was in the
same position.
"""

from __future__ import annotations

from app.api.mapping import to_response
from app.api.v1.species.schemas import SpeciesResponse
from app.domain.models.species import Species


def _species(**fields: object) -> Species:
    return Species(scientific_name="Solanum lycopersicum", genus="Solanum", **fields)  # type: ignore[arg-type]


def test_the_light_fields_reach_the_response() -> None:
    response = to_response(
        _species(light_requirement="full_sun", shade_tolerance="partial_shade", row_spacing_cm="60--80"),
        SpeciesResponse,
    )

    assert (response.light_requirement, response.shade_tolerance, response.row_spacing_cm) == (
        "full_sun",
        "partial_shade",
        "60--80",
    )


def test_a_species_without_them_answers_null_not_a_default() -> None:
    response = to_response(_species(), SpeciesResponse)

    assert response.light_requirement is None
    assert response.shade_tolerance is None
    assert response.row_spacing_cm is None
