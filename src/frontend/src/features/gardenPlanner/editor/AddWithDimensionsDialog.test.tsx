import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { LocationType } from '@/api/types';
import { pointer, px, setupEditor } from './editorTestKit';

const listLocationTypes = vi.hoisted(() => vi.fn());
vi.mock('@/api/endpoints/sites', () => ({ listLocationTypes }));

const type = (key: string, name: string, is_bed = true): LocationType => ({
  key,
  name,
  name_en: name,
  icon: null,
  is_indoor: false,
  is_bed,
  supports_layout: true,
  is_system: true,
  sort_order: 0,
  description: null,
});

beforeEach(() => {
  listLocationTypes.mockResolvedValue([
    type('bed', 'Bed'),
    type('raised_bed', 'Raised bed'),
    type('tent', 'Tent', false),
  ]);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const open = (t: ReturnType<typeof setupEditor>) =>
  t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-with-dimensions')));
const set = (id: string, value: string) =>
  fireEvent.change(screen.getByTestId(id), { target: { value } });

describe('add with dimensions (GP-UX-046)', () => {
  it('creates a bed of the typed size and position, named, and selects it', async () => {
    const t = setupEditor();
    open(t);
    await waitFor(() => expect(listLocationTypes).toHaveBeenCalled());
    set('garden-plan-add-name', 'Herbs');
    set('garden-plan-add-x', '14');
    set('garden-plan-add-y', '14');
    set('garden-plan-add-width', '3,5');
    set('garden-plan-add-length', '1');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-submit')));
    const [key] = t.selected();
    expect(t.state().plan!.locations[key]).toMatchObject({
      name: 'Herbs',
      geometry: { kind: 'rect', origin: [14, 14], width_m: 3.5, length_m: 1 },
    });
    expect(t.state().past).toHaveLength(1);
    await waitFor(() => expect(screen.queryByTestId('garden-plan-add-dialog')).toBeNull());
  });

  it('explains an invalid number under the field and submits with Enter', async () => {
    const t = setupEditor();
    open(t);
    await waitFor(() => expect(listLocationTypes).toHaveBeenCalled());
    set('garden-plan-add-width', 'abc');
    expect(screen.getByTestId('garden-plan-add-width')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText('Please enter a number, e.g. 2.5.')).toBeInTheDocument();
    set('garden-plan-add-width', '3');
    set('garden-plan-add-x', '14');
    set('garden-plan-add-y', '14');
    t.after(() => fireEvent.submit(screen.getByTestId('garden-plan-add-width').closest('form')!));
    const [key] = t.selected();
    expect(t.state().plan!.locations[key].geometry).toMatchObject({ width_m: 3 });
  });

  it('offers only bed types for a bed and uses the chosen one', async () => {
    const t = setupEditor();
    open(t);
    await waitFor(() => expect(listLocationTypes).toHaveBeenCalled());
    fireEvent.mouseDown(await screen.findByRole('combobox', { name: 'Bed type' }));
    expect(screen.getByRole('option', { name: 'Raised bed' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'Tent' })).toBeNull();
    fireEvent.click(screen.getByRole('option', { name: 'Raised bed' }));
    set('garden-plan-add-x', '14');
    set('garden-plan-add-y', '14');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-submit')));
    expect(t.state().plan!.locations[t.selected()[0]].location_type_key).toBe('raised_bed');
  });

  it('creates a garden object with the props its type needs', async () => {
    const t = setupEditor();
    open(t);
    fireEvent.click(screen.getByTestId('garden-plan-add-kind-object'));
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Object type' }));
    fireEvent.click(screen.getByRole('option', { name: 'trellis' }));
    set('garden-plan-add-x', '14');
    set('garden-plan-add-y', '14');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-submit')));
    const garden = t.state().plan!.gardenObjects[t.selected()[0]];
    expect(garden.object_type).toBe('trellis');
    expect(garden.props).toMatchObject({ object_type: 'trellis', height_m: 1.8 });
  });

  it('builds a polygon from a point list', () => {
    const t = setupEditor();
    open(t);
    fireEvent.click(screen.getByTestId('garden-plan-add-shape-polygon'));
    [
      ['0', '14', '15'],
      ['1', '17', '15'],
      ['2', '17', '18'],
    ].forEach(([i, x, y]) => {
      set(`garden-plan-add-point-${i}-x`, x);
      set(`garden-plan-add-point-${i}-y`, y);
    });
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-add-submit')));
    expect(t.state().plan!.locations[t.selected()[0]].geometry).toMatchObject({
      kind: 'polygon',
      points: [
        [14, 15],
        [17, 15],
        [17, 18],
      ],
    });
  });

  it('explains a refusal inside the dialog and creates nothing', () => {
    const t = setupEditor();
    open(t);
    set('garden-plan-add-x', '30');
    set('garden-plan-add-y', '14');
    fireEvent.click(screen.getByTestId('garden-plan-add-submit'));
    expect(screen.getByTestId('garden-plan-add-error')).toHaveTextContent(/sticks out/);
    expect(t.state().past).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-add-dialog')).toBeInTheDocument();
  });

  it('treats a number field that is not a number as invalid', () => {
    const t = setupEditor();
    open(t);
    set('garden-plan-add-width', 'wide');
    expect(screen.getByTestId('garden-plan-add-width')).toHaveAttribute('aria-invalid', 'true');
    fireEvent.click(screen.getByTestId('garden-plan-add-submit'));
    expect(screen.getByTestId('garden-plan-add-error')).toBeInTheDocument();
  });

  it('starts fresh at the middle of the view each time it opens', () => {
    const t = setupEditor();
    open(t);
    set('garden-plan-add-width', '9');
    fireEvent.click(screen.getByTestId('garden-plan-add-cancel'));
    open(t);
    expect(screen.getByTestId('garden-plan-add-width')).toHaveValue('2');
    expect(screen.getByTestId('garden-plan-add-x')).toHaveValue('10');
  });

  it('has no accessibility violations', async () => {
    const t = setupEditor();
    open(t);
    await expectNoA11yViolations(document.body);
  });
});

describe('type choice for drawn shapes (replaces the 2.4 placeholders)', () => {
  it('draws a garden object of the chosen type', async () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object')));
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Object type' }));
    fireEvent.click(screen.getByRole('option', { name: 'lamp' }));
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(15, 12)));
      fireEvent.pointerMove(t.canvas(), pointer(px(17, 14)));
      fireEvent.pointerUp(t.canvas(), pointer(px(17, 14)));
    });
    const garden = t.state().plan!.gardenObjects[t.selected()[0]];
    expect(garden.object_type).toBe('lamp');
    expect(garden.props).toMatchObject({ kind: 'ceiling', height_m: 2.5 });
  });

  it('draws a bed of the chosen bed type once the list is loaded', async () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-bed')));
    fireEvent.mouseDown(await screen.findByRole('combobox', { name: 'Bed type' }));
    fireEvent.click(screen.getByRole('option', { name: 'Raised bed' }));
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(15, 12)));
      fireEvent.pointerMove(t.canvas(), pointer(px(17, 14)));
      fireEvent.pointerUp(t.canvas(), pointer(px(17, 14)));
    });
    expect(t.state().plan!.locations[t.selected()[0]].location_type_key).toBe('raised_bed');
  });
});
