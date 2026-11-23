import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { resolveVisibleSettingsGroups, type SettingsGates } from '@/config/settingsGroups';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import { KioskProvider } from '@/kiosk/KioskProvider';

/**
 * F-11 (#2935) — the grouped settings page, rendered.
 *
 * acceptance-1: desktop shows every group in a side navigation (no tab bar to
 * scroll); a phone shows the group list, and a tap opens the group as a detail
 * view with a back arrow.
 * acceptance-2: every section the group table lists is rendered exactly once,
 * in its group, in both modes.
 * acceptance-3: the navigation lists exactly the visible groups across the gate
 * matrix; Installation is set apart.
 * acceptance-4: `/settings/<group>#<section>` routing, unknown group → 404,
 * invisible group → first visible group, unknown section → top of the group.
 *
 * `@/config/mode` is mocked with getters over a mutable holder so one suite can
 * render both modes (the pattern of `ConnectDeviceDialog.test.tsx`).
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

/** Width-driven `matchMedia` (see `MainLayout.responsive.test.tsx`): md = 900px. */
function stubViewportWidth(width: number): void {
  window.innerWidth = width;
  window.matchMedia = ((query: string) => {
    const min = /\(min-width:\s*([\d.]+)px\)/.exec(query);
    const max = /\(max-width:\s*([\d.]+)px\)/.exec(query);
    const matches = (min === null || width >= Number(min[1])) && (max === null || width <= Number(max[1]));
    return {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}

const DESKTOP = 1280;
const PHONE = 390;

interface Options {
  light?: boolean;
  smartHome?: boolean;
  platformAdmin?: boolean;
}

function storeFor({ smartHome = true, platformAdmin = true }: Options) {
  return createTestStore({
    ...authState({ platformAdmin }),
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
        smart_home_enabled: smartHome,
        module_visibility: {},
      },
      loading: false,
      error: null,
    },
  });
}

function renderAt(route: string, options: Options = {}) {
  modeState.light = options.light ?? false;
  const prefs = { experience_level: 'expert', locale: 'de', theme: 'light', smart_home_enabled: options.smartHome ?? true };
  // The page re-reads the preferences on mount; answered so the smart-home gate stays what the case says.
  server.use(
    http.get('/api/v1/user-preferences', () => HttpResponse.json(prefs)),
    http.get('/api/v1/t/:tenant/user-preferences', () => HttpResponse.json(prefs)),
  );
  // The kiosk section reads the app-wide KioskProvider, as it does under App.tsx.
  return renderWithProviders(
    <KioskProvider>
      <AccountSettingsPage />
    </KioskProvider>,
    { store: storeFor(options), route },
  );
}

function gatesFor({ light = false, smartHome = true, platformAdmin = true }: Options): SettingsGates {
  return { lightMode: light, smartHomeEnabled: smartHome, canManageInstanceSettings: light || platformAdmin };
}

/** The `settings-section-<key>` ids rendered inside the open group's panel. */
function renderedSections(panel: HTMLElement): string[] {
  return Array.from(panel.querySelectorAll('[data-testid^="settings-section-"]')).map((el) =>
    (el.getAttribute('data-testid') ?? '').replace('settings-section-', ''),
  );
}

let scrolledTo: string[] = [];

beforeEach(() => {
  i18n.changeLanguage('de');
  scrolledTo = [];
  // jsdom implements no scrolling; record which element the page asked to scroll to.
  Element.prototype.scrollIntoView = function scrollIntoView(this: Element) {
    scrolledTo.push(this.id);
  };
  stubViewportWidth(DESKTOP);
  server.use(
    http.get('/api/v1/users/me/providers', () => HttpResponse.json([])),
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json([])),
    http.get('/api/v1/auth/api-keys', () => HttpResponse.json([])),
    http.get('/api/v1/admin/settings', () =>
      HttpResponse.json({
        home_assistant: {
          ha_url: '',
          ha_access_token_masked: '',
          ha_timeout: 10,
          source_ha_url: 'default',
          source_ha_access_token: 'default',
          source_ha_timeout: 'default',
        },
        plant_identification: { plantnet_api_key_masked: '', source_plantnet_api_key: 'none' },
      }),
    ),
  );
});

