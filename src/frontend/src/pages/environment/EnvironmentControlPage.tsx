import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/** REQ-018 Environment control / actuator page scaffold. */
export default function EnvironmentControlPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="environment-control-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.environmentControl.title', 'Umgebungssteuerung')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.environmentControl.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-018).'
        )}
      </Typography>
    </Box>
  );
}
