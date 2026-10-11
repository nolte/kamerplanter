"""The plan catalogue store (REQ-056 §7, §13.2, #2142).

Global, not tenant-scoped: a plan is platform configuration every tenant may point at.
The tenant counts per plan are read here too, because they are a question about the
catalogue (may this plan be deleted, how many tenants does it serve) and not about one
tenant.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.models.plan import Plan


class IPlanRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Plan | None:
        """The plan stored under *key*, or ``None``."""

    @abstractmethod
    def get_default(self) -> Plan | None:
        """The plan marked ``is_default`` (the oldest one, should a data error have marked several)."""

    @abstractmethod
    def list_all(self) -> list[Plan]:
        """Every plan, ordered by key. The catalogue is small and kept by hand; it is not paged."""

    @abstractmethod
    def create(self, plan: Plan) -> Plan:
        """Insert *plan*; ``DuplicateError`` when its key is taken."""

    @abstractmethod
    def store_plan(self, plan: Plan) -> Plan | None:
        """Write *plan* whole (name, description, limits); ``None`` when no plan carries its key.

        ``is_default`` is **not** written here - it moves only through :meth:`make_default`, which keeps
        exactly one default.
        """

    @abstractmethod
    def make_default(self, key: str) -> Plan | None:
        """Mark *key* as the one default plan and unmark every other, in one statement.

        ``None`` (and nothing changed) when no plan carries *key*.
        """

    @abstractmethod
    def delete_unused(self, key: str) -> bool:
        """Remove the plan unless a tenant points at it or it is the default; ``True`` when it was removed.

        Decided in one statement, so a plan a tenant was assigned a moment ago is not removed on a count
        read before that.
        """

    @abstractmethod
    def tenant_counts(self) -> dict[str, int]:
        """How many tenants point at each plan key (keys without a tenant are absent)."""

    @abstractmethod
    def count_tenants_on(self, key: str) -> int:
        """How many tenants point at *key*."""
