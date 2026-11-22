import type { Theme } from '@mui/material/styles';
import type { Point } from '../model/types';
import type { Viewport } from './types';
import { cullBoundsM, intersects } from './viewport';

/**
 * The lines of the companion-planting layer (REQ-053 GP-FR-134): one line between two neighbouring occupied slots,
 * judged by the server with the planting dialog's rule. Pure and cheap: the viewport culling runs before anything is
 * drawn, so a pan over a dense plan never puts more than {@link COMPANION_LINE_CAP} lines into the DOM.
 */

export type CompanionLineStatus = 'compatible' | 'incompatible' | 'unknown';

export interface CompanionLine {
  /** `<bed key>:<slot a>|<slot b>`, unique on the plan; the info card looks the edge up by it. */
  id: string;
  a: Point;
  b: Point;
  status: CompanionLineStatus;
}

/** GP-FR-134: at most this many lines per viewport. */
export const COMPANION_LINE_CAP = 500;

/** The server judges at most this many species per slot (`species_truncated` says when it cut). */
export const COMPANION_SPECIES_CAP = 8;

/** Draw and legend order; the cap keeps the strongest statements: an incompatibility is never cut for an unknown. */
export const COMPANION_STATUSES: readonly CompanionLineStatus[] = ['incompatible', 'compatible', 'unknown'];

export interface CompanionLineStyle {
  /** `stroke-dasharray` in screen pixels (the stroke is non-scaling); `none` is a solid line. */
  dash: string;
  widthPx: number;
}

/**
 * The status is carried by the dash pattern AND the colour (WCAG 1.4.1): solid = compatible, dashed = incompatible,
 * dotted = unknown, so the three stay apart in greyscale. The dotted line uses round caps on a near-zero dash.
 */
export const COMPANION_LINE_STYLES: Readonly<Record<CompanionLineStatus, CompanionLineStyle>> = {
  compatible: { dash: 'none', widthPx: 2 },
  incompatible: { dash: '8 5', widthPx: 2.5 },
  unknown: { dash: '0.1 5', widthPx: 2.5 },
};

/** Width of the invisible stroke that takes hover and tap: 24 px (WCAG 2.5.8 target size). */
export const COMPANION_HIT_WIDTH_PX = 24;

/** The colour follows the dash, it never replaces it: green, red and the neutral text grey (3:1 on the canvas). */
export function companionInk(theme: Theme, status: CompanionLineStatus): string {
  const { palette } = theme;
  const dark = palette.mode === 'dark';
  switch (status) {
    case 'compatible':
      return dark ? palette.success.light : palette.success.dark;
    case 'incompatible':
      return dark ? palette.error.light : palette.error.main;
    default:
      return palette.text.secondary;
  }
}

export interface CulledCompanionLines {
  lines: CompanionLine[];
  /** Lines inside the viewport (plus the culling margin) before the cap. */
  candidates: number;
  /** `true` when the cap cut lines that were in view. */
  capped: boolean;
}

/**
 * The lines to draw in `viewport`: those whose segment box meets the culled viewport, ordered incompatible ->
 * compatible -> unknown (stable within a status), and at most `cap` of them. One pass, no sort.
 */
export function cullCompanionLines(
  lines: readonly CompanionLine[],
  viewport: Viewport,
  cap: number = COMPANION_LINE_CAP,
): CulledCompanionLines {
  const bounds = cullBoundsM(viewport);
  const buckets: Record<CompanionLineStatus, CompanionLine[]> = { incompatible: [], compatible: [], unknown: [] };
  let candidates = 0;
  for (const line of lines) {
    const [ax, ay] = line.a;
    const [bx, by] = line.b;
    const box: [number, number, number, number] = [
      Math.min(ax, bx),
      Math.min(ay, by),
      Math.max(ax, bx),
      Math.max(ay, by),
    ];
    if (!intersects(box, bounds)) continue;
    candidates += 1;
    buckets[line.status].push(line);
  }
  const ordered: CompanionLine[] = [];
  for (const status of COMPANION_STATUSES) {
    for (const line of buckets[status]) {
      if (ordered.length >= cap) break;
      ordered.push(line);
    }
  }
  return { lines: ordered, candidates, capped: candidates > ordered.length };
}
