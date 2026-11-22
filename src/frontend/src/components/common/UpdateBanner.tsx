import { useSyncExternalStore } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import Stack from '@mui/material/Stack';
import {
  activateWaitingWorker,
  getWaitingRegistration,
  markUpdateAvailable,
  subscribeToUpdate,
} from '@/lib/serviceWorkerRegistration';

/**
 * "Neue Version verfügbar — Jetzt aktualisieren" (UI-NFR-012 R-014, REQ-053 WP 9.1). Shown while a
 * new service worker waits; "Update now" activates it and the page reloads under the new build,
 * "Later" hides the banner until the next page load.
 */
export default function UpdateBanner() {
  const { t } = useTranslation();
  const registration = useSyncExternalStore(subscribeToUpdate, getWaitingRegistration, () => null);

  return (
    <Snackbar
      open={registration !== null}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      data-testid="pwa-update-banner"
    >
      <Alert
        severity="info"
        variant="filled"
        sx={{ alignItems: 'center' }}
        action={
          <Stack direction="row" spacing={1}>
            <Button color="inherit" size="small" onClick={() => markUpdateAvailable(null)}>
              {t('common.pwa.updateLater')}
            </Button>
            <Button
              color="inherit"
              size="small"
              variant="outlined"
              onClick={() => registration && activateWaitingWorker(registration)}
              data-testid="pwa-update-now"
            >
              {t('common.pwa.updateNow')}
            </Button>
          </Stack>
        }
      >
        {t('common.pwa.updateAvailable')}
      </Alert>
    </Snackbar>
  );
}
