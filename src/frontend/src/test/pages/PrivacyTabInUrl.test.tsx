import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import PrivacySettingsPage from '@/pages/auth/PrivacySettingsPage';
import { authState, createTestStore } from '../helpers';
import { server } from '../mocks/server';
import { saveStepUpResume, storeStepUpReauthError } from '@/utils/stepUpReauth';

/**
 * #3018 (audit N-19, UI-NFR-005 R-001) — the privacy page's tab is part of its URL (`/privacy#export`).
 *
 * The tab lived in component state: a reload or the way back from another page reopened the consents.
 * It now follows the app's tab pattern (`useTabUrl`); `/privacy` without a fragment still opens the
 * consents, and the step-up resume (#1815) still opens the erasure tab — and writes it into the URL.
 */

function renderPrivacyAt(entry: string) {
  const router = createMemoryRouter(
    [
      { path: '/privacy', element: <PrivacySettingsPage /> },
      { path: '/elsewhere', element: <p>elsewhere</p> },
    ],
    { initialEntries: [entry] },
  );
  render(
    <Provider store={createTestStore(authState())}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return router;
}

function selectedTab(): string | null {
  // `hidden`: on a step-up resume the erasure dialog is open, and a modal hides the page behind it.
  const tab = screen.getAllByRole('tab', { hidden: true }).find((el) => el.getAttribute('aria-selected') === 'true');
  return tab?.getAttribute('data-testid') ?? null;
}

describe('PrivacySettingsPage — the tab is restored from the URL (#3018 N-19)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    sessionStorage.clear();
    server.use(
      http.get('/api/v1/privacy/consents', () => HttpResponse.json([])),
      http.get('/api/v1/privacy/restrictions', () => HttpResponse.json([])),
    );
  });
  afterEach(() => {
    cleanup();
  });

  it('opens the tab the fragment names, as a reload or a bookmark does', async () => {
    renderPrivacyAt('/privacy#restrict');
    await waitFor(() => expect(selectedTab()).toBe('privacy-tab-restrict'));
  });

  it('opens the consents on the old URL without a fragment', async () => {
    renderPrivacyAt('/privacy');
    await waitFor(() => expect(selectedTab()).toBe('privacy-tab-consents'));
  });

  it('writes the chosen tab into the URL and restores it on Back and Forward', async () => {
    const user = userEvent.setup();
    const router = renderPrivacyAt('/privacy');
    await user.click(await screen.findByTestId('privacy-tab-export'));
    expect(router.state.location.hash).toBe('#export');

    await act(() => router.navigate('/elsewhere'));
    await act(() => router.navigate(-1));
    expect(router.state.location.hash).toBe('#export');
    await waitFor(() => expect(selectedTab()).toBe('privacy-tab-export'));

    await act(() => router.navigate(1));
    expect(screen.getByText('elsewhere')).toBeInTheDocument();
    await act(() => router.navigate(-1));
    await waitFor(() => expect(selectedTab()).toBe('privacy-tab-export'));
  });

  it('opens the erasure tab on a step-up resume and puts it into the URL', async () => {
    storeStepUpReauthError('step_up_stale', 'account_erasure');
    saveStepUpResume({ surface: 'privacy-erasure', action: 'account_erasure', returnPath: '/privacy' });
    server.use(
      http.get('/api/v1/users/me/providers', () =>
        HttpResponse.json([{ key: 'prov-g', provider: 'google', provider_email: 'tester@example.org' }]),
      ),
    );
    const router = renderPrivacyAt('/privacy');
    expect(selectedTab()).toBe('privacy-tab-erasure');
    expect(await screen.findByTestId('privacy-erasure-dialog')).toBeInTheDocument();
    await waitFor(() => expect(router.state.location.hash).toBe('#erasure'));
    expect(selectedTab()).toBe('privacy-tab-erasure');
  });
});
