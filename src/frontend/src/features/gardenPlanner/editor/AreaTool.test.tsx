/**
 * The tool "Bereich" in the editor (REQ-053 GP-UX-071, §9.5, #2913): the rail button, the type choice with the parent
 * rule, drawing an area, a bed drawn inside it afterwards, the notice when it is drawn around a bed that is there
 * already, and the non-pointer path "Bereich ▸ Mit Maßen hinzufügen".
 */
import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { LocationType } from '@/api/types';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { PlanModel } from '../model/planModel';
import { testPlan } from './tools/toolTestKit';
import { chooseToolMenuEntry, pointer, px, setupEditor } from './editorTestKit';

const listLocationTypes = vi.hoisted(() => vi.fn());
vi.mock('@/api/endpoints/sites', () => ({
  listLocationTypes,
  getSite: () => Promise.reject(new Error('the site is not read in this test')),
}));

const type = (key: string, name: string, flags: Partial<LocationType> = {}): LocationType => ({
  key,
  name,
  name_en: name,
  icon: null,
  is_indoor: false,
  is_bed: false,
  supports_layout: false,
  is_system: true,
  sort_order: 0,
  description: null,
  ...flags,
});

beforeEach(() => {
  listLocationTypes.mockResolvedValue([
    type('bed', 'Bed', { is_bed: true, supports_layout: true }),
    type('tent', 'Tent', { is_indoor: true, supports_layout: true }),
    type('zone', 'Zone'),
    type('room', 'Room', { is_indoor: true }),
    type('garden', 'Garden'),
    type('terrace', 'Terrace'),
    type('greenhouse', 'Greenhouse'),
    // Added by a platform admin: an outdoor area type of its own.
    type('orchard', 'Orchard', { is_system: false, sort_order: 50 }),
  ]);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

/** The test plan as the server reads it after #2913: its `area` location is an area, the area types are named. */
function areaPlan(): PlanModel {
  const plan = testPlan();
  return {
    ...plan,
    areaTypeKeys: ['area', 'garden', 'greenhouse', 'orchard', 'room', 'terrace', 'zone'],
    locations: { ...plan.locations, area: { ...plan.locations.area, is_area: true } },
  };
}

function drag(t: ReturnType<typeof setupEditor>, from: [number, number], to: [number, number]): void {
  t.after(() => {
    fireEvent.pointerDown(t.canvas(), pointer(px(...from)));
    fireEvent.pointerMove(t.canvas(), pointer(px(...to)));
    fireEvent.pointerUp(t.canvas(), pointer(px(...to)));
  });
}

describe('the area tool (GP-UX-071)', () => {
  it('offers the garden area types with the parent rule, and draws an area of the chosen type', async () => {
    const t = setupEditor({ plan: areaPlan() });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-area')));
    expect(t.state().tool).toBe('area');
    const choice = await screen.findByRole('combobox', { name: 'Area type' });
    // The parent rule stands under the choice before the first click.
    expect(screen.getByText(/afterwards belong to it/)).toBeInTheDocument();
    fireEvent.mouseDown(choice);
    const offered = screen.getAllByRole('option').map((option) => option.textContent);
    // The seeded garden types in their order, then the added outdoor type; no bed, tent, room or zone.
    expect(offered).toEqual(['Garden', 'Terrace', 'Greenhouse', 'Orchard']);
    fireEvent.click(screen.getByRole('option', { name: 'Terrace' }));

    drag(t, [13, 13], [19, 18]);
    const [key] = t.selected();
    const area = t.state().plan!.locations[key];
    expect(area).toMatchObject({ location_type_key: 'terrace', name: 'Area 2', is_area: true });
    expect(area.parent_location_key ?? null).toBeNull();
    // Back to the select tool with the area selected, like a drawn bed.
    expect(t.state().tool).toBe('select');
    expect(screen.queryByTestId('garden-plan-notice')).toBeNull();
  });

  it('makes the area the parent of a bed drawn inside it afterwards', async () => {
    const t = setupEditor({ plan: areaPlan(), connected: true });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-area')));
    await screen.findByRole('combobox', { name: 'Area type' });
    drag(t, [13, 13], [19, 18]);
    const [areaKey] = t.selected();

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-bed')));
    drag(t, [14, 14], [16, 15]);
    const [bedKey] = t.selected();
    expect(bedKey).not.toBe(areaKey);
    expect(t.state().plan!.locations[bedKey].parent_location_key).toBe(areaKey);
  });

  it('says so when drawn around a bed that is there: the bed keeps its parent', async () => {
    const t = setupEditor({ plan: areaPlan() });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-area')));
    await screen.findByRole('combobox', { name: 'Area type' });
    // (13, 1)-(17, 5) encloses the bed "solo" (14, 2), 2 x 2 m, which hangs below nothing.
    drag(t, [13, 1], [17, 5]);
    expect(t.state().past).toHaveLength(1);
    expect(t.state().plan!.locations.solo.parent_location_key ?? null).toBeNull();
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(
      'What was inside it already does not belong to it',
    );
  });

  it('adds an area by its dimensions from the sub-menu of Area (the path without a pointer)', async () => {
    const t = setupEditor({ plan: areaPlan() });
    t.after(() => chooseToolMenuEntry('area', 'garden-plan-add-with-dimensions-area'));
    await waitFor(() => expect(listLocationTypes).toHaveBeenCalled());
    expect(screen.getByTestId('garden-plan-add-kind-area')).toHaveAttribute('aria-pressed', 'true');
    // An area is a rect or a polygon: no circle, no line, no height.
    expect(screen.queryByTestId('garden-plan-add-shape-circle')).toBeNull();
    expect(screen.queryByTestId('garden-plan-add-shape-polyline')).toBeNull();
    expect(screen.queryByTestId('garden-plan-add-height')).toBeNull();
    fireEvent.mouseDown(await screen.findByRole('combobox', { name: 'Area type' }));
    fireEvent.click(screen.getByRole('option', { name: 'Greenhouse' }));
    const set = (id: string, value: string) => fireEvent.change(screen.getByTestId(id), { target: { value } });
    set('garden-plan-add-x', '13');
    set('garden-plan-add-y', '13');
    set('garden-plan-add-width', '5');
    set('garden-plan-add-length', '4');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-submit')));
    const area = t.state().plan!.locations[t.selected()[0]];
    expect(area).toMatchObject({ location_type_key: 'greenhouse', name: 'Area 2', is_area: true });
  });

  it('has no accessibility violations with the type choice shown', async () => {
    const t = setupEditor({ plan: areaPlan() });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-area')));
    await screen.findByRole('combobox', { name: 'Area type' });
    await expectNoA11yViolations(document.body);
  });
});
