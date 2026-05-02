import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/** REQ-026 Aquaponik page scaffold. */
export default function AquaponikPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="aquaponik-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.aquaponik.title', 'Aquaponik')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.aquaponik.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-026).'
        )}
      </Typography>
    </Box>
  );
}
