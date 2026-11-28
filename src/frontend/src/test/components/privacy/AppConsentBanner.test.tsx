import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, fireEvent, act } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '../../helpers';
import { server } from '../../mocks/server';
import {
  CONSENT_STORAGE_KEY,
  readConsent,
  readConsentSnapshot,
  resetConsentStoreForTests,
  setAuthStatus,
  setPendingRevoke,
} from '@/observability/consent';
import { resetConsentSyncForTests } from '@/observability/consentSync';

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

interface ServerState {
  granted: boolean;
  revoked: boolean;
}
let serverState: ServerState;
let failGet: boolean;
let failDelete: boolean;

function consentBody() {
  return [
    {
      purpose: 'browser_error_reports',
      label: 'Send error reports from the browser',
      description: '…',
      legal_basis: 'Art. 6(1)(a) GDPR',
      required: false,
      granted: serverState.granted,
      granted_at: null,
      revoked_at: serverState.revoked ? '2026-11-28T09:00:00Z' : null,
      consent_version: serverState.granted || serverState.revoked ? '1.0' : null,
      purpose_version: '1.0',
    },
  ];
}

function installServer(): void {
  server.use(
    http.get('/api/v1/privacy/consents', () =>
      failGet ? new HttpResponse(null, { status: 503 }) : HttpResponse.json(consentBody()),
    ),
    http.post('/api/v1/privacy/consents', () => {
      serverState = { granted: true, revoked: false };
      return HttpResponse.json(consentBody()[0], { status: 201 });
    }),
    http.delete('/api/v1/privacy/consents/:purpose', () => {
      if (failDelete) return new HttpResponse(null, { status: 503 });
      serverState = { granted: false, revoked: true };
      return HttpResponse.json(consentBody()[0]);
    }),
  );
}

async function renderBanner() {
  const { default: AppConsentBanner } = await import('@/components/privacy/AppConsentBanner');
  return renderWithProviders(<AppConsentBanner />);
}

async function renderSettings() {
  const { default: BrowserConsentSettings } =
    await import('@/components/privacy/BrowserConsentSettings');
  return renderWithProviders(<BrowserConsentSettings />);
}

/** #2159/#3025 — the app-shell mount and the settings section of browser error reports. */
describe('AppConsentBanner / BrowserConsentSettings', () => {
  beforeEach(() => {
    modeMock.isLightMode = false;
    resetConsentSyncForTests();
    resetConsentStoreForTests();
    window.localStorage.clear();
    delete window.__RUNTIME_CONFIG__;
    serverState = { granted: false, revoked: false };
    failGet = false;
    failDelete = false;
    installServer();
  });

  afterEach(() => {
    resetConsentSyncForTests();
    resetConsentStoreForTests();
    window.localStorage.clear();
    delete window.__RUNTIME_CONFIG__;
  });

  it('shows the banner on a first visit when error tracking is configured', async () => {
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
    setAuthStatus({ kind: 'signed_out' });
    await renderBanner();
    // #3023 — the banner is a lazy chunk, so it appears once that chunk has loaded.
    expect(await screen.findByTestId('consent-banner')).toBeInTheDocument();
  });

  it('shows no banner in Light mode (REQ-027 household exemption, CB-001)', async () => {
    modeMock.isLightMode = true;
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN, KAMERPLANTER_MODE: 'light' };
    setAuthStatus({ kind: 'signed_out' });
    await renderBanner();
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  it('shows no banner when no DSN is configured (nothing to consent to)', async () => {
    setAuthStatus({ kind: 'signed_out' });
    await renderBanner();
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();
  });

  it('hides the settings section in Light mode and without a DSN', async () => {
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

  describe('settings (signed in)', () => {
    beforeEach(() => {
      window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
      setAuthStatus({ kind: 'signed_in', account: 'user-a' });
    });

    it('the switch is the account consent and shows only what the server confirmed', async () => {
      await renderSettings();
      const toggle = await screen.findByRole('switch');
      await vi.waitFor(() => expect(readConsentSnapshot().account.kind).toBe('undecided'));
      expect(toggle).not.toBeChecked();
      expect(screen.getByTestId('browser-consent-sending')).toHaveAttribute(
        'data-sending',
        'false',
      );

      fireEvent.click(toggle);

      await vi.waitFor(() => expect(toggle).toBeChecked());
      expect(serverState.granted).toBe(true);
      expect(screen.getByTestId('browser-consent-sending')).toHaveAttribute('data-sending', 'true');
    });

    it('a failed revoke switches off at once and shows the pending revoke with a retry (B-6)', async () => {
      serverState = { granted: true, revoked: false };
      failDelete = true;
      await renderSettings();
      const toggle = await screen.findByRole('switch');
      await vi.waitFor(() => expect(toggle).toBeChecked());

      fireEvent.click(toggle);

      expect(await screen.findByTestId('browser-consent-revoke-pending')).toHaveAttribute(
        'role',
        'alert',
      );
      expect(toggle).not.toBeChecked();
      expect(screen.getByTestId('browser-consent-sending')).toHaveAttribute(
        'data-sending',
        'false',
      );

      failDelete = false;
      fireEvent.click(screen.getByRole('button', { name: /Erneut versuchen|Try again/ }));
      await vi.waitFor(() =>
        expect(screen.queryByTestId('browser-consent-revoke-pending')).not.toBeInTheDocument(),
      );
      expect(serverState.revoked).toBe(true);
    });

    it('shows a failed read with a retry, never as consent (CP-012)', async () => {
      serverState = { granted: true, revoked: false };
      failGet = true;
      await renderSettings();

      expect(await screen.findByTestId('browser-consent-sync-failed')).toBeInTheDocument();
      expect(screen.getByRole('switch')).not.toBeChecked();

      failGet = false;
      fireEvent.click(screen.getByRole('button', { name: /Erneut versuchen|Try again/ }));
      await vi.waitFor(() => expect(screen.getByRole('switch')).toBeChecked());
    });

    it('shows a pending revoke left from an earlier page view', async () => {
      act(() => setPendingRevoke('user-a', true));
      failDelete = true;
      await renderSettings();
      expect(await screen.findByTestId('browser-consent-revoke-pending')).toBeInTheDocument();
    });

    it('a device decline is shown and only a reset on this device lifts it (CP-007)', async () => {
      serverState = { granted: true, revoked: false };
      window.localStorage.setItem(
        CONSENT_STORAGE_KEY,
        JSON.stringify({ necessary: true, browser_error_reports: false, version: '1.0' }),
      );
      await renderSettings();
      await vi.waitFor(() => expect(screen.getByRole('switch')).toBeChecked());
      expect(screen.getByTestId('browser-consent-device')).toHaveTextContent(/abgelehnt|declined/);
      expect(screen.getByTestId('browser-consent-sending')).toHaveAttribute(
        'data-sending',
        'false',
      );

      fireEvent.click(screen.getByTestId('browser-consent-device-reset'));

      expect(readConsent().browser_error_reports).toBeNull();
      expect(screen.getByTestId('browser-consent-sending')).toHaveAttribute('data-sending', 'true');
      expect(serverState.granted).toBe(true);
    });
  });
});
