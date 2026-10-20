import { useTranslation } from 'react-i18next';
import Typography from '@mui/material/Typography';
import WaterDropOutlinedIcon from '@mui/icons-material/WaterDropOutlined';
import { daysSince } from './lastWatered';
import type { PlanZone } from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';

interface Props {
  bedKey: string;
  zones: readonly PlanZone[];
  lastWateredAt: string | null | undefined;
  nowMs: number;
}

/**
 * What the info of a bed says about water (GP-UX-006): its irrigation zone and the days since the last watering.
 * Worded as a fact ("3 days since"), never as a need - the plan does not know whether a bed needs water.
 */
export function BedZoneInfo({ bedKey, zones, lastWateredAt, nowMs }: Props) {
  const { t } = useTranslation();
  const zone = zones.find((candidate) => candidate.location_keys.includes(bedKey));
  const days = lastWateredAt ? daysSince(lastWateredAt, nowMs) : null;
  return (
    <div data-testid="garden-plan-panel-water-info">
      {zone && (
        <Typography variant="body2" color="text.secondary" data-testid="garden-plan-panel-zone">
          {t(`${PREFIX}.bed.zone`, { name: zone.name })}
        </Typography>
      )}
      <Typography
        variant="body2"
        color="text.secondary"
        data-testid="garden-plan-panel-last-watered"
        sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
      >
        <WaterDropOutlinedIcon fontSize="inherit" aria-hidden="true" />
        {days === null
          ? t(`${PREFIX}.bed.wateredNone`)
          : t(`${PREFIX}.bed.watered`, { days: t(`${PREFIX}.wateredDays`, { count: days }) })}
      </Typography>
    </div>
  );
}
