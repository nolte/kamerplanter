/**
 * The ghost of a bed template under the pointer (REQ-053 GP-FR-044): the outline of the shape where the click
 * would put it, turned by the chosen angle. Pure drawing; the server places the bed.
 */
import { useTheme } from '@mui/material/styles';
import { toShape } from '../model/geometry';
import type { BedTemplate, Point } from '../model/types';
import { placeGeometry } from './placeGeometry';

interface TemplateGhostProps {
  template: BedTemplate;
  originM: Point;
  rotationDeg: number;
  toScreen: (pointM: Point) => Point;
  pxPerM: number;
}

export function TemplateGhost({ template, originM, rotationDeg, toScreen, pxPerM }: TemplateGhostProps) {
  const { palette } = useTheme();
  const placed = placeGeometry(template.default_geometry, originM, rotationDeg);
  if (!placed) return null;
  const shape = toShape(placed);
  const common = {
    fill: palette.primary.main,
    fillOpacity: 0.18,
    stroke: palette.primary.main,
    strokeWidth: 2,
    strokeDasharray: '6 4',
  };
  return (
    <g data-testid="garden-plan-template-ghost" pointerEvents="none">
      {shape.kind === 'circle' ? (
        <circle
          cx={toScreen(shape.center)[0]}
          cy={toScreen(shape.center)[1]}
          r={shape.radiusM * pxPerM}
          {...common}
        />
      ) : (
        <polygon
          points={shape.vertices.map((vertex) => toScreen(vertex).join(',')).join(' ')}
          {...common}
        />
      )}
    </g>
  );
}
