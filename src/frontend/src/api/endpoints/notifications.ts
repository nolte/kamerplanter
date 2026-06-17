import { tenantClient as client } from '../client';
import type {
  NotificationListResponse,
  NotificationPreferencesRequest,
  NotificationPreferencesResponse,
  NotificationResponse,
  UnreadCountResponse,
  ChannelStatusResponse,
  TestNotificationResponse,
  PwaVapidPublicKeyResponse,
  PwaSubscribeResponse,
} from '../types';

const BASE = '/notifications';

export interface NotificationListParams {
  limit?: number;
  offset?: number;
  unread_only?: boolean;
}

export async function getNotifications(
  params: NotificationListParams = {},
): Promise<NotificationListResponse> {
  const queryParams: Record<string, string | number | boolean> = {};
  if (params.limit != null) queryParams.limit = params.limit;
  if (params.offset != null) queryParams.offset = params.offset;
  if (params.unread_only != null) queryParams.unread_only = params.unread_only;
  const { data } = await client.get<NotificationListResponse>(BASE, {
    params: queryParams,
  });
  return data;
}

export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const { data } = await client.get<UnreadCountResponse>(`${BASE}/count`);
  return data;
}

export async function markRead(
  notificationKey: string,
): Promise<NotificationResponse> {
  const { data } = await client.post<NotificationResponse>(
    `${BASE}/${notificationKey}/read`,
  );
  return data;
}

export async function markActed(
  notificationKey: string,
  actionId: string,
): Promise<NotificationResponse> {
  const { data } = await client.post<NotificationResponse>(
    `${BASE}/${notificationKey}/act`,
    null,
    { params: { action_id: actionId } },
  );
  return data;
}

export async function getPreferences(): Promise<NotificationPreferencesResponse> {
  const { data } = await client.get<NotificationPreferencesResponse>(
    `${BASE}/preferences`,
  );
  return data;
}

export async function updatePreferences(
  prefs: NotificationPreferencesRequest,
): Promise<NotificationPreferencesResponse> {
  const { data } = await client.put<NotificationPreferencesResponse>(
    `${BASE}/preferences`,
    prefs,
  );
  return data;
}

export async function getChannelStatus(): Promise<ChannelStatusResponse[]> {
  const { data } = await client.get<ChannelStatusResponse[]>(
    `${BASE}/channels/status`,
  );
  return data;
}

export async function sendTest(
  channelKey: string,
): Promise<TestNotificationResponse> {
  const { data } = await client.post<TestNotificationResponse>(
    `${BASE}/test`,
    { channel_key: channelKey },
  );
  return data;
}

// ── Web Push (PWA) subscription management ──────────────────────────────

export async function getPwaVapidPublicKey(): Promise<PwaVapidPublicKeyResponse> {
  const { data } = await client.get<PwaVapidPublicKeyResponse>(
    `${BASE}/pwa/vapid-public-key`,
  );
  return data;
}

/**
 * Register a browser push subscription with the backend. Accepts the plain
 * object produced by `PushSubscription.toJSON()` and forwards the endpoint plus
 * the p256dh/auth keys together with the current user agent.
 */
export async function subscribePwa(
  subscription: PushSubscriptionJSON,
): Promise<PwaSubscribeResponse> {
  const { data } = await client.post<PwaSubscribeResponse>(`${BASE}/pwa/subscribe`, {
    endpoint: subscription.endpoint ?? '',
    p256dh: subscription.keys?.p256dh ?? '',
    auth: subscription.keys?.auth ?? '',
    user_agent:
      typeof navigator !== 'undefined' ? navigator.userAgent : '',
  });
  return data;
}

export async function unsubscribePwa(endpoint: string): Promise<void> {
  await client.post(`${BASE}/pwa/unsubscribe`, { endpoint });
}

export async function markAllRead(): Promise<void> {
  // Mark all unread notifications as read by fetching and marking each one.
  // If a bulk endpoint exists in the future, replace this implementation.
  const { items } = await getNotifications({ limit: 200, unread_only: true });
  await Promise.all(
    items.filter((n) => !n.read_at).map((n) => markRead(n.key)),
  );
}
