"""#2012/#2015/#2025 class guard: no code in ``app/`` treats one list page as the whole collection.

``repo.get_all(offset=0, limit=1000, all_tenants=True)`` returns *at most* 1000 rows
plus a ``total``. Nine reads in ``app/tasks`` (#2012) and fifteen more in services,
seed loaders and repositories (#2015) called it once, iterated the rows and dropped
the ``total``: past the page every row was silently never visited (a plant missing
from the care dashboard, a seed product created twice, an import duplicate not seen).
#2025 found the same defect under every other list-method name: seed dedup reads
(``get_all_pests(0, 200)``, ``get_all_sequences(0, 500)``), dashboard aggregates
(``list_by_tenant(..., offset=0, limit=1000)``, ``list_plants(offset=0, limit=10000)``)
and a module constant (``get_all_sequences(0, _SEQUENCE_PAGE)``).

**The rule.** Anywhere under ``app/``, a call is a *fixed window* when either

* it passes ``limit=<n>`` as a keyword and its ``offset=`` keyword is absent or a
  fixed ``<n>`` — whatever the method is called (``get_all``, ``list_by_tenant``,
  ``get_page``, ``find_by_field``, ``list_for_service_account`` ...); or
* it is a list method (name starting ``get_all``, ``list``, ``get_page``, ``find`` or
  ``search``) whose first two positional arguments are a fixed ``<n>`` each
  (``get_all_pests(0, 200)``).

``<n>`` is an integer literal **or a module-level name bound to one** in the same
file (``_SEQUENCE_PAGE = 500``; the #2015 guard missed exactly that spelling). A
``limit`` of 1 is a single-row lookup ("the latest", "does one exist"), never a
collection read, and is not a window. Every other fixed window is a violation unless
:data:`ALLOWED` names it with a reason — a deliberate "newest N" read, a bounded UI
page, a cap that reports ``truncated``. The sanctioned whole-collection spellings
are ``get_all_pages(repo, ...)`` and ``read_all_pages(fetch)`` from
``app.data_access.arango.base_repository`` (they page until the offset reaches
``total``), an aggregate in AQL, or a repository read without ``LIMIT``. A
hand-written paging loop passes because its ``offset`` is a variable. The scan is
an AST walk, so a call split over several lines is seen.

Spellings this does NOT see
---------------------------

* a limit that is not a literal or a same-module constant: a function parameter
  default (``def f(limit=500): repo.list(offset=0, limit=limit)``), an imported
  constant, ``settings.x`` or arithmetic (``limit=PAGE * 2``);
* a positional window on a method outside the list-name prefixes
  (``repo.recent(0, 50)``), and a positional ``limit`` behind a non-literal
  positional ``offset`` without keywords;
* a call reached through an alias (``fetch = repo.get_all; fetch(...)``) or
  ``getattr(repo, "get_all")``;
* an AQL ``LIMIT <n>`` literal inside a repository query, and a ``[:n]`` slice
  applied after a complete read.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"

#: Method-name prefixes whose first two positional arguments are ``offset, limit``.
LIST_METHOD = re.compile(r"^(get_all|list|get_page|find|search)")

_NEWEST_N = (
    "a deliberate 'newest N' window: the repository sorts DESC by time and the caller wants only the recent rows"
)
_MCP_CAP = "MCP tool scan cap: the tool reports `truncated` to the agent when the collection exceeds it"

#: ``(path relative to app/, enclosing function)`` -> reason this single-window read is
#: correct. An entry needs a reason that says why the collection cannot outgrow the
#: window (bounded by construction), why only the newest rows are wanted, or why only
#: the ``total`` is read.
ALLOWED: dict[tuple[str, str], str] = {
    ("domain/services/starter_kit_service.py", "list_kits"): (
        "starter kits come only from starter_kits.yaml (11 rows); no API or service caller writes the collection"
    ),
    ("data_access/arango/enrichment_repository.py", "get_all"): (
        "nothing in app/ writes external_sources; the rows are the registered enrichment adapters"
    ),
    ("data_access/arango/aquaponik_repository.py", "list_species"): (
        "fish species come only from fish_species.yaml (8 rows); create_species has no API or service caller"
    ),
    ("api/v1/admin/pests/router.py", "list_pest_images"): (
        "admin listing of the external inference service's prototypes, a UI page of that service, not our collection"
    ),
    ("api/v1/admin/reference_images/router.py", "list_curation_images"): (
        "admin listing of the external inference service's reference images, a UI page of that service"
    ),
    ("api/v1/privacy/router.py", "get_mcp_activity"): (
        "UI view of the newest 200 MCP audit entries; the complete set is in the Art. 15 export "
        "(data_export_engine, collection mcp_audit_log), so the transparency right is served there"
    ),
    ("domain/services/aquaponik_service.py", "get_cycling_progress"): (
        _NEWEST_N + "; the cycling detector needs the trailing 7 stable tests, 30 covers it"
    ),
    ("domain/services/aquaponik_service.py", "get_fish_health"): (
        _NEWEST_N + "; health alerts look at the last 20 feedings and 5 water tests"
    ),
    ("domain/services/care_reminder_service.py", "confirm_reminder"): (
        _NEWEST_N + "; adaptive learning uses the last 10 confirmations"
    ),
    ("domain/services/pest_detection_service.py", "get_pest_signal_for_plant"): (
        _NEWEST_N + "; the pest signal is built from the 10 most recent detections"
    ),
    ("tasks/tank_maintenance_tasks.py", "check_runoff_trends"): (
        _NEWEST_N + "; the runoff trend compares the 5 most recent runoff events"
    ),
    # MCP tools are keyed by their nested ``run``: an entry covers every ``run`` of the
    # file, so a new fixed window in one of these three files needs a reviewer's eye.
    ("mcp_server/tools/plant_reads.py", "run"): _MCP_CAP + " (list_plants / search_plants, _SCAN_LIMIT)",
    ("mcp_server/tools/nutrition.py", "run"): _MCP_CAP + " (list_nutrient_plans, _SCAN_LIMIT)",
    ("mcp_server/tools/phases.py", "run"): _MCP_CAP + " (list_phase_sequences, _SCAN_LIMIT)",
    ("mcp_server/tools/diagnostics.py", "_inspections"): (
        _NEWEST_N + "; the diagnosis bundle shows the 50 newest inspections inside its window"
    ),
    ("mcp_server/tools/diagnostics.py", "_care"): (
        _NEWEST_N + "; the diagnosis bundle shows the 50 newest care confirmations inside its window"
    ),
}


def _int_constants(tree: ast.Module) -> dict[str, int]:
    """Module-level ``NAME = <int literal>`` (and annotated) bindings of one file."""
    out: dict[str, int] = {}
    for stmt in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets, value = stmt.targets, stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets, value = [stmt.target], stmt.value
        if isinstance(value, ast.Constant) and _is_int_literal(value):
            for target in targets:
                if isinstance(target, ast.Name):
                    out[target.id] = value.value
    return out


def _is_int_literal(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)


def _fixed(node: ast.expr | None, constants: dict[str, int]) -> int | None:
    """The fixed integer ``node`` stands for, or ``None`` when it is not fixed."""
    if isinstance(node, ast.Constant) and _is_int_literal(node):
        return int(node.value)
    if isinstance(node, ast.Name) and node.id in constants:
        return constants[node.id]
    return None


def _method_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _is_fixed_window(call: ast.Call, constants: dict[str, int]) -> bool:
    keywords = {kw.arg: kw.value for kw in call.keywords if kw.arg}
    if "limit" in keywords:
        limit = _fixed(keywords["limit"], constants)
        offset_node = keywords.get("offset")
        offset_fixed = offset_node is None or _fixed(offset_node, constants) is not None
        return limit is not None and limit != 1 and offset_fixed
    name = _method_name(call)
    if name is None or not LIST_METHOD.match(name) or len(call.args) < 2:
        return False
    offset, limit = _fixed(call.args[0], constants), _fixed(call.args[1], constants)
    return offset is not None and limit is not None and limit != 1


def fixed_window_reads(source: str) -> list[tuple[str, int]]:
    """``(enclosing function, line)`` of every list call that asks for one fixed window."""
    tree = ast.parse(source)
    constants = _int_constants(tree)
    found: list[tuple[str, int]] = []

    def visit(node: ast.AST, function: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else function
            if isinstance(child, ast.Call) and _is_fixed_window(child, constants):
                found.append((function, child.lineno))
            visit(child, name)

    visit(tree, "<module>")
    return found


def _live_reads(root: Path) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        for function, line in fixed_window_reads(path.read_text(encoding="utf-8")):
            out.append((relative, function, line))
    return out


def violations(root: Path) -> list[tuple[str, str, int]]:
    return [(path, function, line) for path, function, line in _live_reads(root) if (path, function) not in ALLOWED]


def test_scan_reaches_every_layer() -> None:
    """The walk is recursive: tasks, services, migrations and repositories are all read."""
    scanned = {path.relative_to(APP).parts[0] for path in APP.rglob("*.py")}
    assert {"tasks", "domain", "migrations", "data_access", "api", "mcp_server"} <= scanned


def test_no_code_reads_a_single_fixed_page() -> None:
    assert violations(APP) == [], (
        "a fixed list window reads one page and ignores the rest (#2012, #2015, #2025); use "
        "app.data_access.arango.base_repository.get_all_pages(repo, ...) / read_all_pages(fetch), an AQL "
        "aggregate, or add an ALLOWED entry that says why the collection cannot outgrow the window"
    )


def test_every_allow_list_entry_is_still_a_real_fixed_window_read() -> None:
    live = {(path, function) for path, function, _line in _live_reads(APP)}
    stale = sorted(set(ALLOWED) - live)
    assert stale == [], f"stale allow-list entries (the read was fixed or removed): {stale}"
    assert all(len(reason) > 20 for reason in ALLOWED.values()), "an allow-list entry needs a real reason"


def test_the_scan_is_not_vacuous_on_the_live_tree() -> None:
    """The detector sees the allowed reads in app/ in both the keyword and the constant shape.

    Every allow-listed function holds a live fixed window (stale check above), and the
    live tree carries a keyword-literal window and a module-constant window: a detector
    that matched nothing, or lost the constant resolution, fails here instead of
    passing silently.
    """
    live = _live_reads(APP)
    assert {(p, f) for p, f, _ in live} == set(ALLOWED)
    lines = [(APP / p).read_text(encoding="utf-8").splitlines()[line - 1] for p, _f, line in live]
    assert any("limit=200" in text for text in lines), "keyword literal window not seen"
    assert any(re.search(r"limit=_[A-Z_]+", text) for text in lines), "module-constant window not seen"


class TestDetector:
    """Each spelling the old code used is caught; a paged, helper-routed or single-row read is not."""

    @pytest.mark.parametrize(
        "call",
        [
            "repo.get_all(offset=0, limit=1000, all_tenants=True)",
            "repo.get_all(offset=0, limit=500, all_tenants=True)",
            "repo.get_all(0, 1000, all_tenants=True)",
            "repo.get_all(0, 10000)",
            "repo.get_all(limit=5000, all_tenants=True)",
            "repo.get_all(offset=0, limit=1000)",
            "self.repo.get_all(offset=0, limit=50, tenant_key=tk)",
            "repo.get_all(\n        offset=0,\n        limit=500,\n        tenant_key=tk,\n    )",
            # #2025: every list-method name, positional and keyword
            "ipm_repo.get_all_pests(0, 200)",
            "ps_repo.get_all_sequences(0, 500)",
            "self._repo.get_all_indicators(0, 1000)",
            "self._repo.list_by_tenant(tenant_key, offset=0, limit=1000)",
            "plant_service.list_plants(offset=0, limit=10000, tenant_key=tk)",
            "self._repo.list_feedings(system_key, tenant_key, offset=0, limit=500)",
            "self._events.get_page(filters=f, sort='created_at', limit=500)",
            "audit_repo.list_for_service_account(key, limit=200)",
            "repo.get_all_substrates(offset=0, limit=500)",
            "self._x.find_by_field('a', b, offset=0, limit=20)",
            # a module constant (the #2015 blind spot) is resolved
            "repo.get_all_sequences(0, PAGE)",
            "repo.get_all(offset=0, limit=PAGE, all_tenants=True)",
            "fetch(offset=0, limit=PAGE)",
        ],
    )
    def test_fixed_window_is_flagged(self, call: str) -> None:
        assert fixed_window_reads(f"PAGE = 500\n\n\ndef task():\n    rows, _ = {call}\n") == [("task", 5)]

    @pytest.mark.parametrize(
        "call",
        [
            "get_all_pages(repo, all_tenants=True)",
            "get_all_pages(repo, tenant_key=tk, filters={'a': 1})",
            "read_all_pages(ipm_repo.get_all_pests)",
            "read_all_pages(lambda offset, limit: repo.list_by_tenant(tk, offset=offset, limit=limit))",
            "repo.get_all(offset=offset, limit=100)",
            "repo.get_all(offset=offset, limit=batch_size)",
            "repo.get_all(offset=0, limit=settings.page)",  # documented blind spot: not a constant
            "repo.get_all(offset=0, limit=IMPORTED)",  # documented blind spot: not a module constant here
            "repo.find_by_field('a', b, sort='t', sort_direction='DESC', offset=0, limit=1)",  # single row
            "repo.get_all(offset=0, limit=1)",  # single-row count probe
            "range(0, 101)",
            "date(2026, 5)",
            "repo.recent(0, 50)",  # documented blind spot: not a list-method name
            "repo.get_all_pests(offset, 200)",
        ],
    )
    def test_paged_unrecognised_or_single_row_read_is_not_flagged(self, call: str) -> None:
        assert fixed_window_reads(f"PAGE = 500\n\n\ndef task():\n    rows = {call}\n") == []

    def test_a_constant_bound_in_a_function_is_not_a_module_constant(self) -> None:
        source = "def task():\n    PAGE = 500\n    return repo.get_all(offset=0, limit=PAGE)\n"
        assert fixed_window_reads(source) == []

    def test_annotated_module_constant_is_resolved(self) -> None:
        source = "PAGE: int = 500\n\n\ndef task():\n    return repo.list_by_tenant(tk, offset=0, limit=PAGE)\n"
        assert fixed_window_reads(source) == [("task", 5)]

    def test_allow_list_suppresses_only_its_own_function(self, monkeypatch, tmp_path: Path) -> None:
        (tmp_path / "t.py").write_text(
            "def a():\n    repo.get_all(offset=0, limit=10)\ndef b():\n    repo.list_things(offset=0, limit=10)\n"
        )
        monkeypatch.setitem(ALLOWED, ("t.py", "a"), "a bounded lookup table that cannot exceed ten rows")
        assert violations(tmp_path) == [("t.py", "b", 4)]

    def test_nested_directories_are_scanned_and_keyed_by_relative_path(self, tmp_path: Path) -> None:
        nested = tmp_path / "domain" / "services"
        nested.mkdir(parents=True)
        (nested / "s.py").write_text("def load():\n    repo.get_all_pests(0, 500)\n")
        assert violations(tmp_path) == [("domain/services/s.py", "load", 2)]
