/**
 * "My position" on the field map (REQ-053 GP-UX-026): the REQ-002 opt-in switch, the dot with its accuracy
 * circle following the device, the hints (no GPS, permission denied, far away, insecure context) and that the
 * position never leaves the component - no storage, no IndexedDB, no request, no console line (SR-019).
 */
import { act, cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setActiveTenantSlug } from '@/api/client';
import { planResponse } from '@/test/gardenPlanFixtures';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { normalizePlan } from '../model/planModel';
import { EARTH_RADIUS_M, type GeoPoint } from '../model/ownPosition';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import FieldMap from './FieldMap';

const SITE: GeoPoint = { latitude: 52.52, longitude: 13.405 };
const METRES_PER_DEG = (EARTH_RADIUS_M * Math.PI) / 180;

/** The device `northM` north and `eastM` east of the site, with the digits a leak would carry. */
function near(northM: number, eastM: number): GeoPoint {
  const latitude = SITE.latitude + northM / METRES_PER_DEG;
  return {
    latitude,
    longitude: SITE.longitude + eastM / (METRES_PER_DEG * Math.cos((((SITE.latitude + latitude) / 2) * Math.PI) / 180)),
  };
}

const PLAN = normalizePlan(
  planResponse({
    plan: {
      boundary: { kind: 'rect', origin: [0, 0], width_m: 20, length_m: 10, rotation_deg: 0 },
      north_angle_deg: 0,
      default_grid_m: 0.1,
      adjacency_factor: 1.5,
      plan_revision: 1,
    },
    garden_objects: [],
  }),
);

const originalGeolocation = Object.getOwnPropertyDescriptor(navigator, 'geolocation');
const originalSecureContext = Object.getOwnPropertyDescriptor(window, 'isSecureContext');

interface FakeGeolocation {
  watchPosition: ReturnType<typeof vi.fn>;
  clearWatch: ReturnType<typeof vi.fn>;
  getCurrentPosition: ReturnType<typeof vi.fn>;
  /** Hand the open watch a fix. */
  move: (point: GeoPoint, accuracyM?: number) => void;
  /** Hand the open watch an error (1 denied, 2 unavailable, 3 timeout). */
  fail: (code: number) => void;
}

function installGeolocation(): FakeGeolocation {
  let success: PositionCallback | null = null;
  let failure: PositionErrorCallback | null = null;
  const fake: FakeGeolocation = {
    watchPosition: vi.fn((onSuccess: PositionCallback, onError: PositionErrorCallback) => {
      success = onSuccess;
      failure = onError;
      return 7;
    }),
    clearWatch: vi.fn(() => {
      success = null;
      failure = null;
    }),
    getCurrentPosition: vi.fn(),
    move: (point, accuracyM = 5) =>
      act(() => success?.({ coords: { ...point, accuracy: accuracyM } } as GeolocationPosition)),
    fail: (code) => act(() => failure?.({ code } as GeolocationPositionError)),
  };
  Object.defineProperty(navigator, 'geolocation', { value: fake, configurable: true });
  return fake;
}

function setSecureContext(value: boolean) {
  Object.defineProperty(window, 'isSecureContext', { value, configurable: true });
}

function setVisibility(state: 'visible' | 'hidden') {
  Object.defineProperty(document, 'visibilityState', { value: state, configurable: true });
  act(() => {
    document.dispatchEvent(new Event('visibilitychange'));
  });
}

let requests: { url: string; body: string }[] = [];

function siteBackend(gps: [number, number] | null) {
  server.use(
    http.get('/api/v1/t/:tenant/sites/:key', ({ params }) =>
      HttpResponse.json({ key: params.key, name: 'Vegetable garden', type: 'outdoor', gps_coordinates: gps }),
    ),
  );
}

/** Field mode holds the switch; this harness does the same with plain state. */
const BED_KEYS: ReadonlySet<string> = new Set(['loc_a', 'loc_b']);

