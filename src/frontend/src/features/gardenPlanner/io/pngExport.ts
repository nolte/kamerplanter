/**
 * The PNG export of the garden plan (REQ-053 GP-FR-144): drawn in the browser, no request to the server.
 *
 * The source is an SVG the export renders itself (see `OffscreenPlanSvg`), never the drawing on screen: a large
 * plan may be on a canvas renderer there (D-01), and then there is no SVG to read. The steps:
 *
 * 1. {@link serializePlanSvg} clones that SVG and writes every computed paint and text style into a `style`
 *    attribute. An SVG drawn as an `<img>` sees none of the page's style sheets, CSS variables or web fonts, so
 *    the computed values (CSS variables already resolved by the browser) are the only way the look survives.
 *    Fonts are not embedded: the computed `font-family` is kept and `sans-serif` appended, so the image uses the
 *    theme font where it is installed on the device and the system sans-serif everywhere else.
 * 2. {@link resolvePngSize} applies the chosen factor (1×/2×/4×) and caps the bitmap at {@link MAX_CANVAS_EDGE_PX}
 *    and {@link MAX_CANVAS_AREA_PX}; a capped export uses the largest factor that fits and says so.
 * 3. {@link rasterizeSvg} loads the SVG from a `blob:` URL into an `<img>` (CSP `img-src blob:`), draws it onto a
 *    `<canvas>`, adds the optional watermark and hands back `toBlob('image/png')`.
 */
import type { PngResolution } from './types';

/**
 * Canvas limits that hold in every supported browser: the smallest values of the published table of
 * `canvas-size` (github.com/jhildenbiddle/canvas-size, "Test Results"). The area is the binding one - iOS Safari
 * refuses a canvas above 16 777 216 pixels (4096 × 4096) and then draws nothing; Chrome and Firefox allow more.
 * The edge is kept at 16 384 px, below Firefox's 32 767 and Chrome's 65 535.
 */
export const MAX_CANVAS_EDGE_PX = 16_384;
export const MAX_CANVAS_AREA_PX = 16_777_216;

/** The plan is fitted into this box (px) for the 1× image; 2× and 4× multiply it. */
export const PNG_BASE_EDGE_PX = 1200;

/** How long an `<img>` may take to decode the SVG before the export gives up. */
export const IMAGE_LOAD_TIMEOUT_MS = 15_000;

export interface PngSize {
  /** The factor applied: the requested one, or less when the cap applied. */
  factor: number;
  widthPx: number;
  heightPx: number;
  /** The requested factor would have exceeded a canvas limit. */
  capped: boolean;
}

/** The bitmap size for `factor` × the base size, capped to the canvas limits (largest factor that fits, 2 decimals). */
export function resolvePngSize(
  baseWidthPx: number,
  baseHeightPx: number,
  requested: PngResolution | number,
  limits: { maxEdgePx: number; maxAreaPx: number } = {
    maxEdgePx: MAX_CANVAS_EDGE_PX,
    maxAreaPx: MAX_CANVAS_AREA_PX,
  },
): PngSize {
  const width = Math.max(1, baseWidthPx);
  const height = Math.max(1, baseHeightPx);
  const fitting = Math.min(
    limits.maxEdgePx / width,
    limits.maxEdgePx / height,
    Math.sqrt(limits.maxAreaPx / (width * height)),
  );
  const capped = requested > fitting;
  const factor = capped ? Math.floor(fitting * 100) / 100 : requested;
  return {
    factor,
    widthPx: Math.max(1, Math.floor(width * factor)),
    heightPx: Math.max(1, Math.floor(height * factor)),
    capped,
  };
}

/**
 * Properties a parent passes on: written on an element only when its value differs from its parent's, which the
 * clone then inherits from the parent's own `style` attribute.
 */
const INHERITED_PROPERTIES = [
  'color',
  'fill',
  'fill-opacity',
  'fill-rule',
  'stroke',
  'stroke-width',
  'stroke-opacity',
  'stroke-dasharray',
  'stroke-dashoffset',
  'stroke-linecap',
  'stroke-linejoin',
  'stroke-miterlimit',
  'paint-order',
  'font-family',
  'font-size',
  'font-style',
  'font-weight',
  'letter-spacing',
  'text-anchor',
  'visibility',
] as const;

