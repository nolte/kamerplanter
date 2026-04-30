import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/** REQ-036 KI-Diagnose-Assistent page scaffold. */
export default function DiagnosePage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="diagnose-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.diagnose.title', 'KI-Diagnose')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.diagnose.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-036).'
        )}
      </Typography>
    </Box>
  );
}
