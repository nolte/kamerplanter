/**
 * What the field map shows for "My position" (REQ-053 GP-UX-026): the dot in screen pixels, a hint, or both. Pure:
 * the device fix, the site's coordinate, the plan and the current view in; nothing is kept.
 */
import { distanceToBoxM, placeOwnPosition } from '../model/ownPosition';
import type { BoundingBox, Point } from '../model/types';
import { toScreen } from '../renderer/viewport';
import type { Viewport } from '../renderer/types';
import type { SiteCoordinates } from './useSiteCoordinates';
import type { DeviceFix, OwnPositionStatus } from './useOwnPosition';

/** The hints without a number in them. */
export type PlainHintReason = 'locating' | 'denied' | 'unavailable' | 'timeout' | 'site_loading' | 'site_error' | 'no_gps';

/** Why no dot is drawn (or what the dot needs to be read with). `null` = the dot is drawn and says it all. */
export type OwnPositionHint =
  | { reason: PlainHintReason }
  | { reason: 'far' | 'outside_view'; distanceM: number }
  | { reason: 'coarse'; accuracyM: number };

/** From this device accuracy on the circle covers more than a garden; the hint says so. */
export const COARSE_ACCURACY_M = 50;

export interface OwnPositionDotPlacement {
  centerPx: Point;
  radiusPx: number;
  radiusM: number;
}

export interface OwnPositionView {
  dot: OwnPositionDotPlacement | null;
  hint: OwnPositionHint | null;
}

const NOTHING: OwnPositionView = { dot: null, hint: null };

export function ownPositionView(input: {
  /** The user's switch. */
  on: boolean;
  /** The device watch; `off` while the site's coordinate is not known yet (nothing is asked of the browser then). */
  status: OwnPositionStatus;
  fix: DeviceFix | null;
  site: SiteCoordinates;
  /** The box of everything drawn on the plan; `null` = nothing drawn. */
  bounds: BoundingBox | null;
  northAngleDeg: number;
  viewport: Viewport | null;
}): OwnPositionView {
  const { on, status, fix, site, bounds, northAngleDeg, viewport } = input;
  // Unsupported and insecure are the switch's own business (hidden / disabled with the reason).
  if (!on || status === 'unsupported' || status === 'insecure') return NOTHING;
  // The site first: without a coordinate the device fix has nothing to be placed against.
  if (site.status !== 'ready') {
    const reason = site.status === 'error' ? 'site_error' : site.status === 'missing' ? 'no_gps' : 'site_loading';
    return { dot: null, hint: { reason } };
  }
  if (status !== 'located' || fix === null) {
    return { dot: null, hint: { reason: status === 'located' || status === 'off' ? 'locating' : status } };
  }
  if (bounds === null || viewport === null) return NOTHING;

  const placed = placeOwnPosition(
    { latitude: fix.latitude, longitude: fix.longitude, accuracyM: fix.accuracyM },
    site.coordinates,
    bounds,
    northAngleDeg,
  );
  if (placed.kind === 'far') return { dot: null, hint: { reason: 'far', distanceM: placed.distanceM } };

  const centerPx = toScreen(viewport, placed.pointM);
  const inView =
    centerPx[0] >= 0 && centerPx[0] <= viewport.widthPx && centerPx[1] >= 0 && centerPx[1] <= viewport.heightPx;
  if (!inView) {
    // 0 = inside the plan, only zoomed past: "Whole plan" brings it back.
    return { dot: null, hint: { reason: 'outside_view', distanceM: distanceToBoxM(placed.pointM, bounds) } };
  }
  const dot = { centerPx, radiusPx: placed.radiusM * viewport.pxPerM, radiusM: placed.radiusM };
  return {
    dot,
    hint: placed.radiusM >= COARSE_ACCURACY_M ? { reason: 'coarse', accuracyM: placed.radiusM } : null,
  };
}
