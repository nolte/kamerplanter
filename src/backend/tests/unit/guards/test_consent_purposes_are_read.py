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

**Purposes the browser reads (#3025 N-40, REQ-025 v1.41).** A purpose whose
processing runs in the browser (``browser_error_reports``: the Sentry SDK of the
frontend) has no backend reader; the backend only stores the decision. Such a
purpose is declared in ``BROWSER_READ_PURPOSES`` and is held to the browser
instead: its key must be named in executable frontend source under
``src/frontend/src`` (tests excluded, comments stripped), and its text version
must equal ``BROWSER_ERROR_REPORTS_VERSION`` in ``observability/consent.ts`` — a
raised text version that the browser does not know would let it accept grants
to the old wording.

**Limits, stated.** "Referenced" is weaker than "read by a consent check": a key
that only appears in a label table elsewhere passes. The guard closes the class
the audit found — a purpose nothing mentions at all — not every way a reference
can be idle; the per-purpose tests (``test_error_tracking_consent.py`` for
``error_tracking``) prove the reading.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

_source_text = load_repo_script("source_text")

APP = Path(__file__).resolve().parents[3] / "app"
DECLARATION = APP / "domain" / "engines" / "consent_engine.py"
_REPO_ROOT = find_repo_root(Path(__file__).resolve())
FRONTEND_SRC = _REPO_ROOT / "src" / "frontend" / "src" if _REPO_ROOT else None
FRONTEND_CONSENT = FRONTEND_SRC / "observability" / "consent.ts" if FRONTEND_SRC else None


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


def _module_constants(tree: ast.Module) -> dict[str, str]:
    return {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def browser_read_purposes(source: str) -> set[str]:
    """Keys in ``BROWSER_READ_PURPOSES = frozenset({...})`` of *source*, names resolved to their values."""
    tree = ast.parse(source)
    constants = _module_constants(tree)
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            target: ast.expr | None = node.target
        elif isinstance(node, ast.Assign):
            target = node.targets[0]
        else:
            continue
        if not (isinstance(target, ast.Name) and target.id == "BROWSER_READ_PURPOSES" and node.value is not None):
            continue
        for element in ast.walk(node.value):
            if isinstance(element, ast.Name) and element.id in constants:
                found.add(constants[element.id])
            elif isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.add(element.value)
    return found


def purpose_versions(source: str) -> dict[str, str]:
    """``{key: version}`` of every ``ConsentPurpose(...)`` in *source*; ``"1.0"`` (the model default) when unset."""
    tree = ast.parse(source)
    constants = _module_constants(tree)
    versions: dict[str, str] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ConsentPurpose"):
            continue
        kwargs = {kw.arg: kw.value for kw in node.keywords}
        key_node = kwargs.get("key")
        if isinstance(key_node, ast.Name):
            key = constants.get(key_node.id)
        elif isinstance(key_node, ast.Constant):
            key = key_node.value
        else:
            key = None
        version_node = kwargs.get("version")
        version = version_node.value if isinstance(version_node, ast.Constant) else "1.0"
        if isinstance(key, str) and isinstance(version, str):
            versions[key] = version
    return versions


_TS_VERSION = re.compile(r"export\s+const\s+BROWSER_ERROR_REPORTS_VERSION\s*=\s*['\"]([^'\"]+)['\"]")


def frontend_version(consent_ts: str) -> str | None:
    """The value of ``BROWSER_ERROR_REPORTS_VERSION`` in executable TypeScript (comments stripped)."""
    match = _TS_VERSION.search(_source_text.executable_source(consent_ts, language="typescript"))
    return match.group(1) if match else None


def named_in_frontend(key: str, sources: list[str]) -> bool:
    """Whether *key* appears as a quoted string in the executable part of any of *sources*."""
    literal = re.compile(rf"""['"`]{re.escape(key)}['"`]""")
    return any(literal.search(_source_text.executable_source(text, language="typescript")) for text in sources)


def _frontend_sources() -> list[str]:
    assert FRONTEND_SRC is not None
    return [
        path.read_text(encoding="utf-8")
        for path in sorted(FRONTEND_SRC.rglob("*"))
        if path.suffix in {".ts", ".tsx"} and "test" not in path.relative_to(FRONTEND_SRC).parts[:1]
    ]


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
    assert {"plant_identification", "error_tracking", "browser_error_reports"} <= set(purposes)
    assert "core_functionality" not in purposes  # required, not a consent
    browser = browser_read_purposes(declaration)
    assert browser == {"browser_error_reports"}
    # A purpose read by the browser is exempt here only; the test below holds it to the frontend.
    assert [key for key in unread_purposes(declaration, _other_modules()) if key not in browser] == []


@pytest.mark.skipif(FRONTEND_SRC is None or not FRONTEND_SRC.is_dir(), reason="frontend sources not in this checkout")
def test_every_browser_read_purpose_is_named_by_the_frontend_with_the_same_text_version() -> None:
    declaration = DECLARATION.read_text(encoding="utf-8")
    browser = browser_read_purposes(declaration)
    versions = purpose_versions(declaration)
    sources = _frontend_sources()

    assert browser, "non-vacuity: at least one browser-read purpose is declared"
    assert [key for key in sorted(browser) if not named_in_frontend(key, sources)] == []
    assert FRONTEND_CONSENT is not None
    assert frontend_version(FRONTEND_CONSENT.read_text(encoding="utf-8")) == versions["browser_error_reports"]


def test_the_browser_detectors() -> None:
    declaration = (
        'A = "a_browser"\n'
        "BROWSER_READ_PURPOSES: frozenset[str] = frozenset({A})\n"
        "P = [ConsentPurpose(key=A, label_de='', version=\"2.1\"), ConsentPurpose(key='b', label_de='')]\n"
    )
    assert browser_read_purposes(declaration) == {"a_browser"}
    assert purpose_versions(declaration) == {"a_browser": "2.1", "b": "1.0"}
    # Comments name nothing: a key or a version only in prose does not count.
    assert named_in_frontend("a_browser", ["// 'a_browser' is read here\nconst x = 1;"]) is False
    assert named_in_frontend("a_browser", ["const KEY = 'a_browser';"]) is True
    assert frontend_version("// export const BROWSER_ERROR_REPORTS_VERSION = '9.9';\n") is None
    assert frontend_version("export const BROWSER_ERROR_REPORTS_VERSION = '2.1';\n") == "2.1"


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
