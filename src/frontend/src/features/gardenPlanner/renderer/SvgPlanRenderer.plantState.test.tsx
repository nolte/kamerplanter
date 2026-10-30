import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import {
  NO_SELECTION,
  TEST_LABELS,
  bed,
  options,
  plantedBed,
  viewportAt,
} from './rendererTestKit';
import type { PlantMarkerState } from './types';

/**
 * The state channels of a plant marker and the red outline of a refused object (REQ-053 WP 3.7:
 * GP-UX-059/060/062, GP-FR-190 cluster summary, GP-UX-017).
 */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

function state(overrides: Partial<PlantMarkerState> = {}): PlantMarkerState {
  return {
    lifecycle: 'active',
    badge: null,
    initial: 'T',
    progress: 0.5,
    ariaLabel: 'Tomato, Flowering',
    ...overrides,
  };
}

function model(count = 3) {
  const { slots, plants } = plantedBed('loc_a', 1, 1, count, 0.5);
  return smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] });
}

function mount(pxPerM: number, opts = options()) {
  const view = render(
    wrap(new SvgPlanRenderer().render(model(), viewportAt(0, 10, pxPerM), NO_SELECTION, opts)),
  );
  return view.container.querySelector('svg') as SVGSVGElement;
}

describe('plant marker channels', () => {
  it('uses the state label, the initial and one badge on a stated marker of the entered bed', () => {
    const svg = mount(
      100,
      options({
        enteredLocationKey: 'loc_a',
        plantStates: { loc_a_p0: state({ badge: 'overdue', ariaLabel: 'Tomato, 2 tasks overdue' }) },
      }),
    );
    const marker = svg.querySelector('g[data-plan-key="loc_a_p0"]') as SVGGElement;
    expect(marker.getAttribute('aria-label')).toBe('Tomato, 2 tasks overdue');
    expect(marker.querySelector('text')?.textContent).toBe('T');
    expect(marker.querySelectorAll('[data-plan-badge-reason]')).toHaveLength(1);
    // the plants without a state keep the plain label and no badge
    const plain = svg.querySelector('g[data-plan-key="loc_a_p1"]') as SVGGElement;
    expect(plain.getAttribute('aria-label')).toBe('Plant LOC_A-1');
    expect(plain.querySelector('[data-plan-badge-reason]')).toBeNull();
  });

  it('draws the phase progress arc only from the detail zoom on (R-014)', () => {
    const opts = options({ enteredLocationKey: 'loc_a', plantStates: { loc_a_p0: state() } });
    expect(mount(99, opts).querySelector('[data-plan-progress]')).toBeNull();
    expect(mount(100, opts).querySelector('[data-plan-progress="0.50"]')).not.toBeNull();
  });

  it('points the marker at the open bubble with aria-describedby (GP-UX-058)', () => {
    const svg = mount(
      100,
      options({
        enteredLocationKey: 'loc_a',
        plantStates: { loc_a_p0: state() },
        describedPlantKey: 'loc_a_p0',
      }),
    );
    expect(svg.querySelector('g[data-plan-key="loc_a_p0"]')?.getAttribute('aria-describedby')).toBe('gp-plant-info');
    expect(svg.querySelector('g[data-plan-key="loc_a_p1"]')?.getAttribute('aria-describedby')).toBeNull();
  });

  it('summarises a dense bed as "n plants, m need attention" with the top reason (GP-FR-190, GP-UX-060)', () => {
    const labels = {
      ...TEST_LABELS,
      clusterSummary: ({ count, attention }: { count: number; attention: number }) =>
        `${count} plants - ${attention} need attention`,
    };
    const svg = mount(
      10, // 0.5 m = 5 px: below the marker threshold, one cluster
      options({
        labels,
        plantStates: {
          loc_a_p0: state({ badge: 'water' }),
          loc_a_p1: state({ badge: 'problem' }),
          loc_a_p2: state(),
        },
      }),
    );
    const cluster = svg.querySelector('[data-plan-cluster="loc_a"]') as SVGGElement;
    expect(cluster.getAttribute('aria-label')).toBe('3 plants - 2 need attention');
    // the badge shows the highest priority among them: problem beats water
    expect(cluster.querySelector('[data-plan-badge-reason]')?.getAttribute('data-plan-badge-reason')).toBe('problem');
  });

  it('keeps the plain cluster text when no state of the bed is known', () => {
    const svg = mount(10, options());
    const cluster = svg.querySelector('[data-plan-cluster="loc_a"]') as SVGGElement;
    expect(cluster.getAttribute('aria-label')).toBe(TEST_LABELS.cluster({ count: 3 }));
    expect(cluster.querySelector('[data-plan-badge-reason]')).toBeNull();
  });
});

