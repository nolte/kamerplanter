/**
 * Legend of the plant markers (REQ-053 GP-UX-005, GP-UX-061): the ring per lifecycle and the badge per reason,
 * drawn with the same parts as the markers so the legend can never drift from the plan. Collapsed by default;
 * the explanation is text first, the picture is a help (GP-UX-015).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { PlantStateLegendItems } from './PlantStateLegendItems';

export default function PlantStateLegend() {
  const { t } = useTranslation();
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
      <PlantStateLegendItems />
    </Box>
  );
}
