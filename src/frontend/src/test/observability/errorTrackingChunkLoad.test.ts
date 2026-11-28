import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

/**
 * #2159 — CI-002: before consent the SDK chunk is not even *fetched*.
 *
 * `errorTracking.test.ts` proves `Sentry.init` is not called; this file counts
 * the chunk load itself. A mock factory runs once per module registry, so every
 * case resets the registry and re-imports the modules under test — the counter
 * then sees exactly the loads that case caused.
 */
const imported = vi.fn();

async function loadModules() {
  vi.resetModules();
  vi.doMock('@sentry/react', () => {
    imported();
    return {
      init: vi.fn(),
      captureException: vi.fn(),
      close: vi.fn(() => Promise.resolve(true)),
      getClient: vi.fn(() => undefined),
      getIsolationScope: vi.fn(() => ({ clearBreadcrumbs: vi.fn() })),
      getCurrentScope: vi.fn(() => ({ clearBreadcrumbs: vi.fn() })),
    };
  });
  const tracking = await import('@/observability/errorTracking');
  const consent = await import('@/observability/consent');
  return { tracking, consent };
}

describe('error-tracking chunk load', () => {
  beforeEach(() => {
    imported.mockClear();
    window.localStorage.removeItem('kamerplanter:consent:v1');
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: 'https://key@tracker.example/1' };
  });

  afterEach(() => {
    window.localStorage.removeItem('kamerplanter:consent:v1');
    delete window.__RUNTIME_CONFIG__;
    vi.doUnmock('@sentry/react');
  });

  it.each([
    ['undecided', null],
    ['declined', false],
  ] as const)('does not load the chunk while consent is %s', async (_label, decision) => {
    window.localStorage.setItem(
      'kamerplanter:consent:v1',
      JSON.stringify({ necessary: true, browser_error_reports: decision, version: '1.0' }),
    );
    const { tracking, consent } = await loadModules();
    // Signed out, so the device decision is the one that counts (UI-NFR-013 §5.4).
    consent.setAuthStatus({ kind: 'signed_out' });

    await expect(tracking.initErrorTracking()).resolves.toBe(false);

    expect(imported).not.toHaveBeenCalled();
    tracking.resetErrorTrackingForTests();
  });

  it('loads the chunk once consent is given (positive control for the counter)', async () => {
    const { tracking, consent } = await loadModules();
    consent.setAuthStatus({ kind: 'signed_out' });
    await tracking.initErrorTracking();
    expect(imported).not.toHaveBeenCalled();

    consent.decideOnDevice(true);
    await vi.waitFor(() => expect(tracking.isErrorTrackingActive()).toBe(true));

    expect(imported).toHaveBeenCalledTimes(1);
    tracking.resetErrorTrackingForTests();
    consent.resetConsentStoreForTests();
  });
});
