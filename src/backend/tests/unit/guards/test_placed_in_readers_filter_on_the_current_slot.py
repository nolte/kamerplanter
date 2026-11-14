"""#2774 — every reader of ``placed_in`` that means "on the slot now" filters on the plant's own ``slot_key``.

``ArangoPlantInstanceRepository.update`` adds a ``placed_in`` edge to the new slot of a moved plant and keeps the
edge to the slot it left (#2948): that edge is the old slot's crop-rotation history. The edge alone therefore no
longer says where a plant stands - only the plant's own ``slot_key`` does. A reader that asks "which plants stand
in this slot / bed" and follows the edge without comparing ``slot_key`` counts a moved plant on every slot it ever
stood in (a phantom occupant, a refused sowing, and in ``clear_bed`` a plant of another bed removed).

The population is every place under ``app/`` that names the edge collection: the constant ``PLACED_IN`` (as an
attribute or a bare name) and every string literal containing the word ``placed_in`` (AQL text with
``@@placed_in``, bind keys, edge lists), docstrings excluded. Each site is keyed by its enclosing unit (the function
or class, or the module-level constant it is assigned to) and listed in :data:`_SITES` with a verdict:

* ``current`` - a reader of the current occupancy. Checked against the code: the unit's AQL text (its own string
  literals plus the module-level string constants it names) must compare an attribute ``.slot_key`` with something
  other than ``null``, and every literal in it that reads ``@@placed_in`` must do so itself;
* ``history`` - a reader that deliberately sees every slot a plant ever stood in (reason given);
* ``writer`` / ``declaration`` - writes edges, or names the collection for a transaction, an index, the graph or an
  export. Checked against the code: such a unit must contain no AQL that iterates ``@@placed_in``.

An unclassified site fails, and so does a register entry no site matches any more (a stale entry).

What this does not see: a traversal over ``GRAPH 'kamerplanter_graph'`` without ``edgeCollections`` that reaches
``placed_in`` implicitly - it names neither the constant nor the string. The behaviour itself is held by
``tests/integration/test_moved_plant_slot_readers.py``.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
BACKEND = APP.parent

_CURRENT = "current"
_HISTORY = "history"
_WRITER = "writer"
_DECLARATION = "declaration"

_PR = "app/data_access/arango/planting_reservation_repository.py"
_PI = "app/data_access/arango/plant_instance_repository.py"
_PS = "app/data_access/arango/plant_state_repository.py"
_CO = "app/data_access/arango/collections.py"

#: ``"path:unit"`` → ``(verdict, reason)``.
_SITES: dict[str, tuple[str, str]] = {
    # -- readers of the current occupancy ---------------------------------------------------------------------
    f"{_PR}:_MARK_SLOT_SOWN": (_CURRENT, "refuses sowing a slot a plant stands in"),
    f"{_PR}:ArangoPlantingReservationRepository.mark_slot_sown": (_CURRENT, "executes _MARK_SLOT_SOWN"),
    f"{_PR}:_CLEAR_SOWN_SLOT": (_CURRENT, "refuses thinning a slot a plant stands in"),
    f"{_PR}:ArangoPlantingReservationRepository._thin_sown_slot": (_CURRENT, "executes _CLEAR_SOWN_SLOT"),
    f"{_PR}:_ACTIVE_PLANTS_IN_SLOTS": (_CURRENT, "the occupants a reservation conflicts with"),
    f"{_PR}:_Reads.active_plants_in": (_CURRENT, "executes _ACTIVE_PLANTS_IN_SLOTS"),
    f"{_PR}:ArangoPlantingReservationRepository._plant_rows": (_CURRENT, "the bed's plantings, one row per plant"),
    f"{_PR}:ArangoPlantingReservationRepository._live_plants": (_CURRENT, "the plants clear_bed removes"),
    f"{_PS}:_SOWN_SLOTS": (_CURRENT, "sown slots without a standing plant"),
    f"{_PS}:ArangoPlantStateRepository.list_sown_slots": (_CURRENT, "executes _SOWN_SLOTS"),
    f"{_PI}:ArangoPlantInstanceRepository.get_active_by_slot": (_CURRENT, "plants currently occupying a slot"),
    "app/data_access/arango/site_repository.py:ArangoSiteRepository.get_slot_for_plant": (
        _CURRENT,
        "the slot a plant stands in (watering)",
    ),
    # -- history readers: every slot a plant ever stood in is the point -----------------------------------------
    f"{_PI}:ArangoPlantInstanceRepository.get_history_by_slot": (
        _HISTORY,
        "the slot's crop-rotation history includes the plants that left it",
    ),
    f"{_PR}:ArangoPlantingReservationRepository._remove_orphan_layout_slots": (
        _HISTORY,
        "a slot any plant ever stood in keeps its rotation history and is not deleted",
    ),
    "app/data_access/arango/planting_run_repository.py:ArangoPlantingRunRepository.get_existing_ids_at_location": (
        _HISTORY,
        "instance ids ever used at the location must not be reissued",
    ),
    "app/data_access/arango/watering_log_repository.py:ArangoWateringLogRepository.get_last_watering_date_for_run": (
        _HISTORY,
        "a watering of any slot the run's plants stood in counts for the run",
    ),
    "app/data_access/arango/watering_repository.py:ArangoWateringRepository.get_by_location": (
        _HISTORY,
        "watering events join the plant, not where it stands today",
    ),
    "app/data_access/arango/watering_repository.py:ArangoWateringRepository.get_stats_by_location": (
        _HISTORY,
        "watering events join the plant, not where it stands today",
    ),
    # -- writers --------------------------------------------------------------------------------------------------
    f"{_PI}:ArangoPlantInstanceRepository.create": (_WRITER, "create_edge to the new plant's slot"),
    f"{_PI}:ArangoPlantInstanceRepository.update": (_WRITER, "create_edge_if_absent to the plant's new slot"),
    f"{_PI}:ArangoPlantInstanceRepository.delete": (_WRITER, "delete_edges of the deleted plant"),
    f"{_PR}:ArangoPlantingReservationRepository._insert_plants": (_WRITER, "inserts the edge of a new plant"),
    # -- declarations: transaction collection sets, schema, graph, export, migrations -----------------------------
    f"{_CO}:PLACED_IN": (_DECLARATION, "the collection name constant"),
    f"{_CO}:EDGE_COLLECTIONS": (_DECLARATION, "the edge collections created at startup"),
    f"{_CO}:GRAPH_EDGE_DEFINITIONS": (_DECLARATION, "the named graph's edge definition"),
    f"{_PR}:_RESERVATION_READ": (_DECLARATION, "transaction read set"),
    f"{_PR}:_DROP_READ": (_DECLARATION, "transaction read set"),
    f"{_PR}:_CLEAR_READ": (_DECLARATION, "transaction read set"),
    f"{_PR}:_QUICK_WRITE": (_DECLARATION, "transaction write set"),
    f"{_PR}:_THIN_WRITE": (_DECLARATION, "transaction write set"),
    f"{_PR}:_SOW_READ": (_DECLARATION, "transaction read set"),
    "app/domain/engines/tenant_export_engine.py:TenantExportEngine": (
        _DECLARATION,
        "the edge collections a tenant export copies",
    ),
    "app/migrations/versions/v0102_purge_site_orphans.py:_EDGE_ENDS": (
        _DECLARATION,
        "a one-off migration's list of edge ends to purge",
    ),
}

_NAMES_THE_EDGE = re.compile(r"\bplaced_in\b")
_ITERATES_THE_EDGE = re.compile(r"\bIN\s+@@placed_in\b")
_COMPARISON = re.compile(r"([\w.@()]+)\s*==\s*([\w.@()]+)")


def _docstrings(tree: ast.AST) -> set[int]:
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                found.add(id(first.value))
    return found


def _is_site(node: ast.AST, docstrings: set[int]) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == "PLACED_IN":
        return True
    if isinstance(node, ast.Name) and node.id == "PLACED_IN":
        return True
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        and bool(_NAMES_THE_EDGE.search(node.value))
    )


def _module_strings(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = <expression>`` → the string literals of the expression, joined."""
    strings: dict[str, str] = {}
    for stmt in tree.body:
        target = stmt.targets[0] if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 else None
        if isinstance(stmt, ast.AnnAssign):
            target = stmt.target
        value = getattr(stmt, "value", None)
        if isinstance(target, ast.Name) and value is not None:
            strings[target.id] = _literals(value)
    return strings


