import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  ENVIRONMENTS,
  initErrorTracking,
  isErrorTrackingActive,
  isSensitiveName,
  redactRecord,
  resetErrorTrackingForTests,
  scrubBreadcrumb,
  scrubEvent,
  scrubUrl,
} from '@/observability/errorTracking';

/**
 * #777 — the browser half of the error-tracking contract.
 *
 * Two properties matter and both fail silently in production if they break:
 * the optionality contract (no DSN => the SDK chunk is never even fetched) and
 * the scrubbing rules (nothing personal leaves the browser).
 */
describe('errorTracking', () => {
  beforeEach(() => {
    resetErrorTrackingForTests();
    delete window.__RUNTIME_CONFIG__;
  });

  afterEach(() => {
    delete window.__RUNTIME_CONFIG__;
    vi.restoreAllMocks();
  });

  describe('optionality', () => {
    it('does nothing when no runtime config was served at all', async () => {
      await expect(initErrorTracking()).resolves.toBe(false);
      expect(isErrorTrackingActive()).toBe(false);
    });

    it('does nothing when the DSN is present but empty', async () => {
      // A Helm value or entrypoint default of "" arrives as a blank string,
      // not as an absent key — the shape every deployment ships by default.
      window.__RUNTIME_CONFIG__ = { SENTRY_DSN: '   ' };

      await expect(initErrorTracking()).resolves.toBe(false);
      expect(isErrorTrackingActive()).toBe(false);
    });
  });

  describe('scrubUrl', () => {
    it('keeps the path and redacts credential-shaped parameters by name', () => {
      expect(scrubUrl('/api/v1/plants?page=2&api_key=s3cr3t&sort=name')).toBe(
        '/api/v1/plants?page=2&api_key=[redacted]&sort=name',
      );
    });

    it('leaves a URL without a query string untouched', () => {
      expect(scrubUrl('/api/v1/plants')).toBe('/api/v1/plants');
    });

    it('leaves a valueless parameter alone rather than guessing', () => {
      expect(scrubUrl('/x?flag')).toBe('/x?flag');
    });
  });

  describe('isSensitiveName / redactRecord', () => {
    it('matches on the name, never on the value', () => {
      expect(isSensitiveName('Authorization')).toBe(true);
      expect(isSensitiveName('refresh_token')).toBe(true);
      expect(isSensitiveName('plantName')).toBe(false);
    });

    it('redacts in place and keeps the key visible', () => {
      const record: Record<string, unknown> = { tenant: 'acme', access_token: 'abc' };
      redactRecord(record);
      // The key survives so a reader can tell a credential was present here.
      expect(record).toEqual({ tenant: 'acme', access_token: '[redacted]' });
    });
  });

  describe('scrubEvent', () => {
    it('drops the request body and cookies but keeps the route', () => {
      const event: Record<string, unknown> = {
        request: {
          url: 'https://kp.example/plants/new?token=abc',
          data: { note: 'private observation' },
          cookies: { session: 'xyz' },
        },
      };

      const request = scrubEvent(event).request as Record<string, unknown>;

      expect(request.data).toBeUndefined();
      expect(request.cookies).toBeUndefined();
      expect(request.url).toBe('https://kp.example/plants/new?token=[redacted]');
    });

    it('keeps only the join keys on the user context', () => {
      const event: Record<string, unknown> = {
        user: { id: 'users/42', tenant: 'acme', email: 'grower@example.org', username: 'grower' },
      };

      expect(scrubEvent(event).user).toEqual({ id: 'users/42', tenant: 'acme' });
    });

    it('redacts extra, tags and contexts by key name', () => {
      const event: Record<string, unknown> = {
        extra: { plantId: 'plants/1', sessionToken: 'abc' },
        tags: { release: 'x' },
        contexts: { apiKey: 'nope' },
      };

      const scrubbed = scrubEvent(event);

      expect(scrubbed.extra).toEqual({ plantId: 'plants/1', sessionToken: '[redacted]' });
      expect(scrubbed.tags).toEqual({ release: 'x' });
      expect(scrubbed.contexts).toEqual({ apiKey: '[redacted]' });
    });

    it('tolerates an event carrying none of those sections', () => {
      // The hook runs on every event; a throw here would drop it entirely.
      expect(scrubEvent({ message: 'boom' })).toEqual({ message: 'boom' });
    });
  });

  describe('scrubBreadcrumb', () => {
    it('drops ui.input breadcrumbs wholesale', () => {
      expect(scrubBreadcrumb({ category: 'ui.input', message: 'input[name=email]' })).toBeNull();
    });

    it('keeps navigation breadcrumbs but scrubs their URLs', () => {
      const crumb = scrubBreadcrumb({
        category: 'navigation',
        data: { from: '/login?token=a', to: '/dashboard' },
      });

      expect(crumb).not.toBeNull();
      expect((crumb!.data as Record<string, unknown>).from).toBe('/login?token=[redacted]');
      expect((crumb!.data as Record<string, unknown>).to).toBe('/dashboard');
    });

    it('redacts credential-shaped keys in breadcrumb data', () => {
      const crumb = scrubBreadcrumb({ category: 'fetch', data: { authorization: 'Bearer x' } })!;

      expect((crumb.data as Record<string, unknown>).authorization).toBe('[redacted]');
    });
  });

  it('declares the same stage vocabulary as the Python side', () => {
    // Alert rules filter on these exact strings across every component; a
    // divergence here means a stage that silently never alerts.
    expect(ENVIRONMENTS).toEqual(['development', 'e2e', 'staging', 'production']);
  });
});
