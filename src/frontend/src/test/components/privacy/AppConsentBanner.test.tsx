import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '../../helpers';
import { CONSENT_STORAGE_KEY, resetConsentStoreForTests } from '@/observability/consent';

/**
 * `isLightMode` is a module constant resolved at import time, so each case
 * re-imports the components under a fresh mock of `@/config/mode`.
 */
const modeMock = vi.hoisted(() => ({ isLightMode: false }));
vi.mock('@/config/mode', () => ({
  get isLightMode() {
    return modeMock.isLightMode;
  },
  get isFullMode() {
    return !modeMock.isLightMode;
  },
  get KAMERPLANTER_MODE() {
    return modeMock.isLightMode ? 'light' : 'full';
  },
}));

const DSN = 'https://key@tracker.example/1';

async function renderBanner() {
  const { default: AppConsentBanner } = await import('@/components/privacy/AppConsentBanner');
  return renderWithProviders(<AppConsentBanner />);
}

async function renderSettings() {
  const { default: BrowserConsentSettings } =
    await import('@/components/privacy/BrowserConsentSettings');
  return renderWithProviders(<BrowserConsentSettings />);
}

/** #2159 — the app-shell mount: Light mode and DSN-less deployments ask nothing. */
describe('AppConsentBanner / BrowserConsentSettings', () => {
  beforeEach(() => {
    modeMock.isLightMode = false;
    resetConsentStoreForTests();
    window.localStorage.removeItem(CONSENT_STORAGE_KEY);
    delete window.__RUNTIME_CONFIG__;
  });

  afterEach(() => {
    resetConsentStoreForTests();
    window.localStorage.removeItem(CONSENT_STORAGE_KEY);
    delete window.__RUNTIME_CONFIG__;
  });

  it('shows the banner on a first visit when error tracking is configured', async () => {
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
    await renderBanner();
    expect(screen.getByTestId('consent-banner')).toBeInTheDocument();
  });

  it('shows no banner in Light mode (REQ-027 household exemption, CB-001)', async () => {
    modeMock.isLightMode = true;
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN, KAMERPLANTER_MODE: 'light' };
    await renderBanner();
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  it('shows no banner when no DSN is configured (nothing to consent to)', async () => {
    await renderBanner();
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  it('offers the revoke switch in the privacy settings and writes the store', async () => {
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, error_tracking: true, external_services: false }),
    );
    await renderSettings();

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeChecked();
    expect(toggle).toHaveAccessibleDescription(/diesen Browser|this browser/);
    fireEvent.click(toggle);

    expect(toggle).not.toBeChecked();
    const stored = JSON.parse(window.localStorage.getItem(CONSENT_STORAGE_KEY)!);
    expect(stored.error_tracking).toBe(false);
    expect(stored.external_services).toBe(false);
  });

  it('hides the revoke switch in Light mode and without a DSN', async () => {
    modeMock.isLightMode = true;
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
    const { unmount } = await renderSettings();
    expect(screen.queryByTestId('browser-consent-settings')).not.toBeInTheDocument();
    unmount();

    modeMock.isLightMode = false;
    delete window.__RUNTIME_CONFIG__;
    await renderSettings();
    expect(screen.queryByTestId('browser-consent-settings')).not.toBeInTheDocument();
  });
});
