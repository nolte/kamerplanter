import { act, cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { PlanModel } from '../model/planModel';
import type { PlanLocation } from '../model/types';
import { setupEditor, typeAndBlur } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';

afterEach(() => cleanup());

const field = (id: string) => screen.getByTestId(`garden-plan-panel-field-${id}`);

function planWithPolygon(): PlanModel {
  const plan = testPlan();
  const poly: PlanLocation = {
    ...plan.locations.solo,
    key: 'poly',
    name: 'Triangle',
    geometry: {
      kind: 'polygon',
      points: [
        [3, 14],
        [7, 14],
        [5, 17],
      ],
      rotation_deg: 0,
    },
    bbox: [3, 14, 7, 17],
    area_m2: 6,
  };
  return { ...plan, locations: { ...plan.locations, poly } };
}

describe('empty state (GP-UX-049)', () => {
  it('says what to do with exactly one action, which starts the bed tool', () => {
    const t = setupEditor();
    const empty = screen.getByTestId('garden-plan-panel-empty');
    expect(empty).toHaveTextContent(/Pick a bed or object/);
    expect(within(empty).getAllByRole('button')).toHaveLength(1);
    t.after(() => fireEvent.click(within(empty).getByRole('button', { name: 'Draw a bed' })));
    expect(t.state().tool).toBe('bed');
  });

  it('has no accessibility violations', async () => {
    const t = setupEditor();
    await expectNoA11yViolations(t.view.container);
  });
});

describe('editing values (GP-FR-024, GP-FR-155)', () => {
  it('shows the values of the selected bed with axis symbols', () => {
    const t = setupEditor();
    t.click(4, 4);
    expect(screen.getByTestId('garden-plan-panel-title')).toHaveTextContent('Bed 1');
    expect(field('x')).toHaveValue('3');
    expect(field('width')).toHaveValue('2');
    expect(screen.getByLabelText(/x →/)).toBeInTheDocument();
    expect(screen.getByLabelText(/y ↑/)).toBeInTheDocument();
    expect(screen.getByLabelText(/↺/)).toBeInTheDocument();
  });

  it('commits a typed value on blur as ONE undo step', () => {
    const t = setupEditor();
    t.click(4, 4);
    const before = t.state().past.length;
    t.after(() => typeAndBlur(field('width'), '2,5'));
    expect(t.state().past).toHaveLength(before + 1);
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ width_m: 2.5 });
    expect(t.state().past[t.state().past.length - 1].label).toBe('pages.gardenPlan.editor.actions.edit');
  });

  it('commits on Enter and does nothing for an unchanged value', () => {
    const t = setupEditor();
    t.click(4, 4);
    t.after(() => {
      fireEvent.change(field('length'), { target: { value: '3' } });
      fireEvent.keyDown(field('length'), { key: 'Enter' });
    });
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ length_m: 3 });
    const count = t.state().past.length;
    t.after(() => typeAndBlur(field('length'), '3'));
    expect(t.state().past).toHaveLength(count);
  });

  it('puts the old value back on Escape', () => {
    const t = setupEditor();
    t.click(4, 4);
    fireEvent.change(field('width'), { target: { value: '9' } });
    fireEvent.keyDown(field('width'), { key: 'Escape' });
    expect(field('width')).toHaveValue('2');
    expect(t.state().past).toHaveLength(0);
  });

  it('marks a value outside the parent red, explains it and commits nothing (GP-UX-053)', () => {
    const t = setupEditor();
    t.click(4, 4);
    fireEvent.change(field('width'), { target: { value: '30' } });
    expect(field('width')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByTestId('garden-plan-panel-error')).toHaveTextContent(/sticks out/);
    fireEvent.blur(field('width'));
    expect(t.state().past).toHaveLength(0);
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ width_m: 2 });
  });

  it('refuses text that is not a number', () => {
    const t = setupEditor();
    t.click(4, 4);
    fireEvent.change(field('width'), { target: { value: 'abc' } });
    expect(field('width')).toHaveAttribute('aria-invalid', 'true');
    fireEvent.blur(field('width'));
    expect(t.state().past).toHaveLength(0);
  });

  it('renames a bed and keeps the old name for a blank one', () => {
    const t = setupEditor();
    t.click(4, 4);
    const name = screen.getByTestId('garden-plan-panel-name');
    t.after(() => typeAndBlur(name, ' Herbs '));
    expect(t.state().plan!.locations.b1.name).toBe('Herbs');
    t.after(() => typeAndBlur(screen.getByTestId('garden-plan-panel-name'), '  '));
    expect(t.state().plan!.locations.b1.name).toBe('Herbs');
    expect(t.state().past).toHaveLength(1);
  });

  it('lists polygon points, edits one, and keeps three', () => {
    const t = setupEditor({ plan: planWithPolygon() });
    t.click(5, 15);
    expect(t.selected()).toEqual(['poly']);
    const points = screen.getByTestId('garden-plan-panel-points');
    expect(within(points).getByText('Points (3)')).toBeInTheDocument();
    t.after(() => typeAndBlur(screen.getByTestId('garden-plan-panel-point-2-y'), '17.5'));
    expect(t.state().plan!.locations.poly.geometry).toMatchObject({
      points: [
        [3, 14],
        [7, 14],
        [5, 17.5],
      ],
    });
    // Three points are the minimum: no point can be deleted.
    for (const button of within(points).getAllByRole('button', { name: /Delete point/ })) {
      expect(button).toBeDisabled();
    }
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-add-point')));
    expect((t.state().plan!.locations.poly.geometry as { points: unknown[] }).points).toHaveLength(
      4,
    );
    t.after(() => fireEvent.click(screen.getByRole('button', { name: 'Delete point 4' })));
    expect((t.state().plan!.locations.poly.geometry as { points: unknown[] }).points).toHaveLength(
      3,
    );
  });

  it('refuses a polygon point that would cross the outline', () => {
    const t = setupEditor({ plan: planWithPolygon() });
    t.click(5, 15);
    const count = t.state().past.length;
    // The triangle (3,14) (7,14) (5,17): moving the apex far outside the boundary is refused.
    typeAndBlur(screen.getByTestId('garden-plan-panel-point-2-y'), '55');
    expect(screen.getByTestId('garden-plan-panel-error')).toBeInTheDocument();
    expect(t.state().past).toHaveLength(count);
  });
});

