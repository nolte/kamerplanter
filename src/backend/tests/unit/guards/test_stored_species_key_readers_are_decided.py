"""#2082 — a reader that follows a **stored** species key resolves it under the tenant, or is listed.

``PlantInstance.species_key`` of a plant a legacy planting run created can name another
tenant's private species (before #2081 the run service followed a foreign entry key). A
reader that follows the field with the unscoped ``species_repo.get_by_key`` returns that
species' name or data to the wrong tenant. ``test_legacy_reference_field_readers_are_decided``
covers the entries of a run; this guard covers the **species-key readers of the rest of
the app**.

The population is derived, not listed: every function under ``app/`` (migrations aside) that
reads a ``species_key`` (attribute or dict key) **and** follows it through a species lookup
(:data:`_LOOKUPS`) or a tenant resolver (:data:`_RESOLVERS`). Each is in :data:`_READERS`:

* ``resolves`` — the function must call a tenant resolver (``readable_species``, a
  ``get_species(..., tenant_key=...)`` or ``resolve_species(..., tenant_key=...)``);
* ``listed`` — it still looks the species up unscoped, with the reason it was not changed in
  #2082. The function must **not** already resolve (a fix must move the entry), so the list
  shrinks and never goes stale.

What this does not see: a reader that reaches the species by a name not in :data:`_LOOKUPS`
(a new repository method), or that receives an already-loaded species. The behaviour of the
two routes that carry the exposure is held by
``tests/integration/test_run_plants_species_name_tenant_scope.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"

_LOOKUP_ATTRS = {"get_species", "get_species_or_raise", "get_species_by_key", "resolve_species", "_resolve_species"}
_RESOLVER_NAMES = {"readable_species", "_require_readable_species", "_species_is_readable"}
_TENANT_KWARGS = {"tenant_key"}
_TENANT_POSITION = 3

_RESOLVES = "resolves"
_LISTED = "listed"

_ROTATION_REASON = (
    "echoes botanical family keys (global catalogue), never a species name; an unreadable species' family is"
    " the only thing it could carry, and only as a key the caller's own plant history already implies"
)
_NEIGHBOUR_NAME_REASON = (
    "names a neighbour only when the species has a global companion edge; the app has no tenant write path"
    " for those edges (seed-only), so a tenant's private species cannot be that neighbour (re-judged #2082)"
)
_FISH_REASON = "the 'species' is the global fish catalogue (fish_species), not the tenant-owned species collection"
_CARE = "app/domain/services/care_reminder_service.py:CareReminderService"

#: ``"path:qualified name"`` -> ``(verdict, reason)``.
_READERS: dict[str, tuple[str, str]] = {
    "app/domain/services/planting_run_service.py:PlantingRunService.add_entry": (_RESOLVES, ""),
    "app/domain/services/planting_run_service.py:PlantingRunService.create_plants": (_RESOLVES, ""),
    "app/domain/services/planting_run_service.py:PlantingRunService.create_run": (_RESOLVES, ""),
    "app/domain/services/planting_run_service.py:PlantingRunService.get_phase_timeline": (_RESOLVES, ""),
    "app/domain/services/planting_run_service.py:PlantingRunService.update_entry": (_RESOLVES, ""),
    "app/domain/services/propagation_service.py:PropagationService._require_event_references": (_RESOLVES, ""),
    "app/domain/services/succession_plan_service.py:SuccessionPlanService.create_plan": (_RESOLVES, ""),
    "app/tasks/irrigation_tasks.py:_resolve_species_kc": (_RESOLVES, ""),
    "app/api/v1/overwintering_profiles/tenant_router.py:auto_generate_overwintering_profile": (_RESOLVES, ""),
    "app/api/v1/plant_instances/tenant_router.py:_to_response": (_RESOLVES, ""),
    "app/api/v1/planting_runs/tenant_router.py:get_phase_timeline": (_RESOLVES, ""),
    "app/api/v1/planting_runs/tenant_router.py:list_plants": (_RESOLVES, ""),
    "app/api/v1/tasks/tenant_router.py:create_workflow": (_RESOLVES, ""),
    "app/domain/services/diagnose_service.py:DiagnoseService._build_context": (_RESOLVES, ""),
    "app/domain/services/overwintering_materializer.py:OverwinteringMaterializer.materialize": (_RESOLVES, ""),
    "app/domain/services/overwintering_profile_service.py:OverwinteringProfileService._resolve_plant_hardiness": (
        _RESOLVES,
        "",
    ),
    "app/domain/services/overwintering_profile_service.py:OverwinteringProfileService._resolve_subject_labels": (
        _RESOLVES,
        "",
    ),
    "app/domain/services/plant_photo_service.py:PlantPhotoService.assess_photo": (_RESOLVES, ""),
    "app/domain/services/print_service.py:PrintService.generate_care_checklist_pdf": (_RESOLVES, ""),
    "app/domain/services/print_service.py:PrintService.generate_plant_labels_pdf": (_RESOLVES, ""),
    "app/domain/services/species_service.py:SpeciesService.create_cultivar": (_RESOLVES, ""),
    "app/domain/services/watering_service.py:WateringService.suggest_volume": (_RESOLVES, ""),
    "app/mcp_server/tools/plant_reads.py:GetPlant.run": (_RESOLVES, ""),
    "app/mcp_server/tools/species.py:GetSpeciesInfo.run": (_RESOLVES, ""),
    "app/tasks/reference_contribution_tasks.py:_evaluate": (_RESOLVES, ""),
    "app/domain/engines/companion_planting_engine.py:CompanionPlantingEngine.check_compatibility": (
        _LISTED,
        _NEIGHBOUR_NAME_REASON,
    ),
    "app/domain/engines/companion_planting_engine.py:CompanionPlantingEngine.get_companion_recommendations": (
        _LISTED,
        _NEIGHBOUR_NAME_REASON,
    ),
    "app/domain/engines/crop_rotation_validator.py:CropRotationValidator.validate_planting": (
        _LISTED,
        _ROTATION_REASON,
    ),
    "app/domain/services/aquaponik_service.py:AquaponikService.create_stock": (
        _LISTED,
        f"the stock's species key comes from the request and is not a plant row; {_FISH_REASON}",
    ),
    "app/domain/services/aquaponik_service.py:AquaponikService.get_feeding_recommendation": (
        _LISTED,
        f"reads the species of the tenant's own stock for a feeding factor; {_FISH_REASON}",
    ),
    "app/domain/services/aquaponik_service.py:AquaponikService._primary_species": (
        _LISTED,
        f"reads the species of the tenant's own stock for a feeding factor; {_FISH_REASON}",
    ),
    f"{_CARE}.care_inputs_for_plant": (_RESOLVES, ""),
    f"{_CARE}._build_plant_data_for_tenant": (_RESOLVES, ""),
    f"{_CARE}.ensure_seasonal_winter_tasks": (_RESOLVES, ""),
    "app/domain/services/species_service.py:SpeciesService.get_compatible_species": (
        _LISTED,
        "the key is the request's path parameter, not a stored one; a separate catalogue-read question",
    ),
    "app/domain/services/species_service.py:SpeciesService.get_incompatible_species": (
        _LISTED,
        "the key is the request's path parameter, not a stored one; a separate catalogue-read question",
    ),
    "app/tasks/care_tasks.py:generate_due_care_reminders": (_RESOLVES, ""),
}


def _mentions_species_key(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr == "species_key":
            return True
        if isinstance(sub, ast.Constant) and sub.value == "species_key":
            return True
    return False


def _calls(node: ast.AST) -> list[ast.Call]:
    return [sub for sub in ast.walk(node) if isinstance(sub, ast.Call)]


def _is_lookup(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr in _LOOKUP_ATTRS:
            return True
        return func.attr == "get_by_key" and "species" in ast.unparse(func.value).lower()
    return False


def _is_resolver(call: ast.Call) -> bool:
    func = call.func
    name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
    if name in _RESOLVER_NAMES:
        return True
    # ``get_species(..., tenant_key=...)`` / ``resolve_species(..., tenant_key=...)``
    if name in _LOOKUP_ATTRS and any(kw.arg in _TENANT_KWARGS for kw in call.keywords):
        return True
    # ``CareReminderService._resolve_species(key, cache, tenant_key)`` takes the tenant positionally
    return name == "_resolve_species" and len(call.args) >= _TENANT_POSITION


def _function_nodes(rel: str, tree: ast.AST):
    def walk(node: ast.AST, stack: list[str]):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                yield from walk(child, [*stack, child.name])
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                yield f"{rel}:{'.'.join([*stack, child.name])}", child
                yield from walk(child, [*stack, child.name])
            else:
                yield from walk(child, stack)

    yield from walk(tree, [])


def readers(sources: dict[str, str]) -> dict[str, ast.AST]:
    """``"path:qualname"`` -> the function node, for every function that follows a stored species key."""
    found: dict[str, ast.AST] = {}
    for rel, source in sources.items():
        if "/migrations/" in rel:
            continue
        for name, node in _function_nodes(rel, ast.parse(source)):
            if not _mentions_species_key(node):
                continue
            if any(_is_lookup(c) or _is_resolver(c) for c in _calls(node)):
                found[name] = node
    return found


def _tree_sources() -> dict[str, str]:
    return {str(p.relative_to(APP.parent)): p.read_text(encoding="utf-8") for p in sorted(APP.rglob("*.py"))}


def _resolves(node: ast.AST) -> bool:
    return any(_is_resolver(c) for c in _calls(node))


@pytest.fixture(scope="module")
def population() -> dict[str, ast.AST]:
    return readers(_tree_sources())


def test_every_reader_of_a_stored_species_key_is_decided(population) -> None:
    found = set(population)

    assert sorted(found - set(_READERS)) == [], (
        "decide the new reader: resolve under the tenant, or list it with a reason"
    )
    assert sorted(set(_READERS) - found) == [], "registered readers that no longer exist or no longer follow the key"


def test_a_reader_marked_resolves_calls_a_tenant_resolver(population) -> None:
    unresolved = sorted(
        k for k, (v, _) in _READERS.items() if v == _RESOLVES and k in population and not _resolves(population[k])
    )

    assert unresolved == [], f"registered as resolving under the tenant but no resolver is called: {unresolved}"


def test_a_listed_reader_does_not_already_resolve(population) -> None:
    stale = sorted(k for k, (v, _) in _READERS.items() if v == _LISTED and k in population and _resolves(population[k]))

    assert stale == [], f"listed as unscoped but it resolves now — mark it resolves: {stale}"


def test_every_listed_reader_names_its_reason() -> None:
    assert [k for k, (v, why) in _READERS.items() if v == _LISTED and not why.strip()] == []


def test_the_scan_is_not_vacuous(population) -> None:
    assert len(population) >= 25, len(population)
    assert sum(1 for v, _ in _READERS.values() if v == _RESOLVES) >= 15


# -- selftests: the guard can fail ------------------------------------------------------

_UNSCOPED = """
class Service:
    def label(self, plant):
        return self._species_repo.get_by_key(plant.species_key).scientific_name
