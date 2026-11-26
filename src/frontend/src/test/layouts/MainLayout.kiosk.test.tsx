import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import MainLayout from '@/layouts/MainLayout';
import { KioskProvider, useKiosk } from '@/kiosk/KioskProvider';
import { KIOSK_IDLE_MS, KIOSK_WARNING_MS } from '@/kiosk/useKioskTimeout';
import { useReportUnsavedInput } from '@/kiosk/kioskSession';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { createTestStore } from '@/test/helpers';
import { server } from '@/test/mocks/server';

// Light mode keeps KioskProvider from attempting a server preference sync,
// mirroring MainLayout.light.test.tsx.
vi.mock('@/config/mode', () => ({
  isLightMode: true,
  isFullMode: false,
  KAMERPLANTER_MODE: 'light',
}));

const KIOSK_ON = { 'kp-kiosk-preference': JSON.stringify({ kiosk_enabled: true, high_contrast: true }) };

function stubLocalStorage(seed?: Record<string, string>) {
  const store = new Map<string, string>(Object.entries(seed ?? {}));
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
}

/**
 * `/giessprotokoll` is where the "Bewässerung erfassen" tile leads: a regular MainLayout route
 * with a breadcrumb trail of its own, so its absence in kiosk mode is a measurement, not an
 * empty page.
 */
function renderTileDestination(initialEntries: string[] = ['/giessprotokoll']) {
  const router = createMemoryRouter(
    [
      {
        element: <MainLayout />,
        children: [
          { path: '/giessprotokoll', element: <h1 data-testid="watering-page">Gießprotokoll</h1> },
          { path: '/dashboard', element: <h1 data-testid="dashboard-page">Dashboard</h1> },
          { path: '/guarded-form', element: <GuardedFormPage /> },
          { path: '/dialog-form', element: <DialogFormPage /> },
          { path: '/settings', element: <KioskSwitchPage /> },
        ],
      },
      { path: '/kiosk', element: <div data-testid="kiosk-start-marker" /> },
    ],
    { initialEntries },
  );
  render(
    <Provider store={createTestStore()}>
      <KioskProvider>
        <ThemeContextProvider>
          <RouterProvider router={router} />
        </ThemeContextProvider>
      </KioskProvider>
    </Provider>,
  );
  return router;
}

/** A page form guarded by `useBlocker` (UnsavedChangesGuard) with unsaved input. */
function GuardedFormPage() {
  return (
    <>
      <h1 data-testid="guarded-form-page">Formular</h1>
      <UnsavedChangesGuard dirty />
    </>
  );
}

/** A dialog form (FormDialog reports the same way) with unsaved input and no navigation guard. */
function DialogFormPage() {
  useReportUnsavedInput(true);
  return <h1 data-testid="dialog-form-page">Dialog</h1>;
}

/** Stands in for the settings switch that turns kiosk mode on. */
function KioskSwitchPage() {
  const { enableKiosk } = useKiosk();
  return (
    <button type="button" onClick={enableKiosk}>
      Kiosk an
    </button>
  );
}

async function renderWithFakeTimers(path: string) {
  vi.useFakeTimers();
  let router!: ReturnType<typeof renderTileDestination>;
  await act(async () => {
    router = renderTileDestination([path]);
    await vi.advanceTimersByTimeAsync(0);
  });
  return router;
}

const breadcrumbNav = () => screen.queryByRole('navigation', { name: 'Brotkrumen-Navigation' });

/**
 * #3025 N-37 (UI-NFR-019 R-003, R-017, R-018, R-021, R-033..R-036) — a kiosk session stays a
 * kiosk session. The pages the kiosk tiles lead to are MainLayout routes; while kiosk mode is on,
 * MainLayout renders them into the kiosk shell: no hamburger, no sidebar, no breadcrumbs, a Back
 * button instead, and the inactivity timeout keeps running and returns to the kiosk start.
 */
