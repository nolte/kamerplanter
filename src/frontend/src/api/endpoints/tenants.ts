import client from '../client';
import type {
  Invitation,
  InvitationCreate,
  InvitationLinkCreate,
  LocationAssignment,
  Membership,
  Tenant,
  TenantCreate,
  TenantUpdate,
  TenantWithRole,
} from '../types';

const BASE = '/tenants';

// ── Tenant CRUD ─────────────────────────────────────────────────────

export async function listMyTenants(): Promise<TenantWithRole[]> {
  const res = await client.get<TenantWithRole[]>(`${BASE}/`);
  return res.data;
}

export async function createOrganization(data: TenantCreate): Promise<Tenant> {
  const res = await client.post<Tenant>(`${BASE}/`, data);
  return res.data;
}

export async function getTenant(slug: string): Promise<Tenant> {
  const res = await client.get<Tenant>(`${BASE}/${slug}`);
  return res.data;
}

export async function updateTenant(slug: string, data: TenantUpdate): Promise<Tenant> {
  const res = await client.patch<Tenant>(`${BASE}/${slug}`, data);
  return res.data;
}

export async function deleteTenant(slug: string): Promise<void> {
  await client.delete(`${BASE}/${slug}`);
}

// ── Members ─────────────────────────────────────────────────────────

export async function listMembers(slug: string): Promise<Membership[]> {
  const res = await client.get<Membership[]>(`${BASE}/${slug}/members`);
  return res.data;
}

export async function changeMemberRole(
  slug: string,
  membershipKey: string,
  role: string,
): Promise<void> {
  await client.patch(`${BASE}/${slug}/members/${membershipKey}/role`, { role });
}

export async function removeMember(slug: string, membershipKey: string): Promise<void> {
  await client.delete(`${BASE}/${slug}/members/${membershipKey}`);
}

export async function leaveTenant(slug: string): Promise<void> {
  await client.post(`${BASE}/${slug}/leave`);
}

// ── Invitations ─────────────────────────────────────────────────────

export async function listInvitations(slug: string): Promise<Invitation[]> {
  const res = await client.get<Invitation[]>(`${BASE}/${slug}/invitations`);
  return res.data;
}

export async function createEmailInvitation(
  slug: string,
  data: InvitationCreate,
): Promise<{ invitation_key: string; token: string; expires_at: string }> {
  const res = await client.post(`${BASE}/${slug}/invitations/email`, data);
  return res.data;
}

export async function createLinkInvitation(
  slug: string,
  data: InvitationLinkCreate,
): Promise<{ invitation_key: string; token: string; expires_at: string }> {
  const res = await client.post(`${BASE}/${slug}/invitations/link`, data);
  return res.data;
}

export async function revokeInvitation(slug: string, invitationKey: string): Promise<void> {
  await client.delete(`${BASE}/${slug}/invitations/${invitationKey}`);
}

export async function acceptInvitation(token: string): Promise<void> {
  await client.post(`${BASE}/invitations/accept`, { token });
}

// ── Assignments ─────────────────────────────────────────────────────

export async function listAssignments(slug: string): Promise<LocationAssignment[]> {
  const res = await client.get<LocationAssignment[]>(`${BASE}/${slug}/assignments`);
  return res.data;
}

export async function createAssignment(
  slug: string,
  data: { membership_key: string; location_key: string; can_edit?: boolean; notes?: string },
): Promise<LocationAssignment> {
  const res = await client.post<LocationAssignment>(`${BASE}/${slug}/assignments`, data);
  return res.data;
}

export async function updateAssignment(
  slug: string,
  assignmentKey: string,
  data: { can_edit?: boolean; notes?: string },
): Promise<LocationAssignment> {
  const res = await client.patch<LocationAssignment>(
    `${BASE}/${slug}/assignments/${assignmentKey}`,
    data,
  );
  return res.data;
}

export async function deleteAssignment(slug: string, assignmentKey: string): Promise<void> {
  await client.delete(`${BASE}/${slug}/assignments/${assignmentKey}`);
}
