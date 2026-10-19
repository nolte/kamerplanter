/**
 * What a plant marker draws for its state (REQ-053 GP-UX-059/060/062), as data: the ring style per
 * lifecycle and the shape and colour of the one attention badge. Colour is never the only carrier -
 * every lifecycle has its own ring (dashed, dotted with seeds, solid, double, crossed) and every badge its own
 * outline, so the five states stay apart in greyscale and for colour-blind viewers (GP-ACC-052).
 */
import type { AttentionCode, Lifecycle } from '../model/plantState';

export interface RingStyle {
  /** `stroke-dasharray` of the ring; `null` = solid. */
  dash: string | null;
  /** A second ring around the first ("Ring mit Erntesymbol"). */
  double: boolean;
  /** Seed dots inside the disc (direct sowing, before emergence). */
  seeds: boolean;
  /** A cross on an empty ring (failed plant, free place to replant). */
  cross: boolean;
  /** The disc is drawn faint (a place that is only planned) or not at all. */
  discOpacity: number;
  ringOpacity: number;
}

export const RING_STYLES: Readonly<Record<Lifecycle, RingStyle>> = {
  planned: { dash: '3 2', double: false, seeds: false, cross: false, discOpacity: 0.4, ringOpacity: 1 },
  sown: { dash: '1 2', double: false, seeds: true, cross: false, discOpacity: 0.4, ringOpacity: 1 },
  active: { dash: null, double: false, seeds: false, cross: false, discOpacity: 1, ringOpacity: 1 },
  harvesting: { dash: null, double: true, seeds: false, cross: false, discOpacity: 1, ringOpacity: 1 },
  failed: { dash: null, double: false, seeds: false, cross: true, discOpacity: 0, ringOpacity: 0.7 },
  historic: { dash: '6 3', double: false, seeds: false, cross: false, discOpacity: 0.5, ringOpacity: 0.7 },
};

export type BadgeShape = 'triangle' | 'hexagon' | 'circle' | 'drop' | 'square';

export interface BadgeStyle {
  shape: BadgeShape;
  /** Fill of the badge; the glyph and the outline are white. */
  fill: string;
  /** Outline path of the shape in a -1…1 box. */
  outline: string;
  /** Glyph strokes in the same box. */
  glyph: string;
}

/** White separates every badge from the bed in light and dark; the fills reach 3:1 against white (WCAG 1.4.11). */
export const BADGE_OUTLINE = '#FFFFFF';

export const BADGE_STYLES: Readonly<Record<AttentionCode, BadgeStyle>> = {
  problem: {
    shape: 'triangle',
    fill: '#B84300',
    outline: 'M0 -1L1 0.85L-1 0.85Z',
    glyph: 'M0 -0.3V0.3M0 0.55V0.58',
  },
  frost: {
    shape: 'hexagon',
    fill: '#01579B',
    outline: 'M0 -1L0.87 -0.5L0.87 0.5L0 1L-0.87 0.5L-0.87 -0.5Z',
    glyph: 'M0 -0.55V0.55M-0.48 -0.27L0.48 0.27M-0.48 0.27L0.48 -0.27',
  },
  overdue: {
    shape: 'circle',
    fill: '#C62828',
    outline: 'M0 -1A1 1 0 1 1 0 1A1 1 0 1 1 0 -1Z',
    glyph: 'M0 -0.5V0.1M0 0.45V0.48',
  },
  water: {
    shape: 'drop',
    fill: '#0D47A1',
    outline: 'M0 -1C0.8 -0.1 0.95 0.3 0.95 0.5A0.95 0.95 0 0 1 -0.95 0.5C-0.95 0.3 -0.8 -0.1 0 -1Z',
    glyph: 'M-0.35 0.45A0.4 0.4 0 0 0 0.05 0.85',
  },
  harvest: {
    shape: 'square',
    fill: '#1B5E20',
    outline: 'M-0.85 -0.85H0.85V0.85H-0.85Z',
    glyph: 'M-0.5 0L-0.1 0.42L0.55 -0.4',
  },
};

/** Share of the marker radius that the badge radius takes, and where its centre sits (upper right). */
export const BADGE_RADIUS_SHARE = 0.62;
export const BADGE_OFFSET_SHARE = 0.85;
/** Marker radius when it carries a state: large enough for a badge and the species initial. */
export const STATE_MARKER_RADIUS_PX = 9;
/** From this zoom (px/m) the ring also shows the phase progress (R-014). */
export const DETAIL_PX_PER_M = 100;

/** DOM id of the one open plant info bubble; the focused or hovered marker points at it (GP-UX-058). */
export const PLANT_INFO_ID = 'gp-plant-info';
