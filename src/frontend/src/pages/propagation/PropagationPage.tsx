import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

/**
 * REQ-017 Propagation / Vermehrungsmanagement page scaffold.
 * Full lineage graph + clone/cross/graft/division forms land with the
 * REQ-017 implementation PR.
 */
export default function PropagationPage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="propagation-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.propagation.title', 'Vermehrungsmanagement')}
      </Typography>
      <Typography color="text.secondary">
        {t(
          'pages.propagation.scaffoldNotice',
          'Diese Funktion ist noch in Vorbereitung (REQ-017).'
        )}
      </Typography>
    </Box>
  );
}