/** Properties that are not inherited, with the value that needs no attribute. */
const OWN_PROPERTIES: Readonly<Record<string, string>> = {
  opacity: '1',
  display: '',
  'dominant-baseline': 'auto',
  'vector-effect': 'none',
};

/** Lengths in screen pixels, not user units, for a `vector-effect: non-scaling-stroke` element. */
const SCREEN_LENGTH_PROPERTIES = new Set(['stroke-width', 'stroke-dasharray', 'stroke-dashoffset']);

/** Multiply every number of a CSS length list ("2px", "6px, 4px") by `factor`. */
function scaleLengths(value: string, factor: number): string {
  if (factor === 1 || value === 'none') return value;
  return value.replace(/-?\d*\.?\d+(?:e-?\d+)?/gi, (match) => String(Number(match) * factor));
}

/** Append a generic family so the image falls back to a system font where the theme font is not installed. */
function withGenericFamily(value: string): string {
  return /\b(sans-serif|serif|monospace|system-ui)\b/.test(value) ? value : `${value}, sans-serif`;
}

export interface SerializeOptions {
  /** The SVG's own size in px (its `width`/`height`), multiplied by `factor` into the image size. */
  widthPx: number;
  heightPx: number;
  /** The factor of {@link resolvePngSize}; strokes in screen pixels scale with it. */
  factor: number;
  /** Computed style source; the browser's by default (a test passes a resolver). */
  getStyle?: (element: Element) => CSSStyleDeclaration;
}

/**
 * The SVG as a standalone document: a deep clone with every computed paint and text style inlined, the image size
 * as `width`/`height` and the `viewBox` unchanged. Interaction attributes (focus, roles, ARIA) are dropped - the
 * image is not a control - and the clone never touches the source.
 */
export function serializePlanSvg(svg: SVGSVGElement, options: SerializeOptions): string {
  const getStyle = options.getStyle ?? ((element: Element) => window.getComputedStyle(element));
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const sources: Element[] = [svg, ...svg.querySelectorAll('*')];
  const targets: Element[] = [clone, ...clone.querySelectorAll('*')];
  const computed = new Map<Element, CSSStyleDeclaration>();
  const styleOf = (element: Element): CSSStyleDeclaration => {
    let style = computed.get(element);
    if (!style) {
      style = getStyle(element);
      computed.set(element, style);
    }
    return style;
  };

  sources.forEach((source, index) => {
    const target = targets[index];
    if (!target) return;
    const style = styleOf(source);
    const parentStyle = source === svg || !source.parentElement ? null : styleOf(source.parentElement);
    const nonScaling = style.getPropertyValue('vector-effect').trim() === 'non-scaling-stroke';
    const parentNonScaling =
      parentStyle?.getPropertyValue('vector-effect').trim() === 'non-scaling-stroke';
    const declarations: string[] = [];
    for (const property of INHERITED_PROPERTIES) {
      let value = style.getPropertyValue(property).trim();
      if (value === '') continue;
      const parentValue = parentStyle?.getPropertyValue(property).trim() ?? null;
      // The parent's scaled length is not this element's when only one of them is non-scaling.
      if (value === parentValue && !(SCREEN_LENGTH_PROPERTIES.has(property) && nonScaling !== parentNonScaling)) {
        continue;
      }
      if (nonScaling && SCREEN_LENGTH_PROPERTIES.has(property)) value = scaleLengths(value, options.factor);
      if (property === 'font-family') value = withGenericFamily(value);
      declarations.push(`${property}:${value}`);
    }
    for (const [property, initial] of Object.entries(OWN_PROPERTIES)) {
      const value = style.getPropertyValue(property).trim();
      if (value === '' || value === initial) continue;
      if (property === 'display' && value !== 'none') continue;
      declarations.push(`${property}:${value}`);
    }
    target.removeAttribute('class');
    target.removeAttribute('tabindex');
    target.removeAttribute('role');
    target.removeAttribute('aria-pressed');
    target.removeAttribute('aria-roledescription');
    target.removeAttribute('aria-describedby');
    target.removeAttribute('data-testid');
    if (declarations.length > 0) target.setAttribute('style', declarations.join(';'));
    else target.removeAttribute('style');
  });

  // The serializer writes the SVG namespace declaration itself; a copied `xmlns` attribute (React sets one) would
  // be written a second time, and a duplicate attribute makes the document unreadable for the `<img>`.
  clone.removeAttribute('xmlns');
  clone.setAttribute('width', String(Math.floor(options.widthPx * options.factor)));
  clone.setAttribute('height', String(Math.floor(options.heightPx * options.factor)));
  return new XMLSerializer().serializeToString(clone);
}

