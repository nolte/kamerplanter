import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import { visuallyHidden } from '@mui/utils';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

/**
 * The permanent connectivity indicator of the app shell (UI-NFR-012 R-033–R-035, REQ-053 WP 9.1):
 * a green dot while online, an orange "Offline" chip while offline.
 *
 * ONE live region that stays mounted; only its content changes. A screen reader announces a change
 * of content inside an existing `role="status"` region — a region that is itself swapped for a new
 * element is a new region, and the change to "Offline" would go unannounced.
 */
export default function ConnectivityIndicator() {
  const { t } = useTranslation();
  const online = useOnlineStatus();

  return (
    <Box
      role="status"
      aria-live="polite"
      data-testid="connectivity-indicator"
      data-online={online ? 'true' : 'false'}
      sx={{ display: 'inline-flex', alignItems: 'center', mr: 1, flexShrink: 0 }}
    >
      {online ? (
        <Tooltip title={t('common.pwa.onlineHint')}>
          <Box
            tabIndex={0}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 20,
              height: 20,
              borderRadius: '50%',
              bgcolor: 'background.paper',
            }}
          >
            <Box aria-hidden sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: 'success.main' }} />
            <Box component="span" sx={visuallyHidden}>
              {t('common.pwa.online')}
            </Box>
          </Box>
        </Tooltip>
      ) : (
        <Tooltip title={t('common.pwa.offlineHint')}>
          <Chip
            icon={<CloudOffIcon />}
            label={t('common.pwa.offline')}
            color="warning"
            size="small"
            tabIndex={0}
            sx={{ fontWeight: 600 }}
          />
        </Tooltip>
      )}
    </Box>
  );
}
