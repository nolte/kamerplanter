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

The role vocabulary (#2121)
===========================

The role model is typed as **enums** (``TenantRole``, ``AdminScope``, the tenant
lifecycle ``TenantStatus``), which the join above deliberately does not count. Its
drift also had a second shape: REQ-023 §5a kept writing ``role: admin`` long after
migration ``v0032`` retired the value — in prose, in pseudocode, in JSON examples
— and nothing compared that to the code. Three checks close it:

* **The enum join** — the same ``(model, field)`` join, for fields typed as one of
  :data:`_ROLE_MODEL_ENUMS` (directly, ``| None``, ``Optional[...]`` or
  ``list[...]``). A spec ``Literal`` for such a field must name exactly the enum's
  values. Limited to the role model on purpose: the same join over *every* enum
  finds further divergent pairs in REQ-001/002/004/006/007/014/019, recorded in the
  #2121 PR as a follow-up rather than silently registered here.
* **Role literals in REQ-023/024/049** — every value written for a role-bearing key
  (``role: lead``, ``"new_role": "lead"``, ``tenant_roles[...] == "lead"``,
  ``Rolle 'lead'``, ``grower → lead``) is a ``TenantRole`` value, every
  ``admin_scopes`` list member an ``AdminScope`` value. Version-history rows are
  history and are skipped; a deliberate historical mention (the ``v0032`` mapping
  table) is a register entry that must keep matching.
* **Role lists in the steering files** — ``CLAUDE.md`` and its offload name the
  roles as slash lists (``viewer/grower/lead``); every member must be a role.
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
#: Empty since #1670 agreed REQ-026 and the aquaponics engine; it only shrinks.
_KNOWN_DIVERGENT: dict[tuple[str, str], str] = {}

#: Floor on the number of joined pairs. 14 on 2026-09-23; set below that so a
#: legitimately retired model does not trip it, and high enough that a parser
#: which stopped matching (0 joins → nothing to compare) is caught.
_JOINED_FLOOR = 12

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_MODEL_HEADING = re.compile(r"\*\*`:?([A-Z][A-Za-z0-9]+)`\*\*")
_PY_CLASS = re.compile(r"^\s*class\s+([A-Z][A-Za-z0-9]+)\s*\(")
_LITERAL_FIELD = re.compile(r"`?([a-z][a-z0-9_]*)\s*:\s*(?:Optional\[|list\[)?Literal\[([^\]]*)\]")
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


# ── the role vocabulary (#2121) ───────────────────────────────────────────────

#: The enums the role model is typed with. The enum join is limited to these (see the
#: module docstring for why it is not run over every enum here).
_ROLE_MODEL_ENUMS = ("TenantRole", "AdminScope", "TenantStatus", "TenantType", "InvitationStatus", "InvitationType")
_ENUMS_MODULE = _APP_DIR / "common" / "enums.py"

#: The documents that own the role vocabulary (REQ-049 is the authority, REQ-023/024 its users).
_ROLE_MODEL_SPECS = ("REQ-023_*.md", "REQ-024_*.md", "REQ-049_*.md")
#: The steering files agents read on every turn (CLAUDE.md "Domain Concepts" and decision 9).
_STEERING_FILES = (_REPO_ROOT / "CLAUDE.md", _REPO_ROOT / ".claude" / "reference" / "claude-md-offload.md")

#: Deliberate mentions of a retired value: (spec file prefix, value, a substring of the line).
#: An entry whose line no longer exists goes red, so the register only shrinks.
_HISTORICAL_ROLE_LITERALS: dict[tuple[str, str, str], str] = {
    (
        "REQ-049",
        "admin",
        '| `role: "admin"` | `role: "lead"`',
    ): "the v0032 mapping table names the value it migrates away from",
}

#: Joined (model, field) pairs typed with a role-model enum: 7 on 2026-10-05 (Membership.role,
#: Membership.admin_scopes, Invitation.role/status/invitation_type, Tenant.status/tenant_type).
#: The floor sits below that.
_ROLE_ENUM_JOIN_FLOOR = 5
#: Role/scope literals found in REQ-023/024/049: 66 on 2026-10-05; the floor sits below that.
_ROLE_LITERAL_FLOOR = 50

#: Keys whose value is a domain role.
_ROLE_KEY = re.compile(
    r"""\b(?:role|new_role|previous_role|default_role|target_role|min_role)\b["'`]?\s*(?:==|!=|=|:)\s*["'`]?([a-z][a-z_]*)\b(?![.\[(])"""
)
_TOKEN_ROLE = re.compile(r"""tenant_roles\[\s*["'][^"']+["']\s*\]\s*(?:==|!=)\s*["']([a-z_]+)["']""")
_ROLE_WORDS = r"viewer|grower|lead|admin|owner|member|platform_viewer"
#: German prose names a role after the word "Rolle" ("mit Rolle 'admin'", "jeder Rolle (auch `admin`)");
#: only role-like words are taken there, a backticked field name further on is not a role.
_GERMAN_ROLE = re.compile(rf"""\bRolle\b[^\n*|]{{0,30}}?['"`]({_ROLE_WORDS})['"`]""")
_ROLE_ARROW = re.compile(rf"""`?\b({_ROLE_WORDS})\b`?\s*(?:→|->)\s*`?([a-z_]+)\b""")
_SCOPE_LIST = re.compile(r"""\badmin_scopes\b["'`]?\s*[:=]\s*\[([^\]]*)\]""")
_SCOPE_MEMBER = re.compile(r"""[a-z_]+""")
_SLASH_ROLES = re.compile(rf"""\b((?:{_ROLE_WORDS})(?:/(?:{_ROLE_WORDS}|[a-z]+))+)\b""")
_VERSION_ROW = re.compile(r"^\|\s*\d+\.\d+\s*\|")
#: A ``role:`` in a type annotation or an ARIA attribute is not a domain role.
_NOT_A_ROLE_VALUE = frozenset(
    {"str", "int", "bool", "list", "dict", "none", "any", "optional"}
    | {"alert", "status", "dialog", "button", "region", "navigation", "main", "log", "progressbar", "tab"}
    | {"tabpanel", "tablist", "menu", "menuitem", "listbox", "option", "presentation", "img", "link", "group"}
)


def enum_values_in(source: str) -> dict[str, frozenset[str]]:
    """Every ``StrEnum`` class of *source* with its string values (an ``ast`` walk, like the code side above)."""
    found: dict[str, frozenset[str]] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef) and any(ast.unparse(base).endswith("StrEnum") for base in node.bases):
            values = frozenset(
                stmt.value.value
                for stmt in node.body
                if isinstance(stmt, ast.Assign)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            )
            if values:
                found[node.name] = values
    return found


