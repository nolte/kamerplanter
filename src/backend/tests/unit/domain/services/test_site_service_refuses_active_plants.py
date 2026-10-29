"""#2513 WP-3 — the site service lets the repository's ``site.has_active_plants`` refusal through unchanged.

The refusal is decided inside the repository's delete transaction (it must hold against the snapshot the delete
writes on). The service adds nothing on top: the very ``PlanError`` reaches the caller — same object, same code,
same ``details`` — and the service writes nothing after it.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import PlanError
from app.domain.models.site import Site
from app.domain.services.site_service import SiteService

TENANT = "t-own"


def _refusal() -> PlanError:
    return PlanError(
        "site.has_active_plants",
        "A site with active plants cannot be deleted.",
        status_code=409,
        active_plant_count=2,
    )


def test_the_repository_refusal_reaches_the_caller_unchanged_and_nothing_further_is_written() -> None:
    refusal = _refusal()
    repo = MagicMock()
    repo.get_site_or_raise.return_value = Site(_key="site-own", tenant_key=TENANT, name="Own", type="outdoor")
    repo.delete_site.side_effect = refusal

    with pytest.raises(PlanError) as raised:
        SiteService(repo).delete_site("site-own", tenant_key=TENANT, user_key="u-own")

    assert raised.value is refusal
    assert raised.value.status_code == 409
    assert raised.value.error_code == "site.has_active_plants"
    assert raised.value.details == [
        {
            "field": "request",
            "reason": "A site with active plants cannot be deleted.",
            "code": "site.has_active_plants",
            "active_plant_count": 2,
        }
    ]
    # One ownership read, one delete attempt — no other repository call before or after the refusal.
    assert [name for name, _args, _kwargs in repo.method_calls] == ["get_site_or_raise", "delete_site"]
    repo.delete_site.assert_called_once_with("site-own", user_key="u-own")
