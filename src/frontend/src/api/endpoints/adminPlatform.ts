import apiClient from '@/api/client';
import type {
  AdminAddMemberRequest,
  AdminAddUserToTenantRequest,
  AdminPlatformStats,
  AdminTenant,
  AdminTenantMember,
  AdminTenantUpdate,
  AdminUser,
  AdminUserMembership,
  AdminUserUpdate,
  TenantRole,
} from '@/api/types';

export async function fetchAdminStats(): Promise<AdminPlatformStats> {
  const { data } = await apiClient.get<AdminPlatformStats>('/admin/platform/stats');
  return data;
}

export async function fetchAdminTenants(): Promise<AdminTenant[]> {
  const { data } = await apiClient.get<AdminTenant[]>('/admin/platform/tenants');
  return data;
}

export async function fetchAdminUsers(): Promise<AdminUser[]> {
  const { data } = await apiClient.get<AdminUser[]>('/admin/platform/users');
  return data;
}

export async function updateAdminTenant(
  key: string,
  payload: AdminTenantUpdate,
): Promise<AdminTenant> {
  const { data } = await apiClient.patch<AdminTenant>(
    `/admin/platform/tenants/${encodeURIComponent(key)}`,
    payload,
  );
  return data;
}

export async function updateAdminUser(
  key: string,
  payload: AdminUserUpdate,
): Promise<AdminUser> {
  const { data } = await apiClient.patch<AdminUser>(
    `/admin/platform/users/${encodeURIComponent(key)}`,
    payload,
  );
  return data;
}

export async function deleteAdminTenant(key: string): Promise<void> {
  await apiClient.delete(`/admin/platform/tenants/${encodeURIComponent(key)}`);
}

export async function deleteAdminUser(key: string): Promise<void> {
  await apiClient.delete(`/admin/platform/users/${encodeURIComponent(key)}`);
}

export async function fetchTenantMembers(tenantKey: string): Promise<AdminTenantMember[]> {
  const { data } = await apiClient.get<AdminTenantMember[]>(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members`,
  );
  return data;
}

export async function addTenantMember(
  tenantKey: string,
  payload: AdminAddMemberRequest,
): Promise<AdminTenantMember> {
  const { data } = await apiClient.post<AdminTenantMember>(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members`,
    payload,
  );
  return data;
}

export async function removeTenantMember(
  tenantKey: string,
  membershipKey: string,
): Promise<void> {
  await apiClient.delete(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members/${encodeURIComponent(membershipKey)}`,
  );
}

export async function changeTenantMemberRole(
  tenantKey: string,
  membershipKey: string,
  role: TenantRole,
): Promise<AdminTenantMember> {
  const { data } = await apiClient.patch<AdminTenantMember>(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members/${encodeURIComponent(membershipKey)}/role`,
    { role },
  );
  return data;
}

export async function fetchUserMemberships(userKey: string): Promise<AdminUserMembership[]> {
  const { data } = await apiClient.get<AdminUserMembership[]>(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships`,
  );
  return data;
}

export async function addUserToTenant(
  userKey: string,
  payload: AdminAddUserToTenantRequest,
): Promise<AdminUserMembership> {
  const { data } = await apiClient.post<AdminUserMembership>(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships`,
    payload,
  );
  return data;
}

export async function removeUserFromTenant(
  userKey: string,
  membershipKey: string,
): Promise<void> {
  await apiClient.delete(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships/${encodeURIComponent(membershipKey)}`,
  );
}

export async function changeUserMembershipRole(
  userKey: string,
  membershipKey: string,
  role: TenantRole,
): Promise<AdminUserMembership> {
  const { data } = await apiClient.patch<AdminUserMembership>(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships/${encodeURIComponent(membershipKey)}/role`,
    { role },
  );
  return data;
}
