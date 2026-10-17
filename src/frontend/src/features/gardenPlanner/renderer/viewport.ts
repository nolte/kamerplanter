import type { BoundingBox, Point } from '../model/types';
import { CULL_MARGIN } from './lod';
import type { Viewport } from './types';

export function toScreen(viewport: Viewport, [x, y]: Point): Point {
  return [(x - viewport.originM[0]) * viewport.pxPerM, (viewport.originM[1] - y) * viewport.pxPerM];
}

export function toModel(viewport: Viewport, [px, py]: Point): Point {
  return [viewport.originM[0] + px / viewport.pxPerM, viewport.originM[1] - py / viewport.pxPerM];
}

/** The visible model rectangle, grown by `margin` of its own size on every side. */
export function viewportBoundsM(viewport: Viewport, margin = 0): BoundingBox {
  const widthM = viewport.widthPx / viewport.pxPerM;
  const heightM = viewport.heightPx / viewport.pxPerM;
  const [ox, oy] = viewport.originM;
  return [
    ox - widthM * margin,
    oy - heightM - heightM * margin,
    ox + widthM + widthM * margin,
    oy + heightM * margin,
  ];
}

export function cullBoundsM(viewport: Viewport): BoundingBox {
  return viewportBoundsM(viewport, CULL_MARGIN);
}

export function intersects(a: BoundingBox, b: BoundingBox): boolean {
  return a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
}
