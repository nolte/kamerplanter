import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import PublicOnlyRoute from '@/auth/PublicOnlyRoute';
import AppConsentBanner from '@/components/privacy/AppConsentBanner';
import {
  CONSENT_STORAGE_KEY,
  readConsent,
  resetConsentStoreForTests,
} from '@/observability/consent';
import {
  bindConsentToAuth,
  resetConsentAuthBridgeForTests,
} from '@/observability/consentAuthBridge';
import { createTestStore } from '../../helpers';

const DSN = 'https://key@tracker.example/1';

/**
 * UI-NFR-013 v1.4 CW-006 (#3025 F-5) — a decision made without signing in can be
 * taken back without signing in: the link under every public page (mounted by
 * `PublicOnlyRoute`, as in `AppRoutes`) resets the device decision and the banner
 * asks again. The sign-in state reaches the consent store through the bridge of
 * `main.tsx`.
 */
function renderPublicPage() {
  const store = createTestStore({
    auth: {
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      initialized: true,
    },
  } as never);
  const unbind = bindConsentToAuth(store);
  const router = createMemoryRouter(
    [{ element: <PublicOnlyRoute />, children: [{ path: '/login', element: <h1>Login</h1> }] }],
    { initialEntries: ['/login'] },
  );
  const view = render(
    <Provider store={store}>
      <SnackbarProvider>
        <RouterProvider router={router} />
        <AppConsentBanner />
      </SnackbarProvider>
    </Provider>,
  );
  return { ...view, unbind };
}

describe('device consent reset on the public pages (CW-006)', () => {
  let unbind: (() => void) | null = null;

  beforeEach(() => {
    resetConsentAuthBridgeForTests();
    resetConsentStoreForTests();
    window.localStorage.clear();
    window.__RUNTIME_CONFIG__ = { SENTRY_DSN: DSN };
  });

  afterEach(() => {
    unbind?.();
    unbind = null;
    resetConsentStoreForTests();
    window.localStorage.clear();
    delete window.__RUNTIME_CONFIG__;
  });

  it.each([
    ['a grant', true],
    ['a decline', false],
  ])('takes back %s of this browser and lets the banner ask again', async (_label, decision) => {
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, browser_error_reports: decision, version: '1.0' }),
    );
    unbind = renderPublicPage().unbind;
    expect(await screen.findByText('Login')).toBeInTheDocument();
    expect(screen.queryByTestId('consent-banner')).not.toBeInTheDocument();

    const reset = screen.getByTestId('device-consent-reset');
    expect(reset).toHaveAccessibleName(
      /Entscheidung dieses Browsers zu Fehlerberichten ändern|Change this browser's decision on error reports/,
    );
    fireEvent.click(reset);

    expect(readConsent().browser_error_reports).toBeNull();
    // N-d: the link is gone; the banner's heading takes the focus.
    await vi.waitFor(() => expect(screen.getByTestId('consent-banner-heading')).toHaveFocus());
    expect(await screen.findByTestId('consent-banner')).toHaveAttribute(
      'data-consent-form',
      'device',
    );
    expect(screen.queryByTestId('device-consent-reset')).not.toBeInTheDocument();
  });

  it('is not offered while this browser has not decided, or without a DSN', async () => {
    unbind = renderPublicPage().unbind;
    expect(await screen.findByText('Login')).toBeInTheDocument();
    expect(screen.queryByTestId('device-consent-reset')).not.toBeInTheDocument();
    unbind();

    delete window.__RUNTIME_CONFIG__;
    window.localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ necessary: true, browser_error_reports: true, version: '1.0' }),
    );
    resetConsentStoreForTests();
    unbind = renderPublicPage().unbind;
    expect(screen.queryByTestId('device-consent-reset')).not.toBeInTheDocument();
  });
});
