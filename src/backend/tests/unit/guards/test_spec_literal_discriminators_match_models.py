"""A ``Literal[...]`` the spec declares for a model field is the one the code declares (#1620).

REQ-023 §Datenmodell says ``account_type: Literal['human', 'service']`` in three
places; the model shipped ``Literal["user", "service"]``. Nothing compared the two,
and the divergence went unnoticed from April to September 2026 — until #1616 made
the value a security boundary (``allows_interactive_auth``): a predicate written
from the spec, ``account_type == 'human'``, was false for every stored account, so
"is this a human?" failed in the permissive direction.

The rename is the cheap half. This module is the guard the issue asked for, and it
enumerates the **class** rather than the one field: every ``(model, field)`` for
which the spec declares a string ``Literal`` *and* the code declares a Pydantic
field typed as a string ``Literal`` — directly, through ``Optional[...]``/``| None``,
or through a module-level alias such as ``AccountType = Literal[...]`` — must carry
the same value set on both sides. A third spelling of ``account_type`` goes red
here whichever side introduces it.

What is measured, and what is not
=================================

* Joined on ``(model name, field name)``. The spec names its models as
  ``**`:User`**`` headings (REQ-023 style) or as ``class User(...)`` lines inside
  code fences; a ``Literal`` declared outside any model heading is not a model
  discriminator and is ignored.
* The code side is limited to fields typed as a **string** ``Literal``. Fields typed
  as an enum are a different class with a different guard shape
  (``test_provider_type_vocabulary.py``, ``test_entity_name_vocabulary.py``) and
  are not counted here; a spec ``Literal`` whose code field is an enum is therefore
  *unjoined*, not "agreeing".
* **Prose does not count on either side.** The spec side drops HTML comments
  before parsing. The code side is an ``ast`` walk over annotations, which is the
  same lexer ``scripts/source_text.py`` uses for Python and the reason its output
  is exact there: a ``# account_type: Literal["x"]`` in a comment never becomes an
  annotation node, and a docstring is an expression statement, not a field. So
  neither a comment nor a ``<!-- ... -->`` in the spec can satisfy or break the
  check. The self-tests at the bottom keep that true — they are the falsification,
  not the docstring. (``executable_source`` itself is not applied here: its
  line-preserving output is meant for substring gates and is not guaranteed to
  re-parse; measured, it does not for every module under ``app/``.)

Known divergences are a **register**, not an allowlist: an entry must still
diverge (a stale one goes red, so the register only shrinks), and the anchor of
this issue — ``User.account_type`` — is deliberately *not* in it. The join count
carries a floor below today's inventory so that a parser that quietly stops
matching cannot turn the whole module vacuously green (NFR-018 §2).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
assert _REPO_ROOT is not None
_SPEC_DIRS = (_REPO_ROOT / "spec" / "req", _REPO_ROOT / "spec" / "nfr")
_APP_DIR = _REPO_ROOT / "src" / "backend" / "app"

#: (model, field) pairs where spec and code are known to disagree, with the reason.
#: An entry that stops diverging goes red (``test_the_register_holds_only_live_divergences``).
#: All three are one REQ-026 question, tracked as #1670.
_KNOWN_DIVERGENT: dict[tuple[str, str], str] = {
    ("BiofilterDimensioning", "status"): "REQ-026 §Biofilter lists three states; the engine also reports `unknown`.",
    ("HealthAlert", "severity"): "REQ-026 §Health-Alerts lists three levels; the engine also emits `ok`.",
    ("WaterQualityEvaluation", "severity"): "REQ-026 §Wasserqualität lists three levels; the engine also emits `info`.",
}

#: Floor on the number of joined pairs. 14 on 2026-09-23; set below that so a
#: legitimately retired model does not trip it, and high enough that a parser
#: which stopped matching (0 joins → nothing to compare) is caught.
_JOINED_FLOOR = 12

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_MODEL_HEADING = re.compile(r"\*\*`:?([A-Z][A-Za-z0-9]+)`\*\*")
_PY_CLASS = re.compile(r"^\s*class\s+([A-Z][A-Za-z0-9]+)\s*\(")
_LITERAL_FIELD = re.compile(r"`?([a-z][a-z0-9_]*)\s*:\s*(?:Optional\[)?Literal\[([^\]]*)\]")
_QUOTED = re.compile(r"'([^']*)'|\"([^\"]*)\"")


# ── spec side ─────────────────────────────────────────────────────────────────


def spec_literals_in(text: str, *, origin: str = "<text>") -> dict[tuple[str, str], list[tuple[frozenset[str], str]]]:
    """Every ``field: Literal[...]`` under a model heading, keyed by ``(model, field)``.

    HTML comments are removed first: a commented-out declaration is prose.
    """
    found: dict[tuple[str, str], list[tuple[frozenset[str], str]]] = {}
    model: str | None = None
    for lineno, line in enumerate(_HTML_COMMENT.sub("", text).splitlines(), start=1):
        heading = _MODEL_HEADING.search(line)
        if heading:
            model = heading.group(1)
        py_class = _PY_CLASS.match(line)
        if py_class:
            model = py_class.group(1)
        for match in _LITERAL_FIELD.finditer(line):
            values = frozenset(a or b for a, b in _QUOTED.findall(match.group(2)))
            if model and values:
                found.setdefault((model, match.group(1)), []).append((values, f"{origin}:{lineno}"))
    return found


def _spec_literals() -> dict[tuple[str, str], list[tuple[frozenset[str], str]]]:
    found: dict[tuple[str, str], list[tuple[frozenset[str], str]]] = {}
    for spec_dir in _SPEC_DIRS:
        for md in sorted(spec_dir.glob("*.md")):
            hits = spec_literals_in(md.read_text(encoding="utf-8"), origin=str(md.relative_to(_REPO_ROOT)))
            for key, declarations in hits.items():
                found.setdefault(key, []).extend(declarations)
    return found


# ── code side ─────────────────────────────────────────────────────────────────


def _string_literal_values(node: ast.expr, aliases: dict[str, frozenset[str]]) -> frozenset[str] | None:
    """The string members of a ``Literal[...]`` annotation, seen through the wrappers the models use."""
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        if node.value.id == "Literal":
            members = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            values = frozenset(m.value for m in members if isinstance(m, ast.Constant) and isinstance(m.value, str))
            return values or None
        if node.value.id == "Optional":
            return _string_literal_values(node.slice, aliases)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _string_literal_values(node.left, aliases) or _string_literal_values(node.right, aliases)
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    return None


def code_literals_in(source: str, *, origin: str = "<source>") -> dict[tuple[str, str], tuple[frozenset[str], str]]:
    """Every class field typed as a string ``Literal``, keyed by ``(class, field)``.

    Annotations only: a declaration that lives in a comment or a docstring is not
    an annotation node and is therefore not a declaration.
    """
    tree = ast.parse(source)
    aliases: dict[str, frozenset[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            values = _string_literal_values(node.value, aliases)
            if values:
                aliases[node.targets[0].id] = values
    found: dict[tuple[str, str], tuple[frozenset[str], str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                values = _string_literal_values(stmt.annotation, aliases)
                if values:
                    found[(node.name, stmt.target.id)] = (values, f"{origin}:{stmt.lineno}")
    return found


def _code_literals() -> dict[tuple[str, str], tuple[frozenset[str], str]]:
    found: dict[tuple[str, str], tuple[frozenset[str], str]] = {}
    for py in sorted(_APP_DIR.rglob("*.py")):
        found.update(code_literals_in(py.read_text(encoding="utf-8"), origin=str(py.relative_to(_REPO_ROOT))))
    return found


# ── the join ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def joined() -> dict[tuple[str, str], tuple[list[tuple[frozenset[str], str]], tuple[frozenset[str], str]]]:
    spec, code = _spec_literals(), _code_literals()
    return {key: (spec[key], code[key]) for key in sorted(set(spec) & set(code))}


class TestSpecAndCodeAgree:
    def test_every_joined_pair_agrees_unless_registered(self, joined) -> None:
        """The rule. A message names both files so the reader knows which side to read."""
        divergent = []
        for key, (spec_hits, (code_values, code_loc)) in joined.items():
            if key in _KNOWN_DIVERGENT:
                continue
            for spec_values, spec_loc in spec_hits:
                if spec_values != code_values:
                    divergent.append(
                        f"{key[0]}.{key[1]}: {spec_loc} declares {sorted(spec_values)} "
                        f"<-> {code_loc} declares {sorted(code_values)}"
                    )
        assert not divergent, "spec and code disagree on a model discriminator:\n  " + "\n  ".join(divergent)

    def test_the_anchor_of_this_issue_is_joined_and_agrees(self, joined) -> None:
        """``User.account_type`` — REQ-023 ↔ ``app/domain/models/user.py`` — is in the class."""
        spec_hits, (code_values, _) = joined[("User", "account_type")]
        assert code_values == frozenset({"human", "service"})
        assert all(values == code_values for values, _ in spec_hits)

    def test_the_register_holds_only_live_divergences(self, joined) -> None:
        """A registered pair that now agrees is a stale entry; the register only shrinks."""
        stale = []
        for key, reason in _KNOWN_DIVERGENT.items():
            assert key in joined, f"registered pair {key} is not joined any more ({reason})"
            spec_hits, (code_values, _) = joined[key]
            if all(values == code_values for values, _ in spec_hits):
                stale.append(f"{key[0]}.{key[1]} agrees now — remove it from _KNOWN_DIVERGENT")
        assert not stale, "\n".join(stale)

    def test_the_join_is_not_vacuous(self, joined) -> None:
        """A parser that stopped matching would compare nothing and pass; the floor catches it."""
        assert len(joined) >= _JOINED_FLOOR, (
            f"only {len(joined)} joined pairs; the parsers used to find {_JOINED_FLOOR}+"
        )


class TestProseDoesNotCount:
    """The self-tests for the "a comment must not satisfy it" property, both sides."""

    _SPEC = (
        "- **`:User`** — account\n"
        "  - Properties:\n"
        "    - `account_type: Literal['human', 'service']`\n"
        "    <!-- - `status: Literal['ghost']` -->\n"
    )
    _CODE = (
        "from typing import Literal\n"
        'AccountType = Literal["human", "service"]\n'
        "class User:\n"
        '    """status: Literal["ghost"]"""\n'
        "    account_type: AccountType\n"
        '    # nickname: Literal["ghost"]\n'
    )

    def test_an_html_comment_in_the_spec_declares_nothing(self) -> None:
        found = spec_literals_in(self._SPEC)
        assert found == {("User", "account_type"): [(frozenset({"human", "service"}), "<text>:3")]}

    def test_a_comment_or_docstring_in_the_code_declares_nothing(self) -> None:
        found = code_literals_in(self._CODE)
        assert set(found) == {("User", "account_type")}
        assert found[("User", "account_type")][0] == frozenset({"human", "service"})

    def test_the_alias_is_seen_through(self) -> None:
        """``AccountType = Literal[...]`` is how ``user.py`` declares it; a direct-only walk would miss the anchor."""
        assert code_literals_in(self._CODE)[("User", "account_type")][0] == frozenset({"human", "service"})
