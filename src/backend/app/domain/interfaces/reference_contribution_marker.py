"""#1753 (GDPR-001/002) — the persisted fact "user contributions may exist".

The reference-index store is chosen per process from
``settings.inference_service_enabled``. A process without the flag — the
celery-worker that runs the scheduled Art. 17 erasure, or any process after the
flag was switched off — binds the no-op store, which on its own would answer
"nothing to delete" while contributed vectors sit in the inference-service.

This marker closes that: the only writer of contributions
(``ReferenceImageService.contribute_user_reference``) records it *before* its
upsert, and the no-op store refuses to report success while it is set. It
holds a timestamp, no personal data, and is never cleared by the erasure — a
deployment that has ever accepted a contribution must reach the index to erase.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class IReferenceContributionMarker(ABC):
    """Read and set the instance-wide "reference contributions exist since" marker."""

    @abstractmethod
    def record_reference_contributions(self, now: datetime) -> None:
        """Set the marker to *now* unless it is already set (idempotent, atomic).

        Raises on a storage failure — a contribution must not be written when
        the marker could not be.
        """

    @abstractmethod
    def reference_contributions_since(self) -> datetime | None:
        """When the first contribution was accepted, or ``None`` if never.

        Raises on a storage failure; a caller deciding whether an erasure may
        skip the index must not read a failure as "never".
        """
