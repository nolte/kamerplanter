/**
 * The PNG export pipeline (REQ-053 GP-FR-144): the serialized SVG carries the computed styles inline, the factor
 * sets the image size, the canvas cap reduces the factor, and the watermark is drawn only when it is chosen.
 * jsdom has no layout and no canvas, so the computed styles come from a resolver that does what a browser does
 * (CSS variables resolved, inherited values passed down) and the canvas is a recording double.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  MAX_CANVAS_AREA_PX,
  MAX_CANVAS_EDGE_PX,
  planPngFilename,
  rasterizeSvg,
  resolvePngSize,
  serializePlanSvg,
  type RasterDeps,
  type RasterizeOptions,
} from './pngExport';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** A tiny plan drawing: a bed (non-scaling stroke), its label and a plant marker, styled by class + CSS variables. */
function drawing(): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, 'svg');
  // React writes `xmlns` as a plain attribute; the export must not serialize it twice.
  svg.setAttribute('xmlns', SVG_NS);
  svg.setAttribute('width', '300');
  svg.setAttribute('height', '200');
  svg.setAttribute('viewBox', '0 -2 3 2');
  svg.setAttribute('class', 'css-plan');
  svg.setAttribute('data-testid', 'garden-plan-svg');
  const group = document.createElementNS(SVG_NS, 'g');
  group.setAttribute('class', 'gp-obj');
  group.setAttribute('tabindex', '0');
  group.setAttribute('role', 'button');
  group.setAttribute('data-plan-key', 'bed_1');
  const shape = document.createElementNS(SVG_NS, 'path');
  shape.setAttribute('class', 'gp-shape');
  shape.setAttribute('id', 'shape');
  shape.setAttribute('d', 'M0 0 L1 0 L1 -1 Z');
  const label = document.createElementNS(SVG_NS, 'text');
  label.setAttribute('id', 'label');
  label.textContent = 'Beet 1';
  group.append(shape, label);
  svg.append(group);
  document.body.append(svg);
  return svg;
}

const VARS: Record<string, string> = { '--plan-bed': 'rgb(46, 125, 50)', '--plan-text': 'rgba(0, 0, 0, 0.87)' };

