/**
 * Marker and guide lines of the snap (REQ-053 GP-FR-154): a ring where the point will land, with
 * thin guide lines through it - green for an object corner or edge, grey for the grid. On an object edge
 * the edge itself is drawn as a solid guide.
 */
import { useTheme } from '@mui/material/styles';
import type { Point } from '../model/types';
import type { SnapMark } from './tools/snap';

export type { SnapMark };

interface SnapMarkerProps {
  mark: SnapMark;
  toScreen: (pointM: Point) => Point;
  widthPx: number;
  heightPx: number;
}

export function SnapMarker({ mark, toScreen, widthPx, heightPx }: SnapMarkerProps) {
  const { palette } = useTheme();
  const [x, y] = toScreen(mark.point);
  const color = mark.kind === 'grid' ? palette.text.secondary : palette.success.main;
  const guide = mark.guide ? [toScreen(mark.guide[0]), toScreen(mark.guide[1])] : null;
  return (
    <g data-testid="garden-plan-snap-marker" data-kind={mark.kind} pointerEvents="none">
      {guide && (
        <line
          data-testid="garden-plan-snap-guide"
          x1={guide[0][0]}
          y1={guide[0][1]}
          x2={guide[1][0]}
          y2={guide[1][1]}
          stroke={color}
          strokeWidth={3}
          opacity={0.7}
        />
      )}
      <line x1={x} x2={x} y1={0} y2={heightPx} stroke={color} strokeWidth={1} strokeDasharray="2 4" opacity={0.6} />
      <line x1={0} x2={widthPx} y1={y} y2={y} stroke={color} strokeWidth={1} strokeDasharray="2 4" opacity={0.6} />
      <circle cx={x} cy={y} r={mark.kind === 'grid' ? 4 : 6} fill="none" stroke={color} strokeWidth={2} />
    </g>
  );
}
