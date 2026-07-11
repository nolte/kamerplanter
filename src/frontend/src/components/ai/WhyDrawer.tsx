import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Drawer from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import AIResponse from './AIResponse';
import { resolveAiErrorMessage } from './aiErrorMessage';
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
  const [error, setError] = useState<string | null>(null);
  // Bumped by the retry button to re-run the load effect below without
  // requiring the drawer to be closed and reopened first (avoids a dead end
  // when the KI feature is disabled/un-consented at the moment the drawer
  // first opens but gets enabled while it stays open).
  const [retryToken, setRetryToken] = useState(0);

  const retry = useCallback(() => setRetryToken((n) => n + 1), []);

  useEffect(() => {
    if (!open) return;
    let active = true;
    setLoading(true);
    setError(null);
    setAnswer(null);
    const run = async () => {
      try {
        const result = await aiApi.explain({
          ...request,
          language: i18n.language.startsWith('en') ? 'en' : 'de',
        });
        if (active) setAnswer(result);
      } catch (err) {
        if (active) setError(resolveAiErrorMessage(err, t, t('ai.why.error')));
      } finally {
        if (active) setLoading(false);
      }
    };
    void run();
    return () => {
      active = false;
    };
    // request identity is stable per open; re-run only when the drawer opens
    // or the retry button bumps `retryToken`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, retryToken]);

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
          <Stack spacing={1} sx={{ py: 2 }} role="alert">
            <Typography variant="body2" color="error" data-testid="why-error">
              {error}
            </Typography>
            <Button
              size="small"
              variant="outlined"
              onClick={retry}
              sx={{ alignSelf: 'flex-start', minHeight: 48 }}
              data-testid="why-retry"
            >
              {t('ai.why.retry')}
            </Button>
          </Stack>
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
            <Button variant="contained" onClick={onFollow} sx={{ minHeight: 48 }}>
              {t('ai.why.follow')}
            </Button>
          )}
          <Button onClick={onClose} sx={{ minHeight: 48 }}>
            {t('common.close')}
          </Button>
        </Stack>
      </Box>
    </Drawer>
  );
}
