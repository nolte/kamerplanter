import axios from 'axios';
import client from '../client';
import { ApiError } from '../errors';
import { fetchAllPages } from '../paginate';
import type {
  ApiErrorResponse,
  CredentialStepUp,
  Invitation,
  InvitationCreate,
  InvitationCreated,
  InvitationLinkCreate,
  LocationAssignment,
  Membership,
  Tenant,
  TenantCreate,
  TenantDeleteRequest,
  TenantDeletionAccepted,
  TenantEntitlements,
  TenantExport,
  TenantUpdate,
  TenantWithRole,
} from '../types';

const BASE = '/tenants';

// ── Tenant CRUD ─────────────────────────────────────────────────────

export async function listMyTenants(): Promise<TenantWithRole[]> {
  const res = await client.get<TenantWithRole[]>(BASE);
  return res.data;
}

/**
 * Every tenant of the account **including** those whose deletion is scheduled (#2166):
 * `pending_deletion` and `orphaned` tenants come with `status` and `deletion_scheduled_at`.
 * They resolve for nobody, so this list is for showing them (and offering the cancellation
 * to their management) — never for the tenant switcher; that one uses {@link listMyTenants}.
 */
export async function listMyTenantsWithScheduledDeletion(): Promise<TenantWithRole[]> {
  const res = await client.get<TenantWithRole[]>(BASE, {
    params: { include_scheduled_deletion: true },
  });
  return res.data;
}

/**
 * Cancel the scheduled deletion of a tenant inside its grace (#2123, #2166). Only a lead with
 * the `management` scope may; the body carries the requester's **own** step-up for the act
 * `tenant_erasure_cancel`, bound to the tenant's key. Answers the reopened tenant.
 */
export async function cancelTenantErasure(slug: string, stepUp: CredentialStepUp): Promise<Tenant> {
  const res = await client.post<Tenant>(`${BASE}/${slug}/erasure/cancel`, stepUp);
  return res.data;
}

export async function createOrganization(data: TenantCreate): Promise<Tenant> {
  const res = await client.post<Tenant>(BASE, data);
  return res.data;
}

export async function getTenant(slug: string): Promise<Tenant> {
  const res = await client.get<Tenant>(`${BASE}/${slug}`);
  return res.data;
}

/**
 * The garden's plan and, per quota dimension, the effective limit and the usage (REQ-056 §7.7, #2142).
 * Open to every member; `service_accounts` and `ai_tokens_per_tenant_day` come for a `lead` only, and
 * `ai_calls_per_user_day.used` is always the caller's own count.
 */
export async function getTenantEntitlements(slug: string): Promise<TenantEntitlements> {
  const res = await client.get<TenantEntitlements>(`${BASE}/${slug}/entitlements`);
  return res.data;
}

export async function updateTenant(slug: string, data: TenantUpdate): Promise<Tenant> {
  const res = await client.patch<Tenant>(`${BASE}/${slug}`, data);
  return res.data;
}

/** Accepts the deletion (202, #1792): the tenant is frozen and erased afterwards — not yet gone. */
export async function deleteTenant(
  slug: string,
  stepUp: TenantDeleteRequest,
): Promise<TenantDeletionAccepted> {
  const res = await client.delete<TenantDeletionAccepted>(`${BASE}/${slug}`, { data: stepUp });
  return res.data;
}

// ── Exports (REQ-056 §8, #2138) — full mode only ────────────────────

/** How many of the caller's own exports the settings card shows (newest first). */
export const TENANT_EXPORT_LIST_LIMIT = 10;

/**
 * Request an export of the whole tenant (REQ-056 §8.2) — `202 Accepted` with the pending record.
 * Lead **and** `management` scope; the body carries the requester's **own** step-up for the act
 * `tenant_export`, bound to the tenant's key. `409 EXPORT_ALREADY_RUNNING` while one runs,
 * `429 RATE_LIMIT_EXCEEDED` past the daily limit.
 */
export async function requestTenantExport(
  slug: string,
  stepUp: CredentialStepUp,
): Promise<TenantExport> {
  const res = await client.post<TenantExport>(`${BASE}/${slug}/exports`, stepUp);
  return res.data;
}

/** The caller's own exports of the tenant, newest first — the first {@link TENANT_EXPORT_LIST_LIMIT}. */
export async function listTenantExports(slug: string): Promise<TenantExport[]> {
  const res = await client.get<TenantExport[]>(`${BASE}/${slug}/exports`, {
    params: { offset: 0, limit: TENANT_EXPORT_LIST_LIMIT },
  });
  return res.data;
}

