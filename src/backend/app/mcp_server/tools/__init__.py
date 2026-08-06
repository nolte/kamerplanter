"""REQ-033 curated MCP tool palette (§2).

Importing this package registers every tool with the global registry via the
``@mcp_tool`` decorator. Keep the imports side-effecting and explicit so the
palette is deterministic.

Current palette (extensible — see the PR/report for the deferred remainder of
the inventory in §2):

* read (mcp.read):  list_tenants, list_species, get_species_info,
  list_plants, get_plant, list_plants_at_location, get_plant_care_log,
  get_plant_diagnostics, list_planting_runs, list_tasks, get_due_care_tasks,
  get_harvest_readiness, list_nutrient_plans, get_nutrient_plan,
  get_plant_nutrient_plan, get_sowing_calendar, list_fertilizers,
  calculate_mixing_protocol, list_pests, get_pest, list_diseases, get_disease,
  get_treatment, get_plant_inspections, list_cultivars, get_cultivar,
  list_substrates, list_overwintering_profiles, list_starter_kits,
  list_phase_definitions, list_hardiness_zones, search_glossary,
  search_plant_knowledge, get_mcp_activity, list_pending_diary_analyses,
  get_diary_entry, get_diary_entry_photos, list_diary_entries
* write (mcp.write): confirm_care_task, archive_plant, set_plant_location,
  add_plant_diary_entry, claim_diary_analysis, submit_diary_analysis,
  record_feeding_event, create_inspection, assign_nutrient_plan
* setup (mcp.setup): create_site

The five ``*_diary_analys*`` / ``get_diary_entry*`` tools (REQ-050 §4,
REQ-033 §2.2a) are the complete contract for the external analysis agent in the
separate ``kamerplanter-goose`` repository; ``get_diary_entry_photos`` is the
only tool in the palette that returns something other than text (REQ-033 §4.3b).
``add_plant_diary_entry`` sits in the same module but outside that contract: it
is the REQ-033 §2.2 write tool for *documenting* an observation, and it never
touches the analysis state machine.

Five tools serve the two external **analysis processes** rather than the analysis
*contract*, and each is paired with the read tool that finds its result again
(§4.1 addressability rule):

* ``record_feeding_event`` (write) — amount, EC/pH and the tank reference, which
  ``get_plant_care_log``'s boolean confirmation could never carry. Surfaced by
  ``get_plant_diagnostics``.
* ``get_plant_diagnostics`` (read) — the §2.1 aggregate: EC/pH **trend** over a
  window, sensors, IPM inspections, Karenz and recent care in one call (AC-5).
* ``create_inspection`` (write) — turns a one-off analysis into IPM history so
  the next analysis has a prior. Surfaced by ``get_plant_inspections``.
* ``search_plant_knowledge`` (read) — the RAG bridge to REQ-031, returning
  citable chunk references so a rationale can name its source (AC-4).
* ``assign_nutrient_plan`` (write) — binds an *existing* plan to a plant;
  authoring plans stays UI work. Surfaced by ``get_plant_nutrient_plan``.

Tools whose ``Input`` extends ``TenantToolInput`` act inside one tenant, which
the dispatcher binds per call; the rest (``list_tenants``, the species catalogue,
``search_plant_knowledge``, ``get_mcp_activity``) read data that carries no
tenant. The distinction is **derived** from the Input model
(``ToolBase.__init_subclass__``) and never set by hand.
"""

from __future__ import annotations

from app.mcp_server.tools import (  # noqa: F401  (side-effect registration)
    calendar,
    care,
    catalogs,
    diagnostics,
    diary,
    feeding,
    harvest,
    ipm,
    knowledge,
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
