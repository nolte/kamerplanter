import { useEffect, useState } from 'react';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import { useTranslation } from 'react-i18next';

const STORAGE_KEY = 'kamerplanter:consent:v1';

export type ConsentChoice = 'all' | 'necessary' | 'custom';

export interface ConsentState {
  necessary: true;
  error_tracking: boolean | null;
  external_services: boolean | null;
  timestamp: string | null;
  version: string;
}

const INITIAL_STATE: ConsentState = {
  necessary: true,
  error_tracking: null,
  external_services: null,
  timestamp: null,
  version: '1.0',
};

function readConsent(): ConsentState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return INITIAL_STATE;
    const parsed = JSON.parse(raw) as Partial<ConsentState>;
    return { ...INITIAL_STATE, ...parsed, necessary: true };
  } catch {
    return INITIAL_STATE;
  }
}

function writeConsent(state: ConsentState): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    /* localStorage unavailable — silent no-op (private mode, etc.) */
  }
}

export interface ConsentBannerProps {
  /**
   * If true, suppresses the banner regardless of stored state. The Light mode
   * (REQ-027) sets this to `true` because the GDPR household exemption
   * (Art. 2 (2) lit. c) waives the consent requirement (UI-NFR-013 CB-001).
   */
  suppress?: boolean;
  /** Test seam — overrides the default localStorage-backed state read. */
  initialState?: ConsentState;
  /** Called whenever the user makes a choice. */
  onChoice?: (state: ConsentState, choice: ConsentChoice) => void;
}

/**
 * UI-NFR-013 §3.1 Consent Banner.
 *
 * Minimal-invasive bottom banner with three equal-prominence actions:
 * "Alle akzeptieren" / "Nur Notwendige" / "Einstellungen". Stores the
 * decision in localStorage for unauthenticated users; the consent sync
 * with the REQ-025 backend (`POST /api/v1/privacy/consents`) lives in a
 * follow-up integration step.
 */
export default function ConsentBanner({
  suppress = false,
  initialState,
  onChoice,
}: ConsentBannerProps) {
  const { t } = useTranslation();
  const [state, setState] = useState<ConsentState>(() => initialState ?? readConsent());

  // Re-read once on mount so the banner reflects late-loaded persisted state.
  useEffect(() => {
    if (initialState) return;
    setState(readConsent());
  }, [initialState]);

  if (suppress) return null;
  const decided = state.error_tracking !== null && state.external_services !== null;
  if (decided) return null;

  const decide = (choice: ConsentChoice) => {
    const next: ConsentState = {
      ...state,
      necessary: true,
      timestamp: new Date().toISOString(),
      error_tracking: choice === 'all' ? true : choice === 'necessary' ? false : state.error_tracking,
      external_services: choice === 'all' ? true : choice === 'necessary' ? false : state.external_services,
    };
    setState(next);
    writeConsent(next);
    onChoice?.(next, choice);
  };

  return (
    <Paper
      elevation={6}
      role="region"
      aria-label={t('consent.banner.aria_label', 'Datenschutz-Einwilligung')}
      data-testid="consent-banner"
      sx={{
        position: 'fixed',
        left: 16,
        right: 16,
        bottom: 16,
        zIndex: (theme) => theme.zIndex.snackbar + 1,
        p: 2,
        borderRadius: 2,
      }}
    >
      <Stack spacing={1.5}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {t('consent.banner.title', 'Wir respektieren Ihre Privatsphäre')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t(
            'consent.banner.body',
            'Notwendige Cookies sind für Login, Spracheinstellung und Tenant-Auswahl aktiv. Optional sind Fehleranalyse (Sentry) und externe Dienste (HaveIBeenPwned, Stammdatenanreicherung).'
          )}
        </Typography>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 1,
            justifyContent: 'flex-end',
          }}
        >
          <Button
            variant="outlined"
            data-testid="consent-banner-settings"
            onClick={() => decide('custom')}
          >
            {t('consent.banner.settings', 'Einstellungen')}
          </Button>
          <Button
            variant="outlined"
            data-testid="consent-banner-necessary"
            onClick={() => decide('necessary')}
          >
            {t('consent.banner.necessary', 'Nur Notwendige')}
          </Button>
          <Button
            variant="contained"
            data-testid="consent-banner-accept-all"
            onClick={() => decide('all')}
          >
            {t('consent.banner.accept_all', 'Alle akzeptieren')}
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}