describe('locked objects (GP-FR-156)', () => {
  it('shows the values but takes no input and can be unlocked in one undo step', () => {
    const t = setupEditor();
    t.click(15, 9);
    expect(t.selected()).toEqual(['lock']);
    expect(screen.getByTestId('garden-plan-panel-locked')).toBeInTheDocument();
    expect(field('width')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-panel-name')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-panel-delete')).toBeDisabled();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-locked-switch')));
    expect(t.state().plan!.locations.lock.locked).toBe(false);
    expect(t.state().past).toHaveLength(1);
    expect(field('width')).not.toBeDisabled();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-locked-switch')));
    expect(t.state().plan!.locations.lock.locked).toBe(true);
  });
});

describe('z-order and duplicate (GP-FR-025/027)', () => {
  it('brings a bed to the front and back as one step each', () => {
    const t = setupEditor();
    t.click(15, 3);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-front')));
    expect(t.state().plan!.locations.solo.z_order).toBe(2);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-back')));
    expect(t.state().plan!.locations.solo.z_order).toBeLessThan(0);
    expect(t.state().past).toHaveLength(2);
  });

  it('duplicates with an offset, selects the copy, copies no slots or plants', () => {
    const t = setupEditor();
    t.click(4, 4);
    const slots = Object.keys(t.state().plan!.slots).length;
    const plants = Object.keys(t.state().plan!.plants).length;
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-duplicate')));
    expect(t.state().past).toHaveLength(1);
    const [copyKey] = t.selected();
    const copy = t.state().plan!.locations[copyKey];
    expect(copy.name).toBe('Bed 1 (copy)');
    expect(copy.geometry).not.toEqual(t.state().plan!.locations.b1.geometry);
    expect(Object.keys(t.state().plan!.slots)).toHaveLength(slots);
    expect(Object.keys(t.state().plan!.plants)).toHaveLength(plants);
    // One undo removes the copy again.
    expect(t.state().past[t.state().past.length - 1].label).toBe('pages.gardenPlan.editor.actions.duplicate');
  });

  it('reports when the copy would leave its parent', () => {
    const t = setupEditor();
    // The boundary is 20 x 20: a bed in the corner has no free direction for a huge step.
    t.click(15, 3);
    t.after(() => {
      fireEvent.change(field('x'), { target: { value: '18.9' } });
      fireEvent.blur(field('x'));
    });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-duplicate')));
    expect(t.state().past.length).toBeGreaterThanOrEqual(1);
  });
});

describe('stack list (GP-UX-033)', () => {
  it('lists the objects under a repeated click and selects the one that is tapped', () => {
    const t = setupEditor();
    t.click(4, 4);
    t.click(4, 4);
    const list = screen.getByTestId('garden-plan-panel-stack');
    expect(within(list).getByText('Objects at this spot (2)')).toBeInTheDocument();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-stack-item-area')));
    expect(t.selected()).toEqual(['area']);
  });
});

