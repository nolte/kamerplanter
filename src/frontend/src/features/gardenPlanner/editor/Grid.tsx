/**
 * The grid of the plan (REQ-053 GP-FR-011): lines at the chosen step, drawn only while they are at
 * least 8 px apart (else the next coarser step), with a stronger line at every whole metre. A
 * decorative layer under the pointer: the snap raster does not depend on it.
 */
import { useId } from 'react';
import { useTheme } from '@mui/material/styles';
import type { Viewport } from '../renderer';
import { MIN_GRID_LINE_PX, displayGridStep } from '../model/units';

interface GridProps {
  viewport: Viewport;
  /** The step the user chose, in metres. */
  stepM: number;
}

/** Offset of the first line: the model origin lies at `-origin * pxPerM` from the left edge. */
function phase(originCoordinateM: number, stepPx: number, pxPerM: number, flip: boolean): number {
  const offsetPx = (flip ? -originCoordinateM : originCoordinateM) * pxPerM;
  return ((-offsetPx % stepPx) + stepPx) % stepPx;
}

export function Grid({ viewport, stepM }: GridProps) {
  const id = useId();
  const { palette } = useTheme();
  const { pxPerM, originM, widthPx, heightPx } = viewport;
  const shown = displayGridStep(stepM, pxPerM);
  const stepPx = shown * pxPerM;
  const majorPx = pxPerM; // every whole metre
  const showMajor = shown < 1 && majorPx >= MIN_GRID_LINE_PX * 2;
  const line = palette.mode === 'dark' ? palette.grey[600] : palette.grey[400];
  const x0 = phase(originM[0], stepPx, pxPerM, false);
  // Screen y points down while model y points up.
  const y0 = phase(originM[1], stepPx, pxPerM, true);
  const mx0 = phase(originM[0], majorPx, pxPerM, false);
  const my0 = phase(originM[1], majorPx, pxPerM, true);
  return (
    <svg
      width={widthPx}
      height={heightPx}
      aria-hidden="true"
      focusable="false"
      data-testid="garden-plan-grid"
      data-step-m={shown}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
    >
      <defs>
        <pattern
          id={`${id}-minor`}
          width={stepPx}
          height={stepPx}
          x={x0}
          y={y0}
          patternUnits="userSpaceOnUse"
        >
          <path d={`M${stepPx} 0V${stepPx}M0 ${stepPx}H${stepPx}`} fill="none" stroke={line} strokeWidth={1} opacity={0.35} />
        </pattern>
        {showMajor && (
          <pattern
            id={`${id}-major`}
            width={majorPx}
            height={majorPx}
            x={mx0}
            y={my0}
            patternUnits="userSpaceOnUse"
          >
            <path d={`M${majorPx} 0V${majorPx}M0 ${majorPx}H${majorPx}`} fill="none" stroke={line} strokeWidth={1} opacity={0.7} />
          </pattern>
        )}
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id}-minor)`} />
      {showMajor && <rect width="100%" height="100%" fill={`url(#${id}-major)`} />}
    </svg>
  );
}
