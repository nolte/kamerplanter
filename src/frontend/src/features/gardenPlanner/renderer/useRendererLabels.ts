import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { Geometry } from '../model/types';
import type { RendererLabels } from './types';

/** Renderer texts from `pages.gardenPlan.renderer.*` (DE/EN); stable until the language changes. */
export function useRendererLabels(): RendererLabels {
  const { t, i18n } = useTranslation();
  return useMemo(() => {
    const prefix = 'pages.gardenPlan.renderer';
    const number = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
    const size = (geometry: Geometry, areaM2: number): string => {
      if (geometry.kind === 'rect') {
        return t(`${prefix}.sizeRect`, {
          width: number.format(geometry.width_m),
          length: number.format(geometry.length_m),
        });
      }
      if (geometry.kind === 'circle') {
        return t(`${prefix}.sizeCircle`, { diameter: number.format(geometry.radius_m * 2) });
      }
      return t(`${prefix}.sizeArea`, { area: number.format(areaM2) });
    };
    return {
      canvas: t(`${prefix}.canvas`),
      canvasRole: t(`${prefix}.canvasRole`),
      boundary: t(`${prefix}.boundary`),
      bed: ({ name, size: dimension, plants, openTasks }) =>
        [
          name,
          t(`${prefix}.bedType`),
          dimension,
          plants > 0 ? t(`${prefix}.plantCount`, { count: plants }) : null,
          openTasks > 0 ? t(`${prefix}.openTaskCount`, { count: openTasks }) : null,
        ]
          .filter(Boolean)
          .join(', '),
      object: ({ label, typeLabel, size: dimension }) =>
        [label, typeLabel, dimension].filter(Boolean).join(', '),
      plant: ({ id }) => t(`${prefix}.plant`, { id }),
      slot: ({ id }) => t(`${prefix}.slot`, { id }),
      cluster: ({ count }) => t(`${prefix}.plantCount`, { count }),
      clusterSummary: ({ count, attention }) => t(`${prefix}.clusterSummary`, { count, attention }),
      objectType: (type) => t(`${prefix}.objectType.${type}`),
      size,
    };
  }, [t, i18n.language]);
}
