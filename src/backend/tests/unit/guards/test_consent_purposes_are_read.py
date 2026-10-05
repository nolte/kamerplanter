"""Every consent purpose the system offers is named by code outside its declaration (#2136, MT-040).

A purpose in ``ConsentEngine.PURPOSES`` is shown to the person — in the privacy
settings, in the public privacy policy (Art. 13) — as a processing they can
agree to or refuse. A purpose no code reads is a promise without a mechanism:
granting it starts nothing, revoking it stops nothing (Art. 7 (3)). Measured at
#2136: three of eleven purposes were named nowhere under ``app/`` but in their
own declaration — ``error_tracking`` (Sentry ran regardless), ``hibp_check``
(no HaveIBeenPwned feature exists) and ``external_enrichment`` (the GBIF/Perenual
sync is a global catalogue job with no user in it).

**The rule.** Each key of an *optional* purpose (a consent, Art. 6 (1) a — the
required ``core_functionality`` is the contract basis and refuses nothing) is
referenced by at least one module under ``app/`` other
than ``consent_engine.py`` — as a string literal that is not a docstring, or
through the module-level constant ``consent_engine.py`` binds it to
(``DIARY_AI_ANALYSIS``, ``ERROR_TRACKING``) imported elsewhere.

**Limits, stated.** "Referenced" is weaker than "read by a consent check": a key
that only appears in a label table elsewhere passes. The guard closes the class
the audit found — a purpose nothing mentions at all — not every way a reference
can be idle; the per-purpose tests (``test_error_tracking_consent.py`` for
``error_tracking``) prove the reading.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"
DECLARATION = APP / "domain" / "engines" / "consent_engine.py"


def declared_purposes(source: str) -> dict[str, str | None]:
    """``{key: constant_name}`` of every optional ``ConsentPurpose(key=…)`` in *source*."""
    tree = ast.parse(source)
    constants = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    by_value = {value: name for name, value in constants.items()}
    purposes: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ConsentPurpose"):
            continue
        if any(
            kw.arg == "required" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords
        ):
            # A required purpose (Art. 6 (1) b) is no consent: nothing can be refused.
            continue
        for keyword in node.keywords:
            if keyword.arg != "key":
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                purposes[keyword.value.value] = by_value.get(keyword.value.value)
            elif isinstance(keyword.value, ast.Name) and keyword.value.id in constants:
                purposes[constants[keyword.value.id]] = keyword.value.id
    return purposes


def _docstring_nodes(tree: ast.AST) -> set[int]:
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                found.add(id(body[0].value))
    return found


def references_in(source: str) -> tuple[set[str], set[str]]:
    """``(string literals, names)`` a module uses — docstrings excluded."""
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    return literals, names


def unread_purposes(declaration: str, others: list[str]) -> list[str]:
    purposes = declared_purposes(declaration)
    literals: set[str] = set()
    names: set[str] = set()
    for source in others:
        found_literals, found_names = references_in(source)
        literals |= found_literals
        names |= found_names
    return sorted(
        key for key, constant in purposes.items() if key not in literals and (constant is None or constant not in names)
    )


def _other_modules() -> list[str]:
    return [path.read_text(encoding="utf-8") for path in sorted(APP.rglob("*.py")) if path != DECLARATION]


def test_every_offered_consent_purpose_is_named_outside_its_declaration() -> None:
    declaration = DECLARATION.read_text(encoding="utf-8")
    purposes = declared_purposes(declaration)

    # Non-vacuity: the detector reads the real registry, which is not empty.
    assert {"plant_identification", "error_tracking"} <= set(purposes)
    assert "core_functionality" not in purposes  # required, not a consent
    assert unread_purposes(declaration, _other_modules()) == []


@pytest.mark.parametrize(
    ("other", "expected"),
    [
        ("x = 1\n", ["a_literal", "b_constant"]),
        ('"""a_literal is mentioned in a docstring only."""\nX = "a_literal is not it"\n', ["a_literal", "b_constant"]),
        ('def f():\n    """a_literal"""\n    return "a_literal"\n', ["b_constant"]),
        ("from app.domain.engines.consent_engine import B_CONSTANT\n", ["a_literal"]),
        ('require("a_literal")\nuse(B_CONSTANT)\n', []),
    ],
)
def test_the_detector(other: str, expected: list[str]) -> None:
    declaration = (
        'B_CONSTANT = "b_constant"\n'
        "PURPOSES = [\n"
        '    ConsentPurpose(key="a_literal", label_de="", label_en=""),\n'
        "    ConsentPurpose(key=B_CONSTANT, label_de='', label_en=''),\n"
        '    ConsentPurpose(key="c_required", label_de="", label_en="", required=True),\n'
        "]\n"
    )

    assert unread_purposes(declaration, [other]) == expected
