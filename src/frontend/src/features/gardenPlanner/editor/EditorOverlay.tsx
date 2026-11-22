/**
 * Everything the editor draws on top of the plan while the user works (REQ-053 GP-NFR-009): the
 * ghost outline of a shape being moved, resized or drawn (red when the live validation refuses it,
 * GP-UX-053), the marquee, and the handles. Plain SVG in canvas pixels, no pointer events, hidden
 * from assistive technology - the plan itself carries the accessible names; this layer only
 * shows what a gesture is about to do.
 */
import type { ReactNode } from 'react';
import { useTheme } from '@mui/material/styles';
import type { Shape } from '../model/geometry';
import type { Point } from '../model/types';
import { Handles } from './Handles';
import type { HandleSet } from './tools/handles';
import type { Overlay } from './tools/machineTypes';
import type { VertexSelection } from './tools/selectMachine';

interface EditorOverlayProps {
  overlay: Overlay;
  handles: HandleSet | null;
  vertex: VertexSelection | null;
  toScreen: (pointM: Point) => Point;
  pxPerM: number;
  widthPx: number;
  heightPx: number;
  /** Extra layers drawn last: dimension text, snap marker (WP 2.5). */
  children?: ReactNode;
}

function pathOf(shape: Shape, toScreen: (pointM: Point) => Point): string {
  if (shape.kind === 'circle') return '';
  const points = shape.vertices.map(toScreen);
  return `M${points.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join('L')}${shape.closed ? 'Z' : ''}`;
}

export function EditorOverlay({
  overlay,
  handles,
  vertex,
  toScreen,
  pxPerM,
  widthPx,
  heightPx,
  children,
}: EditorOverlayProps) {
  const theme = useTheme();
  const { palette } = theme;
  return (
    <svg
      width={widthPx}
      height={heightPx}
      aria-hidden="true"
      focusable="false"
      data-testid="garden-plan-overlay"
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
    >
      {overlay.shapes.map((item) => {
        const color = item.invalid ? palette.error.main : palette.primary.main;
        const common = {
          fill: item.draft ? 'none' : color,
          fillOpacity: 0.15,
          stroke: color,
          strokeWidth: 2,
          strokeDasharray: item.invalid ? undefined : '6 4',
          'data-testid': 'garden-plan-ghost',
          'data-invalid': item.invalid ? 'true' : 'false',
        };
        if (item.shape.kind === 'circle') {
          const [cx, cy] = toScreen(item.shape.center);
          return (
            <circle key={item.key} cx={cx} cy={cy} r={item.shape.radiusM * pxPerM} {...common} />
          );
        }
        return <path key={item.key} d={pathOf(item.shape, toScreen)} {...common} />;
      })}
      {overlay.marquee && (
        <rect
          data-testid="garden-plan-marquee"
          x={overlay.marquee.x}
          y={overlay.marquee.y}
          width={overlay.marquee.width}
          height={overlay.marquee.height}
          fill={palette.primary.main}
          fillOpacity={0.1}
          stroke={palette.primary.main}
          strokeDasharray="4 3"
        />
      )}
      {handles && <Handles set={handles} toScreen={toScreen} vertex={vertex} />}
      {children}
    </svg>
  );
}
