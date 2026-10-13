"""REQ-024 / REQ-025 — the write side of the declared tenant-erasure inventory (#1769).

The caller hands over a :class:`TenantErasurePlan` built by
:meth:`TenantErasureEngine.build_plan`, never a collection name, so the inventory
the guard checks is the inventory that runs.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from app.domain.models.tenant_erasure import TenantErasurePlan, TenantErasureReport


class ITenantErasureExecutor(ABC):
    """Applies the ArangoDB part of a tenant deletion."""

    @abstractmethod
    def run_tenant_erasure(
        self,
        plan: TenantErasurePlan,
        *,
        pseudonymize: Callable[[str], str],
        on_progress: Callable[[dict[str, list[str]]], None] | None = None,
    ) -> TenantErasureReport:
        """Erase ``plan.tenant_key`` as the plan declares, then count what is left.

        Args:
            plan: The declared plan; its entries give the order.
            pseudonymize: Maps an account key found on a retained row to the
                value that replaces it (the account's tombstone hash). Handed in
                as a function so the salt never reaches the data-access layer.
            on_progress: Called with the parent keys resolved so far (merged with
                ``plan.known_parent_keys``) **before** the first row of a parent
                collection is removed — the caller persists them, because a
                deleted parent cannot be re-selected — and again after every
                batch. The call is the heartbeat of a long run (#1792); it may
                raise to stop the run (a lost claim), and the exception
                propagates. Between two calls the executor writes at most one
                bounded batch.

        Returns:
            What each entry matched and changed, the edges removed, and
            ``unreached`` — everything still holding the tenant after the commit.
            A non-empty ``unreached`` means the deletion is **not** complete.

        The rows go in bounded batches, one transaction each (#1792), so a run can
        stop between any two of them; re-running is safe — a second run finds only
        what the first did not reach.
        """
