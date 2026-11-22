import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { photoFile, photoForQueue } from './queuedPhoto';

/**
 * REQ-053 WP 9.4 (#2744), UI-NFR-012 R-043/R-044, G-W9 (g): a photo for the offline buffer is re-encoded through a
 * canvas to JPEG 80 at ≤ 1920 px — and what lands in IndexedDB is that re-encode, never the original file, so the
 * original's EXIF block (camera, GPS position) does not survive on the device.
 *
 * jsdom has no image decoder and no canvas encoder: both are stubbed. The canvas stub answers with what a browser
 * canvas writes — a bare JFIF JPEG; a browser's `toBlob` never writes EXIF. The test pins that the stored bytes
 * ARE the canvas output and that the original's EXIF/GPS bytes are not among them.
 */

const ascii = (text: string) => [...text].map((char) => char.charCodeAt(0));

/** A camera JPEG: SOI, an APP1 EXIF segment with a GPS tag text, a bit of scan data, EOI. */
const CAMERA_JPEG = new Uint8Array([
  0xff, 0xd8,
  0xff, 0xe1, 0x00, 0x20, ...ascii('Exif'), 0x00, 0x00, ...ascii('GPSLatitude 52.5200N'), 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0xff, 0xda, 0x01, 0x02, 0x03,
  0xff, 0xd9,
]);
/** What the canvas encoder writes: SOI, APP0 JFIF, data, EOI — no APP1. */
const CANVAS_JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, ...ascii('JFIF'), 0x00, 0x09, 0x09, 0xff, 0xd9]);

function contains(haystack: Uint8Array, needle: number[]): boolean {
  outer: for (let index = 0; index + needle.length <= haystack.length; index += 1) {
    for (let offset = 0; offset < needle.length; offset += 1) {
      if (haystack[index + offset] !== needle[offset]) continue outer;
    }
    return true;
  }
  return false;
}

let canvasSize: { width: number; height: number } | null = null;
let encoded: { type: string | undefined; quality: number | undefined } | null = null;

beforeEach(() => {
  canvasSize = null;
  encoded = null;
  vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:x'), revokeObjectURL: vi.fn() }));
  class DecodedImage {
    width = 4000;
    height = 3000;
    onload: (() => void) | null = null;
    onerror: (() => void) | null = null;
    set src(_value: string) {
      queueMicrotask(() => this.onload?.());
    }
  }
  vi.stubGlobal('Image', DecodedImage);
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(function (this: HTMLCanvasElement) {
    canvasSize = { width: this.width, height: this.height };
    return { drawImage: vi.fn() } as unknown as CanvasRenderingContext2D;
  } as never);
  vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback, type, quality) => {
    encoded = { type, quality };
    callback(new Blob([CANVAS_JPEG], { type: 'image/jpeg' }));
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('photoForQueue', () => {
  it('stores the canvas re-encode (≤ 1920 px, JPEG 80), never the original — no EXIF or GPS survives', async () => {
    expect(contains(CAMERA_JPEG, ascii('Exif'))).toBe(true);
    const stored = await photoForQueue(new File([CAMERA_JPEG], 'IMG_0001.JPG', { type: 'image/jpeg' }));

    expect(canvasSize).toEqual({ width: 1920, height: 1440 });
    expect(encoded).toEqual({ type: 'image/jpeg', quality: 0.8 });
    const bytes = new Uint8Array(stored.bytes);
    expect(bytes).toEqual(CANVAS_JPEG);
    expect(contains(bytes, ascii('Exif'))).toBe(false);
    expect(contains(bytes, ascii('GPS'))).toBe(false);
    expect(contains(bytes, [0xff, 0xe1])).toBe(false); // no APP1 segment at all
    // A generic name: the original's (`IMG_0001.JPG`, often with date, place or person) is not kept.
    expect(stored).toMatchObject({ type: 'image/jpeg', name: 'photo.jpg' });
    expect(new Uint8Array(await photoFile(stored).arrayBuffer())).toEqual(CANVAS_JPEG);
  });

  it('fails instead of storing the original when the canvas cannot encode', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback) => callback(null));
    await expect(photoForQueue(new File([CAMERA_JPEG], 'a.jpg', { type: 'image/jpeg' }))).rejects.toThrow();
  });
});
