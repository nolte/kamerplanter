import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import { NO_SELECTION, bed, options, viewportAt } from './rendererTestKit';
import type { RenderOptions, UnderlayRenderEntry } from './types';

/** The underlay layer (REQ-053 GP-FR-033, WP 7.15): below every object, decorative, only when it is given. */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

const ENTRY: UnderlayRenderEntry = {
  href: 'blob:http://localhost/under',
  widthPx: 800,
  heightPx: 400,
  underlay: {
    attachment_key: 'att_1',
    calibration: { p1_px: [100, 200], p2_px: [500, 200], distance_m: 4 },
    origin: [1, 9],
    rotation_deg: 0,
    opacity: 0.4,
  },
};

function mount(extra: Partial<RenderOptions>) {
  const model = smallPlan({ locations: [bed('loc_a', 1, 1)], garden_objects: [], slots: [], plants: [] });
  const view = render(
    wrap(new SvgPlanRenderer().render(model, viewportAt(0, 10, 60), NO_SELECTION, options(extra))),
  );
  return view.container.querySelector('svg') as SVGSVGElement;
}

describe('underlay layer', () => {
  it('draws nothing while the layer is off', () => {
    expect(mount({}).querySelector('[data-plan-underlay]')).toBeNull();
  });

  it('draws the picture first, at the calibrated scale, decorative only', () => {
    const svg = mount({ underlayLayer: ENTRY });
    const layer = svg.querySelector('[data-plan-underlay]') as SVGGElement;

    expect(layer.getAttribute('transform')).toBe('translate(1 -9) rotate(0) scale(0.01)');
    expect(layer.getAttribute('aria-hidden')).toBe('true');
    expect(layer.getAttribute('pointer-events')).toBe('none');
    const image = layer.querySelector('image') as SVGImageElement;
    expect(image.getAttribute('href')).toBe(ENTRY.href);
    expect(image.getAttribute('opacity')).toBe('0.4');
    // below every object: nothing precedes it in the canvas
    expect(svg.firstElementChild).toBe(layer);
  });

  it('draws nothing for a calibration that gives no scale', () => {
    const broken = { ...ENTRY, underlay: { ...ENTRY.underlay, calibration: { ...ENTRY.underlay.calibration, distance_m: 0 } } };
    expect(mount({ underlayLayer: broken }).querySelector('[data-plan-underlay]')).toBeNull();
  });
});
