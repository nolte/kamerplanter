"""#2012/#2015 class guard: no code in ``app/`` treats one ``get_all`` page as the whole collection.

``repo.get_all(offset=0, limit=1000, all_tenants=True)`` returns *at most* 1000 rows
plus a ``total``. Nine reads in ``app/tasks`` (#2012) and fifteen more in services,
seed loaders and repositories (#2015) called it once, iterated the rows and dropped
the ``total``: past the page every row was silently never visited (a plant missing
from the care dashboard, a seed product created twice, an import duplicate not seen).

**The rule.** Anywhere under ``app/``, a ``<anything>.get_all(...)`` call whose
``limit`` is an integer literal and whose ``offset`` is absent or an integer literal
is a single fixed window, i.e. one page. Such a call is a violation unless
:data:`ALLOWED` names it with a reason. The sanctioned spelling is
``get_all_pages(repo, ...)`` from ``app.data_access.arango.base_repository`` (it pages
until the offset reaches ``total``); a hand-written paging loop passes because its
``offset`` is a variable. The scan is an AST walk, so a call split over several
lines is seen (two of the #2015 sites were missed by the issue's line-based grep).

Spellings this does NOT see
---------------------------

* a limit held in a variable or constant (``limit=PAGE``, ``limit=_SCAN_LIMIT``,
  ``limit=settings.x``) together with a fixed offset: the call is not recognised as
  a fixed window (the MCP tools use this spelling on purpose and report
  ``truncated``);
* a ``get_all`` reached through an alias (``fetch = repo.get_all; fetch(...)``) or
  through ``getattr(repo, "get_all")``;
* other list methods with the same defect (``get_all_pests(0, 200)``,
  ``get_all_sequences(0, 500)``, ``list_by_tenant(..., offset=0, limit=1000)``,
  ``list_plants(offset=0, limit=10000)``); swept by hand in #2015 and tracked as
  #2025, not guarded here;
* an AQL ``LIMIT <n>`` literal inside a repository query, and a ``[:n]`` slice applied
  after a complete read.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"

#: ``(path relative to app/, enclosing function)`` -> reason this single-window read is
#: correct. An entry needs a reason that says why the collection cannot outgrow the
#: window (bounded by construction), or why only the ``total`` is read.
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
    ("api/v1/admin/recognition/router.py", "get_recognition_status"): (
        "limit=1 is a count probe: only the returned total is used, the rows are discarded"
    ),
}


def _int_literal(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)


def fixed_window_reads(source: str) -> list[tuple[str, int]]:
    """``(enclosing function, line)`` of every ``get_all`` call that asks for one fixed window."""
    tree = ast.parse(source)
    found: list[tuple[str, int]] = []

    def visit(node: ast.AST, function: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else function
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "get_all"
                and _is_fixed_window(child)
            ):
                found.append((function, child.lineno))
            visit(child, name)

    visit(tree, "<module>")
    return found


def _is_fixed_window(call: ast.Call) -> bool:
    keywords = {kw.arg: kw.value for kw in call.keywords if kw.arg}
    offset = keywords.get("offset", call.args[0] if call.args else None)
    limit = keywords.get("limit", call.args[1] if len(call.args) > 1 else None)
    return _int_literal(limit) and (offset is None or _int_literal(offset))


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
    assert {"tasks", "domain", "migrations", "data_access", "api"} <= scanned


def test_no_code_reads_a_single_fixed_page() -> None:
    assert violations(APP) == [], (
        "a fixed get_all window reads one page and ignores the rest (#2012, #2015); use "
        "app.data_access.arango.base_repository.get_all_pages(repo, ...) or add an ALLOWED "
        "entry that says why the collection cannot outgrow the window"
    )


def test_every_allow_list_entry_is_still_a_real_fixed_window_read() -> None:
    live = {(path, function) for path, function, _line in _live_reads(APP)}
    stale = sorted(set(ALLOWED) - live)
    assert stale == [], f"stale allow-list entries (the read was fixed or removed): {stale}"
    assert all(len(reason) > 20 for reason in ALLOWED.values()), "an allow-list entry needs a real reason"


class TestDetector:
    """Each spelling the old code used is caught; a paged or helper-routed read is not."""

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
        ],
    )
    def test_fixed_window_is_flagged(self, call: str) -> None:
        assert fixed_window_reads(f"def task():\n    rows, _ = {call}\n") == [("task", 2)]

    @pytest.mark.parametrize(
        "call",
        [
            "get_all_pages(repo, all_tenants=True)",
            "get_all_pages(repo, tenant_key=tk, filters={'a': 1})",
            "repo.get_all(offset=offset, limit=100)",
            "repo.get_all(offset=offset, limit=batch_size)",
            "repo.get_all(offset=0, limit=PAGE, all_tenants=True)",  # the documented blind spot
            "repo.get_all_tasks(0, 200, {})",
            "repo.get_all_pests(0, 200)",  # other list methods: swept by hand, not guarded
        ],
    )
    def test_paged_or_unrecognised_read_is_not_flagged(self, call: str) -> None:
        assert fixed_window_reads(f"def task():\n    rows = {call}\n") == []

    def test_allow_list_suppresses_only_its_own_function(self, monkeypatch, tmp_path: Path) -> None:
        (tmp_path / "t.py").write_text(
            "def a():\n    repo.get_all(offset=0, limit=10)\ndef b():\n    repo.get_all(offset=0, limit=10)\n"
        )
        monkeypatch.setitem(ALLOWED, ("t.py", "a"), "a bounded lookup table that cannot exceed ten rows")
        assert violations(tmp_path) == [("t.py", "b", 4)]

    def test_nested_directories_are_scanned_and_keyed_by_relative_path(self, tmp_path: Path) -> None:
        nested = tmp_path / "domain" / "services"
        nested.mkdir(parents=True)
        (nested / "s.py").write_text("def load():\n    repo.get_all(0, 500)\n")
        assert violations(tmp_path) == [("domain/services/s.py", "load", 2)]
