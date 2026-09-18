from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.mapping import to_response
from app.api.v1.phase_sequences.schemas import (
    EntryReorderRequest,
    PhaseDefinitionCreate,
    PhaseDefinitionResponse,
    PhaseDefinitionSpeciesResponse,
    PhaseDefinitionUpdate,
    PhaseSequenceCloneRequest,
    PhaseSequenceCreate,
    PhaseSequenceEntryCreate,
    PhaseSequenceEntryResponse,
    PhaseSequenceEntryUpdate,
    PhaseSequenceResponse,
    PhaseSequenceSpeciesResponse,
    PhaseSequenceUpdate,
)
from app.common.auth import get_current_user, get_is_platform_admin, require_platform_admin
from app.common.dependencies import get_phase_sequence_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE, UNAUTHORIZED_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.domain.models.user import User
from app.domain.services.phase_sequence_service import PhaseSequenceService

router = APIRouter(tags=["phase-sequences"], responses={**UNAUTHORIZED_RESPONSE, **NOT_FOUND_RESPONSE})

# ── Authorisation (#1501) ───────────────────────────────────────────────────────
#
# Phase definitions, phase sequences and their entries are **installation-wide**:
# none of the three models carries a ``tenant_key``, so one row is the row every
# tenant's lifecycle configuration resolves. That places them in exactly the class
# `growth_phases`, `location_types` and `activities` already occupy, and they now
# carry the same gate — ``require_platform_admin`` on the write, nothing on the
# read (a catalogue nobody may read is as broken as one anybody may edit).
#
# Every write route carries the gate TWICE on purpose, and the two halves are not
# redundant in the way that word usually means:
#
# * ``dependencies=[Depends(require_platform_admin)]`` refuses before the handler
#   body runs, so the 403 is the route's published contract and appears in the
#   OpenAPI document;
# * ``is_platform_admin=Depends(get_is_platform_admin)`` threaded into the service
#   is what a *non-HTTP* caller would meet. The service is the layer that owns the
#   rule (`app/core/permissions.py` argues why a rule may live in only one place),
#   and its argument is keyword-only with no default, so a future caller that
#   forgets it gets a ``TypeError`` rather than a silent grant.
#
# Dropping either half is what "the two enforcement paths drift" looks like in
# practice: the router copy alone leaves the service open to the next caller, the
# service copy alone leaves the refusal undocumented.
_PLATFORM_ADMIN = [Depends(require_platform_admin)]


# ── Helper functions ──


def _def_response(
    defn: PhaseDefinition,
    usage_count: int = 0,
) -> PhaseDefinitionResponse:
    return to_response(defn, PhaseDefinitionResponse, usage_count=usage_count)


def _entry_response(entry_dict: dict) -> PhaseSequenceEntryResponse:
    """Build entry response from enriched dict (from get_full_sequence)."""
    pd = entry_dict.get("phase_definition")
    pd_resp = None
    if pd:
        pd_resp = PhaseDefinitionResponse(
            key=pd.get("key") or pd.get("_key") or "",
            **{k: v for k, v in pd.items() if k not in ("key", "_key")},
        )
    return PhaseSequenceEntryResponse(
        key=entry_dict.get("key") or entry_dict.get("_key") or "",
        phase_sequence_key=entry_dict.get("phase_sequence_key", ""),
        phase_definition_key=entry_dict.get("phase_definition_key", ""),
        sequence_order=entry_dict.get("sequence_order", 0),
        override_duration_days=entry_dict.get("override_duration_days"),
        effective_duration_days=entry_dict.get("effective_duration_days", 1),
        is_terminal=entry_dict.get("is_terminal", False),
        allows_harvest=entry_dict.get("allows_harvest", False),
        is_recurring=entry_dict.get("is_recurring", False),
        phase_definition=pd_resp,
        created_at=entry_dict.get("created_at"),
        updated_at=entry_dict.get("updated_at"),
    )


def _simple_entry_response(entry: PhaseSequenceEntry) -> PhaseSequenceEntryResponse:
    """Build entry response from model (no resolved definition)."""
    return to_response(entry, PhaseSequenceEntryResponse)


# ── Species Phase Sequence Lookup ──


