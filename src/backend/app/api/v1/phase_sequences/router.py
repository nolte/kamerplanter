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
from app.common.auth import get_current_user
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
)
def create_phase_definition(
    body: PhaseDefinitionCreate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Create a new phase definition."""
    defn = PhaseDefinition(**body.model_dump())
    created = service.create_definition(defn)
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
)
def update_phase_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    body: PhaseDefinitionUpdate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Update an existing phase definition."""
    data = body.model_dump(exclude_none=True)
    updated = service.update_definition(key, data)
    usage = service._repo.get_definition_usage_count(key)
    return _def_response(updated, usage_count=usage)


@router.delete("/phase-definitions/{key}", status_code=204)
def delete_phase_definition(
    key: Annotated[str, Path(description="Document key of the phase definition.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Delete a phase definition."""
    service.delete_definition(key)
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
)
def create_phase_sequence(
    body: PhaseSequenceCreate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Create a new phase sequence."""
    seq = PhaseSequence(**body.model_dump())
    created = service.create_sequence(seq)
    return to_response(created, PhaseSequenceResponse)


@router.post(
    "/phase-sequences/{key}/clone",
    response_model=PhaseSequenceResponse,
    status_code=201,
)
def clone_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence to clone.")],
    body: PhaseSequenceCloneRequest,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Duplicate a phase sequence into a new editable, tenant-owned copy (is_system=false)."""
    cloned = service.clone_sequence(key, body.new_name)
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
    service.get_sequence(key)  # ensure exists
    return [PhaseSequenceSpeciesResponse(**row) for row in service._repo.get_species_for_sequence(key)]


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
    full = service.get_full_sequence(key)
    entries = [_entry_response(e) for e in full.get("entries", [])]
    return PhaseSequenceResponse(
        key=full.get("key") or full.get("_key") or key,
        name=full["name"],
        display_name=full.get("display_name", ""),
        display_name_de=full.get("display_name_de", ""),
        description=full.get("description", ""),
        description_de=full.get("description_de", ""),
        cycle_type=full.get("cycle_type", "annual"),
        is_repeating=full.get("is_repeating", False),
        cycle_restart_entry_order=full.get("cycle_restart_entry_order"),
        is_system=full.get("is_system", False),
        tags=full.get("tags", []),
        entries=entries,
        created_at=full.get("created_at"),
        updated_at=full.get("updated_at"),
    )


@router.put(
    "/phase-sequences/{key}",
    response_model=PhaseSequenceResponse,
)
def update_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence.")],
    body: PhaseSequenceUpdate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Update a phase sequence and return it with its resolved entries."""
    data = body.model_dump(exclude_none=True)
    service.update_sequence(key, data)
    full = service.get_full_sequence(key)
    entries = [_entry_response(e) for e in full.get("entries", [])]
    seq = service.get_sequence(key)
    return to_response(seq, PhaseSequenceResponse, entries=entries)


@router.delete("/phase-sequences/{key}", status_code=204)
def delete_phase_sequence(
    key: Annotated[str, Path(description="Document key of the phase sequence.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Delete a phase sequence."""
    service.delete_sequence(key)
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
)
def create_entry(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    body: PhaseSequenceEntryCreate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Add an entry to a phase sequence."""
    entry = PhaseSequenceEntry(
        phase_sequence_key=seq_key,
        **body.model_dump(),
    )
    created = service.create_entry(entry)
    return _simple_entry_response(created)


@router.put(
    "/phase-sequences/{seq_key}/entries/{key}",
    response_model=PhaseSequenceEntryResponse,
)
def update_entry(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    key: Annotated[str, Path(description="Document key of the phase-sequence entry.")],
    body: PhaseSequenceEntryUpdate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Update a phase-sequence entry."""
    # Verify entry belongs to sequence
    entry = service.get_entry(key)
    if entry.phase_sequence_key != seq_key:
        from app.common.exceptions import ValidationError

        raise ValidationError("Entry does not belong to this sequence.")
    data = body.model_dump(exclude_none=True)
    updated = service.update_entry(key, data)
    return _simple_entry_response(updated)


@router.delete(
    "/phase-sequences/{seq_key}/entries/{key}",
    status_code=204,
)
def delete_entry(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    key: Annotated[str, Path(description="Document key of the phase-sequence entry.")],
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Delete a phase-sequence entry."""
    # Verify entry belongs to sequence
    entry = service.get_entry(key)
    if entry.phase_sequence_key != seq_key:
        from app.common.exceptions import ValidationError

        raise ValidationError("Entry does not belong to this sequence.")
    service.delete_entry(key)
    return Response(status_code=204)


@router.post(
    "/phase-sequences/{seq_key}/entries/reorder",
    response_model=list[PhaseSequenceEntryResponse],
)
def reorder_entries(
    seq_key: Annotated[str, Path(description="Document key of the phase sequence.")],
    body: EntryReorderRequest,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Reorder the entries of a phase sequence."""
    orders = [item.model_dump() for item in body.entries]
    entries = service.reorder_entries(seq_key, orders)
    return [_simple_entry_response(e) for e in entries]
