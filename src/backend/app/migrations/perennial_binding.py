"""Backwards-compatible import path for the phase-sequence classifier.

The classifier moved to :mod:`app.domain.engines.phase_sequence_resolver` (#1006):
it is a pure attribute-driven engine, and leaving it under ``app.migrations`` made it
unreachable for the service layer, which may not import migration modules
(NFR-001 / BACKEND.md §2.1). That is why ``create_species`` and the CSV import bound
no phase sequence while the seed did.

The migrations (v0022, v0024, v0027, v0028, v0029) and their tests keep importing from
here, so the v0022 contract and the migration history are untouched. New code should
import from the engine directly.
"""

from app.domain.engines.phase_sequence_resolver import (
    CAM_DOUBLE_REST_SEQUENCE,
    CAM_SUCCULENT_REST_SEQUENCE,
    CLONAL_MONOCARP_SEQUENCE,
    EVERGREEN_PERENNIAL_SEQUENCE,
    FERN_SPORE_SEQUENCE,
    GEOPHYTE_FINE_SEQUENCE,
    INDOOR_DEFAULT_SEQUENCE,
    PALM_EVERGREEN_SEQUENCE,
    PHOTOPERIODIC_ORNAMENTAL_SEQUENCE,
    RUNNER_PERENNIAL_SEQUENCE,
    resolve_perennial_sequence_name,
    resolve_phase_sequence_name,
)

__all__ = [
    "CAM_DOUBLE_REST_SEQUENCE",
    "CAM_SUCCULENT_REST_SEQUENCE",
    "CLONAL_MONOCARP_SEQUENCE",
    "EVERGREEN_PERENNIAL_SEQUENCE",
    "FERN_SPORE_SEQUENCE",
    "GEOPHYTE_FINE_SEQUENCE",
    "INDOOR_DEFAULT_SEQUENCE",
    "PALM_EVERGREEN_SEQUENCE",
    "PHOTOPERIODIC_ORNAMENTAL_SEQUENCE",
    "RUNNER_PERENNIAL_SEQUENCE",
    "resolve_perennial_sequence_name",
    "resolve_phase_sequence_name",
]