describe('objects a refused save named (GP-UX-017)', () => {
  it('draws a heavy red outline on exactly those objects', () => {
    const svg = mount(
      100,
      options({ invalidKeys: new Set(['loc_a']) }),
    );
    const flagged = svg.querySelector('g[data-plan-key="loc_a"]') as SVGGElement;
    expect(flagged.getAttribute('data-plan-invalid')).toBe('true');
    const outline = flagged.querySelector('path') as SVGPathElement;
    expect(outline.getAttribute('stroke')).toBe(theme.palette.error.main);
    expect(Number(outline.getAttribute('stroke-width'))).toBeGreaterThan(3);
    const other = svg.querySelector('g[data-plan-key="__boundary__"]');
    expect(other?.getAttribute('data-plan-invalid')).toBeNull();
  });
});

describe('plant-state layer on the overview plan (GP-UX-061, #2488)', () => {
  // The bed is not entered: before #2488 the overview never drew a state channel.
  const layerStates = {
    loc_a_p0: state({ badge: 'overdue', lifecycle: 'harvesting' }),
    loc_a_p1: state(),
    loc_a_p2: state({ lifecycle: 'sown' }),
  };

  it('draws ring, initial and badge of every stated plant at marker LOD with the layer on, decoratively', () => {
    const svg = mount(
      30, // 0.5 m = 15 px: marker LOD
      options({
        plantStateLayer: { states: layerStates, attentionOnly: false },
        phaseColors: { ph_flower: '#AB47BC' },
      }),
    );
    const markers = [...svg.querySelectorAll('g[data-plan-state-layer="true"]')];
    expect(markers.map((m) => m.getAttribute('data-plan-key'))).toEqual(['loc_a_p0', 'loc_a_p1', 'loc_a_p2']);
    expect(markers.every((m) => m.getAttribute('aria-hidden') === 'true' && !m.hasAttribute('role'))).toBe(true);
    expect(markers.map((m) => m.querySelector('[data-plan-lifecycle]')?.getAttribute('data-plan-lifecycle'))).toEqual([
      'harvesting',
      'active',
      'sown',
    ]);
    expect(svg.querySelectorAll('[data-plan-badge-reason]')).toHaveLength(1);
    expect(svg.querySelector('[data-plan-badge-reason]')?.getAttribute('data-plan-badge-reason')).toBe('overdue');
    expect(markers[1].querySelector('text')?.textContent).toBe('T');
    // nothing is focusable on the overview but the objects: the bubble and the focus stay in the bed view
    expect(svg.querySelectorAll('[tabindex="0"]')).toHaveLength(1);
    expect(svg.querySelector('[data-plan-markers="loc_a"]')).toBeNull();
  });

  it('draws no channel on the overview without the layer, even with states at hand', () => {
    const svg = mount(30, options({ plantStates: layerStates }));
    expect(svg.querySelector('[data-plan-state-layer]')).toBeNull();
    expect(svg.querySelector('[data-plan-lifecycle]')).toBeNull();
    expect(svg.querySelector('[data-plan-badge-reason]')).toBeNull();
    expect(svg.querySelector('[data-plan-markers="loc_a"]')).not.toBeNull();
  });

  it('keeps only the plant with a badge under "only plants that need attention"', () => {
    const svg = mount(30, options({ plantStateLayer: { states: layerStates, attentionOnly: true } }));
    const markers = [...svg.querySelectorAll('g[data-plan-state-layer="true"]')];
    expect(markers.map((m) => m.getAttribute('data-plan-key'))).toEqual(['loc_a_p0']);
  });

  it('counts the badged plants in the cluster below marker LOD and hides a calm cluster under the filter', () => {
    const labels = {
      ...TEST_LABELS,
      clusterSummary: ({ count, attention }: { count: number; attention: number }) =>
        `${count} plants - ${attention} need attention`,
    };
    const svg = mount(10, options({ labels, plantStateLayer: { states: layerStates, attentionOnly: false } }));
    const cluster = svg.querySelector('[data-plan-cluster="loc_a"]') as SVGGElement;
    expect(cluster.getAttribute('aria-label')).toBe('3 plants - 1 need attention');
    expect(cluster.querySelector('[data-plan-badge-reason]')?.getAttribute('data-plan-badge-reason')).toBe('overdue');
    const allCalm = { loc_a_p0: state(), loc_a_p1: state(), loc_a_p2: state() };
    const calm = mount(10, options({ labels, plantStateLayer: { states: allCalm, attentionOnly: true } }));
    expect(calm.querySelector('[data-plan-cluster="loc_a"]')).toBeNull();
  });

  it('names the total and the attention count under the filter, and draws only the kept plants', () => {
    const labels = {
      ...TEST_LABELS,
      clusterSummary: ({ count, attention }: { count: number; attention: number }) =>
        `${count} plants - ${attention} need attention`,
    };
    const svg = mount(10, options({ labels, plantStateLayer: { states: layerStates, attentionOnly: true } }));
    const cluster = svg.querySelector('[data-plan-cluster="loc_a"]') as SVGGElement;
    // 3 plants in the bed, 1 of them needs attention: swapping the two would read "1 plants - 3 need attention"
    expect(cluster.getAttribute('aria-label')).toBe('3 plants - 1 need attention');
    expect(cluster.querySelector('text')?.textContent).toBe('1');
  });
});
