"""#1489 — no caller hands ``auto_generate_profile`` a ``*_key`` as the family.

``FAMILY_CARE_MAP`` is keyed by the botanical family **name**; ``Species.family_key``
holds a numeric ArangoDB document key. The two are the same *kind* of thing to a
reader and nothing alike to the map, so passing the key matched no entry and the
engine answered with the ``TROPICAL`` 7-day preset — plausible values, no error,
every plant created since #1440 carrying them for good.

The engine now refuses a numeric value at runtime (``auto_generate_profile`` raises
``ValueError``), and that guard is the one that actually protects the data. This
file is the *earlier* one: it fails on the commit that writes the call, not on the
request that runs it, and it catches the case the runtime guard cannot — a key that
happens to be non-numeric, or a call on a path no test exercises.

**What it matches is the argument's NAME.** ``botanical_family=species.family_key``,
``botanical_family=family_key``, ``botanical_family=row["family_key"]`` — anything
whose spelling ends in ``_key``. A name is not a type, so this is a heuristic; it is
the heuristic that would have caught the defect on the day it was written, which is
the only property being claimed for it.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: Every call that produces care presets, not just the engine method that reads the
#: map. **Measured, and it is the whole point of the set having four names**: the
#: first version of this guard listed the two generators and stayed green against
#: the actual #1489 defect, because ``_bootstrap_care_profile`` never called the
#: engine — it passed ``species.family_key`` to ``get_or_create_profile``, which
#: forwarded it. A guard that cannot see the line it exists for is the failure class
#: this repository keeps paying for, so the predicate is the *argument travelling*,
#: at every door it can enter by. ``generate_profile`` is named although nothing
#: calls it today: a rename is how a guard quietly stops matching.
_GENERATORS = frozenset(
    {
        "auto_generate_profile",
        "generate_profile",
        "get_or_create_profile",
        "reset_profile",
    }
)

#: The keyword whose value must be a family NAME.
_FAMILY_ARGUMENT = "botanical_family"

#: Argument spellings that name a document key rather than a family name. A
#: suffix rather than a list, because the defect is the *kind* of value, and the
#: three spellings it already had in this tree (``family_key``,
#: ``species.family_key``, ``record["family_key"]``) share nothing but the suffix.
_KEYISH_SUFFIX = "_key"


def _keyish_source(node: ast.expr) -> str | None:
    """The ``*_key`` spelling this expression reduces to, or ``None``.

    ``family_key`` (Name), ``species.family_key`` (Attribute) and
    ``record["family_key"]`` (Subscript with a constant index) are the three shapes
    a stored key arrives in here. A call is deliberately **not** one of them:
    ``resolve_family_name(family_key)`` is the resolution this guard wants people to
    use, and reading its argument would report the fix as the defect.
    """
    if isinstance(node, ast.Name):
        name = node.id
    elif isinstance(node, ast.Attribute):
        name = node.attr
    elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        name = node.slice.value
    else:
        return None
    return name if name.endswith(_KEYISH_SUFFIX) else None


def scan_source(source: str, *, label: str = "<memory>") -> list[dict]:
    """Every ``<generator>(botanical_family=<something>_key)`` call in one module."""
    offences: list[dict] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
        if name not in _GENERATORS:
            continue
        for keyword in node.keywords:
            if keyword.arg != _FAMILY_ARGUMENT:
                continue
            spelling = _keyish_source(keyword.value)
            if spelling is not None:
                offences.append({"where": f"{label}:{node.lineno}", "argument": spelling})
    return offences


def _module_files() -> list[Path]:
    return sorted(_APP.rglob("*.py"))


def scan_tree() -> list[dict]:
    offences: list[dict] = []
    for path in _module_files():
        label = path.relative_to(_APP.parent).as_posix()
        offences.extend(scan_source(path.read_text(encoding="utf-8"), label=label))
    return offences


# ── The guard ────────────────────────────────────────────────────────────────


class TestNoStoredKeyIsPassedAsAFamily:
    def test_the_tree_passes_no_document_key_as_a_botanical_family(self) -> None:
        offences = scan_tree()

        assert not offences, (
            "these calls hand a stored document key to `botanical_family`, which "
            f"FAMILY_CARE_MAP keys by NAME — the #1489 defect: {offences}. Resolve it "
            "through `resolve_care_inputs` / `get_family_name_resolver` first."
        )

    def test_the_scan_still_finds_the_generator_calls(self) -> None:
        """A floor. A scan that stopped matching ``auto_generate_profile`` at all —
        a rename, a moved ``app/`` — would pass the assertion above over a tree full
        of offences."""
        calls = 0
        for path in _module_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                    if name in _GENERATORS:
                        calls += 1
        assert calls >= 6, f"expected the service, the router and the migrations to reach a generator, found {calls}"

    def test_the_scan_reads_more_than_a_handful_of_modules(self) -> None:
        assert len(_module_files()) > 100


# ── The scanner, driven from synthetic source ────────────────────────────────


_THE_DEFECT = """
def bootstrap(species, engine, plant):
    return engine.auto_generate_profile(
        species_name=species.scientific_name,
        botanical_family=species.family_key,
        plant_key=plant.key,
    )
