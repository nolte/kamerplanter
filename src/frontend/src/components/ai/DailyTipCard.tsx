import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import Button from '@mui/material/Button';
import AIResponse from './AIResponse';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { aiApi } from '@/api';
import type { AiTipCard } from '@/api/types';

const DISMISS_STORAGE_PREFIX = 'kp.ai.dailyTip.dismissed';

// UI-NFR-001 R-011: 48x48 touch target on mobile/tablet.
const TOUCH_TARGET_SX = { minWidth: { xs: 48, sm: 32 }, minHeight: { xs: 48, sm: 32 } } as const;

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
 *
 * Seit #1461 erzeugt der `GET` den Tipp nicht mehr selbst — ein Lesezugriff darf
 * nicht schreiben und keinen LLM-Aufruf kosten. `null` heisst darum auch „fuer
 * heute noch nichts erzeugt"; einem Grower bietet die Karte dann ausdruecklich
 * `POST /ai/daily-tip/refresh` an, statt unsichtbar zu bleiben.
 */
export default function DailyTipCard() {
  const { t, i18n } = useTranslation();
  const dismissStorageKey = `${DISMISS_STORAGE_PREFIX}.${todayKey()}`;
  const [tip, setTip] = useState<AiTipCard | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [generating, setGenerating] = useState(false);
  // Generating is a write (`require_tenant_role(grower)`), so the invitation is
  // absent for a viewer rather than present and refused.
  const { canEdit } = useTenantPermissions();
  // Lazy init from storage so the "already dismissed today" state is set without
  // a cascading setState inside the effect (react-hooks/set-state-in-effect).
  const [dismissed, setDismissed] = useState(() => readDismissed(dismissStorageKey));

  useEffect(() => {
    if (readDismissed(dismissStorageKey)) return;
    let active = true;
    aiApi
      .getDailyTip()
      .then((result) => {
        if (active) {
          setTip(result);
          setLoaded(true);
        }
      })
      .catch(() => {
        // Online-only feature (UI-NFR-012): a failure hides the card silently.
        // `loaded` stays false, so the "generate" invitation is not offered for
        // what may be an outage rather than an empty day.
        if (active) setTip(null);
      });
    return () => {
      active = false;
    };
  }, [dismissStorageKey]);

  const handleDismiss = useCallback(() => {
    setDismissed(true);
    persistDismissed(dismissStorageKey);
    void aiApi.dismissDailyTip().catch(() => undefined);
  }, [dismissStorageKey]);

  const handleGenerate = useCallback(() => {
    setGenerating(true);
    aiApi
      .refreshDailyTip(i18n.language.startsWith('en') ? 'en' : 'de')
      .then(setTip)
      .catch(() => undefined)
      .finally(() => setGenerating(false));
  }, [i18n.language]);

  if (dismissed) return null;

  if (!tip) {
    if (!loaded || !canEdit) return null;
    return (
      <Card variant="outlined" data-testid="daily-tip-empty">
        <CardContent>
          <Typography variant="overline" color="text.secondary">
            {t('ai.dailyTip.heading')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('ai.dailyTip.empty')}
          </Typography>
          <Button
            size="small"
            startIcon={<AutoAwesomeIcon />}
            onClick={handleGenerate}
            disabled={generating}
            sx={{ minHeight: 48 }}
            data-testid="daily-tip-generate"
          >
            {t('ai.dailyTip.generate')}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="outlined" data-testid="daily-tip-card">
      <CardContent sx={{ position: 'relative' }}>
        <IconButton
          size="small"
          onClick={handleDismiss}
          aria-label={t('ai.dailyTip.dismiss')}
          sx={{ position: 'absolute', top: 8, right: 8, ...TOUCH_TARGET_SX }}
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
