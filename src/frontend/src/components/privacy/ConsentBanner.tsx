import { useId, useState } from 'react';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import type { SxProps, Theme } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { useConsent } from '@/hooks/useConsent';
import { useConsentTexts } from '@/hooks/useConsentTexts';
import { consentPrompt, decideOnDevice } from '@/observability/consent';
import { decideAccountConsent } from '@/observability/consentSync';
import { errorTrackerHost } from '@/observability/errorTracking';
import { BOTTOM_NAV_OFFSET } from '@/components/layout/bottomNavOffset';

export type ConsentChoice = 'all' | 'necessary' | 'custom';

export interface ConsentBannerProps {
  /** Called whenever the user makes a choice, with the decision and the button used. */
  onChoice?: (granted: boolean, choice: ConsentChoice) => void;
}

/** WCAG 2.5.5 — UI-NFR-013 v1.3 asks for 48 px targets in the banner. */
const TOUCH_TARGET = { minHeight: 48 } as const;

const CATEGORY_TEST_ID = 'consent-banner-browser-error-reports';

const BANNER_SX: SxProps<Theme> = {
  position: 'fixed',
  left: 16,
  right: 16,
  // Clear of the iOS home indicator / Android gesture bar — and of the phone's bottom navigation, whose
  // offset already contains that inset (#3018).
  bottom: `calc(16px + var(${BOTTOM_NAV_OFFSET}, env(safe-area-inset-bottom)))`,
  // Above page content and the app bar, below modals, drawers and
  // snackbars — a dialog or an error toast must never hide under it.
  zIndex: (theme) => theme.zIndex.modal - 1,
  p: 2,
  borderRadius: 2,
  // `dvh` tracks the visible viewport when mobile browser chrome shows.
  maxHeight: 'calc(100dvh - 32px)',
  overflowY: 'auto',
};

/**
 * UI-NFR-013 §3.1/§4 consent banner for browser error reports (#2159, #3025).
 *
 * Minimal-invasive bottom banner with three equal-prominence actions:
 * "Alle akzeptieren" / "Nur Notwendige" / "Einstellungen" (CB-002..CB-004).
 * Two forms, chosen by `consentPrompt` (§5.4):
 *
 * - **device** (signed out): the click is stored in this browser only;
 * - **account** (signed in, no valid account decision): the click is stored in
 *   the account via the REQ-025 API. A failed grant keeps the banner with an
 *   error and a retry; a decline stops this browser at once even if the request
 *   fails, and says so (CP-012).
 *
 * Never shown before the sign-in state and, when signed in, the account consent
 * are known — so it does not flash on a new device before the account is read.
 */
