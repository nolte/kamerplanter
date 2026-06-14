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

import * as calendar from '@/api/endpoints/calendar';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('calendar endpoints — events', () => {
  it('getCalendarEvents gets with start and end only', async () => {
    client.get.mockResolvedValue({ data: { events: [] } });
    await calendar.getCalendarEvents('2026-01-01', '2026-01-31');
    expect(client.get).toHaveBeenCalledWith('/calendar/events', {
      params: { start: '2026-01-01', end: '2026-01-31' },
    });
  });

  it('getCalendarEvents adds category and tenant_key params', async () => {
    client.get.mockResolvedValue({ data: { events: [] } });
    await calendar.getCalendarEvents('2026-01-01', '2026-01-31', 'care', 't1');
    expect(client.get).toHaveBeenCalledWith('/calendar/events', {
      params: { start: '2026-01-01', end: '2026-01-31', category: 'care', tenant_key: 't1' },
    });
  });
});

describe('calendar endpoints — feeds', () => {
  it('createCalendarFeed posts name and filters', async () => {
    client.post.mockResolvedValue({ data: { key: 'f1' } });
    const filters = { categories: ['care'], site_key: 's1' };
    await calendar.createCalendarFeed('My Feed', filters);
    expect(client.post).toHaveBeenCalledWith('/calendar/feeds', {
      name: 'My Feed',
      filters,
    });
  });

  it('listCalendarFeeds gets with no params by default', async () => {
    client.get.mockResolvedValue({ data: [] });
    await calendar.listCalendarFeeds();
    expect(client.get).toHaveBeenCalledWith('/calendar/feeds', { params: {} });
  });

  it('listCalendarFeeds adds user_key and tenant_key params', async () => {
    client.get.mockResolvedValue({ data: [] });
    await calendar.listCalendarFeeds('u1', 't1');
    expect(client.get).toHaveBeenCalledWith('/calendar/feeds', {
      params: { user_key: 'u1', tenant_key: 't1' },
    });
  });

  it('getCalendarFeed gets feed by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'f1' } });
    await calendar.getCalendarFeed('f1');
    expect(client.get).toHaveBeenCalledWith('/calendar/feeds/f1');
  });

  it('updateCalendarFeed puts feed body', async () => {
    client.put.mockResolvedValue({ data: { key: 'f1' } });
    const body = {
      name: 'X',
      filters: { categories: [], site_key: null },
      is_active: true,
    };
    await calendar.updateCalendarFeed('f1', body);
    expect(client.put).toHaveBeenCalledWith('/calendar/feeds/f1', body);
  });

  it('deleteCalendarFeed deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await calendar.deleteCalendarFeed('f1');
    expect(client.delete).toHaveBeenCalledWith('/calendar/feeds/f1');
  });

  it('regenerateCalendarFeedToken posts to regenerate-token', async () => {
    client.post.mockResolvedValue({ data: { key: 'f1' } });
    await calendar.regenerateCalendarFeedToken('f1');
    expect(client.post).toHaveBeenCalledWith('/calendar/feeds/f1/regenerate-token');
  });
});

describe('calendar endpoints — sowing & season overview', () => {
  it('getSowingCalendar gets with no params by default', async () => {
    client.get.mockResolvedValue({ data: {} });
    await calendar.getSowingCalendar();
    expect(client.get).toHaveBeenCalledWith('/calendar/sowing', { params: {} });
  });

  it('getSowingCalendar adds site_id and stringified year', async () => {
    client.get.mockResolvedValue({ data: {} });
    await calendar.getSowingCalendar('s1', 2026);
    expect(client.get).toHaveBeenCalledWith('/calendar/sowing', {
      params: { site_id: 's1', year: '2026' },
    });
  });

  it('getSeasonOverview gets with no params by default', async () => {
    client.get.mockResolvedValue({ data: {} });
    await calendar.getSeasonOverview();
    expect(client.get).toHaveBeenCalledWith('/calendar/season-overview', { params: {} });
  });

  it('getSeasonOverview adds site_id and stringified year', async () => {
    client.get.mockResolvedValue({ data: {} });
    await calendar.getSeasonOverview('s1', 2027);
    expect(client.get).toHaveBeenCalledWith('/calendar/season-overview', {
      params: { site_id: 's1', year: '2027' },
    });
  });
});
