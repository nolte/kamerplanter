/**
 * What the field map shows for "My position" (REQ-053 GP-UX-026): dot or hint, from the watch, the site's
 * coordinate, the plan and the view.
 */
import { describe, expect, it } from 'vitest';
import { EARTH_RADIUS_M } from '../model/ownPosition';
import type { BoundingBox } from '../model/types';
import type { Viewport } from '../renderer/types';
import { ownPositionView } from './ownPositionView';
import type { SiteCoordinates } from './useSiteCoordinates';

const SITE = { latitude: 48.1, longitude: 11.5 };
const READY: SiteCoordinates = { status: 'ready', coordinates: SITE };
const BOUNDS: BoundingBox = [0, 0, 20, 10];
/** The whole plan at 10 px/m: top-left (0, 10). */
const VIEW: Viewport = { originM: [0, 10], pxPerM: 10, widthPx: 200, heightPx: 100 };
const DEG = (EARTH_RADIUS_M * Math.PI) / 180;

function fix(northM: number, accuracyM = 5) {
  return { latitude: SITE.latitude + northM / DEG, longitude: SITE.longitude, accuracyM };
}

const base = { on: true, site: READY, bounds: BOUNDS, northAngleDeg: 0, viewport: VIEW };

describe('ownPositionView', () => {
  it('shows nothing while the switch is off, and leaves unsupported/insecure to the switch', () => {
    expect(ownPositionView({ ...base, on: false, status: 'off', fix: null })).toEqual({ dot: null, hint: null });
    expect(ownPositionView({ ...base, status: 'insecure', fix: null })).toEqual({ dot: null, hint: null });
  });

  it('names the site state before the device: loading, error, no GPS', () => {
    const loading = ownPositionView({ ...base, site: { status: 'loading', coordinates: null }, status: 'off', fix: null });
    expect(loading.hint).toEqual({ reason: 'site_loading' });
    const failed = ownPositionView({ ...base, site: { status: 'error', coordinates: null }, status: 'off', fix: null });
    expect(failed.hint).toEqual({ reason: 'site_error' });
    const missing = ownPositionView({ ...base, site: { status: 'missing', coordinates: null }, status: 'off', fix: null });
    expect(missing.hint).toEqual({ reason: 'no_gps' });
  });

  it('passes the watch state on until there is a fix', () => {
    expect(ownPositionView({ ...base, status: 'off', fix: null }).hint).toEqual({ reason: 'locating' });
    expect(ownPositionView({ ...base, status: 'locating', fix: null }).hint).toEqual({ reason: 'locating' });
    expect(ownPositionView({ ...base, status: 'denied', fix: null }).hint).toEqual({ reason: 'denied' });
    expect(ownPositionView({ ...base, status: 'timeout', fix: null }).hint).toEqual({ reason: 'timeout' });
  });

  it('draws the dot in screen pixels with the accuracy radius scaled by the zoom', () => {
    const view = ownPositionView({ ...base, status: 'located', fix: fix(2, 4) });
    expect(view.hint).toBeNull();
    // Anchor (10, 5) + 2 m north = (10, 7) -> screen (100, 30).
    expect(view.dot?.centerPx[0]).toBeCloseTo(100, 4);
    expect(view.dot?.centerPx[1]).toBeCloseTo(30, 4);
    expect(view.dot?.radiusM).toBe(4);
    expect(view.dot?.radiusPx).toBe(40);
  });

  it('draws the dot and says so when the accuracy is coarse', () => {
    const view = ownPositionView({ ...base, status: 'located', fix: fix(0, 80) });
    expect(view.dot).not.toBeNull();
    expect(view.hint).toEqual({ reason: 'coarse', accuracyM: 80 });
  });

  it('hints instead of drawing when the position is outside the view, with its distance from the plan', () => {
    const zoomed: Viewport = { originM: [0, 10], pxPerM: 40, widthPx: 200, heightPx: 100 };
    const inside = ownPositionView({ ...base, viewport: zoomed, status: 'located', fix: fix(-4) });
    expect(inside.dot).toBeNull();
    expect(inside.hint).toEqual({ reason: 'outside_view', distanceM: 0 });
    const beyond = ownPositionView({ ...base, status: 'located', fix: fix(105) });
    expect(beyond.dot).toBeNull();
    expect(beyond.hint?.reason).toBe('outside_view');
    if (beyond.hint?.reason === 'outside_view') expect(beyond.hint.distanceM).toBeCloseTo(100, 3);
  });

  it('reports far beyond 500 m', () => {
    const far = ownPositionView({ ...base, status: 'located', fix: fix(1000) });
    expect(far.dot).toBeNull();
    expect(far.hint?.reason).toBe('far');
  });
});
