import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

/**
 * The permanent connectivity indicator of the app shell (UI-NFR-012 R-033–R-035, REQ-053 WP 9.1):
 * a green dot while online, an orange "Offline" chip while offline. A polite live region, so a
 * screen reader hears the change without losing its place.
 */
export default function ConnectivityIndicator() {
  const { t } = useTranslation();
  const online = useOnlineStatus();

  if (!online) {
    return (
      <Tooltip title={t('common.pwa.offlineHint')}>
        <Chip
          role="status"
          aria-live="polite"
          icon={<CloudOffIcon />}
          label={t('common.pwa.offline')}
          color="warning"
          size="small"
          sx={{ mr: 1, fontWeight: 600 }}
          data-testid="connectivity-indicator"
          data-online="false"
        />
      </Tooltip>
    );
  }

  return (
    <Tooltip title={t('common.pwa.onlineHint')}>
      <Box
        role="status"
        aria-live="polite"
        aria-label={t('common.pwa.online')}
        tabIndex={0}
        data-testid="connectivity-indicator"
        data-online="true"
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 20,
          height: 20,
          mr: 1,
          borderRadius: '50%',
          bgcolor: 'background.paper',
          flexShrink: 0,
        }}
      >
        <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: 'success.main' }} />
      </Box>
    </Tooltip>
  );
}