def _literals(node: ast.AST) -> str:
    return "\n".join(n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str))


class _Unit:
    def __init__(self, node: ast.AST) -> None:
        self.node = node
        self.lines: list[int] = []


def _sites() -> tuple[dict[str, _Unit], dict[str, dict[str, str]]]:
    """``"path:unit"`` → the unit with the lines naming the edge; plus the module string constants per path."""
    units: dict[str, _Unit] = {}
    constants: dict[str, dict[str, str]] = {}
    for path in sorted(APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(BACKEND).as_posix()
        constants[rel] = _module_strings(tree)
        docstrings = _docstrings(tree)

        def visit(
            node: ast.AST, stack: list[str], owner: ast.AST, *, rel: str = rel, docstrings: set[int] = docstrings
        ) -> None:
            for child in ast.iter_child_nodes(node):
                child_stack, child_owner = stack, owner
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    child_stack, child_owner = [*stack, child.name], child
                elif not stack and isinstance(child, (ast.Assign, ast.AnnAssign)):
                    target = child.targets[0] if isinstance(child, ast.Assign) else child.target
                    child_stack = [target.id if isinstance(target, ast.Name) else "<module>"]
                    child_owner = child
                if _is_site(child, docstrings):
                    key = f"{rel}:{'.'.join(child_stack) or '<module>'}"
                    units.setdefault(key, _Unit(child_owner)).lines.append(child.lineno)
                visit(child, child_stack, child_owner)

        visit(tree, [], tree)
    return units, constants


def _aql_text(unit: _Unit, module_constants: dict[str, str]) -> tuple[str, list[str]]:
    """The unit's own literals plus the module constants it names; and the literals that iterate the edge."""
    own = [n.value for n in ast.walk(unit.node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    named = [
        module_constants[n.id]
        for n in ast.walk(unit.node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in module_constants
    ]
    text = "\n".join([*own, *named])
    iterating = [chunk for chunk in [*own, *named] if _ITERATES_THE_EDGE.search(chunk)]
    return text, iterating


def _compares_the_current_slot(aql: str) -> bool:
    """Whether ``aql`` compares an attribute ``.slot_key`` with something other than ``null``."""
    for match in _COMPARISON.finditer(aql):
        left, right = match.group(1), match.group(2)
        if "null" in (left, right):
            continue
        if left.endswith(".slot_key") or right.endswith(".slot_key"):
            return True
    return False


def test_every_site_naming_placed_in_is_classified() -> None:
    units, _ = _sites()
    unclassified = sorted(f"{key} (line {units[key].lines[0]})" for key in units if key not in _SITES)
    assert not unclassified, (
        "These units name the placed_in edge collection but are not classified in _SITES. A reader of the "
        "current occupancy must filter on the plant's own slot_key (#2774); a history reader, writer or "
        "declaration needs an entry with its reason:\n  " + "\n  ".join(unclassified)
    )


def test_no_register_entry_is_stale() -> None:
    units, _ = _sites()
    stale = sorted(key for key in _SITES if key not in units)
    assert not stale, "These _SITES entries no longer name placed_in (remove them):\n  " + "\n  ".join(stale)


def test_current_readers_filter_on_the_plants_own_slot_key() -> None:
    units, constants = _sites()
    failures: list[str] = []
    for key, (verdict, _reason) in sorted(_SITES.items()):
        if verdict != _CURRENT or key not in units:
            continue
        path = key.split(":", 1)[0]
        text, iterating = _aql_text(units[key], constants[path])
        if not _compares_the_current_slot(text):
            failures.append(f"{key}: no comparison of the plant's slot_key")
        failures.extend(
            f"{key}: an AQL literal iterating @@placed_in compares no slot_key"
            for chunk in iterating
            if not _compares_the_current_slot(chunk)
        )
    assert not failures, (
        "A placed_in edge also leads to a slot the plant left (#2948); a reader of the current occupancy must "
        "compare the plant's own slot_key (#2774):\n  " + "\n  ".join(failures)
    )


def test_writers_and_declarations_read_no_edges() -> None:
    units, constants = _sites()
    reading = []
    for key, (verdict, _reason) in sorted(_SITES.items()):
        if verdict not in (_WRITER, _DECLARATION) or key not in units:
            continue
        _text, iterating = _aql_text(units[key], constants[key.split(":", 1)[0]])
        if iterating:
            reading.append(key)
    assert not reading, (
        "These units are classified writer/declaration but iterate @@placed_in - classify them as a reader:\n  "
        + "\n  ".join(reading)
    )


def test_every_verdict_is_known_and_reasoned() -> None:
    bad = sorted(
        key
        for key, (verdict, reason) in _SITES.items()
        if verdict not in (_CURRENT, _HISTORY, _WRITER, _DECLARATION) or not reason.strip()
    )
    assert not bad, "Unknown verdict or empty reason:\n  " + "\n  ".join(bad)


def test_the_comparison_detector_rejects_the_null_check_and_accepts_the_filter() -> None:
    """The detector must not take ``plant.slot_key == null`` (the loose-plant arm) for the current-slot filter."""
    assert not _compares_the_current_slot("FILTER plant.location_key == @k AND plant.slot_key == null")
    assert not _compares_the_current_slot('"slot_key": slot_key, FILTER s._key == @slot_key')
    assert _compares_the_current_slot("FILTER plant != null AND plant.slot_key == s._key")
    assert _compares_the_current_slot("FILTER PARSE_IDENTIFIER(e._to).key == plant.slot_key")
    assert _compares_the_current_slot("FILTER v.slot_key == @slot_key")
