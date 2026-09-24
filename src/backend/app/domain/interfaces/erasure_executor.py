"""REQ-025 Art. 17 — the write side of the declared erasure inventory (#1664).

The erasure plan (:meth:`ErasureEngine.build_erasure_plan`) declares, step by
step, which ArangoDB rows of a user are removed, which retained rows lose their
user reference and which audit rows are pseudonymised. This interface is how a
plan turns into writes. The caller hands over the *plan*, never a collection
name, so the inventory an auditor reads stays the inventory that runs (#1622).
"""

from abc import ABC, abstractmethod
from collections.abc import Collection

from app.domain.models.privacy import ErasureExecutionReport, ErasureExecutor, ErasurePlan


class IErasureExecutor(ABC):
    """Applies the ArangoDB part of an :class:`ErasurePlan` in declared order."""

    @abstractmethod
    def run_erasure_plan(
        self,
        plan: ErasurePlan,
        *,
        tombstone: str | None,
        executors: Collection[ErasureExecutor] | None = None,
    ) -> ErasureExecutionReport:
        """Run every ArangoDB step of *plan* for ``plan.user_key``.

        Args:
            plan: The declared plan. Its ``steps`` give the order; its
                ``anonymize`` and ``pseudonymize_audit`` rules are applied when
                the matching phase step is reached.
            tombstone: The subject's :meth:`ErasureEngine.compute_tombstone_hash`.
                Required as soon as a ``tombstone_hash`` rule is reached; the
                executor refuses to start without it rather than half-running.
            executors: Restrict the run to the steps attributed to these
                executors. ``None`` runs every ArangoDB step of the plan.

        Returns:
            The rows each step reached, in declared order.

        A step that touches no row is not an error — a re-run after a crash
        finds the rows the first run already handled gone and reports ``0``.
        """
