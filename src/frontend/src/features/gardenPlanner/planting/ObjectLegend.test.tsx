/**
 * REQ-053 WP 10.6 (#2827, GP-FR-180, GP-UX-005): the object legend in the side panel's tab "Ebenen".
 *
 * Pinned: one entry per class the plan holds, in the order of the object menu, with its count and how many lie outside
 * the property; nothing for a class the plan does not hold; a text when there are no objects; it sits in the tab
 * "Ebenen" and hides with the legend switch; axe is clean.
 */
import { cleanup, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { gardenObject } from '@/test/gardenPlanFixtures';
import type { GardenObject, GardenObjectType } from '../model/types';
import { openPanelTab, setupEditor } from '../editor/editorTestKit';
import ObjectLegend from './ObjectLegend';

afterEach(() => cleanup());

const LABELS: Partial<Record<GardenObjectType, string>> = { tree: 'Tree', window: 'Window', lamp: 'Lamp' };
const label = (type: GardenObjectType) => LABELS[type] ?? type;

function objects(): Record<string, GardenObject> {
  return {
    l1: gardenObject('l1', 1, 1, {
      object_type: 'lamp',
      geometry: { kind: 'point', origin: [1, 1] },
      props: { object_type: 'lamp', kind: 'ceiling', height_m: 2.5 },
    }),
    t1: gardenObject('t1', 5, 5),
    t2: gardenObject('t2', 8, 5, { off_site: true }),
    w1: gardenObject('w1', 2, 9, {
      object_type: 'window',
      geometry: { kind: 'polyline', width_m: 0.1, points: [[2, 9], [3, 9]] },
      props: { object_type: 'window' },
    }),
  };
}

describe('object legend (GP-FR-180)', () => {
  it('lists each class the plan holds, in menu order, with its count and the off-site share', () => {
    renderWithProviders(<ObjectLegend objects={objects()} objectTypeLabel={label} />);

    const items = screen.getAllByRole('listitem');
    expect(items.map((item) => item.getAttribute('data-testid'))).toEqual([
      'garden-plan-legend-object-tree',
      'garden-plan-legend-object-window',
      'garden-plan-legend-object-lamp',
    ]);
    expect(screen.getByTestId('garden-plan-legend-object-tree')).toHaveTextContent(
      'Tree (2) - 1 of them outside the property',
    );
    expect(screen.getByTestId('garden-plan-legend-object-window')).toHaveTextContent('Window (1)');
    expect(screen.queryByTestId('garden-plan-legend-object-door')).not.toBeInTheDocument();
  });

  it('says so when the plan holds no objects', () => {
    renderWithProviders(<ObjectLegend objects={{}} objectTypeLabel={label} />);

    expect(screen.queryAllByRole('listitem')).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-legend-objects')).toHaveTextContent(/no objects/);
  });

  it('has no axe violations', async () => {
    renderWithProviders(<ObjectLegend objects={objects()} objectTypeLabel={label} />);

    await expectNoA11yViolations(screen.getByTestId('garden-plan-legend-objects'));
  });
});

describe('in the tab "Ebenen"', () => {
  it('shows the legend of the plan objects and hides it with the legend switch', () => {
    setupEditor();
    openPanelTab('layers');

    expect(screen.getByTestId('garden-plan-legend-object-tree')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('garden-plan-legend-toggle'));
    expect(screen.queryByTestId('garden-plan-legend-objects')).not.toBeInTheDocument();
  });
});
