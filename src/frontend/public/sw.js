/* Kamerplanter service worker — Web Push notification channel.
 *
 * Intentionally framework-free plain JavaScript: this file is served as-is from
 * /sw.js (it is NOT processed by Vite). It only handles push delivery and
 * notification clicks; it does not cache app assets.
 */

/* global self, clients */

const DEFAULT_ICON = '/icons/icon-192.png';
const DEFAULT_BADGE = '/icons/icon-192.png';
const DEFAULT_TITLE = 'Kamerplanter';

self.addEventListener('install', () => {
  // Activate the new worker immediately instead of waiting for old clients.
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Take control of already-open clients as soon as the worker activates.
  event.waitUntil(self.clients.claim());
});

/**
 * Parse the push payload. The backend pushes a JSON body; fall back to a plain
 * text body or an empty object so a malformed push never throws.
 */
function parsePushData(event) {
  if (!event.data) {
    return {};
  }
  try {
    return event.data.json();
  } catch {
    try {
      return { body: event.data.text() };
    } catch {
      return {};
    }
  }
}

self.addEventListener('push', (event) => {
  const payload = parsePushData(event);
  const title = payload.title || DEFAULT_TITLE;
  const options = {
    body: payload.body || '',
    icon: payload.icon || DEFAULT_ICON,
    badge: payload.badge || DEFAULT_BADGE,
    data: payload.data || {},
    actions: Array.isArray(payload.actions) ? payload.actions : [],
    tag: payload.tag,
    renotify: payload.tag ? true : undefined,
    requireInteraction: payload.requireInteraction === true,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

/**
 * Constrain a notification-supplied URL to a safe same-origin path. The push
 * payload is built server-side but may carry data derived from user content, so
 * the service worker must never navigate cross-origin (open-redirect / phishing
 * from the trusted app origin). Any cross-origin, non-parseable, or unexpected
 * scheme falls back to the app root.
 */
function toSafeSameOriginPath(candidate) {
  if (!candidate || typeof candidate !== 'string') {
    return '/';
  }
  try {
    const url = new URL(candidate, self.location.origin);
    if (url.origin !== self.location.origin) {
      return '/';
    }
    return url.pathname + url.search + url.hash;
  } catch {
    return '/';
  }
}

/**
 * Resolve the URL to open/focus for a notification click. Action buttons may
 * carry their own URL via data.action_urls[actionId]; otherwise fall back to
 * data.url or the app root. The result is always a safe same-origin path.
 */
function resolveTargetUrl(notification, action) {
  const data = notification.data || {};
  if (action && data.action_urls && data.action_urls[action]) {
    return toSafeSameOriginPath(data.action_urls[action]);
  }
  return toSafeSameOriginPath(data.url);
}

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const targetUrl = resolveTargetUrl(event.notification, event.action);

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Focus an already-open client when one exists.
        for (const client of windowClients) {
          if ('focus' in client) {
            client.focus();
            if ('navigate' in client && targetUrl) {
              client.navigate(targetUrl).catch(() => {
                /* navigation is best-effort */
              });
            }
            return undefined;
          }
        }
        // Otherwise open a new window at the target URL.
        if (self.clients.openWindow) {
          return self.clients.openWindow(targetUrl);
        }
        return undefined;
      }),
  );
});
