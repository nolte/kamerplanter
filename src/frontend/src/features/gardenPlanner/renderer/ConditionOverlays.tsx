import { memo } from 'react';
import type { Theme } from '@mui/material/styles';
import type { FrostRisk, PlanLocation, SoilDrainage, SunWindow } from '../model/types';
import type { SceneShape } from './scene';
import type { ShapeEntry } from './planIndex';

/**
 * The site-condition layers of the plan (REQ-053 GP-FR-169, GP-FR-047): sun window, drainage ("moisture") and
 * frost risk of a bed, read from the plan's lean site conditions (#2538). Every value has a pattern AND a small
 * glyph of its own, so no meaning rests on colour alone (WCAG 1.4.1) and the values stay apart in greyscale
 * (as GP-ACC-052). A bed whose value is not known gets nothing - the layer never invents a value (E-10).
 * Like the zone layers, the overlays are decorative (`aria-hidden`, no pointer events): the facts are in the
 * properties panel, the bed page and the legend.
 */

export type ConditionLayerId = 'sun' | 'moisture' | 'frost';

/**
 * The pattern families. No two values share a family - not within a layer and not across the plan: the zone
 * hatchings (straight parallel lines at 0, 45, 90 and 135 degrees) and the "last watered" patterns (dots, grid,
 * zigzag, short dashes) are families of their own, so a pattern alone always names one value even with several
 * layers on and no glyph drawn (WCAG 1.4.1).
 */
export type ConditionPatternKind =
  | 'triangleUp'
  | 'ring'
  | 'triangleDown'
  | 'diamond'
  | 'checker'
  | 'waves'
  | 'drops'
  | 'arrows'
  | 'xmark'
  | 'plus'
  | 'star';

/** One stroke (or filled) path of a glyph in a 12 x 12 box. */
export interface GlyphPart {
  d: string;
  filled?: boolean;
}

export interface ConditionSpec<V extends string> {
  id: ConditionLayerId;
  /** The known values in legend order (`unknown` is never drawn). */
  values: readonly V[];
  patterns: Readonly<Record<V, ConditionPatternKind>>;
  glyphs: Readonly<Record<V, readonly GlyphPart[]>>;
  /** The bed's value, `undefined` when not known. */
  read: (location: PlanLocation) => V | undefined;
  /**
   * The glyph's place in the row along the bottom edge of the bed (0 = left), one per layer, so three layers on at
   * once never stack their glyphs and the top edge stays free for the zone number and the task badge.
   */
  slot: 0 | 1 | 2;
  /** The theme colour family of the ink; it only follows the pattern, it never replaces it. */
  tone: 'warning' | 'info' | 'secondary';
}

const HORIZON: GlyphPart = { d: 'M0 10.5H12' };
const FLAKE = 'M6 1.5V10.5M2.1 3.75L9.9 8.25M2.1 8.25L9.9 3.75';

export const SUN_CONDITION: ConditionSpec<Exclude<SunWindow, 'unknown'>> = {
  id: 'sun',
  values: ['morning', 'midday', 'afternoon', 'all_day', 'mixed'],
  patterns: {
    morning: 'triangleUp',
    midday: 'ring',
    afternoon: 'triangleDown',
    all_day: 'diamond',
    mixed: 'checker',
  },
  glyphs: {
    // The sun low on the left of the horizon, high in the middle, low on the right; a full sun with rays; half a sun.
    morning: [HORIZON, { d: 'M0.5 10.5A3.5 3.5 0 0 1 7.5 10.5Z', filled: true }],
    midday: [HORIZON, { d: 'M3.5 4.5A2.5 2.5 0 1 0 8.5 4.5A2.5 2.5 0 1 0 3.5 4.5Z', filled: true }],
    afternoon: [HORIZON, { d: 'M4.5 10.5A3.5 3.5 0 0 1 11.5 10.5Z', filled: true }],
    all_day: [
      { d: 'M3.5 6A2.5 2.5 0 1 0 8.5 6A2.5 2.5 0 1 0 3.5 6Z', filled: true },
      { d: 'M6 0.5V2.5M6 9.5V11.5M0.5 6H2.5M9.5 6H11.5M2.1 2.1L3.5 3.5M8.5 8.5L9.9 9.9M2.1 9.9L3.5 8.5M8.5 3.5L9.9 2.1' },
    ],
    mixed: [{ d: 'M2 6A4 4 0 1 0 10 6A4 4 0 1 0 2 6Z' }, { d: 'M6 2A4 4 0 0 0 6 10Z', filled: true }],
  },
  read: (location) => {
    const value = location.site_conditions?.sun_profile?.sun_window;
    return value && value !== 'unknown' ? value : undefined;
  },
  slot: 0,
  tone: 'warning',
};

