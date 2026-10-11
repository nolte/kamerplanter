"""REQ-056 AK-19 (#2142) — no module but the entitlement service reads a quota setting.

Before #2142 every quota check read its own setting (``settings.storage_tenant_quota_mb``
in ``AttachmentService``, ``settings.tenant_max_members_ceiling`` handed to
``TenantService`` ...). A plan can only decide a tenant's quota if nothing reads the
setting past it: one direct read, and the plan of that dimension is inert for that path.

The predicate: under ``app/``, outside ``domain/services/entitlement_service.py`` and
``config/settings.py``, no attribute access ``<x>.<name>`` and no string literal equal to
``<name>`` (a ``getattr(settings, "...")`` spelling) for any setting in
:data:`~app.domain.services.entitlement_service.INSTANCE_SETTINGS`. The list is read
from the service, so a dimension added there is guarded the moment it exists.

Traces to REQ-056 AK-19 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import ast
from pathlib import Path

import app
from app.domain.services.entitlement_service import INSTANCE_SETTINGS

_APP = Path(app.__file__).resolve().parent

#: The two modules allowed to name a quota setting: its definition and its one reader.
ALLOWED = {
    Path("config/settings.py"): "defines the settings",
    Path("domain/services/entitlement_service.py"): "the one reader (REQ-056 §7.4)",
}

_NAMES = frozenset(INSTANCE_SETTINGS.values())


def quota_setting_reads(source: str) -> list[tuple[int, str]]:
    """``(line, name)`` of every attribute access or string literal naming a quota setting."""
    hits: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr in _NAMES:
            hits.append((node.lineno, node.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in _NAMES:
            hits.append((node.lineno, node.value))
    return hits


def test_no_module_but_the_entitlement_service_reads_a_quota_setting() -> None:
    offenders: list[str] = []
    for path in sorted(_APP.rglob("*.py")):
        relative = path.relative_to(_APP)
        if relative in ALLOWED:
            continue
        offenders.extend(f"app/{relative}:{line} reads {name}" for line, name in quota_setting_reads(path.read_text()))

    assert offenders == [], "read the limit through EntitlementService.limit/require instead:\n" + "\n".join(offenders)


def test_the_allowed_modules_exist() -> None:
    """An allowlisted path that moved would silently widen nothing - but it would stop being true."""
    assert all((_APP / relative).is_file() for relative in ALLOWED)


def test_the_predicate_finds_each_spelling_of_a_read() -> None:
    """Self-test: the predicate fails on an injected direct read (REQ-056 AK-19)."""
    assert quota_setting_reads("limit = settings.storage_tenant_quota_mb\n") == [(1, "storage_tenant_quota_mb")]
    assert quota_setting_reads("limit = self._settings.storage_max_photos_per_instance\n") == [
        (1, "storage_max_photos_per_instance")
    ]
    assert quota_setting_reads('limit = getattr(settings, "ai_budget_user_calls_per_day")\n') == [
        (1, "ai_budget_user_calls_per_day")
    ]
    assert quota_setting_reads("f(max_members_ceiling=settings.tenant_max_members_ceiling)\n") == [
        (1, "tenant_max_members_ceiling")
    ]


def test_the_predicate_ignores_prose_and_neighbours() -> None:
    """A docstring that mentions a setting, and a setting with a similar name, are not reads."""
    assert quota_setting_reads('"""Reads ``storage_tenant_quota_mb`` through the plan."""\n') == []
    assert quota_setting_reads("x = settings.storage_max_file_size_mb\n") == []
    assert quota_setting_reads('logger.info("ai_budget_exceeded")\n') == []
