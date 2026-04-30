import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/** REQ-029 KI-Pflanzenidentifikation page scaffold. */
export default function PlantIdentificationPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="plant-identification-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.plantIdentification.title', 'KI-Pflanzenerkennung')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.plantIdentification.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-029).'
        )}
      </Typography>
    </Box>
  );
}
