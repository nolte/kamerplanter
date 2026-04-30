import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/** REQ-035 KI-Fachbegriff-Glossar page scaffold. */
export default function GlossarPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="glossar-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.glossar.title', 'Fachbegriff-Glossar')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.glossar.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-035).'
        )}
      </Typography>
    </Box>
  );
}
