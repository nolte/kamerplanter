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

import * as tenants from '@/api/endpoints/tenants';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('tenants endpoints — tenant CRUD', () => {
  it('listMyTenants gets /tenants', async () => {
    client.get.mockResolvedValue({ data: [] });
    await tenants.listMyTenants();
    expect(client.get).toHaveBeenCalledWith('/tenants');
  });

  it('createOrganization posts to /tenants', async () => {
    client.post.mockResolvedValue({ data: { key: 't1' } });
    const payload = { name: 'Org' } as never;
    await tenants.createOrganization(payload);
    expect(client.post).toHaveBeenCalledWith('/tenants', payload);
  });

  it('getTenant gets tenant by slug', async () => {
    client.get.mockResolvedValue({ data: { slug: 'org' } });
    await tenants.getTenant('org');
    expect(client.get).toHaveBeenCalledWith('/tenants/org');
  });

  it('updateTenant patches tenant by slug', async () => {
    client.patch.mockResolvedValue({ data: { slug: 'org' } });
    const payload = { name: 'X' } as never;
    await tenants.updateTenant('org', payload);
    expect(client.patch).toHaveBeenCalledWith('/tenants/org', payload);
  });

  it('deleteTenant deletes tenant by slug', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await tenants.deleteTenant('org');
    expect(client.delete).toHaveBeenCalledWith('/tenants/org');
  });
});

describe('tenants endpoints — members', () => {
  it('listMembers gets members for slug', async () => {
    client.get.mockResolvedValue({ data: [] });
    await tenants.listMembers('org');
    expect(client.get).toHaveBeenCalledWith('/tenants/org/members');
  });

  it('changeMemberRole patches role', async () => {
    client.patch.mockResolvedValue({ data: undefined });
    await tenants.changeMemberRole('org', 'm1', 'lead');
    expect(client.patch).toHaveBeenCalledWith('/tenants/org/members/m1/role', {
      role: 'lead',
    });
  });

  it('removeMember deletes membership', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await tenants.removeMember('org', 'm1');
    expect(client.delete).toHaveBeenCalledWith('/tenants/org/members/m1');
  });

  it('leaveTenant posts to leave endpoint', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await tenants.leaveTenant('org');
    expect(client.post).toHaveBeenCalledWith('/tenants/org/leave');
  });
});

describe('tenants endpoints — invitations', () => {
  it('listInvitations gets invitations for slug', async () => {
    client.get.mockResolvedValue({ data: [] });
    await tenants.listInvitations('org');
    expect(client.get).toHaveBeenCalledWith('/tenants/org/invitations');
  });

  it('createEmailInvitation posts to email invitations', async () => {
    client.post.mockResolvedValue({ data: { invitation_key: 'i1', token: 't', expires_at: 'x' } });
    const payload = { email: 'a@b.de', role: 'grower' } as never;
    await tenants.createEmailInvitation('org', payload);
    expect(client.post).toHaveBeenCalledWith('/tenants/org/invitations/email', payload);
  });

  it('createLinkInvitation posts to link invitations', async () => {
    client.post.mockResolvedValue({ data: { invitation_key: 'i1', token: 't', expires_at: 'x' } });
    const payload = { role: 'viewer' } as never;
    await tenants.createLinkInvitation('org', payload);
    expect(client.post).toHaveBeenCalledWith('/tenants/org/invitations/link', payload);
  });

  it('revokeInvitation deletes invitation', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await tenants.revokeInvitation('org', 'i1');
    expect(client.delete).toHaveBeenCalledWith('/tenants/org/invitations/i1');
  });

  it('acceptInvitation posts token to global accept endpoint', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await tenants.acceptInvitation('tok');
    expect(client.post).toHaveBeenCalledWith('/tenants/invitations/accept', { token: 'tok' });
  });
});

describe('tenants endpoints — assignments', () => {
  it('listAssignments gets assignments for slug', async () => {
    client.get.mockResolvedValue({ data: [] });
    await tenants.listAssignments('org');
    expect(client.get).toHaveBeenCalledWith('/tenants/org/assignments');
  });

  it('createAssignment posts assignment', async () => {
    client.post.mockResolvedValue({ data: { key: 'a1' } });
    const payload = { membership_key: 'm1', location_key: 'l1' };
    await tenants.createAssignment('org', payload);
    expect(client.post).toHaveBeenCalledWith('/tenants/org/assignments', payload);
  });

  it('updateAssignment patches assignment', async () => {
    client.patch.mockResolvedValue({ data: { key: 'a1' } });
    const payload = { can_edit: true };
    await tenants.updateAssignment('org', 'a1', payload);
    expect(client.patch).toHaveBeenCalledWith('/tenants/org/assignments/a1', payload);
  });

  it('deleteAssignment deletes assignment', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await tenants.deleteAssignment('org', 'a1');
    expect(client.delete).toHaveBeenCalledWith('/tenants/org/assignments/a1');
  });
});
