"""#2902 — a server-built species name goes through the one display rule, never ``common_names[0]``.

``Species.common_names`` is a flat, language-mixed list; the seed files list the English name
first for most species. Every reader that built ONE name by taking the first entry showed
"Tomato" in the German UI: eleven of them, in services, an engine, a router, an MCP tool and
four AQL projections (``FIRST(species.common_names)``, ``species.common_names[0]``). The rule —
requested language, else ``de``, else the scientific name; a species without a language map
falls back to its first listed name — lives in :mod:`app.domain.models.species_names` and only
there.

**The rule.** No file under ``app/`` outside :data:`_ALLOWED` takes the first common name on its
own, in any of these spellings:

* Python: ``<x>.common_names[0]`` / ``common_names[0]`` (any name or attribute ending in
  ``common_names``, e.g. ``species_common_names[0]``), ``(<x>.common_names or [...])[0]``,
  ``<row>["common_names"][0]``, ``<row>.get("common_names")[0]`` and ``next(iter(<…common_names…>))``;
* AQL in a string literal (or the literal parts of an f-string): ``common_names[0]`` and
  ``FIRST(<…>common_names)``.

Docstrings are not read: they explain the defect, they do not commit it.

**Blind spots**, named rather than discovered later:

* an alias — ``names = species.common_names`` and then ``names[0]``, or AQL that ``LET``-binds the
  list and takes ``FIRST`` of the binding;
* slicing or unpacking — ``common_names[:1]``, ``first, *_ = species.common_names``, ``NTH(…, 0)``;
* a new repository method whose row field is named differently and is filled with the first entry
  by an AQL spelling not listed above, or a query assembled from non-literal pieces;
* a name read that is not the first entry at all (``common_names[-1]``, ``min(common_names)``).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"

#: ``path relative to app/`` -> why the file may read the first entry itself.
_ALLOWED: dict[str, str] = {
    "domain/models/species_names.py": "the resolver itself, including the no-map fallback to the first listed name",
    "data_access/external/gbif_adapter.py": "external identification/enrichment names (GBIF), not the catalogue's",
    "data_access/external/perenual_adapter.py": "external enrichment names (Perenual), not the catalogue's",
    "data_access/external/plantnet_adapter.py": "external identification names (Pl@ntNet), not the catalogue's",
    "domain/engines/identification_engine.py": "carries a provider's suggestion names through unchanged",
    "domain/engines/enrichment_engine.py": "merges external enrichment names, it shows none",
    "domain/models/identification.py": "the identification result model (external names)",
    "domain/models/enrichment.py": "the enrichment result model (external names)",
    "domain/interfaces/plant_identification_adapter.py": "the identification adapter contract (external names)",
}

_AQL_SPELLINGS = (
    re.compile(r"common_names\s*\[\s*0\s*\]"),
    re.compile(r"FIRST\s*\(\s*[\w.]*common_names\s*\)", re.IGNORECASE),
)


def _names_common_names(node: ast.AST) -> bool:
    """``node`` is a name, attribute or string key that denotes a ``…common_names`` list (not the i18n map)."""
    if isinstance(node, ast.Name):
        return node.id.endswith("common_names")
    if isinstance(node, ast.Attribute):
        return node.attr.endswith("common_names")
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.endswith("common_names")
    return False


def _is_common_names_list(node: ast.AST) -> bool:
    """``x.common_names``, ``common_names``, ``row["common_names"]`` or ``row.get("common_names", …)``."""
    if _names_common_names(node) and not isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Subscript):
        return _names_common_names(node.slice)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
        return _names_common_names(node.args[0])
    return False


def _mentions_common_names(node: ast.AST) -> bool:
    return any(_is_common_names_list(child) for child in ast.walk(node))


def _is_zero(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == 0 and not isinstance(node.value, bool)


def _docstrings(tree: ast.AST) -> set[int]:
    """``id`` of every docstring constant (module, class, function)."""
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


def first_name_reads(source: str) -> list[int]:
    """Line numbers of every read of the first common name in ``source`` (see the module docstring)."""
    tree = ast.parse(source)
    docstrings = _docstrings(tree)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and _is_zero(node.slice):
            value = node.value
            if _is_common_names_list(value) or (isinstance(value, ast.BoolOp) and _mentions_common_names(value)):
                lines.add(node.lineno)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "next"
            and node.args
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Name)
            and node.args[0].func.id == "iter"
            and _mentions_common_names(node.args[0])
        ):
            lines.add(node.lineno)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            for match in (m for pattern in _AQL_SPELLINGS for m in pattern.finditer(node.value)):
                lines.add(node.lineno + node.value.count("\n", 0, match.start()))
    return sorted(lines)


def _resolver_calls(source: str) -> int:
    return sum(
        1
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"localized_common_name", "localized_vernacular_name"}
    )


def _sweep() -> tuple[list[str], int, int]:
    findings: list[str] = []
    calls = 0
    files = 0
    for path in sorted(APP.rglob("*.py")):
        rel = path.relative_to(APP).as_posix()
        source = path.read_text(encoding="utf-8")
        files += 1
        if rel == "domain/models/species_names.py":
            continue
        calls += _resolver_calls(source)
        if rel in _ALLOWED:
            continue
        findings.extend(f"{rel}:{line}" for line in first_name_reads(source))
    return findings, calls, files


def test_no_reader_shows_the_first_common_name_on_its_own() -> None:
    findings, calls, files = _sweep()

    assert findings == [], (
        "a species display name goes through app.domain.models.species_names "
        f"(localized_common_name / localized_vernacular_name), never the first list entry (#2902): {findings}"
    )
    # Not vacuous: the sweep read the app and saw the converted readers call the resolver.
    assert files > 500, f"the sweep read only {files} files"
    assert calls >= 12, f"the sweep saw only {calls} resolver calls"


def test_every_allowed_file_exists() -> None:
    """An allowance for a file that is gone would silently cover a new file of the same name."""
    missing = [rel for rel in _ALLOWED if not (APP / rel).is_file()]

    assert missing == []


def test_the_detector_sees_every_spelling_it_claims() -> None:
    planted = (
        "def a(species):\n"  # 1
        "    return species.common_names[0]\n"  # 2
        "def b(common_names):\n"  # 3
        "    return common_names[0]\n"  # 4
        "def c(species):\n"  # 5
        "    return (species.common_names or [None])[0]\n"  # 6
        "def d(row):\n"  # 7
        "    return row['common_names'][0]\n"  # 8
        "def e(row):\n"  # 9
        "    return row.get('species_common_names', [])[0]\n"  # 10
        "def f(species):\n"  # 11
        "    return next(iter(species.common_names), None)\n"  # 12
        "Q = '''\n"  # 13
        "  LET n = FIRST(species.common_names)\n"  # 14
        "  LET m = sp.common_names[0]\n"  # 15
        "'''\n"  # 16
        "def g(col):\n"  # 17
        "    return f'FOR s IN {col} RETURN first(s.common_names)'\n"  # 18
    )

    assert first_name_reads(planted) == [2, 4, 6, 8, 10, 12, 14, 15, 18]


def test_the_detector_leaves_what_is_not_a_first_name_read() -> None:
    planted = (
        '"""Docstring: the old reader took species.common_names[0]."""\n'  # 1
        "def a(species):\n"  # 2
        '    """FIRST(species.common_names) in prose is no read."""\n'  # 3
        "    return species.common_names_i18n['de'][0]\n"  # 4
        "def b(species):\n"  # 5
        "    return list(species.common_names)\n"  # 6
        "def c(species):\n"  # 7
        "    return species.traits[0]\n"  # 8
        "def d(species):\n"  # 9
        "    return species.common_names[1]\n"  # 10
    )

    assert first_name_reads(planted) == []