export interface RasterizeOptions {
  widthPx: number;
  heightPx: number;
  /** The image factor; the watermark grows with it so it reads the same on every resolution. */
  factor: number;
  /** Painted under the plan; a PNG is transparent otherwise. */
  background: string;
  /** The watermark text, or `null` for none (the default, GP-FR-144). */
  watermark: string | null;
  /** Text colour of the watermark. */
  watermarkColor: string;
}

/** The parts of the browser the rasterizer needs; a test replaces them (jsdom draws nothing). */
export interface RasterDeps {
  loadImage: (url: string) => Promise<CanvasImageSource>;
  createCanvas: () => HTMLCanvasElement;
}

/** Load `url` into an `<img>`; rejects on an error or after {@link IMAGE_LOAD_TIMEOUT_MS}. */
export function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const timer = window.setTimeout(() => {
      image.onload = null;
      image.onerror = null;
      reject(new Error('png-export: image load timed out'));
    }, IMAGE_LOAD_TIMEOUT_MS);
    image.onload = () => {
      window.clearTimeout(timer);
      resolve(image);
    };
    image.onerror = () => {
      window.clearTimeout(timer);
      reject(new Error('png-export: the SVG could not be loaded as an image'));
    };
    image.decoding = 'async';
    image.src = url;
  });
}

export const BROWSER_RASTER_DEPS: RasterDeps = {
  loadImage,
  createCanvas: () => document.createElement('canvas'),
};

/** The watermark in the bottom-right corner, on a light plate so it stays legible on any fill. */
function drawWatermark(context: CanvasRenderingContext2D, options: RasterizeOptions, text: string): void {
  const fontPx = Math.round(12 * options.factor);
  const pad = Math.round(6 * options.factor);
  context.font = `${fontPx}px sans-serif`;
  context.textAlign = 'right';
  context.textBaseline = 'bottom';
  const width = context.measureText(text).width;
  context.globalAlpha = 0.7;
  context.fillStyle = options.background;
  context.fillRect(options.widthPx - width - 3 * pad, options.heightPx - fontPx - 3 * pad, width + 2 * pad, fontPx + 2 * pad);
  context.globalAlpha = 1;
  context.fillStyle = options.watermarkColor;
  context.fillText(text, options.widthPx - 2 * pad, options.heightPx - 2 * pad);
}

/** Draw `svgText` onto a canvas of the given size and encode it as PNG. */
export async function rasterizeSvg(
  svgText: string,
  options: RasterizeOptions,
  deps: RasterDeps = BROWSER_RASTER_DEPS,
): Promise<Blob> {
  const url = URL.createObjectURL(new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' }));
  try {
    const image = await deps.loadImage(url);
    const canvas = deps.createCanvas();
    canvas.width = options.widthPx;
    canvas.height = options.heightPx;
    const context = canvas.getContext('2d');
    // A canvas above the browser's limit has no context; the cap keeps us below it, this is the last guard.
    if (!context) throw new Error('png-export: no 2d context for the canvas');
    context.fillStyle = options.background;
    context.fillRect(0, 0, options.widthPx, options.heightPx);
    context.drawImage(image, 0, 0, options.widthPx, options.heightPx);
    if (options.watermark !== null) drawWatermark(context, options, options.watermark);
    return await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error('png-export: the canvas produced no image'));
      }, 'image/png');
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}

/**
 * A key as a file-name fragment, the same rule as the server's `safe_filename_part`
 * (`garden_plan_export_service.py`): every character outside `[A-Za-z0-9_-]` becomes `_`, at most 64 characters,
 * `plan` when nothing is left.
 */
export function safeFilenamePart(key: string): string {
  return key.replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 64) || 'plan';
}

/**
 * `garden-plan-<site>-<yyyymmdd>.png`: the site part as the server's PDF/SVG/JSON names make it
 * (`garden-plan-<site>.<ext>`), plus the local calendar day of the export, which the server names do not carry.
 */
export function planPngFilename(siteKey: string, date: Date): string {
  const stamp = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
  return `garden-plan-${safeFilenamePart(siteKey)}-${stamp}.png`;
}
