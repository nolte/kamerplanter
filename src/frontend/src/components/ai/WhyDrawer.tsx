import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Drawer from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import AIResponse from './AIResponse';
import { aiApi } from '@/api';
import type { AiExplainRequest, AiResponse as AiResponseData } from '@/api/types';

export interface WhyDrawerProps {
  open: boolean;
  onClose: () => void;
  request: AiExplainRequest;
  /** Optional primary action ("dieser Empfehlung folgen"). */
  onFollow?: () => void;
}

/**
 * REQ-031 §6.4 — rechter Drawer mit der KI-"Warum?"-Antwort.
 *
 * Laedt `POST /ai/explain` beim Oeffnen, zeigt waehrenddessen einen Spinner
 * ("KI denkt nach…") und rendert die Antwort durch die `<AIResponse>`-Huelle.
 */
export default function WhyDrawer({ open, onClose, request, onFollow }: WhyDrawerProps) {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<AiResponseData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!open) return;
    let active = true;
    setLoading(true);
    setError(false);
    setAnswer(null);
    const run = async () => {
      try {
        const result = await aiApi.explain({
          ...request,
          language: i18n.language.startsWith('en') ? 'en' : 'de',
        });
        if (active) setAnswer(result);
      } catch {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    };
    void run();
    return () => {
      active = false;
    };
    // request identity is stable per open; re-run only when the drawer opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <Drawer anchor="right" open={open} onClose={onClose} data-testid="why-drawer">
      <Box sx={{ width: { xs: '100vw', sm: 360 }, p: 2 }} role="region" aria-label={t('ai.why.title')}>
        <Typography variant="h6" gutterBottom>
          {t('ai.why.title')}
        </Typography>

        {loading && (
          <Stack direction="row" spacing={1} sx={{ py: 2, alignItems: 'center' }}>
            <CircularProgress size={20} />
            <Typography variant="body2" color="text.secondary">
              {t('ai.why.thinking')}
            </Typography>
          </Stack>
        )}

        {error && (
          <Typography variant="body2" color="error" sx={{ py: 2 }} data-testid="why-error">
            {t('ai.why.error')}
          </Typography>
        )}

        {answer && (
          <AIResponse
            sources={answer.sources}
            modelName={answer.model_name}
            providerType={answer.provider_type}
            usesTenantData={answer.uses_tenant_data}
            usesCloudProvider={answer.uses_cloud_provider}
            confidence={answer.confidence}
            cultivarHint={answer.cultivar_hint}
            fallbackSpecies={answer.fallback_species}
            languageMismatchWarning={answer.language_mismatch_warning}
          >
            <Typography variant="body2">{answer.answer_text}</Typography>
          </AIResponse>
        )}

        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
          {onFollow && answer && (
            <Button variant="contained" onClick={onFollow}>
              {t('ai.why.follow')}
            </Button>
          )}
          <Button onClick={onClose}>{t('common.close')}</Button>
        </Stack>
      </Box>
    </Drawer>
  );
}
