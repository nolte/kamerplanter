"""Domain models for the declared tenant erasure (REQ-024 / REQ-025, #1769).

Tenant deletion used to remove storage, the derived indexes, memberships,
invitations, assignments and the tenant document, and nothing else: every other
collection holding the tenant's rows kept them under a ``tenant_key`` that
pointed at nothing. These models carry the declared inventory that replaces
the hand-written list (:class:`TenantErasureEntry`), what one run did with it
(:class:`TenantErasureReport`) and the persisted proof plus retry state
(:class:`TenantErasureRecord`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

#: What tenant deletion does with an inventoried collection's rows of the tenant.
#:
#: * ``delete`` — the rows go, together with every edge that touches them;
#: * ``pseudonymize`` — the rows stay because a retention law keeps them (CanG,
#:   PflSchG); every account key on them becomes that account's tombstone hash
#:   and their free-text name fields are emptied (the account erasure's
#:   ``tombstone_hash`` rules for the same collection, not a second copy);
#: * ``retain`` — the rows stay untouched, for the reason given (an audit log
#:   with its own retention purge, a row that only *looks* tenant-owned).
type TenantErasureAction = Literal["delete", "pseudonymize", "retain"]

#: Which entry point asked for the deletion.
type TenantErasureOrigin = Literal["tenant_management", "platform_admin"]

type TenantErasureStatus = Literal["in_progress", "completed", "partially_completed"]


class TenantErasureParent(BaseModel):
    """A row belongs to the tenant because its parent row does.

    ``field`` holds the parent's ``_key``; ``where`` narrows a polymorphic
    reference (``workflow_executions.entity_key`` names a plant, a location, a
    tank or a run, told apart by ``entity_type``).
    """

    model_config = {"frozen": True}

    field: str
    collection: str
    where: dict[str, str] = Field(default_factory=dict)


class TenantErasureEntry(BaseModel):
    """One collection of the declared tenant-erasure inventory.

    A row of *collection* belongs to the tenant when its ``tenant_key`` is the
    tenant's key, **or** when one of *parents* points at a row of the tenant —
    ``locations``/``slots`` carry a ``tenant_key`` field that no write path fills
    (#1397), so their site is the only reliable anchor.
    """

    model_config = {"frozen": True}

    collection: str
    action: TenantErasureAction
    #: The field holding the tenant's key. ``tenant_key`` everywhere but on an
    #: API key, whose tenant restriction is ``tenant_scope`` (#1769 review GDPR-007).
    tenant_field: str = "tenant_key"
    parents: tuple[TenantErasureParent, ...] = ()
    #: Rows matching one of these equality examples are never the tenant's to
    #: erase (a system seed the v0004 backfill stamped, ``is_system: true``).
    keep_when: tuple[dict[str, bool | str], ...] = ()
    #: An edge collection of access grants (``tenant_has_access``): a row another
    #: tenant was granted stays, because that tenant's data points at it (#1638).
    keep_if_granted_via: str | None = None
    #: Why the rows are not deleted. Required for ``pseudonymize`` and ``retain``.
    reason: str | None = None

    @model_validator(mode="after")
    def _reason_for_what_stays(self) -> TenantErasureEntry:
        if self.action != "delete" and not (self.reason and self.reason.strip()):
            msg = f"tenant-erasure entry '{self.collection}' keeps rows ({self.action}) and must say why"
            raise ValueError(msg)
        return self


class TenantErasurePseudonymization(BaseModel):
    """The account-key fields of an ``pseudonymize`` entry, read off the account erasure's rules."""

    model_config = {"frozen": True}

    collection: str
    user_field: str
    clear_fields: tuple[str, ...] = ()


class TenantErasurePlan(BaseModel):
    """What one run of the executor is asked to do for one tenant."""

    tenant_key: str
    tenant_collection: str
    entries: list[TenantErasureEntry]
    pseudonymizations: list[TenantErasurePseudonymization] = Field(default_factory=list)
    #: Collections that may hold rows stamped with the tenant's key and are
    #: deliberately left alone — the ``retain`` entries and the declared
    #: non-tenant collections. Everything else still holding such a row after the
    #: run is residue.
    residue_exempt: list[str] = Field(default_factory=list)
    #: Parent keys an earlier attempt of this deletion resolved (#1769 review
    #: SEC-001). A parent it deleted cannot be re-selected, so a child written
    #: after that attempt's snapshot is reached only through these.
    known_parent_keys: dict[str, list[str]] = Field(default_factory=dict)


class TenantErasureOutcome(BaseModel):
    """What the run did with one inventoried collection."""

    collection: str
    action: TenantErasureAction
    matched: int = Field(default=0, ge=0)
    affected: int = Field(default=0, ge=0)


class TenantErasureReport(BaseModel):
    """The executor's account of one run. Names no account and no tenant."""

    outcomes: list[TenantErasureOutcome] = Field(default_factory=list)
    edges_removed: int = Field(default=0, ge=0)
    tenant_document_removed: bool = False
    #: The keys of every parent collection's rows this run resolved, merged with
    #: :attr:`TenantErasurePlan.known_parent_keys` — persisted for the retry.
    parent_keys: dict[str, list[str]] = Field(default_factory=dict)
    #: Inventoried collections the database does not have (they hold no rows).
    absent_collections: list[str] = Field(default_factory=list)
    #: What still holds the tenant after the commit: ``<collection>`` for an
    #: inventoried collection with residue, ``undeclared:<collection>`` for a
    #: collection outside the inventory holding a row stamped with the tenant's
    #: key, ``tenants`` when the tenant document survived. Non-empty means the
    #: deletion is **not** complete.
    unreached: list[str] = Field(default_factory=list)


class TenantErasureRecord(BaseModel):
    """Persisted proof and retry state of one tenant deletion (#1769).

    Keyed per tenant (:meth:`TenantErasureEngine.record_key`), so two concurrent
    deletions of one tenant collide instead of running twice. Carries no tenant
    name, slug or owner — a personal tenant's name is its owner's display name.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    tenant_type: str
    origin: TenantErasureOrigin
    status: TenantErasureStatus = "in_progress"
    requested_at: datetime | None = None
    completed_at: datetime | None = None
    attempt_count: int = Field(default=0, ge=0)
    last_attempt_at: datetime | None = None
    next_attempt_at: datetime | None = None
    error_message: str | None = None
    #: The external/storage phase, as it reported (#1753, #1759).
    reference_index_binding: str | None = None
    reference_index_removed: int | None = Field(default=None, ge=0)
    pest_prototype_binding: str | None = None
    pest_prototypes_removed: int | None = Field(default=None, ge=0)
    storage_objects_removed: int | None = Field(default=None, ge=0)
    #: Raw sensor readings removed from TimescaleDB (#1769 review GDPR-001).
    timeseries_rows_removed: int | None = Field(default=None, ge=0)
    #: The ArangoDB phase, as the executor reported it.
    outcomes: list[TenantErasureOutcome] = Field(default_factory=list)
    edges_removed: int | None = Field(default=None, ge=0)
    unreached: list[str] = Field(default_factory=list)
    #: Parent keys resolved by earlier attempts (SEC-001); fed into the retry.
    parent_keys: dict[str, list[str]] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
