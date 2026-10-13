"""REQ-025 / REQ-010 — delete contributed pest prototypes whose contribution is gone (issue #1771).

Before #1766 (``0c217e570``) deleting a pest-image contribution removed its
link document and attachment but left the prototype the promotion index task
had written into the inference-service's ``pest_embeddings``. Those rows carry
the contribution key (``source_record_id``) and the tenant (``source_url``) but
no user key, and the account erasure finds prototypes only through a user's
contribution documents — so no erasure reaches them. Only a tenant deletion,
by prefix, does.

The sweep closes that residue and any later one (an undo that exhausted its
retries in ``erase_pest_prototype_task``):

1. page through the contribution keys the index holds (keyset, ascending);
2. ask ArangoDB which of them still name a ``pest_image_contributions``
   document — tenant-agnostic, keys only;
3. delete the prototypes of the others through the same authenticated,
   ``user_contributed``-bound erase route the Art. 17 erasure uses, active and
   deactivated rows alike (a row without its document serves no curation
   purpose: nothing can re-promote or demote it);
4. record the counts in ``system_settings.pest_prototype_orphan_sweep``.

A process bound to the no-op store (no inference-service configured, no
prototype ever marked) has looked at nothing: it reports ``skipped`` and
records **no** run, so a worker without the flags never leaves a record saying
the index was swept (GDPR review of #1771 — v0061 does not mark a deployment
whose contribution documents were all deleted, which is exactly this residue).

**Idempotent:** a second run finds no orphan and removes nothing. **Fails
loud:** an unreachable index, a refusing no-op binding or a failed record
raises; nothing is recorded as done. The log carries counts, never a key.

A prototype is only ever written for a contribution whose document exists
(the index task reads it first and undoes the upsert when it vanished
meanwhile), and ArangoDB does not reuse a document key, so a key without a
document cannot become valid again: deleting its prototype can never take one
that a live contribution needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from app.common.exceptions import FeatureNotConfiguredError
from app.domain.interfaces.pest_image_repository import IPestImageRepository
from app.domain.interfaces.pest_prototype_store import IPestPrototypeOrphanSweepLog, IPestPrototypeStore

logger = structlog.get_logger()

#: Keys per listing page and per erase request (the service refuses more than 1000).
SWEEP_PAGE_SIZE = 500


@dataclass(frozen=True)
class PestPrototypeOrphanSweepResult:
    """Counts of one run — never a key."""

    examined: int
    orphaned: int
    removed: int
    binding: str
    #: ``completed`` (swept and recorded) or ``skipped`` (no index reachable, nothing recorded).
    status: str = "completed"


class PestPrototypeOrphanSweepService:
    """Finds and deletes contributed pest prototypes without a contribution document."""

    def __init__(
        self,
        *,
        store: IPestPrototypeStore,
        pest_image_repo: IPestImageRepository,
        sweep_log: IPestPrototypeOrphanSweepLog,
        page_size: int = SWEEP_PAGE_SIZE,
    ) -> None:
        self._store = store
        self._repo = pest_image_repo
        self._log = sweep_log
        self._page_size = page_size

    async def run(self) -> PestPrototypeOrphanSweepResult:
        """Delete every orphaned contributed prototype and record the counts.

        Raises:
            FeatureNotConfiguredError: this process cannot reach the index while
                a prototype may exist in it.
            ExternalSourceError: the index could not be listed or a delete did
                not go through.
        """
        error = self._store.configuration_error()
        if error is not None:
            raise FeatureNotConfiguredError("pest_prototype_orphan_sweep", error)
        if self._store.binding == "noop":
            logger.warning(
                "pest_prototype_orphan_sweep_skipped",
                reason="no_inference_service_in_this_process",
                binding=self._store.binding,
            )
            return PestPrototypeOrphanSweepResult(
                examined=0, orphaned=0, removed=0, binding=self._store.binding, status="skipped"
            )

        examined = orphaned = removed = 0
        after: str | None = None
        while True:
            keys, next_after = await self._store.list_contribution_keys(after=after, limit=self._page_size)
            examined += len(keys)
            if keys:
                existing = self._repo.existing_keys(keys)
                # A key blank to the erase route (Python's ``strip``) is refused
                # there with 422 and would stop every run on this page; the
                # listing leaves such keys out by the index's own whitespace
                # rule, which does not cover every Unicode space (code review).
                orphans = [key for key in keys if key not in existing and key.strip()]
                if orphans:
                    removed += await self._store.delete_contributions(orphans)
                    orphaned += len(orphans)
            if next_after is None:
                break
            if next_after == after:
                # A cursor that does not advance would loop forever. (Compared
                # for equality only: the order is the index's collation, not
                # Python's.)
                msg = "pest-prototype key listing did not advance its cursor"
                raise RuntimeError(msg)
            after = next_after

        result = PestPrototypeOrphanSweepResult(
            examined=examined, orphaned=orphaned, removed=removed, binding=self._store.binding
        )
        self._log.record_pest_prototype_orphan_sweep(
            now=datetime.now(UTC),
            examined=result.examined,
            orphaned=result.orphaned,
            removed=result.removed,
            binding=result.binding,
        )
        logger.info(
            "pest_prototype_orphan_sweep_completed",
            examined=result.examined,
            orphaned=result.orphaned,
            removed=result.removed,
            binding=result.binding,
        )
        return result
