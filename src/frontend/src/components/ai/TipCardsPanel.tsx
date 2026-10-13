import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';
import RefreshIcon from '@mui/icons-material/Refresh';
import CircularProgress from '@mui/material/CircularProgress';
import AIResponse from './AIResponse';
import { resolveAiErrorMessage } from './aiErrorMessage';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { apiLanguage } from '@/i18n/apiLanguage';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { aiApi } from '@/api';
import type { AiTipCard } from '@/api/types';

/**
 * Whether a tip's `action_url` may be rendered into an `href` (review SCR-012).
 *
 * The value arrives from a persisted record on a card the user is invited to
 * press. The backend refuses anything but a site-relative path at the model
 * boundary (`AiTipCard._action_url_is_site_relative`), and this is the second
 * half of that pair: a stale row written before the constraint, or a future
 * producer reached through another path, must not be able to put `javascript:`
 * behind a button.
 *
 * `//evil.example` is rejected with the rest — it starts with `/` and is an
 * absolute, protocol-relative URL, which is exactly what a "starts with /" check
 * lets through.
 */
export function isSiteRelative(url: string | null | undefined): url is string {
  return typeof url === 'string' && url.startsWith('/') && !url.startsWith('//');
}

export interface TipCardsPanelProps {
  /** Context type: `plant_instance` | `planting_run` | `general`. */
  contextType: string;
  /** Context key (plant/run key). */
  contextKey: string;
  /** Optional heading above the cards. */
  title?: string;
}

/**
 * REQ-031 §6.2 — Tipp-Karten fuer einen Pflanzen-/Run-Kontext.
 *
 * Jede Karte wird durch die `<AIResponse>`-Huelle gerendert. Beginner sehen
 * kompaktere Karten (max 2) mit zugeklapptem Quellen-Footer (REQ-021). Ein
 * "Aktualisieren"-Button erzwingt eine Neugenerierung. Die Sichtbarkeit ist an
 * Stufe-2 (Tenant-Setting) gebunden — der aufrufende Kontext blendet das Panel
 * aus, wenn KI fuer den Tenant deaktiviert ist.
 */
export default function TipCardsPanel({ contextType, contextKey, title }: TipCardsPanelProps) {
  const { t, i18n } = useTranslation();
  const { level } = useExpertiseLevel();
  const [tips, setTips] = useState<AiTipCard[] | null>(null);
  const [mayGenerate, setMayGenerate] = useState(false);
  const [loading, setLoading] = useState(false);
  /**
   * A failed *forced* refresh, kept rather than swallowed (review SCR-003).
   *
   * The `catch` below deliberately leaves the tips in place on a forced refresh,
   * which is right — but it also said nothing. In the empty state introduced by
   * #1461 that is total silence: the panel shows "no tips yet, generate one", the
   * click is refused, and nothing anywhere changes.
   */
  const [refreshError, setRefreshError] = useState<unknown>(null);

  const language = apiLanguage(i18n.language);

  const load = useCallback(
    async (force: boolean) => {
      setLoading(true);
      setRefreshError(null);
      try {
        const result = force
          ? await aiApi.refreshTips(contextType, contextKey, language)
          : await aiApi.getTips(contextType, contextKey);
        setTips(result.tips);
        setMayGenerate(result.refresh_available === true);
      } catch (err: unknown) {
        // Online-only feature (UI-NFR-012): hide the panel when it has nothing to
        // show. A *forced* refresh that fails is different — the panel already
        // holds tips the reader may see, and clearing them turns a failed
        // regeneration into the loss of the read surface too. #1353 made that
        // reachable: `POST /ai/tips/refresh` answers 403 to a viewer, and before
        // this the whole panel vanished on the click.
        if (force) setRefreshError(err);
        else setTips([]);
      } finally {
        setLoading(false);
      }
    },
    [contextType, contextKey, language],
  );

  useEffect(() => {
    void load(false);
  }, [load]);

  // Regenerating tips is a write on the server (`require_tenant_role(grower)`
  // since #1353); `canEdit` is the same predicate client-side, and
  // `refresh_available` is the server's own answer to it. Both are required: the
  // flag is absent on an older response, and `canEdit` alone would put the
  // control on a surface the server then refuses.
  const { canEdit } = useTenantPermissions();
  const canRefresh = canEdit && mayGenerate;

  const maxCards = level === 'beginner' ? 2 : 4;
  const visibleTips = (tips ?? []).slice(0, maxCards);

  if (loading && tips === null) {
    return (
      <Box data-testid="tip-cards-loading">
        <Skeleton variant="rounded" height={90} sx={{ mb: 1 }} />
        <Skeleton variant="rounded" height={90} />
      </Box>
    );
  }

  // Empty and nobody here can do anything about it — stay invisible, as before.
  //
  // Empty and the caller MAY generate is a new state (#1461): reading the tips
  // no longer generates them on a cache miss, so without an explicit invitation
  // a grower would never find out that tips exist at all. The panel then renders
  // its heading, one sentence of explanation and the generate button.
  if (tips !== null && visibleTips.length === 0 && !canRefresh) {
    return null;
  }

  const isEmpty = tips !== null && visibleTips.length === 0;

  return (
    <Box data-testid="tip-cards-panel">
      <Stack
        direction="row"
        sx={{ mb: 1, alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {title ?? t('ai.tips.heading')}
        </Typography>
        {canRefresh && (
        <Button
          size="small"
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />}
          onClick={() => void load(true)}
          disabled={loading}
          aria-busy={loading}
          sx={{ minHeight: 48 }}
          data-testid={isEmpty ? 'tip-cards-generate' : 'tip-cards-refresh'}
        >
          {t(refreshError !== null ? 'ai.errors.retry' : isEmpty ? 'ai.tips.generate' : 'ai.tips.refresh')}
        </Button>
        )}
      </Stack>

      {/* Announced, because it replaces content the reader is already looking at
          (UI-NFR-002 R-011). In the empty state the error takes the place of the
          "nothing generated yet" sentence — repeating both would be noise; with
          cards present it sits above them, so the read surface survives a failed
          regeneration exactly as the `catch` intends. */}
      <Box aria-live="polite">
        {refreshError !== null && (
          <Box sx={{ mb: isEmpty ? 0 : 1.5 }} data-testid="tip-cards-refresh-error">
            <ErrorDisplay
              error={resolveAiErrorMessage(refreshError, t, t('ai.errors.tipsGenerateFailed'))}
            />
          </Box>
        )}
        {isEmpty && refreshError === null && (
          <Typography variant="body2" color="text.secondary" data-testid="tip-cards-empty">
            {t('ai.tips.empty')}
          </Typography>
        )}
      </Box>

      <Stack spacing={1.5}>
        {visibleTips.map((tip) => (
          <Card key={tip.key ?? tip.title} variant="outlined">
            <CardContent>
              <AIResponse
                sources={tip.sources}
                modelName={tip.model_name}
                usesTenantData={tip.uses_tenant_data}
                confidence={tip.confidence}
                languageMismatchWarning={tip.language_mismatch_warning}
              >
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {tip.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {tip.body}
                </Typography>
              </AIResponse>
            </CardContent>
            {isSiteRelative(tip.action_url) && (
              <CardActions>
                <Button size="small" href={tip.action_url}>
                  {t('ai.tips.learnMore')}
                </Button>
              </CardActions>
            )}
          </Card>
        ))}
      </Stack>
    </Box>
  );
}
