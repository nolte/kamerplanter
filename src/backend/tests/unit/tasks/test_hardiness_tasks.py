"""REQ-039 — unit tests for the ``refresh_site_hardiness_zones`` Celery task.

Mocks the lazily imported ``app.common.dependencies`` and stubs the AQL cursor so
no real DB / service is touched. Covers the kill-switch, the resolve path, the
"no climate normals yet" skip and per-site error isolation across tenants.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_hardiness_zone_service = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_site_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_db = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.hardiness_tasks as module

    yield module, mock_deps


def _site_doc(**overrides):
    doc = {"_key": "site1", "name": "Beet", "type": "outdoor", "tenant_key": "t1", "gps_coordinates": [52.5, 13.4]}
    doc.update(overrides)
    return doc


def _wire(deps, docs):
    db = MagicMock()
    db.aql.execute.return_value = iter(docs)
    deps.get_db.return_value = db
    site_repo = MagicMock()
    site_repo._from_doc.side_effect = lambda doc: doc
    deps.get_site_repo.return_value = site_repo
    service = MagicMock()
    deps.get_hardiness_zone_service.return_value = service
    return service


class TestRefreshSiteHardinessZones:
    def test_noop_when_disabled(self, task_module, monkeypatch):
        module, _deps = task_module
        monkeypatch.setattr(module.settings, "hardiness_zone_refresh_enabled", False, raising=False)

        result = module.refresh_site_hardiness_zones()

        assert result == {"status": "skipped", "reason": "hardiness_zone_refresh_disabled"}

    def test_resolves_eligible_site(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "hardiness_zone_refresh_enabled", True, raising=False)
        service = _wire(deps, [_site_doc()])

        result = module.refresh_site_hardiness_zones()

        assert result == {"status": "ok", "resolved": 1, "skipped": 0, "errors": 0}
        service.resolve_for_site.assert_called_once_with("site1", "t1")

    def test_skips_site_without_normals(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "hardiness_zone_refresh_enabled", True, raising=False)
        service = _wire(deps, [_site_doc()])
        service.resolve_for_site.side_effect = ValidationError("no normals")

        result = module.refresh_site_hardiness_zones()

        assert result == {"status": "ok", "resolved": 0, "skipped": 1, "errors": 0}

    def test_filter_includes_unzoned_manual_sites(self, task_module, monkeypatch):
        # SEC-003: a freshly created site keeps the default source ``manual`` with
        # ``hardiness_zone == null``; the AQL filter must still pick it up (bind-var
        # clean, no inline ``'manual'`` literal / f-string).
        module, deps = task_module
        monkeypatch.setattr(module.settings, "hardiness_zone_refresh_enabled", True, raising=False)
        _wire(deps, [])

        module.refresh_site_hardiness_zones()

        query, kwargs = deps.get_db.return_value.aql.execute.call_args
        aql = query[0]
        assert "s.hardiness_zone_source != @manual OR s.hardiness_zone == null" in aql
        assert "'manual'" not in aql  # literal must be bound, not inlined
        assert kwargs["bind_vars"]["manual"] == "manual"

    def test_resolves_new_unzoned_manual_site(self, task_module, monkeypatch):
        # A new site returned by the (now inclusive) query gets its zone derived;
        # a *set* manual zone is excluded by the query and never re-derived.
        module, deps = task_module
        monkeypatch.setattr(module.settings, "hardiness_zone_refresh_enabled", True, raising=False)
        service = _wire(deps, [_site_doc(hardiness_zone_source="manual", hardiness_zone=None)])

        result = module.refresh_site_hardiness_zones()

        assert result == {"status": "ok", "resolved": 1, "skipped": 0, "errors": 0}
        service.resolve_for_site.assert_called_once_with("site1", "t1")

    def test_error_isolated_across_tenants(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "hardiness_zone_refresh_enabled", True, raising=False)
        service = _wire(deps, [_site_doc(_key="site1", tenant_key="t1"), _site_doc(_key="site2", tenant_key="t2")])

        def _resolve(site_key, tenant_key):
            if site_key == "site1":
                raise RuntimeError("boom")

        service.resolve_for_site.side_effect = _resolve

        result = module.refresh_site_hardiness_zones()

        assert result["status"] == "ok"
        assert result["resolved"] == 1
        assert result["errors"] == 1
        assert service.resolve_for_site.call_count == 2