export const MOISTURE_CONDITION: ConditionSpec<Exclude<SoilDrainage, 'unknown'>> = {
  id: 'moisture',
  values: ['poor', 'moderate', 'good'],
  // Standing water, a drop, water running off - the same pictures as the glyphs.
  patterns: { poor: 'waves', moderate: 'drops', good: 'arrows' },
  glyphs: {
    // Water standing (two waves), a drop, water running off (an arrow through the ground).
    poor: [{ d: 'M0 4Q1.5 2.5 3 4T6 4T9 4T12 4M0 8.5Q1.5 7 3 8.5T6 8.5T9 8.5T12 8.5' }],
    moderate: [{ d: 'M6 1C6 1 2.5 5.5 2.5 7.5A3.5 3.5 0 0 0 9.5 7.5C9.5 5.5 6 1 6 1Z' }],
    good: [{ d: 'M0 4H12M6 0.5V11M3 8L6 11L9 8' }],
  },
  read: (location) => {
    const value = location.soil_profile?.drainage;
    return value && value !== 'unknown' ? value : undefined;
  },
  slot: 1,
  tone: 'info',
};

export const FROST_CONDITION: ConditionSpec<Exclude<FrostRisk, 'unknown'>> = {
  id: 'frost',
  values: ['low', 'normal', 'high'],
  patterns: { low: 'xmark', normal: 'plus', high: 'star' },
  glyphs: {
    // A small cross, a snowflake, a snowflake in a warning triangle.
    low: [{ d: 'M4 4L8 8M4 8L8 4' }],
    normal: [{ d: FLAKE }],
    high: [{ d: 'M6 0.5L11.5 11.5H0.5Z' }, { d: 'M6 5V10M3.85 6.25L8.15 8.75M3.85 8.75L8.15 6.25' }],
  },
  read: (location) => {
    const value = location.site_conditions?.microclimate?.frost_risk;
    return value && value !== 'unknown' ? value : undefined;
  },
  slot: 2,
  tone: 'secondary',
};

/** The three layers in the order of the view bar and the legend. */
export const CONDITION_SPECS = [SUN_CONDITION, MOISTURE_CONDITION, FROST_CONDITION] as const;

/** The ink of a layer: the dark shade on a light canvas, the light shade on a dark one. */
export function conditionInk(theme: Theme, tone: ConditionSpec<string>['tone']): string {
  const family = theme.palette[tone];
  return theme.palette.mode === 'dark' ? family.light : family.dark;
}

const PATTERN_TILE_PX = 10;
const LINE_PX = 1.4;
const GLYPH_PX = 14;
const GLYPH_PAD_PX = 4;
/** The distance between the glyphs of the row: wider than a glyph with its backdrop, so they never touch. */
const GLYPH_PITCH_PX = 20;
/** The round backdrop (r 7.5 around the centre of the 12-unit box) reaches this far past the glyph's box. */
const GLYPH_BACKDROP_PX = (GLYPH_PX * 1.5) / 12;
/**
 * The band along the top edge of a bed that no glyph enters: the task badge (22 px high, top-right) and the zone
 * number (13 px, top-left) live there. On a circle the band hangs from the badge's place on the rim.
 */
export const GLYPH_TOP_RESERVE_PX = 24;

function num(value: number): string {
  return String(Number(value.toFixed(3)));
}

