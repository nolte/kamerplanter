import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { ThemeContextProvider } from '@/theme';
import KioskSettingsTab from '@/pages/auth/KioskSettingsTab';
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
}

function renderTab() {
  const router = createMemoryRouter(
    [
      { path: '/settings', element: <KioskSettingsTab /> },
      { path: '/kiosk', element: <div data-testid="kiosk-route" /> },
    ],
    { initialEntries: ['/settings'] },
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

describe('KioskSettingsTab (UI-NFR-019)', () => {
  beforeEach(() => stubLocalStorage());
  afterEach(() => vi.unstubAllGlobals());

  it('renders the kiosk and high-contrast toggles (R-001, R-045)', () => {
    renderTab();
    expect(screen.getByTestId('kiosk-mode-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('high-contrast-toggle')).toBeInTheDocument();
  });

  it('turning the kiosk toggle on also checks it (persisted state)', async () => {
    const user = userEvent.setup();
    renderTab();
    const toggle = screen.getByTestId('kiosk-mode-toggle').querySelector('input')!;
    expect(toggle).not.toBeChecked();

    await act(async () => {
      await user.click(toggle);
    });
    expect(toggle).toBeChecked();
  });

  it('opens the kiosk start page via the open button (R-001)', async () => {
    const user = userEvent.setup();
    renderTab();
    await act(async () => {
      await user.click(screen.getByTestId('kiosk-open-button'));
    });
    expect(screen.getByTestId('kiosk-route')).toBeInTheDocument();
  });

  it('toggles high-contrast independently of kiosk (R-045)', async () => {
    const user = userEvent.setup();
    renderTab();
    const hc = screen.getByTestId('high-contrast-toggle').querySelector('input')!;
    const kiosk = screen.getByTestId('kiosk-mode-toggle').querySelector('input')!;

    await act(async () => {
      await user.click(hc);
    });
    expect(hc).toBeChecked();
    expect(kiosk).not.toBeChecked();
  });
});
