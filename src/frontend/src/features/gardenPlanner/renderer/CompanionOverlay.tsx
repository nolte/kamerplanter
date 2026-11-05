import { memo, useMemo } from 'react';
import { useTheme } from '@mui/material/styles';
import {
  COMPANION_HIT_WIDTH_PX,
  COMPANION_LINE_STYLES,
  companionInk,
  cullCompanionLines,
  type CompanionLine,
} from './companionLines';
import type { Viewport } from './types';

/**
 * The companion-planting layer of the plan (REQ-053 GP-FR-134): a line between two neighbouring occupied slots,
 * solid green = compatible, dashed red = incompatible, dotted grey = unknown. Culled to the viewport and capped at
 * 500 lines before anything is drawn. Its own chunk (UI-NFR-003): the plan route carries none of it until the layer
 * is switched on.
 *
 * The drawing is decorative for assistive technology (`aria-hidden`): what a line says is shown in the info card
 * the editor opens on hover or tap, which names the status in words. Each line carries an invisible 24 px stroke
 * (`data-companion-edge`) that takes the pointer, so a finger can hit a 2 px line.
 */
interface Props {
  lines: readonly CompanionLine[];
  viewport: Viewport;
}

function num(value: number): string {
  return String(Number(value.toFixed(3)));
}

function CompanionLayer({ lines, viewport }: Props) {
  const theme = useTheme();
  // Culling depends on the viewport and the lines only; a pointer move redraws nothing.
  const culled = useMemo(() => cullCompanionLines(lines, viewport), [lines, viewport]);
  const inks = useMemo(
    () => ({
      compatible: companionInk(theme, 'compatible'),
      incompatible: companionInk(theme, 'incompatible'),
      unknown: companionInk(theme, 'unknown'),
    }),
    [theme],
  );
  return (
    <g
      data-testid="garden-plan-companion-layer"
      data-companion-candidates={culled.candidates}
      data-companion-drawn={culled.lines.length}
      aria-hidden="true"
    >
      {culled.lines.map((line) => {
        const style = COMPANION_LINE_STYLES[line.status];
        const x1 = num(line.a[0]);
        const y1 = num(-line.a[1]);
        const x2 = num(line.b[0]);
        const y2 = num(-line.b[1]);
        return (
          <g key={line.id} data-companion-edge={line.id} data-companion-status={line.status} style={{ cursor: 'pointer' }}>
            <line
              className="gp-companion-line"
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={inks[line.status]}
              strokeWidth={style.widthPx}
              strokeDasharray={style.dash}
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
              pointerEvents="none"
            />
            <line
              className="gp-companion-hit"
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="transparent"
              strokeWidth={COMPANION_HIT_WIDTH_PX}
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
              pointerEvents="stroke"
            />
          </g>
        );
      })}
    </g>
  );
}

export default memo(CompanionLayer);
