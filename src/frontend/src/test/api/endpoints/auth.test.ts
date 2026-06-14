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

import * as auth from '@/api/endpoints/auth';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
  // Reset cookies between tests so CSRF header assertions are deterministic.
  Object.defineProperty(document, 'cookie', {
    writable: true,
    configurable: true,
    value: '',
  });
});

describe('auth endpoints', () => {
  it('register posts to /auth/register and returns data', async () => {
    const profile = { key: 'u1', email: 'a@b.de' };
    client.post.mockResolvedValue({ data: profile });
    const payload = { email: 'a@b.de', password: 'pw' } as never;
    await expect(auth.register(payload)).resolves.toEqual(profile);
    expect(client.post).toHaveBeenCalledWith('/auth/register', payload);
  });

  it('login posts to /auth/login and returns data', async () => {
    const res = { access_token: 'tok' };
    client.post.mockResolvedValue({ data: res });
    const payload = { email: 'a@b.de', password: 'pw' } as never;
    await expect(auth.login(payload)).resolves.toEqual(res);
    expect(client.post).toHaveBeenCalledWith('/auth/login', payload);
  });

  it('refresh posts to /auth/refresh with CSRF header from cookie', async () => {
    document.cookie = 'csrf_token=abc123';
    client.post.mockResolvedValue({ data: { access_token: 't' } });
    await auth.refresh();
    expect(client.post).toHaveBeenCalledWith('/auth/refresh', null, {
      headers: { 'X-CSRF-Token': 'abc123' },
    });
  });

  it('refresh sends empty header object when no CSRF cookie present', async () => {
    client.post.mockResolvedValue({ data: { access_token: 't' } });
    await auth.refresh();
    expect(client.post).toHaveBeenCalledWith('/auth/refresh', null, {
      headers: {},
    });
  });

  it('logout posts to /auth/logout with CSRF header', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await auth.logout();
    expect(client.post).toHaveBeenCalledWith('/auth/logout', null, {
      headers: {},
    });
  });

  it('logoutAll posts to /auth/logout-all', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await auth.logoutAll();
    expect(client.post).toHaveBeenCalledWith('/auth/logout-all', null, {
      headers: {},
    });
  });

  it('verifyEmail posts token to /auth/verify-email', async () => {
    const profile = { key: 'u1' };
    client.post.mockResolvedValue({ data: profile });
    await expect(auth.verifyEmail('tok')).resolves.toEqual(profile);
    expect(client.post).toHaveBeenCalledWith('/auth/verify-email', { token: 'tok' });
  });

  it('requestPasswordReset posts email', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await auth.requestPasswordReset('a@b.de');
    expect(client.post).toHaveBeenCalledWith('/auth/password-reset/request', {
      email: 'a@b.de',
    });
  });

  it('confirmPasswordReset posts token and new_password', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await auth.confirmPasswordReset('tok', 'newpw');
    expect(client.post).toHaveBeenCalledWith('/auth/password-reset/confirm', {
      token: 'tok',
      new_password: 'newpw',
    });
  });

  it('getOAuthProviders gets /auth/oauth/providers', async () => {
    const providers = [{ name: 'google' }];
    client.get.mockResolvedValue({ data: providers });
    await expect(auth.getOAuthProviders()).resolves.toEqual(providers);
    expect(client.get).toHaveBeenCalledWith('/auth/oauth/providers');
  });

  it('getProfile gets /users/me', async () => {
    const profile = { key: 'u1' };
    client.get.mockResolvedValue({ data: profile });
    await expect(auth.getProfile()).resolves.toEqual(profile);
    expect(client.get).toHaveBeenCalledWith('/users/me');
  });

  it('updateProfile patches /users/me', async () => {
    const profile = { key: 'u1', display_name: 'X' };
    client.patch.mockResolvedValue({ data: profile });
    const payload = { display_name: 'X' } as never;
    await expect(auth.updateProfile(payload)).resolves.toEqual(profile);
    expect(client.patch).toHaveBeenCalledWith('/users/me', payload);
  });

  it('listProviders gets /users/me/providers', async () => {
    client.get.mockResolvedValue({ data: [] });
    await expect(auth.listProviders()).resolves.toEqual([]);
    expect(client.get).toHaveBeenCalledWith('/users/me/providers');
  });

  it('unlinkProvider deletes provider by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await auth.unlinkProvider('p1');
    expect(client.delete).toHaveBeenCalledWith('/users/me/providers/p1');
  });

  it('changePassword posts current and new password', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await auth.changePassword('old', 'new');
    expect(client.post).toHaveBeenCalledWith('/users/me/password', {
      current_password: 'old',
      new_password: 'new',
    });
  });

  it('changePassword passes null current password for federated accounts', async () => {
    client.post.mockResolvedValue({ data: undefined });
    await auth.changePassword(null, 'new');
    expect(client.post).toHaveBeenCalledWith('/users/me/password', {
      current_password: null,
      new_password: 'new',
    });
  });

  it('listSessions gets /users/me/sessions', async () => {
    client.get.mockResolvedValue({ data: [] });
    await expect(auth.listSessions()).resolves.toEqual([]);
    expect(client.get).toHaveBeenCalledWith('/users/me/sessions');
  });

  it('revokeSession deletes session by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await auth.revokeSession('s1');
    expect(client.delete).toHaveBeenCalledWith('/users/me/sessions/s1');
  });

  it('deleteAccount deletes /users/me', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await auth.deleteAccount();
    expect(client.delete).toHaveBeenCalledWith('/users/me');
  });

  it('createApiKey posts to /auth/api-keys', async () => {
    const created = { key: 'k1', secret: 's' };
    client.post.mockResolvedValue({ data: created });
    const payload = { name: 'CI' } as never;
    await expect(auth.createApiKey(payload)).resolves.toEqual(created);
    expect(client.post).toHaveBeenCalledWith('/auth/api-keys', payload);
  });

  it('listApiKeys gets /auth/api-keys', async () => {
    client.get.mockResolvedValue({ data: [] });
    await expect(auth.listApiKeys()).resolves.toEqual([]);
    expect(client.get).toHaveBeenCalledWith('/auth/api-keys');
  });

  it('revokeApiKey deletes key by id', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await auth.revokeApiKey('k1');
    expect(client.delete).toHaveBeenCalledWith('/auth/api-keys/k1');
  });
});
