/**
 * REQ-053 WP 10.6 (#2827, GP-FR-180): the property fields of window, door, furniture, lamp and trellis and the switch
 * `off_site` in the side panel's tab "Eigenschaften".
 *
 * Pinned: per class the save sends ONE `update_fields` whose props carry exactly the fields of the backend props model
 * (`app/domain/models/garden_object.py`, mirrored in `BACKEND_PROPS_FIELDS` below) and the panel reads the value back
 * from the plan model; a value the model refuses (bounds, required, length) is not committed and the field says what
 * to enter; a PPFD is never invented; switching `off_site` off is refused while the shape sticks out; axe is clean.
 */
import { act, cleanup, fireEvent, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import * as api from '../../api/gardenPlan';
import { normalizePlan } from '../../model/planModel';
import type {
  GardenObject,
  GardenObjectProps,
  GardenObjectType,
  PlanBatchResponse,
  PlanOperation,
} from '../../model/types';
import { setSelection } from '../../state/gardenPlanSlice';
import { openPanelTab, setupEditor, typeAndBlur } from '../editorTestKit';

vi.mock('../../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
}));

const applyPlanBatch = vi.mocked(api.applyPlanBatch);

/**
 * The fields of the backend props models (`garden_object.py`, `WindowProps` ... `LampProps`, `extra="forbid"`): a key
 * outside this list would be a 422 on the save. Keep in step with the model.
 */
const BACKEND_PROPS_FIELDS: Partial<Record<GardenObjectType, readonly string[]>> = {
  window: ['object_type', 'sill_height_m', 'glazing'],
  door: ['object_type', 'swing'],
  furniture: ['object_type'],
  lamp: ['object_type', 'kind', 'height_m', 'ppfd_ref'],
  trellis: ['object_type', 'height_m'],
};

const line = (x: number) => ({
  kind: 'polyline' as const,
  width_m: 0.1,
  points: [
    [x, 15],
    [x + 1, 15],
  ] as [number, number][],
});

function objectsPlan(extra: GardenObject[] = []) {
  return normalizePlan(
    planResponse({
      plan: {
        boundary: { kind: 'rect', origin: [0, 0], width_m: 20, length_m: 20, rotation_deg: 0 },
        north_angle_deg: 0,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
        plan_revision: 7,
      },
      locations: [],
      slots: [],
      plants: [],
      garden_objects: [
        gardenObject('win', 2, 15, {
          object_type: 'window',
          label: 'Kitchen window',
          geometry: line(2),
          bbox: [2, 15, 3, 15],
          props: { object_type: 'window' },
        }),
        gardenObject('door', 5, 15, {
          object_type: 'door',
          label: 'Door',
          geometry: line(5),
          bbox: [5, 15, 6, 15],
          props: { object_type: 'door', swing: 'inwards' },
        }),
        gardenObject('shelf', 8, 2, {
          object_type: 'furniture',
          label: 'Shelf',
          geometry: { kind: 'rect', origin: [8, 2], width_m: 1, length_m: 0.5, rotation_deg: 0 },
          bbox: [8, 2, 9, 2.5],
          props: { object_type: 'furniture' },
        }),
        gardenObject('lamp', 12, 12, {
          object_type: 'lamp',
          label: 'Grow light',
          geometry: { kind: 'point', origin: [12, 12] },
          bbox: [11.75, 11.75, 12.25, 12.25],
          props: { object_type: 'lamp', kind: 'grow_light', height_m: 1.2 },
        }),
        gardenObject('trel', 14, 15, {
          object_type: 'trellis',
          label: 'Trellis',
          geometry: line(14),
          bbox: [14, 15, 15, 15],
          props: { object_type: 'trellis', height_m: 1.8 },
        }),
        ...extra,
      ],
    }),
  );
}

function ok(): PlanBatchResponse {
  return { plan_revision: 8, key_map: {}, updated: [], deleted: [], derived: {} };
}