describe('MainLayout in kiosk mode (#3025 N-37)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/t/:tenant/notifications/count', () => HttpResponse.json({ unread_count: 0 })),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders the standard shell with hamburger and breadcrumbs outside kiosk mode', async () => {
    stubLocalStorage();
    renderTileDestination();

    expect(await screen.findByTestId('watering-page')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar-toggle')).toBeInTheDocument();
    expect(breadcrumbNav()).toBeInTheDocument();
    expect(screen.queryByTestId('kiosk-shell')).toBeNull();
    expect(screen.queryByTestId('kiosk-badge')).toBeNull();
  });

  it('renders a tile destination in the kiosk shell — no hamburger, sidebar or breadcrumbs', async () => {
    stubLocalStorage(KIOSK_ON);
    renderTileDestination();

    expect(await screen.findByTestId('kiosk-shell')).toBeInTheDocument();
    expect(screen.getByTestId('watering-page')).toBeInTheDocument();
    expect(screen.queryByTestId('sidebar-toggle')).toBeNull();
    expect(screen.queryByTestId('sidebar')).toBeNull();
    expect(breadcrumbNav()).toBeNull();
    // R-003, R-017, R-018 — badge, Back in place of the breadcrumbs, Home.
    expect(screen.getByTestId('kiosk-badge')).toHaveTextContent('Kiosk');
    expect(screen.getByRole('button', { name: 'Zurück' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument();
    // W-09 — the kiosk shell has a skip link to its main landmark as well.
    expect(screen.getByRole('link', { name: 'Zum Inhalt springen' })).toHaveAttribute('href', '#main-content');
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content');
  });

  it('keeps the inactivity timeout running on a tile destination and returns to the kiosk start', async () => {
    stubLocalStorage(KIOSK_ON);
    vi.useFakeTimers();
    let router!: ReturnType<typeof renderTileDestination>;
    await act(async () => {
      router = renderTileDestination();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(screen.getByTestId('kiosk-shell')).toBeInTheDocument();
    expect(screen.queryByTestId('kiosk-timeout-overlay')).toBeNull();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_IDLE_MS);
    });
    expect(screen.getByTestId('kiosk-timeout-overlay')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_WARNING_MS);
    });
    expect(router.state.location.pathname).toBe('/kiosk');
    expect(screen.getByTestId('kiosk-start-marker')).toBeInTheDocument();
  });

  it('warns that unsaved dialog input will be discarded, then returns to the start (R-035, R-038)', async () => {
    stubLocalStorage(KIOSK_ON);
    const router = await renderWithFakeTimers('/dialog-form');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_IDLE_MS);
    });
    expect(screen.getByTestId('kiosk-timeout-unsaved')).toHaveTextContent(
      'Ungespeicherte Eingaben werden dann verworfen.',
    );
    expect(screen.getByRole('alertdialog')).toHaveAccessibleDescription(/verworfen/);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_WARNING_MS);
    });
    expect(router.state.location.pathname).toBe('/kiosk');
  });

  it('says nothing about discarding when there is no unsaved input', async () => {
    stubLocalStorage(KIOSK_ON);
    await renderWithFakeTimers('/giessprotokoll');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_IDLE_MS);
    });
    expect(screen.getByTestId('kiosk-timeout-overlay')).toBeInTheDocument();
    expect(screen.queryByTestId('kiosk-timeout-unsaved')).toBeNull();
  });

  it('returns to the start past an unsaved-changes guard, leaving no prompt behind (R-035)', async () => {
    stubLocalStorage(KIOSK_ON);
    const router = await renderWithFakeTimers('/guarded-form');
    expect(screen.getByTestId('guarded-form-page')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_IDLE_MS);
    });
    expect(screen.getByTestId('kiosk-timeout-unsaved')).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(KIOSK_WARNING_MS);
    });
    expect(router.state.location.pathname).toBe('/kiosk');
    expect(screen.queryByTestId('guarded-form-page')).toBeNull();
    expect(screen.queryByTestId('confirm-dialog')).toBeNull();
  });

  it('still asks before a navigation of the user leaves the guarded form', async () => {
    stubLocalStorage(KIOSK_ON);
    const user = userEvent.setup();
    const router = renderTileDestination(['/guarded-form']);

    await user.click(await screen.findByRole('button', { name: 'Start' }));
    expect(router.state.location.pathname).toBe('/guarded-form');
    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
  });

  it('renders the kiosk app bar sticky, so Back and Home stay visible on long pages (R-018)', async () => {
    stubLocalStorage(KIOSK_ON);
    renderTileDestination();
    expect(await screen.findByTestId('kiosk-app-bar')).toHaveClass('MuiAppBar-positionSticky');
  });

  it('moves the focus into the kiosk shell when switching kiosk mode on unmounts the switch', async () => {
    stubLocalStorage();
    const user = userEvent.setup();
    renderTileDestination(['/settings']);

    await user.click(await screen.findByRole('button', { name: 'Kiosk an' }));
    expect(await screen.findByTestId('kiosk-shell')).toBeInTheDocument();
    await vi.waitFor(() => expect(screen.getByRole('main')).toHaveFocus());
  });

  it('goes back in the history with the Back button (R-017)', async () => {
    stubLocalStorage(KIOSK_ON);
    const user = userEvent.setup();
    const router = renderTileDestination(['/dashboard']);

    await act(async () => {
      await router.navigate('/giessprotokoll');
    });
    await user.click(await screen.findByRole('button', { name: 'Zurück' }));
    expect(router.state.location.pathname).toBe('/dashboard');
  });

  it('sends Back to the kiosk start when the page is the first of the session (R-017)', async () => {
    stubLocalStorage(KIOSK_ON);
    const user = userEvent.setup();
    const router = renderTileDestination();

    await user.click(await screen.findByRole('button', { name: 'Zurück' }));
    expect(router.state.location.pathname).toBe('/kiosk');
  });

  it('switches back to the standard shell without a reload when kiosk mode is left (R-004)', async () => {
    stubLocalStorage(KIOSK_ON);
    const user = userEvent.setup();
    const router = renderTileDestination();

    // Leaving is held (operator decision 2026-11-27); the keyboard path leaves directly.
    (await screen.findByTestId('kiosk-exit-button')).focus();
    await user.keyboard('{Enter}');
    expect(router.state.location.pathname).toBe('/dashboard');
    expect(await screen.findByTestId('sidebar-toggle')).toBeInTheDocument();
    expect(screen.queryByTestId('kiosk-shell')).toBeNull();
  });
});
