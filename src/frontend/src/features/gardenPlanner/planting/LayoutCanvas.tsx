/**
 * The bed at scale with the positions of a planting (REQ-053 GP-FR-063/067/072/068): the preview of the
 * dialog, the freely placed points with their yellow ring below the spacing, and the single plant that
 * "Correct position" moves. It draws in the bed frame (anchor at (0, 0), y up), so it needs no plan
 * viewport. Colour never carries the entry alone: each layer has its own marker shape.
 */
import { memo, useCallback, useEffect, useMemo, useRef, type PointerEvent as ReactPointerEvent } from 'react';
import { useTheme } from '@mui/material/styles';
import { toLocalShape, type Shape } from '../model/geometry';
import type { Geometry, Point } from '../model/types';

/** Marker shapes by layer index: circle, square, diamond, triangle. */
export const MARKER_SHAPES = ['circle', 'square', 'diamond', 'triangle'] as const;
export type MarkerShape = (typeof MARKER_SHAPES)[number];

export interface CanvasLayer {
  id: string;
  shape: MarkerShape;
  color: string;
  positions: readonly Point[];
  zones?: readonly (readonly Point[])[];
  /** Indices of positions closer than the spacing: they get the yellow ring (hint, not a blocker). */
  flagged?: readonly number[];
  label?: string;
}

interface LayoutCanvasProps {
  bed: Geometry;
  layers: readonly CanvasLayer[];
  /** Slots that stand in the bed already, drawn small and grey. */
  existing?: readonly Point[];
  /** Accessible name of the drawing. */
  label: string;
  /** The layer whose points can be added to, selected and dragged. */
  interactiveLayerId?: string;
  selected?: { layerId: string; index: number } | null;
  onAdd?: (point: Point) => void;
  onSelect?: (layerId: string, index: number) => void;
  onMove?: (layerId: string, index: number, point: Point) => void;
  /**
   * Hold a marker this long before it follows the pointer (field mode: 500 ms long press, GP-UX-023), so a
   * wet thumb resting on the bed does not move a plant. Without it a drag starts at once.
   */
  dragHoldMs?: number;
  testId?: string;
}

const PAD_SHARE = 0.06;
const MARKER_SHARE = 0.014;
const HIT_FACTOR = 2.6;
const CM = 100;