type Harness = ReturnType<typeof setupEditor>;

function select(key: string, plan = objectsPlan()): Harness {
  const t = setupEditor({ plan });
  t.after(() => {
    act(() => {
      t.store.dispatch(setSelection([{ entity: 'garden_object', key }]));
    });
  });
  openPanelTab('properties');
  t.rerender();
  return t;
}

/** Leave the field and bring the editor up to date with the store. */
function edit(t: Harness, testId: string, value: string) {
  t.after(() => typeAndBlur(screen.getByTestId(testId), value));
}

async function save(t: Harness): Promise<PlanOperation[]> {
  applyPlanBatch.mockResolvedValue(ok());
  await act(async () => {
    fireEvent.click(screen.getByTestId('garden-plan-save'));
  });
  t.rerender();
  expect(applyPlanBatch).toHaveBeenCalledTimes(1);
  return applyPlanBatch.mock.calls[0][1].operations;
}

/** The props of the one `update_fields` of `key` the save sent, checked against the backend model's fields. */
function sentProps(ops: PlanOperation[], key: string, type: GardenObjectType): Record<string, unknown> {
  const edits = ops.filter((op) => op.op === 'update_fields' && op.entity === 'garden_object' && op.key === key);
  expect(edits).toHaveLength(1);
  const op = edits[0];
  if (op.op !== 'update_fields' || op.entity !== 'garden_object' || !op.fields.props) throw new Error('no props');
  const props = op.fields.props;
  expect(Object.keys(props).every((field) => BACKEND_PROPS_FIELDS[type]?.includes(field))).toBe(true);
  expect(props.object_type).toBe(type);
  return props;
}

const storedProps = (t: Harness, key: string): GardenObjectProps => t.state().plan!.gardenObjects[key].props;

beforeEach(() => applyPlanBatch.mockReset());
afterEach(() => cleanup());

