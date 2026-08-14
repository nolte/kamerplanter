import re

from app.common.enums import DataOrigin, DuplicateStrategy, EntityType, ImportJobStatus, TenantRole
from app.common.exceptions import ValidationError
from app.config.settings import settings
from app.domain.engines.csv_parser import CsvParser
from app.domain.engines.import_engine import ImportEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.row_validator import RowValidator
from app.domain.interfaces.import_job_repository import IImportJobRepository
from app.domain.models.import_job import ImportJob
from app.domain.services.catalogue_authorization import require_platform_admin_for_global_catalogue
from app.domain.services.phase_sequence_binder import PhaseSequenceBinder

# Imported by their private names on purpose: these are the *same* two decisions
# `SpeciesService` runs for the interactive routes, and #1110 exists because the
# import had its own (absent) answer. A public re-export or a local copy would
# reintroduce exactly the second opinion the issue is about — the underscore is
# the honest marker that this module is reaching into a sibling's rule rather
# than owning one.
from app.domain.services.species_service import (  # noqa: PLC2701
    _authorize_tenant_owned_create,
    _authorize_tenant_owned_write,
)


class ImportService:
    def __init__(
        self,
        import_repo: IImportJobRepository,
        species_repo=None,
        family_repo=None,
        phase_sequence_binder: PhaseSequenceBinder | None = None,
    ) -> None:
        self._repo = import_repo
        self._species_repo = species_repo
        self._family_repo = family_repo
        # A CSV import mints species exactly like create_species does, so it owes them
        # the same phase-sequence binding (#1006). Optional, so existing constructions
        # keep working and simply do not bind.
        self._phase_sequence_binder = phase_sequence_binder
        self._parser = CsvParser()
        self._validator = RowValidator()
        self._engine = ImportEngine(self._parser, self._validator)

    def upload(
        self,
        file_bytes: bytes,
        entity_type: EntityType,
        filename: str,
        duplicate_strategy: DuplicateStrategy = DuplicateStrategy.SKIP,
        uploaded_by: str = "",
    ) -> ImportJob:
        existing_keys = self._get_existing_keys(entity_type)
        job = self._engine.upload_and_validate(
            file_bytes,
            entity_type,
            filename,
            duplicate_strategy,
            existing_keys,
        )
        job.uploaded_by = uploaded_by
        return self._repo.save(job)

    def get_job(self, key: str) -> ImportJob:
        job = self._repo.get_or_raise(key)
        return job

    def list_jobs(self, offset: int = 0, limit: int = 50) -> tuple[list[ImportJob], int]:
        return self._repo.list_all(offset, limit)

    def confirm(
        self,
        key: str,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> ImportJob:
        """Apply a staged import job's rows, ownership-stamped and role-gated (#1110).

        This is the write half of the import; :meth:`upload` only stages rows for
        preview and touches no master data. The three keyword arguments are the
        same triple the interactive catalogue routes carry, and they arrive from
        the same resolver — :func:`~app.common.auth.get_active_tenant_context` —
        so an imported row and a hand-created one land in the same tenant with the
        same permission answer. They default to the **system context**
        (``caller_role is None``, no gate, global stamp), which is what keeps the
        seeders, migrations and existing tests importing without an HTTP caller;
        every HTTP call passes a real role.

        Before #1110 there was no such context at all: ``ImportService`` built
        entities with the model default ``tenant_key = ''`` — *global* — and wrote
        them repository-direct. So any authenticated user, a viewer of a shared
        tenant included, could inject rows into the catalogue every tenant reads,
        via ``POST /api/v1/import/upload`` + confirm. Worse, they could not undo
        it: deleting a global row has required a platform admin since #1109. The
        import was the unlocked back door of the gates #1109/#1113/#1120 fitted to
        the front.
        """
        job = self.get_job(key)
        if job.status != ImportJobStatus.PREVIEW_READY:
            raise ValidationError(f"Job must be in PREVIEW_READY status, got {job.status}")

        self._authorize_confirm(
            job.entity_type,
            tenant_key=tenant_key,
            caller_role=caller_role,
            is_platform_admin=is_platform_admin,
        )

        create_fn = self._get_create_fn(job.entity_type, tenant_key=tenant_key)
        # The "update" duplicate strategy only takes effect when an update_fn is
        # supplied; otherwise the engine can only create/skip/fail duplicates.
        update_fn = None
        if job.duplicate_strategy == DuplicateStrategy.UPDATE:
            update_fn = self._get_update_fn(
                job.entity_type,
                tenant_key=tenant_key,
                caller_role=caller_role,
                is_platform_admin=is_platform_admin,
            )
        job = self._engine.confirm_import(job, create_fn, update_fn=update_fn)
        return self._repo.update(key, job)

    def _authorize_confirm(
        self,
        entity_type: EntityType,
        *,
        tenant_key: str | None,
        caller_role: TenantRole | None,
        is_platform_admin: bool,
    ) -> None:
        """Decide whether this caller may apply an import of ``entity_type``.

        Two different answers, because the two catalogues have different shapes:

        * **Species and cultivars** are a *hybrid* catalogue — a row can be
          tenant-owned — so the rule is the ordinary tenant-owned create gate, and
          this calls the very function ``SpeciesService.create_species`` calls
          rather than restating it. A viewer is refused; a grower or lead may
          import into their own tenant.
        * **Botanical families** are global-*only*: the model carries no
          ``tenant_key``, so there is no tenant to import them into and no
          ownership arm to fall back on. The only honest answer is the one the
          interactive route already gives — platform admin, or 403.

        Ordering mirrors ``create_species`` in the species router: the "no active
        tenant" refusal wins over the role refusal, because with no resolvable
        tenant ``caller_role`` is the fail-safe VIEWER *default* rather than a
        standing anyone assigned, and answering 403 would report a role nobody
        holds.
        """
        if entity_type == EntityType.BOTANICAL_FAMILY:
            # System context (seeders, migrations) passes no role and stays ungated,
            # exactly as `_authorize_tenant_owned_create` leaves it ungated.
            if caller_role is not None:
                require_platform_admin_for_global_catalogue(
                    is_platform_admin=is_platform_admin, entity="botanical family"
                )
            return

        if entity_type not in (EntityType.SPECIES, EntityType.CULTIVAR):
            return

        # SEC-004 (#808), transplanted from the species router: in full mode a
        # tenant-owned create with no resolvable active tenant must not be stamped
        # global. `caller_role is not None` narrows this to HTTP callers — the
        # router's own guard needs no such condition because nothing but HTTP
        # reaches it, whereas this service is also the seeders' entry point.
        if caller_role is not None and settings.kamerplanter_mode == "full" and not tenant_key:
            raise ValidationError("Cannot import tenant-owned master data without an active tenant.")

        _authorize_tenant_owned_create(
            plural_noun="species" if entity_type == EntityType.SPECIES else "cultivars",
            caller_role=caller_role,
            is_platform_admin=is_platform_admin,
        )

    def delete_job(self, key: str) -> bool:
        self.get_job(key)
        return self._repo.delete(key)

    def get_template(self, entity_type: EntityType) -> str:
        return self._parser.get_template(entity_type)

    def _bind_phase_sequence(self, species) -> None:
        """Bind an imported species to its default phase sequence (#1006).

        Best-effort by construction: the binder swallows its own failures, and a
        missing binder (older construction, tests) simply skips. An import must not
        fail a row over master data the row never carried.
        """
        if self._phase_sequence_binder is not None and species is not None:
            self._phase_sequence_binder.bind_default(species)

    def _get_existing_keys(self, entity_type: EntityType) -> set[str]:
        if entity_type == EntityType.SPECIES and self._species_repo:
            docs, _ = self._species_repo.get_all(0, 10000)
            return {
                d.get("scientific_name", d.get("_key", ""))
                if isinstance(d, dict)
                else getattr(d, "scientific_name", "")
                for d in docs
            }
        if entity_type == EntityType.BOTANICAL_FAMILY and self._family_repo:
            docs, _ = self._family_repo.get_all(0, 10000)
            return {d.get("name", d.get("_key", "")) if isinstance(d, dict) else getattr(d, "name", "") for d in docs}
        return set()

    @staticmethod
    def _owner_stamp(tenant_key: str | None) -> tuple[str, DataOrigin]:
        """Return the ``(tenant_key, origin)`` an imported row is created with (#1110).

        ``tenant_key is None`` is the system context (seeders, migrations): those
        rows really are global reference data, and ``""`` is the model default they
        already carried. An HTTP caller always brings a resolved key — or was
        refused by :meth:`_authorize_confirm` before reaching here.

        The provenance travels with the ownership rather than being decided
        separately, because the two must agree: a tenant-owned row marked
        ``origin=SYSTEM`` is rendered read-only by the UI, so the importing tenant
        could not edit or delete what it had just created. One function, so the
        create path and the update path's create-fallback cannot drift apart on it.
        """
        owner_key = tenant_key or ""
        return owner_key, DataOrigin.TENANT if owner_key else DataOrigin.SYSTEM

    def _get_create_fn(self, entity_type: EntityType, *, tenant_key: str | None = None):
        owner_key, origin = self._owner_stamp(tenant_key)

        if entity_type == EntityType.SPECIES and self._species_repo:
            from app.domain.models.species import Species

            def create_species(data: dict):
                species = Species(
                    scientific_name=data["scientific_name"],
                    tenant_key=owner_key,
                    origin=origin,
                    **_species_fields_from_row(data, self._family_repo),
                )
                # REQ-048 Stufe 1 / SEC-003: route through the atomic dedup UPSERT
                # instead of a plain insert. A plain create() only trips the exact-
                # name unique index, so a normalized-duplicate (differing only by
                # the hybrid marker × vs x, casing or whitespace) would be inserted
                # as a second row. The UPSERT resolves onto the existing record.
                created = self._species_repo.upsert_by_normalized_scientific_name(species)
                self._bind_phase_sequence(created)

            return create_species

        if entity_type == EntityType.CULTIVAR and self._species_repo:
            from app.domain.models.species import Cultivar

            def create_cultivar(data: dict):
                cultivar = Cultivar(
                    species_key=data["species_key"],
                    name=data["cultivar_name"],
                    tenant_key=owner_key,
                    origin=origin,
                    **_cultivar_fields_from_row(data),
                )
                self._species_repo.create_cultivar(cultivar)

            return create_cultivar

        if entity_type == EntityType.BOTANICAL_FAMILY and self._family_repo:
            from app.domain.models.botanical_family import BotanicalFamily

            def create_family(data: dict):
                family = BotanicalFamily(
                    name=data["name"],
                    common_name=data.get("common_name", ""),
                    order_name=data.get("order_name", ""),
                    description=data.get("description", ""),
                )
                self._family_repo.create(family)

            return create_family

        def noop(data: dict):
            pass

        return noop

    def _get_update_fn(
        self,
        entity_type: EntityType,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ):
        """Return an update function for the "update" duplicate strategy.

        The engine only invokes ``update_fn(row)`` for DUPLICATE rows, so each
        function looks up the existing record by its natural key and mutates only
        the columns present in the CSV row (empty cells never clobber existing
        data). Returns ``None`` when the entity has no repository wired.

        Ownership-gated per row since #1110, and this arm was the sharper hole of
        the two: ``_authorize_confirm`` decides whether the caller may *create*
        master data, but ``duplicate_strategy=UPDATE`` writes rows that already
        exist — including the **global seed catalogue** every tenant reads. Any
        authenticated user could therefore upload a CSV naming a seeded species
        and overwrite its fields wholesale. The gate here is the same
        :func:`~app.domain.services.species_service._authorize_tenant_owned_write`
        the interactive ``PUT /species/{key}`` runs, so an import and an edit form
        answer identically: foreign row → 404, global row → platform admin only,
        own row → writing role required.
        """
        owner_key, origin = self._owner_stamp(tenant_key)

        if entity_type == EntityType.SPECIES and self._species_repo:

            def update_species(data: dict):
                existing = self._species_repo.get_by_scientific_name(data["scientific_name"])
                if existing is None:
                    # Duplicate flagged at preview time but gone now — create instead.
                    from app.domain.models.species import Species

                    # SEC-003: still route the fallback create through the atomic
                    # dedup UPSERT so a normalized-duplicate never slips in here.
                    # Stamped exactly like the create path (#1110): this branch mints
                    # a row, so an unstamped one here would reopen the global-write
                    # hole through the back of the *update* strategy.
                    created = self._species_repo.upsert_by_normalized_scientific_name(
                        Species(
                            scientific_name=data["scientific_name"],
                            tenant_key=owner_key,
                            origin=origin,
                            **_species_fields_from_row(data, self._family_repo),
                        )
                    )
                    self._bind_phase_sequence(created)
                    return
                _authorize_tenant_owned_write(
                    existing,
                    existing.key or "",
                    entity="Species",
                    plural_noun="species",
                    tenant_key=tenant_key,
                    caller_role=caller_role,
                    is_platform_admin=is_platform_admin,
                    can_role_write=MembershipEngine.can_edit_resource,
                )
                for field, value in _species_fields_from_row(data, self._family_repo).items():
                    setattr(existing, field, value)
                self._species_repo.update(existing.key, existing)

            return update_species

        if entity_type == EntityType.BOTANICAL_FAMILY and self._family_repo:
            from app.domain.models.botanical_family import BotanicalFamily

            def update_family(data: dict):
                existing = self._family_repo.get_by_name(data["name"])
                if existing is None:
                    # Duplicate flagged at preview time but gone now — create instead.
                    self._family_repo.create(
                        BotanicalFamily(name=data["name"], description=data.get("description", ""))
                    )
                    return
                # description is the only free-text field the family template maps
                # to (common_name/order_name have no matching model field).
                if data.get("description"):
                    existing.description = data["description"]
                self._family_repo.update(existing.key, existing)

            return update_family

        # CULTIVAR duplicates are not detected by _get_existing_keys yet, so the
        # engine never reaches the update branch for them; no update_fn needed.
        return None


_BOOL_TRUE = frozenset({"true", "1", "yes", "ja", "y", "wahr", "x"})
_BOOL_FALSE = frozenset({"false", "0", "no", "nein", "n", "falsch"})


def _to_int(value: str | None) -> int | None:
    """Parse an integer from a CSV cell; empty/invalid → ``None`` (empty-tolerant)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _to_bool(value: str | None) -> bool | None:
    """Parse a boolean from a CSV cell; empty/unknown → ``None`` (keep model default)."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in _BOOL_TRUE:
        return True
    if text in _BOOL_FALSE:
        return False
    return None


def _species_fields_from_row(data: dict, family_repo=None) -> dict:
    """Map the SPECIES CSV template columns to ``Species`` model fields.

    Only ``scientific_name`` is required (handled by the caller); every other
    column is optional and empty-tolerant — an empty cell is simply omitted so
    the model default stays in place. Enum columns are pre-validated by
    ``RowValidator`` before a row is imported.

    Two template columns have no direct model field:
      * ``cycle_type`` — no matching ``Species`` field → intentionally dropped;
      * ``family_name`` — resolved to the referenced ``BotanicalFamily`` document
        via ``family_repo.get_by_name`` and stored as ``family_key`` (an ArangoDB
        ``_key``). When no family matches (or no ``family_repo`` is wired) the
        ``family_key`` is left unset rather than filled with the display name —
        writing the name into the ``_key``-typed field produced a dangling
        reference that ``crop_rotation_validator.get_by_key`` could never resolve,
        silently breaking the crop-rotation / companion family checks for
        imported species.
    """
    from app.common.enums import GrowthHabit, RootType, Suitability

    fields: dict = {}
    if data.get("common_name"):
        # Template column is singular; the model stores a list of common names.
        fields["common_names"] = [data["common_name"]]
    family_name = data.get("family_name")
    if family_name and family_repo is not None:
        family = family_repo.get_by_name(family_name)
        if family is not None and family.key:
            fields["family_key"] = family.key
    if data.get("growth_habit"):
        fields["growth_habit"] = GrowthHabit(data["growth_habit"].lower())
    if data.get("root_type"):
        fields["root_type"] = RootType(data["root_type"].lower())
    if data.get("description"):
        fields["description"] = data["description"]
    if data.get("container_suitable"):
        fields["container_suitable"] = Suitability(data["container_suitable"].lower())
    if data.get("recommended_container_volume_l"):
        fields["recommended_container_volume_l"] = data["recommended_container_volume_l"]
    depth = _to_int(data.get("min_container_depth_cm"))
    if depth is not None:
        fields["min_container_depth_cm"] = depth
    if data.get("mature_height_cm"):
        fields["mature_height_cm"] = data["mature_height_cm"]
    if data.get("mature_width_cm"):
        fields["mature_width_cm"] = data["mature_width_cm"]
    if data.get("spacing_cm"):
        fields["spacing_cm"] = data["spacing_cm"]
    if data.get("indoor_suitable"):
        fields["indoor_suitable"] = Suitability(data["indoor_suitable"].lower())
    if data.get("balcony_suitable"):
        fields["balcony_suitable"] = Suitability(data["balcony_suitable"].lower())
    greenhouse = _to_bool(data.get("greenhouse_recommended"))
    if greenhouse is not None:
        fields["greenhouse_recommended"] = greenhouse
    support = _to_bool(data.get("support_required"))
    if support is not None:
        fields["support_required"] = support
    return fields


def _cultivar_fields_from_row(data: dict) -> dict:
    """Map the optional CULTIVAR CSV template columns to ``Cultivar`` model fields.

    ``species_key`` and ``cultivar_name`` are required and handled by the caller.
    The ``description`` template column has no matching ``Cultivar`` field and is
    intentionally dropped. ``traits`` is a delimited list coerced to ``PlantTrait``
    values (unknown tokens are ignored).
    """
    from app.common.enums import PlantTrait

    fields: dict = {}
    if data.get("breeder"):
        fields["breeder"] = data["breeder"]
    if data.get("traits"):
        traits: list[PlantTrait] = []
        for raw in re.split(r"[,;|]", data["traits"]):
            token = raw.strip().lower()
            if not token:
                continue
            try:
                traits.append(PlantTrait(token))
            except ValueError:
                continue  # ignore unknown trait tokens rather than failing the row
        if traits:
            fields["traits"] = traits
    return fields
