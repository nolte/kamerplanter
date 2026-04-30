import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/**
 * REQ-008 Post-Harvest page scaffold.
 *
 * The full curing / drying / storage workflow UI lands with the REQ-008
 * implementation PR. This placeholder pins the route name + page
 * boundary so the router can already include it.
 */
export default function PostHarvestPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="post-harvest-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.postHarvest.title', 'Nacherntebehandlung')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.postHarvest.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-008).'
        )}
      </Typography>
    </Box>
  );
}