/** Declared (cascaded) values per element; `var(--x)` is resolved like a browser's computed value. */
const DECLARED: Record<string, Record<string, string>> = {
  svg: { 'font-family': '"Roboto", "Helvetica", "Arial"', 'font-size': '16px', fill: 'var(--plan-text)' },
  shape: { fill: 'var(--plan-bed)', stroke: 'rgb(97, 97, 97)', 'stroke-width': '2px', 'stroke-dasharray': '6px, 4px', 'vector-effect': 'non-scaling-stroke' },
  label: { 'font-size': '0.12px', 'text-anchor': 'middle' },
};
const INHERITED = new Set(['fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'font-family', 'font-size', 'text-anchor']);

function keyOf(element: Element): string {
  return element.tagName === 'svg' ? 'svg' : (element.getAttribute('id') ?? '');
}

function computed(element: Element): CSSStyleDeclaration {
  const resolve = (property: string): string => {
    const own = DECLARED[keyOf(element)]?.[property];
    if (own !== undefined) return own.replace(/var\((--[\w-]+)\)/g, (_, name: string) => VARS[name] ?? '');
    if (INHERITED.has(property) && element.parentElement) return computedOf(element.parentElement, property);
    return '';
  };
  return { getPropertyValue: resolve } as unknown as CSSStyleDeclaration;
}

function computedOf(element: Element, property: string): string {
  return computed(element).getPropertyValue(property);
}

function parse(text: string): Document {
  return new DOMParser().parseFromString(text, 'image/svg+xml');
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('serializePlanSvg', () => {
  it('writes the computed styles inline, with CSS variables resolved and a system-font fallback', () => {
    const text = serializePlanSvg(drawing(), { widthPx: 300, heightPx: 200, factor: 1, getStyle: computed });
    expect(text).not.toContain('var(');
    expect(text.match(/xmlns=/g)).toHaveLength(1);
    const doc = parse(text);
    const root = doc.documentElement;
    expect(root.getAttribute('style')).toContain('fill:rgba(0, 0, 0, 0.87)');
    expect(root.getAttribute('style')).toContain('font-family:"Roboto", "Helvetica", "Arial", sans-serif');
    const shape = doc.querySelector('path');
    expect(shape?.getAttribute('style')).toContain('fill:rgb(46, 125, 50)');
    expect(shape?.getAttribute('style')).toContain('stroke:rgb(97, 97, 97)');
    // The label inherits its family from the root's own style attribute; only what differs is written.
    const label = doc.querySelector('text');
    expect(label?.getAttribute('style')).toContain('font-size:0.12px');
    expect(label?.getAttribute('style')).not.toContain('font-family');
  });

  it('drops the classes and the interaction attributes and leaves the source untouched', () => {
    const svg = drawing();
    const text = serializePlanSvg(svg, { widthPx: 300, heightPx: 200, factor: 1, getStyle: computed });
    expect(text).not.toContain('class=');
    expect(text).not.toContain('tabindex');
    expect(text).not.toContain('role=');
    expect(text).toContain('data-plan-key="bed_1"');
    expect(svg.getAttribute('class')).toBe('css-plan');
    expect(svg.querySelector('#shape')?.getAttribute('style')).toBeNull();
  });

  it('sizes the image by the factor and scales strokes that are in screen pixels', () => {
    const doc = parse(serializePlanSvg(drawing(), { widthPx: 300, heightPx: 200, factor: 4, getStyle: computed }));
    expect(doc.documentElement.getAttribute('width')).toBe('1200');
    expect(doc.documentElement.getAttribute('height')).toBe('800');
    expect(doc.documentElement.getAttribute('viewBox')).toBe('0 -2 3 2');
    const style = doc.querySelector('path')?.getAttribute('style') ?? '';
    expect(style).toContain('stroke-width:8px');
    expect(style).toContain('stroke-dasharray:24px, 16px');
  });
});

describe('resolvePngSize', () => {
  it('applies the requested factor while the bitmap fits', () => {
    expect(resolvePngSize(1200, 800, 2)).toEqual({ factor: 2, widthPx: 2400, heightPx: 1600, capped: false });
    expect(resolvePngSize(1200, 800, 4)).toEqual({ factor: 4, widthPx: 4800, heightPx: 3200, capped: false });
  });

  it('caps at the canvas area and reports the reduced factor', () => {
    const size = resolvePngSize(1200, 1200, 4);
    expect(size.capped).toBe(true);
    expect(size.factor).toBeLessThan(4);
    expect(size.factor).toBe(3.41);
    expect(size.widthPx * size.heightPx).toBeLessThanOrEqual(MAX_CANVAS_AREA_PX);
  });

  it('caps at the canvas edge for a long, narrow plan', () => {
    const size = resolvePngSize(6000, 100, 4);
    expect(size.capped).toBe(true);
    expect(size.widthPx).toBeLessThanOrEqual(MAX_CANVAS_EDGE_PX);
    expect(size.factor).toBe(2.73);
  });
});

describe('rasterizeSvg', () => {
  let calls: string[];
  let canvas: { width: number; height: number; getContext: () => unknown; toBlob: (cb: BlobCallback, type?: string) => void };
  let deps: RasterDeps;
  const base: RasterizeOptions = {
    widthPx: 2400,
    heightPx: 1600,
    factor: 2,
    background: '#ffffff',
    watermark: null,
    watermarkColor: '#555555',
  };

  beforeEach(() => {
    calls = [];
    const context = {
      font: '',
      fillStyle: '',
      globalAlpha: 1,
      textAlign: '',
      textBaseline: '',
      fillRect: (...args: number[]) => calls.push(`fillRect(${args.join(',')})`),
      drawImage: (_image: unknown, ...args: number[]) => calls.push(`drawImage(${args.join(',')})`),
      measureText: (text: string) => ({ width: text.length * 10 }),
      fillText: (text: string) => calls.push(`fillText(${text})`),
    };
    canvas = {
      width: 0,
      height: 0,
      getContext: () => context,
      toBlob: (callback, type) => callback(new Blob(['png'], { type })),
    };
    deps = {
      loadImage: vi.fn(async () => ({}) as CanvasImageSource),
      createCanvas: () => canvas as unknown as HTMLCanvasElement,
    };
    URL.createObjectURL = vi.fn(() => 'blob:svg');
    URL.revokeObjectURL = vi.fn();
  });

  it('draws the SVG at the image size onto the background and encodes a PNG', async () => {
    const blob = await rasterizeSvg('<svg/>', base, deps);
    expect(blob.type).toBe('image/png');
    expect(canvas.width).toBe(2400);
    expect(canvas.height).toBe(1600);
    expect(deps.loadImage).toHaveBeenCalledWith('blob:svg');
    expect(calls).toEqual(['fillRect(0,0,2400,1600)', 'drawImage(0,0,2400,1600)']);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:svg');
  });

  it('draws no watermark unless it is chosen', async () => {
    await rasterizeSvg('<svg/>', base, deps);
    expect(calls.some((call) => call.startsWith('fillText'))).toBe(false);
    await rasterizeSvg('<svg/>', { ...base, watermark: 'Kamerplanter · 8. Nov. 2026' }, deps);
    expect(calls).toContain('fillText(Kamerplanter · 8. Nov. 2026)');
  });

  it('fails when the browser gives no context for the canvas', async () => {
    canvas.getContext = () => null;
    await expect(rasterizeSvg('<svg/>', base, deps)).rejects.toThrow('no 2d context');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:svg');
  });
});

describe('planPngFilename', () => {
  it('names the site and the day', () => {
    expect(planPngFilename('s1', new Date(2026, 10, 8))).toBe('garden-plan-s1-20261108.png');
  });

  it('makes the site key safe like the server does', () => {
    expect(planPngFilename('../a b/ü"x', new Date(2026, 10, 8))).toBe('garden-plan-___a_b___x-20261108.png');
    expect(planPngFilename('k'.repeat(80), new Date(2026, 10, 8))).toBe(`garden-plan-${'k'.repeat(64)}-20261108.png`);
    expect(planPngFilename('', new Date(2026, 10, 8))).toBe('garden-plan-plan-20261108.png');
  });
});