describe('empty bed (GP-UX-049)', () => {
  it('offers exactly the planting action and opens the bed page', () => {
    const onOpenLocation = vi.fn<(locationKey: string) => void>();
    const t = setupEditor({ onOpenLocation });
    t.click(7, 4);
    expect(t.selected()).toEqual(['b2']);
    const empty = screen.getByTestId('garden-plan-panel-empty-bed');
    expect(empty).toHaveTextContent('This bed is empty.');
    fireEvent.click(within(empty).getByRole('button', { name: 'Plant it' }));
    expect(onOpenLocation).toHaveBeenCalledWith('b2');
    fireEvent.click(screen.getByTestId('garden-plan-panel-details'));
    expect(onOpenLocation).toHaveBeenCalledTimes(2);
  });

  it('is not shown for a bed with positions', () => {
    const t = setupEditor();
    t.click(4, 4);
    expect(screen.queryByTestId('garden-plan-panel-empty-bed')).toBeNull();
  });
});

describe('sun and shade tiles (GP-FR-157, TC-053-036)', () => {
  it('shows the five tiles for a selected bed and stores a choice as ONE undo step', async () => {
    const t = setupEditor();
    t.click(4, 4);
    const group = await screen.findByRole('radiogroup', { name: 'Sun and shade of the bed' });
    expect(within(group).getAllByRole('radio')).toHaveLength(5);
    expect(within(group).getByRole('radio', { name: 'Unknown' })).toBeChecked();

    const before = t.state().past.length;
    t.after(() => fireEvent.click(within(group).getByRole('radio', { name: 'Partial shade' })));

    expect(t.state().plan!.locations.b1.sun_exposure).toBe('partial_shade');
    expect(t.state().past).toHaveLength(before + 1);
    expect(t.state().past[t.state().past.length - 1].label).toBe('pages.gardenPlan.editor.actions.edit');
    // The change is unsaved until the save bar is used (planning mode).
    expect(t.state().plan!.locations.b2.sun_exposure).toBe('unknown');
  });

  it('takes no input on a locked bed', async () => {
    const t = setupEditor();
    t.click(15, 9);
    const group = await screen.findByRole('radiogroup', { name: 'Sun and shade of the bed' });

    for (const radio of within(group).getAllByRole('radio')) expect(radio).toBeDisabled();
  });

  it('sets the sun for all selected beds at once, as one undo step, and leaves a locked bed alone', async () => {
    const t = setupEditor();
    t.click(4, 4);
    t.click(7, 4, { shiftKey: true });
    t.click(15, 9, { shiftKey: true });
    expect(t.selected()).toHaveLength(3);
    const bulk = await screen.findByTestId('garden-plan-panel-sun-bulk');
    expect(bulk).toHaveTextContent('Set the sun for all selected beds');
    expect(bulk).toHaveTextContent('Applies to 2 selected beds. Locked beds stay as they are.');

    const before = t.state().past.length;
    t.after(() => fireEvent.click(within(bulk).getByRole('radio', { name: 'Full sun' })));

    const { locations } = t.state().plan!;
    expect([locations.b1.sun_exposure, locations.b2.sun_exposure]).toEqual(['full_sun', 'full_sun']);
    expect(locations.lock.sun_exposure).toBe('unknown');
    expect(t.state().past).toHaveLength(before + 1);
  });

  it('says so and takes no input when every selected bed is locked', async () => {
    const base = testPlan();
    const plan: PlanModel = {
      ...base,
      locations: { ...base.locations, b1: { ...base.locations.b1, locked: true } },
    };
    const t = setupEditor({ plan });
    t.click(4, 4);
    t.click(15, 9, { shiftKey: true });
    const bulk = await screen.findByTestId('garden-plan-panel-sun-bulk');

    expect(bulk).toHaveTextContent('All selected beds are locked. Unlock them to set the sun.');
    for (const radio of within(bulk).getAllByRole('radio')) expect(radio).toBeDisabled();
  });

  it('has no accessibility violations with the tiles shown', async () => {
    const t = setupEditor();
    t.click(4, 4);
    await screen.findByRole('radiogroup', { name: 'Sun and shade of the bed' });
    await expectNoA11yViolations(t.view.container);
  });
});

