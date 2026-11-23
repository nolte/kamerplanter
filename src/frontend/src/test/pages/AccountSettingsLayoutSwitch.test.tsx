import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act, cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import { KioskProvider } from '@/kiosk/KioskProvider';

/**
 * F-11 (#2935) follow-up — crossing the `md` breakpoint must not remount the open
 * settings group.
 *
 * The page used to render the phone layout and the desktop layout as two
 * differently shaped trees, so every crossing of the breakpoint unmounted the
 * open group and mounted a fresh one. The group owns its state (F-11): an open
 * device-pairing flow, a half-typed password, an unsaved form were thrown away
 * by a rotated tablet, a resized window — or by the e2e screenshot, which
 * collapses the viewport for a few milliseconds (nightly 2026-11-23: the pairing
 * dialog vanished right after it opened on `full` and `full-tablet`).
 *
 * `matchMedia` is a live stub here: its lists re-read the current width and
 * notify their `change` listeners, which is what `useMediaQuery` subscribes to.
 */

const { modeState } = vi.hoisted(() => ({ modeState: { light: false } }));

vi.mock('@/config/mode', () => ({
  get isLightMode() {
    return modeState.light;
  },
  get isFullMode() {
    return !modeState.light;
  },
  get KAMERPLANTER_MODE() {
    return modeState.light ? 'light' : 'full';
  },
}));

const DESKTOP = 1280;
/** The width the e2e screenshot briefly collapses the viewport to. */
const COLLAPSED = 1;

let viewportWidth = DESKTOP;
type ChangeListener = (event: { matches: boolean; media: string }) => void;
let changeListeners: Array<{ query: string; listener: ChangeListener }> = [];
const originalMatchMedia = window.matchMedia;

function matchesWidth(query: string, width: number): boolean {
  const min = /\(min-width:\s*([\d.]+)px\)/.exec(query);
  const max = /\(max-width:\s*([\d.]+)px\)/.exec(query);
  return (min === null || width >= Number(min[1])) && (max === null || width <= Number(max[1]));
}

function installLiveMatchMedia(): void {
  window.matchMedia = ((query: string) => {
    const list = {
      get matches() {
        return matchesWidth(query, viewportWidth);
      },
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: (_type: string, listener: ChangeListener) => {
        changeListeners.push({ query, listener });
      },
      removeEventListener: (_type: string, listener: ChangeListener) => {
        changeListeners = changeListeners.filter((entry) => entry.listener !== listener);
      },
      dispatchEvent: vi.fn(),
    };
    return list as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}

function resizeTo(width: number): void {
  act(() => {
    viewportWidth = width;
    window.innerWidth = width;
    for (const { query, listener } of [...changeListeners]) {
      listener({ matches: matchesWidth(query, width), media: query });
    }
  });
}

function renderAt(route: string) {
  const prefs = { experience_level: 'expert', locale: 'de', theme: 'light', smart_home_enabled: false };
  server.use(
    http.get('/api/v1/user-preferences', () => HttpResponse.json(prefs)),
    http.get('/api/v1/t/:tenant/user-preferences', () => HttpResponse.json(prefs)),
  );
  const store = createTestStore({
    ...authState(),
    ...tenantState('lead'),
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: 'expert',
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: false,
        module_visibility: {},
      },
      loading: false,
      error: null,
    },
  });
  return renderWithProviders(
    <KioskProvider>
      <AccountSettingsPage />
    </KioskProvider>,
    { store, route },
  );
}

beforeEach(() => {
  i18n.changeLanguage('de');
  modeState.light = false;
  viewportWidth = DESKTOP;
  window.innerWidth = DESKTOP;
  changeListeners = [];
  installLiveMatchMedia();
  Element.prototype.scrollIntoView = function scrollIntoView() {};
  server.use(
    http.get('/api/v1/users/me/providers', () =>
      HttpResponse.json([{ key: 'prov-1', provider: 'local', provider_email: 'tester@example.org' }]),
    ),
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json([])),
    http.get('/api/v1/auth/api-keys', () => HttpResponse.json([])),
  );
});

afterEach(() => {
  cleanup();
  window.matchMedia = originalMatchMedia;
  modeState.light = false;
});

describe('settings page — crossing the md breakpoint', () => {
  it('keeps the open group mounted', async () => {
    renderAt('/settings/security#sessions');
    const panel = await screen.findByTestId('settings-panel-security');
    expect(screen.getByTestId('settings-nav-sidebar')).toBeInTheDocument();

    resizeTo(COLLAPSED);
    // Phone layout: no side navigation, a back arrow — and still the same group element.
    expect(screen.queryByTestId('settings-nav-sidebar')).not.toBeInTheDocument();
    expect(screen.getByTestId('settings-back-button')).toBeInTheDocument();
    expect(screen.getByTestId('settings-panel-security')).toBe(panel);

    resizeTo(DESKTOP);
    expect(screen.getByTestId('settings-nav-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('settings-panel-security')).toBe(panel);
  });

  it('keeps an opened device-pairing flow open', async () => {
    const user = userEvent.setup();
    renderAt('/settings/security#sessions');

    await user.click(await screen.findByTestId('connect-device-button'));
    expect(await screen.findByTestId('connect-device-step-up-dialog')).toBeInTheDocument();

    resizeTo(COLLAPSED);
    resizeTo(DESKTOP);

    // A remount would have reset the group's `connectDeviceOpen` state and closed the flow.
    expect(screen.getByTestId('connect-device-step-up-dialog')).toBeInTheDocument();
  });

  it('stacks the experience toggle when the panel is narrow (tablet)', async () => {
    // 820 px is "desktop" by the md breakpoint (768), but the panel next to the app
    // drawer and the settings navigation is only ~250 px: three side-by-side buttons
    // ran out of the card, which clipped "expert" out of reach (nightly 2026-11-23).
    resizeTo(820);
    renderAt('/settings/display#experience');
    const group = (await screen.findByTestId('experience-toggle-expert')).closest('.MuiToggleButtonGroup-root');
    expect(group).not.toBeNull();
    const ownClasses = Array.from(group!.classList).filter((c) => c.startsWith('css-'));
    const css = Array.from(document.querySelectorAll('style'))
      .map((el) => el.textContent ?? '')
      .join('\n')
      .replace(/\s+/g, ' ');
    const stacked = ownClasses.some((cls) =>
      new RegExp(`@container settings-panel \\(max-width: 559\\.98px\\) ?\\{ ?\\.${cls}\\{[^}]*flex-direction: ?column`).test(css),
    );
    expect(stacked).toBe(true);
  });

  it('still shows the group list on a phone when no group is open', async () => {
    resizeTo(390);
    renderAt('/settings');
    expect(await screen.findByTestId('settings-nav-list')).toBeInTheDocument();
    expect(screen.queryByTestId('settings-back-button')).not.toBeInTheDocument();
  });
});
