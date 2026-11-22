/**
 * Web Push delivery logic of the service worker (taken over from the former `public/sw.js`,
 * REQ-053 WP 9.1, #2741). Pure functions; `src/sw.ts` wires them to the `push` and
 * `notificationclick` events.
 */

export const DEFAULT_NOTIFICATION_ICON = '/icons/icon-192.png';
export const DEFAULT_NOTIFICATION_BADGE = '/icons/icon-192.png';
export const DEFAULT_NOTIFICATION_TITLE = 'Kamerplanter';

/** The part of `PushMessageData` the parser reads. */
export interface PushDataLike {
  json(): unknown;
  text(): string;
}

/** The JSON body the backend pushes; every field is optional and untrusted. */
export interface PushPayload {
  title?: unknown;
  body?: unknown;
  icon?: unknown;
  badge?: unknown;
  data?: unknown;
  actions?: unknown;
  tag?: unknown;
  requireInteraction?: unknown;
}

/** Options handed to `showNotification` (a superset of the DOM lib's `NotificationOptions`). */
export interface PushNotificationOptions {
  body: string;
  icon: string;
  badge: string;
  data: Record<string, unknown>;
  actions: unknown[];
  tag?: string;
  renotify?: boolean;
  requireInteraction: boolean;
}

/**
 * Parse the push payload. The backend pushes a JSON body; fall back to a plain text body or an empty
 * object so a malformed push never throws.
 */
export function parsePushData(data: PushDataLike | null | undefined): PushPayload {
  if (!data) return {};
  try {
    const parsed = data.json();
    return parsed && typeof parsed === 'object' ? (parsed as PushPayload) : {};
  } catch {
    try {
      return { body: data.text() };
    } catch {
      return {};
    }
  }
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

/** Title and options of the notification shown for one push. */
export function buildNotification(payload: PushPayload): {
  title: string;
  options: PushNotificationOptions;
} {
  const tag = asString(payload.tag);
  const data =
    payload.data && typeof payload.data === 'object' ? (payload.data as Record<string, unknown>) : {};
  return {
    title: asString(payload.title) ?? DEFAULT_NOTIFICATION_TITLE,
    options: {
      body: asString(payload.body) ?? '',
      icon: asString(payload.icon) ?? DEFAULT_NOTIFICATION_ICON,
      badge: asString(payload.badge) ?? DEFAULT_NOTIFICATION_BADGE,
      data,
      actions: Array.isArray(payload.actions) ? payload.actions : [],
      tag,
      renotify: tag ? true : undefined,
      requireInteraction: payload.requireInteraction === true,
    },
  };
}

/**
 * Constrain a notification-supplied URL to a safe same-origin path. The push payload is built
 * server-side but may carry data derived from user content, so the worker must never navigate
 * cross-origin (open redirect / phishing from the trusted app origin). Any cross-origin,
 * non-parseable or unexpected value falls back to the app root.
 */
export function toSafeSameOriginPath(candidate: unknown, origin: string): string {
  if (!candidate || typeof candidate !== 'string') return '/';
  try {
    const url = new URL(candidate, origin);
    if (url.origin !== origin) return '/';
    return url.pathname + url.search + url.hash;
  } catch {
    return '/';
  }
}

/**
 * The URL to open or focus for a notification click. Action buttons may carry their own URL via
 * `data.action_urls[actionId]`; otherwise `data.url` or the app root. Always a same-origin path.
 */
export function resolveTargetUrl(
  notificationData: unknown,
  action: string | undefined,
  origin: string,
): string {
  const data =
    notificationData && typeof notificationData === 'object'
      ? (notificationData as { action_urls?: unknown; url?: unknown })
      : {};
  const actionUrls =
    data.action_urls && typeof data.action_urls === 'object'
      ? (data.action_urls as Record<string, unknown>)
      : undefined;
  if (action && actionUrls && actionUrls[action]) {
    return toSafeSameOriginPath(actionUrls[action], origin);
  }
  return toSafeSameOriginPath(data.url, origin);
}
