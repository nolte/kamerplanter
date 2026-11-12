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
    // A reserved position's day, read as the UTC calendar day it names (GP-FR-074).
    const day = new Intl.DateTimeFormat(i18n.language, { day: 'numeric', month: 'short', timeZone: 'UTC' });
    const dayText = (isoDay: string): string => {
      const parsed = new Date(`${isoDay}T00:00:00Z`);
      return Number.isNaN(parsed.getTime()) ? isoDay : day.format(parsed);
    };
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
      slot: ({ id, plannedFrom }) =>
        plannedFrom
          ? t(`${prefix}.slotPlanned`, { id, date: dayText(plannedFrom) })
          : t(`${prefix}.slot`, { id }),
      plannedDate: (isoDay) => t(`${prefix}.plannedDate`, { date: dayText(isoDay) }),
      cluster: ({ count }) => t(`${prefix}.plantCount`, { count }),
      // Two plurals: the plant count and the attention count each pick their own form ("4 plants · 1 needs attention").
      clusterSummary: ({ count, attention }) =>
        t(`${prefix}.clusterSummary`, { count, attention: t(`${prefix}.clusterAttention`, { count: attention }) }),
      objectType: (type) => t(`${prefix}.objectType.${type}`),
      size,
    };
  }, [t, i18n.language]);
}
