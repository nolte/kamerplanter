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
 * The SDK is behind a dynamic `import()`; the hoisted factory intercepts it so
 * `initErrorTracking` can be driven to its `Sentry.init` call without loading
 * the real chunk. Only the two members this module touches are stubbed.
 */
const sentryStub = vi.hoisted(() => ({ init: vi.fn(), captureException: vi.fn() }));
vi.mock('@sentry/react', () => sentryStub);

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
    sentryStub.init.mockReset();
    vi.restoreAllMocks();
  });

  describe('optionality', () => {
    it('does nothing when no runtime config was served at all', async () => {
      await expect(initErrorTracking()).resolves.toBe(false);
      expect(isErrorTrackingActive()).toBe(false);
      // The chunk contract: nothing was even imported, let alone initialised.
      expect(sentryStub.init).not.toHaveBeenCalled();
    });

    it('does nothing when the DSN is present but empty', async () => {
      // A Helm value or entrypoint default of "" arrives as a blank string,
      // not as an absent key — the shape every deployment ships by default.
      window.__RUNTIME_CONFIG__ = { SENTRY_DSN: '   ' };

      await expect(initErrorTracking()).resolves.toBe(false);
      expect(isErrorTrackingActive()).toBe(false);
      // The chunk contract: nothing was even imported, let alone initialised.
      expect(sentryStub.init).not.toHaveBeenCalled();
    });
  });

  describe('init options', () => {
    it('turns every dataCollection category off explicitly (Sentry 11 defaults are permissive)', async () => {
      window.__RUNTIME_CONFIG__ = { SENTRY_DSN: 'https://key@tracker.example/1' };

      await expect(initErrorTracking()).resolves.toBe(true);

      expect(sentryStub.init).toHaveBeenCalledTimes(1);
      const options = sentryStub.init.mock.calls[0]![0] as Record<string, unknown>;
      // Restated literally rather than imported from the module: the point is
      // that a drift in the block (a category dropped, a value flipped to the
      // SDK's permissive default) fails here. `sendDefaultPii` no longer exists
      // in v11, so the block below is the only thing keeping default-PII off.
      expect(options.dataCollection).toEqual({
        userInfo: false,
        cookies: false,
        httpHeaders: { request: false, response: false },
        httpBodies: [],
        urlQueryParams: false,
        graphQL: { document: false, variables: false },
        genAI: { inputs: false, outputs: false },
        databaseQueryData: false,
        stackFrameVariables: false,
      });
      expect(options).not.toHaveProperty('sendDefaultPii');
    });

    it('wires the scrubbing hooks the PII policy relies on', async () => {
      window.__RUNTIME_CONFIG__ = { SENTRY_DSN: 'https://key@tracker.example/1' };

      await expect(initErrorTracking()).resolves.toBe(true);

      const options = sentryStub.init.mock.calls[0]![0] as {
        beforeSend: (event: Record<string, unknown>) => Record<string, unknown>;
        beforeBreadcrumb: (crumb: Record<string, unknown>) => Record<string, unknown> | null;
      };
      // Driven through the options actually handed to the SDK, not through
      // `scrubEvent` directly: the wiring is what this case certifies.
      const sent = options.beforeSend({ request: { cookies: { session: 'x' }, url: '/plants' } });
      expect((sent.request as Record<string, unknown>).cookies).toBeUndefined();
      expect((sent.request as Record<string, unknown>).url).toBe('/plants');
      expect(options.beforeBreadcrumb({ category: 'ui.input' })).toBeNull();
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
