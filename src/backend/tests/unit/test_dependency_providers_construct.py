"""Every zero-argument provider in ``app.common.dependencies`` constructs (#1645).

Unit and integration tests build services with fakes directly; nothing there
goes through ``dependencies.py``. So a provider that passes a keyword its
constructor does not accept is invisible until the first request in a real
process — PR #1662 shipped ``personal_data_repo=`` into ``get_tenant_service``
and every catalog read in the compose smoke answered 500 with
``TypeError: TenantService.__init__() got an unexpected keyword argument``.

The test walks the whole provider set with the datastore constructors stubbed,
so the assertion is on the wiring, not on any one provider. The floor on the
provider count keeps the walk honest: a refactor that made the enumeration miss
most of the module would otherwise still report green.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest

from app.common import dependencies as deps

#: Counted on 2026-09-23. A drop below this means the enumeration lost
#: providers, not that the module shrank — raise it when providers are added.
PROVIDER_FLOOR = 180


def _zero_argument_providers() -> list[str]:
    names: list[str] = []
    for name, func in inspect.getmembers(deps, inspect.isfunction):
        if not name.startswith("get_") or func.__module__ != deps.__name__:
            continue
        if name in {"get_db", "get_connection", "get_timescale_connection"}:
            continue  # the stubbed datastore roots themselves
        required = [
            param
            for param in inspect.signature(func).parameters.values()
            if param.default is inspect.Parameter.empty
            and param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
        ]
        if not required:
            names.append(name)
    return names


@pytest.fixture
def stubbed_datastores(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps, "get_db", lambda: MagicMock(name="arango_db"))
    monkeypatch.setattr(deps, "get_connection", lambda: MagicMock(name="arango_connection"))
    monkeypatch.setattr(deps, "get_timescale_connection", lambda: MagicMock(name="timescale"))


def test_the_enumeration_covers_the_module() -> None:
    providers = _zero_argument_providers()
    assert len(providers) >= PROVIDER_FLOOR, (
        f"only {len(providers)} providers enumerated; the module has more — the walk lost part of the set"
    )


def test_every_provider_constructs_its_object(stubbed_datastores: None) -> None:
    failures: dict[str, str] = {}
    for name in _zero_argument_providers():
        try:
            getattr(deps, name)()
        except Exception as exc:  # noqa: BLE001 — every failure is reported, none swallowed
            failures[name] = f"{type(exc).__name__}: {exc}"
    assert not failures, "providers whose constructor call fails:\n" + "\n".join(
        f"  {name}: {message}" for name, message in sorted(failures.items())
    )
