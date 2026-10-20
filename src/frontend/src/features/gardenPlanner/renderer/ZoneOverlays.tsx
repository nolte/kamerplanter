import { useMemo } from 'react';
import type { Theme } from '@mui/material/styles';
import { centroid } from '../model/geometry';
import type { SceneShape } from './scene';
import type { ShapeEntry } from './planIndex';
import type { RenderOptions, WateredLayerEntry, ZoneLayerEntry } from './types';

/**
 * The zone layer and the "last watered" layer (REQ-053 GP-FR-110, GP-UX-031): outlines and hatchings drawn over
 * the beds. Both are decorative (`aria-hidden`, no pointer events): the facts are in the zone panel, the
 * properties panel and the legend. Every class has a pattern of its own, so no meaning rests on colour alone
 * (WCAG 1.4.1). A pattern's unit is a metre like everything else in the viewBox, hence the `/ pxPerM`.
 */

const PATTERN_TILE_PX = 8;
const LINE_PX = 1.6;

function num(value: number): string {
  return String(Number(value.toFixed(3)));
}

function pathOf(entry: ShapeEntry): string {
  const { shape } = entry;
  if (shape.kind === 'circle') return '';
  return `M${shape.vertices.map(([x, y]) => `${num(x)} ${num(-y)}`).join('L')}${shape.closed ? 'Z' : ''}`;
}

interface OutlineProps {
  entry: ShapeEntry;
  fill: string;
  stroke: string;
  strokeWidth?: number;
  strokeOpacity?: number;
  strokeDasharray?: string;
}

function Outline({ entry, ...paint }: OutlineProps) {
  const { shape } = entry;
  if (shape.kind === 'circle') {
    return (
      <circle
        cx={num(shape.center[0])}
        cy={num(-shape.center[1])}
        r={num(shape.radiusM)}
        vectorEffect="non-scaling-stroke"
        {...paint}
      />
    );
  }
  return <path d={pathOf(entry)} vectorEffect="non-scaling-stroke" {...paint} />;
}

/** The four hatching variants of a zone: angle and dash differ, the colour is the zone's own. */
export const ZONE_VARIANTS = [
  { angle: 45, dash: undefined },
  { angle: 135, dash: '10 4' },
  { angle: 0, dash: '3 3' },
  { angle: 90, dash: '12 4 3 4' },
] as const;



const zonePatternId = (variant: number): string => `gp-zone-hatch-${variant % ZONE_VARIANTS.length}`;

interface ZoneLayerProps {
  shapes: readonly SceneShape[];
  zones: readonly ZoneLayerEntry[];
  pxPerM: number;
  theme: Theme;
}

export function ZoneLayer({ shapes, zones, pxPerM, theme }: ZoneLayerProps) {
  const byKey = useMemo(() => new Map(shapes.map((shape) => [shape.entry.key, shape.entry])), [shapes]);
  const tile = PATTERN_TILE_PX / pxPerM;
  return (
    <g data-testid="garden-plan-zone-layer" aria-hidden="true" pointerEvents="none">
      <defs>
        {zones.map((zone) => {
          const variant = ZONE_VARIANTS[zone.variant % ZONE_VARIANTS.length];
          return (
            <pattern
              key={zone.key}
              id={`${zonePatternId(zone.variant)}-${zone.key}`}
              patternUnits="userSpaceOnUse"
              width={num(tile)}
              height={num(tile)}
              patternTransform={`rotate(${variant.angle})`}
            >
              <line x1="0" y1="0" x2="0" y2={num(tile)} stroke={zone.color} strokeWidth={num(LINE_PX / pxPerM)} />
            </pattern>
          );
        })}
      </defs>
      {zones.flatMap((zone) =>
        zone.locationKeys.map((bedKey) => {
          const entry = byKey.get(bedKey);
          if (!entry) return null;
          const variant = ZONE_VARIANTS[zone.variant % ZONE_VARIANTS.length];
          return (
            <g key={`${zone.key}:${bedKey}`} data-zone-key={zone.key} data-zone-bed={bedKey}>
              <Outline entry={entry} fill={`url(#${zonePatternId(zone.variant)}-${zone.key})`} stroke="none" />
              <Outline
                entry={entry}
                fill="none"
                stroke={theme.palette.background.paper}
                strokeWidth={6}
                strokeOpacity={0.9}
              />
              <Outline
                entry={entry}
                fill="none"
                stroke={zone.color}
                strokeWidth={3}
                strokeDasharray={variant.dash}
              />
            </g>
          );
        }),
      )}
    </g>
  );
}