"""

_THE_FIX = """
def bootstrap(species, engine, plant, resolve_family_name):
    return engine.auto_generate_profile(
        botanical_family=resolve_family_name(species.family_key),
        plant_key=plant.key,
    )
"""

_BARE_NAME = """
def backfill(engine, family_key):
    return engine.auto_generate_profile(botanical_family=family_key)
"""

_SUBSCRIPT = """
def backfill(engine, record):
    return engine.auto_generate_profile(botanical_family=record["family_key"])
"""

_A_NAME = """
def backfill(engine, families, family_key):
    return engine.auto_generate_profile(botanical_family=families[family_key])
"""

_ANOTHER_CALL = """
def unrelated(engine, species):
    return engine.calculate_due_date(botanical_family=species.family_key)
"""

#: The shape the real defect had: the key never reached the engine directly, it was
#: handed to the service method that forwards it.
_THE_DEFECT_ONE_LAYER_UP = """
def _bootstrap_care_profile(plant, species):
    get_care_reminder_service().get_or_create_profile(
        plant.key,
        botanical_family=species.family_key,
        may_create=True,
    )
"""


class TestTheScannerItself:
    """Both directions per shape. A matcher that fired on everything would satisfy
    the positive cases alone; one that fired on nothing would satisfy the guard."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (_THE_DEFECT, "family_key"),
            (_BARE_NAME, "family_key"),
            (_SUBSCRIPT, "family_key"),
        ],
        ids=["attribute", "bare-name", "subscript"],
    )
    def test_each_spelling_of_a_stored_key_is_caught(self, source: str, expected: str) -> None:
        offences = scan_source(source, label="svc.py")

        assert [o["argument"] for o in offences] == [expected]

    def test_the_defect_is_caught_where_it_actually_stood(self) -> None:
        """Against the real call site of #1489 — a service method, not the engine.

        The first version of this scanner passed this case, which is why the
        generator set names the forwarding methods too.
        """
        offences = scan_source(_THE_DEFECT_ONE_LAYER_UP, label="app/common/dependencies.py")

        assert [o["argument"] for o in offences] == ["family_key"]

    def test_the_resolved_call_is_not_an_offence(self) -> None:
        """The fix must not read as the defect — the argument is a *call* whose own
        argument is the key, and reporting that would make the guard unusable."""
        assert scan_source(_THE_FIX) == []

    def test_a_lookup_through_the_catalogue_is_not_an_offence(self) -> None:
        """``families[family_key]`` is the batched resolution v0049 uses: the
        subscript's *index* is the key, the value is the name."""
        assert scan_source(_A_NAME) == []

    def test_another_method_taking_the_same_argument_is_not_an_offence(self) -> None:
        assert scan_source(_ANOTHER_CALL) == []

    def test_a_call_without_the_argument_is_not_an_offence(self) -> None:
        assert scan_source("def f(engine):\n    return engine.auto_generate_profile(plant_key='p1')\n") == []


class TestTheGuardAgainstTheRealTree:
    def test_injecting_the_defect_into_the_real_scan_reddens_it(self, monkeypatch, tmp_path) -> None:
        """The mutation, against the real walk rather than a fragment: an ``rglob``
        that matched nothing, or a label that swallowed the offence, would leave
        every case above green."""
        app = tmp_path / "app"
        app.mkdir()
        (app / "dependencies.py").write_text(_THE_DEFECT, encoding="utf-8")
        monkeypatch.setattr(sys.modules[__name__], "_APP", app)

        assert [o["where"] for o in scan_tree()] == ["app/dependencies.py:3"]