/** The shared body of a pattern tile, also used by the legend swatches (same look, same meaning). */
export function ConditionPatternTile({
  kind,
  tile,
  line,
  color,
}: {
  kind: ConditionPatternKind;
  tile: number;
  line: number;
  color: string;
}) {
  const h = tile / 2;
  const stroke = { stroke: color, strokeWidth: num(line), fill: 'none' };
  const fill = { fill: color };
  switch (kind) {
    case 'triangleUp':
      return <path d={`M${num(h)} ${num(h - tile * 0.25)}L${num(h + tile * 0.25)} ${num(h + tile * 0.2)}L${num(h - tile * 0.25)} ${num(h + tile * 0.2)}Z`} {...fill} />;
    case 'triangleDown':
      return <path d={`M${num(h)} ${num(h + tile * 0.25)}L${num(h + tile * 0.25)} ${num(h - tile * 0.2)}L${num(h - tile * 0.25)} ${num(h - tile * 0.2)}Z`} {...fill} />;
    case 'ring':
      return <circle cx={num(h)} cy={num(h)} r={num(tile * 0.22)} {...stroke} />;
    case 'diamond': {
      const q = tile * 0.3;
      return <path d={`M${num(h)} ${num(h - q)}L${num(h + q)} ${num(h)}L${num(h)} ${num(h + q)}L${num(h - q)} ${num(h)}Z`} {...stroke} />;
    }
    case 'checker':
      // Full ink: the pattern alone carries the value, so it has to reach 3:1 like every other mark (WCAG 1.4.11).
      return <rect x="0" y="0" width={num(h)} height={num(h)} {...fill} />;
    case 'waves':
      return (
        <path
          d={`M0 ${num(h)}Q${num(tile / 4)} ${num(h - tile / 4)} ${num(h)} ${num(h)}T${num(tile)} ${num(h)}`}
          {...stroke}
        />
      );
    case 'drops': {
      // A real drop: a point on top, a round belly below.
      const w = tile * 0.2;
      const belly = h + tile * 0.1;
      return (
        <path
          d={`M${num(h)} ${num(h - tile * 0.32)}Q${num(h + w)} ${num(belly - tile * 0.12)} ${num(h + w)} ${num(belly)}A${num(w)} ${num(w)} 0 0 1 ${num(h - w)} ${num(belly)}Q${num(h - w)} ${num(belly - tile * 0.12)} ${num(h)} ${num(h - tile * 0.32)}Z`}
          {...fill}
        />
      );
    }
    case 'arrows': {
      const q = tile * 0.18;
      const tip = h + tile * 0.28;
      return (
        <path
          d={`M${num(h)} ${num(h - tile * 0.3)}V${num(tip)}M${num(h - q)} ${num(tip - q)}L${num(h)} ${num(tip)}L${num(h + q)} ${num(tip - q)}`}
          {...stroke}
        />
      );
    }
    case 'xmark': {
      const q = tile * 0.2;
      return <path d={`M${num(h - q)} ${num(h - q)}L${num(h + q)} ${num(h + q)}M${num(h - q)} ${num(h + q)}L${num(h + q)} ${num(h - q)}`} {...stroke} />;
    }
    case 'plus':
      return <path d={`M${num(h)} ${num(h - tile / 4)}V${num(h + tile / 4)}M${num(h - tile / 4)} ${num(h)}H${num(h + tile / 4)}`} {...stroke} />;
    case 'star': {
      const r = tile / 3;
      const d = r * 0.7;
      return (
        <path
          d={`M${num(h)} ${num(h - r)}V${num(h + r)}M${num(h - r)} ${num(h)}H${num(h + r)}M${num(h - d)} ${num(h - d)}L${num(h + d)} ${num(h + d)}M${num(h - d)} ${num(h + d)}L${num(h + d)} ${num(h - d)}`}
          {...stroke}
        />
      );
    }
  }
}

/**
 * A value's glyph, `size` wide, with its top-left at (`x`, `y`) of the caller's coordinate system; a round backdrop
 * in the canvas colour keeps it legible over any pattern. Also used by the legend.
 */
