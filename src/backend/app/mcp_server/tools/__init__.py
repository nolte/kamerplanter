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
  get_plant_inspections, list_cultivars, get_cultivar, list_substrates,
  list_overwintering_profiles, list_starter_kits, list_phase_definitions,
  list_hardiness_zones, search_glossary, get_mcp_activity,
  list_pending_diary_analyses, get_diary_entry, get_diary_entry_photos
* write (mcp.write): confirm_care_task, archive_plant, set_plant_location,
  claim_diary_analysis, submit_diary_analysis
* setup (mcp.setup): create_site

The five ``*_diary_*`` tools (REQ-050 §4, REQ-033 §2.2a) are the complete
contract for the external analysis agent in the separate ``kamerplanter-goose``
repository; ``get_diary_entry_photos`` is the only tool in the palette that
returns something other than text (REQ-033 §4.3b).

Tools whose ``Input`` extends ``TenantToolInput`` act inside one tenant, which
the dispatcher binds per call; the rest (``list_tenants``, the species
catalogue, ``get_mcp_activity``) read data that carries no tenant.
"""

from __future__ import annotations

from app.mcp_server.tools import (  # noqa: F401  (side-effect registration)
    calendar,
    care,
    catalogs,
    diary,
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
