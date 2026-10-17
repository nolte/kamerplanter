/**
 * Dimension text on the canvas (REQ-053 GP-FR-014): width, length (radius) and area next to the
 * selected object and next to every outline a gesture is drawing or scaling. SVG in canvas pixels,
 * part of the editor overlay (decorative; the plan's own accessible names carry the sizes).
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import type { Shape } from '../model/geometry';
import type { Point } from '../model/types';
import { formatArea, formatLength, type LengthUnit } from '../model/units';
import { dimensionsOfShape, labelAnchor, type Dimensions } from './dimensions';

export interface DimensionItem {
  key: string;
  shape: Shape;
}

interface DimensionLabelsProps {
  items: readonly DimensionItem[];
  toScreen: (pointM: Point) => Point;
  unit: LengthUnit;
}

const MAX_LABELS = 5;

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

export function DimensionLabels({ items, toScreen, unit }: DimensionLabelsProps) {
  const { t, i18n } = useTranslation();
  const { palette } = useTheme();
  const labels = useMemo(
    () =>
      items.slice(0, MAX_LABELS).flatMap((item) => {
        const dimensions = dimensionsOfShape(item.shape);
        if (dimensions === null) return [];
        const [x, y] = toScreen(labelAnchor(item.shape));
        return [{ key: item.key, x, y, text: dimensionText(dimensions, unit, i18n.language, t) }];
      }),
    [items, toScreen, unit, i18n.language, t],
  );
  return (
    <>
      {labels.map((label) => (
        <text
          key={label.key}
          data-testid="garden-plan-dimension"
          x={label.x}
          y={Math.max(14, label.y - 6)}
          textAnchor="middle"
          fontSize={12}
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
