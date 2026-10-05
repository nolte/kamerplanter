import apiClient from '@/api/client';
import type {
  AccountDeletionAccepted,
  AccountErasureRequest,
  ErasureStatus,
  AdminAddMemberRequest,
  AdminAddUserToTenantRequest,
  AdminPlatformStats,
  AdminTenant,
  AdminTenantMember,
  AdminTenantUpdate,
  AdminUser,
  AdminUserMembership,
  AdminUserUpdate,
  CredentialStepUp,
  ErasurePreview,
  TenantDeleteRequest,
  TenantDeletionAccepted,
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

/**
 * Partially update a tenant. Changing `is_active` passes the **admin's own**
 * step-up (#2009): the payload then carries `current_password` (or
 * `step_up_token` / `step_up_code` for an admin without one) for the act
 * `admin_tenant_update`, bound to the tenant's key; 401 without it.
 */
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

/**
 * Partially update another account. Turning `email_verified` or `is_active`
 * from false to true passes the **admin's own** step-up (#1857): the payload
 * then carries `current_password` (or `step_up_token` / `step_up_code` for an
 * admin without one) for the act `admin_account_update`; 401 without it.
 */
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

/** Accepts the deletion (202, #1792): the tenant is frozen and erased afterwards — not yet gone. */
export async function deleteAdminTenant(
  key: string,
  stepUp: TenantDeleteRequest,
): Promise<TenantDeletionAccepted> {
  const { data } = await apiClient.delete<TenantDeletionAccepted>(
    `/admin/platform/tenants/${encodeURIComponent(key)}`,
    { data: stepUp },
  );
  return data;
}

/**
 * Cancel a scheduled tenant deletion inside its grace (#2123): the tenant is `active` again with
 * every membership as it was. Carries the **admin's own** step-up (`tenant_erasure_cancel`).
 */
export async function cancelAdminTenantErasure(key: string, stepUp: CredentialStepUp): Promise<AdminTenant> {
  const { data } = await apiClient.post<AdminTenant>(
    `/admin/platform/tenants/${encodeURIComponent(key)}/erasure/cancel`,
    stepUp,
  );
  return data;
}

/**
 * Accept the erasure of another account (#1814, 202 since #1949): the account is closed and the
 * other members told at once, the data is erased afterwards by a worker — not yet gone. The body
 * echoes the **target's** e-mail and carries the **admin's own** current password when the admin's
 * account has one.
 */
export async function deleteAdminUser(key: string, stepUp: AccountErasureRequest): Promise<AccountDeletionAccepted> {
  const { data } = await apiClient.delete<AccountDeletionAccepted>(
    `/admin/platform/users/${encodeURIComponent(key)}`,
    { data: stepUp },
  );
  return data;
}

/**
 * GET /admin/platform/erasures/{erasure_key} — the status of an account erasure the admin deletion
 * accepted (#1949): `completed`, `in_progress`, or `partially_completed` for a run the daily beat retries.
 */
export async function getAdminErasureStatus(erasureKey: string): Promise<ErasureStatus> {
  const { data } = await apiClient.get<ErasureStatus>(`/admin/platform/erasures/${encodeURIComponent(erasureKey)}`);
  return data;
}

/**
 * GET /admin/platform/users/{key}/erasure-preview — which personal tenants deleting
 * *that* account takes with it, and how many other members each has (REQ-025
 * AK-FK-06, #1961). The shape of the self-service preview; a count, never who.
 */
export async function getAdminUserErasurePreview(key: string): Promise<ErasurePreview> {
  const { data } = await apiClient.get<ErasurePreview>(
    `/admin/platform/users/${encodeURIComponent(key)}/erasure-preview`,
  );
  return data;
}

export async function fetchTenantMembers(tenantKey: string): Promise<AdminTenantMember[]> {
  const { data } = await apiClient.get<AdminTenantMember[]>(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members`,
  );
  return data;
}

/**
 * Add an account to a tenant (#2106): the body carries the **admin's own** step-up —
 * `current_password`, or `step_up_token` / `step_up_code` for the act `admin_membership_add`
 * bound to `<tenant_key>|<user_key>`; 401 without it.
 */
export async function addTenantMember(
  tenantKey: string,
  payload: AdminAddMemberRequest,
  stepUp: CredentialStepUp,
): Promise<AdminTenantMember> {
  const { data } = await apiClient.post<AdminTenantMember>(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members`,
    { ...payload, ...stepUp },
  );
  return data;
}

/**
 * Remove a member (#2009): the body carries the **admin's own** step-up —
 * `current_password`, or `step_up_token` / `step_up_code` for the act
 * `admin_membership_removal` bound to the membership's key; 401 without it.
 */
export async function removeTenantMember(
  tenantKey: string,
  membershipKey: string,
  stepUp: CredentialStepUp,
): Promise<void> {
  await apiClient.delete(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members/${encodeURIComponent(membershipKey)}`,
    { data: stepUp },
  );
}

/**
 * Change a member's role (#2032): an actual change carries the **admin's own**
 * step-up — `current_password`, or `step_up_token` / `step_up_code` for the act
 * `admin_membership_role_change` bound to the membership's key; 401 without it.
 */
export async function changeTenantMemberRole(
  tenantKey: string,
  membershipKey: string,
  role: TenantRole,
  stepUp: CredentialStepUp,
): Promise<AdminTenantMember> {
  const { data } = await apiClient.patch<AdminTenantMember>(
    `/admin/platform/tenants/${encodeURIComponent(tenantKey)}/members/${encodeURIComponent(membershipKey)}/role`,
    { role, ...stepUp },
  );
  return data;
}

export async function fetchUserMemberships(userKey: string): Promise<AdminUserMembership[]> {
  const { data } = await apiClient.get<AdminUserMembership[]>(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships`,
  );
  return data;
}

/** Add a user to a tenant (#2106): the same step-up body as {@link addTenantMember}. */
export async function addUserToTenant(
  userKey: string,
  payload: AdminAddUserToTenantRequest,
  stepUp: CredentialStepUp,
): Promise<AdminUserMembership> {
  const { data } = await apiClient.post<AdminUserMembership>(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships`,
    { ...payload, ...stepUp },
  );
  return data;
}

/** Remove a user from a tenant (#2009): the same step-up body as {@link removeTenantMember}. */
export async function removeUserFromTenant(
  userKey: string,
  membershipKey: string,
  stepUp: CredentialStepUp,
): Promise<void> {
  await apiClient.delete(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships/${encodeURIComponent(membershipKey)}`,
    { data: stepUp },
  );
}

/** Change a user's role in a tenant (#2032): the same step-up body as {@link changeTenantMemberRole}. */
export async function changeUserMembershipRole(
  userKey: string,
  membershipKey: string,
  role: TenantRole,
  stepUp: CredentialStepUp,
): Promise<AdminUserMembership> {
  const { data } = await apiClient.patch<AdminUserMembership>(
    `/admin/platform/users/${encodeURIComponent(userKey)}/memberships/${encodeURIComponent(membershipKey)}/role`,
    { role, ...stepUp },
  );
  return data;
}
