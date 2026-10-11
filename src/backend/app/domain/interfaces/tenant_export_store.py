"""Ports of the tenant export and import (REQ-056 §8, #2138)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.models.tenant_export import TenantExportRequest, TenantImportRequest


class ITenantDataStore(ABC):
    """Reads one tenant's rows for an export and writes an import's rows (ArangoDB)."""

    @abstractmethod
    def migration_level(self) -> str | None:
        """The highest applied schema migration of this database (``None`` on a virgin one)."""

    @abstractmethod
    def tenant_document(self, tenant_key: str) -> dict[str, Any] | None:
        """The stored tenant document, or ``None``."""

    @abstractmethod
    def collection_names(self) -> set[str]:
        """Every non-system document collection this database has."""

    @abstractmethod
    def edge_collection_names(self) -> list[str]:
        """Every edge collection this database has (sorted)."""

    @abstractmethod
    def iter_tenant_rows(
        self, entry: TenantErasureEntry, *, tenant_key: str, parent_keys: dict[str, list[str]], page_size: int
    ) -> Iterator[list[dict[str, Any]]]:
        """Pages of the tenant's rows of *entry* — the tenant-erasure predicate, never another tenant's row.

        A row belongs to the tenant when it carries the tenant's key in ``entry.tenant_field``
        or points at a parent row of the tenant (``parent_keys``) while carrying no other
        tenant's key. ``keep_if_granted_via`` does not apply: a granted row is still the tenant's.
        """

    @abstractmethod
    def edges_touching(self, edge_collection: str, ids: list[str]) -> list[dict[str, Any]]:
        """Every edge of *edge_collection* whose ``_from`` or ``_to`` is one of *ids*."""

    @abstractmethod
    def existing_global_keys(self, collection: str, keys: list[str]) -> set[str]:
        """Which of *keys* name a **global** row of *collection* (no tenant's key on it)."""

    @abstractmethod
    def insert_documents(self, collection: str, documents: list[dict[str, Any]]) -> list[str]:
        """Insert one batch in one transaction (all or nothing); returns the written keys."""

    @abstractmethod
    def remove_documents(self, collection: str, keys: list[str]) -> int:
        """Remove the documents *keys* of *collection* (an import's rollback)."""

    @abstractmethod
    def remove_tenant_shell(self, *, tenant_key: str) -> None:
        """Remove a tenant an import founded, its memberships and every edge onto either (rollback)."""


class ITenantExportRequestRepository(ABC):
    """``tenant_export_requests`` (tenant-scoped; part of the tenant-erasure inventory)."""

    @abstractmethod
    def create(self, request: TenantExportRequest) -> TenantExportRequest: ...

    @abstractmethod
    def get(self, key: str) -> TenantExportRequest | None: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_tenant(
        self, *, tenant_key: str, requested_by_user_key: str, offset: int, limit: int
    ) -> list[TenantExportRequest]:
        """One page of the requests one account made for the tenant, newest first."""

    @abstractmethod
    def count_requested_since(self, *, tenant_key: str, since: datetime) -> int:
        """Requests of the tenant since *since*, in every state (the daily limit counts failures too)."""

    @abstractmethod
    def active_keys(self, *, tenant_key: str) -> list[str]:
        """Keys of the tenant's ``pending``/``running`` requests, oldest first."""

    @abstractmethod
    def claim(self, key: str, now: datetime) -> TenantExportRequest | None:
        """``pending`` → ``running`` atomically; ``None`` when it is not pending any more."""

    @abstractmethod
    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantExportRequest | None: ...

    @abstractmethod
    def list_expiry_due(self, now: datetime) -> list[TenantExportRequest]:
        """``completed`` requests past ``expires_at``."""

    @abstractmethod
    def list_stale_active(self, before: datetime) -> list[TenantExportRequest]:
        """``pending``/``running`` requests not touched since *before* (a crashed or lost run)."""

    @abstractmethod
    def delete_finished_before(self, before: datetime) -> int:
        """Remove ``failed``/``expired`` requests finished before *before* (NFR-011 R-40)."""


class ITenantImportRequestRepository(ABC):
    """``tenant_import_requests`` (global: the target tenant comes into being during the run)."""

    @abstractmethod
    def create(self, request: TenantImportRequest) -> TenantImportRequest: ...

    @abstractmethod
    def get(self, key: str) -> TenantImportRequest | None: ...

    @abstractmethod
    def claim(self, key: str, now: datetime) -> TenantImportRequest | None:
        """``pending`` → ``validating`` atomically."""

    @abstractmethod
    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantImportRequest | None: ...

    @abstractmethod
    def delete_finished_before(self, before: datetime) -> int:
        """Remove ``completed``/``failed`` requests finished before *before* (NFR-011 R-40)."""

    @abstractmethod
    def list_stale_active(self, before: datetime) -> list[TenantImportRequest]:
        """``pending``/``validating``/``running`` requests not touched since *before* (a run that died, SEC-007)."""
