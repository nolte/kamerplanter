import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import AIResponse from './AIResponse';
import { aiApi } from '@/api';
import type { AiTipCard } from '@/api/types';

const DISMISS_STORAGE_PREFIX = 'kp.ai.dailyTip.dismissed';

function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Safe localStorage access — never throws when storage is unavailable. */
function readDismissed(key: string): boolean {
  try {
    return localStorage.getItem(key) === '1';
  } catch {
    return false;
  }
}

function persistDismissed(key: string): void {
  try {
    localStorage.setItem(key, '1');
  } catch {
    // Storage unavailable (private mode / SSR) — dismissal stays in-memory.
  }
}

/**
 * REQ-031 §6.3 — Tipp-des-Tages-Karte am Top des Dashboards.
 *
 * Laedt einmalig pro Session `GET /ai/daily-tip`, rendert die Antwort durch die
 * `<AIResponse>`-Huelle und blendet sich nach dem Schliessen fuer den Rest des
 * Tages aus (Persistenz via API + Local-Storage). Ist die KI deaktiviert oder
 * der Knowledge-Service nicht erreichbar (`null`), rendert die Karte nichts.
 */
export default function DailyTipCard() {
  const { t, i18n } = useTranslation();
  const dismissStorageKey = `${DISMISS_STORAGE_PREFIX}.${todayKey()}`;
  const [tip, setTip] = useState<AiTipCard | null>(null);
  // Lazy init from storage so the "already dismissed today" state is set without
  // a cascading setState inside the effect (react-hooks/set-state-in-effect).
  const [dismissed, setDismissed] = useState(() => readDismissed(dismissStorageKey));

  useEffect(() => {
    if (readDismissed(dismissStorageKey)) return;
    let active = true;
    aiApi
      .getDailyTip(i18n.language.startsWith('en') ? 'en' : 'de')
      .then((result) => {
        if (active) setTip(result);
      })
      .catch(() => {
        // Online-only feature (UI-NFR-012): a failure hides the card silently.
        if (active) setTip(null);
      });
    return () => {
      active = false;
    };
  }, [dismissStorageKey, i18n.language]);

  const handleDismiss = useCallback(() => {
    setDismissed(true);
    persistDismissed(dismissStorageKey);
    void aiApi.dismissDailyTip().catch(() => undefined);
  }, [dismissStorageKey]);

  if (dismissed || !tip) return null;

  return (
    <Card variant="outlined" data-testid="daily-tip-card">
      <CardContent sx={{ position: 'relative' }}>
        <IconButton
          size="small"
          onClick={handleDismiss}
          aria-label={t('ai.dailyTip.dismiss')}
          sx={{ position: 'absolute', top: 8, right: 8 }}
          data-testid="daily-tip-dismiss"
        >
          <CloseIcon fontSize="small" />
        </IconButton>
        <Typography variant="overline" color="text.secondary">
          {t('ai.dailyTip.heading')}
        </Typography>
        <AIResponse
          sources={tip.sources}
          modelName={tip.model_name}
          usesTenantData={tip.uses_tenant_data}
          confidence={tip.confidence}
          languageMismatchWarning={tip.language_mismatch_warning}
        >
          <Box sx={{ pr: 4 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {tip.title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {tip.body}
            </Typography>
          </Box>
        </AIResponse>
      </CardContent>
    </Card>
  );
}
