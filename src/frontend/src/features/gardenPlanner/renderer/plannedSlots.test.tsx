import { act, render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { KonvaPlanRenderer } from './KonvaPlanRenderer';
import {
  contextOf,
  installRecordingCanvas,
  nextFrame,
  uninstallRecordingCanvas,
} from './konvaTestCanvas';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import { bed, options, plantedBed, viewportAt } from './rendererTestKit';

/**
 * REQ-053 GP-FR-074: a reserved, still empty position (`planned_from` of `GET /plan`) is drawn dashed with its first
 * day, in both renderers, and its name says so. A free position and a planted one carry no date.
 */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

beforeAll(installRecordingCanvas);
afterAll(uninstallRecordingCanvas);

/** Bed loc_a with three slots: s0 reserved from 22 April, s1 free, s2 planted (its reservation is consumed). */
function model() {
  const { slots, plants } = plantedBed('loc_a', 1, 1, 3, 0.5);
  slots[0].planned_from = '2027-04-22';
  slots[2].planned_from = '2027-04-01';
  return smallPlan({
    slots,
    plants: plants.filter((plant) => plant.slot_key === slots[2].key),
    locations: [bed('loc_a', 1, 1)],
    garden_objects: [],
  });
}

const entered = () => options({ enteredLocationKey: 'loc_a' });

describe('SvgPlanRenderer - reserved positions (GP-FR-074)', () => {
  it('draws the reserved empty position dashed with its date and names it reserved', () => {
    const { container } = render(
      wrap(new SvgPlanRenderer().render(model(), viewportAt(0, 10, 100), { selectedKeys: new Set() }, entered())),
    );
    const reserved = container.querySelector('g[data-plan-key="loc_a_s0"]') as SVGGElement;
    expect(reserved.getAttribute('aria-label')).toBe('Slot LOC_A_0, planned from 2027-04-22');
    expect(reserved.querySelector('circle')?.getAttribute('stroke-dasharray')).toBe('2 2');
    const date = reserved.querySelector('[data-plan-planned-from]');
    expect(date?.textContent).toBe('from 2027-04-22');
    expect(date?.getAttribute('aria-hidden')).toBe('true');

    const free = container.querySelector('g[data-plan-key="loc_a_s1"]') as SVGGElement;
    expect(free.getAttribute('aria-label')).toBe('Slot LOC_A_1');
    expect(free.querySelector('[data-plan-planned-from]')).toBeNull();
    // The planted slot shows the plant, not the date of its consumed reservation.
    expect(container.querySelectorAll('[data-plan-planned-from]')).toHaveLength(1);
  });

  it('draws no date without a date label', () => {
    const labels = { ...entered().labels, plannedDate: undefined };
    const { container } = render(
      wrap(
        new SvgPlanRenderer().render(model(), viewportAt(0, 10, 100), { selectedKeys: new Set() }, {
          ...entered(),
          labels,
        }),
      ),
    );
    expect(container.querySelector('[data-plan-planned-from]')).toBeNull();
  });
});

describe('KonvaPlanRenderer - reserved positions (GP-FR-074)', () => {
  it('writes the date beside the dashed ring of the reserved position only', async () => {
    const view = render(
      wrap(new KonvaPlanRenderer().render(model(), viewportAt(0, 10, 100), { selectedKeys: new Set() }, entered())),
    );
    await act(nextFrame);
    const canvas = view.container.querySelector<HTMLCanvasElement>('[data-testid="garden-plan-konva"] canvas');
    const plan = contextOf(canvas as HTMLCanvasElement);
    const dates = plan.ops('fillText').filter((call) => String(call.args[0]).startsWith('from '));
    expect(new Set(dates.map((call) => call.args[0]))).toEqual(new Set(['from 2027-04-22']));
    // Slot 0 sits at (1.1, 1.5) -> (110, 850) px; the date starts right of the ring, on its centre line.
    expect(dates[0].args[1] as number).toBeGreaterThan(110);
    expect(dates[0].args[2]).toBe(850);
    // The ring itself stays dashed.
    const dashed = plan.ops('stroke').filter((call) => call.lineDash.join(',') === '2,2');
    expect(dashed.length).toBeGreaterThan(0);
    expect(view.container.querySelector('[data-plan-key="loc_a_s0"]')).toHaveAttribute(
      'aria-label',
      'Slot LOC_A_0, planned from 2027-04-22',
    );
  });
});