/**
 * Read a blob-typed error body back as the API's error envelope.
 *
 * With `responseType: 'blob'` the error body arrives as a `Blob`, so the client's interceptor
 * cannot recognise the envelope and rethrows the raw Axios error; without this the card would
 * show "Request failed with status code 404" for an expired archive.
 */
async function rethrowBlobError(error: unknown): Promise<never> {
  if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
    let parsed: Partial<ApiErrorResponse> | null;
    try {
      parsed = JSON.parse(await error.response.data.text()) as Partial<ApiErrorResponse>;
    } catch {
      parsed = null;
    }
    if (parsed?.error_id && parsed.error_code) {
      throw new ApiError(parsed as ApiErrorResponse, error.response.status);
    }
  }
  throw error;
}

/**
 * The archive of a completed export as a ZIP blob — only for the person who requested it and
 * only until it expires (404 after, NFR-011 R-05). Every download is audited by the backend.
 */
export async function downloadTenantExport(slug: string, exportKey: string): Promise<Blob> {
  try {
    const res = await client.get<Blob>(`${BASE}/${slug}/exports/${exportKey}/download`, {
      responseType: 'blob',
    });
    return res.data;
  } catch (error) {
    return rethrowBlobError(error);
  }
}

// ── Members ─────────────────────────────────────────────────────────

/**
 * Every member of a tenant, oldest membership first. The route returns one bounded page since MT-035 (#2131); every page
 * is read so the member list stays complete.
 */
export async function listMembers(slug: string): Promise<Membership[]> {
  return fetchAllPages(async (offset, limit) => {
    const res = await client.get<Membership[]>(`${BASE}/${slug}/members`, {
      params: { offset, limit },
    });
    return res.data;
  });
}

/**
 * Change a member's role (#2032): an actual change carries the **acting administrator's
 * own** step-up — `current_password`, or `step_up_token` / `step_up_code` for the act
 * `tenant_member_role_change` bound to the membership's key; 401 without it.
 */
export async function changeMemberRole(
  slug: string,
  membershipKey: string,
  role: string,
  stepUp: CredentialStepUp,
): Promise<void> {
  await client.patch(`${BASE}/${slug}/members/${membershipKey}/role`, { role, ...stepUp });
}

/**
 * Remove a member (#2032): the body carries the **acting administrator's own** step-up —
 * `current_password`, or `step_up_token` / `step_up_code` for the act
 * `tenant_member_removal` bound to the membership's key; 401 without it.
 */
export async function removeMember(
  slug: string,
  membershipKey: string,
  stepUp: CredentialStepUp,
): Promise<void> {
  await client.delete(`${BASE}/${slug}/members/${membershipKey}`, { data: stepUp });
}

export async function leaveTenant(slug: string): Promise<void> {
  await client.post(`${BASE}/${slug}/leave`);
}

// ── Invitations ─────────────────────────────────────────────────────

/**
 * Every invitation of a tenant, newest first. The route returns one bounded page since MT-035 (#2131); every page is read so
 * the list this feeds stays complete.
 */
export async function listInvitations(slug: string): Promise<Invitation[]> {
  return fetchAllPages(async (offset, limit) => {
    const res = await client.get<Invitation[]>(`${BASE}/${slug}/invitations`, {
      params: { offset, limit },
    });
    return res.data;
  });
}

export async function createEmailInvitation(
  slug: string,
  data: InvitationCreate,
): Promise<InvitationCreated> {
  const res = await client.post<InvitationCreated>(`${BASE}/${slug}/invitations/email`, data);
  return res.data;
}

export async function createLinkInvitation(
  slug: string,
  data: InvitationLinkCreate,
): Promise<InvitationCreated> {
  const res = await client.post<InvitationCreated>(`${BASE}/${slug}/invitations/link`, data);
  return res.data;
}

export async function revokeInvitation(slug: string, invitationKey: string): Promise<void> {
  await client.delete(`${BASE}/${slug}/invitations/${invitationKey}`);
}

export async function acceptInvitation(token: string): Promise<void> {
  await client.post(`${BASE}/invitations/accept`, { token });
}

// ── Assignments ─────────────────────────────────────────────────────

/**
 * Every location assignment of a tenant, oldest first. The route returns one bounded page since MT-035 (#2131); every
 * page is read so the assignment list stays complete.
 */
export async function listAssignments(slug: string): Promise<LocationAssignment[]> {
  return fetchAllPages(async (offset, limit) => {
    const res = await client.get<LocationAssignment[]>(`${BASE}/${slug}/assignments`, {
      params: { offset, limit },
    });
    return res.data;
  });
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
