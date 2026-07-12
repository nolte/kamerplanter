import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import PageTitle from '@/components/layout/PageTitle';
import DiagnosisWizard from '@/components/diagnosis/DiagnosisWizard';

/**
 * REQ-036 KI-Diagnose-Assistent — der strukturierte, symptombasierte
 * Diagnose-Assistent (abgegrenzt von der REQ-038 Foto-Bilderkennung).
 *
 * Hostet den mehrstufigen `<DiagnosisWizard>` (Symptomauswahl → optionaler
 * Kontext/Foto-Hinweis → Top-3-Ergebnis mit IPM-Bruecke).
 */
export default function DiagnosePage() {
  const { t } = useTranslation();
  return (
    <Box sx={{ p: 3 }} data-testid="diagnose-page">
      <PageTitle title={t('diagnose.title')} />
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        {t('diagnose.subtitle')}
      </Typography>
      <Paper sx={{ p: { xs: 2, sm: 3 } }}>
        <DiagnosisWizard />
      </Paper>
    </Box>
  );
}