/** One pattern per class; the order is the order of the legend. Colour follows the patterns, never replaces them. */
export const WATERED_PATTERNS: Record<WateredLayerEntry['wateredClass'], 'dots' | 'cross' | 'diagonal' | 'sparse'> = {
  d0_1: 'dots',
  d2_3: 'cross',
  d4_7: 'diagonal',
  d8plus: 'sparse',
};

/** The shared body of a pattern tile, also used by the legend swatches (same look, same meaning). */
export function WateredPatternTile({
  kind,
  tile,
  line,
  color,
}: {
  kind: (typeof WATERED_PATTERNS)[WateredLayerEntry['wateredClass']];
  tile: number;
  line: number;
  color: string;
}) {
  switch (kind) {
    case 'dots':
      return <circle cx={num(tile / 2)} cy={num(tile / 2)} r={num(line * 1.4)} fill={color} />;
    case 'cross':
      return (
        <path
          d={`M0 ${num(tile / 2)}H${num(tile)}M${num(tile / 2)} 0V${num(tile)}`}
          stroke={color}
          strokeWidth={num(line)}
          fill="none"
        />
      );
    case 'diagonal':
      return (
        <path d={`M0 ${num(tile)}L${num(tile)} 0`} stroke={color} strokeWidth={num(line)} fill="none" />
      );
    case 'sparse':
      return <path d={`M0 ${num(tile / 2)}H${num(tile / 3)}`} stroke={color} strokeWidth={num(line)} fill="none" />;
  }
}

const wateredPatternId = (wateredClass: WateredLayerEntry['wateredClass']): string =>
  `gp-watered-${wateredClass}`;

interface WateredLayerProps {
  shapes: readonly SceneShape[];
  layer: NonNullable<RenderOptions['wateredLayer']>;
  pxPerM: number;
  fontPx: number;
  theme: Theme;
}

export function WateredLayer({ shapes, layer, pxPerM, fontPx, theme }: WateredLayerProps) {
  const ink = theme.palette.mode === 'dark' ? theme.palette.info.light : theme.palette.info.dark;
  const tile = (PATTERN_TILE_PX + 2) / pxPerM;
  const line = LINE_PX / pxPerM;
  const classes = Object.keys(WATERED_PATTERNS) as (keyof typeof WATERED_PATTERNS)[];
  return (
    <g data-testid="garden-plan-watered-layer" aria-hidden="true" pointerEvents="none">
      <defs>
        {classes.map((wateredClass) => (
          <pattern
            key={wateredClass}
            id={wateredPatternId(wateredClass)}
            patternUnits="userSpaceOnUse"
            width={num(tile)}
            height={num(tile)}
          >
            <WateredPatternTile kind={WATERED_PATTERNS[wateredClass]} tile={tile} line={line} color={ink} />
          </pattern>
        ))}
      </defs>
      {shapes.map((shape) => {
        const watered = layer.byBed[shape.entry.key];
        if (!watered || shape.entry.kind !== 'location') return null;
        const [cx, cy] = centroid(shape.entry.geometry);
        return (
          <g key={shape.entry.key} data-watered-bed={shape.entry.key} data-watered-class={watered.wateredClass}>
            <Outline entry={shape.entry} fill={`url(#${wateredPatternId(watered.wateredClass)})`} stroke="none" />
            {shape.showLabel ? (
              <text
                x={num(cx)}
                y={num(-cy + (fontPx * 1.9) / pxPerM)}
                textAnchor="middle"
                fontSize={num(fontPx / pxPerM)}
                fill={theme.palette.text.primary}
                stroke={theme.palette.background.paper}
                strokeWidth={num(3 / pxPerM)}
                paintOrder="stroke"
              >
                {layer.label(watered.days)}
              </text>
            ) : null}
          </g>
        );
      })}
    </g>
  );
}
