import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { ThemeContextProvider } from '@/theme';
import KioskLayout from '@/layouts/KioskLayout';
import { KioskProvider } from '@/kiosk/KioskProvider';
import { createTestStore } from '@/test/helpers';

vi.mock('@/config/mode', () => ({
  isLightMode: true,
  isFullMode: false,
  KAMERPLANTER_MODE: 'light',
}));

function stubLocalStorage() {
  const store = new Map<string, string>();
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: false } as MediaQueryList));
  return store;
}

function renderLayout() {
  const router = createMemoryRouter(
    [
      {
        path: '/kiosk',
        element: <KioskLayout />,
        children: [{ index: true, element: <div data-testid="kiosk-start-marker" /> }],
      },
      { path: '/dashboard', element: <div data-testid="dashboard-route" /> },
    ],
    { initialEntries: ['/kiosk'] },
  );
  return render(
    <Provider store={createTestStore()}>
      <KioskProvider>
        <ThemeContextProvider>
          <RouterProvider router={router} />
        </ThemeContextProvider>
      </KioskProvider>
    </Provider>,
  );
}

describe('KioskLayout (UI-NFR-019)', () => {
  beforeEach(() => stubLocalStorage());
  afterEach(() => vi.unstubAllGlobals());

  it('shows the permanent kiosk badge (R-003)', async () => {
    await act(async () => {
      renderLayout();
    });
    expect(screen.getByTestId('kiosk-badge')).toBeInTheDocument();
    expect(screen.getByTestId('kiosk-start-marker')).toBeInTheDocument();
  });

  it('persists kiosk mode on entry via the /kiosk URL (R-001, R-002)', async () => {
    const store = stubLocalStorage();
    await act(async () => {
      renderLayout();
    });
    // enableKiosk on mount writes the preference to localStorage.
    const persisted = JSON.parse(store.get('kp-kiosk-preference')!);
    expect(persisted.kiosk_enabled).toBe(true);
  });

  it('exits kiosk mode and routes to the dashboard (R-004)', async () => {
    const user = userEvent.setup();
    await act(async () => {
      renderLayout();
    });
    await act(async () => {
      await user.click(screen.getByTestId('kiosk-exit-button'));
    });
    expect(screen.getByTestId('dashboard-route')).toBeInTheDocument();
  });
});
