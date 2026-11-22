/**
 * The state channels of a plant marker (REQ-053 GP-UX-059/060): the phase-coloured disc with the species
 * initial (fill), the ring whose style tells the lifecycle, an optional progress arc of the phase and the one
 * attention badge in the upper right. Drawn into the marker's own `<g>` by the renderer; the group carries the
 * role, the `aria-label` and the handlers, so everything here is decorative (`aria-hidden`).
 */
import type { MarkerEntry } from './planIndex';
import {
  BADGE_OFFSET_SHARE,
  BADGE_OUTLINE,
  BADGE_RADIUS_SHARE,
  BADGE_STYLES,
  RING_STYLES,
} from './plantMarkerStyle';
import type { PlantMarkerState } from './types';
import type { AttentionCode } from '../model/plantState';

function num(value: number): string {
  return value.toFixed(4);
}

/**
 * An arc from twelve o'clock clockwise by `fraction` of the circle. A real path rather than a dashed circle:
 * with `non-scaling-stroke` a dash is measured in screen pixels, so a dash pattern would not follow the fraction.
 */
export function progressArc(cx: number, cy: number, r: number, fraction: number): string {
  const share = Math.min(Math.max(fraction, 0), 1);
  if (share >= 1) {
    // A full circle is two half arcs: one arc cannot start and end at the same point.
    return `M${num(cx)} ${num(cy - r)}A${num(r)} ${num(r)} 0 1 1 ${num(cx)} ${num(cy + r)}A${num(r)} ${num(r)} 0 1 1 ${num(cx)} ${num(cy - r)}`;
  }
  const angle = share * 2 * Math.PI;
  const x = cx + r * Math.sin(angle);
  const y = cy - r * Math.cos(angle);
  return `M${num(cx)} ${num(cy - r)}A${num(r)} ${num(r)} 0 ${share > 0.5 ? 1 : 0} 1 ${num(x)} ${num(y)}`;
}

interface BadgeProps {
  code: AttentionCode;
  x: number;
  y: number;
  /** Radius in model units (metres). */
  radius: number;
}

/** One attention badge: a white-outlined shape with a glyph; its outline differs per reason. */
export function PlantBadge({ code, x, y, radius }: BadgeProps) {
  const style = BADGE_STYLES[code];
  return (
    <g
      data-plan-badge-reason={code}
      data-plan-badge-shape={style.shape}
      transform={`translate(${num(x)} ${num(y)}) scale(${num(radius)})`}
      aria-hidden="true"
    >
      <path d={style.outline} fill={style.fill} stroke={BADGE_OUTLINE} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
      <path
        d={style.glyph}
        fill="none"
        stroke={BADGE_OUTLINE}
        strokeWidth={1.4}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </g>
  );
}

interface PlantMarkerBodyProps {
  entry: MarkerEntry;
  state: PlantMarkerState;
  /** Marker radius in model units (metres). */
  radius: number;
  pxPerM: number;
  /** Phase colour (or the default plant colour) of the disc. */
  fill: string;
  /** Colour of the ring and the cross (the text colour of the theme). */
  ringColor: string;
  /** Colour of the species initial on the disc. */
  initialColor: string;
  selectedColor: string;
  selected: boolean;
  /** The zoom is far enough in for the phase progress arc (R-014). */
  detail: boolean;
}

/** Disc, ring, seeds, cross, progress arc, initial and badge of one plant, centred on the marker. */
export function PlantMarkerBody({
  entry,
  state,
  radius,
  pxPerM,
  fill,
  ringColor,
  initialColor,
  selectedColor,
  selected,
  detail,
}: PlantMarkerBodyProps) {
  const ring = RING_STYLES[state.lifecycle];
  const cx = entry.x;
  const cy = -entry.y;
  const stroke = selected ? selectedColor : ringColor;
  const px = 1 / pxPerM;
  const seeds: [number, number][] = [
    [-0.35, 0.25],
    [0.3, 0.3],
    [0, -0.35],
  ];
  return (
    <>
      <circle
        className="gp-shape"
        cx={num(cx)}
        cy={num(cy)}
        r={num(radius)}
        fill={ring.discOpacity === 0 ? 'none' : fill}
        fillOpacity={ring.discOpacity === 0 ? undefined : ring.discOpacity}
        stroke={stroke}
        strokeOpacity={ring.ringOpacity}
        strokeWidth={selected ? 3 : 1.5}
        strokeDasharray={ring.dash ?? undefined}
        vectorEffect="non-scaling-stroke"
        data-plan-lifecycle={state.lifecycle}
        aria-hidden="true"
      />
      {ring.double ? (
        <circle
          cx={num(cx)}
          cy={num(cy)}
          r={num(radius + 2.5 * px)}
          fill="none"
          stroke={stroke}
          strokeWidth={1.5}
          vectorEffect="non-scaling-stroke"
          aria-hidden="true"
        />
      ) : null}
      {ring.seeds
        ? seeds.map(([dx, dy]) => (
            <circle
              key={`${dx}:${dy}`}
              cx={num(cx + dx * radius)}
              cy={num(cy + dy * radius)}
              r={num(radius * 0.12)}
              fill={ringColor}
              aria-hidden="true"
            />
          ))
        : null}
      {ring.cross ? (
        <path
          d={`M${num(cx - radius * 0.6)} ${num(cy - radius * 0.6)}L${num(cx + radius * 0.6)} ${num(cy + radius * 0.6)}M${num(cx + radius * 0.6)} ${num(cy - radius * 0.6)}L${num(cx - radius * 0.6)} ${num(cy + radius * 0.6)}`}
          stroke={ringColor}
          strokeWidth={2}
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          aria-hidden="true"
        />
      ) : null}
      {detail && state.progress !== null && !ring.cross && state.progress > 0 ? (
        <path
          d={progressArc(cx, cy, radius + 5 * px, state.progress)}
          fill="none"
          stroke={fill}
          strokeWidth={3}
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          data-plan-progress={state.progress.toFixed(2)}
          aria-hidden="true"
        />
      ) : null}
      {!ring.cross && state.initial ? (
        <text
          x={num(cx)}
          y={num(cy + (radius * 0.38))}
          fontSize={num(radius * 1.15)}
          textAnchor="middle"
          fontWeight={700}
          fill={initialColor}
          aria-hidden="true"
          pointerEvents="none"
        >
          {state.initial}
        </text>
      ) : null}
      {state.badge ? (
        <PlantBadge
          code={state.badge}
          x={cx + radius * BADGE_OFFSET_SHARE}
          y={cy - radius * BADGE_OFFSET_SHARE}
          radius={radius * BADGE_RADIUS_SHARE}
        />
      ) : null}
    </>
  );
}
