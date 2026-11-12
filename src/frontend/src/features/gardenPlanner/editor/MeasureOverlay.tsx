/**
 * The measurement of the measure tool on the canvas (REQ-053 GP-UX-071, #2913): the measured line, its points, the
 * length of every segment and the total at its end, in the user's length unit. Drawn inside the editor overlay like
 * the dimension text (`DimensionLabels`), so it looks the same over every renderer; the overlay is hidden from
 * assistive technology - the editor's status text announces the same total.
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import type { Point } from '../model/types';
import { formatLength, type LengthUnit } from '../model/units';
import { DIMENSION_FONT_PX, dimensionTextProps } from './DimensionLabels';
import type { MeasureView } from './tools/measureMachine';

interface MeasureOverlayProps {
  measure: MeasureView;
  toScreen: (pointM: Point) => Point;
  unit: LengthUnit;
  widthPx: number;
}

/** Room between the line's end and the total, in screen pixels. */
const OFFSET_PX = 10;
/** Average glyph width of the dimension text as a share of its size (as `placeDimensionLabel` estimates it). */
const GLYPH_EM = 0.62;

export function MeasureOverlay({ measure, toScreen, unit, widthPx }: MeasureOverlayProps) {
  const { t, i18n } = useTranslation();
  const { palette } = useTheme();
  const textProps = dimensionTextProps(palette);
  const drawn = useMemo(() => {
    const length = (valueM: number) => formatLength(valueM, unit, i18n.language);
    const pathPx = measure.pathM.map(toScreen);
    const several = measure.segmentsM.length >= 2;
    // The segments carry their own length once there are two or more; a single segment is the total.
    const segments = several
      ? measure.segmentsM.map((lengthM, index) => {
          const [ax, ay] = pathPx[index];
          const [bx, by] = pathPx[index + 1];
          return { x: (ax + bx) / 2, y: (ay + by) / 2 - OFFSET_PX / 2, text: length(lengthM) };
        })
      : [];
    const totalText = several
      ? t('pages.gardenPlan.editor.measure.total', { length: length(measure.totalM) })
      : length(measure.totalM);
    const [endX, endY] = pathPx[pathPx.length - 1];
    const textWidth = totalText.length * DIMENSION_FONT_PX * GLYPH_EM;
    // Right of and above the end; to the left near the right edge, below near the top edge.
    const towardsLeft = endX + OFFSET_PX + textWidth > widthPx;
    const total = {
      x: towardsLeft ? endX - OFFSET_PX : endX + OFFSET_PX,
      y: endY - OFFSET_PX < DIMENSION_FONT_PX ? endY + OFFSET_PX + DIMENSION_FONT_PX : endY - OFFSET_PX,
      anchor: towardsLeft ? 'end' : 'start',
      text: totalText,
    } as const;
    const fixed = pathPx.slice(0, measure.fixedPoints);
    const d = `M${pathPx.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join('L')}`;
    return { d, fixed, segments, total };
  }, [i18n.language, measure, t, toScreen, unit, widthPx]);

  const color = palette.secondary.main;
  return (
    <g data-testid="garden-plan-measure" data-done={measure.done ? 'true' : 'false'}>
      <path
        d={drawn.d}
        fill="none"
        stroke={color}
        strokeWidth={2}
        // Dashed while it still follows the pointer, solid once it is finished.
        strokeDasharray={measure.done ? undefined : '6 4'}
        data-testid="garden-plan-measure-line"
      />
      {drawn.fixed.map(([x, y], index) => (
        <circle key={index} cx={x} cy={y} r={4} fill={palette.background.paper} stroke={color} strokeWidth={2} />
      ))}
      {drawn.segments.map((segment, index) => (
        <text
          key={index}
          data-testid="garden-plan-measure-segment"
          x={segment.x}
          y={segment.y}
          textAnchor="middle"
          {...textProps}
        >
          {segment.text}
        </text>
      ))}
      {/* A lone start point has no length yet. */}
      {measure.pathM.length >= 2 && (
        <text
          data-testid="garden-plan-measure-total"
          x={drawn.total.x}
          y={drawn.total.y}
          textAnchor={drawn.total.anchor}
          {...textProps}
        >
          {drawn.total.text}
        </text>
      )}
    </g>
  );
}
