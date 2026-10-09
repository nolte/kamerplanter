import { useState } from 'react';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import { useTranslation } from 'react-i18next';
import { useConsent } from '@/hooks/useConsent';
import type { ConsentState, OptionalConsentCategory } from '@/observability/consent';

export type { ConsentState } from '@/observability/consent';

export type ConsentChoice = 'all' | 'necessary' | 'custom';

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
 * The categories the settings view offers. Only a category some code reads is
 * asked for: `external_services` stays in the stored state for compatibility,
 * but since REQ-025 v1.31 (#2136) no processing reads it (there is no HIBP
 * check, and the master-data enrichment sends species names only), so asking
 * for it would be consent with no effect.
 */
const CATEGORIES: { key: OptionalConsentCategory; testId: string }[] = [
  { key: 'error_tracking', testId: 'consent-banner-error-tracking' },
];

/**
 * UI-NFR-013 §3.1 Consent Banner.
 *
 * Minimal-invasive bottom banner with three equal-prominence actions:
 * "Alle akzeptieren" / "Nur Notwendige" / "Einstellungen" (CB-002..CB-004).
 * "Einstellungen" expands a per-category selection in place. The decision goes
 * through the shared consent store (`@/observability/consent`), so the error
 * tracker starts or stops on the same click; the sync with the REQ-025 backend
 * (`POST /api/v1/privacy/consents`) is a follow-up integration step.
 */
export default function ConsentBanner({
  suppress = false,
  initialState,
  onChoice,
}: ConsentBannerProps) {
  const { t } = useTranslation();
  const { consent: stored, setConsent } = useConsent();
  const [override, setOverride] = useState<ConsentState | undefined>(initialState);
  const [customizing, setCustomizing] = useState(false);
  const state = override ?? stored;
  const [draft, setDraft] = useState<Record<OptionalConsentCategory, boolean>>(() => ({
    error_tracking: state.error_tracking === true,
    external_services: state.external_services === true,
  }));

  if (suppress) return null;
  const decided = state.error_tracking !== null && state.external_services !== null;
  if (decided) return null;

  const decide = (choice: ConsentChoice) => {
    const granted = choice === 'all';
    const next: ConsentState = {
      ...state,
      necessary: true,
      timestamp: new Date().toISOString(),
      error_tracking: choice === 'custom' ? draft.error_tracking : granted,
      external_services:
        choice === 'custom' ? (state.external_services ?? draft.external_services) : granted,
    };
    if (override) setOverride(next);
    setConsent(next);
    onChoice?.(next, choice);
  };

  return (
    <Paper
      elevation={6}
      role="region"
      aria-label={t('consent.banner.aria_label')}
      data-testid="consent-banner"
      sx={{
        position: 'fixed',
        left: 16,
        right: 16,
        bottom: 16,
        zIndex: (theme) => theme.zIndex.snackbar + 1,
        p: 2,
        borderRadius: 2,
        maxHeight: 'calc(100vh - 32px)',
        overflowY: 'auto',
      }}
    >
      <Stack spacing={1.5}>
        <Typography variant="subtitle1" component="h2" sx={{ fontWeight: 600 }}>
          {t('consent.banner.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('consent.banner.body')}
        </Typography>
        {customizing && (
          <Stack spacing={1} data-testid="consent-banner-categories">
            {CATEGORIES.map(({ key, testId }) => (
              <Box key={key}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={draft[key]}
                      onChange={(_, checked) => setDraft((d) => ({ ...d, [key]: checked }))}
                      slotProps={{ input: { 'aria-describedby': `${testId}-desc` } }}
                    />
                  }
                  label={t(`consent.banner.category.${key}.label`)}
                  data-testid={testId}
                />
                <Typography
                  id={`${testId}-desc`}
                  variant="caption"
                  color="text.secondary"
                  component="p"
                >
                  {t(`consent.banner.category.${key}.description`)}
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 1,
            justifyContent: 'flex-end',
          }}
        >
          {customizing ? (
            <Button
              variant="outlined"
              data-testid="consent-banner-save"
              onClick={() => decide('custom')}
            >
              {t('consent.banner.save')}
            </Button>
          ) : (
            <Button
              variant="outlined"
              data-testid="consent-banner-settings"
              onClick={() => setCustomizing(true)}
            >
              {t('consent.banner.settings')}
            </Button>
          )}
          {/* CB-003: "Nur Notwendige" and "Alle akzeptieren" carry the same
              visual weight — a lighter "no" would steer the decision. */}
          <Button
            variant="contained"
            data-testid="consent-banner-necessary"
            onClick={() => decide('necessary')}
          >
            {t('consent.banner.necessary')}
          </Button>
          <Button
            variant="contained"
            data-testid="consent-banner-accept-all"
            onClick={() => decide('all')}
          >
            {t('consent.banner.accept_all')}
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}
