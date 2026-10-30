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

/** The pattern families; within one layer no two values share a family. */
export type ConditionPatternKind =
  | 'rising'
  | 'vertical'
  | 'falling'
  | 'crosshatch'
  | 'checker'
  | 'waves'
  | 'dashes'
  | 'drops'
  | 'dot'
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
  /** Where the glyph sits in the bed, so three layers on at once never stack their glyphs. */
  corner: 'topRight' | 'bottomRight' | 'bottomLeft';
  /** The theme colour family of the ink; it only follows the pattern, it never replaces it. */
  tone: 'warning' | 'info' | 'secondary';
}

const HORIZON: GlyphPart = { d: 'M0 10.5H12' };
const FLAKE = 'M6 1.5V10.5M2.1 3.75L9.9 8.25M2.1 8.25L9.9 3.75';

export const SUN_CONDITION: ConditionSpec<Exclude<SunWindow, 'unknown'>> = {
  id: 'sun',
  values: ['morning', 'midday', 'afternoon', 'all_day', 'mixed'],
  patterns: { morning: 'rising', midday: 'vertical', afternoon: 'falling', all_day: 'crosshatch', mixed: 'checker' },
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
  corner: 'topRight',
  tone: 'warning',
};

export const MOISTURE_CONDITION: ConditionSpec<Exclude<SoilDrainage, 'unknown'>> = {
  id: 'moisture',
  values: ['poor', 'moderate', 'good'],
  patterns: { poor: 'waves', moderate: 'dashes', good: 'drops' },
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
  corner: 'bottomRight',
  tone: 'info',
};

export const FROST_CONDITION: ConditionSpec<Exclude<FrostRisk, 'unknown'>> = {
  id: 'frost',
  values: ['low', 'normal', 'high'],
  patterns: { low: 'dot', normal: 'plus', high: 'star' },
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
  corner: 'bottomLeft',
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
  switch (kind) {
    case 'rising':
      return <path d={`M0 ${num(tile)}L${num(tile)} 0`} {...stroke} />;
    case 'vertical':
      return <path d={`M${num(h)} 0V${num(tile)}`} {...stroke} />;
    case 'falling':
      return <path d={`M0 0L${num(tile)} ${num(tile)}`} {...stroke} />;
    case 'crosshatch':
      return <path d={`M0 0L${num(tile)} ${num(tile)}M0 ${num(tile)}L${num(tile)} 0`} {...stroke} />;
    case 'checker':
      return <rect x="0" y="0" width={num(h)} height={num(h)} fill={color} fillOpacity={0.45} />;
    case 'waves':
      return (
        <path
          d={`M0 ${num(h)}Q${num(tile / 4)} ${num(h - tile / 4)} ${num(h)} ${num(h)}T${num(tile)} ${num(h)}`}
          {...stroke}
        />
      );
    case 'dashes':
      return <path d={`M${num(tile / 4)} ${num(h)}H${num((tile * 3) / 4)}`} {...stroke} />;
    case 'drops':
      return <circle cx={num(h)} cy={num(h)} r={num(line)} fill={color} />;
    case 'dot':
      return <circle cx={num(h)} cy={num(h)} r={num(line * 0.75)} fill={color} />;
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

function glyphOrigin(entry: ShapeEntry, corner: ConditionSpec<string>['corner'], size: number, pad: number) {
  const [minX, minY, maxX, maxY] = entry.bbox;
  switch (corner) {
    case 'topRight':
      return [maxX - pad - size, -maxY + pad] as const;
    case 'bottomRight':
      return [maxX - pad - size, -minY - pad - size] as const;
    case 'bottomLeft':
      return [minX + pad, -minY - pad - size] as const;
  }
}

interface ConditionLayerProps<V extends string> {
  spec: ConditionSpec<V>;
  shapes: readonly SceneShape[];
  pxPerM: number;
  theme: Theme;
}

/** One condition layer over the beds of the scene that carry a value. */
export function ConditionLayer<V extends string>({ spec, shapes, pxPerM, theme }: ConditionLayerProps<V>) {
  const ink = conditionInk(theme, spec.tone);
  const tile = PATTERN_TILE_PX / pxPerM;
  const line = LINE_PX / pxPerM;
  const size = GLYPH_PX / pxPerM;
  const pad = GLYPH_PAD_PX / pxPerM;
  return (
    <g data-testid={`garden-plan-${spec.id}-layer`} aria-hidden="true" pointerEvents="none">
      <defs>
        {spec.values.map((value) => (
          <pattern
            key={value}
            id={conditionPatternId(spec.id, value)}
            data-condition-pattern={spec.patterns[value]}
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
        const [gx, gy] = glyphOrigin(entry, spec.corner, size, pad);
        return (
          <g key={entry.key} data-condition-bed={entry.key} data-condition-value={value}>
            <Outline entry={entry} fill={`url(#${conditionPatternId(spec.id, value)})`} />
            {shape.showLabel ? (
              <ConditionGlyph
                parts={spec.glyphs[value]}
                x={gx}
                y={gy}
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
