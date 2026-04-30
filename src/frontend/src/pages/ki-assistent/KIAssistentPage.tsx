import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/** REQ-031 KI-Assistent Pflanzenberatung page scaffold. */
export default function KIAssistentPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="ki-assistent-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.kiAssistent.title', 'KI-Assistent')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.kiAssistent.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-031).'
        )}
      </Typography>
    </Box>
  );
}
