/**
 * The ring and badge entries of the plant-marker legend (REQ-053 GP-UX-005, GP-UX-061), drawn with the same parts as
 * the markers so a legend can never drift from the plan. Shared by the bed view's legend and the plan's layer legend.
 */
import { useTheme } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { AttentionCode, Lifecycle } from '../model/plantState';
import { PlantBadge, PlantMarkerBody } from '../renderer/PlantMarker';
import type { MarkerEntry } from '../renderer/planIndex';

const LEGEND_RINGS: readonly { lifecycle: Lifecycle; key: string }[] = [
  { lifecycle: 'planned', key: 'ringPlanned' },
  { lifecycle: 'sown', key: 'ringSown' },
  { lifecycle: 'active', key: 'ringActive' },
  { lifecycle: 'harvesting', key: 'ringHarvesting' },
  { lifecycle: 'failed', key: 'ringFailed' },
];
const LEGEND_BADGES: readonly { code: AttentionCode; key: string }[] = [
  { code: 'problem', key: 'badgeProblem' },
  { code: 'frost', key: 'badgeFrost' },
  { code: 'overdue', key: 'badgeOverdue' },
  { code: 'water', key: 'badgeWater' },
  { code: 'harvest', key: 'badgeHarvest' },
];
const SAMPLE: MarkerEntry = { key: 'legend', kind: 'plant', displayId: '', locationKey: '', x: 0, y: 0 };
const RADIUS = 9;

const LIST_SX = { listStyle: 'none', m: 0, p: 0, display: 'grid', gap: 0.75 } as const;
const ITEM_SX = { display: 'flex', alignItems: 'center', gap: 1.5 } as const;

export function PlantStateLegendItems() {
  const { t } = useTranslation();
  const theme = useTheme();
  const fill = theme.palette.success.main;
  return (
    <>
      <Typography variant="body2" sx={{ mb: 0.75, fontWeight: 600 }}>
        {t('pages.gardenPlan.plantState.legend.ring')}
      </Typography>
      <Box component="ul" sx={LIST_SX}>
        {LEGEND_RINGS.map(({ lifecycle, key }) => (
          <Box component="li" key={key} data-legend-ring={lifecycle} sx={ITEM_SX}>
            <svg width={32} height={32} viewBox="-16 -16 32 32" aria-hidden="true" focusable="false">
              <PlantMarkerBody
                entry={SAMPLE}
                state={{ lifecycle, badge: null, initial: 'T', progress: null, ariaLabel: '' }}
                radius={RADIUS}
                pxPerM={1}
                fill={fill}
                ringColor={theme.palette.text.primary}
                initialColor={theme.palette.getContrastText(fill)}
                selectedColor={theme.palette.primary.main}
                selected={false}
                detail={false}
              />
            </svg>
            <Typography variant="body2">{t(`pages.gardenPlan.plantState.legend.${key}`)}</Typography>
          </Box>
        ))}
      </Box>
      <Typography variant="body2" sx={{ mt: 1.5, mb: 0.75, fontWeight: 600 }}>
        {t('pages.gardenPlan.plantState.legend.badge')}
      </Typography>
      <Box component="ul" sx={LIST_SX}>
        {LEGEND_BADGES.map(({ code, key }) => (
          <Box component="li" key={key} data-legend-badge={code} sx={ITEM_SX}>
            <svg width={32} height={32} viewBox="-16 -16 32 32" aria-hidden="true" focusable="false">
              <PlantBadge code={code} x={0} y={0} radius={11} />
            </svg>
            <Typography variant="body2">{t(`pages.gardenPlan.plantState.legend.${key}`)}</Typography>
          </Box>
        ))}
      </Box>
    </>
  );
}
