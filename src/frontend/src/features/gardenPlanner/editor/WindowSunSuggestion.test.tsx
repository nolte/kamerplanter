import { cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { gardenObject } from '@/test/gardenPlanFixtures';
import { getSite } from '@/api/endpoints/sites';
import type { Site } from '@/api/types';
import { patchSun } from '../bed/bedApi';
import type { PlanModel } from '../model/planModel';
import type { GardenObject, Geometry, PlanLocation, SunWindow } from '../model/types';
import { openPanelTab, setupEditor } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';

/**
 * "Aus Fenster vorschlagen" in the properties panel (REQ-053 GP-FR-181, WP 10.7, G-W10 c): a suggestion is a
 * preview - opening it, cancelling it or closing it writes nothing; only the confirmation writes, and it writes
 * exactly `site_conditions.sun_profile.sun_window` through the plan batch (never the bed page's PATCH).
 */
vi.mock('../bed/bedApi', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../bed/bedApi')>()),
  patchSun: vi.fn(),
}));

vi.mock('@/api/endpoints/sites', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/endpoints/sites')>()),
  listLocationTypes: vi.fn(async () => []),
  getSite: vi.fn(),
}));

beforeEach(() => {
  // By default the site cannot be read: the 1.5 m default and no latitude (the northern hemisphere is assumed).
  vi.mocked(getSite).mockRejectedValue(new Error('offline'));
});

afterEach(() => {
  cleanup();
  vi.mocked(patchSun).mockClear();
  vi.mocked(getSite).mockReset();
});

const SECTION = 'garden-plan-panel-window-suggest-section';
const BUTTON = 'garden-plan-panel-window-suggest';
const DIALOG = 'garden-plan-window-suggestion-dialog';

function line(points: [number, number][]): Geometry {
  return { kind: 'polyline', points, width_m: 0.1 };
}

function windowObject(key: string, geometry: Geometry, label = ''): GardenObject {
  return gardenObject(key, 0, 0, {
    object_type: 'window',
    label,
    geometry,
    bbox: null,
    props: { object_type: 'window', sill_height_m: 0.9, glazing: 'double' },
  });
}

/**
 * The test plan (boundary 0..20 m, north up) plus a windowsill `sill` 1 x 2 m at (18.8, 14) right next to the east
 * wall, and the given windows. `sunWindow` is the sill's stored sun window.
 */
function planWith(windows: GardenObject[], sunWindow?: SunWindow): PlanModel {
  const base = testPlan();
  const sill: PlanLocation = {
    ...base.locations.solo,
    key: 'sill',
    name: 'Sill',
    geometry: { kind: 'rect', origin: [18.8, 14], width_m: 1, length_m: 2, rotation_deg: 0 },
    bbox: [18.8, 14, 19.8, 16],
    area_m2: 2,
    ...(sunWindow ? { site_conditions: { sun_profile: { sun_window: sunWindow } } } : {}),
  };
  const objects = Object.fromEntries(windows.map((object) => [object.key, object]));
  return {
    ...base,
    locations: { ...base.locations, sill },
    gardenObjects: { ...base.gardenObjects, ...objects },
  };
}

/** A window in the east wall beside the sill (faces east: morning). */
const EAST = windowObject('w_east', line([[20, 14.5], [20, 15.5]]), 'Living room');
/** A window in the north wall, far from the sill. */
const NORTH_FAR = windowObject('w_north', line([[2, 20], [4, 20]]));

function selectSill(plan: PlanModel) {
  const t = setupEditor({ plan });
  t.click(19.3, 15);
  return t;
}

async function openSuggestion() {
  fireEvent.click(await screen.findByTestId(BUTTON));
  return screen.getByTestId(DIALOG);
}

describe('where the action appears', () => {
  it('a garden plan without windows shows no window suggestion (unchanged garden)', async () => {
    const t = setupEditor();
    t.click(4, 4);
    await screen.findByTestId('garden-plan-panel-sun-profile-window');
    expect(screen.queryByTestId(SECTION)).not.toBeInTheDocument();
  });

  it('a plan with a window offers it on a bed, with a 48 px button and the radius in the hint', async () => {
    selectSill(planWith([EAST]));
    const button = await screen.findByTestId(BUTTON);
    expect(button).toBeEnabled();
    expect(within(screen.getByTestId(SECTION)).getByText(/within 1\.5 m/)).toBeInTheDocument();
  });
});

