import re

from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus
from app.common.exceptions import ValidationError
from app.domain.engines.csv_parser import CsvParser
from app.domain.engines.import_engine import ImportEngine
from app.domain.engines.row_validator import RowValidator
from app.domain.interfaces.import_job_repository import IImportJobRepository
from app.domain.models.import_job import ImportJob
from app.domain.services.phase_sequence_binder import PhaseSequenceBinder


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

    def confirm(self, key: str) -> ImportJob:
        job = self.get_job(key)
        if job.status != ImportJobStatus.PREVIEW_READY:
            raise ValidationError(f"Job must be in PREVIEW_READY status, got {job.status}")

        create_fn = self._get_create_fn(job.entity_type)
        # The "update" duplicate strategy only takes effect when an update_fn is
        # supplied; otherwise the engine can only create/skip/fail duplicates.
        update_fn = None
        if job.duplicate_strategy == DuplicateStrategy.UPDATE:
            update_fn = self._get_update_fn(job.entity_type)
        job = self._engine.confirm_import(job, create_fn, update_fn=update_fn)
        return self._repo.update(key, job)

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

    def _get_create_fn(self, entity_type: EntityType):
        if entity_type == EntityType.SPECIES and self._species_repo:
            from app.domain.models.species import Species

            def create_species(data: dict):
                species = Species(
                    scientific_name=data["scientific_name"],
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

    def _get_update_fn(self, entity_type: EntityType):
        """Return an update function for the "update" duplicate strategy.

        The engine only invokes ``update_fn(row)`` for DUPLICATE rows, so each
        function looks up the existing record by its natural key and mutates only
        the columns present in the CSV row (empty cells never clobber existing
        data). Returns ``None`` when the entity has no repository wired.
        """
        if entity_type == EntityType.SPECIES and self._species_repo:

            def update_species(data: dict):
                existing = self._species_repo.get_by_scientific_name(data["scientific_name"])
                if existing is None:
                    # Duplicate flagged at preview time but gone now — create instead.
                    from app.domain.models.species import Species

                    # SEC-003: still route the fallback create through the atomic
                    # dedup UPSERT so a normalized-duplicate never slips in here.
                    created = self._species_repo.upsert_by_normalized_scientific_name(
                        Species(
                            scientific_name=data["scientific_name"],
                            **_species_fields_from_row(data, self._family_repo),
                        )
                    )
                    self._bind_phase_sequence(created)
                    return
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