function Harness({ initiallyOn = false }: { initiallyOn?: boolean }) {
  const [on, setOn] = useState(initiallyOn);
  return (
    <FieldMap
      plan={PLAN}
      renderer={renderer}
      labels={TEST_LABELS}
      bedKeys={BED_KEYS}
      selectedBedKey={null}
      initialView={null}
      onViewChange={() => undefined}
      onSelectBed={() => undefined}
      ownPositionOn={on}
      onOwnPositionChange={setOn}
    />
  );
}

let renderer: SvgPlanRenderer;

function switchOn() {
  fireEvent.click(screen.getByTestId('field-mode-position-switch'));
}

beforeEach(() => {
  renderer = new SvgPlanRenderer();
  setSecureContext(true);
  setVisibility('visible');
  setActiveTenantSlug('garden');
  requests = [];
  server.events.on('request:start', async ({ request }) => {
    requests.push({ url: request.url, body: await request.clone().text() });
  });
});

afterEach(() => {
  server.events.removeAllListeners();
  cleanup();
  setActiveTenantSlug(null);
  if (originalGeolocation) Object.defineProperty(navigator, 'geolocation', originalGeolocation);
  else delete (navigator as { geolocation?: unknown }).geolocation;
  if (originalSecureContext) Object.defineProperty(window, 'isSecureContext', originalSecureContext);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('My position switch (GP-UX-026, REQ-002 opt-in)', () => {
  it('starts off, asks nothing of the browser and reads no site until the user switches it on', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    renderWithProviders(<Harness />);
    const input = screen.getByTestId('field-mode-position-switch');
    expect(input).not.toBeChecked();
    // Label and description are attached to the switch for assistive technology.
    expect(screen.getByRole('switch', { name: 'My position' })).toBe(input);
    expect(input).toHaveAccessibleDescription(/stays on this device/);
    expect(geo.watchPosition).not.toHaveBeenCalled();
    expect(geo.getCurrentPosition).not.toHaveBeenCalled();
    expect(requests).toEqual([]);
  });

  it('draws the dot with an accuracy circle and lets it follow the device', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    renderWithProviders(<Harness />);
    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalledOnce());
    expect(screen.getByTestId('field-mode-position-hint')).toHaveAttribute('data-reason', 'locating');

    geo.move(near(2, -3), 8);
    const dot = await screen.findByTestId('field-mode-position-dot');
    expect(dot).toHaveAttribute('role', 'img');
    expect(dot).toHaveAccessibleName('Your approximate position, accuracy ±8 m');
    expect(dot).toHaveStyle({ pointerEvents: 'none' });
    expect(screen.queryByTestId('field-mode-position-hint')).toBeNull();
    const firstX = Number(screen.getByTestId('field-mode-position-accuracy').getAttribute('cx'));

    geo.move(near(2, 3), 8);
    await waitFor(() =>
      expect(Number(screen.getByTestId('field-mode-position-accuracy').getAttribute('cx'))).toBeGreaterThan(firstX),
    );
  });

  it('never draws the accuracy circle smaller than 3 m', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    renderWithProviders(<Harness />);
    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalled());
    geo.move(near(0, 0), 0.4);
    const dot = await screen.findByTestId('field-mode-position-dot');
    expect(dot).toHaveAttribute('data-accuracy-m', '3');
    expect(dot).toHaveAccessibleName('Your approximate position, accuracy ±3 m');
  });

  it('stops watching when switched off, while the tab is hidden and when the map is left', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    const view = renderWithProviders(<Harness />);
    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalledTimes(1));
    geo.move(near(1, 1));
    await screen.findByTestId('field-mode-position-dot');

    setVisibility('hidden');
    expect(geo.clearWatch).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('field-mode-position-dot')).toBeNull();
    setVisibility('visible');
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalledTimes(2));

    switchOn(); // off again
    expect(geo.clearWatch).toHaveBeenCalledTimes(2);
    expect(screen.queryByTestId('field-mode-position-dot')).toBeNull();

    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalledTimes(3));
    view.unmount();
    expect(geo.clearWatch).toHaveBeenCalledTimes(3);
  });
});