describe('window (GP-FR-180)', () => {
  it('saves sill height and glazing as the WindowProps fields and reads them back', async () => {
    const user = userEvent.setup();
    const t = select('win');
    const section = screen.getByTestId('garden-plan-panel-object-props');
    expect(section).toHaveAttribute('data-object-type', 'window');

    edit(t, 'garden-plan-panel-window-sill-height', '0,85');
    await user.click(within(section).getByRole('combobox', { name: 'Glazing' }));
    await user.click(within(screen.getByRole('listbox')).getByRole('option', { name: 'Double or multiple glazing' }));
    t.rerender();

    expect(screen.getByTestId('garden-plan-panel-window-sill-height')).toHaveValue('0.85');
    expect(screen.getByTestId('garden-plan-panel-window-glazing')).toHaveValue('double');
    expect(storedProps(t, 'win')).toEqual({ object_type: 'window', sill_height_m: 0.85, glazing: 'double' });

    const ops = await save(t);
    // Two edits of the same object are two operations; the last one carries both values.
    const winOps = ops.filter((op) => op.op === 'update_fields' && op.key === 'win');
    const last = winOps[winOps.length - 1];
    expect(last).toMatchObject({ fields: { props: { sill_height_m: 0.85, glazing: 'double' } } });
    for (const op of ops) {
      if (op.op === 'update_fields' && op.entity === 'garden_object' && op.fields.props) {
        expect(Object.keys(op.fields.props).every((f) => BACKEND_PROPS_FIELDS.window!.includes(f))).toBe(true);
      }
    }
  });

  it('allows a sill at floor level and clears the glazing to null', async () => {
    const user = userEvent.setup();
    const plan = objectsPlan();
    plan.gardenObjects.win = { ...plan.gardenObjects.win, props: { object_type: 'window', glazing: 'single' } };
    const t = select('win', plan);

    edit(t, 'garden-plan-panel-window-sill-height', '0');
    expect(storedProps(t, 'win')).toMatchObject({ sill_height_m: 0 });
    await user.click(screen.getByRole('combobox', { name: 'Glazing' }));
    await user.click(within(screen.getByRole('listbox')).getByRole('option', { name: 'Not given' }));
    t.rerender();

    expect(storedProps(t, 'win')).toEqual({ object_type: 'window', sill_height_m: 0, glazing: null });
  });

  it('refuses a negative sill height with a text that says what to enter', () => {
    const t = select('win');

    edit(t, 'garden-plan-panel-window-sill-height', '-0.1');

    expect(storedProps(t, 'win')).toEqual({ object_type: 'window' });
    expect(screen.getByText('Enter a sill height between 0 and 1,000 m, or leave the field empty.')).toBeInTheDocument();
  });

  it('shows the derived orientation read-only and says it is not available yet', () => {
    select('win');

    const orientation = screen.getByTestId('garden-plan-panel-window-orientation');
    expect(orientation).toHaveAttribute('data-available', 'false');
    expect(orientation).toHaveTextContent('Orientation: not available yet');
    expect(within(orientation).queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('has no axe violations in the panel', async () => {
    select('win');

    await expectNoA11yViolations(screen.getByTestId('garden-plan-panel'));
  });
});

describe('door (GP-FR-180)', () => {
  it('saves the swing as DoorProps.swing, trimmed, and clears it to null', async () => {
    const t = select('door');
    const swing = screen.getByTestId('garden-plan-panel-door-swing');
    expect(swing).toHaveValue('inwards');

    edit(t, 'garden-plan-panel-door-swing', '  outwards, hinged left ');
    expect(screen.getByTestId('garden-plan-panel-door-swing')).toHaveValue('outwards, hinged left');
    expect(sentProps(await save(t), 'door', 'door')).toEqual({ object_type: 'door', swing: 'outwards, hinged left' });
  });

  it('sends null for an emptied swing', async () => {
    const t = select('door');

    edit(t, 'garden-plan-panel-door-swing', '');

    expect(sentProps(await save(t), 'door', 'door')).toEqual({ object_type: 'door', swing: null });
  });

  it('refuses more than 50 characters', () => {
    const t = select('door');

    edit(t, 'garden-plan-panel-door-swing', 'x'.repeat(51));

    expect(storedProps(t, 'door')).toEqual({ object_type: 'door', swing: 'inwards' });
    expect(screen.getByText('At most 50 characters. Shorten the description.')).toBeInTheDocument();
  });
});

describe('furniture (GP-FR-180)', () => {
  it('offers no props fields (FurnitureProps has none) but the off-site switch', () => {
    select('shelf');

    const section = screen.getByTestId('garden-plan-panel-object-props');
    expect(screen.getByTestId('garden-plan-panel-furniture-note')).toBeInTheDocument();
    expect(within(section).queryAllByRole('textbox')).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-panel-off-site-switch')).toBeInTheDocument();
  });
});

describe('lamp (GP-FR-180)', () => {
  it('saves kind, height and reference PPFD as the LampProps fields and reads them back', async () => {
    const user = userEvent.setup();
    const t = select('lamp');

    await user.click(screen.getByRole('combobox', { name: 'Kind of lamp' }));
    await user.click(within(screen.getByRole('listbox')).getByRole('option', { name: 'Ceiling light' }));
    t.rerender();
    edit(t, 'garden-plan-panel-lamp-height', '2,4');
    edit(t, 'garden-plan-panel-lamp-ppfd', '650');

    expect(screen.getByTestId('garden-plan-panel-lamp-kind')).toHaveValue('ceiling');
    expect(screen.getByTestId('garden-plan-panel-lamp-height')).toHaveValue('2.4');
    expect(screen.getByTestId('garden-plan-panel-lamp-ppfd')).toHaveValue('650');
    expect(screen.getByText('µmol/m²/s')).toBeInTheDocument();

    const ops = await save(t);
    const lampOps = ops.filter((op) => op.op === 'update_fields' && op.key === 'lamp');
    expect(lampOps).toHaveLength(3);
    expect(lampOps[lampOps.length - 1]).toMatchObject({
      fields: { props: { object_type: 'lamp', kind: 'ceiling', height_m: 2.4, ppfd_ref: 650 } },
    });
    for (const op of lampOps) {
      if (op.op === 'update_fields' && op.entity === 'garden_object' && op.fields.props) {
        expect(Object.keys(op.fields.props).every((f) => BACKEND_PROPS_FIELDS.lamp!.includes(f))).toBe(true);
      }
    }
  });

  it('invents no PPFD: an unknown value stays empty with a hint', () => {
    select('lamp');

    expect(screen.getByTestId('garden-plan-panel-lamp-ppfd')).toHaveValue('');
    expect(screen.getByText(/there is no default value/)).toBeInTheDocument();
  });

  it('refuses an empty height (required) and a negative PPFD', () => {
    const t = select('lamp');

    edit(t, 'garden-plan-panel-lamp-height', '');
    edit(t, 'garden-plan-panel-lamp-ppfd', '-5');

    expect(storedProps(t, 'lamp')).toEqual({ object_type: 'lamp', kind: 'grow_light', height_m: 1.2 });
    expect(screen.getByText('Enter a height between 0.01 and 1,000 m. The field cannot be empty.')).toBeInTheDocument();
    expect(screen.getByText('Enter a value of 0 µmol/m²/s or more, or leave the field empty.')).toBeInTheDocument();
  });

  it('has no axe violations in the panel', async () => {
    select('lamp');

    await expectNoA11yViolations(screen.getByTestId('garden-plan-panel'));
  });
});

describe('trellis (GP-FR-180)', () => {
  it('saves the height as TrellisProps.height_m and reads it back', async () => {
    const t = select('trel');

    edit(t, 'garden-plan-panel-trellis-height', '2.2');

    expect(screen.getByTestId('garden-plan-panel-trellis-height')).toHaveValue('2.2');
    expect(sentProps(await save(t), 'trel', 'trellis')).toEqual({ object_type: 'trellis', height_m: 2.2 });
  });

  it('refuses a height above the model bound', () => {
    const t = select('trel');

    edit(t, 'garden-plan-panel-trellis-height', '1001');

    expect(storedProps(t, 'trel')).toEqual({ object_type: 'trellis', height_m: 1.8 });
    expect(screen.getByTestId('garden-plan-panel-trellis-height')).toHaveAttribute('aria-invalid', 'true');
  });

  it('takes no input on a locked object', () => {
    const plan = objectsPlan();
    plan.gardenObjects.trel = { ...plan.gardenObjects.trel, locked: true };
    select('trel', plan);

    expect(screen.getByTestId('garden-plan-panel-trellis-height')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-panel-off-site-switch')).toBeDisabled();
  });
});

describe('off_site switch (§9.5, V-03)', () => {
  it('saves off_site as one update_fields and reads it back', async () => {
    const t = select('shelf');

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-off-site-switch')));

    expect(screen.getByTestId('garden-plan-panel-off-site-switch')).toBeChecked();
    const ops = await save(t);
    expect(ops).toEqual([{ op: 'update_fields', entity: 'garden_object', key: 'shelf', fields: { off_site: true } }]);
  });

  it('refuses to switch off while the object sticks out of the boundary, and says why', () => {
    const outside = gardenObject('house', 19, 5, {
      object_type: 'building',
      label: "Neighbour's house",
      geometry: { kind: 'rect', origin: [19, 5], width_m: 4, length_m: 4, rotation_deg: 0 },
      bbox: [19, 5, 23, 9],
      props: { object_type: 'building' },
      off_site: true,
    });
    const t = select('house', objectsPlan([outside]));

    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-off-site-switch')));

    expect(t.state().plan!.gardenObjects.house.off_site).toBe(true);
    expect(t.state().pending).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-panel-off-site-error')).toHaveTextContent(/Move it fully inside/);
  });
});
