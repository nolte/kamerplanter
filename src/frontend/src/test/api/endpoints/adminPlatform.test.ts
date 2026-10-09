import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { client };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import * as admin from '@/api/endpoints/adminPlatform';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('adminPlatform endpoints — stats, tenants, users', () => {
  it('fetchAdminStats gets platform stats', async () => {
    client.get.mockResolvedValue({ data: {} });
    await admin.fetchAdminStats();
    expect(client.get).toHaveBeenCalledWith('/admin/platform/stats');
  });

  it('fetchAdminTenants gets tenants', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchAdminTenants();
    expect(client.get).toHaveBeenCalledWith('/admin/platform/tenants', { params: { offset: 0, limit: 200 } });
  });

  it('fetchAdminUsers gets users', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchAdminUsers();
    expect(client.get).toHaveBeenCalledWith('/admin/platform/users', { params: { offset: 0, limit: 200 } });
  });

  it('updateAdminTenant patches encoded tenant key', async () => {
    client.patch.mockResolvedValue({ data: { key: 't 1' } });
    const payload = { name: 'X' } as never;
    await admin.updateAdminTenant('t 1', payload);
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/tenants/t%201', payload);
  });

  it('updateAdminUser patches encoded user key', async () => {
    client.patch.mockResolvedValue({ data: { key: 'u1' } });
    const payload = { is_active: false } as never;
    await admin.updateAdminUser('u1', payload);
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/users/u1', payload);
  });

  it("updateAdminUser carries the admin's own step-up beside the update (#1857)", async () => {
    client.patch.mockResolvedValue({ data: { key: 'u1' } });
    await admin.updateAdminUser('u1', { email_verified: true, current_password: 'admin-pw' });
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/users/u1', {
      email_verified: true,
      current_password: 'admin-pw',
    });
  });

  it('deleteAdminTenant deletes encoded tenant key and carries the step-up (#1791)', async () => {
    const accepted = { tenant_key: 't/1', status: 'in_progress', requested_at: null, message: 'ok' };
    client.delete.mockResolvedValue({ data: accepted });
    await expect(admin.deleteAdminTenant('t/1', { confirm_slug: 't-1' })).resolves.toEqual(accepted);
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/tenants/t%2F1', {
      data: { confirm_slug: 't-1' },
    });
  });

  it('getAdminUserErasurePreview reads the encoded target key and returns the preview (#1961)', async () => {
    client.get.mockResolvedValue({ data: { personal_tenants: [{ name: 'Garden', other_member_count: 2 }] } });
    const preview = await admin.getAdminUserErasurePreview('u 1');
    expect(client.get).toHaveBeenCalledWith('/admin/platform/users/u%201/erasure-preview');
    expect(preview.personal_tenants).toEqual([{ name: 'Garden', other_member_count: 2 }]);
  });

  it('getAdminErasureStatus reads the encoded erasure key (#1949)', async () => {
    client.get.mockResolvedValue({ data: { key: 'er/1', status: 'partially_completed', requested_at: null } });
    const status = await admin.getAdminErasureStatus('er/1');
    expect(client.get).toHaveBeenCalledWith('/admin/platform/erasures/er%2F1');
    expect(status.status).toBe('partially_completed');
  });

  it("deleteAdminUser deletes encoded user key and carries the target's e-mail step-up (#1814)", async () => {
    const accepted = { erasure_key: 'er-1', status: 'scheduled', requested_at: null, message: 'accepted' };
    client.delete.mockResolvedValue({ data: accepted });
    // 202 since #1949: the accepted request comes back, not `void`.
    await expect(
      admin.deleteAdminUser('u/1', { confirm_email: 'target@example.org', password: 'admin-pw' }),
    ).resolves.toEqual(accepted);
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/users/u%2F1', {
      data: { confirm_email: 'target@example.org', password: 'admin-pw' },
    });
  });
});

describe('adminPlatform endpoints — tenant members', () => {
  it('fetchTenantMembers gets members for tenant', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchTenantMembers('t1');
    expect(client.get).toHaveBeenCalledWith('/admin/platform/tenants/t1/members', {
      params: { offset: 0, limit: 200 },
    });
  });

  it("addTenantMember posts member to tenant with the admin's step-up (#2106)", async () => {
    client.post.mockResolvedValue({ data: { key: 'm1' } });
    const payload = { user_key: 'u1', role: 'grower' } as never;
    await admin.addTenantMember('t1', payload, { current_password: 'pw' });
    expect(client.post).toHaveBeenCalledWith('/admin/platform/tenants/t1/members', {
      user_key: 'u1',
      role: 'grower',
      current_password: 'pw',
    });
  });

  it("removeTenantMember deletes member from tenant with the admin's step-up (#2009)", async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await admin.removeTenantMember('t1', 'm1', { current_password: 'pw' });
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/tenants/t1/members/m1', {
      data: { current_password: 'pw' },
    });
  });

  it("changeTenantMemberRole patches member role with the admin's step-up (#2032)", async () => {
    client.patch.mockResolvedValue({ data: { key: 'm1' } });
    await admin.changeTenantMemberRole('t1', 'm1', 'lead' as never, { current_password: 'pw' });
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/tenants/t1/members/m1/role', {
      role: 'lead',
      current_password: 'pw',
    });
  });
});

describe('adminPlatform endpoints — user memberships', () => {
  it('fetchUserMemberships gets memberships for user', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchUserMemberships('u1');
    expect(client.get).toHaveBeenCalledWith('/admin/platform/users/u1/memberships');
  });

  it("addUserToTenant posts membership for user with the admin's step-up (#2106)", async () => {
    client.post.mockResolvedValue({ data: { key: 'm1' } });
    const payload = { tenant_key: 't1', role: 'viewer' } as never;
    await admin.addUserToTenant('u1', payload, { step_up_code: '12345678' });
    expect(client.post).toHaveBeenCalledWith('/admin/platform/users/u1/memberships', {
      tenant_key: 't1',
      role: 'viewer',
      step_up_code: '12345678',
    });
  });

  it("removeUserFromTenant deletes membership for user with the admin's step-up (#2009)", async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await admin.removeUserFromTenant('u1', 'm1', { step_up_code: '12345678' });
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/users/u1/memberships/m1', {
      data: { step_up_code: '12345678' },
    });
  });

  it("changeUserMembershipRole patches membership role with the admin's step-up (#2032)", async () => {
    client.patch.mockResolvedValue({ data: { key: 'm1' } });
    await admin.changeUserMembershipRole('u1', 'm1', 'grower' as never, { step_up_token: 'tok' });
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/users/u1/memberships/m1/role', {
      role: 'grower',
      step_up_token: 'tok',
    });
  });
});
