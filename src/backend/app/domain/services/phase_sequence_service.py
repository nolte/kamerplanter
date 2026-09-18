from app.common.exceptions import NotFoundError, ValidationError
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.domain.services.catalogue_authorization import require_platform_admin_for_global_catalogue

#: The entity name the refusal names, per model. One map rather than a literal at
#: each call site: eleven copies of a string is eleven chances to name the wrong
#: catalogue in a 403.
_DEFINITION = "phase definition"
_SEQUENCE = "phase sequence"
_ENTRY = "phase-sequence entry"


class PhaseSequenceService:
    """Service for managing phase definitions, sequences, and entries.

    **Every write here is installation-wide** (#1501). Unlike species, cultivars
    and substrates, none of the three models carries a ``tenant_key`` — measured,
    not assumed: :mod:`app.domain.models.phase_sequence` declares ``is_system``
    and nothing else that could express ownership. So there is no hybrid arm and
    no ownership arm to fall back on; this is the *global-only* shape
    :mod:`app.domain.services.catalogue_authorization` describes for botanical
    families, and the only honest answer to "who may change a row every tenant
    reads" is platform admin.

    Until #1501 the eleven write routes above this service resolved
    ``get_current_user`` and nothing else, and the service re-gated nothing: any
    authenticated member of any tenant could delete the phase definition REQ-003's
    state machine runs on, for everyone.

    ``is_platform_admin`` is **keyword-only and carries no default** on every write
    method. A default would be the drift this module cannot afford: a new caller
    that forgets the argument would inherit permission rather than a
    ``TypeError``. Nothing but the router reaches these methods — the seeders in
    ``app/migrations/seed_phase_sequences.py`` write through the *repository*
    directly (measured) — so there is no system-context escape to keep open and
    none is offered.
    """

    def __init__(self, repo: IPhaseSequenceRepository) -> None:
        self._repo = repo

    # ── PhaseDefinition CRUD ──

    def list_definitions(
        self,
        offset: int = 0,
        limit: int = 50,
        name_filter: str | None = None,
    ) -> tuple[list[PhaseDefinition], int]:
        return self._repo.get_all_definitions(offset, limit, name_filter)

    def get_definition(self, key: str) -> PhaseDefinition:
        defn = self._repo.get_definition_by_key(key)
        if not defn:
            raise NotFoundError("PhaseDefinition", key)
        return defn

    def create_definition(self, defn: PhaseDefinition, *, is_platform_admin: bool) -> PhaseDefinition:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_DEFINITION)
        return self._repo.create_definition(defn)

    def update_definition(self, key: str, data: dict, *, is_platform_admin: bool) -> PhaseDefinition:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_DEFINITION)
        defn = self.get_definition(key)
        for field, value in data.items():
            setattr(defn, field, value)
        return self._repo.update_definition(key, defn)

    def get_sequences_for_definition(self, key: str) -> list:
        self.get_definition(key)
        return self._repo.get_sequences_for_definition(key)

    def get_species_for_definition(self, key: str) -> list[dict]:
        """List all species (global catalog) that traverse a phase definition (FIX-01 R5/R9).

        Composed from existing repository building blocks: every sequence that uses the
        definition (``get_sequences_for_definition``) → the species linked to each
        sequence (``get_species_for_sequence``), de-duplicated by species key. Per
        species the phase's typical duration is the ``PhaseSequenceEntry`` override for
        this definition in that species' sequence when set, else the ``PhaseDefinition``
        default. A missing definition raises ``NotFoundError``; an empty species list is
        a valid result (no 404, R7).
        """
        defn = self.get_definition(key)
        default_days = defn.typical_duration_days
        result: dict[str, dict] = {}
        for seq in self._repo.get_sequences_for_definition(key):
            seq_key = seq.key or ""
            # Duration override this species' sequence declares for this definition (if any).
            override: int | None = None
            for entry in self._repo.get_entries_for_sequence(seq_key):
                if entry.phase_definition_key == key and entry.override_duration_days is not None:
                    override = entry.override_duration_days
                    break
            duration = override if override is not None else default_days
            for species in self._repo.get_species_for_sequence(seq_key):
                species_key = species.get("key")
                if not species_key:
                    continue
                existing = result.get(species_key)
                if existing is None:
                    result[species_key] = {
                        "key": species_key,
                        "scientific_name": species.get("scientific_name") or "",
                        "common_names": species.get("common_names") or [],
                        "typical_duration_days": duration,
                        "illustration": defn.illustration,
                    }
                elif override is not None and existing["typical_duration_days"] == default_days:
                    # Same species reached again via another sequence that DOES declare a
                    # species-specific override — prefer it over the definition default.
                    existing["typical_duration_days"] = duration
        return list(result.values())

    def delete_definition(self, key: str, *, is_platform_admin: bool) -> bool:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_DEFINITION)
        defn = self.get_definition(key)
        if defn.is_system:
            raise ValidationError("Cannot delete system phase definitions.")
        usage_count = self._repo.get_definition_usage_count(key)
        if usage_count > 0:
            raise ValidationError(
                f"Cannot delete phase definition '{defn.name}': still referenced by {usage_count} sequence entries.",
            )
        return self._repo.delete_definition(key)

    # ── PhaseSequence CRUD ──

    def get_sequence_by_species(self, species_key: str) -> PhaseSequence | None:
        return self._repo.get_sequence_by_species(species_key)

    def get_species_for_sequence(self, key: str) -> list[dict]:
        """List the species bound to a sequence — the reverse lookup (issue #949).

        This is what turns "this one plant looks wrong" into "a whole cohort sits on
        the wrong template": seeing *Yucca gigantea* bucketed with Rosenkohl and
        Porree is a systemic finding, not a per-plant complaint.

        An unknown sequence raises ``NotFoundError``; an empty species list is a
        valid result, mirroring :meth:`get_species_for_definition`.
        """
        self.get_sequence(key)
        return self._repo.get_species_for_sequence(key)

    def list_sequences(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PhaseSequence], int]:
        return self._repo.get_all_sequences(offset, limit)

    def get_sequence(self, key: str) -> PhaseSequence:
        seq = self._repo.get_sequence_by_key(key)
        if not seq:
            raise NotFoundError("PhaseSequence", key)
        return seq

    def get_full_sequence(self, key: str) -> dict:
        """Return sequence data with entries and resolved phase definitions."""
        seq = self.get_sequence(key)
        entries = self._repo.get_entries_for_sequence(key)

        enriched_entries = []
        for entry in entries:
            entry_dict = entry.model_dump()
            defn = self._repo.get_definition_by_key(entry.phase_definition_key)
            if defn:
                entry_dict["phase_definition"] = defn.model_dump()
                entry_dict["effective_duration_days"] = (
                    entry.override_duration_days
                    if entry.override_duration_days is not None
                    else defn.typical_duration_days
                )
            else:
                entry_dict["phase_definition"] = None
                entry_dict["effective_duration_days"] = entry.override_duration_days or 1
            enriched_entries.append(entry_dict)

        return {
            **seq.model_dump(),
            "entries": enriched_entries,
        }

    def create_sequence(self, seq: PhaseSequence, *, is_platform_admin: bool) -> PhaseSequence:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_SEQUENCE)
        return self._repo.create_sequence(seq)

    def update_sequence(self, key: str, data: dict, *, is_platform_admin: bool) -> PhaseSequence:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_SEQUENCE)
        seq = self.get_sequence(key)
        for field, value in data.items():
            setattr(seq, field, value)
        updated = self._repo.update_sequence(key, seq)
        # ``species_key`` is not just document metadata: the lifecycle engine resolves
        # a species to its sequence through the ``HAS_PHASE_SEQUENCE`` edge, which
        # ``create_sequence`` builds from this same field. Writing the field without
        # re-pointing the edge was the #1099 silent drop — a 200 that bound nothing.
        # Re-point the edge whenever the caller supplies a non-empty species_key so
        # the binding is genuinely applied end-to-end (partially resolves #949).
        if data.get("species_key"):
            self._repo.set_species_sequence(data["species_key"], key)
        return updated

    def clone_sequence(self, source_key: str, new_name: str, *, is_platform_admin: bool) -> PhaseSequence:
        """Clone a phase sequence (metadata + ordered entries) into an editable copy.

        The clone is always editable (``is_system=False``), so a derived lifecycle
        can be built from a read-only system sequence without rebuilding every phase
        entry by hand. Raises ``NotFoundError`` if the source is missing.

        The docstring used to call the clone "tenant-owned". It never was:
        :class:`~app.domain.models.phase_sequence.PhaseSequence` carries no
        ``tenant_key``, so the copy lands in the same installation-wide catalogue
        as its source and is visible to every tenant. That sentence is why cloning
        looked like a tenant-local operation and stayed ungated; the clone is a
        global create and is gated as one (#1501).
        """
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_SEQUENCE)
        self.get_sequence(source_key)  # ensure the source exists (404 otherwise)
        return self._repo.clone_sequence(source_key, new_name)

    def delete_sequence(self, key: str, *, is_platform_admin: bool) -> bool:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_SEQUENCE)
        seq = self.get_sequence(key)
        if seq.is_system:
            raise ValidationError("Cannot delete system phase sequences.")
        usage_count = self._repo.get_sequence_usage_count(key)
        if usage_count > 0:
            raise ValidationError(
                f"Cannot delete phase sequence '{seq.name}': "
                f"still referenced by {usage_count} workflows or lifecycle configs.",
            )
        return self._repo.delete_sequence(key)

    # ── PhaseSequenceEntry CRUD ──

    def get_entries(self, seq_key: str) -> list[PhaseSequenceEntry]:
        self.get_sequence(seq_key)  # ensure sequence exists
        return self._repo.get_entries_for_sequence(seq_key)

    def get_entry(self, key: str) -> PhaseSequenceEntry:
        entry = self._repo.get_entry_by_key(key)
        if not entry:
            raise NotFoundError("PhaseSequenceEntry", key)
        return entry

    def create_entry(self, entry: PhaseSequenceEntry, *, is_platform_admin: bool) -> PhaseSequenceEntry:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_ENTRY)
        # Validate references exist
        self.get_sequence(entry.phase_sequence_key)
        self.get_definition(entry.phase_definition_key)
        return self._repo.create_entry(entry)

    def update_entry(self, key: str, data: dict, *, is_platform_admin: bool) -> PhaseSequenceEntry:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_ENTRY)
        entry = self.get_entry(key)
        # Validate new references if provided
        if "phase_definition_key" in data:
            self.get_definition(data["phase_definition_key"])
        for field, value in data.items():
            setattr(entry, field, value)
        return self._repo.update_entry(key, entry)

    def delete_entry(self, key: str, *, is_platform_admin: bool) -> bool:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_ENTRY)
        self.get_entry(key)  # ensure exists
        return self._repo.delete_entry(key)

    def reorder_entries(
        self,
        seq_key: str,
        orders: list[dict],
        *,
        is_platform_admin: bool,
    ) -> list[PhaseSequenceEntry]:
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=_ENTRY)
        self.get_sequence(seq_key)  # ensure sequence exists
        return self._repo.reorder_entries(seq_key, orders)