afterEach(() => {
  cleanup();
  modeState.light = false;
});

describe('settings layout — desktop (acceptance-1)', () => {
  it('lists every group in a side navigation instead of a scrolling tab bar', async () => {
    renderAt('/settings');

    const nav = await screen.findByTestId('settings-nav-sidebar');
    for (const group of ['account', 'display', 'notifications', 'security', 'integrations', 'installation']) {
      expect(within(nav).getByTestId(`settings-group-${group}`)).toBeInTheDocument();
    }
    // No tab bar is left that could need horizontal scrolling.
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument();
    expect(screen.queryAllByRole('tab')).toHaveLength(0);
    // `/settings` opens the first group next to the navigation.
    expect(screen.getByTestId('settings-group-panel-account')).toBeInTheDocument();
    expect(within(nav).getByTestId('settings-group-account')).toHaveClass('Mui-selected');
    expect(screen.queryByTestId('settings-back-button')).not.toBeInTheDocument();
  });

  it('opens a group from the navigation and expands it to its sections', async () => {
    const user = userEvent.setup();
    const { router } = renderAt('/settings');

    await user.click(await screen.findByTestId('settings-group-display'));

    expect(router.state.location.pathname).toBe('/settings/display');
    expect(await screen.findByTestId('settings-group-panel-display')).toBeInTheDocument();
    const sections = screen.getByTestId('settings-nav-sections-display');
    expect(within(sections).getByTestId('settings-nav-section-dashboard')).toHaveAttribute(
      'href',
      '/settings/display#dashboard',
    );
    // Keyboard focus follows to the group heading (UI-NFR-002).
    await waitFor(() => expect(screen.getByTestId('settings-group-title')).toHaveFocus());
  });

  it('sets the operator group apart below a divider and a heading', async () => {
    renderAt('/settings');
    const nav = await screen.findByTestId('settings-nav-sidebar');
    const heading = within(nav).getByTestId('settings-nav-operator-heading');
    const items = Array.from(nav.querySelectorAll('[data-testid^="settings-group-"], [data-testid="settings-nav-operator-heading"]'));
    // The heading sits right before Installation, after every personal group.
    expect(items.indexOf(heading)).toBe(items.length - 2);
    expect(items[items.length - 1]).toHaveAttribute('data-testid', 'settings-group-installation');
  });
});

describe('settings layout — phone (acceptance-1)', () => {
  beforeEach(() => stubViewportWidth(PHONE));

  it('shows the group list, and a tap opens the group with a back arrow', async () => {
    const user = userEvent.setup();
    const { router } = renderAt('/settings');

    const list = await screen.findByTestId('settings-nav-list');
    expect(screen.queryByTestId('settings-nav-sidebar')).not.toBeInTheDocument();
    expect(screen.queryByTestId(/^settings-group-panel-/)).not.toBeInTheDocument();

    await user.click(within(list).getByTestId('settings-group-security'));

    expect(router.state.location.pathname).toBe('/settings/security');
    expect(await screen.findByTestId('settings-group-panel-security')).toBeInTheDocument();
    expect(screen.queryByTestId('settings-nav-list')).not.toBeInTheDocument();

    const back = screen.getByTestId('settings-back-button');
    expect(back).toHaveAccessibleName('Zurück zur Übersicht der Einstellungen');
    await user.click(back);

    expect(router.state.location.pathname).toBe('/settings');
    expect(await screen.findByTestId('settings-nav-list')).toBeInTheDocument();
  });

  it('opens a section link as the group detail scrolled to the section', async () => {
    renderAt('/settings/display#dashboard');

    expect(await screen.findByTestId('settings-group-panel-display')).toBeInTheDocument();
    expect(screen.getByTestId('settings-back-button')).toBeInTheDocument();
    await waitFor(() => expect(scrolledTo).toContain('settings-section-dashboard'));
  });
});