export default function ConsentBanner({ onChoice }: ConsentBannerProps) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { snapshot } = useConsent();
  const [customizing, setCustomizing] = useState(false);
  const [draft, setDraft] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const [outdated, setOutdated] = useState(false);
  const textsReady = useConsentTexts();
  const categoriesId = useId();
  const errorId = useId();

  const prompt = consentPrompt(snapshot);
  // CB-007: never a decision to a text that is not on screen (the texts are a lazy bundle).
  if ((prompt === null && !outdated) || !textsReady) return null;

  const decide = async (choice: ConsentChoice) => {
    if (busy) return;
    const granted = choice === 'all' ? true : choice === 'necessary' ? false : draft;
    onChoice?.(granted, choice);
    if (prompt === 'device') {
      decideOnDevice(granted);
      return;
    }
    setBusy(true);
    setFailed(false);
    const result = await decideAccountConsent(granted);
    setBusy(false);
    if (result === 'confirmed') return;
    if (result === 'outdated') {
      setOutdated(true);
      return;
    }
    if (granted) setFailed(true);
    // A decline already applies here and the banner is gone: say that it is not stored yet.
    else enqueueSnackbar(t('consent.banner.revoke_pending'), { variant: 'warning' });
  };

  const host =
    errorTrackerHost() ?? t('consent.banner.category.browser_error_reports.host_unknown');
  const busyProps = { 'aria-disabled': busy || undefined, 'aria-busy': busy || undefined };

  if (prompt === 'confirm' && !outdated) {
    // CP-014 (operator decision 2026-11-28): the account agreed, this browser has not — ask it
    // once. Both answers write only this device; the account stays as it is.
    const confirm = (granted: boolean) => {
      onChoice?.(granted, granted ? 'all' : 'necessary');
      decideOnDevice(granted);
    };
    return (
      <Paper
        elevation={6}
        role="region"
        aria-label={t('consent.banner.aria_label')}
        data-testid="consent-banner"
        data-consent-form="confirm"
        sx={BANNER_SX}
      >
        <Stack spacing={1.5}>
          <Typography variant="subtitle1" component="h2" sx={{ fontWeight: 600 }}>
            {t('consent.banner.confirm_title')}
          </Typography>
          <Typography variant="body2" color="text.secondary" data-testid="consent-banner-summary">
            {t('consent.banner.confirm_body')} {t('consent.banner.summary', { host })}
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 1,
              justifyContent: 'flex-end',
            }}
          >
            {/* Equal weight, as CB-003 asks of every pair of answers. */}
            <Button
              variant="contained"
              data-testid="consent-banner-confirm-no"
              onClick={() => confirm(false)}
              sx={TOUCH_TARGET}
            >
              {t('consent.banner.confirm_no')}
            </Button>
            <Button
              variant="contained"
              data-testid="consent-banner-confirm-yes"
              onClick={() => confirm(true)}
              sx={TOUCH_TARGET}
            >
              {t('consent.banner.confirm_yes')}
            </Button>
          </Box>
        </Stack>
      </Paper>
    );
  }

  if (outdated) {
    // CP-013: the server holds a newer text than this page — no decision until it is reloaded.
    return (
      <Paper
        elevation={6}
        role="region"
        aria-label={t('consent.banner.aria_label')}
        data-testid="consent-banner"
        sx={BANNER_SX}
      >
        <Alert
          severity="warning"
          role="alert"
          data-testid="consent-banner-outdated"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => window.location.reload()}
              sx={TOUCH_TARGET}
            >
              {t('consent.banner.reload')}
            </Button>
          }
        >
          {t('consent.banner.text_outdated')}
        </Alert>
      </Paper>
    );
  }

  return (
    <Paper
      elevation={6}
      role="region"
      aria-label={t('consent.banner.aria_label')}
      data-testid="consent-banner"
      data-consent-form={prompt}
      sx={BANNER_SX}
    >
      <Stack spacing={1.5}>
        <Typography variant="subtitle1" component="h2" sx={{ fontWeight: 600 }}>
          {t('consent.banner.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" data-testid="consent-banner-summary">
          {t('consent.banner.intro')} {t('consent.banner.summary', { host })}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t(prompt === 'account' ? 'consent.banner.scope_account' : 'consent.banner.scope_device')}{' '}
          {t(
            prompt === 'account'
              ? 'consent.banner.change_hint_account'
              : 'consent.banner.change_hint_device',
          )}
        </Typography>
        {failed && (
          <Alert
            severity="error"
            role="alert"
            id={errorId}
            data-testid="consent-banner-error"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => void decide('all')}
                sx={TOUCH_TARGET}
                data-testid="consent-banner-retry"
                {...busyProps}
              >
                {t('consent.banner.retry')}
              </Button>
            }
          >
            {t('consent.banner.grant_failed')}
          </Alert>
        )}
        {/* Always rendered (hidden while collapsed) so the toggle's
            aria-controls points at a real element. */}
        <Stack
          spacing={1}
          id={categoriesId}
          hidden={!customizing}
          // Stack's own `display: flex` would beat the UA rule for [hidden].
          sx={{ display: customizing ? 'flex' : 'none' }}
          data-testid="consent-banner-categories"
        >
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={draft}
                  onChange={(_, checked) => setDraft(checked)}
                  slotProps={{ input: { 'aria-describedby': `${CATEGORY_TEST_ID}-desc` } }}
                />
              }
              label={t('consent.banner.category.browser_error_reports.label')}
              data-testid={CATEGORY_TEST_ID}
              sx={TOUCH_TARGET}
            />
            <Typography
              id={`${CATEGORY_TEST_ID}-desc`}
              variant="caption"
              color="text.secondary"
              component="p"
            >
              {t('consent.banner.category.browser_error_reports.description', { host })}
            </Typography>
          </Box>
          <Box>
            <Button
              variant="outlined"
              data-testid="consent-banner-save"
              onClick={() => void decide('custom')}
              sx={TOUCH_TARGET}
              {...busyProps}
            >
              {t('consent.banner.save')}
            </Button>
          </Box>
        </Stack>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 1,
            justifyContent: 'flex-end',
          }}
        >
          {/* Stays mounted when expanded: unmounting the focused button would
              drop keyboard focus to <body>. */}
          <Button
            variant="outlined"
            data-testid="consent-banner-settings"
            aria-expanded={customizing}
            aria-controls={categoriesId}
            onClick={() => setCustomizing((open) => !open)}
            sx={TOUCH_TARGET}
          >
            {t('consent.banner.settings')}
          </Button>
          {/* CB-003: "Nur Notwendige" and "Alle akzeptieren" carry the same
              visual weight — a lighter "no" would steer the decision. While a
              decision is sent they are aria-disabled, not disabled, so focus stays. */}
          <Button
            variant="contained"
            data-testid="consent-banner-necessary"
            onClick={() => void decide('necessary')}
            sx={TOUCH_TARGET}
            {...busyProps}
          >
            {t('consent.banner.necessary')}
          </Button>
          <Button
            variant="contained"
            data-testid="consent-banner-accept-all"
            onClick={() => void decide('all')}
            sx={TOUCH_TARGET}
            aria-describedby={failed ? errorId : undefined}
            {...busyProps}
          >
            {t('consent.banner.accept_all')}
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}
