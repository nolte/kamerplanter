"""REQ-033 curated MCP tool palette (§2).

Importing this package registers every tool with the global registry via the
``@mcp_tool`` decorator. Keep the imports side-effecting and explicit so the
palette is deterministic.

Cut-1 core palette (extensible — see the PR/report for the deferred remainder of
the ~30-tool inventory in §2):

* read (mcp.read):  list_tenants, list_species, get_species_info,
  list_plants, get_plant, list_plants_at_location, get_plant_care_log,
  list_planting_runs, list_tasks, get_due_care_tasks, get_harvest_readiness,
  list_nutrient_plans, get_nutrient_plan, get_plant_nutrient_plan,
  get_sowing_calendar, list_fertilizers, calculate_mixing_protocol,
  list_pests, get_pest, list_diseases, get_disease, get_treatment,
  get_plant_inspections, get_mcp_activity
* write (mcp.write): confirm_care_task, archive_plant, set_plant_location
* setup (mcp.setup): create_site

Tools whose ``Input`` extends ``TenantToolInput`` act inside one tenant, which
the dispatcher binds per call; the rest (``list_tenants``, the species
catalogue, ``get_mcp_activity``) read data that carries no tenant.
"""

from __future__ import annotations

from app.mcp_server.tools import (  # noqa: F401  (side-effect registration)
    calendar,
    care,
    harvest,
    ipm,
    nutrient_calc,
    nutrition,
    plant_reads,
    plants,
    privacy,
    runs,
    sites,
    species,
    tasks,
    tenants,
)
