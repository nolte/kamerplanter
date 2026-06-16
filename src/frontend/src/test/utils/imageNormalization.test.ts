import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  normalizeImage,
  MAX_EDGE,
  JPEG_QUALITY,
  MAX_UPLOAD_BYTES,
} from '@/utils/imageNormalization';

/**
 * REQ-029-A §0.1.1 point 4 — client-side image normalization unit tests.
 *
 * jsdom ships no working image decoder and no canvas backend, so the browser
 * primitives the module depends on (`new Image()` decode, `<canvas>` 2D context,
 * `canvas.toBlob`, `URL.createObjectURL`) are stubbed. The tests then exercise
 * the *logic* the module owns: scale/target-size computation, EXIF-stripping
 * re-encode parameters, output filename derivation, object-URL lifecycle and the
 * error paths (decode failure, unsupported format, missing context, encode
 * failure).
 */

interface FakeContext {
  drawImage: ReturnType<typeof vi.fn>;
}

interface CanvasState {
  width: number;
  height: number;
  ctx: FakeContext | null;
  toBlobArgs: { type: string; quality: number } | null;
  blob: Blob | null;
}

// ── Image decode stub ────────────────────────────────────────────────────────
// The module sets `img.src = url` and waits for onload/onerror. We drive that
// from the test by configuring the natural size and whether decode succeeds.
let imageConfig: { width: number; height: number; fail: boolean };

class FakeImage {
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  width = 0;
  height = 0;
  set src(_value: string) {
    queueMicrotask(() => {
      if (imageConfig.fail) {
        this.onerror?.();
        return;
      }
      this.width = imageConfig.width;
      this.height = imageConfig.height;
      this.onload?.();
    });
  }
}

// ── Canvas stub ──────────────────────────────────────────────────────────────
let lastCanvas: CanvasState | null = null;
let canvasConfig: { contextAvailable: boolean; blob: Blob | null };

function createFakeCanvas(): HTMLCanvasElement {
  const state: CanvasState = {
    width: 0,
    height: 0,
    ctx: null,
    toBlobArgs: null,
    blob: canvasConfig.blob,
  };
  lastCanvas = state;
  const canvas = {
    get width() {
      return state.width;
    },
    set width(v: number) {
      state.width = v;
    },
    get height() {
      return state.height;
    },
    set height(v: number) {
      state.height = v;
    },
    getContext: vi.fn((kind: string) => {
      if (kind !== '2d' || !canvasConfig.contextAvailable) return null;
      state.ctx = { drawImage: vi.fn() };
      return state.ctx;
    }),
    toBlob: vi.fn(
      (cb: (blob: Blob | null) => void, type: string, quality: number) => {
        state.toBlobArgs = { type, quality };
        cb(state.blob);
      },
    ),
  };
  return canvas as unknown as HTMLCanvasElement;
}

let createElementSpy: ReturnType<typeof vi.spyOn>;
let createObjectUrlSpy: ReturnType<typeof vi.fn>;
let revokeObjectUrlSpy: ReturnType<typeof vi.fn>;
let objectUrlCounter = 0;

beforeEach(() => {
  imageConfig = { width: 100, height: 100, fail: false };
  canvasConfig = { contextAvailable: true, blob: new Blob(['x'], { type: 'image/jpeg' }) };
  lastCanvas = null;
  objectUrlCounter = 0;

  vi.stubGlobal('Image', FakeImage);

  createElementSpy = vi
    .spyOn(document, 'createElement')
    .mockImplementation(((tag: string) => {
      if (tag === 'canvas') return createFakeCanvas();
      // Defer to the real implementation for any non-canvas element.
      return Object.getPrototypeOf(document).createElement.call(document, tag);
    }) as typeof document.createElement);

  createObjectUrlSpy = vi.fn(() => `blob:object-${(objectUrlCounter += 1)}`);
  revokeObjectUrlSpy = vi.fn();
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: createObjectUrlSpy,
    revokeObjectURL: revokeObjectUrlSpy,
  });
});

afterEach(() => {
  createElementSpy.mockRestore();
  vi.unstubAllGlobals();
});

function makeFile(name: string, type: string): File {
  return new File([new Uint8Array([1, 2, 3])], name, { type });
}

describe('imageNormalization constants', () => {
  it('exposes the upload guard rails matching the API limits', () => {
    expect(MAX_EDGE).toBe(1280);
    expect(JPEG_QUALITY).toBe(0.85);
    expect(MAX_UPLOAD_BYTES).toBe(5 * 1024 * 1024);
  });
});

