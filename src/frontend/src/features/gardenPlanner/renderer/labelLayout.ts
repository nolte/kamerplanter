/**
 * Label placement on the plan (REQ-053 GP-UX-047, GP-NFR-067): where a name sits, how far it is shortened and which
 * name gives way when two collide. Renderer-independent, like the scene it feeds.
 *
 * - The anchor is the shared `labelAnchor` (the pole of inaccessibility of a polygon, the centre of a rect or
 *   circle) - the point the PDF writer uses too (GP-FR-003). It is cached per geometry object: an edit replaces only
 *   the geometry it touches (structural sharing), so a pan or an unrelated edit never searches a pole again.
 * - A name is shortened with "…" to the room a centred label has at the anchor (the PDF's rule, with the canvas font).
 * - When two labels overlap on screen, the larger object keeps its name (GP-UX-047); equal areas resolve by paint
 *   order, so the same data and viewport always give the same picture (GP-FR-003).
 */
import { areaM2 } from '../model/geometry';
import { labelAnchor, truncateLabel, type LabelAnchor } from '../model/labelAnchor';
import type { Geometry } from '../model/types';
import { ICON_SIZE_PX } from './lod';
import type { ShapeEntry } from './planIndex';

/** Average glyph width as a share of the font size: the estimate every label fit on the canvas uses. */
export const GLYPH_WIDTH_EM = 0.6;
/** A shortened name keeps at least this many characters (two letters and the ellipsis). */
const MIN_LABEL_CHARS = 3;
/** Half the height a plain label takes about its anchor, as a share of the font size (it is centred there). */
const HALF_LINE_EM = 0.6;
/** Below its baseline a name reaches this share of the font size. */
const DESCENT_EM = 0.25;
/** The gap between an object's type icon and its name below it, as a share of the font size. */
export const ICON_LINE_GAP_EM = 0.9;

const anchorCache = new WeakMap<Geometry, LabelAnchor>();

/** {@link labelAnchor}, computed once per geometry object. */
export function labelAnchorOf(geometry: Geometry): LabelAnchor {
  let cached = anchorCache.get(geometry);
  if (!cached) {
    cached = labelAnchor(geometry);
    anchorCache.set(geometry, cached);
  }
  return cached;
}

/** The characters a label `roomPx` wide holds at `fontPx`. */
export function labelChars(roomPx: number, fontPx: number): number {
  return Math.max(MIN_LABEL_CHARS, Math.floor(roomPx / (fontPx * GLYPH_WIDTH_EM)));
}

/** The name as drawn: shortened with "…" to the room a centred label has at the anchor (as in the PDF). */
export function fitLabel(name: string, geometry: Geometry, pxPerM: number, fontPx: number): string {
  return truncateLabel(name, labelChars(labelAnchorOf(geometry).widthM * pxPerM, fontPx));
}

/** The size that decides a label collision: the object's area, else its box (a path or a point has no area). */
export function labelWeight(entry: ShapeEntry): number {
  return entry.areaM2 || areaM2(entry.geometry) || entry.bboxAreaM2;
}

export interface LabelCandidate {
  key: string;
  text: string;
  /** Anchor in metres (plan frame). */
  x: number;
  y: number;
  /** The type icon is drawn above the name and takes room too. */
  withIcon: boolean;
  weight: number;
  /** Paint order of the object: the tie-break of equal weights. */
  order: number;
}

type ScreenBox = readonly [number, number, number, number];

function screenBox(candidate: LabelCandidate, pxPerM: number, fontPx: number): ScreenBox {
  const cx = candidate.x * pxPerM;
  const cy = -candidate.y * pxPerM;
  const textWidth = candidate.text.length * fontPx * GLYPH_WIDTH_EM;
  if (!candidate.withIcon) {
    const half = HALF_LINE_EM * fontPx;
    return [cx - textWidth / 2, cy - half, cx + textWidth / 2, cy + half];
  }
  // As drawn: the icon centred one gap above the anchor, the name's baseline one gap below it.
  const gap = ICON_LINE_GAP_EM * fontPx;
  const width = Math.max(textWidth, ICON_SIZE_PX);
  return [cx - width / 2, cy - gap - ICON_SIZE_PX / 2, cx + width / 2, cy + gap + DESCENT_EM * fontPx];
}

function overlap(a: ScreenBox, b: ScreenBox): boolean {
  return a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
}

/**
 * The keys whose labels stay: candidates are taken from the largest object down, and one whose box would overlap a
 * label already kept gives way (GP-UX-047).
 */
export function resolveLabelCollisions(
  candidates: readonly LabelCandidate[],
  pxPerM: number,
  fontPx: number,
): Set<string> {
  const ranked = [...candidates].sort((a, b) => b.weight - a.weight || a.order - b.order);
  const kept: ScreenBox[] = [];
  const keys = new Set<string>();
  for (const candidate of ranked) {
    const box = screenBox(candidate, pxPerM, fontPx);
    if (kept.some((other) => overlap(box, other))) continue;
    kept.push(box);
    keys.add(candidate.key);
  }
  return keys;
}
