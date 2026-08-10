"""#1090 acceptance-4: the global cultivar write paths stay global (tenant_key == "").

The Cultivar pendant of ``test_seed_species_global_tenant_key.py``. Two paths build
``Cultivar`` records without an interactive caller and must therefore never bind one
to a tenant:

* :func:`app.migrations.cultivar_seed.build_cultivar` — the single source of truth
  every plant seeder (``seed_data``, ``seed_plant_info``,
  ``seed_plant_info_extended``, ``seed_adventskalender``) uses to turn a YAML
  cultivar entry into a model;
* the CSV import create path in :class:`ImportService`.

Both inherit the model default ``tenant_key == ""`` — the global/system catalogue
every tenant may read. This guards that they stay *global* write paths: a stamp
appearing here would move seeded master data into one tenant's catalogue and out of
everyone else's, and (for the seed loader) would do so on every boot.

The seed-YAML direction is closed structurally as well: ``tenant_key`` is absent
from the cultivar seed schema and listed in ``_CULTIVAR_MODEL_RUNTIME_ONLY``
(``test_seed_schema_conformance.py``), so a data file cannot introduce one.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.common.enums import EntityType
from app.domain.services.import_service import ImportService
from app.migrations.cultivar_seed import build_cultivar


def test_seed_build_cultivar_is_global_tenant_key_empty():
    cultivar = build_cultivar({"name": "Genovese", "breeder": "Seed Co"}, "sp_basil")

    assert cultivar.tenant_key == ""


def test_seed_build_cultivar_cannot_be_given_an_owner_by_the_yaml_entry():
    # A stray ``tenant_key`` in a data file must be inert: the builder maps an
    # explicit field list and never splats the entry into the model.
    cultivar = build_cultivar({"name": "Genovese", "tenant_key": "tenant_42"}, "sp_basil")

    assert cultivar.tenant_key == ""


def test_csv_import_creates_global_cultivars():
    species_repo = MagicMock()
    service = ImportService(MagicMock(), species_repo=species_repo, family_repo=MagicMock())

    create_fn = service._get_create_fn(EntityType.CULTIVAR)
    create_fn({"species_key": "sp_basil", "cultivar_name": "Genovese", "breeder": "", "traits": ""})

    created = species_repo.create_cultivar.call_args[0][0]
    assert created.tenant_key == ""
