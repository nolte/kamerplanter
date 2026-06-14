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
    expect(client.get).toHaveBeenCalledWith('/admin/platform/tenants');
  });

  it('fetchAdminUsers gets users', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchAdminUsers();
    expect(client.get).toHaveBeenCalledWith('/admin/platform/users');
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

  it('deleteAdminTenant deletes encoded tenant key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await admin.deleteAdminTenant('t/1');
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/tenants/t%2F1');
  });

  it('deleteAdminUser deletes encoded user key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await admin.deleteAdminUser('u1');
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/users/u1');
  });
});

describe('adminPlatform endpoints — tenant members', () => {
  it('fetchTenantMembers gets members for tenant', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchTenantMembers('t1');
    expect(client.get).toHaveBeenCalledWith('/admin/platform/tenants/t1/members');
  });

  it('addTenantMember posts member to tenant', async () => {
    client.post.mockResolvedValue({ data: { key: 'm1' } });
    const payload = { user_key: 'u1', role: 'grower' } as never;
    await admin.addTenantMember('t1', payload);
    expect(client.post).toHaveBeenCalledWith('/admin/platform/tenants/t1/members', payload);
  });

  it('removeTenantMember deletes member from tenant', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await admin.removeTenantMember('t1', 'm1');
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/tenants/t1/members/m1');
  });

  it('changeTenantMemberRole patches member role', async () => {
    client.patch.mockResolvedValue({ data: { key: 'm1' } });
    await admin.changeTenantMemberRole('t1', 'm1', 'admin' as never);
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/tenants/t1/members/m1/role', {
      role: 'admin',
    });
  });
});

describe('adminPlatform endpoints — user memberships', () => {
  it('fetchUserMemberships gets memberships for user', async () => {
    client.get.mockResolvedValue({ data: [] });
    await admin.fetchUserMemberships('u1');
    expect(client.get).toHaveBeenCalledWith('/admin/platform/users/u1/memberships');
  });

  it('addUserToTenant posts membership for user', async () => {
    client.post.mockResolvedValue({ data: { key: 'm1' } });
    const payload = { tenant_key: 't1', role: 'viewer' } as never;
    await admin.addUserToTenant('u1', payload);
    expect(client.post).toHaveBeenCalledWith('/admin/platform/users/u1/memberships', payload);
  });

  it('removeUserFromTenant deletes membership for user', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await admin.removeUserFromTenant('u1', 'm1');
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/users/u1/memberships/m1');
  });

  it('changeUserMembershipRole patches membership role', async () => {
    client.patch.mockResolvedValue({ data: { key: 'm1' } });
    await admin.changeUserMembershipRole('u1', 'm1', 'grower' as never);
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/users/u1/memberships/m1/role', {
      role: 'grower',
    });
  });
});
