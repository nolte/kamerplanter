"""Reusable Pydantic validators shared across domain models and request schemas.

Centralising these keeps a single source of truth for cross-cutting field rules
so a fix lands in one place rather than being copied onto every schema that
mirrors a domain field (#1035).
"""

from typing import Annotated

from pydantic import AfterValidator, Field


def _reject_blank_display_name(value: str) -> str:
    """Reject a display name that is empty or whitespace-only after stripping.

    ``min_length=1`` is length-based, so it lets ``"   "`` through and the value
    is persisted (#1035). This closes that gap with the same reject-not-normalise
    contract the empty string already has: a blank name is refused, but a valid
    name is returned **unchanged** — internal spaces (``"Bob Smith"``) and
    surrounding spaces are preserved so every path that reads the raw
    ``display_name`` (e.g. the personal-tenant name derived at registration) stays
    consistent with what the user submitted. Normalising would have to be applied
    identically at all of those read sites to avoid drift; reject-only needs no
    such coordination and is the minimum the issue calls for.
    """
    if not value.strip():
        raise ValueError("must not be empty or whitespace-only")
    return value


#: A user-facing display name: 1–200 characters, rejected when blank after
#: stripping (#1035). Use ``DisplayName`` on required fields and
#: ``DisplayName | None`` (with ``= None``) on optional-update fields.
#:
#: The ``AfterValidator`` runs on model validation, so it fires both at the
#: FastAPI request boundary (→ 422 for free) and on the repository's
#: ``model_validate`` re-check in ``_to_doc`` (→ mapped to 422), covering the
#: direct-construction, self-service and platform-admin write paths alike.
DisplayName = Annotated[
    str,
    Field(min_length=1, max_length=200),
    AfterValidator(_reject_blank_display_name),
]