describe('normalizeImage', () => {
  it('downscales the longer edge to MAX_EDGE preserving aspect ratio', async () => {
    imageConfig = { width: 4000, height: 2000, fail: false };
    const result = await normalizeImage(makeFile('huge.jpg', 'image/jpeg'));

    expect(lastCanvas).not.toBeNull();
    // Longest edge clamped to MAX_EDGE, the shorter scaled proportionally.
    expect(lastCanvas!.width).toBe(MAX_EDGE);
    expect(lastCanvas!.height).toBe(MAX_EDGE / 2);
    expect(lastCanvas!.ctx?.drawImage).toHaveBeenCalledWith(
      expect.anything(),
      0,
      0,
      MAX_EDGE,
      MAX_EDGE / 2,
    );
    expect(result.file).toBeInstanceOf(File);
  });

  it('does not upscale images already within the limit', async () => {
    imageConfig = { width: 640, height: 480, fail: false };
    await normalizeImage(makeFile('small.png', 'image/png'));

    expect(lastCanvas!.width).toBe(640);
    expect(lastCanvas!.height).toBe(480);
  });

  it('rounds fractional target dimensions and never produces a zero edge', async () => {
    // 1281x1 → scale = 1280/1281, height rounds to 0 but is floored to 1.
    imageConfig = { width: 1281, height: 1, fail: false };
    await normalizeImage(makeFile('sliver.jpg', 'image/jpeg'));

    expect(lastCanvas!.width).toBe(MAX_EDGE);
    expect(lastCanvas!.height).toBe(1);
  });

  it('re-encodes as JPEG at the configured quality to strip EXIF', async () => {
    const result = await normalizeImage(makeFile('photo.jpg', 'image/jpeg'));

    expect(lastCanvas!.toBlobArgs).toEqual({ type: 'image/jpeg', quality: JPEG_QUALITY });
    expect(result.file.type).toBe('image/jpeg');
  });

  it('derives a .jpg output name from the source basename', async () => {
    const result = await normalizeImage(makeFile('My Plant.HEIC', 'image/heic'));
    expect(result.file.name).toBe('My Plant.jpg');
  });

  it('falls back to a "plant" basename when the input name has no stem', async () => {
    const result = await normalizeImage(makeFile('.png', 'image/png'));
    expect(result.file.name).toBe('plant.jpg');
  });

  it('creates a source object URL and revokes it afterwards', async () => {
    const result = await normalizeImage(makeFile('photo.jpg', 'image/jpeg'));

    // One URL for decoding the source, one for the returned preview.
    expect(createObjectUrlSpy).toHaveBeenCalledTimes(2);
    expect(revokeObjectUrlSpy).toHaveBeenCalledTimes(1);
    expect(result.previewUrl).toMatch(/^blob:object-/);
  });

  it('accepts an unknown image/* subtype not in the explicit allow-list', async () => {
    // image/avif is not enumerated but starts with image/ → allowed.
    await expect(
      normalizeImage(makeFile('pic.avif', 'image/avif')),
    ).resolves.toMatchObject({ file: expect.any(File) });
  });

  it('accepts a typeless file (drag & drop sometimes omits the MIME type)', async () => {
    await expect(
      normalizeImage(makeFile('mystery', '')),
    ).resolves.toMatchObject({ file: expect.any(File) });
  });

  it('throws UNSUPPORTED_FORMAT for a non-image input', async () => {
    await expect(
      normalizeImage(makeFile('notes.pdf', 'application/pdf')),
    ).rejects.toThrow('UNSUPPORTED_FORMAT');
  });

  it('rejects with IMAGE_DECODE_FAILED when the bitmap cannot be decoded', async () => {
    imageConfig = { width: 0, height: 0, fail: true };
    await expect(
      normalizeImage(makeFile('broken.jpg', 'image/jpeg')),
    ).rejects.toThrow('IMAGE_DECODE_FAILED');
    // The source URL must still be revoked on the error path (finally block).
    expect(revokeObjectUrlSpy).toHaveBeenCalledTimes(1);
  });

  it('throws CANVAS_UNAVAILABLE when no 2D context is obtainable', async () => {
    canvasConfig.contextAvailable = false;
    await expect(
      normalizeImage(makeFile('photo.jpg', 'image/jpeg')),
    ).rejects.toThrow('CANVAS_UNAVAILABLE');
    expect(revokeObjectUrlSpy).toHaveBeenCalledTimes(1);
  });

  it('throws CANVAS_ENCODE_FAILED when toBlob yields null', async () => {
    canvasConfig.blob = null;
    await expect(
      normalizeImage(makeFile('photo.jpg', 'image/jpeg')),
    ).rejects.toThrow('CANVAS_ENCODE_FAILED');
    expect(revokeObjectUrlSpy).toHaveBeenCalledTimes(1);
  });
});
