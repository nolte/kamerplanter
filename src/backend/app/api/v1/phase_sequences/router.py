from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.phase_sequences.schemas import (
    EntryReorderRequest,
    PhaseDefinitionCreate,
    PhaseDefinitionResponse,
    PhaseDefinitionUpdate,
    PhaseSequenceCreate,
    PhaseSequenceEntryCreate,
    PhaseSequenceEntryResponse,
    PhaseSequenceEntryUpdate,
    PhaseSequenceResponse,
    PhaseSequenceUpdate,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_phase_sequence_service
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.domain.models.user import User
from app.domain.services.phase_sequence_service import PhaseSequenceService

router = APIRouter(tags=["phase-sequences"])


# ── Helper functions ──


def _def_response(
    defn: PhaseDefinition,
    usage_count: int = 0,
) -> PhaseDefinitionResponse:
    return PhaseDefinitionResponse(
        key=defn.key or "",
        usage_count=usage_count,
        **defn.model_dump(exclude={"key"}),
    )


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
    return PhaseSequenceEntryResponse(
        key=entry.key or "",
        **entry.model_dump(exclude={"key"}),
    )


# ── Species Phase Sequence Lookup ──


@router.get("/species/{species_key}/phase-sequence", response_model=PhaseSequenceResponse | None)
def get_species_phase_sequence(
    species_key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """Get the PhaseSequence associated with a species."""
    seq = service.get_sequence_by_species(species_key)
    if not seq:
        return None
    full = service.get_full_sequence(seq.key or "")
    entries = [_entry_response(e) for e in full.get("entries", [])]
    return PhaseSequenceResponse(
        key=seq.key or "",
        entries=entries,
        **seq.model_dump(exclude={"key"}),
    )


# ── PhaseDefinition endpoints ──


@router.get("/phase-definitions", response_model=list[PhaseDefinitionResponse])
def list_phase_definitions(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    name: str | None = Query(None),
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    definitions, _ = service.list_definitions(offset, limit, name_filter=name)
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
    defn = PhaseDefinition(**body.model_dump())
    created = service.create_definition(defn)
    return _def_response(created)


@router.get(
    "/phase-definitions/{key}",
    response_model=PhaseDefinitionResponse,
)
def get_phase_definition(
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    defn = service.get_definition(key)
    usage = service._repo.get_definition_usage_count(key)
    return _def_response(defn, usage_count=usage)


@router.get(
    "/phase-definitions/{key}/sequences",
    response_model=list[PhaseSequenceResponse],
)
def list_sequences_for_definition(
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List all PhaseSequences that use this definition."""
    sequences = service.get_sequences_for_definition(key)
    return [PhaseSequenceResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in sequences]


@router.put(
    "/phase-definitions/{key}",
    response_model=PhaseDefinitionResponse,
)
def update_phase_definition(
    key: str,
    body: PhaseDefinitionUpdate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_definition(key, data)
    usage = service._repo.get_definition_usage_count(key)
    return _def_response(updated, usage_count=usage)


@router.delete("/phase-definitions/{key}", status_code=204)
def delete_phase_definition(
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    service.delete_definition(key)
    return Response(status_code=204)


# ── PhaseSequence endpoints ──


@router.get("/phase-sequences", response_model=list[PhaseSequenceResponse])
def list_phase_sequences(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    sequences, _ = service.list_sequences(offset, limit)
    result = []
    for seq in sequences:
        full = service.get_full_sequence(seq.key or "")
        entries = [_entry_response(e) for e in full.get("entries", [])]
        result.append(
            PhaseSequenceResponse(
                key=seq.key or "",
                entries=entries,
                **seq.model_dump(exclude={"key"}),
            ),
        )
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
    seq = PhaseSequence(**body.model_dump())
    created = service.create_sequence(seq)
    return PhaseSequenceResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/phase-sequences/{key}/species")
def list_species_for_sequence(
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    """List all species that use this phase sequence."""
    service.get_sequence(key)  # ensure exists
    return service._repo.get_species_for_sequence(key)


@router.get(
    "/phase-sequences/{key}",
    response_model=PhaseSequenceResponse,
)
def get_phase_sequence(
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
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
    key: str,
    body: PhaseSequenceUpdate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    data = body.model_dump(exclude_none=True)
    service.update_sequence(key, data)
    full = service.get_full_sequence(key)
    entries = [_entry_response(e) for e in full.get("entries", [])]
    seq = service.get_sequence(key)
    return PhaseSequenceResponse(
        key=seq.key or "",
        entries=entries,
        **seq.model_dump(exclude={"key"}),
    )


@router.delete("/phase-sequences/{key}", status_code=204)
def delete_phase_sequence(
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    service.delete_sequence(key)
    return Response(status_code=204)


# ── PhaseSequenceEntry endpoints ──


@router.get(
    "/phase-sequences/{seq_key}/entries",
    response_model=list[PhaseSequenceEntryResponse],
)
def list_entries(
    seq_key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    # Return entries with resolved definitions via get_full_sequence
    full = service.get_full_sequence(seq_key)
    return [_entry_response(e) for e in full.get("entries", [])]


@router.post(
    "/phase-sequences/{seq_key}/entries",
    response_model=PhaseSequenceEntryResponse,
    status_code=201,
)
def create_entry(
    seq_key: str,
    body: PhaseSequenceEntryCreate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
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
    seq_key: str,
    key: str,
    body: PhaseSequenceEntryUpdate,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
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
    seq_key: str,
    key: str,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
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
    seq_key: str,
    body: EntryReorderRequest,
    _user: User = Depends(get_current_user),
    service: PhaseSequenceService = Depends(get_phase_sequence_service),
):
    orders = [item.model_dump() for item in body.entries]
    entries = service.reorder_entries(seq_key, orders)
    return [_simple_entry_response(e) for e in entries]