def _enum_of(node: ast.expr, enums: dict[str, frozenset[str]]) -> frozenset[str] | None:
    if isinstance(node, ast.Name):
        return enums.get(node.id)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in ("Optional", "list"):
        return _enum_of(node.slice, enums)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _enum_of(node.left, enums) or _enum_of(node.right, enums)
    return None


def code_enum_fields_in(
    source: str, enums: dict[str, frozenset[str]], *, origin: str = "<source>"
) -> dict[tuple[str, str], tuple[frozenset[str], str]]:
    """Every class field typed with one of *enums*, keyed by ``(class, field)``."""
    found: dict[tuple[str, str], tuple[frozenset[str], str]] = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                values = _enum_of(stmt.annotation, enums)
                if values:
                    found[(node.name, stmt.target.id)] = (values, f"{origin}:{stmt.lineno}")
    return found


def role_literals_in(text: str, *, origin: str = "<text>") -> list[tuple[str, str, str, str]]:
    """Every role or scope value written for a role-bearing key: ``(axis, value, location, line)``.

    ``axis`` is ``"role"`` or ``"scope"``. HTML comments are blanked line-preservingly
    (a commented-out example is prose); version-history rows are skipped (they record
    what was true then).
    """
    blanked = _HTML_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    found: list[tuple[str, str, str, str]] = []
    for lineno, line in enumerate(blanked.splitlines(), start=1):
        if _VERSION_ROW.match(line):
            continue
        loc = f"{origin}:{lineno}"
        values = [m.group(1) for m in _ROLE_KEY.finditer(line)]
        values += [m.group(1) for m in _TOKEN_ROLE.finditer(line)]
        values += [m.group(1) for m in _GERMAN_ROLE.finditer(line)]
        for arrow in _ROLE_ARROW.finditer(line):
            values += [arrow.group(1), arrow.group(2)]
        found += [("role", v, loc, line) for v in values if v not in _NOT_A_ROLE_VALUE]
        for scopes in _SCOPE_LIST.finditer(line):
            found += [("scope", v, loc, line) for v in _SCOPE_MEMBER.findall(scopes.group(1))]
    return found