export function ConditionGlyph({
  parts,
  x,
  y,
  size,
  color,
  backdrop,
  value,
}: {
  parts: readonly GlyphPart[];
  x: number;
  y: number;
  size: number;
  color: string;
  backdrop: string;
  value: string;
}) {
  return (
    <g transform={`translate(${num(x)} ${num(y)}) scale(${num(size / 12)})`} data-condition-glyph={value}>
      <circle cx="6" cy="6" r="7.5" fill={backdrop} fillOpacity={0.9} />
      {parts.map((part) => (
        <path
          key={part.d}
          d={part.d}
          fill={part.filled ? color : 'none'}
          stroke={color}
          strokeWidth="1.4"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

export const conditionPatternId = (layer: ConditionLayerId, value: string): string => `gp-${layer}-${value}`;

function Outline({ entry, fill }: { entry: ShapeEntry; fill: string }) {
  const { shape } = entry;
  if (shape.kind === 'circle') {
    return <circle cx={num(shape.center[0])} cy={num(-shape.center[1])} r={num(shape.radiusM)} fill={fill} />;
  }
  const d = `M${shape.vertices.map(([x, y]) => `${num(x)} ${num(-y)}`).join('L')}${shape.closed ? 'Z' : ''}`;
  return <path d={d} fill={fill} />;
}

/**
 * The top-left of a layer's glyph box in drawing coordinates (y flipped), or `null` when the bed has no room for it
 * below the top band (badge, zone number) - then the pattern alone tells the value, as below label zoom.
 * A rectangle lines the glyphs up along its bottom edge from the left; a circle centres the row on the lowest
 * chord that still holds all three, as the task badge moves to the rim on a circle.
 */
export function glyphOrigin(entry: ShapeEntry, slot: ConditionSpec<string>['slot'], pxPerM: number): [number, number] | null {
  const size = GLYPH_PX / pxPerM;
  const pitch = GLYPH_PITCH_PX / pxPerM;
  const backdrop = GLYPH_BACKDROP_PX / pxPerM;
  const reserve = GLYPH_TOP_RESERVE_PX / pxPerM;
  const { shape } = entry;
  let x: number;
  let y: number;
  let bandBottom: number;
  if (shape.kind === 'circle') {
    const [cx, cy] = [shape.center[0], -shape.center[1]];
    const r = shape.radiusM;
    // The row's backdrops keep the same distance to the rim as they keep to a rectangle's edge.
    const inset = (GLYPH_PAD_PX - GLYPH_BACKDROP_PX) / pxPerM;
    const halfWidth = pitch + size / 2 + backdrop;
    const halfHeight = size / 2 + backdrop;
    const reach = r - inset;
    if (reach < halfWidth) return null;
    const rowCentre = cy + Math.sqrt(reach * reach - halfWidth * halfWidth) - halfHeight;
    x = cx + (slot - 1) * pitch - size / 2;
    y = rowCentre - size / 2;
    bandBottom = cy - r * Math.SQRT1_2 + reserve;
  } else {
    const [minX, minY, maxX, maxY] = entry.bbox;
    const pad = GLYPH_PAD_PX / pxPerM;
    x = minX + pad + slot * pitch;
    y = -minY - pad - size;
    if (x + size + backdrop > maxX) return null;
    bandBottom = -maxY + reserve;
  }
  return y - backdrop >= bandBottom ? [x, y] : null;
}

interface ConditionLayerProps<V extends string> {
  spec: ConditionSpec<V>;
  shapes: readonly SceneShape[];
  pxPerM: number;
  theme: Theme;
}

/** One condition layer over the beds of the scene that carry a value. */
function ConditionLayerView<V extends string>({ spec, shapes, pxPerM, theme }: ConditionLayerProps<V>) {
  const ink = conditionInk(theme, spec.tone);
  const tile = PATTERN_TILE_PX / pxPerM;
  const line = LINE_PX / pxPerM;
  const size = GLYPH_PX / pxPerM;
  return (
    <g data-testid={`garden-plan-${spec.id}-layer`} aria-hidden="true" pointerEvents="none">
      <defs>
        {spec.values.map((value) => (
          <pattern
            key={value}
            id={conditionPatternId(spec.id, value)}
            data-condition-pattern={spec.patterns[value]}
            data-pattern-family={spec.patterns[value]}
            patternUnits="userSpaceOnUse"
            width={num(tile)}
            height={num(tile)}
          >
            <ConditionPatternTile kind={spec.patterns[value]} tile={tile} line={line} color={ink} />
          </pattern>
        ))}
      </defs>
      {shapes.map((shape) => {
        const { entry } = shape;
        if (entry.kind !== 'location' || !entry.source) return null;
        const value = spec.read(entry.source as PlanLocation);
        if (value === undefined) return null;
        const origin = shape.showLabel ? glyphOrigin(entry, spec.slot, pxPerM) : null;
        return (
          <g key={entry.key} data-condition-bed={entry.key} data-condition-value={value}>
            <Outline entry={entry} fill={`url(#${conditionPatternId(spec.id, value)})`} />
            {origin ? (
              <ConditionGlyph
                parts={spec.glyphs[value]}
                x={origin[0]}
                y={origin[1]}
                size={size}
                color={ink}
                backdrop={theme.palette.background.paper}
                value={value}
              />
            ) : null}
          </g>
        );
      })}
    </g>
  );
}

/** Memoised like the shape nodes: a pan or a zoom-independent re-render leaves an unchanged layer alone. */
export const ConditionLayer = memo(ConditionLayerView) as typeof ConditionLayerView;
