import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { inflateSync } from 'node:zlib';
import { describe, expect, it } from 'vitest';
import { matchRoutes, type RouteObject } from 'react-router-dom';
import { router } from '@/routes/AppRoutes';

/**
 * #3025 W-33/L-15 — the hand-written web app manifest (`public/manifest.json`, UI-NFR-012 §7.2).
 *
 * - An icon declares one purpose per entry. `"any maskable"` hands the same picture to both slots: as `any` it is
 *   shown with the padding a mask needs, as `maskable` it is cropped as if it had none. The spec's manifest lists
 *   `any` and `maskable` as separate entries (UI-NFR-012 §7.2).
 * - Every shortcut leads to a route of the app, not to the 404 page (the former `/kalender/aussaat`).
 * - The maskable icon keeps its motif inside the safe zone, the centred circle of 80 % diameter a mask may keep
 *   (W3C manifest "maskable" purpose). The regular 512 px icon reaches 41.6 % from the centre, so the leaf tips
 *   would be cut; the maskable entry uses a padded copy.
 */
interface ManifestIcon {
  src: string;
  sizes: string;
  purpose?: string;
}

interface Manifest {
  icons: ManifestIcon[];
  shortcuts?: { name: string; url: string }[];
  start_url: string;
}

const manifest = JSON.parse(readFileSync(join(process.cwd(), 'public/manifest.json'), 'utf8')) as Manifest;

/** Decode an 8-bit RGB/RGBA, non-interlaced PNG (enough for the app icons) into rows of pixels. */
function decodePng(path: string): { width: number; height: number; channels: number; data: Uint8Array } {
  const file = readFileSync(path);
  let offset = 8;
  let width = 0;
  let height = 0;
  let channels = 0;
  const idat: Buffer[] = [];
  while (offset < file.length) {
    const length = file.readUInt32BE(offset);
    const type = file.toString('ascii', offset + 4, offset + 8);
    const body = file.subarray(offset + 8, offset + 8 + length);
    if (type === 'IHDR') {
      width = body.readUInt32BE(0);
      height = body.readUInt32BE(4);
      expect(body[8]).toBe(8);
      expect(body[12]).toBe(0);
      channels = body[9] === 6 ? 4 : body[9] === 2 ? 3 : 0;
      expect(channels).toBeGreaterThan(0);
    } else if (type === 'IDAT') {
      idat.push(body);
    }
    offset += 12 + length;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const data = new Uint8Array(height * stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const value = raw[y * (stride + 1) + 1 + x];
      const left = x >= channels ? data[y * stride + x - channels] : 0;
      const up = y > 0 ? data[(y - 1) * stride + x] : 0;
      const upLeft = y > 0 && x >= channels ? data[(y - 1) * stride + x - channels] : 0;
      let predicted = 0;
      if (filter === 1) predicted = left;
      else if (filter === 2) predicted = up;
      else if (filter === 3) predicted = (left + up) >> 1;
      else if (filter === 4) {
        const p = left + up - upLeft;
        const pa = Math.abs(p - left);
        const pb = Math.abs(p - up);
        const pc = Math.abs(p - upLeft);
        predicted = pa <= pb && pa <= pc ? left : pb <= pc ? up : upLeft;
      }
      data[y * stride + x] = (value + predicted) & 0xff;
    }
  }
  return { width, height, channels, data };
}

/** The farthest motif pixel (differs from the corner colour) from the centre, as a fraction of the width. */
function motifExtent(path: string): number {
  const { width, height, channels, data } = decodePng(path);
  const background = [data[0], data[1], data[2]];
  let farthest = 0;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * channels;
      const diff =
        Math.abs(data[i] - background[0]) + Math.abs(data[i + 1] - background[1]) + Math.abs(data[i + 2] - background[2]);
      if (diff > 30) farthest = Math.max(farthest, Math.hypot(x + 0.5 - width / 2, y + 0.5 - height / 2));
    }
  }
  return farthest / width;
}

function resolvesToAPage(url: string): boolean {
  const matches = matchRoutes(router.routes as RouteObject[], url);
  if (!matches) return false;
  return matches[matches.length - 1].route.path !== '*';
}

describe('web app manifest', () => {
  it('gives every icon exactly one purpose', () => {
    for (const icon of manifest.icons) {
      expect((icon.purpose ?? 'any').trim().split(/\s+/), icon.src).toHaveLength(1);
    }
  });

  it('offers an any icon and a maskable icon of 512 px', () => {
    const large = manifest.icons.filter((icon) => icon.sizes === '512x512');
    expect(large.map((icon) => icon.purpose ?? 'any').sort()).toEqual(['any', 'maskable']);
  });

  it('keeps the maskable icon\u2019s motif inside the safe zone', () => {
    const maskable = manifest.icons.find((icon) => icon.purpose === 'maskable');
    expect(maskable).toBeDefined();
    const extent = motifExtent(join(process.cwd(), 'public', maskable!.src));
    expect(extent).toBeLessThanOrEqual(0.4);
    // The check itself sees the problem in the unpadded icon.
    expect(motifExtent(join(process.cwd(), 'public/icons/icon-512.png'))).toBeGreaterThan(0.4);
  });

  it('points the start URL and every shortcut at a page of the app', () => {
    expect(resolvesToAPage(manifest.start_url)).toBe(true);
    for (const shortcut of manifest.shortcuts ?? []) {
      expect(resolvesToAPage(shortcut.url), shortcut.url).toBe(true);
    }
    // The check itself would see the former dead shortcut.
    expect(resolvesToAPage('/kalender/aussaat')).toBe(false);
  });
});
