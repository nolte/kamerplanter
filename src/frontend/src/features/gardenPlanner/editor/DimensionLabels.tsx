/**
 * Dimension text on the canvas (REQ-053 GP-FR-014): width, length (radius) and area next to the
 * selected object and next to every outline a gesture is drawing or scaling. SVG in canvas pixels,
 * part of the editor overlay (decorative; the plan's own accessible names carry the sizes). The text
 * stands outside, above the edge, and moves past any handle in its way (GP-UX-047).
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import type { Shape } from '../model/geometry';
import type { Point } from '../model/types';
import { formatArea, formatLength, type LengthUnit } from '../model/units';
import { dimensionsOfShape, labelAnchor, labelAnchorBelow, placeDimensionLabel, type Dimensions } from './dimensions';
import { HANDLE_VISIBLE_PX } from './tools/handles';

export interface DimensionItem {
  key: string;
  shape: Shape;
}

interface DimensionLabelsProps {
  items: readonly DimensionItem[];
  toScreen: (pointM: Point) => Point;
  unit: LengthUnit;
  /** Screen centres of the handles drawn on the selection: the text keeps clear of them. */
  handlesPx?: readonly Point[];
  /** Canvas height in pixels: a text without room above the shape goes below it. */
  heightPx: number;
}

const MAX_LABELS = 5;
const FONT_PX = 12;
const NO_HANDLES: readonly Point[] = [];

export function dimensionText(
  dimensions: Dimensions,
  unit: LengthUnit,
  locale: string,
  t: (key: string, options: Record<string, string>) => string,
): string {
  const length = (value: number) => formatLength(value, unit, locale);
  const area = (value: number) => formatArea(value, locale);
  const prefix = 'pages.gardenPlan.editor.dimensions';
  switch (dimensions.kind) {
    case 'circle':
      return t(`${prefix}.circle`, {
        diameter: length(dimensions.diameterM),
        area: area(dimensions.areaM2),
      });
    case 'line':
      return t(`${prefix}.line`, { length: length(dimensions.lengthM) });
    default:
      return t(`${prefix}.${dimensions.kind}`, {
        width: length(dimensions.widthM),
        length: length(dimensions.lengthM),
        area: area(dimensions.areaM2),
      });
  }
}

export function DimensionLabels({ items, toScreen, unit, handlesPx = NO_HANDLES, heightPx }: DimensionLabelsProps) {
  const { t, i18n } = useTranslation();
  const { palette } = useTheme();
  const labels = useMemo(
    () =>
      items.slice(0, MAX_LABELS).flatMap((item) => {
        const dimensions = dimensionsOfShape(item.shape);
        if (dimensions === null) return [];
        const text = dimensionText(dimensions, unit, i18n.language, t);
        const [x, y] = placeDimensionLabel({
          topPx: toScreen(labelAnchor(item.shape)),
          bottomPx: toScreen(labelAnchorBelow(item.shape)),
          text,
          fontPx: FONT_PX,
          handlesPx,
          handleSizePx: HANDLE_VISIBLE_PX,
          heightPx,
        });
        return [{ key: item.key, x, y, text }];
      }),
    [items, toScreen, unit, i18n.language, t, handlesPx, heightPx],
  );
  return (
    <>
      {labels.map((label) => (
        <text
          key={label.key}
          data-testid="garden-plan-dimension"
          x={label.x}
          y={label.y}
          textAnchor="middle"
          fontSize={FONT_PX}
          fontWeight={600}
          fill={palette.text.primary}
          stroke={palette.background.paper}
          strokeWidth={3}
          paintOrder="stroke"
        >
          {label.text}
        </text>
      ))}
    </>
  );
}
