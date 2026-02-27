import { useMemo } from 'react';
import { useAppSelector } from '@/store/hooks';
import type { TenantRole } from '@/api/types';

interface TenantPermissions {
  role: TenantRole | null;
  isAdmin: boolean;
  canEdit: boolean;
  canManageMembers: boolean;
  canInvite: boolean;
  hasTenant: boolean;
}

export function useTenantPermissions(): TenantPermissions {
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);

  return useMemo(() => {
    if (!activeTenant) {
      return {
        role: null,
        isAdmin: false,
        canEdit: false,
        canManageMembers: false,
        canInvite: false,
        hasTenant: false,
      };
    }

    const role = activeTenant.role;
    const isAdmin = role === 'admin';
    const canEdit = role === 'admin' || role === 'grower';

    return {
      role,
      isAdmin,
      canEdit,
      canManageMembers: isAdmin,
      canInvite: isAdmin,
      hasTenant: true,
    };
  }, [activeTenant]);
}
