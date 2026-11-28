import { useEffect, useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';
import { useConsent } from '@/hooks/useConsent';
import { useConsentTexts } from '@/hooks/useConsentTexts';
import { browserReportsPermittedNow, decideOnDevice } from '@/observability/consent';
import {
  decideAccountConsent,
  reconcileAccountConsent,
  startAccountSync,
} from '@/observability/consentSync';
import { errorTrackerHost, isBrowserConsentManaged } from '@/observability/errorTracking';

/** WCAG 2.5.5 — UI-NFR-013 v1.3 asks for 48 px targets. */
const TOUCH_TARGET = { minHeight: 48 } as const;

/**
 * "Fehlerberichte aus dem Browser" in Datenschutz → Einwilligungen (UI-NFR-013
 * §4.2, CW-001/CW-002/CW-005, CP-007, CP-012; #2159, #3025).
 *
 * - The switch is the **account** consent `browser_error_reports`. It shows what
 *   the server confirmed, never an optimistic state; while a change is sent it
 *   is `aria-busy`, and a failure shows an error.
 * - "Dieser Browser sendet zurzeit …" is the decision function itself.
 * - The **device** decision (made while signed out) is shown with a reset: the
 *   only way to lift a decline of this browser (CP-007).
 * - A failed read and a pending revoke are shown with a retry (CP-012).
 *
 * Rendered only where the consent is managed (DSN configured, full mode); the
 * page's general purpose list then leaves `browser_error_reports` out, so the
 * purpose has one control.
 */
export default function BrowserConsentSettings() {
  const { t } = useTranslation();
  const { snapshot } = useConsent();
  const [busy, setBusy] = useState(false);
  const [writeFailed, setWriteFailed] = useState(false);
  const managed = isBrowserConsentManaged();
  const textsReady = useConsentTexts();

  // The page works even if the shell's lazy load of the sync module failed.
  useEffect(() => {
    if (managed) startAccountSync();
  }, [managed]);

  // CB-007: no switch to a text that is not on screen.
  if (!managed || !textsReady) return null;

  const { account, pendingRevoke } = snapshot;
  const device = snapshot.device.browser_error_reports;
  const accountGranted = account.kind === 'granted' && !pendingRevoke;
  // CP-013: the server holds another text than this page shows — reload before deciding.
  const outdated = account.kind === 'outdated';
  // Re-evaluated on every snapshot change; the age limit of an account grant is part of it.
  const sending = browserReportsPermittedNow(snapshot);
  const host =
    errorTrackerHost() ?? t('consent.banner.category.browser_error_reports.host_unknown');

  const toggle = async (granted: boolean) => {
    if (busy || outdated) return;
    setBusy(true);
    setWriteFailed(false);
    const result = await decideAccountConsent(granted);
    setBusy(false);
    // A failed revoke is already shown as pending; a failed grant needs its own message.
    if (result === 'failed' && granted) setWriteFailed(true);
  };

  const retry = () => {
    setWriteFailed(false);
    void reconcileAccountConsent();
  };

  return (
    <Box data-testid="browser-consent-settings" sx={{ mb: 2 }}>
      <Typography variant="subtitle2" component="h3">
        {t('consent.settings.heading')}
      </Typography>
      <Typography
        id="browser-consent-settings-desc"
        variant="body2"
        color="text.secondary"
        sx={{ mb: 1 }}
      >
        {t('consent.banner.category.browser_error_reports.description', { host })}{' '}
        {t('consent.banner.scope_account')}
      </Typography>
      <FormControlLabel
        control={
          <Switch
            checked={accountGranted}
            onChange={(_, checked) => void toggle(checked)}
            slotProps={{
              input: {
                'aria-describedby': 'browser-consent-settings-desc',
                'aria-busy': busy || undefined,
                'aria-disabled': busy || outdated || undefined,
              },
            }}
          />
        }
        sx={TOUCH_TARGET}
        label={t('consent.settings.account_switch')}
        data-testid="browser-consent-account-switch"
      />
      <Typography
        variant="body2"
        role="status"
        sx={{ mb: 1 }}
        data-testid="browser-consent-sending"
        data-sending={sending ? 'true' : 'false'}
      >
        {account.kind === 'unknown'
          ? t('consent.settings.loading')
          : t(sending ? 'consent.settings.status_sending' : 'consent.settings.status_not_sending')}
      </Typography>

      {outdated && (
        <Alert
          severity="warning"
          role="alert"
          sx={{ mb: 1 }}
          data-testid="browser-consent-outdated"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => window.location.reload()}
              sx={TOUCH_TARGET}
            >
              {t('consent.settings.reload')}
            </Button>
          }
        >
          {t('consent.settings.text_outdated')}
        </Alert>
      )}
      {writeFailed && (
        <Alert
          severity="error"
          role="alert"
          sx={{ mb: 1 }}
          data-testid="browser-consent-write-failed"
        >
          {t('consent.settings.write_failed')}
        </Alert>
      )}
      {pendingRevoke && (
        <Alert
          severity="warning"
          role="alert"
          sx={{ mb: 1 }}
          data-testid="browser-consent-revoke-pending"
          action={
            <Button color="inherit" size="small" onClick={retry} sx={TOUCH_TARGET}>
              {t('consent.settings.retry')}
            </Button>
          }
        >
          {t('consent.settings.revoke_pending')}
        </Alert>
      )}
      {!pendingRevoke && account.kind === 'failed' && (
        <Alert
          severity="warning"
          role="alert"
          sx={{ mb: 1 }}
          data-testid="browser-consent-sync-failed"
          action={
            <Button color="inherit" size="small" onClick={retry} sx={TOUCH_TARGET}>
              {t('consent.settings.retry')}
            </Button>
          }
        >
          {t('consent.settings.sync_failed')}
        </Alert>
      )}

      {/* v1.5 (operator decision 2026-11-28): this device's own decision, next to the
          account's — "not from this device, otherwise yes" is the device switch off. */}
      <Box data-testid="browser-consent-device">
        <FormControlLabel
          control={
            <Switch
              checked={device === true}
              onChange={(_, checked) => decideOnDevice(checked)}
              slotProps={{ input: { 'aria-describedby': 'browser-consent-device-desc' } }}
            />
          }
          sx={TOUCH_TARGET}
          label={t('consent.settings.device_switch')}
          data-testid="browser-consent-device-switch"
        />
        <Typography
          id="browser-consent-device-desc"
          variant="body2"
          color="text.secondary"
          sx={{ mb: 0.5 }}
        >
          {t(
            device === null
              ? 'consent.settings.device_undecided'
              : device
                ? 'consent.settings.device_granted'
                : 'consent.settings.device_denied',
          )}
        </Typography>
        {device !== null && (
          <Button
            variant="outlined"
            size="small"
            onClick={() => decideOnDevice(null)}
            sx={TOUCH_TARGET}
            data-testid="browser-consent-device-reset"
          >
            {t('consent.settings.device_reset')}
          </Button>
        )}
      </Box>
    </Box>
  );
}
