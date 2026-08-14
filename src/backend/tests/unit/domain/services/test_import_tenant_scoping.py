"""The CSV import is ownership-stamped and role-gated like the routes it shadows (#1110).

`ImportService` writes the *same* master-data rows as `POST /api/v1/species`,
`POST /api/v1/botanical-families` and their PUT siblings — but reached the
repository by a different door, and that door had no lock on it. Rows were built
with the model default ``tenant_key = ''`` (**global**) and written
repository-direct, so any authenticated caller, a viewer of a shared tenant
included, could inject master data into the catalogue every tenant reads, and
could not remove it afterwards: deleting a global row has required a platform
admin since #1109.

Each test here is written to fail against the pre-#1110 service — that is the
point of the file. The two that matter most are the ones nobody would write from
the issue title alone:

  * :func:`test_update_strategy_refuses_overwriting_a_global_row` — the *update*
    duplicate strategy was the sharper hole. Creating rows pollutes the shared
    catalogue; ``duplicate_strategy=UPDATE`` **overwrites seeded rows in place**,
    and it did so with no ownership check whatsoever.
  * :func:`test_system_context_import_stays_global_and_ungated` — the falsifiability
    counterpart. A gate that also stopped the seeders would be a regression wearing
    a security fix's clothes, so the ungated system path is pinned explicitly.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import DataOrigin, DuplicateStrategy, EntityType, ImportJobStatus, TenantRole
from app.common.exceptions import ForbiddenError, ValidationError
from app.config.settings import settings
from app.domain.models.import_job import ImportJob
from app.domain.models.species import Cultivar, Species
from app.domain.services.import_service import ImportService

_TENANT = "tenant_acme"

_SPECIES_ROW = {"scientific_name": "Rosa canina", "common_name": "Dog rose"}
_CULTIVAR_ROW = {"species_key": "sp_rosa", "cultivar_name": "Alba"}


def _service() -> tuple[ImportService, MagicMock, MagicMock]:
    species_repo = MagicMock()
    family_repo = MagicMock()
    family_repo.get_by_name.return_value = None
    return ImportService(MagicMock(), species_repo=species_repo, family_repo=family_repo), species_repo, family_repo


def _staged_job(entity_type: EntityType, strategy: DuplicateStrategy = DuplicateStrategy.SKIP) -> ImportJob:
    """A job in the one status `confirm` accepts, so the gate is what rejects — not the status."""
    return ImportJob(
        entity_type=entity_type,
        status=ImportJobStatus.PREVIEW_READY,
        filename="rows.csv",
        duplicate_strategy=strategy,
    )


def _confirming(svc: ImportService, job: ImportJob) -> MagicMock:
    """Wire the job repository so `confirm` loads ``job`` and applies zero rows.

    The row set is empty on purpose: every test here is about the *decision*
    `confirm` makes before applying anything, and an empty job keeps a refusal
    unambiguous — nothing could have been written even if the gate had passed.
    """
    svc._repo.get_or_raise.return_value = job
    return svc._repo


# ── Ownership stamp: an imported row belongs to the importing tenant ──────────


def test_species_import_is_stamped_with_the_importing_tenant():
    svc, species_repo, _ = _service()

    svc._get_create_fn(EntityType.SPECIES, tenant_key=_TENANT)(_SPECIES_ROW)

    species: Species = species_repo.upsert_by_normalized_scientific_name.call_args[0][0]
    assert species.tenant_key == _TENANT
    # The pin the issue asks for, stated as the property rather than the value:
    # a tenant caller's import must never mint a row in the global catalogue.
    assert species.tenant_key != ""


def test_cultivar_import_is_stamped_with_the_importing_tenant():
    svc, species_repo, _ = _service()

    svc._get_create_fn(EntityType.CULTIVAR, tenant_key=_TENANT)(_CULTIVAR_ROW)

    cultivar: Cultivar = species_repo.create_cultivar.call_args[0][0]
    assert cultivar.tenant_key == _TENANT
    assert cultivar.tenant_key != ""


def test_imported_rows_are_editable_by_the_tenant_that_imported_them():
    """Ownership without matching provenance would be a half-fix.

    `origin=SYSTEM` is what the UI reads to render a record read-only. A row
    stamped with a tenant but left at the model's SYSTEM default would sit in the
    importing tenant's catalogue *uneditable and undeletable by its own owner* —
    passing a `tenant_key` assertion while failing the user.
    """
    svc, species_repo, _ = _service()

    svc._get_create_fn(EntityType.SPECIES, tenant_key=_TENANT)(_SPECIES_ROW)

    species: Species = species_repo.upsert_by_normalized_scientific_name.call_args[0][0]
    assert species.origin == DataOrigin.TENANT


def test_update_strategy_fallback_create_is_stamped_too():
    """The update path mints rows as well — via its vanished-duplicate fallback."""
    svc, species_repo, _ = _service()
    species_repo.get_by_scientific_name.return_value = None

    svc._get_update_fn(EntityType.SPECIES, tenant_key=_TENANT, caller_role=TenantRole.GROWER)(_SPECIES_ROW)

    species: Species = species_repo.upsert_by_normalized_scientific_name.call_args[0][0]
    assert species.tenant_key == _TENANT


# ── Role gate: a viewer may not import master data ────────────────────────────


@pytest.mark.parametrize("entity_type", [EntityType.SPECIES, EntityType.CULTIVAR])
def test_viewer_may_not_confirm_a_master_data_import(entity_type):
    svc, _, _ = _service()
    _confirming(svc, _staged_job(entity_type))

    with pytest.raises(ForbiddenError):
        svc.confirm("job1", tenant_key=_TENANT, caller_role=TenantRole.VIEWER)


@pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
def test_a_writing_role_may_confirm(role):
    """The gate must admit the roles that legitimately curate master data.

    Without this the suite would pass just as well against a service that refuses
    *everyone* — the failure mode a one-sided permission test cannot see.
    """
    svc, _, _ = _service()
    _confirming(svc, _staged_job(EntityType.SPECIES))

    svc.confirm("job1", tenant_key=_TENANT, caller_role=role)


def test_platform_admin_may_confirm_despite_a_viewer_rank():
    """Light-mode curation (REQ-027) rides on the platform-admin bypass, not on rank."""
    svc, _, _ = _service()
    _confirming(svc, _staged_job(EntityType.SPECIES))

    svc.confirm("job1", tenant_key=_TENANT, caller_role=TenantRole.VIEWER, is_platform_admin=True)


# ── Botanical families are global-only: platform admin or nothing ─────────────


def test_family_import_refuses_a_non_admin():
    """The import was the unlocked back door of the gate #1120 fitted to the router.

    `BotanicalFamily` carries no ``tenant_key``, so there is no tenant to import
    one into — the interactive POST answers 403 for a non-admin, and this path
    writes the identical rows.
    """
    svc, _, _ = _service()
    _confirming(svc, _staged_job(EntityType.BOTANICAL_FAMILY))

    with pytest.raises(ForbiddenError):
        svc.confirm("job1", tenant_key=_TENANT, caller_role=TenantRole.LEAD)


def test_family_import_admits_a_platform_admin():
    svc, _, _ = _service()
    _confirming(svc, _staged_job(EntityType.BOTANICAL_FAMILY))

    svc.confirm("job1", tenant_key=_TENANT, caller_role=TenantRole.LEAD, is_platform_admin=True)


# ── The sharper hole: UPDATE overwrites rows that already exist ───────────────


def test_update_strategy_refuses_overwriting_a_global_row():
    """A non-admin must not rewrite the shared seed catalogue through an import.

    `duplicate_strategy=UPDATE` resolves an existing record by its natural key and
    writes the CSV's columns onto it. Pointed at a seeded species — every tenant
    reads those — it was an unauthenticated-in-effect edit of global reference
    data, and strictly worse than the create hole the issue title names: creating
    adds a row somebody can ignore, this one *changes* a row everybody already
    depends on.
    """
    svc, species_repo, _ = _service()
    species_repo.get_by_scientific_name.return_value = Species(
        key="sp_seeded", scientific_name="Rosa canina", tenant_key=""
    )

    update_fn = svc._get_update_fn(EntityType.SPECIES, tenant_key=_TENANT, caller_role=TenantRole.LEAD)

    with pytest.raises(ForbiddenError):
        update_fn(_SPECIES_ROW)
    species_repo.update.assert_not_called()


def test_update_strategy_hides_a_foreign_tenants_row_behind_404():
    """Ownership hiding, identical to `PUT /species/{key}`: never confirm it exists."""
    from app.common.exceptions import NotFoundError

    svc, species_repo, _ = _service()
    species_repo.get_by_scientific_name.return_value = Species(
        key="sp_other", scientific_name="Rosa canina", tenant_key="tenant_other"
    )

    update_fn = svc._get_update_fn(EntityType.SPECIES, tenant_key=_TENANT, caller_role=TenantRole.LEAD)

    with pytest.raises(NotFoundError):
        update_fn(_SPECIES_ROW)
    species_repo.update.assert_not_called()


def test_update_strategy_allows_the_caller_to_rewrite_its_own_row():
    svc, species_repo, _ = _service()
    species_repo.get_by_scientific_name.return_value = Species(
        key="sp_own", scientific_name="Rosa canina", tenant_key=_TENANT
    )

    svc._get_update_fn(EntityType.SPECIES, tenant_key=_TENANT, caller_role=TenantRole.GROWER)(_SPECIES_ROW)

    species_repo.update.assert_called_once()


# ── No active tenant: refuse rather than fall back to a global stamp ──────────


def test_full_mode_import_without_an_active_tenant_is_refused(monkeypatch):
    """SEC-004 (#808), transplanted: an unresolvable tenant must not become "global".

    The species router already answers 422 here. Falling back to ``""`` instead
    would hand the shared catalogue exactly the write this issue closes, by the
    quietest route available — a caller with no tenant context at all.
    """
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    svc, _, _ = _service()
    _confirming(svc, _staged_job(EntityType.SPECIES))

    with pytest.raises(ValidationError):
        svc.confirm("job1", tenant_key="", caller_role=TenantRole.LEAD)


# ── Falsifiability: the seeders must keep working ─────────────────────────────


def test_system_context_import_stays_global_and_ungated():
    """No HTTP caller → no role → no gate, and the row is genuinely global.

    Seeders, migrations and the enrichment paths import master data with no
    caller at all; ``caller_role is None`` is the same system-context escape
    `_authorize_tenant_owned_create` already grants them. A gate that also
    refused these would be a regression dressed as a security fix — and it is a
    real risk here, because the *natural* implementation (gate everything, stamp
    everything) breaks them silently at seed time rather than loudly in a test.
    """
    svc, species_repo, _ = _service()
    _confirming(svc, _staged_job(EntityType.SPECIES))

    svc.confirm("job1")  # no tenant, no role — must not raise

    svc._get_create_fn(EntityType.SPECIES)(_SPECIES_ROW)
    species: Species = species_repo.upsert_by_normalized_scientific_name.call_args[0][0]
    assert species.tenant_key == ""
    assert species.origin == DataOrigin.SYSTEM
