"""``prepare-reuse`` is a batch write and takes the batch write gate — MT-045.1 (#2144).

``POST /substrates/batches/{key}/prepare-reuse`` resolved the caller's tenant and
the batch under it (#1195), but the router dropped the role: the service had no
``caller_role`` parameter, so a viewer ran the preparation every other batch
write refuses them. Load-then-gate order like ``update_batch``: a foreign batch
answers 404 before the role is asked, so the gate is no existence oracle.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.services.substrate_service import SubstrateService
from tests.unit.domain.services.test_substrate_batch_slot_assignment_scope import _Anchors, _SubstrateRepo


def _service() -> tuple[SubstrateService, MagicMock]:
    service = SubstrateService(_SubstrateRepo(), slot_anchors=_Anchors())  # type: ignore[arg-type]
    service.get_substrate = MagicMock()  # type: ignore[method-assign]
    lifecycle = MagicMock()
    lifecycle.check_reusability.return_value = (True, [], [], 4.0, None)
    service._lifecycle_mgr = lifecycle
    return service, lifecycle


def test_a_viewer_may_not_prepare_a_batch_for_reuse() -> None:
    service, lifecycle = _service()

    with pytest.raises(ForbiddenError):
        service.prepare_reuse("b_a", tenant_key="t_a", caller_role=TenantRole.VIEWER, is_platform_admin=False)

    lifecycle.check_reusability.assert_not_called()


def test_a_grower_prepares_their_own_batch() -> None:
    service, lifecycle = _service()

    result = service.prepare_reuse("b_a", tenant_key="t_a", caller_role=TenantRole.GROWER, is_platform_admin=False)

    assert result["can_reuse"] is True
    lifecycle.check_reusability.assert_called_once_with("b_a")


def test_a_foreign_batch_answers_404_before_the_role_is_asked() -> None:
    service, lifecycle = _service()

    with pytest.raises(NotFoundError):
        service.prepare_reuse("b_b", tenant_key="t_a", caller_role=TenantRole.VIEWER, is_platform_admin=False)

    lifecycle.check_reusability.assert_not_called()