describe('My position hints', () => {
  it('says so when the site has no GPS coordinates, without asking the browser', async () => {
    const geo = installGeolocation();
    siteBackend(null);
    renderWithProviders(<Harness />);
    switchOn();
    const hint = await screen.findByTestId('field-mode-position-hint');
    await waitFor(() => expect(hint).toHaveAttribute('data-reason', 'no_gps'));
    expect(hint).toHaveTextContent('This site has no GPS coordinates');
    expect(geo.watchPosition).not.toHaveBeenCalled();
    expect(screen.queryByTestId('field-mode-position-dot')).toBeNull();
  });

  it('says so when the permission is denied, and draws nothing', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    renderWithProviders(<Harness />);
    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalled());
    geo.fail(1);
    const hint = await screen.findByTestId('field-mode-position-hint');
    expect(hint).toHaveAttribute('data-reason', 'denied');
    expect(hint).toHaveTextContent('You declined location access');
    expect(screen.queryByTestId('field-mode-position-dot')).toBeNull();
  });

  it('reports a device far from the plan instead of drawing the dot off the canvas', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    renderWithProviders(<Harness />);
    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalled());
    geo.move(near(0, 2000));
    const hint = await screen.findByTestId('field-mode-position-hint');
    expect(hint).toHaveAttribute('data-reason', 'far');
    expect(hint).toHaveTextContent(/about 2 km away from the plan/);
    expect(screen.queryByTestId('field-mode-position-dot')).toBeNull();
  });

  it('keeps the switch disabled with the reason outside a secure context (REQ-002)', () => {
    installGeolocation();
    setSecureContext(false);
    renderWithProviders(<Harness />);
    const input = screen.getByTestId('field-mode-position-switch');
    expect(input).toBeDisabled();
    expect(input).toHaveAccessibleDescription(/secure connection/);
  });

  it('hides the switch in a browser without geolocation (REQ-002)', () => {
    Object.defineProperty(navigator, 'geolocation', { value: undefined, configurable: true });
    renderWithProviders(<Harness />);
    expect(screen.queryByTestId('field-mode-position-switch')).toBeNull();
  });
});

describe('the position never leaves the device (SR-019)', () => {
  it('writes no storage, opens no IndexedDB, sends no request with it and logs nothing', async () => {
    const geo = installGeolocation();
    siteBackend([SITE.latitude, SITE.longitude]);
    const openDb = vi.fn();
    vi.stubGlobal('indexedDB', { open: openDb, deleteDatabase: vi.fn() });
    const consoleSpies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((level) =>
      vi.spyOn(console, level).mockImplementation(() => undefined),
    );

    const { store } = renderWithProviders(<Harness />);
    const stateBefore = JSON.stringify(store.getState());
    // From here on (the theme provider writes its own key at mount): local- and sessionStorage share the prototype.
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    switchOn();
    await waitFor(() => expect(geo.watchPosition).toHaveBeenCalled());
    const device = near(3, 4);
    geo.move(device, 6);
    geo.move(near(4, 5), 6);
    await screen.findByTestId('field-mode-position-dot');

    // The digits of the device fix, as any serialisation would print them.
    const leaks = [String(device.latitude), String(device.longitude), device.latitude.toFixed(5), device.longitude.toFixed(5)];
    const carries = (text: string) => leaks.some((leak) => text.includes(leak));

    expect(setItem).not.toHaveBeenCalled();
    expect(openDb).not.toHaveBeenCalled();
    // The one request is the site read, before any fix existed; none carries the position.
    expect(requests.map((request) => new URL(request.url).pathname)).toEqual(['/api/v1/t/garden/sites/site_1']);
    for (const request of requests) expect(carries(request.url + request.body)).toBe(false);
    for (const spy of consoleSpies) {
      for (const call of spy.mock.calls) expect(carries(call.map(String).join(' '))).toBe(false);
    }
    // Nothing of it reached the Redux store.
    expect(JSON.stringify(store.getState())).toBe(stateBefore);
    expect(carries(JSON.stringify(store.getState()))).toBe(false);
    // The DOM carries the projected screen point and the accuracy only, never the coordinates.
    expect(carries(document.body.innerHTML)).toBe(false);
  });
});
