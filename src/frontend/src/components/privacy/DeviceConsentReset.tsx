import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import { useTranslation } from 'react-i18next';
import { useConsent } from '@/hooks/useConsent';
import { decideOnDevice, requestConsentBannerFocus } from '@/observability/consent';
import { isBrowserConsentManaged } from '@/observability/errorTracking';

/**
 * "Entscheidung dieses Browsers zu Fehlerberichten ändern" on the public pages
 * (UI-NFR-013 v1.4 CW-006, #3025).
 *
 * A decision made without signing in must be as easy to take back as it was to
 * give (Art. 7 (3) GDPR) — and the privacy settings are behind the sign-in. The
 * link resets the device decision, so the banner (device form) asks again.
 * Mounted by `PublicOnlyRoute` under every signed-out page; shown only where the
 * consent is managed and this browser has decided. Its label is in the core
 * namespace, so the way back never depends on a lazily loaded text.
 */
export default function DeviceConsentReset() {
  const { t } = useTranslation();
  const { snapshot } = useConsent();
  if (!isBrowserConsentManaged()) return null;
  if (snapshot.auth.kind !== 'signed_out' || snapshot.device.browser_error_reports === null) {
    return null;
  }
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
      <Button
        variant="text"
        size="small"
        color="inherit"
        onClick={() => {
          // The link disappears with the click; the banner that asks again takes the focus.
          requestConsentBannerFocus();
          decideOnDevice(null);
        }}
        sx={{ minHeight: 48, textDecoration: 'underline', color: 'text.secondary' }}
        data-testid="device-consent-reset"
      >
        {t('consentPublic.reset')}
      </Button>
    </Box>
  );
}
