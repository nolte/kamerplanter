/**
 * Offline and nothing in the plan cache (REQ-053 WP 9.2): an empty state that says why and what
 * helps (the EmptyState pattern of #2641), never an error with a retry that cannot succeed.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import EmptyState from '@/components/common/EmptyState';

interface OfflineCacheMissProps {
  /** Which data is missing (`pages.gardenPlan.offline.miss.<subject>`). */
  subject: 'plan' | 'beds' | 'sites' | 'bed' | 'bedDetails';
  testId?: string;
}

export default function OfflineCacheMiss({ subject, testId = 'offline-cache-miss' }: OfflineCacheMissProps) {
  const { t } = useTranslation();
  return (
    <Box data-testid={testId}>
      <EmptyState
        message={t(`pages.gardenPlan.offline.miss.${subject}`)}
        description={t('pages.gardenPlan.offline.miss.hint')}
      />
    </Box>
  );
}