"""

_SCOPED = """
def label(repo, plant, tenant_key):
    return readable_species(repo, plant.species_key, tenant_key)
"""

_OTHER = """
def unrelated(repo, key):
    return repo.get_by_key(key)
"""


def test_selftest_an_unscoped_reader_is_found_and_does_not_resolve() -> None:
    found = readers({"app/x.py": _UNSCOPED})

    assert set(found) == {"app/x.py:Service.label"}
    assert not _resolves(found["app/x.py:Service.label"])
    assert "app/x.py:Service.label" not in _READERS


def test_selftest_a_scoped_reader_is_found_and_resolves() -> None:
    found = readers({"app/x.py": _SCOPED})

    assert set(found) == {"app/x.py:label"}
    assert _resolves(found["app/x.py:label"])


def test_selftest_the_care_resolver_counts_only_when_it_is_handed_the_tenant() -> None:
    bare = "def f(self, plant, cache):\n    return self._resolve_species(plant.species_key, cache)\n"
    scoped = (
        "def f(self, plant, cache):\n    return self._resolve_species(plant.species_key, cache, plant.tenant_key)\n"
    )

    assert not _resolves(readers({"app/x.py": bare})["app/x.py:f"])
    assert _resolves(readers({"app/x.py": scoped})["app/x.py:f"])


def test_selftest_a_function_that_never_reads_a_species_key_is_not_a_reader() -> None:
    assert readers({"app/x.py": _OTHER}) == {}
