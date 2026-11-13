/**
 * A caption on the plan (REQ-053 GP-UX-071, #2913): both renderers draw a `text_label` as its text - centred in its
 * box, turned with it, as large as the box allows - and not as a box with an icon, a name label and a size. The box
 * outline appears only while the caption is selected.
 */
import { act, render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import type { GardenObject } from '../model/types';
import { KonvaPlanRenderer } from './KonvaPlanRenderer';
import { contextOf, installRecordingCanvas, nextFrame, uninstallRecordingCanvas } from './konvaTestCanvas';
import { captionOf, planPalette, shapeAriaLabel, shapeStyle } from './planDrawing';
import { shapeEntries } from './planIndex';
import { NO_SELECTION, TEST_LABELS, gardenObject, options, viewportAt } from './rendererTestKit';
import { buildScene } from './scene';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import type { RenderSelection } from './types';

const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

beforeAll(installRecordingCanvas);
afterAll(uninstallRecordingCanvas);

/** "Kräuterecke": a 3 × 0.5 m box anchored at (5, 6), turned by `rotation` degrees. */
function caption(rotation = 0): GardenObject {
  return gardenObject('cap', 5, 6, {
    object_type: 'text_label',
    label: 'Kräuterecke',
    geometry: { kind: 'rect', origin: [5, 6], width_m: 3, length_m: 0.5, rotation_deg: rotation },
    bbox: [5, 6, 8, 6.5],
    props: { object_type: 'text_label' },
  });
}

const plan = (rotation = 0) => smallPlan({ garden_objects: [caption(rotation)] });
const VIEW = viewportAt(0, 10, 100);
const LABELS = { ...TEST_LABELS, caption: ({ text, typeLabel }: { text: string; typeLabel: string }) => `${text}, ${typeLabel}` };

describe('the shared caption drawing', () => {
  it('centres the text in its box at the PDF font size and keeps the turn', () => {
    const entry = shapeEntries(plan(30)).find((item) => item.key === 'cap')!;
    const drawn = captionOf(entry)!;
    expect(drawn.text).toBe('Kräuterecke');
    expect(drawn.fontM).toBeCloseTo(0.4);
    expect(drawn.rotationDeg).toBe(30);
    // The centre of the turned box: origin + R(30°)·(1.5, 0.25).
    expect(drawn.x).toBeCloseTo(5 + 1.5 * Math.cos(Math.PI / 6) - 0.25 * Math.sin(Math.PI / 6), 3);
    expect(drawn.y).toBeCloseTo(6 + 1.5 * Math.sin(Math.PI / 6) + 0.25 * Math.cos(Math.PI / 6), 3);
  });

  it('draws no box unless selected, and names the caption by its text', () => {
    const entry = shapeEntries(plan()).find((item) => item.key === 'cap')!;
    const palette = planPalette(theme);
    expect(shapeStyle(entry, false, false, palette)).toMatchObject({ fill: 'none', stroke: 'none' });
    expect(shapeStyle(entry, true, false, palette)).toMatchObject({ fill: 'none', stroke: palette.selected });
    const scene = buildScene(plan(), VIEW, { selectedKeys: new Set(['cap']) }, {});
    const item = scene.shapes.find((shape) => shape.entry.key === 'cap')!;
    expect(shapeAriaLabel(item, LABELS)).toBe('Kräuterecke, text_label');
  });

  it('gives a caption no type icon, no name label and no printed size in the scene', () => {
    const scene = buildScene(plan(), viewportAt(4, 7, 400), { selectedKeys: new Set(['cap']) }, {});
    const item = scene.shapes.find((shape) => shape.entry.key === 'cap')!;
    expect(item.showIcon).toBe(false);
    expect(item.label).toBeNull();
    expect(item.showDimensions).toBe(false);
    // Every other object keeps its icon.
    const other = buildScene(
      smallPlan({ garden_objects: [gardenObject('tree', 5, 5)] }),
      viewportAt(4, 7, 400),
      NO_SELECTION,
      {},
    ).shapes.find((shape) => shape.entry.key === 'tree')!;
    expect(other.showIcon).toBe(true);
  });
});

describe('SvgPlanRenderer draws a caption as its text', () => {
  function mount(rotation = 0, selection: RenderSelection = NO_SELECTION) {
    const view = render(wrap(new SvgPlanRenderer().render(plan(rotation), VIEW, selection, options({ labels: LABELS }))));
    const node = view.container.querySelector('[data-plan-key="cap"]') as SVGGElement;
    return { ...view, node };
  }

  it('writes the text centred, at the box\'s font size, hidden from the accessibility tree (the group names it)', () => {
    const { node } = mount();
    const text = node.querySelector('[data-testid="garden-plan-caption-cap"]')!;
    expect(text.textContent).toBe('Kräuterecke');
    expect(text.getAttribute('font-size')).toBe('0.4000');
    expect(text.getAttribute('text-anchor')).toBe('middle');
    expect(text.getAttribute('transform')).toBeNull();
    expect(text.getAttribute('aria-hidden')).toBe('true');
    expect(node.getAttribute('aria-label')).toBe('Kräuterecke, text_label');
    // No name label and no type icon besides it.
    expect(node.querySelector('[data-testid="garden-plan-label-cap"]')).toBeNull();
    expect(node.querySelectorAll('path')).toHaveLength(1);
    expect(node.querySelector('path')!.getAttribute('stroke')).toBe('none');
  });

  it('turns the text with its box (mirrored: the drawing has y down) and outlines the selected box', () => {
    const { node } = mount(30, { selectedKeys: new Set(['cap']) });
    const text = node.querySelector('[data-testid="garden-plan-caption-cap"]')!;
    expect(text.getAttribute('transform')).toMatch(/^rotate\(-30 /);
    expect(node.querySelector('path')!.getAttribute('stroke')).not.toBe('none');
  });

  it('keeps markup in a caption as text', () => {
    const hostile = gardenObject('evil', 5, 6, { ...caption(), key: 'evil', label: '<img src=x onerror=alert(1)>' });
    const view = render(
      wrap(new SvgPlanRenderer().render(smallPlan({ garden_objects: [hostile] }), VIEW, NO_SELECTION, options())),
    );
    expect(view.container.querySelector('img')).toBeNull();
    expect(view.container.querySelector('[data-testid="garden-plan-caption-evil"]')!.textContent).toBe(
      '<img src=x onerror=alert(1)>',
    );
  });
});

describe('KonvaPlanRenderer draws a caption as its text', () => {
  it('writes the text (once per frame), turned about its centre, at the box\'s font size in pixels', async () => {
    const view = render(wrap(new KonvaPlanRenderer().render(plan(30), VIEW, NO_SELECTION, options({ labels: LABELS }))));
    await act(nextFrame);
    const canvas = view.container.querySelector<HTMLCanvasElement>('[data-testid="garden-plan-konva"] canvas')!;
    const layer = contextOf(canvas);
    const writes = layer.ops('fillText').filter((call) => call.args[0] === 'Kräuterecke');
    expect(writes.length).toBeGreaterThan(0);
    for (const write of writes) {
      expect(write.args.slice(1)).toEqual([0, 0]);
      // 0.4 m at 100 px/m.
      expect(write.font).toMatch(/^40px /);
    }
    // One turn per write, nothing else on the plan is turned.
    const rotate = layer.ops('rotate').map((call) => call.args[0] as number);
    expect(rotate).toHaveLength(writes.length);
    for (const angle of rotate) expect(angle).toBeCloseTo(-Math.PI / 6);
    // The caption is no name label: its text is never written a second time at the label size.
    expect(layer.ops('fillText').filter((call) => call.args[0] === 'Kräuterecke' && !String(call.font).startsWith('40px'))).toEqual([]);
  });
});
