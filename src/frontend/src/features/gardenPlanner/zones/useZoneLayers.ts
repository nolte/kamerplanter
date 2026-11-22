import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { RenderOptions, ZoneLayerEntry } from '../renderer/types';
import { wateredByBed } from './lastWatered';
import type { PlanZone } from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';

interface Input {
  zones: readonly PlanZone[];
  showZones: boolean;
  showLastWatered: boolean;
  lastWateredAt: Readonly<Record<string, string | null | undefined>>;
  /** The instant "days since" counts from; the editor ticks it by the day. */
  nowMs: number;
}

/** What the renderer draws for the two layers, from the data and the layer switches. */
export function useZoneLayers({
  zones,
  showZones,
  showLastWatered,
  lastWateredAt,
  nowMs,
}: Input): Pick<RenderOptions, 'zoneLayer' | 'wateredLayer'> {
  const { t } = useTranslation();
  const zoneLayer = useMemo<readonly ZoneLayerEntry[] | undefined>(
    () =>
      showZones
        ? zones.map((zone, index) => ({
            key: zone.key,
            color: zone.color,
            variant: index,
            locationKeys: zone.location_keys,
          }))
        : undefined,
    [showZones, zones],
  );
  const byBed = useMemo(
    () => (showLastWatered ? wateredByBed(lastWateredAt, nowMs) : null),
    [showLastWatered, lastWateredAt, nowMs],
  );
  const wateredLayer = useMemo<RenderOptions['wateredLayer']>(
    () => (byBed ? { byBed, label: (days) => t(`${PREFIX}.wateredDays`, { count: days }) } : undefined),
    [byBed, t],
  );
  return useMemo(() => ({ zoneLayer, wateredLayer }), [zoneLayer, wateredLayer]);
}