describe('the preview writes nothing without a confirmation (G-W10 c)', () => {
  it('opening shows the suggestion, the window and the caveats, and changes nothing', async () => {
    const t = selectSill(planWith([EAST]));
    const pending = t.state().pending.length;
    const past = t.state().past.length;

    const dialog = await openSuggestion();

    expect(within(dialog).getByTestId('garden-plan-window-suggestion-value')).toHaveAttribute(
      'data-sun-window',
      'morning',
    );
    const item = within(dialog).getByTestId('garden-plan-window-suggestion-window-w_east');
    expect(item).toHaveAttribute('data-orientation', 'east');
    expect(item).toHaveTextContent('Living room');
    const hints = within(dialog).getByTestId('garden-plan-window-suggestion-hints');
    const codes = Array.from(hints.querySelectorAll('[data-hint]')).map((li) => li.getAttribute('data-hint'));
    expect(codes).toEqual(['hemisphere_assumed', 'shading_not_considered', 'season', 'window_distance', 'glazing']);
    expect(screen.queryByTestId('garden-plan-window-suggestion-replace')).not.toBeInTheDocument();

    expect(t.state().pending).toHaveLength(pending);
    expect(t.state().past).toHaveLength(past);
    expect(t.state().plan!.locations.sill.site_conditions).toBeUndefined();
  });

  it('cancelling closes the preview and changes nothing', async () => {
    const t = selectSill(planWith([EAST]));
    const pending = t.state().pending.length;
    await openSuggestion();

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-window-suggestion-cancel')));

    expect(screen.queryByTestId(DIALOG)).not.toBeInTheDocument();
    expect(t.state().pending).toHaveLength(pending);
    expect(t.state().plan!.locations.sill.site_conditions).toBeUndefined();
  });

  it('the confirmation writes exactly the sun window as ONE operation of the plan save', async () => {
    const t = selectSill(planWith([EAST]));
    const before = t.state().plan!.locations.sill;
    await openSuggestion();

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-window-suggestion-apply')));

    const last = t.state().pending[t.state().pending.length - 1].op;
    expect(last).toEqual({
      op: 'update_fields',
      entity: 'location',
      key: 'sill',
      fields: { site_conditions: { sun_profile: { sun_window: 'morning' } } },
    });
    const after = t.state().plan!.locations.sill;
    expect(after.site_conditions).toEqual({ sun_profile: { sun_window: 'morning' } });
    // The coarse class is not touched (no sun_exposure from a window).
    expect(after.sun_exposure).toBe(before.sun_exposure);
    expect(patchSun).not.toHaveBeenCalled();
    expect(screen.queryByTestId(DIALOG)).not.toBeInTheDocument();
  });
});

describe('a stored value is only replaced on an explicit confirmation', () => {
  it('names both values, offers "Replace" and leaves the value on cancel', async () => {
    const t = selectSill(planWith([EAST], 'afternoon'));
    const dialog = await openSuggestion();

    expect(within(dialog).getByTestId('garden-plan-window-suggestion-replace')).toHaveTextContent(
      /Afternoon.*Morning/,
    );
    expect(within(dialog).getByTestId('garden-plan-window-suggestion-apply')).toHaveTextContent('Replace');

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-window-suggestion-cancel')));
    expect(t.state().plan!.locations.sill.site_conditions?.sun_profile?.sun_window).toBe('afternoon');
  });

  it('replaces only after the confirmation', async () => {
    const t = selectSill(planWith([EAST], 'afternoon'));
    await openSuggestion();

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-window-suggestion-apply')));

    expect(t.state().plan!.locations.sill.site_conditions?.sun_profile?.sun_window).toBe('morning');
  });

  it('a suggestion equal to the stored value offers nothing to take over', async () => {
    const t = selectSill(planWith([EAST], 'morning'));
    const pending = t.state().pending.length;
    const dialog = await openSuggestion();

    expect(within(dialog).getByTestId('garden-plan-window-suggestion-unchanged')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-window-suggestion-apply')).not.toBeInTheDocument();
    expect(t.state().pending).toHaveLength(pending);
  });
});

describe('without a suggestion the preview explains why', () => {
  it('no window within the radius', async () => {
    selectSill(planWith([NORTH_FAR]));
    const dialog = await openSuggestion();

    expect(within(dialog).getByTestId('garden-plan-window-suggestion-none')).toHaveTextContent(
      /no window within 1\.5 m/,
    );
    expect(screen.queryByTestId('garden-plan-window-suggestion-apply')).not.toBeInTheDocument();
  });

  it('a north window brings diffuse light only', async () => {
    const northBeside = windowObject('w_n', line([[18.8, 20], [19.8, 20]]));
    const plan = planWith([northBeside]);
    // The sill reaches up to y = 16; widen the radius so the north wall counts.
    vi.mocked(getSite).mockResolvedValue({
      type: 'indoor',
      gps_coordinates: [52.5, 13.4],
      window_thresholds: { suggestion_radius_m: 5 },
    } as Site);
    selectSill(plan);
    await screen.findByText(/within 5 m/);
    const dialog = await openSuggestion();

    expect(within(dialog).getByTestId('garden-plan-window-suggestion-none')).toHaveTextContent(/diffuse light/);
    expect(within(dialog).getByTestId('garden-plan-window-suggestion-window-w_n')).toHaveAttribute(
      'data-orientation',
      'north',
    );
  });

  it('in the southern hemisphere the same north window gives midday', async () => {
    const northBeside = windowObject('w_n', line([[18.8, 20], [19.8, 20]]));
    vi.mocked(getSite).mockResolvedValue({
      type: 'indoor',
      gps_coordinates: [-33.9, 151.2],
      window_thresholds: { suggestion_radius_m: 5 },
    } as Site);
    selectSill(planWith([northBeside]));
    await screen.findByText(/within 5 m/);
    const dialog = await openSuggestion();

    expect(within(dialog).getByTestId('garden-plan-window-suggestion-value')).toHaveAttribute(
      'data-sun-window',
      'midday',
    );
  });
});

describe('the window shows its derived orientation (GP-FR-181)', () => {
  it('as direction and azimuth, read-only', () => {
    const t = setupEditor({ plan: planWith([EAST]) });
    t.click(20, 15);
    openPanelTab('properties');
    const orientation = screen.getByTestId('garden-plan-panel-window-orientation');
    expect(orientation).toHaveAttribute('data-available', 'true');
    expect(orientation).toHaveTextContent('East, 90°');
    expect(screen.queryByTestId('garden-plan-panel-window-orientation-convention')).not.toBeInTheDocument();
  });
});

describe('accessibility', () => {
  it('the open preview has no violations', async () => {
    const t = selectSill(planWith([EAST]));
    await openSuggestion();
    await expectNoA11yViolations(t.view.baseElement);
  });
});
