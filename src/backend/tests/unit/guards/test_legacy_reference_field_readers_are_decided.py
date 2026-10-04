"""#1963 — every reader of a field v0067 left behind is decided, and a species reader resolves it.

``tests/unit/guards/test_tenant_reference_keys_are_resolved.py`` classifies a stored
reference field ``verified`` when every **write** path resolves it under the tenant. That
says nothing about a row written *before* the fix, and v0067 (#1878) removed only the
cross-tenant **edge** such a row had: the document still carries the foreign key in its
own field. A reader that follows the field — not the edge — reaches the foreign row.

The population this guard derives is the readers of the four mirrored fields (a fifth
relation, ``feeds_from``, has no field at all, only an edge):

* ``planting_run_entries.species_key`` — through the repository reads that return an
  entry (``get_entries``, and the by-key reads in the run module);
* ``equipment.location_key`` — through the equipment reads;
* ``location_assignments.location_key`` — through the assignment reads;
* ``watering_logs.slot_keys`` — the attribute, and the AQL that names it;
* ``feeds_from`` — the edge constant outside the migrations.

Each reader is listed in :data:`_READERS` with a verdict. Two are checked **against the
code**, not only against the register, because they are the ones that can dereference a
foreign row:

* ``resolves`` — the function must call a tenant resolver
  (:data:`_RESOLVER_CALLS`) — it would otherwise be a reader that trusts the field;
* ``key-only`` — the function must call *no* species lookup
  (:data:`_SPECIES_LOOKUPS`) — it compares or echoes the key, and a lookup added later
  must be decided again.

What this does not see: a reader that gets a legacy entry by a path none of the
detectors name (a new repository method, a raw AQL over the collection that names no
field) — the detectors are the set above, so the register is only as complete as they
are. The behaviour itself is held by ``tests/integration/test_legacy_foreign_field_readers.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"

_ENTRY_READS = {"get_entries"}
_ENTRY_READS_IN_RUN_MODULES = {"get_entry", "get_entry_or_raise"}
_EQUIPMENT_READS = {"get_equipment", "get_equipment_or_raise", "list_equipment", "find_equipment_by_location"}
_ASSIGNMENT_READS = {"list_assignments", "list_by_membership", "get_by_membership_and_location"}

#: Calls that resolve a species under a tenant.
_RESOLVER_CALLS = {"_require_readable_species", "_species_is_readable", "readable_species", "_species_harvest_bars"}
#: The calls that *are* the resolver (``_species_harvest_bars`` resolves through ``readable_species``).
_RESOLVERS = {"_require_readable_species", "_species_is_readable", "readable_species"}
#: Calls that follow a species key to the species (or its phase data).
_SPECIES_LOOKUPS = {
    "get_species",
    "get_lifecycle_by_species",
    "get_sequence_by_species",
    "_resolve_initial_phase",
    "_resolve_growth_phases_for_timeline",
}

_ENTRY = "planting_run_entries.species_key"
_EQUIPMENT = "equipment.location_key"
_ASSIGNMENT = "location_assignments.location_key"
_SLOTS = "watering_logs.slot_keys"
_FEEDS = "feeds_from"

_ECHO = "key-only"
_RESOLVES = "resolves"

_P = "app/domain/services/planting_run_service.py"
_I = "app/domain/services/inventree_service.py"
_T = "app/domain/services/tenant_service.py"
_W = "app/domain/services/watering_log_service.py"
_WR = "app/data_access/arango/watering_log_repository.py"
_TK = "app/data_access/arango/tank_repository.py"

#: ``(field, "path:qualified name")`` → ``(verdict, reason)``.
_READERS: dict[tuple[str, str], tuple[str, str]] = {
    # -- planting_run_entries.species_key: the one field a reader dereferences --------------
    (_ENTRY, f"{_P}:PlantingRunService.create_plants"): (
        _RESOLVES,
        "resolves every entry under the run's tenant first",
    ),
    (_ENTRY, f"{_P}:PlantingRunService.get_phase_timeline"): (
        _RESOLVES,
        "skips a species the run's tenant may not read",
    ),
    (_ENTRY, "app/tasks/irrigation_tasks.py:_resolve_species_kc"): (
        _RESOLVES,
        "readable_species under the run's tenant",
    ),
    (_ENTRY, "app/domain/services/calendar_service.py:CalendarService._build_entries_from_runs"): (
        _RESOLVES,
        "_species_harvest_bars resolves through readable_species; the phase bars come from get_phase_timeline",
    ),
    (_ENTRY, f"{_P}:PlantingRunService._apply_clone_config"): (
        _ECHO,
        "copies the entries; create_run resolves every entry's species before anything is stored",
    ),
    (_ENTRY, f"{_P}:PlantingRunService.list_entries"): (_ECHO, "returns the entries; the route echoes the key"),
    (_ENTRY, f"{_P}:PlantingRunService.add_entry"): (
        _ECHO,
        "sums quantities; the new entry's species is resolved on write",
    ),
    (_ENTRY, f"{_P}:PlantingRunService.update_entry"): (
        _ECHO,
        "sums quantities; a changed species is resolved on write",
    ),
    (_ENTRY, f"{_P}:PlantingRunService.delete_entry"): (_ECHO, "sums quantities"),
    (_ENTRY, f"{_P}:PlantingRunService._entry_of_run"): (_ECHO, "checks the entry belongs to the run"),
    (_ENTRY, f"{_P}:PlantingRunService.adopt_plants"): (
        _ECHO,
        "compares the plant's species key with the entries' keys",
    ),
    (_ENTRY, "app/data_access/arango/planting_run_repository.py:ArangoPlantingRunRepository.delete"): (
        _ECHO,
        "removes the entries with the run",
    ),
    # -- equipment.location_key: echoed, never followed (the by-location read walks the edge) --
    (_EQUIPMENT, "app/api/v1/equipment/tenant_router.py:equipment_by_location"): (_ECHO, "edge read, tenant-filtered"),
    (_EQUIPMENT, "app/api/v1/equipment/tenant_router.py:get_equipment"): (_ECHO, "echoes the field"),
    (_EQUIPMENT, "app/api/v1/equipment/tenant_router.py:list_equipment"): (_ECHO, "echoes the field"),
    (_EQUIPMENT, f"{_I}:InvenTreeService.delete_equipment"): (_ECHO, "ownership check only"),
    (_EQUIPMENT, f"{_I}:InvenTreeService.find_equipment_by_location"): (_ECHO, "edge read, tenant-filtered"),
    (_EQUIPMENT, f"{_I}:InvenTreeService.get_equipment"): (_ECHO, "ownership check only"),
    (_EQUIPMENT, f"{_I}:InvenTreeService.list_equipment"): (_ECHO, "tenant-filtered list"),
    (_EQUIPMENT, f"{_I}:InvenTreeService.update_equipment"): (
        _ECHO,
        "compares the stored key with the new one; the new one is resolved under the tenant",
    ),
    # -- location_assignments.location_key: echoed ------------------------------------------
    (_ASSIGNMENT, "app/api/v1/tenants/router.py:list_assignments"): (_ECHO, "echoes the field"),
    (_ASSIGNMENT, f"{_T}:TenantService.create_assignment"): (_ECHO, "resolves the *new* location under the tenant"),
    (_ASSIGNMENT, f"{_T}:TenantService.list_assignments"): (_ECHO, "tenant-filtered list"),
    # -- watering_logs.slot_keys ------------------------------------------------------------
    (_SLOTS, "app/api/v1/watering_logs/schemas.py:WateringLogCreate.check_domain_rules"): (_ECHO, "request validation"),
    (_SLOTS, "app/data_access/arango/collections.py:ensure_collections"): (_ECHO, "declares the index"),
    (_SLOTS, f"{_WR}:ArangoWateringLogRepository.create"): (_ECHO, "writes the edges of the verified slots"),
    (_SLOTS, f"{_WR}:ArangoWateringLogRepository.get_last_watering_date_for_run"): (
        _ECHO,
        "intersects the tenant's own logs with the run's slots; no slot is loaded",
    ),
    (_SLOTS, f"{_W}:WateringLogService.create_log"): (_ECHO, "resolves every slot under the log's tenant first"),
    (_SLOTS, f"{_W}:WateringLogService.update_log"): (_ECHO, "passes the stored keys to the domain-rule check"),
    # -- feeds_from: no mirrored field, only the edge ---------------------------------------
    (_FEEDS, f"{_TK}:ArangoTankRepository.delete"): (_ECHO, "removes the edges with the tank"),
    (_FEEDS, f"{_TK}:ArangoTankRepository.link_feeds_from"): (
        _ECHO,
        "writes the edge; the service resolved both tanks",
    ),
}


def _is_run_module(rel: str) -> bool:
    return "planting_run" in rel


class _ReaderVisitor(ast.NodeVisitor):
    """Collects the functions of one module that read a mirrored field."""

    def __init__(self, rel: str, found: dict[tuple[str, str], ast.AST]) -> None:
        self.rel = rel
        self.found = found
        self.stack: list[str] = []

    def _note(self, field: str, node: ast.AST) -> None:
        self.found.setdefault((field, f"{self.rel}:{'.'.join(self.stack)}"), node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                attr = sub.func.attr
                if attr in _ENTRY_READS or (attr in _ENTRY_READS_IN_RUN_MODULES and _is_run_module(self.rel)):
                    self._note(_ENTRY, node)
                if attr in _EQUIPMENT_READS:
                    self._note(_EQUIPMENT, node)
                if attr in _ASSIGNMENT_READS or (attr == "list_by_tenant" and "assign" in ast.unparse(sub.func.value)):
                    self._note(_ASSIGNMENT, node)
            if isinstance(sub, ast.Attribute) and sub.attr == "slot_keys":
                self._note(_SLOTS, node)
            if isinstance(sub, ast.Attribute) and sub.attr == "FEEDS_FROM":
                self._note(_FEEDS, node)
            if (
                isinstance(sub, ast.Constant)
                and isinstance(sub.value, str)
                and "slot_keys" in sub.value
                and "/data_access/" in self.rel
            ):
                self._note(_SLOTS, node)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = _function  # noqa: N815
    visit_AsyncFunctionDef = _function  # noqa: N815


def readers(sources: dict[str, str]) -> dict[tuple[str, str], ast.AST]:
    """``(field, "path:qualname")`` → the function node, for every reader of a mirrored field."""
    found: dict[tuple[str, str], ast.AST] = {}
    for rel, source in sources.items():
        if "/migrations/" in rel or "/domain/models/" in rel:
            continue
        _ReaderVisitor(rel, found).visit(ast.parse(source))
    return found


def _tree_sources() -> dict[str, str]:
    return {str(path.relative_to(APP.parent)): path.read_text(encoding="utf-8") for path in sorted(APP.rglob("*.py"))}


def _call_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute):
                if func.attr == "get_by_key" and "species" in ast.unparse(func.value):
                    names.add("get_species")
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


@pytest.fixture(scope="module")
def population() -> dict[tuple[str, str], ast.AST]:
    return readers(_tree_sources())


def test_every_reader_of_a_mirrored_field_is_decided(population) -> None:
    found = set(population)
    undecided = sorted(found - set(_READERS))
    stale = sorted(set(_READERS) - found)

    assert undecided == [], (
        "a reader of a field v0067 left behind is not in the register — decide whether it resolves the stored "
        f"key under the tenant or only echoes it, then list it: {undecided}"
    )
    assert stale == [], f"registered readers that no longer exist — drop the entry: {stale}"


def test_the_scan_reaches_every_field(population) -> None:
    per_field: dict[str, int] = {}
    for field, _ in population:
        per_field[field] = per_field.get(field, 0) + 1

    # Non-vacuity: every mirrored field has readers, so an empty scan fails here.
    assert set(per_field) == {_ENTRY, _EQUIPMENT, _ASSIGNMENT, _SLOTS, _FEEDS}, per_field
    assert per_field[_ENTRY] >= 10, per_field


def test_a_reader_that_resolves_calls_a_tenant_resolver(population) -> None:
    unresolved = sorted(
        key
        for key, (verdict, _) in _READERS.items()
        if verdict == _RESOLVES and key in population and not (_call_names(population[key]) & _RESOLVER_CALLS)
    )

    assert unresolved == [], f"registered as resolving the stored species but no resolver is called: {unresolved}"


def test_the_calendar_bars_resolve_the_species_they_are_built_from() -> None:
    """``_build_entries_from_runs`` resolves one call down; that callee must still resolve."""
    tree = ast.parse(_tree_sources()["app/domain/services/calendar_service.py"])
    harvest_bars = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_species_harvest_bars"
    )

    assert _call_names(harvest_bars) & _RESOLVERS


def test_a_reader_marked_key_only_looks_up_no_species(population) -> None:
    looking_up = sorted(
        key
        for key, (verdict, _) in _READERS.items()
        if key[0] == _ENTRY
        and verdict == _ECHO
        and key in population
        and _call_names(population[key]) & _SPECIES_LOOKUPS
    )

    assert looking_up == [], f"registered as key-only but a species is looked up through the stored key: {looking_up}"


def test_every_write_path_of_an_entry_species_resolves_it() -> None:
    """The register's ``resolved on write`` reasons are true: the three writers call the resolver."""
    tree = ast.parse(_tree_sources()[_P])
    service = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "PlantingRunService")
    methods = {n.name: n for n in service.body if isinstance(n, ast.FunctionDef)}

    for writer in ("create_run", "add_entry", "update_entry", "create_plants"):
        assert _call_names(methods[writer]) & _RESOLVERS, writer


# -- selftests: the guard can fail ----------------------------------------------------


_UNDECIDED = """
class Service:
    def new_reader(self, run_key):
        for entry in self._repo.get_entries(run_key):
            self._species_repo.get_by_key(entry.species_key)
"""


def test_selftest_an_undecided_reader_is_found() -> None:
    found = readers({"app/domain/services/new_service.py": _UNDECIDED})

    assert set(found) == {(_ENTRY, "app/domain/services/new_service.py:Service.new_reader")}
    assert (_ENTRY, "app/domain/services/new_service.py:Service.new_reader") not in _READERS


def test_selftest_a_lookup_through_the_stored_key_is_seen_and_a_resolver_is_too() -> None:
    node = next(iter(readers({"app/domain/services/new_service.py": _UNDECIDED}).values()))

    assert _call_names(node) & _SPECIES_LOOKUPS == {"get_species"}
    assert not _call_names(node) & _RESOLVERS
    resolving = ast.parse("def f(self, e):\n    self._require_readable_species(e.species_key, 't')\n").body[0]
    assert _call_names(resolving) & _RESOLVERS