describe('settings inventory — rendered (acceptance-2)', () => {
  it.each([
    ['full', false],
    ['light', true],
  ] as const)('renders every visible section exactly once, in its group (%s mode)', async (_mode, light) => {
    const options: Options = { light, smartHome: true, platformAdmin: true };
    const seen: string[] = [];
    for (const group of resolveVisibleSettingsGroups(gatesFor(options))) {
      renderAt(`/settings/${group.key}`, options);
      const panel = await screen.findByTestId(`settings-group-panel-${group.key}`);
      const rendered = renderedSections(panel);
      expect(rendered, group.key).toEqual(group.sections.map((s) => s.key));
      seen.push(...rendered);
      cleanup();
    }
    expect(new Set(seen).size).toBe(seen.length);
    expect(seen).toContain('dashboard');
  });
});

describe('settings navigation — gate matrix (acceptance-3)', () => {
  const MATRIX: Options[] = [
    { light: false, smartHome: false, platformAdmin: false },
    { light: false, smartHome: true, platformAdmin: false },
    { light: false, smartHome: false, platformAdmin: true },
    { light: false, smartHome: true, platformAdmin: true },
    { light: true, smartHome: false, platformAdmin: false },
    { light: true, smartHome: true, platformAdmin: false },
  ];

  it.each(MATRIX)('lists exactly the visible groups (%o)', async (options) => {
    renderAt('/settings', options);
    const nav = await screen.findByTestId('settings-nav-sidebar');
    const listed = Array.from(nav.querySelectorAll('[data-testid^="settings-group-"]')).map((el) =>
      (el.getAttribute('data-testid') ?? '').replace('settings-group-', ''),
    );
    expect(listed).toEqual(resolveVisibleSettingsGroups(gatesFor(options)).map((g) => g.key));
    const operator = options.light || options.platformAdmin;
    expect(listed.includes('installation')).toBe(operator);
    expect(within(nav).queryByTestId('settings-nav-operator-heading') !== null).toBe(operator);
  });

  it('renders the smart-home-gated sections only with smart home on', async () => {
    renderAt('/settings/integrations', { smartHome: false });
    const panel = await screen.findByTestId('settings-group-panel-integrations');
    expect(renderedSections(panel)).toEqual(['ha']);
  });
});

describe('settings routing (acceptance-4)', () => {
  it('opens group and section from /settings/<group>#<section>', async () => {
    renderAt('/settings/security#apikeys');

    expect(await screen.findByTestId('settings-group-panel-security')).toBeInTheDocument();
    await waitFor(() => expect(scrolledTo).toContain('settings-section-apikeys'));
    expect(screen.getByTestId('settings-nav-section-apikeys')).toHaveClass('Mui-selected');
  });

  it('shows the 404 page for an unknown group', async () => {
    renderAt('/settings/platform');

    expect(await screen.findByTestId('not-found-page')).toBeInTheDocument();
    expect(screen.queryByTestId('account-settings-page')).not.toBeInTheDocument();
  });

  it('shows the first visible group for a known group the user does not see', async () => {
    const { router } = renderAt('/settings/installation#storage', { platformAdmin: false });

    expect(await screen.findByTestId('settings-group-panel-account')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/settings/account');
    expect(screen.queryByTestId('settings-section-storage')).not.toBeInTheDocument();
  });

  it('waits for the profile before deciding a platform admin may not see a group', async () => {
    // `user` not loaded yet: the deep link must not be sent away on a guess.
    modeState.light = false;
    const store = createTestStore({ ...tenantState('lead') });
    const { router } = renderWithProviders(<AccountSettingsPage />, { store, route: '/settings/installation' });

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(router.state.location.pathname).toBe('/settings/installation');
    expect(screen.queryByTestId(/^settings-group-panel-/)).not.toBeInTheDocument();
  });

  it('shows the top of the group for an unknown section', async () => {
    renderAt('/settings/display#no-such-section');

    expect(await screen.findByTestId('settings-group-panel-display')).toBeInTheDocument();
    await waitFor(() => expect(scrolledTo).toContain('settings-group-heading-display'));
    expect(scrolledTo.some((id) => id.startsWith('settings-section-'))).toBe(false);
  });

  it('lands an old /settings#<tab> bookmark on the first visible group (no mapping, Q5)', async () => {
    const { router } = renderAt('/settings#ha');

    expect(await screen.findByTestId('settings-group-panel-account')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/settings');
  });
});
