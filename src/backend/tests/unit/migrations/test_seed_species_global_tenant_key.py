"""F-3/#808 acceptance-3: the seed path builds species as global (tenant_key == "").

The plant-info seed loader constructs ``Species`` models straight from the YAML
catalogue and never binds them to a tenant, so they inherit the model default
``tenant_key == ""`` (the global/system catalogue every tenant reads). This guards
that the seed path stays a *global* write path and never accidentally stamps an
owner onto seeded master data.
"""

from __future__ import annotations

from app.migrations.seed_plant_info import _build_species


def test_seed_build_species_is_global_tenant_key_empty():
    species_list = _build_species({"new_species": [{"scientific_name": "Rosa canina"}]})

    assert len(species_list) == 1
    assert species_list[0].tenant_key == ""
