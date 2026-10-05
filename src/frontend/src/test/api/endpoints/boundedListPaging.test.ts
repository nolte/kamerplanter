/**
 * MT-035 (#2131) — list routes that answered every row now answer one bounded
 * page (default 50, at most 200). The endpoint functions behind views that need
 * the whole list read page after page, so nothing is cut at row 51.
 *
 * Each case serves a full first page and a short second one: a function that
 * still issued a single request would return 200 rows instead of 201.
 */
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
  getActiveTenantSlug: () => 'mein-garten',
}));

import * as admin from '@/api/endpoints/adminPlatform';
import * as ai from '@/api/endpoints/ai';
import * as postHarvest from '@/api/endpoints/postHarvest';
import * as tasks from '@/api/endpoints/tasks';
import * as tenants from '@/api/endpoints/tenants';
import { MAX_PAGE_SIZE } from '@/api/paginate';

const client = mocks.client;

function rows(count: number, from = 0): { key: string }[] {
  return Array.from({ length: count }, (_, i) => ({ key: `row-${from + i}` }));
}

beforeEach(() => {
  vi.clearAllMocks();
  client.get.mockReset();
});

const cases: { name: string; url: string; load: () => Promise<unknown[]>; extra?: Record<string, string> }[] = [
  { name: 'fetchAdminTenants', url: '/admin/platform/tenants', load: () => admin.fetchAdminTenants() },
  { name: 'fetchAdminUsers', url: '/admin/platform/users', load: () => admin.fetchAdminUsers() },
  { name: 'listInvitations', url: '/tenants/org/invitations', load: () => tenants.listInvitations('org') },
  { name: 'listConversations', url: '/ai/conversations', load: () => ai.listConversations() },
  { name: 'getTasksForPlant', url: '/tasks/plants/p1', load: () => tasks.getTasksForPlant('p1') },
  {
    name: 'getTasksForPlant with status',
    url: '/tasks/plants/p1',
    load: () => tasks.getTasksForPlant('p1', 'pending'),
    extra: { status: 'pending' },
  },
  {
    name: 'getObservations',
    url: '/post-harvest/ph1/observations',
    load: () => postHarvest.getObservations('ph1'),
  },
];

describe('bounded list routes are read completely (MT-035)', () => {
  it.each(cases)('$name reads past the first page', async ({ url, load, extra }) => {
    client.get
      .mockResolvedValueOnce({ data: rows(MAX_PAGE_SIZE) })
      .mockResolvedValueOnce({ data: rows(1, MAX_PAGE_SIZE) });

    const all = await load();

    expect(all).toHaveLength(MAX_PAGE_SIZE + 1);
    expect(client.get).toHaveBeenCalledTimes(2);
    expect(client.get).toHaveBeenNthCalledWith(1, url, {
      params: { offset: 0, limit: MAX_PAGE_SIZE, ...extra },
    });
    expect(client.get).toHaveBeenNthCalledWith(2, url, {
      params: { offset: MAX_PAGE_SIZE, limit: MAX_PAGE_SIZE, ...extra },
    });
  });

  it.each(cases)('$name stops after a short first page', async ({ load }) => {
    client.get.mockResolvedValueOnce({ data: rows(3) });

    expect(await load()).toHaveLength(3);
    expect(client.get).toHaveBeenCalledTimes(1);
  });
});
