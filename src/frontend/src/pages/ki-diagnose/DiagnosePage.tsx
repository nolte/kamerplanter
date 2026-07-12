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
      <Typography color="text.secondary" sx={{ mb: 2, maxWidth: '72ch' }}>
        {t('diagnose.subtitle')}
      </Typography>
      {/* 760px caps the reading column so the wizard's short-answer
          controls (checkboxes, notes field, result cards) don't stretch
          into an uncomfortably wide single-line-of-sight on desktop —
          same READING_COL_MAX convention as TankDetailPage / FertilizerDetailPage. */}
      <Paper sx={{ p: { xs: 2, sm: 3 }, maxWidth: 760 }}>
        <DiagnosisWizard />
      </Paper>
    </Box>
  );
}