function boundsOf(shape: Shape): [number, number, number, number] {
  if (shape.kind === 'circle') {
    const [cx, cy] = shape.center;
    return [cx - shape.radiusM, cy - shape.radiusM, cx + shape.radiusM, cy + shape.radiusM];
  }
  const xs = shape.vertices.map((v) => v[0]);
  const ys = shape.vertices.map((v) => v[1]);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

function polygonPath(points: readonly Point[]): string {
  return `${points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x} ${-y}`).join('')}Z`;
}

function markerPath(shape: MarkerShape, x: number, y: number, r: number): string | null {
  const cy = -y;
  switch (shape) {
    case 'square':
      return `M${x - r} ${cy - r}h${2 * r}v${2 * r}h${-2 * r}Z`;
    case 'diamond':
      return `M${x} ${cy - 1.25 * r}L${x + 1.25 * r} ${cy}L${x} ${cy + 1.25 * r}L${x - 1.25 * r} ${cy}Z`;
    case 'triangle':
      return `M${x} ${cy - 1.2 * r}L${x + 1.15 * r} ${cy + r}L${x - 1.15 * r} ${cy + r}Z`;
    default:
      return null;
  }
}

interface MarkerProps {
  shape: MarkerShape;
  x: number;
  y: number;
  r: number;
  color: string;
  selected: boolean;
}

function Marker({ shape, x, y, r, color, selected }: MarkerProps) {
  const path = markerPath(shape, x, y, r);
  const common = {
    fill: color,
    fillOpacity: 0.85,
    stroke: selected ? '#000' : color,
    strokeWidth: selected ? 3 : 1,
    vectorEffect: 'non-scaling-stroke' as const,
  };
  return path ? <path d={path} {...common} /> : <circle cx={x} cy={-y} r={r} {...common} />;
}

const MemoMarker = memo(Marker);

function LayoutCanvas({
  bed,
  layers,
  existing,
  label,
  interactiveLayerId,
  selected = null,
  onAdd,
  onSelect,
  onMove,
  dragHoldMs,
  testId = 'layout-canvas',
}: LayoutCanvasProps) {
  const theme = useTheme();
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useRef<{ layerId: string; index: number; moved: boolean; armed: boolean } | null>(null);
  const holdTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearHold = () => {
    if (holdTimer.current !== null) clearTimeout(holdTimer.current);
    holdTimer.current = null;
  };
  useEffect(() => clearHold, []);
  const shape = useMemo(() => toLocalShape(bed), [bed]);
  const view = useMemo(() => {
    const [minX, minY, maxX, maxY] = boundsOf(shape);
    const width = Math.max(maxX - minX, 0.1);
    const height = Math.max(maxY - minY, 0.1);
    const pad = Math.max(width, height) * PAD_SHARE;
    return {
      x: minX - pad,
      y: -maxY - pad,
      width: width + 2 * pad,
      height: height + 2 * pad,
      marker: Math.max(width, height) * MARKER_SHARE,
    };
  }, [shape]);

  const toBedPoint = useCallback(
    (clientX: number, clientY: number): Point | null => {
      const svg = svgRef.current;
      if (!svg) return null;
      const rect = svg.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return null;
      const x = view.x + ((clientX - rect.left) / rect.width) * view.width;
      const y = -(view.y + ((clientY - rect.top) / rect.height) * view.height);
      return [Math.round(x * CM) / CM, Math.round(y * CM) / CM];
    },
    [view],
  );

  const onBackgroundClick = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (!onAdd || drag.current) return;
    const point = toBedPoint(event.clientX, event.clientY);
    if (point) onAdd(point);
  };

  const startDrag = (event: ReactPointerEvent<SVGElement>, layerId: string, index: number) => {
    event.stopPropagation();
    if (layerId !== interactiveLayerId) return;
    const hold = dragHoldMs ?? 0;
    drag.current = { layerId, index, moved: false, armed: hold <= 0 };
    clearHold();
    if (hold > 0) {
      holdTimer.current = setTimeout(() => {
        if (drag.current) drag.current.armed = true;
        holdTimer.current = null;
      }, hold);
    }
    event.currentTarget.setPointerCapture?.(event.pointerId);
    onSelect?.(layerId, index);
  };
  const moveDrag = (event: ReactPointerEvent<SVGElement>) => {
    const current = drag.current;
    if (!current || !onMove || !current.armed) return;
    const point = toBedPoint(event.clientX, event.clientY);
    if (!point) return;
    current.moved = true;
    onMove(current.layerId, current.index, point);
  };
  const endDrag = (event: ReactPointerEvent<SVGElement>) => {
    event.stopPropagation();
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    clearHold();
    // The click that ends a drag must not add a point; clear on the next tick.
    setTimeout(() => {
      drag.current = null;
    }, 0);
  };

  const outline =
    shape.kind === 'circle' ? (
      <circle
        cx={shape.center[0]}
        cy={-shape.center[1]}
        r={shape.radiusM}
        fill={theme.palette.action.hover}
        stroke={theme.palette.text.secondary}
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
      />
    ) : (
      <path
        d={polygonPath(shape.vertices)}
        fill={theme.palette.action.hover}
        stroke={theme.palette.text.secondary}
        strokeWidth={2}
        vectorEffect="non-scaling-stroke"
      />
    );
  const r = view.marker;

  return (
    <svg
      ref={svgRef}
      role="img"
      aria-label={label}
      viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`}
      width="100%"
      style={{
        display: 'block',
        maxHeight: '55vh',
        touchAction: interactiveLayerId && onMove ? 'none' : 'auto',
        cursor: onAdd ? 'crosshair' : 'default',
      }}
      onPointerUp={onAdd ? onBackgroundClick : undefined}
      data-testid={testId}
    >
      {outline}
      {existing?.map(([x, y], index) => (
        <circle
          key={`e${index}`}
          cx={x}
          cy={-y}
          r={r * 0.6}
          fill="none"
          stroke={theme.palette.text.secondary}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
          data-testid={`${testId}-existing`}
        />
      ))}
      {layers.map((layer) => (
        <g key={layer.id} data-layer={layer.id}>
          {layer.zones?.map((zone, index) => (
            <path
              key={`z${index}`}
              d={polygonPath(zone)}
              fill={layer.color}
              fillOpacity={0.25}
              stroke={layer.color}
              strokeDasharray="6 4"
              strokeWidth={2}
              vectorEffect="non-scaling-stroke"
            />
          ))}
          {layer.positions.map(([x, y], index) => {
            const isSelected = selected?.layerId === layer.id && selected.index === index;
            const interactive = layer.id === interactiveLayerId;
            return (
              <g key={`p${index}`}>
                {layer.flagged?.includes(index) ? (
                  <circle
                    cx={x}
                    cy={-y}
                    r={r * 1.9}
                    fill="none"
                    stroke={theme.palette.warning.main}
                    strokeWidth={3}
                    vectorEffect="non-scaling-stroke"
                    data-testid={`${testId}-ring`}
                  />
                ) : null}
                <MemoMarker shape={layer.shape} x={x} y={y} r={r} color={layer.color} selected={isSelected} />
                {interactive ? (
                  <circle
                    cx={x}
                    cy={-y}
                    r={r * HIT_FACTOR}
                    fill="transparent"
                    style={{ touchAction: 'none', cursor: onMove ? 'grab' : 'pointer' }}
                    onPointerDown={(event) => startDrag(event, layer.id, index)}
                    onPointerMove={moveDrag}
                    onPointerUp={endDrag}
                    onPointerCancel={endDrag}
                    data-testid={`${testId}-point-${index}`}
                  />
                ) : null}
              </g>
            );
          })}
        </g>
      ))}
    </svg>
  );
}

export default memo(LayoutCanvas);
