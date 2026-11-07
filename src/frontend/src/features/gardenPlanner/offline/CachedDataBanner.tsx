/**
 * "Stand von hh:mm" (REQ-053 WP 9.2, GP-UX-024): shown whenever a view reads from the plan cache
 * instead of the network, so nobody mistakes the last loaded state for the current one.
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import CloudOffIcon from '@mui/icons-material/CloudOff';

interface CachedDataBannerProps {
  /** Epoch milliseconds of the online read the shown data comes from. */
  cachedAt: number;
  /** Distinguishes several banners on one page. */
  testId?: string;
}

export default function CachedDataBanner({ cachedAt, testId = 'offline-cached-banner' }: CachedDataBannerProps) {
  const { t, i18n } = useTranslation();
  const time = useMemo(
    () => new Intl.DateTimeFormat(i18n.language, { hour: '2-digit', minute: '2-digit' }).format(new Date(cachedAt)),
    [cachedAt, i18n.language],
  );
  return (
    <Alert severity="info" icon={<CloudOffIcon />} role="status" sx={{ mb: 2 }} data-testid={testId}>
      {t('pages.gardenPlan.offline.cachedAt', { time })}
    </Alert>
  );
}
