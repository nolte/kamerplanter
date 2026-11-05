import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme, type Theme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { smallPlan } from '@/test/gardenPlanFixtures';
import {
  COMPANION_HIT_WIDTH_PX,
  COMPANION_LINE_CAP,
  COMPANION_LINE_STYLES,
  COMPANION_STATUSES,
  cullCompanionLines,
  type CompanionLine,
  type CompanionLineStatus,
} from './companionLines';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import { NO_SELECTION, bed, options, viewportAt } from './rendererTestKit';
import type { RenderOptions } from './types';

/** The companion-planting layer of the plan (REQ-053 GP-FR-134, WP 8.16). */

/** A view of 10 x 10 m: model (0, 10) top-left, 100 px/m, 1000 x 1000 px. */
const VIEW = viewportAt(0, 10, 100);

function line(id: string, status: CompanionLineStatus, x = 1, y = 1, length = 0.3): CompanionLine {
  return { id, a: [x, y], b: [x + length, y], status };
}

/** `count` lines inside VIEW, cycling through the statuses (unknown first, so the ordering is not free). */
function manyLines(count: number): CompanionLine[] {
  const order: CompanionLineStatus[] = ['unknown', 'compatible', 'incompatible'];
  return Array.from({ length: count }, (_, i) =>
    line(`bed:s${i}|s${i + 1}`, order[i % 3], 0.5 + (i % 30) * 0.3, 0.5 + Math.floor(i / 30) * 0.3),
  );
}

async function mount(extra: Partial<RenderOptions>, theme: Theme = createTheme()) {
  const model = smallPlan({ locations: [bed('loc_a', 1, 1)], garden_objects: [], slots: [], plants: [] });
  const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;
  const view = render(wrap(new SvgPlanRenderer().render(model, VIEW, NO_SELECTION, options(extra))));
  if (extra.companionLayer && extra.companionLayer.lines.length > 0) {
    // The layer is its own chunk: wait until it is in.
    await screen.findByTestId('garden-plan-companion-layer');
  }
  return view;
}

const drawn = (container: HTMLElement) => [...container.querySelectorAll('[data-companion-edge]')];

describe('cullCompanionLines', () => {
  it('keeps at most 500 of more than 500 lines in view, incompatible before compatible before unknown', () => {
    const lines = manyLines(900);
    const culled = cullCompanionLines(lines, VIEW);
    expect(COMPANION_LINE_CAP).toBe(500);
    expect(culled.candidates).toBe(900);
    expect(culled.lines).toHaveLength(500);
    expect(culled.capped).toBe(true);
    const statuses = culled.lines.map((entry) => entry.status);
    // all 300 incompatible lines survive the cap, then 200 of the 300 compatible ones; the unknown ones are cut
    expect(statuses.filter((status) => status === 'incompatible')).toHaveLength(300);
    expect(statuses.filter((status) => status === 'compatible')).toHaveLength(200);
    expect(statuses.filter((status) => status === 'unknown')).toHaveLength(0);
    expect(statuses.indexOf('compatible')).toBe(300);
    expect(statuses.lastIndexOf('incompatible')).toBe(299);
  });

  it('drops lines outside the viewport plus margin before the cap counts them', () => {
    const inView = line('in', 'compatible', 2, 2);
    const farAway = line('far', 'incompatible', 50, 50);
    // A line crossing the view with both ends outside it is still drawn.
    const crossing: CompanionLine = { id: 'cross', a: [-5, 5], b: [15, 5], status: 'unknown' };
    const culled = cullCompanionLines([inView, farAway, crossing], VIEW);
    expect(culled.lines.map((entry) => entry.id)).toEqual(['in', 'cross']);
    expect(culled.candidates).toBe(2);
    expect(culled.capped).toBe(false);
  });
});

