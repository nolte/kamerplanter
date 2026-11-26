import { readFileSync } from 'node:fs';
import { join } from 'node:path';
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

  it('points the start URL and every shortcut at a page of the app', () => {
    expect(resolvesToAPage(manifest.start_url)).toBe(true);
    for (const shortcut of manifest.shortcuts ?? []) {
      expect(resolvesToAPage(shortcut.url), shortcut.url).toBe(true);
    }
    // The check itself would see the former dead shortcut.
    expect(resolvesToAPage('/kalender/aussaat')).toBe(false);
  });
});
