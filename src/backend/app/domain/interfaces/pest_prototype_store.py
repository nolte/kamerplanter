"""REQ-010 / REQ-025 — erasure-side store of contributed pest prototypes (issue #1759).

A promoted pest-image contribution is indexed into the inference-service's
pgvector ``pest_embeddings`` table (``app/tasks/pest_image_tasks.py``) with
``source = 'user_contributed'``, ``source_record_id = <contribution key>`` and
``source_url = contribution://<tenant key>/<contribution key>``. The prototype
is derived from the user's photo and names the contribution, so the Art. 17
erasure and the tenant deletion must *delete* it — before #1759 they only
deactivated promoted rows, skipped demoted ones, and swallowed every error.

Two bindings, chosen per process by
:func:`app.common.dependencies.get_pest_prototype_store`:

* ``inference_service`` — the deletes go through the inference-service and
  raise :class:`~app.common.exceptions.ExternalSourceError` when they do not go
  through;
* ``noop`` — the process reaches no inference-service. It removes nothing only
  while the persisted marker says no prototype was ever indexed, and refuses
  otherwise (the #1753 pattern).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar


class IPestPrototypeStore(ABC):
    """Deletes the pest prototypes indexed from user contributions."""

    #: Which physical index this store reaches (``"inference_service"`` /
    #: ``"noop"``); reported by the erasure next to the removed count.
    binding: ClassVar[str] = "unbound"

    def configuration_error(self) -> str | None:
        """Why this store cannot erase on this deployment, or ``None`` when it can.

        Operator-facing, names no subject. May raise when the answer cannot be
        determined (marker unreadable); a failure is never read as "can erase".
        """
        return None

    @abstractmethod
    async def delete_contributions(self, contribution_keys: list[str]) -> int:
        """Delete the prototypes indexed from these contributions, active or not.

        Returns the number removed; ``0`` without a call for an empty list.
        Raises when the delete does not go through.
        """

    @abstractmethod
    async def delete_tenant_contributions(self, tenant_key: str) -> int:
        """Delete every prototype contributed within *tenant_key*.

        Also reaches a prototype whose contribution document is already gone.
        Raises when the delete does not go through.
        """


class IPestPrototypeContributionMarker(ABC):
    """The persisted fact "a contributed pest prototype may be in the index" (#1759).

    Set by the promotion index task before its upsert, never cleared. Lets a
    process that reaches no inference-service refuse instead of reporting "0
    removed" while prototypes sit in the index.
    """

    @abstractmethod
    def record_pest_prototype_contributions(self, now: datetime) -> None:
        """Set the marker to *now* unless already set. Raises on a storage failure."""

    @abstractmethod
    def pest_prototype_contributions_since(self) -> datetime | None:
        """When the first contribution was indexed, or ``None``. Raises on a storage failure."""
