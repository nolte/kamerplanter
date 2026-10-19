/**
 * Legend of the plant markers (REQ-053 GP-UX-005, GP-UX-061): the ring per lifecycle and the badge per reason,
 * drawn with the same parts as the markers so the legend can never drift from the plan. Collapsed by default;
 * the explanation is text first, the picture is a help (GP-UX-015).
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

export default function PlantStateLegend() {
  const { t } = useTranslation();
  const theme = useTheme();
  const fill = theme.palette.success.main;
  return (
    <Box
      component="details"
      data-testid="plant-state-legend"
      sx={{
        mt: 1,
        '& summary': {
          cursor: 'pointer',
          minHeight: 44,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          borderRadius: 1,
          '&::before': { content: '"\\25B8"', display: 'inline-block', transition: 'transform 0.15s' },
          '&:focus-visible': { outline: '2px solid', outlineColor: 'primary.main', outlineOffset: 2 },
        },
        '&[open] > summary::before': { transform: 'rotate(90deg)' },
      }}
    >
      <Typography component="summary" variant="subtitle2">
        {t('pages.gardenPlan.plantState.legend.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.plantState.legend.intro')}
      </Typography>
      <Typography variant="body2" sx={{ mb: 0.75, fontWeight: 600 }}>
        {t('pages.gardenPlan.plantState.legend.ring')}
      </Typography>
      <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'grid', gap: 0.75 }}>
        {LEGEND_RINGS.map(({ lifecycle, key }) => (
          <Box component="li" key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <svg width={32} height={32} viewBox="-16 -16 32 32" aria-hidden="true">
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
      <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'grid', gap: 0.75 }}>
        {LEGEND_BADGES.map(({ code, key }) => (
          <Box component="li" key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <svg width={32} height={32} viewBox="-16 -16 32 32" aria-hidden="true">
              <PlantBadge code={code} x={0} y={0} radius={11} />
            </svg>
            <Typography variant="body2">{t(`pages.gardenPlan.plantState.legend.${key}`)}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
