"""#2109 — every rate-limit setting is read by the application.

The defect class: a ``Settings`` field that names a rate limit, documented to
operators as a control, while no code reads it. ``rate_limit_general =
"100/minute"`` was one (#2109): the environment-variable reference listed
``RATE_LIMIT_GENERAL`` as "the rate limit for general API endpoints", and
nothing enforced it. A limit an operator can set and that does nothing is worse
than no setting — it reads as protection.

The class is **every field of ``Settings`` whose name contains ``rate_limit``**,
enumerated from the model, not listed by hand. Each must be read as an
attribute (``settings.<name>``, ``self._settings.<name>``, …) in at least one
module under ``app/`` other than ``app/config/settings.py`` — parsed, so a name
in a comment or docstring does not count.

**What it cannot see**: a read that does not reach a decision (a value logged
but never compared), and a read through ``getattr`` with a computed name.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
_SETTINGS_MODULE = APP / "config" / "settings.py"


def _rate_limit_fields() -> set[str]:
    from app.config.settings import Settings

    return {name for name in Settings.model_fields if "rate_limit" in name}


def _attributes_read(source: str) -> set[str]:
    return {node.attr for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Attribute)}


def _read_fields(fields: set[str], modules: list[Path]) -> set[str]:
    read: set[str] = set()
    for path in modules:
        read |= _attributes_read(path.read_text(encoding="utf-8")) & fields
    return read


def _app_modules() -> list[Path]:
    return sorted(p for p in APP.rglob("*.py") if "__pycache__" not in p.parts and p != _SETTINGS_MODULE)


def test_every_rate_limit_setting_is_read_somewhere() -> None:
    fields = _rate_limit_fields()
    assert len(fields) >= 10, sorted(fields)  # non-vacuity: the enumeration found the family

    unread = fields - _read_fields(fields, _app_modules())
    assert not unread, f"rate-limit settings no code reads (#2109): {sorted(unread)}"


def test_the_scan_ignores_prose_and_counts_attribute_reads() -> None:
    """Self-test through the same reader: a docstring mention is no read, an attribute is."""
    fields = {"rate_limit_example"}
    prose = '"""Mentions rate_limit_example only in prose."""\n# rate_limit_example\n'
    read = "LIMIT = settings.rate_limit_example\n"

    assert not (_attributes_read(prose) & fields)
    assert _attributes_read(read) & fields == fields