@router.get("/species/{species_key}/phase-sequence", response_model=PhaseSequenceResponse | None)
def get_species_phase_sequence(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Get the PhaseSequence associated with a species."""
    seq = service.get_sequence_by_species(species_key)
    if not seq:
        return None
    full = service.get_full_sequence(seq.key or "")
    entries = [_entry_response(e) for e in full.get("entries", [])]
    return to_response(seq, PhaseSequenceResponse, entries=entries)


# ── PhaseDefinition endpoints ──


@router.get("/phase-definitions", response_model=list[PhaseDefinitionResponse])
def list_phase_definitions(
    pagination: PaginationParams = Depends(get_pagination),
    name: str | None = Query(None, description="Filter phase definitions by name (substring match)."),
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List phase definitions (paginated), optionally filtered by name."""
    definitions, _ = service.list_definitions(pagination.offset, pagination.limit, name_filter=name)
    result = []
    for defn in definitions:
        usage = service._repo.get_definition_usage_count(defn.key or "")
        result.append(_def_response(defn, usage_count=usage))
    return result


@router.post(
    "/phase-definitions",
    response_model=PhaseDefinitionResponse,
    status_code=201,
    dependencies=_PLATFORM_ADMIN,
)
def create_phase_definition(
    body: PhaseDefinitionCreate,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Create a new phase definition. Platform admins only (#1501)."""
    defn = PhaseDefinition(**body.model_dump())
    created = service.create_definition(defn, is_platform_admin=is_platform_admin)
    return _def_response(created)


@router.get(
    "/phase-definitions/{key}",
    response_model=PhaseDefinitionResponse,
)
def get_phase_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Return a single phase definition by key."""
    defn = service.get_definition(key)
    usage = service._repo.get_definition_usage_count(key)
    return _def_response(defn, usage_count=usage)


@router.get(
    "/phase-definitions/{key}/sequences",
    response_model=list[PhaseSequenceResponse],
)
def list_sequences_for_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List all PhaseSequences that use this definition."""
    sequences = service.get_sequences_for_definition(key)
    return [to_response(s, PhaseSequenceResponse) for s in sequences]


@router.get(
    "/phase-definitions/{key}/species",
    response_model=list[PhaseDefinitionSpeciesResponse],
)
def list_species_for_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List all species (global catalog) that traverse this phase definition (FIX-01 R5/R9).

    Global read-only endpoint composed from existing repository building blocks; an
    empty list is a valid result (no 404, R7).
    """
    return [PhaseDefinitionSpeciesResponse(**row) for row in service.get_species_for_definition(key)]


@router.put(
    "/phase-definitions/{key}",
    response_model=PhaseDefinitionResponse,
    dependencies=_PLATFORM_ADMIN,
)
def update_phase_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    body: PhaseDefinitionUpdate,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Update an existing phase definition. Platform admins only (#1501)."""
    data = body.model_dump(exclude_none=True)
    updated = service.update_definition(key, data, is_platform_admin=is_platform_admin)
    usage = service._repo.get_definition_usage_count(key)
    return _def_response(updated, usage_count=usage)


@router.delete("/phase-definitions/{key}", status_code=204, dependencies=_PLATFORM_ADMIN)
def delete_phase_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Delete a phase definition. Platform admins only (#1501)."""
    service.delete_definition(key, is_platform_admin=is_platform_admin)
    return Response(status_code=204)


# ── PhaseSequence endpoints ──


@router.get("/phase-sequences", response_model=list[PhaseSequenceResponse])
def list_phase_sequences(
    pagination: PaginationParams = Depends(get_pagination),
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List phase sequences (paginated), each with its resolved entries."""
    sequences, _ = service.list_sequences(pagination.offset, pagination.limit)
    result = []
    for seq in sequences:
        full = service.get_full_sequence(seq.key or "")
        entries = [_entry_response(e) for e in full.get("entries", [])]
        result.append(to_response(seq, PhaseSequenceResponse, entries=entries))
    return result


@router.post(
    "/phase-sequences",
    response_model=PhaseSequenceResponse,
    status_code=201,
    dependencies=_PLATFORM_ADMIN,
)
def create_phase_sequence(
    body: PhaseSequenceCreate,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Create a new phase sequence. Platform admins only (#1501)."""
    seq = PhaseSequence(**body.model_dump())
    created = service.create_sequence(seq, is_platform_admin=is_platform_admin)
    return to_response(created, PhaseSequenceResponse)


@router.post(
    "/phase-sequences/{key}/clone",
    response_model=PhaseSequenceResponse,
    status_code=201,
    dependencies=_PLATFORM_ADMIN,
)
def clone_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence to clone.")],
    body: PhaseSequenceCloneRequest,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Duplicate a phase sequence into a new editable copy (is_system=false).

    Platform admins only (#1501). The clone is **not** tenant-owned — this
    docstring said it was, and that claim is why a global create read as a local
    one; ``PhaseSequence`` carries no ``tenant_key`` at all.
    """
    cloned = service.clone_sequence(key, body.new_name, is_platform_admin=is_platform_admin)
    full = service.get_full_sequence(cloned.key or "")
    entries = [_entry_response(e) for e in full.get("entries", [])]
    return to_response(cloned, PhaseSequenceResponse, entries=entries)


@router.get("/phase-sequences/{key}/species", response_model=list[PhaseSequenceSpeciesResponse])
def list_species_for_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List all species that use this phase sequence."""
    # Goes through the service (which itself checks the sequence exists) rather than
    # reaching into its private repository — the API layer must not skip a layer.
    return [PhaseSequenceSpeciesResponse(**row) for row in service.get_species_for_sequence(key)]


@router.get(
    "/phase-sequences/{key}",
    response_model=PhaseSequenceResponse,
)
def get_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Return a single phase sequence by key, with its resolved entries."""
    # Map the whole persisted model (via ``to_response``) rather than hand-copying a
    # subset of fields: the hand-built response used to silently drop ``species_key``
    # (and every perennial/photoperiod field), so a PUT that stored the species
    # binding answered 200 while this GET reported ``species_key: ""`` (#1099).
    full = service.get_full_sequence(key)
    entries = [_entry_response(e) for e in full.get("entries", [])]
    seq = service.get_sequence(key)
    return to_response(seq, PhaseSequenceResponse, entries=entries)


@router.put(
    "/phase-sequences/{key}",
    response_model=PhaseSequenceResponse,
    dependencies=_PLATFORM_ADMIN,
)
def update_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence.")],
    body: PhaseSequenceUpdate,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Update a phase sequence and return it with its resolved entries. Platform admins only (#1501)."""
    data = body.model_dump(exclude_none=True)
    service.update_sequence(key, data, is_platform_admin=is_platform_admin)
    full = service.get_full_sequence(key)
    entries = [_entry_response(e) for e in full.get("entries", [])]
    seq = service.get_sequence(key)
    return to_response(seq, PhaseSequenceResponse, entries=entries)


@router.delete("/phase-sequences/{key}", status_code=204, dependencies=_PLATFORM_ADMIN)
def delete_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence.")],
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Delete a phase sequence. Platform admins only (#1501)."""
    service.delete_sequence(key, is_platform_admin=is_platform_admin)
    return Response(status_code=204)


# ── PhaseSequenceEntry endpoints ──


@router.get(
    "/phase-sequences/{seq_key}/entries",
    response_model=list[PhaseSequenceEntryResponse],
)
def list_entries(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List a phase sequence's entries with their resolved phase definitions."""
    # Return entries with resolved definitions via get_full_sequence
    full = service.get_full_sequence(seq_key)
    return [_entry_response(e) for e in full.get("entries", [])]


@router.post(
    "/phase-sequences/{seq_key}/entries",
    response_model=PhaseSequenceEntryResponse,
    status_code=201,
    dependencies=_PLATFORM_ADMIN,
)
def create_entry(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    body: PhaseSequenceEntryCreate,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Add an entry to a phase sequence. Platform admins only (#1501)."""
    entry = PhaseSequenceEntry(
        phase_sequence_key=seq_key,
        **body.model_dump(),
    )
    created = service.create_entry(entry, is_platform_admin=is_platform_admin)
    return _simple_entry_response(created)


@router.put(
    "/phase-sequences/{seq_key}/entries/{key}",
    response_model=PhaseSequenceEntryResponse,
    dependencies=_PLATFORM_ADMIN,
)
def update_entry(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    key: Annotated[str, Path(description="Document key of the phase-sequence entry.")],
    body: PhaseSequenceEntryUpdate,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Update a phase-sequence entry. Platform admins only (#1501)."""
    # Verify entry belongs to sequence
    entry = service.get_entry(key)
    if entry.phase_sequence_key != seq_key:
        from app.common.exceptions import ValidationError

        raise ValidationError("Entry does not belong to this sequence.")
    data = body.model_dump(exclude_none=True)
    updated = service.update_entry(key, data, is_platform_admin=is_platform_admin)
    return _simple_entry_response(updated)


@router.delete(
    "/phase-sequences/{seq_key}/entries/{key}",
    status_code=204,
    dependencies=_PLATFORM_ADMIN,
)
def delete_entry(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    key: Annotated[str, Path(description="Document key of the phase-sequence entry.")],
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Delete a phase-sequence entry. Platform admins only (#1501)."""
    # Verify entry belongs to sequence
    entry = service.get_entry(key)
    if entry.phase_sequence_key != seq_key:
        from app.common.exceptions import ValidationError

        raise ValidationError("Entry does not belong to this sequence.")
    service.delete_entry(key, is_platform_admin=is_platform_admin)
    return Response(status_code=204)


@router.post(
    "/phase-sequences/{seq_key}/entries/reorder",
    response_model=list[PhaseSequenceEntryResponse],
    dependencies=_PLATFORM_ADMIN,
)
def reorder_entries(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    body: EntryReorderRequest,
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Reorder the entries of a phase sequence. Platform admins only (#1501)."""
    orders = [item.model_dump() for item in body.entries]
    entries = service.reorder_entries(seq_key, orders, is_platform_admin=is_platform_admin)
    return [_simple_entry_response(e) for e in entries]
