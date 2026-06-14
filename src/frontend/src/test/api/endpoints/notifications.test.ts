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

import * as notifications from '@/api/endpoints/notifications';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('notifications endpoints — list & count', () => {
  it('getNotifications gets with empty params by default', async () => {
    client.get.mockResolvedValue({ data: { items: [], total: 0 } });
    await notifications.getNotifications();
    expect(client.get).toHaveBeenCalledWith('/notifications', { params: {} });
  });

  it('getNotifications maps limit, offset and unread_only params', async () => {
    client.get.mockResolvedValue({ data: { items: [], total: 0 } });
    await notifications.getNotifications({ limit: 10, offset: 5, unread_only: true });
    expect(client.get).toHaveBeenCalledWith('/notifications', {
      params: { limit: 10, offset: 5, unread_only: true },
    });
  });

  it('getUnreadCount gets /notifications/count', async () => {
    client.get.mockResolvedValue({ data: { count: 3 } });
    await notifications.getUnreadCount();
    expect(client.get).toHaveBeenCalledWith('/notifications/count');
  });
});

describe('notifications endpoints — read & act', () => {
  it('markRead posts to read endpoint', async () => {
    client.post.mockResolvedValue({ data: { key: 'n1' } });
    await notifications.markRead('n1');
    expect(client.post).toHaveBeenCalledWith('/notifications/n1/read');
  });

  it('markActed posts with action_id param', async () => {
    client.post.mockResolvedValue({ data: { key: 'n1' } });
    await notifications.markActed('n1', 'snooze');
    expect(client.post).toHaveBeenCalledWith('/notifications/n1/act', null, {
      params: { action_id: 'snooze' },
    });
  });
});

describe('notifications endpoints — preferences & channels', () => {
  it('getPreferences gets /notifications/preferences', async () => {
    client.get.mockResolvedValue({ data: {} });
    await notifications.getPreferences();
    expect(client.get).toHaveBeenCalledWith('/notifications/preferences');
  });

  it('updatePreferences puts preferences', async () => {
    client.put.mockResolvedValue({ data: {} });
    const prefs = { email_enabled: true } as never;
    await notifications.updatePreferences(prefs);
    expect(client.put).toHaveBeenCalledWith('/notifications/preferences', prefs);
  });

  it('getChannelStatus gets channel status', async () => {
    client.get.mockResolvedValue({ data: [] });
    await notifications.getChannelStatus();
    expect(client.get).toHaveBeenCalledWith('/notifications/channels/status');
  });

  it('sendTest posts channel key', async () => {
    client.post.mockResolvedValue({ data: { success: true } });
    await notifications.sendTest('ch1');
    expect(client.post).toHaveBeenCalledWith('/notifications/test', { channel_key: 'ch1' });
  });
});

describe('notifications endpoints — markAllRead orchestration', () => {
  it('fetches unread notifications and marks each unread one as read', async () => {
    client.get.mockResolvedValue({
      data: {
        items: [
          { key: 'n1', read_at: null },
          { key: 'n2', read_at: '2026-01-01' },
          { key: 'n3', read_at: null },
        ],
        total: 3,
      },
    });
    client.post.mockResolvedValue({ data: { key: 'x' } });

    await notifications.markAllRead();

    expect(client.get).toHaveBeenCalledWith('/notifications', {
      params: { limit: 200, unread_only: true },
    });
    // Only the two items without read_at should be marked read.
    expect(client.post).toHaveBeenCalledTimes(2);
    expect(client.post).toHaveBeenCalledWith('/notifications/n1/read');
    expect(client.post).toHaveBeenCalledWith('/notifications/n3/read');
    expect(client.post).not.toHaveBeenCalledWith('/notifications/n2/read');
  });

  it('marks nothing when there are no unread notifications', async () => {
    client.get.mockResolvedValue({ data: { items: [], total: 0 } });
    await notifications.markAllRead();
    expect(client.post).not.toHaveBeenCalled();
  });
});
