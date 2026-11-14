"""#2774 - a reader of where a plant stands *now* selects it by its own ``slot_key``, never through ``placed_in``.

``ArangoPlantInstanceRepository.update`` adds a ``placed_in`` edge to the new slot of a moved plant and keeps the
edge to the slot it left (#2948): that edge is the old slot's crop-rotation history. A plant moved before #2948 has
no edge to its current slot at all. The edge therefore never says where a plant stands - only the plant's own
``slot_key`` does. A reader that asks "which plants stand in this slot / bed" through the edge counts a moved plant
on every slot it ever stood in and misses a plant moved before #2948 on the slot it stands in (a phantom occupant,
a sowing over a standing plant, and in ``clear_bed`` a plant of another bed removed or one of this bed left).

Two registers, both checked against the code:

* :data:`_CURRENT_READERS` - the readers of the current occupancy. Each unit must exist (no stale entry) and its
  AQL - its own string literals plus the module-level string constants it names - must not name ``placed_in``
  at all: it selects the plants by ``slot_key`` (or looks the slot up by it).
* :data:`_SITES` - every place under ``app/`` that names the edge collection (the constant ``PLACED_IN`` as an
  attribute or a bare name, and every non-docstring string literal containing the word ``placed_in``), keyed by
  its enclosing unit (function, class, or module-level assignment), with a verdict: ``history`` (a reader that
  deliberately sees every slot a plant ever stood in, reason given), ``ever-or-now`` (a reader of "any plant
  ever or now": it keeps the edges and must also select the plants by their own ``slot_key`` in a loop over
  ``@@plants``, because a plant moved before #2948 has no edge to its slot), ``writer`` or ``declaration``
  (writes edges, or names the collection for the schema, the graph, a transaction or an export; such a unit must
  not iterate ``@@placed_in``). There is no ``current`` verdict: a new reader of the edge is history or
  ever-or-now, with a reason, or it is wrong. An unclassified site fails, and so does an entry no site matches any more.

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

_HISTORY = "history"
_EVER_OR_NOW = "ever-or-now"
_WRITER = "writer"
_DECLARATION = "declaration"

_PR = "app/data_access/arango/planting_reservation_repository.py"
_PI = "app/data_access/arango/plant_instance_repository.py"
_PS = "app/data_access/arango/plant_state_repository.py"
_CO = "app/data_access/arango/collections.py"

_SS = "app/data_access/arango/site_repository.py"

#: ``"path:unit"`` of every reader of the current occupancy → what it answers. None of them may name ``placed_in``.
_CURRENT_READERS: dict[str, str] = {
    f"{_PR}:_MARK_SLOT_SOWN": "refuses sowing a slot a plant stands in",
    f"{_PR}:ArangoPlantingReservationRepository.mark_slot_sown": "executes _MARK_SLOT_SOWN",
    f"{_PR}:_CLEAR_SOWN_SLOT": "refuses thinning a slot a plant stands in",
    f"{_PR}:ArangoPlantingReservationRepository.thin_sown_slot": "executes _CLEAR_SOWN_SLOT",
    f"{_PR}:_ACTIVE_PLANTS_IN_SLOTS": "the occupants a reservation conflicts with",
    f"{_PR}:_Reads.active_plants_in": "executes _ACTIVE_PLANTS_IN_SLOTS",
    f"{_PR}:ArangoPlantingReservationRepository._plant_rows": "the bed's plantings, one row per plant",
    f"{_PR}:ArangoPlantingReservationRepository._live_plants": "the plants clear_bed removes",
    f"{_PS}:_SOWN_SLOTS": "sown slots without a standing plant",
    f"{_PS}:ArangoPlantStateRepository.list_sown_slots": "executes _SOWN_SLOTS",
    f"{_PI}:ArangoPlantInstanceRepository.get_active_by_slot": "plants currently occupying a slot",
    f"{_SS}:ArangoSiteRepository.get_slot_for_plant": "the slot a plant stands in (watering)",
    "app/data_access/arango/watering_log_repository.py:ArangoWateringLogRepository.get_last_watering_date_for_run": (
        "the slots a run's plants stand in now"
    ),
}

#: ``"path:unit"`` → ``(verdict, reason)`` for every unit naming ``placed_in``.
_SITES: dict[str, tuple[str, str]] = {
    # -- history readers: every slot a plant ever stood in is the point -----------------------------------------
    f"{_PI}:ArangoPlantInstanceRepository.get_history_by_slot": (
        _HISTORY,
        "the slot's crop-rotation history includes the plants that left it",
    ),
    # -- "ever or now": the edges for the plants that left, plus the plants whose own slot_key names the slot -------
    f"{_PR}:ArangoPlantingReservationRepository._remove_orphan_layout_slots": (
        _EVER_OR_NOW,
        "a slot any plant ever stood in keeps its history, and one a plant stands in now is not deleted",
    ),
    "app/data_access/arango/planting_run_repository.py:ArangoPlantingRunRepository.get_existing_ids_at_location": (
        _EVER_OR_NOW,
        "instance ids ever used or in use at the location must not be reissued",
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
    f"{_PR}:_DROP_READ": (_DECLARATION, "transaction read set"),
    f"{_PR}:_QUICK_WRITE": (_DECLARATION, "transaction write set"),
    f"{_PR}:_THIN_WRITE": (_DECLARATION, "transaction write set"),
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
#: A loop over the plant collection that compares the loop variable's own ``slot_key`` before the next ``FOR``.
_SELECTS_BY_SLOT_KEY = re.compile(r"\bFOR\s+(\w+)\s+IN\s+@@plants\b(?:(?!\bFOR\b).)*?\b\1\.slot_key\b", re.DOTALL)


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
    docstrings = _docstrings(unit.node)
    own = [
        n.value
        for n in ast.walk(unit.node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
    ]
    named = [
        module_constants[n.id]
        for n in ast.walk(unit.node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in module_constants
    ]
    text = "\n".join([*own, *named])
    iterating = [chunk for chunk in [*own, *named] if _ITERATES_THE_EDGE.search(chunk)]
    return text, iterating


def _unit_nodes() -> dict[str, tuple[ast.AST, dict[str, str]]]:
    """``"path:unit"`` → the unit's node and its module's string constants, for every function, class and
    module-level assignment under ``app/``."""
    found: dict[str, tuple[ast.AST, dict[str, str]]] = {}
    for path in sorted(APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(BACKEND).as_posix()
        constants = _module_strings(tree)

        def visit(node: ast.AST, stack: list[str], *, rel: str = rel, constants: dict[str, str] = constants) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = [*stack, child.name]
                    found[f"{rel}:{'.'.join(name)}"] = (child, constants)
                    visit(child, name)
                elif not stack and isinstance(child, (ast.Assign, ast.AnnAssign)):
                    target = child.targets[0] if isinstance(child, ast.Assign) else child.target
                    if isinstance(target, ast.Name):
                        found[f"{rel}:{target.id}"] = (child, constants)

        visit(tree, [])
    return found


def test_every_site_naming_placed_in_is_classified() -> None:
    units, _ = _sites()
    unclassified = sorted(f"{key} (line {units[key].lines[0]})" for key in units if key not in _SITES)
    assert not unclassified, (
        "These units name the placed_in edge collection but are not classified in _SITES. A reader of the "
        "current occupancy must not read the edge at all but select by the plant's own slot_key (#2774); a "
        "history reader, writer or declaration needs an entry with its reason:\n  " + "\n  ".join(unclassified)
    )


def test_no_register_entry_is_stale() -> None:
    units, _ = _sites()
    stale = sorted(key for key in _SITES if key not in units)
    assert not stale, "These _SITES entries no longer name placed_in (remove them):\n  " + "\n  ".join(stale)


def test_current_readers_exist_and_do_not_read_placed_in() -> None:
    units = _unit_nodes()
    stale = sorted(key for key in _CURRENT_READERS if key not in units)
    assert not stale, "These _CURRENT_READERS entries no longer exist (update the register):\n  " + "\n  ".join(stale)
    through_the_edge = []
    for key in sorted(_CURRENT_READERS):
        node, constants = units[key]
        text, _iterating = _aql_text(_Unit(node), constants)
        names_the_constant = any(
            (isinstance(n, ast.Attribute) and n.attr == "PLACED_IN")
            or (isinstance(n, ast.Name) and n.id == "PLACED_IN")
            for n in ast.walk(node)
        )
        if names_the_constant or _NAMES_THE_EDGE.search(text):
            through_the_edge.append(key)
    assert not through_the_edge, (
        "A placed_in edge also leads to a slot the plant left (#2948) and is missing for a plant moved before it; a "
        "reader of the current occupancy selects the plants by their own slot_key instead (#2774):\n  "
        + "\n  ".join(through_the_edge)
    )


def test_no_reader_is_both_current_and_registered_as_an_edge_site() -> None:
    both = sorted(set(_CURRENT_READERS) & set(_SITES))
    assert not both, "Registered as a current reader and as a placed_in site:\n  " + "\n  ".join(both)


def test_ever_or_now_readers_also_select_by_slot_key() -> None:
    """A reader of "ever stood here" keeps the edges, and must also count a plant standing here by its slot_key:
    a plant moved before #2948 has no edge to the slot it stands in (#2774)."""
    units, constants = _sites()
    missing = []
    for key, (verdict, _reason) in sorted(_SITES.items()):
        if verdict != _EVER_OR_NOW or key not in units:
            continue
        text, _iterating = _aql_text(units[key], constants[key.split(":", 1)[0]])
        if not _SELECTS_BY_SLOT_KEY.search(text):
            missing.append(key)
    assert not missing, (
        "These ever-or-now readers count no plant by its own slot_key (a FOR over @@plants comparing "
        "<var>.slot_key):\n  " + "\n  ".join(missing)
    )


def test_the_slot_key_detector_needs_the_loop_variable() -> None:
    assert _SELECTS_BY_SLOT_KEY.search("FOR plant IN @@plants FILTER plant.slot_key == s._key")
    assert _SELECTS_BY_SLOT_KEY.search("FOR plant IN @@plants\n  FILTER plant.slot_key IN slots[*]._key")
    assert not _SELECTS_BY_SLOT_KEY.search("FOR plant IN @@plants FILTER plant.location_key == @k")
    assert not _SELECTS_BY_SLOT_KEY.search("FOR p IN @@plants FILTER p.x == 1 FOR q IN @@other FILTER p.slot_key")


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
        if verdict not in (_HISTORY, _EVER_OR_NOW, _WRITER, _DECLARATION) or not reason.strip()
    )
    assert not bad, "Unknown verdict or empty reason:\n  " + "\n  ".join(bad)
