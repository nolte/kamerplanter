import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Link from '@mui/material/Link';
import SymptomPicker from './SymptomPicker';
import DiagnosisResultsPanel from './DiagnosisResultsPanel';
import { diagnoseApi } from '@/api';
import type { DiagnosisResult, DiagnosisSymptom } from '@/api/types';

type WizardStep = 0 | 1 | 2;

function resolveLanguage(i18nLanguage: string): 'de' | 'en' {
  return i18nLanguage.startsWith('en') ? 'en' : 'de';
}

/**
 * REQ-036 §5 — the guided multi-step diagnosis wizard.
 *
 * Step 1 symptom selection → Step 2 optional notes / photo hint → Step 3 the
 * top-3 result. The photo step is a soft bridge to the REQ-038 CV image
 * diagnosis (not a rebuild); the notes are never surfaced verbatim to the LLM
 * (the backend only forwards a neutral "user added notes" flag).
 */
export default function DiagnosisWizard() {
  const { t, i18n } = useTranslation();
  const language = useMemo(() => resolveLanguage(i18n.language), [i18n.language]);

  const [activeStep, setActiveStep] = useState<WizardStep>(0);
  const [symptoms, setSymptoms] = useState<DiagnosisSymptom[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    diagnoseApi
      .listSymptoms(language)
      .then((data) => {
        if (!cancelled) {
          setSymptoms(data);
          setLoadError(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [language]);

  const toggleSymptom = useCallback((slug: string) => {
    setSelected((prev) => (prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]));
  }, []);

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setAnalyzeError(false);
    try {
      const analysis = await diagnoseApi.analyzeDiagnosis({
        symptom_slugs: selected,
        extra_notes: notes.trim() || null,
        language,
      });
      setResult(analysis);
      setActiveStep(2);
    } catch {
      setAnalyzeError(true);
    } finally {
      setLoading(false);
    }
  }, [selected, notes, language]);

  const steps = useMemo(
    () => [t('diagnose.steps.symptoms'), t('diagnose.steps.context'), t('diagnose.steps.results')],
    [t],
  );

  const restart = useCallback(() => {
    setSelected([]);
    setNotes('');
    setResult(null);
    setAnalyzeError(false);
    setActiveStep(0);
  }, []);

  return (
    <Box data-testid="diagnosis-wizard">
      <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {loadError ? (
        <Alert severity="warning" data-testid="diagnosis-load-error">
          {t('diagnose.errors.loadSymptoms')}
        </Alert>
      ) : null}

      {activeStep === 0 ? (
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('diagnose.steps.symptomsHelp')}
          </Typography>
          <SymptomPicker symptoms={symptoms} selected={selected} onToggle={toggleSymptom} />
          <Stack direction="row" sx={{ mt: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              disabled={selected.length === 0}
              onClick={() => setActiveStep(1)}
              data-testid="diagnosis-next-context"
            >
              {t('common.next', 'Weiter')}
            </Button>
          </Stack>
        </Box>
      ) : null}

      {activeStep === 1 ? (
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('diagnose.steps.contextHelp')}
          </Typography>
          <TextField
            label={t('diagnose.context.notesLabel')}
            helperText={t('diagnose.context.notesHelp')}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            multiline
            minRows={2}
            fullWidth
            slotProps={{ htmlInput: { maxLength: 2000 } }}
            data-testid="diagnosis-notes"
          />
          <Alert severity="info" sx={{ mt: 2 }} data-testid="diagnosis-photo-hint">
            {t('diagnose.context.photoHint')}{' '}
            <Link component={RouterLink} to="/pflanzen/identifikation">
              {t('diagnose.context.photoLink')}
            </Link>
          </Alert>
          {analyzeError ? (
            <Alert severity="error" sx={{ mt: 2 }} data-testid="diagnosis-analyze-error">
              {t('diagnose.errors.analyze')}
            </Alert>
          ) : null}
          <Stack direction="row" sx={{ mt: 2, justifyContent: 'space-between' }}>
            <Button onClick={() => setActiveStep(0)}>{t('common.back', 'Zurück')}</Button>
            <Button
              variant="contained"
              onClick={runAnalysis}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} color="inherit" /> : undefined}
              data-testid="diagnosis-analyze"
            >
              {t('diagnose.actions.analyze')}
            </Button>
          </Stack>
        </Box>
      ) : null}

      {activeStep === 2 && result ? (
        <Box>
          {result.status === 'ok' && result.candidates.length > 0 ? (
            <DiagnosisResultsPanel result={result} />
          ) : (
            <Alert severity="warning" data-testid="diagnosis-empty-result">
              {result.status === 'knowledge_service_error'
                ? t('diagnose.errors.serviceUnavailable')
                : result.status === 'error'
                  ? t('diagnose.errors.invalidOutput')
                  : t('diagnose.errors.noResult')}
            </Alert>
          )}
          <Stack direction="row" sx={{ mt: 2, justifyContent: 'flex-start' }}>
            <Button onClick={restart} data-testid="diagnosis-restart">
              {t('diagnose.actions.restart')}
            </Button>
          </Stack>
        </Box>
      ) : null}
    </Box>
  );
}
