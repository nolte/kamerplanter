"""REQ-024 v1.4 RBAC permission matrix tests."""

import pytest

from app.common.enums import TenantRole
from app.core.permissions import (
    Action,
    ResourceType,
    assert_permission,
    has_permission,
    list_permissions,
)


class TestPlantDomainCRUD:
    def test_admin_has_full_crud_on_plants(self):
        for action in (Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE):
            assert has_permission(TenantRole.LEAD, ResourceType.PLANT, action)

    def test_grower_may_read_create_update_but_not_delete_plants(self):
        # REQ-024 §1a.1 ("❌D" throughout) / REQ-049 §2.3: delete is the
        # irreversibility boundary and is lead-only. The matrix used to grant it
        # to growers too — that drift is now corrected so the descriptive matrix
        # and MembershipEngine.can_delete_resource agree.
        for action in (Action.READ, Action.CREATE, Action.UPDATE):
            assert has_permission(TenantRole.GROWER, ResourceType.PLANT, action)
        assert not has_permission(TenantRole.GROWER, ResourceType.PLANT, Action.DELETE)

    def test_viewer_only_reads_plants(self):
        assert has_permission(TenantRole.VIEWER, ResourceType.PLANT, Action.READ)
        for action in (Action.CREATE, Action.UPDATE, Action.DELETE):
            assert not has_permission(TenantRole.VIEWER, ResourceType.PLANT, action)


class TestTenantManagement:
    def test_only_admin_can_invite(self):
        assert has_permission(TenantRole.LEAD, ResourceType.MEMBERSHIP, Action.INVITE)
        assert not has_permission(TenantRole.GROWER, ResourceType.MEMBERSHIP, Action.INVITE)
        assert not has_permission(TenantRole.VIEWER, ResourceType.MEMBERSHIP, Action.INVITE)

    def test_all_roles_can_read_tenant_metadata(self):
        for role in (TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER):
            assert has_permission(role, ResourceType.TENANT, Action.READ)

    def test_only_admin_can_delete_tenant(self):
        assert has_permission(TenantRole.LEAD, ResourceType.TENANT, Action.DELETE)
        assert not has_permission(TenantRole.GROWER, ResourceType.TENANT, Action.DELETE)
        assert not has_permission(TenantRole.VIEWER, ResourceType.TENANT, Action.DELETE)


class TestVerbsBeyondCRUD:
    def test_grower_can_confirm_harvest(self):
        assert has_permission(TenantRole.LEAD, ResourceType.HARVEST, Action.CONFIRM)
        assert has_permission(TenantRole.GROWER, ResourceType.HARVEST, Action.CONFIRM)
        # Viewer cannot confirm a harvest.
        assert not has_permission(TenantRole.VIEWER, ResourceType.HARVEST, Action.CONFIRM)

    def test_viewer_can_confirm_their_own_care_tasks(self):
        # Care reminders + tasks are confirmable by viewers since
        # confirming them is the read-side acknowledgement.
        assert has_permission(TenantRole.VIEWER, ResourceType.TASK, Action.CONFIRM)
        assert has_permission(TenantRole.VIEWER, ResourceType.CARE_PROFILE, Action.CONFIRM)

    def test_calendar_feed_export_is_open_to_everyone_with_membership(self):
        for role in (TenantRole.LEAD, TenantRole.GROWER, TenantRole.VIEWER):
            assert has_permission(role, ResourceType.CALENDAR_FEED, Action.EXPORT)


class TestAssertPermission:
    def test_passes_silently_when_permitted(self):
        assert_permission(TenantRole.LEAD, ResourceType.PLANT, Action.CREATE)

    def test_raises_with_explanatory_message_when_denied(self):
        with pytest.raises(PermissionError, match="viewer"):
            assert_permission(TenantRole.VIEWER, ResourceType.PLANT, Action.DELETE)


class TestListPermissions:
    def test_admin_list_includes_membership_invite(self):
        perms = list_permissions(TenantRole.LEAD)
        assert (ResourceType.MEMBERSHIP, Action.INVITE) in perms

    def test_viewer_list_excludes_create_actions(self):
        perms = list_permissions(TenantRole.VIEWER)
        actions = {a for _, a in perms}
        assert Action.CREATE not in actions
        assert Action.DELETE not in actions
        assert Action.READ in actions
