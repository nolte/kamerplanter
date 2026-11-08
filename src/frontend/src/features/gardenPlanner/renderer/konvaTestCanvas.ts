/**
 * Test support for the Konva renderer (REQ-053 D-01): jsdom has no canvas - `getContext('2d')` returns `null` - and
 * the repo does not ship the native `canvas` package. Instead of pixels the tests read **what is drawn**: every
 * canvas gets a {@link RecordingContext} that keeps each call (with the fill, stroke, font and alpha in force), so a
 * test asserts "the label is written at the anchor" or "the dragged bed is on the drag layer", not a bitmap.
 * Test support only: nothing in the app imports this module.
 */

export interface CanvasCall {
  op: string;
  args: unknown[];
  fillStyle: unknown;
  strokeStyle: unknown;
  font: string;
  lineWidth: number;
  lineCap: string;
  globalAlpha: number;
  lineDash: number[];
}

/** A 2D context that draws nothing and remembers everything. Unknown methods are recorded, not thrown. */
export class RecordingContext {
  calls: CanvasCall[] = [];
  canvas: HTMLCanvasElement | null = null;
  fillStyle: unknown = '#000000';
  strokeStyle: unknown = '#000000';
  lineWidth = 1;
  lineCap = 'butt';
  lineJoin = 'miter';
  miterLimit = 10;
  lineDashOffset = 0;
  globalAlpha = 1;
  globalCompositeOperation = 'source-over';
  imageSmoothingEnabled = true;
  font = '10px sans-serif';
  textAlign = 'start';
  textBaseline = 'alphabetic';
  direction = 'inherit';
  shadowBlur = 0;
  shadowColor = 'rgba(0, 0, 0, 0)';
  shadowOffsetX = 0;
  shadowOffsetY = 0;
  filter = 'none';
  private dash: number[] = [];

  record(op: string, args: unknown[]): void {
    this.calls.push({
      op,
      args,
      fillStyle: this.fillStyle,
      strokeStyle: this.strokeStyle,
      font: this.font,
      lineWidth: this.lineWidth,
      lineCap: this.lineCap,
      globalAlpha: this.globalAlpha,
      lineDash: [...this.dash],
    });
  }

  /** Calls of one kind, e.g. every `fillText`. */
  ops(op: string): CanvasCall[] {
    return this.calls.filter((call) => call.op === op);
  }

  reset(): void {
    this.calls = [];
  }

  setLineDash(dash: number[]): void {
    this.dash = [...dash];
  }

  getLineDash(): number[] {
    return [...this.dash];
  }

  measureText(text: string): TextMetrics {
    return { width: text.length * 6, actualBoundingBoxAscent: 8, actualBoundingBoxDescent: 2 } as TextMetrics;
  }

  createLinearGradient(): CanvasGradient {
    return { addColorStop: () => undefined } as CanvasGradient;
  }

  createRadialGradient(): CanvasGradient {
    return { addColorStop: () => undefined } as CanvasGradient;
  }

  createPattern(): CanvasPattern | null {
    return null;
  }

  getImageData(_x: number, _y: number, width = 1, height = 1): ImageData {
    return { data: new Uint8ClampedArray(Math.max(1, width * height) * 4), width, height } as ImageData;
  }

  isPointInPath(): boolean {
    return false;
  }

  getTransform(): { a: number; b: number; c: number; d: number; e: number; f: number } {
    return { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
  }
}

/** A `Path2D` stand-in that keeps the path data it was built from. */
export class RecordedPath {
  constructor(readonly d: string = '') {}
  addPath(): void {}
}

const contexts = new WeakMap<HTMLCanvasElement, RecordingContext>();

function recordingProxy(context: RecordingContext): RecordingContext {
  return new Proxy(context, {
    get(target, property, receiver) {
      if (property in target) {
        const value = Reflect.get(target, property, receiver);
        return typeof value === 'function' ? value.bind(target) : value;
      }
      // Any other drawing method (`arc`, `fillText`, `setTransform`, ...) is a recorded no-op.
      return typeof property === 'string' ? (...args: unknown[]) => target.record(property, args) : undefined;
    },
  });
}

/** The recorder behind a canvas, created on first use. */
export function contextOf(canvas: HTMLCanvasElement): RecordingContext {
  let context = contexts.get(canvas);
  if (!context) {
    const raw = new RecordingContext();
    raw.canvas = canvas;
    context = recordingProxy(raw);
    contexts.set(canvas, context);
  }
  return context;
}

let restore: (() => void) | null = null;

/** Gives every canvas a recording 2D context and `Path2D` a stand-in; call {@link uninstallRecordingCanvas} after. */
export function installRecordingCanvas(): void {
  if (restore) return;
  const prototype = HTMLCanvasElement.prototype;
  const original = Object.getOwnPropertyDescriptor(prototype, 'getContext');
  const hadPath2D = 'Path2D' in globalThis;
  const originalPath2D = (globalThis as { Path2D?: unknown }).Path2D;
  Object.defineProperty(prototype, 'getContext', {
    configurable: true,
    writable: true,
    value: function getContext(this: HTMLCanvasElement) {
      return contextOf(this);
    },
  });
  (globalThis as { Path2D?: unknown }).Path2D = RecordedPath;
  restore = () => {
    if (original) Object.defineProperty(prototype, 'getContext', original);
    if (hadPath2D) (globalThis as { Path2D?: unknown }).Path2D = originalPath2D;
    else delete (globalThis as { Path2D?: unknown }).Path2D;
  };
}

export function uninstallRecordingCanvas(): void {
  restore?.();
  restore = null;
}

/** Resolves after the next animation frame: Konva's `batchDraw` paints there. */
export function nextFrame(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}
