/**
 * The handles of the selected object (REQ-053 GP-FR-022/023, GP-UX-048): drawn on the overlay in
 * screen pixels. Visible size is 14 px; the 48 px hit area is computed by the select machine
 * (`handleAt`), not by these nodes - the overlay takes no pointer events, so a single sink on the
 * canvas sees every gesture. Handles are pointer affordances; the keyboard reaches the same edits
 * through the panel and the list view (WP 2.6/2.7).
 */
import { useTheme } from '@mui/material/styles';
import type { Point } from '../model/types';
import { HANDLE_VISIBLE_PX, type Handle, type HandleSet } from './tools/handles';
import type { VertexSelection } from './tools/selectMachine';

interface HandlesProps {
  set: HandleSet;
  toScreen: (pointM: Point) => Point;
  vertex: VertexSelection | null;
}

const HALF = HANDLE_VISIBLE_PX / 2;

export function Handles({ set, toScreen, vertex }: HandlesProps) {
  const theme = useTheme();
  const stroke = theme.palette.primary.main;
  const fill = theme.palette.background.paper;
  return (
    <g data-testid="garden-plan-handles" data-density={set.density}>
      {set.handles.map((handle) => (
        <HandleMark
          key={handle.id}
          handle={handle}
          at={toScreen(handle.pointM)}
          picked={vertex !== null && handle.kind === 'vertex' && handle.index === vertex.index}
          stroke={stroke}
          fill={fill}
        />
      ))}
    </g>
  );
}

interface HandleMarkProps {
  handle: Handle;
  at: Point;
  picked: boolean;
  stroke: string;
  fill: string;
}

function HandleMark({ handle, at, picked, stroke, fill }: HandleMarkProps) {
  const [x, y] = at;
  const common = {
    stroke,
    strokeWidth: 2,
    fill: picked ? stroke : fill,
    'data-testid': `garden-plan-handle-${handle.id}`,
    'data-handle-kind': handle.kind,
  };
  if (handle.kind === 'rotate' || handle.kind === 'radius') {
    return <circle cx={x} cy={y} r={HALF} {...common} />;
  }
  if (handle.kind === 'midpoint') {
    // A "+" on the edge: insert a point here (GP-FR-023).
    return (
      <g data-testid={common['data-testid']} data-handle-kind="midpoint">
        <circle cx={x} cy={y} r={HALF - 2} stroke={stroke} strokeWidth={1.5} fill={fill} />
        <path
          d={`M${x - 3} ${y}H${x + 3}M${x} ${y - 3}V${y + 3}`}
          stroke={stroke}
          strokeWidth={1.5}
        />
      </g>
    );
  }
  return (
    <rect
      x={x - HALF}
      y={y - HALF}
      width={HANDLE_VISIBLE_PX}
      height={HANDLE_VISIBLE_PX}
      rx={2}
      {...common}
    />
  );
}
