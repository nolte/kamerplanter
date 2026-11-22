/**
 * REQ-053 WP 9.14 (#2754, GP-FR-111): the water-source fields of the properties panel.
 *
 * Pinned: kind, capacity and last refill are offered - exactly the three fields `WaterSourceProps` carries; every
 * change is ONE `update_fields` of the whole props object through the plan (never a PATCH of its own); a value the
 * server would refuse (capacity <= 0) is not committed; clearing the capacity sends `null`.
 */
import { act, cleanup, fireEvent, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import i18n from '@/i18n/i18n';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import type { PlanOperation, WaterSourceProps } from '../model/types';
import { setupEditor } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';
import { WaterSourceFields } from './WaterSourceFields';

afterEach(() => cleanup());

const ORIGINAL_LANGUAGE = i18n.language;

const BARREL: WaterSourceProps = {
  object_type: 'water_source',
  water_source_kind: 'rain_barrel',
  capacity_liters: 300,
  last_refilled_at: '2026-10-01T00:00:00Z',
};

function renderFields(props: WaterSourceProps = BARREL, disabled = false) {
  const onCommit = vi.fn<(ops: PlanOperation[], label: string) => void>();
  renderWithProviders(<WaterSourceFields objectKey="ws1" props={props} disabled={disabled} onCommit={onCommit} />);
  return onCommit;
}

const propsOf = (ops: PlanOperation[]) => {
  const [op] = ops;
  if (op.op !== 'update_fields' || op.entity !== 'garden_object') throw new Error(`unexpected op ${op.op}`);
  return { key: op.key, props: op.fields.props };
};

describe('water source fields (GP-FR-111)', () => {
  it('shows the stored kind, capacity and last refill', () => {
    renderFields();

    expect(screen.getByTestId('garden-plan-panel-water-source-kind')).toHaveValue('rain_barrel');
    expect(screen.getByTestId('garden-plan-panel-water-source-capacity')).toHaveValue('300');
    expect(screen.getByTestId('garden-plan-panel-water-source-refilled')).toHaveValue('2026-10-01');
  });

  it.each([
    ['de', '12,5'],
    ['en', '12.5'],
  ])('writes a fractional capacity with the separator of %s and commits nothing unchanged (#2905)', async (language, shown) => {
    await act(() => i18n.changeLanguage(language));
    try {
      const onCommit = renderFields({ ...BARREL, capacity_liters: 12.5 });
      const capacity = screen.getByTestId('garden-plan-panel-water-source-capacity');
      expect(capacity).toHaveValue(shown);
      fireEvent.blur(capacity);
      expect(onCommit).not.toHaveBeenCalled();
    } finally {
      cleanup();
      await act(() => i18n.changeLanguage(ORIGINAL_LANGUAGE));
    }
  });

  it('commits a new kind as one update_fields with the whole props object', async () => {
    const user = userEvent.setup();
    const onCommit = renderFields();

    await user.click(screen.getByRole('combobox', { name: 'Kind of water source' }));
    await user.click(within(screen.getByRole('listbox')).getByRole('option', { name: 'Cistern' }));

    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(propsOf(onCommit.mock.calls[0][0])).toEqual({
      key: 'ws1',
      props: { ...BARREL, water_source_kind: 'cistern' },
    });
    expect(onCommit.mock.calls[0][1]).toBe('edit');
  });

  it('commits a typed capacity on blur, accepts a decimal comma and clears to null', () => {
    const onCommit = renderFields();
    const capacity = screen.getByTestId('garden-plan-panel-water-source-capacity');

    fireEvent.change(capacity, { target: { value: '1000,5' } });
    fireEvent.blur(capacity);
    fireEvent.change(capacity, { target: { value: '' } });
    fireEvent.blur(capacity);

    expect(onCommit.mock.calls.map((call) => propsOf(call[0]).props?.capacity_liters)).toEqual([1000.5, null]);
  });

  it('refuses a capacity of zero or less and commits nothing', () => {
    const onCommit = renderFields();
    const capacity = screen.getByTestId('garden-plan-panel-water-source-capacity');

    fireEvent.change(capacity, { target: { value: '0' } });
    fireEvent.blur(capacity);

    expect(onCommit).not.toHaveBeenCalled();
    expect(screen.getByText('Enter a capacity above 0 litres, or leave the field empty.')).toBeInTheDocument();
  });

  it('commits the day of the last refill as midnight UTC, and an emptied field as null', () => {
    const onCommit = renderFields();
    const refilled = screen.getByTestId('garden-plan-panel-water-source-refilled');

    fireEvent.change(refilled, { target: { value: '2026-11-02' } });
    fireEvent.blur(refilled);
    fireEvent.change(refilled, { target: { value: '' } });
    fireEvent.blur(refilled);

    expect(onCommit.mock.calls.map((call) => propsOf(call[0]).props?.last_refilled_at)).toEqual([
      '2026-11-02T00:00:00Z',
      null,
    ]);
  });

  it('shows the UTC day of a stored instant with an offset, not the day written in the string', () => {
    renderFields({ ...BARREL, last_refilled_at: '2026-11-02T23:30:00-02:00' });

    expect(screen.getByTestId('garden-plan-panel-water-source-refilled')).toHaveValue('2026-11-03');
  });

  it('caps the day at today (UTC) and commits no day in the future', () => {
    const onCommit = renderFields();
    const refilled = screen.getByTestId('garden-plan-panel-water-source-refilled');
    const tomorrow = new Date(Date.now() + 86_400_000).toISOString().slice(0, 10);

    expect(refilled).toHaveAttribute('max', new Date().toISOString().slice(0, 10));
    fireEvent.change(refilled, { target: { value: tomorrow } });
    fireEvent.blur(refilled);

    expect(onCommit).not.toHaveBeenCalled();
    expect(screen.getByText('That day is in the future. Pick today or an earlier day.')).toBeInTheDocument();
  });

  it('does not commit an unchanged value', () => {
    const onCommit = renderFields();
    const capacity = screen.getByTestId('garden-plan-panel-water-source-capacity');

    fireEvent.change(capacity, { target: { value: '300' } });
    fireEvent.blur(capacity);
    fireEvent.blur(screen.getByTestId('garden-plan-panel-water-source-refilled'));

    expect(onCommit).not.toHaveBeenCalled();
  });

  it('takes no input on a locked object', () => {
    renderFields(BARREL, true);

    expect(screen.getByTestId('garden-plan-panel-water-source-capacity')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-panel-water-source-refilled')).toBeDisabled();
  });

  it('has no axe violations', async () => {
    renderFields();

    await expectNoA11yViolations(screen.getByTestId('garden-plan-panel-water-source'));
  });
});

describe('in the properties panel', () => {
  function planWithWaterSource() {
    const plan = testPlan();
    const tree = plan.gardenObjects.t1;
    return {
      ...plan,
      gardenObjects: {
        ...plan.gardenObjects,
        ws1: {
          ...tree,
          key: 'ws1',
          object_type: 'water_source' as const,
          label: 'Barrel',
          parent_location_key: null,
          geometry: { kind: 'point' as const, origin: [17, 17] as [number, number] },
          bbox: [16.75, 16.75, 17.25, 17.25] as [number, number, number, number],
          props: { object_type: 'water_source' as const, water_source_kind: 'tap' as const },
        },
      },
    };
  }

  it('shows the fields for a selected water source and writes through the plan', () => {
    const t = setupEditor({ plan: planWithWaterSource() });
    t.click(17, 17);

    expect(screen.getByTestId('garden-plan-panel-water-source')).toBeInTheDocument();
    const capacity = screen.getByTestId('garden-plan-panel-water-source-capacity');
    t.after(() => {
      fireEvent.change(capacity, { target: { value: '200' } });
      fireEvent.blur(capacity);
    });

    const queue = t.state().pending;
    const pending = queue[queue.length - 1]?.op;
    expect(pending).toMatchObject({
      op: 'update_fields',
      entity: 'garden_object',
      key: 'ws1',
      fields: { props: { object_type: 'water_source', water_source_kind: 'tap', capacity_liters: 200 } },
    });
  });

  it('offers no water-source fields for another object type', () => {
    const t = setupEditor({ plan: planWithWaterSource() });
    t.click(9, 9);

    expect(screen.getByTestId('garden-plan-panel-form')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-panel-water-source')).not.toBeInTheDocument();
  });
});