describe('companion layer', () => {
  it('draws nothing while the layer is off or empty', async () => {
    const off = await mount({});
    expect(off.container.querySelector('[data-testid="garden-plan-companion-layer"]')).toBeNull();
    off.unmount();
    const empty = await mount({ companionLayer: { lines: [] } });
    expect(empty.container.querySelector('[data-testid="garden-plan-companion-layer"]')).toBeNull();
  });

  it('puts at most 500 lines into the DOM for more than 500 candidates', async () => {
    const { container } = await mount({ companionLayer: { lines: manyLines(800) } });
    const layer = screen.getByTestId('garden-plan-companion-layer');
    expect(layer.getAttribute('data-companion-candidates')).toBe('800');
    expect(drawn(container)).toHaveLength(500);
    expect(container.querySelectorAll('line.gp-companion-line')).toHaveLength(500);
  });

  it('tells the statuses apart by dash pattern, not by colour alone (greyscale)', async () => {
    // A theme in which green, red and the neutral grey are the same grey: only the dash can tell them apart.
    const grey = '#757575';
    const greyscale = createTheme({
      palette: {
        success: { main: grey, dark: grey, light: grey },
        error: { main: grey, dark: grey, light: grey },
        text: { secondary: grey },
      },
    });
    const lines = COMPANION_STATUSES.map((status, i) => line(`bed:${status}`, status, 1, 1 + i));
    const { container } = await mount({ companionLayer: { lines } }, greyscale);
    const visible = (status: CompanionLineStatus) =>
      container.querySelector(`[data-companion-status="${status}"] line.gp-companion-line`) as SVGLineElement;
    const strokes = COMPANION_STATUSES.map((status) => visible(status).getAttribute('stroke'));
    expect(new Set(strokes).size).toBe(1);
    const dashes = COMPANION_STATUSES.map((status) => visible(status).getAttribute('stroke-dasharray'));
    expect(new Set(dashes).size).toBe(3);
    // solid = compatible, dashed = incompatible, dotted (a near-zero dash with round caps) = unknown
    expect(visible('compatible').getAttribute('stroke-dasharray')).toBe('none');
    const [dash, gap] = (visible('incompatible').getAttribute('stroke-dasharray') ?? '').split(' ').map(Number);
    expect(dash).toBeGreaterThanOrEqual(4);
    expect(gap).toBeGreaterThanOrEqual(3);
    const [dot, space] = (visible('unknown').getAttribute('stroke-dasharray') ?? '').split(' ').map(Number);
    expect(dot).toBeLessThan(1);
    expect(space).toBeGreaterThanOrEqual(3);
    expect(visible('unknown').getAttribute('stroke-linecap')).toBe('round');
    expect(COMPANION_LINE_STYLES.unknown.dash).not.toBe(COMPANION_LINE_STYLES.incompatible.dash);
  });

  it('colours the statuses with the theme: green, red and the neutral grey', async () => {
    const theme = createTheme();
    const lines = COMPANION_STATUSES.map((status, i) => line(`bed:${status}`, status, 1, 1 + i));
    const { container } = await mount({ companionLayer: { lines } }, theme);
    const stroke = (status: CompanionLineStatus) =>
      container.querySelector(`[data-companion-status="${status}"] line.gp-companion-line`)?.getAttribute('stroke');
    expect(stroke('compatible')).toBe(theme.palette.success.dark);
    expect(stroke('incompatible')).toBe(theme.palette.error.main);
    expect(stroke('unknown')).toBe(theme.palette.text.secondary);
  });

  it('is decorative for assistive technology and gives every line a 24 px pointer target', async () => {
    const { container } = await mount({ companionLayer: { lines: [line('bed:a|b', 'incompatible')] } });
    const layer = screen.getByTestId('garden-plan-companion-layer');
    expect(layer.getAttribute('aria-hidden')).toBe('true');
    const hit = container.querySelector('[data-companion-edge="bed:a|b"] line.gp-companion-hit') as SVGLineElement;
    expect(Number(hit.getAttribute('stroke-width'))).toBeGreaterThanOrEqual(24);
    expect(COMPANION_HIT_WIDTH_PX).toBe(24);
    expect(hit.getAttribute('pointer-events')).toBe('stroke');
    expect(hit.getAttribute('vector-effect')).toBe('non-scaling-stroke');
    const visible = container.querySelector('[data-companion-edge="bed:a|b"] line.gp-companion-line');
    expect(visible?.getAttribute('pointer-events')).toBe('none');
    // in drawing coordinates: metres, y negated
    expect(visible?.getAttribute('y1')).toBe('-1');
  });

  it('has no accessibility violations with the layer on', async () => {
    const { container } = await mount({ companionLayer: { lines: manyLines(12) } });
    await expectNoA11yViolations(container, { minImpact: 'serious' });
  });
});
