/**
 * What the touch layer draws on the canvas (REQ-053 GP-UX-036/040): the long-press progress ring
 * under the finger and the crosshair in the middle of the plan that "set point" aims at while a
 * draw tool is active. Decoration only - hidden from assistive technology, no pointer events.
 */
import Box from '@mui/material/Box';
import { keyframes, useTheme } from '@mui/material/styles';
import type { Point } from '../model/types';
import type { PressRing } from './tools/useTouchInput';
import { LONG_PRESS_MS } from './tools/touchGestures';

const RADIUS = 26;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const fill = keyframes`from { stroke-dashoffset: ${CIRCUMFERENCE}; } to { stroke-dashoffset: 0; }`;

interface TouchOverlayProps {
  ring: PressRing | null;
  /** The centre of the plan in canvas pixels, or `null` when no crosshair is wanted. */
  crosshair: Point | null;
  widthPx: number;
  heightPx: number;
}

export function TouchOverlay({ ring, crosshair, widthPx, heightPx }: TouchOverlayProps) {
  const { palette } = useTheme();
  if (!ring && !crosshair) return null;
  return (
    <Box
      component="svg"
      width={widthPx}
      height={heightPx}
      aria-hidden="true"
      focusable="false"
      data-testid="garden-plan-touch-overlay"
      sx={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
    >
      {crosshair && (
        <g stroke={palette.primary.main} strokeWidth={2} data-testid="garden-plan-crosshair">
          <line x1={crosshair[0] - 16} y1={crosshair[1]} x2={crosshair[0] + 16} y2={crosshair[1]} />
          <line x1={crosshair[0]} y1={crosshair[1] - 16} x2={crosshair[0]} y2={crosshair[1] + 16} />
          <circle cx={crosshair[0]} cy={crosshair[1]} r={5} fill="none" />
        </g>
      )}
      {ring && (
        <>
          <circle
            cx={ring.pointPx[0]}
            cy={ring.pointPx[1]}
            r={RADIUS}
            fill={ring.armed ? palette.primary.main : 'none'}
            fillOpacity={0.2}
            stroke={palette.divider}
            strokeWidth={4}
          />
          <Box
            component="circle"
            cx={ring.pointPx[0]}
            cy={ring.pointPx[1]}
            r={RADIUS}
            fill="none"
            stroke={palette.primary.main}
            strokeWidth={4}
            strokeDasharray={CIRCUMFERENCE}
            data-testid="garden-plan-press-ring"
            data-armed={ring.armed ? 'true' : 'false'}
            sx={{
              transformOrigin: `${ring.pointPx[0]}px ${ring.pointPx[1]}px`,
              transform: 'rotate(-90deg)',
              strokeDashoffset: ring.armed ? 0 : CIRCUMFERENCE,
              animation: ring.armed ? 'none' : `${fill} ${LONG_PRESS_MS}ms linear forwards`,
              '@media (prefers-reduced-motion: reduce)': { animation: 'none', strokeDashoffset: 0 },
            }}
          />
        </>
      )}
    </Box>
  );
}
