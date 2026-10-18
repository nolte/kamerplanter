"""REQ-053 WP 3.3 (#2393) — the ``adjacency_recompute`` task resolves site and tenant itself (GP-FR-130, GP-NFR-016)."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.domain.interfaces.graph_repository import AdjacencySync
from app.domain.services.adjacency_service import AdjacencyResult
from app.tasks import adjacency as module
from app.tasks import celery_app


def _patched(*, location, site, active=True, recompute=None):
    sites = MagicMock()
    sites.get_location_by_key.return_value = location
    sites.get_site_by_key.return_value = site
    tenants = MagicMock()
    tenants.get_by_key.return_value = SimpleNamespace(is_active=active)
    service = MagicMock()
    service.recompute = recompute or MagicMock(
        return_value=AdjacencyResult("bed", 2, AdjacencySync(created=4, removed=1))
    )
    patches = [
        patch("app.common.dependencies.get_site_repo", return_value=sites),
        patch("app.common.dependencies.get_tenant_repo", return_value=tenants),
        patch("app.common.dependencies.get_adjacency_service", return_value=service),
    ]
    return patches, service


def _run(location_key, **kwargs):
    patches, service = _patched(**kwargs)
    for p in patches:
        p.start()
    try:
        return module.adjacency_recompute.run(location_key), service
    finally:
        for p in patches:
            p.stop()


LOCATION = SimpleNamespace(site_key="site_1")
SITE = SimpleNamespace(tenant_key="ten_1")


def test_the_task_is_registered_under_its_published_name():
    assert module.TASK_NAME in celery_app.tasks
    assert module.adjacency_recompute.name == module.TASK_NAME


def test_it_resolves_the_tenant_from_the_stored_site_and_recomputes():
    result, service = _run("bed", location=LOCATION, site=SITE)
    service.recompute.assert_called_once_with("bed", tenant_key="ten_1")
    assert result == {"status": "ok", "location_key": "bed", "pairs": 2, "created": 4, "updated": 0, "removed": 1}


def test_the_message_names_only_the_bed():
    """GP-FR-130: the job receives ``location_key`` and nothing a caller could use to name another tenant."""
    assert list(inspect.signature(module.adjacency_recompute.run).parameters) == ["location_key"]


@pytest.mark.parametrize(
    ("location", "site"),
    [(None, SITE), (LOCATION, None), (LOCATION, SimpleNamespace(tenant_key=""))],
    ids=["bed-gone", "site-gone", "site-without-tenant"],
)
def test_a_bed_that_is_gone_is_skipped_without_a_retry(location, site):
    result, service = _run("bed", location=location, site=site)
    assert result["status"] == "skipped"
    service.recompute.assert_not_called()


def test_an_empty_key_is_skipped():
    result, service = _run("", location=LOCATION, site=SITE)
    assert result["status"] == "skipped"
    service.recompute.assert_not_called()


def test_a_tenant_that_is_not_active_is_left_alone():
    result, service = _run("bed", location=LOCATION, site=SITE, active=False)
    assert result == {"status": "skipped", "reason": "tenant_not_active", "location_key": "bed"}
    service.recompute.assert_not_called()


def test_a_failure_is_retried_not_swallowed():
    boom = MagicMock(side_effect=ConnectionError("db down"))
    patches, _service = _patched(location=LOCATION, site=SITE, recompute=boom)
    for p in patches:
        p.start()
    try:
        with (
            patch.object(module.adjacency_recompute, "retry", side_effect=RuntimeError("retried")) as retry,
            pytest.raises(RuntimeError, match="retried"),
        ):
            module.adjacency_recompute.run("bed")
        retry.assert_called_once()
    finally:
        for p in patches:
            p.stop()