def slash_role_lists_in(text: str, *, origin: str = "<text>") -> list[tuple[list[str], str]]:
    """Every slash list that starts with a role word (``viewer/grower/lead``), with its location."""
    return [
        (match.group(1).split("/"), f"{origin}:{lineno}")
        for lineno, line in enumerate(text.splitlines(), start=1)
        for match in _SLASH_ROLES.finditer(line)
    ]


def _role_model_spec_files() -> list[Path]:
    return sorted(p for pattern in _ROLE_MODEL_SPECS for p in (_REPO_ROOT / "spec" / "req").glob(pattern))


@pytest.fixture(scope="module")
def vocabulary() -> dict[str, frozenset[str]]:
    enums = enum_values_in(_ENUMS_MODULE.read_text(encoding="utf-8"))
    missing = [name for name in _ROLE_MODEL_ENUMS if name not in enums]
    assert not missing, f"role-model enums not found in {_ENUMS_MODULE.name}: {missing}"
    return {name: enums[name] for name in _ROLE_MODEL_ENUMS}


@pytest.fixture(scope="module")
def role_literals() -> list[tuple[str, str, str, str]]:
    found: list[tuple[str, str, str, str]] = []
    for md in _role_model_spec_files():
        found += role_literals_in(md.read_text(encoding="utf-8"), origin=md.name)
    return found


def _registered(origin: str, value: str, line: str) -> bool:
    return any(
        origin.startswith(prefix) and value == registered and marker in line
        for prefix, registered, marker in _HISTORICAL_ROLE_LITERALS
    )


class TestRoleModelVocabulary:
    def test_enum_typed_role_fields_agree_with_the_spec(self, vocabulary) -> None:
        """A spec ``Literal`` for a field the code types with a role-model enum names exactly its values."""
        code: dict[tuple[str, str], tuple[frozenset[str], str]] = {}
        for py in sorted(_APP_DIR.rglob("*.py")):
            code.update(
                code_enum_fields_in(py.read_text(encoding="utf-8"), vocabulary, origin=str(py.relative_to(_REPO_ROOT)))
            )
        spec = _spec_literals()
        joined = sorted(set(spec) & set(code))
        assert len(joined) >= _ROLE_ENUM_JOIN_FLOOR, f"only {len(joined)} role-model fields joined: {joined}"
        assert ("Membership", "role") in joined and ("Membership", "admin_scopes") in joined
        divergent = [
            f"{model}.{field}: {loc} declares {sorted(values)} <-> {code[(model, field)][1]} declares "
            f"{sorted(code[(model, field)][0])}"
            for model, field in joined
            for values, loc in spec[(model, field)]
            if values != code[(model, field)][0]
        ]
        assert not divergent, "spec and code disagree on a role-model field:\n  " + "\n  ".join(divergent)

    def test_every_role_literal_in_the_role_specs_is_a_tenant_role(self, vocabulary, role_literals) -> None:
        """The rule of #2121: no ``role: admin`` (or any other retired or invented value) in REQ-023/024/049."""
        allowed = {"role": vocabulary["TenantRole"], "scope": vocabulary["AdminScope"]}
        stale = [
            f"{loc}: {axis} {value!r} is not one of {sorted(allowed[axis])}"
            for axis, value, loc, line in role_literals
            if value not in allowed[axis] and not _registered(loc, value, line)
        ]
        assert not stale, "role literals the code does not know:\n  " + "\n  ".join(stale)

    def test_the_historical_register_holds_only_live_entries(self, role_literals) -> None:
        missing = [
            f"{key} — {reason}"
            for key, reason in _HISTORICAL_ROLE_LITERALS.items()
            if not any(
                loc.startswith(key[0]) and value == key[1] and key[2] in line for _, value, loc, line in role_literals
            )
        ]
        assert not missing, "registered historical role literals no longer present (remove them):\n  " + "\n  ".join(
            missing
        )

    def test_the_role_literal_scan_is_not_vacuous(self, role_literals) -> None:
        """A pattern that stopped matching would find nothing and pass; per-file and total floors catch it."""
        assert len(role_literals) >= _ROLE_LITERAL_FLOOR, f"only {len(role_literals)} role literals found"
        per_file = {loc.split(":")[0] for _, _, loc, _ in role_literals}
        assert len(per_file) == len(_role_model_spec_files()) == 3, per_file
        assert {axis for axis, *_ in role_literals} == {"role", "scope"}

    def test_role_lists_in_the_steering_files_name_tenant_roles(self, vocabulary) -> None:
        found = [
            (members, loc)
            for path in _STEERING_FILES
            for members, loc in slash_role_lists_in(path.read_text(encoding="utf-8"), origin=path.name)
        ]
        assert found, "no role list found in CLAUDE.md or its offload — the pattern went blind"
        stale = [
            f"{loc}: {'/'.join(members)}" for members, loc in found if not set(members) <= vocabulary["TenantRole"]
        ]
        assert not stale, "a steering file names roles the code does not have:\n  " + "\n  ".join(stale)


