import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';
import { isLightMode } from '@/config/mode';
import { useConsent } from '@/hooks/useConsent';
import { isErrorTrackingConfigured } from '@/observability/errorTracking';

/**
 * The revoke path for the browser-held `error_tracking` consent (UI-NFR-013
 * CW-001..CW-003, #2159).
 *
 * The consent banner disappears once a decision is made (CB-006); without this
 * switch a grant could not be taken back. Toggling it writes the shared consent
 * store, and the error tracker closes or starts on that write — no reload.
 * Rendered under the same conditions as the banner (see `AppConsentBanner`).
 */
export default function BrowserConsentSettings() {
  const { t } = useTranslation();
  const { consent, setConsent } = useConsent();

  // Hidden in Light mode: the tracker never runs there (errorTracking.ts
  // `trackingPermitted`), so a switch would offer a choice without effect.
  if (isLightMode || !isErrorTrackingConfigured()) return null;

  return (
    <Box data-testid="browser-consent-settings" sx={{ mb: 2 }}>
      <Typography variant="subtitle2" component="h3">
        {t('consent.browser.heading')}
      </Typography>
      <Typography
        id="browser-consent-settings-desc"
        variant="body2"
        color="text.secondary"
        sx={{ mb: 1 }}
      >
        {t('consent.browser.description')}
      </Typography>
      <FormControlLabel
        control={
          <Switch
            checked={consent.error_tracking === true}
            onChange={(_, checked) =>
              setConsent({
                ...consent,
                error_tracking: checked,
                timestamp: new Date().toISOString(),
              })
            }
            slotProps={{ input: { 'aria-describedby': 'browser-consent-settings-desc' } }}
          />
        }
        sx={{ minHeight: 44 }}
        label={t('consent.browser.error_tracking')}
        data-testid="browser-consent-error-tracking"
      />
    </Box>
  );
}