describe('sun window and leaf shade (GP-FR-158/159, #2538)', () => {
  const PROFILE = 'garden-plan-panel-sun-profile';
  const lastPending = (t: ReturnType<typeof setupEditor>) => t.state().pending[t.state().pending.length - 1].op;

  it('commits a chip as ONE update_fields operation of the plan save, not a PATCH', async () => {
    const t = setupEditor();
    t.click(4, 4);
    const window = await screen.findByTestId(`${PROFILE}-window`);
    expect(within(window).getAllByRole('radio')).toHaveLength(6);
    expect(within(window).getByRole('radio', { name: 'Not known' })).toBeChecked();

    const before = t.state().past.length;
    t.after(() => fireEvent.click(screen.getByTestId(`${PROFILE}-window-morning-input`)));

    expect(t.state().past).toHaveLength(before + 1);
    expect(t.state().past[t.state().past.length - 1].label).toBe('pages.gardenPlan.editor.actions.edit');
    expect(lastPending(t)).toEqual({
      op: 'update_fields',
      entity: 'location',
      key: 'b1',
      fields: { site_conditions: { sun_profile: { sun_window: 'morning' } } },
    });
    expect(t.state().plan!.locations.b1.site_conditions).toEqual({ sun_profile: { sun_window: 'morning' } });
    expect(screen.getByTestId(`${PROFILE}-window-morning-input`)).toBeChecked();
  });

  it('commits the leaf-shade switch the same way and undo takes it back', async () => {
    const t = setupEditor();
    t.click(4, 4);
    const foliage = await screen.findByTestId(`${PROFILE}-foliage`);

    t.after(() => fireEvent.click(foliage));

    expect(lastPending(t)).toEqual({
      op: 'update_fields',
      entity: 'location',
      key: 'b1',
      fields: { site_conditions: { sun_profile: { foliage_shade_in_summer: true } } },
    });
    expect(t.state().plan!.locations.b1.site_conditions?.sun_profile?.foliage_shade_in_summer).toBe(true);

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    expect(t.state().plan!.locations.b1.site_conditions).toBeUndefined();
    expect(t.state().pending).toHaveLength(0);
  });

  it('commits valid hours on blur and nothing for text that is not a number', async () => {
    const t = setupEditor();
    t.click(4, 4);
    const hours = await screen.findByTestId(`${PROFILE}-hours`);
    const pending = t.state().pending.length;

    t.after(() => typeAndBlur(hours, 'viel'));
    expect(t.state().pending).toHaveLength(pending);

    t.after(() => typeAndBlur(hours, '6,5'));
    expect(lastPending(t)).toMatchObject({
      fields: { site_conditions: { sun_profile: { direct_sun_hours_summer: 6.5 } } },
    });
  });

  it('shows the stored profile of the selected bed and takes no input on a locked bed', async () => {
    const base = testPlan();
    const plan: PlanModel = {
      ...base,
      locations: {
        ...base.locations,
        lock: {
          ...base.locations.lock,
          site_conditions: { sun_profile: { sun_window: 'afternoon', foliage_shade_in_summer: true } },
        },
      },
    };
    const t = setupEditor({ plan });
    t.click(15, 9);
    await screen.findByTestId(`${PROFILE}-window`);

    expect(screen.getByTestId(`${PROFILE}-window-afternoon-input`)).toBeChecked();
    expect(screen.getByTestId(`${PROFILE}-foliage`)).toBeChecked();
    expect(screen.getByTestId(`${PROFILE}-foliage`)).toBeDisabled();
    for (const radio of within(screen.getByTestId(`${PROFILE}-window`)).getAllByRole('radio'))
      expect(radio).toBeDisabled();
  });

  it('has no accessibility violations with the chips and the switch shown', async () => {
    const t = setupEditor();
    t.click(4, 4);
    await screen.findByTestId(`${PROFILE}-window`);
    await expectNoA11yViolations(t.view.container);
  });
});

describe('several objects and a plant', () => {
  it('shows the count and the actions that work on many', () => {
    const t = setupEditor();
    t.click(4, 4);
    t.click(15, 3, { shiftKey: true });
    expect(t.selected()).toHaveLength(2);
    expect(screen.getByTestId('garden-plan-panel-multi')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-panel-title')).toHaveTextContent('2 objects selected');
  });

  it('shows a selected plant read-only', () => {
    const t = setupEditor();
    act(() => {
      t.store.dispatch({
        type: 'gardenPlan/setSelection',
        payload: [{ entity: 'plant', key: 'p1' }],
      });
    });
    act(() => t.rerender());
    expect(screen.getByTestId('garden-plan-panel-readonly')).toHaveTextContent(/TOM-1/);
  });
});

describe('accessibility', () => {
  it('has no violations with a bed selected, with a polygon and when locked', async () => {
    const t = setupEditor({ plan: planWithPolygon() });
    t.click(4, 4);
    await expectNoA11yViolations(t.view.container);
    t.click(5, 15);
    await expectNoA11yViolations(t.view.container);
    t.click(15, 9);
    await expectNoA11yViolations(t.view.container);
  });
});