class TestRoleLiteralScanSelfTest:
    """Falsification of the scanner itself: each shape it claims to see, and what it must ignore."""

    def test_each_written_shape_is_seen(self) -> None:
        text = (
            "Membership in tenant/platform (role: admin)\n"
            '  "new_role": "owner",\n'
            'is_admin = tenant_roles["platform"] == "admin"\n'
            "    4. Rolle wird auf 'admin' hochgestuft\n"
            "   a) Max' Rolle: grower → admin\n"
            "  admin_scopes: [management, finance]\n"
        )
        values = [(axis, value) for axis, value, _, _ in role_literals_in(text)]
        assert ("role", "admin") in values
        assert ("role", "owner") in values
        assert values.count(("role", "admin")) == 4
        assert ("scope", "finance") in values and ("scope", "management") in values

    def test_comments_history_rows_types_and_aria_are_not_roles(self) -> None:
        text = (
            "<!-- role: admin -->\n"
            "| 1.7 | 2026-03-17 | role: admin was retired |\n"
            "    - `role: str`\n"
            'Hinweis (`role="alert"`) und `role="status"`\n'
            "    role: m.role,\n"
            "    - `role: Literal['responsible', 'helper']`\n"
            "| AK-29 | Rolle **Leitung** besteht `can_edit_resource` |\n"
            "Die fachliche Rolle ist unabhängig von `admin_scopes` gültig\n"
        )
        assert role_literals_in(text) == []

    def test_a_steering_slash_list_with_a_retired_role_is_seen(self) -> None:
        found = slash_role_lists_in("- **Membership** — role (admin/grower/viewer).\n(viewer/grower/lead)")
        assert [members for members, _ in found] == [["admin", "grower", "viewer"], ["viewer", "grower", "lead"]]

    def test_the_enum_walk_sees_list_and_optional_fields(self) -> None:
        enums = enum_values_in("from enum import StrEnum\nclass R(StrEnum):\n    A = 'a'\n    B = 'b'\n")
        code = code_enum_fields_in(
            "class M:\n    role: R\n    scopes: list[R]\n    maybe: R | None\n    other: str\n", enums
        )
        assert set(code) == {("M", "role"), ("M", "scopes"), ("M", "maybe")}

    def test_the_spec_side_reads_list_of_literal(self) -> None:
        found = spec_literals_in(
            "- **`:Membership`**\n    - `admin_scopes: list[Literal['management', 'technical']]`\n"
        )
        assert found[("Membership", "admin_scopes")][0][0] == frozenset({"management", "technical"})
